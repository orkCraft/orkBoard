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
