"""What a party's map says is wrong, by code (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §2.2; decisions §183.4): the hints a leader is given before it looks at its map, each
grounded in what the map holds. A hint is not a verdict (the leader judges it, `core/idea_concerns.py`). Read from the files, the Board and git; no model, no face; nothing is written.

    map_signals.signals(state_dir, root, craft, pages=None, ref="dev")     # [{on, kind, words}], at most MAX_SIGNALS; [] for a craft that has none by code or a map that cannot be read
    map_signals.pictures(state_dir, root, since="", limit=4)               # Design's screens' pictures kept after `since`, to be read: [{id, name, path, at}]

`on` is the id of a part of the map as it is drawn (`realm/map_parts.py`), "" where a hint belongs to no part; `kind` names the rule; `words` is a line for a model, in plain English. A hint that
is about a part of another map (a pain piled on a screen) also has `map` (that map's id). By craft (the craft of the party, as `map_text.of` takes it):
- `tech` (System, from the newest snapshot of the ref): `cycle` (parts that use one another in a loop), `fan_in` (a part used by FAN_IN parts or more), `fan_out` (one using FAN_OUT or more),
  `big` (a part holding a source file of BIG_LINES lines or more, counted at the ref's head), `hotspot` (a part changed HOT_TIMES times or more in the last CHURN_DAYS days whose longest source file is
  HOT_LINES lines or more), `unstable` (a part used by UNSTABLE_IN parts or more whose instability, what it uses over what it uses and what uses it, is UNSTABLE_I or more), `shared_churn` (a part two
  containers or more share, changed in the last CHURN_DAYS days in commits that also touched files of SHARED_FROM containers or more other than the part's own files), `untested_churn` (a part changed
  CHURN_TIMES times in the last CHURN_DAYS days with no test mapped to it: none by the gate's map (`gate_config.gate_files`), none named after one of its files, none inside it).
- `game-design` (the loop): each of `loop.findings_kinds` by its kind, on the loop's step or the currency it names (`no_source`, `pile_up`, `no_reward`, `unfed`, `flat`), then `spike` (two
  neighbouring steps of a loop whose intensities differ by SPIKE or more, on the later), `no_hook` (a loop is kept and no hook is D1, on the core loop's first step), `unground` (a step resting on no
  file where another step of its loop does, on that step). These three are hints only: the map's *what the loop says* stays as it is.
- `design` (the screens): `loose` (a screen nothing leads to), `dead_end` (one that leads nowhere and is not where the flow ends), `no_picture` (one with no picture kept), `no_states` (a screen whose
  own file, read at the ref's head, names no loading, error, empty, retry or fallback state), `a11y` (one whose file has an image with no alt text, a press on a div or span with no role, or an input
  with no label). A screen whose file is not read (shared by several screens, over SCREEN_BYTES, missing) has neither of the last two.
- `product` (the tree): `unserved` (a job no goal serves), `pains` (a screen or a step with PAINS_PILED pains or more pinned: on that screen, `map` "screens"), `pain_loose` (pains pinned to no
  screen or step: `on` ""), `vague_outcome` (an outcome whose text holds no number: `on` ""), `no_evidence` (a job served by EVIDENCE_GOALS goals or more, none tested by an experiment), `off_tree` (with
  `pages`: OFF_TREE goals or more of the Board's line serve no job: `on` ""), `untested` (with `pages`: a goal in line or at work that rests on a hypothesis still open with no test, the first such
  one a goal; `on` the goal's id where the tree names it, else "": `realm/hypotheses.py`).
- `art`, `release`, `marketing`: `realm/map_signals_crafts.py` (its module says which).
"""
from __future__ import annotations

import dataclasses
import re
import subprocess
from pathlib import Path, PurePosixPath

from orkboard.realm import code_map, commit_goal, gate_config, goal_line, hypotheses, idea_lens, ideas, loop, map_signals_crafts, opportunity_tree, project_map, screen_map, system_overview

