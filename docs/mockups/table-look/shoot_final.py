"""The product as built, spec 160 L (a camera, not a test): Tech's tab lit and out, the Orkmaster's, the new chair dealt, the header's stage dealt and the backpack open at 1280 x 800; the phone Here, Away and the backpack at 390 x 844.

    FINAL_OUT=docs/mockups/table-look/shots PYTHONPATH=. uv run --extra dev --extra browser --extra gui pytest -q -s -p tests.conftest -p no:xdist docs/mockups/table-look/shoot_final.py
"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import pytest
from tests import narrow
from tests.browser_kit import WAIT_MS, gui  # noqa: F401
from tests.test_chair_deal_browser import LIVEOPS, MARKETING, RELEASE, preset
from tests.test_header_project_browser import OFFERED
from tests.test_window_desktop_browser import WindowHost
from tests.test_table_desktop_browser import TableHost

OUT = Path(os.environ.get("FINAL_OUT", "docs/mockups/table-look/shots"))
HERE = {"here": True, "until": "2026-11-08T23:00", "held": False}


def host():
    """The rich table with the presence, the chair's three crafts (Marketing the Orkmaster's pick), the project's stage and the lamp that turns."""
    h = WindowHost()
    rich = TableHost(rich=True, line=3)
    h.nodes = rich.nodes + [n for n in h.nodes if n["slug"] == "music"]
    h.pres = dict(HERE)
    h.stage = "being_made"
    snapshot, handle = h.snapshot, h.handle
    presets = [preset("liveops", "LiveOps", LIVEOPS, "event-imp", "live"), preset("marketing", "Marketing", MARKETING, "growth-hack-gnome", "idea", recommended=True),
               preset("release", "Release", RELEASE, "release-night-king", "being_made")]

    def snap():
        doc = snapshot()
        doc["state"]["presence"] = dict(h.pres)
        return doc

    def hd(name, a):
        if name == "presence.set":
            h.pres.update(here=a["here"], until="2026-11-08T23:00" if a["here"] else "2026-11-09T19:00", held=True)
            h.rev += 1
            h.ws.send(json.dumps(snap()))
            return dict(h.pres)
        if name == "ideas.party_presets":
            return {"kind": {"id": "game", "words": "a game", "how": ""}, "presets": presets}
        if name == "ideas.stage":
            return {"stage": h.stage, "read": "idea", "kept": True, "kind": "game", "offered": OFFERED}
        if name == "ideas.party_price":
            if a["leader"] == "release-night-king":
                return {"error": "No price"}
            return {"low": 4.0, "high": 5.0, "learned": True, "ideas": 3, "checks": [], "hints": []}
        return handle(name, a)
    h.snapshot, h.handle = snap, hd
    return h


def open_page(browser, server, ctx, tab=None):
    h = host()
    pg = browser.new_context(**ctx).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route_web_socket("**/ws*", h.on_socket)
    pg.goto(server.url)
    pg.locator(".up-top" if ctx is narrow.NARROW else ".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    if tab:
        pg.locator(f'.table-tab[data-tab="{tab}"]').click()
    pg.wait_for_timeout(2500)
    OUT.mkdir(parents=True, exist_ok=True)
    return pg, h, errs


def test_desktop(gui):
    server, browser = gui
    pg, h, errs = open_page(browser, server, narrow.WIDE)
    print("open tab:", pg.locator("#table-pane").get_attribute("data-party"))
    pg.mouse.move(640, 790)
    pg.screenshot(path=str(OUT / "final-orkmaster.png"))
    pg.locator('.table-tab[data-tab="tech"]').click()
    pg.wait_for_timeout(1800)
    pg.mouse.move(640, 790)
    pg.screenshot(path=str(OUT / "final-tech-lit.png"))
    pg.locator(".presence-chain").click()
    pg.wait_for_timeout(1500)
    pg.mouse.move(640, 790)
    pg.screenshot(path=str(OUT / "final-tech-out.png"))
    pg.locator(".presence-chain").click()
    pg.wait_for_timeout(1200)
    pg.locator("[data-backpack]").click()
    pg.wait_for_timeout(1500)
    pg.mouse.move(640, 790)
    pg.screenshot(path=str(OUT / "final-pack.png"))
    pg.locator("[data-backpack]").click()
    pg.wait_for_timeout(800)
    pg.locator('.col-head__pick[data-deal="stage"]').click()
    pg.locator(".hand-card, .hand-craft").first.wait_for(timeout=WAIT_MS)
    pg.mouse.move(2, 2)
    pg.wait_for_timeout(800)
    pg.screenshot(path=str(OUT / "final-header.png"))
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(600)
    pg.locator(".table-chair").click()
    pg.locator(".hand-crafts .hand-craft").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => [...document.querySelectorAll('.hand-craft__price')].every((e) => e.textContent.trim())", timeout=WAIT_MS)
    pg.mouse.move(2, 2)
    pg.wait_for_timeout(800)
    pg.screenshot(path=str(OUT / "final-chair.png"))
    print("errors:", errs)


def test_phone(gui):
    server, browser = gui
    pg, h, errs = open_page(browser, server, narrow.NARROW)
    pg.locator(".hand-up").wait_for(timeout=WAIT_MS)
    pg.screenshot(path=str(OUT / "final-phone.png"))
    pg.locator(".up-top .presence-chain").click()
    pg.wait_for_function("() => document.querySelector('.hand-up').classList.contains('is-out')", timeout=WAIT_MS)
    pg.wait_for_timeout(800)
    pg.screenshot(path=str(OUT / "final-phone-away.png"))
    pg.locator(".up-top .presence-chain").click()
    pg.wait_for_timeout(800)
    pg.locator(".up-top .stall-pack").click()
    pg.locator(".stall-merchant").wait_for(state="visible", timeout=WAIT_MS)
    pg.wait_for_timeout(1200)
    pg.screenshot(path=str(OUT / "final-phone-pack.png"))
    print("errors:", errs)
