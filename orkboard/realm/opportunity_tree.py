"""Product's map, the opportunity solution tree (docs/specs/102-the-other-maps-and-picking-on-them.md §8; decisions §172): the outcome the project means to move, the users' jobs to
be done under it, the goals of the Board that serve each job and the experiments that test a goal. Kept by the person and Product's leader; read by code, no model (the leader's
first proposal is `core/idea_tree.py`'s); no face.

    opportunity_tree.read(state_dir)                          # {outcomes: [{id, text}], jobs: [{id, when, want, so, segment, by, at}], serves: [{job, goal}], tests: [{goal, experiment}]}
    opportunity_tree.keep(state_dir, outcomes, jobs, by)      # the outcomes and/or the jobs replaced whole (None leaves one as it is) → the record; ValueError in plain words
    opportunity_tree.attach(state_dir, job, goal)             # the goal serves the job (a goal serves one job at most: it moves); an empty `job` detaches the goal → the `serves`
    opportunity_tree.test(state_dir, goal, experiment)        # the experiment tests the goal (an experiment tests one goal at most); an empty `experiment` takes the goal's off → the `tests`
    opportunity_tree.parse(answer)                            # the leader's answer, strictly → {outcomes: [{text}], jobs: [{when, want, so, segment}]} or None
    opportunity_tree.goals(state_dir, pages)                  # {slug: {slug, title, element, place}} of the goals the record names that the Board still has
    opportunity_tree.text(state_dir, root, since="", pages=None)   # Product's leader's map as text (~3,000 characters), with the hypotheses under their job; None when nothing is kept
    opportunity_tree.proposal(state_dir) / save_proposal(...) # what the first proposal did: {status: "asking"|"done"|"failed", error, at}

`<state_dir>/tree.json` is `{outcomes, jobs, serves, tests, proposal}`. One or two outcomes and three to seven jobs; a job is *When <when>, I want to <want>, so I can <so>* for a
`segment` of the project's people. A job's `id` stays with it (its want's slug at first), so its goals stay when the person words it again; a job kept again unchanged keeps its `by` and
`at`, so the leader's jobs the person did not touch stay *Proposed by the leader*. A job gone takes its `serves` with it. A goal's `place` is where its work is: "line" (not started, or
waiting for the person), "work" (read, planned, being done or judged, or its way talked), "done" (the Board's `done`, a pitch sent or passed). The text is the same bytes for the same record
and the same goals; under each job its hypotheses (`realm/hypotheses.py`: *Hypothesis (open): … — we'll know when …*; the proposed ones are not shown), the ones on no job after the jobs; `root` and `since` are there for `map_text.of`'s uniform call: nothing under the tree changes with the code.
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.realm import hypotheses, ideas, idea_element

FILE = "tree.json"
MIN_OUTCOMES, MAX_OUTCOMES = 1, 2
MIN_JOBS, MAX_JOBS = 3, 7
OUTCOME_CHARS, PART_CHARS, SEGMENT_CHARS = 160, 90, 40       # an outcome's text, a job's when / want / so, its segment
LIMIT = 3000                                                  # the text, at most (map_text.LIMIT's)
SHOWN = (5, 3, 2, 1, 0)                                       # the most goals a job's line names, tried in turn until the text fits
BY = ("person", "leader")
WORK = ("reading", "planning", "working", "judging", "talk", "decided", "sections")      # the Board's states of a goal being read, planned, done or talked (goal_place's `_AT_WORK`, `_WAY`)
DONE = ("done", "sent", "passed")
PLACE_WORDS = {"line": "in line", "work": "at work", "done": "done"}
NOTHING = "Nothing to read yet: the outcome and the users' jobs."
_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
_SLUG = re.compile(r"[a-z0-9-]{1,80}")
_WORDS = re.compile(r"[a-z0-9]+")
_LEAD = {"when": re.compile(r"^when\s+", re.I), "want": re.compile(r"^(?:i\s+want\s+to|to)\s+", re.I), "so": re.compile(r"^so\s+(?:that\s+i\s+can\s+|that\s+|i\s+can\s+)", re.I)}


def _words(value: object, n: int) -> str:
    return " ".join(value.split())[:n] if isinstance(value, str) else ""


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:max(0, n - 1)].rstrip() + "…"


def _file(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


def _record(state_dir: Path) -> dict:
    got = ideas._json(_file(state_dir))
    return got if isinstance(got, dict) else {}


def _part(key: str, value: object) -> str:
    """A job's `when`, `want` or `so` as it is kept: one line, bounded, without the words the sentence puts before it, without a full stop at the end."""
    text = _words(value, PART_CHARS * 2)
    text = _LEAD[key].sub("", text).strip().rstrip(".,;:").strip()
    return text[:PART_CHARS].rstrip()


