---
change-id: signal-assistant-enclave-architecture
---
# Proposal: Enclave-Centered Architecture for Signal Assistant Bot

This proposal outlines an enclave-centered architecture for a privacy-focused commercial Signal assistant bot. The core objective is to minimize data exposure to host environments and governmental tracking by leveraging Trusted Execution Environments (TEEs). This document will detail the architectural design, threat model, data flows, identity management, key management, logging, storage policies, and implications for law enforcement, providing an implementation-ready guide for senior engineers. The primary goal is to build an assistant that can interact with users via Signal, with its core logic within a secure, verifiable enclave that securely interacts with external Large Language Model (LLM) APIs.

The detailed architecture document is provided in `design.md`.
