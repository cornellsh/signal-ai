## ADDED Requirements

### Requirement: Signal IDs SHALL Never Be Linked to Internal Activity Outside Enclave
Signal IDs (phone numbers) shall never be directly linked to internal user activity or stored in plaintext outside the enclave.
#### Scenario: Host Observes User Activity
Given the host monitors activity related to the bot,
When the host logs or processes events related to user interactions,
Then any identifiers associated with these events shall be `internal_user_id` and shall not be the user's Signal ID or phone number.

### Requirement: Enclave SHALL Generate Opaque Internal User IDs
When a new Signal ID interacts with the bot, the enclave shall generate a cryptographically secure, random, and opaque `internal_user_id`.
#### Scenario: First Interaction of a New User
Given a Signal ID initiates communication with the bot for the first time,
When the enclave receives and processes this initial message,
Then the enclave shall generate a unique, random, and opaque `internal_user_id` for that Signal ID.

### Requirement: Identity Mapping SHALL Be Stored Only Within Enclave's Secure Storage
The mapping between `Signal_ID` and `internal_user_id` shall be stored exclusively within the enclave's secure storage, encrypted with an enclave-specific key, and this storage shall be attested and bound to the enclave.
#### Scenario: Persistent Storage of Mapping
Given an `internal_user_id` has been generated for a `Signal_ID`,
When this mapping is persisted,
Then it shall be stored only within the enclave's secure, attested, and bound storage,
And it shall be encrypted using a key held solely by the enclave.

### Requirement: Host SHALL Only See Internal User IDs
The host environment shall only ever see `internal_user_id` when interacting with the enclave (e.g., requesting LLM inference for a specific user), and shall never see the associated Signal ID.
#### Scenario: Host Calls Enclave API for LLM Inference
Given the host needs the enclave to perform LLM inference for a user,
When the host makes an API call to the enclave's LLM inference service,
Then the host shall provide the `internal_user_id` as the user identifier,
And the host shall not provide, nor have access to, the user's Signal ID for this operation.

### Requirement: Identity Mappings SHALL Be Lost on Enclave Destruction Without Secure Storage
If the enclave is destroyed or re-provisioned without its secure storage, all identity mappings shall be lost, requiring users to re-bind their identities (appearing as new users to the bot).
#### Scenario: Enclave Redeployment Without Data Migration
Given an enclave is redeployed without migrating its secure storage containing identity mappings,
When a previously known Signal ID interacts with the bot,
Then the enclave shall treat this Signal ID as a new user, generating a new `internal_user_id`,
And the bot shall not recognize the user's past interactions.
