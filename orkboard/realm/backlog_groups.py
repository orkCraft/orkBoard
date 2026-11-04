"""The backlog's groups (docs/specs/135-a-new-goal-matched-against-the-face-down-pile.md §B; decisions §242.5): once at the reset, before the queue of §239 starts its first goal, one call
of the Orkmaster over the titles of the goals put off says which of them look like one goal. The answer waits as **one card** in the hand, *These look like one goal*. No model and no face
here: the call is `core/idea_groups.py`'s, the answers are `gui/ideas_groups.py`'s; this module keeps the record, cleans the answer strictly and bounds each group by code.

    backlog_groups.reset_key(held_untils)             # the reset of the goals ripe: the earliest `held_until` that has passed ("" with none)
    backlog_groups.asked(rec, key)                    # True when the record covers the reset `key` (a call was made at or after it)
    backlog_groups.read(state_dir) / save(state_dir, rec) / set_open(state_dir, rid, open, now)   # <state_dir>/backlog_groups.json, written whole under a lock
    backlog_groups.new(reset, groups)                 # a record: `ready` with groups, else `none`
    backlog_groups.lifted(rec, now)                   # the card lies lifted and fresh: the queue waits (a face that is gone never holds it past LIFT_S)
    backlog_groups.clean(answer, ripe, root, state_dir)   # the model's answer, strictly: [{id, goals: [slug], why, answer: ""}]
    backlog_groups.fits_group(root, state_dir, slugs) # joining the others into the first stays small (A's rule, `goal_match.fits`, for the whole group)
    backlog_groups.rows(state_dir, root, settings)    # [] or the one Needs you row `{kind: "groups", id, groups: [{id, goals: [{idea, title, party, head}], why, adds}], cost, blocks, priority, at}`

The record is `{"reset": "<reset_key>", "at": "…", "status": "ready" | "answered" | "none", "groups": [{"id": "g-…", "goals": [slug, …], "why": "…", "answer": "" | "join" | "apart"}],
"open": false, "open_at": ""}`. The card's id is the record's `reset`.
"""
from __future__ import annotations

import datetime as dt
import json
import secrets
import threading
from pathlib import Path
from typing import Any, Iterable

from orkboard.realm import goal_match, goal_refine, goal_team, idea_target, ideas, roles

