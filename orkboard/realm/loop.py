"""Game design's loop (docs/specs/107-what-the-owners-day-said.md §14; docs/specs/102-the-other-maps-and-picking-on-them.md §2; decisions §112.8, §156.3, §182): the game's loops one in another,
its currencies and why a player comes back, which the person and Game design's leader keep, each step tied to the files it rests on. Read by code, no model (the leader's proposal is
`core/idea_loop.py`'s); no face.

    loop.read(state_dir)                           # what is kept: {version: 2, loops, currencies, hooks, by, at, was?}, each as below; empty lists before any (a version 1 file, `cards`, reads as one core loop)
    loop.kept(data)                                # True when `data` has a loop
    loop.keep(state_dir, root, data, by)           # replaced whole → (kept, dropped): `data` is {loops, currencies, hooks} (or v1's {cards}); limits below; a `rests_on` path only where dev's tree has it
    loop.parse(answer, root)                       # the leader's answer, strictly but clamped to the limits → {loops, currencies, hooks} or None
    loop.findings(data)                            # what the loop says, by code: [str] (a currency nothing takes, one nothing gives, a loop that rewards nothing, a span nothing feeds, a flat feeling)
    loop.findings_on(data)                         # the same with the part each is on (spec 108 §2.2): [(id, str)], `cur:<id>` for a currency, a loop's first step for a loop
    loop.config_files(root)                        # the project's configs by name, chosen by code from dev's tree: balance*, config/, levels/, *.config.*; bounded
    loop.heads(root, paths)                        # {path: its first lines} of the first few of them, bounded
    loop.text(state_dir, root, since="")           # the loops as text for a leader's call (~3,000 characters); None when none is kept
    loop.proposal(state_dir) / save_proposal(...)   # what the proposal did: {status: "asking"|"done"|"failed", error, at}

`<state_dir>/loop.json` is `{version: 2, loops: [{id, span, name, line, feeds, steps: [{id, name, line, feel, intensity, gives, takes, rests_on, by, at}]}], currencies: [{id, name, kind, line}],
hooks: [{when, line}], by, at, was, proposal}`. One to three loops, one of each `span` (`core`: seconds, `session`: minutes, `meta`: days and weeks), three to six steps each; `feeds` is the span a loop
feeds (an outer one, "" for none); `feel` is one of MDA's eight (or "" where none was said), `intensity` 1 to 5 (clamped; 3 where none was said); `gives` / `takes` are currency ids. Zero to four
currencies, zero to three hooks (D1, D7, D30). A step's id stays with it (a name's slug at first); a step kept again unchanged keeps its `by` and `at`, so the leader's steps the person did not
touch stay *Proposed by the leader*. `by` and `at` of the whole are who kept it last and when; when the leader proposes again over what the person kept, the person's version is put aside whole in
`was`. A `rests_on` path is a file of dev's tree or a folder of it, posix, relative, never a secret's; one that is not is dropped and said (`dropped`), never kept. With no `dev` branch no path can
be checked, so none is kept. The text is the same bytes for the same record and the same dev head; with `since` (the commit of the party's last call) it ends with what changed under the steps' files,
each with its goal.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from orkboard.hooks.warder import is_secret
from orkboard.realm import commit_goal, ideas

FILE = "loop.json"
REF = "dev"
SPANS = ("core", "session", "meta")                   # the loops from the inside out
TIME = {"core": "seconds", "session": "minutes", "meta": "days and weeks"}
FEELS = ("sensation", "fantasy", "narrative", "challenge", "fellowship", "discovery", "expression", "submission")      # MDA's eight kinds of fun
KINDS = ("soft", "hard", "energy", "progress", "social", "time")
WHENS = ("D1", "D7", "D30")
MAX_LOOPS, MIN_STEPS, MAX_STEPS, MAX_CURRENCIES, MAX_HOOKS = 3, 3, 6, 4, 3
INTENSITY_MIN, INTENSITY_MAX, INTENSITY = 1, 5, 3     # a step's intensity: the range, and where none was said
NAME_CHARS, LINE_CHARS = 40, 160
PATHS, PATH_CHARS = 6, 200            # the most files a step rests on; one path's length
LIMIT = 3000                          # the text, at most (map_text.LIMIT's)
CHANGED = 1200                        # … and what changed under the steps, at most (map_text.CHANGED's)
SHOWN = 3                             # the most files a step's line names in the text
CONFIGS, PER_FOLDER = 40, 8           # the most config files named, and of one folder
HEAD_FILES, HEAD_LINES, HEAD_CHARS, HEAD_TOTAL = 10, 6, 300, 2500
READ_BYTES = 200_000                  # a file larger than this is named, never read
_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
_WORDS = re.compile(r"[a-z0-9]+")
_MODES = ("100644", "100755")
_SKIP = {"node_modules", "vendor", "dist", "build", "target", "venv", ".venv", "__pycache__", ".git", ".next", "Pods"}
_TEXT = {".json", ".jsonc", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv", ".tsv", ".txt", ".xml", ".lua", ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".cs",
         ".gd", ".tres", ".tscn", ".tmx", ".ldtk", ".dart", ".kt", ".java", ".rs", ".go", ".swift", ".md"}
BY = ("person", "leader")


def _words(value: object, n: int) -> str:
    return " ".join(value.split())[:n] if isinstance(value, str) else ""


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:max(0, n - 1)].rstrip() + "…"


def _file(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


def _record(state_dir: Path) -> dict:
    got = ideas._json(_file(state_dir))
    return got if isinstance(got, dict) else {}


# -- dev's tree -----------------------------------------------------------------------------------------------------------------------

def tree(root: Path) -> dict[str, int]:
    """`{path: bytes}` of the files of dev's head (`git ls-tree -r -l`: blobs only, no link, no submodule); {} with no `dev`."""
    tip = commit_goal.head(Path(root), REF)
    if not tip:
        return {}
    try:
        got = commit_goal.git(Path(root), "ls-tree", "-r", "-l", "-z", tip)
    except (OSError, subprocess.SubprocessError):
        return {}
    out: dict[str, int] = {}
    for row in got.stdout.split("\0") if got.returncode == 0 else []:
        head, _, path = row.partition("\t")
        bits = head.split()
        if len(bits) == 4 and bits[0] in _MODES and bits[1] == "blob" and bits[3].isdigit() and path:
            out[path] = int(bits[3])
    return out


