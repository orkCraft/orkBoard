"""The project's own hypotheses file (docs/specs/133-a-hypothesis-its-two-conditions-its-test-its-file.md part C; decisions §235.6): a Markdown file of numbered hypotheses, read into items and
written back by changing only the lines a change touches. Pure: text in, text out; no git, no state, no model, no face.

    hypotheses_file.find(root, chosen="")        # the file's path from the root: the chosen one, else docs/hypotheses.md, each only when it is a regular file inside the root; None
    hypotheses_file.parse(text)                  # {items: [file item], skipped: [n]}; a section with no *Holds when* is skipped, never made up
    hypotheses_file.apply(old, items, drop=())   # (new text, {item id: id it got}): `items` (the record's, not the proposed) written into `old`; a section nobody changed is returned byte for byte

A section is `## H<n>. <title>` up to the next `## ` heading; its id is `h<n>` and its text the title (the belief in one line), cut to 200. Inside it (`### ` blocks, any other line kept as written):

    **Status:** <word>[; <note>]. **Raised:** …                  # held · refuted, anything else open ("testing" is read from the goals' places, not kept here)
    ### What would prove it, what would refute it
    - **Holds** when <line>   |   - **Proves:** <line>           # the first one is the signal (*Holds when*); a continuation line is indented
    - **Refuted, <name>**: <line>  |  - **Refuted** when <line>  |  - **Refutes:** <line>      # a way, three at most, `name` "" without one
    ### If it holds                                              # its first paragraph is `if_holds`
    ### If it is refuted, <name>                                 # that way's `change`
    ### How we test it
    - Measure: <what> — from <source>[ (by <party>)] — holds <op> <n>[ <unit>][, refuted <way> <op> <n>[ <unit>]] — <N> weeks | <N> days | until <YYYY-MM-DD>   # a measure (spec 133 C.2); only a line of exactly this
                                                                 # shape names one, any other line is kept as written; its value is never written; `from -` says no source
    ### Evidence                                                 # `- <text> (<ref>) — <day>`, the newest twelve (written by Orkboard)
    ### Verdict                                                  # `<held|refuted>: <why> (decision §<n>, <way>) — <day>` (written by Orkboard)

A file item is `{id, n, text, signal, refuted, if_holds, measures, raised, state, evidence, verdict}` (`raised` the Status line's day, "" with none) with the record's shapes. Words are cut as the record cuts them; nothing is invented. `apply` changes a part only when the
item's value differs from what the section parses to (so a long line the record cut is never rewritten short), appends an item that has no section as `## H<n+1>.` (and says the id it got), and removes a
section only when its id is in `drop`.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from orkboard.realm import hypotheses as hyp, hypothesis_measures as hm

DEFAULT = "docs/hypotheses.md"
HEAD = "# Hypotheses\n\nWhat we believe and have not yet shown.\n"
EVIDENCE_KEPT = hyp.EVIDENCE
_SECTION = re.compile(r"^## H(\d+)\.[ \t]*(.*?)[ \t]*$")
_BLOCK = re.compile(r"^###[ \t]+(.*?)[ \t]*$")
_STATUS = re.compile(r"^\*\*Status:\*\*[ \t]*(.*?)(?:[ \t]*(\*\*Raised:\*\*.*))?$")
_HOLDS = re.compile(r"^- \*\*(?:Holds|Proves)\b[^*]*\*\*:?[ \t]*(?:when\b,?[ \t]*)?(.*)$")
_WAY = re.compile(r"^- \*\*(?:Refuted|Refutes)(?:,[ \t]*([^*:]+?))?[ \t]*:?\*\*:?[ \t]*(?:when\b,?[ \t]*)?(.*)$")
_EVIDENCE = re.compile(r"^- (.*?)(?: \(([^()]*)\))? — (\d{4}-\d\d-\d\d)$")
_VERDICT = re.compile(r"^(held|refuted):[ \t]*(.*?)(?:[ \t]*\(decision §(\d+)(?:,[ \t]*([^)]*))?\))?(?:[ \t]*— (\d{4}-\d\d-\d\d))?[ \t]*$")
_DECISION = re.compile(r"§(\d+)")
_MEASURE = re.compile(r"^- Measure:[ \t]*(.+)$")
_FROM = re.compile(r"^from[ \t]+(.+?)(?:[ \t]+\(by ([a-z0-9-]+)\))?$")
_BAR = re.compile(r"^(>=|<=|>|<|=|≥|≤)[ \t]*(-?\d+(?:\.\d+)?)(?:[ \t]+(.+))?$")
_WAYBAR = re.compile(r"^(.*?)[ \t]*(>=|<=|>|<|=|≥|≤)[ \t]*(-?\d+(?:\.\d+)?)(?:[ \t]+(.+))?$")
_SPAN = re.compile(r"^(?:(\d{1,3})[ \t]+(weeks?|days?)|until[ \t]+(\d{4}-\d\d-\d\d))$")
_OP = {"≥": ">=", "≤": "<="}
_RAISED = re.compile(r"\*\*Raised:\*\*[ \t]*(\d{4}-\d\d-\d\d)")


def find(root, chosen: str = "") -> str | None:
    """The path (from `root`, with `/`) of the project's hypotheses file: `chosen` when it is a regular file inside the root, else `docs/hypotheses.md` when it is one; None. Never a link, never outside."""
    base = Path(root)
    for rel in [r for r in (str(chosen or "").strip(), DEFAULT) if r]:
        try:
            real, cand = base.resolve(), (base / rel).resolve()
            if cand != real and cand.is_relative_to(real) and (base / rel).is_file() and not (base / rel).is_symlink() and not cand.is_symlink():
                return cand.relative_to(real).as_posix()
        except (OSError, ValueError, RuntimeError):
            continue
    return None


