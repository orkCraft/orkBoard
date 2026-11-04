"""The onboarding's first screen (docs/design/gui-onboarding.md; spec 37 §4): your AI tools, found on this machine,
each with a Check, the warning of an experimental one, and a request for one the orks cannot run on yet. Orkboard's:
it opens on a machine never set up and closes on Open the board (`onboarding.skip`), the tools found kept on; no
class, no Mission 1 and no town.

Orkline's onboarding (gui/onboarding_town.py) is this screen and its own steps after it: who you are, the MCP
servers, your first town and the town going up while you watch.

    ob = Onboarding(host)                 # active on a machine never set up, unless ORKCRAFT_ONBOARDING=0
    host.commands.update(ob.commands())   # onboarding.tools · .check · .detect · .request · .skip · .close · .cancel
                                          # (.check, .detect and .request are aliases: the tools' own commands are `tools.*`, gui/tools_host.py)
    ob.snapshot()                         # the snapshot's `onboarding`, None when there is none
    ob.tick(now)                          # from the host's clock (the town's raising, in Orkline)

The host is read as `host.town` (its machine, demo, call and toast: Orkline's town, Orkboard's `BoardHost`) and
`host.on_change`.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable

from orkboard import settings, tools
from orkboard.env import getenv
from orkboard.gui import tools_host
from orkboard.gui.tools_host import ISSUES, ToolsError   # noqa: F401  (ISSUES: re-exported)
from orkboard.realm import harnesses
from orkboard.realm.sign_in import CHECK_PROMPT   # noqa: F401  (a short real request, on the tool's cheapest tier)

TOOLS, WHO, MCP, TOWN, SURVEY, RAISING = "tools", "who", "mcp", "town", "survey", "raising"
RAISE_STEP_S = 0.8          # between two raising steps of the town (gui/onboarding_town.py): each building seen going up
RECOMMENDED = ("claude", "codex", "cursor")    # what the step offers to install when no AI tool is here


class OnboardingError(Exception):
    """A step the page sent that cannot be taken; its text is shown to the person."""


def off() -> bool:
    return getenv("ONBOARDING").lower() in ("0", "false", "no", "off")


class Onboarding:
    def __init__(self, host, detect: Callable[[], list[tools.ToolStatus]] | None = None,
                 detect_others: Callable[[], list[tools.Other]] | None = None,
                 ask: Callable[..., Any] | None = None) -> None:
        self.host = host
        self.again = False              # opened from the map's menu on a town that stands (Orkline's Set up again)
        self.step = TOOLS
        self.picked: dict[str, settings.ToolChoice] = {}
        self.warder = True
        # the tools found, a Check, the look itself: the tools' own (gui/tools_host.py), which this screen reads
        self.tools_host = tools_host.ToolsHost(host, detect, detect_others, ask, on_found=self._found)
        self.active = self.wanted()
        if self.active:
            self._look()

    @property
    def statuses(self) -> list[tools.ToolStatus] | None:
        return self.tools_host.statuses

    @property
    def others(self) -> list[tools.Other]:
        return self.tools_host.others

    @property
    def checks(self) -> dict[str, dict]:
        return self.tools_host.checks

    @property
    def _finder(self):
        return self.tools_host._finder

    @property
    def _ask(self):
        return self.tools_host._ask

    @_ask.setter
    def _ask(self, ask) -> None:
        self.tools_host._ask = ask

    def _check_run(self, tid: str) -> None:
        """The Check's request, run now (on its own thread in `tools.check`): the tools' own."""
        self.tools_host._check_run(tid)

    def wanted(self) -> bool:
        """Orkboard opens on no form: the first open is the Orkmaster's (docs/specs/130 D.2; hand/setupcards.js, hand/addtool.js)."""
        return False

    def _look(self) -> None:
        """The AI tools on a thread (`--version` runs for each)."""
        self.tools_host.scan()

    # -- what the page sees ------------------------------------------------------------------------

    def _found(self, found: list[tools.ToolStatus], others: list[tools.Other]) -> None:
        """The tools found are in: what is picked, as this screen shows it (the tools' own is `tools_host`)."""
        kept = self.host.town.machine.tools if self.again else {}    # set up again: what was chosen stays
        # an experimental tool (agy) is never on by default: the person turns it on after its warning
        self.picked = {st.id: kept.get(st.id) or settings.ToolChoice(
                           enabled=st.found and st.tool.available and not harnesses.risky(st.id), billing=st.billing)
                       for st in found}

    def steps(self) -> list[str]:
        """The steps of this run, from what is known so far: the first screen alone in Orkboard."""
        return [TOOLS]

    def _tools_rows(self) -> list[dict]:
        rows = []
        for st in self.statuses or []:
            if not st.found:
                continue
            choice = self.picked.get(st.id, settings.ToolChoice())
            h = harnesses.get(st.id)
            rows.append({"id": st.id, "title": st.tool.title, "mark": h.mark if h else "", "version": st.version,
                         "logged_in": st.logged_in, "login": st.tool.login, "enabled": choice.enabled, "billing": choice.billing,
                         "check": self.checks.get(st.id), "risk": harnesses.risky(st.id)})
        return rows

    @staticmethod
    def _recommended() -> list[dict]:
        """What the step offers when no AI tool is here: how to install each and sign in (harnesses.REGISTRY)."""
        out = []
        for tid in RECOMMENDED:
            h = harnesses.get(tid)
            if h is not None:
                out.append({"id": h.id, "title": h.title, "mark": h.mark, "install": h.install, "login": h.login})
        return out

    def _not_run_on(self) -> dict:
        """The tools the orks don't run on here: `missing` (not found), `others` (found, but no harness) and `cli`
        (an app here whose CLI the orks run on is not: Cursor's editor without cursor-agent). A tool found
        is never named again below the table."""
        statuses = self.statuses or []
        found = {st.id for st in statuses if st.found}
        others = [o for o in self.others if o.id not in found]
        cli = {o.id: h for o in others if (h := harnesses.get(o.id))}
        return {"missing": [st.tool.title for st in statuses if not st.found and st.id not in cli],
                "others": [{"id": o.id, "title": o.title} for o in others if o.id not in cli],
                "cli": [{"id": o.id, "title": o.title, "bin": cli[o.id].bin} for o in others if o.id in cli]}

    def snapshot(self) -> dict[str, Any] | None:
        if not self.active:
            return None
        steps = self.steps()
        return {
            "step": self.step, "steps": steps,
            "n": steps.index(self.step) if self.step in steps else len(steps) - 1,
            "tools": {"ready": self.statuses is not None, "rows": self._tools_rows(), **self._not_run_on(),
                      "warder": self.warder, "warder_agy": self._warder_agy(), "recommended": self._recommended()},
            "tool_titles": {t.id: t.title for t in tools.TOOLS},
            "again": self.again,
            "raising": None,
        }

    # -- the page's commands -----------------------------------------------------------------------

    def commands(self) -> dict[str, Callable[[dict], Any]]:
        return {"onboarding.skip": self.skip, "onboarding.close": self.close, "onboarding.cancel": self.cancel}

    def _warder_agy(self) -> str:
        """What the guard step says about agy when agy is chosen (Orkline's: the Security reviewer guards its town)."""
        return ""

    def _enabled(self) -> list[str]:
        machine = self.host.town.machine
        return [t for t, c in {**machine.tools, **self.picked}.items() if c.enabled]

    def cancel(self, args: dict) -> None:
        """Set up again, left without saving (a first run has no way out but Skip)."""
        if self.again:
            self.active = self.again = False
            self.host.on_change()

    def _live(self) -> None:
        if not self.active or self.step == RAISING:
            raise OnboardingError("The onboarding is not open")

    def _go(self, after: str) -> dict | None:
        """The first screen answered: the tools are saved and the board opens."""
        self._save_machine()
        self.active = False
        self.host.on_change()
        return None

    def skip(self, args: dict) -> dict | None:
        """Open the board: the tools found kept on, saved; nothing else is set up."""
        self._live()
        return self._go(TOOLS)

    def close(self, args: dict) -> None:
        """The first screen leaves the page (Orkline's: once its town stands)."""
        self.active = False
        self.host.on_change()

    def _save_machine(self) -> None:
        town = self.host.town
        m = town.machine
        tools_ = dict(m.tools)
        tools_.update(self.picked)
        town.machine = replace(m, tools=tools_, onboarded=True)
        settings.save(town.machine)

    def tick(self, now: float | None = None) -> None:
        """Nothing goes up in Orkboard (Orkline's raises its town, one step a tick)."""