def _folders(files: dict[str, int]) -> set[str]:
    return {"/".join(p.split("/")[:n]) for p in files for n in range(1, len(p.split("/")))}


def _path(raw: object) -> str:
    """A path as it is kept (posix, relative, no `..`, no secret, bounded), "" for one that is none."""
    if not isinstance(raw, str):
        return ""
    path = raw.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    path = path.strip("/")
    bits = path.split("/")
    if not path or len(path) > PATH_CHARS or any(b in ("", ".", "..") for b in bits) or "\0" in path or is_secret(path):
        return ""
    return path


def _rests(raw: object, have: set[str]) -> tuple[list[str], list[str]]:
    """(the paths kept, the paths dropped) of a card's `rests_on`: each a file or a folder of dev's tree, once, at most PATHS."""
    if not isinstance(raw, list):
        raise ValueError("What a step rests on is a list of files")
    kept: list[str] = []
    dropped: list[str] = []
    for item in raw:
        path = _path(item)
        if path and path in kept:
            continue
        if path and path in have and len(kept) < PATHS:
            kept.append(path)
        elif isinstance(item, str) and item.strip():
            dropped.append(item.strip()[:PATH_CHARS])
    return kept, dropped


# -- what is kept ---------------------------------------------------------------------------------------------------------------------

def _slug(name: str, taken: set[str], base: str = "step") -> str:
    base = "-".join(_WORDS.findall(name.lower()))[:36].strip("-") or base
    out, n = base, 1
    while out in taken:
        n += 1
        out = f"{base}-{n}"
    return out


def _pick_id(given: object, name: str, taken: set[str], base: str = "step") -> str:
    """The id a thing keeps: the one it came with when that is well made and free, else a name's slug. It is taken."""
    out = given if isinstance(given, str) and _ID.fullmatch(given) and given not in taken else _slug(name, taken, base)
    taken.add(out)
    return out


