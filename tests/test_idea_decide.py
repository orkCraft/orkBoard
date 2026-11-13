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

from orkboard.gui.board_host import Orkboard
from orkboard.realm import decisions_log, goal_team, idea_questions, idea_target, ideas, library, spec_sections


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    (h.ideas.state_dir / "project.json").write_text('{"decisions": "docs/decisions.md"}', encoding="utf-8")        # this project keeps its decisions as one file (a project with no log gets a MADR folder: spec 127 B.4)
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


def test_a_stop_during_the_call_puts_the_goal_back_at_its_route_card(host, parties, model):
    def stopped(row):
        raise InterruptedError("stopped")
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "for": "f", "against": "a", "questions": []}
    model.said[("decide", "")] = stopped
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    host.command("ideas.talk", {"idea": slug})
    _until(host, slug, "routed")
    assert _state(host, slug)["error"] == "" and _row(host, slug, "decision") is None and _row(host, slug, "route") is not None


# -- Confirm and start --------------------------------------------------------------------------------------------------------------------------


def test_confirm_by_the_leaders_writes_the_agreed_heading_with_their_stances_among_the_points_then_the_sections_follow(host, parties, model):
    slug = _decided(host, parties, model)
    sections = []
    host.ideas.keeper.sections = lambda s: sections.append((s, _state(host, s)["state"]))
    got = host.ideas.keeper.confirm(slug, "my words are not theirs", host.ideas._decision_tree(), "leaders")        # the person's text is the person's: the leaders confirm what was worded
    assert got["number"] == 1 and got["title"] == DECISION["title"] and got["commit"] and sections == [(slug, "sections")]
    entry = git(host.repo_root, "show", "dev:docs/decisions.md")
    head = next(line for line in entry.splitlines() if line.startswith("## 1. "))
    assert head.startswith("## 1. Dark mode ships as a setting (") and head.endswith(", the leaders, all agreed; Orkboard)") and "the person" not in head
    assert "my words are not theirs" not in entry and "3. No scheduling.\n4. For " in entry and ": tech for" in entry                # the leaders' stances, numbered on
    d = spec_sections.record(host.ideas.state_dir, slug)["decision"]
    assert d["confirmed"] is True and d["confirmed_by"] == "leaders" and "For" in d["text"]
    assert ideas.talk(host.ideas.state_dir, slug)[-1]["who"] == "keeper" and "the leaders, all agreed" in ideas.talk(host.ideas.state_dir, slug)[-1]["text"]


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
    assert git(host.repo_root, "rev-parse", "dev") == got["commit"] and "Orkboard board" in git(host.repo_root, "log", "-1", "--format=%an", "dev")
    assert git(host.repo_root, "log", "-1", "--format=%s", "dev") == "board: decision 1 — Dark mode ships as a setting"
    files = git(host.repo_root, "show", "--name-only", "--format=", "dev").splitlines()
    assert "docs/decisions.md" in files and any(f.endswith(f"pages/ideas/{slug}.md") for f in files) and len(files) >= 2                       # the file and the Board's pages, one commit
    assert not (host.repo_root / "docs" / "decisions.md").exists()                                                # the person's tree is not touched
    assert "Decision 1: Dark mode ships as a setting" in ideas.idea_page(host.ideas.root(), slug).section("Decisions")
    assert _row(host, slug, "decision") is None and spec_sections.record(host.ideas.state_dir, slug)["decision"]["confirmed"] is True


def test_the_number_is_read_again_at_the_commit_so_two_goals_never_take_one(host, parties, model):
    first = _decided(host, parties, model, text="add a dark mode option")
    second = _decided(host, parties, model, text="add a light mode option")
    assert _row(host, first, "decision")["number"] == _row(host, second, "decision")["number"] == 1                        # both were worded before either was confirmed
    host.ideas.keeper.sections = lambda s: None
    a = host.command("ideas.confirm", {"idea": second})
    b = host.command("ideas.confirm", {"idea": first})
    assert (a["number"], b["number"]) == (1, 2)
    assert decisions_log.headings(git(host.repo_root, "show", "dev:docs/decisions.md"))[0].startswith("1. ") and len(decisions_log.headings(git(host.repo_root, "show", "dev:docs/decisions.md"))) == 2


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


# -- the leaders the person overruled (spec 108 §4.4, decisions §183.3) ---------------------------------------------------------------------------

NO = {"verdict": "no", "why": "It adds a third caller to server/ws", "instead": "Only the setting"}


