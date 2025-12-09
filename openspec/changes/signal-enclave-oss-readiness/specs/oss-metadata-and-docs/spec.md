## ADDED Requirements

### Requirement: README.md in the Enclave Repository SHALL clearly describe the project, its scope, architecture, and local development.
The top-level `README.md` in the `signal-assistant-enclave` repository MUST provide essential information for understanding and interacting with the enclave package.

#### Scenario: README.md presence and scope description
The `signal-assistant-enclave` repository (located at `enclave_package/` as a submodule) SHALL contain a `README.md` at its top-level.
The `README.md` SHALL clearly state the scope of the enclave package, specifying what it includes (enclave code, privacy core, tests) and what it does not include (host-side Signal integration, proprietary operational stack).

#### Scenario: README.md privacy architecture summary and links
The `README.md` SHALL summarize the privacy architecture and include links to the canonical privacy documentation in the host repository (`docs/signal_assistant_core.md` and `docs/privacy_architecture.md`).

#### Scenario: README.md TEE-agnostic model explanation
The `README.md` SHALL describe the TEE-agnostic model, explaining the use of simulated enclaves versus real hardware TEEs and defining the in-scope and out-of-scope aspects related to TEE implementation.

#### Scenario: README.md local test instructions
The `README.md` SHALL provide instructions on how to run enclave-only tests locally using `poetry` and `pytest`.

#### Scenario: README.md local dev harness instructions (if applicable)
The `README.md` SHALL (if applicable) provide instructions on how to run the enclave within a small development harness.

### Requirement: SECURITY.md in the Enclave Repository SHALL define the threat model and reporting process for security issues.
The `SECURITY.md` file MUST define the security posture and incident response for the enclave repository.

#### Scenario: SECURITY.md presence and threat model description
The `signal-assistant-enclave` repository SHALL contain a `SECURITY.md` at its top-level.
The `SECURITY.md` SHALL provide a high-level description of the threat model relevant to the enclave.

#### Scenario: SECURITY.md security issue reporting
The `SECURITY.md` SHALL clearly state the process for reporting security issues.

#### Scenario: SECURITY.md security-sensitive code clarification
The `SECURITY.md` SHALL clarify that the enclave repository contains security-sensitive code and that changes must preserve defined invariants.

### Requirement: CONTRIBUTING.md in the Enclave Repository SHALL outline the contribution process and reference OpenSpec.
The `CONTRIBUTING.md` file MUST guide external contributors on how to engage with the `signal-assistant-enclave` project.

#### Scenario: CONTRIBUTING.md presence and process definition
The `signal-assistant-enclave` repository SHALL contain a `CONTRIBUTING.md` at its top-level.
The `CONTRIBUTING.md` SHALL define the contribution process, including requirements for tests, style expectations, and guidelines for proposing changes that may affect privacy-related behavior.

#### Scenario: CONTRIBUTING.md OpenSpec reference
The `CONTRIBUTING.md` SHALL reference the OpenSpec-driven process used in the host repository for major architectural changes, even if external contributors cannot fully execute it.

### Requirement: LICENSE file in the Enclave Repository SHALL specify an OSI-approved license and clarify scope.
The `LICENSE` file MUST establish the legal terms under which the `signal-assistant-enclave` software is distributed.

#### Scenario: LICENSE file presence and OSI approval
The `signal-assistant-enclave` repository SHALL contain a `LICENSE` file at its top-level.
The `LICENSE` file SHALL specify an appropriate Open Source Initiative (OSI) approved license for the enclave component.

#### Scenario: LICENSE file host repo scope clarification
The `LICENSE` file SHALL include a clear note indicating that the host repository and any commercial deployment are outside the scope of this license.
