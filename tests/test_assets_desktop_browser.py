"""Spec 88 part B on the desktop (docs/specs/88-assets-and-play.md §6, "As built (A)"): Chromium at 1 440 × 900 against the project test's stub host with `ideas.assets`, `ideas.asset_before`, `ideas.play` and
`ideas.play_stop` answering in the shapes part A gives them, and the signed addresses served by the test (`/media/_asset/…`). The Orkmaster's level has three tabs (Field, Assets, Play) and opens on Field; the files
as cards in a column for each kind in the order of §0, a stack ×n, *Changed by <goal>* with the goal's element; a card pressed lifts large (art at its size, a sound playing, *Not picked (n)*); a changed one turns
over to *Before* in steps of at most 0.42 s; what changed since the device's last look is dealt, sealed and crumbled once and not under reduced motion, and the look is written when the tab is left; the filter by kind
and by goal; Play's states (*Open the build*, *Starting the build…*, the sandboxed frame with *Plays dev at <short commit>* and *Stop the build*, the error, *Nothing here yet*). Screenshots to the directory
ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import io
import re
import shutil
import struct
import subprocess
import wave
import zlib
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_project_desktop_browser import ProjectHost, _project  # noqa: E402
from tests.test_route_desktop_browser import shot  # noqa: E402
from tests.test_shell_browser import _calls, _open  # noqa: E402

pytestmark = pytest.mark.browser

SHOP = "/work/shop"
HEAD, OLD = "a" * 40, "b" * 40
KINDS = ["Screens", "Art and icons", "Sound", "Music", "Clips", "Fonts"]
FONT = next((p for p in Path("/usr/share/fonts/truetype").rglob("*.ttf")), None) if Path("/usr/share/fonts/truetype").exists() else None


def png(w: int, h: int, rgb=(200, 80, 40)) -> bytes:
    """A solid PNG of w × h."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def wav(seconds=2.0) -> bytes:
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(8000)
        w.writeframes(b"\x80" * int(8000 * seconds))
    return out.getvalue()


def webm(tmp: Path) -> bytes:
    """A half second of test picture as WebM, or nothing where ffmpeg is not (the clip then has the *film* sign)."""
    if not shutil.which("ffmpeg"):
        return b""
    dest = tmp / "clip.webm"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=64x48:rate=10:duration=0.5", "-c:v", "libvpx", str(dest)], check=False)
    return dest.read_bytes() if dest.exists() else b""


def url(sha: str, path: str) -> str:
    return f"/media/_asset/{sha}/{path}?s=sig"


def asset(path: str, kind: str, **more) -> dict:
    base = {"id": path, "kind": kind, "name": path.split("/")[-1], "bytes": 1234, "w": None, "h": None, "seconds": None, "goal": "", "task": "", "at": "2026-10-26T10:00:00",
            "change": "", "url": url(HEAD, path)}
    return base | more


def doc(since="") -> dict:
    since = since if since == OLD else ""                                      # only the old look has anything since it (dev's head has not moved past itself)
    """`ideas.assets` as part A answers it: dev's head, a screen, art (a stack of seven in art/ui/, a changed hero, an added one, a 16 px icon), a sound added, music with variants not picked, a clip, a font."""
    stack = [asset(f"art/ui/btn{i}.png", "art", w=64, h=64, stack="art/ui") for i in range(7)]
    rows = [
        asset("art/hero.png", "art", w=400, h=240, goal="passkey", task="t1", change="changed" if since else ""),
        asset("art/fresh.png", "art", w=200, h=120, goal="website", task="t2", change="added" if since else ""),
        asset("screen:passkey/t1", "screen", name="Sign in", w=390, h=844, goal="passkey", task="t1", url=url(HEAD, "screen/passkey-t1.png")),
        asset("audio/jump.wav", "sound", seconds=2.0, goal="website", task="t2", change="added" if since else ""),
        asset("music/theme.wav", "music", seconds=95.0, others={"goal": "passkey", "pick": "p1", "picked": "A", "variants": [
            {"key": "B", "name": "slow", "mime": "audio/wav", "w": None, "h": None, "seconds": 2.0, "url": url(HEAD, "music/theme-b.wav")},
            {"key": "C", "name": "fast", "mime": "audio/wav", "w": None, "h": None, "seconds": 2.0, "url": url(HEAD, "music/theme-c.wav")}]}),
        asset("clips/intro.webm", "clip", seconds=0.5, w=64, h=48),
        asset("fonts/pixel.ttf", "font"),
        asset("art/icon.png", "art", w=16, h=16),
        *stack,
    ]
    return {"commit": HEAD, "short": HEAD[:7], "ref": "dev", "since": OLD if since else "", "assets": rows,
            "removed": [{"id": "art/old.png", "kind": "art", "goal": "passkey", "task": "t0", "at": "2026-10-26T09:00:00"}] if since else [],
            "stacks": [{"folder": "art/ui", "kind": "art", "n": 7}],
            "goals": {"passkey": {"title": "Passkey login", "element": "meadow"}, "website": {"title": "Landing copy", "element": "lava"}}}