# -- the record kept ------------------------------------------------------------------------------------------------------------------

def read(state_dir: Path) -> dict:
    """The record kept, each part checked: whatever is not of the shape reads as absent (the file is not trusted); `serves` and `tests` name jobs and goals by their ids."""
    rec = _record(state_dir)
    outcomes = [{"id": r["id"], "text": _words(r.get("text"), OUTCOME_CHARS)} for r in rec.get("outcomes", []) if isinstance(r, dict)
                and isinstance(r.get("id"), str) and _ID.fullmatch(r["id"]) and _words(r.get("text"), OUTCOME_CHARS)] if isinstance(rec.get("outcomes"), list) else []
    jobs: list[dict] = []
    for r in rec.get("jobs", []) if isinstance(rec.get("jobs"), list) else []:
        if not (isinstance(r, dict) and isinstance(r.get("id"), str) and _ID.fullmatch(r["id"])):
            continue
        when, want, so = (_part(k, r.get(k)) for k in ("when", "want", "so"))
        if when and want and so:
            jobs.append({"id": r["id"], "when": when, "want": want, "so": so, "segment": _words(r.get("segment"), SEGMENT_CHARS), "by": r["by"] if r.get("by") in BY else "person",
                         "at": str(r.get("at") or "")})
    have = {j["id"] for j in jobs}
    serves, seen = [], set()
    for r in rec.get("serves", []) if isinstance(rec.get("serves"), list) else []:
        if isinstance(r, dict) and r.get("job") in have and isinstance(r.get("goal"), str) and _SLUG.fullmatch(r["goal"]) and r["goal"] not in seen:
            seen.add(r["goal"])
            serves.append({"job": r["job"], "goal": r["goal"]})
    tests, tested = [], set()
    for r in rec.get("tests", []) if isinstance(rec.get("tests"), list) else []:
        if isinstance(r, dict) and all(isinstance(r.get(k), str) and _SLUG.fullmatch(r[k]) for k in ("goal", "experiment")) and r["experiment"] not in tested and r["goal"] != r["experiment"]:
            tested.add(r["experiment"])
            tests.append({"goal": r["goal"], "experiment": r["experiment"]})
    return {"outcomes": outcomes[:MAX_OUTCOMES], "jobs": jobs[:MAX_JOBS], "serves": serves, "tests": tests}


def _id_of(text: str, taken: set[str], fallback: str) -> str:
    base = "-".join(_WORDS.findall(text.lower()))[:36].strip("-") or fallback
    out, n = base, 1
    while out in taken:
        n += 1
        out = f"{base}-{n}"
    return out


def _clean_outcomes(items: object) -> list[dict]:
    """The outcomes as they would be kept before their ids: [{id?, text}]. ValueError in plain words."""
    if not isinstance(items, list) or not MIN_OUTCOMES <= len(items) <= MAX_OUTCOMES:
        raise ValueError(f"A tree has {MIN_OUTCOMES} or {MAX_OUTCOMES} outcomes")
    out, seen = [], set()
    for o in items:
        text = _words(o.get("text") if isinstance(o, dict) else None, OUTCOME_CHARS)
        if not text:
            raise ValueError("An outcome is a few words on what the project means to move")
        if text.lower() in seen:
            raise ValueError("Two outcomes say the same")
        seen.add(text.lower())
        out.append({"id": o.get("id") if isinstance(o.get("id"), str) else "", "text": text})
    return out


