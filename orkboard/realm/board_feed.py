"""The phone's feed (decisions §291.5–§291.9, goal 169 stage E): what waits for the person first, then each leader's posts since the
device's last look, newest first, as plain data. A pure read of the event log (board_recap's) and the Board's rows: no face, no model; it
writes nothing, starts nothing and moves nothing.

    board_feed.build(root, state_dir, rows, since, now, ready=(), pages=None, route=None, into="dev")
        -> {since, heads, waits, posts, seen}

- `waits`: the specs that start by themselves at a clock time (a plan's look's wait, `look_until` on the Board's row: spec 144 A), the
  soonest first, then the goals done and waiting for main (`ready`: the discard's main pile, `ideas.gate`'s `ideas`), in dev's order.
  Each `{kind ("starts" · "main"), goal, short, title, party, leader, at, acts}`; `at` the clock time it starts (local ISO) or "".
- `posts`: the leaders' posts since `since`, newest first, one leader's posts in a row one stack: `[{leader, post, more: [post…]}]`,
  `post` the first shown, `more` the rest under it (oldest last). A post is `{leader, at, kind ("news" · "concern" · "change"), goal,
  text, event, acts}`; `goal` is "" for a post of no goal. A post's leader is the party its event names (its `party`, a party flag's
  `goal`, a task's party in its plan, else the goal's party); an event that names none, or a party the Board no longer has, is the
  Orkmaster's (`orkmaster`). Posts carry no act: none of the events they come from carries one where it is shown today.
- `seen`: what came before `since` (a day back at most), one item, never news: `{since, leaders: [the heads, newest first, each once],
  posts: [post…]}`; None when nothing came before, or `since` is None (everything is news).
- `heads`: the Orkmaster, then the leaders in the Board's order (a route's: its leaders in route order): `[{leader, news, asks}]`.
- `route`: a goal's slug: the feed cut to its route, its leaders' heads only and that goal's waits and posts (a goal's screen).

No count anywhere (§223, §291.9): a head has news or asks, never a number. Times are never compared as text.
"""
from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from pathlib import Path
from typing import Any

from orkboard.realm import board_recap, event_log, ideas

ORKMASTER = "orkmaster"
SEEN_BACK = dt.timedelta(days=1)          # the seen line reaches this far before the look
POSTS_MAX = 60                            # the most posts since the look
SEEN_MAX = 12                             # the most posts under the seen line
TEXT_MAX = 140


def _cut(text: object, n: int = TEXT_MAX) -> str:
    one = " ".join(str(text or "").split())
    return one if len(one) <= n else one[:n - 1].rstrip() + "…"


class _Board:
    """The names the posts are worded with: the Board's goals and parties, and a goal's tasks from its plan (read once each)."""

    def __init__(self, state_dir: Path, rows: dict, into: str):
        self.state_dir, self.into = state_dir, into
        self.ideas = {str(i.get("slug")): i for i in rows.get("ideas") or [] if isinstance(i, dict) and i.get("slug")}
        self.parties = {str(t.get("slug")): t for t in rows.get("tracks") or [] if isinstance(t, dict) and t.get("slug")}
        self._plans: dict[str, list[dict]] = {}

    def short(self, slug: str) -> str:
        i = self.ideas.get(slug) or {}
        return str(i.get("short") or i.get("title") or slug)

    def party_name(self, slug: str) -> str:
        p = self.parties.get(slug) or {}
        return str(p.get("short") or p.get("title") or slug)

    def task(self, slug: str, tid: str) -> dict:
        if slug not in self._plans:
            try:
                self._plans[slug] = [t for t in (ideas.plan(self.state_dir, slug) or {}).get("tasks") or [] if isinstance(t, dict)]
            except (OSError, ValueError):
                self._plans[slug] = []
        return next((t for t in self._plans[slug] if str(t.get("id")) == tid), {})

    def leader(self, party: object) -> str:
        return party if isinstance(party, str) and party in self.parties else ORKMASTER


# -- what each event posts: (kind, the party it names, its words) or None when it posts nothing ---------------------------------------------

Said = tuple[str, str, str] | None


def _task_state(r: dict, b: _Board) -> Said:
    slug, tid = str(r.get("idea") or ""), str(r.get("task") or "")
    task = b.task(slug, tid)
    from orkboard.realm.board_map import task_short          # board_map reads goal_flags, which reads board_recap
    name = task_short(task) if task else "A task"
    party = str(task.get("party") or (b.ideas.get(slug) or {}).get("track") or "")
    if r.get("state") == "merged" and r.get("clean") is not True:
        return "news", party, f"{b.short(slug)}: {name} is in {b.into}"
    if r.get("state") == "failed":
        return "concern", party, f"{b.short(slug)}: {name} failed"
    return None


