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
from tests.test_table_desktop_browser import TableHost, node, tab, watch  # noqa: E402

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
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
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













# -- Edit ----------------------------------------------------------------------------------------------------------------------------------------------







# -- + ---------------------------------------------------------------------------------------------------------------------------------------------------





# -- Propose ---------------------------------------------------------------------------------------------------------------------------------------------





