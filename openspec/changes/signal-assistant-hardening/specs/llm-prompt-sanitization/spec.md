# LLM Prompt Sanitization Hardening

## ADDED Requirements

### Requirement: `SanitizedPrompt` Type Enforcement
*   **Description:** The system MUST enforce sanitization via the type system. A dedicated wrapper type, `SanitizedPrompt` (or equivalent), MUST be defined. `PIISanitizer.sanitize` MUST return this type. `LLMClient.generate_response` MUST accept *only* this type as its prompt argument.
*   **core Ref:** 7.1.3
*   **privacy Ref:** 5.2.1.8

#### Scenario:
    *   `GIVEN` a developer attempts to pass a raw string to `LLMClient.generate_response`.
    *   `WHEN` the code is interpreted or statically analyzed.
    *   `THEN` it SHOULD raise a type error or runtime validation error.
    *   `GIVEN` a string has been processed by `PIISanitizer.sanitize`.
    *   `WHEN` it is passed to `LLMClient`.
    *   `THEN` it is accepted as a valid `SanitizedPrompt`.

## MODIFIED Requirements

### Requirement: Robust PII Detection
*   **Description:** The `PIISanitizer` regex patterns MUST be hardened to support international phone number formats (e.g., E.164, dot/space separators) and robust email address structures.
*   **core Ref:** 10.3
*   **privacy Ref:** 6.2

#### Scenario:
    *   `GIVEN` a user message contains "+44 20 7123 4567".
    *   `WHEN` sanitized.
    *   `THEN` the number is redacted.
