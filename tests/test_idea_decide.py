"""Spec 99 E (docs/specs/99-a-goals-way.md §6) on the keeper: the decision (one call of the Orkmaster on the cheaper tier with no tools, given the asked words, the stances,
the answers, the defaults and the decisions file's last ten headings; worded by code when the call cannot be had) and *Confirm and start* (the numbered entry appended to the
project's decisions file, the number read again at the commit, committed to dev with the Board's pages; never for a bug). The model call is stubbed (`keeper.call`); the commit
test is a real git repository."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time

import pytest

from orkboard.core import idea_keeper
from orkboard.core.idea_decide import body_of, clean_decision, corrected, demote, entry_of, worded
from orkboard.gui.board_host import Orkboard
from orkboard.realm import decisions_log, goal_team, idea_questions, idea_target, ideas, library, spec_sections


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def parties(host):
    return {"product": _party(host, "Product", "product-manager", ["copywriter"], "product"),
            "tech": _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")}


DECISION = {"title": "Dark mode ships as a setting", "why": "People read at night; Tech keeps one theme file.", "points": ["Product asks for a setting, off by default.", "Tech adds the theme.", "No scheduling."]}


class Model:
    """The keeper's call stubbed: `said[(step, party)]` the JSON answered (or a callable of the call), `calls` every call made."""

    def __init__(self, host):
        self.host, self.calls, self.said, self.lock = host, [], {}, threading.Lock()
        host.ideas.keeper.call = self

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        row = {"tier": tier, "prompt": prompt, "effort": effort, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"], "party": getattr(k._tls, "party", ""),
               "as_role": getattr(k._tls, "as_role", "")}
        with self.lock:
            self.calls.append(row)
        answer = self.said.get((row["step"], row["party"]), self.said.get((row["step"], "")))
        if callable(answer):
            answer = answer(row)
        if isinstance(answer, str):
            return answer, 0.01, 10, ""
        return json.dumps(answer if answer is not None else {"title": "A goal", "questions": []}), 0.01, 10, ""

    def steps(self, step):
        return [c for c in self.calls if c["step"] == step]


@pytest.fixture
def model(host):
    return Model(host)


def _state(host, slug):
    return ideas.state(host.ideas.state_dir, slug)


def _until(host, slug, state, seconds=10):
    for _ in range(int(seconds * 100)):
        if _state(host, slug)["state"] == state and not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError(f"the goal never reached {state}: {_state(host, slug)['state']} {_state(host, slug)['error']}")


def _row(host, slug, kind):
    return next((n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug and n["kind"] == kind), None)


def _decided(host, parties, model, which=("tech",), text="add a dark mode option", per=0, answer=DECISION):
    """A goal sent to Talk with the questions the leaders ask (`per` each), answered by their picks: the decision is worded and waits."""
    for who in which:
        model.said[("talk_round", parties[who])] = {"stance": f"{who} stance", "for": f"{who} for", "against": f"{who} against", "second_round": False,
                                                    "questions": [{"ask": f"{who} question {n}", "choices": ["A", "B"], "pick": 0, "why": "because", "blocks": False} for n in range(per)]}
    model.said[("decide", "")] = answer
    slug = host.command("ideas.add", {"text": text, "track": parties[which[0]]})["slug"]
    host.command("ideas.route_set", {"idea": slug, "route": [parties[w] for w in which]})
    host.command("ideas.talk", {"idea": slug})
    if per:
        for _ in range(1000):
            if _row(host, slug, "talk"):
                break
            time.sleep(0.01)
        host.command("ideas.talk_answer", {"idea": slug, "answers": [], "decide": True})
    _until(host, slug, "decided")
    return slug


# -- the words of a decision, strictly ----------------------------------------------------------------------------------------------------

def test_a_decision_is_a_title_a_why_and_numbered_points_by_code():
    got = clean_decision({"title": " Dark  mode ", "why": "Because.", "points": ["1. One", "- Two", "Two", 3, "", "Three"]})
    assert got == {"title": "Dark mode", "why": "Because.", "points": ["One", "Two", "Three"]}               # the model never numbers; a repeat once; a non-text point is nothing
    assert body_of(got["why"], got["points"]) == "Why: Because.\n\n1. One\n2. Two\n3. Three"
    assert clean_decision({"title": "T", "why": "W", "points": ["only one"]}) is None and clean_decision({"title": "", "why": "W", "points": ["a", "b"]}) is None
    assert clean_decision("not an object") is None and clean_decision({"title": "T", "why": "W", "points": "a, b"}) is None
    assert len(clean_decision({"title": "T", "why": "W", "points": [f"p{n}" for n in range(20)]})["points"]) == 8


