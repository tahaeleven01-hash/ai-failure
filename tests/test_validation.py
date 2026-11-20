"""
Unit tests for AFM case validation engine.
"""

from pathlib import Path
import pytest
import yaml

from afm.validation import validate_case_file


def test_validate_existing_synthetic_cases():
    root = Path(__file__).resolve().parent.parent
    synthetic_dir = root / "examples" / "synthetic"
    schema_path = root / "schemas" / "failure-case.schema.json"

    for case_file in synthetic_dir.rglob("case.yaml"):
        res = validate_case_file(case_file, schema_path=schema_path, verify_references=True)
        assert res.valid is True, f"Failed validation on {case_file}: {res.errors}"
        assert res.case is not None
        assert res.case_id == res.case.id


def test_validate_missing_file():
    res = validate_case_file(Path("non_existent_file.yaml"))
    assert res.valid is False
    assert any("File not found" in err for err in res.errors)


def test_validate_invalid_yaml(tmp_path: Path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("key: [unclosed list", encoding="utf-8")
    res = validate_case_file(bad_yaml)
    assert res.valid is False
    assert any("YAML parsing error" in err for err in res.errors)


def test_validate_exposed_secret_strict(tmp_path: Path):
    secret_yaml = tmp_path / "secret.yaml"
    content = {
        "id": "SYN-9999",
        "title": "Secret Test Case",
        "description": "Testing that secrets are caught.",
        "categories": ["hallucinated-api"],
        "status": "reproducible",
        "is_synthetic": True,
        "agent": {"name": "AgentX"},
        "task": {"prompt": "Use sk-proj-1234567890abcdefghijklmnopqrstuvwxyz1234567890 to authenticate."},
        "behavior": {"expected": "Clean text", "observed": "Exposed key"},
        "verification": {"method_type": "manual", "failure_criteria": "Leaks key"},
        "submission": {"submitted_by": "tester", "date": "2026-11-18"},
    }
    secret_yaml.write_text(yaml.dump(content), encoding="utf-8")

    res = validate_case_file(secret_yaml, strict_secrets=True)
    assert res.valid is False
    assert any("Security Violation" in err for err in res.errors)


def test_validate_missing_referenced_entrypoint(tmp_path: Path):
    case_path = tmp_path / "case.yaml"
    content = {
        "id": "SYN-9998",
        "title": "Missing Reference Case",
        "description": "Testing that missing entrypoints are flagged as warnings.",
        "categories": ["hallucinated-api"],
        "status": "reproducible",
        "is_synthetic": True,
        "agent": {"name": "AgentX"},
        "task": {"prompt": "Run the code"},
        "behavior": {"expected": "Runs without errors", "observed": "Fails unexpectedly"},
        "reproduction": {
            "type": "docker",
            "entrypoint": "does_not_exist.py",
        },
        "verification": {"method_type": "manual", "failure_criteria": "Throws exception"},
        "submission": {"submitted_by": "tester", "date": "2026-11-18"},
    }
    case_path.write_text(yaml.dump(content), encoding="utf-8")

    res = validate_case_file(case_path, verify_references=True)
    assert res.valid is True
    assert any("does not exist" in w for w in res.warnings)
