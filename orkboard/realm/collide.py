"""Two goals of different parties that change the same thing (docs/specs/71-orkmaster-keeps-parties-apart.md, decisions §86): what a goal
touches, the overlap with the open goals of other parties, the questions the Orkmaster asks about it and the answers kept, a goal that waits
for another party's flag. Code only: the judge that tells a collision from a coincidence is core/idea_collide.py.

    touches(root, state_dir, "auth-api")           # ["orkboard/realm/", "orkboard/realm/x.py", …]: its page's `touches`, its plan's files, normalised
    overlaps(root, state_dir, "auth-api")          # [{"other": slug, "paths": [shared paths]}] with the open goals of other parties; [] with none
    pair_id("b", "a")                              # "a|b": the pair, sorted
    known(state_dir, "a|b", "plan")                # asked already (open) or answered: never asked again (a changed spec may ask once more)
    add_open / add_answered / take_open / put_back # <state_dir>/collide.json: `{"open": [...], "answered": [last 200]}`
    rows(root, state_dir)                          # the Needs you rows (`kind: "collide"`, spec 71 §8.1), on the goal asked about
    collisions(root, state_dir)                    # the project's level: [{"id", "a", "b"}], the open ones
    waits_for(...) / holds(root, state_dir, slug)  # a goal's `depends_on` across parties: the node's `waits_for`; whether its start is held
    work(repo_root, now)                           # what the Orkmaster's stops did in the last week: asked, answered, taken, usd

A goal's touches are read, never written. A stop is `{id, by, asked, other, why, first, at}`: `asked` the goal the question is on (the later
of the two by its plan's `made_at`, or the goal whose spec did not change), `other` the one beside it. No face, no model, no git.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from orkboard.realm import event_log, idea_flag, ideas, pitches, releases

FILE = "collide.json"
KEEP = 200                         # the answers kept
OPEN_MAX = 50                      # the questions kept open: the oldest beyond goes
BY = ("plan", "change")            # how a stop was found: a plan was made · a spec changed after it
NOT_OPEN = ("done", "passed", "sent", "proposed")        # a goal in these states is not open (judging and judged are a pitch's: left out by its party)
MAX_PATHS = 40                     # the most paths a goal's touches keep
WHY_CHARS = 200
_DOC_SUFFIX = (".md", ".rst", ".txt")
_BRIEF_PATH = re.compile(r"`([A-Za-z0-9_./-]+)`")


# -- what a goal touches (§1) -----------------------------------------------------------------------------------------

def norm(path: object) -> str:
    """A path as touches compare it: forward slashes, no leading `./` or `/`, no glob tail; a folder (a trailing `/`, or a last name with no
    dot) ends with `/`. "" for what is not a path (prose, a dot, a long line)."""
    p = str(path or "").strip().strip("`'\"").replace("\\", "/")
    p = re.sub(r"/{2,}", "/", p)
    while p.startswith("./"):
        p = p[2:]
    p = re.sub(r"/?\*+$", "/", p.lstrip("/"))
    if not p or p in (".", "/") or " " in p or "*" in p or len(p) > 200:
        return ""
    last = p.rstrip("/").rsplit("/", 1)[-1]
    return p if p.endswith("/") else (p if "." in last else p + "/")


def is_docs(path: str) -> bool:
    return path.startswith(("docs/", "doc/")) or path.endswith(_DOC_SUFFIX)


def is_test(path: str) -> bool:
    last = path.rstrip("/").rsplit("/", 1)[-1]
    return path.startswith(("tests/", "test/")) or "/tests/" in path or last.startswith("test_") or last.endswith(("_test.py", ".test.js", ".spec.js"))


def _list(text: object) -> list[str]:
    try:
        got = json.loads(text) if str(text or "").strip() else []
    except ValueError:
        return []
    return [str(x) for x in got if isinstance(x, str)] if isinstance(got, list) else []


def touches(root: Path, state_dir: Path, slug: str) -> list[str]:
    """What a goal touches, normalised, each once, sorted: the paths its page's `touches` names (as core/idea_keeper.py reads it), the files
    its plan's tasks name (a `files` list, or a path in backticks in the brief), and the files its merged tasks changed (their `files`). Read
    only; [] for a goal that is gone or names none."""
    page = ideas.idea_page(root, slug)
    if page is None:
        return []
    found = _list(page.get("touches"))
    for t in (ideas.plan(state_dir, slug) or {}).get("tasks") or []:
        if not isinstance(t, dict):
            continue
        if isinstance(t.get("files"), list):
            found += [str(f) for f in t["files"] if isinstance(f, str)]
        if t.get("state") != "merged":
            found += [m for m in _BRIEF_PATH.findall(str(t.get("brief") or "")) if "/" in m]
    return sorted({p for p in (norm(f) for f in found) if p})[:MAX_PATHS]


def _code(paths: list[str]) -> list[str]:
    return [p for p in paths if not is_docs(p) and not is_test(p)]


def shared(a: list[str], b: list[str]) -> list[str]:
    """The paths of two goals' touches that overlap: the same path, or a folder and what is in it (a module `orkboard/realm/x.py` and its
    folder `orkboard/realm/`). `tests/` and docs are left out, unless both goals touch docs only. Each shared path once, the deeper one."""
    if a and b and all(is_docs(p) for p in a) and all(is_docs(p) for p in b):
        pa, pb = a, b
    else:
        pa, pb = _code(a), _code(b)
    out = set()
    for x in pa:
        for y in pb:
            if x == y or (x.endswith("/") and y.startswith(x)):
                out.add(y)
            elif y.endswith("/") and x.startswith(y):
                out.add(x)
    return sorted(out)


# -- the open goals, the finder (§2.1) --------------------------------------------------------------------------------

def open_goals(root: Path, state_dir: Path, rows: list[dict] | None = None) -> list[dict]:
    """The goals a collision may name: not done, not dropped (gone), not a pitch, not a release, in a party but General. `rows`: `ideas.ideas(root)`."""
    out, ideation = [], {}
    for i in rows if rows is not None else ideas.ideas(root):
        if i["track"] not in ideation:
            ideation[i["track"]] = i["track"] == ideas.GENERAL or pitches.is_ideation(root, i["track"])
        if ideation[i["track"]]:
            continue
        if ideas.state(state_dir, i["slug"]).get("state") in NOT_OPEN or releases.read(state_dir, i["slug"]) is not None:
            continue
        out.append(i)
    return out


def overlaps(root: Path, state_dir: Path, slug: str, *, planned: bool = False) -> list[dict]:
    """What the goal shares with each open goal of another party: `[{"other": slug, "paths": [...]}]`, by slug; [] when it touches nothing,
    is not open, or nothing overlaps (no model is asked then). `planned`: only the goals that have a plan (a spec changed under them)."""
    page = ideas.idea_page(root, slug)
    mine = touches(root, state_dir, slug) if page is not None else []
    if not mine or ideas.state(state_dir, slug).get("state") in NOT_OPEN or releases.read(state_dir, slug) is not None \
            or page.get("track") == ideas.GENERAL or pitches.is_ideation(root, page.get("track") or ""):
        return []
    out = []
    for i in open_goals(root, state_dir):
        if i["slug"] == slug or i["track"] == page.get("track") or (planned and ideas.plan(state_dir, i["slug"]) is None):
            continue
        if paths := shared(mine, touches(root, state_dir, i["slug"])):
            out.append({"other": i["slug"], "paths": paths})
    return sorted(out, key=lambda o: o["other"])


def later_of(state_dir: Path, a: str, b: str) -> str:
    """Of two goals, the one a plan question is asked on: the later by its plan's `made_at`; a goal with no plan yet is later than one with
    a plan; a tie is `a` (the goal whose plan was just made)."""
    made = [str((ideas.plan(state_dir, s) or {}).get("made_at") or "") for s in (a, b)]
    if made[0] and made[1]:
        return b if made[1] > made[0] else a
    return b if made[0] and not made[1] else a


# -- the questions and the answers kept (§2.3) -------------------------------------------------------------------------

def pair_id(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


def path(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


def read(state_dir: Path) -> dict:
    """`{"open": [stop], "answered": [{id, by, answer, at, note?}]}`, as kept; empty with no file or a broken one."""
    try:
        data = ideas._json(path(state_dir))
    except ValueError:
        data = None
    data = data if isinstance(data, dict) else {}
    return {"open": [x for x in data.get("open") or [] if isinstance(x, dict) and x.get("id")],
            "answered": [x for x in data.get("answered") or [] if isinstance(x, dict) and x.get("id")]}


def _write(state_dir: Path, data: dict) -> None:
    data = {"open": data["open"][-OPEN_MAX:], "answered": data["answered"][-KEEP:]}
    ideas._write_json(path(state_dir), data)


def known(state_dir: Path, pair: str, by: str) -> bool:
    """Whether the pair is asked already (open) or answered: it is never asked again. A spec changed after the plan is new, though: a pair
    answered when its plans were made may still be asked once when a spec changes under it (`by` "change"); a plan made again never asks
    a pair that was answered by anything."""
    got = read(state_dir)
    return any(x["id"] == pair for x in got["open"]) or any(x["id"] == pair and (by == "plan" or x.get("by") == "change") for x in got["answered"])


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def add_open(state_dir: Path, pair: str, by: str, asked: str, other: str, why: str, first: str) -> dict:
    """A stop opened on `asked` (the goal beside it is `other`); `first` the judge's suggestion, "" or one of the two."""
    stop = {"id": pair, "by": by, "asked": asked, "other": other, "why": " ".join(str(why).split())[:WHY_CHARS],
            "first": first if first in (asked, other) else "", "at": _now()}
    with ideas.LOCK:
        got = read(state_dir)
        got["open"] = [x for x in got["open"] if x["id"] != pair] + [stop]
        _write(state_dir, got)
    return stop


