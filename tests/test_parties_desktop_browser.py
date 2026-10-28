"""Spec 100 part D, the one place of the parties (docs/specs/100-a-goals-way-as-cards.md §4, decisions §151.5, §164; spec 99 §1; mockup docs/mockups/s2b/ state 8), at both widths (`tests/narrow.py`), against the
stub host of the table's tests (tests/test_table_desktop_browser.py `TableHost`) with the commands of the parties added: `ideas.stage`, `ideas.stage_set`, `ideas.party_presets` (a game's, as the realm gives them),
`ideas.party_price`, `ideas.goal_save` and `ideas.project_ask`; and `ideas.project_facts`, which the real host does not have yet.

The first start (no party yet): the project's kind in a field, the stages' headings with the parties under them, the project's stage picked on its heading and the stages reached ticked, Release ticked and locked in
every project, each party its leader's head (its party's race), **Start** making the ticked parties and then asking the project. A party opened at the right: the size's three lines and their price a goal, the
leader's row with its name of its own beside its role (§164), its map, its AI tool's mark and tier; **Does** and **Checks** with their cards, at most five and two ticked, *Checks* dimmed under *Lean* with the words of
each size; a made party: **Save** (*From the next task*) with only what changed, a seat's popover; what the leader keeps (read only). The narrow width: the left a screen and the right the next. Screenshots go to the
directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import library, party_presets, project_stage  # noqa: E402
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost, shot, watch  # noqa: E402

pytestmark = pytest.mark.browser

RECIPES = {"game": "game-design", "tech": "tech", "art": "art", "release": "release"}
PRICE = {"lean": (0.5, 1.5), "standard": (1.0, 3.0), "full": (2.0, 5.0)}        # dollars a goal; the stub's rate is 0.5 dollars a percent
FACTS = [{"key": "for_whom", "text": "Friends on a couch", "by": "person"}, {"key": "leaves_out", "text": "Online ranking", "by": "read"}]


class PartiesHost(TableHost):
    """The table's host with the one place of the parties' commands. `made`: the project's four parties are there (else none: the first start)."""

    def __init__(self, made: bool = True, stage: str = "being_made", facts: bool = False, wide_squads: bool = False):
        super().__init__(rich=False, line=0)
        if not made:
            self.parties, self.nodes = [], []
        self.stage, self.facts, self.wide_squads, self.made_extra = stage, facts, wide_squads, []

    def snapshot(self):
        s = super().snapshot()
        s["state"]["rate"] = {"usd_per_pct": 0.5, "window": "week", "tool": "claude"}
        return s

    def board(self):
        b = super().board()
        for t in b["tracks"]:
            t["recipe"] = RECIPES.get(t["slug"], "")
            t["size"] = "standard" if t["slug"] == "tech" else "lean"
        return b

    def presets(self):
        rows = party_presets.listed("game")
        if self.wide_squads:                                                     # more cards than a squad may hold: a sixth who does in Art, a third who checks in Tech
            for r in rows:
                if r["id"] == "art":
                    r["build"] = [*r["build"], "ui-kit"]
                if r["id"] == "tech":
                    r["check"] = [*r["check"], "art-reviewer"]
        return {"kind": {"id": "game", "words": "a game"}, "presets": rows}

    def stage_doc(self):
        return {"stage": self.stage, "read": "being_made", "kept": self.stage != "being_made", "kind": "game", "offered": project_stage.offered("game")}

    def handle(self, name, a):
        if name == "ideas.stage":
            self.log.append((name, a))
            return self.stage_doc()
        if name == "ideas.stage_set":
            self.log.append((name, a))
            self.stage = a["stage"]
            return self.stage_doc()
        if name == "ideas.party_presets":
            self.log.append((name, a))
            return self.presets()
        if name == "ideas.party_price":
            self.log.append((name, a))
            low, high = PRICE[a["size"]]
            return {"low": low, "high": high, "learned": False, "ideas": 0, "checks": [], "hints": [], "types": []}
        if name == "ideas.goal_save":
            self.log.append((name, a))
            if not a.get("slug"):
                from tests.test_table_desktop_browser import party
                slug = a["preset"]
                self.parties.append(party(slug, len(self.parties), []))
                self.made_extra.append(slug)
            self.rev += 1
            return {"slug": a.get("slug") or a["preset"]}
        if name == "ideas.project_ask":
            self.log.append((name, a))
            return {"ok": True}
        if name == "ideas.project_facts":
            self.log.append((name, a))
            return {"facts": FACTS if self.facts and a["party"] == "tech" else []}
        return super().handle(name, a)

    def called(self, name):
        return [a for n, a in self.log if n == name]