class AssetsHost(ProjectHost):
    """The project test's world plus the four commands of part A. `play` is the script of `ideas.play`'s answers (the last one repeats); `empty`: a project with no assets."""

    def __init__(self, empty=False):
        super().__init__()
        self.empty = empty
        self.play = [{"state": "stopped"}]
        self.at = 0

    def handle(self, name, a):
        if name == "ideas.assets":
            self.log.append((name, a))
            if self.empty:
                return doc() | {"assets": [], "stacks": [], "goals": {}}
            return copy.deepcopy(doc(a.get("since", "")))
        if name == "ideas.asset_before":
            self.log.append((name, a))
            if a["path"] == "art/hero.png":
                return {"path": a["path"], "since": OLD, "url": url(OLD, a["path"]), "bytes": 99, "w": 400, "h": 240, "seconds": None}
            return {"path": a["path"], "since": OLD, "url": ""}
        if name == "ideas.play":
            self.log.append((name, a))
            got = self.play[min(self.at, len(self.play) - 1)]                      # each call takes the next answer of the script, the last repeats
            self.at += 1
            return copy.deepcopy(got)
        if name == "ideas.play_stop":
            self.log.append((name, a))
            self.play = [{"state": "stopped"}]
            self.at = 0
            return {"ok": True, "stopped": True}
        return super().handle(name, a)


def serve(pg, tmp: Path) -> None:
    """The signed addresses and the preview's, answered by the test."""
    clip = webm(tmp)
    font = FONT.read_bytes() if FONT else b""
    types = {".png": "image/png", ".wav": "audio/wav", ".webm": "video/webm", ".ttf": "font/ttf"}

    def asset_route(route):
        path = route.request.url.split("?")[0]
        ext = "." + path.rsplit(".", 1)[-1]
        body = {".png": png(*((400, 240) if "hero" in path else (200, 120) if "fresh" in path else (16, 16) if "icon" in path else (64, 64)), rgb=(40, 120, 200) if OLD[:3] in path else (200, 80, 40)),
                ".wav": wav(), ".webm": clip, ".ttf": font}.get(ext, b"")
        route.fulfill(status=200 if body else 404, body=body, headers={"Content-Type": types.get(ext, "application/octet-stream"), "Access-Control-Allow-Origin": "*"})

    pg.route("**/media/_asset/**", asset_route)
    pg.route("http://127.0.0.1:5999/**", lambda r: r.fulfill(status=200, body="<!doctype html><title>build</title><p>the build</p>", headers={"Content-Type": "text/html"}))


@pytest.fixture
def level(gui, tmp_path):
    pg, host, errors = _open(gui, host=AssetsHost(), ready=".arena[data-goal=passkey]")
    serve(pg, tmp_path)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _tab(pg, name):
    pg.get_by_role("tab", name=name).click()


def _assets(pg):
    _project(pg)
    _tab(pg, "Assets")
    pg.locator(".assets[data-state=shown]").wait_for(timeout=WAIT_MS)


def _card(pg, path):
    return pg.locator(f'.assets-card[data-asset="{path}"]')


# -- the three tabs ---------------------------------------------------------------------------------------------------------------------------------------

def test_the_level_has_three_tabs_and_opens_on_field(level):
    pg, host = level
    _project(pg)
    tabs = pg.get_by_role("tab")
    assert [t.text_content().strip() for t in tabs.all()] == ["Field", "Assets and files", "Play"]
    assert tabs.nth(0).get_attribute("aria-selected") == "true" and pg.locator(".arena-project__cols").count() == 1      # today's level
    assert pg.locator(".assets, .playpane").count() == 0 and not [c for c in host.log if c[0] in ("ideas.assets", "ideas.play")]    # nothing asked until a tab is opened
    _tab(pg, "Assets")
    pg.locator(".assets").wait_for(timeout=WAIT_MS)
    assert pg.locator(".arena-project__cols").count() == 0 and pg.get_by_role("tab", name="Assets").get_attribute("aria-selected") == "true"
    _tab(pg, "Play")
    pg.locator(".playpane").wait_for(timeout=WAIT_MS)
    assert pg.locator(".assets").count() == 0
    pg.get_by_role("tab", name="Play").press("ArrowLeft")                                                           # ← moves to the tab before
    assert pg.get_by_role("tab", name="Assets").get_attribute("aria-selected") == "true"
    _tab(pg, "Field")
    pg.locator(".arena-pcol").first.wait_for(timeout=WAIT_MS)
    assert pg.locator(".arena-project__heads .arena-pcol__head").count() == 4                                    # the Field is as it was


