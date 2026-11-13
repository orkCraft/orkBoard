"""Spec 128 E (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md; decisions §206.5): the bubble's *Make it a change*. The person's words to a leader about a goal that is
agreed or at work: the leader replans its part (one call, its tasks not started, its own lines of the spec) and the result waits in the hand as a decision with the plan now and
proposed and its price (`ideas.change` → the Needs you row `leader_change`); *Accept* applies it and writes it down as the person's, *Keep the spec* drops it; a Design leader
answers three looks. The model call is stubbed (`keeper.call`)."""
from __future__ import annotations

import json
import sys
import threading
import time

import pytest

from orkboard.core import idea_keeper
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.gui.ideas_change import change_commands
from orkboard.realm import event_log, goal_team, ideas, leader_change, library, spec_sections

SAID = "Show the winner first on the results screen"
CHANGE = {"why": "Results lists the winner first, and rounds keep their score.",
          "lines": ["changed Results — the winner first", "new Winner — a banner above the list"],
          "change": [{"id": "k2", "title": "Winner first", "brief": "Put the winner at the top of the results list.", "tier": "laborer"},
                     {"id": "k5", "title": "Another party's task", "brief": "It is not Tech's: it stays."}],
          "drop": ["k3"],
          "add": [{"key": "n1", "title": "Winner banner", "brief": "Draw a banner for the winner.", "tier": "warrior", "after": ["k2"]}]}
LOOKS = {"why": "Three ways the winner could show.", "looks": [
    {"name": "Banner", "why": "A banner on top.", "lines": ["changed Results — a banner for the winner"]},
    {"name": "Crown", "why": "A crown on the first row.", "lines": ["changed Results — a crown on the first row"]},
    {"name": "Podium", "why": "A podium of three.", "lines": ["changed Results — a podium of three", "new Podium — three steps"]}]}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    assert set(change_commands(h.ideas)) == {"ideas.change", "ideas.change_take", "ideas.change_keep"} <= set(h.commands)
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
    return _party(host, "Design", "product-designer", ["ui-kit"], "design")


class Model:
    """The keeper's call stubbed: `answer` the JSON (or a callable of the call) every call gets; `calls` every call made."""

    def __init__(self, host, answer):
        self.host, self.calls, self.answer = host, [], answer
        host.ideas.keeper.call = self

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        self.calls.append({"tier": tier, "prompt": prompt, "step": k.measure()["step"], "key": getattr(k._tls, "key", ""), "tools": getattr(k._tls, "tools", True)})
        answer = self.answer(self.calls[-1]) if callable(self.answer) else self.answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.02, 100, ""


def _goal(host, party, rows=(("k1", "merged", [], ""), ("k2", "ready", ["k1"], "grunt"), ("k3", "waiting", ["k2"], "grunt"), ("k4", "review", ["k1"], "grunt"), ("k5", "ready", [], "copywriter")),
          state="working", will=("changed Results — plain list",)):
    """An idea in the party, its plan passed and at work (`rows`: id, state, after, role), the party's own section holding `will` as its *Will be*."""
    root, st = host.ideas.root(), host.ideas.state_dir
    slug = ideas.add_idea(root, "show the winner", party, st)
    page = ideas.idea_page(root, slug)
    title = ideas.track_page(root, party).title
    spec_sections.arrange(page, {}, [(title, spec_sections.join({"Will be": "\n".join(f"- {w}" for w in will), "Done when": "- The winner shows"}))])
    ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
    tasks = []
    for tid, tstate, after, role in rows:
        t = idea_keeper._task(tid, f"Task {tid}", f"Do {tid}", "code", "warrior", list(after))
        t.update(state=tstate, role=role, **({"started": "2026-10-23T10:00:00"} if tstate not in ("waiting", "ready", "held") else {}))
        tasks.append(t)
    data = {"idea": slug, "made_at": "2026-10-23T09:00:00", "passed_at": "2026-10-23T09:30:00", "passed_by": "person", "estimate": idea_keeper.estimate(tasks), "todos": [], "tasks": tasks}
    ideas._write_json(ideas.state_folder(st, slug) / "plan.json", data)
    ideas.save_state(st, slug, state=state)
    runner = host.ideas.runner(need=True)                      # made first, so that it does not take the goal up, and starts nothing
    runner._launch = lambda s, t: None
    return slug


def _wait(host, slug, party):
    for _ in range(1000):
        if not host.ideas.keeper.busy(f"change:{slug}:{party}"):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _ask(host, slug, party, text=SAID, **more):
    got = host.command("ideas.change", {"idea": slug, "party": party, "text": text, **more})
    _wait(host, slug, party)
    return got


def _rows(host, slug=None):
    return [n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "leader_change" and (slug is None or n["idea"] == slug)]


