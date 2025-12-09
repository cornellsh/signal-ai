# Attestation & Measurement Registry Specification

## 1. Introduction
This specification defines the normative requirements for the **Attestation & Measurement Registry**. This registry serves as the authoritative allowlist for Enclave code. It binds specific, verifiable cryptographic measurements (`MRENCLAVE`) to human-readable versions and operational statuses.

## 2. Terminology
-   **Measurement (MRENCLAVE):** A cryptographic hash representing the initial state (code + data) of the Enclave memory. Uniquely identifies a build.
-   **Registry:** A verifiable data structure listing authorized Measurements.
-   **Status:** The operational state of a measurement (`active`, `deprecated`, `revoked`).

## ADDED Requirements

### Registry Structure

### Requirement: Canonical Registry File
*   **Description:** The project MUST maintain a canonical `measurement_registry.json` (or equivalent) file under version control.
*   **Ref:** core-9.4.1

#### Scenario: Registry Existence
*   **Given** a clean checkout of the repository.
*   **When** a developer lists files in the expected config directory.
*   **Then** `measurement_registry.json` MUST be present.

### Requirement: Strict Registry Schema
*   **Description:** The registry MUST adhere to a strict schema containing `mrenclave`, `version`, `git_commit`, `profile` (e.g. `PROD`), and `status` (`active`, `deprecated`, `revoked`).
*   **Ref:** core-9.4.1

#### Scenario: Schema Validation
*   **Given** a registry file with a missing `git_commit` field.
*   **When** the CI validation tool runs.
*   **Then** it MUST fail with a schema validation error.

### Requirement: Multi-Party Registry Changes
*   **Description:** Changes to the registry (adding/revoking) MUST require multi-party review or cryptographic signing (e.g., CODEOWNERS approval or PGP signatures).
*   **Ref:** core-9.4.3

#### Scenario: Unauthorized Change Attempt
*   **Given** a PR that modifies `measurement_registry.json`.
*   **When** the PR is submitted without a CODEOWNER approval.
*   **Then** the merge button MUST be disabled or the build MUST fail.

### Registration Process

### Requirement: Active Status Registration
*   **Description:** A maintainer MUST explicitly add a new build's `MRENCLAVE` to the registry with `status: active` before it can be deployed to Production.
*   **Ref:** core-9.4.1

#### Scenario: Releasing a New Build
*   **Given** a new Enclave binary built from commit `C`.
*   **When** the build pipeline completes successfully and outputs `MRENCLAVE`.
*   **Then** that measurement is NOT automatically trusted.
*   **And** a human maintainer MUST commit an update to `measurement_registry.json` adding it.

### Verification Logic

### Requirement: Host-Side Measurement Verification
*   **Description:** The Host MUST abort startup if the Enclave's measurement is not in the registry or is revoked.
*   **Ref:** core-9.4.3

#### Scenario: Enclave Startup with Invalid Measurement
*   **Given** an Enclave starting up in the `PROD` environment with measurement `M`.
*   **When** the Host Orchestrator prepares to provision keys.
*   **And** `M` is NOT in the registry OR `M.status` is `revoked`.
*   **Then** the Host MUST abort the startup and MUST NOT provision any keys.

### Requirement: Client-Side Measurement Verification
*   **Description:** Compliant clients MUST verify the Enclave's measurement against the public Registry.
*   **Ref:** privacy-9.3

#### Scenario: Client Verification of Attestation
*   **Given** a client connecting to the Assistant.
*   **When** the client verifies the Attestation Report and extracts measurement `M`.
*   **Then** the client MUST verify `M` exists in the public Registry with `status: active`.
*   **If** verification fails, the client MUST warn the user or terminate the connection.

### Revocation & Deprecation

### Requirement: Revocation Enforcement
*   **Description:** Revoked measurements MUST be permanently rejected by the Host/KMS.
*   **Ref:** core-9.4.3

#### Scenario: Key Provisioning with Revoked Build
*   **Given** a valid Enclave build `V1` that has been marked `revoked` in the registry.
*   **When** an operator attempts to start `V1`.
*   **Then** the KMS MUST refuse to unseal keys for it, citing the revocation status.

### Requirement: Deprecation Warning
*   **Description:** If an Enclave build marked `deprecated` is started, the Host MUST emit a warning log.
*   **Ref:** core-9.4.3

#### Scenario: Running Deprecated Version
*   **Given** an Enclave build `V1` marked `deprecated`.
*   **When** it starts up.
*   **Then** it SHOULD be allowed to run and receive keys.
*   **But** the Host logs MUST emit a warning about the deprecated status.

## 4. Relationship to Core Specs
This spec operationalizes:
-   `core-9.4.1` (Attested Measurements / Claims)
-   `core-9.4.3` (Attestation Gating Key Access)
