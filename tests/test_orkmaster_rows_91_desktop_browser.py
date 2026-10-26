"""Spec 91 part F on the desktop (docs/specs/91-the-owners-list.md §8, decisions §107.6): Chromium at 1 440 × 900 against the proposal test's stub host (the Passkey, Ideation, Website and Release parties, the
Orkmaster's deal and its reading of a mobile project) with `ideas.kind_for` answered by the real words (core/idea_kind.py). The Orkmaster's level has, beside its crowned head, two rows: *Parties* (a dashed
*New party* and two or three ready parties, each with *Add*) and *New goal* (a line, *for <party>*, *Add goal*; under it the party's kinds, three at most, the guessed one marked, and *More kinds…*). The two
piles and the project line's + are gone. The line is guessed a kind as it is typed and never asks for one first; *Add goal* sends what New goal sends. Screenshots to the directory ORKCRAFT_SHOTS_DIR names
when it is set."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.core import idea_kind  # noqa: E402
from orkboard.realm import goal_types  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_project_desktop_browser import ARTIST, LACKING, LOGO, _project  # noqa: E402
from tests.test_proposals_desktop_browser import ProposalHost  # noqa: E402
from tests.test_route_desktop_browser import RELEASE_TYPE, shot  # noqa: E402
from tests.test_shell_browser import _calls, _open  # noqa: E402

pytestmark = pytest.mark.browser


def kind_row(type_id, used=0, missing=()):
    t = goal_types.BY_ID[type_id]
    return {"id": t.id, "name": t.name, "sign": t.sign, "line": t.line, "lens": t.lens, "refs": t.refs, "used": used, "missing": list(missing), "asks": []}


BUG, FEATURE, TIDY, SCREEN = kind_row("bug", 2), kind_row("feature"), kind_row("tidy"), kind_row("screen")
PASSKEY = [BUG, kind_row("logo", missing=[ARTIST]), FEATURE, TIDY, SCREEN]              # five: the row shows three
WEBSITE = [kind_row("logo"), SCREEN]
ROWS = [("passkey", "Passkey"), ("website", "Website"), ("release", "Release"), ("ideas", "Ideation")]


class RowsHost(ProposalHost):
    """The proposal test's world with five kinds in Passkey, two in Website and `ideas.kind_for` / `ideas.party_for` as the host answers them: the kinds the line says (the real words), the party that offers the kind."""

    def __init__(self):
        super().__init__()
        self.types = {"passkey": PASSKEY, "website": WEBSITE, "release": [RELEASE_TYPE]}

    def map_doc(self):
        doc = super().map_doc()
        for g in doc["goals"]:
            g["types"] = copy.deepcopy(self.types.get(g["slug"], []))
        return doc

    def handle(self, name, a):
        if name == "ideas.kind_for":
            self.log.append((name, a))
            offered = [t["id"] for t in self.types.get(a.get("party", ""), [])] if a.get("party") else [t.id for t in goal_types.CATALOG]
            return {"type": idea_kind.guess(a.get("text"), offered), "types": idea_kind.ranked(a.get("text"), offered)}
        if name == "ideas.party_for" and a.get("type"):
            self.log.append((name, a))

            def fit(slug):
                found = next((t for t in self.types.get(slug, []) if t["id"] == a["type"]), None)
                return "none" if found is None else "missing" if found["missing"] else "whole"
            parties = [{"party": s, "name": n, "fits": fit(s), "missing": [ARTIST] if fit(s) == "missing" else []} for s, n in ROWS]
            parties.sort(key=lambda p: ("whole", "missing", "none").index(p["fits"]))
            return {"parties": parties, "suggested": parties[0]["party"] if parties[0]["fits"] != "none" else "passkey"}
        return super().handle(name, a)


@pytest.fixture
def rows(gui):
    pg, host, errors = _open(gui, host=RowsHost(), ready=".arena[data-goal=passkey]")
    _project(pg)
    pg.locator(".arena-prows").wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _parties(pg):
    return pg.locator('.arena-prow[data-row="parties"]')


def _goal(pg):
    return pg.locator('.arena-prow[data-row="goal"]')


