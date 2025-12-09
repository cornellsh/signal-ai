# Signal Assistant Core Specification

## 1. Introduction: Purpose and Target Users

The Signal Assistant MUST provide secure, AI-powered conversational assistance directly within the Signal messaging platform. Its core mission MUST be to enhance user productivity and information access while upholding Signal's paramount commitment to privacy and security through the use of Trusted Execution Environments (TEEs).

### 1.1 Purpose
*   **Requirement 1.1.1:** The Assistant MUST provide AI-powered conversational capabilities within the Signal ecosystem.
*   **Requirement 1.1.2:** The Assistant MUST operate with a primary focus on user privacy and security, leveraging TEEs as a fundamental architectural component.

### 1.2 Target Users
*   **Requirement 1.2.1:** The primary target users for the initial release SHALL be individual Signal users seeking an intelligent assistant that respects their privacy.
*   **Requirement 1.2.2:** Future extensions MAY cater to organizational use cases, but this is outside the scope of the current specification.

## 2. Primary Use Cases and Interaction Patterns

The Signal Assistant MUST facilitate a defined set of secure and private interactions.

### 2.1 Use Cases
*   **Requirement 2.1.1 (Answering Questions):** Users MUST be able to ask general knowledge questions or seek information.
*   **Requirement 2.1.2 (Summarizing Conversations):** Users MAY request summaries of long message threads, provided this can be done within privacy-preserving constraints (e.g., in-enclave processing, ephemeral data).
*   **Requirement 2.1.3 (Information Retrieval):** The Assistant MAY access and synthesize information from secure, permitted sources.
*   **Requirement 2.1.4 (Task Automation):** The Assistant MAY facilitate simple task automation (e.g., setting reminders within a Signal context), once such capabilities are securely integrated and specified.

### 2.2 Interaction Patterns
*   **Requirement 2.2.1:** Users MUST interact with the Assistant directly through standard Signal messages.
*   **Requirement 2.2.2:** Interaction MAY occur in one-on-one chats or in group chats where the Assistant is explicitly included.
*   **Requirement 2.2.3:** The Assistant MUST process natural language queries and respond with text-based replies.

## 3. High-Level Functional Requirements and Non-Goals

### 3.1 Functional Requirements
*   **Requirement 3.1.1 (Natural Language Understanding - NLU):** The Assistant MUST interpret user queries expressed in natural language.
*   **Requirement 3.1.2 (Contextual Awareness):** The Assistant SHOULD maintain limited conversational context to provide more relevant responses, managed securely within the Enclave.
*   **Requirement 3.1.3 (Response Generation):** The Assistant MUST generate informative, concise, and helpful text-based responses.
*   **Requirement 3.1.4 (Secure Integration with Signal):** The Assistant MUST seamlessly send and receive messages via the Signal protocol, with all cryptographic operations occurring within the Enclave.
*   **Requirement 3.1.5 (Privacy by Design):** All sensitive data processing MUST occur within a Trusted Execution Environment (TEE).
*   **Requirement 3.1.6 (Extensible Knowledge Base):** The Assistant MAY access and utilize various information sources, including external Large Language Models (LLMs), with interactions mediated and secured by the Enclave.

### 3.2 Non-Goals
*   **Non-Goal 3.2.1 (Initiating Calls/Video):** The Assistant MUST NOT initiate or participate in voice or video calls.
*   **Non-Goal 3.2.2 (Unactioned Message Sending):** The Assistant MUST NOT send messages to other Signal users without explicit, direct user instruction and confirmation, processed securely within the Enclave.
*   **Non-Goal 3.2.3 (Direct Access to User Device Data):** The Assistant MUST NOT directly access local user data on their device (e.g., contacts, calendar, location) unless explicitly and securely integrated with user-controlled permissions and specified in a separate, approved design.
*   **Non-Goal 3.2.4 (General Purpose Application Platform):** The Assistant is NOT intended to be a platform for running arbitrary user-submitted code or complex third-party applications.

## 4. System Components and Responsibilities

The Signal Assistant system MUST be comprised of strictly defined components, each with explicit responsibilities and boundaries to enforce the overall security and privacy posture. A strict separation of concerns, particularly between untrusted host components and the trusted Enclave, MUST be maintained.

### 4.1 Signal Integration Layer (Host)
*   **Responsibility:** The Signal Integration Layer MUST act as the primary interface between the Signal network and the Host.
*   **What it MUST DO:**
    *   Terminate TLS connections from Signal servers.
    *   Receive encrypted (Signal protocol) messages addressed to the Assistant.
    *   Re-encrypt the *entire Signal-encrypted payload* using an Enclave-specific symmetric key (Host-Enclave Transport Key) immediately upon receipt.
    *   Transmit host-encrypted payloads to the Enclave via a secure IPC mechanism.
    *   Receive host-encrypted responses from the Enclave.
    *   Decrypt the host-encrypted responses to retrieve the Signal-encrypted payload.
    *   Transmit the Signal-encrypted payload to the Signal servers for delivery to the user.
    *   Manage non-sensitive aspects of Signal communication (e.g., webhook registration, basic connection management).
*   **What it MUST NOT DO:**
    *   Decrypt the Signal protocol encrypted messages or access their plaintext content.
    *   Access any PII within messages or related metadata.
    *   Modify Signal-encrypted payloads.
    *   Store any plaintext sensitive data persistently.
