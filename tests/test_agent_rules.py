"""Spec 151 C (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md; decisions §255.5–§255.6): the Board's rules for any AI tool, written into the project.

The block into a missing file and into one with the person's text (kept byte for byte), written again in place and never twice, `CLAUDE.md`'s import, the wiki's own pointer kept and added to, each role
file holding its prompt's fixed text, a changed file written back and said, nothing written without the yes, the block at most 60 lines. No model is called."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.core import idea_accept, idea_sections, idea_talk
from orkboard.gui.board_host import Orkboard
from orkboard.realm import agent_rules, agent_rules_text, goal_route, goal_team, ideas, library, roles

WIKI = "llm-wiki/general"
DECISIONS = "docs/decisions.md"
PERSON = "# Our rules\n\nUse tabs.\n\nNever touch the vendor folder.\n"


def project(tmp_path: Path, crafts=("engineering", "design")) -> Path:
    """A project folder with the Board's folder holding a party for each craft."""
    root = tmp_path / "shop"
    wiki = root / WIKI
    wiki.mkdir(parents=True)
    for title, craft, leader in (("Tech", "engineering", "architect"), ("Design", "design", "product-designer"), ("Product", "product", "product-manager")):
        if craft in crafts:
            slug, _new = ideas.save_goal(wiki, None, title, "About " + title, None, "normal", craft=craft)
            goal_team.set_team(wiki, slug, [], leader=leader)
    return root


def write(root: Path, **more) -> list[str]:
    return agent_rules.write(root, WIKI, decisions=DECISIONS, **more)


def check(root: Path) -> list[dict]:
    return agent_rules.check(root, WIKI, decisions=DECISIONS)


def test_the_block_goes_into_a_missing_file_with_the_one_line_and_every_file_is_made(tmp_path):
    root = project(tmp_path)
    written = write(root)
    text = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert text.startswith(agent_rules_text.OWN_LINE + "\n\n<!-- orkboard:begin schema=3 hash=") and text.endswith("<!-- orkboard:end -->\n")
    assert f"`{WIKI}/pages/ideas/<slug>.md`" in text and f"`{DECISIONS}`" in text and f"`{WIKI}/BOARD.md`" in text
    assert written == ["AGENTS.md", "CLAUDE.md", f"{WIKI}/BOARD.md", f"{WIKI}/AGENTS.md", f"{WIKI}/CLAUDE.md",
                       *[f"{WIKI}/roles/{i}.md" for i in ("orkmaster", "tech-leader", "design-leader", "taskmaster", "grunt")],
                       *[f".claude/agents/ork-{i}.md" for i in ("orkmaster", "tech-leader", "design-leader", "taskmaster", "grunt")],
                       *[f".claude/skills/{i}/SKILL.md" for i in ("orkmaster", "tech-leader", "design-leader", "taskmaster")], ".claude/skills/orkboard/SKILL.md"]
    assert check(root) == [] and agent_rules.has_rules(root)


def test_the_persons_own_text_above_and_below_the_block_is_kept_byte_for_byte_and_the_block_is_written_in_place(tmp_path, monkeypatch):
    root = project(tmp_path)
    (root / "AGENTS.md").write_bytes("Mine, above — ünï.\r\n\r\n".encode("utf-8"))
    write(root)
    first = (root / "AGENTS.md").read_bytes()
    assert first.startswith("Mine, above — ünï.\r\n\r\n".encode("utf-8")) and b"\r\n<!-- orkboard:end -->\r\n" in first
    below = "\r\n\r\nMine, below.\r\n  indented\twith a tab, no newline at the end".encode("utf-8")
    (root / "AGENTS.md").write_bytes(first + below)
    monkeypatch.setattr(agent_rules_text, "agents_body", lambda wiki, decisions: "## The Board (Orkboard)\n\nA newer text.")      # the package's text changes
    assert [f["what"] for f in check(root) if f["path"] == "AGENTS.md"] == ["outdated"]
    assert write(root, only={"AGENTS.md"}) == ["AGENTS.md"]
    now = (root / "AGENTS.md").read_bytes()
    assert now.startswith("Mine, above — ünï.\r\n\r\n".encode("utf-8")) and now.endswith(below) and b"A newer text." in now and now.count(b"orkboard:begin") == 1
    assert [f for f in check(root) if f["path"] == "AGENTS.md"] == []


