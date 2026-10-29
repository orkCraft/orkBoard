"""The two widths every browser test of the window runs at (docs/specs/94-one-page-fitted-to-the-width.md §1.6, spec 98 §6.2):
the wide desktop and the narrow window (`narrow` = `FINE`, a mouse); `phone` is the narrow width held upright, with touch. Since spec 103 A a narrow window with touch is the phone's first screen, the hand (frame/upright.js); `FINE` is the same width with a mouse
(a narrow desktop window, VS Code's side bar), which keeps spec 94 §3's table over the hand.

    @pytest.mark.parametrize("width", narrow.WIDTHS)
    def test_something(gui, width):
        page = narrow.page(browser, width)       # a new page at that width (a context of its own)
        …
        narrow.no_sideways(page)                 # nothing scrolls sideways
"""
from __future__ import annotations

WIDE = {"viewport": {"width": 1280, "height": 800}}
NARROW = {"viewport": {"width": 390, "height": 844}, "has_touch": True, "is_mobile": True, "device_scale_factor": 2}
FINE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2}      # the narrow width with a mouse: a narrow desktop window, VS Code's side bar (not a phone: no touch)
WIDTHS = ("wide", "narrow")              # the table's two widths: "narrow" is the narrow desktop window, FINE (a mouse), where spec 94 §3's table lies over the hand
PHONE_WIDTHS = ("wide", "phone")         # for what a touch phone shows (spec 103 A): "phone" is NARROW (upright, touch), where the first screen is the hand


def context(browser, width: str):
    """A browser context at `width`: "wide", "narrow" (FINE: the narrow table, a mouse) or "phone" (NARROW: touch, the hand first)."""
    return browser.new_context(**{"wide": WIDE, "narrow": FINE, "phone": NARROW}[width])


def page(browser, width: str):
    """A new page in a context of its own at `width`."""
    return context(browser, width).new_page()


def no_sideways(pg) -> None:
    """The page does not scroll sideways (spec 94 §1.2: no fixed width a part of the window)."""
    over = pg.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert over <= 0, f"the page scrolls sideways by {over} px"
