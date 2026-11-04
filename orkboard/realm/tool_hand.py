"""The AI tools in the hand: what the adding card shows, what is refused, the order, and what putting one back does
(docs/specs/130-the-first-open-is-the-orkmasters.md part A; decisions §232.4, §232.5). Pure: it reads the machine's settings, the tools found
(`tools.detect`) and the environment's *names*; it runs no tool, writes nothing and has no face. The host's commands are gui/tools_host.py.

    tool_hand.hand(machine)                         # the tools in the hand, in the person's order (`settings.tool_order`)
    tool_hand.key_found("claude", env)              # the NAME of the variable that holds a key the tool takes ("" with none); never its value
    tool_hand.third_line("codex", "api", True, env) # the card's third line: {state, line, needs, var, warn, cost}
    tool_hand.card(statuses, machine, env)          # the adding card: {n, max, full, tools: [row], first}
    tool_hand.refusal(row, machine, billing, env, risk_read)   # "" when Test & add may go on, else why not, in words
    tool_hand.add(machine, "codex", "api")          # in the hand, at the end of the order (the main tool when the hand was empty)
    tool_hand.put_back_plan(machine, "claude", parties)        # what putting it back would do, said before it is done
    tool_hand.take_out(machine, "claude")           # out of the hand; the undo record
    tool_hand.restore(machine, undo)                # …and back as it was
    tool_hand.reorder(machine, ["codex", "claude"]) # the person's order (a permutation of the hand); its first is the main tool

A tool is **in the hand or not** (§232.4): there is no third state. The interface says *AI tool*, *Add an AI tool*, *Test & add*, *Put back*.
"""
from __future__ import annotations

import os
from typing import Any, Iterable, Mapping

from orkboard import settings
from orkboard.realm import harnesses, tool_errors

HAND_MAX = 6                                                     # the most tools in the hand (§232.4: "up to six")
READY, SIGNED_OUT, NOT_INSTALLED = "ready", "signed_out", "not_installed"
GROUPS = (READY, SIGNED_OUT, NOT_INSTALLED)                      # the adding card's groups, in the order it shows them (toolpick.js's three)
# The variables a tool takes a key from: `tool_errors.TAKES_KEYS` alone, the keys that win over a sign-in. Antigravity is not in it: with GEMINI_API_KEY
# set and no Google sign-in, agy 1.5.0 asked for the sign-in and ran nothing (decisions §250.5), so no key is promised for it until one is shown to work
# (spec 143 D.5). Only the names are read here, never a value.
KEYS: dict[str, tuple[str, ...]] = dict(tool_errors.TAKES_KEYS)
BILLINGS = settings.BILLINGS
TEST_COST = "about $0.001"                                       # what Test & add costs on an API key, said under the button


def hand(machine: Any) -> list[str]:
    """The tools in the hand, in the person's order: the potions left to right, the first the main tool's place."""
    return settings.tool_order(machine)


def key_found(tool_id: str, env: Mapping[str, str] | None = None) -> str:
    """The name of the first variable of the tool's keys that is set in the environment, "" with none. The value is never read out, kept or sent."""
    env = os.environ if env is None else env
    return next((v for v in KEYS.get(tool_id, ()) if env.get(v)), "")