def test_an_entry_is_the_files_heading_with_the_date_and_who_and_a_body_never_starts_a_heading_of_its_own():
    import datetime as dt
    assert entry_of(119, "Dark mode", "Why: x.", dt.date(2026, 10, 28)) == "## 119. Dark mode (28 October, the person and Orkboard)\n\nWhy: x.\n"
    assert demote("Why\n# One\n## Two\n### Three\n#nospace") == "Why\n### One\n### Two\n### Three\n#nospace"
    assert corrected("## 12. A better title (28 October, the person and Orkboard)\nWhy: mine.", "Old") == ("A better title", "Why: mine.")
    assert corrected("Why: just words.\n## sneaky", "Old") == ("Old", "Why: just words.\n### sneaky")
    assert worded("Dark mode", "add a dark mode option\nmore", ["Which first? — Web"], ["Tech"])["points"] == ["Which first? — Web", "Done by Tech"]


# -- the call -----------------------------------------------------------------------------------------------------------------------------------

def test_one_call_of_the_orkmaster_on_the_cheaper_tier_with_no_tools_and_the_decision_waits_in_a_row(host, parties, model):
    (host.repo_root / "docs" / "decisions.md").write_text("# Decisions\n\n## 7. Seven (1 May, the owner)\n\nWhy: x.\n\n## 8. Eight (2 May, the owner)\n\nWhy: y.\n", encoding="utf-8")
    git(host.repo_root, "add", "-A")
    git(host.repo_root, "commit", "-qm", "decisions")
    git(host.repo_root, "branch", "-f", "dev", "HEAD")
    host.ideas._board_tree.ensure()                                                                                   # the Board's tree follows dev
    slug = _decided(host, parties, model, ("product", "tech"), per=1)
    calls = model.steps("decide")
    assert len(calls) == 1 and calls[0]["tools"] is False and calls[0]["as_role"] == "orkmaster" and (calls[0]["tier"], calls[0]["effort"]) == idea_target.pick("decide", "balance")
    assert idea_target.pick("decide", "balance") == idea_target.pick("route", "balance") == ("warrior", "low")
    prompt = calls[0]["prompt"]
    assert "add a dark mode option" in prompt and "product stance" in prompt and "tech question 0 — A" in prompt and "Product, then Tech" in prompt     # the words, the stances, the answers
    assert "7. Seven" in prompt and "8. Eight" in prompt and "Read no file" in prompt                                                              # the last headings, no file
    row = _row(host, slug, "decision")
    assert row == {**row, "kind": "decision", "idea": slug, "number": 9, "title": DECISION["title"], "confirmed": False, "error": "",
                   "text": "Why: People read at night; Tech keeps one theme file.\n\n1. Product asks for a setting, off by default.\n2. Tech adds the theme.\n3. No scheduling."}
    assert _state(host, slug)["state"] == "decided" and _state(host, slug)["measure"]["step"] == "decide"
    assert spec_sections.record(host.ideas.state_dir, slug)["decision"]["by"] == "orkmaster"


def test_a_call_that_cannot_be_had_is_worded_by_code_for_the_person_to_correct(host, parties, model):
    slug = _decided(host, parties, model, per=1, answer="I am sorry, I cannot")
    d = spec_sections.record(host.ideas.state_dir, slug)["decision"]
    assert d["by"] == "code" and d["title"] == "add a dark mode option" and "tech question 0 — A" in d["text"]
    row = _row(host, slug, "decision")
    assert row["number"] == 1 and row["text"].startswith("Why: The person asked for this and talked it through with Tech")        # no decisions file yet: number 1


def test_a_stop_during_the_call_puts_the_goal_back_at_its_route_card(host, parties, model):
    def stopped(row):
        raise InterruptedError("stopped")
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "for": "f", "against": "a", "questions": []}
    model.said[("decide", "")] = stopped
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    host.command("ideas.talk", {"idea": slug})
    _until(host, slug, "routed")
    assert _state(host, slug)["error"] == "" and _row(host, slug, "decision") is None and _row(host, slug, "route") is not None


