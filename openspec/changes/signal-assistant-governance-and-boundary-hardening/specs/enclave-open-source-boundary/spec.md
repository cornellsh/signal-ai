# Enclave Open Source Boundary

## ADDED Requirements

### Requirement: Module Dependency Boundary
- `src/signal_assistant/enclave/**` MUST NOT import:
    - `signal_assistant.host.*`
    - host storage / transport / proxy modules
    - test-only or mock-only modules
- Enclave code MAY depend on:
    - standard library
    - explicitly whitelisted third-party libs
    - `signal_assistant.enclave.*` internal modules
- CI MUST include a static check that enforces this boundary.

#### Scenario: Accidental host import
- **Given** a developer adds `from signal_assistant.host.storage import BlobStore` to an enclave module.
- **When** the static boundary check runs in CI.
- **Then** it identifies the forbidden import path.
- **And** the check fails.

### Requirement: Enclave Packaging
- The system SHALL define a Python package target for the enclave (e.g., `signal-assistant-enclave`).
- The package MUST be buildable from the existing repo (e.g., via `pyproject.toml` extras or a separate build config).
- The package MUST include `src/signal_assistant/enclave/**` and minimal shared serialization/exceptions types if needed.
- The package MUST exclude host implementation, governance scripts and registry, and LE host tooling.

#### Scenario: Enclave-only OSS package build
- **Given** the codebase is set up for packaging.
- **When** a build command for `signal-assistant-enclave` is executed (e.g., `pip install .[enclave]`).
- **Then** the package SHALL build successfully.
- **And** the resulting package SHALL contain only enclave-specific code and whitelisted dependencies.
- **And** it SHALL NOT contain any host-specific or governance-related files.

### Requirement: Documentation and Spec Exposure
- The public enclave package MUST ship or reference `docs/signal_assistant_core.md`, `docs/privacy_architecture.md`, and a subset of `openspec` deltas that define enclave behavior and privacy invariants.
- It MUST NOT expose internal operational governance docs intended only for host operators.

#### Scenario: Enclave documentation review
- **Given** the `signal-assistant-enclave` package is prepared for release.
- **When** a documentation review is conducted.
- **Then** it SHALL be confirmed that only relevant public documentation (core, privacy architecture, enclave-specific specs) is included or linked.
- **And** sensitive internal operational governance documents SHALL be explicitly excluded.

### Requirement: Tests for Boundary
- The system SHALL include tests / checks that verify:
    - Building the enclave package succeeds without any host/governance modules.
    - A minimal “enclave-only” test harness can decrypt a mocked Signal message, run through the LLMPipeline with sanitized prompts, and produce a response, without importing host or governance code.

#### Scenario: Enclave-only test harness execution
- **Given** the `signal-assistant-enclave` package is built and installed.
- **When** a test suite designed for the enclave-only test harness is executed.
- **Then** the tests SHALL run successfully.
- **And** these tests SHALL verify core enclave functionality (decryption, LLM processing) without relying on or importing any host-specific components.
