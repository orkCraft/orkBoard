"""Before/after shots of the window with the mockup's CSS and JS laid over it: not a test of the product, a camera.
The table's stub host from the browser tests (goals in the lanes, a failure and a question in the hand, a goal done).

    MOCK_OUT=/tmp/after MOCK_CSS=docs/mockups/table-look/table-look.css MOCK_JS=docs/mockups/table-look/table-look.js \
    MOCK_SCALE=2 uv run --extra dev --extra browser --extra gui pytest -q -p tests.conftest -p no:xdist docs/mockups/table-look/shoot.py
    (without MOCK_CSS and MOCK_JS: the window as it is, the "before")"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import pytest
from tests import narrow
from tests.browser_kit import WAIT_MS, gui  # noqa: F401
from tests.test_window_desktop_browser import WindowHost
from tests.test_table_desktop_browser import TableHost

OUT = Path(os.environ["MOCK_OUT"])
CSS = Path(os.environ["MOCK_CSS"]).read_text() if os.environ.get("MOCK_CSS") else ""
JS = Path(os.environ["MOCK_JS"]).read_text() if os.environ.get("MOCK_JS") else ""
DUMP = os.environ.get("MOCK_DUMP")
SCALE = int(os.environ.get("MOCK_SCALE", "1"))

TREE = """(root) => { const rows=[]; const walk=(e,d)=>{ if(d>16) return; const r=e.getBoundingClientRect(); if(r.width>20&&r.height>10){ const cs=getComputedStyle(e); rows.push('  '.repeat(d)+e.tagName.toLowerCase()+(typeof e.className==='string'&&e.className?'.'+e.className.trim().split(/\\s+/).join('.'):'')+Object.entries(e.dataset).map(([k,v])=>`[${k}=${String(v).slice(0,24)}]`).join('')+` ${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)} bg=${cs.backgroundColor} fs=${cs.fontSize}`+(e.children.length===0&&e.innerText?` "${e.innerText.trim().slice(0,30)}"`:''));} for(const c of e.children) walk(c,d+1); }; walk(document.querySelector(root),0); return rows.join('\\n'); }"""


def host():
    h = WindowHost()
    rich = TableHost(rich=True, line=3)
    music = [n for n in h.nodes if n["slug"] == "music"]
    h.nodes = rich.nodes + music
    for n in h.nodes:
        if n["slug"] == "timer":
            n["asked"] = [{"ask": "Where does the timer run?", "choices": ["Server counts, phones show it", "Each phone counts down alone"], "pick": 0, "why": "One clock.", "by": None, "look": False}]
    return h


def dress(pg):
    if CSS:
        pg.add_style_tag(content=CSS)
    if JS:
        pg.evaluate(JS)
    pg.wait_for_timeout(500)


@pytest.mark.parametrize("width", ["wide", "phone"])
def test_shots(gui, width):
    server, browser = gui
    h = host()
    if width == "wide":
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=SCALE)
    else:
        ctx = narrow.context(browser, "narrow")
    pg = ctx.new_page()
    art = os.environ.get("MOCK_ART")
    if art:
        def serve(route):
            rel = route.request.url.split("/mock-art/", 1)[1].split("?")[0]
            f = Path(art) / rel
            route.fulfill(path=str(f)) if f.exists() else route.fulfill(status=404, body="")
        pg.route("**/mock-art/**", serve)
    pg.route_web_socket("**/ws*", h.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(2500)
    dress(pg)
    OUT.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(OUT / f"board-{width}.png"))
    if DUMP and width == "wide":
        Path(DUMP).write_text(pg.evaluate(TREE, ".frame"))
    if width != "wide":
        return
    tabs = pg.evaluate("() => [...document.querySelectorAll('.table-tab')].map(e => e.dataset.tab)")
    for t in tabs:
        try:
            pg.locator(f'.table-tab[data-tab="{t}"]').click(timeout=3000)
            pg.wait_for_timeout(1800)
            if JS:
                pg.evaluate(JS); pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / f"tab-{t}.png"))
        except Exception as e:
            print("fail", t, str(e).splitlines()[0])
    pg.locator(".col-head__tab").first.click(); pg.wait_for_timeout(1500)
    # a hand card lifted
    try:
        pg.locator(".hand-card").nth(1).click(timeout=3000); pg.wait_for_timeout(1500)
        pg.screenshot(path=str(OUT / "hand-lifted.png"))
    except Exception as e:
        print("fail lift", str(e).splitlines()[0])