def _overruled(host, parties, model, answer=DECISION, **said):
    """A goal whose Tech said `said` (a verdict) in Talk and the person went on anyway: the decision is worded and waits."""
    model.said[("talk_round", parties["tech"])] = {"stance": "tech stance", "for": "tech for", "against": "tech against", "second_round": False, "questions": [], **said}
    model.said[("decide", "")] = answer
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"]]})
    host.command("ideas.talk", {"idea": slug})
    for _ in range(1000):
        if _row(host, slug, "objection") or _row(host, slug, "decision"):
            break
        time.sleep(0.01)
    if said.get("verdict") == "no":
        assert _state(host, slug)["state"] == "talk" and model.steps("decide") == []                                  # the decision waits for the person's answer
        host.command("ideas.objection", {"idea": slug, "party": parties["tech"], "answer": "go"})
    if said.get("verdict") == "doubt":                                                                                 # a doubt alone is a hearing (spec 120 §3.4): the person's throw
        for _ in range(500):
            if host.command("ideas.hearing", {"idea": slug}):
                break
            time.sleep(0.01)
        assert model.steps("decide") == []
        idea_questions.save_record(host.ideas.state_dir, slug, {**idea_questions.record(host.ideas.state_dir, slug), "hearing": False})
        host.ideas.keeper._on(slug, "decide")                       # the hearing closed by hand (no throw, which would confirm at once), so the decision's card waits
    _until(host, slug, "decided")
    return slug


def test_the_decision_is_given_each_no_the_person_overruled_and_its_entry_says_it(host, parties, model):
    slug = _overruled(host, parties, model, **NO)
    name = host.ideas.keeper._name("architect")
    line = f"Against {name}: It adds a third caller to server/ws"
    prompt = model.steps("decide")[0]["prompt"]
    assert "Leaders the person overruled, and those who doubted" in prompt and f"- {line}" in prompt and "word for word" in prompt
    text = _row(host, slug, "decision")["text"]
    assert f"4. {line}" in text.split("\n") and "1. Product asks for a setting, off by default." in text          # the Orkmaster's points stay, the overruled is added
    host.ideas.keeper.sections = lambda s: None
    host.command("ideas.confirm", {"idea": slug})
    entry = git(host.repo_root, "show", "dev:docs/decisions.md")
    assert f"4. {line}\n" in entry + "\n"                                                                              # and it is in the file the entry is appended to


# -- a decision with no goal (spec 116 §4: a hypothesis's verdict) -----------------------------------------------------------------------------------

def test_write_decision_appends_the_next_numbered_entry_with_no_goal_and_commits_it_to_dev(host):
    k = host.ideas.keeper
    tree = host.ideas._decision_tree()
    first = k.write_decision("Hypothesis held: People want a sketch", "Signal: most ask for one\n\n## Not a heading of the file's own", tree)
    second = k.write_decision("Hypothesis refuted: Teams want sharing", "Why: nobody asked.", tree)
    assert (first["number"], second["number"]) == (1, 2) and first["path"] == "docs/decisions.md" and first["commit"] and first["held"] == "" and first["pages"] >= 0
    log = git(host.repo_root, "show", "dev:docs/decisions.md")
    assert log.startswith("# Decisions\n\n## 1. Hypothesis held: People want a sketch (") and ", the person and Orkboard)\n\nSignal: most ask for one" in log
    assert "### Not a heading of the file's own" in log
    assert [h.split(" (")[0] for h in decisions_log.headings(log)] == ["1. Hypothesis held: People want a sketch", "2. Hypothesis refuted: Teams want sharing"]
    assert git(host.repo_root, "rev-parse", "dev") == second["commit"] and git(host.repo_root, "log", "-1", "--format=%s", "dev") == "board: decision 2 — Hypothesis refuted: Teams want sharing"
    assert not (host.repo_root / "docs" / "decisions.md").exists()


def test_a_goals_decision_and_a_goalless_one_share_the_numbers(host, parties, model):
    slug = _decided(host, parties, model)
    host.ideas.keeper.sections = lambda s: None
    tree = host.ideas._decision_tree()
    assert host.ideas.keeper.write_decision("No goal", "Why: x.", tree)["number"] == 1
    assert host.command("ideas.confirm", {"idea": slug})["number"] == 2


# -- a project whose decisions are a folder of ADR files (spec 126 D) ---------------------------------------------------------------------------------

