# AI Failure Museum (AFM) — Implementation Plan

## Executive Summary
The **AI Failure Museum (AFM)** is a production-quality, open-source AI agent failure registry and reproduction engine. It turns real and synthetic AI agent failures into structured, reproducible, and evaluatable cases with strong security guardrails, an extensible taxonomy, a rich CLI, a pluggable evaluation adapter architecture, and an editorial web dashboard.

---

## Architecture & Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Language & Runtime** | Python 3.11+ (Python 3.13 tested) | Modern typing, standard tooling |
| **Package Management** | `pyproject.toml` (PEP 621 / hatchling) | Standardized Python packaging |
| **Data Validation & Schemas** | Pydantic v2 & JSON Schema | Type safety, serialization, automatic JSON Schema generation |
| **CLI Framework** | Typer & Rich | Intuitive subcommands, formatted tables, spinners, colored output |
| **YAML Engine** | PyYAML / ruamel.yaml | Human-readable case definitions |
| **Testing** | pytest, pytest-cov | Unit and integration test coverage |
| **Reproduction Engine** | Docker isolation + subprocess timeout | Sandboxed reproduction with CPU, memory, and network constraints |
| **Web Dashboard** | Next.js 15 (App Router), TypeScript, Tailwind CSS | High performance, static export support, responsive editorial theme |
| **Design System** | Minimal Editorial Dark (`#0B0D10`, `#15191F`, `#F5F5F5`, `#9299A4`, `#FF5A45`) | Focus on technical readability and typography |

---

## Milestones & Status

### Milestone 1 — Architecture & Plan
- [x] Inspect workspace and system environment (Python 3.13.2, Node.js v24.18.0, npm 11.16.0, Git).
- [x] Document project architecture, security boundaries, and data models.
- [x] Define JSON Schema for failure cases (`schemas/failure-case.schema.json`).
- [x] Initialize repository structure and configuration files (`pyproject.toml`).
- [x] Verify acceptance criteria for Milestone 1.

### Milestone 2 — Functional Core
- [x] Implement core data models (`models.py`) with Pydantic v2.
- [x] Implement failure validation engine (`validation.py`).
- [x] Implement registry loader and query engine (`registry.py`).
- [x] Implement security utilities and secret redactor (`security.py`).
- [x] Implement CLI commands (`afm list`, `afm show`, `afm validate`, `afm doctor`, `afm new`).
- [x] Create at least 3 rich synthetic failure cases (`SYN-0001`, `SYN-0002`, `SYN-0003`) under `examples/synthetic/`.
- [x] Build comprehensive unit test suite in `tests/` covering models, validation, registry, and CLI.
- [x] Verify acceptance criteria for Milestone 2.

### Milestone 3 — Reproduction Engine
- [x] Implement Docker-based isolated runner (`runner.py`) with memory/CPU/timeout limits.
- [x] Implement strict host-execution prevention when Docker is absent or unsafe.
- [x] Implement assertion engine (exit code, stdout regex, stderr checks, file checks).
- [x] Implement `afm reproduce` command with detailed diagnostic output.
- [x] Add unit and mock integration tests for reproduction engine.
- [x] Verify acceptance criteria for Milestone 3.

### Milestone 4 — Evaluation System & Reporting
- [x] Implement pluggable agent evaluation adapter interface (`adapters/base.py`).
- [x] Implement mock evaluation adapter (`adapters/mock.py`).
- [x] Implement evaluation orchestration engine (`evaluation.py`).
- [x] Implement structured report generator (`reporting.py`) for Markdown and JSON output.
- [x] Implement CLI command `afm evaluate` and `afm report`.
- [x] Add tests for evaluation flow and report formatting.
- [x] Verify acceptance criteria for Milestone 4.

### Milestone 5 — Web Dashboard
- [x] Initialize Next.js TypeScript Tailwind app under `web/`.
- [x] Implement brand theme (`#0B0D10`, `#15191F`, `#F5F5F5`, `#9299A4`, `#FF5A45`).
- [x] Implement static registry data exporter (`scripts/export_registry.py`).
- [x] Build Homepage with registry metrics, hero, and featured cases.
- [x] Build Failure Explorer (`/failures`) with search, category filter, reproducibility filter, status filter.
- [x] Build Failure Details page (`/failures/[id]`) with technical overview, task, behavior, reproduction, and evidence.
- [x] Build Contribution page (`/contribute`) and Documentation page (`/docs`).
- [x] Verify web dashboard builds cleanly without runtime errors (`next build` SSG verified).

### Milestone 6 — Open-Source Infrastructure & Documentation
- [x] Create `README.md`, `LICENSE` (Apache 2.0), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `ROADMAP.md`.
- [x] Add technical architecture documentation in `docs/architecture.md`.
- [x] Create GitHub Actions workflows for PR validation and test suite (`.github/workflows/`).
- [x] Create GitHub Issue and PR templates (`.github/ISSUE_TEMPLATE/`, `PULL_REQUEST_TEMPLATE.md`).
- [x] Verify acceptance criteria for Milestone 6.

### Milestone 7 — Quality Assurance & Verification
- [x] Run full test suite with coverage report (43 tests passed, 77% coverage).
- [x] Perform end-to-end CLI workflow tests (`list`, `show`, `validate`, `doctor`, `evaluate`, `report`, `reproduce`).
- [x] Verify clean package installation and CLI entrypoint (`pip install -e .`).
- [x] Audit security protections (secret redactor, path traversal, Docker isolation policies).
- [x] Finalize report with implemented features, test results, and next priorities.

---

## Known Environment Constraints & Security Posture
1. **Docker Host Availability**: Docker is not installed or running in the current host environment. The reproduction engine is strictly designed to detect this and fail safely with informative messaging rather than falling back to dangerous host execution.
2. **PowerShell Script Policy**: `npm.ps1` is blocked by default Windows execution policy; all node commands must be invoked via `npm.cmd` or `npx.cmd`.
3. **No Unrestricted Execution**: No external code from failure definitions will be executed outside controlled container environments.
