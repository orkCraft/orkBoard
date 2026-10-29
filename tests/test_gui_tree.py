"""Spec 102 G (docs/specs/102-the-other-maps-and-picking-on-them.md §8; decisions §172): Product's opportunity tree on the host and its keeper. `ideas.tree` (the outcomes, the jobs, the goals
that serve them with the Board's title, element and place, whether it is being proposed, the proposal's status), `ideas.tree_set` (the person's, `by: "person"`), `ideas.tree_attach` (a goal
under a job; an experiment on a goal), `ideas.tree_propose` (one call of Product's leader on the step `tree`: the cheaper tier, no tools, given the project's answers and the start files;
the outcomes and jobs kept `by: "leader"`; asked once, a failure after one more try asked again at the next press). The model call is stubbed (`keeper.call`).

These tests compose the mixins onto the keeper and the host the way the lead's wiring does (the `host` fixture): they pass with or without that wiring in `core/idea_keeper.py` and
`gui/ideas.py`.
"""
from __future__ import annotations

import json
import sys
import time

import pytest

from orkboard.core.idea_tree import TreeMixin as KeeperTree
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.gui.ideas_tree import TreeMixin as GuiTree, tree_commands
from orkboard.realm import goal_team, idea_spend, idea_target, ideas, library, opportunity_tree as tree, project_facts

COMMANDS = {"ideas.tree", "ideas.tree_set", "ideas.tree_attach", "ideas.tree_propose"}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    if not isinstance(h.ideas.keeper, KeeperTree):                            # wired by the lead: the keeper's bases, the host's and its table
        h.ideas.keeper.__class__ = type("KeeperWithTree", (KeeperTree, type(h.ideas.keeper)), {})
    if not isinstance(h.ideas, GuiTree):
        h.ideas.__class__ = type("IdeasWithTree", (GuiTree, type(h.ideas)), {})
    h.commands.update(tree_commands(h.ideas))
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def product(host):
    return _party(host, "Product", "product-manager", ["copywriter"], "product")


def make_goal(host, title, state="", element=""):
    slug = ideas.add_idea(host.ideas.root(), title, "general", host.ideas.state_dir)
    changes = {**({"state": state} if state else {}), **({"element": element} if element else {})}
    if changes:
        ideas.save_state(host.ideas.state_dir, slug, **changes)
    return slug


def job(want, when="I start a new project", so="judge the idea", segment="solo founders", **more):
    return {"when": when, "want": want, "so": so, "segment": segment, **more}


OUT = [{"text": "Cut the time to a first sketch from ten minutes to two"}]
THREE = [job("see a sketch"), job("share it with a friend"), job("compare two versions")]
ANSWER = {"outcomes": OUT, "jobs": THREE}


class Model:
    """The keeper's call stubbed: `answer` the JSON (or a callable of the call) every call gets, `calls` every call made."""

    def __init__(self, host, answer=None):
        self.host, self.calls, self.answer = host, [], ANSWER if answer is None else answer
        host.ideas.keeper.call = self

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        self.calls.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"],
                           "key": getattr(k._tls, "key", ""), "tool": k.tool_now()})
        answer = self.answer(self.calls[-1]) if callable(self.answer) else self.answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""


@pytest.fixture
def model(host):
    return Model(host)


def _wait(host, party):
    for _ in range(1000):
        if not host.ideas.keeper.busy_goal(party):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _propose(host, party=None):
    got = host.command("ideas.tree_propose", {})
    if party:
        _wait(host, party)
    return got


# -- the call: Product's leader, the cheaper tier, no tools, the project's answers and the start files -------------------------------------

def test_the_first_proposal_is_one_call_of_products_leader_on_the_cheaper_tier_with_no_tools_given_the_answers_and_the_start_files(host, product, model):
    (host.ideas.keeper.repo_root / "README.md").write_text("# Sketchy\n\nA sketch pad for solo founders.\n", encoding="utf-8")
    (host.ideas.keeper.repo_root / "docs" / "decisions.md").write_text("## 1. SECRET DECISION TEXT\n", encoding="utf-8")
    project_facts.keep(host.ideas.state_dir, product, "for_whom", "Solo founders with no designer", "person")
    project_facts.keep(host.ideas.state_dir, product, "hurts", "A first sketch takes ten minutes", "person")
    project_facts.keep(host.ideas.state_dir, product, "leaves_out", "Teams and sharing", "person")
    assert _propose(host, product) == {"ok": True, "asked": True}
    (call,) = model.calls
    assert call["step"] == "tree" and call["tools"] is False and call["key"] == f"goal:{product}"
    assert (call["tier"], call["effort"]) == idea_target.pick("tree", "balance") == ("warrior", "low")
    assert call["budget"] == idea_target.budget("tree", "balance")
    p = call["prompt"]
    assert p.startswith("You are Product manager, the leader of this goal's party")                                    # its leader's voice
    assert "Solo founders with no designer" in p and "A first sketch takes ten minutes" in p and "Teams and sharing" in p      # the project's answers (the common core)
    assert "Sketchy" in p and "docs/notes.md" in p and "SECRET DECISION TEXT" not in p                                  # the README and docs/'s top level; the decisions file never
    assert "Read no file" in p and '"outcomes"' in p and '"jobs"' in p and "3 to 7" in p and "1 or 2" in p


