from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Signal Credentials
    signal_phone_number: str = Field(..., description="Phone number for the Signal account.")
    signal_password: str = Field(..., description="Password for the Signal account.")

    # LLM API Key
    llm_api_key: str = Field(..., description="API key for the external LLM service.")

    # Database Connection
    database_url: str = Field("sqlite:///./sql_app.db", description="URL for database connection.")

    # TEE Attestation Service Endpoint
    tee_attestation_service_endpoint: str | None = Field(
        None, description="Endpoint for the TEE attestation service (optional)."
    )

    # Metrics and Health (Keeping for now, might be removed later if not needed)
    metrics_host: str = Field("0.0.0.0", description="Host for Prometheus metrics.")
    metrics_port: int = Field(9000, description="Port for Prometheus metrics.")
    health_host: str = Field("0.0.0.0", description="Host for readiness/liveness server.")
    health_port: int = Field(8081, description="Port for readiness/liveness server.")
    health_timeout: float = Field(5.0, description="Timeout for startup health checks.")


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    """
    return Settings()