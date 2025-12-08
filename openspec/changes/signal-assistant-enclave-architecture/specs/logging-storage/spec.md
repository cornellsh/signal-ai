## ADDED Requirements

### Requirement: System SHALL NEVER Store Plaintext User Prompts/LLM Responses
The system shall never store plaintext user prompts or LLM responses persistently, neither within nor outside the enclave. After LLM inference and response generation, these shall be immediately purged from enclave memory.
#### Scenario: Prompt/Response Lifetime
Given a user prompt enters the enclave and an LLM response is generated,
When the response is encrypted for outbound transmission,
Then the plaintext prompt and response shall be purged from enclave memory and never written to any persistent storage, ensuring perfect forward secrecy for conversations.

### Requirement: System SHALL NEVER Store Signal-Encrypted Message Payloads Persistently
Signal-encrypted message payloads shall be transiently held in enclave memory only for decryption/encryption, and never persistently stored.
#### Scenario: Signal Payload Handling
Given an incoming Signal-encrypted message,
When the enclave decrypts it,
Then the original Signal-encrypted payload shall not be stored persistently within the enclave or on the host.

### Requirement: Identity Mappings SHALL Be Stored Encrypted with TTL
Identity mappings (`Signal_ID -> internal_user_id`) shall be stored in the enclave's secure storage on the host, encrypted with the Secure Storage Key, with an indefinite TTL unless explicitly deleted by the user.
#### Scenario: User Deletes Account
Given a user requests account deletion,
When the deletion process is initiated,
Then the `Signal_ID -> internal_user_id` mapping shall be irrevocably purged from the secure storage.



### Requirement: Host Operational Logs SHALL Be Non-Sensitive and Anonymized
Operational logs on the host shall only contain non-sensitive data, be anonymized to `internal_user_id`, and explicitly exclude plaintext user message content, Signal IDs, or LLM output.
#### Scenario: Host Logging an Event
Given the host records an event related to message processing,
When a log entry is created,
Then it shall include non-sensitive metadata (e.g., timestamp, `internal_user_id`, message size, processing duration, error codes),
And shall explicitly exclude any content related to the user's message or Signal ID.

### Requirement: Host Operational Logs SHALL Have Hard TTL
Host operational logs shall have a maximum retention period of 30 days, after which they shall be hard purged.
#### Scenario: Automated Log Purge
Given the system has operational logs older than 30 days,
When the log management system runs its scheduled purge,
Then these logs shall be irrevocably deleted from the host disk.

### Requirement: Enclave Secure Logs SHALL Be Ephemeral
Enclave secure logs shall be in-memory and ephemeral, purged on enclave shutdown or at very short intervals (e.g., 1 hour), and never written to persistent storage unless anonymized, encrypted, and adhering to host operational log TTLs.
#### Scenario: Enclave Debugging
Given the enclave needs to generate temporary debugging information,
When such information is created,
Then it shall reside in ephemeral, in-memory logs within the enclave,
And be purged automatically within a short timeframe (e.g., 1 hour),
And only be forwarded to host if it is anonymized, encrypted with a separate logging key, and adheres to a 30-day TTL.
