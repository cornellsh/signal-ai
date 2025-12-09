# Design: Operational Governance Architecture

## 1. Architectural Overview
This design introduces a control plane for the "Supply Chain" of the Signal Assistant Enclave. It bridges the gap between a compiled binary and a running, trusted service.

The architecture consists of three main components:
1.  **The Registry:** A tamper-evident source of truth (e.g., a signed JSON/YAML file in the repo, or a transparency log) listing all valid Enclave Measurements (MRENCLAVE) and their metadata (version, git commit, status).
2.  **The Gatekeeper (Host/Orchestrator):** A component in the Host that checks the Enclave's attestation report against the Registry before provisioning keys or opening network ports.
3.  **The Self-Aware Enclave:** Logic within the Enclave that validates its own configuration against its compiled-in "Environment Identity" (e.g., preventing Dev flags in a Release build).

## 2. Data Flows

### 2.1 Release & Registration Flow
1.  **CI Build:** Compiles the Enclave code from a specific Git Commit.
2.  **Measurement:** The build process generates the `MRENCLAVE` (measurement hash).
3.  **Verification:** Automated tests verify the build passes all spec-enforcement suites.
4.  **Registration:** A authorized maintainer "signs off" on the build, adding `{ "measurement": "...", "version": "1.2.0", "status": "active" }` to the `measurement_registry.json`.
5.  **Publish:** The updated registry is committed and deployed.

### 2.2 Startup & Attestation Flow
1.  **Enclave Start:** The Host launches the Enclave.
2.  **Self-Check:** The Enclave initializes. It checks its compiled-in build type (`RELEASE` vs `DEBUG`). If `RELEASE`, it asserts that `MOCK_ATTESTATION` is false and `LOG_LEVEL` is `INFO` (not DEBUG). If check fails, it `panic()`s.
3.  **Attestation Generation:** The Enclave generates a Remote Attestation Report including its `MRENCLAVE`.
4.  **Registry Lookup:** The Host (or Key Provisioning Service) fetches the current `measurement_registry.json`.
5.  **Validation:**
    -   Is the `MRENCLAVE` present in the registry?
    -   Is its status `active`?
    -   (Optional) Is it the *latest* version?
6.  **Provisioning:** If valid, the Host/KMS releases the sealed keys (ESSK, SPK) to the Enclave. If invalid, the process aborts.

### 2.3 Client Verification Flow
1.  **Handshake:** A Signal Client (or Auditor) connects to the Assistant.
2.  **Challenge:** The Client requests an Attestation Quote.
3.  **Response:** The Assistant returns the Quote (signed by the TEE hardware).
4.  **Verification:** The Client verifies the signature chain and extracts the `MRENCLAVE`.
5.  **Registry Check:** The Client checks the extracted `MRENCLAVE` against the public `measurement_registry.json`.
6.  **Trust:** If the measurement is found and active, the Client proceeds. Otherwise, it warns the user or terminates the connection.

## 3. Detailed Component Design

### 3.1 Environment Taxonomy
We define strict build profiles:

| Profile | Optimization | Logging | Mock Attest | Allowed Env |
| :--- | :--- | :--- | :--- | :--- |
| `DEV` | O0/O1 | DEBUG | Allowed | Local, CI |
| `TEST` | O2 | INFO | Allowed | CI, Test-Cluster |
| `STAGE` | O2/O3 | INFO | **FORBIDDEN** | Staging |
| `PROD` | O3 | WARN/INFO | **FORBIDDEN** | Production |

**Enforcement:**
-   The `PROD` profile MUST be compiled with preprocessor directives (e.g., `#define PRODUCTION`) that physically exclude code paths for mock attestation or unsafe debug commands.
-   The Registry entry for a measurement SHOULD include the target profile.

### 3.2 The Measurement Registry Schema
```json
{
  "schema_version": "1.0",
  "measurements": [
    {
      "mrenclave": "sha256:...",
      "version": "1.0.1",
      "git_commit": "a1b2c3d...",
      "build_timestamp": "2025-10-27T10:00:00Z",
      "profile": "PROD",
      "status": "active", // active, deprecated, revoked
      "revocation_reason": null
    }
  ],
  "signatures": [ ... ]
}
```

## 4. Trade-offs & Decisions

### 4.1 Registry Storage
-   *Option A: Blockchain/Transparency Log.* High integrity, high complexity.
-   *Option B: Central Database.* Low complexity, single point of failure/trust.
-   *Option C: Signed File in Repo.* Good balance. The repo is the source of truth for code, so it fits to be the source of truth for measurements. We choose **Option C** for this phase.

### 4.2 Fail-Open vs Fail-Closed
-   We strictly choose **Fail-Closed**. If the registry is unreachable or the measurement is missing, the system MUST NOT start. Availability is secondary to preventing unauthorized code execution.

## 5. Non-Goals
-   This design does not protect against physical side-channel attacks on the TEE hardware itself (e.g., Hertzbleed).
-   It does not automate the human decision to "approve" a release, only the enforcement of that decision.
