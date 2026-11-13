"""The AI tools in the hand (docs/specs/130-the-first-open-is-the-orkmasters.md part A.1–A.2; decisions §232.4, §232.5): `machine.tool_order` and its reading by
`harnesses.main` and `settings.tool_order`, the adding card's rows, the key found by name and never by value, what is refused, the third line, the order,
and what putting a tool back plans and undoes."""
from __future__ import annotations

from pathlib import Path

import pytest

from orkboard import settings, tools
from orkboard.realm import tool_hand


def machine_of(*on: str, order: tuple[str, ...] = (), main: str = "", api: tuple[str, ...] = ()) -> settings.MachineSettings:
    m = settings.MachineSettings()
    for t in on:
        m.tools[t] = settings.ToolChoice(enabled=True, billing="api" if t in api else "subscription")
    m.tool_order, m.main_tool = list(order), main
    return m


def status(tool_id: str, found: bool = True, logged_in: bool | None = True, billing: str = "subscription") -> tools.ToolStatus:
    return tools.ToolStatus(next(t for t in tools.TOOLS if t.id == tool_id), found=found, version="1.0" if found else "", logged_in=logged_in, billing=billing)


# -- machine.tool_order (A.1) -------------------------------------------------------------------------------------

def test_the_order_is_kept_in_the_settings_and_cleaned_when_read(tmp_path: Path):
    f = tmp_path / "settings.json"
    m = machine_of("claude", "codex", order=("codex", "claude"))
    settings.save(m, f)
    assert settings.load(f).tool_order == ["codex", "claude"]
    assert '"tool_order"' in f.read_text(encoding="utf-8")
    # unknown ids, repeats and a thing that is no list are dropped; a file written before the order is []
    assert settings.clean_tool_order(["codex", "nope", "codex", 3, "claude"]) == ["codex", "claude"]
    assert settings.clean_tool_order("claude") == [] and settings.clean_tool_order(None) == []
    assert settings.MachineSettings.from_dict({}).tool_order == []


# -- the key, by name (A.2) -----------------------------------------------------------------------------------------

def test_a_key_is_found_by_its_name_and_its_value_is_never_read_out():
    assert tool_hand.key_found("codex", {"CODEX_API_KEY": "sk-secret"}) == "CODEX_API_KEY"
    assert tool_hand.key_found("claude", {"ANTHROPIC_API_KEY": "x"}) == "ANTHROPIC_API_KEY"
    assert tool_hand.key_found("claude", {"OPENAI_API_KEY": "x"}) == ""
    assert tool_hand.key_found("claude", {"ANTHROPIC_API_KEY": ""}) == ""                           # set but empty is not a key
    assert tool_hand.key_found("agy", {"GEMINI_API_KEY": "x", "GOOGLE_API_KEY": "x"}) == ""                   # Antigravity takes no key here (§250.5)
    line = tool_hand.third_line("agy", "api", True, {"GEMINI_API_KEY": "x"})
    assert line["state"] == "no_key" and line["line"] == "Antigravity signs in with Google; it takes no key here."
    card = tool_hand.card([status("codex", billing="api")], machine_of(), {"CODEX_API_KEY": "sk-secret"})
    assert "sk-secret" not in repr(card)


def test_a_key_that_would_win_over_the_subscription_is_said_before_it_costs():
    got = tool_hand.third_line("claude", "subscription", True, {"ANTHROPIC_API_KEY": "x"})
    assert got["state"] == "ok"
    assert got["warn"] == "ANTHROPIC_API_KEY is set in your environment: Claude Code uses it before your subscription and is paid per token."


# -- the adding card (A.2) ----------------------------------------------------------------------------------------

def test_the_card_lists_the_tools_not_in_the_hand_in_three_groups():
    m = machine_of("claude")
    got = tool_hand.card([status("claude"), status("codex", logged_in=False), status("agy"), status("cursor", found=False, logged_in=None)], m, {})
    assert got["ready"] and got["n"] == 1 and got["max"] == 6 and not got["full"]
    rows = {r["id"]: r for r in got["tools"]}
    assert "claude" not in rows                                                                      # in the hand: not offered again
    assert [r["group"] for r in got["tools"]] == ["ready", "signed_out", "not_installed"]
    assert rows["cursor"]["install"] and not rows["cursor"]["pickable"]                              # not installed: how to install it, never picked
    assert rows["codex"]["lines"]["subscription"]["needs"] == "sign_in"
    assert set(rows["agy"]["lines"]) == {"subscription", "api"}
    assert got["first"] == ""                                                                        # the only ready tool is experimental: nothing is picked for the person


# -- add, order, put back (A.2) -----------------------------------------------------------------------------------

def test_a_tool_comes_into_the_hand_at_the_end_and_the_first_is_the_main_tool():
    m = machine_of()
    tool_hand.add(m, "codex", "api")
    assert tool_hand.hand(m) == ["codex"] and m.main_tool == "codex" and m.tools["codex"].billing == "api"
    tool_hand.add(m, "claude", "subscription")
    assert tool_hand.hand(m) == ["codex", "claude"] and m.main_tool == "codex"                       # the second is not the main tool
    tool_hand.add(m, "codex", "subscription")                                                        # again: its place is the end, its billing the new one
    assert tool_hand.hand(m) == ["claude", "codex"] and m.tools["codex"].billing == "subscription"


def test_the_next_tool_is_the_next_in_the_hand_round_again():
    assert tool_hand.next_after(["claude", "codex", "agy"], "claude") == "codex"
    assert tool_hand.next_after(["claude", "codex", "agy"], "agy") == "claude"
    assert tool_hand.next_after(["claude"], "claude") is None


def test_putting_a_tool_back_says_what_follows_and_the_last_tool_asks():
    m = machine_of("claude", "codex")
    plan = tool_hand.put_back_plan(m, "claude", [{"slug": "art", "name": "Art"}])
    assert plan["last"] is False and plan["next"] == "codex" and plan["ask"] == ""
    assert plan["line"] == "The orks stop using it after the task at work"
    assert plan["parties"][0]["line"] == "Art is set to Claude Code: it goes on with Codex, the next in your hand"
    only = tool_hand.put_back_plan(machine_of("claude"), "claude")
    assert only["last"] and only["next"] is None
    assert only["ask"] == "Without it nothing is worked on: goals wait in the Orkmaster's column until you add a tool"


def test_a_tool_put_back_comes_back_where_it_was_paid_as_it_was():
    m = machine_of("claude", "codex", "agy", order=("claude", "codex", "agy"), api=("codex",))
    undo = tool_hand.take_out(m, "claude")
    assert tool_hand.hand(m) == ["codex", "agy"] and not m.tools["claude"].enabled
    assert m.main_tool == "codex" and undo["main"] is True                                           # the main tool's place passes to the first left
    assert settings.main_tool(m) == "codex"
    tool_hand.restore(m, undo)
    assert tool_hand.hand(m) == ["claude", "codex", "agy"] and settings.main_tool(m) == "claude" and m.tools["claude"].enabled
    undo = tool_hand.take_out(m, "codex")                                                            # a middle one, paid by its key
    assert undo["billing"] == "api" and undo["at"] == 1 and not undo["main"]
    tool_hand.restore(m, undo)
    assert tool_hand.hand(m) == ["claude", "codex", "agy"] and m.tools["codex"].billing == "api"
    with pytest.raises(ValueError, match="not in your hand"):
        tool_hand.take_out(m, "pi")
    with pytest.raises(ValueError, match="nothing to undo"):
        tool_hand.restore(m, {"tool": "nope", "billing": "api"})
