"""Design's map: the app's screens along their flow, and Product's pains pinned on them (docs/specs/102-the-other-maps-and-picking-on-them.md §1,
decisions §112.7, §134.2). Read from dev's tree by code with no model (realm/screen_routes.py reads the routes; never the working tree), as text in the
leaders' calls (§156.1–§156.2, the model of realm/map_text.py's System) and as cards on the party's tab.

    screen_map.read(state_dir, root)
        # {"head": "<dev sha>", "source": "react-router", "entry": "home",
        #  "screens": [{"id": "orders", "name": "Orders", "path": "/orders", "file": "src/pages/Orders.tsx", "picture": {…}}],   # `picture` only when one is kept
        #  "links": [{"from": "home", "to": "orders"}],
        #  "steps": [["home"], ["orders", "settings"], ["order"]], "loose": [], "more": 0}
    screen_map.text(state_dir, root, since="")     # about 3,000 characters: the steps, the flow, the pains under their screens; None with no screen
    screen_map.step_id(1)                          # "step:1": a pain may be pinned to a screen's id or a step's
    screen_map.screen_of(state_dir, root, path)    # the screen a page's path reaches: {"id", "name", "step"} (`step` its number, from 1), None when it reaches none
    screen_map.file_of(root, screen_id)            # the file of a screen's component ("" for an id the newest screens do not have)

A screen's id is its path as a word (`/` home, `/orders/:id` orders-id). The links are read from the screens' files by name (`navigate("/x")`,
`router.push("/x")`, `<Link to="/x">`, `href="/x"`, `Navigator.pushNamed(context, "/x")`, `context.go("/x")`, `goto("/x")`), in the order they stand; a
route with a parameter takes `/orders/12` and `/orders/${id}`. The steps run breadth first from the entry (`/`, else the first screen nothing links to,
else the first), a screen once; the screens no link leads to are the last step, and `loose`. A screen's `picture` is the newest kept for it: a task's
picture (realm/idea_shots.py) of a task that changed the screen's file, or a screen kept with a lens (realm/idea_lens.py) that goes by its name or path.
A pain's place is `idea_lens.keep_segment(…, on=)`. The text is the same bytes for the same dev head and pains (no time, no pictures). Bounded: MAX_SCREENS
screens, MAX_LINKS links. No face.
"""
from __future__ import annotations

import copy
import datetime as dt
import re
import subprocess
import threading
from pathlib import Path

from orkboard.realm import commit_goal, idea_lens, ideas, screen_routes

REF = "dev"
LIMIT = 3000                       # the map's text, at most
STEPS_ROOM, FLOW_ROOM, CHANGED = 1500, 500, 500
MAX_SCREENS = 60
MAX_LINKS = 400
LINE = 360                         # a step's line, at most
STEP = "step:"
_LOCK = threading.Lock()
_CACHE: dict[tuple[str, str], dict] = {}
_CACHE_MAX = 8

_STR = r"""["'`]([^"'`\s]{1,200})["'`]"""
_LINKS = [
    re.compile(r"\b(?:navigate|push|replace|goto|go|redirect|pushNamed|pushReplacementNamed|popAndPushNamed|pushNamedAndRemoveUntil)\s*\(\s*(?:context\s*,\s*)?" + _STR),
    re.compile(r"\b(?:to|href)\s*=\s*(?:\{\s*)?" + _STR),
    re.compile(r":to\s*=\s*\"\s*'([^'\s]{1,200})'\s*\""),
    re.compile(r"\b(?:push|replace)\s*\(\s*\{\s*(?:path|name)\s*:\s*" + _STR),
]


# -- the text, bounded (realm/map_text.py's, kept here so the two modules need not import one another) ----------------------------------------------

def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:max(0, n - 1)].rstrip() + "…"


