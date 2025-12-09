# Signal Assistant Enclave Release Process

This document outlines the "Ceremony" required to release a new version of the Signal Assistant Enclave.

## Prerequisites
- Maintainer access to the `signal-ai` repository.
- `tools/registry.py` and `ci/verify_release_build.py` available.

## Steps

### 1. Build and Verify
Trigger the CI pipeline for the release branch (`release/vX.Y.Z`). The CI will:
1.  Run the full test suite (Core, Privacy, Spec Enforcement).
2.  Compute the candidate `MRENCLAVE`.
3.  Verify that `PROD` profile builds do not contain `MOCK_ATTESTATION` code.
4.  Produce a `candidate_entry.json` artifact.

### 2. Candidate Review
A Release Manager must review the `candidate_entry.json`:
- **Version:** Matches the tag.
- **Commit:** Matches the release tag commit.
- **Profile:** MUST be `PROD` for production releases.

### 3. Registry Update (The Ceremony)
Run the registry tool to add the measurement:

```bash
python3 tools/registry.py add \
  --mrenclave "sha256:..." \
  --version "1.2.0" \
  --commit "a1b2c3d..." \
  --profile "PROD"
```

Commit the change to `measurement_registry.json`:

```bash
git add measurement_registry.json
git commit -S -m "release: authorize enclave v1.2.0"
git push origin main
```

### 4. Deployment
Once the registry change is merged, the Gatekeeper (Host) will automatically accept the new measurement. Redeploy the Enclave service.

## Emergency Patching
Follow the same process. **Never** bypass the registry, as the Host will refuse to start.
