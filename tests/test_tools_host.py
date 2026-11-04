"""The AI tools' own commands (docs/specs/130-the-first-open-is-the-orkmasters.md part A.2–A.3; decisions §232.4, §232.5): `tools.*` on Orkboard's host,
the onboarding's old names kept as aliases, Test & add, the order, the billing, Put back and its Undo, and nothing of it on the phone."""
from __future__ import annotations

import sys

import pytest

from orkboard import settings, tools
from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import goal_team, ideas, tool_errors, tool_hand


def found(*ids: str, signed_out: tuple[str, ...] = (), unknown: tuple[str, ...] = ()) -> list[tools.ToolStatus]:
    return [tools.ToolStatus(t, found=t.id in ids, version="2.0" if t.id in ids else "",
                             logged_in=False if t.id in signed_out else None if t.id in unknown else True) for t in tools.TOOLS]


@pytest.fixture
def board(fake_repo, monkeypatch) -> Orkboard:
    monkeypatch.setattr(tools, "detect", lambda *a, **k: found("claude", "codex", "agy", "hermes", signed_out=("hermes",)))
    monkeypatch.setattr(tools, "detect_others", lambda *a, **k: [])
    b = Orkboard(fake_repo)
    b.tools_host._ask = lambda tool, prompt, model=None: "ok"
    yield b
    sys.modules.pop("orkboard.core.idea_runner", None)


def looked(b: Orkboard) -> dict:
    card = b.command("tools.card", {})
    b.tools_host._finder.join(5)
    return b.command("tools.card", {}) if not card["ready"] else card


def add(b: Orkboard, tool: str, **args) -> dict:
    got = b.command("tools.test_add", {"tool": tool, **args})
    b.tools_host._worker.join(5)
    return got


# -- the commands, and the onboarding's names kept (A.3) --------------------------------------------------------

def test_the_tools_have_commands_of_their_own_and_the_old_names_are_aliases(fake_repo, monkeypatch):
    monkeypatch.setenv("ORKCRAFT_ONBOARDING", "1")
    monkeypatch.setattr(tools, "detect", lambda *a, **k: found("claude", "codex"))
    monkeypatch.setattr(tools, "detect_others", lambda *a, **k: [])
    b = Orkboard(fake_repo)
    b.onboarding._finder.join(5)
    assert {"tools.look", "tools.card", "tools.check", "tools.test_add", "tools.put_back_plan", "tools.put_back", "tools.put_back_undo", "tools.order", "tools.billing",
            "tools.request", "first_open.ask", "first_open.kind", "first_open.tools_skip", "projects.new_folder"} <= set(b.commands)
    assert {"tools.sign_in", "tools.sign_in_done"} <= set(b.commands)                      # spec 45's, in the same namespace, untouched
    assert {"onboarding.tools", "onboarding.check", "onboarding.detect", "onboarding.request", "onboarding.skip"} <= set(b.commands)
    # the alias and the command are one thing: the same look, the same Check, the same request
    assert b.onboarding.statuses is b.tools_host.statuses and b.onboarding.checks is b.tools_host.checks
    asked = []
    b.tools_host._ask = lambda tool, prompt, model=None: asked.append(tool) or "ok"
    b.command("onboarding.check", {"tool": "claude"})
    b.tools_host._worker.join(5)
    assert asked == ["claude"] and b.tools_host.checks["claude"]["state"] == "ok"
    assert b.snapshot()["onboarding"]["tools"]["rows"][0]["check"]["state"] == "ok"        # the page's old rows read the same Check
    b.command("tools.check", {"tool": "codex"})
    b.tools_host._worker.join(5)
    assert asked == ["claude", "codex"] and b.onboarding.checks["codex"]["state"] == "ok"
    old = b.command("onboarding.request", {"name": "Zed", "note": "edits"})
    assert old == b.command("tools.request", {"name": "Zed", "note": "edits"}) and "title=Support+Zed" in old["url"]
    with pytest.raises(CommandError, match="Name the tool"):
        b.command("onboarding.request", {})
    with pytest.raises(CommandError, match="not found"):
        b.command("onboarding.check", {"tool": "cursor"})
    b.command("onboarding.detect", {})                                                      # Check again: the look begins again, for both names
    b.onboarding._finder.join(5)
    assert b.onboarding.statuses is not None
    b.command("tools.look", {})
    b.tools_host._finder.join(5)


def test_the_phone_sets_no_tool_and_sees_none(board):
    assert not any(BoardPhone.allowed(board, name) for name in ("tools.test_add", "tools.put_back", "tools.order", "tools.billing", "tools.card",
                                                                 "first_open.ask", "projects.new_folder"))
    assert {"tools", "laid"} <= set(board.snapshot()) and not {"tools", "laid"} & set(board.phone_snapshot())


# -- the card and Test & add (A.2) ----------------------------------------------------------------------------------