def _line(pg):
    return pg.locator(".arena-goalrow__text")


def _chips(pg):
    return pg.locator(".arena-kind")


def _type(pg, words):
    """The line typed as a person does (key by key), then waited for until its kind was asked."""
    _line(pg).click()
    pg.keyboard.type(words, delay=5)


def _for(pg):
    return pg.locator(".arena-for__btn")


def _use_party(pg, slug):
    _for(pg).click()
    pg.locator(f'.arena-for__opt[data-party="{slug}"]').click()


# -- the rows beside the Orkmaster's head ---------------------------------------------------------------------------------------------------------------------

def test_the_rows_stand_beside_the_orkmasters_crowned_head_parties_first_and_new_goal_under_it(rows):
    pg, host = rows
    head = pg.locator(".arena-prows__ork .ork-race__head")
    assert "peon-crown" in head.get_attribute("src") and head.bounding_box()["width"] == 64                                  # the crowned head, 64 px
    parties, goal = _parties(pg), _goal(pg)
    assert parties.locator(".arena-prow__lab b").text_content() == "Parties" and parties.locator(".arena-prow__lab .arena-cap").inner_text() == "who works on this project"
    assert goal.locator(".arena-prow__lab b").text_content() == "New goal" and goal.locator(".arena-prow__lab .arena-cap").inner_text() == "say it in a line: the Orkmaster picks its kind"
    hb, pb, gb = head.bounding_box(), parties.bounding_box(), goal.bounding_box()
    assert hb["x"] + hb["width"] <= pb["x"] and hb["x"] + hb["width"] <= gb["x"]                                              # the rows are to its right
    assert pb["y"] < gb["y"] and hb["y"] <= pb["y"] + 8 and hb["y"] + hb["height"] <= gb["y"] + gb["height"]                    # parties over new goal, the head beside both
    assert pb["y"] + pb["height"] <= pg.locator(".arena-project__body").bounding_box()["y"]                                    # all of it over the table
    shot(pg, "desk-orkmaster-rows.png")


def test_no_pile_and_no_plus_stand_any_more_new_goal_and_new_party_are_the_rows(rows):
    pg, host = rows
    assert pg.locator(".arena-new, .arena-new__pile, .arena-pjnew, .arena-pjgoal").count() == 0
    assert pg.locator(".arena-left__proj").get_by_role("button", name="New goal").count() == 0 and pg.locator(".arena-plus").count() == 0
    assert pg.locator(".arena-prows").get_by_role("button", name="New party", exact=True).count() == 1
    assert pg.locator(".arena-prows").get_by_role("button", name="Add goal", exact=True).count() == 1


def test_the_parties_row_has_a_dashed_new_party_and_two_or_three_ready_parties_each_with_its_head_its_name_who_and_add(rows):
    pg, host = rows
    new = _parties(pg).get_by_role("button", name="New party", exact=True)
    assert new.get_attribute("class").count("arena-rcard--new") == 1 and new.evaluate("e => getComputedStyle(e).borderTopStyle") == "dashed"
    cards = _parties(pg).locator("article.arena-rcard")
    assert 2 <= cards.count() <= 3
    assert [c.get_attribute("data-preset") for c in cards.all()] == ["mobile-features", "mobile-architecture", "game"]        # the proposals first, then the library's, those it has never
    first = cards.first
    assert first.locator(".arena-rcard__head .ork-race__head").count() == 1 and first.locator(".arena-rcard__name").inner_text() == "Mobile app: features"
    assert "Screens and what people do on them" in first.locator(".arena-rcard__cap").inner_text() and first.locator(".arena-rcard__who").inner_text().startswith("Product manager")
    assert first.get_by_role("button", name="Add", exact=False).inner_text() == "Add"
    assert _calls(pg, host, "ideas.proposals")[-1] == {}
    assert _parties(pg).locator('[data-preset="release"], [data-preset="ideation"]').count() == 0                            # those the project has are not offered


def test_new_party_opens_new_party(rows):
    pg, host = rows
    _parties(pg).get_by_role("button", name="New party", exact=True).click()
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator(".shell-prop").first.wait_for(timeout=WAIT_MS)
    assert dlg.locator(".shell-prop.is-asked").count() == 0                                                                  # the proposals, none picked out