def test_the_step_is_as_the_loops_on_the_cheaper_tier_in_the_specs_stage_of_its_partys_ledger(host, product, model):
    _propose(host, product)
    spent = idea_spend.of_goal(host.ideas.state_dir, product)
    assert spent["usd"] == 0.01 and spent["stages"]["spec"]["usd"] == 0.01
    assert idea_spend.STEP_STAGE["tree"] == "spec" and "tree" in idea_target.STEPS and set(idea_target.MATRIX) >= set(idea_target.STEPS)
    for target in idea_target.TARGETS:
        assert idea_target.pick("tree", target) == idea_target.pick("loop", target)
    assert idea_target.READS["tree"] == 0 and idea_target.CONTEXT["tree"] == idea_target.CONTEXT["loop"] and idea_target.CAPS["tree"] == idea_target.CAPS["loop"] <= 0.15


def test_the_proposal_is_kept_by_the_leader_and_the_command_reads_it(host, product, model):
    assert host.command("ideas.tree", {}) == {"outcomes": [], "jobs": [], "serves": [], "tests": [], "proposing": False, "status": "", "party": product}
    _propose(host, product)
    got = host.command("ideas.tree", {})
    assert got["status"] == "done" and got["proposing"] is False and got["party"] == product and "error" not in got
    assert [o["text"] for o in got["outcomes"]] == [OUT[0]["text"]]
    assert [j["want"] for j in got["jobs"]] == ["see a sketch", "share it with a friend", "compare two versions"] and all(j["by"] == "leader" and j["at"] for j in got["jobs"])
    assert tree.read(host.ideas.state_dir)["jobs"] == got["jobs"]
    assert tree.text(host.ideas.state_dir, host.ideas.keeper.repo_root).splitlines()[4] == "1. When I start a new project, I want to see a sketch, so I can judge the idea. For solo founders."


def test_it_is_asked_once_a_tree_kept_or_proposed_is_never_asked_again(host, product, model):
    assert _propose(host, product)["asked"] is True and _propose(host, product)["asked"] is False and len(model.calls) == 1
    tree.save_proposal(host.ideas.state_dir, "")                                                                        # the proposal forgotten: the tree stands, so nothing is asked
    assert _propose(host, product)["asked"] is False and len(model.calls) == 1


def test_a_tree_the_person_kept_first_is_never_asked_and_never_overwritten_by_a_late_proposal(host, product):
    def late(call):
        host.command("ideas.tree_set", {"outcomes": [{"text": "Mine"}], "jobs": [job(w) for w in ("a", "b", "c")]})        # the person keeps theirs while the leader is asked
        return ANSWER

    model = Model(host, late)
    _propose(host, product)
    got = tree.read(host.ideas.state_dir)
    assert [o["text"] for o in got["outcomes"]] == ["Mine"] and [j["want"] for j in got["jobs"]] == ["a", "b", "c"] and {j["by"] for j in got["jobs"]} == {"person"} and len(model.calls) == 1
    assert _propose(host, product)["asked"] is False and len(model.calls) == 1


def test_a_call_that_does_not_answer_is_tried_once_more_then_recorded_and_asked_again_at_the_next_press(host, product):
    model = Model(host, "not json at all")
    _propose(host, product)
    assert len(model.calls) == 2                                                                                      # one more try
    got = host.command("ideas.tree", {})
    assert got["jobs"] == [] and got["status"] == "failed" and "did not answer" in got["error"] and got["proposing"] is False
    for bad in ({**ANSWER, "jobs": THREE[:2]}, {**ANSWER, "outcomes": []}, {**ANSWER, "jobs": "no"}, {**ANSWER, "jobs": [*THREE[:2], {"when": "w", "want": "x", "so": "s"}]}):    # strictly
        model.answer = bad
        _propose(host, product)
        assert host.command("ideas.tree", {})["status"] == "failed" and not tree.read(host.ideas.state_dir)["jobs"]
    model.answer = ANSWER
    assert _propose(host, product)["asked"] is True and host.command("ideas.tree", {})["status"] == "done" and len(tree.read(host.ideas.state_dir)["jobs"]) == 3