def test_the_card_is_looked_for_once_and_lists_what_is_not_in_the_hand(board):
    first = board.command("tools.card", {})
    assert first["ready"] in (True, False)
    card = looked(board)
    assert card["ready"] and card["n"] == 0 and not card["full"]
    rows = {r["id"]: r for r in card["tools"]}
    assert rows["claude"]["group"] == "ready" and rows["hermes"]["group"] == "signed_out"
    assert rows["cursor"]["group"] == "not_installed" and not rows["cursor"]["pickable"]
    assert card["first"] == "claude"
    assert board.snapshot()["tools"]["hand"] == [] and board.snapshot()["tools"]["main"] == ""


def test_test_and_add_puts_the_tool_in_the_hand_after_it_answers(board):
    looked(board)
    asked = []
    board.tools_host._ask = lambda tool, prompt, model=None: asked.append((tool, model)) or "ok"
    got = add(board, "codex", billing="subscription")
    assert got["adding"]["codex"]["state"] in ("running", "added")                           # the page is told at once; the answer comes on a thread (it may be in already)
    assert asked == [("codex", "laborer")]                                                  # one short request, on the lightest tier
    state = board.snapshot()["tools"]
    assert state["order"] == ["codex"] and state["main"] == "codex" and state["hand"][0]["main"] and state["hand"][0]["billing"] == "subscription"
    done = state["adding"]["codex"]
    assert done["state"] == "added" and done["line"] == "Codex is in your hand. Add another AI tool?" and done["n"] == 1 and not done["full"]
    saved = settings.load()
    assert saved.tools["codex"].enabled and saved.tool_order == ["codex"] and saved.main_tool == "codex"
    add(board, "claude")
    assert board.snapshot()["tools"]["order"] == ["codex", "claude"] and board.snapshot()["tools"]["main"] == "codex"
    assert "claude" not in {r["id"] for r in board.command("tools.card", {})["tools"]}      # the card offers only the tools not in the hand


def test_a_tool_that_fails_its_test_is_not_added_and_says_why(board):
    looked(board)

    def fail(tool, prompt, model=None):
        raise tool_errors.ToolError(tool, "401 unauthorized: please run /login")
    board.tools_host._ask = fail
    add(board, "claude")
    got = board.snapshot()["tools"]
    assert got["hand"] == [] and got["adding"]["claude"]["state"] == "failed"
    assert got["adding"]["claude"]["kind"] == "login" and "Claude Code" in got["adding"]["claude"]["line"]
    assert settings.load().tool_order == [] and not settings.load().tools["claude"].enabled


def test_test_and_add_is_refused_before_a_request_is_made(board, monkeypatch):
    looked(board)
    asked = []
    board.tools_host._ask = lambda tool, prompt, model=None: asked.append(tool) or "ok"
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    for tool, args, why in (("hermes", {}, "not signed in"), ("cursor", {}, "not installed"), ("agy", {}, "experimental"),
                            ("codex", {"billing": "api"}, "No key found: set CODEX_API_KEY in your environment, then Test again"),
                            ("nope", {}, "Say which AI tool")):
        with pytest.raises(CommandError, match=why):
            board.command("tools.test_add", {"tool": tool, **args})
    assert asked == [] and board.snapshot()["tools"]["hand"] == []
    add(board, "agy", risk_read=True)                                                       # its warning read: it goes on
    assert board.snapshot()["tools"]["order"] == ["agy"]


def test_the_key_found_in_the_environment_is_named_and_the_tool_is_paid_by_it(board, monkeypatch):
    monkeypatch.setenv("CODEX_API_KEY", "sk-never-shown")
    card = looked(board)
    line = next(r for r in card["tools"] if r["id"] == "codex")["lines"]["api"]
    assert line["line"] == "Uses the key in your environment: CODEX_API_KEY" and "sk-never-shown" not in repr(card)
    add(board, "codex", billing="api")
    assert board.snapshot()["tools"]["adding"]["codex"]["state"] == "added" and board.snapshot()["tools"]["hand"][0]["billing"] == "api"
    assert "sk-never-shown" not in repr(board.snapshot()) and "sk-never-shown" not in settings.path().read_text(encoding="utf-8")


def test_a_full_hand_adds_no_more(board, monkeypatch):
    """The registry holds six tools today, so a hand of six leaves nothing to offer; the bound is the constant's, tried here at two."""
    assert tool_hand.HAND_MAX == 6
    monkeypatch.setattr(tool_hand, "HAND_MAX", 2)
    looked(board)
    for t in ("claude", "codex"):
        add(board, t)
    card = board.command("tools.card", {})
    assert card["full"] and card["n"] == 2 and board.snapshot()["tools"]["full"]
    with pytest.raises(CommandError, match="holds 2"):
        board.command("tools.test_add", {"tool": "hermes"})


# -- the order and the billing ---------------------------------------------------------------------------------------

