"""Spec 107 §2.4 (B), the page's part of the logs: Save logs sends what the window can say of itself (its size, face, open tab, what
lies over the pane, the System's lens) and the page's last 20 errors, console.error's too (js/crashes.js `recentErrors`,
js/shell/errors.js `saveLogs`); `saveLogs(said, days)` keeps its signature. Against the table's stub host."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost  # noqa: E402

pytestmark = pytest.mark.browser

SAVE = """async (n) => {
  const m = await import('/static/js/shell/errors.js');
  return m.saveLogs('the words', n);
}"""


class LogsHost(TableHost):
    def handle(self, name, a):
        if name == "logs.save":
            self.log.append((name, a))
            return {"path": "/home/me/Downloads/orkboard-logs-x.zip", "name": "orkboard-logs-x.zip", "folder": "/home/me/Downloads"}
        return super().handle(name, a)


def test_save_logs_sends_the_pages_state_and_its_last_twenty_errors(gui):
    server, browser = gui
    host = LogsHost()
    pg = browser.new_page(viewport={"width": 1280, "height": 800})
    seen: list[str] = []
    pg.on("pageerror", lambda e: seen.append(str(e)))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    pg.evaluate("""() => {
      for (let i = 0; i < 25; i++) console.error(new TypeError('boom ' + i));
      console.error('plain words', { a: 1 });
      window.dispatchEvent(new ErrorEvent('error', { error: new RangeError('fell'), message: 'fell' }));
    }""")
    pg.evaluate(SAVE, 1)
    [(_, args)] = [c for c in host.log if c[0] == "logs.save"]
    page = args["page"]
    assert args["said"] == "the words" and args["days"] == 1
    assert (page["w"], page["h"]) == (1280, 800) and page["dpr"] >= 1 and page["face"] == "desktop"
    assert page["tab"] == "orkmaster" and page["over"] == "" and page["lens"] == ""
    assert len(page["errors"]) == 20 and page["errors"][-1].startswith("RangeError: fell") and page["errors"][-2] == "plain words {\"a\":1}"
    assert page["errors"][-3].startswith("TypeError: boom 24") and " @ " in page["errors"][-3]            # the message and the stack's first line
    assert not seen
    pg.context.close()


def test_the_pages_face_is_the_editors_in_a_frame_and_the_apps_in_its_window(gui):
    server, browser = gui
    host = LogsHost()
    pg = browser.new_page(viewport={"width": 1280, "height": 800})
    pg.route_web_socket("**/ws*", host.on_socket)
    face = "import('/static/js/shell/errors.js').then((m) => m.pageState().face)"
    pg.goto(server.url + "&app=1")
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    assert pg.evaluate(face) == "app"
    pg.evaluate("(url) => { const f = document.createElement('iframe'); f.id = 'f'; f.src = url; document.body.append(f); }",
                server.url + "&app=1")                                  # the editor's panel shows the page in a frame
    frame = pg.wait_for_selector("#f").content_frame()
    frame.wait_for_load_state()
    assert frame.evaluate(face) == "vscode"
    pg.context.close()
