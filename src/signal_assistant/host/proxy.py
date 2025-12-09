# src/signal_assistant/host/proxy.py

from typing import Any, Dict

from signal_assistant.host.transport import SecureChannel
from signal_assistant.enclave.serialization import CommandSerializer

class EnclaveProxy:
    """
    Acts as a proxy for the host to interact with the enclave.
    Utilizes the SecureChannel for communication.
    """
    def __init__(self, host_to_enclave_queue, enclave_to_host_queue):
        self.secure_channel = SecureChannel(enclave_to_host_queue, host_to_enclave_queue)
        self.secure_channel.establish()

    def send_command(self, command: str, payload: Dict[str, Any]) -> bytes:
        """
        Sends a command to the enclave and receives a response.
        Payload is now a dictionary.
        """
        message_bytes = CommandSerializer.serialize(command, payload)
        print(f"Host EnclaveProxy sending command: {command} with payload: {payload}")
        self.secure_channel.send(message_bytes)
        response = self.secure_channel.receive()
        print(f"Host EnclaveProxy received response: {response}")
        return response

    def get_enclave_status(self) -> str:
        """
        Fetches the status of the enclave.
        """
        response = self.send_command("GET_STATUS", {})
        return f"Enclave Status: {response.decode()}"