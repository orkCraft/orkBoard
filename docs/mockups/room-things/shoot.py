"""Before/after shots of the top row's three things: the door, the backpack and the new chair as they are (before), and
the mockup's lamp chain, backpack and chair dealing its crafts to the hand (after). Not a test of the product, a camera.
Both are drawn with the table's look (../table-look/); the after reuses ../answer-cards/' cards. The desktop only.

    MOCK_OUT=/tmp/room PYTHONPATH=. uv run --extra dev --extra browser --extra gui \
        pytest -q -p tests.conftest -p no:xdist docs/mockups/room-things/shoot.py
    (MOCK_BEFORE=1: the top row as it is; the stub host has no door, so the before shows none)"""
import importlib.util, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from tests.browser_kit import WAIT_MS, gui  # noqa: F401,E402

_spec = importlib.util.spec_from_file_location("table_look_shoot", HERE.parent / "table-look" / "shoot.py")
_look = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_look)
host = _look.host  # the table-look camera's stub host

OUT = Path(os.environ["MOCK_OUT"])
BEFORE = bool(os.environ.get("MOCK_BEFORE"))
LOOK_CSS = (HERE.parent / "table-look" / "table-look.css").read_text()
LOOK_JS = (HERE.parent / "table-look" / "table-look.js").read_text()
CARDS_CSS = (HERE.parent / "answer-cards" / "answer-cards.css").read_text()
CSS = (HERE / "room.css").read_text()
JS = (HERE / "room.js").read_text()
TAG = "before" if BEFORE else "after"


def dress(pg, mode):
    pg.evaluate(LOOK_JS)
    if not BEFORE:
        pg.evaluate(JS, mode)
    pg.mouse.move(5, 5)
    pg.wait_for_timeout(400)


def test_shots(gui):
    server, browser = gui
    h = host()
    pg = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
    pg.route_web_socket("**/ws*", h.on_socket)
    pg.goto(server.url)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(2500)
    pg.add_style_tag(content=LOOK_CSS)
    if not BEFORE:
        pg.add_style_tag(content=CARDS_CSS)
        pg.add_style_tag(content=CSS)
    OUT.mkdir(parents=True, exist_ok=True)
    dress(pg, "on")
    pg.screenshot(path=str(OUT / f"{TAG}-board.png"))
    if not BEFORE:
        dress(pg, "off")
        pg.screenshot(path=str(OUT / f"{TAG}-lamp-off.png"))
        dress(pg, "chair")
        pg.screenshot(path=str(OUT / f"{TAG}-chair.png"))
        pg.evaluate("() => { document.querySelector('.ac-stage')?.remove(); document.body.classList.remove('ac-on'); document.querySelector('.table-chair')?.classList.remove('rt-lit'); }")
    else:
        pg.get_by_text("New party").first.click(); pg.wait_for_timeout(1500)
        pg.screenshot(path=str(OUT / f"{TAG}-chair.png"))
        pg.keyboard.press("Escape"); pg.wait_for_timeout(800)
    pg.evaluate("() => document.querySelector('.table-tabs .stall-pack')?.click()"); pg.wait_for_timeout(1500)
    dress(pg, "pack")
    pg.screenshot(path=str(OUT / f"{TAG}-pack.png"))
