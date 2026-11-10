"""Spec 123 part F (docs/specs/123-the-leaders-at-the-table.md §7, §8; decisions §201), the tabs as the table's far side, in a real browser at both widths (`tests/narrow.py`: 1280 × 800 and 390 × 844)
against a stub host that is the maps' (`ConcernHost`: Tech and Game design with a record of concerns each) and the bubble's (`AskHost`) at once, with the leaders' races as the real host sends them (shaman, unicorn, dryad, lich, fairy).

The open head is 48 x 44 and the others 36 x 33 (36 at the narrow width), the open tab has no fill and no bar, its head 3 px lower over the rim, its name in the ink and the leader's own name under it (the project's: *the Orkmaster*), the others'
names muted; the party's header has no *Leads*, the sword and the shield with their tools, a role under each head; the open head is a button of its own in the tab's cell (no button holds a button): pressed it opens the bubble, the field focused,
Enter asks, the answer and *Make it a goal*, Esc closes it and the head has the focus; its marks (the alert sign, the dot) are buttons stepping through the marked parts; the faces by mood (a party's tasks at work focused, an alert worried,
a spent tool asleep, a hearing's drop no, a goal done while the page was open pleased and none for what was found there); a chair under each head at the wide width and none under 760 px; the empty chair deals its crafts to the hand on the wide page (decisions §272; the narrow one opens the parties' place) and is gone when
every craft is at the table, and stays when the host gives no list; the die's front face halts (spec 139 A, decisions §246: no door in the top row), says *Stopped* (`aria-disabled`), refuses a second press and goes back when a task runs or a goal is started; the tabs' row and the hand on the room's
colour with a 3 px rim, no divider between the tabs (the lanes keep theirs); no sideways scroll; under reduced motion nothing is pulled out. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_ask_desktop_browser import ANSWER, AskHost, record as answer  # noqa: E402
from tests.test_concerns_desktop_browser import GAME, TECH, ConcernHost, concern, record  # noqa: E402
from tests.test_table_desktop_browser import HEAD, node, party, shot, tab, title, watch  # noqa: E402

pytestmark = pytest.mark.browser

RACES = {"game": "unicorn", "tech": "shaman", "art": "dryad", "release": "lich", "market": "fairy"}
CRAFT = {"game": "product", "tech": "engineering", "art": "design", "release": "product", "market": "marketing"}
SPENT = [{"provider": "claude", "name": "Claude", "left": 0.0, "rows": [{"window": "5h", "left": 0.0, "reset": "2099-01-01T00:00:00"}]},
         {"provider": "codex", "name": "Codex", "left": 0.18, "rows": [{"window": "daily", "left": 0.18, "reset": ""}]}]
PRESETS = [{"id": slug, "group": "stage", "locked": False, "leader": slug} for slug in ("game", "tech", "art", "market", "run")] + [{"id": "release", "group": "stage", "locked": True, "leader": "release"},
                                                                                                                                 {"id": "mixed", "group": "own", "locked": False, "leader": "taskmaster"}]


def hearing(drop="art"):
    """A Talk's hearing as the host's Needs you row has it (spec 120 §4): a side that drops the goal, held by `drop`'s leader, and the side that does it."""
    return {"kind": "hearing", "idea": "timer", "moment": "talk", "heading": "Art says no", "text": "Art says no", "own": True, "left_out": 0,
            "sides": [{"dir": "right", "kind": "go", "leaders": ["tech"], "names": ["Architect"], "also": [], "line": "Do it", "outcome": "go"},
                      {"dir": "left", "kind": "drop", "leaders": [drop], "names": [drop], "also": [], "line": "Drop it", "outcome": "drop"}]}


