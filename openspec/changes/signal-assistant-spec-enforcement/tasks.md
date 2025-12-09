# Tasks: Signal Assistant Spec-Enforcement Execution Plan

This document outlines the concrete, execution-ready tasks required to implement the spec-enforcement phase for the Signal Assistant. Each task is designed to be small, verifiable, and references the relevant sections of the `Signal Assistant Core Specification` (core) and `Signal Assistant Enclave Privacy Architecture Document` (privacy).

---

## Phase 1: Foundational Updates & Logging Enforcement

### Task 1.1: Refactor Host Logging Interface

*   **Description:** Create a new Host-side logging module (`src/signal_assistant/host/logging_client.py`) with explicit functions for allowed log fields. Replace direct logging calls in Host components (`src/signal_assistant/host/proxy.py`, `src/signal_assistant/host/transport.py`, `src/signal_assistant/host/storage/`) with calls to this new interface.
*   **Spec References:** `core` 4.1, 4.2, 4.6, 10.4, 11.5; `privacy` 4.1, 10.1.
*   **Tests/Guardrails:**
    *   Unit tests for `logging_client.py` to ensure it rejects `SignalID` and plaintext PII.
    *   `rg` checks to confirm no direct `logging.*` calls in Host core modules.
*   **Dependencies:** None.
*   **Estimated Effort:** Medium.

### Task 1.2: Refactor Enclave Logging Interface

*   **Description:** Create a new Enclave-side secure logging module (`src/signal_assistant/enclave/secure_logging.py`) that enforces `core` 11.5 schema, accepts only `internal_user_id` and allowed metadata, and handles anonymization/encryption before forwarding to Host (if persistent). Replace direct logging calls in Enclave components (`src/signal_assistant/enclave/app.py`, `src/signal_assistant/enclave/bot/`, `src/signal_assistant/enclave/kms.py`, etc.) with calls to this new interface.
*   **Spec References:** `core` 4.3, 4.6, 10.4, 11.5; `privacy` 4.1, 10.1.
*   **Tests/Guardrails:**
    *   Unit tests for `secure_logging.py` to reject forbidden content and ensure proper anonymization.
    *   `rg` checks to confirm no direct `logging.*` calls in Enclave core modules.
*   **Dependencies:** Task 1.1 (Host-side logging interface).
*   **Estimated Effort:** Medium.

### Task 1.3: Develop Static Analysis for Logging Violations

*   **Description:** Implement custom static analysis rules (e.g., using `pylint` or `ruff` plugins) or `ripgrep` patterns in CI to:
    *   Detect attempts to log forbidden keywords like "prompt:", "response:", "message body:".
    *   Detect attempts to log `SignalID` or common PII patterns (phone numbers, emails) directly in log messages outside of the `PIISanitizer` context.
    *   Block direct usage of `logging` module functions in core Host and Enclave files (forcing use of new interfaces).
*   **Spec References:** `core` 10.4, 11.5.
*   **Tests/Guardrails:** Integrate into CI pipeline; verify it flags mock violations in test branches.
*   **Dependencies:** None (can be developed in parallel).
*   **Estimated Effort:** Medium.

### Task 1.4: Integration Test for Host Logging Blindness

*   **Description:** Create an integration test (`tests/test_logging_blindness.py`) that simulates a full message flow (user -> Host -> Enclave -> Host -> user) using synthetic messages with known PII and Signal IDs. This test MUST mock external LLM calls. It will then inspect the Host's *actual* log files to assert that no plaintext PII, raw `SignalID`, or their simple encodings appear.
*   **Spec References:** `core` 10.2, 10.4, 11.5; `privacy` 4.1, 5.3, 10.1.
*   **Tests/Guardrails:** Test passes if Host logs are clean; fails otherwise.
*   **Dependencies:** Task 1.1, Task 1.2, basic Host-Enclave message flow operational.
*   **Estimated Effort:** High.

## Phase 2: LLM Prompt Pipeline Enforcement

### Task 2.1: Refactor `PIISanitizer` Module

