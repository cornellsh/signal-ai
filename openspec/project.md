# Project Context

## Purpose
The project implements a privacy-preserving Signal Virtual Assistant that:
- Acts as a Signal contact users can message like a normal chat.
- Uses a Trusted Execution Environment (Enclave/TEE) as the trust anchor for all sensitive processing.
- Orchestrates external LLMs and tools while enforcing strict privacy, key-management, and law-enforcement constraints.
- Treats `docs/signal_assistant_core.md` and `docs/privacy_architecture.md` as canonical specifications for behavior and invariants.

Goals:
- End-to-end design where plaintext content and key material only exist inside the Enclave.
- Minimal, pseudonymized host visibility (Host “blindness” by design).
- Clear, testable invariants and enforcement mechanisms derived from the specs.
- Architecture suitable for production deployment under realistic legal and threat models.

## Tech Stack
- Primary language: Python (backend + enclave application logic).
- Runtime: Linux (host), TEE platform abstraction (e.g., SGX/SEV-SNP-like model; actual TEE binding pluggable).
- Messaging: Signal protocol (via Signal bot / integration layer).
- LLM: External LLM APIs (HTTP/JSON over TLS, keyed by enclave-held credentials).
- Persistence: Host-side storage (DB or filesystem) containing only enclave-encrypted blobs and non-sensitive logs.
- Tooling:
  - OpenSpec for architecture/spec/task definitions.
  - Pytest or similar for tests.
  - Pre-commit hooks, static analysis/linters.

## Project Conventions

### Code Style
- Python: PEP 8 as baseline, with:
  - Type hints required for public functions.
  - `black`/`ruff`-style formatting (deterministic, no bikeshedding).
- Naming:
  - `snake_case` for functions/variables.
  - `CamelCase` for classes.
  - Config/constant identifiers in `UPPER_SNAKE_CASE`.
- Modules separated by responsibility:
  - `enclave/` (Signal stack, KMS, prompt pipeline, sanitizer, LE policy).
  - `host/` (Signal integration, orchestration, monitoring).
- No logging of raw user input or Signal IDs anywhere; all such code paths must go through dedicated logging helpers enforcing the schema.

### Architecture Patterns
- Strict Host / Enclave split:
  - Host is untrusted orchestrator and resource provider.
  - Enclave is the only place where plaintext content and keys exist.
- “Spec-first” development:
  - All new features must map to requirements in the core and privacy specs.
  - Invariants (section 10 in core spec) are treated as non-negotiable constraints.
- Clear boundaries:
  - Enclave exposes a narrow, explicit interface to Host (IPC/transport + attestation).
  - Prompt pipeline is centralized (single path to external LLMs).
  - Logging goes through a central API with schema enforcement.
- No “convenience bypasses”:
  - No debug-only paths that bypass sanitization, attestation gating, or logging rules.

### Testing Strategy
- Unit tests:
  - Enclave components: KMS, transport, prompt builder, PII sanitization, LE policy.
  - Host components: Signal integration, IPC, logging wrappers.
- Integration tests:
  - Round-trip Signal message → enclave → LLM stub → response, verifying:
    - No plaintext or Signal IDs appear in host-visible logs or storage.
    - Final assembled prompts are sanitized before leaving enclave.
  - Attestation gating and key release behavior (positive and negative paths).
  - User-deletion path: mapping + long-term memory + host metadata deletion.
- Property / invariant tests:
  - Tests asserting key invariants (e.g., “no plaintext at rest”, “no Signal_ID in logs”) using synthetic inputs and corpus scans.
- Tooling:
  - Static checks/linters verifying:
    - No direct logging of message text or Signal IDs.
    - No external LLM calls outside the centralized prompt pipeline.

### Git Workflow
- Branching:
  - `main` is protected and always in a releasable state.
  - Feature branches: `feature/<short-description>`.
  - Fix branches: `fix/<short-description>`.
- Commits:
  - Small, logically-scoped commits with imperative messages (e.g., `enforce logging schema in host logger`).
  - References to spec sections when relevant (e.g., `core-10.4`, `privacy-9.1.1`).
- Reviews:
  - All PRs require review.
  - PR template should include:
    - Which spec sections / invariants are touched.
    - How tests enforce new/changed behavior.

## Domain Context
- Signal Assistant is a bot within the Signal ecosystem, not a general-purpose SaaS chat app.
- Threat model:
  - Host OS, hypervisor, and operator are potentially malicious.
  - Enclave + attestation provide integrity and confidentiality guarantees.
- Identity model:
  - Signal user identities (phone/UUID) are bound to `internal_user_id` inside the enclave.
  - Host only sees `internal_user_id` in persisted data/logs.
- Privacy posture:
  - No persistent plaintext conversation content.
  - External LLMs only see PII-sanitized prompts.
  - Law enforcement access is technically constrained: no retrospective plaintext, no covert wiretapping without attestation changes and public detectability.
- Long-term memory:
  - Only redacted summaries/embeddings and non-PII metadata, associated with `internal_user_id`, under strict retention.

## Important Constraints
- Privacy and security:
  - Invariants in `docs/signal_assistant_core.md` and `docs/privacy_architecture.md` are binding.
  - No host-side plaintext content or key material.
- Legal / LE:
  - Architecture must support the documented law-enforcement posture (limited metadata, no historical plaintext).
- Performance:
  - Latency and throughput targets exist but are secondary to privacy/security invariants.
- Operational:
  - No “hidden” debug features that weaken guarantees.
  - Attestation must gate key access; no manual overrides in production.

## External Dependencies
- Signal servers / APIs for message delivery and bot identity.
- TEE/attestation platform (e.g., cloud vendor’s SGX/SEV-like offering or abstraction).
- External LLM APIs (OpenAI/Anthropic/etc.), accessed only via enclave-held credentials and sanitized prompts.
- Optional:
  - Metrics/monitoring stack (Prometheus-like, log aggregation), receiving only anonymized/aggregated telemetry.
