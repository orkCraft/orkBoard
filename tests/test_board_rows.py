"""Spec 116 C (docs/specs/116-hypotheses-on-products-tree.md §4.1) on `realm/board_rows.py`: the row `hypothesis`, one for each open hypothesis whose every test is done, laid after `project_q`,
built into the Board's Needs you and the Map's rows; it comes when the last test is done and not before, and leaves when judged."""
from __future__ import annotations

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import board_map, board_rows, hypotheses, ideas, project_questions


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    h.ideas.root()
    return h


def goal(host, title, state=""):
    slug = ideas.add_idea(host.ideas.root(), title, "general", host.ideas.state_dir)
    if state:
        ideas.save_state(host.ideas.state_dir, slug, state=state)
    return slug


def test_no_row_without_hypotheses_or_pages(host):
    assert board_rows.rows(host.ideas.state_dir, host.ideas.root()) == [] and board_rows.hypothesis(host.ideas.state_dir) == []
    item = hypotheses.add(host.ideas.state_dir, "People want a sketch", "most ask for one")
    hypotheses.attach(host.ideas.state_dir, item["id"], test=goal(host, "Interview", state="done"))
    assert board_rows.rows(host.ideas.state_dir) == []                                                  # without the pages no test can be told done


def test_the_row_appears_when_the_last_test_is_done_and_not_before(host):
    state, root = host.ideas.state_dir, host.ideas.root()
    item = hypotheses.add(state, "People want a sketch", "most ask for one in a minute")
    assert board_rows.rows(state, root) == []                                                          # open with no test: nothing is due
    first, second = goal(host, "Interview five founders", state="done"), goal(host, "Playtest the sketch", state="working")
    hypotheses.attach(state, item["id"], test=first)
    hypotheses.attach(state, item["id"], test=second)
    assert board_rows.rows(state, root) == []                                                          # one test still at work
    ideas.save_state(state, second, state="done")
    hypotheses.evidence(state, item["id"], "Four of five asked", ref=first)
    (row,) = board_rows.rows(state, root)
    assert row == {"kind": "hypothesis", "id": item["id"], "text": "People want a sketch", "signal": "most ask for one in a minute",
                   "evidence": [{"text": "Four of five asked", "ref": first, "at": row["evidence"][0]["at"]}],
                   "tests": [{"slug": first, "title": "Interview five founders"}, {"slug": second, "title": "Playtest the sketch"}],
                   "party": "", "leader": "orkmaster", "blocks": False, "priority": "normal", "at": item["at"]}


def test_a_test_gone_from_the_board_is_not_done(host):
    state, root = host.ideas.state_dir, host.ideas.root()
    item = hypotheses.add(state, "People want a sketch", "s")
    test = goal(host, "Interview", state="done")
    hypotheses.attach(state, item["id"], test=test)
    assert len(board_rows.rows(state, root)) == 1
    ideas.drop(root, test, state)
    assert board_rows.rows(state, root) == []


def test_a_proposed_one_is_not_due_and_a_judged_one_leaves(host):
    state, root = host.ideas.state_dir, host.ideas.root()
    proposed = hypotheses.add(state, "Founders pay", "ten say so", by="leader", party="product")
    hypotheses.attach(state, proposed["id"], test=goal(host, "Ask them", state="done"))
    assert board_rows.rows(state, root) == []
    hypotheses.keep(state, proposed["id"])
    assert [r["id"] for r in board_rows.rows(state, root)] == [proposed["id"]]
    hypotheses.judge(state, proposed["id"], "held", decision=3)
    assert board_rows.rows(state, root) == []


def test_a_leaders_hypothesis_names_its_party_and_that_partys_leader(host):
    state, root = host.ideas.state_dir, host.ideas.root()
    party, _new = ideas.save_goal(root, None, "Product", "About Product", None, "normal", craft="product")
    item = hypotheses.add(state, "Founders pay", "ten say so", by="leader", party=party)
    hypotheses.keep(state, item["id"])
    hypotheses.attach(state, item["id"], test=goal(host, "Ask them", state="done"))
    (row,) = board_rows.rows(state, root)
    assert row["party"] == party and row["leader"] == "taskmaster"                                      # a party with no leader of its own is led by the Taskmaster


def test_it_lies_after_the_projects_questions_in_the_rows_the_map_and_the_hand_lay(host):
    state, root = host.ideas.state_dir, host.ideas.root()
    item = hypotheses.add(state, "People want a sketch", "s")
    hypotheses.attach(state, item["id"], test=goal(host, "Interview", state="done"))
    project_questions.save_record(state, {"status": "waiting", "party": "", "leader": "orkmaster", "questions": [{"q": "Who is it for?"}], "at": "2000-01-01T00:00:00"})
    kinds = [r["kind"] for r in board_rows.rows(state, root)]
    assert kinds == ["project_q", "hypothesis"]
    assert [r["kind"] for r in board_map.build(root, state)["rows"]] == kinds
    needs = host.command("ideas.board")["needs_you"]
    assert [n["kind"] for n in needs if n["kind"] in ("project_q", "hypothesis")] == kinds
    assert needs[-1]["kind"] == "hypothesis"                                                          # it holds nothing back: after the goals' own
