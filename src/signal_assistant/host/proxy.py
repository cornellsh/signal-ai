from typing import Any, Dict
from signal_assistant.host.transport import SecureChannel
from signal_assistant.enclave.serialization import CommandSerializer
from signal_assistant.host.logging_client import LoggingClient

# Instantiate the logger once per module
host_logger = LoggingClient("HostApp")

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
        # Log command and payload keys, but NOT sensitive payload content
        host_logger.info(f"Host EnclaveProxy sending command: {command}", metadata={"payload_keys": list(payload.keys())})
        self.secure_channel.send(message_bytes)
        response = self.secure_channel.receive()
        host_logger.info(f"Host EnclaveProxy received response.", metadata={"response_len": len(response)})
        return response

    def get_enclave_status(self) -> str:
        """
        Fetches the status of the enclave.
        """
        response = self.send_command("GET_STATUS", {})
        return f"Enclave Status: {response.decode()}"

    def send_eak_to_enclave(self, eak: str, attestation_verified_by_host: bool) -> bool:
        """
        Simulates sending an External API Key (EAK) to the Enclave.
        This operation is gated by host-side attestation verification.
        """
        if not attestation_verified_by_host:
            host_logger.error("Host: Refusing to provision EAK to Enclave. Host attestation verification failed.")
            return False
        
        # In a real scenario, the host would verify the enclave's attestation report.
        # Here, we assume 'attestation_verified_by_host' means that check passed.

        # The EAK itself is sensitive, but `send_command` uses a SecureChannel,
        # so it will be encrypted during transport.
        try:
            response = self.send_command("PROVISION_EAK", {"eak": eak.encode('utf-8')})
            if response.decode('utf-8') == "EAK Provisioned":
                host_logger.info("Host: Successfully provisioned EAK to Enclave.", metadata={"eak_prefix": eak[:5]})
                return True
            else:
                host_logger.error(f"Host: Enclave failed to provision EAK: {response.decode('utf-8')}")
                return False
        except Exception as e:
            host_logger.error(f"Host: Error provisioning EAK to Enclave: {e}")
            return False
