import asyncio
import logging
import struct
import websockets
from signal_assistant.config import host_settings
from signal_assistant.host.transport import VsockServer
from signal_assistant.host.storage.database import SessionLocal
from signal_assistant.host.storage.blob_store import BlobStore

logger = logging.getLogger(__name__)

# Constants (Must match Enclave)
TYPE_SIGNAL_IN = 0x01
TYPE_SIGNAL_OUT = 0x02
TYPE_GET_STATE = 0x03
TYPE_STATE_RESP = 0x04
TYPE_SET_STATE = 0x05

class SignalProxy:
    """
    Proxies traffic between Signal Service and Enclave.
    Also handles Storage Requests from Enclave.
    """
    def __init__(self):
        self.signal_ws_url = host_settings.signal_service_url
        self.enclave_reader = None
        self.enclave_writer = None
        self.signal_ws = None
        self.transport = VsockServer()

    async def run(self):
        logger.info("Starting Signal Proxy...")
        await self.transport.start(self.handle_enclave_connection)

    async def handle_enclave_connection(self, reader, writer):
        logger.info("Enclave connected!")
        self.enclave_reader = reader
        self.enclave_writer = writer
        
        try:
            logger.info(f"Connecting to Signal Service at {self.signal_ws_url}...")
            async with websockets.connect(self.signal_ws_url) as ws:
                self.signal_ws = ws
                logger.info("Connected to Signal Service")
                
                # Run bridge tasks
                task_s2e = asyncio.create_task(self.bridge_signal_to_enclave())
                task_e2h = asyncio.create_task(self.bridge_enclave_to_host())
                
                done, pending = await asyncio.wait(
                    [task_s2e, task_e2h], 
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in pending:
                    task.cancel()
                    
        except Exception as e:
            logger.error(f"Proxy connection failed: {e}")
        finally:
            logger.info("Closing Enclave connection...")
            writer.close()
            await writer.wait_closed()

    async def bridge_signal_to_enclave(self):
        """
        Signal -> Enclave (Wrapped in TYPE_SIGNAL_IN)
        """
        try:
            async for message in self.signal_ws:
                data = message if isinstance(message, bytes) else message.encode('utf-8')
                await self.send_packet_to_enclave(TYPE_SIGNAL_IN, data)
        except Exception as e:
            logger.error(f"Signal->Enclave bridge failed: {e}")
            raise

    async def bridge_enclave_to_host(self):
        """
        Enclave -> Host (Dispatch based on Type)
        """
        try:
            while True:
                header = await self.enclave_reader.readexactly(5)
                msg_type = header[0]
                length = struct.unpack(">I", header[1:])[0]
                payload = await self.enclave_reader.readexactly(length)

                if msg_type == TYPE_SIGNAL_OUT:
                    # Payload is raw envelope to send to Signal
                    await self.signal_ws.send(payload)
                elif msg_type == TYPE_GET_STATE:
                    await self.handle_get_state(payload)
                elif msg_type == TYPE_SET_STATE:
                    await self.handle_set_state(payload)
                else:
                    logger.warning(f"Unknown message type from Enclave: {msg_type}")
        except asyncio.IncompleteReadError:
            logger.info("Enclave disconnected (EOF)")
            raise
        except Exception as e:
            logger.error(f"Enclave->Host bridge failed: {e}")
            raise

    async def send_packet_to_enclave(self, msg_type, payload):
        header = struct.pack(">BI", msg_type, len(payload))
        self.enclave_writer.write(header + payload)
        await self.enclave_writer.drain()

    async def handle_get_state(self, payload):
        """
        Payload: [SignalID (utf8)]
        """
        try:
            signal_id = payload.decode('utf-8')
            logger.debug(f"Handling GET_STATE for user_hash={hash(signal_id)}")
            
            # DB Operation (Synchronous, might block event loop slightly, ideally run in executor)
            # For MVP/Low-throughput, this is okay.
            with SessionLocal() as db:
                store = BlobStore(db)
                blob = store.get_state(signal_id) or b""
            
            # Resp: [SignalID Len: 4][SignalID][Blob]
            id_bytes = signal_id.encode('utf-8')
            resp_payload = struct.pack(">I", len(id_bytes)) + id_bytes + blob
            await self.send_packet_to_enclave(TYPE_STATE_RESP, resp_payload)
        except Exception as e:
            logger.error(f"GET_STATE failed: {e}")

    async def handle_set_state(self, payload):
        """
        Payload: [SignalID Len: 4][SignalID][Blob]
        """
        try:
            id_len = struct.unpack(">I", payload[:4])[0]
            signal_id = payload[4:4+id_len].decode('utf-8')
            blob = payload[4+id_len:]
            
            logger.debug(f"Handling SET_STATE for user_hash={hash(signal_id)} ({len(blob)} bytes)")
            
            with SessionLocal() as db:
                store = BlobStore(db)
                store.save_state(signal_id, blob)
        except Exception as e:
            logger.error(f"SET_STATE failed: {e}")