MAX_SIGNALS = 20
FAN_IN, FAN_OUT = 8, 12             # a part used by this many parts, one using this many
BIG_LINES = 800                     # a source file this long
CHURN_DAYS, CHURN_TIMES = 30, 6     # a part changed this many times in this many days
SHARED_FROM = 2                     # a shared part changed from this many containers
HOT_TIMES, HOT_LINES = 4, 400       # a part changed this many times in CHURN_DAYS whose longest source file is this long
UNSTABLE_IN, UNSTABLE_I = 4, 0.6    # a part used by this many parts whose instability (uses / (uses + used_by)) is this or more
PAINS_PILED = 3                     # pains pinned to one screen or step
SCREEN_BYTES = 200_000              # a screen's file is read up to this size
SPIKE = 3                           # two neighbouring steps whose intensities differ by this much
EVIDENCE_GOALS = 2                  # a job served by this many goals needs an experiment
OFF_TREE = 3                        # goals in line that serve no job
TESTS = ("tests", "test", "__tests__", "spec")
ORDER = ("cycle", "fan_in", "fan_out", "big", "hotspot", "unstable", "shared_churn", "untested_churn")
_SOURCE = tuple(f"*{e}" for e in sorted(code_map.PY | code_map.JS))
_TEST_NAME = re.compile(r"(?:^test_.+|.+_test|.+\.test|.+\.spec)$")


def _git(root: Path, *args: str) -> str:
    try:
        got = commit_goal.git(Path(root), *args)
    except (OSError, subprocess.SubprocessError):
        return ""
    return got.stdout if got.returncode == 0 else ""


def _part(path: str) -> str:
    """The part a file lies in: its folder (`code_map`'s rule), "." at the project's top."""
    return PurePosixPath(path).parent.as_posix()


def _in_skipped(path: str) -> bool:
    return any(bit in code_map.SKIP for bit in path.split("/")[:-1])


# -- Tech: System ---------------------------------------------------------------------------------------------------------------------

def cycles(uses: dict[str, list[str]]) -> list[list[str]]:
    """The groups of two parts or more that use one another round and round (strongly connected components), each sorted, in order of their first part."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on: set[str] = set()
    out: list[list[str]] = []
    count = 0
    for start in sorted(uses):
        if start in index:
            continue
        work = [(start, iter(sorted(t for t in uses.get(start, []) if t in uses)))]
        index[start] = low[start] = count
        count += 1
        stack.append(start)
        on.add(start)
        while work:
            node, it = work[-1]
            for nxt in it:
                if nxt not in index:
                    index[nxt] = low[nxt] = count
                    count += 1
                    stack.append(nxt)
                    on.add(nxt)
                    work.append((nxt, iter(sorted(t for t in uses.get(nxt, []) if t in uses))))
                    break
                if nxt in on:
                    low[node] = min(low[node], index[nxt])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[node])
                if low[node] == index[node]:
                    group = []
                    while True:
                        top = stack.pop()
                        on.discard(top)
                        group.append(top)
                        if top == node:
                            break
                    if len(group) >= 2:
                        out.append(sorted(group))
    return sorted(out)


def _lines(root: Path, sha: str) -> dict[str, tuple[str, int]]:
    """`{part: (its longest source file, its lines)}` at `sha` (git grep counts the lines; a binary file is skipped)."""
    best: dict[str, tuple[str, int]] = {}
    for row in _git(root, "grep", "-I", "-c", "", sha, "--", *_SOURCE).splitlines():
        head, _sep, n = row.rpartition(":")
        path = head[len(sha) + 1:] if head.startswith(sha + ":") else head
        if not n.isdigit() or _in_skipped(path):
            continue
        part = _part(path)
        if int(n) > best.get(part, ("", 0))[1]:
            best[part] = (PurePosixPath(path).name, int(n))
    return best


def _churn(root: Path, sha: str) -> list[list[str]]:
    """The files each commit of the last CHURN_DAYS days changed (merges apart), newest first."""
    out = _git(root, "log", sha, f"--since={CHURN_DAYS}.days.ago", "--no-merges", "--name-only", "--format=%x1e")
    return [[f for f in chunk.splitlines() if f.strip()] for chunk in out.split("\x1e")[1:]]


def _tracked(root: Path, sha: str) -> list[str]:
    return [p for p in _git(root, "ls-tree", "-r", "--name-only", sha).splitlines() if p]


def _tested(part: str, files: list[str], tracked: set[str], gate: gate_config.Gate, root: Path) -> bool:
    """A test is mapped to the part: the gate's map finds one for a file of it, a file of it is a test or lies in a tests folder, or a test is named after one of its files."""
    if any(bit in TESTS for bit in part.split("/")):
        return True
    names = [PurePosixPath(f).name for f in files]
    if any(_TEST_NAME.match(PurePosixPath(n).stem) for n in names):
        return True
    touched = [f"{part}/{n}" if part != "." else n for n in names]
    if gate_config.gate_files(dataclasses.replace(gate, always=()), touched, Path(root)):
        return True
    stems = {PurePosixPath(n).stem for n in names if PurePosixPath(n).stem != "__init__"}
    return any(_TEST_NAME.match(PurePosixPath(t).stem) and re.sub(r"^test_|_test$|\.test$|\.spec$", "", PurePosixPath(t).stem) in stems for t in tracked)


