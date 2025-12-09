# Proposal: Spec-Driven Enforcement for Signal Assistant Privacy & Security

## 1. Scope and Objectives

This proposal outlines the strategy for implementing **spec-driven enforcement** mechanisms across the Signal Assistant project. The primary objective is to align the implementation, tests, and tooling with the canonical privacy and security specifications, and to introduce concrete, testable guardrails that prevent architectural and implementation drift over time.

Specifically, this proposal addresses enforcement for:

*   **Enclave-only plaintext and key handling:** Ensuring sensitive data and cryptographic keys are exclusively processed and managed within the Trusted Execution Environment (TEE).
    *   *References:* `core` 4, 8, 9, 10.1–10.3, 10.5; `privacy` 5–7.
*   **Host blindness + logging constraints:** Guaranteeing the untrusted Host never accesses sensitive plaintext and adheres to strict logging policies.
    *   *References:* `core` 4.1–4.2, 4.6, 10.2, 10.4, 11.5; `privacy` 4, 7, 10.
*   **Identity mapping, deletion, and LE access posture:** Defining and enforcing the secure management of user identities, data deletion processes, and strict Law Enforcement (LE) access controls.
    *   *References:* `core` 5; `privacy` 8–9, 12.3.
*   **LLM prompt construction, sanitization, and external LLM interaction:** Ensuring a secure and auditable pipeline for constructing, sanitizing, and sending prompts to external Large Language Models (LLMs).
    *   *References:* `core` 7–8; `privacy` 5–6.

The output of this proposal will be:

*   **Design-level rules:** Explicit principles and patterns that the codebase *must* follow.
*   **A set of checks/tests/guardrails:** Concrete, verifiable mechanisms (unit tests, integration tests, static analysis, runtime assertions) to enforce these rules and prevent regressions.

## 2. Invariants → Enforcement Mapping

This section explicitly maps key invariants and requirements from the core and privacy specifications to the enforcement mechanisms that will be implemented.

