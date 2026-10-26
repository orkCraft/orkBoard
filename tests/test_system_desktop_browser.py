"""Spec 89 part B on the desktop (docs/specs/89-the-tech-lens-system.md §6, "As built (A)"): Chromium at 1 440 × 900 against the project test's stub host with a Tech party the Architect leads and
`ideas.system`, `ideas.system_part` and `ideas.system_rearrange` answering in the shapes part A gives them. The party has two tabs, System and Board, and opens on System when something changed since the device's
last look, else on the tab last pressed; the parts lie as the field's cards in a column for each area with the area's name over it (*n files*, *Uses k · Used by m*, a gone part's place kept, a stack ×n); what
changed is played once in the order the goals landed (new dealt, changed sealed with the goal's element, gone crumble), in steps, the whole at most 3 s, ended by a press, none under reduced motion; *Since your
last look at <time>* and the goals, a press on one dims the others' marks; a card hovered draws its uses (a new one in its goal's element); a card pressed shows its part beside the table, a goal there opens the
goal; *Rearrange*; *Reading the project…* while the host reads. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import json
import re

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import ELDER, HEAD as GRUNT, member  # noqa: E402
from tests.test_map_desktop_browser import node  # noqa: E402
from tests.test_project_desktop_browser import ProjectHost  # noqa: E402
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _calls, _open, _party_card  # noqa: E402

pytestmark = pytest.mark.browser

SHOP = "/work/shop"
HEAD, OLD = "a" * 40, "b" * 40
LOOK = f"orkboard.system.look.{SHOP}"
TAB = f"orkboard.party.tab.{SHOP}.tech"
AREAS = ["shop", "app", "core", "ui", "vendor"]
GOALS = {"register": {"title": "Passkey login", "element": "meadow"}, "landing": {"title": "Landing copy", "element": "lava"}}


def card(path, row, count=2, uses=(), used_by=(), gone=False):
    return {"path": path, "name": "shop" if path == "." else path.rsplit("/", 1)[-1], "count": count, "uses": list(uses), "used_by": list(used_by), "row": row, "gone": gone}


def system(since="", rearranged=False) -> dict:
    """`ideas.system` as part A answers it: five areas; since the old look, Passkey login (`register`) added src/app/screens and changed src/core, Landing copy (`landing`) took src/core/old away, and the person changed src/ui/icons; a vendor
    column of sixteen parts shows fourteen and stacks two."""
    marked = since == OLD
    core = [card("src/core", 0, 5, ["src/core/db"], ["src/app", "src/app/screens", "."]), card("src/core/db", 2, 3, [], ["src/core"])]
    if marked:
        core.insert(1, card("src/core/old", 1, 1, [], [], gone=True))
    if rearranged:                                                       # laid out anew: the gone part's place is taken away
        core = [card("src/core", 0, 5, ["src/core/db"], ["src/app", "src/app/screens", "."]), card("src/core/db", 1, 3, [], ["src/core"])]
    app = [card("src/app", 0, 4, ["src/core", "src/ui"], []), card("src/app/screens", 1, 6, ["src/core"], [])]      # the new part is in dev's head either way: marked only since the old look
    vendor = [card(f"vendor/lib{i:02d}", i, 1) for i in range(16)]
    cols = [{"name": "shop", "parts": [card(".", 0, 3, ["src/core"], [])], "stack": []},
            {"name": "app", "parts": app, "stack": []},
            {"name": "core", "parts": core, "stack": []},
            {"name": "ui", "parts": [card("src/ui", 0, 2, [], ["src/app"]), card("src/ui/icons", 1, 9)], "stack": []},
            {"name": "vendor", "parts": vendor[:14], "stack": vendor[14:]}]
    changed = {"src/app/screens": {"kind": "new", "goal": "register", "task": "t1", "at": "2026-10-26T09:00:00"},
               "src/core": {"kind": "changed", "goal": "register", "task": "t2", "at": "2026-10-26T09:10:00"},
               "src/core/old": {"kind": "gone", "goal": "landing", "task": "w1", "at": "2026-10-26T10:00:00"},
               "src/ui/icons": {"kind": "changed", "goal": "", "task": "", "at": "2026-10-26T11:00:00"}} if marked else {}
    uses = [{"from": "src/app/screens", "to": "src/core", "kind": "new", "goal": "register", "task": "t1", "at": "2026-10-26T09:00:00"}] if marked else []
    return {"commit": HEAD, "short": HEAD[:7], "at": "2026-10-26T11:00:00", "ref": "dev", "since": OLD if marked else HEAD if since == HEAD else "", "columns": cols, "changed": changed,
            "uses_changed": uses, "goals": copy.deepcopy(GOALS) if marked else {}}


def many(since="") -> dict:
    """Twelve goals, each of which changed one part: the reveal is shortened to fit in 3 s."""
    doc = system()
    if since != OLD:
        return doc
    parts = [card(f"src/p{i:02d}", i, 1) for i in range(12)]
    doc["columns"] = [{"name": "src", "parts": parts, "stack": []}]
    doc["changed"] = {p["path"]: {"kind": "changed", "goal": f"g{i:02d}", "task": "t", "at": f"2026-10-26T{8 + i:02d}:00:00"} for i, p in enumerate(parts)}
    doc["goals"] = {f"g{i:02d}": {"title": f"Goal {i}", "element": ["meadow", "ice", "dust", "void", "lava"][i % 5]} for i in range(12)}
    doc["since"] = OLD
    return doc


PART = {"path": "src/core", "name": "core", "count": 5, "files": ["src/core/a.py", "src/core/b.py", "src/core/c.py", "src/core/d.py", "src/core/e.py"], "uses": ["src/core/db"],
        "used_by": ["src/app", "src/app/screens", "."], "gone": False, "kind": "changed", "since": OLD,
        "changes": [{"goal": "register", "task": "t2", "at": "2026-10-26T09:10:00", "made": "Kept the passkey's challenge in the store"},
                    {"goal": "", "task": "", "at": "2026-10-26T09:20:00", "made": ""}],
        "goals": {"register": GOALS["register"]}}


class SystemHost(ProjectHost):
    """The project test's world with a Tech party the Architect leads (its Grunts and its Reviewer) and the three commands of part A. `hold`: `ideas.system` is not answered until `release()`;
    `crowd`: the twelve goals' answer."""

    def __init__(self, crowd=False, old=False):
        super().__init__()
        self.goals["tech"] = self.goal("tech", "Tech", "normal", "ready", order=7)
        self.add(node("cache", "tech", "Cache the sign-in", "ready", 1), "ice")
        self.crowd, self.old, self.hold, self.held, self.rearranged = crowd, old, False, [], False

    def map_doc(self):
        doc = super().map_doc()
        for g in doc["goals"]:
            if g["slug"] == "tech":
                g["leader"] = self.leader("architect")
                g["party"] = [{**g["leader"], "band": "lead", "state": "free", "why": ""}, member("grunt", "Grunts", GRUNT, "build"), member("reviewer", "Reviewer", ELDER, "check")]
        return doc

    def answer(self, a):
        return many(a.get("since", "")) if self.crowd else system(a.get("since", ""), self.rearranged)

    def handle(self, name, a):
        if name == "ideas.system" and not self.old:
            self.log.append((name, a))
            return self.answer(a)
        if name == "ideas.system_rearrange":
            self.log.append((name, a))
            self.rearranged = True
            return self.answer(a)
        if name == "ideas.system_part":
            self.log.append((name, a))
            if a["path"] == "src/core":
                return copy.deepcopy(PART) if a.get("since") == OLD else copy.deepcopy(PART) | {"kind": "", "since": "", "changes": [], "goals": {}}
            c = next((c for col in system(OLD)["columns"] for c in col["parts"] + col["stack"] if c["path"] == a["path"]), None)
            if c is None:
                return {"error": "That part is not in the project"}
            return {"path": c["path"], "name": c["name"], "count": c["count"], "files": [f"{c['path']}/f{i}.py" for i in range(c["count"])], "uses": c["uses"], "used_by": c["used_by"],
                    "gone": c["gone"], "kind": "", "since": "", "changes": [], "goals": {}}
        return super().handle(name, a)

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            if self.hold and m["name"] == "ideas.system":
                self.log.append((m["name"], m["args"]))
                self.held.append(m)
                return
            ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}))
        ws.on_message(on_message)

    def release(self):
        self.hold = False
        for m in self.held:
            self.ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.answer(m["args"])}))
        self.held = []


