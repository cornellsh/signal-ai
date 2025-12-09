# Design for Signal Assistant Enclave Privacy Documentation

## Purpose
This document outlines the design and structure for the "Signal Assistant Enclave Privacy Architecture Document" (hereafter, "Privacy Document"). The Privacy Document will serve as the definitive source of truth regarding how user data is handled, protected, and managed within the Signal Assistant ecosystem, with a specific focus on the enclave's role. It will be detailed yet accessible, designed for both technical and non-technical stakeholders.

## Document Structure

The Privacy Document will be organized into the following key sections:

### 1. Executive Summary
-   **Purpose:** High-level overview of the Signal Assistant's privacy commitment and the document's scope.
-   **Key Takeaways:** Summarize the core privacy principles and guarantees.

### 2. Introduction & Scope
-   **Project Overview:** Briefly describe the Signal Assistant and its primary function.
-   **Definition of Terms:** Define "Enclave," "PII," "Host," "User Data," etc.
-   **Document Scope:** What the document covers (e.g., data types, processing stages, protective measures) and what it does not (e.g., general Signal protocol privacy, unless directly impacted by the assistant).

### 3. Privacy Principles
-   **Core Privacy Commitments:** Explicitly state the foundational principles (e.g., data minimization, privacy by design, user control, transparency).
-   **Architectural Philosophy:** How privacy guides the overall design, especially the use of TEEs.

### 4. Data Inventory & Classification
-   **Data Types Processed:**
    -   User Messages (plaintext, encrypted)
    -   User IDs (Signal IDs, internal IDs)
    -   LLM Inputs/Outputs
    -   Interaction Logs
    -   Key Material
    -   Metadata
-   **Data Classification:** Categorize data by sensitivity (e.g., PII, sensitive non-PII, non-sensitive).

### 5. Data Flow & Processing
-   **High-Level Data Flow Diagram:** Visual representation of data movement.
-   **Detailed Data Flow Descriptions:**
    -   **Inbound Messages:** How messages are received, decrypted (in enclave), sanitized, and processed.
    -   **Outbound Messages:** How messages are composed, encrypted (in enclave), and sent.
    -   **LLM Interaction:** How data interacts with external LLM APIs (e.g., anonymized prompts).
    -   **KMS Operations:** Data involved in key generation, storage, and retrieval.
    -   **Identity Binding:** Data used for binding user identities to enclave data.
-   **Data Processing Locations:** Explicitly identify where data is processed (Host vs. Enclave).

### 6. Privacy Enhancing Technologies & Controls
-   **Enclave's Role:**
    -   How the enclave protects confidentiality and integrity.
    -   Attestation and its implications for trust.
-   **PII Sanitization:**
    -   Description of `PIISanitizer` (e.g., `privacy_core/sanitizer.py`).
    -   What PII is targeted and how it's transformed/redacted.
    -   Where sanitization occurs (e.g., before LLM interaction, before logging).
-   **Encryption Mechanisms:**
    -   End-to-End Encryption (Signal Protocol - future integration).
    -   Host-Enclave Transport Encryption (`cryptography.fernet`).
    -   Storage Encryption (for data at rest on host, managed by enclave).
-   **Data Minimization:** How unnecessary data collection/retention is avoided.

### 7. Data Storage & Retention
-   **Storage Locations:** Where different types of data are stored (e.g., host database, blob store, enclave secure storage).
-   **Retention Policies:** How long different data types are kept and why.
-   **Deletion Policies:** Procedures for data deletion.

### 8. Identity Management & Anonymization
-   **Identity Binding:** How user identities are linked to enclave operations.
-   **Internal Identifiers:** Use of pseudonymous identifiers within the enclave.
-   **Anonymization Strategies:** Techniques used to prevent re-identification.

### 9. Law Enforcement & Access Policies
-   **LE Policy Enforcement:** Description of how `CHECK_LE_POLICY` command works.
-   **Transparency:** How requests for data are handled, if applicable.
-   **Legal & Regulatory Context:** Acknowledgment of relevant legal frameworks (e.g., GDPR, CCPA, specific regional laws).

### 10. Auditability & Accountability
-   **Logging Strategy:** What is logged, where, and why (focus on privacy-preserving aspects of logging).
-   **Audit Trails:** How system activities related to data access and processing are recorded.

### 11. Threat Model (Privacy-Specific)
-   **Identified Privacy Threats:** Scenarios where user privacy could be compromised.
-   **Mitigation Strategies:** How the design and implementation address these threats.

### 12. User Transparency & Control
-   **User Consent:** How user consent is obtained and managed.
-   **Information Provided to Users:** What users are told about data handling.
-   **Mechanisms for User Data Access/Deletion:** How users can exercise their rights.

### 13. Future Considerations
-   **Real Signal Protocol Integration:** Impact on privacy architecture.
-   **Hardware TEE Integration:** Further privacy guarantees.
-   **Ongoing Privacy Reviews:** Commitment to continuous assessment.

## Audience
-   **Primary:** Project managers, senior developers, architects, security engineers.
-   **Secondary:** Compliance officers, legal team, future auditors.

## Format & Style
-   Clear, concise, and unambiguous language.
-   Avoid excessive technical jargon where possible; explain terms clearly.
-   Use diagrams and flowcharts where beneficial.
-   Maintained as a Markdown document within the `docs/` directory.
