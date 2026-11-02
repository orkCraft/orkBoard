"""A change asked of a leader (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md E; decisions §206.5), as `gui/ideas.py`'s `Ideas` has it: the commands the bubble's
*Make it a change* and the decision card in the hand send. The record (`realm/leader_change.py`) waits in the goal's state folder; its Needs you row is `kind: "leader_change"`
(`realm/board_map.py` reads it); the leader makes it (`core/idea_leader_change.py`).

    ideas.change {idea, party, part?, text}        # the party's leader replans its part from the words (in the background); `{ok, id}`; a refusal is an IdeasError in the keeper's words
    ideas.change_take {idea, id, look?, decide?, via?}   # *Accept*: the plan change is taken by the runner (its tasks not started), the party's *Will be* lines written into its section of the
                                                   # spec, and the person's decision written into the goal's Decisions. A Design change takes the look `look` (its key), or the first when `decide`
                                                   # is true (*Let Design decide*). `{ok, added, changed, dropped, left}`
    ideas.change_keep {idea, id, via?}             # *Keep the spec* (and *Talk more*, which opens the bubble again): the change is dropped, nothing else changes; `{ok}`
"""
from __future__ import annotations

from typing import Any

from orkboard.gui.ideas_args import IdeasError, _opt, _str, _text, _via
from orkboard.core.idea_leader_change import TEXT_CHARS
from orkboard.realm import event_log, idea_change, ideas, leader_change

NOT_READY = "That change did not come: ask the leader again"


class ChangeMixin:
    def change(self, args: dict) -> dict:
        slug, party = _text(args, "idea", 100), _text(args, "party", 100)
        part = args.get("part", "")
        if not isinstance(part, str):
            raise IdeasError("part is not text")
        cid = self.keeper.change_ask(slug, party, part, _str(args, "text", TEXT_CHARS * 2))
        self.changed(slug)
        return {"ok": True, "id": cid}

    def _title_of(self, party: str) -> str:
        page = ideas.track_page(self.root(), party)
        return (page.title if page is not None else "") or party

    def change_take(self, args: dict) -> dict:
        slug, cid = _text(args, "idea", 100), _text(args, "id", 40)
        want, decide = _opt(args, "look"), args.get("decide") is True
        with ideas.LOCK:                             # claimed: a second press finds none waiting
            rec = leader_change.get(self.state_dir, slug, cid)
            if rec is None:
                raise IdeasError("No change waits for this goal")
            if rec.get("status") != "ready":
                raise IdeasError(NOT_READY)
            look = None
            if rec.get("shape") == "looks":
                looks = rec.get("looks") or []
                look = next((x for x in looks if x["key"] == want), looks[0] if decide and looks else None)
                if look is None:
                    raise IdeasError("Pick a look, or let the leader decide")
            if self.keeper.busy(slug):
                raise IdeasError("The keeper is busy with this goal: a moment")
            change = rec.get("change") or {}
            ops = bool(change.get("change") or change.get("drop") or change.get("add")) and ideas.plan(self.state_dir, slug) is not None
            runner = self.runner(need=True) if ops else None
            leader_change.drop(self.state_dir, slug, cid)
        got = {"added": 0, "changed": 0, "dropped": 0, "left": []}
        try:
            if ops:
                got = runner.revise_tasks(slug, change)
                now = ideas.plan(self.state_dir, slug) or {}
                self.keeper.write_stages(slug, {**now, "tasks": idea_change.in_order(now.get("tasks") or [])})
        except Exception:
            leader_change.put(self.state_dir, slug, rec)             # it did not apply: it waits as it did
            raise
        lines = look["lines"] if look else (rec.get("after") or {}).get("lines") or []
        wrote = bool(lines) and leader_change.write_lines(self.root(), slug, rec["party"], lines)
        said = f" · {rec['part']}" if rec.get("part") else ""
        how = f", look {look['name']}" if look else ""
        ideas.update(self.root(), slug, {}, [f"The person decided, {self._title_of(rec['party'])}{said}{how}: {rec['text']}"])
        self._ev(event_log.LEADER_CHANGE_ANSWERED, args, idea=slug, party=rec["party"], take=True, look=look["key"] if look else "", added=got["added"], changed_n=got["changed"],
                 dropped=got["dropped"], wrote=wrote, via=_via(args))
        self.changed(slug)
        return {"ok": True, **got}

    def change_keep(self, args: dict) -> dict:
        slug, cid = _text(args, "idea", 100), _text(args, "id", 40)
        rec = leader_change.get(self.state_dir, slug, cid)
        if rec is None or not leader_change.drop(self.state_dir, slug, cid):
            raise IdeasError("No change waits for this goal")
        self._ev(event_log.LEADER_CHANGE_ANSWERED, args, idea=slug, party=rec["party"], take=False, look="", added=0, changed_n=0, dropped=0, via=_via(args))
        self.changed(slug)
        return {"ok": True}


def change_commands(ideas_: Any) -> dict:
    """The change asked of a leader's commands by name (`gui/ideas.py` adds them to its table: `**change_commands(self)`)."""
    return {"ideas.change": ideas_.change, "ideas.change_take": ideas_.change_take, "ideas.change_keep": ideas_.change_keep}
