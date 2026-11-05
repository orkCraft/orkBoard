"""Spec 128 part G (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md, decisions §206.10), in a real browser against a stub host: a goal's rune is a shape in a
colour. Two goals of one shape and different hues are drawn in their hues (the computed background of the rune differs; the shape is the same mask), in the Orkmaster's column and
on a task card; a goal with a shape and no hue of its own is drawn in its shape's colour; the + card's seal shows the next goal's shape in `next_hues[shown]`."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import ColumnHost, back, open_column, ripe  # noqa: E402
from tests import narrow  # noqa: E402
from tests.test_hand_desktop_browser import head, node, task  # noqa: E402
from tests.test_table_desktop_browser import TableHost, node as table_node, task as table_task  # noqa: E402

pytestmark = pytest.mark.browser


class HueHost(ColumnHost):
    """The column's project with runes of 25: two goals of the shape ice in the hues ice and lava (To review), a goal of the shape void kept from before (no hue: its shape's colour), and two goals at
    work of one shape (meadow) in two hues, each with a task running."""

    def __init__(self):
        super().__init__()
        self.nodes = [
            node("one", "tech", "Round timer on phones", "table", state="ready", agreed=True, element="ice", hue="ice", back=back(ripe=ripe(120))),
            node("two", "tech", "Tidy the scoring module", "table", state="ready", agreed=True, element="ice", hue="lava", back=back(ripe=ripe(480))),
            node("old", "design", "Lobby in Polish", "table", state="ready", agreed=True, element="void", back=back(ripe=ripe(300))),
            node("wa", "tech", "Make the loop", "table", state="working", element="meadow", hue="meadow", stage="implementation", tasks=[task("a1", "Write the loop", "running", head=head("peon", "tech"))]),
            node("wb", "tech", "Make the lobby", "table", state="working", element="meadow", hue="void", stage="implementation", tasks=[task("b1", "Write the lobby", "running", head=head("peon", "tech"))]),
        ]
        for g in self.parties:
            g["next_hues"] = {"meadow": "dust", "ice": "meadow", "dust": "lava", "void": "ice", "lava": "void"}
            g["next_element"], g["next_hue"], g["free_elements"] = "dust", "lava", []              # the project's next goal: a dust rune in the lava hue, no shape free


def colour(pg, selector, token=None):
    """The rune's computed colours: `[background-color of each match]`; `token`: the value of the custom property `--ork-elem-<token>` on the root."""
    if token:
        return pg.evaluate("(t) => { const s = document.createElement('span'); s.style.color = `var(--ork-elem-${t})`; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; }", token)
    return pg.eval_on_selector_all(selector, "els => els.map((e) => getComputedStyle(e).backgroundColor)")


def test_two_goals_of_one_shape_and_different_hues_are_drawn_in_their_hues_in_the_column(gui):
    pg, host, log = open_column(gui, host=HueHost())
    try:
        one = pg.locator('.col-card[data-goal="one"] .ork-sigil__seal .ork-elem').first
        two = pg.locator('.col-card[data-goal="two"] .ork-sigil__seal .ork-elem').first
        one.wait_for(timeout=WAIT_MS)
        assert "ice" in one.get_attribute("class").split() and "ice" in two.get_attribute("class").split(), "the same shape"
        assert "k-lava" in two.get_attribute("class").split() and "k-lava" not in one.get_attribute("class").split()
        a, b = colour(pg, '.col-card[data-goal="one"] .ork-sigil__seal .ork-elem'), colour(pg, '.col-card[data-goal="two"] .ork-sigil__seal .ork-elem')
        assert a[0] != b[0], "drawn in two colours"
        assert a[0] == colour(pg, "", "ice") and b[0] == colour(pg, "", "lava"), (a, b)
        old = colour(pg, '.col-card[data-goal="old"] .ork-sigil__seal .ork-elem')
        assert old[0] == colour(pg, "", "void"), "a goal of before has no hue: its shape's colour"
        assert not [m for m in log if "pageerror" in m], log
    finally:
        pg.close()


def test_two_goals_of_one_shape_and_different_hues_are_drawn_in_their_hues_on_a_task_card(gui):
    server, browser = gui
    host = TableHost()
    host.nodes.append(table_node("plain", "tech", "Keep the seat when a tab sleeps", "working", "implementation", "ice", "feature", [table_task("p1", "Keep the seat when a tab sleeps", "running")]))
    host.nodes.append(table_node("hued", "tech", "Keep the seat after a restart", "working", "implementation", "ice", "feature",
                                 [table_task("h1", "Keep the seat after a restart", "running")], hue="lava"))
    pg = narrow.page(browser, "wide")
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    try:
        pg.goto(server.url)
        pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
        plain = pg.locator('.table .table-card[data-goal="plain"] .ork-elem').first
        hued = pg.locator('.table .table-card[data-goal="hued"] .ork-elem').first
        plain.wait_for(timeout=WAIT_MS)
        hued.wait_for(timeout=WAIT_MS)
        assert "ice" in plain.get_attribute("class").split() and "ice" in hued.get_attribute("class").split(), "the same shape"
        a, b = plain.evaluate("e => getComputedStyle(e).backgroundColor"), hued.evaluate("e => getComputedStyle(e).backgroundColor")
        assert a != b, "drawn in two colours"
        assert a == colour(pg, "", "ice") and b == colour(pg, "", "lava"), (a, b)
        assert not errors, errors
    finally:
        pg.close()


