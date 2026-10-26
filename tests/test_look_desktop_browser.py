"""Spec 85 B (docs/specs/85-the-elf-asks-and-shows.md §1, §3, §4, §5): the faces of the look on the desktop, in a real browser at 1 440 × 900 against the arena's stub host.
The elf's question is a stop in the hand with the elf's head and *<Name> asks about the look*, its choices answer in one click and *Pictures you like* opens the form that takes
pictures; a card with a picture wears it as its face and a result opened in the right column shows it large, or says there is none (spec 90 §2.3); a card and a stack say *k of n done*; the card of a merged task
turns over once to *What it made*."""
from __future__ import annotations

import base64

import pytest

pytest.importorskip("playwright.sync_api")

from tests import pick_files as pf  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import ELF, member  # noqa: E402
from tests.test_field_rows_browser import RowsHost  # noqa: E402
from tests.test_shell_browser import _calls, _open, _stop, box  # noqa: E402

pytestmark = pytest.mark.browser

PNG = "data:image/png;base64," + base64.b64encode(pf.png(64, 40)).decode()
SHOT = {"id": "k3-shot-r1", "file": "shot.png", "w": 1280, "h": 800, "url": PNG}
ELF_BY = member("screens", "Screens", ELF, "build")
MOOD = {"ask": "What mood should the sign-in have?", "choices": ["Calm", "Loud", "Playful"], "pick": 0, "why": "the product is a tool", "look": True, "by": ELF_BY}
REFS = {"ask": "Any pictures to start from?", "choices": ["Pictures you like", "None", "Links"], "pick": 1, "why": "", "look": True, "by": ELF_BY}


class LookHost(RowsHost):
    """The arena's stub with its goals counted, a picture on two tasks and the elf's questions."""

    def __init__(self, questions=(MOOD,)):
        super().__init__()
        for n in self.nodes:
            n["done"], n["of"] = n["progress"]["done"], n["progress"]["total"]
            for t in n["tasks"]:
                t["shot"], t["made"] = None, ""
        self.node_of("register")["tasks"][2]["shot"] = dict(SHOT)                 # k3 runs, with a picture
        self.node_of("register")["results"][0]["shot"] = dict(SHOT)               # the result of k1 waits for a look, with its picture
        self.node_of("signin")["results"][0]["shot"] = {"none": "no picture: no preview"}
        second = self.node_of("second")
        second["asked"] = [dict(q) for q in questions]
        self.questions = list(questions)

    def needs_you(self):
        rows = super().needs_you()
        for r in rows:
            if r.get("idea") == "second":
                r["asked"] = [{k: v for k, v in q.items() if k not in ("by",)} for q in self.questions]
                r["text"] = self.questions[0]["ask"]
                r["questions"] = [q["ask"] for q in self.questions]
        return rows


@pytest.fixture
def look(gui):
    pg, host, errors = _open(gui, host=LookHost(), ready=".arena-phead")
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    pg.locator(".arena-task[data-key='register/k3']").wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def card(pg, key):
    return pg.locator(f".arena-task[data-key='{key}']")


# -- the elf asks (§1, §5) -----------------------------------------------------------------------------------------------------------------

def test_the_elfs_question_is_a_stop_with_its_head_and_its_name_over_the_look(look):
    pg, host = look
    stop = pg.locator(".arena-hc[data-kind=asks]")
    assert stop.locator(".arena-banner").inner_text() == "Screens asks about the look"
    assert "/races/elf-warrior" in stop.locator(".arena-hc__who img.ork-race__head").get_attribute("src")                         # the elf's head, small
    assert stop.locator(".arena-hc__who").get_attribute("title") == "asked by Screens"
    assert "What mood should the sign-in have?" in stop.locator(".arena-hc__text").inner_text()


def test_a_question_that_is_not_of_the_look_keeps_its_own_title(gui):
    host = LookHost(questions=({**MOOD, "look": False},))
    pg, host, errors = _open(gui, host=host, ready=".arena-phead")
    assert pg.locator(".arena-hc[data-kind=asks] .arena-banner").inner_text() == "Passkey on a second device"
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_choice_of_the_look_answers_in_one_click_with_the_pick_marked(look):
    pg, host = look
    stop = _stop(pg, "asks")
    buttons = stop.locator(".arena-hc__q.is-text")
    assert [b.inner_text() for b in buttons.all()] == ["● Calm", "Loud", "Playful"]
    buttons.nth(1).click()
    assert _calls(pg, host, "ideas.answer") == [{"slug": "second", "answers": ["Loud"]}]


