"""Spec 115 part A (docs/specs/115-the-live-product-under-each-leaders-eyes.md §2.2), Chromium against the probe (gui/static/play/probe.js): a parent
page (the Board's stand-in) frames a fake dev server through the proxy (gui/play_proxy.py) and hears the probe.

`place` at load and at every change of the history (pushState, a hash route, back); `under` a box (the best cover first, the component's file from a
`data-source` attribute, a canvas named as one); `event`: an uncaught error, a rejection, console.error, a failed fetch and an XHR (no query, no
body), a press that did nothing against one that brought a request or a change; `picture` (inputs masked, a canvas as an image, no script, a base);
`state`; and a message from another origin ignored."""
from __future__ import annotations

import http.server
import json
import threading
import time

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.gui import play_proxy  # noqa: E402
from tests.browser_kit import launch, playwright  # noqa: E402

pytestmark = pytest.mark.browser

APP = """<!doctype html>
<html><head><meta charset="utf-8"><title>Tower brawl</title>
<style>body{margin:0;font:16px sans-serif} button,a,input,textarea{position:absolute} #go{left:20px;top:20px;width:100px;height:40px}
#dead{left:140px;top:20px;width:100px;height:40px} #push{left:260px;top:20px;width:100px;height:40px} #hash{left:380px;top:20px;width:100px;height:40px}
#boom{left:20px;top:80px;width:100px;height:40px} #fail{left:140px;top:80px;width:100px;height:40px} #grow{left:260px;top:80px;width:100px;height:40px}
#name{left:20px;top:140px;width:160px} #notes{left:200px;top:140px;width:160px;height:40px} #game{position:absolute;left:20px;top:220px;width:300px;height:200px;background:#123}</style>
</head><body>
<button id="go" data-source="src/components/Go.jsx:12:3" onclick="fetch('/api/ok?x=1')">Go</button>
<button id="dead">Nothing happens</button>
<button id="push" onclick="history.pushState({}, '', '/level/2')">Push</button>
<button id="hash" onclick="location.hash = '#/menu/sound?x=1'">Hash</button>
<button id="boom" onclick="setTimeout(function () { throw new Error('kaboom ' + 'x'.repeat(400)); }); console.error('bad thing', 42); Promise.reject(new Error('nope'))">Boom</button>
<button id="fail" onclick="fetch('/api/fail?token=abc', {method: 'POST', body: 'secret body'}); var x = new XMLHttpRequest(); x.open('GET', '/api/ok?y=2'); x.send()">Fail</button>
<button id="grow" onclick="var p = document.createElement('p'); p.textContent = 'more'; document.body.appendChild(p)">Grow</button>
<input id="name" type="text"><textarea id="notes"></textarea>
<canvas id="game" width="300" height="200"></canvas>
<script>
  var c = document.getElementById('game').getContext('2d'); c.fillStyle = '#e33'; c.fillRect(10, 10, 100, 100);
  window.__ork = { state: function () { return { level: 3, gold: 40 }; } };
</script>
</body></html>"""
PLAIN = "<!doctype html><title>plain</title><p>no state here</p>"
BIG = "<!doctype html><title>big</title><script>window.__ork = {state: function () { return {blob: 'x'.repeat(5000)}; }};</script>"
PAGES = {"/": APP, "/level/2": APP, "/plain": PLAIN, "/big": BIG}


class Dev(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_a) -> None:
        pass

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        status, body, kind = (200, PAGES[path], "text/html") if path in PAGES else (500, "boom", "text/plain") if path == "/api/fail" else (200, "{}", "application/json")
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(data)

    do_POST = do_GET


