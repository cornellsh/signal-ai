# src/signal_assistant/host/proxy.py

from signal_assistant.host.transport import SecureChannel

class EnclaveProxy:
    """
    Acts as a proxy for the host to interact with the enclave.
    Utilizes the SecureChannel for communication.
    """
    def __init__(self, host_to_enclave_queue, enclave_to_host_queue):
        self.secure_channel = SecureChannel(enclave_to_host_queue, host_to_enclave_queue)
        self.secure_channel.establish()

    def send_command(self, command: str, payload: bytes) -> bytes:
        """
        Sends a command to the enclave and receives a response.
        """
        message = f"{command}:{payload.decode() if payload else ''}".encode()
        print(f"Host EnclaveProxy sending command: {command} with payload: {payload}")
        self.secure_channel.send(message)
        response = self.secure_channel.receive()
        print(f"Host EnclaveProxy received response: {response}")
        return response

    def get_enclave_status(self) -> str:
        """
        Fetches the status of the enclave.
        """
        response = self.send_command("GET_STATUS", b"")
        return f"Enclave Status: {response.decode()}"