# -- the table of assets ----------------------------------------------------------------------------------------------------------------------------------

def test_the_assets_lie_in_a_section_for_each_kind_in_the_order_of_the_words_with_the_thing_itself_as_the_face(level):
    pg, host = level
    _assets(pg)
    assert [c.get_attribute("aria-label") for c in pg.locator(".assets-sec").all()] == KINDS
    assert [h.text_content().strip().rsplit(" ", 1)[0] for h in pg.locator(".assets-sec > h3").all()] == KINDS
    assert pg.locator('.assets-sec[data-kind="art"] .arena-stk').count() == 4                  # hero, fresh, icon and the stack of seven as one
    hero = _card(pg, "art/hero.png")
    img = hero.locator("img.assets-face__img")
    pg.wait_for_function("e => e.complete && e.naturalWidth > 0", arg=img.element_handle(), timeout=WAIT_MS)
    assert img.evaluate("e => getComputedStyle(e).objectFit") == "contain" and "is-pixel" not in (img.get_attribute("class") or "")      # art whole, smooth when it fills the card
    icon = _card(pg, "art/icon.png").locator("img")
    pg.wait_for_function("e => e.complete && e.naturalWidth > 0", arg=icon.element_handle(), timeout=WAIT_MS)
    assert "is-pixel" in icon.get_attribute("class")                                                                  # smaller than the card: crisp
    screen = _card(pg, "screen:passkey/t1")
    assert screen.locator("img").get_attribute("src") == url(HEAD, "screen/passkey-t1.png") and screen.locator(".arena-task__name").text_content().strip() == "Sign in"
    sound = _card(pg, "audio/jump.wav")
    assert sound.locator(".assets-face__title").text_content().strip() == "jump.wav" and sound.locator(".ork-sign.sound").count() == 1 and sound.locator(".assets-face__len").text_content().strip() == "0:02"
    assert _card(pg, "music/theme.wav").locator(".assets-face__len").text_content().strip() == "1:35"
    clip = _card(pg, "clips/intro.webm")
    assert clip.locator("video").count() == 1
    pg.wait_for_function("() => document.querySelector('.assets-card[data-kind=clip] .assets-face__video, .assets-card[data-kind=clip] .assets-face__sign')", timeout=WAIT_MS)
    if shutil.which("ffmpeg"):
        pg.wait_for_selector(".assets-card[data-kind=clip] video.is-shown", timeout=WAIT_MS)                          # the first frame the browser gives
    else:
        assert clip.locator(".ork-sign.film").count() == 1
    font = _card(pg, "fonts/pixel.ttf")
    assert font.locator(".assets-face__font").text_content().strip() == "pixel.ttf"
    if FONT:
        pg.wait_for_function("() => /orkboard-asset-/.test(document.querySelector('.assets-face__font').style.fontFamily)", timeout=WAIT_MS)   # its name set in it
    shot(pg, "assets-table.png")


def test_a_goals_files_say_changed_by_the_goal_with_its_element_and_a_folder_of_more_than_six_is_a_stack(level):
    pg, host = level
    _assets(pg)
    hero = _card(pg, "art/hero.png")
    foot = hero.locator(".assets-changed")
    assert foot.text_content().strip().strip() == "Changed by Passkey login" and foot.locator(".ork-elem.meadow").count() == 1
    assert _card(pg, "art/fresh.png").locator(".assets-changed .ork-elem.lava").count() == 1
    assert _card(pg, "art/icon.png").locator(".assets-changed").count() == 0                                          # the person's own: no goal to name
    stack = pg.locator('.assets-sec[data-kind="art"] .assets-stk[data-n="7"]')
    assert stack.count() == 1 and stack.locator(".arena-stk__n").text_content().strip() == "×7" and stack.locator(".arena-stk__edge").count() == 2
    assert pg.locator('.assets-card[data-asset^="art/ui/"]').count() == 1                                             # shut: the front only
    stack.locator("button.assets-card").click()
    assert pg.locator('.assets-card[data-asset^="art/ui/"]').count() == 7                                             # opened: every file
    fold = pg.locator(".assets-stack > button")
    assert fold.text_content().strip().strip() == "art/ui ×7" and fold.get_attribute("aria-expanded") == "true"
    fold.click()
    assert pg.locator('.assets-card[data-asset^="art/ui/"]').count() == 1
    text = pg.locator(".assets").text_content().strip()
    assert not re.search(r"\bcards?\b", text, re.I), text                                                            # a person never reads the word "card"


