"""The canvas hook (docs/specs/78-canvases.md §5, hooks/canvas.py): a PostToolUse payload that is a canvas is one line in
the project's store, at once; anything else writes nothing, and the answer is always `{}` with exit 0."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from orkboard.core.canvases import Canvases
from orkboard.hooks import canvas as hook, warder

ROOT = Path(__file__).resolve().parent.parent
ART = "https://claude.ai/artifact/0f3c9a"
FIGMA = "https://www.figma.com/design/AbC123/Onboarding"


@pytest.fixture
def project(tmp_path) -> Path:
    p = tmp_path / "proj"
    (p / ".git").mkdir(parents=True)
    (p / "src").mkdir()
    return p


def _hook(args: list[str], text: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "orkboard.hooks.canvas", *args], input=text, capture_output=True,
                          text=True, cwd=cwd, timeout=30, env={**os.environ, "PYTHONPATH": str(ROOT)})


def _run(tool: str, payload, cwd: Path, raw: str | None = None) -> subprocess.CompletedProcess:
    return _hook([tool], raw if raw is not None else json.dumps(payload), cwd)


def _lines(project: Path) -> list[dict]:
    f = project / ".orkcraft" / "canvases.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []


def _claude(project: Path, cwd: str | None = None) -> dict:
    return {"session_id": "s-1", "cwd": cwd or str(project / "src"), "hook_event_name": "PostToolUse",
            "tool_name": "Artifact", "tool_input": {"file_path": "/tmp/onboarding.html", "title": "Onboarding"},
            "tool_response": f"Published. View it at {ART}"}


def _codex(project: Path) -> dict:
    return {"session_id": "c-1", "turn_id": "t1", "cwd": str(project), "model": "gpt-5.5", "permission_mode": "default",
            "tool_name": "mcp__figma__create_new_file", "tool_use_id": "u1", "tool_input": {"fileName": "Onboarding"},
            "tool_response": {"content": [{"type": "text", "text": f"Created {FIGMA}"}]}}


def _agy(project: Path) -> dict:
    return {"toolCall": {"name": "generate_image", "args": {"Prompt": "a lantern in the fog\nsoft", "ImageName": "lantern"}},
            "conversationId": "conv-9", "workspacePaths": [str(project)], "modelName": "gemini-3.8-flash-high",
            "toolResult": "Saved the image to /home/u/.gemini/antigravity/brain/conv-9/lantern_1.png"}


def _assert_silent(r: subprocess.CompletedProcess) -> None:
    assert r.stdout.strip() == "{}" and r.returncode == 0


# -- what it writes ------------------------------------------------------------------------------------------------

def test_a_claude_artifact_is_one_line_the_store_reads_back(project):
    _assert_silent(_run("claude", _claude(project), project / "src"))
    (line,) = _lines(project)
    assert line["key"] == f"claude:{ART}" and line["kind"] == "page" and line["title"] == "Onboarding"
    assert line["session"] == "s-1" and line["at"]
    new, seen = Canvases(project).shown()
    assert [c.url for c in new] == [ART] and seen == []


def test_no_argument_is_claude(project):
    _assert_silent(_hook([], json.dumps(_claude(project)), project))
    assert len(_lines(project)) == 1


def test_a_codex_figma_file_is_a_design(project):
    _assert_silent(_run("codex", _codex(project), project))
    (c,) = Canvases(project).shown()[0]
    assert (c.tool, c.kind, c.url, c.title, c.session, c.model) == (
        "codex", "design", FIGMA, "Onboarding", "c-1", "gpt-5.5")


def test_an_agy_picture_is_a_picture_with_its_conversation_and_model(project):
    _assert_silent(_run("agy", _agy(project), project / "src"))
    (c,) = Canvases(project).shown()[0]
    assert (c.tool, c.kind, c.session, c.model) == ("agy", "picture", "conv-9", "gemini-3.8-flash-high")
    assert c.file.endswith("lantern_1.png") and c.title == "a lantern in the fog"


@pytest.mark.parametrize("key", ["result", "output"])
def test_agy_names_its_answer_in_other_keys_too(project, key):
    payload = _agy(project)
    payload[key] = payload.pop("toolResult")
    _assert_silent(_run("agy", payload, project))
    assert len(_lines(project)) == 1


def test_agy_without_an_answer_reads_the_image_from_its_arguments(project):
    payload = _agy(project)
    payload.pop("toolResult")
    payload["toolCall"]["args"]["TargetFile"] = "/home/u/brain/conv-9/lantern.png"
    _assert_silent(_run("agy", payload, project))
    assert _lines(project)[0]["file"] == "/home/u/brain/conv-9/lantern.png"


def test_the_project_is_the_nearest_folder_with_orkcraft_or_git(tmp_path):
    outer = tmp_path / "outer"
    inner = outer / "apps" / "web"
    (outer / ".git").mkdir(parents=True)
    (inner / ".orkcraft").mkdir(parents=True)
    assert hook.project_of(str(inner)) == inner.resolve()
    assert hook.project_of(str(outer / "apps")) == outer.resolve()


def test_a_git_worktree_writes_to_its_main_checkout(project):
    work = project / ".orkcraft" / "worktrees" / "t1"
    work.mkdir(parents=True)
    gitdir = project / ".git" / "worktrees" / "t1"
    gitdir.mkdir(parents=True)
    (work / ".git").write_text(f"gitdir: {gitdir}\n")
    _assert_silent(_run("claude", _claude(project, cwd=str(work)), work))
    assert len(_lines(project)) == 1 and not (work / ".orkcraft" / "canvases.jsonl").exists()


def test_a_canvas_drawn_again_is_appended_and_stays_one_card(project):
    _run("claude", _claude(project), project)
    _run("claude", _claude(project), project)
    assert len(_lines(project)) == 2 and len(Canvases(project).shown()[0]) == 1


# -- what it leaves alone ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tool, payload", [
    ("claude", {"tool_name": "Bash", "tool_input": {"command": "ls"}, "tool_response": f"{ART}"}),
    ("claude", {"tool_name": "Artifact", "tool_input": {"action": "read", "url": ART}, "tool_response": ART}),
    ("claude", {"tool_name": "Artifact", "tool_input": {"file_path": "/tmp/a.html"}, "tool_response": "no link"}),
    ("claude", {"tool_name": "Artifact", "tool_input": {"file_path": "/tmp/a.html"},
                "tool_response": {"is_error": True, "content": ART}}),
    ("codex", {"tool_name": "mcp__figma__get_metadata", "tool_input": {}, "tool_response": FIGMA}),
    ("agy", {"toolCall": {"name": "run_command", "args": {"CommandLine": "ls"}}, "toolResult": "/tmp/a.png"}),
])
def test_a_tool_that_is_no_canvas_writes_nothing(project, tool, payload):
    _assert_silent(_run(tool, {"cwd": str(project), "workspacePaths": [str(project)], **payload}, project))
    assert _lines(project) == [] and not (project / ".orkcraft").exists()


# -- it never blocks -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tool", ["claude", "codex", "agy"])
@pytest.mark.parametrize("raw", ["not json at all", "", "[1, 2]", "null", '{"tool_name": 7, "tool_input": "x"}',
                                 '{"toolCall": "x", "workspacePaths": "y"}'])
def test_a_bad_payload_still_answers_nothing_and_exits_0(project, tool, raw):
    _assert_silent(_run(tool, None, project, raw=raw))
    assert _lines(project) == []


def test_a_cwd_outside_any_project_writes_nothing(tmp_path):
    outside = tmp_path / "nowhere"
    outside.mkdir()
    if any((p / ".git").exists() or (p / ".orkcraft").is_dir() for p in (outside.resolve(), *outside.resolve().parents)):
        pytest.skip("the temp folder is inside a project")
    _assert_silent(_run("claude", _claude(outside, cwd=str(outside)), outside))
    assert not (outside / ".orkcraft").exists()


def test_an_unwritable_store_is_swallowed(project):
    (project / ".orkcraft").write_text("a file where the folder should be")
    _assert_silent(_run("claude", _claude(project), project))


def test_in_process_main_prints_the_answer_and_returns_0(project, capsys):
    assert hook.main(["claude"], io.StringIO(json.dumps(_claude(project)))) == 0
    assert capsys.readouterr().out.strip() == "{}" and len(_lines(project)) == 1
    assert hook.main(["agy"], io.StringIO("{broken")) == 0
    assert capsys.readouterr().out.strip() == "{}"


def test_a_stdin_that_never_ends_is_given_up_on_after_the_timeout(monkeypatch, capsys):
    class Stuck:
        def read(self):
            time.sleep(3)
            return ""
    monkeypatch.setattr(hook, "TIMEOUT", 0.2)
    t = time.monotonic()
    assert hook.main(["claude"], Stuck()) == 0
    assert time.monotonic() - t < 2 and capsys.readouterr().out.strip() == "{}"


def test_it_imports_nothing_heavy():
    out = subprocess.run([sys.executable, "-c", "import sys, orkboard.hooks.canvas; "
                          "print(json.dumps(sorted(m for m in sys.modules if m.startswith('orkboard'))))"
                          .replace("print(json", "import json; print(json")],
                         capture_output=True, text=True, cwd=ROOT, timeout=30)
    assert set(json.loads(out.stdout)) <= {"orkboard", "orkboard.hooks", "orkboard.hooks.canvas", "orkboard.sources",
                                           "orkboard.sources.canvases"}, out.stdout


# -- the Warder guards it ------------------------------------------------------------------------------------------

def test_the_warder_guards_the_hooks_own_file():
    assert {"orkcraft/hooks/canvas.py", "orkboard/hooks/canvas.py"} <= set(warder.SELF)
    assert warder.self_name(warder.REPO / "orkboard" / "hooks" / "canvas.py") == "orkboard/hooks/canvas.py"
