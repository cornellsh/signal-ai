# Signal Assistant Spec Enforcement Phase

This directory contains the proposal, design, tasks, and detailed spec deltas for implementing a comprehensive spec-enforcement phase for the Signal Assistant.

The goal of this phase is to align the implementation, tests, and tooling with the canonical `Signal Assistant Core Specification` and `Signal Assistant Enclave Privacy Architecture Document`, and to introduce concrete, testable mechanisms to prevent architectural and implementation drift over time.

Key areas addressed include:
*   Enclave-only plaintext and key handling.
*   Host blindness and logging constraints.
*   Identity mapping, deletion, and Law Enforcement (LE) access posture.
*   LLM prompt construction, sanitization, and external LLM interaction.

Detailed rationale, enforcement mechanisms, and a phased execution plan can be found in `proposal.md`, `design.md`, and `tasks.md` respectively. Specific requirements and modifications to existing specifications are detailed in the `specs/` subdirectory.