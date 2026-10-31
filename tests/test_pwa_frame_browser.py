"""The installed app is the desktop's page in a frame (docs/specs/117-the-phone-a-menu-of-the-leaders.md §2, part A; docs/specs/94-one-page-fitted-to-the-width.md §4), in a real
browser at 390 × 844 with touch: `/app/` (gui/pwa.py `serve`, the phone listener's own files, put in front of the browser the way the listener would serve them, CSP header
and all; the listener over TLS is tests/test_phones.py's and test_pwa.py's) loads orkUI, the page and the import map of `page/vendor/` under the strict CSP, `pwa/frame.js`
pairs (`pairWith`) and imports the page, which speaks the phone's protocol to a stand-in socket (`route_web_socket`, as tests/test_link_paired_browser.py) over the stub host
of the hand. An unpaired app says so and opens no socket; a code in the address pairs (`/api/version`, `/api/pair`); the page draws the phone's upright hand from the
snapshot and an answer goes as a command; a notification's arrival is logged and picks the goal it names; the worker installs every file it lists and, with the computer
away, opens the app from its cache on the kept snapshot with *As of …*; a phone forgotten on the computer says so and keeps nothing."""
from __future__ import annotations

import json
import re
from urllib.parse import urlsplit

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.gui import pwa  # noqa: E402
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, need, node  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

DEVICE = {"id": "dev-1", "token": "tok-" + "p" * 36, "name": "Test phone"}
WHY = "A new player meets it before the lobby, so it decides what the lobby needs from them."
QUESTION = "Which sign-in first?"
BLANK = "<!doctype html><html><head><meta charset='utf-8'></head><body></body></html>"
RECORD = """() => { window.__sockets = []; const W = window.WebSocket;
  window.WebSocket = function (url, protocols) { window.__sockets.push({ url, protocols }); return new W(url, protocols); };
  window.WebSocket.prototype = W.prototype; Object.assign(window.WebSocket, { OPEN: 1, CONNECTING: 0, CLOSING: 2, CLOSED: 3 }); }"""


class Host(HandHost):
    """A project of four parties whose Tech goal *Sign-in* asks a card question (`HandHost`'s Board, the hand's one entry), over the phone's protocol."""

    def __init__(self):
        super().__init__(bare=True)
        asked = [{"ask": QUESTION, "choices": ["Email link", "Passkey", "Google"], "pick": 0, "why": WHY, "by": None, "look": False}]
        signin = node("signin", "tech", "Sign-in", "hand", state="talk", element="dust", asked=asked, type={"sign": "feature", "name": "Feature"})
        question = {"id": "q1", "by": "tech", "leader": "Tech lead", "q": QUESTION, "choices": ["Email link", "Passkey", "Google"], "pick": 0, "why": WHY, "project": False}
        self.nodes = [n for n in self.nodes if n["place"] != "hand"] + [signin]
        self.needs = [need("talk", "tech", "signin", signin["title"], QUESTION, at="2026-10-20T09:30:00", round=1, stances=[], questions=[question], blocks=True)]
        self.dead = False                       # every socket is closed as it opens: the computer is away

    def snapshot(self):
        doc = super().snapshot()
        doc["state"]["projects"] = {"current": "/p/party-game", "open": [{"path": "/p/party-game", "name": "Party game", "needs_you": 0, "working": 0}], "recent": []}
        return doc

    def on_socket(self, ws):
        if self.dead:
            ws._loop.create_task(ws._impl_obj.close())      # a sync `ws.close()` here waits on the dispatcher itself (as tests/test_link_paired_browser.py)
            return
        super().on_socket(ws)