*   **Description:** Ensure `src/signal_assistant/enclave/privacy_core/sanitizer.py` has a clear, static `sanitize(text: str) -> str` interface. Implement robust regex-based detection and redaction for common PII patterns (phone numbers, email addresses).
*   **Spec References:** `core` 4.3.1, 7.1.3, 8.1.7, 10.3; `privacy` 5.2.1, 6.2.
*   **Tests/Guardrails:**
    *   Comprehensive unit tests for `PIISanitizer.sanitize` covering various PII inputs, edge cases, and non-PII strings.
*   **Dependencies:** None.
*   **Estimated Effort:** Low.

### Task 2.2: Implement `LLMPipeline` Orchestration in Enclave

*   **Description:** Create/refactor a central `LLMPipeline` component (`src/signal_assistant/enclave/bot/orchestrator.py`) to manage all LLM interactions. This component MUST encapsulate user message input, context retrieval, tool calls, *final prompt assembly*, and then *mandatorily* pass the assembled prompt through `PIISanitizer.sanitize` before calling the external LLM client.
*   **Spec References:** `core` 7.1, 7.2, 7.3, 8.1.8, 8.2.1, 10.1, 10.3.
*   **Tests/Guardrails:**
    *   Unit tests for `LLMPipeline` mocking dependencies to verify the flow.
*   **Dependencies:** Task 2.1.
*   **Estimated Effort:** Medium.

### Task 2.3: Integration Test for PII Sanitization Enforcement

*   **Description:** Develop an integration test (`tests/test_llm_pipeline_sanitization.py`) that simulates a user interaction where the `user_message`, internal `context`, or mocked `tool_outputs` *intentionally contain PII*. This test MUST then assert that the mocked external LLM API client (`src/signal_assistant/enclave/bot/llm.py`) receives a version of the prompt where all PII has been redacted by the `PIISanitizer`.
*   **Spec References:** `core` 7.1.3, 10.3, 8.2.1; `privacy` 5.2.2.
*   **Tests/Guardrails:** Test passes if PII is redacted; fails if PII reaches the mock LLM client.
*   **Dependencies:** Task 2.2, mocked external LLM client.
*   **Estimated Effort:** High.

## Phase 3: Key Management & Attestation Gating Enforcement

### Task 3.1: Modify KMS APIs for Attestation Gating

*   **Description:** Update `src/signal_assistant/enclave/kms.py` to include an `attestation_verified: bool` parameter in key retrieval (`get_key`) and unsealing (`unseal_key`) functions. Sensitive keys (SPKs, ESSKs, EAKs) MUST only be returned if this flag is `True`. Implement a new `AttestationError` exception.
*   **Spec References:** `core` 9.1, 9.2, 9.4.3.
*   **Tests/Guardrails:**
    *   Unit tests for `kms.py` verifying that calls for sensitive keys with `attestation_verified=False` raise `AttestationError`.
*   **Dependencies:** None.
*   **Estimated Effort:** Medium.

### Task 3.2: Implement Enclave Internal Attestation Verification

*   **Description:** In `src/signal_assistant/enclave/app.py` (or a dedicated `AttestationService`), implement the logic to perform internal attestation verification during Enclave startup. Store the result in a `self.attestation_is_verified: bool` flag. Ensure all calls to `kms.get_key` and `kms.unseal_key` for sensitive types use this flag.
*   **Spec References:** `core` 9.4, 9.4.3.
*   **Tests/Guardrails:**
    *   Unit tests for `enclave/app.py` mocking attestation results, verifying `attestation_is_verified` state.
*   **Dependencies:** Task 3.1.
*   **Estimated Effort:** Medium.

### Task 3.3: Host-Side EAK Provisioning Integration

*   **Description:** Modify the Host's EAK provisioning logic (where external service API keys are provided to the Enclave, likely part of `src/signal_assistant/host/proxy.py` or startup scripts) to ensure EAKs are *only* sent to the Enclave *after* the Host has successfully verified the Enclave's attestation report. This provisioning must use an encrypted channel.
*   **Spec References:** `core` 9.1.5, 9.4.3.
*   **Tests/Guardrails:**
    *   Integration test: Host attempts to provision EAK to a mocked Enclave with invalid attestation report; assert provisioning fails.
