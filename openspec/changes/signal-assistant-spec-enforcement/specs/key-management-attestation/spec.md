# Key Management and Attestation Gating Specification

This document details the requirements for enforcing attestation-gated access to cryptographic keys within the Signal Assistant Enclave, aligning with the `Signal Assistant Core Specification` (core) and `Signal Assistant Enclave Privacy Architecture Document` (privacy).

## MODIFIED Requirements

*(This section will expand upon and modify existing core and privacy requirements related to key management and attestation. While the core documents specify the model, this spec delta focuses on *enforcement* mechanisms.)*

### KMS API Attestation Gating

### Requirement: Attestation-Dependent Key Retrieval

*   **Description:** The Enclave's Key Management Service (KMS) (`src/signal_assistant/enclave/kms.py`) MUST modify its key retrieval and unsealing APIs (e.g., `get_key`, `unseal_key`) to accept an explicit `attestation_verified: bool` parameter. Access to sensitive key types (Enclave Secure Storage Keys (ESSKs), Signal Protocol Keys (SPKs), External Service API Keys (EAKs)) MUST be conditional on this parameter being `True`.
*   **core Ref:** 9.1.1, 9.1.2, 9.1.3, 9.1.5, 9.4.3, 10.1
*   **privacy Ref:** 5.2.4, 6.1

#### Scenario:
    *   `GIVEN` an Enclave component attempts to retrieve an ESSK.
    *   `WHEN` `kms.get_key(key_id, attestation_verified=False)` is called.
    *   `THEN` the call MUST raise an `AttestationError` or similar security exception.
    *   `GIVEN` an Enclave component attempts to retrieve an EAK.
    *   `WHEN` `kms.get_key(key_id, attestation_verified=True)` is called.
    *   `THEN` the EAK MUST be successfully returned (assuming it exists and is authorized for the calling context).

### Requirement: SecureConfig Attestation Integration

*   **Description:** The `SecureConfig` module (`src/signal_assistant/enclave/secure_config.py`) responsible for managing sensitive configuration values, particularly EAKs, MUST integrate with the KMS such that it only retrieves EAKs by passing the Enclave's currently verified attestation status to the KMS.
*   **core Ref:** 9.1.5, 9.4.3
*   **privacy Ref:** 5.2.4

#### Scenario:
    *   `GIVEN` the Enclave's internal attestation state is `False`.
    *   `WHEN` `SecureConfig.get_llm_api_key()` is invoked.
    *   `THEN` `SecureConfig` MUST internally call `kms.get_key` with `attestation_verified=False`.
    *   `AND` the `get_llm_api_key` call MUST propagate an `AttestationError` or return an appropriate secure error response.

### Enclave Internal Attestation

### Requirement: Enclave Lifecycle Attestation Verification

*   **Description:** The primary Enclave application entry point (`src/signal_assistant/enclave/app.py`) MUST perform its own internal attestation verification during its startup sequence. The result of this verification (e.g., `self.attestation_is_verified: bool`) MUST be stored securely within the Enclave's runtime state.
*   **core Ref:** 9.4
*   **privacy Ref:** 6.1

#### Scenario:
    *   `GIVEN` the Enclave starts up with expected measurements.
    *   `WHEN` `enclave/app.py` performs its internal attestation check.
    *   `THEN` `self.attestation_is_verified` MUST be set to `True`.
    *   `GIVEN` the Enclave starts up with unexpected measurements (simulated for testing).
    *   `WHEN` `enclave/app.py` performs its internal attestation check.
    *   `THEN` `self.attestation_is_verified` MUST be set to `False`.

### Host-Side EAK Provisioning

### Requirement: Attestation-Gated Host Provisioning of EAKs

*   **Description:** The Host's component responsible for provisioning External Service API Keys (EAKs) to the Enclave (e.g., part of `src/signal_assistant/host/proxy.py` or a dedicated provisioning service) MUST only release EAKs to an Enclave instance if its remote attestation report has been successfully verified against a known-good set of measurements. This provisioning MUST occur over an encrypted channel to prevent Host visibility of the plaintext EAK.
*   **core Ref:** 9.1.5, 9.4.3
*   **privacy Ref:** 11.2.7

#### Scenario:
    *   `GIVEN` the Host detects an Enclave instance attempting to request EAKs.
    *   `WHEN` the Enclave provides an invalid or unverified attestation report.
    *   `THEN` the Host MUST refuse to provision the EAKs to that Enclave.
    *   `GIVEN` the Host detects an Enclave instance attempting to request EAKs.
    *   `WHEN` the Enclave provides a valid and verified attestation report.
    *   `THEN` the Host MUST securely transmit the EAKs (encrypted for the Enclave) to that Enclave.

### "No Debug Bypass" Invariant

### Requirement: Prohibition of Attestation Bypass Mechanisms

*   **Description:** There MUST NOT exist any code path, environment variable, CLI flag, configuration option, or other mechanism (on either Host or Enclave) that allows for the bypass of attestation checks for the purpose of accessing or providing sensitive cryptographic keys (ESSKs, SPKs, EAKs) to an Enclave.
*   **core Ref:** 9.4.3
*   **privacy Ref:** 11.2.7

#### Scenario:
    *   `GIVEN` an attempt to start an Enclave with a `--debug-attestation-bypass` flag.
    *   `WHEN` the Enclave attempts to obtain EAKs.
    *   `THEN` key access MUST still be gated by attestation status, and the flag MUST have no effect on this gating.
    *   `AND` the existence of such a flag in released code is a policy violation.

## ADDED Requirements

*(No new requirements are ADDED beyond modifying existing ones for enforcement. This section implicitly refines the *how* of existing requirements.)*

## REMOVED Requirements

*(None)*