def test_the_order_is_the_persons_and_its_first_is_the_main_tool(board):
    looked(board)
    for t in ("claude", "codex", "agy"):
        add(board, t, risk_read=True)
    got = board.command("tools.order", {"order": ["agy", "codex", "claude"]})
    assert got["order"] == ["agy", "codex", "claude"] and got["main"] == "agy"
    assert settings.load().tool_order == ["agy", "codex", "claude"] and settings.main_tool(settings.load()) == "agy"
    with pytest.raises(CommandError, match="each once"):
        board.command("tools.order", {"order": ["agy"]})
    assert board.snapshot()["tools"]["order"] == ["agy", "codex", "claude"]


def test_a_tool_in_the_hand_is_paid_by_its_key_only_when_the_key_is_there(board, monkeypatch):
    looked(board)
    add(board, "codex")
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    with pytest.raises(CommandError, match="No key found: set CODEX_API_KEY"):
        board.command("tools.billing", {"tool": "codex", "billing": "api"})
    monkeypatch.setenv("CODEX_API_KEY", "x")
    got = board.command("tools.billing", {"tool": "codex", "billing": "api"})
    assert got["hand"][0]["billing"] == "api" and settings.load().tools["codex"].billing == "api"
    assert board.command("tools.billing", {"tool": "codex", "billing": "subscription"})["hand"][0]["billing"] == "subscription"
    with pytest.raises(CommandError, match="not in your hand"):
        board.command("tools.billing", {"tool": "claude", "billing": "subscription"})


# -- Put back and Undo ------------------------------------------------------------------------------------------------

def test_a_tool_is_put_back_and_the_toasts_undo_brings_it_back(board, fake_repo):
    looked(board)
    for t in ("claude", "codex"):
        add(board, t)
    slug = ideas.add_track(fake_repo, "Art")
    goal_team.set_tool(fake_repo, slug, "claude")                                            # a party set to Claude Code by name
    said = board.command("tools.put_back_plan", {"tool": "claude"})                          # said under the button before it is pressed: nothing changes
    assert said["next"] == "codex" and said["parties"][0]["goes_on_with"] == "codex" and board.snapshot()["tools"]["order"] == ["claude", "codex"]
    assert goal_team.tool_of(fake_repo, slug) == "claude"
    got = board.command("tools.put_back", {"tool": "claude"})
    assert got["ok"] and got["plan"] == said and got["plan"]["line"] == "The orks stop using it after the task at work"
    assert got["plan"]["parties"][0]["line"] == "Art is set to Claude Code: it goes on with Codex, the next in your hand"
    assert board.snapshot()["tools"]["order"] == ["codex"] and board.snapshot()["tools"]["main"] == "codex"
    assert goal_team.tool_of(fake_repo, slug) == "codex"                                     # it goes on with the next in the hand
    saved = settings.load()
    assert not saved.tools["claude"].enabled and saved.tool_order == ["codex"]
    board.command("tools.put_back_undo", {"undo": got["undo"]})
    assert board.snapshot()["tools"]["order"] == ["claude", "codex"] and board.snapshot()["tools"]["main"] == "claude"
    assert goal_team.tool_of(fake_repo, slug) == "claude" and settings.load().tools["claude"].enabled
    with pytest.raises(CommandError, match="nothing to undo"):
        board.command("tools.put_back_undo", {"undo": "claude"})


def test_the_last_tool_asks_before_it_is_put_back(board):
    looked(board)
    add(board, "claude")
    asks = board.command("tools.put_back", {"tool": "claude"})
    assert board.command("tools.put_back_plan", {"tool": "claude"})["last"] is True
    assert asks["ok"] is False and asks["ask"] == "Without it nothing is worked on: goals wait in the Orkmaster's column until you add a tool"
    assert board.snapshot()["tools"]["order"] == ["claude"]                                  # nothing changed
    sure = board.command("tools.put_back", {"tool": "claude", "sure": True})
    assert sure["ok"] and board.snapshot()["tools"]["order"] == [] and board.snapshot()["tools"]["main"] == ""
    board.command("tools.put_back_undo", {"undo": sure["undo"]})
    assert board.snapshot()["tools"]["order"] == ["claude"] and board.snapshot()["tools"]["main"] == "claude"
    with pytest.raises(CommandError, match="not in your hand"):
        board.command("tools.put_back", {"tool": "codex"})


def test_a_tool_put_back_is_taken_out_of_the_work_that_follows_the_main_tool(board):
    """The order is what the work reads (`tool_now`): a tool put back is not moved on to, and the main tool passes to the next."""
    from orkboard.realm import tool_now
    looked(board)
    for t in ("claude", "codex"):
        add(board, t)
    board.command("tools.put_back", {"tool": "claude"})
    got = tool_now.now(board.machine, [], 0.0)
    assert got["main"] == "codex" and got["now"] == "codex"
    assert tool_hand.hand(board.machine) == ["codex"]
