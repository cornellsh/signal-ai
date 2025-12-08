# Tasks: Refactor signal-ai to AI-Powered Signal Assistant

This document outlines the ordered tasks to transform the `signal-ai` project into a commercial, hosted, AI-powered Signal assistant with extreme privacy guarantees.

## Phase 1: Project Cleanup, Renaming, and Initial Setup

1.  [x] **Cleanup Existing Codebase:**
    *   **Description:** Remove all outdated, unused, or "dead" code from the `src/signal_ai/` directory that is not relevant to the new AI assistant bot. This includes old commands, services, and any experimental code from the `signal-client` development phase.
    *   **Validation:** Directory `src/signal_ai/` contains only essential files or empty placeholders.
2.  [x] **Rename Top-Level Package:**
    *   **Description:** Rename the top-level package from `src/signal_ai` to `src/ai_assistant_bot` to reflect the new project's purpose. Update all internal references accordingly.
    *   **Validation:** All imports and module references are updated, and the project can be built/run without errors (though functionality is minimal at this stage).
3.  [x] **Update Core Dependencies:**
    *   **Description:** Review `pyproject.toml` and `poetry.lock`. Ensure `signal-client` is the latest stable version. Remove any unnecessary development dependencies. Add essential core dependencies for the new architecture (e.g., specific TEE SDK client libraries, database drivers, LLM API client libraries).
    *   **Validation:** `poetry update` runs successfully, and all dependencies are aligned with the new project's needs.
4.  [x] **Implement Core Configuration:**
    *   **Description:** Refine `config.py` to handle environment variables for Signal credentials, AI model API keys, database connections, and TEE attestation service endpoints.
    *   **Validation:** Bot can load configuration correctly from `.env` file.

## Phase 2: Establishing the Privacy Core (TEE-Bound Components)

This phase focuses on implementing the critical privacy-preserving components within a simulated TEE environment (for development) and preparing them for a real TEE deployment. These components will eventually form the "open-source privacy core."

5.  [x] **Design the Privacy Core's Boundaries and APIs:**
    *   **Description:** Formally define the strict boundaries, interfaces, and APIs for the "Privacy Core." This minimal set of code will be responsible for Signal message decryption, initial prompt sanitization (PII stripping), Signal key management, and remote attestation integration. Document the proposed interfaces.
    *   **Validation:** A clear architectural document detailing the Privacy Core's scope and interfaces (e.g., a markdown file in the `signal_adapter` or `core` directory) exists and is approved.
6.  [x] **Implement TEE-Compatible Signal Adapter (Privacy Core Component):**
    *   **Description:** Based on the Privacy Core API design from Task 5, implement the `signal_adapter` components (client, events, messages) that will run within the TEE. This involves implementing the logic for securely receiving encrypted messages from the Event Processing Layer and performing decryption *only within this TEE-bound adapter*. Develop this against a development mock TEE environment.
    *   **Validation:** Unit tests verify that message decryption logic is isolated within this component and adheres to the defined Privacy Core API. Signal keys are demonstrably not accessible outside this component.
7.  **Develop Initial Prompt Sanitization Logic (Privacy Core Component):**
    *   **Description:** Implement the logic within the Privacy Core to detect and strip PII from the decrypted message content. This process must occur *before* the sanitized prompt leaves the TEE for interaction with external LLM APIs.
    *   **Validation:** Unit tests demonstrate effective PII stripping for various data types and scenarios, ensuring no PII is inadvertently exposed.
8.  **Integrate TEE SDK and Attestation Logic (Development Mock):**
    *   **Description:** Integrate a TEE SDK (or a mock interface for development) to manage the simulated secure enclave environment. Implement logic within the Privacy Core to generate mock attestation reports, including a simulated code measurement based on the Privacy Core's components. This mock should allow for local testing of the attestation process.
    *   **Validation:** A development endpoint or internal function can be called to return a mock attestation report, which can be verified against a predefined mock hash.
9.  **Define Secure Key Provisioning Mechanism (Conceptual & Mock):**
    *   **Description:** Define and document the conceptual flow for securely provisioning the bot's Signal private key into the TEE, ensuring the developer never has plaintext access. This documentation should outline the steps involved and the security considerations. For immediate testing, implement a simple mock mechanism that simulates a secure key load, allowing development of dependent components.
    *   **Validation:** Comprehensive documentation for the key provisioning process is complete. A basic mock function allows the `signal_adapter` to simulate key loading.

