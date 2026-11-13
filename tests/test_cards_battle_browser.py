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


# -- stage K: the battle's ways in the hand (decisions §303.4) -------------------------------------------------------------------------------------

class Spy:
    """`ideas.conflict` and `ideas.undo`, answered by stubs that log what the page sent (the host's own effect and events are tests/test_conflict.py's); `lefts` the conflicts each answer leaves."""

    def __init__(self, host, lefts):
        self.commands, self.log, self.lefts = host.commands, [], list(lefts)
        self.was = {n: self.commands.get(n) for n in ("ideas.conflict", "ideas.undo")}
        self.commands["ideas.conflict"] = self.conflict
        self.commands["ideas.undo"] = lambda args: (self.log.append(("ideas.undo", dict(args))), {"ok": True})[1]

    def conflict(self, args):
        self.log.append(("ideas.conflict", dict(args)))
        return {"ok": True, "left": self.lefts.pop(0) if self.lefts else 0, "reworded": args.get("choice") != "replace"}

    def sent(self, name):
        return [a for n, a in self.log if n == name]

    def close(self):
        self.commands.update({k: v for k, v in self.was.items() if v})


def battle_open(gui, how="hand", width=1440, height=900, lefts=(1, 0), **kw):
    pg, _host = opened(gui, width, height, **kw)
    spy = Spy(gui[0].host, lefts)
    if how == "hand":
        pg.locator(CARD).first.click(timeout=WAIT_MS)
    else:
        pg.evaluate("() => import('/static/js/cards/spreads/open.js').then((m) => m.openSpread({ kind: 'battle', slug: 'timer' }))")
    pg.locator("[data-spread=battle] [data-old]").first.wait_for(timeout=WAIT_MS)
    return pg, spy


def test_the_hand_holds_the_three_ways_each_with_its_line_and_the_seal_is_dim_until_a_way_that_asks_is_picked(gui):
    pg, spy = battle_open(gui)
    try:
        ways = pg.locator(".frame-hand .mathand [data-way]")
        assert [w.locator("b").inner_text() for w in ways.all()] == ["New wins", "Old wins", "Your words"]
        lines = [w.locator("small").inner_text() for w in ways.all()]
        assert "replaces it" in lines[0] and "One press" in lines[0] and "§212" in lines[0]
        assert "worded again within §212" in lines[1] and "Asks first" in lines[1] and "yours" in lines[2].lower()
        seal = pg.locator("[data-spread=battle] .mf-seal")
        assert seal.get_attribute("aria-disabled") == "true" and "pick Old wins or Your words" in seal.inner_text()
        seal.click(force=True)
        pg.wait_for_timeout(200)
        assert not spy.log
        shot(pg, "K-battle-desk")
    finally:
        spy.close()
        pg.close()


def test_new_wins_is_one_press_from_the_hand_the_toast_offers_undo_and_the_next_old_card_is_laid(gui):
    pg, spy = battle_open(gui, "hand")
    try:
        pg.locator(".frame-hand .mathand [data-way=new]").click()
        pg.wait_for_function("() => document.body.innerText.includes('Undo')", timeout=WAIT_MS)
        assert spy.sent("ideas.conflict") == [{"idea": "timer", "number": 212, "choice": "replace", "from": "hand"}]
        assert pg.locator("[data-spread=battle]").count() == 1                                      # one left: the mat stays and lays the next
        pg.get_by_role("button", name="Undo", exact=True).click()
        pg.wait_for_timeout(300)
        assert spy.sent("ideas.undo") == [{"idea": "timer"}]
        pg.locator(".frame-hand .mathand [data-way=new]").click()                                   # the last one: the mat closes
        pg.locator("[data-spread=battle]").wait_for(state="detached", timeout=WAIT_MS)
        assert [a["choice"] for a in spy.sent("ideas.conflict")] == ["replace", "replace"]
    finally:
        spy.close()
        pg.close()


def test_old_wins_lights_the_seal_with_its_cost_said_before_anything_is_sent_and_goes_sealed_from_the_mat(gui):
    pg, spy = battle_open(gui, "mat", lefts=(0,))
    try:
        pg.locator(".frame-hand .mathand [data-way=old]").click()
        picked = pg.locator(".frame-hand .mathand [data-way=old]").evaluate("(e) => { const s = getComputedStyle(e); return [s.outlineStyle, s.outlineWidth]; }")
        assert picked == ["solid", "2px"], picked                                                   # the picked way is marked on its own card (Design's note on P2)
        seal = pg.locator("[data-spread=battle] .mf-seal")
        assert seal.get_attribute("aria-disabled") is None and "Old wins" in seal.inner_text() and "A paid pass" in seal.inner_text() and "$" in seal.inner_text()
        assert not spy.log                                                                          # nothing is sent before the seal
        seal.click()
        pg.locator("[data-spread=battle]").wait_for(state="detached", timeout=WAIT_MS)
        assert spy.sent("ideas.conflict") == [{"idea": "timer", "number": 212, "choice": "keep", "sealed": True, "from": "mat"}]
        assert not spy.sent("ideas.undo") and "Undo" not in pg.locator("body").inner_text()      # a sealed move offers no Undo
    finally:
        spy.close()
        pg.close()


