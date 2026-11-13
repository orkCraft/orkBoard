"""Spec 62 A (docs/specs/62-spec-after-start.md, Tests → A): what changed since the plan, the leader's plan change (the keeper's model call
stubbed), its being taken by the runner under its lock, kept, or dropped by itself, the stop, the events and the word."""
from __future__ import annotations

import datetime as dt
import json
import threading
import time

import pytest

from orkboard.core import idea_keeper
from orkboard.core.idea_keeper import IdeaKeeper, KeeperError
from orkboard.core.idea_runner import IdeaRunner, Run, RunnerError
from orkboard.realm import event_log, idea_change, idea_checks, idea_target, ideas
from orkboard.sources.limits import Limit

STEPS = (("propose a plan change", "revise"), ("turn it into a plan", "plan"), ("Rewrite only that section", "talk"))
CHECK = idea_checks.TAGS[0]                      # a check task's kind
OLD = "2026-10-23T10:00:00"                      # when a task started
NEW_PLAN = {"tasks": [{"id": "a", "title": "The table", "brief": "Add it", "tier": "warrior"}]}


class Model:
    """Answers by what it is asked (the step the prompt says); a list is a sequence (its last repeats); remembers every call."""

    def __init__(self, **answers) -> None:
        self.answers, self.asked, self.gate = answers, [], {}

    def __call__(self, tier, prompt, effort="", budget=None):
        step = next((s for k, s in STEPS if k in prompt), "?")
        self.asked.append({"step": step, "tier": tier, "prompt": prompt, "effort": effort, "budget": budget})
        if step in self.gate:
            self.gate[step].wait(5)
        got = self.answers.get(step, {})
        if isinstance(got, list):
            got = got.pop(0) if len(got) > 1 else got[0]
        if isinstance(got, Exception):
            raise got
        return (got if isinstance(got, str) else json.dumps(got)), 0.02, 1000, ""

    def of(self, step):
        return [a for a in self.asked if a["step"] == step]


@pytest.fixture
def keeper(fake_repo, tmp_path):
    root, state = tmp_path / "wiki", fake_repo / ".orkcraft"
    settings = {"target": "balance", "autostart": True, "night": "01:00-07:00"}
    k = IdeaKeeper(fake_repo, state, lambda: root, lambda: settings)
    k.root, k.state, k.settings_now, k.limits_now, k.repo = root, state, settings, [], fake_repo
    k.limits = lambda: k.limits_now
    k.goal = ideas.add_track(root, "Ship the table")
    return k


def _wait(k, slug):
    for _ in range(300):
        if not k.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _plan(keeper, slug, rows, passed=True, state="working", **more):
    """plan.json as the plan call and the runner leave it: `rows` are (id, state, after, kind?); a task that is not waiting, ready or held
    has started. Written as it is, past `save_plan`'s refusal of a passed plan."""
    tasks = []
    for tid, st, after, *kind in rows:
        t = idea_keeper._task(tid, f"Task {tid}", f"Do {tid}", kind[0] if kind else "code", "warrior", list(after))
        t.update(state=st, role="", **({"started": OLD} if st not in ("waiting", "ready", "held") else {}))
        tasks.append(t)
    data = {"idea": slug, "made_at": "2026-10-23T09:00:00", "passed_at": "2026-10-23T09:30:00" if passed else None,
            "passed_by": "person", "estimate": idea_keeper.estimate(tasks), "todos": [], "tasks": tasks, **more}
    ideas._write_json(ideas.state_folder(keeper.state, slug) / "plan.json", data)
    ideas.save_state(keeper.state, slug, state=state if passed else "plan")
    return data


def _idea(keeper, text="export csv", **kw):
    return ideas.add_idea(keeper.root, text, keeper.goal, keeper.state, **kw)


def _tasks(keeper, slug):
    return {t["id"]: t for t in ideas.plan(keeper.state, slug)["tasks"]}


def _events(keeper, event):
    return [r for r in event_log.read(keeper.repo) if r["event"] == event]


# -- §1: what changed since the plan ------------------------------------------------------------------------------