*   **Data Received/Sent:** Signal-encrypted messages (inbound), host-encrypted messages (inbound to Enclave), host-encrypted messages (outbound from Enclave), Signal-encrypted messages (outbound to Signal).
*   **Raw Content Visibility:** NONE. It MUST only handle encrypted payloads.
*   **Persistent Storage:** MAY store non-sensitive configuration data (e.g., Signal server endpoint URLs, public keys for attestation verification) not containing secrets. MUST NOT store any sensitive data or PII persistently.

### 4.2 Host (Untrusted Environment)
*   **Responsibility:** The Host MUST act solely as an untrusted resource provisioner and orchestrator for the Enclave and non-sensitive services.
*   **What it MUST DO:**
    *   Provide CPU, memory, network, and storage resources to the Enclave.
    *   Launch, attest, and monitor the Enclave's operational status.
    *   Manage connections to external services (e.g., external LLM APIs) *only* under strict Enclave control and with appropriate encryption.
    *   Provide block storage for the Enclave's persistent encrypted data.
    *   Handle non-sensitive operational logic (e.g., billing, general system health monitoring).
*   **What it MUST NOT DO:**
    *   Access or tamper with the Enclave's protected memory or execution state.
    *   Decrypt or access any sensitive data intended for the Enclave (unless explicitly re-encrypted by the Enclave for transport).
    *   Infer or log user activity based on sensitive content.
    *   Store any plaintext sensitive data persistently.
*   **Data Received/Sent:** Enclave attestation reports, host-encrypted data (to/from Enclave), encrypted blobs for persistent storage.
*   **Raw Content Visibility:** NONE.
*   **Persistent Storage:** MAY store Enclave-encrypted data blobs, non-sensitive operational logs (referencing `internal_user_id` only, with strict TTLs), and non-sensitive configuration.

### 4.3 Enclave (Trusted Execution Environment)
*   **Responsibility:** The Enclave MUST serve as the trusted core where all sensitive operations and data reside. It MUST be designed to minimize its attack surface.
*   **What it MUST DO:**
    *   Decrypt host-encrypted payloads received from the Signal Integration Layer.
    *   Decrypt Signal protocol encrypted messages using its internal Signal identity and session keys.
    *   Perform Identity Mapping, securely binding Signal User Identifiers to `internal_user_id`s.
    *   Orchestrate LLM interactions, including prompt construction, sanitization, and response processing.
    *   Manage all cryptographic keys (Signal keys, storage keys, LLM API keys) via its internal KMS.
    *   Encrypt/decrypt data for persistent storage on the Host's Persistence Layer via the Secure Storage Interface.
    *   Generate and verify remote attestations.
    *   Generate secure, anonymized logs for forwarding to the Host.
    *   Implement all core Assistant Bot Logic.
    *   Enforce safety and guardrail policies for LLM interactions.
*   **What it MUST NOT DO:**
    *   Expose any plaintext sensitive data (user messages, LLM prompts/responses, Signal keys, `Signal_ID` to `internal_user_id` mappings) outside its trusted boundary.
    *   Store plaintext sensitive data persistently.
    *   Perform any operation that could compromise user privacy or system integrity.
*   **Data Received/Sent:** Host-encrypted payloads (inbound), Signal-encrypted messages (decrypted internally), plaintext user messages (processed internally), LLM prompts (outbound to LLM API), LLM responses (inbound from LLM API), plaintext responses (processed internally), Signal-encrypted messages (encrypted internally), host-encrypted payloads (outbound).
*   **Raw Content Visibility:** FULL for data within its trusted boundary. This is the *only* component that sees plaintext sensitive data.
*   **Persistent Storage:** MAY manage encrypted persistent storage on the Host via the Secure Storage Interface.

#### 4.3.1 Sub-components within Enclave
*   **Signal Protocol Stack:** MUST manage Signal message decryption/encryption and session state using Enclave-held keys.
*   **Identity Mapping Service:** MUST securely bind Signal User Identifiers to opaque `internal_user_id`s, and store this mapping exclusively within Enclave secure storage.
*   **Assistant Bot Logic:** MUST contain the core business logic for processing user requests, coordinating actions, and applying safety policies.
*   **LLM API Proxy/Client:** MUST securely connect to and interact with external third-party LLM APIs, ensuring prompts are sanitized and responses are processed within the Enclave.
*   **Key Management Service (KMS):** MUST generate, store, and manage all cryptographic keys used within the Enclave, ensuring keys never leave the Enclave in plaintext.
*   **Secure Storage Interface:** MUST encrypt and decrypt data for persistent storage on the Host, using Enclave-generated keys.
*   **Attestation Logic:** MUST generate and verify remote attestations to confirm the Enclave's integrity.
*   **Secure Logging Proxy:** MUST forward encrypted, anonymized logs to the Host, ensuring no PII or sensitive content is exposed.
*   **PII Sanitizer:** MUST redact or replace PII from messages/prompts before further processing or transmission to external components.

### 4.4 Persistence Layer (Host, Enclave-Encrypted)
*   **Responsibility:** The Persistence Layer MUST provide durable, block-level storage on the untrusted Host for data managed and encrypted by the Enclave.
*   **What it MUST DO:**
    *   Store encrypted data blobs provided by the Enclave.
    *   Return encrypted data blobs upon request from the Enclave.
*   **What it MUST NOT DO:**
    *   Interpret, decrypt, or modify the contents of the encrypted data blobs.
    *   Access any plaintext sensitive data.
*   **Data Received/Sent:** Encrypted data blobs (to/from Enclave via Host).
*   **Raw Content Visibility:** NONE. All data is encrypted.
*   **Persistent Storage:** Stores encrypted data blobs indefinitely or according to Enclave-managed retention policies.