class App:
    """A browser context at the phone's width whose `/app/` and `/ds/orkui/` are the phone listener's files, its pairing answered, its socket the stub's."""

    def __init__(self, browser, origin, host=None):
        self.host, self.origin, self.errors = host or Host(), origin, []
        self.served: list[str] = []             # every path asked of the app's files (the page's, the worker's)
        self.away = False                       # the app's files are not reachable: the worker's cache answers
        self.paired: list[dict] = []            # what /api/pair got
        self.checked: list[str] = []            # …and the Authorization /api/version got first
        self.ctx = browser.new_context(**narrow.NARROW)
        self.ctx.route("**/app/**", self.files)
        self.ctx.route("**/ds/orkui/**", self.files)
        self.ctx.route("**/api/version", self.version)
        self.ctx.route("**/api/pair", self.pair)
        self.ctx.route("**/blank", lambda r: r.fulfill(status=200, content_type="text/html", body=BLANK))
        self.pg = self.ctx.new_page()
        self.pg.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))
        self.pg.on("console", lambda m: m.type == "error" and self.errors.append(f"console: {m.text} {m.location.get('url', '')}"))
        self.pg.route_web_socket("**/ws*", self.host.on_socket)
        self.pg.add_init_script(f"({RECORD})()")

    def files(self, route):
        """The listener's answer for `pwa.serve`: its status, its headers (the CSP among them) and its body."""
        url = urlsplit(route.request.url)
        if self.away:
            route.abort("connectionrefused")
            return
        self.served.append(url.path)
        head, _, body = pwa.serve("GET", url.path + (f"?{url.query}" if url.query else "")).partition(b"\r\n\r\n")
        lines = head.decode("ascii").split("\r\n")
        headers = dict(line.split(": ", 1) for line in lines[1:])
        route.fulfill(status=int(lines[0].split()[1]), body=body, headers={k: v for k, v in headers.items() if k not in ("Content-Length", "Connection")})

    def version(self, route):
        self.checked.append(route.request.headers.get("authorization"))
        route.fulfill(status=200, content_type="application/json", body=json.dumps({"name": "orkboard", "api": 1}))

    def pair(self, route):
        self.paired.append(json.loads(route.request.post_data))
        route.fulfill(status=200, content_type="application/json", body=json.dumps({"id": DEVICE["id"], "token": DEVICE["token"], "name": DEVICE["name"]}))

    def keep_pairing(self):
        """The phone is paired already: its storage has the device (what the frame wrote when it paired)."""
        self.pg.goto(f"{self.origin}/blank")
        self.pg.evaluate("(d) => { localStorage.clear(); localStorage.setItem('orkcraft.device', JSON.stringify(d)); }", DEVICE)

    def open(self, hash=""):
        self.pg.goto(f"{self.origin}/app/{hash}")
        return self.pg

    def ready(self):
        self.pg.wait_for_selector("[data-frame][data-upright='1']", timeout=WAIT_MS)
        self.pg.get_by_text(QUESTION).first.wait_for(timeout=WAIT_MS)
        return self.pg

    def close(self):
        self.ctx.close()


@pytest.fixture
def app(gui):
    server, browser = gui
    one = App(browser, server.origin)
    yield one
    one.close()


def storage(pg):
    return pg.evaluate("() => [localStorage.getItem('orkcraft.device'), localStorage.getItem('orkcraft.town')]")


def test_paired_the_app_draws_the_pages_upright_hand_under_the_strict_csp_and_answers_as_a_command(app):
    app.keep_pairing()
    pg = app.open()
    app.ready()
    assert pg.evaluate("() => document.documentElement.dataset.look") == "office"
    sock = pg.evaluate("() => window.__sockets")
    assert len(sock) == 1 and sock[0]["url"].startswith("wss://") and sock[0]["url"].endswith("/ws")
    assert sock[0]["protocols"] == ["orkcraft.v1", f"bearer.{DEVICE['token']}"]
    assert pg.evaluate("() => import('./page/js/link.js').then((l) => [l.isPaired(), l.online.value, l.town.value.focus])") == [True, True, "board"]
    # the CSP is the strict one: its only inline script is the import map, by its hash; the page and orkUI came by the app's addresses
    csp = pg.evaluate("() => fetch(location.href).then((r) => r.headers.get('content-security-policy'))")
    assert "script-src 'self' 'sha256-" in csp and "unsafe" not in csp
    assert {"/app/page/board.js", "/app/page/vendor/preact.mjs", "/app/roles.css", "/app/frame.js"} <= set(app.served)
    assert not any(p.startswith("/static/") for p in app.served)
    assert pg.evaluate("() => document.querySelector('#phone').hidden && !document.querySelector('#app').hidden")
    narrow.no_sideways(pg)
    # one tap on a choice answers: the command goes over the phone's socket
    pg.get_by_text("Passkey").first.click()
    assert _calls(pg, app.host, "ideas.talk_answer") == [{"idea": "signin", "answers": [{"id": "q1", "pick": 1}]}]
    assert not app.errors, "\n".join(app.errors)


def test_the_frame_adds_nothing_to_the_pages_window(app):
    """It adds a status line (hidden while the computer answers) and the status bar's inset (none here): the page's frame fills the window as it does without it."""
    app.keep_pairing()
    pg = app.open()
    app.ready()
    win = pg.evaluate("() => [innerWidth, innerHeight]")
    box = pg.evaluate("() => { const r = document.querySelector('[data-frame]').getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }")
    assert box == [0, 0, win[0], win[1]]
    assert pg.locator("#phone-status").is_hidden()


def test_unpaired_the_app_says_so_and_opens_no_socket(app):
    pg = app.open()
    pg.get_by_text("This phone is not paired with the board yet.").wait_for(timeout=WAIT_MS)
    assert pg.evaluate("() => window.__sockets.length") == 0 and pg.evaluate("() => document.querySelector('#app').hidden")
    assert "/app/page/board.js" not in app.served                              # the page is not loaded before there is a pairing
    assert storage(pg) == [None, None] and not app.errors, "\n".join(app.errors)


