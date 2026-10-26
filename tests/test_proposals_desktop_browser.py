"""Spec 75 part B on the desktop (docs/specs/75-parties-fitted-to-the-project.md §5, §6 B; decisions §90): Chromium at 1 440 × 900 against a stub host with spec §4.1's shapes — `ideas.map`'s `project.kind`,
`ideas.proposals` (a mobile app's three proposals, each in Lean, Standard and Full; an empty folder that asks its line; the line read as a wiki, as garbage, with no model), `ideas.goal_save` keeping `size`
and a party's `size` on the map. New party opens on the proposals (the switch changes the heads, the agents and the price; *Make it* sends the leader, the team and `size`); an empty project asks *What is this
project for?* and *Read it* draws a wiki's; *More: the library* shows the tiles with the size switch; the Orkmaster's deal shows the proposals first; *About this party*'s and *Edit the party*'s *Its size* save
it; the top bar has no Target and Settings has it, reworded; an older host (no `project.kind`) keeps today's New party. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import library, roles  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_project_desktop_browser import HAVING, ORK, ProjectHost  # noqa: E402
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _calls, _new_party, _open, _parties, _show_goal  # noqa: E402

pytestmark = pytest.mark.browser

PRICES = {"lean": (0.4, 1.2), "standard": (1.1, 3.4), "full": (2.2, 6.5)}
TARGET = {"lean": "thrift", "standard": "balance", "full": "quality"}


def head(agent_id):
    a = library.get(agent_id)
    return {"race": "skeleton" if a.id.startswith("release-") else roles.RACES[a.craft], "tier": a.tier}


def proposal(pid, name, line, why, leader, build, check, have=False):
    """A proposal as `ideas.proposals` gives it (spec §4.1): Lean the leader alone, Standard the first two builders and the first checker, Full every seat."""
    teams = {"lean": [], "standard": [*build[:2], *check[:1]], "full": [*build, *check]}
    sizes = {}
    for size, team in teams.items():
        low, high = PRICES[size]
        sizes[size] = {"leader": leader, "team": team, "agents": 1 + len(team), "target": TARGET[size], "price": {"low": low, "high": high}, "heads": [head(i) for i in (leader, *team)]}
    return {"id": pid, "name": name, "line": line, "why": why, "have": have, "sizes": sizes}


FEATURES = proposal("mobile-features", "Mobile app: features", "Screens and what people do on them", "ios/ and android/ are here", "product-manager",
                    ["grunt", "artist", "aso", "ui-kit"], ["reviewer", "accessibility-reviewer"])
ARCHITECTURE = proposal("mobile-architecture", "Mobile app: architecture", "How it is built, what it stores, what it calls", "ios/ and android/ are here", "architect",
                        ["grunt", "tester"], ["reviewer", "security-reviewer"])
RELEASE = proposal("release", "Release", "A version out: what is new, the build, the stores' list", "an app goes to the stores", "release-manager",
                   ["release-engineer", "release-notes", "aso"], ["release-checker"])
IDEATION = proposal("ideation", "Ideation", "Pitches judged from four sides", "a new project starts with ideas", "investor",
                    ["product-view", "market-view", "tech-view", "design-view"], ["skeptic"])
WIKI = proposal("wiki", "Wiki", "The team's pages, kept and edited", "a team's wiki", "product-manager", ["copywriter"], ["editor"])
CODE = proposal("engineering", "Engineering", "Plan, build, test and review", "code it cannot tell", "architect", ["grunt", "tester"], ["reviewer"])
TOOLS = {"main": "claude", "tools": [
    {"id": "claude", "name": "Claude Code", "ready": True, "signed_in": True, "installed": True, "experimental": False, "tiers": True},
    {"id": "codex", "name": "Codex", "ready": True, "signed_in": True, "installed": True, "experimental": False, "tiers": True},
    {"id": "pi", "name": "pi", "ready": True, "signed_in": True, "installed": True, "experimental": False, "tiers": False},
    {"id": "cursor", "name": "Cursor", "ready": False, "signed_in": False, "installed": True, "experimental": False, "tiers": False},
    {"id": "agy", "name": "Antigravity", "ready": False, "signed_in": True, "installed": False, "experimental": True, "tiers": True},
    {"id": "hermes", "name": "Hermes Agent", "ready": False, "signed_in": True, "installed": False, "experimental": False, "tiers": False}]}
KINDS = {"mobile": ("a mobile app", ["ios/", "android/"]), "empty": ("an empty folder", []), "wiki": ("a team's wiki", ["mkdocs.yml"]), "code": ("code", ["pyproject.toml"])}


def kind(kid):
    words, signs = KINDS[kid]
    return {"id": kid, "words": words, "signs": list(signs)}


class ProposalHost(ProjectHost):
    """The project test's host (Passkey, Ideation, Website, Release; the Orkmaster's deal) with the Orkmaster's reading of the project: `kind` (mobile, or empty), `ideas.proposals`, the sizes saved with a party
    and a party's `size` on the map. `kind=None`: a host from before spec 75 (no `project.kind`, no `ideas.proposals`). `model=False`: no model reads an empty folder's line."""

    def __init__(self, kind_id="mobile", model=True):
        super().__init__()
        self.kind_id, self.model, self.sizes, self.read = kind_id, model, {}, {"wiki": "wiki", "garbage": "code"}
        self.tools_doc, self.moves, self.refuse_size = copy.deepcopy(TOOLS), {}, ""         # `ideas.tools`; who joins and leaves with a size (`moves[slug][size] = {team, joins, leaves}`); a size the host refuses
        self.deal = [{"id": "mobile-features", "why": "proposal", "n": 0}, {"id": "mobile-architecture", "why": "proposal", "n": 0}, *copy.deepcopy(HAVING[:-2]), {"id": "release", "why": "have", "n": 0}, {"id": "ideation", "why": "have", "n": 0}]

    def map_doc(self):
        doc = super().map_doc()
        if self.kind_id:
            doc["project"]["kind"] = kind(self.kind_id)
        for g in doc["goals"]:
            if g["slug"] in self.sizes:
                g["size"] = self.sizes[g["slug"]]
        return doc

    def working(self, slug, member):
        return any(m["slug"] == member and m["state"] not in ("", "free") for m in self.party.get(slug, []))

    def proposed(self, a):
        if self.kind_id == "empty" and not a.get("about"):
            return {"kind": kind("empty"), "ask": True, "proposals": [copy.deepcopy(IDEATION)]}
        if a.get("about"):                                                  # the line, read by a model of the cheaper tier (§4.2): anything but a kind of §1 is `code`
            if not self.model:
                return {"kind": kind("code"), "ask": False, "read": False, "proposals": [copy.deepcopy(CODE)]}
            got = "wiki" if "wiki" in a["about"] else "code"
            return {"kind": kind(got), "ask": False, "read": True, "proposals": [copy.deepcopy(WIKI if got == "wiki" else CODE), copy.deepcopy(IDEATION)]}
        have = RELEASE | {"have": True}
        return {"kind": kind("mobile"), "ask": False, "proposals": [copy.deepcopy(FEATURES), copy.deepcopy(ARCHITECTURE), copy.deepcopy(have)]}

    def handle(self, name, a):
        if name == "ideas.proposals":
            self.log.append((name, a))
            return self.proposed(a)
        if name == "ideas.tools":                                           # spec 81 §1.4: the list a party's AI tool is picked from
            self.log.append((name, a))
            return copy.deepcopy(self.tools_doc)
        if name == "ideas.party_sizes":                                     # spec 81 §3: what each size would make of the party
            self.log.append((name, a))
            team = self.goals[a["slug"]].get("team", [])
            said = lambda ids: [{"slug": i, "name": i.replace("-", " ").title(), "head": head(i)} for i in ids]       # noqa: E731
            return {"size": self.sizes.get(a["slug"], ""), "sizes": {s: {"recipe": "", "team": (m := self.moves.get(a["slug"], {}).get(s, {})).get("team", team), "tiers": {},
                                                                           "joins": said(m.get("joins", [])), "leaves": said(m.get("leaves", []))} for s in PRICES}}
        if name == "tools.sign_in":                                         # spec 45: the tool's own sign-in opens
            self.log.append((name, a))
            return {"harness": a["harness"], "state": "open", "by": "browser"}
        if name == "ideas.goal_save" and a.get("size") and self.refuse_size:
            self.log.append((name, a))
            return {"error": self.refuse_size}
        if name == "ideas.party_price" and a.get("size"):                    # §3.3: a size's Target and its team, its price
            self.log.append((name, a))
            low, high = PRICES[a["size"]]
            return {"low": low + 0.1 * len(a.get("team") or []), "high": high + 0.1 * len(a.get("team") or []), "learned": False, "ideas": 0, "checks": [], "hints": [], "types": []}
        if name == "ideas.goal_save":
            was = self.goals.get(a.get("slug", ""), {}).get("team", [])
            gone = [m for m in was if m not in a.get("team", was) and self.working(a["slug"], m)]
            if gone:                                                         # spec 52's swap holds on the host: a member with work open never leaves
                self.log.append((name, a))
                return {"error": f"{gone[0].title()} has work open: it cannot leave"}
            was_tool = self.goals.get(a.get("slug", ""), {}).get("tool", "")
            got = super().handle(name, a)
            slug = a.get("slug") or got["slug"]
            self.goals[slug]["tool"] = a["tool"] if "tool" in a else was_tool                # spec 81: the party's AI tool, "" the Main tool
            if a.get("size"):
                self.sizes[slug] = a["size"]
                if a.get("slug") and "team" not in a and a["size"] in self.moves.get(slug, {}):        # the host gives the party the size's team (spec 81 §3)
                    self.goals[slug]["team"] = list(self.moves[slug][a["size"]]["team"])
            return self.bump(got) if a.get("size") else got
        return super().handle(name, a)


@pytest.fixture
def desk(gui):
    pg, host, errors = _open(gui, host=ProposalHost(), ready=".arena[data-goal=passkey]")
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _dialog(pg):
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator(".shell-prop, .shell-props__ask").first.wait_for(timeout=WAIT_MS)
    return dlg


def _card(dlg, pid):
    return dlg.locator(f'.shell-prop[data-proposal="{pid}"]')


def _words(el):
    return " ".join(el.inner_text().split())


# -- New party opens on the proposals ---------------------------------------------------------------------------------------------------------------------------

def test_new_party_opens_on_the_orkmasters_three_proposals_for_a_mobile_project_each_standard_picked(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    assert _calls(pg, host, "ideas.proposals")[-1] == {}
    head_ = dlg.locator(".shell-props__head")
    assert "Orkmaster proposes" in head_.text_content() and "for this project" in head_.text_content()
    assert head_.locator(".shell-props__kind").inner_text() == "a mobile app · ios/ · android/"                          # the kind's words and signs
    assert "peon-crown" in head_.locator(".ork-race__head").get_attribute("src")                                           # the Orkmaster's head
    cards = dlg.locator(".shell-prop")
    assert [c.get_attribute("data-proposal") for c in cards.all()] == ["mobile-features", "mobile-architecture", "release"]
    first = _card(dlg, "mobile-features")
    assert first.locator(".shell-prop__name").text_content() == "Mobile app: features"
    assert first.locator(".shell-prop__line").inner_text() == "Screens and what people do on them" and first.locator(".shell-prop__why").inner_text() == "ios/ and android/ are here"
    group = first.get_by_role("radiogroup", name="Size")
    assert [r.inner_text() for r in group.get_by_role("radio").all()] == ["Lean", "Standard", "Full"]
    assert group.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"                             # Standard picked
    assert first.locator(".shell-prop__heads .ork-race__head").count() == 4 and first.locator(".shell-prop__agents").inner_text() == "4 agents"
    assert first.locator(".shell-prop__price").inner_text() == "≈$1–3 a goal"
    assert _card(dlg, "release").get_attribute("class").count("is-have") == 1 and _card(dlg, "release").locator(".shell-prop__have").inner_text() == "You have one"
    assert dlg.locator(".shell-craft-tile").count() == 0 and dlg.get_by_role("button", name="More: the library").count() == 1      # the library is under More
    assert dlg.get_by_role("button", name="Make it").count() == 3
    pg.wait_for_timeout(300)
    shot(pg, "desk-proposals.png")


def test_the_size_switch_changes_the_heads_the_agents_and_the_price_and_the_arrows_move_it(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    card = _card(dlg, "mobile-features")
    group = card.get_by_role("radiogroup", name="Size")
    group.get_by_role("radio", name="Lean").click()
    assert card.get_attribute("data-size") == "lean" and card.locator(".shell-prop__agents").inner_text() == "one agent"
    assert card.locator(".shell-prop__heads .ork-race__head").count() == 1 and card.locator(".shell-prop__price").inner_text() == "≈$0.40–1.20 a goal"
    group.get_by_role("radio", name="Full").click()
    assert card.locator(".shell-prop__agents").inner_text() == "7 agents" and card.locator(".shell-prop__heads .ork-race__head").count() == 7
    assert card.locator(".shell-prop__price").inner_text() == "≈$2–7 a goal"
    assert group.get_by_role("radio", name="Full").get_attribute("aria-checked") == "true" and group.get_by_role("radio", name="Lean").get_attribute("aria-checked") == "false"
    assert _card(dlg, "mobile-architecture").get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"       # another card keeps its own
    group.get_by_role("radio", name="Full").focus()
    pg.keyboard.press("ArrowLeft")
    assert group.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true" and group.get_by_role("radio", name="Standard").evaluate("e => document.activeElement === e")
    assert [r.get_attribute("tabindex") for r in group.get_by_role("radio").all()] == ["-1", "0", "-1"]                    # one tab stop


def test_make_it_saves_the_party_with_its_leader_its_team_and_its_size_and_shows_it(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    _card(dlg, "mobile-architecture").get_by_role("button", name="Make it").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent == {"title": "Mobile app: architecture", "about": "How it is built, what it stores, what it calls", "leader": "architect", "team": ["grunt", "tester", "reviewer"],
                    "every": [], "priority": "normal", "size": "standard", "proposal": "mobile-architecture"}
    pg.get_by_role("dialog", name="New party").wait_for(state="detached", timeout=WAIT_MS)
    pg.locator('.arena[data-goal="mobile-architecture"], .arena-phead[data-goal="how-it"]').first.wait_for(timeout=WAIT_MS)       # the new party is shown (its slug is the stub's)
    _new_party(pg)
    dlg = _dialog(pg)
    card = _card(dlg, "mobile-features")
    card.get_by_role("radio", name="Lean").click()
    card.get_by_role("button", name="Make it").click()
    sent = _calls(pg, host, "ideas.goal_save", at_least=2)[-1]
    assert sent["leader"] == "product-manager" and sent["team"] == [] and sent["size"] == "lean" and sent["title"] == "Mobile app: features" and sent["proposal"] == "mobile-features"
    _new_party(pg)
    dlg = _dialog(pg)
    _card(dlg, "release").get_by_role("radio", name="Full").click()
    _card(dlg, "release").get_by_role("button", name="Make it").click()
    sent = _calls(pg, host, "ideas.goal_save", at_least=3)[-1]
    assert sent["leader"] == "release-manager" and sent["size"] == "full" and sent["preset"] == "release" and sent["proposal"] == "release" and sent["team"] == ["release-engineer", "release-notes", "aso", "release-checker"]


def test_more_the_library_opens_todays_tiles_and_seats_with_the_size_switch_added(desk):
    pg, host = desk
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.get_by_role("button", name="More: the library").click()
    dlg.locator(".shell-craft-tile").first.wait_for(timeout=WAIT_MS)
    assert dlg.locator(".shell-prop").count() == 0 and dlg.get_by_label("Name", exact=True).count() == 1 and dlg.get_by_role("region", name="Leads").count() == 1
    size = dlg.get_by_role("group", name="Its size")
    assert size.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"
    assert "Works as Balance" in size.inner_text()
    size.get_by_role("radio", name="Full").click()
    assert "Works as Quality" in size.inner_text()
    dlg.locator('.shell-craft-tile[data-craft="design"]').click()
    pg.wait_for_timeout(500)
    assert _calls(pg, host, "ideas.party_price")[-1].get("size") == "full"                                                 # the price reads the size's Target
    dlg.get_by_label("What it is for").fill("Designs of our own.")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["size"] == "full" and sent["leader"] == "product-designer" and sent["about"] == "Designs of our own."


def test_a_proposal_the_host_would_not_give_falls_back_to_the_library(gui):
    host = ProposalHost()
    host.proposed = lambda a: {"error": "No project"}
    pg, host, errors = _open(gui, host=host, ready=".arena[data-goal=passkey]")
    _new_party(pg)
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator(".shell-craft-tile").first.wait_for(timeout=WAIT_MS)
    assert dlg.locator(".shell-prop").count() == 0
    pg.close()


# -- an empty folder asks its line -----------------------------------------------------------------------------------------------------------------------------

def test_an_empty_project_asks_the_line_and_read_it_draws_the_proposals_of_what_it_says(gui):
    pg, host, errors = _open(gui, host=ProposalHost(kind_id="empty"), ready=".arena[data-goal=passkey]")
    _new_party(pg)
    dlg = _dialog(pg)
    assert dlg.locator(".shell-props__kind").inner_text() == "an empty folder"
    ask = dlg.locator(".shell-props__ask")
    line = ask.get_by_label("What is this project for?")
    assert line.get_attribute("placeholder") == "a line is enough: a mobile app for…, our team's wiki, my design files"
    read = ask.get_by_role("button", name="Read it")
    assert read.is_disabled()                                                                                               # a line first
    assert [c.get_attribute("data-proposal") for c in dlg.locator(".shell-prop").all()] == ["ideation"]                     # Ideation beside it at once
    pg.wait_for_timeout(300)
    shot(pg, "desk-proposals-empty.png")
    line.fill("our team's wiki for the support desk")
    read.click()
    dlg.locator('.shell-prop[data-proposal="wiki"]').wait_for(timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.proposals")[-1] == {"about": "our team's wiki for the support desk"}
    assert [c.get_attribute("data-proposal") for c in dlg.locator(".shell-prop").all()] == ["wiki", "ideation"]
    assert dlg.locator(".shell-props__kind").inner_text() == "a team's wiki · mkdocs.yml"
    assert dlg.get_by_label("What is this project for?").input_value() == "our team's wiki for the support desk"             # the line stays to be read again
    dlg.locator('.shell-prop[data-proposal="wiki"]').get_by_role("button", name="Make it").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["leader"] == "product-manager" and sent["team"] == ["copywriter", "editor"] and sent["size"] == "standard"
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_line_no_model_could_read_gives_the_proposals_for_code_and_says_so(gui):
    pg, host, errors = _open(gui, host=ProposalHost(kind_id="empty", model=False), ready=".arena[data-goal=passkey]")
    _new_party(pg)
    dlg = _dialog(pg)
    dlg.get_by_label("What is this project for?").fill("something")
    dlg.get_by_role("button", name="Read it").click()
    dlg.locator('.shell-prop[data-proposal="engineering"]').wait_for(timeout=WAIT_MS)
    assert "No model could read the line: these are the proposals for code." in dlg.inner_text() and dlg.locator(".shell-props__kind").inner_text() == "code · pyproject.toml"
    pg.close()
    assert not errors, "\n".join(errors)


# -- the Orkmaster's deal ---------------------------------------------------------------------------------------------------------------------------------------

def test_the_orkmasters_row_shows_the_proposals_first_each_with_its_why_and_add_opens_new_party_on_it(desk):
    pg, host = desk
    pg.get_by_role("button", name="The project").click()
    cards = pg.locator('.arena-prow[data-row="parties"] article.arena-rcard')
    cards.first.wait_for(timeout=WAIT_MS)
    ids = [c.get_attribute("data-preset") for c in cards.all()]
    assert ids[:2] == ["mobile-features", "mobile-architecture"] and len(ids) == 3 and len(ids) == len(set(ids))        # the proposals first, then the library's; those it has (Release, Ideation) are not offered
    assert "release" not in ids and "ideation" not in ids and ids[2] == "game"                                          # the library's parties follow
    first = cards.nth(0)
    assert first.locator(".arena-rcard__name").inner_text() == "Mobile app: features" and first.locator(".arena-rcard__why").inner_text() == "ios/ and android/ are here"
    assert first.get_attribute("data-proposal") == "mobile-features" and first.locator(".arena-rcard__head .ork-race__head").count() == 1      # its leader's head
    assert first.locator(".arena-rcard__cap").inner_text().startswith("Product manager + 3") and "Screens and what people do on them" in first.locator(".arena-rcard__cap").inner_text()
    first.get_by_role("button", name="Add Mobile app: features").click()
    dlg = _dialog(pg)
    assert dlg.locator('.shell-prop[data-proposal="mobile-features"]').get_attribute("class").count("is-asked") == 1        # New party on that proposal
    assert dlg.locator('.shell-prop[data-proposal="mobile-architecture"]').get_attribute("class").count("is-asked") == 0


def test_a_library_party_of_the_row_opens_new_party_on_the_library_with_the_size_switch(desk):
    pg, host = desk
    pg.get_by_role("button", name="The project").click()
    card = pg.locator('.arena-prow[data-row="parties"] article.arena-rcard[data-preset="game"]')
    card.wait_for(timeout=WAIT_MS)
    card.get_by_role("button", name="Add Game").click()
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator(".shell-craft-tile").first.wait_for(timeout=WAIT_MS)
    assert dlg.locator('.shell-craft-tile[data-craft="game"]').get_attribute("aria-pressed") == "true" and dlg.get_by_role("group", name="Its size").count() == 1


# -- its size in About this party and Edit the party -------------------------------------------------------------------------------------------------------------

TEAM = ["grunt", "tester", "reviewer"]


def _party(host, slug="passkey", size="standard"):
    host.goals[slug].update(leader=host.leader("architect"), team=list(TEAM), every=[], about="Builds the sign-in.", craft="engineering")
    host.party[slug] = [{"slug": s, "name": s.title(), "head": None, "band": b, "state": "free", "why": ""} for s, b in (("architect", "lead"), ("grunt", "build"), ("tester", "build"), ("reviewer", "check"))]
    if size:
        host.sizes[slug] = size
    host.bump({})


def _about(pg, slug="passkey"):
    _show_goal(pg, slug)
    if not pg.locator(".shell-goal").count():                                                                               # a party saved from its Edit stays shown in the drawer
        pg.get_by_role("button", name="About this party").click()
    sec = pg.locator('.shell-goal [data-sec="size"]')
    sec.wait_for(timeout=WAIT_MS)
    return sec


def test_about_this_partys_its_size_shows_each_sizes_price_and_a_press_saves_the_size(desk):
    pg, host = desk
    _party(host)
    sec = _about(pg)
    group = sec.get_by_role("radiogroup", name="Size")
    pg.wait_for_function("() => document.querySelectorAll('[data-sec=size] .ork-switch__sub').length === 3", timeout=WAIT_MS)
    assert [r.locator(".ork-switch__sub").inner_text() for r in group.get_by_role("radio").all()] == ["≈$0.70–1.50 a goal", "≈$1–4 a goal", "≈$3–7 a goal"]
    assert group.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true" and "Works as Balance" in sec.inner_text()
    asked = [a for n, a in host.log if n == "ideas.party_price" and a.get("size")]
    assert {a["size"] for a in asked} == {"lean", "standard", "full"} and all(a["team"] == TEAM and a["leader"] == "architect" for a in asked)      # the party's own team, the size's Target
    pg.wait_for_timeout(300)
    shot(pg, "desk-size.png")
    group.get_by_role("radio", name="Lean").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent == {"slug": "passkey", "about": "Builds the sign-in.", "priority": "high", "size": "lean"}                    # the size alone: the team stays
    pg.wait_for_function("() => document.querySelector('[data-sec=size] [data-value=lean]')?.getAttribute('aria-checked') === 'true'", timeout=WAIT_MS)
    assert "Works as Thrift" in sec.inner_text()


def test_a_party_with_no_size_of_its_own_says_it_works_as_the_target(desk):
    pg, host = desk
    _party(host, size="")
    sec = _about(pg)
    assert sec.get_by_role("radio", checked=True).count() == 0 and "No size of its own yet: it works as Balance" in sec.inner_text()


MOVES = {"lean": {"team": [], "joins": [], "leaves": ["grunt", "tester", "reviewer"]},
         "standard": {"team": list(TEAM), "joins": [], "leaves": []},
         "full": {"team": [*TEAM, "security-reviewer"], "joins": ["security-reviewer"], "leaves": []}}


def test_the_size_switch_shows_the_heads_that_join_and_leave_before_the_press_and_one_press_saves_the_size(desk):
    """Spec 81 §4.3: the heads that join and leave are shown under the switch, then one press saves the size: no *With its team*, no second confirm."""
    pg, host = desk
    _party(host)
    host.moves["passkey"] = copy.deepcopy(MOVES)
    sec = _about(pg)
    pg.wait_for_function("() => document.querySelectorAll('[data-sec=size] .shell-size__moves li').length === 2", timeout=WAIT_MS)
    moves = sec.locator(".shell-size__moves")
    lean, full = moves.locator('[data-size-move="lean"]'), moves.locator('[data-size-move="full"]')
    assert _words(lean) == "Lean Leaves: Grunt, Tester, Reviewer" and lean.locator('[data-move="leaves"] .ork-race__head').count() == 3
    assert _words(full) == "Full Joins: Security Reviewer" and full.locator('[data-move="joins"] .ork-race__head').count() == 1
    assert moves.locator('[data-size-move="standard"]').count() == 0 and "With its team" not in sec.inner_text()              # (the size picked changes no one)
    assert not [1 for n, a in host.log if n == "ideas.goal_save" and a.get("size")]                                           # nothing sent before the press
    pg.wait_for_timeout(300)
    shot(pg, "desk-size-moves.png")
    sec.get_by_role("radio", name="Lean").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent == {"slug": "passkey", "about": "Builds the sign-in.", "priority": "high", "size": "lean"}                    # one press: the size alone, the host gives it its team
    pg.wait_for_function("() => document.querySelector('[data-sec=size] [data-value=lean]')?.getAttribute('aria-checked') === 'true'", timeout=WAIT_MS)
    assert sec.get_by_role("alert").count() == 0 and sec.get_by_role("button").count() == 0


def test_a_member_with_work_open_is_not_let_go_by_a_size_and_it_is_said_in_place(desk):
    pg, host = desk
    _party(host)
    host.moves["passkey"] = copy.deepcopy(MOVES)
    host.party["passkey"] = [{"slug": "architect", "name": "Architect", "head": None, "band": "lead", "state": "free", "why": ""},
                             {"slug": "grunt", "name": "Grunt", "head": None, "band": "build", "state": "work", "why": ""},
                             {"slug": "tester", "name": "Tester", "head": None, "band": "build", "state": "free", "why": ""},
                             {"slug": "reviewer", "name": "Reviewer", "head": None, "band": "check", "state": "free", "why": ""}]
    host.bump({})
    sec = _about(pg)
    pg.wait_for_function("() => document.querySelectorAll('[data-sec=size] .shell-size__moves li').length === 2", timeout=WAIT_MS)
    sec.get_by_role("radio", name="Lean").click()
    assert sec.get_by_role("alert").inner_text() == "Grunt has work open: it cannot leave"
    assert not [1 for n, a in host.log if n == "ideas.goal_save" and a.get("size")]
    sec.get_by_role("radio", name="Full").click()                                                                              # a size that lets no one go is free to pick
    assert _calls(pg, host, "ideas.goal_save")[-1]["size"] == "full" and sec.get_by_role("alert").count() == 0


def test_a_hosts_own_refusal_of_a_size_is_said_in_place_not_toasted(desk):
    pg, host = desk
    _party(host)
    host.moves["passkey"] = copy.deepcopy(MOVES)
    host.refuse_size = "Tester has work open: it cannot leave"                                                                  # the page's own list says free: the host knows better
    sec = _about(pg)
    pg.wait_for_function("() => document.querySelectorAll('[data-sec=size] .shell-size__moves li').length === 2", timeout=WAIT_MS)
    sec.get_by_role("radio", name="Lean").click()
    sec.get_by_role("alert").wait_for(timeout=WAIT_MS)
    assert sec.get_by_role("alert").inner_text() == "Tester has work open: it cannot leave" and pg.locator(".ork-toast, .shell-toast").count() == 0
    assert sec.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"


def test_a_host_that_refuses_a_team_change_with_work_open_is_heard(desk):
    """The host refuses a change that drops a member with work open (spec 75 host, 5): the refusal is shown as it is said."""
    pg, host = desk
    _party(host)
    host.party["passkey"][1]["state"] = "work"
    host.bump({})
    _about(pg)
    pg.get_by_role("region", name="Preview").get_by_role("button", name="Edit the party").click()
    dlg = pg.get_by_role("dialog", name="Edit the party")
    dlg.get_by_role("button", name="Change the party").click()
    dlg.get_by_role("button", name="Take out: Grunt").click()
    dlg.get_by_role("button", name="Save party").click()
    pg.get_by_text("Grunt has work open: it cannot leave").first.wait_for(timeout=WAIT_MS)
    assert dlg.is_visible()                                                                                                  # the dialog stays: nothing was saved


def test_edit_the_party_has_its_size_and_save_party_sends_it(desk):
    pg, host = desk
    _party(host)
    _about(pg)
    pg.get_by_role("region", name="Preview").get_by_role("button", name="Edit the party").click()
    dlg = pg.get_by_role("dialog", name="Edit the party")
    size = dlg.get_by_role("group", name="Its size")
    size.wait_for(timeout=WAIT_MS)
    assert size.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"
    size.get_by_role("radio", name="Full").click()
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert sent["slug"] == "passkey" and sent["size"] == "full" and "team" not in sent                                      # the size alone
    host.moves["passkey"] = copy.deepcopy(MOVES)
    _about(pg)
    pg.get_by_role("region", name="Preview").get_by_role("button", name="Edit the party").click()
    dlg = pg.get_by_role("dialog", name="Edit the party")
    size = dlg.get_by_role("group", name="Its size")
    pg.wait_for_function("() => document.querySelectorAll('.shell-modal .shell-size__moves li').length === 1", timeout=WAIT_MS)       # (it is Full now: Lean is the one that changes who is in)
    assert "Lean Leaves: Grunt, Tester, Reviewer" in _words(size)                                                                # (shown before the press)
    size.get_by_role("radio", name="Lean").click()
    assert size.get_by_role("radio", name="Lean").get_attribute("aria-checked") == "true"
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save", at_least=2)[-1]
    assert sent["size"] == "lean" and sent["team"] == [] and sent["leader"] == "architect"            # the team the size gave goes with Save party


# -- the Target leaves the top bar; Settings keeps it ----------------------------------------------------------------------------------------------------------------

def test_the_top_bar_has_no_target_and_settings_has_it_under_a_party_with_no_size_of_its_own(desk):
    pg, host = desk
    top = pg.locator(".shell-top")
    assert top.get_by_role("button", name="Agents").count() == 0 and top.get_by_role("button", name="Files").count() == 0 and top.get_by_role("button", name="Settings").count() == 1
    assert "Target" not in top.inner_text() and pg.locator(".board-target__chip").count() == 0
    top.get_by_role("button", name="Settings").click()
    dlg = pg.get_by_role("dialog", name="Settings")
    field = dlg.get_by_role("group", name="A party with no size of its own works as")
    assert [r.inner_text() for r in field.get_by_role("radio").all()] == ["Thrift", "Balance", "Quality"]
    assert field.get_by_role("radio", name="Balance").get_attribute("aria-checked") == "true"
    assert "the default: each step on the tier it needs" in field.inner_text()
    field.get_by_role("radio", name="Quality").click()
    assert _calls(pg, host, "ideas.board_set")[-1] == {"target": "quality"}
    pg.wait_for_function("() => document.querySelector('[data-settings=target] [data-value=quality]')?.getAttribute('aria-checked') === 'true'", timeout=WAIT_MS)
    assert "heavier models, more reasoning, three proposals a night" in field.inner_text()


# -- an older host --------------------------------------------------------------------------------------------------------------------------------------------

def test_a_host_without_the_reading_keeps_todays_new_party_and_asks_for_no_proposals(gui):
    pg, host, errors = _open(gui, host=ProposalHost(kind_id=None), ready=".arena[data-goal=passkey]")
    _new_party(pg)
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator(".shell-craft-tile").first.wait_for(timeout=WAIT_MS)
    assert dlg.locator('.shell-craft-tile[aria-pressed="true"]').get_attribute("data-craft") == "engineering" and dlg.locator(".shell-prop").count() == 0
    assert dlg.get_by_role("group", name="Its size").count() == 0 and dlg.get_by_role("button", name="More: the library").count() == 0
    dlg.get_by_label("What it is for").fill("A party as before.")
    dlg.get_by_role("button", name="Save party").click()
    sent = _calls(pg, host, "ideas.goal_save")[-1]
    assert "size" not in sent and sent["leader"] == "architect"
    assert not [1 for n, _ in host.log if n == "ideas.proposals"]
    pg.get_by_role("dialog", name="New party").wait_for(state="detached", timeout=WAIT_MS)
    pg.get_by_role("button", name="The project").click()                                                                     # the row's parties are the library's, as before
    cards = pg.locator('.arena-prow[data-row="parties"] article.arena-rcard')
    cards.first.wait_for(timeout=WAIT_MS)
    assert cards.count() >= 2 and all(c.get_attribute("data-proposal") == "" for c in cards.all())
    assert not [1 for n, _ in host.log if n == "ideas.proposals"]
    top = pg.locator(".shell-top")
    assert "Target" not in top.inner_text()                                                                                   # the Target left the top bar for every host
    pg.locator(".shell-goal").wait_for(timeout=WAIT_MS)                                                                      # the party just made is shown: no size on this host
    assert pg.locator('.shell-goal [data-sec="size"]').count() == 0
    pg.close()
    assert not errors, "\n".join(errors)
