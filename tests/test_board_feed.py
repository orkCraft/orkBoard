"""Goal 169 E (decisions §291.5–§291.9): `board_feed.build`, the phone's feed as data, on a fixture log and Board rows, and `ideas.feed` on
the host and the phone. Code, no model, no browser."""
from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, Orkboard
from orkboard.realm import board_feed, event_log, ideas

NOW = dt.datetime(2026, 11, 10, 12, 0).astimezone()
SINCE = NOW - dt.timedelta(hours=3)                     # the device's last look


def _at(hours_ago: float) -> dt.datetime:
    return NOW - dt.timedelta(hours=hours_ago)


def _log(root: Path, event: str, hours_ago: float, **fields) -> None:
    row = event_log.line(event, at=_at(hours_ago), **fields)
    target = event_log.path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _plan(state: Path, slug: str, *tasks) -> None:
    folder = state / "ideas" / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan.json").write_text(json.dumps({"idea": slug, "tasks": [{"id": i, "title": t, "state": s, **({"party": p} if p else {})}
                                                                          for i, t, s, p in tasks]}))


def _route(state: Path, slug: str, *parties) -> None:
    folder = state / "ideas" / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "state.json").write_text(json.dumps({"state": "working", "route": [{"party": p} for p in parties]}))


def _rows(*items, parties=("tech", "art", "release")):
    """`items`: (slug, party, state, extra)."""
    return {"ideas": [{"slug": s, "short": s.title(), "title": f"Title of {s}", "track": p, "state": st, **extra} for s, p, st, extra in items],
            "tracks": [{"slug": g, "short": g.title(), "title": f"{g.title()} party"} for g in parties], "needs_you": []}


@pytest.fixture
def where(tmp_path):
    root, state = tmp_path / "project", tmp_path / "state"
    root.mkdir()
    state.mkdir()
    return root, state


def _board(where):
    """A spec set to start at a clock time, a goal waiting for main, and Tech's and Art's news since the look."""
    root, state = where
    _plan(state, "reconnect", ("k1", "Resume the session", "merged", "tech"), ("k2", "The lobby", "merged", "art"))
    _log(root, "task_state", 2.5, idea="reconnect", task="k1", state="merged", was="review", round=1)
    _log(root, "task_state", 1, idea="reconnect", task="k2", state="merged", was="review", round=1)
    _log(root, "leader_objected", 0.5, idea="lobby", party="tech", verdict="doubt", has_instead=False)
    rows = _rows(("reconnect", "tech", "working", {}),
                 ("leaderboard", "tech", "plan", {"look_until": (NOW + dt.timedelta(hours=2)).timestamp()}),
                 ("signin", "release", "done", {}), ("lobby", "art", "talk", {}))
    ready = [{"slug": "signin", "title": "Title of signin", "goal": "release", "tasks": [], "main_ready": True, "main_reason": ""}]
    return rows, ready


def _keys(data, out=None) -> set[str]:
    out = set() if out is None else out
    if isinstance(data, dict):
        for k, v in data.items():
            out.add(k)
            _keys(v, out)
    elif isinstance(data, list):
        for v in data:
            _keys(v, out)
    return out


def test_waits_come_first_then_the_posts_newest_first_with_their_leaders_and_times(where):
    root, state = where
    rows, ready = _board(where)
    got = board_feed.build(root, state, rows, SINCE, NOW, ready=ready)
    json.dumps(got)
    assert [(w["kind"], w["goal"]) for w in got["waits"]] == [("starts", "leaderboard"), ("main", "signin")]
    starts, main = got["waits"]
    assert dt.datetime.fromisoformat(starts["at"]) == (NOW + dt.timedelta(hours=2)).replace(microsecond=0)
    assert [a["act"] for a in starts["acts"]] == ["change_spec", "start_now"] and starts["acts"][1]["args"] == {"slug": "leaderboard"}
    assert main["leader"] == "release" and [a["command"] for a in main["acts"]] == ["ideas.to_main"]
    posts = [s["post"] for s in got["posts"]]
    assert [(p["leader"], p["goal"]) for p in posts] == [("tech", "lobby"), ("art", "reconnect"), ("tech", "reconnect")]
    assert [p["kind"] for p in posts] == ["concern", "news", "news"]
    times = [board_feed.board_recap.when(p["at"]) for p in posts]
    assert times == sorted(times, reverse=True) and all(SINCE <= t < NOW for t in times)
    assert posts[1]["text"] == "Reconnect: The lobby is in dev"
    assert got["seen"] is None
    assert [(h["leader"], h["news"]) for h in got["heads"]] == [("orkmaster", False), ("tech", True), ("art", True), ("release", False)]


def test_one_leaders_posts_in_a_row_are_one_stack(where):
    root, state = where
    _plan(state, "physics", ("k1", "Split rooms", "merged", ""), ("k2", "Jump", "merged", ""), ("k3", "Lobby look", "merged", "art"))
    _log(root, "task_state", 2.5, idea="physics", task="k3", state="merged", was="review", round=1)
    _log(root, "task_state", 2, idea="physics", task="k1", state="merged", was="review", round=1)
    _log(root, "task_state", 1, idea="physics", task="k2", state="failed", was="running", round=1)
    _log(root, "concerns_made", 0.5, party="tech", n=2, alerts=1)
    got = board_feed.build(root, state, _rows(("physics", "tech", "working", {})), SINCE, NOW)
    assert [(s["leader"], len(s["more"])) for s in got["posts"]] == [("tech", 2), ("art", 0)]
    first = got["posts"][0]
    assert first["post"]["text"] == "New concerns on its map" and [p["kind"] for p in first["more"]] == ["concern", "news"]


