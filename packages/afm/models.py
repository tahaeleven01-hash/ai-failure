"""
Pydantic data models for the AI Failure Museum (AFM).
Defines schemas for failure cases, taxonomy, metadata, reproduction instructions,
and assertion rules.
"""

from __future__ import annotations

import datetime
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CaseStatus(str, Enum):
    """Lifecycle status of a failure case in the registry."""
    SUBMITTED = "submitted"
    VALIDATED = "validated"
    REPRODUCIBLE = "reproducible"
    NON_REPRODUCIBLE = "non-reproducible"
    ARCHIVED = "archived"


class FailureCategory(str, Enum):
    """Extensible taxonomy of AI agent failure categories."""
    HALLUCINATED_API = "hallucinated-api"
    INCORRECT_CODE_MODIFICATION = "incorrect-code-modification"
    DESTRUCTIVE_FILE_OPERATION = "destructive-file-operation"
    DEPENDENCY_CONFLICT = "dependency-conflict"
    FAILED_BUG_FIX = "failed-bug-fix"
    INCORRECT_TEST_GENERATION = "incorrect-test-generation"
    SECURITY_REGRESSION = "security-regression"
    CONTEXT_MISUNDERSTANDING = "context-misunderstanding"
    INSTRUCTION_FOLLOWING_FAILURE = "instruction-following-failure"
    FALSE_SUCCESS_CLAIM = "false-success-claim"
    ENVIRONMENT_CONFIGURATION_FAILURE = "environment-configuration-failure"


class EvidenceType(str, Enum):
    """Format or media type of failure evidence."""
    LOG = "log"
    DIFF = "diff"
    SCREENSHOT = "screenshot"
    RECORDING = "recording"
    LINK = "link"


class AssertionType(str, Enum):
    """Types of assertion rules used to verify reproduction outcomes."""
    EXIT_CODE_EQUALS = "exit_code_equals"
    EXIT_CODE_NOT_EQUALS = "exit_code_not_equals"
    STDOUT_CONTAINS = "stdout_contains"
    STDOUT_NOT_CONTAINS = "stdout_not_contains"
    STDERR_CONTAINS = "stderr_contains"
    STDERR_NOT_CONTAINS = "stderr_not_contains"
    FILE_EXISTS = "file_exists"
    FILE_CONTAINS = "file_contains"
    DURATION_UNDER = "duration_under"


