"""Spec 131 A.2–A.4 (docs/specs/131-a-leaders-slices-and-the-cascade.md; decisions §233) on the keeper: Confirm begins one cut; the call is given every party and the standing slices of the decisions changed;
`clean_cut`; a failed cut keeps nothing; the fold marks what it read; each reader of the table has the part right after the facts; a member's call has none; the decision's call has the touched leaders' slices.
The keeper's call is stubbed (`keeper.call`), as `tests/test_idea_journal.py` does; no real model.
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from orkboard.core import idea_keeper
from orkboard.core.idea_slices import SlicesMixin
from orkboard.gui.board_host import Orkboard
from orkboard.realm import event_log, goal_team, idea_questions, idea_target, ideas, library, project_facts, slices

MAP = "THE MAP TEXT\nsecond line of the map"
HEAD = "What you hold of the project's decisions (newest first; read the decision for the rest):\n"
LOG = """# Decisions

## 5. The screens hold ten seconds (1 May 2026, the person and Orkboard)

Why: People read slowly.

1. Screens hold 10 seconds.
2. No timers elsewhere.

## 6. The screens hold six seconds (2 May 2026, the person and Orkboard)

Changes: 5.

Why: People read faster than we thought.

1. Screens hold 6 seconds.
2. Art draws them quicker.
"""


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    assert isinstance(h.ideas.keeper, SlicesMixin) and idea_keeper.SlicesMixin is SlicesMixin
    (h.ideas.state_dir / "project.json").write_text('{"decisions": "docs/decisions.md"}', encoding="utf-8")
    h.ideas.keeper._map = lambda party: MAP
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


@pytest.fixture
def design(host):
    return _party(host, "Design", "product-designer", ["artist"], "design")


@pytest.fixture
def release(host):
    return _party(host, "Release", "release-manager", [], "engineering")


@pytest.fixture
def goal(host, tech):
    slug = ideas.add_idea(host.ideas.root(), "add a score board", tech, host.ideas.state_dir, "normal", "hold")
    ideas.save_state(host.ideas.state_dir, slug, marks=[{"map": "screens", "id": "step:1", "name": "Step 1"}])
    return slug


def _log(host, text=LOG):
    """The decisions file as dev holds it (the Board's tree: where the keeper reads it)."""
    host.ideas._decision_tree().edit_file("docs/decisions.md", lambda old: text, "decisions")


class Model:
    """The keeper's call stubbed: `said[step]` the JSON (or text, or a callable of the call) every call of that step gets, `calls` every call made, `live` the most calls at once."""

    def __init__(self, host):
        self.host, self.calls, self.said, self.lock, self.now, self.live, self.pause = host, [], {}, threading.Lock(), 0, 0, 0.0
        host.ideas.keeper.call = self

    def steps(self, step):
        return [c for c in self.calls if c["step"] == step]

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        row = {"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"], "key": getattr(k._tls, "key", ""),
               "as_role": getattr(k._tls, "as_role", "")}
        with self.lock:
            self.calls.append(row)
            self.now += 1
            self.live = max(self.live, self.now)
        try:
            time.sleep(self.pause)
            answer = self.said.get(row["step"], {})
            answer = answer(row) if callable(answer) else answer
            if isinstance(answer, Exception):
                raise answer
            return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""
        finally:
            with self.lock:
                self.now -= 1


@pytest.fixture
def model(host):
    return Model(host)


def _idle(host):
    k = host.ideas.keeper
    for _ in range(2000):
        if not k._busy and not k._sl()["queue"] and not k._sl()["running"]:
            return
        time.sleep(0.01)
    raise AssertionError(f"the keeper never finished: {k._busy}")


def _events(host, name=event_log.SLICES_CUT):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


CUT = {"slices": {"tech": {"says": "Your builds are quick.", "points": ["6.2"], "replaces": []}, "design": {"says": "Your screens hold 6 seconds.", "points": ["6.1"], "replaces": []}}}


# -- clean_cut ----------------------------------------------------------------------------------------------------------------------------

# -- the cut ------------------------------------------------------------------------------------------------------------------------------

