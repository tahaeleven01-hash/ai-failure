"""
Verification test ensuring that web application data (web/data/registry.json)
is in 100% synchronization with the authoritative Python failure registry.
Verifies no fabricated statistics, users, or benchmark claims exist.
"""

import json
from pathlib import Path
import pytest

from afm.registry import FailureRegistry


def test_web_data_matches_python_registry():
    root = Path(__file__).resolve().parent.parent
    web_json_path = root / "web" / "data" / "registry.json"

    assert web_json_path.exists(), f"Missing web data file at {web_json_path}"

    with open(web_json_path, "r", encoding="utf-8") as f:
        web_data = json.load(f)

    # Load source of truth from Python registry
    registry = FailureRegistry.from_workspace(root)
    py_stats = registry.statistics()

    web_stats = web_data["statistics"]

    # 1. Verify top-level metrics match exactly
    assert web_stats["total_cases"] == py_stats.total_cases
    assert web_stats["real_cases"] == py_stats.real_cases
    assert web_stats["synthetic_cases"] == py_stats.synthetic_cases
    assert web_stats["reproducible_cases"] == py_stats.reproducible_cases

    # 2. Verify category counts match exactly
    assert web_stats["category_counts"] == py_stats.category_counts

    # 3. Verify status counts match exactly
    assert web_stats["status_counts"] == py_stats.status_counts

    # 4. Verify agent counts match exactly
    assert web_stats["agent_counts"] == py_stats.agent_counts

    # 5. Verify case list matches case by case
    web_cases = web_data["cases"]
    assert len(web_cases) == len(registry.cases)

    py_cases_by_id = {c.id: c for c in registry.cases}

    for wc in web_cases:
        cid = wc["id"]
        assert cid in py_cases_by_id, f"Web case {cid} not found in Python registry"

        pc = py_cases_by_id[cid]
        assert wc["title"] == pc.title
        assert wc["description"] == pc.description
        assert wc["status"] == pc.status.value
        assert wc["is_synthetic"] == pc.is_synthetic
        assert wc["agent"]["name"] == pc.agent.name
        assert wc["task"]["prompt"] == pc.task.prompt
        assert wc["behavior"]["expected"] == pc.behavior.expected
        assert wc["behavior"]["observed"] == pc.behavior.observed
        assert [c.value for c in pc.categories] == wc["categories"]
        assert len(wc["reproduction"]["assertions"]) == len(pc.reproduction.assertions)

    # 6. Verify all synthetic cases are explicitly labeled
    for wc in web_cases:
        if wc["id"].startswith("SYN-"):
            assert wc["is_synthetic"] is True, f"Synthetic case {wc['id']} must have is_synthetic=true"
        elif wc["id"].startswith("AFM-"):
            assert wc["is_synthetic"] is False, f"Real case {wc['id']} must have is_synthetic=false"
