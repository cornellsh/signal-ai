# Tasks: Secure Implementation

## Spec 1: Foundation
- [x] **Restructure:** Move code to `src/signal_assistant/host` and `src/signal_assistant/enclave`.
- [x] **Config:** Define distinct `HostSettings` and `EnclaveSettings`.
- [x] **Deps:** Split `pyproject.toml` dependencies.

## Spec 2: Host Sidecar
- [x] **Transport:** Implement VSock server (Host side) to accept Enclave connections.
- [x] **Proxy:** Implement the Signal WebSocket proxy (Host <-> Signal Service).
- [x] **Storage:** Implement the "Blind Blob Store" (Postgres wrapper).

## Spec 3: Enclave Core
- [x] **Bootstrap:** Implement VSock client (Enclave side).
- [x] **Signal:** Integate `libsignal` (FFI/Rust) inside the Enclave logic.
- [x] **Crypto:** Implement KMS/Sealing logic using AWS Nitro SDK (mocked for dev).
- [x] **Logic:** Move `BotOrchestrator` inside the Enclave boundary.

## Spec 4: Persistence
- [x] **Encryption:** Implement AES-GCM wrapper for state blobs.
- [x] **State Manager:** Implement the "Fetch Blob -> Decrypt -> Process -> Encrypt -> Push Blob" loop.