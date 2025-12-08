# Design Document: Signal Assistant Bot Enclave Architecture

## 1. Introduction and Goals

This document outlines the architecture for a privacy-focused commercial Signal assistant bot, leveraging Trusted Execution Environments (TEEs) to minimize data exposure. The primary goal is to build an assistant that can interact with users via Signal, with its core logic within a secure, verifiable enclave that securely interacts with external Large Language Model (LLM) APIs.

**Core Goals:**
1.  **Maximize User Privacy:** Minimize the plaintext data accessible to the host environment and third parties.
2.  **Verifiable Security:** Enable independent verification of the code running within the enclave through remote attestation.
3.  **Regulatory Compliance & Transparency:** Clearly define data handling, retention policies, and capabilities/limitations for law enforcement requests.
4.  **Operational Resilience:** Design for robust key management, secure storage, and efficient operation at LLM scale.
5.  **Implementation Readiness:** Provide a detailed design sufficient for senior engineers to implement.

## 2. Threat Model

Our threat model assumes a sophisticated adversary with the following capabilities:
*   **Malicious Host Operator:** The cloud provider or a compromised host operator has full control over the physical server and the host OS. They can inspect memory, storage, network traffic outside the enclave, and attempt to manipulate the enclave's inputs/outputs.
*   **Network Eavesdropper:** An adversary can intercept all network traffic between the user, Signal servers, and our host/enclave.
*   **Compromised External Systems:** Dependencies outside the core Signal network (e.g., identity providers, billing systems) could be compromised.
*   **Insider Threat:** Malicious employees within our organization, or contractors, may attempt to access sensitive user data.
*   **Zero-day Exploits:** While TEEs are designed to mitigate certain classes of attacks, we acknowledge the possibility of novel vulnerabilities in the TEE hardware or software stack.

**Out of Scope (for this document, but critical for overall security):**
*   Signal protocol vulnerabilities.
*   Client-side Signal application vulnerabilities.
*   Side-channel attacks beyond typical TEE protections (e.g., Rowhammer, Spectre/Meltdown variants not mitigated by TEE).
*   Denial of Service (DoS) attacks.

## 3. Architectural Overview: Enclave vs. Host Separation

The architecture is strictly enclave-centric. The principle is: **sensitive data and logic reside exclusively within the TEE.**

### Host (Untrusted Environment)
The host machine, running a standard OS (e.g., Linux), is considered untrusted. Its primary roles are:
*   **Resource Provisioning:** Allocate CPU, memory, network, and storage resources to the enclave.
*   **Enclave Management:** Launch, attest, and monitor the enclave.
*   **Secure Channel Termination (Pre-enclave):** Terminate TLS connections from Signal servers. This is a necessary compromise as Signal traffic is not directly TEE-aware. However, *all sensitive data is immediately re-encrypted for the enclave*.
*   **Proxy/Multiplexer:** Forward encrypted messages and commands to the enclave and relay encrypted responses back out.
*   **Persistent Encrypted Storage:** Provide block storage that the enclave can encrypt/decrypt with its own keys.
*   **External Service Orchestration:** Manage connections to external services *only* under strict enclave control and with appropriate encryption.
*   **Billing/Operational Logic:** Handle non-sensitive operational aspects.

**Data on Host (Always encrypted or non-sensitive):**
*   Encrypted Signal message payloads (before re-encryption for enclave, after decryption from Signal).
*   Enclave encrypted data-at-rest.
*   Public keys for attestation verification.
*   Configuration data that does not contain secrets.
*   Application logs (see Logging section).

### Enclave (Trusted Execution Environment)
The enclave is the trusted core where all sensitive operations occur. It is designed to be highly specialized and minimize its attack surface.

