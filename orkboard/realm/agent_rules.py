"""The Board's rules for any AI tool, written into the project (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md part C; decisions §255.5–§255.6, §255.11).

    agent_rules.write(root, wiki_rel)           # the files below written; the paths from `root` that changed (a file that is as the package makes it is not touched)
    agent_rules.check(root, wiki_rel)           # [{path, what}] for each Orkboard file or block that is not the package's: missing · outdated · changed (by hand) · broken · not ours
    agent_rules.has_rules(root)                 # the project has Orkboard's block in its AGENTS.md
    agent_rules.refresh(root, wiki_rel)         # {written, by_hand}: what `check` found written again, a block or file changed by hand written back (the host's start, C.5)

| File | What |
|---|---|
| `AGENTS.md`, `CLAUDE.md` (root) | Orkboard's block between `<!-- orkboard:begin schema=1 hash=… -->` and `<!-- orkboard:end -->`; `CLAUDE.md`'s holds `@AGENTS.md` |
| `<wiki>/BOARD.md` | Orkboard's whole file: the page's format, the phases, a question's line, the gate's record, taking a goal |
| `<wiki>/AGENTS.md`, `<wiki>/CLAUDE.md` | a pointer to BOARD.md, as a block added to the file the folder has (an LLM wiki's own pointer stays) |
| `<wiki>/roles/<id>.md` | a seat's instruction, from the code its prompt is built from (`orkmaster`, `<craft>-leader`, `taskmaster`, `grunt`) |
| `.claude/agents/ork-<id>.md` | Claude Code's subagent for each role: its `tools` (a Grunt every tool, in a `worktree`) and `model` (spec 154 C.1) |
| `.claude/skills/<id>/SKILL.md` | a forked skill for each seat that has steps (`orkmaster`, `<craft>-leader`, `taskmaster`), run as its subagent (spec 154 C.2) |
| `.claude/skills/orkboard/SKILL.md` | the conductor: the way of a goal through those skills (spec 154 C.3) |

The person's own text in a file that holds a block is kept byte for byte; only Orkboard's block, and only Orkboard's own files, are written. A file at an Orkboard path that carries no stamp is the
person's own and is left. Each block and file carries `schema` and the hash of its text (`agent_rules_text.digest`): a hash that is not the text's was changed by hand; a text that is not the package's
is outdated. Pure files: no model, no git (the host commits the paths written, through the Board's tree).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from orkboard.realm import agent_rules_text as T
from orkboard.realm import seat_frames

AGENTS, CLAUDE = "AGENTS.md", "CLAUDE.md"
HASH_LINE = re.compile(r"^hash: ([0-9a-f]*)[ \t]*$", re.M)
SCHEMA_LINE = re.compile(r"^schema: (\d+)[ \t]*$", re.M)
MODELS = ("opus", "sonnet", "haiku")
OK, MISSING, OUTDATED, CHANGED, BROKEN, NOT_OURS = "ok", "missing", "outdated", "changed", "broken", "not ours"


@dataclass(frozen=True)
class Item:
    """One thing the rules make: a `block` in a file the person may hold text in, or an Orkboard `file` of its own (`text` complete, hash not yet stamped)."""
    kind: str
    path: str
    text: str
    lead: str = ""                     # a block's file made new holds this line above the block


# -- what the project has ------------------------------------------------------------------------------------------------------------------------------------

def _wiki(wiki_rel: str) -> str:
    wiki = str(wiki_rel or "").strip().strip("/")
    if ".." in Path(wiki).parts:
        raise ValueError("The Board's folder lies inside the project")
    return wiki


def decisions_of(root: Path, chosen: str = "") -> str:
    """The place of the project's decisions, from `root` (`decisions_log.path`: its file or its ADR folder, a folder said with a closing slash)."""
    from orkboard.realm import decisions_log
    base = Path(root)
    where = decisions_log.path(base, chosen)
    rel = where.relative_to(base).as_posix()
    return rel + "/" if decisions_log.is_folder(base, chosen) else rel


def crafts_of(root: Path, wiki_rel: str) -> list[str]:
    """The crafts the project's parties have, once each in the Board's order: the parties a goal's route may name (`goal_route.parties`), by `goal_team.craft_of`."""
    from orkboard.realm import goal_route, goal_team
    wiki_dir = Path(root) / _wiki(wiki_rel)
    out: list[str] = []
    try:
        for p in goal_route.parties(wiki_dir):
            craft = goal_team.craft_of(wiki_dir, p["slug"])
            if craft and craft not in out:
                out.append(craft)
    except OSError:
        pass
    return out


