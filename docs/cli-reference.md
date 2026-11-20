# CLI Reference

The `afm` command-line interface provides tools for exploring, validating, reproducing, and evaluating AI agent failure cases.

```bash
afm [OPTIONS] COMMAND [ARGS]...
```

---

## Commands

### `afm list`
List registered failure cases.

**Options:**
- `-c, --category <TEXT>`: Filter by category (e.g. `hallucinated-api`).
- `-s, --status <TEXT>`: Filter by case status (`reproducible`, `validated`, etc.).
- `-a, --agent <TEXT>`: Filter by agent name.
- `-q, --search <TEXT>`: Free text search across title, ID, and description.
- `--synthetic / --no-synthetic`: Filter synthetic test cases.
- `-f, --format <table|json>`: Output format (default: `table`).

### `afm show <case-id>`
Display detailed technical overview of a specific failure case.

**Options:**
- `-f, --format <text|json>`: Output format.

### `afm validate [case-id]`
Validate case definitions against the published JSON schema and security isolation rules.

**Options:**
- `--strict / --no-strict`: When strict (default), flags exposed secrets and missing references.

### `afm reproduce <case-id>`
Execute the reproduction procedure inside an isolated Docker container.

**Options:**
- `-t, --timeout <INTEGER>`: Override execution timeout in seconds.
- `--allow-network`: Enable network mode (`bridge`) if the case requires it.

### `afm evaluate <case-id>`
Evaluate whether an AI coding agent can resolve the task in the case.

**Options:**
- `-a, --adapter <TEXT>`: Agent adapter to use (`mock`, etc.).
- `-t, --timeout <INTEGER>`: Maximum timeout in seconds (default: 120).
- `-f, --format <table|json>`: Output format.

### `afm report [case-id]`
Generate structured Markdown or JSON report for a case or whole registry.

**Options:**
- `-f, --format <markdown|json>`: Report format (default: `markdown`).
- `-o, --output <PATH>`: Write output to a file.

### `afm doctor`
Inspect system diagnostics: Python version, Docker availability, schema integrity, and registry health.

### `afm new`
Scaffold a new failure case using interactive prompts.

**Options:**
- `--id <TEXT>`: Case ID (e.g. `AFM-0002` or `SYN-0004`).
- `--title <TEXT>`: Case title.
- `--category <TEXT>`: Primary failure category.
- `--agent <TEXT>`: Name of the agent.
- `--synthetic`: Mark as synthetic test double.