def _tasks(host, slug):
    return {t["id"]: t for t in ideas.plan(host.ideas.state_dir, slug)["tasks"]}


def _events(host, event):
    return [r for r in event_log.read(host.ideas.host.repo_root) if r["event"] == event]


# -- the refusals -----------------------------------------------------------------------------------------------------------------------

def test_no_words_a_gone_goal_or_party_a_goal_not_agreed_or_done_and_the_demo_are_refused_in_plain_words(host, tech, monkeypatch):
    slug = _goal(host, tech)
    model = Model(host, CHANGE)
    for text in ("", "  \n "):
        with pytest.raises(CommandError, match="Say what to change"):
            host.command("ideas.change", {"idea": slug, "party": tech, "text": text})
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.change", {"idea": "nope", "party": tech, "text": SAID})
    with pytest.raises(CommandError, match="That party is gone"):
        host.command("ideas.change", {"idea": slug, "party": "nobody", "text": SAID})
    ideas.save_state(host.ideas.state_dir, slug, state="done")
    with pytest.raises(CommandError, match="done: make a new goal"):
        host.command("ideas.change", {"idea": slug, "party": tech, "text": SAID})
    ideas.save_state(host.ideas.state_dir, slug, state="raw")
    with pytest.raises(CommandError, match="not agreed yet"):
        host.command("ideas.change", {"idea": slug, "party": tech, "text": SAID})
    ideas.save_state(host.ideas.state_dir, slug, state="decided")
    monkeypatch.setattr(host.ideas.keeper, "demo", True)
    with pytest.raises(CommandError, match="The demo runs no model"):
        host.command("ideas.change", {"idea": slug, "party": tech, "text": SAID})
    assert not model.calls and leader_change.read(host.ideas.state_dir, slug) == [] and _rows(host) == []      # nothing begun, nothing kept


# -- a change asked ---------------------------------------------------------------------------------------------------------------------

def test_a_change_asked_makes_a_decision_row_with_the_plan_now_and_proposed_the_lines_and_the_price(host, tech):
    slug = _goal(host, tech)
    model = Model(host, CHANGE)
    got = _ask(host, slug, tech, part="Results")
    (row,) = _rows(host, slug)
    assert got["ok"] and got["id"] == row["id"] == row["task"] and row["goal"] == row["party"] == tech and row["part"] == "Results" and row["said"] == SAID
    assert row["shape"] == "plan" and row["status"] == "ready" and row["text"] == CHANGE["why"] and row["blocks"] is False
    # now: the party's tasks not started only (k1 merged, k4 at review stay as they are; k5 is the Product party's)
    assert row["before"]["tasks"] == [{"id": "k2", "title": "Task k2", "short": row["before"]["tasks"][0]["short"], "op": "change"},
                                      {"id": "k3", "title": "Task k3", "short": row["before"]["tasks"][1]["short"], "op": "drop"}]
    assert [(t["id"], t["title"], t["op"]) for t in row["after"]["tasks"]] == [("k2", "Winner first", "change"), ("", "Winner banner", "add")]
    assert row["before"]["lines"] == ["changed Results — plain list"] and row["after"]["lines"] == CHANGE["lines"]
    assert isinstance(row["usd_low"], float) and isinstance(row["usd_high"], float) 
    json.dumps(row)
    # one call on the party's own step, no tools, the person's words, its part, its map and its tasks in it; another party's task is not offered
    (call,) = model.calls
    assert call["step"] == "plan" and call["key"] == f"goal:{tech}" and call["tools"] is False
    assert SAID in call["prompt"] and "this part of the goal's change: Results" in call["prompt"] and "Task k2" in call["prompt"] and "Task k5" not in call["prompt"].split("Your tasks not started")[1] and "Task k5" in call["prompt"].split("Your tasks not started")[0]
    assert "changed Results — plain list" in call["prompt"]
    assert _events(host, event_log.LEADER_CHANGE_ASKED)[0]["ok"] is True
    assert ideas.plan(host.ideas.state_dir, slug)["tasks"][1]["title"] == "Task k2"             # nothing is applied yet
    assert next(n for n in host.command("ideas.board")["ideas"] if n["slug"] == slug)["state"] == "working"       # the goal at work does not move


def test_a_change_waits_as_asking_with_no_row_until_the_leader_has_answered(host, tech):
    slug = _goal(host, tech)
    go, entered = threading.Event(), threading.Event()

    def slow(_call):
        entered.set()
        go.wait(5)
        return CHANGE

    Model(host, slow)
    host.command("ideas.change", {"idea": slug, "party": tech, "text": SAID})
    assert entered.wait(5) and [r["status"] for r in leader_change.read(host.ideas.state_dir, slug)] == ["asking"] and _rows(host) == []
    with pytest.raises(CommandError, match="on a change of this goal already"):
        host.command("ideas.change", {"idea": slug, "party": tech, "text": "Again"})
    go.set()
    _wait(host, slug, tech)
    assert len(_rows(host)) == 1


