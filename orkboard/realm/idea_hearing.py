"""A hearing (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §4; decisions §198.6): the goal's card in the middle and at most three sides around it, each side the words of the
leaders who stand on it, thrown by the person to the one they take. Pure code, no model, no face; `realm/idea_objections.py` gives the row, `core/idea_throw.py` and
`gui/ideas_hearing.py` do what a throw says, the faces (spec 120 §6.7) draw it.

    of_talk(rec, name_of)        # {moment: "talk", title, sides, left_out, own: true}: the sides of a Talk's disagreement (the stances of the Talk's record)
    of_fork(fork, name_of=None)  # {moment: "fork", id, about, title, sides, left_out, own: true}: the sides of a fork (`spec_sections` `forks`)
    is_open(rec)                 # a Talk's hearing is open: a no is unanswered, or the part that weighs the verdicts said a hearing (`rec["hearing"]` is true)
    namer(state_dir)             # leader id → the name it is called by (the person's role, else the library's)
    DIRS / DECIDED               # the three places a side stands; what a throw of a hearing no longer open is told
    snapshot(root, state_dir, slug) / dropped(...) / restore(...)   # what a throw may change, kept as it was and put back (spec 120 §6.7: Undo of a throw, `keeper.unthrow`); UNDO_S, WENT_ON

A side is `{dir, kind, leaders: [party], names: [name], also: [name], line, outcome}`, `dir` one of `right` · `left` · `up`, and for a Talk's `instead` / `after` / `after_title` / `doubts`
(`kind` one of `go` · `drop` · `smaller` · `later`; a fork's is `side`, with `party`). `line` is the first leader's own words, `also` the other leaders named after it.
`go` is always right. Left takes the first of `drop`, `later`; up the next of `smaller`, `later`, `drop`; a kind with no leader is no side. A doubt with neither `instead` nor `after`
adds its words to `go`'s side (`doubts`). More kinds than fit: the last is left out (`left_out`), and its leaders' words go to the decision (the throw names them overruled).
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from orkboard.realm import idea_spend, ideas, library, roles

DIRS = ("right", "left", "up")                  # → ← ↑ : a side's place; down is no side
DECIDED = "This was decided already"            # a throw of a hearing that is no longer open
WENT_ON = "It went on already"                 # an Undo of a throw that cannot be taken back any more
UNDO_S = 8                                      # how long a throw can be taken back, in seconds (the page's toast waits 6)
SNAP_BYTES = 4_000_000                          # a goal's folder larger than this is not kept for an Undo
GO_ALONE = "Go on anyway"                       # the `go` side when no leader said go
KINDS = ("go", "drop", "smaller", "later")
TITLE_CHARS = 80
LEFT_FIRST = ("drop", "later")                  # what the left takes, first of
UP_FIRST = ("smaller", "later", "drop")         # what the top takes, next of


def namer(state_dir) -> Callable[[str], str]:
    """The name a leader is called by: the person's role of it, else the library's, else its id."""
    def name_of(leader: str) -> str:
        r = roles.role(state_dir, leader)
        if r and r.get("name"):
            return str(r["name"])
        a = library.get(leader)
        return a.name if a else str(leader)
    return name_of


def is_open(rec: dict) -> bool:
    """A Talk's hearing is open while a no is unanswered (the decision waits), or while the weigher of the verdicts said a hearing for a doubt (`rec["hearing"]` is true)."""
    if not isinstance(rec, dict) or rec.get("mode") != "talk":
        return False
    return rec.get("hearing") is True or any(isinstance(o, dict) and not o.get("answer") for o in rec.get("objections") or [])


def _s(value: object) -> str:
    return " ".join(str(value or "").split()) if isinstance(value, (str, int)) else ""


