import asyncio
import os
import logging
import sys
import socket
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 1. Force TCP by hiding AF_VSOCK (must be done before importing transport modules)
if hasattr(socket, "AF_VSOCK"):
    del socket.AF_VSOCK
    logger.info("Forced TCP fallback by hiding socket.AF_VSOCK")

# 2. Override Configuration via Environment Variables
os.environ["SIGNAL_SERVICE_URL"] = "ws://localhost:8081"
os.environ["VSOCK_PORT"] = "5000"
# Ensure we have required settings for Enclave to start
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key"
if "SIGNAL_PHONE_NUMBER" not in os.environ:
    os.environ["SIGNAL_PHONE_NUMBER"] = "+15550000000"

# Import application components after environment setup
from signal_assistant.mocks import MockSignalLib, MockSignalService
from signal_assistant.host.proxy import SignalProxy
from signal_assistant_enclave.app import EnclaveApp
import signal_assistant.enclave.signal_lib
import signal_assistant.enclave.app
from signal_assistant.config import host_settings, enclave_settings
from signal_assistant.host.storage.database import init_db

async def run_simulation():
    # 2.5 Ensure Settings are Applied (Reload/Override if necessary)
    if host_settings:
        logger.info(f"Original Host Settings URL: {host_settings.signal_service_url}")
        host_settings.signal_service_url = os.environ["SIGNAL_SERVICE_URL"]
        host_settings.vsock_port = int(os.environ["VSOCK_PORT"])
        
        # Audit Fix: Use in-memory DB for fresh simulation state
        host_settings.database_url = "sqlite:///:memory:"
        logger.info(f"Updated Host Settings URL: {host_settings.signal_service_url}")
        logger.info(f"Updated Host Settings DB: {host_settings.database_url}")
    
    # 3. Initialize Database (Host)
    logger.info("Initializing Database...")
    init_db()

    # 4. Monkey Patch SignalLib
    logger.info("Patching SignalLib with MockSignalLib...")
    # Patch both the original module and the import in EnclaveApp
    signal_assistant.enclave.signal_lib.SignalLib = MockSignalLib
    signal_assistant.enclave.app.SignalLib = MockSignalLib
    
    # 5. Start Mock Signal Service
    logger.info("Starting Mock Signal Service...")
    mock_service = MockSignalService(port=8081)
    await mock_service.start()
    
    # 5. Start Host Proxy
    logger.info("Starting Host Sidecar...")
    host_proxy = SignalProxy()
    host_task = asyncio.create_task(host_proxy.run())
    
    # Give host time to start listening
    await asyncio.sleep(0.5)
    
    # 6. Start Enclave App
    logger.info("Starting Enclave App...")
    enclave_app = EnclaveApp()
    enclave_task = asyncio.create_task(enclave_app.run())
    
    # Give enclave time to connect
    await asyncio.sleep(0.5)
    
    print("\n" + "="*60)
    print("SIMULATION STARTED")
    print("Environment: Single Process (Host + Enclave + Mock Service)")
    print("Bot is ready. Type your message and press Enter.")
    print("Type '/exit' to quit.")
    print("="*60 + "\n")

    # 7. Interactive Loop
    try:
        loop = asyncio.get_running_loop()
        while True:
            # Run input in executor to avoid blocking the event loop
            msg = await loop.run_in_executor(None, input, "> ")
            
            if msg.strip() == "/exit":
                break
                
            if msg.strip():
                # Inject message as if from a user
                user_number = "+15559999999"
                await mock_service.inject_message(user_number, msg)
                
                # Wait a bit for response to be printed by MockService
                await asyncio.sleep(0.2)
                
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user.")
    except EOFError:
        pass # Handle Ctrl+D
    finally:
        print("\nShutting down simulation...")
        await mock_service.stop()
        
        # Cancel background tasks
        host_task.cancel()
        enclave_task.cancel()
        
        # Wait for cancellation
        try:
            await asyncio.wait([host_task, enclave_task], timeout=1.0)
        except Exception:
            pass
            
def main():
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
