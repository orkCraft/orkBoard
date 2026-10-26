"""Canvases on the desktop (docs/specs/78-canvases.md §3, Tests → B; a kind of Assets since docs/specs/90-what-the-first-look-said.md §2.3), in a real browser at 1 440 × 900 against Orkboard's
own host on a fixture project: the section *Canvases* among Assets' kinds (none with no canvases, the count of what is not seen), a card's words (the elf's small head, the kind, the title in the text face, the tool and
when), *Open on claude.ai* in the person's browser, a link of another host as text, *Show here* (a picture, a page in a sandbox with no scripts, Markdown as text), *Seen* into *Seen* with
the count down, and a canvas that arrives while the page is seen drawing in once (none under reduced motion)."""
from __future__ import annotations

import base64
import datetime as dt
import subprocess

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.gui.board_host import Orkboard  # noqa: E402
from orkboard.gui.server import Server  # noqa: E402
from orkboard.sources.canvases import Canvas  # noqa: E402
from tests.browser_kit import WAIT_MS, launch, playwright  # noqa: E402

pytestmark = pytest.mark.browser

ART = "https://claude.ai/artifact/0f3c"
FIGMA = "https://www.figma.com/design/abc/Onboarding"
ELSEWHERE = "https://example.com/board/42"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
PAGE = "<!doctype html><title>Pricing</title><h1>Plans</h1><script>document.title = 'ran'</script>"


def _ago(minutes: int) -> str:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=minutes)).isoformat(timespec="seconds")


@pytest.fixture
def board(tmp_path, monkeypatch):
    """Orkboard on a fixture project that has a party, a picture, a page and a note under it."""
    for key, value in {"ORKCRAFT_SETTINGS_FILE": tmp_path / "settings.json", "ORKCRAFT_LOOK": "office", "ORKCRAFT_ONBOARDING": "0", "ORKCRAFT_LIMITS": "0",
                       "ORKCRAFT_NO_UPDATE": "1", "ORKCRAFT_MODEL_LIST": "0", "XDG_CONFIG_HOME": tmp_path / "config", "XDG_CACHE_HOME": tmp_path / "cache",
                       "ORKCRAFT_STATE_DIR": tmp_path / "state", "CODEX_HOME": tmp_path / "codex", "HOME": tmp_path}.items():
        monkeypatch.setenv(key, str(value))
    repo = tmp_path / "project"
    (repo / "art").mkdir(parents=True)
    (repo / "README.md").write_text("# Demo project\n", encoding="utf-8")
    (repo / "art" / "mark.png").write_bytes(PNG)
    (repo / "art" / "pricing.html").write_text(PAGE, encoding="utf-8")
    (repo / "art" / "notes.md").write_text("# Notes\n\n- one\n", encoding="utf-8")
    git = ["git", "-c", "user.email=test@orkcraft.local", "-c", "user.name=Test Runner"]
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "init"], cwd=repo, check=True)
    host = Orkboard(repo)
    host.command("ideas.goal_save", {"about": "More people try it.", "priority": "high"})
    return host, repo


@pytest.fixture
def desk(board):
    """(page, host, repo, errors): the window open on the project's Assets (spec 90 §2.3), the host's canvases still empty."""
    host, repo = board
    server = Server(host)
    thread = server.start_thread()
    pw = playwright.sync_playwright().start()
    browser = launch(pw)
    errors: list[str] = []
    try:
        pg = browser.new_page(viewport={"width": 1440, "height": 900})
        pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        pg.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
        pg.goto(server.url)
        pg.get_by_role("button", name="The project").click()
        pg.get_by_role("tab", name="Assets").click()
        pg.locator(".assets[data-state=shown]").wait_for(timeout=WAIT_MS)
        yield pg, host, repo, errors
    finally:
        browser.close()
        pw.stop()
        server.stop()
        thread.join(10)
    assert not errors, "\n".join(errors)


def _add(host, **kw):
    kw.setdefault("title", "Onboarding")
    return host.ideas.canvas_store.add(Canvas(kw.pop("tool", "claude"), kw.pop("kind", "design"), kw.pop("title"), kw.pop("at", _ago(4)), **kw))


