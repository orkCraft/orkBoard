"""The Board's branch (realm/board_branch.py, spec 137 A, decisions §244.1, §244.11–12): what goes and what never does, the scrub, the commit by
plumbing, the unpack, the config, the public check. No network: the HTTP getter is a fake."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from orkboard.realm import board_branch as bb

WIKI = "llm-wiki/general"
KEY = "sk-" + "a1B2c3D4e5F6g7H8i9J0k1L2"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def make_origin(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(origin)], check=True, capture_output=True)
    seed = tmp_path / "seed"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "t@x")
    git(seed, "config", "user.name", "T")
    (seed / "a.txt").write_text("one\n")
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "start")
    git(seed, "remote", "add", "origin", str(origin))
    git(seed, "push", "-q", "origin", "main")
    return origin


def make_clone(origin: Path, where: Path) -> Path:
    subprocess.run(["git", "clone", "-q", str(origin), str(where)], check=True, capture_output=True)
    git(where, "config", "user.email", "t@x")
    git(where, "config", "user.name", "T")
    (where / ".git" / "info" / "exclude").write_text(".orkcraft/\n")
    return where


def put(state: Path, rel: str, body: str | bytes) -> Path:
    f = state / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(body if isinstance(body, bytes) else body.encode())
    return f


def seed_board(state: Path) -> None:
    put(state, f"board/{WIKI}/pages/ideas/dark-mode.md", "# Dark mode\n")
    put(state, f"board/{WIKI}/pages/tracks/tech.md", "# Tech\n")
    put(state, f"board/{WIKI}/specs/one.md", "# Spec\n")
    put(state, "ideas/dark-mode/state.json", json.dumps({"state": "ready"}))
    put(state, "ideas/dark-mode/plan.json", json.dumps({"tasks": []}))
    put(state, "ideas/dark-mode/talk.jsonl", '{"who": "you", "text": "hi"}\n')
    put(state, "ideas/dark-mode/photos/1.jpg", b"\xff\xd8\xff" + b"0" * 64)
    put(state, "goals/tech/state.json", "{}")
    put(state, "roles/taskmaster.json", "{}")
    for n in ("kinds.json", "segments.json", "project.json", "cascades.json", "slices.json"):
        put(state, n, "{}")
    put(state, "checks.toml", "a = 1\n")
    put(state, "canvases.jsonl", "")


NEVERS = ("ideas/dark-mode/secrets.json", "ideas/dark-mode/worktree/x.txt", "ideas/dark-mode/sign-in/token", "sign-in/token",
          "drive.json", "worktrees/t/x.txt", "logs/2026/calls.jsonl", "usage/u.json", "crashes/c.json", "repair/r.json", "screens/s.png",
          "claims.json", "journal.json", "goals/tech/secrets.json", "board/llm-wiki/general/pages/ideas/secrets.json",
          "board/.git", "random.txt", "ideas.json", "inbox.json", "taken.json", "other/x.json", "board-sync.json")


# -- the allow list (A.2) ------------------------------------------------------------------------------------------

def test_what_goes_and_what_never_does(tmp_path):
    state = tmp_path / ".orkcraft"
    seed_board(state)
    for n in NEVERS:
        put(state, n, "x")
    files, held = bb.pack(state, WIKI)
    assert held == []
    assert {"board/llm-wiki/general/pages/ideas/dark-mode.md", "board/llm-wiki/general/pages/tracks/tech.md", "board/llm-wiki/general/specs/one.md",
            "ideas/dark-mode/state.json", "ideas/dark-mode/plan.json", "ideas/dark-mode/talk.jsonl", "ideas/dark-mode/photos/1.jpg",
            "goals/tech/state.json", "roles/taskmaster.json", "kinds.json", "segments.json", "project.json", "cascades.json", "slices.json",
            "checks.toml", "canvases.jsonl"} == set(files)


@pytest.mark.parametrize("rel", NEVERS)
def test_a_never_file_and_a_file_not_listed_stay_home(tmp_path, rel):
    state = tmp_path / ".orkcraft"
    seed_board(state)
    put(state, rel, "x")
    files, _ = bb.pack(state, WIKI)
    assert rel not in files and not bb.allowed(rel, WIKI)


def test_never_is_checked_again_over_a_listed_folder(tmp_path):
    """A `secrets.json` inside `ideas/<slug>/` stays home, and so does anything under a worktree or sign-in folder of a listed one."""
    state = tmp_path / ".orkcraft"
    seed_board(state)
    put(state, "ideas/dark-mode/secrets.json", '{"k": "v"}')
    put(state, "ideas/dark-mode/worktrees/a/b.txt", "x")
    put(state, "ideas/dark-mode/sign-in/c.json", "{}")
    files, _ = bb.pack(state, WIKI)
    assert not [p for p in files if "secrets" in p or "worktree" in p or "sign-in" in p]
    assert "ideas/dark-mode/state.json" in files
    assert "secrets.json" in bb.NEVER and "worktrees/" in bb.NEVER and bb.allowed("lease.json")


def test_a_path_that_leaves_the_folder_is_never_listed():
    for rel in ("../x.json", "ideas/../../x", "/etc/passwd", "ideas//x", "ideas/./x"):
        assert not bb.allowed(rel, WIKI)


def test_a_symlink_is_not_followed(tmp_path):
    state = tmp_path / ".orkcraft"
    seed_board(state)
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    (state / "ideas" / "dark-mode" / "link.json").symlink_to(outside)
    (state / "kinds.json").unlink()
    (state / "kinds.json").symlink_to(outside)
    files, _ = bb.pack(state, WIKI)
    assert "ideas/dark-mode/link.json" not in files and "kinds.json" not in files


def test_a_photo_over_the_limit_is_held_back_and_said(tmp_path):
    state = tmp_path / ".orkcraft"
    seed_board(state)
    put(state, "ideas/dark-mode/photos/2.jpg", b"0" * (bb.PHOTO_MAX + 1))
    put(state, "ideas/dark-mode/photos/3.jpg", b"0" * bb.PHOTO_MAX)
    files, held = bb.pack(state, WIKI)
    assert held == ["ideas/dark-mode/photos/2.jpg"]
    assert "ideas/dark-mode/photos/2.jpg" not in files and "ideas/dark-mode/photos/3.jpg" in files


def test_the_lease_is_not_read_from_disk(tmp_path):
    state = tmp_path / ".orkcraft"
    seed_board(state)
    put(state, "lease.json", "{}")
    assert "lease.json" not in bb.pack(state, WIKI)[0]


# -- the scrub (A.2) ------------------------------------------------------------------------------------------------

def test_a_line_with_a_secrets_shape_is_held_back_in_a_text_file(tmp_path):
    state = tmp_path / ".orkcraft"
    seed_board(state)
    put(state, f"board/{WIKI}/pages/ideas/dark-mode.md", f"# Dark mode\nkey {KEY} here\nfine\n")
    files, held = bb.pack(state, WIKI)
    body = files[f"board/{WIKI}/pages/ideas/dark-mode.md"].decode()
    assert KEY not in body and "held back" in body and "fine" in body
    assert held == [f"board/{WIKI}/pages/ideas/dark-mode.md"]


def test_a_json_with_a_held_line_is_not_sent_at_all(tmp_path):
    state = tmp_path / ".orkcraft"
    seed_board(state)
    put(state, "ideas/dark-mode/plan.json", json.dumps({"tasks": [], "note": f"token = {KEY}"}, indent=1))
    files, held = bb.pack(state, WIKI)
    assert "ideas/dark-mode/plan.json" not in files and held == ["ideas/dark-mode/plan.json"]
    assert all(KEY not in b.decode("utf-8", "replace") for b in files.values())


def test_a_jsonl_loses_the_held_line_and_stays_json(tmp_path):
    state = tmp_path / ".orkcraft"
    seed_board(state)
    put(state, "ideas/dark-mode/talk.jsonl", '{"text": "a"}\n' + json.dumps({"text": KEY}) + '\n{"text": "b"}\n')
    files, held = bb.pack(state, WIKI)
    lines = files["ideas/dark-mode/talk.jsonl"].decode().splitlines()
    assert [json.loads(ln)["text"] for ln in lines] == ["a", "b"] and held == ["ideas/dark-mode/talk.jsonl"]


# -- the commit, the fetch, the push, the read (A.3) ---------------------------------------------------------------

def test_commit_makes_no_commit_for_the_same_tree(tmp_path):
    root = make_clone(make_origin(tmp_path), tmp_path / "a")
    state = root / ".orkcraft"
    seed_board(state)
    cfg = bb.BoardConfig()
    files, _ = bb.pack(state, WIKI)
    first = bb.commit(root, state, cfg, files, "one", "")
    assert first and git(root, "rev-parse", bb.LOCAL_REF).strip() == first
    assert bb.commit(root, state, cfg, files, "again", first) == ""
    second = bb.commit(root, state, cfg, {**files, "kinds.json": b'{"a": 1}'}, "two", first)
    assert second and second != first and git(root, "rev-parse", f"{second}^").strip() == first
    assert not (state / "board.index").exists()


def test_commit_leaves_the_working_tree_the_index_and_the_branches_alone(tmp_path):
    root = make_clone(make_origin(tmp_path), tmp_path / "a")
    state = root / ".orkcraft"
    seed_board(state)
    before = (git(root, "status", "--porcelain"), git(root, "branch", "-a"), git(root, "rev-parse", "HEAD"))
    bb.commit(root, state, bb.BoardConfig(), bb.pack(state, WIKI)[0], "one", "")
    assert (git(root, "status", "--porcelain"), git(root, "branch", "-a"), git(root, "rev-parse", "HEAD")) == before


def test_pushed_fetched_and_read_back(tmp_path):
    origin = make_origin(tmp_path)
    a, b = make_clone(origin, tmp_path / "a"), make_clone(origin, tmp_path / "b")
    state = a / ".orkcraft"
    seed_board(state)
    cfg = bb.BoardConfig()
    assert bb.fetch(b, cfg) == {"ok": True, "tip": "", "why": ""}          # no branch yet: not a failure
    files, _ = bb.pack(state, WIKI)
    made = bb.commit(a, state, cfg, files, "one", "")
    assert bb.push(a, cfg, made) == {"ok": True, "refused": False, "why": ""}
    got = bb.fetch(b, cfg)
    assert got["ok"] and got["tip"] == made
    assert bb.files_at(b, bb.REMOTE_REF) == files
    assert git(origin, "rev-parse", "--verify", "refs/heads/orkboard/board").strip() == made


def test_a_push_that_is_not_a_fast_forward_is_refused_and_never_forced(tmp_path):
    origin = make_origin(tmp_path)
    a, b = make_clone(origin, tmp_path / "a"), make_clone(origin, tmp_path / "b")
    cfg = bb.BoardConfig()
    first = bb.commit(a, a / ".orkcraft", cfg, {"kinds.json": b"{}"}, "one", "")
    assert bb.push(a, cfg, first)["ok"]
    other = bb.commit(b, b / ".orkcraft", cfg, {"kinds.json": b'{"b": 1}'}, "other", "")
    got = bb.push(b, cfg, other)
    assert not got["ok"] and got["refused"] and got["why"]
    assert git(origin, "rev-parse", "refs/heads/orkboard/board").strip() == first


def test_fetch_and_push_say_why_when_the_remote_is_not_there(tmp_path):
    a = make_clone(make_origin(tmp_path), tmp_path / "a")
    cfg = bb.BoardConfig(remote="nowhere")
    assert bb.fetch(a, cfg)["ok"] is False and bb.fetch(a, cfg)["why"]
    made = bb.commit(a, a / ".orkcraft", cfg, {"kinds.json": b"{}"}, "one", "")
    got = bb.push(a, cfg, made)
    assert got["ok"] is False and got["refused"] is False and got["why"]


# -- the working copy, kept from the branch (A.4) -----------------------------------------------------------------

class FakeTree:
    """A Board tree as unpack sees it: it exists, and says what it was asked to commit."""

    def __init__(self, wiki_rel: str = WIKI, exists: bool = True) -> None:
        self.wiki_rel, self._exists, self.flushed = wiki_rel, exists, []
        self.ensured = 0

    def exists(self) -> bool:
        return self._exists

    def ensure(self) -> None:
        self.ensured += 1
        self._exists = True

    def flush(self, now: float = 0.0, force: bool = False, message: str = "", files=()) -> dict:
        self.flushed.append((force, message))
        return {"commit": "abc", "pages": 1, "what": "x", "held": ""}


def test_unpack_writes_removes_a_listed_file_the_branch_dropped_and_leaves_the_rest(tmp_path):
    state = tmp_path / ".orkcraft"
    seed_board(state)
    for n in ("ideas/dark-mode/secrets.json", "sign-in/token", "drive.json", "logs/x.log", "random.txt"):
        put(state, n, "keep me")
    put(state, "goals/dropped/state.json", "{}")                         # a goal the other worker dropped
    put(state, "ideas/dark-mode/state.json", '{"state": "old"}')
    tree = FakeTree()
    branch = {"ideas/dark-mode/state.json": b'{"state": "working"}', "ideas/new/state.json": b"{}",
              f"board/{WIKI}/pages/ideas/new.md": b"# New\n", "kinds.json": b"{}"}
    got = bb.unpack(state, branch, tree, by="other")
    assert json.loads((state / "ideas/dark-mode/state.json").read_text())["state"] == "working"
    assert (state / "ideas/new/state.json").is_file() and (state / f"board/{WIKI}/pages/ideas/new.md").read_text() == "# New\n"
    assert not (state / "goals/dropped/state.json").exists() and not (state / "ideas/dark-mode/plan.json").exists()
    assert not (state / f"board/{WIKI}/specs/one.md").exists()                                # a page the branch dropped goes too
    for n in ("ideas/dark-mode/secrets.json", "sign-in/token", "drive.json", "logs/x.log", "random.txt"):
        assert (state / n).read_text() == "keep me"                                           # not listed, or never: untouched
    assert got["removed"] >= 3 and got["written"] >= 3
    assert not list(state.rglob("*.board-tmp"))


def test_unpack_commits_the_pages_once(tmp_path):
    state = tmp_path / ".orkcraft"
    tree = FakeTree()
    bb.unpack(state, {f"board/{WIKI}/pages/ideas/a.md": b"a", f"board/{WIKI}/pages/ideas/b.md": b"b", "kinds.json": b"{}"}, tree, by="the cloud")
    assert tree.flushed == [(True, "board: the Board taken from the cloud")]
    tree2 = FakeTree()
    bb.unpack(state, {f"board/{WIKI}/pages/ideas/a.md": b"a", f"board/{WIKI}/pages/ideas/b.md": b"b", "kinds.json": b'{"x": 1}'}, tree2, by="x")     # no page changed: no commit
    assert tree2.flushed == []


def test_unpack_makes_the_tree_when_missing_and_writes_nothing_outside_the_list(tmp_path):
    state = tmp_path / ".orkcraft"
    tree = FakeTree(exists=False)
    bb.unpack(state, {f"board/{WIKI}/pages/ideas/a.md": b"a", "../escape.txt": b"x", "ideas/../../escape2.txt": b"x", "secrets.json": b"x",
                      "drive.json": b"x", "ideas/s/secrets.json": b"x", "random.txt": b"x", "lease.json": b"{}"}, tree)
    assert tree.ensured == 1
    assert not (tmp_path / "escape.txt").exists() and not (tmp_path / "escape2.txt").exists()
    assert sorted(p.relative_to(state).as_posix() for p in state.rglob("*") if p.is_file()) == [f"board/{WIKI}/pages/ideas/a.md"]


def test_unpack_does_not_remove_a_file_pack_held_back(tmp_path):
    state = tmp_path / ".orkcraft"
    seed_board(state)
    put(state, "ideas/dark-mode/plan.json", json.dumps({"note": f"token = {KEY}"}))           # held: the branch never had it
    bb.unpack(state, {"kinds.json": b"{}"}, FakeTree())
    assert (state / "ideas/dark-mode/plan.json").is_file()


def test_unpack_with_the_real_board_tree_commits_the_pages(tmp_path):
    from orkboard.realm.idea_git import BoardTree
    root = make_clone(make_origin(tmp_path), tmp_path / "a")
    state = root / ".orkcraft"
    git(root, "branch", "dev")
    tree = BoardTree(root, state, WIKI, lambda: "dev")
    got = bb.unpack(state, {f"board/{WIKI}/pages/ideas/a.md": b"# A\n", "ideas/a/state.json": b"{}"}, tree, by="the cloud")
    assert tree.exists() and (tree.root() / "pages/ideas/a.md").read_text() == "# A\n" and got["commit"]
    assert "the Board taken from the cloud" in git(root, "log", "-1", "--format=%s", "dev")


# -- turned on (A.1) -------------------------------------------------------------------------------------------------

def test_config_off_means_nothing_runs(tmp_path):
    assert bb.read_config(tmp_path) is None
    (tmp_path / "orkcraft.toml").write_text('[journal]\nremote = "origin"\n')
    assert bb.read_config(tmp_path) is None
    (tmp_path / "orkcraft.toml").write_text("not = [toml")
    assert bb.read_config(tmp_path) is None


def test_config_reads_the_table_and_ignores_a_bad_value(tmp_path):
    (tmp_path / "orkcraft.toml").write_text("[board]\n")
    assert bb.read_config(tmp_path) == bb.BoardConfig("origin", "orkboard/board")
    (tmp_path / "orkcraft.toml").write_text('[board]\nremote = "up"\nbranch = "b/x"\n')
    assert bb.read_config(tmp_path) == bb.BoardConfig("up", "b/x")
    (tmp_path / "orkcraft.toml").write_text('[board]\nremote = "--upload-pack=x"\nbranch = "../x"\n')
    assert bb.read_config(tmp_path) == bb.BoardConfig("origin", "orkboard/board")


def test_the_public_check_refuses_a_200_and_goes_on_for_a_404(tmp_path):
    root = make_clone(make_origin(tmp_path), tmp_path / "a")
    git(root, "remote", "set-url", "origin", "git@github.com:acme/widgets.git")
    asked = []
    ok, line = bb.private_check(root, bb.BoardConfig(), lambda url: asked.append(url) or 200)
    assert not ok and "only to a private repository" in line
    assert asked == ["https://api.github.com/repos/acme/widgets"]
    assert bb.private_check(root, bb.BoardConfig(), lambda url: 404) == (True, "")
    assert bb.private_check(root, bb.BoardConfig(), lambda url: 0) == (True, "")             # not reachable: goes on
    git(root, "remote", "set-url", "origin", "https://github.com/acme/widgets")
    assert asked[-1] and bb.private_check(root, bb.BoardConfig(), lambda url: asked.append(url) or 200)[0] is False
    assert asked[-1] == "https://api.github.com/repos/acme/widgets"


def test_a_remote_not_on_github_goes_on_with_a_line_and_asks_nothing(tmp_path):
    root = make_clone(make_origin(tmp_path), tmp_path / "a")

    def never(url):
        raise AssertionError("no network")
    ok, line = bb.private_check(root, bb.BoardConfig(), never)
    assert ok and "must be private" in line


# -- spec 151 F: the visibility as a word, `in_code` beside the table, a push that waits ------------------------------------

def test_the_visibility_is_a_word_and_in_code_alone_is_no_yes_to_the_branch(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    assert bb.visibility(root, None, lambda url: 200) == "none"
    git(root, "remote", "add", "origin", "https://github.com/acme/app.git")
    assert [bb.visibility(root, None, lambda url, c=c: c) for c in (200, 404, 0, 403)] == ["public", "private", "unknown", "unknown"]
    git(root, "remote", "set-url", "origin", "git@example.org:acme/app.git")
    assert bb.visibility(root, None, lambda url: 200) == "unknown"
    git(root, "remote", "set-url", "origin", str(tmp_path / "origin.git"))
    assert bb.visibility(root, None, lambda url: 200) == "private"                       # a folder on this computer is nobody's public repository
    (root / "orkcraft.toml").write_text("[board]\nin_code = false\n")
    assert bb.read_config(root) is None
    bb.turn_on(root)
    assert bb.read_config(root) == bb.BoardConfig("origin", "orkboard/board") and "in_code = false" in (root / "orkcraft.toml").read_text()


def test_put_key_keeps_every_other_line():
    text = '[gate]\nalways = ["x"]\n\n[board]\nremote = "up"\n\n[journal]\ninbox = "i"\n'
    out = bb.put_key(text, "in_code", "true")
    assert out == '[gate]\nalways = ["x"]\n\n[board]\nin_code = true\nremote = "up"\n\n[journal]\ninbox = "i"\n'
    assert bb.put_key(out, "in_code", "false").count("in_code") == 1 and "in_code = false" in bb.put_key(out, "in_code", "false")


def test_pack_leaves_a_goal_kept_off_at_home_only_in_a_public_repository_with_the_yes(tmp_path):
    state = tmp_path / ".orkcraft"
    for slug in ("a", "b"):
        (state / "ideas" / slug).mkdir(parents=True)
        (state / "ideas" / slug / "state.json").write_text(json.dumps({"state": "raw", "kept_off": slug == "b"}))
        (state / "board" / WIKI / "pages" / "ideas").mkdir(parents=True, exist_ok=True)
        (state / "board" / WIKI / "pages" / "ideas" / f"{slug}.md").write_text(f"# {slug}\n")
    assert f"board/{WIKI}/pages/ideas/b.md" in bb.pack(state, WIKI)[0]                  # no `in_code`: the repository is not said to be public
    (tmp_path / "orkcraft.toml").write_text("[board]\nin_code = true\n")
    files, _held = bb.pack(state, WIKI)
    assert f"board/{WIKI}/pages/ideas/a.md" in files and "ideas/a/state.json" in files
    assert f"board/{WIKI}/pages/ideas/b.md" not in files and "ideas/b/state.json" not in files
