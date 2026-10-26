"""Spec 91 part A on the desktop (docs/specs/91-the-owners-list.md §1, §3, §4; decisions §107), in a real browser at 1 440 × 900: the top bar has the product's name and *Settings* as a word on its left; on its
right one chip for each AI tool (its mark, name, share left and window; a tool not read shows a dash) and *Stop all*, nothing else (no *Agents*, *Files* nor *Spend*, no gear); a chip opens the panel under it
(that tool's line and what used it, today's *Spend*, *Last week*) and Esc or a press elsewhere closes it; *Settings* opens Settings; the Orkmaster's *Assets and files* tab has the switch *Assets* / *Files*, *Files* the project's tree
(a file opens in the right column); a toast stands at the page's foot, centred, and never over a dialog."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_assets_desktop_browser import AssetsHost  # noqa: E402
from tests.test_project_desktop_browser import _project  # noqa: E402
from tests.test_shell_browser import _open, box  # noqa: E402
from tests.test_week_desktop_browser import WEEK  # noqa: E402

pytestmark = pytest.mark.browser

FILES = {"notes.txt": "one\ntwo\n", "README.md": "# Shop\n"}


class BarHost(AssetsHost):
    """The assets test's world with a file tree, and limits for three tools: Claude and Codex read (Claude low), Cursor not."""

    def __init__(self):
        super().__init__(empty=True)
        self.limits = [
            {"provider": "claude", "name": "Claude", "left": 0.18, "rows": [{"window": "5h", "left": 0.62, "reset": "2026-10-26T18:00"}, {"window": "week", "left": 0.18, "reset": "2026-10-30T09:00"}]},
            {"provider": "codex", "name": "Codex", "left": 0.4, "rows": [{"window": "5h", "left": 0.4, "reset": "2026-10-26T18:00"}]},
            {"provider": "cursor", "name": "Cursor", "left": None, "error": "not signed in", "rows": []}]

    def handle(self, name, a):
        if name == "ideas.week_work":
            self.log.append((name, a))
            return dict(WEEK)
        if name == "ideas.usage":
            self.log.append((name, a))
            return {"provider": a["provider"], "window": "5h", "scope": "project", "scopes": ["project"], "outside": 0, "estimated": True, "tokens_only": False,
                    "rows": [{"party": "passkey", "title": "Sign in with a passkey", "share": 12, "tokens": 60_000, "members": []}]}
        if name == "files.tree":
            self.log.append((name, a))
            return {"entries": [{"name": n, "path": n, "dir": False, "secret": False, "ignored": False} for n in FILES]}
        if name == "files.read":
            self.log.append((name, a))
            text = FILES[a["path"]]
            return {"path": a["path"], "kind": "markdown" if a["path"].endswith(".md") else "text", "text": text, "html": f"<p>{text}</p>", "size": len(text), "mtime": 1.0}
        return super().handle(name, a)


@pytest.fixture
def bar(gui):
    pg, host, errors = _open(gui, host=BarHost(), ready=".arena[data-goal=passkey]")
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _toast(pg, text="Saved for the test", seconds=60):
    pg.evaluate("([t, s]) => import('/static/js/link.js').then((m) => m.toast(t, 'information', '', s))", [text, seconds])
    pg.locator(".gui-toast", has_text=text).wait_for(timeout=WAIT_MS)


