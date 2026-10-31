"""What the live product knew when a place on it was marked (docs/specs/115-the-live-product-under-each-leaders-eyes.md §5; decisions §193): a goal's **play**, kept beside it
(`<state_dir>/ideas/<slug>/play.json`) and read into its calls' prompts after the lens. No face, no model.

    save(state_dir, slug, play)                  # one mark kept (appended; the newest MAX_MARKS stay); the mark as kept, cleaned and bounded
    read(state_dir, slug)                        # [mark], oldest first; [] with none
    prompt_lines(state_dir, slug)                # for a keeper's prompt ("" with none): the errors, the failed requests and the server's lines first (Tech's), then the element and the state
    failed(state_dir, slug, kind="bug")          # a mark of that kind holds an error or a failed request: a bug's report that holds its failure (realm/goal_route.py `reproduces`)
    newest(state_dir, slugs, screen, kind, path) # the slug among `slugs` whose newest mark is on that screen (else that path) and of that kind, the latest first; "" with none
    scrub(text)                                  # a text with what looks like a secret masked (`***`)
    elements(raw)                                # the probe's elements under a box, cleaned

A mark, as `save` is given it and as `read` returns it:

    {kind: "bug" | "looks" | "missing" | "confusing", text, path, screen: {id, name} | None, box: {x, y, w, h} (shares 0..1), commit, at,
     under: [{selector, role, text, rect, file?, line?}] (three at most), errors: [{message, stack, source, count}] (ten), requests: [{method, path, status, ms, host?}] (ten),
     lines: [str] (the server's last 40), state: {…} | None (2 KB of JSON at most), picture: the id of the screen the lens keeps ("" with none)}

The file is `{"marks": [...]}`, several marks on one goal in a list, the oldest dropped after MAX_MARKS; a file of the first shape (the mark itself, flat) is read as one mark. **Secrets out:** a line
that names a secret file or carries a token is dropped whole (as gui/play_lines.py keeps the server's lines); any other text has the token masked, a file the Warder keeps from the orks
(`hooks/warder.py` `is_secret`) is not kept, and a state's key that names a secret (a password, a token, a key, a cookie, a session) keeps no value. Whatever the page sent, nothing else is kept.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from orkboard.hooks.warder import is_secret
from orkboard.realm import ideas

KINDS = ("bug", "looks", "missing", "confusing")
MAX_MARKS = 8                       # the marks one goal keeps
MAX_UNDER = 3                       # the elements under a box
MAX_ERRORS = 10
MAX_REQUESTS = 10
MAX_LINES = 40                      # the server's last lines
MAX_LINE = 300                      # the longest of one
MAX_STATE = 2048                    # a game's state as JSON, in bytes
MAX_PROMPT = 12_000                 # the most characters read into a prompt
TOKEN = re.compile(r"sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{8,}|xox[a-z]-[A-Za-z0-9-]{8,}|AKIA[A-Z0-9]{12,}")
WORD = re.compile(r"""[^\s'"`()\[\]<>,;=]+""")
SECRET_KEY = re.compile(r"pass(word|wd)?|secret|token|api[-_]?key|auth|cookie|session|credential|private", re.I)


def _words(v: object, n: int) -> str:
    return " ".join(str(v if v is not None else "").split())[:n]


def secret(text: str) -> bool:
    """Whether a line names a secret file or carries a token (it is then never kept)."""
    return bool(TOKEN.search(text)) or any(is_secret(word) for word in WORD.findall(text))


def scrub(text: object, n: int = 300) -> str:
    """A text on one line, at most `n` characters, a token masked and a secret file's name masked."""
    plain = _words(text, n * 2)
    plain = TOKEN.sub("***", plain)
    plain = WORD.sub(lambda m: "***" if is_secret(m.group(0)) else m.group(0), plain)
    return plain[:n]


def _num(v: object, default: float = 0.0) -> float:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else default


def _unit(v: object) -> float:
    return round(min(1.0, max(0.0, _num(v))), 4)


def _file(v: object) -> str:
    """A file the probe named, as given when it is not a secret's; "" otherwise."""
    text = _words(v, 300)
    return "" if not text or is_secret(text.split(":")[0]) or secret(text) else text


def _rect(v: object) -> dict | None:
    return {k: round(_num(v.get(k)), 1) for k in ("x", "y", "w", "h")} if isinstance(v, dict) else None


def elements(raw: object) -> list[dict]:
    """The elements under a box as the probe named them, bounded, secrets out: `[{selector, role, text, rect, file?, line?}]`, MAX_UNDER at most."""
    out = []
    for e in (raw if isinstance(raw, list) else [])[:MAX_UNDER]:
        if not isinstance(e, dict) or not _words(e.get("selector"), 300):
            continue
        row = {"selector": scrub(e.get("selector")), "role": scrub(e.get("role"), 40), "text": scrub(e.get("text"), 80), "rect": _rect(e.get("rect"))}
        if file := _file(e.get("file")):
            row["file"] = file
            if _num(e.get("line")) > 0:
                row["line"] = int(_num(e.get("line")))
        out.append(row)
    return out


def _errors(raw: object) -> list[dict]:
    out = []
    for e in (raw if isinstance(raw, list) else [])[-MAX_ERRORS:]:
        if isinstance(e, dict) and (msg := scrub(e.get("message"))):
            out.append({"message": msg, "stack": scrub(e.get("stack")), "source": scrub(e.get("source"), 20),
                        "count": max(1, int(_num(e.get("count"), 1)))})
    return out


def _requests(raw: object) -> list[dict]:
    out = []
    for r in (raw if isinstance(raw, list) else [])[-MAX_REQUESTS:]:
        if isinstance(r, dict) and _words(r.get("path"), 300):
            row = {"method": scrub(r.get("method") or "GET", 10).upper(), "path": scrub(r.get("path")), "status": int(_num(r.get("status"))), "ms": round(_num(r.get("ms")))}
            if host := scrub(r.get("host"), 100):
                row["host"] = host
            out.append(row)
    return out


def _lines(raw: object) -> list[str]:
    plain = [_words(x, MAX_LINE) for x in (raw if isinstance(raw, list) else []) if isinstance(x, str)]
    return [x for x in plain if x and not secret(x)][-MAX_LINES:]


def _clean_state(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(k)[:60]: ("***" if SECRET_KEY.search(str(k)) else _clean_state(x)) for k, x in list(v.items())[:60]}
    if isinstance(v, list):
        return [_clean_state(x) for x in v[:60]]
    return scrub(v, 200) if isinstance(v, str) else (v if isinstance(v, (int, float, bool)) or v is None else None)


def _state(raw: object) -> Any:
    """A game's state, secrets out, at most MAX_STATE bytes as JSON; None when there is none or it is larger."""
    if raw is None:
        return None
    got = _clean_state(raw)
    try:
        return got if len(json.dumps(got, ensure_ascii=False).encode("utf-8")) <= MAX_STATE else None
    except (TypeError, ValueError):
        return None


def clean(play: object) -> dict | None:
    """One mark as it is kept (see the module); None for what is no mark (no kind of the four)."""
    if not isinstance(play, dict) or play.get("kind") not in KINDS:
        return None
    here = play.get("screen") if isinstance(play.get("screen"), dict) else None
    box = play.get("box") if isinstance(play.get("box"), dict) else None
    return {"kind": play["kind"], "text": scrub(play.get("text"), 300), "path": _words(play.get("path"), 300) or "/",
            "screen": {"id": _words(here.get("id"), 80), "name": _words(here.get("name"), 120)} if here and _words(here.get("id"), 80) else None,
            "box": {k: _unit(box.get(k)) for k in ("x", "y", "w", "h")} if box else None,
            "commit": _words(play.get("commit"), 40), "at": _words(play.get("at"), 40),
            "under": elements(play.get("under")), "errors": _errors(play.get("errors")), "requests": _requests(play.get("requests")),
            "lines": _lines(play.get("lines")), "state": _state(play.get("state")), "picture": _words(play.get("picture"), 40)}


# -- the file --------------------------------------------------------------------------------------------------------------------------------

def _file_of(state_dir: Path, slug: str) -> Path:
    return ideas.state_folder(Path(state_dir), slug) / "play.json"


def read(state_dir: Path, slug: str) -> list[dict]:
    """The goal's marks, oldest first; [] with none (or a goal name that is none)."""
    try:
        got = ideas._json(_file_of(state_dir, slug)) or {}
    except ValueError:
        return []
    rows = got.get("marks") if isinstance(got.get("marks"), list) else ([got] if got.get("kind") else [])
    return [m for m in map(clean, rows) if m is not None]


def save(state_dir: Path, slug: str, play: dict) -> dict:
    """One mark kept after the goal's others (the newest MAX_MARKS stay); the mark as kept. ValueError for what is no mark."""
    mark = clean(play)
    if mark is None:
        raise ValueError("A mark is a bug, looks wrong, missing or confusing")
    with ideas.LOCK:
        marks = [*read(state_dir, slug), mark][-MAX_MARKS:]
        ideas._write_json(_file_of(state_dir, slug), {"marks": marks})
    return mark


def update(state_dir: Path, slug: str, index: int, **changes: object) -> None:
    """A kept mark changed (the one at `index` of `read`'s list), cleaned again."""
    with ideas.LOCK:
        marks = read(state_dir, slug)
        if -len(marks) <= index < len(marks):
            marks[index] = clean({**marks[index], **changes}) or marks[index]
            ideas._write_json(_file_of(state_dir, slug), {"marks": marks})


def failed(state_dir: Path, slug: str, kind: str = "bug") -> bool:
    """A kept mark of `kind` holds an error or a failed request (the failure of a bug's report)."""
    return any(m["kind"] == kind and (m["errors"] or m["requests"]) for m in read(state_dir, slug))


def newest(state_dir: Path, slugs: Iterable[str], screen: str, kind: str, path: str = "") -> str:
    """Among `slugs`, the goal whose latest mark of `kind` is on the screen `screen` (its id; with none, on the page `path` without its query) and was made last; "" when none is."""
    here = _words(path, 300).split("?")[0].split("#")[0]
    best, found = ("", -1), ""
    for n, slug in enumerate(slugs):
        for m in read(state_dir, slug):
            same = (m["screen"] or {}).get("id") == screen if screen else (not m["screen"] and m["path"].split("?")[0].split("#")[0] == here)
            if m["kind"] == kind and same and (m["at"], n) >= best:
                best, found = (m["at"], n), slug
    return found


# -- read into a prompt ----------------------------------------------------------------------------------------------------------------------

KIND_WORDS = {"bug": "a bug", "looks": "something that looks wrong", "missing": "something missing", "confusing": "something confusing"}


def _pct(v: float) -> str:
    return f"{round(v * 100)} %"


def _mark_lines(n: int, m: dict) -> list[str]:
    where = f"the page {m['path']}" + (f" (the screen \"{m['screen']['name']}\")" if m["screen"] and m["screen"].get("name") else "")
    head = f"- Mark {n}: {KIND_WORDS[m['kind']]} on {where}" + (f", at commit {m['commit'][:7]}" if m["commit"] else "")
    if m["box"] and not m["picture"]:                           # with a picture the lens says the box
        b = m["box"]
        head += f", the box from {_pct(b['x'])} to {_pct(b['x'] + b['w'])} across and {_pct(b['y'])} to {_pct(b['y'] + b['h'])} down"
    rows = [head + (f": {m['text']}" if m["text"] else "")]
    if m["errors"]:
        rows.append("  Errors the page threw, newest last:")
        rows += [f"    {e['message']}" + (f" (x{e['count']})" if e["count"] > 1 else "") + (f", at {e['stack']}" if e["stack"] else "") for e in m["errors"]]
    if m["requests"]:
        rows.append("  Requests that failed or were slow, newest last:")
        rows += [f"    {r['method']} {r['path']} {r['status'] or 'no answer'}, {r['ms']} ms" + (f", to {r['host']}" if r.get("host") else "") for r in m["requests"]]
    if m["lines"]:
        rows += ["  The server's last lines before the mark:", *[f"    {x}" for x in m["lines"]]]
    for e in m["under"]:
        at = f" in {e['file']}" + (f":{e['line']}" if e.get("line") else "") if e.get("file") else ""
        rows.append(f"  The element: {e['selector']}" + (f" ({e['role']})" if e["role"] else "") + (f" saying \"{e['text']}\"" if e["text"] else "") + at)
    if m["state"] is not None:
        rows.append(f"  The game's state: {json.dumps(m['state'], ensure_ascii=False)}")
    return rows


def prompt_lines(state_dir: Path, slug: str) -> str:
    """For a keeper's prompt: what the live product knew at each mark ("" with none), after the lens's lines."""
    marks = read(state_dir, slug)
    if not marks:
        return ""
    rows: list[str] = []
    for n, m in enumerate(marks, 1):
        rows += _mark_lines(n, m)
    text = "\n".join(rows)
    if len(text) > MAX_PROMPT:
        text = text[:MAX_PROMPT].rsplit("\n", 1)[0] + "\n  …"
    return "The person marked places on the running product (Play) and what it knew then comes with each mark; start from it:\n" + text + "\n"
