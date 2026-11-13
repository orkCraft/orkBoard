"""The computer tells the phone its project's repository at pairing (docs/specs/136 C.1): `/api/pair`'s answer carries `remote`, `owner/name` of the shown project's `origin` when it is on
github.com, "" when it has none, so the phone's repository field starts filled."""
from __future__ import annotations

import asyncio
import subprocess
from types import SimpleNamespace

import pytest

from orkboard.gui import phone_journal
from tests.test_phones import _https, _listening, _serve


def _run(url: str, code: int = 0):
    def run(cmd, **kw):
        return SimpleNamespace(stdout=url.encode(), returncode=code)
    return run


@pytest.mark.parametrize("url,want", [
    ("git@github.com:me/shop.git\n", "me/shop"),
    ("https://github.com/me/shop.git\n", "me/shop"),
    ("https://github.com/me/shop\n", "me/shop"),
    ("https://user:tok@github.com/me/my.shop/\n", "me/my.shop"),
    ("ssh://git@github.com/me/shop.git\n", "me/shop"),
    ("https://gitlab.com/me/shop.git\n", ""),
    ("/some/bare/repo\n", ""),
    ("", ""),
])
def test_the_repository_is_read_from_a_github_origin(tmp_path, url, want):
    assert phone_journal.github_repo(tmp_path, _run(url)) == want


def test_no_origin_is_no_repository(tmp_path):
    assert phone_journal.github_repo(tmp_path, _run("", 2)) == ""
    assert phone_journal.github_repo(tmp_path, lambda *a, **k: (_ for _ in ()).throw(OSError("no git"))) == ""


@pytest.mark.asyncio
async def test_the_pairing_answer_names_the_projects_repository(fake_repo):
    subprocess.run(["git", "remote", "add", "origin", "git@github.com:me/shop.git"], cwd=str(fake_repo), check=True, capture_output=True)
    server, task = await _serve(fake_repo)
    try:
        offer = server.host.command("phones.pair")
        await _listening(server)
        status, body, _ = await asyncio.to_thread(_https, offer["address"], "POST", "/api/pair", {"code": offer["code"], "name": "Test phone"})
        assert status == 200 and body["remote"] == "me/shop" and body["token"] and body["id"]
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)


@pytest.mark.asyncio
async def test_a_project_without_a_remote_says_so_with_an_empty_one(fake_repo):
    server, task = await _serve(fake_repo)
    try:
        offer = server.host.command("phones.pair")
        await _listening(server)
        status, body, _ = await asyncio.to_thread(_https, offer["address"], "POST", "/api/pair", {"code": offer["code"], "name": "Test phone"})
        assert status == 200 and body["remote"] == ""
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)
