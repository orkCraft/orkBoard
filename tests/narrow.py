"""The two widths every browser test of the window runs at (docs/specs/94-one-page-fitted-to-the-width.md §1.6, spec 98 §6.2):
the wide desktop and the narrow phone held upright, with touch.

    @pytest.mark.parametrize("width", narrow.WIDTHS)
    def test_something(gui, width):
        page = narrow.page(browser, width)       # a new page at that width (a context of its own)
        …
        narrow.no_sideways(page)                 # nothing scrolls sideways
"""
from __future__ import annotations

WIDE = {"viewport": {"width": 1280, "height": 800}}
NARROW = {"viewport": {"width": 390, "height": 844}, "has_touch": True, "is_mobile": True, "device_scale_factor": 2}
WIDTHS = ("wide", "narrow")


def context(browser, width: str):
    """A browser context at `width` ("wide" or "narrow")."""
    return browser.new_context(**(WIDE if width == "wide" else NARROW))


def page(browser, width: str):
    """A new page in a context of its own at `width`."""
    return context(browser, width).new_page()


def no_sideways(pg) -> None:
    """The page does not scroll sideways (spec 94 §1.2: no fixed width a part of the window)."""
    over = pg.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert over <= 0, f"the page scrolls sideways by {over} px"
