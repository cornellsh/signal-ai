# Tasks for Signal Assistant Enclave OSS Readiness

This document outlines the high-level tasks required to achieve OSS readiness for the `signal-assistant-enclave` repository. These tasks are ordered to facilitate logical progression and allow for incremental validation.

1.  **Draft and Refine Top-Level Documentation (Enclave Repo)**
    *   **Description**: Create initial drafts and refine `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `LICENSE` files within the `enclave_package/` directory (representing the `signal-assistant-enclave` repo).
    *   **Validation**: Manual review of content for clarity, completeness, and adherence to OSS best practices.

2.  **Implement Enclave Repo CI Workflows**
    *   **Description**: Develop and integrate GitHub Actions workflows into the `signal-assistant-enclave` repo (within `enclave_package/.github/workflows/`) to run `poetry install`, `pytest` (enclave-only tests), and static analysis (`ruff`/`mypy` or existing PII checks).
    *   **Validation**: Successful execution of CI workflows on PRs and `main` branches within the enclave repo. CI failures on test/lint/type-check errors.

3.  **Define and Document Enclave Versioning & Tag Strategy**
    *   **Description**: Establish a SemVer-compliant versioning scheme for the enclave package. Document the process for bumping versions, cutting new git tags (e.g., `vX.Y.Z`), and updating `pyproject.toml` within the `signal-assistant-enclave` repo.
    *   **Validation**: Clear documentation of the versioning strategy. Verifiable application of the strategy in practice (e.g., creating a new tag).

4.  **Update Host Repo Documentation for Two-Repo Model**
    *   **Description**: Modify `docs/enclave_integration.md` and `docs/release_process.md` in the *host* repository to accurately reflect the two-repo model, the distinct roles of each repository, and the mapping between enclave tags/versions and `measurement_registry.json` entries. Include the "trust story" for auditors.
    *   **Validation**: Manual review of updated host documentation for accuracy, consistency, and clarity regarding the cross-repo relationship.

5.  **Implement Registry / Tag Mapping Checks (Host CI)**
    *   **Description**: (Conditional) Develop and integrate checks into the *host* repo's CI pipeline to verify that entries in `measurement_registry.json` correctly reference existing git tags and versions within the `signal-assistant-enclave` submodule.
    *   **Validation**: Host CI successfully identifies and fails if `measurement_registry.json` contains references to non-existent enclave tags/versions.

6.  **Develop Enclave Versioning Helper Script/Doc (Host Repo)**
    *   **Description**: Create a small helper script or detailed documentation in the host repo describing the workflow for bumping enclave versions, cutting new tags, regenerating candidate registry entries, and updating the `measurement_registry.json` and submodule pointer.
    *   **Validation**: The script/documentation clearly outlines the process and enables a user to perform the versioning workflow successfully.