def _empty() -> dict:
    return {"version": 2, "loops": [], "currencies": [], "hooks": [], "by": "", "at": ""}


def _intensity(raw: object) -> int | None:
    """A step's intensity clamped to 1–5; INTENSITY where none was said; None for what is no number."""
    if raw is None or raw == "":
        return INTENSITY
    if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
        return None
    try:
        n = float(raw)
    except ValueError:
        return None
    return None if n != n else round(max(INTENSITY_MIN, min(INTENSITY_MAX, n)))


def _refs(raw: object, by_word: dict[str, str]) -> list[str]:
    """The currency ids a step gives or takes: each word of `raw` (an id, or a name in lower case) that `by_word` knows, once; what it does not know is left out."""
    return list(dict.fromkeys(by_word[x.strip().lower()] for x in raw if isinstance(x, str) and x.strip().lower() in by_word)) if isinstance(raw, list) else []


def _read_step(r: object, currencies: set[str], taken: set[str]) -> dict | None:
    if not isinstance(r, dict):
        return None
    name, line = _words(r.get("name"), NAME_CHARS), _words(r.get("line"), LINE_CHARS)
    if not (name and line and isinstance(r.get("id"), str) and _ID.fullmatch(r["id"]) and r["id"] not in taken):
        return None
    taken.add(r["id"])
    paths = [p for p in (_path(x) for x in r["rests_on"]) if p][:PATHS] if isinstance(r.get("rests_on"), list) else []
    n = _intensity(r.get("intensity"))
    return {"id": r["id"], "name": name, "line": line, "feel": r["feel"] if r.get("feel") in FEELS else "", "intensity": INTENSITY if n is None else n,
            "gives": _refs(r.get("gives"), {c: c for c in currencies}), "takes": _refs(r.get("takes"), {c: c for c in currencies}), "rests_on": paths,
            "by": r["by"] if r.get("by") in BY else "person", "at": str(r.get("at") or "")}


def _read_v2(rec: dict) -> dict:
    out = _empty()
    cur, taken = set(), set()
    for r in rec.get("currencies") if isinstance(rec.get("currencies"), list) else []:
        name = _words(r.get("name"), NAME_CHARS) if isinstance(r, dict) else ""
        if name and isinstance(r.get("id"), str) and _ID.fullmatch(r["id"]) and r["id"] not in cur and len(out["currencies"]) < MAX_CURRENCIES:
            cur.add(r["id"])
            out["currencies"].append({"id": r["id"], "name": name, "kind": r["kind"] if r.get("kind") in KINDS else "soft", "line": _words(r.get("line"), LINE_CHARS)})
    seen = set()
    for r in rec.get("loops") if isinstance(rec.get("loops"), list) else []:
        if not isinstance(r, dict) or r.get("span") not in SPANS or r["span"] in seen or not isinstance(r.get("steps"), list):
            continue
        name = _words(r.get("name"), NAME_CHARS)
        steps = [s for s in (_read_step(x, cur, taken) for x in r["steps"]) if s][:MAX_STEPS]
        if name and steps:
            seen.add(r["span"])
            feeds = r.get("feeds") if r.get("feeds") in SPANS and SPANS.index(r["feeds"]) > SPANS.index(r["span"]) else ""
            out["loops"].append({"id": r["span"], "span": r["span"], "name": name, "line": _words(r.get("line"), LINE_CHARS), "feeds": feeds, "steps": steps})
    out["loops"].sort(key=lambda lp: SPANS.index(lp["span"]))
    seen = set()
    for r in rec.get("hooks") if isinstance(rec.get("hooks"), list) else []:
        line = _words(r.get("line"), LINE_CHARS) if isinstance(r, dict) else ""
        if line and r.get("when") in WHENS and r["when"] not in seen:
            seen.add(r["when"])
            out["hooks"].append({"when": r["when"], "line": line})
    out["hooks"].sort(key=lambda h: WHENS.index(h["when"]))
    out["by"] = rec["by"] if rec.get("by") in BY else ("person" if out["loops"] else "")
    out["at"] = str(rec.get("at") or "")
    return out


