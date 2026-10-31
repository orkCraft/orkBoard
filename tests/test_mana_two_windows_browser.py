"""The mana in two windows (docs/specs/114-the-mana-in-two-windows.md part B, decisions §192), in a real browser against a stub host, at the two widths of `tests/narrow.py`: each potion's liquid is the tool's shortest window and its
bottle's size the longest (large above 0.6, medium above 0.3, small above 0.1, else the vial; orkUI's `size-*`), every bottle standing on its floor in a slot of the large bottle's size, the colour by the lower of the two shares (a full
vial is danger), the now share in bold with the week's muted under it and the words of both; a tab's sword and shield framed when their side follows the default (the tool now) and bare when a tool is set, dim with the moon while that
tool is dry, the default potion's hover marking the framed marks too. The windows themselves (`hand/windows.js`) are read through the page's module. Screenshots to $D114_SHOTS when it is set (d114-*.png)."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand  # noqa: E402
from tests.test_hand_mana_browser import mana_of  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["D114_SHOTS"]) if os.environ.get("D114_SHOTS") else None
WINDOWS = "/static/js/hand/windows.js"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"d114-{name}.png"))


def local(delta: dt.timedelta, hour: int | None = None) -> str:
    at = dt.datetime.now() + delta
    return (at.replace(hour=hour, minute=0) if hour is not None else at).strftime("%Y-%m-%dT%H:%M")


SOON = local(dt.timedelta(days=0), None)                       # a reset today: said as *HH:MM*
WEEK = local(dt.timedelta(days=3), 9)                          # a reset in three days at 09:00: said as *Day 09:00*
WEEK_SAID = (dt.datetime.now() + dt.timedelta(days=3)).strftime("%a") + " 09:00"
SOON_SAID = SOON[-5:]


def limit(provider, name, *rows):
    """A tool's limit as the snapshot has it: each row `(window, left, reset)`; `left` the smallest."""
    return {"provider": provider, "name": name, "left": min(r[1] for r in rows), "rows": [{"window": w, "left": v, "reset": r} for w, v, r in rows]}


def two(provider, name, now, week, soon=SOON, later=WEEK):
    return limit(provider, name, ("5h", now, soon), ("week", week, later))


def windows(pg, l):
    return pg.evaluate("([m, l]) => import(m).then((x) => x.windowsOf(l, new Date()))", [WINDOWS, l])


def token(pg, name):
    """A colour token as the page resolves it (an `rgb(…)`)."""
    return pg.evaluate("(n) => { const e = document.createElement('i'); e.style.color = `var(${n})`; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }", name)


def open_mana(gui, limits, width="wide", mana=None, parties=None):
    host = HandHost()
    host.limits, host.mana = limits, mana or mana_of("claude", "claude")
    for slug, more in (parties or {}).items():
        next(p for p in host.parties if p["slug"] == slug).update(more)
    pg, host, log = open_hand(gui, host, width)
    pg.locator(".up-pot" if width == "phone" else ".hand-mana .hand-pot").first.wait_for(timeout=WAIT_MS)       # the phone's top row has bottles of its own (spec 117 B)
    pg.wait_for_timeout(300)
    return pg, host, log


def pot(pg, provider):
    return pg.locator(f'.hand-pot[data-provider="{provider}"]')


# -- the windows (spec 114 §3.1) ----------------------------------------------------------------------------------------------------------------

