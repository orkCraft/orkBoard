"""**To main** asks the checks first, with no Release party seated (docs/specs/158-the-window-as-a-table.md stage D, decisions §274), in a real browser against the portal's stub with Release taken out:
the discard's To main (and the portal) asks `ideas.to_main_checks` and sends `ideas.to_main` only when they are green, at both widths; a red check's words name the test and nothing is sent; a project with no tests is refused by the host and the
card offers *To main without the tests*, the only press that sends `untested: true`; the merge of dev whole (`ideas.gate_merge`) says *Running the tests…* while the host runs them and says a red in words."""
from __future__ import annotations

import pytest
import json

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import open_hand  # noqa: E402
from tests.test_portal_browser import PortalHost, lane_card, open_lane, picked_is, tomain  # noqa: E402
from tests.test_shell_browser import _sent  # noqa: E402

pytestmark = pytest.mark.browser

NO_TESTS = "This project has no tests, so nothing can show the goal is safe for main: send it with To main without the tests"
NOT_RUN = "Its checks have not been run: run the checks on the way into main first"
UNTESTED = "To main without the tests"


class NoReleaseHost(PortalHost):
    """The portal's project with no Release party seated (stage C made it removable); the host answers as ideas_gate.py does: a goal whose checks were not asked is refused."""

    def __init__(self):
        super().__init__()
        self.parties = [p for p in self.parties if p["slug"] != "release"]
        self.checked = False
        self.red = False
        self.no_tests = False

    def handle(self, name, a):
        if name == "ideas.to_main_checks":
            self.log.append((name, a))
            self.checked = True
            tests = {"name": "Tests", "state": "failed", "words": "tests/test_player.py::test_lobby_opens failed (1 of 12)"} if self.red else {"name": "Tests", "state": "passed", "words": ""}
            return {"idea": a["idea"], "running": False, "checks": [{"name": "The merge", "state": "passed", "words": ""}, tests]}
        if name == "ideas.to_main" and not a.get("untested"):
            if not self.checked:
                self.log.append((name, a))
                return {"error": NOT_RUN}
            if self.no_tests:
                self.log.append((name, a))
                return {"error": NO_TESTS}
        if name == "ideas.gate_merge" and self.red:
            self.log.append((name, a))
            return {"error": "Sealed: Tests is red: tests/test_player.py::test_lobby_opens failed (1 of 12)"}
        return super().handle(name, a)



class DeferredRetryHost(NoReleaseHost):
    """Hold the retry reply without blocking Playwright's synchronous event handler."""

    def __init__(self):
        super().__init__()
        self.retry_reply = None

    def on_socket(self, ws):
        super().on_socket(ws)

        def on_message(raw):
            message = json.loads(raw)
            reply = {"t": "reply", "id": message["id"], "ok": True,
                     "result": self.handle(message["name"], message["args"])}
            if message["name"] == "ideas.to_main_checks" and message["args"].get("again"):
                self.retry_reply = reply
            else:
                ws.send(json.dumps(reply))
        ws.on_message(on_message)

    def finish_retry(self):
        assert self.retry_reply is not None, "the explicit retry must have reached the host"
        self.ws.send(json.dumps(self.retry_reply))
        self.retry_reply = None


def names(host):
    return [n for n, _ in host.log if n in ("ideas.to_main_checks", "ideas.to_main")]


def narrow_view(gui, host):
    """The narrow window with the discard's view open (the pile pressed)."""
    pg, host, log = open_hand(gui, host=host, width="narrow")
    pile = pg.locator(".table-end .hand-done")
    pile.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    pile.click()
    pg.locator(".portal-cards").wait_for(timeout=WAIT_MS)
    return pg, host, log


def press_to_main(pg, width, slug="music"):
    """Opens the goal's card and presses what sends it: the table's To main at the wide width, the portal at the narrow."""
    if width == "wide":
        lane_card(pg, slug).click()
        picked_is(pg, slug)
        pg.locator("[data-tomain] [data-to-main]").click()
    else:
        pg.locator(f'[data-portal-card="{slug}"]').click()
        pg.locator(".portal-host .ork-portal").click()


