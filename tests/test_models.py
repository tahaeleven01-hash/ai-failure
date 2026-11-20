"""
Unit tests for AFM data models and validation constraints.
"""

import datetime
import pytest
from pydantic import ValidationError

from afm.models import (
    AgentMetadata,
    AssertionRule,
    AssertionType,
    BehaviorComparison,
    CaseStatus,
    FailureCase,
    FailureCategory,
    ReproductionProcedure,
    SubmissionMetadata,
    TaskDefinition,
    VerificationMethod,
)


def sample_valid_case_dict():
    return {
        "id": "SYN-0001",
        "title": "Synthetic Failure Case for Testing",
        "description": "A synthetic failure definition to verify model parsing.",
        "categories": ["hallucinated-api"],
        "status": "reproducible",
        "is_synthetic": True,
        "agent": {
            "name": "TestAgent",
            "version": "1.0",
        },
        "task": {
            "prompt": "Find all markdown files recursively.",
            "target_files": ["finder.py"],
        },
        "behavior": {
            "expected": "Use os.walk or glob.",
            "observed": "Called os.path.find_files which does not exist.",
        },
        "reproduction": {
            "type": "docker",
            "timeout_seconds": 30,
            "assertions": [
                {
                    "type": "exit_code_equals",
                    "value": 1,
                }
            ],
        },
        "verification": {
            "method_type": "automated-test",
            "expected_exit_code": 1,
            "failure_criteria": "Throws AttributeError on invalid API call.",
        },
        "submission": {
            "submitted_by": "test-maintainer",
            "date": "2026-11-18",
        },
    }


def test_valid_failure_case():
    data = sample_valid_case_dict()
    case = FailureCase.model_validate(data)
    assert case.id == "SYN-0001"
    assert case.categories == [FailureCategory.HALLUCINATED_API]
    assert case.status == CaseStatus.REPRODUCIBLE
    assert case.is_synthetic is True


def test_invalid_case_id_pattern():
    data = sample_valid_case_dict()
    data["id"] = "INVALID-12"
    with pytest.raises(ValidationError) as exc:
        FailureCase.model_validate(data)
    assert "Case ID 'INVALID-12' is invalid" in str(exc.value)


def test_synthetic_id_mismatch():
    data = sample_valid_case_dict()
    # SYN prefix with is_synthetic=False should fail
    data["is_synthetic"] = False
    with pytest.raises(ValidationError) as exc:
        FailureCase.model_validate(data)
    assert "Cases with ID prefix 'SYN-' must have 'is_synthetic: true'" in str(exc.value)


def test_real_id_synthetic_mismatch():
    data = sample_valid_case_dict()
    data["id"] = "AFM-0001"
    data["is_synthetic"] = True
    with pytest.raises(ValidationError) as exc:
        FailureCase.model_validate(data)
    assert "Cases with ID prefix 'AFM-' cannot have 'is_synthetic: true'" in str(exc.value)


def test_missing_required_fields():
    data = sample_valid_case_dict()
    del data["title"]
    del data["agent"]
    with pytest.raises(ValidationError) as exc:
        FailureCase.model_validate(data)
    errors = [e["loc"][0] for e in exc.value.errors()]
    assert "title" in errors
    assert "agent" in errors


def test_extra_fields_forbidden():
    data = sample_valid_case_dict()
    data["unexpected_property"] = "malicious or invalid"
    with pytest.raises(ValidationError) as exc:
        FailureCase.model_validate(data)
    assert "unexpected_property" in str(exc.value)
