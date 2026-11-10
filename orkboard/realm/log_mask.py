"""A secret's value masked in a task's log before the log leaves the host (docs/specs/168 I1, decisions §283.16.9).

`mask(text, values)` is pure: it hides every value in `values` wherever it stands in `text`: in plain words, percent-encoded
in a URL (`%` escapes, and `+` for a space) and escaped as a JSON string says it (`\\"`, `\\n`, `\\u00e9`). A value shorter than
`MIN` letters, or empty, is never masked (it would eat the words around it); the longest value goes first, so a value that holds
another is hidden whole. `known(...)` reads the values a goal's task could print: the goal's `secret` to-dos (the keychain's
`orkcraft-ideas`, or `secrets.json`), the project's `.env` files and the host's own variables that are named like a secret. It
reads values and never keeps, logs or shows them.

    mask("curl https://x.io/?key=sk%2Dabc123", ["sk-abc123"])  # → "curl https://x.io/?key=••••"

No face, no model, no bus.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import quote, quote_plus

MASK = "••••"
MIN = 4                                           # a value of fewer letters would mask words that are not it
NAMED = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|PASSWD|PASS|CREDENTIAL|AUTH|COOKIE|PRIVATE)", re.I)
DOTENV = (".env", ".env.local", ".env.development", ".env.production", ".env.test")
_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
_ESCAPE = re.compile(r"%[0-9A-F]{2}")
_KEPT_OUT = {"ORKCRAFT_ORC", "ORKCRAFT_IDEA", "ORKCRAFT_TASK"}


def forms(value: str) -> list[str]:
    """The ways a value may stand in a log: as it is, percent-encoded (`%20` and `+`; escapes in upper or lower case) and escaped for a JSON string (ASCII or not), longest first."""
    out = {value, quote(value, safe=""), quote_plus(value), quote(value, safe="-_.~"), json.dumps(value)[1:-1], json.dumps(value, ensure_ascii=False)[1:-1]}
    out.update(_ESCAPE.sub(lambda m: m.group(0).lower(), f) for f in list(out) if "%" in f)
    return sorted((f for f in out if len(f) >= MIN), key=len, reverse=True)


def usable(values) -> list[str]:
    """The values worth hiding: texts of `MIN` letters or more, each once, the longest first."""
    return sorted({v for v in values if isinstance(v, str) and len(v) >= MIN and v.strip()}, key=len, reverse=True)


def mask(text: str, values, mask: str = MASK) -> str:
    """`text` with every form of every value in `values` replaced by `mask`."""
    text = str(text or "")
    for value in usable(values):
        for form in forms(value):
            if form in text:
                text = text.replace(form, mask)
    return text


def dotenv_values(text: str) -> list[str]:
    """The values of a `.env` file's lines (`NAME=value`, quotes taken off) whose name looks like a secret's."""
    out = []
    for line in str(text or "").splitlines():
        m = _LINE.match(line)
        if m and NAMED.search(m.group(1)):
            v = m.group(2)
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            elif " #" in v:
                v = v.split(" #", 1)[0].rstrip()
            out.append(v)
    return out


def environ_values(environ) -> list[str]:
    """The values of the variables named like a secret (a key, a token, a password…) in an environment mapping."""
    return [v for k, v in dict(environ).items() if k not in _KEPT_OUT and NAMED.search(str(k)) and isinstance(v, str)]


def known(state_dir: Path, repo_root: Path, slug: str, plan: dict | None, environ=None) -> list[str]:
    """Every value a task of the goal could print: its secret to-dos' values, the project's `.env` files and the host's own secret-named variables."""
    from orkboard.realm.idea_git import read_secret
    found: list[str] = []
    for todo in (plan or {}).get("todos") or []:
        if isinstance(todo, dict) and todo.get("kind") == "secret":
            try:
                value = read_secret(Path(state_dir), slug, str(todo.get("id") or ""))
            except Exception:
                value = None
            if value:
                found.append(value)
    for name in DOTENV:
        try:
            found += dotenv_values((Path(repo_root) / name).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    found += environ_values(os.environ if environ is None else environ)
    return usable(found)
