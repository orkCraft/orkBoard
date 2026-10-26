"""Spec 81 part C, the phone (docs/specs/81-a-party-its-tool-and-size.md §4, §5 "C"; decisions §98): Chromium at 390 × 844 against spec 75's stub host with `ideas.tools` and `ideas.party_sizes` (spec §1.4, §3). New party (spec 91 §7)
has **Its AI tool** under the size switch — the phone's own select, *Main tool (Claude Code)* picked, then *Ready*, *Not signed in* and *Not installed* (disabled); a tool with no tiers says it *runs its own
model* where the price was; a tool not signed in stays picked and says its sign-in is the computer's; the pick is sent as `tool`. *About this party* has the list (a change saves `tool`) and its size switch shows the heads
that join and leave before the press, then saves in one press, a refusal said in place. No sideways scroll at 390 px; the service worker's version."""
from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest

from orkboard.gui import pwa
from tests.test_pwa_arena_browser import SCENE, _about, _redrawn, _scene, _shot_to  # noqa: F401
from tests.test_pwa_project_browser import calls  # noqa: F401
from tests.test_pwa_proposals_browser import ARCH, MOBILE, PM, _new_party, proposing  # noqa: F401
from tests.test_pwa_route_browser import norm  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _called, _phone  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

TOOLS = {"main": "claude", "tools": [
    {"id": "claude", "name": "Claude Code", "ready": True, "signed_in": True, "installed": True, "experimental": False, "tiers": True},
    {"id": "codex", "name": "Codex", "ready": True, "signed_in": True, "installed": True, "experimental": False, "tiers": True},
    {"id": "pi", "name": "pi", "ready": True, "signed_in": True, "installed": True, "experimental": False, "tiers": False},
    {"id": "cursor", "name": "Cursor", "ready": False, "signed_in": False, "installed": True, "experimental": False, "tiers": False},
    {"id": "agy", "name": "Antigravity", "ready": False, "signed_in": True, "installed": False, "experimental": True, "tiers": True},
    {"id": "hermes", "name": "Hermes Agent", "ready": False, "signed_in": True, "installed": False, "experimental": False, "tiers": False}]}


def head_of(race, tier):
    return {"race": race, "tier": tier}


def the_moves(slug="passkey"):
    """What each size would make of the Passkey party (spec §3): Lean lets three go, Full takes one in."""
    said = lambda ids: [{"slug": i, "name": i.title(), "head": head_of("peon", "warrior")} for i in ids]       # noqa: E731
    return {"size": "standard", "sizes": {
        "lean": {"recipe": "engineering-code", "team": [], "tiers": {}, "joins": [], "leaves": said(["grunt", "tester", "reviewer"])},
        "standard": {"recipe": "engineering-code", "team": ["grunt", "tester", "reviewer"], "tiers": {}, "joins": [], "leaves": []},
        "full": {"recipe": "engineering-code", "team": ["grunt", "tester", "reviewer", "security-reviewer"], "tiers": {}, "joins": said(["security-reviewer"]), "leaves": []}}}


def with_tools(monkeypatch, *, tools=TOOLS, moves=True, refuse="", size_of="standard", **more):
    """Spec 75's host plus spec 81's: `ideas.tools`, `ideas.party_sizes` (`moves=False`: an older host), a size the host refuses (`refuse`), and the tool kept with a party."""
    proposing(monkeypatch, **more)
    for g in SCENE["map"]["goals"]:
        g["leader"] = {"slug": ARCH, "name": "Architect", "head": {"craft": "engineering", "race": "peon", "tier": "elder"}}
        g["size"] = size_of
        g.setdefault("tool", "")
    real = Stub.commands

    def commands(self):
        got = real(self)

        def tools_(a):
            self.calls.append(("ideas.tools", {k: v for k, v in a.items() if k not in ("link", "device")}))
            return copy.deepcopy(tools) if tools else {"error": "No command ideas.tools"}

        def sizes_(a):
            self.calls.append(("ideas.party_sizes", {k: v for k, v in a.items() if k not in ("link", "device")}))
            return the_moves(a["slug"]) if moves else {"error": "No command ideas.party_sizes"}

        def goal_save(a):
            if refuse and a.get("size"):
                self.calls.append(("ideas.goal_save", {k: v for k, v in a.items() if k not in ("link", "device")}))
                return {"error": refuse}
            r = got["ideas.goal_save"](a)
            for g in SCENE["map"]["goals"]:
                if g["slug"] == a.get("slug"):
                    if "tool" in a:
                        g["tool"] = a["tool"]
            return r
        return {**got, "ideas.tools": tools_, "ideas.party_sizes": sizes_, "ideas.goal_save": goal_save}
    monkeypatch.setattr(Stub, "commands", commands)


