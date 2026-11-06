"""Spec 130 B (decisions §232.3–§232.5, §232.8, §232.10; mockup docs/mockups/setup/), in a real browser on Orkboard's real host, with `tools.detect` and the request faked: the potions' empty slot, the card that adds one AI tool, a potion's own card, and the
Orkmaster's setup cards."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard import settings  # noqa: E402
from orkboard.realm import first_open, project_kind, tool_errors, tool_hand  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.first_open_kit import desk, found, git_repo  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser
SLOT = '[data-empty-slot="1"]'
ADD = '[data-lift="add-tool"]'
TEST = '[data-test-add="1"]'


def laid_project(host):
    first_open.lay(host.ideas.state_dir)
    project_kind.keep(host.ideas.state_dir, "code")


def fill_hand(host, *ids):
    for t in ids:
        tool_hand.add(host.machine, t, "subscription")
    settings.save(host.machine)
    host.on_change()


def order_of(host):
    return tool_hand.hand(host.machine)


@pytest.fixture
def project(tmp_path):
    return git_repo(tmp_path / "shop")


def open_desk(desk, project, *hand, status=None, laid=True):
    d = desk(project, **({"status": status} if status else {}))
    if laid:
        laid_project(d.host)
    fill_hand(d.host, *hand)
    d.host.tools_host.scan()
    d.host.tools_host._finder.join(5)
    pg = d.open()
    pg.wait_for_selector(SLOT if len(hand) < 6 else ".hand-pot", state="attached", timeout=WAIT_MS)
    return d, pg


def test_the_empty_slot_is_faint_at_rest_lit_when_the_orkmaster_asks_and_gone_at_six(desk, project):
    d, pg = open_desk(desk, project, "claude")
    slot = pg.locator(SLOT)
    assert slot.get_attribute("aria-label") == "Add an AI tool" and "is-lit" not in slot.get_attribute("class")
    assert pg.locator(".hand-pot").first.get_attribute("data-provider") == "claude"
    assert pg.locator(".hand-mana > .hand-pot").last.get_attribute("data-empty-slot") == "1", "the row ends with it"
    fill_hand(d.host, *[t for t in ("codex", "agy", "cursor", "pi", "hermes")])
    pg.wait_for_function("(s) => !document.querySelector(s)", arg=SLOT, timeout=WAIT_MS)
    assert not d.errors, d.errors


def test_the_empty_slot_is_lit_and_the_card_comes_up_while_the_orkmaster_asks_for_a_tool(desk, project):
    d = desk(project)
    project_kind.keep(d.host.ideas.state_dir, "code")
    pg = d.open()
    pg.wait_for_selector(ADD, timeout=WAIT_MS)
    assert "is-lit" in pg.locator(SLOT).get_attribute("class")
    assert "Which AI tool shall the orks think with?" in pg.locator(".fo-bubble").inner_text()
    assert not d.errors, d.errors


def test_the_cards_groups_and_the_first_ready_tool_picked_and_one_not_installed_is_never_picked(desk, project):
    d, pg = open_desk(desk, project, status=lambda: found("claude", "codex", "agy", signed_out=("agy",)))
    pg.locator(SLOT).click()
    pg.locator(f"{ADD} select[name=tool]").wait_for(timeout=WAIT_MS)
    assert "Add an AI tool · 1 of up to 6" in pg.locator(ADD).text_content()
    groups = pg.eval_on_selector_all(f"{ADD} select[name=tool] optgroup", "els => els.map((e) => [e.label, e.children.length])")
    assert [g[0] for g in groups] == ["Ready", "Not signed in", "Not installed"], groups
    assert pg.locator(f"{ADD} select[name=tool]").input_value() == "claude"
    assert pg.eval_on_selector_all(f"{ADD} optgroup[data-group=not_installed] option", "els => els.every((e) => e.disabled)")
    assert "Nothing else was run, and no key was read" in pg.locator(ADD).inner_text()
    assert not d.errors, d.errors


def test_the_third_line_follows_and_test_and_add_waits_for_a_sign_in_and_for_a_key(desk, project, monkeypatch):
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    d, pg = open_desk(desk, project, status=lambda: found("claude", "codex", "agy", signed_out=("agy",)))
    pg.locator(SLOT).click()
    tool, paid, test = pg.locator(f"{ADD} select[name=tool]"), pg.locator(f"{ADD} select[name=billing]"), pg.locator(TEST)
    tool.wait_for(timeout=WAIT_MS)
    assert "Signed in to your subscription" in pg.locator(ADD).inner_text() and test.is_enabled()
    tool.select_option("agy")
    pg.locator(f'{ADD} [data-third="signed_out"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(f"{ADD} [data-sign-in=agy]").count() == 1 and test.is_disabled(), "it waits for the sign-in"
    tool.select_option("codex")
    paid.select_option("api")
    pg.locator(f'{ADD} [data-third="no_key"]').wait_for(timeout=WAIT_MS)
    assert "CODEX_API_KEY" in pg.locator(ADD).inner_text() and test.is_disabled(), "it names the variable and waits"
    assert pg.locator(f"{ADD} input[type=password], {ADD} input[name*=key]").count() == 0, "no field to type a key in"
    assert not d.asked, "nothing was run"
    assert not d.errors, d.errors


def test_a_key_in_the_way_is_said_before_it_costs_and_its_value_nowhere(desk, project, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-the-secret-value")
    d, pg = open_desk(desk, project)
    pg.locator(SLOT).click()
    pg.locator(f"{ADD} [data-warn]").wait_for(timeout=WAIT_MS)
    text = pg.locator(ADD).inner_text()
    assert "ANTHROPIC_API_KEY is set in your environment" in text and "sk-the-secret-value" not in pg.content()
    assert not d.errors, d.errors


def test_test_and_add_turns_the_card_and_go_on_leaves_the_first_potion_framed(desk, project):
    d = desk(project)
    project_kind.keep(d.host.ideas.state_dir, "code")
    pg = d.open()
    pg.locator(TEST).wait_for(timeout=WAIT_MS)
    pg.locator(TEST).click()
    turned = pg.locator(f'{ADD} [data-turned="1"]')
    turned.wait_for(timeout=WAIT_MS)
    assert d.asked == ["claude"] and "Claude Code is in your hand. Add another AI tool?" in turned.inner_text()
    pot = pg.locator('.hand-pot[data-provider="claude"]')
    pot.wait_for(timeout=WAIT_MS)
    assert pot.get_attribute("data-default") == "1", "the first tool is the main tool"
    turned.get_by_role("button", name="Add another").click()
    pg.locator(TEST).wait_for(timeout=WAIT_MS)
    pg.wait_for_function("(s) => document.querySelector(s).value === 'codex'", arg=f"{ADD} select[name=tool]", timeout=WAIT_MS)
    assert pg.locator(f'{ADD} option[value="claude"]').count() == 0, "without the tools in the hand"
    pg.locator(TEST).click()
    pg.locator(f'{ADD} [data-done="1"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(f'{ADD} [data-done="1"]').inner_text().upper() == "GO ON"
    assert not d.errors, d.errors


def test_a_failure_says_why_in_the_tools_words_and_adds_nothing(desk, project):
    d, pg = open_desk(desk, project)
    d.fail["claude"] = tool_errors.ToolError("claude", "401 unauthorized")
    pg.locator(SLOT).click()
    pg.locator(TEST).wait_for(timeout=WAIT_MS)
    pg.locator(TEST).click()
    pg.locator(f'{ADD} [data-failed="1"]').wait_for(timeout=WAIT_MS)
    assert order_of(d.host) == [] and pg.locator('.hand-pot[data-provider="claude"]').count() == 0
    assert not d.errors, d.errors


def test_closing_the_card_with_no_tool_says_what_follows_and_goes_on(desk, project):
    d = desk(project)
    project_kind.keep(d.host.ideas.state_dir, "code")
    pg = d.open()
    pg.locator(ADD).wait_for(timeout=WAIT_MS)
    pg.locator(f'{ADD} [data-close="1"]').click()
    pg.get_by_text("No AI tool: the Board opens, and nothing is worked on until you add one").wait_for(timeout=WAIT_MS)
    pg.locator(ADD).wait_for(state="detached", timeout=WAIT_MS)
    assert d.host.first_open.tools_skipped is True
    assert not d.errors, d.errors


def test_a_potions_card_orders_with_the_arrows_and_by_dragging(desk, project):
    d, pg = open_desk(desk, project, "claude", "codex", "agy")
    pg.locator('.hand-pot[data-provider="codex"]').click()
    card = pg.locator('[data-lift="tool"][data-tool="codex"]')
    card.wait_for(timeout=WAIT_MS)
    card.locator('[data-left="1"]').click()
    pg.wait_for_function("() => document.querySelector('.hand-pot').dataset.provider === 'codex'", timeout=WAIT_MS)
    assert order_of(d.host) == ["codex", "claude", "agy"] and d.host.machine.main_tool == "codex", "the first is the main tool"
    assert pg.locator('.hand-pot[data-provider="codex"]').get_attribute("data-default") == "1"
    pg.keyboard.press("Escape")
    card.wait_for(state="detached", timeout=WAIT_MS)
    pg.locator('.hand-pot[data-provider="agy"]').drag_to(pg.locator('.hand-pot[data-provider="codex"]'))
    pg.wait_for_function("() => document.querySelector('.hand-pot').dataset.provider === 'agy'", timeout=WAIT_MS)
    assert order_of(d.host) == ["agy", "codex", "claude"]
    assert not d.errors, d.errors


def test_put_back_says_what_follows_goes_at_once_and_undo_brings_it_back(desk, project):
    d, pg = open_desk(desk, project, "claude", "codex")
    pg.locator('.hand-pot[data-provider="claude"]').click()
    card = pg.locator('[data-lift="tool"]')
    plan = card.locator('[data-plan="1"]')
    plan.wait_for(timeout=WAIT_MS)
    assert "The orks stop using it after the task at work" in plan.inner_text() and order_of(d.host) == ["claude", "codex"], "said before; nothing changed"
    card.locator('[data-put-back="1"]').click()
    pg.locator('.hand-pot[data-provider="claude"]').wait_for(state="detached", timeout=WAIT_MS)
    assert order_of(d.host) == ["codex"]
    pg.get_by_role("button", name="Undo").click()
    pg.locator('.hand-pot[data-provider="claude"]').wait_for(timeout=WAIT_MS)
    assert order_of(d.host) == ["claude", "codex"] and d.host.machine.main_tool == "claude"
    assert not d.errors, d.errors


def test_the_last_tool_asks_first(desk, project):
    d, pg = open_desk(desk, project, "claude")
    pg.locator('.hand-pot[data-provider="claude"]').click()
    card = pg.locator('[data-lift="tool"]')
    card.locator('[data-put-back="1"]').click()
    last = card.locator('[data-last="1"]')
    last.wait_for(timeout=WAIT_MS)
    assert "Without it nothing is worked on" in last.inner_text() and order_of(d.host) == ["claude"]
    assert "Keep it" not in last.inner_text()
    last.locator('[data-sure="1"]').click()
    pg.locator('.hand-pot[data-provider="claude"]').wait_for(state="detached", timeout=WAIT_MS)
    assert order_of(d.host) == []
    assert not d.errors, d.errors


def test_what_used_it_is_a_link_on_the_card(desk, project):
    d, pg = open_desk(desk, project, "claude")
    pg.locator('.hand-pot[data-provider="claude"]').click()
    pg.locator('[data-used="1"]').click()
    pg.locator('.table-over[data-kind="limits"]').wait_for(timeout=WAIT_MS)
    assert not d.errors, d.errors


def test_the_setup_cards_answers_move_the_question_on(desk, tmp_path):
    folder = tmp_path / "nogit"
    folder.mkdir()
    (folder / "project.godot").write_text("[application]\n", encoding="utf-8")
    d = desk(folder)
    pg = d.open()
    pg.locator(f'{ADD} [data-close="1"]').click()                       # the tools' card comes first (spec 150 G): closed with none added, the project's step
    card = pg.locator('[data-setup="git"]')
    card.wait_for(timeout=WAIT_MS)
    assert "Start git here?" in pg.locator(".fo-bubble").inner_text()
    card.locator('[data-start-git="1"]').click()
    pg.locator('[data-setup="ring"] [data-ring-go="1"]').click()            # its release branch said, the table comes
    kind = pg.locator('[data-setup="kind"]')
    kind.wait_for(timeout=WAIT_MS)
    assert "Right?" in kind.inner_text() and kind.locator(".ork-chip").count() >= 1, "the signs read as chips"
    kind.locator('[data-else="1"]').click()
    kind.locator('[data-kind="game"]').click()
    pg.locator('[data-setup="parties"]').wait_for(timeout=WAIT_MS)
    assert project_kind.kept(d.host.ideas.state_dir) == "game"
    assert not d.errors, d.errors


def test_an_empty_folder_asks_what_it_is_for(desk, tmp_path):
    folder = git_repo(tmp_path / "blank", ".gitkeep", "")
    d = desk(folder)
    pg = d.open()
    pg.locator(f'{ADD} [data-close="1"]').click()                       # the tools' card first, closed
    kind = pg.locator('[data-setup="kind"]')
    kind.wait_for(timeout=WAIT_MS)
    assert "The folder is empty. What is it for?" in kind.inner_text()
    assert kind.locator('[data-read="1"]').is_disabled()
    kind.locator('[data-kinds="1"]').click()
    kind.locator('[data-kind="web"]').click()
    pg.locator('[data-setup="parties"]').wait_for(timeout=WAIT_MS)
    assert project_kind.kept(d.host.ideas.state_dir) == "web"
    assert not d.errors, d.errors