def _tech(state_dir: Path, root: Path, ref: str) -> list[dict]:
    snap = project_map.ensure(state_dir, root, ref)
    if not snap:
        return []
    sha = snap["commit"]
    by = {p["path"]: p for p in snap["parts"] if isinstance(p, dict) and p.get("path")}
    out: dict[str, list[dict]] = {k: [] for k in ORDER}
    for group in cycles({p: list(v.get("uses") or []) for p, v in by.items()}):
        shown = ", ".join(group[:4]) + (f" and {len(group) - 4} more" if len(group) > 4 else "")
        out["cycle"].append({"on": group[0], "kind": "cycle", "words": f"{shown} use one another in a cycle"})
    for p, v in sorted(by.items()):
        if len(v.get("used_by") or []) >= FAN_IN:
            out["fan_in"].append({"on": p, "kind": "fan_in", "words": f"{p} is used by {len(v['used_by'])} parts"})
        if len(v.get("uses") or []) >= FAN_OUT:
            out["fan_out"].append({"on": p, "kind": "fan_out", "words": f"{p} uses {len(v['uses'])} parts"})
    longest = _lines(root, sha)
    for part, (name, n) in sorted(longest.items()):
        if n >= BIG_LINES and part in by:
            out["big"].append({"on": part, "kind": "big", "words": f"{part} holds {name} of {n} lines"})
    commits = _churn(root, sha)
    containers = [c["path"] for c in (snap.get("overview") or {}).get("containers") or []]
    touched: dict[str, int] = {}
    outside: dict[str, set[str]] = {}
    shared = {s["path"]: s for s in (snap.get("overview") or {}).get("shared") or [] if isinstance(s, dict)}
    for files in commits:
        parts = {_part(f) for f in files} & set(by)
        for part in parts:
            touched[part] = touched.get(part, 0) + 1
            if part in shared:
                outside.setdefault(part, set()).update(c for f in files if _part(f) != part and (c := system_overview.owner(f, containers)))
    for part, others in sorted(outside.items()):
        if len(others) >= SHARED_FROM:
            out["shared_churn"].append({"on": part, "kind": "shared_churn", "words": f"{part} is shared by {len(shared[part].get('containers') or [])} containers and was changed in the last "
                                        f"{CHURN_DAYS} days along with files of {len(others)} containers ({', '.join(sorted(others)[:4])})"})
    for part, n in sorted(touched.items(), key=lambda kv: (-kv[1], kv[0])):
        name, lines = longest.get(part, ("", 0))
        if n >= HOT_TIMES and lines >= HOT_LINES:
            out["hotspot"].append({"on": part, "kind": "hotspot", "words": f"{part} changed {n} times in the last {CHURN_DAYS} days and holds {name} of {lines} lines"})
    for p, v in sorted(by.items()):
        used, uses = len(v.get("used_by") or []), len(v.get("uses") or [])
        if used >= UNSTABLE_IN and uses / (uses + used) >= UNSTABLE_I:
            out["unstable"].append({"on": p, "kind": "unstable", "words": f"{p} is used by {used} parts and itself uses {uses}: what many stand on keeps changing with what it uses"})
    hot = {p: n for p, n in touched.items() if n >= CHURN_TIMES}
    if hot:
        tracked, gate = _tracked(root, sha), gate_config.read(root)
        names = set(tracked)
        for part, n in sorted(hot.items(), key=lambda kv: (-kv[1], kv[0])):
            if not _tested(part, list(by[part].get("files") or []), names, gate, root):
                out["untested_churn"].append({"on": part, "kind": "untested_churn", "words": f"{part} changed {n} times in the last {CHURN_DAYS} days and no test is mapped to it"})
    return [s for k in ORDER for s in out[k]]


