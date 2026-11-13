"""Spec 34 on the host: a goal by dialog and read at once, an idea read now or later, the keeper's priority and place,
the agents' roles and the task types, each with its event. The model call is stubbed (`jobs.run_read`)."""
from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, goal_team, idea_photos, ideas, jobs, roles

NEW_COMMANDS = {"ideas.goal_save", "ideas.goal", "ideas.read_now", "ideas.roles", "ideas.role_save", "ideas.role_drop",
                "ideas.kind_set", "ideas.doc"}
GOAL = {"title": "Grow installs", "about": "More people try Orkline.", "priority": "high", "deadline": "2026-12-01",
        "metrics": [{"name": "weekly installs", "target": "50"}, {"name": "", "target": "x"}],
        "links": ["docs/specs/34-v1-round-2.md", "https://example.com/post", "docs/specs/34-v1-round-2.md"]}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def model(monkeypatch):
    """A stubbed keeper: answers by what it is asked; `seen` holds every call."""
    seen = []
    answers = {"goal": {"summary": "Installs are the first step.\nCount them weekly.", "questions": ["Which channel first?"],
                        "reply": "Noted."},
               "idea": {"gist": "Dark mode.\nIt glares at night.", "why": "Moves weekly installs.", "size": "S",
                        "priority": "high", "priority_why": "Helps night users stay.", "before": "", "questions": []}}

    def run_read(harness, prompt, workdir, cancel, model="", env=None, resume="", timeout_s=0, **kw):
        kind = "goal" if "saved a goal" in prompt else "idea"
        seen.append({"kind": kind, "model": model, "prompt": prompt, "env": env})
        return json.dumps(answers[kind]), 0.01, 10, "s-1"

    monkeypatch.setattr(jobs, "run_read", run_read)
    run_read.seen, run_read.answers = seen, answers
    return run_read


def _add(host, text, **more):
    """An idea under a goal (spec 35 §3: no idea without one), waiting for the night unless asked."""
    root = host.ideas.root()
    goal = next((t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != "general"), None) or ideas.add_track(root, "First goal")
    return host.command("ideas.add", {"text": text, "track": goal, "hold": True, **more})


def _wait(host, slug="", goal=False):
    k = host.ideas.keeper
    for _ in range(400):
        if not (k.busy_goal(slug) if goal else k.busy(slug)):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _events(host, name):
    return [r for r in event_log.read(Path(host.town.repo_root)) if r["event"] == name]


def test_a_goal_saved_is_read_by_the_keeper_at_once_and_written(host, model):
    slug = host.command("ideas.goal_save", GOAL)["slug"]
    assert slug == "grow-installs"
    _wait(host, slug, goal=True)
    (call,) = model.seen
    assert call["model"] == "opus" or "opus" in call["model"]                     # spec 35 §1: the goal step is elder
    assert "More people try Orkline." in call["prompt"] and "weekly installs" in call["prompt"]
    assert "The metrics the person set" in call["prompt"] and '"metrics"' not in call["prompt"]       # spec 50 §2.5: the metrics of before are passed on, none asked
    assert "Write the specs" in call["prompt"] or "34-v1-round-2" in call["prompt"]            # a linked file is read …
    assert "https://example.com/post (a web link: not fetched)" in call["prompt"]            # … a URL only named
    g = host.command("ideas.goal", {"slug": slug})
    assert g["state"] == "asks" and g["priority"] == "high" and g["deadline"] == "2026-12-01"
    assert g["summary"].startswith("Installs are the first step.") and g["questions"] == ["Which channel first?"]
    assert g["metrics"] == [{"name": "weekly installs", "target": "50", "how": ""}]               # as the person wrote them
    assert g["links"] == ["docs/specs/34-v1-round-2.md", "https://example.com/post"] and g["description"] == "More people try Orkline."
    text = (host.ideas.root() / "pages/tracks/grow-installs.md").read_text()      # spec 35 §13: the Board's tree
    assert "priority: high" in text and "## Summary" in text and "## Metrics" in text and "## Open questions" in text
    board = host.command("ideas.board")
    row = next(t for t in board["tracks"] if t["slug"] == slug)
    assert row["state"] == "asks" and row["priority"] == "high" and row["metrics"] and row["links"]
    assert {"idea": "", "goal": slug, "kind": "goal", "title": "Grow installs", "text": "Which channel first?"} in [
        {k: n[k] for k in ("idea", "goal", "kind", "title", "text")} for n in board["needs_you"]]     # spec 35 §10
    saved = _events(host, "goal_saved")[0]
    assert saved["goal"] == slug and saved["new"] is True and saved["priority"] == "high" and saved["device"] == "desktop"
    assert saved["metrics"] == ["weekly installs"] and len(saved["links"]) == 2
    read = _events(host, "goal_read")[0]
    assert read["goal"] == slug and read["state"] == "asks" and read["seconds"] is not None


