"""**The table of cards fits at 1280 x 800 and 1440 x 900** (goal 170, stage G): on mocks the table, an L, the gate's spread and a leader's
table are opened at both sizes and checked: no text under 12 px, every text at 4.5:1 on its ground (the muted one too), no act's
button clipped (its box inside every container that clips it, once scrolled into view), and every act a button with its word, reached
by Tab with a visible focus. A lane too narrow for its acts wraps them; it never hides one."""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from tests import mock_kit, narrow  # noqa: E402
from tests.browser_kit import launch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import serve_mock  # noqa: E402

pytestmark = pytest.mark.browser
SIZES = [(1280, 800), (1440, 900)]
MAT_SIZES = SIZES + [(390, 844)]                      # the mats (goal 171, stage L) are also drawn on the phone: the whole screen

# What is read of the page: every element with a text of its own, its size and its colour against the ground it lies on.
TEXTS = """(root) => {
  const sel = document.querySelector(root) || document.body, cv = document.createElement("canvas").getContext("2d");
  const parse = (c) => { cv.clearRect(0, 0, 1, 1); cv.fillStyle = "#000"; cv.fillStyle = c; cv.fillRect(0, 0, 1, 1); const d = cv.getImageData(0, 0, 1, 1).data; return { r: d[0], g: d[1], b: d[2], a: d[3] / 255 }; };
  const over = (top, under) => ({ r: top.r * top.a + under.r * (1 - top.a), g: top.g * top.a + under.g * (1 - top.a), b: top.b * top.a + under.b * (1 - top.a), a: 1 });
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  // The ground a word lies on: its element's and its parents' layers from the word outwards, up to the first opaque plate or card (a background colour of alpha 1); what lies under that one is not seen.
  // An image (the felt's dither) counts only where it lies on or inside that opaque layer, so a mat's words on a plate are measured.
  const ground = (el) => { const layers = []; let image = false, opaque = false;
    for (let e = el; e && !opaque; e = e.parentElement) { const cs = getComputedStyle(e), bg = parse(cs.backgroundColor), er = e.getBoundingClientRect();
      const pc = getComputedStyle(e, "::before");      // orkUI draws a button's ground on its ::before
      if (pc.content !== "none" && pc.content !== "normal" && pc.position === "absolute" && parseFloat(pc.width) >= er.width - 6 && parseFloat(pc.height) >= er.height - 6) { const pb = parse(pc.backgroundColor); if (pb.a > 0) { layers.push(pb); if (pb.a >= 1) opaque = true; } if (pc.backgroundImage !== "none") image = true; }
      if (bg.a > 0) { layers.push(bg); if (bg.a >= 1) opaque = true; }
      if (cs.backgroundImage !== "none") image = true; }
    let c = { r: 9, g: 8, b: 7, a: 1 };
    for (const l of layers.reverse()) c = over(l, c);
    return { c, image }; };
  // The size a word is drawn at: its font size times the scale of every transform above it (a scaled mat's words are smaller than their font says).
  const drawn = (el) => { let k = 1; for (let e = el; e && e !== document.documentElement; e = e.parentElement) { const t = getComputedStyle(e).transform; if (t && t !== "none") { const m = new DOMMatrix(t); k *= Math.sqrt(m.a * m.a + m.b * m.b); } } return k; };
  const out = [], seen = new Set();
  const walker = document.createTreeWalker(sel, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const text = n.textContent.trim(), el = n.parentElement;
    if (!text || !el || seen.has(el)) continue;
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if (cs.visibility === "hidden" || cs.display === "none" || +cs.opacity === 0 || r.width < 1 || r.height < 1 || el.closest("[aria-hidden='true'], [hidden], script, style, .mock-plate")) continue;
    if (el.closest("kbd")) continue;
    // A word cut off by its field: the rect of its text lies partly outside the rect of the nearest ancestor that scrolls or clips, the ancestor scrolled to its start.
    // A word wholly outside (a list scrolled away) is not cut: it waits to be scrolled to. A word in a field that is itself out of view is skipped as before.
    let clipped = false, cut = "";
    const range = document.createRange(); range.selectNodeContents(n); const wr = range.getBoundingClientRect();
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) { const o = getComputedStyle(p);
      if (o.overflowX === "visible" && o.overflowY === "visible") continue;
      const pr = p.getBoundingClientRect(), l = wr.left + p.scrollLeft, t = wr.top + p.scrollTop, rt = l + wr.width, bt = t + wr.height;
      if (wr.bottom < pr.top || wr.top > pr.bottom || wr.right < pr.left || wr.left > pr.right) clipped = true;
      else if (!cut) { const scrolls = /auto|scroll/.test(o.overflowX + o.overflowY), edge = scrolls ? (l < pr.left - 1 || t < pr.top - 1) : (l < pr.left - 1 || t < pr.top - 1 || rt > pr.right + 1 || bt > pr.bottom + 1);
        // a scroller's far edge is reached by scrolling; a line clamp and an ellipsis are the page's own marks of a truncation, not a cut
        if (edge && !(el.closest("[style*='line-clamp'], .ellipsis") || /ellipsis/.test(cs.textOverflow) || cs.webkitLineClamp !== "none" && cs.webkitLineClamp !== "" || (p.style && /clamp/.test(p.style.cssText)))) cut = p.tagName.toLowerCase() + "." + String(p.className).slice(0, 30); } }
    if (clipped) continue;
    seen.add(el);
    const fg = parse(cs.color), g = ground(el), under = over(fg, g.c), a = lum(under), b = lum(g.c), ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    out.push({ text: text.slice(0, 40), cls: (el.className && el.className.baseVal === undefined ? el.className : "").toString().slice(0, 50), tag: el.tagName, cut, size: Math.round(parseFloat(cs.fontSize) * drawn(el) * 100) / 100, ratio: Math.round(ratio * 100) / 100, image: g.image });
  }
  return out;
}"""