def test_the_decision_is_asked_only_of_a_goal_at_talk(host, parties, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    with pytest.raises(idea_keeper.KeeperError, match="not at Talk"):
        host.ideas.keeper.decide(slug)
    with pytest.raises(idea_keeper.KeeperError, match="gone"):
        host.ideas.keeper.decide("nobody")


# -- Confirm and start --------------------------------------------------------------------------------------------------------------------------

def test_confirm_appends_the_numbered_entry_and_commits_it_to_dev_with_the_pages_then_the_sections_follow(host, parties, model):
    slug = _decided(host, parties, model)
    sections = []
    host.ideas.keeper.sections = lambda s: sections.append((s, _state(host, s)["state"]))                  # E's second half is the next tests'
    got = host.command("ideas.confirm", {"idea": slug})
    assert got["ok"] is True and got["number"] == 1 and got["title"] == DECISION["title"] and got["path"] == "docs/decisions.md" and got["commit"] and got["held"] == ""
    assert sections == [(slug, "sections")] and _state(host, slug)["state"] == "sections"
    entry = git(host.repo_root, "show", "dev:docs/decisions.md")
    assert entry.startswith("# Decisions\n\n## 1. Dark mode ships as a setting (") and ", the person and Orkboard)\n\nWhy: People read at night" in entry
    assert "1. Product asks for a setting, off by default.\n2. Tech adds the theme.\n3. No scheduling.\n" in entry + "\n"
    assert git(host.repo_root, "rev-parse", "dev") == got["commit"] and "Orkline board" in git(host.repo_root, "log", "-1", "--format=%an", "dev")
    assert git(host.repo_root, "log", "-1", "--format=%s", "dev") == "board: decision 1 — Dark mode ships as a setting"
    files = git(host.repo_root, "show", "--name-only", "--format=", "dev").splitlines()
    assert "docs/decisions.md" in files and any(f.endswith(f"pages/ideas/{slug}.md") for f in files) and len(files) >= 2                       # the file and the Board's pages, one commit
    assert not (host.repo_root / "docs" / "decisions.md").exists()                                                # the person's tree is not touched
    assert "Decision 1: Dark mode ships as a setting" in ideas.idea_page(host.ideas.root(), slug).section("Decisions")
    assert _row(host, slug, "decision") is None and spec_sections.record(host.ideas.state_dir, slug)["decision"]["confirmed"] is True


def test_the_person_s_correction_is_kept_as_written_and_its_heading_is_the_title(host, parties, model):
    slug = _decided(host, parties, model)
    host.ideas.keeper.sections = lambda s: None
    host.command("ideas.confirm", {"idea": slug, "text": "## 3. Light and dark (28 October, the person and Orkboard)\nWhy: mine.\n\n## 1. Sneaky\n1. Only dark."})
    entry = git(host.repo_root, "show", "dev:docs/decisions.md")
    assert "## 1. Light and dark (" in entry and "Why: mine.\n\n### 1. Sneaky\n1. Only dark." in entry                         # a heading inside is demoted, the number is the file's own
    assert [h.split(" (")[0] for h in decisions_log.headings(entry)] == ["1. Light and dark"]


def test_the_number_is_read_again_at_the_commit_so_two_goals_never_take_one(host, parties, model):
    first = _decided(host, parties, model, text="add a dark mode option")
    second = _decided(host, parties, model, text="add a light mode option")
    assert _row(host, first, "decision")["number"] == _row(host, second, "decision")["number"] == 1                        # both were worded before either was confirmed
    host.ideas.keeper.sections = lambda s: None
    a = host.command("ideas.confirm", {"idea": second})
    b = host.command("ideas.confirm", {"idea": first})
    assert (a["number"], b["number"]) == (1, 2)
    assert decisions_log.headings(git(host.repo_root, "show", "dev:docs/decisions.md"))[0].startswith("1. ") and len(decisions_log.headings(git(host.repo_root, "show", "dev:docs/decisions.md"))) == 2


def test_the_number_follows_the_file_as_dev_holds_it_even_when_it_moved_after_the_decision_was_worded(host, parties, model):
    slug = _decided(host, parties, model)
    tree = host.ideas._board_tree
    tree.edit_file("docs/decisions.md", lambda old: "# Decisions\n\n## 41. Forty-one (1 May, the owner)\n\nWhy: x.\n", "someone else's")
    host.ideas.keeper.sections = lambda s: None
    assert host.command("ideas.confirm", {"idea": slug})["number"] == 42


def test_the_path_the_project_chose_is_the_decisions_file_and_the_file_is_made_with_a_head(host, parties, model):
    (host.ideas.state_dir).mkdir(parents=True, exist_ok=True)
    (host.ideas.state_dir / "project.json").write_text(json.dumps({"decisions": "notes/adr.md"}), encoding="utf-8")
    slug = _decided(host, parties, model)
    host.ideas.keeper.sections = lambda s: None
    assert host.command("ideas.confirm", {"idea": slug})["path"] == "notes/adr.md"
    assert git(host.repo_root, "show", "dev:notes/adr.md").startswith("# Decisions\n\n## 1. ")
    (host.ideas.state_dir / "project.json").write_text(json.dumps({"decisions": "../outside.md"}), encoding="utf-8")          # never outside the project
    assert host.ideas.keeper._decisions()[1] == "docs/decisions.md"


def test_a_decision_confirmed_twice_writes_once_and_asks_the_sections_again(host, parties, model):
    slug = _decided(host, parties, model)
    asked = []
    host.ideas.keeper.sections = lambda s: asked.append(_state(host, s)["state"])
    host.command("ideas.confirm", {"idea": slug})
    ideas.save_state(host.ideas.state_dir, slug, state="decided", error="The sections failed: x")          # what a failed section leaves
    row = _row(host, slug, "decision")
    assert row["confirmed"] is True and row["error"] == "The sections failed: x" and row["number"] == 1
    got = host.command("ideas.confirm", {"idea": slug})
    assert got["number"] == 1 and asked == ["sections", "sections"]
    assert decisions_log.headings(git(host.repo_root, "show", "dev:docs/decisions.md")) and git(host.repo_root, "show", "dev:docs/decisions.md").count("## 1.") == 1


def test_confirm_is_refused_in_plain_words_where_there_is_nothing_to_confirm_or_the_sections_could_not_follow(host, parties, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    with pytest.raises(idea_keeper.KeeperError, match="no decision to confirm"):
        host.ideas.keeper.confirm(slug)
    with pytest.raises(idea_keeper.KeeperError, match="gone"):
        host.ideas.keeper.confirm("nobody")
    decided = _decided(host, parties, model)
    k = host.ideas.keeper
    k.window_until = lambda: time.time() + 3600                                                                                    # a spent window: the sections would be refused, so nothing is written
    with pytest.raises(idea_keeper.KeeperError, match="window is spent"):
        k.confirm(decided)
    assert not decisions_log.path(host.repo_root).exists() and spec_sections.record(host.ideas.state_dir, decided)["decision"]["confirmed"] is False


def test_without_the_boards_tree_the_file_is_written_in_the_working_copy_and_nothing_is_committed(host, parties, model):
    slug = _decided(host, parties, model)
    host.ideas.keeper.sections = lambda s: None
    before = git(host.repo_root, "rev-parse", "dev")
    got = host.ideas.keeper.confirm(slug)                                                                            # no tree handed to it
    assert got["number"] == 1 and got["commit"] == ""
    assert (host.repo_root / "docs" / "decisions.md").read_text(encoding="utf-8").startswith("# Decisions\n\n## 1. ")
    assert git(host.repo_root, "rev-parse", "dev") == before                                                          # the keeper never commits


def test_a_bug_and_a_recurring_round_are_never_decided(host, parties, model):
    """A bug's Talk is its diagnosis (core/idea_talk.py) and goes to the sections; a recurring round is not routed: neither reaches `decide`."""
    slug = host.command("ideas.add", {"text": "every week review the logs", "track": parties["tech"], "recurring": True})["slug"]
    assert _state(host, slug)["state"] != "decided" and spec_sections.record(host.ideas.state_dir, slug) == {}
    assert idea_questions.record(host.ideas.state_dir, slug) == {}
