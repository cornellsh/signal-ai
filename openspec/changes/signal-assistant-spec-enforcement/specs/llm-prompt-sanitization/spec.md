# LLM Prompt Construction and Sanitization Specification

This document details the requirements for the secure and privacy-preserving construction and sanitization of prompts for external Large Language Models (LLMs) within the Signal Assistant Enclave, aligning with the `Signal Assistant Core Specification` (core) and `Signal Assistant Enclave Privacy Architecture Document` (privacy).

## ADDED Requirements

### LLMPipeline Orchestration

### Requirement: Single, Mandatory LLM Interaction Pipeline

*   **Description:** The Enclave MUST implement a single, canonical `LLMPipeline` component (e.g., within `src/signal_assistant/enclave/bot/orchestrator.py`) that centralizes all interactions with external LLMs. This pipeline MUST be the *only* code path for sending text to an external LLM.
*   **core Ref:** 7.1, 7.2, 7.3, 8.1.8, 8.2.1
*   **privacy Ref:** 5.2.2

#### Scenario:
    *   `GIVEN` any request requires interaction with an external LLM (e.g., user message, tool call outcome).
    *   `WHEN` an Enclave component needs to send data to an external LLM.
    *   `THEN` it MUST invoke the `LLMPipeline` to handle the interaction.
    *   `AND` it MUST NOT directly call the external LLM client (`src/signal_assistant/enclave/bot/llm.py`).

### Requirement: Integrated PII Sanitization

*   **Description:** The `LLMPipeline` MUST ensure that the *fully assembled prompt string* (including user messages, context, and tool outputs) is passed through the `PIISanitizer` (`src/signal_assistant/enclave/privacy_core/sanitizer.py`) *before* being transmitted to any external LLM.
*   **core Ref:** 7.1.3, 8.1.7, 10.1, 10.3
*   **privacy Ref:** 5.2.1.8, 6.2

#### Scenario:
    *   `GIVEN` the `LLMPipeline` has assembled a prompt containing PII from a user message.
    *   `WHEN` the prompt is prepared for transmission to an external LLM.
    *   `THEN` the `PIISanitizer.sanitize()` method MUST be invoked on the assembled prompt string.
    *   `AND` the prompt sent to the external LLM MUST be the sanitized version, with all detected PII redacted.

### PIISanitizer Module

### Requirement: Robust PII Detection and Redaction

*   **Description:** The `PIISanitizer` module (`src/signal_assistant/enclave/privacy_core/sanitizer.py`) MUST provide a static `sanitize(text: str) -> str` method that reliably detects and redacts common Personally Identifiable Information (PII) patterns, such as phone numbers and email addresses, from arbitrary text.
*   **core Ref:** 4.3.1, 7.1.3, 10.3
*   **privacy Ref:** 6.2

#### Scenario:
    *   `GIVEN` a string "My email is user@example.com and my number is +1-555-123-4567."
    *   `WHEN` `PIISanitizer.sanitize()` is called with this string.
    *   `THEN` the returned string MUST be "My email is [EMAIL] and my number is [PHONE_NUMBER]."

## MODIFIED Requirements

*(No explicit modifications to existing requirements are defined in this spec delta, as these are primarily ADDED functionalities for enforcement. Existing `core` and `privacy` requirements are referenced as foundational principles.)*

## REMOVED Requirements

*(None)*