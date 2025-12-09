# Design: Hardening Patterns

## Type-Safe Sanitization (`SanitizedPrompt`)
To prevent accidental bypass of the PII sanitizer, we introduce a `SanitizedPrompt` wrapper type.
- **Problem**: Passing raw `str` to `LLMClient.generate_response` allows any developer to accidentally skip the sanitization step.
- **Solution**: `LLMClient` will only accept `SanitizedPrompt`. The only way to obtain a `SanitizedPrompt` instance is via `PIISanitizer.sanitize()`.
- **Constraint**: `SanitizedPrompt` should wrap the string and be immutable.

## Identity Mapping Integration
The `IdentityMappingService` must be the single source of truth.
- `EnclaveApp` must not derive `internal_user_id` itself or use `SignalID` for any purpose other than obtaining the `internal_user_id`.
- **Flow**: `Inbound Message (SignalID)` -> `IdentityMappingService.map(SignalID)` -> `internal_user_id`.
- **LE Policy**: `EnclaveApp` must delegate all LE commands to `IdentityMappingService.handle_le_request`.

## Fail-Closed Attestation
- **Problem**: Current code returns `True` for attestation verification.
- **Solution**: The default implementation must return `False` or raise an error.
- **Testing**: Use dependency injection or a strictly gated environment variable (`MOCK_ATTESTATION_FOR_TESTS_ONLY`) that logs a critical warning when used, ensuring it cannot be enabled silently in production.

## Persistence
- **Problem**: `IdentityMappingService` uses an in-memory dict.
- **Solution**: Use `Enclave.secure_config` or a dedicated `StateStore` abstraction (mocked for now as file-backed or similar, but defined as "Secure Enclave Storage") to persist the mapping.