### 4.5 External LLM APIs (Third-Party)
*   **Responsibility:** External LLM APIs MUST provide the underlying large language model capabilities to the Enclave.
*   **What it MAY DO:**
    *   Receive prompts from the Enclave.
    *   Process prompts and generate responses.
    *   Return responses to the Enclave.
*   **What it MUST NOT DO:**
    *   Receive unsanitized prompts containing PII from the Enclave.
    *   Retain prompts or responses beyond immediate processing, unless explicitly agreed upon with strict privacy controls.
*   **Data Received/Sent:** Sanitized LLM prompts (inbound from Enclave), LLM responses (outbound to Enclave).
*   **Raw Content Visibility:** FULL for the sanitized prompt and response *during processing*.
*   **Persistent Storage:** Assumed to have its own retention policies, which the Enclave's PII sanitization and data minimization efforts are designed to mitigate against.

### 4.6 Monitoring and Telemetry (Host)
*   **Responsibility:** To collect and report operational metrics and system health without compromising user privacy.
*   **What it MUST DO:**
    *   Collect non-sensitive system metrics (CPU usage, memory, network traffic).
    *   Collect anonymized operational logs (e.g., event timestamps, `internal_user_id`, message sizes, error codes) from the Host and Secure Logging Proxy within the Enclave.
*   **What it MUST NOT DO:**
    *   Collect or report any plaintext user message content, LLM prompts/responses, or Signal IDs.
    *   Link `internal_user_id`s to Signal IDs.
*   **Raw Content Visibility:** NONE.
*   **Persistent Storage:** Stores anonymized metrics and operational logs with strict TTLs.

## 5. Identity and Session Model

The Signal Assistant SHALL implement a privacy-centric identity and session model to ensure user pseudonymity and data security.

### 5.1 Identity Mapping
#### 5.1.1 Signal Identifier to Internal User ID Mapping
*   **Requirement 5.1.1.1:** Each unique Signal User Identifier (UUID, representing a specific Signal account) MUST be mapped to a single, cryptographically secure, random, and opaque `internal_user_id` within the Enclave.
*   **Requirement 5.1.1.2:** The mapping from Signal User Identifier to `internal_user_id` MUST occur exclusively within the Enclave.
*   **Requirement 5.1.1.3:** The Enclave MUST store this mapping only within its secure, attested storage.
*   **Requirement 5.1.1.4:** The Host MUST NEVER see the direct Signal User Identifier in association with user activity or persistent data. The Host SHALL only operate on `internal_user_id` when communicating with the Enclave.
*   **Requirement 5.1.1.5:** Multi-device interactions (a single Signal User Identifier interacting from multiple linked devices) SHALL be recognized as originating from the same `internal_user_id`. The system MUST NOT differentiate between a user's linked devices for identity purposes, treating them as extensions of the same user.
*   **Requirement 5.1.1.6:** If a user reinstalls the Signal application on a device, their Signal User Identifier remains the same, and the existing `internal_user_id` mapping SHALL be used by the Enclave.
*   **Requirement 5.1.1.7:** If a user changes their phone number but transfers their Signal account, their Signal User Identifier MAY change. The Enclave SHOULD attempt to remap the new Signal User Identifier to the existing `internal_user_id` if verifiable (e.g., via a secure account recovery process initiated by the user). If re-mapping is not possible, the new Signal User Identifier SHALL be treated as a new user with a new `internal_user_id`.

#### 5.1.2 Internal User ID Properties
*   **Requirement 5.1.2.1:** `internal_user_id`s MUST be generated with sufficient entropy to prevent brute-force enumeration.
*   **Requirement 5.1.2.2:** `internal_user_id`s MUST NOT contain any information directly derivable from the Signal User Identifier or any other PII.

### 5.2 Per-User State Management
All per-user state is managed within or secured by the Enclave.

#### 5.2.1 Configuration and Preferences
*   **Requirement 5.2.1.1:** User-specific configurations and preferences (e.g., language settings, notification preferences) SHALL be associated with the `internal_user_id`.
*   **Requirement 5.2.1.2:** This state MUST be stored encrypted on the Host's Persistence Layer via the Enclave's Secure Storage Interface.
*   **Requirement 5.2.1.3:** Retention Policy: User configurations and preferences SHALL be retained as long as the `internal_user_id` mapping exists. Upon user deletion, this state MUST be purged.

#### 5.2.2 Conversational Context / Long-Term Memory
*   **Requirement 5.2.2.1 (Ephemeral Conversational Context):** Limited conversational context (e.g., recent turns, topic tracking) MAY be maintained per `internal_user_id` to provide coherent responses. This context MUST exist only within the Enclave's volatile memory and MUST be ephemeral.
*   **Requirement 5.2.2.2 (Long-Term Memory Content):** Long-term memory, if implemented, MUST NOT store raw plaintext user messages or LLM responses. Instead, it MAY store:
    *   **Redacted summaries:** Summaries of past interactions where all PII has been removed by the Enclave's PII Sanitizer.
    *   **Semantic embeddings:** Numerical representations of redacted conversations, intended for retrieval or contextualization, generated within the Enclave.
    *   **User preferences/interests:** Explicitly provided or inferred preferences, stored as non-PII data.
