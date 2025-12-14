"""Compatibility package for running from source.

This repository uses a `src/` layout. When running directly from the repo root
(without an editable install), `python -m meritscalc.main` would normally fail
because `src/` is not on `sys.path`.

This lightweight package extends `meritscalc`'s module search path to include
`src/meritscalc`, making `meritscalc.*` importable in dev/test environments.
"""

from __future__ import annotations

from pathlib import Path


# Make submodules (logic/settings/qt_ui/...) resolvable from `src/meritscalc`.
_SRC_MERITSCALC = Path(__file__).resolve().parent.parent / "src" / "meritscalc"
if _SRC_MERITSCALC.is_dir():
    __path__.append(str(_SRC_MERITSCALC))  # type: ignore[name-defined]


# Re-export common symbols for convenience.
from .logic import MeritsCalculator  # noqa: E402  # type: ignore
from .settings import SettingsManager  # noqa: E402  # type: ignore

__all__: list[str] = ["MeritsCalculator", "SettingsManager"]
