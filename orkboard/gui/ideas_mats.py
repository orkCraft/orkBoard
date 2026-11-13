"""The cards' commands, over the Board's `Ideas` (docs/specs/171; decisions §301): what the table of cards asks of the host, read from the Board's own pages.

    ideas.turns {}      # the moves that wait for the person (`realm/board_turns.py`): {turns: [{goal, kind, at, questions?}]}; read only, no model, no write
    ideas.verdicts {}   # each goal's tokens: {<goal>: [{leader, verdict, why, stance, for, against, instead, assumes}]}, one for each leader of its route that has said its `### Talk`
    ideas.tables {}     # each party's framework: {<party>: {architecture | jtbd: its cards}}; what is not laid is empty and says who fills it, never an example
    ideas.undo {idea}   # the goal's last one-press move put back (`core/idea_undo.py`), only while its page is still as the move left it
    ideas.take_back {slug}   # a Drop's Undo
    ideas.answer_way {slug, answers, from}   # a question's way played from the hand: each answer written under its open question in the page, no pass begun, no model; its Undo is kept
    ideas.ask_cost {}   # what a paid pass of a leader (reply, ask) is capped at, said before it runs: {calls, usd_high}; read only
    ideas.reply {slug, leader, text, sealed}        # the person's reply to a leader's token on a goal: a paid pass (`core/idea_ask.py` `board_ask`), goal named; {ok, cost}, the answer comes as `ask` in the snapshot
    ideas.ask_leader {slug, leader, text, sealed} | {party, framework, card, text, sealed}   # a leader not on the card, or a part of a leader's framework
    A one-press move (`ideas.drop`, `ideas.queue` for Hold, `ideas.answer_way`) keeps its Undo and logs `move_played`; a sealed one (Merge into main, Send to a branch, Ship a release) goes only with `sealed: true`.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from orkboard.core import idea_undo
from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _device, _text
from orkboard.realm import board_map, board_turns, code_layers, board_ask, event_log, goal_phase, idea_questions, idea_target, ideas, opportunity_tree, page_talk

SEALED_BY = {"ideas.to_main": "merge_main", "ideas.gate_merge": "merge_main", "ideas.goal_to_dev": "send_branch", "ideas.release_out": "ship_release",
             "ideas.reply": "paid_pass", "ideas.ask_leader": "paid_pass", "ideas.gate_fix_stage": "fix_stage"}
ONE_PRESS_BY = ("ideas.drop", "ideas.queue", "ideas.answer_way", "ideas.gate_fix_goal")      # each runs no model (tests/test_ideas_mats_closed.py); `ideas.answer` begins the keeper's pass, so it is none of them; gate_fix_goal keeps its own Undo (gui/ideas_battle.py)
SEALED_ON_CARDS = {"ideas.start": "start_work"}        # sealed where a card of the hand or a mat plays it (`from: hand|mat`): starting begins paid work that cannot be undone; the older faces' presses of it (no `from`) are as they were


def move_kind(name: str, args: dict) -> str:
    """The kind of the hand's move a command is ("" for any other): a Hold is the queue's `hold` (or the old `night`), an answer_way is a question's way."""
    if name in SEALED_BY:
        return SEALED_BY[name]
    if name in SEALED_ON_CARDS:
        return SEALED_ON_CARDS[name] if args.get("from") in ("hand", "mat") else ""
    if name == "ideas.drop":
        return "drop"
    if name == "ideas.queue":
        return "hold" if args.get("queue") in ("hold", "night") else ""
    return "answer" if name == "ideas.answer_way" else "fix_goal" if name == "ideas.gate_fix_goal" else ""


