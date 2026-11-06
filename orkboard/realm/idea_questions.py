"""A question the Taskmaster asks of an idea or a goal (docs/specs/41-phone-round-3.md §9): what it asks, its choices,
the one it recommends and why — taken strictly from the model's answer, kept in the page as one line, read back.

    q = idea_questions.of({"ask": "Which store first?", "choices": ["App Store", "Google Play"], "pick": 0,
                           "why": "most of its users are on iPhone"})
    idea_questions.all_of(answer["questions"], 3)       # the model's questions, each taken by `of`
    idea_questions.line(q)       # "Which store first? (**App Store** / Google Play) — most of its users are on iPhone"
    idea_questions.parse(line)   # {"ask", "choices", "pick", "why"}; a line of before ("… (one / other)") too
    idea_questions.picks(lines)  # each question's recommended choice ("" where it has none): Let the Taskmaster decide
    idea_questions.tally(lines, answers)   # how the person answered: picked, recommended, typed
    idea_questions.card(raw, id=, by=, leader=, project=)   # a leader's question as a hand's card (spec 99 §5.2): {id, by, leader, q, choices, pick, why, project[, for]}; `for` (spec 128 D) only when it names a party
    idea_questions.answer_line(answer, day)   # "  - Answered: <answer> (the person, YYYY-MM-DD)": the line under a question of a page (spec 151 A.6)
    idea_questions.answers(lines)             # each question's answer in those lines, "" where it has none
    idea_questions.for_of(raw)   # whom a question is for: a party's slug, else "person"
    idea_questions.record(state_dir, slug) / save_record(…)  # what a goal's Talk keeps beside its state (talk.json: the cards waiting, the answers, the defaults, the cause)
    idea_questions.talk_of(state_dir, slug)                  # …read as data for the stances' *More*: {mode, round, done, heard, stances: [{…, questions: [..]}], cause}

The page is the memory: the line says the pick too (in bold), so the person reading the page sees it. No face, no model.
"""
from __future__ import annotations

import re

from orkboard.realm.idea_page import ANSWERED

ASK_CHARS = 300
CHOICES = (2, 4)                 # a question's choices: at least, at most
CHOICE_CHARS = 40
WHY_CHARS = 120

# "<ask> (<choice> / **<pick>** / …)<?.!> — <why>": the choices in the last brackets that hold a slash.
_LINE = re.compile(r"^(.*?)\s*\(([^()]*/[^()]*)\)\s*([?.!]?)\s*(?:[—–]\s*(.*))?$")
_BOLD = re.compile(r"^\*\*(.+)\*\*$")


