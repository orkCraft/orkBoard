"""Spec 88 C, the phone (docs/specs/88-assets-and-play.md §0, §7): Chromium at 390 × 844 against the world of tests/test_pwa_project_browser.py with a stub host that answers `ideas.assets` and `ideas.asset_before`
as spec 88 "As built (A)" says. The project's sheet has a section *Assets*: the kinds as rows of 74 px tokens (a stack of more than six files opens in place, *All n* shows a kind whole), the changes since this
device's last look marked with their goal's element (the look kept in `localStorage` once the section was in view), a removed file as a ghost, a token pressed opens the asset's screen (large, playing, *Before* /
*Now*, *Not picked (n)*), Play's place says *Play on the computer*; an older host has no section. No sideways scroll; the service worker's version."""
from __future__ import annotations

import base64
import re
from pathlib import Path

import pytest

from tests import pick_files as pf
from tests.test_pwa_arena_browser import SCENE, _scene, _shot_to  # noqa: F401
from tests.test_pwa_project_browser import _project, hosted
from tests.test_pwa_route_browser import norm, world  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _called, _phone  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

ROOT = Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static" / "pwa"
uri = lambda data: "data:image/png;base64," + base64.b64encode(data).decode()      # noqa: E731
NOW, WAS, OTHER = uri(pf.png(320, 200)), uri(pf.png(20, 20)), uri(pf.png(30, 30))
SMALL = uri(pf.png(16, 16))
HEAD, SINCE = "c" * 40, "a" * 40
GOALS = {"register": {"title": "WebAuthn register", "element": "ice"}, "sync": {"title": "Sync", "element": "lava"}}
PLAYS = "window.__played = []; HTMLMediaElement.prototype.play = function () { window.__played.push(this.tagName); return Promise.resolve(); };"


def asset(id, kind, **more):
    return {"id": id, "kind": kind, "name": id.rsplit("/", 1)[-1], "bytes": 1200, "w": None, "h": None, "seconds": None, "goal": "", "task": "", "at": "2026-10-20T10:00:00",
            "change": "", "url": NOW, **more}


def answer(since=""):
    """`ideas.assets` as the host answers it: the changed first."""
    marked = bool(since)
    art = [asset("art/logo.png", "art", w=320, h=200, goal="register", task="k1", change="changed" if marked else "", url=NOW,
                 others={"goal": "register", "pick": "p1", "picked": "A", "variants": [
                     {"key": "B", "name": "monogram", "mime": "image/png", "w": 30, "h": 30, "seconds": None, "url": OTHER},
                     {"key": "C", "name": "wordmark", "mime": "image/png", "w": 30, "h": 30, "seconds": None, "url": OTHER}]}),
           asset("art/pixel.png", "art", w=16, h=16, url=SMALL),
           *(asset(f"art/more{i}.png", "art", w=20, h=20, url=WAS) for i in range(8)),
           *(asset(f"art/icons/i{i}.png", "art", w=16, h=16, url=SMALL, stack="art/icons", goal="sync" if i == 0 else "", change="added" if marked and i == 0 else "") for i in range(7))]
    listed = [asset("screen:register/k1", "screen", w=320, h=200, goal="register", task="k1", change="added" if marked else "", url=NOW),
              *art,
              asset("audio/sfx/click.wav", "sound", seconds=0.4, url="/media/_asset/x/click.wav"),
              asset("audio/theme.ogg", "music", seconds=94, url="/media/_asset/x/theme.ogg", goal="sync", change="changed" if marked else ""),
              asset("video/intro.mp4", "clip", seconds=12, w=640, h=360, url="/media/_asset/x/intro.mp4"),
              asset("fonts/pixel.ttf", "font", url="/media/_asset/x/pixel.ttf")]
    return {"commit": HEAD, "short": "cccccc", "ref": "dev", "since": SINCE if marked else "",
            "assets": sorted(listed, key=lambda a: not a["change"]),                                                          # the host's order: the changed first
            "removed": [{"id": "art/old.png", "kind": "art", "goal": "register", "task": "k1", "at": "2026-10-21T10:00:00"}] if marked else [],
            "stacks": [{"folder": "art/icons", "kind": "art", "n": 7}], "goals": GOALS}


def assets_host(monkeypatch, empty=False, serves=True):
    """The project's world with the host of spec 88 A: `ideas.assets` and `ideas.asset_before` (the version before of the logo)."""
    hosted(monkeypatch)
    real = Stub.commands

    def commands(self):
        got = real(self)

        def serve(name, run):
            def call(a):
                a = {k: v for k, v in a.items() if k != "link" and k != "device"}
                self.calls.append((name, dict(a)))
                return run(a)
            return call

        def before(a):
            return {"path": a["path"], "since": a["since"], "url": WAS, "bytes": 800, "w": 20, "h": 20, "seconds": None}

        def listed(a):
            data = answer(a.get("since", ""))
            return {**data, "assets": [], "removed": [], "stacks": []} if empty else data
        if not serves:                                  # an older host: the commands are not known to it
            return {**got, "ideas.assets": serve("ideas.assets", lambda a: {"error": "Unknown command: ideas.assets"})}
        return {**got, "ideas.assets": serve("ideas.assets", listed), "ideas.asset_before": serve("ideas.asset_before", before)}
    monkeypatch.setattr(Stub, "commands", commands)


