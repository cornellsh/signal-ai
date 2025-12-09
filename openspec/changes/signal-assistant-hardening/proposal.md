# Proposal: Signal Assistant Implementation Hardening

## Background
A focused red-team review of the `signal-assistant-spec-enforcement` work identified several critical gaps where the implementation did not fully align with the specification's intent. Specifically, `SignalID` leakage was possible in `app.py`, the LE policy checks were disconnected from the main application flow, LLM sanitization relied on convention rather than type safety, and attestation checks were hardcoded to bypass in production paths.

## Goal
This proposal aims to close all identified red-team findings (1.1, 2.1, 2.2, 3.1, 4.1, 4.2) by enforcing strict type safety, wiring up disconnected components, and implementing fail-closed security defaults. This ensures the codebase strictly adheres to the `Signal Assistant Core Specification` and `Enclave Privacy Architecture`.

## Scope
1.  **Identity & Logging**: Wire `IdentityMappingService` into `EnclaveApp` to prevent `SignalID` leakage.
2.  **LLM Sanitization**: Introduce `SanitizedPrompt` type to enforce sanitization at the compiler/interpreter level.
3.  **Attestation**: Remove hardcoded bypasses and enforce fail-closed logic.
4.  **Persistence**: Ensure identity mappings and user state persist across Enclave restarts.