class LeadersHost(ConcernHost, AskHost):
    """The maps' host with the bubble's commands, the leaders' races, and what the tabs read: the limits (`spent`), the parties' recipes (`presets`: none, as an older host), the door (`halt` stops every task)."""

    def __init__(self, presets=None):
        super().__init__()
        for p in self.parties:
            p["leader"] = {**p["leader"], "head": HEAD(RACES[p["slug"]], "elder", CRAFT[p["slug"]])}
            p["party"][0] = {**p["party"][0], "head": p["leader"]["head"]}
        self.records["tech"]["rubric"] = None
        self.spent = False
        self.presets = presets
        self.halted = 0

    def snapshot(self):
        doc = super().snapshot()
        if self.spent:
            doc["state"]["limits"] = copy.deepcopy(SPENT)
        return doc

    def board(self):
        doc = super().board()
        for t in doc["tracks"]:
            t["recipe"] = t["slug"]
        return doc

    def handle(self, name, a):
        if name == "ideas.party_presets" and self.presets is not None:
            self.log.append((name, a))
            return {"kind": {"id": "code", "words": "code"}, "presets": copy.deepcopy(self.presets)}
        if name == "halt":
            self.log.append((name, a))
            self.halted += 1
            for n in self.nodes:
                for t in n.get("tasks", []):
                    if t["state"] in ("running", "testing"):
                        t["state"] = "done"
            self.rev += 1
            return {"stopped": 3}
        return super().handle(name, a)

    def change(self):
        self.rev += 1
        self.ws.send(json.dumps(self.snapshot()))


def start(gui, width, host=None, **context):
    errors: list[str] = []
    server, browser = gui
    host = host or LeadersHost()
    pg = browser.new_context(**{**(narrow.WIDE if width == "wide" else narrow.FINE), **context}).new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    return pg, host, errors


@pytest.fixture(params=narrow.WIDTHS)
def desk(gui, request):
    pg, host, errors = start(gui, request.param)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.fixture
def wide(gui):
    pg, host, errors = start(gui, "wide")
    yield pg, host
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def cell(pg, slug):
    """A tab's cell; the Orkmaster's at the wide width is the column's head (spec 128 B.2)."""
    return pg.locator(f'.table-tabcell[data-cell="{slug}"], .col-head') if slug == "orkmaster" else pg.locator(f'.table-tabcell[data-cell="{slug}"]')


