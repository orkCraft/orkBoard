"""The project's journal on its own remote (realm/remote_journal.py, decisions §229): off unless asked, packed small and with
no secret, sent by git's plumbing to a branch of its own with the working tree untouched, and `orkboard drive journal`."""
from __future__ import annotations

import datetime as dt
import gzip
import json
import subprocess
from pathlib import Path

import pytest

from orkboard.gui import drive
from orkboard.realm import event_log, remote_journal as rj

NOW = dt.datetime(2026, 11, 3, 12, 0, 0)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def town(tmp_path: Path):
    origin, repo = tmp_path / "origin.git", tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(origin)], check=True, capture_output=True)
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "t@x")
    git(repo, "config", "user.name", "T")
    (repo / ".gitignore").write_text(".orkcraft/\n")
    (repo / "a.txt").write_text("one\n")
    (repo / "orkcraft.toml").write_text("[journal]\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "start")
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "origin", "main")
    state = repo / ".orkcraft"
    goal = state / "ideas" / "jump"
    goal.mkdir(parents=True)
    (goal / "state.json").write_text(json.dumps({"state": "failed", "error": "the gate was red"}))
    broken = state / "ideas" / "broken"
    broken.mkdir()
    (broken / "state.json").write_text("{not json")
    (state / "drive.json").write_text('{"url": "http://127.0.0.1:1/?token=abc"}')
    logs = state / "logs" / "2026-11-03" / "board"
    logs.mkdir(parents=True)
    (logs / "calls.jsonl").write_text(json.dumps({"at": "2026-11-03T08:00:00", "tool": "claude", "model": "sonnet", "step": "talk_round",
                                                  "tokens": 10, "cost": 0.1, "code": 0, "idea": "jump"}) + "\n")
    (logs / "001-ork.json.gz").write_bytes(gzip.compress(b'{"prompt": "the code"}'))
    event_log.record(repo, event_log.STOP_ALL, count=1, device="desktop")
    return repo, origin, state


def test_no_journal_table_is_off(tmp_path):
    assert rj.read_config(tmp_path) is None
    (tmp_path / "orkcraft.toml").write_text('[gate]\nrun = "pytest"\n')
    assert rj.read_config(tmp_path) is None


def test_a_config_reads_with_defaults_and_ignores_a_bad_value(tmp_path):
    (tmp_path / "orkcraft.toml").write_text("[journal]\n")
    assert rj.read_config(tmp_path) == rj.JournalConfig("origin", "orkboard/journal", 15, False)
    (tmp_path / "orkcraft.toml").write_text('[journal]\nremote = "up"\nevery = 0\nprompts = "yes"\nbranch = 3\n')
    assert rj.read_config(tmp_path) == rj.JournalConfig("up", "orkboard/journal", 15, False)
    (tmp_path / "orkcraft.toml").write_text('[journal]\nevery = 5\nprompts = true\n')
    c = rj.read_config(tmp_path)
    assert (c.every, c.prompts) == (5, True)


def test_pack_holds_the_listed_files_and_never_the_token(town):
    repo, _, state = town
    files = rj.pack(repo, state, NOW)
    assert set(files) == {"status.md", "events.jsonl", "spend.json", "spend.txt", "calls/2026-11-03-board.jsonl"}
    assert not any("drive" in n or ".env" in n for n in files)
    status = files["status.md"]
    assert "jump" in status and "failed" in status and "unreadable" in status
    assert "stop_all" in files["events.jsonl"]
    with_prompts = rj.pack(repo, state, NOW, prompts=True)
    assert isinstance(with_prompts["calls/2026-11-03-board-001-ork.json.gz"], bytes)


@pytest.mark.parametrize("secret", [
    "sk-" + "a" * 24, "sk-ant-" + "b" * 24, "ghp_" + "c" * 32, "github_pat_" + "d" * 32, "xoxb-1234567890-abc", "AKIA" + "A" * 16,
    "AIza" + "e" * 35, "-----BEGIN RSA PRIVATE KEY-----", "API_KEY = abcdefghijkl1234", 'password: "hunter2hunter2x"'])