*   **Requirement 5.2.2.3 (Long-Term Memory PII Classification):** Any data stored as long-term memory MUST be treated as **pseudonymous data**, associated only with the `internal_user_id` and having undergone PII sanitization. It MUST NOT contain direct PII.
*   **Requirement 5.2.2.4 (Security of Stored Memory):** All long-term memory data MUST be managed securely within the Enclave and stored encrypted on the Host's Persistence Layer via the Enclave's Secure Storage Interface.
*   **Requirement 5.2.2.5 (Retention and Deletion Policy):**
    *   Ephemeral conversational context MUST be purged within the Enclave after a short, defined period (e.g., session end or inactivity timeout).
    *   Long-term memory, if implemented, SHALL adhere to user-configurable or system-defined retention policies (e.g., 90 days, 180 days). It MUST be automatically pruned or deleted upon expiration of its retention period.
    *   All long-term memory associated with an `internal_user_id` MUST be irrevocably purged upon user deletion.

#### 5.2.3 Task Queues and Rate Limits
*   **Requirement 5.2.3.1:** Per-user task queues (for asynchronous operations) and rate limits MUST be managed, associated with the `internal_user_id`.
*   **Requirement 5.2.3.2:** This state MAY reside ephemerally within the Enclave or on the Host, provided it contains no PII and only references `internal_user_id`.
*   **Requirement 5.2.3.3:** Retention Policy: Task queue entries SHALL be transient, existing only until task completion or expiration. Rate limit states SHALL reset according to their defined time windows.

## 6. Message and Command Model

The Signal Assistant MUST process incoming messages and commands based on their classification and adhere to defined protocols for interpretation and error handling.

### 6.1 Message Classification
Incoming messages to the Signal Assistant SHALL be classified into the following categories within the Enclave:

*   **Requirement 6.1.1:** **Normal Assistant Chat:** Messages intended for conversational interaction with the LLM or Assistant Bot Logic. These messages MAY contain natural language queries, statements, or requests for information.
*   **Requirement 6.1.2:** **Control/Configuration Commands:** Messages containing explicit instructions to the Assistant for managing its behavior, settings, or linked services. These commands MUST adhere to a predefined format (e.g., prefixed with a reserved character or keyword). Examples include:
    *   `!settings` or `/settings`: Access user-specific configuration.
    *   `!link <service>`: Link to an external service.
    *   `!delete_data`: Initiate user data deletion.
*   **Requirement 6.1.3:** **Admin/System-Only Operations:** Messages or signals intended for administrative control or system-level actions (e.g., attestation requests, key rotation triggers, diagnostics). These MUST originate from authorized system administrators or trusted host components, and SHALL bypass normal user-facing processing. Access to these operations MUST be strictly controlled by the Enclave.

### 6.2 Reserved Prefixes, Keywords, and Message Formats
*   **Requirement 6.2.1:** The Assistant SHALL reserve specific prefixes or keywords for Control/Configuration Commands. The default prefix for such commands SHOULD be `!` or `/`.
*   **Requirement 6.2.2:** Control/Configuration Commands MAY follow a structured format (e.g., `!command <argument> <value>`) that MUST be parsed by the Enclave's Assistant Bot Logic.
*   **Requirement 6.2.3:** Messages not matching a Control/Configuration Command format SHALL be treated as Normal Assistant Chat.

### 6.3 Error and Fallback Behavior
The Assistant MUST provide robust error handling and fallback mechanisms for message and command processing.

*   **Requirement 6.3.1:** **Malformed Control Commands:** If a message is identified as a Control/Configuration Command but is syntactically malformed, the Assistant SHOULD respond with an informative error message to the user, explaining the correct syntax.
*   **Requirement 6.3.2:** **Unknown Control Commands:** If a message uses a reserved prefix but corresponds to an unknown command, the Assistant SHOULD respond with a message indicating that the command is not recognized and MAY suggest available commands.
*   **Requirement 6.3.3:** **Backend Failures (LLM, KMS, Storage):** In the event of an unrecoverable failure in backend services (e.g., LLM API unavailability, KMS error, Secure Storage access failure), the Assistant MUST provide a graceful degradation or an informative error message to the user, indicating temporary unavailability or specific issues. The response MUST NOT leak internal system details.
*   **Requirement 6.3.4:** **Fallback for Unprocessable Chat:** If a Normal Assistant Chat message cannot be processed (e.g., due to NLU failure, content policy violation), the Assistant SHOULD provide a polite fallback response, indicating that it could not understand or process the request.
*   **Requirement 6.3.5:** All error responses to users MUST be generated *within the Enclave* and MUST NOT reveal sensitive internal state or PII.

## 7. LLM Orchestration Model

The Enclave's LLM API Proxy/Client and Assistant Bot Logic MUST collectively manage the secure and robust interaction with external Large Language Models. This includes careful orchestration of prompts, responses, and the enforcement of safety policies.

### 7.1 Prompt Construction
*   **Requirement 7.1.1:** The Assistant Bot Logic (within the Enclave) MUST be responsible for constructing the final prompt sent to the LLM.
*   **Requirement 7.1.2:** Prompt construction MUST incorporate the user's message, relevant conversational context (if any), and any system-level instructions or guardrails.
*   **Requirement 7.1.3:** The PII Sanitizer (within the Enclave) MUST process the user's message and any other sensitive data components *before* their inclusion in the final prompt.
*   **Requirement 7.1.4:** The constructed prompt MUST be designed to minimize data exposure to the LLM, sending only information strictly necessary for generating a relevant response.

### 7.2 Model Selection and Interaction
*   **Requirement 7.2.1:** The LLM API Proxy/Client (within the Enclave) MAY support interaction with multiple LLM providers or models.
*   **Requirement 7.2.2:** Model selection, if dynamic, MUST be determined by Enclave logic based on factors such as performance, cost, and specific task requirements.
*   **Requirement 7.2.3:** The LLM API Proxy/Client MUST establish secure (e.g., TLS-protected) and authenticated connections to external LLM APIs.
*   **Requirement 7.2.4:** LLM API keys and credentials MUST be managed exclusively by the Enclave's KMS and MUST NOT be exposed to the Host.

