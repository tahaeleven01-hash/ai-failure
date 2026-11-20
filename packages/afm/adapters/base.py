"""
Pluggable Agent Adapter Interface for AI Failure Museum.
Defines base class and data structures for invoking AI coding agents in evaluation pipelines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class AgentExecutionOutput:
    """Raw output and state modifications captured from an agent run."""
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    modified_files: List[str] = field(default_factory=list)
    diff: Optional[str] = None
    error_message: Optional[str] = None


class BaseAdapter(ABC):
    """
    Abstract interface for AI agent runners (CLI or API-driven).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier of the adapter (e.g. 'mock', 'claude-code', 'gemini-cli')."""
        pass

    @property
    def is_mock(self) -> bool:
        """Indicates whether this adapter is a mock/synthetic test double."""
        return False

    @property
    def version(self) -> str:
        """Version of the adapter implementation."""
        return "0.1.0"

    @abstractmethod
    def run_agent(
        self,
        task_prompt: str,
        context: Optional[str],
        workspace_dir: Path,
        timeout_seconds: int = 120,
    ) -> AgentExecutionOutput:
        """
        Executes the agent against the specified workspace and task prompt.
        """
        pass