class AgentMetadata(BaseModel):
    """Metadata regarding the original AI agent that exhibited the failure."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Name of the AI agent (e.g. Claude Code, Codex, DevAgent)")
    version: Optional[str] = Field(None, description="Reported version of the agent or CLI tool")
    model: Optional[str] = Field(None, description="Underlying foundation model if known (e.g. claude-3-5-sonnet)")
    provider: Optional[str] = Field(None, description="Entity or vendor providing the agent")


class TaskDefinition(BaseModel):
    """The original prompt, goal, and context provided to the agent."""
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(..., min_length=5, description="Exact or summarized user prompt passed to the agent")
    context: Optional[str] = Field(None, description="Additional context, repository state, or instructions given")
    target_repository: Optional[str] = Field(None, description="Public repository or synthetic project targeted")
    target_files: List[str] = Field(default_factory=list, description="Files intended to be inspected or edited")


class BehaviorComparison(BaseModel):
    """Comparative contrast between what was expected and what actually occurred."""
    model_config = ConfigDict(extra="forbid")

    expected: str = Field(..., min_length=5, description="Documented correct or expected behavior")
    observed: str = Field(..., min_length=5, description="Actual flawed behavior observed during the session")


class EnvironmentSpecification(BaseModel):
    """Host or container execution environment details."""
    model_config = ConfigDict(extra="forbid")

    os: Optional[str] = Field(None, description="Operating system where failure occurred (e.g. Ubuntu 22.04, Linux)")
    runtime: Optional[str] = Field(None, description="Runtime and version (e.g. Python 3.11, Node.js 20)")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Key packages and versions")
    docker_image: Optional[str] = Field(None, description="Docker image required or recommended for reproduction")


class AssertionRule(BaseModel):
    """A programmatic check to confirm that the failure reproduced."""
    model_config = ConfigDict(extra="forbid")

    type: AssertionType = Field(..., description="Assertion check type")
    target: Optional[str] = Field(None, description="File path or target when applicable")
    value: Union[str, int, float] = Field(..., description="Expected value, regex, substring, status code, or threshold")
    description: Optional[str] = Field(None, description="Human explanation of what this assertion tests")


class ReproductionProcedure(BaseModel):
    """Specification of how to execute the reproduction in an isolated environment."""
    model_config = ConfigDict(extra="forbid")

    type: str = Field(default="docker", description="Reproduction execution strategy ('docker', 'script', 'manual')")
    entrypoint: Optional[str] = Field(None, description="Script or command file inside the case directory")
    command: Optional[str] = Field(None, description="Inline command to run within the container")
    working_dir: Optional[str] = Field(None, description="Working directory inside container (e.g. /workspace)")
    timeout_seconds: int = Field(default=60, ge=1, le=600, description="Maximum execution timeout in seconds")
    assertions: List[AssertionRule] = Field(default_factory=list, description="Assertions to confirm failure reproduced")
    requires_network: bool = Field(default=False, description="Whether network access is strictly required")
    requires_docker: bool = Field(default=True, description="Whether Docker is required for safe execution")


class VerificationMethod(BaseModel):
    """Methodology for verifying whether the failure or fix is valid."""
    model_config = ConfigDict(extra="forbid")

    method_type: str = Field(..., description="Verification approach (e.g. 'automated-test', 'static-analysis', 'manual-audit')")
    test_runner: Optional[str] = Field(None, description="Test runner command (e.g. pytest, npm test)")
    expected_exit_code: Optional[int] = Field(None, description="Expected exit code when reproducing failure")
    failure_criteria: str = Field(..., min_length=5, description="Clear criteria defining reproduction success")


class EvidenceReference(BaseModel):
    """Pointers to artifacts, terminal logs, or recordings demonstrating the failure."""
    model_config = ConfigDict(extra="forbid")

    type: EvidenceType = Field(..., description="Evidence category")
    path_or_url: str = Field(..., description="Relative file path within case directory or verifiable URL")
    description: Optional[str] = Field(None, description="Contextual note describing the evidence")


class SubmissionMetadata(BaseModel):
    """Authorship and submission details."""
    model_config = ConfigDict(extra="forbid")

    submitted_by: str = Field(..., min_length=2, description="GitHub username or handle of the submitter")
    date: datetime.date = Field(..., description="Submission date (YYYY-MM-DD)")
    updated_date: Optional[datetime.date] = Field(None, description="Last update date")
    original_pr_or_issue: Optional[str] = Field(None, description="Link to original issue or pull request")


class FailureCase(BaseModel):
    """
    Complete specification of an AI Agent Failure Case.
    Every case in the museum must conform to this schema.
    """
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique case identifier (e.g. AFM-0001 or SYN-0001)")
    title: str = Field(..., min_length=5, max_length=150, description="Short, descriptive title of the failure")
    description: str = Field(..., min_length=10, description="Comprehensive summary of what occurred")
    categories: List[FailureCategory] = Field(..., min_length=1, description="List of relevant failure categories")
    status: CaseStatus = Field(default=CaseStatus.SUBMITTED, description="Current verification lifecycle status")
    is_synthetic: bool = Field(default=False, description="Explicit flag indicating whether case is synthetic")
    agent: AgentMetadata = Field(..., description="AI Agent details")
    task: TaskDefinition = Field(..., description="Original task prompt and context")
    behavior: BehaviorComparison = Field(..., description="Expected vs observed behavior")
    environment: EnvironmentSpecification = Field(default_factory=EnvironmentSpecification, description="Execution environment")
    reproduction: ReproductionProcedure = Field(default_factory=ReproductionProcedure, description="Reproduction instructions")
    verification: VerificationMethod = Field(..., description="Verification method and criteria")
    evidence: List[EvidenceReference] = Field(default_factory=list, description="Evidence items")
    submission: SubmissionMetadata = Field(..., description="Submission metadata")
    tags: List[str] = Field(default_factory=list, description="Optional discovery tags")

    @field_validator("id")
    @classmethod
    def validate_case_id(cls, v: str) -> str:
        pattern = r"^(AFM|SYN)-\d{4}$"
        if not re.match(pattern, v):
            raise ValueError(f"Case ID '{v}' is invalid. Must match pattern '{pattern}' (e.g. AFM-0001 or SYN-0001).")
        return v

    @field_validator("is_synthetic")
    @classmethod
    def validate_synthetic_id_alignment(cls, v: bool, info: Any) -> bool:
        case_id = info.data.get("id")
        if case_id:
            if case_id.startswith("SYN-") and not v:
                raise ValueError("Cases with ID prefix 'SYN-' must have 'is_synthetic: true'.")
            if case_id.startswith("AFM-") and v:
                raise ValueError("Cases with ID prefix 'AFM-' cannot have 'is_synthetic: true'. Use 'SYN-' prefix for synthetic cases.")
        return v