### 7.3 Tool Calling and External API Interaction
*   **Requirement 7.3.1:** If the Assistant supports tool-calling capabilities, the decision to invoke an external tool (e.g., information retrieval service, calendar API) MUST be made by the Assistant Bot Logic *within the Enclave*.
*   **Requirement 7.3.2:** Data sent to external tools MUST undergo PII sanitization (if applicable) and data minimization *within the Enclave* before transmission.
*   **Requirement 7.3.3:** Responses from external tools MUST be processed by the Enclave, and any sensitive information MUST be handled according to Enclave privacy policies before being used in LLM prompts or user responses.

### 7.4 Error Handling and Resilience
*   **Requirement 7.4.1:** The LLM API Proxy/Client MUST implement policies for timeouts on LLM API calls.
*   **Requirement 7.4.2:** Retry mechanisms, with exponential backoff, SHOULD be implemented for transient LLM API failures.
*   **Requirement 7.4.3:** Vendor fallback strategies (switching to an alternative LLM provider/model) MAY be implemented in the event of persistent failures or degraded performance from a primary provider.
*   **Requirement 7.4.4:** Unrecoverable LLM errors MUST result in a graceful, non-informative error response to the user, generated within the Enclave (as per Requirement 6.3.3).

### 7.5 Safety and Guardrails Logic
*   **Requirement 7.5.1:** Safety and guardrails logic MUST be implemented within the Enclave, both pre-prompt and post-processing.
*   **Requirement 7.5.2:** **Pre-Prompt Guardrails:** The Assistant Bot Logic MUST analyze constructed prompts for potential policy violations (e.g., harmful content, PII presence) *before* sending them to the LLM.
*   **Requirement 7.5.3:** **Post-Processing Guardrails:** LLM responses MUST be analyzed by the Assistant Bot Logic for safety, ethical guidelines, and policy adherence *before* being presented to the user.
*   **Requirement 7.5.4:** Violations of safety policies MUST result in appropriate actions (e.g., preventing the response from reaching the user, generating a canned refusal message, logging the incident for review).
*   **Requirement 7.5.5:** The safety mechanisms MUST operate entirely within the Enclave to prevent sensitive information from being exposed during filtering.

## 8. Conceptual Data Flow

The system MUST enforce a strictly controlled data flow to maintain privacy, with the Enclave serving as the central trust anchor.

### 8.1 Inbound Message Flow (User to Enclave)
*   **Requirement 8.1.1 (User Message Origin):** A user MUST send an encrypted message via their Signal client.
*   **Requirement 8.1.2 (Signal Network Transport):** The message MUST traverse the Signal network, remaining end-to-end encrypted to the bot's Signal identity.
*   **Requirement 8.1.3 (Host Ingress & Re-encryption):** The Host's Signal Integration Layer MUST receive the Signal-encrypted message. The Host MUST immediately re-encrypt the *entire* Signal-encrypted payload using a Host-Enclave symmetric key and forward it via secure IPC to the Enclave. The Host MUST NOT decrypt the Signal message.
*   **Requirement 8.1.4 (Enclave Decryption & Processing - Layer 1):** The Enclave MUST decrypt the host-encrypted payload.
*   **Requirement 8.1.5 (Enclave Decryption & Processing - Layer 2):** The Enclave's Signal Protocol Stack MUST decrypt the user's message using its internal Signal identity and session keys. The plaintext user message MUST become accessible *only within the Enclave's memory*.
*   **Requirement 8.1.6 (Identity Binding):** The Signal sender's ID MUST be used by the Enclave's Identity Mapping Service to retrieve or create an `internal_user_id`. This mapping MUST occur *exclusively inside the Enclave*.
*   **Requirement 8.1.7 (PII Sanitization):** The plaintext user message (prompt) MUST be passed through the Enclave's PII Sanitizer to redact or replace any detected PII *before* further processing or interaction with external services.
*   **Requirement 8.1.8 (LLM Prompting):** The (potentially sanitized) plaintext user message (prompt) MUST be fed to the Enclave's LLM API Proxy/Client.

### 8.2 LLM Interaction Flow (Enclave to External LLM API)
*   **Requirement 8.2.1 (Enclave Sends Prompt):** The Enclave's LLM API Proxy/Client MUST make a secure, authenticated call to the external LLM API, sending the PII-sanitized prompt over an encrypted channel (e.g., TLS).
*   **Requirement 8.2.2 (External LLM Processing):** The external LLM API MAY process the prompt and generate a response.
*   **Requirement 8.2.3 (LLM Response to Enclave):** The LLM API MUST return the response over the secure channel to the Enclave. The LLM response MUST exist in plaintext *only within the Enclave's memory*.

### 8.3 Outbound Message Flow (Enclave to User)
*   **Requirement 8.3.1 (Enclave Response Generation & Encryption - Layer 1):** The Enclave's Assistant Bot Logic MUST process the LLM response. The Enclave's Signal Protocol Stack MUST then encrypt the generated response using the appropriate Signal session keys for the recipient.
*   **Requirement 8.3.2 (Enclave Egress & Re-encryption):** The Signal-encrypted response MUST be re-encrypted by the Enclave using the Host-Enclave symmetric key and sent back to the Host via secure IPC.
*   **Requirement 8.3.3 (Host Egress Decryption):** The Host MUST decrypt the Enclave's transport encryption to retrieve the Signal-encrypted payload. The Host MUST NOT access the plaintext response.
*   **Requirement 8.3.4 (Host Transmission):** The Host MUST transmit the Signal-encrypted message to the Signal server for delivery to the user.
*   **Requirement 8.3.5 (User Message Receipt):** The Signal network MUST deliver the encrypted response to the user's Signal client, which then decrypts it for display.

