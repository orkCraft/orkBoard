"""Spec 121 part B (docs/specs/121-the-day-the-morning-and-the-night.md §3.3), in a real browser: a sketch's page, served by `/media/` and shown in an
`iframe sandbox="allow-scripts"` (no `allow-same-origin`) inside the Board's own page, runs its own script and style, and

- loads nothing from outside: its `fetch`, its `<img src=https://…>` and its `<link rel=stylesheet>` to an address of another origin never reach
  that address (a local server of the test counts every request), each reported by the browser as a policy violation;
- cannot read `parent.document`, its storage, nor the Board's page: its origin is opaque (`"null"`);
- opened on its own, not in a frame, its origin is opaque too (the second policy `sandbox allow-scripts`).
"""
from __future__ import annotations

import http.server
import json
import threading

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.gui import media  # noqa: E402
from tests import pick_files as pf  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser


@pytest.fixture
def outside():
    """An address of another origin that counts what is asked of it: `(base url, the paths asked)`."""
    asked: list[str] = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):                               # noqa: N802
            asked.append(self.path)
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "text/css" if self.path.endswith(".css") else "text/plain")
            self.end_headers()
            self.wfile.write(b"body{background:red}")

        def log_message(self, *a):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", asked
    httpd.shutdown()
    httpd.server_close()
    thread.join(5)


def sketch(base: str) -> bytes:
    """A page that does everything a page should not be able to: it asks the outside address three ways, reaches for its parent and its storage, and
    reports what it found to the page that holds it (`postMessage`, the one thing a framed page may do)."""
    return f"""<!doctype html><meta charset="utf-8"><title>A</title>
<link rel="stylesheet" href="{base}/outside.css">
<style>#box {{ color: rgb(1, 2, 3); }}</style>
<img src="{base}/outside.png" alt="">
<p id="box">A sketch</p>
<script>
const report = {{ violations: [], origin: String(window.origin) }};
document.addEventListener("securitypolicyviolation", (e) => report.violations.push(e.blockedURI + " " + e.effectiveDirective));
const tries = [];
try {{ report.parent = String(parent.document.title); }} catch (e) {{ report.parent = "blocked: " + e.name; }}
try {{ report.storage = String(localStorage.length); }} catch (e) {{ report.storage = "blocked: " + e.name; }}
try {{ report.top = String(top.document.body.innerHTML.length); }} catch (e) {{ report.top = "blocked: " + e.name; }}
tries.push(fetch("{base}/outside.json").then(() => (report.fetch = "reached"), (e) => (report.fetch = "blocked: " + e.name)));
Promise.all(tries).then(() => setTimeout(() => {{
  report.color = getComputedStyle(document.getElementById("box")).color;
  parent.postMessage(JSON.stringify(report), "*");
}}, 400));
</script>""".encode("utf-8")


def test_a_sketchs_page_runs_its_own_script_and_loads_nothing_and_reads_nothing_of_the_board(gui, outside, tmp_path):
    server, browser = gui
    base, asked = outside
    pf.make_page_pick(server.host.ideas.state_dir, tmp_path / "pg", sketch(base), slug="sketch-page")
    address = media.url("sketch-page", "sketch-r1", "a.html")
    pg = browser.new_page()
    try:
        pg.goto(server.url)
        pg.evaluate("""(src) => {
          window.__heard = [];
          window.addEventListener("message", (e) => window.__heard.push(e.data));
          document.body.setAttribute("data-board-secret", "the board's page");
          const f = document.createElement("iframe");
          f.setAttribute("sandbox", "allow-scripts");
          f.setAttribute("title", "Sketch A by Design");
          f.src = src;
          document.body.append(f);
        }""", address)
        pg.wait_for_function("window.__heard.length > 0", timeout=WAIT_MS)
        got = json.loads(pg.evaluate("window.__heard[0]"))
    finally:
        pg.close()
    assert got["origin"] == "null"                                       # an opaque origin: no allow-same-origin
    assert got["parent"].startswith("blocked: ") and got["top"].startswith("blocked: ") and got["storage"].startswith("blocked: ")
    assert got["fetch"].startswith("blocked: ")                          # its script ran, and its request did not leave
    assert got["color"] == "rgb(1, 2, 3)"                                # its own style applied; the outside sheet (red body) did not
    assert asked == []                                                   # nothing reached the outside address: not the fetch, the image or the sheet
    directives = " ".join(got["violations"])
    assert "connect-src" in directives or "default-src" in directives     # the browser counted them as policy violations
    assert len(got["violations"]) >= 3


def test_a_sketchs_page_opened_on_its_own_still_has_an_opaque_origin(gui, outside, tmp_path):
    server, browser = gui
    base, asked = outside
    pf.make_page_pick(server.host.ideas.state_dir, tmp_path / "pg", sketch(base), slug="sketch-solo")
    pg = browser.new_page()
    try:
        response = pg.goto(server.origin + media.url("sketch-solo", "sketch-r1", "a.html"))
        assert response is not None and response.status == 200
        assert pg.evaluate("String(window.origin)") == "null"            # the second policy, `sandbox allow-scripts`: not the Board's origin
        assert pg.evaluate("(() => { try { return String(localStorage.length); } catch (e) { return 'blocked: ' + e.name; } })()").startswith("blocked: ")
        pg.wait_for_timeout(600)
    finally:
        pg.close()
    assert asked == []
