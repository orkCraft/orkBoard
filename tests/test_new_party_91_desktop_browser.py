"""Spec 91 part E on the desktop (docs/specs/91-the-owners-list.md §7, decisions §107.5): Chromium at 1 440 × 900 against the proposals test's stub host with `ideas.party_presets` (the real
presets of a mobile app, from realm/party_presets.py) and `ideas.tools` with `makes`. New party is one dialog in two halves: presets on the left (*By stage of the project*, *By craft*, *Your own
party*), the name, the size and the team by seats on the right (*Leads*, *Does*, *Checks*). A preset pressed fills the bands; a size changes the seats and their tiers at once; a seat is taken out and
another put in from the band's short list (Esc closes the list, not the dialog); a seat's AI tool is picked from groups that say what the role needs and why a tool cannot; Save party sends `tools`.
Edit the party is the same dialog on the party. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_proposals_desktop_browser import TOOLS, ProposalHost, _about, _party  # noqa: E402
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _calls, _new_party, _open, _show_goal  # noqa: E402

pytestmark = pytest.mark.browser

# the stub's tools, as ideas.tools gives them now: Antigravity installed and ready, and the only one that makes pictures
MAKING = copy.deepcopy(TOOLS)
for row in MAKING["tools"]:
    row["makes"] = ["pictures"] if row["id"] == "agy" else []
    if row["id"] == "agy":
        row.update(ready=True, installed=True, signed_in=True)
MAKING["tools"].sort(key=lambda r: 0 if r["ready"] else 1)


class PresetHost(ProposalHost):
    """The proposals host (its `ideas.party_presets` answers the real rows for its kind) with the tools that say what they make."""

    def __init__(self, kind_id="mobile"):
        super().__init__(kind_id=kind_id)
        self.tools_doc = copy.deepcopy(MAKING)
        self.hold = False                                                  # a save is only recorded, and refused (the stub makes no slug of a party with no words)

    def handle(self, name, a):
        if name == "ideas.goal_save" and self.hold:
            self.log.append((name, a))
            return {"error": "held by the test"}
        return super().handle(name, a)


@pytest.fixture
def desk(gui):
    pg, host, errors = _open(gui, host=PresetHost(), ready=".arena[data-goal=passkey]")
    pg.set_default_timeout(WAIT_MS)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _dialog(pg, name="New party"):
    dlg = pg.get_by_role("dialog", name=name)
    dlg.locator(".shell-preset").first.wait_for(timeout=WAIT_MS)
    dlg.locator(".shell-seat[data-seat]").first.wait_for(timeout=WAIT_MS)                                                   # the seats are filled: a preset is pressed
    return dlg


def _words(el):
    return " ".join(el.inner_text().split())


def _seats(dlg, band):
    """The roles in a band, in order."""
    return [s.get_attribute("data-seat") for s in dlg.locator(f'.shell-band[data-band="{band}"] .shell-seat[data-seat]').all()]


def _tier(dlg, role):
    """The tier a seat's head wears: its image says it."""
    return dlg.locator(f'.shell-seat[data-seat="{role}"] .ork-race__head').get_attribute("src").rsplit("-", 1)[1].split(".")[0].split("@")[0]


def _size(dlg, word):
    dlg.get_by_role("radiogroup", name="Size").get_by_role("radio", name=word).click()


def _press(dlg, craft):
    dlg.locator(f'.shell-preset[data-craft="{craft}"]').click()


# -- two halves --------------------------------------------------------------------------------------------------------------------------------------------------

