# Tasks: Implement Privacy-Focused Signal Assistant Bot Architecture

This document outlines the actionable tasks required to implement the privacy-focused Signal assistant bot architecture as specified in `openspec/changes/refactor-privacy-arch-spec/specs/privacy-architecture/spec.md` and detailed in `openspec/changes/refactor-privacy-arch-spec/design.md`.

## Overall Setup & Infrastructure

1.  **Task:** [x] Research and select a specific TEE technology (e.g., Intel SGX, AMD SEV, AWS Nitro Enclaves) appropriate for the production environment.
    *   **Description:** Evaluate TEE options based on security features, performance, development tooling, and cloud provider support.
    *   **Verification:** Document the chosen TEE and rationale in a technical decision record (TDR).
2.  **Task:** [x] Establish a development environment for the chosen TEE.
    *   **Description:** Set up SDKs, compilers, and necessary tools for building and debugging TEE enclaves.
    *   **Verification:** Successfully compile and run a basic "hello world" enclave example.
3.  **Task:** [x] Define and implement the secure, attested communication channel between the Host and the Enclave.
    *   **Description:** Implement mechanisms for secure data exchange, ensuring integrity and confidentiality of communication between untrusted and trusted components.
    *   **Verification:** Demonstrate secure channel establishment and data transfer using TEE attestation mechanisms.

## Host Components Implementation

1.  **Task:** [x] Implement the Host Signal Transport Layer.
    *   **Description:** Develop the component responsible for receiving encrypted Signal messages and transmitting encrypted responses. Ensure it never stores plaintext message content or sensitive metadata beyond immediate processing.
    *   **Verification:** Unit tests confirming no sensitive data is logged or stored by the host transport layer. Integration tests with mock Signal server for message ingress/egress.
2.  **Task:** [x] Implement the Enclave Loader/Manager.
    *   **Description:** Develop the component to load, attest, and manage the lifecycle of the TEE enclave.
    *   **Verification:** Successfully load and attest the enclave, verifying its integrity measurement (attestation hash).
3.  **Task:** [x] Implement a Host-side API Gateway (if required by external services).
    *   **Description:** Create a strictly mediated gateway for the enclave to communicate with external services (e.g., persistent encrypted storage, specific external APIs for LLM dependencies).
    *   **Verification:** Access controls and mediation logic are correctly implemented and tested.
4.  **Task:** [x] Configure Host System Logging to be privacy-preserving.
    *   **Description:** Ensure host logs only contain non-sensitive operational data and explicitly exclude plaintext user messages, LLM prompts/responses, user IDs, or any linkable activity.
    *   **Verification:** Review log output and implement automated checks to prevent sensitive data leakage.

## Enclave Components Implementation

1.  **Task:** [x] Implement the Enclave Signal Message Handler.
    *   **Description:** Develop the component responsible for decrypting incoming Signal messages and encrypting outgoing responses using Signal session keys provisioned within the enclave's KMS.
    *   **Verification:** Unit tests for decryption/encryption logic. Integration tests with the Host Signal Transport Layer.
2.  **Task:** [x] Implement the Enclave Identity Mapper.
    *   **Description:** Develop the component to store and manage the mapping between Signal IDs and ephemeral internal `user_id`s exclusively within the enclave, subject to strict TTLs.
    *   **Verification:** Unit tests confirming identity mapping confidentiality and proper TTL enforcement.
3.  **Task:** [x] Integrate the LLM Orchestrator/Core Model within the Enclave.
    *   **Description:** Securely integrate the proprietary LLM model weights, inference logic, and any associated prompts/memory into the enclave environment.
    *   **Verification:** Successful execution of LLM inference within the TEE with protected model weights.
4.  **Task:** [x] Implement the Enclave-side Storage Manager.
    *   **Description:** Develop the component to encrypt/decrypt data for persistent storage on the host, using keys managed *within* the enclave.
    *   **Verification:** Unit tests for encryption/decryption of data blobs. Integration tests with host-side encrypted storage.
5.  **Task:** [x] Implement the Enclave Key Management System (KMS).
    *   **Description:** Develop the KMS to securely generate, store, and manage all cryptographic keys (Signal session keys, storage keys, attestation keys) within the enclave, leveraging forward secrecy.
    *   **Verification:** Unit tests confirming secure key generation, storage, and access controls. Demonstrate key rotation mechanisms.
6.  **Task:** [x] Implement the Privacy Policy Enforcer within the Enclave.
    *   **Description:** Develop logic to implement and enforce hard TTLs for all internal data and control what data can be logged or sent out of the enclave.
    *   **Verification:** Unit tests demonstrating automatic purging of data after TTL expiry and strict control over data egress.

## Data Flows Implementation

1.  **Task:** [x] Implement Signal Message Ingress data flow.
    *   **Description:** From Signal servers to Host Signal Transport Layer to Enclave. Ensure plaintext content is never exposed on the host.
    *   **Verification:** End-to-end integration test demonstrating secure message flow.
2.  **Task:** [x] Implement Enclave Ingress & Decryption data flow.
    *   **Description:** Encrypted Signal message to Enclave, decryption and extraction of sender's Signal ID.
    *   **Verification:** Unit tests within enclave for decryption.
3.  **Task:** [x] Implement LLM Processing data flow.
    *   **Description:** Plaintext message and `user_id` to LLM, generation of response within the enclave.
    *   **Verification:** Integration tests ensuring LLM processes queries correctly within the enclave.
4.  **Task:** [x] Implement Response Encryption & Enclave Egress data flow.
    *   **Description:** Plaintext LLM response to Enclave Signal Message Handler, encryption, and secure transfer to Host Signal Transport Layer.
    *   **Verification:** End-to-end integration test demonstrating secure response flow.
