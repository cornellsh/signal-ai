## ADDED Requirements

### Requirement: Host `enclave_integration.md` SHALL be updated to describe the two-repository model and audience.
The `enclave_integration.md` documentation in the host repository MUST be updated to clearly define the relationship between the public enclave and private host repositories.

#### Scenario: Clarifying repo distinction
The `docs/enclave_integration.md` file in the host repository SHALL be updated to clearly describe the distinction between the public `signal-assistant-enclave` repository and the private host repository.

#### Scenario: Explaining audience and use cases for each repo
The documentation SHALL explain the expected audience and use cases for each repository (e.g., auditors/integrators for the enclave, internal development for the host).

### Requirement: Host `enclave_integration.md` SHALL identify canonical sources for privacy and invariants.
This section MUST explicitly list the authoritative files in the host repository for privacy and invariant definitions.

#### Scenario: Identifying canonical files for privacy and invariants
The `docs/enclave_integration.md` file SHALL explain which files in the host repository are considered canonical for privacy and invariants, specifically mentioning `docs/signal_assistant_core.md`, `docs/privacy_architecture.md`, `invariant_manifest.py`, and `measurement_registry.json`.

### Requirement: Host `enclave_integration.md` SHALL clarify the attestation scope and host's role.
The documentation MUST clearly delineate which parts of the system are subject to public attestation and the host's responsibilities.

#### Scenario: Clarifying public attestable code
The `docs/enclave_integration.md` file SHALL clarify that the `signal-assistant-enclave` repository contains the only public code expected to be attestable.

#### Scenario: Host responsibility for enforcement
The documentation SHALL state that the host code is private and is responsible for enforcing the measurement registry and overall governance model.

### Requirement: Host `enclave_integration.md` SHALL include a "Trust Story" for third-party auditors.
A dedicated section MUST guide third-party auditors on how to verify the integrity and provenance of running enclave instances.

#### Scenario: Inclusion of a "trust story" section
The `docs/enclave_integration.md` file SHALL include a "trust story" section.

#### Scenario: Verification process for running enclave
This section SHALL describe how a third-party auditor can verify that a running enclave instance corresponds to a particular `signal-assistant-enclave` git tag and a specific `measurement_registry.json` entry.

#### Scenario: OpenSpec change process for invariant-affecting changes
The trust story SHALL clarify that changes to the enclave that affect invariants must undergo the OpenSpec change process in the host repository and be reflected in new public enclave tags and updated measurement registry entries.