# -- Accept and Keep the spec --------------------------------------------------------------------------------------------------------------

def test_accept_applies_the_plan_change_to_its_tasks_writes_its_lines_into_its_section_and_records_the_persons_decision(host, tech):
    slug = _goal(host, tech)
    Model(host, CHANGE)
    _ask(host, slug, tech, part="Results")
    (row,) = _rows(host, slug)
    got = host.command("ideas.change_take", {"idea": slug, "id": row["id"], "via": "hand"})
    assert got["ok"] and (got["added"], got["changed"], got["dropped"]) == (1, 1, 1)
    tasks = _tasks(host, slug)
    assert tasks["k2"]["title"] == "Winner first" and tasks["k2"]["brief"].startswith("Put the winner") and "k3" not in tasks and tasks["k6"]["title"] == "Winner banner"
    assert tasks["k5"]["title"] == "Task k5" and tasks["k4"]["state"] == "review" and tasks["k1"]["state"] == "merged"      # another party's, at work and merged: as they were
    page = ideas.idea_page(host.ideas.root(), slug)
    title = ideas.track_page(host.ideas.root(), tech).title
    sec = dict(spec_sections.sections_of(page))[title]
    assert spec_sections.items(spec_sections.split(sec)["Will be"]) == CHANGE["lines"] and spec_sections.split(sec)["Done when"] == "- The winner shows"
    decision = page.section("Decisions")
    assert "The person decided" in decision and "Results" in decision and SAID in decision
    assert _rows(host) == [] and leader_change.read(host.ideas.state_dir, slug) == []
    (ev,) = _events(host, event_log.LEADER_CHANGE_ANSWERED)
    assert ev["take"] is True and ev["changed_n"] == 1 and ev["via"] == "hand" and ev["wrote"] is True
    with pytest.raises(CommandError, match="No change waits"):
        host.command("ideas.change_take", {"idea": slug, "id": row["id"]})


def test_keep_the_spec_drops_the_change_and_nothing_else_changes(host, tech):
    slug = _goal(host, tech)
    Model(host, CHANGE)
    _ask(host, slug, tech)
    (row,) = _rows(host, slug)
    plan, page = ideas.plan(host.ideas.state_dir, slug), ideas.idea_page(host.ideas.root(), slug).text()
    assert host.command("ideas.change_keep", {"idea": slug, "id": row["id"]}) == {"ok": True}
    assert _rows(host) == [] and ideas.plan(host.ideas.state_dir, slug) == plan and ideas.idea_page(host.ideas.root(), slug).text() == page
    (ev,) = _events(host, event_log.LEADER_CHANGE_ANSWERED)
    assert ev["take"] is False and ev["party"] == tech
    with pytest.raises(CommandError, match="No change waits"):
        host.command("ideas.change_keep", {"idea": slug, "id": row["id"]})


# -- Design: three looks -----------------------------------------------------------------------------------------------------------------

def test_a_design_leader_answers_three_looks_and_the_one_taken_is_written_as_its_lines(host, design):
    slug = _goal(host, design, rows=(("k1", "ready", [], "ui-kit"),))
    model = Model(host, LOOKS)
    _ask(host, slug, design, part="Results")
    (row,) = _rows(host, slug)
    assert row["shape"] == "looks" and [x["name"] for x in row["looks"]] == ["Banner", "Crown", "Podium"] and [x["key"] for x in row["looks"]] == ["1", "2", "3"]
    assert row["text"] == LOOKS["why"] and "Offer exactly 3 looks" in model.calls[0]["prompt"] and "Winner first" not in model.calls[0]["prompt"]
    with pytest.raises(CommandError, match="Pick a look"):
        host.command("ideas.change_take", {"idea": slug, "id": row["id"]})
    assert host.command("ideas.change_take", {"idea": slug, "id": row["id"], "look": "3"})["ok"]
    sec = dict(spec_sections.sections_of(ideas.idea_page(host.ideas.root(), slug)))[ideas.track_page(host.ideas.root(), design).title]
    assert spec_sections.items(spec_sections.split(sec)["Will be"]) == LOOKS["looks"][2]["lines"]
    assert "look Podium" in ideas.idea_page(host.ideas.root(), slug).section("Decisions") and _events(host, event_log.LEADER_CHANGE_ANSWERED)[0]["look"] == "3"
    assert ideas.plan(host.ideas.state_dir, slug)["tasks"][0]["title"] == "Task k1"                      # looks replan no task

