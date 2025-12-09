# Enclave Integration Documentation

## 1. Two-Repo Model and Rationale

The `signal-assistant` project employs a two-repository model to manage its core components:

*   **`signal-assistant-enclave` (Public Repository):** This repository contains the sensitive, privacy-preserving core logic of the Signal Assistant. It is maintained as an open-source project to ensure transparency, community scrutiny, and auditable security. All changes to the core enclave implementation *must* originate from this public repository.
*   **`signal-ai` (Private Repository):** This repository contains the host application code, governance tooling, the `measurement_registry.json` file, attestation and enforcement logic, and the OpenSpec change management system. It consumes the `signal-assistant-enclave` as a Git submodule.

**Rationale for this model:**

*   **Enforce Open-Source Boundary:** Ensures the enclave remains transparent and prevents "hidden forks" or divergent code within the private host. All security-critical code changes are public.
*   **Reproducible Enclave Builds:** Guarantees that the enclave used by `signal-ai` is built from a stable, versioned, and auditable commit from the public repository, enhancing trust and verification.
*   **Avoid Local Edits:** Prevents unmanaged modifications to enclave code within `signal-ai`. All enclave code changes are funneled through a controlled public process.
*   **Clear API Contract:** Establishes a minimal, well-defined public API for the enclave, restricting host access to internal implementation details and enhancing modularity and security.

## 2. Workflow for Proposing/Implementing Changes in `signal-assistant-enclave`

All development for the `signal-assistant-enclave` core functionality occurs in its dedicated public repository.

1.  **Propose Change:** Submit a detailed proposal (e.g., design document, issue) to the `signal-assistant-enclave` public repository, outlining the change, its rationale, and any security implications.
2.  **Develop & Test:** Implement the change within a feature branch in the `signal-assistant-enclave` repository. Ensure comprehensive unit and integration tests are written and pass.
3.  **Code Review:** Submit a Pull Request (PR) for review by maintainers and the community. This review process focuses heavily on security, correctness, and adherence to design principles.
4.  **Merge:** Once approved, the changes are merged into the `main` branch of the `signal-assistant-enclave` repository.
5.  **Release & Tag:** For production-ready changes, create a new semantic version tag (e.g., `v1.0.0`) on the `main` branch. This tag signifies a stable release point.

## 3. Process for Updating `signal-ai` Host to a New Enclave Version

When a new version of `signal-assistant-enclave` is released (i.e., tagged in its public repository), the `signal-ai` host needs to be updated to consume it.

1.  **Update Submodule:**
    *   Navigate to the `signal-ai` repository.
    *   Update the `enclave_package` submodule to the desired new commit (usually the commit corresponding to the latest tag):
        ```bash
        git submodule update --remote enclave_package
        # Or, to pin to a specific commit/tag:
        cd enclave_package
        git checkout <new_enclave_commit_sha_or_tag>
        cd ..
        git add enclave_package
        ```
    *   Verify that the submodule is pointing to the correct commit:
        ```bash
        git submodule status enclave_package
        ```

2.  **Update `measurement_registry.json`:**
    *   Edit the `measurement_registry.json` file in the `signal-ai` repository.
    *   Locate the entry for `signal-assistant-enclave`. If one doesn't exist, create it following existing patterns.
    *   Update the `git_commit` field to the exact SHA of the commit the `enclave_package` submodule is currently pinned to.
    *   Update the `version` field to the semantic version string (e.g., "1.0.0") corresponding to the tag.
    *   Example `measurement_registry.json` entry:
        ```json
        {
            "name": "signal-assistant-enclave",
            "mrenclave": "sha256:...",
            "version": "1.2.3",
            "git_commit": "abcdef1234567890abcdef1234567890abcdef12",
            "build_timestamp": "2025-01-01T12:00:00Z",
            "profile": "PROD",
            "status": "active",
            "revocation_reason": null
        }
        ```

3.  **Run CI/CD Checks:**
    *   Commit both the updated `enclave_package` submodule reference and the `measurement_registry.json` changes.
    *   Push the changes to a new branch and open a Pull Request in the `signal-ai` repository.
    *   The CI/CD pipeline will automatically run checks, including:
        *   **Dirty Submodule Check:** Ensures `enclave_package` is clean and properly pinned.
        *   **Forbidden Imports Check:** Prevents host code from importing internal enclave modules.
        *   **Registry Consistency Check:** Verifies that `measurement_registry.json` matches the submodule's pinned commit and version tag.
        *   **OpenSpec Validation:** Ensures compliance with current OpenSpecs.
        *   **Policy Drift Check:** Verifies other governance invariants.
    *   All CI checks must pass before the PR can be merged.

4.  **Deploy:** Once the PR is merged and all checks pass, the `signal-ai` host can be safely deployed with the new enclave version.

## 4. Trust and Attestation Story

The integration of `signal-assistant-enclave` as a submodule, combined with rigorous CI/CD checks and `measurement_registry.json` management, forms the foundation of our trust and attestation story:

*   **Transparency and Auditability:** The enclave's open-source nature and public change workflow ensure that its entire history and implementation are transparent and auditable.
*   **Immutable References:** By pinning the `enclave_package` submodule to specific, cryptographically signed (via git commits) versions and recording these in `measurement_registry.json`, we create an immutable record of the exact enclave code used in any given `signal-ai` build.
*   **Build-Time Enforcement:** The CI checks actively enforce the intended separation of concerns and versioning invariants at build time, preventing misconfigurations or unauthorized modifications from reaching production.
*   **Measurement and Attestation (Future/External):** The `mrenclave` field in `measurement_registry.json` represents the cryptographic measurement of the enclave. In a full Trusted Execution Environment (TEE) setup (e.g., Intel SGX, AMD SEV), this `mrenclave` would be generated by the TEE's measurement process and used for remote attestation. This allows external parties to verify that the correct and expected enclave code is running in a secure environment. The `git_commit` and `version` provide human-readable and verifiable links back to the exact source code that produced that `mrenclave`.
*   **Policy Enforcement:** The `invariant_manifest` (and other checks like Policy Drift) ensures that the entire system, including the host and enclave, adheres to predefined security and privacy policies.

This layered approach ensures a high degree of assurance regarding the integrity and provenance of the `signal-assistant-enclave` within the broader `signal-ai` system.
