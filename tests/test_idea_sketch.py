"""Spec 121 A (docs/specs/121-the-day-the-morning-and-the-night.md §2, §9) on the keeper and the host: a goal that is seen or heard is sketched in place of its sections (the state `sketch`, then `sections` once one
is picked or none is wanted) — which goals (each craft, a goal type, the short way and a pitch none, a project with nothing to sketch from none, the person's own word either way), the page's call (the party's
tier, no tools, the one picture of the screen), a page kept as a pick `sketch-r<round>` and never in the project's tree, Art's pick task only with the media tools and a paid tool only with the person's yes,
the answers (pick, again at most three rounds, no sketch), the sections given the sketch picked, the brief naming its path, the cost in the goal's ledger, the events. The model call is stubbed
(`keeper.call`, and `keeper.work_call` for Art), as in tests/test_idea_decide.py."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from orkboard.gui.board_host import CommandError
from orkboard.realm import event_log, idea_pick, idea_spend, idea_target, ideas, paid, sketches, task_brief
from tests import pick_files as pf
from tests.test_idea_decide import DECISION, Model, _decided, _party, _row, _state, _until, host, model  # noqa: F401  (the fixtures and the helpers of the decision's tests)

PAGE = "<!doctype html><html><head><style>body{margin:0}</style></head><body><button onclick=\"this.textContent='Done'\">Press</button></body></html>"
PAGES = {"variants": [{"name": "Quiet", "why": "A calm list", "html": PAGE}, {"name": "Loud", "why": "Everything at once", "html": PAGE + "<!-- loud -->"},
                      {"name": "Plain", "why": "Words only", "html": PAGE + "<!-- plain -->"}]}


@pytest.fixture
def parties(host):
    return {"product": _party(host, "Product", "product-manager", ["copywriter"], "product"), "design": _party(host, "Design", "product-designer", ["artist", "ui-kit"], "design"),
            "tech": _party(host, "Tech", "architect", ["grunt", "tester"], "engineering"), "art": _party(host, "Art", "art-director", ["artist"], "design"),
            "game": _party(host, "Game design", "game-designer", [], "product")}


@pytest.fixture
def looked(host):
    """The project has a look to sketch from (a stylesheet): the ground of a sketch."""
    (Path(host.repo_root) / "styles.css").write_text("body { background: #101010; color: #eee; font-family: monospace; }\n", encoding="utf-8")


def _events(host, name):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


def _record(host, slug):
    return sketches.record(host.ideas.state_dir, slug)


def _sections(host):
    """The sections stubbed: the goal only reaches `sections`, as Confirm and start leaves it; `seen` is `[(slug, state)]`."""
    seen = []
    host.ideas.keeper.sections = lambda s: seen.append((s, _state(host, s)["state"]))
    return seen


def _settle(host, slug, status="asked", seconds=10):
    for _ in range(int(seconds * 100)):
        if _record(host, slug).get("status") == status and not host.ideas.keeper.busy(slug):
            return _record(host, slug)
        time.sleep(0.01)
    raise AssertionError(f"the sketch never reached {status}: {_record(host, slug)} {_state(host, slug)}")


def _confirmed(host, parties, model, which=("design",), text="add a settings screen", said=PAGES):
    """A goal sent to Talk, decided and confirmed: the sections stubbed. `(slug, [(goal, state) the sections were asked in])`."""
    model.said[("sketch", "")] = said
    slug = _decided(host, parties, model, which, text)
    seen = _sections(host)
    host.command("ideas.confirm", {"idea": slug})
    return slug, seen


def _sketched(host, parties, model, **kw):
    slug, seen = _confirmed(host, parties, model, **kw)
    _settle(host, slug)
    return slug, seen


def _pick(host, slug, **args):
    return host.command("ideas.pick", {"slug": slug, "task": "sketch", **args})


# -- in place of the sections --------------------------------------------------------------------------------------------------------------

def test_a_goal_with_design_on_its_route_is_sketched_in_place_of_its_sections(host, parties, model, looked):
    slug, seen = _confirmed(host, parties, model)
    assert _state(host, slug)["state"] == "sketch" and seen == []                                         # the sketch, not the sections
    rec = _settle(host, slug)
    assert (rec["craft"], rec["party"], rec["leader"], rec["kind"], rec["round"]) == ("design", parties["design"], "product-designer", "page", 1)
    assert _state(host, slug)["state"] == "sketch" and seen == [] and rec["status"] == "asked"            # the person has not answered: nothing else begins
    assert rec["ask"].startswith("add a settings screen")


def test_a_goal_with_no_craft_that_sketches_goes_straight_to_its_sections(host, parties, model, looked):
    slug, seen = _confirmed(host, parties, model, which=("tech",), text="move the cache to the server")
    assert seen == [(slug, "sections")] and model.steps("sketch") == [] and _record(host, slug) == {}
    assert _events(host, event_log.SKETCH_SKIPPED) == []                                                   # none was wanted, none was skipped


def test_a_goal_type_that_is_seen_names_the_projects_design_when_the_route_has_none(host, parties, model, looked):
    slug, seen = _confirmed(host, parties, model, which=("tech",), text="a new screen for the settings")
    rec = _settle(host, slug)
    assert rec["craft"] == "design" and rec["party"] == parties["design"] and seen == []


def test_a_project_with_nothing_to_sketch_from_gets_no_sketch(host, parties, model):
    slug, seen = _confirmed(host, parties, model)                                                          # no look, no screens, no preview, no assets
    assert seen == [(slug, "sections")] and model.steps("sketch") == [] and _record(host, slug) == {}


def test_a_project_with_a_look_screens_a_preview_or_assets_has_something_to_sketch_from(host, tmp_path):
    keeper = host.ideas.keeper
    assert keeper.sketch_ground() is False
    (Path(host.repo_root) / "index.html").write_text("<!doctype html><title>x</title>", encoding="utf-8")        # a static preview
    assert keeper.sketch_ground() is True
    (Path(host.repo_root) / "index.html").unlink()
    assert keeper.sketch_ground() is False
    (Path(host.repo_root) / "tokens.css").write_text(":root{--ink:#111}", encoding="utf-8")
    assert keeper.sketch_ground() is True


def test_the_person_asks_for_a_sketch_on_any_goal_and_turns_it_off_for_one(host, parties, model):
    model.said[("sketch", "")] = PAGES
    slug = _decided(host, parties, model, ("tech",), "move the cache to the server")                       # no ground, no craft: none by rule
    host.command("ideas.sketch_now", {"idea": slug})                                                       # *Sketch it first*
    assert _record(host, slug)["prefer"] == "yes"
    seen = _sections(host)
    host.command("ideas.confirm", {"idea": slug})
    rec = _settle(host, slug)
    assert rec["craft"] == "design" and seen == [] and _state(host, slug)["state"] == "sketch"            # the project's Design, though nothing routes to it
    other = _decided(host, parties, model, ("design",), "add another settings screen")
    host.command("ideas.sketch_skip", {"idea": other})                                                     # *No sketch*
    seen = _sections(host)
    (Path(host.repo_root) / "styles.css").write_text("body{}", encoding="utf-8")
    host.command("ideas.confirm", {"idea": other})
    assert seen == [(other, "sections")] and _record(host, other)["prefer"] == "no" and len(model.steps("sketch")) == 1


def test_a_goal_whose_spec_is_written_cannot_be_asked_a_sketch_for_and_a_goal_gone_is_refused(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model)
    with pytest.raises(CommandError, match="It is being sketched"):
        host.command("ideas.sketch_now", {"idea": slug})
    _pick(host, slug, key="A")
    with pytest.raises(CommandError, match="Its spec is written already"):
        host.command("ideas.sketch_now", {"idea": slug})
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.sketch_now", {"idea": "nobody"})


def test_the_short_way_is_never_sketched_by_rule(host, parties, model, looked):
    keeper = host.ideas.keeper
    slug = host.command("ideas.add", {"text": "add a settings screen", "track": parties["design"]})["slug"]
    host.command("ideas.route_set", {"idea": slug, "route": [parties["design"]]})
    assert keeper.sketch_for(slug)["craft"] == "design"
    st = _state(host, slug)
    ideas.save_state(host.ideas.state_dir, slug, route_how={**st["route_how"], "short": True})
    assert keeper.sketch_for(slug) is None
    ideas.save_state(host.ideas.state_dir, slug, route_how={**st["route_how"], "short": False, "kind": "bug"})
    assert keeper.sketch_for(slug) is None


# -- the page's call -----------------------------------------------------------------------------------------------------------------------

def test_the_page_is_one_call_on_the_partys_tier_with_no_tools_and_no_read(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model)
    (call,) = model.steps("sketch")
    assert call["tools"] is False and call["party"] == parties["design"]
    assert (call["tier"], call["effort"]) == idea_target.pick("sketch", "balance") == ("elder", "medium")
    assert idea_target.pick("sketch", "thrift") == ("warrior", "low") and idea_target.pick("sketch", "quality") == ("elder", "high")
    assert "You are" in call["prompt"] and "speak for Design" in call["prompt"] and "Read no file" in call["prompt"]                 # its voice, then its party's words
    assert idea_target.READS["sketch"] == 0 and idea_target.reads_of("sketch", "design") == 1 and idea_target.CONTEXT["sketch"] > 0 and idea_target.CAPS["sketch"] > 0
    assert _state(host, slug)["measure"]["step"] == "sketch" and _state(host, slug)["measure"]["cost"] == 0.01


def test_the_leader_is_given_the_goal_the_decision_the_answers_and_the_projects_look(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model, text="add a settings screen with a dark mode switch")
    prompt = model.steps("sketch")[0]["prompt"]
    assert "add a settings screen with a dark mode switch" in prompt and DECISION["why"][:20] in prompt                                    # the goal, and what was decided
    assert "/* styles.css */" in prompt and "background: #101010" in prompt                                                              # the look, named by its file
    assert "2 to 3 throwaway variants" in prompt and "<!doctype html>" in prompt and f"{sketches.PAGE_KB} KB" in prompt and "no `src`, `href` or `url(`" in prompt
    assert '"variants"' in prompt and "phone's width" in prompt
    assert "The picture of the screen" not in prompt                                                                                     # none is kept


def test_design_reads_the_one_picture_of_the_screen_the_goal_changes_when_one_is_kept(host, parties, model, looked, monkeypatch):
    from orkboard.realm import map_signals
    monkeypatch.setattr(map_signals, "pictures", lambda *a, **k: [{"id": "orders", "name": "Orders", "path": "shots/orders.png", "at": "1"}, {"id": "settings", "name": "Settings", "path": "shots/settings.png", "at": "0"}])
    slug, _seen = _sketched(host, parties, model, text="add a dark mode switch to the settings screen")
    (call,) = model.steps("sketch")
    assert call["tools"] is True and "The picture of the screen this goal changes (read it):\nshots/settings.png (Settings)" in call["prompt"]
    assert "Start from these files: shots/settings.png. Read at most 1 files in all" in call["prompt"] and "shots/orders.png" not in call["prompt"]


def test_game_design_sketches_a_loop_on_a_page_with_no_art(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model, which=("game",), text="balance the reward of the first press")
    rec = _record(host, slug)
    assert rec["craft"] == "game-design" and rec["party"] == parties["game"] and rec["kind"] == "page"
    prompt = model.steps("sketch")[0]["prompt"]
    assert "small playable of the step of the loop this goal changes" in prompt and "no art" in prompt and model.steps("sketch")[0]["party"] == parties["game"]


def test_several_crafts_on_the_route_one_sketch_by_the_first(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model, which=("product", "design", "game", "tech"), text="add a settings screen")
    assert len(model.steps("sketch")) == 1 and _record(host, slug)["party"] == parties["design"]


# -- kept as a pick, and never in the project ----------------------------------------------------------------------------------------------

def test_the_pages_are_kept_as_a_pick_beside_the_goal_and_nothing_is_written_to_the_projects_tree(host, parties, model, looked):
    before = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=host.repo_root, capture_output=True, text=True).stdout
    slug, _seen = _sketched(host, parties, model)
    pick = idea_pick.load(host.ideas.state_dir, slug, "sketch-r1")
    assert pick["by"] == "leader" and pick["kind"] == "page" and pick["task"] == "sketch" and pick["round"] == 1 and pick["target"] == ""
    assert [(v["key"], v["name"], v["file"], v["mime"], v["why"]) for v in pick["variants"]] == [
        ("A", "Quiet", "a.html", "text/html", "A calm list"), ("B", "Loud", "b.html", "text/html", "Everything at once"), ("C", "Plain", "c.html", "text/html", "Words only")]
    folder = host.ideas.state_dir / "ideas" / slug / "picks" / "sketch-r1"
    assert (folder / "a.html").read_text(encoding="utf-8") == PAGE and sorted(p.name for p in folder.iterdir()) == ["a.html", "b.html", "c.html", "pick.json"]
    assert not [p for p in (host.ideas.state_dir / "ideas" / slug).iterdir() if p.name.startswith("sketch-")]          # the scratch folder is gone
    after = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=host.repo_root, capture_output=True, text=True).stdout
    state = str(host.ideas.state_dir.relative_to(host.repo_root))
    assert [ln for ln in after.splitlines() if ln not in before.splitlines() and state not in ln and ".html" in ln] == []         # no page in the project's tree
    assert not list(Path(host.repo_root).glob("*.html")) and not list(Path(host.repo_root, "src").glob("*.html"))
    assert subprocess.run(["git", "log", "--all", "--format=%H", "--", "*.html"], cwd=host.repo_root, capture_output=True, text=True).stdout.strip() == ""      # never committed


def test_the_row_a_face_reads_is_a_picks_with_a_pages_url_and_no_inline_text(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model)
    row = _row(host, slug, "pick")
    assert row["sketch"] is True and row["task"] == "sketch" and row["idea"] == slug and row["blocks"] is True and row["media"] == "page" and row["n"] == 3
    assert (row["round"], row["rounds"], row["rounds_left"], row["error"], row["now"]) == (1, 3, 2, "", False)
    assert row["title"].endswith(" sketched it") and row["text"] == row["title"] and row["craft"] == "design" and row["party"] == parties["design"]
    assert row["by"]["slug"] == "product-designer" and row["by"]["name"] and row["by"]["head"]
    assert [(v["key"], v["name"], v["mime"]) for v in row["variants"]] == [("A", "Quiet", "text/html"), ("B", "Loud", "text/html"), ("C", "Plain", "text/html")]
    assert all(v["url"].startswith(f"/media/{slug}/sketch-r1/") and "?s=" in v["url"] and "text" not in v for v in row["variants"])
    board = host.command("ideas.board")
    assert next(i for i in board["ideas"] if i["slug"] == slug)["state"] == "sketch" and "sketching" not in next(i for i in board["ideas"] if i["slug"] == slug)


def test_while_the_sketch_is_made_the_goal_says_who_is_sketching_and_asks_nothing(host, parties, model, looked):
    gate = {}

    def slow(row):
        gate["during"] = (host.command("ideas.board"), host.command("ideas.page", {"slug": slug}))
        return PAGES
    model.said[("sketch", "")] = slow
    slug = _decided(host, parties, model, ("design",), "add a settings screen")
    _sections(host)
    host.command("ideas.confirm", {"idea": slug})
    _settle(host, slug)
    board, page = gate["during"]
    mine = next(i for i in board["ideas"] if i["slug"] == slug)
    assert mine["sketching"] == {"craft": "design", "party": parties["design"], "leader": "product-designer", "name": mine["sketching"]["name"], "round": 1} and mine["sketching"]["name"]
    assert page["sketching"] == mine["sketching"] and not [n for n in board["needs_you"] if n["idea"] == slug and n["kind"] == "pick"]
    assert next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug).get("sketching") is None


# -- a call that keeps to nothing --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("bad", ["not json at all", {"variants": [{"name": "A", "why": "x", "html": PAGE}]}, {"variants": [{"name": "A", "why": "x", "html": PAGE}, {"name": "B", "why": "y", "html": "<div>no page</div>"}]},
                                 {"variants": [{"name": "A", "why": "x", "html": PAGE}, {"name": "B", "why": "y", "html": PAGE.replace("<button", '<img src="https://example.com/a.png"><button')}]}])
def test_an_answer_that_is_no_sketch_is_asked_once_more_then_there_is_no_sketch_and_the_sections_follow(host, parties, model, looked, bad):
    slug, seen = _confirmed(host, parties, model, said=bad)
    _until(host, slug, "sections")
    for _ in range(500):
        if seen:
            break
        time.sleep(0.01)
    assert seen == [(slug, "sections")] and len(model.steps("sketch")) == 2                                 # tried once more
    rec = _record(host, slug)
    assert rec["status"] == "skipped" and rec["answer"] == "skipped" and rec["why"].endswith("did not answer: try again")
    assert any(t["text"].startswith("No sketch: ") for t in ideas.talk(host.ideas.state_dir, slug))
    assert [e["why"] for e in _events(host, event_log.SKETCH_SKIPPED)] == [rec["why"]] and _events(host, event_log.SKETCH_MADE) == []
    assert _row(host, slug, "pick") is None


def test_a_stop_puts_the_goal_back_at_its_decision_and_says_nothing(host, parties, model, looked):
    def stopped(row):
        raise InterruptedError("stopped")
    slug, seen = _confirmed(host, parties, model, said=stopped)
    _until(host, slug, "decided")
    assert seen == [] and _record(host, slug)["status"] == "" and _state(host, slug)["error"] == "" and _events(host, event_log.SKETCH_SKIPPED) == []
    model.said[("sketch", "")] = PAGES                                                                     # *Start* asks again: the decision is written once, the sketch made
    host.command("ideas.confirm", {"idea": slug})
    assert _settle(host, slug)["status"] == "asked" and _row(host, slug, "pick")["sketch"] is True


# -- the answers ----------------------------------------------------------------------------------------------------------------------------

def test_pick_this_one_goes_to_the_sections_and_keeps_what_was_picked(host, parties, model, looked):
    slug, seen = _sketched(host, parties, model)
    got = _pick(host, slug, key="B", note="Keep the big buttons")
    assert got["ok"] is True and got["answer"] == "picked" and got["round"] == 1
    assert seen == [(slug, "sections")] and _state(host, slug)["state"] == "sections"
    rec = _record(host, slug)
    assert rec["status"] == "picked" and rec["picked"] == {"key": "B", "name": "Loud", "why": "Everything at once", "note": "Keep the big buttons", "file": "b.html", "mime": "text/html",
                                                          "kind": "page", "round": 1, "pick": "sketch-r1"}
    pick = idea_pick.load(host.ideas.state_dir, slug, "sketch-r1")
    assert idea_pick.answered(pick) and pick["picked"] == "B" and pick["note"] == "Keep the big buttons"
    (answered,) = _events(host, event_log.SKETCH_ANSWERED)
    assert (answered["idea"], answered["answer"], answered["round"], answered["note_chars"], answered["device"]) == (slug, "picked", 1, len("Keep the big buttons"), "desktop")
    assert "minutes_since_goal" in answered and _row(host, slug, "pick") is None
    with pytest.raises(CommandError, match="There is no sketch to answer now"):
        _pick(host, slug, key="A")


def test_a_letter_that_is_no_variant_and_a_late_answer_are_refused_in_words(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model)
    with pytest.raises(CommandError, match="Pick one of A, B, C"):
        _pick(host, slug, key="Z")
    with pytest.raises(CommandError, match="A note says what to change: write one first"):
        _pick(host, slug, key=None)
    with pytest.raises(CommandError, match="skip and now are on or off"):
        _pick(host, slug, skip="yes")
    assert _record(host, slug)["status"] == "asked" and _events(host, event_log.SKETCH_ANSWERED) == []        # nothing was said answered


def test_sketch_again_with_a_note_is_a_new_round_given_the_note_and_the_variants_before(host, parties, model, looked):
    slug, seen = _sketched(host, parties, model)
    model.said[("sketch", "")] = {"variants": [{"name": "Rounder", "why": "Soft corners", "html": PAGE + "<!-- r2a -->"}, {"name": "Softer", "why": "Quiet colours", "html": PAGE + "<!-- r2b -->"}]}
    got = _pick(host, slug, key=None, note="Rounder corners please")
    assert got["answer"] == "again" and got["round"] == 2
    rec = _settle(host, slug)
    assert rec["round"] == 2 and rec["status"] == "asked" and rec["notes"] == [{"round": 1, "note": "Rounder corners please"}] and seen == []
    prompt = model.steps("sketch")[1]["prompt"]
    assert "The round before, and what the person asks to change" in prompt and "- A · Quiet: A calm list" in prompt and "The person asks: Rounder corners please" in prompt
    assert idea_pick.answered(idea_pick.load(host.ideas.state_dir, slug, "sketch-r1")) and not idea_pick.answered(idea_pick.load(host.ideas.state_dir, slug, "sketch-r2"))
    row = _row(host, slug, "pick")
    assert row["round"] == 2 and row["rounds_left"] == 1 and [v["name"] for v in row["variants"]] == ["Rounder", "Softer"] and row["variants"][0]["url"].startswith(f"/media/{slug}/sketch-r2/")
    assert [e["answer"] for e in _events(host, event_log.SKETCH_ANSWERED)] == ["again"] and [e["round"] for e in _events(host, event_log.SKETCH_MADE)] == [1, 2]
    _pick(host, slug, key="A")
    assert seen == [(slug, "sections")] and _record(host, slug)["picked"]["round"] == 2 and _record(host, slug)["picked"]["pick"] == "sketch-r2"


def test_three_rounds_at_most_the_fourth_is_refused_in_words(host, parties, model, looked):
    slug, seen = _sketched(host, parties, model)
    for n in (1, 2):
        _pick(host, slug, key=None, note=f"again {n}")
        assert _settle(host, slug)["round"] == n + 1
    assert _row(host, slug, "pick")["rounds_left"] == 0
    with pytest.raises(CommandError, match="Three rounds: pick one or go on"):
        _pick(host, slug, key=None, note="once more")
    assert _record(host, slug)["round"] == 3 and _record(host, slug)["status"] == "asked" and len(model.steps("sketch")) == 3 and seen == []        # nothing was made, nothing was answered
    assert not idea_pick.answered(idea_pick.load(host.ideas.state_dir, slug, "sketch-r3"))
    _pick(host, slug, key="C")                                                                             # …and one of the third round can still be picked
    assert seen == [(slug, "sections")] and _record(host, slug)["picked"]["round"] == 3


def test_a_new_round_that_cannot_be_made_opens_the_round_before_again_with_why(host, parties, model, looked):
    slug, seen = _sketched(host, parties, model)
    model.said[("sketch", "")] = "not json"
    _pick(host, slug, key=None, note="Rounder")
    rec = _settle(host, slug)
    assert rec["round"] == 1 and rec["status"] == "asked" and rec["error"].startswith("The new round could not be made: ") and rec["notes"] == [] and seen == []
    assert not idea_pick.answered(idea_pick.load(host.ideas.state_dir, slug, "sketch-r1"))
    row = _row(host, slug, "pick")
    assert row["round"] == 1 and row["rounds_left"] == 2 and row["error"].startswith("The new round could not be made") and _state(host, slug)["state"] == "sketch"
    model.said[("sketch", "")] = PAGES
    _pick(host, slug, key=None, note="Rounder, again")                                                     # the round that failed did not count
    assert _settle(host, slug)["round"] == 2 and _record(host, slug)["error"] == ""


def test_no_sketch_go_on_goes_to_the_sections(host, parties, model, looked):
    slug, seen = _sketched(host, parties, model)
    got = _pick(host, slug, skip=True)
    assert got["answer"] == "skipped" and seen == [(slug, "sections")] and _state(host, slug)["state"] == "sections"
    rec = _record(host, slug)
    assert rec["status"] == "skipped" and rec["why"] == "the person said no" and rec.get("picked") is None and sketches.context(host.ideas.state_dir, slug) == ""
    assert [e["answer"] for e in _events(host, event_log.SKETCH_ANSWERED)] == ["skipped"] and [e["why"] for e in _events(host, event_log.SKETCH_SKIPPED)] == ["the person said no"]
    assert idea_pick.answered(idea_pick.load(host.ideas.state_dir, slug, "sketch-r1")) and _row(host, slug, "pick") is None


def test_ideas_sketch_skip_on_a_goal_being_sketched_is_no_sketch_go_on(host, parties, model, looked):
    slug, seen = _sketched(host, parties, model)
    host.command("ideas.sketch_skip", {"idea": slug})
    assert seen == [(slug, "sections")] and _record(host, slug)["status"] == "skipped"


def test_the_answers_are_a_phones_too(host, parties, model, looked):
    from orkboard.gui.board_host import BoardPhone
    assert {"ideas.sketch_now", "ideas.sketch_skip", "ideas.pick"} <= set(host.commands) and all(BoardPhone.allowed(host, c, {}) for c in ("ideas.sketch_now", "ideas.sketch_skip", "ideas.pick"))
    slug, _seen = _sketched(host, parties, model)
    host.command("ideas.pick", {"slug": slug, "task": "sketch", "key": "A", "device": "phone", "via": "hand"})
    assert _events(host, event_log.SKETCH_ANSWERED)[0]["via"] == "hand"


def test_a_spent_window_or_a_keeper_that_may_not_run_refuses_the_answer_and_loses_nothing(host, parties, model, looked):
    slug, seen = _sketched(host, parties, model)
    keeper = host.ideas.keeper
    keeper.budget_ok = lambda: False
    with pytest.raises(CommandError, match="spend limit"):
        _pick(host, slug, key="A")
    keeper.budget_ok = lambda: True
    assert _record(host, slug)["status"] == "asked" and not idea_pick.answered(idea_pick.load(host.ideas.state_dir, slug, "sketch-r1")) and seen == []
    _pick(host, slug, key="A")
    assert seen == [(slug, "sections")]


def test_pick_and_build_now_keeps_the_press_with_the_goal_and_a_refused_answer_builds_nothing(host, parties, model, looked):
    slug, seen = _sketched(host, parties, model)
    with pytest.raises(CommandError, match="Pick one of"):
        _pick(host, slug, key="Z", now=True)
    assert host.ideas._build_now_of(slug) is None
    _pick(host, slug, key="A", now=True, device="phone")
    assert host.ideas._build_now_of(slug) == {"device": "phone"} and seen == [(slug, "sections")]
    other, _s = _sketched(host, parties, model, text="add another settings screen")
    _pick(host, other, skip=True, now=True)
    assert host.ideas._build_now_of(other) is None                                                         # no sketch, nothing to build now
    third, _s = _sketched(host, parties, model, text="add a third settings screen")
    model.said[("sketch", "")] = PAGES
    _pick(host, third, key=None, note="again", now=True)
    assert host.ideas._build_now_of(third) is None                                                         # another round is no pick


def test_with_work_at_night_on_the_row_offers_pick_and_build_now(host, parties, model, looked):
    host.command("ideas.board_set", {"work_at_night": True})
    slug, _seen = _sketched(host, parties, model)
    assert _row(host, slug, "pick")["now"] is True


# -- the sections and the build rest on the sketch ---------------------------------------------------------------------------------------------

def _entry(host, parties, who="design"):
    return {"party": parties[who], "leader": "product-designer"}


def test_the_sections_are_given_the_sketch_the_person_picked_before_the_map_and_told_to_rest_on_it(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model, which=("design", "tech"))
    keeper = host.ideas.keeper
    route = keeper._route(slug)
    before = keeper.section_prompt(slug, _entry(host, parties), route, True)
    assert "The sketch the person picked" not in before and "A sketch was picked" not in before
    _pick(host, slug, key="B", note="Keep the big buttons")
    prompt = keeper.section_prompt(slug, _entry(host, parties), route, True)
    assert "The sketch the person picked:\nSketch B · Loud — Everything at once\nThe person said: \"Keep the big buttons\"\nIts page (the first 6,000 characters):\n<!doctype html>" in prompt
    assert PAGE + "<!-- loud -->" in prompt and "A sketch was picked (above): the parts it shows are the parts the work changes" in prompt
    other = keeper.section_prompt(slug, {"party": parties["tech"], "leader": "architect"}, route, False)
    assert "The sketch the person picked" in other and "A sketch was picked" in other                      # every leader's section, not Design's alone


def test_a_page_cut_at_six_thousand_characters_in_the_sections_context(host, parties, model, looked):
    big = {"variants": [{"name": "Big", "why": "w", "html": "<!doctype html><body>" + "x" * 9000 + "</body>"}, {"name": "Small", "why": "w", "html": PAGE}]}
    slug, _seen = _sketched(host, parties, model, said=big)
    _pick(host, slug, key="A")
    prompt = host.ideas.keeper.section_prompt(slug, _entry(host, parties), host.ideas.keeper._route(slug), True)
    assert "x" * 5000 in prompt and "x" * 6001 not in prompt and "…" in prompt


def test_a_goal_whose_sketch_was_not_picked_is_given_none(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model)
    _pick(host, slug, skip=True)
    assert "The sketch the person picked" not in host.ideas.keeper.section_prompt(slug, _entry(host, parties), host.ideas.keeper._route(slug), True)


def test_the_builds_brief_names_the_picked_files_path_as_a_reference(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model)
    assert task_brief.sketch_note(host.ideas.state_dir, slug) == ""
    _pick(host, slug, key="A", note="Calm")
    note = task_brief.sketch_note(host.ideas.state_dir, slug)
    path = host.ideas.state_dir / "ideas" / slug / "picks" / "sketch-r1" / "a.html"
    assert note.startswith("# The sketch the person picked\n\n") and f"`{path}`" in note and "A · Quiet" in note and 'The person said: "Calm"' in note
    assert "never copy it into the project" in note and "outside this worktree" in note and "It is a page at" in note
    assert sketches.reference_dirs(host.ideas.state_dir, slug) == (str(path.parent),)


def test_a_task_is_told_of_the_sketch_in_its_prompt_before_its_own_words(host, parties, model, looked):
    from orkboard.core.idea_task import TaskMixin
    slug, _seen = _sketched(host, parties, model)
    _pick(host, slug, key="A")
    runner = SimpleNamespace(repo_root=host.repo_root, state_dir=host.ideas.state_dir, settings={}, _role=lambda t: {"name": "Grunt", "instruction": "", "slug": "grunt"}, _env=lambda *a: {}, _reading=lambda *a: "", _without=lambda *a: [], tool_of=lambda *a: "claude")
    plan = {"tasks": [{"id": "k1", "title": "Build it", "brief": "Make the screen"}]}
    prompt = TaskMixin._prompt(runner, slug, plan, plan["tasks"][0])
    assert prompt.index("# The idea") < prompt.index("# The sketch the person picked") < prompt.index("# Your task: Build it")


# -- the cost, the events -------------------------------------------------------------------------------------------------------------------

def test_the_sketchs_cost_goes_to_the_goals_ledger_as_its_spec_stage(host, parties, model, looked):
    assert idea_spend.STEP_STAGE["sketch"] == "spec"
    slug, _seen = _sketched(host, parties, model)
    got = idea_spend.of_idea(host.ideas.state_dir, slug)
    lines = [json.loads(ln) for ln in (host.ideas.state_dir / "ideas" / slug / "spend.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [ln["step"] for ln in lines if ln["step"] == "sketch"] == ["sketch"] and got["stages"]["spec"]["usd"] >= 0.01


def test_sketch_made_says_how_many_in_how_long_and_at_what_cost(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model)
    (made,) = _events(host, event_log.SKETCH_MADE)
    assert (made["idea"], made["craft"], made["kind"], made["n"], made["round"], made["cost"]) == (slug, "design", "page", 3, 1, 0.01) and isinstance(made["seconds"], (int, float))
    assert "html" not in json.dumps(made) and PAGE not in json.dumps(made)                                 # never a word of the page


def test_the_events_and_the_word_are_known():
    assert {"sketch_made", "sketch_answered", "sketch_skipped"} <= set(event_log.EVENTS)
    from orkboard.realm import lexicon
    assert lexicon.term("sketch") == "sketch" and lexicon.term("sketch", many=True) == "sketches"


# -- Art: a pick task, with the media tools, and a paid tool only with the person's yes ----------------------------------------------------------

def _art_goal(host, parties, model, text="draw a logo for the app", **kw):
    model.said[("sketch", "")] = PAGES
    slug = _decided(host, parties, model, ("art",), text)
    seen = _sections(host)
    host.command("ideas.confirm", {"idea": slug})
    return slug, seen


def _works(host, files=None):
    """The Art sketch's task stubbed: it makes `files` in its folder and a manifest, as a pick task does; `calls` every call."""
    calls = []

    def work(tier, prompt, effort, budget, workdir, task):
        calls.append({"tier": tier, "prompt": prompt, "workdir": Path(workdir), "task": task})
        pf.leave(Path(workdir), files or {"a.png": pf.png(4, 4), "b.png": pf.png(5, 5), "c.png": pf.png(6, 6)}, names={"a.png": "Anchor", "b.png": "Wolf", "c.png": "Horn"})
        return "done", 0.07, 100, ""
    host.ideas.keeper.work_call = work
    return calls