def _fit(lines: list[str], room: int, more: str) -> list[str]:
    """`lines` as many as fit in `room` characters (joined by newlines); the ones left out are one last line, `more` with their number."""
    if sum(len(ln) + 1 for ln in lines) <= room + 1:
        return list(lines)
    reserve = len(more.format(n=len(lines))) + 1
    out, used = [], 0
    for line in lines:
        if used + len(line) + 1 + reserve > room + 1:
            break
        out.append(line)
        used += len(line) + 1
    return out + [more.format(n=len(lines) - len(out))]


# -- ids, links, steps ----------------------------------------------------------------------------------------------------------------------------------

def step_id(n: int) -> str:
    return f"{STEP}{int(n)}"


def _slug(path: str) -> str:
    if path == "/":
        return "home"
    out = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", path.replace("*", "all").replace(":", "").lower())).strip("-")
    return out or "screen"


def _ids(rows: list[dict]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for r in rows:
        base = _slug(r["path"])
        seen[base] = seen.get(base, 0) + 1
        out.append(base if seen[base] == 1 else f"{base}-{seen[base]}")
    return out


def _segments(path: str) -> list[str]:
    path = re.sub(r"\$\{[^}]*\}", ":x", path.split("?")[0].split("#")[0])
    return [b for b in path.strip("/").split("/") if b]


def _matches(pattern: list[str], got: list[str]) -> int:
    """How well a target's segments fit a route's: -1 for no fit, else the number of static segments that agree (a parameter fits any one segment)."""
    score = 0
    for i, want in enumerate(pattern):
        if want == "*":
            return score
        if i >= len(got):
            return -1
        if want.startswith(":") or got[i].startswith(":"):
            continue
        if want != got[i]:
            return -1
        score += 1
    return score if len(got) == len(pattern) else -1


def _target(path: str, patterns: list[tuple[str, list[str]]]) -> str:
    """The id of the screen a link's path reaches ("" when it reaches none): an exact path first, else the fit with the most static segments."""
    if not path.startswith("/"):
        return ""
    got = _segments(path)
    best, score = "", -1
    for sid, pat in patterns:
        s = _matches(pat, got)
        if s > score:
            best, score = sid, s
    return best


def _links(tree: screen_routes.Tree, rows: list[dict], ids: list[str]) -> list[dict]:
    """The links `{from, to}` the screens' files hold, each once, in the order screens and links stand. A file that several screens share (the table
    itself) says nothing of any one of them."""
    patterns = [(sid, _segments(r["path"])) for sid, r in zip(ids, rows)]
    count: dict[str, int] = {}
    for r in rows:
        count[r["file"]] = count.get(r["file"], 0) + 1
    files = [r["file"] for r in rows if count[r["file"]] == 1]
    tree.load(files)
    out, seen = [], set()
    for sid, r in zip(ids, rows):
        if count[r["file"]] != 1:
            continue
        text = tree.text(r["file"])
        found = sorted(((m.start(), m.group(1)) for rx in _LINKS for m in rx.finditer(text)))
        for _at, path in found:
            to = _target(path, patterns)
            if to and to != sid and (sid, to) not in seen:
                seen.add((sid, to))
                out.append({"from": sid, "to": to})
                if len(out) >= MAX_LINKS:
                    return out
    return out


def _entry(ids: list[str], rows: list[dict], links: list[dict]) -> str:
    if not ids:
        return ""
    home = next((sid for sid, r in zip(ids, rows) if r["path"] == "/"), "")
    if home:
        return home
    linked = {k["to"] for k in links}
    return next((sid for sid in ids if sid not in linked), ids[0])


def _steps(ids: list[str], links: list[dict], entry: str) -> tuple[list[list[str]], list[str]]:
    """(the steps, the screens no link leads to): breadth first from the entry, a screen once; the screens left over are the last step."""
    if not entry:
        return [], []
    nxt: dict[str, list[str]] = {}
    for k in links:
        nxt.setdefault(k["from"], []).append(k["to"])
    seen, steps, row = {entry}, [], [entry]
    while row:
        steps.append(row)
        later = []
        for sid in row:
            for to in nxt.get(sid, []):
                if to not in seen:
                    seen.add(to)
                    later.append(to)
        row = later
    loose = [sid for sid in ids if sid not in seen]
    return (steps + [loose] if loose else steps), loose


# -- the read ---------------------------------------------------------------------------------------------------------------------------------------------

def _core(root: Path, sha: str) -> dict:
    """Dev's screens, links and steps at `sha` (kept for the last few commits asked)."""
    key = (str(root), sha)
    with _LOCK:
        if key in _CACHE:
            return _CACHE[key]
        tree = screen_routes.Tree(root, sha)
        source, rows = screen_routes.routes(tree)
        more = max(0, len(rows) - MAX_SCREENS)
        rows = rows[:MAX_SCREENS]
        ids = _ids(rows)
        links = _links(tree, rows, ids)
        entry = _entry(ids, rows, links)
        steps, loose = _steps(ids, links, entry)
        _CACHE[key] = {"head": sha, "source": source, "entry": entry, "more": more, "loose": loose, "links": links, "steps": steps,
                       "screens": [{"id": sid, "name": r["name"], "path": r["path"], "file": r["file"]} for sid, r in zip(ids, rows)]}
        while len(_CACHE) > _CACHE_MAX:
            _CACHE.pop(next(iter(_CACHE)))
        return _CACHE[key]


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def _changed_files(root: Path, sha: str, cache: dict[str, set[str]]) -> set[str]:
    if sha not in cache:
        try:
            got = commit_goal.git(root, "show", "-m", "--first-parent", "--name-only", "--format=", sha)
            cache[sha] = set(got.stdout.split("\n")) - {""} if got.returncode == 0 else set()
        except (OSError, subprocess.SubprocessError):
            cache[sha] = set()
    return cache[sha]


def _shots(state_dir: Path, root: Path, files: set[str]) -> dict[str, dict]:
    """The newest picture of a task that changed each of `files`: `{file: picture}` (a task that landed, its commit's files)."""
    folder = Path(state_dir) / "ideas"
    out: dict[str, dict] = {}
    if not folder.is_dir():
        return out
    cache: dict[str, set[str]] = {}
    for d in sorted(folder.iterdir()):
        if not d.is_dir() or not re.fullmatch(r"[a-z0-9-]+", d.name):
            continue
        for t in (ideas.plan(state_dir, d.name) or {}).get("tasks") or []:
            shot = t.get("shot") if isinstance(t, dict) else None
            sha = str(t.get("commit") or "") if isinstance(t, dict) else ""
            if not isinstance(shot, dict) or shot.get("none") or not isinstance(shot.get("id"), str) or not isinstance(shot.get("file"), str) \
                    or not commit_goal.FULL_SHA.fullmatch(sha):
                continue
            pic = {"kind": "shot", "goal": d.name, "task": str(t.get("id") or ""), "id": shot["id"], "file": shot["file"], "w": shot.get("w"),
                   "h": shot.get("h"), "at": str(shot.get("at") or "")}
            for f in files & _changed_files(root, sha, cache):
                if f not in out or pic["at"] > out[f]["at"]:
                    out[f] = pic
    return out


def _lens_pictures(state_dir: Path, screens: list[dict]) -> dict[str, dict]:
    """The screen kept with a lens that goes by a screen's name, path or id (the latest kept first): `{screen id: picture}`."""
    kept = idea_lens.screens(state_dir)
    out: dict[str, dict] = {}
    for s in screens:
        wants = {_norm(s["name"]), _norm(s["path"]), _norm(s["id"])} - {""}
        for k in kept:
            if _norm(k["name"]) in wants:
                try:
                    at = _iso((Path(state_dir).parent / k["path"]).stat().st_mtime)
                except OSError:
                    at = ""
                out[s["id"]] = {"kind": "lens", "id": k["id"], "name": k["name"], "at": at}
                break
    return out


def pictures(state_dir: Path, root: Path, screens: list[dict]) -> dict[str, dict]:
    """Each screen's newest kept picture, by its id: `{"kind": "shot", goal, task, id, file, w, h, at}` (the host signs its url, realm/idea_shots.py) or
    `{"kind": "lens", id, name, at}` (a kept screen: `idea_lens.screen_data`)."""
    shots = _shots(state_dir, Path(root), {s["file"] for s in screens})
    lens = _lens_pictures(state_dir, screens)
    out = {}
    for s in screens:
        mine = [p for p in (shots.get(s["file"]), lens.get(s["id"])) if p]
        if mine:
            out[s["id"]] = max(mine, key=lambda p: p["at"])
    return out


def head_of(root: Path) -> str:
    return commit_goal.head(Path(root), REF)


def _route(path: object) -> str:
    """A running page's path as a route: its query out, and a route that lives in the hash (`/#/orders`, a page on a static host) taken when the path itself is the top."""
    if not isinstance(path, str):
        return ""
    base, _, frag = path.strip()[:600].partition("#")
    base = base.split("?")[0]
    if frag.startswith("/") and base in ("", "/"):
        return frag
    return base if base.startswith("/") else ("/" + base if base else "")


def screen_of(state_dir: Path, root: Path, path: str) -> dict | None:
    """The screen of dev's newest screens that a page's path reaches, `{id, name, step}` (`_target`'s own rule: an exact path, else the fit with the most static segments),
    `step` the number of the step it lies in (from 1, as `step_id` takes it); None for a path no screen fits and for a project with no `dev` or no screen. Reads the screens
    through `_core`, so a head read before costs no new read of the repository. `state_dir` is there for the other reads' uniform call."""
    route = _route(path)
    root = Path(root)
    sha = head_of(root) if route else ""
    core = _core(root, sha) if sha else None
    if not core or not core["screens"]:
        return None
    sid = _target(route, [(s["id"], _segments(s["path"])) for s in core["screens"]])
    if not sid:
        return None
    step = next((n for n, row in enumerate(core["steps"], 1) if sid in row), None)
    return {"id": sid, "name": next(s["name"] for s in core["screens"] if s["id"] == sid), "step": step}


def file_of(root: Path, screen_id: str) -> str:
    """The file of a screen's component at dev's head ("" when the newest screens have no such id)."""
    root = Path(root)
    sha = head_of(root)
    core = _core(root, sha) if sha else None
    return next((s["file"] for s in (core or {}).get("screens") or [] if s["id"] == screen_id), "")


def read(state_dir: Path, root: Path) -> dict:
    """Design's map at dev's head (see the module's doc); the same shape, empty, for a project with no `dev` or no screen to read."""
    root = Path(root)
    sha = head_of(root)
    if not sha:
        return {"head": "", "source": "", "entry": "", "more": 0, "loose": [], "links": [], "steps": [], "screens": []}
    core = copy.deepcopy(_core(root, sha))                     # the cache is not the caller's to change
    pics = pictures(state_dir, root, core["screens"])
    return {**core, "screens": [{**s, **({"picture": pics[s["id"]]} if s["id"] in pics else {})} for s in core["screens"]]}


# -- the text -----------------------------------------------------------------------------------------------------------------------------------------------

def _label(s: dict) -> str:
    return f"{s['name']} ({s['path']})"


def _step_lines(core: dict) -> list[str]:
    by = {s["id"]: s for s in core["screens"]}
    lines = []
    for n, row in enumerate(core["steps"], 1):
        loose = bool(core["loose"]) and n == len(core["steps"])
        names = [_label(by[sid]) for sid in row]
        line = f"Step {n}{' (no link leads here)' if loose else ''}: " + ", ".join(names)
        if len(line) > LINE:
            shown = []
            for nm in names:
                if len(f"Step {n}: " + ", ".join(shown + [nm])) + 22 > LINE:
                    break
                shown.append(nm)
            line = f"Step {n}{' (no link leads here)' if loose else ''}: " + ", ".join(shown) + f" and {len(names) - len(shown)} more"
        lines.append(line)
    return lines


def _flow_lines(core: dict) -> list[str]:
    by = {s["id"]: s["name"] for s in core["screens"]}
    return [f"- {by[k['from']]} to {by[k['to']]}" for k in core["links"]]


def _pain_lines(core: dict, segs: list[dict], room: int) -> list[str]:
    """The pains under the screens (and steps) they are pinned to, by segment; those with no place, or whose screen is gone, after."""
    by = {s["id"]: s for s in core["screens"]}
    steps = {step_id(n) for n in range(1, len(core["steps"]) + 1)}
    at: dict[str, list[tuple[str, str]]] = {}
    free: list[tuple[str, str]] = []
    for seg in sorted(segs, key=lambda x: x["segment"].lower()):          # by segment, so a pain kept later does not move the others
        for p in seg["pains"]:
            (at.setdefault(p["on"], []) if p["on"] in by or p["on"] in steps else free).append((seg["segment"], p["text"]))
    if not at and not free:
        return []
    order: list[tuple[str, str]] = []
    for n, row in enumerate(core["steps"], 1):
        order.append((step_id(n), f"Step {n}"))
        order += [(sid, _label(by[sid])) for sid in row]
    lines = ["Pains (segment: pain), under the screen or step each is pinned to:"]
    for key, label in order:
        if key in at:
            lines.append(label)
            lines += [f"- {seg}: {pain}" for seg, pain in at[key]]
    if free:
        lines.append("Not pinned to a screen:")
        lines += [f"- {seg}: {pain}" for seg, pain in free]
    return _fit([_cut(ln, 240) for ln in lines], room, "- and {n} more pains")


def _since(root: Path, since: str, core: dict) -> str:
    head = "Changed since your last call"
    before = commit_goal.resolve(root, since, REF)
    if not before:
        return f"{head}: not known (that commit is not on dev)."
    if before == core["head"]:
        return f"{head}: nothing."
    old = _core(root, before)
    was, now = {s["path"] for s in old["screens"]}, {s["path"]: s for s in core["screens"]}
    new = [p for p in now if p not in was]
    gone = [p for p in old["screens"] if p["path"] not in now]
    rows = [f"- new screen {_label(now[p])}" for p in new] + [f"- gone screen {_label(s)}" for s in gone]
    if not rows:
        return f"{head}: no screen came or went."
    return "\n".join([f"{head}:"] + _fit(rows, CHANGED - len(head) - 2, "- and {n} more"))


def text(state_dir: Path, root: Path, since: str = "") -> str | None:
    """Design's map as text at dev's head (about LIMIT characters at most): the steps, a line each, the flow, then the pains under their screens, by segment;
    when `since` (the commit of the party's last call) is set, the screens that came or went after it. None for a project with no `dev` or no screen to read.
    The same bytes for the same dev head and pains."""
    root = Path(root)
    sha = head_of(root)
    core = _core(root, sha) if sha else None
    if not core or not core["screens"]:
        return None
    entry = next(s for s in core["screens"] if s["id"] == core["entry"])
    head = f"The map of the screens at dev {sha[:7]}, read from {screen_routes.SOURCES.get(core['source'], core['source'])}; the entry is {_label(entry)}"
    lines = [head, "", "Steps (breadth first from the entry, a screen once):"] + _fit(_step_lines(core), STEPS_ROOM, "- and {n} more steps")
    if core["more"]:
        lines.append(f"({core['more']} more screens are not named)")
    flow = _flow_lines(core)
    if flow:
        lines += ["", "Links (one screen to another, as its file says):"] + _fit(flow, FLOW_ROOM, "- and {n} more links")
    used = len("\n".join(lines))
    pains = _pain_lines(core, idea_lens.segments_placed(state_dir), max(0, LIMIT - used - 2))
    if pains:
        lines += [""] + pains
    out = "\n".join(lines)[:LIMIT]
    since = str(since or "").strip()
    return out + "\n\n" + _since(root, since, core) if since else out
