"""The Tech leader's tab with a leader's six moods (from check_sheet.py's OUT_DIR) on the mockup's table: the Orkmaster's table, then
Tech open in each mood. MOCK_DIR = check_sheet.py's OUT_DIR; the shots go to MOCK_DIR/moodshots.

    PYTHONPATH=. MOCK_DIR=/tmp/heads MOCK_OUT=/tmp/x uv run --extra dev --extra browser --extra gui pytest -q -p tests.conftest -p no:xdist \
        docs/mockups/leader-heads/sketches/shoot_tab.py"""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "docs" / "mockups" / "table-look"))
from tests.browser_kit import WAIT_MS, gui  # noqa: F401
from shoot import host
S = Path(os.environ["MOCK_DIR"]); OUT = S / "moodshots"; OUT.mkdir(exist_ok=True)
LOOK = ROOT / "docs" / "mockups" / "table-look"
CSS = (LOOK / "table-look.css").read_text(); JS = (LOOK / "table-look.js").read_text()
SWAP = """(m) => { for (const img of document.querySelectorAll('.table-tabcell[data-cell="tech"] img.ork-race__head')) {
  const w = Math.round(img.getBoundingClientRect().width); const size = w >= 46 ? 48 : w >= 34 ? 36 : 24;
  img.removeAttribute("srcset"); img.src = `/mock-art/${m}-${size}@2x.png`; img.style.imageRendering = "pixelated"; img.style.width = (size === 24 ? 24 : 48) + "px"; img.style.height = (size === 24 ? 24 : 48) + "px"; } }"""

def test_moods(gui):
    server, browser = gui
    h = host(); ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2); pg = ctx.new_page()
    pg.route("**/mock-art/**", lambda r: r.fulfill(path=str(S / r.request.url.split("/mock-art/", 1)[1])))
    pg.route_web_socket("**/ws*", h.on_socket); pg.goto(server.url)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS); pg.wait_for_timeout(2500)
    pg.add_style_tag(content=CSS); pg.evaluate(JS); pg.wait_for_timeout(400)
    pg.evaluate(SWAP, "calm"); pg.wait_for_timeout(400)
    pg.screenshot(path=str(OUT / "board.png"))
    pg.locator('.table-tab[data-tab="tech"]').click(); pg.wait_for_timeout(1800); pg.evaluate(JS); pg.wait_for_timeout(300)
    for m in ["calm", "focused", "worried", "no", "pleased", "asleep"]:
        pg.evaluate(SWAP, m); pg.wait_for_timeout(350)
        pg.screenshot(path=str(OUT / f"tech-{m}.png"), clip={"x": 160, "y": 0, "width": 900, "height": 130})
