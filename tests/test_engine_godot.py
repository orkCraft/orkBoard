"""Spec 145 A (docs/specs/145-the-engines-read.md): a Godot project read for the maps. The fixture is tests/fixtures/engines/godot/ (a GDScript game) and
godot_csharp/ (a C# one): the parts and their uses (a `preload`, an `extends` by path, an `extends` by `class_name`, a scene's script and instance), the
container with its stack and ways in, the screens (a `Control`-rooted menu and options, a `Node2D` level is none) and the link between them, nothing read under
`.godot/`. Real git repositories for the screens (tests/test_commit_goal.py's), no model."""
from __future__ import annotations

import shutil
from pathlib import Path

from orkboard.realm import code_map, engine_godot, screen_map, screen_routes, system_overview
from tests.test_commit_goal import git, repo  # noqa: F401  (the fixtures)

FIXTURES = Path(__file__).parent / "fixtures" / "engines"


def project(tmp_path: Path, name: str = "godot") -> Path:
    shutil.copytree(FIXTURES / name, tmp_path / name)
    return tmp_path / name


def on_dev(repo: Path, folder: Path) -> str:
    for f in folder.rglob("*"):
        if f.is_file():
            target = repo / f.relative_to(folder)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, target)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the game")
    return git(repo, "rev-parse", "dev")


def by_path(rows: list[dict]) -> dict[str, dict]:
    return {r["path"]: r for r in rows}


def test_a_godot_project_is_found_at_the_root_and_one_or_two_folders_down(tmp_path):
    assert engine_godot.detect(project(tmp_path))
    assert not engine_godot.detect(tmp_path / "nothing")
    nested = tmp_path / "nested"
    shutil.copytree(FIXTURES / "godot", nested / "games" / "skyhop")
    assert engine_godot.detect(nested)
    deep = tmp_path / "deep"
    shutil.copytree(FIXTURES / "godot", deep / "a" / "b" / "c")
    assert not engine_godot.detect(deep)


def test_each_folder_of_scripts_is_a_part_and_its_uses_are_preload_extends_and_class_names(tmp_path):
    got = by_path(code_map.parts(project(tmp_path)))
    assert got["scripts/game"]["files"] == ["enemy.gd", "level.gd", "player.gd", "settings.gd", "tuning.gd"]
    assert got["scripts/game"]["uses"] == ["scripts/core"]           # `extends "res://…/base_level.gd"`, `extends Mob`, `Rng.new()`
    assert got["scripts/ui"]["uses"] == ["scenes", "scripts/game"]   # `preload("res://…/tuning.gd")`, `Settings.new()`, `preload("res://…/main_menu.tscn")`
    assert got["scripts/core"]["uses"] == [] and got["scripts/core"]["used_by"] == ["scripts/game"]
    assert got["autoload"]["uses"] == [] and got["autoload"]["used_by"] == []
    assert "Node" not in got and not any("Node" in u for r in got.values() for u in r["uses"])       # the engine's own classes are no part and no link


def test_the_project_is_one_container_with_its_stack_and_ways_in(tmp_path):
    ov = system_overview.read(project(tmp_path))
    assert [c["path"] for c in ov["containers"]] == ["."]
    c = ov["containers"][0]
    assert c["name"] == "Skyhop" and c["manifests"] == ["project.godot"] and c["stack"] == [{"name": "Godot", "role": "game"}]
    assert c["ways_in"] == [{"kind": "main", "name": "", "path": "scenes/main_menu.tscn"},
                            {"kind": "autoload", "name": "Events", "path": "autoload/events.gd"},
                            {"kind": "autoload", "name": "Save", "path": "autoload/save.gd"}]
    assert c["parts"] == ["autoload", "scenes", "scripts/core", "scripts/game", "scripts/ui", "ui"] and c["layers"]


def test_a_control_rooted_scene_is_a_screen_and_a_node2d_level_is_not(repo, tmp_path):
    sha = on_dev(repo, project(tmp_path))
    source, rows = screen_routes.routes(screen_routes.Tree(repo, sha))
    assert source == "godot"
    assert [(r["path"], r["name"], r["file"]) for r in rows] == [
        ("res://scenes/main_menu.tscn", "MainMenu", "scenes/main_menu.tscn"),        # the main scene first
        ("res://scenes/options.tscn", "Options", "scenes/options.tscn")]            # a MarginContainer root; Level1 (Node2D), Player, Hud (CanvasLayer) are none


def test_the_scenes_change_to_one_another_by_a_const_and_by_a_preload(repo, tmp_path):
    on_dev(repo, project(tmp_path))
    got = screen_map.read(repo / ".orkcraft", repo)
    assert got["source"] == "godot" and got["entry"] == got["screens"][0]["id"]
    ids = {s["name"]: s["id"] for s in got["screens"]}
    assert [(k["from"], k["to"]) for k in got["links"]] == [(ids["MainMenu"], ids["Options"]), (ids["Options"], ids["MainMenu"])]
    assert got["steps"] == [[ids["MainMenu"]], [ids["Options"]]] and got["loose"] == []
    assert "read from Godot scenes" in screen_map.text(repo / ".orkcraft", repo)


