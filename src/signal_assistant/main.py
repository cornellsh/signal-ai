import asyncio
import logging
from signal_assistant.host.storage.database import init_db
from signal_assistant.host.proxy import SignalProxy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def async_main():
    logger.info("Initializing Host Sidecar...")
    init_db()
    
    proxy = SignalProxy()
    # This runs forever
    await proxy.run()

def run_host():
    """
    Entry point for the Host Sidecar.
    """
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Host stopped.")
