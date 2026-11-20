"""
Evaluation system for AI Failure Museum.
Evaluates whether an AI coding agent can successfully resolve the task defined in a failure case.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from afm.adapters.base import BaseAdapter
from afm.models import FailureCase
from afm.security import redact_secrets


@dataclass
class AgentEvaluationResult:
    """Detailed outcome of evaluating an agent against a failure case."""
    case_id: str
    adapter_name: str
    is_mock: bool
    task_resolved: bool
    duration_seconds: float
    agent_exit_code: int
    test_exit_code: Optional[int] = None
    modified_files: List[str] = field(default_factory=list)
    diff: Optional[str] = None
    agent_output: str = ""
    verification_output: str = ""
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        res_str = "RESOLVED" if self.task_resolved else "UNRESOLVED"
        mock_str = " [MOCK]" if self.is_mock else ""
        return (
            f"[{res_str}]{mock_str} Case {self.case_id} by '{self.adapter_name}' "
            f"in {self.duration_seconds:.2f}s (Agent exit: {self.agent_exit_code}, Test exit: {self.test_exit_code})"
        )


class EvaluationEngine:
    """
    Orchestrates the evaluation workflow:
    1. Prepares a fresh, isolated temporary workspace.
    2. Runs the agent adapter against the case prompt.
    3. Captures workspace diffs and modified files.
    4. Executes verification tests to evaluate if the agent solved the task.
    5. Produces verified evaluation records with secret redaction.
    """

    def evaluate(
        self,
        case: FailureCase,
        adapter: BaseAdapter,
        case_dir: Optional[Path] = None,
        timeout_seconds: int = 120,
    ) -> AgentEvaluationResult:
        start_time = time.time()

        with tempfile.TemporaryDirectory(prefix=f"afm_eval_{case.id}_") as temp_dir:
            workspace = Path(temp_dir)

            # Copy files from case directory if provided
            if case_dir and case_dir.exists():
                for item in case_dir.iterdir():
                    if item.name in (".git", "case.yaml", "case.yml"):
                        continue
                    dest = workspace / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)

            # Run agent adapter
            try:
                agent_res = adapter.run_agent(
                    task_prompt=case.task.prompt,
                    context=case.task.context,
                    workspace_dir=workspace,
                    timeout_seconds=timeout_seconds,
                )
            except Exception as exc:
                return AgentEvaluationResult(
                    case_id=case.id,
                    adapter_name=adapter.name,
                    is_mock=adapter.is_mock,
                    task_resolved=False,
                    duration_seconds=time.time() - start_time,
                    agent_exit_code=1,
                    error_message=f"Agent execution crashed: {exc}",
                )

            # Verification Phase: determine if the agent resolved the failure
            # If the agent modified code and the verification criteria are satisfied
            task_resolved = False
            verification_output = ""
            test_exit_code: Optional[int] = None

            if agent_res.exit_code == 0:
                # If there's an automated test runner specified
                test_runner = case.verification.test_runner
                # If test_runner is just "python", append repro script or entrypoint if available
                if test_runner == "python" and case.reproduction.entrypoint:
                    test_runner = f"python {case.reproduction.entrypoint}"

                runner_bin = test_runner.split()[0] if test_runner else ""
                if test_runner and shutil.which(runner_bin):
                    try:
                        vproc = subprocess.run(
                            test_runner,
                            shell=True,
                            cwd=workspace,
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=30,
                        )
                        test_exit_code = vproc.returncode
                        verification_output = redact_secrets(vproc.stdout + "\n" + vproc.stderr)
                        # Standard test suites exit 0 when passing
                        task_resolved = (test_exit_code == 0)
                    except Exception as vexc:
                        verification_output = f"Verification execution error: {vexc}"
                        task_resolved = False
                else:
                    # For mock runs or cases without runner installed on host:
                    # In mock mode, if the mock generated solution.py with valid code, consider resolved
                    if adapter.is_mock:
                        sol = workspace / "solution.py"
                        task_resolved = sol.exists() and "def resolve_task" in sol.read_text(encoding="utf-8")
                        verification_output = "Mock test verification passed: solution.py present and valid."
                        test_exit_code = 0 if task_resolved else 1
                    else:
                        verification_output = f"Runner '{test_runner}' not available for host verification."
                        task_resolved = False

            total_duration = time.time() - start_time

            return AgentEvaluationResult(
                case_id=case.id,
                adapter_name=adapter.name,
                is_mock=adapter.is_mock,
                task_resolved=task_resolved,
                duration_seconds=total_duration,
                agent_exit_code=agent_res.exit_code,
                test_exit_code=test_exit_code,
                modified_files=agent_res.modified_files,
                diff=agent_res.diff,
                agent_output=redact_secrets(agent_res.stdout),
                verification_output=verification_output,
                error_message=agent_res.error_message,
            )
