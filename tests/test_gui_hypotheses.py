"""Spec 116 C (docs/specs/116-hypotheses-on-products-tree.md §4; decisions §194): the hypotheses of Product's map on the host. `ideas.hypotheses` (each with its state as shown and its goals' title,
element and place), `ideas.hypothesis_set` (the person's, open at once), `_keep`, `_drop`, `_attach` (a goal that rests on it, a goal that tests it), `_evidence`, `_judge` (held and refuted write a
numbered decision with no goal and the row *Did it hold?* leaves; unsure keeps it open) and `ideas.hypotheses_propose` (the keeper's, called only where it is). Refusals in plain words. The keeper's
proposal (Part B) is stubbed."""
from __future__ import annotations

import subprocess
import sys

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import decisions_log, hypotheses, ideas, opportunity_tree as tree

COMMANDS = {"ideas.hypotheses", "ideas.hypothesis_set", "ideas.hypothesis_keep", "ideas.hypothesis_drop", "ideas.hypothesis_attach", "ideas.hypothesis_evidence", "ideas.hypothesis_judge",
            "ideas.hypotheses_propose"}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    h.ideas.root()                                                     # the Board's tree stands: a decision is committed to dev
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def make_goal(host, title, state="", element=""):
    slug = ideas.add_idea(host.ideas.root(), title, "general", host.ideas.state_dir)
    changes = {**({"state": state} if state else {}), **({"element": element} if element else {})}
    if changes:
        ideas.save_state(host.ideas.state_dir, slug, **changes)
    return slug


def hold(host, text="People want a sketch first", signal="most ask for one within a minute", **more):
    return host.command("ideas.hypothesis_set", {"text": text, "signal": signal, **more})["item"]


def with_test(host, state="done", **more):
    """An open hypothesis with one test goal in `state`."""
    item = hold(host, **more)
    goal = make_goal(host, "Interview five founders", state=state, element="ice")
    host.command("ideas.hypothesis_attach", {"id": item["id"], "test": goal})
    return item["id"], goal


def hand(host):
    return [n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "hypothesis"]


def refused(host, command, args, match):
    with pytest.raises(CommandError, match=match):
        host.command(command, args)


def test_the_commands_are_in_the_table(host):
    assert COMMANDS <= set(host.commands)


# -- read and keep ----------------------------------------------------------------------------------------------------------------------------

def test_nothing_is_kept_at_first(host):
    assert host.command("ideas.hypotheses", {}) == {"items": [], "party": "", "proposing": False, "status": ""}


def test_the_person_s_hypothesis_is_open_at_once_and_its_words_change_with_its_id_staying(host):
    got = host.command("ideas.hypothesis_set", {"text": " People  want a sketch first ", "signal": "most ask for one", "axis": "desirable"})
    item = got["item"]
    assert got["ok"] is True and item["id"] == "people-want-a-sketch-first" and item["state"] == "open" and item["by"] == "person" and item["axis"] == "desirable" and item["tests"] == [] and item["rests"] == []
    again = host.command("ideas.hypothesis_set", {"id": item["id"], "text": "People want a sketch before anything"})["item"]
    assert again["id"] == item["id"] and again["text"] == "People want a sketch before anything" and again["signal"] == "most ask for one"
    assert host.command("ideas.hypotheses", {})["items"] == [again]


def test_a_hypothesis_on_a_job_names_a_job_of_the_tree(host):
    tree.keep(host.ideas.state_dir, [{"text": "Cut the time to a first sketch"}], [{"when": "I start", "want": "see a sketch", "so": "judge it", "segment": "founders"},
                                                                                     {"when": "I finish", "want": "share it", "so": "show it", "segment": "founders"},
                                                                                     {"when": "I doubt", "want": "compare two", "so": "choose", "segment": "founders"}], "person")
    job = tree.read(host.ideas.state_dir)["jobs"][0]["id"]
    assert hold(host, on=job)["on"] == job
    refused(host, "ideas.hypothesis_set", {"text": "Another", "signal": "s", "on": "no-such-job"}, "That job is gone")


