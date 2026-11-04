"""A change to a spec asked of the Orkmaster (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md C; decisions §224.4, §225.2–3): the person's words, routed by the
Orkmaster to the leaders whose sections they touch, rewritten by them, and kept as one record that waits in the hand until the person accepts, talks more or drops it.
No face, no model: core/idea_spec_change.py makes it, gui/ideas_spec_change.py answers for it.

    FILE                                       # <state_folder>/spec_changes.json: {"changes": [record]}
    read / get / put / drop (state_dir, slug, …)
    open_on(state_dir, slug)                   # a change is open on the goal: asked and not answered yet (asking · ready), which holds the look's wait (A.4)
    sections(root, slug)                       # [{party, title}]: the parties that have a section in the goal's spec
    mention(root, text)                        # the party an `@Tech` in the words names ("" with none): §224.5's one leader, which goes to `ideas.change`
    by_code(root, state_dir, slug, text)       # the sections' parties the words touch, read by code (their name in the words, the goal types the words say): the preview's
    estimate(state_dir, root, parties, settings)   # {calls, usd_low, usd_high}: the route's call, each party's rewrite, the join; priced from the tiers they run on
    rows(state_dir, slug, ctx=None)            # the Needs you rows (`kind: "spec_change"`, asked by the Orkmaster) of a goal's change

A record is `{id, idea, text, status, parties: [{party, title, why, before: {tasks, lines}, after: {tasks, lines}, change}], agree: {ok, line}, estimate, made_at, error}`:
`status` asking · ready · failed; `before`/`after` as realm/leader_change.py keeps them; `change` the plan change as the runner takes it (realm/idea_change.py).
"""
from __future__ import annotations

import re
import secrets
from pathlib import Path

from orkboard.realm import goal_route, idea_target, ideas, leader_change, spec_sections

FILE = "spec_changes.json"
STATUS = ("asking", "ready", "failed")
OPEN = ("asking", "ready")                 # …a failed one holds nothing (spec 144 A.4)
KEEP = 20
SPREAD = goal_route.SPREAD
CHANGE_STATES = tuple(x for x in leader_change.CHANGE_STATES if x != "working") + ("ready",)      # a spec made or being made: not a goal at work (that is spec 128 E's change of one leader)
TEXT_CHARS = 1_000


def new_id() -> str:
    return "s" + secrets.token_hex(4)


def _path(state_dir: Path, slug: str) -> Path:
    return ideas.state_folder(state_dir, slug) / FILE


def read(state_dir: Path, slug: str) -> list[dict]:
    """The changes asked of the Orkmaster about the goal, the oldest first."""
    got = (ideas._json(_path(state_dir, slug)) or {}).get("changes")
    return [dict(r) for r in got if isinstance(r, dict) and r.get("id")] if isinstance(got, list) else []


def get(state_dir: Path, slug: str, cid: str) -> dict | None:
    return next((r for r in read(state_dir, slug) if r["id"] == cid), None)


def put(state_dir: Path, slug: str, rec: dict) -> dict:
    """A record saved: replaces the one of its id, else added last."""
    with ideas.LOCK:
        rows_ = [r for r in read(state_dir, slug) if r["id"] != rec["id"]]
        ideas._write_json(_path(state_dir, slug), {"changes": [*rows_, rec][-KEEP:]})
    return rec


def drop(state_dir: Path, slug: str, cid: str) -> bool:
    """A record taken away; False when there was none."""
    with ideas.LOCK:
        rows_ = read(state_dir, slug)
        left = [r for r in rows_ if r["id"] != cid]
        if len(left) == len(rows_):
            return False
        ideas._write_json(_path(state_dir, slug), {"changes": left})
    return True


def open_on(state_dir: Path, slug: str) -> bool:
    return any(r.get("status") in OPEN for r in read(state_dir, slug))


# -- the sections and where the words go (by code) ------------------------------------------------------------------------------------------------

def sections(root: Path, slug: str) -> list[dict]:
    """`[{party, title}]`: the parties with a section of their own in the goal's spec (a page of before has none), in the order written."""
    page = ideas.idea_page(root, slug)
    if page is None:
        return []
    parties = [{"slug": t["slug"], "title": t["title"]} for t in ideas.tracks(root, make=False)]
    return [{"party": s.party, "title": s.title} for s in spec_sections.read(page, parties)["sections"] if s.party and not s.older]


