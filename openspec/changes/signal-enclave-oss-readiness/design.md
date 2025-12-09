# Design Document: Signal Assistant Enclave OSS Readiness

## 1. Introduction
This design document outlines the architectural considerations and rationale behind preparing the `signal-assistant-enclave` repository for open-source consumption. The primary goal is to provide a clear, understandable, and verifiable open-source artifact that integrates seamlessly with the private host repository while maintaining strict governance and security invariants.

## 2. Architectural Context
The project employs a critical two-repository model:
- **Host Repository (Private)**: Orchestrates the overall Signal Assistant functionality, handles Signal integration, key management service (KMS) interactions, host-side data persistence (encrypted), and operational governance. It is the primary locus of control and defines the authoritative invariant manifest and measurement registry.
- **Enclave Repository (Public, `signal-assistant-enclave`)**: Contains the core privacy-preserving logic, the Signal protocol implementation within the TEE, prompt sanitization, law enforcement policy enforcement, and attestation mechanisms. This repository is designed to be independently auditable and verifiable. It is consumed by the host repository as a git submodule (`enclave_package/`).

The design prioritizes maintaining a clear separation of concerns and trust boundaries between these two components. The host is considered untrusted and relies entirely on the attestation and cryptographic guarantees provided by the enclave.

## 3. Design Principles for OSS Readiness

### 3.1. Enclave Self-Containment and Clarity
The public enclave repository must be comprehensible on its own. This implies:
- **Comprehensive Top-Level Documentation**: `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `LICENSE` files must explain the enclave's purpose, security model, contribution guidelines, and licensing terms *without* requiring knowledge of the private host component. Cross-references to canonical host documentation will be provided where appropriate, but the enclave's fundamental role must be clear from its own `README`.
- **Minimal Dependencies**: The `pyproject.toml` (or equivalent) in the enclave repo should declare only necessary dependencies for its operation and testing.
- **Independent Testability**: Enclave-specific tests must be runnable entirely within the enclave repository, independent of the host.

### 3.2. Verifiable Build and Test Process
External auditors and contributors must be able to verify the integrity and correctness of the enclave code.
- **GitHub Actions CI**: A dedicated CI pipeline within the `signal-assistant-enclave` GitHub repository will execute `poetry install`, `pytest` (for enclave-only tests), and static analysis tools (e.g., `ruff`, `mypy`) on every pull request and push to `main`. This ensures continuous validation of code quality and functional correctness.
- **Explicit Failure Conditions**: The CI must fail on any test failure, linting violation, or type-checking error, establishing clear quality gates.
- **Separation from Host CI**: The host repo's CI should *not* duplicate the enclave's CI. Instead, the host CI will treat the enclave submodule as a dependency, potentially verifying its existence and version, but relying on the enclave's own CI for internal quality.

### 3.3. Versioning and Registry Alignment
A robust versioning scheme is crucial for traceability and trust.
- **Semantic Versioning (SemVer)**: The enclave repository will adhere to SemVer (e.g., `vX.Y.Z`) for its releases, managed via git tags. This provides a clear, machine-readable indication of changes and API compatibility.
- **Canonical Source for Measurements**: The host repository's `measurement_registry.json` is the authoritative source for attested enclave measurements. Each entry in this registry *must* correspond to a specific, immutable git tag in the public `signal-assistant-enclave` repository. This establishes a direct, auditable link between a deployed enclave's measurement and its exact source code version.
- **Documentation of Mapping**: The relationship between enclave git tags/versions and `measurement_registry.json` entries will be thoroughly documented in both host (e.g., `docs/enclave_integration.md`, `docs/release_process.md`) and enclave `README.md` (via cross-reference).
- **Host-Side Verification**: The host CI will include a check to ensure that all active entries in `measurement_registry.json` indeed point to existing and valid git tags in the `signal-assistant-enclave` submodule. This prevents the host from deploying against an unverified or non-existent enclave version.
- **Helper Tooling**: A utility script or documented workflow in the host repo will facilitate the process of bumping enclave versions, creating git tags, and updating the `measurement_registry.json` and submodule pointer, streamlining the release process.

### 3.4. Cross-Repository Documentation and Trust Story
Clarity on the interaction and trust model between the host and enclave is paramount for auditors.
- **Updated Host Integration Docs**: `docs/enclave_integration.md` in the host repo will be revised to:
    - Explicitly differentiate the roles of the public enclave repo and the private host repo.
    - Guide third-party auditors on how to use the public enclave repo.
    - Highlight canonical documents in the host repo (`signal_assistant_core.md`, `privacy_architecture.md`, `invariant_manifest.py`, `measurement_registry.json`) as the sources of truth for invariants and governance.
    - Clarify that only the enclave code is publicly attestable, while the host enforces the registry and governance.
- **"Trust Story" Section**: A dedicated section will describe the process for a third-party auditor to verify that a running enclave instance corresponds to a specific enclave git tag and `measurement_registry.json` entry. This will detail the attestation process and how to link observed measurements to source code.
- **OpenSpec as Governance**: The documentation will reiterate that significant changes affecting privacy invariants within the enclave *must* originate as OpenSpec changes in the host repo, subsequently leading to new attested enclave versions and registry updates.

## 4. Open Questions / Future Considerations
- Granularity of static analysis in enclave CI: Can existing PII-related checks be easily scoped to the enclave, or do new, enclave-specific checks need to be developed?
- Integration of `poetry` into GitHub Actions: Ensure efficient caching and dependency management.
- Detailed design of the versioning helper script: What level of automation is desired for updating submodules and registry entries?
