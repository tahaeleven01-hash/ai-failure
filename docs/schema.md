# Failure Case Schema & Taxonomy Reference

## Overview

Every failure case in the AI Failure Museum must be defined in a `case.yaml` file that adheres strictly to the schema defined in `schemas/failure-case.schema.json`.

---

## Required Fields

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique identifier matching `^(AFM\|SYN)-\d{4}$`. Real cases use `AFM-`; synthetic test cases use `SYN-`. |
| `title` | `string` | Short title between 5 and 150 characters. |
| `description` | `string` | Comprehensive description of the failure and its impact. |
| `categories` | `array[string]` | One or more taxonomy categories. |
| `status` | `string` | One of `submitted`, `validated`, `reproducible`, `non-reproducible`, `archived`. |
| `is_synthetic` | `boolean` | Must be `true` for `SYN-` cases, `false` for `AFM-` cases. |
| `agent` | `object` | Agent details: `name` (required), `version`, `model`, `provider`. |
| `task` | `object` | Task details: `prompt` (required), `context`, `target_repository`, `target_files`. |
| `behavior` | `object` | Behavior contrast: `expected` (required), `observed` (required). |
| `environment` | `object` | Host environment: `os`, `runtime`, `dependencies`, `docker_image`. |
| `reproduction` | `object` | Execution details: `type`, `entrypoint`, `command`, `timeout_seconds`, `assertions`. |
| `verification` | `object` | Verification details: `method_type`, `test_runner`, `expected_exit_code`, `failure_criteria`. |
| `evidence` | `array[object]` | Evidence items: `type` (`log`, `diff`, `screenshot`, `recording`, `link`), `path_or_url`, `description`. |
| `submission` | `object` | Submission details: `submitted_by`, `date` (YYYY-MM-DD). |

---

## Failure Taxonomy

The supported categories are:
1. `hallucinated-api`: Agent invoked a non-existent standard library or third-party method.
2. `incorrect-code-modification`: Agent edited code in a way that introduces syntax or logic errors.
3. `destructive-file-operation`: Agent deleted or truncated unintended files or directories.
4. `dependency-conflict`: Agent installed incompatible package versions breaking the environment.
5. `failed-bug-fix`: Agent attempted to fix a defect but left the bug unresolved.
6. `incorrect-test-generation`: Agent created invalid or circular tests.
7. `security-regression`: Agent introduced an insecure pattern (e.g. SQL injection, exposed secret).
8. `context-misunderstanding`: Agent misread existing repository architecture or instructions.
9. `instruction-following-failure`: Agent violated explicit negative or positive prompt constraints.
10. `false-success-claim`: Agent falsely declared success (e.g. by deleting or commenting out tests).
11. `environment-configuration-failure`: Agent misconfigured system or environment variables.