def test_a_talk_keeps_the_plan_sections_it_wrote_and_no_other(keeper):
    slug = _idea(keeper)
    _plan(keeper, slug, [("k1", "ready", [])], passed=False)
    keeper.call = model = Model(talk=[
        {"reply": "Out it is.", "sections": {"Out": "No export of images"}, "decisions": ["No images"]},
        {"reply": "Same.", "sections": {"Out": "No export of images"}},                            # the text is the same
        {"reply": "Why.", "sections": {"Why": "People ask for it"}},                                 # not a plan section
        {"reply": "Asked.", "sections": {"Open questions": "- Which delimiter?"}},
        {"reply": "Done when.", "sections": {"Done when": "- A file downloads"}},
        {"reply": "Gist.", "sections": {"Gist": "Export the table as csv"}},
        {"reply": "Out again.", "sections": {"Out": "No export of images or pdf"}}])             # once each, in PLAN_SECTIONS' order
    seen = []
    for section in ("Out", "Out", "Why", "Open questions", "Done when", "Gist", "Out"):
        keeper.say(slug, f"About {section}", section)
        _wait(keeper, slug)
        seen.append(ideas.state(keeper.state, slug)["changed"])
    assert seen == [["Out"], ["Out"], ["Out"], ["Out"], ["Done when", "Out"], ["Gist", "Done when", "Out"], ["Gist", "Done when", "Out"]]
    assert ideas.idea_page(keeper.root, slug).section("Why") == "People ask for it" and len(model.asked) == 7


def test_a_talk_while_a_change_waits_keeps_what_changed_and_the_change_stays(keeper):
    slug = _idea(keeper)
    _plan(keeper, slug, [("k1", "merged", []), ("k2", "ready", ["k1"])])
    idea_change.mark(keeper.state, slug, ["Gist"])
    idea_change.write(keeper.state, slug, {"why": "w", "change": [{"id": "k2", "title": "Two"}], "drop": [], "add": [], "changed": ["Gist"],
                                           "estimate": {"usd_low": 0, "usd_high": 0}})
    keeper.call = Model(talk={"reply": "Out.", "sections": {"Out": "No export of images"}})
    keeper.say(slug, "No images", "Out")
    _wait(keeper, slug)
    assert ideas.state(keeper.state, slug)["changed"] == ["Gist", "Out"] and idea_change.read(keeper.state, slug)["change"][0]["id"] == "k2"
    assert ideas.state(keeper.state, slug)["state"] == "working"                       # the talk does not move the goal


def test_a_plan_made_clears_what_changed_and_the_change_that_waited(keeper):
    slug = _idea(keeper)
    _plan(keeper, slug, [("k1", "ready", [])], passed=False, state="plan")
    idea_change.set_section(keeper.root, keeper.state, slug, "Out", "No images")
    idea_change.write(keeper.state, slug, {"why": "x", "change": [], "drop": [], "add": [], "changed": ["Out"], "estimate": {"usd_low": 0, "usd_high": 0}})
    assert ideas.state(keeper.state, slug)["changed"] == ["Out"]
    keeper.call = Model(plan=NEW_PLAN)
    keeper.plan(slug)                                              # Re-plan, before the start
    _wait(keeper, slug)
    assert ideas.state(keeper.state, slug)["changed"] == [] and idea_change.read(keeper.state, slug) is None
    assert [t["id"] for t in ideas.plan(keeper.state, slug)["tasks"]] == ["k1"]


# -- §2: Re-plan what is left ------------------------------------------------------------------------------------

