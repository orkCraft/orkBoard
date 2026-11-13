"""orkGet's copy (docs/specs/41-orkget.md §2, §7): `orkboard/orkget/` is orkGet's, stamped and never edited here, and
Orkboard's profile is what its installed copies were told."""
from __future__ import annotations

import tomllib
from pathlib import Path

from orkboard.orkget import stamp

ROOT = Path(__file__).resolve().parents[1]
COPY = ROOT / "orkboard" / "orkget"


def test_the_copy_is_untouched():
    """A change is made in orkGet, then copied: `python -m orkboard.orkget.stamp <a checkout of orkGet>`."""
    assert stamp.problems() == []


def test_a_byte_changed_in_the_copy_is_named(tmp_path):
    import shutil
    shutil.copytree(COPY, tmp_path / "orkget", ignore=shutil.ignore_patterns("__pycache__"))
    with (tmp_path / "orkget" / "updates.py").open("a", encoding="utf-8") as f:
        f.write("# by hand\n")
    assert stamp.problems(tmp_path / "orkget") == ["changed: updates.py (a change is made in orkGet, then copied)"]


def test_a_wheel_carries_the_copys_files():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    kept = data["tool"]["setuptools"]["package-data"]["orkboard"]
    assert {"orkget/ORKGET.json", "orkget/schemas/*.json", "orkget/install.sh"} <= set(kept)
