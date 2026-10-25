"""Canvases' readers (docs/specs/78-canvases.md §1): what Claude Code, Codex and agy drew, read from their files on the
machine. Each reader runs on the fixture of its tool (`tests/fixtures/canvases/`, written by hand until §0 records a real
session: its README says so); the home of each tool is the test's own, never the real one."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from orkboard.sources import canvases, sessions, transcripts
from orkboard.sources.canvases import Canvas, read_agy, read_all, read_claude, read_codex

FIXTURES = Path(__file__).parent / "fixtures" / "canvases"
SESSION_ID = "0199aaaa-0000-7000-8000-000000000001"


@pytest.fixture(autouse=True)
def _clean_caches():
    canvases._CLAUDE.clear()
    canvases._CODEX.clear()
    yield
    canvases._CLAUDE.clear()
    canvases._CODEX.clear()


@pytest.fixture
def world(tmp_path: Path, monkeypatch) -> Path:
    """A project and a home of each tool, all under `tmp_path`: the project's root."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ORKCRAFT_CLAUDE_HOME", str(tmp_path / "claude"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    monkeypatch.setenv("ORKCRAFT_AGY_HOME", str(tmp_path / "agy"))
    project = (tmp_path / "project").resolve()
    project.mkdir()
    return project


def _claude(project: Path, name: str = "sess-1", text: str | None = None, mtime: float | None = None) -> Path:
    folder = sessions.claude_projects_dir(project)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.jsonl"
    path.write_text(text if text is not None else (FIXTURES / "claude_session.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def _codex(project: Path, cwd: Path | None = None, name: str = f"rollout-2026-10-25T10-00-00-{SESSION_ID}",
           text: str | None = None, mtime: float | None = None) -> Path:
    home = Path(os.environ["CODEX_HOME"])
    folder = home / "sessions" / "2026" / "10" / "25"
    folder.mkdir(parents=True, exist_ok=True)
    text = text if text is not None else (FIXTURES / "codex_rollout.jsonl").read_text(encoding="utf-8")
    path = folder / f"{name}.jsonl"
    path.write_text(text.replace("__PROJECT__", str(cwd or project)).replace("__CODEX_HOME__", str(home)), encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def _agy(conv: str = "conv-1", mtime: float = 1792923600.0) -> Path:
    folder = sessions.agy_brain_dir() / conv
    shutil.copytree(FIXTURES / "agy_brain", folder)
    for p in folder.iterdir():
        os.utime(p, (mtime, mtime))
    return folder


def _by_title(found: list[Canvas]) -> dict[str, Canvas]:
    return {c.title: c for c in found}


# -- Claude Code ------------------------------------------------------------------------------------------------------

def test_claude_reads_the_artifacts_the_docs_and_the_figma_files_a_session_made(world):
    _claude(world)
    found = read_claude(world)
    assert [c.title for c in found] == ["Onboarding", "Landing design", "Launch notes", "Elf kit"]   # no failed, no Bash call
    page, design, doc, fig = found
    assert (page.tool, page.kind, page.url, page.file) == ("claude", "page", "https://claude.ai/artifact/a1b2c3",
                                                          "/work/elf-page/onboarding.html")
    assert (page.session, page.model, page.at) == ("sess-1", "claude-opus-5-5", "2026-10-25T10:00:09.000Z")  # the result's line
    assert (design.kind, design.url, design.file) == ("design", "https://claude.ai/code/artifact/d4e5f6", "")
    assert (doc.kind, doc.url, doc.model, doc.at) == ("document", "https://claude.ai/artifact/9a8b7c", "claude-sonnet-5-5",
                                                      "2026-10-25T10:04:03.000Z")
    assert (fig.kind, fig.url) == ("design", "https://www.figma.com/design/AbCdEf123/Elf-kit")
    assert all(c.key == f"claude:{c.url}" for c in found)


def test_claude_reads_the_projects_worktrees_too_and_ignores_another_projects_folder(world, tmp_path):
    other = (tmp_path / "other").resolve()
    other.mkdir()
    _claude(other, "elsewhere")
    assert read_claude(world) == []
    tree = world / ".orkcraft" / "worktrees" / "t1"
    tree.mkdir(parents=True)
    _claude(tree, "in-a-tree")
    _claude(world, "in-the-project")
    assert sorted({c.session for c in read_claude(world)}) == ["in-a-tree", "in-the-project"]


def test_claude_a_broken_line_is_skipped_and_a_line_still_being_written_waits(world):
    lines = (FIXTURES / "claude_session.jsonl").read_text(encoding="utf-8").splitlines()
    use = json.dumps({"type": "assistant", "timestamp": "2026-10-25T11:00:00.000Z", "message": {
        "model": "m", "content": [{"type": "tool_use", "id": "late", "name": "Artifact", "input": {"title": "Late page"}}]}})
    result = json.dumps({"type": "user", "timestamp": "2026-10-25T11:00:02.000Z", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "late", "content": "https://claude.ai/artifact/late1"}]}})
    path = _claude(world, text="\n".join(lines[:4] + ["{not json", "[1, 2]", "", *lines[4:], use]) + "\n" + result[:25])
    assert [c.title for c in read_claude(world)] == ["Onboarding", "Landing design", "Launch notes", "Elf kit"]
    with path.open("a", encoding="utf-8") as f:
        f.write(result[25:] + "\n")                        # the line is whole now: read from where it was left
    assert read_claude(world)[-1].title == "Late page"