def ids_of(crafts: list[str]) -> list[str]:
    """The role ids: `orkmaster`, `<craft>-leader` for each craft, `taskmaster`, `grunt`."""
    return ["orkmaster", *[f"{c}-leader" for c in crafts], "taskmaster", "grunt"]


def _race(craft: str) -> str:
    from orkboard.realm import roles
    members = roles.PARTY_RACES.get(craft, (roles.RACES[roles.DEFAULT_CRAFT],) * 2)[0]
    return T.RACE_WORDS.get(members, members)


def _seat(role_id: str) -> tuple[str, str]:
    """`(seat, craft)` of a role id."""
    if role_id.endswith("-leader"):
        return "leader", role_id[:-len("-leader")]
    return role_id, ""


def _title(role_id: str) -> str:
    seat, craft = _seat(role_id)
    return f"The {craft.replace('-', ' ')} leader" if seat == "leader" else seat.capitalize() if seat != "orkmaster" else "The Orkmaster"


def _describe(role_id: str) -> str:
    seat, craft = _seat(role_id)
    return {"orkmaster": "Routes a goal of this project's Board: names the parties that write its spec and do its work. Use it for a goal in phase new.",
            "leader": f"Speaks for the {craft.replace('-', ' ')} party of this project's Board: its view in Talk and its section of a goal's spec. Use it for a goal in phase talk or spec.",
            "taskmaster": "Plans a goal's work on this project's Board in stages and keeps it. Use it for a goal in phase work.",
            "grunt": "Does one task of a goal's work on this project's Board, in a branch of its own. Use it for a task of a goal in phase work."}[seat]


def _front(pairs: list[tuple[str, str]]) -> str:
    return "---\n" + "".join(f"{v}\n" if k == "#" else f"{k}: {v}\n" for k, v in pairs) + f"schema: {T.SCHEMA}\nhash: \n---\n"


def model_of(role_id: str) -> str:
    """The model a seat's subagent names in Claude Code (spec 154 C.1): the seat's tier through Orkboard's own tier table for Claude Code (`harnesses.model_on`), one of `opus`, `sonnet`, `haiku`; `inherit`
    where it names none. A leader's tier is its party's (`party_recipes.tiers_for`: Veteran, the Release manager's Seasoned), the Taskmaster's and a Grunt's their roles' (`library`); the Orkmaster has no role in the library."""
    from orkboard.realm import harnesses, library, party_recipes
    seat, craft = _seat(role_id)
    if seat == "leader":
        lead = library.RELEASE_MANAGER if craft == party_recipes.RELEASE else role_id
        tier = party_recipes.tiers_for(lead, [], "standard").get(lead, "")
    else:
        agent = library.get(seat)
        tier = agent.tier if agent is not None else ""
    model = harnesses.model_on("claude", tier) if tier else ""
    return model if model in MODELS else "inherit"


def _agent_front(role_id: str, seat: str) -> str:
    pairs = [("name", f"ork-{role_id}"), ("description", json.dumps(_describe(role_id), ensure_ascii=False)), ("#", T.CLAUDE_OWN_AGENT)]
    if seat == "grunt":
        pairs += [("model", model_of(role_id)), ("isolation", "worktree")]           # every tool: `tools` left out inherits them all
    else:
        pairs += [("tools", T.FILE_TOOLS), ("model", model_of(role_id))]
    return _front(pairs)


