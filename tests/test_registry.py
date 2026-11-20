"""
Unit tests for FailureRegistry discovery, indexing, duplicate detection, and queries.
"""

from pathlib import Path
import pytest
import yaml

from afm.models import CaseStatus, FailureCategory
from afm.registry import DuplicateCaseIdError, FailureRegistry, CaseNotFoundError


def test_registry_loading_from_workspace():
    root = Path(__file__).resolve().parent.parent
    registry = FailureRegistry.from_workspace(root)

    assert len(registry.cases) >= 3
    assert "SYN-0001" in [c.id for c in registry.cases]
    assert "SYN-0002" in [c.id for c in registry.cases]
    assert "SYN-0003" in [c.id for c in registry.cases]


def test_registry_duplicate_id_detection(tmp_path: Path):
    # Create two case files with the same ID
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()

    case_data = {
        "id": "SYN-1111",
        "title": "Case One Title Here",
        "description": "Case One detailed description here",
        "categories": ["hallucinated-api"],
        "status": "reproducible",
        "is_synthetic": True,
        "agent": {"name": "AgentA"},
        "task": {"prompt": "Prompt A details"},
        "behavior": {"expected": "Expected behavior text", "observed": "Observed behavior text"},
        "verification": {"method_type": "manual", "failure_criteria": "Criteria details here"},
        "submission": {"submitted_by": "tester", "date": "2026-11-18"},
    }

    (dir1 / "case.yaml").write_text(yaml.dump(case_data), encoding="utf-8")
    (dir2 / "case.yaml").write_text(yaml.dump(case_data), encoding="utf-8")

    registry = FailureRegistry([tmp_path])
    with pytest.raises(DuplicateCaseIdError) as exc:
        registry.load(strict=True)
    assert "Duplicate case ID detected: 'SYN-1111'" in str(exc.value)


def test_registry_get_case_not_found():
    root = Path(__file__).resolve().parent.parent
    registry = FailureRegistry.from_workspace(root)

    with pytest.raises(CaseNotFoundError):
        registry.get("AFM-9999")


def test_registry_queries():
    root = Path(__file__).resolve().parent.parent
    registry = FailureRegistry.from_workspace(root)

    # By category
    hallucinated = registry.query(category=FailureCategory.HALLUCINATED_API)
    assert any(c.id == "SYN-0001" for c in hallucinated)

    # By text search
    searched = registry.query(text="os.path.find_files")
    assert len(searched) == 1
    assert searched[0].id == "SYN-0001"

    # By synthetic flag
    reals = registry.query(is_synthetic=False)
    assert len(reals) == 0  # No real cases in synthetic example dir


def test_registry_statistics():
    root = Path(__file__).resolve().parent.parent
    registry = FailureRegistry.from_workspace(root)
    stats = registry.statistics()

    assert stats.total_cases >= 3
    assert stats.synthetic_cases >= 3
    assert stats.real_cases == 0
    assert stats.reproducible_cases >= 3
    assert "hallucinated-api" in stats.category_counts


def test_registry_export_json(tmp_path: Path):
    root = Path(__file__).resolve().parent.parent
    registry = FailureRegistry.from_workspace(root)

    out_file = tmp_path / "registry.json"
    registry.export_json(out_file)
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "SYN-0001" in content
    assert '"total_cases":' in content
