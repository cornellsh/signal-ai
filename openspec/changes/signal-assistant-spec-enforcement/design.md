# Design Document: Signal Assistant Spec-Enforcement Architecture

## 1. Introduction

This design document provides the architectural rationale and considerations for the Signal Assistant Spec-Enforcement phase. The primary goal is to formalize and enforce the critical privacy and security invariants outlined in the `Signal Assistant Core Specification` and `Signal Assistant Enclave Privacy Architecture Document`. This involves establishing clear boundaries, defining trusted interfaces, and implementing verifiable mechanisms to prevent architectural and implementation drift.

## 2. Architectural Philosophy: Enforcement by Design

The core philosophy of this enforcement design is to make privacy and security compliance *architecturally inherent* rather than solely reliant on developer diligence or retrospective audits. This is achieved through:

*   **Minimizing Trust Boundaries:** Explicitly defining where sensitive data can exist (solely within the Enclave) and where it cannot (Host, external logs, unsanitized LLM calls).
*   **Mandatory Pathways:** Creating single, unavoidable code paths for critical operations (e.g., LLM prompting, key access) that inherently include security controls.
*   **Compile-time and Runtime Checks:** Leveraging static analysis (linters) for early detection of policy violations and runtime assertions/integration tests for dynamic validation.
*   **Verifiable State:** Ensuring that system state (e.g., attestation status) directly gates access to sensitive resources.

## 3. Key Design Decisions and Rationale

### 3.1 Centralized Logging Interface

**Problem:** Ad-hoc logging across Host and Enclave components risks privacy violations by inadvertently logging sensitive data, direct `Signal_ID`s, or PII.

**Solution:** Implement a mandatory, centralized logging interface for both Host and Enclave.

**Rationale:**
*   **Enforcement at the Source:** By controlling the logging function's API, we can programmatically restrict what can be logged, preventing sensitive data from ever reaching log sinks.
*   **Consistency:** Ensures all logs adhere to the `core` 11.5 schema constraints, simplifying parsing and auditing.
*   **Auditability:** Provides a single point of control and review for all operational logging, crucial for `privacy` 10.
*   **Host Blindness:** The Enclave-side logger can anonymize and encrypt sensitive metadata before transmitting it to the Host, maintaining `core` 10.2.

**Trade-offs:**
*   **Initial Overhead:** Requires refactoring existing logging calls.
*   **Reduced Flexibility:** Developers cannot log arbitrary strings containing potentially sensitive information, requiring careful thought about what truly constitutes non-sensitive operational data. This is an intentional and necessary constraint for privacy.

### 3.2 Single LLM Prompt Orchestration Pipeline

**Problem:** Multiple code paths for interacting with external LLMs increase the risk of bypassing PII sanitization or other guardrails, leading to data leakage.

**Solution:** Consolidate all LLM interaction logic into a single, mandatory `LLMPipeline` component within the Enclave.

**Rationale:**
*   **Guaranteed Sanitization:** Ensures that PII sanitization (`core` 10.3, `privacy` 6.2) is *always* applied to the *fully assembled* prompt before any external LLM call.
*   **Unified Safety Controls:** Centralizes pre- and post-processing safety checks (`core` 7.5), making them universally applicable.
*   **Simpler Auditing:** Reviewing a single component to ensure LLM interaction compliance is more efficient than auditing numerous dispersed call sites.
*   **Maintainability:** Changes to prompt engineering, sanitization logic, or external LLM APIs are managed in one place.

**Trade-offs:**
*   **Tight Coupling:** The `LLMPipeline` becomes a critical component; any issues within it impact all LLM interactions. This necessitates robust testing.
*   **Performance Implications:** While minimal, forcing all interactions through a single pipeline might introduce minor overhead compared to highly optimized, direct calls (if such existed). However, the security benefit significantly outweighs this.

### 3.3 Attestation-Gated Key Management

**Problem:** Keys (especially EAKs and sealed Enclave keys) could be provisioned to or used by a compromised or unauthorized Enclave, undermining the TEE's security guarantees. Backdoor mechanisms for key access circumvent trust.

**Solution:** Enforce attestation-gating for all sensitive key access, both at the Host-to-Enclave provisioning stage and within the Enclave's internal KMS. Explicitly prohibit any bypass.