### 8.4 Key Flow Invariant
*   **Requirement 8.4.1:** Throughout the entire data flow, sensitive plaintext data (user messages, LLM prompts/responses, Signal keys, `Signal_ID` to `internal_user_id` mappings) MUST ONLY exist within the attested boundary of the Enclave.

## 9. Key Management and Attestation Model

The secure and private operation of the Signal Assistant hinges on robust key management and the integrity guarantees provided by remote attestation. All runtime usage and storage at rest of critical cryptographic keys on the server side MUST be confined to the Enclave. The Host MUST NOT hold or use any such keys in plaintext.

### 9.1 Key Types and Purpose

The Enclave's Key Management Service (KMS) MUST manage diverse cryptographic keys, each with a specific purpose and lifecycle, designed to uphold the system's privacy and security invariants.

*   **9.1.1 Enclave Root Key (ERK):**
    *   **Purpose:** The ERK MUST be a unique, hardware-derived symmetric key specific to each Enclave instance. It serves as the trust anchor for all other keys, used solely to seal (encrypt) other sensitive keys and data blobs for persistent storage on the untrusted Host.
    *   **Properties:** The ERK MUST be generated by the TEE hardware, remain resident in secure memory, and MUST NEVER be exposed outside the Enclave. Its availability is implicitly tied to the Enclave's attested integrity.

*   **9.1.2 Enclave Secure Storage Keys (ESSK):**
    *   **Purpose:** ESSKs MUST be symmetric keys derived from or protected by the ERK, used to encrypt sensitive persistent data (e.g., Signal identity keys, identity mappings, long-term memory, configuration) before it is written to the Host's untrusted storage. These keys MAY be differentiated for different data types (e.g., per-user, per-service).
    *   **Properties:** ESSKs MUST be generated and managed exclusively within the Enclave's KMS. They MUST be sealed by the ERK when at rest and MUST ONLY be unsealed and used within an attested Enclave.

*   **9.1.3 Signal Protocol Keys (SPK):**
    *   **Purpose:** SPKs comprise the full suite of keys required for the Signal Protocol: identity keys (signing keys), prekeys, signed prekeys, and session keys. They enable end-to-end encryption with Signal users.
    *   **Properties:** SPKs MUST be generated, stored, and managed exclusively within the Enclave's Signal Protocol Stack and KMS. They MUST NEVER leave the Enclave in plaintext. When persisted to untrusted Host storage, they MUST be encrypted using an ESSK.

*   **9.1.4 Enclave Signing/Attestation Keys (ESAK):**
    *   **Purpose:** ESAKs are asymmetric key pairs used by the Enclave to cryptographically sign attestation reports and potentially sign other critical internal artifacts or messages to external trusted components.
    *   **Properties:** ESAKs MUST be generated and managed exclusively within the Enclave's KMS. The private key MUST NEVER leave the Enclave. The public key forms part of the attestation report, enabling external verification of the Enclave's authenticity.

*   **9.1.5 External Service API Keys (EAK):**
    *   **Purpose:** These keys or credentials grant the Enclave access to external third-party services (e.g., Large Language Models).
    *   **Properties:** EAKs MUST be provisioned to the Enclave securely (e.g., via a remote KMS or a dedicated provisioning service) in a way that keeps the Host blind (only opaque encrypted blobs transit the Host). They MUST be stored and used exclusively within the Enclave's KMS and MAY be protected by an ESSK when at rest. They MUST NEVER be exposed to the Host. The release of EAKs to the Enclave MUST be gated on verified attestation measurements as described in 9.4.3. This ensures that EAKs are never exposed in plaintext to the Host, either during transit or at rest, nor can they be "snuck" into host environment variables or config files while claiming compliance.

### 9.2 Location and Visibility

The principle of Host Blindness (Invariant 10.2) and Plaintext Confidentiality (Invariant 10.1) critically informs the location and visibility of all keys.

| Key Type                               | Where Generated                                | Stored at Rest (Location & Encryption)              | Components Seeing Plaintext       | Host Interaction / Usage                                     |
| :------------------------------------- | :--------------------------------------------- | :-------------------------------------------------- | :-------------------------------- | :----------------------------------------------------------- |
| **Enclave Root Key (ERK)**             | TEE Hardware (Enclave)                         | Secure Memory (Ephemeral, never leaves TEE)         | Enclave (TEE Hardware)            | Host MUST NEVER see or use.                                  |
| **Enclave Secure Storage Keys (ESSK)** | Enclave KMS                                    | Host Persistence Layer (Sealed by ERK)              | Enclave KMS                       | Host can only store/retrieve encrypted blobs; MUST NOT use directly. |
| **Signal Protocol Keys (SPK)**         | Enclave Signal Protocol Stack/KMS              | Host Persistence Layer (Encrypted by ESSK)          | Enclave Signal Protocol Stack/KMS | Host can only store/retrieve encrypted blobs; MUST NOT use directly. |
| **Enclave Signing/Attestation Keys (ESAK)** | Enclave KMS                                    | Enclave Secure Storage (Optional, Sealed by ERK)    | Enclave KMS                       | Host only sees public key within attestation reports; MUST NOT use private key. |
| **External Service API Keys (EAK)**   | Enclave KMS (or securely provisioned to Enclave) | Enclave Secure Storage (Encrypted by ESSK)          | Enclave KMS                       | Host MUST NEVER see or use.                                  |

