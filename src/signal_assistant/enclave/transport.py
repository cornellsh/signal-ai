import asyncio
import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VsockClient:
    """
    Client running inside the Enclave that connects to the Host.
    """
    def __init__(self, port: int = 5000):
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def connect(self):
        """
        Establishes connection to the Host.
        """
        sock = None
        host = None
        
        if hasattr(socket, "AF_VSOCK"):
            logger.info("VSock support detected.")
            # Host CID is usually 2 (QEMU/Firecracker default)
            # Some environments use VMADDR_CID_HOST
            cid = getattr(socket, "VMADDR_CID_HOST", 2)
            try:
                sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
                sock.connect((cid, self.port))
            except OSError as e:
                logger.error(f"Failed to connect via VSock: {e}")
                sock = None
        
        if sock is None:
            # Fallback to TCP
            host = "127.0.0.1"
            logger.info(f"Connecting via TCP to {host}:{self.port}")

        try:
            if sock:
                self.reader, self.writer = await asyncio.open_connection(sock=sock)
            else:
                self.reader, self.writer = await asyncio.open_connection(host, self.port)
            logger.info("Connected to Host.")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    async def send(self, data: bytes):
        if not self.writer:
            raise RuntimeError("Not connected")
        self.writer.write(data)
        await self.writer.drain()

    async def receive(self, n: int) -> bytes:
        if not self.reader:
            raise RuntimeError("Not connected")
        return await self.reader.readexactly(n)
