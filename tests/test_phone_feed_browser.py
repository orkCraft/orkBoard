"""The project's feed on the phone (goal 169 F, decisions §291.5–§291.9; the mockup docs/mockups/phone/feed.html v3, screens 1, 2, 3 and 6), in a real browser against a stub host that feeds `ideas.feed`, with touch at 390 × 844: with no goal picked the phone's
middle is the feed (hand/upfeed.js), asked with this phone's own last look (js/linkpaired.js `looked`), drawn in the reader's order: the heads row on top, what waits first, then the news newest first, one leader's posts in a row one block, the goals at work as
sideways cards with a button each way, the one seen line that spreads; the hand's row at the foot unchanged, no card raised, no tab. A head pressed narrows the feed to it and says so; pressed again the whole feed. A goal's screen (goal 169 G, screen 4) is the
same reader cut to the goal's route (`ideas.feed` with `route`): its heads the route's leaders, its blocks in the reader's order, the goal's question still in the hand, raised. Pictures for Design to $FEED_SHOTS when it is set (at 390 × 844, three device
pixels a pixel)."""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests import narrow  # noqa: E402
from tests.test_hand_context_narrow_browser import box, cards, css_colour, open_up, pots  # noqa: E402
from tests.test_hand_desktop_browser import node, sig, task  # noqa: E402
from tests.test_phone_look_browser import CONCERN, READABLE, SEAT, LookHost, pick_from_menu  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["FEED_SHOTS"]) if os.environ.get("FEED_SHOTS") else None
PROJECT = "/p/party-game"
LEADERBOARD = "Leaderboard is ready to start"
LOBBY = "Lobby takes the game's colours"


def iso(t: dt.datetime) -> str:
    return t.astimezone().isoformat(timespec="seconds")


def post(leader, at, text, kind="news", goal=""):
    return {"leader": leader, "at": iso(at), "kind": kind, "goal": goal, "text": text, "event": "idea.added", "acts": []}


class FeedHost(LookHost):
    """LookHost's project (Tech's *Keep the seat…* at work, Tech's concerns), two goals ready for main, a plan of Tech's that starts by itself, Design's lobby at work too, and the reader's answer as realm/board_feed.py gives it: the heads (the Orkmaster, Tech with news
    and asking, Design with news, Product and Release with none), what waits (the plan's clock, Lobby waiting for main), the posts since the look (Tech's three in a row, then Design's concern, then the Orkmaster's) and what came before it."""

    def __init__(self, scenario="ready"):
        super().__init__(scenario)
        self.nodes += [node("leader", "tech", LEADERBOARD, "table", state="plan", element="void", type={"sign": "tune", "name": "Tune"}),
                       node("lobby", "design", LOBBY, "table", state="working", element="ice", stage="implementation", type={"sign": "screen", "name": "Screen"}, tasks=[task("l1", "Paint the lobby", "running")])]
        self.now = dt.datetime.now().astimezone().replace(microsecond=0)

    def feed(self, a):
        if a.get("route"):
            return {**self.goal_feed(a), "since": iso(dt.datetime.fromtimestamp(a["since"] / 1000)) if a.get("since") else ""}
        now, since_ms = self.now, a.get("since")
        since = dt.datetime.fromtimestamp(since_ms / 1000).astimezone() if since_ms else None
        mins = lambda m: now - dt.timedelta(minutes=m)              # noqa: E731
        starts = (now + dt.timedelta(minutes=53)).replace(second=0)
        tech = [post("tech", mins(5), "Keep the seat: Keep the seat is in dev", goal="seat"), post("tech", mins(9), "Accepted step 1 of Keep the seat", goal="seat"), post("tech", mins(14), "Keep the seat's plan changed", "change", goal="seat")]
        posts = [{"leader": "tech", "post": tech[0], "more": tech[1:]},
                 {"leader": "design", "post": post("design", mins(30), "Doubts Round timer shows on every phone", "concern", goal="phones"), "more": []},
                 {"leader": "orkmaster", "post": post("orkmaster", mins(42), "Chat in the lobby was added", goal="chat"), "more": []}]
        seen = None
        if since is not None:
            old = [post("product", since - dt.timedelta(hours=2), "Pick the theme of the first week was added"), post("design", since - dt.timedelta(hours=3), "Accepted step 2 of Daily quests", goal="daily")]
            seen = {"since": iso(since), "leaders": ["product", "design"], "posts": old}
        return {"since": iso(since) if since else "",
                "heads": [{"leader": "orkmaster", "news": True, "asks": False}, {"leader": "tech", "news": True, "asks": True}, {"leader": "design", "news": True, "asks": False},
                          {"leader": "product", "news": False, "asks": False}, {"leader": "release", "news": False, "asks": False}],
                "waits": [{"kind": "starts", "goal": "leader", "short": LEADERBOARD, "title": LEADERBOARD, "party": "tech", "leader": "orkmaster", "at": iso(starts),
                           "acts": [{"act": "change_spec", "command": "ideas.spec_change", "args": {"idea": "leader"}}, {"act": "start_now", "command": "ideas.start_now", "args": {"slug": "leader"}}]},
                          {"kind": "main", "goal": "music", "short": "Lobby", "title": "Lobby music loop", "party": "tech", "leader": "release", "at": "", "main_ready": True, "main_reason": "",
                           "acts": [{"act": "to_main", "command": "ideas.to_main", "args": {"idea": "music"}}]}],
                "posts": posts, "seen": seen}

    def handle(self, name, a):
        if name == "ideas.feed":
            self.log.append((name, a))
            return self.feed(a)
        if name in ("ideas.start_now", "ideas.spec_change"):
            self.log.append((name, a))
            return {"ok": True}
        return super().handle(name, a)