### 9.3 Rotation and Compromise Handling

A robust key management strategy MUST include mechanisms for key rotation and defined procedures for handling suspected compromises to minimize blast radius.

*   **9.3.1 Rotation Schedule and Triggers:**
    *   **ERK:** The ERK is intrinsically tied to the Enclave instance and TEE hardware. It implicitly rotates upon Enclave re-provisioning or a full system redeployment. There is no direct "rotation" mechanism for the ERK itself in an active Enclave.
    *   **ESSK:** ESSKs SHOULD be rotated periodically (e.g., annually, semi-annually) and/or upon major system updates or policy changes. Rotation MUST involve re-encrypting all data protected by the old ESSK with a newly generated ESSK.
    *   **SPK (Identity Keys):** Signal identity keys SHOULD be rotated periodically (e.g., annually) or upon explicit user request. Session keys are ephemeral and rotate per Signal Protocol specification.
    *   **ESAK (Signing Keys):** ESAKs for attestation SHOULD be rotated upon major code changes (which would change attestation measurements) or periodically (e.g., annually).
    *   **External Service API Keys:** EAKs SHOULD be rotated regularly according to service provider recommendations (e.g., quarterly) or upon suspicion of compromise. This rotation MUST be managed via secure re-provisioning to the Enclave.

*   **9.3.2 Compromise Handling and Blast Radius:**
    *   **Suspected Compromise of a Signal Session Key:**
        *   **Action:** The Enclave MUST immediately terminate the compromised session, discard the session key, and initiate a new Signal session key exchange.
        *   **Blast Radius:** Limited to the messages exchanged within that single session. No long-term data or other sessions are affected.
    *   **Suspected Compromise of an ESSK:**
        *   **Action:** The Enclave MUST invalidate the compromised ESSK, generate a new one, and re-encrypt all data previously protected by the compromised key using the new ESSK. This requires a full re-keying operation for affected data.
        *   **Blast Radius:** All data encrypted by that specific ESSK instance is at risk. Data integrity and confidentiality would be restored once re-keyed.
    *   **Suspected Compromise of an Enclave Root Key (ERK) / Enclave Attestation:**
        *   **Action:** This implies a fundamental compromise of the Enclave itself. All operations MUST cease immediately. The compromised Enclave instance MUST be taken offline and its sealed data rendered permanently inaccessible by subsequent *attested* Enclaves. A fresh, attested Enclave instance MUST be provisioned, requiring a full system re-initialization and re-provisioning of all keys and data (if backups exist and are secure).
        *   **Blast Radius:** Catastrophic. All secrets and data ever processed by that specific Enclave instance could be compromised. This scenario underscores the critical importance of attestation and secure operational practices.
    *   **Suspected Compromise of an External Service API Key (EAK):**
        *   **Action:** The Enclave MUST immediately invalidate the compromised key and cease all communication with the affected external service. A new EAK MUST be securely provisioned to the Enclave.
        *   **Blast Radius:** Limited to unauthorized access or usage of the specific external service by the (now invalid) key. No internal Enclave data is directly compromised.
### 9.4 Attestation Model

Remote attestation provides cryptographic assurance of the Enclave's integrity, ensuring that critical operations, including key management, occur in a trusted environment.

*   **9.4.1 Attested Measurements / Claims:**
    *   The attestation report MUST include cryptographic measurements (hashes) of the Enclave's loaded code (e.g., application binary, libraries), configuration (e.g., memory layout, environment variables), and potentially key policies (e.g., restrictions on key usage).
    *   These measurements provide a unique, immutable fingerprint of the trusted execution environment.

*   **9.4.2 Attestation Verifiers:**
    *   **Deployment Controller / Orchestration Service:** A trusted Host component (or external orchestration service) MUST verify the Enclave's attestation report during startup and whenever its integrity is questioned. This verification MUST occur *before* provisioning any sensitive data or external service keys (EAKs) to the Enclave. The verifier itself MUST NOT gain access to EAKs in plaintext.
    *   **Monitoring Service:** A continuous monitoring service SHOULD periodically re-verify the Enclave's attestation to detect any runtime tampering.
    *   **Clients / Auditing Bodies (Optional):** The system SHOULD provide a mechanism for end-users or independent auditing bodies to verify the public attestation reports, binding the Enclave's public key to a known-good software image.

