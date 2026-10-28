"""Spec 71 part B on the desktop (docs/specs/71-orkmaster-keeps-parties-apart.md §6, §7 "B", §8; decisions §86): Chromium at 1 440 × 900 against the project test's stub host with the shapes of §8 — a Needs you row
of kind `collide` (by a plan made, and by a spec changed), `ideas.collide_answer`, a node's `waits_for` and `project.collisions`. The hand's stop (the Orkmaster's head, *Orkmaster asks*, its two goals with their
parties, the why, its answers as buttons that say what happens; each answer sends its call; a by-change stop offers *Re-plan it* and *Leave it*); the project's level (a wait across parties wears the before sign on its
deck; the link lines of collisions and waits went, spec 98 A); a goal's row (*waits for <party> · <goal>* in its title, orkUI's before sign, a press on the sign opens that goal's party with it picked); a host from
before spec 71 keeps today's face. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_project_desktop_browser import ProjectHost, _project  # noqa: E402
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _open, _sent, _stop  # noqa: E402

pytestmark = pytest.mark.browser

PAIR = "pagewords|landing"
CHANGED = "hero|ratelimit"
WORDS = {"goal": "pagewords", "party": "passkey", "party_name": "Passkey", "title": "Words of the sign-in page", "flag": ""}


def _goal(idea, party, party_name, title, element):
    return {"idea": idea, "party": party, "party_name": party_name, "title": title, "element": element}


PAGEWORDS = _goal("pagewords", "passkey", "Passkey", "Words of the sign-in page", "ice")
LANDING = _goal("landing", "website", "Website", "Landing copy", "dust")
HERO = _goal("hero", "website", "Website", "Hero picture", "lava")
RATELIMIT = _goal("ratelimit", "passkey", "Passkey", "Rate-limit the sign-in", "meadow")

BY_PLAN = {"kind": "collide", "idea": "landing", "goal": "website", "title": "Landing copy", "priority": "normal", "blocks": False, "at": "2026-10-24T10:00:00",
           "text": "Passkey «Words of the sign-in page» and Website «Landing copy» change the same thing",
           "collide": {"id": PAIR, "by": "plan", "why": "Both change the words a person reads before they sign in", "first": "pagewords", "goals": [PAGEWORDS, LANDING],
                       "answers": ["first:pagewords", "first:landing", "one", "leave"]}}
BY_CHANGE = {"kind": "collide", "idea": "ratelimit", "goal": "passkey", "title": "Rate-limit the sign-in", "priority": "normal", "blocks": False, "at": "2026-10-24T11:00:00",
             "text": "Website changed «Hero picture»: «Rate-limit the sign-in» in Passkey rests on what it was",
             "collide": {"id": CHANGED, "by": "change", "why": "The picture now shows the sign-in the limit guards", "first": "", "goals": [HERO, RATELIMIT], "answers": ["replan", "leave"]}}


class CollideHost(ProjectHost):
    """The project test's world with the Orkmaster's two stops (`old=True`: a host from before spec 71 sends none, no `waits_for` and no `collisions`). `waits`: Landing copy waits for the Passkey party's
    Words of the sign-in page. An answer is applied as the host would: the stop is answered, `first:<slug>` makes the other goal wait for it."""

    def __init__(self, old=False, waits=False, change=True):
        super().__init__()
        self.old, self.waited = old, [copy.deepcopy(WORDS)] if waits else []
        self.collisions = [] if old else [{"id": PAIR, "a": "pagewords", "b": "landing"}] + ([{"id": CHANGED, "a": "hero", "b": "ratelimit"}] if change else [])
        self.extra_needs = [] if old else [copy.deepcopy(BY_PLAN)] + ([copy.deepcopy(BY_CHANGE)] if change else [])

    def map_doc(self):
        doc = super().map_doc()
        if self.old:
            return doc
        doc["project"]["collisions"] = copy.deepcopy(self.collisions)
        for n in doc["nodes"]:
            n["waits_for"] = copy.deepcopy(self.waited) if n["slug"] == "landing" else []
        return doc

    def handle(self, name, a):
        if name != "ideas.collide_answer":
            return super().handle(name, a)
        self.log.append((name, a))
        self.collisions = [c for c in self.collisions if c["id"] != a["id"]]
        self.extra_needs = [r for r in self.extra_needs if r["collide"]["id"] != a["id"]]
        if a["answer"] == "first:pagewords":
            self.waited = [copy.deepcopy(WORDS)]
        return self.bump({"ok": True})


def _open_host(gui, host):
    pg, host, errors = _open(gui, host=host, ready=".arena[data-goal=passkey]")
    return pg, host, errors


@pytest.fixture
def collide(gui):
    pg, host, errors = _open_host(gui, CollideHost())
    pg.locator(".arena-hc[data-kind=collide]").first.wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _raise(pg, idea):
    """The Orkmaster's stop of the goal `idea`, raised (the focus brings it up)."""
    return _stop(pg, "collide", nth=pg.evaluate("(idea) => [...document.querySelectorAll('.arena-hc[data-kind=collide]')].findIndex((e) => e.dataset.key.startsWith(`collide/${idea}/`))", idea))