def test_editing_a_goal_sends_it_again_and_keeps_what_the_keeper_wrote(host, model):
    slug = host.command("ideas.goal_save", GOAL)["slug"]
    _wait(host, slug, goal=True)
    model.answers["goal"] = {"summary": "Second reading.", "questions": [], "metrics": [{"name": "an answer's own", "target": "9", "how": "counted"}]}
    host.command("ideas.goal_save", {**GOAL, "slug": slug, "title": "Grow installs fast", "priority": "low"})
    _wait(host, slug, goal=True)
    assert len(model.seen) == 2
    g = host.command("ideas.goal", {"slug": slug})
    assert g["state"] == "ready" and g["summary"] == "Second reading." and g["title"] == "Grow installs fast"
    assert g["metrics"] == [{"name": "weekly installs", "target": "50", "how": ""}]      # spec 50 §2.5: a metric in the answer is not read; those of before stay as written
    assert [e["new"] for e in _events(host, "goal_saved")] == [True, False]


def test_the_answer_to_a_goals_question_is_the_same_talk_on_the_goal(host, model):
    slug = host.command("ideas.goal_save", GOAL)["slug"]
    _wait(host, slug, goal=True)
    model.answers["goal"] = {"summary": "Clear now.", "questions": [], "reply": "Thanks, npm first."}
    assert host.command("ideas.say", {"slug": slug, "text": "npm first"}) == {"ok": True}
    _wait(host, slug, goal=True)
    g = host.command("ideas.goal", {"slug": slug})
    assert g["state"] == "ready" and [(t["who"], t["text"]) for t in g["talk"]] == [("you", "npm first"), ("keeper", "Thanks, npm first.")]
    assert "npm first" in model.seen[-1]["prompt"]


def test_an_idea_added_now_is_read_at_once_later_waits_for_the_batch(host, model):
    # spec 35 §3: `now` became the queue (the closed dialog's goal is held, spec 83); spec 99 §4: a goal sent makes no call, it waits as `routed` until Talk
    # (until part D lands Talk reads it as before); with no question the plan follows at once (this stub answers it with no plan, so the idea stays ready)
    later = _add(host, "wait for the batch")["slug"]
    now = _add(host, "dark mode please", hold=False)["slug"]
    assert model.seen == [] and ideas.state(host.ideas.state_dir, now)["state"] == "routed"
    ideas.save_state(host.ideas.state_dir, now, state="raw", queue="now")                # Talk is part D's (tests/test_idea_talk.py): this test is of the draft
    host.ideas.keeper.draft(now)
    _wait(host, now)
    assert [c["kind"] for c in model.seen][:1] == ["idea"] and "dark mode please" in model.seen[0]["prompt"]
    assert ideas.state(host.ideas.state_dir, later)["state"] == "raw"
    assert ideas.state(host.ideas.state_dir, now)["state"] == "ready"
    assert [e["now"] for e in _events(host, "idea_added")] == [False, True]
    seen = len(model.seen)
    host.command("ideas.read_now", {"slug": later})                      # the card's Process now
    _wait(host, later)
    assert len(model.seen) > seen and ideas.state(host.ideas.state_dir, later)["state"] == "ready"
    with pytest.raises(CommandError, match="read this goal already"):
        host.command("ideas.read_now", {"slug": later})