def test_a_call_lost_with_the_process_is_not_proposing_and_is_asked_again(host, product, model):
    tree.save_proposal(host.ideas.state_dir, "asking")                                                                  # the record of a run that died
    assert host.command("ideas.tree", {})["proposing"] is False and host.command("ideas.tree", {})["status"] == ""
    assert _propose(host, product)["asked"] is True and len(model.calls) == 1


def test_a_proposal_being_asked_is_proposing_and_is_not_asked_a_second_time(host, product):
    seen = {}

    def slow(call):
        seen["tree"] = host.command("ideas.tree", {})
        seen["again"] = host.command("ideas.tree_propose", {})
        return ANSWER

    Model(host, slow)
    _propose(host, product)
    assert seen["tree"]["proposing"] is True and seen["tree"]["status"] == "asking" and seen["tree"]["jobs"] == [] and seen["again"]["asked"] is False


def test_no_product_party_or_no_call_to_make_is_asked_false_with_why_never_a_refusal(host, model, monkeypatch):
    assert _propose(host) == {"ok": True, "asked": False, "why": "Product has no party here: make it first"} and not model.calls
    assert host.command("ideas.tree", {})["party"] == ""
    _party(host, "Product", "product-manager", ["copywriter"], "product")
    monkeypatch.setattr(host.ideas.keeper, "_may_run", lambda: "Today's spend limit is reached: the keeper waits")
    assert _propose(host) == {"ok": True, "asked": False, "why": "Today's spend limit is reached: the keeper waits"}
    assert not model.calls and tree.proposal(host.ideas.state_dir)["status"] == ""                                      # nothing begun: asked at the next press


def test_a_party_that_is_not_products_is_not_asked(host, model):
    _party(host, "Game design", "game-designer", ["level-designer"], "product")
    _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")
    assert _propose(host)["asked"] is False and not model.calls


# -- the person's outcomes and jobs ----------------------------------------------------------------------------------------------------

def test_the_person_sets_the_outcomes_and_jobs_kept_by_the_person_and_one_part_alone_leaves_the_other(host, product):
    got = host.command("ideas.tree_set", {"outcomes": OUT, "jobs": THREE})
    assert got["ok"] is True and got["serves"] == [] and [j["by"] for j in got["jobs"]] == ["person"] * 3 and got["outcomes"][0]["text"] == OUT[0]["text"]
    assert host.command("ideas.tree", {})["jobs"] == got["jobs"]
    only = host.command("ideas.tree_set", {"outcomes": [{"text": "Keep people coming back"}]})
    assert only["jobs"] == got["jobs"] and only["outcomes"][0]["text"] == "Keep people coming back"
    again = host.command("ideas.tree_set", {"jobs": [got["jobs"][0], {**got["jobs"][1], "so": "show it off"}, got["jobs"][2]]})
    assert again["jobs"][0] == got["jobs"][0] and again["jobs"][1]["so"] == "show it off" and again["jobs"][1]["id"] == got["jobs"][1]["id"]


def test_the_jobs_of_the_leader_the_person_did_not_touch_stay_the_leaders(host, product, model):
    _propose(host, product)
    kept = tree.read(host.ideas.state_dir)["jobs"]
    got = host.command("ideas.tree_set", {"jobs": [kept[0], {**kept[1], "want": "pass it on"}, kept[2]]})
    assert [j["by"] for j in got["jobs"]] == ["leader", "person", "leader"] and got["jobs"][1]["id"] == kept[1]["id"]