def start(gui, width, errors, **kw):
    """The window at `width` against a PartiesHost: `(page, host)`."""
    server, browser = gui
    host = PartiesHost(**kw)
    pg = narrow.page(browser, width)
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    return pg, host


def opened(pg, props="{}"):
    """The place opened over the pane (part E wires the tabs' + and a party's … Edit to it; here the page is asked directly)."""
    pg.evaluate("() => import('/static/js/frame/state.js').then((m) => m.openOver('parties', %s, {title: 'Board', key: ''}, 'Parties'))" % props)
    pg.locator(".parties[data-screen]").wait_for(timeout=WAIT_MS)


@pytest.fixture(params=narrow.WIDTHS)
def first(gui, request):
    """The first start at one of the two widths: the project is a game being made, no party yet."""
    errors: list[str] = []
    pg, host = start(gui, request.param, errors, made=False)
    opened(pg)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.fixture(params=narrow.WIDTHS)
def made(gui, request):
    """The place on a project with its four parties (Game design, Tech led by the Architect, Art, Release)."""
    errors: list[str] = []
    pg, host = start(gui, request.param, errors)
    opened(pg, "{party: 'tech'}")
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.fixture(params=narrow.WIDTHS)
def crowded(gui, request):
    """The same on a project with squads that have more cards than a squad holds."""
    errors: list[str] = []
    pg, host = start(gui, request.param, errors, made=False, wide_squads=True)
    opened(pg)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def wide(w):
    return w == "wide"


def row(pg, party):
    return pg.locator(f'.parties__row[data-party="{party}"]')


def ticked(pg, party):
    return row(pg, party).locator('[role="checkbox"]').get_attribute("aria-checked") == "true"


def words(loc):
    """What a thing says, whatever case orkUI draws it in."""
    return " ".join(loc.evaluate("e => { const t = [], w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); while (w.nextNode()) t.push(w.currentNode.textContent); return t.join(' '); }").split())


def title(pg):
    return " ".join(pg.locator(".table-title__pt").text_content().split())


def to_left(pg):
    """The narrow width: the right is a screen, back to the left (the wide window shows both)."""
    if not pg.locator(".parties__left").is_visible():
        pg.get_by_role("button", name="Parties", exact=True).click()


def open_party(pg, party):
    to_left(pg)
    row(pg, party).locator(".parties__open").click()
    pg.locator(f'.parties__party[data-party="{party}"]').wait_for(timeout=WAIT_MS)


def seat(pg, slug):
    return pg.locator(f'.parties__role[data-seat="{slug}"]')


def ticks(pg, band):
    return [s.get_attribute("data-seat") for s in pg.locator(f'.parties__col[data-band="{band}"] .parties__role[data-on="true"]').all()]


def head_of(pg, locator):
    return locator.locator(".ork-race__head").first.get_attribute("src")


def waits_for(pg, host, name, n=1):
    for _ in range(80):
        if len(host.called(name)) >= n:
            return
        pg.wait_for_timeout(50)
    raise AssertionError(f"{name} was not called {n} times: {host.log}")


# -- the first start: the left -------------------------------------------------------------------------------------------------------------------------------------

def test_the_left_has_the_kind_a_field_the_stages_their_parties_and_release_in_every_project(first):
    pg, host, w = first
    assert title(pg) == "Board · Parties"
    kind = pg.locator(".parties__kind")
    assert "Read from the project" in words(kind) and kind.locator("input").input_value() == "a game"          # a field, to correct
    assert [s.get_attribute("data-stage") for s in pg.locator(".parties__stage").all()] == ["idea", "being_made", "live", "every"]
    heads = {s.get_attribute("data-stage"): words(s.locator(".parties__stage-h").first) for s in pg.locator(".parties__stage").all()}
    assert heads == {"idea": "Idea", "being_made": "Being made The project is here", "live": "Live", "every": "In every project"}      # the project is at the stage read
    under = lambda stage: [r.get_attribute("data-party") for r in pg.locator(f'.parties__stage[data-stage="{stage}"] .parties__row').all()]  # noqa: E731
    assert under("idea") == ["game-design", "art"] and under("being_made") == ["tech"] and under("live") == ["liveops", "marketing"] and under("every") == ["release"]
    assert {p: ticked(pg, p) for p in ("game-design", "art", "tech", "liveops", "marketing", "release")} == {"game-design": True, "art": True, "tech": True, "liveops": False, "marketing": False, "release": True}
    release = row(pg, "release")
    assert release.locator('[role="checkbox"]').get_attribute("aria-disabled") == "true" and "the one way into main" in words(release)      # ticked and locked
    release.locator('[role="checkbox"]').click(force=True)
    assert ticked(pg, "release")
    for party, race in (("game-design", "unicorn"), ("art", "dryad"), ("tech", "shaman"), ("liveops", "imp"), ("marketing", "fairy"), ("release", "lich")):
        assert race in head_of(pg, row(pg, party)), party                                                              # the leader's head, its party's race
    assert "Release" in words(release) and "Knight" not in words(pg.locator(".parties__left"))            # no word of a race on the left
    assert pg.get_by_role("button", name="Start", exact=True).is_visible() and "From the next task" not in words(pg.locator(".parties"))
    pg.wait_for_function("() => document.querySelector('[data-total]').innerText.includes('about')", timeout=WAIT_MS)       # the prices come from the host
    total = pg.locator("[data-total]").inner_text()
    assert total.startswith("These parties: about ") and total.endswith("% of Claude's week a goal"), total
    shot(pg, f"parties-first-{w}.png")