def _clean_jobs(items: object) -> list[dict]:
    """The jobs as they would be kept before their ids, `by` and `at`: [{id?, when, want, so, segment}]. ValueError in plain words."""
    if not isinstance(items, list) or not MIN_JOBS <= len(items) <= MAX_JOBS:
        raise ValueError(f"A tree has {MIN_JOBS} to {MAX_JOBS} jobs")
    out, seen = [], set()
    for j in items:
        if not isinstance(j, dict):
            raise ValueError("A job is a situation, a motive, an outcome and a segment")
        when, want, so = (_part(k, j.get(k)) for k in ("when", "want", "so"))
        if not (when and want and so):
            raise ValueError("A job says when, what the person wants to do and so what they can")
        if (when.lower(), want.lower(), so.lower()) in seen:
            raise ValueError(f"Two jobs say the same: {want}")
        seen.add((when.lower(), want.lower(), so.lower()))
        out.append({"id": j.get("id") if isinstance(j.get("id"), str) else "", "when": when, "want": want, "so": so, "segment": _words(j.get("segment"), SEGMENT_CHARS)})
    return out


def keep(state_dir: Path, outcomes: object, jobs: object, by: str) -> dict:
    """The outcomes and/or the jobs replaced whole (`None` leaves that part as it is) → the record. `by` is who kept the jobs: "person" or "leader"; a job that is the same as the one kept
    under its `id` (or, with no `id`, the same words) keeps its own `by` and `at`. A job gone takes its goals with it. ValueError, in plain words, for a `by` that is none, a count outside one or
    two outcomes or three to seven jobs, an outcome or a job with a part missing, two the same."""
    if by not in BY:
        raise ValueError(f"A tree is kept by the person or the leader, not {by!r}")
    new_outcomes = _clean_outcomes(outcomes) if outcomes is not None else None
    new_jobs = _clean_jobs(jobs) if jobs is not None else None
    with ideas.LOCK:
        rec = _record(state_dir)
        now, mine = ideas._now(), read(state_dir)
        if new_outcomes is not None:
            before, taken = {o["id"]: o for o in mine["outcomes"]}, set()
            kept = []
            for o in new_outcomes:
                oid = o["id"] if o["id"] in before and o["id"] not in taken else _id_of(o["text"], taken | set(before), "outcome")
                taken.add(oid)
                kept.append({"id": oid, "text": o["text"]})
            rec["outcomes"] = kept
        if new_jobs is not None:
            before = {j["id"]: j for j in mine["jobs"]}
            words = {(j["when"], j["want"], j["so"]): j["id"] for j in mine["jobs"]}
            taken, kept = set(), []
            for j in new_jobs:
                same_id = j["id"] if j["id"] in before and j["id"] not in taken else ""
                old = before.get(same_id or words.get((j["when"], j["want"], j["so"]), ""))
                if old is not None and old["id"] in taken:
                    old = None
                unchanged = old is not None and (old["when"], old["want"], old["so"], old["segment"]) == (j["when"], j["want"], j["so"], j["segment"])
                jid = old["id"] if old is not None else _id_of(j["want"], taken | set(before), "job")
                taken.add(jid)
                kept.append({"id": jid, "when": j["when"], "want": j["want"], "so": j["so"], "segment": j["segment"], "by": old["by"] if unchanged else by, "at": old["at"] if unchanged else now})
            rec["jobs"] = kept
            rec["serves"] = [s for s in mine["serves"] if s["job"] in taken]
        ideas._write_json(_file(state_dir), rec)
    return read(state_dir)


def _goal(value: object, what: str) -> str:
    slug = value.strip() if isinstance(value, str) else ""
    if not _SLUG.fullmatch(slug):
        raise ValueError(f"{what} is a goal's name")
    return slug


def attach(state_dir: Path, job: str, goal: str) -> list[dict]:
    """The goal serves the job → the `serves`. A goal serves one job at most: attached to another it moves; an empty `job` detaches it. ValueError for a job that is not kept or a goal
    that is no name."""
    goal = _goal(goal, "What serves a job")
    job = job.strip() if isinstance(job, str) else ""
    with ideas.LOCK:
        mine = read(state_dir)
        if job and job not in {j["id"] for j in mine["jobs"]}:
            raise ValueError("That job is gone")
        serves = [s for s in mine["serves"] if s["goal"] != goal] + ([{"job": job, "goal": goal}] if job else [])
        ideas._write_json(_file(state_dir), {**_record(state_dir), "serves": serves})
    return read(state_dir)["serves"]