MADR_FILE = "---\nstatus: accepted\ndate: 2026-03-0{n}\n---\n\n# Title {n}\n\n## Context and Problem Statement\n\nWhy {n}.\n\n## Decision Outcome\n\nChosen {n}.\n"
NYGARD_FILE = "# {n}. Title {n}\n\nDate: 2026-03-0{n}\n\n## Status\n\nAccepted\n\n## Context\n\nWhy {n}.\n\n## Decision\n\nChosen {n}.\n\n## Consequences\n\nNone.\n"


def _adr_folder(host, rel, text, n=2):
    """The project keeps its decisions as `rel`'s files (committed to dev, the Board's tree following it)."""
    (host.ideas.state_dir / "project.json").unlink(missing_ok=True)              # the project chose no file: the folder is the only log it keeps
    folder = host.repo_root / rel
    folder.mkdir(parents=True)
    for i in range(1, n + 1):
        (folder / f"{i:04d}-title-{i}.md").write_text(text.format(n=i), encoding="utf-8")
    git(host.repo_root, "add", "-A")
    git(host.repo_root, "commit", "-qm", "adrs")
    git(host.repo_root, "branch", "-f", "dev", "HEAD")
    host.ideas.root()
    host.ideas._board_tree.ensure()


def test_a_decision_is_the_next_madr_file_of_the_projects_folder_committed_through_the_boards_tree(host):
    from orkboard.realm import doc_formats
    _adr_folder(host, "docs/decisions", MADR_FILE)
    tree = host.ideas._decision_tree()
    first = host.ideas.keeper.write_decision("Hypothesis held: People want a sketch", "Signal: most ask for one\n\n## Not a heading", tree)
    second = host.ideas.keeper.write_decision("Teams want sharing", "Why: nobody asked.", tree, "leaders", "share-it")
    assert (first["number"], second["number"]) == (3, 4) and first["path"] == "docs/decisions/0003-hypothesis-held-people-want-a-sketch.md" and first["commit"] and first["held"] == ""
    assert second["path"] == "docs/decisions/0004-teams-want-sharing.md" and git(host.repo_root, "rev-parse", "dev") == second["commit"]
    assert git(host.repo_root, "log", "-1", "--format=%s", "dev") == "board: decision 4 — Teams want sharing"
    assert "docs/decisions/0004-teams-want-sharing.md" in git(host.repo_root, "show", "--name-only", "--format=", "dev").splitlines()
    text = git(host.repo_root, "show", f"dev:{first['path']}")
    assert text.startswith("---\nstatus: accepted\ndate: ") and "decision-makers: [the person]" in text and "ork-goal" not in text
    assert not (host.repo_root / "docs" / "decisions" / "0003-hypothesis-held-people-want-a-sketch.md").exists()                    # the person's tree is not touched
    rec = doc_formats.parse_record(text, "0003-x.md")
    assert (rec["format"], rec["number"], rec["title"], rec["status"]) == ("madr", 3, "Hypothesis held: People want a sketch", "accepted")
    assert rec["decision"].startswith("Signal: most ask for one") and "#### Not a heading" in rec["decision"]                  # a heading of the body never splits the record
    other = doc_formats.parse_record(git(host.repo_root, "show", f"dev:{second['path']}"), "0004-x.md")
    assert other["deciders"] == ["the leaders"] and other["extra"]["ork-goal"] == "share-it"
    assert "docs/decisions.md" not in git(host.repo_root, "ls-tree", "--name-only", "dev", "docs/")                                # no one-file log was made beside the folder


def test_a_goals_confirm_in_a_folder_writes_the_file_with_the_goal_and_the_leaders_read_the_folder(host, parties, model):
    _adr_folder(host, "docs/decisions", MADR_FILE)
    slug = _decided(host, parties, model)
    prompt = model.steps("decide")[0]["prompt"]
    assert "(docs/decisions)" in prompt and "1. Title 1" in prompt and "2. Title 2" in prompt
    assert spec_sections.record(host.ideas.state_dir, slug)["decision"]["number"] == 3                                    # the number the card shows
    host.ideas.keeper.sections = lambda s: None
    got = host.command("ideas.confirm", {"idea": slug})
    assert got["number"] == 3 and got["path"] == "docs/decisions/0003-dark-mode-ships-as-a-setting.md" and got["commit"]
    text = git(host.repo_root, "show", f"dev:{got['path']}")
    assert f"ork-goal: {slug}" in text and "decision-makers: [the person]" in text and "## Decision Outcome\n\nWhy: People read at night" in text
    assert "3. No scheduling." in text
    assert spec_sections.record(host.ideas.state_dir, slug)["decision"]["path"] == got["path"]