def test_the_bar_has_the_name_and_settings_on_the_left_and_the_chips_and_stop_all_on_the_right(bar):
    pg, host = bar
    top = pg.locator(".shell-top")
    buttons = [b.get_attribute("aria-label") or b.inner_text().strip() for b in top.get_by_role("button").all()]
    assert buttons == ["Settings", "Claude 18 % left, week", "Codex 40 % left, 5h", "Cursor: limits not read", "Stop all"]
    for gone in ("Agents", "Files", "Spend"):
        assert top.get_by_role("button", name=gone).count() == 0 and gone not in top.inner_text()
    assert top.locator(".ork-icon, svg").count() == 0 and top.get_by_role("button", name="Settings", exact=True).count() == 1       # no gear: Settings is a word
    brand, settings, chips, stop = (box(pg, s) for s in (".shell-top__brand", ".shell-top__settings", ".shell-top__chips", ".shell-top .ork-btn.danger"))
    assert brand["x"] < settings["x"] < chips["x"] < stop["x"]
    chip = top.locator(".shell-top__chip[data-provider=claude]")
    assert chip.inner_text().split() == ["Claude", "18", "%", "week"] and chip.locator("img.ork-mark").count() == 1 and "is-warn" in chip.get_attribute("class")      # the tightest row's window; 20 % or less is the warning
    assert top.locator(".shell-top__chip[data-provider=codex]").get_attribute("class").count("is-") == 1 and "is-ok" in top.locator(".shell-top__chip[data-provider=codex]").get_attribute("class")
    unread = top.locator(".shell-top__chip[data-provider=cursor]")
    assert unread.inner_text().split() == ["Cursor", "—"] and "is-unread" in unread.get_attribute("class")
    assert pg.locator(".shell-top__limits").count() == 0                                                                           # nothing opens at rest


def test_a_chip_opens_the_panel_under_it_with_spend_and_last_week_and_esc_or_a_press_elsewhere_closes_it(bar):
    pg, host = bar
    chip = pg.locator(".shell-top__chip[data-provider=codex]")
    chip.click()
    panel = pg.locator(".shell-top__limits")
    panel.wait_for(timeout=WAIT_MS)
    assert chip.get_attribute("aria-expanded") == "true"
    region = panel.get_by_role("region", name="What is left of Codex")                                                              # the pressed tool's line only
    assert [x.get_attribute("data-provider") for x in region.locator(".arena-limit").all()] == ["codex"] and panel.locator(".arena-limit").count() == 1
    region.locator(".arena-usage__row").first.wait_for(timeout=WAIT_MS)                                                             # and what used it
    assert [a for n, a in host.log if n == "ideas.usage"][-1] == {"provider": "codex", "scope": "project"}
    chips, shown = box(pg, ".shell-top__chips"), panel.bounding_box()
    assert shown["y"] >= chips["y"] + chips["height"] and shown["x"] + shown["width"] <= 1440 + 1                                  # under the chips, inside the window
    assert panel.get_by_role("button", name="Last week").count() == 1 and panel.get_by_role("button", name="Spend today: $2.40. This week's work").count() == 1
    pg.keyboard.press("Escape")
    panel.wait_for(state="detached", timeout=WAIT_MS)
    assert chip.evaluate("e => e === document.activeElement")                                                                      # the focus is back on the chip
    chip.click()
    panel.wait_for(timeout=WAIT_MS)
    pg.locator(".shell-top__brand").click()                                                                                        # a press elsewhere
    panel.wait_for(state="detached", timeout=WAIT_MS)
    chip.click()
    pg.locator(".shell-top__chip[data-provider=claude]").click()                                                                    # another chip: the same panel stays, the same chip closes it
    panel.wait_for(timeout=WAIT_MS)
    assert pg.locator(".shell-top__chip[aria-expanded=true]").count() == 1
    pg.locator(".shell-top__chip[data-provider=claude]").click()
    panel.wait_for(state="detached", timeout=WAIT_MS)


def test_the_spend_line_in_the_panel_opens_the_weeks_work(bar):
    pg, host = bar
    pg.locator(".shell-top__chip").first.click()
    pg.get_by_role("button", name="Spend today: $2.40. This week's work").click()
    pg.get_by_role("dialog", name="This week").wait_for(timeout=WAIT_MS)
    assert pg.locator(".shell-top__limits").count() == 0


def test_settings_is_a_word_that_opens_settings(bar):
    pg, host = bar
    pg.locator(".shell-top").get_by_role("button", name="Settings").click()
    assert pg.get_by_role("dialog", name="Settings").is_visible()
    pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.querySelector('[role=dialog]')", timeout=WAIT_MS)
    assert pg.get_by_role("button", name="Settings").evaluate("e => e === document.activeElement")


