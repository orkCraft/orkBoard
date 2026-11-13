"""Spec 145 B (docs/specs/145-the-engines-read.md): a Unity project read for the maps. The fixture is tests/fixtures/engines/unity/: three `.asmdef`s (one referencing
another by name, one by GUID), loose scripts (`Assembly-CSharp`), `using` between parts, the build settings' scenes (one disabled) and a `.uxml`, `LoadScene` by
name and by build index; nothing read under `Library/`. Real git repositories for the screens, no model."""
from __future__ import annotations

import shutil
from pathlib import Path

from orkboard.realm import code_map, engine_unity, screen_routes, system_overview
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


def test_a_using_between_two_parts_is_a_use_and_the_engines_own_namespace_is_none(tmp_path):
    got = by_path(code_map.parts(project(tmp_path)))
    assert got["Assets/Scripts/Gameplay"]["uses"] == ["Assets/Scripts/Core"]          # `using Game.Core;`; `using UnityEngine;` is the engine's
    assert got["Assets/Scripts/UI"]["uses"] == ["Assets/Scripts/Gameplay"]
    assert got["Assets/Loose"]["uses"] == ["Assets/Loose/Shared", "Assets/Scripts/Core"]
    assert got["Assets/Scripts/Core"]["used_by"] == ["Assets/Loose", "Assets/Scripts/Gameplay"]
    assert not any("UnityEngine" in u for r in got.values() for u in r["uses"])


def test_the_enabled_build_scenes_in_order_and_each_uxml_are_the_screens(repo, tmp_path):
    sha = on_dev(repo, project(tmp_path))
    source, rows = screen_routes.routes(screen_routes.Tree(repo, sha))
    assert source == "unity"
    assert [(r["name"], r["file"]) for r in rows] == [("Menu", "Assets/Scenes/Menu.unity"), ("Level1", "Assets/Scenes/Level1.unity"),     # Debug is disabled
                                                      ("Hud", "Assets/UI/Hud.uxml")]


def test_nothing_under_library_temp_or_packages_is_read(tmp_path):
    root = project(tmp_path)
    for folder in ("Library/PackageCache/x", "Temp", "Packages/com.x", "Obj", "Logs", "UserSettings"):
        (root / folder).mkdir(parents=True)
        (root / folder / "Cache.cs").write_text("namespace Game.Core { }\nusing Game.Gameplay;\n")
        (root / folder / "Cache.asmdef").write_text('{"name": "Cache", "references": []}')
    assert [p["path"] for p in code_map.parts(root)] == ["Assets/Loose", "Assets/Loose/Shared", "Assets/Scripts/Core", "Assets/Scripts/Gameplay", "Assets/Scripts/UI"]
    assert "Cache" not in {c["name"] for c in system_overview.read(root)["containers"]}
