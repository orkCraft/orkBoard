"""A change asked of a leader (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md E; decisions §206.5): the person's words to a leader about a goal that
is agreed or at work (the bubble's *Make it a change*). The leader replans its part from them and the result waits as one decision in the hand: its plan now and proposed,
its price, *Accept*, *Talk more*, *Keep the spec*; a Design leader answers with three looks to choose from instead. No face, no model: the keeper makes it
(core/idea_leader_change.py), the host answers it (gui/ideas_change.py).

    CHANGE_STATES                              # the states of a goal a change may be asked on
    read / get / put / drop (state_dir, slug, …)   # <state_folder>/leader_changes.json: {"changes": [record]}
    owned(root, plan, idea_party, party)       # the ids of the plan's tasks that are this party's and not started
    snapshot(tasks, ids)                       # [{id, title, short, op}]: tasks as the card draws them
    proposal(root, plan, idea_party, party, got)   # `before` and `after` of a change as the keeper cleaned it
    spec_lines(root, slug, party)              # the party's *Will be* lines of the goal now (the card's *Now*)
    write_lines(root, slug, party, lines)      # …and the lines it proposes written into its section (a page of before has none: False)
    rows(state_dir, slug)                      # the Needs you rows (`kind: "leader_change"`) of a goal

A record is `{id, idea, party, part, text, status, shape, made_at, why, before, after, change, looks, estimate, error}`: `status` asking · ready · failed; `shape` plan · looks;
`before`/`after` `{tasks: [{id, title, short, op}], lines: [text]}` (`op`: "" the task as it is, change, add, drop); `change` the plan change as the runner takes it
(realm/idea_change.py: `change`, `drop`, `add`); `looks` `[{key, name, why, lines}]` for a Design leader; `estimate` `{usd_low, usd_high}`.
"""
from __future__ import annotations

import secrets
from pathlib import Path

from orkboard.realm import goal_team, idea_change, ideas, spec_sections
from orkboard.realm.idea_words import short_of

FILE = "leader_changes.json"
CHANGE_STATES = ("decided", "sketch", "sections", "planning", "plan", "working")       # agreed or at work: a goal done is a new goal's business (spec 128 E.1)
STATUS = ("asking", "ready", "failed")
LINES = 12                         # the lines of a change a leader proposes, at most
LINE_CHARS = 200
LOOKS = 3
KEEP = 20                          # the changes kept for a goal: the oldest go first


def new_id() -> str:
    return "c" + secrets.token_hex(4)


# -- the file -----------------------------------------------------------------------------------------------------------------------------------

def _path(state_dir: Path, slug: str) -> Path:
    return ideas.state_folder(state_dir, slug) / FILE


def read(state_dir: Path, slug: str) -> list[dict]:
    """The changes asked of the goal's leaders, the oldest first."""
    got = (ideas._json(_path(state_dir, slug)) or {}).get("changes")
    return [dict(r) for r in got if isinstance(r, dict) and r.get("id")] if isinstance(got, list) else []


def get(state_dir: Path, slug: str, cid: str) -> dict | None:
    return next((r for r in read(state_dir, slug) if r["id"] == cid), None)


def put(state_dir: Path, slug: str, rec: dict) -> dict:
    """A record saved: replaces the one of its id, else added last."""
    with ideas.LOCK:
        rows = [r for r in read(state_dir, slug) if r["id"] != rec["id"]]
        ideas._write_json(_path(state_dir, slug), {"changes": [*rows, rec][-KEEP:]})
    return rec


def drop(state_dir: Path, slug: str, cid: str) -> bool:
    """A record taken away; False when there was none."""
    with ideas.LOCK:
        rows = read(state_dir, slug)
        left = [r for r in rows if r["id"] != cid]
        if len(left) == len(rows):
            return False
        ideas._write_json(_path(state_dir, slug), {"changes": left})
    return True


# -- the plan now and proposed --------------------------------------------------------------------------------------------------------------------

def owned(root: Path, plan: dict | None, idea_party: str, party: str) -> set[str]:
    """The ids of the plan's tasks that are `party`'s and not started (spec 62's `open_task`): by their role (the party's team and its leader), a task with no role by the
    party the plan was made in (`idea_party`)."""
    team = {*goal_team.team_of(root, party), goal_team.leader_of(root, party)}
    out = set()
    for t in (plan or {}).get("tasks") or []:
        if not isinstance(t, dict) or not idea_change.open_task(t):
            continue
        role = str(t.get("role") or "")
        if role in team or (not role and party == idea_party):
            out.add(str(t.get("id")))
    return out


def snapshot(tasks: list[dict], ids: set[str] | None = None, ops: dict[str, str] | None = None) -> list[dict]:
    """Tasks as the card draws them: `{id, title, short, op}`, those of `ids` only when given; `ops`: a task's id → what is done to it (default "")."""
    return [{"id": str(t.get("id") or ""), "title": str(t.get("title") or ""), "short": str(t.get("short") or short_of(str(t.get("title") or ""))),
             "op": (ops or {}).get(str(t.get("id")), "")}
            for t in tasks if isinstance(t, dict) and (ids is None or str(t.get("id")) in ids)]


def clean_lines(value: object) -> list[str]:
    """The lines a leader proposes: text only, one line each, at most LINES of LINE_CHARS."""
    if not isinstance(value, list):
        return []
    lines = [" ".join(str(v).split())[:LINE_CHARS] for v in value if isinstance(v, (str, int, float)) and not isinstance(v, bool)]
    return [ln for ln in lines if ln][:LINES]


