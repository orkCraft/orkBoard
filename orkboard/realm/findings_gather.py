"""Where a finding is found (docs/specs/132-four-levels-the-way-down-and-findings.md D.2; decisions §234.3): the gathering by code, each thing a `findings.add`, each call in a `try` that never fails what it
records. No model, no face.

    findings_gather.verdict(state_dir, wiki, repo, slug, ref="dev")   # the goal reached the discard: its verdict against the spec read once (`goal_result.of`), each `differs` and `missing` line a finding (`source` verdict,
                                                                 # `on` the part's id, `party` its party), the verdict and the checks kept in its quality record; how many findings were added
    findings_gather.lens(state_dir, repo, party, craft, concerns, ref="dev", now=None)   # a look of the party's leader ended: each `alert` on a part that a goal which reached the discard within `LENS_DAYS`
                                                                 # touched is that goal's (`source` lens); any other `alert` no goal was made of is a finding of no goal (`source` concern)
    findings_gather.hypothesis(state_dir, item, party="", goals=(), measured="")   # a hypothesis judged refuted (spec 133 D): one finding of no goal (`source` hypothesis, `on` its id, `party` Product's), the goals that
                                                                 # rested on it named in it; None for one that is not refuted
    findings_gather.touched_by(touch, craft, on)                 # whether the commits a goal brought changed the part `on` (a part of Tech's System, a screen of Design's)

**Checks** (D.2's `check` source): this code runs a goal's checks while the goal is at work (its check tasks, `realm/idea_checks.py`) and on the way into main (`realm/main_checks.py`), never again after the goal
landed, so no check "goes red after landing" here and nothing is gathered from one; the record keeps the checks as they stood when the goal landed (`checks`: each check task's checker, state and findings left), and a
later source that does run a check again calls `findings.add` with `source: "check"`. **Hypotheses** (`hypothesis`) are `hypothesis` below (spec 133 D); **measures** (`measure`) only call `findings.add` (§202 calls it).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from orkboard.realm import findings, goal_result, goal_team, idea_checks, ideas, spec_sections

LENS_DAYS = 14                                   # an alert on a part a goal touched this many days after it reached the discard is that goal's


def _verdict_rows(state_dir: Path, root: Path, repo: Path, slug: str, ref: str) -> list[dict]:
    """`goal_result.of`'s `parties`, each part flat: `[{party, id, kind, verdict, line}]`."""
    page = ideas.idea_page(root, slug)
    if page is None:
        return []
    tracks = ideas.tracks(root, make=False)
    home = str(page.get("track") or ideas.GENERAL)
    sections = spec_sections.read(page, [{"slug": t["slug"], "title": t["title"]} for t in tracks], home)["sections"]
    tasks = (ideas.plan(state_dir, slug) or {}).get("tasks") or []
    crafts = {t["slug"]: goal_team.craft_of(root, t["slug"]) for t in tracks}
    touch = goal_result.touched(state_dir, repo, slug, ref)
    got = goal_result.of(sections, tasks, touch, True, crafts, home, (ideas.plan(state_dir, slug) or {}).get("accepts"))
    return [{"party": p["party"], "id": w["id"], "kind": w["kind"], "verdict": w["verdict"], "line": w["line"]} for p in got["parties"] for w in p["parts"]]


def _checks(state_dir: Path, slug: str) -> list[dict]:
    """The goal's check tasks as they stand: `[{by, state, left}]`."""
    out = []
    for t in (ideas.plan(state_dir, slug) or {}).get("tasks") or []:
        if isinstance(t, dict) and t.get("kind") in idea_checks.TAGS:
            found = t.get("findings") if isinstance(t.get("findings"), list) else None
            out.append({"by": idea_checks.checker_of_tag(str(t.get("kind"))), "state": str(t.get("state") or ""), "left": idea_checks.counts(found)["left"] or 0})
    return out


def verdict(state_dir: Path, root: Path, repo: Path, slug: str, ref: str = "dev") -> int:
    """The goal reached the discard (see the module). `root` the Board's pages (the Wiki), `repo` the project's folder. 0 and nothing kept for a goal that is not done or is gone; a read that fails changes nothing and is 0, never an error."""
    try:
        if ideas.state(Path(state_dir), slug)["state"] != "done":
            return 0
        rows = _verdict_rows(Path(state_dir), Path(root), Path(repo), slug, ref)
        before = findings.record(state_dir, slug)
        findings.save_record(state_dir, slug, verdict=rows, checks=_checks(Path(state_dir), slug), at=before["at"] or dt.datetime.now().isoformat(timespec="seconds"), status=before["status"] or "gathered")
        added = 0
        for r in rows:
            if r["verdict"] in ("differs", "missing"):
                before_n = len(findings.of_goal(state_dir, slug))
                findings.add(state_dir, {"source": "verdict", "idea": slug, "party": r["party"], "on": r["id"], "found":
                                         f"{'Not done' if r['verdict'] == 'missing' else 'Not quite'}: {r['kind'] or 'change'} {r['id']} — {r['line']}"})
                added += len(findings.of_goal(state_dir, slug)) - before_n
        return added
    except Exception:
        return 0


