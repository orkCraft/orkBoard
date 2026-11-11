"""Pictures of the readable look: today's look and three proposed ones (a font, the colours a step lifted, round corners), laid
over the existing mockups (the table's template, the phone's hand) by stylesheets only. Not a test of the product, a camera.

    uv run --with playwright python docs/mockups/readable-look/shoot.py

Each look is `looks/base.css` plus its own sheet, loaded after orkUI's tokens; the mockups' own pages are not changed.
"""
import functools, http.server, os, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MOCK_OUT", HERE / "shots"))
OUT.mkdir(parents=True, exist_ok=True)
ROOT = HERE.parents[2]


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_port}/docs/mockups"
LOOKS = [("0-now", None), ("a-tavern", "a-tavern.css"), ("b-poster", "b-poster.css"), ("c-tale", "c-tale.css")]
NAMES = {"0-now": "Today: Pixelify + IBM Plex, notched", "a-tavern": "A, the tavern: Rubik",
         "b-poster": "B, the poster: Unbounded + Onest", "c-tale": "C, the tale: Alegreya SC + Alegreya Sans"}
# (shot, page, viewport, scale, the element to cut, or None for the window)
SCENES = [
    ("desktop-ask", "table-template/index.html?scene=ask&pics=1", (1366, 768), 1, None),
    ("desktop-project", "table-template/index.html?scene=project", (1366, 768), 1, None),
    ("phone-hand", "phone/hand.html", (1300, 1000), 3, ".ph"),
    # the desktop's cards close up: the table's first row and the lifted card, at a laptop's DPR 2
    ("desktop-cards", "table-template/index.html?scene=ask&pics=1", (1366, 768), 2, (166, 108, 800, 240)),
]


def dress(page, sheet):
    if not sheet:
        return
    page.add_style_tag(url=f"{BASE}/readable-look/fonts/fonts.css")
    page.add_style_tag(url=f"{BASE}/readable-look/looks/base.css")
    page.add_style_tag(url=f"{BASE}/readable-look/looks/{sheet}")


with sync_playwright() as p:
    _exe = next((c for c in (os.environ.get("ORKCRAFT_CHROMIUM", ""), "/opt/pw-browsers/chromium") if c and Path(c).exists()), None)
    b = p.chromium.launch(executable_path=_exe) if _exe else p.chromium.launch()
    for scene, url, (w, h), dpr, cut in SCENES:
        for look, sheet in LOOKS:
            page = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dpr)
            page.goto(f"{BASE}/{url}")
            dress(page, sheet)
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(600)
            shot = OUT / f"{scene}-{look}.png"
            if isinstance(cut, tuple):
                page.screenshot(path=str(shot), clip=dict(zip(("x", "y", "width", "height"), cut)))
            else:
                (page.locator(cut).first if cut else page).screenshot(path=str(shot))
            page.close()
    # the comparison sheets: the four looks side by side, each scene
    for scene, _, (w, h), dpr, cut in SCENES:
        cols, cw = (4, 390) if isinstance(cut, str) else (2, cut[2]) if cut else (2, w)
        cells = "".join(f'<figure><figcaption>{NAMES[l]}</figcaption><img src="{scene}-{l}.png"></figure>' for l, _ in LOOKS)
        html = (f'<!doctype html><meta charset="utf-8"><style>body{{margin:0;background:#0c0b0a;color:#dedbd6;'
                f'font:600 15px/20px system-ui}}main{{display:grid;grid-template-columns:repeat({cols},auto);gap:16px;padding:16px}}'
                f'figure{{margin:0}}figcaption{{padding:0 0 6px}}img{{display:block;width:{cw}px}}</style><main>{cells}</main>')
        sheet = OUT / f"compare-{scene}.html"
        sheet.write_text(html)
        page = b.new_page(viewport={"width": cols * (cw + 16) + 16, "height": 600}, device_scale_factor=2 if cut else 1)
        page.goto(sheet.as_uri())
        page.wait_for_timeout(300)
        page.locator("main").screenshot(path=str(OUT / f"compare-{scene}.png"))
        page.close()
        sheet.unlink()
        for l, _ in LOOKS:   # only the comparisons are kept
            (OUT / f"{scene}-{l}.png").unlink()
    # the specimen: the four looks' faces, Latin and Cyrillic, on a card
    page = b.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
    page.goto(f"{BASE}/readable-look/specimen.html")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(600)
    page.locator("main").screenshot(path=str(OUT / "specimen.png"))
    page.close()
    b.close()
server.shutdown()
print("shots in", OUT)
