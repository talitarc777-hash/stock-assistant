"""Shared bootstrap helpers for script execution."""

from __future__ import annotations

from pathlib import Path
import sys


def ensure_project_root_on_path() -> None:
    """Add project root to sys.path for script imports."""
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