def test_the_persons_drag_wins_over_the_keepers_place(host, model):
    a = _add(host, "alpha idea")["slug"]
    b = _add(host, "beta idea")["slug"]
    host.command("ideas.move", {"slug": b})                              # the person drags b to the end: theirs now
    model.answers["idea"]["before"] = a
    host.command("ideas.read_now", {"slug": b})
    _wait(host, b)
    assert [i["slug"] for i in host.command("ideas.board")["ideas"]] == [a, b]


def test_roles_are_made_edited_dropped_and_the_built_ins_refused(host):
    got = host.command("ideas.roles")
    assert [r["slug"] for r in got["roles"]] == ["taskmaster", "grunt"] and all(r["spend_today"] == 0 for r in got["roles"])
    assert [(k["kind"], k["label"], k["role"]) for k in got["kinds"]][:5] == [
        ("code", "Code", "grunt"), ("tests", "Tests", "grunt"), ("docs", "Docs", "grunt"),
        ("text", "Text for people", "grunt"), ("research", "Research", "grunt")]
    assert [k["kind"] for k in got["kinds"]] == list(roles.TASK_KINDS) and all(k["role"] == "grunt" for k in got["kinds"])
    assert [m["id"] for m in got["models"]] == ["", "elder", "warrior", "laborer"]      # spec 36 §3: By Target, the tiers
    slug = host.command("ideas.role_save", {"name": "Docs scribe", "model": "laborer", "max_parallel": 2,
                                            "instruction": "Write plainly."})["slug"]
    assert host.command("ideas.kind_set", {"kind": "docs", "role": slug}) == {"ok": True}
    got = host.command("ideas.roles")
    assert next(r for r in got["roles"] if r["slug"] == slug)["instruction"] == "Write plainly."
    assert next(k for k in got["kinds"] if k["kind"] == "docs")["role"] == slug
    host.command("ideas.role_save", {"slug": slug, "name": "Scribe", "model": "warrior", "max_parallel": 3, "instruction": ""})
    assert next(r for r in host.command("ideas.roles")["roles"] if r["slug"] == slug)["name"] == "Scribe"
    for slug_ in ("taskmaster", "grunt"):
        with pytest.raises(CommandError, match="edited, not deleted"):
            host.command("ideas.role_drop", {"slug": slug_})
    with pytest.raises(CommandError, match="at once"):
        host.command("ideas.role_save", {"name": "Bad", "model": "warrior", "max_parallel": 99})
    assert host.command("ideas.role_drop", {"slug": slug}) == {"ok": True}
    assert next(k for k in host.command("ideas.roles")["kinds"] if k["kind"] == "docs")["role"] == "grunt"
    saved, dropped, kind = (_events(host, n) for n in ("role_saved", "role_dropped", "kind_set"))
    assert [(e["role"], e["model"], e["max_parallel"], e["new"]) for e in saved] == [
        (slug, "laborer", 2, True), (slug, "warrior", 3, False)]
    assert dropped[0]["role"] == slug and dropped[0]["kinds"] == ["docs"] and kind[0]["kind"] == "docs"


def test_a_linked_document_is_read_from_the_repository_or_the_wiki_only(host):
    repo = Path(host.town.repo_root)
    (repo / "notes.md").write_text("# Notes\nhello\n")
    assert host.command("ideas.doc", {"path": "notes.md"}) == {"path": "notes.md", "text": "# Notes\nhello\n", "truncated": False,
                                                              "html": "<h1>Notes</h1>\n<p>hello</p>\n"}   # spec 37 §8
    slug = _add(host, "an idea")["slug"]
    assert "an idea" in host.command("ideas.doc", {"path": f"pages/ideas/{slug}.md"})["text"]       # a Wiki page
    for bad in ("../outside.md", "/etc/passwd", "nope.md", "https://example.com/x"):
        with pytest.raises(CommandError):
            host.command("ideas.doc", {"path": bad})


