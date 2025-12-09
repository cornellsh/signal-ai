## ADDED Requirements

### Requirement: GitHub Actions CI for the Enclave Repository SHALL be implemented and run on PRs and main.
GitHub Actions CI workflows MUST be implemented for the `signal-assistant-enclave` repository to ensure code quality and correctness.

#### Scenario: CI workflow implementation
The `signal-assistant-enclave` repository SHALL implement GitHub Actions CI workflows.

#### Scenario: CI trigger conditions
The CI workflows SHALL run on every Pull Request and every push to the `main` branch.

#### Scenario: Dependency management in CI
The CI workflows SHALL execute `poetry install` to manage dependencies.

#### Scenario: Enclave test execution in CI
The CI workflows SHALL run `pytest` for all tests located under `enclave_package/tests/` (or the equivalent test suite within the `signal-assistant-enclave` repository).

#### Scenario: Static analysis in CI
The CI workflows SHALL perform static analysis (e.g., using `ruff`, `mypy`, or existing PII/logging-related checks scoped to enclave code).

### Requirement: The Enclave CI SHALL have explicit failure conditions for tests, type-checking, and linting.
The CI MUST be configured to fail if any quality gates are not met, preventing the merge of problematic code.

#### Scenario: Test failure in CI
The GitHub Actions CI for the `signal-assistant-enclave` repository SHALL fail if any `pytest` tests fail.

#### Scenario: Type-checking failure in CI
The CI SHALL fail if the code does not pass type-checking (e.g., `mypy`).

#### Scenario: Linting failure in CI
The CI SHALL fail if the code does not pass linting (e.g., `ruff`).

### Requirement: The Enclave CI MAY optionally provide a summary of invariant/manifest or registry state.
To aid in transparency and auditing, the Enclave CI SHALL be capable of optionally generating and displaying summaries of critical security-related states.

#### Scenario: Invariant/manifest summary output
The GitHub Actions CI for the `signal-assistant-enclave` repository MAY optionally compute and print a summary of the invariant/manifest or registry state if a mirrored local representation exists within the enclave repository.

### Requirement: The Enclave CI SHALL be logically separated from the Host CI.
The CI process for the enclave repository MUST operate independently from the host repository's CI.

#### Scenario: Enclave CI independence
The CI for the `signal-assistant-enclave` repository SHALL be logically separate and independent from the host repository’s CI.

#### Scenario: Host CI treatment of enclave
The host repository’s CI SHALL treat the enclave as a submodule dependency with its own independent CI status, rather than duplicating enclave-specific CI checks.