def test_art_without_the_media_tools_set_up_says_so_and_the_sections_follow(host, parties, model, looked, monkeypatch):
    monkeypatch.setattr(sketches, "media_ready", lambda kind, which=None: False)
    calls = _works(host)
    slug, seen = _art_goal(host, parties, model)
    assert seen == [(slug, "sections")] and calls == [] and model.steps("sketch") == []
    rec = _record(host, slug)
    assert rec["status"] == "skipped" and rec["why"] == "the media tools are not set up"
    assert [t["text"] for t in ideas.talk(host.ideas.state_dir, slug) if t["text"].startswith("No sketch")] == ["No sketch: the media tools are not set up"]
    assert [e["why"] for e in _events(host, event_log.SKETCH_SKIPPED)] == ["the media tools are not set up"]


def test_art_with_the_media_tools_asks_a_pick_task_in_a_folder_of_the_goals_state(host, parties, model, looked, monkeypatch):
    monkeypatch.setattr(sketches, "media_ready", lambda kind, which=None: True)
    calls = _works(host)
    slug, seen = _art_goal(host, parties, model)
    rec = _settle(host, slug)
    assert rec["craft"] == "art" and rec["kind"] == "image" and seen == [] and model.steps("sketch") == []        # a task, not a question
    (call,) = calls
    assert call["task"]["pick"]["kind"] == "image" and call["task"]["pick"]["n"] == 3 and call["task"]["leader"] is True                    # a pick task (spec 51): the media tools follow its `pick`
    assert (call["tier"], idea_target.pick("sketch", "balance")) == ("elder", ("elder", "medium"))
    state = host.ideas.state_dir.resolve()
    assert call["workdir"].resolve().is_relative_to(state) and not call["workdir"].exists()                                               # in the goal's state, gone after
    assert "no paid service" in call["prompt"] and "draw a logo for the app" in call["prompt"] and ".orkcraft-pick.json" in call["prompt"]
    pick = idea_pick.load(host.ideas.state_dir, slug, "sketch-r1")
    assert pick["by"] == "leader" and pick["kind"] == "image" and [(v["name"], v["mime"]) for v in pick["variants"]] == [("Anchor", "image/png"), ("Wolf", "image/png"), ("Horn", "image/png")]
    row = _row(host, slug, "pick")
    assert row["media"] == "image" and row["sketch"] is True and [v["w"] for v in row["variants"]] == [4, 5, 6] and "text" not in row["variants"][0]
    (made,) = _events(host, event_log.SKETCH_MADE)
    assert made["craft"] == "art" and made["kind"] == "image" and made["cost"] == 0.07
    _pick(host, slug, key="B")
    assert seen == [(slug, "sections")] and _record(host, slug)["picked"]["mime"] == "image/png"
    assert "It is a picture (`b.png`)" in sketches.context(host.ideas.state_dir, slug)