FILE = "backlog_groups.json"
STATUS = ("ready", "answered", "none")
ANSWERS = ("", "join", "apart")
TITLE_CHARS = 80               # a title as the call is given it
GOALS_MAX = 40                 # the goals one call is given, at most
CHARS = 3_000                  # the most the call reads (as `idea_collide.CHARS`)
GROUPS_MAX = 5
GROUP_MAX = 4
WHY_CHARS = 160
LIFT_S = 600                   # the queue waits for the card only this long since it was lifted
_LOCK = threading.Lock()


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _file(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


def reset_key(held_untils: Iterable[str]) -> str:
    """The reset the goals ripe belong to: the earliest of their `held_until` ("" when there is none)."""
    return min((str(h) for h in held_untils if h), default="")


def asked(rec: dict | None, key: str) -> bool:
    """The record covers the reset `key`: a call was made at or after the earliest ripe `held_until` (so the goals of a reset that still wait are never asked about twice)."""
    return bool(rec and key and rec.get("at") and key <= str(rec["at"]))


# -- the store ----------------------------------------------------------------------------------------------------------------------------

def read(state_dir: Path) -> dict:
    """The record, or {} when there is none (a file that is missing or broken)."""
    try:
        raw = json.loads(_file(state_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict) or raw.get("status") not in STATUS or not isinstance(raw.get("reset"), str):
        return {}
    groups = []
    for g in raw.get("groups") if isinstance(raw.get("groups"), list) else []:
        if isinstance(g, dict) and isinstance(g.get("id"), str) and isinstance(g.get("goals"), list):
            groups.append({"id": g["id"], "goals": [str(s) for s in g["goals"] if isinstance(s, str)], "why": str(g.get("why") or ""),
                           "answer": g.get("answer") if g.get("answer") in ANSWERS else ""})
    return {"reset": raw["reset"], "at": str(raw.get("at") or ""), "status": raw["status"], "groups": groups, "open": raw.get("open") is True, "open_at": str(raw.get("open_at") or "")}


def _write(state_dir: Path, rec: dict) -> None:
    f = _file(state_dir)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)


def save(state_dir: Path, rec: dict) -> dict:
    """The record kept, whole. OSError for a disk that refused."""
    with _LOCK:
        _write(state_dir, rec)
    return rec


def new(reset: str, groups: list[dict]) -> dict:
    """A record for the reset `reset`: `ready` for the groups, `none` with no group (the queue goes on at once)."""
    return {"reset": reset, "at": _now(), "status": "ready" if groups else "none", "groups": [dict(g) for g in groups], "open": False, "open_at": ""}


def update(state_dir: Path, rid: str, **fields: Any) -> dict | None:
    """The fields of the record of the card `rid` changed (under the lock); None when the record is another's."""
    with _LOCK:
        rec = read(state_dir)
        if not rec or rec["reset"] != rid:
            return None
        rec.update(fields)
        _write(state_dir, rec)
        return rec


def set_open(state_dir: Path, rid: str, open_: bool, now: str = "") -> dict | None:
    """The face says the card is lifted (`open_`) or put down; only while it is `ready`."""
    with _LOCK:
        rec = read(state_dir)
        if not rec or rec["reset"] != rid or rec["status"] != "ready":
            return None
        rec.update(open=bool(open_), open_at=(now or _now()) if open_ else "")
        _write(state_dir, rec)
        return rec


def lifted(rec: dict | None, now: float) -> bool:
    """The card is ready, lies lifted and was lifted less than LIFT_S ago: the queue waits for it."""
    if not rec or rec.get("status") != "ready" or not rec.get("open"):
        return False
    try:
        return now - dt.datetime.fromisoformat(rec["open_at"]).timestamp() < LIFT_S
    except ValueError:
        return False


# -- the answer, strictly -------------------------------------------------------------------------------------------------------------------

def _route_parties(state_dir: Path, slug: str, home: str) -> list[str]:
    out = [r.get("party") if isinstance(r, dict) else r for r in ideas.state(state_dir, slug)["route"] or ()]
    return [p for p in dict.fromkeys(out) if p] or ([home] if home else [])


def parties_of(root: Path, state_dir: Path, slug: str) -> list[str]:
    page = ideas.idea_page(root, slug)
    return _route_parties(state_dir, slug, str(page.get("track") or "") if page is not None else "")


def fits_group(root: Path, state_dir: Path, slugs: list[str]) -> bool:
    """Joining the others of `slugs` into the first (in the order given) adds no more than one party to its route in all, and its Gist and every `Added:` line stay within `JOIN_CHARS`
    (`goal_match.fits`, asked once for all the words that would join)."""
    if len(slugs) < 2:
        return False
    texts, parties = [], []
    for s in slugs[1:]:
        page = ideas.idea_page(root, s)
        if page is None:
            return False
        texts.append(goal_refine.words(page).strip())
        parties += parties_of(root, state_dir, s)
    return goal_match.fits(root, state_dir, slugs[0], f"\n\n{goal_refine.ADDED}".join(texts), parties)


def _one_line(v: object, n: int) -> str:
    return " ".join(str(v or "").split())[:n].rstrip() if isinstance(v, (str, int, float)) and not isinstance(v, bool) else ""


def clean(answer: object, ripe: list[str], root: Path | None = None, state_dir: Path | None = None) -> list[dict]:
    """The groups of the model's answer (`{"groups": [{"goals": [slug…], "why": "…"}]}`), strictly. `ripe`: the slugs of the goals it was given, in the Orkmaster's order. A slug that was not
    given is dropped; a goal in a second group is dropped from it; a group of fewer than two goals is dropped; a group has at most GROUP_MAX goals (the first in the order, the rest go on alone)
    and a list at most GROUPS_MAX groups; `why` is one line of WHY_CHARS. With `root` and `state_dir` each group is then checked as `fits_group`: a group that fails goes on alone, its goals unjoined.
    `[{id, goals (in the Orkmaster's order), why, answer: ""}]`, [] for anything that is no answer."""
    raw = answer.get("groups") if isinstance(answer, dict) else None
    if not isinstance(raw, list):
        return []
    order = {s: n for n, s in enumerate(ripe)}
    used: set[str] = set()
    out: list[dict] = []
    for g in raw:
        goals = g.get("goals") if isinstance(g, dict) else None
        if not isinstance(goals, list):
            continue
        mine = sorted({s for s in goals if isinstance(s, str) and s in order and s not in used}, key=order.__getitem__)[:GROUP_MAX]
        if len(mine) < 2:
            continue
        if root is not None and state_dir is not None and not fits_group(root, state_dir, mine):
            continue
        used.update(mine)
        out.append({"id": "g-" + secrets.token_hex(3), "goals": mine, "why": _one_line(g.get("why"), WHY_CHARS), "answer": ""})
        if len(out) >= GROUPS_MAX:
            break
    return out


# -- the card -----------------------------------------------------------------------------------------------------------------------------

def rows(state_dir: Path, root: Path | None = None, settings: dict | None = None) -> list[dict]:
    """The one Needs you row of the groups `ready` (`realm/board_rows.py` lays it): `{kind: "groups", id, groups: [{id, goals: [{idea, title, party, head}], why, adds}], cost, blocks, priority, at}`.
    `adds` is the party a group would add to the first goal's route ([] or one); `cost` is what the joins would cost in all, `{calls, usd_high}` (a first goal whose decision is worded is worded
    again: one `decide` call; none before its decision, only words move), None when none. A goal gone from the Board leaves its group; a group left with one goal leaves the card."""
    rec = read(state_dir)
    if not rec or rec["status"] != "ready" or root is None:
        return []
    out, calls, usd = [], 0, 0.0
    for g in rec["groups"]:
        if g["answer"]:
            continue
        pages = {s: ideas.idea_page(root, s) for s in g["goals"]}
        slugs = [s for s in g["goals"] if pages[s] is not None]
        if len(slugs) < 2:
            continue
        goals = []
        for s in slugs:
            party = str(pages[s].get("track") or "")
            goals.append({"idea": s, "title": _one_line(pages[s].title, TITLE_CHARS), "party": party, "head": _head(state_dir, root, party, settings)})
        have = set(parties_of(root, state_dir, slugs[0]))
        adds = sorted({p for s in slugs[1:] for p in parties_of(root, state_dir, s)} - have)
        if ideas.state(state_dir, slugs[0])["state"] == "decided":
            calls += 1
            usd += idea_target.budget("decide", idea_target.target_for(settings, ideas.track_page(root, goals[0]["party"]) if goals[0]["party"] else None)) or 0.0
        out.append({"id": g["id"], "goals": goals, "why": g["why"], "adds": adds})
    if not out:
        return []
    return [{"kind": "groups", "id": rec["reset"], "groups": out, "cost": {"calls": calls, "usd_high": round(usd, 4)} if calls else None, "blocks": False, "priority": "normal", "at": rec["at"]}]


def _head(state_dir: Path, root: Path, party: str, settings: dict | None) -> dict:
    """The head of the party's leader, as the card draws a goal's asker; {} for a goal of no party."""
    if not party or ideas.track_page(root, party) is None:
        return {}
    lead = roles.role(state_dir, goal_team.leader_of(root, party)) or roles.role(state_dir, roles.TASKMASTER)
    try:
        return goal_team.head_in(root, party, lead, idea_target.target_for(settings, ideas.track_page(root, party)))
    except Exception:                                          # a head is never worth the card
        return {}
