"""
Command Line Interface for AI Failure Museum (AFM).
Built with Typer and Rich for clear diagnostics, tabular views, and interactive wizards.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from afm.adapters import get_adapter, list_adapters
from afm.evaluation import EvaluationEngine
from afm.models import CaseStatus, FailureCategory
from afm.registry import FailureRegistry
from afm.reporting import format_case_markdown, format_stats_markdown
from afm.runner import ReproductionRunner, ReproductionStatus, is_docker_available
from afm.validation import validate_case_file

app = typer.Typer(
    name="afm",
    help="AI Failure Museum — Production-quality AI agent failure registry and reproduction engine.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def get_workspace_root() -> Path:
    """Finds workspace root containing pyproject.toml or failures/."""
    current = Path.cwd().resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / "failures").exists():
            return parent
    return current


@app.command("list")
def list_cases(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by failure category"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (submitted, reproducible, etc.)"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Filter by agent name"),
    search: Optional[str] = typer.Option(None, "--search", "-q", help="Free text search query"),
    synthetic: Optional[bool] = typer.Option(None, "--synthetic/--no-synthetic", help="Filter synthetic cases"),
    format_output: str = typer.Option("table", "--format", "-f", help="Output format: table or json"),
) -> None:
    """List registered AI agent failure cases with filters."""
    root = get_workspace_root()
    registry = FailureRegistry.from_workspace(root)

    cases = registry.query(
        text=search,
        category=category,
        status=status,
        agent=agent,
        is_synthetic=synthetic,
    )

    if format_output.lower() == "json":
        data = [c.model_dump(mode="json") for c in cases]
        typer.echo(json.dumps(data, indent=2))
        return

    if not cases:
        rprint("[yellow]No failure cases matched the specified criteria.[/yellow]")
        return

    table = Table(title=f"AI Failure Museum Registry ({len(cases)} cases)", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="bold cyan", width=10)
    table.add_column("Title", style="white", min_width=30)
    table.add_column("Agent", style="blue")
    table.add_column("Categories", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Type", style="dim")

    for c in cases:
        cats = ", ".join(k.value for k in c.categories[:2])
        if len(c.categories) > 2:
            cats += f" (+{len(c.categories) - 2})"
        c_type = "Synthetic" if c.is_synthetic else "Real"
        table.add_row(
            c.id,
            c.title[:45] + ("..." if len(c.title) > 45 else ""),
            c.agent.name,
            cats,
            c.status.value,
            c_type,
        )

    console.print(table)


@app.command("show")
def show_case(
    case_id: str = typer.Argument(..., help="Case identifier (e.g. AFM-0001 or SYN-0001)"),
    format_output: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
) -> None:
    """Display comprehensive details of a specific failure case."""
    root = get_workspace_root()
    registry = FailureRegistry.from_workspace(root)

    try:
        case = registry.get(case_id)
    except Exception as exc:
        rprint(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    if format_output.lower() == "json":
        typer.echo(json.dumps(case.model_dump(mode="json"), indent=2))
        return

    md_content = format_case_markdown(case)
    console.print(Panel(md_content, title=f"Case Details: {case.id}", border_style="cyan"))


@app.command("validate")
def validate(
    case_id: Optional[str] = typer.Argument(None, help="Specific case ID to validate (or validate all if omitted)"),
    strict: bool = typer.Option(True, "--strict/--no-strict", help="Fail validation on exposed secrets and syntax warnings"),
) -> None:
    """Validate failure case metadata and schemas."""
    root = get_workspace_root()
    registry = FailureRegistry.from_workspace(root)
    schema_path = root / "schemas" / "failure-case.schema.json"

    files_to_validate = []

    if case_id:
        try:
            case_file = registry.get_file_path(case_id)
            if not case_file:
                rprint(f"[bold red]Error:[/bold red] Case file for '{case_id}' could not be located.")
                raise typer.Exit(code=1)
            files_to_validate.append(case_file)
        except Exception as exc:
            rprint(f"[bold red]Error:[/bold red] {exc}")
            raise typer.Exit(code=1)
    else:
        # Collect all YAML files under failures/ and examples/
        for sp in [root / "failures", root / "examples" / "synthetic"]:
            if sp.exists():
                files_to_validate.extend(list(sp.rglob("*.y*ml")))

    if not files_to_validate:
        rprint("[yellow]No case files found to validate.[/yellow]")
        return

    all_passed = True
    table = Table(title="Validation Summary", show_header=True)
    table.add_column("File / Case", style="cyan")
    table.add_column("Result", style="bold")
    table.add_column("Issues / Diagnostics", style="white")

    for fpath in files_to_validate:
        res = validate_case_file(fpath, schema_path=schema_path, verify_references=True, strict_secrets=strict)
        if not res.valid:
            all_passed = False
            issues = "\n".join(f"[red]• {err}[/red]" for err in res.errors)
            table.add_row(f"{res.case_id or fpath.name}", "[bold red]FAIL[/bold red]", issues)
        else:
            warnings = "\n".join(f"[yellow]• {w}[/yellow]" for w in res.warnings) if res.warnings else "[green]None[/green]"
            table.add_row(f"{res.case_id or fpath.name}", "[bold green]PASS[/bold green]", warnings)

    console.print(table)

    if not all_passed:
        rprint("\n[bold red]Validation failed for one or more cases.[/bold red]")
        raise typer.Exit(code=1)
    else:
        rprint("\n[bold green]All validated cases conform to specification.[/bold green]")


@app.command("reproduce")
def reproduce(
    case_id: str = typer.Argument(..., help="Case identifier to reproduce"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Override execution timeout in seconds"),
    memory: str = typer.Option("512m", "--memory", "-m", help="Container memory limit (e.g. 512m, 1g)"),
    cpus: float = typer.Option(1.0, "--cpus", help="Container CPU cores limit"),
    pids: int = typer.Option(100, "--pids", help="Container maximum process limit"),
    allow_network: bool = typer.Option(False, "--allow-network", help="Allow container network access if requested"),
    format_output: str = typer.Option("table", "--format", "-f", help="Output format: table or json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="File to write structured JSON report to"),
    test_driver: bool = typer.Option(False, "--test-driver", help="Use isolated test driver for synthetic case verification"),
) -> None:
    """Reproduce a failure in a restricted container sandbox."""
    root = get_workspace_root()
    registry = FailureRegistry.from_workspace(root)

    try:
        case = registry.get(case_id)
        case_file = registry.get_file_path(case_id)
    except Exception as exc:
        rprint(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    case_dir = case_file.parent if case_file else root

    from afm.runner import ContainerSecurityConfig, IsolatedTestDriver, DockerCliDriver

    sec_config = ContainerSecurityConfig(
        memory_limit=memory,
        memory_swap=memory,
        cpu_limit=cpus,
        pids_limit=pids,
        network_mode="bridge" if allow_network else "none",
    )

    driver = IsolatedTestDriver() if test_driver else DockerCliDriver()
    runner = ReproductionRunner(
        security_config=sec_config,
        enforce_docker=not test_driver,
        driver=driver,
    )

    if format_output != "json":
        rprint(f"[bold cyan]Initiating reproduction for {case.id}...[/bold cyan]")
        rprint(f"[dim]Resource constraints: memory={memory}, cpus={cpus}, pids={pids}, network={sec_config.network_mode}[/dim]")

    res = runner.run(case=case, case_dir=case_dir, custom_timeout=timeout, allow_network=allow_network)

    # Output structured JSON report if requested
    if output:
        output.write_text(res.to_json(indent=2), encoding="utf-8")
        if format_output != "json":
            rprint(f"[green]Structured JSON report written to {output}[/green]")

    if format_output == "json":
        typer.echo(res.to_json(indent=2))
        if not res.passed:
            raise typer.Exit(code=1 if res.status == ReproductionStatus.FAILED else 2)
        return

    if res.status == ReproductionStatus.UNSUPPORTED_ENVIRONMENT:
        rprint(Panel(
            f"[bold red]Reproduction Cannot Proceed[/bold red]\n\n"
            f"{res.error_message}\n\n"
            f"[dim]Security Note: Running untrusted code on the host without container isolation "
            f"violates AFM safety standards.[/dim]",
            title="Environment Unsupported",
            border_style="red",
        ))
        raise typer.Exit(code=2)

    if res.status in (ReproductionStatus.SECURITY_VIOLATION, ReproductionStatus.VALIDATION_ERROR):
        rprint(Panel(
            f"[bold red]Reproduction Rejected[/bold red]\n\n"
            f"{res.error_message}",
            title=f"{res.status.value.replace('-', ' ').title()}",
            border_style="red",
        ))
        raise typer.Exit(code=2)

    if res.status == ReproductionStatus.TIMEOUT:
        rprint(Panel(
            f"[bold red]Execution Timed Out[/bold red]\n\n"
            f"{res.error_message}",
            title="Timeout Deadline Exceeded",
            border_style="red",
        ))
        raise typer.Exit(code=1)

    # Format execution outcome
    color = "green" if res.passed else "red"
    rprint(f"\n[{color}]Reproduction Status: {res.status.value.upper()}[/{color}] (took {res.duration_seconds:.2f}s, exit code {res.exit_code})")

    if res.assertion_results:
        table = Table(title="Assertion Outcomes", show_header=True)
        table.add_column("Assertion", style="cyan")
        table.add_column("Result", style="bold")
        table.add_column("Expected", style="white")
        table.add_column("Actual", style="yellow")
        table.add_column("Details", style="dim")

        for ar in res.assertion_results:
            p_str = "[green]PASSED[/green]" if ar.passed else "[red]FAILED[/red]"
            table.add_row(ar.rule_type, p_str, str(ar.expected), str(ar.actual or ""), ar.details)
        console.print(table)

    if not res.passed:
        raise typer.Exit(code=1)


@app.command("evaluate")
def evaluate(
    case_id: str = typer.Argument(..., help="Case identifier to evaluate against"),
    adapter: str = typer.Option("mock", "--adapter", "-a", help=f"Agent adapter to use ({', '.join(list_adapters())})"),
    timeout: int = typer.Option(120, "--timeout", "-t", help="Evaluation timeout in seconds"),
    format_output: str = typer.Option("table", "--format", "-f", help="Output format: table or json"),
) -> None:
    """Evaluate whether an agent can complete the original task."""
    root = get_workspace_root()
    registry = FailureRegistry.from_workspace(root)

    try:
        case = registry.get(case_id)
        case_file = registry.get_file_path(case_id)
        agent_adapter = get_adapter(adapter)
    except Exception as exc:
        rprint(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    case_dir = case_file.parent if case_file else None

    rprint(f"[cyan]Evaluating case {case.id} using adapter '{adapter}'...[/cyan]")
    engine = EvaluationEngine()
    result = engine.evaluate(case=case, adapter=agent_adapter, case_dir=case_dir, timeout_seconds=timeout)

    if format_output.lower() == "json":
        typer.echo(json.dumps(result.to_dict(), indent=2))
        return

    table = Table(title=f"Agent Evaluation Report: {case.id}")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Case ID", result.case_id)
    table.add_row("Adapter", f"{result.adapter_name} {'(MOCK DOUBLE)' if result.is_mock else ''}")
    table.add_row("Task Resolved", "[bold green]YES[/bold green]" if result.task_resolved else "[bold red]NO[/bold red]")
    table.add_row("Duration", f"{result.duration_seconds:.2f} seconds")
    table.add_row("Agent Exit Code", str(result.agent_exit_code))
    table.add_row("Test Exit Code", str(result.test_exit_code))
    table.add_row("Files Modified", ", ".join(result.modified_files) if result.modified_files else "None")

    console.print(table)

    if result.diff:
        rprint("\n[bold]Code Diff Generated by Agent:[/bold]")
        console.print(Syntax(result.diff, "diff", theme="monokai", line_numbers=True))

    if result.error_message:
        rprint(f"\n[bold red]Agent Error:[/bold red] {result.error_message}")


@app.command("report")
def report(
    case_id: Optional[str] = typer.Argument(None, help="Case ID to generate report for (or all registry stats if omitted)"),
    format_type: str = typer.Option("markdown", "--format", "-f", help="Report format: markdown or json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="File to write report to"),
) -> None:
    """Generate structured Markdown or JSON report."""
    root = get_workspace_root()
    registry = FailureRegistry.from_workspace(root)

    if case_id:
        try:
            case = registry.get(case_id)
        except Exception as exc:
            rprint(f"[bold red]Error:[/bold red] {exc}")
            raise typer.Exit(code=1)

        if format_type.lower() == "json":
            content = json.dumps(case.model_dump(mode="json"), indent=2)
        else:
            content = format_case_markdown(case)
    else:
        stats = registry.statistics()
        if format_type.lower() == "json":
            content = json.dumps({
                "total_cases": stats.total_cases,
                "real_cases": stats.real_cases,
                "synthetic_cases": stats.synthetic_cases,
                "reproducible_cases": stats.reproducible_cases,
                "status_counts": stats.status_counts,
                "category_counts": stats.category_counts,
                "agent_counts": stats.agent_counts,
            }, indent=2)
        else:
            content = format_stats_markdown(stats)

    if output:
        output.write_text(content, encoding="utf-8")
        rprint(f"[green]Report written to {output}[/green]")
    else:
        typer.echo(content)


@app.command("doctor")
def doctor() -> None:
    """Verify local development environment, tooling, and registry integrity."""
    root = get_workspace_root()
    table = Table(title="AI Failure Museum — System Diagnostics", show_header=True)
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="white")

    # 1. Python Check
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)
    table.add_row(
        "Python Runtime",
        "[green]OK[/green]" if py_ok else "[red]FAIL[/red]",
        f"Version {py_ver} ({sys.executable})",
    )

    # 2. Docker Check
    docker_ok = is_docker_available()
    table.add_row(
        "Docker Isolation Sandbox",
        "[green]AVAILABLE[/green]" if docker_ok else "[yellow]UNAVAILABLE[/yellow]",
        "Docker daemon reachable for container isolation" if docker_ok else "Docker not detected; safe reproduction is restricted",
    )

    # 3. Schema Check
    schema_file = root / "schemas" / "failure-case.schema.json"
    schema_ok = schema_file.exists()
    table.add_row(
        "JSON Schema",
        "[green]FOUND[/green]" if schema_ok else "[red]MISSING[/red]",
        str(schema_file.relative_to(root)) if schema_ok else "Run 'python scripts/generate_schema.py'",
    )

    # 4. Registry Discovery Check
    try:
        reg = FailureRegistry.from_workspace(root)
        stats = reg.statistics()
        reg_ok = True
        reg_details = f"Discovered {stats.total_cases} cases ({stats.synthetic_cases} synthetic, {stats.real_cases} real)"
    except Exception as exc:
        reg_ok = False
        reg_details = f"Discovery error: {exc}"

    table.add_row(
        "Registry Discovery",
        "[green]OK[/green]" if reg_ok else "[red]FAIL[/red]",
        reg_details,
    )

    console.print(table)


@app.command("new")
def new_case(
    case_id: Optional[str] = typer.Option(None, "--id", help="Case ID (e.g. AFM-0002 or SYN-0004)"),
    title: Optional[str] = typer.Option(None, "--title", help="Case title"),
    category: Optional[str] = typer.Option(None, "--category", help="Primary failure category"),
    agent_name: Optional[str] = typer.Option(None, "--agent", help="Name of the agent"),
    synthetic: bool = typer.Option(False, "--synthetic", help="Mark case as synthetic"),
) -> None:
    """Create a new failure case scaffold with guided prompts."""
    root = get_workspace_root()

    rprint("[bold cyan]=== AI Failure Museum Case Generator ===[/bold cyan]")

    # Prompt if missing
    if not case_id:
        default_id = "SYN-0004" if synthetic else "AFM-0001"
        case_id = typer.prompt("Case ID (e.g. AFM-0001 or SYN-0001)", default=default_id)

    is_synth = case_id.startswith("SYN-") or synthetic

    if not title:
        title = typer.prompt("Case Title")

    if not category:
        rprint("\nAvailable categories:")
        for cat in FailureCategory:
            rprint(f"  - {cat.value}")
        category = typer.prompt("Primary Category", default="hallucinated-api")

    if not agent_name:
        agent_name = typer.prompt("Agent Name", default="ExampleAgent")

    # Determine directory
    target_dir = root / ("examples/synthetic" if is_synth else "failures") / case_id
    target_dir.mkdir(parents=True, exist_ok=True)
    case_file = target_dir / "case.yaml"

    if case_file.exists():
        rprint(f"[bold red]Error:[/bold red] Case file already exists at {case_file}")
        raise typer.Exit(code=1)

    template = f"""id: {case_id}
