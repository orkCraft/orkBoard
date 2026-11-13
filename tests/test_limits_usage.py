"""Spec 91 B (docs/specs/91-the-owners-list.md §2, decisions §107): what used an AI tool's limit, by party and member. The pure split
(realm/limit_usage.py): pairs of reads split by the tokens of the calls between them, across parties and members; a reset (the left going up)
is not use; use with no call is outside Orkboard; fewer than two reads gives tokens only; the shares add up to no more than 100. The command
(`ideas.usage`, gui/ideas_usage.py) over a project's ledgers and its `limits_read` events: its rows, titles and names, the live read closing
the last pair, a tool unknown refused. No model is called."""
from __future__ import annotations

import datetime as dt
import json

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, idea_spend, ideas, limit_usage

T0 = dt.datetime(2026, 10, 26, 9, 0).astimezone()


def at(hours: float) -> dt.datetime:
    return T0 + dt.timedelta(hours=hours)


def read(hours: float, left: float) -> dict:
    return {"at": at(hours), "left": left}


def call(hours: float, party: str, agent: str, tokens: int) -> dict:
    return {"at": at(hours), "party": party, "agent": agent, "tokens": tokens}


def shares(got: dict) -> dict:
    return {r["party"]: (r["share"], {m["agent"]: m["share"] for m in r["members"]}) for r in got["rows"]}


def test_a_pair_of_reads_is_split_by_the_tokens_of_the_calls_between_them_across_parties_and_members():
    reads = [read(0, 0.90), read(1, 0.50)]                                          # 40 % used in the hour
    lines = [call(0.2, "alpha", "backend", 300), call(0.4, "alpha", "taskmaster", 100), call(0.6, "beta", "grunt", 600)]
    got = limit_usage.split(reads, lines)
    assert got["tokens_only"] is False and got["outside"] == 0
    assert shares(got) == {"beta": (24, {"grunt": 24}), "alpha": (16, {"backend": 12, "taskmaster": 4})}
    assert [r["party"] for r in got["rows"]] == ["beta", "alpha"]                   # by share
    assert got["rows"][0]["tokens"] == 600 and got["rows"][1]["tokens"] == 400


def test_a_reset_is_not_use_and_only_the_reads_since_it_count():
    reads = [read(0, 0.30), read(1, 0.10), read(2, 0.95), read(3, 0.85)]            # the window reset between the 2nd and the 3rd
    lines = [call(0.5, "old", "grunt", 100), call(2.5, "new", "grunt", 100)]
    got = limit_usage.split(reads, lines)
    assert shares(got) == {"new": (10, {"grunt": 10})} and got["outside"] == 0      # the old window's 20 % and the rise are not counted
    assert limit_usage.split([read(0, 0.5), read(1, 0.9)], [call(0.5, "a", "g", 1)])["tokens_only"] is True     # a reset leaves one read: tokens only


def test_the_shares_are_whole_percents_that_never_add_up_to_more_than_a_hundred():
    reads = [read(0, 1.0), read(1, 0.0)]                                             # all of it used, in thirds
    lines = [call(0.1, "a", "x", 1), call(0.2, "b", "y", 1), call(0.3, "c", "z", 1)]
    got = limit_usage.split(reads, lines)
    assert sum(r["share"] for r in got["rows"]) + got["outside"] == 100 and all(isinstance(r["share"], int) for r in got["rows"])
    odd = limit_usage.split([read(0, 1.0), read(1, 0.5), read(2, 0.0)], [call(0.5, "a", "x", 3), call(0.6, "a", "y", 3), call(1.5, "b", "x", 1)])
    for r in odd["rows"]:
        assert sum(m["share"] for m in r["members"]) == r["share"]                   # a party's members add up to the party
    assert sum(r["share"] for r in odd["rows"]) + odd["outside"] <= 100


# -- the command ---------------------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    h.root, h.state = h.ideas.root(), h.ideas.state_dir
    yield h


def spend_line(hours: float, role: str, tokens: int, tool: str = "claude") -> dict:
    return idea_spend.line("task", role, tool, "m", "warrior", "", {"in": tokens, "out": 0, "cache_read": None, "cache_write": None}, 0.1,
                           at=at(hours).replace(tzinfo=None).isoformat(timespec="seconds"))


def limits_row(left: float, reset: dt.datetime, window: str = "week") -> list[dict]:
    return [{"provider": "claude", "name": "Claude", "left": left, "rows": [{"window": window, "left": left, "reset": reset.isoformat(timespec="minutes")}]}]


def write_read(h, hours: float, left: float, provider: str = "claude", window: str = "week") -> None:
    event_log.record(h.ideas.host.repo_root, event_log.LIMITS_READ, at=at(hours), provider=provider, left=left, window=window)


@pytest.fixture
def world(host, monkeypatch):
    """Two parties with a goal each; the week reset in 5 days; the tool has 40 % of the week left now."""
    alpha, beta = ideas.add_track(host.root, "Alpha"), ideas.add_track(host.root, "Beta")
    a = ideas.add_idea(host.root, "Alpha goal", alpha, host.state)
    b = ideas.add_idea(host.root, "Beta goal", beta, host.state)
    now = dt.datetime.now().astimezone()
    monkeypatch.setattr(host.ideas, "limits", lambda: limits_row(0.40, now + dt.timedelta(days=5)))
    return host, (alpha, beta), (a, b), now


