"""Spec 90 part B on the desktop (docs/specs/90-what-the-first-look-said.md §2–§4, §7 B; decisions §105.2–§105.4): Chromium at 1 440 × 900 against the arena's, the project's, Assets' and System's
stub hosts. With nothing open there is no right column and the pane takes the width; a thing opened (Agents, an asset, a part of System) is the window's right column, max(480px, 34%) wide and at most
640 px, docked beside the pane and pushing it, never over it; Esc, or the last tab's ×, closes it. No *Waits for your look* column: a result to look at is the hand's card; *Merge dev into main* is one
card, *n goals ready for main*, its answer *Merge into main*, and a quiet line under the project's line; the limits are under *Spend* in the top bar; the canvases are a kind of Assets; Assets' kinds lie
as sections one under another, their cards wrapping across the width; a party's tabs and its members' faces lie on the table's wood, the table beginning under the party's line. Screenshots to the
directory ORKCRAFT_SHOTS_DIR names when it is set (right-closed.png, right-open.png, assets-sections.png)."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui, open_pane  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import ArenaHost  # noqa: E402
from tests.test_assets_desktop_browser import AssetsHost, _assets, _card, serve  # noqa: E402
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _calls, _open, _sent, _stop  # noqa: E402
from tests.test_system_desktop_browser import OLD as SYS_OLD, SystemHost, _part, _rest, _seed, _tech  # noqa: E402

pytestmark = pytest.mark.browser

CANVASES = [{"key": "claude:https://claude.ai/artifact/0f3c", "tool": "claude", "tool_word": "Claude", "kind": "design", "title": "Onboarding", "at": "2026-10-26T10:00:00",
             "host": "claude.ai", "url": "https://claude.ai/artifact/0f3c", "local": False, "head": {"craft": "design", "race": "elf", "tier": "warrior"}, "idea": "", "task": ""}]


class CanvasHost(AssetsHost):
    """Assets' world with one canvas not yet seen (`ideas.canvases`, spec 78)."""

    def __init__(self):
        super().__init__()
        self.canvases, self.seen = copy.deepcopy(CANVASES), []

    def handle(self, name, a):
        if name == "ideas.canvases":
            self.log.append((name, a))
            return {"canvases": copy.deepcopy(self.canvases), "seen": copy.deepcopy(self.seen)}
        if name == "ideas.canvas_seen":
            self.log.append((name, a))
            self.seen += [c for c in self.canvases if c["key"] == a["key"]]
            self.canvases = [c for c in self.canvases if c["key"] != a["key"]]
            return {"ok": True}
        return super().handle(name, a)


@pytest.fixture
def party(gui):
    pg, host, errors = _open(gui, host=ArenaHost(), ready=".arena-phead")
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


@pytest.fixture
def assets(gui, tmp_path):
    pg, host, errors = _open(gui, host=CanvasHost(), ready=".arena[data-goal=passkey]")
    serve(pg, tmp_path)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


@pytest.fixture
def tech(gui):
    pg, host, errors = _open(gui, host=SystemHost(), ready=".arena[data-goal=passkey]")
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _box(pg, sel):
    return pg.locator(sel).first.bounding_box()


def _column(pg):
    """The right column, once it is out."""
    pg.locator(".shell-drawer").wait_for(timeout=WAIT_MS)
    return pg.locator(".shell-drawer")


def _pushes(pg):
    """The right column is docked at the window's right, as wide as §2 says, and the pane ends where it begins: nothing of the pane under it."""
    col, arena = _box(pg, ".shell-drawer"), _box(pg, ".shell-main > .arena")
    want = min(640, max(480, 0.34 * 1440))
    assert abs(col["width"] - want) <= 1 and abs(col["x"] + col["width"] - 1440) <= 1, col
    assert abs(arena["x"] + arena["width"] - col["x"]) <= 1 and arena["width"] < 1440 - 470                # pushed: the pane narrowed by it, never covered
    assert pg.locator(".shell-drawer").evaluate("e => getComputedStyle(e).position") != "absolute"


# -- §2.1: no right column with nothing open; one opened pushes the pane; Esc and the last × close it ------------------------------------------------------------