def _read_v1(rows: list) -> dict:
    """A version 1 file: its cards are one core loop, no feeling said, intensity 3, no currency, no hook."""
    out = _empty()
    taken: set[str] = set()
    steps = [s for s in (_read_step(r, set(), taken) for r in rows) if s][:MAX_STEPS]
    if steps:
        out["loops"] = [{"id": "core", "span": "core", "name": "The loop", "line": "", "feeds": "", "steps": steps}]
        out["by"] = "person" if any(s["by"] == "person" for s in steps) else "leader"
        out["at"] = max(s["at"] for s in steps)
    return out


def read(state_dir: Path) -> dict:
    """What is kept, each part checked: whatever is not of the shape reads as absent (the file is not trusted). `was` is there when the leader's proposal replaced the person's version."""
    rec = _record(state_dir)
    out = _read_v2(rec) if isinstance(rec.get("loops"), list) else _read_v1(rec["cards"]) if isinstance(rec.get("cards"), list) else _empty()
    if isinstance(rec.get("was"), dict) and (was := _read_v2(rec["was"]))["loops"]:
        out["was"] = was
    return out


def kept(data: dict) -> bool:
    return bool(data and data.get("loops"))


def _from_cards(cards: object) -> dict:
    """A version 1 answer (`cards`) as one core loop."""
    if not isinstance(cards, list):
        raise ValueError(f"A loop has {MIN_STEPS} to {MAX_STEPS} steps")
    steps = [{k: v for k, v in c.items() if k in ("id", "name", "line", "rests_on")} if isinstance(c, dict) else c for c in cards]
    return {"loops": [{"span": "core", "name": "The loop", "line": "", "feeds": "", "steps": steps}]}


