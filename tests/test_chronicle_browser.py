"""The past through the open tab's eyes (docs/specs/168-the-window-played-as-a-card-games-table.md G3, decisions §283.28: it left the discard for the history book, table/history.js; before it docs/specs/156-one-pick-and-the-release-column.md D.5, decisions §261.9;
docs/specs/134-release-keeps-the-chronicle.md B, decisions §238.3–§238.4), in a real browser at the wide width against a stub host (the road's `RoadHost` with the `ideas.chronicle*` and `ideas.history` commands answered as the host answers them): a goal of the past
is picked and the table shows it as it was; a decision's entry opens over the pane, its *Changes* and *changed by* walked, a decision gone said in words; a decision newer than a party's last look is a muted dot on its tab, gone once the history is opened through that
tab. Screenshots to ORKCRAFT_SHOTS_DIR when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import RoadHost, call, open_hand, sig  # noqa: E402
from tests.test_table_desktop_browser import shot  # noqa: E402

pytestmark = pytest.mark.browser


def goal(idea, title, day, decision=0, element="meadow"):
    return {"idea": idea, "title": title, "party": "design", "element": element, "hue": "", "at": f"{day}T10:00:00", "day": day, "commit": "a" * 40, "decision": decision}


UNRELEASED = {"goals": [goal("words-then", "Words on the sign-in screen", "2026-11-04", 0, "ice")], "decisions": []}
NEW = {"id": "v:0.4", "kind": "tag", "name": "v0.4", "day": "2026-11-02", "open": True,
       "goals": [goal("seat", "Reconnect keeps your seat", "2026-10-31", 238, "dust")],
       "decisions": [{"number": 240, "title": "A hypothesis's verdict", "day": "2026-11-01", "changes": [], "changed_by": [], "goal": ""}]}
OLD = {"id": "v:0.3", "kind": "tag", "name": "v0.3", "day": "2026-10-28", "open": False}
OLD_FULL = {**OLD, "open": True, "goals": [goal("lobby", "A lobby with a chat", "2026-10-27", 0, "dust")], "decisions": [{"number": 212, "title": "The server owns every clock", "day": "2026-10-20", "changes": [], "changed_by": [], "goal": ""}]}
DECISIONS = {
    238: {"number": 238, "title": "The past lives past the portal", "day": "2026-11-04", "changes": [{"n": 206, "point": 3, "title": "The Orkmaster's column"}], "changed_by": [{"number": 241, "title": "A later word", "day": "2026-11-05", "points": [2]}],
          "entry": "## 238. The past lives past the portal\n\nWhy: the owner asked.", "goal": "seat"},
    206: {"number": 206, "title": "The Orkmaster's column", "day": "2026-10-01", "changes": [], "changed_by": [{"number": 238, "title": "The past lives past the portal", "day": "2026-11-04", "points": [3]}], "entry": "## 206. The column", "goal": ""},
    240: {"number": 240, "title": "A hypothesis's verdict", "day": "2026-11-01", "changes": [], "changed_by": [], "entry": "## 240. A verdict", "goal": ""},
    212: {"number": 212, "title": "The server owns every clock", "day": "2026-10-20", "changes": [], "changed_by": [], "entry": "## 212. The clocks", "goal": ""},
}


def cards(n, first_day=20):
    """n cards, one a day from the 20th of November down: goals g1, g3.. and decisions 302, 304.. on their own days, the newest first."""
    return ([goal(f"g{i}", f"Goal {i}", f"2026-11-{first_day - i:02d}") for i in range(1, n + 1, 2)],
            [{"number": 300 + i, "title": f"Decision {i}", "day": f"2026-11-{first_day - i:02d}", "changes": [], "changed_by": [], "goal": ""} for i in range(2, n + 1, 2)])


class PastHost(RoadHost):
    def __init__(self, newest=0, deck=None, history=None):
        super().__init__(bare=True)
        self.newest = newest
        self.history = history
        self.deck = deck                                                                                      # (goals, decisions) of v0.4 when a test wants a different deck

    def handle(self, name, a):
        if not name.startswith(("ideas.chronicle", "ideas.history")):
            return super().handle(name, a)
        self.log.append((name, a))
        if name == "ideas.chronicle_last":
            return {"decisions": [{"number": self.newest, "title": "A decision", "element": "", "kind": "decision", "parties": ["design"], "version": "", "at": "2026-11-05T10:00:00"}] if self.newest else []}
        if name == "ideas.history":
            return self.history if self.history is not None else {"kind": "tag", "versions": [{"id": "v:0.4", "name": "v0.4", "day": "2026-11-02"}], "goals": []}
        if name == "ideas.chronicle":
            new = {**NEW, "goals": self.deck[0], "decisions": self.deck[1]} if self.deck else NEW
            return {"kind": "tag", "earlier": {"kind": "tag", "name": "v0.4", "day": "2026-11-02"}, "chapters": [new, OLD], "unreleased": UNRELEASED}
        if name == "ideas.chronicle_chapter":
            return {**NEW, "goals": self.deck[0], "decisions": self.deck[1]} if self.deck and a["id"] == "v:0.4" else OLD_FULL
        if name == "ideas.chronicle_find":
            want = a["query"].lower().split()
            gs, ds = (self.deck or (NEW["goals"], NEW["decisions"]))
            hit = lambda s: all(w in s.lower() for w in want)  # noqa: E731
            mine = {"id": a["id"], "kind": "tag", "name": "v0.4", "day": "2026-11-02",
                    "goals": [{"idea": g["idea"], "title": g["title"], "in": ["title"]} for g in gs if hit(g["title"])],
                    "decisions": [{"number": d["number"], "title": d["title"], "day": d["day"], "in": ["decision"]} for d in ds if hit(d["title"])]}
            return {"query": a["query"], "found": 0, "more": 0, "chapters": [mine] if mine["goals"] or mine["decisions"] else [], "unreleased": None}
        if name == "ideas.chronicle_goal":
            return {**NEW["goals"][0], "spec": {"asked": "A seat that stays.", "gist": "Keep the seat for a minute.", "sections": [{"party": "design", "title": "Design", "parts": {"Will": "Show the seat held."}}]},
                    "decision": DECISIONS[238], "changed_by": [{"number": 241, "title": "A later word", "day": "2026-11-05", "points": [2]}], "how_now": [{"capability": "seat", "title": "The kept seat"}],
                    "quality": {"findings": [{"id": "f1", "source": "lens", "what": "The bar is hard to see", "found": "", "level": "work"}]}}
        if name == "ideas.chronicle_decision":
            if a["number"] not in DECISIONS:
                return {"error": "That decision is not in the log"}
            return DECISIONS[a["number"]]
        raise AssertionError(name)


def asked(host, name):
    return [a for n, a in host.log if n == name]


def open_past(gui, tab="design", host=None, seen=None):
    pg, host, log = open_hand(gui, host=host or PastHost())
    if seen is not None:
        pg.evaluate("(n) => localStorage.setItem('orkboard.past.seen.design', String(n))", seen)
        pg.reload()
        pg.wait_for_selector(".hand", state="attached", timeout=WAIT_MS)
    pg.locator(".table-tab[data-tab]").first.wait_for(timeout=WAIT_MS)
    if tab != "orkmaster":
        call(pg, "frame/state.js", "openTab", tab)
    pg.locator(".release-lane").wait_for(timeout=WAIT_MS)
    return pg, host, log


def finish(pg, log):
    pg.close()
    assert not log, "\n".join(log)


def test_a_goal_card_of_the_past_is_picked_and_the_table_shows_it_as_it_was(gui):
    pg, host, log = open_past(gui)
    call(pg, "frame/state.js", "pick", "seat")                                                              # a card of the history book is picked (history.js)
    pg.locator(".chr-goal").wait_for(timeout=WAIT_MS)
    assert sig(pg, "frame/state.js", "picked") == "seat" and sig(pg, "frame/state.js", "over") is None, "picked, nothing over the pane"
    assert pg.locator("#table-pane .chr-goal").count() == 1, "the table shows it"
    text = pg.locator(".chr-goal").inner_text()
    assert "Reconnect keeps your seat" in text and "A seat that stays." in text and "Show the seat held." in text
    assert pg.locator(".chr-changed").inner_text().startswith("changed by §241")
    assert pg.locator(".chr-decision .chr-link").inner_text() == "§238 The past lives past the portal" and "The bar is hard to see" in pg.locator(".chr-quality").inner_text()
    shot(pg, "past-goal.png")
    pg.keyboard.press("Escape")                                                                             # put away as any pick
    pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.picked.value === '')", timeout=WAIT_MS)
    finish(pg, log)


def test_a_decision_opens_its_entry_over_the_pane_its_links_are_walked_and_one_gone_is_said_in_words(gui):
    pg, host, log = open_past(gui)
    pg.evaluate("() => import('/static/js/table/chronicle.js').then((m) => m.openChronicle({ decision: 238 }))")
    page = pg.locator('.chr-decision-page[data-decision="238"]')
    page.wait_for(timeout=WAIT_MS)
    assert sig(pg, "frame/state.js", "over")["kind"] == "chronicle" and "Why: the owner asked." in page.locator(".chr-entry").inner_text()
    assert page.locator('[data-links="Changes"] .chr-link').inner_text() == "§206.3 The Orkmaster's column"
    assert page.locator('[data-links="Changed by"] .chr-link').inner_text() == "§241.2 A later word"
    page.get_by_role("button", name="The goal it came from").click()
    pg.locator(".chr-goal").wait_for(timeout=WAIT_MS)
    pg.locator(".chr-back button").click()
    page.wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")                                                                             # ← leaves for the tab's table
    pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.over.value === null)", timeout=WAIT_MS)
    pg.evaluate("() => import('/static/js/table/chronicle.js').then((m) => m.openChronicle({ decision: 240 }))")      # a decision of no goal
    pg.locator('.chr-decision-page[data-decision="240"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".chr-decision-page").get_by_role("button", name="The goal it came from").count() == 0
    pg.evaluate("() => import('/static/js/table/chronicle.js').then((m) => m.openChronicle({ decision: 999 }))")
    pg.locator(".chr-err").first.wait_for(timeout=WAIT_MS)
    assert "not in the log" in pg.locator(".chr-err").first.inner_text()
    finish(pg, log)


def test_a_decision_named_by_the_conflict_or_the_bubble_opens_its_entry(gui):
    pg, host, log = open_past(gui)
    pg.evaluate("() => import('/static/js/table/chronicle.js').then((m) => m.openChronicle({ decision: 212 }))")
    pg.locator('.chr-decision-page[data-decision="212"]').wait_for(timeout=WAIT_MS)
    assert pg.locator("[data-title]").text_content().strip().endswith("Decision §212 · through Design")
    finish(pg, log)


def test_never_looked_at_nothing_is_new_the_first_read_is_taken_as_seen(gui):
    pg, host, log = open_past(gui, tab="orkmaster", host=PastHost(newest=241))
    pg.wait_for_function("() => localStorage.getItem('orkboard.past.seen.design') === '241'", timeout=WAIT_MS)
    assert pg.locator(".table-tab__new").count() == 0
    finish(pg, log)


# -- a first open over the real host (spec 162 J; decisions §277): the past from history lies once ---------------------------------------------------

import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402


HERE = Path(__file__).resolve().parents[1]
HISTORY = [("201-first-sign", "201"), ("202-then-seat", "202"), ("203-the-lobby", "203"), ("204-no-decision", "")]


def _page(slug, decisions):
    return (f"---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nsize:\npriority: normal\nshort: {slug}\nphase: done\nroute: design, tech\nspec: docs/specs/{slug}.md\n"
            f"decisions: {decisions}\nby: person\nlaid: history\nschema: 3\n---\n# {slug}\n\n## Gist\n{slug}.\n")


@pytest.fixture(scope="module")
def first_open(tmp_path_factory, gui):
    """The real host and server over a git project whose goal pages are laid done as history, with decisions: in a log: `(server, browser)`, the browser the gui fixture's, the state its own."""
    tmp = tmp_path_factory.mktemp("first_open")
    browser = gui[1]
    mp = pytest.MonkeyPatch()
    mp.setenv("ORKCRAFT_STATE_DIR", str(tmp / "state"))
    repo = tmp / "project"
    wiki = repo / "llm-wiki/general/pages"
    (wiki / "ideas").mkdir(parents=True)
    (wiki / "tracks").mkdir()
    (repo / "docs").mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    for t in ("design", "product", "tech", "general"):
        shutil.copy(HERE / f"llm-wiki/general/pages/tracks/{t}.md", wiki / "tracks" / f"{t}.md")
    log = ["# Decisions\n"]
    for n, day in ((201, "26 October 2026"), (202, "27 October 2026"), (203, "3 November 2026")):
        log.append(f"## {n}. Decision {n} ({day}, the owner)\n\nWhy: a reason.\n")
    (repo / "docs/decisions.md").write_text("\n".join(log), encoding="utf-8")
    for slug, dec in HISTORY:
        (wiki / "ideas" / f"{slug}.md").write_text(_page(slug, dec), encoding="utf-8")
    git = ["git", "-c", "user.email=test@orkcraft.local", "-c", "user.name=Test Runner"]
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
    when = {**os.environ, "GIT_AUTHOR_DATE": "2026-11-04T10:00:00", "GIT_COMMITTER_DATE": "2026-11-04T10:00:00"}      # a goal with no decision lies on its commit's day: a fixed one, not the day the test runs
    subprocess.run([*git, "commit", "-qm", "init"], cwd=repo, check=True, env=when)
    from orkboard.gui.board_host import Orkboard
    from orkboard.gui.server import Server
    from orkboard.realm import project_kind
    host = Orkboard(repo)
    project_kind.keep(host.ideas.state_dir, "code")
    host.first_open.tools_skipped = True
    server = Server(host)
    thread = server.start_thread()
    yield server, browser
    server.stop()
    thread.join(10)
    mp.undo()


