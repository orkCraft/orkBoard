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
WIDTHS = ("wide",)                       # one path, one width (decisions §308): a second width only where the behaviour differs, and then it is named in the test
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


def unroll_drum(pg, timeout: int = 10000) -> None:
    """At the wide width the AI tools lie in the right column's row, three at most; every tool lies in the list under it only while it is unrolled (spec 168 A4, decisions §285.1; hover or focus): the pointer goes onto the row and stays. Under 760 px the potions always lie in their rows: nothing to do."""
    if pg.viewport_size["width"] < 760:
        return
    pg.locator(".pots__row").wait_for(timeout=timeout)
    b = pg.locator(".pots__row").bounding_box()
    pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    pg.locator(".pots[data-open]").wait_for(timeout=timeout)