def test_the_command_splits_the_weeks_use_by_party_and_member(world):
    h, (alpha, beta), (a, b), now = world
    base = (now - T0).total_seconds() / 3600                                         # hours from T0 to now
    for hours, left in ((base - 40, 0.90), (base - 20, 0.70), (base - 1, 0.45)):
        write_read(h, hours, left)
    write_read(h, base - 30, 0.55, provider="codex")                                  # another tool's read is not this one's
    idea_spend.append(h.state, spend_line(base - 30, "backend", 300), idea=a)
    idea_spend.append(h.state, spend_line(base - 25, "grunt", 100), idea=a)
    idea_spend.append(h.state, spend_line(base - 10, "grunt", 500), idea=b)
    idea_spend.append(h.state, spend_line(base - 10, "grunt", 999, tool="codex"), idea=b)   # another tool's call is not counted
    got = h.command("ideas.usage", {"provider": "claude"})
    assert (got["provider"], got["name"], got["window"], got["scope"], got["estimated"], got["tokens_only"]) == ("claude", "Claude", "week", "project", True, False)
    assert got["left"] == 0.40 and got["reset"]
    assert got["scopes"] == ["project", "all"]
    by = {r["title"]: r for r in got["rows"]}
    assert set(by) == {"Alpha", "Beta"}
    assert {m["name"] for m in by["Alpha"]["members"]} == {"backend", "Grunt"} and by["Alpha"]["members"][0]["agent"] == "backend"
    # 10 % from the window's start to the first read (no call: outside); 20 % to the 2nd read (Alpha's 400 tokens); 25 % to the 3rd
    # (Beta's 500); 5 % from the 3rd to now (no call: outside)
    assert by["Alpha"]["share"] == 20 and by["Beta"]["share"] == 25 and got["outside"] == 15
    assert sum(r["share"] for r in got["rows"]) + got["outside"] <= 100
    assert got["rows"][0]["title"] == "Beta"                                          # rows by share


def test_a_party_own_ledger_the_night_and_a_goal_since_removed_have_rows_of_their_own(world):
    h, (alpha, _beta), (a, _b), now = world
    base = (now - T0).total_seconds() / 3600
    write_read(h, base - 10, 0.90)
    idea_spend.append(h.state, spend_line(base - 5, "taskmaster", 100), goal=alpha)             # a party's own call
    idea_spend.append(h.state, spend_line(base - 4, "taskmaster", 100))                          # the night's proposals
    idea_spend.append(h.state, spend_line(base - 3, "grunt", 100), idea="gone-goal")             # a goal whose page is gone
    got = h.command("ideas.usage", {"provider": "claude"})
    assert {r["title"] for r in got["rows"]} == {"Alpha", "Orkmaster", "Goals since removed"}
    assert next(r for r in got["rows"] if r["title"] == "Alpha")["members"][0]["name"] == "Taskmaster"


def test_the_command_refuses_an_unknown_tool_and_an_unknown_scope(host):
    with pytest.raises(CommandError, match="No AI tool nothing"):
        host.command("ideas.usage", {"provider": "nothing"})
    with pytest.raises(CommandError, match="provider"):
        host.command("ideas.usage", {})
    with pytest.raises(CommandError, match="No scope"):
        host.command("ideas.usage", {"provider": "claude", "scope": "world"})


def test_all_projects_read_every_project_open_here(world, tmp_path):
    h, (alpha, _beta), (a, _b), now = world
    base = (now - T0).total_seconds() / 3600
    write_read(h, base - 10, 0.90)
    idea_spend.append(h.state, spend_line(base - 5, "grunt", 100), idea=a)
    got = h.command("ideas.usage", {"provider": "claude", "scope": "all"})
    assert got["scope"] == "all" and [r["title"] for r in got["rows"]] == [f"Alpha · {h.ideas.host.repo_root.name}"]
    json.dumps(got)                                                                   # plain data all through


# -- spec 149 H.2: what a goal took of a tool's window, from the reads at its first call and now -------------------------------------------------

def _event(hours: float, left: float, provider: str = "codex", window: str = "week") -> dict:
    return {"event": event_log.LIMITS_READ, "at": at(hours).isoformat(), "provider": provider, "left": left, "window": window}


def _row(hours: float, tool: str = "codex", tokens: int = 1000) -> dict:
    return {"at": at(hours).isoformat(), "tool": tool, "tokens": {"total": tokens}}


def test_a_goal_took_what_the_reads_from_its_first_call_to_now_show():
    events = [_event(-1, 0.90), _event(2, 0.89), _event(5, 0.88)]
    got = limit_usage.goal_share(events, [_row(0.5), _row(3), _row(4)])
    assert got == {"tool": "codex", "window": "week", "share": 2.0}                       # 0.90 at its first call (the read before it) to 0.88 now
    assert limit_usage.goal_share(events[1:], [_row(0.5)]) is None                          # no read before its first call: nothing to say
    assert limit_usage.goal_share(events[:1], [_row(0.5)]) is None                          # read once: left out
    assert limit_usage.goal_share(events, [_row(0.5, tool="claude")]) is None               # the reads are another tool's
    assert limit_usage.goal_share(events, []) is None

