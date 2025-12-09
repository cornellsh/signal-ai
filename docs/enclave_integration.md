# Enclave Integration Documentation

## 1. Two-Repo Model and Rationale

The project deliberately splits into two repositories so that the sensitive enclave code can remain transparent, auditable, and independently released while the Signal-aware host remains private and focused on orchestration, governance, and operational tooling.

* **`signal-assistant-enclave` (Public Repository)** operates as the open-source enclave artifact. Its intended audience is auditors, security researchers, and integrators who want to understand or reuse the privacy-preserving logic without access to the private host. It contains the TEE implementation, the privacy core, the sanitizers, governance checks, and the enclave-specific tests described in `README.md`, `SECURITY.md`, and `CONTRIBUTING.md`.
* **`signal-ai` (Private Host Repository)** is intended for internal developers and operators. It owns Signal integration, host-side persistence, the `measurement_registry.json` specimen, the OpenSpec change system, and the deployment/configuration automation that binds a host build to an attested enclave release.

This separation: (1) keeps the enclave boundary auditable, (2) prevents unsanctioned edits inside the private host, and (3) enables the host to treat the enclave as a cryptographically measured dependency.

## 2. Canonical Sources & OpenSpec

The host repository defines the truth for privacy/invariant governance. Auditors and contributors should reference the following canonical sources:

* `docs/signal_assistant_core.md`
* `docs/privacy_architecture.md`
* `invariant_manifest.py`
* `measurement_registry.json`

Changes that affect these resources must be proposed via OpenSpec (`openspec/changes/`) so that there is an auditable trail linking spec revisions to new enclave releases. Documenting this requirement inside `CONTRIBUTING.md` and `SECURITY.md` helps reinforce the invariant-preserving workflow.

## 3. Workflow for Proposing or Implementing Enclave Changes

1. Propose your change in the enclave repo (issue, doc, etc.). Reflect the same intent in an OpenSpec change inside the private host repo if it touches invariants, attestation, or the trust story.
2. Implement and test the enclave change. The enclave-specific CI (`.github/workflows/ci.yml`) runs `poetry install`, `pytest`, `ruff`, and `mypy` to validate the enclave in isolation.
3. Once the enclave change is ready, create a `vX.Y.Z` git tag whose version matches the `pyproject.toml` version.
4. Run the host release tooling (`ci/verify_release_build.py` and `tools/registry.py`) to compute the `mrenclave`, produce a candidate registry entry, and capture the mapping between the tag, commit, and measurement.
5. Update the host documentation and release notes so auditors know which `measurement_registry.json` entry pairs with the new tag and what OpenSpec change request authorized it.

This document also serves as a guide to understanding how the public enclave code, the measurement registry, and the host infrastructure fit together, even though the host remains private.

## 4. Process for Updating `signal-ai` to a New Enclave Version

1. **Update the Submodule:** After the enclave publishes a new tag, update the `enclave_package` submodule to the tagged commit, verify the clean state, and commit the change in the host repo.
2. **Record the Measurement:** Run `tools/registry.py add` (with `--name signal-assistant-enclave` and `--tag vX.Y.Z`) to insert the `mrenclave`, `version`, `tag`, `git_commit`, and profile into `measurement_registry.json`. This step guarantees that the host has a persistent, human-readable pointer to the enclave tag referenced in CI and production.
3. **Cross-Check:** Host CI uses `ci/verify_release_build.py` to confirm that every active entry in `measurement_registry.json` references a real git tag that points to the recorded commit. If any active entry fails this check, the CI run fails and prevents merging the release.
4. **Enforce Governance:** The host remains responsible for enforcing the registry and invariant model. It must never import enclave internals directly (`ci/static_analysis/check_enclave_imports.py`) and must treat `measurement_registry.json` as the authoritative source of truth for attested enclave code.
5. **Document the Trust Story:** Keep `docs/enclave_integration.md`, `docs/release_process.md`, and `docs/enclave_version_management.md` updated so external parties know how to trace a running enclave back to its git tags, OpenSpec change, and registry entry.

## 5. Trust Story for Third-Party Auditors

Auditors who want to verify the enclave can follow these steps:

1. **Obtain an Attestation Quote:** Capture the enclave’s `mrenclave` from the attested runtime (real TEE or simulation). This measurement is the cryptographic anchor of the enclave.
2. **Consult `measurement_registry.json`:** Look up the measurement entry (typically the most recent `status: active` entry). It now includes `name`, `version`, `tag`, `git_commit`, and `profile`, which lets the auditor confirm the identity of the enclave and the intended deployment profile.
3. **Map to a Git Tag:** Use the recorded `tag` (or the normalized `vX.Y.Z` version) to check out the `signal-assistant-enclave` repository at that tag. Inspect `README.md`, `SECURITY.md`, and `CONTRIBUTING.md` to understand how the enclave was built and what behaviors are expected.
4. **Verify OpenSpec Traceability:** The `tag` should correspond to an OpenSpec change in the private host repo. That change ensures the invariant and governance context is documented for audit trails and release notes.
5. **Check Host CI Guards:** When the host builds with this enclave, `ci/verify_release_build.py` runs. It guarantees that the submodule commit is recorded in `measurement_registry.json`, that the commit status remains `active`, and that the measurement entry references a `vX.Y.Z` tag. Any deviation results in a CI failure.

This layered process ensures that every deployed enclave can be traced to a public tag, a registry entry, and a documented change request, satisfying auditors' expectations while keeping the host boundary private.
