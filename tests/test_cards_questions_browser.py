"""Goal 171 L3, on the `gui` fixture's real host (`?table=cards`, no `?mock=1`, nothing laid by hand): every question's way the hand deals is one press. A goal that asks, a goal at Talk whose
leader asks the person (the keeper's record holds the card, the page does not yet), a bug's cause and a party's own question each deal a turn card; pressing a way sends `ideas.answer_way`
(the answer lands under its question, no keeper or model is reached) and its Undo puts the pages back byte for byte; no request of the hand's ways is `ideas.talk_answer`, `ideas.answer` or
`ideas.cause_answer`, and the old Needs you card of those questions is not dealt."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser

HEAD = "---\nowner: board\nkind: idea\ntrack: tech\norder: {n}\nphase: {phase}\nroute: tech\nasks: person\nschema: 3\n---\n# {title}\n\n## Gist\nA goal.\n"
OLD = ("ideas.talk_answer", "ideas.answer", "ideas.cause_answer")
ENTRIES = ("ask", "call", "work_call", "_claude", "_claude_work", "board_ask", "read_now", "draft", "answer", "read_goal", "talk_answer", "cause_answer", "objection_answer", "_go_on", "_finish")


def lay(server):
    from orkboard.realm import goal_phase, idea_questions, ideas
    host = server.host.ideas
    root, state = host.root(), host.state_dir
    if not ideas.track_page(root, "tech"):
        ideas.add_track(root, "Tech")
    folder = root / ideas.IDEAS
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plain.md").write_text(HEAD.format(n=1, phase="spec", title="Plain goal") + "\n## Open questions\n- Which store first? (**App Store** / Google Play) — most users\n", encoding="utf-8")
    (folder / "talky.md").write_text(HEAD.format(n=2, phase="talk", title="Talky goal"), encoding="utf-8")
    (folder / "buggy.md").write_text(HEAD.format(n=3, phase="talk", title="Buggy goal"), encoding="utf-8")
    for slug in ("plain", "talky", "buggy"):
        ideas.save_state(state, slug, state="raw")
    ideas.save_state(state, "talky", state="talk")
    ideas.save_state(state, "buggy", state="talk")
    card = idea_questions.card({"q": "Keep the timer in the corner?", "choices": ["Keep it", "Move it"], "pick": 0, "why": "less to learn"}, id="r1-tech-0", by="tech", leader="Tech")
    idea_questions.save_record(state, "talky", {"mode": "talk", "round": 1, "stances": [], "waiting": [card]})
    case = idea_questions.card({"q": "Does it happen offline?", "choices": ["Yes", "No"], "pick": 1, "why": ""}, id="r1-tech-1", by="tech", leader="Tech")
    idea_questions.save_record(state, "buggy", {"mode": "bug", "round": 1, "stances": [], "waiting": [case], "cause": {"text": "the cache is stale", "where": [], "pending": True, "guesses": 1}})
    track = ideas.track_page(root, "tech")
    track.set_section("Open questions", "- Ship the app first? (**Yes** / Later) — it is ready", ideas.TRACK_SECTIONS)
    ideas._write(root / ideas.TRACKS / "tech.md", track.text())
    ideas.save_goal_state(state, "tech", state="asks")
    goal_phase.mirror(root, state, lambda i, st, plan, asks: host._idea_needs(i, st, plan, asks, root))      # the host's own keys are written before the person plays: the pages are as they will lie
    return host


def files(host):
    from orkboard.core import idea_undo
    return {s: idea_undo.snapshot(host.root(), host.state_dir, s) for s in ("plain", "talky", "buggy")} | {"tech": idea_undo.snapshot(host.root(), host.state_dir, "tech", True)}


def test_every_question_deals_a_turn_card_whose_way_is_one_press_with_its_undo_and_no_pass(gui, monkeypatch):
    from orkboard.core import idea_undo
    from orkboard.realm import harnesses
    server, browser = gui
    host = lay(server)
    reached: list[str] = []

    def boom(entry):
        def fail(*a, **k):
            reached.append(entry)
            raise AssertionError(f"a model or a pass was reached through {entry}")
        return fail
    for entry in ENTRIES:
        if hasattr(host.keeper, entry):
            monkeypatch.setattr(host.keeper, entry, boom(f"keeper.{entry}"))
    monkeypatch.setattr(harnesses.Harness, "call", boom("Harness.call"))

    pg = browser.new_page(viewport={"width": 1440, "height": 900})
    sent: list[dict] = []

    def on_ws(ws):
        def frame(payload):
            try:
                row = json.loads(payload if isinstance(payload, str) else payload.decode())
            except (ValueError, AttributeError):
                return
            if isinstance(row, dict) and row.get("t") == "cmd":
                sent.append({"name": row["name"], "args": row["args"]})
        ws.on("framesent", frame)
    pg.on("websocket", on_ws)
    pg.goto(server.url + ("&" if "?" in server.url else "?") + "table=cards")
    pg.wait_for_selector(".cards-lane", timeout=WAIT_MS)
    hand = ".frame-hand button.hand-card"
    card = lambda goal: f"{hand}[data-key='turn/{goal}/asks']"      # noqa: E731  (a party's card has no goal of its own: its key names it)
    for goal in ("plain", "talky", "buggy", "tech"):                  # each question is its turn card, and only that: the old card is not dealt
        pg.locator(card(goal)).first.wait_for(timeout=WAIT_MS)
    assert pg.locator(f"{hand}[data-kind=talk], {hand}[data-kind=asks], {hand}[data-kind=goal], {hand}[data-kind=cause]").count() == 0

    wanted = {"plain": ["Google Play"], "talky": ["Move it"], "buggy": ["Yes", "Yes, that is the cause"], "tech": ["Later"]}
    for goal, answers in wanted.items():
        before = files(host)
        pg.locator(card(goal)).first.click(timeout=WAIT_MS)
        for a in answers:
            pg.locator(".hand-ways-row").get_by_text(a, exact=True).first.click(timeout=WAIT_MS)
        for _ in range(100):                                                          # an earlier toast may still lie there: wait for the command itself
            if any(x["name"] == "ideas.answer_way" and x["args"]["slug"] == goal for x in sent):
                break
            pg.wait_for_timeout(100)
        pg.wait_for_timeout(300)
        moves = [s for s in sent if s["name"] == "ideas.answer_way" and s["args"]["slug"] == goal]
        assert moves and moves[-1]["args"]["answers"] == answers and moves[-1]["args"]["from"] == "hand", moves
        assert (moves[-1]["args"].get("party") is True) == (goal == "tech")
        now = files(host)
        assert now[goal] != before[goal]                                              # the answer lies under its question
        assert answers[-1] in now[goal]["page"] and "Answered" in now[goal]["page"], now[goal]["page"]
        kept = idea_undo.read(host.state_dir, goal, goal == "tech")["before"]          # the host's own bookkeeping may touch a goal's state between: the page is what the person wrote
        assert "Answered" not in kept["page"]
        pg.locator(".gui-toast", has_text="Sent:").first.get_by_role("button", name="Undo").click(timeout=WAIT_MS)
        for _ in range(100):                                                          # the toast of an earlier Undo may still lie there: wait for the page itself
            if "Answered" not in files(host)[goal]["page"]:
                break
            pg.wait_for_timeout(100)
        assert files(host)[goal]["page"] == kept["page"], files(host)[goal]["page"]      # byte for byte
        pg.locator(card(goal)).first.wait_for(timeout=WAIT_MS)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)
    assert reached == []
    assert not [s for s in sent if s["name"] in OLD], [s for s in sent if s["name"] in OLD]
    pg.close()