def test_a_proposed_hypothesis_is_kept_or_dropped(host):
    proposed = hypotheses.add(host.ideas.state_dir, "Founders pay for it", "ten say so", by="leader", party="product")
    assert host.command("ideas.hypotheses", {})["items"][0]["state"] == "proposed"
    got = host.command("ideas.hypothesis_keep", {"id": proposed["id"]})
    assert got["ok"] is True and got["item"]["state"] == "open"
    other = hypotheses.add(host.ideas.state_dir, "Teams want sharing", "they ask", by="leader", party="product")
    assert host.command("ideas.hypothesis_drop", {"id": other["id"]}) == {"ok": True}
    assert [i["id"] for i in host.command("ideas.hypotheses", {})["items"]] == [proposed["id"]]


def test_a_change_is_published_so_the_page_refreshes(host):
    seen = []
    host.ideas.host.publish = lambda topic, **data: seen.append(topic)
    hold(host)
    assert seen


# -- the goals: rests on, tests, and the state as shown ---------------------------------------------------------------------------------------

def test_a_goal_rests_on_a_hypothesis_and_a_test_tests_it_each_with_its_title_element_and_place(host):
    item = hold(host)
    rests = make_goal(host, "Dark mode", state="working", element="lava")
    test = make_goal(host, "Interview five founders", element="ice")
    host.command("ideas.hypothesis_attach", {"id": item["id"], "goal": rests})
    got = host.command("ideas.hypothesis_attach", {"id": item["id"], "test": test})["item"]
    assert got["rests"] == [{"slug": rests, "title": "Dark mode", "element": "lava", "place": "work"}]
    assert got["tests"] == [{"slug": test, "title": "Interview five founders", "element": "ice", "place": "line"}]
    assert got["state"] == "testing"                                                                  # a test is in line: shown as testing, kept as open
    assert hypotheses.read(host.ideas.state_dir)["items"][0]["state"] == "open"
    ideas.save_state(host.ideas.state_dir, test, state="done")
    assert host.command("ideas.hypotheses", {})["items"][0]["state"] == "open"


def test_a_test_moves_to_another_hypothesis_and_an_empty_id_takes_it_off(host):
    a, b = hold(host, "Claim a", "sa"), hold(host, "Claim b", "sb")
    goal = make_goal(host, "An experiment")
    host.command("ideas.hypothesis_attach", {"id": a["id"], "test": goal})
    host.command("ideas.hypothesis_attach", {"id": b["id"], "test": goal})
    items = {i["id"]: i for i in host.command("ideas.hypotheses", {})["items"]}
    assert items[a["id"]]["tests"] == [] and [g["slug"] for g in items[b["id"]]["tests"]] == [goal]
    assert host.command("ideas.hypothesis_attach", {"id": "", "test": goal}) == {"ok": True, "item": None}
    assert all(i["tests"] == [] for i in host.command("ideas.hypotheses", {})["items"])


def test_a_goal_gone_from_the_board_is_left_out_of_the_goals_shown(host):
    item = hold(host)
    goal = make_goal(host, "Soon gone")
    host.command("ideas.hypothesis_attach", {"id": item["id"], "test": goal})
    ideas.drop(host.ideas.root(), goal, host.ideas.state_dir)
    assert host.command("ideas.hypotheses", {})["items"][0]["tests"] == []


def test_evidence_is_a_line_with_where_from(host):
    item = hold(host)
    got = host.command("ideas.hypothesis_evidence", {"id": item["id"], "text": "Four of five asked for it", "ref": "interview-five"})["item"]
    assert [(e["text"], e["ref"]) for e in got["evidence"]] == [("Four of five asked for it", "interview-five")]


# -- judged ------------------------------------------------------------------------------------------------------------------------------------