def test(state_dir: Path, goal: str, experiment: str) -> list[dict]:
    """The experiment (a goal) tests the goal → the `tests`. An experiment tests one goal at most: set on another it moves; an empty `experiment` takes all of the goal's off, an empty `goal`
    takes the experiment off. ValueError for a name that is none, a goal tested by itself, and for both empty."""
    goal, experiment = (v.strip() if isinstance(v, str) else "" for v in (goal, experiment))
    if not goal and not experiment:
        raise ValueError("Say which goal an experiment tests")
    goal, experiment = (_goal(v, "What an experiment tests") if v else "" for v in (goal, experiment))
    if goal and goal == experiment:
        raise ValueError("A goal is not its own experiment")
    with ideas.LOCK:
        tests = read(state_dir)["tests"]
        if goal and experiment:
            tests = [t for t in tests if t["experiment"] != experiment] + [{"goal": goal, "experiment": experiment}]
        else:
            tests = [t for t in tests if t["experiment"] != experiment] if experiment else [t for t in tests if t["goal"] != goal]
        ideas._write_json(_file(state_dir), {**_record(state_dir), "tests": tests})
    return read(state_dir)["tests"]


def parse(answer: object) -> dict | None:
    """The leader's answer, strictly: `{outcomes: [{text}], jobs: [{when, want, so, segment}]}` with one or two outcomes and three to seven jobs, every part a non-empty text, no two outcomes or
    jobs the same. None for anything else (the call is tried once more)."""
    if not isinstance(answer, dict):
        return None
    jobs = answer.get("jobs")
    if not isinstance(jobs, list) or not all(isinstance(j, dict) and all(isinstance(j.get(k), str) and j[k].strip() for k in ("when", "want", "so", "segment")) for j in jobs):
        return None
    try:
        outcomes, kept = _clean_outcomes(answer.get("outcomes")), _clean_jobs([{k: v for k, v in j.items() if k != "id"} for j in jobs])
    except ValueError:
        return None
    return {"outcomes": [{"text": o["text"]} for o in outcomes], "jobs": [{k: j[k] for k in ("when", "want", "so", "segment")} for j in kept]}


def proposal(state_dir: Path) -> dict:
    """What the first proposal did: `{status: "" | "asking" | "done" | "failed", error, at}`."""
    got = _record(state_dir).get("proposal")
    got = got if isinstance(got, dict) else {}
    return {"status": got.get("status") if got.get("status") in ("asking", "done", "failed") else "", "error": str(got.get("error") or "")[:300], "at": str(got.get("at") or "")}


def save_proposal(state_dir: Path, status: str, error: str = "") -> None:
    """The proposal's state kept beside the tree (`status` "" forgets it: the next press asks again)."""
    with ideas.LOCK:
        rec = _record(state_dir)
        if status:
            rec["proposal"] = {"status": status, "error": " ".join(str(error).split())[:300], "at": ideas._now()}
        else:
            rec.pop("proposal", None)
        ideas._write_json(_file(state_dir), rec)


# -- the goals the tree names ---------------------------------------------------------------------------------------------------------

def place_of(state_dir: Path, slug: str) -> str:
    """Where a goal's work is: "line" | "work" | "done"."""
    state = ideas.state(state_dir, slug)["state"]
    return "done" if state in DONE else "work" if state in WORK else "line"


def goals(state_dir: Path, pages: Path) -> dict[str, dict]:
    """`{slug: {slug, title, element, place}}` of every goal the record names (as serving a job or as an experiment) that the Board's pages still have; a goal dropped from the Board is
    left out."""
    rec = read(state_dir)
    out: dict[str, dict] = {}
    for slug in dict.fromkeys([s["goal"] for s in rec["serves"]] + [t[k] for t in rec["tests"] for k in ("goal", "experiment")]):
        try:
            page = ideas.idea_page(Path(pages), slug)
        except (OSError, ValueError):
            page = None
        if page is not None:
            out[slug] = {"slug": slug, "title": _words(page.title or slug, 80), "element": idea_element.of(state_dir, slug), "place": place_of(state_dir, slug)}
    return out


def _places(state_dir: Path, pages: Path | None, slugs: list[str]) -> dict[str, str]:
    """`{slug: place}` of the goals among `slugs` that the Board's pages still have; empty without `pages` (the goals cannot be told from the Board's)."""
    out: dict[str, str] = {}
    for slug in dict.fromkeys(slugs) if pages is not None else ():
        try:
            page = ideas.idea_page(Path(pages), slug)
        except (OSError, ValueError):
            page = None
        if page is not None:
            out[slug] = place_of(state_dir, slug)
    return out


