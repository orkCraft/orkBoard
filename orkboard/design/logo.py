"""Which logo a product shows (docs/specs/107-what-the-owners-day-said.md §12): Orkboard's mark, the Orkmaster's crowned head (`design-system/logo/orkboard/`, made by `design/mark.py`), where it is Orkboard that runs; the ork
mark of `design-system/logo/` where Orkline runs these modules (`brand.name()`, decisions §95). No face.

    logo.own()                       # True when the product running is Orkboard
    logo.favicon()                   # the file `/favicon.ico` answers with
    logo.phone_icon("icon-192.png")  # Orkboard's file for a name the phone's app serves, else None (the app's own file stays)
"""
from __future__ import annotations

from pathlib import Path

from orkboard import brand
from orkboard.design import tokens

ROOT = tokens.SYSTEM / "logo"
BOARD = ROOT / "orkboard"
PHONE = ("icon-192.png", "icon-512.png", "apple-touch-icon.png")        # what pwa/index.html and the manifest name


def own() -> bool:
    return brand.name() == brand.DEFAULT


def favicon() -> Path:
    return (BOARD if own() else ROOT) / "favicon.ico"


def phone_icon(name: str) -> Path | None:
    return BOARD / name if own() and name in PHONE else None