**Components within Enclave:**
*   **Signal Protocol Stack:** Handle Signal message decryption/encryption using enclave-held keys.
*   **Identity Mapping Service:** Securely bind Signal IDs to internal user IDs.
*   **Assistant Bot Logic:** The core business logic for processing user requests.
*   **LLM API Proxy/Client:** Securely connect to and interact with external third-party LLM APIs.
*   **Key Management Service (KMS):** Generate, store, and manage all cryptographic keys used within the enclave.
*   **Secure Storage Interface:** Encrypt and decrypt data for persistent storage on the host.
*   **Attestation Logic:** Generate and verify remote attestations.
*   **Secure Logging Proxy:** Forward encrypted, anonymized logs to the host.

**Data in Enclave (Plaintext or Decrypted):**
*   Signal keys (identity keys, session keys).
*   Internal user IDs.
*   Plaintext user messages.
*   LLM API keys/credentials (encrypted at rest, decrypted in memory for API calls).
*   LLM prompts and responses (plaintext within the enclave, only transiently during API call preparation and processing).
*   Enclave-generated keys (storage keys, identity binding keys).
*   Ephemeral session data.

## 4. Detailed Data Flows

### 4.1. Inbound Message Flow (Signal Server → User → Signal Server → Host → Enclave)

1.  **User to Signal Server:** User sends an encrypted message to the bot's Signal ID.
2.  **Signal Server to Bot Host:** Signal server delivers the encrypted message to the bot's host (webhook or persistent connection). The message payload is encrypted end-to-end by Signal, but the transport is typically TLS terminated at the host.
3.  **Host Processing:**
    *   Host receives the Signal-encrypted message (Signal's Double Ratchet).
    *   Host immediately re-encrypts the *entire* Signal-encrypted message payload using an enclave-specific symmetric key (established via a secure channel after attestation) and sends it to the enclave via an IPC mechanism (e.g., shared memory, local socket). The host never sees the plaintext Signal message.
4.  **Enclave Ingress:**
    *   Enclave decrypts the host-encrypted payload using its symmetric key.
    *   Enclave uses its internal Signal protocol stack to decrypt the actual user message using its Signal identity and session keys.
    *   **Identity Binding:** The Signal sender ID/phone number is used to look up or create an internal, anonymized user ID. This mapping occurs ONLY inside the enclave.
    *   **LLM Processing:** The plaintext user message (prompt) is fed to the LLM API Proxy/Client.
    *   **Response Generation:** The LLM API returns a response.
    *   **Secure Logging:** Relevant, anonymized data is securely logged (see Logging section).

### 4.2. Outbound Message Flow (Enclave → Host → Signal Server → User)

1.  **Enclave Egress:**
    *   The LLM-generated response, along with the recipient Signal ID, is encrypted by the enclave's Signal protocol stack using the appropriate Signal session keys.
    *   The Signal-encrypted response is then re-encrypted by the enclave using the host-specific symmetric key for transport back to the host.
2.  **Host Processing:**
    *   Host receives the host-encrypted Signal message.
    *   Host decrypts the host-encrypted message to retrieve the Signal-encrypted payload.
    *   Host transmits the Signal-encrypted message to the Signal server for delivery to the user.
3.  **Signal Server to User:** Signal server delivers the encrypted message to the user.

## 5. Identity Binding

Identity binding is a critical privacy boundary.
*   **Principle:** Signal IDs (phone numbers) are never directly linked to internal user activity or stored in plaintext outside the enclave.
*   **Internal ID Generation:** When a new Signal ID interacts with the bot, the enclave generates a cryptographically secure, random, and opaque `internal_user_id`.
*   **Mapping Storage:** The mapping `(Signal_ID, internal_user_id)` is stored *only within the enclave's secure storage*, encrypted with an enclave-specific key. This storage is attested and bound to the enclave.
*   **Host Visibility:** The host only ever sees `internal_user_id` when interacting with the enclave (e.g., requesting LLM inference for a specific user). It never sees the associated Signal ID.
*   **Implications:** If the enclave is destroyed or re-provisioned without its secure storage, all identity mappings are lost, and users would appear as new to the bot (requiring re-binding). This is an explicit design choice for privacy.

## 6. Key Management and Rotation

All keys are managed by an Enclave Key Management Service (KMS).

### 6.1. Enclave Root Key
*   **Derivation:** Derived from the TEE's unique hardware-backed key (e.g., Intel SGX Seal Key, AMD SEV-SNP Guest Owner Key). This key never leaves the enclave.
*   **Purpose:** Encrypts all other enclave-generated keys at rest.

### 6.2. Signal Keys
*   **Identity Keys:** Generated securely within the enclave upon bot registration with Signal. Never leave the enclave.
*   **Pre-Keys:** Generated and rotated within the enclave.
*   **Session Keys:** Established and managed by the Signal protocol stack within the enclave for each conversation. Provide forward secrecy.
*   **Storage:** Signal keys are stored encrypted (using the Enclave Root Key) within the enclave's persistent secure storage.

### 6.3. Enclave Data Encryption Keys
*   **Host-Enclave Transport Key:** A short-lived, ephemeral symmetric key established via a secure authenticated channel (e.g., TLS with mutual attestation or a bespoke attestation-bound key exchange) between the host proxy and the enclave. Rotated frequently (e.g., per session or per hour). Used for immediate re-encryption of Signal payloads between host and enclave.
*   **Secure Storage Key:** A symmetric key generated by the enclave and used to encrypt all persistent data stored on the host's disk (e.g., identity mappings). This key is encrypted by the Enclave Root Key when at rest.

### 6.4. Key Rotation
*   **Signal Session Keys:** Automatically handled by the Signal protocol (Double Ratchet).
*   **Host-Enclave Transport Key:** Rotated frequently as part of the secure channel setup.
*   **Secure Storage Key:** Rotated periodically (e.g., monthly). Requires re-encrypting all affected data.
*   **Identity Keys:** Rotated periodically (e.g., annually) or upon suspected compromise, requiring re-registration with Signal.

## 7. Logging and Storage Behavior

**Principle:** Log and store only what is strictly necessary, always encrypted if sensitive, and with explicit TTLs.

### 7.1. What We NEVER Store (Plaintext or Encrypted)
*   **Raw User Prompts/LLM Responses:** After LLM inference and response generation, the plaintext prompts and responses are immediately purged from enclave memory. They are never written to any persistent storage, even encrypted. This ensures perfect forward secrecy for conversations.
*   **Signal-encrypted message payloads:** These are transiently held in enclave memory only for decryption/encryption, never persistently stored.

### 7.2. What We Store (Encrypted with Hard TTLs)

All persistent storage happens on the untrusted host, encrypted by enclave-generated keys.

*   **Identity Mappings (`Signal_ID -> internal_user_id`):**
    *   **Location:** Enclave's secure storage on host, encrypted with Secure Storage Key.
    *   **Content:** Pairings of Signal ID and internal user ID.
    *   **TTL:** Indefinite, unless user explicitly requests deletion. On user deletion, the mapping is irrevocably purged from secure storage.
*   **Operational Logs (Host):**
    *   **Location:** Host disk.
    *   **Content:** Non-sensitive operational data, such as:
        *   Timestamp of message receipt/send.
        *   `internal_user_id` (NOT Signal ID).
        *   Message size.
        *   Processing duration (enclave time).
        *   Error codes.
        *   Attestation verification logs.
    *   **Privacy:** No plaintext user message content, Signal IDs, or LLM output is ever included. All content-related data is anonymized to the `internal_user_id`.
    *   **TTL:** Max 30 days for debugging/auditing purposes. Hard purged thereafter.
*   **Enclave Secure Logs (Within Enclave):**
    *   **Location:** In-memory, ephemeral.
    *   **Content:** Debugging information *within the enclave*, potentially including partial, ephemeral plaintext data for immediate debugging.
    *   **TTL:** Purged on enclave shutdown or at very short intervals (e.g., 1 hour). Never written to persistent storage. Can be forwarded to host *only* if anonymized and encrypted with a separate logging key that is distinct from the primary secure storage key, and falls under the operational logs TTL.

## 8. Law Enforcement Section: Capabilities and Limitations

This section explicitly states what data we can and cannot provide to law enforcement, assuming a properly functioning, attested enclave architecture.

### 8.1. Historical Data Access
**What We CANNOT Provide (Retrospective):**
*   **Plaintext User Messages (Prompts/Responses):** We never store plaintext conversation content, even encrypted. Once processed, it is purged from memory. Therefore, we cannot provide historical plaintext messages under any circumstances.
*   **Signal IDs linked to Conversation Content:** Due to the identity binding strategy, Signal IDs are never linked to any stored conversation metadata.
*   **Encrypted LLM Prompts/Responses:** As noted, these are never stored, even encrypted.

**What We CAN Provide (Retrospective):**
*   **Operational Logs (Host):** Limited metadata (timestamps, `internal_user_id`, message sizes, error codes) for up to 30 days. This data does NOT contain conversation content or direct Signal IDs.
*   **Proof of Communication:** We can confirm that communication occurred between our bot and a specific Signal ID at a certain time, but without revealing content or purpose of the communication.
*   **Identity Mappings (`internal_user_id` to `Signal_ID`):** If a valid legal order specifically targets the mapping for a known `internal_user_id` or `Signal_ID`, and the enclave is running, we *could* retrieve this mapping *from within the running enclave*. However, this would require a specific enclave API call and could only provide the direct mapping, not any associated conversation data. If the enclave is not running, or if its secure storage has been purged, this mapping cannot be recovered.

### 8.2. Prospective Wiretapping (Live Content Access)

**What is REQUIRED for Prospective Wiretapping:**
To enable real-time plaintext access to conversations, *fundamental changes to the enclave code and its attestation would be required.* This means:

1.  **New Enclave Build:** A new version of the enclave software would need to be developed, specifically designed to:
    *   Store plaintext messages persistently.
    *   Exfiltrate plaintext messages to the host or a third party.
    *   Or, modify the identity mapping to expose Signal IDs directly.
2.  **New Attestation Hash:** This new enclave build would have a completely different cryptographic measurement (attestation hash).
3.  **Customer Consent/Notification:** Deployment of such an enclave would invalidate all previous attestations and fundamentally change the privacy guarantees. Users/customers would need to be explicitly notified, and in most cases, actively consent to such a change, as the integrity of the system would be verifiably altered.
4.  **No Covert Change:** Due to the nature of remote attestation, it is *not possible* to covertly alter the enclave's behavior to enable wiretapping without invalidating the attestation and making the change publicly detectable by anyone verifying the attestation.

**Our Policy:** We commit to never deploying an enclave with wiretapping capabilities without explicit, public changes to the software, new attestations, and full transparency to our users.

## 9. Considerations for LLM-Scale Workloads

The use of TEEs for securely interacting with external LLM APIs introduces unique considerations.
*   **Memory:** Enclaves have limited memory.
*   **Performance:** Cryptographic operations (message re-encryption) and TEE context switching add latency. Optimize IPC between host and enclave. Batching requests to the LLM API within the enclave can amortize overheads.
*   **Model Confidentiality:** The primary goal is that user prompts/responses remain confidential from the host. Enclave ensures this by processing prompts/responses in plaintext *only* within the TEE before sending to a third-party LLM API.
*   **Cost:** TEE instances are typically more expensive than standard VMs. Optimize resource utilization.

## 10. Conclusion

This architecture provides a robust framework for a privacy-preserving Signal assistant bot, leveraging TEEs to establish strong privacy guarantees. By strictly isolating sensitive data and logic within the enclave, we can provide a high degree of assurance against host compromise and retrospective government tracking, while maintaining transparency about the system's capabilities and limitations. Implementation will require careful attention to secure engineering practices, especially around attestation, key management, and the host-enclave interface.
