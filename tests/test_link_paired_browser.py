"""One link, two ways (docs/specs/94-one-page-fitted-to-the-width.md §2, part B), in a real browser at the two widths of
`tests/narrow.py`: `js/link.js` paired (`pairWith`, then `connect`) speaks the phone's protocol `orkcraft.v1` to a stand-in
for the phone listener (Playwright's `route_web_socket`; the listener itself is tests/test_phones.py's), whose `state` is the
real `Orkboard.phone_snapshot()` and whose `mobile.hello` says what a phone may send. It reads the page's snapshot (no
onboarding, no repository path), offers only what a phone may do (`can`), keeps the last snapshot greyed with *As of …* when
the computer goes away, keeps an answer given then (`deliver`) and sends it when the computer answers again, and a phone
forgotten on the computer says so."""
from __future__ import annotations

import json
import re

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.gui.board_host import BoardPhone  # noqa: E402
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser

DEVICE = {"id": "dev-1", "token": "tok-phone-1", "name": "Test phone"}
BLANK = """<!doctype html><html data-product="Orkboard"><head><meta charset="utf-8"><script type="importmap">
{"imports": {"preact": "/static/vendor/preact.mjs", "preact/hooks": "/static/vendor/preact-hooks.mjs", "htm": "/static/vendor/htm.mjs",
"@preact/signals-core": "/static/vendor/signals-core.mjs", "@preact/signals": "/static/vendor/preact-signals.mjs"}}
</script></head><body></body></html>"""
RECORD = """() => { window.__sockets = []; const W = window.WebSocket;
  window.WebSocket = function (url, protocols) { window.__sockets.push({ url, protocols }); return new W(url, protocols); };
  window.WebSocket.prototype = W.prototype; Object.assign(window.WebSocket, { OPEN: 1, CONNECTING: 0, CLOSING: 2, CLOSED: 3 }); }"""
START = """async (device) => {
  const link = await import('/static/js/link.js');
  window.L = link;
  link.pairWith(device);
  link.connect();
}"""


class Phone:
    """The phone listener's stand-in: the snapshot a phone gets, `mobile.hello`, and the commands it is sent, answered ok."""

    def __init__(self, host):
        self.host = host
        self.mode = "ok"                     # "dead": every socket is closed as it opens
        self.got: list[tuple[str, dict]] = []
        self.refuse: dict[str, str] = {}
        self.ws = None

    def snapshot(self) -> dict:
        return BoardPhone.phone_snapshot(self.host)

    def on_socket(self, ws):
        if self.mode == "dead":
            ws.close()
            return
        self.ws = ws
        ws.send(json.dumps({"t": "state", "state": self.snapshot()}))

        def on_message(raw):
            m = json.loads(raw)
            if m["name"] == "mobile.hello":
                said = [c for c in sorted(self.host.commands) if BoardPhone.allowed(self.host, c, {"path": "x.md"})]
                result = {"name": "orkcraft", "api": 1, "commands": said}
            else:
                self.got.append((m["name"], m["args"]))
                if m["name"] in self.refuse:
                    ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": False, "error": self.refuse[m["name"]]}))
                    return
                result = {"echo": m["name"]}
            ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": result}))
        ws.on_message(on_message)


@pytest.fixture(params=narrow.WIDTHS)
def paired(gui, request):
    """A blank page of the window's origin at one width, paired with a `Phone`: `(page, phone)`."""
    server, browser = gui
    phone = Phone(server.host)
    errors: list[str] = []
    pg = narrow.page(browser, request.param)
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.route("**/blank", lambda route: route.fulfill(status=200, content_type="text/html", body=BLANK))
    pg.route_web_socket("**/ws*", phone.on_socket)
    pg.add_init_script(f"({RECORD})()")
    pg.goto(f"{server.origin}/blank")
    pg.evaluate("() => localStorage.clear()")
    yield pg, phone
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def start(pg):
    pg.evaluate(START, DEVICE)
    pg.wait_for_function("() => window.L.town.value !== null", timeout=WAIT_MS)


def test_paired_the_link_speaks_the_phones_protocol_and_reads_the_phones_snapshot(paired):
    pg, phone = paired
    start(pg)
    sock = pg.evaluate("() => window.__sockets[0]")
    assert sock["url"].startswith("wss://") and sock["url"].endswith("/ws")
    assert sock["protocols"] == ["orkcraft.v1", f"bearer.{DEVICE['token']}"]
    town = pg.evaluate("() => window.L.town.value")
    assert town["rev"] == phone.snapshot()["rev"] and town["focus"] == "board"
    assert "mana" in town and "projects" in town
    assert not {"onboarding", "sign_in", "repo", "usage_ask"} & set(town)         # the computer's own stay there
    assert pg.evaluate("() => window.L.isPaired() && window.L.online.value")
    # a command and its reply: resolved with the result, refused with the computer's words
    assert pg.evaluate("() => window.L.command('ideas.board')") == {"echo": "ideas.board"}
    phone.refuse["ideas.add"] = "Open a folder first"
    said = pg.evaluate("() => window.L.command('ideas.add', {text: 'x'}, true).then(() => 'sent', (e) => e.message)")
    assert said == "Open a folder first"
    assert [n for n, _ in phone.got] == ["ideas.board", "ideas.add"]


