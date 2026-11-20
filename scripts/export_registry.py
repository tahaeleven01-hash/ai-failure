"""
Exports current AFM registry to web/data/registry.json for the web dashboard.
Enriches cases with inline reproduction scripts and evidence contents when present.
"""

import json
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "packages"))

from afm.registry import FailureRegistry
from afm.security import resolve_safe_path


def main() -> None:
    registry = FailureRegistry.from_workspace(root_dir)
    web_data_dir = root_dir / "web" / "data"
    web_data_dir.mkdir(parents=True, exist_ok=True)

    dest = web_data_dir / "registry.json"

    stats = registry.statistics()
    enriched_cases = []

    for case in registry.cases:
        case_dict = case.model_dump(mode="json")
        case_file = registry.get_file_path(case.id)

        if case_file and case_file.parent.exists():
            case_dir = case_file.parent

            # Attach reproduction code if available
            entrypoint = case.reproduction.entrypoint or "repro.py"
            try:
                ep_path = resolve_safe_path(case_dir, entrypoint)
                if ep_path.exists() and ep_path.is_file():
                    case_dict["reproduction_code"] = ep_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

            # Attach evidence contents if local files
            for ev in case_dict.get("evidence", []):
                p = ev.get("path_or_url", "")
                if not (p.startswith("http://") or p.startswith("https://")):
                    try:
                        ev_path = resolve_safe_path(case_dir, p)
                        if ev_path.exists() and ev_path.is_file():
                            ev["content"] = ev_path.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        pass

        enriched_cases.append(case_dict)

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
        "cases": enriched_cases,
    }

    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Registry exported to {dest}")
    print(f"Total Cases: {stats.total_cases} ({stats.real_cases} real, {stats.synthetic_cases} synthetic)")


if __name__ == "__main__":
    main()
