from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from typing import Optional

class HostSettings(BaseSettings):
    """Configuration for the Untrusted Host Sidecar."""
    database_url: str = Field("sqlite:///./signal_assistant.db", description="Database connection string")
    signal_service_url: str = Field("ws://localhost:8080/v1/receive", description="URL for the Signal Service WebSocket")
    signal_account_path: Optional[str] = Field(None, description="Path to the Signal account data directory.")
    signal_account_id: Optional[str] = Field(None, description="The phone number/account ID for the Signal client.")
    
    # We might need to listen on a port for VSock (simulated via TCP in dev)
    vsock_port: int = Field(5000, description="Port for VSock communication")

    model_config = SettingsConfigDict(env_file=".env.host", env_file_encoding="utf-8", extra='ignore')

class EnclaveSettings(BaseSettings):
    """Configuration for the Trusted Enclave Core."""
    signal_phone_number: str = Field(..., description="The phone number registered to this bot")
    
    # AI Configuration
    openai_api_key: SecretStr = Field(..., description="API Key for the LLM provider")

    model_config = SettingsConfigDict(env_file=".env.enclave", env_file_encoding="utf-8", extra='ignore')

# Global instances (to be imported by respective components)
# Note: In a real TEE deployment, only one of these would likely be valid/loaded per process.
try:
    host_settings = HostSettings()
except Exception:
    host_settings = None

try:
    enclave_settings = EnclaveSettings()
except Exception:
    enclave_settings = None