# -- the text in sections and blocks ----------------------------------------------------------------------------------------------------------

def _chunks(text: str) -> list[tuple[str, list[str]]]:
    """The file in order: `("pre", lines)` for what lies before a section or between sections (a `## ` heading that is none of ours starts one), `("sec", lines)` for each `## H<n>.` section. A line
    between ``` fences is never a heading. Joined back with "\\n" the chunks are the text."""
    out: list[tuple[str, list[str]]] = []
    fenced = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        starts = not fenced and line.startswith("## ")
        if starts and _SECTION.match(line):
            out.append(("sec", [line]))
        elif starts or not out:
            out.append(("pre", [line]))
        else:
            out[-1][1].append(line)
    return out


def _blocks(lines: list[str]) -> list[tuple[str, int, int]]:
    """The `### ` blocks of a section: `(lower-cased name, heading's index, end index)`; the end is the next heading's index (or the section's end)."""
    heads, fenced = [], False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced and (m := _BLOCK.match(line)):
            heads.append((m.group(1).strip().lower(), i))
    return [(name, i, heads[k + 1][1] if k + 1 < len(heads) else len(lines)) for k, (name, i) in enumerate(heads)]


def _bullets(lines: list[str]) -> list[tuple[int, int, str]]:
    """The `- ` bullets of a stretch of lines: `(first index, end index, the line with its indented continuation lines joined by spaces)`."""
    out: list[tuple[int, int, str]] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("- "):
            j = i + 1
            while j < len(lines) and lines[j].strip() and lines[j][:1] in " \t":
                j += 1
            out.append((i, j, " ".join([lines[i].rstrip(), *(ln.strip() for ln in lines[i + 1:j])])))
            i = j
        else:
            i += 1
    return out


def _paragraph(lines: list[str], n: int) -> str:
    """The first paragraph of a body (its lines joined by spaces), cut to `n`."""
    out: list[str] = []
    for line in lines:
        if not line.strip():
            if out:
                break
            continue
        out.append(line.strip())
    return hyp._words(" ".join(out), n)


def _find_block(lines: list[str], *needles: str, startswith: str = "") -> tuple[str, int, int] | None:
    for name, a, b in _blocks(lines):
        if (startswith and name.startswith(startswith)) or (needles and all(n in name for n in needles)):
            return name, a, b
    return None


