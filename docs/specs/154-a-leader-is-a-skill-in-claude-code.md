# 154. A leader is a skill in Claude Code: each seat a subagent and a forked skill, the conductor, Talk and Accepted in the page

Decisions §258. **Builds:** the cheaper model, a part a session, each in its own worktree, reviewed by the spec's author and
merged into `main` on the critical tests and the part's own (CLAUDE.md, alpha). **Waves** (parts of a wave share no file):
**1** A, B · **2** C · **3** D. No new pane, column, drawer or dialog: nothing of the page changes. **Changes the Board's schema**
(§255.12): the page's (B) and the rules' (C).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The agent's frame of each seat** | each seat's rules one text; the call's frame unchanged; an agent's frame (read, write, give back) for *route*, *talk*, *section*, *accept*, *plan* | `realm/goal_route.py`, `core/idea_talk.py`, `core/idea_sections.py`, `core/idea_accept.py`, `realm/roles.py` (their `instruction`), a new `realm/seat_frames.py` (the agent's frames); `tests/test_agent_rules_prompts.py` (unchanged, green), a new `tests/test_seat_frames.py` |
| **B. Talk and Accepted in the page** | a party's `### Talk` and `### Accepted` read and written; BOARD.md says them; `orkboard check` reads them; the page's schema | a new `realm/page_talk.py`, `realm/goal_phase.py` (`SCHEMA`), `realm/board_check.py`, 151 C's `realm/agent_rules_text.py` (`board_md` only); a new `tests/test_page_talk.py`, `tests/test_board_check.py`, `tests/test_agent_rules.py` |
| **C. The seats in Claude Code, and the conductor** | a subagent and a forked skill a seat; their tools and model; the `orkboard` skill conducting; `orkboard check` knows the new files | `realm/agent_rules.py`, `realm/agent_rules_text.py` (all but `board_md`), `realm/board_check.py` (the files' list only); `tests/test_agent_rules.py`, `tests/test_board_check.py`, `tests/test_board_cli_goals.py` |
| **D. This repository, and the trial's arm** | `orkboard init` here; the trial gains Talk by forked skills | this repository's `.claude/`, `AGENTS.md`, `llm-wiki/general/`; `docs/trials/151-the-board-in-three-tools.md` |

**Not this spec:** Orkboard reading a page's `### Talk` and `### Accepted` into Talk's record and the plan (a spec of its own,
§258.6); a phone's face for any of it; skills for tools other than Claude Code beyond the Agent Skills fields.

## 0. What is there today

- Spec 151 C wrote `.claude/agents/ork-<id>.md` (`orkmaster`, `<craft>-leader`, `taskmaster`, `grunt`) and
  `.claude/skills/orkboard/SKILL.md`, from `agent_rules_text.subagent_body` and `skill_body`; a subagent's body is its role file's
  text: the prompt's fixed text **for a call** (`goal_route.instruction`, `idea_talk.instruction`, `idea_sections.instruction`,
  `idea_accept.instruction`, `roles.instruction`), placeholders where a call pastes its context, and an answer as one JSON object.
- The subagents name no `tools` (every tool) and no `model`.
- A leader's say in Talk is `talk.jsonl` and Talk's record (`idea_questions.record`), working state; its acceptance is the plan's
  (§256). The page holds a party's section (`## <Party>`, its parts `### Why`, `### Done when`, … : `realm/spec_sections.py`).
- Claude Code (its docs, 6 November): a skill's `context: fork` and `agent: <subagent>` run it as that subagent with none of the
  conversation, giving back what it found (in the background unless `background: false`); `argument-hint`, `$ARGUMENTS`;
  `disable-model-invocation`, `user-invocable`; a subagent's `tools`, `disallowedTools`, `model` (`sonnet`, `opus`, `haiku`,
  `inherit`), `isolation: worktree`, `skills`; a subagent starts subagents three layers deep at most.

## A. The agent's frame of each seat (§258.7)

