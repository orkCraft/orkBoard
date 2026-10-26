"""Spec 92 on the real host (docs/specs/92-running-and-the-team.md §3, §4): Orkboard's own host and server on a fixture repository, no stub, in Chromium at 1 440 × 900. A project with no party has the
*Operations* row and the line *Make it a Team party*; the line opens New party on Team; Save makes the party, the row and the line go, and the Team party's Board is the real Operations list; the
person's note says where it is (`~/.config/orkcraft/ops/team.json`, never in the repository); Team is then greyed in New party; removing the party gives the row back."""
from __future__ import annotations

import subprocess

import pytest

playwright = pytest.importorskip("playwright.sync_api")

from orkboard.gui.board_host import Orkboard  # noqa: E402
from orkboard.gui.server import Server  # noqa: E402
from orkboard.realm import op_runs, ops_team  # noqa: E402
from tests.browser_kit import WAIT_MS, launch  # noqa: E402

pytestmark = pytest.mark.browser

OPS_ROW = '.arena-phead[data-goal="@operations"]'


@pytest.fixture
def board(tmp_path, monkeypatch):
    for key, value in {"ORKCRAFT_SETTINGS_FILE": tmp_path / "settings.json", "ORKCRAFT_ONBOARDING": "0", "ORKCRAFT_LIMITS": "0", "ORKCRAFT_NO_UPDATE": "1",
                       "XDG_CONFIG_HOME": tmp_path / "config"}.items():
        monkeypatch.setenv(key, str(value))
    repo = tmp_path / "project"
    (repo / "src").mkdir(parents=True)
    (repo / "README.md").write_text("# Demo project\n", encoding="utf-8")
    git = ["git", "-c", "user.email=test@orkcraft.local", "-c", "user.name=Test Runner"]
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "init"], cwd=repo, check=True)
    return Orkboard(repo)


def test_a_team_party_made_on_the_real_host_takes_the_operations_row_away_shows_the_real_list_and_removing_it_gives_the_row_back(board):
    server = Server(board)
    thread = server.start_thread()
    with playwright.sync_playwright() as p:
        browser = launch(p)
        try:
            pg = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
            pg.set_default_timeout(WAIT_MS)
            errors: list[str] = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(server.url)
            pg.get_by_text("No parties yet").wait_for()
            pg.locator(OPS_ROW).wait_for()
            line = pg.get_by_role("button", name="Make it a Team party")
            assert line.count() == 1
            line.click()
            dlg = pg.get_by_role("dialog", name="New party")
            dlg.locator(".shell-preset").first.wait_for()
            assert dlg.locator(".shell-preset[aria-pressed=true]").get_attribute("data-craft") == "team"
            dlg.get_by_role("button", name="Save party").click()
            pg.locator(".arena[data-team=true] .board-ops").wait_for()                          # the real Operations list in the Team party's field
            assert pg.locator(OPS_ROW).count() == 0 and pg.get_by_role("button", name="Make it a Team party").count() == 0
            note = ops_team.get(op_runs.root())
            assert note and note["project"] == str(board.repo_root) and note["party"] == "team"
            assert not list(board.repo_root.rglob("team.json"))                                  # the note is the person's, never in the repository
            tracks = board.command("ideas.board")["tracks"]
            assert next(t for t in tracks if t["slug"] == "team")["recipe"] == "team"
            assert board.snapshot()["ops_team"] == {"name": board.repo_root.name, "party": "team", "here": True}
            pg.get_by_role("button", name="New party", exact=True).click()                       # the left column's New party: Team is there, greyed
            again = pg.get_by_role("dialog", name="New party")
            again.locator(".shell-preset").first.wait_for()
            off = again.locator('.shell-preset[data-craft="team"]')
            assert off.is_disabled() and off.locator("[data-blocked]").inner_text() == "Team is in this project"
            pg.keyboard.press("Escape")
            board.command("ideas.track_drop", {"slug": "team"})                                  # removed: Operations are in the column again
            pg.locator(OPS_ROW).wait_for()
            pg.get_by_role("button", name="Make it a Team party").wait_for()
            assert ops_team.get(op_runs.root()) is None
            assert not errors, errors
        finally:
            browser.close()
            server.stop()
            thread.join(10)
