"""
Unit tests for evaluation adapters, orchestration engine, and benchmark metrics.
"""

from pathlib import Path
import pytest

from afm.adapters import get_adapter, list_adapters
from afm.adapters.mock import MockAdapter, MockBehavior
from afm.evaluation import EvaluationEngine
from afm.models import FailureCase


@pytest.fixture
def sample_case() -> FailureCase:
    return FailureCase.model_validate({
        "id": "SYN-0001",
        "title": "Synthetic Evaluation Case",
        "description": "Used to test evaluation engine orchestration.",
        "categories": ["hallucinated-api"],
        "status": "reproducible",
        "is_synthetic": True,
        "agent": {"name": "TestAgent"},
        "task": {"prompt": "Implement a resolve_task function returning True."},
        "behavior": {"expected": "Working code", "observed": "Crashed"},
        "reproduction": {"type": "docker", "timeout_seconds": 10},
        "verification": {
            "method_type": "automated-test",
            "test_runner": 'python -c "import solution; assert solution.resolve_task()"',
            "expected_exit_code": 0,
            "failure_criteria": "Assert fails",
        },
        "submission": {"submitted_by": "tester", "date": "2026-11-18"},
    })


def test_adapter_registry():
    adapters = list_adapters()
    assert "mock" in adapters
    adapter = get_adapter("mock")
    assert isinstance(adapter, MockAdapter)
    assert adapter.is_mock is True


def test_mock_adapter_success_execution(tmp_path: Path):
    adapter = MockAdapter(behavior=MockBehavior.SUCCESS, delay=0.01)
    output = adapter.run_agent(task_prompt="Solve this", context=None, workspace_dir=tmp_path)

    assert output.exit_code == 0
    assert "solution.py" in output.modified_files
    assert (tmp_path / "solution.py").exists()
    assert "+ def resolve_task" in output.diff


def test_mock_adapter_failure_execution(tmp_path: Path):
    adapter = MockAdapter(behavior=MockBehavior.FAIL, delay=0.01)
    output = adapter.run_agent(task_prompt="Solve this", context=None, workspace_dir=tmp_path)

    assert output.exit_code == 1
    assert "Simulated agent failure" in output.error_message


def test_evaluation_engine_workflow(sample_case: FailureCase):
    engine = EvaluationEngine()
    adapter = MockAdapter(behavior=MockBehavior.SUCCESS, delay=0.01)

    result = engine.evaluate(case=sample_case, adapter=adapter, timeout_seconds=10)

    assert result.case_id == "SYN-0001"
    assert result.adapter_name == "mock"
    assert result.is_mock is True
    assert result.task_resolved is True
    assert result.agent_exit_code == 0
    assert result.test_exit_code == 0
    assert "solution.py" in result.modified_files
