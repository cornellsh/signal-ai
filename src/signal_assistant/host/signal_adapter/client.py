import logging
import time
from typing import Generator, Optional
from pathlib import Path # Add Path import
from signal_assistant.config import host_settings
from signal_assistant.host.signal_adapter.types import RawEnvelope

try:
    import signal_client
except ImportError:
    # This should not happen if poetry install was successful
    # but provides a graceful fallback for dev environments
    signal_client = None

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Custom exception for configuration related errors."""
    pass

class SignalAdapter:
    def __init__(self):
        if signal_client is None:
            raise ConfigurationError(
                "signal-client library not found. Please ensure it is installed and configured correctly."
            )

        if not host_settings.signal_account_id:
            raise ConfigurationError("Signal account ID (phone number) is not configured in host settings.")
        
        self.phone_number = host_settings.signal_account_id
        self.account_path = host_settings.signal_account_path
        self._connected = False
        self.client = None # Will be initialized during connect

        logger.info(f"SignalAdapter initialized for {self.phone_number}")

    def connect(self):
        """
        Establishes connection to the Signal process/socket.
        """
        if self._connected and self.client:
            logger.info("Already connected to Signal network.")
            return

        try:
            logger.info(f"Attempting to connect to Signal for account {self.phone_number} using path {self.account_path}...")
            # Assuming signal_client.SignalClient takes account_id and account_path
            self.client = signal_client.SignalClient(
                account_id=self.phone_number,
                account_path=Path(self.account_path) # Path is required
            )
            self.client.start() # Correct method to establish connection
            self._connected = True
            logger.info("Connected to Signal network.")
        except Exception as e:
            self._connected = False
            logger.error(f"Failed to connect to Signal network for {self.phone_number}: {e}", exc_info=True)
            raise ConfigurationError(f"Signal connection failed: {e}")


    def listen(self) -> Generator[RawEnvelope, None, None]:
        """
        Yields raw envelopes from the network using the real signal_client.
        """
        if not self._connected or not self.client:
            self.connect()

        logger.info(f"Listening for messages for {self.phone_number}...")
        while True:
            try:
                # Assuming signal_client.SignalClient has a method to receive messages
                # and it returns an object that can be mapped to RawEnvelope.
                # This part is highly dependent on the actual signal_client API.
                # For now, we'll assume a 'receive' method that gives us a dictionary or object
                # with source_identifier, timestamp, payload, and type.
                raw_message = self.client.receive_message() 
                if raw_message:
                    # Adapt raw_message to RawEnvelope based on signal-client documentation.
                    # Assuming raw_message is a dict with keys like 'source_number', 'timestamp', 'message_body', 'message_type'
                    envelope = RawEnvelope(
                        source_identifier=raw_message.get('source_number', 'unknown'),
                        timestamp=raw_message.get('timestamp', int(time.time() * 1000)),
                        payload=raw_message.get('message_body', '').encode('utf-8'), # Convert text to bytes
                        type=raw_message.get('message_type', 0) # Placeholder, needs refinement based on actual types
                    )
                    yield envelope
            except Exception as e:
                logger.error(f"Error while listening for messages: {e}", exc_info=True)
                # Depending on the error, we might want to re-connect or just log and continue.
                time.sleep(5) # Prevent busy loop on errors

    def send_message(self, recipient: str, text: str):
        """
        Sends a plaintext message to a recipient using the real signal_client.
        """
        if not self._connected or not self.client:
            self.connect()

        logger.info(f"Sending message to {recipient}: {text}")
        try:
            # Assuming signal_client.SignalClient has a 'send' method
            self.client.send(recipient, text)
            logger.info(f"Message sent successfully to {recipient}.")
        except Exception as e:
            logger.error(f"Failed to send message to {recipient}: {e}", exc_info=True)
            raise

    def stop(self):
        """
        Stops the signal client and disconnects from the Signal service.
        """
        if self._connected and self.client:
            try:
                self.client.stop()
                self._connected = False
                logger.info("Disconnected from Signal network.")
            except Exception as e:
                logger.error(f"Error while stopping Signal client: {e}", exc_info=True)