def test_the_call_is_the_orkmasters_on_the_cheaper_tier_with_no_tools_and_is_given_the_entry_and_every_party(host, tech, design, release, model):
    _log(host)
    model.said["slice"] = CUT
    assert host.ideas.keeper.slices_cut(6) is True
    _idle(host)
    (call,) = model.calls
    assert call["step"] == "slice" and call["tools"] is False and call["as_role"] == "orkmaster"
    assert (call["tier"], call["effort"]) == idea_target.pick("slice", "balance") == idea_target.pick("decide", "balance") == ("warrior", "low")
    assert call["budget"] == idea_target.budget("slice", "balance")
    p = call["prompt"]
    assert "## 6. The screens hold six seconds" in p and "1. Screens hold 6 seconds." in p and "Read no file" in p and '{"slices": {' in p        # the entry as written
    for party, leader, craft in ((tech, "Architect", "tech"), (design, "Product designer", "design"), (release, "Release manager", "release")):
        assert f"- {party} — " in p and leader in p
    assert "THE MAP TEXT" in p and "second line of the map" not in p                          # a map's first line
    assert "What each holds now of what this decision changes:\n(none)" in p                  # nothing is held yet


def test_a_slice_is_kept_for_each_party_that_got_one_and_the_others_are_none_and_the_event_has_no_word_of_it(host, tech, design, release, model):
    _log(host)
    model.said["slice"] = CUT
    host.ideas.keeper.slices_cut(6)
    _idle(host)
    store = slices.read(host.ideas.state_dir)
    assert store["from"] == 6 and store["cut"] == {"6": [tech, design]}                      # release is not there: that is the answer
    assert {s["party"]: s["says"] for s in store["slices"]} == {tech: "Your builds are quick.", design: "Your screens hold 6 seconds."}
    assert slices.kept_from(host.ideas.state_dir) == 6
    (e,) = _events(host)
    assert (e["decision"], e["parties"], e["none"], e["replaced"], e["failed"]) == (6, 2, 1, 0, False) and e["cost"] == 0.01 and "seconds" in e
    assert "Your builds" not in json.dumps(e)


def test_the_call_is_given_the_standing_slices_of_the_decisions_the_entry_changes(host, tech, design, model):
    _log(host)
    (old,) = slices.add_cut(host.ideas.state_dir, 5, {design: {"says": "Your screens hold 10 seconds.", "points": ["5.1"]}, tech: {"says": "Unrelated.", "points": ["4.1"]}})[:1]
    elsewhere = slices.add_cut(host.ideas.state_dir, 4, {tech: {"says": "Not on 5 at all.", "points": ["4.1"]}}) and None
    model.said["slice"] = {"slices": {design: {"says": "Your screens hold 6 seconds.", "points": ["6.1"], "replaces": [old["id"]]}, tech: {"says": "x", "points": ["6.1"], "replaces": ["s-invented"]}}}
    host.ideas.keeper.slices_cut(6)
    _idle(host)
    p = model.calls[0]["prompt"]
    assert f"{old['id']} {design}: Your screens hold 10 seconds. (§5.1)" in p and "Not on 5 at all" not in p
    mine = {s["party"]: s for s in slices.read(host.ideas.state_dir)["slices"] if s["decision"] == 6}
    assert mine[design]["was"] == "Your screens hold 10 seconds (§5.1)" and [s["id"] for s in slices.standing(host.ideas.state_dir, design)] == [mine[design]["id"]]
    assert mine[tech]["was"] == "" and (e := _events(host)[0])["replaced"] == 1 and e["parties"] == 2


def test_a_failed_cut_keeps_nothing_records_failed_and_is_not_tried_again(host, tech, model):
    _log(host)
    model.said["slice"] = "I am sorry, I cannot"
    host.ideas.keeper.slices_cut(6)
    _idle(host)
    assert len(model.steps("slice")) == 2                                                    # the call is tried once more
    assert slices.read(host.ideas.state_dir)["slices"] == [] and not slices.is_cut(host.ideas.state_dir, 6) and slices.from_(host.ideas.state_dir) is None
    (e,) = _events(host)
    assert e["failed"] is True and e["parties"] == 0 and e["decision"] == 6
    model.said["slice"] = {"slices": []}                                                    # an answer that is no cut is a failed cut too
    host.ideas.keeper.slices_cut(6)
    _idle(host)
    assert len(_events(host)) == 2 and all(e["failed"] for e in _events(host)) and not slices.is_cut(host.ideas.state_dir, 6)


# -- Confirm ------------------------------------------------------------------------------------------------------------------------------

