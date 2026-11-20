"""
Unit tests for the reproduction runner, assertion evaluations, container preparation,
security isolation policies, timeouts, and structured JSON reporting.
"""

import json
from pathlib import Path
import pytest

from afm.models import AssertionRule, AssertionType, FailureCase
from afm.runner import (
    AssertionResult,
    CONTAINER_SECURITY_DISCLAIMER,
    ContainerSecurityConfig,
    IsolatedTestDriver,
    ReproductionResult,
    ReproductionRunner,
    ReproductionStatus,
    build_docker_run_args,
    evaluate_assertions,
    validate_reproduction_input,
)


def sample_valid_case() -> FailureCase:
    return FailureCase.model_validate({
        "id": "SYN-0001",
        "title": "Synthetic Test Case For Runner",
        "description": "Comprehensive synthetic case to test reproduction runner pipeline.",
        "categories": ["hallucinated-api"],
        "status": "reproducible",
        "is_synthetic": True,
        "agent": {"name": "TestAgent"},
        "task": {"prompt": "Run the task properly"},
        "behavior": {"expected": "Expected outcome here", "observed": "Observed failure here"},
        "reproduction": {
            "type": "docker",
            "entrypoint": "repro.py",
            "command": "python repro.py",
            "timeout_seconds": 30,
            "assertions": [
                {
                    "type": "exit_code_equals",
                    "value": 1,
                    "description": "Exit code 1 on failure",
                },
                {
                    "type": "stderr_contains",
                    "value": "AttributeError",
                    "description": "AttributeError in trace",
                },
            ],
        },
        "verification": {"method_type": "automated-test", "failure_criteria": "Fails reproduction check"},
        "submission": {"submitted_by": "tester", "date": "2026-11-18"},
    })


def test_evaluate_assertions_exit_code():
    rules = [
        AssertionRule(type=AssertionType.EXIT_CODE_EQUALS, value=1),
        AssertionRule(type=AssertionType.EXIT_CODE_EQUALS, value=0),
    ]
    results = evaluate_assertions(rules, exit_code=1, stdout="", stderr="")
    assert results[0].passed is True
    assert results[1].passed is False
    assert results[0].actual == 1


def test_evaluate_assertions_exit_code_not_equals():
    rules = [
        AssertionRule(type="exit_code_not_equals", value=0, description="Exit code must not be 0"),
    ]
    results = evaluate_assertions(rules, exit_code=1, stdout="", stderr="")
    assert results[0].passed is True
    assert results[0].actual == 1


def test_evaluate_assertions_stdout():
    rules = [
        AssertionRule(type=AssertionType.STDOUT_CONTAINS, value="DATA_LOSS"),
        AssertionRule(type=AssertionType.STDOUT_NOT_CONTAINS, value="FATAL_ERROR"),
    ]
    results = evaluate_assertions(rules, exit_code=0, stdout="DATA_LOSS_DETECTED in config", stderr="")
    assert results[0].passed is True
    assert results[1].passed is True


def test_evaluate_assertions_stderr():
    rules = [
        AssertionRule(type=AssertionType.STDERR_CONTAINS, value="AttributeError"),
        AssertionRule(type="stderr_not_contains", value="SyntaxError"),
    ]
    results = evaluate_assertions(rules, exit_code=1, stdout="", stderr="Traceback: AttributeError: 'NoneType'")
    assert results[0].passed is True
    assert results[1].passed is True


def test_evaluate_assertions_file_checks(tmp_path: Path):
    test_file = tmp_path / "output.txt"
    test_file.write_text("Hello world assertion", encoding="utf-8")

    rules = [
        AssertionRule(type=AssertionType.FILE_EXISTS, target="output.txt", value=""),
        AssertionRule(type=AssertionType.FILE_CONTAINS, target="output.txt", value="Hello world"),
        AssertionRule(type=AssertionType.FILE_EXISTS, target="missing.txt", value=""),
    ]
    results = evaluate_assertions(rules, exit_code=0, stdout="", stderr="", workspace_dir=tmp_path)
    assert results[0].passed is True
    assert results[1].passed is True
    assert results[2].passed is False


