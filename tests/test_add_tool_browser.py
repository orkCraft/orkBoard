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


def unroll(pg):
    """The wide width's tools lie in the row the drum unrolls into (spec 156 E.5): the pointer rests on the drum."""
    pg.locator(".pots__row").wait_for(timeout=WAIT_MS)
    b = pg.locator(".pots__row").bounding_box()
    pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    pg.locator(".pots[data-open]").wait_for(timeout=WAIT_MS)


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
    pot.wait_for(state="attached", timeout=WAIT_MS)
    assert pg.locator('.pot-s[data-provider="claude"]').count() == 1 and pg.locator(".pot-s.is-front").get_attribute("data-provider") == "claude", "the first tool is the main tool: in front of the drum"
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
    unroll(pg)
    pg.locator(SLOT).click()
    pg.locator(TEST).wait_for(timeout=WAIT_MS)
    pg.locator(TEST).click()
    pg.locator(f'{ADD} [data-failed="1"]').wait_for(timeout=WAIT_MS)
    assert order_of(d.host) == [] and pg.locator('.hand-pot[data-provider="claude"]').count() == 0
    assert not d.errors, d.errors






def test_put_back_says_what_follows_goes_at_once_and_undo_brings_it_back(desk, project):
    d, pg = open_desk(desk, project, "claude", "codex")
    unroll(pg)
    pg.locator('.hand-pot[data-provider="claude"]').click()
    card = pg.locator('[data-lift="tool"]')
    plan = card.locator('[data-plan="1"]')
    plan.wait_for(timeout=WAIT_MS)
    assert "The orks stop using it after the task at work" in plan.inner_text() and order_of(d.host) == ["claude", "codex"], "said before; nothing changed"
    card.locator('[data-put-back="1"]').click()
    pg.locator('.hand-pot[data-provider="claude"]').wait_for(state="detached", timeout=WAIT_MS)
    assert order_of(d.host) == ["codex"]
    pg.get_by_role("button", name="Undo").click()
    pg.locator('.hand-pot[data-provider="claude"]').wait_for(state="attached", timeout=WAIT_MS)
    assert order_of(d.host) == ["claude", "codex"] and d.host.machine.main_tool == "claude"
    assert not d.errors, d.errors