| Invariant/Requirement Citation | Description                                                                                                                                                                                                                                                                     | Enforcement Mechanisms (Code, Tests, Tooling)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| :----------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `core` 10.1, 10.2, 8.4.1        | **Plaintext Confidentiality & Host Blindness:** Sensitive plaintext data (user messages, LLM prompts/responses with PII, cryptographic keys) MUST NEVER exist outside the attested Enclave. Host MUST NEVER see or process plaintext sensitive data.                                  | **Code:** Enclave-Host IPC MUST use mandatory encryption (`src/signal_assistant/enclave/transport.py`). Sensitive data types (e.g., `SignalID`, `PlainTextContent`) MUST be exclusively defined and handled within the Enclave's internal modules. Host-side data structures MUST avoid direct representation of sensitive types. <br/> **Tests:** Integration tests (`test_enclave_host_comm.py`) MUST verify that Signal-encrypted payloads are re-encrypted by the Host and only decrypted within the Enclave. Negative tests MUST confirm Host attempts to access plaintext sensitive data fail or raise errors. <br/> **Tooling:** Static analysis (linters) to detect `SignalID` or raw string usage related to messages/prompts on the Host side.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `core` 10.3, 7.1.3, 8.1.7, 8.2.1 | **PII Sanitization Enforcement:** All user-provided content for external services (LLMs) or persistent storage MUST undergo PII sanitization within the Enclave. Fully assembled prompts MUST pass through `PIISanitizer` before external LLM interaction.                                | **Code:** A single, mandatory `LLMPipeline` or similar orchestration component within the Enclave (`src/signal_assistant/enclave/bot/orchestrator.py`) MUST encapsulate prompt assembly, PII sanitization, and external LLM calls. The `PIISanitizer` (`src/signal_assistant/enclave/privacy_core/sanitizer.py`) MUST have a well-defined interface. <br/> **Tests:** Unit tests for `PIISanitizer` covering various PII patterns (phone numbers, emails) and ensuring redaction. Integration tests for the `LLMPipeline` MUST assert that unsanitized PII from user input, context, or tool outputs cannot reach the external LLM mock. <br/> **Tooling:** (Future) Static analysis to detect direct LLM API calls from Enclave modules that bypass the `LLMPipeline`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `core` 10.4, 11.5               | **Logging Content Restriction:** Operational logs (Host and Enclave-derived) MUST NEVER contain plaintext user content, LLM prompts/responses, or direct Signal IDs. Only `internal_user_id`s or other non-PII pseudonyms are allowed.                                                    | **Code:** A central logging interface (`src/signal_assistant/enclave/secure_config.py` for Enclave, `src/signal_assistant/host/proxy.py` for Host) MUST enforce schema constraints (`core` 11.5). `SignalID` and plaintext content types MUST NOT be accepted by logging functions. <br/> **Tests:** Unit tests for logging interfaces to ensure invalid content is rejected. Integration tests with synthetic messages/Signal IDs MUST verify that Host-visible logs do not contain these values or their simple encodings. <br/> **Tooling:** Static analysis / linters (e.g., `ruff` or custom checks) to forbid direct logging of message bodies, "prompt:", "response:", patterns resembling PII, and raw `SignalID`s.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `core` 10.5, `privacy` 7.2      | **Ephemeral Sensitive Data:** Plaintext user messages and LLM responses in Enclave memory MUST be ephemeral and purged immediately after processing. They MUST NOT be stored persistently in plaintext.                                                                              | **Code:** Enclave logic (`src/signal_assistant/enclave/app.py`, `src/signal_assistant/enclave/bot/orchestrator.py`) MUST manage sensitive data with short-lived variables and explicit memory-clearing patterns where applicable. `LongTermMemory` storage MUST only handle redacted/sanitized data (as per `core` 5.2.2.2). <br/> **Tests:** Integration tests involving `LongTermMemory` mocks MUST assert that only sanitized content is stored. Review of memory management in critical Enclave modules. <br/> **Tooling:** (Future) Memory analysis tools to detect unexpected persistence of sensitive data within Enclave runtime.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `core` 10.6, `privacy` 4.1/8/9  | **Identity Pseudonymity:** Mapping between `Signal_ID` and `internal_user_id` MUST be managed exclusively within the Enclave's secure storage. Host cannot link `internal_user_id`s to real-world `Signal_ID`s.                                                                          | **Code:** `IdentityMappingService` (`src/signal_assistant/enclave/privacy_core/core.py` for the service, `src/signal_assistant/enclave/state_encryption.py` for secure storage) MUST handle `Signal_ID` to `internal_user_id` mapping. The Host (`src/signal_assistant/host/proxy.py`, `src/signal_assistant/host/storage/database.py`) MUST ONLY operate with `internal_user_id` for user-related data. <br/> **Tests:** Unit tests for `IdentityMappingService` ensuring secure storage and retrieval. Integration tests for Host components verifying `Signal_ID`s are never logged or stored. Negative tests to confirm Host attempts to de-anonymize fail. <br/> **Tooling:** Static analysis for `Signal_ID` usage outside `IdentityMappingService` (except for transient network handling on Host).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `core` 9.4.3                    | **Attestation Gating Key Access & "no debug bypass":** Host MUST NOT release sensitive keys (EAKs) to Enclave unless its attestation report is verified. Enclave MUST use verified attestation state to gate access to its own sealed keys. No bypass for attestation checks. | **Code:** Key provisioning mechanisms (`src/signal_assistant/enclave/kms.py`) MUST integrate with attestation verification logic (`src/signal_assistant/enclave/app.py`). `SecureConfig` (`src/signal_assistant/enclave/secure_config.py`) MUST only release critical config (e.g., LLM API keys) post-attestation. No environment variable, CLI flag, or config option on Host or Enclave is permitted to bypass attestation checks for key access. <br/> **Tests:** Negative integration tests: attempts to start Enclave with invalid measurements (mocked) MUST fail to obtain keys. Unit tests for `KMS` and `SecureConfig` to ensure attestation dependency. <br/> **Tooling:** Review of config parsing for critical values to ensure no backdoors.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

## 3. Logging and Observability Enforcement

**Goal:** Define a concrete design for logging/telemetry that satisfies `core` 4.2, 4.6, 10.2, 10.4, 11.2, 11.5, and `privacy` 4 (Data Inventory rows), 7 (Retention), 10 (Auditability).

