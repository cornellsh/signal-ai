# Privacy Core API Design

## 1. Introduction

This document formally defines the boundaries, interfaces, and APIs for the "Privacy Core" of the AI-Powered Signal Assistant. The Privacy Core is a critical, minimal set of code designed to execute within a Trusted Execution Environment (TEE). Its primary purpose is to handle sensitive operations related to Signal message processing and key management, ensuring the developer (and external entities) are technically unable to access plaintext user data or bot private keys.

## 2. Core Principles of the Privacy Core

*   **Minimality:** The codebase within the TEE is kept as small as possible to reduce the attack surface and simplify attestation.
*   **Confidentiality:** All sensitive data (encrypted messages, private keys) remains encrypted or is processed only within the TEE in plaintext.
*   **Integrity:** The TEE ensures that the Privacy Core's code has not been tampered with.
*   **Attestability:** Users can cryptographically verify the exact code running within the TEE.
*   **Limited Interface:** The API exposed by the Privacy Core is narrow and well-defined, minimizing potential leakage points.

## 3. Boundaries of the Privacy Core

The Privacy Core encompasses the following functionalities:

*   **Signal Message Decryption:** Receiving encrypted Signal messages from the external Event Processing Layer and decrypting them.
*   **Initial Prompt Sanitization (PII Stripping):** Analyzing decrypted messages to identify and remove Personally Identifiable Information (PII) before the message content is passed to external (non-TEE) components or LLM APIs.
*   **Signal Key Management:** Securely storing, using, and managing the bot's Signal private keys.
*   **Remote Attestation Integration:** Generating and facilitating the verification of attestation reports to confirm the integrity of the TEE and its loaded code.

The Privacy Core *does not* include:

*   Interaction with external LLM APIs (beyond passing sanitized prompts).
*   Long-term memory storage or retrieval (only short-term PII stripping).
*   Complex application logic or bot commands.
*   Database interactions (other than potentially storing attestation-related metadata).
*   Network communication beyond receiving encrypted Signal events and returning processed data.

## 4. Proposed Interfaces and APIs

The Privacy Core will expose a gRPC or similar high-performance, contract-first API to the external (non-TEE) Event Processing Layer. This ensures strict type enforcement and efficient cross-process communication.

### 4.1. `SignalPrivacyService`

This service handles the core message processing and key management.

#### `ProcessEncryptedMessage(request: ProcessEncryptedMessageRequest) returns (ProcessEncryptedMessageResponse)`

*   **Description:** Receives an encrypted Signal message, decrypts it, strips PII, and returns the sanitized message content or relevant metadata.
*   **`ProcessEncryptedMessageRequest`:**
    *   `encrypted_message_data`: `bytes` - The raw, encrypted Signal message payload.
    *   `sender_id`: `string` - The Signal ID of the sender.
    *   `timestamp`: `uint64` - The message timestamp.
*   **`ProcessEncryptedMessageResponse`:**
    *   `sanitized_message_text`: `string` - The message content after decryption and PII stripping.
    *   `message_type`: `enum` - (e.g., TEXT, ATTACHMENT, REACTION) - Type of the original message.
    *   `conversation_id`: `string` - Identifier for the conversation (e.g., group ID or sender ID).
    *   `is_pdl_stripped`: `bool` - Indicates if PII was detected and stripped.
    *   `error`: `string` (optional) - Error message if processing failed.

#### `GetAttestationReport(request: GetAttestationReportRequest) returns (GetAttestationReportResponse)`

*   **Description:** Returns the current attestation report from the TEE, allowing external verification of the Privacy Core's integrity.
*   **`GetAttestationReportRequest`:** (empty or includes nonce for freshness)
*   **`GetAttestationReportResponse`:**
    *   `report`: `bytes` - The raw TEE attestation report.
    *   `quote_signature`: `bytes` - Signature over the report.
    *   `public_key`: `bytes` - Public key associated with the TEE.
    *   `measurement_hash`: `bytes` - Hash of the code running within the TEE.

### 4.2. `KeyManagementService` (Internal to TEE, not exposed externally)

This service manages the bot's Signal private keys within the TEE. It will only expose internal APIs to other components *within* the Privacy Core.

*   `LoadPrivateKey(key_data: bytes)`: Securely loads a private key into the TEE.
*   `RotatePrivateKey()`: Manages key rotation securely.

## 5. Data Flow (Encrypted to Sanitized)

1.  External Event Processor receives encrypted Signal message.
2.  Event Processor calls `SignalPrivacyService.ProcessEncryptedMessage` with `encrypted_message_data`.
3.  Privacy Core (within TEE):
    *   Decrypts `encrypted_message_data` using securely stored Signal private key.
    *   Performs PII stripping on the decrypted plaintext.
    *   Returns `sanitized_message_text` and metadata.
4.  External AI Orchestration Layer receives `sanitized_message_text` and proceeds with LLM interaction.

## 6. Remote Attestation Workflow

1.  User (or external verifier) requests an attestation report from the bot.
2.  Bot's external component calls `SignalPrivacyService.GetAttestationReport`.
3.  Privacy Core (within TEE) generates a fresh attestation report (quote).
4.  Privacy Core returns the report, signature, public key, and code measurement hash.
5.  User's verification tool validates the report against expected measurements and the public key, confirming the Privacy Core's integrity.

## 7. Future Considerations

*   **Protocol Buffers/gRPC Definition:** Formal `.proto` files will be created for the defined services and messages.
*   **Error Handling:** Detailed error codes and handling strategies will be implemented.
*   **Versioning:** API versioning will be considered for future evolution.