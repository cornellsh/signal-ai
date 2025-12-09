# Proposal: Signal Assistant Governance and Boundary Hardening

## Summary
This proposal hardens the operational governance of the Signal Assistant Enclave by establishing a tamper-evident registry, strictly enforcing environment boundaries, automating policy drift detection, and defining a clean open-source boundary for the enclave code.

## Rationale
Current governance relies on host-side enforcement and implicit environment variables, which can be bypassed or misconfigured. To achieve a secure supply chain and verifiable privacy guarantees:
1.  **Registry Integrity:** The enclave must verify its own status (active vs. revoked) independently of the Host.
2.  **Environment Control:** "Implicit DEV" risks accidental production exposure of debug features; dangerous capabilities must be centralized and gated.
3.  **Policy Continuity:** Manual reviews catch some drift, but automated gates tied to invariant manifests are required to prevent silent weakening of privacy protections.
4.  **OSS Readiness:** To build trust, the enclave code must be publishable as a self-contained, verifiable artifact without dependencies on host-side infrastructure.

## Goals
1.  **Tamper-Evident Registry:** Enforce registry integrity and "active" status checks inside the enclave.
2.  **Explicit Governance:** Eliminate implicit environments and centralize dangerous capabilities behind a manifest.
3.  **Automated Policy Gates:** Detect and block policy drift in CI using an invariant manifest.
4.  **Clean OSS Boundary:** Decouple enclave code from host logic to enable standalone open-source publishing.
