"""Spec 130 C.1–C.4 (decisions §232.2, §232.6; mockup docs/mockups/setup/ #parties, #seat), in a real browser on Orkboard's real host: the parties as the Orkmaster's large card on the table: its width, the kinds' list and the stage's mark, a party's line and its heads with the shadows, the size switch that
changes the heads at once and saves nothing, Start that makes the parties and lays the table, Save afterwards, and a head pressed that opens its seat, its AI tool and its level. It replaces the place of two halves (spec 100 §4). No tool is called."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import first_open, goal_team, ideas, project_kind, project_stage  # noqa: E402
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


def test_the_card_is_large_says_what_the_project_is_and_never_covers_the_potions(desk, game):
    d, pg = open_first(desk, game)
    box = pg.locator(CARD).bounding_box()
    assert pg.locator(CARD).evaluate("e => e.offsetWidth") == 620
    assert "The parties for skyhop".upper() in pg.locator(".pc-title").inner_text().upper()
    assert pg.locator(".pc-kind select").input_value() == "game"
    assert pg.locator('[data-how="1"]').inner_text().startswith("read from ")
    pot = pg.locator(".hand-mana").bounding_box()                                                                      # the drum (the potions lie in a row only while it is unrolled)
    assert box["x"] + box["width"] <= pot["x"] or box["y"] + box["height"] <= pot["y"]
    assert pg.locator(".parties__left, .parties__right").count() == 0, "its half-and-half layout is gone"
    assert not d.errors, d.errors


def test_the_stage_is_marked_and_set_by_a_press_on_anothers_heading(desk, game):
    d, pg = open_first(desk, game)
    here = pg.locator('.pc-stage[data-stage-head="idea"]')
    assert "The project is here" in here.inner_text()
    assert pg.locator('.pc-later [data-party="liveops"]').count() == 1, "the stages not reached lie in one line"
    pg.locator('.pc-stage[data-stage-head="being_made"]').click()
    pg.locator('.pc-stage[data-stage-head="being_made"] .parties__here').wait_for(timeout=WAIT_MS)
    assert project_stage.current(d.host.ideas.state_dir, d.host.repo_root)["stage"] == "being_made"
    assert row(pg, "tech").get_attribute("data-on") == "true", "the parties of a stage reached come ticked"
    assert not d.errors, d.errors


def test_a_partys_line_its_heads_and_its_shadows_and_the_size_changes_them_at_once_and_saves_nothing(desk, game):
    d, pg = open_first(desk, game)
    r = row(pg, "game-design")
    assert r.get_attribute("data-size") == "lean" or r.get_attribute("data-size") == "standard"
    r.locator('[data-size="lean"]').click()
    assert r.locator('.pc-grp[data-band="build"] [data-seat]').count() == 1 and r.locator('.pc-grp[data-band="check"] [data-seat]').count() == 0, "Lean: the first who does, no checker"
    assert r.locator(".pc-hd.is-empty").count() >= 3, "Lean: the rest are shadows"
    assert "Lean: one does it, the leader accepts it" in r.inner_text()
    assert "is-dim" in r.locator('.pc-grp[data-band="check"]').get_attribute("class")
    r.locator('[data-size="standard"]').click()
    assert r.locator('.pc-grp[data-band="build"] [data-seat]').count() == 2 and r.locator('.pc-grp[data-band="check"] [data-seat]').count() == 1
    assert r.locator('[data-lean="1"]').count() == 0
    r.locator('[data-size="full"]').click()
    assert r.locator('.pc-grp[data-band="build"] button[data-seat]').count() >= 2
    assert pg.locator(".pc-grp[data-band=build] .pc-hd.is-empty").first.get_attribute("title").endswith("an empty seat")
    assert parties_of(d.host) == {}, "nothing saved until Start"
    title = r.locator('[data-size="standard"]')
    pg.wait_for_function("(s) => /about \\$[0-9.]+–[0-9.]+ a goal/.test(document.querySelector(s).title)", arg='.pc-row[data-party="game-design"] [data-size="standard"]', timeout=WAIT_MS)
    assert title.get_attribute("aria-label").startswith("Standard: about $")
    assert not d.errors, d.errors


def test_a_shadow_is_not_pressed_and_release_is_a_craft_as_any(desk, game):
    """Decisions §274.1: Release is offered as any craft, ticked where its stage is reached, and can be unticked."""
    d, pg = open_first(desk, game)
    r = row(pg, "release")
    box = r.locator('[role="checkbox"]')
    assert r.get_attribute("data-locked") == "false" and box.get_attribute("aria-disabled") != "true"
    assert box.get_attribute("aria-checked") == "true" and "in every project" not in r.inner_text()
    box.click()
    pg.wait_for_function("() => document.querySelector('.pc-row[data-party=release] [role=checkbox]').getAttribute('aria-checked') === 'false'", timeout=WAIT_MS)
    assert pg.locator("button.pc-hd.is-empty").count() == 0
    assert not d.errors, d.errors


def test_the_leaders_mark_is_framed_when_it_follows_the_main_tool_and_bare_when_set(desk, game):
    d, pg = open_first(desk, game)
    r = row(pg, "art")
    mark = r.locator(".pc-lmark")
    assert "is-framed" in mark.get_attribute("class") and mark.get_attribute("data-tool") == "claude"
    r.locator(".pc-lead").click()
    seat = pg.locator(".pc-seat")
    seat.wait_for(timeout=WAIT_MS)
    assert "The party's AI tool" in seat.text_content() and seat.locator("select option").first.text_content().startswith("Main tool (")
    seat.locator("select").select_option("codex")
    pg.wait_for_function("() => document.querySelector('.pc-row[data-party=art] .pc-lmark').dataset.tool === 'codex'", timeout=WAIT_MS)
    assert "is-framed" not in mark.get_attribute("class")
    assert not d.errors, d.errors


def test_a_seat_says_its_tool_and_its_level_as_three_heads_and_a_leader_on_novice_says_the_cost(desk, game):
    d, pg = open_first(desk, game)
    r = row(pg, "game-design")
    r.locator('[data-size="standard"]').click()
    r.locator(".pc-lead").click()
    seat = pg.locator(".pc-seat")
    seat.wait_for(timeout=WAIT_MS)
    tiles = seat.locator(".pc-tier")
    assert tiles.count() == 3 and [t.text_content().split("≈")[0] for t in tiles.all()] == ["Novice", "Seasoned", "Veteran"]
    assert seat.locator("[data-off]").count() == 0, "never for the leader"
    pg.wait_for_function("() => document.querySelector('.pc-tier small')", timeout=WAIT_MS)
    assert "a step" in tiles.first.inner_text()
    seat.locator('[data-tier="laborer"]').click()
    seat.locator('[data-novice="1"]').wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    seat.wait_for(state="detached", timeout=WAIT_MS)
    assert pg.locator(CARD).count() == 1, "Esc lowers the seat first"
    member = r.locator('.pc-grp[data-band="build"] button[data-seat]').first
    slug = member.get_attribute("data-seat")
    member.click()
    seat.wait_for(timeout=WAIT_MS)
    assert seat.locator("select option").first.text_content().startswith("As the party (")
    seat.locator("select").select_option("codex")
    r.locator(f'[data-seat="{slug}"] .pc-own').wait_for(timeout=WAIT_MS)
    seat.locator(f'[data-off="{slug}"]').click()
    r.locator(f'button[data-seat="{slug}"]').wait_for(state="detached", timeout=WAIT_MS)
    pg.locator('[data-act="start"]').click()
    pg.locator(CARD).wait_for(state="detached", timeout=WAIT_MS)
    made = next(t for t in parties_of(d.host).values() if t["recipe"] == "game-design")
    assert slug not in made["team"]
    assert goal_team.tiers_of(d.host.ideas.root(), made["slug"]).get(made["leader"]) == "laborer", "a seat set by hand keeps what was set"
    assert made["size"] == "standard", "and the party's size stays picked"
    assert not d.errors, d.errors


def test_its_foot_says_what_they_cost_and_start_makes_the_parties_and_lays_the_table(desk, game):
    d, pg = open_first(desk, game)
    assert first_open.laid(d.host.ideas.state_dir, d.host.repo_root) is False
    pg.wait_for_function("() => /Together ≈ \\$[0-9.]+–[0-9.]+ a goal at the API's prices. On a subscription it is taken from its limits instead./.test(document.querySelector('[data-total]').textContent)", timeout=WAIT_MS)
    pg.locator('[data-act="start"]').click()
    pg.locator(CARD).wait_for(state="detached", timeout=WAIT_MS)
    pg.locator('.frame[data-laid="1"]').wait_for(timeout=WAIT_MS)
    until(pg, lambda: first_open.kept(d.host.ideas.state_dir))                  # the table is laid as the parties are made; Start's last step (the project's questions) keeps it a moment after
    assert first_open.kept(d.host.ideas.state_dir) is True
    assert set(p["recipe"] for p in parties_of(d.host).values()) >= {"game-design", "art", "release"}
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


def test_the_leaders_seat_of_a_made_party_says_what_it_keeps_of_the_project(desk, game):
    d, pg = open_first(desk, game)
    pg.locator('[data-act="start"]').click()
    pg.locator(CARD).wait_for(state="detached", timeout=WAIT_MS)
    pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.over.value === null)", timeout=WAIT_MS)      # the start has finished (its last step closes the card it came from): the chair is pressed after it
    edit_parties(pg)
    row(pg, "art").locator(".pc-lead").click()
    facts = pg.locator(".pc-seat [data-facts]")
    facts.wait_for(timeout=WAIT_MS)
    assert "Sprite Dryad" in pg.locator(".pc-seat").inner_text(), "the leader's name of its own (§164)"
    facts.locator('[data-act="add-fact"]').click()
    facts.locator("[data-adding] input").fill("Pixel art at 16 px")
    facts.locator("[data-adding] button").click()
    facts.locator(".parties__fact input").first.wait_for(timeout=WAIT_MS)
    assert not d.errors, d.errors


def test_the_kind_is_corrected_from_the_list_and_the_parties_are_asked_again(desk, game):
    d, pg = open_first(desk, game)
    pg.locator(".pc-kind select").select_option("web")
    pg.wait_for_function("() => document.querySelector('.pc-kind select').value === 'web'", timeout=WAIT_MS)
    until(pg, lambda: project_kind.kept(d.host.ideas.state_dir) == "web")
    assert not d.errors, d.errors


def test_at_the_narrow_width_the_card_is_the_screen(desk, game):
    d, pg = open_first(desk, game, width=420)
    assert pg.locator(CARD).evaluate("e => e.offsetWidth") <= 420 and pg.evaluate("() => document.documentElement.scrollWidth <= innerWidth + 1")
    assert not d.errors, d.errors


def test_a_facts_key_is_made_of_its_first_words_and_the_hosts_format(desk, game):
    d, pg = open_first(desk, game)
    got = pg.evaluate("() => import('/static/js/table/partyseats2.js').then((m) => [m.factKey('Who pays for it?', []), m.factKey('Who pays for it?', ['who_pays_for_it']), m.factKey('!!', []), m.factKey('x'.repeat(80), ['x'.repeat(36)])])")
    assert got[0] == "who_pays_for_it" and got[1] == "who_pays_for_it_2" and got[2] == "fact" and len(got[3]) <= 40
    assert not d.errors, d.errors
