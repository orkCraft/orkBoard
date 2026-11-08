"""Pure question and answer formatting shared with the Board instructions. Existing providers re-export their original names."""
from orkboard.realm.seat_question_rules import LINE_CHARS

def _plain(value: object, limit: int) -> str:
    text = " ".join(value.split()) if isinstance(value, str) else ""
    return text if len(text) <= limit else text[:limit - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def _lines_of(raw: object, choices: list[str]) -> list[str]:
    """A question's way lines (spec 159): a list in the ways' order, or a dict by way; [] unless every way has one within `LINE_CHARS` that the page reads back whole."""
    if isinstance(raw, dict):
        low = {" ".join(str(k).split()).lower(): v for k, v in raw.items()}
        raw = [low.get(c.lower()) for c in choices]
    if not choices or not isinstance(raw, list) or len(raw) != len(choices):
        return []
    lines = [" ".join(x.split()) if isinstance(x, str) else "" for x in raw]
    if not all(0 < len(x) <= LINE_CHARS for x in lines) or _split(_tail(choices, lines), choices) != ("", lines):
        return []
    return lines


def _tail(choices: list[str], lines: list[str]) -> str:
    return "".join(f" · {c}: {x}" for c, x in zip(choices, lines))


def line(q: dict) -> str:
    """The page's line: the ask, its choices in brackets (the pick in bold), and why after a dash."""
    if not q.get("choices"):
        return q["ask"]
    said = " / ".join(f"**{c}**" if n == q.get("pick") else c for n, c in enumerate(q["choices"]))
    lines = _lines_of(q.get("lines"), q["choices"])
    why = f" — {q['why']}" if q.get("why") else " —" if lines else ""
    return f"{q['ask']} ({said})" + why + _tail(q["choices"], lines) if lines else f"{q['ask']} ({said})" + why


ANSWER_CHARS = 2000


def answer_line(answer: str, day: str, who: str = "the person") -> str:
    """The line under a question that was answered: `  - Answered: <answer> (the person, 2026-11-06)`, the answer on one line."""
    said = " ".join(str(answer or "").split())[:ANSWER_CHARS]
    return f"  - Answered: {said} ({who}, {day})"


def _split(why: str, choices: list[str]) -> tuple[str, list[str] | None]:
    """A why with its way lines at its end, `(the why alone, the lines)`; `(why, None)` where it has none (every way named, in order, or nothing)."""
    text = " " + why
    start = 0
    while (p := text.find(f" · {choices[0]}: ", start)) >= 0:
        out, at = [], p
        for n, c in enumerate(choices):
            head = f" · {c}: "
            if not text.startswith(head, at):
                break
            at += len(head)
            nxt = text.find(f" · {choices[n + 1]}: ", at) if n + 1 < len(choices) else len(text)
            if nxt < 0:
                break
            out.append(text[at:nxt].strip())
            at = nxt
        else:
            if all(0 < len(x) <= LINE_CHARS for x in out):
                return text[:p].strip(), out
        start = p + 1
    return why, None