def _row(pg):
    return pg.locator('.assets-sec[data-kind="canvas"]')


def _unfold(pg):
    """The section's cards, once the host's canvases are read (no fold: a kind of Assets lies open)."""
    _row(pg).wait_for(timeout=WAIT_MS)
    pg.locator(".arena-canvas").first.wait_for(timeout=WAIT_MS)


def _count(pg):
    return _row(pg).locator(".assets-sec__n").inner_text()


def _card(pg, key):
    return pg.locator(f'.arena-canvas[data-key="{key}"]')


# -- the section (§3.1, spec 90 §2.3) --------------------------------------------------------------------------------------------------

def test_no_canvases_no_section(desk):
    pg, host, repo, errors = desk
    pg.wait_for_timeout(400)
    assert pg.locator(".arena-canvases").count() == 0
    assert pg.get_by_role("group", name="Kinds").get_by_role("button", name="Canvases").count() == 0


def test_the_section_is_a_kind_of_assets_after_the_files_with_the_count_of_what_is_not_seen_and_signals_nothing(desk):
    pg, host, repo, errors = desk
    _add(host, url=ART)
    _add(host, url=FIGMA, tool="codex", kind="design", title="Checkout")
    _unfold(pg)
    assert _row(pg).locator("h3").text_content().strip() == "Canvases 2" and pg.locator(".arena-canvas").count() == 2
    assert [x.get_attribute("aria-label") for x in pg.locator(".assets-sec").all()][-1] == "Canvases"                       # after the project's files
    assert pg.get_by_role("group", name="Kinds").get_by_role("button", name="Canvases").count() == 1
    assert pg.locator(".shell-top").inner_text().count("Canvases") == 0 and pg.locator(".shell-top .ork-count").count() == 0         # nothing in the top bar


# -- the card (§3.2) ----------------------------------------------------------------------------------------------------------------

def test_a_card_is_a_frame_with_the_elfs_small_head_its_kind_its_title_in_the_text_face_its_tool_and_when(desk):
    pg, host, repo, errors = desk
    _add(host, url=ART, title="Onboarding, v2", model="claude-sonnet-4-5")
    _unfold(pg)
    card = _card(pg, f"claude:{ART}")
    assert "ork-frame" in card.get_attribute("class")
    head = card.locator("img.ork-race__head.small")
    assert head.count() == 1 and "elf-" in head.get_attribute("src") and head.get_attribute("title").endswith("elf · Design")      # design's race, small, its words in its title
    assert card.locator(".arena-canvas__kind").inner_text().lower() == "design"                                                         # the kind (small caps by the label type)
    assert card.locator(".arena-canvas__title").inner_text() == "Onboarding, v2"
    assert card.locator(".arena-cap").first.inner_text() == "Claude · 4 min ago"
    fonts = card.evaluate("""(c) => [getComputedStyle(c.querySelector('.arena-canvas__kind')).fontFamily, getComputedStyle(c.querySelector('.arena-canvas__title')).fontFamily]""")
    token = pg.evaluate("""(n) => { const i = document.createElement('i'); i.style.fontFamily = `var(${n})`; document.body.append(i); const f = getComputedStyle(i).fontFamily; i.remove(); return f; }""",
                        "--ork-font-text")
    assert fonts[1] == token and fonts[0] != token                                                                                      # a title is never in the pixel face
    colours = card.evaluate("""(c) => [...c.querySelectorAll('*')].map((e) => getComputedStyle(e).color)""")
    alert = pg.evaluate("""() => { const i = document.createElement('i'); i.style.color = 'var(--ork-alert)'; document.body.append(i); const c = getComputedStyle(i).color; i.remove(); return c; }""")
    assert alert not in colours                                                                                                         # not a signal


# -- what it offers (§3.3) ----------------------------------------------------------------------------------------------------------

