# Identity and LE Control Hardening

## MODIFIED Requirements

### Requirement: Persistent Identity Mapping
*   **Description:** The `IdentityMappingService` MUST persist the `SignalID` <-> `internal_user_id` mapping to the Enclave's secure storage (simulated if necessary) so that mappings survive Enclave restarts.
*   **core Ref:** 5.1
*   **privacy Ref:** 8.1

#### Scenario:
    *   `GIVEN` a user "Alice" is mapped to "uuid-1".
    *   `WHEN` the Enclave restarts and reloads state.
    *   `THEN` "Alice" is still mapped to "uuid-1".

### Requirement: Strict LE Policy Delegation
*   **Description:** `EnclaveApp` MUST delegate ALL Law Enforcement policy checks and execution to `IdentityMappingService.handle_le_request`. It MUST NOT implement any shadow or simplified policy checks (like string matching on request bodies) within the command processing loop.
*   **core Ref:** 6.1.3
*   **privacy Ref:** 9.4.3

#### Scenario:
    *   `GIVEN` an inbound `CHECK_LE_POLICY` command.
    *   `WHEN` processed by `EnclaveApp`.
    *   `THEN` it invokes `IdentityMappingService.handle_le_request`.