LOOKED = """(ms) => { localStorage.setItem('orkcraft.looked', JSON.stringify({ '%s': ms })); }""" % PROJECT


def at_look(minutes_ago=60):
    return int((dt.datetime.now() - dt.timedelta(minutes=minutes_ago)).timestamp() * 1000)


def open_feed(gui, since=None, host=None, scenario="ready"):
    """The phone against a FeedHost, this phone's last look at the project `since` (ms) when given."""
    init = f"localStorage.setItem('orkcraft.looked', JSON.stringify({{ '{PROJECT}': {since} }}));" if since else None
    pg, host, log = open_up(gui, host=host or FeedHost(scenario), init=init)
    pg.locator(".up-feed .post-card").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def feed(pg):
    return pg.locator(".hand-up .up-feed")


def heads(pg):
    return pg.locator(".up-fh .up-fh__head")


def head_of(pg, leader):
    return pg.locator(f'.up-fh .up-fh__head[data-leader="{leader}"]')


def blocks(pg):
    """The feed's blocks in the page's order: `[(kind, its leader or goal)]`."""
    return pg.eval_on_selector_all(".up-feed > .post-card, .up-feed > .up-fd__lab, .up-feed > .up-fd__seen",
                                   "(els) => els.map((e) => e.classList.contains('up-fd__lab') ? ['label', e.textContent.trim()] : e.classList.contains('up-fd__seen') ? ['seen', ''] : [e.dataset.wait ? 'wait' : e.classList.contains('post-card--work') ? 'work' : 'post', e.dataset.wait ? e.dataset.goal : e.dataset.leader])")


def looked(pg):
    return pg.evaluate(f"() => (JSON.parse(localStorage.getItem('orkcraft.looked')) || {{}})['{PROJECT}'] ?? null")


