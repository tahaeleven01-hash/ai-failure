"""
Reporting engine for AI Failure Museum.
Formats failure cases, reproduction logs, and evaluation benchmarks into
human-readable Markdown or machine-readable JSON.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from afm.models import FailureCase
from afm.registry import RegistryStats


def format_case_markdown(case: FailureCase) -> str:
    """Renders a comprehensive, technical Markdown report of a failure case."""
    synthetic_badge = " *(Synthetic Test Case)*" if case.is_synthetic else ""
    categories_str = ", ".join(f"`{c.value}`" for c in case.categories)
    tags_str = ", ".join(case.tags) if case.tags else "None"

    lines = [
        f"# [{case.id}] {case.title}{synthetic_badge}",
        "",
        f"**Status:** `{case.status.value}` | **Categories:** {categories_str} | **Date:** {case.submission.date}",
        f"**Submitted by:** @{case.submission.submitted_by} | **Tags:** {tags_str}",
        "",
        "## Summary",
        case.description,
        "",
        "## Agent Profile",
        f"- **Name:** {case.agent.name}",
        f"- **Version:** {case.agent.version or 'Unspecified'}",
        f"- **Model:** {case.agent.model or 'Unspecified'}",
        f"- **Provider:** {case.agent.provider or 'Unspecified'}",
        "",
        "## Original Task & Prompt",
        "```text",
        case.task.prompt,
        "```",
    ]

    if case.task.context:
        lines.extend([
            "",
            "### Context",
            f"> {case.task.context}",
        ])

    if case.task.target_files:
        lines.extend([
            "",
            "### Target Files",
            *(f"- `{f}`" for f in case.task.target_files),
        ])

    lines.extend([
        "",
        "## Behavior Contrast",
        "| Aspect | Description |",
        "|---|---|",
        f"| **Expected Behavior** | {case.behavior.expected} |",
        f"| **Observed Behavior** | {case.behavior.observed} |",
        "",
        "## Execution Environment",
        f"- **OS:** {case.environment.os or 'Any / POSIX'}",
        f"- **Runtime:** {case.environment.runtime or 'Default'}",
        f"- **Docker Image:** `{case.environment.docker_image or 'None specified'}`",
    ])

    if case.environment.dependencies:
        lines.append("- **Dependencies:**")
        for pkg, ver in case.environment.dependencies.items():
            lines.append(f"  - `{pkg}`: `{ver}`")

    lines.extend([
        "",
        "## Reproduction Procedure",
        f"- **Type:** `{case.reproduction.type}`",
        f"- **Entrypoint:** `{case.reproduction.entrypoint or 'Inline command'}`",
        f"- **Command:** `{case.reproduction.command or 'N/A'}`",
        f"- **Timeout:** {case.reproduction.timeout_seconds} seconds",
        f"- **Network Required:** {'Yes' if case.reproduction.requires_network else 'No (Isolated)'}",
        f"- **Docker Required:** {'Yes' if case.reproduction.requires_docker else 'No'}",
        "",
        "### Reproduction Assertions",
    ])

    if case.reproduction.assertions:
        for idx, a in enumerate(case.reproduction.assertions, 1):
            desc = f" — {a.description}" if a.description else ""
            lines.append(f"{idx}. **{a.type.value}**: `{a.value}`{desc}")
    else:
        lines.append("*No automated assertions defined.*")

    lines.extend([
        "",
        "## Verification Criteria",
        f"- **Method Type:** `{case.verification.method_type}`",
        f"- **Expected Exit Code:** `{case.verification.expected_exit_code}`",
        f"- **Criteria:** {case.verification.failure_criteria}",
        "",
        "## Attached Evidence",
    ])

    if case.evidence:
        for ev in case.evidence:
            desc = f" — {ev.description}" if ev.description else ""
            lines.append(f"- **[{ev.type.value.upper()}]** `{ev.path_or_url}`{desc}")
    else:
        lines.append("*No evidence files attached.*")

    return "\n".join(lines)


def format_stats_markdown(stats: RegistryStats) -> str:
    """Formats registry statistics into Markdown summary."""
    lines = [
        "# AI Failure Museum — Registry Statistics",
        "",
        f"- **Total Cases:** {stats.total_cases}",
        f"- **Real Cases:** {stats.real_cases}",
        f"- **Synthetic Cases:** {stats.synthetic_cases}",
        f"- **Reproducible Cases:** {stats.reproducible_cases}",
        "",
        "## Cases by Status",
    ]
    for status, count in sorted(stats.status_counts.items()):
        lines.append(f"- `{status}`: {count}")

    lines.extend(["", "## Cases by Category"])
    for cat, count in sorted(stats.category_counts.items()):
        lines.append(f"- `{cat}`: {count}")

    lines.extend(["", "## Cases by Agent"])
    for agent, count in sorted(stats.agent_counts.items()):
        lines.append(f"- `{agent}`: {count}")

    return "\n".join(lines)
