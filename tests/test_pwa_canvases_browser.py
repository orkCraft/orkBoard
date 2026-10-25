"""Spec 78 part C, the phone (docs/specs/78-canvases.md §4, §7; decisions §93): Chromium at 390 × 844, paired over the phone listener, against the real canvas store of the project (the Board's other
commands are the stub's). No canvases: no row; some: the fold row *Canvases · n* (n the ones not seen), folded at first, above what waits for you; a line is the elf's small head, the kind, the title in
the text face, the tool and what a tap does; a link opens in the phone's browser (an allowed host's only: another host's is text, never a link); a picture shows in a sheet; a page is never shown on
the phone; *Seen* lowers the count and folds the line under *Seen*; no sideways scroll, every tap 44 px; `sw.js` v86."""
from __future__ import annotations

import base64
from pathlib import Path

import pytest

from orkboard.gui import pwa
from orkboard.gui.board_host import BoardPhone
from orkboard.sources.canvases import Canvas
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, _phone  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
CLAUDE = "https://claude.ai/artifact/0f3c"
FIGMA = "https://www.figma.com/design/abc/Onboarding"
FAR = "https://evil.example.com/steal"


def host_of(monkeypatch) -> dict:
    """The phone's snapshot as the host would say it with the canvases' count and rev (gui/ideas.py `snapshot`), and the host the listener serves, for the test to add canvases to."""
    got: dict = {}
    real = BoardPhone.phone_snapshot

    def snap(host):
        s = real(host)
        got["host"] = host
        full = host.snapshot()
        return {**s, "canvases_new": full["canvases_new"], "canvases_rev": full["canvases_rev"], "rev": f"{s['rev']}-c{full['canvases_rev']}"}
    monkeypatch.setattr(BoardPhone, "phone_snapshot", staticmethod(snap))
    return got


def made(fake_repo: Path, got: dict) -> list[Canvas]:
    """Four canvases: Claude's design (a link), Figma's, a picture Codex drew (a file of the project), a page of Claude's (a file) and a picture whose link is of another host."""
    (fake_repo / "elf.png").write_bytes(PNG)
    (fake_repo / "page.html").write_text("<h1>Not for the phone</h1>", encoding="utf-8")
    cs = [Canvas("claude", "design", "Onboarding flow", "2026-10-25T10:00:00+00:00", url=CLAUDE, model="claude-opus-5-5"),
          Canvas("claude", "design", "Settings screen", "2026-10-25T10:10:00+00:00", url=FIGMA),
          Canvas("codex", "picture", "A pixel elf", "2026-10-25T10:20:00+00:00", file=str(fake_repo / "elf.png")),
          Canvas("claude", "page", "Landing draft", "2026-10-25T10:30:00+00:00", file=str(fake_repo / "page.html")),
          Canvas("agy", "picture", "Far away", "2026-10-25T10:40:00+00:00", url=FAR)]
    for c in cs:
        assert got["host"].ideas.canvas_store.add(c)
    return cs


async def _row(page, stub, n):
    stub.bump({})
    await page.locator(f'.cv:not([hidden]) .gfold__n:text-is("· {n}")').wait_for(timeout=WAIT_MS * 2)