def test_a_first_open_lays_each_history_goal_once_in_the_history_never_in_the_discard_and_no_tab_wears_the_dot(first_open):
    server, browser = first_open
    ctx = browser.new_context(viewport={"width": 1366, "height": 768})
    pg = ctx.new_page()
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
    pg.goto(server.url)
    pg.locator(".table-tab[data-tab]").first.wait_for(timeout=WAIT_MS)
    call(pg, "frame/state.js", "openTab", "design")
    pg.locator("[data-book]").click()
    pg.locator(".hist-card").first.wait_for(timeout=WAIT_MS)                                               # the history draws although the flags were raised while it first asked
    assert sorted(c.get_attribute("data-goal") for c in pg.locator(".hist-card [data-goal]").all()) == sorted(h[0] for h in HISTORY), "each card lies once"
    assert pg.locator(".release-lane__past, .release-lane .sm").count() == 0 and pg.locator(".release-lane__done").count() == 0, "none in the discard, none among the goals done and not yet seen"
    pg.locator("[data-book]").click()
    pg.wait_for_timeout(500)
    assert pg.locator(".table-tab__new").count() == 0, "no party's tab wears the past's dot"
    pg.evaluate("() => document.querySelectorAll('[class*=toast]').forEach((e) => { e.style.display = 'none'; })")      # the shot is of the lane
    pg.locator("[data-book]").click()
    pg.locator(".hist-card").first.wait_for(timeout=WAIT_MS)
    shot(pg, "past-first-open-design-1366.png")
    pg.locator("[data-book]").click()
    for tab in ("tech", "product", "design"):                                                           # the dot is not lit by a look at another tab either
        call(pg, "frame/state.js", "openTab", tab)
        pg.wait_for_timeout(300)
        assert pg.locator(".table-tab__new").count() == 0, tab
    assert not errors, errors
    ctx.close()