def test_the_plus_cards_seal_shows_the_next_goals_shape_in_its_hue(gui):
    pg, host, log = open_column(gui, host=HueHost())
    try:
        pg.locator('.table-tab[data-tab="tech"]').click()
        seal = pg.locator(".hand .hand-plus .ork-sigil__seal .ork-elem").first
        seal.wait_for(timeout=WAIT_MS)
        assert "dust" in seal.get_attribute("class").split() and "k-lava" in seal.get_attribute("class").split()
        assert seal.evaluate("e => getComputedStyle(e).backgroundColor") == colour(pg, "", "lava"), "the shape of the next goal in its hue"
        assert not [m for m in log if "pageerror" in m], log
    finally:
        pg.close()


@pytest.mark.parametrize("explicit", [False, True])
def test_draft_preview_is_read_only_and_submission_allocates_its_rune(gui, fake_repo, explicit):
    """Drive the face with real snapshot predictions and submit to the real host.

    Only the surrounding Board is stubbed, to keep background work out of this check.
    """
    from orkboard.gui.board_host import Orkboard
    from orkboard.realm import idea_element, ideas

    real = Orkboard(fake_repo)
    root, state = real.ideas.root(), real.ideas.state_dir
    party = ideas.add_track(root, "Tech")
    # Every shape held once: default meadow/ice; explicit dust/meadow.
    for shape in idea_element.ELEMENTS:
        slug = ideas.add_idea(root, f"Holder {shape}", party, state)
        ideas.save_state(state, slug, state="working", element=shape, hue=shape)
    snapshot = real.command("ideas.map", {})["goals"][0]

    class AllocatingHost(HueHost):
        def __init__(self):
            super().__init__()
            self.allocated = None
            for g in self.parties:
                for key in ("next_element", "next_hue", "next_hues", "free_elements"):
                    g[key] = snapshot[key]

        def handle(self, name, args):
            if name == "ideas.add":
                self.log.append((name, args))
                self.allocated = real.command(name, {**args, "party": party, "hold": True})
                return self.allocated
            return super().handle(name, args)

    host = AllocatingHost()
    pg, host, log = open_column(gui, host=host)
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in state.rglob("state.json")}
    rev = real.snapshot()["ideas_rev"]
    shape = "dust" if explicit else snapshot["next_element"]
    hue = snapshot["next_hues"][shape]
    assert shape != hue
    seal = ".hand .hand-plus .ork-sigil__seal .ork-elem"
    square = '.hand-field [data-sq="rune"] .ork-elem'

    def check(selector):
        pg.wait_for_function("([s, shape, hue]) => { const e = document.querySelector(s); return e?.classList.contains(shape) && e.classList.contains(`k-${hue}`); }", arg=[selector, shape, hue], timeout=WAIT_MS)
        assert colour(pg, selector)[0] == colour(pg, "", hue)

    try:
        pg.locator('.table-tab[data-tab="tech"]').click()
        pg.locator(".hand .hand-plus").click()
        area = pg.locator(".hand-field__text")
        area.fill("A fresh preview allocation")
        if explicit:
            pg.locator('[data-sq="rune"]').click()
            for choice in idea_element.ELEMENTS:
                assert colour(pg, f'[data-rune="{choice}"] .ork-elem')[0] == colour(pg, "", choice)
            pg.locator('[data-rune="dust"]').click()
            check('.hand-field .corner__rune .ork-elem')
        check(square)
        check(seal)
        area.press("Escape")
        pg.wait_for_selector(".hand-field", state="detached", timeout=WAIT_MS)
        check(seal)
        pg.locator(".hand .hand-plus").click()
        check(square)
        assert pg.locator(".hand-field__text").input_value() == "A fresh preview allocation"
        assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in state.rglob("state.json")} == before
        assert real.snapshot()["ideas_rev"] == rev
        assert not [a for name, a in host.log if name == "ideas.add"]
        pg.locator(".hand-field__text").press("Enter")
        pg.wait_for_selector(".hand-field", state="detached", timeout=WAIT_MS)
        assert (host.allocated["element"], host.allocated["hue"]) == (shape, hue)
        sent = [a for name, a in host.log if name == "ideas.add"][-1]
        assert sent.get("element") == (shape if explicit else None)
        assert "hue" not in sent
        assert not [m for m in log if "pageerror" in m], log
    finally:
        pg.close()
        real.close()
