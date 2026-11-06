# The Board in three tools: a goal of this repository worked without the app, and Talk three ways

Decisions §255.15 and §258.8; specs 151 G and 154 D. Written before the runs. This repository is laid out on its own Board
(spec 151 H): its goals are `llm-wiki/general/pages/ideas/`, its rules are Orkboard's block in `AGENTS.md`, and Claude Code
finds the seats' subagents and skills in `.claude/`.

## What is asked

1. **Does a tool that has never seen Orkboard work a goal by the rules?** It reads `AGENTS.md`, takes the goal, routes it,
   holds Talk, writes the spec, does the stages in a branch, has its leader accept them, runs the gate and opens a pull
   request. It **stops at the person's decision** and never answers for the person.
2. **Does Orkboard read what it did?** Opened on the result, it shows the goal in its phase, the question in the hand, the
   gate's record and the journals' lines taken in.
3. **Is Talk better in voices of their own?** The same goal's Talk three ways, judged blind.

## The arms

| Arm | Tool | What it has |
|---|---|---|
| **Orkboard** | the app, its own Talk | the leaders' calls, as today |
| **Forked skills** | Claude Code | the `orkboard` skill conducting; `/<craft>-leader talk`, each leader in a context of its own (§258) |
| **One voice** | Codex, then Cursor | `AGENTS.md` alone: one conversation plays every leader |

Each tool runs twice in a fresh clone of this repository at the same commit: first with nothing installed (the rules alone),
then with Orkboard run from git (`uvx --from git+https://github.com/orkCraft/orkBoard orkboard`). The first run is a cloud
session, as the one §255 was decided in; Codex and Cursor run on the owner's computer.

## The goals

Picked by the owner from this repository's goals not yet done (`orkboard goal list --phase spec`, `--phase work`), **each with
a decision only the person can make**: a choice between two ways that the spec cannot settle. One goal for the whole trial, or
one a tool; the same goal for the three Talk arms.

| Goal | Why it was picked | The person's decision in it |
|---|---|---|
| *(the owner writes them here before the first run)* | | |

## What is recorded, a run

- Read the rules (it says so, or acts by them); took the goal (`orkboard/taken`, or said so in the pull request).
- Routed it (`route` in the page); Talk: each leader of the route said its say in `### Talk` under its party's section.
- **Stopped at the person's decision**: the question under *Open questions* with `asks: person`, said in the chat, the turn
  ended. *Answered it itself* is the trial's first finding, whatever else went well.
- The sections, with their *Done when*; the stages in a branch; the leader's `### Accepted` after each party's stages.
- The gate run and its record in `gate`; the pull request; `orkboard check` on it.
- **A leader's fork runs no command**: a `/tech-leader talk` in a fresh session refuses a Bash call, in a cloud session and on the
  desktop (the person's answer in goal 154's Talk; the session that built spec 154 had loaded the subagents before their `tools`).
- The time, and what it spent (its tool's own count; Orkboard's `drive spend` for the app).

## Then Orkboard opens it

On the pull request's branch: every goal in its phase; the question in the hand, answered there and written back under its
line; the gate's record on the goal; the journals' lines a tool added, taken in once. What Orkboard does not show is a finding.

## Talk judged

The three arms' Talk of the same goal, their words alone (no arm named), read by the owner as
`docs/trials/h1-head-to-head.md` reads a plan: which says no where it should, which asks the question that matters, which
agrees with itself. Then the tally: the arm whose Talk the owner would act on.

## Findings

*(written after the runs: each a line, with the tool, the step and what it did; each sent on as the owner says, as spec 143's
and 149's were)*
