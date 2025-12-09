# Enclave Version Management

This document captures the manual steps that maintainers use to advance the `signal-assistant-enclave` release train and keep the host's `measurement_registry.json` in sync with deployable tags.

## 1. Prepare an enclave release

1. Kick off the OpenSpec change in the host repository if the change affects invariants or the attestation story. The enclave release SHOULD correspond to an approved change so that auditors can trace from a tag back to the spec.
2. In the enclave repository:
   - Update `pyproject.toml` to the new semantic version (e.g., `version = "1.2.0"`).
   - Run the enclave CI locally (`poetry run pytest`, `poetry run ruff check src tests`, `poetry run mypy src tests`).
   - Commit the changes and push to the enclave `main` branch.
3. Create a signed git tag in the enclave repo that mirrors the version using the `vX.Y.Z` format. Example:
   ```bash
   git tag -a v1.2.0 -m "Release enclave v1.2.0"
   git push origin v1.2.0
   ```

## 2. Capture the attested measurement

1. Run `ci/verify_release_build.py` from the host repository to build the enclave candidate for the target profile and produce a candidate registry entry. Provide `--output` to serialize the entry and include the generated `mrenclave`.
2. Use `tools/registry.py add` to insert the entry into `measurement_registry.json`, ensuring you pass `--name signal-assistant-enclave` and `--tag v<version>` so the entry records the git tag that corresponds to the release:
   ```bash
   python3 tools/registry.py add \
     --mrenclave <sha> \
     --version 1.2.0 \
     --tag v1.2.0 \
     --commit <enclave-commit> \
     --profile PROD
   ```
3. The registry entry now contains the tuple `(name, version, tag, git_commit)`. The host CI (via `ci/verify_release_build.py`) will later validate that every active entry references a tag that points to the recorded commit. If that check fails, the release cannot be merged.

## 3. Update the host submodule and registry

1. In the host repository, update the `enclave_package` submodule to the new enclave commit and commit the change.
2. Ensure `measurement_registry.json` contains the new entry that references the same commit and tag. If you are patching an existing entry (e.g., adding `tag` after the fact), edit the file manually or rerun `tools/registry.py add` and remove outdated entries as appropriate.
3. Run host CI (which exercises `ci/verify_release_build.py`) to confirm:
   - The host submodule is clean and matches the new commit.
   - Every `measurement_registry.json` active entry points to an existing `signal-assistant-enclave` git tag.
   - The `ci/verify_release_build.py` guard ensures the submodule commit is recorded as `active` and that the tag/commit mapping matches the registry entry.

## 4. Auditing & Trust Story

- Auditors verify a running enclave by comparing the `mrenclave` returned during attestation to an entry in `measurement_registry.json`.
- Each registry entry records the git tag (`vX.Y.Z`), the enclave `git_commit`, and the semantic `version`. The `tag` field makes it easy to check out the exact release.
- With that tag, auditors can inspect the public `signal-assistant-enclave` Git history, read `README.md`/`SECURITY.md`/`CONTRIBUTING.md`, and confirm the change request via OpenSpec.
- Any attempt to run a commit/tag not present in `measurement_registry.json` or without a matching `tag` will fail the host CI and therefore cannot be deployed.

For more detail on the trust story and how auditors trace measurements to OpenSpec changes, see `docs/enclave_integration.md` and `docs/release_process.md`.