def test_the_row_comes_when_the_last_test_is_done_and_judging_it_held_writes_the_next_numbered_decision_and_the_row_leaves(host):
    host.ideas.keeper.write_decision("An earlier decision", "Why: before.", host.ideas._decision_tree())
    item_id, goal = with_test(host, state="working")
    host.command("ideas.hypothesis_evidence", {"id": item_id, "text": "Four of five asked for it", "ref": goal})
    assert hand(host) == []
    ideas.save_state(host.ideas.state_dir, goal, state="done")
    (row,) = hand(host)
    assert row["id"] == item_id and row["tests"] == [{"slug": goal, "title": "Interview five founders"}] and row["blocks"] is False
    got = host.command("ideas.hypothesis_judge", {"id": item_id, "state": "held", "why": "Clear enough to build on"})
    assert got["ok"] is True and got["decision"]["number"] == 2 and got["decision"]["commit"] and got["item"]["state"] == "held"
    assert got["item"]["verdict"]["decision"] == 2 and got["item"]["verdict"]["why"] == "Clear enough to build on"
    assert hand(host) == []
    log = git(host.repo_root, "show", "dev:docs/decisions.md")
    assert decisions_log.headings(log)[-1].split(" (")[0] == "2. Hypothesis held: People want a sketch first"
    entry = log[log.index("## 2. "):]
    assert "the person and Orkboard)" in entry.splitlines()[0]
    assert "Signal: most ask for one within a minute" in entry and "- Four of five asked for it (" + goal + ")" in entry
    assert "Tests: Interview five founders" in entry and "Why: Clear enough to build on" in entry
    assert git(host.repo_root, "log", "-1", "--format=%s", "dev") == "board: decision 2 — Hypothesis held: People want a sketch first"


def test_refuted_writes_its_decision_too_with_the_title_cut_to_a_decisions_length(host):
    item_id, goal = with_test(host, text="x" * 190)
    ideas.save_state(host.ideas.state_dir, goal, state="done")
    got = host.command("ideas.hypothesis_judge", {"id": item_id, "state": "refuted"})
    assert got["item"]["state"] == "refuted" and got["decision"]["number"] == 1
    (heading,) = decisions_log.headings(git(host.repo_root, "show", "dev:docs/decisions.md"))
    assert heading.startswith("1. Hypothesis refuted: xxx") and len(heading.split(" (")[0]) <= 123
    assert "Why:" not in git(host.repo_root, "show", "dev:docs/decisions.md")                         # no why given: no line for it


def test_not_sure_yet_keeps_it_open_with_the_why_as_evidence_and_writes_nothing(host):
    item_id, goal = with_test(host)
    got = host.command("ideas.hypothesis_judge", {"id": item_id, "state": "unsure", "why": "Only two of five answered"})
    assert got["ok"] is True and "decision" not in got and got["item"]["state"] == "open" and got["item"]["verdict"] == {}
    assert [e["text"] for e in got["item"]["evidence"]] == ["Only two of five answered"]
    assert not decisions_log.path(host.repo_root).exists() and "decisions.md" not in git(host.repo_root, "ls-tree", "-r", "--name-only", "dev")
    assert len(hand(host)) == 1                                                                       # it is still due: the answer was not final


def test_judging_without_a_decision_numbers_it_after_the_existing_ones_each_time(host):
    first, g1 = with_test(host, text="First claim")
    second, g2 = with_test(host, text="Second claim")
    for g in (g1, g2):
        ideas.save_state(host.ideas.state_dir, g, state="done")
    assert host.command("ideas.hypothesis_judge", {"id": second, "state": "held"})["decision"]["number"] == 1
    assert host.command("ideas.hypothesis_judge", {"id": first, "state": "refuted"})["decision"]["number"] == 2
    assert [h.split(". ", 1)[0] for h in decisions_log.headings(git(host.repo_root, "show", "dev:docs/decisions.md"))] == ["1", "2"]