title: "{title}"
description: "Detailed description of the failure observed with {agent_name}."
categories:
  - {category}
status: submitted
is_synthetic: {'true' if is_synth else 'false'}
agent:
  name: "{agent_name}"
  version: "1.0.0"
  model: "gpt-4o"
  provider: "OpenAI"
task:
  prompt: "User instruction or prompt that led to the failure."
  context: "Context provided in system prompt or files."
  target_repository: "owner/repo"
  target_files:
    - "example.py"
behavior:
  expected: "Expected, correct behavior that should have occurred."
  observed: "Actual flawed behavior observed."
environment:
  os: "Linux / POSIX"
  runtime: "Python 3.11"
  dependencies: {{}}
  docker_image: "python:3.11-slim"
reproduction:
  type: "docker"
  entrypoint: "repro.py"
  command: "python repro.py"
  timeout_seconds: 60
  requires_network: false
  requires_docker: true
  assertions:
    - type: exit_code_equals
      value: 1
      description: "Exit code 1 reflects failure"
verification:
  method_type: "automated-test"
  test_runner: "python repro.py"
  expected_exit_code: 1
  failure_criteria: "Failure reproduction confirmed by script exit code."
evidence:
  - type: log
    path_or_url: "evidence/reproduction.log"
    description: "Captured log output"
submission:
  submitted_by: "contributor"
  date: "{datetime.date.today().isoformat()}"
tags:
  - {category}
"""
    case_file.write_text(template, encoding="utf-8")

    # Create evidence directory and sample repro script
    evidence_dir = target_dir / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    (evidence_dir / "reproduction.log").write_text("Captured evidence log goes here.\n", encoding="utf-8")

    repro_file = target_dir / "repro.py"
    repro_file.write_text(
        '"""\nReproduction script for {}\n"""\nimport sys\n\n# Implement reproduction logic here\nsys.exit(1)\n'.format(case_id),
        encoding="utf-8",
    )

    rprint(f"\n[bold green]Case scaffolded successfully at:[/bold green] {case_file}")
    rprint("Next steps:")
    rprint(f"  1. Edit {case_file} with accurate reproduction instructions")
    rprint(f"  2. Implement {repro_file}")
    rprint(f"  3. Validate case: afm validate {case_id}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