def _step(r: dict, b: _Board) -> Said:
    slug, step, verdict = str(r.get("idea") or ""), str(r.get("step") or ""), str(r.get("verdict") or "")
    if r.get("failed") is True:
        return None
    if verdict == "back":
        return "concern", str(r.get("party") or ""), f"Sent step {step} of {b.short(slug)} back"
    if verdict in ("accepted", "gone_on"):
        return "news", str(r.get("party") or ""), f"Accepted step {step} of {b.short(slug)}" if verdict == "accepted" else f"{b.short(slug)} went on after step {step}"
    return None


def _objected(r: dict, b: _Board) -> Said:
    word = "Says no to" if r.get("verdict") == "no" else "Doubts"
    return "concern", str(r.get("party") or ""), f"{word} {b.short(str(r.get('idea') or ''))}"


def _concerns(r: dict, b: _Board) -> Said:
    return ("concern", str(r.get("party") or ""), "New concerns on its map") if r.get("n") or r.get("alerts") else None


def _findings(r: dict, b: _Board) -> Said:
    if r.get("failed") is True or not r.get("findings"):
        return None
    slug = str(r.get("idea") or "")
    return "concern", str(r.get("party") or ""), f"Findings on {b.short(slug)}" if slug else "Findings on the code"


def _accepted(r: dict, b: _Board) -> Said:
    return "news", str(r.get("goal") or ""), "Accepted against its measures" if r.get("met") else "Accepted, its measures not met"


def _flagged(r: dict, b: _Board) -> Said:
    slug = str(r.get("idea") or "")
    return "news", str((b.ideas.get(slug) or {}).get("track") or r.get("goal") or ""), f"{b.short(slug)} is in main"


def _leader_change(r: dict, b: _Board) -> Said:
    return ("change", str(r.get("party") or ""), f"Changed {b.short(str(r.get('idea') or ''))}'s spec") if r.get("take") else None


def _spec_change(r: dict, b: _Board) -> Said:
    return ("change", "", f"{b.short(str(r.get('idea') or ''))}'s spec changed") if r.get("answer") == "take" else None


def _moved(r: dict, b: _Board) -> Said:
    return "change", "", f"{b.short(str(r.get('goal') or ''))} moved to {b.party_name(str(r.get('to') or ''))}"


def _passed(r: dict, b: _Board) -> Said:
    slug = str(r.get("idea") or "")
    return "news", "", f"{b.short(slug)} started by itself" if r.get("by") == "auto" else f"{b.short(slug)} started"


def _idea(words: str, kind: str = "news") -> Callable[[dict, _Board], Said]:
    return lambda r, b: (kind, "", words.format(b.short(str(r.get("idea") or ""))))


# event → (its goal's field, what it posts)
POSTS: dict[str, tuple[str, Callable[[dict, _Board], Any]]] = {
    event_log.TASK_STATE: ("idea", _task_state),
    event_log.STEP_ACCEPTED: ("idea", _step),
    event_log.LEADER_OBJECTED: ("idea", _objected),
    event_log.CONCERNS_MADE: ("", _concerns),
    event_log.FINDINGS_TOLD: ("idea", _findings),
    event_log.GOAL_ACCEPTED: ("", _accepted),
    event_log.IDEA_FLAGGED: ("idea", _flagged),
    event_log.LEADER_CHANGE_ANSWERED: ("idea", _leader_change),
    event_log.SPEC_CHANGE_ANSWERED: ("idea", _spec_change),
    event_log.IDEA_MOVED: ("goal", _moved),
    event_log.PLAN_PASSED: ("idea", _passed),
    event_log.IDEA_ADDED: ("idea", _idea("{} was added")),
    event_log.PLAN_MADE: ("idea", _idea("{}'s plan is made")),
    event_log.PLAN_REVISED: ("idea", _idea("{}'s plan changed", "change")),
    event_log.DECISION_CHANGED: ("idea", _idea("{}'s decision changed", "change")),
    event_log.GOAL_TO_DEV: ("idea", _idea("{} went into dev")),
    event_log.GOAL_TO_MAIN: ("idea", _idea("{} went to main")),
}


def _post(r: dict, b: _Board) -> dict | None:
    """The post an event line makes, else None (an event that posts nothing, or of a goal the Board no longer has)."""
    field, said = POSTS[str(r.get("event"))]
    goal = str(r.get(field) or "") if field else ""
    if goal and goal not in b.ideas:
        return None
    got = said(r, b)
    if got is None:
        return None
    kind, party, text = got
    return {"leader": b.leader(party), "at": str(r.get("at") or ""), "kind": kind, "goal": goal, "text": _cut(text),
            "event": str(r.get("event")), "acts": []}


def stacks(posts: list[dict]) -> list[dict]:
    """Posts newest first, one leader's posts in a row one stack: `[{leader, post, more}]`."""
    out: list[dict] = []
    for p in posts:
        if out and out[-1]["leader"] == p["leader"]:
            out[-1]["more"].append(p)
        else:
            out.append({"leader": p["leader"], "post": p, "more": []})
    return out


# -- what waits for the person -------------------------------------------------------------------------------------------------------------