# -- a measure's line ------------------------------------------------------------------------------------------------------------------------

def _num(n: float) -> str:
    return str(int(n)) if n == int(n) else repr(n)


def _plain(text: object) -> str:
    """A word of a measure as its line can hold it: one line, no ` — `."""
    return " ".join(str(text or "").replace(" — ", " - ").split())


def _bar_of(op: str, n: str, unit: str | None) -> dict:
    return {"op": _OP.get(op, op), "n": float(n), "unit": " ".join((unit or "").split())}


def _parse_measure(text: str) -> tuple[dict, str] | None:
    """One `- Measure:` line as `(a raw measure, "span" | "until")`, or None for a line of another shape."""
    m = _MEASURE.match(text.strip())
    parts = m.group(1).split(" — ") if m else []
    if len(parts) != 4 or not parts[0].strip():
        return None
    src = _FROM.match(parts[1].strip())
    span = _SPAN.match(parts[3].strip())
    if not src or not span:
        return None
    holds, ways = None, []
    segs = re.split(r"(?:^|,[ \t]+)(holds|refuted)[ \t]+", parts[2].strip())
    if len(segs) < 3 or segs[0] != "":
        return None
    for kind, body in zip(segs[1::2], segs[2::2]):
        if kind == "holds":
            b = _BAR.match(body.strip())
            if not b or holds is not None:
                return None
            holds = _bar_of(*b.groups())
        else:
            b = _WAYBAR.match(body.strip())
            if not b:
                return None
            ways.append({"way": " ".join(b.group(1).split()), **_bar_of(*b.groups()[1:])})
    days = int(span.group(1)) * (7 if span.group(2).startswith("week") else 1) if span.group(1) else 0
    raw = {"what": parts[0].strip(), "from": "" if src.group(1).strip() == "-" else src.group(1).strip(), "by": src.group(2) or "", "bars": {"holds": holds, "refuted": ways},
           "span_days": days or hm.SPAN_DEFAULT, "date": span.group(3) or ""}
    return raw, "until" if span.group(3) else "span"


def _measure_spots(lines: list[str]) -> list[tuple[int, int, dict, str]]:
    """The measure lines of *How we test it*: `(first index, end index, raw measure, form)`, four at most."""
    block = _find_block(lines, startswith="how we test")
    if not block:
        return []
    out = []
    for i, j, text in _bullets(lines[block[1] + 1:block[2]]):
        if (got := _parse_measure(text)) and len(out) < hm.MAX_MEASURES:
            out.append((block[1] + 1 + i, block[1] + 1 + j, got[0], got[1]))
    return out


def _key(m: dict, form: str) -> tuple:
    bars = m["bars"]
    h = bars.get("holds")
    return (_plain(m["what"]), _plain(m["from"]), m.get("by") or "", (h["op"], float(h["n"]), _plain(h.get("unit"))) if h else None,
            tuple((_plain(w["way"]), w["op"], float(w["n"]), _plain(w.get("unit"))) for w in bars.get("refuted") or []), m["date"] if form == "until" else m["span_days"])


def _form(m: dict, started: str) -> str:
    """How an item's measure is written: as its span when its date is that span from `started`, else as the day."""
    return "until" if m.get("date") and not (started and m["date"] == hm.date_of(started, m["span_days"])) else "span"


def _measure_line(m: dict, started: str) -> str:
    def bar(b: dict) -> str:
        return f"{b['op']} {_num(float(b['n']))}" + (f" {_plain(b['unit'])}" if _plain(b.get("unit")) else "")
    bars = ([f"holds {bar(m['bars']['holds'])}"] if m["bars"].get("holds") else []) + [f"refuted {(_plain(w['way']) + ' ') if _plain(w['way']) else ''}{bar(w)}" for w in m["bars"].get("refuted") or []]
    span = f"until {m['date']}" if _form(m, started) == "until" else (f"{m['span_days'] // 7} weeks" if m["span_days"] % 7 == 0 else f"{m['span_days']} days")
    return f"- Measure: {_plain(m['what'])} — from {_plain(m['from']) or '-'}{' (by ' + m['by'] + ')' if m.get('by') else ''} — {', '.join(bars)} — {span}"