def _clean(data: object, have: set[str], clamp: bool) -> tuple[dict, list[dict]]:
    """`data` as it would be kept, before its steps' `by` and `at`: {loops, currencies, hooks}, and what was dropped [{name, path}]. ValueError in plain words. With `clamp` (the model's
    answer) what is over a limit is cut and an unknown feeling or kind is left unsaid; without it (a person's) it is refused."""
    if not isinstance(data, dict):
        raise ValueError("A loop is loops, currencies and hooks")
    if "loops" not in data and "cards" in data:
        data = _from_cards(data["cards"])
    rows, many = data.get("loops"), data.get("currencies") or []
    if not isinstance(rows, list) or not rows or (len(rows) > MAX_LOOPS and not clamp):
        raise ValueError("A game has one to three loops")
    if not isinstance(many, list) or (len(many) > MAX_CURRENCIES and not clamp):
        raise ValueError(f"A game has at most {MAX_CURRENCIES} currencies")
    taken_cur, names_cur = set(), set()
    refs: dict[str, str] = {}                                  # a currency by its id or its name in lower case
    currencies = []
    for c in many[:MAX_CURRENCIES]:
        name = _words(c.get("name"), NAME_CHARS) if isinstance(c, dict) else ""
        if not name:
            raise ValueError("A currency has a name")
        if name.lower() in names_cur:
            raise ValueError(f"Two currencies are named {name}")
        names_cur.add(name.lower())
        kind = c.get("kind") or "soft"
        if kind not in KINDS:
            if not clamp:
                raise ValueError(f"A currency is {', '.join(KINDS[:-1])} or {KINDS[-1]}")
            kind = "soft"
        cid = _pick_id(c.get("id"), name, taken_cur, "currency")
        refs.update({name.lower(): cid, cid: cid})
        currencies.append({"id": cid, "name": name, "kind": kind, "line": _words(c.get("line"), LINE_CHARS)})
    loops, dropped, spans, taken = [], [], set(), set()
    for r in rows[:MAX_LOOPS]:
        if not isinstance(r, dict) or r.get("span") not in SPANS:
            raise ValueError("A loop is the core, session or meta loop")
        span = r["span"]
        if span in spans:
            raise ValueError(f"Two loops are the {span} loop")
        spans.add(span)
        name = _words(r.get("name"), NAME_CHARS)
        if not name:
            raise ValueError(f"The {span} loop has a name")
        items = r.get("steps")
        if not isinstance(items, list) or len(items) < MIN_STEPS or (len(items) > MAX_STEPS and not clamp):
            raise ValueError(f"The {span} loop has {MIN_STEPS} to {MAX_STEPS} steps")
        steps, names = [], set()
        for s in items[:MAX_STEPS]:
            sname, line = (_words(s.get("name"), NAME_CHARS), _words(s.get("line"), LINE_CHARS)) if isinstance(s, dict) else ("", "")
            if not sname or not line:
                raise ValueError("A step has a name and a line")
            if sname.lower() in names:
                raise ValueError(f"Two steps of the {span} loop are named {sname}")
            names.add(sname.lower())
            feel = s.get("feel") or ""
            if feel not in FEELS and not clamp and feel:
                raise ValueError(f"A feeling is one of {', '.join(FEELS[:-1])} or {FEELS[-1]}")
            n = _intensity(s.get("intensity"))
            if n is None and not clamp:
                raise ValueError("An intensity is a number from 1 to 5")
            rests, lost = _rests(s.get("rests_on", []), have)
            dropped += [{"name": sname, "path": p} for p in lost]
            steps.append({"id": _pick_id(s.get("id"), sname, taken), "name": sname, "line": line, "feel": feel if feel in FEELS else "", "intensity": INTENSITY if n is None else n,
                          "gives": _refs(s.get("gives"), refs), "takes": _refs(s.get("takes"), refs), "rests_on": rests})
        feeds = r.get("feeds") if r.get("feeds") in SPANS and SPANS.index(r["feeds"]) > SPANS.index(span) else ""
        loops.append({"id": span, "span": span, "name": name, "line": _words(r.get("line"), LINE_CHARS), "feeds": feeds, "steps": steps})
    loops.sort(key=lambda lp: SPANS.index(lp["span"]))
    for lp in loops:                                           # a loop feeds the next one out that the game has (the core of a game with no session loop feeds its meta loop)
        if lp["feeds"] and lp["feeds"] not in spans:
            lp["feeds"] = next((o for o in SPANS[SPANS.index(lp["feeds"]):] if o in spans), "")
    hooks, seen = [], set()
    for h in (data.get("hooks") if isinstance(data.get("hooks"), list) else [])[:MAX_HOOKS if clamp else None]:
        line = _words(h.get("line"), LINE_CHARS) if isinstance(h, dict) else ""
        if not line or h.get("when") not in WHENS or h["when"] in seen:
            if clamp:
                continue
            raise ValueError("A hook is D1, D7 or D30, once each, with a line")
        seen.add(h["when"])
        hooks.append({"when": h["when"], "line": line})
    if len(hooks) > MAX_HOOKS:
        raise ValueError(f"A game has at most {MAX_HOOKS} hooks")
    hooks.sort(key=lambda h: WHENS.index(h["when"]))
    return {"loops": loops, "currencies": currencies, "hooks": hooks}, dropped


def _bare(data: dict) -> dict:
    """What a loop says, without who kept each step and when: to tell a keeping that changes nothing."""
    return {"loops": [{**lp, "steps": [{k: v for k, v in s.items() if k not in ("by", "at")} for s in lp["steps"]]} for lp in data["loops"]], "currencies": data["currencies"], "hooks": data["hooks"]}


def keep(state_dir: Path, root: Path, data: object, by: str) -> tuple[dict, list[dict]]:
    """The loops replaced whole by `data` (`{loops, currencies, hooks}`; a version 1 `{cards}` is one core loop) → (what is kept, what was dropped `[{name, path}]`). `by` is who kept them: "person" or
    "leader"; a step the same as the one kept under its `id` keeps its own `by` and `at`; nothing changed keeps all. The leader's keeping over a person's version puts it aside in `was`. ValueError, in
    plain words, for a `by` that is none, a count outside the limits, a loop, step, currency or hook not of the shape, two of one name or span; a path that is not a file or folder of dev's tree is
    dropped, not refused."""
    if by not in BY:
        raise ValueError(f"A loop is kept by the person or the leader, not {by!r}")
    files = tree(Path(root))
    clean, dropped = _clean(data, set(files) | _folders(files), False)
    return _store(state_dir, clean, by), dropped