def test_what_came_before_the_look_is_the_one_seen_item_never_news(where):
    root, state = where
    _plan(state, "physics", ("k1", "Split rooms", "merged", ""), ("k2", "Jump", "merged", "art"))
    _log(root, "task_state", 5, idea="physics", task="k1", state="merged", was="review", round=1)        # before the look
    _log(root, "task_state", 4, idea="physics", task="k2", state="merged", was="review", round=1)        # before the look
    _log(root, "plan_made", 6, idea="physics", tasks=2)                                                  # before the look, the Orkmaster's
    _log(root, "task_state", 40, idea="physics", task="k1", state="merged", was="review", round=1)       # more than a day before: not read
    _log(root, "goal_to_dev", 1, idea="physics", into="dev")
    got = board_feed.build(root, state, _rows(("physics", "tech", "working", {})), SINCE, NOW)
    assert [s["post"]["event"] for s in got["posts"]] == ["goal_to_dev"]
    seen = got["seen"]
    assert seen["leaders"] == ["art", "tech", "orkmaster"] and [p["event"] for p in seen["posts"]] == ["task_state", "task_state", "plan_made"]
    assert dt.datetime.fromisoformat(seen["since"]) == SINCE.replace(microsecond=0)
    assert {h["leader"]: h["news"] for h in got["heads"]}["art"] is False
    everything = board_feed.build(root, state, _rows(("physics", "tech", "working", {})), None, NOW)
    assert everything["seen"] is None and len([p for s in everything["posts"] for p in (s["post"], *s["more"])]) == 5


def test_an_event_that_names_no_party_is_the_orkmasters(where):
    root, state = where
    _log(root, "findings_told", 1, idea="", party="", findings=2)
    _log(root, "concerns_made", 0.8, party="gone", n=1, alerts=0)           # a party the Board no longer has
    _log(root, "idea_added", 0.5, idea="physics", track="tech")
    got = board_feed.build(root, state, _rows(("physics", "tech", "raw", {})), SINCE, NOW)
    assert [(s["leader"], [p["text"] for p in (s["post"], *s["more"])]) for s in got["posts"]] == [
        ("orkmaster", ["Physics was added", "New concerns on its map", "Findings on the code"])]


def test_a_route_cuts_the_feed_to_its_goal_and_its_leaders(where):
    root, state = where
    rows, ready = _board(where)
    _route(state, "reconnect", "tech")
    _log(root, "plan_made", 2, idea="reconnect", tasks=2)
    got = board_feed.build(root, state, rows, SINCE, NOW, ready=ready, route="reconnect")
    assert [h["leader"] for h in got["heads"]] == ["orkmaster", "tech"]
    assert got["waits"] == []
    assert [(s["post"]["leader"], s["post"]["goal"]) for s in got["posts"]] == [("orkmaster", "reconnect"), ("tech", "reconnect")]   # Art's post is off the route
    spec = board_feed.build(root, state, rows, SINCE, NOW, ready=ready, route="leaderboard")
    assert [w["goal"] for w in spec["waits"]] == ["leaderboard"] and spec["posts"] == []
    with pytest.raises(ValueError):
        board_feed.build(root, state, rows, SINCE, NOW, route="nothing")


def test_no_key_of_the_feed_is_a_count(where):
    root, state = where
    rows, ready = _board(where)
    _log(root, "task_state", 5, idea="reconnect", task="k1", state="merged", was="review", round=1)
    got = board_feed.build(root, state, rows, SINCE, NOW, ready=ready)
    assert got["seen"] is not None
    keys = _keys(got)
    assert not keys & {"n", "count", "counts", "unread", "total", "news_count"}
    assert not any("count" in k or "unread" in k for k in keys)


# -- the host's and the phone's `ideas.feed` -----------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo) -> Orkboard:
    return Orkboard(fake_repo)


def test_the_feed_is_the_hosts_and_a_phones(host):
    assert BoardPhone.allowed(host, "ideas.feed", {})
    root, state = host.ideas.root(), host.ideas.state_dir
    goal, _new = ideas.save_goal(root, None, "Offline mode", "About it", None, "normal")
    slug = ideas.add_idea(root, "Retry queue", goal, state)
    event_log.record(Path(host.ideas.host.repo_root), "plan_made", idea=slug, tasks=1)
    got = host.command("ideas.feed", {"since": int((time.time() - 3600) * 1000)})
    json.dumps(got)
    assert [s["post"]["goal"] for s in got["posts"]] == [slug] and got["posts"][0]["leader"] == "orkmaster"
    assert host.command("ideas.feed", {})["seen"] is None
    assert host.command("ideas.feed", {"route": slug})["heads"][0]["leader"] == "orkmaster"


def test_since_is_as_the_recap_takes_it(host):
    from orkboard.gui.board_host import CommandError
    for bad in ({"since": "yesterday"}, {"since": True}):
        with pytest.raises(CommandError, match="last look"):
            host.command("ideas.feed", bad)
    with pytest.raises(CommandError, match="ahead of now"):
        host.command("ideas.feed", {"since": int((time.time() + 7200) * 1000)})
    with pytest.raises(CommandError, match="slug"):
        host.command("ideas.feed", {"route": 3})
