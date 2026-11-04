"""Spec 145 B (docs/specs/145-the-engines-read.md): a Unity project read for the maps. The fixture is tests/fixtures/engines/unity/: three `.asmdef`s (one referencing
another by name, one by GUID), loose scripts (`Assembly-CSharp`), `using` between parts, the build settings' scenes (one disabled) and a `.uxml`, `LoadScene` by
name and by build index; nothing read under `Library/`. Real git repositories for the screens, no model."""
from __future__ import annotations

import shutil
from pathlib import Path

from orkboard.realm import code_map, engine_unity, screen_map, screen_routes, system_overview
from tests.test_commit_goal import git, repo  # noqa: F401  (the fixture)
from tests.test_engine_godot import FIXTURES, by_path, on_dev


def project(tmp_path: Path) -> Path:
    shutil.copytree(FIXTURES / "unity", tmp_path / "unity")
    return tmp_path / "unity"


def test_a_unity_project_is_found_by_its_version_file_or_by_assets_with_metas(tmp_path):
    assert engine_unity.detect(project(tmp_path))
    bare = tmp_path / "bare"
    (bare / "ProjectSettings").mkdir(parents=True)
    (bare / "Assets").mkdir()
    assert not engine_unity.detect(bare)
    (bare / "Assets" / "Scenes.meta").write_text("fileFormatVersion: 2\n")
    assert engine_unity.detect(bare)
    assert not engine_unity.detect(tmp_path / "nothing")


def test_each_asmdef_is_a_container_and_the_loose_scripts_are_assembly_csharp(tmp_path):
    ov = system_overview.read(project(tmp_path))
    got = {c["path"]: c for c in ov["containers"]}
    assert {p: c["name"] for p, c in got.items()} == {"Assets": "Assembly-CSharp", "Assets/Scripts/Core": "Game.Core",
                                                       "Assets/Scripts/Gameplay": "Game.Gameplay", "Assets/Scripts/UI": "Game.UI"}
    assert all(c["stack"] == [{"name": "Unity", "role": "game"}] for c in got.values())
    assert got["Assets/Scripts/Core"]["manifests"] == ["Core.asmdef"]
    assert got["Assets"]["parts"] == ["Assets/Loose", "Assets/Loose/Shared"]               # everything under an `.asmdef` is that container's


def test_a_references_name_and_a_guid_are_links_and_what_is_no_asmdef_of_the_project_is_left_out(tmp_path):
    links = system_overview.read(project(tmp_path))["links"]
    assert [(k["from"], k["to"]) for k in links] == [("Assets/Scripts/Gameplay", "Assets/Scripts/Core"),     # by name (Unity.TextMeshPro: a package's, left out)
                                                     ("Assets/Scripts/UI", "Assets/Scripts/Gameplay")]      # by GUID (the other GUID is none of the project's)
    assert all(k["http"] == [] and k["socket"] == [] for k in links)


def test_a_using_between_two_parts_is_a_use_and_the_engines_own_namespace_is_none(tmp_path):
    got = by_path(code_map.parts(project(tmp_path)))
    assert got["Assets/Scripts/Gameplay"]["uses"] == ["Assets/Scripts/Core"]          # `using Game.Core;`; `using UnityEngine;` is the engine's
    assert got["Assets/Scripts/UI"]["uses"] == ["Assets/Scripts/Gameplay"]
    assert got["Assets/Loose"]["uses"] == ["Assets/Loose/Shared", "Assets/Scripts/Core"]
    assert got["Assets/Scripts/Core"]["used_by"] == ["Assets/Loose", "Assets/Scripts/Gameplay"]
    assert not any("UnityEngine" in u for r in got.values() for u in r["uses"])


def test_the_namespace_a_part_does_not_declare_is_no_use_and_a_global_one_is_used_by_none(tmp_path):
    root = project(tmp_path)
    (root / "Assets" / "Loose" / "Global.cs").write_text("using System;\nusing Missing.Space;\n\npublic class Global { }\n")
    got = by_path(code_map.parts(root))
    assert got["Assets/Loose"]["uses"] == ["Assets/Loose/Shared", "Assets/Scripts/Core"] and "Global.cs" in got["Assets/Loose"]["files"]
    assert not any(r["path"] == "Assets/Loose" for r in code_map.parts(root) for u in r["uses"] if u == "Assets/Loose")


def test_the_enabled_build_scenes_in_order_and_each_uxml_are_the_screens(repo, tmp_path):
    sha = on_dev(repo, project(tmp_path))
    source, rows = screen_routes.routes(screen_routes.Tree(repo, sha))
    assert source == "unity"
    assert [(r["name"], r["file"]) for r in rows] == [("Menu", "Assets/Scenes/Menu.unity"), ("Level1", "Assets/Scenes/Level1.unity"),     # Debug is disabled
                                                      ("Hud", "Assets/UI/Hud.uxml")]


def test_load_scene_by_name_and_by_build_index_are_the_links_and_the_first_scene_is_the_entry(repo, tmp_path):
    on_dev(repo, project(tmp_path))
    got = screen_map.read(repo / ".orkcraft", repo)
    ids = {s["name"]: s["id"] for s in got["screens"]}
    assert got["entry"] == ids["Menu"]
    assert [(k["from"], k["to"]) for k in got["links"]] == [(ids["Menu"], ids["Level1"]),        # `SceneManager.LoadScene("Level1")` in the Menu's script
                                                            (ids["Level1"], ids["Menu"])]        # `SceneManager.LoadScene(0)`: build index 0 is the Menu
    assert got["loose"] == [ids["Hud"]]                                                          # a `.uxml` no scene loads
    assert "read from Unity scenes" in screen_map.text(repo / ".orkcraft", repo)


def test_nothing_under_library_temp_or_packages_is_read(tmp_path):
    root = project(tmp_path)
    for folder in ("Library/PackageCache/x", "Temp", "Packages/com.x", "Obj", "Logs", "UserSettings"):
        (root / folder).mkdir(parents=True)
        (root / folder / "Cache.cs").write_text("namespace Game.Core { }\nusing Game.Gameplay;\n")
        (root / folder / "Cache.asmdef").write_text('{"name": "Cache", "references": []}')
    assert [p["path"] for p in code_map.parts(root)] == ["Assets/Loose", "Assets/Loose/Shared", "Assets/Scripts/Core", "Assets/Scripts/Gameplay", "Assets/Scripts/UI"]
    assert "Cache" not in {c["name"] for c in system_overview.read(root)["containers"]}