### 3.1 Central Logging Interface
*   A dedicated, shared logging interface MUST be implemented for both Host and Enclave components. This interface MUST enforce the logging schema constraints defined in `core` 11.5.
    *   **Enclave Logging (`src/signal_assistant/enclave/secure_config.py` or similar module):**
        *   MUST provide functions that accept only `internal_user_id` and explicitly allowed non-sensitive metadata fields.
        *   MUST reject or error if attempts are made to log `SignalID`, plaintext message content, LLM prompts/responses, or other PII.
        *   MUST ensure logs are anonymized and encrypted before sending to the Host for persistence (if any persistent logging is required beyond ephemeral in-enclave logs).
    *   **Host Logging (`src/signal_assistant/host/proxy.py` or similar module):**
        *   MUST consume logs from the Enclave (already anonymized/encrypted by Enclave).
        *   MUST provide logging functions that accept only `internal_user_id` and explicitly allowed non-sensitive metadata.
        *   MUST reject or error if attempts are made to log `SignalID`, plaintext message content, LLM prompts/responses, or other PII directly on the Host.
        *   MUST enforce the 30-day retention policy (`privacy` 10.1.4).

### 3.2 Static Analysis / Linting Rules
*   Custom static analysis or linting rules (e.g., using `ruff` plugins, custom `pylint` checks, or `grep`/`ripgrep` hooks in CI) MUST be developed and integrated into the CI/CD pipeline. These rules will target:
    *   **Forbidden Keywords:** Flagging direct logging of strings like "prompt:", "response:", "message body:", or variable names strongly suggesting sensitive content (e.g., `raw_message`, `user_input_text`).
    *   **PII Patterns:** Detecting attempts to log strings matching common PII patterns (e.g., regex for phone numbers, email addresses) directly in logging calls (unless explicitly within the `PIISanitizer` context).
    *   **Raw `Signal_ID` Logging:** Forbidding the logging of `Signal_ID`s outside of the `IdentityMappingService` (where it's used for mapping only, not logged).
    *   **Derivative Logging:** Prohibiting the logging of hashed/fingerprinted derivatives of content or `Signal_ID`s that could act as stable, pseudo-anonymous identifiers beyond the allowed `internal_user_id` (e.g., `md5(message_body)`, `sha256(Signal_ID)`).

### 3.3 Runtime Assertions/Tests
*   **Unit Tests:** For the central logging interfaces (Enclave and Host), unit tests MUST assert that:
    *   Attempts to log forbidden content (plaintext PII, Signal IDs) result in defined errors or rejections.
    *   Only allowed fields are successfully processed and formatted.
*   **Integration Tests:** End-to-end integration tests MUST be developed to verify:
    *   **Synthetic Message Flow:** Given synthetic user messages with known PII and Signal IDs, the final Host-visible operational logs (using mocks for external LLMs) contain *no traces* of the PII, Signal IDs, or their simple encodings.
    *   **Host Blindness Check:** Tests SHOULD attempt to simulate a malicious Host reading logs or memory and confirm that sensitive data is not exposed.

## 4. LLM Prompt Construction and Sanitization Pipeline

**Goal:** Design a concrete prompt pipeline that enforces `core` 7.1–7.3, 8.1.7, 8.2.1, 10.1, 10.3, and `privacy` 5.2, 6.2.

### 4.1 Single, Well-Defined Pipeline
*   A single, canonical `LLMPipeline` (or similar orchestrator, likely in `src/signal_assistant/enclave/bot/orchestrator.py`) MUST be established within the Enclave for all interactions with external LLMs. This pipeline will encompass:
    1.  **User message reception:** From the Enclave's Signal Protocol Stack.
    2.  **Context retrieval:** Fetching relevant (sanitized) conversational context or `LongTermMemory`.
    3.  **Tool calls:** Orchestrating and integrating outputs from any Enclave-internal or securely mediated external tools.
    4.  **Final prompt assembly:** Constructing the complete prompt string.
    5.  **PII Sanitization:** Passing the *fully assembled prompt string* through the `PIISanitizer` (`src/signal_assistant/enclave/privacy_core/sanitizer.py`).
    6.  **External LLM interaction:** Sending the *sanitized* prompt to the LLM API Proxy/Client.
*   **No Bypass Path:** There MUST NOT be any code path within the Enclave that sends text to an external LLM without passing through this `LLMPipeline` and its integrated PII sanitization step.

### 4.2 Interface Signatures
*   **`LLMPipeline` (within `orchestrator.py`):**
    ```python
    def process_user_request(
        internal_user_id: str,
        user_message: str,  # Plaintext, from Signal Protocol Stack
        context_data: Optional[Dict[str, Any]] = None, # sanitized context/memory
        tools: Optional[List[Tool]] = None,
    ) -> str: # Returns LLM response after processing and internal safety checks
        # ... internal orchestration ...
        final_prompt = _assemble_prompt(user_message, context_data, tool_outputs)
        sanitized_prompt = PII_Sanitizer.sanitize(final_prompt)
        llm_response = LLM_Client.call_llm(sanitized_prompt, internal_user_id)
        # ... post-processing, safety checks ...
        return llm_response
    ```
*   **`PIISanitizer` (within `sanitizer.py`):**
    ```python
    class PIISanitizer:
        @staticmethod
        def sanitize(text: str) -> str:
            # ... regex matching, redaction logic ...
            return sanitized_text
    ```

### 4.3 Unit and Integration Tests
*   **Unit Tests for `PIISanitizer`:**
    *   MUST cover a comprehensive set of known PII patterns (phone numbers, various email formats, potentially other identified PII types).
    *   MUST assert that PII is correctly redacted or replaced with generic tokens.
    *   MUST include edge cases (e.g., PII at beginning/end of string, multiple PII instances, no PII).
*   **Integration Tests for `LLMPipeline`:**
    *   **Unsanitized Input Scenario:** Develop tests where synthetic `user_message`, `context_data`, and `tool_outputs` *intentionally contain PII*. These tests MUST assert that the mock external LLM *receives a sanitized prompt*, and the original PII is not present in the outgoing mock call.
    *   **Bypass Detection:** Negative tests designed to simulate direct calls to `LLM_Client.call_llm` that bypass `PIISanitizer` (potentially through static analysis rather than runtime test).
    *   **Combinatorial Tests:** Cover combinations of inputs to ensure sanitization is consistent regardless of prompt complexity.

## 5. Key Management & Attestation Gating

**Goal:** Translate `core` 9.1–9.4 and Invariants 10.1, 10.2 into concrete APIs for key access within the Enclave and a clear model for attestation gating.

### 5.1 Concrete APIs for Key Access within Enclave
*   **`KMS` Module (`src/signal_assistant/enclave/kms.py`):**
    *   MUST be the single source of truth for all key generation, storage, retrieval, and deletion within the Enclave.
    *   **`get_key(key_id: KeyID, attestation_verified: bool) -> bytes`:** A unified API that *explicitly* requires an `attestation_verified` flag. Access to sensitive keys (SPKs, ESSKs, EAKs) MUST be conditional on this flag being `True`.
    *   **`seal_key(key_id: KeyID, plaintext_key: bytes) -> EncryptedKeyBlob`:** Encrypts a key using the ERK for persistent storage.
    *   **`unseal_key(encrypted_blob: EncryptedKeyBlob, attestation_verified: bool) -> bytes`:** Decrypts a key, again conditional on `attestation_verified`.
*   **`SecureConfig` Module (`src/signal_assistant/enclave/secure_config.py`):**
    *   MUST manage sensitive configuration values, especially External Service API Keys (EAKs).
    *   **`get_llm_api_key(internal_user_id: Optional[str] = None) -> str`:** MUST internally call `KMS.get_key` with the `attestation_verified` flag derived from the Enclave's current attested state.

### 5.2 Attestation Gating Model
*   **Host-Side Provisioning:** The Host's Enclave launcher/orchestrator (`src/signal_assistant/host/proxy.py` or similar) MUST only provision External Service API Keys (EAKs) to the Enclave *after* successfully verifying the Enclave's attestation report against a known-good measurement. This provisioning MUST occur via an encrypted channel such that the Host never sees the EAK in plaintext (`core` 9.4.3).
*   **Enclave-Side Gating:**
    *   The `EnclaveApp` (`src/signal_assistant/enclave/app.py`) MUST perform its own internal attestation verification during initialization. This verification result MUST set an internal `self.attestation_is_verified: bool` flag.
    *   All calls to `KMS.get_key` and `KMS.unseal_key` for sensitive key types (SPKs, ESSKs, EAKs) MUST reference this `self.attestation_is_verified` flag. If `False`, the operation MUST fail securely (e.g., raise an `AttestationError`).
*   **"No Debug/Emergency Override" Invariant (`core` 9.4.3):**
    *   Code review and architectural design MUST explicitly prohibit any environment variable, CLI flag, configuration setting, or hardcoded value that bypasses the attestation checks for key access.
    *   This includes ensuring that `SecureConfig` does not have alternative code paths for obtaining EAKs when attestation fails.

### 5.3 Expected Tests
*   **Negative Tests (Attestation Failure):**
    *   An integration test suite MUST simulate (or use a TEE test harness) an Enclave starting with *unexpected/invalid attestation measurements*. These tests MUST assert that:
        *   The Host-side provisioning logic *refuses to provide EAKs* to this Enclave.
        *   Even if (hypothetically) EAKs were provisioned, the Enclave's internal `KMS.get_key` and `unseal_key` calls for sensitive keys *fail due to `attestation_is_verified` being `False`*.
    *   These tests validate the "no debug bypass" invariant.
*   **Regression Tests:**
    *   Any new sensitive key type introduced (e.g., for a new external service) MUST be registered with `KMS` and `SecureConfig` such that it falls under the same attestation gating regime. Tests MUST be added to verify this for new key types.
*   **Unit Tests:** For `KMS.get_key`, `KMS.unseal_key`, and `SecureConfig.get_llm_api_key` to confirm they correctly gate access based on the `attestation_verified` flag.

## 6. Identity Mapping, Deletion, and LE Control Path

**Goal:** Map from `core` 5.1–5.2, 6.1.3, and `privacy` 8 (Identity), 9 (LE), 7.3, 12.3 to concrete enclave interfaces and control paths.

### 6.1 Enclave Interface for Identity Management
*   **`IdentityMappingService` (`src/signal_assistant/enclave/privacy_core/core.py`):**
    *   **`map_signal_id_to_internal_id(signal_id: SignalID) -> InternalUserID`:**
        *   Input: Raw `SignalID`. Output: `InternalUserID`.
        *   MUST perform the mapping and persist it encrypted in secure storage (`core` 5.1.1.1-3).
        *   MUST be the *only* component directly handling `SignalID` for mapping purposes.
    *   **`delete_user_data(internal_user_id: InternalUserID)`:**
        *   Input: `InternalUserID`.
        *   MUST trigger the deletion of:
            *   The `(Signal_ID, internal_user_id)` mapping from secure storage (`privacy` 7.3).
            *   All `LongTermMemory` associated with `internal_user_id`.
            *   Any other persisted user-specific configuration/preferences.
            *   (Via Host IPC): Notify Host to delete or schedule deletion of Host-side metadata uniquely keyed by `internal_user_id` (e.g., `Host Operational Logs` entries older than 30 days are automatically purged, but more recent entries should be marked for accelerated deletion if possible).
    *   **`handle_le_request(request_type: LE_REQUEST_TYPE, target_id: Union[SignalID, InternalUserID], auth_context: Dict) -> LE_RESPONSE`:**
        *   Input: Type of LE request, target ID (could be `SignalID` or `InternalUserID`), authorization context (e.g., legal order details).
        *   MUST call `CHECK_LE_POLICY` (`privacy` 9.4.3) internally *before* any data access.
        *   If `CHECK_LE_POLICY` permits, it MAY retrieve:
            *   `SignalID` for a given `internal_user_id` (if `request_type` allows and `auth_context` is valid).
            *   Limited host-side operational logs associated with `internal_user_id` (if `request_type` allows).
        *   MUST enforce multi-party authorization for sensitive LE requests (`privacy` 9.1.2.3).
        *   MUST default to DENY in ambiguous cases (`privacy` 9.4.3).

### 6.2 Allowed Callers and Preconditions
*   `map_signal_id_to_internal_id`: Only callable by the `EnclaveApp` after initial Signal message decryption.
*   `delete_user_data`: Callable via a securely authenticated control command (`core` 6.1.2) from the user or by an authorized internal system administrative command (`core` 6.1.3) within the Enclave.
*   `handle_le_request`: Callable only by an explicitly designated and authenticated internal administrative API endpoint within the Enclave, which itself MUST be gated by external multi-party controls.

### 6.3 Data Deletion for "User Deletion" Request (`privacy` 7.3)
When `delete_user_data(internal_user_id)` is called:
*   **Mapping:** The `(Signal_ID, internal_user_id)` mapping MUST be irrevocably purged from the Enclave's secure storage.
*   **Long-Term Memory & Persisted Context:** All `LongTermMemory` entries (redacted summaries, embeddings) and any persisted conversational context/state linked to that `internal_user_id` MUST be purged.
*   **Host-side metadata:** The Host (`src/signal_assistant/host/storage/database.py`, `src/signal_assistant/host/proxy.py`) MUST be instructed (via secure Enclave-to-Host IPC) to delete any metadata uniquely keyed by `internal_user_id` (e.g., non-content Signal metadata, Host operational logs related to that ID, subject to its own TTL and log purging policies). The instruction will prioritize immediate deletion where technically feasible.

### 6.4 Auditing and Testing LE Operations
*   **Auditing:** All calls to `handle_le_request` (including successful and failed `CHECK_LE_POLICY` evaluations) MUST be securely logged *within the Enclave* (ephemerally, or anonymized/encrypted and sent to Host logs as per `core` 11.5). These logs MUST include `request_type`, `target_id` (if `internal_user_id`), `auth_context` (sanitized), and the `LE_RESPONSE` outcome.
*   **Tests:**
    *   **Positive Tests:** A mock LE request (with valid `auth_context`) MUST be used to confirm that `handle_le_request` correctly retrieves an `internal_user_id`'s associated `SignalID` (if that specific capability is enabled and requested) or provides limited operational logs, strictly adhering to `CHECK_LE_POLICY` and `privacy` 9.1.2.
    *   **Negative Tests:** Mock LE requests with invalid `auth_context` or for forbidden data types (e.g., plaintext messages) MUST assert that `CHECK_LE_POLICY` returns `DENY` and no sensitive data is exposed.
    *   **Multi-party Control Mock:** Simulate the external multi-party control process to ensure the `handle_le_request` endpoint is not directly callable without proper authorization.

## 7. Tasks and Execution Plan

This section outlines concrete, execution-ready tasks for implementing the spec-enforcement phase. Each task references relevant spec sections and specifies required tests/guardrails.

### 7.1 Central Logging/Telemetry Module + Schema Enforcement
*   **Task:** Refactor Host and Enclave logging to use unified interfaces that enforce `core` 11.5 schema constraints.
    *   **Spec References:** `core` 4.2, 4.6, 10.2, 10.4, 11.2, 11.5; `privacy` 4, 7, 10.
    *   **Tests/Guardrails:**
        *   Unit tests for new logging interfaces to reject forbidden content.
        *   Integration test: synthetic message flow, assert Host logs contain no PII/Signal IDs.
        *   Static analysis rule: forbid `SignalID` and plaintext PII patterns in logging calls.
*   **Estimated Effort:** Medium

### 7.2 Prompt Pipeline Refactor and Final-Prompt Sanitizer Integration
*   **Task:** Implement a single `LLMPipeline` in the Enclave that centralizes prompt construction and integrates mandatory `PIISanitizer` before external LLM calls.
    *   **Spec References:** `core` 7.1–7.3, 8.1.7, 8.2.1, 10.1, 10.3; `privacy` 5.2, 6.2.
    *   **Tests/Guardrails:**
        *   Unit tests for `PIISanitizer` with diverse PII patterns.
        *   Integration test: `LLMPipeline` receives PII-laden input, sends sanitized prompt to mock LLM.
        *   Static analysis rule: detect direct LLM client calls bypassing `LLMPipeline`.
*   **Estimated Effort:** Medium

### 7.3 Key-Access APIs + Attestation Gate Wiring
*   **Task:** Update `KMS` and `SecureConfig` APIs to include `attestation_verified` flag and enforce attestation gating for sensitive key access.
    *   **Spec References:** `core` 9.1–9.4, 10.1, 10.2.
    *   **Tests/Guardrails:**
        *   Unit tests for `KMS.get_key`, `unseal_key` with `attestation_verified` flag.
        *   Negative integration test: Enclave with invalid attestation fails to obtain keys.
        *   Code review: verify no bypass paths for key access.
*   **Estimated Effort:** High

### 7.4 Identity/Deletion/LE Control Path in Enclave Code + Tests
*   **Task:** Implement/refactor `IdentityMappingService` for user deletion and the `handle_le_request` API with `CHECK_LE_POLICY` and multi-party authorization enforcement.
    *   **Spec References:** `core` 5.1–5.2, 6.1.3; `privacy` 8, 9, 7.3, 12.3.
    *   **Tests/Guardrails:**
        *   Unit tests for `IdentityMappingService` (mapping, deletion).
        *   Unit tests for `handle_le_request` (positive LE request, negative LE request with invalid auth).
        *   Integration test: simulate user deletion, assert mappings/memory purged.
        *   Integration test: simulate LE request, assert `CHECK_LE_POLICY` enforcement.
*   **Estimated Effort:** High

### 7.5 Integration Tests for Core Invariants
*   **Task:** Develop end-to-end integration tests to verify critical system-level invariants.
    *   **Spec References:** `core` 10.1, 10.2, 10.5, 10.6; `privacy` relevant sections.
    *   **Tests/Guardrails:**
        *   **"no plaintext at rest"**: Test that after processing, no sensitive plaintext remains in any Host-side persistent storage or memory (use mocked persistence layers).
        *   **"no unsanitized prompt to external LLM"**: Confirm `LLMPipeline`'s sanitization as per Task 7.2.
        *   **"LE mapping requires CHECK_LE_POLICY and multi-party controls"**: Confirm `handle_le_request`'s behavior as per Task 7.4.
*   **Estimated Effort:** Medium/High

## 8. Traceability

This proposal ensures traceability from core/privacy invariants to enforcement mechanisms through explicit cross-referencing.

*   **Invariant-to-Enforcement Mapping (Section 2):** Provides a direct link from cited `core`/`privacy` sections to the code, tests, and tooling that enforce them.
*   **Task-level References (Section 7):** Each task explicitly lists the `core`/`privacy` spec sections it implements and the tests/guardrails it will introduce.

**Goal:** Given any section number from `docs/signal_assistant_core.md` or `docs/privacy_architecture.md` (e.g., `core` 10.4, `privacy` 9.1.1.2), one can locate:
1.  **The enforcement design:** Within Section 2 and its detailed sub-sections in this proposal.
2.  **The code/tests that implement it:** Through the described code modules and associated tests/guardrails within this proposal's tasks.

## Summary

This proposal establishes a robust framework for **spec-driven enforcement** of privacy and security invariants for the Signal Assistant. It details concrete designs for:
*   A centralized, schema-enforced logging and observability system.
*   A mandatory, PII-sanitizing LLM prompt construction pipeline.
*   Attestation-gated key management and provisioning.
*   Secure identity mapping, user data deletion, and a strictly controlled Law Enforcement access path.

The proposal includes a detailed mapping of invariants to enforcement mechanisms, outlining necessary code changes, unit/integration tests, and static analysis tooling. It ensures strong traceability from high-level specifications to implementation details.

**Remaining Gaps:**
*   **Advanced PII Detection:** While basic PII sanitization is covered, more advanced, context-aware PII detection (e.g., for custom PII types or more complex patterns) is an area for future enhancement.
*   **Formal Verification:** The proposal does not include formal verification of critical enclave code, which could further strengthen guarantees but is a significant undertaking.
*   **Memory Analysis Tooling:** Development of runtime memory analysis tools for enclaves to detect sensitive data persistence is noted as a future tooling consideration.