def test_the_phone_asks_the_feed_with_its_own_last_look_and_draws_its_blocks_in_the_readers_order_with_no_tab(gui):
    since = at_look()
    pg, host, log = open_feed(gui, since)
    try:
        assert _calls(pg, host, "ideas.feed")[0] == {"since": since}, "this phone's own last look, as ms"
        assert feed(pg).get_attribute("data-look") == "feed" and sig(pg, "frame/state.js", "picked") == ""
        got = blocks(pg)
        hh = pg.eval_on_selector_all(".up-fh .up-fh__head", "(els) => els.map((e) => e.dataset.leader)")
        assert hh == ["orkmaster", "tech", "design", "product", "release"], "the heads in the reader's order"
        assert got[0] == ["label", "Waits for you"] and got[1] == ["wait", "leader"] and got[2] == ["wait", "music"], "what waits first, the clock's then main's"
        assert got[3][0] == "label" and got[3][1].startswith("New since your last look · "), got[3]
        assert [b for b in got[4:7]] == [["post", "tech"], ["post", "design"], ["post", "orkmaster"]], "the news newest first, one leader's posts one block"
        assert got[7] == ["work", "orkmaster"] and got[8] == ["seen", ""], "the goals at work, then the seen line"
        top, first, row, h = box(pg.locator(".up-fh")), box(pg.locator(".post-card").first), box(pg.locator(".up-row")), pg.viewport_size["height"]
        assert box(pg.locator(".up-top"))["y"] < top["y"] < first["y"] < row["y"] and abs(row["y"] + row["height"] - h) <= 1, "the heads row on top, the hand's row at the foot"
        assert pg.locator('.hand-up [role="tab"], .hand-up [role="tablist"]').count() == 0, "no tab of §223 in the hand"
        assert pg.locator('.hand-up .up-card[aria-pressed="true"]').count() == 0 and cards(pg).count() >= 2 and pg.locator(".hand-up .hand-lifted").count() == 0, "the hand's row unchanged, no card of it raised"
        clock = pg.locator('.post-card[data-wait="starts"] .post-card__clock').inner_text().strip()
        assert clock.startswith("Starts by itself at ") and clock[-5:-2].endswith(":")
        assert not any(ch.isdigit() for ch in pg.locator(".up-fh").inner_text()), "no count on a head"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_with_no_look_the_feed_asks_with_no_since_and_the_look_is_written_when_the_person_leaves_never_on_the_first_draw(gui):
    pg, host, log = open_feed(gui)
    try:
        assert _calls(pg, host, "ideas.feed")[0] == {}, "none kept: everything is news"
        assert pg.locator(".up-fd__seen").count() == 0 and looked(pg) is None, "nothing written on the first draw"
        before = int(dt.datetime.now().timestamp() * 1000) - 1000
        cards(pg).first.click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.look === 'goal'", timeout=WAIT_MS)
        ms = looked(pg)
        assert ms is not None and ms >= before, "a goal picked leaves the feed: the look is written"
        n = len(_calls(pg, host, "ideas.feed"))
        cards(pg).first.click()                                         # the card looked at, pressed again: back to the feed
        feed(pg).wait_for(timeout=WAIT_MS)
        got = _calls(pg, host, "ideas.feed", at_least=n + 1)
        assert got[-1] == {"since": ms} and sig(pg, "frame/state.js", "picked") == "", "asked again with the look written when it left"
        pg.locator(".up-fd__seen").wait_for(timeout=WAIT_MS)
        ms2 = looked(pg)
        pg.evaluate("() => { Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true }); document.dispatchEvent(new Event('visibilitychange')); }")
        assert looked(pg) >= ms2, "the page hidden writes it too"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_look_is_wiped_with_the_pairing(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        pg.evaluate("async () => { const m = await import('/static/js/linkpaired.js'); m.store.clear(); }")
        assert looked(pg) is None, "kept beside the pairing, wiped with it as the kept town is"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_head_pressed_is_aria_pressed_the_others_faint_a_line_says_the_feed_shows_only_it_and_pressed_again_the_whole_feed(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        head_of(pg, "tech").click()
        pg.locator(".up-fd__only").wait_for(timeout=WAIT_MS)
        assert head_of(pg, "tech").get_attribute("aria-pressed") == "true" and sig(pg, "frame/state.js", "tab") == "tech"
        faint = [float(h.evaluate("(e) => getComputedStyle(e).opacity")) < 1 for h in heads(pg).all()]
        assert faint == [True, False, True, True, True], "the others faint"
        assert pg.locator(".up-fd__only").inner_text().strip() == "The feed shows only Tech"
        got = blocks(pg)
        assert ["post", "design"] not in got and ["post", "orkmaster"] not in got and ["post", "tech"] in got, "narrowed to its posts"
        assert ["work", "tech"] in got and got.index(["work", "tech"]) < got.index(["post", "tech"]), "its goals at work above its posts"
        assert pg.locator('.post-card--work[data-leader="tech"] .up-fd__gc').count() == 1 and pg.locator('.post-card--work[data-leader="tech"] .up-fd__gc').get_attribute("data-goal") == "seat"
        concern = pg.locator(".up-fd__concerns .up-concern__what").first
        concern.wait_for(timeout=WAIT_MS)
        assert concern.inner_text().strip() == CONCERN["what"] and box(concern)["y"] < box(pg.locator('.post-card--news[data-leader="tech"]'))["y"], "its concerns above its posts"
        assert pg.locator(".up-ph, .up-squad, .up-tools").count() == 0, "the party's long header is not drawn"
        shot(pg, "tech")
        head_of(pg, "tech").click()
        pg.locator(".up-fd__only").wait_for(state="detached", timeout=WAIT_MS)
        assert head_of(pg, "tech").get_attribute("aria-pressed") == "false" and all(float(h.evaluate("(e) => getComputedStyle(e).opacity")) == 1 for h in heads(pg).all())
        assert sig(pg, "frame/state.js", "tab") == "orkmaster" and ["post", "design"] in blocks(pg), "the whole feed again, no line"
        head_of(pg, "orkmaster").click()
        pg.locator(".up-fd__only").wait_for(timeout=WAIT_MS)
        assert pg.locator(".up-fd__only").inner_text().strip() == "The feed shows only Orkmaster" and [b for b in blocks(pg) if b[0] == "post"] == [["post", "orkmaster"]]
        head_of(pg, "orkmaster").click()
        pg.locator(".up-fd__only").wait_for(state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_party_picked_in_the_crowns_menu_opens_the_same_narrowed_feed(gui):         # was test_phone_look_browser's party look (its header, squad and tools: gone)
    pg, host, log = open_feed(gui, at_look())
    try:
        pick_from_menu(pg, "party", "Tech")
        pg.locator(".up-fd__only").wait_for(timeout=WAIT_MS)
        assert feed(pg).get_attribute("data-only") == "tech" and head_of(pg, "tech").get_attribute("aria-pressed") == "true" and sig(pg, "frame/state.js", "picked") == ""
        assert pg.locator('.hand-up .up-card[aria-pressed="true"]').count() == 0, "no card raised"
        pg.locator('.post-card--work[data-leader="tech"] .up-fd__gc').first.click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'seat'", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "seat" and sig(pg, "frame/state.js", "tab") == "orkmaster", "a press on its goal picks the goal"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_party_with_no_concerns_and_no_goal_at_work_has_neither(gui):              # was test_phone_look_browser's party with neither section
    pg, host, log = open_feed(gui, at_look())
    try:
        pick_from_menu(pg, "party", "Release")
        pg.locator(".up-fd__only").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".up-concerns, .post-card--work").count() == 0, "none when it has none"
        assert [b for b in blocks(pg) if b[0] == "wait"] == [["wait", "music"]], "its own wait: Lobby waits for main under Release"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_heads_say_news_with_a_sign_and_asking_with_the_yellow_ring_and_its_bang_never_a_number_each_44_px_its_name_14_px(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        for h in heads(pg).all():
            r = box(h)
            assert r["width"] >= 44 and r["height"] >= 44, h.get_attribute("data-leader")
            assert h.locator(".up-fh__name").evaluate("(e) => parseFloat(getComputedStyle(e).fontSize)") == 14
        tech, design, product = head_of(pg, "tech"), head_of(pg, "design"), head_of(pg, "product")
        assert tech.locator(".up-fh__ask").inner_text().strip() == "!" and "is-asks" in tech.get_attribute("class") and tech.get_attribute("aria-label") == "Tech: asks you"
        assert design.locator(".up-fh__news .ork-sign.post").count() == 1 and design.get_attribute("aria-label") == "Design: news since your last look", "the ring is never alone: a sign beside it"
        assert product.locator(".up-fh__news, .up-fh__ask").count() == 0 and product.get_attribute("aria-label") == "Product"
        assert tech.locator(".up-fh__ring").evaluate("(e) => getComputedStyle(e).backgroundColor") == pg.evaluate("() => { const e = document.createElement('i'); e.style.color = 'var(--ork-alert)'; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }")
        assert product.locator(".up-fh__ring").evaluate("(e) => getComputedStyle(e).backgroundColor") == "rgba(0, 0, 0, 0)", "no ring with no news"
        text = pg.locator(".up-feed").inner_text()
        assert not any(ch.isdigit() for ch in pg.locator(".up-fh").inner_text()) and "deck" not in text.lower() and "stack" not in text.lower()
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_one_leaders_posts_in_a_row_are_one_block_more_from_it_opens_them_and_the_seen_line_spreads(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        tech = pg.locator('.post-card--news[data-leader="tech"]')
        assert "is-stacked" in tech.get_attribute("class") and tech.locator(".post-card__more").count() == 0, "the edges of the rest under its card"
        assert tech.locator(".post-card__name").inner_text().strip() == "Tech" and tech.locator(".post-card__sub").first.inner_text().strip().startswith("news · ")
        more = tech.get_by_role("button", name="More from Tech")
        assert more.get_attribute("aria-expanded") == "false" and box(more)["height"] >= 44
        more.click()
        assert tech.locator(".post-card__more").count() == 2 and "is-stacked" not in tech.get_attribute("class") and tech.get_by_role("button", name="Less from Tech").get_attribute("aria-expanded") == "true"
        line = pg.locator(".up-fd__seenline")
        assert line.locator(".up-fd__seenwords").inner_text().strip().startswith("You have seen everything since ") and line.locator(".up-fd__small").count() == 2, "its small heads"
        assert line.get_attribute("aria-expanded") == "false" and pg.locator(".up-fd__spread").count() == 0
        line.click()
        spread = pg.locator(".up-fd__spread .post-card--seen")
        assert spread.count() == 2 and all(c.locator(".post-card__who").count() == 1 for c in spread.all()), "spread: each card's head showing"
        assert [c.get_attribute("data-leader") for c in spread.all()] == ["product", "design"]
        old = pg.locator(".up-fd__spread").inner_text()
        assert "Pick the theme" in old and "Pick the theme" not in pg.locator(".up-feed > .post-card--news").all_inner_texts()[0], "what came before the look is never news"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_wait_carries_only_its_own_acts_each_the_command_the_reader_names(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        plan, main = pg.locator('.post-card[data-wait="starts"]'), pg.locator('.post-card[data-wait="main"]')
        assert [b.get_attribute("data-act") for b in plan.locator(".post-card__acts button").all()] == ["change_spec", "start_now"]
        assert [b.get_attribute("data-act") for b in main.locator(".post-card__acts button").all()] == ["to_main"] and main.locator('[data-act="to_main"]').inner_text().strip() == "To main"
        assert all(box(b)["height"] >= 44 for b in pg.locator(".post-card__acts button").all())
        plan.locator('[data-act="start_now"]').click()
        assert _calls(pg, host, "ideas.start_now") == [{"slug": "leader"}]
        plan.locator('[data-act="change_spec"]').click()
        plan.locator("textarea").fill("Show the top ten, not three")
        plan.locator('[data-act="send"]').click()
        assert _calls(pg, host, "ideas.spec_change") == [{"idea": "leader", "text": "Show the top ten, not three"}], "the words go with the command the reader names"
        main.locator('[data-act="to_main"]').click()
        assert _calls(pg, host, "ideas.to_main") == [{"idea": "music"}]
        plan.locator(".post-card__goal").click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'leader'", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_goals_at_work_are_sideways_cards_with_a_button_each_way_of_44_px(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        work = pg.locator('.up-feed > .post-card--work[data-leader="orkmaster"]')
        work.scroll_into_view_if_needed()
        assert [c.get_attribute("data-goal") for c in work.locator(".up-fd__gc").all()] == ["seat", "lobby"], "each party's goals at work, the Board's order"
        prev, nxt = work.get_by_role("button", name="Previous goals"), work.get_by_role("button", name="Next goals")
        assert all(box(b)["width"] >= 44 and box(b)["height"] >= 44 for b in (prev, nxt))
        assert prev.is_disabled() and not nxt.is_disabled(), "at the start: only the way on"
        car = work.locator(".up-fd__car")
        nxt.click()
        pg.wait_for_function("() => document.querySelector('.post-card--work .up-fd__car').scrollLeft > 0 && !document.querySelector('.post-card--work [aria-label=\"Previous goals\"]').disabled", timeout=WAIT_MS)
        assert car.evaluate("(e) => e.scrollWidth > e.clientWidth")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_keys_walk_the_heads_the_blocks_and_their_arrows(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        head_of(pg, "orkmaster").focus()
        seen = []
        for _ in range(40):
            seen.append(pg.evaluate("() => { const e = document.activeElement; return e.classList.contains('up-fh__head') ? 'head' : e.classList.contains('up-fd__arrow') ? 'arrow' : e.matches('article.post-card') ? 'block' : e.classList.contains('up-fd__seenline') ? 'seen' : 'other'; }"))
            pg.keyboard.press("Tab")
        assert seen[:5] == ["head"] * 5, seen
        assert "block" in seen and "arrow" in seen and "seen" in seen, seen
        assert seen.index("block") < seen.index("arrow") < seen.index("seen")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_feed_reads_at_17_px_nothing_under_14_and_every_word_at_4_5_to_1(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        pg.locator(".up-fd__seenline").click()
        got = pg.evaluate(READABLE)
        assert got["body"] == "17px" and got["min"] >= 14, got["small"]
        assert got["low"] == [], got["low"]
        assert pg.locator(".post-card").first.evaluate("(e) => getComputedStyle(e).backgroundColor") == "rgb(51, 55, 58)", "a block on the lifted card"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_with_nothing_picked_nothing_in_the_hand_and_nothing_fed_the_feed_says_nothing_waits_and_the_crown_and_the_plus_card_stay(gui):   # was test_phone_look_browser's empty middle
    pg, host, log = open_up(gui, "empty")
    try:
        pg.get_by_text("Nothing waits for you.", exact=True).wait_for(timeout=WAIT_MS)
        assert feed(pg).count() == 1 and pg.locator(".post-card").count() == 0 and cards(pg).count() == 0
        assert pg.locator(".up-crown").count() == 1 and pg.locator(".up-plus .hand-plus").count() == 1
        pick_from_menu(pg, "party", "Tech")
        assert feed(pg).get_attribute("data-only") == "tech", "a party can be looked at with an empty hand: its feed"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def goal_blocks(pg):
    """A goal's feed's blocks in the page's order, as `blocks` reads the project's."""
    return pg.eval_on_selector_all(".up-gfeed > .post-card, .up-gfeed > .up-fd__lab, .up-gfeed > .up-fd__seen",
                                   "(els) => els.map((e) => e.classList.contains('up-fd__lab') ? ['label', e.textContent.trim()] : e.classList.contains('up-fd__seen') ? ['seen', ''] : [e.dataset.wait ? 'wait' : 'post', e.dataset.wait ? e.dataset.goal : e.dataset.leader])")


def goal_heads(pg):
    return pg.locator(".up-gfeed .up-fh__head")


def test_a_goals_screen_asks_the_feed_cut_to_its_route_with_the_look_the_project_was_drawn_with_its_heads_the_routes_leaders(gui):
    since = at_look()
    pg, host, log = open_feed(gui, since)
    try:
        pick_from_menu(pg, "goal", SEAT)
        pg.locator(".up-gfeed .post-card").first.wait_for(timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.feed")[-1] == {"since": since, "route": "seat"}, "the same reader cut to the goal's route, with the look the project's feed was drawn with"
        assert looked(pg) > since, "leaving the project's feed wrote the look; the goal's feed did not read it"
        assert [h.get_attribute("data-leader") for h in goal_heads(pg).all()] == ["orkmaster", "design", "tech", "product"], "its heads the route's leaders, in route order"
        assert pg.locator(".up-route, .up-step").count() == 0 and pg.locator('.up-look[data-look="goal"] > .up-fh').count() == 0, "in place of the route's legs, inside the goal's screen"
        assert goal_blocks(pg)[0][0] == "label" and goal_blocks(pg)[1:] == [["post", "tech"], ["post", "design"]], "its posts in the reader's order, one leader's in a row one block"
        ys = [box(pg.locator(s).first)["y"] for s in (".up-gh", ".up-phases", ".up-gfeed .up-fh", ".up-gfeed .post-card", ".up-why", ".up-tasks")]
        assert ys == sorted(ys) and len(set(ys)) == 6, "the header, the phases, the heads, the blocks, then why and the step's tasks"
        assert all(box(h)["height"] >= 44 and box(h)["width"] >= 44 for h in goal_heads(pg).all()), "each head 44 px at least"
        assert not any(ch.isdigit() for ch in pg.locator(".up-gfeed .up-fh").inner_text()), "no count on a head"
        pg.locator(".up-gfeed .post-card__open").click()
        assert pg.locator(".up-gfeed .post-card__more").count() == 1, "More from Tech opens the rest of its stack"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goals_question_stays_in_the_hand_raised_its_pick_one_tap_away_and_its_leader_asks_in_the_heads(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        pg.locator('.hand-up .up-card[data-key="goal:signin"]').click()
        pg.locator(".up-gfeed .up-fh__head").first.wait_for(timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.feed")[-1]["route"] == "signin"
        assert pg.locator('.hand-up .up-card[aria-pressed="true"]').get_attribute("data-key") == "goal:signin", "its card raised in the hand"
        assert [h.get_attribute("data-leader") for h in goal_heads(pg).all()] == ["orkmaster", "tech"]
        tech = pg.locator('.up-gfeed .up-fh__head[data-leader="tech"]')
        assert "is-asks" in tech.get_attribute("class") and tech.locator(".up-fh__ask").inner_text().strip() == "!", "the leader that asks: the yellow ring and its !"
        assert box(pg.locator(".hand-up .hand-lifted"))["y"] < box(pg.locator(".up-gfeed"))["y"], "its card with its answers over its feed"
        pg.locator(".hand-up .hand-lifted .q-card", has_text="Passkey").click()
        assert _calls(pg, host, "ideas.talk_answer") == [{"idea": "signin", "answers": [{"id": "q1", "pick": 1}]}], "one tap answers"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_head_pressed_in_a_goals_feed_narrows_it_and_the_goal_stays_picked(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        pick_from_menu(pg, "goal", SEAT)
        pg.locator(".up-gfeed .post-card").first.wait_for(timeout=WAIT_MS)
        tech = pg.locator('.up-gfeed .up-fh__head[data-leader="tech"]')
        tech.click()
        pg.locator(".up-gfeed .up-fd__only").wait_for(timeout=WAIT_MS)
        assert tech.get_attribute("aria-pressed") == "true" and pg.locator(".up-gfeed .up-fd__only").inner_text().strip() == "The feed shows only Tech"
        assert [float(h.evaluate("(e) => getComputedStyle(e).opacity")) < 1 for h in goal_heads(pg).all()] == [True, True, False, True], "the others faint"
        assert [b for b in goal_blocks(pg) if b[0] == "post"] == [["post", "tech"]], "narrowed to its posts"
        assert sig(pg, "frame/state.js", "picked") == "seat" and sig(pg, "frame/state.js", "tab") == "orkmaster", "the goal stays picked, no party picked"
        tech.click()
        pg.locator(".up-gfeed .up-fd__only").wait_for(state="detached", timeout=WAIT_MS)
        assert tech.get_attribute("aria-pressed") == "false" and [b for b in goal_blocks(pg) if b[0] == "post"] == [["post", "tech"], ["post", "design"]], "pressed again, the goal's whole feed"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


@pytest.mark.skipif(not SHOTS, reason="pictures for Design: set FEED_SHOTS")
def test_pictures_of_the_feed_for_design(gui):
    """The top of the project's feed, Tech's head pressed, and a goal's feed (Keep the seat, picked in the crown's menu), at 390 × 844 and three device pixels a pixel (Design's pictures, goals 169 F and G)."""
    server, browser = gui
    host = FeedHost()
    context = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, device_scale_factor=3)
    context.add_init_script(f"localStorage.setItem('orkcraft.looked', JSON.stringify({{ '{PROJECT}': {at_look(95)} }}));")
    pg = context.new_page()
    pg.route_web_socket("**/ws*", host.on_socket)
    try:
        pg.goto(server.url)
        pg.locator(".up-feed .post-card").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(800)
        shot(pg, "top")
        head_of(pg, "tech").click()
        pg.locator(".up-fd__concerns .up-concern").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        shot(pg, "tech")
        head_of(pg, "tech").click()
        pick_from_menu(pg, "goal", SEAT)
        pg.locator(".up-gfeed .post-card").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(1200)
        shot(pg, "goal")
    finally:
        context.close()


# -- the folding header, the round button and the chain (goal 169 H, decisions §292; feed.html v3 screens 7 and 8) ------------------------------------------

PLAY_UP, ROUND = "Play it on the computer", "Play, Inventory, History"


class FoldHost(FeedHost):
    """FeedHost's project with the person here (the lamp's chain lit *Here*, until 23:00) and, `asleep`, no preview to play (the die faint)."""

    def __init__(self, scenario="ready", asleep=False):
        super().__init__(scenario)
        self.asleep = asleep
        self.presence = {"here": True, "until": "2026-11-10T23:00", "held": False}

    def snapshot(self):
        s = super().snapshot()
        s["state"]["presence"] = dict(self.presence)
        if self.asleep:
            s["state"]["preview"] = ""
        return s

    def handle(self, name, a):
        if name == "presence.set":
            self.log.append((name, a))
            self.presence = {"here": a["here"], "until": "2026-11-10T19:00", "held": True}
            self.rev += 1
            self.ws.send(json.dumps(self.snapshot()))
            return self.presence
        return super().handle(name, a)


def open_fold(gui, host=None):
    return open_feed(gui, at_look(), host=host or FoldHost())


def top(pg):
    return pg.locator(".hand-up .up-top")


def middle(pg):
    return pg.locator(".hand-up .up-look")


def scroll_feed(pg, y):
    middle(pg).evaluate("(e, y) => { e.scrollTop = y; e.dispatchEvent(new Event('scroll')); }", y)
    pg.wait_for_timeout(250)


def round_button(pg):
    return pg.locator(".hand-up .up-round")


def options(pg):
    return pg.locator(".up-sel .up-sel__opt")


def focused(pg):
    return pg.evaluate("() => document.activeElement?.className || ''")


def test_the_header_holds_the_crown_the_name_settings_stop_all_the_bottles_and_the_chain_and_no_die_or_backpack(gui):
    pg, host, log = open_fold(gui)
    try:
        t = top(pg)
        kids = t.evaluate("(e) => [...e.children].filter((c) => getComputedStyle(c).display !== 'none').map((c) => [...c.classList].find((k) => k !== 'up-ico'))")
        assert kids[0] == "up-crown" and "up-stop" in kids and kids.index("up-stop") < kids.index("up-pots") < kids.index("presence-chain"), kids
        assert t.locator(".up-die, .stall-pack, .ork-die, .hand-book").count() == 0, "the die and the backpack left the header for the round button"
        stop = t.get_by_role("button", name="Stop all", exact=True)
        r = box(stop)
        assert r["width"] >= 44 and r["height"] >= 44 and stop.evaluate("(e) => getComputedStyle(e).color") == css_colour(pg, "--ork-danger"), "Stop all, 44 px, in the danger colour"
        chain = t.locator(".presence-chain")
        assert "/ds/orkui/chain/chain-rest" in chain.locator("img").get_attribute("src") and chain.locator(".presence-chain__word").inner_text() == "Here", "orkUI's chain at rest, lit Here"
        c, pots = box(chain), box(t.locator(".up-pots"))
        assert c["x"] >= pots["x"] + pots["width"] - 1 and c["width"] >= 44 and c["height"] >= 44 and c["x"] + c["width"] <= 390, "hung beside the bottles at the header's right"
        assert box(chain.locator("img"))["y"] <= box(t)["y"] + 1, "it hangs from the header's top edge"
        stop.click()
        for _ in range(40):
            if any(n == "halt" for n, _a in host.log):
                break
            pg.wait_for_timeout(50)
        assert any(n == "halt" for n, _a in host.log), "Stop all sends halt, as the menu's"
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_scrolled_the_heads_go_and_the_header_folds_to_one_thin_row_of_the_bottles_stop_all_and_the_chain(gui):
    pg, host, log = open_fold(gui)
    try:
        t, full = top(pg), box(top(pg))
        assert round(full["height"]) in (60, 61) and "is-thin" not in t.get_attribute("class")
        scroll_feed(pg, 600)
        pg.wait_for_function("() => document.querySelector('.up-top').classList.contains('is-thin')", timeout=WAIT_MS)
        thin = box(t)
        assert thin["height"] <= 45 and thin["y"] == full["y"], "one thin row where the header was"
        assert box(pg.locator(".up-fh"))["y"] + box(pg.locator(".up-fh"))["height"] <= thin["y"] + thin["height"] + 1, "the heads row scrolled away with the feed"
        for sel in (".up-pots", ".up-stop", ".presence-chain"):
            assert t.locator(sel).is_visible(), f"{sel} kept in the thin row"
        for sel in (".up-crown", ".up-name", ".up-set"):
            assert t.locator(sel).is_hidden(), f"{sel} folded away"
        assert t.locator(".presence-chain__word").inner_text() == "Here" and pots(pg).count() == 4
        for b in t.locator(".up-pot, .up-stop, .presence-chain").all():
            r = box(b)
            assert r["width"] >= 44 and r["height"] >= 44, r
        scroll_feed(pg, 0)
        pg.wait_for_function("() => !document.querySelector('.up-top').classList.contains('is-thin')", timeout=WAIT_MS)
        assert round(box(t)["height"]) in (60, 61) and t.locator(".up-crown").is_visible()
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_focused_block_is_never_under_the_folded_header(gui):
    pg, host, log = open_fold(gui)
    try:
        scroll_feed(pg, 600)
        pg.wait_for_function("() => document.querySelector('.up-top').classList.contains('is-thin')", timeout=WAIT_MS)
        assert middle(pg).evaluate("(e) => getComputedStyle(e).scrollPaddingTop") == "44px", "the middle's scroll-padding-top is the thin row's height"
        head_of(pg, "orkmaster").focus()
        walked = 0
        for _ in range(30):
            pg.keyboard.press("Tab")
            pg.wait_for_timeout(60)
            r = pg.evaluate("() => { const e = document.activeElement; if (!e?.closest('.up-look')) return null; const b = e.getBoundingClientRect(), t = document.querySelector('.up-top').getBoundingClientRect(); return [b.top, b.bottom, t.bottom]; }")
            if r is None:
                continue
            walked += 1
            assert r[0] >= r[2] - 1, f"the focused block's top {r[0]} lies under the header's foot {r[2]}"
        assert walked >= 10
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_round_button_lies_at_the_foots_right_its_face_the_die_in_its_state_and_no_count(gui):
    pg, host, log = open_fold(gui)
    try:
        b, plus_card, row = round_button(pg), box(pg.locator(".up-plus .hand-plus")), box(pg.locator(".up-row"))
        r = box(b)
        assert r["width"] >= 56 and r["height"] >= 56 and r["x"] + r["width"] >= 390 - 16 and r["y"] >= row["y"] - 8, "round, at the foot's right"
        assert plus_card["x"] <= 16 and plus_card["x"] + plus_card["width"] < 390 / 2, "the + card at the foot's left"
        assert b.get_attribute("aria-label") == ROUND and b.get_attribute("aria-expanded") == "false"
        assert b.get_attribute("data-state") == "white" and "/ds/orkui/die/die-rest" in b.locator("img").get_attribute("src"), "white while dev can be played"
        assert not any(ch.isdigit() for ch in b.inner_text() + b.get_attribute("aria-label")), "no count on the button"
        pick_from_menu(pg, "goal", SEAT)
        pg.wait_for_function("() => document.querySelector('.up-round').dataset.state === 'rune'", timeout=WAIT_MS)
        elem = next(n for n in host.nodes if n["slug"] == "seat")
        want = elem.get("hue") or elem.get("element")
        assert b.get_attribute("data-elem") == want and b.evaluate("(e) => getComputedStyle(e).backgroundColor") == css_colour(pg, f"--ork-elem-{want}"), "in the picked goal's rune"
        assert "Play: " in b.get_attribute("title")
    finally:
        pg.close()
    assert not log, "\n".join(log)
    pg, host, log = open_fold(gui, FoldHost(asleep=True))
    try:
        b = round_button(pg)
        assert b.get_attribute("data-state") == "faint" and float(b.locator("img").evaluate("(e) => getComputedStyle(e).opacity")) < 0.6, "faint while nothing can be played"
        assert b.get_attribute("title") == f"{ROUND} · Nothing to play yet"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_round_buttons_selector_of_three_by_touch_44_px_closes_on_a_second_press_and_outside(gui):
    pg, host, log = open_fold(gui)
    try:
        b = round_button(pg)
        b.tap()
        options(pg).first.wait_for(timeout=WAIT_MS)
        assert b.get_attribute("aria-expanded") == "true" and pg.locator(".up-round__scrim").is_visible()
        got = [(o.locator(".up-sel__word").inner_text(), o.locator(".up-sel__line").inner_text(), o.locator("img").get_attribute("src")) for o in options(pg).all()]
        assert [g[0] for g in got] == ["Play", "Inventory", "History"] and all(g[1] for g in got), got
        assert ["/die/die-rest" in got[0][2], "/pack/pack-shut" in got[1][2], "/book/book-shut" in got[2][2]] == [True] * 3, "each its cartoon picture"
        rb = box(b)
        for o in options(pg).all():
            r = box(o)
            assert r["width"] >= 44 and r["height"] >= 44 and r["y"] + r["height"] <= rb["y"] + 1 and r["x"] + r["width"] <= 390, ("rising over the foot, 44 px", r)
        assert not any(ch.isdigit() for ch in pg.locator(".up-sel").inner_text()), "no count"
        b.tap()
        pg.locator(".up-sel").wait_for(state="detached", timeout=WAIT_MS)
        assert b.get_attribute("aria-expanded") == "false", "a second press closes it"
        b.tap()
        options(pg).first.wait_for(timeout=WAIT_MS)
        pg.touchscreen.tap(120, 300)
        pg.locator(".up-sel").wait_for(state="detached", timeout=WAIT_MS)
        assert pg.locator(".up-round__scrim").count() == 0 and middle(pg).get_attribute("data-look") == "feed", "a tap outside closes it and presses nothing under it"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_keys_walk_the_round_buttons_three_and_esc_puts_the_focus_back(gui):
    pg, host, log = open_fold(gui)
    try:
        b = round_button(pg)
        b.focus()
        pg.keyboard.press("Enter")
        options(pg).first.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => document.activeElement?.dataset.place === 'play'", timeout=WAIT_MS)
        pg.keyboard.press("ArrowDown")
        assert pg.evaluate("() => document.activeElement.dataset.place") == "inventory"
        pg.keyboard.press("Tab")
        assert pg.evaluate("() => document.activeElement.dataset.place") == "history"
        pg.keyboard.press("ArrowDown")
        assert pg.evaluate("() => document.activeElement.dataset.place") == "play", "the arrows go round"
        pg.keyboard.press("ArrowUp")
        assert pg.evaluate("() => document.activeElement.dataset.place") == "history"
        pg.keyboard.press("Escape")
        pg.locator(".up-sel").wait_for(state="detached", timeout=WAIT_MS)
        assert "up-round" in focused(pg), "the focus back on the button"
        pg.keyboard.press("Space")
        options(pg).first.wait_for(timeout=WAIT_MS)
        pg.keyboard.press("ArrowDown")
        pg.keyboard.press("Enter")
        pg.locator(".stall-merchant").wait_for(state="visible", timeout=WAIT_MS)
        assert pg.locator(".up-sel").count() == 0, "Inventory by keys opens the stall"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_play_still_says_it_plays_on_the_computer_inventory_opens_the_stall_and_history_the_book(gui):
    pg, host, log = open_fold(gui)
    try:
        b = round_button(pg)
        b.tap()
        pg.get_by_role("button", name=PLAY_UP, exact=True).tap()
        pg.get_by_text(PLAY_UP, exact=True).wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".up-sel").count() == 0 and pg.locator(".table-over").count() == 0 and pg.locator(".play-throw, .playpane").count() == 0, "nothing thrown, no view opens"
        assert all("play" not in str(n) for n, _a in host.log)
        b.tap()
        options(pg).nth(1).tap()
        pg.locator(".stall-merchant").wait_for(state="visible", timeout=WAIT_MS)
        pg.locator("[data-stall-back]").click()
        pg.locator(".hand-up").wait_for(state="visible", timeout=WAIT_MS)
        b.tap()
        options(pg).nth(2).tap()
        pg.wait_for_selector('.table-over[data-kind="history"]', timeout=WAIT_MS)
        assert pg.locator(".hand-up").is_hidden(), "the history over the pane, as the book opens it"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_chain_pulled_says_away_and_pulled_again_here(gui):
    pg, host, log = open_fold(gui)
    try:
        chain = top(pg).locator(".presence-chain")
        assert chain.get_attribute("aria-label") == "Here, until 23:00" and chain.get_attribute("aria-pressed") == "true"
        chain.tap()
        pg.wait_for_function("() => document.querySelector('.up-top .presence-chain').dataset.here === 'false'", timeout=WAIT_MS)
        assert _calls(pg, host, "presence.set") == [{"here": False}]
        assert chain.locator(".presence-chain__word").inner_text() == "Away" and "/chain/chain-pulled" in chain.locator("img").get_attribute("src")
        assert chain.get_attribute("aria-label") == "Away, until 19:00 · held" and pg.locator(".hand-up").evaluate("(e) => e.classList.contains('is-out')")
        scroll_feed(pg, 600)
        pg.wait_for_function("() => document.querySelector('.up-top').classList.contains('is-thin')", timeout=WAIT_MS)
        chain.tap()
        pg.wait_for_function("() => document.querySelector('.up-top .presence-chain').dataset.here === 'true'", timeout=WAIT_MS)
        assert chain.locator(".presence-chain__word").inner_text() == "Here", "the thin row's chain turns it as well"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.skipif(not SHOTS, reason="pictures for Design: set FEED_SHOTS")
def test_pictures_of_the_header_and_the_round_button_for_design(gui):
    """Goal 169 H, beside feed.html v3 screens 7 and 8: the feed's top with the header, scrolled with the header folded, and the round button open, at 390 × 844 and three device pixels a pixel."""
    server, browser = gui
    host = FoldHost()
    context = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, device_scale_factor=3)
    context.add_init_script(f"localStorage.setItem('orkcraft.looked', JSON.stringify({{ '{PROJECT}': {at_look(95)} }}));")
    pg = context.new_page()
    pg.route_web_socket("**/ws*", host.on_socket)
    try:
        pg.goto(server.url)
        pg.locator(".up-feed .post-card").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(800)
        shot(pg, "h-top")
        scroll_feed(pg, 640)
        pg.wait_for_timeout(400)
        shot(pg, "h-thin")
        scroll_feed(pg, 0)
        pg.wait_for_timeout(300)
        round_button(pg).tap()
        options(pg).first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        shot(pg, "h-round")
    finally:
        context.close()


@pytest.mark.skipif(not SHOTS, reason="pictures for Design: set FEED_SHOTS")
def test_pictures_of_a_stack_opened_and_the_seen_line_spread_for_design(gui):
    """Goal 169 I, beside feed.html v3 screen 6: Tech's stack opened (More from Tech pressed, its posts shown) and the seen line pressed, spread as a deck, each card's head showing, at 390 x 844 and three device pixels a pixel."""
    server, browser = gui
    host = FeedHost()
    context = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, device_scale_factor=3)
    context.add_init_script(f"localStorage.setItem('orkcraft.looked', JSON.stringify({{ '{PROJECT}': {at_look(95)} }}));")
    pg = context.new_page()
    pg.route_web_socket("**/ws*", host.on_socket)
    try:
        pg.goto(server.url)
        pg.locator(".up-feed .post-card").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(800)
        tech = pg.locator('.post-card--news[data-leader="tech"]')
        tech.get_by_role("button", name="More from Tech").click()
        pg.locator('.post-card--news[data-leader="tech"] .post-card__more').first.wait_for(timeout=WAIT_MS)
        tech.scroll_into_view_if_needed()
        pg.wait_for_timeout(500)
        shot(pg, "stack-open")
        line = pg.locator(".up-fd__seenline")
        line.click()
        pg.locator(".up-fd__spread .post-card--seen").first.wait_for(timeout=WAIT_MS)
        scroll_feed(pg, 100000)
        pg.wait_for_timeout(500)
        shot(pg, "seen-spread")
    finally:
        context.close()
