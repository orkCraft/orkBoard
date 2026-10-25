"""Spec 81 part B on the desktop (docs/specs/81-a-party-its-tool-and-size.md §4, §5 B; decisions §98): Chromium at 1 440 × 900 against the proposals test's stub host with `ideas.tools` (spec §1.4's shape).
New party's cards and *More: the library* have **Its AI tool** under the size switch, a list that drops down (orkUI's `.ork-select` around a native select): *Main tool (Claude Code)* picked, then *Ready*, *Not signed in* and *Not
installed* (disabled); a tool with no tiers says *runs its own model* where the price was; a row not signed in, picked, opens its sign-in and stays picked; the pick is sent as `tool` with *Make it* and *Save party*; *Edit the party*
has the list with the party's tool. The size switch's joins and leaves are in tests/test_proposals_desktop_browser.py. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_proposals_desktop_browser import ProposalHost, _about, _card, _dialog, _party, _words, desk  # noqa: E402,F401
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _calls, _new_party, _open  # noqa: E402

pytestmark = pytest.mark.browser


def _select(card):
    return card.locator("select")


def _groups(select):
    return select.evaluate("s => [...s.querySelectorAll('optgroup')].map(g => [g.label, [...g.querySelectorAll('option')].map(o => [o.value, o.textContent, o.disabled])])")


def test_each_card_has_its_ai_tool_under_the_size_switch_the_main_tool_picked_and_the_tools_in_three_groups(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    card = _card(dlg, "mobile-features")
    box = card.get_by_role("group", name="Its AI tool")
    box.wait_for(timeout=WAIT_MS)
    assert box.locator(".ork-select > select.ork-field").count() == 1                                                       # orkUI's select around the native one
    sel = _select(card)
    assert sel.input_value() == "" and sel.locator("option:checked").inner_text() == "Main tool (Claude Code)"
    assert [o[1] for o in sel.evaluate("s => [...s.options].map(o => [o.value, o.textContent])")][:1] == ["Main tool (Claude Code)"]
    got = _groups(sel)
    assert [g[0] for g in got] == ["Ready", "Not signed in", "Not installed"]
    assert got[0][1] == [["claude", "Claude Code", False], ["codex", "Codex", False], ["pi", "pi · runs its own model", False]]
    assert got[1][1] == [["cursor", "Cursor · runs its own model", False]]
    assert got[2][1] == [["agy", "Antigravity", True], ["hermes", "Hermes Agent · runs its own model", True]]                  # shown, never picked
    assert _card(dlg, "mobile-architecture").locator("select").input_value() == ""                                         # each card has its own
    pg.wait_for_timeout(300)
    shot(pg, "desk-tool.png")


def test_the_tool_picked_is_sent_with_make_it_and_the_main_tool_sends_none(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    card = _card(dlg, "mobile-features")
    _select(card).select_option("codex")
    assert _select(card).input_value() == "codex" and _select(_card(dlg, "mobile-architecture")).input_value() == ""
    card.get_by_role("button", name="Make it").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["tool"] == "codex" and sent["proposal"] == "mobile-features" and sent["size"] == "standard"
    _new_party(pg)
    dlg = _dialog(pg)
    _card(dlg, "mobile-architecture").get_by_role("button", name="Make it").click()
    assert "tool" not in _calls(pg, host, "ideas.goal_save", at_least=2)[-1]                                                # the Main tool is none


def test_a_tool_with_no_tiers_says_it_runs_its_own_model_where_the_price_was(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    card = _card(dlg, "mobile-features")
    assert "≈$1–3 a goal" in _words(card.locator(".shell-prop__foot"))
    _select(card).select_option("pi")
    foot = _words(card.locator(".shell-prop__foot"))
    assert "runs its own model" in foot and "a goal" not in foot and "4 agents" in foot                                    # the heads and the agents stay
    _select(card).select_option("")
    assert "≈$1–3 a goal" in _words(card.locator(".shell-prop__foot"))
    _select(card).select_option("pi")
    card.get_by_role("button", name="Make it").click()
    assert _calls(pg, host, "ideas.goal_save")[-1]["tool"] == "pi"


def test_a_tool_not_signed_in_opens_its_sign_in_and_stays_picked(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    card = _card(dlg, "mobile-features")
    _select(card).select_option("cursor")
    assert _calls(pg, host, "tools.sign_in")[-1] == {"harness": "cursor"}
    assert _select(card).input_value() == "cursor" and "Not signed in: its sign-in opens" in _words(card.get_by_role("group", name="Its AI tool"))
    _select(card).select_option("codex")                                                                                   # a tool that is ready opens nothing
    assert len(_calls(pg, host, "tools.sign_in", at_least=1)) == 1
    card.get_by_role("button", name="Make it").click()
    assert _calls(pg, host, "ideas.goal_save")[-1]["tool"] == "codex"


def test_the_library_has_the_list_too_and_save_party_sends_the_tool(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.get_by_role("button", name="More: the library").click()
    dlg.locator(".shell-craft-tile").first.wait_for(timeout=WAIT_MS)
    sel = dlg.get_by_role("group", name="Its AI tool").locator("select")
    assert sel.input_value() == "" and [g[0] for g in _groups(sel)] == ["Ready", "Not signed in", "Not installed"]
    assert dlg.locator("#goal-form").get_by_role("group", name="Its size").count() == 1
    sel.select_option("pi")
    assert "Runs its own model: its price is its own." in _words(dlg.locator("#goal-form"))
    dlg.get_by_label("What it is for").fill("A party on pi.")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["tool"] == "pi" and sent["size"] == "standard"


def test_edit_the_party_has_the_list_with_the_partys_tool_and_save_party_sends_a_change_only(desk):
    pg, host = desk
    _party(host)
    host.goals["passkey"]["tool"] = "codex"
    host.bump({})
    _about(pg)
    pg.get_by_role("region", name="Preview").get_by_role("button", name="Edit the party").click()
    dlg = pg.get_by_role("dialog", name="Edit the party")
    sel = dlg.get_by_role("group", name="Its AI tool").locator("select")
    sel.wait_for(timeout=WAIT_MS)
    assert sel.input_value() == "codex"
    dlg.get_by_role("button", name="Save party").click()
    assert "tool" not in _calls(pg, host, "ideas.goal_save")[-1]                                                            # nothing changed: nothing sent
    _about(pg)
    pg.get_by_role("region", name="Preview").get_by_role("button", name="Edit the party").click()
    dlg = pg.get_by_role("dialog", name="Edit the party")
    sel = dlg.get_by_role("group", name="Its AI tool").locator("select")
    sel.wait_for(timeout=WAIT_MS)
    assert sel.input_value() == "codex"
    sel.select_option("")
    dlg.get_by_role("button", name="Save party").click()
    assert _calls(pg, host, "ideas.goal_save", at_least=2)[-1]["tool"] == ""                                                # the Main tool again


def test_a_host_without_the_list_has_no_field(gui):
    host = ProposalHost()
    host.tools_doc = {"error": "Unknown command"}
    pg, host, errors = _open(gui, host=host, ready=".arena[data-goal=passkey]")
    _new_party(pg)
    dlg = _dialog(pg)
    card = _card(dlg, "mobile-features")
    card.get_by_role("button", name="Make it").wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    assert card.get_by_role("group", name="Its AI tool").count() == 0 and "tool" not in (_calls(pg, host, "ideas.tools") and {})
    card.get_by_role("button", name="Make it").click()
    assert "tool" not in _calls(pg, host, "ideas.goal_save")[-1]
    pg.close()
    assert not errors, "\n".join(errors)