def proposal(root: Path, state_dir: Path, slug: str, plan: dict | None, idea_party: str, party: str, got: dict, lines: list[str]) -> tuple[dict, dict]:
    """`(before, after)` of a change as the keeper cleaned it (`got`: `change`, `drop`, `add`), restricted to the party's tasks not started: `before` the tasks as they are
    (those the change changes or drops marked), `after` the tasks as they will be (the dropped gone, the changed as changed, the added last); the lines now and proposed."""
    ids = owned(root, plan, idea_party, party)
    tasks = [t for t in (plan or {}).get("tasks") or [] if isinstance(t, dict) and str(t.get("id")) in ids]
    changed = {str(c["id"]): c for c in got.get("change") or []}
    dropped = {str(i) for i in got.get("drop") or []}
    ops = {**{i: "change" for i in changed}, **{i: "drop" for i in dropped}}
    now = [{**s, "op": ops.get(s["id"], "")} for s in snapshot(tasks)]
    then = [{"id": str(t["id"]), "title": str(changed[str(t["id"])].get("title") or t.get("title") or ""),
             "short": str(changed[str(t["id"])].get("short") or t.get("short") or ""), "op": "change"} if str(t["id"]) in changed
            else {**s, "op": ""} for t, s in zip(tasks, snapshot(tasks)) if str(t["id"]) not in dropped]
    then += [{"id": "", "title": str(a.get("title") or ""), "short": str(a.get("short") or short_of(str(a.get("title") or ""))), "op": "add"} for a in got.get("add") or []]
    return {"tasks": now, "lines": spec_lines(root, slug, party)}, {"tasks": then, "lines": lines}


# -- the party's lines in the spec ---------------------------------------------------------------------------------------------------------------

def _section(page: ideas.Page | None, root: Path, party: str) -> spec_sections.Section | None:
    """The party's own section of a page of the new format; None on a page of before or one where the party has none."""
    if page is None:
        return None
    parties = [{"slug": t["slug"], "title": t["title"]} for t in ideas.tracks(root, make=False)]
    return next((s for s in spec_sections.read(page, parties, party)["sections"] if s.party == party and not s.older), None)


def spec_lines(root: Path, slug: str, party: str) -> list[str]:
    """The party's *Will be* lines of the goal as its spec has them now (its section's part; none on a page of before)."""
    sec = _section(ideas.idea_page(root, slug), root, party)
    return spec_sections.items(sec.parts.get("Will be", "")) if sec else []


def write_lines(root: Path, slug: str, party: str, lines: list[str]) -> bool:
    """The party's *Will be* part replaced by `lines` (its other parts and every other section as they were). False when the goal's page has no section of the party."""
    with ideas.LOCK:
        page = ideas.idea_page(root, slug)
        sec = _section(page, root, party)
        if page is None or sec is None:
            return False
        parts = dict(sec.parts)
        parts["Will be"] = "\n".join(f"- {ln}" for ln in lines)
        page.sections = [(n, spec_sections.join(parts) if n == sec.title else t) for n, t in page.sections]
        ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
    return True


# -- the Needs you rows -----------------------------------------------------------------------------------------------------------------------

def rows(state_dir: Path, slug: str, root: Path | None = None) -> list[dict]:
    """The rows of the goal's changes that wait for the person (one that is still asked is none yet): `{kind: "leader_change", level: "spec", pulls (realm/way_down.py: the party's open tasks the change pulls after it, and their price; `root` given), id, task (the id again, the stop's key), goal (the
    party asked: the card lies under its lane), party, part, said, shape, status, text, why, before, after, looks, usd_low, usd_high, error, at}`."""
    out = []
    for r in read(state_dir, slug):
        if r.get("status") not in ("ready", "failed"):
            continue
        est = r.get("estimate") if isinstance(r.get("estimate"), dict) else {}
        looks = r.get("shape") == "looks"
        out.append({"kind": "leader_change", "id": r["id"], "task": r["id"], "goal": str(r.get("party") or ""), "party": str(r.get("party") or ""), "part": str(r.get("part") or ""),
                    "said": str(r.get("text") or ""), "shape": "looks" if looks else "plan", "status": r["status"], "blocks": False,
                    "text": str(r.get("error") or "No change came: ask again") if r["status"] == "failed" else str(r.get("why") or r.get("text") or ""),
                    "why": str(r.get("why") or ""), "before": r.get("before") or {"tasks": [], "lines": []}, "after": r.get("after") or {"tasks": [], "lines": []},
                    "looks": r.get("looks") or [], "usd_low": est.get("usd_low"), "usd_high": est.get("usd_high"), "error": str(r.get("error") or ""),
                    "at": str(r.get("made_at") or ""), "level": "spec",
                    "pulls": _pulls(state_dir, root, slug, str(r.get("party") or ""))})
    return out


def _pulls(state_dir: Path, root: Path | None, slug: str, party: str) -> dict:
    """What a change of the party's section pulls (spec 132 C.2); nothing pulled when the root is not given or a read fails (a row is never lost to its price)."""
    from orkboard.realm import way_down                     # way_down reads this module's `owned`
    if root is None:
        return way_down.empty("spec")
    try:
        return way_down.pulls(state_dir, root, "spec", slug=slug, party=party)
    except Exception:
        return way_down.empty("spec")
