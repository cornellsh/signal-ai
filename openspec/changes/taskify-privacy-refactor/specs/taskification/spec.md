## ADDED Requirements
### Requirement: Privacy-Focused Signal Assistant Architecture
The system SHALL adhere to a privacy-centric architecture for the Signal assistant bot, specifically designed around a Trusted Execution Environment (TEE) to minimize data exposure and provide strong guarantees against government tracking.

#### Scenario: Architecture Overview
- **WHEN** reviewing the system design
- **THEN** the architecture SHALL explicitly define threat models, goals, TEE component responsibilities, data flows, identity binding, key management, logging/storage policies, and a law enforcement disclosure framework as detailed in `design.md`.

### Requirement: TEE-Based Data Protection
Sensitive user data, LLM models, and cryptographic keys SHALL be processed and managed exclusively within the attested TEE enclave to protect them from the host environment.

#### Scenario: Data Visibility
- **WHEN** an administrator inspects the host system
- **THEN** they SHALL NOT observe plaintext user messages, LLM prompts, LLM responses, Signal session keys, storage encryption keys, or identity mappings. These SHALL only be visible in plaintext within the enclave.

### Requirement: Strict Identity Binding and Anonymization
User identities (Signal IDs/phone numbers) SHALL be mapped to ephemeral, internal `user_id`s exclusively within the enclave, and this mapping SHALL never be exposed to the host in plaintext.

#### Scenario: Identity Mapping Confidentiality
- **WHEN** a user interacts with the bot
- **THEN** the mapping between their Signal ID and the internal `user_id` used for conversation history SHALL be stored only within the enclave, subject to strict TTLs, and SHALL NOT be accessible in plaintext by the host.

### Requirement: Robust Key Management and Rotation
All cryptographic keys essential for privacy (Signal session keys, storage keys, attestation keys) SHALL be securely generated, stored, and managed within the enclave's Key Management System (KMS), leveraging forward secrecy where applicable.

#### Scenario: Key Protection
- **WHEN** keys are used for encryption or decryption
- **THEN** they SHALL be handled exclusively by the enclave's KMS and SHALL NEVER be exposed in plaintext outside the enclave.

### Requirement: Data Minimization and Hard TTLs
All logs and stored data SHALL adhere to principles of data minimization and strict Time-To-Live (TTL) policies, ensuring sensitive information is purged automatically after defined periods.

#### Scenario: Conversation History Deletion
- **WHEN** a conversation history encrypted blob reaches its configured TTL (e.g., 72 hours)
- **THEN** it SHALL be automatically purged from storage by the enclave's Storage Manager or flagged for host-side deletion, making it irrecoverable.

### Requirement: Transparent Law Enforcement Disclosure Policy
The system SHALL have an explicit and transparent policy detailing what data can and cannot be disclosed to law enforcement, based on technical and architectural limitations, with clear identification of conditions required for prospective tracking.

#### Scenario: Response to Subpoena for Plaintext Data
- **WHEN** a legally binding order requests historical plaintext user messages
- **THEN** the service provider SHALL NOT be able to provide such data, as it is fundamentally designed not to possess or decrypt it historically, and any attempt to enable prospective access would require a publicly verifiable change to the enclave's attestation hash.