# Every act (a button) in a surface: its word, whether its box is inside what clips it once it is scrolled into view.
ACTS = """(root) => {
  const sel = document.querySelector(root) || document.body, out = [];
  for (const b of sel.querySelectorAll("button, [role='button'], a[href]")) {
    const cs = getComputedStyle(b);
    if (cs.display === "none" || cs.visibility === "hidden" || b.closest("[aria-hidden='true'], [hidden], .mock-plate, [inert]") || b.disabled && false) continue;
    b.scrollIntoView({ block: "nearest", inline: "nearest" });
    const r = b.getBoundingClientRect(), bad = [];
    if (r.width < 1 || r.height < 1) bad.push("no box");
    const seen = (box) => { const w = Math.min(r.right, box.right) - Math.max(r.left, box.left), h = Math.min(r.bottom, box.bottom) - Math.max(r.top, box.top); return Math.max(0, w) * Math.max(0, h) / (r.width * r.height || 1); };   // the part of its box inside `box`: a card tilted a few degrees may overshoot by a corner
    if (seen({ left: 0, top: 0, right: innerWidth, bottom: innerHeight }) < 0.9) bad.push("outside the window");
    for (let p = b.parentElement; p && p !== document.documentElement; p = p.parentElement) {
      const o = getComputedStyle(p);
      if (o.overflow === "visible" && o.overflowX === "visible" && o.overflowY === "visible") continue;
      if (seen(p.getBoundingClientRect()) < 0.9) bad.push("clipped by " + p.tagName.toLowerCase() + "." + String(p.className).slice(0, 30));
    }
    const word = (b.innerText || "").trim() || b.getAttribute("aria-label") || "";
    out.push({ word: word.slice(0, 40), cls: String(b.className).slice(0, 40), bad });
  }
  return out;
}"""

# Tab from the first element of a surface: every act of it is reached, with a visible focus (an outline or a shadow).
KEY = """(a) => a.tagName + "|" + String(a.className).slice(0, 40) + "|" + (a.dataset.key || a.dataset.goal || "") + "|" + (a.innerText || a.getAttribute("aria-label") || "").trim().slice(0, 30)"""
# the acts of a surface, in the page's order (the tabs and the radios of a group not selected are reached by the arrow keys: ARIA's roving tabindex)
TAB = """(root) => { const key = %s, sel = document.querySelector(root) || document.body;
  return [...sel.querySelectorAll("button, [role='button'], a[href]")].filter((b) => { const cs = getComputedStyle(b); return cs.display !== "none" && cs.visibility !== "hidden" && !b.closest("[aria-hidden='true'], [hidden], .mock-plate, [inert]") && !b.disabled && !(b.tabIndex < 0 && /^(tab|radio)$/.test(b.getAttribute("role") || "")); }).map((b) => ({ key: key(b), tab: b.tabIndex >= 0 })); }""" % KEY