def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def _decided(host, tech, model):
    model.said["talk_round"] = {"stance": "s", "for": "f", "against": "a", "second_round": False, "questions": []}
    model.said["decide"] = {"title": "Dark mode ships as a setting", "why": "People read at night.", "points": ["Product asks for a setting.", "Tech adds the theme."]}
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    host.command("ideas.route_set", {"idea": slug, "route": [tech]})
    host.command("ideas.talk", {"idea": slug})
    for _ in range(1000):
        if ideas.state(host.ideas.state_dir, slug)["state"] == "decided" and not host.ideas.keeper.busy(slug):
            return slug
        time.sleep(0.01)
    raise AssertionError("never decided")


def test_confirm_begins_one_cut_of_the_decision_it_wrote_and_never_waits_for_it(host, tech, design, model):
    slug = _decided(host, tech, model)
    model.said["slice"] = {"slices": {tech: {"says": "Your theme is one file.", "points": ["1.2"], "replaces": []}, design: None}}
    host.ideas.keeper.sections = lambda s: None
    got = host.command("ideas.confirm", {"idea": slug})
    assert got["ok"] is True and got["number"] == 1
    _idle(host)
    (call,) = model.steps("slice")
    assert "## 1. Dark mode ships as a setting" in call["prompt"] and "2. Tech adds the theme." in call["prompt"]
    store = slices.read(host.ideas.state_dir)
    assert store["from"] == 1 and store["cut"] == {"1": [tech]} and [(s["party"], s["points"]) for s in store["slices"]] == [(tech, ["1.2"])]
    assert call["key"] == slug                                                              # the goal's own: its ledger


def test_a_hypothesis_verdict_is_a_decision_with_no_goal_and_is_cut_too(host, tech, design, model):
    host.ideas.root()                                                                       # the Board's tree stands: the decision lands in dev
    item = host.command("ideas.hypothesis_set", {"text": "People want a sketch first", "signal": "most ask for one"})["item"]
    test_goal = ideas.add_idea(host.ideas.root(), "Interview five founders", "general", host.ideas.state_dir)
    host.command("ideas.hypothesis_attach", {"id": item["id"], "test": test_goal})
    ideas.save_state(host.ideas.state_dir, test_goal, state="done")
    model.said["slice"] = {"slices": {tech: None, design: {"says": "Your sketches come first.", "points": ["1"], "replaces": []}}}
    got = host.command("ideas.hypothesis_judge", {"id": item["id"], "state": "held", "why": "Clear enough"})
    assert got["decision"]["number"] == 1
    _idle(host)
    (call,) = model.steps("slice")
    assert "## 1. Hypothesis held: People want a sketch first" in call["prompt"] and call["key"] != tech
    assert slices.is_cut(host.ideas.state_dir, 1) and [(s["party"], s["points"]) for s in slices.read(host.ideas.state_dir)["slices"]] == [(design, ["1"])]
    unsure = host.command("ideas.hypothesis_set", {"text": "Another claim", "signal": "a signal"})["item"]
    goal2 = ideas.add_idea(host.ideas.root(), "Another test", "general", host.ideas.state_dir)
    host.command("ideas.hypothesis_attach", {"id": unsure["id"], "test": goal2})
    ideas.save_state(host.ideas.state_dir, goal2, state="done")
    host.command("ideas.hypothesis_judge", {"id": unsure["id"], "state": "unsure", "why": "Not sure"})
    _idle(host)
    assert len(model.steps("slice")) == 1                                                   # not sure yet writes no decision: nothing to cut


# -- the fold -----------------------------------------------------------------------------------------------------------------------------

def _many(host, party, n=10, start=1):
    for k in range(start, start + n):
        slices.add_cut(host.ideas.state_dir, k, {party: {"says": f"Slice number {k:02d} " + "w" * 150, "points": [f"{k}.1"]}})


def test_the_fold_is_one_call_of_the_partys_leader_given_its_old_digest_and_the_slices_past_the_bound(host, tech, model):
    _many(host, tech)
    owed = [s["says"] for s in slices.past_bound(host.ideas.state_dir, tech)]
    model.said["slice_digest"] = {"digest": "You keep the early slices short (§1.1, §2.1)."}
    assert host.ideas.keeper.slices_fold_for([tech, tech, "ghost", ""]) == 1
    _idle(host)
    (call,) = model.calls
    assert call["step"] == "slice_digest" and call["tools"] is False and call["key"] == f"goal:{tech}" and call["as_role"] == ""
    assert (call["tier"], call["effort"]) == idea_target.pick("slice_digest", "balance") and call["budget"] == idea_target.budget("slice_digest", "balance")
    p = call["prompt"]
    assert p.startswith("You are Architect, the leader of this goal's party") and "Read no file" in p and '{"digest": "…"}' in p and str(slices.DIGEST_CHARS) in p      # its leader's voice
    assert all(x in p for x in owed) and "Slice number 10" not in p and "Your digest so far" not in p and "(§1.1)" in p


