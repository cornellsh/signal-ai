## ADDED Requirements

### Requirement: Host SHALL Re-encrypt Signal Payload for Enclave
Upon receiving a Signal-encrypted message, the host SHALL immediately re-encrypt the entire Signal-encrypted payload using an enclave-specific symmetric key (established via a secure channel after attestation) before sending it to the enclave.
#### Scenario: Host Re-encryption on Message Receipt
Given the host receives a Signal-encrypted message from Signal servers,
When the host processes this message for enclave delivery,
Then the host shall re-encrypt the full Signal-encrypted message payload,
And the host shall use an enclave-specific symmetric key for this re-encryption.
And the host shall not decrypt the original Signal message payload at any point.

### Requirement: Host SHALL Use IPC for Enclave Communication
The host SHALL utilize a secure Inter-Process Communication (IPC) mechanism (e.g., shared memory, local socket) to send the host-encrypted Signal payload to the enclave.
#### Scenario: IPC Mechanism Usage
Given the host has re-encrypted a Signal message payload for the enclave,
When the host transmits this re-encrypted payload,
Then the host shall send it to the enclave via an established IPC channel.

### Requirement: Enclave SHALL Decrypt Host-Encrypted Payload
The enclave SHALL decrypt the host-encrypted payload using its symmetric key upon ingress.
#### Scenario: Enclave Decrypts Host Payload
Given the enclave receives a host-encrypted message payload via IPC,
When the enclave processes the incoming payload,
Then the enclave shall successfully decrypt it using the pre-established host-enclave symmetric key.

### Requirement: Enclave SHALL Decrypt Signal Message
The enclave SHALL utilize its internal Signal protocol stack and enclave-held Signal keys to decrypt the actual user message.
#### Scenario: Signal Message Decryption within Enclave
Given the enclave has decrypted the host-encrypted payload, revealing the Signal-encrypted message,
When the enclave processes this Signal-encrypted message,
Then the enclave's Signal protocol stack shall decrypt the user message using its identity and session keys,
And the plaintext user message shall become accessible only within the enclave.

### Requirement: Enclave SHALL Perform Identity Binding
The enclave SHALL perform identity binding, using the Signal sender ID/phone number to look up or create an `internal_user_id`, with this mapping occurring exclusively inside the enclave.
#### Scenario: New User Interaction
Given a user with a new Signal ID interacts with the bot,
When the enclave processes the incoming message,
Then the enclave shall generate a cryptographically secure, random, and opaque `internal_user_id` for this Signal ID,
And the mapping of `(Signal_ID, internal_user_id)` shall be created and stored *only* within the enclave's secure storage.

### Requirement: Enclave SHALL Process LLM Interaction
The plaintext user message (prompt) SHALL be fed to the LLM API Proxy/Client within the enclave to generate a response.
#### Scenario: LLM Response Generation
Given the enclave has decrypted a user message to plaintext,
When the enclave processes this plaintext message,
Then the plaintext message shall be provided as a prompt to the LLM API Proxy/Client running inside the enclave,
And the LLM API shall return a response to the enclave.

### Requirement: Enclave SHALL Perform Secure Logging for Inbound Messages
After processing, relevant and anonymized data related to the inbound message SHALL be securely logged within the enclave (as per logging requirements).
#### Scenario: Inbound Message Logging
Given an inbound message has been processed by the enclave,
When logging occurs for this event,
Then the enclave shall generate log entries containing anonymized data (e.g., `internal_user_id`, message size, processing time),
And these log entries shall be handled according to the secure logging specifications.
