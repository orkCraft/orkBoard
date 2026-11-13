"""Spec 130 C.1–C.4 (decisions §232.2, §232.6; mockup docs/mockups/setup/ #parties, #seat), in a real browser on Orkboard's real host: the parties as the Orkmaster's large card on the table: its width, the kinds' list and the stage's mark, a party's line and its heads with the shadows, the size switch that
changes the heads at once and saves nothing, Start that makes the parties and lays the table, Save afterwards, and a head pressed that opens its seat, its AI tool and its level. It replaces the place of two halves (spec 100 §4). No tool is called."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import first_open, ideas, project_kind, project_stage  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.first_open_kit import desk, git_repo  # noqa: E402,F401  (fixture)
from tests.test_add_tool_browser import fill_hand  # noqa: E402

pytestmark = pytest.mark.browser
CARD = ".parties.ork-card"


def row(pg, party):
    return pg.locator(f'.pc-row[data-party="{party}"]')


@pytest.fixture
def game(tmp_path):
    return git_repo(tmp_path / "skyhop", "project.godot", "[application]\n")


def open_first(desk, root, width=1280, stage="idea"):
    d = desk(root, width=width)
    project_kind.keep(d.host.ideas.state_dir, "game")
    project_stage.keep(d.host.ideas.state_dir, stage)
    fill_hand(d.host, "claude", "codex")
    pg = d.open()
    if width >= 760:                                                         # the first open's room (spec 150 G): the parties are chairs, their large card a press away
        pg.locator('[data-setup="parties"] [data-act="parties"]').click()
    pg.wait_for_selector(f"{CARD} .pc-row", timeout=WAIT_MS)
    return d, pg


def edit_parties(pg):
    """The place of the parties again, as a party's *Edit* opens it (`openParties`; spec 161 I: the new chair deals its crafts to the hand instead, tests/test_chair_deal_browser.py)."""
    pg.evaluate("() => import('/static/js/table/parties.js').then((m) => m.openParties({}))")
    pg.locator(f"{CARD} .pc-row").first.wait_for(timeout=WAIT_MS)


def until(pg, ok):
    for _ in range(50):
        if ok():
            return
        pg.wait_for_timeout(100)
    assert ok()


def parties_of(host):
    return {t["slug"]: t for t in ideas.tracks(host.ideas.root(), make=False) if t["slug"] != ideas.GENERAL}














def test_its_foot_says_what_they_cost_and_start_makes_the_parties_and_lays_the_table(desk, game):
    d, pg = open_first(desk, game)
    assert first_open.laid(d.host.ideas.state_dir, d.host.repo_root) is False
    pg.wait_for_function("() => /Together ≈ \\$[0-9.]+–[0-9.]+ a goal at the API's prices. On a subscription it is taken from its limits instead./.test(document.querySelector('[data-total]').textContent)", timeout=WAIT_MS)
    pg.locator('[data-act="start"]').click()
    pg.locator(CARD).wait_for(state="detached", timeout=WAIT_MS)
    pg.locator('.frame[data-laid="1"]').wait_for(timeout=WAIT_MS)
    until(pg, lambda: first_open.kept(d.host.ideas.state_dir))                  # the table is laid as the parties are made; Start's last step (the project's questions) keeps it a moment after
    assert first_open.kept(d.host.ideas.state_dir) is True
    assert set(p["recipe"] for p in parties_of(d.host).values()) >= {"game-design", "art"} and "release" not in set(p["recipe"] for p in parties_of(d.host).values())
    assert not d.errors, d.errors


def test_later_the_same_card_saves_only_what_changed_from_the_next_task(desk, game):
    d, pg = open_first(desk, game)
    pg.locator('[data-act="start"]').click()
    pg.locator(CARD).wait_for(state="detached", timeout=WAIT_MS)
    pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.over.value === null)", timeout=WAIT_MS)      # the start has finished (its last step closes the card it came from): the chair is pressed after it
    edit_parties(pg)
    pg.locator(f"{CARD} .pc-row").first.wait_for(timeout=WAIT_MS)
    save = pg.locator('[data-act="save"]')
    assert save.is_disabled() and "From the next task" in pg.locator(".pc-foot").inner_text()
    assert row(pg, "art").locator('[role="checkbox"]').get_attribute("aria-disabled") == "true", "a made party is ticked for good here"
    row(pg, "art").locator('[data-size="full"]').click()
    save.click()
    pg.locator(CARD).wait_for(state="detached", timeout=WAIT_MS)
    assert next(t for t in parties_of(d.host).values() if t["recipe"] == "art")["size"] == "full"
    assert not d.errors, d.errors