def _plain(value: object, limit: int) -> str:
    text = " ".join(value.split()) if isinstance(value, str) else ""
    return text if len(text) <= limit else text[:limit - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def _choice_ok(c: str) -> bool:
    return 0 < len(c) <= CHOICE_CHARS and not set(c) & set("()/*")


def of(raw: object) -> dict | None:
    """A question from the model's answer, strictly: a dict {"ask", "choices", "pick", "why"} or a plain string (a
    model or a page of before). Choices that break the rules are dropped together (the ask stays, alone); `pick` is
    an index of them, else None. None for nothing to ask."""
    if isinstance(raw, str):
        q = parse(raw)
        return q if q["ask"] else None
    if not isinstance(raw, dict):
        return None
    ask = _plain(raw.get("ask"), ASK_CHARS)
    if not ask:
        return None
    choices = [" ".join(c.split()) for c in raw.get("choices") or [] if isinstance(c, str)] \
        if isinstance(raw.get("choices"), list) else []
    if not CHOICES[0] <= len(choices) <= CHOICES[1] or not all(_choice_ok(c) for c in choices) \
            or len({c.lower() for c in choices}) < len(choices):
        choices = []
    pick = raw.get("pick")
    if isinstance(pick, str):
        pick = next((n for n, c in enumerate(choices) if c.lower() == " ".join(pick.split()).lower()), None)
    pick = pick if isinstance(pick, int) and not isinstance(pick, bool) and 0 <= pick < len(choices) else None
    return {"ask": ask, "choices": choices, "pick": pick, "why": _plain(raw.get("why"), WHY_CHARS) if choices else ""}


def all_of(raw: object, limit: int) -> list[dict]:
    """The model's questions, each taken by `of`, at most `limit`."""
    return [q for q in (of(x) for x in raw) if q][:limit] if isinstance(raw, list) else []


def line(q: dict) -> str:
    """The page's line: the ask, its choices in brackets (the pick in bold), and why after a dash."""
    if not q.get("choices"):
        return q["ask"]
    said = " / ".join(f"**{c}**" if n == q.get("pick") else c for n, c in enumerate(q["choices"]))
    return f"{q['ask']} ({said})" + (f" — {q['why']}" if q.get("why") else "")


def parse(text: str) -> dict:
    """A page's line back into its question; a line with no valid choices is its ask alone."""
    text = " ".join(str(text or "").split())
    m = _LINE.match(text)
    if not m:
        return {"ask": text, "choices": [], "pick": None, "why": ""}
    raw = [c.strip() for c in m.group(2).split("/") if c.strip()]
    bold = [bool(_BOLD.match(c)) for c in raw]
    choices = [_BOLD.sub(r"\1", c).strip() for c in raw]
    if not CHOICES[0] <= len(choices) <= CHOICES[1] or not all(0 < len(c) <= CHOICE_CHARS for c in choices):
        return {"ask": text, "choices": [], "pick": None, "why": ""}
    ask = m.group(1).strip()
    if m.group(3) and not re.search(r"[?.!]$", ask):
        ask += m.group(3)
    return {"ask": ask, "choices": choices, "pick": bold.index(True) if sum(bold) == 1 else None,
            "why": (m.group(4) or "").strip()}


def picks(lines: list[str]) -> list[str]:
    """Each question's recommended choice, "" where it has none (Let the Taskmaster decide's answers)."""
    out = []
    for text in lines:
        q = parse(text)
        out.append(q["choices"][q["pick"]] if q["pick"] is not None else "")
    return out


def tally(lines: list[str], answers: list[str]) -> dict[str, int]:
    """How the person answered the questions, for the events: `picked` (one of its choices), `recommended` (its
    pick), `typed` (anything else written)."""
    out = {"picked": 0, "recommended": 0, "typed": 0}
    for n, text in enumerate(lines):
        said = " ".join(str(answers[n] if n < len(answers) else "").split())
        if not said:
            continue
        q = parse(text)
        hit = next((i for i, c in enumerate(q["choices"]) if c.lower() == said.lower()), None)
        if hit is None:
            out["typed"] += 1
            continue
        out["picked"] += 1
        out["recommended"] += hit == q["pick"]
    return out


# -- an answer's line under its question in a page (docs/specs/151 A.6) -------------------------------------------------------------------

ANSWER_CHARS = 2000
_ANSWER_TAIL = re.compile(r"^(.*)\s\([^()]*,\s*\d{4}-\d{2}-\d{2}\)$")


def answer_line(answer: str, day: str, who: str = "the person") -> str:
    """The line under a question that was answered: `  - Answered: <answer> (the person, 2026-11-06)`, the answer on one line."""
    said = " ".join(str(answer or "").split())[:ANSWER_CHARS]
    return f"  - Answered: {said} ({who}, {day})"


def _rows(lines: object) -> list[list]:
    """A section's lines as `[question line, its answer line or None]`, in order (a blank line is none; a second answer line is not kept)."""
    text = lines if isinstance(lines, str) else "\n".join(str(x) for x in lines or [])
    rows: list[list] = []
    for ln in text.split("\n"):
        if not ln.strip():
            continue
        if rows and ANSWERED.match(ln):
            rows[-1][1] = rows[-1][1] or ln
            continue
        rows.append([ln, None])
    return rows


def questions_of(lines: object) -> list[str]:
    """The questions of a section's lines (the list marker taken off), answered ones too, in order: the index of one is its `page-<n>` card's."""
    return [re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", q).strip() for q, _a in _rows(lines)]


def answers(lines: object) -> list[str]:
    """Each question's answer in a section's lines (a text, or its lines), "" where it has none; one for each question of `questions_of`."""
    out = []
    for _q, a in _rows(lines):
        said = ANSWERED.match(a).group(1) if a else ""
        tail = _ANSWER_TAIL.match(said)
        out.append((tail.group(1) if tail else said).strip())
    return out


def with_answer(lines: object, ask: str | int, answer: str, day: str, who: str = "the person") -> str:
    """The section's text with the answer written under its question: `ask` is the question's index (`questions_of`), or its text (a question the page lacks is added as a list
    line at the end). An answer there already is replaced."""
    rows = _rows(lines)
    n = ask if isinstance(ask, int) else next((i for i, q in enumerate(questions_of(lines)) if parse(q)["ask"] == parse(str(ask))["ask"]), None)
    if n is None:
        rows.append([f"- {' '.join(str(ask).split())}", None])
        n = len(rows) - 1
    if not 0 <= n < len(rows):
        raise ValueError("That question is not in the page")
    rows[n][1] = answer_line(answer, day, who)
    return "\n".join(ln for row in rows for ln in row if ln)


def open_of(lines: object) -> list[tuple[int, str]]:
    """The questions with no answer yet, `(index, question)`."""
    return [(n, q) for n, (q, (_l, a)) in enumerate(zip(questions_of(lines), _rows(lines))) if not a]


# -- a question as a card (docs/specs/99-a-goals-way.md §5.2; decisions §153.5) -------------------------------------------------------

CARD_CHOICE_CHARS = 60           # a card's choice, at most: it holds what the project holds (a container, a path), which a page's line (CHOICE_CHARS) could not


def card(raw: object, *, id: str, by: str, leader: str, project: bool = False) -> dict | None:
    """A leader's question as the hand's card, taken strictly from its answer: `{id, by: party, leader, q, choices: [2..4], pick: index, why, project}`.
    Two to four real choices (`CHOICES`), never padded, each a different one; one picked for the person (an index of them, or the choice itself) with its why.
    Anything else (no question, a choice that is none, too few or too many, no pick) is not a card: None. *Other…* is the face's. `id`, `by` and `leader`
    are the caller's (code names them, never the model); `project` says the question is about the project, not the goal."""
    if not isinstance(raw, dict):
        return None
    q = _plain(raw.get("q") if raw.get("q") is not None else raw.get("ask"), ASK_CHARS)
    got = raw.get("choices")
    if not q or not isinstance(got, list) or not CHOICES[0] <= len(got) <= CHOICES[1]:
        return None
    choices = [" ".join(c.split()) if isinstance(c, str) else "" for c in got]
    if not all(0 < len(c) <= CARD_CHOICE_CHARS for c in choices) or len({c.lower() for c in choices}) < len(choices):
        return None
    pick = raw.get("pick")
    if isinstance(pick, str):
        pick = next((n for n, c in enumerate(choices) if c.lower() == " ".join(pick.split()).lower()), None)
    if not isinstance(pick, int) or isinstance(pick, bool) or not 0 <= pick < len(choices):
        return None
    out = {"id": str(id), "by": str(by), "leader": str(leader), "q": q, "choices": choices, "pick": pick,
           "why": _plain(raw.get("why"), WHY_CHARS), "project": bool(project)}
    if (to := for_of(raw)) != PERSON:
        out["for"] = to                                   # a party that may answer it (spec 128 D.1): kept only when it is one; no `for` is the person's
    return out


PERSON = "person"
_FOR = re.compile(r"[a-z0-9][a-z0-9_-]{0,59}")


def for_of(raw: object) -> str:
    """Whom a leader's question is for (spec 128 D.1), from the model's answer: a party's slug (a lowercase word of letters, digits, `-` and `_`), else `PERSON` (what only the person
    can choose, `""`, or anything that is none). Whether the party exists, and whether the question may be passed at all, is `realm/idea_pass.py`'s."""
    got = raw.get("for") if isinstance(raw, dict) else None
    got = got.strip().lower() if isinstance(got, str) else ""
    return got if got != PERSON and _FOR.fullmatch(got) else PERSON


def default_of(c: dict) -> str:
    """The answer a card takes when nobody answers it: its leader's pick."""
    return c["choices"][c["pick"]]


def answer_of(c: dict, said: object) -> tuple[str, str] | None:
    """A person's answer to a card, `{id, pick?|text?}` as the command has it, as `(text, how)`: `how` "text" (the words written, *Other…*: they win when both
    are given) or "pick" (one of its choices, by its index). None for no answer, or a pick that is none of the card's choices."""
    if not isinstance(said, dict):
        return None
    text = " ".join(said["text"].split())[:2000] if isinstance(said.get("text"), str) else ""
    if text:
        return text, "text"
    pick = said.get("pick")
    if isinstance(pick, int) and not isinstance(pick, bool) and 0 <= pick < len(c["choices"]):
        return c["choices"][pick], "pick"
    return None


# -- what a Talk keeps: <state_dir>/ideas/<slug>/talk.json ----------------------------------------------------------------------------

TALK_FILE = "talk.json"


def record(state_dir, slug: str) -> dict:
    """What a goal's Talk keeps (core/idea_talk.py): `{mode: "talk"|"bug", round, stances, heard: [party], waiting: [card], second: [party], again: [party], answers, defaults, keys, weight, cause}`,
    {} before it has begun. `heard`: the parties whose leader has answered, as each does (spec 120 §2.3); a stance is `{party, leader, craft, weigher, stance, for, against, verdict, why, instead,
    after, priority, risk}` (`priority` Product's, `risk` Tech's, `weigher` Product weighing a goal it is not routed on); `again`: the parties to hear again after the answers (spec 120 §3.2);
    `weight`: `{priority, risk}` (`realm/idea_ripe.py`). The talk itself is `talk.jsonl`; this is the state the rows and the decision read, never a model."""
    from orkboard.realm import ideas
    return ideas._json(ideas.state_folder(state_dir, slug) / TALK_FILE) or {}


def save_record(state_dir, slug: str, rec: dict) -> dict:
    """The Talk's record replaced whole (a caller that read it first holds `ideas.LOCK` for both)."""
    from orkboard.realm import ideas
    with ideas.LOCK:
        ideas._write_json(ideas.state_folder(state_dir, slug) / TALK_FILE, rec)
    return rec


def _asked(c: dict, state: str) -> dict:
    """A question as the Talk read says it: the card's `id`, `q`, `choices`, `pick`, `why`, `project`, its `state` ("waiting", "answered" or "closed": left to its leader's
    pick) and, once answered or closed, its `answer` and `round`; an answered one also its `how` ("pick", "text" or "decide")."""
    pick = c.get("pick")
    out = {"id": str(c.get("id") or ""), "q": str(c.get("q") or ""), "choices": [str(x) for x in c.get("choices") or []],
           "pick": pick if isinstance(pick, int) and not isinstance(pick, bool) else None, "why": str(c.get("why") or ""), "project": bool(c.get("project")), "state": state}
    if state != "waiting":
        out["answer"] = str(c.get("answer") or "")
        out["round"] = 2 if c.get("round") == 2 else 1
    if state == "answered":
        out["how"] = str(c.get("how") or "pick")
        if c.get("answered_by"):
            out["answered_by"] = str(c["answered_by"])      # a party's leader answered it for the person (spec 128 D.2)
    return out


def talk_of(state_dir, slug: str) -> dict:
    """A goal's Talk as it is kept, as data, never words: `{mode: "talk"|"bug"|"", round, done, heard: [party], stances: [{party, leader, weigher, stance, for, against, questions}], cause}`. Each
    stance holds its party's questions: those the person answered (`state` "answered": `answer`, `how`, `round`), those left to the leaders' picks ("closed": `answer`) and
    those waiting ("waiting"). `cause` is a bug's guess, `{text, where, by, pending, confirmed}`, None with none. A Talk not begun (or taken back) is `{mode: "", round: 1,
    done: false, stances: [], cause: None}`; a question of a party with no stance (a bug's) lies under a stance of its own with no words."""
    rec = record(state_dir, slug)
    asked: dict[str, list[dict]] = {}
    for key, state in (("answers", "answered"), ("defaults", "closed"), ("waiting", "waiting")):
        for c in rec.get(key) or []:
            if isinstance(c, dict):
                asked.setdefault(str(c.get("by") or ""), []).append(_asked(c, state))
    stances = [{"party": str(s.get("party") or ""), "leader": str(s.get("leader") or ""), "stance": str(s.get("stance") or ""), "for": str(s.get("for") or ""),
                "against": str(s.get("against") or ""), "weigher": bool(s.get("weigher"))} for s in rec.get("stances") or [] if isinstance(s, dict)]
    stances += [{"party": p, "leader": "", "stance": "", "for": "", "against": "", "weigher": False} for p in asked if p not in {s["party"] for s in stances}]
    for s in stances:
        s["questions"] = asked.get(s["party"], [])
    c = rec.get("cause") if isinstance(rec.get("cause"), dict) and rec.get("cause") else None
    cause = None if c is None else {"text": str(c.get("text") or ""), "where": [str(w) for w in c.get("where") or []], "by": str(c.get("by") or ""),
                                    "pending": bool(c.get("pending")), "confirmed": bool(c.get("confirmed"))}
    return {"mode": rec.get("mode") if rec.get("mode") in ("talk", "bug") else "", "round": 2 if rec.get("round") == 2 else 1, "done": bool(rec.get("done")),
            "heard": [str(p) for p in rec.get("heard") or [] if isinstance(p, str)], "stances": stances, "cause": cause}