def test_the_portal_asks_the_checks_then_sends_with_no_release_seated_at_the_narrow_width(gui):
    pg, host, log = narrow_view(gui, NoReleaseHost())
    try:
        press_to_main(pg, "narrow", "codes")
        assert _sent(pg, host, ("ideas.to_main", {"idea": "codes"}))
        assert names(host) == ["ideas.to_main_checks", "ideas.to_main"], "the checks are asked first, then the goal is sent"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_discards_to_main_asks_the_checks_then_sends_at_the_narrow_width(gui):
    pg, host, log = narrow_view(gui, NoReleaseHost())
    try:
        pg.locator(".hand-part__head [data-to-main]").click()
        assert _sent(pg, host, ("ideas.to_main", {"idea": "music"}))
        assert names(host) == ["ideas.to_main_checks", "ideas.to_main"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_to_main_on_the_table_asks_the_checks_then_sends_at_the_wide_width(gui):
    pg, host, log = open_lane(gui, NoReleaseHost())
    try:
        press_to_main(pg, "wide")
        assert _sent(pg, host, ("ideas.to_main", {"idea": "music"}))
        assert names(host) == ["ideas.to_main_checks", "ideas.to_main"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", ["narrow", "wide"])
def test_a_red_check_names_the_test_and_nothing_is_sent(gui, width):
    host = NoReleaseHost()
    host.red = True
    pg, host, log = open_lane(gui, host) if width == "wide" else narrow_view(gui, host)
    try:
        if width == "wide":
            lane_card(pg, "music").click()
        else:
            press_to_main(pg, width)
        where = tomain(pg) if width == "wide" else pg.locator(".portal-host")
        where.get_by_text("tests/test_player.py::test_lobby_opens failed").first.wait_for(timeout=WAIT_MS)
        assert "Tests is red" in where.text_content()
        pg.wait_for_timeout(400)
        assert "ideas.to_main" not in names(host), "a red check sends nothing"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", ["narrow", "wide"])
def test_a_project_with_no_tests_offers_to_main_without_the_tests_and_only_that_press_sends_untested(gui, width):
    host = NoReleaseHost()
    host.no_tests = True
    pg, host, log = open_lane(gui, host) if width == "wide" else narrow_view(gui, host)
    try:
        press_to_main(pg, width)
        btn = pg.locator("[data-to-main-untested]")
        btn.wait_for(timeout=WAIT_MS)
        assert btn.text_content() == UNTESTED
        assert pg.locator("[data-stopped]").text_content() == NO_TESTS
        assert [a for n, a in host.log if n == "ideas.to_main"] == [{"idea": "music"}], "the first press sent no `untested`"
        btn.click()
        assert _sent(pg, host, ("ideas.to_main", {"idea": "music", "untested": True}))
        pg.wait_for_function("() => document.querySelectorAll('[data-portal-card=\"music\"]').length === 0", timeout=WAIT_MS)
    finally:
        pg.close()
    assert all("no tests" in m for m in log), "\n".join(log)


def test_the_merge_of_dev_says_the_tests_run_while_they_do_and_a_red_in_words(gui):
    host = NoReleaseHost()
    host.red = True
    pg, host, log = open_lane(gui, host)
    try:
        said = pg.evaluate("""async () => {
          const m = await import('/static/js/arena/gate.js'), p = m.mergeGate(), during = [m.testing.value, m.TESTING];
          await p;
          return [...during, m.testing.value];
        }""")
        assert said == [True, "Running the tests…", False], "the running state shows while the host runs the tests and ends with the answer"
        pg.get_by_text("Tests is red: tests/test_player.py::test_lobby_opens failed").first.wait_for(timeout=WAIT_MS)
    finally:
        pg.close()
    assert all("Tests is red" in m for m in log), "\n".join(log)


def test_red_survives_reselection_and_only_test_again_retries(gui):
    host = DeferredRetryHost()
    host.red = True
    pg, host, log = open_lane(gui, host)
    try:
        lane_card(pg, "music").click()
        retry = tomain(pg).get_by_role("button", name="Test again", exact=True)
        retry.wait_for(timeout=WAIT_MS)
        assert tomain(pg).locator("[data-to-main]").is_disabled()
        count = names(host).count("ideas.to_main_checks")
        pg.evaluate("async () => { const p = await import('/static/js/table/portal.js'); p.close(); p.choose('music'); }")
        retry.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert not any(a.get("again") for n, a in host.log if n == "ideas.to_main_checks")
        assert "ideas.to_main" not in names(host)
        host.red = False
        retry.click()
        tomain(pg).get_by_text("Checking the way into main", exact=True).wait_for(timeout=WAIT_MS)
        assert tomain(pg).locator("[data-to-main]").is_disabled()
        assert "ideas.to_main" not in names(host)
        assert _sent(pg, host, ("ideas.to_main_checks", {"idea": "music", "again": True}))
        host.finish_retry()
        pg.wait_for_function("() => !document.querySelector('[data-tomain] [data-to-main]')?.disabled", timeout=WAIT_MS)
        assert any(a.get("again") is True for n, a in host.log if n == "ideas.to_main_checks")
        assert names(host).count("ideas.to_main_checks") > count
        tomain(pg).locator("[data-to-main]").click()
        assert _sent(pg, host, ("ideas.to_main", {"idea": "music"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_green_test_again_lifts_the_seal_the_gates_row_still_says(gui):
    """Trial 152 E's review: the gate's row says `main_ready: false` as the Board was read, and is not read again when a check ends; a Test again that
    passes lifts the seal on the goal's card and in the discard all the same."""
    host = NoReleaseHost()
    host.red = True
    for row in host.gate_doc["ideas"]:
        if row["slug"] == "music":
            row.update(main_ready=False, main_reason="tests/test_player.py::test_lobby_opens failed (1 of 12)")
    pg, host, log = open_lane(gui, host)
    try:
        assert lane_card(pg, "music").get_attribute("aria-label").endswith("checks failed"), "the row's word before any check is followed here"
        lane_card(pg, "music").click()
        retry = tomain(pg).get_by_role("button", name="Test again", exact=True)
        retry.wait_for(timeout=WAIT_MS)
        host.red = False
        retry.click()
        pg.wait_for_function("() => document.querySelector('.release-lane [data-portal-card=\"music\"]')?.getAttribute('aria-label').endsWith('ready for main')", timeout=WAIT_MS)
        assert "Checks failed" not in lane_card(pg, "music").text_content()
        assert not tomain(pg).locator("[data-to-main]").is_disabled()
    finally:
        pg.close()
    assert not log, "\n".join(log)
