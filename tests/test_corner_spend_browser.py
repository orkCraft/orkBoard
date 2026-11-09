"""Spec 168 C5 (docs/specs/168-the-window-played-as-a-card-games-table.md, decisions §283.17, §283.18), in a real browser against a stub host: a card's bottom right is the spend, with its unit beside it —
the share of its tool's window where the page has measured it, money only with a price (Codex has none), else tokens; at work what it has spent so far, done what it spent in all, ahead ≈ its party's average
for its kind; *asks you* wins while a question waits (tests/test_corners_browser.py). The small card has no room for it: its time and its figure are in its preview. The verdicts by their signs (corners.js `Verdict`)."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import open_column  # noqa: E402
from tests.test_corners_browser import table  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser

CODEX = {"tokens": 12000, "usd": None, "tool": "codex"}
PRICED = {"tokens": 5000, "usd": 0.42, "tool": "claude"}


def foot(pg, key):
    return pg.locator(f'[data-lkey="{key}"] .corner--foot .corner__much')


def put(host, slug, tid, **more):
    node = next(n for n in host.nodes if n["slug"] == slug)
    next(t for t in node["tasks"] if t["id"] == tid).update(more)
    host.push()


def test_a_codex_task_says_tokens_and_no_money_and_a_priced_one_says_dollars(table):
    pg, host = table
    put(host, "rules", "r1", spend=CODEX)
    put(host, "calm", "k1", spend=PRICED)
    codex, priced = foot(pg, "t:task:rules/r1"), foot(pg, "t:task:calm/k1")
    codex.wait_for(timeout=WAIT_MS)
    priced.wait_for(timeout=WAIT_MS)
    assert codex.inner_text().strip() == "12k tok" and codex.get_attribute("data-unit") == "tokens", "Codex has no prices: tokens"
    assert "$" not in codex.inner_text()
    assert priced.inner_text().strip() == "$0.42" and priced.get_attribute("data-unit") == "usd", "a priced task with no window measured: money"
    for much in (codex, priced):
        assert much.get_attribute("data-est") is None
        card = much.locator("xpath=ancestor::*[contains(@class,'table-card')]")
        assert card.locator(".corner--foot").bounding_box()["height"] <= 20.5 and card.bounding_box()["width"] == 144, "it fits the foot of the 144 x 202 card"
        fb, mb = card.locator(".corner--foot").bounding_box(), much.bounding_box()
        assert mb["x"] + mb["width"] <= fb["x"] + fb["width"] + 0.5, "the figure stays inside the card"


def test_the_share_of_the_window_where_it_is_measured_and_a_task_ahead_is_an_estimate(table):
    pg, host = table
    snap = host.snapshot
    host.snapshot = lambda: _with_rate(snap())
    put(host, "rules", "r1", spend={"tokens": 5000, "usd": 0.42, "tool": "claude"})
    put(host, "calm", "k1", spend=CODEX)
    put(host, "seat", "s1", spend=None, spend_est={"tokens": 8000, "usd": 0.7, "tool": "claude", "n": 4})
    share, codex = foot(pg, "t:task:rules/r1"), foot(pg, "t:task:calm/k1")
    share.wait_for(timeout=WAIT_MS)
    assert share.inner_text().strip().endswith("%") and share.get_attribute("data-unit") == "share" and "window" in share.get_attribute("title"), "the share of the tool's window, as the mana measures it"
    assert codex.inner_text().strip() == "12k tok", "a tool whose window is not measured stays in tokens"
    ahead = pg.evaluate("""async () => { const c = await import('/static/js/table/corners.js'); return c.muchOf({ est: c.figureOf({ tokens: 8000, usd: 0.7, tool: 'claude' }) }); }""")
    assert ahead["est"] is True and ahead["text"].startswith("≈ ") and ahead["unit"] == "share", ahead
    drawn = pg.evaluate("""async () => {
      const [{ render, h }, c] = await Promise.all([import('preact'), import('/static/js/table/corners.js')]);
      const box = document.createElement('div'); box.style.width = '120px'; document.body.appendChild(box);
      render(h(c.CornerFoot, { much: c.muchOf({ est: c.figureOf({ tokens: 18000, usd: null, tool: 'codex' }) }) }), box);
      const e = box.querySelector('.corner__much'); return [e.textContent, e.dataset.est, e.dataset.unit]; }""")
    assert drawn == ["≈ 18k tok", "1", "tokens"], "a card ahead: the party's average, marked as an estimate"


def test_the_small_cards_time_and_figure_are_in_its_preview_only(gui):
    pg, host, log = open_column(gui)
    try:
        pg.evaluate("""async () => {
          const [{ render, h }, { SmallCard }] = await Promise.all([import('preact'), import('/static/js/table/smallcard.js')]);
          const box = document.createElement('div'); box.id = 'sm-test'; box.style.cssText = 'position:fixed;left:400px;top:120px;z-index:5'; document.body.appendChild(box);
          render(h(SmallCard, { n: { slug: 'g', title: 'Goal g', element: 'ice', hue: 'ice', type: { sign: 'bug' } }, time: '4 min left', much: '12k tok' }), box);
        }""")
        card = pg.locator("#sm-test .sm")
        card.wait_for(timeout=WAIT_MS)
        assert card.inner_text().strip() == "", "no words on the small card"
        card.hover()
        pg.locator('[data-preview="face"]').wait_for(timeout=WAIT_MS)
        assert pg.locator('[data-preview="face"] .pv-time__t').inner_text() == "4 min left" and pg.locator('[data-preview="face"] .pv-time__m').inner_text() == "12k tok"
        box = pg.locator('[data-preview="face"]').bounding_box()
        assert (round(box["width"]), round(box["height"])) == (144, 202)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_verdicts_by_their_signs(table):
    pg, host = table
    got = pg.evaluate("""async () => {
      const [{ render, h }, c] = await Promise.all([import('preact'), import('/static/js/table/corners.js')]);
      const box = document.createElement('div'); document.body.appendChild(box);
      const colour = (v) => { const d = document.createElement('i'); d.style.color = v; document.body.append(d); const x = getComputedStyle(d).color; d.remove(); return x; };
      const cases = [['go', {}], ['doubt', {}], ['no', {}], ['no', { failed: true }], ['doubt', { waits: true }]];
      render(h('div', null, ...cases.map(([verdict, more]) => h(c.Verdict, { verdict, ...more }))), box);
      const out = [...box.querySelectorAll('.verdict')].map((e) => ({ sign: e.querySelector('.ork-sign').className, colour: getComputedStyle(e).color, ring: getComputedStyle(e).boxShadow }));
      return { out, ink: colour('var(--ork-ink)'), ok: colour('var(--ork-success)'), bad: colour('var(--ork-danger)') };
    }""")
    out, ink, ok, bad = got["out"], got["ink"], got["ok"], got["bad"]
    assert [o["sign"].replace("ork-sign ", "") for o in out] == ["check", "alert", "cross", "cross", "alert"]
    assert out[0]["colour"] == ok and out[0]["ring"] == "none", "✓ in the success colour, no ring"
    assert out[1]["colour"] == ink and out[2]["colour"] == ink, "! and ✗ in the ink"
    assert out[3]["colour"] == bad, "red only for a call that failed"
    assert out[4]["ring"] != "none" and out[1]["ring"] == "none" and out[2]["ring"] == "none", "the alert's ring only where a question waits"


def _with_rate(snapshot):
    state = snapshot["state"]
    state["rate"] = {"usd_per_pct": 0.35, "tool": "claude", "window": "5h"}
    return snapshot
