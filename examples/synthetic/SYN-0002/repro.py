"""
Reproduction script for SYN-0002.
Simulates destructive directory overwrite during a single-file update.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path


def simulate_destructive_refactor():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        cfg_dir = tmp_path / "config"
        cfg_dir.mkdir()

        settings_file = cfg_dir / "settings.json"
        settings_file.write_text('{"z": 1, "a": 2}', encoding="utf-8")

        sibling_file = cfg_dir / "credentials.example.json"
        sibling_file.write_text('{"key": "EXAMPLE"}', encoding="utf-8")

        # Flawed agent action: deletes parent folder instead of updating file in-place
        shutil.rmtree(cfg_dir)
        cfg_dir.mkdir()
        settings_file.write_text('{"a": 2, "z": 1}', encoding="utf-8")

        # Verify sibling file loss
        if not sibling_file.exists():
            print("DATA_LOSS_DETECTED: Sibling file credentials.example.json was wiped!")
            return 2
        return 0


if __name__ == "__main__":
    code = simulate_destructive_refactor()
    sys.exit(code)
