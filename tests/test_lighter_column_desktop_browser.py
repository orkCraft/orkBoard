"""Spec 73 part B on the desktop (docs/specs/73-a-lighter-column.md §0–§4, §6 B; decisions §88), in a real browser at 1 440 × 900 against the project test's stub host (Passkey with eight new goals and four
flags, one of them waiting for main; Ideation; Website; Release; the host's `project` block and `ideas.party_for`): a goal's row is one line (28 px: its element, its type's sign, its title, one state's sign; no pile, no
›; what its second line said is in its title); a press picks it, a second press opens its screen (Enter, Enter again); the open party's heading says *Taskmaster leads* and the column has no leader row, no *Goals n*;
*New · 8* with *Process now*, *Flags · 4* with *1 waits for main*, each one 28 px row; the 2 px rule under the open party; no + in the project line: New goal is the Orkmaster's row (spec 91 §8), its *More kinds…* deals the party picked's types first and New goal opens with it picked;
no New goal pile in the column; Ideation's rows and *Judge now*; a host from before spec 70. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_map_desktop_browser import node  # noqa: E402
from tests.test_project_desktop_browser import ProjectHost, _project  # noqa: E402
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _calls, _open, _parties, _show_goal  # noqa: E402

pytestmark = pytest.mark.browser

BUG = {"id": "fix", "name": "Fix a bug", "sign": "bug"}
FEATURE = {"id": "feature", "name": "A feature", "sign": "feature"}


class LighterHost(ProjectHost):
    """Passkey with eight new goals (two of the arena's and six more), four flags, one goal done that waits for main, a typed goal at work and a planned one that asks nothing."""

    def __init__(self, project=True):
        super().__init__(project=project)
        for i in range(1, 7):
            self.add(node(f"raw{i}", "passkey", f"A new goal of the person, number {i}", "raw", 3), "dust")
        self.add(node("waiting", "passkey", "Passkey on the lock screen", "done", 1, stage="done", progress={"done": 2, "total": 2}, folded=True), "ice")
        self.add(node("planned", "passkey", "Plan the audit log", "plan", 2), "void")
        self.node_of("register")["type"] = BUG
        self.node_of("recovery")["type"] = FEATURE


@pytest.fixture
def lighter(gui):
    pg, host, errors = _open(gui, host=LighterHost(), ready=".arena[data-goal=passkey]")
    _show_goal(pg, "passkey")
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _row(pg, slug):
    return pg.locator(f'.arena-goal[data-slug="{slug}"]')


def _main(pg, slug):
    return _row(pg, slug).locator(".arena-goal__main")


def _fold(pg, word):
    return pg.locator(f'.arena-pbody .arena-frow[data-fold="{word}"]')


def _preview(pg, title):
    pg.locator(".shell-preview").get_by_text(title).first.wait_for(timeout=WAIT_MS)


# -- a goal is one line ---------------------------------------------------------------------------------------------------------------------------------

def test_a_goal_is_one_line_of_28_px_with_its_element_its_type_its_title_and_its_state_and_nothing_else(lighter):
    pg, host = lighter
    col = pg.locator(".arena-left").bounding_box()
    row = _row(pg, "register")
    main = row.locator(".arena-goal__main")
    assert main.bounding_box()["height"] == 28 and row.bounding_box()["height"] == 28
    elem = row.locator(".ork-elem").bounding_box()
    assert elem["x"] - col["x"] == 12 and elem["width"] == 12 and elem["height"] == 12                                           # 12 px in from the column's edge, orkUI's element at 12 px
    kind = row.locator(".arena-goal__type")
    assert kind.locator(".ork-sign.bug").count() == 1 and kind.bounding_box()["width"] == 12                                      # its type's sign, in its goal's colour
    assert kind.evaluate("e => getComputedStyle(e).color") == row.locator(".ork-elem").evaluate("e => getComputedStyle(e).backgroundColor")
    title = row.locator(".arena-goal__title")
    assert title.inner_text() == "WebAuthn register" and title.evaluate("e => getComputedStyle(e).textOverflow + getComputedStyle(e).whiteSpace") == "ellipsisnowrap"
    mark = row.locator(".arena-goal__mark")
    assert mark.locator(".ork-sign.work").count() == 1 and mark.bounding_box()["width"] == 12
    assert row.inner_text().strip() == "WebAuthn register"                                                                      # no second line
    assert row.locator(".arena-goal__pile, .arena-goal__edge, .arena-goal__line, .arena-goal__open, .ork-chev").count() == 0      # no pile, no ›
    assert main.get_attribute("title").startswith("WebAuthn register · 0/6 in dev · implementation")                              # the old second line is in its title, after the whole title
    right = row.bounding_box()["x"] + row.bounding_box()["width"]
    assert right - (mark.bounding_box()["x"] + mark.bounding_box()["width"]) >= 8                                               # the state's sign at its right


def test_a_goal_with_no_type_keeps_the_space_and_a_planned_one_has_no_state_sign(lighter):
    pg, host = lighter
    plain, typed = _row(pg, "signin"), _row(pg, "register")
    none = plain.locator(".arena-goal__type")
    assert none.count() == 1 and none.locator(".ork-sign").count() == 0 and none.bounding_box()["width"] == 12                        # no sign, the space kept
    assert plain.locator(".arena-goal__title").bounding_box()["x"] == typed.locator(".arena-goal__title").bounding_box()["x"]        # the titles line up
    planned = _row(pg, "planned")
    assert planned.count() == 1 and planned.locator(".arena-goal__mark").bounding_box()["width"] == 12 and planned.locator(".arena-goal__mark .ork-sign").count() == 0       # only planned: nothing
    assert _row(pg, "recovery").locator(".arena-goal__mark .ork-sign.alert").count() == 1                                              # a goal that asks you: its sign
    assert _row(pg, "recovery").locator(".arena-goal__type .ork-sign.feature").count() == 1
    assert _row(pg, "signin").locator(".arena-goal__main").evaluate("e => e.scrollWidth <= e.clientWidth + 1")                      # a row never grows past the column


def test_a_press_picks_a_goal_a_second_press_opens_its_screen_and_enter_does_the_same(lighter):
    pg, host = lighter
    main = _main(pg, "register")
    assert main.get_attribute("aria-pressed") == "false"
    main.click()
    assert main.get_attribute("aria-pressed") == "true" and _row(pg, "register").get_attribute("class").count("is-on") == 1
    assert _row(pg, "signin").get_attribute("class").count("is-off") == 1                                                            # the others stand back
    assert pg.locator(".shell-preview").count() == 0 or not pg.locator(".shell-preview .board-ideaview").count()                     # picked, not opened
    main.click()                                                                                                                      # a second press opens its screen
    pg.locator(".shell-preview .board-ideaview").wait_for(timeout=WAIT_MS)
    _preview(pg, "WebAuthn register")
    pg.get_by_role("button", name="Close the right column").click()
    other = _main(pg, "signin")                                                                                                      # the keyboard: Enter picks, Enter again opens
    other.focus()
    pg.keyboard.press("Enter")
    assert other.get_attribute("aria-pressed") == "true"
    pg.keyboard.press("Enter")
    pg.locator(".shell-preview .board-ideaview").wait_for(timeout=WAIT_MS)
    _preview(pg, "Sign in with the passkey")


def test_hovering_a_row_peeks_as_before_and_show_all_takes_every_pick_out(lighter):
    pg, host = lighter
    _main(pg, "register").click()
    show = pg.get_by_role("button", name="Show all")
    assert show.count() == 1
    show.click()
    assert _main(pg, "register").get_attribute("aria-pressed") == "false" and pg.get_by_role("button", name="Show all").count() == 0


# -- the open party's heading is its leader ---------------------------------------------------------------------------------------------------------------

def test_the_open_heading_is_its_leader_taskmaster_leads_and_the_column_has_no_leader_row_and_no_goals_heading(lighter):
    pg, host = lighter
    head = pg.locator(".arena-phead[aria-current=true]")
    assert head.locator(".arena-phead__name").inner_text().strip() == "Passkey"
    leads = head.locator(".arena-phead__leads")
    assert leads.inner_text().strip() == "Taskmaster leads" and leads.evaluate("e => getComputedStyle(e).color") == pg.locator(".arena-cap").first.evaluate("e => getComputedStyle(e).color")
    ph = head.locator(".arena-plist__head").bounding_box()
    assert ph["width"] == 24 and ph["height"] == 22 and "peon" in head.locator(".ork-race__head").get_attribute("src")           # the leader's head, 24 × 22
    assert head.locator(".ork-sign.work").count() == 1                                                                                   # the work sign while it is at work
    k, n = head.locator(".arena-phead__count").inner_text().strip().split("/")                                                             # and k/n
    assert head.get_attribute("title") == f"Passkey · Taskmaster leads · {k} of {n} goals done"
    assert pg.locator(".arena-lead, .arena-left__head, .arena-left .arena-member").count() == 0                                           # no leader row, no heading of the goals
    assert pg.get_by_role("heading", name="Goals").count() == 0 and "Goals" not in pg.locator(".arena-pbody").inner_text()
    body = pg.locator(".arena-pbody").bounding_box()
    assert 0 <= body["y"] - (head.bounding_box()["y"] + head.bounding_box()["height"]) <= 1                                               # the groups come directly under it
    assert [t.strip().lower() for t in pg.locator(".arena-pbody .arena-sec").all_text_contents()] == ["at work", "planning"]
    assert pg.get_by_role("button", name="Process now", exact=False).count() == 1 and pg.locator(".arena-left .arena-frow .arena-power").count() == 1      # Process now is only the New row's


def test_a_closed_party_heading_is_unchanged_and_the_open_party_ends_in_a_2_px_rule_in_the_frames_colour(lighter):
    pg, host = lighter
    closed = _parties(pg).locator('.arena-phead[data-goal="website"]')
    assert closed.locator(".arena-phead__leads").count() == 0 and closed.locator(".arena-phead__who").count() == 0
    open_ = pg.locator(".arena-party.is-open").first
    rule = open_.evaluate("e => { const c = getComputedStyle(e); return [c.borderBottomWidth, c.borderBottomStyle, c.borderBottomColor]; }")
    frame = pg.locator(".arena-left").evaluate("e => getComputedStyle(e).borderRightColor")
    assert rule == ["2px", "solid", frame]
    shut = pg.locator(".arena-party:not(.is-open)").first.evaluate("e => getComputedStyle(e).borderBottomWidth")
    assert shut == "1px"


# -- New and Flags are rows -----------------------------------------------------------------------------------------------------------------------------

def test_new_is_a_folded_28_px_row_with_process_now_at_its_right_and_the_goals_unfold_below_it(lighter):
    pg, host = lighter
    row = _fold(pg, "new")
    assert row.bounding_box()["height"] == 28
    toggle = row.locator(".arena-frow__main")
    assert toggle.get_attribute("aria-label") == "New · 8" and toggle.get_attribute("aria-expanded") == "false" and toggle.locator(".ork-chev.right").count() == 1       # › while folded
    assert toggle.locator(".arena-frow__word").evaluate("e => getComputedStyle(e).textTransform") == "uppercase"                           # the pixel face's small caps, as the groups
    assert toggle.locator(".arena-frow__n").inner_text().strip() == "· 8"
    assert pg.locator(".arena-goal[data-slug^=raw]").count() == 0
    power = row.get_by_role("button", name="Process now")
    assert power.inner_text().strip() == "Process now" and power.is_enabled()                                                             # its words without the count
    assert power.bounding_box()["x"] > toggle.locator(".arena-frow__word").bounding_box()["x"] and power.bounding_box()["height"] == 22
    assert power.get_attribute("title").startswith("Taskmaster reads “")
    power.click()
    sent = _calls(pg, host, "ideas.queue")[-1]
    assert sent["queue"] == "now" and sent["via"] == "party" and sent["slug"]
    toggle.click()
    assert toggle.get_attribute("aria-expanded") == "true" and toggle.locator(".ork-chev").get_attribute("class") == "ork-chev"       # ⌄ when open
    rows = pg.locator(".arena-pbody .arena-goal")
    assert pg.locator(".arena-goal[data-slug^=raw]").count() == 6 and row.locator("xpath=following-sibling::*[1]").get_attribute("class").count("arena-goal") == 1
    first = pg.locator(".arena-goal[data-slug=raw1]")
    assert first.bounding_box()["height"] == 28 and first.bounding_box()["y"] > row.bounding_box()["y"]
    first.locator(".arena-goal__main").click()                                                                                          # a goal not yet read opens on a press
    pg.locator(".shell-preview .board-ideaview").wait_for(timeout=WAIT_MS)
    assert rows.count() > 6


def test_flags_is_a_folded_28_px_row_with_one_waits_for_main_at_its_right_and_the_flags_unfold_below_it(lighter):
    pg, host = lighter
    row = _fold(pg, "flags")
    assert row.bounding_box()["height"] == 28
    toggle = row.locator(".arena-frow__main")
    assert toggle.get_attribute("aria-label") == "Flags · 4" and toggle.get_attribute("aria-expanded") == "false"
    aside = row.locator(".arena-frow__aside")
    assert aside.inner_text().strip() == "1 waits for main" and aside.bounding_box()["x"] > toggle.locator(".arena-frow__word").bounding_box()["x"]
    assert aside.evaluate("e => getComputedStyle(e).color") == pg.locator(".arena-cap").first.evaluate("e => getComputedStyle(e).color")      # muted
    assert pg.locator(".arena-flagrow").count() == 0
    toggle.click()
    assert toggle.get_attribute("aria-expanded") == "true"
    assert pg.locator(".arena-flagrow").count() == 5                                                                                    # the one that waits for main, then the four flags
    assert pg.locator(".arena-flagrow").first.inner_text().strip().endswith("waits for main")


def test_new_and_flags_come_after_planning_in_that_order(lighter):
    pg, host = lighter
    ys = [pg.locator(".arena-pbody .arena-sec").nth(1).bounding_box()["y"], _fold(pg, "new").bounding_box()["y"], _fold(pg, "flags").bounding_box()["y"],
          _parties(pg).locator('.arena-phead[data-goal="ideas"]').bounding_box()["y"]]
    assert ys == sorted(ys) and len(set(ys)) == 4                                                                                      # Planning, New, Flags, then the closed parties


def test_a_party_with_nothing_new_still_has_the_new_row_with_process_now_disabled(gui):
    class Quiet(LighterHost):
        def __init__(self):
            super().__init__()
            self.nodes = [n for n in self.nodes if not n["slug"].startswith("raw") and n["slug"] not in ("magic", "log")]
    pg, host, errors = _open(gui, host=Quiet(), ready=".arena[data-goal=passkey]")
    _show_goal(pg, "passkey")
    row = _fold(pg, "new")
    assert row.locator(".arena-frow__main").get_attribute("aria-label") == "New · 0" and row.get_by_role("button", name="Process now").is_disabled()
    pg.close()
    assert not errors, "\n".join(errors)


# -- New goal at the Orkmaster ---------------------------------------------------------------------------------------------------------------------------

def test_no_plus_stands_in_the_project_line_new_goal_is_a_row_of_the_orkmasters_level(lighter):
    pg, host = lighter
    line = pg.locator(".arena-left__proj")
    assert line.get_by_role("button", name="New goal").count() == 0 and pg.locator(".arena-plus").count() == 0                                # spec 91 §8: one way in
    ork, proj = pg.get_by_role("button", name="The project").bounding_box(), line.locator(".shell-proj").bounding_box()
    assert ork["x"] + ork["width"] <= proj["x"]                                                                                               # the Orkmaster's head, then the project switcher
    _project(pg)
    assert pg.locator('.arena-prow[data-row="goal"]').get_by_role("button", name="Add goal", exact=True).count() == 1


def test_a_party_picked_in_the_new_goal_row_deals_its_types_first_and_new_goal_opens_with_that_party_picked(lighter):
    pg, host = lighter
    _project(pg)
    pg.locator(".arena-for__btn").click()
    pg.locator('.arena-for__opt[data-party="passkey"]').click()                                                                              # the party the person picked (Passkey shown before)
    pg.get_by_role("button", name="More kinds…").click()
    deal = pg.get_by_role("dialog", name="New goal for the project")
    deal.locator(".arena-type").first.wait_for(timeout=WAIT_MS)
    assert [c.get_attribute("data-type") for c in deal.locator(".arena-type").all()] == ["", "fix", "logo", "release"]                    # Your own goal, Passkey's own, then the others'
    deal.locator('.arena-type[data-type="logo"]').click()
    form = pg.get_by_role("dialog", name="New goal")
    form.locator('.arena-typed[data-type="logo"]').wait_for(timeout=WAIT_MS)
    its = form.get_by_role("group", name="Its party")
    its.locator(".arena-itsparty__chip").first.wait_for(timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.party_for")[-1] == {"type": "logo"}
    chips = its.locator(".arena-itsparty__chip")
    assert its.get_attribute("data-picked") == "passkey" and chips.locator("xpath=..").locator('[data-party="passkey"]').get_attribute("aria-checked") == "true"      # the party picked, not Website (the Orkmaster's)
    assert [c.get_attribute("data-party") for c in chips.all()] == ["website", "passkey", "release", "ideas"]                            # the others as chips, as on the level
    assert its.locator(".arena-itsparty__says").inner_text().strip() == "Orkmaster suggests Website · takes it whole"
    shot(pg, "desk-lighter-newgoal.png")
    form.get_by_label("The goal", exact=True).fill("A new mark")
    form.get_by_role("button", name="Add the goal").click()
    sent = _calls(pg, host, "ideas.add")[-1]
    assert sent["track"] == "passkey" and sent["type"] == "logo"
    form.wait_for(state="detached", timeout=WAIT_MS)


def test_another_party_picked_in_the_row_deals_its_types_first_and_your_own_goal_picks_it_too(lighter):
    pg, host = lighter
    _show_goal(pg, "website")
    _project(pg)
    pg.locator(".arena-for__btn").click()
    pg.locator('.arena-for__opt[data-party="website"]').click()
    assert pg.locator(".arena-for__btn").inner_text().strip() == "for Website"
    pg.get_by_role("button", name="More kinds…").click()
    deal = pg.get_by_role("dialog", name="New goal for the project")
    deal.locator(".arena-type").first.wait_for(timeout=WAIT_MS)
    assert [c.get_attribute("data-type") for c in deal.locator(".arena-type").all()] == ["", "logo", "fix", "release"]
    deal.locator('.arena-type[data-type=""]').click()
    form = pg.get_by_role("dialog", name="New goal")
    its = form.get_by_role("group", name="Its party")
    its.locator(".arena-itsparty__chip").first.wait_for(timeout=WAIT_MS)
    assert "type" not in _calls(pg, host, "ideas.party_for")[-1] and its.get_attribute("data-picked") == "website"
    form.get_by_label("Your goal").fill("Offline mode")
    form.get_by_role("button", name="Add the goal").click()
    sent = _calls(pg, host, "ideas.add")[-1]
    assert sent["track"] == "website" and sent["text"] == "Offline mode" and "type" not in sent


def test_more_kinds_on_the_projects_level_is_spec_70s_no_party_at_first_the_orkmaster_suggests_it_for_the_kind(lighter):
    pg, host = lighter
    _project(pg)
    pg.get_by_role("button", name="More kinds…").click()                                                                                     # no party picked by the person: none is passed on
    deal = pg.get_by_role("dialog", name="New goal for the project")
    deal.locator(".arena-type").first.wait_for(timeout=WAIT_MS)
    assert [c.get_attribute("data-type") for c in deal.locator(".arena-type").all()] == ["", "fix", "logo", "release"]
    deal.locator('.arena-type[data-type="logo"]').click()
    form = pg.get_by_role("dialog", name="New goal")
    form.locator(".arena-itsparty__chip").first.wait_for(timeout=WAIT_MS)
    assert form.get_by_role("group", name="Its party").get_attribute("data-picked") == "website"                                              # the Orkmaster's suggestion


def test_no_new_goal_pile_stands_in_the_column_any_more(lighter):
    pg, host = lighter
    assert pg.locator(".arena-left .arena-new, .arena-left .arena-new__pile").count() == 0
    assert pg.get_by_role("button", name="New goal: your own, or pick its type").count() == 0
    _show_goal(pg, "ideas")
    assert pg.locator(".arena-left .arena-new, .arena-left .arena-new__pile").count() == 0


def test_a_host_from_before_spec_70_has_the_plus_28_px_and_notched_and_new_goal_is_the_shown_partys_own(gui):
    pg, host, errors = _open(gui, host=LighterHost(project=False), ready=".arena[data-goal=passkey]")
    _show_goal(pg, "passkey")
    plus = pg.locator(".arena-left__proj").get_by_role("button", name="New goal")
    box = plus.bounding_box()
    assert plus.count() == 1 and box["width"] == 28 and box["height"] == 28 and plus.get_attribute("title") == "New goal: in Passkey, or another"      # no Orkmaster to hold the rows: the + stays
    assert box["x"] + box["width"] <= pg.locator(".arena-left__proj .shell-proj").bounding_box()["x"] and plus.evaluate("e => getComputedStyle(e, '::before').clipPath") != "none"
    pg.get_by_role("button", name="New goal").click()
    dlg = pg.get_by_role("dialog", name="New goal")
    dlg.wait_for(timeout=WAIT_MS)
    assert dlg.get_by_role("group", name="Its party").count() == 0 and dlg.get_by_label("Party").input_value() == "passkey"                    # no Orkmaster to suggest: the party's own
    pg.close()
    assert not errors, "\n".join(errors)


# -- Ideation ---------------------------------------------------------------------------------------------------------------------------------------------

def test_ideations_rows_are_one_line_too_with_judge_now_in_the_new_row(gui):
    class Lab(LighterHost):
        def __init__(self):
            super().__init__()
            self.add(node("pitch", "ideas", "Dark mode for the sign-in", "raw", 3), "dust")
    pg, host, errors = _open(gui, host=Lab(), ready=".arena[data-goal=passkey]")
    _show_goal(pg, "ideas")
    head = pg.locator(".arena-phead[aria-current=true]")
    assert head.locator(".arena-phead__leads").inner_text().strip() == "Investor leads" and pg.locator(".arena-lead").count() == 0
    for word in ("new", "sent"):                                                                                                       # the folds, opened
        _fold(pg, word).locator(".arena-frow__main").click()
    rows = pg.locator(".arena-pbody .arena-pitchrow")
    assert rows.count() >= 1 and all(b["height"] == 28 for b in [r.bounding_box() for r in rows.all()])
    row = rows.first
    assert row.locator(".arena-goal__pile, .arena-goal__line, .arena-goal__open, .ork-chev").count() == 0 and row.locator(".ork-elem").count() == 1
    assert " · " in row.locator("button").get_attribute("title")                                                                           # its line is in its title
    new = _fold(pg, "new")
    assert new.bounding_box()["height"] == 28 and new.locator(".arena-frow__main").get_attribute("aria-label") == "New · 1"
    judge = new.get_by_role("button", name="Judge now")
    assert judge.inner_text().strip() == "Judge now" and judge.is_enabled() and judge.get_attribute("title").startswith("Investor and the four views judge")
    assert pg.get_by_role("button", name="Process now").count() == 0
    assert _fold(pg, "sent").locator(".arena-frow__main").get_attribute("aria-expanded") == "true" and _fold(pg, "sent").bounding_box()["height"] == 28      # Sent is a row too
    pg.close()
    assert not errors, "\n".join(errors)


# -- looking at it ----------------------------------------------------------------------------------------------------------------------------------------

def test_a_screenshot_of_the_column_at_1440_by_900(lighter):
    pg, host = lighter
    assert pg.viewport_size == {"width": 1440, "height": 900}
    pg.mouse.move(900, 600)
    shot(pg, "desk-lighter.png")
    assert pg.locator(".arena-left").evaluate("e => e.scrollWidth <= e.clientWidth + 1")                                                    # no sideways scroll in the column
