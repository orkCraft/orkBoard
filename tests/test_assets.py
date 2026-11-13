"""Spec 88 §1–§4 (docs/specs/88-assets-and-play.md): the project's assets by kind, read from dev's tree (never the working tree), the
skipped folders and secrets, the cap with the changed first, stacks, a pick's others, what changed since a commit with its goal, and the
version before written once into the before-cache. Real git repositories, real small files (tests/pick_files.py)."""
from __future__ import annotations

import json
from pathlib import Path

from orkboard.realm import assets, idea_pick, idea_shots, ideas
from tests import pick_files as pf
from tests.test_commit_goal import git, land, repo, state  # noqa: F401  (the fixture)

PNG = pf.png(5, 4)


def put(path: Path, files: dict[str, bytes], message: str = "") -> str:
    """Files written and committed on what `path` has checked out; the new head."""
    for name, data in files.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_bytes(data)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", message or "assets")
    return git(path, "rev-parse", "HEAD")


def land_files(repo: Path, slug: str, tid: str, files: dict[str, bytes]) -> str:
    """A task that lands binary files into dev (tests/test_commit_goal.py's `land`, with bytes)."""
    from orkboard.realm.idea_git import IdeaGit
    g = IdeaGit(repo)
    path, branch = g.prepare(slug, tid, "dev")
    put(path, files, f"{tid}: assets")
    sha, subjects, _ = g.land(path, branch, "dev", push=False)
    g.remove(path)
    folder = ideas.state_folder(state(repo), slug)
    folder.mkdir(parents=True, exist_ok=True)
    plan = ideas.plan(state(repo), slug) or {"tasks": []}
    plan["tasks"].append({"id": tid, "title": f"Task {tid}", "short": f"Short {tid}", "state": "merged", "commit": sha, "subjects": subjects})
    (folder / "plan.json").write_text(json.dumps(plan))
    return sha


def by_id(rows: list[dict]) -> dict[str, dict]:
    return {r["id"]: r for r in rows}


# -- kinds -----------------------------------------------------------------------------------------------------------------

def test_the_kinds_by_extension_and_a_sound_by_its_folder_or_its_length():
    assert [assets.kind_of(p) for p in ("a/b.PNG", "x.jpeg", "i.svg", "c.mp4", "c.webm", "c.mov", "f.woff2", "f.otf")] == \
        ["art", "art", "art", "clip", "clip", "clip", "font", "font"]
    assert assets.kind_of("game/sfx/jump.wav") == "sound" and assets.kind_of("Audio/ui/click.ogg") == "sound"
    assert assets.kind_of("game/ui-sounds/x.mp3") == "sound" and assets.kind_of("sounds.wav") == "music"     # a folder names it, not a file
    assert assets.kind_of("music/theme.ogg", 120.0) == "music" and assets.kind_of("ui/ding.wav", 0.4) == "sound"
    assert assets.kind_of("ui/ding.flac") == "music" and assets.kind_of("README.md") == ""


# -- the assets of dev's tree ---------------------------------------------------------------------------------------------

def test_the_assets_are_dev_trees_by_kind_with_their_sizes_and_lengths_and_nothing_else(repo):
    put(repo, {"art/hero.png": PNG, "art/icon.svg": pf.svg(24, 12), "game/sfx/jump.wav": pf.wav(0.5), "music/theme.wav": pf.wav(12, rate=200),
               "music/short.wav": pf.wav(2, rate=200), "clips/intro.mp4": pf.mp4(seconds=5, w=320, h=240), "fonts/Pixel.ttf": b"\x00\x01\x00\x00font",
               "node_modules/pkg/logo.png": PNG, ".github/x.png": PNG, "design/looks/home.png": PNG, "art/.env.png": PNG,
               "README.md": b"# hi", "src/app.js": b"x"})
    (repo / "art" / "draft.png").write_bytes(PNG)                                       # the working tree's own: never listed
    git(repo, "checkout", "-q", "main")
    put(repo, {"art/main-only.png": PNG})                                               # main's, not dev's
    git(repo, "checkout", "-q", "dev")
    rows = by_id(assets.listed(state(repo), repo, "dev"))
    assert set(rows) == {"art/hero.png", "art/icon.svg", "game/sfx/jump.wav", "music/theme.wav", "music/short.wav", "clips/intro.mp4",
                         "fonts/Pixel.ttf"}
    hero = rows["art/hero.png"]
    assert {k: hero[k] for k in ("kind", "name", "bytes", "w", "h", "seconds", "goal", "task", "change")} == \
        {"kind": "art", "name": "hero.png", "bytes": len(PNG), "w": 5, "h": 4, "seconds": None, "goal": "", "task": "", "change": ""}
    assert hero["at"][:4].isdigit() and (rows["art/icon.svg"]["w"], rows["art/icon.svg"]["h"]) == (24, 12)
    assert (rows["game/sfx/jump.wav"]["kind"], rows["game/sfx/jump.wav"]["seconds"]) == ("sound", 0.5)
    assert (rows["music/theme.wav"]["kind"], rows["music/theme.wav"]["seconds"]) == ("music", 12.0)
    assert rows["music/short.wav"]["kind"] == "sound"                                   # shorter than ten seconds: a sound
    assert {k: rows["clips/intro.mp4"][k] for k in ("kind", "w", "h", "seconds")} == {"kind": "clip", "w": 320, "h": 240, "seconds": 5.0}
    assert rows["fonts/Pixel.ttf"]["kind"] == "font" and rows["fonts/Pixel.ttf"]["w"] is None
    assert (state(repo) / "assets-before" / "measured.json").is_file()                 # read once, kept by blob


