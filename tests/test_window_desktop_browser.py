"""Spec 98 part E, the window (docs/specs/98-the-table-and-the-hand.md §7, §8): the table over the hand is the page's only window, at both widths (`tests/narrow.py`), against the table's stub host with stops added
(a failure and a question). No top bar, no left column, no right column and no dialog in the page; every place that was a dialog or the drawer is reached over the pane (Settings, the projects, Files, New party, Edit and Remove the party,
Pair a phone, what used a tool and the week's work, Play, the discard, a stop's questions and to-do); the keyboard (Esc lowers a lifted card, else closes what is over the pane, else picks none; Ctrl+O opens the projects);
a hand card lifted raises its card of the table (`.is-about`). Screenshots to $WINDOW_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_shell_browser import QR  # noqa: E402
from tests.test_hand_desktop_browser import need, node as hand_node, task as hand_task  # noqa: E402
from tests.test_table_desktop_browser import TableHost, open_menu, open_tab, tab, title  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["WINDOW_SHOTS"]) if os.environ.get("WINDOW_SHOTS") else None
GONE = ".shell-top, .shell-main, .shell-drawer, .shell-backdrop, .arena, .arena-left, .arena-hand, .shell-modal, [aria-modal='true'], [role='dialog'][aria-modal='true']"


class WindowHost(TableHost):
    """The table's project with stops in the hand: a failed task of Tech's goal (about its card), a question of the Game design party's goal the Orkmaster reads, a to-do, and a goal done."""

    def __init__(self):
        super().__init__(rich=False)                                                 # no failed check, no pick, no goal in line: the hand's cards are the ones below
        asked = [{"ask": "Where does the timer run?", "choices": ["Server counts, phones show it", "Each phone counts down alone"], "pick": 0, "why": "One clock.", "by": None, "look": False}]
        todo = {"id": "t9", "title": "EXPORT_KEY", "kind": "secret", "why": "The export needs it", "choices": [], "steps": [], "accept": [], "done": False}
        for n in self.nodes:
            if n["slug"] == "timer":
                n["asked"] = asked
        self.nodes.append(hand_node("music", "tech", "Lobby music loop", "discard", state="done", element="void", updated="2026-10-20T12:00:00",
                                    tasks=[hand_task("m1", "Make the loop", "merged", made="Add the lobby loop")]))
        self.needs = [need("failed", "tech", "seat", "Keep the seat when a socket reconnects", "It failed", at="2026-10-20T08:00:00"),
                      need("asks", "game", "timer", "Round timer shows on every phone", "Where does the timer run?", at="2026-10-20T09:30:00", asked=asked),
                      need("todo", "tech", "results", "Results screen with the round's best answer", "EXPORT_KEY", todo=todo, at="2026-10-20T09:10:00")]
        self.gate_doc = {"into": "dev", "main": "main", "same": False, "commits": 3, "files": 4, "ideas": [{"slug": "music", "title": "Lobby music loop", "goal": "tech", "tasks": 1}]}

    def snapshot(self):
        snap = super().snapshot()
        snap["state"]["phones"] = []                                           # the town's paired phones (Pair a phone reads them)
        return snap

    def board(self):
        return {**super().board(), "needs_you": [dict(n) for n in self.needs]}

    def handle(self, name, a):
        if name == "ideas.gate":
            self.log.append((name, a))
            return dict(self.gate_doc)
        if name == "ideas.week_work":
            self.log.append((name, a))
            return {"usd": 46.1, "merged": 12, "first_time": 10, "usd_per_merged": 3.84, "into": "dev"}
        if name == "phones.list":
            self.log.append((name, a))
            return {"phones": [], "listening": True, "address": "https://192.168.1.20:8443", "tail_address": "", "open": [], "pairing": 100, "awake_offer": ""}
        if name == "phones.pair":
            self.log.append((name, a))
            return {"phones": [], "listening": True, "address": "https://192.168.1.20:8443", "tail_address": "", "tail_trusted": False, "tailscale": False, "fingerprint": "AB:CD", "open": [],
                    "pairing": 120, "awake_offer": "", "link": "orkcraft://x", "qr": QR, "code": "123456", "app_link": "https://192.168.1.20:8443/app", "app_qr": QR}
        if name == "phones.tailnet":
            return {"running": True, "installed": True, "phones": [{"name": "Pixel 8", "os": "Android", "online": True}], "install_qr": QR, "dns_qr": QR,
                    "install": "https://tailscale.com/download", "dns": "https://login.tailscale.com/admin/dns", "account": "me@example.com"}
        if name == "phones.pair_stop":
            return {"phones": [], "pairing": 0}
        if name == "ideas.play":
            self.log.append((name, a))
            return {"state": "nothing", "how": "x"}
        if name == "awake.state":
            return {"mode": "carts", "can": True, "battery": False, "why": "", "paired": False}
        return super().handle(name, a)


