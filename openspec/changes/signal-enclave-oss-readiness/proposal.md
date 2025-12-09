# Proposal: Signal Assistant Enclave OSS Readiness

## Why
This proposal addresses the need to make the `signal-assistant-enclave` repository (synced as a git submodule under `enclave_package/`) an "OSS-ready" artifact. Currently, while technically correct, it lacks the packaging, documentation, and governance required for external auditors and integrators to easily understand and consume it as an open-source enclave package.

The project operates on a two-repo model:
- **Private/commercial host repo (this repo)**: Contains Signal integration, host orchestration, registry, and operational governance.
- **Public enclave repo (signal-assistant-enclave)**: Contains the enclave code, privacy core, and tests, intended as the open-source artifact.

## Goals
- **Self-contained & Consumable Enclave**: Transform the `signal-assistant-enclave` repo into a self-contained, understandable, and consumable open-source enclave package.
- **Documentation & Version Alignment**: Align public-facing documentation and versioning within the enclave repo with the invariant manifest, measurement registry, and attestation/governance story established in the host repo.
- **Minimal OSS Posture**: Implement a sensible open-source posture including a clear `README`, `LICENSE`, `CONTRIBUTING` guide, and CI for enclave-only tests, along with a clear release/versioning policy.
- **Consistent Host References**: Ensure the host repo’s integration documentation and `measurement_registry.json` consistently reference the public enclave repo and its version tags.

## Non-goals
- No new features or behavior changes to the enclave or host beyond what is strictly necessary for OSS readiness and governance.
- No modifications to the existing privacy invariants or law-enforcement policies.
- No alterations to the fundamental two-repo split, boundary definitions, or the submodule wiring mechanism.

## Proposed Spec Areas
1.  **OSS Metadata & Top-Level Docs (enclave repo)**: Define requirements for a comprehensive `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `LICENSE` within the `signal-assistant-enclave` repo.
2.  **Enclave Repo CI & Quality Gates**: Specify GitHub Actions CI for the `signal-assistant-enclave` repo to enforce code quality, run tests, and perform static analysis on PRs and `main`.
3.  **Versioning & Registry / Tag Mapping**: Establish a clear versioning scheme for the enclave package and define the mapping between enclave git tags/versions and entries in the host repo's `measurement_registry.json`.
4.  **Cross-Repo Documentation & Boundary Clarification**: Update host repo documentation (`docs/enclave_integration.md`) to clearly describe the two-repo model, the role of each repository, and the "trust story" for third-party auditors.