# -- Game design: the loop ------------------------------------------------------------------------------------------------------------

def _game(state_dir: Path) -> list[dict]:
    data = loop.read(state_dir)
    out = [{"on": on, "kind": kind, "words": words} for on, kind, words in loop.findings_kinds(data)]
    loops = [lp for lp in data.get("loops") or [] if lp.get("steps")]
    for lp in loops:
        for prev, step in zip(lp["steps"], lp["steps"][1:]):
            if abs(step["intensity"] - prev["intensity"]) >= SPIKE:
                out.append({"on": step["id"], "kind": "spike", "words": f"The {lp['span']} loop jumps from intensity {prev['intensity']} at {prev['name']} to {step['intensity']} at {step['name']}"})
    if loops and not any(h["when"] == "D1" for h in data.get("hooks") or []):
        core = next((lp for lp in loops if lp["span"] == "core"), loops[0])
        out.append({"on": core["steps"][0]["id"], "kind": "no_hook", "words": "No hook says why a player comes back on the first day (D1)"})
    for lp in loops:
        if any(s["rests_on"] for s in lp["steps"]):
            out += [{"on": s["id"], "kind": "unground", "words": f"The step {s['name']} of the {lp['span']} loop rests on no file, though others of it do"} for s in lp["steps"] if not s["rests_on"]]
    return out


# -- Design: the screens --------------------------------------------------------------------------------------------------------------

_STATES = ("loading", "error", "empty", "spinner", "skeleton", "retry", "fallback", "catch")
_TAG = re.compile(r"<(img|div|span|input)(?![\w-])")
_PRESS = re.compile(r"(?<!\w)(?:onClick|@click|on:click)(?![\w-])")
_ATTR = {"alt": re.compile(r"(?<![\w-])alt\s*="), "role": re.compile(r"(?<![\w-])role\s*="), "label": re.compile(r"(?<![\w-])(?:aria-label|aria-labelledby|id|placeholder)\s*="),
         "hidden": re.compile(r"""(?<![\w-])type\s*=\s*\{?["']hidden["']""")}
TAG_CHARS = 1500                    # a tag is read this far


def _attrs(text: str, at: int) -> str:
    """The attributes of the tag starting at `at`, up to its closing `>` outside braces and quotes."""
    depth, quote = 0, ""
    for i in range(at, min(len(text), at + TAG_CHARS)):
        c = text[i]
        if quote:
            quote = "" if c == quote else quote
        elif c in "\"'`":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth = max(0, depth - 1)
        elif c == ">" and depth == 0:
            return text[at:i]
    return text[at:at + TAG_CHARS]


def _a11y(text: str) -> str:
    """The first thing in a screen's file a person with a screen reader or a keyboard would stumble on (a tag with its attributes spread is not judged); "" for none."""
    for m in _TAG.finditer(text):
        tag, attrs = m.group(1), _attrs(text, m.end())
        if "{..." in attrs:
            continue
        if tag == "img" and not _ATTR["alt"].search(attrs):
            return "an image with no alt text"
        if tag in ("div", "span") and _PRESS.search(attrs) and not _ATTR["role"].search(attrs):
            return f"a press on a {tag} with no role"
        if tag == "input" and not _ATTR["label"].search(attrs) and not _ATTR["hidden"].search(attrs):
            return "an input with no label"
    return ""


def _screen_text(root: Path, sha: str, path: str) -> str | None:
    """A screen's file at `sha`, None when it is not there, is binary or is over SCREEN_BYTES."""
    text = _git(root, "--literal-pathspecs", "show", f"{sha}:{path}")
    return text if text and len(text) <= SCREEN_BYTES and "\0" not in text[:2000] else None


