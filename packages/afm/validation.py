"""
Validation engine for AI Failure Museum definitions.
Validates case files against Pydantic models, JSON Schema, and integrity checks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import ValidationError

from afm.models import FailureCase
from afm.security import find_exposed_secrets, resolve_safe_path


@dataclass
class ValidationResult:
    """Represents the outcome of validating a single failure case file."""
    path: Path
    valid: bool
    case_id: Optional[str] = None
    case: Optional[FailureCase] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASSED" if self.valid else "FAILED"
        prefix = f"[{status}] {self.path.name}"
        if self.case_id:
            prefix = f"[{status}] {self.case_id} ({self.path.name})"
        return prefix


def validate_case_file(
    path: Union[str, Path],
    schema_path: Optional[Path] = None,
    verify_references: bool = True,
    strict_secrets: bool = True,
) -> ValidationResult:
    """
    Validates a YAML case file against the FailureCase schema and integrity rules.
    """
    case_file = Path(path).resolve()
    result = ValidationResult(path=case_file, valid=True)

    if not case_file.exists():
        result.valid = False
        result.errors.append(f"File not found: {case_file}")
        return result

    # 1. Parse YAML safely
    try:
        with open(case_file, "r", encoding="utf-8") as f:
            raw_content = f.read()
            data = yaml.safe_load(raw_content)
    except yaml.YAMLError as exc:
        result.valid = False
        result.errors.append(f"YAML parsing error: {exc}")
        return result
    except Exception as exc:
        result.valid = False
        result.errors.append(f"Failed to read file: {exc}")
        return result

    if not isinstance(data, dict):
        result.valid = False
        result.errors.append("Case definition must be a YAML dictionary.")
        return result

    # 2. Check for exposed secrets in raw text
    secret_warnings = find_exposed_secrets(raw_content)
    if secret_warnings:
        if strict_secrets:
            result.valid = False
            result.errors.extend([f"Security Violation: {w}" for w in secret_warnings])
        else:
            result.warnings.extend([f"Security Warning: {w}" for w in secret_warnings])

    # 3. Validate with Pydantic model
    try:
        case = FailureCase.model_validate(data)
        result.case = case
        result.case_id = case.id
    except ValidationError as exc:
        result.valid = False
        for err in exc.errors():
            loc = " -> ".join(str(p) for p in err["loc"])
            msg = err["msg"]
            result.errors.append(f"Field '{loc}': {msg}")
        return result

    # 4. Optional JSON Schema validation for draft compliance
    if schema_path and schema_path.exists():
        try:
            import jsonschema

            with open(schema_path, "r", encoding="utf-8") as sf:
                schema_dict = json.load(sf)
            jsonschema.validate(instance=data, schema=schema_dict)
        except Exception as exc:
            result.warnings.append(f"JSON Schema discrepancy: {exc}")

    # 5. Verify local referenced files if requested
    if verify_references and result.case:
        case_dir = case_file.parent

        # Verify reproduction entrypoint
        if result.case.reproduction.entrypoint:
            entrypoint = result.case.reproduction.entrypoint
            try:
                ep_path = resolve_safe_path(case_dir, entrypoint)
                if not ep_path.exists():
                    result.warnings.append(
                        f"Referenced reproduction entrypoint '{entrypoint}' does not exist at {ep_path}"
                    )
            except ValueError as ve:
                result.valid = False
                result.errors.append(str(ve))

        # Verify evidence files (if local relative path)
        for ev in result.case.evidence:
            if not (ev.path_or_url.startswith("http://") or ev.path_or_url.startswith("https://")):
                try:
                    ev_path = resolve_safe_path(case_dir, ev.path_or_url)
                    if not ev_path.exists():
                        result.warnings.append(f"Evidence file '{ev.path_or_url}' not found at {ev_path}")
                except ValueError as ve:
                    result.valid = False
                    result.errors.append(str(ve))

    return result
