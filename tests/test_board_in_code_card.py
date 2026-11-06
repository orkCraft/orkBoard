"""Spec 151 F, the faces (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md F.1, F.3, F.4, C.4, D; decisions §255.10), on Orkboard's real host and a fixture repository (real git in tmp_path; GitHub's
anonymous check faked, no model, no AI tool, no network): the Orkmaster's card thrown while the question is wanted and answered both ways, the unknown remote's two steps, the card thrown again when the
repository is found public since, the rules' switch in its three states, `orkboard init --publish | --keep-off` and the refusal, a new goal kept off reaching `board_in_code`, and another tool's hold on a row."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.gui import agent_rules_switch as switch, board_cli
from orkboard.gui.board_host import Orkboard
from orkboard.gui.board_in_code_host import _State
from orkboard.realm import agent_rules, board_branch, board_in_code, event_log, goal_take, ideas, lexicon

ASK = "Your goals, their specs, the leaders' words and the decisions will be public, in the repository's history: a later No does not take them back."


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def code(monkeypatch):
    """GitHub's answer to the anonymous check, changeable: 404 private, 200 public, 0 no answer. Any other look at the network fails the test."""
    box = {"code": 404, "asked": 0}

    def get(url):
        box["asked"] += 1
        return box["code"]
    monkeypatch.setattr(board_branch, "http_status", get)
    return box


@pytest.fixture
def host(fake_repo, code):
    git(fake_repo, "remote", "add", "origin", "https://github.com/acme/app.git")
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def look(host):
    """The host's tick, once and in this thread: the day's look kept, the Orkmaster's card read afresh."""
    p = host.projects.current()
    return host.board_in_code.run(p, _State())


def cards(host):
    return [r for r in host.command("ideas.board", {})["needs_you"] if r["kind"] == "in_code"]


def a_day_passes(root: Path) -> None:
    """The kept look is a day old: the next one asks GitHub again."""
    cache = root / ".orkcraft" / board_in_code.CACHE
    data = json.loads(cache.read_text(encoding="utf-8"))
    cache.write_text(json.dumps({**data, "until": 0}), encoding="utf-8")


# -- F.1: the card ----------------------------------------------------------------------------------------------------------------

def test_a_private_repository_is_asked_nothing(host, code):
    look(host)
    assert cards(host) == [] and board_in_code.read(host.projects.current().root) is None


def test_a_public_repository_throws_the_publish_question_with_its_two_answers(host, code):
    code["code"] = 200
    look(host)
    (row,) = cards(host)
    assert row["step"] == "publish" and row["public"] is True and row["blocks"] is True
    assert row["text"] == ASK and row["words"]["publish"] == "Publish the Board" and row["words"]["off"] == "Keep the Board off the repository"
    assert row["held"] == "This repository is public now: the Board waits for your answer before anything is pushed."


def test_the_pages_already_in_the_history_are_counted_in_the_question(host, code):
    root = host.projects.current().root
    look(host)                                                                                     # private: the Board went into the work branch
    ideas.save_goal(host.ideas.root(), None, "Tech", "About Tech", None, "normal", craft="engineering")
    host.ideas.tree_flush(force=True)
    pages = board_in_code.pages_in_history(root, "dev")
    assert pages >= 1
    code["code"] = 200
    a_day_passes(root)
    look(host)                                                                                     # …and the repository is public now
    (row,) = cards(host)
    assert row["pages_in_history"] == pages
    assert row["text"] == ASK + (f" {pages} pages of the Board are already in its history." if pages != 1 else " 1 page of the Board is already in its history.")


def test_publish_writes_the_yes_flushes_the_tree_and_says_so_in_the_log(host, code):
    code["code"] = 200
    look(host)
    root = host.projects.current().root
    flushed = []
    real = host.ideas.tree_flush
    host.ideas.tree_flush = lambda force=False: flushed.append(force) or real(force)
    got = host.command("ideas.in_code", {"answer": "publish"})
    assert got == {"ok": True, "answer": "publish", "in_code": True, "visibility": "public"}
    assert board_in_code.read(root) is True and flushed == [True] and cards(host) == []
    said = [r for r in event_log.read(root) if r["event"] == event_log.BOARD_IN_CODE_ANSWERED]
    assert [(r["answer"], r["visibility"]) for r in said] == [("publish", "public")]
    assert board_in_code.status(root, root / ".orkcraft")["goes"] is True


