"""Spec 102 G (docs/specs/102-the-other-maps-and-picking-on-them.md §8; decisions §172): Product's opportunity tree as code reads it, `realm/opportunity_tree.py`: one or two outcomes and three
to seven jobs kept in `<state_dir>/tree.json`, the goals that serve a job (one job at most) and the experiments that test a goal, the leader's answer taken strictly, the text with the goals'
titles and places from the Board's pages and the same bytes for the same record and goals. No git, no model."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import hypotheses as hyp, ideas, opportunity_tree as tree


def job(want, when="I start a new project", so="judge the idea", segment="solo founders", **more):
    return {"when": when, "want": want, "so": so, "segment": segment, **more}


OUT = [{"text": "Cut the time to a first sketch from ten minutes to two"}]
THREE = [job("see a sketch"), job("share it with a friend"), job("compare two versions")]


@pytest.fixture
def state(tmp_path: Path) -> Path:
    (tmp_path / "state").mkdir()
    return tmp_path / "state"


@pytest.fixture
def pages(tmp_path: Path) -> Path:
    return tmp_path / "pages"


def goal(pages: Path, state: Path, title: str, board_state: str = "", element: str = "") -> str:
    slug = ideas.add_idea(pages, title, "general", state)
    changes = {**({"state": board_state} if board_state else {}), **({"element": element} if element else {})}
    if changes:
        ideas.save_state(state, slug, **changes)
    return slug


def kept(state, by="person"):
    return tree.keep(state, OUT, THREE, by)


# -- the record kept ------------------------------------------------------------------------------------------------------------------

def test_nothing_is_kept_before_a_tree_and_the_outcomes_and_jobs_are_kept_in_order_with_who_kept_them(state):
    assert tree.read(state) == {"outcomes": [], "jobs": [], "serves": [], "tests": []} and tree.text(state, state) is None
    got = tree.keep(state, [{"text": "  Cut the time   to a first sketch "}, {"text": "Keep people coming back"}], THREE, "leader")
    assert [o["text"] for o in got["outcomes"]] == ["Cut the time to a first sketch", "Keep people coming back"] and len({o["id"] for o in got["outcomes"]}) == 2
    assert [j["id"] for j in got["jobs"]] == ["see-a-sketch", "share-it-with-a-friend", "compare-two-versions"]
    assert all(j["by"] == "leader" and j["at"] and j["segment"] == "solo founders" for j in got["jobs"])
    assert got == tree.read(state) and got["serves"] == [] and got["tests"] == []
    assert json.loads((state / "tree.json").read_text())["jobs"][0]["when"] == "I start a new project"


def test_a_job_keeps_its_id_who_kept_it_and_its_goals_while_it_is_the_same_and_a_job_gone_takes_its_goals(state):
    first = kept(state, "leader")
    tree.attach(state, "see-a-sketch", "dark-mode")
    tree.attach(state, "compare-two-versions", "faster-pages")
    ids = [j["id"] for j in first["jobs"]]
    again = tree.keep(state, OUT, [{**first["jobs"][0]}, {**first["jobs"][1], "so": "show it off"}, {k: v for k, v in first["jobs"][2].items() if k != "id"}], "person")
    assert [j["id"] for j in again["jobs"]] == ids                                                    # the third came with no id: the same words are the same job
    assert [j["by"] for j in again["jobs"]] == ["leader", "person", "leader"] and again["jobs"][0] == first["jobs"][0] and again["jobs"][2] == first["jobs"][2]
    assert again["jobs"][1]["so"] == "show it off" and again["jobs"][1]["at"]
    assert len(again["serves"]) == 2
    gone = tree.keep(state, None, [first["jobs"][0], job("brand new"), job("another"), job("a fourth")], "person")
    assert gone["serves"] == [{"job": "see-a-sketch", "goal": "dark-mode"}]                           # the job that went took its goal


def test_a_count_outside_the_bounds_or_a_part_missing_is_refused_in_plain_words_and_changes_nothing(state):
    before = kept(state)
    four = [{"text": f"Outcome {n}"} for n in range(3)]
    for outcomes, jobs, why in ((four, None, "1 or 2 outcomes"), ([], None, "1 or 2 outcomes"), ("no", None, "1 or 2 outcomes"), ([{"text": ""}], None, "few words"),
                                ([{"text": "A"}, {"text": "a"}], None, "Two outcomes say the same"), (None, THREE[:2], "3 to 7 jobs"), (None, [job(f"w{n}") for n in range(8)], "3 to 7 jobs"),
                                (None, "no", "3 to 7 jobs"), (None, [*THREE[:2], job("")], "when, what the person wants"), (None, [*THREE[:2], "no"], "situation, a motive"),
                                (None, [*THREE[:2], {**THREE[0]}], "Two jobs say the same")):
        with pytest.raises(ValueError, match=why):
            tree.keep(state, outcomes, jobs, "person")
    with pytest.raises(ValueError, match="person or the leader"):
        tree.keep(state, OUT, THREE, "model")
    assert tree.read(state) == before


# -- the goals under a job, the experiments under a goal ------------------------------------------------------------------------------

def test_a_goal_serves_one_job_at_most_attaching_moves_it_and_an_empty_job_detaches_it(state):
    kept(state)
    assert tree.attach(state, "see-a-sketch", "dark-mode") == [{"job": "see-a-sketch", "goal": "dark-mode"}]
    tree.attach(state, "see-a-sketch", "faster-pages")
    assert tree.attach(state, "share-it-with-a-friend", "dark-mode") == [{"job": "see-a-sketch", "goal": "faster-pages"}, {"job": "share-it-with-a-friend", "goal": "dark-mode"}]
    assert tree.attach(state, "", "dark-mode") == [{"job": "see-a-sketch", "goal": "faster-pages"}] and tree.attach(state, "", "dark-mode") == tree.read(state)["serves"]
    for args, why in ((("no-such-job", "dark-mode"), "That job is gone"), (("see-a-sketch", ""), "goal's name"), (("see-a-sketch", "Not A Slug"), "goal's name")):
        with pytest.raises(ValueError, match=why):
            tree.attach(state, *args)
    assert tree.read(state)["serves"] == [{"job": "see-a-sketch", "goal": "faster-pages"}]


# -- the leader's answer, strictly ---------------------------------------------------------------------------------------------------


# -- its text --------------------------------------------------------------------------------------------------------------------------

def test_the_text_is_the_outcome_then_each_job_as_its_sentence_with_its_goals_and_the_jobs_none_serve(state, pages):
    one, two, three = goal(pages, state, "Dark mode"), goal(pages, state, "Faster pages", "working"), goal(pages, state, "Share links", "done")
    exp = goal(pages, state, "Try a contrast test", "planning")
    tree.keep(state, OUT, THREE, "person")
    tree.attach(state, "see-a-sketch", one)
    tree.attach(state, "see-a-sketch", two)
    tree.attach(state, "share-it-with-a-friend", three)
    tree.test(state, one, exp)
    assert tree.text(state, state, pages=pages) == """The opportunity tree