def test_pictures_you_like_opens_the_form_which_takes_pictures_and_sends_them_with_the_answer(gui, tmp_path):
    pg, host, errors = _open(gui, host=LookHost(questions=(REFS,)), ready=".arena-phead")
    stop = _stop(pg, "asks")
    stop.get_by_role("button", name="Pictures you like").click()
    form = pg.get_by_role("dialog", name="Questions: Passkey on a second device")
    form.wait_for(timeout=WAIT_MS)
    assert form.get_by_label("Answer 1: Any pictures to start from?").input_value() == "Pictures you like"
    assert [b.inner_text() for b in form.locator(".board-questions__choices button").all()] == ["Pictures you like", "None", "Links"]
    assert form.locator("[data-pictures]").count() == 1
    (tmp_path / "like.png").write_bytes(pf.png(40, 30))
    form.locator("input[type=file]").set_input_files(str(tmp_path / "like.png"))
    form.locator("[data-pictures] img").wait_for(timeout=WAIT_MS)
    assert form.locator("[data-pictures] img").count() == 1
    form.locator(".board-questions__choices button", has_text="None").click()                  # a choice fills the box
    assert form.get_by_label("Answer 1: Any pictures to start from?").input_value() == "None"
    form.locator(".board-questions__choices button", has_text="Pictures you like").click()
    form.get_by_role("button", name="Send").click()
    (sent,) = _calls(pg, host, "ideas.answer")
    assert sent["slug"] == "second" and sent["answers"] == ["Pictures you like"] and len(sent["photos"]) == 1
    assert base64.b64decode(sent["photos"][0]["data"])[:3] == b"\xff\xd8\xff"                       # shrunk to a JPEG
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_question_with_no_picture_choice_has_no_add_a_picture(gui):
    pg, host, errors = _open(gui, host=LookHost(questions=(MOOD,)), ready=".arena-phead")
    _stop(pg, "asks").get_by_role("button", name="Open…").click()
    form = pg.get_by_role("dialog", name="Questions: Passkey on a second device")
    form.wait_for(timeout=WAIT_MS)
    assert form.locator("[data-pictures]").count() == 0 and form.get_by_label("Answer 1: What mood should the sign-in have?").input_value() == "Calm"
    pg.close()
    assert not errors, "\n".join(errors)


# -- a card's picture, its count (§3, §4) ---------------------------------------------------------------------------------------------------

def test_a_card_with_a_picture_wears_it_as_its_face_behind_its_words(look):
    pg, host = look
    shot, plain = card(pg, "register/k3"), card(pg, "register/k2")
    assert "has-shot" in shot.get_attribute("class") and "has-shot" not in plain.get_attribute("class")
    img = shot.locator("img.arena-task__shot")
    assert img.get_attribute("src") == PNG and plain.locator("img").count() == 0
    whole, face = shot.bounding_box(), img.bounding_box()
    assert abs(face["width"] - whole["width"]) <= 2 and abs(face["height"] - whole["height"]) <= 2                                # the whole card
    assert abs(whole["height"] / whole["width"] - 7 / 5) < 0.02 and abs(plain.bounding_box()["width"] - whole["width"]) <= 1      # still 5:7, as wide as the others
    assert img.evaluate("e => getComputedStyle(e).position") == "absolute" and img.evaluate("e => getComputedStyle(e).pointerEvents") == "none"
    assert shot.locator(".arena-task__name").evaluate("e => getComputedStyle(e).zIndex") == "1"                                  # its words are over it
    assert shot.locator(".arena-task__name").inner_text() == "Register screen"
    shot.click()                                                                                                       # a press still opens the task
    pg.locator(".shell-drawer").wait_for(timeout=WAIT_MS)


def test_a_card_says_how_far_its_goal_is_and_a_goal_with_no_plan_says_nothing(look):
    pg, host = look
    assert card(pg, "register/k3").locator(".arena-task__count").inner_text() == "0 of 6 done"
    assert card(pg, "signin/v1").locator(".arena-task__count").inner_text() == "2 of 4 done"
    host.node_of("register")["done"], host.node_of("register")["of"] = 3, 6
    host.bump({})
    pg.wait_for_function("() => document.querySelector(\"[data-key='register/k3'] .arena-task__count\")?.textContent === '3 of 6 done'", timeout=WAIT_MS)
    host.node_of("register")["of"] = 0
    host.bump({})
    pg.wait_for_function("() => !document.querySelector(\"[data-key='register/k3'] .arena-task__count\")", timeout=WAIT_MS)


