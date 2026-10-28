"""Spec 75 A (docs/specs/75-parties-fitted-to-the-project.md §1, Tests → A): what the project is, read by names: each kind from a folder made in the
test, the order when two hold, the walk's limit and what it never reads, the cache `ideas.map` reads. Code, no model."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from orkboard.realm import project_kind


def make(root: Path, *names: str, **files: str) -> Path:
    """A folder with these names (a trailing / is a folder, else an empty file) and these files with their text."""
    root.mkdir(parents=True, exist_ok=True)
    for n in names:
        if n.endswith("/"):
            (root / n).mkdir(parents=True, exist_ok=True)
        else:
            (root / n).parent.mkdir(parents=True, exist_ok=True)
            (root / n).write_text("", encoding="utf-8")
    for n, text in files.items():
        (root / n).parent.mkdir(parents=True, exist_ok=True)
        (root / n).write_text(text, encoding="utf-8")
    return root


def kind(root: Path) -> str:
    return project_kind.read(root, fresh=True)["kind"]


def test_an_empty_folder_a_readme_dot_files_and_the_boards_own_are_empty(tmp_path):
    assert project_kind.read(tmp_path / "gone", fresh=True) == {"kind": "empty", "signs": []}
    root = make(tmp_path / "a")
    assert project_kind.read(root, fresh=True) == {"kind": "empty", "signs": []}
    make(root, "README.md", ".gitignore", ".git/HEAD", ".orkcraft/ideas/x.json", "orkcraft.toml", "LICENSE", "docs/")
    assert kind(root) == "empty"
    make(root, "notes.txt")
    assert kind(root) != "empty"


@pytest.mark.parametrize("names,files,want,sign", [
    (("ios/Runner.swift", "android/build.gradle", "README.md"), {}, "mobile", "ios/"),
    (("pubspec.yaml", "lib/main.dart"), {}, "mobile", "pubspec.yaml"),
    (("App.xcodeproj/project.pbxproj", "App/main.swift"), {}, "mobile", ".xcodeproj"),
    ((), {"package.json": json.dumps({"dependencies": {"expo": "1", "react": "18"}})}, "mobile", "package.json: expo"),
    (("project.godot", "main.gd"), {}, "game", "project.godot"),
    (("ProjectSettings/ProjectVersion.txt", "Assets/a.cs"), {}, "game", "ProjectSettings/"),
    (("Game.uproject", "Source/a.cpp"), {}, "game", "Game.uproject"),
    ((), {"package.json": json.dumps({"dependencies": {"react": "18", "left-pad": "1"}}), "src/App.jsx": ""}, "web", "package.json: react"),
    (("index.html", "style.css"), {}, "web", "index.html"),
    (("pyproject.toml", "app/main.py"), {}, "backend", "pyproject.toml"),
    (("go.mod", "main.go"), {}, "backend", "go.mod"),
    (("Dockerfile", "main.c"), {}, "backend", "Dockerfile"),
    (("dbt_project.yml", "models/a.yml"), {}, "data", "dbt_project.yml"),
    (("a.ipynb", "b.ipynb", "q.sql", "util.py"), {}, "data", "2 notebooks"),
    ((".obsidian/app.json", "Daily.md", "Plan.md"), {}, "wiki", ".obsidian/"),
    (("mkdocs.yml", "docs/index.md"), {}, "wiki", "mkdocs.yml"),
    (("docs/a.md", "docs/b.md", "logo.png"), {}, "wiki", "docs/"),
    (("a.md", "b.md", "c.md", "d.txt"), {}, "wiki", "3 Markdown pages"),
    (("brand.fig", *[f"pic{n}.png" for n in range(30)], "README.md"), {}, "design", "31 pictures"),
    (("a.docx", "b.pdf", "c.txt", "d.pdf", "e.md"), {}, "texts", "5 documents"),
    (("main.c", "util.c", "util.h", "notes.md"), {}, "code", "2 .c files"),
])
def test_each_kind_from_a_folder_made_for_it(tmp_path, names, files, want, sign):
    got = project_kind.read(make(tmp_path / "p", *names, **files), fresh=True)
    assert got["kind"] == want and sign in got["signs"] and len(got["signs"]) <= project_kind.SIGNS
    assert all(isinstance(s, str) and len(s) <= project_kind.SIGN_CHARS for s in got["signs"])


def test_a_folder_of_nothing_known_is_code(tmp_path):
    got = project_kind.read(make(tmp_path / "p", "thing.bin", "other.dat"), fresh=True)
    assert got["kind"] == "code" and got["signs"] == []


def test_the_first_that_holds_wins_a_react_native_app_is_mobile_and_an_app_with_a_backend_file_is_web(tmp_path):
    rn = make(tmp_path / "rn", **{"package.json": json.dumps({"dependencies": {"react": "1", "react-native": "1"}}), "App.js": ""})
    assert kind(rn) == "mobile"
    web = make(tmp_path / "web", "Dockerfile", **{"package.json": json.dumps({"devDependencies": {"vite": "5"}})})
    assert kind(web) == "web"                                                   # web before backend
    game = make(tmp_path / "game", "project.godot", "pyproject.toml", "ios/")
    assert kind(game) == "mobile"                                               # mobile before game
    back = make(tmp_path / "back", "pyproject.toml", "a.ipynb", "b.ipynb", "c.sql")
    assert kind(back) == "backend"                                              # backend before data
    code_wiki = make(tmp_path / "cw", "mkdocs.yml", "docs/a.md", "tool.py")
    assert kind(code_wiki) == "code"                                            # a wiki has no code
    pics_code = make(tmp_path / "pc", *[f"p{n}.png" for n in range(20)], "x.py")
    assert kind(pics_code) == "code"


def test_a_notebooks_and_sql_folder_is_data_only_when_they_outnumber_the_other_code(tmp_path):
    assert kind(make(tmp_path / "a", "a.ipynb", "b.sql", "tool.py")) == "data"
    assert kind(make(tmp_path / "b", "a.ipynb", "tool.py", "tool2.py")) == "code"


def test_markdown_decides_wiki_before_texts_and_pictures_before_documents(tmp_path):
    assert kind(make(tmp_path / "a", "a.md", "b.md", "c.pdf")) == "wiki"
    assert kind(make(tmp_path / "b", "a.md", "b.docx", "c.pdf", "d.png")) == "texts"
    assert kind(make(tmp_path / "c", "a.png", "b.svg", "c.fig", "d.md")) == "design"


def test_it_reads_names_and_a_package_jsons_dependencies_only(tmp_path, monkeypatch):
    root = make(tmp_path / "p", "pyproject.toml", "app.py", **{"package.json": json.dumps({"dependencies": {"react": "1"}, "scripts": {"x": "SECRET"}})})
    opened = []
    real = Path.read_text

    def spy(self, *a, **k):
        opened.append(self.name)
        return real(self, *a, **k)
    monkeypatch.setattr(Path, "read_text", spy)
    assert project_kind.read(root, fresh=True)["kind"] == "web"
    assert [n for n in opened if n != "project.json"] == ["package.json"]                      # the Board's own state (the kind the person kept) is not the project's file


def test_the_walk_stops_at_two_thousand_entries_and_skips_git_dot_folders_and_the_boards_pages(tmp_path, monkeypatch):
    root = tmp_path / "big"
    for d in ("a", "b", "c"):
        (root / d).mkdir(parents=True)
        for n in range(900):
            (root / d / f"f{n}.png").write_text("")
    for hidden in (".git", ".venv", ".orkcraft", "node_modules", "pages/tracks", "pages/ideas"):
        (root / hidden).mkdir(parents=True)
        (root / hidden / "x.py").write_text("")
    walked = []
    real = os.scandir

    def counted(path):
        it = real(path)
        walked.append(os.path.relpath(str(path), root))
        return it
    monkeypatch.setattr(os, "scandir", counted)
    got = project_kind.scan(root)
    assert got["facts"]["seen"] <= project_kind.LIMIT == 2000
    assert got["facts"]["pictures"] < 2700 and got["facts"]["pictures"] >= 1500
    assert got["kind"] == "design"                                              # (the .py inside hidden folders was never seen)
    assert not [w for w in walked if w.split(os.sep)[0] in (".git", ".venv", ".orkcraft", "node_modules") or w.startswith(("pages/tracks", "pages/ideas"))]
    assert got["facts"]["code"] == 0


def test_the_top_level_is_always_seen_before_the_depths(tmp_path):
    root = tmp_path / "deep"
    for n in range(2500):
        (root / "pics").mkdir(parents=True, exist_ok=True)
        (root / "pics" / f"{n}.png").write_text("")
    make(root, "go.mod")
    assert project_kind.read(root, fresh=True)["kind"] == "backend"


def test_the_read_is_kept_while_the_top_level_is_as_it_was_and_read_again_when_it_changes(tmp_path, monkeypatch):
    root = make(tmp_path / "p", "app.py")
    calls = []
    real = project_kind.scan
    monkeypatch.setattr(project_kind, "scan", lambda r: calls.append(r) or real(r))
    first = project_kind.read(root)
    for _ in range(5):
        assert project_kind.read(root) == first
    assert len(calls) == 1
    time.sleep(0.01)
    make(root, "ios/")
    assert project_kind.read(root)["kind"] == "mobile" and len(calls) == 2
    other = make(tmp_path / "q", **{"package.json": json.dumps({"dependencies": {"expo": "1"}})})
    assert project_kind.read(other)["kind"] == "mobile"
    before = len(calls)
    (other / "package.json").write_text(json.dumps({"dependencies": {"next": "1"}}))            # edited in place: its folder's time does not move
    os.utime(other / "package.json", ns=(1, 12345))
    assert project_kind.read(other)["kind"] == "web" and len(calls) == before + 1


def test_the_words_are_the_specs():
    assert [project_kind.words(k) for k in project_kind.KINDS] == ["an empty folder", "a mobile app", "a game", "a web app", "a backend",
                                                                   "data work", "a team's wiki", "a designer's folder", "texts", "code"]
    assert project_kind.in_words(["ios/", "android/"]) == "ios/ and android/ are here"
    assert project_kind.in_words(["pubspec.yaml"]) == "pubspec.yaml is here" and project_kind.in_words([]) == ""
    assert project_kind.in_words(["a", "b", "c"]) == "a, b and c are here"


# -- spec 100 F: the person's correction of the kind, read before the files ---------------------------------------------------------------

def test_a_kind_the_person_kept_is_read_before_the_files_with_the_rest_of_project_json_left_as_it_is(tmp_path):
    root = make(tmp_path / "p", "package.json", "src/app.py", **{".orkcraft/project.json": json.dumps({"stage": "live", "decisions": "d.md"})})
    state = root / ".orkcraft"
    before = project_kind.read(root, fresh=True)["kind"]
    assert project_kind.kept(state) == "" and before == "code"                     # the files' own reading (a source file, no web sign)
    assert project_kind.keep(state, "game") == "game"
    assert json.loads((state / "project.json").read_text()) == {"stage": "live", "decisions": "d.md", "kind": "game"}
    assert project_kind.kept(state) == "game"
    assert project_kind.read(root) == {"kind": "game", "signs": []}                         # with no `fresh`, and the files unchanged: the person's word first
    assert project_kind.read(root, fresh=True) == {"kind": "game", "signs": []}
    full = project_kind.read_full(root)
    assert full["kind"] == "game" and full["kept"] is True and full["facts"]["code"] >= 1
    (state / "project.json").write_text(json.dumps({"stage": "live"}))                       # the key gone: the files again
    assert project_kind.read(root, fresh=True)["kind"] == before and "kept" not in project_kind.read_full(root)


def test_a_kind_that_is_none_is_refused_and_a_state_with_a_bad_kind_reads_as_none(tmp_path):
    state = tmp_path / "state"
    for bad in ("", "castle", None, 3, "Game"):
        with pytest.raises(ValueError, match="A kind is one of empty, mobile, game"):
            project_kind.keep(state, bad)
    assert not (state / "project.json").exists()
    state.mkdir()
    (state / "project.json").write_text(json.dumps({"kind": "castle"}))
    assert project_kind.kept(state) == ""
    (state / "project.json").write_text("not json")
    assert project_kind.kept(state) == ""


def test_the_kept_kind_reaches_the_stage(tmp_path):
    from orkboard.realm import project_stage
    root = make(tmp_path / "p", "src/app.py")
    assert project_stage.read(root) == "being_made"
    project_kind.keep(root / ".orkcraft", "empty")                                         # the person says it is a bare folder: no code to count
    assert project_kind.read_full(root)["kind"] == "empty" and project_stage.read(root) == "idea"
    project_kind.keep(root / ".orkcraft", "mobile")
    assert project_stage.read(root) == "being_made" and project_kind.read(root)["kind"] == "mobile"