def mention(root: Path, text: str) -> str:
    """The party an `@Name` in the words names (its title or slug, any case); "" with none. §224.5: one leader directly."""
    by = {}
    for t in ideas.tracks(root, make=False):
        by[str(t["slug"]).lower()] = t["slug"]
        by[str(t["title"]).lower()] = t["slug"]
    for m in re.finditer(r"(?<![\w@])@([\w-]+)", str(text or "")):
        if m.group(1).lower() in by:
            return by[m.group(1).lower()]
    return ""


def by_code(root: Path, state_dir: Path, slug: str, text: str) -> list[str]:
    """The slugs of the parties whose sections the words touch, in the spec's order, read by code: a party named in the words (its title or slug as a word), else the parties the goal types the
    words say name (`goal_route.route`) that have a section; where code finds none, every party that has a section (the Orkmaster's call narrows it)."""
    mine = sections(root, slug)
    if not mine:
        return []
    said = str(text or "").lower()
    named = [m["party"] for m in mine if any(re.search(rf"(?<!\w){re.escape(w.lower())}(?!\w)", said) for w in {m["title"], m["party"]} if w)]
    if named:
        return named
    typed = {r["party"] for r in goal_route.route(state_dir, root, str(text or ""))["route"]}
    found = [m["party"] for m in mine if m["party"] in typed]
    return found or [m["party"] for m in mine]


def estimate(state_dir: Path, root: Path, parties: list[str], settings: dict | None = None) -> dict:
    """`{calls, usd_low, usd_high}` read by code before any model: the Orkmaster's route (step `route`), each party's rewrite (step `plan`, under its Target) and, with more than one party,
    the join; each priced from the tier its step runs on; ±50 %."""
    base, calls = 0.0, 0

    def one(step: str, slug: str = "") -> None:
        nonlocal base, calls
        got = idea_target.pick(step, idea_target.target_for(settings, ideas.track_page(root, slug) if slug else None))
        if got is not None:
            calls += 1
            base += idea_target.floor(idea_target.tier_of(got[0]))
    one("route")
    for p in parties:
        one("plan", p)
    if len(parties) > 1:
        one("join")
    return {"calls": calls, "usd_low": round(base * SPREAD[0], 2), "usd_high": round(base * SPREAD[1], 2)}


# -- the Needs you rows ------------------------------------------------------------------------------------------------------------------------

def rows(state_dir: Path, slug: str, ctx: dict | None = None) -> list[dict]:
    """The goal's change as a Needs you row (one a goal; one still `asking` is a row too, to say *Its leaders are rewriting*): `{kind: "spec_change", asker: "orkmaster", id, task (the id again, the
    stop's key), said, status, text, agree: {ok, line}, parties, calls, usd_low, usd_high, error, at, low, reset}`; the caller adds the goal's own fields. `ctx`: `goal_route.context` (whether the
    limits run low, and until when)."""
    ctx = ctx or {}
    out = []
    for r in read(state_dir, slug)[-1:]:
        if r.get("status") not in STATUS:
            continue
        est = r.get("estimate") if isinstance(r.get("estimate"), dict) else {}
        agree = r.get("agree") if isinstance(r.get("agree"), dict) else {"ok": True, "line": ""}
        out.append({"kind": "spec_change", "asker": "orkmaster", "id": r["id"], "task": r["id"], "said": str(r.get("text") or ""), "status": r["status"], "blocks": False,
                    "text": str(r.get("error") or "No change came: ask again") if r["status"] == "failed" else str(agree.get("line") or r.get("text") or ""),
                    "agree": agree, "parties": [p for p in r.get("parties") or [] if isinstance(p, dict)], "calls": est.get("calls"),
                    "usd_low": est.get("usd_low"), "usd_high": est.get("usd_high"), "error": str(r.get("error") or ""), "at": str(r.get("made_at") or ""),
                    "low": bool(ctx.get("low")), "reset": str(ctx.get("until") or ""), "level": "spec"})
    return out
