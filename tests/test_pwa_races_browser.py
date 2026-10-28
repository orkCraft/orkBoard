"""Who does a task on the phone (decisions §53; the desktop's tests/test_races_browser.py): Agents at 390 × 844 with each agent's
head (its craft's race in its tier's gear) beside its name and each card's head, the agent's sheet picking the craft and showing
the head it will wear, the menu's Agents button an ork; every head is served beside the app's files. Against the stub of
test_pwa_shell_browser.py with the host's heads."""
from __future__ import annotations

import pytest

from orkboard.realm import roles
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, _agents, _called, _menu, _phone, _shot  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

# The desktop's Agents page went (spec 98 A); its stub's roles and heads stay here for the phone's.
MINE = {"layout": {"slug": "layout", "name": "Layout", "model": "elder", "max_parallel": 1, "instruction": "", "builtin": False, "craft": "design"},
        "seer": {"slug": "seer", "name": "Seer", "model": "", "max_parallel": 2, "instruction": "", "builtin": False, "craft": "data"},
        "herald": {"slug": "herald", "name": "Herald", "model": "laborer", "max_parallel": 1, "instruction": "", "builtin": False, "craft": "marketing"}}
BUILTIN = {"taskmaster": {"model": "elder", "craft": "engineering"}, "grunt": {"model": "", "craft": "engineering"}}


def _crafts(target="balance"):
    models = ["", *roles.TIERS]
    return [{"craft": c, "label": roles.CRAFT_LABELS[c], "race": roles.RACES[c], "heads": {m: roles.head_tier(m, target) for m in models}}
            for c in roles.CRAFTS]


def _heads(name, got, all_roles, a=None):
    """What the host adds to a stub's answer: each role's head and craft, each chip's head, the crafts (realm/roles.py)."""
    def role_of(slug):
        return {**BUILTIN.get(slug, {}), **all_roles.get(slug, {})} or BUILTIN["grunt"]
    if name == "ideas.agents":
        for b in got["roles"]:
            b["head"] = roles.head(role_of(b["role"]), "balance")
            for c in b.get("chips") or []:
                if "task" in c:
                    c["head"] = roles.head(role_of(c.get("role") or b["role"]), "balance", c.get("tier") or "warrior")
    if name == "ideas.roles":
        for r in got["roles"]:
            r["craft"] = role_of(r["slug"]).get("craft", "engineering")
            r["head"] = roles.head(role_of(r["slug"]), "balance")
        got["crafts"] = _crafts()
    if name == "ideas.role_save" and a and a.get("craft"):
        all_roles[got["slug"]]["craft"] = a["craft"]
    return got


def _with_heads(stub):
    stub.roles.update({k: dict(v) for k, v in MINE.items()})
    run = stub.run
    stub.run = lambda name, a: _heads(name, run(name, a), stub.roles, a)       # the commands call stub.run when they run
    stub.bump({})


async def _drawn(page, selector):
    return await page.evaluate(f"[...document.querySelectorAll({selector!r})].every((i) => i.complete && i.naturalWidth > 0)")


@pytest.mark.asyncio
async def test_agents_wear_their_races_the_cards_their_runners_and_the_button_is_a_robot(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        _with_heads(stub)
        button = (await _menu(page)).get_by_role("button", name="Agents")
        assert await button.locator("img").count() == 0                                                   # a head says a craft: the button is orkUI's robot
        assert (await button.locator("svg.ork-icon use").get_attribute("href")).endswith("#robot")
        await button.click()
        agents = page.locator(".screen .agents")
        await agents.locator(".role[data-slug=layout]").wait_for(timeout=WAIT_MS)
        head = lambda slug: agents.locator(f".role[data-slug={slug}] .role-head > img.ork-race__head")       # noqa: E731
        assert await head("layout").get_attribute("src") == "races/elf-elder.png"
        assert await head("seer").get_attribute("src") == "races/goblin-warrior.png"
        assert await head("herald").get_attribute("src") == "races/gnome-laborer.png"
        assert await head("grunt").get_attribute("src") == "races/peon-warrior.png"
        assert (await head("layout").bounding_box())["width"] == 24
        assert (await agents.locator(".role[data-slug=seer] .role-head").get_attribute("aria-label")).startswith("Seer: a goblin, Data, Seasoned; up to 2 at once")
        card = agents.locator(".role[data-role=grunt] .chip").first
        assert await card.locator("img.ork-race__head").get_attribute("src") == "races/peon-warrior.png"
        assert (await card.locator("img.ork-race__head").bounding_box())["width"] == 24              # a head is drawn at 24 × 22, never at 12 (decisions §161)
        assert await _drawn(page, "img.ork-race__head")
        assert await page.evaluate(NO_SCROLL)
        await _shot(page, "phone-agents-races-390x844")


@pytest.mark.asyncio
async def test_the_agents_sheet_picks_the_craft_and_shows_the_head_it_will_wear(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        _with_heads(stub)
        await _agents(page)
        await page.locator(".agents .role[data-slug=layout]").wait_for(timeout=WAIT_MS)
        await page.get_by_role("button", name="+ Add agent").click()
        await page.get_by_role("dialog", name="Add an agent").get_by_role("button", name="Your own").click()
        sheet = page.get_by_role("dialog", name="Add agent")
        await sheet.get_by_label("Name").fill("Counter")
        craft = sheet.get_by_label("Craft")
        assert [" ".join((await o.text_content()).split()) for o in await craft.locator("option").all()] == [
            "Engineering: an ork", "Design: an elf", "Data: a goblin", "Marketing: a gnome", "Product: a lich"]
        await craft.select_option("data")
        await sheet.get_by_label("Model").select_option("laborer")
        assert await sheet.locator(".craft-now img.ork-race__head").get_attribute("src") == "races/goblin-laborer.png"
        assert "Novice" in await sheet.locator(".craft-now").inner_text()
        await sheet.get_by_role("button", name="Save agent").click()
        assert await _called(stub, "ideas.role_save", {"name": "Counter", "model": "laborer", "max_parallel": 2, "instruction": "", "kinds": [],
                                                       "craft": "data"})
