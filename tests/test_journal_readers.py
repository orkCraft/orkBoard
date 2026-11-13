"""Spec 125 C (docs/specs/125-the-journals.md §C; decisions §203): both journals in every leader's call, and the calibration line. Each step of the table has its journals (or the one it is given)
as parts of their own, after the project's facts and before the map; a member's call has none; `measures.of_party` and the line it makes; `CONTEXT` grew by 3,000 for them.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from orkboard.core import idea_journal
from orkboard.gui.board_host import Orkboard
from orkboard.realm import event_log, goal_team, ideas, journals, library, measures, project_facts

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


# -- each step of the table ---------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("rnd", [1, 2])
def test_talks_round_has_both_journals_after_the_facts_and_before_the_map(host, tech, goal, rnd):
    _write(host, tech, goal)
    prompt = host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), rnd, "Q? A.", False, set())
    _has_both(prompt)
    _after(prompt, "What is known of the project", "What you said before")
    _after(prompt, "What you said before", "What the project decided")
    _before_the_map(prompt, "What you said before", "What the project decided")


def test_a_struck_entry_is_never_read_into_a_call(host, tech, goal):
    _write(host, tech, goal)
    s = host.ideas.state_dir
    entry = next(e for e in journals.read(s, tech) if e["kind"] == "stance")
    journals.strike(s, tech, entry["id"], "not so")
    prompt = host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), 1, "", False, set())
    assert "would break THE CACHE" not in prompt and "Fix the cache" in prompt


# -- the context grew -----------------------------------------------------------------------------------------------------------------------



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

