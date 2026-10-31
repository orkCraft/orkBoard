"""The preview command's output as Play keeps it (docs/specs/115-the-live-product-under-each-leaders-eyes.md §2.3): the last `KEEP` lines
with their time, colour codes out, a line that names a secret out, for a mark's *the server's last lines*.

    tail = Tail()                      # a list `core/idea_shot.py opened(tail=…)` feeds as it does any `tail`: its last lines, for a start that failed
    tail.lines                         # [(time, text)], the last KEEP (a wall-clock time, `time.time()`)
    tail.before(t, n=40)               # the texts of the last `n` lines at or before `t` (None: now), oldest first

`opened` hands over lines already without colour codes and without blank ones; `Tail` takes out the rest: a line is dropped whole when one of its
words is a file the Warder keeps from the orks (`hooks/warder.py` `is_secret`: `.env*`, keys, certificates, credentials) or looks like a token
(the prefixes `hooks/warder.py` knows: `sk-`, `ghp_`, `xoxb-`, `AKIA…`).
"""
from __future__ import annotations

import re
import threading
import time
from collections import deque

from orkboard.core import idea_shot
from orkboard.hooks.warder import is_secret

KEEP = 400                                          # the lines kept
WORD = re.compile(r"""[^\s'"`()\[\]<>,;=]+""")      # a line's words, to ask each whether it is a secret's name
TOKEN = re.compile(r"sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{8,}|xox[a-z]-[A-Za-z0-9-]{8,}|AKIA[A-Z0-9]{12,}")


def secret(text: str) -> bool:
    """Whether a line names a secret file or carries a token (it is then never kept)."""
    return bool(TOKEN.search(text)) or any(is_secret(word) for word in WORD.findall(text))


class Tail(list):
    """`opened`'s `tail` list, which also keeps every line with its time (the list itself is what a failed start shows, as before)."""

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self.lines: deque[tuple[float, str]] = deque(maxlen=KEEP)

    def append(self, text: str) -> None:
        super().append(text)
        plain = idea_shot.ANSI.sub("", text).rstrip()
        if plain.strip() and not secret(plain):
            with self._lock:
                self.lines.append((time.time(), plain))

    def before(self, t: float | None = None, n: int = 40) -> list[str]:
        """The last `n` lines kept at or before the time `t` (None: now), oldest first."""
        t = time.time() if t is None else t
        with self._lock:
            kept = [text for at, text in self.lines if at <= t]
        return kept[-n:] if n > 0 else []