def test_claude_an_unchanged_file_is_not_parsed_again_and_a_grown_one_is_read_on(world, monkeypatch):
    path = _claude(world)
    parsed = []
    real = canvases._feed
    monkeypatch.setattr(canvases, "_feed", lambda tail, p, line: (parsed.append((p.name, tail.offset)), real(tail, p, line))[1])
    first = read_claude(world)
    assert read_claude(world) == first and parsed == [("sess-1.jsonl", 0)]      # the second pass opened nothing
    call = {"type": "assistant", "timestamp": "2026-10-25T12:00:00.000Z", "message": {"model": "m", "content": [
        {"type": "tool_use", "id": "x1", "name": "Artifact", "input": {"title": "Next page"}}]}}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(call) + "\n")
    grown = read_claude(world)
    assert [n for n, _ in parsed] == ["sess-1.jsonl"] * 2 and parsed[1][1] > 0     # read on from where it was, not again
    assert grown == first                                                     # the call has no answer yet: no canvas
    with path.open("a", encoding="utf-8") as f:                               # its answer comes in a later read
        f.write(json.dumps({"type": "user", "timestamp": "2026-10-25T12:00:03.000Z", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "x1", "content": "https://claude.ai/artifact/n3x7"}]}}) + "\n")
    assert [c.title for c in read_claude(world)][-1] == "Next page" and len(parsed) == 3
    path.write_text("", encoding="utf-8")                                     # a file that shrank is read again
    assert read_claude(world) == []