def go(pg, slug):
    tab(pg, slug).click()
    pg.locator(f'.table-tab[data-tab="{slug}"][aria-selected="true"], .col-head__tab[data-tab="{slug}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
    pg.wait_for_function("(s) => document.querySelector(`.table-tabcell[data-cell=\"${s}\"] img.ork-race__head, .col-head img.ork-race__head`)?.complete", arg=slug, timeout=WAIT_MS)


def face(pg, slug):
    """The file of a tab's head, minus the folder and the size: `shaman-elder-worried`, `shaman-elder` for calm."""
    src = cell(pg, slug).locator("img.ork-race__head").get_attribute("src").rsplit("/", 1)[1]
    return src.removesuffix(".png").removesuffix("@2x")


def mood(pg, slug):
    return cell(pg, slug).locator("img.ork-race__head").get_attribute("data-mood")


def paint(pg, token, prop="color"):
    return pg.evaluate("([t, p]) => { const e = document.createElement('i'); e.style[p] = `var(${t})`; document.body.append(e); const c = getComputedStyle(e)[p]; e.remove(); return c; }", [token, prop])


def waits(pg, slug, want):
    pg.wait_for_function("([s, m]) => document.querySelector(s === 'orkmaster' ? '.col-head img.ork-race__head, .table-tabcell[data-cell=orkmaster] img.ork-race__head' : `.table-tabcell[data-cell=\"${s}\"] img.ork-race__head`)?.dataset.mood === (m || undefined)", arg=[slug, want], timeout=WAIT_MS)


# -- the heads ----------------------------------------------------------------------------------------------------------------------------------------

def test_the_open_head_is_large_the_others_36_the_open_tab_has_no_fill_and_the_leaders_name_under_its_party_s(desk):
    pg, host, w = desk
    big = w == "wide"
    go(pg, "tech")
    box = lambda slug: cell(pg, slug).locator("img.ork-race__head").bounding_box()          # noqa: E731
    assert (box("tech")["width"], box("tech")["height"]) == ((48, 44) if big else (36, 33))
    for slug in ("orkmaster", "game", "art", "market"):
        assert (box(slug)["width"], box(slug)["height"]) == ((24, 22) if big and slug == "orkmaster" else (36, 33)), slug      # the Orkmaster's head in the column (spec 128 B.2) is the small size
    nav, rim = pg.locator(".table-tabs").bounding_box(), pg.locator(".table-tabs").evaluate("e => parseFloat(getComputedStyle(e).borderBottomWidth)")
    assert rim == 3 and abs(box("tech")["y"] + box("tech")["height"] - (nav["y"] + nav["height"])) <= 1, "the open head 3 px lower, over the table's rim"
    assert abs(box("game")["y"] + box("game")["height"] - (nav["y"] + nav["height"] - 3)) <= 1, "the others stand on the rim"
    assert nav["height"] >= (60 if big else 52) and nav["height"] <= (72 if big else 62)   # 72: orkUI 0.40's Rubik grew the tab name's line by a pixel (71)
    open_tab_box = tab(pg, "tech")
    fill, rule = open_tab_box.evaluate("e => [getComputedStyle(e).backgroundColor, getComputedStyle(e).boxShadow]")
    assert fill == "rgba(0, 0, 0, 0)" and (not big or "0px -3px 0px 0px inset" in rule), "no fill on the open tab, its party's colour is the rule under it (decisions §268.1, §275.1)"
    assert not big or tab(pg, "game").evaluate("e => getComputedStyle(e).boxShadow") != "none", "a closed tab has the thin rule of its party under it"
    if big:
        assert cell(pg, "tech").locator(".table-tab__who").text_content() == "Architect" and cell(pg, "game").locator(".table-tab__who").count() == 0
        assert open_tab_box.locator(".table-tab__main").evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-ink")
        assert tab(pg, "game").locator(".table-tab__main").evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-ink"), "a tab's name is the light ink, open or closed (decisions §275.1)"
        assert open_tab_box.locator(".table-tab__who").evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-ink-muted")
        go(pg, "orkmaster")
        # the column's head says the project (its name), not "The Orkmaster": the head's aria-label/title still name it (decisions §272.5)
        assert cell(pg, "orkmaster").evaluate("e => !!e.closest('.frame-column')") and cell(pg, "orkmaster").get_attribute("aria-label") == "The Orkmaster"
        assert tab(pg, "orkmaster").evaluate("e => getComputedStyle(e).backgroundColor") == "rgba(0, 0, 0, 0)"
    shot(pg, f"leaders-tabs-{w}.png")


def test_the_header_has_no_leads_the_sword_and_the_shield_with_their_tools_and_a_role_under_each_head(wide):
    pg, host = wide
    go(pg, "tech")
    pg.get_by_role("button", name="Tech's menu").click()                                       # the seats and tools lie in the leader's inventory now (spec 168 E1)
    pg.get_by_role("menuitem", name="Seats and tools").click()
    head = pg.locator(".stall-seats")
    head.wait_for(timeout=WAIT_MS)
    assert "Leads" not in head.inner_text() and head.get_by_role("group", name="Leads").count() == 0
    sides = head.locator(".table-side")
    assert sides.count() == 2 and [s.locator(".ork-sign").get_attribute("class").split()[-1] for s in sides.all()] == ["sword", "shield"]
    assert all(s.get_attribute("title").split(" on ")[0] in ("Does", "Checks") and s.locator(".ork-mark").count() == 1 for s in sides.all()), "each side says its tool"
    assert [r.text_content() for r in head.locator(".table-seat__role").all()] == ["Grunts", "Tester", "Reviewer"]
    assert head.locator(".table-seat__role").first.evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-ink-muted")


# -- the open head: a button of its own, the bubble ---------------------------------------------------------------------------------------------------------

def test_the_open_head_is_a_button_of_its_own_beside_the_tab_s_and_no_button_holds_a_button(wide):
    pg, host = wide
    go(pg, "tech")
    assert pg.evaluate("() => [...document.querySelectorAll('button')].filter((b) => b.querySelector('button')).length") == 0, "no button holds a button"
    head = pg.locator('[data-ask-head="tech"]')
    assert head.count() == 1 and head.get_attribute("aria-label") == "Ask the Architect" and head.get_attribute("aria-haspopup") == "dialog" and head.get_attribute("aria-expanded") == "false"
    assert head.evaluate("e => !e.closest('[role=tab]')") and head.locator("img.ork-race__head").count() == 1
    assert pg.locator("[data-ask-head]").count() == 1, "the open tab's head only"
    go(pg, "orkmaster")
    ask = pg.locator("[data-ask-head]")
    assert ask.get_attribute("data-ask-head") == "orkmaster" and ask.get_attribute("aria-haspopup") == "dialog" and ask.get_attribute("role") == "tab", "the Orkmaster's head is its tab, the column's (spec 128 B.2): pressed again it asks"
    assert ask.get_attribute("aria-label") == "The Orkmaster · shop" and "Press again to ask it" in ask.get_attribute("title")


def test_the_head_pressed_opens_the_bubble_focused_enter_asks_the_answer_makes_a_goal_and_esc_closes_it(wide):
    pg, host = wide
    go(pg, "tech")
    head = pg.locator('[data-ask-head="tech"]')
    head.click()
    pg.locator(".table-ask__bubble").wait_for(timeout=WAIT_MS)
    assert head.get_attribute("aria-expanded") == "true" and pg.evaluate("() => document.activeElement.className").endswith("table-ask__field")
    pg.keyboard.type("Why does the timer run on the server?")
    pg.keyboard.press("Enter")
    pg.locator(".table-ask__reading").wait_for(timeout=WAIT_MS)
    assert host.sent("ideas.ask") == [{"party": "tech", "q": "Why does the timer run on the server?"}]
    host.put(answer("answered", "tech"))
    pg.locator(".table-ask__text").wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-ask__text").inner_text() == ANSWER
    goal = pg.get_by_role("button", name="Make it a goal")
    goal.click()
    pg.wait_for_function("() => !document.querySelector('.table-ask__bubble')", timeout=WAIT_MS)
    assert host.sent("ideas.ask_goal") == [{}]
    host.put(None)
    head.click()
    pg.locator(".table-ask__bubble").wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.querySelector('.table-ask__bubble')", timeout=WAIT_MS)
    assert head.get_attribute("aria-expanded") == "false" and pg.evaluate("() => document.activeElement.dataset.askHead") == "tech", "the head has the focus back"
    head.click()
    pg.locator(".table-ask__bubble").wait_for(timeout=WAIT_MS)
    head.click()                                                                                                         # the head again puts it away
    pg.wait_for_function("() => !document.querySelector('.table-ask__bubble')", timeout=WAIT_MS)
    go(pg, "orkmaster")
    pg.locator('[data-ask-head="orkmaster"]').click()
    pg.locator(".table-ask__field").wait_for(timeout=WAIT_MS)
    pg.keyboard.type("Where are we?")
    pg.keyboard.press("Enter")
    pg.locator(".table-ask__reading").wait_for(timeout=WAIT_MS)
    assert host.sent("ideas.ask")[-1] == {"party": "", "q": "Where are we?"}


def test_no_head_opens_a_bubble_at_the_narrow_width_and_the_open_one_is_no_button(gui):
    pg, host, errors = start(gui, "narrow")
    go(pg, "tech")
    assert pg.locator("[data-ask-head]").count() == 0 and cell(pg, "tech").locator("img.ork-race__head").count() == 1
    shot(pg, "leaders-tabs-narrow-open.png")
    pg.context.close()
    assert not errors, "\n".join(errors)


# -- its marks ----------------------------------------------------------------------------------------------------------------------------------------

def test_the_marks_beside_the_open_head_step_through_the_marked_parts(desk):
    pg, host, w = desk
    go(pg, "tech")
    pg.locator(".table-sys .sys[data-state=shown]").wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => document.querySelectorAll('[data-concern]').length >= 2", timeout=WAIT_MS)
    marks = cell(pg, "tech").locator(".table-mark")
    alert, note = marks.locator("xpath=.").filter(has=pg.locator(".ork-sign.alert")), cell(pg, "tech").locator(".table-mark.is-note")
    assert marks.count() == 2 and alert.count() == 1 and note.count() == 1
    assert alert.get_attribute("aria-label") == "The Architect: 1 alert, step through it" and note.get_attribute("aria-label") == "The Architect: 2 notes, step through them"
    assert alert.evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-alert") and note.evaluate("e => e.closest('[role=tab]') === null")
    assert pg.locator("[role=tab] .table-mark").count() == 0, "no button inside a tab's button"
    assert cell(pg, "tech").locator(".table-tab__alert").count() == 0, "the open tab's alert is its mark"
    alert.click()
    pg.locator("[data-concern=alert].is-lifted, [data-concern=alert][aria-pressed=true]").first.wait_for(timeout=WAIT_MS)
    note.click()
    pg.locator("[data-concern=note].is-lifted, [data-concern=note][aria-pressed=true]").first.wait_for(timeout=WAIT_MS)
    if w == "wide":
        shot(pg, "leaders-marks-wide.png")
    other = cell(pg, "game")                                                                                             # another tab keeps its alert sign as today
    assert other.locator(".table-tab__alert").count() == 1 and other.locator(".table-mark").count() == 0
    host.records["tech"] = record(status="looking", rubric=None)
    host.records["tech"]["concerns"] = copy.deepcopy(TECH)
    host.change()
    if w == "wide":
        pg.wait_for_function("() => document.querySelector('[data-ask-head=\"tech\"]').title === 'The Architect is looking at the table'", timeout=WAIT_MS)       # while it looks, the head says so


# -- the faces ----------------------------------------------------------------------------------------------------------------------------------------

def test_the_faces_follow_the_state_a_party_at_work_focused_an_alert_worried_a_spent_tool_asleep(wide):
    pg, host = wide
    go(pg, "art")                                                                                                        # an open tab with no mark and no work: calm
    assert mood(pg, "art") is None and face(pg, "art") == "dryad-elder"
    assert mood(pg, "tech") == "worried" and face(pg, "tech") == "shaman-elder-worried" and mood(pg, "game") == "worried", "an alert on the map"
    assert cell(pg, "tech").locator("img.ork-race__head").get_attribute("src").endswith("-worried@2x.png")
    host.records["tech"] = record(rubric=None)                                                                           # nothing wrong any more: the party's task at work says it
    host.records["game"] = record(rubric=None)
    host.change()
    waits(pg, "tech", "focused")
    assert face(pg, "tech") == "shaman-elder-focused" and mood(pg, "game") == "focused" and mood(pg, "market") is None
    host.nodes = [n for n in host.nodes if not n.get("tasks")]                                                           # nothing at work: calm
    host.change()
    waits(pg, "tech", None)
    assert face(pg, "tech") == "shaman-elder"
    host.records["tech"] = record(status="looking", rubric=None)                                                         # its leader looks at its map: focused
    host.change()
    waits(pg, "tech", "focused")
    host.records["tech"] = record(rubric=None)
    host.spent = True                                                                                                    # the AI tool has no window left: every leader asleep, the Orkmaster too
    host.change()
    for slug in ("tech", "game", "art", "market", "orkmaster"):
        waits(pg, slug, "asleep")
    assert face(pg, "market") == "fairy-elder-asleep" and face(pg, "orkmaster") == "peon-crown-asleep"
    shot(pg, "leaders-faces-asleep.png")
    host.spent = False
    host.change()
    waits(pg, "market", None)


def test_a_drop_in_an_open_hearing_says_no_and_a_goal_done_while_the_page_is_open_pleases_but_not_one_found_there(gui):
    pg, host, errors = start(gui, "wide")
    host.needs = [hearing("art")]
    host.change()
    waits(pg, "art", "no")
    assert face(pg, "art") == "dryad-elder-no" and mood(pg, "tech") != "no", "the leader that holds the drop says no, the one that does it does not"
    host.needs = []
    host.change()
    waits(pg, "art", None)
    host.nodes.append(node("icons", "art", "Icons for the four rounds", "done", place="discard"))                          # a goal of Art reaches the discard while the page is open
    host.change()
    waits(pg, "art", "pleased")
    assert face(pg, "art") == "dryad-elder-pleased"
    pg.context.close()
    again = LeadersHost()
    again.nodes.append(node("icons", "art", "Icons for the four rounds", "done", place="discard"))                         # found there on coming back: never news
    pg, host, errors2 = start(gui, "wide", again)
    pg.wait_for_timeout(500)
    assert mood(pg, "art") is None
    pg.context.close()
    assert not errors and not errors2, "\n".join(errors + errors2)


def test_moodof_is_the_rule_asleep_before_no_before_worried_before_focused(wide):
    pg, host = wide
    got = pg.evaluate("""async () => {
        const { moodOf } = await import('/static/js/table/moods.js'), { mapData } = await import('/static/js/shell/store.js'), { town } = await import('/static/js/link.js');
        const g = mapData.value.goals.find((x) => x.slug === 'art'), spent = { limits: [{ provider: 'claude', name: 'Claude', left: 0, rows: [{ window: '5h', left: 0, reset: '' }] }], mana: { main: 'claude' } };
        const fine = { limits: [{ provider: 'claude', name: 'Claude', left: 0.5, rows: [{ window: '5h', left: 0.5, reset: '' }] }], mana: { main: 'claude' } };
        return [moodOf(g, fine), moodOf({ ...g, concerns: { alerts: 1, notes: 0, status: 'ready' } }, fine), moodOf({ ...g, concerns: { alerts: 1, notes: 0, status: 'ready' } }, spent), moodOf(g, {}), moodOf(null, fine), moodOf(null, spent), moodOf(g, town.value)];
    }""")
    assert got == ["", "worried", "asleep", "", "focused", "asleep", ""]                                                  # the Orkmaster reads two goals in this host: focused


# -- the chairs, the empty chair ---------------------------------------------------------------------------------------------------------------------------

def test_a_chair_stands_under_each_head_at_the_wide_width_and_none_under_760(desk):
    pg, host, w = desk
    go(pg, "tech")
    chairs = pg.locator(".table-tabcell .ork-chair:not(.is-empty)")
    if w == "wide":
        assert chairs.count() == 4 and pg.locator(".ork-chair.big").count() == 1 and cell(pg, "tech").locator(".ork-chair.big").count() == 1       # the open leader's is the large one; Release, seated, has no tab and so no chair (decisions §283.29)
        box = cell(pg, "game").locator(".ork-chair").bounding_box()
        assert (box["width"], box["height"]) == (44, 24) and (cell(pg, "tech").locator(".ork-chair.big").bounding_box()["width"], cell(pg, "tech").locator(".ork-chair.big").bounding_box()["height"]) == (52, 28)
        head, back = cell(pg, "game").locator("img.ork-race__head").bounding_box(), cell(pg, "game").locator(".ork-chair").bounding_box()
        assert head["y"] + head["height"] - (back["y"] + back["height"]) <= 1 and head["y"] < back["y"], "the head stands over the back's rail"
        assert cell(pg, "game").locator(".ork-chair").get_attribute("aria-hidden") == "true"
    else:
        assert chairs.count() == 0


def test_the_empty_chair_opens_the_parties_place_lit_by_hover_and_by_focus_and_is_gone_when_every_craft_is_at_the_table(gui):
    errors: list[str] = []
    pg, host, errs = start(gui, "wide", LeadersHost(presets=PRESETS))
    chair = pg.locator(".table-tabs__end .table-chair")
    chair.wait_for(timeout=WAIT_MS)
    assert chair.get_attribute("aria-label") == "New party" and chair.text_content().strip() == "New party" and chair.locator(".ork-chair.is-empty").count() == 1, "a craft (run) is not at the table"
    assert not chair.locator(".ork-chair").evaluate("e => e.classList.contains('is-lit')")
    chair.hover()
    pg.wait_for_function("() => document.querySelector('.table-chair .ork-chair').classList.contains('is-lit')", timeout=WAIT_MS)
    pg.mouse.move(5, 300)
    pg.wait_for_function("() => !document.querySelector('.table-chair .ork-chair').classList.contains('is-lit')", timeout=WAIT_MS)
    pg.keyboard.press("Tab")
    chair.focus()
    pg.keyboard.press("Shift+Tab")
    pg.keyboard.press("Tab")
    pg.wait_for_function("() => document.activeElement.classList.contains('table-chair')", timeout=WAIT_MS)
    assert chair.locator(".ork-chair").evaluate("e => e.classList.contains('is-lit')"), "lit by the focus"
    shot(pg, "leaders-empty-chair-wide.png")
    chair.click()
    pg.locator('[data-chair-deal="question"]').wait_for(timeout=WAIT_MS)                                                  # the wide page deals the crafts to the hand (decisions §272.2); the narrow page opens the parties' place
    assert pg.locator('.table-over[data-kind="parties"]').count() == 0 and ("ideas.party_presets", {}) in host.log
    assert pg.locator(".hand-crafts .hand-craft").count() >= 1 and chair.get_attribute("aria-pressed") == "true"
    pg.get_by_role("button", name="Put it back").click()
    pg.locator('[data-chair-deal="question"]').wait_for(state="detached", timeout=WAIT_MS)
    run = party("run", len(host.parties))                                                                                 # the last craft sits down: nothing is left to offer
    run["leader"] = {**run["leader"], "head": HEAD("goblin", "elder", "data")}
    RACES["run"], CRAFT["run"] = "imp", "data"
    run["leader"] = {**run["leader"], "head": HEAD("imp", "elder", "data")}
    host.parties.append(run)
    host.change()
    pg.locator('.table-tab[data-tab="run"]').wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => !document.querySelector('.table-tabs__end .table-chair')", timeout=WAIT_MS)
    assert pg.locator(".table-tabs__end .table-door").count() == 0, "Stop all is the die's front face, no door of the top row (spec 139 A.4)"
    pg.context.close()
    assert not errors and not errs, "\n".join(errors + errs)


def test_the_empty_chair_is_always_there_while_the_host_gives_no_list_and_small_under_760(gui):
    pg, host, errors = start(gui, "wide")                                                                                 # a host with no `ideas.party_presets`: no reliable signal
    assert pg.locator(".table-tabs__end .table-chair").count() == 1
    pg.context.close()
    pg, host, errors2 = start(gui, "narrow")
    chair = pg.locator(".table-tabs__end .table-chair")
    box = chair.locator(".ork-chair").bounding_box()
    assert (box["width"], box["height"]) == (18, 18) and chair.get_attribute("aria-label") == "New party" and chair.text_content().strip() == "" and chair.bounding_box()["width"] <= 40
    chair.click()
    pg.locator('.table-over[data-kind="parties"]').wait_for(timeout=WAIT_MS)
    pg.context.close()
    assert not errors and not errors2, "\n".join(errors + errors2)


def test_under_reduced_motion_the_empty_chair_is_lit_and_not_pulled_out(gui):
    pg, host, errors = start(gui, "wide", reduced_motion="reduce")
    pg.locator(".table-chair").hover()
    pg.wait_for_function("() => document.querySelector('.table-chair .ork-chair').classList.contains('is-lit')", timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    assert pg.locator(".table-chair .ork-chair").evaluate("e => getComputedStyle(e).transform") == "none"
    assert pg.locator(".ork-chair:not(.is-empty)").first.evaluate("e => getComputedStyle(e).transform") == "none"
    pg.context.close()
    assert not errors, "\n".join(errors)


# -- Stop all: a button under the die (it was the die's front face, spec 139 A.4, decisions §246.1; spec 156 E.3, decisions §261.12) ------------------------------------

def test_stop_all_halts_says_stopped_has_no_button_to_press_again_and_comes_back_when_a_task_runs(desk):
    pg, host, w = desk
    wide = w == "wide"                                   # from 760 px up Stop all is the right column's head's (spec 168 A4, decisions 285.2); under it, it stays under the die
    sel, said = (".rh-stop", None) if wide else (".hand-die__stop", ".hand-die__stopped")
    stop = pg.locator(sel)
    assert stop.get_attribute("aria-label") == "Stop all: stop every run of this project's orks" and stop.get_attribute("aria-disabled") is None and stop.inner_text() == "Stop all"
    assert stop.evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-danger") and stop.evaluate("e => e.tagName") == "BUTTON", "in the danger colour while a task runs"
    shot(pg, f"leaders-die-running-{w}.png")
    stop.click()
    if said:
        pg.wait_for_function("() => document.querySelector('.hand-die__stopped')?.textContent === 'Stopped'", timeout=WAIT_MS)
        assert pg.locator(said).evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-ink-muted"), "Stopped is muted"
    else:
        pg.wait_for_function("() => !document.querySelector('.rh-stop')", timeout=WAIT_MS)             # the head says nothing once stopped
    assert host.halted == 1 and pg.locator(sel).count() == 0, "nothing to press: a host that does not keep *stopped* has no Resume"
    shot(pg, f"leaders-die-stopped-{w}.png")
    pg.wait_for_function("() => !document.querySelector('.table-lane [data-state=running]')", timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    assert host.halted == 1 and pg.locator(sel).count() == 0 and (not said or pg.locator(said).count() == 1), "nothing runs: it stays stopped"
    seat = next(n for n in host.nodes if n["slug"] == "rules")
    seat["tasks"][0]["state"] = "running"                                                                                # a task runs again
    host.change()
    pg.wait_for_function("s => document.querySelector(s)?.textContent === 'Stop all'", arg=sel, timeout=WAIT_MS)
    assert not said or pg.locator(said).count() == 0


def test_stopped_goes_back_when_a_goal_is_started_from_the_page(wide):
    pg, host = wide
    pg.locator(".rh-stop").click()                       # at the wide width Stop all is the right column's head's (spec 168 A4)
    pg.wait_for_function("() => !document.querySelector('.rh-stop')", timeout=WAIT_MS)
    pg.evaluate("() => import('/static/js/board/store.js').then((m) => m.ask('ideas.add', { text: 'A new goal' }))")
    pg.wait_for_function("() => !!document.querySelector('.rh-stop')", timeout=WAIT_MS)


# -- the dark edges -------------------------------------------------------------------------------------------------------------------------------------

def test_the_tabs_row_the_hand_and_the_frame_lie_on_the_room_with_a_rim_and_no_divider_between_the_tabs(desk):
    pg, host, w = desk
    room, rim = paint(pg, "--ork-room", "backgroundColor"), paint(pg, "--ork-table-rim", "borderBottomColor")
    assert pg.locator(".table-tabs").evaluate("e => [getComputedStyle(e).backgroundColor, getComputedStyle(e).borderBottomWidth, getComputedStyle(e).borderBottomColor]") == [room, "3px", rim]
    assert pg.locator(".hand").evaluate("e => [getComputedStyle(e).backgroundColor, getComputedStyle(e).borderTopWidth, getComputedStyle(e).borderTopColor]") == [room, "3px", rim]
    assert pg.locator(".frame").evaluate("e => getComputedStyle(e).backgroundColor") == room and pg.locator(".table").evaluate("e => getComputedStyle(e).backgroundColor") == room
    assert room == "rgb(9, 8, 7)"
    assert pg.locator(".table-tab").evaluate_all("els => els.map((e) => getComputedStyle(e).borderLeftWidth + getComputedStyle(e).borderRightWidth)") == ["0px0px"] * pg.locator(".table-tab").count(), "no divider between the tabs"
    assert pg.locator(".table-tabs__end").evaluate("e => getComputedStyle(e).borderLeftWidth") == "0px"
    assert pg.locator(".table-lane").first.evaluate("e => getComputedStyle(e).borderLeftWidth") == "1px", "the lanes keep theirs"
    assert pg.locator(".table-pane").evaluate("e => [e.classList.contains('ork-table'), getComputedStyle(e).backgroundImage !== 'none' || getComputedStyle(e).backgroundColor !== 'rgba(0, 0, 0, 0)']") == [True, True], "the table lies on its leader's felt (decisions §269.2)"
    assert pg.locator(".table-tabs__end .table-logs, .table-tabs__end .table-door").count() == 0, "the top row's end has neither the bug nor the door"
    shot(pg, f"leaders-room-{w}.png")
