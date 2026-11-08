"""Spec 165 part J, a goal's reach lit, dimmed and said on a leader's map (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §280.1, §280.3, §280.4), in a real browser at 1280 x 800, the host faked.

`ideas.reach {party}` answers `{party, map, goals: {slug: {lit, one, two, no_test}}}`: with Tech's System open, the goal under the pointer or focus in the hand (else the goal picked) lights the parts its *Will be* names
(`data-reach="lit"`, a solid edge in its element), one step out dashed, two dotted, the rest dimmed, and a line says *changes*, *reaches* and *no test* in words. Hover and focus light the same; hovering sends no command;
leaving the hand, Esc and a goal with no entry clear it all; a touch press lights nothing."""
from __future__ import annotations

import os

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_concerns_desktop_browser import INDEX, LOBBY, ROOMS, ConcernHost  # noqa: E402
from tests.test_heat_desktop_browser import open_tab  # noqa: E402

pytestmark = pytest.mark.browser

REACH = "hand/reachhover.js"
ENTRY = {"lit": [LOBBY], "one": [ROOMS], "two": [], "no_test": [ROOMS]}


class ReachHost(ConcernHost):
    def __init__(self):
        super().__init__()
        self.reach = {"tech": {"timer": dict(ENTRY), "seat": {"lit": [], "one": [], "two": [], "no_test": []}}}
        self.reach_asked = 0
        asked = [{"ask": "Where does the seat live?", "choices": ["In the room", "In the socket"], "pick": None, "why": "", "by": None, "look": False}]
        for n in self.nodes:
            if n["slug"] == "timer":                                                                  # a goal asking: a card of the hand, its reach on Tech's System kept
                n.update(state="asks", asks_you=True, asked=asked)
        self.needs.append({"kind": "asks", "goal": "game", "idea": "timer", "title": "Round timer shows on every phone", "text": asked[0]["ask"], "at": "2026-10-20T09:30:00", "priority": "normal", "blocks": False, "asked": asked})

    def handle(self, name, a):
        if name == "ideas.reach":
            self.log.append((name, a))
            self.reach_asked += 1
            return {"party": a["party"], "map": "", "goals": {k: dict(v) for k, v in self.reach.get(a["party"], {}).items()}}
        return super().handle(name, a)


def state(pg, pid):
    return pg.locator(f'[data-pick-id="{pid}"]').first.get_attribute("data-reach")


def name_goal(pg, slug):
    pg.evaluate("([m, s]) => import(m).then((x) => { x.reachGoal.value = s; })", [f"/static/js/{REACH}", slug])


def opened(gui):
    host = ReachHost()
    pg, errors = open_tab(gui, host, "tech", ".table-sys .sys[data-state=shown]")
    pg.wait_for_function("() => import('/static/js/table/reach.js').then((x) => Object.keys(x.reachData.value).length > 0)", timeout=WAIT_MS)
    return host, pg, errors


def test_a_goal_named_lights_its_parts_dims_the_rest_and_the_line_says_it_in_words(gui):
    host, pg, errors = opened(gui)
    assert state(pg, LOBBY) is None and pg.locator(".rc-line").is_hidden()
    sent = len(host.log)
    name_goal(pg, "timer")
    pg.wait_for_function(f"() => document.querySelector('[data-pick-id=\"{LOBBY}\"]')?.dataset.reach === 'lit'", timeout=WAIT_MS)
    assert state(pg, LOBBY) == "lit" and state(pg, ROOMS) == "one" and state(pg, INDEX) == "dim"
    line = pg.locator(".rc-line")
    assert line.get_attribute("aria-live") == "polite"
    text = line.inner_text()
    assert text.startswith("changes ") and " · reaches " in text and " · no test " in text and not any(c.isdigit() for c in text)
    assert [n for n, _ in host.log[sent:] if n != "ideas.night"] == [], "lighting sends no command"
    outline = pg.locator(f'[data-pick-id="{LOBBY}"]').first.evaluate("e => getComputedStyle(e.classList.contains('pick') ? e.firstElementChild : e).outlineStyle")
    assert outline == "solid"
    assert pg.locator(f'[data-pick-id="{ROOMS}"]').first.evaluate("e => getComputedStyle(e.classList.contains('pick') ? e.firstElementChild : e).outlineStyle") == "dashed"
    assert not errors, "\n".join(errors)
    pg.context.close()


def test_leaving_esc_and_a_goal_with_no_will_be_clear_it_all(gui):
    host, pg, errors = opened(gui)
    for slug in ("timer", "seat", "unknown"):
        name_goal(pg, "timer")
        pg.wait_for_function(f"() => document.querySelector('[data-pick-id=\"{LOBBY}\"]')?.dataset.reach === 'lit'", timeout=WAIT_MS)
        name_goal(pg, slug)
        if slug == "timer":
            pg.keyboard.press("Escape")
        pg.wait_for_function("() => document.querySelectorAll('[data-reach]').length === 0", timeout=WAIT_MS)
        assert pg.locator(".rc-line").is_hidden()
    assert not errors, "\n".join(errors)
    pg.context.close()


