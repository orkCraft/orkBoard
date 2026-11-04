"""Spec 144 C (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md; decisions §224.4, §225.2–3): a change to a spec asked of the Orkmaster. The words go to the leaders whose sections they
touch (the route, the cheaper tier), each rewrites its own section, the join says whether they agree, and the result is one record that waits in the hand as one Needs you row (`kind: "spec_change"`,
asked by the Orkmaster). *Accept* writes every section and one Decisions line and begins the look's wait again; *Talk more* and *Drop it* write nothing. The AI tools are faked as
tests/test_make_change.py fakes them: the keeper's call (`keeper.call`) is stubbed, never a real tool."""
from __future__ import annotations

import datetime as dt
import json
import threading
import time

import pytest

from orkboard.gui.board_host import CommandError
from orkboard.realm import event_log, idea_target, ideas, leader_change, spec_change, spec_sections
from tests.test_make_change import CHANGE, Model, _events, _goal, _party, design, host, tech  # noqa: F401  (fixtures)

SAID = "Make the winner stand out, nicer"
NOW = dt.datetime(2026, 11, 4, 12, 0, 0).timestamp()
TECH_DONE = {**CHANGE, "lines": ["changed Results — the winner first"]}
DESIGN = {"why": "A banner above the list.", "lines": ["new Winner banner — drawn above the list"], "change": [], "drop": [], "add": []}


@pytest.fixture
def clock(host, monkeypatch):
    class Clock:
        now = NOW
    monkeypatch.setattr(host.ideas, "_wall", lambda: Clock.now)
    monkeypatch.setattr(idea_target, "in_night", lambda spec, now=None: False)
    return Clock


def made(host, tech, design):
    """A goal whose spec is made: a plan not passed yet, a section for each of the two parties."""
    slug = _goal(host, tech, state="plan")
    root, st = host.ideas.root(), host.ideas.state_dir
    page = ideas.idea_page(root, slug)
    titles = {p: ideas.track_page(root, p).title for p in (tech, design)}
    spec_sections.arrange(page, {}, [(titles[tech], spec_sections.join({"Will be": "- changed Results — plain list", "Done when": "- The winner shows"})),
                                     (titles[design], spec_sections.join({"Will be": "- changed Banner — none", "Done when": "- A banner looks right"}))])
    ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
    ideas.edit_plan(st, slug, lambda p: p.update(passed_at=None, passed_by=None))
    return slug


def speaks(host, tech, design, route=None, join=None):
    """The tools faked by step: the Orkmaster's route, each leader's rewrite on its own step, the join."""
    def answer(call):
        if call["step"] == "route":
            return {"route": route if route is not None else [tech, design]}
        if call["step"] == "join":
            return join or {"agree": True, "line": "The banner and the list agree."}
        return TECH_DONE if call["key"] == f"goal:{tech}" else DESIGN
    return Model(host, answer)


def wait(host, slug):
    for _ in range(1000):
        if not host.ideas.keeper.busy(f"spec_change:{slug}"):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def ask(host, slug, text=SAID):
    got = host.command("ideas.spec_change", {"idea": slug, "text": text})
    wait(host, slug)
    return got


def rows(host, slug=None):
    return [n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "spec_change" and (slug is None or n["idea"] == slug)]


def page_text(host, slug):
    return ideas.idea_page(host.ideas.root(), slug).text()


def plan_of(host, slug):
    return ideas.plan(host.ideas.state_dir, slug)


# -- the preview (by code, nothing started) --------------------------------------------------------------------------------------------------

def test_the_preview_says_where_it_goes_and_what_it_costs_by_code_and_starts_nothing(host, tech, design):
    slug = made(host, tech, design)
    model = speaks(host, tech, design)
    got = host.command("ideas.spec_change_preview", {"idea": slug, "text": "Tech should show the winner first"})
    assert got["ok"] and got["id"] == "" and [p["party"] for p in got["parties"]] == [tech]
    both = host.command("ideas.spec_change_preview", {"idea": slug, "text": "Make it nicer"})
    assert [p["party"] for p in both["parties"]] == [tech, design] and [p["title"] for p in both["parties"]] == ["Tech", "Design"]
    assert both["estimate"]["calls"] == 4 and both["estimate"]["usd_high"] >= both["estimate"]["usd_low"] > 0      # the route, two rewrites, the join
    assert not model.calls and spec_change.read(host.ideas.state_dir, slug) == []
    assert host.command("ideas.spec_change_preview", {"idea": slug, "text": "@Design a banner"})["via"] == "change"


# -- a change asked of the Orkmaster -------------------------------------------------------------------------------------------------------

