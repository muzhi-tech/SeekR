"""Shared path setup for seekr-evolve scripts.

Centralises the sys.path insertions needed so that:
  - seekr.scripts.models is importable
  - sibling scripts (effect_collector, strategy_generator, parity_auditor) are importable

Usage at the top of a script:

    from _path_setup import ensure_paths
    ensure_paths()
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPTS_DIR.parents[1]  # seekr/

_paths_initialized = False


def ensure_paths() -> None:
    """Add seekr-evolve/scripts/ and project root to sys.path (once)."""
    global _paths_initialized
    if _paths_initialized:
        return
    scripts_str = str(_SCRIPTS_DIR)
    root_str = str(_PROJECT_ROOT)
    if scripts_str not in sys.path:
        sys.path.insert(0, scripts_str)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    _paths_initialized = True
