# Tasks: Signal Assistant Operational Governance

This implementation plan focuses on building the "Control Plane" for Enclave builds: the Registry, the Gatekeeper, and the build-time governance tools.

## Phase 1: The Registry & Build Tools
- [x] **Define Registry Schema:** Create the JSON schema for `measurement_registry.json` including `mrenclave`, `version`, `commit`, `profile`, and `status`.
- [x] **Implement Registry CLI:** Create `tools/registry.py` to:
    - `add`: Compute MRENCLAVE from a docker image/binary and append to registry.
    - `verify`: Check if a given MRENCLAVE exists and is active.
    - `list`: Show all active measurements.
- [x] **Integrate with CI:** Update GitHub Actions / CI pipeline to:
    - Automatically compute MRENCLAVE for every build.
    - Fail if a `PROD` build contains `MOCK_ATTESTATION` code (grep check or symbol check).
    - Generate a "Candidate Registry Entry" artifact for maintainers to approve.

## Phase 2: Runtime Enforcement (The Gatekeeper)
- [x] **Host-Side Check:** Update `src/signal_assistant/host/launcher.py` (or equivalent) to:
    - Load `measurement_registry.json`.
    - Receive the Enclave's Attestation Report.
    - Validate the reported `MRENCLAVE` against the registry.
    - **Fatal Error** if validation fails.
- [x] **Enclave-Side Self-Check:** Update `src/signal_assistant/enclave/app.py`:
    - Add startup logic to check `Config.ENVIRONMENT`.
    - Panic if `ENVIRONMENT == PROD` but `MOCK_ATTESTATION` is enabled.
- [x] **Test: Misconfiguration:** Add an integration test that builds a "poisoned" PROD image (with mock flags) and asserts that it:
    1. Fails CI checks (if possible).
    2. Fails to start (Enclave self-check).

## Phase 3: Client Verification & Policy Drift
- [x] **Client Verification Tool:** Create a standalone script `verify_enclave.py` for auditors/users:
    - Connects to the running Assistant.
    - Requests an Attestation Quote.
    - Verifies the Quote against the public `measurement_registry.json` in the repo.
- [x] **Policy Drift Detector:** Create a script that:
    - Diffs the PII Sanitizer rules between the current commit and the `git_commit` of the last active registry entry.
    - Alerts if rules were removed.

## Phase 4: Documentation & Process
- [x] **Update Release Process:** Document the "Ceremony" for adding a new measurement to the registry (who approves, how to sign).
- [x] **Rollback Runbook:** Document steps to revert to a previous registry entry.
