from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    scripts_dir = skill_root / "scripts"
    sys.path.insert(0, str(scripts_dir))

