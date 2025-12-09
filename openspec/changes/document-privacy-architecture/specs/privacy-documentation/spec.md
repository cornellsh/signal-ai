## ADDED Requirements

### Requirement: System Context and Model Derivation
The Privacy Architecture Document SHALL clearly state that its underlying system model and components are derived from the `signal-assistant-core` specification.
#### Scenario: Referencing Core Spec
- The Privacy Architecture Document SHALL reference the `openspec/changes/document-privacy-architecture/specs/signal-assistant-core/spec.md` for details on system purpose, components, and high-level data flow.
- The Privacy Architecture Document SHALL avoid duplicating definitions of core system components or general data flow, instead focusing on privacy-specific details.

### Requirement: Comprehensive Privacy Document
The project SHALL have a comprehensive Privacy Architecture Document that serves as the definitive source of truth for all privacy aspects of the Signal Assistant Enclave.
#### Scenario: Accessibility for Stakeholders
- The Privacy Document SHALL be written in a human-understandable format, accessible to both senior technical staff and project managers.
- The Privacy Document SHALL clearly define all domain-specific terms relevant to privacy.

### Requirement: Privacy Principles and Commitments
The Privacy Document SHALL explicitly state the core privacy principles and commitments guiding the Signal Assistant Enclave.
#### Scenario: Architectural Philosophy
- The Privacy Document SHALL explain how privacy principles influenced the overall architectural design, particularly the use of Trusted Execution Environments (TEEs).

### Requirement: Data Inventory and Classification
The Privacy Document SHALL provide a detailed inventory and classification of all data types processed by the Signal Assistant Enclave.
#### Scenario: Sensitivity Categorization
- The Privacy Document SHALL categorize data by sensitivity (e.g., PII, sensitive non-PII, non-sensitive).

### Requirement: Data Flow and Processing Description
The Privacy Document SHALL clearly describe the end-to-end data flow and processing stages within the Signal Assistant Enclave.
#### Scenario: Inbound and Outbound Message Processing
- The Privacy Document SHALL detail the processing of inbound messages, including decryption, PII sanitization, and handling within the enclave.
- The Privacy Document SHALL detail the processing of outbound messages, including composition and encryption within the enclave.
#### Scenario: External Interactions
- The Privacy Document SHALL describe how data interacts with external services, such as Large Language Model (LLM) APIs, including any anonymization or redaction performed.
#### Scenario: Enclave vs Host Processing
- The Privacy Document SHALL explicitly identify where specific data processing activities occur (i.e., within the Enclave or on the Host).

### Requirement: Privacy Enhancing Technologies and Controls
The Privacy Document SHALL detail all privacy-enhancing technologies and controls implemented within the Signal Assistant Enclave.
#### Scenario: Enclave Protection
- The Privacy Document SHALL explain how the enclave protects data confidentiality and integrity.
- The Privacy Document SHALL discuss the role of attestation in establishing trust in the enclave's privacy guarantees.
#### Scenario: PII Sanitization
- The Privacy Document SHALL provide a detailed description of the PII sanitization mechanisms, including what PII is targeted, how it is transformed/redacted, and where in the data flow it occurs.
#### Scenario: Encryption Mechanisms
- The Privacy Document SHALL describe all encryption mechanisms employed, including host-enclave transport encryption and any future end-to-end encryption (e.g., Signal Protocol).

### Requirement: Data Storage and Retention Policies
The Privacy Document SHALL define the policies for data storage, retention, and deletion.
#### Scenario: Storage Locations
- The Privacy Document SHALL specify where different types of data are stored (e.g., host database, blob store, enclave secure storage).
#### Scenario: Retention and Deletion
- The Privacy Document SHALL clearly state the retention periods for various data types and the procedures for data deletion.

### Requirement: Identity Management and Anonymization
The Privacy Document SHALL explain how user identities are managed and how anonymization is applied.
#### Scenario: Identity Binding
- The Privacy Document SHALL describe the process of securely binding user identities to enclave operations.
- The Privacy Document SHALL explain the use of internal, pseudonymous identifiers within the enclave.

### Requirement: Law Enforcement and Access Policies
The Privacy Document SHALL outline the procedures and policies for handling law enforcement requests and controlled access to data.
#### Scenario: LE Policy Enforcement
- The Privacy Document SHALL describe the mechanism for enforcing law enforcement policies, such as the `CHECK_LE_POLICY` command.
- The Privacy Document SHALL acknowledge and reference relevant legal and regulatory frameworks for data access.

### Requirement: Auditing and Accountability
The Privacy Document SHALL describe the logging strategy and audit trails related to privacy-sensitive operations.
#### Scenario: Privacy-Preserving Logging
- The Privacy Document SHALL detail what information is logged, where, and why, with a focus on preserving privacy.

### Requirement: Privacy Threat Model
The Privacy Document SHALL include a section on privacy-specific threats and their mitigation strategies.
#### Scenario: Identified Threats and Mitigations
- The Privacy Document SHALL outline potential privacy threats to the Signal Assistant Enclave and describe how the design and implementation mitigate these threats.

### Requirement: User Transparency and Control
The Privacy Document SHALL describe how user transparency and control over their data are maintained.
#### Scenario: Consent and Information
- The Privacy Document SHALL explain how user consent is obtained and managed.
- The Privacy Document SHALL specify what information is provided to users regarding data handling practices.
