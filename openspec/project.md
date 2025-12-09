# Project Context

## Purpose
The primary purpose of this project is to develop a secure and privacy-preserving Signal Assistant operating within a trusted execution environment (enclave). The assistant handles various secure messaging flows (inbound and outbound), manages cryptographic keys, enforces defined law enforcement policies, and facilitates secure logging and storage. A core objective is to isolate sensitive operations within the enclave to protect user data and communication integrity.

## Tech Stack
- **Language:** Python (3.x)
- **Dependency Management:** Poetry
- **Testing Framework:** Pytest
- **Secure Communication:** `cryptography.fernet` (for host-enclave transport encryption)
- **Serialization:** JSON with custom base64 handling for `bytes` data (implemented via `CommandSerializer`)
- **Messaging Protocol (Current/Mock):** Mock Signal Protocol (intended to be replaced with a full Signal Protocol library)
- **Runtime Environment:** Simulated Enclave environment (with a clear host-enclave separation)
- **Operating System (Development):** Linux
- **Operating System (Windows Build):** Builds are intended to be run on Windows using `build_windows.ps1`

## Project Conventions

### Code Style
- **Language Style:** Adherence to PEP 8 for Python code.
- **Modularity:** Code is organized into logical modules and sub-packages (e.g., `enclave`, `host`, `privacy_core`).
- **Type Hinting:** Used for clarity and maintainability.
- **Comments:** Used to explain complex logic, design decisions, and mock implementations.

### Architecture Patterns
- **Enclave-Host Separation:** Strict division of responsibilities and code between the untrusted host and the trusted enclave.
- **Secure Communication Channel:** All communication between the host and enclave occurs over an encrypted and authenticated channel.
- **Command-based Interaction:** Host communicates with the enclave by sending structured commands, and the enclave responds with processing results.
- **Mocking for Development:** Use of mock implementations for external dependencies (like the Signal Protocol library) to facilitate development before integrating real components.

### Testing Strategy
- **Unit Testing:** Individual components are tested in isolation.
- **Integration Testing:** Verification of interactions between host and enclave components, and message flows.
- **Validation against Specs:** Tests confirm adherence to architectural specifications (`openspec`).
- **Iterative Testing:** Tests are developed and run iteratively during the development process.

### Git Workflow
- **Branching:** Implied feature branching strategy for new work and fixes.
- **Commit Conventions:** Clear, concise, and descriptive commit messages are preferred, typically following a `Type: Subject` format.

## Domain Context
- **Signal Assistant:** Refers to an AI assistant designed to integrate with and enhance the Signal messaging experience, emphasizing privacy and security.
- **Enclave:** A trusted execution environment (TEE) providing hardware-level isolation for sensitive code and data, protecting it from the potentially compromised host OS.
- **KMS (Key Management System):** Responsible for the secure generation, storage, retrieval, and lifecycle management of cryptographic keys within the enclave.
- **PII Sanitization:** The process of identifying and removing or transforming Personally Identifiable Information from data to protect user privacy.
- **LE Policy (Law Enforcement Policy):** Mechanisms within the enclave to enforce access controls and data handling policies, potentially allowing audited access under specific legal mandates.

## Important Constraints
- **Security and Privacy:** These are paramount, given the nature of the "enclave" and "Signal Assistant" functionality. All components must be designed and implemented with security as a top priority.
- **Performance:** While not explicitly detailed, secure messaging and real-time assistant capabilities imply a need for efficient processing.
- **Future Hardware Dependency:** The "enclave" concept implies a future dependency on specific hardware TEEs (e.g., Intel SGX, AMD SEV) for true security guarantees.
- **Cross-Platform Build:** Development currently on Linux, but specific build process for Windows is defined.

## External Dependencies
- `cryptography` Python library (for Fernet encryption)
- Standard Python `json` and `base64` modules
- **Future:** A full, production-grade Signal Protocol implementation library.
- **Future:** Secure, production-grade Key Management System (KMS) solution.
- Host-side database and blob storage for persistent data (encrypted).