OBSERVE = """(() => {                      // records when each part's moment of the reveal starts, and when the reveal starts and ends
  const fx = window.__fx = { at: {}, kind: {}, seal: {}, steps: {}, playing: 0, done: 0, unborn: new Set() };
  const look = () => {
    const now = performance.now(), sys = document.querySelector('.sys[data-state=shown]');
    if (sys && sys.dataset.reveal === 'playing' && !fx.playing) fx.playing = now;
    if (sys && sys.dataset.reveal === 'done' && fx.playing && !fx.done) fx.done = now;
    document.querySelectorAll('.sys-part.sys-unborn').forEach((e) => fx.unborn.add(e.dataset.part));
    for (const k of ['dealt', 'sealed', 'crumble']) document.querySelectorAll(`.sys-part.sys-${k}`).forEach((e) => {
      const p = e.dataset.part;
      if (fx.at[p] == null) { fx.at[p] = now; fx.kind[p] = k; }
      const el = k === 'sealed' ? e.querySelector('.sys-seal') : e;
      if (el) fx.steps[k] = getComputedStyle(el).animationTimingFunction + ' ' + getComputedStyle(el).animationDuration;
      const s = e.querySelector('.sys-seal .ork-elem');
      if (s) fx.seal[p] = [...s.classList].filter((c) => !['ork-elem', 'big', 'dim'].includes(c)).join(' ');
    });
  };
  new MutationObserver(look).observe(document, { subtree: true, childList: true, attributes: true });
})();"""


