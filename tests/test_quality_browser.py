"""Spec 132 D's face (docs/specs/132-four-levels-the-way-down-and-findings.md D.3, D.4; decisions §234.3–§234.4, §237.1–§237.2, §237.8) in a real browser against the table's stub host answering the rows `quality` and `finding`
(realm/findings.py `rows`), `ideas.quality` and the four commands of gui/ideas_findings.py: the quality card of a goal (its face *Quality of <goal>*, the finder's head, never urgent: after a failure, a question, under its
party's lane; lifted, each finding the finder's head, its level's sign, *<Party> found: …*, *The cause is in the code / the spec / the decision*, the way down in one line with its cost, **Fix it there**, **Not now** and under its **…**
**Another level…**; **Fix all there** with two findings or more), a finding of no goal as a card of its own, and the *Quality* page a done goal's *Done* mark opens (the verdict against the spec, the checks, the lenses, each finding
with what became of it; a finding put off taken again with **Fix it there**). Screenshots to $QUALITY_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_shell_browser import _calls  # noqa: E402
from tests.test_table_desktop_browser import WayHost, pick, title, watch  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["QUALITY_SHOTS"]) if os.environ.get("QUALITY_SHOTS") else None
GOAL = "Keep the seat when a socket reconnects"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(450)
        pg.screenshot(path=str(SHOTS / name))


def pulls(level, sections=0, tasks=0, usd=0.0):
    return {"level": level, "sections": [{"idea": "seat", "party": "tech"}] * sections, "tasks": [{"idea": "seat", "id": f"t{i}"} for i in range(tasks)], "checks": 0, "estimate": {"usd_low": usd / 2, "usd_high": usd}}


def finding(fid, level, what, party="tech", **more):
    return {"id": fid, "party": party, "level": level, "what": what, "cause": f"cause of {fid}", "change": f"change of {fid}", "shows": f"the screen of {fid}", "promised": f"the promise of {fid}", "source": "verdict", "on": "server/rooms.ts",
            "answer": "", "pulls": pulls(level, 2 if level == "decision" else 1 if level == "spec" else 0, 3 if level == "decision" else 1, 0.8 if level == "decision" else 0.4 if level == "spec" else 0.1), **more}


F_DECISION = finding("fd", "decision", "The order of rooms was never decided", party="game")
F_SPEC = finding("fs", "spec", "The spec leaves the seat count out")
F_WORK = finding("fw", "work", "The list is plain: no order")


def quality_row(findings, idea="seat"):
    total = {"level": findings[0]["level"], "sections": [], "tasks": [], "checks": 0, "estimate": {"usd_low": 0.5, "usd_high": 1.3}}
    return {"kind": "quality", "idea": idea, "goal": "tech", "title": GOAL, "text": f"Quality of {GOAL}", "priority": "normal", "blocks": False, "at": "2026-11-03T10:00:00", "level": findings[0]["level"], "findings": findings, "pulls": total}


def record(findings):
    return {"idea": "seat", "title": GOAL, "state": "done", "at": "2026-11-03T10:00:00", "result": {"parties": [{"party": "tech", "parts": [], "done_when": [{"text": "A seventh player is refused", "state": "ok"}]}]},
            "verdict": [{"party": "tech", "id": "server/rooms.ts", "kind": "changed", "verdict": "differs", "line": "the cap is eight"}, {"party": "tech", "id": "lobby-screen", "kind": "changed", "verdict": "ok", "line": "ten seats"},
                        {"party": "game", "id": "seat-list", "kind": "new", "verdict": "missing", "line": "never made"}],
            "checks": [{"by": "reviewer", "state": "ok", "left": 0}, {"by": "tester", "state": "failed", "left": 2}], "lenses": [], "hypothesis": None, "findings": findings}


class QualityHost(WayHost):
    """The way host with the goal `seat` done and the quality rows the test puts; the four commands answer and take the finding out of the hand as the real host does."""

    def __init__(self, findings=(), fails=False, **kw):
        super().__init__(state="done", **kw)
        if not fails:                                                   # the stub's goal `seat` has a failed task: its failure card would lie in front of everything
            next(n for n in self.nodes if n["slug"] == "seat")["tasks"] = []
        self.findings = [dict(f) for f in findings]
        self.put()

    def put(self):
        waiting = [f for f in self.findings if not f["answer"] or f["answer"] == "moved"]
        self.needs = [quality_row(waiting)] if waiting else []

    def handle(self, name, a):
        if name == "ideas.quality":
            self.log.append((name, a))
            return record([{**f, "status": "sorted" if f["answer"] in ("", "later", "moved") else "answered"} for f in self.findings])
        if name in ("ideas.finding_fix", "ideas.finding_later", "ideas.finding_move", "ideas.finding_fix_all"):
            self.log.append((name, a))
            if name == "ideas.finding_fix_all":
                self.findings = [{**f, "answer": "fix"} for f in self.findings]
                self.put()
                self.push()
                return {"ok": True, "fixed": [{"id": f["id"], "level": f["level"], "fix": {"idea": "fix-x"}} for f in self.findings], "refused": []}
            f = next(x for x in self.findings if x["id"] == a["id"])
            f["answer"] = {"ideas.finding_fix": "fix", "ideas.finding_later": "later", "ideas.finding_move": "moved"}[name]
            if name == "ideas.finding_move":
                f["level"] = a["level"]
            self.put()
            self.push()
            return {"ok": True, "level": f["level"], "fix": {"idea": "fix-x"}, "pulls": f["pulls"]}
        return super().handle(name, a)


def start(gui, width, host):
    errors: list[str] = []
    server, browser = gui
    pg = narrow.page(browser, width)
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    return pg, errors


def card(pg, kind="quality"):
    return pg.locator(f'.hand-card[data-kind="{kind}"]').first


def lift(pg, kind="quality"):
    card(pg, kind).wait_for(timeout=WAIT_MS)
    card(pg, kind).click(position={"x": 10, "y": 20})
    lifted = pg.locator(".hand-lifted")
    lifted.wait_for(timeout=WAIT_MS)
    return lifted


def test_a_goals_findings_are_one_card_never_urgent_lying_behind_a_failure_with_its_leaders_head_and_the_sum_as_its_gem(gui):
    host = QualityHost([F_DECISION, F_SPEC, F_WORK], fails=True)
    pg, errors = start(gui, "wide", host)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelectorAll('.hand-stack').length > 0", timeout=WAIT_MS)
        stack = pg.locator('.hand-stack[data-goal="seat"]')
        assert stack.count() == 1 and stack.locator('.hand-card[data-top="1"]').get_attribute("data-kind") == "failed", "a failure first: the quality card is never urgent"
        assert stack.get_attribute("data-cards") == "2" and pg.locator('.hand-card[data-kind="quality"]').count() == 0, "the card lies under it, face down"
        host.nodes[[n["slug"] for n in host.nodes].index("seat")]["tasks"] = []
        host.push()
        card(pg).wait_for(timeout=WAIT_MS)
        assert pg.locator('.hand-card[data-kind="quality"]').count() == 1, "one card a goal, not a card a finding"
        gem = card(pg).locator(".ork-gem")
        assert gem.get_attribute("data-cost") == "$0.50–1.30", gem.get_attribute("data-cost")
        assert card(pg).locator(".ork-race__head, img.ork-race__head").count() >= 1, "the first finding's leader asks"
        shot(pg, "wide-quality-card.png")
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_lifted_each_finding_says_who_found_it_its_level_its_cause_its_way_down_and_two_answers(gui):
    host = QualityHost([F_WORK, F_DECISION, F_SPEC])
    pg, errors = start(gui, "wide", host)
    try:
        lifted = lift(pg)
        items = lifted.locator(".hand-finding")
        assert [i.get_attribute("data-level") for i in items.all()] == ["work", "decision", "spec"], "in the host's order (it sorts: Decision first)"
        assert " ".join(lifted.locator(".hand-lifted__kind").text_content().split()) == "Quality of " + GOAL
        first = lifted.locator('.hand-finding[data-finding="fd"]')
        assert "found: The order of rooms was never decided" in " ".join(first.locator(".hand-finding__what").inner_text().split())
        assert first.locator(".hand-finding__what").inner_text().startswith("Game design found:") or first.locator(".hand-finding__what").inner_text().startswith("game found:")
        assert first.locator(".hand-finding__cause").inner_text() == "The cause is in the decision: cause of fd"
        assert lifted.locator('.hand-finding[data-finding="fs"] .hand-finding__cause').inner_text() == "The cause is in the spec: cause of fs"
        assert lifted.locator('.hand-finding[data-finding="fw"] .hand-finding__cause').inner_text() == "The cause is in the code: cause of fw"
        sign = first.locator(".hand-finding__who .ork-sign")
        assert sign.get_attribute("title") == "Changes the decision" and "compass" in sign.get_attribute("class")
        assert " ".join(first.locator(".hand-wayline__words").inner_text().split()) == "About $0.40–0.80 at API prices: 2 sections, 3 tasks", first.locator(".hand-wayline__words").inner_text()
        assert [b.inner_text().strip() for b in first.locator(".hand-finding__acts .ork-btn:not(.hand-finding__dots)").all()] == ["Fix it there", "Not now"]
        assert first.locator('[aria-label="Another level…"]').count() == 0, "Another level… is under the finding's …"
        first.get_by_role("button", name="More answers").click()
        levels = first.locator('[aria-label="Another level…"] .ork-btn')
        assert [b.inner_text().strip() for b in levels.all()] == ["Spec", "Work"]
        shot(pg, "wide-quality-lifted.png")
        assert lifted.get_by_role("button", name="Fix all there").count() == 1
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_fix_it_there_not_now_and_another_level_send_their_commands_and_the_card_closes_with_its_last_finding(gui):
    host = QualityHost([F_SPEC, F_WORK])
    pg, errors = start(gui, "wide", host)
    try:
        lifted = lift(pg)
        lifted.locator('.hand-finding[data-finding="fs"]').get_by_role("button", name="More answers").click()
        lifted.locator('.hand-finding[data-finding="fs"] [data-level="work"]').click()
        assert _calls(pg, host, "ideas.finding_move") == [{"id": "fs", "level": "work"}]
        lifted.locator('.hand-finding[data-finding="fs"] [data-answer="later"]').click()
        assert _calls(pg, host, "ideas.finding_later") == [{"id": "fs"}]
        pg.wait_for_function("() => document.querySelectorAll('.hand-lifted .hand-finding').length === 1", timeout=WAIT_MS)
        lifted.locator('.hand-finding[data-finding="fw"] [data-answer="fix"]').click()
        assert _calls(pg, host, "ideas.finding_fix") == [{"id": "fw"}]
        pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"quality\"]')", timeout=WAIT_MS)       # answered: the card left the hand
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_fix_all_there_sends_the_goal_and_closes_the_card(gui):
    host = QualityHost([F_DECISION, F_SPEC, F_WORK])
    pg, errors = start(gui, "wide", host)
    try:
        lifted = lift(pg)
        button = lifted.get_by_role("button", name="Fix all there")
        assert "About" in button.get_attribute("title") and "at API prices" in button.get_attribute("title"), "its cost said first"
        button.click()
        assert _calls(pg, host, "ideas.finding_fix_all") == [{"idea": "seat"}]
        pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_finding_of_no_goal_is_a_card_of_its_own(gui):
    host = QualityHost([])
    host.needs = [{"kind": "finding", "idea": "", "goal": "tech", "id": "fl", "title": "A lens found the lobby slow", "text": "A lens found the lobby slow", "party": "tech", "level": "work", "what": "A lens found the lobby slow", "cause": "no index",
                   "change": "", "shows": "", "promised": "", "source": "lens", "on": "lobby", "answer": "", "priority": "normal", "blocks": False, "at": "2026-11-03T10:00:00", "pulls": pulls("work", 0, 1, 0.1)},
                  {"kind": "finding", "idea": "", "goal": "tech", "id": "fm", "title": "A concern about the rules", "text": "A concern about the rules", "party": "tech", "level": "spec", "what": "A concern about the rules", "cause": "",
                   "change": "", "shows": "", "promised": "", "source": "concern", "on": "rules", "answer": "", "priority": "normal", "blocks": False, "at": "2026-11-03T10:01:00", "pulls": pulls("spec", 1, 1, 0.3)}]
    pg, errors = start(gui, "wide", host)
    try:
        pg.locator('.hand-card[data-kind="finding"]').first.wait_for(timeout=WAIT_MS)
        assert pg.locator('.hand-stack[data-stack^="party:tech"]').get_attribute("data-cards") == "2", "each its own card (one under the other)"
        lifted = lift(pg, "finding")
        assert lifted.locator(".hand-finding").count() == 1 and lifted.get_by_role("button", name="Fix all there").count() == 0
        assert "The cause is in the code" in lifted.inner_text()
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_done_mark_opens_the_quality_page_with_the_verdict_the_checks_and_each_finding_and_what_became_of_it(gui):
    later = {**F_SPEC, "answer": "later"}
    fixed = {**F_WORK, "answer": "fix", "fix": {"idea": "fix-x"}}
    host = QualityHost([later, fixed])
    pg, errors = start(gui, "wide", host)
    try:
        pg.locator('.table-tab[data-tab="tech"]').click()                       # through Tech: the result, and under it the quality record on the table (spec 156 C.1)
        pick(pg, "seat")
        pg.locator(".table-phases").wait_for(timeout=WAIT_MS)
        page = pg.locator('.phase-quality .quality-page')
        page.wait_for(timeout=WAIT_MS)
        page.locator(".quality-finding").first.wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-over").count() == 0 and pg.locator("button[data-phase]").count() == 0
        verdict = page.locator('[data-part="verdict"]')
        assert [r.get_attribute("data-verdict") for r in verdict.locator("li[data-verdict]").all()] == ["differs", "ok", "missing"]
        assert "≠" in verdict.inner_text() and "✗" in verdict.inner_text() and "A seventh player is refused" in verdict.inner_text()
        assert "reviewer" in page.locator('[data-part="checks"]').inner_text() and "2 left" in page.locator('[data-part="checks"]').inner_text()
        fates = {f.get_attribute("data-finding"): f.locator('[data-part="fate"]').inner_text() for f in page.locator(".quality-finding").all()}
        assert fates["fs"] == "Not now: put off" and fates["fw"].startswith("Fixed there by a fix goal"), fates
        assert page.locator('[data-finding="fw"] [data-answer="fix"]').count() == 0, "a fixed one is not fixed twice"
        shot(pg, "wide-quality-page.png")
        page.locator('[data-finding="fs"] [data-answer="fix"]').click()
        assert _calls(pg, host, "ideas.finding_fix") == [{"id": "fs"}], "taken again from the record, no new call of a leader's"
        pg.wait_for_function("() => document.querySelector('.quality-finding[data-finding=\"fs\"] [data-part=\"fate\"]')?.innerText.startsWith('Fixed there')", timeout=WAIT_MS)
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)