def test_add_takes_a_proposal_as_the_pile_did_and_a_library_party_opens_the_library_picked(rows):
    pg, host = rows
    _parties(pg).locator('article[data-proposal="mobile-features"]').get_by_role("button", name="Add Mobile app: features").click()
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator(".shell-prop").first.wait_for(timeout=WAIT_MS)
    assert "is-asked" in dlg.locator('.shell-prop[data-proposal="mobile-features"]').get_attribute("class")
    assert "is-asked" not in dlg.locator('.shell-prop[data-proposal="mobile-architecture"]').get_attribute("class")
    pg.keyboard.press("Escape")
    dlg.wait_for(state="detached", timeout=WAIT_MS)
    _parties(pg).locator('article[data-preset="game"]').get_by_role("button", name="Add Game").click()
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator(".shell-craft-tile").first.wait_for(timeout=WAIT_MS)
    assert dlg.locator('.shell-craft-tile[data-craft="game"]').get_attribute("aria-pressed") == "true"


def test_a_host_that_does_not_read_the_project_offers_the_librarys_parties_in_the_deals_order_and_asks_for_no_proposals(gui):
    host = RowsHost()
    host.kind_id = None
    host.deal = copy.deepcopy(LACKING)
    pg, host, errors = _open(gui, host=host, ready=".arena[data-goal=passkey]")
    _project(pg)
    cards = _parties(pg).locator("article.arena-rcard")
    cards.first.wait_for(timeout=WAIT_MS)
    assert [c.get_attribute("data-preset") for c in cards.all()] == ["release", "ideation", "game"]                           # Release first when flags wait, Ideation next
    assert cards.first.locator(".arena-rcard__name").inner_text() == "Release" and cards.first.locator(".ork-race__head").count() == 1
    assert not [1 for n, _ in host.log if n == "ideas.proposals"]
    cards.first.get_by_role("button", name="Add Release").click()
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator(".shell-craft-tile").first.wait_for(timeout=WAIT_MS)
    assert dlg.locator('.shell-craft-tile[data-craft="release"]').get_attribute("aria-pressed") == "true" and dlg.locator(".arena-releasesfrom").count() == 1
    pg.close()
    assert not errors, "\n".join(errors)


# -- the new goal: the party, the kinds ----------------------------------------------------------------------------------------------------------------------

def test_before_a_word_is_typed_the_orkmaster_suggests_the_party_and_shows_its_three_most_used_kinds_with_none_marked(rows):
    pg, host = rows
    _for(pg).wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => document.querySelector('.arena-for__btn')?.innerText.includes('Passkey')", timeout=WAIT_MS)
    assert _for(pg).inner_text().strip() == "for Passkey" and "type" not in _calls(pg, host, "ideas.party_for")[-1]                 # the Orkmaster's guess with no kind: the first party
    assert pg.locator(".arena-kinds__label").inner_text() == "Passkey's kinds:"
    assert [c.get_attribute("data-type") for c in _chips(pg).all()] == ["bug", "logo", "feature"]                                  # three of five, as the party lists them
    assert all(c.get_attribute("data-guessed") == "false" and c.get_attribute("aria-pressed") == "false" for c in _chips(pg).all())
    assert pg.locator(".arena-kinds").get_by_role("button", name="More kinds…").count() == 1
    assert pg.get_by_role("button", name="Add goal", exact=True).is_disabled()                                                    # nothing to add yet
    assert not [1 for n, _ in host.log if n == "ideas.kind_for"]                                                                  # no line, no guess


