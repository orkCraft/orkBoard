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


# -- the cloud run's settings (spec 137 D) -----------------------------------------------------------------------------------

def test_the_cloud_run_is_offered_once_the_board_is_kept_and_choosing_writes_nothing(tmp_path):
    from orkboard.realm import cloud_run
    root = repo(tmp_path / "shop")
    sw = bsw.BoardSwitch(host(root, tmp_path / "st"))
    assert "cloud" not in sw.switch(), "no cloud run before the Board is kept in the repository"
    with pytest.raises(ValueError, match="Turn on"):
        sw.cloud_write({})
    board_branch.turn_on(root)
    c = sw.switch()["cloud"]
    assert (c["secret"], c["schedule"], c["usd"], c["set_up"], c["workflow"]) == ("oauth", "2h", 1.0, False, "none")
    assert [x["id"] for x in c["secrets"]] == ["oauth", "api_key"] and [x["label"] for x in c["schedules"]] == ["Every 2 hours", "Never"]
    assert c["ceiling"] == "At most $1 a cloud run" and c["minute"] == "About a minute of Actions when it finds nothing" and c["runs_a_day"] == 12
    assert "Planned: the work starts on your computer" in c["line"] and "never does the work" in c["line"]
    assert "shares this week's limits" in c["secrets"][0]["line"] and "by the token" in c["secrets"][1]["line"]
    assert not (root / ".github").exists() and cloud_run.read_config(root) is None


def test_the_yes_writes_the_settings_and_the_workflow_into_the_project_and_says_to_commit_it(tmp_path):
    from orkboard.realm import cloud_run
    root = repo(tmp_path / "shop")
    board_branch.turn_on(root)
    sw = bsw.BoardSwitch(host(root, tmp_path / "st"))
    got = sw.cloud_write({"secret": "api_key", "schedule": "never", "usd": 2})
    assert got["ok"] and got["line"] == "Written to .github/workflows/orkboard.yml. Commit it to your default branch for the cloud run to start."
    assert cloud_run.read_config(root) == cloud_run.CloudConfig("api_key", "never", 2.0)
    text = (root / ".github/workflows/orkboard.yml").read_text()
    assert "secrets.ANTHROPIC_API_KEY" in text and "--usd 2" in text and "schedule:" not in text
    assert (root / "orkcraft.toml").read_text().count("[board]") == 1
    c = sw.switch()["cloud"]
    assert c["set_up"] and c["workflow"] == "ours" and c["current"] and c["secret"] == "api_key" and c["ceiling"] == "At most $2 a cloud run"
    sw.cloud_write({"secret": "oauth", "schedule": "2h"})                       # a new yes rewrites our own file
    assert "secrets.CLAUDE_CODE_OAUTH_TOKEN" in (root / ".github/workflows/orkboard.yml").read_text()


def test_a_workflow_of_the_persons_own_is_never_overwritten(tmp_path):
    root = repo(tmp_path / "shop")
    board_branch.turn_on(root)
    mine = root / ".github/workflows/orkboard.yml"
    mine.parent.mkdir(parents=True)
    mine.write_text("name: mine\n")
    sw = bsw.BoardSwitch(host(root, tmp_path / "st"))
    assert sw.switch()["cloud"]["workflow"] == "other"
    with pytest.raises(ValueError, match="file of your own"):
        sw.cloud_write({})
    assert mine.read_text() == "name: mine\n" and "[cloud_run]" not in (root / "orkcraft.toml").read_text()


def test_the_cloud_run_words_are_in_the_glossary():
    for key, word in (("planned", "Planned"), ("cloud_secret", "the secret that pays"), ("cloud_ceiling", "ceiling")):
        assert lexicon.term(key) == word, key
    rows = {key: (w, was) for key, w, was in lexicon.glossary()}
    assert rows["cloud_ceiling"] == ("ceiling", "") and lexicon.term("cloud_ceiling", many=True) == "ceilings"
