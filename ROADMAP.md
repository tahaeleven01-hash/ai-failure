# AI Failure Museum (AFM) — Roadmap

## Phase 1: Core Registry & Reproduction Engine (Completed)
- [x] Pydantic v2 data models for failure cases, taxonomy, and assertion rules.
- [x] Machine-readable JSON Schema export (`schemas/failure-case.schema.json`).
- [x] Filesystem discovery engine with duplicate ID prevention.
- [x] Secret sanitization and path traversal defenses.
- [x] Docker isolation engine with resource boundaries and timeout protection.
- [x] Initial suite of synthetic failure cases (`SYN-0001`, `SYN-0002`, `SYN-0003`).

## Phase 2: Web Dashboard & CLI Tools (Completed)
- [x] Typer CLI (`list`, `show`, `validate`, `reproduce`, `evaluate`, `report`, `doctor`, `new`).
- [x] Next.js 14 editorial web dashboard with dark technical visual identity.
- [x] Searchable Failure Explorer with multi-dimensional filtering.
- [x] Comprehensive failure detail view with behavior comparison and assertions.
- [x] Static registry data export pipeline.

## Phase 3: Extended Agent Adapters (Near-Term)
- [ ] Direct CLI adapter for `claude-code`.
- [ ] Direct CLI adapter for `gemini-cli`.
- [ ] Direct CLI adapter for `codex-cli`.
- [ ] Standardized diff parser and patch application engine.

## Phase 4: Automated Benchmarking & Matrix Evaluation (Mid-Term)
- [ ] Multi-agent comparative evaluation runs (`afm evaluate --all-adapters`).
- [ ] Regression tracking across agent model versions (e.g. Sonnet 3.5 vs. Sonnet 3.7 vs. Gemini 2.5).
- [ ] Markdown benchmark matrix generator with win/loss/regression metrics.

## Phase 5: Ecosystem & Dataset Publishing (Long-Term)
- [ ] Automated parquet / arrow dataset export for Hugging Face datasets.
- [ ] Integration with GitHub Actions for automated agent regression gates.
- [ ] Community verification badge program for verified reproducible cases.
