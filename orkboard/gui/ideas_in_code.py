"""The Orkmaster's question about the Board in the code (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md F.1, F.3; decisions §255.10), as `gui/ideas.py`'s `Ideas` has it.

    ideas.in_code_rows()        # [] or [{kind: "in_code", step, visibility, public, pages_in_history, title, text, ask, held, words, blocks, priority}] in the hand (a project's card, no goal's)
    ideas.in_code {answer}      # "publish" · "off" · "private": `[board] in_code` written, the Board's tree flushed at once so the pages land on the right side
                                #   {ok, answer, in_code, visibility}

**The card is the question while it is wanted** (`realm/board_in_code.py` `pending_question`: a public or unreadable remote, `in_code` not said), thrown by the Orkmaster as the conflict card is (decisions §254.6). `step`:
`private` for a remote Orkboard cannot read (*Is this repository private?*: **Private** writes the yes, **Public** goes on to the publish question, which the page asks without a call), `publish` for the question
itself (**Publish the Board** · **Keep the Board off the repository**). A repository found public since (the host's daily tick, `gui/board_in_code_host.py`) is the same question again, `held` saying that the
Board's pushes wait (`board_in_code.HELD`). The rows read the last look's word and ask the network nothing; the history's pages are counted at most every `SEEN_S`. The host returns the words (from `realm/lexicon.py`) and data.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from orkboard import settings
from orkboard.gui.ideas_args import IdeasError
from orkboard.realm import board_in_code, event_log, lexicon

ANSWERS = ("publish", "off", "private")
SEEN_S = 30                 # the question is read again after this long, or at once when it is answered or the day's look changed it


def words() -> dict:
    """The four answers' words, from the glossary: `private` · `public` (for a remote Orkboard cannot read), `publish` · `off`."""
    return {"private": lexicon.term("repo_private"), "public": lexicon.term("repo_public"), "publish": lexicon.term("publish_board"), "off": lexicon.term("keep_board_off")}


class InCodeMixin:
    """Needs `host`, `state_dir`, `settings_now()`, `tree_flush()`, `changed()` and `_ev()` (gui/ideas.py)."""

    def _in_code_branch(self) -> str:
        return str(self.settings_now().get("merge_into") or settings.IDEAS["merge_into"])

    def in_code_forget(self) -> None:
        """The question is read afresh at the next board (the day's look found something, or it was answered)."""
        self.__dict__["_in_code_seen"] = {}

    def _in_code_question(self) -> dict | None:
        root = Path(self.host.repo_root)
        seen = self.__dict__.setdefault("_in_code_seen", {})
        now, key = time.monotonic(), (str(root), self._in_code_branch())
        if key in seen and now - seen[key][0] < SEEN_S:
            return seen[key][1]
        got = board_in_code.pending_question(root, key[1], ask=False)
        seen[key] = (now, got)
        return got

    def in_code_rows(self) -> list[dict]:
        """The Orkmaster's card while the question is wanted; [] otherwise, for a demo and for a folder with no git history."""
        if self.host.demo or not (Path(self.host.repo_root) / ".git").exists():
            return []
        try:
            q = self._in_code_question()
        except Exception:                                                    # a question that cannot be read never breaks the board
            return []
        if q is None:
            return []
        unreadable = q["visibility"] == "unknown"
        return [{"kind": "in_code", "step": "private" if unreadable else "publish", "visibility": q["visibility"], "public": q["public"], "pages_in_history": q["pages_in_history"],
                 "title": lexicon.term("is_private") if unreadable else lexicon.term("publish_board") + "?",
                 "text": board_in_code.question_text(q["pages_in_history"]), "ask": lexicon.term("is_private"),
                 "held": board_in_code.HELD if q["public"] else "",
                 "words": words(),
                 "blocks": True, "priority": "high", "at": ""}]

    def in_code(self, args: dict) -> dict:
        """`{answer}`: **Publish the Board** (`publish`: `in_code = true`), **Keep the Board off the repository** (`off`: `in_code = false`), **Private** (`private`, for a remote that could not be read:
        `in_code = true`, nothing is public). The Board's tree is flushed at once, so the pages land on the right side: in the work branch, or off it. Refused in words when nothing asks."""
        answer = args.get("answer")
        if answer not in ANSWERS:
            raise IdeasError("The answer is publish, off or private")
        q = board_in_code.pending_question(Path(self.host.repo_root), self._in_code_branch())      # the day's look, asked of GitHub only when it is a day old
        if q is None:
            raise IdeasError("Nothing asks about the Board in the code now")
        if answer == "private" and q["visibility"] != "unknown":
            raise IdeasError("Only a repository Orkboard cannot read asks whether it is private")
        yes = answer != "off"
        try:
            board_in_code.write(Path(self.host.repo_root), yes)
        except OSError as e:
            raise IdeasError(f"The answer could not be written to orkcraft.toml: {' '.join(str(e).split())[:200]}") from None
        self.in_code_forget()
        self.tree_flush(force=True)                                           # the pages enter the work branch, or stay off it, now
        self._ev(event_log.BOARD_IN_CODE_ANSWERED, args, answer=answer, visibility=q["visibility"])
        self.changed("")
        return {"ok": True, "answer": answer, "in_code": yes, "visibility": q["visibility"]}


def in_code_commands(c: Any) -> dict:
    """The question's command by name (`gui/ideas.py` adds it to its table: `**in_code_commands(self)`)."""
    return {"ideas.in_code": c.in_code}