def played(ideas_: Any, name: str, fn: Any) -> Any:
    """`gui/ideas.py`'s `guarded` runs a command through this: a sealed kind is refused unless the page sends its seal; a one-press move keeps its Undo and logs `move_played`."""
    if name not in SEALED_BY and name not in ONE_PRESS_BY and name not in SEALED_ON_CARDS:
        return fn

    def run(args: dict) -> Any:
        kind = move_kind(name, args)
        if not kind:
            return fn(args)
        if idea_undo.way(kind) == "sealed":
            if args.get("sealed") is not True:
                raise IdeasError(f"{idea_undo.SEALED[kind]} cannot be undone: it goes only on its seal")
            got = fn(args)      # a refusal raised above: nothing logged; it keeps no Undo
            origin = args["from"] if args.get("from") in ("hand", "mat") else ""
            goal = next((args[k] for k in ("slug", "idea") if isinstance(args.get(k), str)), "")      # as `ideas.to_main`, `ideas.goal_to_dev` and `ideas.conflict` send it
            ideas_._ev(event_log.MOVE_PLAYED, args, idea=goal, kind=kind, **{"from": origin})
            return got
        slug = args.get("slug") if isinstance(args.get("slug"), str) else ""
        if not slug:
            return fn(args)
        i, party = ideas_, args.get("party") is True and name == "ideas.answer_way"      # a party's own question (its reading asked it) is answered as a goal's, on its own page
        before = idea_undo.snapshot(i.root(), i.state_dir, slug, party)
        got = fn(args)
        origin = args["from"] if args.get("from") in ("hand", "mat") else ""
        if idea_undo.keep(i.state_dir, slug, kind, before, idea_undo.snapshot(i.root(), i.state_dir, slug, party), i.host.publish, origin, party):
            i._ev(event_log.MOVE_PLAYED, args, idea=slug, kind=kind, **{"from": origin})
        return got
    return run


