# Implementation Tasks

## Phase 1: Identity & Logging Wiring
- [x] Refactor `EnclaveApp` to instantiate `IdentityMappingService`. <!-- id: wiring-1 -->
- [x] Update `EnclaveApp` to map `SignalID` to `internal_user_id` immediately upon message receipt. <!-- id: wiring-2 -->
- [x] Ensure `EnclaveApp` uses only `internal_user_id` for all downstream processing and logging. <!-- id: wiring-3 -->
- [x] Remove shadow LE policy logic from `EnclaveApp` and delegate to `IdentityMappingService`. <!-- id: wiring-4 -->
- [x] Verify `SignalID` does not appear in logs (Integration Test). <!-- id: test-wiring -->

## Phase 2: LLM Pipeline Hardening
- [x] Define `SanitizedPrompt` type (dataclass/class). <!-- id: llm-1 -->
- [x] Update `PIISanitizer.sanitize` to return `SanitizedPrompt`. <!-- id: llm-2 -->
- [x] Update `LLMClient.generate_response` to accept only `SanitizedPrompt`. <!-- id: llm-3 -->
- [x] Update `LLMPipeline` to assemble prompt and sanitize it before calling client. <!-- id: llm-4 -->
- [x] Strengthen `PIISanitizer` regexes for international phones and robust emails. <!-- id: llm-5 -->
- [x] Verify type enforcement and regex robustness (Unit Tests). <!-- id: test-llm -->

## Phase 3: Attestation Gating
- [x] Refactor `EnclaveApp._perform_attestation_verification` to fail closed (return `False`) by default. <!-- id: attest-1 -->
- [x] Implement a strict override mechanism for testing (e.g., specific env var with warning). <!-- id: attest-2 -->
- [x] Verify `KMS` denies access when attestation fails. <!-- id: test-attest -->

## Phase 4: Persistence & Deletion
- [x] Implement `load_state` and `save_state` in `IdentityMappingService`. <!-- id: persist-1 -->
- [x] Update `map_signal_id_to_internal_id` and `delete_user_data` to persist changes. <!-- id: persist-2 -->
- [x] Verify mapping persists across "restarts" (Integration Test). <!-- id: test-persist -->