## Phase 3: Core Bot Functionality (Closed-Source Components)

This phase builds the main AI assistant logic, which will interact with the Privacy Core and external services.

10. **Scaffold Event Processing Layer:**
    *   **Description:** Implement the event listener and router outside the TEE, forwarding encrypted Signal events to the Privacy Core and receiving processed (sanitized) events/prompts back.
    *   **Validation:** Encrypted Signal messages are received and correctly relayed to the Privacy Core interface.
11. **Scaffold AI Orchestration Layer (External LLM Integration):**
    *   **Description:** Implement the `llm_manager` and `orchestrator` components. This layer will receive sanitized prompts from the Privacy Core, interact with external LLM APIs (e.g., Gemini, ChatGPT), and manage tool calling.
    *   **Validation:** The AI Orchestration layer can receive a sanitized prompt and obtain a response from an external LLM.
12. **Implement Basic Short-Term Memory (Sliding Window/Summarization):**
    *   **Description:** Implement initial logic for managing conversation history (sliding window and/or summarization) to maintain context for the LLM. This will primarily occur outside the TEE but might involve calls to the Privacy Core for sensitive summarization.
    *   **Validation:** Bot maintains basic conversation context across a few turns.
13. **Set up Persistence Layer:**
    *   **Description:** Implement the chosen database (e.g., SQLAlchemy with PostgreSQL) for storing user profiles, conversation summaries (not raw messages), bot configuration, and long-term memory data.
    *   **Validation:** Database can be initialized, and basic anonymized data (e.g., user preferences, summary hashes) can be stored and retrieved.
14. **Implement Core Application Logic & Commands:**
    *   **Description:** Develop the main business logic and bot commands (e.g., `/remember`, `/mypatterns`) that leverage the AI Orchestration and Persistence layers. This is the closed-source functional core.
    *   **Validation:** Core commands function as expected, demonstrating interaction with AI and persistence.

## Phase 4: Security Hardening, Verification, and Deployment

15. **Integrate Real Remote Attestation:**
    *   **Description:** Replace the development mock with actual TEE SDK integration for generating and verifying attestation reports on a real TEE platform.
    *   **Validation:** The bot can provide a cryptographically verifiable attestation report.
16. **Develop User-Side Attestation Verification Tool (Open Source):**
    *   **Description:** Create a simple, open-source client-side application or script that allows users to independently request and verify the bot's attestation report against published hashes.
    *   **Validation:** Users can verify the integrity of the Privacy Core.
17. **Refine Privacy Core & Open Source:**
    *   **Description:** Publicly release the Privacy Core code. Conduct and publish an independent security audit of this open-source component.
    *   **Validation:** Privacy Core is open-source and has undergone an external audit.
18. **Implement Comprehensive Monitoring & Alerting:**
    *   **Description:** Set up robust logging, monitoring, and alerting specifically for attestation failures, TEE health, and potential security anomalies.
    *   **Validation:** System operators are alerted immediately to any integrity issues.
19. **Perform End-to-End Security Audit:**
    *   **Description:** Conduct a final comprehensive security audit focusing on the entire hybrid architecture, the interface between the open-source Privacy Core and the closed-source Core Bot, and the LLM integration points.
    *   **Validation:** Audit report identifies and addresses any remaining critical vulnerabilities.
20. **Deployment and CI/CD for TEE:**
    *   **Description:** Set up secure CI/CD pipelines to build and deploy the TEE-bound components and the Core Bot, ensuring no plaintext keys or sensitive data are exposed during the deployment process.
    *   **Validation:** Automated, secure deployment to production TEE environment is functional.

## Phase 5: Advanced Features and Refinement

21. **Robust Long-Term Memory (RAG and Personalization):**
    *   **Description:** Implement advanced RAG capabilities and user profile management in the Persistence Layer to provide human-like memory and personalization.
    *   **Validation:** Bot demonstrates effective recall of past information and personalized interactions.
22. **Expand `signal-client` Utilization:**
    *   **Description:** Implement handling for various Signal message types (media, groups, reactions) and advanced client features.
    *   **Validation:** Bot correctly processes and responds to different Signal message types.
23. **Commercial Features:**
    *   **Description:** Implement features related to user subscriptions, premium access, or custom integrations.
    *   **Validation:** Commercial features are functional and secure.
24. **Continuous Improvement:**
    *   **Description:** Establish processes for ongoing security reviews, code updates, and feature enhancements.
    *   **Validation:** Regular updates are deployed securely and efficiently.