def items(root: Path, wiki_rel: str, crafts: list[str] | None = None, decisions: str | None = None) -> list[Item]:
    """Everything the rules make for this project, in the order they are written. `crafts`: the project's (`crafts_of`); `decisions`: the decisions' place (`decisions_of`)."""
    wiki = _wiki(wiki_rel)
    crafts = crafts_of(root, wiki) if crafts is None else list(crafts)
    decisions = decisions_of(root) if decisions is None else decisions
    shown = wiki or "."
    base = f"{wiki}/" if wiki else ""
    out = [Item("block", AGENTS, T.agents_body(shown, decisions), T.OWN_LINE),
           Item("block", CLAUDE, T.claude_body()),
           Item("file", f"{base}BOARD.md", T.FILE_MARK.format(schema=T.SCHEMA, hash="") + "\n" + T.board_md(shown, decisions))]
    if wiki:                                                   # a Board folder of its own: a pointer where a tool loads the folder's file
        out += [Item("block", f"{wiki}/{AGENTS}", T.pointer_body()), Item("block", f"{wiki}/{CLAUDE}", T.pointer_body())]
    for role_id in ids_of(crafts):
        seat, craft = _seat(role_id)
        name = _title(role_id)
        race = _race(craft) if craft else "ork"
        out.append(Item("file", f"{base}roles/{role_id}.md",
                        _front([("seat", seat), ("craft", craft or ("tech" if seat in ("taskmaster", "grunt") else "none")), ("race", race)]) + T.role_body(seat, craft, shown, decisions, name)))
    for role_id in ids_of(crafts):
        seat, craft = _seat(role_id)
        out.append(Item("file", f".claude/agents/ork-{role_id}.md",
                        _agent_front(role_id, seat) + T.subagent_body(seat, craft, shown, decisions, _title(role_id), f"{base}roles/{role_id}.md")))
    for role_id in ids_of(crafts):                                # a skill for each seat that has steps (a Grunt has none), run forked as the seat's subagent; the caller waits for its line
        if role_id != "grunt" and seat_frames.steps(role_id):
            out.append(Item("file", f".claude/skills/{role_id}/SKILL.md",
                            _front([("name", role_id), ("description", json.dumps(T.skill_description(role_id, seat_frames.title_of(role_id)), ensure_ascii=False)), ("#", T.CLAUDE_OWN),
                                    ("argument-hint", '"<step> <goal>"'), ("context", "fork"), ("agent", f"ork-{role_id}"), ("background", "false")])
                            + T.seat_skill_body(role_id, shown, decisions)))
    out.append(Item("file", ".claude/skills/orkboard/SKILL.md",
                    _front([("name", "orkboard"), ("description", json.dumps(T.SKILL_DESCRIPTION, ensure_ascii=False)), ("#", T.CLAUDE_OWN_STANDARD)]) + T.skill_body(shown)))
    return out


# -- stamps --------------------------------------------------------------------------------------------------------------------------------------------------

def _neutral(text: str) -> tuple[str | None, str]:
    """`(recorded hash, the text with it left empty)` of an Orkboard file: its front matter's `hash:` line, or BOARD.md's first line. None when the file carries no stamp."""
    if (m := T.FILE_RE.match(text)):
        return m.group(2), text[:m.start(2)] + text[m.end(2):]
    head = text.split("\n---\n", 1)[0] if text.startswith("---\n") else ""
    if head and (m := HASH_LINE.search(head)):
        return m.group(1), text[:m.start(1)] + text[m.end(1):]
    return None, text


def stamped(text: str) -> str:
    """An Orkboard file's text with its hash filled in."""
    _recorded, neutral = _neutral(text)
    h = T.digest(neutral)
    if (m := T.FILE_RE.match(neutral)):
        return neutral[:m.start(2)] + h + neutral[m.start(2):]
    m = HASH_LINE.search(neutral)
    return neutral[:m.start(1)] + h + neutral[m.start(1):] if m else neutral


def block_text(body: str) -> str:
    """The block as the file holds it: its begin marker with the schema and the hash of the body, the body, its end marker."""
    return T.BEGIN.format(schema=T.SCHEMA, hash=T.digest(body)) + "\n" + body.strip("\n") + "\n" + T.END


def find_block(text: str) -> tuple[int, int, str, str, str] | None:
    """`(start, end, schema, hash, body)` of Orkboard's block in a file's text, the span including both markers; None for a file with no complete block."""
    m = T.BEGIN_RE.search(text)
    if not m:
        return None
    end = text.find(T.END, m.end())
    if end < 0:
        return None
    return m.start(), end + len(T.END), m.group(1), m.group(2), text[m.end():end].replace("\r\n", "\n").strip("\n")


def _read(path: Path) -> str | None:
    try:
        return path.read_bytes().decode("utf-8", "surrogateescape")
    except OSError:
        return None