def _store(state_dir: Path, clean: dict, by: str) -> dict:
    """`clean` (from `_clean`) written as `by` kept it, the steps' `by` and `at` as `keep` says → what is kept."""
    with ideas.LOCK:
        before = read(state_dir)
        old = {s["id"]: s for lp in before["loops"] for s in lp["steps"]}
        now = ideas._now()
        for lp in clean["loops"]:
            for s in lp["steps"]:
                o = old.get(s["id"])
                same = o is not None and {k: v for k, v in o.items() if k not in ("by", "at")} == s
                s.update(by=o["by"] if same else by, at=o["at"] if same else now)
        same_all = kept(before) and _bare(before) == _bare(clean)
        rec = {k: v for k, v in _record(state_dir).items() if k not in ("cards", "was")}
        was = {k: v for k, v in before.items() if k != "was"} if by == "leader" and kept(before) and before["by"] == "person" and not same_all else before.get("was")
        rec.update(version=2, **clean, by=before["by"] if same_all else by, at=before["at"] if same_all else now)
        if was:
            rec["was"] = was
        ideas._write_json(_file(state_dir), rec)
    return read(state_dir)


def parse(answer: object, root: Path) -> dict | None:
    """The leader's answer, strictly: `{loops, currencies, hooks}` with one to three loops (one of a span), three to six steps each, each a name and a line; what is over a limit is cut, a feeling that
    is none is left unsaid, an intensity is clamped to 1–5, a currency a step names that is none is left out, the paths dev's tree does not have are left out. None for anything else (the call is
    tried once more)."""
    files = tree(Path(root))
    try:
        clean, _dropped = _clean(answer, set(files) | _folders(files), True)
    except ValueError:
        return None
    for lp in clean["loops"]:
        for s in lp["steps"]:
            s.pop("id")                                     # made at keeping
    return clean


def findings_on(data: dict) -> list[tuple[str, str]]:
    """`findings` with the part of the map each is about, as the map stamps its cards (`realm/map_parts.py`): `[(id, words)]`; a currency finding is on `cur:<id>`, a loop's on its first step."""
    loops, currencies = data.get("loops") or [], data.get("currencies") or []
    steps = [s for lp in loops for s in lp["steps"]]
    gives, takes = {c for s in steps for c in s["gives"]}, {c for s in steps for c in s["takes"]}
    first = {lp["span"]: lp["steps"][0]["id"] for lp in loops if lp["steps"]}
    out: list[tuple[str, str]] = []
    for c in currencies:
        if c["id"] not in gives:
            out.append((f"cur:{c['id']}", f"Nothing gives {c['name']}"))
        elif c["id"] not in takes:
            out.append((f"cur:{c['id']}", f"{c['name']} is only earned: it will pile up"))
    if currencies:
        out += [(first[lp["span"]], f"The {lp['span']} loop rewards nothing") for lp in loops if lp["span"] in first and not any(s["gives"] for s in lp["steps"])]
    fed = {lp["feeds"] for lp in loops}
    out += [(first[lp["span"]], f"Nothing feeds the {lp['span']} loop") for lp in loops if lp["span"] in first and lp["span"] != "core" and lp["span"] not in fed]
    out += [(first[lp["span"]], f"The {lp['span']} loop's feeling is flat") for lp in loops
            if lp["span"] in first and any(s["feel"] for s in lp["steps"]) and len({s["intensity"] for s in lp["steps"]}) == 1]
    return out


def findings(data: dict) -> list[str]:
    """What the loop says, by code, in the order it matters: a currency nothing gives, or nothing takes (it will pile up); a loop no step of which gives anything (where there are currencies); a span
    nothing feeds; a loop whose feeling is flat (all one intensity, where a feeling is said)."""
    return [words for _on, words in findings_on(data)]