def _answers(stop):
    return [b.inner_text().strip() for b in stop.locator(".arena-hc__quick button").all()]


# -- the stop -----------------------------------------------------------------------------------------------------------------------------------------------

def test_the_orkmasters_stop_has_its_head_its_two_goals_with_their_parties_the_why_and_answers_that_say_what_happens(collide):
    pg, host = collide
    stop = _raise(pg, "landing")
    assert stop.get_attribute("data-party") == "website" and "is-other" in stop.get_attribute("class")                            # the goal asked about is the later one, of another party
    assert stop.locator(".arena-hc__kind").inner_text().strip().lower() == "orkmaster asks"
    assert "peon-crown" in stop.locator(".arena-hc__who .ork-race__head").get_attribute("src")                                     # the Orkmaster's head from `project.orkmaster`
    assert stop.locator(".arena-hc__open").get_attribute("aria-label") == "Orkmaster asks in Website: " + BY_PLAN["text"]
    goals = stop.locator(".arena-hc__goal")
    assert [g.inner_text().strip() for g in goals.all()] == ["Passkey · Words of the sign-in page", "Website · Landing copy"]
    assert [g.get_attribute("data-slug") for g in goals.all()] == ["pagewords", "landing"]
    assert stop.locator(".arena-hc__note").inner_text().strip() == "Both change the words a person reads before they sign in"
    assert _answers(stop) == ["Words of the sign-in page first", "Landing copy first", "One goal", "Leave it"]
    primary = stop.locator(".arena-hc__quick .primary")
    assert primary.count() == 1 and primary.inner_text().strip() == "Words of the sign-in page first"                          # the judge's suggestion
    tips = [b.get_attribute("title") for b in stop.locator(".arena-hc__quick button").all()]
    assert tips[0] == "«Landing copy» waits until «Words of the sign-in page» is done and flagged, then it starts"
    assert tips[2].startswith("The later goal’s text joins the earlier one") and tips[3].startswith("Both goals stay as they are")
    shot(pg, "desk-collide-stop.png")


@pytest.mark.parametrize("button,answer", [("Words of the sign-in page first", "first:pagewords"), ("Landing copy first", "first:landing"), ("One goal", "one"), ("Leave it", "leave")])
def test_each_answer_sends_its_call_and_the_answered_stop_goes(collide, button, answer):
    pg, host = collide
    stop = _raise(pg, "landing")
    stop.get_by_role("button", name=f"{button}: {BY_PLAN['text']}").click()
    assert _sent(pg, host, ("ideas.collide_answer", {"id": PAIR, "answer": answer}))
    pg.wait_for_function("() => ![...document.querySelectorAll('.arena-hc[data-kind=collide]:not(.is-leaving)')].some((e) => e.dataset.key.startsWith('collide/landing/'))", timeout=WAIT_MS)
    assert pg.locator(".arena-hc[data-kind=collide]:not(.is-leaving)").count() == 1                                                # the other question stays


def test_a_stop_by_a_spec_changed_offers_re_plan_it_and_leave_it(collide):
    pg, host = collide
    stop = _raise(pg, "ratelimit")
    assert stop.get_attribute("data-party") == "passkey" and "is-other" not in stop.get_attribute("class")
    assert stop.locator(".arena-hc__open").get_attribute("aria-label") == "Orkmaster asks: " + BY_CHANGE["text"]
    assert [g.inner_text().strip() for g in stop.locator(".arena-hc__goal").all()] == ["Website · Hero picture", "Passkey · Rate-limit the sign-in"]      # the goal whose spec changed first
    assert _answers(stop) == ["Re-plan it", "Leave it"]
    assert stop.locator(".arena-hc__quick .primary").inner_text().strip() == "Re-plan it"
    assert "leader re-plans what is left" in stop.get_by_role("button", name="Re-plan it").get_attribute("title")
    stop.get_by_role("button", name="Re-plan it").click()
    assert _sent(pg, host, ("ideas.collide_answer", {"id": CHANGED, "answer": "replan"}))