def test_the_shortest_window_is_the_liquid_and_the_longest_the_bottle_whatever_the_order_the_rows_come_in(gui):
    pg, host, log = open_mana(gui, [two("claude", "Claude Code", 0.3, 0.82)])
    try:
        for rows in ([("5h", 0.3, SOON), ("week", 0.82, WEEK)], [("week", 0.82, WEEK), ("5h", 0.3, SOON)]):
            got = windows(pg, limit("claude", "Claude Code", *rows))
            assert got["read"] and got["two"] and got["liquid"] == 0.3 and got["size"] == "large" and got["level"] == "ok"
            assert (got["now"]["window"], got["now"]["share"], got["week"]["window"], got["week"]["share"]) == ("5h", "30%", "week", "82%")
        codex = windows(pg, limit("codex", "Codex", ("weekly", 0.45, WEEK), ("5h", 1.0, SOON), ("daily", 0.9, SOON)))              # three windows: the shortest and the longest, the day between is neither
        assert codex["now"]["window"] == "5h" and codex["week"]["window"] == "weekly" and codex["liquid"] == 1 and codex["size"] == "medium"
        grouped = windows(pg, limit("agy", "Antigravity", ("Gemini · week", 0.5, WEEK), ("Gemini · 5h", 0.2, SOON)))             # a group in front of the name does not hide its length
        assert grouped["two"] and grouped["liquid"] == 0.2 and grouped["size"] == "medium"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_tool_with_one_window_keeps_the_large_bottle_and_its_level_and_one_not_read_has_none(gui):
    pg, host, log = open_mana(gui, [two("claude", "Claude Code", 0.3, 0.82)])
    try:
        one = windows(pg, limit("pi", "Pi", ("month", 0.55, WEEK)))
        assert not one["two"] and one["week"] is None and one["size"] == "large" and one["liquid"] == 0.55 and one["level"] == "ok" and one["now"]["window"] == "month"
        low = windows(pg, limit("agy", "Antigravity", ("daily", 0.04, "")))
        assert low["size"] == "large" and low["level"] == "danger"                                                                # one window: its own level, whatever its size
        same = windows(pg, limit("agy", "Antigravity", ("daily", 0.9, SOON), ("daily", 0.15, SOON)))
        assert not same["two"] and same["liquid"] == 0.15 and same["level"] == "warn"                                             # two windows of one length are one: the tightest
        bare = windows(pg, {"provider": "x", "name": "X", "left": 0.4, "rows": []})
        assert bare["read"] and not bare["two"] and bare["liquid"] == 0.4 and bare["size"] == "large"                             # a host that gives no rows: the tool's share
        none = windows(pg, {"provider": "codex", "name": "Codex", "left": None, "error": "Not logged in", "rows": []})
        assert none["read"] is False and none["level"] == "unread" and none["liquid"] == 0 and none["now"] is None and none["week"] is None and none["dry"] is False
        by_reset = windows(pg, limit("hermes", "Hermes", ("blue", 0.5, local(dt.timedelta(hours=2))), ("red", 0.5, local(dt.timedelta(days=5)))))
        assert by_reset["two"] and by_reset["now"]["window"] == "blue" and by_reset["week"]["window"] == "red"                    # a window the page does not know by name: told by how far its reset is
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_size_changes_at_sixty_thirty_and_ten_percent_of_the_week(gui):
    pg, host, log = open_mana(gui, [two("claude", "Claude Code", 0.3, 0.82)])
    try:
        sizes = pg.evaluate("([m, v]) => import(m).then((x) => v.map((w) => x.sizeOf(w)))", [WINDOWS, [1, 0.61, 0.6, 0.31, 0.3, 0.11, 0.1, 0.05, 0]])
        assert sizes == ["large", "large", "medium", "medium", "small", "small", "vial", "vial", "vial"]               # above, not at: 0.6 is a medium, 0.3 a small, 0.1 a vial
        by_week = [windows(pg, limit("claude", "C", ("5h", 1, SOON), ("week", w, WEEK)))["size"] for w in (0.61, 0.6, 0.31, 0.3, 0.11, 0.1)]
        assert by_week == ["large", "medium", "medium", "small", "small", "vial"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_colour_is_the_lower_of_the_two_shares_at_todays_levels(gui):
    pg, host, log = open_mana(gui, [two("claude", "Claude Code", 0.3, 0.82)])
    try:
        level = lambda now, week: windows(pg, limit("claude", "C", ("5h", now, SOON), ("week", week, WEEK)))["level"]      # noqa: E731
        assert level(0.3, 0.82) == "ok" and level(1, 0.9) == "ok"
        assert level(0.2, 0.9) == "warn" and level(0.9, 0.2) == "warn" and level(0.9, 0.15) == "warn"                   # the warning at 20 % or less, from either window
        assert level(1, 0.05) == "danger" and level(0.05, 1) == "danger" and level(0, 0.5) == "danger"                  # a full vial is danger: the week stops it first
        assert level(1, 0.06) == "warn" and level(1, 0.1) == "warn"                                                      # a vial between 5 and 10 % of the week: the warning, today's levels
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_window_at_zero_is_dry_and_says_when_the_last_of_them_is_back(gui):
    pg, host, log = open_mana(gui, [two("claude", "Claude Code", 0.3, 0.82)])
    try:
        dry = windows(pg, limit("claude", "C", ("5h", 0, SOON), ("week", 0.5, WEEK)))
        assert dry["dry"] and dry["back"] == SOON and dry["liquid"] == 0
        both = windows(pg, limit("claude", "C", ("5h", 0, SOON), ("week", 0, WEEK)))
        assert both["dry"] and both["back"] == WEEK                                                                      # out of both: back when the later one is
        assert not windows(pg, limit("claude", "C", ("5h", 0.01, SOON), ("week", 0.5, WEEK)))["dry"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the potions in the hand (spec 114 §3.1–§3.4) -------------------------------------------------------------------------------------------------

TOOLS = [two("claude", "Claude Code", 0.3, 0.82), two("codex", "Codex", 1.0, 0.45), two("cursor", "Cursor", 0.7, 0.18), two("agy", "Antigravity", 1.0, 0.04)]
SIZE_CELLS = {"large": (14, 18), "medium": (12, 14), "small": (10, 10), "vial": (8, 9)}                                 # orkUI's four bottles, in cells


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_each_potion_is_its_weeks_bottle_standing_on_its_floor_in_a_slot_of_the_large_ones_size(gui, width):
    pg, host, log = open_mana(gui, TOOLS[:3] if width == "wide" else TOOLS[:3], width)
    try:
        want = {"claude": "large", "codex": "medium", "cursor": "small"}
        cell = 2 if width == "narrow" else 3
        slots = {}
        for provider, size in want.items():
            b = pot(pg, provider)
            assert b.get_attribute("data-size") == size
            potion = b.locator(".ork-potion")
            classes = potion.get_attribute("class").split()
            assert (f"size-{size}" in classes) == (size != "large") and not any(c.startswith("size-") and c != f"size-{size}" for c in classes)      # the large has no size class
            slot, box = b.locator(".hand-pot__slot").bounding_box(), potion.bounding_box()
            assert (slot["width"], slot["height"]) == (14 * cell, 18 * cell)                                             # the slot is the large bottle's: 42 x 54, 28 x 36 small
            assert (box["width"], box["height"]) == (SIZE_CELLS[size][0] * cell, SIZE_CELLS[size][1] * cell)                # the bottle is drawn at its own size
            assert box["y"] + box["height"] == pytest.approx(slot["y"] + slot["height"], abs=0.5)                           # on its floor
            assert box["x"] + box["width"] / 2 == pytest.approx(slot["x"] + slot["width"] / 2, abs=0.5)                     # centred
            slots[provider] = slot
        assert len({s["y"] for s in slots.values()}) == 1 and len({s["height"] for s in slots.values()}) == 1             # the row does not move when the bottle changes
        assert len({b.locator(".hand-pot__share").bounding_box()["y"] for b in pg.locator(".hand-pot").all()}) == 1
        assert len({b.locator("img.ork-mark").bounding_box()["y"] for b in pg.locator(".hand-pot").all()}) == 1
        narrow.no_sideways(pg)
        shot(pg, f"{width}-sizes")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_liquid_is_the_now_share_whatever_the_bottle(gui):
    pg, host, log = open_mana(gui, TOOLS)
    try:
        style = lambda p: pot(pg, p).locator(".ork-potion").get_attribute("style").replace(" ", "")      # noqa: E731
        assert "--ork-potion-left:0.3" in style("claude") and "--ork-potion-left:1" in style("codex") and "--ork-potion-left:0.7" in style("cursor")
        assert pot(pg, "agy").get_attribute("data-size") == "vial" and "--ork-potion-left:1" in style("agy")            # a vial brim-full
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_full_vial_is_danger_and_the_week_that_is_low_warns_the_whole_potion(gui):
    pg, host, log = open_mana(gui, TOOLS)
    try:
        danger, alert = token(pg, "--ork-danger"), token(pg, "--ork-alert")
        vial = pot(pg, "agy")
        assert "is-danger" in vial.locator(".ork-potion").get_attribute("class").split() and vial.get_attribute("data-level") == "danger"
        assert vial.locator(".hand-pot__share").evaluate("e => getComputedStyle(e).color") == danger                    # the now share, brim-full, in the danger colour
        small = pot(pg, "cursor")
        assert "is-warn" in small.locator(".ork-potion").get_attribute("class").split() and small.locator(".hand-pot__share").evaluate("e => getComputedStyle(e).color") == alert       # 70 % now, 18 % of the week
        ok = pot(pg, "claude")
        assert ok.get_attribute("data-level") == "ok" and not {"is-warn", "is-danger"} & set(ok.locator(".ork-potion").get_attribute("class").split())      # 30 % now, 82 % of the week: no signal
        assert pot(pg, "codex").get_attribute("data-level") == "ok"
        shot(pg, "wide-states")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_two_shares_stand_under_the_potion_the_now_share_bold_and_the_weeks_muted(gui, width):
    pg, host, log = open_mana(gui, TOOLS[:3], width)
    try:
        b = pot(pg, "claude")
        share, week = b.locator(".hand-pot__share"), b.locator(".hand-pot__week")
        assert share.inner_text() == "30%" and share.evaluate("e => getComputedStyle(e).fontWeight") == "600"
        assert week.inner_text() == ("82%" if width == "narrow" else "week 82%")                                         # the phone's width keeps the share alone, the words are on the control
        assert week.evaluate("e => getComputedStyle(e).color") == token(pg, "--ork-ink-muted") and week.evaluate("e => getComputedStyle(e).fontWeight") != "600"
        assert share.bounding_box()["y"] < week.bounding_box()["y"]                                                      # the week's under the now share
        assert [x.locator(".hand-pot__share").inner_text() for x in pg.locator(".hand-pot").all()] == ["30%", "100%", "70%"]
        assert [x.locator(".hand-pot__week").inner_text().replace("week ", "") for x in pg.locator(".hand-pot").all()] == ["82%", "45%", "18%"]
        if width == "wide":
            assert pg.locator(".hand-mana").bounding_box()["x"] + pg.locator(".hand-mana").bounding_box()["width"] == pytest.approx(pg.viewport_size["width"], abs=1)
        narrow.no_sideways(pg)
        shot(pg, f"{width}-shares")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_potions_words_say_both_windows_and_when_each_comes_back(gui):
    pg, host, log = open_mana(gui, TOOLS[:2] + [two("hermes", "Hermes", 0.5, 0.5, soon="", later="")])
    try:
        said = lambda p: pot(pg, p).get_attribute("aria-label")                                                           # noqa: E731
        assert said("claude") == f"Claude Code: 30% of the 5 hours left, until {SOON_SAID}; 82% of the week, until {WEEK_SAID}, the default"
        assert said("codex") == f"Codex: 100% of the 5 hours left, until {SOON_SAID}; 45% of the week, until {WEEK_SAID}"
        assert said("hermes") == "Hermes: 50% of the 5 hours left; 50% of the week"                                       # no reset said: no *until*
        assert pot(pg, "claude").get_attribute("title") == said("claude")
        host.mana = mana_of("claude", "codex")                                                                             # the default moves: ', the default' with it
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-pot[data-provider=\"codex\"]').getAttribute('aria-label').endsWith(', the default')", timeout=WAIT_MS)
        assert not said("claude").endswith(", the default")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_tool_with_one_window_named_so_says_it_under_its_share_and_a_tool_not_read_stays_an_empty_potion(gui):
    one = limit("pi", "Pi", ("month", 0.55, ""))
    off = {"provider": "codex", "name": "Codex", "left": None, "error": "Not logged in", "rows": []}
    pg, host, log = open_mana(gui, [two("claude", "Claude Code", 0.3, 0.82), one, off])
    try:
        b = pot(pg, "pi")
        assert b.get_attribute("data-size") == "large" and b.locator(".hand-pot__share").inner_text() == "55%" and b.locator(".hand-pot__week").inner_text() == "of the month"
        assert b.get_attribute("aria-label") == "Pi: 55% of the month left"
        assert "--ork-potion-left:0.55" in b.locator(".ork-potion").get_attribute("style").replace(" ", "")
        gone = pot(pg, "codex")
        assert gone.locator(".hand-pot__share").inner_text() == "?" and gone.locator(".hand-pot__week").count() == 0 and gone.get_attribute("aria-label") == "Codex: limits not read yet"
        assert "--ork-potion-left:0" in gone.locator(".ork-potion").get_attribute("style").replace(" ", "") and gone.locator(".ork-potion").get_attribute("class").split() == ["ork-potion"]
        shot(pg, "wide-one-window")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_dry_potion_is_an_empty_bottle_of_the_weeks_size_in_the_danger_colour(gui):
    pg, host, log = open_mana(gui, [two("claude", "Claude Code", 0.3, 0.82), two("hermes", "Hermes", 0.0, 0.5, soon=SOON), two("agy", "Antigravity", 0.0, 0.0)])
    try:
        hermes = pot(pg, "hermes")
        assert hermes.get_attribute("data-size") == "medium" and "--ork-potion-left:0" in hermes.locator(".ork-potion").get_attribute("style").replace(" ", "")
        assert hermes.get_attribute("data-level") == "danger" and hermes.locator(".hand-pot__share").inner_text() == "0%"
        assert hermes.get_attribute("aria-label") == f"Hermes: 0% of the 5 hours left, until {SOON_SAID}; 50% of the week, until {WEEK_SAID}"
        assert pot(pg, "agy").get_attribute("data-size") == "vial"
        shot(pg, "wide-dry")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_that_spends_hatches_the_liquid_the_now_share_shows(gui):
    pg, host, log = open_mana(gui, [two("claude", "Claude Code", 0.5, 0.82), two("codex", "Codex", 1.0, 0.45)])
    try:
        pg.locator(".hand-pot").first.wait_for(timeout=WAIT_MS)
        assert pot(pg, "claude").locator(".hand-pot__took").count() == 0 and pot(pg, "claude").locator(".hand-pot__week").inner_text() == "week 82%"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_four_to_six_tools_keep_their_two_lines_in_two_small_rows(gui, width):
    limits = [*TOOLS, two("hermes", "Hermes", 0.5, 0.5), two("aider", "Aider", 0.4, 0.2)]
    pg, host, log = open_mana(gui, limits, width)
    try:
        p = pg.locator(".hand-mana .hand-pot")
        assert p.count() == 6 and all(b.locator(".hand-pot__slot").evaluate("e => e.classList.contains('is-small')") for b in p.all())
        assert [b.get_attribute("data-size") for b in p.all()] == ["large", "medium", "small", "vial", "medium", "small"]
        hand, mana = pg.locator(".hand").bounding_box(), pg.locator(".hand-mana").bounding_box()
        assert mana["y"] + mana["height"] <= hand["y"] + hand["height"] + 1 and hand["height"] <= 260                       # the hand holds both rows and grows by what they need
        narrow.no_sideways(pg)
        shot(pg, f"{width}-six")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_upright_on_a_phone_a_tool_is_a_bottle_by_its_week_its_now_share_in_the_colour_of_the_lower_share(gui):
    pg, host, log = open_mana(gui, [two("claude", "Claude Code", 0.3, 0.82), two("agy", "Antigravity", 1.0, 0.04)], "phone")
    try:
        tools = pg.locator(".up-pots .up-pot")
        tools.first.wait_for(timeout=WAIT_MS)
        assert [t.locator(".up-pot__share").inner_text() for t in tools.all()] == ["30%", "100%"] and tools.locator(".ork-potion.small").count() == 2      # a bottle each on the phone's top row (spec 117 B)
        assert [t.get_attribute("data-size") for t in tools.all()] == ["large", "vial"]                                    # the bottle is the week's: 82% large, 4% the vial
        assert [t.get_attribute("data-level") for t in tools.all()] == ["ok", "danger"]                                  # a full tool whose week is spent is red
        assert tools.nth(0).get_attribute("aria-label").startswith("Claude Code: 30% of the 5 hours left") and "82% of the week" in tools.nth(0).get_attribute("aria-label")
        shot(pg, "phone-tools")
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the tabs' marks (spec 114 §3.5) ----------------------------------------------------------------------------------------------------------

def side(tool, default, mixed=False):
    return {"tool": tool, "default": default, "mixed": mixed}


def marks(does, checks, lean=False, **more):
    return {"does_tool": does["tool"], "does_default": does["default"], "does_mixed": does["mixed"], "checks_tool": "" if lean else checks["tool"], "checks_default": False if lean else checks["default"],
            "checks_mixed": False if lean else checks["mixed"], "lean": lean, **more}


PARTY_MARKS = {"tech": marks(side("claude", True), side("claude", True)),                                  # both sides follow the default
               "design": marks(side("codex", False), side("claude", True)),                                # Does set to Codex, Checks follow
               "product": marks(side("claude", False), side("codex", False)),                              # both set; Claude is dry
               "release": marks(side("codex", False), side("", False), lean=True)}                         # Lean: no separate check
LIMITS = [two("claude", "Claude Code", 0.0, 0.5, soon=WEEK), two("codex", "Codex", 0.8, 0.9), two("cursor", "Cursor", 0.7, 0.7)]


def open_tabs(gui, limits=LIMITS, mana=None, width="wide"):
    pg, host, log = open_mana(gui, limits, width, mana or mana_of("claude", "codex", until=WEEK), PARTY_MARKS)
    pg.locator('.table-tab[data-tab="tech"] .table-tab__marks').wait_for(state="attached", timeout=WAIT_MS)
    return pg, host, log


def tab(pg, slug):
    return pg.locator(f'.table-tab[data-tab="{slug}"]')


def line(pg, slug):
    """A tab's second line in order as `[kind, tool]`: a tool's mark `framed` (in the default's frame), `dry` (dim, with the moon) or bare."""
    return pg.locator(f'.table-tab[data-tab="{slug}"] .table-tab__marks').evaluate("""e => [...e.querySelectorAll('[data-tool]')].map((m) => [m.closest('.table-tab__follow') ? 'framed' : m.closest('.table-tab__dry') ? 'dry' : 'bare', m.dataset.tool])""")


def test_a_side_that_follows_the_default_is_framed_with_the_tool_now_and_a_set_side_is_bare(gui):
    pg, host, log = open_tabs(gui)                                                                         # Claude is out: the work is on Codex
    try:
        assert line(pg, "tech") == [["framed", "codex"], ["framed", "codex"]]                              # both sides follow: the tool now
        assert line(pg, "design") == [["bare", "codex"], ["framed", "codex"]]                              # Does is Codex on purpose, Checks follow
        assert [m for m in line(pg, "release")] == [["bare", "codex"]]                                     # Lean: the shield is faint with no mark
        assert tab(pg, "tech").get_attribute("aria-label") == "Tech · Does on the default (now Codex) · Checks on the default (now Codex)"
        assert tab(pg, "design").get_attribute("aria-label") == "Design · Does on Codex, set for this party · Checks on the default (now Codex)"
        assert tab(pg, "release").get_attribute("aria-label") == "Release · Does on Codex, set for this party · no separate check" and tab(pg, "release").get_attribute("title") == tab(pg, "release").get_attribute("aria-label")
        frame = tab(pg, "tech").locator(".table-tab__follow").first
        got = frame.evaluate("e => { const s = getComputedStyle(e); return [s.borderTopWidth, s.borderTopStyle, s.borderTopColor, s.clipPath !== 'none']; }")
        assert got == ["1px", "solid", token(pg, "--ork-ink"), True]                                         # 1 px in the ink, orkUI's notch
        assert tab(pg, "design").locator(".table-tab__follow").count() == 1 and tab(pg, "product").locator(".table-tab__follow").count() == 0
        head, line_box = tab(pg, "tech").bounding_box(), tab(pg, "tech").locator(".table-tab__marks").bounding_box()
        assert head["height"] == pytest.approx(52, abs=1) and line_box["y"] + line_box["height"] <= head["y"] + head["height"]      # the frame takes no room: the tab keeps its height
        assert tab(pg, "tech").locator(".table-tab__follow").first.evaluate("e => e.closest('.table-tab__marks').getAttribute('aria-hidden')") == "true"
        shot(pg, "wide-tabs-marks")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_framed_mark_changes_when_the_default_moves_on_and_a_bare_one_stays(gui):
    pg, host, log = open_tabs(gui)
    try:
        host.limits = [two("claude", "Claude Code", 1.0, 0.5), *LIMITS[1:]]                               # Claude is back: the work goes on with it
        host.mana = mana_of("claude", "claude")
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.table-tab[data-tab=\"tech\"] .table-tab__follow [data-tool]').dataset.tool === 'claude'", timeout=WAIT_MS)
        assert line(pg, "tech") == [["framed", "claude"], ["framed", "claude"]]
        assert line(pg, "design") == [["bare", "codex"], ["framed", "claude"]]                             # its set side stays on Codex, its following side moved
        assert tab(pg, "tech").get_attribute("aria-label") == "Tech · Does on the default (now Claude Code) · Checks on the default (now Claude Code)"
        host.mana = {**mana_of("claude", "claude"), "now": None}                                           # every tool out: the Main tool stands in
        host.bump({})
        pg.wait_for_timeout(200)
        assert line(pg, "tech") == [["framed", "claude"], ["framed", "claude"]]
        host.mana = None                                                                                     # the host says nothing: the Main tool the map names
        host.bump({})
        pg.wait_for_timeout(200)
        assert line(pg, "tech") == [["framed", "claude"], ["framed", "claude"]]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_set_tool_that_is_dry_is_dim_with_the_moon_beside_it_and_the_words_say_when_it_is_back(gui):
    pg, host, log = open_tabs(gui)
    try:
        assert line(pg, "product") == [["dry", "claude"], ["bare", "codex"]]                               # Claude is dry: Does waits
        dim = tab(pg, "product").locator(".table-tab__dry")
        assert dim.count() == 1 and dim.locator(".ork-sign.moon").count() == 1 and dim.locator("[data-tool]").evaluate("e => getComputedStyle(e).opacity") == "0.35"
        assert dim.locator(".ork-sign.moon").bounding_box()["x"] > dim.locator("[data-tool]").bounding_box()["x"]      # the moon beside it
        assert tab(pg, "product").locator(".ork-sign.moon").count() == 1                                    # only the dry one has a moon
        assert tab(pg, "product").get_attribute("aria-label") == f"Product · Does waits for Claude Code until {WEEK_SAID} · Checks on Codex, set for this party"
        assert tab(pg, "tech").locator(".ork-sign.moon").count() == 0 and tab(pg, "design").locator(".ork-sign.moon").count() == 0       # a following side never waits: it has moved on
        host.limits = [two("claude", "Claude Code", 0.6, 0.5), *LIMITS[1:]]                                # Claude has its 5 hours back
        host.bump({})
        pg.wait_for_function("() => document.querySelectorAll('.table-tab[data-tab=\"product\"] .ork-sign.moon').length === 0", timeout=WAIT_MS)
        assert line(pg, "product") == [["bare", "claude"], ["bare", "codex"]]
        assert tab(pg, "product").get_attribute("aria-label") == "Product · Does on Claude Code, set for this party · Checks on Codex, set for this party"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_host_that_does_not_say_whether_a_side_follows_draws_bare_marks_in_the_words_of_before(gui):
    old = {"does_tool": "claude", "checks_tool": "codex", "does_mixed": False, "checks_mixed": False, "lean": False}
    pg, host, log = open_mana(gui, LIMITS, "wide", mana_of("claude", "codex"), {"tech": old})
    try:
        pg.locator('.table-tab[data-tab="tech"] .table-tab__marks').wait_for(state="attached", timeout=WAIT_MS)
        assert line(pg, "tech") == [["bare", "claude"], ["bare", "codex"]] and tab(pg, "tech").get_attribute("aria-label") == "Tech · Does on Claude Code · Checks on Codex"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def outlined(pg):
    return sorted(pg.locator(".table-tab .is-marked").evaluate_all("els => els.map((e) => [e.closest('.table-tab').dataset.tab, e.dataset.tool, !!e.closest('.table-tab__follow')])"))


def test_the_default_potion_hovered_marks_the_framed_marks_as_well_as_its_tools_own(gui):
    pg, host, log = open_mana(gui, LIMITS, "wide", mana_of("claude", "codex", until=WEEK), {**PARTY_MARKS, "product": {**PARTY_MARKS["product"], "tool": "claude"}})
    try:
        pg.locator('.table-tab[data-tab="tech"] .table-tab__marks').wait_for(state="attached", timeout=WAIT_MS)
        assert outlined(pg) == []
        pot(pg, "codex").hover()                                                                            # the project's tab: the default potion is the tool now, Codex
        pg.wait_for_function("() => document.querySelectorAll('.table-tab .is-marked').length > 0", timeout=WAIT_MS)
        assert outlined(pg) == sorted([["tech", "codex", True], ["tech", "codex", True], ["design", "codex", False], ["design", "codex", True], ["product", "codex", False], ["release", "codex", False]])
        assert tab(pg, "tech").locator(".table-tab__follow").first.evaluate("e => getComputedStyle(e).boxShadow") != "none"       # a framed mark that is marked has its ring
        pg.mouse.move(5, 300)
        pg.wait_for_function("() => document.querySelectorAll('.table-tab .is-marked').length === 0", timeout=WAIT_MS)
        tab(pg, "product").click()                                                                          # a party set to Claude: its tab frames Claude's potion, the default is still Codex's
        pg.wait_for_timeout(500)
        assert pg.locator('.hand-pot[data-default="1"]').get_attribute("data-provider") == "claude"
        pot(pg, "claude").hover()                                                                           # the framed potion: its own tool's marks, and the framed marks (the tool now)
        pg.wait_for_function("() => document.querySelectorAll('.table-tab .is-marked').length > 0", timeout=WAIT_MS)
        got = outlined(pg)
        assert ["product", "claude", False] in got and ["tech", "codex", True] in got and ["design", "codex", True] in got       # the framed marks are marked, though they show Codex
        assert ["design", "codex", False] not in got and ["release", "codex", False] not in got                                 # a bare Codex mark is not: it is not the default's
        pg.mouse.move(5, 300)
        pg.wait_for_function("() => document.querySelectorAll('.table-tab .is-marked').length === 0", timeout=WAIT_MS)
        pot(pg, "cursor").focus()                                                                           # a potion that is not the default's marks its own tool's marks only
        pg.wait_for_timeout(300)
        assert outlined(pg) == []                                                                           # nobody drinks from Cursor here
        pot(pg, "codex").focus()
        pg.wait_for_function("() => document.querySelectorAll('.table-tab .is-marked').length > 0", timeout=WAIT_MS)
        assert ["design", "codex", False] in outlined(pg) and ["tech", "codex", True] in outlined(pg)       # Codex's own marks, bare or framed
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_narrow_width_has_heads_only_and_says_the_words_on_the_tab(gui):
    pg, host, log = open_tabs(gui, width="narrow")
    try:
        assert tab(pg, "tech").locator(".table-tab__marks").is_hidden()                                     # a row of heads: no second line
        assert tab(pg, "product").get_attribute("title") == f"Product · Does waits for Claude Code until {WEEK_SAID} · Checks on Codex, set for this party"
        assert tab(pg, "tech").get_attribute("title") == "Tech · Does on the default (now Codex) · Checks on the default (now Codex)"
        shot(pg, "narrow-tabs")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_full_week_is_a_large_full_bottle_and_a_low_five_hours_a_large_bottle_nearly_empty_in_the_danger_colour(gui):
    pg, host, log = open_mana(gui, [two("claude", "Claude Code", 1.0, 1.0), two("codex", "Codex", 0.04, 0.9)])
    try:
        full, low = pot(pg, "claude"), pot(pg, "codex")
        assert full.get_attribute("data-size") == "large" and full.get_attribute("data-level") == "ok" and "--ork-potion-left:1" in full.locator(".ork-potion").get_attribute("style").replace(" ", "")
        assert low.get_attribute("data-size") == "large" and low.get_attribute("data-level") == "danger"                  # the week is plentiful, the 5 hours are not: a large bottle, one row of red
        assert low.locator(".hand-pot__share").inner_text() == "4%" and low.locator(".hand-pot__week").inner_text() == "week 90%"
        shot(pg, "wide-full-and-five-hours-low")
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the room the second line takes (the hand's height at the wide width, its width at the narrow one) ----------------------------------------------

MORE = [two("hermes", "Hermes", 0.5, 0.5), two("aider", "Aider", 0.4, 0.2)]
PAID = {"tool": "agy", "name": "Antigravity", "until": "2026-10-29T18:00", "usd_task": 0.4}


@pytest.mark.parametrize("tools,paid", [(4, False), (6, False), (6, True)], ids=["four", "six", "six-and-paid"])
def test_at_1280_by_800_two_rows_of_potions_leave_the_portal_ring_and_its_label_clear_of_the_panes_head(gui, tools, paid):
    pg, host, log = open_mana(gui, (TOOLS + MORE)[:tools], "wide", mana_of("claude", "claude", paid=PAID if paid else None))
    try:
        pg.locator(".portal__label").wait_for(timeout=WAIT_MS)
        label, ask, ring = pg.locator(".portal__label").bounding_box(), pg.locator(".table-ask").bounding_box(), pg.locator(".ork-portal-ring").bounding_box()
        assert label["y"] >= ask["y"] + ask["height"] and ring["y"] >= label["y"] + label["height"]                # the label and the ring lie under the line that asks the Orkmaster, never over the pane's head
        hand = pg.locator(".hand").bounding_box()
        assert hand["height"] <= (190 if paid else 170)                                                          # the week's share lies beside the now share: two rows are no taller than with one share
        assert pg.locator(".hand-pot__shares").first.evaluate("e => getComputedStyle(e).flexDirection") == "row"
        narrow.no_sideways(pg)
        shot(pg, f"fix-wide-two-rows-{tools}{'-paid' if paid else ''}")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("tools", [3, 4, 6])
def test_at_390_the_potions_and_both_their_lines_lie_inside_the_window_and_the_hand_grows_for_them(gui, tools):
    pg, host, log = open_mana(gui, (TOOLS + MORE)[:tools], "narrow")
    try:
        height = pg.viewport_size["height"]
        for sel in (".hand-pot__share", ".hand-pot__week", ".hand-pot", ".hand-mana", ".hand"):
            for b in pg.locator(sel).all():
                box = b.bounding_box()
                assert box["y"] + box["height"] <= height + 0.5 and box["x"] + box["width"] <= pg.viewport_size["width"] + 0.5, (sel, box)       # nothing cut off at the window's foot or edge
        weeks = pg.locator(".hand-pot__week").all()
        assert weeks and all(w.is_visible() for w in weeks)
        mana, hand = pg.locator(".hand-mana").bounding_box(), pg.locator(".hand").bounding_box()
        assert mana["y"] >= hand["y"]                                                                              # the hand holds them
        narrow.no_sideways(pg)
        shot(pg, f"fix-narrow-{tools}")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_at_390_three_tools_take_no_more_width_than_before_so_the_die_overlaps_the_cards_no_more(gui):
    pg, host, log = open_mana(gui, TOOLS[:3], "narrow")
    try:
        pots = pg.locator(".hand-pot").all()
        widths = [b.bounding_box()["width"] for b in pots]
        assert all(w <= 44 for w in widths), widths                                                                # a potion is as wide as its share, the slot of the large bottle (28 px at the small size) inside it
        mana, die = pg.locator(".hand-mana").bounding_box(), pg.locator(".hand-die").bounding_box()
        assert mana["width"] <= 120, mana                                                                         # as wide as three potions were before the second line (spec 112 B: the die stands where it stood)
        assert die["x"] + die["width"] <= mana["x"] + 1 and die["x"] >= 200, die                                  # the die ends where the potions begin, as far right as on main
        assert pots[0].locator(".hand-pot__slot").bounding_box()["width"] == 28
        shot(pg, "fix-narrow-die")
    finally:
        pg.close()
    assert not log, "\n".join(log)