def test_a_code_in_the_address_pairs_the_phone_and_the_page_opens(app):
    pg = app.open("#pair=code-of-the-qr")
    app.ready()
    assert app.checked == ["Bearer code-of-the-qr"] and app.paired == [{"code": "code-of-the-qr", "name": "Browser"}]
    assert json.loads(storage(pg)[0]) == DEVICE
    assert pg.evaluate("() => window.__sockets[0].protocols[1]") == f"bearer.{DEVICE['token']}"
    assert pg.evaluate("() => location.hash + location.search") == ""            # the code is once: nothing of it stays in the address
    assert not app.errors, "\n".join(app.errors)


def test_a_notification_opens_the_app_logged_and_the_goal_it_names_is_picked(app):
    app.keep_pairing()
    pg = app.open("#needs&from=push-needs&goal=signin")
    app.ready()
    assert [a for a in _calls(pg, app.host, "ideas.log", 2) if a["what"] == "push"] == [{"event": "opened", "what": "push", "ref": "needs", "device": "phone"}]       # once
    pg.wait_for_function("() => import('./page/js/frame/state.js').then((s) => s.picked.value === 'signin')", timeout=WAIT_MS)
    assert pg.evaluate("() => location.hash") == ""
    assert not app.errors, "\n".join(app.errors)


def test_a_phone_forgotten_on_the_computer_says_so_keeps_nothing_and_pairs_again_by_a_new_code(app):
    app.keep_pairing()
    pg = app.open()
    app.ready()
    app.host.ws.close(code=1008, reason="This phone was forgotten")
    pg.get_by_text("The board forgot this phone. Pair it again to use it.").wait_for(timeout=WAIT_MS)
    assert pg.evaluate("() => document.querySelector('#app').hidden") and storage(pg) == [None, None]
    pg.evaluate("() => { location.hash = '#pair=a-new-code'; }")                # a code scanned while the app is open
    pg.wait_for_function("() => !document.querySelector('#app').hidden && document.querySelector('[data-frame]')", timeout=WAIT_MS)
    app.ready()
    assert [p["code"] for p in app.paired] == ["a-new-code"] and json.loads(storage(pg)[0]) == DEVICE
    assert not app.errors, "\n".join(app.errors)


def test_the_worker_keeps_every_file_it_lists_and_with_the_computer_away_the_app_opens_on_the_kept_snapshot(app):
    app.keep_pairing()
    pg = app.open()
    app.ready()
    pg.evaluate("() => navigator.serviceWorker.ready.then(() => true)")
    pg.wait_for_function("async () => (await caches.keys()).includes('orkcraft-app-v104') && (await (await caches.open('orkcraft-app-v104')).keys()).length > 200", timeout=WAIT_MS * 3)
    kept = pg.evaluate("async () => (await (await caches.open('orkcraft-app-v104')).keys()).map((r) => new URL(r.url).pathname)")
    have = set(kept)
    assert {f"/app/{name}" for name in pwa.page_shell()} <= have                 # the page's files, as sw.js was told them
    assert {"/app/", "/app/frame.js", "/app/frame.css", "/app/old.html", "/app/board-app.js"} <= have
    rev = pg.evaluate("() => import('./page/js/link.js').then((l) => l.town.value.rev)")
    pg.wait_for_function("() => navigator.serviceWorker.controller !== null", timeout=WAIT_MS)
    assert not app.errors, "\n".join(app.errors)
    # the computer goes away: its files and its socket both
    app.away, app.host.dead = True, True
    pg.reload()
    pg.wait_for_selector("[data-frame]", timeout=WAIT_MS)                         # opened from the worker's cache
    pg.wait_for_function("() => document.querySelector('#phone-status') && !document.querySelector('#phone-status').hidden", timeout=WAIT_MS)
    line = pg.locator("#phone-status").inner_text()
    assert re.match(r"^As of .+\. (The board went away: trying again…|Cannot reach the board|Connecting…)", line), line
    assert pg.evaluate("() => import('./page/js/link.js').then((l) => [l.town.value.rev, l.stale.value])") == [rev, True]
    pg.wait_for_timeout(1500)                                                      # the page asked the Board's commands: one "Not connected" toast, not one a command
    assert pg.evaluate("() => import('./page/js/link.js').then((l) => l.toasts.value.filter((t) => t.message === 'Not connected to the town').length)") <= 1
    narrow.no_sideways(pg)
    assert not app.errors, "\n".join(app.errors)                                   # every font, head, sign and picture the page drew came from the cache
