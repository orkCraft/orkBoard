"""Recurring goals: what the project's running party proposes, and a goal that comes back (docs/specs/92-running-and-the-team.md §2, decisions §108).

    listed("mobile-liveops")                     # [{id, title, every, words}, …]: the recurring goals a party made from that recipe proposes
    get("mobile-liveops", "deps")                # one of them with its text, or None
    set_every(root, "ship-it", "week", words)    # the goal comes back every week once it is done ("" stops it); `words`: what it comes back as
    every_of(root, "ship-it")                    # "day" · "week" · "month" · ""
    words_of(root, "ship-it")                    # what the next goal is written from: the words it was made with, else its Gist
    due(root, state_dir, now)                    # [slug, …]: recurring goals that were done a period ago (and stamps the day each was first seen done)
    hand_over(root, old, new)                    # the new goal repeats as the old one did; the old one stops (it stays as it was done)

A recurring goal is an ordinary goal of the party with `repeat` on its page (`day`, `week` or `month`). When it is done the host waits its period and
then adds a fresh goal with the same words in the same party, and the repeat moves to the new one: the done goal stays as the record of that round, and
dropping the goal that carries the repeat ends it. Nothing here starts a model: the new goal is added as the person's own New goal is. No face, no model.

The routines are the recipes' own (`party_recipes` `<kind>-liveops`: the stage a project's running is, named LiveOps for a game, Upkeep for words and
files, Run for the rest): two to four a recipe, each a title, how often, and the few lines the party's leader drafts the goal from.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from orkboard.realm import ideas

EVERY = {"day": 1, "week": 7, "month": 30}                               # how often, in days
WORDS = {"day": "every day", "week": "every week", "month": "every month"}
META, FROM, TEXT = "repeat", "repeat_from", "repeat_text"                 # the page's keys: how often, the day it was first seen done, and the words it comes back as (JSON: one line)


def _r(rid: str, title: str, every: str, text: str) -> dict:
    return {"id": rid, "title": title, "every": every, "text": text}


_DEPS = _r("deps", "Weekly dependency check", "week",
           "Look at the project's dependencies for new versions and known security problems. List what is out of date, update what is safe and passes the tests, "
           "and say what needs the person's look and why.")
_LINKS = _r("links", "Check the links", "week",
            "Follow every link in the pages and docs and list the ones that no longer work. Fix those whose new address is certain and say which ones need a person.")

# The recurring goals of each running party (the recipes `<kind>-liveops`), most useful first; a party proposes them when it is made.
ROUTINES: dict[str, list[dict]] = {
    "game-liveops": [
        _r("numbers", "Read the week's numbers", "week", "Read the week's numbers of play: who came back, where they stopped, what they spent. Say what moved and what to try, with the counts it comes from."),
        _r("players", "Read what players say", "week", "Read what players wrote this week in the reviews and the community. Group it by what they ask for or are annoyed by, with how many said it, and propose the smallest fixes."),
        _r("crashes", "Look at the crash reports", "week", "Look at the week's crashes and errors. List the most common with how many players they touch, and fix what is small and certain."),
    ],
    "mobile-liveops": [
        _DEPS,
        _r("reviews", "Read the new reviews", "week", "Read the store reviews that came in this week. Group them by what people ask for or are annoyed by, with how many said it, and draft answers for the person to send."),
        _r("crashes", "Look at the crashes", "week", "Look at the week's crashes and errors of the app. List the most common with how many people they touch, and fix what is small and certain."),
    ],
    "web-liveops": [
        _DEPS,
        _r("uptime", "Look at errors and speed", "week", "Look at the week's errors and slow pages of the site. List the worst with where they happen, and fix what is small and certain."),
        _r("feedback", "Read what people write", "week", "Read what people wrote this week through the contact page and the community. Group it by what they ask for, with how many said it."),
    ],
    "backend-liveops": [
        _DEPS,
        _r("incidents", "Read the week's incidents", "week", "Read the week's errors and incidents of the service. List each with what it touched and how long, and write what would stop it coming back."),
        _r("slow", "Find the slowest calls", "week", "Find the slowest calls and queries of the week. List the worst with how often they run, and propose the smallest change that speeds them."),
    ],
    "data-liveops": [
        _r("fresh", "Check the data is fresh", "day", "Check that each pipeline ran and each table has the day's rows. List what is late or empty and since when."),
        _r("recount", "Recount the key numbers", "week", "Recount the key numbers of the reports from their source on a sample, and say which ones differ and by how much."),
    ],
    "wiki-liveops": [
        _r("stale", "Find stale pages", "week", "Find the pages nobody has touched for a long time or that say something the project no longer does. List them with what is out of date, and fix what is certain."),
        _LINKS,
        _r("sources", "Take in the new sources", "week", "Read the sources added since the last time (notes, documents, links) and take them into the pages they belong to, saying which pages changed."),
    ],
    "design-liveops": [
        _r("drift", "Find what drifted from the kit", "month", "Compare the screens with the design system and list where they use a colour, a size or a component that is not the kit's."),
        _r("contrast", "Check contrast and tap sizes", "month", "Check the screens for contrast, tap sizes and names a screen reader says, and list what fails and where."),
    ],
    "texts-liveops": [
        _r("stale", "Find stale texts", "month", "Find the texts that say something that is no longer true, and list them with what changed."),
        _LINKS,
    ],
    "code-liveops": [
        _DEPS,
        _r("builds", "Look at the failing builds", "week", "Look at the week's failing builds and tests. List what fails most with since when, and fix what is small and certain."),
    ],
}


def _row(recipe_id: str) -> list[dict]:
    return ROUTINES.get(recipe_id, [])


def listed(recipe_id: str) -> list[dict]:
    """The recurring goals a recipe proposes, as a face shows them: `{id, title, every, words}`; none for a recipe with none."""
    return [{"id": r["id"], "title": r["title"], "every": r["every"], "words": WORDS[r["every"]]} for r in _row(recipe_id)]


def get(recipe_id: str, routine_id: str) -> dict | None:
    return next((r for r in _row(recipe_id) if r["id"] == routine_id), None)


def text_of(routine: dict) -> str:
    """The goal's words: the title as its first line (it becomes the goal's title), then what to do."""
    return f"{routine['title']}\n\n{routine['text']}"


def every_of(root: Path, slug: str) -> str:
    page = ideas.idea_page(root, slug)
    value = page.get(META) if page is not None else ""
    return value if value in EVERY else ""


def words_of(root: Path, slug: str) -> str:
    """What the next goal is written from: the words the repeat was set with (the keeper rewrites a goal's Gist as it drafts it), else the goal's Gist."""
    page = ideas.idea_page(root, slug)
    if page is None:
        return ""
    try:
        kept = json.loads(page.get(TEXT) or '""')
    except ValueError:
        kept = ""
    return kept if isinstance(kept, str) and kept.strip() else page.section("Gist")


def set_every(root: Path, slug: str, every: str, words: str = "") -> None:
    """The goal comes back `every` ("day", "week" or "month") once it is done; "" stops it. `words`: what it comes back as (kept as it is when none is given and
    the repeat goes on). ValueError for another word."""
    if every and every not in EVERY:
        raise ValueError("A goal comes back every day, week or month")
    page = ideas.idea_page(root, slug)
    keep = json.dumps(words, ensure_ascii=False) if every and words else (page.get(TEXT) if every and page is not None else "")
    ideas.set_meta(root, slug, **{META: every, FROM: "", TEXT: keep})


def hand_over(root: Path, old: str, new: str) -> None:
    """The repeat moves from a goal that was done to the goal that renews it."""
    every, words = every_of(root, old), words_of(root, old)
    ideas.set_meta(root, old, **{META: "", FROM: "", TEXT: ""})
    if every:
        set_every(root, new, every, words)


def due(root: Path, state_dir: Path, now: dt.datetime) -> list[str]:
    """The recurring goals that were done a period ago: a goal is first seen done at `now` (the day is kept on its page), and is due once `EVERY` days
    have passed from then; a goal that is not done any more (it was reopened) forgets the day. Writes only that day."""
    out = []
    for g in ideas.ideas(root):
        every = every_of(root, g["slug"])
        if not every:
            continue
        page = ideas.idea_page(root, g["slug"])
        seen = page.get(FROM) if page is not None else ""
        if ideas.state(state_dir, g["slug"])["state"] != "done":
            if seen:
                ideas.set_meta(root, g["slug"], **{FROM: ""})
            continue
        if not seen:
            ideas.set_meta(root, g["slug"], **{FROM: now.isoformat(timespec="seconds")})
            continue
        try:
            since = dt.datetime.fromisoformat(seen)
        except ValueError:
            ideas.set_meta(root, g["slug"], **{FROM: now.isoformat(timespec="seconds")})
            continue
        if now - since >= dt.timedelta(days=EVERY[every]):
            out.append(g["slug"])
    return out