def add_answered(state_dir: Path, pair: str, by: str, answer: str, note: str = "") -> None:
    """A pair answered (`answer`: the stop's, or "no" for a judge that said they do not collide), kept with the last 200."""
    with ideas.LOCK:
        got = read(state_dir)
        got["open"] = [x for x in got["open"] if x["id"] != pair]
        got["answered"] = [x for x in got["answered"] if not (x["id"] == pair and x.get("by") == by)] + [
            {"id": pair, "by": by, "answer": answer, "at": _now(), **({"note": note} if note else {})}]
        _write(state_dir, got)


def open_of(state_dir: Path, pair: str) -> dict | None:
    return next((x for x in read(state_dir)["open"] if x["id"] == pair), None)


def answered(state_dir: Path, pair: str) -> bool:
    return any(x["id"] == pair for x in read(state_dir)["answered"])


def take_open(state_dir: Path, pair: str) -> dict | None:
    """The open stop, claimed: a second press finds none."""
    with ideas.LOCK:
        got = read(state_dir)
        stop = next((x for x in got["open"] if x["id"] == pair), None)
        if stop is not None:
            got["open"] = [x for x in got["open"] if x["id"] != pair]
            _write(state_dir, got)
    return stop


def put_back(state_dir: Path, stop: dict) -> None:
    """A stop whose answer did not apply waits as it did (the answer kept for it is taken back)."""
    with ideas.LOCK:
        got = read(state_dir)
        got["answered"] = [x for x in got["answered"] if not (x["id"] == stop["id"] and x.get("by") == (stop.get("by") or "plan"))]
        got["open"] = [x for x in got["open"] if x["id"] != stop["id"]] + [stop]
        _write(state_dir, got)


