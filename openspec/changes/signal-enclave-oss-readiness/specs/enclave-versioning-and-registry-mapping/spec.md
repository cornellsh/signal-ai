## ADDED Requirements

### Requirement: The Enclave Package SHALL have a clearly defined versioning scheme.
A consistent and transparent versioning scheme MUST be established for tracking changes and releases of the enclave package.

#### Scenario: Versioning scheme definition
The `signal-assistant-enclave` repository SHALL establish a versioning scheme for the enclave package.

#### Scenario: Semantic Versioning adoption
The versioning scheme SHALL follow Semantic Versioning (SemVer).

#### Scenario: Version definition in `pyproject.toml`
The version SHALL be explicitly defined in the `pyproject.toml` file of the enclave package.

#### Scenario: Git tag format for versions
Git tags in the `signal-assistant-enclave` repository SHALL correspond to the versions, using a `vX.Y.Z` format.

### Requirement: There SHALL be a defined mapping between Enclave versions and Host `measurement_registry.json` entries.
This mapping MUST ensure traceability between deployed enclave versions and their corresponding measurements in the host system.

#### Scenario: Defined mapping for git tags and registry entries
There SHALL be a defined mapping between:
- Git tags and versions in the `signal-assistant-enclave` repository, and
- Entries in the `measurement_registry.json` file within the host repository (specifically, the `git_commit` and `version` fields of each measurement).

### Requirement: All `measurement_registry.json` entries SHALL reference existing Enclave tags.
To maintain integrity and auditability, all active measurement entries MUST point to verifiable enclave source code versions.

#### Scenario: Validation of `measurement_registry.json` entries
Every "active" measurement entry in the host repository's `measurement_registry.json` SHALL reference a `git_commit` and `version` that correspond to an existing and valid git tag and version in the `signal-assistant-enclave` repository.

### Requirement: Host documentation SHALL describe the Enclave version mapping for auditors.
Clear documentation MUST be provided for third-party auditors to verify the integrity and provenance of enclave deployments.

#### Scenario: Explicit description in host documentation
The documentation in the host repository, specifically `docs/enclave_integration.md` and `docs/release_process.md`, SHALL explicitly describe the mapping between `measurement_registry.json` entries and enclave tags/versions.

#### Scenario: Auditor traceability from registry to source
This documentation SHALL enable auditors to trace from a `measurement_registry.json` entry to the corresponding enclave git tag and its source code.

### Requirement: The Host repository SHALL provide tooling/documentation for managing Enclave versions.
To facilitate efficient and error-free version management, dedicated tools or comprehensive documentation MUST be provided.

#### Scenario: Provision of helper for versioning workflow
The host repository SHALL provide a helper script or detailed documentation describing the workflow for:
- Bumping the enclave version.
- Cutting a new enclave git tag.
- Regenerating a candidate entry for `measurement_registry.json`.
- Committing the updated `measurement_registry.json` and the corresponding submodule pointer.