def test_each_role_file_holds_its_prompts_fixed_text_and_its_front_matter(tmp_path):
    root = project(tmp_path, crafts=("engineering", "design", "product"))
    write(root)
    roles_dir = root / WIKI / "roles"
    assert sorted(p.stem for p in roles_dir.glob("*.md")) == sorted(["orkmaster", "tech-leader", "design-leader", "product-leader", "taskmaster", "grunt"])
    orkmaster = (roles_dir / "orkmaster.md").read_text(encoding="utf-8")
    assert goal_route.rules() in orkmaster and idea_sections.join_rules() in orkmaster and "Read no file" not in orkmaster and "JSON" not in orkmaster
    for craft in ("tech", "design", "product"):
        text = (roles_dir / f"{craft}-leader.md").read_text(encoding="utf-8")
        assert idea_talk.rules(craft) in text and idea_sections.rules() in text and "## Accepting a step\n\n" + idea_accept.rules() in text and "## What it reads" in text
        assert "Read no file" not in text and "one JSON object" not in text and "(The context follows" not in text        # a call's frame is the call's (§258.7)
        assert f"seat: leader\ncraft: {craft}\nrace: " in text and f"schema: {agent_rules_text.SCHEMA}\nhash: " in text
    assert "race: elf\n" in (roles_dir / "design-leader.md").read_text(encoding="utf-8") and "race: knight\n" in (roles_dir / "product-leader.md").read_text(encoding="utf-8")
    assert "race: ork\n" in (roles_dir / "tech-leader.md").read_text(encoding="utf-8")
    for seat in ("taskmaster", "grunt"):
        assert roles.rules(seat) in (roles_dir / f"{seat}.md").read_text(encoding="utf-8")
    assert f"`{WIKI}/journals/tech.md`" not in (roles_dir / "grunt.md").read_text(encoding="utf-8")
    agent = (root / ".claude/agents/ork-tech-leader.md").read_text(encoding="utf-8")
    assert agent.startswith("---\nname: ork-tech-leader\ndescription: \"") and idea_talk.rules("tech") in agent and "Read no file" not in agent and "one JSON object" not in agent and f"Read `{WIKI}/BOARD.md` first" in agent
    skill = (root / ".claude/skills/orkboard/SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---\nname: orkboard\ndescription: \"" + agent_rules_text.SKILL_DESCRIPTION + "\"\n") and f"{WIKI}/BOARD.md" in skill


def test_a_block_or_file_changed_by_hand_is_found_and_written_back_and_said_once(tmp_path):
    root = project(tmp_path)
    write(root)
    role = root / WIKI / "roles/tech-leader.md"
    role.write_text(role.read_text(encoding="utf-8").replace("You are not here to agree.", "You agree."), encoding="utf-8")
    block = (root / "AGENTS.md").read_text(encoding="utf-8")
    (root / "AGENTS.md").write_text(block.replace("Main is the person's.", "Main is anyone's."), encoding="utf-8")
    assert {(f["path"], f["what"]) for f in check(root)} == {(f"{WIKI}/roles/tech-leader.md", "changed"), ("AGENTS.md", "changed")}
    got = agent_rules.refresh(root, WIKI, decisions=DECISIONS)
    assert sorted(got["written"]) == sorted(["AGENTS.md", f"{WIKI}/roles/tech-leader.md"])
    assert "roles/tech-leader.md was changed by hand: Orkboard's own is written back; a project's own role is made on Agents." in got["by_hand"]
    assert "AGENTS.md was changed by hand: Orkboard's own is written back; a project's own role is made on Agents." in got["by_hand"]
    assert check(root) == [] and "Main is the person's." in (root / "AGENTS.md").read_text(encoding="utf-8")
    assert agent_rules.refresh(root, WIKI, decisions=DECISIONS) == {"written": [], "by_hand": []}                  # said once: the next start finds nothing


def test_an_outdated_file_is_written_again_without_a_word_and_a_project_without_the_rules_is_left_alone(tmp_path, monkeypatch):
    root = project(tmp_path)
    assert agent_rules.refresh(root, WIKI, decisions=DECISIONS) == {"written": [], "by_hand": []} and not (root / "AGENTS.md").exists()
    write(root)
    monkeypatch.setattr(agent_rules_text, "skill_body", lambda wiki: "# A newer skill\n")
    assert [f["what"] for f in check(root)] == ["outdated"]
    got = agent_rules.refresh(root, WIKI, decisions=DECISIONS)
    assert got == {"written": [".claude/skills/orkboard/SKILL.md"], "by_hand": []} and "A newer skill" in (root / ".claude/skills/orkboard/SKILL.md").read_text(encoding="utf-8")


