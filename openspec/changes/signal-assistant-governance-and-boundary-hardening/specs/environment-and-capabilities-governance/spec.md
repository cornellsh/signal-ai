# Environment and Capabilities Governance

## ADDED Requirements

### Requirement: Environment Model
- The system SHALL replace “implicit DEV” with an explicit environment model, including build-time profiles (`DEV`, `TEST`, `STAGE`, `PROD`) and a runtime environment derived from signed config or immutable build metadata.
- For released artifacts, the default environment MUST be `PROD`. Non-PROD MUST only be reachable in test binaries, dev builds, or explicit “dev mode” artifacts not used in production.

#### Scenario: Implicit DEV forbidden
- **Given** a production release artifact.
- **When** it is deployed without explicit environment configuration.
- **Then** it defaults to `PROD` behavior (secure, no debug).
- **And** it refuses to run if any "dev-only" flags are present in the environment variables.

### Requirement: Dangerous Capabilities Manifest
- The system SHALL introduce a single `DangerousCapabilities` manifest (code-level or config-level), listing capabilities such as `MOCK_ATTESTATION`, `EXTENDED_DEBUG_LOGGING`, `LE_SIMULATION`, and `ANY_CONTENT_LOGGING`.
- All dangerous behaviors MUST be behind explicit checks against this manifest. Direct ad-hoc use of env vars or `if debug:` branches for privacy-relevant behavior is forbidden.

#### Scenario: New dangerous capability added
- **Given** a new capability `UNSAFE_FEATURE_X` that could compromise privacy is introduced.
- **When** a developer implements `UNSAFE_FEATURE_X`.
- **Then** `UNSAFE_FEATURE_X` SHALL be added to the `DangerousCapabilities` manifest.
- **And** its usage SHALL be gated by checks against this manifest.
- **And** policy documents and tests SHALL be updated accordingly.

### Requirement: CI and Runtime Enforcement
- CI MUST:
    - For PROD builds, assert that `DangerousCapabilities` is empty/disabled.
    - Refuse to build or sign a PROD artifact if any dangerous capability is enabled.
- Runtime MUST:
    - On startup in PROD, panic/fail closed if any dangerous capability is enabled, regardless of how it was toggled.
    - Log a clear, non-PII “misconfiguration” error via secure logging.

#### Scenario: PROD build with MOCK_ATTESTATION
- **Given** a developer attempts to enable `MOCK_ATTESTATION` in the `DangerousCapabilities` manifest.
- **When** they trigger a build with `--profile PROD`.
- **Then** the CI verification script detects the forbidden capability.
- **And** the build fails.