FOCUS = """(root) => { const key = %s, a = document.activeElement; if (!a || a === document.body || !a.closest(root)) return null; const cs = getComputedStyle(a), line = parseFloat(cs.outlineWidth) > 0 && cs.outlineStyle !== "none",
  shadow = cs.boxShadow !== "none" || getComputedStyle(a, "::before").boxShadow !== "none" || getComputedStyle(a, "::after").boxShadow !== "none";
  return { key: key(a), seen: line || shadow }; }""" % KEY


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_turned)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/?mock=1"
    s.shutdown()


def fresh(b, url, size):
    if size[0] <= 700:                                # a phone: its own page (/app/), upright with touch, the mat the whole screen
        pg = b.new_context(**narrow.NARROW).new_page()
        pg.goto(url.replace("/?mock=1", "/app/?mock=1"))
        pg.wait_for_selector(".up-card", timeout=20000)
        pg.wait_for_selector(".up-ct .cards-m", timeout=20000)
    else:
        pg = b.new_page(viewport={"width": size[0], "height": size[1]})
        pg.goto(url)
        pg.wait_for_selector(".cards-m", timeout=15000)
    pg.wait_for_timeout(800)
    return pg


def open_table(pg):
    pg.locator('.cards-lane[data-party="tech"] [data-value="architecture"]').click()
    pg.wait_for_selector('.tb[data-framework="architecture"]')


def open_l(pg):
    pg.locator(".cards-m:not([data-mat])").first.focus()        # a word, no mat: it opens as an L (decisions §297.1)
    pg.keyboard.press("Enter")
    pg.wait_for_selector(".cards-l")


def open_gate(pg):
    for i in range(pg.locator(".cards-s:visible").count()):
        card = pg.locator(".cards-s:visible").nth(i)
        if "to review" in (card.get_attribute("aria-label") or ""):
            card.scroll_into_view_if_needed()
            card.click()
            pg.locator(".cards-l__acts button", has_text="At the gate").click()
            pg.wait_for_selector(".sp-veil[data-spread='gate']")
            return
    raise AssertionError("no goal to review on the mock")


def open_mat(pg, goal="174-example-3"):
    """A mat open from the hand's card of a move that waits (a spec all written: its seal lies at the foot): the mat and, under it, the hand's ways. On the phone the card lifts
    in the feed's foot and *Open it* opens the mat, its ways at the foot of its own screen."""
    if pg.viewport_size["width"] <= 700:
        pg.locator(f".up-card[data-key='card:turn/{goal}/spec']").click()
        pg.locator(".up-look .hand-lifted[data-kind=turn]").get_by_role("button", name="Open it").click()
        pg.wait_for_selector("[data-spread=track] .mf-foot")
        return
    pg.locator(f".frame-hand button.hand-card[data-kind=turn][data-goal='{goal}']").click()
    pg.wait_for_selector("[data-spread=track] .mf")
    pg.wait_for_selector(".frame-hand .mathand")


def closed_mat(pg):
    pg.wait_for_selector(".cards-m[data-mat]:visible")
    pg.locator(".cards-m[data-mat]:visible").first.scroll_into_view_if_needed()


SURFACES = {"the table": (lambda pg: None, ".frame"), "an L": (open_l, ".cards-l"),
            "the gate spread": (open_gate, ".sp-veil"), "a leader's table": (open_table, ".sp-veil"),
            "an open mat": (open_mat, "[data-spread=track]"), "a closed mat": (closed_mat, ".cards-m[data-mat]"),
            "the hand with a mat open": (open_mat, ".frame-hand")}
