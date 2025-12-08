# Signal Assistant

A privacy-focused AI assistant for Signal, designed with a secure "Privacy Core" architecture.

## Architecture

- **Signal Adapter**: Handles raw I/O with `signal-client`.
- **Privacy Core**: Trusted boundary for decryption and PII sanitization.
- **Bot Orchestrator**: AI logic and state management.
- **Storage**: Persistence layer.

## Development

```bash
poetry install
poetry run signal-assistant --help
```