def _put(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8", "surrogateescape"))


def _with_block(old: str | None, item: Item) -> str | None:
    """The file's new text with Orkboard's block in it, the person's text byte for byte; None where the file is broken (a begin marker with no end) and left."""
    nl = "\r\n" if old and "\r\n" in old else "\n"
    block = block_text(item.text).replace("\n", nl)
    if old is None:
        return (item.lead + nl + nl if item.lead else "") + block + nl
    if (got := find_block(old)) is not None:
        return old[:got[0]] + block + old[got[1]:]
    if T.BEGIN_RE.search(old):
        return None
    if not old.strip():
        return block + nl
    return old + ("" if old.endswith("\n") else nl) + nl + block + nl


# -- write, check ------------------------------------------------------------------------------------------------------------------------------------------

def write(root: Path, wiki_rel: str, crafts: list[str] | None = None, decisions: str | None = None, only: set[str] | None = None) -> list[str]:
    """The rules written into the project at `root`: the paths (from `root`) that changed. A block's file keeps the person's text; an Orkboard file is written whole; a file at an Orkboard path with no
    stamp is the person's and stays; a file that is as the package makes it is not touched, so writing twice changes nothing. `only`: write just these paths."""
    root, written = Path(root), []
    for item in items(root, wiki_rel, crafts, decisions):
        if only is not None and item.path not in only:
            continue
        path = root / item.path
        old = _read(path) if path.is_file() else None
        if item.kind == "block":
            new = _with_block(old, item)
        else:
            new = stamped(item.text)
            if old is not None and _neutral(old)[0] is None:
                continue                                             # not Orkboard's: the person's own file
        if new is None or new == old:
            continue
        _put(path, new)
        written.append(item.path)
    return written


def has_rules(root: Path) -> bool:
    """The project has Orkboard's block in its root AGENTS.md."""
    text = _read(Path(root) / AGENTS)
    return text is not None and find_block(text) is not None


def check(root: Path, wiki_rel: str, crafts: list[str] | None = None, decisions: str | None = None) -> list[dict]:
    """`[{path, what}]` for every block and file of the rules that is not the package's, by hash: `missing`, `outdated` (the package's text changed; the file is as it was written), `changed` (the text is
    not the one its hash says: changed by hand), `broken` (a begin marker with no end), `not ours` (a file at an Orkboard path with no stamp). Nothing for one that is as it should be."""
    root, out = Path(root), []
    for item in items(root, wiki_rel, crafts, decisions):
        path = root / item.path
        old = _read(path) if path.is_file() else None
        if old is None:
            out.append({"path": item.path, "what": MISSING})
        elif item.kind == "block":
            got = find_block(old)
            if got is None:
                out.append({"path": item.path, "what": BROKEN if T.BEGIN_RE.search(old) else MISSING})
            elif T.digest(got[4]) != got[3]:
                out.append({"path": item.path, "what": CHANGED})
            elif got[3] != T.digest(item.text) or int(got[2]) != T.SCHEMA:
                out.append({"path": item.path, "what": OUTDATED})
        else:
            recorded, neutral = _neutral(old)
            if recorded is None:
                out.append({"path": item.path, "what": NOT_OURS})
            elif T.digest(neutral) != recorded:
                out.append({"path": item.path, "what": CHANGED})
            elif old != stamped(item.text):
                out.append({"path": item.path, "what": OUTDATED})
    return out


def refresh(root: Path, wiki_rel: str, crafts: list[str] | None = None, decisions: str | None = None) -> dict:
    """The rules written again where the package's text differs (C.5), for a project that has them: `{written: [paths], by_hand: [lines]}`. Only Orkboard's blocks and files are written; one changed by
    hand is written back and said (`by_hand`, one line each: `agent_rules_text.BYHAND`). A project without the rules, and a file that is not Orkboard's, are left."""
    if not has_rules(root):
        return {"written": [], "by_hand": []}
    wiki = _wiki(wiki_rel)
    found = [f for f in check(root, wiki, crafts, decisions) if f["what"] in (MISSING, OUTDATED, CHANGED)]
    if not found:
        return {"written": [], "by_hand": []}
    shown = lambda p: p[len(wiki) + 1:] if wiki and p.startswith(f"{wiki}/roles/") else p     # noqa: E731  (a role as the line names it: roles/tech-leader.md)
    return {"written": write(root, wiki, crafts, decisions, only={f["path"] for f in found}),
            "by_hand": [T.BYHAND.format(path=shown(f["path"])) for f in found if f["what"] == CHANGED]}
