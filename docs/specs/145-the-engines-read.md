# 145. The engines read: System and Screens of a Godot, a Unity and an Unreal project

Decisions §208.5, §209.5, §220.2–3 (§218.4: the engines before every hint). **Builds:** the cheaper model, A (Godot), then B
(Unity), then C (Unreal), then D (the words), each its own commit into `main` as its tests and the critical ones are green
(CLAUDE.md, Alpha) · **Review:** the critical tests and each part's own · P1. Code only, no model, nothing run, nothing
fetched; no face changes beyond D's one line: the maps draw what the host gives them. No change to orkUI.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. Godot** | parts from `.gd` files, their uses from `preload`, `load`, `extends` and `class_name`; the project a container, its main scene and autoloads its ways in; a `Control`-rooted `.tscn` a screen, `change_scene_to_*` its links | new `realm/engine_godot.py`; `realm/code_map.py`, `realm/system_overview.py`, `realm/screen_routes.py` / `realm/screen_map.py` (one call each); new `tests/test_engine_godot.py` with a fixture project under `tests/fixtures/engines/godot/` |
| **B. Unity** | each `.asmdef` a container (and `Assets/` outside them, `Assembly-CSharp`), its `references` its links; C#'s `using` between parts; the build settings' scenes and UI Toolkit's `.uxml` the screens, `SceneManager.LoadScene` the links | new `realm/engine_unity.py`; the same three callers; new `tests/test_engine_unity.py`, `tests/fixtures/engines/unity/` |
| **C. Unreal** | the `.uproject`'s modules, each `.Build.cs` a container, its `Public`/`PrivateDependencyModuleNames` that are the project's own its links | new `realm/engine_unreal.py`; `realm/system_overview.py`, `realm/code_map.py`; new `tests/test_engine_unreal.py`, `tests/fixtures/engines/unreal/` |
| **D. The words** | §220.3's line at a new project's first read; a Godot C# project told it has no Play yet (§220.2) | `realm/project_kind.py` (`words`, `in_words`), where the first open says the project's kind (`gui/first_open_cards.py`); `realm/lexicon.py` if a new word; `tests/test_first_open.py`, `tests/test_project_kind.py` (or the kind's test file) |

**Not this spec:** Play for an engine (§220.1, §220.4–7: a web build from the command line, the canvas marked by coordinates, the
proxy's isolation, checked first on the real engines); the hints of §208.2–4 and §209.2–4 (their evidence is asked for before their
spec, §208.7); a second map, files as cards, any new tab (§208.1, §209.1).

## 0. What is there today

- `realm/code_map.py` reads Python and JS/TS alone (`PY`, `JS`): a game in an engine has no parts.
- `realm/system_overview.py` finds containers by `MANIFESTS = ("package.json", "pyproject.toml", "go.mod", "Cargo.toml")`, two folders
  deep: an engine's project is no container.
- `realm/screen_routes.py` reads web and Flutter routers, else a `screens/`, `views/` or `pages/` folder: no scene is a screen.
- `realm/project_kind.py` knows `project.godot` (`GAME_FILES`) and `.gd` is in `CODE`; nothing else of an engine.

## Common to A, B, C

1. **One module an engine**, each with the same three entry points, so the callers add one line each and an engine is one file:
   `detect(root) -> bool`; `parts(root, files) -> list[dict]` in `code_map.parts`'s shape (`path`, `files`, `count`, `uses`, `used_by`);
   `containers(root) -> list[dict]` in `system_overview`'s container shape (its stack named *Godot*, *Unity* or *Unreal*, its ways in);
   and for A and B `screens(tree) -> (source, rows)` in `screen_routes.routes`'s shape, plus the link patterns `screen_map` reads.
   Read each caller first and match its shapes exactly; a field an engine cannot fill is empty, never guessed.
