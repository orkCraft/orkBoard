"""Spec 125 C (docs/specs/125-the-journals.md §C; decisions §203): both journals in every leader's call, and the calibration line. Each step of the table has its journals (or the one it is given)
as parts of their own, after the project's facts and before the map; a member's call has none; `measures.of_party` and the line it makes; `CONTEXT` grew by 3,000 for them.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from orkboard.core import idea_journal
from orkboard.gui.board_host import Orkboard
from orkboard.realm import concerns as concern_store, event_log, goal_team, idea_questions, idea_target, ideas, journals, library, measures, project_facts

MAP = "THE MAP TEXT"


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    h.ideas.keeper._map = lambda party: MAP                       # a leader's map as text, whatever the project holds
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
def goal(host, tech):
    slug = ideas.add_idea(host.ideas.root(), "add a score board", tech, host.ideas.state_dir, "normal", "hold")
    ideas.save_state(host.ideas.state_dir, slug, marks=[{"map": "system", "id": "cache", "name": "Cache"}])
    return slug


def _write(host, tech, goal):
    """A leader's journal with a line on this goal, one on a part it points at (of another goal), one of nothing near, and the project's with a line on this goal."""
    s = host.ideas.state_dir
    journals.add(s, tech, "stance", "You said no to “Add a score board” because it would break THE CACHE.", idea=goal)
    journals.add(s, tech, "concern_goal", "Your concern on the cache became the goal “Fix the cache”.", idea="fix-cache", on=["cache"])
    journals.add(s, journals.PROJECT, "decision", "Decision 12: no accounts in the first release.", idea=goal, ref="12")
    project_facts.keep(s, tech, "for_whom", "Friends at one TV", "person")


def _before_the_map(prompt, *needles):
    at = prompt.index(f"Your party's map:\n{MAP}")
    for n in needles:
        assert n in prompt and prompt.index(n) < at, n


def _after(prompt, first, second):
    assert prompt.index(first) < prompt.index(second)


def _has_both(prompt):
    assert "What you said before and what came of it (your journal, newest last):\n" in prompt
    assert "What the project decided and what came of it (its journal, newest last):\n" in prompt
    assert "Add a score board” because it would break THE CACHE" in prompt and "Decision 12: no accounts" in prompt
    assert "Fix the cache" in prompt                                                       # an entry on a part of the goal's marks


def _route(tech):
    return [{"party": tech, "leader": "architect"}]


# -- the parts ---------------------------------------------------------------------------------------------------------------------------

def test_a_leaders_parts_are_its_own_journal_with_the_goals_marks_and_the_projects_each_a_part_of_its_own(host, tech, goal):
    _write(host, tech, goal)
    own, project = idea_journal.parts(host.ideas.state_dir, host.repo_root, tech, goal)
    assert own[0] == "What you said before and what came of it (your journal, newest last)" and project[0] == "What the project decided and what came of it (its journal, newest last)"
    assert "Add a score board” because" in own[1] and "Fix the cache" in own[1] and "Decision 12" not in own[1]       # the part of the goal's marks: `cache`
    assert "Decision 12" in project[1]
    only = idea_journal.parts(host.ideas.state_dir, host.repo_root, tech, "")                                         # no goal: no marks, only the latest
    assert any("Fix the cache" in t for _h, t in only)


def test_an_empty_journal_adds_no_part_and_the_orkmasters_tab_is_given_the_projects_alone(host, tech, goal):
    s, root = host.ideas.state_dir, host.repo_root
    assert idea_journal.parts(s, root, tech, goal) == []
    journals.add(s, journals.PROJECT, "decision", "Decision 1: ship it.", idea=goal)
    assert [h for h, _t in idea_journal.parts(s, root, tech, goal)] == ["What the project decided and what came of it (its journal, newest last)"]
    journals.add(s, tech, "stance", "You said go.", idea=goal)
    assert len(idea_journal.parts(s, root, tech, goal)) == 2
    assert [h for h, _t in idea_journal.parts(s, root, "", goal)] == ["What the project decided and what came of it (its journal, newest last)"]
    assert idea_journal.parts(s, root, tech, goal, own=False)[0][1].endswith("Decision 1: ship it.")


def test_a_journal_that_cannot_be_read_never_stops_a_call(host, tech, goal, monkeypatch):
    _write(host, tech, goal)
    monkeypatch.setattr(journals, "text", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    assert idea_journal.parts(host.ideas.state_dir, host.repo_root, tech, goal) == []
    assert "Your party's map" in host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), 1, "", False, set())


# -- each step of the table ---------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("rnd", [1, 2])
def test_talks_round_has_both_journals_after_the_facts_and_before_the_map(host, tech, goal, rnd):
    _write(host, tech, goal)
    prompt = host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), rnd, "Q? A.", False, set())
    _has_both(prompt)
    _after(prompt, "What is known of the project", "What you said before")
    _after(prompt, "What you said before", "What the project decided")
    _before_the_map(prompt, "What you said before", "What the project decided")


def test_the_verdict_and_the_weighing_have_both_journals_before_the_map(host, tech, goal):
    _write(host, tech, goal)
    entry = {"party": tech, "leader": "architect"}
    for prompt in (host.ideas.keeper.verdict_prompt(goal, entry, _route(tech), []), host.ideas.keeper.weigh_prompt(goal, entry, _route(tech), [])):
        _has_both(prompt)
        _after(prompt, "What is known of the project", "What you said before")
        _before_the_map(prompt, "What you said before", "What the project decided")


@pytest.mark.parametrize("first", [True, False])
def test_the_sections_have_both_journals_after_the_facts_and_before_the_map(host, tech, goal, first):
    _write(host, tech, goal)
    prompt = host.ideas.keeper.section_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), first)
    _has_both(prompt)
    _after(prompt, "What is known of the project", "What you said before")
    _before_the_map(prompt, "What you said before", "What the project decided")


def test_the_leaders_look_has_its_own_journal_and_the_projects_before_its_frame_and_its_map(host, tech, goal):
    _write(host, tech, goal)
    s = host.ideas.state_dir
    prompt = host.ideas.keeper.concerns_prompt(tech, "tech", MAP, [{"id": "cache", "name": "Cache"}], [], [], concern_store.read(s, tech))
    assert "What you said before and what came of it (your journal, newest last):\n" in prompt and "What the project decided and what came of it" in prompt
    assert "Decision 12" in prompt and "Fix the cache" in prompt and "would break THE CACHE" in prompt       # no goal, no marks: the latest of each (`on`: none)
    _after(prompt, "What is known of the project", "What you said before")
    assert prompt.index("What the project decided") < prompt.index(f"Your party's map:\n{MAP}")


def test_a_quick_question_to_a_leader_has_both_the_orkmasters_tab_the_projects_alone(host, tech, goal):
    _write(host, tech, goal)
    keeper = host.ideas.keeper
    mine = keeper.ask_prompt(tech, "Is the cache safe?")
    assert "What you said before and what came of it (your journal, newest last):\n" in mine and "What the project decided and what came of it" in mine
    assert "Add a score board” because" in mine and "Decision 12" in mine
    _after(mine, "What is known of the project", "What you said before")
    orkmaster = keeper.ask_prompt("", "What did we decide?")
    assert "What the project decided and what came of it (its journal, newest last):\n" in orkmaster and "Decision 12" in orkmaster
    assert "What you said before" not in orkmaster


def test_the_decisions_wording_has_the_projects_journal_alone_before_the_decisions_file(host, tech, goal):
    _write(host, tech, goal)
    keeper = host.ideas.keeper
    prompt = keeper.decision_prompt(goal, _route(tech), idea_questions.record(host.ideas.state_dir, goal))
    assert "What the project decided and what came of it (its journal, newest last):\n" in prompt and "Decision 12: no accounts" in prompt
    assert "What you said before" not in prompt and "would break THE CACHE" not in prompt
    _after(prompt, "What the project decided", "The project's decisions file")


def test_a_goal_with_no_journals_has_prompts_as_before(host, tech, goal):
    keeper = host.ideas.keeper
    entry = {"party": tech, "leader": "architect"}
    for prompt in (keeper.round_prompt(goal, entry, _route(tech), 1, "", False, set()), keeper.verdict_prompt(goal, entry, _route(tech), []),
                   keeper.section_prompt(goal, entry, _route(tech), True), keeper.ask_prompt(tech, "q?"),
                   keeper.decision_prompt(goal, _route(tech), idea_questions.record(host.ideas.state_dir, goal))):
        assert "journal" not in prompt and "What you said before" not in prompt and "What the project decided and what came of it" not in prompt


def test_a_struck_entry_is_never_read_into_a_call(host, tech, goal):
    _write(host, tech, goal)
    s = host.ideas.state_dir
    entry = next(e for e in journals.read(s, tech) if e["kind"] == "stance")
    journals.strike(s, tech, entry["id"], "not so")
    prompt = host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), 1, "", False, set())
    assert "would break THE CACHE" not in prompt and "Fix the cache" in prompt


def test_a_members_call_is_given_none(host, tech, goal):
    """Only the leaders' prompts ask for the journals: no module of a member's call (a task's prompt, the Taskmaster's runner) reads `idea_journal`."""
    users = sorted(p.name for p in Path(idea_journal.__file__).parent.glob("*.py") if p.name != "idea_journal.py" and "idea_journal" in p.read_text(encoding="utf-8"))
    assert users == ["idea_accept.py", "idea_ask.py", "idea_concerns.py", "idea_decide.py", "idea_keeper.py", "idea_pass.py", "idea_sections.py", "idea_talk.py", "idea_verdict.py"]


# -- the context grew -----------------------------------------------------------------------------------------------------------------------

def test_the_context_of_each_step_that_reads_the_journals_grew_by_three_thousand():
    before = {"talk_round": 8_000, "talk_verdict": 6_000, "section_first": 12_000, "section": 12_000, "concerns": 12_000, "ask": 8_000, "decide": 8_000}
    for step, was in before.items():
        assert idea_target.CONTEXT[step] == was + 3_000 + (2_500 if step in ("talk_round", "section_first", "section") else 0) + (2_500 if step == "decide" else 1_200), step      # (and 2,500 more for the living specs: spec 127 C.3; the leaders' slices: spec 131 A.4)
    assert idea_target.CONTEXT["join"] == 8_000 and idea_target.CONTEXT["project_q"] == 12_000 + 1_200      # the rest stay (project_q grew for the slices: spec 131 A.4)


def test_what_fit_before_is_not_cut_now(host, tech, goal):
    _write(host, tech, goal)
    text = "x" * 7_000
    host.ideas.keeper._map = lambda party: text
    prompt = host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), 1, "", False, set())
    assert "x" * 6_999 in prompt and "What the project decided" in prompt


def test_a_calls_journals_are_at_most_three_thousand_characters(host, tech, goal):
    s = host.ideas.state_dir
    for i in range(80):
        journals.add(s, tech, "stance", f"You said go on “Goal {i}” " + "w" * 200, idea=f"g{i}")
        journals.add(s, journals.PROJECT, "decision", f"Decision {i}: " + "w" * 250, idea=f"g{i}")
    own, project = idea_journal.parts(s, host.repo_root, tech, "g1")
    assert len(own[1]) <= journals.CALL_CHARS + 400 and len(project[1]) <= journals.CALL_CHARS


# -- the calibration -------------------------------------------------------------------------------------------------------------------------

def _log(root, event, **fields):
    event_log.record(Path(root), event, **fields)


def _history(root):
    """Tech objected on a, b, c, d; the person went on against its no on a, b, c; a and b came back at Review, c was merged; d was heeded. Design objected to e (went on, merged).
    f and g, no one objected to: f came back, g was merged."""
    for idea in "abcd":
        _log(root, event_log.LEADER_OBJECTED, idea=idea, party="tech", verdict="no", has_instead=False)
    for idea in "abc":
        _log(root, event_log.OBJECTION_ANSWERED, idea=idea, party="tech", answer="go")
    _log(root, event_log.OBJECTION_ANSWERED, idea="d", party="tech", answer="drop")
    _log(root, event_log.LEADER_OBJECTED, idea="e", party="design", verdict="doubt", has_instead=False)
    _log(root, event_log.OBJECTION_ANSWERED, idea="e", party="design", answer="go")
    for idea, decision in (("a", "back"), ("b", "fix"), ("c", "merge"), ("e", "merge"), ("f", "drop"), ("g", "merge")):
        _log(root, event_log.RESULT_DECIDED, idea=idea, decision=decision)


def test_of_party_counts_the_partys_own_objections_and_what_came_of_the_ones_overruled(tmp_path):
    _history(tmp_path)
    assert measures.of_party(tmp_path, "tech") == {"objections": 4, "overruled": 3, "overruled_decided": 3, "overruled_came_back": 2, "unobjected_came_back_share": 0.5}
    assert measures.of_party(tmp_path, "design") == {"objections": 1, "overruled": 1, "overruled_decided": 1, "overruled_came_back": 0, "unobjected_came_back_share": 0.5}
    assert measures.of_party(tmp_path, "art") == {"objections": 0, "overruled": 0, "overruled_decided": 0, "overruled_came_back": 0, "unobjected_came_back_share": 0.5}


def test_of_party_of_a_project_with_no_log_is_all_zero(tmp_path):
    assert measures.of_party(tmp_path, "tech") == {"objections": 0, "overruled": 0, "overruled_decided": 0, "overruled_came_back": 0, "unobjected_came_back_share": None}


def test_the_calibration_line_says_the_record_in_the_products_words_and_only_once_a_no_was_overruled_and_decided(tmp_path):
    _history(tmp_path)
    assert measures.calibration(measures.of_party(tmp_path, "tech")) == ("Your record: 3 of your 4 no's were overruled; 2 of the 3 decided came back at Review (67 %), "
                                                                          "against 50 % of the goals no one objected to.")
    assert measures.calibration(measures.of_party(tmp_path, "art")) == "" and measures.calibration({}) == ""
    assert measures.calibration({"objections": 2, "overruled": 1, "overruled_decided": 1, "overruled_came_back": 1, "unobjected_came_back_share": None}) == (
        "Your record: 1 of your 2 no's were overruled; 1 of the 1 decided came back at Review (100 %).")


def test_the_line_follows_the_leaders_own_journal_in_its_calls_and_is_never_kept(host, tech, goal):
    _write(host, tech, goal)
    root = host.repo_root
    _history(root)
    own = idea_journal.parts(host.ideas.state_dir, root, tech, goal)[0][1]
    assert own.rstrip().endswith("against 50 % of the goals no one objected to.") and "Your record: 3 of your 4 no's were overruled" in own
    assert own.index("Add a score board") < own.index("Your record:")
    assert "Your record" not in "".join(e["text"] for e in journals.read(host.ideas.state_dir, tech))        # computed at the call: no entry keeps it
    assert "Your record: 3 of your 4" in host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), 1, "", False, set())
    project = idea_journal.parts(host.ideas.state_dir, root, tech, goal)[1][1]
    assert "Your record" not in project                                                                       # the project's journal has none


def test_a_leader_with_a_record_and_no_journal_is_still_told_its_record(host, tech, goal):
    _history(host.repo_root)
    (heading, body), = idea_journal.parts(host.ideas.state_dir, host.repo_root, tech, goal)
    assert heading.startswith("What you said before") and body.startswith("Your record: 3 of your 4")
