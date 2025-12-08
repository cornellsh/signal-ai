## ADDED Requirements

### Requirement: System SHALL NOT Provide Historical Plaintext User Messages
The system shall be unable to provide historical plaintext user messages (prompts/responses) to law enforcement, as these are never stored persistently.
#### Scenario: Law Enforcement Request for Past Conversations
Given a legal order for historical plaintext conversations,
When the request is evaluated against the system's capabilities,
Then the system shall confirm that no such data exists or can be retrieved, due to its ephemeral nature.

### Requirement: System SHALL NOT Provide Signal IDs Linked to Conversation Content
The system shall be unable to provide Signal IDs linked to conversation content, as the identity binding strategy ensures Signal IDs are never associated with stored conversation metadata.
#### Scenario: Law Enforcement Request for Signal ID-Content Link
Given a legal order requests specific Signal IDs linked to particular conversation content,
When the request is evaluated,
Then the system shall confirm that such linkages are not maintained or retrievable.

### Requirement: System SHALL NOT Provide Encrypted LLM Prompts/Responses
The system shall be unable to provide encrypted LLM prompts or responses, as these are never stored persistently, even in encrypted form.
#### Scenario: Law Enforcement Request for Encrypted Prompts
Given a legal order requests stored encrypted LLM prompts or responses,
When the request is evaluated,
Then the system shall confirm that no such data is stored.

### Requirement: System SHALL Provide Limited Host Operational Logs
The system can provide limited host operational logs (timestamps, `internal_user_id`, message sizes, error codes) for up to 30 days, which do not contain conversation content or direct Signal IDs.
#### Scenario: Law Enforcement Request for Operational Metadata
Given a legal order requests operational metadata for a specific time period,
When the request is fulfilled,
Then the system shall provide host operational logs containing only non-sensitive, anonymized metadata up to 30 days old.

### Requirement: System SHALL Provide Proof of Communication
The system can provide confirmation that communication occurred between the bot and a specific Signal ID at a certain time, without revealing content or purpose.
#### Scenario: Law Enforcement Request for Communication Confirmation
Given a legal order requests confirmation of communication with a specific Signal ID,
When the request is fulfilled,
Then the system shall provide records indicating communication events (e.g., message receipt/send timestamps with `internal_user_id`), but no content.

### Requirement: System SHALL Provide Identity Mappings from Running Enclave
If a valid legal order specifically targets the mapping for a known `internal_user_id` or `Signal_ID`, and the enclave is running, the system can retrieve this mapping from within the running enclave via a specific enclave API call.
#### Scenario: Law Enforcement Request for Identity Mapping
Given a legal order targets an identity mapping for a known `internal_user_id` or `Signal_ID`,
When the enclave is running and the request is processed through a secure API,
Then the enclave shall provide the direct `Signal_ID -> internal_user_id` mapping.
And if the enclave is not running or its secure storage is purged, this mapping shall not be recoverable.

### Requirement: Fundamental Enclave Changes SHALL Be Required for Prospective Wiretapping
To enable real-time plaintext access to conversations (prospective wiretapping), fundamental changes to the enclave code and its attestation shall be required.
#### Scenario: Regulatory Demand for Wiretapping Capability
Given a regulatory demand for prospective wiretapping capability,
When the system is evaluated,
Then it shall be determined that a new enclave build, with a different cryptographic attestation hash, explicitly designed for this purpose, would be necessary.

### Requirement: System SHALL NOT Allow Covert Wiretapping Capability
It shall not be possible to covertly alter the enclave's behavior to enable wiretapping without invalidating the attestation and making the change publicly detectable.
#### Scenario: Attestation Verification After Alleged Covert Change
Given an external party attempts to verify the enclave's attestation after an alleged covert wiretapping change,
When remote attestation is performed,
Then the attestation report shall reflect a changed cryptographic measurement, indicating a modification to the enclave's code or configuration, making the change detectable.

### Requirement: Transparency SHALL Be Maintained for Wiretapping Deployment
The organization shall commit to never deploying an enclave with wiretapping capabilities without explicit, public changes to the software, new attestations, and full transparency to its users.
#### Scenario: Deployment of Wiretapping-Enabled Enclave
Given a wiretapping-enabled enclave is considered for deployment,
When deployment occurs,
Then customers shall be explicitly notified, and the deployment shall be accompanied by public changes to the software and new attestations that are verifiable by users.