def test_a_set_that_is_none_is_refused_in_plain_words_and_changes_nothing(host, product):
    host.command("ideas.tree_set", {"outcomes": OUT, "jobs": THREE})
    before = tree.read(host.ideas.state_dir)
    for bad, why in (({}, "Say the outcomes or the jobs"), ({"jobs": THREE[:2]}, "3 to 7 jobs"), ({"jobs": "no"}, "3 to 7 jobs"), ({"outcomes": []}, "1 or 2 outcomes"),
                     ({"outcomes": [{"text": ""}]}, "few words"), ({"jobs": [*THREE[:2], job("")]}, "when, what the person wants"), ({"jobs": [*THREE[:2], THREE[0]]}, "Two jobs say the same")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.tree_set", bad)
    assert tree.read(host.ideas.state_dir) == before


# -- the goals under a job, the experiments on a goal ----------------------------------------------------------------------------------

def test_a_goal_is_attached_under_a_job_with_the_boards_title_element_and_place_and_the_command_reads_it(host, product):
    host.command("ideas.tree_set", {"outcomes": OUT, "jobs": THREE})
    dark, fast = make_goal(host, "Dark mode", element="ice"), make_goal(host, "Faster pages", "working")
    got = host.command("ideas.tree_attach", {"job": "see-a-sketch", "goal": dark})
    assert got == {"ok": True, "serves": [{"job": "see-a-sketch", "goal": dark, "title": "Dark mode", "element": "ice", "place": "line"}]}
    host.command("ideas.tree_attach", {"job": "see-a-sketch", "goal": fast})
    moved = host.command("ideas.tree_attach", {"job": "share-it-with-a-friend", "goal": dark})
    assert [(s["job"], s["goal"], s["place"]) for s in moved["serves"]] == [("see-a-sketch", fast, "work"), ("share-it-with-a-friend", dark, "line")]
    ideas.save_state(host.ideas.state_dir, fast, state="done")
    assert host.command("ideas.tree", {})["serves"][0]["place"] == "done"
    assert host.command("ideas.tree_attach", {"job": "", "goal": dark})["serves"] == [{"job": "see-a-sketch", "goal": fast, "title": "Faster pages", "element": "", "place": "done"}]


def test_an_experiment_is_set_on_a_goal_and_taken_off_it(host, product):
    dark, test, other = make_goal(host, "Dark mode"), make_goal(host, "Try dark mode on ten people", "working"), make_goal(host, "Try contrast")
    got = host.command("ideas.tree_attach", {"goal": dark, "experiment": test})
    assert got == {"ok": True, "tests": [{"goal": dark, "experiment": test, "title": "Try dark mode on ten people", "element": "", "place": "work"}]}
    host.command("ideas.tree_attach", {"goal": dark, "experiment": other})
    assert [t["experiment"] for t in host.command("ideas.tree", {})["tests"]] == [test, other]
    assert [t["experiment"] for t in host.command("ideas.tree_attach", {"goal": dark, "experiment": ""})["tests"]] == []


def test_an_attach_that_is_none_is_refused_in_plain_words_and_changes_nothing(host, product):
    host.command("ideas.tree_set", {"outcomes": OUT, "jobs": THREE})
    dark = make_goal(host, "Dark mode")
    host.command("ideas.tree_attach", {"job": "see-a-sketch", "goal": dark})
    before = tree.read(host.ideas.state_dir)
    for bad, why in (({"job": "no-such-job", "goal": dark}, "That job is gone"), ({"job": "see-a-sketch", "goal": "ghost"}, "That goal is gone"), ({"job": "see-a-sketch", "goal": ""}, "That goal is gone"),
                     ({"goal": dark, "experiment": "ghost"}, "That goal is gone"), ({"goal": "ghost", "experiment": dark}, "That goal is gone"), ({"goal": dark, "experiment": dark}, "its own experiment"),
                     ({"job": "see-a-sketch", "goal": 3}, "not text")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.tree_attach", bad)
    assert tree.read(host.ideas.state_dir) == before


def test_a_goal_dropped_from_the_board_is_left_out_of_the_command_and_a_detach_still_works(host, product):
    host.command("ideas.tree_set", {"outcomes": OUT, "jobs": THREE})
    dark, fast = make_goal(host, "Dark mode"), make_goal(host, "Faster pages")
    host.command("ideas.tree_attach", {"job": "see-a-sketch", "goal": dark})
    host.command("ideas.tree_attach", {"job": "see-a-sketch", "goal": fast})
    (host.ideas.root() / ideas.IDEAS / f"{dark}.md").unlink()
    assert [s["goal"] for s in host.command("ideas.tree", {})["serves"]] == [fast]
    assert host.command("ideas.tree_attach", {"job": "", "goal": dark})["ok"] is True and [s["goal"] for s in tree.read(host.ideas.state_dir)["serves"]] == [fast]


def test_the_commands_are_in_the_table_by_name(host):
    assert COMMANDS <= set(host.commands) and set(tree_commands(host.ideas)) == COMMANDS
