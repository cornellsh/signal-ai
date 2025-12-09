# Identity and Law Enforcement Control Specification

This document details the requirements for managing user identities, data deletion, and Law Enforcement (LE) access control within the Signal Assistant Enclave, aligning with the `Signal Assistant Core Specification` (core) and `Signal Assistant Enclave Privacy Architecture Document` (privacy).

## ADDED Requirements

### IdentityMappingService

### Requirement: Centralized Identity Mapping Management

*   **Description:** The Enclave MUST implement an `IdentityMappingService` (within `src/signal_assistant/enclave/privacy_core/core.py`) as the sole authority for managing the mapping between Signal User Identifiers (`SignalID`) and `internal_user_id`s.
*   **core Ref:** 5.1, 10.6
*   **privacy Ref:** 8.1

#### Scenario:
    *   `GIVEN` a user's `SignalID` is received by the Enclave for the first time.
    *   `WHEN` the `IdentityMappingService.map_signal_id_to_internal_id(signal_id)` function is invoked.
    *   `THEN` a new, cryptographically secure `internal_user_id` MUST be generated and associated with the `SignalID`.
    *   `AND` this mapping MUST be securely stored encrypted within the Enclave's secure storage.
    *   `AND` subsequent requests with the same `SignalID` MUST retrieve the existing `internal_user_id`.

### Requirement: Exclusive `SignalID` Handling

*   **Description:** The `IdentityMappingService` MUST be the *only* component within the Enclave that directly handles `SignalID` for mapping purposes. All other Enclave components and the Host MUST operate using `internal_user_id` for user-related data.
*   **core Ref:** 5.1.1.4, 10.6
*   **privacy Ref:** 8.1.1.2

#### Scenario:
    *   `GIVEN` an Enclave component processes a user's request.
    *   `WHEN` the component requires a user identifier.
    *   `THEN` it MUST use the `internal_user_id` obtained from `IdentityMappingService`, and MUST NOT directly access or store the `SignalID`.

### User Data Deletion

### Requirement: Comprehensive User Data Deletion Trigger

*   **Description:** The `IdentityMappingService` MUST provide a `delete_user_data(internal_user_id)` function that, when invoked, triggers a comprehensive deletion process for all data associated with the given `internal_user_id`.
*   **core Ref:** 5.2.1.3, 5.2.2.5
*   **privacy Ref:** 7.3

#### Scenario:
    *   `GIVEN` a user has interacted with the Assistant, generating mappings, long-term memory, and configuration.
    *   `WHEN` `IdentityMappingService.delete_user_data(internal_user_id)` is called.
    *   `THEN` the `(Signal_ID, internal_user_id)` mapping MUST be irrevocably purged from the Enclave's secure storage.
    *   `AND` all `LongTermMemory` and persisted conversational context/state associated with the `internal_user_id` MUST be purged.
    *   `AND` any user-specific configuration/preferences associated with the `internal_user_id` MUST be purged.
    *   `AND` a secure IPC notification MUST be sent to the Host to request deletion of Host-side metadata uniquely keyed by that `internal_user_id`.

### Requirement: User Deletion via Control Command

*   **Description:** Users MUST be able to initiate their data deletion via a secure, authenticated control command processed by the Enclave.
*   **core Ref:** 6.1.2
*   **privacy Ref:** 12.3

#### Scenario:
    *   `GIVEN` a user sends a `!delete_data` command to the Assistant.
    *   `WHEN` the Enclave processes this control command.
    *   `THEN` the `IdentityMappingService.delete_user_data()` function MUST be invoked for the sender's `internal_user_id`.

### Law Enforcement (LE) Control Path

### Requirement: Dedicated LE Request Handling API

*   **Description:** The Enclave MUST expose a dedicated internal API (`IdentityMappingService.handle_le_request(request_type, target_id, auth_context)`) for processing Law Enforcement (LE) data requests. This API MUST be the sole entry point for such requests.
*   **core Ref:** 6.1.3
*   **privacy Ref:** 9.1.2.3, 9.4.3

#### Scenario:
    *   `GIVEN` an authenticated internal administrative system wishes to query user data for LE purposes.
    *   `WHEN` `IdentityMappingService.handle_le_request()` is called with the request details.
    *   `THEN` the request MUST be processed according to the defined LE policy.

### Requirement: Mandatory `CHECK_LE_POLICY` Enforcement

*   **Description:** The `handle_le_request` function MUST internally invoke a `CHECK_LE_POLICY` function *before* attempting any data access. `CHECK_LE_POLICY` MUST validate the legal basis and authorization context, and MUST default to DENY in ambiguous cases.
*   **core Ref:** (implied by 6.1.3)
*   **privacy Ref:** 9.4.3

#### Scenario:
    *   `GIVEN` `handle_le_request` is invoked with `auth_context` representing an invalid legal order.
    *   `WHEN` `CHECK_LE_POLICY` is executed.
    *   `THEN` `CHECK_LE_POLICY` MUST return `DENY`.
    *   `AND` `handle_le_request` MUST NOT proceed to access any sensitive user data.

### Requirement: Multi-Party Authorization for Sensitive LE Requests

*   **Description:** The `handle_le_request` function, through `CHECK_LE_POLICY`, MUST enforce multi-party authorization for sensitive LE requests (e.g., retrieving `SignalID` to `internal_user_id` mappings). This authorization MUST involve at least two independent approvals.
*   **core Ref:** (implied by 6.1.3)
*   **privacy Ref:** 9.1.2.3

#### Scenario:
    *   `GIVEN` a request to retrieve a `SignalID` mapping is made via `handle_le_request`.
    *   `WHEN` `CHECK_LE_POLICY` evaluates the `auth_context`.
    *   `THEN` it MUST verify the presence of at least two distinct authorization tokens/signatures corresponding to independent approvers.
    *   `AND` if this condition is not met, the request MUST be denied.

### Requirement: Limited Data Provisioning for LE

*   **Description:** `handle_le_request`, if permitted by `CHECK_LE_POLICY`, MUST *only* provide data explicitly allowed by `privacy` 9.1.2 (Limited Host Operational Logs, Proof of Communication, Identity Mappings from Running Enclave via audited control path, Non-Content Signal Metadata). It MUST NOT provide any data explicitly forbidden by `privacy` 9.1.1 (Plaintext User Messages, Signal IDs Linked to Content/Memory, Encrypted LLM Prompts/Responses, Plaintext Keys).
*   **core Ref:** (implied by 6.1.3)
*   **privacy Ref:** 9.1.1, 9.1.2

#### Scenario:
    *   `GIVEN` a valid LE request for historical plaintext messages is submitted.
    *   `WHEN` `handle_le_request` processes this request.
    *   `THEN` it MUST deny the request, as per `privacy` 9.1.1.1.
    *   `GIVEN` a valid LE request for an `internal_user_id`'s corresponding `SignalID` (with valid multi-party auth).
    *   `WHEN` `handle_le_request` processes this request.
    *   `THEN` it MAY retrieve and return the `SignalID` from the currently running Enclave, as per `privacy` 9.1.2.3.

## MODIFIED Requirements

*(No explicit modifications to existing requirements are defined in this spec delta, as these are primarily ADDED functionalities for enforcement. Existing `core` and `privacy` requirements are referenced as foundational principles.)*

## REMOVED Requirements

*(None)*