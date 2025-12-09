# Operational Governance for Signal Assistant Enclave

## 1. Problem Description
The current Signal Assistant architecture defines rigorous core and privacy invariants (e.g., "no plaintext keys outside enclave", "PII sanitization"). However, it lacks a formal **operational governance** layer to ensure these invariants hold true in real-world deployments over time. Specifically, there are no normative mechanisms to:
1.  Prevent a "dev-mode" enclave build (with debug logging or mock attestation) from being accidentally or maliciously deployed to production.
2.  Allow clients and operators to cryptographically verify that a running enclave matches a specific, authorized version of the code.
3.  Governing the lifecycle of enclave measurements (release, rollback, revocation) to prevent "policy drift" or the reintroduction of vulnerable versions.

Without this layer, the theoretical security of the TEE is undermined by the practical risks of misconfiguration, operational error, or supply-chain confusion.

## 2. Proposed Change
We propose establishing a formal **Operational Governance** layer for the Signal Assistant, codified in three new specifications:

1.  **Attestation & Measurement Registry:** A normative system for publishing, versioning, and verifying authorized enclave measurements (MRENCLAVE/MRSIGNER). This registry becomes the root of trust for allowing an enclave to receive keys or serve traffic.
2.  **Environment & Configuration Governance:** A strict taxonomy of environments (Local, CI, Test, Staging, Prod) with hard rules on allowed configurations. "Dangerous" flags (e.g., `MOCK_ATTESTATION`) must be impossible to enable in production builds.
3.  **Release, Rollback & Policy Drift:** A defined lifecycle for enclave builds, requiring explicit approval and registration of measurements before deployment, and preventing silent weakening of privacy policies (policy drift).

This proposal moves beyond *what* the enclave does (covered by Core/Privacy specs) to *how* it is safely built, shipped, and verified.

## 3. Scope & Dependencies
### In Scope
-   Definition of the "Measurement Registry" data structures and validation logic.
-   Startup-time enforcement of environment invariants (e.g., "I am a production build, I refuse to run if mock-attestation is enabled").
-   CI/CD policy requirements for build verification.
-   Protocols for client/operator verification of running enclaves against the registry.

### Out of Scope
-   The internal implementation of the TEE platform itself (SGX/SEV-SNP details).
-   Changes to the core Signal Protocol or LLM sanitization logic (except where configuration governs them).
-   Manual operational runbooks (we focus on technical enforcement).

### Relationships
-   **Builds on:** `signal-assistant-spec-enforcement` (using the enforcement framework to check operational invariants).
-   **Enforces:** `docs/signal_assistant_core.md` (specifically Section 9.4 Attestation Model).
-   **Enforces:** `docs/privacy_architecture.md` (specifically Section 9.3 Public Detectability).

## 4. Key Invariants Enforced
-   **Registry-Gated Execution:** No enclave shall receive secrets or serve production traffic unless its measurement is listed as "Active" in the signed Measurement Registry.
-   **Environment Isolation:** Code paths that weaken security (e.g., `MOCK_ATTESTATION`) must be structurally unreachable in production builds, not just configuration-gated.
-   **Anti-Rollback:** Revoked measurements must be permanently rejected, preventing replay of vulnerable old versions.