def _seed(pg, look=OLD, tab=""):
    """The device's last look (and its last tab) set before the page reads them, once (a reload keeps what the page wrote since)."""
    at = "2026-10-26T08:30:00"
    tabs = f"localStorage.setItem('{TAB}', '{tab}');" if tab else ""
    pg.add_init_script(f"try {{ if (!sessionStorage.getItem('seeded')) {{ localStorage.setItem('{LOOK}', JSON.stringify({{commit: '{look}', at: '{at}'}})); {tabs} sessionStorage.setItem('seeded', '1'); }} }} catch (e) {{}}")


def _tech(pg):
    """The Tech party shown: its heading pressed in the column."""
    _party_card(pg, "tech").click()
    pg.locator('.arena[data-goal="tech"]').wait_for(timeout=WAIT_MS)


def _shown(pg):
    pg.locator(".sys[data-state=shown]").wait_for(timeout=WAIT_MS)


def _rest(pg):
    _shown(pg)
    pg.locator('.sys[data-reveal="done"]').wait_for(timeout=WAIT_MS)


def _part(pg, path):
    return pg.locator(f'.sys-part[data-part="{path}"]')


@pytest.fixture
def tech(gui):
    pg, host, errors = _open(gui, host=SystemHost(), ready=".arena[data-goal=passkey]")
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _reopen(gui, host, init="", reduced=False):
    pg = gui[1].new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce" if reduced else "no-preference")
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    if init:
        pg.add_init_script(init)
    pg.goto(gui[0].url)
    pg.locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    return pg, errors


# -- the two tabs -------------------------------------------------------------------------------------------------------------------------------------------

