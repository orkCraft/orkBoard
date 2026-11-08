"""Run a craft tool through the existing pick lifecycle (spec 158 C)."""
from __future__ import annotations

import json
from pathlib import Path

from orkboard.core import craft_run, craft_spend
from orkboard.realm import craft_tools, goal_route, idea_pick, ideas
from orkboard.realm.board_tree import spec_paths


def available(root: Path, party: str, harness: str = "") -> dict:
    return {r["id"]: r for r in craft_tools.for_party(root, party, harness or goal_route.party_tool(root, party))
            if r["taken"] and r["here"]}


def plan_lines(root: Path, party: str) -> str:
    rows = available(root, party)
    return ("\nCraft tools available for pick.tool (use only these ids, with image or audio picks): "
            + json.dumps([{k: r[k] for k in ("id", "makes", "cap")} for r in rows.values()]) + "\n")


def clean_plan(plan: dict, root: Path, party: str) -> None:
    allowed = available(root, party)
    for task in plan.get("tasks", []):
        pick = task.get("pick") or {}
        if pick.get("tool") and pick["tool"] not in allowed:
            pick.pop("tool", None)


def board_root(runner, slug: str) -> Path:
    rel, _ = spec_paths(runner.repo_root, runner.state_dir, slug)
    for base in (runner.state_dir / "board", runner.repo_root):
        if rel and (base / rel).is_file():
            return (base / rel).parent.parent.parent
    raise ValueError("The tool's party could not be read from the Board")


def session(runner, slug, tid, task, path, cancel, model, env, prompt, resume, spent, effort):
    ask = idea_pick.ask_of(task) or {}
    tool_id = ask.get("tool")
    if not tool_id:
        return runner._session(slug, tid, path, cancel, model, env, prompt, resume, spent, effort)
    root = board_root(runner, slug)
    page = ideas.idea_page(root, slug)
    party = task.get("party") or (page.get("track") if page else "") or ideas.GENERAL
    rows = {r["id"]: r for r in craft_tools.for_party(root, party, runner.tool_of(slug, task), check_key=False)}
    row = rows.get(tool_id)
    if not row or not row["taken"]:
        raise ValueError("The party has not taken that tool")
    if not row["here"]:
        raise ValueError(f"{row['title']} is not here: {row['why']}")
    makers = {"openai-images": ("image", craft_run.PictureMaker), "elevenlabs-sound": ("audio", craft_run.SoundMaker)}
    kind, maker = makers.get(tool_id, (None, None))
    if kind != ask["kind"] or maker is None:
        raise ValueError("That tool cannot make this pick's kind")
    if cancel.is_set():
        raise InterruptedError("stopped")
    idea_pick.discard(path)
    spend = craft_spend.Spend(runner.state_dir, slug, tid, tool_id, row["cap"])
    try:
        files = maker(spend=spend).make(ask["ask"] + ("\n" + task["why"] if task.get("why") else ""),
                                       path / idea_pick.PICK_DIR, count=ask["n"])
    finally:
        task.update(craft_cost=spend.cost(), craft_cap=row["cap"])
        runner._set_task(slug, tid, craft_cost=task["craft_cost"], craft_cap=task["craft_cap"])
    try:
        (path / idea_pick.PICK_FILE).write_text(json.dumps({"variants": [
            {"name": f"Variant {i + 1}", "file": f.name, "why": ""} for i, f in enumerate(files)]}), encoding="utf-8")
    except BaseException:
        idea_pick.discard(path)
        raise
    return ""
