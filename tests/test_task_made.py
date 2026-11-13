"""Spec 142 part D (docs/specs/142-a-cards-window-where-it-has-something-to-show.md, decisions §249.3): what a task made, by its craft, read by code (realm/task_made.py): a numstat and its three files, the first image
a task's commits added, an image's size, the kinds that come from what the Board holds, and nothing leaving `craft_made` absent. The git kinds run against a real repository in a temp folder."""
from __future__ import annotations

import struct
import subprocess
import zlib
from pathlib import Path

from orkboard.realm import task_made


def png(w: int, h: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
    raw = b"".join(b"\x00" + b"\x00\x00\x00\xff" * w for _ in range(h))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def test_the_first_image_a_commit_added_or_changed_is_found_a_deleted_one_is_not():
    text = "M\tsrc/a.py\nD\told/gone.png\nA\tart/hero.PNG\nA\tart/second.gif\n"
    assert task_made.first_image(text) == "art/hero.PNG"
    assert task_made.first_image("M\tdocs/a.md\nA\tsrc/b.py\n") == "" and task_made.first_image("") == ""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def repo_with(tmp_path: Path, image: bool) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "dev")
    (repo / "a.py").write_text("one\n")
    git(repo, "add", "."), git(repo, "commit", "-qm", "start")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "a.py").write_text("one\ntwo\nthree\n")
    (repo / "b.py").write_text("x\n" * 9)
    if image:
        (repo / "art").mkdir()
        (repo / "art" / "hero.png").write_bytes(png(16, 24))
    git(repo, "add", "."), git(repo, "commit", "-qm", "the work")
    return repo, base, git(repo, "rev-parse", "HEAD")


def test_a_merged_tech_task_reads_its_files_from_its_commits_and_is_cached_by_its_tip(tmp_path):
    repo, _base, tip = repo_with(tmp_path, image=False)
    task = {"id": "k1", "state": "merged", "commit": tip, "subjects": ["the work"]}
    got = task_made.git_made(repo, "lobby", task, "tech", lambda c, p: "")
    assert got == {"kind": "diff", "files": [{"path": "b.py", "added": 9, "removed": 0}, {"path": "a.py", "added": 2, "removed": 0}]}
    (repo / "b.py").unlink()                                                    # the same tip is not read again
    assert task_made.git_made(repo, "lobby", task, "tech", lambda c, p: "") is got


def test_a_task_at_review_reads_its_branch_since_its_base_and_art_finds_the_image_it_added(tmp_path):
    repo, base, tip = repo_with(tmp_path, image=True)
    git(repo, "branch", "idea/lobby/k2", tip)
    task = {"id": "k2", "state": "review", "base": base}
    asked = []
    got = task_made.git_made(repo, "lobby", task, "art", lambda c, p: asked.append((c, p)) or f"/media/_asset/{c}/{p}")
    assert got == {"kind": "asset", "url": f"/media/_asset/{tip}/art/hero.png", "w": 16, "h": 24, "name": "hero.png"} and asked == [(tip, "art/hero.png")]
    assert task_made.git_made(repo, "lobby", task, "tech", lambda c, p: "")["files"][0]["path"] == "b.py"


def test_the_map_gives_each_task_its_partys_kind_and_none_where_a_craft_has_none(tmp_path):
    from orkboard.gui.ideas_map import MapMixin

    repo, _base, tip = repo_with(tmp_path, image=False)

    class Host:
        repo_root = str(repo)

    class Stub(MapMixin):
        host = Host()
        state_dir = tmp_path / "state"

        def main_checks_now(self):
            return {"ship": [{"name": "Tests", "state": "passed", "words": ""}]}

    def node(slug, goal, shot=None):
        return {"slug": slug, "goal": goal, "tasks": [{"id": "k1", "state": "merged", "commit": tip, "subjects": ["the work"], "shot": shot}, {"id": "k2", "state": "running"}]}

    got = {"goals": [{"slug": g, "party_craft": c} for g, c in (("code", "tech"), ("looks", "design"), ("rel", "release"), ("ops", "run"), ("bare", ""))],
           "nodes": [node("lobby", "code"), node("pic", "looks", {"id": "p", "file": "shot.png", "url": "/media/pic/p/shot.png?s=1"}), node("ship", "rel"), node("watch", "ops"), node("none", "bare"), node("flat", "looks")]}
    Stub().made_for(got)
    by = {n["slug"]: n["tasks"] for n in got["nodes"]}
    assert by["lobby"][0]["craft_made"]["kind"] == "diff" and "craft_made" not in by["lobby"][1], "a task at work has none"
    assert by["pic"][0]["craft_made"] == {"kind": "screen", "before": "", "after": "/media/pic/p/shot.png?s=1"}
    assert by["ship"][0]["craft_made"] == {"kind": "checks", "items": [{"name": "Tests", "state": "passed"}]}
    assert "craft_made" not in by["watch"][0] and "craft_made" not in by["none"][0] and "craft_made" not in by["flat"][0], "Run has no kind yet; a party with no craft none; no shot none"