def test_no_right_column_with_nothing_open_one_opened_pushes_the_pane_and_esc_or_the_last_tab_closes_it(party):
    pg, host = party
    assert pg.locator(".shell-drawer").count() == 0 and abs(_box(pg, ".shell-main > .arena")["width"] - 1440) <= 1             # nothing open: the pane takes the width
    assert pg.locator(".arena-look").count() == 0 and "Waits for your look" not in pg.locator("body").inner_text()              # no Waits column (§2.3)
    shot(pg, "right-closed.png")
    open_pane(pg, "agents")
    _column(pg)
    _pushes(pg)
    assert pg.locator(".arena-play").bounding_box()["width"] < 1440 - 480 - 240                                                 # the field itself is narrower: the pane was pushed
    pg.keyboard.press("Escape")                                                                                               # Esc: the column goes
    pg.locator(".shell-drawer").wait_for(state="detached", timeout=WAIT_MS)
    assert abs(_box(pg, ".shell-main > .arena")["width"] - 1440) <= 1
    open_pane(pg, "agents")                                                     # back, with its tab
    _column(pg).get_by_role("button", name="Close Agents").click()                                                            # the last tab's ×: no column at all
    pg.locator(".shell-drawer").wait_for(state="detached", timeout=WAIT_MS)
    assert abs(_box(pg, ".shell-main > .arena")["width"] - 1440) <= 1


# -- §2.2–§3: an asset opens in the right column, never over the window; Assets' sections across the width; the canvases are a kind of Assets ----------------------

def test_an_asset_pressed_opens_in_the_right_column_pushing_the_level_and_esc_closes_it(assets):
    pg, host = assets
    _assets(pg)
    _card(pg, "art/hero.png").click()
    col = _column(pg)
    lift = col.get_by_role("region", name="hero.png")
    lift.wait_for(timeout=WAIT_MS)
    assert pg.locator(".assets-lift").count() == 1 and pg.locator(".assets .assets-lift").count() == 0                         # in the column, nothing over the window
    assert col.locator(".shell-ptab.is-on .shell-ptab__main").text_content().split()[:2] == ["Asset", "hero.png"]                                  # a tab of its own kind
    img = lift.locator("img.assets-lift__img")
    pg.wait_for_function("e => e.complete && e.naturalWidth > 0", arg=img.element_handle(), timeout=WAIT_MS)
    assert abs(img.bounding_box()["width"] - 400) <= 1                                                                         # at its size: the column holds 400 px
    assert "is-on" in _card(pg, "art/hero.png").get_attribute("class")
    _pushes(pg)
    shot(pg, "right-open.png")
    _card(pg, "art/icon.png").click()                                                                                          # another replaces it in the passing tab
    col.get_by_role("region", name="icon.png").wait_for(timeout=WAIT_MS)
    assert col.locator(".shell-ptab").count() == 1
    pg.keyboard.press("Escape")
    pg.locator(".shell-drawer").wait_for(state="detached", timeout=WAIT_MS)
    assert pg.locator(".assets-lift").count() == 0


def test_assets_kinds_lie_as_sections_one_under_another_their_cards_wrapping_across_the_width(assets):
    pg, host = assets
    _assets(pg)
    secs = pg.locator(".assets-sec")
    assert [s.get_attribute("aria-label") for s in secs.all()] == ["Screens", "Art and icons", "Sound", "Music", "Clips", "Fonts", "Canvases"]
    boxes = [s.bounding_box() for s in secs.all()]
    assert all(abs(b["x"] - boxes[0]["x"]) <= 1 for b in boxes) and all(b["y"] > a["y"] + a["height"] - 1 for a, b in zip(boxes, boxes[1:]))     # one under another
    table = _box(pg, ".assets-body")
    assert all(b["width"] >= table["width"] - 96 for b in boxes)                                                               # each the width of the table
    pg.locator('.assets-sec[data-kind="art"] .assets-stk[data-n="7"] button').click()                                          # the stack opened: ten files of art
    cards = [c.bounding_box() for c in pg.locator('.assets-sec[data-kind="art"] .assets-card').all()]
    rows = sorted({round(c["y"]) for c in cards})
    assert len(cards) == 10 and len(rows) >= 2                                                                                 # they wrap …
    span = max(max(c["x"] + c["width"] for c in cards if round(c["y"]) == y) - min(c["x"] for c in cards if round(c["y"]) == y) for y in rows)
    assert span > table["width"] * 0.6                                                                                         # … across the width
    assert pg.locator(".arena-look, .arena-canvases__list").count() == 0
    shot(pg, "assets-sections.png")