def test_a_stage_picked_on_its_heading_is_the_projects_and_the_stages_reached_are_ticked(first):
    pg, host, w = first
    pg.locator('.parties__stage[data-stage="live"] .parties__stage-h').click()
    waits_for(pg, host, "ideas.stage_set")
    assert host.called("ideas.stage_set") == [{"stage": "live"}]
    pg.wait_for_function("() => document.querySelector('.parties__stage[data-stage=\"live\"] .parties__here')", timeout=WAIT_MS)
    assert pg.locator(".parties__here").count() == 1 and pg.locator('.parties__stage[data-stage="being_made"] .parties__here').count() == 0
    assert all(ticked(pg, p) for p in ("game-design", "art", "tech", "liveops", "marketing", "release"))
    pg.locator('.parties__stage[data-stage="idea"] .parties__stage-h').click()
    pg.wait_for_function("() => document.querySelector('.parties__stage[data-stage=\"idea\"] .parties__here')", timeout=WAIT_MS)
    assert [p for p in ("game-design", "art", "tech", "liveops", "marketing") if ticked(pg, p)] == ["game-design", "art"]
    row(pg, "tech").locator('[role="checkbox"]').click()                                                                # a party the person ticks stays ticked
    assert ticked(pg, "tech")


def test_start_makes_the_ticked_parties_then_asks_the_project_and_the_place_closes(first):
    pg, host, w = first
    row(pg, "liveops").locator('[role="checkbox"]').click()
    pg.get_by_role("button", name="Start", exact=True).click()
    waits_for(pg, host, "ideas.project_ask")
    saves = host.called("ideas.goal_save")
    assert [a["preset"] for a in saves] == ["game-design", "tech", "art", "release", "liveops"]                           # the ticked parties, in the stages' order
    assert saves[0]["leader"] == "game-designer" and saves[0]["size"] == "lean" and saves[0]["team"] == ["level-designer", "copywriter", "playtester"]
    assert saves[1]["leader"] == "architect" and saves[1]["size"] == "standard"
    assert saves[3]["leader"] == "release-manager" and saves[3]["team"] == [] and saves[3]["size"] == "lean"
    assert host.called("ideas.project_ask") == [{}] and [n for n, _ in host.log].index("ideas.project_ask") > max(i for i, (n, _) in enumerate(host.log) if n == "ideas.goal_save")
    pg.locator(".parties").wait_for(state="detached", timeout=WAIT_MS)


# -- a party opened: the right ---------------------------------------------------------------------------------------------------------------------------------------

def test_at_the_narrow_width_the_left_is_a_screen_and_the_right_the_next(first):
    pg, host, w = first
    if wide(w):
        assert pg.locator(".parties__left").is_visible() and pg.locator(".parties__right").is_visible()
        assert pg.locator('.parties__party[data-party="game-design"]').count() == 1                                      # the first party is open
        return
    assert pg.locator(".parties__left").is_visible() and not pg.locator(".parties__right").is_visible()
    open_party(pg, "tech")
    assert pg.locator(".parties__right").is_visible() and not pg.locator(".parties__left").is_visible()
    shot(pg, f"parties-tech-{w}.png")
    pg.get_by_role("button", name="Parties", exact=True).click()
    pg.locator(".parties__left").wait_for(state="visible", timeout=WAIT_MS)