def serve(handler) -> http.server.ThreadingHTTPServer:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class Parent(http.server.BaseHTTPRequestHandler):
    """The Board's stand-in: a page that frames `?src=` at 800 x 600 and keeps every message it hears (`window.msgs`)."""

    def log_message(self, *_a) -> None:
        pass

    def do_GET(self) -> None:
        src = self.path.split("src=", 1)[1] if "src=" in self.path else ""
        page = f"""<!doctype html><body style="margin:0"><iframe id="f" src="{src}" style="border:0;width:800px;height:600px"></iframe>
<script>
  window.msgs = []; var n = 0;
  addEventListener('message', function (e) {{ window.msgs.push({{origin: e.origin, data: e.data}}); }});
  window.ask = function (kind, extra) {{ var id = ++n; document.getElementById('f').contentWindow.postMessage(Object.assign({{ork: 1, kind: kind, id: id}}, extra), new URL(document.getElementById('f').src).origin); return id; }};
</script></body>""".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)


@pytest.fixture(scope="module")
def chromium():
    pw = playwright.sync_playwright().start()
    browser = launch(pw)
    yield browser
    browser.close()
    pw.stop()


class Rig:
    """One dev server, its proxy, a parent page (and another at a second origin)."""

    def __init__(self, chromium, o: str | None = "parent") -> None:
        self.dev = serve(Dev)
        self.parent, self.other = serve(Parent), serve(Parent)
        self.parent_origin = f"http://127.0.0.1:{self.parent.server_address[1]}"
        self.other_origin = f"http://127.0.0.1:{self.other.server_address[1]}"
        self.proxy = play_proxy.PlayProxy(self.dev.server_address[1], "p1", self.parent_origin if o == "parent" else "").start()
        self.context = chromium.new_context(viewport={"width": 900, "height": 700})
        self.errors: list[str] = []

    def open(self, which: str = "parent", path: str = "/"):
        base = self.parent_origin if which == "parent" else self.other_origin
        pg = self.context.new_page()
        pg.on("pageerror", lambda e: self.errors.append(str(e)))
        pg.goto(f"{base}/?src={self.proxy.url_of(path)}")
        return pg

    def close(self) -> None:
        self.context.close()
        self.proxy.stop()
        for s in (self.dev, self.parent, self.other):
            s.shutdown()
            s.server_close()


@pytest.fixture
def rig(chromium):
    r = Rig(chromium)
    yield r
    r.close()


def heard(pg, kind: str, since: int = 0, **match) -> list[dict]:
    return [m["data"] for m in pg.evaluate("window.msgs")[since:] if m["data"].get("kind") == kind and all(m["data"].get(k) == v for k, v in match.items())]


def wait_for(pg, kind: str, timeout: float = 8.0, since: int = 0, **match) -> dict:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if got := heard(pg, kind, since, **match):
            return got[-1]
        time.sleep(0.05)
    raise AssertionError(f"no {kind} {match} heard; heard: {[m['data'].get('kind') for m in pg.evaluate('window.msgs')]}")


def events(pg, name: str, since: int = 0) -> list[dict]:
    return [m for m in heard(pg, "event", since) if m["event"] == name]


def wait_event(pg, name: str, timeout: float = 8.0, **match) -> dict:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if got := [e for e in events(pg, name) if all(e.get(k) == v for k, v in match.items())]:
            return got[-1]
        time.sleep(0.05)
    raise AssertionError(f"no event {name} {match}; heard: {events(pg, name)}")


def ask(pg, kind: str, **extra) -> dict:
    ident = pg.evaluate("([k, x]) => window.ask(k, x)", [kind, extra])
    return wait_for(pg, kind, id=ident)


def frame(pg):
    return pg.frame_locator("#f")


def rect(pg, selector: str) -> dict:
    return frame(pg).locator(selector).evaluate("e => { const r = e.getBoundingClientRect(); return {x: r.left, y: r.top, w: r.width, h: r.height}; }")


def test_place_is_told_at_load_and_at_every_change_of_the_history(rig):
    pg = rig.open()
    first = wait_for(pg, "place")
    assert first["ork"] == 1 and first["play"] == "p1" and first["path"] == "/" and first["route"] == "" and first["viewport"] == {"w": 800, "h": 600}
    assert pg.evaluate("window.msgs[0].origin") == rig.proxy.origin
    frame(pg).locator("#push").click()
    assert wait_for(pg, "place", path="/level/2")["route"] == ""
    frame(pg).locator("#hash").click()
    assert wait_for(pg, "place", route="/menu/sound")["path"] == "/level/2"
    pg.frames[1].evaluate("history.back()")
    wait_for(pg, "place", since=len(pg.evaluate("window.msgs")) - 1, route="")
    assert not rig.errors


