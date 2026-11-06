---
name: orkboard
description: "Work a goal of this project's Board: take it, route it, hold Talk, write its spec, do it, run the gate, and stop at what the person decides"
# `name` and `description` are the Agent Skills standard's; this skill runs in the conversation and uses no field of Claude Code's own.
schema: 3
hash: 2871ea542453
---
# Work a goal of this project's Board

You conduct. Each seat of the Board is a skill that runs in a context of its own and gives you back one line; you call them in order and write nothing of theirs. Read `llm-wiki/general/BOARD.md` first: the page's format, the phases, a question's line and the gate's record. This project's own rules in `AGENTS.md` and `CLAUDE.md` win.

1. **Take the goal.** Pick a goal whose `phase` is not `done` and that is not on Hold (`queue: hold`); take it (`uvx --from git+https://github.com/orkCraft/orkBoard orkboard goal take <slug>`, or BOARD.md's way). Another's goal is not yours.
2. **Route it:** call `/orkmaster route <slug>`. It writes `route` in the page and moves `phase` to `talk`; read `route` back.
3. **Talk:** call `/<craft>-leader talk <slug>` for every leader of the route **in one turn, side by side**, then wait until all of them are back. Each writes its own `### Talk` in its section and gives you its verdict.
4. **The person's questions:** a question only the person can settle is under `## Open questions` with `asks: person`. Say each in the chat and **end your turn**; go on when it is answered (`uvx --from git+https://github.com/orkCraft/orkBoard orkboard goal answer`). Never answer for the person.
5. **Sections:** call `/<craft>-leader section <slug>` for each leader of the route, in the route's order. Then move `phase` to `spec` (`uvx --from git+https://github.com/orkCraft/orkBoard orkboard goal phase <slug> spec`).
6. **Plan:** call `/taskmaster plan <slug>`; it writes `## Stages`. Move `phase` to `work`.
7. **Do the tasks:** work in a branch of your own. Give each task of the stages, in order, to a Grunt (the `ork-grunt` subagent: the task, the goal's page and the gate), one at a time. A Grunt works in a worktree of its own and never asks the person.
8. **Accept:** at the end of a party's stages, before the next party's, call `/<craft>-leader accept <slug>` for that party. What it does not accept is one more task for each thing, then accept again; twice at most. What is still not accepted goes in the pull request under “Not accepted”.
9. **Run the gate** (`[gate]` in `orkcraft.toml`), write its record in `gate`, open a pull request, set `phase: done` only with the gate green.
10. **Stop at what the person decides**: a choice between ways, a cost above what was agreed, a decision against an earlier one, dropping or holding a goal, going into main.

You never write a leader's part yourself: not its `### Talk`, its section, its `### Accepted`, and not the route or the stages. If a skill gave back nothing, call it again; do not write it for it.