def test_re_plan_what_is_left_refuses_in_words(keeper):
    keeper.call = Model(revise={})
    with pytest.raises(KeeperError, match="gone"):
        keeper.revise("nothing")
    slug = _idea(keeper)
    with pytest.raises(KeeperError, match="This goal has no plan yet"):
        keeper.revise(slug)
    _plan(keeper, slug, [("k1", "ready", [])], passed=False, state="plan")
    with pytest.raises(KeeperError, match="Its plan is not started: Re-plan it"):
        keeper.revise(slug)
    _plan(keeper, slug, [("k1", "merged", [])], state="done")
    with pytest.raises(KeeperError, match="This goal is done"):
        keeper.revise(slug)
    _plan(keeper, slug, [("k1", "merged", []), ("k2", "ready", ["k1"])])
    keeper.demo = True
    with pytest.raises(KeeperError, match="demo"):
        keeper.revise(slug)
    keeper.demo, keeper.budget_ok = False, lambda: False
    with pytest.raises(KeeperError, match="spend limit"):
        keeper.revise(slug)
    keeper.budget_ok = lambda: True
    reset = dt.datetime.now() + dt.timedelta(hours=1)
    keeper.limits_now = [Limit("claude", "", "session", 0.01, reset)]
    with pytest.raises(KeeperError, match="spent"):
        keeper.revise(slug)
    keeper.limits_now = []
    assert keeper.call.asked == [] and ideas.state(keeper.state, slug)["state"] == "working"
    keeper.call.gate["revise"] = release = threading.Event()
    keeper.revise(slug)
    assert keeper.busy(slug) == "planning" and ideas.state(keeper.state, slug)["state"] == "working"      # busy as Re-plan; the state stays
    with pytest.raises(KeeperError, match="The keeper is busy with this goal: a moment"):
        keeper.revise(slug)
    release.set()
    _wait(keeper, slug)


def test_the_call_is_made_on_the_plan_step_and_the_plan_change_is_saved_beside_the_plan(keeper):
    slug = _idea(keeper)
    plan = _plan(keeper, slug, [("k1", "merged", []), ("k2", "running", ["k1"]), ("k3", "ready", ["k1"]), ("k4", "waiting", ["k3"]),
                                ("k5", "waiting", ["k1", "k2", "k3", "k4"], CHECK)])
    before = json.dumps(ideas.plan(keeper.state, slug), sort_keys=True)
    idea_change.mark(keeper.state, slug, ["Out"])
    keeper.call = model = Model(revise={
        "why": "  The export is csv only now.\n", "drop": ["k4"],
        "change": [{"id": "k3", "title": "Write the csv", "short": "Csv writer", "brief": "Write rows as csv.", "kind": "tests", "tier": "laborer", "after": ["k2"]}],
        "add": [{"key": "n1", "title": "Stream rows", "brief": "Stream big files", "kind": "code", "tier": "elder", "after": ["k3"]}]})
    keeper.revise(slug)
    _wait(keeper, slug)
    (call,) = model.of("revise")
    assert (call["tier"], call["effort"], call["budget"]) == (*idea_target.pick("plan", "balance"), idea_target.budget("plan", "balance"))
    saved = idea_change.read(keeper.state, slug)
    assert json.dumps(ideas.plan(keeper.state, slug), sort_keys=True) == before          # nothing is applied, no task touched
    assert set(saved) == {"made_at", "why", "changed", "change", "drop", "add", "estimate"}
    assert saved["why"] == "The export is csv only now." and saved["changed"] == ["Out"] and saved["drop"] == ["k4"]
    assert saved["change"] == [{"id": "k3", "title": "Write the csv", "short": "Csv writer", "brief": "Write rows as csv.", "kind": "tests",
                                "tier": "laborer", "after": ["k2"], "role": ""}]
    assert saved["add"] == [{"key": "n1", "title": "Stream rows", "short": "Stream rows", "brief": "Stream big files", "kind": "code",
                             "tier": "elder", "after": ["k3"], "role": ""}]
    assert ideas.state(keeper.state, slug)["state"] == "working" and ideas.state(keeper.state, slug)["error"] == ""
    assert saved["made_at"] and idea_change.summary(saved, ideas.plan(keeper.state, slug)) == {
        "made_at": saved["made_at"], "why": saved["why"], "added": 1, "changed": 1, "dropped": 1, "usd_low": saved["estimate"]["usd_low"],
        "usd_high": saved["estimate"]["usd_high"], "rows": [{"op": "add", "id": "", "title": "Stream rows"},
                                                           {"op": "change", "id": "k3", "title": "Write the csv"},
                                                           {"op": "drop", "id": "k4", "title": "Task k4"}]}
    keeper.call = Model(revise={"why": "Again", "change": [], "drop": [], "add": []})
    keeper.revise(slug)                                          # a newer one replaces it
    _wait(keeper, slug)
    again = idea_change.read(keeper.state, slug)
    assert again["why"] == "Again" and again["change"] == [] and again["drop"] == [] and again["add"] == [] and again["estimate"] == {"usd_low": 0.0, "usd_high": 0.0}
    assert idea_change.text_of(idea_change.summary(again, ideas.plan(keeper.state, slug))) == "The plan stays as it is"