# -- a card lifted -----------------------------------------------------------------------------------------------------------------------------------------

def _lifted(pg, name):
    """A file opened in the right column (docs/specs/90-what-the-first-look-said.md §2–§3)."""
    return pg.locator(".shell-drawer").get_by_role("region", name=name, exact=True)


def test_a_pressed_card_opens_art_at_its_size_in_the_right_column_and_esc_puts_it_away(level):
    pg, host = level
    _assets(pg)
    _card(pg, "art/hero.png").click()
    lift = _lifted(pg, "hero.png")
    lift.wait_for(timeout=WAIT_MS)
    img = lift.locator("img.assets-lift__img")
    pg.wait_for_function("e => e.complete && e.naturalWidth > 0", arg=img.element_handle(), timeout=WAIT_MS)
    box = img.bounding_box()
    assert abs(box["width"] - 400) <= 1 and abs(box["height"] - 240) <= 1                                              # at its size: 400 × 240 in a column that is wider
    assert lift.get_by_text("Changed by Passkey login").count() == 1 and lift.locator("h3").count() == 0              # no variants: no Not picked
    shot(pg, "assets-lifted.png")
    pg.keyboard.press("Escape")
    pg.locator(".assets-lift").wait_for(state="detached", timeout=WAIT_MS)
    _card(pg, "art/icon.png").click()
    small = _lifted(pg, "icon.png").locator("img.assets-lift__img")
    pg.wait_for_function("e => e.complete && e.naturalWidth > 0", arg=small.element_handle(), timeout=WAIT_MS)
    assert "is-pixel" in small.get_attribute("class") and abs(small.bounding_box()["width"] - 16) <= 1                  # a 16 px icon is not blown up
    pg.get_by_role("button", name="Close icon.png").click()                                                          # its tab's ×: the last, so no column
    pg.locator(".assets-lift, .shell-drawer").first.wait_for(state="detached", timeout=WAIT_MS)