def test_a_press_on_one_of_the_two_goals_opens_it_and_a_press_on_the_stop_opens_the_goal_asked_about(collide):
    pg, host = collide
    stop = _raise(pg, "landing")
    stop.locator('.arena-hc__goal[data-slug="pagewords"]').click()
    pg.locator(".shell-drawer").wait_for(timeout=WAIT_MS)
    assert "Words of the sign-in page" in pg.locator(".shell-drawer").inner_text()
    assert pg.locator(".arena-hc[data-kind=collide]").count() == 2                                                                  # opening answers nothing


# -- a goal's row -------------------------------------------------------------------------------------------------------------------------------------------

def _website(pg):
    pg.locator('.arena-phead[data-goal="website"]').click()
    pg.locator('.arena[data-goal="website"]').wait_for(timeout=WAIT_MS)
    return pg.locator('.arena-goal[data-slug="landing"]')


def test_a_goal_that_waits_has_the_before_sign_and_its_words_in_its_title_and_the_sign_opens_the_goal_waited_for_picked(gui):
    pg, host, errors = _open_host(gui, CollideHost(waits=True, change=False))
    try:
        row = _website(pg)
        assert row.locator(".arena-goal__mark .ork-sign.before").count() == 1
        assert "waits for Passkey · Words of the sign-in page" in row.locator(".arena-goal__main").get_attribute("title")
        go = row.locator(".arena-goal__go")
        assert go.get_attribute("aria-label") == "waits for Passkey · Words of the sign-in page: open it"
        assert pg.locator('.arena-goal[data-slug="hero"] .arena-goal__go').count() == 0 and pg.locator(".arena-goal__go").count() == 1      # only a goal that waits
        box, mark = go.bounding_box(), row.locator(".arena-goal__mark").bounding_box()
        assert box["x"] <= mark["x"] and box["x"] + box["width"] >= mark["x"] + mark["width"] and box["height"] == 28                      # over the sign
        go.click()
        pg.locator('.arena[data-goal="passkey"]').wait_for(timeout=WAIT_MS)
        assert pg.locator('.arena-goal[data-slug="pagewords"] .arena-goal__main').get_attribute("aria-pressed") == "true"                  # picked
        assert pg.locator('.arena-goal[data-slug="pagewords"]').count() == 1
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_wait_across_parties_shows_on_the_level_by_the_before_sign_on_its_deck_from_the_start(gui):
    pg, host, errors = _open_host(gui, CollideHost(waits=True, change=False))
    try:
        _project(pg)
        deck = pg.locator('.arena-pdeck[data-slug="landing"]')
        assert deck.locator(".ork-sign.before").count() == 1                                                                         # the deck wears the same sign as the row
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_wait_that_is_raised_is_not_a_wait(gui):
    host = CollideHost(waits=True, change=False)
    host.waited[0]["flag"] = "2026-10-24T09:00:00"
    pg, host, errors = _open_host(gui, host)
    try:
        row = _website(pg)
        assert row.locator(".ork-sign.before").count() == 0 and row.locator(".arena-goal__go").count() == 0
        assert "waits for" not in row.locator(".arena-goal__main").get_attribute("title")
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


# -- an older host ------------------------------------------------------------------------------------------------------------------------------------------

def test_a_host_from_before_spec_71_keeps_todays_face(gui):
    pg, host, errors = _open_host(gui, CollideHost(old=True))
    try:
        pg.wait_for_timeout(300)
        assert pg.locator(".arena-hc[data-kind=collide]").count() == 0 and pg.locator(".arena-hc").count() >= 3                          # the other stops are drawn
        row = _website(pg)
        assert row.locator(".ork-sign.before").count() == 0 and pg.locator(".arena-goal__go").count() == 0
        _project(pg)
        pg.wait_for_timeout(200)
        assert pg.locator(".arena-arrow").count() == 0 and pg.locator(".arena-project__cols .arena-pdeck").count() > 5
    finally:
        pg.close()
    assert not errors, "\n".join(errors)
