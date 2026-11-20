"""
Security utilities and isolation policy enforcement for AI Failure Museum.
Handles secret redaction, path traversal protection, and container isolation validation.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Common patterns for API keys and tokens
SECRET_PATTERNS = [
    # Generic bearer tokens & API keys
    (re.compile(r"(?i)(api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{16,})['\"]?"), r"\1=[REDACTED]"),
    # OpenAI API Keys
    (re.compile(r"sk-[a-zA-Z0-9]{20,T3BlbkFJ[a-zA-Z0-9]{20,}"), "[REDACTED_OPENAI_KEY]"),
    (re.compile(r"sk-proj-[a-zA-Z0-9_\-]{40,}"), "[REDACTED_OPENAI_KEY]"),
    # Anthropic API Keys
    (re.compile(r"sk-ant-[a-zA-Z0-9_\-]{30,}"), "[REDACTED_ANTHROPIC_KEY]"),
    # GitHub Personal Access Tokens
    (re.compile(r"gh[pous]_[a-zA-Z0-9]{36,}"), "[REDACTED_GITHUB_TOKEN]"),
    # AWS Access Key ID
    (re.compile(r"\b(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    # Private RSA / SSH Keys
    (re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+ PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    # JSON Web Tokens
    (re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b"), "[REDACTED_JWT]"),
    # Slack tokens
    (re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}"), "[REDACTED_SLACK_TOKEN]"),
]

# Sensitive mount targets that must never be mounted into reproduction containers
FORBIDDEN_HOST_MOUNTS = [
    "/var/run/docker.sock",
    "//var/run/docker.sock",
    "/var/run",
    "/etc",
    "/boot",
    "/sys",
    "/proc",
    "~/.ssh",
    "~/.aws",
    "~/.config",
    "~/.gitconfig",
    "~/.bashrc",
    "~/.zshrc",
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
]


def redact_secrets(text: str) -> str:
    """
    Scans input text and redacts any recognized API keys, credentials, or private tokens.
    """
    if not text:
        return text

    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def find_exposed_secrets(text: str) -> List[str]:
    """
    Detects potential exposed secrets in the text and returns a list of warnings.
    """
    warnings = []
    if not text:
        return warnings

    for pattern, _ in SECRET_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            warnings.append(f"Potential secret detected matching pattern {pattern.pattern[:30]}...")
    return warnings


def resolve_safe_path(base_dir: Path, relative_path: str) -> Path:
    """
    Resolves relative_path against base_dir and verifies that the resulting path
    stays within base_dir, preventing directory traversal attacks.
    """
    base_resolved = base_dir.resolve()
    target_path = (base_dir / relative_path).resolve()

    try:
        target_path.relative_to(base_resolved)
    except ValueError:
        raise ValueError(f"Path traversal detected: '{relative_path}' resolves outside '{base_dir}'.")

    return target_path


def validate_container_security(
    mounts: Optional[List[str]] = None,
    network_mode: Optional[str] = "none",
    memory_limit: Optional[str] = "512m",
    cpu_limit: Optional[float] = 1.0,
    privileged: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Audits a container execution configuration against AFM security policies.
    Returns (is_compliant, list_of_violations).
    """
    violations = []

    if privileged:
        violations.append("Containers must never run in privileged mode.")

    # Check mounts
    if mounts:
        for mount in mounts:
            host_path = mount.split(":")[0] if ":" in mount else mount
            normalized = host_path.replace("\\", "/").lower()
            for forbidden in FORBIDDEN_HOST_MOUNTS:
                if forbidden.lower() in normalized:
                    violations.append(f"Mounting sensitive directory or socket '{host_path}' is strictly prohibited.")

    # Check network isolation
    if network_mode not in ("none", "host-denied", None) and network_mode != "bridge":
        violations.append(f"Unsafe network mode: '{network_mode}'. Default must be 'none'.")

    # Check resource boundaries
    if cpu_limit is not None and cpu_limit > 2.0:
        violations.append(f"CPU limit '{cpu_limit}' exceeds policy maximum of 2.0 cores.")

    if memory_limit:
        mem_match = re.match(r"^(\d+)([mgMG])$", memory_limit)
        if mem_match:
            val, unit = int(mem_match.group(1)), mem_match.group(2).lower()
            val_mb = val if unit == "m" else val * 1024
            if val_mb > 2048:
                violations.append(f"Memory limit '{memory_limit}' ({val_mb}MB) exceeds policy maximum of 2048MB.")

    return len(violations) == 0, violations
