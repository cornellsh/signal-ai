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

## Simulation Mode

For local development and testing, the Signal Assistant can be run in a simulation mode that bypasses the need for a real Signal account, an SGX enclave, or a deployed Signal Service. This mode allows developers to interact directly with the bot via a command-line interface.

**Key Features of Simulation Mode:**
-   **Local Execution**: Both the Host and Enclave components run in a single process on your local machine.
-   **Mocked Signal Service**: An in-memory WebSocket server emulates the external Signal Service, accepting messages from your CLI and displaying bot responses.
-   **Mocked Cryptography**: The internal Signal encryption/decryption is replaced with transparent JSON handling, allowing you to see message payloads.
-   **Ephemeral State**: A transient in-memory database is used, ensuring each simulation run starts with a clean slate.

**How to Use Simulation Mode:**

1.  Ensure you have all dependencies installed:
    ```bash
    poetry install
    ```
2.  Start the simulation:
    ```bash
    poetry run signal-assistant simulate
    ```
3.  Type your message at the `>` prompt and press Enter. The bot's response will be displayed in the console.
4.  Type `/exit` to quit the simulation.