def answers_of(stop: dict) -> list[str]:
    """What the person may answer: `first:<slug>` for each goal (the other waits for it), `one`, `leave`; by a changed spec `replan`, `leave`."""
    if stop.get("by") == "change":
        return ["replan", "leave"]
    return [f"first:{stop['other']}", f"first:{stop['asked']}", "one", "leave"]


# -- the faces' shapes (§8) -----------------------------------------------------------------------------------------

def _goal(root: Path, state_dir: Path, slug: str, parties: dict[str, str], state_of: Any) -> dict | None:
    page = ideas.idea_page(root, slug)
    st = state_of(slug)
    if page is None or st.get("state") in NOT_OPEN:
        return None
    party = page.get("track") or ideas.GENERAL
    return {"idea": slug, "party": party, "party_name": parties.get(party, party), "title": page.title, "element": st.get("element") or ""}


def rows(root: Path, state_dir: Path, *, tracks: list[dict] | None = None, state_of: Any = None) -> list[dict]:
    """The Needs you rows of the open stops (§8.1): on the goal asked about, `blocks: false`, priority normal. A stop whose goal is gone or
    done is not shown. `state_of(slug)`: the host's reading of a goal's state, else the file's."""
    stops = read(state_dir)["open"]
    if not stops:
        return []
    state_of = state_of or (lambda s: ideas.state(state_dir, s))
    parties = {t["slug"]: t["title"] for t in (tracks if tracks is not None else ideas.tracks(root, make=False))}
    out = []
    for s in stops:
        other, asked = (_goal(root, state_dir, s.get(k, ""), parties, state_of) for k in ("other", "asked"))
        if other is None or asked is None:
            continue
        change = s.get("by") == "change"
        text = (f"{other['party_name']} changed «{other['title']}»: «{asked['title']}» in {asked['party_name']} rests on what it was" if change else
                f"{asked['party_name']} «{asked['title']}» and {other['party_name']} «{other['title']}» change the same thing")
        out.append({"kind": "collide", "idea": asked["idea"], "goal": asked["party"], "title": asked["title"], "priority": "normal", "blocks": False,
                    "at": s.get("at") or "", "text": text,
                    "collide": {"id": s["id"], "by": s.get("by") or "plan", "why": s.get("why") or "", "first": s.get("first") or "",
                                "goals": [other, asked], "answers": answers_of(s)}})
    return out