def test_keeping_the_board_off_writes_the_no_and_nothing_goes_to_the_work_branch(host, code):
    code["code"] = 200
    look(host)
    root = host.projects.current().root
    host.command("ideas.in_code", {"answer": "off"})
    assert board_in_code.read(root) is False and cards(host) == []
    assert board_in_code.status(root, root / ".orkcraft")["goes"] is False
    assert "in_code = false" in (root / "orkcraft.toml").read_text(encoding="utf-8")
    assert [r["answer"] for r in event_log.read(root) if r["event"] == event_log.BOARD_IN_CODE_ANSWERED] == ["off"]


def test_an_answer_with_no_question_or_a_wrong_one_is_refused_in_words(host, code):
    with pytest.raises(Exception) as none:
        host.command("ideas.in_code", {"answer": "publish"})
    assert "Nothing asks about the Board in the code now" in str(none.value)
    code["code"] = 200
    a_day_passes(host.projects.current().root)                                                     # the refused answer asked GitHub: private, a day ago
    look(host)
    with pytest.raises(Exception) as bad:
        host.command("ideas.in_code", {"answer": "maybe"})
    assert "The answer is publish, off or private" in str(bad.value)
    with pytest.raises(Exception) as priv:
        host.command("ideas.in_code", {"answer": "private"})
    assert "Only a repository Orkboard cannot read" in str(priv.value) and board_in_code.read(host.projects.current().root) is None


# -- the remote Orkboard cannot read: two steps ----------------------------------------------------------------------------------

def test_a_remote_orkboard_cannot_read_asks_if_it_is_private_first_and_private_is_the_yes(host, code):
    git(host.projects.current().root, "remote", "set-url", "origin", "git@gitlab.example.com:acme/app.git")
    look(host)
    (row,) = cards(host)
    assert row["step"] == "private" and row["visibility"] == "unknown" and row["ask"] == "Is this repository private?" and row["title"] == "Is this repository private?"
    assert row["words"]["private"] == "Private" and row["words"]["public"] == "Public" and row["held"] == "" and row["text"] == ASK
    root = host.projects.current().root
    got = host.command("ideas.in_code", {"answer": "private"})
    assert got["in_code"] is True and board_in_code.read(root) is True and cards(host) == []
    assert [(r["answer"], r["visibility"]) for r in event_log.read(root) if r["event"] == event_log.BOARD_IN_CODE_ANSWERED] == [("private", "unknown")]


def test_public_goes_on_to_the_publish_question_and_the_answer_there_is_the_same_command(host, code):
    git(host.projects.current().root, "remote", "set-url", "origin", "git@gitlab.example.com:acme/app.git")
    look(host)
    (row,) = cards(host)
    assert row["step"] == "private"                                                                # Public sends nothing: the page asks the publish question (the row carries its words)
    host.command("ideas.in_code", {"answer": "off"})
    assert board_in_code.read(host.projects.current().root) is False and cards(host) == []


# -- F.3: found public since ---------------------------------------------------------------------------------------------------------

def test_a_repository_found_public_since_throws_the_card_again_with_the_hold(host, code, monkeypatch):
    root = host.projects.current().root
    look(host)
    assert cards(host) == []                                                                       # private: it goes, nothing is asked
    code["code"] = 200
    a_day_passes(root)                                                                             # a day has passed: the look is asked again
    toasts = []
    host.projects.current().toast = lambda message, **kw: toasts.append(message)
    got = host.board_in_code.run(host.projects.current(), _State())
    assert got["found_public"] is True and toasts == [board_in_code.HELD]
    (row,) = cards(host)
    assert row["step"] == "publish" and row["held"] == board_in_code.HELD
    assert board_in_code.push_hold(root) == board_in_code.HELD
    host.command("ideas.in_code", {"answer": "off"})
    assert cards(host) == [] and board_in_code.push_hold(root) == ""


def test_the_card_is_not_in_a_demo(host, code):
    code["code"] = 200
    look(host)
    assert len(cards(host)) == 1
    host.ideas.host.demo = True
    assert host.ideas.in_code_rows() == []