EDGE = {"x": 10, "y": 24}                                        # a press on a hand card's left edge: a card behind another in its lane shows only that (spec 101 §4.3)


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(450)
        pg.screenshot(path=str(SHOTS / name))


@pytest.fixture(params=narrow.WIDTHS)
def window(gui, request):
    server, browser = gui
    host = WindowHost()
    pg = narrow.page(browser, request.param)
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource") and errors.append(f"console: {m.text}"))
    pg.on("response", lambda r: r.status >= 400 and errors.append(f"{r.status}: {r.url}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    pg.locator(".hand-card").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def over(pg, kind):
    pg.locator(f'.table-over[data-kind="{kind}"]').wait_for(timeout=WAIT_MS)


def back(pg):
    pg.locator(".table-title__back").click()
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)


def nothing_modal(pg):
    assert pg.locator(GONE).count() == 0
    assert pg.locator("dialog").count() == 0


# -- no top bar, no left column, no drawer, no dialog -------------------------------------------------------------------------------------------------

def test_the_page_is_the_table_over_the_hand_and_nothing_else(window):
    pg, host, w = window
    assert pg.locator(".frame-table .table").count() == 1 and pg.locator(".frame-hand .hand").count() == 1
    assert [c.get_attribute("class").split()[0] for c in pg.locator(".shell > *").all()] == ["frame"]                    # the shell holds the frame (and the sign-in page, which draws nothing until it has a tool to sign in)
    nothing_modal(pg)
    assert pg.locator("header.shell-top, .shell-top__chip, .arena-pswitch").count() == 0                                # no top bar: the tabs hold Stop all, the hand the limits
    shot(pg, f"window-board-{w}.png")


def test_a_press_that_opened_a_dialog_opens_a_place_over_the_pane_never_a_dialog(window):
    pg, host, w = window
    open_menu(pg)
    pg.get_by_role("menuitem", name="Settings").click()
    over(pg, "settings")
    nothing_modal(pg)
    assert title(pg) == "Board · Settings" and pg.locator('.place[aria-label="Settings"]').count() == 1
    pg.get_by_role("button", name="Pair a phone").click()                                                               # Pair a phone was a dialog of Settings: a place of its own
    over(pg, "pair")
    assert title(pg).endswith("Pair a phone") and pg.locator(".shell-pair").count() == 1
    nothing_modal(pg)
    pg.get_by_role("button", name="← Settings").click()
    over(pg, "settings")
    pg.get_by_role("button", name="Done", exact=True).click()
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)


def test_every_place_is_reached_over_the_pane(window):
    pg, host, w = window
    # the ▾ after the project's name: the projects (spec 107 §8.2); the Orkmaster's …: Settings, Files
    pg.get_by_role("button", name="Switch project").click()
    over(pg, "projects")
    nothing_modal(pg)
    back(pg)
    for word, kind in (("Settings", "settings"), ("Files", "files")):
        open_menu(pg)
        pg.get_by_role("menuitem", name=word).click()
        over(pg, kind)
        nothing_modal(pg)
        back(pg)
    # + : the one place of the parties; the party's …: Edit (the same place, at that party) and Remove party
    pg.get_by_role("button", name="New party").click()
    over(pg, "parties")
    assert title(pg) == "Board · Parties" and pg.get_by_role("button", name="Save party").count() == 0
    nothing_modal(pg)
    back(pg)
    open_tab(pg, "art")
    pg.get_by_role("button", name="Art's menu").click()
    pg.get_by_role("menuitem", name="Edit").click()
    over(pg, "parties")
    assert title(pg) == "Art · Parties"
    nothing_modal(pg)
    pg.get_by_role("button", name="Back").click()
    pg.locator(".table-head").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Art's menu").click()
    pg.get_by_role("menuitem", name="Remove party").click()
    over(pg, "party")
    pg.locator(".place__text").wait_for(timeout=WAIT_MS)
    nothing_modal(pg)
    pg.keyboard.press("Escape")
    pg.locator(".table-head").wait_for(timeout=WAIT_MS)
    open_tab(pg, "orkmaster")
    # a tool's limits and the week's work; Play
    if w == "wide":
        pg.locator(".hand-pot").first.click()                                                                              # the limits are the hand's potions (spec 104 B)
    else:
        open_menu(pg)
        pg.locator(".table-menu__chips .table-chip").first.click()
    over(pg, "limits")
    pg.get_by_role("button", name="Spend today: $2.40. This week's work").click()
    over(pg, "week")
    nothing_modal(pg)
    pg.get_by_role("button", name="Close").click()
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Play", exact=True).click()
    over(pg, "play")
    nothing_modal(pg)
    back(pg)
    # the hand's: the discard, a stop's questions and its to-do
    pg.locator(".hand-done").click()
    over(pg, "discard")
    shot(pg, f"window-discard-{w}.png")
    nothing_modal(pg)
    back(pg)
    pg.locator('.hand-card[data-kind="asks"]').click(position=EDGE)
    pg.get_by_role("button", name="Open…").click()
    over(pg, "stop")
    pg.locator('[data-form="ask"] textarea').first.wait_for(timeout=WAIT_MS)                                           # the questions are a form in the pane, not a dialog
    nothing_modal(pg)
    back(pg)
    pg.locator('.hand-card[data-kind="todo"]').click(position=EDGE)
    pg.get_by_role("button", name="Open…").click()
    over(pg, "stop")
    pg.locator('.board-todo-dialog[data-kind="secret"]').wait_for(timeout=WAIT_MS)
    nothing_modal(pg)
    back(pg)