def test_an_answer_that_changes_a_started_task_names_an_unknown_id_or_closes_a_cycle_is_cut(keeper):
    slug = _idea(keeper)
    plan = _plan(keeper, slug, [("k1", "merged", []), ("k2", "running", ["k1"]), ("k3", "waiting", ["k1"]), ("k4", "waiting", ["k3"]),
                                ("k5", "waiting", ["k4"]), ("k6", "waiting", ["k1", "k2", "k3", "k4", "k5"], CHECK)])
    got = idea_revise_clean(plan, {
        "why": "x", "drop": ["k1", "k2", "k9", "k5", "k6", "k5"],
        "change": [{"id": "k2", "title": "Started"}, {"id": "k9", "title": "Unknown"}, {"id": "k6", "title": "A check"},
                   {"id": "k1", "title": "Merged"}, {"id": "k4", "title": "Task k4"},                      # nothing changes: left out
                   {"id": "k3", "title": "Third", "after": ["k5", "k1", "zzz", "k3", "k6"]}, {"id": "k3", "title": "Twice"}],
        "add": [{"key": "x", "title": "First", "brief": "b", "after": ["k3", "nothing", "x2", "k5"]},
                {"key": "x2", "title": "Second", "brief": "b", "after": ["x", "k4"], "kind": CHECK, "tier": "god"},
                {"title": "No brief"}, {"brief": "No title"}, "no", {"title": "Third", "brief": "b", "after": ["x"]}]})
    assert got["drop"] == ["k5"]                                    # the merged, the started, the unknown and the check stay; once
    assert [c["id"] for c in got["change"]] == ["k3"]
    assert got["change"][0]["after"] == ["k1"]                      # k5 waits for k3 (a cycle), zzz is nothing, k3 itself, k6 a check
    assert got["change"][0]["title"] == "Third" and got["change"][0]["brief"] == "Do k3" and got["change"][0]["kind"] == "code"
    first, second, third = got["add"]
    assert (first["key"], second["key"], third["key"]) == ("n1", "n2", "n3")
    assert first["after"] == ["k3", "n2"] and second["after"] == ["k4"]                  # n2 waits for n1 would close a cycle; k5 is dropped
    assert second["kind"] == "code" and second["tier"] == "warrior"                    # a check's tag and an unknown tier give way
    assert third["after"] == ["n1"] and len(got["add"]) == 3


def idea_revise_clean(plan, answer):
    from orkboard.core import idea_revise
    return idea_revise.clean_change(plan, answer)


def test_a_failed_call_is_the_goals_error_and_saves_nothing(keeper):
    slug = _idea(keeper)
    _plan(keeper, slug, [("k1", "merged", []), ("k2", "ready", ["k1"])])
    keeper.call = Model(revise=RuntimeError("claude: not logged in"))
    keeper.revise(slug)
    _wait(keeper, slug)
    st = ideas.state(keeper.state, slug)
    assert st["state"] == "working" and st["error"].startswith("No plan change: ") and "not logged in" in st["error"]
    assert idea_change.read(keeper.state, slug) is None and _events(keeper, event_log.PLAN_REVISED) == []
    keeper.call = Model(revise="no json at all")
    keeper.revise(slug)
    _wait(keeper, slug)
    assert "JSON" in ideas.state(keeper.state, slug)["error"] and idea_change.read(keeper.state, slug) is None
    keeper.call = Model(revise={"why": "fine", "change": [], "drop": [], "add": []})
    keeper.revise(slug)
    _wait(keeper, slug)
    assert ideas.state(keeper.state, slug)["error"] == "" and idea_change.read(keeper.state, slug)["why"] == "fine"


