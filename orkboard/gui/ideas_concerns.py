"""A party's concerns (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §2.5; decisions §183.4–§183.6), as `gui/ideas.py`'s `Ideas` has them: the commands the map's faces read and answer them by.

    ideas.concerns {party}              # → the record (`realm/concerns.py`) as the face reads it: {party, map, leader, has_map, at, map_hash, by, status: "" | "looking" | "ready" | "failed", error?, measure,
                                        #    concerns: [{id, on, name, level: "alert" | "note", what, why, fix, signal, idea?}], dismissed: [{on, what, at, map_hash, part_hash}], alerts, notes, waits?}
                                        #    (`idea`: the slug of the goal made of a concern) and starts a look when one is due (the person opened the map and it has none yet, or it changed and the last is a day old); `waits` is why one could
                                        #    not be made now (a spent window or limit), in plain words; nothing is touched then
    ideas.concerns_again {party}        # a look now → {ok, asked: bool, why?}
    ideas.concern_dismiss {party, id}   # *Not a problem*: the concern is dismissed (not raised again while its part is as it was) → {ok, concerns, alerts, notes}
    ideas.concern_goal {party, id}      # *Make it a goal*: an `ideas.add` of the party with the concern's what and fix as its words, its part as the goal's mark and the type its map's default
                                        #    (System `restructure`, screens `screen`, the loop `balance`; none where the party is not offered it) → {ok, idea, concerns, alerts, notes}

`alerts` and `notes` count the open concerns (no goal was made of them). The party's snapshot row (`ideas.map` `goals[]`) carries `concerns: {alerts, notes, status}` for its tab. The host returns keys and data,
never interface words; a refusal is plain words.
"""
from __future__ import annotations

from typing import Any

from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _str
from orkboard.realm import concerns as store, event_log, goal_team, goal_types, ideas, map_parts

DEFAULT_TYPE = {"system": "restructure", "screens": "screen", "game-design": "balance"}      # a map's goal type, when its party is offered it


class ConcernsMixin:
    def _concern_party(self, args: dict) -> str:
        party = _str(args, "party", 100).strip()
        if not party or party == ideas.GENERAL or party not in {t["slug"] for t in ideas.tracks(self.root(make=False), make=False)}:
            raise IdeasError("That party is gone")
        return party

    def _concern_record(self, party: str) -> dict:
        """The record as the face reads it: a look lost with the process is no longer `looking`; the counts of the open concerns."""
        rec = store.read(self.state_dir, party)
        if rec["status"] == "looking" and not self.keeper.busy_goal(party):
            rec["status"] = ""
        return {**rec, **store.counts(rec)}

    def concerns_counts(self, party: str) -> dict:
        """The party's row in the snapshot: `{alerts, notes, status}`."""
        try:
            rec = self._concern_record(party)
        except (OSError, ValueError):
            return {"alerts": 0, "notes": 0, "status": ""}
        return {k: rec[k] for k in ("alerts", "notes", "status")}

    def concerns(self, args: dict) -> dict:
        party = self._concern_party(args)
        root = self.root(make=False)
        craft = map_parts.craft_of(root, party)
        out = {"party": party, "map": map_parts.MAPS.get(craft, ""), "leader": goal_team.leader_of(root, party), "has_map": craft in map_parts.MAPS}
        waits = ""
        if out["has_map"]:
            try:
                if self.keeper.concerns(party, "open"):
                    self.changed("")                                  # the look has begun: the strip says so
            except KeeperError as e:                                  # a spent window or limit: said on the strip, nothing touched
                waits = str(e)
        rec = self._concern_record(party)
        if rec["concerns"]:                                           # the page sends no event of its own: each opening of a map that has concerns is one `concern_opened`
            self._ev(event_log.CONCERN_OPENED, args, party=party, level="alert" if any(c["level"] == "alert" for c in rec["concerns"]) else "note")
        return {**out, **rec, **({"waits": waits} if waits else {})}

    def concerns_again(self, args: dict) -> dict:
        party = self._concern_party(args)
        try:
            asked = self.keeper.concerns(party, "again")
        except KeeperError as e:                                      # the keeper's refusals are plain words; none fails the caller
            return {"ok": True, "asked": False, "why": str(e)}
        self.changed("")
        return {"ok": True, "asked": asked}

    def _concern(self, args: dict) -> tuple[str, dict]:
        party = self._concern_party(args)
        cid = _str(args, "id", 60).strip()
        found = next((c for c in store.read(self.state_dir, party)["concerns"] if c["id"] == cid), None)
        if found is None:
            raise IdeasError("That concern is gone")
        return party, found

    def concern_dismiss(self, args: dict) -> dict:
        party, found = self._concern(args)
        craft, text, parts = self.keeper.concern_context(party)
        part = next((p for p in parts if p["id"] == found["on"]), {"id": found["on"], "name": found["name"]})
        store.dismiss(self.state_dir, party, found["id"], store.part_hash(text, part))
        self._ev(event_log.CONCERN_DISMISSED, args, party=party, level=found["level"])
        self.changed("")
        rec = self._concern_record(party)
        return {"ok": True, "concerns": rec["concerns"], "alerts": rec["alerts"], "notes": rec["notes"]}

    def concern_goal(self, args: dict) -> dict:
        party, found = self._concern(args)
        root = self.root(make=False)
        craft = map_parts.craft_of(root, party)
        map_id = map_parts.MAPS.get(craft, "")
        offered = {t.id for t, _missing in goal_types.offered(self.state_dir, root, party)}
        kind = DEFAULT_TYPE.get(map_id, "")
        text = found["what"] + (f"\n\n{found['fix']}" if found["fix"] else "")
        made = self.add({"party": party, "text": text, "marks": [{"map": map_id, "id": found["on"], "name": found["name"]}], **({"type": kind} if kind in offered else {}),
                         **({"device": args["device"]} if "device" in args else {})})
        store.made_goal(self.state_dir, party, found["id"], made["slug"])
        self._ev(event_log.CONCERN_GOAL, args, party=party, level=found["level"], idea=made["slug"])
        self.changed("")
        rec = self._concern_record(party)
        return {"ok": True, "idea": made["slug"], "type": made.get("type", ""), "concerns": rec["concerns"], "alerts": rec["alerts"], "notes": rec["notes"]}


def concerns_commands(ideas_: Any) -> dict:
    """A party's concerns by name (`gui/ideas.py` adds them to its table: `**concerns_commands(self)`)."""
    return {"ideas.concerns": ideas_.concerns, "ideas.concerns_again": ideas_.concerns_again,
            "ideas.concern_dismiss": ideas_.concern_dismiss, "ideas.concern_goal": ideas_.concern_goal}