@pytest.mark.asyncio
async def test_no_canvases_no_row_and_with_some_a_row_folded_at_first_with_its_count(fake_repo, monkeypatch):
    got = host_of(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.wait_for_timeout(800)
        assert await page.locator(".cv").count() == 1 and await page.locator(".cv").is_hidden()            # nothing drawn: no row
        made(fake_repo, got)
        await _row(page, stub, 5)
        head = page.locator(".cv .gfold__head")
        assert await head.get_attribute("aria-expanded") == "false" and await head.get_attribute("aria-label") == "Canvases 5"
        assert (await page.locator(".cv .gfold__word").inner_text()).strip().lower() == "canvases"
        assert await page.locator(".cv-list").is_hidden() and await page.locator(".cv__line").count() == 0    # folded
        assert (await head.bounding_box())["height"] >= 44 and await page.evaluate(NO_SCROLL)
        stops, row = await page.locator(".handzone").bounding_box(), await page.locator(".cv").bounding_box()
        assert row["y"] + row["height"] <= stops["y"] + 1                                                       # above what waits for you


@pytest.mark.asyncio
async def test_a_line_says_its_kind_its_title_and_its_tool_and_what_a_tap_does(fake_repo, monkeypatch):
    got = host_of(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        made(fake_repo, got)
        await _row(page, stub, 5)
        await page.locator(".cv .gfold__head").click()
        lines = page.locator(".cv__line")
        await lines.first.wait_for(timeout=WAIT_MS)
        assert await lines.count() == 5 and await page.locator(".cv__line.is-seen").count() == 0
        first = lines.first                                                                                    # newest first
        assert await first.get_attribute("data-key") == f"agy:{FAR}"
        by = {await l.locator(".cv__title").inner_text(): l for l in await lines.all()}
        design = by["Onboarding flow"]
        assert (await design.locator(".cv__kind").inner_text()).strip().lower() == "design"
        assert "Claude · Open on claude.ai" in " ".join((await design.locator(".cv__sub").inner_text()).split())
        assert await design.locator(".cv__top img.ork-race__head.small").count() == 1                          # design's race, small
        assert "elf" in await design.locator(".cv__top img").get_attribute("src")
        font = await design.locator(".cv__title").evaluate("(e) => getComputedStyle(e).fontFamily")
        assert "pixel" not in font.lower()                                                                     # a title someone wrote is never in the pixel face
        assert "Open in Figma" in await by["Settings screen"].locator(".cv__sub").inner_text()
        assert "Show picture" in await by["A pixel elf"].locator(".cv__sub").inner_text() and "Codex" in await by["A pixel elf"].locator(".cv__sub").inner_text()
        page_line = by["Landing draft"]                                                                        # a page: no tap beyond a link, and it has none
        assert await page_line.locator("a, button.cv__main").count() == 0 and await page_line.locator(".cv__main.is-still").count() == 1
        far = by["Far away"]                                                                                   # another host's link: text, never a link
        assert await far.locator("a").count() == 0 and FAR in await far.locator(".cv__sub").inner_text() and "Antigravity" in await far.locator(".cv__sub").inner_text()
        assert await by["Onboarding flow"].locator("a").get_attribute("href") == CLAUDE
        for b in await page.locator(".cv__line a, .cv__line button").all():
            assert (await b.bounding_box())["height"] >= 44
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_link_opens_in_the_phones_browser_and_a_picture_shows_in_a_sheet(fake_repo, monkeypatch):
    got = host_of(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        async def hosted(route):
            await route.fulfill(status=200, content_type="text/html", body="<p>claude</p>")
        await page.context.route("https://claude.ai/**", hosted)
        made(fake_repo, got)
        await _row(page, stub, 5)
        await page.locator(".cv .gfold__head").click()
        link = page.locator('.cv__line:has(.cv__title:text-is("Onboarding flow")) a')
        await link.wait_for(timeout=WAIT_MS)
        assert await link.get_attribute("target") == "_blank" and "noopener" in await link.get_attribute("rel")
        async with page.context.expect_page(timeout=WAIT_MS) as opened:
            await link.click()
        popup = await opened.value
        assert popup.url.startswith(CLAUDE) and page.url.startswith("https://") and "claude.ai" not in page.url        # the app stays where it was
        await popup.close()
        await page.locator('.cv__line:has(.cv__title:text-is("A pixel elf")) .cv__main').click()
        sheet = page.locator("dialog.sheet[open]")
        await sheet.wait_for(timeout=WAIT_MS)
        img = sheet.locator("img.cv-pic")
        await page.wait_for_function("() => document.querySelector('.cv-pic') && document.querySelector('.cv-pic').naturalWidth > 0", timeout=WAIT_MS)
        assert (await img.get_attribute("src")).startswith("data:image/png;base64,") and await img.get_attribute("alt") == "A pixel elf"
        assert "A pixel elf" in await sheet.locator(".cv-pic__title").inner_text()
        await sheet.get_by_role("button", name="Close").click()
        await sheet.wait_for(state="hidden", timeout=WAIT_MS)


@pytest.mark.asyncio
async def test_seen_lowers_the_count_and_folds_the_line_under_seen(fake_repo, monkeypatch):
    got = host_of(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        made(fake_repo, got)
        await _row(page, stub, 5)
        await page.locator(".cv .gfold__head").click()
        line = page.locator('.cv__line:has(.cv__title:text-is("Onboarding flow"))')
        await line.locator('button[data-act="seen"]').click()
        await page.locator('.cv .gfold__n:text-is("· 4")').wait_for(timeout=WAIT_MS)
        await page.locator(".cv__line.is-seen").wait_for(timeout=WAIT_MS)
        assert await page.locator(".cv__line").count() == 5 and await page.locator(".cv__line:not(.is-seen)").count() == 4
        assert await page.locator(".cv__line.is-seen .cv__title").inner_text() == "Onboarding flow"
        assert await page.locator(".cv__line.is-seen button[data-act=seen]").count() == 0                       # seen: nothing to press
        assert got["host"].ideas.canvas_store.new_count() == 4
        for _ in range(4):                                                                                     # all seen: the row stays (they are on the Board), at zero
            await page.locator('.cv__line:not(.is-seen) button[data-act="seen"]').first.click()
            await page.wait_for_timeout(150)
        await page.locator('.cv .gfold__n:text-is("· 0")').wait_for(timeout=WAIT_MS)
        assert await page.locator(".cv__none").inner_text() == "All seen." and not await page.locator(".cv").is_hidden()
        assert await page.evaluate(NO_SCROLL)


def test_the_service_worker_is_one_up_and_keeps_the_new_file():
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert 'const CACHE = "orkcraft-app-v86";' in sw and '"shell-canvases.js"' in sw[sw.index("const SHELL"):sw.index("];", sw.index("const SHELL"))]
