# src/signal_assistant/enclave/secure_config.py
from cryptography.fernet import Fernet

# In a real scenario, this key would be securely generated and exchanged, NOT hardcoded.
# This is for simulation/demonstration purposes only.
# Fernet keys must be 32 url-safe base64-encoded bytes.
SHARED_SYMMETRIC_KEY = Fernet.generate_key()

# KMS Master Key for encrypting/decrypting other keys within the KMS
# This key itself would need to be very securely managed (e.g., hardware-backed)
KMS_MASTER_KEY = Fernet.generate_key()

# Key for simulating Signal message encryption/decryption
SIGNAL_MESSAGE_KEY = Fernet.generate_key()