def _waits(b: _Board, ready: list[dict], now: dt.datetime) -> list[dict]:
    starts = []
    for slug, i in b.ideas.items():
        until = i.get("look_until")
        if i.get("state") != "plan" or not isinstance(until, (int, float)) or isinstance(until, bool) or until <= now.timestamp():
            continue
        at = dt.datetime.fromtimestamp(float(until)).astimezone()
        starts.append((at, {"kind": "starts", "goal": slug, "short": b.short(slug), "title": str(i.get("title") or slug),
                            "party": str(i.get("track") or ""), "leader": ORKMASTER, "at": at.isoformat(timespec="seconds"),
                            "acts": [{"act": "change_spec", "command": "ideas.spec_change", "args": {"idea": slug}},
                                     {"act": "start_now", "command": "ideas.start_now", "args": {"slug": slug}}]}))
    out = [w for _at, w in sorted(starts, key=lambda x: x[0])]
    release = b.leader("release")
    for g in ready or []:
        slug = str(g.get("slug") or g.get("idea") or "") if isinstance(g, dict) else ""
        if slug not in b.ideas:
            continue
        i = b.ideas[slug]
        out.append({"kind": "main", "goal": slug, "short": b.short(slug), "title": str(i.get("title") or slug), "party": str(i.get("track") or ""),
                    "leader": release, "at": "", "main_ready": g.get("main_ready") is not False, "main_reason": str(g.get("main_reason") or ""),
                    "acts": [{"act": "to_main", "command": "ideas.to_main", "args": {"idea": slug}}]})
    return out


def _route(state_dir: Path, pages: Path | None, slug: str, home: str) -> list[str]:
    """A goal's route, its parties in order (the state's, else its page's `route:`), its own party among them."""
    try:
        route = ideas.state(state_dir, slug).get("route") or ()
    except (OSError, ValueError):
        route = ()
    if not route and pages is not None:
        try:
            page = ideas.idea_page(Path(pages), slug)
        except (OSError, ValueError):
            page = None
        route = [x.strip() for x in str(page.get("route", "") or "").split(",")] if page is not None else []
    out: list[str] = []
    for r in route:
        p = r.get("party") if isinstance(r, dict) else r
        if isinstance(p, str) and p and p not in out:
            out.append(p)
    if home and home not in out:
        out.append(home)
    return out


def _asking(rows: dict, b: _Board) -> set[str]:
    """The leaders whose goals ask the person a question now (the Board's Needs you rows of kind `asks`)."""
    return {b.leader(n.get("goal")) for n in rows.get("needs_you") or [] if isinstance(n, dict) and n.get("kind") == "asks"}


def build(root: Path, state_dir: Path, rows: dict, since: dt.datetime | None, now: dt.datetime, ready: list[dict] | tuple = (),
          pages: Path | None = None, route: str | None = None, into: str = "dev", back: dt.timedelta = dt.timedelta(days=30)) -> dict[str, Any]:
    """The feed (see the module). `root`: the project's folder (its event log); `rows`: `ideas.board`'s `{ideas, tracks, needs_you}`;
    `since`: the device's last look, None for none; `ready`: the goals ready for main (`ideas.gate`'s `ideas`); `pages`: the Board's
    pages, for a route a goal's state does not hold; `back`: how far the feed reads with no look."""
    b = _Board(state_dir, rows, into)
    now = now.astimezone()
    since = since.astimezone() if since is not None else None
    floor = since - SEEN_BACK if since is not None else now - back
    log = board_recap.events_between(Path(root), floor, now, *POSTS)
    made = [p for p in (_post(r, b) for r in log) if p is not None]
    made.reverse()                                                       # newest first
    waits = _waits(b, list(ready or []), now)

    leaders = [ORKMASTER, *b.parties]
    if route:
        if route not in b.ideas:
            raise ValueError(f"No goal {route} on the Board")
        mine = _route(state_dir, pages, route, str(b.ideas[route].get("track") or ""))
        leaders = [ORKMASTER, *(p for p in mine if p in b.parties)]
        made = [p for p in made if p["goal"] == route and p["leader"] in leaders]
        waits = [w for w in waits if w["goal"] == route]

    def new(p: dict) -> bool:
        at = board_recap.when(p["at"])
        return since is None or (at is not None and at >= since)

    news = [p for p in made if new(p)][:POSTS_MAX]
    old = [p for p in made if not new(p)][:SEEN_MAX]
    seen = None
    if old:
        order: list[str] = []
        for p in old:
            if p["leader"] not in order:
                order.append(p["leader"])
        seen = {"since": since.isoformat(timespec="seconds") if since else "", "leaders": order, "posts": old}
    asking, fresh = _asking(rows, b), {p["leader"] for p in news}
    heads = [{"leader": k, "news": k in fresh, "asks": k in asking} for k in leaders]
    return {"since": since.isoformat(timespec="seconds") if since else "", "heads": heads, "waits": waits, "posts": stacks(news), "seen": seen}