def test_open_on_claude_ai_opens_the_link_in_the_persons_browser(desk, monkeypatch):
    pg, host, repo, errors = desk
    opened: list[str] = []
    monkeypatch.setattr("orkboard.gui.ideas_canvases.webbrowser.open", lambda url, *a, **k: opened.append(url) or True)
    _add(host, url=ART)
    _add(host, url=FIGMA, kind="design", title="Checkout", at=_ago(1))
    _unfold(pg)
    assert _card(pg, f"claude:{ART}").get_by_role("button", name="Open on claude.ai").count() == 1
    assert _card(pg, f"claude:{FIGMA}").get_by_role("button", name="Open in Figma").count() == 1                                        # the word follows the host
    _card(pg, f"claude:{ART}").get_by_role("button", name="Open on claude.ai").click()
    pg.wait_for_function("() => true")
    for _ in range(100):
        if opened:
            break
        pg.wait_for_timeout(50)
    assert opened == [ART]


def test_a_link_of_another_host_is_text_never_a_link(desk):
    pg, host, repo, errors = desk
    _add(host, url=ELSEWHERE, title="Board 42")
    _unfold(pg)
    card = pg.locator(".arena-canvas")
    assert card.locator(".arena-canvas__text").inner_text() == ELSEWHERE
    assert card.locator("a").count() == 0 and card.get_by_role("button", name="Open", exact=False).count() == 0 and card.get_by_role("button", name="Show here").count() == 0


def test_show_here_shows_a_picture_in_the_preview(desk):
    pg, host, repo, errors = desk
    _add(host, tool="agy", kind="picture", title="The mark", file=str(repo / "art" / "mark.png"))
    _unfold(pg)
    card = pg.locator(".arena-canvas")
    assert card.locator(".arena-canvas__kind").inner_text().lower() == "picture"
    card.get_by_role("button", name="Show here").click()
    pic = pg.locator(".shell-preview .arena-cview__pic")
    pic.wait_for(timeout=WAIT_MS)
    assert pic.get_attribute("src").startswith("data:image/png;base64,") and pic.get_attribute("alt") == "The mark"
    assert "The mark" in pg.locator(".shell-ptab.is-on").inner_text()                                                                   # the tab says what it holds


def test_show_here_shows_a_page_in_a_sandbox_with_no_scripts_and_markdown_as_text(desk):
    pg, host, repo, errors = desk
    _add(host, tool="claude", kind="page", title="Pricing", file=str(repo / "art" / "pricing.html"), at=_ago(2))
    _add(host, tool="claude", kind="document", title="Notes", file=str(repo / "art" / "notes.md"), at=_ago(9))
    _unfold(pg)
    pg.locator('.arena-canvas', has_text="Pricing").get_by_role("button", name="Show here").click()
    frame = pg.locator(".shell-preview iframe.arena-cview__page")
    frame.wait_for(timeout=WAIT_MS)
    assert frame.get_attribute("sandbox") == "" and "<h1>Plans</h1>" in frame.get_attribute("srcdoc")                                    # no allow-scripts, no allow-same-origin
    inner = pg.frame_locator(".shell-preview iframe.arena-cview__page")
    inner.locator("h1").wait_for(timeout=WAIT_MS)
    assert inner.locator("h1").inner_text() == "Plans" and inner.locator("html").evaluate("e => document.title") != "ran"                # its script never ran
    pg.get_by_role("button", name="Close the right column").click()
    pg.locator('.arena-canvas', has_text="Notes").get_by_role("button", name="Show here").click()
    pre = pg.locator(".shell-preview pre")
    pre.wait_for(timeout=WAIT_MS)
    assert "# Notes" in pre.inner_text() and pg.locator(".shell-preview iframe").count() == 0
    blocked = [e for e in errors if "Blocked script execution" in e]
    assert blocked and all("sandboxed" in e for e in blocked)                                                                           # the browser refused its script: the one console line this page may have
    errors[:] = [e for e in errors if e not in blocked]


def test_a_file_outside_the_project_has_no_show_here(desk, tmp_path):
    pg, host, repo, errors = desk
    outside = tmp_path / "elsewhere.png"
    outside.write_bytes(PNG)
    _add(host, tool="agy", kind="picture", title="Elsewhere", file=str(outside))
    _unfold(pg)
    assert pg.locator(".arena-canvas").get_by_role("button", name="Show here").count() == 0