def test_evaluate_assertions_duration():
    rules = [
        AssertionRule(type="duration_under", value=5.0, description="Under 5s"),
        AssertionRule(type="duration_under", value=0.5, description="Under 0.5s"),
    ]
    results = evaluate_assertions(rules, exit_code=0, stdout="", stderr="", duration_seconds=1.2)
    assert results[0].passed is True
    assert results[1].passed is False


def test_build_docker_run_args():
    case = sample_valid_case()
    case_dir = Path("/tmp/case_dir")
    cfg = ContainerSecurityConfig(
        memory_limit="256m",
        memory_swap="256m",
        cpu_limit=0.5,
        pids_limit=50,
        network_mode="none",
        read_only_rootfs=True,
    )
    args = build_docker_run_args(case, case_dir, cfg, "python repro.py")

    assert "docker" in args
    assert "run" in args
    assert "--rm" in args
    assert "--network" in args and "none" in args
    assert "--memory=256m" in args
    assert "--memory-swap=256m" in args
    assert "--cpus=0.5" in args
    assert "--pids-limit=50" in args
    assert "--read-only" in args
    assert "--security-opt" in args and "no-new-privileges" in args
    assert "-w" in args and "/workspace" in args
    assert "python repro.py" in args


def test_input_validation_missing_entrypoint(tmp_path: Path):
    case = sample_valid_case()
    case.reproduction.entrypoint = "non_existent.py"
    cfg = ContainerSecurityConfig()
    ok, errors = validate_reproduction_input(case, tmp_path, cfg)
    assert ok is False
    assert any("does not exist" in e for e in errors)


def test_input_validation_path_traversal(tmp_path: Path):
    case = sample_valid_case()
    case.reproduction.entrypoint = "../../outside.py"
    cfg = ContainerSecurityConfig()
    ok, errors = validate_reproduction_input(case, tmp_path, cfg)
    assert ok is False
    assert any("Path traversal detected" in e for e in errors)


def test_input_validation_invalid_memory_format(tmp_path: Path):
    case = sample_valid_case()
    # create repro.py in tmp_path
    (tmp_path / "repro.py").write_text("print('test')", encoding="utf-8")
    cfg = ContainerSecurityConfig(memory_limit="invalid_mem")
    ok, errors = validate_reproduction_input(case, tmp_path, cfg)
    assert ok is False
    assert any("Invalid memory limit format" in e for e in errors)


def test_input_validation_memory_exceeds_policy(tmp_path: Path):
    case = sample_valid_case()
    (tmp_path / "repro.py").write_text("print('test')", encoding="utf-8")
    cfg = ContainerSecurityConfig(memory_limit="4096m")
    ok, errors = validate_reproduction_input(case, tmp_path, cfg)
    assert ok is False
    assert any("exceeds safety cap" in e for e in errors)


def test_runner_refuses_unsafe_host_execution(tmp_path: Path):
    """
    Verifies that when Docker is enforced and Docker is unavailable,
    the runner safely returns UNSUPPORTED_ENVIRONMENT without running code on host.
    """
    case = sample_valid_case()
    (tmp_path / "repro.py").write_text("print('test')", encoding="utf-8")

    runner = ReproductionRunner(enforce_docker=True)
    res = runner.run(case=case, case_dir=tmp_path)

    # When docker is not running on host
    if res.status == ReproductionStatus.UNSUPPORTED_ENVIRONMENT:
        assert "Docker daemon is not available" in res.error_message
        assert res.exit_code is None


def test_runner_timeout_handling(tmp_path: Path):
    case = sample_valid_case()
    (tmp_path / "repro.py").write_text("import time; time.sleep(1)", encoding="utf-8")

    # Driver simulating timeout
    driver = IsolatedTestDriver(simulate_timeout=True)
    runner = ReproductionRunner(enforce_docker=False, driver=driver)
    res = runner.run(case=case, case_dir=tmp_path, custom_timeout=1)

    assert res.status == ReproductionStatus.TIMEOUT
    assert "timed out" in res.error_message


