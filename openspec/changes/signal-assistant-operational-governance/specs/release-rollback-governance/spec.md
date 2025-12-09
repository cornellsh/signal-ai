# Release, Rollback & Policy Drift Governance Specification

## 1. Introduction
This specification defines the normative requirements for **Release, Rollback, and Policy Drift**. It governs how the Enclave evolves over time, ensuring that new versions do not silently weaken privacy guarantees and that known-bad versions cannot be reintroduced.

## ADDED Requirements

### Release Criteria

### Requirement: Production Release Gating
*   **Description:** A new Enclave build MUST NOT be released to Production unless it passes all spec-enforcement tests and its measurement is active in the Registry.
*   **Ref:** core-9.4.1

#### Scenario: Blocked Unregistered Release
*   **Given** a new Enclave build `V_NEW` that passes all tests.
*   **But** its measurement `M_NEW` has NOT been added to `measurement_registry.json`.
*   **When** the CD pipeline attempts to promote it to Production.
*   **Then** the promotion step MUST fail.

### Requirement: Immutable Commit Linkage
*   **Description:** The Registry entry MUST link the measurement to a specific, immutable Git commit.
*   **Ref:** core-9.4.1

#### Scenario: Traceability Check
*   **Given** a registry entry for version `1.2.0`.
*   **When** an auditor checks the `git_commit` field.
*   **Then** that commit SHA MUST exist in the upstream repository.

### Policy Drift Detection

### Requirement: Automated Drift Detection
*   **Description:** The release process MUST automatically detect "weakened" privacy policies (e.g., fewer PII regexes).
*   **Ref:** privacy-9.3

#### Scenario: Silent Weakening Detection
*   **Given** a PR that removes the "Email Address" regex from the PII sanitizer.
*   **When** the CI runs the Policy Drift check.
*   **Then** it detects that `sanitizer_rules` count decreased.
*   **And** it fails the build or blocks the release until a "Privacy Impact Statement" is attached.

### Requirement: Explicit Weakening Approval
*   **Description:** Policy weakening changes MUST require explicit "Privacy Exception" approval.
*   **Ref:** privacy-9.3

#### Scenario: Privacy Exception Approval
*   **Given** a detected policy weakening (e.g., removing a restricted log field).
*   **When** the developer adds a `privacy-exception: approved` label (or equivalent).
*   **Then** the Policy Drift check passes.

### Rollback Governance

### Requirement: Active Version Rollback Only
*   **Description:** The system MUST allow rollback to a previous version ONLY IF it is still marked `active` in the Registry.
*   **Ref:** core-9.4.3

#### Scenario: Valid Rollback
*   **Given** current version `V2` is unstable.
*   **And** previous version `V1` is `active` in the registry.
*   **When** an operator initiates a rollback to `V1`.
*   **Then** the operation succeeds.

### Requirement: Revoked Version Rollback Ban
*   **Description:** The system MUST strictly forbid rollback to `revoked` versions.
*   **Ref:** core-9.4.3

#### Scenario: Blocked Revoked Rollback
*   **Given** current version `V2` is crashing.
*   **And** previous version `V1` is `revoked` in the registry due to a security flaw.
*   **When** an operator attempts to deploy `V1`.
*   **Then** the Gatekeeper (Host) denies the deployment because `V1.status == revoked`.

### Data Migration & Key Rotation

### Requirement: Seal Key Migration Testing
*   **Description:** Data migration paths for Sealed Data MUST be tested if the Seal Key derivation changes.
*   **Ref:** core-9.1.2

#### Scenario: Incompatible Upgrade Prevention
*   **Given** a new version `V2` that changes the sealing key context.
*   **When** `V2` attempts to unseal data written by `V1` without a migration handler.
*   **Then** the unseal operation fails, and `V2` MUST enter a safe failure state (not corrupting data).

### Requirement: Minimum Compatible Version
*   **Description:** The Registry MUST support declaring "Min Compatible Version".
*   **Ref:** core-9.1.2

#### Scenario: Min Version Enforcement
*   **Given** a registry entry for `V3` declaring `min_compatible: V2`.
*   **When** an operator attempts to upgrade directly from `V1` to `V3`.
*   **Then** the deployment tool SHOULD warn or block, advising an intermediate upgrade to `V2`.

## 3. Relationship to Core Specs
This spec operationalizes:
-   `privacy-9.2` (Prospective Wiretapping - requiring code changes and new attestation)
-   `privacy-9.3` (Public Detectability of Attestation)