*   **Dependencies:** Task 3.2, working attestation verification on Host.
*   **Estimated Effort:** Medium.

### Task 3.4: Negative Integration Test for Attestation Bypass

*   **Description:** Create an integration test (`tests/test_attestation_gating.py`) that uses a mocked Enclave (or TEE test harness) with a deliberately invalid attestation measurement. Assert that this Enclave instance *fails to obtain and use any sensitive keys* (SPKs, ESSKs, EAKs) for operations like message decryption or LLM calls. This test directly verifies the "no debug bypass" invariant.
*   **Spec References:** `core` 9.4.3; `privacy` 11.2.7.
*   **Tests/Guardrails:** Test fails if keys are accessible; passes if key access is denied.
*   **Dependencies:** Task 3.1, Task 3.2, Task 3.3.
*   **Estimated Effort:** High.

## Phase 4: Identity & LE Control Path Enforcement

### Task 4.1: Implement `IdentityMappingService` (Mapping & Deletion)

*   **Description:** Create/refactor `src/signal_assistant/enclave/privacy_core/core.py` to contain the `IdentityMappingService`. Implement `map_signal_id_to_internal_id` and `delete_user_data` methods, ensuring secure storage and comprehensive deletion as specified.
*   **Spec References:** `core` 5.1, 5.2.1, 5.2.2, 10.6; `privacy` 7.3, 8.1, 8.2, 8.3.
*   **Tests/Guardrails:**
    *   Unit tests for mapping: `SignalID` to `InternalUserID` and vice-versa (within Enclave).
    *   Unit tests for `delete_user_data`: verify mapping, long-term memory, config are marked for deletion.
*   **Dependencies:** Enclave secure storage mechanisms.
*   **Estimated Effort:** Medium.

### Task 4.2: Implement `handle_le_request` and `CHECK_LE_POLICY`

*   **Description:** In `src/signal_assistant/enclave/privacy_core/core.py` (or `app.py`), implement `handle_le_request(request_type, target_id, auth_context)` and the internal `CHECK_LE_POLICY` function. `CHECK_LE_POLICY` MUST enforce multi-party authorization and default to DENY. Ensure `handle_le_request` only allows data retrieval (`SignalID` mapping, limited logs) permitted by `privacy` 9.1.2.
*   **Spec References:** `core` 5.1.1.3, 6.1.3; `privacy` 9.1.2.3, 9.4.3, 11.2.9.
*   **Tests/Guardrails:**
    *   Unit tests for `CHECK_LE_POLICY`: positive (valid auth, permitted type) and negative (invalid auth, forbidden type).
    *   Unit tests for `handle_le_request`: verify it calls `CHECK_LE_POLICY` and respects its decision, and only returns allowed data.
*   **Dependencies:** Task 4.1.
*   **Estimated Effort:** High.

### Task 4.3: Integration Test for User Deletion

*   **Description:** Create an integration test (`tests/test_user_deletion.py`) that simulates a user:
    1.  Interacting with the Assistant (generating some mappings, long-term memory).
    2.  Initiating a deletion request.
    3.  Asserting that the `(Signal_ID, internal_user_id)` mapping is purged, associated `LongTermMemory` is cleared, and Host-side metadata is removed (or marked for accelerated removal).
*   **Spec References:** `core` 5.2.1.3, 5.2.2.5; `privacy` 7.3.
*   **Tests/Guardrails:** Test passes if all associated data is irrecoverably deleted.
*   **Dependencies:** Task 4.1, working Host-Enclave IPC.
*   **Estimated Effort:** High.

### Task 4.4: Integration Test for LE Control Path