def test_a_cut_begins_the_fold_of_the_party_it_gave_a_slice_whose_slices_are_past_the_bound(host, tech, design, model):
    _log(host, LOG.replace("## 6.", "## 20."))
    _many(host, tech, 10, start=10)
    model.said["slice"] = CUT
    model.said["slice_digest"] = {"digest": "You keep it short (§10.1)."}
    host.ideas.keeper.slices_cut(20)
    _idle(host)
    assert [c["key"] for c in model.steps("slice_digest")] == [f"goal:{tech}"]              # tech's are past the bound; design's one fits
    assert slices.digest(host.ideas.state_dir, tech)["text"] == "You keep it short (§10.1)." and slices.digest(host.ideas.state_dir, design) == {}


# -- the recut ----------------------------------------------------------------------------------------------------------------------------

def test_a_store_that_is_missing_is_cut_again_from_slices_from_at_the_first_leaders_call(host, tech, model):
    text = "# Decisions\n\n" + "".join(f"## {n}. Decision {n} (1 May 2026, the person and Orkboard)\n\nWhy: x.\n\n1. One.\n2. Two.\n\n" for n in range(1, 21))
    _log(host, text)
    (host.ideas.state_dir / "project.json").write_text('{"decisions": "docs/decisions.md", "slices_from": 3}', encoding="utf-8")
    model.said["slice"] = CUT
    model.said["talk_round"] = {"stance": "s", "for": "f", "against": "a", "second_round": False, "questions": []}
    assert not slices.exists(host.ideas.state_dir)
    host.ideas.keeper.ask("ask", "a leader's call", tools=False)                            # the first leader's call after the start
    _idle(host)
    done = [int(c["prompt"].split("## ")[1].split(".")[0]) for c in model.steps("slice")]
    assert done == list(range(3, 3 + slices.RECUT_MAX))                                     # oldest first, twelve in one go, one call each
    assert slices.from_(host.ideas.state_dir) == 3 and not slices.is_cut(host.ideas.state_dir, 15)
    host.ideas.keeper.ask("ask", "again", tools=False)
    _idle(host)
    assert len(model.steps("slice")) == slices.RECUT_MAX                                    # once a start: the rest wait for the next


# -- what a leader holds, for the readers' tests and the decision's call ----------------------------------------------------------------------

def _hold(host, tech, design=None):
    """Tech holds a slice (and Design one), the project has a fact and both journals have a line: the parts a leader's call is given before its map."""
    slices.add_cut(host.ideas.state_dir, 6, {tech: {"says": "Your builds are quick.", "points": ["6.2"]}, **({design: {"says": "Design's own slice.", "points": ["6.1"]}} if design else {})})
    project_facts.keep(host.ideas.state_dir, tech, "for_whom", "Friends at one TV", "person")
    from orkboard.realm import journals
    journals.add(host.ideas.state_dir, tech, "stance", "You said go on “Add a score board”.", idea="add-a-score-board")
    journals.add(host.ideas.state_dir, journals.PROJECT, "decision", "Decision 12: no accounts.", idea="add-a-score-board", ref="12")


def _route(tech):
    return [{"party": tech, "leader": "architect"}]


# -- the decision's call ------------------------------------------------------------------------------------------------------------------

def test_the_decisions_call_has_the_touched_leaders_slices_after_the_journals_and_before_the_decisions_file(host, tech, design, release, goal):
    _hold(host, tech, design)
    slices.add_cut(host.ideas.state_dir, 7, {release: {"says": "Release's untouched slice.", "points": ["7.1"]}})
    _log(host)
    keeper = host.ideas.keeper
    prompt = keeper.decision_prompt(goal, _route(tech), idea_questions.record(host.ideas.state_dir, goal))
    head = "What the leaders hold that this goal touches:\n"
    assert head in prompt
    assert f"- Architect ({tech}): Your builds are quick. (§6.2)" in prompt                      # the route's party
    assert f"({design}): Design's own slice. (§6.1)" in prompt                                  # a party whose map a mark of the goal names (screens)
    assert "Release's untouched slice" not in prompt
    assert prompt.index("Decision 12: no accounts") < prompt.index(head) < prompt.index("The project's decisions file")
    assert "Where the goal goes against a line under *What the leaders hold that this goal touches*, say so in a point and put that decision's number in `changes`." in prompt

