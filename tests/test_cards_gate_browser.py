"""Goal "The battle and the gate", stage L (decisions §300.8, §303): the gate mat laid upright on the host's `ideas.gate_guards`, its ring gone, in a real browser on the `gui` fixture's Board
(`?table=cards`, no `?mock=1`), a red gate laid in its state as stage E keeps it: one failing test in a file naming §N, a failing file naming none, a passing file naming §M. The Fix it way's commands
(`ideas.gate_fix_goal`, `ideas.gate_fix_stage`) are stages G and H's: here they are stubs that log what the page sent, and the tests check which one was sent and how, never their effect."""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import goal_branch, ideas  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser
SIZES = [(1440, 900), (1280, 800)]
LOG = "# Decisions\n\n## 1. First\nPlain.\n\n## 2. Second, the old card\nIt stands.\n\n## 3. Third\nAlso stands.\n"
PAGE = "---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nphase: work\nschema: 3\n---\n# {t}\n\n## Gist\nA goal.\n"
SENT = ("ideas.goal_to_dev", "ideas.to_main", "ideas.gate_fix_stage", "ideas.gate_fix_goal", "ideas.ask_leader", "ideas.undo")


def _w(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def lay(server, slug: str, *, red: bool, branch: bool = True) -> None:
    """A goal with its gate as stage E keeps it: on its branch (the way to dev) or, with `branch` false, done in dev (the way to main, the Tests step's record)."""
    host = server.host
    repo, root = Path(host.repo_root), host.ideas.root()
    if not ideas.track_page(root, "tech"):
        ideas.add_track(root, "Tech")
    (root / ideas.IDEAS).mkdir(parents=True, exist_ok=True)
    (root / ideas.IDEAS / f"{slug}.md").write_text(PAGE.format(t=slug), encoding="utf-8")
    ideas.save_state(host.ideas.state_dir, slug, state="decided")
    _w(repo, "docs/decisions.md", LOG)
    _w(repo, "tests/test_red.py", '"""Guards decisions §2."""\n\ndef test_a():\n    assert 0\n')
    _w(repo, "tests/test_bare.py", '"""Nothing named."""\n\ndef test_c():\n    assert 0\n')
    _w(repo, "tests/test_ok.py", '"""Guards decisions §3."""\n\ndef test_d():\n    pass\n')
    failing = ["tests/test_red.py::test_a", "tests/test_bare.py::test_c"] if red else []
    files = ["tests/test_red.py", "tests/test_bare.py", "tests/test_ok.py"] if red else ["tests/test_ok.py"]
    if branch:
        goal_branch.update(host.ideas.state_dir, slug, branch=f"goal/{slug}", failing=failing, files=files)
    else:
        host.ideas._main_checks[slug] = {"running": False, "checks": [{"name": "Tests", "state": "failed" if red else "passed", "words": "", "files": files,
                                                                    "failures": [{"id": i, "classification": "new"} for i in failing]}]}


class Spy:
    """The Fix it way's commands and the moves the gate sends, answered by stubs that log (name, arguments)."""

    def __init__(self, server):
        self.commands, self.log = server.host.commands, []
        self.was = {n: self.commands.get(n) for n in SENT}
        for name in SENT:
            self.commands[name] = lambda args, name=name: (self.log.append((name, dict(args))), {"ok": True})[1]

    def sent(self, name):
        return [a for n, a in self.log if n == name]

    def close(self):
        for name, fn in self.was.items():
            if fn is None:
                self.commands.pop(name, None)
            else:
                self.commands[name] = fn


def open_gate(gui, slug, size=(1440, 900), hash_=None):
    server, browser = gui
    pg = browser.new_page(viewport={"width": size[0], "height": size[1]})
    seen = []
    pg.on("pageerror", lambda e: seen.append(str(e)))
    base = server.url + ("&table=cards" if "?" in server.url else "?table=cards")
    pg.goto(base + (hash_ or f"#mat=gate:{slug}"))
    pg.wait_for_selector("[data-spread=gate] .gt-line, [data-spread=gate] .gt-guards", timeout=WAIT_MS)
    pg.wait_for_selector("[data-spread=gate] .gt[data-way]:not([data-way=''])", timeout=WAIT_MS)
    return pg, seen


INSIDE = """() => { const f = document.querySelector('[data-spread=gate] .mf-field'), fr = f.getBoundingClientRect(); f.scrollTop = 0; f.scrollLeft = 0;
  const out = []; for (const e of f.querySelectorAll('.mf-zl, .gt .sp-card, .gt-line, .gt-agree, .gt-more, .mf-zone')) { const r = e.getBoundingClientRect();
    if (r.width && r.height && !(r.top >= fr.top - 0.5 && r.left >= fr.left - 0.5 && r.right <= fr.right + 0.5 && r.bottom <= fr.bottom + 0.5)) out.push([e.className.toString().slice(0, 30), Math.round(r.top), Math.round(r.bottom), Math.round(fr.top), Math.round(fr.bottom)]); }
  return out; }"""


@pytest.mark.parametrize("size", SIZES)
def test_a_red_gate_lies_upright_every_card_inside_its_field_with_the_decision_it_guards_face_up_and_no_ring(gui, size):
    server, _ = gui
    lay(server, "red-goal", red=True)
    spy = Spy(server)
    try:
        pg, seen = open_gate(gui, "red-goal", size)
        gate = pg.locator("[data-spread=gate]")
        assert gate.locator(".sp-ring, .sp-gate, .sp-gk").count() == 0 and pg.evaluate("document.querySelector('[data-spread=gate] svg circle') === null")
        assert gate.locator(".mf-zl").all_text_contents() == ["What its tests guard", "Yours"]
        d = gate.locator(".gt-guards .sp-card[data-cardkind=decision]")                             # §2 face up with the gate's no
        assert d.count() == 1 and "§2" in d.inner_text() and "Second, the old card" in d.inner_text() and d.locator(".sp-chk.is-no").count() == 1
        assert ", a decision" in d.get_attribute("aria-label") and d.locator(".cards-c--tr .ork-sign").count() == 1
        part = gate.locator(".gt-guards .sp-card[data-cardkind=part]")                              # the test naming none: its file, in the code face
        assert part.count() == 1 and "tests/test_bare.py" in part.inner_text() and ", a part" in part.get_attribute("aria-label")
        assert "Plex Mono" in part.locator(".sp-card__name").evaluate("e => getComputedStyle(e).fontFamily")
        pile = gate.locator(".gt-agree")                                                            # the agreeing §M a pile by its thickness, never a number
        assert pile.count() == 1 and pile.locator(".sp-thick span").count() >= 1 and not any(ch.isdigit() for ch in pile.inner_text())
        line = gate.locator(".gt-line")
        assert "No total" in line.text_content() and line.locator(".cards-ct").count() == 1
        assert gate.locator(".gt-yours .sp-card[data-cardkind=goal]").count() == 1 and "red-goal" in gate.locator(".gt-yours").text_content().lower()
        top = lambda s: gate.locator(s).bounding_box()["y"]                                         # upright: guards, the line, Yours
        assert top(".gt-guards") < top(".gt-line") < top(".gt-yours")
        assert pg.evaluate(INSIDE) == [], pg.evaluate(INSIDE)
        hand = pg.locator(".frame-hand .mathand")                                                   # the ways lie in the hand
        assert hand.locator("[data-way=fix]").count() == 1 and hand.locator("[data-way=stale]").count() == 1
        assert "Fix it" in hand.locator("[data-way=fix]").inner_text() and "The test is out of date" in hand.locator("[data-way=stale]").inner_text()
        seal = gate.locator(".mf-seal")
        assert seal.get_attribute("aria-disabled") == "true" and "Send to" in seal.inner_text() and "2 checks disagree" in seal.inner_text()
        seal.click(force=True)
        pg.wait_for_timeout(300)
        assert spy.log == [] and not seen
        pg.close()
    finally:
        spy.close()


@pytest.mark.parametrize("size", SIZES)
def test_with_every_check_agreeing_the_pile_lies_alone_and_the_seal_is_lit(gui, size):
    server, _ = gui
    lay(server, "green-goal", red=False)
    spy = Spy(server)
    try:
        pg, _seen = open_gate(gui, "green-goal", size)
        gate = pg.locator("[data-spread=gate]")
        assert gate.locator(".gt-agree").count() == 1 and gate.locator(".gt-guards .sp-card").count() == 0 and gate.locator(".sp-chk.is-no").count() == 0
        assert pg.locator(".frame-hand .mathand [data-way]").count() == 0
        seal = gate.locator(".mf-seal")
        assert seal.get_attribute("aria-disabled") is None and "Send to" in seal.inner_text()
        assert pg.evaluate(INSIDE) == []
        gate.locator(".gt-agree").click()                                                           # pressed, it spreads: §3 face up with its check
        assert gate.locator(".gt-spread .sp-card[data-cardkind=decision]").count() == 1 and gate.locator(".gt-spread .sp-chk:not(.is-no)").count() == 1
        seal.click()
        pg.wait_for_function("() => !document.querySelector('[data-spread=gate]')", timeout=WAIT_MS)
        assert spy.sent("ideas.goal_to_dev") == [{"idea": "green-goal", "sealed": True, "from": "mat"}]
        pg.close()
    finally:
        spy.close()


def test_a_gate_opened_by_its_hand_card_sends_its_move_from_the_hand(gui):
    server, _ = gui
    lay(server, "hand-goal", red=False)
    spy = Spy(server)
    try:
        pg, _seen = open_gate(gui, "hand-goal")
        pg.evaluate("() => import('/static/js/cards/spreads/open.js').then((m) => { m.openSpread({ kind: 'gate', slug: 'hand-goal', opened: 'hand' }); })")
        pg.wait_for_selector("[data-spread=gate] .gt[data-way=dev]", timeout=WAIT_MS)
        pg.locator("[data-spread=gate] .mf-seal").click()
        pg.wait_for_function("() => !document.querySelector('[data-spread=gate]')", timeout=WAIT_MS)
        assert spy.sent("ideas.goal_to_dev") == [{"idea": "hand-goal", "sealed": True, "from": "hand"}]
        pg.close()
    finally:
        spy.close()


def test_fix_it_on_an_unmerged_goal_runs_its_stage_again_only_on_the_seal_with_its_cost_said(gui):
    server, _ = gui
    lay(server, "stage-goal", red=True)
    spy = Spy(server)
    try:
        pg, _seen = open_gate(gui, "stage-goal")
        fix = pg.locator(".frame-hand .mathand [data-way=fix]")
        assert "its stage again" in fix.inner_text()
        fix.click()
        pg.wait_for_timeout(300)
        assert spy.log == []                                                                        # a pass is never one press
        seal = pg.locator("[data-spread=gate] .mf-seal")
        assert "Fix it" in seal.inner_text() and "A paid pass" in seal.inner_text() and seal.get_attribute("aria-disabled") is None
        seal.click()
        pg.wait_for_function("() => !document.querySelector('[data-spread=gate]')", timeout=WAIT_MS)
        assert spy.sent("ideas.gate_fix_stage") == [{"idea": "stage-goal", "sealed": True, "from": "mat"}] and not spy.sent("ideas.gate_fix_goal")
        pg.close()
    finally:
        spy.close()


def test_fix_it_on_a_done_goal_makes_a_fix_goal_in_one_press_and_its_toast_offers_undo(gui):
    server, _ = gui
    lay(server, "done-goal", red=True, branch=False)
    spy = Spy(server)
    try:
        pg, _seen = open_gate(gui, "done-goal")
        assert pg.locator("[data-spread=gate] .gt[data-way=main]").count() == 1
        seal = pg.locator("[data-spread=gate] .mf-seal")
        assert "Merge into main" in seal.inner_text() and seal.get_attribute("aria-disabled") == "true"
        fix = pg.locator(".frame-hand .mathand [data-way=fix]")
        assert "new Fix goal" in fix.inner_text()
        fix.click()
        pg.wait_for_function("() => document.body.innerText.includes('Undo')", timeout=WAIT_MS)
        assert spy.sent("ideas.gate_fix_goal") == [{"idea": "done-goal", "from": "mat"}] and not spy.sent("ideas.gate_fix_stage")
        pg.get_by_role("button", name="Undo").click()
        pg.wait_for_timeout(300)
        assert spy.sent("ideas.undo") == [{"idea": "done-goal"}]
        pg.close()
    finally:
        spy.close()


def test_the_test_is_out_of_date_asks_tech_on_the_seal_with_its_cost_said_never_in_one_press(gui):
    server, _ = gui
    lay(server, "stale-goal", red=True)
    spy = Spy(server)
    try:
        pg, _seen = open_gate(gui, "stale-goal")
        way = pg.locator(".frame-hand .mathand [data-way=stale]")
        way.click()
        pg.wait_for_timeout(300)
        assert spy.log == []
        seal = pg.locator("[data-spread=gate] .mf-seal")
        pg.wait_for_function("() => /Ask Tech/.test(document.querySelector('[data-spread=gate] .mf-seal').innerText)", timeout=WAIT_MS)
        pg.wait_for_function("() => /A paid pass/.test(document.querySelector('[data-spread=gate] .mf-seal').innerText)", timeout=WAIT_MS)
        seal.click()
        for _ in range(60):
            if spy.sent("ideas.ask_leader"):
                break
            pg.wait_for_timeout(50)
        got = spy.sent("ideas.ask_leader")
        assert len(got) == 1 and got[0]["slug"] == "stale-goal" and got[0]["leader"] == "tech" and got[0]["sealed"] is True and got[0]["from"] == "mat"
        assert "tests/test_red.py::test_a" in got[0]["text"]
        pg.close()
    finally:
        spy.close()