def _design(state_dir: Path, root: Path) -> list[dict]:
    got = screen_map.read(state_dir, root)
    screens = got.get("screens") or []
    if len(screens) < 2:
        return []
    ids = {s["id"] for s in screens}
    links = [k for k in got.get("links") or [] if k["from"] in ids and k["to"] in ids]
    led_to, leads = {k["to"] for k in links if k["from"] != k["to"]}, {k["from"] for k in links if k["from"] != k["to"]}
    steps = got.get("steps") or []
    loose = set(got.get("loose") or [])
    last = [row for row in steps if not set(row) <= loose][-1:] or [[]]
    ends = set(last[0])
    out = []
    for s in screens:
        sid, name = s["id"], s["name"]
        if sid != got.get("entry") and sid not in led_to:
            out.append({"on": sid, "kind": "loose", "words": f"Nothing leads to the screen {name} ({s['path']})"})
        elif sid not in leads and sid not in ends and sid not in loose:
            out.append({"on": sid, "kind": "dead_end", "words": f"The screen {name} ({s['path']}) leads nowhere and is not where the flow ends"})
    out += [{"on": s["id"], "kind": "no_picture", "words": f"The screen {s['name']} ({s['path']}) has no picture kept"} for s in screens if not s.get("picture")]
    own = {s["file"] for s in screens if sum(1 for o in screens if o["file"] == s["file"]) == 1}            # a file several screens share says nothing of any one
    texts = {s["id"]: _screen_text(root, got["head"], s["file"]) for s in screens if s["file"] in own and got.get("head")}
    shown = [s for s in screens if texts.get(s["id"]) is not None]
    out += [{"on": s["id"], "kind": "no_states", "words": f"The screen {s['name']} ({s['path']}) says nothing of loading, error or empty states"} for s in shown
            if not any(w in texts[s["id"]].lower() for w in _STATES)]
    out += [{"on": s["id"], "kind": "a11y", "words": f"{s['name']} ({s['path']}): {what}"} for s in shown if (what := _a11y(texts[s["id"]]))]
    return out


# -- Product: the tree and the pains ----------------------------------------------------------------------------------------------------

def _product(state_dir: Path, root: Path, pages: Path | None = None) -> list[dict]:
    rec = opportunity_tree.read(state_dir)
    served = {s["job"] for s in rec["serves"]}
    out = [{"on": j["id"], "kind": "unserved", "words": f"No goal serves the job: {j['want']}"} for j in rec["jobs"] if j["id"] not in served]
    out += [{"on": "", "kind": "vague_outcome", "words": f"The outcome holds no number, so nothing says when it is met: {o['text']}"} for o in rec["outcomes"] if not any(c.isdigit() for c in o["text"])]
    have = set(opportunity_tree.goals(state_dir, Path(pages))) if pages is not None else None         # a goal the Board dropped serves nothing
    tested = {t["goal"] for t in rec["tests"]}
    for j in rec["jobs"]:
        mine = [s["goal"] for s in rec["serves"] if s["job"] == j["id"] and (have is None or s["goal"] in have)]
        if len(mine) >= EVIDENCE_GOALS and not tested & set(mine):
            out.append({"on": j["id"], "kind": "no_evidence", "words": f"{len(mine)} goals serve the job {j['want']} and no experiment tests any of them"})
    placed = [p for seg in idea_lens.segments_placed(state_dir) for p in seg["pains"]]
    try:
        got = screen_map.read(state_dir, root)
        known = {s["id"] for s in got.get("screens") or []} | {screen_map.step_id(n) for n in range(1, len(got.get("steps") or []) + 1)}
    except Exception:                                # a map that cannot be read: the pains stand where they were pinned
        known = {p["on"] for p in placed if p["on"]}
    piled: dict[str, list[str]] = {}
    for p in placed:
        if p["on"] in known:
            piled.setdefault(p["on"], []).append(p["text"])
    out += [{"on": on, "map": "screens", "kind": "pains", "words": f"{len(texts)} pains are pinned to {on}: " + "; ".join(texts[:3])}
            for on, texts in sorted(piled.items()) if len(texts) >= PAINS_PILED]
    loose = [p["text"] for p in placed if p["on"] not in known]
    if loose:
        out.append({"on": "", "kind": "pain_loose", "words": f"{len(loose)} pains are pinned to no screen or step: " + "; ".join(loose[:3])})
    if pages is not None:
        on_tree = {s["goal"] for s in rec["serves"]}
        off = [g["title"] for g in goal_line.line(Path(pages), state_dir) if g["slug"] not in on_tree]
        if len(off) >= OFF_TREE:
            out.append({"on": "", "kind": "off_tree", "words": f"{len(off)} goals in line serve no job: " + "; ".join(off[:3])})
        out += _untested(state_dir, Path(pages), set(have or ()))
    return out