def test_a_party_opened_has_the_size_with_its_lines_and_prices_the_leaders_row_and_the_two_columns(first):
    pg, host, w = first
    open_party(pg, "tech")
    sizes = pg.locator(".parties__size")
    pg.wait_for_function("() => document.querySelectorAll('.parties__size .ork-gem').length === 3", timeout=WAIT_MS)
    assert [s.get_attribute("data-size") for s in sizes.all()] == ["lean", "standard", "full"] and sizes.nth(1).get_attribute("aria-checked") == "true"       # Tech is proposed Standard
    text = [words(s) for s in sizes.all()]
    assert text[0].startswith("Lean plan → do, one at once") and text[1].startswith("Standard plan → do → one check, two at once") and text[2].startswith("Full plan → do → every check it concerns, three at once")
    assert [s.locator(".ork-gem").get_attribute("data-cost") for s in sizes.all()] == ["1–3%", "2–6%", "4–10%"] and all(t.endswith("a goal") for t in text)       # its price a goal, in the tool's week
    assert {a["size"] for a in host.called("ideas.party_price") if a["leader"] == "architect"} >= {"lean", "standard", "full"}
    lead = pg.locator(".parties__lead")
    said = words(lead)
    assert said.startswith("Sh.man · Architect") and "Map: System, the code's containers and their links" in said and said.endswith("Claude Code · Veteran"), said      # §164: its name beside its role
    assert "shaman-elder" in head_of(pg, lead) and "harness-claude-ink" in lead.locator(".ork-mark").get_attribute("src")                               # its race's higher form; its tool's mark in ink
    assert [c.get_attribute("data-band") for c in pg.locator(".parties__col").all()] == ["build", "check"]
    assert pg.locator('.parties__col[data-band="build"] .ork-sign.sword').count() == 1 and pg.locator('.parties__col[data-band="check"] .ork-sign.shield').count() == 1
    assert ticks(pg, "build") == ["grunt", "tester"] and ticks(pg, "check") == ["reviewer"]                                                           # the squad ticked
    shot(pg, f"parties-open-{w}.png")
    assert pg.locator('.parties__col[data-band="check"] .parties__role').count() == 2                                                                # security reviewer: a card, not ticked
    g = seat(pg, "grunt")
    assert "peon-warrior" in head_of(pg, g) and "harness-claude-ink" in g.locator(".ork-mark").get_attribute("src") and "Grunt" in words(g)      # head with the gear of its tier, role, tool mark
    open_party(pg, "game-design")
    assert "Dungeon Master Knight · Game designer" in words(pg.locator(".parties__lead")) and "Map:" not in words(pg.locator(".parties__lead"))
    open_party(pg, "release")
    assert pg.locator('.parties__size[data-size="standard"]').is_disabled() and pg.locator('.parties__size[data-size="lean"]').get_attribute("aria-checked") == "true"       # Release works lean
    assert "Release Night King · Release manager" in words(pg.locator(".parties__lead"))


def test_the_size_changes_the_checks_column_lean_dims_it_and_each_size_says_what_checks(first):
    pg, host, w = first
    open_party(pg, "tech")
    checks = pg.locator('.parties__col[data-band="check"]')
    hint = lambda: words(checks.locator(".parties__hint"))  # noqa: E731
    assert "is-dim" not in checks.get_attribute("class") and hint() == "One checker checks each task"
    pg.locator('.parties__size[data-size="full"]').click()
    assert hint() == "Every checker a task concerns" and pg.locator('.parties__party[data-party="tech"]').get_attribute("data-size") == "full"
    assert "shaman-elder" in head_of(pg, pg.locator(".parties__lead")) and "elder" in head_of(pg, seat(pg, "reviewer"))                                    # the tiers follow the size
    pg.locator('.parties__size[data-size="lean"]').click()
    assert "is-dim" in checks.get_attribute("class") and hint() == "No separate check: the doer runs its own tests"
    assert "shaman-warrior" in head_of(pg, pg.locator(".parties__lead"))
    assert int(checks.evaluate("e => getComputedStyle(e.querySelector('.parties__role')).opacity * 100")) < 100                                              # dimmed
    shot(pg, f"parties-lean-{w}.png")
    pg.locator('.parties__size[data-size="standard"]').click()
    assert hint() == "One checker checks each task" and "is-dim" not in checks.get_attribute("class")


