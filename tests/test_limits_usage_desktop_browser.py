"""Spec 91 B on the desktop (docs/specs/91-the-owners-list.md §2, decisions §107; js/arena/limits.js): the panel of one tool's limit, in a real browser at
1 440 × 900 against a stub host that answers `ideas.usage` in its shape. `<Limits provider=…>` is mounted on the page as the top bar mounts it
in a chip's panel: the tool's line, the switch *This project* / *All projects* (only when the host's `scopes` has "all"), a row a party with a thin
meter and its share and a smaller row a member under it, *Outside Orkboard*, and the line that says every share is an estimate; the switch asks
again with its scope; tokens only when the limit was not read twice; a host that cannot tell says so; `<Limits />` with no provider is the
tool lines as before."""
from __future__ import annotations

import copy
import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import ArenaHost  # noqa: E402
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _calls, _open  # noqa: E402

pytestmark = pytest.mark.browser

PROJECT = {"provider": "claude", "name": "Claude", "left": 0.62, "window": "5h", "reset": "2099-01-01T18:00", "scope": "project", "scopes": ["project", "all"],
           "rows": [{"party": "passkey", "title": "Sign in with a passkey", "share": 18, "tokens": 90_000,
                     "members": [{"agent": "backend", "name": "Backend", "share": 12, "tokens": 60_000}, {"agent": "screens", "name": "Screens", "share": 6, "tokens": 30_000}]},
                    {"party": "pricing", "title": "Pricing page", "share": 7, "tokens": 35_000,
                     "members": [{"agent": "taskmaster", "name": "Taskmaster", "share": 7, "tokens": 35_000}]},
                    {"party": "weekly", "title": "Weekly report email", "share": 0, "tokens": 800,
                     "members": [{"agent": "grunt", "name": "Grunt", "share": 0, "tokens": 800}]}],
           "outside": 9, "estimated": True, "tokens_only": False}
EVERYWHERE = {**PROJECT, "scope": "all", "rows": [{"party": "/work/shop::passkey", "title": "Sign in with a passkey · shop", "share": 30, "tokens": 150_000,
                                                      "members": [{"agent": "backend", "name": "Backend", "share": 30, "tokens": 150_000}]}], "outside": 4}
TOKENS = {**PROJECT, "rows": [{"party": "passkey", "title": "Sign in with a passkey", "share": None, "tokens": 12_400,
                               "members": [{"agent": "backend", "name": "Backend", "share": None, "tokens": 12_400}]}], "outside": 0, "tokens_only": True}

MOUNT = """async (provider) => {
  const { render, h } = await import("preact");
  const { Limits } = await import("/static/js/arena/limits.js");
  document.getElementById("usage-probe")?.remove();
  const el = document.createElement("div");
  el.id = "usage-probe";
  el.style.cssText = "position:fixed;top:60px;right:16px;width:312px;z-index:90;background:var(--ork-panel);padding:8px 12px";
  document.body.append(el);
  render(h(Limits, provider ? { provider } : {}), el);
}"""


class UsageHost(ArenaHost):
    """The arena's world with `ideas.usage` answering as the host does; `usage=None`: a host from before spec 91 (the command is refused)."""

    def __init__(self, usage=None, refuse=False):
        super().__init__()
        self.usage, self.refuse = usage if usage is not None else {"project": copy.deepcopy(PROJECT), "all": copy.deepcopy(EVERYWHERE)}, refuse

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            if m["name"] == "ideas.usage" and self.refuse:
                self.log.append((m["name"], m["args"]))
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": False, "error": "Unknown command ideas.usage"}))
                return
            ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}))
        ws.on_message(on_message)

    def handle(self, name, a):
        if name == "ideas.usage":
            self.log.append((name, a))
            return copy.deepcopy(self.usage[a.get("scope") or "project"])
        return super().handle(name, a)


def panel(gui, host, provider="claude"):
    pg, host, errors = _open(gui, host=host, ready=".arena-phead")
    pg.evaluate(MOUNT, provider)
    pg.wait_for_selector("#usage-probe .arena-limits", timeout=WAIT_MS)
    return pg, host, errors


def texts(loc):
    return [t.strip() for t in loc.all_inner_texts()]