def test_the_page_is_unchanged_but_for_the_script_and_the_probe_adds_nothing(rig):
    pg = rig.open()
    wait_for(pg, "place")
    f = pg.frames[1]
    assert f.evaluate("document.head.firstElementChild.src").endswith("/__ork/probe.js?o=" + rig.parent_origin.replace(":", "%3A").replace("/", "%2F") + "&p=p1")
    assert f.evaluate("document.querySelectorAll('body *').length") == 11                      # the page's own elements, none the probe's
    assert f.evaluate("document.title") == "Tower brawl" and f.evaluate("getComputedStyle(document.body).margin") == "0px"


def test_under_a_box_the_elements_it_covers_best_come_first(rig):
    pg = rig.open()
    wait_for(pg, "place")
    box = rect(pg, "#go")
    got = ask(pg, "under", box=box)["elements"]
    assert 1 <= len(got) <= 3 and got[0]["selector"] == "#go" and got[0]["role"] == "button" and got[0]["text"] == "Go"
    assert got[0]["rect"] == {"x": 20, "y": 20, "w": 100, "h": 40} and got[0]["file"] == "src/components/Go.jsx" and got[0]["line"] == 12
    assert all(set(e) <= {"selector", "role", "text", "rect", "file", "line"} for e in got)
    point = ask(pg, "under", box={"x": 150, "y": 30, "w": 0, "h": 0})["elements"]                # a press: the smallest element there
    assert point[0]["selector"] == "#dead" and "file" not in point[0]


def test_a_canvas_is_named_as_one_and_a_long_text_is_cut(rig):
    pg = rig.open()
    wait_for(pg, "place")
    got = ask(pg, "under", box={"x": 40, "y": 240, "w": 120, "h": 100})["elements"]
    assert got[0]["role"] == "canvas" and got[0]["selector"] == "#game" and got[0]["text"] == ""
    frame(pg).locator("#dead").evaluate("e => { e.textContent = 'word '.repeat(60); }")
    assert len(ask(pg, "under", box=rect(pg, "#dead"))["elements"][0]["text"]) <= 80


def test_errors_are_told_with_a_short_message_and_the_first_frame(rig):
    pg = rig.open()
    wait_for(pg, "place")
    frame(pg).locator("#boom").click()
    uncaught = wait_event(pg, "error", source="error")
    assert uncaught["message"].startswith("Uncaught Error: kaboom") and len(uncaught["message"]) <= 300 and uncaught["page"] == "/"
    assert uncaught["stack"] and "\n" not in uncaught["stack"] and len(uncaught["stack"]) <= 300
    assert wait_event(pg, "error", source="rejection")["message"] == "nope"
    said = wait_event(pg, "error", source="console")
    assert said["message"] == "bad thing 42" and isinstance(said["at"], int)


def test_requests_are_told_without_a_query_or_a_body(rig):
    pg = rig.open()
    wait_for(pg, "place")
    frame(pg).locator("#fail").click()
    failed = wait_event(pg, "request", method="POST", path="/api/fail")
    assert failed["status"] == 500 and isinstance(failed["ms"], int) and failed["page"] == "/" and "host" not in failed
    xhr = wait_event(pg, "request", method="GET", path="/api/ok")
    assert xhr["status"] == 200
    assert "token" not in json.dumps(events(pg, "request")) and "secret" not in json.dumps(events(pg, "request"))
    assert not [e for e in events(pg, "request") if "__ork" in e["path"]]                       # the probe's own file is no request of the page's


