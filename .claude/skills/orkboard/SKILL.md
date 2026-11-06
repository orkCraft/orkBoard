---
name: orkboard
description: "Work a goal of this project's Board: take it, route it, hold Talk, write its spec, do it, run the gate, and stop at what the person decides"
schema: 2
hash: 7016be9394bb
---
# Work a goal of this project's Board

Read `llm-wiki/general/BOARD.md` first: the page's format, the phases, a question's line and the gate's record. This project's own rules in `AGENTS.md` and `CLAUDE.md` win.

1. **Take the goal.** Pick a goal whose `phase` is not `done` and that is not on Hold (`queue: hold`); take it (`uvx --from git+https://github.com/orkCraft/orkBoard orkboard goal take <slug>`, or BOARD.md's way). Another's goal is not yours.
2. **Route it** as the Orkmaster does: read `llm-wiki/general/roles/orkmaster.md`, write `route` in the page and move `phase` to `talk`.
3. **Hold Talk.** For each leader of the route, in a pass of its own, read only `llm-wiki/general/roles/<craft>-leader.md` and the page, and write what that leader says. A question only the person can settle goes under
   `## Open questions` with `asks: person`; say it in the chat and end your turn.
4. **Write the spec.** Each leader writes its section (*Why*, *Done when*, *Stages*); move `phase` to `spec`.
5. **Do the work** in a branch of your own, the stages in order (`llm-wiki/general/roles/taskmaster.md`, `llm-wiki/general/roles/grunt.md`); `phase: work`.
6. **Run the gate** (`[gate]` in `orkcraft.toml`), write its record in `gate`, open a pull request, set `phase: done` only with the gate green.
7. **Stop at what the person decides**: a choice between ways, a cost above what was agreed, a decision against an earlier one, dropping or holding a goal, going into main. Never answer for the person.
