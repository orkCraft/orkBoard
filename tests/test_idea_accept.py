"""Spec 152 B (docs/specs/152-a-leader-leads-and-accepts.md B; decisions §256.3, §257.5): a step accepted by its leader. After a step's tasks land, its leader looks at the whole of it against its
section (`accept_step`, one call a step): accepted, back (a fix task for each thing, twice at most, then findings) or a line it *cannot see* (a finding, never accepted in silence); the next step and the
goal's end wait for it. Through the host, the keeper's call stubbed (as test_idea_steps.py's) and the runner's sessions not spawned; `accepts` asks for the real acceptance (tests/conftest.py)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from threading import Event

import pytest

from orkboard.realm import event_log, findings, goal_team, idea_route, idea_spend, idea_target, ideas, journals, task_made
from tests.test_idea_sections import _confirmed, host, model, parties, section  # noqa: F401  (the fixtures of the sections' tests)

pytestmark = pytest.mark.accepts

OK = {"verdict": "accepted", "done_when": [{"n": 1, "met": True, "why": "it is so"}], "back": [], "learned": ["A theme is one file"]}
BACK = {"verdict": "back", "done_when": [{"n": 1, "met": False, "why": "not saved"}],
        "back": [{"what": "The setting is not saved", "where": "src/theme", "task": "k1", "done_when": 1}], "learned": []}


def _plan(row):
    """The plan's answer: its one task proves every Done when line of its section (spec 153 C), so no line is left unclaimed but where a test says so."""
    text = " ".join(row["prompt"].split())
    if "step 2 of 2" in text:
        return {"tasks": [{"id": "a", "title": "Build the setting", "brief": "Build it", "kind": "code", "tier": "warrior", "proves": [1, 2, 3, 4, 5]}]}
    return {"tasks": [{"id": "a", "title": "Make the settings screen", "brief": "Make it", "kind": "design", "tier": "elder", "proves": [1, 2, 3, 4, 5]}]}


@pytest.fixture
def work(host, parties, model):                                                  # noqa: F811
    return _work(host, parties, model)


def _work(host, parties, model, plan=None):
    """A two-step goal (Product, then Tech) planned and started, its runner spawning nothing: `work.merge(*ids)` as a session that landed; `work.look()` as the clock has the leader accept."""
    model.said[("plan", "")] = plan or _plan
    model.said[("accept_step", "")] = OK
    slug = _confirmed(host, parties, model, ("product", "tech"))
    runner = host.ideas.runner(need=True)
    spawned = []

    def spawn(slug_, tid, cancel, again):
        spawned.append((slug_, tid))
        runner._runs[(slug_, tid)] = type("Run", (), {"thread": None, "cancel": Event(), "why": "", "role": ""})()

    runner._spawn = spawn

    class Work:
        clock = 1000.0
    w = Work()
    w.host, w.slug, w.parties, w.model, w.runner, w.spawned = host, slug, parties, model, runner, spawned
    w.merge = lambda *ids: [(runner._runs.pop((slug, i), None), runner._set_task(slug, i, state="merged", commit="c" * 40, subjects=[f"{i} landed"], finished="x")) for i in ids]
    w.plan = lambda: ideas.plan(host.ideas.state_dir, slug)
    w.tasks = lambda: {t["id"]: t for t in w.plan()["tasks"]}
    w.state = lambda: ideas.state(host.ideas.state_dir, slug)["state"]
    w.until = lambda: [time.sleep(0.01) for _ in range(1500) if host.ideas.keeper.busy(slug)]

    def tick():
        w.clock += 100
        began = host.ideas.keeper.tick(w.clock)
        w.until()
        return began
    w.tick = tick
    host.command("ideas.start", {"slug": slug})
    return w


def _kinds(w, party):
    return [e["kind"] for e in journals.of_goal(w.host.ideas.state_dir, party, w.slug)]


# -- the answer, strictly ----------------------------------------------------------------------------------------------------------------

