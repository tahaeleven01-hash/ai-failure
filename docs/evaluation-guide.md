# Agent Evaluation Guide

## Overview

While reproduction answers whether we can *recreate* the original bug, evaluation answers:
> **"Can an AI coding agent successfully complete the original task without repeating the failure?"**

---

## Evaluation Workflow

1. **Isolation**: A clean, temporary working directory is spawned for each evaluation run.
2. **Task Prompting**: The agent adapter receives the original task prompt and repository context.
3. **Execution Monitoring**: The agent runs up to a configurable timeout (default 120s).
4. **State Diffing**: AFM captures all created or modified files and generates unified diffs.
5. **Verification**: AFM executes the case's verification method (`test_runner`). If the test suite passes (exit code 0) and the original failure criteria are resolved, the evaluation is marked as `RESOLVED`.
6. **Secret Sanitization**: All agent logs and test outputs are scrubbed for API tokens before recording.

---

## Pluggable Adapters

AFM provides an extensible adapter architecture in `afm.adapters`.

### Built-in Mock Adapter
The `mock` adapter allows testing evaluation flows deterministically without external API costs or model calls:

```bash
afm evaluate SYN-0001 --adapter mock
```

### Implementing a Custom Adapter
To create an adapter for a coding agent CLI:

```python
from pathlib import Path
from afm.adapters.base import BaseAdapter, AgentExecutionOutput

class MyAgentAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "my-agent"

    def run_agent(self, task_prompt: str, context: str, workspace_dir: Path, timeout_seconds: int):
        # Invoke agent CLI inside workspace_dir
        ...
```