def test_a_party_the_architect_leads_has_system_and_board_and_opens_on_the_tab_last_pressed_unless_something_changed(tech):
    pg, host = tech
    assert pg.locator(".sys-tabs").count() == 0                                                                    # a party the Taskmaster leads: no tabs
    _tech(pg)
    tabs = pg.locator(".sys-tabs [role=tab]")
    assert [t.text_content().strip() for t in tabs.all()] == ["System", "Board"]
    assert tabs.nth(0).get_attribute("aria-selected") == "true"                                                   # a new device: System
    _shown(pg)
    assert _calls(pg, host, "ideas.system") == [{"party": "tech"}]                                                 # no look yet: nothing since
    assert pg.locator(".sys-part[data-change]").count() == 0 and pg.locator(".sys-since").count() == 0
    pg.get_by_role("tab", name="Board").click()
    pg.locator(".arena-team").wait_for(timeout=WAIT_MS)
    assert pg.locator(".sys").count() == 0 and pg.locator(".arena-member").count() == 2                             # the field as it was: its Grunts and its Reviewer over their columns
    assert json.loads(pg.evaluate(f"localStorage.getItem('{LOOK}')"))["commit"] == HEAD                            # the System was left: its look is dev's head
    pg.get_by_role("tab", name="Board").press("ArrowLeft")
    assert pg.get_by_role("tab", name="System").get_attribute("aria-selected") == "true"
    pg.get_by_role("tab", name="Board").click()
    pg.reload()
    _tech(pg)
    assert pg.get_by_role("tab", name="Board").get_attribute("aria-selected") == "true"                             # nothing changed since: the tab last pressed
    _calls(pg, host, "ideas.system", 3)
    pg.wait_for_timeout(300)
    assert pg.get_by_role("tab", name="Board").get_attribute("aria-selected") == "true"
    pg.evaluate(f"localStorage.setItem('{LOOK}', JSON.stringify({{commit: '{OLD}', at: '2026-10-26T08:30:00'}}))")    # a look before the goals landed
    pg.reload()
    _tech(pg)
    pg.locator(".sys[data-state=shown]").wait_for(timeout=WAIT_MS)                                                 # something changed: System
    assert pg.get_by_role("tab", name="System").get_attribute("aria-selected") == "true"
    assert {"party": "tech", "since": OLD} in _calls(pg, host, "ideas.system")


def test_reading_the_project_while_the_host_reads_it(tech):
    pg, host = tech
    host.hold = True
    _tech(pg)
    note = pg.locator(".sys[data-state=reading]")
    note.wait_for(timeout=WAIT_MS)
    assert note.text_content().strip() == "Reading the project…"
    _calls(pg, host, "ideas.system")
    host.release()
    _shown(pg)
    assert pg.locator(".sys-part").count() > 0


# -- the table of parts -----------------------------------------------------------------------------------------------------------------------------------

def test_the_parts_lie_as_the_fields_cards_in_a_column_for_each_area_with_its_name_over_it(tech):
    pg, host = tech
    _tech(pg)
    _rest(pg)
    assert [a.get_attribute("data-area") for a in pg.locator(".sys-area").all()] == AREAS
    core = _part(pg, "src/core")
    box = core.bounding_box()
    assert abs(box["width"] - 128) <= 1 and abs(box["height"] - 180) <= 1                                           # the field's card, 128 × 180
    assert core.locator(".sys-part__name").text_content().strip() == "core"
    assert core.locator(".sys-part__files").text_content().strip() == "5 files"
    assert core.locator(".sys-part__uses").text_content().strip() == "Uses 1 · Used by 3"
    assert _part(pg, ".").locator(".sys-part__name").text_content().strip() == "shop"
    head = pg.locator('.sys-area[data-area="core"] .sys-area__nm').bounding_box()
    assert abs((head["x"] + head["width"] / 2) - (box["x"] + box["width"] / 2)) <= 2 and head["y"] + head["height"] <= box["y"]      # the area's name over its column, centred
    db = _part(pg, "src/core/db").bounding_box()
    assert db["y"] - box["y"] > 2 * 180                                                                            # row 2: the gone part's place (row 1) is kept
    stack = pg.locator('.sys-stk[data-n="2"]')
    assert stack.count() == 1 and stack.locator(".arena-stk__n").text_content().strip() == "×2" and stack.locator(".arena-stk__edge").count() == 1
    assert pg.locator('.sys-part[data-part^="vendor/"]').count() == 15                                             # fourteen and the stack's front
    stack.locator("button").click()
    assert pg.locator('.sys-part[data-part^="vendor/"]').count() == 16                                             # opened: every part
    pg.locator(".sys-area__fold").click()
    assert pg.locator('.sys-part[data-part^="vendor/"]').count() == 15
    text = pg.locator(".sys").text_content()
    assert not re.search(r"\bcards?\b", text, re.I), text                                                          # a person never reads the word "card"


