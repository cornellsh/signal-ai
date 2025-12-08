import json
import logging
import asyncio
from typing import Optional, Tuple
import websockets
from websockets.server import serve

logger = logging.getLogger(__name__)

class MockSignalLib:
    """
    Mock implementation of SignalLib for simulation.
    Uses JSON for 'encryption' to allow transparent debugging.
    """
    def __init__(self):
        pass

    def decrypt_envelope(self, envelope_bytes: bytes) -> Tuple[Optional[str], Optional[str]]:
        try:
            # SignalProxy sends data as bytes.
            data = json.loads(envelope_bytes.decode('utf-8'))
            return data.get('sender'), data.get('text')
        except Exception as e:
            logger.error(f"Mock decryption failed: {e}")
            return None, None

    def encrypt_message(self, recipient_id: str, plaintext: str) -> bytes:
        return json.dumps({
            "recipient": recipient_id,
            "text": plaintext
        }).encode('utf-8')

class MockSignalService:
    """
    Mock Signal Service WebSocket Server.
    """
    def __init__(self, port: int = 8081):
        self.port = port
        self.server = None
        self.clients = set()
        
    async def start(self):
        self.server = await serve(self.handler, "localhost", self.port)
        logger.info(f"Mock Signal Service running on ws://localhost:{self.port}")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handler(self, websocket):
        self.clients.add(websocket)
        logger.info("Mock Signal Service: Client connected")
        try:
            async for message in websocket:
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info("Mock Signal Service: Client disconnected")

    async def handle_message(self, message):
        try:
            if isinstance(message, bytes):
                text = message.decode('utf-8')
            else:
                text = message
            
            # Try to parse as JSON if it matches our MockSignalLib format
            data = json.loads(text)
            logger.info(f"Mock Signal Service RECEIVED: To {data.get('recipient')}: {data.get('text')}")
            # Print to stdout for the user to see
            print(f"\n[Bot -> You]: {data.get('text')}\n> ", end="", flush=True)
            
        except Exception:
            logger.info(f"Mock Signal Service RECEIVED (raw): {message}")

    async def inject_message(self, sender: str, text: str):
        """
        Sends a message to all connected clients (the Host Proxy).
        """
        if not self.clients:
            logger.warning("No clients connected to Mock Service. Waiting...")
            return

        payload = json.dumps({
            "sender": sender,
            "text": text
        })
        
        # Websockets send
        for ws in self.clients:
            await ws.send(payload)

