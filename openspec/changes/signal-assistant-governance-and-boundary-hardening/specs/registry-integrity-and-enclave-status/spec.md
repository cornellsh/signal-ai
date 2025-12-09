# Registry Integrity and Enclave Status

## ADDED Requirements

### Requirement: Registry Integrity
- The registry MUST be cryptographically signed or fetched from a trusted service that enforces multi-party updates.
- The Host MUST verify the registry’s signature (or authenticated source) before using any entry.
- Local edits to `measurement_registry.json` MUST be detectable and MUST cause startup to fail closed.

#### Scenario: Tampered Registry
- **Given** a valid `measurement_registry.json`.
- **When** an operator manually modifies an entry's status from "revoked" to "active" without a valid signature.
- **Then** the Host detects the signature mismatch on startup.
- **And** the Host aborts execution immediately (Fatal Error).

### Requirement: Status-Aware Enclave Gating
- The Enclave MUST be able to distinguish between:
    - “measurement known and active”
    - “measurement known but revoked”
    - “measurement unknown”
- KMS key release (for SPKs, ESSKs, EAKs) MUST depend on both:
    - attestation measurement match, and
    - an “active” status for that measurement.
- The Enclave MUST refuse to unseal or use sensitive keys if:
    - its measurement is revoked, or
    - its measurement is not in the registry.

#### Scenario: Revoked measurement cannot decrypt
- **Given** an enclave with a measurement that has been marked `revoked` in the registry.
- **When** the Host attempts to start the enclave and establish a session.
- **Then** the Enclave (independently of Host checks) verifies its status is not `active`.
- **And** the Enclave refuses to unseal the Service Public Key (SPK).
- **And** the session establishment fails.

### Requirement: End-to-End Flow
- On a fresh release, the CI SHALL compute the measurement and propose a new registry entry. The entry MUST go through a multi-party approval workflow before being marked `status = "active"`.
- At runtime, the Host SHALL verify registry integrity and that the enclave’s measurement is active. The Enclave SHALL verify its own measurement and status before enabling KMS. If Host and Enclave disagree on status/measurement, the system MUST fail closed.

#### Scenario: Host and Enclave Disagree
- **Given** the Host believes the enclave's measurement is active, but the Enclave's internal registry check determines it is revoked.
- **When** the Enclave attempts to initialize KMS.
- **Then** the Enclave SHALL fail closed, refusing to unseal keys or process traffic.
- **And** the Host's subsequent attempts to communicate will fail, leading to overall system shutdown.