def test_typing_a_goal_guesses_its_kind_marks_it_and_never_asks_for_one_first(rows):
    pg, host = rows
    _use_party(pg, "passkey")
    _type(pg, "Tidy up and refactor the sign-in code")
    guessed = pg.locator('.arena-kind[data-guessed="true"]')
    guessed.wait_for(timeout=WAIT_MS)
    assert guessed.get_attribute("data-type") == "tidy" and guessed.inner_text().strip() == "Clean up · guessed" and guessed.get_attribute("aria-pressed") == "true"
    assert _chips(pg).first.get_attribute("data-type") == "tidy" and _chips(pg).count() == 3                                       # the guessed one leads, still three
    assert any(a.get("text", "").startswith("Tidy up") for a in _calls(pg, host, "ideas.kind_for"))
    shot(pg, "desk-orkmaster-guess.png")
    _line(pg).fill("")                                                                                                            # the line emptied: nothing is guessed
    pg.wait_for_function("() => !document.querySelector('.arena-kind[data-guessed=true]')", timeout=WAIT_MS)
    assert pg.get_by_role("button", name="Add goal", exact=True).is_disabled()


def test_the_orkmaster_guesses_the_party_from_the_kind_the_line_says_and_a_party_picked_by_the_person_stays(rows):
    pg, host = rows
    _type(pg, "A new logo for the shop")
    pg.wait_for_function("() => document.querySelector('.arena-for__btn')?.innerText.includes('Website')", timeout=WAIT_MS)       # Website takes a logo whole, Passkey misses an Artist
    assert _calls(pg, host, "ideas.party_for", at_least=2)[-1] == {"type": "logo"}
    assert pg.locator(".arena-kinds__label").inner_text() == "Website's kinds:" and _chips(pg).first.get_attribute("data-type") == "logo"
    assert _chips(pg).first.inner_text().strip() == "New logo · guessed"
    _use_party(pg, "release")                                                                                                       # the person picks another: it stays as the line goes on
    _line(pg).press_sequentially(" in pixel art", delay=5)
    pg.wait_for_timeout(700)
    assert _for(pg).inner_text().strip() == "for Release"


def test_for_a_party_lists_the_parties_with_how_they_fit_and_switches_the_kinds(rows):
    pg, host = rows
    _type(pg, "Fix the crash")
    pg.locator('.arena-kind[data-type="bug"][data-guessed="true"]').wait_for(timeout=WAIT_MS)
    _for(pg).click()
    options = pg.get_by_role("listbox", name="Its party").get_by_role("option")
    shot(pg, "desk-orkmaster-for.png")
    assert [o.get_attribute("data-party") for o in options.all()] == ["passkey", "website", "release", "ideas"] and options.first.get_attribute("aria-selected") == "true"
    assert options.first.locator("small").inner_text() == "takes it whole" and options.nth(1).locator("small").inner_text() == "no one there does it"
    options.nth(1).click()                                                                                                          # Website
    assert _for(pg).inner_text().strip() == "for Website" and pg.get_by_role("listbox").count() == 0
    assert pg.locator(".arena-kinds__label").inner_text() == "Website's kinds:"
    assert [c.get_attribute("data-type") for c in _chips(pg).all()] == ["logo", "screen"]                                          # its own two: the other party's guess is not carried
    assert pg.locator('.arena-kind[data-guessed="true"]').count() == 0 and pg.locator('.arena-kind[aria-pressed="true"]').count() == 0
    _for(pg).click()
    pg.keyboard.press("Escape")
    assert pg.get_by_role("listbox").count() == 0 and _for(pg).inner_text().strip() == "for Website"                                  # Esc puts the list away, keeping the pick
    _use_party(pg, "passkey")
    pg.locator('.arena-kind[data-type="bug"][data-guessed="true"]').wait_for(timeout=WAIT_MS)                                       # back: the line's kind is Passkey's again
    assert _chips(pg).first.get_attribute("data-type") == "bug"


def test_more_kinds_opens_the_full_list_grouped_with_the_line_carried_into_new_goal(rows):
    pg, host = rows
    _type(pg, "Offline mode for the shop")
    pg.get_by_role("button", name="More kinds…").click()
    deal = pg.get_by_role("dialog", name="New goal for the project")
    deal.locator(".arena-type").first.wait_for(timeout=WAIT_MS)
    groups = deal.get_by_role("group")
    assert [g.locator(".arena-types__label").text_content() for g in groups.all()] == ["Passkey's kinds:", "Other parties' kinds"]
    assert [c.get_attribute("data-type") for c in deal.locator(".arena-type").all()][:6] == ["", "bug", "logo", "feature", "tidy", "screen"]       # Your own goal, then all five of the party
    assert "release" in [c.get_attribute("data-type") for c in deal.locator(".arena-type").all()]                                    # the others' follow
    pg.wait_for_timeout(500)
    deal.locator('.arena-type[data-type="tidy"]').click()
    form = pg.get_by_role("dialog", name="New goal")
    form.locator('.arena-typed[data-type="tidy"]').wait_for(timeout=WAIT_MS)
    assert form.get_by_label("The goal", exact=True).input_value() == "Offline mode for the shop"                                    # what was typed is there
    assert not [1 for n, _ in host.log if n == "ideas.add"]                                                                          # nothing was added by choosing a kind
    pg.keyboard.press("Escape")