def proposal(state_dir: Path) -> dict:
    """What the first proposal did: `{status: "" | "asking" | "done" | "failed", error, at}`."""
    got = _record(state_dir).get("proposal")
    got = got if isinstance(got, dict) else {}
    return {"status": got.get("status") if got.get("status") in ("asking", "done", "failed") else "", "error": str(got.get("error") or "")[:300], "at": str(got.get("at") or "")}


def save_proposal(state_dir: Path, status: str, error: str = "") -> None:
    """The proposal's state kept beside the cards (`status` "" forgets it: the next press asks again)."""
    with ideas.LOCK:
        rec = _record(state_dir)
        if status:
            rec["proposal"] = {"status": status, "error": " ".join(str(error).split())[:300], "at": ideas._now()}
        else:
            rec.pop("proposal", None)
        ideas._write_json(_file(state_dir), rec)


# -- the project's configs, chosen by code --------------------------------------------------------------------------------------------

def _class_of(path: str) -> int | None:
    """Why a file is a config of the game's: 0 `balance*`, 1 a `config/` folder's, 2 a `levels/` folder's, 3 `*.config.*`; None for one that is none."""
    bits = path.split("/")
    if any(b in _SKIP or b.startswith(".") for b in bits[:-1]) or is_secret(path) or Path(bits[-1]).suffix.lower() not in _TEXT:
        return None
    name = bits[-1].lower()
    if name.startswith("balance"):
        return 0
    if "config" in (b.lower() for b in bits[:-1]):
        return 1
    if "levels" in (b.lower() for b in bits[:-1]):
        return 2
    return 3 if ".config." in name else None


def config_files(root: Path) -> list[str]:
    """The files of dev's tree that are the game's configs, by name (CONFIGS at most, PER_FOLDER of one folder): `balance*`, then `config/`'s, `levels/`'s and `*.config.*`; shallow
    first, then by path. [] with no `dev`."""
    found = sorted(((c, p.count("/"), p) for p in tree(Path(root)) if (c := _class_of(p)) is not None))
    out: list[str] = []
    per: dict[str, int] = {}
    for _c, _depth, path in found:
        folder = path.rpartition("/")[0]
        if per.get(folder, 0) >= PER_FOLDER:
            continue
        per[folder] = per.get(folder, 0) + 1
        out.append(path)
        if len(out) >= CONFIGS:
            break
    return out


def heads(root: Path, paths: list[str]) -> dict[str, str]:
    """`{path: its first HEAD_LINES lines}` (each cut to HEAD_CHARS) of the first HEAD_FILES of `paths` that dev's tree has, a file too large or not text left out; HEAD_TOTAL
    characters at most in all."""
    files = tree(Path(root))
    tip = commit_goal.head(Path(root), REF)
    out: dict[str, str] = {}
    used = 0
    for path in [p for p in paths if p in files][:HEAD_FILES]:
        if files[path] > READ_BYTES or is_secret(path) or not tip:
            continue
        try:
            got = commit_goal.git(Path(root), "--literal-pathspecs", "show", f"{tip}:{path}")
        except (OSError, subprocess.SubprocessError):
            continue
        if got.returncode != 0 or "\0" in got.stdout[:2000]:
            continue
        text = _cut("\n".join(got.stdout.replace("\r\n", "\n").split("\n")[:HEAD_LINES]).strip(), HEAD_CHARS)
        if not text or used + len(text) > HEAD_TOTAL:
            continue
        out[path] = text
        used += len(text)
    return out


# -- its text -------------------------------------------------------------------------------------------------------------------------

def _step(n: int, s: dict, names: dict[str, str], level: int) -> list[str]:
    """A step as text: its name and line, then what it feels like and gives or takes, then what it rests on. Level 1 shortens the lines and the files, level 2 leaves the second line out,
    level 3 keeps a short name only."""
    if level > 2:
        return [f"{n}. {_cut(s['name'], 24)}"]
    out = [f"{n}. {s['name']}: {_cut(s['line'], 60) if level else s['line']}"]
    if level > 1:
        return out
    bits = [f"feels {s['feel']}, intensity {s['intensity']}/5"] if s["feel"] else []
    bits += [f"{word} {', '.join(names[c] for c in s[key])}" for key, word in (("gives", "gives"), ("takes", "takes")) if s[key]]
    files = s["rests_on"]
    shown = 1 if level else SHOWN
    rests = ", ".join(_cut(f, 80) for f in files[:shown]) + (f", +{len(files) - shown}" if len(files) > shown else "") if files else "no file named"
    return out + [f"   {'; '.join(bits)}. Rests on: {rests}" if bits else f"   Rests on: {rests}"]


