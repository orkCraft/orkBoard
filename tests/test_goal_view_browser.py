"""Spec 128 part F.2–F.3 (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md, decisions §206.4, §206.8; mockup docs/mockups/goal-card/), in a real browser against a stub host: a goal picked at a leader's tab.

A goal agreed or at work picked shows, in place of the leader's map, what it will change: the parts of the leader's section of the spec (its *Will be* lines) each a card with New, Changes or Read only and its lines (+ added, ~ changed), Tech's contract as a
diff, Design's screens Now and Will be; beside it a small whole map with the parts lit, the section's *Done when* and the goal's tasks at this leader; a part pressed opens the leader's bubble with it. A goal done (the discard's) shows what it changed against
what its spec promised, each part As promised, Not quite, More than promised or Not done, and its *Done when* checked; the Play die wears its rune and plays that goal. Nothing picked: the maps as they were; Esc or the title's × picks nothing."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, head, node, open_hand, sig, task  # noqa: E402

pytestmark = pytest.mark.browser

TECH_SECTION = "### Done when\n- Rounds keep their score\n- The lobby opens\n\n### Will be\n- new src/lobby — a lobby\n- changed src/score — keep rounds\n- gone src/old"
DESIGN_SECTION = "### Done when\n- The winner shows first\n\n### Will be\n- changed results — the winner first\n- new podium — a podium of three"
SYSTEM = {"commit": "abc1234def", "short": "abc1234", "at": "", "ref": "dev", "since": "", "changed": {}, "uses_changed": [], "goals": {}, "overview": {"containers": [], "links": [], "shared": [], "parts": {}},
          "columns": [{"name": "src", "parts": [{"path": "src/score", "name": "score", "count": 3, "uses": ["src/net"], "used_by": [], "row": 0, "gone": False},
                                                {"path": "src/net", "name": "net", "count": 2, "uses": [], "used_by": ["src/score"], "row": 1, "gone": False},
                                                {"path": "src/other", "name": "other", "count": 1, "uses": [], "used_by": [], "row": 2, "gone": False},
                                                {"path": "src/old", "name": "old", "count": 1, "uses": [], "used_by": [], "row": 3, "gone": False}], "stack": []}]}
SCREENS = {"head": "abc", "source": "routes", "entry": "lobby", "more": False, "segments": [], "loose": [], "steps": [["lobby"], ["results"]],
           "screens": [{"id": "lobby", "name": "Lobby", "path": "/lobby", "file": "src/lobby.tsx"}, {"id": "results", "name": "Results", "path": "/results", "file": "src/results.tsx"}],
           "links": [{"from": "lobby", "to": "results"}]}
RESULT = {"idea": "codes", "state": "done", "files": 5, "screens": [], "parties": [
    {"party": "tech", "title": "Tech", "parts": [{"id": "src/score", "kind": "changed", "verdict": "ok", "line": "keep rounds", "note": "keep rounds"},
                                                {"id": "src/lobby", "kind": "new", "verdict": "differs", "line": "its tasks landed, but nothing of this part changed", "note": "a lobby"},
                                                {"id": "src/extra", "kind": "", "verdict": "extra", "line": "changed, and its spec did not say so", "note": ""},
                                                {"id": "src/old", "kind": "gone", "verdict": "missing", "line": "nothing of it landed", "note": ""}],
     "done_when": [{"text": "Rounds keep their score", "state": "ok"}, {"text": "The lobby opens", "state": ""}]}]}


class GoalHost(HandHost):
    """Four parties (Tech led by the Architect, Design with its screens), a goal at work whose plan runs across Tech, Design and Product, one agreed with no plan, one waiting in analysis, and one done in the discard; `ideas.page`,
    `ideas.system`, `ideas.screens`, `ideas.goal_result` and `ideas.play` answer in the shapes the host sends."""

    def __init__(self):
        super().__init__(bare=True)
        tech, design, product = (next(p for p in self.parties if p["slug"] == s) for s in ("tech", "design", "product"))
        tech["leader"] = {**tech["leader"], "slug": "architect"}
        design["party_craft"] = "design"
        tasks = [task("m1", "Make the lobby", "merged", party="tech", step=1, made="the lobby", head=head("peon", tier="warrior")),
                 task("m2", "Draw the winner first", "running", party="design", step=2, after=["m1"], head=head("dryad", "design")),
                 task("m3", "Keep the rounds", "waiting", party="tech", step=1, after=["m1", "m2"]),
                 task("m4", "Name the theme", "waiting", party="product", step=3, after=["m3"])]
        music = node("music", "tech", "Music in the lobby", "table", state="working", element="meadow", stage="implementation", tasks=tasks,
                     route=[{"party": "tech", "leader": "tech-lead", "head": {"race": "orc", "tier": "elder"}}, {"party": "design", "leader": "design-lead", "head": {"race": "dryad", "tier": "elder"}}, {"party": "release", "leader": "release-lead", "head": {"race": "lich", "tier": "elder"}}])
        timer = node("timer", "tech", "The clock after a reconnect", "table", state="working", element="dust", stage="implementation", tasks=[task("t1", "Reset the clock", "running", party="tech", step=1)])
        fresh = node("fresh", "design", "Host can skip a round", "table", state="ready", agreed=True, element="void", back={"route": [], "cost": None, "offer": [], "short": False, "heard": [], "stances": [], "round": 1,
                                                                                                                  "ripe": {"left_s": 120, "seconds": 240, "risk": "low", "priority": "high", "held": False, "by": "", "why": ""}})
        codes = node("codes", "tech", "Room codes without look-alikes", "discard", state="done", element="ice", updated="2026-10-20T12:00:00",
                     tasks=[task("c1", "Make the codes", "merged", party="tech", step=1, made="four letters")])
        self.nodes = [music, timer, fresh, codes]
        self.result = RESULT

    def handle(self, name, a):
        if name == "ideas.page":
            self.log.append((name, a))
            return {"slug": a["slug"], "title": a["slug"], "track": "tech", "state": "working", "checks": [], "sections": [
                {"name": "Asked", "thesis": "", "text": "Music in the lobby"}, {"name": "Tech", "thesis": "", "text": TECH_SECTION}, {"name": "Design", "thesis": "", "text": DESIGN_SECTION}]}
        if name == "ideas.system":
            self.log.append((name, a))
            return SYSTEM
        if name == "ideas.screens":
            self.log.append((name, a))
            return SCREENS
        if name == "ideas.goal_result":
            self.log.append((name, a))
            return self.result
        if name == "ideas.play":
            self.log.append((name, a))
            return {"state": "stopped"} if a.get("peek") else {"state": "starting"}
        return super().handle(name, a)


def open_goals(gui, width="wide"):
    pg, host, log = open_hand(gui, host=GoalHost(), width=width)
    pg.wait_for_selector(".col-card", timeout=WAIT_MS)
    return pg, host, log


def pick_music(pg):
    pg.locator('.col-card[data-goal="music"]').click()
    pg.wait_for_function("() => document.querySelector('.table-board--plan, .gv')", timeout=WAIT_MS)


def open_tab(pg, slug):
    pg.locator(f'.table-tab[data-tab="{slug}"]').click()


def texts(pg, selector):
    return [t.strip() for t in pg.locator(selector).all_inner_texts()]


def test_a_goal_at_work_picked_shows_at_tech_what_it_will_change_in_cards_with_their_lines_the_contract_as_a_diff_and_a_small_map_lit(gui):
    pg, host, log = open_goals(gui)
    try:
        open_tab(pg, "tech")
        pg.wait_for_selector(".table-sys", timeout=WAIT_MS)
        assert pg.locator(".gv").count() == 0, "nothing picked: the System as it was"
        pick_music(pg)
        view = pg.locator('.gv[data-view="will"][data-party="tech"]')
        view.wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-sys").count() == 0, "the view takes the map's place"
        pg.wait_for_selector(".gv-card", timeout=WAIT_MS)
        pg.wait_for_selector('.gv-card[data-part="src/net"]', timeout=WAIT_MS)
        assert "what it will change" in view.locator(".gv-title").inner_text().lower() and "music in the lobby" in view.locator(".gv-title").inner_text().lower()
        cards = {c.get_attribute("data-part"): c for c in view.locator(".gv-card").all()}
        assert set(cards) == {"src/lobby", "src/score", "src/old", "src/net"}, "the section's parts, then the part they use read only"
        kind = lambda part: cards[part].locator(".gv-kind").text_content().strip()  # noqa: E731
        assert (kind("src/lobby"), kind("src/score"), kind("src/old"), kind("src/net")) == ("New", "Changes", "Goes", "Read only")
        assert cards["src/score"].locator("b").first.inner_text() == "score", "a part named as the map names it"
        assert texts(pg, '.gv-card[data-part="src/lobby"] .gv-lines li') == ["+ a lobby"] and texts(pg, '.gv-card[data-part="src/score"] .gv-lines li') == ["~ keep rounds"]
        assert pg.locator('.gv-card[data-part="src/lobby"] .gv-lines li.is-add').count() == 1 and pg.locator('.gv-card[data-part="src/score"] .gv-lines li.is-chg').count() == 1
        diff = view.locator(".gv-diff").inner_text()
        assert "+ src/lobby — a lobby" in diff and "~ src/score — keep rounds" in diff and "- src/old" in diff, "Tech's contract as a diff"
        assert pg.locator(".gv-diff .add").count() == 1 and pg.locator(".gv-diff .del").count() == 1
        # the side: the small whole map with its parts lit, the section's Done when, its tasks here
        lit = pg.eval_on_selector_all(".gv-mini__b.is-lit", "els => els.map((e) => e.dataset.id).sort()")
        assert lit == ["src/lobby", "src/old", "src/score"], "the parts it touches are lit, a new part beside the map"
        assert pg.eval_on_selector_all(".gv-mini__b.is-read", "els => els.map((e) => e.dataset.id)") == ["src/net"]
        assert pg.locator(".gv-mini__b").count() == 5
        assert texts(pg, ".gv-done li") == ["Rounds keep their score", "The lobby opens"]
        assert texts(pg, ".gv-tasks li") == ["Make the lobby · done", "Keep the rounds · waiting"], "its tasks at Tech, not Design's or Product's"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.gv-mini__b.is-lit')).backgroundColor") == pg.evaluate(
            "() => { const s = document.createElement('i'); s.style.color = 'var(--ork-elem-meadow)'; document.body.appendChild(s); const c = getComputedStyle(s).color; s.remove(); return c; }"), "lit in the goal's rune colour"
        # a part pressed opens the leader's bubble with it
        cards["src/score"].click()
        pg.wait_for_selector('.table-ask__bubble[data-ask="tech"]', timeout=WAIT_MS)
        assert sig(pg, "table/ask.js", "askOpen") == "tech" and sig(pg, "table/ask.js", "askPart") == {"id": "src/score", "name": "score"}
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_at_design_the_screens_a_goal_changes_are_cards_with_now_and_will_be_and_a_leader_it_does_not_touch_says_so(gui):
    pg, host, log = open_goals(gui)
    try:
        pick_music(pg)
        open_tab(pg, "design")
        view = pg.locator('.gv[data-view="will"][data-party="design"]')
        view.wait_for(timeout=WAIT_MS)
        pg.wait_for_selector('.gv-card[data-part="results"]', timeout=WAIT_MS)
        assert pg.locator(".scr-map").count() == 0
        results, podium = view.locator('.gv-card[data-part="results"]'), view.locator('.gv-card[data-part="podium"]')
        assert results.locator(".gv-kind").text_content().strip() == "Changes" and podium.locator(".gv-kind").text_content().strip() == "New"
        assert texts(pg, '.gv-card[data-part="results"] .gv-pair figcaption') == ["Now", "Will be"], "the screen now and as it will be"
        assert podium.locator(".gv-pair .gv-ph em").first.inner_text().strip() == "none", "a new screen has no picture now"
        assert pg.locator(".gv-diff").count() == 0, "the contract's diff is Tech's"
        assert pg.locator(".gv-mini[data-kind='screens']").count() == 1 and pg.locator(".gv-mini__b.is-lit").count() >= 1
        assert texts(pg, ".gv-done li") == ["The winner shows first"] and texts(pg, ".gv-tasks li") == ["Draw the winner first · working"]
        open_tab(pg, "release")
        pg.wait_for_selector('.gv[data-party="release"] .gv-empty[data-state="none"]', timeout=WAIT_MS)
        assert "nothing of it is on Release’s table" in pg.locator(".gv-empty").inner_text()
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_esc_and_the_titles_cross_pick_nothing_and_the_leaders_map_is_back(gui):
    pg, host, log = open_goals(gui)
    try:
        open_tab(pg, "tech")
        pick_music(pg)
        pg.locator(".gv").wait_for(timeout=WAIT_MS)
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".table-sys", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "" and pg.locator(".gv").count() == 0 and pg.locator(".table-title__unpick").count() == 0
        pick_music(pg)
        pg.locator(".gv").wait_for(timeout=WAIT_MS)
        assert "music in the lobby" in pg.locator(".table-title__pt").inner_text().lower()
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".table-sys", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == ""
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_done_picked_from_the_discard_shows_what_it_changed_against_what_its_spec_promised_and_its_done_when_checked(gui):
    pg, host, log = open_goals(gui)
    try:
        open_tab(pg, "tech")
        pg.wait_for_selector(".table-sys", timeout=WAIT_MS)
        pg.locator('.release-lane [data-slug="codes"], .release-lane [data-portal-card="codes"]').first.click()
        pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.picked.value === 'codes')", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "codes" and sig(pg, "frame/state.js", "over") is None, "the goal pressed in the discard is the goal picked, nothing over the pane (spec 156 D.3)"
        view = pg.locator('.gv[data-view="changed"][data-party="tech"]')
        view.wait_for(timeout=WAIT_MS)
        assert pg.locator('.table-tab[aria-selected="true"]').get_attribute("data-tab") == "tech", "the open tab stays"
        pg.wait_for_selector('.gv-card[data-part="src/score"]', timeout=WAIT_MS)
        assert "against what its spec promised" in view.locator(".gv-title").inner_text().lower()
        words = {c.get_attribute("data-part"): c.locator(".gv-kind").text_content().strip() for c in view.locator(".gv-card").all()}
        assert words == {"src/score": "✓ As promised", "src/lobby": "≠ Not quite", "src/extra": "+ More than promised", "src/old": "✗ Not done"}
        assert pg.locator('.gv-card[data-part="src/lobby"] .gv-lines li.is-dif').count() == 1, "Not quite carries the leader's line"
        assert "keep rounds" in pg.locator('.gv-card[data-part="src/score"]').inner_text()
        assert texts(pg, ".gv-done li") == ["✓ Rounds keep their score", "The lobby opens"] and "done when, checked" in view.locator(".gv-side").inner_text().lower()
        assert pg.locator(".gv-diff").count() == 0, "a goal done has its parts judged, not its contract drawn"
        assert [a for n, a in host.log if n == "ideas.goal_result"][0] == {"idea": "codes"}
        # nothing picked again: Esc
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".table-sys", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_play_die_wears_the_picked_goals_rune_says_play_and_the_goal_and_plays_it(gui):
    pg, host, log = open_goals(gui)
    try:
        die = pg.locator(".hand-die")
        play = pg.locator(".hand-die__play")
        die.wait_for(timeout=WAIT_MS)
        assert die.get_attribute("data-elem") is None and play.get_attribute("aria-label").startswith("Play"), "nothing picked: the die as it was"
        plain = pg.evaluate("() => getComputedStyle(document.querySelector('.hand-die .ork-die')).getPropertyValue('--_pip')")
        pick_music(pg)
        pg.wait_for_selector('.hand-die[data-elem="meadow"]', timeout=WAIT_MS)
        assert play.get_attribute("aria-label") == "Play: Music in the lobby" and play.get_attribute("title") == "Play: Music in the lobby"
        token = pg.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--ork-elem-meadow').trim()")
        worn = pg.evaluate("() => [getComputedStyle(document.querySelector('.hand-die .ork-die')).getPropertyValue('--_pip').trim(), getComputedStyle(document.querySelector('.hand-die .ork-die')).getPropertyValue('--_edge').trim()]")
        assert token and worn == [token, token] and worn[0] != plain.strip(), "the pips and the edge in orkUI's element token"
        play.click()
        pg.wait_for_function("() => document.querySelector('.hand-die[data-open]')", timeout=WAIT_MS)
        for _ in range(100):
            asked = [a for n, a in host.log if n == "ideas.play" and not a.get("peek")]
            if asked:
                break
            pg.wait_for_timeout(50)
        assert asked and asked[0].get("idea") == "music", asked
        assert play.get_attribute("aria-label") == "Close the preview"
        play.click()                                                                              # closes it as ever
        pg.wait_for_function("() => !document.querySelector('.hand-die[data-open]')", timeout=WAIT_MS)
        pg.keyboard.press("Escape")                                                               # nothing picked: the die as it was
        pg.wait_for_function("() => !document.querySelector('.hand-die').dataset.elem", timeout=WAIT_MS)
        assert play.get_attribute("aria-label").startswith("Play") and ":" not in play.get_attribute("aria-label").replace("Play: the project", "")
        # a goal not yet at work does not give the die its rune
        pg.locator('.col-card[data-goal="fresh"]').click()
        pg.wait_for_selector('.col-card[data-goal="fresh"].ork-picked, .col-card[data-goal="fresh"][aria-pressed="true"], [data-lift="acts"]', timeout=WAIT_MS)
        assert die.get_attribute("data-elem") is None, "a goal in review has nothing to play yet"
    finally:
        pg.close()
    assert not log, "\n".join(log)