# -- one section parsed -----------------------------------------------------------------------------------------------------------------------

def _status(lines: list[str]) -> tuple[int, str, str, str]:
    """`(line index or -1, word, note, the Raised part)` of the Status line."""
    for i, line in enumerate(lines):
        if m := _STATUS.match(line):
            body = m.group(1).strip()
            word = (re.match(r"[A-Za-z]+", body) or re.match(r"", body)).group(0).lower()
            return i, word, body[len(word):].lstrip(" ;.,").rstrip(" ."), m.group(2) or ""
    return -1, "", "", ""


def _section(lines: list[str]) -> dict | None:
    """One section as an item (see the module), or None for a section with no *Holds when*."""
    m = _SECTION.match(lines[0])
    n = int(m.group(1))
    block = _find_block(lines, "prove") or _find_block(lines, "refute")
    holds, ways = "", []
    if block:
        _name, a, b = block
        for _i, _j, text in _bullets(lines[a + 1:b]):
            if h := _HOLDS.match(text):
                holds = holds or hyp._cut(" ".join(h.group(1).split()), hyp.TEXT_CHARS)
            elif w := _WAY.match(text):
                way = {"name": hyp._words(w.group(1) or "", hyp.NAME_CHARS), "when": hyp._cut(" ".join(w.group(2).split()), hyp.TEXT_CHARS), "change": ""}
                if way["when"] and (not way["name"] or way["name"].lower() not in {x["name"].lower() for x in ways}) and len(ways) < hyp.MAX_WAYS:
                    ways.append(way)
    if not holds:
        return None
    for way in ways:
        got = _find_block(lines, startswith=f"if it is refuted, {way['name'].lower()}") if way["name"] else None
        if got:
            way["change"] = _paragraph(lines[got[1] + 1:got[2]], hyp.DRAFT_CHARS)
    got = _find_block(lines, startswith="if it holds")
    _i, word, note, raised = _status(lines)
    state = word if word in hyp.JUDGED else "open"
    evidence = []
    if block := _find_block(lines, startswith="evidence"):
        for _i, _j, text in _bullets(lines[block[1] + 1:block[2]]):
            if e := _EVIDENCE.match(text):
                evidence.append({"text": hyp._words(e.group(1), hyp.TEXT_CHARS), "ref": hyp._words(e.group(2) or "", 80), "at": e.group(3)})
            elif text[2:].strip():
                evidence.append({"text": hyp._words(text[2:], hyp.TEXT_CHARS), "ref": "", "at": ""})
    verdict: dict = {}
    if state in hyp.JUDGED:
        verdict = {"state": state, "why": "", "decision": int(d.group(1)) if (d := _DECISION.search(note)) else 0, "way": "", "at": ""}
        if block := _find_block(lines, startswith="verdict"):
            body = next((ln.strip() for ln in lines[block[1] + 1:block[2]] if ln.strip()), "")
            if v := _VERDICT.match(body):
                verdict = {"state": v.group(1), "why": hyp._words(v.group(2), hyp.TEXT_CHARS), "decision": int(v.group(3) or 0), "way": hyp._words(v.group(4) or "", hyp.NAME_CHARS), "at": v.group(5) or ""}
                state = v.group(1)
    return {"id": f"h{n}", "n": n, "text": hyp._cut(" ".join(m.group(2).split()), hyp.TEXT_CHARS) or f"Hypothesis {n}", "signal": holds, "refuted": ways,
            "if_holds": _paragraph(lines[got[1] + 1:got[2]], hyp.DRAFT_CHARS) if got else "",
            "measures": hm.lenient([raw for _a, _b, raw, _f in _measure_spots(lines)]), "raised": (r.group(1) if (r := _RAISED.search(raised)) else ""), "state": state, "evidence": evidence[-EVIDENCE_KEPT:], "verdict": verdict}