def test_a_change_touching_two_sections_goes_to_their_two_parties_and_comes_back_as_one_record(host, tech, design, clock):
    slug = made(host, tech, design)
    model = speaks(host, tech, design)
    got = ask(host, slug)
    assert got["ok"] and [p["party"] for p in got["parties"]] == [tech, design] and got["estimate"]["calls"] == 4
    (row,) = rows(host, slug)
    assert row["id"] == row["task"] == got["id"] and row["asker"] == "orkmaster" and row["status"] == "ready" and row["said"] == SAID and row["blocks"] is False
    assert [p["party"] for p in row["parties"]] == [tech, design] and row["agree"] == {"ok": True, "line": "The banner and the list agree."}
    tech_row, design_row = row["parties"]
    assert tech_row["before"]["lines"] == ["changed Results — plain list"] and tech_row["after"]["lines"] == TECH_DONE["lines"]
    assert design_row["before"]["lines"] == ["changed Banner — none"] and design_row["after"]["lines"] == DESIGN["lines"]
    assert [c["step"] for c in model.calls] == ["route", "plan", "plan", "join"] and [c["tools"] for c in model.calls] == [False] * 4
    assert model.calls[1]["key"] == f"goal:{tech}" and model.calls[2]["key"] == f"goal:{design}" and SAID in model.calls[1]["prompt"]
    assert "changed Results — plain list" in model.calls[1]["prompt"] and "Banner" in model.calls[0]["prompt"]
    assert isinstance(row["usd_low"], float) and row["calls"] == 4
    json.dumps(row)
    assert _events(host, event_log.SPEC_CHANGE_ASKED)[0]["ok"] is True
    assert "plain list" in page_text(host, slug), "nothing is written before the person accepts"


def test_only_the_parties_the_route_names_rewrite_and_a_lone_party_has_no_join(host, tech, design, clock):
    slug = made(host, tech, design)
    model = speaks(host, tech, design, route=[design])
    ask(host, slug)
    (row,) = rows(host, slug)
    assert [p["party"] for p in row["parties"]] == [design] and [c["step"] for c in model.calls] == ["route", "plan"] and row["agree"]["ok"] is True


def test_a_leader_with_nothing_to_change_stays_out_of_the_record(host, tech, design, clock):
    slug = made(host, tech, design)
    Model(host, lambda c: {"route": [tech, design]} if c["step"] == "route" else TECH_DONE if c["key"] == f"goal:{tech}" else {"why": "Nothing.", "lines": [], "change": [], "drop": [], "add": []})
    ask(host, slug)
    (row,) = rows(host, slug)
    assert row["status"] == "ready" and [p["party"] for p in row["parties"]] == [tech]


def test_a_failed_route_is_failed_with_the_tools_words(host, tech, design, clock):
    slug = made(host, tech, design)

    def out_of_room(call):
        raise RuntimeError("The tool is out of room until Mon 09:00")
    Model(host, out_of_room)
    ask(host, slug)
    (row,) = rows(host, slug)
    assert row["status"] == "failed" and "out of room" in row["text"] and "out of room" in row["error"]
    assert "plain list" in page_text(host, slug)
    with pytest.raises(CommandError, match="did not come"):
        host.command("ideas.spec_change_take", {"idea": slug, "id": row["id"]})
    assert not spec_change.open_on(host.ideas.state_dir, slug), "a failure holds nothing"


def test_at_one_leader_goes_to_the_single_leaders_change_as_built(host, tech, design):
    slug = made(host, tech, design)
    model = Model(host, TECH_DONE)
    got = host.command("ideas.spec_change", {"idea": slug, "text": "@Tech show the winner first"})
    for _ in range(500):
        if not host.ideas.keeper.busy(f"change:{slug}:{tech}"):
            break
        time.sleep(0.01)
    assert got["ok"] and got["via"] == "change" and [p["party"] for p in got["parties"]] == [tech]
    assert spec_change.read(host.ideas.state_dir, slug) == [] and [r["party"] for r in leader_change.read(host.ideas.state_dir, slug)] == [tech]
    assert [c["step"] for c in model.calls] == ["plan"], "no route: the person named the leader"


def test_refusals_are_in_plain_words(host, tech, design):
    slug = made(host, tech, design)
    model = speaks(host, tech, design)
    with pytest.raises(CommandError, match="Say what to change"):
        host.command("ideas.spec_change", {"idea": slug, "text": "  "})
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.spec_change", {"idea": "nope", "text": SAID})
    ideas.save_state(host.ideas.state_dir, slug, state="working")
    with pytest.raises(CommandError, match="at work"):
        host.command("ideas.spec_change", {"idea": slug, "text": SAID})
    ideas.save_state(host.ideas.state_dir, slug, state="done")
    with pytest.raises(CommandError, match="done: make a new goal"):
        host.command("ideas.spec_change", {"idea": slug, "text": SAID})
    assert not model.calls and spec_change.read(host.ideas.state_dir, slug) == []


# -- the acts -------------------------------------------------------------------------------------------------------------------------------