def _joined(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _side(kind: str, group: list[dict], name_of: Callable[[str], str], line: str, outcome: str, **more) -> dict:
    names = [name_of(s["leader"]) for s in group]
    return {"dir": "", "kind": kind, "leaders": [s["party"] for s in group], "names": names, "also": names[1:], "line": line, "outcome": outcome, **more}


def of_talk(rec: dict, name_of: Callable[[str], str]) -> dict:
    """The hearing of a Talk's disagreement: `{moment: "talk", title, sides: [...], left_out: [...], own: true}` from the stances of its record (`party`, `leader`, `verdict`, `why`,
    `for`, `instead`, `after`, and `after_title` when the goal named is in line). `name_of(leader)`: the name a leader is called by. Never more than three sides."""
    stances = [s for s in rec.get("stances") or [] if isinstance(s, dict) and s.get("party") and s.get("leader")]
    against = [s for s in stances if s.get("verdict") in ("no", "doubt") and _s(s.get("why"))]
    goes = [s for s in stances if s not in against]
    drop = [s for s in against if s["verdict"] == "no" and not _s(s.get("instead")) and not _s(s.get("after"))]
    smaller = [s for s in against if _s(s.get("instead"))]
    later = [s for s in against if _s(s.get("after"))]
    doubts = [s for s in against if s["verdict"] == "doubt" and not _s(s.get("instead")) and not _s(s.get("after"))]
    made: dict[str, dict] = {}
    said = [{"party": s["party"], "leader": s["leader"], "name": name_of(s["leader"]), "why": _s(s.get("why"))} for s in doubts]
    made["go"] = _side("go", goes, name_of, _s(goes[0].get("for") or goes[0].get("stance")) if goes else "", "Do it" if goes else GO_ALONE, doubts=said)
    if drop:
        made["drop"] = _side("drop", drop, name_of, _s(drop[0]["why"]), "Drop it")
    if smaller:
        first = _s(smaller[0]["instead"])
        group = [s for s in smaller if _s(s["instead"]).lower() == first.lower()]
        made["smaller"] = _side("smaller", group, name_of, _s(group[0]["why"]), f"Do the smaller one: {first}", instead=first)
    if later:
        first = _s(later[0]["after"])
        group = [s for s in later if _s(s["after"]) == first]
        title = _s(group[0].get("after_title")) or first
        made["later"] = _side("later", group, name_of, _s(group[0]["why"]), f"After {title}", after=first, after_title=title)
    sides = [made["go"]]
    made["go"]["dir"] = "right"
    left = next((k for k in LEFT_FIRST if k in made), "")
    up = next((k for k in UP_FIRST if k in made and k != left), "")
    for k, d in ((left, "left"), (up, "up")):
        if k:
            made[k]["dir"] = d
            sides.append(made[k])
    left_out = [made[k] for k in ("drop", "later", "smaller") if k in made and k not in (left, up)]
    sides.sort(key=lambda s: DIRS.index(s["dir"]))
    return {"moment": "talk", "title": _title(against, name_of), "sides": sides, "left_out": left_out, "own": True}


def _title(against: list[dict], name_of: Callable[[str], str]) -> str:
    """*<Leader> and <Leader> disagree* (one leader: *<Leader> says no*, for a doubt *has a doubt*)."""
    names = list(dict.fromkeys(name_of(s["leader"]) for s in against))
    if not names:
        return "The leaders disagree"
    if len(names) == 1:
        return f"{names[0]} says no" if against[0]["verdict"] == "no" else f"{names[0]} has a doubt"
    return f"{_joined(names)} disagree"


def of_fork(fork: dict, name_of: Callable[[str], str] | None = None) -> dict:
    """The hearing of a fork: its sides in their order, right · left · up, at most three; a fourth is said by the fork's `about` and answered by the person's own words
    (`left_out`). A side is `{dir, kind: "side", party, leaders, names, also, line (its why), outcome (its says)}`. `name_of` names the leaders (a side's `leader`) for the title."""
    name = name_of or (lambda leader: str(leader))
    given = [s for s in fork.get("sides") or [] if isinstance(s, dict) and s.get("party")]
    sides = []
    for s, d in zip(given, DIRS):
        who = name(s.get("leader") or s["party"])
        sides.append({"dir": d, "kind": "side", "party": s["party"], "leaders": [s["party"]], "names": [who], "also": [], "line": _s(s.get("why")), "outcome": _s(s.get("says"))})
    left_out = [{"kind": "side", "party": s["party"], "leaders": [s["party"]], "line": _s(s.get("why")), "outcome": _s(s.get("says"))} for s in given[len(DIRS):]]
    leaders = list(dict.fromkeys(x for s in sides for x in s["names"]))
    about = _s(fork.get("about"))
    title = f"{_joined(leaders)} disagree" if len(leaders) > 1 and name_of else about
    return {"moment": "fork", "id": str(fork.get("id") or ""), "about": about, "title": title, "sides": sides, "left_out": left_out, "own": True}


# -- Undo of a throw (spec 120 §6.7) --------------------------------------------------------------------------------------------------------------

def snapshot(root: Path, state_dir: Path, slug: str) -> dict | None:
    """The goal as a throw finds it, to be put back: its page, every file of its state folder (in memory) and where `spend-gone.jsonl` ends (a drop appends the goal's ledger to it).
    None when the goal's folder is too large to keep (`SNAP_BYTES`): such a throw cannot be taken back."""
    page = Path(root) / ideas.IDEAS / f"{slug}.md"
    folder = Path(state_dir) / "ideas" / slug
    files, size = {}, 0
    for f in sorted(folder.rglob("*")) if folder.is_dir() else []:
        if f.is_file():
            data = f.read_bytes()
            size += len(data)
            if size > SNAP_BYTES:
                return None
            files[str(f.relative_to(folder))] = data
    gone = Path(state_dir) / "ideas" / idea_spend.GONE
    return {"page": page.read_text(encoding="utf-8") if page.exists() else None, "files": files, "gone_at": gone.stat().st_size if gone.exists() else 0, "appended": b""}


def dropped(state_dir: Path, snap: dict) -> None:
    """The goal was dropped: what its drop appended to `spend-gone.jsonl` is noted, so that putting the goal back takes it out again."""
    gone = Path(state_dir) / "ideas" / idea_spend.GONE
    if gone.exists():
        snap["appended"] = gone.read_bytes()[snap["gone_at"]:]


def restore(root: Path, state_dir: Path, slug: str, snap: dict) -> None:
    """Put the goal back as `snapshot` kept it: its page, its state folder as it was (the files a throw made go), the ledger lines a drop moved to `spend-gone.jsonl` taken out of it, and the pages' index."""
    import shutil
    with ideas.LOCK:
        if snap["page"] is not None:
            page = Path(root) / ideas.IDEAS / f"{slug}.md"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(snap["page"], encoding="utf-8")
        folder = Path(state_dir) / "ideas" / slug
        shutil.rmtree(folder, ignore_errors=True)
        for rel, data in snap["files"].items():
            (folder / rel).parent.mkdir(parents=True, exist_ok=True)
            (folder / rel).write_bytes(data)
        if snap["appended"]:
            gone = Path(state_dir) / "ideas" / idea_spend.GONE
            have = gone.read_bytes() if gone.exists() else b""
            at = have.find(snap["appended"], max(0, snap["gone_at"] - 1))
            if at >= 0:
                gone.write_bytes(have[:at] + have[at + len(snap["appended"]):])
        ideas._reindex(root)