def test_plan_revised_carries_the_sections_the_counts_the_price_and_the_calls_measure(keeper):
    slug = _idea(keeper)
    _plan(keeper, slug, [("k1", "merged", []), ("k2", "ready", ["k1"]), ("k3", "waiting", ["k2"])])
    idea_change.mark(keeper.state, slug, ["Done when", "Gist"])
    keeper.call = Model(revise={"why": "w", "drop": ["k3"], "add": [{"title": "New", "brief": "b"}], "change": [{"id": "k2", "title": "Second"}]})
    keeper.revise(slug)
    _wait(keeper, slug)
    (row,) = _events(keeper, event_log.PLAN_REVISED)
    saved = idea_change.read(keeper.state, slug)
    assert row["idea"] == slug and row["changed"] == ["Gist", "Done when"] and (row["added"], row["changed_n"], row["dropped"]) == (1, 1, 1)
    assert (row["usd_low"], row["usd_high"]) == (saved["estimate"]["usd_low"], saved["estimate"]["usd_high"])
    assert row["step"] == "plan" and row["prompt_chars"] > 100 and row["cost"] == 0.02 and row["tokens"]["total"] == 1000


# -- the file, its summary and its words ---------------------------------------------------------------------------


# -- §3.2: taken by the runner, under its lock ----------------------------------------------------------------------

@pytest.fixture
def runner(fake_repo):
    r = IdeaRunner(fake_repo, fake_repo / ".orkcraft", {"ideas": {"max_parallel": 4}}, None, limits=lambda: [], events=False)
    r.launched = []

    def launch(slug, task):                                       # no work is really done
        task.update(state="running", started=OLD)
        r._runs[(slug, task["id"])] = Run(threading.current_thread(), threading.Event())
        r.launched.append(task["id"])
    r._launch = launch
    return r


def _change(**more):
    return {"made_at": "2026-10-23T11:00:00", "why": "w", "changed": [], "estimate": {"usd_low": 0, "usd_high": 0},
            "change": [], "drop": [], "add": [], **more}


def _row(tid, **more):
    return {"id": tid, "title": f"New {tid}", "short": f"New {tid}", "brief": f"Brief {tid}", "kind": "docs", "tier": "laborer", "after": [], "role": "", **more}


def _add(key, **more):
    return {"key": key, "title": f"Added {key}", "short": f"Add {key}", "brief": f"Brief {key}", "kind": "code", "tier": "elder", "after": [], "role": "", **more}


