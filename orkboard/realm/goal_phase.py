"""A goal's phase in its page (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md part A; decisions §255.3): the five phases a goal is in, whatever its fine state, and the keys of its
front matter that say it to any AI tool reading the repository.

    goal_phase.PHASES                      # ("new", "talk", "spec", "work", "done")
    goal_phase.of("sketch")                # "spec": the phase of a fine state (`ideas.STATES`; a state dict too)
    goal_phase.first("work")               # "ready": the fine state a goal moved to a phase from outside starts at
    goal_phase.keys(st, gate, asks, by)    # the front matter of a goal: {"phase", "route", "queue", "asks", "gate", "by", "schema"}, a key only where it has something to say
    goal_phase.gate_of(plan)               # "<short commit> · <n> files · green | red | did not finish" from the goal's last gate, "" when no gate ran
    goal_phase.mirror(root, state_dir)     # the keys written into each goal page where they differ from its state; `state.json` keeps `phase_written`
    goal_phase.moved(root, state_dir)      # the pages whose phase was changed by someone else since the Board wrote it
    goal_phase.move_to(state_dir, slug, phase)        # …and the goal's state moved there
    goal_phase.outside_cards(page)         # a question laid outside (`asks: person`, a line of *Open questions* with no answer) as the hand's cards

Pure code over the Board's files: no face, no model, no git (the host asks the Board's tree for the write and reads the commit's author).
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from orkboard.realm import idea_questions, ideas
from orkboard.realm.idea_page import Page

PHASES = ("new", "talk", "spec", "work", "done")
SCHEMA = "3"                                       # the Board's schema as pages carry it (decisions §255.12; 2: a *Done when* line may carry its proof, §257.4; 3: a party's section may hold *Talk* and *Accepted*, §258.6). A page of 1 or 2 is read as it is; the Board writes 3 when it next writes it
SCHEMA_FLOOR = "2"                                 # `orkboard check` finds a page of an older schema than this; 3 only adds two parts, so a page of 2 asks for no rewrite
STATE_PHASE = {"raw": "new", "reading": "new", "asks": "new", "proposed": "new", "judging": "new", "judged": "new", "sent": "new", "passed": "new",
               "routed": "talk", "talk": "talk",
               "decided": "spec", "sketch": "spec", "sections": "spec",
               "ready": "work", "planning": "work", "plan": "work", "working": "work", "failed": "work",
               "done": "done"}
FIRST = {"new": "raw", "talk": "routed", "spec": "decided", "work": "ready", "done": "done"}
WORDS = {"talk": "Talk", "spec": "Spec", "work": "Work", "done": "Done"}      # a phase in a word, as `board_ask` says it to the Orkmaster; a goal in `new` is an "Idea"
MANAGED = ("phase", "route", "queue", "asks", "gate", "by", "schema")          # the keys the Board writes (`spec` is a tool's: only read)
KEPT = ("route", "gate")                            # a page's own, kept while the Board's state has none to write (an AI tool routed it or ran its gate: trial 152 E, F2)
PERSON = "person"
OUTSIDE_ID = "page-"                                # the id of a card made of a page's question: `page-<index of the question>`


def of(state: object) -> str:
    """The phase of a fine state (a word of `ideas.STATES`, or a state's dict); `new` for any other."""
    word = state.get("state") if isinstance(state, dict) else state
    return STATE_PHASE.get(str(word or ""), "new")


def first(phase: str) -> str:
    """The fine state a goal starts at when someone moved it to `phase` from outside; `raw` for a word that is no phase."""
    return FIRST.get(phase, "raw")


def words() -> dict[str, str]:
    """`board_ask`'s table: every fine state past `new` in the word of its phase, a failed one said so."""
    out = {s: WORDS[p] for s, p in STATE_PHASE.items() if p in WORDS}
    out["failed"] = "Work, failed"
    return out


# -- the keys -----------------------------------------------------------------------------------------------------------------------

def gate_of(plan: dict | None) -> str:
    """The goal's last gate in a line, `<short commit> · <n> files · green | red | did not finish` (a task still to land has no commit: `—`); "" when no gate ran. The last is the
    newest finish among the plan's tasks that ran one (`tests` with a verdict and `ran` not false)."""
    best, at = None, ""
    for t in (plan or {}).get("tasks") or []:
        tests = t.get("tests") if isinstance(t, dict) else None
        if not isinstance(tests, dict) or "green" not in tests or tests.get("ran") is False:
            continue
        if best is None or str(t.get("finished") or "") >= at:
            best, at = t, str(t.get("finished") or "")
    if best is None:
        return ""
    tests, diff = best["tests"], best.get("diff") if isinstance(best.get("diff"), dict) else {}
    files = diff.get("files") if isinstance(diff.get("files"), int) and not isinstance(diff.get("files"), bool) else 0
    verdict = "did not finish" if tests.get("env") else "green" if tests.get("green") else "red"
    return f"{str(best.get('commit') or '')[:7] or '—'} · {files} file{'' if files == 1 else 's'} · {verdict}"


def keys(st: dict, gate: str = "", asks: bool = False, by: str = "") -> dict[str, str]:
    """The front matter of a goal's page that says where it is (A.2), in the order they are written: `phase`; `route` (the parties' slugs of its route, in order, `tech, design`); `queue`
    (`hold` or `night` when its state has it); `asks` (`person` while a card waits for the person); `gate`; `by` (`person`, or a tool's name); `schema`."""
    out = {"phase": of(st)}
    route = [str(r.get("party")) for r in st.get("route") or [] if isinstance(r, dict) and r.get("party")]
    if route:
        out["route"] = ", ".join(route)
    if st.get("queue") in ("hold", "night"):
        out["queue"] = st["queue"]
    if asks:
        out["asks"] = PERSON
    if gate:
        out["gate"] = gate
    if by:
        out["by"] = by
    out["schema"] = SCHEMA
    return out


def phase_of_page(page: Page | None) -> str:
    """The phase a page says: "" when it says none (a page of before, or a word that is no phase)."""
    got = page.get("phase").strip().lower() if page is not None else ""
    return got if got in PHASES else ""


def _needs_of(root: Path, state_dir: Path) -> Callable:
    from orkboard.realm import board_map
    return lambda i, st, plan, asks: board_map.idea_needs(root, state_dir, i, st, plan, asks)


def _more_than_schema(page: Page, before: str, schema: str | None) -> bool:
    """Whether the page, as the Board would write it, differs from `before` in a key other than `schema` (spec 155 G.1: a page is not written only to move its schema).
    `schema`: what the page said (None for no such line)."""
    meta = list(page.meta)
    try:
        if schema is None:
            page.meta = [(k, v) for k, v in meta if k != "schema"]
        else:
            page.set("schema", schema)
        return page.text() != before
    finally:
        page.meta = meta


def mirror(root: Path, state_dir: Path, needs: Callable | None = None, only: str = "") -> list[str]:
    """The keys of each goal's page written where they differ from its state (A.3), and `state.json`'s `phase_written` set to the phase written: the slugs of the pages written. A page is
    written only when its text would change. `needs(i, st, plan, asks)` answers the rows of the hand for a goal (the host's, which has more than the Board's own); `asks: person` is there
    while it answers any. `by` says who laid the goal (decisions §255.3): the page's own, else the person's; the Board never changes one a page has. `only`: one goal's slug."""
    needs = needs or _needs_of(root, state_dir)
    written = []
    found, pages = ideas.ideas_and_pages(root)
    for i in found:
        slug, page = i["slug"], pages[i["slug"]]
        if only and slug != only:
            continue
        with ideas.LOCK:
            st = ideas.state(state_dir, slug)
            phase = of(st)
            changing = st.get("phase_written") != phase
            by = page.get("by") or PERSON                # who laid it: kept as the page says, never who moved it last
            plan = ideas.plan(state_dir, slug)
            try:
                asking = bool(needs(i, st, plan, ideas.items(page.section("Open questions"))))
            except Exception:                  # a row that cannot be read leaves `asks` as it was written
                asking = page.get("asks") == PERSON
            asking = asking or (page.get("asks") == PERSON and bool(idea_questions.open_of(page.section("Open questions"))))      # a question no card can show still waits
            want = keys(st, gate_of(plan), asking, by)
            before = page.text()
            schema = page.get("schema") if any(k == "schema" for k, _v in page.meta) else None
            for k in MANAGED:
                if k in want:
                    page.set(k, want[k])
                elif k in KEPT and page.get(k):
                    continue
                elif k != "by":
                    page.meta = [(mk, mv) for mk, mv in page.meta if mk != k]
            if page.text() != before and _more_than_schema(page, before, schema):
                ideas._write(Path(root) / ideas.IDEAS / f"{slug}.md", page.text())
                written.append(slug)
            if changing:
                ideas.save_state(state_dir, slug, phase_written=phase)
    return written


# -- moved outside (A.4) -----------------------------------------------------------------------------------------------------------

def moved(root: Path, state_dir: Path) -> list[dict]:
    """The goals whose page says a phase other than the Board wrote (A.4): `[{slug, title, to, was, new, by}]`; `to` the phase the page says, `was` the phase of the goal's state ("" for none),
    `new` whether the goal has no state folder (a page laid outside), `by` the page's own `by` ("" when it says none). Not here: a page with no `phase` (from before: the next flush gives
    it one), one that says what the Board wrote, and a goal that has nothing written yet (`phase_written` "") whose page agrees with its state."""
    out = []
    found, pages = ideas.ideas_and_pages(root)
    with ideas.LOCK:
        for i in found:
            slug, page = i["slug"], pages[i["slug"]]
            to = phase_of_page(page)
            if not to:
                continue
            if not (ideas.state_folder(state_dir, slug) / "state.json").exists():
                out.append({"slug": slug, "title": page.title or slug, "to": to, "was": "", "new": True, "by": page.get("by")})
                continue
            st = ideas.state(state_dir, slug)
            if to != (st.get("phase_written") or of(st)):
                out.append({"slug": slug, "title": page.title or slug, "to": to, "was": of(st), "new": False, "by": page.get("by")})
    return out


def move_to(state_dir: Path, slug: str, phase: str) -> None:
    """The goal's state moved to where a phase starts (`first`), the phase kept as written. A goal with no state folder gets one."""
    if phase not in PHASES:
        raise ValueError(f"No phase {phase!r}")
    ideas.save_state(state_dir, slug, state=first(phase), phase_written=phase, error="")


# -- a question laid outside (A.5) -------------------------------------------------------------------------------------------------

def outside_cards(page: Page | None) -> list[dict]:
    """The cards of a page that asks the person (`asks: person`): a line of *Open questions* with no answer under it, as Talk's questions are (`idea_questions.card`, `by` the page's `by`),
    its id `page-<n>`, n the question's place among the section's questions. A question with no choices is no card (the hand's cards have two to four), and a card with no recommended
    choice takes the first."""
    if page is None or page.get("asks") != PERSON:
        return []
    by = page.get("by") or PERSON
    out = []
    for n, q in idea_questions.open_of(page.section("Open questions")):
        got = idea_questions.parse(q)
        if not got["choices"]:
            continue
        card = idea_questions.card({"q": got["ask"], "choices": got["choices"], "pick": got["pick"] if got["pick"] is not None else 0, "why": got["why"], "lines": got.get("lines")},
                                   id=f"{OUTSIDE_ID}{n}", by=by, leader="")
        if card:
            out.append(card)
    return out


def outside_rows(page: Page | None) -> list[dict]:
    """The hand's row for those cards, the shape of Talk's own (`board_map.talk_rows`): `[{kind: "talk", round: 1, stances: [], questions: [card], text, outside: True}]`, none for no card."""
    cards = outside_cards(page)
    return [{"kind": "talk", "round": 1, "stances": [], "questions": cards, "text": cards[0]["q"], "outside": True}] if cards else []
