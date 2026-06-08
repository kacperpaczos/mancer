"""Helper for loading reference coreutils outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent / "coreutils_outputs"


def load_coreutils_output(command: str, scenario_id: str) -> dict[str, Any]:
    """Returns dictionary from saved JSON file for given scenario."""

    path = FIXTURES_DIR / command / f"{scenario_id}.json"
    if not path.exists():
        available = sorted((FIXTURES_DIR / command).glob("*.json"))
        raise FileNotFoundError(f"No fixture for {command}/{scenario_id}. " f"Available: {[p.stem for p in available]}")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data