def test_a_tasks_newest_picture_is_a_screen(repo, tmp_path):
    s = state(repo)
    for rnd, w in ((1, 3), (2, 6)):
        png = tmp_path / f"shot{rnd}.png"
        png.write_bytes(pf.png(w, 4))
        idea_shots.store(s, "dark-mode", "k2", rnd, png)
    folder = ideas.state_folder(s, "dark-mode")
    (folder / "plan.json").write_text(json.dumps({"tasks": [{"id": "k2", "title": "Draw the home screen", "short": "Home screen"}]}))
    rows = [r for r in assets.listed(s, repo, "dev") if r["kind"] == "screen"]
    assert len(rows) == 1
    assert {k: rows[0][k] for k in ("id", "name", "w", "h", "goal", "task")} == \
        {"id": "screen:dark-mode/k2", "name": "Home screen", "w": 6, "h": 4, "goal": "dark-mode", "task": "k2"}
    assert rows[0]["shot"] == {"goal": "dark-mode", "id": "k2-shot-r2", "file": "shot.png"}


def test_a_picked_files_variants_not_picked_lie_under_it(repo, tmp_path):
    s = state(repo)
    pick = pf.make_pick(s, tmp_path / "v", {"a.png": pf.png(2, 2), "b.png": pf.png(3, 3), "c.png": pf.png(4, 4)}, slug="logo")
    idea_pick.answer(s, "logo", pick, "B", "the round one")
    (ideas.state_folder(s, "logo") / "plan.json").write_text(json.dumps({"tasks": [pf.task(3, state="merged")]}))
    put(repo, {"assets/logo.png": pf.png(3, 3)})
    row = by_id(assets.listed(s, repo, "dev"))["assets/logo.png"]
    assert row["others"]["goal"] == "logo" and row["others"]["pick"] == "k1-r1" and row["others"]["picked"] == "B"
    assert [(v["key"], v["file"], v["w"]) for v in row["others"]["variants"]] == [("A", "a.png", 2), ("C", "c.png", 4)]


# -- what changed (§3) -----------------------------------------------------------------------------------------------------

def test_added_changed_and_removed_since_a_commit_with_their_goals(repo):
    since = put(repo, {"art/hero.png": PNG, "art/old.png": PNG, "sfx/hit.wav": pf.wav(0.3)})
    land_files(repo, "dark-mode", "k1", {"art/hero.png": pf.png(8, 8), "art/new.svg": pf.svg()})
    git(repo, "rm", "-q", "art/old.png")
    git(repo, "commit", "-q", "-m", "my own: the old one goes")
    got = assets.changed(state(repo), repo, since)
    assert got["since"] == since
    assert [(r["id"], r["kind"], r["goal"], r["task"]) for r in got["added"]] == [("art/new.svg", "art", "dark-mode", "k1")]
    assert [(r["id"], r["goal"], r["task"]) for r in got["changed"]] == [("art/hero.png", "dark-mode", "k1")]
    assert [(r["id"], r["kind"], r["goal"]) for r in got["removed"]] == [("art/old.png", "art", "")]           # the person's own
    rows = by_id(assets.listed(state(repo), repo, "dev", got))
    assert rows["art/hero.png"]["change"] == "changed" and rows["art/new.svg"]["change"] == "added" and rows["sfx/hit.wav"]["change"] == ""
    assert (rows["art/hero.png"]["goal"], rows["art/hero.png"]["task"]) == ("dark-mode", "k1")
    assert [r["id"] for r in assets.listed(state(repo), repo, "dev", got)][:2] in (["art/hero.png", "art/new.svg"], ["art/new.svg", "art/hero.png"])


# -- the version before (§4) ------------------------------------------------------------------------------------------------