def test_a_sound_sketch_is_a_pick_of_sounds_with_audio_tools(host, parties, model, looked, monkeypatch):
    asked = []
    monkeypatch.setattr(sketches, "media_ready", lambda kind, which=None: asked.append(kind) or kind == "audio")
    calls = _works(host, {"a.wav": pf.wav(0.5), "b.wav": pf.wav(0.6), "c.wav": pf.wav(0.7)})
    slug, _seen = _art_goal(host, parties, model, text="a new sound for the win jingle")
    rec = _settle(host, slug)
    assert asked == ["audio"] and rec["kind"] == "audio" and calls[0]["task"]["pick"]["kind"] == "audio"
    assert [v["mime"] for v in idea_pick.load(host.ideas.state_dir, slug, "sketch-r1")["variants"]] == ["audio/wav"] * 3


def test_an_art_task_that_leaves_nothing_usable_is_no_sketch(host, parties, model, looked, monkeypatch):
    monkeypatch.setattr(sketches, "media_ready", lambda kind, which=None: True)
    host.ideas.keeper.work_call = lambda *a: ("done", 0.01, 1, "")                                         # it made no file and no manifest
    slug, seen = _art_goal(host, parties, model)
    _until(host, slug, "sections")
    assert _record(host, slug)["status"] == "skipped" and "left no variants" in _record(host, slug)["why"]


