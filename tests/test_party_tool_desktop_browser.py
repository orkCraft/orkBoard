"""Spec 81 part B on the desktop (docs/specs/81-a-party-its-tool-and-size.md §4, §5 B; decisions §98), in the dialog of spec 91 §7: Chromium at 1 440 × 900 against the stub host of tests/test_new_party_91_desktop_browser.py
(`ideas.party_presets`, `ideas.tools` in spec §1.4's shape). New party's size bar has **Its AI tool** for the party, a list that drops down (orkUI's `.ork-select` around a native select): *Main tool (Claude Code)*
picked, then *Ready*, *Not signed in* and *Not installed* (disabled); a tool with no tiers says *runs its own model* where the price was; a row not signed in, picked, opens its sign-in and stays picked; the pick is sent as
`tool` with *Save party*; *Edit the party* has the list with the party's tool. A seat's own tool (spec 91 §6) is tests/test_new_party_91_desktop_browser.py's; the size switch's seats and tiers are too.
Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_new_party_91_desktop_browser import PresetHost, _dialog, _words, desk  # noqa: E402,F401
from tests.test_proposals_desktop_browser import _about, _party  # noqa: E402
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _calls, _new_party, _open  # noqa: E402

pytestmark = pytest.mark.browser


def _select(dlg):
    return dlg.get_by_role("group", name="Its AI tool").locator("select")


def _groups(select):
    return select.evaluate("s => [...s.querySelectorAll('optgroup')].map(g => [g.label, [...g.querySelectorAll('option')].map(o => [o.value, o.textContent, o.disabled])])")


def test_the_party_has_its_ai_tool_in_the_size_bar_the_main_tool_picked_and_the_tools_in_three_groups(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    box = dlg.get_by_role("group", name="Its AI tool")
    box.wait_for(timeout=WAIT_MS)
    assert dlg.locator(".shell-sizebar").get_by_role("group", name="Its AI tool").count() == 1                                  # beside the size switch
    assert box.locator(".ork-select > select.ork-field").count() == 1                                                       # orkUI's select around the native one
    sel = _select(dlg)
    assert sel.input_value() == "" and sel.locator("option:checked").inner_text() == "Main tool (Claude Code)"
    assert [o[1] for o in sel.evaluate("s => [...s.options].map(o => [o.value, o.textContent])")][:1] == ["Main tool (Claude Code)"]
    got = _groups(sel)
    assert [g[0] for g in got] == ["Ready", "Not signed in", "Not installed"]
    assert got[0][1] == [["claude", "Claude Code", False], ["codex", "Codex", False], ["pi", "pi · runs its own model", False], ["agy", "Antigravity", False]]       # Antigravity is ready here
    assert got[1][1] == [["cursor", "Cursor · runs its own model", False]]
    assert got[2][1] == [["hermes", "Hermes Agent · runs its own model", True]]                                             # shown, never picked
    pg.wait_for_timeout(300)
    shot(pg, "desk-tool.png")


def test_the_tool_picked_is_sent_with_save_party_and_the_main_tool_sends_none(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    _select(dlg).select_option("codex")
    assert _select(dlg).input_value() == "codex"
    dlg.get_by_label("What it is for").fill("On codex.")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["tool"] == "codex" and sent["proposal"] == "mobile-build" and sent["size"] == "standard"
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.get_by_label("What it is for").fill("On the Main tool.")
    dlg.get_by_role("button", name="Save party").click()
    assert "tool" not in _calls(pg, host, "ideas.goal_save", at_least=2)[-1]                                                # the Main tool is none


def test_a_tool_with_no_tiers_says_it_runs_its_own_model_where_the_price_was(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    form = dlg.locator("#goal-form")
    dlg.locator(".shell-price").wait_for(timeout=WAIT_MS)
    assert "a goal" in _words(dlg.locator(".shell-price")) and form.locator(".shell-tool__own").count() == 0
    _select(dlg).select_option("pi")
    assert "Runs its own model: its price is its own." in _words(form) and dlg.locator(".shell-price").count() == 0
    assert dlg.locator('[data-foot="agents"]').inner_text().startswith("2 agents")                                           # the seats and the agents stay
    _select(dlg).select_option("")
    dlg.locator(".shell-price").wait_for(timeout=WAIT_MS)
    assert "Runs its own model" not in _words(form)
    _select(dlg).select_option("pi")
    dlg.get_by_label("What it is for").fill("On pi.")
    dlg.get_by_role("button", name="Save party").click()
    assert _calls(pg, host, "ideas.goal_save")[-1]["tool"] == "pi"


def test_a_tool_not_signed_in_opens_its_sign_in_and_stays_picked(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    _select(dlg).select_option("cursor")
    assert _calls(pg, host, "tools.sign_in")[-1] == {"harness": "cursor"}
    assert _select(dlg).input_value() == "cursor" and "Not signed in: its sign-in opens" in _words(dlg.get_by_role("group", name="Its AI tool"))
    _select(dlg).select_option("codex")                                                                                     # a tool that is ready opens nothing
    assert len(_calls(pg, host, "tools.sign_in", at_least=1)) == 1
    dlg.get_by_label("What it is for").fill("x")
    dlg.get_by_role("button", name="Save party").click()
    assert _calls(pg, host, "ideas.goal_save")[-1]["tool"] == "codex"


def test_edit_the_party_has_the_list_with_the_partys_tool_and_save_party_sends_a_change_only(desk):
    pg, host = desk
    _party(host)
    host.goals["passkey"]["tool"] = "codex"
    host.bump({})
    _about(pg)
    pg.get_by_role("region", name="Preview").get_by_role("button", name="Edit the party").click()
    dlg = pg.get_by_role("dialog", name="Edit the party")
    sel = _select(dlg)
    sel.wait_for(timeout=WAIT_MS)
    assert sel.input_value() == "codex"
    dlg.get_by_role("button", name="Save party").click()
    assert "tool" not in _calls(pg, host, "ideas.goal_save")[-1]                                                            # nothing changed: nothing sent
    _about(pg)
    pg.get_by_role("region", name="Preview").get_by_role("button", name="Edit the party").click()
    dlg = pg.get_by_role("dialog", name="Edit the party")
    sel = _select(dlg)
    sel.wait_for(timeout=WAIT_MS)
    assert sel.input_value() == "codex"
    sel.select_option("")
    dlg.get_by_role("button", name="Save party").click()
    assert _calls(pg, host, "ideas.goal_save", at_least=2)[-1]["tool"] == ""                                                # the Main tool again


def test_a_host_without_the_list_has_no_field(gui):
    host = PresetHost()
    host.tools_doc = {"error": "Unknown command"}
    pg, host, errors = _open(gui, host=host, ready=".arena[data-goal=passkey]")
    _new_party(pg)
    dlg = _dialog(pg)
    pg.wait_for_timeout(300)
    assert dlg.get_by_role("group", name="Its AI tool").count() == 0 and dlg.locator("[data-seat-tool]").count() == 0       # no list: no field, no seat's button
    dlg.get_by_label("What it is for").fill("x")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert "tool" not in sent and "tools" not in sent
    pg.close()
    assert not errors, "\n".join(errors)