def test_your_words_opens_its_field_in_the_hands_place_then_the_seal_sends_them_and_esc_in_the_field_leaves_the_mat(gui):
    pg, spy = battle_open(gui, "hand", lefts=(0,))
    try:
        pg.locator(".frame-hand .mathand [data-way=words]").click()
        field = pg.get_by_role("textbox", name="Your words for the new decision")
        field.wait_for(timeout=WAIT_MS)
        assert pg.locator(".frame-hand .mathand [data-way=new]").count() == 0                       # the field lies in the ways' place
        shot(pg, "K-battle-words")
        pg.keyboard.press("Escape")                                                                 # closes the field only
        pg.locator(".frame-hand .mathand [data-way=words]").wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => document.activeElement?.dataset?.way === 'words'", timeout=3000)
        assert pg.locator("[data-spread=battle]").count() == 1
        pg.locator(".frame-hand .mathand [data-way=words]").click()
        pg.get_by_role("textbox", name="Your words for the new decision").fill("Eight seconds, the server keeps the end only")
        seal = pg.locator("[data-spread=battle] .mf-seal")
        assert seal.get_attribute("aria-disabled") == "true"                                        # written is not sent: the seal is still dim
        pg.keyboard.press("Enter")
        pg.wait_for_function("() => !document.querySelector('.hand-pen')", timeout=WAIT_MS)
        assert not spy.log and seal.get_attribute("aria-disabled") is None and "Your words" in seal.inner_text() and "$" in seal.inner_text()
        seal.click()
        pg.locator("[data-spread=battle]").wait_for(state="detached", timeout=WAIT_MS)
        assert spy.sent("ideas.conflict") == [{"idea": "timer", "number": 212, "choice": "other", "text": "Eight seconds, the server keeps the end only", "sealed": True, "from": "hand"}]
    finally:
        spy.close()
        pg.close()


def test_tab_goes_through_the_old_cards_the_line_yours_the_hands_ways_and_the_seal_and_close_each_with_a_visible_focus(gui):
    pg, spy = battle_open(gui, "hand")
    try:
        seen = []                                                                                   # the focus starts on Close
        for _ in range(30):
            pg.keyboard.press("Tab")
            seen.append(pg.evaluate("""() => { const a = document.activeElement;
              return [(a.closest('[data-old]') || a).dataset.old || a.dataset.way || a.dataset.seal || (a.classList.contains('sp-shut') ? 'close' : a.closest('.bt-line') ? 'line' : a.closest('.bt-yours') ? 'yours' : a.tagName),
                      a.matches(':focus-visible')]; }"""))
            if len(seen) > 1 and seen[-1] == seen[0]:
                break
        names = [s[0] for s in seen]
        assert all(s[1] for s in seen), seen
        for want in ("§212", "§213", "line", "yours", "new", "old", "words", "reword", "close"):
            assert want in names, names
        assert names.index("§212") < names.index("§213") < names.index("line") < names.index("yours") < names.index("new") < names.index("old") < names.index("words") < names.index("reword") < names.index("close")
    finally:
        spy.close()
        pg.close()


def test_the_ways_lie_in_a_row_at_the_foot_on_a_phone_and_the_seal_follows_them(gui):
    pg, spy = battle_open(gui, "mat", 390, 844, has_touch=True, is_mobile=True)
    try:
        ways = pg.locator("[data-spread=battle] .sp-hand [data-way]")
        assert [w.locator("b").inner_text() for w in ways.all()] == ["New wins", "Old wins", "Your words"]
        assert ways.first.locator("small").is_hidden() and "One press" in ways.first.get_attribute("aria-label")
        assert pg.evaluate("() => document.documentElement.scrollWidth") <= 390
        pg.locator("[data-spread=battle] .sp-hand [data-way=old]").click()
        assert "Old wins" in pg.locator("[data-spread=battle] .mf-seal").inner_text()
        shot(pg, "K-battle-phone")
    finally:
        spy.close()
        pg.close()


def test_the_wording_is_the_lexicons():
    from orkboard.realm import lexicon
    src = (Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static" / "js" / "cards" / "spreads" / "battle.js").read_text(encoding="utf-8")
    for key, word in (("new_wins", "New wins"), ("old_wins", "Old wins"), ("your_words", "Your words")):
        assert lexicon.term(key) == word and f'"{word}"' in src
    assert "battle_settle" not in src