def collisions(root: Path, state_dir: Path, *, state_of: Any = None) -> list[dict]:
    """The project's level (§8.4): the open stops as `{"id", "a", "b"}` (the pair sorted, as its id is)."""
    state_of = state_of or (lambda s: ideas.state(state_dir, s))
    out = []
    for s in read(state_dir)["open"]:
        a, b = sorted((s.get("asked", ""), s.get("other", "")))
        if all(ideas.idea_page(root, x) is not None and state_of(x).get("state") not in NOT_OPEN for x in (a, b)):
            out.append({"id": s["id"], "a": a, "b": b})
    return out


# -- a goal that waits for another party's (§4) ---------------------------------------------------------------------

def waits_for(state_dir: Path, slug: str, depends: list[str], party: str, track_of: dict[str, str], titles: dict[str, str],
              parties: dict[str, str]) -> list[dict]:
    """A node's `waits_for` (§8.3): the goals of other parties its `depends_on` names that still exist, `[{goal, party, party_name, title,
    flag}]` (`flag` the date the goal's flag was raised, "" before; the wait ends then); [] with none."""
    out = []
    for d in depends:
        if d == slug or d not in track_of or track_of[d] == party:
            continue
        flag = idea_flag.flag_of(state_dir, d)
        out.append({"goal": d, "party": track_of[d], "party_name": parties.get(track_of[d], track_of[d]), "title": titles.get(d, d),
                    "flag": str(flag.get("at") or "") if flag else ""})
    return out


def holds(root: Path, state_dir: Path, slug: str) -> list[str]:
    """The goals of other parties this goal waits for and whose flag is not raised yet; [] when its start is free."""
    page = ideas.idea_page(root, slug)
    if page is None:
        return []
    out = []
    for d in _list(page.get("depends_on")):
        other = ideas.idea_page(root, d)
        if other is not None and d != slug and (other.get("track") or "") != (page.get("track") or "") and idea_flag.flag_of(state_dir, d) is None:
            out.append(d)
    return out


def chain(root: Path, slug: str) -> set[str]:
    """Every goal this one waits for, through the goals they wait for (its `depends_on`, deeply): what a new wait must not close a cycle on."""
    seen, todo = set(), [slug]
    while todo:
        for d in _list((ideas.idea_page(root, todo.pop()) or ideas.Page()).get("depends_on")):
            if d not in seen:
                seen.add(d)
                todo.append(d)
    return seen


