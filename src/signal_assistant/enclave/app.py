import asyncio
import logging
import struct
import base64
import time
from signal_assistant.enclave.transport import VsockClient
from signal_assistant.enclave.signal_lib import SignalLib
from signal_assistant.enclave.kms import NitroKMS
from signal_assistant.enclave.state_encryption import StateEncryptor
from signal_assistant.enclave.bot.orchestrator import BotOrchestrator
from signal_assistant.enclave.privacy_core.core import DecryptedPayload

logger = logging.getLogger(__name__)

# Protocol Constants
TYPE_SIGNAL_IN = 0x01
TYPE_SIGNAL_OUT = 0x02
TYPE_GET_STATE = 0x03
TYPE_STATE_RESP = 0x04
TYPE_SET_STATE = 0x05

class EnclaveApp:
    def __init__(self):
        self.transport = VsockClient()
        self.signal = SignalLib()
        self.kms = NitroKMS()
        self.orchestrator = BotOrchestrator()
        
        # Crypto setup
        # In real world: Unseal the Master Key
        # The mock KMS just returns input, so we use a dummy key for dev
        # We pass a base64 encoded string because the mock KMS expects to decode it.
        unsealed = self.kms.unseal(base64.b64encode(b"dummy_sealed_data"))
        self.master_key = b"0" * 32 
        
        self.state_crypto = StateEncryptor(self.master_key)
        
        self.pending_states = {} # signal_id -> Future

    async def run(self):
        await self.transport.connect()
        logger.info("Enclave Application Started.")
        
        while True:
            try:
                # Read Header: [Type: 1][Length: 4]
                header = await self.transport.receive(5)
                msg_type = header[0]
                length = struct.unpack(">I", header[1:])[0]
                payload = await self.transport.receive(length)
                
                if msg_type == TYPE_SIGNAL_IN:
                    # Dispatch to background task to avoid blocking loop
                    asyncio.create_task(self.handle_signal_message(payload))
                elif msg_type == TYPE_STATE_RESP:
                    self.handle_state_response(payload)
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                # Simple reconnect delay
                await asyncio.sleep(1)

    async def handle_signal_message(self, envelope_bytes: bytes):
        try:
            sender, text = self.signal.decrypt_envelope(envelope_bytes)
            if not sender:
                logger.warning("Failed to decrypt envelope")
                return

            logger.info(f"Processing message from {sender}")
            
            # Fetch State
            state_blob = await self.fetch_state(sender)
            
            # Decrypt State
            try:
                state = self.state_crypto.decrypt(state_blob)
            except Exception:
                logger.warning("Failed to decrypt state, starting fresh.")
                state = {}

            # Process
            # SECURITY NOTE: time.time() uses Host time which is untrusted in TEE.
            # In production, use a secure time source or treat as untrusted.
            decrypted_payload = DecryptedPayload(sender=sender, content=text, timestamp=int(time.time() * 1000))
            response_text, new_state = await asyncio.to_thread(self.orchestrator.process_message, decrypted_payload, state)
            
            # Encrypt State
            new_blob = self.state_crypto.encrypt(new_state)
            
            # Save State
            await self.save_state(sender, new_blob)
            
            # Send Response
            resp_envelope = self.signal.encrypt_message(sender, response_text)
            await self.send_message(resp_envelope)
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    async def fetch_state(self, signal_id: str) -> bytes:
        # Send GET_STATE
        # We use signal_id as correlation ID for simplicity here. 
        # In prod, use unique RequestID.
        future = asyncio.get_event_loop().create_future()
        self.pending_states[signal_id] = future
        
        payload = signal_id.encode('utf-8')
        await self.send_packet(TYPE_GET_STATE, payload)
        
        # Wait for response (with timeout)
        try:
            return await asyncio.wait_for(future, timeout=5.0)
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching state for {signal_id}")
            del self.pending_states[signal_id]
            return b""

    def handle_state_response(self, payload: bytes):
        # Format: [SignalID Len: 4][SignalID][Blob]
        try:
            id_len = struct.unpack(">I", payload[:4])[0]
            signal_id = payload[4:4+id_len].decode('utf-8')
            blob = payload[4+id_len:]
            
            if signal_id in self.pending_states:
                if not self.pending_states[signal_id].done():
                    self.pending_states[signal_id].set_result(blob)
                del self.pending_states[signal_id]
        except Exception as e:
            logger.error(f"Bad state response: {e}")

    async def save_state(self, signal_id: str, blob: bytes):
        # Format: [SignalID Len: 4][SignalID][Blob]
        id_bytes = signal_id.encode('utf-8')
        payload = struct.pack(">I", len(id_bytes)) + id_bytes + blob
        await self.send_packet(TYPE_SET_STATE, payload)

    async def send_message(self, envelope: bytes):
        await self.send_packet(TYPE_SIGNAL_OUT, envelope)

    async def send_packet(self, msg_type: int, payload: bytes):
        header = struct.pack(">BI", msg_type, len(payload))
        await self.transport.send(header + payload)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = EnclaveApp()
    asyncio.run(app.run())
