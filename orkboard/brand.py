"""The product's name as a person reads it (decisions §95): Orkboard's, or Orkline's where Orkline runs these modules.
It is the name the running product's orkGet profile carries (`orkboard/product.py` binds Orkboard's), so a module never
names the other product.

    brand.name()                          # "Orkboard" here, "Orkline" in Orkline
"""
from __future__ import annotations

DEFAULT = "Orkboard"


def name() -> str:
    from orkboard.orkget import profile
    try:
        return profile.current().name
    except RuntimeError:                  # nothing bound a profile yet (a module used on its own, a test)
        return DEFAULT


def git_identity() -> list[str]:
    """The `-c` arguments that make the running product the author of a commit it makes itself: its name, and a local address (spec 149 F.3)."""
    who = name()
    return ["-c", f"user.name={who}", "-c", f"user.email={who.lower()}@localhost"]


def board_author() -> tuple[str, str]:
    """(name, email) of the commits of the Board's own pages: *Orkboard board* here, *Orkline board* in Orkline (spec 149 F.3)."""
    who = name()
    return f"{who} board", f"board@{who.lower()}.local"