def test_the_canvases_are_a_kind_of_assets_with_spec_78s_cards(assets):
    pg, host = assets
    _assets(pg)
    sec = pg.locator('.assets-sec[data-kind="canvas"]')
    sec.wait_for(timeout=WAIT_MS)
    assert sec.locator("h3").text_content().strip() == "Canvases 1" and sec.locator(".arena-canvas").count() == 1
    card = sec.locator(".arena-canvas")
    assert card.locator(".arena-canvas__title").inner_text() == "Onboarding" and card.get_by_role("button", name="Open on claude.ai").count() == 1
    kinds = pg.get_by_role("group", name="Kinds").get_by_role("button")
    assert kinds.last.text_content().strip() == "Canvases"
    kinds.last.click()                                                                                                         # the filter by kind: the canvases alone
    assert [s.get_attribute("aria-label") for s in pg.locator(".assets-sec").all()] == ["Canvases"]
    card.get_by_role("button", name="Seen").click()                                                                            # Seen folds it into Seen
    pg.locator('.assets-sec[data-kind="canvas"] .arena-frow[data-fold="seen"]').wait_for(timeout=WAIT_MS)
    assert _sent(pg, host, ("ideas.canvas_seen", {"key": CANVASES[0]["key"]}))


# -- §2.2: a part of System opens in the right column ---------------------------------------------------------------------------------------------------------------