def _paid_machine(monkeypatch, host, tool="codex"):
    from orkboard import settings as machine
    conf = SimpleNamespace(tools={"claude": SimpleNamespace(enabled=True, billing="subscription"), "codex": SimpleNamespace(enabled=True, billing="api")}, main_tool="claude")
    monkeypatch.setattr(machine, "cached", lambda: conf)
    monkeypatch.setattr(host.ideas.keeper, "tool_now", lambda: tool)


def test_a_tool_that_would_be_paid_is_used_only_with_the_persons_yes(host, parties, model, looked, monkeypatch):
    monkeypatch.setattr(sketches, "media_ready", lambda kind, which=None: True)
    calls = _works(host)
    _paid_machine(monkeypatch, host)
    slug, seen = _art_goal(host, parties, model)
    assert seen == [(slug, "sections")] and calls == [] and _record(host, slug)["why"] == "it would be paid, and you have not said yes"
    paid.answer(host.ideas.state_dir, True, time.time() + 3600, time.time())                               # the person's yes, held until the reset
    other, seen = _art_goal(host, parties, model, text="draw another logo for the app")
    assert _settle(host, other)["status"] == "asked" and len(calls) == 1 and seen == []


def test_a_main_tool_billed_by_its_api_by_the_persons_own_choice_is_not_paid(host, parties, model, looked, monkeypatch):
    from orkboard import settings as machine
    conf = SimpleNamespace(tools={"claude": SimpleNamespace(enabled=True, billing="api")}, main_tool="claude")
    monkeypatch.setattr(machine, "cached", lambda: conf)
    monkeypatch.setattr(host.ideas.keeper, "tool_now", lambda: "claude")
    assert host.ideas.keeper._would_be_paid() is False
    monkeypatch.setattr(host.ideas.keeper, "tool_now", lambda: "nobody")
    assert host.ideas.keeper._would_be_paid() is False                                                     # a tool the machine does not know holds nothing back


