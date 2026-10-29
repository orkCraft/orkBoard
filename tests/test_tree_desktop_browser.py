"""Spec 102 part H, Product's map: the opportunity solution tree (docs/specs/102-the-other-maps-and-picking-on-them.md §8.4; decisions §172, §175.1; mockup docs/mockups/s3/ state 2), at both widths
(`tests/narrow.py`: 1280 × 800, and 390 × 844 with touch), against a stub host of its own (the table's `TableHost` with a party of the craft `product`, and the commands the tree reads: `ideas.tree`,
`ideas.tree_set`, `ideas.tree_attach`, `ideas.tree_propose`, `ideas.add`).

The outcome as a banner with **Edit**; the jobs as columns under it (stacked at 390), each its sentence with the three keywords muted and its segment; the goals that serve a job as the Board's goal cards (element,
name in the body face, the type's two-tone sign, its place), an experiment under its goal; a job no goal serves says so, with a green **+**. A press on a goal picks it (frame/state.js `pick`). **Edit** keeps a job
or the outcome through `ideas.tree_set` and a refusal is said in its own words. **+** opens the field addressed to Product with the job noted as a mark, sent with `ideas.add`. **Propose** when nothing is kept.
Every job and goal wrapped in `Pickable` (map `product`). No sideways scroll. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost, node, shot, tab, watch  # noqa: E402

pytestmark = pytest.mark.browser

OUTCOME = {"id": "lobby", "text": "Of 10 players in a lobby, 6 reach a round — we want 8"}
JOBS = [
    {"id": "get-everyone-in", "when": "I start a game night", "want": "get everyone into the lobby fast", "so": "begin before people drift off", "segment": "Hosts", "by": "leader", "at": "2026-10-29T08:00:00"},
    {"id": "play-again", "when": "a round ends", "want": "play again with the same group", "so": "keep the night going", "segment": "Hosts", "by": "leader", "at": "2026-10-29T08:00:00"},
    {"id": "jump-in", "when": "I join late", "want": "see where the round is", "so": "jump in without asking", "segment": "Players", "by": "person", "at": "2026-10-29T08:00:00"},
    {"id": "answer-calmly", "when": "a prompt appears", "want": "have time to read and answer", "so": "play without rushing", "segment": "Players", "by": "leader", "at": "2026-10-29T08:00:00"},
]
GOALS = {"room-code": ("Room code on every phone", "meadow", "feature", "work"), "seat-kept": ("Seat kept after a reconnect", "ice", "feature", "done"),
         "late-catch": ("Late players catch up", "dust", "feature", "line"), "round-timer": ("Round timer on every phone", "meadow", "feature", "work"),
         "try-20": ("Try 20 seconds to answer", "ice", "abtest", "line")}
SERVES = [("get-everyone-in", "room-code"), ("jump-in", "seat-kept"), ("jump-in", "late-catch"), ("answer-calmly", "round-timer")]
TESTS = [("round-timer", "try-20")]
PARTY = "game"                                                                                       # the stub's first party, here Product


class Refused(Exception):
    """A command the host refuses in plain words."""


class TreeHost(TableHost):
    def __init__(self, kept: bool = True):
        super().__init__(rich=False)
        for p in self.parties:
            p["party_craft"] = "tech" if p["slug"] == "tech" else None
        product = self.parties[0]
        product["title"] = product["short"] = "Product"
        product["party_craft"] = "product"
        for slug, (title, element, sign, place) in GOALS.items():
            self.nodes.append(node(slug, PARTY, title, "done" if place == "done" else "working" if place == "work" else "ready", element=element, sign=sign, place="deck" if place == "line" else "table"))
        self.outcomes = [dict(OUTCOME)] if kept else []
        self.jobs = copy.deepcopy(JOBS) if kept else []
        self.serves = [{"job": j, "goal": g} for j, g in SERVES] if kept else []
        self.tests = [{"goal": g, "experiment": e} for g, e in TESTS] if kept else []
        self.proposal = {"asked": True}
        self.refuse = ""

    def _row(self, slug):
        title, element, _, place = GOALS[slug]
        return {"title": title, "element": element, "place": place}

    def tree(self):
        return {"outcomes": copy.deepcopy(self.outcomes), "jobs": copy.deepcopy(self.jobs), "serves": [{**s, **self._row(s["goal"])} for s in self.serves],
                "tests": [{**t, **self._row(t["experiment"])} for t in self.tests], "proposing": False, "status": "", "party": PARTY}

    def handle(self, name, a):
        if name == "ideas.tree":
            self.log.append((name, a))
            return self.tree()
        if name == "ideas.tree_set":
            self.log.append((name, a))
            if self.refuse:
                raise Refused(self.refuse)
            if a.get("outcomes") is not None:
                self.outcomes = [{"id": o.get("id") or f"o{i}", "text": o["text"]} for i, o in enumerate(a["outcomes"])]
            if a.get("jobs") is not None:
                self.jobs = [{**j, "by": "person", "at": "2026-10-29T09:00:00"} for j in a["jobs"]]
            self.rev += 1
            return {"ok": True, "outcomes": self.outcomes, "jobs": self.jobs, "serves": []}
        if name == "ideas.tree_attach":
            self.log.append((name, a))
            self.serves = [s for s in self.serves if s["goal"] != a["goal"]] + ([{"job": a["job"], "goal": a["goal"]}] if a.get("job") else [])
            self.rev += 1
            return {"ok": True, "serves": self.tree()["serves"]}
        if name == "ideas.tree_propose":
            self.log.append((name, a))
            if self.proposal.get("asked"):
                self.outcomes, self.jobs = [dict(OUTCOME)], copy.deepcopy(JOBS)
                self.rev += 1
            return {"ok": True, **self.proposal}
        if name == "ideas.add":
            self.log.append((name, a))
            return {"slug": "new-goal", "queue": "now", "element": "meadow", "route": [a.get("party") or "tech"]}
        return super().handle(name, a)

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            try:
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}))
            except Refused as e:
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": False, "error": str(e)}))
        ws.on_message(on_message)


def open_tree(gui, request_param, host):
    errors: list[str] = []
    server, browser = gui
    pg = narrow.page(browser, request_param)
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    return pg, errors


@pytest.fixture(params=narrow.WIDTHS)
def tree(gui, request):
    """The window at one of the two widths on Product's tab against a TreeHost with a tree kept: `(page, host, width)`; the page's errors are asserted at the end."""
    host = TreeHost()
    pg, errors = open_tree(gui, request.param, host)
    go(pg)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.fixture(params=narrow.WIDTHS)
def bare(gui, request):
    """The same with nothing kept."""
    host = TreeHost(kept=False)
    pg, errors = open_tree(gui, request.param, host)
    go(pg, ".mp-propose")
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def go(pg, ready=".tr-col"):
    tab(pg, PARTY).click()
    pg.locator(f'.table-tab[data-tab="{PARTY}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
    pg.locator(ready).first.wait_for(timeout=WAIT_MS)


def wide(w):
    return w == "wide"


def job(pg, jid):
    return pg.locator(f'.tr-job[data-job="{jid}"]')


def col(pg, jid):
    return pg.locator(f'.tr-col[data-job="{jid}"]')


def goal(pg, gid):
    return pg.locator(f'.tr-goal[data-id="{gid}"]')


def sent(host, name):
    return [a for n, a in host.log if n == name]


# -- the tree ------------------------------------------------------------------------------------------------------------------------------------------

def test_the_tree_is_the_outcome_as_a_banner_and_the_jobs_as_columns_that_stack_at_the_narrow_width(tree):
    pg, host, w = tree
    banner = pg.locator(".tr-banner")
    assert banner.locator(".ork-label").inner_text().lower() == "outcome" and banner.locator(".tr-banner__t").inner_text() == OUTCOME["text"]
    assert banner.get_by_role("button", name="Edit the outcome").inner_text() == "Edit"
    assert pg.locator(".tr-col").count() == 4 and pg.locator(".tr-job").count() == 4
    first = job(pg, "get-everyone-in")
    assert first.locator(".tr-segment").inner_text().strip().lower() == "hosts"
    assert " ".join(first.locator(".tr-job__s").inner_text().split()) == "When I start a game night, I want to get everyone into the lobby fast, so I can begin before people drift off."
    keys = first.locator(".tr-k")
    assert keys.all_text_contents() == ["When", "I want to", "so I can"]
    ink, muted = (first.locator(".tr-job__s").evaluate("e => getComputedStyle(e).color"), keys.first.evaluate("e => getComputedStyle(e).color"))
    assert ink != muted, "the three keywords are muted"
    boxes = [col(pg, j["id"]).bounding_box() for j in JOBS]
    banner_box = banner.bounding_box()
    if wide(w):
        assert len({round(b["y"]) for b in boxes}) == 1 and all(boxes[i]["x"] < boxes[i + 1]["x"] for i in range(3)), "side by side, one row"
        assert boxes[0]["y"] > banner_box["y"] + banner_box["height"], "under the banner"
        assert pg.locator(".tr-stub").count() == 1
    else:
        assert len({round(b["x"]) for b in boxes}) == 1 and all(boxes[i]["y"] < boxes[i + 1]["y"] for i in range(3)), "stacked"
        assert all(b["width"] > 300 for b in boxes), "each as wide as the screen allows"
        assert pg.locator(".tr-stub").evaluate("e => getComputedStyle(e).display") == "none"
    shot(pg, f"tree-{w}.png")


def test_a_goal_that_serves_a_job_is_the_boards_card_its_element_name_sign_and_place_and_an_experiment_lies_under_its_goal(tree):
    pg, host, w = tree
    g = goal(pg, "room-code")
    assert col(pg, "get-everyone-in").locator(".tr-goal").count() == 1 and col(pg, "jump-in").locator(".tr-goal").count() == 2
    assert g.locator(".ork-elem.meadow").count() == 1 and g.locator(".mp-card__nm").inner_text().strip() == "Room code on every phone"
    assert "pixel" not in g.locator(".mp-card__nm").evaluate("e => getComputedStyle(e).fontFamily").lower(), "a goal's words are in the body face"
    assert g.locator(".mp-win .ork-sign.big.feature").count() == 1 and g.locator(".tr-place").text_content().strip() == "At work"
    assert [goal(pg, s).locator(".tr-place").text_content().strip() for s in ("seat-kept", "late-catch")] == ["Done", "In line"]
    assert g.locator(".tr-place .ork-sign.work").count() == 1 and goal(pg, "seat-kept").locator(".tr-place .ork-sign.check").count() == 1 and goal(pg, "late-catch").locator(".tr-place .ork-sign.before").count() == 1
    test = col(pg, "answer-calmly").locator(".tr-tests .tr-goal")
    assert test.count() == 1 and test.get_attribute("data-id") == "try-20" and test.locator(".mp-win .ork-sign.big.abtest").count() == 1
    parent, child = goal(pg, "round-timer").bounding_box(), test.bounding_box()
    assert child["y"] > parent["y"] + parent["height"] - 1 and child["x"] > parent["x"], "under its goal, a step in"


def test_a_job_no_goal_serves_says_so_with_a_green_plus_and_the_count_is_said(tree):
    pg, host, w = tree
    empty = col(pg, "play-again")
    assert empty.locator(".tr-goal").count() == 0 and empty.locator(".tr-nogoal .mp-cap").inner_text() == "No goal serves this yet"
    plus = empty.get_by_role("button", name="Write a goal for this job")
    assert plus.count() == 1 and col(pg, "jump-in").get_by_role("button", name="Write a goal for this job").count() == 0
    action = pg.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--ork-action').trim()")
    assert action and plus.evaluate("e => getComputedStyle(e).color") == pg.evaluate("c => { const s = document.createElement('i'); s.style.color = c; document.body.appendChild(s); const r = getComputedStyle(s).color; s.remove(); return r; }", action)
    assert pg.locator(".tr-note").inner_text() == "1 job no goal serves"
    box = plus.bounding_box()
    assert box["width"] >= (44 if not wide(w) else 24) and box["height"] >= (44 if not wide(w) else 24), "a press the finger can find"
    shot(pg, f"tree-empty-job-{w}.png")


def test_a_press_on_a_goal_picks_it_and_again_puts_it_down(tree):
    pg, host, w = tree
    g = goal(pg, "late-catch")
    g.locator(".mp-card__nm").click()
    pg.locator('.tr-goal[data-id="late-catch"][aria-pressed], .tr-goal[data-id="late-catch"].is-lit').wait_for(timeout=WAIT_MS)
    assert g.locator(".mp-card__nm").get_attribute("aria-pressed") == "true" and "is-lit" in g.get_attribute("class")
    assert goal(pg, "room-code").locator(".mp-card__nm").get_attribute("aria-pressed") == "false"
    goal(pg, "room-code").click(position={"x": 12, "y": 40})
    pg.locator('.tr-goal[data-id="room-code"].is-lit').wait_for(timeout=WAIT_MS)
    assert "is-lit" not in g.get_attribute("class"), "one goal is picked at a time"
    goal(pg, "room-code").locator(".mp-card__nm").click()
    pg.wait_for_selector('.tr-goal.is-lit', state="detached", timeout=WAIT_MS)


def test_every_job_and_goal_is_pickable_with_its_map_id_and_name(tree):
    pg, host, w = tree
    pickable = pg.locator('[data-pick-map="product"]')
    assert pickable.count() == 4 + 5
    mine = pg.locator('[data-pick-id="get-everyone-in"]')
    assert mine.get_attribute("data-pick-name") == "get everyone into the lobby fast" and mine.get_attribute("data-pick-map") == "product"
    g = pg.locator('[data-pick-id="round-timer"]')
    assert g.get_attribute("data-pick-name") == "Round timer on every phone" and g.get_attribute("data-pick-group") == "answer-calmly"
    assert pg.locator('[data-pick-id="try-20"]').get_attribute("data-pick-group") == "answer-calmly"


# -- Edit ----------------------------------------------------------------------------------------------------------------------------------------------

def test_edit_keeps_the_job_through_tree_set_with_the_other_jobs_as_they_are(tree):
    pg, host, w = tree
    job(pg, "play-again").get_by_role("button", name="Edit the job: play again with the same group").click()
    form = pg.locator(".tr-form")
    form.wait_for(timeout=WAIT_MS)
    assert form.locator('input[name="segment"]').input_value() == "Hosts" and form.locator('textarea[name="want"]').input_value() == "play again with the same group"
    form.locator('input[name="segment"]').fill("Friends")
    form.locator('textarea[name="want"]').fill("start another round")
    shot(pg, f"tree-edit-{w}.png")
    form.get_by_role("button", name="Save").click()
    pg.wait_for_function("() => [...document.querySelectorAll('.tr-job__s')].some((e) => e.textContent.includes('start another round'))", timeout=WAIT_MS)
    got = sent(host, "ideas.tree_set")
    assert len(got) == 1 and "outcomes" not in got[0] and [j["id"] for j in got[0]["jobs"]] == [j["id"] for j in JOBS]
    assert got[0]["jobs"][1] == {"id": "play-again", "when": "a round ends", "want": "start another round", "so": "keep the night going", "segment": "Friends"}
    assert got[0]["jobs"][0] == {"id": "get-everyone-in", "when": "I start a game night", "want": "get everyone into the lobby fast", "so": "begin before people drift off", "segment": "Hosts"}
    assert pg.locator(".tr-form").count() == 0 and job(pg, "play-again").locator(".tr-segment").inner_text().strip().lower() == "friends"


def test_a_refusal_is_said_in_its_own_words_and_cancel_leaves_the_job(tree):
    pg, host, w = tree
    host.refuse = "Two jobs say the same: play again with the same group"
    job(pg, "get-everyone-in").get_by_role("button", name="Edit the job: get everyone into the lobby fast").click()
    form = pg.locator(".tr-form")
    form.locator('textarea[name="want"]').fill("play again with the same group")
    form.get_by_role("button", name="Save").click()
    alert = form.locator("[role=alert]")
    alert.wait_for(timeout=WAIT_MS)
    assert alert.inner_text() == "Two jobs say the same: play again with the same group" and pg.locator(".tr-form").count() == 1, "the form stays, with what was written"
    form.get_by_role("button", name="Cancel").click()
    assert pg.locator(".tr-form").count() == 0 and "get everyone into the lobby fast" in job(pg, "get-everyone-in").inner_text()


def test_edit_on_the_outcome_keeps_it_through_tree_set_and_a_second_may_be_added(tree):
    pg, host, w = tree
    pg.get_by_role("button", name="Edit the outcome").click()
    form = pg.locator(".tr-banner.is-editing")
    form.locator('textarea[name="outcome-0"]').fill("Of 10 players in a lobby, 7 reach a round")
    form.get_by_role("button", name="Add a second outcome").click()
    form.locator('textarea[name="outcome-1"]').fill("Hosts start a second round in 8 of 10 nights")
    shot(pg, f"tree-edit-outcome-{w}.png")
    form.get_by_role("button", name="Save").click()
    pg.wait_for_function("() => document.querySelectorAll('.tr-banner__t').length === 2", timeout=WAIT_MS)
    got = sent(host, "ideas.tree_set")
    assert got == [{"outcomes": [{"id": "lobby", "text": "Of 10 players in a lobby, 7 reach a round"}, {"text": "Hosts start a second round in 8 of 10 nights"}]}]
    assert pg.locator(".tr-banner .ork-label").inner_text().lower() == "outcomes"
    assert pg.locator(".tr-banner__t").all_text_contents() == ["Of 10 players in a lobby, 7 reach a round", "Hosts start a second round in 8 of 10 nights"]


# -- + ---------------------------------------------------------------------------------------------------------------------------------------------------

def test_plus_on_an_empty_job_opens_the_field_addressed_to_product_with_the_job_noted_and_sends_it_with_the_goal(tree):
    pg, host, w = tree
    col(pg, "play-again").get_by_role("button", name="Write a goal for this job").click()
    field = pg.locator(".hand-field")
    field.wait_for(timeout=WAIT_MS)
    assert field.locator(".hand-chip[data-by=tab]").inner_text().strip() == "Product", "addressed to Product"
    chip = field.locator(".pick-chip")
    assert chip.count() == 1 and chip.get_attribute("data-mark") == "play-again" and chip.inner_text().strip() == "play again with the same group"
    assert "ork-picked" in job(pg, "play-again").get_attribute("class"), "Product's map is in picking: the job is marked"
    shot(pg, f"tree-plus-{w}.png")
    pg.locator(".hand-field__text").fill("Play again in one press")
    pg.locator(".hand-field__text").press("Enter")
    pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
    got = sent(host, "ideas.add")
    assert got == [{"text": "Play again in one press", "party": PARTY, "marks": [{"map": "product", "id": "play-again", "name": "play again with the same group"}]}]


def test_plus_puts_the_address_back_when_the_person_had_taken_it_off(tree):
    pg, host, w = tree
    pg.locator(".hand .hand-plus").click()
    pg.locator(".hand-field").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Take off Product").click()
    assert pg.locator(".hand-chip[data-by=tab]").count() == 0
    col(pg, "play-again").get_by_role("button", name="Write a goal for this job").click()
    pg.locator(".hand-chip[data-by=tab]").wait_for(timeout=WAIT_MS)
    assert pg.locator(".pick-chip").count() == 1


# -- Propose ---------------------------------------------------------------------------------------------------------------------------------------------

def test_with_nothing_kept_the_map_says_so_and_propose_asks_product_once_and_the_tree_appears(bare):
    pg, host, w = bare
    assert pg.locator(".mp-nothing").inner_text().startswith("Nothing to read yet: the outcome and the users' jobs") and pg.locator(".tr-col").count() == 0
    button = pg.get_by_role("button", name="Propose")
    assert button.is_enabled() and "Product reads" in pg.locator(".mp-propose .mp-cap").inner_text()
    shot(pg, f"tree-propose-{w}.png")
    button.click()
    pg.locator(".tr-col").first.wait_for(timeout=WAIT_MS)
    assert len(sent(host, "ideas.tree_propose")) == 1 and pg.locator(".tr-col").count() == 4 and pg.locator(".mp-propose").count() == 0


def test_a_proposal_that_cannot_be_asked_is_said_with_its_why(bare):
    pg, host, w = bare
    host.proposal = {"asked": False, "why": "The limits are spent: it can be asked after they reset"}
    pg.get_by_role("button", name="Propose").click()
    alert = pg.locator(".mp-propose [role=alert]")
    alert.wait_for(timeout=WAIT_MS)
    assert alert.inner_text() == "The limits are spent: it can be asked after they reset" and pg.locator(".tr-col").count() == 0


def test_more_than_five_jobs_lie_in_two_rows_each_with_its_lines(gui):
    host = TreeHost()
    host.jobs += [{"id": f"extra-{i}", "when": f"w{i}", "want": f"do {i}", "so": f"so {i}", "segment": "Hosts", "by": "person", "at": "x"} for i in range(3)]
    pg, errors = open_tree(gui, "wide", host)
    go(pg)
    assert pg.locator(".tr-tier").count() == 2 and pg.locator(".tr-stub").count() == 2
    rows = [[c.bounding_box()["y"] for c in t.locator(".tr-col").all()] for t in pg.locator(".tr-tier").all()]
    assert [len(r) for r in rows] == [4, 3] and all(len(set(round(y) for y in r)) == 1 for r in rows) and rows[0][0] < rows[1][0]
    narrow.no_sideways(pg)
    shot(pg, "tree-seven-wide.png")
    pg.context.close()
    assert not errors, "\n".join(errors)