# -- when, and what waits ----------------------------------------------------------------------------------------------------------------

def test_a_step_is_due_when_its_tasks_are_in_and_not_accepted_and_the_next_step_and_the_goals_end_wait_for_it(work):
    slug, p = work.slug, work.parties
    assert work.state() == "working" and not idea_route.due(work.plan())
    work.merge("k1")
    work.runner.tick()
    assert idea_route.due(work.plan()) and idea_route.next_step(work.plan()) is None and idea_route.steps_left(work.plan())
    assert work.state() == "working" and slug in work.runner._active                       # held, as one with a step left
    assert work.tick() is True                                                             # the clock begins the acceptance before the next step's plan
    assert [c["party"] for c in work.model.steps("accept_step")] == [""] and len(work.model.steps("accept_step")) == 1
    assert list(work.tasks()) == ["k1"] and idea_route.accepted(work.plan(), 1) and not idea_route.due(work.plan())
    assert work.plan()["accepts"]["1"]["verdict"] == "accepted" and work.plan()["accepts"]["1"]["round"] == 1
    assert work.tick() is True and list(work.tasks()) == ["k1", "k2"]                       # then the next step is planned
    work.merge("k2")
    work.runner.tick()
    assert work.state() == "working" and idea_route.due(work.plan()) and slug in work.runner._active      # the last step lands: the goal does not end
    work.tick()
    work.runner.tick()
    assert work.state() == "done" and slug not in work.runner._active
    assert work.model.steps("accept_step") and len(work.model.steps("accept_step")) == 2 and _kinds(work, p["product"]).count("accepted") == 1


# -- accepted: the journal, the event, the cost --------------------------------------------------------------------------------------------