def calls(stub, name):
    return [c[1] for c in stub.calls if c[0] == name]


async def _assets(page):
    project = await _project(page)
    section = project.locator(".pj-assets")
    await section.locator(".as-kind").first.wait_for(timeout=WAIT_MS)
    await section.scroll_into_view_if_needed()
    return project, section


async def _look(page):
    return await page.evaluate("() => localStorage.getItem('orkcraft.assets.look')")


async def _close(page, project):
    await project.get_by_role("button", name="Close").first.click()
    await project.wait_for(state="hidden", timeout=WAIT_MS)


# -- the section (§7) ----------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_the_projects_sheet_has_a_section_assets_after_the_parties_with_the_kinds_as_rows_of_74_px_tokens(fake_repo, monkeypatch):
    assets_host(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project, section = await _assets(page)
        assert await section.locator("h3").inner_text() == "Assets"
        kids = await project.evaluate("(d) => [...d.querySelector('.project').children].map((e) => e.className.split(' ')[0])")
        assert kids[-1] == "pj-assets" and kids.index("pj-party") < kids.index("pj-assets")                                  # after the parties
        kinds = section.locator(".as-kind")
        assert [await k.get_attribute("data-kind") for k in await kinds.all()] == ["screen", "art", "sound", "music", "clip", "font"]
        assert [norm(await k.locator("h4").inner_text()) for k in await kinds.all()] == ["Screens 1", "Art and icons 17", "Sound 1", "Music 1", "Clips 1", "Fonts 1"]
        token = section.locator('.as-token[data-id="audio/sfx/click.wav"]')
        box = await token.locator(".as-face").bounding_box()
        assert abs(box["width"] - 74) <= 2 and abs(box["height"] / box["width"] - 7 / 5) < 0.03                              # 74 px, 5:7
        assert await token.locator(".ork-sign.sound").count() == 1 and norm(await token.inner_text()) == "0:01 click.wav"          # a sound: its sign, its length, its name as it is
        assert await section.locator('.as-token[data-id="video/intro.mp4"] .ork-sign.film').count() == 1
        assert "0:12" in await section.locator('.as-token[data-id="video/intro.mp4"]').inner_text()
        assert await section.locator('.as-token[data-id="art/logo.png"] img.as-img').get_attribute("src") == NOW              # art: the picture itself
        assert "is-pixel" in await section.locator('.as-token[data-id="art/pixel.png"] img').get_attribute("class")          # 16 px: crisp
        assert "is-pixel" not in await section.locator('.as-token[data-id="art/logo.png"] img').get_attribute("class")
        assert await section.locator('.as-token[data-id="fonts/pixel.ttf"] .as-aa').count() == 1                              # a font: set in itself when the browser reads it
        for t in await section.locator(".as-token").all():
            assert (await t.bounding_box())["height"] >= 44
        assert norm(await section.locator(".as-play").inner_text()) == "Play on the computer"                                 # Play is the machine's own
        assert await section.locator("button:has-text('Play'), iframe").count() == 0
        text = await section.inner_text()
        assert not re.search(r"card|null|undefined", text, re.I)
        assert calls(stub, "ideas.assets") == [{}]                                                                            # no look yet: nothing marked
        assert await section.locator("[data-change]").count() == 0
        await _shot_to(page, "phone-assets")
        assert await page.evaluate(NO_SCROLL) and await project.evaluate("(d) => d.scrollWidth <= d.clientWidth")


@pytest.mark.asyncio
async def test_a_kind_shows_a_few_tokens_all_n_shows_it_whole_and_a_stack_opens_in_place(fake_repo, monkeypatch):
    assets_host(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project, section = await _assets(page)
        art = section.locator('.as-kind[data-kind="art"]')
        assert await art.locator(".as-token").count() == 8                                                                    # two lines of four
        more = art.get_by_role("button", name=re.compile(r"^All \d+$"))
        assert await more.inner_text() == "All 11" and (await more.bounding_box())["height"] >= 44                             # 10 files and a stack of 7
        stack = art.locator(".as-token.is-many")
        await more.click()
        assert await art.locator(".as-more").count() == 0
        stack = art.locator('.as-token[data-stack="art/icons"]')
        assert await stack.get_attribute("data-n") == "7" and "×7" in await stack.inner_text() and await stack.locator(".as-name").inner_text() == "icons"
        assert await art.locator(".as-token[data-id]").count() == 10                                                          # the stack's files are not among them
        await stack.click()
        assert await art.locator(".as-token[data-id]").count() == 17 and await art.locator('[data-stack="art/icons"]').get_attribute("aria-expanded") == "true"
        await art.locator('[data-stack="art/icons"]').click()                                                                 # the front token folds it again
        assert await art.locator(".as-token[data-id]").count() == 10
        assert await page.evaluate(NO_SCROLL) and await project.evaluate("(d) => d.scrollWidth <= d.clientWidth")


# -- the last look and what changed (§7) ----------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_the_changes_since_the_devices_last_look_wear_their_goals_element_and_the_look_is_kept_when_the_section_was_seen(fake_repo, monkeypatch):
    assets_host(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project, section = await _assets(page)
        await page.wait_for_timeout(200)
        await _close(page, project)                                                                                           # the section was in view: this is the device's look
        assert "c" * 40 in (await _look(page) or "")
        project, section = await _assets(page)
        assert calls(stub, "ideas.assets")[-1] == {"since": HEAD}
        logo = section.locator('.as-token[data-id="art/logo.png"]')
        assert await logo.get_attribute("data-change") == "changed" and await logo.locator(".as-mark .ork-elem.ice").count() == 1      # the goal's element
        assert "WebAuthn register" in await logo.get_attribute("aria-label") and "Changed by WebAuthn register" in await logo.get_attribute("title")
        shot = section.locator('.as-token[data-id="screen:register/k1"]')
        assert await shot.get_attribute("data-change") == "added" and await shot.locator(".as-mark .ork-elem.ice").count() == 1
        assert await section.locator('.as-token[data-id="audio/theme.ogg"] .as-mark .ork-elem.lava').count() == 1
        assert await section.locator('.as-token[data-id="audio/sfx/click.wav"] .as-mark').count() == 0                         # unchanged: no mark
        assert await section.locator('.as-token[data-id="art/pixel.png"][data-change]').count() == 0
        gone = section.locator('.as-token.is-removed')
        assert await gone.count() == 1 and await gone.get_attribute("data-id") == "art/old.png" and await gone.locator(".as-mark .ork-elem.ice").count() == 1
        assert "is-changed" in await logo.get_attribute("class") and "is-changed" not in await section.locator('[data-id="art/pixel.png"]').get_attribute("class")
        assert await section.locator('.as-token[data-stack="art/icons"] .as-mark .ork-elem.lava').count() == 1                 # a stack with a changed file says so
        await _shot_to(page, "phone-assets-changes")
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_sheet_put_away_before_the_section_came_into_view_keeps_no_look(fake_repo, monkeypatch):
    assets_host(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        await project.locator(".pj-assets .as-kind").first.wait_for(state="attached", timeout=WAIT_MS)
        await project.evaluate("(d) => { d.scrollTop = 0; }")
        visible = await project.locator(".pj-assets").evaluate("(e) => { const r = e.getBoundingClientRect(); return r.top < innerHeight; }")
        if visible:
            pytest.skip("the section is in view at once at this height")
        await _close(page, project)
        assert not await _look(page)


# -- the asset's screen (§7) ---------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_a_token_opens_the_assets_screen_large_with_before_and_now_and_the_variants_not_picked(fake_repo, monkeypatch):
    assets_host(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project, section = await _assets(page)
        await _close(page, project)
        project, section = await _assets(page)                                                                                # now with a look: the logo changed
        await section.locator('.as-token[data-id="art/logo.png"]').click()
        screen = page.get_by_role("dialog", name="logo.png")
        await screen.wait_for(timeout=WAIT_MS)
        big = screen.locator(".as-stage img.as-big")
        assert await big.get_attribute("src") == NOW
        box = await big.bounding_box()
        assert box["width"] >= 200                                                                                            # large, not a token
        assert "Changed by WebAuthn register" in await screen.locator(".as-by").inner_text() and await screen.locator(".as-by .ork-elem.ice").count() == 1
        now, before = screen.get_by_role("button", name="Now"), screen.get_by_role("button", name="Before")
        assert await now.get_attribute("aria-pressed") == "true" and await before.get_attribute("aria-pressed") == "false"
        assert (await before.bounding_box())["height"] >= 44 and (await now.bounding_box())["height"] >= 44
        assert calls(stub, "ideas.asset_before") == []                                                                        # asked when pressed
        await before.click()
        assert await _called(stub, "ideas.asset_before", {"path": "art/logo.png", "since": SINCE})
        await page.wait_for_function("(src) => document.querySelector('.asset-sheet .as-stage img').getAttribute('src') === src", arg=WAS)
        assert await before.get_attribute("aria-pressed") == "true" and await now.get_attribute("aria-pressed") == "false"
        await now.click()
        assert await big.get_attribute("src") == NOW or await screen.locator(".as-stage img").get_attribute("src") == NOW
        await before.click()
        assert len(calls(stub, "ideas.asset_before")) == 1                                                                    # once
        others = screen.locator(".as-others")
        assert norm(await others.locator("h4").inner_text()) == "Not picked (2)"
        tiles = others.locator(".pk")
        assert await tiles.count() == 2 and [norm(await t.locator(".pk__label").inner_text()) for t in await tiles.all()] == ["B · monogram", "C · wordmark"]
        await tiles.first.locator(".pk__view").click()
        assert await others.locator(".pk.is-on").count() == 0 and await others.locator(".pk__label[aria-checked=true]").count() == 0       # looked at, never picked
        await _shot_to(page, "phone-asset-screen")
        assert await page.evaluate(NO_SCROLL) and await screen.evaluate("(d) => d.scrollWidth <= d.clientWidth")
        await screen.get_by_role("button", name="Close").click()
        await screen.wait_for(state="hidden", timeout=WAIT_MS)
        assert await project.is_visible()                                                                                     # back in the project's sheet


@pytest.mark.asyncio
async def test_a_file_that_did_not_change_has_no_before_and_a_sound_and_a_clip_play_with_their_controls(fake_repo, monkeypatch):
    assets_host(monkeypatch)
    async with _phone(fake_repo, monkeypatch, init=PLAYS) as (stub, page):
        project, section = await _assets(page)
        await section.locator('.as-token[data-id="audio/sfx/click.wav"]').click()
        screen = page.get_by_role("dialog", name="click.wav")
        await screen.wait_for(timeout=WAIT_MS)
        audio = screen.locator(".as-stage audio")
        assert await audio.get_attribute("src") == "/media/_asset/x/click.wav" and await audio.evaluate("(a) => a.controls")      # playing, with its controls
        assert await page.evaluate("window.__played") == ["AUDIO"]
        assert await screen.get_by_role("button", name="Before").count() == 0 and await screen.locator(".as-others").count() == 0
        assert "0:01" in await screen.locator(".as-bar").inner_text()
        await screen.get_by_role("button", name="Close").click()
        await screen.wait_for(state="hidden", timeout=WAIT_MS)
        await section.locator('.as-token[data-id="video/intro.mp4"]').click()
        screen = page.get_by_role("dialog", name="intro.mp4")
        await screen.wait_for(timeout=WAIT_MS)
        video = screen.locator(".as-stage video")
        assert await video.evaluate("(v) => v.controls && v.playsInline") and await page.evaluate("window.__played") == ["AUDIO", "VIDEO"]
        await screen.get_by_role("button", name="Close").click()
        await section.locator('.as-token[data-id="fonts/pixel.ttf"]').click()
        screen = page.get_by_role("dialog", name="pixel.ttf")
        await screen.wait_for(timeout=WAIT_MS)
        assert "ABCDEFGHIJKLM" in await screen.locator(".as-font").inner_text()
        assert await page.evaluate(NO_SCROLL)


# -- an older host, an empty project -------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_a_host_without_assets_has_no_section_and_a_project_without_files_says_nothing_here_yet(fake_repo, monkeypatch):
    assets_host(monkeypatch, serves=False)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        await page.wait_for_timeout(500)
        assert await project.locator(".pj-assets").is_hidden() and "Assets" not in await project.inner_text()
        assert await project.locator(".pj-party").count() == 4                                                                # the rest of the sheet as it was


@pytest.mark.asyncio
async def test_an_empty_project_says_nothing_here_yet(fake_repo, monkeypatch):
    assets_host(monkeypatch, empty=True)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        section = project.locator(".pj-assets")
        await section.get_by_text("Nothing here yet").wait_for(timeout=WAIT_MS)
        assert await section.locator(".as-token").count() == 0 and "Play on the computer" in await section.inner_text()


# -- the worker --------------------------------------------------------------------------------------------------------------------------------------

def test_the_service_worker_is_v95_keeps_shell_assets_and_the_section_has_no_colour_of_its_own():
    sw = (ROOT / "sw.js").read_text(encoding="utf-8")
    assert 'const CACHE = "orkcraft-app-v103"' in sw and '"shell-assets.js"' in sw
    css = (ROOT / "app.css").read_text(encoding="utf-8")
    block = css[css.index("Assets (spec 88 C)"):]
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|border-radius", block)
    js = (ROOT / "shell-assets.js").read_text(encoding="utf-8")
    assert "orkcraft" in js and not re.search(r"\bcards?\b", re.sub(r"//.*", "", js).replace("`", ""), re.I)       # the state keeps Orkline's names; no word "card" in what a person reads
