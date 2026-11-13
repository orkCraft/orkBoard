"""Spec 102 A (docs/specs/102-the-other-maps-and-picking-on-them.md §1) on the host: `ideas.screens` (the screens of the app at dev's head along their flow, each with
its newest picture, and the project's segments with their pains' places) and `ideas.pain_pin` (a pain pinned to a screen or a step, or taken off it). Keys and data,
never words but a refusal's.

These tests compose the mixin onto the host the way the lead's wiring does (the `host` fixture): they pass without that wiring in `gui/ideas.py`.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.gui.ideas_screens import ScreensMixin, screens_commands
from orkboard.realm import idea_lens, idea_shots, ideas

PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32
COMMANDS = {"ideas.screens", "ideas.pain_pin"}
APP = {
    "package.json": json.dumps({"dependencies": {"react-router-dom": "6"}}),
    "src/App.jsx": 'import { Routes, Route } from "react-router-dom";\nimport Home from "./Home";\nimport Cart from "./Cart";\n'
                   'export default () => <Routes><Route path="/" element={<Home />} /><Route path="/cart" element={<Cart />} /></Routes>;\n',
    "src/Home.jsx": 'export default () => <Link to="/cart">Cart</Link>;\n',
    "src/Cart.jsx": "export default () => null;\n",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def commit(repo: Path, files: dict[str, str]) -> str:
    for name, text in files.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "files")
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def host(fake_repo) -> Orkboard:
    git(fake_repo, "checkout", "-q", "-b", "dev")
    commit(fake_repo, APP)
    h = Orkboard(fake_repo)
    assert isinstance(h.ideas, ScreensMixin) and set(screens_commands(h.ideas)) <= set(h.commands)      # wired: the host's bases and its table
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def test_the_screens_come_with_their_flow_and_the_segments_with_their_pains_places(host):
    idea_lens.keep_segment(host.ideas.state_dir, "Shop owners", "Orders get lost", on="cart")
    idea_lens.keep_segment(host.ideas.state_dir, "Shop owners", "Refunds take a week")
    got = host.command("ideas.screens", {})
    assert got["head"] == git(Path(host.ideas.host.repo_root), "rev-parse", "dev") and got["source"] == "react-router" and got["entry"] == "home"
    assert [(s["id"], s["name"], s["path"], s["file"]) for s in got["screens"]] == [("home", "Home", "/", "src/Home.jsx"), ("cart", "Cart", "/cart", "src/Cart.jsx")]
    assert got["links"] == [{"from": "home", "to": "cart"}] and got["steps"] == [["home"], ["cart"]] and got["loose"] == [] and got["more"] == 0
    assert got["segments"] == [{"segment": "Shop owners", "pains": [{"text": "Refunds take a week", "on": ""}, {"text": "Orders get lost", "on": "cart"}]}]
    json.dumps(got)


def test_a_picture_comes_with_its_signed_address_and_a_kept_screen_with_its_id(host):
    repo, state = Path(host.ideas.host.repo_root), host.ideas.state_dir
    sha = commit(repo, {"src/Cart.jsx": "export default () => 1;\n"})
    folder = ideas.state_folder(state, "pay")
    folder.mkdir(parents=True)
    (repo / "p.png").write_bytes(PNG)
    shot = idea_shots.store(state, "pay", "k1", 1, repo / "p.png")
    (folder / "plan.json").write_text(json.dumps({"tasks": [{"id": "k1", "state": "merged", "commit": sha, "shot": shot}]}))
    sid = idea_lens.keep_screen(state, PNG, "Home")
    by = {s["id"]: s for s in host.command("ideas.screens", {})["screens"]}
    assert by["cart"]["picture"]["kind"] == "shot" and by["cart"]["picture"]["goal"] == "pay"
    assert by["cart"]["picture"]["url"].startswith("/media/pay/k1-shot-r1/shot.png?s=")
    assert by["home"]["picture"]["kind"] == "lens" and by["home"]["picture"]["id"] == sid and "url" not in by["home"]["picture"]


def test_a_pain_is_pinned_to_a_screen_or_a_step_moved_and_taken_off(host):
    idea_lens.keep_segment(host.ideas.state_dir, "Shop owners", "Orders get lost")
    got = host.command("ideas.pain_pin", {"segment": "Shop owners", "pain": "Orders get lost", "on": "cart"})
    assert got == {"ok": True, "segments": [{"segment": "Shop owners", "pains": [{"text": "Orders get lost", "on": "cart"}]}]}
    assert host.command("ideas.screens", {})["segments"] == got["segments"]
    assert host.command("ideas.pain_pin", {"segment": "shop owners", "pain": "orders get LOST", "on": "step:1"})["segments"][0]["pains"] == [{"text": "Orders get lost", "on": "step:1"}]
    assert host.command("ideas.pain_pin", {"segment": "Shop owners", "pain": "Orders get lost", "on": ""})["segments"][0]["pains"] == [{"text": "Orders get lost", "on": ""}]
    assert json.loads((host.ideas.state_dir / "segments.json").read_text())["segments"][0]["pains"] == ["Orders get lost"]     # no place, a string again


def test_a_pin_is_refused_for_a_pain_or_a_screen_that_is_gone_in_plain_words(host):
    idea_lens.keep_segment(host.ideas.state_dir, "Shop owners", "Orders get lost")
    for args, why in (({"segment": "Nobody", "pain": "Orders get lost", "on": "cart"}, "That pain is gone"),
                      ({"segment": "Shop owners", "pain": "Another", "on": "cart"}, "That pain is gone"),
                      ({"segment": "Shop owners", "pain": "Orders get lost", "on": "checkout"}, "That screen is gone"),
                      ({"segment": "Shop owners", "pain": "Orders get lost", "on": "step:9"}, "That screen is gone"),
                      ({"segment": "", "pain": "Orders get lost", "on": "cart"}, "segment is missing"),
                      ({"segment": "Shop owners", "pain": "Orders get lost", "on": 3}, "on is not text")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.pain_pin", args)
    assert idea_lens.segments_placed(host.ideas.state_dir)[0]["pains"] == [{"text": "Orders get lost", "on": ""}]


def test_a_project_with_no_screen_answers_none_and_no_pin_holds(fake_repo):
    git(fake_repo, "checkout", "-q", "-b", "dev")
    h = Orkboard(fake_repo)
    got = h.command("ideas.screens", {})
    assert got["screens"] == [] and got["links"] == [] and got["steps"] == [] and got["entry"] == "" and got["segments"] == []
    idea_lens.keep_segment(h.ideas.state_dir, "Shop owners", "Orders get lost")
    with pytest.raises(CommandError, match="That screen is gone"):
        h.command("ideas.pain_pin", {"segment": "Shop owners", "pain": "Orders get lost", "on": "home"})
    assert h.command("ideas.pain_pin", {"segment": "Shop owners", "pain": "Orders get lost", "on": ""})["ok"]


def test_the_commands_are_the_two_named():
    class Fake:
        screens = pain_pin = staticmethod(lambda a: {})
    assert set(screens_commands(Fake)) == COMMANDS
