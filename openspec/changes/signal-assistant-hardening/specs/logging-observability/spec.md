# Logging and Observability Hardening

## MODIFIED Requirements

### Requirement: Identity Isolation in Logging
*   **Description:** The Enclave application logic (`src/signal_assistant/enclave/app.py`) MUST resolve the `SignalID` to an `internal_user_id` immediately upon message ingress using the `IdentityMappingService`. All subsequent logging calls MUST use *only* the `internal_user_id`. The `SignalID` MUST NOT be passed to any logging function, even if the logging function claims to be secure.
*   **core Ref:** 11.5
*   **privacy Ref:** 5.3, 8.1

#### Scenario:
    *   `GIVEN` an inbound message from SignalID "12345".
    *   `WHEN` `EnclaveApp` processes the message.
    *   `THEN` it MUST first call `map_signal_id_to_internal_id("12345")` to get "uuid-abc".
    *   `AND` it MUST log "Processing message for uuid-abc", NOT "Processing message for 12345".