class Mats:
    """The cards' commands, as `gui/ideas_say.py`'s `Say` is the say's."""

    def __init__(self, ideas_: Any) -> None:
        self.i = ideas_

    def turns(self, args: dict) -> dict:
        root = self.i.root(make=False)
        found, pages = ideas.ideas_and_pages(root)
        parties = [{"slug": t["slug"], "title": t["title"]} for t in ideas.tracks(root, make=False)]
        at = {i["slug"]: ideas.touched_at(root, self.i.state_dir, i["slug"]) for i in found}
        waiting = {i["slug"]: w for i in found if (w := self.waiting(i["slug"]))}
        asking = {t["slug"]: page for t in parties if ideas.goal_state(self.i.state_dir, t["slug"])["state"] == "asks" and (page := ideas.track_page(root, t["slug"])) is not None}
        return {"turns": board_turns.turns({i["slug"]: pages[i["slug"]] for i in found}, parties, at, waiting, asking)}

    def waiting(self, slug: str) -> list[dict]:
        """The cards the keeper's record holds for the person at a goal's Talk, as `talk_rows` lays them (a leader's question; a bug's case questions, then its guess as a yes-or-no question):
        read only. They are what the old Needs you card asked, and the page does not hold them until they are answered."""
        if ideas.state(self.i.state_dir, slug)["state"] != "talk":
            return []
        out: list[dict] = []
        for row in board_map.talk_rows(self.i.state_dir, slug):
            if row["kind"] == "talk":
                out += row["questions"]
            elif row["kind"] == "cause":
                out += row["q"]
                out.append({"q": f"Is this the cause? {row['cause']}".strip()[:200], "choices": [CAUSE_YES, CAUSE_NO], "pick": 0})
        return out


    def verdicts(self, args: dict) -> dict:
        root = self.i.root(make=False)
        found, pages = ideas.ideas_and_pages(root)
        parties = ideas.tracks(root, make=False)
        out: dict[str, list] = {}
        for i in found:
            page, seen = pages[i["slug"]], []
            for slug in board_turns.route_of(page):
                say = page_talk.read_talk(page, board_turns._title(parties, slug))
                if say is not None:
                    seen.append({"leader": slug, **say})
            if seen:
                out[i["slug"]] = seen
        return out

    def tables(self, args: dict) -> dict:
        root = self.i.root(make=False)
        have = {t["slug"] for t in ideas.tracks(root, make=False)}
        out: dict[str, dict] = {}
        if "tech" in have:
            arch = code_layers.architecture(Path(self.i.host.repo_root))
            if arch is not None:
                out["tech"] = {"architecture": arch}
        if "product" in have:
            out["product"] = {"jtbd": jobs_to_be_done(opportunity_tree.read(self.i.state_dir))}
        return out

    def undo(self, args: dict, kind: str = "", key: str = "idea") -> dict:
        slug = args.get(key)
        if not isinstance(slug, str) or not slug.strip():
            raise IdeasError(f"{key} is not text")
        party = args.get("party") is True
        got = idea_undo.undo(self.i.root(), self.i.state_dir, slug.strip(), self.i.host.publish, kind, party)
        self.i.tree_note(f"goal:{slug.strip()}" if party else slug.strip(), "undone")
        self.i._ev(event_log.MOVE_UNDONE, args, idea=slug.strip(), kind=got["kind"])
        self.i.changed(f"goal:{slug.strip()}" if party else slug.strip())
        return {"ok": True, **got}

    def answer_way(self, args: dict) -> dict:
        """A question's way played from the hand: each answer (in the order of the questions that wait, `board_turns.asking`) written under its question in the page, as `ideas_phase.py`
        `outside_answer` writes one, with the page's `asks` followed at once. A leader's question to the person (Talk's, a bug's cause) is written as `talk_answer` writes it
        (`answers_written`: under its line, added where the page lacks it) and the keeper's record is left as it is. No keeper pass is begun and no model runs; a leader's pass that must follow is
        a separate, sealed move (`ideas.reply`). `party: true`: the questions of a party's own page."""
        slug, answers = _text(args, "slug", 100), args.get("answers")
        if not isinstance(answers, list) or not all(isinstance(a, str) for a in answers):
            raise IdeasError("answers are a list of text")
        root, party = self.i.root(), args.get("party") is True
        page = ideas.track_page(root, slug) if party else ideas.idea_page(root, slug)
        if page is None:
            raise IdeasError("That party is gone" if party else "That goal is gone")
        text, day = page.section("Open questions"), dt.date.today().isoformat()
        waiting = board_turns.asking(page, () if party else self.waiting(slug))
        given = [(q, " ".join(a.split())[:2000]) for q, a in zip(waiting, answers)]
        if not waiting:
            raise IdeasError("This goal asks nothing now")
        if not any(a for _q, a in given):
            raise IdeasError("Answer at least one question")
        for q, a in given:
            if a:
                text = idea_questions.with_answer(text, q["n"] if "n" in q else q["line"], a, day, "the person")
        with ideas.LOCK:
            if party:
                page.set_section("Open questions", text, ideas.TRACK_SECTIONS)
                ideas._write(root / ideas.TRACKS / f"{slug}.md", page.text())
            else:
                ideas.set_section(root, slug, "Open questions", text)
        if not party:
            goal_phase.mirror(root, self.i.state_dir, lambda i, st, plan, asks: self.i._idea_needs(i, st, plan, asks, root), only=slug)
        self.i._ev(event_log.IDEA_ANSWERED, args, idea=slug, answers=sum(1 for _q, a in given if a), decided=False, round=1, recommended=0, picked=0,
                   typed=sum(1 for _q, a in given if a), **({"from": args["from"]} if args.get("from") in ("hand", "open") else {}))
        self.i._what[f"goal:{slug}" if party else slug] = "answered"
        self.i.changed(f"goal:{slug}" if party else slug)
        return {"ok": True}

    def ask_cost(self, args: dict | None = None) -> dict:
        """What one paid pass (a quick question's call, the cheaper tier, no tools) is capped at under the Target, read before any model runs."""
        return {"calls": 1, "usd_high": idea_target.budget("ask", idea_target.target_for(self.i.settings_now()))}

    def _pass(self, party: str, about: str, text: str) -> dict:
        """The question to `party`'s leader, `about` named first, begun through the keeper's `board_ask`; its cost is returned with it (the page said it on the tool's potion before)."""
        if not ideas.track_page(self.i.root(make=False), party):
            raise IdeasError("That party is gone")
        q = f"{about} {text}"
        if len(q) > board_ask.Q_CHARS:
            q = f"{about} {text[:max(0, board_ask.Q_CHARS - len(about) - 1)]}"
        try:
            self.i.keeper.board_ask(party, q)
        except KeeperError as e:
            raise IdeasError(str(e)) from None
        self.i.changed("")
        return {"ok": True, **self.ask_cost()}

    def _goal(self, args: dict) -> tuple[str, str]:
        slug = _text(args, "slug", 100)
        page = ideas.idea_page(self.i.root(make=False), slug)
        if page is None:
            raise IdeasError(f"No goal {slug!r}")
        return slug, page.title

    def reply(self, args: dict) -> dict:
        slug, title = self._goal(args)
        return self._pass(_text(args, "leader", 100), f"About the goal «{title}» ({slug}), in answer to your word:", _text(args, "text", board_ask.Q_CHARS))

    def ask_leader(self, args: dict) -> dict:
        if isinstance(args.get("slug"), str) and args["slug"].strip():
            slug, title = self._goal(args)
            return self._pass(_text(args, "leader", 100), f"About the goal «{title}» ({slug}):", _text(args, "text", board_ask.Q_CHARS))
        party, framework, card = _text(args, "party", 100), _text(args, "framework", 100), _text(args, "card", 100)
        return self._pass(party, f"About {framework}, its part «{card}»:", _text(args, "text", board_ask.Q_CHARS))

    def take_back(self, args: dict) -> dict:
        return self.undo(args, "drop", "slug")