def test_a_sound_plays_when_lifted_with_its_controls_and_the_variants_not_picked_lie_under_it(level):
    pg, host = level
    _assets(pg)
    _card(pg, "music/theme.wav").click()
    lift = _lifted(pg, "theme.wav")
    lift.wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => { const a = document.querySelector('.assets-lift__face.is-now audio'); return !!a && !a.paused; }", timeout=WAIT_MS)       # playing
    assert lift.locator(".is-now .pick-play").get_attribute("aria-label").startswith("Pause")                                  # its control says what a press does
    assert lift.locator(".assets-lift__others h3").text_content().strip() == "Not picked (2)"
    assert [o.text_content().strip() for o in lift.locator(".assets-other__label").all()] == ["B · slow", "C · fast"]
    assert lift.locator(".assets-other audio").count() == 2
    lift.locator(".is-now .pick-play").first.click()                                                                          # Pause
    pg.wait_for_function("() => document.querySelector('.assets-lift__face.is-now audio').paused", timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    _card(pg, "clips/intro.webm").click()
    clip = _lifted(pg, "intro.webm")
    clip.wait_for(timeout=WAIT_MS)
    assert clip.locator("video").count() == 1 and clip.locator(".pick-play").count() + clip.locator(".pick-miss").count() >= 1


def test_a_changed_file_turns_over_to_before_in_steps_and_back_to_now(level):
    pg, host = level
    pg.add_init_script(f"try {{ localStorage.setItem('orkboard.assets.look.{SHOP}', '{OLD}'); }} catch (e) {{}}")
    pg.reload()
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    _assets(pg)
    _card(pg, "art/fresh.png").click()
    lift = _lifted(pg, "fresh.png")
    lift.wait_for(timeout=WAIT_MS)
    assert lift.get_by_role("radio").count() == 0                                                                     # an added file has no version before
    pg.keyboard.press("Escape")
    _card(pg, "art/hero.png").click()
    lift = _lifted(pg, "hero.png")
    lift.wait_for(timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.asset_before") == [{"path": "art/hero.png", "since": OLD}]
    now, before = lift.get_by_role("radio", name="Now"), lift.get_by_role("radio", name="Before")
    before.wait_for(timeout=WAIT_MS)
    assert now.get_attribute("aria-checked") == "true" and before.get_attribute("aria-checked") == "false"
    face = lift.locator(".assets-lift__face.is-now")
    assert face.evaluate("e => getComputedStyle(e).transitionTimingFunction").startswith("steps(") and \
        face.evaluate("e => parseFloat(getComputedStyle(e).transitionDuration)") <= 0.42                                  # spec 74's steps, at most 0.42 s
    before.click()
    stage = lift.locator(".assets-lift__stage")
    assert "is-turned" in stage.get_attribute("class") and before.get_attribute("aria-checked") == "true"
    pg.wait_for_timeout(500)
    old = lift.locator(".assets-lift__face.is-before img")
    assert old.get_attribute("src") == url(OLD, "art/hero.png")                                                       # the file as it was
    assert lift.locator(".assets-lift__face.is-before").evaluate("e => new DOMMatrix(getComputedStyle(e).transform).m11") > 0.99      # turned to face us
    shot(pg, "assets-before.png")
    now.click()
    assert "is-turned" not in stage.get_attribute("class")


# -- what changed since the last look ----------------------------------------------------------------------------------------------------------------------

LOOK = f"orkboard.assets.look.{SHOP}"
OBSERVE = """(() => {                      // records what the reveal plays on which file, as it appears (it lasts about a second)
  const fx = window.__fx = { dealt: new Set(), sealed: new Set(), crumble: new Set(), seal: "", steps: [] };
  const look = () => {
    document.querySelectorAll('.assets-card.is-dealt-in').forEach((e) => { fx.dealt.add(e.dataset.asset); fx.steps[0] = getComputedStyle(e).animationTimingFunction; });
    document.querySelectorAll('.assets-card.is-sealed').forEach((e) => { fx.sealed.add(e.dataset.asset); const s = e.querySelector('.assets-seal'); if (s) { fx.steps[1] = getComputedStyle(s).animationTimingFunction; fx.seal = [...s.querySelector('.ork-elem').classList].filter((c) => c !== 'ork-elem' && c !== 'big' && c !== 'dim').join(' '); } });
    document.querySelectorAll('.assets-card.is-crumble').forEach((e) => { fx.crumble.add(e.dataset.removed); fx.steps[2] = getComputedStyle(e).animationTimingFunction; });
  };
  new MutationObserver(look).observe(document, { subtree: true, childList: true, attributes: true });
})();"""


def test_the_changes_since_the_devices_last_look_are_dealt_sealed_and_crumbled_once(level):
    pg, host = level
    pg.add_init_script(f"try {{ if (!sessionStorage.getItem('seeded')) {{ localStorage.setItem('{LOOK}', '{OLD}'); sessionStorage.setItem('seeded', '1'); }} }} catch (e) {{}}")
    pg.add_init_script(OBSERVE)
    pg.reload()
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    _project(pg)
    _tab(pg, "Assets")
    pg.wait_for_function("() => window.__fx.dealt.size > 0 && window.__fx.sealed.size > 0 && window.__fx.crumble.size > 0", timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.assets") == [{"since": OLD}]
    fx = pg.evaluate("() => ({dealt: [...__fx.dealt].sort(), sealed: [...__fx.sealed], crumble: [...__fx.crumble], seal: __fx.seal, steps: __fx.steps})")      # what the page played, seen as it came
    assert fx["dealt"] == ["art/fresh.png", "audio/jump.wav"]                                                           # added: dealt
    assert fx["sealed"] == ["art/hero.png"] and fx["seal"] == "meadow"                                                  # changed: sealed with its goal's element
    assert fx["crumble"] == ["art/old.png"]                                                                             # removed: crumbles
    assert all(x.startswith("steps(") for x in fx["steps"]) and len(fx["steps"]) == 3                                   # all three in steps
    shot(pg, "assets-reveal.png")
    pg.wait_for_selector(".assets-card.is-crumble, .assets-card.is-dealt-in, .assets-seal", state="detached", timeout=WAIT_MS)      # played once, then they are as they are
    assert _card(pg, "art/fresh.png").count() == 1 and _card(pg, "art/hero.png").locator(".assets-changed").count() == 1
    _tab(pg, "Play")                                                                                                    # the tab is left: the look is the commit shown
    pg.locator(".playpane").wait_for(timeout=WAIT_MS)
    assert pg.evaluate(f"localStorage.getItem('{LOOK}')") == HEAD
    _tab(pg, "Assets")
    pg.locator(".assets[data-state=shown]").wait_for(timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.assets", 2)[1] == {"since": HEAD}
    assert pg.locator(".assets-card.is-dealt-in, .assets-card.is-sealed, .assets-card.is-crumble").count() == 0        # nothing new since: nothing played


def test_nothing_is_played_under_reduced_motion_and_a_new_device_marks_nothing(gui, tmp_path):
    pg, host, errors = _open(gui, host=AssetsHost(), ready=".arena[data-goal=passkey]")
    serve(pg, tmp_path)
    _assets(pg)
    assert _calls(pg, host, "ideas.assets") == [{}]                                                                    # no look yet: no since, nothing marked
    assert pg.locator(".assets-card[data-change], .assets-card.is-dealt-in, .assets-card.is-sealed, .assets-card.is-crumble").count() == 0
    pg.close()
    pg = gui[1].new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    host = AssetsHost()
    pg.route_web_socket("**/ws*", host.on_socket)
    serve(pg, tmp_path)
    pg.add_init_script(f"try {{ localStorage.setItem('{LOOK}', '{OLD}'); }} catch (e) {{}}")
    pg.goto(gui[0].url)
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    _assets(pg)
    assert _calls(pg, host, "ideas.assets") == [{"since": OLD}]
    assert pg.locator(".assets-card[data-change]").count() == 3                                                          # still marked by the foot's words, but not played
    assert pg.locator(".assets-card.is-dealt-in, .assets-card.is-sealed, .assets-card.is-crumble, .assets-seal").count() == 0
    pg.close()
    assert not errors, "\n".join(errors)


# -- the filter -----------------------------------------------------------------------------------------------------------------------------------------

def test_the_filter_by_kind_and_by_goal(level):
    pg, host = level
    _assets(pg)
    kinds = pg.locator(".assets-kinds button")
    assert [k.text_content().strip() for k in kinds.all()] == KINDS
    kinds.filter(has_text="Sound").click()
    assert [c.get_attribute("aria-label") for c in pg.locator(".assets-sec").all()] == ["Sound"] and kinds.filter(has_text="Sound").get_attribute("aria-pressed") == "true"
    kinds.filter(has_text="Sound").click()                                                                               # pressed again: all kinds
    assert pg.locator(".assets-sec").count() == 6
    goals = pg.get_by_label("Goal", exact=True)
    assert goals.locator("option").evaluate_all("l => l.map(e => e.textContent)") == ["All goals", "Passkey login", "Landing copy"]
    goals.select_option(label="Landing copy")
    assert pg.locator(".assets-card").evaluate_all("l => l.map(e => e.dataset.asset).sort()") == ["art/fresh.png", "audio/jump.wav"]
    assert [c.get_attribute("aria-label") for c in pg.locator(".assets-sec").all()] == ["Art and icons", "Sound"]
    kinds.filter(has_text="Sound").click()
    assert pg.locator(".assets-card").count() == 1
    goals.select_option(label="All goals")
    kinds.filter(has_text="Sound").click()
    assert pg.locator(".assets-sec").count() == 6


def test_a_project_with_no_assets_says_nothing_here_yet(gui, tmp_path):
    pg, host, errors = _open(gui, host=AssetsHost(empty=True), ready=".arena[data-goal=passkey]")
    _assets(pg)
    assert pg.locator(".assets-none__title").text_content().strip() == "Nothing here yet" and pg.locator(".assets-sec").count() == 0
    pg.close()
    assert not errors, "\n".join(errors)


# -- Play -----------------------------------------------------------------------------------------------------------------------------------------------

PLAYING = {"state": "playing", "url": "http://127.0.0.1:5999/", "commit": HEAD, "short": HEAD[:7], "dev": HEAD}


def _play(pg):
    _project(pg)
    _tab(pg, "Play")
    pg.locator(".playpane").wait_for(timeout=WAIT_MS)


def test_play_opens_the_build_polls_while_it_starts_and_shows_it_in_a_sandboxed_frame(level):
    pg, host = level
    host.play = [{"state": "stopped"}, {"state": "starting", "commit": HEAD, "short": HEAD[:7]}, PLAYING]
    _play(pg)
    assert _calls(pg, host, "ideas.play") == [{"peek": True}]                                                           # asked what it is, starting nothing
    pg.locator('.playpane[data-state="idle"]').wait_for(timeout=WAIT_MS)
    assert pg.get_by_role("button", name="Open the build").count() == 1 and pg.locator("iframe").count() == 0
    pg.get_by_role("button", name="Open the build").click()
    pg.locator('.playpane[data-state="starting"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-stage-words").text_content().strip() == "Making its worktree" and pg.locator(".play-title").text_content().strip() == "shop"
    shot(pg, "play-starting.png")
    pg.locator('.playpane[data-state="playing"]').wait_for(timeout=WAIT_MS)
    calls = _calls(pg, host, "ideas.play", 3)
    assert calls[1] == {} and calls[2] == {"peek": True}                                                                # pressed once, then polled
    frame = pg.locator("iframe.play-frame")
    assert frame.get_attribute("sandbox") == "allow-scripts allow-same-origin allow-pointer-lock" and frame.get_attribute("src") == "http://127.0.0.1:5999/"
    assert pg.locator(".play-at").text_content().strip().strip() == f"Plays dev at {HEAD[:7]}"
    assert pg.frame_locator("iframe.play-frame").locator("p").text_content().strip() == "the build"
    shot(pg, "play-playing.png")
    pg.get_by_role("button", name="Stop the build").click()
    pg.locator('.playpane[data-state="idle"]').wait_for(timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.play_stop") == [{}] and pg.locator("iframe").count() == 0
    assert pg.get_by_role("button", name="Open the build").count() == 1


def test_play_already_running_shows_at_once_and_says_when_dev_has_moved_on(level):
    pg, host = level
    host.play = [PLAYING | {"dev": "c" * 40}]
    _play(pg)
    pg.locator('.playpane[data-state="playing"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-moved").text_content().strip() == "dev is at ccccccc now"
    pg.get_by_role("button", name="Open the build").click()                                                              # a merge changes nothing until it is pressed again
    assert _calls(pg, host, "ideas.play", 2)[1] == {"fresh": True}


def test_play_says_why_the_build_would_not_start_and_nothing_here_yet_for_a_project_with_no_preview(level):
    pg, host = level
    host.play = [{"state": "stopped"}, {"state": "failed", "error": "did not open"}]
    _play(pg)
    pg.get_by_role("button", name="Open the build").click()
    err = pg.locator(".play-error")
    err.wait_for(timeout=WAIT_MS)
    assert err.text_content().strip() == "The build would not start: did not open" and pg.get_by_role("button", name="Open the build").count() == 1       # and may be pressed again
    shot(pg, "play-error.png")
    host.play = [{"state": "failed", "error": "no preview", "none": True}]
    host.at = 0
    pg.get_by_role("button", name="Open the build").click()
    pg.locator('.playpane[data-state="none"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".assets-none__title").text_content().strip() == "Nothing here yet"
    assert "checks.toml" in pg.locator(".playpane").text_content().strip() and "preview" in pg.locator(".playpane").text_content().strip()
    assert pg.get_by_role("button", name="Open the build").count() == 0


# -- the start screen and the page that answered (spec 90 §1) ---------------------------------------------------------------------------------------------

WATCH_FRAME = """(() => {                    // records the state of the pane each time a frame is put into the page
  window.__frames = [];
  new MutationObserver((list) => { for (const m of list) for (const n of m.addedNodes) {
    const frames = n.nodeType === 1 ? (n.matches("iframe.play-frame") ? [n] : [...n.querySelectorAll("iframe.play-frame")]) : [];
    for (const f of frames) window.__frames.push(f.closest(".playpane")?.dataset.state || "?");
  } }).observe(document, { childList: true, subtree: true });
})()"""
CANVAS = "() => { const e = document.createElement('i'); e.style.background = 'var(--ork-canvas)'; document.body.append(e); const c = getComputedStyle(e).backgroundColor; e.remove(); return c; }"


def test_the_start_screen_is_black_with_the_name_looping_in_steps_and_the_frame_only_after_the_page_answered(level):
    pg, host = level
    pg.evaluate(WATCH_FRAME)
    host.play = [{"state": "stopped"}, {"state": "starting", "commit": HEAD, "short": HEAD[:7]}, {"state": "starting", "commit": HEAD, "short": HEAD[:7]},
                 {"state": "starting", "commit": HEAD, "short": HEAD[:7]}, PLAYING]
    _play(pg)
    pg.evaluate("""() => { new MutationObserver(() => { const e = document.querySelector('.play-intro.is-fading');
      if (e && !window.__fade) window.__fade = getComputedStyle(e).animationTimingFunction; }).observe(document.body, {subtree: true, childList: true, attributes: true}); }""")
    pg.get_by_role("button", name="Open the build").click()
    pane = pg.locator('.playpane[data-state="starting"]')
    pane.wait_for(timeout=WAIT_MS)
    assert pg.locator("iframe").count() == 0                                                                           # no frame while it starts
    black = pg.evaluate(CANVAS)
    assert pane.evaluate("e => getComputedStyle(e).backgroundColor") == black and pg.locator(".play-intro").evaluate("e => getComputedStyle(e).backgroundColor") == black
    title, note = pg.locator(".play-title"), pg.locator(".play-starting")
    assert title.text_content().strip() == "shop" and pg.locator(".play-stage-words").text_content().strip() == "Making its worktree"       # no stage said yet: the first
    assert "Pixelify" in title.evaluate("e => getComputedStyle(e).fontFamily") and title.evaluate("e => parseFloat(getComputedStyle(e).fontSize)") >= 40       # the pixel face, large
    assert title.evaluate("e => getComputedStyle(e).animationTimingFunction").startswith("steps(") and title.evaluate("e => getComputedStyle(e).animationName") == "play-name-loop"
    assert note.evaluate("e => getComputedStyle(e).color") == pg.evaluate("() => { const e = document.createElement('i'); e.style.color = 'var(--ork-ink-faint)'; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }")
    box, pbox = title.bounding_box(), pane.bounding_box()
    assert abs((box["x"] + box["width"] / 2) - (pbox["x"] + pbox["width"] / 2)) < 3                                    # centred
    assert abs((box["y"] + box["height"] / 2) - (pbox["y"] + pbox["height"] / 2)) < 60
    shot(pg, "play-start-screen.png")
    pg.locator('.playpane[data-state="playing"]').wait_for(timeout=WAIT_MS)
    assert pg.locator("iframe.play-frame").count() == 1
    timing = pg.wait_for_function("() => window.__fade", timeout=WAIT_MS).json_value()      # the name faded over the frame coming up (caught as it began)
    assert timing.startswith("steps(")
    pg.locator(".play-intro").wait_for(state="detached", timeout=WAIT_MS)
    assert pg.frame_locator("iframe.play-frame").locator("p").text_content().strip() == "the build"
    assert pg.evaluate("window.__frames") == ["playing"]                                                               # a frame was put in only once the page had answered
    assert pg.locator("iframe.play-frame").evaluate("e => getComputedStyle(e).backgroundColor") == black


def test_under_reduced_motion_the_start_screen_has_no_steps_and_the_page_follows_the_name_at_once(gui, tmp_path):
    pg = gui[1].new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    host = AssetsHost()
    host.play = [{"state": "stopped"}, {"state": "starting", "commit": HEAD, "short": HEAD[:7]}, {"state": "starting", "commit": HEAD, "short": HEAD[:7]}, PLAYING]
    pg.route_web_socket("**/ws*", host.on_socket)
    serve(pg, tmp_path)
    pg.goto(gui[0].url)
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    pg.evaluate(WATCH_FRAME)
    _play(pg)
    pg.get_by_role("button", name="Open the build").click()
    pg.locator('.playpane[data-state="starting"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-title").text_content().strip() == "shop" and pg.locator("iframe").count() == 0
    assert pg.locator(".play-title").evaluate("e => getComputedStyle(e).animationName") == "none" and pg.locator(".play-starting").evaluate("e => getComputedStyle(e).animationName") == "none"
    assert pg.locator(".play-title").evaluate("e => getComputedStyle(e).opacity") == "1"                                # there at once, not coming up
    pg.locator('.playpane[data-state="playing"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-intro").count() == 0 and pg.locator("iframe.play-frame").count() == 1                      # the name and then the page: nothing fades between
    assert pg.frame_locator("iframe.play-frame").locator("p").text_content().strip() == "the build"
    assert pg.evaluate("window.__frames") == ["playing"]
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_build_whose_ports_give_no_page_says_so_with_the_ports_tried_and_offers_to_stop_it(level):
    pg, host = level
    pg.evaluate(WATCH_FRAME)
    host.play = [{"state": "stopped"}, {"state": "failed", "why": "nopage", "error": "The build started, but no port gives a page. Name it in .orkcraft/checks.toml: preview_port or preview_path.", "ports": [3001, 5173]}]
    _play(pg)
    pg.get_by_role("button", name="Open the build").click()
    pane = pg.locator('.playpane[data-state="nopage"]')
    pane.wait_for(timeout=WAIT_MS)
    assert pg.locator(".play-error").text_content().strip() == "The build started, but no port gives a page. Name it in .orkcraft/checks.toml: preview_port or preview_path."
    assert pg.locator(".play-ports").text_content().strip() == "Ports tried: 3001, 5173"
    assert pg.get_by_role("button", name="Stop the build").count() == 1 and pg.get_by_role("button", name="Open the build").count() == 0
    assert pg.locator("iframe").count() == 0 and pg.evaluate("window.__frames") == []                                   # never a frame, never a white page
    shot(pg, "play-nopage.png")
    pg.get_by_role("button", name="Stop the build").click()
    pg.locator('.playpane[data-state="idle"]').wait_for(timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.play_stop") == [{}]
