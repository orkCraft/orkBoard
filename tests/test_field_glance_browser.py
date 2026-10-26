"""Spec 82 B (docs/specs/82-the-field-at-a-glance.md §3–§7): what the field says at a glance, in a real browser at 1 440 × 900 against the arena's stub host (each task with the row
the town gives it): a card at work wears orkUI's busy mark top left, a held card says its reason and a waiting one does not, a member is a face over its column with a 2 px rule as wide
as the column, the arrows go in square steps, and a new stop rises out of the fan and goes back (nothing on the first draw; none that moves under reduced motion)."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import pip  # noqa: E402
from tests.test_field_rows_browser import RowsHost, alone  # noqa: E402
from tests.test_shell_browser import _open, box  # noqa: E402

pytestmark = pytest.mark.browser


@pytest.fixture
def field(gui):
    pg, host, errors = _open(gui, host=RowsHost(), ready=".arena-phead")
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    pg.locator(".arena-task[data-key='register/k3']").wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def token(pg, name, prop="color"):
    """What an orkUI token computes to, as the page paints it."""
    return pg.evaluate("([n, p]) => { const e = document.createElement('i'); e.style[p] = `var(${n})`; document.body.appendChild(e); const c = getComputedStyle(e)[p]; e.remove(); return c; }", [name, prop])


def card(pg, key):
    return pg.locator(f".arena-task[data-key='{key}']")


# -- a card at work (§4) ------------------------------------------------------------------------------------------------------------------

def test_a_card_at_work_wears_the_busy_mark_top_left_and_no_other_card_does(field):
    pg, host = field
    running = card(pg, "register/k3")
    busy = running.locator(".ork-busy")
    assert busy.count() == 1 and running.locator(".ork-sign.work").count() == 0                          # orkUI's busy mark, no state sign
    assert "working 4 min" in running.locator(".arena-task__foot").inner_text()
    mark, elem, whole = busy.bounding_box(), running.locator(".ork-elem").bounding_box(), running.bounding_box()
    assert (mark["width"], mark["height"]) == (12, 12) and mark["x"] < elem["x"] and mark["y"] - whole["y"] < 12 and mark["x"] - whole["x"] < 12        # top left, before the goal's element
    assert busy.evaluate("e => getComputedStyle(e).animationName") == "ork-busy-turn" and busy.evaluate("e => getComputedStyle(e, '::after').animationName") == "ork-busy-sand"      # the hourglass runs (orkUI 0.11.0)
    assert pg.locator(".arena-task:not([data-state=running]):not([data-state=testing]) .ork-busy").count() == 0      # a card that waits, is held, failed or lies at Review does not
    host.node_of("register")["tasks"][2]["state"] = "testing"
    host.bump({})
    pg.wait_for_function("() => document.querySelector(\"[data-key='register/k3'] .arena-task__foot\")?.textContent.trim() === 'testing'", timeout=WAIT_MS)
    assert card(pg, "register/k3").locator(".ork-busy").count() == 1 and card(pg, "register/k3").get_attribute("data-state") == "testing"
    assert card(pg, "register/k3").evaluate("e => getComputedStyle(e).borderTopColor") == token(pg, "--ork-edge", "borderTopColor")        # the ink edge, as today


def test_the_busy_mark_stands_still_under_reduced_motion(gui):
    server, browser = gui
    host = RowsHost()
    pg = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".arena-task[data-key='register/k3'] .ork-busy").wait_for(timeout=WAIT_MS)
    assert pg.locator(".ork-busy").first.evaluate("e => getComputedStyle(e, '::after').animationName") == "none"
    pg.close()


# -- held and waiting (§3) ----------------------------------------------------------------------------------------------------------------

def test_a_held_card_says_its_reason_with_its_sign_and_a_waiting_card_is_not_dashed(field):
    pg, host = field
    held, waiting = card(pg, "cookie/f2"), card(pg, "register/k5")
    assert "is-held" in held.get_attribute("class") and "is-wait" not in held.get_attribute("class")
    assert held.evaluate("e => getComputedStyle(e).borderTopStyle") == "dashed"                          # the dashed edge
    assert " ".join(held.locator(".arena-task__foot").inner_text().split()) == "held: tonight" and held.locator(".arena-task__foot .ork-sign.night").count() == 1
    assert "tonight · after 01:00" in held.get_attribute("title")                                        # the time is in its tooltip
    assert "is-wait" in waiting.get_attribute("class") and "is-held" not in waiting.get_attribute("class")
    assert waiting.evaluate("e => getComputedStyle(e).borderTopStyle") == "solid"                        # a waiting card lies lower and is not drawn as a held one
    assert waiting.locator(".arena-task__foot .ork-sign.before").count() == 1 and waiting.locator(".arena-task__foot .ork-sign.night, .arena-task__foot .ork-sign.pause").count() == 0
    reasons = [({"kind": "limits", "ref": "", "title": "", "until": "2099-01-01T14:20"}, "after 14:20", {}, "held: window", "pause"),
               ({"kind": "night", "ref": "", "title": "", "until": ""}, "", {}, "held: tonight", "night"),
               ({"kind": "sign_in", "ref": "codex", "title": "Codex", "tool": "Codex", "until": ""}, "", {"held_for": "sign_in"}, "held: sign in", "alert"),
               ({"kind": "week", "ref": "", "title": "", "until": "2099-01-05T09:00"}, "week · after 09:00", {}, "held: week", "pause")]
    for waits, note, more, words, sign in reasons:
        alone(host, [pip("k1", "Challenge store", "held") | {"note": note, **more}], waits=waits)
        pg.wait_for_function("(w) => document.querySelector(\"[data-key='register/k1'] .arena-task__foot\")?.textContent.trim() === w", arg=words, timeout=WAIT_MS)
        foot = card(pg, "register/k1").locator(".arena-task__foot")
        assert foot.locator(f".ork-sign.{sign}").count() == 1, words
        assert card(pg, "register/k1").evaluate("e => getComputedStyle(e).borderTopStyle") == "dashed", words
        assert foot.bounding_box()["x"] + foot.bounding_box()["width"] <= card(pg, "register/k1").bounding_box()["x"] + card(pg, "register/k1").bounding_box()["width"], words   # never cut: it wraps


# -- a member is a face (§5) --------------------------------------------------------------------------------------------------------------

def test_a_member_is_a_face_over_its_column_with_a_rule_as_wide_as_the_column(field):
    pg, host = field
    for agent in ("backend", "screens", "reviewer", "words"):
        member, column = pg.locator(f".arena-member[data-agent={agent}]"), box(pg, f".arena-stack[data-agent={agent}]")
        whole, rule = member.bounding_box(), member.locator(".arena-member__rule").bounding_box()
        assert abs(rule["width"] - column["width"]) <= 1 and abs(rule["x"] - column["x"]) <= 1 and rule["height"] == 2, agent      # the full width of the column, 2 px
        assert abs(whole["width"] - column["width"]) <= 1, agent                                                                         # no 200 px cap
        port, line = member.locator(".arena-tport").bounding_box(), member.locator(".arena-member__line").bounding_box()
        assert (port["width"], port["height"]) == (40, 40) and abs(port["x"] + 20 - (column["x"] + column["width"] / 2)) <= 1, agent        # the head, 40 px, centred
        assert abs(line["x"] + line["width"] / 2 - (column["x"] + column["width"] / 2)) <= 1 and port["y"] + 40 <= line["y"] + 1, agent       # the name and its marks centred under it
        assert rule["y"] >= line["y"] + line["height"] - 1, agent                                                                        # the rule under them
        assert member.evaluate("e => getComputedStyle(e).borderTopWidth") == "0px" and member.evaluate("e => getComputedStyle(e).backgroundColor") == "rgba(0, 0, 0, 0)", agent       # no frame
        assert member.evaluate("e => getComputedStyle(e).clipPath") == "none", agent
    assert [m.locator("img.ork-mark").count() for m in pg.locator(".arena-member").all()] == [2, 2, 2, 2]
    name = pg.locator(".arena-member[data-agent=backend] .arena-member__nm").bounding_box()
    mark = pg.locator(".arena-member[data-agent=backend] img.arena-mark--r").bounding_box()
    assert mark["x"] > name["x"] + name["width"] - 1 and abs((mark["y"] + mark["height"] / 2) - (name["y"] + name["height"] / 2)) <= 2       # the marks beside the name


def test_the_rule_is_the_edge_the_ink_while_it_works_and_the_danger_colour_while_it_calls(field):
    pg, host = field
    rule = lambda agent: pg.locator(f".arena-member[data-agent={agent}] .arena-member__rule").evaluate("e => getComputedStyle(e).backgroundColor")      # noqa: E731
    assert rule("words") == token(pg, "--ork-edge", "backgroundColor")                                   # next: the edge
    assert rule("screens") == token(pg, "--ork-ink", "backgroundColor")                                  # at work: ink
    assert rule("backend") == token(pg, "--ork-danger", "backgroundColor")                               # it calls (a failure): danger
    assert pg.locator(".arena-member[data-agent=screens] .arena-tport .ork-busy").count() == 1 and pg.locator(".arena-member[data-agent=screens] .arena-tport .ork-busy").bounding_box()["width"] == 12     # the head turns
    assert pg.locator(".arena-member[data-agent=words] .ork-busy, .arena-member[data-agent=backend] .ork-busy").count() == 0
    host.party["passkey"][4]["state"] = "work"                                                           # Words starts working: its rule turns ink and its head turns
    host.bump({})
    pg.wait_for_function("() => document.querySelector('.arena-member[data-agent=words] .ork-busy')", timeout=WAIT_MS)
    assert rule("words") == token(pg, "--ork-ink", "backgroundColor")
    host.party["passkey"][4]["state"] = "needs"
    host.party["passkey"][4]["why"] = "pick"
    host.bump({})
    pg.wait_for_function("() => !document.querySelector('.arena-member[data-agent=words] .ork-busy')", timeout=WAIT_MS)
    assert rule("words") == token(pg, "--ork-danger", "backgroundColor")
    pg.locator(".arena-member[data-agent=screens]").hover()                                              # the peek stays
    assert pg.locator(".arena-mcol[data-agent=screens] .arena-peek").is_visible()


# -- the arrows in steps (§6) -------------------------------------------------------------------------------------------------------------

def test_an_arrow_between_cards_in_different_rows_goes_in_square_steps_and_none_joins_cards_of_one_row(field):
    pg, host = field
    chain = [pip("a", "First", "running", wave=1), pip("b", "Second", "waiting", ["a"], 2, "screens"), pip("c", "Third", "waiting", ["b"], 3), pip("d", "Fourth", "waiting", ["c"], 4, "screens")]
    alone(host, chain)
    pg.locator(".arena-task[data-task=d]").wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => !document.querySelector('.is-drawn, .is-leaving') && document.getAnimations().every((a) => String(a.animationName || '').startsWith('ork-busy'))", timeout=WAIT_MS)      # the cards are in their places
    card(pg, "register/b").hover()                                                                       # b: waits for a (row Now), c waits for b (row Later)
    pg.wait_for_function("() => document.querySelectorAll('.arena-arrow').length === 2", timeout=WAIT_MS)
    base = pg.locator(".arena-arrows").bounding_box()
    for edge, (frm, to) in {"a>b": ("a", "b"), "b>c": ("b", "c")}.items():
        group = pg.locator(f".arena-arrow[data-edge='{edge}']")
        pts = [tuple(float(v) for v in p.split(",")) for p in group.locator("polyline").get_attribute("points").split()]
        a, b = card(pg, f"register/{frm}").bounding_box(), card(pg, f"register/{to}").bounding_box()
        assert len(pts) == 4 and all(p[0] == q[0] or p[1] == q[1] for p, q in zip(pts, pts[1:])), edge             # square corners: every step horizontal or vertical
        assert abs(pts[0][0] + base["x"] - (a["x"] + a["width"] / 2)) <= 1 and abs(pts[0][1] + base["y"] - (a["y"] + a["height"])) <= 1, edge        # down from the bottom centre
        assert pts[0][0] == pts[1][0] and pts[1][1] == pts[2][1] and pts[2][0] == pts[3][0], edge               # down, across, down
        assert a["y"] + a["height"] < pts[1][1] + base["y"] < b["y"], edge                                      # across between the rows
        tip = [tuple(float(v) for v in p.split(",")) for p in group.locator("polygon").get_attribute("points").split()][0]
        assert abs(tip[0] + base["x"] - (b["x"] + b["width"] / 2)) <= 1 and abs(tip[1] + base["y"] - b["y"]) <= 1, edge                              # into the top centre of the waiting card
        assert group.locator("polyline").evaluate("e => getComputedStyle(e).strokeWidth") == "2px" and group.locator("line").count() == 0
    pg.mouse.move(5, 5)
    pg.wait_for_function("() => !document.querySelector('.arena-arrow')", timeout=WAIT_MS)
    card(pg, "register/c").hover()                                                                       # c waits for b (a step down) and d waits for c: both in Later, one row, no arrow
    pg.wait_for_function("() => document.querySelectorAll('.arena-arrow').length === 1", timeout=WAIT_MS)
    assert pg.locator(".arena-arrow").get_attribute("data-edge") == "b>c"
    pg.mouse.move(5, 5)
    card(pg, "register/d").hover()                                                                       # d waits only for c, in its own row: nothing to draw
    pg.wait_for_timeout(300)
    assert pg.locator(".arena-arrow").count() == 0


# -- a new stop rises (§7) ----------------------------------------------------------------------------------------------------------------

def todo(n):
    return {"kind": "todo", "idea": "recovery", "goal": "passkey", "title": "Recovery codes", "text": f"SECRET_{n}", "priority": "high", "blocks": False, "at": "x",
            "todo": {"id": f"t{n}", "title": f"SECRET_{n}", "kind": "secret", "why": "to send the codes", "choices": [], "steps": [], "accept": [], "done": False}}


WATCH = """() => { window.__rise = {}; const seen = (el, t, on) => { const k = el.dataset.key; (window.__rise[k] = window.__rise[k] || {})[on ? 'up' : 'down'] = t; };
  new MutationObserver((ms) => { for (const m of ms) { const el = m.target, was = (m.oldValue || '').split(' '), is = el.className.split(' '), t = performance.now();
    if (!was.includes('is-up') && is.includes('is-up')) seen(el, t, true); if (was.includes('is-up') && !is.includes('is-up')) seen(el, t, false);
    if (!was.includes('is-called') && is.includes('is-called')) seen(el, t, true); if (was.includes('is-called') && !is.includes('is-called')) seen(el, t, false); } })
    .observe(document.querySelector('.arena-hand'), { subtree: true, attributes: true, attributeFilter: ['class'], attributeOldValue: true }); }"""


def test_a_new_stop_rises_out_of_the_fan_stays_and_goes_back_several_in_turn_and_none_on_the_first_draw(gui):
    server, browser = gui
    host = RowsHost()
    pg = browser.new_page(viewport={"width": 1440, "height": 900})
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    pg.locator(".arena-hc").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(1200)
    assert pg.locator(".arena-hc.is-up, .arena-hc.is-down, .arena-hc.is-called").count() == 0            # the first draw after the page opens raises nothing
    before = pg.locator(".arena-hc").count()
    pg.evaluate(WATCH)
    host.extra_needs = [todo(1), todo(2)]                                                                # two stops come at once
    host.bump({})
    one = pg.locator(".arena-hc[data-key='todo/recovery/t1']")
    two = pg.locator(".arena-hc[data-key='todo/recovery/t2']")
    pg.wait_for_function("() => document.querySelector(\".arena-hc[data-key='todo/recovery/t1']\")?.classList.contains('is-up')", timeout=WAIT_MS)
    assert pg.locator(".arena-hc").count() == before + 2
    assert pg.locator(".arena-hc.is-up").count() == 1 and not two.evaluate("e => e.classList.contains('is-up')")        # in turn: the second is not up yet
    assert one.evaluate("e => getComputedStyle(e).transitionDuration") == "0.2s"                         # 0.2 s up
    pg.wait_for_function("() => getComputedStyle(document.querySelector(\".arena-hc[data-key='todo/recovery/t1']\")).transform === 'matrix(1, 0, 0, 1, 0, -184)'", timeout=WAIT_MS)      # upright and whole, its foot on the hand's top line
    raised, rest = one.bounding_box(), pg.locator(".arena-hc").first.bounding_box()
    assert raised["y"] < rest["y"] - 100
    pg.wait_for_function("() => document.querySelector(\".arena-hc[data-key='todo/recovery/t2']\")?.classList.contains('is-up')", timeout=WAIT_MS)
    assert one.evaluate("e => e.classList.contains('is-up')")                                            # the first is still up when the second rises
    pg.wait_for_function("() => !document.querySelector('.arena-hc.is-up, .arena-hc.is-down')", timeout=12_000)
    seen = pg.evaluate("window.__rise")
    t1, t2 = seen["todo/recovery/t1"], seen["todo/recovery/t2"]
    assert 450 <= t2["up"] - t1["up"] <= 900                                                             # 0.6 s apart
    assert 2400 <= t1["down"] - t1["up"] <= 3100 and 2400 <= t2["down"] - t2["up"] <= 3100               # 2.5 s up, then back
    pg.wait_for_function("() => getComputedStyle(document.querySelector(\".arena-hc[data-key='todo/recovery/t1']\")).transform !== 'matrix(1, 0, 0, 1, 0, -184)'", timeout=WAIT_MS)       # back in the fan
    assert pg.locator(".arena-hc").count() == before + 2
    host.extra_needs = [todo(2)]                                                                         # one leaves…
    host.bump({})
    pg.wait_for_function("() => !document.querySelector(\".arena-hc[data-key='todo/recovery/t1']\")", timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    assert pg.locator(".arena-hc.is-up").count() == 0                                                    # … and none that was there rises
    pg.close()


def test_a_stop_that_is_hovered_stays_up_longer(gui):
    server, browser = gui
    host = RowsHost()
    pg = browser.new_page(viewport={"width": 1440, "height": 900})
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".arena-hc").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(800)
    host.extra_needs = [todo(1)]
    host.bump({})
    one = pg.locator(".arena-hc[data-key='todo/recovery/t1']")
    pg.wait_for_function("() => document.querySelector(\".arena-hc[data-key='todo/recovery/t1']\")?.classList.contains('is-up')", timeout=WAIT_MS)
    one.locator(".arena-hc__open").hover()
    pg.wait_for_timeout(3600)                                                                            # past its 2.5 s: the pointer is on it
    assert one.evaluate("e => e.classList.contains('is-up')")
    pg.mouse.move(5, 5)
    pg.wait_for_function("() => !document.querySelector('.arena-hc.is-up')", timeout=WAIT_MS)
    pg.close()


def test_under_reduced_motion_a_new_stop_does_not_move_its_edge_is_the_alert_colour_for_2_5_s(gui):
    server, browser = gui
    host = RowsHost()
    pg = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".arena-hc").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(800)
    assert pg.locator(".arena-hc.is-called").count() == 0                                                # none on the first draw
    pg.evaluate(WATCH)
    host.extra_needs = [todo(1), todo(2)]
    host.bump({})
    pg.wait_for_function("() => document.querySelectorAll('.arena-hc.is-called').length === 2", timeout=WAIT_MS)
    one = pg.locator(".arena-hc[data-key='todo/recovery/t1']")
    assert one.evaluate("e => getComputedStyle(e).borderTopColor") == token(pg, "--ork-alert", "borderTopColor")
    assert token(pg, "--ork-alert", "borderTopColor") in one.evaluate("e => getComputedStyle(e).boxShadow")           # the edge, thicker (a stop is the alert colour already)
    assert one.evaluate("e => getComputedStyle(e).transform") != "matrix(1, 0, 0, 1, 0, -184)" and one.evaluate("e => getComputedStyle(e).transitionDuration") in ("0s", "0s, 0s")      # no move
    assert pg.locator(".arena-hc.is-up").count() == 0
    pg.wait_for_function("() => !document.querySelector('.arena-hc.is-called')", timeout=8000)
    seen = pg.evaluate("window.__rise")["todo/recovery/t1"]
    assert 2400 <= seen["down"] - seen["up"] <= 3100
    assert one.evaluate("e => getComputedStyle(e).boxShadow") == "none"                                   # and it is as it was
    pg.close()
