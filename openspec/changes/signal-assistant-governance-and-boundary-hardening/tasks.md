# Tasks

## 1. Registry Integrity & Enclave Status
- [X] Implement signature verification for `measurement_registry.json` in Host. <!-- id: task-registry-sig-host -->
- [X] Add `status` field checks to `KeyManagementService` (enclave-side). <!-- id: task-kms-status-check -->
- [X] Update `EnclaveApp` to ingest and verify registry status on startup. <!-- id: task-enclave-registry-ingest -->
- [X] Add tests for revoked/unknown measurements causing KMS seal failure. <!-- id: task-registry-tests -->

## 2. Environment & Capabilities Governance
- [X] Create `src/signal_assistant/enclave/capabilities.py` defining `DangerousCapabilities`. <!-- id: task-cap-manifest -->
- [X] Implement `DangerousCapabilities` check in `verify_release_build.py`. <!-- id: task-ci-cap-check -->
- [X] Add runtime panic in `EnclaveApp` if `PROD` and `DangerousCapabilities` active. <!-- id: task-runtime-cap-check -->
- [X] Refactor existing `MOCK_ATTESTATION` usage to use the new manifest. <!-- id: task-refactor-mock -->
- [X] Add tests for "PROD with dangerous capability" rejection. <!-- id: task-cap-tests -->

## 3. Policy Drift & Release Pipeline
- [X] Define `InvariantManifest` schema and generate initial manifest. <!-- id: task-invariant-manifest -->
- [X] Update `policy_drift_check.py` to compare `InvariantManifest` versions. <!-- id: task-drift-check-update -->
- [X] Integrate `policy_drift_check` and `openspec validate` into release pipeline. <!-- id: task-pipeline-integrate -->
- [X] Add scenarios for permissible vs. impermissible drift. <!-- id: task-drift-tests -->

## 4. Enclave OSS Boundary
- [X] Add `import-linter` or similar check to forbid `enclave -> host` imports. <!-- id: task-boundary-lint -->
- [X] Create `pyproject.toml` (or build config) for `signal-assistant-enclave` package. <!-- id: task-enclave-pkg -->
- [X] Create minimal enclave-only test harness (no host code). <!-- id: task-enclave-harness -->
- [X] Verify `signal-assistant-enclave` builds and passes tests in isolation. <!-- id: task-verify-pkg -->