*   **Description:** Create an integration test (`tests/test_le_control.py`) to verify the LE control path. Simulate valid and invalid LE requests against the Enclave (using `handle_le_request`). Assert that:
    *   Valid requests (with mocked multi-party authorization) return *only* the explicitly permitted data (e.g., `SignalID` mapping for a known `internal_user_id`).
    *   Invalid requests (e.g., for plaintext messages, without multi-party auth, or for an unknown `internal_user_id`) are denied by `CHECK_LE_POLICY` and return no sensitive data.
*   **Spec References:** `core` 5.1.1.4, 6.1.3; `privacy` 9.1, 9.1.1, 9.1.2, 9.4.3.
*   **Tests/Guardrails:** Test passes if LE requests are handled according to policy; fails if policy is violated.
*   **Dependencies:** Task 4.2.
*   **Estimated Effort:** High.

## Phase 5: Spec Delta Documentation

### Task 5.1: Draft `identity-le-control/spec.md`

*   **Description:** Draft the spec delta for identity management and LE control path, detailing requirements for `IdentityMappingService`, `delete_user_data`, `handle_le_request`, and `CHECK_LE_POLICY`. Include `## ADDED Requirements` and `#### Scenario:` sections.
*   **Spec References:** `core` 5, 6.1.3; `privacy` 8, 9, 12.3.
*   **Tests/Guardrails:** Validate with `openspec validate`.
*   **Dependencies:** Tasks 4.1, 4.2.
*   **Estimated Effort:** Medium.

### Task 5.2: Draft `key-management-attestation/spec.md`

*   **Description:** Draft the spec delta for key management and attestation gating, detailing requirements for `KMS` API updates, Enclave internal attestation, and Host-side EAK provisioning. Include `## MODIFIED Requirements` and `#### Scenario:` sections.
*   **Spec References:** `core` 9, 10.1, 10.2; `privacy` 5.2.4, 6.1.
*   **Tests/Guardrails:** Validate with `openspec validate`.
*   **Dependencies:** Tasks 3.1, 3.2, 3.3.
*   **Estimated Effort:** Medium.

### Task 5.3: Draft `llm-prompt-sanitization/spec.md`

*   **Description:** Draft the spec delta for the LLM prompt pipeline and PII sanitization, detailing requirements for `LLMPipeline` and `PIISanitizer` interfaces and mandatory usage. Include `## ADDED Requirements` and `#### Scenario:` sections.
*   **Spec References:** `core` 7.1–7.3, 8.1.7, 8.2.1, 10.1, 10.3; `privacy` 5.2.2, 6.2.
*   **Tests/Guardrails:** Validate with `openspec validate`.
*   **Dependencies:** Tasks 2.1, 2.2.
*   **Estimated Effort:** Medium.

### Task 5.4: Draft `logging-observability/spec.md`

*   **Description:** Draft the spec delta for logging and observability enforcement, detailing requirements for Host and Enclave logging interfaces, static analysis, and runtime checks. Include `## ADDED Requirements` and `#### Scenario:` sections.
*   **Spec References:** `core` 4.2, 4.6, 10.2, 10.4, 11.2, 11.5; `privacy` 4, 7, 10.
*   **Tests/Guardrails:** Validate with `openspec validate`.
*   **Dependencies:** Tasks 1.1, 1.2, 1.3.
*   **Estimated Effort:** Medium.

---

## Overall Validation

### Task 6.1: Run `openspec validate signal-assistant-spec-enforcement --strict`

*   **Description:** Execute the `openspec validate` command with the `--strict` flag to ensure all drafted spec deltas conform to the OpenSpec guidelines and the overall proposal is consistent.
*   **Spec References:** N/A (Tooling requirement).
*   **Tests/Guardrails:** Command must pass without errors.
*   **Dependencies:** All `spec.md` files from Tasks 5.1-5.4.
*   **Estimated Effort:** Low.

### Task 6.2: Final Proposal Review and Sign-off

*   **Description:** Conduct a thorough review of `proposal.md`, `design.md`, and `tasks.md` to ensure completeness, clarity, and alignment with all user requirements and canonical documents.
*   **Spec References:** All.
*   **Tests/Guardrails:** N/A.
*   **Dependencies:** All prior tasks.
*   **Estimated Effort:** Low.