5.  **Task:** [x] Implement Signal Message Egress data flow.
    *   **Description:** Host Signal Transport Layer transmits encrypted response to Signal servers.
    *   **Verification:** Integration test with mock Signal server for outgoing messages.

## Strict Rules for Identity Binding

1.  **Task:** [x] Ensure Identity Mapper adheres to mapping location rules.
    *   **Description:** Verify that all Signal ID to `user_id` mappings are generated and stored exclusively within the enclave.
    *   **Verification:** Code review and unit tests.
2.  **Task:** [x] Implement anonymization for internal `user_id`s.
    *   **Description:** Ensure `user_id`s are ephemeral, randomly generated, and contain no PII.
    *   **Verification:** Code review and unit tests.
3.  **Task:** [x] Implement strict plaintext exposure prevention for identity mappings.
    *   **Description:** Ensure the host environment never accesses plaintext `(Signal ID -> user_id)` mappings.
    *   **Verification:** Penetration testing simulation and code review.
4.  **Task:** [x] Enforce TTLs for identity mappings.
    *   **Description:** Implement automatic purging of identity mappings after defined TTLs (e.g., 24-72 hours).
    *   **Verification:** Unit tests for TTL enforcement and purging logic.

## Concrete Key Management and Rotation

1.  **Task:** [x] Implement Enclave Attestation Key management.
    *   **Description:** Secure generation, storage (hardware-backed), rotation, and accessibility controls for attestation keys.
    *   **Verification:** Attestation report verification and secure key access tests.
2.  **Task:** [x] Implement Signal Session Key management.
    *   **Description:** Secure generation/derivation, storage (volatile, encrypted), and rotation for Signal session keys within the enclave KMS, leveraging Signal Protocol forward secrecy.
    *   **Verification:** Unit tests for key lifecycle and forward secrecy.
3.  **Task:** [x] Implement Storage Encryption Key management.
    *   **Description:** Secure generation (from TEE sealing key), storage, and rotation (DEKs) for storage encryption keys within the enclave KMS.
    *   **Verification:** Unit tests for key generation, wrapping, and rotation. Ensure encrypted blobs are unreadable without enclave-internal keys.

## Logging and Storage Behavior with Hard TTLs

1.  **Task:** [x] Implement privacy-preserving Host Logging.
    *   **Description:** Ensure host logs exclude all sensitive data (plaintext messages, user IDs, etc.).
    *   **Verification:** Automated log scanning and code review.
2.  **Task:** [x] Implement sensitive Enclave Logging.
    *   **Description:** Implement mechanisms for sensitive logs to be either immediately discarded or encrypted with an enclave-generated key (not shared with host) before emission, with extremely short TTLs.
    *   **Verification:** Unit tests for enclave logging behavior and secure log handling.
3.  **Task:** [x] Implement Conversation History storage with hard TTLs.
    *   **Description:** Store conversation history as encrypted blobs on the host, with a maximum 72-hour configurable TTL, automatically purged by the enclave's Storage Manager.
    *   **Verification:** Integration tests for storage, encryption, and automatic purging.
4.  **Task:** [x] Ensure Identity Mapping storage adheres to TTLs.
    *   **Description:** Store identity mappings within the enclave (volatile or encrypted persistent) with a maximum 72-hour TTL.
    *   **Verification:** Unit tests for identity mapping TTLs.
5.  **Task:** [x] Implement secure LLM Model Weights storage.
    *   **Description:** Store model weights as encrypted blobs on the host, decrypted only within the enclave.
    *   **Verification:** Ensure model weights are protected at rest and in transit.
6.  **Task:** [x] Implement checks to ensure no prohibited data is stored.
    *   **Description:** Verify that raw/unhashed Signal IDs, plaintext messages, plaintext identity mappings, or any PII not essential for immediate conversation are never persistently stored outside the enclave or beyond their TTL.
    *   **Verification:** Code review, security audits, and automated data flow analysis.

## Transparent Law Enforcement Disclosure Policy (Documentation & Verification)

1.  **Task:** [x] Document the technical limitations of data disclosure to law enforcement.
    *   **Description:** Create formal documentation outlining what data can and cannot be disclosed, based on the implemented architecture.
    *   **Verification:** Review documentation against the implemented system and architectural principles.
2.  **Task:** [x] Implement mechanisms for public verifiability of attestation hash changes.
    *   **Description:** Ensure that any change to the enclave's attestation hash (e.g., due to software updates that could impact privacy guarantees) is publicly verifiable.
    *   **Verification:** Develop a process and tooling for users/auditors to verify the attestation hash.

## Verification & Testing

1.  **Task:** [x] Develop comprehensive unit tests for all enclave and host components.
    *   **Description:** Ensure individual components function correctly and adhere to privacy requirements.
    *   **Verification:** Achieve high unit test coverage.
2.  **Task:** [x] Develop integration tests for data flows and component interactions.
    *   **Description:** Verify secure and correct communication between host and enclave, and proper data handling.
    *   **Verification:** Successful execution of integration test suite.
3.  **Task:** [x] Conduct security audits and penetration testing.
    *   **Description:** Identify potential vulnerabilities and ensure the system withstands attacks targeting privacy.
    *   **Verification:** Successful completion of security audits with findings addressed.
4.  **Task:** [x] Implement continuous attestation verification.
    *   **Description:** Continuously monitor the enclave's attestation status to detect any tampering or unauthorized changes.
    *   **Verification:** Develop monitoring and alerting systems for attestation failures.