def test_a_press_that_did_nothing_is_told_apart_from_one_that_did(rig):
    pg = rig.open()
    wait_for(pg, "place")
    frame(pg).locator("#dead").click()
    dead = wait_event(pg, "press", timeout=4, selector="#dead")
    assert dead["changed"] is False and dead["dom"] is False and dead["moved"] is False and dead["request"] is False
    assert dead["pressable"] is True and dead["role"] == "button" and dead["rect"] == {"x": 140, "y": 20, "w": 100, "h": 40}
    frame(pg).locator("#go").click()
    assert wait_event(pg, "press", timeout=4, selector="#go")["request"] is True
    frame(pg).locator("#grow").click()
    grew = wait_event(pg, "press", timeout=4, selector="#grow")
    assert grew["dom"] is True and grew["changed"] is True and grew["request"] is False
    frame(pg).locator("#push").click()
    moved = wait_event(pg, "press", timeout=4, selector="#push")
    assert moved["moved"] is True and moved["changed"] is True


def test_a_picture_is_the_document_with_inputs_masked_and_a_canvas_as_an_image(rig):
    pg = rig.open()
    wait_for(pg, "place")
    frame(pg).locator("#name").fill("hunter2")
    frame(pg).locator("#notes").fill("my private notes")
    got = ask(pg, "picture")
    html = got["html"]
    assert "none" not in got and got["w"] == 800 and got["h"] == 600
    assert html.startswith("<!DOCTYPE html>") and f'<base href="{rig.proxy.origin}/">' in html
    assert "hunter2" not in html and "private" not in html and "•••••••" in html and "••••••••••••••••" in html
    assert "<canvas" not in html and 'src="data:image/png;base64,' in html
    assert "<script" not in html and "onclick" not in html and "Tower brawl" in html and "Nothing happens" in html


def test_a_canvas_that_cannot_be_read_is_blank_and_a_big_page_has_no_picture(rig):
    pg = rig.open()
    wait_for(pg, "place")
    frame(pg).locator("#game").evaluate("""c => { c.toDataURL = () => { throw new DOMException('tainted', 'SecurityError'); }; }""")
    html = ask(pg, "picture")["html"]
    assert "<canvas" not in html and "<img" in html and 'src="data:' not in html
    frame(pg).locator("body").evaluate("b => { b.insertAdjacentHTML('beforeend', '<div>' + 'x'.repeat(5 * 1024 * 1024) + '</div>'); }")
    big = ask(pg, "picture")
    assert big["none"] is True and "html" not in big


def test_state_is_what_the_page_tells_in_two_kilobytes(rig):
    pg = rig.open()
    wait_for(pg, "place")
    assert ask(pg, "state")["state"] == {"level": 3, "gold": 40}
    pg2 = rig.open(path="/plain")
    wait_for(pg2, "place")
    assert ask(pg2, "state").get("none") is True and "state" not in ask(pg2, "state")
    pg3 = rig.open(path="/big")
    wait_for(pg3, "place")
    assert ask(pg3, "state").get("none") is True


def test_a_message_from_another_origin_is_ignored_and_none_is_sent_to_it(rig):
    other = rig.open("other")
    other.wait_for_timeout(700)
    assert other.evaluate("window.msgs") == []                                                  # the probe posts to its parent's origin only
    other.evaluate("window.ask('under', {box: {x: 0, y: 0, w: 800, h: 600}})")
    other.evaluate("window.ask('state')")
    other.wait_for_timeout(700)
    assert other.evaluate("window.msgs") == []                                                  # and answers no one else
    pg = rig.open()
    assert wait_for(pg, "place")["path"] == "/"                                                 # the right parent is heard as ever


def test_with_no_origin_given_the_browser_names_the_parent(chromium):
    rig = Rig(chromium, o=None)
    try:
        pg = rig.open()
        assert wait_for(pg, "place")["play"] == "p1"
        assert ask(pg, "state")["state"] == {"level": 3, "gold": 40}
    finally:
        rig.close()


def test_a_page_that_is_not_framed_is_left_alone(rig):
    pg = rig.context.new_page()
    pg.goto(rig.proxy.url_of("/"))
    assert pg.evaluate("window.__orkProbe") is None and pg.evaluate("document.title") == "Tower brawl"
    pg.evaluate("document.getElementById('boom').click()")
    pg.wait_for_timeout(300)
    assert not rig.errors
