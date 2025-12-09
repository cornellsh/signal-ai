# Environment & Configuration Governance Specification

## 1. Introduction
This specification defines the normative requirements for **Environment & Configuration Governance**. It ensures that the Enclave's behavior matches its operational context and that dangerous configurations (e.g., test mocks) are structurally impossible in production.

## 2. Environment Taxonomy
The system recognizes the following environments:
1.  **LOCAL:** Developer workstations.
2.  **CI:** Automated testing pipelines.
3.  **TEST:** Shared test cluster (synthetic data).
4.  **STAGE:** Pre-production (mirror of Prod, redacted/synthetic data).
5.  **PROD:** Live production (real user data).

## ADDED Requirements

### Build Profiles & Compilation

### Requirement: Build Profile Support
*   **Description:** The build system MUST support distinct profiles: `DEV` and `PROD`, where `PROD` physically excludes unsafe code paths.
*   **Ref:** core-10.7

#### Scenario: Compile-Time Exclusion
*   **Given** the build system configured for profile `PROD`.
*   **When** the compiler processes the source code.
*   **Then** code blocks wrapped in `#ifndef PRODUCTION` (or equivalent) MUST NOT be included in the binary.

### Requirement: Mock Logic Exclusion
*   **Description:** `MOCK_ATTESTATION` logic MUST be wrapped in conditional compilation blocks ensuring it is **only** present in `DEV` builds.
*   **Ref:** core-10.7

#### Scenario: Mock Logic Absence
*   **Given** a `PROD` binary.
*   **When** a strings/symbol analysis is performed.
*   **Then** symbols related to `MockAttestationService` MUST NOT be present.

### Runtime Configuration Rules

### Requirement: Production Configuration Validation
*   **Description:** The Enclave MUST panic at startup if `MOCK_ATTESTATION` is enabled in a `PROD` environment.
*   **Ref:** core-10.7

#### Scenario: Production Safety Check
*   **Given** a `PROD` build of the Enclave.
*   **When** it is launched with `MOCK_ATTESTATION_FOR_TESTS_ONLY=1`.
*   **Then** the Enclave startup routine MUST fail with a fatal error: "Illegal configuration: Mock attestation not allowed in Production build."

### Requirement: Production Log Level
*   **Description:** Debug logging MUST be disabled in `PROD` builds.
*   **Ref:** core-11.5

#### Scenario: Log Level Enforcement
*   **Given** a `PROD` build of the Enclave.
*   **When** the configuration attempts to set `LOG_LEVEL=DEBUG`.
*   **Then** the Enclave MUST ignore this setting and default to `INFO` or `WARN`.

### CI/CD Enforcement

### Requirement: Unsafe Default Detection
*   **Description:** The CI pipeline MUST fail if a PR attempts to merge code that enables `MOCK_ATTESTATION` by default.
*   **Ref:** core-10.7

#### Scenario: Unsafe Default Configuration
*   **Given** a Pull Request that changes the default `config.py` to set `MOCK_ATTESTATION = True`.
*   **When** the CI validation runs.
*   **Then** it MUST detect this unsafe default and fail the build.

### Requirement: Deployment Profile Verification
*   **Description:** Deployment scripts for `PROD` MUST verify the artifact profile.
*   **Ref:** core-10.7

#### Scenario: Deploying Dev Build to Prod
*   **Given** a deployment request to the `PROD` environment.
*   **When** the artifact metadata indicates it was built with profile `DEV`.
*   **Then** the deployment script MUST abort immediately.

### Feature Flags & Toggles

### Requirement: Dangerous Toggle Protection
*   **Description:** Dangerous toggles (e.g., PII bypass) MUST be treated as `DEV`-only features.
*   **Ref:** core-10.7

#### Scenario: PII Bypass Attempt in Prod
*   **Given** a `PROD` build.
*   **When** a configuration flag `DISABLE_PII_SANITIZATION=true` is provided.
*   **Then** the Enclave MUST either refuse to start or ignore the flag and log a critical warning.

## 4. Relationship to Core Specs
This spec operationalizes:
-   `core-10.7` (Attestation Integrity)
-   `core-11.5` (Logging Schema Constraints)