def test_new_party_is_presets_on_the_left_and_the_team_by_seats_on_the_right(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    assert _calls(pg, host, "ideas.party_presets")[-1] == {}
    left = dlg.get_by_role("navigation", name="Presets")
    assert [h.text_content() for h in left.locator("h3").all()] == ["By stage of the project", "By craft", "Your own party"]
    assert _words(left.locator(".shell-presets__kind")) == "For a mobile app: the Orkmaster knows what this project is"
    stages = left.get_by_role("region", name="By stage of the project").locator(".shell-preset")
    assert [(c.get_attribute("data-craft"), c.locator("b").text_content()) for c in stages.all()] == [
        ("ideation", "Ideation"), ("mobile-concept", "Concept"), ("mobile-build", "Build"), ("release", "Release"), ("mobile-liveops", "LiveOps")]
    assert all(c.locator("small").first.inner_text() for c in stages.all())                                                       # a line each
    crafts = left.get_by_role("region", name="By craft").locator(".shell-preset")
    assert [c.locator("b").text_content() for c in crafts.all()] == ["Tech", "Design", "Data", "Marketing", "Product", "Art and sound"]
    own = left.get_by_role("region", name="Your own party").locator(".shell-preset")
    assert own.locator("b").text_content() == "Your own party" and own.locator("small").inner_text() == "Start from the Taskmaster and add who you need"
    pressed = [c.get_attribute("data-craft") for c in dlg.locator(".shell-preset[aria-pressed=true]").all()]
    assert pressed == ["mobile-build"]                                                                                      # the project's Build is where it opens
    for label in ("Name", "What it is for"):
        assert dlg.get_by_label(label, exact=True).count() == 1
    assert dlg.get_by_label("Name", exact=True).input_value() == "" and dlg.get_by_label("Name", exact=True).get_attribute("placeholder") == "Build"       # the pressed preset's name is the placeholder: the Taskmaster names a party that has only what it is for
    size = dlg.get_by_role("radiogroup", name="Size")
    assert [r.inner_text() for r in size.get_by_role("radio").all()] == ["Lean", "Standard", "Full"]
    assert size.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"
    assert _words(dlg.locator(".shell-sizebar__says")).startswith("2 agents: the leader Veteran, the rest Seasoned")
    assert [dlg.get_by_role("region", name=b).locator("h3").text_content() for b in ("Leads", "Does", "Checks")] == ["Leads", "Does", "Checks"]
    assert [dlg.locator(f'[data-seats="{b}"]').inner_text() for b in ("lead", "build", "check")] == ["1 of 1 seats", "1 of 1 seats", "0 of 1 seats"]
    assert (_seats(dlg, "lead"), _seats(dlg, "build"), _seats(dlg, "check")) == (["product-manager"], ["grunt"], [])
    assert dlg.locator('[data-free="check"]').inner_text().strip().endswith("Add a checker")
    assert _words(dlg.locator('.shell-seat[data-seat="grunt"]')).startswith("Grunt Seasoned ork · Writes the code a task asks for, with its tests")
    assert dlg.locator('[data-foot="agents"]').inner_text() == "2 agents · a task goes to the one who does its kind of work, the Grunt fills in"
    assert dlg.get_by_role("button", name="Save party").is_disabled() is False and dlg.get_by_role("button", name="Cancel").count() == 1
    pg.wait_for_timeout(300)
    shot(pg, "desk-new-party-91.png")


def test_a_stage_preset_fills_the_bands_and_a_press_on_another_replaces_them(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    _press(dlg, "mobile-concept")
    assert dlg.locator(".shell-preset[aria-pressed=true]").get_attribute("data-craft") == "mobile-concept"
    assert (_seats(dlg, "lead"), _seats(dlg, "build"), _seats(dlg, "check")) == (["product-designer"], ["ui-kit"], [])        # Standard: the leader and the first builder
    assert dlg.get_by_label("Name", exact=True).get_attribute("placeholder") == "Concept"
    _press(dlg, "mobile-liveops")
    assert (_seats(dlg, "lead"), _seats(dlg, "build")) == (["analyst"], ["data-engineer"]) and dlg.get_by_label("Name", exact=True).get_attribute("placeholder") == "LiveOps"
    dlg.get_by_label("Name", exact=True).fill("Our numbers")
    _press(dlg, "design")
    assert _seats(dlg, "lead") == ["product-designer"] and dlg.get_by_label("Name", exact=True).input_value() == "Our numbers"      # a name the person typed stays
    _press(dlg, "mixed")
    assert (_seats(dlg, "lead"), _seats(dlg, "build"), _seats(dlg, "check")) == (["taskmaster"], [], [])
    assert dlg.locator('[data-free="lead"]').count() == 1 and dlg.locator('[data-free="build"]').count() == 1
    assert dlg.locator('[data-foot="agents"]').inner_text().startswith("1 agent ·")


def test_a_size_changes_the_seats_and_their_tiers_at_once(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    _press(dlg, "mobile-build")
    _size(dlg, "Full")
    assert (_seats(dlg, "build"), _seats(dlg, "check")) == (["grunt"], ["reviewer"])
    assert (_tier(dlg, "product-manager"), _tier(dlg, "grunt"), _tier(dlg, "reviewer")) == ("elder", "warrior", "elder")        # the leader and the checker Veteran, the builder Seasoned
    assert _words(dlg.locator(".shell-sizebar__says")).startswith("3 agents, Seasoned and up")
    assert dlg.locator('[data-foot="agents"]').inner_text().startswith("3 agents ·")
    _size(dlg, "Lean")
    assert (_seats(dlg, "lead"), _seats(dlg, "build"), _seats(dlg, "check")) == (["product-manager"], [], [])
    assert _tier(dlg, "product-manager") == "warrior" and _words(dlg.locator(".shell-sizebar__says")).startswith("One agent, Seasoned")
    assert dlg.get_by_role("radio", name="Lean").get_attribute("aria-checked") == "true" and dlg.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "false"
    _size(dlg, "Standard")
    assert (_seats(dlg, "build"), _seats(dlg, "check")) == (["grunt"], []) and _tier(dlg, "product-manager") == "elder" and _tier(dlg, "grunt") == "warrior"
    assert _calls(pg, host, "ideas.party_price", at_least=2)[-1]["size"] in ("lean", "standard", "full")
    dlg.get_by_role("radio", name="Standard").focus()                                                                       # the arrows move the pick
    pg.keyboard.press("ArrowRight")
    assert dlg.get_by_role("radio", name="Full").get_attribute("aria-checked") == "true" and (_seats(dlg, "build"), _seats(dlg, "check")) == (["grunt"], ["reviewer"])


def test_a_seat_is_taken_out_and_another_put_in_from_the_bands_short_list(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.get_by_role("button", name="Remove Grunt from the party").click()
    assert _seats(dlg, "build") == [] and dlg.locator('[data-free="build"]').inner_text().strip().endswith("Add a member")
    assert dlg.get_by_label("Name", exact=True).get_attribute("placeholder") == "Its name, in a few words" and dlg.locator(".shell-preset[aria-pressed=true]").count() == 0     # a seat changed by hand: no preset is pressed
    dlg.locator('[data-free="build"]').click()
    pop = dlg.get_by_role("group", name="Add a member")
    rows = pop.locator(".shell-team-row")
    assert 1 <= rows.count() <= 6 and pop.get_by_role("button", name="More roles").count() == 1                              # a short list, the rest behind More roles
    assert [r.get_attribute("data-agent") for r in rows.all()][:3] == ["grunt", "ui-kit", "artist"]                         # the recipe's builders, the most needed first (Grunt, taken out, is offered again)
    assert pop.locator('[data-agent="grunt"]').count() == 1 and pop.locator('[data-agent="product-manager"]').count() == 0     # only the band's roles
    assert pop.locator('[data-agent="artist"] .shell-seat__needs').inner_text() == "needs pictures"
    pg.keyboard.press("Escape")
    pop.wait_for(state="detached", timeout=WAIT_MS)
    assert pg.get_by_role("dialog", name="New party").count() == 1                                                          # Esc closed the list, not the dialog
    assert dlg.locator('[data-free="build"]').evaluate("e => document.activeElement === e")                                 # the focus is back where it was
    dlg.locator('[data-free="build"]').click()
    dlg.get_by_role("group", name="Add a member").locator('[data-agent="artist"]').click()
    assert _seats(dlg, "build") == ["artist"] and dlg.locator('[data-free="build"]').count() == 0
    assert dlg.locator('.shell-seat[data-seat="artist"] .shell-seat__needs').inner_text() == "needs pictures"
    dlg.locator('[data-free="check"]').click()
    pop = dlg.get_by_role("group", name="Add a checker")
    assert pop.locator('[data-agent="grunt"]').count() == 0 and pop.locator('[data-agent="accessibility-reviewer"]').count() == 1
    pop.locator('[data-agent="accessibility-reviewer"]').click()
    assert _seats(dlg, "check") == ["accessibility-reviewer"] and dlg.locator('[data-foot="agents"]').inner_text().startswith("3 agents ·")
    _size(dlg, "Lean")
    _size(dlg, "Full")
    assert (_seats(dlg, "build"), _seats(dlg, "check")) == (["artist"], ["accessibility-reviewer"])                          # the seats the person chose come back with the size
    dlg.get_by_role("button", name="Remove Product manager from the party").click()
    assert _seats(dlg, "lead") == ["taskmaster"]                                                                            # the Taskmaster leads again


# -- a seat's AI tool ----------------------------------------------------------------------------------------------------------------------------------------

def test_the_artists_tool_is_antigravity_the_picker_groups_and_the_reasons_and_the_payload_carries_tools(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.get_by_role("button", name="Remove Grunt from the party").click()
    dlg.locator('[data-free="build"]').click()
    dlg.get_by_role("group", name="Add a member").locator('[data-agent="artist"]').click()
    btn = dlg.locator('[data-seat-tool="artist"]')
    assert _words(btn) == "Party's tool · Claude Code" and btn.get_attribute("aria-label") == "Its AI tool for Artist: Party's tool · Claude Code"
    btn.click()
    pop = dlg.get_by_role("group", name="Its AI tool for Artist")
    rows = pop.locator("button.shell-pop__row")
    assert _words(rows.first) == "The party's tool (Claude Code)" and rows.first.get_attribute("aria-pressed") == "true"
    can = pop.locator('[data-group="can"]')
    assert can.locator("h4").text_content() == "Can do what Artist needs"
    assert [r.get_attribute("data-tool") for r in can.locator(".shell-pop__row").all()] == ["agy"]                          # the ready tool that makes pictures
    assert "Pictures, code and text" in _words(can.locator(".shell-pop__row")) and can.locator("[data-experimental]").inner_text() == "experimental"
    cannot = pop.locator('[data-group="cannot"]')
    assert cannot.locator("h4").text_content() == "Cannot make pictures"
    got = {r.get_attribute("data-tool"): _words(r) for r in cannot.locator(".shell-pop__row").all()}
    assert set(got) == {"claude", "codex", "pi", "cursor", "hermes"} and "draws no pictures" in got["claude"] and "draws no pictures" in got["cursor"]
    assert "its Seasoned model" in got["claude"] and "runs its own model" in got["pi"]
    assert _words(pop.locator(".shell-pop__foot")) == "The tier comes from the party's size. Each tool runs its own model for it."
    pg.wait_for_timeout(300)
    shot(pg, "desk-seat-tool-91.png")
    assert pop.locator('.shell-pop__row[data-tool="hermes"]').is_disabled() is True                                         # not installed: shown, not taken
    can.locator('[data-tool="agy"]').click()
    assert dlg.get_by_role("group", name="Its AI tool for Artist").count() == 0 and _words(btn) == "Antigravity"
    dlg.get_by_label("What it is for").fill("Pictures for the store.")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["leader"] == "product-manager" and sent["team"] == ["artist"] and sent["size"] == "standard" and sent["tools"] == {"artist": "agy"}
    assert "tool" not in sent                                                                                               # the party's own tool is the Main tool


def test_a_tool_that_cannot_do_the_need_may_still_be_picked_and_a_role_that_needs_sound_has_none_that_can(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    _press(dlg, "mobile-concept")
    dlg.get_by_role("button", name="Remove UI-kit from the party").click() if dlg.get_by_role("button", name="Remove UI-kit from the party").count() else dlg.locator('[data-act="remove"]').nth(1).click()
    dlg.locator('[data-free="build"]').click()
    dlg.get_by_role("group", name="Add a member").get_by_role("button", name="More roles").click()
    dlg.get_by_role("group", name="Add a member").locator('[data-agent="sound-designer"]').click()
    dlg.locator('[data-seat-tool="sound-designer"]').click()
    pop = dlg.get_by_role("group", name="Its AI tool for Sound designer")
    assert _words(pop.locator("[data-none]")) == "No AI tool here makes sound: this seat writes it as code or a brief"
    assert pop.locator('[data-group="can"] .shell-pop__row').count() == 0
    cannot = pop.locator('[data-group="cannot"]')
    assert cannot.locator("h4").text_content() == "Cannot make sound" and cannot.locator(".shell-pop__row").count() == 6      # every tool, under what it cannot do
    assert "makes no sound" in _words(cannot.locator('[data-tool="agy"]'))
    cannot.locator('[data-tool="codex"]').click()                                                                          # the person decides
    assert _words(dlg.locator('[data-seat-tool="sound-designer"]')) == "Codex"
    dlg.get_by_label("What it is for").fill("Sounds.")
    dlg.get_by_role("button", name="Save party").click()
    assert _calls(pg, host, "ideas.goal_save")[-1]["tools"] == {"sound-designer": "codex"}


def test_a_seat_set_back_to_the_partys_tool_and_a_seat_that_leaves_send_no_tools(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.locator('[data-seat-tool="grunt"]').click()
    dlg.get_by_role("group", name="Its AI tool for Grunt").locator('[data-tool="codex"]').click()
    assert _words(dlg.locator('[data-seat-tool="grunt"]')) == "Codex"
    dlg.locator('[data-seat-tool="grunt"]').click()
    dlg.get_by_role("group", name="Its AI tool for Grunt").locator('[data-tool=""]').click()
    assert _words(dlg.locator('[data-seat-tool="grunt"]')) == "Party's tool · Claude Code"
    dlg.get_by_label("What it is for").fill("x")
    dlg.get_by_role("button", name="Save party").click()
    assert "tools" not in _calls(pg, host, "ideas.goal_save")[-1]
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.locator('[data-seat-tool="grunt"]').click()
    dlg.get_by_role("group", name="Its AI tool for Grunt").locator('[data-tool="codex"]').click()
    dlg.get_by_role("button", name="Remove Grunt from the party").click()
    dlg.get_by_label("What it is for").fill("y")
    dlg.get_by_role("button", name="Save party").click()
    assert "tools" not in _calls(pg, host, "ideas.goal_save", at_least=2)[-1]                                               # a seat that left took its tool


# -- save ---------------------------------------------------------------------------------------------------------------------------------------------------

def test_save_party_sends_the_leader_the_team_the_size_and_the_recipe_and_the_party_is_shown(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    _press(dlg, "mobile-concept")
    _size(dlg, "Full")
    dlg.get_by_label("What it is for").fill("Draw the app before it is built.")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent == {"about": "Draw the app before it is built.", "leader": "product-designer", "team": ["ui-kit", "accessibility-reviewer"], "every": [],
                    "priority": "normal", "size": "full", "proposal": "mobile-concept"}
    pg.get_by_role("dialog", name="New party").wait_for(state="detached", timeout=WAIT_MS)
    _new_party(pg)
    dlg = _dialog(pg)
    _press(dlg, "design")
    dlg.get_by_label("What it is for").fill("Our screens.")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save", at_least=2)[-1]
    assert sent["leader"] == "product-designer" and sent["team"] == ["ui-kit"] and sent["preset"] == "design" and "proposal" not in sent and sent["size"] == "standard"


def test_a_preset_pressed_and_nothing_typed_is_saved_under_the_presets_name_and_a_name_or_a_line_is_the_persons(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    _press(dlg, "mobile-concept")
    assert dlg.get_by_role("button", name="Save party").is_enabled()                                                       # a preset is a name already
    host.hold = True
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["title"] == "Concept" and sent["about"] == "" and sent["leader"] == "product-designer" and sent["proposal"] == "mobile-concept"
    host.hold = False
    dlg.get_by_role("button", name="Cancel").click()
    pg.get_by_role("dialog", name="New party").wait_for(state="detached", timeout=WAIT_MS)
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.get_by_label("Name", exact=True).fill("Our first look")
    host.hold = True
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save", at_least=2)[-1]
    assert sent["title"] == "Our first look"
    host.hold = False
    dlg.get_by_role("button", name="Cancel").click()
    pg.get_by_role("dialog", name="New party").wait_for(state="detached", timeout=WAIT_MS)
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.get_by_label("What it is for").fill("Screens first.")
    dlg.get_by_role("button", name="Save party").click()
    assert "title" not in _calls(pg, host, "ideas.goal_save", at_least=3)[-1]                                              # the Taskmaster names a party that has only what it is for


def test_esc_closes_a_seats_tool_list_and_not_the_dialog_and_the_focus_goes_back_to_its_button(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    btn = dlg.locator('[data-seat-tool="grunt"]')
    btn.focus()
    pg.keyboard.press("Enter")
    pop = dlg.get_by_role("group", name="Its AI tool for Grunt")
    pop.wait_for(timeout=WAIT_MS)
    assert pop.locator("button").first.evaluate("e => document.activeElement === e")                                       # the list takes the focus
    pg.keyboard.press("ArrowDown")
    assert pop.locator("button").nth(1).evaluate("e => document.activeElement === e")                                    # the arrows move between its buttons
    pg.keyboard.press("Escape")
    pop.wait_for(state="detached", timeout=WAIT_MS)
    assert pg.get_by_role("dialog", name="New party").count() == 1 and btn.evaluate("e => document.activeElement === e")
    btn.click()                                                                                                             # a press elsewhere closes it too
    pop.wait_for(timeout=WAIT_MS)
    dlg.get_by_label("Name", exact=True).click()
    pop.wait_for(state="detached", timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    pg.get_by_role("dialog", name="New party").wait_for(state="detached", timeout=WAIT_MS)                             # and Esc with no list open closes the dialog


def test_the_partys_own_tool_is_sent_and_a_seat_on_the_same_tool_sends_none(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.get_by_role("group", name="Its AI tool").locator("select").select_option("codex")
    dlg.locator('[data-seat-tool="grunt"]').click()
    pop = dlg.get_by_role("group", name="Its AI tool for Grunt")
    assert _words(pop.locator("button.shell-pop__row").first) == "The party's tool (Codex)"
    pop.locator('[data-tool="codex"]').click()                                                                              # the party's tool by name is still the party's
    dlg.get_by_label("What it is for").fill("On codex.")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["tool"] == "codex" and "tools" not in sent


def test_ideation_keeps_its_seats_and_a_size_seats_part_of_them(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    _press(dlg, "ideation")
    assert "Ideation reads every pitch from all four sides" in dlg.inner_text()
    assert dlg.get_by_role("button", name="Remove Product view from the party").count() == 0 and dlg.locator("[data-free]").count() == 0
    _size(dlg, "Full")
    assert (_seats(dlg, "lead"), _seats(dlg, "build"), _seats(dlg, "check")) == (["investor"], ["product-view"], ["skeptic"])
    dlg.get_by_label("What it is for").fill("Pitches.")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["leader"] == "investor" and sent["team"] == ["product-view", "skeptic"] and sent["preset"] == "ideation" and sent["proposal"] == "ideation"


# -- Edit the party -----------------------------------------------------------------------------------------------------------------------------------------

def _edit(pg, host, slug="passkey"):
    _party(host, slug)
    _about(pg, slug)
    pg.get_by_role("region", name="Preview").get_by_role("button", name="Edit the party").click()
    dlg = pg.get_by_role("dialog", name="Edit the party")
    dlg.locator(".shell-seat[data-seat]").first.wait_for(timeout=WAIT_MS)
    return dlg


def test_edit_the_party_is_the_same_dialog_filled_from_the_party_and_keeps_its_remove_foot(desk):
    pg, host = desk
    dlg = _edit(pg, host)
    assert dlg.locator(".shell-presets").count() == 1 and dlg.locator(".shell-preset[aria-pressed=true]").count() == 0
    assert (_seats(dlg, "lead"), _seats(dlg, "build"), _seats(dlg, "check")) == (["architect"], ["grunt", "tester"], ["reviewer"])      # a party made before keeps its seats
    assert dlg.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"
    assert dlg.get_by_label("What it is for").input_value() == "Builds the sign-in."
    assert dlg.get_by_role("button", name="Remove party").count() == 1
    pg.wait_for_timeout(300)
    shot(pg, "desk-edit-party-91.png")
    assert "has at most 1 builder" in dlg.inner_text() or "seat" in dlg.inner_text()
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent == {"slug": "passkey", "about": "Builds the sign-in.", "priority": "high"}                                   # nothing changed: nothing but the words (the party's priority is high)
    pg.get_by_role("dialog", name="Edit the party").wait_for(state="detached", timeout=WAIT_MS)


def test_edit_the_party_saves_a_seats_tool_and_a_size_only_when_they_changed(desk):
    pg, host = desk
    dlg = _edit(pg, host)
    dlg.locator('[data-seat-tool="grunt"]').click()
    dlg.get_by_role("group", name="Its AI tool for Grunt").locator('[data-tool="codex"]').click()
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["tools"] == {"grunt": "codex"} and "leader" not in sent and "size" not in sent and "tool" not in sent


def test_a_member_with_work_open_cannot_leave_by_its_x_or_by_a_size(desk):
    pg, host = desk
    dlg = _edit(pg, host)
    host.party["passkey"][1]["state"] = "working"
    host.bump({})
    pg.wait_for_timeout(300)
    dlg.get_by_role("button", name="Remove Grunt from the party").click()
    assert "Grunt has work open: it cannot leave" in dlg.locator(".shell-bands").inner_text()
    assert _seats(dlg, "build") == ["grunt", "tester"]
    _size(dlg, "Lean")
    assert "has work open: it cannot leave" in dlg.locator(".shell-sizebar").inner_text() and dlg.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"
    assert _calls(pg, host, "ideas.goal_save", at_least=0) == []


# -- other kinds, other hosts ------------------------------------------------------------------------------------------------------------------------------------

def test_a_games_stages_are_the_game_designers_and_a_host_without_the_command_has_the_library_s_stages(gui):
    pg, host, errors = _open(gui, host=PresetHost("game"), ready=".arena[data-goal=passkey]")
    _new_party(pg)
    dlg = _dialog(pg)
    assert dlg.locator(".shell-presets__kind").inner_text() == "For a game: the Orkmaster knows what this project is"
    _press(dlg, "game-concept")
    assert (_seats(dlg, "lead"), _seats(dlg, "build")) == (["game-designer"], ["level-designer"])
    _size(dlg, "Full")
    assert _seats(dlg, "check") == ["playtester"]
    pg.close()
    older = ProposalHost()
    older.presets = False                                                                                                   # a host from before `ideas.party_presets`
    pg, host, errors2 = _open(gui, host=older, ready=".arena[data-goal=passkey]")
    _new_party(pg)
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator(".shell-preset").first.wait_for(timeout=WAIT_MS)
    assert [c.get_attribute("data-craft") for c in dlg.get_by_role("region", name="By stage of the project").locator(".shell-preset").all()] == ["ideation", "release"]
    assert [c.get_attribute("data-craft") for c in dlg.get_by_role("region", name="By craft").locator(".shell-preset").all()] == ["engineering", "design", "data", "marketing", "product", "art"]
    assert dlg.locator(".shell-presets__kind").inner_text() == "For a mobile app: the Orkmaster knows what this project is"      # the kind is the map's
    pg.close()
    assert not errors and not errors2, "\n".join(errors + errors2)


def test_the_parties_rows_proposal_opens_new_party_on_its_seats(desk):
    pg, host = desk
    pg.get_by_role("button", name="The project").click()
    card = pg.locator('.arena-prow[data-row="parties"] article.arena-rcard[data-proposal="mobile-architecture"]')
    card.wait_for(timeout=WAIT_MS)
    card.get_by_role("button", name="Add Mobile app: architecture").click()
    dlg = _dialog(pg)
    assert (_seats(dlg, "lead"), _seats(dlg, "build")) == (["architect"], ["grunt"])
    assert dlg.get_by_label("Name", exact=True).get_attribute("placeholder") == "Mobile app: architecture"
    dlg.get_by_label("What it is for").fill("The structure.")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["proposal"] == "mobile-architecture" and sent["leader"] == "architect"