def _cut(text: str, n: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def hypothesis(state_dir: Path, item: dict, party: str = "", goals=(), measured: str = "") -> dict | None:
    """A hypothesis judged `refuted` as a finding (spec 133 D; decisions §235.5): one finding of no goal, kept once (`source` hypothesis, `on` the hypothesis's id), `party` the Product party's slug ("" with none).
    `found` says what was believed, the way it was refuted, what was measured (`measured`, else the last lines of evidence) and **the goals that rested on it** (`goals`: `(slug, title)`), each part cut so that none
    pushes the goals' names out of the finding's 400 characters. None, and nothing kept, for a hypothesis that is not refuted; never an error (a read that fails changes nothing)."""
    try:
        if not isinstance(item, dict) or item.get("state") != "refuted":
            return None
        way = (item.get("verdict") or {}).get("way") or ""
        when = next((w["when"] for w in item.get("refuted") or [] if w["name"] == way), "")
        said = f"Refuted: {_cut(item['text'], 100)}" + (f" ({_cut((way + ': ' if way else '') + when, 80)})" if way or when else "") + "."
        held = f" Believed: {_cut(item['signal'], 60)}."
        seen = measured or "; ".join(e["text"] for e in (item.get("evidence") or [])[-2:])
        found = said + held + (f" Found: {_cut(seen, 80)}." if seen else "")
        if goals:
            found += " Goals that rested on it: " + _cut(", ".join(f"{slug} ({_cut(title, 30)})" for slug, title in goals), 110) + "."
        return findings.add(state_dir, {"source": "hypothesis", "idea": "", "party": party, "on": item["id"], "found": found})
    except Exception:
        return None


def touched_by(touch: dict | None, craft: str, on: str) -> bool:
    """Whether the commits a goal brought changed the part `on`: by the map the craft's party has (`goal_result.TOUCH_CRAFTS`); a craft with no such map is never touched."""
    by = goal_result.TOUCH_CRAFTS.get(craft, "")
    if not touch or not by or not on:
        return False
    if by == "parts":
        return any(goal_result._same(on, p) for p in touch.get("parts") or [])
    return goal_result._on_screen(on, touch.get("screens") or [])


def _recent(state_dir: Path, now: dt.datetime) -> list[str]:
    """The goals that reached the discard within `LENS_DAYS` (their record's `at`), newest first."""
    out = []
    base = Path(state_dir) / "ideas"
    for p in base.glob(f"*/{findings.QUALITY}"):
        try:
            at = dt.datetime.fromisoformat(findings.record(state_dir, p.parent.name)["at"])
        except ValueError:
            continue
        if now - at <= dt.timedelta(days=LENS_DAYS):
            out.append((at, p.parent.name))
    return [slug for _at, slug in sorted(out, reverse=True)]


def lens(state_dir: Path, repo: Path, party: str, craft: str, concerns: list[dict], ref: str = "dev", now: dt.datetime | None = None) -> int:
    """A look of `party`'s leader ended with `concerns` (`realm/concerns.py`'s): see the module. How many findings were added; never an error."""
    try:
        now = now or dt.datetime.now()
        alerts = [c for c in concerns if isinstance(c, dict) and c.get("level") == "alert" and not c.get("idea") and c.get("on")]
        if not alerts:
            return 0
        touches: dict[str, dict | None] = {}
        added = 0
        for c in alerts:
            home = ""
            for slug in _recent(state_dir, now):
                if slug not in touches:
                    try:
                        touches[slug] = goal_result.touched(Path(state_dir), Path(repo), slug, ref)
                    except Exception:
                        touches[slug] = None
                if touched_by(touches[slug], craft, str(c["on"])):
                    home = slug
                    break
            words = f"{c.get('name') or c['on']}: {c.get('what') or ''}"
            n = len(findings.of_goal(state_dir, home))
            findings.add(state_dir, {"source": "lens" if home else "concern", "idea": home, "party": party, "on": str(c.get("id") or c["on"]), "found": words})
            added += len(findings.of_goal(state_dir, home)) - n
        return added
    except Exception:
        return 0
