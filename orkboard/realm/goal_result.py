"""What a goal changed against what its spec promised (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md F.3, decisions §206.8): by code, no model, nothing written.

    goal_result.touched(state_dir, root, slug, ref)     # {"parts": {part path}, "screens": [{screen, name, path}], "files": n}: what the commits of `ref` the goal's tasks brought changed
    goal_result.judge(promised, touched, tasks)         # [{id, kind, verdict, line}] a promised part: `ok` · `differs` · `missing`, then `extra` for a part changed that no line promised
    goal_result.of(sections, tasks, touch, done)        # one answer: {parties: [{party, parts: [...], done_when: [{text, state}]}], files, screens}

The promise is the party's section of the goal's spec, its *Will be* lines (`new|changed|gone <id>`, `realm/spec_sections.py`) and its *Done when*. What was done is read where the project has it:
Tech's map is the project's parts (the folders its files are in), so a part is **touched** when a file of it was changed by the goal's commits; Design's is the screens (`realm/goal_screens.py`:
the screens whose component, or a file it imports, was changed). A craft whose map the host does not read from the files (Product, Game design, Art …) has no such touch: a promised line
there is judged by the party's tasks alone (all merged: *As promised*; some: *Not quite*; none: *Not done*).

- **ok** *As promised*: the part was touched (or, with no touch to read, the party's tasks all landed).
- **differs** *Not quite*: the party's tasks all landed but no file of this part changed (or, with no touch, only some landed).
- **missing** *Not done*: not touched and the party's tasks have not all landed (or none did).
- **extra** *More than promised*: touched, and no *Will be* line of the party names it (only for a map that has a touch to read, and at most `EXTRA_MAX`).

A **Done when** line is `ok` once the goal is done, every task of the party landed and no check of the goal left a finding; else it has no mark (nothing says it is unmet or met).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.realm import goal_screens, idea_checks, project_map, spec_sections

EXTRA_MAX = 8
TOUCH_CRAFTS = {"tech": "parts", "design": "screens"}              # the crafts whose maps are read from the files, and by which key of `touched`


def _same(a: str, b: str) -> bool:
    """Two part paths name one part or one is inside the other; the project's top (`.`) is only itself."""
    a, b = str(a).strip("/"), str(b).strip("/")
    if not a or not b:
        return False
    if a == project_map.TOP or b == project_map.TOP:
        return a == b
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def touched(state_dir: Path, root: Path, slug: str, ref: str = "dev") -> dict:
    """What the goal's merged commits changed: `parts` (the System's parts, a part a file's folder), `screens` (`goal_screens.of`), `files` (how many files)."""
    files = goal_screens.goal_files(state_dir, root, slug, ref)
    return {"parts": sorted({project_map._part_of(f) for f in files}), "screens": goal_screens.of(state_dir, root, slug, ref), "files": len(files)}


def _on_screen(id_: str, screens: list[dict]) -> bool:
    """A *Will be* id names a screen the goal changed: by its id, its name or its path, without case, a leading slash or its dashes."""
    def key(x: str) -> str:
        return "".join(ch for ch in str(x).lower() if ch.isalnum())
    want = key(id_)
    return bool(want) and any(want in (key(s.get("screen")), key(s.get("name")), key(s.get("path"))) for s in screens)


def _landed(tasks: list[dict]) -> tuple[int, int]:
    """(merged, all) of a party's tasks, the dropped ones not counted."""
    live = [t for t in tasks if t.get("state") != "dropped"]
    return sum(1 for t in live if t.get("state") == "merged"), len(live)


def judge(promised: list[dict], touch: dict | None, tasks: list[dict], craft: str = "") -> list[dict]:
    """A party's promised parts and what became of them: `[{id, kind, verdict, line}]` (`kind` new · changed · gone, `line` the leader's words or ours), then each part touched and not promised (`extra`).
    `touch`: `touched()`'s answer or None (no goal commits to read); `craft` says which of its keys this party's map is read by (see the module)."""
    merged, total = _landed(tasks)
    by = TOUCH_CRAFTS.get(craft, "")
    out: list[dict] = []
    for w in promised:
        said = w.get("note") or ""
        if by and touch is not None:
            hit = any(_same(w["id"], p) for p in touch["parts"]) if by == "parts" else _on_screen(w["id"], touch["screens"])
            if hit:
                verdict, line = "ok", said or "as promised"
            elif total and merged == total:
                verdict, line = "differs", "its tasks landed, but nothing of this part changed"
            else:
                verdict, line = "missing", "not done yet" if merged else "nothing of it landed"
        elif total and merged == total:
            verdict, line = "ok", said or "as promised"
        elif merged:
            verdict, line = "differs", f"{merged} of {total} tasks landed"
        else:
            verdict, line = "missing", "nothing of it landed"
        out.append({"id": w["id"], "kind": w["kind"], "verdict": verdict, "line": line, "note": said})
    if by and touch is not None and promised:
        seen = [p for p in (touch["parts"] if by == "parts" else [s["screen"] for s in touch["screens"]]) if p != project_map.TOP]
        names = {s["screen"]: s["name"] for s in touch["screens"]}
        for p in seen:
            if len([x for x in out if x["verdict"] == "extra"]) >= EXTRA_MAX:
                break
            if not any((_same(w["id"], p) if by == "parts" else _on_screen(w["id"], [{"screen": p, "name": names.get(p, ""), "path": ""}])) for w in promised):
                out.append({"id": names.get(p, p) if by == "screens" else p, "kind": "", "verdict": "extra", "line": "changed, and its spec did not say so", "note": ""})
    return out


def of(sections: list[Any], tasks: list[dict], touch: dict | None, done: bool, crafts: dict[str, str], home: str = "") -> dict:
    """One answer for a goal: `sections` are `spec_sections.read`'s (`Section(party, title, parts)`), `tasks` the plan's, `touch` as `touched()`, `done` the goal is done, `crafts` `{party: craft}`, `home` the goal's own party (a plan of before stamps no party: its tasks are the home's).
    `{parties: [{party, title, parts, done_when: [{text, state}]}], files, screens}`; a party with no *Will be* and no *Done when* is left out."""
    checks_left = any((idea_checks.counts(t.get("findings") if isinstance(t.get("findings"), list) else None)["left"] or 0) > 0
                      for t in tasks if t.get("kind") in idea_checks.TAGS)
    out = []
    for s in sections:
        mine = [t for t in tasks if (t.get("party") or home) == s.party] if s.party else []
        will = spec_sections.will_be(s.parts.get("Will be", ""))
        lines = spec_sections.items(s.parts.get("Done when", ""))
        if not will and not lines:
            continue
        merged, total = _landed(mine)
        met = done and bool(total) and merged == total and not checks_left
        out.append({"party": s.party, "title": s.title, "parts": judge(will, touch, mine, crafts.get(s.party, "")),
                    "done_when": [{"text": x, "state": "ok" if met else ""} for x in lines]})
    return {"parties": out, "files": (touch or {}).get("files", 0), "screens": (touch or {}).get("screens", [])}