# -- a result opened in the right column (§3; spec 90 §2.3) ------------------------------------------------------------------------------------

def _opened(pg, key):
    """A result's card in the hand pressed: the result in the right column."""
    pg.locator(f'.arena-hc[data-key="{key}"] .arena-hc__open').focus()
    pg.keyboard.press("Enter")
    got = pg.locator(".shell-drawer .shell-result")
    got.wait_for(timeout=WAIT_MS)
    return got


def test_a_result_opened_shows_the_picture_large_or_says_there_is_none(look):
    pg, host = look
    mine = _opened(pg, "result/register/k1")
    img = mine.locator(".arena-result__shot img")
    img.wait_for(timeout=WAIT_MS)
    whole = mine.bounding_box()
    assert img.get_attribute("src") == PNG and img.get_attribute("alt") == "What “Challenge store” looks like"
    shown = img.bounding_box()
    assert shown["width"] >= whole["width"] - 64 and shown["width"] >= 250 and abs(shown["width"] / shown["height"] - 1280 / 800) < 0.05      # the width of the column, its own shape
    other = _opened(pg, "result/signin/c2")
    none = other.locator("[data-noshot]")
    none.wait_for(timeout=WAIT_MS)
    assert none.inner_text() == "no picture: no preview" and other.locator(".arena-result__shot img").count() == 0


def test_a_result_without_a_picture_or_a_word_about_one_is_as_it_was(look):
    pg, host = look
    host.node_of("register")["results"][0]["shot"] = None
    host.node_of("signin")["results"][0].pop("shot")
    host.bump({})
    got = _opened(pg, "result/register/k1")
    pg.wait_for_function("() => !document.querySelector('.arena-result__shot')", timeout=WAIT_MS)
    assert got.locator(".arena-result__shot img, [data-noshot]").count() == 0


# -- a done card turns over (§4) ------------------------------------------------------------------------------------------------------------

WATCH = """() => { window.__made = []; new MutationObserver((rs) => rs.forEach((r) => r.addedNodes.forEach((n) => {
  const m = n.nodeType === 1 && (n.matches?.('[data-made]') ? n : n.querySelector?.('[data-made]')); if (m) window.__made.push(m.textContent); }))).observe(document.body, { childList: true, subtree: true }); }"""


def test_the_card_of_a_merged_task_turns_over_once_to_what_it_made(look):
    pg, host = look
    pg.evaluate(WATCH)
    task = host.node_of("register")["tasks"][1]                                                   # k2 merges
    task["state"], task["made"] = "merged", "Add the credential table"
    host.node_of("register")["done"] = 1
    host.bump({})
    pg.wait_for_function("() => window.__made.length > 0", timeout=WAIT_MS)
    assert pg.evaluate("window.__made") == ["What it madeAdd the credential table"]
    pg.wait_for_function("() => !document.querySelector(\"[data-key='register/k2']\")", timeout=WAIT_MS)       # then it is gone
    assert pg.locator("[data-made]").count() == 0


def test_a_card_that_is_dropped_or_merged_with_nothing_made_does_not_turn(look):
    pg, host = look
    pg.evaluate(WATCH)
    host.node_of("register")["tasks"][1]["state"] = "merged"                                       # a task that committed nothing: `made` is empty
    host.node_of("register")["tasks"][2]["state"] = "dropped"
    host.bump({})
    pg.wait_for_function("() => !document.querySelector(\"[data-key='register/k2']\") && !document.querySelector(\"[data-key='register/k3']\")", timeout=WAIT_MS)
    assert pg.evaluate("window.__made") == []


def test_the_turn_stands_still_under_reduced_motion(gui):
    server, browser = gui
    host = LookHost()
    pg = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".arena-task[data-key='register/k3']").wait_for(timeout=WAIT_MS)
    assert card(pg, "register/k3").locator(".arena-task__count").inner_text() == "0 of 6 done"
    assert pg.evaluate("() => { const e = document.createElement('i'); e.className = 'arena-task__made'; document.body.appendChild(e); const a = getComputedStyle(e).animationName; e.remove(); return a; }") == "none"
    pg.close()


def test_the_looks_sheet_is_orkuis_tokens_only(look):
    pg, host = look
    img = card(pg, "register/k3").locator(".arena-task__name")
    assert img.evaluate("e => getComputedStyle(e).backgroundColor") != "rgba(0, 0, 0, 0)"                                  # a panel that lets the picture through
    assert box(pg, ".arena-task__count")["height"] <= 16                                           # one caption line (12/16)
