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


def test_a_call_counts_in_the_pair_it_was_made_in_and_pairs_add_up():
    reads = [read(0, 1.0), read(1, 0.8), read(2, 0.5)]
    lines = [call(0.5, "alpha", "grunt", 10), call(1.5, "beta", "grunt", 10), call(1.6, "beta", "grunt", 10), call(5, "beta", "grunt", 999)]
    got = limit_usage.split(reads, lines)
    assert shares(got) == {"beta": (30, {"grunt": 30}), "alpha": (20, {"grunt": 20})} and got["outside"] == 0   # the call after the last read is no pair's


def test_a_reset_is_not_use_and_only_the_reads_since_it_count():
    reads = [read(0, 0.30), read(1, 0.10), read(2, 0.95), read(3, 0.85)]            # the window reset between the 2nd and the 3rd
    lines = [call(0.5, "old", "grunt", 100), call(2.5, "new", "grunt", 100)]
    got = limit_usage.split(reads, lines)
    assert shares(got) == {"new": (10, {"grunt": 10})} and got["outside"] == 0      # the old window's 20 % and the rise are not counted
    assert limit_usage.split([read(0, 0.5), read(1, 0.9)], [call(0.5, "a", "g", 1)])["tokens_only"] is True     # a reset leaves one read: tokens only


def test_use_with_no_call_is_outside_orkboard():
    reads = [read(0, 0.90), read(1, 0.70), read(2, 0.50)]
    got = limit_usage.split(reads, [call(1.5, "alpha", "grunt", 50)])               # nothing was called in the first hour
    assert got["outside"] == 20 and shares(got) == {"alpha": (20, {"grunt": 20})}


def test_the_windows_start_makes_the_use_before_the_first_read_known():
    start = at(-10)
    reads = [read(0, 0.60)]                                                          # 40 % gone when Orkboard first read the limit
    lines = [call(-5, "alpha", "grunt", 100), call(-4, "alpha", "grunt", 100)]
    got = limit_usage.split(reads, lines, start)
    assert got["tokens_only"] is False and shares(got) == {"alpha": (40, {"grunt": 40})}
    assert limit_usage.split(reads, [], start)["outside"] == 40                      # no call of ours: all of it outside


def test_fewer_than_two_reads_gives_tokens_and_no_share():
    lines = [call(0.1, "alpha", "backend", 70), call(0.2, "alpha", "grunt", 30), call(0.3, "beta", "grunt", 500)]
    for reads in ([], [read(0, 0.5)]):
        got = limit_usage.split(reads, lines)
        assert got["tokens_only"] is True and got["outside"] == 0
        assert [(r["party"], r["share"], r["tokens"]) for r in got["rows"]] == [("beta", None, 500), ("alpha", None, 100)]
        assert [(m["agent"], m["share"], m["tokens"]) for m in got["rows"][1]["members"]] == [("backend", None, 70), ("grunt", None, 30)]


def test_the_shares_are_whole_percents_that_never_add_up_to_more_than_a_hundred():
    reads = [read(0, 1.0), read(1, 0.0)]                                             # all of it used, in thirds
    lines = [call(0.1, "a", "x", 1), call(0.2, "b", "y", 1), call(0.3, "c", "z", 1)]
    got = limit_usage.split(reads, lines)
    assert sum(r["share"] for r in got["rows"]) + got["outside"] == 100 and all(isinstance(r["share"], int) for r in got["rows"])
    odd = limit_usage.split([read(0, 1.0), read(1, 0.5), read(2, 0.0)], [call(0.5, "a", "x", 3), call(0.6, "a", "y", 3), call(1.5, "b", "x", 1)])
    for r in odd["rows"]:
        assert sum(m["share"] for m in r["members"]) == r["share"]                   # a party's members add up to the party
    assert sum(r["share"] for r in odd["rows"]) + odd["outside"] <= 100


def test_calls_without_tokens_split_a_pair_evenly():
    got = limit_usage.split([read(0, 1.0), read(1, 0.8)], [call(0.2, "a", "x", 0), call(0.3, "b", "x", 0)])
    assert shares(got) == {"a": (10, {"x": 10}), "b": (10, {"x": 10})}


def test_a_window_is_as_long_as_its_name_says():
    assert limit_usage.window_span("5h") == dt.timedelta(hours=5) and limit_usage.window_span("week") == dt.timedelta(days=7)
    assert limit_usage.window_span("Gemini Models · week") == dt.timedelta(days=7) and limit_usage.window_span("limit") is None


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


def test_the_command_counts_the_use_before_the_first_read_from_the_windows_start(world):
    h, (alpha, _beta), (a, _b), now = world
    base = (now - T0).total_seconds() / 3600
    idea_spend.append(h.state, spend_line(base - 30, "grunt", 100), idea=a)           # in the week (it began 2 days ago), before any read
    got = h.command("ideas.usage", {"provider": "claude"})                            # no read at all but now's: from the start to now
    assert got["tokens_only"] is False and got["outside"] == 0
    assert [(r["title"], r["share"]) for r in got["rows"]] == [("Alpha", 60)]         # the week began with all of it; 40 % is left


def test_no_read_and_no_window_start_gives_tokens_only(host, monkeypatch):
    monkeypatch.setattr(host.ideas, "limits", lambda: [])
    track = ideas.add_track(host.root, "Alpha")
    slug = ideas.add_idea(host.root, "A goal", track, host.state)
    idea_spend.append(host.state, spend_line(-24 * 30, "grunt", 70), idea=slug)
    idea_spend.append(host.state, {**spend_line(-1, "grunt", 70), "at": dt.datetime.now().isoformat(timespec="seconds")}, idea=slug)
    got = host.command("ideas.usage", {"provider": "claude"})
    assert got["tokens_only"] is True and got["left"] is None and got["outside"] == 0
    assert [(r["title"], r["share"], r["tokens"]) for r in got["rows"]] == [("Alpha", None, 70)]       # the week's calls; the older one is not


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
