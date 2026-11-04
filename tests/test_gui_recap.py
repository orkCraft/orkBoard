"""Spec 42 A (docs/specs/42-coming-back.md §1.2, Tests → A): `ideas.recap` on the host and the phone, and `opened`'s new
`what` and `via`."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import event_log, ideas


@pytest.fixture
def host(fake_repo) -> Orkboard:
    return Orkboard(fake_repo)


def _ms(hours_ago: float) -> int:
    return int((time.time() - hours_ago * 3600) * 1000)


def _merge(host, hours_ago: float) -> str:
    root, state = host.ideas.root(), host.ideas.state_dir
    goal, _new = ideas.save_goal(root, None, "Offline mode", "About it", None, "normal")
    slug = ideas.add_idea(root, "Retry queue", goal, state)
    ideas.save_state(state, slug, state="done")
    event_log.record(Path(host.ideas.host.repo_root), "task_state", idea=slug, task="k1", state="merged", was="review", round=1)
    return slug


def test_the_recap_is_the_hosts_and_a_phones_and_needs_a_project():
    assert BoardPhone.allowed(Orkboard(), "ideas.recap", {})
    with pytest.raises(CommandError, match="Open a folder first"):
        Orkboard().command("ideas.recap", {"since": _ms(9)})


def test_the_answer_carries_the_period_and_what_waits(host):
    slug = _merge(host, 1)
    got = host.command("ideas.recap", {"since": _ms(9)})
    json.dumps(got)
    assert got["hours"] == 9 and got["into"] == "dev"
    assert [i["slug"] for i in got["merged"]["ideas"]] == [slug] and got["merged"]["ideas"][0]["done"] is True
    assert got["merged"]["tasks"] == 1 and got["empty"] is False and got["waits"] == {"you": 0, "review": 0}


def test_since_is_required_clamped_to_thirty_days_and_never_ahead(host):
    for bad in ({}, {"since": "yesterday"}, {"since": True}):
        with pytest.raises(CommandError, match="last look"):
            host.command("ideas.recap", bad)
    with pytest.raises(CommandError, match="`since` is ahead of now"):
        host.command("ideas.recap", {"since": _ms(-2)})
    assert host.command("ideas.recap", {"since": _ms(24 * 90)})["hours"] == 24 * 30


def test_opened_takes_the_new_what_and_via(host):
    for what in ("recap", "flag", "week", "push"):
        host.command("ideas.log", {"event": "opened", "what": what, "ref": "x"})
    for via in ("recap", "week", "flags", "push"):
        host.command("ideas.log", {"event": "opened", "what": "idea", "ref": "x", "via": via})
    with pytest.raises(CommandError, match="`what` is one of"):
        host.command("ideas.log", {"event": "opened", "what": "nothing"})
    rows = [r for r in event_log.read(Path(host.town.repo_root)) if r["event"] == "opened"]
    assert [r["what"] for r in rows] == ["recap", "flag", "week", "push", "idea", "idea", "idea", "idea"]


# -- Spec 121 D: `ideas.night` (docs/specs/121-the-day-the-morning-and-the-night.md §5.4) --------------------------------------------------------------

def test_the_night_is_the_hosts_and_a_phones_and_null_when_it_did_nothing(host):
    assert BoardPhone.allowed(host, "ideas.night", {})
    assert host.command("ideas.night", {}) is None
    with pytest.raises(CommandError, match="Open a folder first"):
        Orkboard().command("ideas.night", {})


def test_the_nights_record_lists_the_goals_that_reached_dev_and_the_card_opened_is_one_event(host):
    slug = _merge(host, 1)
    got = host.command("ideas.night", {})
    json.dumps(got)
    assert got["into"] == "dev" and got["empty"] is False and got["failed"] == [] and got["reverts"] == [] and got["checks"] == [] and got["play"] is None
    assert [(g["slug"], g["done"], g["screens"]) for g in got["goals"]] == [(slug, True, [])]
    assert [e for e in event_log.read(Path(host.ideas.host.repo_root)) if e["event"] == event_log.NIGHT_CARD_OPENED] == [], "reading the record is no opening"
    host.command("ideas.night", {"opened": True, "device": "phone"})
    (opened,) = [e for e in event_log.read(Path(host.ideas.host.repo_root)) if e["event"] == event_log.NIGHT_CARD_OPENED]
    assert opened["goals"] == 1 and opened["device"] == "phone"


def test_a_last_look_after_the_nights_window_cuts_the_record_and_it_is_checked(host):
    _merge(host, 1)
    time.sleep(1.2)                                                                  # the log keeps whole seconds
    assert host.command("ideas.night", {"since": _ms(0)}) is None, "the device looked after the goal reached dev"
    assert host.command("ideas.night", {"since": _ms(24 * 90)})["goals"][0]["done"] is True
    for bad in ("yesterday", True):
        with pytest.raises(CommandError, match="last look"):
            host.command("ideas.night", {"since": bad})
    with pytest.raises(CommandError, match="`since` is ahead of now"):
        host.command("ideas.night", {"since": _ms(-2)})


def test_the_hints_of_the_last_play_stay_for_the_card_after_the_play_stops(host):
    from types import SimpleNamespace
    _merge(host, 1)
    ideas_ = host.ideas
    ideas_._play = SimpleNamespace(state="playing", play_id="p1")
    ring = ideas_._ring("p1")
    ring.add({"kind": "error", "message": "boom", "path": "/", "at": 5})
    assert [h["kind"] for h in ideas_.last_play_hints()] == ["error"], "while it plays, the play's own"
    assert host.command("ideas.night", {})["play"]["hints"][0]["words"] == "An error here: boom"
    ideas_._play = None                                                              # Play stopped: its ring is dropped, its hints are kept
    assert [h["kind"] for h in ideas_.last_play_hints()] == ["error"]
    assert host.command("ideas.night", {})["play"]["hints"][0]["kind"] == "error"


def test_the_card_lifted_is_kept_so_the_first_mark_on_play_after_it_is_timed_once(host):
    _merge(host, 1)
    assert host.ideas.card_minutes() is None, "nothing was lifted"
    host.command("ideas.night", {})
    assert host.ideas.card_minutes() is None, "reading the record is no opening"
    host.command("ideas.night", {"opened": True})
    first = host.ideas.card_minutes()
    assert first is not None and 0 <= first < 1 and host.ideas.card_minutes() is None, "timed once: only the first mark after an opening"