def test_with_no_limits_read_one_chip_for_the_spend_opens_the_same_panel(bar):
    pg, host = bar
    host.limits = []
    pg.reload()
    pg.locator(".shell-top__chips").wait_for(timeout=WAIT_MS)
    chips = pg.locator(".shell-top__chip")
    assert chips.count() == 1 and chips.first.get_attribute("aria-label") == "Spend today: $2.40"
    chips.first.click()
    panel = pg.locator(".shell-top__limits")
    panel.wait_for(timeout=WAIT_MS)
    assert panel.get_by_role("button", name="Last week").count() == 1 and panel.locator(".arena-limits").count() == 0


def test_the_orkmasters_assets_and_files_switch_shows_the_tree_and_a_file_opens_in_the_right_column(bar):
    pg, host = bar
    _project(pg)
    tabs = pg.get_by_role("tab")
    assert [t.text_content().strip() for t in tabs.all()] == ["Field", "Assets and files", "Play"]
    pg.get_by_role("tab", name="Assets and files").click()
    pg.locator(".assets").wait_for(timeout=WAIT_MS)
    switch = pg.get_by_role("group", name="Show")
    assets, files = switch.get_by_role("button", name="Assets", exact=True), switch.get_by_role("button", name="Files", exact=True)
    assert assets.get_attribute("aria-pressed") == "true" and files.get_attribute("aria-pressed") == "false"
    tab, sw = box(pg, "#pjpanel"), files.bounding_box()
    assert sw["x"] + sw["width"] > tab["x"] + tab["width"] - 80 and sw["y"] < tab["y"] + 60                                        # at the top right of the tab
    assert pg.locator(".shell-tree").count() == 0
    files.click()
    pg.locator(".shell-tree__row", has_text="notes.txt").wait_for(timeout=WAIT_MS)
    assert files.get_attribute("aria-pressed") == "true" and assets.get_attribute("aria-pressed") == "false" and pg.locator(".assets").count() == 0
    pg.locator(".shell-tree__row", has_text="notes.txt").click()
    pg.locator(".shell-drawer .shell-code").wait_for(timeout=WAIT_MS)                                                              # the file is in the right column
    assert pg.locator(".arena-project").count() == 1
    files.focus()
    pg.keyboard.press("Tab")
    assets.click()                                                                                                                 # back to Assets
    pg.locator(".assets").wait_for(timeout=WAIT_MS)
    assert pg.locator(".shell-tree").count() == 0 and assets.get_attribute("aria-pressed") == "true"


def test_a_toast_stands_at_the_pages_foot_centred(bar):
    pg, host = bar
    _toast(pg)
    toast, win = box(pg, ".gui-toast"), pg.viewport_size
    assert abs((toast["x"] + toast["width"] / 2) - win["width"] / 2) <= 2                                                          # centred
    hand = box(pg, ".arena-stops")
    assert toast["y"] > win["height"] / 2 and toast["y"] + toast["height"] <= hand["y"] + 1                                       # at the foot, not the top, and above the hand
    assert toast["y"] + toast["height"] > hand["y"] - 40


def test_a_toast_never_covers_a_dialog(bar):
    pg, host = bar
    pg.locator(".shell-top").get_by_role("button", name="Settings").click()
    modal = pg.get_by_role("dialog", name="Settings")
    modal.wait_for(timeout=WAIT_MS)
    _toast(pg, "A toast over a dialog")
    _toast(pg, "A second toast")
    toasts, shown = pg.locator(".gui-toasts").bounding_box(), modal.bounding_box()
    assert toasts["y"] >= shown["y"] + shown["height"]                                                                             # below the dialog, foot buttons and all
    assert abs((toasts["x"] + toasts["width"] / 2) - 720) <= 2
    foot = modal.locator(".shell-modal__foot").first
    if foot.count():
        assert toasts["y"] >= foot.bounding_box()["y"] + foot.bounding_box()["height"]