def test_taking_a_plan_change_drops_changes_and_adds_under_the_lock(keeper, runner):
    slug = _idea(keeper)
    plan = _plan(keeper, slug, [("k1", "merged", []), ("k2", "running", ["k1"]), ("k3", "ready", ["k1"]), ("k4", "waiting", ["k3"]),
                                ("k5", "waiting", ["k3", "k4"]), ("k6", "waiting", ["k1", "k2", "k3", "k4", "k5"], CHECK)],
                 todos=[{"id": "t1", "title": "A key", "kind": "confirm", "for": ["k5"], "done": False}], extra="kept")
    ideas._write_json(ideas.state_folder(keeper.state, slug) / "plan.json", {**plan, "tasks": [{**t, "branch": f"idea/{slug}/{t['id']}", "note": "n"}
                                                                                              for t in plan["tasks"]]})
    before = {t["id"]: dict(t) for t in ideas.plan(keeper.state, slug)["tasks"]}
    got = runner.revise_tasks(slug, _change(
        drop=["k4", "k2"], change=[_row("k3", after=["k2", "n1"], role="grunt"), _row("k2"), _row("k9")],
        add=[_add("n1", after=["k3", "k1", "k4"]), _add("n2", after=["n1", "k5", "zzz"], role="grunt")]))
    after = _tasks(keeper, slug)
    assert got == {"added": 2, "changed": 1, "dropped": 1, "left": ["Task k2"]}      # k2 started meanwhile; k9 is gone: neither is counted
    assert list(after) == ["k1", "k2", "k3", "k5", "k6", "k7", "k8"]
    assert after["k2"] == before["k2"]                                               # at work: as it is
    k3 = after["k3"]
    assert (k3["title"], k3["short"], k3["brief"], k3["kind"], k3["tier"], k3["role"]) == ("New k3", "New k3", "Brief k3", "docs", "laborer", "grunt")
    assert k3["after"] == ["k2", "k7"]                                               # n1 (k7) was named by the change first: it cannot wait for k3 as well
    assert k3["id"] == "k3" and k3["branch"] == before["k3"]["branch"] and k3["note"] == "n" and k3["started"] == ""
    assert k3["state"] == "waiting"                                                  # it was ready; now it waits for k2, not merged
    assert after["k5"]["after"] == ["k3"]                                            # out of the others' after, as skip_task does
    k7, k8 = after["k7"], after["k8"]
    assert (k7["state"], k7["after"], k7["title"], k7["kind"], k7["tier"], k7["role"], k7["short"]) == ("waiting", ["k1"], "Added n1", "code", "elder", "", "Add n1")
    assert k8["after"] == ["k7", "k5"] and k8["role"] == "grunt" and k7["brief"] == "Brief n1" and k7["branch"] == "" and k7["cost"] is None
    assert after["k6"]["after"] == ["k1", "k2", "k3", "k5", "k7", "k8"]               # the check task waits for the new tasks too
    new = ideas.plan(keeper.state, slug)
    assert new["passed_at"] == plan["passed_at"] and new["passed_by"] == "person" and new["extra"] == "kept" and new["todos"] == plan["todos"]
    assert new["estimate"]["tasks"] == 7 and new["estimate"]["usd_low"] > plan["estimate"]["usd_low"]      # made again from its tasks
    assert ideas.state(keeper.state, slug)["state"] == "working"


def test_an_added_task_never_takes_an_id_used_before(keeper, runner):
    slug = _idea(keeper)
    _plan(keeper, slug, [("k1", "merged", []), ("k2", "ready", ["k1"]), ("k3", "waiting", ["k1"]), ("k4", "waiting", ["k1"])],
          todos=[{"id": "t1", "title": "Key", "kind": "confirm", "for": ["k6"], "done": False}])
    runner.skip_task(slug, "k3")                                                      # a gap is not filled
    (ideas.state_folder(keeper.state, slug) / "k7.log").write_text("a task that ran\n")
    runner.revise_tasks(slug, _change(add=[_add("n1"), _add("n2")]))
    assert list(_tasks(keeper, slug)) == ["k1", "k2", "k4", "k8", "k9"]               # past k4, the to-do's k6 and the log's k7
    runner.skip_task(slug, "k9")
    runner.revise_tasks(slug, _change(add=[_add("n1")]))
    assert len(_tasks(keeper, slug)) == 5 and not set(_tasks(keeper, slug)) & {"k3", "k6", "k7"}       # a skipped task's id is not one that was used


def test_a_task_that_started_meanwhile_is_left_and_a_change_of_only_such_tasks_changes_nothing(keeper, runner):
    slug = _idea(keeper)
    _plan(keeper, slug, [("k1", "running", []), ("k2", "review", ["k1"]), ("k3", "ready", ["k1"]), ("k4", "waiting", [])])
    ideas.edit_plan(keeper.state, slug, lambda p: p["tasks"][2].update(note="stopped by you", started=OLD))      # stopped on its own: it ran
    before = (ideas.state_folder(keeper.state, slug) / "plan.json").read_text()
    got = runner.revise_tasks(slug, _change(drop=["k1"], change=[_row("k2"), _row("k3")]))
    assert got == {"added": 0, "changed": 0, "dropped": 0, "left": ["Task k1", "Task k2", "Task k3"]}
    assert (ideas.state_folder(keeper.state, slug) / "plan.json").read_text() == before
    with pytest.raises(RunnerError, match="no plan"):
        runner.revise_tasks("nothing", _change())


