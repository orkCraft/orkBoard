"""The night's ladder on the host (docs/specs/168 H3; decisions §283.32; the logic is core/idea_night.py, the rung is `settings.night_rung`).

    ideas.night_ladder {}                                  # the night's card: rung, window, leaders picked, how many tonight
    ideas.night_set {rung, leaders?}                  # the rung (off · ideas · builds · proposals) and the leaders picked; the old `work_at_night` follows
    ideas.night_answer {id, take}                     # a morning proposal: Take (the goal goes on) or Drop (it is gone)

`night_pickup` is called by `route_tick` while the night's window is open. By rung: **ideas** (and up) talks the goals in line (one a pass, as the backlog's
queue does, inside the reserve); **builds** is `work_at_night`'s own (`gui/ideas_board.py` holds the plans for the window); **proposals** asks each leader
picked for one proposal, three a night at most, kept as a goal on Hold so nothing starts it (*Specs*, marked *proposed*). Nothing is spent past the night's reserve.
"""
from __future__ import annotations

import datetime as dt
import time
from typing import Any

from orkboard import settings
from orkboard.core import idea_night
from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import event_log, idea_risk, idea_target, ideas, journals, project_map


class NightMixin:
    def night_card(self, args: dict | None = None) -> dict:
        return idea_night.card(self.settings_now(), self.state_dir)

    def night_set(self, args: dict) -> dict:
        """`{rung, leaders?}`: the ladder's rung (and the leaders picked, a list of parties). The old `work_at_night` is written in step."""
        try:
            values = settings.night_values(str(args.get("rung") or ""), args.get("leaders"))
        except ValueError as e:
            raise IdeasError(str(e)) from None
        if values.get("night_leaders"):
            known = {t["slug"] for t in ideas.tracks(self.root(False), make=False)}
            if missing := [p for p in values["night_leaders"] if p not in known]:
                raise IdeasError(f"No party {missing[0]!r}")
        self.save_settings({**self.settings_now(), **values})
        self._ev(event_log.BOARD_SET, args, **{k: v for k, v in values.items() if k != "night_leaders"})
        self.night_tick()                  # turned down: what was held for the window goes at once, as with the old key
        self.changed("")
        return self.night_card()

    # -- the morning: a proposal's card ------------------------------------------------------------------------

    def night_rows(self, goals: list[dict] | None = None) -> list[dict]:
        """Needs you's rows for the hand: one for each proposal waiting (its card offers *Take* and *Drop*)."""
        return [idea_night.way_row(r) for r in idea_night.rows(self.state_dir)]

    def night_answer(self, args: dict) -> dict:
        pid = _text(args, "id", 120)
        if not isinstance(args.get("take"), bool):
            raise IdeasError("take is true or false")
        try:
            row = idea_night.answer(self.state_dir, pid, args["take"])
        except ValueError as e:
            raise IdeasError(str(e)) from None
        slug = row.get("goal") or ""
        if slug and ideas.idea_page(self.root(), slug) is not None:
            if args["take"]:
                ideas.save_state(self.state_dir, slug, proposed="")
                try:
                    self.queue({"slug": slug, "queue": "now"})    # Take is a press: the goal goes on as any goal does (off Hold, read now)
                except IdeasError:
                    pass                                          # taken all the same; it lies in the deck for the person's own press
            else:
                self.drop({"slug": slug, "why": "A night proposal, dropped"})
        self.changed("")
        return {"ok": True, "status": row["status"]}

    # -- the night's pickup (route_tick) -----------------------------------------------------------------------

    def night_pickup(self, found: list[dict], states: dict, wall: float) -> None:
        s = self.settings_now()
        rung = settings.night_rung(s)
        key = idea_night.night_key(str(s.get("night") or settings.IDEAS["night"]), dt.datetime.fromtimestamp(wall))
        if rung == "off" or not key:
            return
        limits = self._raw_limits()
        if not idea_night.within_reserve(limits, s, wall):         # a night that would spend past the reserve stops
            return
        if idea_risk.night_allows(rung, "talk"):
            self._night_talk(found, states, limits, s, wall)
        if idea_risk.night_allows(rung, "propose"):
            self._night_propose(key, s, limits, wall)

    def _night_talk(self, found: list[dict], states: dict, limits: Any, s: dict, wall: float) -> None:
        """One goal in line talks per pass, and the next only when none started this way is still in Talk."""
        if any(st["from_backlog"] and st["state"] == "talk" for st in states.values()) or self.keeper.window_until():
            return
        for i in found:
            slug, st = i["slug"], states[i["slug"]]
            if st["state"] != "routed" or not st["route"] or st["held_for"] == "hold" or st["route_how"].get("short") or self.keeper.busy(slug):
                continue
            if idea_night.of_goal(self.state_dir, slug) or self.keeper._may_run():
                continue
            if not self.fits_window(slug, st, limits, s, wall):
                continue
            self.route_talk({"idea": slug})
            ideas.save_state(self.state_dir, slug, from_backlog=True)
            return

    def _night_propose(self, key: str, s: dict, limits: Any, wall: float) -> None:
        k = self.keeper
        if k._may_run() or k.window_until() is not None or k.busy("night-proposals"):
            return
        mine = idea_night.who_may(self.state_dir, key, settings.night_leaders(s), "proposals")
        if not mine:
            return
        party = mine[0]                                              # one leader a call; the next at a later pass
        k._start("night-proposals", "proposing", lambda: self._night_make(party, key), key="night-proposals")

    def _night_make(self, party: str, key: str) -> None:
        taken = [r["title"] for r in idea_night.read(self.state_dir)] + [i["title"] for i in ideas.ideas(self.root(False))][:30]
        newest = project_map.newest(self.state_dir) or {}
        text = str(newest.get("overview") or "")[:3000] if isinstance(newest, dict) else ""
        asked = idea_night.prompt(party, text, journals.text(self.state_dir, party), taken)
        got, *_rest = self.keeper.ask("section", asked, tools=False, as_role=self._leader_slug(party))
        made = idea_night.read_answer(got)
        if made is None:
            return
        if not idea_night.within_reserve(self._raw_limits(), self.settings_now(), time.time()):
            return                                                   # the window closed on the call: nothing is laid past the reserve
        self._night_lay(party, key, made)

    def _leader_slug(self, party: str) -> str:
        from orkboard.realm import goal_team
        return goal_team.leader_of(self.root(False), party)

    def _night_lay(self, party: str, key: str, made: dict) -> None:
        """The proposal laid as a goal on Hold in its party (nothing starts it) and kept."""
        out = self.add({"text": f"{made['title']}\n\n{made['spec']}", "track": party, "hold": True})
        slug = out["slug"]
        ideas.save_state(self.state_dir, slug, proposed=key)             # on Hold (`queue: hold`): nothing reads, plans or builds it without a press
        if idea_night.make(self.state_dir, party, key, made["title"], made["spec"], slug) is None:
            self.drop({"slug": slug, "why": "A night proposal past its caps"})
            return
        self.changed("")


def night_commands(ideas_: Any) -> dict:
    return {"ideas.night_ladder": ideas_.night_card, "ideas.night_set": ideas_.night_set, "ideas.night_answer": ideas_.night_answer}