async def groups_of(select):
    return await select.evaluate("s => [...s.querySelectorAll('optgroup')].map(g => [g.label, [...g.querySelectorAll('option')].map(o => [o.value, o.textContent, o.disabled])])")


# -- New party ---------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_new_party_has_its_ai_tool_the_main_tool_picked_and_the_tools_in_three_groups(fake_repo, monkeypatch):
    with_tools(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        field = sheet.locator('.tool-field[data-sec="tool"]')
        await field.wait_for(timeout=WAIT_MS)
        select = field.locator("select")
        assert await select.evaluate("s => s.tagName") == "SELECT" and await select.input_value() == ""
        assert await select.locator("option:checked").inner_text() == "Main tool (Claude Code)"
        got = await groups_of(select)
        assert [g[0] for g in got] == ["Ready", "Not signed in", "Not installed"]
        assert got[0][1] == [["claude", "Claude Code", False], ["codex", "Codex", False], ["pi", "pi · runs its own model", False]]
        assert got[1][1] == [["cursor", "Cursor · runs its own model", False]]
        assert got[2][1] == [["agy", "Antigravity", True], ["hermes", "Hermes Agent · runs its own model", True]]
        assert len(calls(stub, "ideas.tools")) == 1
        box = await select.bounding_box()
        assert box["height"] >= 44 and box["x"] >= 0 and box["x"] + box["width"] <= 390
        await _shot_to(page, "phone-tool")
        assert await page.evaluate(NO_SCROLL) and await sheet.evaluate("(d) => d.scrollWidth <= d.clientWidth")


@pytest.mark.asyncio
async def test_the_tool_picked_goes_with_save_party_and_the_main_tool_sends_none(fake_repo, monkeypatch):
    with_tools(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        select = sheet.locator('.tool-field[data-sec="tool"] select')
        await select.select_option("codex")
        await sheet.get_by_label("What it is for").fill("Mobile app: features")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert sent["tool"] == "codex" and sent["size"] == "standard" and sent["about"] == "Mobile app: features" and sent["team"] == ["grunt"]
        await sheet.wait_for(state="hidden", timeout=WAIT_MS)
        stub.calls.clear()
        sheet = await _new_party(page)                                                                                         # the Main tool picked again sends none
        await sheet.locator('.tool-field[data-sec="tool"] select').select_option("codex")
        await sheet.locator('.tool-field[data-sec="tool"] select').select_option("")
        await sheet.get_by_label("What it is for").fill("Mobile app: architecture")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        assert "tool" not in calls(stub, "ideas.goal_save")[-1]


@pytest.mark.asyncio
async def test_a_tool_with_no_tiers_says_it_runs_its_own_model_where_the_price_was_and_one_not_signed_in_says_whose_sign_in_it_is(fake_repo, monkeypatch):
    with_tools(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        select = sheet.locator('.tool-field[data-sec="tool"] select')
        price = sheet.locator(".party-pricebox")
        await sheet.locator(".party-pricebox .party-price").first.wait_for(timeout=WAIT_MS)
        assert "This party: about" in norm(await price.inner_text()) and "runs its own model" not in norm(await price.inner_text()).lower()
        await select.select_option("pi")
        detail = norm(await price.inner_text())
        assert "Runs its own model: its price is its own." in detail and "a goal" not in detail                                # where the price was
        await select.select_option("")
        await sheet.locator(".party-pricebox .party-price").filter(has_text="This party: about").wait_for(timeout=WAIT_MS)
        await select.select_option("cursor")
        assert await select.input_value() == "cursor"                                                                          # stays picked
        assert "Not signed in: sign in on the computer" in await sheet.locator(".tool-field .tool-hint").inner_text()
        assert not calls(stub, "tools.sign_in")                                                                                # the phone opens nothing on the computer
        await sheet.get_by_label("What it is for").fill("On cursor")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        assert calls(stub, "ideas.goal_save")[-1]["tool"] == "cursor"


@pytest.mark.asyncio
async def test_a_seat_has_its_own_ai_tool_the_party_s_by_default_and_a_pick_goes_with_save_party_as_tools(fake_repo, monkeypatch):
    with_tools(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        seat = sheet.locator('[data-seat-tool="grunt"]')
        await seat.wait_for(timeout=WAIT_MS)
        assert "Party's tool · Claude Code" in norm(await seat.inner_text()) and (await seat.bounding_box())["height"] >= 44
        await seat.click()
        pick = page.get_by_role("dialog", name=re.compile("Its AI tool"))
        await pick.locator('[data-tool="codex"]').click()
        assert "Codex" in norm(await sheet.locator('[data-seat-tool="grunt"]').inner_text())
        await sheet.get_by_label("What it is for").fill("A grunt on codex")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert sent["tools"] == {"grunt": "codex"} and "tool" not in sent                                                      # the party's tool is the Main tool; the seat's is its own
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_host_without_the_list_has_no_field(fake_repo, monkeypatch):
    with_tools(monkeypatch, tools=None)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        await sheet.get_by_role("button", name="Save party").wait_for(timeout=WAIT_MS)
        assert await sheet.locator('[data-sec="tool"]').is_hidden() and await sheet.locator("[data-seat-tool]").count() == 0
        await sheet.get_by_label("What it is for").fill("No list")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert "tool" not in sent and "tools" not in sent


# -- About this party ----------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_about_this_party_has_its_ai_tool_and_a_change_saves_it_at_once(fake_repo, monkeypatch):
    with_tools(monkeypatch)
    SCENE["map"]["goals"][0]["tool"] = "codex"
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        about = await _about(page)
        sec = about.locator('[data-sec="Its AI tool"]')
        await sec.locator("select").wait_for(timeout=WAIT_MS)
        assert await sec.locator("select").input_value() == "codex" and (await sec.locator("h3").text_content()) == "Its AI tool"
        await sec.locator("select").select_option("")
        assert await _called(stub, "ideas.goal_save", {"slug": "passkey", "tool": ""})
        await sec.locator("select").select_option("pi")
        assert await _called(stub, "ideas.goal_save", {"slug": "passkey", "tool": "pi"})
        await page.wait_for_function("() => document.querySelector('dialog[aria-label=\"About this party\"] [data-sec=\"Its AI tool\"] select')?.value === 'pi'")
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_the_size_switch_shows_the_heads_that_join_and_leave_before_the_press_and_one_press_saves_it(fake_repo, monkeypatch):
    with_tools(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        about = await _about(page)
        size = about.locator('[data-sec="Its size"]')
        moves = size.locator(".size-moves")
        await moves.wait_for(timeout=WAIT_MS)
        assert norm(await moves.locator('[data-size-move="lean"]').inner_text()) == "Lean Leaves: Grunt, Tester, Reviewer"
        assert await moves.locator('[data-size-move="lean"] img').count() == 3
        assert norm(await moves.locator('[data-size-move="full"]').inner_text()) == "Full Joins: Security-Reviewer"
        assert await moves.locator('[data-size-move="standard"]').count() == 0                                                  # the size picked changes no one
        assert not calls(stub, "ideas.goal_save")                                                                               # nothing sent before the press
        await _shot_to(page, "phone-size-moves")
        assert await page.evaluate(NO_SCROLL) and await about.evaluate("(d) => d.scrollWidth <= d.clientWidth")
        await size.get_by_role("radio", name="Lean").click()
        assert await _called(stub, "ideas.goal_save", {"slug": "passkey", "size": "lean"})                                      # one press: no second confirm
        assert await about.get_by_role("button", name=re.compile("Make it Lean|Keep them")).count() == 0


@pytest.mark.asyncio
async def test_a_size_the_host_refuses_is_said_in_place_and_the_size_stays(fake_repo, monkeypatch):
    with_tools(monkeypatch, refuse="Tester has work open: it cannot leave")
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        about = await _about(page)
        size = about.locator('[data-sec="Its size"]')
        await size.get_by_role("radio", name="Lean").wait_for(timeout=WAIT_MS)
        await size.get_by_role("radio", name="Lean").click()
        note = size.locator('[role="alert"]')
        await note.wait_for(timeout=WAIT_MS)
        assert await note.inner_text() == "Tester has work open: it cannot leave" and await page.locator(".toast").count() == 0
        assert await size.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_host_without_party_sizes_shows_no_moves(fake_repo, monkeypatch):
    with_tools(monkeypatch, moves=False)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        about = await _about(page)
        size = about.locator('[data-sec="Its size"]')
        await size.get_by_role("radio", name="Full").wait_for(timeout=WAIT_MS)
        await page.wait_for_timeout(300)
        assert await size.locator(".size-moves").is_hidden() and await size.get_by_role("radio").count() == 3


def test_the_service_worker_has_the_tool_file_and_is_one_version_up():
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    shell = sw[sw.index("const SHELL"):sw.index("];", sw.index("const SHELL"))]
    assert int(re.search(r'const CACHE = "orkcraft-app-v(\d+)";', sw).group(1)) >= 91 and '"shell-party-tool.js"' in shell