1. Each seat's `instruction` (A.0's five) is split into **its rules** (what it judges and how: for a leader's Talk the lines under
   *Rules:*; for a section the section's parts and their limits; for *accept* the lines met / not met / cannot see; for the
   route the route's rules; for the plan the stages' rules) and **the call's frame** (the context pasted, the JSON object
   back). `instruction(...)` keeps building the call's prompt from both: **every prompt unchanged by a character**
   (`tests/test_agent_rules_prompts.py`, as it stands, green; a prompt changed on purpose by another spec is that spec's).
2. `realm/seat_frames.py` `agent(seat, step, craft, wiki, decisions)` → the agent's frame around the same rules: **what to read**
   (the goal's page `{wiki}/pages/ideas/<slug>.md`, `{wiki}/project.md`, its party's journal `{wiki}/journals/<party>.md`, the
   decisions' place, for *accept* the gate's record and the files the step changed: `git diff` of its branch), **what to write**
   (B's part of the page, in B's format; the route as the page's `route`; the plan as the page's *Stages*), **what to give back**
   (one line to the conductor: the verdict and its why, or *accepted* / *not accepted: <lines>*). It never says *read no file*
   nor asks for JSON. Steps: `orkmaster` *route*; `<craft>-leader` *talk*, *section*, *accept*; `taskmaster` *plan*; `grunt`
   *task* (its brief's frame: the task, its spec's path, the gate; *a member asks only its leader*: what it cannot settle goes
   back in its line, never to the person).
3. Tests (`tests/test_seat_frames.py`): each seat's agent frame holds its rules' text exactly (the same function's output as
   the call's), names the paths of A.2, holds none of *Read no file*, *JSON*, *(The context follows*; the prompts' test green.

## B. Talk and Accepted in the page (§258.6)

1. `realm/page_talk.py`: a party's say read and written in the goal's page, under its section `## <Party title>`:

   ```markdown
   ### Talk
   - verdict: doubt — the cache adds a second caller to the store
   - stance: Tech can build it in a step if the store keeps one writer
   - for: one screen, no new service
   - against: a second writer to the store
   - instead: show the cached board only
   - assumes: players reload less than once a minute — shown by: the reload events of a week
   ```

   `verdict` one of `go`, `doubt`, `no` (a `doubt` or `no` with no why reads as `go`, as a call's answer does), each line at most
   the call's own limits (200 characters); `instead` and `assumes` only when said. Its questions stay the page's *Open questions*
   (`idea_questions.line`, `asks: person`). And:

   ```markdown
   ### Accepted
   - met: the board shows the best three players
   - not met: a tie is ordered by the earlier score — the order is by name
   - cannot see: the board loads in under a second
   ```

   one line a line of the section's *Done when*, `met`, `not met` (and why after a dash) or `cannot see` (§257.5).
   `read_talk(page, party)`, `write_talk(page, party, say)`, `read_accepted(page, party)`, `write_accepted(page, party, lines)`;
   the section made when the page has none (in `spec_sections`' format); every other part kept byte for byte.
2. `spec_sections` reads `Talk` and `Accepted` as parts it knows (they are not the spec's sections: never folded, never in
   *Done when*'s count).
3. **The page's schema** moves (`goal_phase.SCHEMA`); Orkboard reads every older page as before.
4. BOARD.md (`agent_rules_text.board_md`) says both parts, their lines and where they go, and that the conductor writes nothing
   of a leader's: each leader writes its own.
5. `orkboard check`: a `### Talk` or `### Accepted` it cannot read is a finding in words (the line); a `verdict` it does not know;
   an `Accepted` line that names no line of the section's *Done when*.
6. Tests (`tests/test_page_talk.py`; `tests/test_board_check.py`; `tests/test_agent_rules.py`): written and read back the same;
   a page with other parties' sections and a free part kept byte for byte; the section made; a bad verdict, a free line, a
   line that names no *Done when* found by check; the old schema's pages read.

## C. The seats in Claude Code, and the conductor (§258.2–5)

1. **A subagent a seat**, `.claude/agents/ork-<id>.md` (as today, its front matter gaining):
   - `tools`: the Orkmaster, a leader and the Taskmaster `Read, Grep, Glob, Edit, Write` (the page and the project read, the page
     written: no `Bash`, no web); a Grunt every tool, and `isolation: worktree`.
   - `model`: the seat's tier in the party (`goal_team`, `party_recipes.tiers_for`; the Orkmaster and the Taskmaster their roles'
     tier) through Orkboard's own tier table for Claude Code (find it: `realm/harness_claude.py`, `harnesses.model_on`), as one of
     `opus`, `sonnet`, `haiku`; `inherit` where it names none.
   - its body: who it is (its role's text, A's rules) and *Read `<wiki>/BOARD.md` first*.
2. **A skill a seat's steps**, `.claude/skills/<id>/SKILL.md`: `name: <id>`, a narrow `description` (*Tech's leader on one goal
   of this project's Board: its say in Talk, its section, or its acceptance of its step. Called by the orkboard skill, or as
   /tech-leader talk|section|accept <goal>.*), `argument-hint: "<step> <goal>"`, `context: fork`, `agent: ork-<id>`,
   `background: false` only where the conductor must wait one at a time (the Talk's leaders run side by side: the conductor
   waits for them all); its body: each step's agent frame (A.2), chosen by `$ARGUMENTS`'s first word. The Grunt has none.
3. **The conductor**, `.claude/skills/orkboard/SKILL.md` (spec 151 C's, rewritten): the way of a goal by the skills:
   take it; `/orkmaster route <goal>`; each route leader's `talk` side by side, then wait; questions for the person: say them,
   end the turn; each leader's `section`; `/taskmaster plan <goal>`; a Grunt (the `ork-grunt` subagent) a task, in order, each
   followed, at its step's end, by its leader's `accept`; what is not accepted, one more task, twice at most (§256); the gate;
   the pull request. It never writes a leader's part itself.
4. Written by `agent_rules.write` with the rest (their stamps, `check`'s `missing` / `outdated` / `changed`), only for the seats
   the project's parties have (`crafts_of`), and again when the package's texts change; the rules' schema moves.
5. Only the six fields of the Agent Skills standard where a field is not Claude Code's own (`name`, `description`, …): the rest
   are Claude Code's and say so in a comment of the file's first lines.
6. Tests (`tests/test_agent_rules.py`, `tests/test_board_check.py`, `tests/test_board_cli_goals.py`): each seat's subagent with
   its tools and model, the Grunt's worktree; each skill's front matter (`context: fork`, `agent`, `argument-hint`) and its
   steps' frames; the conductor's steps in order and its never writing a leader's part; a project with two parties gets two
   leaders' files, not six; `check` finds a changed one; `orkboard init` writes them.

## D. This repository, and the trial's arm

1. `uvx --from git+https://github.com/orkCraft/orkBoard orkboard init` here once C is merged: the files written again, committed
   as the Board's files are; `orkboard check` clean.
2. `docs/trials/151-the-board-in-three-tools.md` (written now if it is not yet): Talk measured three ways on one goal of this
   repository: Orkboard's, the forked skills in Claude Code, one voice (the rules alone in another tool), judged as
   `docs/trials/h1-head-to-head.md` judges.

## Done when

- In Claude Code, `/tech-leader talk <goal>` runs in a context of its own and writes its say under `## Tech` / `### Talk` in the
  goal's page, and the conductor's Talk runs the route's leaders side by side and stops at the person's questions.
- A leader's subagent cannot run a command; a Grunt works in a worktree of its own.
- Every prompt Orkboard sends is unchanged by A; each seat's agent frame holds the same rules.
- `orkboard check` reads the new parts and the new files; this repository passes it.
- The critical tests pass: `tests/test_architecture.py` (`realm/seat_frames.py`, `realm/page_talk.py` import no `gui/`),
  `tests/test_board_alone.py`, `tests/test_updates.py`, and each part's own.
