"""Settings' switch for the Board's branch (gui/board_switch.py, spec 137 E, decisions §244.1, §244.11): shown with a remote to keep the Board on,
refused in words on a public repository, written only on the person's yes, remembered on *Not now*, and saying who holds the Board. No network:
the HTTP getter is a fake."""
from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from orkboard.gui import board_switch as bsw
from orkboard.realm import board_branch, lexicon


def repo(path, remote="git@github.com:acme/shop.git"):
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    if remote:
        subprocess.run(["git", "remote", "add", "origin", remote], cwd=path, check=True)
    return path


def host(root, state, status=None):
    p = SimpleNamespace(root=root, ideas=SimpleNamespace(state_dir=state))
    sync = SimpleNamespace(status=lambda q: status or {})
    return SimpleNamespace(project=p, board_sync=sync)


def test_the_switch_is_shown_with_a_remote_and_not_without_one_or_a_project(tmp_path):
    root = repo(tmp_path / "shop")
    s = bsw.BoardSwitch(host(root, tmp_path / "st")).switch()
    assert s["show"] and not s["on"] and s["label"] == "Keep the Board in the repository" and "must be private" in s["line"]
    assert not bsw.BoardSwitch(host(repo(tmp_path / "x", remote=""), tmp_path / "st2")).switch()["show"]
    assert not bsw.BoardSwitch(SimpleNamespace(project=None)).switch()["show"]


def test_turn_on_writes_the_table_after_the_private_check_and_nothing_before(tmp_path, monkeypatch):
    root = repo(tmp_path / "shop")
    (root / "orkcraft.toml").write_text('[gate]\nalways = ["x"]\n')
    sw = bsw.BoardSwitch(host(root, tmp_path / "st"))
    monkeypatch.setattr(bsw, "http_status", lambda url: 200)
    with pytest.raises(ValueError, match="goes only to a private repository"):
        sw.turn_on()
    assert board_branch.read_config(root) is None and "[board]" not in (root / "orkcraft.toml").read_text()
    monkeypatch.setattr(bsw, "http_status", lambda url: 404)
    got = sw.turn_on()
    assert got["ok"] and got["branch"] == "orkboard/board"
    text = (root / "orkcraft.toml").read_text()
    assert text.startswith('[gate]\nalways = ["x"]\n') and text.count("[board]") == 1
    assert board_branch.read_config(root) == board_branch.BoardConfig("origin", "orkboard/board")
    s = sw.switch()
    assert s["on"] and "orkboard/board" in s["status"]
    assert sw.turn_on()["ok"] and (root / "orkcraft.toml").read_text().count("[board]") == 1


def test_a_remote_not_on_github_goes_on_with_the_line_that_it_must_be_private(tmp_path, monkeypatch):
    root = repo(tmp_path / "shop", remote="/srv/git/shop.git")
    monkeypatch.setattr(bsw, "http_status", lambda url: pytest.fail("asked GitHub about a remote that is not on it"))
    got = bsw.BoardSwitch(host(root, tmp_path / "st")).turn_on()
    assert got["ok"] and "must be private" in got["line"] and board_branch.read_config(root) is not None


def test_not_now_is_remembered_and_the_switch_stays(tmp_path):
    root = repo(tmp_path / "shop")
    sw = bsw.BoardSwitch(host(root, tmp_path / "st"))
    assert sw.not_now() == {"ok": True}
    s = sw.switch()
    assert s["show"] and s["asked"] and not s["on"] and board_branch.read_config(root) is None


def test_it_says_who_holds_the_board_and_what_was_kept_aside(tmp_path):
    root = repo(tmp_path / "shop")
    board_branch.turn_on(root)
    held = {"board_held": {"by": "run-1", "kind": "cloud run", "until": "2026-11-04T10:00:00+00:00"},
            "board_aside": {"since": "2026-11-04T09:00:00+00:00", "path": "x"}}
    s = bsw.BoardSwitch(host(root, tmp_path / "st", held)).switch()
    assert s["held"] == "A cloud run has the Board: it gives it back when it ends (at most 30 min)"
    assert s["aside"].startswith("Another worker had the Board while you were offline: your changes since ") and s["aside"].endswith("are kept aside")
    held["board_held"]["kind"] = "computer"
    assert "Another computer has the Board" in bsw.BoardSwitch(host(root, tmp_path / "st", held)).switch()["held"]


def test_the_words_are_in_the_glossary():
    assert lexicon.term("board_branch") == "the Board's branch" and lexicon.term("holds") == "holds the Board"
    assert lexicon.term("cloud_run") == "cloud run" and lexicon.term("cloud_run", many=True) == "cloud runs"