def test_the_place_of_the_parties_is_in_the_pane_and_esc_goes_back(window):
    pg, host, w = window
    pg.get_by_role("button", name="New party").click()
    over(pg, "parties")
    nothing_modal(pg)
    assert pg.locator(".place").count() == 0 and pg.locator(".table-over--form").count() == 0
    pg.keyboard.press("Escape")
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)


# -- the keyboard -------------------------------------------------------------------------------------------------------------------------------------

def test_esc_lowers_a_lifted_card_then_closes_what_is_over_the_pane_then_picks_none(window):
    pg, host, w = window
    pg.locator('[data-lkey="t:task:seat/s2"]').click()                                                                  # a card of the table lifted (the front of its goal's cascade), its goal picked from its back
    pg.get_by_role("button", name="Pick this goal").click()
    assert "Keep the seat" in title(pg)
    open_menu(pg)
    pg.get_by_role("menuitem", name="Files").click()                                                                    # …and a place over the pane
    over(pg, "files")
    pg.locator('.hand-card[data-kind="failed"]').click(position=EDGE)                                                                 # …and a card of the hand lifted
    pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")                                                                                         # 1: lowers the lifted card
    pg.locator(".hand-lifted").wait_for(state="detached", timeout=WAIT_MS)
    assert pg.locator('.table-over[data-kind="files"]').count() == 1                                                     # the place is still open
    pg.keyboard.press("Escape")                                                                                         # 2: closes what is over the pane
    pg.locator(".table-over").wait_for(state="detached", timeout=WAIT_MS)
    assert "Keep the seat" in title(pg)                                                                                  # the goal is still picked
    pg.keyboard.press("Escape")                                                                                         # 3: picks none
    pg.wait_for_function("() => document.querySelector('[data-title]').textContent.toLowerCase().startsWith('the whole project')", timeout=WAIT_MS)
    assert title(pg) == "The whole project · through the Orkmaster"
    pg.keyboard.press("Escape")                                                                                         # nothing left: nothing happens
    assert title(pg) == "The whole project · through the Orkmaster"


def test_ctrl_o_opens_the_projects_over_the_pane(window):
    pg, host, w = window
    pg.keyboard.press("Control+o")
    over(pg, "projects")
    assert title(pg) == "Projects" and pg.locator(".table-projects__one").count() == 3
    nothing_modal(pg)
    pg.keyboard.press("Escape")
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)


# -- a card of the hand lifted raises its card of the table -------------------------------------------------------------------------------------------

def test_a_hand_card_lifted_raises_its_card_of_the_table(window):
    pg, host, w = window
    card = pg.locator('[data-lkey="t:task:seat/s2"]')
    assert "idea:seat" in card.get_attribute("data-about") and "task:seat/s2" in card.get_attribute("data-about")        # a task card says what it is about
    assert "idea:timer" in pg.locator('[data-lkey="t:orc:timer"]').get_attribute("data-about")                            # a goal's other card says its goal
    pg.locator('.hand-card[data-kind="failed"]').click(position=EDGE)
    pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => document.querySelector('[data-lkey=\"t:task:seat/s2\"]').classList.contains('is-about')", timeout=WAIT_MS)
    s1 = pg.locator('[data-lkey="t:task:seat/s1"]')                                                                      # a strip of the same goal (its other task; a token has none): not about the failure
    assert not s1.count() or not s1.evaluate("e => e.classList.contains('is-about')")
    shot(pg, f"window-lifted-{w}.png")
    pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.querySelector('[data-lkey=\"t:task:seat/s2\"]').classList.contains('is-about')", timeout=WAIT_MS)
    pg.locator('.hand-card[data-kind="asks"]').click(position=EDGE)                                                                   # a question is about its goal's cards
    pg.wait_for_function("() => document.querySelector('[data-lkey=\"t:orc:timer\"]').classList.contains('is-about')", timeout=WAIT_MS)


def test_tech_with_a_hand_card_lifted(window):
    pg, host, w = window
    open_tab(pg, "tech")
    pg.locator('.hand-card[data-kind="failed"]').click(position=EDGE)
    pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
    shot(pg, f"window-tech-lifted-{w}.png")