def test_a_squad_has_at_most_five_who_do_and_two_who_check(crowded):
    pg, host, w = crowded
    open_party(pg, "art")
    assert ticks(pg, "build") == ["artist", "sound-designer"] and pg.locator('.parties__col[data-band="build"] .parties__role').count() == 6
    for slug in ("animator", "composer", "icon-artist"):
        seat(pg, slug).locator('[role="checkbox"]').click()
    assert len(ticks(pg, "build")) == 5 and seat(pg, "ui-kit").locator('[role="checkbox"]').is_disabled()                                              # the sixth cannot be ticked
    seat(pg, "composer").locator('[role="checkbox"]').click()
    assert not seat(pg, "ui-kit").locator('[role="checkbox"]').is_disabled()
    open_party(pg, "tech")
    seat(pg, "security-reviewer").locator('[role="checkbox"]').click()
    assert ticks(pg, "check") == ["reviewer", "security-reviewer"] and seat(pg, "art-reviewer").locator('[role="checkbox"]').is_disabled()
    pg.get_by_role("button", name="Start", exact=True).click()                                                                                          # what was ticked is what is made
    waits_for(pg, host, "ideas.project_ask")
    art = next(a for a in host.called("ideas.goal_save") if a["preset"] == "art")
    assert sorted(art["team"]) == ["animator", "art-reviewer", "artist", "icon-artist", "sound-designer"] and len(art["team"]) <= 7


def test_a_card_pressed_ticks_it_where_the_party_is_not_made_yet(first):
    pg, host, w = first
    open_party(pg, "tech")
    seat(pg, "security-reviewer").locator(".parties__seat").click()
    assert ticks(pg, "check") == ["reviewer", "security-reviewer"] and pg.locator(".table-seatpop").count() == 0


# -- a party that is made ------------------------------------------------------------------------------------------------------------------------------------------

def test_a_made_party_is_saved_with_only_what_changed_and_a_seat_pressed_opens_its_popover(made):
    pg, host, w = made
    assert pg.locator(".parties").get_attribute("data-first") == "false" and pg.locator(".parties__party[data-party='tech']").count() == 1      # opened at the right, as asked
    assert ticked(pg, "tech") and row(pg, "tech").locator('[role="checkbox"]').get_attribute("aria-disabled") == "true"                          # made: ticked for good
    assert not ticked(pg, "liveops")
    save = pg.get_by_role("button", name="Save", exact=True)
    assert save.is_disabled() and "From the next task" in words(pg.locator(".parties__foot")) and pg.get_by_role("button", name="Start", exact=True).count() == 0
    seat(pg, "tester").locator(".parties__seat").click()
    pop = pg.locator(".table-seatpop")
    pop.wait_for(timeout=WAIT_MS)
    assert "Tester" in words(pop) and "Take off the seat" in words(pop)
    shot(pg, f"parties-made-popover-{w}.png")
    pg.keyboard.press("Escape")
    pg.locator(".table-seatpop").wait_for(state="detached", timeout=WAIT_MS)
    pg.locator(".parties__lead").click()                                                                              # the leader's row opens its own
    pg.locator('.table-seatpop[data-seat="architect"]').wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    seat(pg, "reviewer").locator('[role="checkbox"]').click()
    seat(pg, "security-reviewer").locator('[role="checkbox"]').click()
    assert ticks(pg, "check") == ["security-reviewer"]
    assert save.is_enabled()
    save.click()
    waits_for(pg, host, "ideas.goal_save")
    assert host.called("ideas.goal_save") == [{"slug": "tech", "leader": "architect", "team": ["grunt", "tester", "security-reviewer"], "every": []}]       # nothing else: not the size, not another party
    assert host.called("ideas.project_ask") == []                                                                   # asked at the first start only
    pg.locator(".parties").wait_for(state="detached", timeout=WAIT_MS)


def test_a_made_partys_size_is_saved_and_a_party_ticked_later_is_made(made):
    pg, host, w = made
    pg.locator('.parties__size[data-size="full"]').click()
    to_left(pg)
    row(pg, "marketing").locator('[role="checkbox"]').click()
    pg.get_by_role("button", name="Save", exact=True).click()
    waits_for(pg, host, "ideas.goal_save", 2)
    saves = host.called("ideas.goal_save")
    assert {"slug": "tech", "size": "full"} in saves and any(a.get("preset") == "marketing" and "slug" not in a for a in saves)


def test_what_the_leader_keeps_of_the_project_is_read_where_the_host_has_it(gui):
    errors: list[str] = []
    pg, host = start(gui, "wide", errors, facts=True)
    opened(pg, "{party: 'tech'}")
    facts = pg.locator("[data-facts]")
    facts.wait_for(timeout=WAIT_MS)
    text = words(facts)
    assert "Friends on a couch" in text and "Online ranking" in text and "From the next goal" in text and "you said" in text and "read from the project" in text
    assert host.called("ideas.project_facts")[0] == {"party": "tech"}
    open_party(pg, "art")
    pg.wait_for_function("() => document.querySelectorAll('[data-facts]').length === 0", timeout=WAIT_MS)             # another party keeps none
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_place_without_facts_draws_none(made):
    pg, host, w = made
    pg.wait_for_timeout(200)
    assert pg.locator("[data-facts]").count() == 0