CAUSE_YES, CAUSE_NO = "Yes, that is the cause", "No, it is elsewhere"
ASKS_JOBS = "Product lays its jobs"
ASKS_PEOPLE = "Product asks the person who the people are"


def jobs_to_be_done(rec: dict) -> dict:
    """Product's Jobs to be done from the tree's record: its jobs when kept, else every zone empty and `fills` saying who lays it; no example."""
    jobs = rec.get("jobs") or []
    segments = list(dict.fromkeys(j["segment"] for j in jobs if j.get("segment")))
    main = jobs[0] if jobs else None
    return {
        "personas": [{"id": f"persona-{n}", "title": s, "line": ""} for n, s in enumerate(segments)],
        "job": {"id": main["id"], "when": main["when"], "want": main["want"], "so": main["so"], "persona": main.get("segment", "")} if main else None,
        "forces": [], "hired": None, "fired": [],
        "jobs": [{"id": j["id"], "title": j["want"], "line": j["when"]} for j in jobs[1:]],
        "fills": {"personas": "" if segments else ASKS_PEOPLE, "job": "" if main else ASKS_JOBS, "jobs": "" if len(jobs) > 1 else ASKS_JOBS,
                  "forces": ASKS_JOBS, "hired": ASKS_JOBS, "fired": ASKS_JOBS},
    }


def mats_commands(ideas_: Any) -> dict:
    """The cards' commands by name (`gui/ideas.py` adds them to its table: `**mats_commands(self)`)."""
    m = Mats(ideas_)
    return {"ideas.turns": m.turns, "ideas.verdicts": m.verdicts, "ideas.tables": m.tables,
            "ideas.undo": m.undo, "ideas.take_back": m.take_back, "ideas.answer_way": m.answer_way, "ideas.ask_cost": m.ask_cost, "ideas.reply": m.reply, "ideas.ask_leader": m.ask_leader}
