"""Goal "The battle and the gate", stage L (decisions §300.8, §303): the gate mat laid upright on the host's `ideas.gate_guards`, its ring gone, in a real browser on the `gui` fixture's Board
(no `?mock=1`), a red gate laid in its state as stage E keeps it: one failing test in a file naming §N, a failing file naming none, a passing file naming §M. The Fix it way's commands
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
    ideas.save_state(host.ideas.state_dir, slug, state="ready" if branch else "done")
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
    pg.goto(server.url + (hash_ or f"#mat=gate:{slug}"))
    pg.wait_for_selector("[data-spread=gate] .gt-line, [data-spread=gate] .gt-guards", timeout=WAIT_MS)
    pg.wait_for_selector("[data-spread=gate] .gt[data-way]:not([data-way=''])", timeout=WAIT_MS)
    return pg, seen


INSIDE = """() => { const f = document.querySelector('[data-spread=gate] .mf-field'), fr = f.getBoundingClientRect(); f.scrollTop = 0; f.scrollLeft = 0;
  const out = []; for (const e of f.querySelectorAll('.mf-zl, .gt .sp-card, .gt-line, .gt-agree, .gt-more, .mf-zone')) { const r = e.getBoundingClientRect();
    if (r.width && r.height && !(r.top >= fr.top - 0.5 && r.left >= fr.left - 0.5 && r.right <= fr.right + 0.5 && r.bottom <= fr.bottom + 0.5)) out.push([e.className.toString().slice(0, 30), Math.round(r.top), Math.round(r.bottom), Math.round(fr.top), Math.round(fr.bottom)]); }
  return out; }"""








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


