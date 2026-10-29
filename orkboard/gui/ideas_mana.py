"""The tool now and going on paid (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §2, §3), as `gui/ideas.py`'s `Ideas` has them: the tool the work follows
when the Main tool is out (realm/tool_now.py), said once when it moves, and the Orkmaster's row `paid` and its one command.

    ideas.tool_now()        # {main, now, until, moved_from} (realm/tool_now.py `now`) for this Board: the machine's tools, the quota's last read, this Board's yes to go on paid
    ideas.follow()          # the tool now: what the runner and the keeper fall to where they fell to the Main tool
    ideas.mana()            # the snapshot's `mana`: {main, now, until, moved: {from, to, until, at, line} | None}
    ideas.mana_tick()       # from the clock: a change of the tool now is published (`bus.TOOL_MOVED`, once) and logged (`tool_moved`)
    ideas.paid_rows()       # [] or the row {kind: "paid", tool, name, until, usd_task, …} in Needs you (realm/paid.py)
    ideas.paid {yes: bool}  # the person's answer: the yes holds until the reset and the work goes on with the tool billed by its API; a no is not asked again before it

The host returns keys, data and the Orkmaster's one line (`moved.line`); the card's words are the page's. A yes is kept in the Board's state (`<state>/paid.json`).
"""
from __future__ import annotations

import datetime as dt
import time
from typing import Any, Callable

from orkboard.core import bus as b
from orkboard.gui.ideas_args import IdeasError
from orkboard.realm import event_log, harnesses, idea_spend, paid, roles, tool_now

LEARNED_LAST = 10                  # a tool's cost a task is the mean of the Board's last tasks that ended on it


def _iso(epoch: float | None, seconds: bool = False) -> str | None:
    return dt.datetime.fromtimestamp(epoch).isoformat(timespec="seconds" if seconds else "minutes") if epoch is not None else None


class ManaMixin:
    _mana_last: tuple[str, str | None] | None = None      # (the Main tool, the tool now) as the last tick saw them
    _mana_moved: dict | None = None

    def tool_now(self, at: float | None = None) -> dict:
        """The tool now for this Board (see the module's words): None-safe, a host with no machine settings says the Main tool."""
        at = time.time() if at is None else at
        machine = getattr(self.host, "machine", None)
        if machine is None:
            return {"main": "", "now": None, "until": None, "moved_from": None}
        return tool_now.now(machine, list(self.host.limits() or []), at, paid.until(self.state_dir, at), self.settings_now())

    def follow(self) -> str | None:
        """What a resolution that fell to the Main tool falls to: the tool now (None while every tool is out: the work holds on the Main tool)."""
        return self.tool_now()["now"]

    def mana(self, at: float | None = None) -> dict[str, Any]:
        """`{main, now, until, moved}` for the snapshot: `until` is when the Main tool is back (ISO, local) while the work is on another; `moved`, the last change this run
        has seen, `{from, to, until, at, line}` (`to` None while every tool is out; `line` the Orkmaster's words, "" then), else None."""
        got = self.tool_now(at)
        return {"main": got["main"], "now": got["now"], "until": _iso(got["until"]) if got["now"] != got["main"] else None, "moved": self._mana_moved}

    def mana_tick(self, at: float | None = None) -> None:
        """From the clock: when the tool now changed since the last tick, once: `bus.TOOL_MOVED {from, to, until}`, the Orkmaster's line kept in `moved`, and `tool_moved` in the event log.
        The Main tool changed in Settings is not a move; a Board that starts with its Main tool out has moved."""
        at = time.time() if at is None else at
        got = self.tool_now(at)
        main, now = got["main"], got["now"]
        before = self._mana_last
        self._mana_last = (main, now)
        if before is None:
            before = (main, main)
        elif before[0] != main:
            before = (main, main)
        if before[1] == now:
            return
        until = got["until"] if now != main else None
        self._mana_moved = {"from": before[1], "to": now, "until": _iso(until), "at": _iso(at, True), "line": tool_now.line(main, now, until, at)}
        self._ev(event_log.TOOL_MOVED, **{"from": before[1] or "", "to": now or "", "until": until})
        self.host.publish(b.TOOL_MOVED, **{"from": before[1], "to": now, "until": until})
        self.changed("")

    # -- going on paid ---------------------------------------------------------------------------------------

    def usd_task_of(self, tool: str) -> float | None:
        """About what a task costs on this tool: the mean of this Board's last tasks that ended on it and were priced, else what the seats already show for a Grunt's
        (`ideas.roles` `usd_task`); None while nothing is priced."""
        costs = [float(t["cost"]) for _s, _title, plan in self._plans() for t in plan.get("tasks") or []
                 if t.get("tool") == tool and t.get("state") in idea_spend.ENDED and isinstance(t.get("cost"), (int, float)) and not isinstance(t.get("cost"), bool)]
        if costs:
            last = costs[-LEARNED_LAST:]
            return round(sum(last) / len(last), 2)
        grunt = roles.role(self.state_dir, roles.GRUNT)
        if grunt is None:
            return None
        return self._usd_task(grunt, idea_spend.by_role(self.state_dir), idea_spend.tier_costs(self.state_dir), self._target())

    def paid_rows(self) -> list[dict]:
        """The Orkmaster's row `paid` while every subscription is out and a tool billed by its API is turned on (realm/paid.py); [] otherwise, and for a demo."""
        if self.host.demo:
            return []
        at = time.time()
        got = self.tool_now(at)
        machine = getattr(self.host, "machine", None)
        if machine is None or got["now"] is not None:
            return []
        tool = tool_now.api_tool(machine)
        return paid.row(self.state_dir, machine, got, self.usd_task_of(tool) if tool else None, at)

    def paid(self, args: dict) -> dict:
        """`ideas.paid {yes}`: *Go on, paid* (true) keeps the yes until the reset, and the work goes on with the tool billed by its API; *Wait* (false) keeps the wait, and the row is
        not asked again before the reset. Refused when nothing asks it now."""
        yes = args.get("yes")
        if not isinstance(yes, bool):
            raise IdeasError("yes is true or false")
        at = time.time()
        got = self.tool_now(at)
        tool = tool_now.api_tool(self.host.machine)
        if got["now"] is not None or tool is None:
            raise IdeasError("Nothing asks to go on paid now")
        ends = paid.answer(self.state_dir, yes, got["until"], at)
        self._ev(event_log.PAID_ANSWERED, args, tool=tool, yes=yes)
        self.mana_tick(at)
        self.changed("")
        return {"ok": True, "tool": tool, "name": harnesses.title(tool), "until": _iso(ends)}


def mana_commands(ideas_: Any) -> dict[str, Callable[[dict], Any]]:
    """The tool now's commands by name (`gui/ideas.py` adds them to its table: `**mana_commands(self)`)."""
    return {"ideas.paid": ideas_.paid}