def test_the_pointer_resting_on_a_hand_card_and_focus_light_the_same_reach_with_no_command(gui):
    host, pg, errors = opened(gui)
    card = pg.locator('.hand-card[data-goal="timer"]').first
    card.wait_for(timeout=WAIT_MS)
    sent = len(host.log)
    box = card.bounding_box()
    pg.mouse.move(box["x"] + 10, box["y"] + 24)
    pg.wait_for_function(f"() => document.querySelector('[data-pick-id=\"{LOBBY}\"]')?.dataset.reach === 'lit'", timeout=WAIT_MS)
    by_hover = pg.locator(".rc-line").inner_text()
    pg.mouse.move(5, 5)
    pg.wait_for_function("() => document.querySelectorAll('[data-reach]').length === 0", timeout=WAIT_MS)
    card.focus()
    pg.wait_for_function(f"() => document.querySelector('[data-pick-id=\"{LOBBY}\"]')?.dataset.reach === 'lit'", timeout=WAIT_MS)
    assert pg.locator(".rc-line").inner_text() == by_hover
    assert [n for n, _ in host.log[sent:] if n != "ideas.night"] == [], host.log[sent:]   # the night poll is the page's own clock
    assert not errors, "\n".join(errors)
    pg.context.close()


def test_a_touch_press_on_a_hand_card_lights_nothing(gui):
    host, pg, errors = opened(gui)
    pg.locator('.hand-card[data-goal="timer"]').first.wait_for(timeout=WAIT_MS)
    pg.evaluate("""() => { const el = document.querySelector('.hand-card[data-goal="timer"]');
      for (const t of ['pointerover', 'pointerdown']) el.dispatchEvent(new PointerEvent(t, { bubbles: true, pointerType: 'touch' })); }""")
    pg.wait_for_timeout(400)
    assert pg.locator("[data-reach]").count() == 0
    assert not errors, "\n".join(errors)
    pg.context.close()


# Part K: dimmed, yet read; the edges seen (decisions §183.5, §280.3).
MEASURE = """(arg) => {
  const [sel, which] = arg;
  const lum = (c) => { const m = c.match(/[\\d.]+/g).map(Number); const rgb = m.slice(0, 3).map((v) => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722; };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const opaque = (el) => { for (let e = el; e; e = e.parentElement) { const c = getComputedStyle(e).backgroundColor; const a = c.match(/[\\d.]+/g); if (a && (a.length < 4 || Number(a[3]) > 0.99)) return c; } return 'rgb(0, 0, 0)'; };
  const card = document.querySelector(sel), el = card.classList.contains('pick') ? card.firstElementChild : card;
  const felt = getComputedStyle(document.getElementById('table-pane')).backgroundColor;
  if (which === 'name') {
    const name = el.querySelector('.sys-part__name') || el;
    return { ratio: ratio(getComputedStyle(name).color, opaque(name)), opacity: getComputedStyle(el).opacity };
  }
  const cs = getComputedStyle(el);
  return { ratio: ratio(cs.outlineColor, felt), style: cs.outlineStyle, width: cs.outlineWidth };
}"""


@pytest.mark.parametrize("out", [False, True])
def test_a_dimmed_name_reads_at_4_5_and_the_edges_stand_at_3_against_the_felt_lamp_lit_and_out(gui, out):
    host, pg, errors = opened(gui)
    if out:
        pg.evaluate("() => document.getElementById('table-pane').classList.add('is-out')")
    name_goal(pg, "timer")
    pg.wait_for_function(f"() => document.querySelector('[data-pick-id=\"{LOBBY}\"]')?.dataset.reach === 'lit'", timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    dim = pg.evaluate(MEASURE, [f'[data-pick-id="{INDEX}"]', "name"])
    assert state(pg, INDEX) == "dim" and dim["opacity"] == "1" and dim["ratio"] >= 4.5, dim      # the frame and the window go down, never the name's ink
    for pid, style in ((LOBBY, "solid"), (ROOMS, "dashed")):
        edge = pg.evaluate(MEASURE, [f'[data-pick-id="{pid}"]', "edge"])
        assert edge["style"] == style and edge["ratio"] >= 3, edge
    one = pg.evaluate(MEASURE, [f'[data-pick-id="{ROOMS}"]', "edge"])
    lit = pg.evaluate(MEASURE, [f'[data-pick-id="{LOBBY}"]', "edge"])
    if os.environ.get("REACH_PICTURES"):
        pg.screenshot(path=f"{os.environ['REACH_PICTURES']}/reach-system-{'out' if out else 'lit'}.png")
    assert float(one["width"][:-2]) > 1 and float(one["width"][:-2]) >= float(lit["width"][:-2])   # a dash heavier than orkUI's disabled hairline
    assert not errors, "\n".join(errors)
    pg.context.close()
