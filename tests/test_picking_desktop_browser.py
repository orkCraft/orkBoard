"""Spec 102 part F, picking on a party's map (docs/specs/102-the-other-maps-and-picking-on-them.md §6, decisions §141, §152; mockup docs/mockups/s3/ state 7), in a real browser at both widths
(`tests/narrow.py`: 1280 × 800, and 390 × 844 with touch), against the table's stub host (Tech led by the Architect, so its tab is the System; Art's tab carries a stub map of this test's own, drawn with `Pickable`
as the other maps do, to hold groups the System's parts alone would not).

The strip (*Pick a part to point at it* · *Stop picking*) over the map while the + card's field is addressed to the party whose tab is open, *Open Tech's map to pick* when another tab is open (the tab kept); a press on a
part marks it (orkUI's brackets, lifted) and again takes it off, a press out of picking lifts the card as before; on the desktop a drag from the empty place draws the dashed box and takes the parts it covers, Shift adds,
a box over a whole container pins it, over the whole map pins *all of System* (sent as no mark); on a touch screen a tap marks, a long press on the empty place then a drag draws the box, a drag alone scrolls; the marks as chips
on the field (a name and ×), past five the first five and *and n more*, a press showing all; picking ends with *Stop picking*, Esc, sending, or the address taken off; the marks go with `ideas.add`; no sideways scroll.
Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost, open_tab, shot, start, system_doc  # noqa: E402

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
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


STUB_MAP = """async () => {
  const { html } = await import('/static/js/html.js');
  const { mapFor, Pickable } = await import('/static/js/table/maps.js');
  const lane = (name, ids) => html`<section class="stub-lane" data-lane=${name} style="display:flex;gap:12px;padding:8px">${ids.map((id) => html`<${Pickable} key=${id} map="assets" id=${id} name=${id} group=${name} groupName=${name + '/'}>
      <article class="ork-card stub-card" data-card=${id} style="width:96px;height:120px;padding:8px">${id}</article><//>`)}</section>`;
  mapFor('art', () => html`<div class="stub-map" style="flex:1;min-height:0;overflow:auto">${lane('sprites', ['hero.png', 'orc.png', 'tower.png'])}${lane('sound', ['hit.wav', 'win.wav'])}</div>`);
}"""


def field(pg):
    return pg.locator(".hand-field")


def open_field(pg, text=""):
    pg.locator(".hand .hand-plus").click()
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


def long_press_drag(pg, a, b):
    """A finger held still at `a`, then dragged to `b` (a touch's box), through the protocol: Playwright's touchscreen only taps."""
    cdp = pg.context.new_cdp_session(pg)
    point = lambda p: [{"x": p[0], "y": p[1], "id": 1}]  # noqa: E731
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": point(a)})
    pg.wait_for_timeout(700)
    for i in range(1, 6):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": point((a[0] + (b[0] - a[0]) * i / 5, a[1] + (b[1] - a[1]) * i / 5))})
        pg.wait_for_timeout(30)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


# -- the strip and a press ------------------------------------------------------------------------------------------------------------------------------------------------------

def test_the_strip_lies_over_the_map_while_the_field_is_addressed_to_the_party_whose_tab_is_open(picking):
    pg, host, w = picking
    ready(pg)
    assert pg.locator(".pick-strip").count() == 0, "no field, no picking"
    open_field(pg)
    strip = pg.locator(".pick-strip")
    strip.wait_for(timeout=WAIT_MS)
    assert " ".join(strip.inner_text().split()) == "Pick a part to point at it Stop picking"
    assert strip.bounding_box()["y"] < part(pg, "server/lobby.ts").bounding_box()["y"], "over the map"
    shot(pg, f"picking-strip-{w}.png")
    pg.get_by_role("button", name="Stop picking").click()
    pg.wait_for_selector(".pick-strip", state="detached", timeout=WAIT_MS)
    assert field(pg).count() == 1, "the field stays: only picking ended"
    part(pg, "server/lobby.ts").click()                                            # out of picking a press lifts the card as ever
    pg.locator(".table-back").wait_for(timeout=WAIT_MS)
    assert chips(pg) == []


def test_a_press_marks_a_part_with_the_brackets_and_again_takes_it_off(picking):
    pg, host, w = picking
    ready(pg)
    open_field(pg)
    lobby = part(pg, "server/lobby.ts")
    lobby.scroll_into_view_if_needed()
    lobby.click()
    pg.locator(".pick-chip").wait_for(timeout=WAIT_MS)
    assert chips(pg) == ["server/lobby.ts"] and "server/lobby.ts" in pg.locator(".pick-chip").inner_text()
    assert "ork-picked" in lobby.get_attribute("class") and "pick-lifted" in lobby.get_attribute("class"), "orkUI's brackets, lifted"
    assert pg.locator(".table-back").count() == 0, "a press in picking marks, it does not lift the card"
    assert field(pg).count() == 1, "a press on the map does not close the field"
    assert part(pg, "server/index.ts").get_attribute("class").count("ork-picked") == 0
    shot(pg, f"picking-one-{w}.png")
    lobby.click()
    pg.wait_for_selector(".pick-chip", state="detached", timeout=WAIT_MS)
    pg.wait_for_function("() => !document.querySelector('.sys-part.ork-picked')", timeout=WAIT_MS)


def test_the_marks_go_with_the_idea_and_are_gone_after_it(picking):
    pg, host, w = picking
    ready(pg)
    open_field(pg, "Players who drop out get their seat back")
    for p in ("server/lobby.ts", "client/net.ts"):
        b = part(pg, p)
        b.scroll_into_view_if_needed()
        b.click()
    pg.locator(".pick-chip").nth(1).wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Send").click()
    pg.wait_for_selector(".hand-field", state="detached", timeout=WAIT_MS)
    sent = host.sent()[-1]
    assert sent["party"] == "tech" and sent["text"] == "Players who drop out get their seat back"
    assert sent["marks"] == [{"map": "system", "id": "server/lobby.ts", "name": "server/lobby.ts", "group": "server"}, {"map": "system", "id": "client/net.ts", "name": "client/net.ts", "group": "client"}]
    assert pg.locator(".ork-picked").count() == 0
    open_field(pg)
    assert pg.locator(".pick-chip").count() == 0, "sent: nothing left marked"


def test_a_press_on_a_part_does_not_lift_it_and_a_press_away_from_the_map_closes_the_field_as_ever(picking):
    pg, host, w = picking
    ready(pg)
    open_field(pg)
    pg.locator(".table-title__pt").click()
    pg.wait_for_selector(".hand-field", state="detached", timeout=WAIT_MS)


# -- the box (the desktop) ------------------------------------------------------------------------------------------------------------------------------------------------------

def test_a_drag_from_the_empty_place_draws_the_dashed_box_and_takes_the_parts_it_covers_shift_adds(picking):
    pg, host, w = picking
    if w != "wide":
        pytest.skip("the desktop's mouse")
    ready(pg)
    open_field(pg)
    (x0, y0), (x1, y1) = around(pg, ["server/lobby.ts", "server/rooms.ts"])
    pg.mouse.move(x0, y0)
    pg.mouse.down()
    pg.mouse.move((x0 + x1) / 2, (y0 + y1) / 2, steps=4)
    pg.mouse.move(x1, y1, steps=4)
    box = pg.locator(".pick-box")
    box.wait_for(timeout=WAIT_MS)
    assert "ork-box" in box.get_attribute("class")
    assert pg.evaluate("() => getComputedStyle(document.querySelector('.pick-box')).borderTopStyle") == "dashed"
    shot(pg, f"picking-box-drawing-{w}.png")
    pg.mouse.up()
    pg.wait_for_selector(".pick-box", state="detached", timeout=WAIT_MS)
    assert chips(pg) == ["server/lobby.ts", "server/rooms.ts"]
    assert pg.locator(".table-back").count() == 0 and field(pg).count() == 1
    shot(pg, f"picking-box-taken-{w}.png")
    (a0, b0), (a1, b1) = around(pg, ["client/net.ts"])
    drag(pg, (a0, b0), (a1, b1), shift=True)
    assert chips(pg) == ["server/lobby.ts", "server/rooms.ts", "client/net.ts"], "Shift adds to what was taken"
    drag(pg, (a0, b0), (a1, b1))
    assert chips(pg) == ["client/net.ts"], "a box without Shift takes the map's marks anew"


def test_a_box_that_takes_a_whole_container_pins_it_and_one_over_the_whole_map_pins_the_map_and_sends_no_mark(picking):
    pg, host, w = picking
    if w != "wide":
        pytest.skip("the desktop's mouse")
    ready(pg)
    open_field(pg, "A goal for the server")
    drag(pg, *around(pg, PARTS["server"]))
    assert chips(pg) == ["server"] and pg.locator(".pick-chip").inner_text().strip() == "server/", "all of a container's parts pin the container"
    assert all("ork-picked" in part(pg, p).get_attribute("class") for p in PARTS["server"])
    shot(pg, f"picking-group-{w}.png")
    pg.get_by_role("button", name="Take server/ off").click()
    assert chips(pg) == [] and pg.locator(".ork-picked").count() == 0
    drag(pg, *around(pg, PARTS["server"] + PARTS["client"]))
    assert chips(pg) == ["all"] and pg.locator(".pick-chip").inner_text().strip() == "all of System"
    shot(pg, f"picking-map-{w}.png")
    pg.get_by_role("button", name="Send").click()
    pg.wait_for_selector(".hand-field", state="detached", timeout=WAIT_MS)
    sent = host.sent()[-1]
    assert sent["party"] == "tech" and "marks" not in sent, "the whole map reads as no mark"
    open_field(pg, "Another")
    drag(pg, *around(pg, PARTS["server"]))
    pg.get_by_role("button", name="Send").click()
    pg.wait_for_selector(".hand-field", state="detached", timeout=WAIT_MS)
    assert host.sent()[-1]["marks"] == [{"map": "system", "group": "server", "name": "server/"}]


def test_a_press_on_a_part_of_a_pinned_group_leaves_the_others_marked(picking):
    pg, host, w = picking
    if w != "wide":
        pytest.skip("the desktop's mouse")
    ready(pg)
    open_field(pg)
    drag(pg, *around(pg, PARTS["server"] + PARTS["client"]))
    assert chips(pg) == ["all"]
    part(pg, "client/hud.ts").click()
    assert chips(pg) == ["server", "client/net.ts", "client/menu.ts"], "the server stays a group, the client's other parts are marked one by one"
    assert "ork-picked" not in part(pg, "client/hud.ts").get_attribute("class")


def test_a_drag_that_starts_on_a_part_draws_no_box_and_marks_nothing(picking):
    pg, host, w = picking
    if w != "wide":
        pytest.skip("the desktop's mouse")
    ready(pg)
    open_field(pg)
    b = centre(pg, "server/lobby.ts")
    pg.mouse.move(b["x"] + 20, b["y"] + 20)
    pg.mouse.down()
    pg.mouse.move(b["x"] + 220, b["y"] + 120, steps=4)
    assert pg.locator(".pick-box").count() == 0
    pg.mouse.up()
    assert chips(pg) == [] and pg.locator(".table-back").count() == 0


# -- a touch screen ------------------------------------------------------------------------------------------------------------------------------------------------------------------

def test_a_long_press_on_the_empty_place_then_a_drag_draws_the_box_on_a_touch_screen_and_a_drag_alone_scrolls(picking):
    pg, host, w = picking
    if w != "narrow":
        pytest.skip("a touch screen")
    ready(pg)
    open_field(pg)
    (x0, y0), (x1, y1) = around(pg, ["server/index.ts", "server/lobby.ts"], pad=3)
    long_press_drag(pg, (30, y0), (x1, y1))                                         # from the empty place at the left (a finger's touch snaps to a card within a few pixels of it)
    pg.wait_for_selector(".pick-box", state="detached", timeout=WAIT_MS)
    assert set(chips(pg)) >= {"server/index.ts", "server/lobby.ts"}, "the long press, then the drag, took what the box covered"
    shot(pg, f"picking-touch-box-{w}.png")


def test_a_drag_alone_on_a_touch_screen_scrolls_the_map_and_draws_no_box(picking):
    pg, host, w = picking
    if w != "narrow":
        pytest.skip("a touch screen")
    ready(pg)
    open_field(pg)
    scroller = pg.locator(".table-sys .sys-scroll")
    before = scroller.evaluate("e => e.scrollLeft")
    y = part(pg, "server/index.ts").bounding_box()["y"] + 40
    cdp = pg.context.new_cdp_session(pg)
    point = lambda x: [{"x": x, "y": y, "id": 1}]  # noqa: E731
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": point(90)})
    for x in range(86, 20, -6):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": point(x)})
        pg.wait_for_timeout(16)
    assert pg.locator(".pick-box").count() == 0
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(300)
    assert scroller.evaluate("e => e.scrollLeft") > before, "a drag is the scroll"
    assert chips(pg) == []


# -- the chips -----------------------------------------------------------------------------------------------------------------------------------------------------------------------

def test_past_five_chips_it_says_and_n_more_in_words_and_a_press_shows_all(picking):
    pg, host, w = picking
    ready(pg)
    open_field(pg)
    for p in PARTS["server"] + PARTS["client"]:
        part(pg, p).dispatch_event("click")                                         # the field covers the map's foot at the narrow width: the press itself is not what is tried here
    pg.locator(".pick-more").wait_for(timeout=WAIT_MS)
    assert len(chips(pg)) == 5 and pg.locator(".pick-more").inner_text().strip() == "and 2 more"
    shot(pg, f"picking-chips-{w}.png")
    pg.locator(".pick-more").click()
    assert len(chips(pg)) == 7 and pg.locator(".pick-more").count() == 0
    assert field(pg).bounding_box()["x"] >= 0 and field(pg).bounding_box()["x"] + field(pg).bounding_box()["width"] <= pg.viewport_size["width"]
    pg.get_by_role("button", name="Take client/hud.ts off").click()
    assert len(chips(pg)) == 6


# -- how it ends ---------------------------------------------------------------------------------------------------------------------------------------------------------------------

def test_esc_with_the_focus_on_the_map_ends_picking_and_keeps_the_marks_and_the_field(picking):
    pg, host, w = picking
    ready(pg)
    open_field(pg)
    b = part(pg, "server/lobby.ts")
    b.scroll_into_view_if_needed()
    b.click()
    b.focus()
    pg.keyboard.press("Escape")
    pg.wait_for_selector(".pick-strip", state="detached", timeout=WAIT_MS)
    assert field(pg).count() == 1 and chips(pg) == ["server/lobby.ts"], "picking ended; what was taken stays the idea's marks"
    assert pg.locator(".ork-picked").count() == 0, "the brackets are for a map in picking"


def test_taking_the_address_off_ends_picking_and_the_text_addressing_it_again_begins_it(picking):
    pg, host, w = picking
    ready(pg)
    open_field(pg)
    pg.get_by_role("button", name="Take off Tech").click()
    pg.wait_for_selector(".pick-strip", state="detached", timeout=WAIT_MS)
    pg.locator(".hand-field__text").fill("@Tech the lobby")
    pg.locator(".pick-strip").wait_for(timeout=WAIT_MS)


def test_stop_picking_holds_until_the_field_is_closed_and_opened_again(picking):
    pg, host, w = picking
    ready(pg)
    open_field(pg)
    pg.get_by_role("button", name="Stop picking").click()
    pg.wait_for_selector(".pick-strip", state="detached", timeout=WAIT_MS)
    pg.locator(".hand-field__text").press("Escape")
    pg.wait_for_selector(".hand-field", state="detached", timeout=WAIT_MS)
    open_field(pg)
    pg.locator(".pick-strip").wait_for(timeout=WAIT_MS)


def test_a_party_named_with_at_is_picked_on_its_own_map_and_the_strip_on_another_tab_offers_it_as_a_link(picking):
    pg, host, w = picking
    open_field(pg, "@Tech the lobby")
    strip = pg.locator(".pick-strip")
    strip.wait_for(timeout=WAIT_MS)
    link = strip.get_by_role("button", name="Open Tech's map to pick")
    assert pg.locator(".table-tab[aria-selected=true]").get_attribute("data-tab") == "orkmaster", "the person's tab is kept"
    shot(pg, f"picking-open-link-{w}.png")
    link.click()
    pg.locator(".table-tab[data-tab=tech][aria-selected=true]").wait_for(timeout=WAIT_MS)
    pg.locator(".table-sys .sys[data-state=shown]").wait_for(timeout=WAIT_MS)
    assert " ".join(pg.locator(".pick-strip").inner_text().split()) == "Pick a part to point at it Stop picking"
    assert field(pg).count() == 1 and pg.locator(".hand-field__text").input_value() == "@Tech the lobby"


def test_another_partys_tab_in_picking_has_the_link_to_the_party_addressed(picking):
    pg, host, w = picking
    open_tab(pg, "game")
    open_field(pg, "@Tech the lobby")
    assert pg.locator(".pick-strip__open").inner_text().strip() == "Open Tech's map to pick"
    assert pg.locator(".pick-host[data-picking]").count() == 0


# -- another map, drawn with Pickable ---------------------------------------------------------------------------------------------------------------------------------------------

def test_a_map_drawn_with_pickable_is_picked_the_same_a_lane_a_group_the_map_all_of_it(picking):
    pg, host, w = picking
    pg.evaluate(STUB_MAP)
    open_tab(pg, "art")
    pg.locator(".stub-map").wait_for(timeout=WAIT_MS)
    open_field(pg, "Art for the towers")
    card = lambda i: pg.locator(f'[data-card="{i}"]')  # noqa: E731
    card("hero.png").click()
    assert chips(pg) == ["hero.png"] and "ork-picked" in card("hero.png").get_attribute("class")
    if w == "wide":
        a = card("hit.wav").bounding_box()
        b = card("win.wav").bounding_box()
        drag(pg, (a["x"] - 8, a["y"] - 8), (b["x"] + b["width"] + 8, b["y"] + b["height"] + 8))
        assert chips(pg) == ["sound"] and pg.locator(".pick-chip").inner_text().strip() == "sound/", "a lane's cards pin the lane"
        shot(pg, f"picking-lane-{w}.png")
        pg.get_by_role("button", name="Send").click()
        pg.wait_for_selector(".hand-field", state="detached", timeout=WAIT_MS)
        assert host.sent()[-1]["marks"] == [{"map": "assets", "group": "sound", "name": "sound/"}]