def test_seen_moves_a_canvas_into_seen_and_the_count_drops(desk):
    pg, host, repo, errors = desk
    _add(host, url=ART)
    _add(host, url=FIGMA, title="Checkout", at=_ago(1))
    _unfold(pg)
    assert _count(pg) == "2" and pg.locator('.arena-frow[data-fold="seen"]').count() == 0
    _card(pg, f"claude:{ART}").get_by_role("button", name="Seen").click()
    pg.wait_for_function("() => document.querySelector('.assets-sec[data-kind=canvas] .assets-sec__n').innerText === '1'", timeout=WAIT_MS)
    assert pg.locator(".arena-canvas").count() == 1 and _card(pg, f"claude:{ART}").count() == 0
    seen = pg.locator('.arena-frow[data-fold="seen"]')
    assert seen.locator(".arena-frow__n").inner_text() == "· 1" and seen.locator("button").get_attribute("aria-expanded") == "false"
    seen.locator("button").click()
    old = _card(pg, f"claude:{ART}")
    old.wait_for(timeout=WAIT_MS)
    assert old.get_by_role("button", name="Seen").count() == 0 and old.get_by_role("button", name="Open on claude.ai").count() == 1       # no Seen button on a seen one
    _card(pg, f"claude:{FIGMA}").get_by_role("button", name="Seen").click()
    pg.wait_for_function("() => document.querySelector('.assets-sec[data-kind=canvas] .assets-sec__n').innerText === '0'", timeout=WAIT_MS)
    assert _row(pg).count() == 1                                                                                                        # seen ones keep the section: its Seen fold is there


# -- a canvas that arrives (§3.4) ---------------------------------------------------------------------------------------------------

def test_a_canvas_that_arrives_while_the_page_is_seen_draws_in_once_and_the_first_read_draws_nothing(desk):
    pg, host, repo, errors = desk
    _add(host, url=ART)
    pg.reload()                                                                                                                          # the page's first read of the project's canvases
    pg.get_by_role("button", name="The project").click()
    pg.get_by_role("tab", name="Assets").click()
    _unfold(pg)
    assert pg.locator(".arena-canvas.is-drawn").count() == 0                                                                            # the first read: nothing draws in
    pg.evaluate("""() => { window.__drawn = []; new MutationObserver((ms) => { for (const m of ms) for (const n of m.addedNodes) { const c = n.matches && n.matches('.arena-canvas.is-drawn') ? n : null;
      if (c) { const s = getComputedStyle(c); window.__drawn.push({ key: c.dataset.key, name: s.animationName, dur: s.animationDuration, fn: s.animationTimingFunction }); } } }).observe(document.body, { subtree: true, childList: true }); }""")
    _add(host, url=FIGMA, title="Checkout", at=_ago(0))
    pg.wait_for_function("() => window.__drawn.length > 0", timeout=WAIT_MS)
    got = pg.evaluate("() => window.__drawn")
    assert [g["key"] for g in got] == [f"claude:{FIGMA}"]
    assert got[0]["name"] == "arena-rise" and got[0]["dur"] == "0.36s" and got[0]["fn"] == "steps(4)"                                   # once, in steps, at most 0.42 s
    pg.locator(".arena-canvas.is-drawn").wait_for(state="detached", timeout=WAIT_MS)                                                    # then it is drawn as the rest are
    assert pg.locator(".arena-canvas").count() == 2


def test_nothing_draws_in_under_reduced_motion(desk):
    pg, host, repo, errors = desk
    pg.emulate_media(reduced_motion="reduce")
    _add(host, url=ART)
    _unfold(pg)
    _add(host, url=FIGMA, title="Checkout", at=_ago(0))
    pg.locator(f'.arena-canvas[data-key="claude:{FIGMA}"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".arena-canvas.is-drawn").count() == 0
    assert pg.locator(f'.arena-canvas[data-key="claude:{FIGMA}"]').evaluate("e => getComputedStyle(e).animationName") == "none"
