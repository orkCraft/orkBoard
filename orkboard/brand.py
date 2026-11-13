"""The product's name as a person reads it (decisions §95): Orkboard, the one product these modules make.

    brand.name()                          # "Orkboard"
    brand.git_identity()                  # the `-c` arguments that make Orkboard the author of a commit it makes itself
    brand.board_author()                  # (name, email) of the commits of the Board's own pages
"""
from __future__ import annotations

NAME = "Orkboard"


def name() -> str:
    return NAME


def git_identity() -> list[str]:
    """The `-c` arguments that make Orkboard the author of a commit it makes itself: its name, and a local address (spec 149 F.3)."""
    return ["-c", f"user.name={NAME}", "-c", f"user.email={NAME.lower()}@localhost"]


def board_author() -> tuple[str, str]:
    """(name, email) of the commits of the Board's own pages: *Orkboard board* (spec 149 F.3)."""
    return f"{NAME} board", f"board@{NAME.lower()}.local"