def test_a_page_sketch_goes_by_the_same_rule_about_a_paid_tool(host, parties, model, looked, monkeypatch):
    _paid_machine(monkeypatch, host)
    slug, seen = _confirmed(host, parties, model)
    assert seen == [(slug, "sections")] and model.steps("sketch") == [] and "paid" in _record(host, slug)["why"]


# -- the way back from the sections' failure --------------------------------------------------------------------------------------------------

def test_the_sections_asked_again_after_a_pick_do_not_sketch_again(host, parties, model, looked):
    slug, seen = _sketched(host, parties, model)
    _pick(host, slug, key="A")
    ideas.save_state(host.ideas.state_dir, slug, state="decided", error="The sections failed: no answer")      # the sections failed: *Try again*
    host.command("ideas.confirm", {"idea": slug})
    assert seen == [(slug, "sections"), (slug, "sections")] and len(model.steps("sketch")) == 1


def test_a_pitch_is_never_sketched(host, parties, model, looked):
    slug = host.command("ideas.add", {"text": "add a settings screen", "track": parties["design"]})["slug"]
    host.ideas.keeper.is_pitch = lambda s: True
    assert host.ideas.keeper.sketch_for(slug) is None


def test_a_sketch_the_host_lost_is_back_at_its_decision_by_the_clock_and_asked_again_by_start(host, parties, model, looked):
    slug = _decided(host, parties, model, ("design",), "add a settings screen")
    keeper = host.ideas.keeper
    ideas.save_state(host.ideas.state_dir, slug, state="sketch")                                           # the process closed while it was made
    sketches.save(host.ideas.state_dir, slug, status="making", round=1, craft="design", party=parties["design"], leader="product-designer", kind="page", ask="x")
    assert keeper.sketch_lost(slug) is True and _state(host, slug)["state"] == "decided" and _record(host, slug)["status"] == ""
    assert keeper.sketch_lost(slug) is False                                                               # nothing more to recover
    ideas.save_state(host.ideas.state_dir, slug, state="sketch")
    sketches.save(host.ideas.state_dir, slug, status="making")
    keeper.tick(now=time.time() + 100_000)                                                                  # the clock finds it too
    assert _state(host, slug)["state"] == "decided"
    ideas.save_state(host.ideas.state_dir, slug, state="sketch")
    sketches.save(host.ideas.state_dir, slug, status="asked")
    assert keeper.sketch_lost(slug) is False and _state(host, slug)["state"] == "sketch"                   # a sketch that waits for the person is not lost


def test_a_goal_being_sketched_has_the_one_row_a_pick_and_no_route_or_decision_card(host, parties, model, looked):
    slug, _seen = _sketched(host, parties, model)
    assert [n["kind"] for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug] == ["pick"]
    mine = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug)
    assert mine["place"] == "table" and mine["asks_you"] is True
    assert next(n for n in host.command("ideas.map")["nodes"] if n["slug"] == slug)["state"] == "sketch"


def test_a_busy_keeper_refuses_the_sketch_and_writes_nothing(host, parties, model, looked):
    slug = _decided(host, parties, model, ("design",), "add a settings screen")
    keeper = host.ideas.keeper
    keeper._busy[slug] = "talking"
    with pytest.raises(Exception, match="busy"):
        keeper.sketch_begin(slug, {"craft": "design", "party": parties["design"], "leader": "product-designer", "kind": "page"})
    assert _record(host, slug) == {} and _state(host, slug)["state"] == "decided"
