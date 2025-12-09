# Policy Drift and Release Pipeline

## ADDED Requirements

### Requirement: Invariant Manifest
- The system SHALL define a machine-readable “invariant manifest” tied to key privacy invariants, logging schema constraints, LE control path constraints, and key-gating invariants.
- This manifest MUST be versioned and referenced by OpenSpec change sets.

#### Scenario: Invariant manifest updates
- **Given** a change to privacy requirements for the system.
- **When** new invariants are defined or existing ones are modified.
- **Then** the `InvariantManifest` SHALL be updated to reflect these changes.
- **And** the manifest MUST be versioned.
- **And** any relevant OpenSpec change set SHALL reference this updated manifest.

### Requirement: Policy Drift Detection
- `tools/policy_drift_check.py` MUST:
    - Compare the invariant manifest between the last active registry entry’s git_commit and the candidate commit.
    - Detect:
        - removal or weakening of invariants,
        - relaxation of logging constraints,
        - expansion of LE responses,
        - weakening of key-gating/attestation conditions.
    - Require an explicit OpenSpec change set reference to justify any change. If a behavior change is not backed by an approved spec delta, the check MUST fail.

#### Scenario: Silent weakening of LE control policy
- **Given** a change to `handle_le_request` that adds a new permissible response type.
- **When** the `policy_drift_check.py` runs during the release process.
- **Then** it detects the expanded response set in the invariant manifest.
- **And** it fails the check because no corresponding OpenSpec delta ID was provided/verified.

### Requirement: CI Integration
- The main release pipeline MUST:
    - Run `openspec validate --strict` for all change sets.
    - Run `policy_drift_check` comparing HEAD against the last active registry entry.
    - Run `ci/verify_release_build.py` for the PROD profile.
- If any of these fail, the pipeline MUST NOT produce or publish a release artifact.

#### Scenario: Release pipeline failure
- **Given** a new code change is introduced.
- **When** the main release pipeline runs.
- **And** `policy_drift_check` detects a weakening of an invariant without a corresponding OpenSpec delta.
- **Then** the pipeline SHALL fail.
- **And** no release artifact SHALL be produced or published.