def test_runner_secret_redaction(tmp_path: Path):
    case = sample_valid_case()
    repro_script = (
        "import sys\n"
        "sys.stderr.write('Traceback with key: sk-proj-1234567890abcdefghijklmnopqrstuvwxyz1234567890\\nAttributeError\\n')\n"
        "sys.exit(1)\n"
    )
    (tmp_path / "repro.py").write_text(repro_script, encoding="utf-8")

    driver = IsolatedTestDriver()
    runner = ReproductionRunner(enforce_docker=False, driver=driver)
    res = runner.run(case=case, case_dir=tmp_path)

    assert res.status == ReproductionStatus.PASSED
    assert res.logs.secrets_redacted is True
    assert "sk-proj-" not in res.logs.stderr
    assert "[REDACTED_OPENAI_KEY]" in res.logs.stderr


def test_structured_json_report_format(tmp_path: Path):
    case = sample_valid_case()
    (tmp_path / "repro.py").write_text("import sys; sys.stderr.write('AttributeError\\n'); sys.exit(1)\n", encoding="utf-8")

    driver = IsolatedTestDriver()
    runner = ReproductionRunner(enforce_docker=False, driver=driver)
    res = runner.run(case=case, case_dir=tmp_path)

    json_str = res.to_json(indent=2)
    data = json.loads(json_str)

    # Verify all expected schema fields
    assert data["case_id"] == "SYN-0001"
    assert data["status"] == "reproduced"
    assert "execution" in data
    assert data["execution"]["exit_code"] == 1
    assert "resource_limits" in data["execution"]
    assert data["execution"]["resource_limits"]["memory_limit"] == "512m"
    assert data["execution"]["resource_limits"]["read_only_rootfs"] is True
    assert "assertions" in data
    assert data["assertions"]["total"] == 2
    assert data["assertions"]["passed"] == 2
    assert data["assertions"]["failed"] == 0
    assert "security" in data
    assert data["security"]["disclaimer"] == CONTAINER_SECURITY_DISCLAIMER
    assert "logs" in data
    assert "AttributeError" in data["logs"]["stderr"]


def test_e2e_reproduce_synthetic_syn_0001():
    root = Path(__file__).resolve().parent.parent
    case_dir = root / "examples" / "synthetic" / "SYN-0001"
    from afm.models import FailureCase
    import yaml

    case_data = yaml.safe_load((case_dir / "case.yaml").read_text(encoding="utf-8"))
    case = FailureCase.model_validate(case_data)

    driver = IsolatedTestDriver()
    runner = ReproductionRunner(enforce_docker=False, driver=driver)
    res = runner.run(case=case, case_dir=case_dir)

    assert res.status == ReproductionStatus.PASSED
    assert res.exit_code == 1
    assert res.assertions_passed_count == 2
    assert res.assertions_total_count == 2


def test_e2e_reproduce_synthetic_syn_0002():
    root = Path(__file__).resolve().parent.parent
    case_dir = root / "examples" / "synthetic" / "SYN-0002"
    from afm.models import FailureCase
    import yaml

    case_data = yaml.safe_load((case_dir / "case.yaml").read_text(encoding="utf-8"))
    case = FailureCase.model_validate(case_data)

    driver = IsolatedTestDriver()
    runner = ReproductionRunner(enforce_docker=False, driver=driver)
    res = runner.run(case=case, case_dir=case_dir)

    assert res.status == ReproductionStatus.PASSED
    assert res.exit_code == 2
    assert "DATA_LOSS_DETECTED" in res.logs.stdout
    assert res.assertions_passed_count == 2


def test_e2e_reproduce_synthetic_syn_0003():
    root = Path(__file__).resolve().parent.parent
    case_dir = root / "examples" / "synthetic" / "SYN-0003"
    from afm.models import FailureCase
    import yaml

    case_data = yaml.safe_load((case_dir / "case.yaml").read_text(encoding="utf-8"))
    case = FailureCase.model_validate(case_data)

    driver = IsolatedTestDriver()
    runner = ReproductionRunner(enforce_docker=False, driver=driver)
    res = runner.run(case=case, case_dir=case_dir)

    assert res.status == ReproductionStatus.PASSED
    assert res.exit_code == 3
    assert "TEST_WAS_TAMPERED" in res.logs.stdout
    assert res.assertions_passed_count == 2