**Rationale:**
*   **Integrity Verification:** Guarantees that only an attested, known-good Enclave (matching expected measurements) can access or unseal sensitive keys (`core` 9.4.3).
*   **Host Blindness Reinforcement:** Host-side provisioning mechanisms for EAKs MUST ensure keys are delivered encrypted to an attested Enclave, preventing the Host from ever seeing them in plaintext.
*   **No Backdoors:** The explicit "no debug bypass" invariant prevents developers (or attackers) from easily circumventing attestation checks for convenience or malicious intent. This is a critical operational security control (`core` 9.4.3).

**Trade-offs:**
*   **Complexity:** Requires careful coordination between Host provisioning logic and Enclave KMS initialization.
*   **Development Friction:** Attestation verification adds a layer of indirection to key access, requiring a more rigorous development and testing cycle. This is an intentional security hardening.

### 3.4 Encapsulated Identity and LE Control

**Problem:** Dispersed handling of `Signal_ID`s, user data deletion, and Law Enforcement (LE) requests increases the risk of inconsistent policy enforcement and data leakage.

**Solution:** Centralize `Signal_ID` to `internal_user_id` mapping, user data deletion, and `handle_le_request` logic within a dedicated `IdentityMappingService` in the Enclave. Implement `CHECK_LE_POLICY` as a mandatory internal gate.

**Rationale:**
*   **Single Source of Truth for Identity:** The `IdentityMappingService` becomes the sole component responsible for managing the sensitive `Signal_ID` to `internal_user_id` mapping, ensuring `core` 10.6 and `privacy` 8.
*   **Guaranteed Data Deletion:** Centralized `delete_user_data` ensures comprehensive purging of all associated data upon user request, fulfilling `privacy` 7.3.
*   **Consistent LE Policy Enforcement:** All LE requests are routed through `handle_le_request`, which *must* invoke `CHECK_LE_POLICY` before any data access, enforcing `privacy` 9.4.3 and multi-party controls. This prevents ad-hoc data disclosure.
*   **Auditability:** Centralized logging of LE request attempts and outcomes within this service supports accountability.

**Trade-offs:**
*   **Criticality:** The `IdentityMappingService` becomes a highly sensitive component; its correctness is paramount for identity privacy.
*   **Integration Points:** Requires careful integration with other Enclave components that need to reference `internal_user_id`s, ensuring they never handle `Signal_ID` directly.

## 4. Cross-Cutting Design Considerations

### 4.1 Static Analysis and CI/CD Integration

The introduction of new static analysis rules (`ruff` plugins, `pylint` checks, `grep`/`ripgrep` hooks) directly into the CI/CD pipeline is a fundamental design choice. This shifts detection of policy violations left in the development lifecycle, catching errors before deployment.

### 4.2 Robust Testing Strategy

The emphasis on comprehensive unit, integration, and particularly *negative* tests for all enforcement mechanisms is critical. Negative tests (`core` 9.4.3, `privacy` 9.1.1.1) prove the system's resilience against disallowed operations and ensure that security controls function as intended even under adversarial conditions.

### 4.3 Data Structures and Type Enforcement

Where possible, using distinct, Enclave-specific types for sensitive data (e.g., `SignalID`, `InternalUserID`, `PlainTextContent`) and enforcing their usage patterns through type-checking (e.g., mypy) can prevent accidental exposure or incorrect handling, particularly across the Host-Enclave boundary. The Host should operate on opaque encrypted blobs or `InternalUserID`s, never `SignalID` or `PlainTextContent`.

## 5. Architectural Diagram (Conceptual)

*(Placeholder: A high-level diagram illustrating the data flow through the enforced pipelines, highlighting the `LLMPipeline` with `PIISanitizer`, `KMS` with attestation gating, and `IdentityMappingService` with `CHECK_LE_POLICY`. Emphasize trust boundaries and mandatory control points.)*

## 6. Future Architectural Enhancements

*   **Dedicated Policy Engine:** For `CHECK_LE_POLICY` and other dynamic policy enforcements, a more sophisticated, declarative policy engine could be integrated into the Enclave, allowing for easier updates and auditing of rules.
*   **Fine-Grained Access Control within Enclave:** Implementing a more granular access control system within the Enclave itself to restrict which internal modules can access specific types of sensitive data or perform critical operations.
*   **Automated Attestation Measurement Verification:** Fully automating the process of generating, storing, and verifying attestation measurements within the CI/CD pipeline, linking them to specific code versions.