def test_accept_writes_both_sections_and_one_decisions_line_and_the_wait_begins_again(host, tech, design, clock):
    host.command("ideas.board_set", {"look_wait": "2h"})
    slug = made(host, tech, design)
    speaks(host, tech, design)
    ideas.edit_plan(host.ideas.state_dir, slug, lambda p: p.update(look_until=NOW - 5000, look_done=True))      # an earlier look was given
    got = ask(host, slug)
    done = host.command("ideas.spec_change_take", {"idea": slug, "id": got["id"], "via": "idea"})
    assert done["ok"] and done["starts"] == "wait"
    text = page_text(host, slug)
    assert "changed Results — the winner first" in text and "new Winner banner — drawn above the list" in text and "plain list" not in text and "changed Banner — none" not in text
    assert text.count("The person decided, Tech, Design: " + SAID) == 1
    plan = plan_of(host, slug)
    assert plan["look_until"] == NOW + 7200 and plan["start_at"] == "2026-11-04T14:00:00" and "look_done" not in plan and plan.get("passed_at") is None
    assert spec_change.read(host.ideas.state_dir, slug) == [] and rows(host, slug) == []
    (answered,) = _events(host, event_log.SPEC_CHANGE_ANSWERED)
    assert answered["answer"] == "take" and answered["parties"] == [tech, design]
    ideas_tasks = {t["id"]: t for t in plan["tasks"]}
    assert ideas_tasks["k2"]["title"] == "Winner first", "the leader's plan change for its tasks not started is taken too"
    with pytest.raises(CommandError, match="No change waits"):
        host.command("ideas.spec_change_take", {"idea": slug, "id": got["id"]})


def test_accept_with_the_limits_low_waits_for_the_reset(host, tech, design, clock, monkeypatch):
    host.command("ideas.board_set", {"look_wait": "30m"})
    slug = made(host, tech, design)
    speaks(host, tech, design)
    reset = NOW + 5 * 3600
    monkeypatch.setattr(idea_target, "reserve_held", lambda *a, **k: reset)
    got = ask(host, slug)
    assert host.command("ideas.spec_change_take", {"idea": slug, "id": got["id"]})["starts"] == "reset"
    assert plan_of(host, slug)["look_until"] == reset


def test_accept_with_no_wait_decides_the_plan_at_once(host, tech, design, clock, monkeypatch):
    host.command("ideas.board_set", {"look_wait": "none"})
    slug = made(host, tech, design)
    speaks(host, tech, design)
    started = []
    monkeypatch.setattr(host.ideas, "pass_plan", lambda s, by, args=None: started.append((s, by)))
    got = ask(host, slug)
    assert host.command("ideas.spec_change_take", {"idea": slug, "id": got["id"]})["starts"] in ("now", "")
    assert "look_until" not in plan_of(host, slug)


def test_drop_it_changes_no_file_and_talk_more_gives_the_words_back(host, tech, design, clock):
    slug = made(host, tech, design)
    speaks(host, tech, design)
    before = (page_text(host, slug), plan_of(host, slug))
    got = ask(host, slug)
    assert host.command("ideas.spec_change_drop", {"idea": slug, "id": got["id"]}) == {"ok": True}
    assert (page_text(host, slug), plan_of(host, slug)) == before and rows(host, slug) == []
    again = ask(host, slug)
    more = host.command("ideas.spec_change_more", {"idea": slug, "id": again["id"]})
    assert more == {"ok": True, "text": SAID} and (page_text(host, slug), plan_of(host, slug)) == before and rows(host, slug) == []
    assert [e["answer"] for e in _events(host, event_log.SPEC_CHANGE_ANSWERED)] == ["drop", "more"]
    with pytest.raises(CommandError, match="No change waits"):
        host.command("ideas.spec_change_drop", {"idea": slug, "id": again["id"]})


# -- the look's wait while it is changed (A.4) --------------------------------------------------------------------------------------------

def test_while_the_record_is_asking_or_ready_the_looks_tick_skips_the_goal(host, tech, design, clock):
    host.command("ideas.board_set", {"look_wait": "30m"})
    slug = made(host, tech, design)
    ideas.edit_plan(host.ideas.state_dir, slug, lambda p: p.update(look_until=NOW + 1800))
    go, entered = threading.Event(), threading.Event()

    def slow(call):
        if call["step"] == "route":
            entered.set()
            go.wait(5)
            return {"route": [tech]}
        return TECH_DONE
    Model(host, slow)
    got = host.command("ideas.spec_change", {"idea": slug, "text": SAID})
    assert entered.wait(5) and [r["status"] for r in spec_change.read(host.ideas.state_dir, slug)] == ["asking"]
    (row,) = rows(host, slug)
    assert row["status"] == "asking"
    assert host.ideas.look_tick(NOW + 9999) == 0 and plan_of(host, slug)["look_until"] == NOW + 1800
    with pytest.raises(CommandError, match="waits: answer it first"):
        host.command("ideas.spec_change", {"idea": slug, "text": "Again"})
    go.set()
    wait(host, slug)
    assert host.ideas.look_tick(NOW + 9999) == 0, "ready: it is still held until the person answers"
    host.command("ideas.spec_change_drop", {"idea": slug, "id": got["id"]})
    assert host.ideas.look_tick(NOW + 9999) == 1