# -- what changed since the last look -------------------------------------------------------------------------------------------------------------------

def test_what_changed_plays_once_in_the_order_the_goals_landed_and_stays_marked_until_seen(tech):
    pg, host = tech
    _seed(pg)
    pg.add_init_script(OBSERVE)
    pg.reload()
    pg.locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    _tech(pg)
    _rest(pg)
    fx = pg.evaluate("() => ({at: __fx.at, kind: __fx.kind, seal: __fx.seal, steps: __fx.steps, unborn: [...__fx.unborn], whole: __fx.done - __fx.playing})")
    assert fx["kind"] == {"src/app/screens": "dealt", "src/core": "sealed", "src/core/old": "crumble", "src/ui/icons": "sealed"}
    assert fx["unborn"] == ["src/app/screens"]                                                                     # the map stood as it was: the new part not yet there
    at = fx["at"]
    assert abs(at["src/app/screens"] - at["src/core"]) < 60 < at["src/core/old"] - at["src/core"] and at["src/core/old"] < at["src/ui/icons"]     # Passkey login, then Landing copy, then the person's
    assert fx["seal"]["src/core"] == "meadow"                                                                      # sealed with its goal's element
    for k, v in fx["steps"].items():
        assert v.startswith("steps(") and float(v.split()[-1].rstrip("s")) <= 0.42, (k, v)
    assert 0 < fx["whole"] <= 3000
    assert _part(pg, "src/core").locator(".arena-task__top .ork-elem.meadow").count() == 1 and _part(pg, "src/core").locator(".sys-part__kind").text_content().strip() == "Changed"
    assert _part(pg, "src/app/screens").locator(".sys-part__kind").text_content().strip() == "New"
    assert _part(pg, "src/ui/icons").locator(".ork-elem").count() == 0 and "By you" in _part(pg, "src/ui/icons").get_attribute("aria-label")
    assert _part(pg, "src/core/old").get_attribute("aria-hidden") == "true" and not _part(pg, "src/core/old").is_visible()      # crumbled: its place stays empty
    assert pg.locator(".sys-since").text_content().strip() == "Since your last look at 26 Oct, 08:30" or pg.locator(".sys-since").text_content().strip().startswith("Since your last look at ")
    assert [b.text_content().strip() for b in pg.locator(".sys-goal").all()] == ["Passkey login", "Landing copy", "By you"]
    shot(pg, "system-rest.png")
    host.nodes[-1]["state"] = "done"                                                                               # a goal lands while the tab is open: read again, nothing played
    host.bump(None)
    _calls(pg, host, "ideas.system", 2)
    pg.wait_for_timeout(400)
    assert pg.locator(".sys-dealt, .sys-sealed, .sys-crumble").count() == 0 and pg.locator('.sys[data-reveal="done"]').count() == 1
    pg.get_by_role("tab", name="Board").click()                                                                    # the tab is left: seen
    pg.get_by_role("tab", name="System").click()
    _rest(pg)
    assert pg.locator(".sys-part.is-marked").count() == 0 and pg.locator(".sys-since").text_content().strip() == "Nothing changed since your last look"
    assert {"party": "tech", "since": HEAD} in _calls(pg, host, "ideas.system", 3)


