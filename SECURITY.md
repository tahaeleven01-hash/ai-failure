# Security Policy

## Security Philosophy & Isolation Model

The AI Failure Museum executes and archives code patterns that represent flawed or destructive behaviors in AI agents. Because failure cases may involve destructive file operations, hallucinated commands, or untrusted external submissions, security is an architectural priority.

---

## 1. Sandbox Isolation Boundaries

When running failure reproductions via `afm reproduce`:
- **Docker Isolation Enforced**: Containerization is mandatory for code execution. If Docker is not available on the host, AFM explicitly aborts execution with status `unsupported-environment` rather than executing directly on the host machine.
- **Resource Limits**: Containers are launched with hard quotas:
  - Default CPU limit: `1.0` cores (maximum allowed: `2.0`).
  - Default Memory limit: `512MB` (maximum allowed: `2048MB`).
- **Filesystem Constraints**: Case directories are mounted read-only (`:ro`). Containers use ephemeral `tmpfs` mounts for temporary writes.
- **Forbidden Host Mounts**: Mounting host sockets (`/var/run/docker.sock`), sensitive configuration directories (`~/.ssh`, `~/.aws`, `~/.config`), or system roots is blocked by the AFM security validator.
- **Network Isolation**: By default, containers run with `--network=none`. Network access is only granted when a case explicitly requires it and the user passes `--allow-network`.

---

## 2. CI & Pull Request Security

- **Untrusted Code Execution**: Pull requests from community forks run only static schema validation (`afm validate`) and unit tests on vetted framework logic.
- **No Privileged Execution in CI**: Community reproduction scripts are never automatically executed in CI environments containing repository secrets.
- **Automated Secret Scrubbing**: All terminal logs, stdout, and stderr are filtered through regular expression redactors to strip OpenAI, Anthropic, AWS, GitHub, and private keys.

---

## 3. Reporting a Vulnerability

If you discover a security vulnerability or containment escape in AFM:
1. Do **not** open a public issue on GitHub.
2. Email full technical details, reproduction steps, and impact assessment to: `security@aifailuremuseum.org`.
3. We will acknowledge receipt within 48 hours and work with you on a coordinated disclosure timeline.