Outcome: Cut the time to a first sketch from ten minutes to two

1. When I start a new project, I want to see a sketch, so I can judge the idea. For solo founders.
   Served by: Dark mode (in line) (tested by Try a contrast test (at work)); Faster pages (at work)
2. When I start a new project, I want to share it with a friend, so I can judge the idea. For solo founders.
   Served by: Share links (done)
3. When I start a new project, I want to compare two versions, so I can judge the idea. For solo founders.
   Served by: no goal yet

No goal serves yet: 3 (compare two versions)"""
    assert tree.text(state, state).splitlines()[5] == f"   Served by: {one} (tested by {exp}); {two}"          # no pages: the goals' slugs


# -- the hypotheses under their job (spec 116 A) -------------------------------------------------------------------------------------

def test_the_hypotheses_are_under_their_job_and_the_ones_on_no_job_after_the_jobs(state, pages):
    one, exp = goal(pages, state, "Dark mode"), goal(pages, state, "Try a contrast test", "planning")
    done_exp = goal(pages, state, "Ask five people", "done")
    tree.keep(state, OUT, THREE, "person")
    tree.attach(state, "see-a-sketch", one)
    hyp.add(state, "People want a sketch first", "most ask within a minute", on="see-a-sketch")
    testing = hyp.add(state, "Contrast matters", "the test shows it", on="see-a-sketch")
    hyp.attach(state, testing["id"], test=exp)
    held = hyp.add(state, "Friends are the audience", "five say so", on="share-it-with-a-friend")
    hyp.attach(state, held["id"], test=done_exp)
    hyp.judge(state, held["id"], "held")
    hyp.add(state, "Not kept yet", "x", on="see-a-sketch", by="leader", party="product")             # proposed: not shown
    hyp.add(state, "Nobody tried this", "x", on="gone-job")                                          # a job that is gone: on no job
    hyp.add(state, "Under no job", "y")
    refuted = hyp.add(state, "It will go viral", "a thousand share", axis="viable")
    hyp.judge(state, refuted["id"], "refuted")
    got = tree.text(state, state, pages=pages)
    assert got == """The opportunity tree

Outcome: Cut the time to a first sketch from ten minutes to two

1. When I start a new project, I want to see a sketch, so I can judge the idea. For solo founders.
   Served by: Dark mode (in line)
   Hypothesis (open): People want a sketch first — we'll know when most ask within a minute
   Hypothesis (testing): Contrast matters — we'll know when the test shows it
2. When I start a new project, I want to share it with a friend, so I can judge the idea. For solo founders.
   Served by: no goal yet
   Hypothesis (held): Friends are the audience — we'll know when five say so
3. When I start a new project, I want to compare two versions, so I can judge the idea. For solo founders.
   Served by: no goal yet

Hypothesis (open): Nobody tried this — we'll know when x
Hypothesis (open): Under no job — we'll know when y
Hypothesis (refuted): It will go viral — we'll know when a thousand share

No goal serves yet: 2 (share it with a friend), 3 (compare two versions)"""
    assert "Not kept yet" not in got
    plain = tree.text(state, state)                                                                  # without pages the Board's places are not known: nothing is testing
    assert "Hypothesis (open): Contrast matters" in plain and "(testing)" not in plain


def test_a_record_with_only_hypotheses_is_still_nothing_to_read_and_none_leaves_the_text_as_it_was(state, pages):
    hyp.add(state, "Alone", "x")
    assert tree.text(state, state, pages=pages) is None
    tree.keep(state, OUT, THREE, "person")
    assert "Hypothesis (open): Alone" in tree.text(state, state)
    hyp.drop(state, "alone")
    assert "Hypothesis" not in tree.text(state, state, pages=pages)


def test_a_hypothesis_with_ways_says_them_in_the_trees_line_and_one_without_has_the_line_it_had(state, pages):
    tree.keep(state, OUT, THREE, "person")
    hyp.add(state, "A push helps", "goals land", on="see-a-sketch", refuted=[{"name": "the hook", "when": "opens only"}, {"name": "the noise", "when": "switched off"}])
    hyp.add(state, "Plain one", "it shows", on="see-a-sketch")
    got = tree.text(state, state, pages=pages)
    assert "   Hypothesis (open): A push helps — we'll know when goals land — refuted when the hook: opens only / the noise: switched off\n" in got
    assert "   Hypothesis (open): Plain one — we'll know when it shows\n" in got