def waiters(root: Path, slug: str, rows_: list[dict] | None = None) -> list[str]:
    """The goals of other parties whose `depends_on` names this goal (they may start once its flag is raised)."""
    mine = (ideas.idea_page(root, slug) or ideas.Page()).get("track") or ""
    out = []
    for i in rows_ if rows_ is not None else ideas.ideas(root):
        if i["track"] != mine and slug in _list((ideas.idea_page(root, i["slug"]) or ideas.Page()).get("depends_on")):
            out.append(i["slug"])
    return out


def _told_path(state_dir: Path, slug: str) -> Path:
    return ideas.state_folder(state_dir, slug) / "collide_told.txt"


def told_of(state_dir: Path, slug: str) -> str:
    """What the Orkmaster told this goal's leader when the person said *Re-plan it* (another party changed a spec this goal rests on);
    "" when nothing. The leader's next plan reads it (core/idea_keeper.py `plan_prompt`, core/idea_revise.py `revise_prompt`)."""
    try:
        return _told_path(state_dir, slug).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def set_told(state_dir: Path, slug: str, text: str) -> None:
    ideas._write(_told_path(state_dir, slug), " ".join(str(text).split())[:600] + "\n")


def clear_told(state_dir: Path, slug: str) -> None:
    """The plan was made again (or its change saved): what it was told is used."""
    _told_path(state_dir, slug).unlink(missing_ok=True)


def add_dependency(root: Path, slug: str, on: str, title: str) -> bool:
    """`on` joins `slug`'s `depends_on` (and a line of its Depends on); False when it was there. The plan-making sections are not marked
    changed: a wait changes no plan."""
    with ideas.LOCK:
        page = ideas.idea_page(root, slug)
        if page is None:
            raise ValueError(f"No goal {slug!r}")
        have = _list(page.get("depends_on"))
        if on in have:
            return False
        ideas.set_meta(root, slug, depends_on=json.dumps([*have, on], ensure_ascii=False))
        line = f"- {on} — {title}"
        text = page.section("Depends on").strip()
        ideas.set_section(root, slug, "Depends on", f"{text}\n{line}".strip() if text and text.lower() not in ("(none)", "none") else line)
    return True


# -- what it cost (§5) ---------------------------------------------------------------------------------------------

def work(repo_root: Path, now: dt.datetime | None = None, days: int = 7) -> dict:
    """The Orkmaster's stops over the last `days`, from the event log: `{"asked", "answered", "taken", "usd"}` (`taken`: answered with
    anything but Leave it; `usd` the judge's cost, None when none was priced)."""
    now = now or dt.datetime.now().astimezone()
    try:
        st = event_log.path(repo_root).stat()
        key = (str(repo_root), st.st_mtime_ns, st.st_size, days, now.strftime("%Y-%m-%dT%H"))
    except OSError:
        return {"asked": 0, "answered": 0, "taken": 0, "usd": None}              # no log yet: nothing was asked
    if key in _WORK:
        return dict(_WORK[key])
    got = _work(repo_root, now, days)
    _WORK.clear()
    _WORK[key] = got
    return dict(got)


_WORK: dict[tuple, dict] = {}              # the last count, by the log's size and time: the Map asks often


def _work(repo_root: Path, now: dt.datetime, days: int) -> dict:
    rows_ = event_log.read(repo_root, since=(now - dt.timedelta(days=days)).isoformat(timespec="seconds"))
    found = [r for r in rows_ if r["event"] == event_log.COLLIDE_FOUND]
    given = [r for r in rows_ if r["event"] == event_log.COLLIDE_ANSWERED]
    priced = [float(r["cost"]) for r in found if isinstance(r.get("cost"), (int, float)) and not isinstance(r.get("cost"), bool)]
    return {"asked": sum(1 for r in found if r.get("collide")), "answered": len(given),
            "taken": sum(1 for r in given if r.get("answer") != "leave"), "usd": round(sum(priced), 4) if priced else None}
