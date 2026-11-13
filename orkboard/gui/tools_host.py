"""The AI tools' own commands (docs/specs/130-the-first-open-is-the-orkmasters.md part A; decisions §232.4, §232.5): the tools found on this computer, a
short request to one (Check), adding one to the hand (Test & add), the order, how each is paid, and putting one back. They were the onboarding's
(`onboarding.check`, `.detect`, `.request`), whose form and names went with spec 130 D.

    th = ToolsHost(host)                    # `host.town`: the machine, `call` and `on_change` (Orkboard's host is its own town)
    host.commands.update(th.commands())     # tools.look · card · check · test_add · put_back · put_back_undo · order · billing · request
    th.snapshot()                           # the snapshot's `tools`: the hand, the order, the main tool, what is being added

    tools.look {}                           # look for the AI tools again (one was just installed): the card says `ready: false` meanwhile
    tools.card {}                           # the card that adds one tool (realm/tool_hand.py `card`); begins the look when it has not been made
    tools.check {tool}                      # one short request to a tool found, on its cheapest tier, on a thread: ✓ and how long, or why it failed
    tools.test_add {tool, billing?, risk_read?}   # Check, and when it answers the tool is in the hand, at the end of the order; nothing is added when it fails
    tools.put_back_plan {tool}              # what putting it back would do, said under the button before it is pressed; changes nothing
    tools.put_back {tool, sure?}            # out of the hand, between tasks; the last tool asks first (`{ok: false, ask}`) unless `sure`
    tools.put_back_undo {undo}              # what the toast's Undo sends back: the record `put_back` gave
    tools.order {order}                     # the person's order (a permutation of the hand); its first tool is the main tool
    tools.billing {tool, billing}           # how a tool in the hand is paid: its subscription, or the API key found in the environment
    tools.request {name, link?, note?}      # a tool the orks cannot run on yet: a filled-in GitHub issue for the browser, nothing sent from here

No key is typed into Orkboard and none is read: the environment is asked for a variable's *name* (`tool_hand.key_found`). Nothing here runs on the
phone (`BoardPhone.COMMANDS` does not list it): the phone shows the tools as before and sets none (§232.10).
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable
from urllib.parse import urlencode

from orkboard import brand, settings, tools
from orkboard.realm import goal_team, harnesses, ideas, tool_errors, tool_hand, tool_run
from orkboard.realm.sign_in import CHECK_PROMPT

ISSUES = "https://github.com/orkCraft/orkBoard/issues/new"


class ToolsError(Exception):
    """A step the page sent that cannot be taken; its text is shown to the person."""


class ToolsHost:
    def __init__(self, host: Any, detect: Callable[[], list[tools.ToolStatus]] | None = None,
                 detect_others: Callable[[], list[tools.Other]] | None = None, ask: Callable[..., Any] | None = None,
                 on_found: Callable[[list[tools.ToolStatus], list[tools.Other]], None] | None = None) -> None:
        self.host = host
        self.statuses: list[tools.ToolStatus] | None = None       # the tools found, None until the look is in
        self.others: list[tools.Other] = []
        self.checks: dict[str, dict] = {}                         # Check: a tool's answer to a short request, or why it gave none
        self.adding: dict[str, dict] = {}                         # Test & add: {tool: {state: running | added | failed, …}}
        self._ask = ask or (lambda tool, prompt, model=None: tool_run.ask(tool, prompt, model))
        self._detectors = (detect or (lambda: tools.detect()), detect_others or (lambda: tools.detect_others()))
        self._on_found = on_found
        self._finder: threading.Thread | None = None
        self._worker: threading.Thread | None = None               # the last Check or Test & add (a test joins it)

    # -- the look ------------------------------------------------------------------------------------

    def scan(self) -> None:
        """The AI tools on a thread (`--version` runs for each); the page shows them when they are in."""
        self.statuses = None
        self.checks = {}
        self._finder = threading.Thread(target=self._detect, args=self._detectors, daemon=True)
        self._finder.start()

    def _detect(self, detect: Callable, detect_others: Callable) -> None:
        try:
            found, others = detect(), detect_others()
        except Exception:                           # a broken tool never stops the first open
            found, others = [], []
        self.host.town.call(self._detected, found, others)

    def _detected(self, found: list[tools.ToolStatus], others: list[tools.Other]) -> None:
        self.statuses, self.others = found, others
        if self._on_found is not None:
            self._on_found(found, others)
        self.host.on_change()

    def _status(self, tool_id: str) -> tools.ToolStatus | None:
        return next((st for st in self.statuses or [] if st.id == tool_id), None)

    # -- the commands ----------------------------------------------------------------------------------

    def commands(self) -> dict[str, Callable[[dict], Any]]:
        return {"tools.look": self.look, "tools.card": self.card, "tools.check": self.check, "tools.test_add": self.test_add,
                "tools.put_back_plan": self.put_back_plan, "tools.put_back": self.put_back, "tools.put_back_undo": self.put_back_undo, "tools.order": self.order,
                "tools.billing": self.billing, "tools.request": self.request}

    @property
    def machine(self) -> settings.MachineSettings:
        return self.host.town.machine

    def look(self, args: dict) -> dict | None:
        """Look for the AI tools again (one was just installed)."""
        self.scan()
        self.host.on_change()
        return None

    def card(self, args: dict) -> dict:
        """The card that adds one tool; the look is begun when it was not made (`ready: false` until it is in: the page is pushed)."""
        if self.statuses is None and (self._finder is None or not self._finder.is_alive()):
            self.scan()
        return tool_hand.card(self.statuses, self.machine)

    def _tool(self, args: dict) -> str:
        tid = str(args.get("tool") or "")
        if harnesses.get(tid) is None:
            raise ToolsError("Say which AI tool")
        return tid

    def check(self, args: dict) -> dict:
        """One short request to a tool found (`tool_run.ask`, its cheapest tier), on a thread. The row shows ✓ and how long the answer took, or what kind of
        failure it was (realm/tool_errors.py)."""
        tid = self._tool(args)
        if not (st := self._status(tid)) or not st.found:
            raise ToolsError("That AI tool is not found here")
        if (self.checks.get(tid) or {}).get("state") == "running":
            return self.snapshot()
        self.checks[tid] = {"state": "running"}
        self._worker = threading.Thread(target=self._check_run, args=(tid,), daemon=True)
        self._worker.start()
        self.host.on_change()
        return self.snapshot()

    def _asked(self, tid: str) -> dict:
        """The request made once: `{state: ok, ms}`, or `{state: failed, kind, line, action, detail, sign_in}` in the tool's words."""
        start = time.monotonic()
        try:
            with tool_errors.doing("check"):
                self._ask(tid, CHECK_PROMPT, "laborer")
            return {"state": "ok", "ms": round((time.monotonic() - start) * 1000)}
        except Exception as e:                      # a timeout or 🛑 Halt All is a failure like any other
            err = e if isinstance(e, tool_errors.ToolError) else tool_errors.ToolError(tid, str(e))
            return {"state": "failed", "kind": err.kind, "line": tool_errors.LINES[err.kind].format(tool=harnesses.title(tid), product=brand.name()),
                    "action": tool_errors.what_to_do(err), "detail": err.detail or str(e),
                    "sign_in": tool_errors.helped(err)}      # its own sign-in can help (spec 45 §7): the card says Sign in

    def _check_run(self, tid: str) -> None:
        self.host.town.call(self._checked, tid, self._asked(tid))

    def _checked(self, tid: str, out: dict) -> None:
        if tid in self.checks:                      # not when a new look began meanwhile
            self.checks[tid] = out
            self.host.on_change()

    # -- Test & add ------------------------------------------------------------------------------------

    def test_add(self, args: dict) -> dict:
        """One short request to the tool's lightest model (on an API key, about $0.001); when it answers, the tool's potion comes into the hand at the end of
        the order. Refused in words (`tool_hand.refusal`): not found or not installed, in the hand already, the hand full, experimental before its warning is
        read, not signed in (on a subscription), no key in the environment (on an API key). A failure says why, in the tool's words, and nothing is added."""
        tid = self._tool(args)
        if self.statuses is None:
            raise ToolsError("The AI tools are being looked for: try again in a moment")
        row = next((r for r in tool_hand.card(self.statuses, self.machine)["tools"] if r["id"] == tid), None)
        st = self._status(tid)
        billing = args.get("billing") if args.get("billing") in tool_hand.BILLINGS else (st.billing if st else "subscription")
        if why := tool_hand.refusal(row, self.machine, billing, None, args.get("risk_read") is True):
            raise ToolsError(why)
        if (self.adding.get(tid) or {}).get("state") == "running":
            return self.snapshot()
        self.adding[tid] = {"state": "running", "billing": billing, "cost": tool_hand.TEST_COST if billing == "api" else ""}
        self._worker = threading.Thread(target=self._add_run, args=(tid, billing), daemon=True)
        self._worker.start()
        self.host.on_change()
        return self.snapshot()

    def _add_run(self, tid: str, billing: str) -> None:
        self.host.town.call(self._added, tid, billing, self._asked(tid))

    def _added(self, tid: str, billing: str, out: dict) -> None:
        if out.get("state") != "ok":
            self.adding[tid] = out
            self.host.on_change()
            return
        if tid in tool_hand.hand(self.machine) or len(tool_hand.hand(self.machine)) >= tool_hand.HAND_MAX:     # filled meanwhile: nothing is added twice
            self.adding.pop(tid, None)
            self.host.on_change()
            return
        tool_hand.add(self.machine, tid, billing)
        self.machine.onboarded = True                               # the machine is set up
        self._saved()
        n = len(tool_hand.hand(self.machine))
        self.adding[tid] = {"state": "added", "ms": out.get("ms"), "title": harnesses.title(tid), "n": n, "full": n >= tool_hand.HAND_MAX,
                            "line": f"{harnesses.title(tid)} is in your hand. Add another AI tool?" if n < tool_hand.HAND_MAX else f"{harnesses.title(tid)} is in your hand."}
        self.host.on_change()

    def _saved(self) -> None:
        settings.save(self.machine)
        follow = getattr(self.host, "_follow_main", None)           # the tool now is read again for what has no Board to ask
        if callable(follow):
            follow()

    # -- the order, the billing, Put back -----------------------------------------------------------------

    def order(self, args: dict) -> dict:
        """The person's order (dragging a potion, or ← and →): a permutation of the hand, kept as `machine.tool_order`; its first tool is the main tool."""
        try:
            tool_hand.reorder(self.machine, args.get("order"))
        except ValueError as e:
            raise ToolsError(str(e)) from None
        self._saved()
        self.host.on_change()
        return self.snapshot()

    def billing(self, args: dict) -> dict:
        """How a tool in the hand is paid: *Subscription*, or *API key*, which needs a key already in the environment (named, never read out)."""
        tid, billing = self._tool(args), args.get("billing")
        if tid not in tool_hand.hand(self.machine):
            raise ToolsError("That AI tool is not in your hand")
        if billing not in tool_hand.BILLINGS:
            raise ToolsError("A tool is paid by its subscription or by its API key")
        st = self._status(tid)
        line = tool_hand.third_line(tid, billing, st.logged_in if st else None)
        if line["state"] in ("no_key", "signed_out"):
            raise ToolsError(line["line"] if line["state"] == "no_key" else f"{harnesses.title(tid)} is not signed in: sign in first")
        self.machine.tools[tid] = settings.ToolChoice(enabled=True, billing=billing)
        self._saved()
        self.host.on_change()
        return {**self.snapshot(), "line": line}

    def _parties_on(self, tool_id: str) -> list[dict]:
        """The parties of the open projects that are set to the tool by name (spec 81's `tool`); the Main tool's followers are not named."""
        out = []
        for project in getattr(getattr(self.host, "projects", None), "open_ones", []) or []:
            try:
                for t in ideas.tracks(project.root, make=False):
                    if goal_team.tool_of(project.root, t["slug"]) == tool_id:
                        out.append({"slug": t["slug"], "name": t["title"], "project": project.path})
            except OSError:
                continue
        return out

    def _project(self, path: str) -> Any:
        return next((p for p in getattr(getattr(self.host, "projects", None), "open_ones", []) or [] if p.path == path), None)

    def put_back_plan(self, args: dict) -> dict:
        """What putting the tool back would do (`tool_hand.put_back_plan`): the orks stop using it after the task at work, each party set to it by name and what it goes
        on with, and, for the last tool, the question. It changes nothing."""
        tid = self._tool(args)
        if tid not in tool_hand.hand(self.machine):
            raise ToolsError("That AI tool is not in your hand")
        return tool_hand.put_back_plan(self.machine, tid, self._parties_on(tid))

    def put_back(self, args: dict) -> dict:
        """The tool out of the hand. **Between tasks, never inside one** (§177.2): a task at work goes on with it until it is done, because a tool is resolved
        when a task starts; no later one starts on it. Each party set to it by name goes on with the next tool in the hand (set to it). **The last tool**
        asks first (`{ok: false, ask, plan}` with nothing changed) unless `sure` is true. Answers `{ok: true, plan, undo}`; `undo` is what `put_back_undo` takes
        (the toast's Undo)."""
        tid = self._tool(args)
        if tid not in tool_hand.hand(self.machine):
            raise ToolsError("That AI tool is not in your hand")
        on = self._parties_on(tid)
        plan = tool_hand.put_back_plan(self.machine, tid, on)
        if plan["last"] and args.get("sure") is not True:
            return {"ok": False, "ask": plan["ask"], "plan": plan}
        undo = tool_hand.take_out(self.machine, tid)
        undo["parties"] = []
        for p in on:
            project = self._project(p["project"])
            if project is not None and plan["next"]:
                goal_team.set_tool(project.root, p["slug"], plan["next"])
                project.ideas.changed("")
                undo["parties"].append({"project": p["project"], "slug": p["slug"]})
        self.adding.pop(tid, None)
        self._saved()
        self.host.on_change()
        return {"ok": True, "plan": plan, "undo": undo}

    def put_back_undo(self, args: dict) -> dict:
        """The toast's Undo: the tool back at its place, paid as it was, the main tool again when it was, and the parties set to it again."""
        undo = args.get("undo")
        if not isinstance(undo, dict):
            raise ToolsError("There is nothing to undo")
        if len(tool_hand.hand(self.machine)) >= tool_hand.HAND_MAX and undo.get("tool") not in tool_hand.hand(self.machine):
            raise ToolsError(f"Your hand holds {tool_hand.HAND_MAX} AI tools: put one back first")
        try:
            tool_hand.restore(self.machine, undo)
        except ValueError as e:
            raise ToolsError(str(e)) from None
        for p in undo.get("parties") or []:
            project = self._project(str(p.get("project") or "")) if isinstance(p, dict) else None
            if project is not None:
                try:
                    goal_team.set_tool(project.root, str(p.get("slug") or ""), str(undo["tool"]))
                    project.ideas.changed("")
                except ValueError:
                    continue
        self._saved()
        self.host.on_change()
        return self.snapshot()

    # -- a tool the orks cannot run on ---------------------------------------------------------------------

    def request(self, args: dict) -> dict:
        """A tool the orks cannot run on yet: a filled-in GitHub issue for the browser. Nothing is sent from here."""
        name = str(args.get("name") or "").strip()[:80]
        if not name:
            raise ToolsError("Name the tool")
        link = str(args.get("link") or "").strip()[:300]
        note = str(args.get("note") or "").strip()[:1000]
        body = "\n\n".join(x for x in (f"Tool: {name}", f"Link: {link}" if link else "",
                                       f"What orks would do with it: {note}" if note else "") if x)
        return {"url": f"{ISSUES}?{urlencode({'title': f'Support {name}', 'body': body, 'labels': 'tool request'})}"}

    # -- what the page sees --------------------------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """The snapshot's `tools`: `{hand: [{id, title, mark, billing, main, version, check, lines}], order, main, max, full, looked, adding}` (`lines`: the third line of a tool's card, by how it is paid; `looked`: the look is in). Nothing secret: a key is named at most,
        in a card's line, never read out."""
        inn = tool_hand.hand(self.machine)
        main = settings.main_tool(self.machine) if inn else ""
        have = {st.id: st for st in self.statuses or []}
        rows = []
        for t in inn:
            h = harnesses.get(t)
            rows.append({"id": t, "title": harnesses.title(t), "mark": h.mark if h else "", "billing": self.machine.tools[t].billing, "main": t == main,
                         "version": have[t].version if t in have else "", "check": self.checks.get(t),
                         "lines": {b: tool_hand.third_line(t, b, have[t].logged_in if t in have else None) for b in tool_hand.BILLINGS}})
        return {"hand": rows, "order": inn, "main": main, "max": tool_hand.HAND_MAX, "full": len(inn) >= tool_hand.HAND_MAX, "looked": self.statuses is not None,
                "adding": {k: dict(v) for k, v in self.adding.items()}}