def parse(text: str) -> dict:
    """The file read: `{items: [file item], skipped: [n]}`, in the file's order; a number twice is read once (the first)."""
    items, skipped, seen = [], [], set()
    for kind, lines in _chunks(text):
        if kind != "sec":
            continue
        n = int(_SECTION.match(lines[0]).group(1))
        if n in seen:
            continue
        seen.add(n)
        got = _section(lines)
        if got is None:
            skipped.append(n)
        else:
            items.append(got)
    return {"items": items, "skipped": skipped}


# -- one section written ----------------------------------------------------------------------------------------------------------------------

def _way_line(way: dict) -> str:
    return f"- **Refuted, {way['name']}**: {way['when']}" if way["name"] else f"- **Refuted** when {way['when']}"


def _set_block(lines: list[str], found: tuple[str, int, int] | None, heading: str, body: list[str]) -> None:
    """The block `found` (or, with none, a new one before `### Evidence` / `### Verdict` or at the section's end) given `heading` and `body` (blank lines around it); `body` empty removes the block."""
    if found:
        _name, a, b = found
        rest = lines[b:]
        lines[a:] = ([heading, "", *body, ""] if body else []) + rest
        return
    if not body:
        return
    cut = next((a for name, a, _b in _blocks(lines) if name.startswith(("evidence", "verdict"))), None)
    if cut is None:
        cut = len(lines)
        while cut > 1 and not lines[cut - 1].strip():
            cut -= 1
        lines[cut:cut] = ["", heading, "", *body]
        if lines[-1].strip():
            lines.append("")
    else:
        lines[cut:cut] = [heading, "", *body, ""]


def _update(lines: list[str], item: dict) -> None:
    """The lines of one parseable section changed to say `item`, in place: only the parts whose parsed value differs."""
    cur = _section(lines)
    assert cur is not None
    n = int(_SECTION.match(lines[0]).group(1))
    if item["text"] != cur["text"]:
        lines[0] = f"## H{n}. {item['text']}"
    state = "open" if item["state"] in ("waiting", "proposed", "testing") else item["state"]
    if state != cur["state"]:
        i, _word, _note, raised = _status(lines)
        verdict = item.get("verdict") or {}
        note = (f"; became decision §{verdict['decision']}" if verdict.get("decision") else "") if state == "held" else (f"; {verdict['why']}" if verdict.get("why") else "") if state == "refuted" else ""
        line = f"**Status:** {state}{note}." + (f" {raised}" if raised else "")
        if i >= 0:
            lines[i] = line
        else:
            lines[1:1] = ["", line]
    if item["signal"] != cur["signal"]:
        _, a, b = _find_block(lines, "prove") or _find_block(lines, "refute")
        first, stop, _text = next(x for x in _bullets(lines[a + 1:b]) if _HOLDS.match(x[2]))
        lines[a + 1 + first:a + 1 + stop] = [f"- **Holds** when {item['signal']}"]
    if [(w["name"], w["when"]) for w in item["refuted"]] != [(w["name"], w["when"]) for w in cur["refuted"]]:
        _, a, b = _find_block(lines, "prove") or _find_block(lines, "refute")
        for first, stop, text in reversed(_bullets(lines[a + 1:b])):               # every way's bullet taken out …
            if _WAY.match(text):
                del lines[a + 1 + first:a + 1 + stop]
        _, a, b = _find_block(lines, "prove") or _find_block(lines, "refute")
        _first, stop, _text = next(x for x in _bullets(lines[a + 1:b]) if _HOLDS.match(x[2]))
        lines[a + 1 + stop:a + 1 + stop] = [_way_line(w) for w in item["refuted"]]      # … and the item's follow the Holds
    cur = _section(lines)
    for w in item["refuted"]:
        have = next((c for c in cur["refuted"] if c["name"].lower() == w["name"].lower()), None)
        if w["name"] and (have or {"change": ""})["change"] != w["change"]:
            heading = f"### If it is refuted, {w['name']}"
            _set_block(lines, _find_block(lines, startswith=f"if it is refuted, {w['name'].lower()}"), heading, [w["change"]] if w["change"] else [])
    spots = _measure_spots(lines)
    started = item.get("started") or ""
    want = [_key(m, _form(m, started)) for m in item.get("measures") or []]
    have = [_key(raw, form) for _a, _b, raw, form in spots]
    if want != have:
        new = [_measure_line(m, started) for m in item.get("measures") or []]
        if len(want) == len(have):                                                    # the same count: only the lines that differ are written again
            for k in reversed(range(len(want))):
                if want[k] != have[k]:
                    lines[spots[k][0]:spots[k][1]] = [new[k]]
        elif spots:
            at = spots[0][0]
            for a, b, _raw, _f in reversed(spots):
                del lines[a:b]
            lines[at:at] = new
        elif block := _find_block(lines, startswith="how we test"):
            end = block[2]
            while end > block[1] + 1 and not lines[end - 1].strip():
                end -= 1
            lines[end:end] = new
            if new and end + len(new) < len(lines) and lines[end + len(new)].strip():
                lines.insert(end + len(new), "")
        else:
            _set_block(lines, None, "### How we test it", new)
    if item["if_holds"] != cur["if_holds"]:
        _set_block(lines, _find_block(lines, startswith="if it holds"), "### If it holds", [item["if_holds"]] if item["if_holds"] else [])
    if [(e["text"], e["ref"]) for e in item["evidence"]] != [(e["text"], e["ref"]) for e in cur["evidence"]]:
        body = [f"- {e['text']}" + (f" ({e['ref']})" if e["ref"] else "") + f" — {(e.get('at') or '')[:10] or dt.date.today().isoformat()}" for e in item["evidence"][-EVIDENCE_KEPT:]]
        _set_block(lines, _find_block(lines, startswith="evidence"), "### Evidence", body)
    verdict = item.get("verdict") or {}
    if state in hyp.JUDGED and verdict and (verdict.get("why"), verdict.get("decision"), verdict.get("way")) != (cur["verdict"].get("why"), cur["verdict"].get("decision"), cur["verdict"].get("way")):
        line = f"{state}: {verdict.get('why') or ''}".rstrip()
        if verdict.get("decision") or verdict.get("way"):
            line += " (" + ", ".join(p for p in (f"decision §{verdict['decision']}" if verdict.get("decision") else "", verdict.get("way") or "") if p) + ")"
        line += f" — {(verdict.get('at') or '')[:10] or dt.date.today().isoformat()}"
        _set_block(lines, _find_block(lines, startswith="verdict"), "### Verdict", [line])