def test_claude_is_bounded_in_files_and_in_bytes(world, monkeypatch):
    for i, name in enumerate(("old", "mid", "new")):
        _claude(world, name, mtime=1_000_000 + i)
    monkeypatch.setattr(sessions, "MAX_LOCAL", 2)
    assert {c.session for c in read_claude(world)} == {"mid", "new"}            # the newest files only
    canvases._CLAUDE.clear()
    monkeypatch.setattr(sessions, "MAX_LOCAL", 60)
    first = (FIXTURES / "claude_session.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)[:3]
    monkeypatch.setattr(transcripts, "MAX_BYTES", sum(map(len, first[:3])) + 5)
    _claude(world, "big", mtime=2_000_000)
    assert [c.title for c in read_claude(world) if c.session == "big"] == ["Onboarding"]   # nothing past the cap


def test_claude_never_raises(world):
    assert read_claude(world) == []                                             # no folder at all
    folder = sessions.claude_projects_dir(world)
    folder.mkdir(parents=True)
    (folder / "binary.jsonl").write_bytes(b"\xff\xfe\x00{\n" * 10)
    (folder / "dir.jsonl").mkdir()
    assert read_claude(world) == []


# -- Codex ------------------------------------------------------------------------------------------------------------

def test_codex_reads_pictures_and_mcp_calls_of_the_rollouts_under_the_project(world):
    home = Path(os.environ["CODEX_HOME"])
    _codex(world)
    found = _by_title(read_codex(world))
    assert set(found) == {"A pixel elf with a lantern, facing left.", "Elf kit", "Flow sketch"}   # no failed, no Canva Err
    pic = found["A pixel elf with a lantern, facing left."]
    assert (pic.tool, pic.kind, pic.url, pic.session, pic.model) == ("codex", "picture", "", SESSION_ID, "gpt-6-luna")
    assert pic.file == str(home / "generated_images" / SESSION_ID / "ig_0001.png")      # the end event's `saved_path`
    assert pic.at == "2026-10-25T10:00:30.050Z"
    fig, td = found["Elf kit"], found["Flow sketch"]
    assert (fig.kind, fig.url, fig.at) == ("design", "https://www.figma.com/design/AbCdEf123/Elf-kit", "2026-10-25T10:02:04.000Z")
    assert (td.kind, td.url, td.at, td.model) == ("design", "https://www.tldraw.com/r/abc123", "2026-10-25T10:03:02.000Z", "gpt-6-luna")


def test_codex_a_picture_with_no_saved_path_is_the_file_codex_keeps_when_it_is_there(world):
    home = Path(os.environ["CODEX_HOME"])
    _codex(world)
    assert "A goblin with a ledger" not in _by_title(read_codex(world))             # no file, no picture
    kept = home / "generated_images" / SESSION_ID / "ig_0002.png"
    kept.parent.mkdir(parents=True)
    kept.write_bytes(b"png")
    assert _by_title(read_codex(world))["A goblin with a ledger"].file == str(kept)


def test_codex_a_rollout_of_another_folder_is_ignored_and_one_in_a_subfolder_is_the_projects(world, tmp_path):
    other = (tmp_path / "other").resolve()
    other.mkdir()
    _codex(world, cwd=other)
    assert read_codex(world) == []
    (world / "sub").mkdir()
    _codex(world, cwd=world / "sub", name=f"rollout-2026-10-25T10-00-00-{SESSION_ID}-b")   # a rollout's `cwd` never changes
    assert len(read_codex(world)) == 3


def test_codex_reads_a_paginated_rollouts_items_and_a_broken_line_is_skipped(world):
    meta = {"timestamp": "2026-10-25T09:00:00.000Z", "type": "session_meta", "payload": {"id": "thread-9", "cwd": str(world)}}
    img = {"timestamp": "2026-10-25T09:01:00.000Z", "type": "event_msg", "payload": {"type": "item_completed", "item": {
        "type": "Extension", "kind": "image_gen.generation", "id": "ig_9", "status": "completed", "revisedPrompt": "A gnome\nwith a flag",
        "result": "Zm9v", "savedPath": "/saved/ig_9.png"}}}
    mcp = {"timestamp": "2026-10-25T09:02:00.000Z", "type": "event_msg", "payload": {"type": "item_completed", "item": {
        "type": "McpToolCall", "id": "c1", "server": "canva", "tool": "create_design", "arguments": {"title": "Poster"},
        "status": "completed", "result": {"content": [{"type": "text", "text": "https://www.canva.com/design/xyz/edit"}]}}}}
    text = "\n".join([json.dumps(meta), "garbage{", json.dumps(img), json.dumps(mcp)]) + "\n"
    _codex(world, text=text)
    found = _by_title(read_codex(world))
    assert (found["A gnome"].file, found["A gnome"].session, found["A gnome"].kind) == ("/saved/ig_9.png", "thread-9", "picture")
    assert (found["Poster"].url, found["Poster"].kind) == ("https://www.canva.com/design/xyz/edit", "design")


def test_codex_an_unchanged_rollout_is_not_parsed_again(world, monkeypatch):
    _codex(world)
    parsed = []
    real = canvases._feed
    monkeypatch.setattr(canvases, "_feed", lambda tail, p, line: (parsed.append(p.name), real(tail, p, line))[1])
    first = read_codex(world)
    assert read_codex(world) == first and len(parsed) == 1


def test_codex_never_raises(world):
    assert read_codex(world) == []                                              # no `~/.codex` at all
    _codex(world, text="\x00\x01 not a rollout\n{\"type\": \"session_meta\", \"payload\": 5}\n")
    assert read_codex(world) == []


# -- agy --------------------------------------------------------------------------------------------------------------

def test_agy_reads_the_pictures_of_a_conversation_but_no_screenshot_recording_plan_or_hidden_file(world):
    folder = _agy()
    found = read_agy(world, ["conv-1"])
    assert len(found) == 1
    pic = found[0]
    assert (pic.tool, pic.kind, pic.title, pic.session, pic.model, pic.url) == (
        "agy", "picture", "A pixel elf with a lantern, facing left", "conv-1", "", "")
    assert pic.file == str(folder / "elf_portrait.png") and pic.at == "2026-10-25T10:20:00+00:00"   # the file's time


def test_agy_a_picture_without_metadata_is_titled_by_its_name_and_only_named_conversations_are_read(world):
    _agy()
    _agy("conv-2")
    (sessions.agy_brain_dir() / "conv-2" / "elf_portrait.png.metadata.json").unlink()
    assert [c.title for c in read_agy(world, ["conv-2"])] == ["elf portrait"]
    assert read_agy(world, []) == []
    assert read_agy(world, ["unknown"]) == []


@pytest.mark.parametrize("bad", ["../conv-1", "conv-1/..", "a/b", "", "..", ".hidden", "/etc"])
def test_agy_an_id_that_is_not_a_plain_name_is_skipped(world, bad):
    _agy()
    assert read_agy(world, [bad]) == []


# -- all of them ------------------------------------------------------------------------------------------------------

def test_read_all_is_every_canvas_oldest_first_and_a_canvas_drawn_again_is_one(world):
    _claude(world)
    _codex(world)
    _agy()
    found = read_all(world, ["conv-1"])
    assert [c.at for c in found] == sorted(c.at for c in found) and len(found) == 8
    assert {c.tool for c in found} == {"claude", "codex", "agy"}
    again = json.dumps({"type": "assistant", "timestamp": "2026-10-25T13:00:00.000Z", "message": {"model": "m", "content": [
        {"type": "tool_use", "id": "again", "name": "Artifact", "input": {"title": "Onboarding v2", "action": "publish"}}]}})
    back = json.dumps({"type": "user", "timestamp": "2026-10-25T13:00:03.000Z", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "again", "content": "https://claude.ai/artifact/a1b2c3"}]}})
    with next(iter(sessions.claude_projects_dir(world).glob("*.jsonl"))).open("a", encoding="utf-8") as f:
        f.write(again + "\n" + back + "\n")
    found = read_all(world, ["conv-1"])
    page = [c for c in found if c.url == "https://claude.ai/artifact/a1b2c3"]
    assert len(found) == 8 and [(c.title, c.at) for c in page] == [("Onboarding v2", "2026-10-25T13:00:03.000Z")]
    assert found[-1] is page[0]


def test_read_all_a_reader_that_fails_gives_nothing_and_the_others_go_on(world, monkeypatch):
    _claude(world)
    _agy()

    def broken(_):
        raise RuntimeError("a format that changed")
    monkeypatch.setattr(canvases, "read_codex", broken)
    found = read_all(world, ["conv-1"])
    assert {c.tool for c in found} == {"claude", "agy"}
    assert read_all(world) == read_claude(world)                                 # no agy conversation named: none read