def test_twelve_goals_play_in_at_most_three_seconds_and_a_press_ends_the_reveal(gui):
    host = SystemHost(crowd=True)
    init = f"try {{ localStorage.setItem('{LOOK}', JSON.stringify({{commit: '{OLD}', at: '2026-10-26T08:30:00'}})); }} catch (e) {{}}"
    pg, errors = _reopen(gui, host, init + OBSERVE)
    _tech(pg)
    _rest(pg)
    fx = pg.evaluate("() => ({at: __fx.at, whole: __fx.done - __fx.playing})")
    assert len(fx["at"]) == 12 and 0 < fx["whole"] <= 3000
    order = sorted(fx["at"], key=fx["at"].get)
    assert order == [f"src/p{i:02d}" for i in range(12)]                                                            # in the order the goals landed
    pg.close()
    pg, errors2 = _reopen(gui, host, init)
    _tech(pg)
    pg.locator('.sys[data-reveal="playing"]').wait_for(timeout=WAIT_MS)
    pg.mouse.click(700, 600)                                                                                        # a press ends it
    pg.locator('.sys[data-reveal="done"]').wait_for(timeout=500)
    assert pg.locator(".sys-part.is-marked").count() == 12 and pg.locator(".sys-sealed").count() == 0
    pg.close()
    assert not errors and not errors2, "\n".join(errors + errors2)


def test_nothing_is_played_under_reduced_motion(gui):
    host = SystemHost()
    pg, errors = _reopen(gui, host, f"try {{ localStorage.setItem('{LOOK}', JSON.stringify({{commit: '{OLD}', at: '2026-10-26T08:30:00'}})); }} catch (e) {{}}" + OBSERVE, reduced=True)
    _tech(pg)
    _rest(pg)
    pg.wait_for_timeout(500)
    assert pg.evaluate("() => Object.keys(__fx.at).length + __fx.unborn.size") == 0 and pg.evaluate("() => __fx.playing") == 0
    assert pg.locator(".sys-part.is-marked").count() == 3                                                          # marked, not played: new, changed and the person's
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_goal_pressed_dims_the_others_marks(tech):
    pg, host = tech
    _seed(pg)
    pg.reload()
    pg.locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    _tech(pg)
    _rest(pg)
    passkey = pg.locator('.sys-goal[data-goal="register"]')
    assert passkey.locator(".ork-elem.meadow").count() == 1
    passkey.click()
    assert passkey.get_attribute("aria-pressed") == "true"
    assert "is-dim" in _part(pg, "src/ui/icons").get_attribute("class") and "is-dim" not in _part(pg, "src/core").get_attribute("class")
    assert _part(pg, "src/core").locator(".ork-elem.dim").count() == 0
    pg.locator('.sys-goal[data-goal=""]').click()                                                                 # By you: the goals' marks dim
    assert "is-dim" in _part(pg, "src/core").get_attribute("class") and _part(pg, "src/core").locator(".ork-elem.dim").count() == 1
    pg.locator('.sys-goal[data-goal=""]').click()
    assert pg.locator(".sys-part.is-dim").count() == 0


# -- the uses, a part, Rearrange ------------------------------------------------------------------------------------------------------------------------

def test_hovering_a_part_draws_its_uses_and_a_new_one_in_its_goals_element(tech):
    pg, host = tech
    _seed(pg)
    pg.reload()
    pg.locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    _tech(pg)
    _rest(pg)
    assert pg.locator(".sys .arena-arrow").count() == 0                                                            # never at rest
    _part(pg, "src/app").hover()
    pg.wait_for_selector(".sys .arena-arrow", timeout=WAIT_MS)
    assert sorted(a.get_attribute("data-edge") for a in pg.locator(".sys .arena-arrow").all()) == ["src/app>src/core", "src/app>src/ui"]
    assert "is-after" in _part(pg, "src/core").get_attribute("class") and "is-src" in _part(pg, "src/app").get_attribute("class")
    _part(pg, "src/app/screens").hover()
    arrow = pg.locator('.sys .arena-arrow[data-edge="src/app/screens>src/core"]')
    arrow.wait_for(timeout=WAIT_MS)
    assert arrow.get_attribute("data-elem") == "meadow" and pg.locator(".sys .arena-arrow").count() == 1
    assert "steps(" in arrow.locator("polyline").evaluate("e => getComputedStyle(e).animationTimingFunction")
    pg.mouse.move(5, 890)
    pg.wait_for_selector(".sys .arena-arrow", state="detached", timeout=WAIT_MS)