def test_add_goal_sends_what_new_goal_sends_the_line_the_party_its_priority_and_the_kind_and_the_row_is_cleared(rows):
    pg, host = rows
    _use_party(pg, "passkey")
    _type(pg, "Fix the crash when signing in")
    pg.locator('.arena-kind[data-type="bug"][data-guessed="true"]').wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Add goal", exact=True).click()
    sent = _calls(pg, host, "ideas.add")[-1]
    assert sent == {"text": "Fix the crash when signing in", "track": "passkey", "priority": "high", "type": "bug"}                 # ideas.add as the dialog sends it: Passkey's own priority
    pg.wait_for_function("() => document.querySelector('.arena-goalrow__text').value === ''", timeout=WAIT_MS)
    assert pg.locator(".arena-kind[aria-pressed=true]").count() == 0 and pg.get_by_role("button", name="Add goal", exact=True).is_disabled()
    # a kind the person picks instead of the guessed one, with Enter in the line
    _type(pg, "Tidy up and refactor the sign-in code")
    pg.locator('.arena-kind[data-type="tidy"][data-guessed="true"]').wait_for(timeout=WAIT_MS)
    pg.locator('.arena-kind[data-type="bug"]').click()
    assert pg.locator('.arena-kind[data-type="bug"]').get_attribute("aria-pressed") == "true" and pg.locator('.arena-kind[data-type="tidy"]').get_attribute("aria-pressed") == "false"
    _line(pg).press("Enter")
    sent = _calls(pg, host, "ideas.add", at_least=2)[-1]
    assert sent["type"] == "bug" and sent["track"] == "passkey" and sent["text"] == "Tidy up and refactor the sign-in code"
    # the pick pressed again lets go: a goal of no kind
    _type(pg, "Something for the shop")
    pg.locator('.arena-kind[data-type="logo"]').click()
    pg.locator('.arena-kind[data-type="logo"]').click()
    pg.get_by_role("button", name="Add goal", exact=True).click()
    sent = _calls(pg, host, "ideas.add", at_least=3)[-1]
    assert "type" not in sent and sent["text"] == "Something for the shop"


def test_a_party_that_takes_pitches_has_no_kinds_and_the_goal_goes_as_a_pitch(rows):
    pg, host = rows
    _use_party(pg, "ideas")
    assert pg.locator(".arena-kind").count() == 0 and "takes it as a pitch" in pg.locator(".arena-kinds").inner_text()
    _type(pg, "A pitch for dark mode")
    pg.get_by_role("button", name="Add goal", exact=True).click()
    sent = _calls(pg, host, "ideas.add")[-1]
    assert sent["track"] == "ideas" and sent["text"] == "A pitch for dark mode" and "type" not in sent


def test_the_rows_hold_in_a_narrow_window_with_no_sideways_scroll(gui):
    server, browser = gui
    pg, host, errors = _open(gui, viewport={"width": 1000, "height": 800}, host=RowsHost(), ready=".arena[data-goal=passkey]")
    _project(pg)
    pg.locator(".arena-prows").wait_for(timeout=WAIT_MS)
    box = pg.locator(".arena-prows").bounding_box()
    assert pg.locator(".arena-goalrow__add").bounding_box()["x"] + pg.locator(".arena-goalrow__add").bounding_box()["width"] <= box["x"] + box["width"]       # Add goal stays in sight
    assert pg.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
    pg.close()
    assert not errors, "\n".join(errors)
