"""
Registry management for AI Failure Museum.
Handles discovery, loading, duplicate detection, querying, and statistics calculation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from afm.models import CaseStatus, FailureCase, FailureCategory
from afm.validation import validate_case_file


class RegistryError(Exception):
    """Base error for registry operations."""
    pass


class DuplicateCaseIdError(RegistryError):
    """Raised when two failure cases declare the same identifier."""
    pass


class CaseNotFoundError(RegistryError):
    """Raised when a requested case ID is not found in the registry."""
    pass


@dataclass
class RegistryStats:
    """Aggregated metrics across all registered failure cases."""
    total_cases: int = 0
    real_cases: int = 0
    synthetic_cases: int = 0
    reproducible_cases: int = 0
    status_counts: Dict[str, int] = field(default_factory=dict)
    category_counts: Dict[str, int] = field(default_factory=dict)
    agent_counts: Dict[str, int] = field(default_factory=dict)


class FailureRegistry:
    """
    In-memory registry of failure cases discovered from filesystem directories.
    """

    def __init__(self, search_paths: Optional[List[Path]] = None):
        self.search_paths: List[Path] = search_paths or []
        self._cases: Dict[str, FailureCase] = {}
        self._case_files: Dict[str, Path] = {}
        self._load_errors: List[Dict[str, Any]] = []

    @classmethod
    def from_workspace(cls, root_dir: Path) -> FailureRegistry:
        """
        Creates a registry instance scanning standard AFM directories:
        - <root>/failures
        - <root>/examples/synthetic
        """
        paths = [
            root_dir / "failures",
            root_dir / "examples" / "synthetic",
        ]
        registry = cls([p for p in paths if p.exists()])
        registry.load()
        return registry

    def load(self, strict: bool = False) -> None:
        """
        Scans all configured search paths, parses YAML files, and populates registry.
        Enforces unique identifiers across all cases.
        """
        self._cases.clear()
        self._case_files.clear()
        self._load_errors.clear()

        discovered_ids: Set[str] = set()

        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            for file_path in search_path.rglob("*.y*ml"):
                # Skip hidden files or lockfiles
                if file_path.name.startswith("."):
                    continue

                res = validate_case_file(file_path, verify_references=False)
                if not res.valid or not res.case:
                    self._load_errors.append({
                        "file": str(file_path),
                        "errors": res.errors,
                    })
                    if strict:
                        raise RegistryError(f"Failed to load case at {file_path}: {'; '.join(res.errors)}")
                    continue

                case = res.case
                if case.id in discovered_ids:
                    prev_path = self._case_files[case.id]
                    msg = (
                        f"Duplicate case ID detected: '{case.id}'. "
                        f"Found in both '{prev_path}' and '{file_path}'."
                    )
                    if strict:
                        raise DuplicateCaseIdError(msg)
                    self._load_errors.append({"file": str(file_path), "errors": [msg]})
                    continue

                discovered_ids.add(case.id)
                self._cases[case.id] = case
                self._case_files[case.id] = file_path

    @property
    def cases(self) -> List[FailureCase]:
        """Returns all loaded failure cases sorted by ID."""
        return sorted(self._cases.values(), key=lambda c: c.id)

    @property
    def load_errors(self) -> List[Dict[str, Any]]:
        """List of files that failed validation during loading."""
        return self._load_errors

    def get(self, case_id: str) -> FailureCase:
        """Retrieves a failure case by ID or raises CaseNotFoundError."""
        clean_id = case_id.strip().upper()
        if clean_id not in self._cases:
            raise CaseNotFoundError(f"Case '{clean_id}' does not exist in the registry.")
        return self._cases[clean_id]

    def get_file_path(self, case_id: str) -> Optional[Path]:
        """Returns the file path for a given case ID."""
        clean_id = case_id.strip().upper()
        return self._case_files.get(clean_id)

    def query(
        self,
        text: Optional[str] = None,
        category: Optional[Union[str, FailureCategory]] = None,
        status: Optional[Union[str, CaseStatus]] = None,
        agent: Optional[str] = None,
        is_synthetic: Optional[bool] = None,
        reproducible_only: bool = False,
    ) -> List[FailureCase]:
        """
        Filters registry cases according to matching criteria.
        """
        results = self.cases

        if is_synthetic is not None:
            results = [c for c in results if c.is_synthetic == is_synthetic]

        if category:
            cat_str = category.value if isinstance(category, FailureCategory) else str(category).lower()
            results = [c for c in results if any(k.value == cat_str for k in c.categories)]

        if status:
            stat_str = status.value if isinstance(status, CaseStatus) else str(status).lower()
            results = [c for c in results if c.status.value == stat_str]

        if agent:
            agent_lower = agent.lower()
            results = [c for c in results if agent_lower in c.agent.name.lower()]

        if reproducible_only:
            results = [c for c in results if c.status == CaseStatus.REPRODUCIBLE]

        if text:
            q = text.lower()
            filtered = []
            for c in results:
                matchable = (
                    f"{c.id} {c.title} {c.description} {c.agent.name} "
                    f"{' '.join(k.value for k in c.categories)} {' '.join(c.tags)}"
                ).lower()
                if q in matchable:
                    filtered.append(c)
            results = filtered

        return results

    def statistics(self) -> RegistryStats:
        """Computes verified statistical summary of the registry."""
        stats = RegistryStats(
            total_cases=len(self._cases),
            synthetic_cases=sum(1 for c in self._cases.values() if c.is_synthetic),
            real_cases=sum(1 for c in self._cases.values() if not c.is_synthetic),
            reproducible_cases=sum(1 for c in self._cases.values() if c.status == CaseStatus.REPRODUCIBLE),
        )

        for case in self._cases.values():
            # Status count
            st = case.status.value
            stats.status_counts[st] = stats.status_counts.get(st, 0) + 1

            # Category count
            for cat in case.categories:
                stats.category_counts[cat.value] = stats.category_counts.get(cat.value, 0) + 1

            # Agent count
            ag = case.agent.name
            stats.agent_counts[ag] = stats.agent_counts.get(ag, 0) + 1

        return stats

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Exports all registered cases as serializable dictionaries."""
        return [case.model_dump(mode="json") for case in self.cases]

    def export_json(self, destination: Path) -> None:
        """Dumps entire registry into a formatted JSON file."""
        stats = self.statistics()
        data = {
            "version": "0.1.0",
            "statistics": {
                "total_cases": stats.total_cases,
                "real_cases": stats.real_cases,
                "synthetic_cases": stats.synthetic_cases,
                "reproducible_cases": stats.reproducible_cases,
                "status_counts": stats.status_counts,
                "category_counts": stats.category_counts,
                "agent_counts": stats.agent_counts,
            },
            "cases": self.to_dict_list(),
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