# -- Settings' line and the host (C.4, C.5) ---------------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def seed(host) -> None:
    """A party and a goal, so the Board has pages and its tree stands."""
    root = host.ideas.root()
    slug, _new = ideas.save_goal(root, None, "Tech", "About Tech", None, "normal", craft="engineering")
    library.install(host.ideas.state_dir, ["architect"])
    goal_team.set_team(root, slug, [], leader="architect")
    ideas.add_idea(root, "add a score board", slug, host.ideas.state_dir, "normal", "hold")


def test_the_yes_writes_the_rules_in_one_board_commit(host, fake_repo):
    seed(host)
    before = git(fake_repo, "rev-list", "--count", "--all")
    got = host.command("rules.write", {})
    assert got["ok"] and "AGENTS.md" in got["written"] and ".claude/skills/orkboard/SKILL.md" in got["written"] and got["commit"]
    assert git(host.ideas.state_dir / "board", "log", "-1", "--format=%s") == "board: the Board's rules (schema 3)"
    assert int(git(fake_repo, "rev-list", "--count", "--all")) > int(before)
    changed = git(host.ideas.state_dir / "board", "show", "--name-only", "--format=", "HEAD").splitlines()
    assert set(got["written"]) <= set(changed)
    s = host.command("rules.switch", {})
    assert s["on"] and s["status"].startswith("The Board's rules are in this project (schema 3)")
    assert host.command("rules.write", {})["written"] == []                                   # a second yes writes nothing more


def test_at_the_start_the_rules_are_written_again_where_the_package_differs_and_a_hand_change_is_said(host, fake_repo, monkeypatch):
    seed(host)
    host.command("rules.write", {})
    board = host.ideas.state_dir / "board"
    role = board / host.ideas._decision_tree().wiki_rel / "roles/tech-leader.md"
    role.write_text(role.read_text(encoding="utf-8") + "\nA line by hand.\n", encoding="utf-8")
    git(board, "add", "-A")
    git(board, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "by hand")
    toasts = []
    host.projects.current().toast = lambda message, **kw: toasts.append(message)
    monkeypatch.setattr(agent_rules_text, "skill_body", lambda wiki: "# A newer skill\n")
    host.agent_rules.start()
    assert "A line by hand." not in role.read_text(encoding="utf-8") and "A newer skill" in (board / ".claude/skills/orkboard/SKILL.md").read_text(encoding="utf-8")
    assert toasts == ["roles/tech-leader.md was changed by hand: Orkboard's own is written back; a project's own role is made on Agents."]
    assert host.command("rules.switch", {})["said"] == toasts
    assert git(board, "log", "-1", "--format=%s") == "board: the Board's rules (schema 3)"
    host.agent_rules.start()
    assert len(toasts) == 1                                                                   # said once


def test_a_direct_write_is_refused_in_words_while_fs_question_is_unanswered_or_answered_no(tmp_path, monkeypatch):
    """Spec 151 C.4, F: the switch shows F's question first (tests/test_board_in_code_card.py); a `rules.write` sent anyway is refused in words and writes nothing."""
    from types import SimpleNamespace
    from orkboard.gui import agent_rules_switch as sw
    rules = sw.AgentRules(SimpleNamespace(project=SimpleNamespace(root=tmp_path, ideas=SimpleNamespace(state_dir=tmp_path / ".orkcraft"))))
    monkeypatch.setattr(sw, "standing", lambda root, state_dir: "ask")
    with pytest.raises(ValueError) as got:
        rules.write()
    assert str(got.value) == sw.ANSWER_FIRST and not (tmp_path / "AGENTS.md").exists()
    monkeypatch.setattr(sw, "standing", lambda root, state_dir: "off")
    with pytest.raises(ValueError) as off:
        rules.write()
    assert str(off.value) == "The Board is kept off this repository: the rules would find no Board" and not (tmp_path / "AGENTS.md").exists()


# -- spec 154 C: the seats in Claude Code, and the conductor ------------------------------------------------------------------------------------------------

def front(path: Path) -> tuple[dict, str]:
    """`(the front matter's fields, the text after it)` of an Orkboard file; a `#` line is a comment and no field."""
    head, body = path.read_text(encoding="utf-8").split("\n---\n", 1)
    return dict(ln.split(": ", 1) for ln in head.splitlines()[1:] if not ln.startswith("#")), body