# -- its text -------------------------------------------------------------------------------------------------------------------------

def _named(slug: str, known: dict[str, dict] | None) -> str | None:
    """A goal as the text names it: its title and place, else its slug; None for a goal the Board no longer has."""
    if known is None:
        return slug
    got = known.get(slug)
    return f"{got['title']} ({PLACE_WORDS[got['place']]})" if got else None


def text(state_dir: Path, root: Path, since: str = "", pages: Path | None = None) -> str | None:
    """Product's map as text: the outcome, each job as its sentence with its segment and the goals that serve it (their title and place with `pages`, else their names), the experiments
    that test a goal after it, the hypotheses under their job (open, testing, held, refuted; not the proposed ones) and the ones on no job after the jobs, and the jobs no goal serves named at the
    end; LIMIT characters at most (the hypotheses' words are cut before a goal is left out). The same bytes for the same record and the same goals. None when nothing is kept."""
    rec = read(state_dir)
    if not rec["outcomes"] and not rec["jobs"]:
        return None
    known = goals(state_dir, Path(pages)) if pages is not None else None
    testers: dict[str, list[str]] = {}
    for t in rec["tests"]:
        if (name := _named(t["experiment"], known)) is not None and (known is None or t["goal"] in known):
            testers.setdefault(t["goal"], []).append(name)
    mine: dict[str, list[tuple[str, str]]] = {}
    for s in rec["serves"]:
        if (name := _named(s["goal"], known)) is not None:
            mine.setdefault(s["job"], []).append((s["goal"], name))

    kept_hyp = hypotheses.read(state_dir)["items"]
    places = _places(state_dir, pages, [t for h in kept_hyp for t in h["tests"]])
    shown_hyp = hypotheses._shown(kept_hyp, places, ("open", "testing", "held", "refuted"))
    job_ids = {j["id"] for j in rec["jobs"]}

    def build(shown: int, tail: bool = True, cap: int = hypotheses.TEXT_CHARS, n_hyp: int = len(shown_hyp)) -> str:
        under: dict[str, list[tuple[dict, str]]] = {}
        for h, st in shown_hyp[:n_hyp]:
            under.setdefault(h["on"] if h["on"] in job_ids else "", []).append((h, st))
        lines = ["The opportunity tree", ""]
        lines += [f"Outcome: {o['text']}" for o in rec["outcomes"]] or ["Outcome: not said yet"]
        lines.append("")
        for n, j in enumerate(rec["jobs"], 1):
            seg = f" For {j['segment']}." if j["segment"] else ""
            lines.append(f"{n}. When {j['when']}, I want to {j['want']}, so I can {j['so']}.{seg}")
            serving = mine.get(j["id"], [])
            if not serving:
                lines.append("   Served by: no goal yet")
            else:
                names = [name + (f" (tested by {', '.join(testers[slug])})" if slug in testers else "") for slug, name in serving[:shown]]
                more = len(serving) - len(names)
                lines.append("   Served by: " + ("; ".join(names) + (f"; and {more} more" if more else "") if names else f"{len(serving)} goals"))
            lines += [f"   {hypotheses._sentence(h, st, cap)}" for h, st in under.get(j["id"], [])]
        if under.get(""):
            lines += [""] + [hypotheses._sentence(h, st, cap) for h, st in under[""]]
        empty = [f"{n} ({_cut(j['want'], 40)})" for n, j in enumerate(rec["jobs"], 1) if j["id"] not in mine]
        if rec["jobs"] and tail:
            lines += ["", ("No goal serves yet: " + ", ".join(empty)) if empty else "A goal serves every job."]
        return "\n".join(lines)

    caps = hypotheses.CAPS[:3] if shown_hyp else hypotheses.CAPS[:1]
    for shown, tail in [(n, True) for n in SHOWN] + [(0, False)]:
        for cap in caps:
            out = build(shown, tail, cap)
            if len(out) <= LIMIT:
                return out
    for n_hyp in range(len(shown_hyp) - 1, -1, -1):                      # the jobs are named before the last hypotheses are
        out = build(0, False, caps[-1], n_hyp)
        if len(out) <= LIMIT:
            return out
    return out[:LIMIT]