def _body(data: dict, level: int) -> list[str]:
    names = {c["id"]: c["name"] for c in data["currencies"]}
    lines: list[str] = []
    for lp in data["loops"]:
        said = [lp["name"], (_cut(lp["line"], 60) if level else lp["line"]), f"Feeds the {lp['feeds']} loop" if lp["feeds"] else ""]
        lines += ["", f"{lp['span'].capitalize()} loop ({TIME[lp['span']]}): " + ". ".join(x.rstrip(".") for x in said if x) + "."]
        for n, s in enumerate(lp["steps"], 1):
            lines += _step(n, s, names, level)
    if data["currencies"]:
        steps = [s for lp in data["loops"] for s in lp["steps"]]
        lines += ["", "Currencies:"]
        for c in data["currencies"]:
            by = lambda key: ", ".join(_cut(s["name"], 24) for s in steps if c["id"] in s[key]) or "nothing"        # noqa: E731
            lines.append(f"- {_cut(c['name'], 24) if level > 2 else c['name']} ({c['kind']}){': ' + _cut(c['line'], 60) if c['line'] and level < 2 else ''}. Given by: {by('gives')}. Taken by: {by('takes')}.")
    if data["hooks"]:
        lines += ["", "Why a player comes back:"] + [f"- {h['when']}: {_cut(h['line'], 40 if level > 2 else 80) if level else h['line']}" for h in data["hooks"]]
    if said := findings(data):
        lines += ["", "What the loop says:"] + [f"- {f}" for f in said]
    return lines


def _fit(lines: list[str], room: int, more: str) -> list[str]:
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


def _changed(state_dir: Path, root: Path, steps: list[dict], since: str) -> str:
    """*Changed since your last call*, under the loops: each step's file (or a file in its folder) a commit of dev touched since `since`, with the goal that made it (`by you` for the
    person's own)."""
    head = "Changed under the loop since your last call"
    base = commit_goal.resolve(Path(root), since)
    if not base:
        return f"{head}: not known (no map was kept at that commit)."
    touched = commit_goal.last_touch(Path(root), REF, base)
    rows = []
    for s in steps:
        for path in s["rests_on"]:
            for file in sorted(f for f in touched if f == path or f.startswith(path + "/")):
                goal = commit_goal.of(state_dir, root, touched[file]["sha"]).get("goal")
                rows.append(f"- {s['name']}: {file} ({f'goal {goal}' if goal else 'by you'})")
    if not rows:
        return f"{head}: nothing."
    return "\n".join([f"{head}:"] + _fit(rows, CHANGED - len(head) - 2, "- and {n} more changes"))


def text(state_dir: Path, root: Path, since: str = "") -> str | None:
    """Game design's map as text: the loops from the core out, each its steps in order (name, line, feeling, what it gives and takes, what it rests on), then the currencies with what gives and
    takes them, why a player comes back and what the loop says, after a first line naming dev's head (`The map of the loop at dev <short>`); LIMIT characters at most (the lines and files
    are shortened, then the names, before anything is cut). The same bytes for the same record and the same head. None when no loop is kept. With `since` (the commit of the party's last call) ends with what
    changed under the steps' files."""
    data = read(state_dir)
    if not kept(data):
        return None
    tip = commit_goal.head(Path(root), REF)
    first = f"The map of the loop at dev {tip[:7]}" if tip else "The map of the loop"
    for level in range(4):
        body = "\n".join([first] + _body(data, level))
        if len(body) <= LIMIT:
            break
    body = body[:LIMIT]
    since = str(since or "").strip()
    return body + "\n\n" + _changed(Path(state_dir), Path(root), [s for lp in data["loops"] for s in lp["steps"]], since) if since else body
