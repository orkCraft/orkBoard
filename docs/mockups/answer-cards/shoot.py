"""Before/after shots of a lifted card: the big opened card (before) and the mockup's answer cards (after). Not a test of
the product, a camera. Both are drawn with the table's look (../table-look/) so that only the lifted card differs.
The table's stub host from the browser tests (a question by Game design and a failure by Tech in the hand). The desktop only.

    MOCK_OUT=/tmp/answer PYTHONPATH=. uv run --extra dev --extra browser --extra gui \
        pytest -q -p tests.conftest -p no:xdist docs/mockups/answer-cards/shoot.py
    (MOCK_BEFORE=1: the opened card as it is, with the table's look only)"""
import os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import pytest
from tests.browser_kit import WAIT_MS, gui  # noqa: F401
import importlib.util
_spec = importlib.util.spec_from_file_location("table_look_shoot", HERE.parent / "table-look" / "shoot.py")
_look = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_look)
host = _look.host  # the table-look camera's stub host

OUT = Path(os.environ["MOCK_OUT"])
BEFORE = bool(os.environ.get("MOCK_BEFORE"))
LOOK_CSS = (HERE.parent / "table-look" / "table-look.css").read_text()
LOOK_JS = (HERE.parent / "table-look" / "table-look.js").read_text()
CSS = (HERE / "answer-cards.css").read_text()
JS = (HERE / "answer-cards.js").read_text()
TAG = "before" if BEFORE else "after"


def dress(pg, mode="q"):
    pg.evaluate(LOOK_JS)
    if not BEFORE:
        print("answer-cards:", pg.evaluate(JS, mode))
    pg.mouse.move(5, 5)
    pg.wait_for_timeout(400)


def lift(pg, kind):
    pg.locator(f'.hand .hand-card[data-kind="{kind}"]').first.click(timeout=3000)
    pg.wait_for_timeout(1400)


def test_shots(gui):
    server, browser = gui
    h = host()
    pg = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
    pg.route_web_socket("**/ws*", h.on_socket)
    pg.goto(server.url)
    pg.locator(".hand-card").first.wait_for(state="attached", timeout=WAIT_MS)
    pg.wait_for_timeout(2500)
    pg.add_style_tag(content=LOOK_CSS)
    if not BEFORE:
        pg.add_style_tag(content=CSS)
    OUT.mkdir(parents=True, exist_ok=True)
    lift(pg, "asks"); dress(pg)
    pg.screenshot(path=str(OUT / f"{TAG}-question.png"))
    if not BEFORE:
        dress(pg, "pen")
        pg.screenshot(path=str(OUT / f"{TAG}-pen.png"))
    pg.keyboard.press("Escape"); pg.wait_for_timeout(800)
    pg.evaluate("() => { document.querySelector('.ac-stage')?.remove(); document.body.classList.remove('ac-on'); document.querySelectorAll('.ac-about').forEach((e) => e.classList.remove('ac-about')); }")
    lift(pg, "failed"); dress(pg)
    pg.screenshot(path=str(OUT / f"{TAG}-failure.png"))
