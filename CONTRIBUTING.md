# Contributing to AI Failure Museum (AFM)

Thank you for your interest in contributing to the AI Failure Museum!

AFM is an open-source registry and reproduction engine designed to capture and evaluate AI coding agent failures in a structured, reproducible manner.

---

## Non-Negotiable Engineering Rules

1. **Never fabricate failure reports**: All submissions must come from authentic agent sessions or be explicitly labeled as synthetic test doubles.
2. **Never expose private credentials**: Scrub all API keys, access tokens, SSH keys, passwords, and private company source code from prompts, context, and logs.
3. **No untrusted execution**: Never execute untrusted code from external submissions directly on your host machine.
4. **Use Docker for reproduction**: Reproduction scripts must run in isolated container environments with network disabled by default.
5. **Deterministic assertions**: Attach programmatic assertions to verify when a failure has been recreated.

---

## Submitting a New Failure Case

### 1. Scaffold the Case Structure
Run the AFM CLI wizard:

```bash
afm new --id AFM-0002 --title "Descriptive title of failure"
```

If you are contributing a synthetic case for framework testing:
```bash
afm new --id SYN-0004 --title "Synthetic case title" --synthetic
```

### 2. Fill Out Case Metadata
Edit the generated `case.yaml` file:
- **`prompt`**: The exact or summarized prompt sent to the agent.
- **`behavior.expected`**: What the agent should have done.
- **`behavior.observed`**: What flawed behavior actually took place.
- **`reproduction`**: Entrypoint script and assertion rules.
- **`evidence`**: Terminal logs, patches, or diffs in `evidence/`.

### 3. Run Validation
Ensure your case adheres strictly to the published schema:

```bash
afm validate AFM-0002
```

### 4. Run Pytest
Run the test suite to verify no regressions were introduced:

```bash
pytest tests/
```

### 5. Open a Pull Request
1. Branch from `master` or `main`: `git checkout -b case/afm-0002`.
2. Commit your case files: `git commit -m "feat(cases): add AFM-0002"`.
3. Open a Pull Request against the upstream repository.

---

## Continuous Integration & Security Policy

To protect maintainers and infrastructure:
- Pull requests from external forks are treated as untrusted.
- CI workflows only run static linting, schema validation (`afm validate`), and unit tests on trusted framework code.
- Reproduction scripts from pull requests are **never** executed automatically in privileged CI runners.