def test_an_accepted_step_is_the_leaders_journal_and_an_event_and_its_call_is_the_leaders_own_on_the_veteran_tier(work):
    h, slug, p = work.host, work.slug, work.parties
    work.merge("k1")
    work.runner.tick()
    work.tick()
    entries = journals.of_goal(h.ideas.state_dir, p["product"], slug)
    acc = [e for e in entries if e["kind"] == "accepted"]
    assert len(acc) == 1 and "You accepted Product's step of" in acc[0]["text"] and "1 of 1 Done when met" in acc[0]["text"]
    assert [e["text"] for e in entries if e["kind"] == "learned"] == ["A theme is one file"]
    call = work.model.steps("accept_step")[0]
    assert call["tools"] is True and idea_target.tier_of(call["tier"]) == "elder" and call["prompt"].startswith("You are Product manager, the leader of this goal's party")
    assert idea_target.MATRIX["accept_step"] == {"thrift": ("elder", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")}
    assert idea_target.READS["accept_step"] == 4 and idea_target.CONTEXT["accept_step"] == 14_000 and idea_target.CAPS["accept_step"] == 0.30
    assert idea_spend.STEP_STAGE["accept_step"] == "work"
    ev = [e for e in event_log.read(Path(h.repo_root)) if e["event"] == event_log.STEP_ACCEPTED]
    assert len(ev) == 1 and ev[0]["idea"] == slug and ev[0]["step"] == 1 and ev[0]["party"] == p["product"] and ev[0]["verdict"] == "accepted" and ev[0]["round"] == 1
    assert ev[0]["back"] == 0 and ev[0]["failed"] is False and "Players" not in json.dumps(ev) and event_log.STEP_ACCEPTED in event_log.EVENTS
    assert any(r["step"] == "accept_step" and r["role"] for r in idea_spend.read(h.ideas.state_dir / "ideas" / slug / idea_spend.FILE))      # in the goal's own ledger


# -- back -----------------------------------------------------------------------------------------------------------------------------------

def test_a_step_sent_back_gets_a_fix_task_for_each_thing_stamped_into_the_step_and_is_due_again_in_round_two(work):
    h, slug, p = work.host, work.slug, work.parties
    work.model.said[("accept_step", "")] = lambda row: BACK
    work.merge("k1")
    work.runner.tick()
    work.tick()
    t = work.tasks()
    assert list(t) == ["k1", "k2"] and t["k2"]["title"] == "Fix: The setting is not saved" and t["k2"]["step"] == 1 and t["k2"]["party"] == p["product"]
    assert t["k2"]["kind"] == "design" and t["k2"]["tier"] == "elder" and t["k2"]["craft"] == "product" and t["k2"].get("leader") == goal_team.leader_of(h.ideas.root(), p["product"])
    assert "The setting is not saved" in t["k2"]["brief"] and "Where: src/theme" in t["k2"]["brief"] and "Players can pick a theme" in t["k2"]["brief"] and t["k2"]["section"]
    assert t["k2"]["role"] and work.plan()["accepts"]["1"]["verdict"] == "back" and work.plan()["accepts"]["1"]["round"] == 1
    assert work.state() == "working" and not idea_route.due(work.plan()) and work.spawned[-1] == (slug, "k2")          # the fix runs as any task
    assert _kinds(work, p["product"]).count("sent_back") == 1 and "accepted" not in _kinds(work, p["product"])
    sent = next(e for e in journals.of_goal(h.ideas.state_dir, p["product"], slug) if e["kind"] == "sent_back")
    assert "You sent back 1 thing of Product's step of" in sent["text"]
    work.model.said[("accept_step", "")] = OK
    work.merge("k2")
    work.runner.tick()
    assert idea_route.due(work.plan()) and idea_route.next_step(work.plan()) is None                                   # due again
    work.tick()
    assert work.plan()["accepts"]["1"]["round"] == 2 and work.plan()["accepts"]["1"]["verdict"] == "accepted"
    assert "look number 2" in work.model.steps("accept_step")[1]["prompt"]
    work.tick()
    assert list(work.tasks())[-1] == "k3" and work.tasks()["k3"]["step"] == 2                                          # then the next step


# -- cannot see, a failed call, a stop ------------------------------------------------------------------------------------------------------

def test_a_stop_keeps_nothing_and_the_next_tick_begins_the_acceptance_again(work):
    h, slug = work.host, work.slug

    def stopped(row):
        raise InterruptedError("stopped")
    work.model.said[("accept_step", "")] = stopped
    work.merge("k1")
    work.runner.tick()
    work.tick()
    assert "accepts" not in work.plan() and findings.of_goal(h.ideas.state_dir, slug) == [] and idea_route.due(work.plan()) and not h.ideas.keeper.busy(slug)
    assert len(work.model.steps("accept_step")) == 1                                                                      # a stop is never tried again
    work.model.said[("accept_step", "")] = OK
    assert work.tick() is True and work.plan()["accepts"]["1"]["verdict"] == "accepted"


# -- the findings are in when the last step is -----------------------------------------------------------------------------------------------

# -- a Done when line says how it is proven (spec 152 F.4) --------------------------------------------------------------------------------

LINES = ["[test] A theme is saved", "[look] The settings screen is dark", "[person] The tone of the words is kind", "The theme loads fast"]
DIFF = (b"diff --git a/tests/test_theme.py b/tests/test_theme.py\nnew file mode 100644\n--- /dev/null\n+++ b/tests/test_theme.py\n@@ -0,0 +1,4 @@\n+import x\n"
        b"+def test_a_theme_is_saved():\n+    pass\n+async def test_it_loads():\n+    pass\ndiff --git a/src/theme.py b/src/theme.py\n--- a/src/theme.py\n+++ b/src/theme.py\n@@ -1 +1,2 @@\n+def theme(): pass\n"
        b"diff --git a/web/box.test.js b/web/box.test.js\nnew file mode 100644\n--- /dev/null\n+++ b/web/box.test.js\n@@ -0,0 +1 @@\n+it('x', () => {})\n")
ALL = {"verdict": "accepted", "done_when": [{"n": i, "met": True, "why": "yes"} for i in range(1, 5)], "back": [], "learned": []}


@pytest.fixture
def proofed(host, parties, model, monkeypatch):                                  # noqa: F811
    """`work`, with Product's section holding `LINES`; git answers `DIFF` for a diff and 3 files for a numstat."""
    model.said[("section_first", "")] = section("Product's why.", LINES, ["changed src/ui — the settings screen"])
    monkeypatch.setattr(task_made, "_git", lambda repo, *a: (b"3\t0\tsrc/theme.py\n" if "--numstat" in a else DIFF) if a and a[0] == "diff" else None)
    w = _work(host, parties, model)
    model.said[("accept_step", "")] = ALL
    return w


def _look(w, shot=False):
    if shot:
        folder = w.host.ideas.state_dir / "ideas" / w.slug / "picks" / "k1-shot-r1"
        folder.mkdir(parents=True)
        (folder / "shot.png").write_bytes(b"\x89PNG")
    w.merge("k1")
    w.runner._set_task(w.slug, "k1", tests={"passed": 5, "failed": 0, "skipped": 0}, **({"shot": {"id": "k1-shot-r1", "file": "shot.png"}} if shot else {}))
    w.runner.tick()
    w.tick()
    return w.model.steps("accept_step")[0]["prompt"]


def test_a_look_line_with_no_picture_is_unseen_by_code_with_a_finding_and_the_leaders_true_does_not_win(proofed):
    h, slug = proofed.host, proofed.slug
    prompt = _look(proofed)
    assert "- Done when 2 [look]: decided by code, unseen: no picture of the step was made (no preview, no Play). Do not judge it." in prompt
    done = {d["n"]: d["met"] for d in proofed.plan()["accepts"]["1"]["done_when"]}
    assert done == {1: True, 2: "unseen", 3: "unseen", 4: True}
    assert sorted(r["what"] for r in findings.of_goal(h.ideas.state_dir, slug)) == ["Nobody could look at: The settings screen is dark", "Only you can judge: The tone of the words is kind"]
    texts = [e["text"] for e in journals.of_goal(h.ideas.state_dir, proofed.parties["product"], slug) if e["kind"] == "accepted"]
    assert "2 of 4 Done when met" in texts[0]


# -- C: a base accepted early (spec 152 C) -----------------------------------------------------------------------------------------------------

def _t(tid, after=(), step=1, **more):
    return {"id": tid, "after": list(after), "step": step, "state": "waiting", **more}


def _fan(row):
    """Step one as a fan: k1 (proves line 1) is a base that k2 and k3 name in `after`."""
    if "step 2 of 2" in " ".join(row["prompt"].split()):
        return _plan(row)
    return {"tasks": [{"id": "a", "title": "Lay the theme store", "brief": "Lay it", "kind": "design", "tier": "elder", "proves": [1]},
                      {"id": "b", "title": "Draw the picker", "brief": "Draw it", "kind": "design", "tier": "elder", "after": ["a"], "proves": [2, 3]},
                      {"id": "c", "title": "Draw the preview", "brief": "Draw it", "kind": "design", "tier": "elder", "after": ["a"], "proves": [4, 5]}]}


@pytest.fixture
def fanned(host, parties, model):                                                # noqa: F811
    return _work(host, parties, model, _fan)


def _states(w):
    return {k: t["state"] for k, t in w.tasks().items()}


def test_a_task_waits_for_its_base_to_be_merged_and_accepted_and_for_nothing_else_a_chain_waits_for_the_merge_only():
    from orkboard.core.idea_plan import readiness
    plan = {"tasks": [_t("k1", state="merged"), _t("k2", ["k1"]), _t("k3", ["k1"])]}
    readiness(plan)
    assert [t["state"] for t in plan["tasks"]] == ["merged", "waiting", "waiting"]                          # merged is not enough
    plan["accepts"] = {"1:k1": {"verdict": "back"}}
    readiness(plan)
    assert plan["tasks"][1]["state"] == "waiting"
    for verdict in ("accepted", "gone_on"):
        plan["accepts"] = {"1:k1": {"verdict": verdict}}
        readiness(plan)
        assert [t["state"] for t in plan["tasks"]] == ["merged", "ready", "ready"]
    chain = {"tasks": [_t("k1", state="merged"), _t("k2", ["k1"]), _t("k3", ["k2"])]}
    readiness(chain)
    assert [t["state"] for t in chain["tasks"]] == ["merged", "ready", "waiting"]                           # no base: as before
    other = {"tasks": [_t("k1", state="merged"), _t("k2", state="ready"), _t("k3", ["k1"]), _t("k4", ["k1", "k2"]), _t("k5", ["k2"])], "accepts": {"1:k1": {"verdict": "accepted"}}}
    readiness(other)
    assert [t["state"] for t in other["tasks"]][2:] == ["ready", "waiting", "waiting"]                      # the dependant still waits for its other `after`


def test_a_base_sent_back_makes_its_dependants_wait_for_its_fixes_and_for_the_second_look(fanned):
    w = fanned
    w.model.said[("accept_step", "")] = BACK
    w.merge("k1")
    w.runner.tick()
    w.tick()
    t = w.tasks()
    assert w.plan()["accepts"]["1:k1"]["verdict"] == "back" and t["k4"]["fix_of"] == "k1" and t["k4"]["step"] == 1 and idea_route.bases(w.plan(), 1) == ["k1"]
    assert _states(w)["k2"] == "waiting" and _states(w)["k3"] == "waiting" and _states(w)["k4"] != "waiting"      # the fix runs; the dependants wait
    assert not idea_route.base_due(w.plan()) and w.tick() is False and len(w.model.steps("accept_step")) == 1      # not looked at again before the fix lands
    w.model.said[("accept_step", "")] = OK
    w.merge("k4")
    w.runner.tick()
    assert _states(w)["k2"] == "waiting" and idea_route.base_due(w.plan()) == ["k1"]                         # the fix is in: the base is looked at again, its dependants still wait
    w.tick()
    assert w.plan()["accepts"]["1:k1"]["round"] == 2 and w.plan()["accepts"]["1:k1"]["verdict"] == "accepted" and "Fix: The setting is not saved" in w.model.steps("accept_step")[1]["prompt"]
    w.runner.tick()
    assert _states(w)["k2"] != "waiting" and _states(w)["k3"] != "waiting"


# -- a step nobody looked at; a screen's line (spec 155 B) ---------------------------------------------------------------------------------


# -- a call that fails, the limit of the looks ---------------------------------------------------------------------------------------------

def test_a_call_that_fails_goes_on_with_one_finding_and_a_step_sent_back_twice_leaves_its_last_look_as_findings_and_goes_on(work):
    h, slug, p = work.host, work.slug, work.parties
    work.model.said[("accept_step", "")] = "no json at all"
    work.merge("k1")
    work.runner.tick()
    work.tick()
    rows = findings.of_goal(h.ideas.state_dir, slug)
    assert len(rows) == 1 and rows[0]["source"] == "accept" and "could not accept this step: its call failed" in rows[0]["what"]
    assert work.plan()["accepts"]["1"]["verdict"] == "gone_on" and not idea_route.due(work.plan()) and "accepted" not in _kinds(work, p["product"])
    work.model.said[("accept_step", "")] = lambda row: BACK                                   # the next step: sent back twice, then what is left is the goal's findings
    work.tick()
    work.merge("k2")
    work.runner.tick()
    work.tick()
    work.merge("k3")
    work.runner.tick()
    work.tick()
    work.merge("k4")
    work.runner.tick()
    work.tick()
    acc = work.plan()["accepts"]["2"]
    assert acc["round"] == 3 and acc["verdict"] == "gone_on" and idea_route.accepted(work.plan(), 2)
    left = [r for r in findings.of_goal(h.ideas.state_dir, slug) if r["what"] == "The setting is not saved"]
    assert len(left) == 1 and left[0]["source"] == "accept" and left[0]["status"] == "told"