def test_a_goal_has_a_craft_its_race_s_head_engineering_when_new_and_kept_when_left_out(host, model):
    """A goal's craft (decisions §53): the person's pick on the phone, its race beside it; engineering by default, an
    unknown one refused, and an edit that leaves it out keeps it (the desktop's dialog does not send it)."""
    slug = host.command("ideas.goal_save", {"about": "A landing page that sells.", "craft": "design"})["slug"]
    _wait(host, slug, goal=True)
    g = next(t for t in host.command("ideas.board", {})["tracks"] if t["slug"] == slug)
    assert (g["craft"], g["race"]) == ("design", "elf")
    host.command("ideas.goal_save", {"slug": slug, "about": "A landing page that sells well."})
    _wait(host, slug, goal=True)
    assert next(t for t in host.command("ideas.board", {})["tracks"] if t["slug"] == slug)["craft"] == "design"
    plain = host.command("ideas.goal_save", {"about": "Faster tests."})["slug"]
    _wait(host, plain, goal=True)
    g = next(t for t in host.command("ideas.board", {})["tracks"] if t["slug"] == plain)
    assert (g["craft"], g["race"]) == ("engineering", "peon")
    with pytest.raises(CommandError, match="Craft is"):
        host.command("ideas.goal_save", {"slug": plain, "about": "Faster tests.", "craft": "alchemy"})
    assert ideas.CRAFTS == roles.CRAFTS


PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32).decode()
JPEG = base64.b64encode(b"\xff\xd8\xff\xe0" + b"\x00" * 32).decode()


