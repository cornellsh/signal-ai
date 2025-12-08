import asyncio
import socket
import logging
from typing import Optional, Callable, Awaitable
from signal_assistant.config import host_settings

logger = logging.getLogger(__name__)

class VsockServer:
    """
    Async Server running on the Host Sidecar that listens for connections from the Enclave.
    Supports AF_VSOCK (on Nitro) and AF_INET (fallback for dev).
    """
    def __init__(self, port: int = None):
        self.port = port or host_settings.vsock_port
        self.server = None

    async def start(self, client_handler: Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]]):
        """
        Starts the asyncio server.
        client_handler: async function(reader, writer)
        """
        sock = None
        host = None
        
        if hasattr(socket, "AF_VSOCK"):
            logger.info("VSock support detected.")
            try:
                sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
                sock.bind((socket.VMADDR_CID_ANY, self.port))
                # start_server calls listen() on the socket
            except OSError as e:
                logger.error(f"Failed to create VSock socket: {e}. Falling back to TCP.")
                sock = None
        
        if sock is None:
            # Fallback to TCP
            host = "127.0.0.1"
            logger.info(f"Using TCP Fallback on {host}:{self.port}")

        try:
            if sock:
                self.server = await asyncio.start_server(client_handler, sock=sock)
            else:
                self.server = await asyncio.start_server(client_handler, host, self.port, reuse_address=True)
            
            logger.info(f"Server started on port {self.port}")
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Server crashed: {e}", exc_info=True)
            raise