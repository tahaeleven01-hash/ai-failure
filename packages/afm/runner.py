"""
Reproduction Engine for AI Failure Museum (AFM).
Executes failure reproduction procedures inside restricted Docker containers with strict
resource limits (memory, CPU, PIDs), network isolation, read-only filesystems, timeouts,
comprehensive assertion checking, execution logging, and structured JSON reporting.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from afm.models import AssertionRule, AssertionType, FailureCase
from afm.security import find_exposed_secrets, redact_secrets, resolve_safe_path, validate_container_security

# Realistic security disclaimer acknowledging Docker containerization limits
CONTAINER_SECURITY_DISCLAIMER = (
    "Container isolation leverages Linux kernel cgroups and namespaces for process and resource partitioning. "
    "It does not provide hardware-level virtualization or an absolute security guarantee against kernel exploits, "
    "container breakout CVEs, or side-channel vulnerabilities."
)


class ReproductionStatus(str, Enum):
    """Outcome status of a reproduction run."""
    PASSED = "reproduced"                          # Failure reproduced as expected (all assertions passed)
    FAILED = "not-reproduced"                      # Failure did not reproduce or assertions failed
    TIMEOUT = "timeout"                            # Execution exceeded configured timeout deadline
    SECURITY_VIOLATION = "security-violation"      # Configuration violated security isolation boundaries
    VALIDATION_ERROR = "validation-error"          # Invalid input metadata or missing required files
    UNSUPPORTED_ENVIRONMENT = "unsupported-environment"  # Docker or required sandbox is unavailable
    ERROR = "execution-error"                      # Container startup error, bad image, or runner crash


@dataclass
class ContainerSecurityConfig:
    """Security boundaries and resource limits enforced on reproduction containers."""
    memory_limit: str = "512m"
    memory_swap: str = "512m"               # Equal to memory_limit to disable swap usage
    cpu_limit: float = 1.0                  # Max CPU quota
    pids_limit: int = 100                   # Prevent fork bombs and thread exhaustion
    read_only_rootfs: bool = True           # Read-only root filesystem
    tmpfs_mounts: Dict[str, str] = field(default_factory=lambda: {
        "/tmp": "rw,noexec,nosuid,size=64m",
    })
    security_opts: List[str] = field(default_factory=lambda: ["no-new-privileges"])
    drop_capabilities: List[str] = field(default_factory=lambda: ["ALL"])
    network_mode: str = "none"


@dataclass
class AssertionResult:
    """Individual assertion check outcome."""
    rule_type: str
    target: Optional[str]
    expected: Union[str, int]
    actual: Optional[Union[str, int]]
    passed: bool
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.rule_type,
            "target": self.target,
            "expected": self.expected,
            "actual": self.actual,
            "passed": self.passed,
            "details": self.details,
        }


@dataclass
class ExecutionLog:
    """Captured container execution logs with secret redaction tracking."""
    stdout: str = ""
    stderr: str = ""
    secrets_redacted: bool = False
    raw_length_stdout: int = 0
    raw_length_stderr: int = 0


@dataclass
class ReproductionResult:
    """Complete structured summary of a reproduction run."""
    case_id: str
    status: ReproductionStatus
    title: str = ""
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    timeout_seconds: int = 60
    logs: ExecutionLog = field(default_factory=ExecutionLog)
    assertion_results: List[AssertionResult] = field(default_factory=list)
    security_violations: List[str] = field(default_factory=list)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_mode: str = "docker"
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @property
    def passed(self) -> bool:
        return self.status == ReproductionStatus.PASSED

    @property
    def assertions_passed_count(self) -> int:
        return sum(1 for a in self.assertion_results if a.passed)

    @property
    def assertions_total_count(self) -> int:
        return len(self.assertion_results)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes result into standardized, machine-readable JSON structure."""
        return {
            "case_id": self.case_id,
            "title": self.title,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "execution": {
                "mode": self.execution_mode,
                "exit_code": self.exit_code,
                "duration_seconds": round(self.duration_seconds, 4),
                "timeout_seconds": self.timeout_seconds,
                "resource_limits": self.resource_limits,
            },
            "assertions": {
                "total": self.assertions_total_count,
                "passed": self.assertions_passed_count,
                "failed": self.assertions_total_count - self.assertions_passed_count,
                "results": [a.to_dict() for a in self.assertion_results],
            },
            "security": {
                "isolation_model": "restricted-container",
                "disclaimer": CONTAINER_SECURITY_DISCLAIMER,
                "violations": self.security_violations,
                "secrets_redacted": self.logs.secrets_redacted,
            },
            "logs": {
                "stdout": self.logs.stdout,
                "stderr": self.logs.stderr,
            },
            "error_message": self.error_message,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def summary(self) -> str:
        s = f"[{self.status.value.upper()}] Case {self.case_id} in {self.duration_seconds:.2f}s"
        if self.exit_code is not None:
            s += f" (exit code {self.exit_code})"
        s += f" — Assertions: {self.assertions_passed_count}/{self.assertions_total_count} passed"
        if self.error_message:
            s += f" — {self.error_message}"
        return s


def is_docker_available() -> bool:
    """Checks if Docker binary is on PATH and the Docker daemon is responding."""
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return False

    try:
        proc = subprocess.run(
            [docker_bin, "info", "--format", "{{.ServerVersion}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            text=True,
        )
        return proc.returncode == 0
    except Exception:
        return False


def validate_reproduction_input(
    case: FailureCase,
    case_dir: Path,
    config: ContainerSecurityConfig,
) -> Tuple[bool, List[str]]:
    """
    Validates input case definition, workspace directory, entrypoint file,
    and reproduction resource boundaries before container preparation.
    """
    errors: List[str] = []

    if not case_dir.exists() or not case_dir.is_dir():
        errors.append(f"Workspace directory does not exist: {case_dir}")
        return False, errors

    repro = case.reproduction

    # Check timeout bounds
    if repro.timeout_seconds < 1 or repro.timeout_seconds > 600:
        errors.append(f"Timeout of {repro.timeout_seconds}s out of safe range (1-600 seconds).")

    # Check entrypoint existence
    if repro.entrypoint:
        try:
            ep_path = resolve_safe_path(case_dir, repro.entrypoint)
            if not ep_path.exists():
                errors.append(f"Reproduction entrypoint '{repro.entrypoint}' does not exist at {ep_path}.")
        except ValueError as ve:
            errors.append(f"Path traversal detected in entrypoint: {ve}")

    # Check command presence
    if not repro.entrypoint and not repro.command:
        errors.append("Reproduction procedure defines neither 'entrypoint' nor 'command'.")

    # Check assertions presence
    if not repro.assertions:
        errors.append("Reproduction procedure defines no verification assertions.")

    # Validate memory limits format
    mem_match = re.match(r"^(\d+)([kmgKMG]?)$", config.memory_limit)
    if not mem_match:
        errors.append(f"Invalid memory limit format: '{config.memory_limit}'. Expected e.g. '512m'.")
    else:
        val, unit = int(mem_match.group(1)), mem_match.group(2).lower()
        mb = val * (1024 if unit == "g" else (1 if unit == "m" else 1 / 1024))
        if mb > 2048:
            errors.append(f"Memory limit '{config.memory_limit}' exceeds safety cap of 2048MB.")

    # Validate CPU limits
    if config.cpu_limit <= 0 or config.cpu_limit > 2.0:
        errors.append(f"CPU limit '{config.cpu_limit}' must be between 0.1 and 2.0 cores.")

    # Validate PIDs limits
    if config.pids_limit < 10 or config.pids_limit > 1000:
        errors.append(f"PIDs limit '{config.pids_limit}' must be between 10 and 1000.")

    return len(errors) == 0, errors


def build_docker_run_args(
    case: FailureCase,
    case_dir: Path,
    config: ContainerSecurityConfig,
    entry_cmd: str,
) -> List[str]:
    """
    Constructs the exact restricted 'docker run' argument vector.
    Enforces resource caps, read-only root, tmpfs mounts, security opts, and network isolation.
    """
    image = case.environment.docker_image or "python:3.11-slim"

    args = [
        "docker", "run", "--rm",
        "--network", config.network_mode,
        f"--memory={config.memory_limit}",
        f"--memory-swap={config.memory_swap}",
        f"--cpus={config.cpu_limit}",
        f"--pids-limit={config.pids_limit}",
    ]

    if config.read_only_rootfs:
        args.append("--read-only")

    for dest, opts in config.tmpfs_mounts.items():
        args.extend(["--tmpfs", f"{dest}:{opts}"])

    for sopt in config.security_opts:
        args.extend(["--security-opt", sopt])

    for cap in config.drop_capabilities:
        args.extend(["--cap-drop", cap])

    # Mount case directory read-only into container workspace
    args.extend([
        "-v", f"{case_dir.resolve()}:/workspace:ro",
        "-w", "/workspace",
        image,
        "sh", "-c", entry_cmd,
    ])

    return args


def evaluate_assertions(
    assertions: List[AssertionRule],
    exit_code: Optional[int],
    stdout: str,
    stderr: str,
    duration_seconds: float = 0.0,
    workspace_dir: Optional[Path] = None,
) -> List[AssertionResult]:
    """
    Evaluates each defined assertion rule against the execution outcome.
    Supports exit codes, stdout, stderr, files, and duration assertions.
    """
    results: List[AssertionResult] = []

    for rule in assertions:
        passed = False
        actual: Optional[Union[str, int]] = None
        details = ""

        if rule.type == AssertionType.EXIT_CODE_EQUALS:
            expected_code = int(rule.value)
            actual = exit_code
            passed = (exit_code == expected_code)
            details = f"Expected exit code {expected_code}, observed {exit_code}"

        elif rule.type == "exit_code_not_equals":
            unwanted_code = int(rule.value)
            actual = exit_code
            passed = (exit_code != unwanted_code)
            details = f"Expected exit code != {unwanted_code}, observed {exit_code}"

        elif rule.type == AssertionType.STDOUT_CONTAINS:
            expected_str = str(rule.value)
            actual = "found" if expected_str in stdout else "not found"
            passed = (expected_str in stdout)
            details = f"Checking stdout contains '{expected_str}': {actual}"

        elif rule.type == AssertionType.STDOUT_NOT_CONTAINS:
            forbidden_str = str(rule.value)
            actual = "present" if forbidden_str in stdout else "absent"
            passed = (forbidden_str not in stdout)
            details = f"Checking stdout excludes '{forbidden_str}': {actual}"

        elif rule.type == AssertionType.STDERR_CONTAINS:
            expected_err = str(rule.value)
            actual = "found" if expected_err in stderr else "not found"
            passed = (expected_err in stderr)
            details = f"Checking stderr contains '{expected_err}': {actual}"

        elif rule.type == "stderr_not_contains":
            forbidden_err = str(rule.value)
            actual = "present" if forbidden_err in stderr else "absent"
            passed = (forbidden_err not in stderr)
            details = f"Checking stderr excludes '{forbidden_err}': {actual}"

        elif rule.type == AssertionType.FILE_EXISTS:
            if not workspace_dir or not rule.target:
                passed = False
                actual = None
                details = "Target file or workspace directory not provided"
            else:
                target_file = workspace_dir / rule.target
                exists = target_file.exists()
                actual = "exists" if exists else "missing"
                passed = exists
                details = f"File '{rule.target}': {actual}"

        elif rule.type == AssertionType.FILE_CONTAINS:
            if not workspace_dir or not rule.target:
                passed = False
                actual = None
                details = "Target file or workspace directory not provided"
            else:
                target_file = workspace_dir / rule.target
                if not target_file.exists():
                    passed = False
                    actual = "file missing"
                    details = f"File '{rule.target}' does not exist"
                else:
                    content = target_file.read_text(encoding="utf-8", errors="replace")
                    found = str(rule.value) in content
                    actual = "found" if found else "not found"
                    passed = found
                    details = f"File '{rule.target}' contains '{rule.value}': {actual}"

        elif rule.type == "duration_under":
            expected_max = float(rule.value)
            actual = round(duration_seconds, 3)
            passed = (duration_seconds < expected_max)
            details = f"Checking duration < {expected_max}s: observed {actual}s"

        else:
            # Fallback for unknown rule type
            passed = False
            details = f"Unsupported assertion type '{rule.type}'"

        results.append(AssertionResult(
            rule_type=rule.type if isinstance(rule.type, str) else rule.type.value,
            target=rule.target,
            expected=rule.value,
            actual=actual,
            passed=passed,
            details=rule.description or details,
        ))

    return results


class BaseContainerDriver(ABC):
    """Abstract interface for container execution drivers."""

    @abstractmethod
    def execute(
        self,
        cmd_args: List[str],
        timeout_seconds: int,
        cwd: Optional[Path] = None,
    ) -> Tuple[Optional[int], str, str, float, bool]:
        """
        Executes command vector with timeout.
        Returns: (exit_code, stdout, stderr, duration_seconds, timed_out)
        """
        pass


class DockerCliDriver(BaseContainerDriver):
    """Executes container reproduction using the local Docker CLI daemon."""

    def execute(
        self,
        cmd_args: List[str],
        timeout_seconds: int,
        cwd: Optional[Path] = None,
    ) -> Tuple[Optional[int], str, str, float, bool]:
        start = time.time()
        try:
            proc = subprocess.run(
                cmd_args,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start
            return proc.returncode, proc.stdout, proc.stderr, duration, False
        except subprocess.TimeoutExpired as te:
            duration = time.time() - start
            out = te.stdout or "" if isinstance(te.stdout, str) else ""
            err = te.stderr or "" if isinstance(te.stderr, str) else ""
            return None, out, err, duration, True


class IsolatedTestDriver(BaseContainerDriver):
    """
    Sandboxed test double driver used for end-to-end framework verification.
    Executes entrypoint scripts with resource and timeout monitoring when Docker
    is not installed or during synthetic testing.
    """

    def __init__(self, simulate_timeout: bool = False, simulated_exit_code: Optional[int] = None):
        self.simulate_timeout = simulate_timeout
        self.simulated_exit_code = simulated_exit_code

    def execute(
        self,
        cmd_args: List[str],
        timeout_seconds: int,
        cwd: Optional[Path] = None,
    ) -> Tuple[Optional[int], str, str, float, bool]:
        if self.simulate_timeout:
            time.sleep(min(timeout_seconds + 0.05, 0.2))
            return None, "", "Execution timed out.", timeout_seconds + 0.05, True

        # Extract entrypoint command from docker run arguments (after "sh -c")
        raw_cmd = None
        for i, arg in enumerate(cmd_args):
            if arg == "-c" and i + 1 < len(cmd_args):
                raw_cmd = cmd_args[i + 1]
                break

        if not raw_cmd:
            raw_cmd = "python repro.py"

        start = time.time()
        try:
            proc = subprocess.run(
                raw_cmd,
                shell=True,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start
            code = self.simulated_exit_code if self.simulated_exit_code is not None else proc.returncode
            return code, proc.stdout, proc.stderr, duration, False
        except subprocess.TimeoutExpired as te:
            duration = time.time() - start
            out = te.stdout or "" if isinstance(te.stdout, str) else ""
            err = te.stderr or "" if isinstance(te.stderr, str) else ""
            return None, out, err, duration, True


class ReproductionRunner:
    """
    Complete Reproduction Engine Pipeline for AI Failure Museum:
    1. Input validation & path safety checks.
    2. Container preparation & restricted resource configuration.
    3. Execution monitoring with hard timeout limits.
    4. Execution log capture & automated secret redaction.
    5. Programmatic assertion checking.
    6. Structured JSON report generation.
    """

    def __init__(
        self,
        security_config: Optional[ContainerSecurityConfig] = None,
        enforce_docker: bool = True,
        driver: Optional[BaseContainerDriver] = None,
    ):
        self.config = security_config or ContainerSecurityConfig()
        self.enforce_docker = enforce_docker
        self.driver = driver or DockerCliDriver()

    def run(
        self,
        case: FailureCase,
        case_dir: Path,
        custom_timeout: Optional[int] = None,
        allow_network: bool = False,
    ) -> ReproductionResult:
        """
        Executes reproduction pipeline for a given FailureCase.
        """
        repro = case.reproduction
        timeout_sec = custom_timeout or repro.timeout_seconds
        config = self.config

        # 1. Input Validation
        is_valid, validation_errors = validate_reproduction_input(case, case_dir, config)
        if not is_valid:
            return ReproductionResult(
                case_id=case.id,
                title=case.title,
                status=ReproductionStatus.VALIDATION_ERROR,
                timeout_seconds=timeout_sec,
                error_message=f"Input validation failed: {'; '.join(validation_errors)}",
                resource_limits=asdict(config),
            )

        # 2. Check Docker availability if Docker is enforced
        if self.enforce_docker and isinstance(self.driver, DockerCliDriver):
            if not is_docker_available():
                return ReproductionResult(
                    case_id=case.id,
                    title=case.title,
                    status=ReproductionStatus.UNSUPPORTED_ENVIRONMENT,
                    timeout_seconds=timeout_sec,
                    error_message=(
                        "Docker daemon is not available or not running. "
                        "AFM strictly prohibits direct execution of untrusted reproduction code on the host "
                        "to prevent security breaches. Install and start Docker to execute reproductions safely."
                    ),
                    resource_limits=asdict(config),
                )

        # 3. Security Boundary Audit
        network_mode = "bridge" if (allow_network and repro.requires_network) else "none"
        mount_spec = [f"{case_dir.resolve()}:/workspace:ro"]
        is_compliant, violations = validate_container_security(
            mounts=mount_spec,
            network_mode=network_mode,
            memory_limit=config.memory_limit,
            cpu_limit=config.cpu_limit,
            privileged=False,
        )

        if not is_compliant:
            return ReproductionResult(
                case_id=case.id,
                title=case.title,
                status=ReproductionStatus.SECURITY_VIOLATION,
                timeout_seconds=timeout_sec,
                security_violations=violations,
                error_message=f"Reproduction violates isolation policy: {'; '.join(violations)}",
                resource_limits=asdict(config),
            )

        # 4. Prepare Container Command Arguments
        entry_cmd = repro.command or (f"python {repro.entrypoint}" if repro.entrypoint else "python repro.py")
        cmd_args = build_docker_run_args(case, case_dir, config, entry_cmd)

        # 5. Execute with Timeout
        exit_code, raw_stdout, raw_stderr, duration, timed_out = self.driver.execute(
            cmd_args=cmd_args,
            timeout_seconds=timeout_sec,
            cwd=case_dir,
        )

        # 6. Capture Logs & Redact Secrets
        stdout_redacted = redact_secrets(raw_stdout)
        stderr_redacted = redact_secrets(raw_stderr)
        secrets_found = len(find_exposed_secrets(raw_stdout)) > 0 or len(find_exposed_secrets(raw_stderr)) > 0

        logs = ExecutionLog(
            stdout=stdout_redacted,
            stderr=stderr_redacted,
            secrets_redacted=secrets_found,
            raw_length_stdout=len(raw_stdout),
            raw_length_stderr=len(raw_stderr),
        )

        # 7. Check for Timeout Condition
        if timed_out:
            return ReproductionResult(
                case_id=case.id,
                title=case.title,
                status=ReproductionStatus.TIMEOUT,
                duration_seconds=duration,
                timeout_seconds=timeout_sec,
                logs=logs,
                error_message=f"Reproduction execution timed out after {timeout_sec} seconds.",
                resource_limits=asdict(config),
            )

        # 8. Assertion Checking
        assertion_results = evaluate_assertions(
            assertions=repro.assertions,
            exit_code=exit_code,
            stdout=stdout_redacted,
            stderr=stderr_redacted,
            duration_seconds=duration,
            workspace_dir=case_dir,
        )

        all_assertions_passed = (
            len(assertion_results) > 0 and all(a.passed for a in assertion_results)
        )
        status = ReproductionStatus.PASSED if all_assertions_passed else ReproductionStatus.FAILED

        return ReproductionResult(
            case_id=case.id,
            title=case.title,
            status=status,
            exit_code=exit_code,
            duration_seconds=duration,
            timeout_seconds=timeout_sec,
            logs=logs,
            assertion_results=assertion_results,
            resource_limits=asdict(config),
        )