*   **9.4.3 Attestation Gating Key Access:**
    *   The Host MUST NOT release sensitive keys or external service credentials (including EAKs) to an Enclave unless its attestation report has been successfully verified against a known set of expected, authorized measurements. This release mechanism MUST ensure that EAKs are delivered to the Enclave in an encrypted, opaque form that the Host cannot decrypt, ensuring Host blindness to the plaintext EAKs.
    *   The Enclave itself MUST use its internally verified attestation state to gate access to its own sealed keys (e.g., ESSKs can only be unsealed if the Enclave's current measurement matches the measurement it was sealed with).
    *   This gating mechanism MUST ensure that only authorized, untampered Enclaves can access and utilize cryptographic keys for their intended purpose.

## 10. System-Level Invariants

The following invariants define the immutable properties and guarantees of the Signal Assistant system, ensuring its secure and privacy-preserving operation. These MUST be upheld across all components and during all operational phases.

*   **Invariant 10.1 (Plaintext Confidentiality):** Sensitive plaintext data (user messages, LLM prompts/responses, Signal keys) MUST NEVER exist outside the attested boundary of the Enclave.
*   **Invariant 10.2 (Host Blindness):** The Host MUST NEVER see or process plaintext sensitive data. It MUST only handle encrypted payloads when dealing with Enclave-destined or Enclave-originated sensitive information.
*   **Invariant 10.3 (PII Sanitization Enforcement):** All user-provided content intended for external services (e.g., LLMs) or for persistent storage MUST undergo PII sanitization within the Enclave *before* leaving the Enclave's processing scope.
*   **Invariant 10.4 (Logging Content Restriction):** Operational logs, both Host and Enclave-derived, MUST NEVER contain plaintext user message content, LLM prompts/responses, or direct Signal IDs. All logged identifiers MUST be `internal_user_id`s or other non-PII pseudonyms.
*   **Invariant 10.5 (Ephemeral Sensitive Data):** Plaintext user messages and LLM responses in the Enclave's memory MUST be ephemeral and purged immediately after processing. They MUST NOT be stored persistently in plaintext.
*   **Invariant 10.6 (Identity Pseudonymity):** The mapping between Signal User Identifiers and `internal_user_id`s MUST be managed exclusively within the Enclave's secure storage, ensuring the Host cannot link `internal_user_id`s to real-world Signal identities.
*   **Invariant 10.7 (Attestation Integrity):** The Enclave's cryptographic measurement (attestation hash) MUST accurately reflect its loaded code and configuration. Any deviation SHALL invalidate the attestation and prevent normal operation.
*   **Invariant 10.8 (Data Minimization):** The system MUST collect, process, and retain only the absolute minimum amount of personal data required to deliver its service.
*   **Invariant 10.9 (SLO/SLA Targets - High-Level):**
    *   **Latency:** The median end-to-end latency for a standard user message-response cycle SHOULD be below 2 seconds. Maximum latency SHOULD be below 5 seconds for 99% of requests.
    *   **Availability:** The Signal Assistant service SHOULD aim for 99.9% uptime (excluding planned maintenance).
    *   **Throughput:** The system SHOULD be capable of processing [N] messages per second per Enclave instance.

## 11. Cross-Cutting Concerns

This section describes overarching principles and requirements that apply across multiple components of the Signal Assistant system.

### 11.1 Privacy Posture
*   **Requirement 11.1.1:** The Signal Assistant MUST adhere to a "privacy-by-design" and "privacy-by-default" philosophy.
*   **Requirement 11.1.2:** The use of a Trusted Execution Environment (TEE) MUST be fundamental to the privacy posture, ensuring user conversations and sensitive processing remain confidential from untrusted hosts and external observers.
*   **Requirement 11.1.3:** Data minimization, secure identity management, and stringent logging policies MUST be enforced to reinforce the privacy commitment.

### 11.2 Robustness and Observability
*   **Requirement 11.2.1:** The system MUST be designed for high availability and operational resilience.
*   **Requirement 11.2.2:** Robust error handling MUST be implemented within both Host and Enclave components.
*   **Requirement 11.2.3:** Comprehensive, privacy-preserving logging MUST be implemented.
*   **Requirement 11.2.4:** Mechanisms to monitor the health and attestation status of Enclaves MUST be in place.

### 11.3 Performance and Cost
*   **Requirement 11.3.1:** The architecture SHOULD aim for efficient operation, balancing security with performance and cost.
*   **Requirement 11.3.2:** IPC between Host and Enclave SHOULD be optimized.
*   **Requirement 11.3.3:** LLM requests MAY be batched within the Enclave where feasible to amortize overheads.
*   **Requirement 11.3.4:** Enclave resources MUST be managed carefully, acknowledging their potentially higher operational cost compared to standard VMs.
*   **Requirement 11.3.5:** Latency MUST be optimized within the constraints of secure processing.

### 11.4 Safety Controls
*   **Requirement 11.4.1:** High-level safety mechanisms MUST be integrated to prevent misuse and mitigate risks associated with AI-generated content.
*   **Requirement 11.4.2:** These controls MUST include prompt sanitization and response filtering, operating exclusively within the secure Enclave environment.
*   **Requirement 11.4.3:** The system MUST adhere to ethical AI guidelines to prevent the generation of harmful, biased, or inappropriate outputs.

### 11.5 Logging Schema Constraints

To uphold privacy and the Host Blindness invariant, all operational logging MUST adhere to the following schema constraints:

*   **Allowed Log Fields:** Operational logs MAY include the following non-sensitive, pseudonymous metadata:
    *   `internal_user_id` (pseudonymous, opaque user identifier managed by the Enclave).
    *   Operation type (e.g., `INBOUND_MESSAGE_RECEIVED`, `LLM_CALL_SUCCESS`).
    *   Timestamps (e.g., `event_timestamp`, `start_time`, `end_time`).
    *   Durations (e.g., `processing_duration_ms`).
    *   Error codes or warning types.
    *   Attestation status or verification results.
    *   Component name (e.g., `Host`, `Enclave_SignalLib`).
    *   Message sizes (encrypted or sanitized message lengths).
    *   Non-sensitive request metadata (e.g., API endpoint invoked without parameters).
    *   Cryptographic operation success/failure.

*   **Explicitly Forbidden Log Fields:** Operational logs MUST NEVER include the following sensitive data:
    *   Any plaintext user content (messages, queries, prompts, responses).
    *   LLM prompts or responses, even if sanitized.
    *   Signal User Identifiers (UUIDs or phone numbers).
    *   Any cryptographic key material (plaintext or encrypted).
    *   Any other Personally Identifiable Information (PII) not explicitly allowed.
    *   Direct links or correlations between `internal_user_id` and Signal User Identifiers.