PHONE_ROOT = {"a closed mat": ".up-ct .cards-m[data-mat]", "the hand with a mat open": "[data-spread=track] .mf-foot"}      # a phone's hand is the foot of the mat's screen
ON_PHONE = {"an open mat", "a closed mat", "the hand with a mat open", "the gate spread"}
CASES = [(n, z) for n in SURFACES for z in MAT_SIZES if z in SIZES or n in ON_PHONE]


def check_texts(pg, root, what):
    bad = []
    for t in pg.evaluate(f"({TEXTS})({root!r})"):
        if t["size"] < 12:
            bad.append(f"{t['size']}px: {t['tag']}.{t['cls']} “{t['text']}”")
        if t["cut"]:
            bad.append(f"cut off by {t['cut']}: {t['tag']}.{t['cls']} “{t['text']}”")
        if t["ratio"] < 4.5 and not t["image"]:
            bad.append(f"{t['ratio']}:1: {t['tag']}.{t['cls']} “{t['text']}”")
    assert not bad, f"{what}:\n" + "\n".join(bad)


def check_acts(pg, root, what):
    acts = pg.evaluate(f"({ACTS})({root!r})")
    bad = [f"{a['word'] or '(no word)'} [{a['cls']}]: {', '.join(a['bad'])}" for a in acts if a["bad"]]
    bad += [f"{a['cls']}: a button with no word" for a in acts if not a["word"]]
    assert not bad, f"{what}:\n" + "\n".join(bad)


def check_tab(pg, root, what):
    """Tab through the surface: every act in it is a button reached with a visible focus."""
    acts = pg.evaluate(f"({TAB})({root!r})")
    keys = [a["key"] for a in acts]
    assert keys, f"{what}: no act"
    assert all(a["tab"] for a in acts), f"{what}: not reached by Tab: " + ", ".join(a["key"] for a in acts if not a["tab"])
    pg.evaluate(f"() => {{ const el = document.querySelector({root!r}); const f = [...el.querySelectorAll('button, [role=button], a[href]')].find((b) => getComputedStyle(b).display !== 'none' && !b.closest('[aria-hidden=true], [inert]')); f.focus(); }}")
    pg.keyboard.press("Tab")
    pg.keyboard.press("Shift+Tab")                    # back on the first act, now by the keyboard
    reached, unseen = set(), set()
    for _ in range(len(keys) * 2 + 20):               # the cards that are no button (a post on its side) are stops too
        info = pg.evaluate(f"({FOCUS})({root!r})")
        if info:
            reached.add(info["key"])
            if not info["seen"]:
                unseen.add(info["key"])
        if all(k in reached for k in keys):
            break
        pg.keyboard.press("Tab")
    missing = [k for k in keys if k not in reached]
    assert not missing, f"{what}: Tab did not reach " + ", ".join(missing)
    assert not unseen, f"{what}: no visible focus on " + ", ".join(sorted(unseen))


@pytest.mark.parametrize("name,size", CASES, ids=lambda c: c if isinstance(c, str) else f"{c[0]}x{c[1]}")
def test_a_surface_fits(page_url, name, size):
    opener, root = SURFACES[name]
    root = PHONE_ROOT.get(name, root) if size[0] <= 700 else root
    with sync_playwright() as p:
        b = launch(p)
        pg = fresh(b, page_url, size)
        opener(pg)
        pg.wait_for_timeout(500)                      # an L turns as it opens
        what = f"{name} at {size[0]}x{size[1]}"
        check_texts(pg, root, what)
        check_acts(pg, root, what)
        b.close()


@pytest.mark.parametrize("name,size", CASES, ids=lambda c: c if isinstance(c, str) else f"{c[0]}x{c[1]}")
def test_every_act_is_a_button_reached_by_tab_with_a_visible_focus(page_url, name, size):
    opener, root = SURFACES[name]
    root = PHONE_ROOT.get(name, root) if size[0] <= 700 else root
    with sync_playwright() as p:
        b = launch(p)
        pg = fresh(b, page_url, size)
        opener(pg)
        pg.wait_for_timeout(500)
        if name == "a closed mat":                    # a closed mat is a card (an article), not a button: it takes the focus and shows it
            pg.locator(root).first.focus()
            seen = pg.evaluate("(r) => { const a = document.activeElement, cs = getComputedStyle(a); return a.matches(r) && a.tabIndex >= 0 && ((parseFloat(cs.outlineWidth) > 0 && cs.outlineStyle !== 'none') || cs.boxShadow !== 'none'); }", root)
            assert seen, f"{name} at {size[0]}x{size[1]}: not reached by Tab or no visible focus"
            b.close()
            return
        check_tab(pg, root, f"{name} at {size[0]}x{size[1]}")
        b.close()


