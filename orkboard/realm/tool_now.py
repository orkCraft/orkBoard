"""The tool now, and moving on (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §2; decisions §177.2): the AI tool the work goes
to when it follows the Main tool. A pure read of the machine's tools, the quota readers' last read and the clock; it writes nothing,
starts nothing and has no face.

    tool_now.now(machine, limits, at, paid_until=None, board=None)   # {main, now, until, moved_from}
    tool_now.follow(kept, main)                                      # what a resolution that fell to the Main tool falls to
    tool_now.keep(result) / tool_now.following(main)                 # the host's last read, for a caller that has no host (tiers, a step's tool)
    tool_now.line(main, now, until, at)                              # the Orkmaster's words, once, when it moves (or is back)

**The Main tool** (`settings.main_tool`) while it has room: no window of it spent or nearly spent (`status.reset_of(…, NEARLY)`, the test the runner's
hold uses) and, with the Board's settings given (`board`), not at the reserve (`idea_target.reserve_held`). Else **the next tool in the order** (the
potions': `settings.tool_order`, after the Main tool and round again) **that has room and is billed by subscription**. Else, while a yes to go on paid
holds (`paid_until` in the future), the first tool in the order billed by its API. Else `now` is None and `until` the soonest reset among the
subscriptions (the Orkmaster asks, `realm/paid.py`). A tool turned on with no limits read has room. A Main tool billed by its API never runs dry.

`until` is when the Main tool is back (the latest of its windows' resets, else its reserve's), while the work is on another tool; None when it is
on the Main tool. `moved_from` is the Main tool while it is on another (or on none), else None.

Only a resolution that falls to the Main tool follows: a seat's or a party's own tool was set on purpose and is never moved. The tool is resolved when
a task (or step) starts, as ever; a run that hits its limit mid-run holds and its next start resolves again.
"""
from __future__ import annotations

import threading
import time
from typing import Any

from orkboard import settings
from orkboard.realm import harnesses, idea_target, status

PAID_HOLD_S = 5 * 3600            # a yes to go on paid when no subscription's reset is known: it holds for the five-hour window


def room(limits: list, tool: str, at: float, board: dict | None = None) -> bool:
    """Whether the tool can take work that starts now: none of its windows spent or nearly spent and, given the Board's settings, not at its reserve."""
    return back_at(limits, tool, at, board) is None


def back_at(limits: list, tool: str, at: float, board: dict | None = None) -> float | None:
    """When the tool has room again (epoch seconds): the latest reset of its windows nearly spent, else its reserve's; None when it has room now."""
    got = [status.reset_of(limits, tool, at, status.NEARLY)]
    if board is not None:
        got.append(idea_target.reserve_held(limits, board, at, tool))
    got = [g for g in got if g is not None]
    return max(got) if got else None


def now(machine: Any, limits: list | None, at: float | None = None, paid_until: float | None = None, board: dict | None = None) -> dict:
    """`{main, now, until, moved_from}` (see the module's words). `limits`: the quota readers' last read; `at`: epoch seconds; `board`: the
    Board's settings (their reserves), given where the reserve holds the work too."""
    at = time.time() if at is None else at
    limits = list(limits or [])
    main = settings.main_tool(machine)
    tools = machine.tools
    order = settings.tool_order(machine)
    out = {"main": main, "now": main, "until": None, "moved_from": None}
    if tools.get(main) is not None and tools[main].billing == "api":      # paid by the person's own choice: it has no window to run dry
        return out
    gone = back_at(limits, main, at, board)
    if gone is None:
        return out
    start = order.index(main) if main in order else None
    after = order if start is None else [*order[start + 1:], *order[:start]]         # the next in the order, round again
    subs = [t for t in after if t != main and tools[t].billing == "subscription"]
    pick = next((t for t in subs if room(limits, t, at, board)), None)
    out.update(until=gone, moved_from=main)
    if pick is not None:
        out["now"] = pick
        return out
    out["now"] = None
    resets = [r for t in [main, *subs] if (r := back_at(limits, t, at, board)) is not None]
    out["until"] = min(resets) if resets else gone
    if paid_until is not None and paid_until > at:
        paid = next((t for t in order if tools[t].billing == "api"), None)
        if paid is not None:
            out["now"] = paid
    return out


def api_tool(machine: Any) -> str | None:
    """The first tool turned on and billed by its API, in the order; None with none (nothing to ask a yes for)."""
    return next((t for t in settings.tool_order(machine) if machine.tools[t].billing == "api"), None)


def follow(kept: dict | None, main: str) -> str:
    """The tool a resolution that falls to the Main tool goes to: the tool now of a read (`now`) made for that Main tool, else the Main tool
    itself (no read, a read of another Main tool, or every tool out: the work holds there as it did)."""
    if kept and kept.get("main") == main and kept.get("now"):
        return str(kept["now"])
    return main


_KEPT: dict = {}
_LOCK = threading.Lock()


def keep(result: dict | None) -> None:
    """The host's last read, for a caller that has no host to ask (the tiers' `main`, a step's tool): the machine's, without a project's yes to go on paid."""
    with _LOCK:
        _KEPT.clear()
        _KEPT.update(result or {})


def following(main: str) -> str:
    """The tool a caller with no host falls to for `main`: `follow` of the host's last read."""
    with _LOCK:
        return follow(dict(_KEPT), main)


def line(main: str, to: str | None, until: float | None, at: float) -> str:
    """The Orkmaster's words, once, when the work moves (or is back), in plain words: *Claude Code is out until Thu 18:00: the work goes on with Codex.*,
    *Claude Code is back: the work goes on with it.*; while every tool is out (`to` None) the card asks instead and there are none ("")."""
    if not to:
        return ""
    name = harnesses.title(main)
    if to == main:
        return f"{name} is back: the work goes on with it."
    when = f" until {idea_target.when_words(until, at)}" if until is not None else ""
    return f"{name} is out{when}: the work goes on with {harnesses.title(to)}."


def pinned_line(tool: str, until: float, at: float) -> str:
    """What a task holds for when its tool was set on purpose (a seat's or a party's: never moved): *Waits for Codex's limit until Thu 18:00: Codex is set for it on purpose,
    so the work does not move on.*"""
    name = harnesses.title(tool)
    return f"Waits for {name}'s limit until {idea_target.when_words(until, at)}: {name} is set for it on purpose, so the work does not move on."
