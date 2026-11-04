"""The AI tools in the hand (docs/specs/130-the-first-open-is-the-orkmasters.md part A.1–A.2; decisions §232.4, §232.5): `machine.tool_order` and its reading by
`harnesses.main` and `settings.tool_order`, the adding card's rows, the key found by name and never by value, what is refused, the third line, the order,
and what putting a tool back plans and undoes."""
from __future__ import annotations

from pathlib import Path

import pytest

from orkboard import settings, tools
from orkboard.realm import harnesses, tool_hand


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


def test_the_tools_turned_on_follow_the_persons_order_then_the_registrys():
    assert settings.tool_order(machine_of("claude", "codex")) == ["claude", "codex"]               # no order: the registry's, as before
    assert settings.tool_order(machine_of("claude", "codex", order=("codex", "claude"))) == ["codex", "claude"]
    assert settings.tool_order(machine_of("claude", "codex", "agy", order=("codex",))) == ["codex", "claude", "agy"]    # what it does not name comes after, in the registry's order
    assert settings.tool_order(machine_of("claude", order=("codex", "claude"))) == ["claude"]       # a tool turned off is not in the hand, named or not
    assert settings.tool_order(machine_of()) == []


def test_harnesses_main_reads_the_order_after_the_chosen_tool():
    assert harnesses.main(["claude", "codex"]) == "claude"                                          # no order: the registry's first, as before
    assert harnesses.main(["claude", "codex"], "", ["codex", "claude"]) == "codex"
    assert harnesses.main(["claude", "codex"], "claude", ["codex", "claude"]) == "claude"           # the chosen one, when it is on, comes first
    assert harnesses.main(["claude", "codex"], "agy", ["codex"]) == "codex"                         # chosen but off: the order
    assert harnesses.main(["codex"], "", ["claude"]) == "codex"                                     # an order that names none on: the registry's
    assert harnesses.main([], "claude", ["claude"]) is None
    m = machine_of("claude", "codex", order=("codex", "claude"))
    assert settings.main_tool(m) == "codex"
    m.main_tool = "claude"
    assert settings.main_tool(m) == "claude"


# -- the key, by name (A.2) -----------------------------------------------------------------------------------------

def test_a_key_is_found_by_its_name_and_its_value_is_never_read_out():
    assert tool_hand.key_found("codex", {"CODEX_API_KEY": "sk-secret"}) == "CODEX_API_KEY"
    assert tool_hand.key_found("claude", {"ANTHROPIC_API_KEY": "x"}) == "ANTHROPIC_API_KEY"
    assert tool_hand.key_found("claude", {"OPENAI_API_KEY": "x"}) == ""
    assert tool_hand.key_found("claude", {"ANTHROPIC_API_KEY": ""}) == ""                           # set but empty is not a key
    assert tool_hand.key_found("agy", {"GOOGLE_API_KEY": "x"}) == "GOOGLE_API_KEY"
    card = tool_hand.card([status("codex", billing="api")], machine_of(), {"CODEX_API_KEY": "sk-secret"})
    assert "sk-secret" not in repr(card)


def test_the_third_line_follows_how_the_tool_is_paid():
    sub = tool_hand.third_line("claude", "subscription", True, {})
    assert (sub["state"], sub["line"]) == ("ok", "Signed in to your subscription") and not sub["warn"]
    out = tool_hand.third_line("claude", "subscription", False, {})
    assert (out["state"], out["needs"], out["line"]) == ("signed_out", "sign_in", "Not signed in")
    assert tool_hand.third_line("claude", "subscription", None, {})["state"] == "unknown"           # it cannot be told without a request: the request tells
    key = tool_hand.third_line("codex", "api", True, {"CODEX_API_KEY": "x"})
    assert key["state"] == "ok" and key["line"] == "Uses the key in your environment: CODEX_API_KEY" and key["cost"] == "Paid per token, by that key"
    none = tool_hand.third_line("codex", "api", True, {})
    assert (none["state"], none["needs"], none["var"]) == ("no_key", "key", "CODEX_API_KEY")
    assert none["line"] == "No key found: set CODEX_API_KEY in your environment, then Test again"


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


def test_the_first_ready_tool_is_the_one_the_card_opens_on():
    got = tool_hand.card([status("claude"), status("codex")], machine_of(), {})
    assert got["first"] == "claude"
    assert tool_hand.card(None, machine_of(), {}) == {"ready": False, "n": 0, "max": 6, "full": False, "tools": [], "first": ""}


def test_test_and_add_is_refused_in_words():
    m = machine_of("claude")
    card = {r["id"]: r for r in tool_hand.card([status("claude"), status("codex", logged_in=False), status("cursor", found=False, logged_in=None),
                                                 status("agy"), status("hermes", logged_in=True)], m, {})["tools"]}
    why = lambda tid, billing="subscription", env=None, risk=False: tool_hand.refusal(card.get(tid), m, billing, env, risk)    # noqa: E731
    assert why("codex") == "Codex is not signed in: sign in first (codex login)"
    assert why("cursor").startswith("Cursor is not installed: ")
    assert why("nope") == "That AI tool is not found here"
    assert why("agy") == "Antigravity is experimental: read its warning first" and why("agy", risk=True) == ""
    assert why("hermes", "api").endswith("is known here: use its subscription")                   # a tool with no key Orkboard knows is paid by its subscription
    assert why("hermes", "bogus") == "A tool is paid by its subscription or by its API key"
    full = machine_of("claude", "codex", "agy", "hermes", "pi", "cursor")
    assert "holds 6" in tool_hand.refusal({"id": "x", "title": "X", "pickable": True, "risk": "", "lines": {}, "install": "", "login": ""}, full, "subscription")


# -- add, order, put back (A.2) -----------------------------------------------------------------------------------

def test_a_tool_comes_into_the_hand_at_the_end_and_the_first_is_the_main_tool():
    m = machine_of()
    tool_hand.add(m, "codex", "api")
    assert tool_hand.hand(m) == ["codex"] and m.main_tool == "codex" and m.tools["codex"].billing == "api"
    tool_hand.add(m, "claude", "subscription")
    assert tool_hand.hand(m) == ["codex", "claude"] and m.main_tool == "codex"                       # the second is not the main tool
    tool_hand.add(m, "codex", "subscription")                                                        # again: its place is the end, its billing the new one
    assert tool_hand.hand(m) == ["claude", "codex"] and m.tools["codex"].billing == "subscription"


def test_the_order_is_a_permutation_of_the_hand_and_its_first_is_the_main_tool():
    m = machine_of("claude", "codex", "agy")
    assert tool_hand.reorder(m, ["agy", "claude", "codex"]) == ["agy", "claude", "codex"]
    assert settings.main_tool(m) == "agy" and m.main_tool == "agy"
    for bad in (["claude", "codex"], ["claude", "codex", "agy", "agy"], ["claude", "codex", "pi"], "claude", None):
        with pytest.raises(ValueError, match="each once"):
            tool_hand.reorder(m, bad)
    assert tool_hand.hand(m) == ["agy", "claude", "codex"]                                           # a refused order changes nothing


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