2. **Bounds as today's**: `code_map.MAX_FILES`, `MAX_BYTES`, `SKIP`, `is_secret`; and each engine's own folders skipped (Godot's
   `.godot/` and `.import/`; Unity's `Library/`, `Temp/`, `Obj/`, `Logs/`, `UserSettings/`, `Packages/` caches; Unreal's
   `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`). Every regex has bounded repeats. Screens read through
   `screen_routes.Tree` (a commit's files), never the working tree, as today.
3. **What is outside the repository is left out**, as `code_map` leaves out an import from outside: an engine's own classes and
   modules (`Node`, `UnityEngine`, `Core`, `Engine`) are no part and no link.
4. **A project with two kinds** (a Godot game with a Python tool beside it) keeps both: the engine's parts and containers are added
   to what is read today, never in place of it.
5. **Fixtures** are small hand-written projects (a few files each, plain text), committed under `tests/fixtures/engines/<engine>/`;
   the tests read them through a temporary git repository where the reader needs a commit (Screens).

## A. Godot (§208.5, §209.5, §220.2)

1. **Detect**: a `project.godot` at the root or one or two folders down; its folder is the project's (`res://` resolves there).
2. **Parts**: each folder of `.gd` files is a part (as `code_map`'s folders). A file uses another by `preload("res://…")`,
   `load("res://…")` and `extends "res://…"` (the path's file), and by `extends Name` or a use of `Name.` / `Name.new(` where `Name`
   is a `class_name` declared in the project. A `.tscn` that attaches a script (`[ext_resource type="Script" path="res://…"]`) and
   instances another scene (`type="PackedScene"`) gives its folder the same uses. C# scripts of a Godot project (`.cs`) are read as
   B.3's `using`.
3. **The container**: the project is one container, stack *Godot* (and *Godot C#* when a `.csproj` with `Godot.NET.Sdk` is beside it);
   its ways in: `run/main_scene` of `[application]`, and each `[autoload]` entry (`Name="*res://path"`), named by its name.
4. **Screens**: a `.tscn` whose root node (the first `[node …]` with no `parent=`) is a `Control` or one of Godot's `Control` kinds (`Container`,
   `Panel`, `MarginContainer`, `VBoxContainer`, `HBoxContainer`, `CenterContainer`, `TextureRect`, … as a fixed list in the module;
   only the root's own type counts, so a `CanvasLayer` or `Node2D` root is not a screen), named by the root node's `name`, its `path` the `res://` path, its `file` the scene. The source is `godot`. Its
   links: in the scene's scripts, `change_scene_to_file("res://….tscn")` and `change_scene_to_packed(preload("res://….tscn"))` (and
   a `const` or `var` holding that path, one level). The entry is `run/main_scene` when it is a screen.
5. **Tests**: the fixture's parts and their uses (a `preload`, an `extends` by path, an `extends` by `class_name`); the container,
   its stack and its ways in (the main scene, two autoloads); the screens (a `Control`-rooted menu and options, a `Node2D` level is
   not one) and the link between them; a C# Godot project's stack; nothing read under `.godot/`.

## B. Unity (§208.5, §209.5)

1. **Detect**: `ProjectSettings/ProjectVersion.txt` or an `Assets/` folder with `.meta` files beside `ProjectSettings/`.
2. **Containers**: each `.asmdef` (JSON: `name`, `references`) is a container, stack *Unity*, its folder and everything under it to
   the next `.asmdef`; the scripts of `Assets/` outside every `.asmdef` are the container `Assembly-CSharp`. Its links are its
   `references`: by name, or `GUID:<guid>` resolved through the `.asmdef.meta` files' `guid:`. A reference to no `.asmdef` of the
   project (Unity's or a package's) is left out.
3. **Parts and their uses**: each folder of `.cs` files is a part. The namespaces a part declares (`namespace X` / `namespace X;`)
   are read once; a file's `using X;` (and `using static X.Y;`) uses the parts that declare `X`. A file with no namespace declares
   the global one, which nothing uses by `using`.
4. **Screens**: the scenes of `ProjectSettings/EditorBuildSettings.asset` that are enabled (`- enabled: 1`, `path: Assets/….unity`),
   in its order, the first the entry; named by the file's stem; and each UI Toolkit document (`.uxml`) as a screen of its own. The
   source is `unity`. Links: `SceneManager.LoadScene("Name")` / `LoadSceneAsync("Name")` by name or by the path, and by a build
   index that the build settings' order names.
5. **Tests**: two `.asmdef`s, one referencing the other by name and one by GUID; `Assembly-CSharp` for the loose scripts; a `using`
   between two parts and one of `UnityEngine` left out; the build settings' scenes, one disabled and left out, a `.uxml`, a
   `LoadScene` by name and one by index; nothing read under `Library/`.

## C. Unreal (§208.5)

1. **Detect**: a `.uproject` at the root.
2. **Containers**: each module (`Source/<Name>/<Name>.Build.cs`, and `Plugins/*/Source/<Name>/<Name>.Build.cs`), stack *Unreal*,
   named by its module; the `.uproject`'s `Modules` give each its `Type` (*Runtime*, *Editor*) as the container's role words. Links:
   the names in `PublicDependencyModuleNames` and `PrivateDependencyModuleNames` (`Add("X")`, `AddRange(new string[] { "X", "Y" })`)
   that are modules of the project; the engine's are left out.
3. **Parts**: each folder of `.h`/`.cpp` files under a module is a part; a file uses another by `#include "…"` that resolves to a file of
   the project (beside it, or under a module's `Public/` or `Private/`). Angle-bracket includes are left out.
4. **No Screens** for Unreal in this spec (§209.5 names Godot and Unity).
5. **Tests**: a game module and an editor module depending on it, with `Core` and `Engine` left out; a plugin's module; an `#include`
   between two folders; nothing read under `Intermediate/`.

## D. The words (§220.2–3)

1. **At the first read of a new project** (where the first open says what the project is: `gui/first_open_cards.py`, and the kind's
   `words`/`in_words` in `realm/project_kind.py`): one line, said once, *Orkboard sees web projects and Godot best; Unity and Flutter
   work, with some checks not there*. Said for every kind (§220.3: *said at the start, never forbidden*), never a choice or a block.
2. **A Godot C# project** (A.3's stack *Godot C#*): the kind's words add *Godot's C# does not build for the web yet: this project has no
   Play until it does*. Nothing else changes.
3. **Tests**: the line once on a new project's first read, not on the second; the C# line for a Godot C# fixture and not for a GDScript one.