def test_the_card_is_not_in_a_folder_with_no_history(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert Orkboard(plain).ideas.in_code_rows() == []


# -- C.4: the switch ---------------------------------------------------------------------------------------------------------------

def test_the_switch_in_a_public_repository_asks_f_first_and_offers_no_rules(host, code):
    code["code"] = 200
    s = host.command("rules.switch", {})
    assert s["show"] and s["state"] == "ask" and not s["on"]
    assert s["question"]["step"] == "publish" and s["question"]["text"] == ASK and s["question"]["words"]["publish"] == "Publish the Board" and s["question"]["words"]["off"] == "Keep the Board off the repository"
    with pytest.raises(Exception) as got:
        host.command("rules.write", {})
    assert str(got.value) == switch.ANSWER_FIRST and not (host.projects.current().root / "AGENTS.md").exists()


def test_the_switch_in_a_repository_orkboard_cannot_read_asks_if_it_is_private_first(host, code):
    git(host.projects.current().root, "remote", "set-url", "origin", "git@gitlab.example.com:acme/app.git")
    s = host.command("rules.switch", {})
    assert s["state"] == "ask" and s["question"]["step"] == "private" and s["question"]["ask"] == "Is this repository private?" and s["question"]["words"]["private"] == "Private"


def test_the_switch_with_the_board_kept_off_says_the_rules_would_find_no_board_and_offers_nothing(host, code):
    code["code"] = 200
    board_in_code.write(host.projects.current().root, False)
    s = host.command("rules.switch", {})
    assert s["state"] == "off" and s["status"] == "The Board is kept off this repository: the rules would find no Board" and s["question"] is None
    with pytest.raises(Exception) as got:
        host.command("rules.write", {})
    assert "the rules would find no Board" in str(got.value)


def test_the_switch_with_the_yes_writes_the_rules_as_before_in_a_public_repository(host, code):
    code["code"] = 200
    root = host.projects.current().root
    ideas.save_goal(host.ideas.root(), None, "Tech", "About Tech", None, "normal", craft="engineering")
    board_in_code.write(root, True)
    s = host.command("rules.switch", {})
    assert s["state"] == "ready" and s["question"] is None and s["write"] == "Write the rules"
    got = host.command("rules.write", {})
    assert got["ok"] and "AGENTS.md" in got["written"]
    assert agent_rules.has_rules(host.ideas.state_dir / "board")


def test_the_switch_in_a_private_repository_is_as_it_was(host, code):
    s = host.command("rules.switch", {})
    assert s["state"] == "ready" and s["question"] is None and s["status"] == ""


# -- E: from a terminal -------------------------------------------------------------------------------------------------------------

@pytest.fixture
def work(tmp_path, code, monkeypatch):
    """A plain clone-like folder with a GitHub remote, the working folder."""
    root = tmp_path / "shop"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@x")
    git(root, "config", "user.name", "T")
    (root / "app.py").write_text("x = 1\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "start")
    git(root, "remote", "add", "origin", "https://github.com/acme/shop.git")
    monkeypatch.chdir(root)
    return root


def ob(*argv: str) -> int:
    return board_cli.run(list(argv))


def test_init_in_a_public_repository_refuses_in_words_naming_both_answers(work, code, capsys):
    code["code"] = 200
    assert ob("init") == 1
    err = capsys.readouterr().err
    assert "This repository is public." in err and ASK in err and "init --publish" in err and "publish the Board and write the rules" in err
    assert "init --keep-off" in err and "keep the Board off the repository" in err
    assert not (work / "AGENTS.md").exists() and board_in_code.read(work) is None


def test_init_in_a_repository_it_cannot_read_says_so(work, code, capsys):
    git(work, "remote", "set-url", "origin", "git@gitlab.example.com:acme/shop.git")
    assert ob("init") == 1
    assert "Orkboard cannot read whether this repository is private." in capsys.readouterr().err


def test_init_publish_writes_the_yes_first_says_what_it_means_and_then_the_rules(work, code, capsys):
    code["code"] = 200
    assert ob("init", "--publish") == 0
    out = capsys.readouterr().out
    assert "wrote orkcraft.toml: in_code = true. " + ASK in out and "wrote AGENTS.md" in out
    assert out.index("in_code = true") < out.index("wrote AGENTS.md")
    assert board_in_code.read(work) is True and agent_rules.has_rules(work)
    assert ob("init") == 0                                                                         # answered: no refusal any more


def test_init_publish_in_a_private_repository_does_not_say_it_is_public(work, code, capsys):
    assert ob("init", "--publish") == 0
    out = capsys.readouterr().out
    assert "in_code = true. The Board goes into this repository." in out and "public" not in out.split("in_code = true.")[1].split("\n")[0]


def test_init_keep_off_writes_the_no_and_no_rules(work, code, capsys):
    code["code"] = 200
    assert ob("init", "--keep-off") == 0
    out = capsys.readouterr().out
    assert "in_code = false" in out and "the rules would find no Board" in out
    assert board_in_code.read(work) is False and not (work / "AGENTS.md").exists() and not (work / "CLAUDE.md").exists()
    assert ob("init") == 1 and "the rules would find no Board" in capsys.readouterr().err        # kept off: a later init says so
    assert not (work / "AGENTS.md").exists()


def test_init_with_both_answers_is_a_bad_call(work, code, capsys):
    assert ob("init", "--publish", "--keep-off") == 2
    assert "two answers" in capsys.readouterr().err and board_in_code.read(work) is None


# -- F.4: a goal kept off -----------------------------------------------------------------------------------------------------------

def _party(host):
    root = host.ideas.root()
    slug, _new = ideas.save_goal(root, None, "Tech", "About Tech", None, "normal", craft="engineering")
    return slug


def test_the_card_offers_keeping_a_goal_off_only_in_a_public_repository_with_the_yes(host, code):
    root = host.projects.current().root
    assert host.snapshot()["keep_off_offered"] is False                                            # private
    code["code"] = 200
    look(host)
    host.ideas._cache = None
    assert host.snapshot()["keep_off_offered"] is False                                            # public, not answered
    board_in_code.write(root, True)
    host.ideas._cache = None
    assert host.snapshot()["keep_off_offered"] is True
    board_in_code.write(root, False)
    host.ideas._cache = None
    assert host.snapshot()["keep_off_offered"] is False


def test_a_repository_with_no_remote_offers_no_line_whatever_was_said(fake_repo, code):
    h = Orkboard(fake_repo)
    board_in_code.write(fake_repo, True)
    h.ideas._cache = None
    assert h.snapshot()["keep_off_offered"] is False


def test_a_new_goal_sent_with_keep_off_is_stored_by_board_in_code_and_the_other_is_not(host, code):
    root, state = host.projects.current().root, host.ideas.state_dir
    code["code"] = 200
    look(host)
    board_in_code.write(root, True)
    party = _party(host)
    kept = host.command("ideas.add", {"text": "rotate the signing key", "party": party, "keep_off": True})["slug"]
    plain = host.command("ideas.add", {"text": "add a score board", "party": party})["slug"]
    assert board_in_code.qualifies(state, kept) and not board_in_code.qualifies(state, plain)
    assert board_in_code.kept_off(root, state, kept) is True and board_in_code.kept_off(root, state, plain) is False
    nodes = {n["slug"]: n for n in host.command("ideas.map", {})["nodes"]}
    assert nodes[kept]["kept_off"] == "Kept off the repository: on this computer only" and "kept_off" not in nodes[plain]


# -- D: another tool holds a goal ---------------------------------------------------------------------------------------------------

def test_a_goal_another_tool_holds_says_by_whom_and_until_when_on_its_row(host, code):
    root, state = host.projects.current().root, host.ideas.state_dir
    party = _party(host)
    held = host.command("ideas.add", {"text": "add a score board", "party": party})["slug"]
    free = host.command("ideas.add", {"text": "fix the menu", "party": party})["slug"]
    until = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    goal_take.cache_set(root, {held: {"by": "codex", "kind": "tool", "until": until}}, "Orkboard on this computer")
    try:
        nodes = {n["slug"]: n for n in host.command("ideas.map", {})["nodes"]}
        want = goal_take.line_of({"by": "codex", "until": until})
        assert nodes[held]["taken"] == want and want.startswith("Taken by codex until ") and "taken" not in nodes[free]
    finally:
        goal_take.cache_clear(root)
    assert "taken" not in {n["slug"]: n for n in host.command("ideas.map", {})["nodes"]}[held]


# -- the glossary -------------------------------------------------------------------------------------------------------------------

def test_the_words_come_from_the_glossary():
    t = lexicon.term
    assert t("in_code") == "the Board in the code" and t("in_code_public") == ASK
    assert t("in_code_pages") == "<n> pages of the Board are already in its history"
    assert (t("publish_board"), t("keep_board_off"), t("is_private"), t("repo_private"), t("repo_public")) == ("Publish the Board", "Keep the Board off the repository", "Is this repository private?", "Private", "Public")
    assert t("keep_goal_off") == "Keep off the repository" and t("goal_kept_off") == "Kept off the repository: on this computer only"
    assert t("rules_find_no_board") == "The Board is kept off this repository: the rules would find no Board"
    assert t("taken_by") == goal_take.TAKEN_LINE.replace("{by}", "<by>").replace("{time}", "<time>")
