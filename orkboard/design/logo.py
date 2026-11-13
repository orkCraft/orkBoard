"""Orkboard's logo (docs/specs/107-what-the-owners-day-said.md §12): the Orkmaster's crowned head (`design-system/logo/orkboard/`, made by
`design/mark.py`). No face.

    logo.favicon()                   # the file `/favicon.ico` answers with
    logo.phone_icon("icon-192.png")  # Orkboard's file for a name the phone's app serves, else None (the app's own file stays)
"""
from __future__ import annotations

from pathlib import Path

from orkboard.design import tokens

ROOT = tokens.SYSTEM / "logo"
BOARD = ROOT / "orkboard"
PHONE = ("icon-192.png", "icon-512.png", "apple-touch-icon.png")        # what pwa/index.html and the manifest name


def favicon() -> Path:
    return BOARD / "favicon.ico"


def phone_icon(name: str) -> Path | None:
    return BOARD / name if name in PHONE else None
