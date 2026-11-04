"""Spec 145 C (docs/specs/145-the-engines-read.md): an Unreal project read for the maps. The fixture is tests/fixtures/engines/unreal/: a game module and an editor module
depending on it (with `Core` and `Engine` left out), a module of a plugin, `#include` between folders; nothing read under `Intermediate/`; no screens. No model."""
from __future__ import annotations

import shutil
from pathlib import Path

from orkboard.realm import code_map, engine_unreal, system_overview
from tests.test_engine_godot import FIXTURES, by_path


def project(tmp_path: Path) -> Path:
    shutil.copytree(FIXTURES / "unreal", tmp_path / "unreal")
    return tmp_path / "unreal"


def test_an_unreal_project_is_a_uproject_at_the_root(tmp_path):
    root = project(tmp_path)
    assert engine_unreal.detect(root) and not engine_unreal.detect(tmp_path / "nothing")
    nested = tmp_path / "nested"
    nested.mkdir()
    shutil.copytree(root, nested / "game")
    assert not engine_unreal.detect(nested)


def test_each_build_cs_is_a_container_with_its_type_for_its_role(tmp_path):
    ov = system_overview.read(project(tmp_path))
    got = {c["path"]: c for c in ov["containers"]}
    assert set(got) == {"Source/Skyhop", "Source/SkyhopEditor", "Source/Inventory", "Plugins/Tools/Source/SkyhopTools"}      # a plugin's module too
    assert got["Source/Skyhop"]["name"] == "Skyhop" and got["Source/Skyhop"]["manifests"] == ["Skyhop.Build.cs"]
    assert got["Source/Skyhop"]["stack"] == [{"name": "Unreal", "role": "game"}]
    assert got["Source/Skyhop"]["role"] == "Runtime" and got["Source/SkyhopEditor"]["role"] == "Editor"        # the `.uproject`'s Modules
    assert got["Plugins/Tools/Source/SkyhopTools"]["role"] == "Editor"                                       # the plugin's own
    assert "role" not in got["Source/Inventory"]                                                              # a module no list types has no role


def test_the_dependency_names_that_are_the_projects_own_modules_are_the_links(tmp_path):
    links = system_overview.read(project(tmp_path))["links"]
    assert [(k["from"], k["to"]) for k in links] == [
        ("Source/Skyhop", "Source/Inventory"), ("Source/Skyhop", "Plugins/Tools/Source/SkyhopTools"),        # Public/PrivateDependencyModuleNames, Add and AddRange
        ("Source/SkyhopEditor", "Source/Skyhop"), ("Plugins/Tools/Source/SkyhopTools", "Source/Inventory")]
    assert not any("Core" in (k["from"] + k["to"]) or "Engine" in k["to"] for k in links)                    # Core, Engine, Slate, UnrealEd: the engine's


def test_a_folder_of_cpp_is_a_part_and_a_quoted_include_that_resolves_is_a_use(tmp_path):
    got = by_path(code_map.parts(project(tmp_path)))
    hero_cpp, hero_h, strike = "Source/Skyhop/Private/Actors", "Source/Skyhop/Public/Actors", "Source/Skyhop/Private/Combat"
    assert got[hero_cpp]["uses"] == [strike, hero_h]                                    # `Actors/Hero.h` under Public/, `Combat/Strike.h` under Private/
    assert got[strike]["uses"] == [hero_h] and got[strike]["files"] == ["Strike.cpp", "Strike.h"]       # `Strike.h` beside it stays in the folder
    assert got[hero_h]["uses"] == ["Source/Inventory/Public/Inventory"]                 # across modules, under the other's Public/
    assert got["Source/SkyhopEditor/Private"]["uses"] == [hero_h]
    assert got["Plugins/Tools/Source/SkyhopTools/Private"]["uses"] == ["Source/Inventory/Public/Inventory"]


def test_angle_brackets_the_engines_headers_and_generated_ones_are_left_out(tmp_path):
    got = by_path(code_map.parts(project(tmp_path)))
    every = {u for r in got.values() for u in r["uses"]}
    assert every <= set(got) and not any("GameFramework" in u or "CoreMinimal" in u for u in every)


def test_the_module_files_are_in_the_owners_parts_and_the_layers_are_read(tmp_path):
    c = {x["path"]: x for x in system_overview.read(project(tmp_path))["containers"]}["Source/Skyhop"]
    assert c["parts"] == ["Source/Skyhop/Private/Actors", "Source/Skyhop/Private/Combat", "Source/Skyhop/Public/Actors"] and c["layers"]


def test_nothing_under_intermediate_binaries_saved_or_derived_data_is_read(tmp_path):
    root = project(tmp_path)
    for folder in ("Intermediate", "Binaries", "Saved", "DerivedDataCache", "Source/Skyhop/Intermediate"):
        (root / folder).mkdir(parents=True, exist_ok=True)
        (root / folder / "Ghost.Build.cs").write_text('PublicDependencyModuleNames.Add("Skyhop");\n')
        (root / folder / "Ghost.cpp").write_text('#include "Actors/Hero.h"\n')
    assert "Ghost" not in {c["name"] for c in system_overview.read(root)["containers"]}
    assert not any("Intermediate" in p["path"] or "Saved" in p["path"] for p in code_map.parts(root))