def test_a_link_or_a_submodule_in_the_tree_is_never_an_asset(repo):
    (repo / "art").mkdir()
    (repo / "art" / "link.png").symlink_to("/etc/passwd")
    put(repo, {"art/real.png": PNG})
    assert set(by_id(assets.listed(state(repo), repo, "dev"))) == {"art/real.png"}
    sha = git(repo, "rev-parse", "HEAD")
    assert assets.materialize(state(repo), repo, sha, "art/link.png") is None


# -- the commands (As built) --------------------------------------------------------------------------------------------------

def test_ideas_assets_answers_the_assets_signed_with_what_changed_and_the_goals(repo, tmp_path):
    from orkboard.gui import media
    from orkboard.gui.board_host import Orkboard
    since = put(repo, {"art/hero.png": PNG, "art/old.png": PNG})
    land_files(repo, "dark-mode", "k1", {"art/hero.png": pf.png(8, 8), "sfx/hit.wav": pf.wav(0.3)})
    git(repo, "rm", "-q", "art/old.png")
    git(repo, "commit", "-q", "-m", "mine")
    png = tmp_path / "shot.png"
    png.write_bytes(pf.png(4, 3))
    idea_shots.store(state(repo), "dark-mode", "k1", 1, png)
    host = Orkboard(repo)
    try:
        head = git(repo, "rev-parse", "dev")
        got = host.command("ideas.assets", {"since": since})
        assert set(got) == {"commit", "short", "ref", "since", "assets", "removed", "stacks", "goals"}
        assert (got["commit"], got["short"], got["ref"], got["since"]) == (head, head[:7], "dev", since)
        rows = by_id(got["assets"])
        hero = rows["art/hero.png"]
        assert hero["url"] == media.asset_url(head, "art/hero.png") and hero["change"] == "changed"
        assert (hero["goal"], hero["task"], hero["kind"], hero["w"]) == ("dark-mode", "k1", "art", 8)
        assert rows["sfx/hit.wav"]["change"] == "added" and rows["sfx/hit.wav"]["kind"] == "sound"
        screen = rows["screen:dark-mode/k1"]
        assert screen["url"] == media.url("dark-mode", "k1-shot-r1", "shot.png") and "shot" not in screen
        assert [(r["id"], r["goal"]) for r in got["removed"]] == [("art/old.png", "")]
        assert set(got["goals"]) == {"dark-mode"} and set(got["goals"]["dark-mode"]) == {"title", "element", "hue"}
        assert media.serve("GET", hero["url"], "", media.state_dirs(host)).read() == pf.png(8, 8)
        plain = host.command("ideas.assets", {})
        assert plain["since"] == "" and plain["removed"] == [] and all(r["change"] == "" for r in plain["assets"])
        before = host.command("ideas.asset_before", {"path": "art/hero.png", "since": since})
        assert before == {"path": "art/hero.png", "since": since, "url": media.asset_url(since, "art/hero.png"), "bytes": len(PNG),
                          "w": 5, "h": 4, "seconds": None}
        assert media.serve("GET", before["url"], "", media.state_dirs(host)).read() == PNG
        added = host.command("ideas.asset_before", {"path": "sfx/hit.wav", "since": since})
        assert added == {"path": "sfx/hit.wav", "since": since, "url": ""}
        for bad in ("../x.png", ".git/x.png", "README.md"):
            try:
                host.command("ideas.asset_before", {"path": bad, "since": since})
                raise AssertionError(bad)
            except Exception as e:
                assert "not one of the project's assets" in str(e)
    finally:
        host.close()


# -- the project's logo (spec 107 §9.2) ----------------------------------------------------------------------------------------

SVG = b"<svg xmlns='http://www.w3.org/2000/svg'/>"


def test_the_logo_is_the_svg_before_any_png_else_the_largest_png_or_webp(repo):
    assert assets.logo(repo) == ""                                                                   # nothing in the project yet
    put(repo, {"README.md": b"x", "art/hero.png": PNG, "logos.png": PNG})                            # not named for one
    assert assets.logo(repo) == ""
    put(repo, {"icon.png": pf.png(16, 16), "web/logo@2x.png": pf.png(64, 64), "brand-mark.webp": b"RIFFxxxxWEBPVP8 " + b"\0" * 8})
    assert assets.logo(repo) == "web/logo@2x.png"                                                    # the largest, by its bytes
    put(repo, {"docs/favicon.svg": SVG})
    assert assets.logo(repo) == "docs/favicon.svg"                                                   # an svg first, whatever the pictures' size
    put(repo, {"logo.svg": SVG, "logo-dark.svg": SVG})
    assert assets.logo(repo) == "logo.svg"                                                           # among svgs the path nearest the root


