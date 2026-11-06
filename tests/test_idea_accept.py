"""Spec 152 B (docs/specs/152-a-leader-leads-and-accepts.md B; decisions §256.3, §257.5): a step accepted by its leader. After a step's tasks land, its leader looks at the whole of it against its
section (`accept_step`, one call a step): accepted, back (a fix task for each thing, twice at most, then findings) or a line it *cannot see* (a finding, never accepted in silence); the next step and the
goal's end wait for it. Through the host, the keeper's call stubbed (as test_idea_steps.py's) and the runner's sessions not spawned; `accepts` asks for the real acceptance (tests/conftest.py)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from threading import Event

import pytest

from orkboard.core import idea_accept
from orkboard.core.idea_accept import clean
from orkboard.realm import event_log, findings, goal_team, idea_pick, idea_route, idea_spend, idea_target, ideas, journals, task_made
from tests.test_idea_sections import _confirmed, host, model, parties, section  # noqa: F401  (the fixtures of the sections' tests)

pytestmark = pytest.mark.accepts

OK = {"verdict": "accepted", "done_when": [{"n": 1, "met": True, "why": "it is so"}], "back": [], "learned": ["A theme is one file"]}
BACK = {"verdict": "back", "done_when": [{"n": 1, "met": False, "why": "not saved"}],
        "back": [{"what": "The setting is not saved", "where": "src/theme", "task": "k1", "done_when": 1}], "learned": []}


def _plan(row):
    text = " ".join(row["prompt"].split())
    if "step 2 of 2" in text:
        return {"tasks": [{"id": "a", "title": "Build the setting", "brief": "Build it", "kind": "code", "tier": "warrior"}]}
    return {"tasks": [{"id": "a", "title": "Make the settings screen", "brief": "Make it", "kind": "design", "tier": "elder"}]}


@pytest.fixture
def work(host, parties, model):                                                  # noqa: F811
    return _work(host, parties, model)


def _work(host, parties, model):
    """A two-step goal (Product, then Tech) planned and started, its runner spawning nothing: `work.merge(*ids)` as a session that landed; `work.look()` as the clock has the leader accept."""
    model.said[("plan", "")] = _plan
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

def test_the_answer_is_cleaned_strictly_four_items_at_most_a_line_met_true_false_or_unseen_and_an_empty_back_is_accepted():
    ids = ["k1", "k2"]
    many = [{"what": f"thing {n}", "where": "x" * 400, "task": "k9" if n == 2 else "k1", "done_when": 7 if n == 1 else 2} for n in range(6)]
    got = clean({"verdict": "back", "done_when": [{"n": 1, "met": "unseen", "why": "no picture"}, {"n": 2, "met": "yes"}, {"n": 2, "met": True}, {"n": 9, "met": True}, {"n": "x"}, "junk"],
                 "back": [*many, {"what": ""}], "learned": ["a", "b", "c", 5, ""]}, ids, 2)
    assert got["verdict"] == "back" and len(got["back"]) == 4 and all(len(b["where"]) <= 200 for b in got["back"])
    assert [b["task"] for b in got["back"]] == ["k1", "k1", "", "k1"]                        # a task that is none of the step's is ""
    assert [b["done_when"] for b in got["back"]] == [2, 0, 2, 2]                           # a line that is none of the section's is 0
    assert [(d["n"], d["met"]) for d in got["done_when"]] == [(1, "unseen"), (2, False)] and got["learned"] == ["a", "b"]
    assert clean({"verdict": "back", "back": []}, ids, 1)["verdict"] == "accepted"
    assert clean({"verdict": "back", "back": [{"what": "x", "task": "k3"}]}, ids, 1)["back"][0]["task"] == ""
    assert clean({"verdict": "maybe"}, ids, 1) is None and clean("no", ids, 1) is None and clean({"done_when": []}, ids, 1) is None


# -- when, and what waits ----------------------------------------------------------------------------------------------------------------

def test_a_step_is_due_when_its_tasks_are_in_and_not_accepted_and_the_next_step_and_the_goals_end_wait_for_it(work):
    h, slug, p = work.host, work.slug, work.parties
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


def test_a_goal_of_before_with_one_step_and_no_route_is_accepted_the_same(host, parties, model):                # noqa: F811
    model.said[("plan", "")] = _plan
    model.said[("accept_step", "")] = OK
    slug = _confirmed(host, parties, model, ("tech",))
    runner = host.ideas.runner(need=True)
    runner._spawn = lambda *a: None
    assert "route" not in ideas.plan(host.ideas.state_dir, slug)
    host.command("ideas.start", {"slug": slug})
    for t in ideas.plan(host.ideas.state_dir, slug)["tasks"]:
        runner._runs.pop((slug, t["id"]), None)
        runner._set_task(slug, t["id"], state="merged", commit="c" * 40, subjects=["landed"], finished="x")
    runner.tick()
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "working" and idea_route.due(ideas.plan(host.ideas.state_dir, slug))
    assert host.ideas.keeper.tick(time.time() + 100) is True
    for _ in range(1500):
        if not host.ideas.keeper.busy(slug):
            break
        time.sleep(0.01)
    runner.tick()
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "done" and len(model.steps("accept_step")) == 1


def test_a_step_whose_tasks_were_all_dropped_landed_nothing_and_is_not_accepted(work):
    work.runner._runs.pop((work.slug, "k1"), None)
    work.runner._set_task(work.slug, "k1", state="dropped")
    assert not idea_route.due(work.plan()) and idea_route.accept_of(work.plan(), 1) == {}
    work.tick()
    assert work.model.steps("accept_step") == []


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


def test_the_call_is_given_the_section_the_promise_read_by_code_each_tasks_files_gate_and_picture_the_stance_and_no_other_partys_section(work, monkeypatch):
    h, slug, p = work.host, work.slug, work.parties
    state = h.ideas.state_dir
    shot = state / "ideas" / slug / "picks" / "k1-shot-r1"
    shot.mkdir(parents=True)
    (shot / "shot.png").write_bytes(b"\x89PNG")
    monkeypatch.setattr(task_made, "_git", lambda repo, *a: b"7\t2\tsrc/theme.py\n" if a and a[0] == "diff" else None)
    work.merge("k1")
    work.runner._set_task(slug, "k1", tests={"passed": 3, "failed": 1, "skipped": 0, "failing": ["tests/test_theme.py::test_saves"], "red_before": ["tests/test_old.py::test_x"]},
                          shot={"id": "k1-shot-r1", "file": "shot.png"})
    assert idea_pick.folder_of(state, slug, "k1-shot-r1") == shot
    work.runner.tick()
    work.tick()
    prompt = work.model.steps("accept_step")[0]["prompt"]
    assert "You lead Product. The tasks of your step have all landed" in prompt                                                      # the leader's voice first, then its task
    assert "Players can pick a theme" in prompt and "1. Players can pick a theme" in prompt and "Product's why." in prompt                     # its section, whole, its Done when numbered
    assert "The theme is one file" not in prompt and "Tech's why." not in prompt                                                          # no other party's part
    assert "What code read of the promise" in prompt and "Will be, changed src" in prompt and "Done when 1:" in prompt                       # judged by code
    assert "Make the settings screen" in prompt and "src/theme.py (+7 -2)" in prompt                                                      # the task, its files and their lines
    assert "gate: 3 passed, 1 failed" in prompt and "tests/test_theme.py::test_saves" in prompt and "red before it: tests/test_old.py::test_x" in prompt
    assert "k1-shot-r1" in prompt and "shot.png" in prompt                                                                                 # its picture
    assert "What you said of this goal in Talk" in prompt and "product stance" in prompt                                                   # the stance of Talk (the journal's `stance`)
    heads = ["Your section, whole:\n", "What code read of the promise:\n", "The tasks of your step:\n", "What you said of this goal in Talk:\n"]
    assert [prompt.index(x) for x in heads] == sorted(prompt.index(x) for x in heads)
    assert '"verdict": "accepted"' in prompt and '"unseen"' in prompt and "Never say true for a line you could not look at" in prompt


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


def test_after_the_second_back_what_is_left_is_the_goals_findings_told_and_the_step_goes_on(work):
    h, slug, p = work.host, work.slug, work.parties
    work.model.said[("accept_step", "")] = lambda row: BACK
    work.merge("k1")
    work.runner.tick()
    work.tick()
    work.merge("k2")
    work.runner.tick()
    work.tick()
    assert list(work.tasks()) == ["k1", "k2", "k3"] and work.plan()["accepts"]["1"]["round"] == 2 and work.plan()["accepts"]["1"]["verdict"] == "back"
    assert findings.of_goal(h.ideas.state_dir, slug) == []
    work.merge("k3")
    work.runner.tick()
    work.tick()
    acc = work.plan()["accepts"]["1"]
    assert acc["round"] == 3 and acc["verdict"] == "gone_on" and idea_route.accepted(work.plan(), 1) and not idea_route.due(work.plan())
    rows = findings.of_goal(h.ideas.state_dir, slug)
    assert len(rows) == 1 and rows[0]["source"] == "accept" and rows[0]["party"] == p["product"] and rows[0]["status"] == "told"
    assert rows[0]["what"] == "The setting is not saved" and rows[0]["shows"] == "src/theme" and rows[0]["promised"] == "Players can pick a theme"
    assert "last look" in work.model.steps("accept_step")[2]["prompt"] and len(work.tasks()) == 3                         # no fourth task: the step goes on
    assert "sent_back" in _kinds(work, p["product"]) and _kinds(work, p["product"]).count("sent_back") == 2
    work.tick()
    assert list(work.tasks())[-1] == "k4" and work.tasks()["k4"]["step"] == 2                                          # the next step's plan follows
    ev = [e for e in event_log.read(Path(h.repo_root)) if e["event"] == event_log.STEP_ACCEPTED]
    assert [(e["round"], e["verdict"]) for e in ev] == [(1, "back"), (2, "back"), (3, "gone_on")]


# -- cannot see, a failed call, a stop ------------------------------------------------------------------------------------------------------

def test_a_line_it_cannot_see_is_a_finding_whatever_the_verdict_and_never_accepted_in_silence(work):
    h, slug, p = work.host, work.slug, work.parties
    work.model.said[("accept_step", "")] = {"verdict": "accepted", "done_when": [{"n": 1, "met": "unseen", "why": "no picture was made"}], "back": [], "learned": []}
    work.merge("k1")
    work.runner.tick()
    work.tick()
    rows = findings.of_goal(h.ideas.state_dir, slug)
    assert len(rows) == 1 and rows[0]["source"] == "accept" and rows[0]["what"] == "Nobody could look at: Players can pick a theme" and rows[0]["status"] == "told"
    assert work.plan()["accepts"]["1"]["verdict"] == "accepted" and list(work.tasks()) == ["k1"]                          # it does not send the step back
    assert "0 of 1 Done when met" in next(e["text"] for e in journals.of_goal(h.ideas.state_dir, p["product"], slug) if e["kind"] == "accepted")


def test_a_call_that_fails_goes_on_with_one_finding_and_a_stop_keeps_nothing(work):
    h, slug, p = work.host, work.slug, work.parties
    work.model.said[("accept_step", "")] = "no json at all"
    work.merge("k1")
    work.runner.tick()
    work.tick()
    assert len(work.model.steps("accept_step")) == 2                                                                      # one more try
    rows = findings.of_goal(h.ideas.state_dir, slug)
    assert len(rows) == 1 and rows[0]["source"] == "accept" and "could not accept this step: its call failed" in rows[0]["what"]
    acc = work.plan()["accepts"]["1"]
    assert acc["verdict"] == "gone_on" and not idea_route.due(work.plan()) and "accepted" not in _kinds(work, p["product"])
    ev = [e for e in event_log.read(Path(h.repo_root)) if e["event"] == event_log.STEP_ACCEPTED]
    assert ev[-1]["failed"] is True and ev[-1]["verdict"] == "gone_on"


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

def test_a_goals_findings_are_ripe_only_when_its_last_step_is_accepted_or_gone_on(work):
    h, slug = work.host, work.slug
    work.merge("k1")
    work.runner.tick()
    work.tick()
    work.tick()
    work.merge("k2")
    work.runner.tick()
    findings.save_record(h.ideas.state_dir, slug, at=ideas._now())                                                       # the verdict was read
    assert idea_route.due(work.plan()) and findings.ripe(h.ideas.state_dir, slug) is False
    work.tick()
    assert findings.ripe(h.ideas.state_dir, slug) is True


def test_the_fix_tasks_are_appended_to_the_plan_here_when_the_host_wires_no_runner(work):
    h, slug, p = work.host, work.slug, work.parties
    h.ideas.keeper.fix_tasks = None
    work.model.said[("accept_step", "")] = lambda row: BACK
    work.merge("k1")
    work.runner.tick()
    work.tick()
    t = work.tasks()["k2"]
    assert t["title"] == "Fix: The setting is not saved" and t["step"] == 1 and t["party"] == p["product"] and t["state"] in ("waiting", "ready") and idea_accept.STAMPS


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


def test_tests_in_a_diff_are_named_by_function_and_a_new_test_file_with_none_by_its_path():
    assert idea_accept.tests_in_diff(DIFF.decode()) == ["tests/test_theme.py::test_a_theme_is_saved", "tests/test_theme.py::test_it_loads", "web/box.test.js"]
    assert idea_accept.tests_in_diff("") == [] and idea_accept.tests_in_diff("diff --git a/src/a.py b/src/a.py\n+++ b/src/a.py\n+def test_not_a_test_file(): pass\n") == ["src/a.py::test_not_a_test_file"]


def test_the_prompt_gives_each_done_when_line_its_proof_the_tests_the_step_added_and_the_pictures(proofed):
    prompt = _look(proofed, shot=True)
    assert "1. [test] A theme is saved" in prompt and "2. [look] The settings screen is dark" in prompt and "3. [person] The tone" in prompt and "4. The theme loads fast" in prompt
    assert "- Done when 1 [test]: proven by a test. gate: 5 passed, 0 failed over 1 task that ran tests; tests the step added: tests/test_theme.py::test_a_theme_is_saved, tests/test_theme.py::test_it_loads, web/box.test.js" in prompt
    assert "- Done when 2 [look]: proven by a picture. pictures: " in prompt and "k1-shot-r1" in prompt.split("Done when 2 [look]")[1].split("\n")[0]
    assert "- Done when 3 [person]: decided by code, unseen: only the person can judge it. Do not judge it." in prompt
    assert "- Done when 4: no mark, you judge it." in prompt


def test_a_look_line_with_a_picture_is_the_leaders_to_judge_and_a_person_line_is_unseen_with_a_finding_asking_the_person(proofed):
    h, slug = proofed.host, proofed.slug
    _look(proofed, shot=True)
    rows = findings.of_goal(h.ideas.state_dir, slug)
    assert [r["what"] for r in rows] == ["Only you can judge: The tone of the words is kind"] and rows[0]["source"] == "accept" and rows[0]["status"] == "told"
    done = {d["n"]: d["met"] for d in proofed.plan()["accepts"]["1"]["done_when"]}
    assert done == {1: True, 2: True, 3: "unseen", 4: True}                                  # the leader's `true` for the person's line does not win
    assert proofed.plan()["accepts"]["1"]["verdict"] == "accepted"


def test_a_look_line_with_no_picture_is_unseen_by_code_with_a_finding_and_the_leaders_true_does_not_win(proofed):
    h, slug = proofed.host, proofed.slug
    prompt = _look(proofed)
    assert "- Done when 2 [look]: decided by code, unseen: no picture of the step was made (no preview, no Play). Do not judge it." in prompt
    done = {d["n"]: d["met"] for d in proofed.plan()["accepts"]["1"]["done_when"]}
    assert done == {1: True, 2: "unseen", 3: "unseen", 4: True}
    assert sorted(r["what"] for r in findings.of_goal(h.ideas.state_dir, slug)) == ["Nobody could look at: The settings screen is dark", "Only you can judge: The tone of the words is kind"]
    texts = [e["text"] for e in journals.of_goal(h.ideas.state_dir, proofed.parties["product"], slug) if e["kind"] == "accepted"]
    assert "2 of 4 Done when met" in texts[0]


def test_nothing_is_sent_back_for_a_line_code_decided_and_a_line_the_leader_answers_missing_is_unseen_too(proofed):
    proofed.model.said[("accept_step", "")] = {"verdict": "back", "done_when": [{"n": 2, "met": False, "why": "dark?"}],
                                               "back": [{"what": "Make it dark", "where": "src/ui", "task": "k1", "done_when": 2}], "learned": []}
    _look(proofed)
    acc = proofed.plan()["accepts"]["1"]
    assert acc["verdict"] == "accepted" and acc["back"] == [] and list(proofed.tasks()) == ["k1"]
    assert {d["n"]: d["met"] for d in acc["done_when"]} == {2: "unseen", 3: "unseen"}


def test_an_unmarked_line_is_judged_as_before_and_a_section_with_no_mark_has_no_proof_part(work):
    work.merge("k1")
    work.runner.tick()
    work.tick()
    prompt = work.model.steps("accept_step")[0]["prompt"]
    assert "How each Done when line is proven" not in prompt and "No task claimed" not in prompt and "1. Players can pick a theme" in prompt
    assert work.plan()["accepts"]["1"]["done_when"] == [{"n": 1, "met": True, "why": "it is so"}] and findings.of_goal(work.host.ideas.state_dir, work.slug) == []


def test_the_lines_no_task_claimed_are_said_when_the_plan_names_them_and_nothing_when_it_does_not(proofed):
    ideas.edit_plan(proofed.host.ideas.state_dir, proofed.slug, lambda p: p.update(unclaimed=[4, 2, 9, 4, "x"]))
    prompt = _look(proofed, shot=True)
    assert "No task claimed: 2. The settings screen is dark; 4. The theme loads fast" in prompt and "9." not in prompt.split("No task claimed")[1].split("\n")[0]
