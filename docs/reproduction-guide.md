# Failure Reproduction Guide

## Overview

Reproduction in AFM answers the question:
> **"Can we systematically and reliably recreate the reported AI agent failure?"**

Reproducing agent failures is essential to prevent regressions in AI coding agents and to provide concrete benchmark targets for model developers.

---

## The Containment Sandbox

Reproduction code submitted by external parties is inherently untrusted. AFM enforces strict isolation:

1. **Docker Requirement**: Live execution requires Docker. If Docker is unavailable, the runner terminates safely with `unsupported-environment`.
2. **Ephemeral Containers**: Launched with `--rm` so containers are deleted immediately after execution.
3. **Restricted Mounts**: Only the specific case directory is mounted, read-only (`:ro`).
4. **No Privileged Access**: Running in privileged mode or mounting `/var/run/docker.sock` is blocked by the AFM security validator.
5. **Resource Quotas**: Hard-coded boundaries of 512MB RAM and 1.0 CPU by default.
6. **Network Isolation**: By default, `--network=none` prevents network egress.

---

## Writing Assertions

Assertions define how AFM confirms that the failure occurred:

```yaml
reproduction:
  type: "docker"
  entrypoint: "repro.py"
  command: "python repro.py"
  timeout_seconds: 30
  assertions:
    - type: exit_code_equals
      value: 1
      description: "Non-zero exit indicates crash"
    - type: stderr_contains
      value: "AttributeError"
      description: "Error trace indicates hallucinated function"
```

Supported assertion types:
- `exit_code_equals`: Compares integer exit code.
- `stdout_contains`: Substring check in standard output.
- `stdout_not_contains`: Ensures forbidden substring is absent.
- `stderr_contains`: Substring check in standard error.
- `file_exists`: Checks if target file was generated.
- `file_contains`: Checks if target file contains expected pattern.