def test_photos_go_with_an_idea_beside_its_state_and_the_taskmaster_reads_them_first(host, model):
    """New idea's photos (realm/idea_photos.py): kept in the idea's state folder, named in the draft's and the plan's
    prompts as paths in the repository; a bad one refuses the idea whole, and deleting the idea deletes them."""
    root = host.ideas.root()
    goal = ideas.add_track(root, "Ship v1")
    for bad, why in (([{"data": base64.b64encode(b"not an image").decode()}], "JPEG, a PNG or a WebP"),
                     ([{"data": "@@@"}], "did not arrive whole"), ([{"data": JPEG}] * 5, "At most 4 photos")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.add", {"text": "Cut off", "track": goal, "hold": True, "photos": bad})
    assert ideas.ideas(root, goal) == []                                                     # nothing half made
    slug = host.command("ideas.add", {"text": "The login screen is cut off", "track": goal, "hold": True,
                                      "photos": [{"data": JPEG}, {"data": PNG}]})["slug"]
    assert idea_photos.listed(host.ideas.state_dir, slug) == [f".orkcraft/ideas/{slug}/photos/1.jpg", f".orkcraft/ideas/{slug}/photos/2.png"]
    assert (idea_photos.folder(host.ideas.state_dir, slug) / "1.jpg").read_bytes()[:3] == b"\xff\xd8\xff"
    prompt = host.ideas.keeper.draft_prompt(root, slug)
    assert "read each one first" in prompt and f"- .orkcraft/ideas/{slug}/photos/2.png" in prompt
    assert f".orkcraft/ideas/{slug}/photos/1.jpg" in host.ideas.keeper.plan_prompt(root, slug)
    assert _events(host, "idea_added")[-1]["photos"] == 2
    host.command("ideas.drop", {"slug": slug})
    assert idea_photos.listed(host.ideas.state_dir, slug) == []


def test_needs_you_carries_every_question_with_its_likely_answers_and_one_answered_on_the_phone_leaves_the_rest_to_decide(host, model):
    """The phone answers a question in its card: the row carries the questions, the Taskmaster is asked to end
    each with its likely answers "(one / other)", and a goal's answers may be fewer than its questions."""
    model.answers["goal"] = {"summary": "Installs first.", "questions": ["Which channel first? (npm / brew)", "Which week?"], "metrics": []}
    slug = host.command("ideas.goal_save", GOAL)["slug"]
    _wait(host, slug, goal=True)
    assert '"choices": ["two to four likely answers, each at most 40 characters"]' in model.seen[0]["prompt"]
    row = next(n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "goal")
    assert row["questions"] == ["Which channel first? (npm / brew)", "Which week?"] and row["text"] == "Which channel first?"
    assert row["asked"] == [{"ask": "Which channel first?", "choices": ["npm", "brew"], "pick": None, "why": "", "kinds": ["other", "other"]},
                            {"ask": "Which week?", "choices": [], "pick": None, "why": ""}]     # a plain string of before
    host.command("ideas.answer", {"slug": slug, "answers": ["npm"], "goal": True})
    _wait(host, slug, goal=True)
    said = model.seen[-1]["prompt"]
    assert "Which channel first? (npm / brew) — npm" in said and "Which week? — (no answer: decide)" in said


# -- spec 99 A: parties by craft ---------------------------------------------------------------------------------------------------------------------------------


def test_a_squad_of_seven_seats_is_kept_whole_with_a_size_and_an_eighth_is_refused(host):
    six = ["grunt", "tester", "artist", "seo", "aso", "reviewer"]
    slug = host.command("ideas.goal_save", {"title": "Tech", "about": "Code.", "leader": "architect", "size": "lean", "proposal": "tech", "team": six})["slug"]
    assert goal_team.team_of(host.ideas.root(), slug) == six                                                       # six besides the leader: seven seats
    with pytest.raises(CommandError, match="at most 7 seats"):
        host.command("ideas.goal_save", {"slug": slug, "team": [*six, "editor"], "leader": "architect"})


def test_release_reads_when_there_is_a_release_not_at_start(host, model, monkeypatch):
    """Spec 143 E.1: a party of Release is not read at its save (Tech's is); it reads once when its lens is opened (a goal ready for main no longer wakes it: decisions §283.29)."""
    tech = host.command("ideas.goal_save", {"about": "Faster tests.", "proposal": "tech"})["slug"]
    rel = host.command("ideas.goal_save", {"about": "A version goes out.", "proposal": "release"})["slug"]
    _wait(host, tech, goal=True)
    _wait(host, rel, goal=True)
    assert len(model.seen) == 1 and "Faster tests" in model.seen[0]["prompt"], "Tech's reading is asked for, Release's is not"
    assert ideas.goal_state(host.ideas.state_dir, rel)["state"] == "raw" and ideas.goal_state(host.ideas.state_dir, tech)["state"] != "raw"
    host.command("ideas.goal_save", {"slug": rel, "about": "A version goes out, with notes."})
    _wait(host, rel, goal=True)
    assert len(model.seen) == 1, "a save of the Release party reads nothing either"
    from orkboard.realm import idea_gate
    monkeypatch.setattr(idea_gate, "same", lambda a, b: False)
    monkeypatch.setattr(idea_gate, "waiting_by_patch", lambda g, a, b: (["abc"], 1))
    monkeypatch.setattr(host.ideas, "_gate_ideas", lambda shas: [{"slug": "x", "title": "X", "goal": tech, "tasks": 1}])
    host.command("ideas.gate", {})
    _wait(host, rel, goal=True)
    assert len(model.seen) == 1, "a goal ready for main: Release waits (decisions §283.29, which changes spec 143 E.1), it reads nothing"
    host.command("ideas.lens", {"track": rel})
    _wait(host, rel, goal=True)
    assert len(model.seen) == 2 and "A version goes out" in model.seen[1]["prompt"], "its lens still reads it, once"
    host.command("ideas.gate", {})
    host.command("ideas.lens", {"track": rel})
    _wait(host, rel, goal=True)
    assert len(model.seen) == 2, "once: a reading kept is not read again"