def test_the_focus_goes_back_to_the_card_that_opened_an_l_or_a_spread_and_tab_stays_in_it(page_url):
    """Esc and Close of an L and of a spread give the focus back to the card that opened it; when that card was drawn again meanwhile it
    goes to the card in its place, never to the body; Tab never leaves an L."""
    with sync_playwright() as p:
        b = launch(p)
        pg = fresh(b, page_url, SIZES[1])
        on = "() => document.activeElement.matches('.cards-m, .cards-s, .frame-hand .hand-card')"
        m = pg.locator(".cards-m:not([data-mat])").first
        m.focus()
        pg.keyboard.press("Enter")
        pg.wait_for_selector(".cards-l")
        pg.wait_for_function("() => !!document.activeElement.closest('.cards-l')")      # the L takes the focus as it opens
        for _ in range(9):
            pg.keyboard.press("Tab")
            assert pg.evaluate("() => !!document.activeElement.closest('.cards-l')"), "Tab left the L"
        label = m.get_attribute("aria-label")
        pg.locator(".cards-l__shut").click()
        pg.wait_for_function(on)
        assert pg.evaluate(on) and pg.evaluate("() => document.activeElement.getAttribute('aria-label')") == label
        # the card is drawn again while the L lies over it: the focus goes to the one in its place
        m.focus()
        pg.keyboard.press("Enter")
        pg.wait_for_selector(".cards-l")
        pg.evaluate("(label) => { const el = [...document.querySelectorAll('.cards-m')].find((e) => e.getAttribute('aria-label') === label); el.replaceWith(el.cloneNode(true)); }", label)
        pg.keyboard.press("Escape")
        pg.wait_for_function(on)
        assert pg.evaluate(on) and pg.evaluate("() => document.activeElement.getAttribute('aria-label')") == label
        # a spread from the deck, closed by Esc and by Close
        for how in ("Escape", "Close"):
            btn = pg.locator("[data-spread-act='cost']")
            btn.click()
            pg.wait_for_selector(".sp-veil")
            pg.keyboard.press("Escape") if how == "Escape" else pg.locator(".sp-shut").click()
            pg.wait_for_timeout(200)
            assert pg.evaluate("() => document.activeElement.matches('[data-spread-act=cost]')")
        b.close()


def test_the_gate_mat_on_the_phone_is_laid_unscaled_and_no_check_is_cut_at_the_screens_edge(page_url):
    """Goal 171 stage N2: no ancestor of the gate's field scales it down, its words are 12 px at least as drawn, every check lies inside the screen's width."""
    with sync_playwright() as p:
        b = launch(p)
        pg = fresh(b, page_url, (390, 844))
        open_gate(pg)
        pg.wait_for_timeout(500)
        pg.locator(".gt-line").wait_for()
        got = pg.evaluate("""() => { const scales = [], gate = document.querySelector('.gt');
          for (let e = gate; e && e !== document.documentElement; e = e.parentElement) { const t = getComputedStyle(e).transform; if (t !== 'none') { const m = new DOMMatrix(t); scales.push(Math.hypot(m.a, m.b)); } }
          const checks = [...document.querySelectorAll('.gt .sp-card, .gt .mf-zone')].map((e) => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right)]; });
          const words = [...gate.querySelectorAll('.sp-card__name, .sp-card__line')].map((e) => parseFloat(getComputedStyle(e).fontSize) * (e.getBoundingClientRect().width / (e.offsetWidth || 1)));
          return { scales, checks, words }; }""")
        assert all(k >= 1 for k in got["scales"]), got["scales"]
        assert got["checks"] and all(left >= 0 and right <= 390 for left, right in got["checks"]), got["checks"]
        assert got["words"] and all(w >= 11.9 for w in got["words"]), got["words"]
        b.close()
