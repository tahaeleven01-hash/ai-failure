# Technical Architecture Document

## 1. System Overview

The **AI Failure Museum (AFM)** is architected as an offline-first, local-capable failure benchmark registry and reproduction framework. The system operates entirely without mandatory cloud connections, paid APIs, or third-party database services.

```text
                  +-----------------------------------+
                  |         AFM CLI (Typer)           |
                  +-----------------+-----------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
    +---------------+       +---------------+       +---------------+
    | Failure       |       | Reproduction  |       | Evaluation    |
    | Registry      |       | Runner        |       | Engine        |
    +-------+-------+       +-------+-------+       +-------+-------+
            |                       |                       |
            v                       v                       v
    [ Pydantic &    ]       [ Docker Engine ]       [ Pluggable     ]
    [ JSON Schema   ]       [ Sandboxing    ]       [ Adapters      ]
            |                       |                       |
            +-----------------------+-----------------------+
                                    |
                                    v
                  +-----------------------------------+
                  | Next.js Editorial Web Dashboard   |
                  +-----------------------------------+
```

---

## 2. Core Subsystems

### 2.1 Data Models & Validation (`afm.models`, `afm.validation`)
- **Pydantic v2 Core**: All entities (`FailureCase`, `AgentMetadata`, `TaskDefinition`, `ReproductionProcedure`, etc.) are modeled with strict schemas. Extra fields are rejected (`extra="forbid"`) to catch typo mistakes early.
- **Prefix Guardrails**: Cases prefixed with `SYN-` are enforced to be `is_synthetic: true`; cases prefixed with `AFM-` are enforced to be real cases (`is_synthetic: false`).
- **Secret Redaction**: Inputs and captured logs are scrubbed via precompiled regular expressions in `afm.security` to prevent accidental credential leakage.

### 2.2 In-Memory Registry (`afm.registry`)
- **Filesystem Discovery**: Scans `failures/` and `examples/synthetic/` for `.yaml` definitions.
- **Duplicate ID Detection**: Validates that all IDs are unique across the repository.
- **In-Memory Querying**: Supports real-time filtering by category, status, agent, and free-text queries without a database engine.
- **Static Export**: Dumps structured JSON to `web/data/registry.json` for consumption by the web dashboard.

### 2.3 Reproduction Runner (`afm.runner`)
- **Strict Isolation**: Runs reproduction procedures inside ephemeral Docker containers (`--rm`).
- **Resource Caps**: Quotas default to 512MB RAM, 1.0 CPU, and strict timeout deadlines.
- **Safe Fallback**: If Docker is not installed or unreachable, AFM strictly refuses to execute scripts on the host to avoid untrusted code execution.

### 2.4 Agent Evaluation Engine (`afm.evaluation`)
- **Separation of Concerns**: Reproduction tests *can we recreate the failure*; evaluation tests *can an agent resolve the task*.
- **Adapter Interface (`BaseAdapter`)**: Encapsulates agent execution. Includes a built-in `MockAdapter` for deterministic CI testing, and prepares for future integrations (`Claude Code`, `Gemini CLI`, `Codex`).
- **Clean Workspace**: Spawns ephemeral temporary directories to measure file changes, diffs, and verification test outputs.

### 2.5 Web Dashboard (`web/`)
- Built with **Next.js 14**, **TypeScript**, and **Tailwind CSS**.
- Pure static compilation (`next build` generates 100% static HTML/JS).
- Follows the technical editorial palette: `#0B0D10` (background), `#15191F` (surface), `#F5F5F5` (text), and `#FF5A45` (accent).

---

## 3. Major Architectural Decisions & Trade-Offs

| Decision | Rationale | Trade-Off |
|---|---|---|
| **YAML for Case Definitions** | Human-readable, diff-friendly in Git PRs | Slower parsing than binary formats, requires safe loader |
| **Pydantic v2 & JSON Schema** | Fast, type-safe, auto-generates standard schemas | Pydantic v2 dependency required |
| **Docker-Only Reproduction** | Strict containment boundary, non-root user, memory limits | Requires Docker for live reproduction; disabled on bare-metal systems |
| **Static Next.js Build** | Fast, zero runtime database, hostable on any static server | Re-build needed when new cases are committed |
| **Mock Adapter in Core** | Allows testing evaluation workflows without external API keys | Real model evaluations require explicit user configuration |