def _skeleton(n: int, item: dict) -> list[str]:
    return [f"## H{n}. {item['text']}", "", f"**Status:** open. **Raised:** {dt.date.today().isoformat()}.", "", "### What would prove it, what would refute it", "",
            f"- **Holds** when {item['signal']}", ""]


def apply(old: str, items: list[dict], drop=()) -> tuple[str, dict]:
    """`old` with the record's `items` written into it (see the module): `(new text, {the id an item had: the id it got})` for the items that had no section."""
    chunks = _chunks(old)
    by_id = {i["id"]: i for i in items if i.get("state") != "proposed"}
    renames: dict[str, str] = {}
    out: list[list[str]] = []
    have: set[int] = set()
    for kind, lines in chunks:
        if kind != "sec":
            out.append(lines)
            continue
        n = int(_SECTION.match(lines[0]).group(1))
        have.add(n)
        id_ = f"h{n}"
        if id_ in drop:
            continue
        lines = list(lines)
        if id_ in by_id and _section(lines) is not None:
            _update(lines, by_id[id_])
        out.append(lines)
    news = [i for i in items if i.get("state") != "proposed" and not (re.fullmatch(r"h\d+", i["id"]) and int(i["id"][1:]) in have)]
    top = max(have, default=0)
    text = "\n".join("\n".join(lines) for lines in out) if chunks else ""
    for item in news:
        top += 1
        lines = _skeleton(top, item)
        _update(lines, {**item, "state": item["state"]})
        renames[item["id"]] = f"h{top}"
        text = (text.rstrip("\n") + "\n\n" if text.strip() else HEAD + "\n") + "\n".join(lines).rstrip("\n") + "\n"
    return text, renames