def test_scrub_holds_back_each_secret_shape(secret):
    text, n = rj.scrub(f"fine\nhere is {secret} ok\nalso fine\n")
    assert n == 1 and secret not in text and rj.HELD in text and "fine\n" in text


def test_scrub_keeps_ordinary_lines():
    ordinary = "the token budget is low\nsk-short\npassword: no\nsecret = x\n"
    assert rj.scrub(ordinary) == (ordinary, 0)


def test_send_makes_the_branch_and_touches_nothing_of_the_person(town):
    repo, origin, state = town
    (repo / "a.txt").write_text("edited\n")
    before = (git(repo, "status", "--porcelain"), git(repo, "rev-parse", "HEAD"), git(repo, "branch", "--show-current"))
    cfg = rj.read_config(repo)
    got = rj.send(repo, state, cfg, NOW)
    assert got["sent"] is True and got["files"] == 5
    assert (git(repo, "status", "--porcelain"), git(repo, "rev-parse", "HEAD"), git(repo, "branch", "--show-current")) == before
    assert "status.md" in git(origin, "ls-tree", "--name-only", "orkboard/journal")
    assert "drive.json" not in git(origin, "ls-tree", "-r", "--name-only", "orkboard/journal")
    assert "Orkboard journal" in git(origin, "log", "-1", "--format=%s", "orkboard/journal")
    assert [e for e in event_log.read(repo) if e["event"] == event_log.JOURNAL_SENT]


def test_a_second_send_with_nothing_changed_sends_nothing(town):
    repo, origin, state = town
    cfg = rj.read_config(repo)
    assert rj.send(repo, state, cfg, NOW)["sent"]
    again = rj.send(repo, state, cfg, NOW)
    assert again == {"sent": False, "why": "nothing changed"}
    assert git(origin, "rev-list", "--count", "orkboard/journal").strip() == "1"


def test_a_push_to_no_remote_says_why_and_does_not_raise(town):
    repo, _, state = town
    got = rj.send(repo, state, rj.JournalConfig(remote="nowhere"), NOW)
    assert got["sent"] is False and got["why"] and len(got["why"]) <= 300
    ok = rj.send(repo, state, rj.JournalConfig(), NOW)          # the failed try left nothing behind that blocks the next
    assert ok["sent"] is True


def test_without_prompts_no_gz_goes_and_with_them_it_does(town):
    repo, origin, state = town
    rj.send(repo, state, rj.JournalConfig(prompts=False), NOW)
    assert ".json.gz" not in git(origin, "ls-tree", "-r", "--name-only", "orkboard/journal")
    rj.send(repo, state, rj.JournalConfig(branch="with", prompts=True), NOW)
    assert ".json.gz" in git(origin, "ls-tree", "-r", "--name-only", "with")


def test_due_respects_every(tmp_path):
    cfg = rj.JournalConfig(every=15)
    assert rj.due(tmp_path, cfg, NOW)
    rj._mark(tmp_path, NOW, {"sent": True})
    assert not rj.due(tmp_path, cfg, NOW + dt.timedelta(minutes=14))
    assert rj.due(tmp_path, cfg, NOW + dt.timedelta(minutes=15))
    assert rj.due(tmp_path, cfg, NOW, urgent=True)


def test_drive_journal_says_it_is_off_without_a_table(tmp_path, capsys):
    (tmp_path / ".git").mkdir()
    assert drive.main(["journal", "--folder", str(tmp_path), "--dry-run"]) == 0
    assert "[journal]" in capsys.readouterr().out


def test_drive_journal_dry_run_lists_and_sends_nothing(town, capsys):
    repo, origin, _ = town
    assert drive.main(["journal", "--folder", str(repo), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "status.md" in out and "bytes" in out and "held back" in out and "drive.json" not in out
    assert git(origin, "branch", "--list", "orkboard/journal").strip() == ""