def _untested(state_dir: Path, pages: Path, named: set[str]) -> list[dict]:
    """A goal in line or at work that rests on a hypothesis still open with no test: one hint a goal, for the first such hypothesis in the order kept; `on` the goal's id where the tree's parts
    name it (`named`), else ""."""
    out, seen = [], set()
    for h in hypotheses.read(state_dir)["items"]:
        if h["state"] != "open" or h["tests"]:
            continue
        for slug in h["rests"]:
            if slug in seen:
                continue
            try:
                page = ideas.idea_page(pages, slug)
            except (OSError, ValueError):
                page = None
            if page is None or opportunity_tree.place_of(state_dir, slug) == "done":
                continue
            seen.add(slug)
            title = " ".join((page.title or slug).split())[:80]
            out.append({"on": slug if slug in named else "", "kind": "untested", "words": f"{title} rests on an untested hypothesis: {h['text']}"})
    return out


def pictures(state_dir: Path, root: Path, since: str = "", limit: int = 4) -> list[dict]:
    """The pictures of Design's screens kept since `since` (an ISO time: a look's; "" all), the newest `limit`: `[{id, name, path, at}]`, `path` a file under the repository to read (relative to it
    when it lies in it). [] for a map that cannot be read."""
    from orkboard.realm import idea_pick
    try:
        screens = screen_map.read(Path(state_dir), Path(root)).get("screens") or []
    except Exception:
        return []
    out = []
    for s in screens:
        pic = s.get("picture")
        if not isinstance(pic, dict) or (since and str(pic.get("at") or "") <= since):
            continue
        if pic.get("kind") == "lens":
            found = next((k["path"] for k in idea_lens.screens(Path(state_dir)) if k["id"] == pic.get("id")), "")
            path = Path(found) if found else None
        else:
            path = idea_pick.folder_of(Path(state_dir), str(pic.get("goal") or ""), str(pic.get("id") or "")) / str(pic.get("file") or "") if pic.get("goal") else None
        if path is not None:
            try:
                path = path.relative_to(root) if path.is_absolute() else path
            except ValueError:
                pass
            out.append({"id": s["id"], "name": s["name"], "path": path.as_posix(), "at": str(pic.get("at") or "")})
    return sorted(out, key=lambda r: (r["at"], r["id"]), reverse=True)[:limit]


def signals(state_dir: Path, root: Path, craft: str, pages: Path | None = None, ref: str = "dev") -> list[dict]:
    """The hints of `craft`'s party's map (see the module): `[{on, kind, words, map?}]`, at most MAX_SIGNALS; [] for a craft that has none by code and for a map that cannot be read."""
    state_dir, root = Path(state_dir), Path(root)
    try:
        rows = {"tech": lambda: _tech(state_dir, root, ref), "game-design": lambda: _game(state_dir), "design": lambda: _design(state_dir, root),
                "product": lambda: _product(state_dir, root, pages), "art": lambda: map_signals_crafts.art(state_dir, root, ref),
                "release": lambda: map_signals_crafts.release(state_dir, root, pages, ref), "marketing": lambda: map_signals_crafts.marketing(state_dir, root, ref)}.get(craft, lambda: [])()
    except Exception:                                # a hint that cannot be read is no hint, never an error for a caller
        return []
    return rows[:MAX_SIGNALS]
