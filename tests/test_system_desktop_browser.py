"""Spec 89 part B and spec 90 E2 on the desktop (docs/specs/89-the-tech-lens-system.md §6, docs/specs/90-what-the-first-look-said.md §6.7): Chromium at 1 440 × 900 against the project test's stub host with a
Tech party the Architect leads and `ideas.system`, `ideas.system_part` and `ideas.system_rearrange` answering in the shapes spec 89 A and spec 90 E1 give them. The party has three tabs, System, Feature modules
and Board, and opens on System when something changed since the device's last look (on Feature modules when the answer has no overview), else on the tab last pressed.

System (spec 90 E2, `ArchHost`: the owner's monorepo, a Vite and React client, an Express and Socket.IO server, a config both use): the containers as columns with their names, stacks and ways in, their layers
named top to bottom, the shared part between the columns it serves, the link as the field's arrow named on it, a press on the name opening its routes and events in the right column, spec 89's reveal on the
parts inside the containers; *Reading the project…* when the answer has no overview (`SystemHost`, a host from before spec 90), Feature modules still shown.

Feature modules (spec 89's System, `SystemHost`): the parts lie as the field's cards in a column for each area with the area's name over it (*n files*, *Uses k · Used by m*, a gone part's place kept, a stack ×n); what
changed is played once in the order the goals landed (new dealt, changed sealed with the goal's element, gone crumble), in steps, the whole at most 3 s, ended by a press, none under reduced motion; *Since your
last look at <time>* and the goals, a press on one dims the others' marks; a card hovered draws its uses (a new one in its goal's element); a card pressed shows its part in the window's right column (spec 90 §2), a goal there
opens the goal; *Rearrange*; *Reading the project…* while the host reads. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
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


def _tech(pg, view=""):
    """The Tech party shown: its heading pressed in the column; `view` (*System*, *Feature modules*): that tab pressed unless it is the one shown."""
    _party_card(pg, "tech").click()
    pg.locator('.arena[data-goal="tech"]').wait_for(timeout=WAIT_MS)
    if view:
        tab = pg.get_by_role("tab", name=view, exact=True)
        if tab.get_attribute("aria-selected") != "true":
            tab.click()


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

def test_a_party_the_architect_leads_has_system_feature_modules_and_board_and_opens_on_the_tab_last_pressed_unless_something_changed(tech):
    pg, host = tech
    assert pg.locator(".sys-tabs").count() == 0                                                                    # a party the Taskmaster leads: no tabs
    _tech(pg)
    tabs = pg.locator(".sys-tabs [role=tab]")
    assert [t.text_content().strip() for t in tabs.all()] == ["System", "Feature modules", "Board"]
    assert tabs.nth(0).get_attribute("aria-selected") == "true"                                                   # a new device: System
    note = pg.locator('.sys[data-state=reading][data-view="system"]')
    note.wait_for(timeout=WAIT_MS)                                                                                 # this host's answer has no overview (a snapshot from before spec 90)
    assert _calls(pg, host, "ideas.system") == [{"party": "tech"}]                                                 # no look yet: nothing since
    pg.wait_for_timeout(200)
    assert note.text_content().strip() == "Reading the project…"
    pg.get_by_role("tab", name="Feature modules").click()                                                          # Feature modules still works
    _shown(pg)
    assert pg.locator('.sys[data-view="modules"] .sys-area').count() == len(AREAS)
    assert pg.locator(".sys-part[data-change]").count() == 0 and pg.locator(".sys-since").count() == 0
    pg.get_by_role("tab", name="Board").click()
    pg.locator(".arena-team").wait_for(timeout=WAIT_MS)
    assert pg.locator(".sys").count() == 0 and pg.locator(".arena-member").count() == 2                             # the field as it was: its Grunts and its Reviewer over their columns
    assert json.loads(pg.evaluate(f"localStorage.getItem('{LOOK}')"))["commit"] == HEAD                            # the lens was left: its look is dev's head
    pg.get_by_role("tab", name="Board").press("ArrowLeft")
    assert pg.get_by_role("tab", name="Feature modules").get_attribute("aria-selected") == "true"
    pg.get_by_role("tab", name="Feature modules").press("ArrowLeft")
    assert pg.get_by_role("tab", name="System", exact=True).get_attribute("aria-selected") == "true"
    pg.get_by_role("tab", name="System", exact=True).press("End")
    assert pg.get_by_role("tab", name="Board").get_attribute("aria-selected") == "true"
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
    pg.locator(".sys[data-state=shown]").wait_for(timeout=WAIT_MS)                                                 # something changed, and no overview: Feature modules, where it is seen
    assert pg.get_by_role("tab", name="Feature modules").get_attribute("aria-selected") == "true"
    assert {"party": "tech", "since": OLD} in _calls(pg, host, "ideas.system")


def test_reading_the_project_while_the_host_reads_it(tech):
    pg, host = tech
    host.hold = True
    _tech(pg, "Feature modules")
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
    _tech(pg, "Feature modules")
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
    pg.get_by_role("tab", name="Board").click()                                                                    # the lens is left: seen
    pg.get_by_role("tab", name="Feature modules").click()
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


def test_a_part_pressed_shows_its_files_uses_and_changes_in_the_right_column_and_a_goal_there_opens_the_goal(tech):
    pg, host = tech
    _seed(pg)
    pg.reload()
    pg.locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    _tech(pg)
    _rest(pg)
    table = pg.locator(".sys-scroll").bounding_box()
    _part(pg, "src/core").click()
    side = pg.locator('.shell-drawer .sys-side[data-path="src/core"]')
    side.locator('[data-sec="files"]').wait_for(timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.system_part") == [{"path": "src/core", "party": "tech", "since": OLD}]
    assert side.get_attribute("aria-label") == "core" and _part(pg, "src/core").get_attribute("aria-pressed") == "true"
    assert side.bounding_box()["x"] >= pg.locator(".sys-scroll").bounding_box()["x"] + pg.locator(".sys-scroll").bounding_box()["width"] - 1 and \
        pg.locator(".sys-scroll").bounding_box()["width"] < table["width"]                                          # in the right column, beside the table (spec 90 §2)
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


# -- System as the architecture (spec 90 E2) ------------------------------------------------------------------------------------------------------------------

ARCH_GOALS = {"rooms": {"title": "Room codes", "element": "meadow"}, "balance": {"title": "Faster rounds", "element": "lava"}}
USES = {"client": ([], []), "client/src": (["client/src/views"], []), "client/src/components": ([], ["client/src/views"]),
        "client/src/views": (["client/src/components", "client/src/net", "config"], ["client/src"]), "client/src/net": ([], ["client/src/views"]),
        "server/src": (["server/src/routes", "server/src/rooms", "config"], []), "server/src/routes": (["server/src/rooms", "server/src/db"], ["server/src"]),
        "server/src/rooms": (["server/src/db"], ["server/src", "server/src/routes"]), "server/src/db": ([], ["server/src/routes", "server/src/rooms"]),
        "config": ([], ["client/src/views", "server/src"])}
FILES = {"client": 1, "client/src": 2, "client/src/components": 7, "client/src/views": 3, "client/src/net": 2, "server/src": 2, "server/src/routes": 1, "server/src/rooms": 3,
         "server/src/db": 1, "config": 1}


def arch(since="", crowd=False) -> dict:
    """`ideas.system` for the owner's monorepo (spec 90 E1's shape): Root (the workspace, its own code the config), client (React, socket.io-client, Vite) and server (Express, Socket.IO); the client calls
    three routes and sends two events, the server sends one back; config used by both. Since the old look, Room codes (`rooms`) added server/src/rooms and changed client/src/net, Faster rounds (`balance`)
    changed the shared config and took server/src/old away, and the person changed client/src/views."""
    marked = since == OLD
    parts = {p: {"path": p, "name": p.rsplit("/", 1)[-1], "count": FILES[p], "uses": u, "used_by": b, "gone": False} for p, (u, b) in USES.items()}
    if marked:
        parts["server/src/old"] = {"path": "server/src/old", "name": "old", "count": 1, "uses": [], "used_by": [], "gone": True}
    containers = [
        {"path": ".", "name": "Root", "manifests": ["package.json"], "stack": [{"name": "concurrently", "role": "build"}], "unknown": 0,
         "ways_in": [{"kind": "script", "name": "dev", "path": "package.json"}], "layers": [{"role": "settings", "parts": ["config"]}], "parts": ["config"], "gone": []},
        {"path": "client", "name": "client", "manifests": ["package.json"],
         "stack": [{"name": "React", "role": "UI"}, {"name": "socket.io-client", "role": "realtime"}, {"name": "Vite", "role": "build"}], "unknown": 1,
         "ways_in": [{"kind": "page", "name": "", "path": "client/index.html"}, {"kind": "script", "name": "dev", "path": "client/package.json"},
                     {"kind": "script", "name": "build", "path": "client/package.json"}],
         "layers": [{"role": "", "parts": ["client", "client/src"]}, {"role": "face", "parts": ["client/src/components", "client/src/views"]}, {"role": "", "parts": ["client/src/net"]}],
         "parts": ["client", "client/src", "client/src/components", "client/src/net", "client/src/views"], "gone": []},
        {"path": "server", "name": "server", "manifests": ["package.json"], "stack": [{"name": "Express", "role": "server"}, {"name": "Socket.IO", "role": "realtime"}], "unknown": 1,
         "ways_in": [{"kind": "main", "name": "", "path": "server/src/index.ts"}, {"kind": "script", "name": "dev", "path": "server/package.json"},
                     {"kind": "script", "name": "start", "path": "server/package.json"}, {"kind": "listen", "name": "", "path": "server/src/index.ts"}],
         "layers": [{"role": "", "parts": ["server/src"]}, {"role": "doors", "parts": ["server/src/routes"]}, {"role": "", "parts": ["server/src/rooms"]}, {"role": "data", "parts": ["server/src/db"]}],
         "parts": ["server/src", "server/src/db", "server/src/rooms", "server/src/routes"], "gone": ["server/src/old"] if marked else []}]
    link = {"from": "client", "to": "server",
            "http": [{"method": "GET", "path": "/api/health", "called_in": "client/src/net/api.ts", "answered_in": "server/src/index.ts"},
                     {"method": "POST", "path": "/api/rooms", "called_in": "client/src/net/api.ts", "answered_in": "server/src/routes/rooms.ts"},
                     {"method": "GET", "path": "/api/rooms/:code", "called_in": "client/src/net/api.ts", "answered_in": "server/src/routes/rooms.ts"}],
            "socket": [{"event": "answer", "way": "out", "emitted_in": "client/src/views/JudgeView.tsx", "handled_in": "server/src/index.ts"},
                       {"event": "join", "way": "out", "emitted_in": "client/src/net/socket.ts", "handled_in": "server/src/index.ts"},
                       {"event": "state", "way": "back", "emitted_in": "server/src/index.ts", "handled_in": "client/src/views/TvView.tsx"}]}
    shared = [{"path": "config", "container": ".", "containers": ["client", "server"], "used_by": ["client/src/views", "server/src"]}]
    if crowd:                                                            # sixteen screens more: a crowded table
        more = [f"client/src/screens/s{i:02d}" for i in range(16)]
        parts.update({x: {"path": x, "name": x.rsplit("/", 1)[-1], "count": 1, "uses": [], "used_by": [], "gone": False} for x in more})
        containers[1]["layers"][1]["parts"] += more
        containers[1]["parts"] += more
    cols = [{"name": "client", "parts": [card(p, i, parts[p]["count"], parts[p]["uses"], parts[p]["used_by"]) for i, p in enumerate(containers[1]["parts"])], "stack": []},
            {"name": "server", "parts": [card(p, i, parts[p]["count"], parts[p]["uses"], parts[p]["used_by"]) for i, p in enumerate(containers[2]["parts"])], "stack": []},
            {"name": "config", "parts": [card("config", 0, 1, *USES["config"])], "stack": []}]
    changed = {"server/src/rooms": {"kind": "new", "goal": "rooms", "task": "t1", "at": "2026-10-26T09:00:00"},
               "client/src/net": {"kind": "changed", "goal": "rooms", "task": "t2", "at": "2026-10-26T09:10:00"},
               "config": {"kind": "changed", "goal": "balance", "task": "w1", "at": "2026-10-26T10:00:00"},
               "server/src/old": {"kind": "gone", "goal": "balance", "task": "w1", "at": "2026-10-26T10:05:00"},
               "client/src/views": {"kind": "changed", "goal": "", "task": "", "at": "2026-10-26T11:00:00"}} if marked else {}
    return {"commit": HEAD, "short": HEAD[:7], "at": "2026-10-26T11:00:00", "ref": "dev", "since": OLD if marked else HEAD if since == HEAD else "", "columns": cols, "changed": changed,
            "uses_changed": [], "goals": copy.deepcopy(ARCH_GOALS) if marked else {},
            "overview": {"containers": containers, "links": [link], "shared": shared, "parts": parts}}


class ArchHost(SystemHost):
    """The Tech party's world with `ideas.system` answering the owner's monorepo (`arch`); `crowd`: sixteen parts more."""

    def __init__(self, crowd=False):
        super().__init__()
        self.many = crowd

    def answer(self, a):
        return arch(a.get("since", ""), self.many)

    def handle(self, name, a):
        if name == "ideas.system_part":
            self.log.append((name, a))
            c = arch(OLD)["overview"]["parts"].get(a["path"])
            if c is None:
                return {"error": "That part is not in the project"}
            return {**c, "files": [f"{c['path']}/f{i}.ts" for i in range(c["count"])], "kind": "", "since": "", "changes": [], "goals": {}}
        return super().handle(name, a)


@pytest.fixture
def mono(gui):
    pg, host, errors = _open(gui, host=ArchHost(), ready=".arena[data-goal=passkey]")
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _arch(pg):
    pg.locator('.sys[data-state=shown][data-view="system"] .arch').wait_for(timeout=WAIT_MS)
    pg.locator('.sys[data-reveal="done"]').wait_for(timeout=WAIT_MS)


def _col(pg, path):
    return pg.locator(f'.arch-col[data-container="{path}"]')


def test_system_lays_the_containers_as_columns_with_their_names_stacks_and_ways_in(mono):
    pg, host = mono
    _tech(pg)
    _arch(pg)
    assert [c.get_attribute("data-container") or "shared" for c in pg.locator(".arch-col").all()] == ["client", "shared", "server", "."]      # Root's own code is all shared: after the others
    assert [c.locator(".arch-name").text_content().strip() for c in pg.locator(".arch-col").all()] == ["client", "Shared", "server", "Root"]
    assert [" ".join(w.text_content().split()) for w in _col(pg, ".").locator(".arch-way").all()] == ["Script dev"]
    client = _col(pg, "client")
    libs = [(li.locator(".arch-lib__nm").text_content().strip(), li.get_attribute("data-role")) for li in client.locator(".arch-lib:not(.is-more)").all()]
    assert libs == [("React", "UI"), ("socket.io-client", "realtime"), ("Vite", "build")]
    assert [li.locator(".arch-lib__role").text_content().strip() for li in client.locator(".arch-lib:not(.is-more)").all()] == ["UI", "realtime", "build"]
    assert client.locator(".arch-lib.is-more").text_content().strip() == "+1 more"                                 # the unknown ones counted, not named
    assert [li.locator(".arch-lib__nm").text_content().strip() for li in _col(pg, "server").locator(".arch-lib:not(.is-more)").all()] == ["Express", "Socket.IO"]
    name, stack = client.locator(".arch-name").bounding_box(), client.locator(".arch-stack").bounding_box()
    assert name["y"] + name["height"] <= stack["y"]                                                                  # the stack under the name, over the layers
    for lib in client.locator(".arch-lib").all():                                                                      # small: a role each, never a full card
        assert lib.bounding_box()["height"] <= 40 and lib.bounding_box()["width"] < 128
    ways = client.locator(".arch-ways")
    assert ways.locator(".arch-ways__h").text_content().strip() == "Ways in"
    assert [w.get_attribute("data-kind") for w in ways.locator(".arch-way").all()] == ["page", "script", "script"]
    assert [" ".join(w.text_content().split()) for w in ways.locator(".arch-way").all()] == ["Page index.html", "Script dev", "Script build"]
    assert ways.locator(".arch-way .ork-icon").count() == 3                                                           # marked
    assert [" ".join(w.text_content().split()) for w in _col(pg, "server").locator(".arch-way").all()] == ["Main index.ts", "Script dev", "Script start", "Listens index.ts"]
    assert ways.bounding_box()["y"] + ways.bounding_box()["height"] <= client.locator(".arch-layer").first.bounding_box()["y"]
    text = pg.locator(".sys").text_content()
    assert not re.search(r"\bcards?\b", text, re.I), text                                                             # a person never reads the word "card"


def test_the_layers_lie_top_to_bottom_as_rows_of_parts_named_at_the_rows_start(mono):
    pg, host = mono
    _tech(pg)
    _arch(pg)
    client, server = _col(pg, "client"), _col(pg, "server")
    rows = lambda col: [[p.get_attribute("data-part") for p in r.locator(".sys-part").all()] for r in col.locator(".arch-layer").all()]   # noqa: E731
    assert rows(client) == [["client", "client/src"], ["client/src/components", "client/src/views"], ["client/src/net"]]
    assert rows(server) == [["server/src"], ["server/src/routes"], ["server/src/rooms"], ["server/src/db"]]
    assert [r.locator(".arch-layer__nm").text_content().strip() for r in client.locator(".arch-layer").all()] == ["", "Its face", ""]
    assert [r.locator(".arch-layer__nm").text_content().strip() for r in server.locator(".arch-layer").all()] == ["", "Its doors", "", "Its data"]
    ys = [r.bounding_box()["y"] for r in server.locator(".arch-layer").all()]
    assert ys == sorted(ys) and len(set(ys)) == 4                                                                     # top to bottom
    face = client.locator('.arch-layer[data-role="face"]')
    nm, first = face.locator(".arch-layer__nm").bounding_box(), face.locator(".sys-part").first.bounding_box()
    assert nm["x"] + nm["width"] <= first["x"] and abs(nm["y"] - first["y"]) < 12                                    # named at the row's start
    a, b = [p.bounding_box() for p in face.locator(".sys-part").all()]
    assert abs(a["y"] - b["y"]) < 1 and b["x"] > a["x"] + a["width"]                                                  # a row
    assert abs(a["width"] - 128) <= 1 and abs(a["height"] - 180) <= 1                                                 # spec 87's card: the table is not crowded
    assert pg.locator(".arch").get_attribute("data-size") == "full"
    views = _part(pg, "client/src/views")
    assert views.locator(".sys-part__name").text_content().strip() == "views" and views.locator(".sys-part__files").text_content().strip() == "3 files"
    assert _col(pg, ".").locator(".arch-layer").count() == 0                                                          # Root's own part is the shared config, drawn between


def test_the_shared_part_lies_between_the_columns_it_serves(mono):
    pg, host = mono
    _tech(pg)
    _arch(pg)
    shared = pg.locator(".arch-shared")
    assert shared.count() == 1 and shared.get_attribute("data-shared") == "client,server"
    assert shared.locator(".arch-name").text_content().strip() == "Shared" and shared.locator(".arch-serves").text_content().strip() == "client · server"
    assert [p.get_attribute("data-part") for p in shared.locator(".sys-part").all()] == ["config"] and pg.locator('.sys-part[data-part="config"]').count() == 1
    c, s, sh = _col(pg, "client").bounding_box(), _col(pg, "server").bounding_box(), shared.bounding_box()
    assert c["x"] + c["width"] <= sh["x"] and sh["x"] + sh["width"] <= s["x"]


def test_the_link_is_the_fields_arrow_between_the_containers_named_on_it_in_steps(mono):
    pg, host = mono
    _tech(pg)
    _arch(pg)
    arrow = pg.locator('.sys .arena-arrow[data-edge="client>server"]')
    arrow.wait_for(timeout=WAIT_MS)
    assert pg.locator(".sys .arena-arrow").count() == 1                                                               # few arrows: one a link
    line = arrow.locator("polyline")
    assert "steps(" in line.evaluate("e => getComputedStyle(e).animationTimingFunction")                            # drawn in steps
    assert line.evaluate("e => getComputedStyle(e).strokeDasharray") not in ("none", "")                              # the field's dashed ink line
    pts = [tuple(float(v) for v in p.split(",")) for p in line.get_attribute("points").split()]
    assert len(pts) == 4 and pts[0][0] == pts[1][0] and pts[1][1] == pts[2][1] and pts[2][0] == pts[3][0]          # square steps: up, across, down
    host_box = pg.locator(".arch").bounding_box()
    c, s = _col(pg, "client").bounding_box(), _col(pg, "server").bounding_box()
    assert c["x"] <= host_box["x"] + pts[0][0] <= c["x"] + c["width"] and s["x"] <= host_box["x"] + pts[3][0] <= s["x"] + s["width"]
    assert host_box["y"] + pts[1][1] < min(c["y"], s["y"])                                                            # its lane over the columns
    name = pg.locator('.arch-link[data-link="client>server"]')
    assert name.text_content().strip() == "HTTP: 3 routes · socket: 3 events"
    nb = name.bounding_box()
    assert c["x"] + c["width"] < nb["x"] + nb["width"] / 2 < s["x"] and abs((nb["y"] + nb["height"] / 2) - (host_box["y"] + pts[1][1])) <= 2      # on the arrow, between the two
    assert name.get_attribute("aria-pressed") == "false"


def test_a_press_on_the_links_name_opens_its_routes_and_events_in_the_right_column(mono):
    pg, host = mono
    _tech(pg)
    _arch(pg)
    pg.wait_for_timeout(300)                                                                                            # the arrow drawn
    shot(pg, "system-architecture.png")
    table = pg.locator(".sys-scroll").bounding_box()
    name = pg.locator('.arch-link[data-link="client>server"]')
    name.click()
    col = pg.locator(".shell-drawer")
    side = col.locator('.arch-side[data-link="client>server"]')
    side.locator('[data-sec="http"]').wait_for(timeout=WAIT_MS)
    assert col.locator(".shell-ptab.is-on .shell-ptab__main").text_content().split()[:4] == ["Link", "client", "→", "server"]
    assert side.get_attribute("aria-label") == "client → server" and name.get_attribute("aria-pressed") == "true"
    assert side.locator('[data-sec="http"] h3').text_content().strip() == "HTTP: 3 routes"
    assert [" ".join(r.locator(".arch-route__head").text_content().split()) for r in side.locator(".arch-route").all()] == ["GET /api/health", "POST /api/rooms", "GET /api/rooms/:code"]
    assert side.locator(".arch-route").nth(2).locator(".arch-route__where").text_content().strip() == "Called in api.ts · answered in rooms.ts"
    assert side.locator('[data-sec="socket"] h3').text_content().strip() == "socket: 3 events"
    events = [(e.locator(".arch-route__path").text_content().strip(), e.locator(".arch-event__way").text_content().strip()) for e in side.locator(".arch-event").all()]
    assert events == [("answer", "client → server"), ("join", "client → server"), ("state", "server → client")]      # join and answer out, the state back
    assert pg.locator(".sys-scroll").bounding_box()["width"] < table["width"] - 400                                     # beside the table, pushing it
    assert col.bounding_box()["x"] >= pg.locator(".sys-scroll").bounding_box()["x"] + pg.locator(".sys-scroll").bounding_box()["width"] - 1
    pg.wait_for_timeout(250)
    shot(pg, "system-link.png")
    pg.locator('.arch-link[data-link="client>server"]').click()                                                         # pressed again: closed
    pg.locator(".shell-drawer").wait_for(state="detached", timeout=WAIT_MS)
    _part(pg, "server/src/routes").click()                                                                              # a part inside a container opens as before
    pg.locator('.shell-drawer .sys-side[data-path="server/src/routes"]').wait_for(timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.system_part")[-1] == {"path": "server/src/routes", "party": "tech"}


def test_what_changed_plays_on_the_parts_inside_the_containers_and_the_shared_one(gui):
    host = ArchHost()
    init = f"try {{ localStorage.setItem('{LOOK}', JSON.stringify({{commit: '{OLD}', at: '2026-10-26T08:30:00'}})); }} catch (e) {{}}"
    pg, errors = _reopen(gui, host, init + OBSERVE)
    _tech(pg)
    _arch(pg)                                                                                                           # something changed: System
    assert pg.get_by_role("tab", name="System", exact=True).get_attribute("aria-selected") == "true"
    fx = pg.evaluate("() => ({at: __fx.at, kind: __fx.kind, seal: __fx.seal, unborn: [...__fx.unborn], whole: __fx.done - __fx.playing})")
    assert fx["kind"] == {"server/src/rooms": "dealt", "client/src/net": "sealed", "config": "sealed", "server/src/old": "crumble", "client/src/views": "sealed"}
    assert fx["unborn"] == ["server/src/rooms"] and 0 < fx["whole"] <= 3000
    at = fx["at"]
    assert at["server/src/rooms"] < at["config"] < at["client/src/views"] and abs(at["config"] - at["server/src/old"]) < 60     # Room codes, then Faster rounds, then the person's
    assert fx["seal"]["client/src/net"] == "meadow" and fx["seal"]["config"] == "lava"                                # sealed with their goals' elements, the shared one too
    assert _part(pg, "config").locator(".sys-part__kind").text_content().strip() == "Changed" and _part(pg, "config").locator(".ork-elem.lava").count() == 1
    assert _part(pg, "server/src/rooms").locator(".sys-part__kind").text_content().strip() == "New"
    old = _part(pg, "server/src/old")
    assert old.get_attribute("aria-hidden") == "true" and not old.is_visible()                                          # crumbled in its container's last row
    assert pg.locator(".sys-since").text_content().strip().startswith("Since your last look at ")
    assert [b.text_content().strip() for b in pg.locator(".sys-goal").all()] == ["Room codes", "Faster rounds", "By you"]
    pg.locator('.sys-goal[data-goal="rooms"]').click()                                                                 # a goal pressed dims the others' marks
    assert "is-dim" in _part(pg, "config").get_attribute("class") and "is-dim" not in _part(pg, "client/src/net").get_attribute("class")
    pg.get_by_role("tab", name="Feature modules").click()                                                              # the other view of the lens: still marked, not played again
    _shown(pg)
    assert pg.locator('.sys[data-view="modules"][data-reveal="done"]').count() == 1 and pg.locator(".sys-part.is-marked").count() == 4
    pg.get_by_role("tab", name="Board").click()                                                                        # the lens is left: seen
    pg.get_by_role("tab", name="System", exact=True).click()
    _arch(pg)
    assert pg.locator(".sys-part.is-marked").count() == 0 and pg.locator('.sys-part[data-part="server/src/old"]').count() == 0
    pg.close()
    assert not errors, "\n".join(errors)


def test_feature_modules_is_the_table_of_folders_as_before(mono):
    pg, host = mono
    _tech(pg, "Feature modules")
    pg.locator('.sys[data-state=shown][data-view="modules"]').wait_for(timeout=WAIT_MS)
    assert [a.get_attribute("data-area") for a in pg.locator(".sys-area").all()] == ["client", "server", "config"]
    assert pg.locator(".arch").count() == 0 and pg.get_by_role("button", name="Rearrange").count() == 1
    assert pg.locator(".sys-table .sys-part").count() == 10
    pg.get_by_role("tab", name="System", exact=True).click()
    _arch(pg)
    assert pg.get_by_role("button", name="Rearrange").count() == 0                                                     # the architecture is laid by its layers


def test_an_answer_with_no_overview_reads_the_project_and_feature_modules_still_works(tech):
    pg, host = tech
    _tech(pg, "System")
    note = pg.locator('.sys[data-state=reading][data-view="system"]')
    note.wait_for(timeout=WAIT_MS)
    _calls(pg, host, "ideas.system")
    pg.wait_for_timeout(300)
    assert note.text_content().strip() == "Reading the project…" and pg.locator(".arch").count() == 0
    pg.get_by_role("tab", name="Feature modules").click()
    _shown(pg)
    assert [a.get_attribute("data-area") for a in pg.locator(".sys-area").all()] == AREAS


def test_a_crowded_table_lays_the_smaller_cards_and_a_row_wraps_after_three(gui):
    pg, host, errors = _open(gui, host=ArchHost(crowd=True), ready=".arena[data-goal=passkey]")
    _tech(pg)
    _arch(pg)
    assert pg.locator(".arch").get_attribute("data-size") == "small"
    box = _part(pg, "client/src/views").bounding_box()
    assert abs(box["width"] - 96) <= 1 and abs(box["height"] - 134.4) <= 1.5                                          # 96 x 134, 5:7
    face = pg.locator('.arch-col[data-container="client"] .arch-layer[data-role="face"] .sys-part')
    ys = sorted({round(p.bounding_box()["y"]) for p in face.all()})
    assert face.count() == 18 and len(ys) == 6                                                                         # three a line
    pg.close()
    assert not errors, "\n".join(errors)