def test_paired_what_a_phone_may_not_do_is_not_offered(paired):
    pg, _phone = paired
    start(pg)
    pg.wait_for_function("() => window.L.allowed.value !== null", timeout=WAIT_MS)
    assert pg.evaluate("() => window.L.can('ideas.add') && window.L.can('halt') && window.L.can('projects.use')")
    assert pg.evaluate("() => window.L.can('files.read')")                         # a Markdown file is read
    for name in ("phones.pair", "git.status", "tools.sign_in", "onboarding.skip", "files.write", "settings.set"):
        assert not pg.evaluate("(n) => window.L.can(n)", name), name


def test_no_signal_the_kept_snapshot_is_greyed_as_of_and_an_answer_waits_for_the_computer(paired):
    pg, phone = paired
    start(pg)
    rev = pg.evaluate("() => window.L.town.value.rev")
    assert pg.evaluate("() => !window.L.stale.value && window.L.offlineLine.value === ''")
    phone.mode = "dead"                                                             # the computer goes away
    phone.ws.close()
    pg.wait_for_function("() => window.L.stale.value", timeout=WAIT_MS)
    line = pg.evaluate("() => window.L.offlineLine.value")
    assert re.match(r"^As of .+\. (The board went away: trying again…|Cannot reach the board)", line), line
    assert pg.evaluate("() => window.L.town.value.rev") == rev                      # still drawn, from what was kept
    assert pg.evaluate("() => window.L.online.value") is False
    kept = pg.evaluate("() => window.L.deliver('ideas.answer', {idea: 'a', text: 'Yes'}, 'Your answer')")
    assert kept == {"ok": True, "kept": True}
    waiting = pg.evaluate("() => window.L.waiting.value")
    assert [(w["name"], w["label"]) for w in waiting] == [("ideas.answer", "Your answer")]
    assert pg.evaluate("() => window.L.SENT_WHEN") == "Sent when the computer answers"
    assert phone.got == []                                                          # nothing reached the computer
    phone.mode = "ok"                                                               # it answers again
    pg.wait_for_function("() => window.L.waiting.value.length === 0 && !window.L.stale.value", timeout=WAIT_MS * 2)
    assert phone.got == [("ideas.answer", {"idea": "a", "text": "Yes"})]
    assert pg.evaluate("() => window.L.offlineLine.value") == ""
    assert pg.evaluate("() => window.L.toasts.value.some((t) => t.message === 'Sent: Your answer')")


def test_a_page_opened_with_no_signal_draws_the_last_snapshot_kept_on_the_phone(paired):
    pg, phone = paired
    start(pg)
    rev = pg.evaluate("() => window.L.town.value.rev")
    phone.mode = "dead"
    pg.reload()                                                                     # a new page: only the phone's storage remains
    pg.evaluate(START, DEVICE)
    pg.wait_for_function("() => window.L.town.value !== null && window.L.stale.value", timeout=WAIT_MS)
    assert pg.evaluate("() => window.L.town.value.rev") == rev
    assert pg.evaluate("() => window.L.offlineLine.value").startswith("As of ")


def test_a_phone_forgotten_on_the_computer_says_so_and_keeps_nothing(paired):
    pg, phone = paired
    start(pg)
    pg.evaluate("() => window.L.deliver('ideas.answer', {}, 'x')")                  # (sent: nothing waits)
    phone.ws.close(code=1008, reason="This phone was forgotten")
    pg.wait_for_function("() => window.L.forgotten.value !== ''", timeout=WAIT_MS)
    assert pg.evaluate("() => window.L.forgotten.value") == "The board forgot this phone. Pair it again to use it."
    assert pg.evaluate("() => [localStorage.getItem('orkcraft.device'), localStorage.getItem('orkcraft.town')]") == [None, None]
    assert pg.evaluate("() => window.L.allowed.value") is None


def test_on_the_computer_the_link_is_not_paired(gui):
    server, browser = gui
    pg = narrow.page(browser, "wide")
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    assert pg.evaluate("() => import('/static/js/link.js').then((l) => [l.isPaired(), l.can('phones.pair'), l.stale.value])") == [False, True, False]
    pg.context.close()
