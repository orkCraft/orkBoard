"""Spec 102 part F, picking on a party's map (docs/specs/102-the-other-maps-and-picking-on-them.md §6, decisions §141, §152; mockup docs/mockups/s3/ state 7), in a real browser at both widths
(`tests/narrow.py`: 1280 × 800, and 390 × 844 with touch), against the table's stub host (Tech led by the Architect, so its tab is the System; Art's tab carries a stub map of this test's own, drawn with `Pickable`
as the other maps do, to hold groups the System's parts alone would not).

The strip (*Pick a part to point at it* · *Stop picking*) over the map while the + card's field is addressed to the party whose tab is open, *Open Tech's table to pick* when another tab is open (the tab kept); a press on a
part marks it (orkUI's brackets, lifted) and again takes it off, a press out of picking lifts the card as before; on the desktop a drag from the empty place draws the dashed box and takes the parts it covers, Shift adds,
a box over a whole container pins it, over the whole map pins *all of Tech's table* (sent as no mark); on a touch screen a tap marks, a long press on the empty place then a drag draws the box, a drag alone scrolls; the marks as chips
on the field (a name and ×), past five the first five and *and n more*, a press showing all; picking ends with *Stop picking*, Esc, sending, or the address taken off; the marks go with `ideas.add`; no sideways scroll.
Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost, open_tab, shot, system_doc  # noqa: E402

pytestmark = pytest.mark.browser

PARTS = {"server": ["server/index.ts", "server/lobby.ts", "server/rooms.ts", "server/timer.ts"], "client": ["client/net.ts", "client/hud.ts", "client/menu.ts"]}


def big_system():
    """The stub System with seven parts in two containers (more than five marks past a box)."""
    doc = system_doc()
    part = lambda path: {"path": path, "name": path.rsplit("/", 1)[-1], "count": 2, "uses": [], "used_by": [], "gone": False}  # noqa: E731
    parts = {p: part(p) for ps in PARTS.values() for p in ps}
    cont = lambda path, name, role: {"path": path, "name": name, "stack": [], "unknown": 0, "ways_in": [], "parts": PARTS[path], "layers": [{"role": role, "parts": PARTS[path]}], "gone": []}  # noqa: E731
    doc["overview"] = {"containers": [cont("server", "server/", "data"), cont("client", "client/", "face")], "shared": [], "links": [], "parts": parts}
    return doc


class PickHost(TableHost):
    """The table's host with a bigger System, and what `ideas.add` was sent with kept."""

    def handle(self, name, a):
        if name == "ideas.system":
            return big_system()
        return super().handle(name, a)

    def sent(self):
        return [a for n, a in self.log if n == "ideas.add"]


@pytest.fixture(params=narrow.WIDTHS)
def picking(gui, request):
    """The window at one width against a PickHost; the page's errors asserted at the end: `(page, host, width)`."""
    errors: list[str] = []
    server, browser = gui
    host = PickHost()
    host.parties[2]["party_craft"] = "art"                                         # Art's tab draws the stub map below
    pg = narrow.page(browser, request.param)
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource") and errors.append(f"console: {m.text}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".cards-lane").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)




def field(pg):
    return pg.locator(".hand-field")


def open_field(pg, text=""):
    pg.locator(".hand :is(.hand-plus, [data-blank-deck])").click()
    field(pg).wait_for(timeout=WAIT_MS)
    if text:
        pg.locator(".hand-field__text").fill(text)


def part(pg, path):
    return pg.locator(f'.sys-part[data-part="{path}"]')


def chips(pg):
    return [c.get_attribute("data-mark") for c in pg.locator(".pick-chip").all()]


def ready(pg, slug="tech"):
    """Tech's tab with its System drawn."""
    open_tab(pg, slug)
    pg.locator(".table-sys .sys[data-state=shown]").wait_for(timeout=WAIT_MS)


def centre(pg, path):
    b = part(pg, path)
    b.scroll_into_view_if_needed()
    return b.bounding_box()


def drag(pg, a, b, shift=False):
    """A mouse drag from `a` to `b`, Shift held when asked."""
    if shift:
        pg.keyboard.down("Shift")
    pg.mouse.move(*a)
    pg.mouse.down()
    pg.mouse.move((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, steps=4)
    pg.mouse.move(*b, steps=4)
    pg.mouse.up()
    if shift:
        pg.keyboard.up("Shift")


def around(pg, paths, pad=6):
    """The corners of a box around the parts `paths`, and the point just outside it, where the System is empty."""
    for p in paths:
        centre(pg, p)                                                               # each in view (a column may need the scroll) before any is measured
    boxes = [centre(pg, p) for p in paths]
    x0, y0 = min(b["x"] for b in boxes) - pad, min(b["y"] for b in boxes) - pad
    x1, y1 = max(b["x"] + b["width"] for b in boxes) + pad, max(b["y"] + b["height"] for b in boxes) + pad
    return (x0, y0), (x1, y1)




# -- the strip and a press ------------------------------------------------------------------------------------------------------------------------------------------------------



def test_a_press_marks_a_part_with_the_brackets_and_again_takes_it_off(picking):
    pg, host, w = picking
    ready(pg)
    open_field(pg)
    lobby = part(pg, "server/lobby.ts")
    lobby.scroll_into_view_if_needed()
    lobby.click()
    pg.locator(".pick-chip").wait_for(timeout=WAIT_MS)
    assert chips(pg) == ["server/lobby.ts"] and "server/lobby.ts" in pg.locator(".pick-chip").inner_text()
    assert "ork-taken" in lobby.get_attribute("class") and "pick-lifted" in lobby.get_attribute("class"), "orkUI's brackets, lifted"
    assert pg.locator(".table-back").count() == 0, "a press in picking marks, it does not lift the card"
    assert field(pg).count() == 1, "a press on the map does not close the field"
    assert part(pg, "server/index.ts").get_attribute("class").count("ork-taken") == 0
    shot(pg, f"picking-one-{w}.png")
    lobby.click()
    pg.wait_for_selector(".pick-chip", state="detached", timeout=WAIT_MS)
    pg.wait_for_function("() => !document.querySelector('.sys-part.ork-taken')", timeout=WAIT_MS)






# -- the box (the desktop) ------------------------------------------------------------------------------------------------------------------------------------------------------









# -- a touch screen ------------------------------------------------------------------------------------------------------------------------------------------------------------------





# -- the chips -----------------------------------------------------------------------------------------------------------------------------------------------------------------------



# -- how it ends ---------------------------------------------------------------------------------------------------------------------------------------------------------------------











# -- another map, drawn with Pickable ---------------------------------------------------------------------------------------------------------------------------------------------

