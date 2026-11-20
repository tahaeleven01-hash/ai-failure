"""
Unit tests for security policies, secret redaction, and path traversal defenses.
"""

from pathlib import Path
import pytest

from afm.security import (
    find_exposed_secrets,
    redact_secrets,
    resolve_safe_path,
    validate_container_security,
)


def test_redact_openai_key():
    raw = "Here is my key sk-proj-1234567890abcdefghijklmnopqrstuvwxyz1234567890 and text."
    redacted = redact_secrets(raw)
    assert "sk-proj-" not in redacted
    assert "[REDACTED_OPENAI_KEY]" in redacted


def test_redact_anthropic_key():
    raw = "anthropic_key = 'sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890'"
    redacted = redact_secrets(raw)
    assert "sk-ant-" not in redacted
    assert "[REDACTED_ANTHROPIC_KEY]" in redacted


def test_redact_generic_token():
    raw = "api_key: 'abcdef12345678901234567890'"
    redacted = redact_secrets(raw)
    assert "abcdef12345678901234567890" not in redacted
    assert "api_key=[REDACTED]" in redacted


def test_find_exposed_secrets():
    raw = "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890abcdef"
    warnings = find_exposed_secrets(raw)
    assert len(warnings) > 0


def test_path_traversal_detection(tmp_path: Path):
    base_dir = tmp_path / "sandbox"
    base_dir.mkdir()

    # Valid relative path inside base
    safe = resolve_safe_path(base_dir, "subdir/file.txt")
    assert safe == (base_dir / "subdir" / "file.txt").resolve()

    # Path traversal attack
    with pytest.raises(ValueError) as exc:
        resolve_safe_path(base_dir, "../../etc/passwd")
    assert "Path traversal detected" in str(exc.value)


def test_container_security_forbidden_mounts():
    # Attempting to mount docker socket
    ok, violations = validate_container_security(
        mounts=["/var/run/docker.sock:/var/run/docker.sock"]
    )
    assert not ok
    assert any("docker.sock" in v for v in violations)


def test_container_security_limits():
    # Exceeding CPU limit
    ok, violations = validate_container_security(cpu_limit=4.0)
    assert not ok
    assert any("CPU limit" in v for v in violations)

    # Exceeding Memory limit
    ok, violations = validate_container_security(memory_limit="4096m")
    assert not ok
    assert any("Memory limit" in v for v in violations)


def test_container_security_privileged_denied():
    ok, violations = validate_container_security(privileged=True)
    assert not ok
    assert any("privileged" in v for v in violations)