def third_line(tool_id: str, billing: str, logged_in: bool | None, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """The card's third line, the one that follows *AI tool* and *Paid by* (§232.4): `{state, line, needs, var, warn, cost}`.
    `state` is `ok` (Test & add may go on), `unknown` (the sign-in cannot be told without a request: it may go on, the request tells), `signed_out`
    (`needs: "sign_in"`: spec 45's sign-in) or `no_key` (`needs: "key"`, `var` the variable to set). `warn` says a key that would win over the subscription
    before it costs; `cost` says what the tool is paid by."""
    title = harnesses.title(tool_id)
    named = key_found(tool_id, env)
    if billing == "api":
        if named:
            return {"state": "ok", "line": f"Uses the key in your environment: {named}", "needs": "", "var": named, "warn": "",
                    "cost": "Paid per token, by that key"}
        var = (KEYS.get(tool_id) or ("",))[0]
        say = (f"No key found: set {var} in your environment, then Test again" if var else
               "Antigravity signs in with Google; it takes no key here." if tool_id == "agy" else
               f"No key {title} takes is known here: use its subscription")
        return {"state": "no_key", "line": say, "needs": "key", "var": var, "warn": "", "cost": ""}
    warn = f"{named} is set in your environment: {title} uses it before your subscription and is paid per token." if named else ""
    if logged_in is False:
        return {"state": "signed_out", "line": "Not signed in", "needs": "sign_in", "var": "", "warn": warn, "cost": ""}
    if logged_in is None:
        return {"state": "unknown", "line": "Sign-in not checked: Test & add will tell", "needs": "", "var": "", "warn": warn, "cost": "Paid by your subscription"}
    return {"state": "ok", "line": "Signed in to your subscription", "needs": "", "var": "", "warn": warn, "cost": "Paid by your subscription"}


def group_of(found: bool, logged_in: bool | None) -> str:
    return NOT_INSTALLED if not found else SIGNED_OUT if logged_in is False else READY


def card(statuses: Iterable[Any] | None, machine: Any, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """The card that adds one tool: `{ready, n, max, full, tools, first}`. `tools` are the tools found on this computer that are not in the hand
    yet, ready first, then not signed in, then not installed, each group in the registry's order; a row is `{id, title, mark, group, version, risk,
    install, login, billing, lines: {subscription, api}, pickable}`, a tool not installed with how to install it and never pickable. `first` is the first
    ready tool, the one the card opens on picked ("" with none). `ready` is false until the tools were looked for."""
    inn = hand(machine)
    if statuses is None:
        return {"ready": False, "n": len(inn), "max": HAND_MAX, "full": len(inn) >= HAND_MAX, "tools": [], "first": ""}
    rows = []
    for st in statuses:
        if st.id in inn or not st.tool.available:
            continue
        h = harnesses.get(st.id)
        rows.append({"id": st.id, "title": st.tool.title, "mark": h.mark if h else "", "group": group_of(st.found, st.logged_in), "version": st.version,
                     "risk": harnesses.risky(st.id), "install": st.tool.install, "login": st.tool.login, "billing": st.billing,
                     "lines": {b: third_line(st.id, b, st.logged_in, env) for b in BILLINGS}, "pickable": st.found})
    rows.sort(key=lambda r: GROUPS.index(r["group"]))                  # a stable sort: the registry's order within a group
    first = next((r["id"] for r in rows if r["group"] == READY and not r["risk"]), "")
    return {"ready": True, "n": len(inn), "max": HAND_MAX, "full": len(inn) >= HAND_MAX, "tools": rows, "first": first}


def refusal(row: Mapping[str, Any] | None, machine: Any, billing: str, env: Mapping[str, str] | None = None, risk_read: bool = False) -> str:
    """Why Test & add may not go on ("" when it may), in the words the card shows. `row` is the tool's row of `card` (None: not found)."""
    if row is None:
        return "That AI tool is not found here"
    title = row["title"]
    if row["id"] in hand(machine):
        return f"{title} is in your hand already"
    if len(hand(machine)) >= HAND_MAX:
        return f"Your hand holds {HAND_MAX} AI tools: put one back to add {title}"
    if not row["pickable"]:
        return f"{title} is not installed: {row['install']}"
    if billing not in BILLINGS:
        return "A tool is paid by its subscription or by its API key"
    if row["risk"] and risk_read is not True:
        return f"{title} is experimental: read its warning first"
    line = row["lines"][billing]
    if line["state"] == "signed_out":
        return f"{title} is not signed in: sign in first ({row['login']})"
    if line["state"] == "no_key":
        return line["line"]
    return ""


def add(machine: Any, tool_id: str, billing: str) -> None:
    """The tool in the hand: turned on, paid as said, at the end of the order. The first tool in an empty hand is the main tool (the first potion, framed)."""
    empty = not hand(machine)
    machine.tools[tool_id] = settings.ToolChoice(enabled=True, billing=billing if billing in BILLINGS else "subscription")
    machine.tool_order = [*[t for t in machine.tool_order if t != tool_id], tool_id]
    if empty:
        machine.main_tool = tool_id


def next_after(order: list[str], tool_id: str) -> str | None:
    """The tool the work goes on with when `tool_id` is out: the next in the order, round again (realm/tool_now.py's), None when it is the only one."""
    rest = [t for t in order if t != tool_id]
    if not rest:
        return None
    if tool_id not in order:
        return rest[0]
    at = order.index(tool_id)
    return ([*order[at + 1:], *order[:at]] or rest)[0]


def put_back_plan(machine: Any, tool_id: str, parties: Iterable[Mapping[str, Any]] = ()) -> dict[str, Any]:
    """What putting the tool back would do, said before it is done: `{tool, title, last, next, parties, line, ask}`. `parties` are the parties set to it
    by name (`{slug, name}`); each goes on with `next`, the next tool in the hand. The last tool asks first (§232.5)."""
    inn = hand(machine)
    nxt = next_after(inn, tool_id)
    title = harnesses.title(tool_id)
    on = [{"slug": p["slug"], "name": p.get("name") or p["slug"], "goes_on_with": nxt,
           "line": f"{p.get('name') or p['slug']} is set to {title}: " + (f"it goes on with {harnesses.title(nxt)}, the next in your hand" if nxt else "it waits until you add a tool")}
          for p in parties]
    last = tool_id in inn and not [t for t in inn if t != tool_id]
    return {"tool": tool_id, "title": title, "last": last, "next": nxt, "parties": on, "line": "The orks stop using it after the task at work",
            "ask": "Without it nothing is worked on: goals wait in the Orkmaster's column until you add a tool" if last else ""}


def take_out(machine: Any, tool_id: str) -> dict[str, Any]:
    """The tool out of the hand (turned off, out of the order); the record `restore` needs: `{tool, billing, at, main}`. The main tool's place passes to the
    first of the hand that is left (None: `main_tool` empty). ValueError for a tool that is not in the hand."""
    inn = hand(machine)
    if tool_id not in inn:
        raise ValueError("That AI tool is not in your hand")
    undo = {"tool": tool_id, "billing": machine.tools[tool_id].billing, "at": inn.index(tool_id), "main": settings.main_tool(machine) == tool_id}
    machine.tools[tool_id] = settings.ToolChoice(enabled=False, billing=machine.tools[tool_id].billing)
    machine.tool_order = [t for t in inn if t != tool_id]
    if machine.main_tool == tool_id or undo["main"]:
        machine.main_tool = machine.tool_order[0] if machine.tool_order else ""
    return undo


def restore(machine: Any, undo: Mapping[str, Any]) -> None:
    """Undo of `take_out`: the tool back at its place, paid as it was, the main tool again when it was. ValueError for a record that is none."""
    tool_id, billing = undo.get("tool"), undo.get("billing")
    if tool_id not in harnesses.ids() or billing not in BILLINGS:
        raise ValueError("There is nothing to undo")
    inn = [t for t in hand(machine) if t != tool_id]
    at = undo.get("at")
    inn.insert(at if isinstance(at, int) and not isinstance(at, bool) and 0 <= at <= len(inn) else len(inn), tool_id)
    machine.tools[tool_id] = settings.ToolChoice(enabled=True, billing=billing)
    machine.tool_order = inn
    if undo.get("main") is True:
        machine.main_tool = tool_id


def reorder(machine: Any, order: object) -> list[str]:
    """The person's order: a permutation of the hand (nothing added, nothing left out; ValueError in words otherwise). Its first tool is the main tool."""
    inn = hand(machine)
    if not isinstance(order, list) or sorted(map(str, order)) != sorted(inn):
        raise ValueError("The order names the AI tools in your hand, each once")
    machine.tool_order = [str(t) for t in order]
    machine.main_tool = machine.tool_order[0] if machine.tool_order else ""
    return list(machine.tool_order)
