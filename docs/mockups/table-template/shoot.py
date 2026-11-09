"""Pictures of the table's template (decision §283, drawn first): each scene at 1366 x 768, the laptop the decision is fitted to,
and the Orkmaster's project at 1440 x 900 too. Not a test of the product, a camera, in docs/mockups/leader-view/shoot.py's way.

    MOCK_OUT=docs/mockups/table-template/shots uv run --with playwright python docs/mockups/table-template/shoot.py

To look at it by hand, serve the repository's root (`python -m http.server` there) and open
http://localhost:8000/docs/mockups/table-template/index.html?scene=project: orkUI's masks are not read from file://.
"""
import functools, http.server, os, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MOCK_OUT", HERE / "shots"))
OUT.mkdir(parents=True, exist_ok=True)
ROOT = HERE.parents[2]   # served over HTTP from the repository's root: orkUI's masks (runes, signs) are not read from file://


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_port}/{HERE.relative_to(ROOT).as_posix()}/index.html"

SHOTS = [
    ("1-project", "scene=project", (1366, 768)),
    ("1-project-900", "scene=project", (1440, 900)),
    ("2-project-balloon", "scene=project&balloon=1", (1366, 768)),
    ("3-idea-orkmaster", "scene=idea-om", (1366, 768)),
    ("4-idea-orkmaster-hover", "scene=idea-om&hover=1", (1366, 768)),
    ("5-idea-tech-groups", "scene=idea-leader&layout=groups", (1366, 768)),
    ("6-idea-tech-rows", "scene=idea-leader&layout=rows", (1366, 768)),
    ("7-ask-tech", "scene=ask", (1366, 768)),
    ("8-tech-project", "scene=leader", (1366, 768)),
    ("9-small-face-b", "scene=idea-om&small=b", (1366, 768)),
    ("10-ask-tech-pictures", "scene=ask&pics=1", (1366, 768)),
    ("11-ask-risk-pictures", "scene=ask&pics=1&card=risk", (1366, 768)),
    ("12-ways-pictures", "scene=pictures", (1440, 900)),
    ("13-inventory-deep", "scene=inventory&slot=deep", (1366, 768)),
    ("14-inventory-start", "scene=inventory&slot=start", (1366, 768)),
]

with sync_playwright() as p:
    _exe = next((c for c in (os.environ.get("ORKCRAFT_CHROMIUM", ""), "/opt/pw-browsers/chromium") if c and Path(c).exists()), None)
    b = p.chromium.launch(executable_path=_exe) if _exe else p.chromium.launch()
    for name, query, (w, h) in SHOTS:
        pg = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2).new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(f"{BASE}?{query}")
        pg.wait_for_timeout(500)
        assert not errors, (name, errors)
        assert pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), name
        pg.screenshot(path=str(OUT / f"{name}.png"))
        pg.close()
    b.close()
server.shutdown()
print("shots in", OUT)
