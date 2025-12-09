import time
from typing import Generator, Optional
from pathlib import Path
from signal_assistant.config import host_settings
from signal_assistant.host.signal_adapter.types import RawEnvelope
from signal_assistant.host import logging_client # Added this line

try:
    import signal_client
except ImportError:
    signal_client = None

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
        self.client = None

        logging_client.info(None, f"SignalAdapter initialized for {self.phone_number}")

    def connect(self):
        """
        Establishes connection to the Signal process/socket.
        """
        if self._connected and self.client:
            logging_client.info(None, "Already connected to Signal network.")
            return

        try:
            logging_client.info(None, f"Attempting to connect to Signal for account {self.phone_number} using path {self.account_path}...")
            self.client = signal_client.SignalClient(
                account_id=self.phone_number,
                account_path=Path(self.account_path)
            )
            self.client.start()
            self._connected = True
            logging_client.info(None, "Connected to Signal network.")
        except Exception as e:
            self._connected = False
            logging_client.error(None, f"Failed to connect to Signal network for {self.phone_number}: {e}", {"exception": str(e)})
            raise ConfigurationError(f"Signal connection failed: {e}")


    def listen(self) -> Generator[RawEnvelope, None, None]:
        """
        Yields raw envelopes from the network using the real signal_client.
        """
        if not self._connected or not self.client:
            self.connect()

        logging_client.info(None, f"Listening for messages for {self.phone_number}...")
        while True:
            try:
                raw_message = self.client.receive_message() 
                if raw_message:
                    envelope = RawEnvelope(
                        source_identifier=raw_message.get('source_number', 'unknown'),
                        timestamp=raw_message.get('timestamp', int(time.time() * 1000)),
                        payload=raw_message.get('message_body', '').encode('utf-8'),
                        type=raw_message.get('message_type', 0)
                    )
                    yield envelope
            except Exception as e:
                logging_client.error(None, f"Error while listening for messages: {e}", {"exception": str(e)})
                time.sleep(5)

    def send_message(self, recipient: str, text: str):
        """
        Sends a plaintext message to a recipient using the real signal_client.
        """
        if not self._connected or not self.client:
            self.connect()

        logging_client.info(None, f"Sending message to {recipient}: {text}")
        try:
            self.client.send(recipient, text)
            logging_client.info(None, f"Message sent successfully to {recipient}.")
        except Exception as e:
            logging_client.error(None, f"Failed to send message to {recipient}: {e}", {"exception": str(e)})
            raise

    def stop(self):
        """
        Stops the signal client and disconnects from the Signal service.
        """
        if self._connected and self.client:
            try:
                self.client.stop()
                self._connected = False
                logging_client.info(None, "Disconnected from Signal network.")
            except Exception as e:
                logging_client.error(None, f"Error while stopping Signal client: {e}", {"exception": str(e)})