def test_a_part_of_system_opens_in_the_right_column_and_a_use_there_opens_in_its_place(tech):
    pg, host = tech
    _seed(pg)
    pg.reload()
    pg.locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    _tech(pg)
    _rest(pg)
    wide = _box(pg, ".sys-scroll")["width"]
    _part(pg, "src/core").click()
    col = _column(pg)
    side = col.locator('.sys-side[data-path="src/core"]')
    side.locator('[data-sec="files"]').wait_for(timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.system_part") == [{"path": "src/core", "party": "tech", "since": SYS_OLD}]
    assert col.locator(".shell-ptab.is-on .shell-ptab__main").text_content().split()[:2] == ["Part", "core"] and _part(pg, "src/core").get_attribute("aria-pressed") == "true"
    _pushes(pg)
    assert _box(pg, ".sys-scroll")["width"] < wide - 400                                                                       # the table narrowed by the column
    side.locator('[data-sec="uses"] button').click()
    col.locator('.sys-side[data-path="src/core/db"]').wait_for(timeout=WAIT_MS)
    _part(pg, "src/core/db").wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    pg.locator(".shell-drawer").wait_for(state="detached", timeout=WAIT_MS)
    assert _part(pg, "src/core").get_attribute("aria-pressed") == "false"


# -- §2.3: the results, the gate and the limits moved -----------------------------------------------------------------------------------------------------------

def test_every_result_waits_showed_is_a_card_in_the_hand(party):
    pg, host = party
    looks = pg.locator(".arena-hc[data-kind=result]")
    looks.first.wait_for(timeout=WAIT_MS)
    labels = [b.get_attribute("aria-label") for b in looks.locator(".arena-hc__open").all()]
    assert sorted(labels) == ["To look at: Challenge store", "To look at: Words on the screens"]
    item = _stop(pg, "result")
    assert item.get_by_role("button", name="Merge into dev").count() == 1                                                       # Review's own answers on it
    item.get_by_role("button", name="Merge into dev").click()
    assert _sent(pg, host, ("ideas.merge", {"slug": "register", "task": "k1"})) or _sent(pg, host, ("ideas.merge", {"slug": "signin", "task": "c2"}))


def test_n_goals_ready_for_main_is_one_card_whose_answer_merges_and_a_quiet_line_under_the_projects_line(party):
    pg, host = party
    assert pg.locator(".arena-gatebox, .arena-gate__btn").count() == 0                                                           # the gate's box went
    item = _stop(pg, "gate")
    assert pg.locator(".arena-hc[data-kind=gate]").count() == 1                                                                 # one card for the batch
    assert item.locator(".arena-banner").inner_text() == "2 goals ready for main"
    assert "Passkey button on the page" in item.inner_text() and "Where the credentials are kept" in item.inner_text()
    line = pg.locator(".arena-left .arena-gateline")
    assert line.locator(".arena-gateline__main").inner_text() == "2 goals in dev wait for main" and "results go into" in line.inner_text()
    assert _box(pg, ".arena-left .arena-gateline")["y"] >= _box(pg, ".arena-left__proj")["y"] + _box(pg, ".arena-left__proj")["height"] - 1     # under the project's line
    item.get_by_role("button", name="Merge into main").click()
    assert _sent(pg, host, ("ideas.gate_merge", {}))
    pg.locator(".arena-hc[data-kind=gate]").wait_for(state="detached", timeout=WAIT_MS)                                          # nothing waits: no card
    pg.wait_for_function("() => document.querySelector('.arena-gateline__main')?.innerText === 'main is up to date'", timeout=WAIT_MS)
    line.locator(".arena-gateline__main").click()                                                                               # the line opens the gate's screen in the right column
    _column(pg).locator(".arena-gateview").wait_for(timeout=WAIT_MS)


def test_one_goal_ready_for_main_and_a_press_on_the_card_opens_the_gates_screen(gui):
    host = ArenaHost()
    host.gate_doc["ideas"] = host.gate_doc["ideas"][:1]
    pg, host, errors = _open(gui, host=host, ready=".arena-phead")
    item = _stop(pg, "gate")
    assert item.locator(".arena-banner").inner_text() == "1 goal ready for main"
    item.locator(".arena-hc__open").click()
    _column(pg).locator(".arena-gateview").wait_for(timeout=WAIT_MS)
    pg.close()
    assert not errors, "\n".join(errors)


def test_the_limits_are_chips_on_the_top_bars_right_and_a_press_opens_their_panel(party):
    pg, host = party
    assert pg.locator(".arena-stops .arena-limits, .arena-limits").count() == 0                                                   # not along the bottom any more
    chips = pg.locator(".shell-top .shell-top__chips")
    codex = chips.get_by_role("button", name="Codex 40 % left, week")
    assert codex.count() == 1 and chips.locator(".shell-top__chip").count() == 2 and chips.locator(".shell-top__spend").count() == 0
    assert _box(pg, ".shell-top__chips")["x"] > _box(pg, ".shell-top__settings")["x"]                                            # on the right, Settings is on the left
    codex.click()
    region = pg.get_by_role("region", name="What is left of your AI tools")
    region.wait_for(timeout=WAIT_MS)
    assert [x.get_attribute("data-provider") for x in region.locator(".arena-limit").all()] == ["claude", "codex"]
    assert region.locator(".arena-limit[data-provider=claude] .ork-crystals i.on, .arena-limit[data-provider=claude] .ork-crystals i.kept").count() == 6
    panel, chipbox = _box(pg, ".shell-top__limits"), _box(pg, ".shell-top__chips")
    assert panel["y"] >= chipbox["y"] + chipbox["height"]                                                                         # under the chips
    assert pg.locator(".shell-top__limits").get_by_role("button", name="Last week").count() == 1 and pg.locator(".shell-top__limits .shell-top__spend").count() == 1
    pg.keyboard.press("Escape")
    region.wait_for(state="detached", timeout=WAIT_MS)


# -- §4: the table starts at the pane's top, the tabs and the faces on its wood -----------------------------------------------------------------------------------

def test_the_party_tabs_and_the_members_faces_lie_on_the_table_from_the_panes_top(tech):
    pg, host = tech
    _seed(pg)
    pg.reload()
    pg.locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    _tech(pg)
    _rest(pg)
    play, top = _box(pg, ".arena-play"), _box(pg, ".arena-top")
    assert "ork-table" in pg.locator(".arena-play").get_attribute("class") and abs(play["y"] - (top["y"] + top["height"])) <= 1    # the wood begins under the party's line
    tabs = _box(pg, ".arena-play > .sys-tabs")
    assert abs(tabs["y"] - play["y"]) <= 4                                                                                      # the tabs at its edge
    wood = pg.evaluate("() => { const i = document.createElement('i'); i.style.background = 'var(--ork-table)'; document.body.append(i); const c = getComputedStyle(i).backgroundColor; i.remove(); return c; }")
    assert pg.locator(".arena-play").evaluate("e => getComputedStyle(e).backgroundColor") == wood
    assert pg.locator(".arena-play > .sys-tabs").evaluate("e => getComputedStyle(e).borderBottomStyle") == "none"
    pg.get_by_role("tab", name="Board").click()
    pg.locator(".arena-play > .arena-team").wait_for(timeout=WAIT_MS)                                                            # the members' faces on the wood, over their columns
    assert pg.locator(".arena-body.ork-table, .sys-scroll.ork-table").count() == 0                                               # one table, not a table on a table
