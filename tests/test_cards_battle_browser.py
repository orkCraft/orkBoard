"""**A battle** (goal "The battle and the gate", stage J; decisions §303), in a real browser on the `gui` fixture's host, `?table=cards` and no `?mock=1`: the hand's conflict card is the battle's card, one a goal however
many conflicts it keeps, with its emblem and *vs §N*; pressed, it opens the battle mat on the host's answer (`ideas.battle`) laid upright in goal 171's frame, with no lifted pair: §N face up above with what rests on it by
kind as the Board's files hold it, the route's columns with the new card's tokens, *No total*, the new card in Yours, no word of mana or price. A goal the skills laid keeps no conflict and so no battle. Opening it starts no pass, writes
nothing and spends nothing. The mat's ways are stage K's; these cases are the ones goal 171's stage G removed (the card's emblem and *vs*, the mat's cards, the phone's stack, Esc's focus), on the host's answer."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser
SHOTS = Path(os.environ["BATTLE_SHOTS"]) if os.environ.get("BATTLE_SHOTS") else None      # the pictures of the mat, drawn on the real page when it is set
CARD = ".frame-hand button.hand-card[data-kind=battle]"
LOG = "# Decisions\n\n## 212. The server owns every clock\nA clock on the client was cheated in the first playtest.\n\n## 213. A second old card\nIt stands.\n"
PAGE = ("---\nowner: board\nkind: idea\ntrack: tech\norder: {n}\nphase: {phase}\nroute: product, tech\nschema: 3\n---\n# {t}\n\n## Gist\nA goal.\n\n"
        "## Product\n### Talk\n- verdict: go\n- stance: fine\n- for: players see one clock\n\n## Tech\n### Talk\n- verdict: doubt — a client clock can be cheated\n- stance: careful\n")


def lay(gui):
    """A goal `timer` whose decision keeps two conflicts (§212 and §213) as `keeper.decide` leaves them, a goal `skills` laid by the skills (no conflict), the decisions log, a goal page and a test file naming §212."""
    from orkboard.realm import ideas, spec_sections
    server, _b = gui
    host = server.host
    root = host.ideas.root()
    for title in ("Product", "Tech"):
        if not ideas.track_page(root, title.lower()):
            ideas.add_track(root, title)
    repo = Path(host.repo_root)
    pages = root / ideas.IDEAS
    pages.mkdir(parents=True, exist_ok=True)
    for n, (slug, phase) in enumerate((("timer", "spec"), ("skills", "spec")), 1):
        (pages / f"{slug}.md").write_text(PAGE.format(n=n, t=slug.title(), phase=phase), encoding="utf-8")
        ideas.save_state(host.ideas.state_dir, slug, state="decided")
    way = spec_sections.record(host.ideas.state_dir, "timer")
    way["decision"] = {"number": 240, "title": "Round timer", "text": "x", "confirmed": False,
                       "conflicts": [{"number": 212, "point": "the server owns every clock of a round", "answer": ""}, {"number": 213, "point": "a second one", "answer": ""}]}
    spec_sections.save_record(host.ideas.state_dir, "timer", way)
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs" / "decisions.md").write_text(LOG, encoding="utf-8")
    rest = repo / "llm-wiki" / "general" / "pages" / "ideas"          # the files a goal that names §212 lies in, as decision_refs reads them
    rest.mkdir(parents=True, exist_ok=True)
    (rest / "rests-on-212.md").write_text("---\nowner: board\nkind: idea\ntrack: tech\norder: 3\nphase: new\nschema: 3\n---\n# Rests\n\n## Gist\nIt rests on §212.\n", encoding="utf-8")
    (repo / "tests").mkdir(exist_ok=True)
    (repo / "tests" / "test_clock.py").write_text('"""Guards decisions §212."""\n\ndef test_clock():\n    pass\n', encoding="utf-8")
    return host


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def opened(gui, width=1440, height=900, **kw):
    host = lay(gui)
    server, browser = gui
    pg = browser.new_page(viewport={"width": width, "height": height}, **kw)
    pg.goto(server.url + ("&" if "?" in server.url else "?") + "table=cards")
    pg.wait_for_selector(".cards-lane", state="attached", timeout=WAIT_MS)
    return pg, host


def test_the_conflict_card_is_one_battle_card_a_goal_with_its_emblem_and_vs_and_a_goal_of_the_skills_has_none(gui):
    pg, _host = opened(gui)
    pg.locator(CARD).first.wait_for(timeout=WAIT_MS)
    assert pg.locator(CARD).count() == 1 and pg.locator(CARD).get_attribute("data-goal") == "timer"          # two conflicts, one card
    card = pg.locator(CARD)
    emblem = card.locator(".cards-emblem")
    assert emblem.count() == 1 and emblem.get_attribute("aria-hidden") == "true" and emblem.locator("i").count() == 3
    text = card.inner_text()
    assert "vs §212 and §213" in text and "battle" in text
    assert pg.locator('.frame-hand .hand-card[data-kind=conflict]').count() == 0                        # the old card is not dealt on this table
    assert pg.locator(".frame-hand .hand-card[data-goal=skills][data-kind=battle]").count() == 0
    pg.close()


def test_pressed_it_opens_the_mat_upright_on_the_hosts_answer_with_no_lifted_pair_and_starts_nothing(gui, monkeypatch):
    pg, host = opened(gui)
    log = Path(host.repo_root) / ".orkcraft" / "usage" / "events.jsonl"
    before = log.read_text(encoding="utf-8") if log.exists() else ""
    calls = []
    for name in ("ask", "call", "work_call", "board_ask", "draft", "answer", "reword", "ripe_begin", "decide"):
        if hasattr(host.ideas.keeper, name):
            monkeypatch.setattr(host.ideas.keeper, name, lambda *a, _n=name, **k: calls.append(_n))
    pg.locator(CARD).first.click(timeout=WAIT_MS)
    sp = pg.locator("[data-spread=battle]")
    sp.wait_for(timeout=WAIT_MS)
    sp.locator("[data-old]").first.wait_for(timeout=WAIT_MS)
    assert pg.locator(".hand-earlier, .hand-lifted[data-kind=conflict], .hand-earlier-host").count() == 0       # §254.6's lifted pair is not drawn here
    olds = sp.locator("[data-old]")
    assert olds.count() == 2 and olds.first.get_attribute("data-old") == "§212"
    assert "rests on it: 1 goal · 1 test" in olds.first.inner_text() and "nothing rests on it" in olds.nth(1).inner_text()      # as the files hold it
    assert sp.locator(".bt-decision .bt-sect").first.inner_text() == "§212"
    zone_y = lambda label: sp.locator(f".mf-zone[aria-label='{label}']").bounding_box()["y"]  # noqa: E731
    line_y = sp.locator(".bt-line").bounding_box()["y"]
    assert zone_y("What it goes against") < line_y < zone_y("Yours")                                      # upright: against, the line, Yours
    assert [c.get_attribute("data-craft") for c in sp.locator(".bt-craft").all()] == ["product", "tech"]
    assert sp.locator(".bt-craft .cards-ct").count() == 2 and "no total" in sp.text_content().lower()
    assert sp.locator(".bt-yours .sp-card").count() == 1 and "Timer" in sp.locator(".bt-yours").inner_text()
    low = sp.text_content().lower()
    assert not any(w in low for w in ("mana", "price", "potion", "to undo", "$"))
    sp.locator("[data-old='§212']").locator("button").click()                                            # pressed: its slip lists what rests on it
    slip = sp.locator(".bt-slip")
    assert "rests-on-212" in slip.inner_text() and "tests/test_clock.py" in slip.inner_text()
    shot(pg, "J-battle-desk")
    inside = sp.evaluate("""(el) => { const f = el.querySelector('.mf-field').getBoundingClientRect();
      return [...el.querySelectorAll('.mf-zone, .bt-line, .bt-one')].every((n) => { const b = n.getBoundingClientRect(); return b.top >= f.top - 1 && b.bottom <= f.bottom + 1 && b.left >= f.left - 1 && b.right <= f.right + 1; }); }""")
    assert inside
    assert (log.read_text(encoding="utf-8") if log.exists() else "") == before and calls == []              # no pass begun, nothing spent, nothing written
    pg.close()


def test_a_goal_with_no_conflict_opened_by_its_address_draws_no_battle(gui):
    pg, _host = opened(gui)
    pg.evaluate("() => import('/static/js/cards/spreads/open.js').then((m) => m.openSpread({ kind: 'battle', slug: 'skills' }))")
    pg.wait_for_timeout(500)
    assert pg.locator("[data-spread=battle]").count() == 0
    pg.close()


def test_esc_puts_the_mat_away_and_the_focus_is_on_the_battle_card(gui):
    pg, _host = opened(gui)
    pg.locator(CARD).first.click(timeout=WAIT_MS)
    pg.locator("[data-spread=battle] [data-old]").first.wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    assert pg.locator(".sp-veil").count() == 0
    pg.wait_for_function("() => document.activeElement?.dataset?.kind === 'battle'", timeout=3000)
    assert pg.evaluate("() => document.activeElement?.dataset?.kind") == "battle"
    pg.close()


def test_on_a_phone_the_battle_is_the_whole_screen_after_a_reload_upright_with_back_and_no_sideways_scroll(gui):
    pg, _host = opened(gui, 390, 844, has_touch=True, is_mobile=True)
    pg.locator("[data-key='card:battle/timer']").wait_for(state="attached", timeout=WAIT_MS)                                    # its card in the phone's row
    pg.evaluate("() => import('/static/js/cards/spreads/open.js').then((m) => m.openSpread({ kind: 'battle', slug: 'timer' }))")
    sp = pg.locator("[data-spread=battle]")
    sp.locator("[data-old]").first.wait_for(timeout=WAIT_MS)
    shot(pg, "J-battle-phone")
    assert pg.url.endswith("#mat=battle:timer") or "#mat=battle:timer" in pg.url
    pg.reload()                                                                                          # its address opens it again
    sp.locator("[data-old]").first.wait_for(timeout=WAIT_MS)
    box = sp.locator(".mf").bounding_box()
    assert box["width"] >= 388 and sp.locator(".sp-shut").inner_text().strip() == "Back"
    ys = [sp.locator(sel).first.bounding_box()["y"] for sel in (".bt-against", ".bt-line", ".bt-yours")]
    assert ys == sorted(ys)
    assert pg.evaluate("() => document.documentElement.scrollWidth") <= 390
    assert json.loads(sp.evaluate("(el) => JSON.stringify([...el.querySelectorAll('.bt *')].filter((n) => n.children.length === 0 && n.textContent.trim() && parseFloat(getComputedStyle(n).fontSize) < 12).length)")) == 0
    pg.close()
