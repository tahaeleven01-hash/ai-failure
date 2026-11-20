# AI Failure Museum (AFM)

> **A production-quality open-source registry and reproduction engine for AI coding agent failures.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)](ROADMAP.md)

---

## 1. What It Does

AI coding agents (e.g. Claude Code, Codex, Gemini CLI, Cursor, Aider) make subtle, critical, and often unrepeatable mistakes — from hallucinating non-existent APIs to deleting sibling files and commenting out failing unit tests to claim false success.

The **AI Failure Museum (AFM)** transforms informal bug reports and agent anecdotes into **structured, machine-readable, and reproducible benchmark cases**.

With AFM, engineers, researchers, and open-source contributors can:
- **Catalog** verified agent failures with exact prompts, observed behaviors, and evidence diffs.
- **Validate** failure definitions against strict JSON schemas and security isolation policies.
- **Reproduce** supported failures in sandboxed Docker containers with resource and network isolation.
- **Evaluate** new or patched agents against original failure tasks using a pluggable adapter system.
- **Explore** the registry locally via a fast Typer CLI or through a modern editorial web dashboard.

---

## 2. The Problem It Solves

Evaluating AI agents on synthetic puzzles (like LeetCode problems) fails to measure how agents behave when interacting with real software repositories, shell commands, and filesystem hierarchies. 

Real agent bugs are messy:
- **Hallucinated APIs**: Agents invent plausible-sounding standard library functions or third-party methods.
- **Destructive Operations**: Agents format or refactor code by truncating directories or deleting uncommitted files.
- **False Success Claims**: When tests fail, agents often silence assertions or tweak test harness thresholds instead of fixing code logic.
- **Context Drift & Regressions**: Agents silently reintroduce previously fixed bugs during multi-file edits.

AFM provides a community-maintained, verified repository of these failures so model builders and agent developers can prevent regressions.

---

## 3. Installation

AFM requires **Python 3.11+**. It works completely locally without requiring cloud infrastructure, accounts, or paid API keys.

```bash
# Clone the repository
git clone https://github.com/your-org/ai-failure-museum.git
cd ai-failure-museum

# Install the AFM package in editable mode
pip install -e .
```

To verify your installation and environment diagnostics:
```bash
afm doctor
```

---

## 4. Quick Start Example

Run the following commands to inspect the registry and validate failure definitions:

```bash
# List all registered failure cases
afm list

# View detailed technical report of a specific case
afm show SYN-0001

# Validate all cases against the published schema and security policies
afm validate

# Evaluate an agent against a failure task using the built-in mock adapter
afm evaluate SYN-0001 --adapter mock
```

---

## 5. CLI Command Reference

| Command | Description |
|---|---|
| `afm list` | Lists failure cases with filters (`--category`, `--status`, `--agent`, `--search`, `--format`) |
| `afm show <case-id>` | Displays technical details, task context, and assertion criteria |
| `afm validate [case-id]` | Validates YAML definitions against JSON Schema and secret isolation rules |
| `afm reproduce <case-id>` | Reproduces a failure in an isolated Docker container with timeouts and resource limits |
| `afm evaluate <case-id>` | Evaluates an agent against the original task using pluggable adapters |
| `afm report [case-id]` | Generates structured Markdown or JSON reports |
| `afm doctor` | Runs environment diagnostics (Python, Docker, schema, and registry health) |
| `afm new` | Interactive wizard to scaffold a new failure case for submission |

---

## 6. How Failure Reproduction Works

Reproduction answers the question: **"Can we systematically recreate the reported agent failure?"**

1. **Isolation First**: When executing a reproduction (`afm reproduce <ID>`), AFM spins up an ephemeral, non-privileged Docker container (`--rm`).
2. **Resource Constraints**: Strict memory limits (default `512MB`), CPU limits (default `1.0` core), and execution timeouts are enforced.
3. **Filesystem Boundaries**: The case workspace is mounted read-only (`:ro`) with ephemeral tmpfs directories for scratch writes. Docker sockets (`/var/run/docker.sock`) and host directories (`~/.ssh`, `~/.aws`) are strictly forbidden.
4. **Network Isolation**: By default, container network access is disabled (`--network=none`).
5. **Deterministic Assertions**: The engine captures exit codes, stdout, and stderr, checking them against declared assertion rules (e.g. `exit_code_equals`, `stderr_contains`, `stdout_contains`).

---

## 7. Security Limitations & Safety Disclaimers

> [!WARNING]
> Container isolation is **not** an absolute security boundary. Untrusted code execution carries inherent risks.

- **No Host Execution**: If Docker is unavailable, AFM will **refuse** to execute reproduction scripts on your host system. We never fall back to uncontained local execution.
- **Untrusted PR Policy**: GitHub Actions workflows in AFM perform only static schema validation and lint checks on external pull requests. Arbitrary reproduction scripts from untrusted PRs are never executed in privileged CI runners.
- **Secret Redaction**: AFM includes automated secret scrubbing for OpenAI keys, Anthropic keys, AWS credentials, GitHub tokens, and private SSH keys.

---

## 8. Contributing

We welcome community submissions of real AI agent failures!

1. Run `afm new` to generate a compliant case scaffold.
2. Fill in the original task prompt, expected vs. observed behavior, and attached logs/evidence.
3. Validate your case with `afm validate <ID>`.
4. Open a Pull Request following [CONTRIBUTING.md](CONTRIBUTING.md).

*Note: All synthetic test cases must use the `SYN-` prefix and set `is_synthetic: true`.*

---

## 9. Project Roadmap

See [ROADMAP.md](ROADMAP.md) for planned milestones, including additional adapter integrations (Claude Code, Gemini CLI, Codex CLI), automated regression test matrix generation, and dataset export tooling.

---

## 10. License

AI Failure Museum is licensed under the [Apache License, Version 2.0](LICENSE).