def test_one_tools_panel_has_its_line_its_rows_by_party_and_member_and_what_is_outside(gui):
    pg, host, errors = panel(gui, UsageHost())
    try:
        box = pg.locator("#usage-probe .arena-limits")
        assert box.get_attribute("aria-label") == "What is left of Claude"
        assert box.locator(".arena-limit[data-provider=claude] b").inner_text() == "62 %"                       # the tool's line, as in the tool lines
        assert box.locator(".arena-limit").count() == 1                                                          # only this tool's
        rows = box.locator(".arena-usage__rows")
        rows.wait_for(timeout=WAIT_MS)
        parties = rows.locator(":scope > li:not(.is-outside) > .arena-usage__line")
        assert texts(parties.locator(".arena-usage__who")) == ["Sign in with a passkey", "Pricing page", "Weekly report email"]
        assert texts(parties.locator(".arena-usage__pct")) == ["18 %", "7 %", "<1 %"]
        passkey = rows.locator("li.arena-usage__row").first
        assert texts(passkey.locator(".arena-usage__members .arena-usage__who")) == ["Backend", "Screens"]
        assert texts(passkey.locator(".arena-usage__members .arena-usage__pct")) == ["12 %", "6 %"]
        outside = rows.locator("li.is-outside .arena-usage__line")
        assert outside.locator(".arena-usage__who").inner_text() == "Outside Orkboard" and outside.locator(".arena-usage__pct").inner_text() == "9 %"
        assert box.locator(".arena-usage__note").inner_text() == "Each share is estimated: the limit read before and after, split by the tokens of each call."
        assert _calls(pg, host, "ideas.usage") == [{"provider": "claude", "scope": "project"}]
        bar = parties.locator(".arena-usage__bar > b")                                                           # the meter is the share of the window
        assert [bar.nth(i).evaluate("e => e.style.width") for i in range(3)] == ["18%", "7%", "0%"]
        tall = [passkey.locator(".arena-usage__line").nth(i).evaluate("e => parseFloat(getComputedStyle(e.querySelector('.arena-usage__bar')).height)") for i in (0, 1)]
        assert tall[0] > tall[1] > 0                                                                             # a member's is thinner
        sizes = pg.evaluate("[...document.querySelectorAll('#usage-probe .arena-usage *')].map(e => parseFloat(getComputedStyle(e).fontSize))")
        assert min(sizes) >= 12                                                                                  # no text under 12 px
        shot(pg, "limits-usage.png")
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_the_switch_asks_again_for_all_projects_and_back(gui):
    pg, host, errors = panel(gui, UsageHost())
    try:
        scope = pg.locator("#usage-probe").get_by_role("group", name="Which projects")
        scope.wait_for(timeout=WAIT_MS)
        assert texts(scope.get_by_role("button")) == ["This project", "All projects"]
        assert scope.get_by_role("button", name="This project").get_attribute("aria-pressed") == "true"
        scope.get_by_role("button", name="All projects").click()
        pg.wait_for_selector("#usage-probe .arena-usage__who:text('Sign in with a passkey · shop')", timeout=WAIT_MS)
        assert scope.get_by_role("button", name="All projects").get_attribute("aria-pressed") == "true"
        assert texts(pg.locator("#usage-probe li.is-outside .arena-usage__pct")) == ["4 %"]
        assert _calls(pg, host, "ideas.usage", 2) == [{"provider": "claude", "scope": "project"}, {"provider": "claude", "scope": "all"}]
        scope.get_by_role("button", name="This project").click()
        pg.wait_for_selector("#usage-probe .arena-usage__who:text('Pricing page')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_host_with_one_project_has_no_switch(gui):
    one = {"project": {**copy.deepcopy(PROJECT), "scopes": ["project"]}}
    pg, host, errors = panel(gui, UsageHost(usage=one))
    try:
        pg.wait_for_selector("#usage-probe .arena-usage__rows", timeout=WAIT_MS)
        assert pg.locator("#usage-probe .arena-usage__scope").count() == 0
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_with_fewer_than_two_reads_the_rows_are_tokens_and_say_so(gui):
    pg, host, errors = panel(gui, UsageHost(usage={"project": copy.deepcopy(TOKENS)}))
    try:
        box = pg.locator("#usage-probe .arena-usage")
        box.locator(".arena-usage__rows").wait_for(timeout=WAIT_MS)
        assert texts(box.locator(".arena-usage__pct")) == ["12k tokens", "12k tokens"]
        assert box.locator(".arena-usage__bar").count() == 0 and box.locator("li.is-outside").count() == 0
        assert "these are tokens, not shares" in box.inner_text()
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_host_that_cannot_tell_says_so_and_the_estimate_line_stays(gui):
    pg, host, errors = panel(gui, UsageHost(refuse=True))
    try:
        box = pg.locator("#usage-probe .arena-usage")
        box.get_by_text("What used it is not known here.").wait_for(timeout=WAIT_MS)
        assert box.locator(".arena-usage__rows").count() == 0
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_without_a_provider_the_panel_is_the_tool_lines_as_before_and_asks_nothing(gui):
    pg, host, errors = panel(gui, UsageHost(), provider="")
    try:
        box = pg.locator("#usage-probe .arena-limits")
        assert [box.locator(".arena-limit").nth(i).get_attribute("data-provider") for i in range(2)] == ["claude", "codex"]
        assert box.locator(".arena-usage").count() == 0
        pg.wait_for_timeout(300)
        assert not [1 for n, _a in host.log if n == "ideas.usage"]
    finally:
        pg.close()
    assert not errors, "\n".join(errors)
