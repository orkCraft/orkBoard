"""Twelve pictures of a leader's view: three faces x with a view and with none x at 1280 x 800 and at 600 x 800.
Not a test of the product, a camera, in docs/mockups/answer-cards/shoot.py's way.

    MOCK_OUT=/tmp/leader-view uv run --with playwright python docs/mockups/leader-view/shoot.py
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ["MOCK_OUT"])
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    _exe = next((c for c in (os.environ.get("ORKCRAFT_CHROMIUM", ""), "/opt/pw-browsers/chromium") if c and Path(c).exists()), None)
    b = p.chromium.launch(executable_path=_exe) if _exe else p.chromium.launch()
    for width in (1280, 600):
        pg = b.new_context(viewport={"width": width, "height": 800}).new_page()
        for face in "abc":
            for state in ("view", "none"):
                pg.goto(f"{(HERE / 'index.html').as_uri()}?face={face}&state={state}")
                pg.wait_for_timeout(500)
                assert pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (face, state, width)
                pg.screenshot(path=str(OUT / f"{face}-{state}-{width}.png"))
    b.close()