def test_a_part_pressed_shows_its_files_uses_and_changes_beside_the_table_and_a_goal_there_opens_the_goal(tech):
    pg, host = tech
    _seed(pg)
    pg.reload()
    pg.locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    _tech(pg)
    _rest(pg)
    table = pg.locator(".sys-scroll").bounding_box()
    _part(pg, "src/core").click()
    side = pg.locator('.sys-side[data-path="src/core"]')
    side.locator('[data-sec="files"]').wait_for(timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.system_part") == [{"path": "src/core", "party": "tech", "since": OLD}]
    assert side.get_attribute("aria-label") == "core" and _part(pg, "src/core").get_attribute("aria-pressed") == "true"
    assert side.bounding_box()["x"] >= pg.locator(".sys-scroll").bounding_box()["x"] + pg.locator(".sys-scroll").bounding_box()["width"] - 1 and \
        pg.locator(".sys-scroll").bounding_box()["width"] < table["width"]                                          # beside the table
    assert side.locator('[data-sec="files"] h3').text_content().strip() == "5 files" and side.locator('[data-sec="files"] li').count() == 5
    assert side.locator('[data-sec="uses"] h3').text_content().strip() == "Uses" and [b.text_content().strip() for b in side.locator('[data-sec="uses"] button').all()] == ["db"]
    assert side.locator('[data-sec="used_by"] h3').text_content().strip() == "Used by" and [b.text_content().strip() for b in side.locator('[data-sec="used_by"] button').all()] == ["app", "screens", "shop"]      # by their names: the top's is the project's
    changes = side.locator(".sys-change")
    assert changes.count() == 2 and changes.nth(0).locator(".sys-change__goal").text_content().strip() == "Passkey login" and changes.nth(0).locator(".ork-elem.meadow").count() == 1
    assert changes.nth(0).locator(".sys-change__made").text_content().strip() == "What it made Kept the passkey's challenge in the store"
    assert changes.nth(1).text_content().strip() == "By you"
    assert side.locator('[data-sec="changes"] h3').text_content().strip().startswith("Since your last look at ")
    shot(pg, "system-part.png")
    side.locator('[data-sec="uses"] button').click()                                                              # a part named there shows that part
    pg.locator('.sys-side[data-path="src/core/db"]').wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    pg.locator(".sys-side").wait_for(state="detached", timeout=WAIT_MS)
    _part(pg, "src/core").click()
    pg.locator('.sys-side[data-path="src/core"] .sys-change__goal[data-goal="register"]').click()                     # a goal there opens the goal
    assert any(a.get("slug") == "register" for a in _calls(pg, host, "ideas.page"))


def test_rearrange_lays_the_parts_out_again(tech):
    pg, host = tech
    _seed(pg)
    pg.reload()
    pg.locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    _tech(pg)
    _rest(pg)
    button = pg.get_by_role("button", name="Rearrange")
    bar = pg.locator(".sys-bar").bounding_box()
    assert button.bounding_box()["x"] + button.bounding_box()["width"] >= bar["x"] + bar["width"] - 24                # in the tab's corner
    db = _part(pg, "src/core/db").bounding_box()["y"]
    button.click()
    assert _calls(pg, host, "ideas.system_rearrange") == [{"party": "tech", "since": OLD}]
    pg.wait_for_function("y => document.querySelector('.sys-part[data-part=\"src/core/db\"]').getBoundingClientRect().y < y - 100", arg=db, timeout=WAIT_MS)      # the gone part's place is taken away


def test_a_host_without_the_system_keeps_the_board_with_no_tabs(gui):
    pg, host, errors = _open(gui, host=SystemHost(old=True), ready=".arena[data-goal=passkey]")
    _tech(pg)
    pg.locator(".arena-team").wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => !document.querySelector('.sys-tabs')", timeout=WAIT_MS)
    assert pg.locator(".sys").count() == 0 and pg.locator(".arena-member").count() == 2
    pg.close()
    assert not errors, "\n".join(errors)
