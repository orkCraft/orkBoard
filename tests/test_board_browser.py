"""`orkboard` in a real browser (docs/specs/37-board-and-line.md §4, Tests → B): Orkboard's own host and server on a
fixture repository, its keeper stubbed. On the desktop (1 440 × 900) the table and the hand, a party saved, its question a card of the hand.
It asks for no camp file: nothing under js/camp/, js/buildings/, sprites/ or v3/ (the network log). Screenshots to docs/design/img/v1/
when ORKCRAFT_SHOTS is set."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")

from orkboard.gui.board_host import Orkboard  # noqa: E402
from orkboard.gui.server import Server  # noqa: E402
from orkboard.realm import project_kind  # noqa: E402
from orkboard.realm import jobs  # noqa: E402
from tests.browser_kit import WAIT_MS, launch  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(__file__).resolve().parent.parent / "docs" / "design" / "img" / "v1"
CAMP = ("/js/camp/", "/js/buildings/", "/sprites/", "/v3/", "/camp/")
GOAL = {"summary": "Installs are the first step.\nCount them weekly.", "questions": ["Which channel first?"],
        "metrics": [{"name": "weekly installs", "how": "npm downloads, per week"}], "reply": "Noted."}


@pytest.fixture
def board(tmp_path, monkeypatch):
    """Orkboard on a fixture repository, its keeper answering a goal with a question: (host, repo)."""
    for key, value in {"ORKCRAFT_SETTINGS_FILE": tmp_path / "settings.json", "ORKCRAFT_ONBOARDING": "0",
                       "ORKCRAFT_LIMITS": "0", "ORKCRAFT_NO_UPDATE": "1", "XDG_CONFIG_HOME": tmp_path / "config"}.items():
        monkeypatch.setenv(key, str(value))
    repo = tmp_path / "project"
    (repo / "src").mkdir(parents=True)
    (repo / "README.md").write_text("# Demo project\n", encoding="utf-8")
    git = ["git", "-c", "user.email=test@orkcraft.local", "-c", "user.name=Test Runner"]
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "init"], cwd=repo, check=True)
    monkeypatch.setattr(jobs, "run_read", lambda *a, **k: (json.dumps(GOAL), 0.01, 10, "s-1"))
    host = Orkboard(repo)
    project_kind.keep(host.ideas.state_dir, "code")                                               # the first open's questions answered (spec 130): the Orkmaster comes to the parties
    host.first_open.tools_skipped = True
    return host


def _camp(urls: list[str]) -> list[str]:
    return [u for u in urls if any(part in u for part in CAMP)]


def test_orkboard_on_the_desktop_the_four_panes_a_goal_saved_and_needs_you_no_camp_file(board):
    server = Server(board)
    thread = server.start_thread()
    with playwright.sync_playwright() as p:
        browser = launch(p)
        try:
            ctx = browser.new_context(viewport={"width": 1440, "height": 900})
            pg = ctx.new_page()
            urls: list[str] = []
            errors: list[str] = []
            ctx.on("request", lambda r: urls.append(r.url))
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(server.url)
            more = pg.locator('[data-setup="parties"] [data-act="parties"]')                        # the first start in the room (spec 150 G): the parties as chairs, their large card a press away (decisions §169.4, §254.8)
            more.click()
            pg.locator('.parties[data-first="true"]').wait_for(timeout=WAIT_MS)
            assert pg.locator(".shell-top, .shell-drawer, .arena-left, .shell-backdrop, [aria-modal]").count() == 0 and pg.locator(".frame.fo-room").count() == 1
            assert pg.evaluate("document.documentElement.dataset.look") == "office"
            assert pg.locator(".gui-hud, .gui-camp, .gui-town, .gui-foot").count() == 0
            pg.keyboard.press("Escape")                                                             # Esc leaves it to the room ...
            pg.locator('.parties[data-first="true"]').wait_for(state="detached", timeout=WAIT_MS)
            more.click()                                                                            # ... whose card opens the one place of the parties again
            pg.locator('.parties[data-first="true"]').wait_for(timeout=WAIT_MS)
            assert pg.locator(".place, .shell-craft-tile").count() == 0 and pg.get_by_role("button", name="Start", exact=True).is_visible()
            pg.locator('.pc-later__one[data-party="marketing"] [role="checkbox"]').click()          # a party of a stage not reached yet: ticked by the person
            pg.get_by_role("button", name="Start", exact=True).click()                              # makes the ticked parties, each with its leader, builders and checkers
            pg.locator(".parties").wait_for(state="detached", timeout=WAIT_MS)
            pg.locator('.frame[data-laid="1"] .table-tabs').wait_for(timeout=WAIT_MS)              # the room gives way to the laid table
            for pane in (".table-tabs", ".table-pane"):                # the window's two parts, on the real host's data
                assert pg.locator(pane).is_visible(), pane
            g = next(t for t in board.command("ideas.board")["tracks"] if t["leader"]["slug"] == "growth")
            assert (g["leader"]["slug"], g["team"]) == ("growth", ["copywriter", "seo", "editor"])
            made = {r["slug"]: r for r in board.command("ideas.roles")["roles"]}
            assert made["copywriter"]["craft"] == "marketing" and made["growth"]["takes"] == ["campaign"]   # the party's agents: the project's roles
            pg.locator(f'.table-tab[data-tab="{g["slug"]}"]').click()                               # its tab
            pg.locator(".table-head").wait_for(timeout=WAIT_MS)             # the party's header: the leader's small cards (spec 168 E1)
            pg.get_by_role("button", name=re.compile(r"'s menu$")).first.click()
            pg.get_by_role("menuitem", name="Seats and tools").click()                              # who is in it lies in its leader's inventory (decisions §283.16.2)
            pg.locator(".stall-seats").wait_for(timeout=WAIT_MS)
            assert pg.locator(".stall-seats .table-seat").count() >= 2
            assert pg.locator(".hand").is_visible()
            assert any(n["kind"] == "goal" for n in board.command("ideas.board")["needs_you"])
            if os.environ.get("ORKCRAFT_SHOTS"):
                SHOTS.mkdir(parents=True, exist_ok=True)
                pg.screenshot(path=str(SHOTS / "orkboard-desktop-1440x900.png"))
            assert not _camp(urls), _camp(urls)
            assert any(u.endswith("/static/board.js") for u in urls) and not any(u.endswith("/static/app.js") for u in urls)
            assert not errors, errors
        finally:
            browser.close()
            server.stop()
            thread.join(10)

