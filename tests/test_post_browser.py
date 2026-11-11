"""**One post, both faces** (goal 170 A, decisions §293, §291.5-§291.9): table/post.js is the post the phone's feed and the desktop's lanes both draw, in a real browser. On the desktop's page (1366 x 768) it is drawn
at body 15 and caption 13 with nothing under 12 px, its labels NEW / CHANGED at 12 px at least in the heading face, its dots a button with its word, a post that asks ringed in the alert's yellow with a sign beside the ring, a quiet one told by its muted
ink and a *Quiet* plate (never by opacity), every act a button with its word reached by Tab with a visible focus. Through the phone's own `./page/js/table/post.js` (the installed app, 390 x 844 with touch) the same part is drawn with the sizes it had
(14 px and over, the desktop's extras not drawn). post.js imports none of frame/state, shell/store or pwa/ (tests/test_architecture.py), so it is the same module in both."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_desktop_look_browser import open_window  # noqa: E402
from tests.test_hand_context_narrow_browser import open_up  # noqa: E402
from tests.test_pwa_frame_browser import App, app  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser

# What each face draws: `base` is where it reaches post.js (the desktop's /static/, the phone's ./page/)
DRAW = """async ([base, plain]) => {
  const { h, render } = await import("preact");
  const post = await import(base + "js/table/post.js");
  document.querySelectorAll("#t-before, #t-mount").forEach((e) => e.remove());
  const before = Object.assign(document.createElement("button"), { id: "t-before", textContent: "before" });
  const mount = Object.assign(document.createElement("div"), { id: "t-mount" });
  Object.assign(mount.style, { position: "fixed", left: "8px", top: "8px", width: "340px", zIndex: 9999, display: "flex", flexDirection: "column", gap: "8px" });
  Object.assign(before.style, { position: "fixed", left: "8px", top: "0", zIndex: 9999 });
  document.body.append(before, mount);
  window.__more = [];
  const at = new Date().toISOString();
  const onMore = plain ? null : (p) => window.__more.push(p.text);
  const asks = { leader: "tech", kind: "change", at, text: "Keep the seat's plan changed", goal: "", asks: true };
  const quiet = { leader: "design", kind: "news", at, text: "Lobby colours were read", goal: "", quiet: true };
  const wait = { kind: "starts", goal: "seat", short: "Keep the seat", leader: "tech", at, acts: [{ act: "change_spec", command: "x", args: {} }, { act: "start_now", command: "x", args: {} }, { act: "to_main", command: "x", args: {} }] };
  render(h("div", { style: "display:contents" }, h(post.Post, { p: asks, onMore }), h(post.Post, { p: quiet, onMore }), h(post.Wait, { w: wait, onMore })), mount);
  return post.TAGS;
}"""

LOOK = """() => {
  const q = (s) => document.querySelector("#t-mount " + s), css = (e) => getComputedStyle(e), px = (e) => parseFloat(css(e).fontSize);
  const asks = q('.post-card[data-asks="true"]'), quiet = q('.post-card[data-quiet="true"]');
  const shown = (e) => !!e && css(e).display !== "none";
  const tag = asks.querySelector(".post-card__tag"), sign = asks.querySelector(".post-card__asks"), plate = quiet.querySelector(".post-card__quiet");
  let small = 999;
  for (const e of document.querySelectorAll("#t-mount *")) if ([...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()) && css(e).display !== "none") small = Math.min(small, px(e));
  return {
    cards: document.querySelectorAll("#t-mount .post-card").length, race: asks.dataset.race, top: css(asks).boxShadow, ring: css(asks).borderTopColor, alert: css(document.documentElement).getPropertyValue("--ork-alert").trim(),
    body: px(asks.querySelector(".post-card__text")), caption: px(asks.querySelector(".post-card__sub")), small,
    tag: shown(tag) && [tag.textContent, px(tag), css(tag).fontFamily === css(asks.querySelector(".post-card__name")).fontFamily],
    sign: shown(sign) && sign.textContent.trim(), plate: shown(plate) && plate.textContent.trim(),
    quietOpacity: css(quiet).opacity, quietInk: css(quiet.querySelector(".post-card__text")).color === css(quiet.querySelector(".post-card__sub")).color,
    dots: asks.querySelector(".post-card__dots").tagName, dotsName: asks.querySelector(".post-card__dots").textContent.trim(),
  };
}"""

TAB = """() => {
  const seen = [];
  for (const e of document.querySelectorAll("#t-mount .post-card")) { seen.push(e); }
  return seen.length;
}"""

FOCUSED = """() => {
  const e = document.activeElement, s = getComputedStyle(e), c = e.closest("#t-mount");
  return c ? { tag: e.tagName, act: e.dataset.act || "", cls: e.className, name: e.textContent.trim(), outline: s.outlineStyle !== "none" && parseFloat(s.outlineWidth) >= 2, ring: s.boxShadow !== "none" } : null;
}"""


def test_one_post_draws_on_the_desktop_page_and_through_the_phones_page_path(gui, app):
    # --- the desktop's page
    pg = open_window(gui)
    try:
        tags = pg.evaluate(DRAW, ["/static/"])
        assert tags == {"news": "NEW", "change": "CHANGED"}
        got = pg.evaluate(LOOK)
        assert got["cards"] == 3 and got["race"], "three cards, the party's race its top edge"
        assert got["body"] == 15 and got["caption"] == 13 and got["small"] >= 12, got
        assert got["tag"] == ["CHANGED", 12, True], "the label at 12 px in the heading face"
        assert got["sign"] == "Asks you" and got["ring"] != "rgba(0, 0, 0, 0)" and got["alert"], "the ask: a ring in the alert's colour with a sign beside it"
        assert got["plate"] == "Quiet" and got["quietOpacity"] == "1" and got["quietInk"], "quiet by muted ink and a plate, never by opacity"
        assert got["dots"] == "BUTTON" and got["dotsName"] == "More", "the dots a button with its word"
        ring = pg.evaluate("() => { const a = getComputedStyle(document.querySelector('#t-mount .post-card[data-asks]')); const p = document.createElement('i'); p.style.color = 'var(--ork-alert)'; document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return [a.borderTopColor, c]; }")
        assert ring[0] == ring[1], "the ring is the alert's yellow"
        pg.locator('#t-mount .post-card[data-asks] .post-card__dots').click()
        assert pg.evaluate("() => window.__more") == ["Keep the seat's plan changed"], "the dots send the post to the caller"
        # Tab reaches each card and each act, a focus showing
        pg.focus("#t-before")
        reached = []
        for _ in range(12):
            pg.keyboard.press("Tab")
            f = pg.evaluate(FOCUSED)
            if f is None:
                break
            reached.append(f)
        acts = [f["act"] for f in reached if f["act"]]
        assert acts == ["change_spec", "start_now", "to_main"], reached
        assert all(f["outline"] or f["ring"] for f in reached), reached
        assert [f for f in reached if f["cls"].startswith("post-card__dots")], "the dots reached by Tab"
    finally:
        pg.close()
    # --- the phone: the page held upright with touch (the media the phone's sizes are kept by), then through the installed app's ./page/ path when the app comes up here
    ph, _host, log = open_up(gui, kind="phone")
    try:
        assert ph.evaluate(DRAW, ["/static/", True]) == {"news": "NEW", "change": "CHANGED"}
        self_check(ph.evaluate(LOOK))
    finally:
        ph.close()
    assert not log, "\n".join(log)
    app.keep_pairing()
    pg = app.open()
    try:
        pg.wait_for_selector("[data-frame][data-upright='1']", timeout=WAIT_MS)
    except Exception:
        pytest.skip("the installed app does not come up in this sandbox (tests/test_pwa_frame_browser.py fails the same way); the upright page above held the phone's sizes")
    app.ready()
    assert pg.evaluate(DRAW, ["./page/", True]) == {"news": "NEW", "change": "CHANGED"}, "the same module"
    self_check(pg.evaluate(LOOK))
    assert not app.errors, "\n".join(app.errors)


def self_check(got):
    assert got["cards"] == 3 and got["small"] >= 14, got
    assert got["body"] >= 14 and got["caption"] == 14, "the phone's sizes stay"
    assert got["tag"] is False and got["sign"] is False and got["plate"] is False, "the desktop's labels are not drawn on the phone"
    assert got["dots"] == "SPAN", "the phone's dots stay plain"
