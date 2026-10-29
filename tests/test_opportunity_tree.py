"""Spec 102 G (docs/specs/102-the-other-maps-and-picking-on-them.md §8; decisions §172): Product's opportunity tree as code reads it, `realm/opportunity_tree.py`: one or two outcomes and three
to seven jobs kept in `<state_dir>/tree.json`, the goals that serve a job (one job at most) and the experiments that test a goal, the leader's answer taken strictly, the text with the goals'
titles and places from the Board's pages and the same bytes for the same record and goals. No git, no model."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import ideas, opportunity_tree as tree


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


def test_the_words_the_sentence_puts_before_a_part_are_not_kept_twice(state):
    got = tree.keep(state, OUT, [job("I want to see a sketch.", when="When I start a new project,", so="so I can judge the idea"), job("to share it", so="so that I can show it"),
                                 job("compare", so="that it is quick")], "person")
    assert got["jobs"][0]["when"] == "I start a new project" and got["jobs"][0]["want"] == "see a sketch" and got["jobs"][0]["so"] == "judge the idea"
    assert (got["jobs"][1]["want"], got["jobs"][1]["so"]) == ("share it", "show it") and got["jobs"][2]["so"] == "that it is quick"


def test_parts_are_bounded_and_one_part_given_leaves_the_other_as_it_is(state):
    long = "word " * 100
    got = tree.keep(state, [{"text": long}], [job(long, when=long, so=long, segment=long), *THREE[:2]], "person")
    assert len(got["outcomes"][0]["text"]) <= tree.OUTCOME_CHARS
    assert all(len(got["jobs"][0][k]) <= n for k, n in (("when", tree.PART_CHARS), ("want", tree.PART_CHARS), ("so", tree.PART_CHARS), ("segment", tree.SEGMENT_CHARS)))
    only = tree.keep(state, [{"text": "Another outcome"}], None, "person")
    assert only["jobs"] == got["jobs"] and [o["text"] for o in only["outcomes"]] == ["Another outcome"]
    assert tree.keep(state, None, THREE, "person")["outcomes"] == only["outcomes"]


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


def test_a_file_that_is_not_of_the_shape_reads_as_absent(state):
    (state / "tree.json").write_text(json.dumps({"outcomes": [{"id": "A B", "text": "x"}, {"id": "ok", "text": "Fine"}, "no"],
                                                 "jobs": [{"id": "j1", "when": "w", "want": "x", "so": "s", "by": "robot"}, {"id": "j2", "when": "w", "want": "", "so": "s"}, 3],
                                                 "serves": [{"job": "j1", "goal": "a"}, {"job": "j1", "goal": "a"}, {"job": "j2", "goal": "b"}, {"job": "j1", "goal": "Bad Slug"}],
                                                 "tests": [{"goal": "a", "experiment": "e"}, {"goal": "a", "experiment": "e"}, {"goal": "a", "experiment": "a"}, {"goal": 1}]}))
    got = tree.read(state)
    assert got["outcomes"] == [{"id": "ok", "text": "Fine"}] and [(j["id"], j["by"], j["segment"]) for j in got["jobs"]] == [("j1", "person", "")]
    assert got["serves"] == [{"job": "j1", "goal": "a"}] and got["tests"] == [{"goal": "a", "experiment": "e"}]
    (state / "tree.json").write_text("[1]")
    assert tree.read(state)["jobs"] == []


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


def test_an_experiment_tests_one_goal_at_most_and_an_empty_one_takes_them_off(state):
    kept(state)
    tree.test(state, "dark-mode", "try-dark")
    tree.test(state, "dark-mode", "try-contrast")
    assert tree.test(state, "faster-pages", "try-dark") == [{"goal": "dark-mode", "experiment": "try-contrast"}, {"goal": "faster-pages", "experiment": "try-dark"}]
    assert tree.test(state, "", "try-contrast") == [{"goal": "faster-pages", "experiment": "try-dark"}]
    tree.test(state, "faster-pages", "try-more")
    assert tree.test(state, "faster-pages", "") == []
    for goal_, experiment, why in (("", "", "Say which goal"), ("a", "a", "its own experiment"), ("a", "Bad Slug", "goal's name")):
        with pytest.raises(ValueError, match=why):
            tree.test(state, goal_, experiment)
    assert tree.read(state)["serves"] == []                                                         # the record's other parts stand
    assert [j["id"] for j in tree.read(state)["jobs"]] == ["see-a-sketch", "share-it-with-a-friend", "compare-two-versions"]


# -- the leader's answer, strictly ---------------------------------------------------------------------------------------------------

def test_the_leaders_answer_is_taken_strictly(state):
    good = {"outcomes": [{"text": "Cut the time"}], "jobs": [job("see a sketch"), job("share it"), job("compare two", so="so I can choose")]}
    got = tree.parse(good)
    assert got == {"outcomes": [{"text": "Cut the time"}], "jobs": [{"when": "I start a new project", "want": "see a sketch", "so": "judge the idea", "segment": "solo founders"},
                                                                    {"when": "I start a new project", "want": "share it", "so": "judge the idea", "segment": "solo founders"},
                                                                    {"when": "I start a new project", "want": "compare two", "so": "choose", "segment": "solo founders"}]}
    assert tree.keep(state, got["outcomes"], got["jobs"], "leader")["jobs"][2]["so"] == "choose"
    for bad in (None, "no", [], {}, {**good, "outcomes": []}, {**good, "outcomes": [{"text": "a"}, {"text": "b"}, {"text": "c"}]}, {**good, "outcomes": ["Cut the time"]},
                {**good, "jobs": good["jobs"][:2]}, {**good, "jobs": [job(f"w{n}") for n in range(8)]}, {**good, "jobs": "no"}, {**good, "jobs": [*good["jobs"][:2], job("x", segment="")]},
                {**good, "jobs": [*good["jobs"][:2], {"when": "w", "want": "x", "so": "s"}]}, {**good, "jobs": [*good["jobs"][:2], job("x", so=3)]}, {**good, "jobs": [*good["jobs"][:2], good["jobs"][0]]}):
        assert tree.parse(bad) is None


def test_the_proposal_is_recorded_beside_the_tree_and_forgotten_on_a_stop(state):
    assert tree.proposal(state) == {"status": "", "error": "", "at": ""}
    tree.save_proposal(state, "failed", "The leader\n did not answer")
    got = tree.proposal(state)
    assert got["status"] == "failed" and got["error"] == "The leader did not answer" and got["at"]
    kept(state)
    assert tree.proposal(state)["status"] == "failed" and tree.read(state)["jobs"]                  # the tree and the proposal live in one file, each alone
    tree.save_proposal(state, "")
    assert tree.proposal(state)["status"] == "" and tree.read(state)["jobs"]


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


def test_a_goal_gone_from_the_board_is_not_in_the_text_and_every_job_served_is_said(state, pages):
    one, two, three = (goal(pages, state, t) for t in ("Dark mode", "Faster pages", "Share links"))
    tree.keep(state, OUT, THREE, "person")
    for n, g in enumerate((one, two, three)):
        tree.attach(state, tree.read(state)["jobs"][n]["id"], g)
    assert tree.text(state, state, pages=pages).endswith("A goal serves every job.")
    (pages / ideas.IDEAS / f"{two}.md").unlink()
    got = tree.text(state, state, pages=pages)
    assert "Faster pages" not in got and two not in got and got.endswith("No goal serves yet: 2 (share it with a friend)")
    assert set(tree.goals(state, pages)) == {one, three}


def test_the_place_of_a_goal_is_in_line_at_work_or_done(state, pages):
    seen = {s: tree.place_of(state, goal(pages, state, f"Goal {s}", s)) for s in ("raw", "ready", "plan", "asks", "failed", "reading", "planning", "working", "judging", "talk", "decided", "sections",
                                                                                "done", "sent", "passed")}
    assert {s: p for s, p in seen.items() if p == "line"}.keys() == {"raw", "ready", "plan", "asks", "failed"}
    assert {s for s, p in seen.items() if p == "work"} == {"reading", "planning", "working", "judging", "talk", "decided", "sections"}
    assert {s for s, p in seen.items() if p == "done"} == {"done", "sent", "passed"}


def test_the_text_is_bounded_and_the_same_bytes_for_the_same_record_and_goals(state, pages):
    words = "word " * 30
    jobs = [job(f"w{n} {words}", when=words, so=words, segment=words) for n in range(7)]
    tree.keep(state, [{"text": "A " + words * 3}, {"text": "B " + words * 4}], jobs, "person")
    names = [goal(pages, state, f"A goal with a long title {n} " + words) for n in range(30)]
    for n, g in enumerate(names):
        tree.attach(state, tree.read(state)["jobs"][n % 7]["id"], g)
    first = tree.text(state, state, pages=pages)
    assert len(first) <= tree.LIMIT and first == tree.text(state, state, pages=pages) == tree.text(state, state, "dev-head-or-whatever", pages=pages)
    assert first.startswith("The opportunity tree\n\nOutcome: ") and "7. When" in first                          # every job is named, the goals are cut first
    assert tree.text(state, state)[:50] == tree.text(state, state)[:50] and len(tree.text(state, state)) <= tree.LIMIT


def test_a_tree_with_jobs_and_no_outcome_still_reads(state):
    tree.keep(state, None, THREE, "person")
    assert tree.text(state, state).splitlines()[2] == "Outcome: not said yet"
