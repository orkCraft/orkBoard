"""A question the Taskmaster asks of an idea or a goal (docs/specs/41-phone-round-3.md §9): what it asks, its choices,
the one it recommends and why — taken strictly from the model's answer, kept in the page as one line, read back.

    q = idea_questions.of({"ask": "Which store first?", "choices": ["App Store", "Google Play"], "pick": 0,
                           "why": "most of its users are on iPhone"})
    idea_questions.all_of(answer["questions"], 3)       # the model's questions, each taken by `of`
    idea_questions.line(q)       # "Which store first? (**App Store** / Google Play) — most of its users are on iPhone"
    idea_questions.parse(line)   # {"ask", "choices", "pick", "why"}; a line of before ("… (one / other)") too
    idea_questions.picks(lines)  # each question's recommended choice ("" where it has none): Let the Taskmaster decide
    idea_questions.tally(lines, answers)   # how the person answered: picked, recommended, typed
    idea_questions.card(raw, id=, by=, leader=, project=)   # a leader's question as a hand's card (spec 99 §5.2): {id, by, leader, q, choices, pick, why, project}
    idea_questions.record(state_dir, slug) / save_record(…)  # what a goal's Talk keeps beside its state (talk.json: the cards waiting, the answers, the defaults, the cause)

The page is the memory: the line says the pick too (in bold), so the person reading the page sees it. No face, no model.
"""
from __future__ import annotations

import re

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
    return {"id": str(id), "by": str(by), "leader": str(leader), "q": q, "choices": choices, "pick": pick,
            "why": _plain(raw.get("why"), WHY_CHARS), "project": bool(project)}


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
    """What a goal's Talk keeps (core/idea_talk.py): `{mode: "talk"|"bug", round, stances, waiting: [card], second: [party], answers, defaults, keys, cause}`,
    {} before it has begun. The talk itself is `talk.jsonl`; this is the state the rows and the decision read, never a model."""
    from orkboard.realm import ideas
    return ideas._json(ideas.state_folder(state_dir, slug) / TALK_FILE) or {}


def save_record(state_dir, slug: str, rec: dict) -> dict:
    """The Talk's record replaced whole (a caller that read it first holds `ideas.LOCK` for both)."""
    from orkboard.realm import ideas
    with ideas.LOCK:
        ideas._write_json(ideas.state_folder(state_dir, slug) / TALK_FILE, rec)
    return rec
