"""Shared pytest bootstrap for the Mewgenics Breeding Manager suite.

Keeps the suite runnable "out of the box" on a fresh clone:

* ensures the ``--basetemp`` directory (``tmp/pytest``) exists so pytest can
  create its per-run temporary tree without a manual ``mkdir`` first;
* extracts the bundled sample saves (``tools/saves/saves.zip``) — the real
  ``*.sav`` fixtures are git-ignored, so parser tests that read them would
  otherwise be skipped / error on a clean checkout.

The extraction only runs when a required save is missing, so an existing
working tree is never touched.

It also exposes a ``gpak_path`` fixture so game-data tests locate the (large,
never-committed) ``resources.gpak`` without a hard-coded install path.
"""
from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

_PROJ_ROOT = Path(__file__).resolve().parent
_SAVES_DIR = _PROJ_ROOT / "tools" / "saves"
_SAVES_ZIP = _SAVES_DIR / "saves.zip"

# Sample saves the parser tests expect to find on disk.
_REQUIRED_SAVES = (
    "7 cats.sav",
    "19cats.sav",
    "21cats new.sav",
    "21cats.sav",
    "23.sav",
    "27cats.sav",
    "35cats.sav",
    "50.sav",
    "202cats.sav",
    "1085cats.sav",
    "4000cats new.sav",
    "4000cats.sav",
)


def _ensure_basetemp_dirs() -> None:
    """Create ``tmp/`` and ``tmp/pytest/`` before pytest resolves basetemp.

    pytest's ``--basetemp`` requires its parent to exist; on a fresh clone
    ``tmp/`` is absent (it is git-ignored), which aborted the session with
    ``FileNotFoundError``.  We also honour a custom ``--basetemp`` passed on
    the command line.
    """
    (_PROJ_ROOT / "tmp").mkdir(parents=True, exist_ok=True)
    (_PROJ_ROOT / "tmp" / "pytest").mkdir(parents=True, exist_ok=True)

    argv = sys.argv
    for i, arg in enumerate(argv):
        value = ""
        if arg.startswith("--basetemp="):
            value = arg.split("=", 1)[1]
        elif arg == "--basetemp" and i + 1 < len(argv):
            value = argv[i + 1]
        if value:
            try:
                Path(os.path.expanduser(value)).mkdir(parents=True, exist_ok=True)
            except OSError:
                pass


def _ensure_sample_saves() -> None:
    """Extract git-ignored sample saves from the tracked ``saves.zip``."""
    if not _SAVES_ZIP.exists():
        return
    missing = [n for n in _REQUIRED_SAVES if not (_SAVES_DIR / n).exists()]
    if not missing:
        return
    try:
        with zipfile.ZipFile(_SAVES_ZIP) as zf:
            available = set(zf.namelist())
            for name in missing:
                if name in available:
                    zf.extract(name, _SAVES_DIR)
    except (OSError, zipfile.BadZipFile):
        # A corrupt/absent archive must not abort collection — individual
        # tests skip themselves when their save fixture is unavailable.
        pass


def _configured_gpak_path() -> str:
    """Best-effort lookup of a previously chosen ``resources.gpak`` path.

    Reads ``settings.json`` directly (no PySide6 import) so collection stays
    dependency-light.
    """
    appdata = os.environ.get("APPDATA", str(Path.home()))
    config_path = Path(appdata) / "MewgenicsBreedingManager" / "settings.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    value = data.get("gpak_path", "")
    return value.strip() if isinstance(value, str) else ""


def _find_gpak_path() -> str | None:
    """Resolve ``resources.gpak`` from env, saved config, then known locations."""
    env_path = os.environ.get("MEWGENICS_GPAK_PATH", "").strip()
    if env_path and Path(env_path).exists():
        return env_path

    saved = _configured_gpak_path()
    if saved and Path(saved).exists():
        return saved

    src_dir = _PROJ_ROOT / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    try:
        from mewgenics.utils.config import _candidate_gpak_paths

        for candidate in _candidate_gpak_paths():
            if candidate and Path(candidate).exists():
                return candidate
    except Exception:
        pass

    return None


@pytest.fixture(scope="session")
def gpak_path() -> str:
    """Path to the game's ``resources.gpak``, or skip the test if absent."""
    path = _find_gpak_path()
    if not path:
        pytest.skip(
            "resources.gpak not found — set MEWGENICS_GPAK_PATH, point the app "
            "at your install, or copy resources.gpak next to the project."
        )
    return path


_ensure_basetemp_dirs()
_ensure_sample_saves()