def test_each_seats_subagent_has_its_tools_and_model_and_a_grunt_every_tool_in_a_worktree(tmp_path):
    from orkboard.realm import harnesses
    root = project(tmp_path, crafts=("engineering", "design", "product"))
    write(root)
    for role in ("orkmaster", "tech-leader", "design-leader", "product-leader", "taskmaster"):
        fields, body = front(root / f".claude/agents/ork-{role}.md")
        assert fields["tools"] == "Read, Grep, Glob, Edit, Write" and "Bash" not in fields["tools"] and "isolation" not in fields
        assert body.startswith(f"Read `{WIKI}/BOARD.md` first, then `{WIKI}/roles/{role}.md`")
    models = {r: front(root / f".claude/agents/ork-{r}.md")[0]["model"] for r in ("orkmaster", "tech-leader", "design-leader", "taskmaster", "grunt")}
    assert models == {"orkmaster": "sonnet", "tech-leader": harnesses.model_on("claude", "warrior"), "design-leader": "sonnet", "taskmaster": "opus", "grunt": "sonnet"}
    grunt, _ = front(root / ".claude/agents/ork-grunt.md")
    assert grunt["isolation"] == "worktree" and "tools" not in grunt and "disallowedTools" not in grunt           # left out: every tool
    assert agent_rules_text.CLAUDE_OWN_AGENT in (root / ".claude/agents/ork-grunt.md").read_text(encoding="utf-8").split("\n---\n")[0]


def test_each_seat_with_steps_has_a_forked_skill_holding_its_steps_frames_and_a_grunt_has_none(tmp_path):
    from orkboard.realm import seat_frames
    root = project(tmp_path, crafts=("engineering", "design"))
    write(root)
    assert sorted(p.parent.name for p in (root / ".claude/skills").glob("*/SKILL.md")) == ["design-leader", "orkboard", "orkmaster", "taskmaster", "tech-leader"]
    for role, steps, craft in (("orkmaster", ("route",), ""), ("tech-leader", ("talk", "section", "accept"), "tech"), ("design-leader", ("talk", "section", "accept"), "design"), ("taskmaster", ("plan",), "")):
        path = root / f".claude/skills/{role}/SKILL.md"
        fields, body = front(path)
        assert fields["name"] == role and fields["context"] == "fork" and fields["agent"] == f"ork-{role}" and fields["argument-hint"] == '"<step> <goal>"' and fields["background"] == "false"
        assert fields["description"].startswith('"') and "Called by the orkboard skill, or as /" in fields["description"] and len(fields["description"]) < 300
        assert "$0" in body and "$1" in body and "stop: write nothing" in body
        assert agent_rules_text.CLAUDE_OWN in path.read_text(encoding="utf-8").split("\n---\n")[0]
        for step in steps:
            assert seat_frames.agent(role, step, craft, WIKI, DECISIONS).strip("\n") in body
        assert [s for s in ("route", "talk", "section", "accept", "plan") if f"When `$0` is `{s}`" in body] == list(steps)
    tech = front(root / ".claude/skills/tech-leader/SKILL.md")[0]["description"]
    assert tech == '"' + "Tech's leader on one goal of this project's Board: its say in Talk, its section, or its acceptance of its step. Called by the orkboard skill, or as /tech-leader talk|section|accept <goal>." + '"'
    assert not (root / ".claude/skills/grunt").exists() and not (root / ".claude/skills/ork-grunt").exists()


def test_a_project_with_two_parties_gets_two_leaders_files_not_more_and_a_changed_one_is_found(tmp_path):
    root = project(tmp_path, crafts=("engineering", "design"))
    write(root)
    files = sorted(p.name for p in (root / ".claude").rglob("*.md"))
    assert files.count("SKILL.md") == 5 and sorted(p.name for p in (root / ".claude/agents").glob("*.md")) == ["ork-design-leader.md", "ork-grunt.md", "ork-orkmaster.md", "ork-taskmaster.md", "ork-tech-leader.md"]
    assert check(root) == []
    skill = root / ".claude/skills/tech-leader/SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\nMy own step.\n", encoding="utf-8")
    agent = root / ".claude/agents/ork-grunt.md"
    agent.write_text(agent.read_text(encoding="utf-8").replace("isolation: worktree", "isolation: none"), encoding="utf-8")
    assert sorted((f["path"], f["what"]) for f in check(root)) == [(".claude/agents/ork-grunt.md", "changed"), (".claude/skills/tech-leader/SKILL.md", "changed")]
    assert sorted(agent_rules.refresh(root, WIKI, decisions=DECISIONS)["written"]) == [".claude/agents/ork-grunt.md", ".claude/skills/tech-leader/SKILL.md"] and check(root) == []

