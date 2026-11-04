"""The phone's answers to the hand's cards, through the inbox (spec 137 C, decisions §244.5): `inbox/<device>/<id>.answer.json`.

    remote_answers.entries(root)                       # [Answer]: the answer files on the fetched inbox (realm/remote_inbox.py fetched it)
    remote_answers.clean(raw, entry)                   # ({"card", "kind", "answer"}, "") · (None, "Could not read this answer: …")
    remote_answers.card_key(row)                       # the id a phone names a card of the hand by
    remote_answers.call(row, kind, answer)             # (command, args): what the hand's own command takes, the card's identity from the row
    remote_answers.take(root, state_dir, config, apply, …)   # one tick: read, take in the journal, apply, say how it went

The file is `{"v": 1, "id", "device", "at", "card": "<the row's id>", "kind": "<the row's kind>", "answer": {…}}`, `answer` being the arguments
the hand's command takes for that kind (`KINDS`). It is **taken as a goal is** (decisions §243.4): written into `taken.json` under its own `id`
and the journal sent first; only when that push went through is it applied, by `apply(answer)` (the host's: it finds the card on the hand and
calls the same command the hand does), and the card's goal (or its kind, for a card of no goal's) goes into the row's `slug` and the next
journal. A card gone, or answered already, is taken with the host's words as `error`; so is a file that cannot be read. Nothing here ever
writes the inbox. What names the card (`idea`, `goal`, a fork's or a stop's id) comes from the Board's row, never from the file; only the
answer's own keys (`KINDS`' third) are passed on.

No face (the host passes `apply`), no model, no network but what `remote_inbox` and `remote_journal` do.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from orkboard.realm import remote_inbox as ri, remote_journal as rj

_ANSWER = re.compile(r"inbox/([A-Za-z0-9._-]+)/([A-Za-z0-9_-]+)\.answer\.json")
MAX_BYTES = 64 * 1024
MAX_PER_TICK = 20

# kind of the hand's row -> (the hand's command, {argument: where the row has it}, the keys of `answer` that are passed on)
KINDS: dict[str, tuple[str, dict[str, str], tuple[str, ...]]] = {
    "talk": ("ideas.talk_answer", {"idea": "idea"}, ("answers", "decide")),
    "cause": ("ideas.cause_answer", {"idea": "idea"}, ("yes", "text", "answers")),
    "hearing": ("ideas.throw", {"idea": "idea", "moment": "moment"}, ("dir", "text")),
    "fork": ("ideas.fork_answer", {"idea": "idea"}, ("side", "text")),
    "decision": ("ideas.confirm", {"idea": "idea"}, ("text",)),
    "project_q": ("ideas.project_answer", {}, ("answers", "decide")),
    "change": ("ideas.revise_answer", {"slug": "idea"}, ("take",)),
    "party": ("ideas.party_answer", {"goal": "goal"}, ("take", "reason")),
    "proposal": ("ideas.proposal", {"slug": "idea"}, ("take", "priority", "reason")),
    "collide": ("ideas.collide_answer", {"id": "collide.id"}, ("answer",)),
}
NOT_A_KIND = "A phone does not answer this kind of card"
GONE = "That card is gone, or answered already"


@dataclass(frozen=True)
class Answer:
    id: str
    device: str
    path: str


def entries(root: Path, run: Callable = subprocess.run) -> list[Answer]:
    """The answer files on the fetched inbox, by id (a ULID sorts by time)."""
    try:
        listing = str(ri._git(root, run, "ls-tree", "-r", "-z", ri.INBOX_REF))
    except RuntimeError:
        return []
    out = []
    for rec in listing.split("\0"):
        m = _ANSWER.fullmatch(rec.partition("\t")[2])
        if m and ri._ID.fullmatch(m.group(2)):
            out.append(Answer(m.group(2), m.group(1), rec.partition("\t")[2]))
    return sorted(out, key=lambda a: (a.id, a.device))


def card_key(row: dict) -> str:
    """The id a phone names a card of the hand by: the row's own `id` (a fork's), a stop's (`collide.id`), else its goal's slug (`idea`), else its
    party's (`goal`); "" for a card of no goal's (the project's question)."""
    collide = row.get("collide") if isinstance(row.get("collide"), dict) else {}
    for v in (row.get("id"), collide.get("id"), row.get("idea"), row.get("goal")):
        if isinstance(v, str) and v:
            return v
    return ""


def _at(row: dict, where: str):
    for part in where.split("."):
        row = row.get(part) if isinstance(row, dict) else None
    return row


def call(row: dict, kind: str, answer: dict) -> tuple[str, dict]:
    """`(command, args)`: the hand's command for this kind of card, with what names the card taken from `row` and only the answer's own keys passed on."""
    name, ident, keys = KINDS[kind]
    args = {arg: _at(row, where) for arg, where in ident.items() if _at(row, where) is not None}
    args.update({k: answer[k] for k in keys if k in answer})
    return name, args


def clean(raw: bytes | str, entry: Answer) -> tuple[dict | None, str]:
    """The answer as the host applies it, or `(None, "Could not read this answer: <why>")`."""
    def bad(why: str) -> tuple[None, str]:
        return None, f"Could not read this answer: {why}"
    if len(raw) > MAX_BYTES:
        return bad("it is too long")
    try:
        data = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    except (ValueError, UnicodeDecodeError):
        return bad("it is not an answer's file")
    if not isinstance(data, dict):
        return bad("it is not an answer's file")
    if data.get("v") != 1:
        return bad("it is of a version this Orkboard does not know")
    if data.get("id") not in (None, entry.id):
        return bad("its id is not its file's")
    kind, card, answer = data.get("kind"), data.get("card"), data.get("answer")
    if not isinstance(kind, str) or kind not in KINDS:
        return bad(NOT_A_KIND.lower())
    if not isinstance(card, str) or len(card) > 200:
        return bad("it names no card")
    if not isinstance(answer, dict):
        return bad("it holds no answer")
    return {"card": card, "kind": kind, "answer": answer, "device": entry.device}, ""


def _read(root: Path, a: Answer, run: Callable) -> tuple[dict | None, str]:
    try:
        raw = ri.read(root, a.path, run)
    except Exception as err:
        return None, f"Could not read this answer: {' '.join(str(err).split())[:120]}"
    return clean(raw, a)


def take(root: Path, state_dir: Path, config: rj.JournalConfig, apply: Callable[[dict], tuple[str, str]], name: str, now: dt.datetime,
         run: Callable = subprocess.run, pages: Path | None = None, needs=frozenset(), out: dict | None = None) -> dict:
    """One tick of the answers, after `remote_inbox.take` fetched the inbox. `apply(answer)` → `(slug, error)`: the card's goal (or kind) when the
    hand's command ran, else the host's words. Returns `out` with `answered` and `answer_errors` added; never raises."""
    out = out if out is not None else {}
    out.setdefault("answered", 0)
    out.setdefault("answer_errors", 0)
    try:
        found = entries(root, run)
        taken_now = {t["id"] for t in rj.read_taken(state_dir, now)}
        todo = [a for a in found if a.id not in taken_now][:MAX_PER_TICK]
        answers: dict[str, dict | None] = {}
        mine: list[dict] = []
        for a in todo:
            got, err = _read(root, a, run)
            answers[a.id] = got
            mine.append({"id": a.id, "by": name, "at": now.isoformat(timespec="seconds"), "slug": "", "error": err})
        if mine:
            mine = ri._take_in_journal(root, state_dir, config, mine, now, run, pages, needs, out)
            for m in mine:
                if m["error"]:                          # one that could not be read is taken with its error, so it is not read again
                    out["answer_errors"] += 1
                    ri._said(root, ok=True, id=m["id"], by=name, slug="", error=m["error"])
        _apply_all(root, state_dir, config, answers, found, apply, name, now, run, pages, needs, out)
    except Exception as e:
        out["why"] = out.get("why") or " ".join(str(e).split())[:300] or type(e).__name__
    return out


def _apply_all(root: Path, state_dir: Path, config: rj.JournalConfig, answers: dict, found: list[Answer], apply: Callable, name: str,
               now: dt.datetime, run: Callable, pages: Path | None, needs, out: dict) -> None:
    """Apply what this machine took and has not applied (this tick's, and a tick's before that stopped): a card answered in between is `GONE`."""
    taken = rj.read_taken(state_dir, now)
    by_id = {a.id: a for a in found}
    changed = False
    for row in taken:
        if row["by"] != name or row["slug"] or row["error"] or row["id"] not in by_id:
            continue                                    # not an answer of ours, or done, or a goal's row
        answer = answers.get(row["id"])
        error = ""
        if answer is None:
            answer, error = _read(root, by_id[row["id"]], run)
        slug = ""
        if answer is not None:
            try:
                slug, error = apply(answer)
            except Exception as e:
                slug, error = "", " ".join(str(e).split())[:300] or type(e).__name__
        row["slug"], row["error"] = slug, error if not slug else ""
        out["answered" if slug else "answer_errors"] += 1
        changed = True
        ri._said(root, ok=True, id=row["id"], by=name, slug=row["slug"], error=row["error"])
    if changed:
        rj.write_taken(state_dir, taken)
        rj.send(root, state_dir, config, now, run, pages, needs)
