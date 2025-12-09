from typing import Any, Dict
import json
import sys
from pathlib import Path
from signal_assistant.host.transport import SecureChannel
from signal_assistant_enclave.serialization import CommandSerializer
from signal_assistant.host.logging_client import LoggingClient
import asyncio
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64

# Instantiate the logger once per module
host_logger = LoggingClient("HostApp")

class RegistryVerifier:
    @staticmethod
    def verify(mrenclave: str) -> bool:
        try:
            # Locate registry at project root
            # src/signal_assistant/host/proxy.py -> ../../../measurement_registry.json
            root_dir = Path(__file__).resolve().parents[3]
            registry_path = root_dir / "measurement_registry.json"
            pub_key_path = root_dir / "keys" / "registry.pub"
            
            if not registry_path.exists():
                host_logger.error(None, f"Registry not found at {registry_path}")
                return False
                
            if not pub_key_path.exists():
                host_logger.error(None, f"Registry public key not found at {pub_key_path}")
                return False
            
            with open(registry_path, "r") as f:
                registry = json.load(f)
                
            # Verify signature
            if not registry.get("signatures"):
                host_logger.error(None, "Registry has no signatures.")
                return False
            
            with open(pub_key_path, "rb") as f:
                pub_key = serialization.load_pem_public_key(f.read())
            
            measurements = registry.get("measurements", [])
            data = json.dumps(measurements, sort_keys=True).encode('utf-8')
            
            sig_entry = registry["signatures"][0]
            sig_bytes = base64.b64decode(sig_entry["signature"])
            
            try:
                pub_key.verify(sig_bytes, data)
                host_logger.info(None, "Registry signature verified.")
            except Exception as e:
                host_logger.error(None, f"Registry signature verification failed: {e}")
                return False
            
            for m in measurements:
                if m["mrenclave"] == mrenclave:
                    if m["status"] == "active":
                        host_logger.info(None, f"MRENCLAVE {mrenclave} verified against registry. Version: {m.get('version')}")
                        return True
                    else:
                        host_logger.error(None, f"MRENCLAVE {mrenclave} found but status is '{m['status']}'.")
                        return False
            
            host_logger.error(None, f"MRENCLAVE {mrenclave} not found in registry.")
            return False
        except Exception as e:
            host_logger.error(None, f"Registry verification failed: {e}")
            return False

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
        # Log command, but avoid logging payload details which might contain sensitive keys or trigger filters
        host_logger.info(None, f"Host EnclaveProxy sending command: {command}")
        self.secure_channel.send(message_bytes)
        response = self.secure_channel.receive()
        if response:
             host_logger.info(None, f"Host EnclaveProxy received response.", metadata={"response_len": len(response)})
        else:
             host_logger.warning(None, "Host EnclaveProxy received no response (timeout).")
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
            host_logger.error(None, "Host: Refusing to provision EAK to Enclave. Host attestation verification failed.")
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

class SignalProxy:
    """
    Main Host Application logic.
    """
    def __init__(self):
        pass

    async def run(self):
        host_logger.info(None, "SignalProxy starting...")
        
        # Simulate receiving Attestation Report from Enclave
        # In a real app, we would connect to the enclave first and request it.
        # For this task, we assume we got it.
        simulated_mrenclave = "sha256:simulated_mrenclave_for_dev"
        
        host_logger.info(None, f"Verifying Enclave Measurement: {simulated_mrenclave}")
        if not RegistryVerifier.verify(simulated_mrenclave):
            host_logger.critical(None, "FATAL: Enclave measurement verification failed. The Enclave is not trusted.")
            # We fail closed.
            sys.exit(1)
            
        host_logger.info(None, "Enclave verified. Establishing connection...")
        
        # Keep alive
        while True:
            await asyncio.sleep(1)