def test_a_verdict_is_refused_in_plain_words_and_writes_nothing(host):
    refused(host, "ideas.hypothesis_judge", {"id": "nobody", "state": "held"}, "That hypothesis is gone")
    proposed = hypotheses.add(host.ideas.state_dir, "Founders pay for it", "ten say so", by="leader", party="product")
    refused(host, "ideas.hypothesis_judge", {"id": proposed["id"], "state": "held"}, "Keep the hypothesis before judging it")
    item = hold(host)
    refused(host, "ideas.hypothesis_judge", {"id": item["id"], "state": "maybe"}, "held, was refuted or is not sure yet")
    host.command("ideas.hypothesis_judge", {"id": item["id"], "state": "held"})
    refused(host, "ideas.hypothesis_judge", {"id": item["id"], "state": "refuted"}, "judged already")
    assert len(decisions_log.headings(git(host.repo_root, "show", "dev:docs/decisions.md"))) == 1       # the one verdict, once


def test_a_decision_that_cannot_be_written_leaves_the_hypothesis_open(host, monkeypatch):
    from orkboard.core.idea_keeper import KeeperError

    def broken(title, body, tree=None):
        raise KeeperError("The decision could not be written: disk full")

    item = hold(host)
    monkeypatch.setattr(host.ideas.keeper, "write_decision", broken)
    refused(host, "ideas.hypothesis_judge", {"id": item["id"], "state": "held"}, "disk full")
    assert hypotheses.read(host.ideas.state_dir)["items"][0]["state"] == "open"


# -- refusals ----------------------------------------------------------------------------------------------------------------------------------

def test_refusals_are_in_plain_words(host):
    refused(host, "ideas.hypothesis_set", {"text": "", "signal": "s"}, "says what we believe")
    refused(host, "ideas.hypothesis_set", {"text": "t", "signal": ""}, "what we'll know when")
    refused(host, "ideas.hypothesis_set", {"text": "t", "signal": "s", "axis": "loud"}, "what people want")
    refused(host, "ideas.hypothesis_set", {"id": "nobody", "text": "t"}, "That hypothesis is gone")
    refused(host, "ideas.hypothesis_keep", {"id": "nobody"}, "That hypothesis is gone")
    refused(host, "ideas.hypothesis_drop", {"id": "nobody"}, "That hypothesis is gone")
    refused(host, "ideas.hypothesis_evidence", {"id": "nobody", "text": "x"}, "That hypothesis is gone")
    item = hold(host)
    refused(host, "ideas.hypothesis_evidence", {"id": item["id"], "text": " "}, "Evidence is a line")
    refused(host, "ideas.hypothesis_attach", {"id": item["id"]}, "Say which goal")
    refused(host, "ideas.hypothesis_attach", {"id": item["id"], "test": "no-such-goal"}, "That goal is gone")
    refused(host, "ideas.hypothesis_attach", {"id": "nobody", "goal": make_goal(host, "A goal")}, "That hypothesis is gone")
    refused(host, "ideas.hypothesis_set", {"text": 3, "signal": "s"}, "text is not text")


def test_seven_open_at_most(host):
    for n in range(7):
        hold(host, f"Claim {n}", f"signal {n}")
    refused(host, "ideas.hypothesis_set", {"text": "One too many", "signal": "s"}, "7 hypotheses are open")


# -- the leaders' proposal ----------------------------------------------------------------------------------------------------------------------

def test_without_the_keepers_proposal_nothing_is_asked_and_it_says_why(host):
    assert not hasattr(host.ideas.keeper, "hypotheses_propose")
    got = host.command("ideas.hypotheses_propose", {})
    assert got["ok"] is True and got["asked"] is False and got["why"]


def test_the_keepers_proposal_is_asked_through_the_command_and_its_refusals_are_not_the_callers(host):
    from orkboard.core.idea_keeper import KeeperError

    calls = []
    host.ideas.keeper.hypotheses_propose = lambda: calls.append(1) or True
    assert host.command("ideas.hypotheses_propose", {}) == {"ok": True, "asked": True} and calls == [1]

    def refuse():
        raise KeeperError("Today's spend limit is reached: the keeper waits")

    host.ideas.keeper.hypotheses_propose = refuse
    assert host.command("ideas.hypotheses_propose", {}) == {"ok": True, "asked": False, "why": "Today's spend limit is reached: the keeper waits"}
