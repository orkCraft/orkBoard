# H1's head-to-head: Orkboard against plan mode alone

Hypothesis H1 (`docs/hypotheses.md`): *goals made in Orkboard are accepted the first time clearly more often than plans made
in an AI tool's plan mode alone, at a cost in the person's minutes worth paying.* This page is how it is tested; the tally is
`orkboard trial` (`orkboard/realm/trial.py`, spec 124 C).

## What is compared

- **Orkboard**: the goal written on the + card, its way as it is (Talk, the hearing if any, the sections, the plan, the work,
  the gate, Review).
- **Plan mode**: the same words given to the same AI tool (Claude Code's plan mode, or Codex's), the same model, the plan
  read and approved by the person, then the work.

Same project, same commit to start from, same model and tier. Each task is done both ways, in two worktrees.

## The tasks

10 to 15 **real** tasks the maker wanted anyway, on two or three real projects: a web app, a mobile app, a game. A mix:
a feature with a screen, a change to the rules or the loop, a fix with a cause to find, a goal that touches two crafts
(a screen and its copy, a mechanic and its art). Not toy tasks, not tasks picked because one way will win.

Write them one a line in `tasks.txt`, then:

```
orkboard trial new h1.csv --tasks tasks.txt
```

`h1.csv` has two rows a task, `orkboard` and `plan`, each shown as **A** or **B** at random (`shown_as`).

## Doing a task

1. Start both ways from the same commit, the same words.
2. While it runs, count **changes** (a plan change or a fork taken after the start, a section rewritten by hand, the plan
   corrected in plan mode) and **questions** (asked of the person during the work), and time **minutes** (the person's own:
   reading, answering, deciding; not the tools' running time).
3. Note **tokens** where the tool says them (empty when not).

## Judging blind

Someone who did not run them (or the maker, a day later, from a list that says only A and B) looks at each task's two
results by their letters: the diff, the screens, Play. For each: **accepted the first time**, `yes` or `no`: would it be
merged as it is, with no send back? Then fill `accepted` on the rows by their `shown_as`.

## The tally

```
orkboard trial h1.csv
```

**Holds** when Orkboard is accepted the first time **20 points or more** more often, at **no more than twice** the person's
minutes, over **10 tasks or more** done both ways. Anything else does not hold, and the tally says which part failed.

Beside it, read the project's own measures over the same days (`orkboard measures <project> --since <day>`): how often a
leader's no was heeded, and whether the goals that went on against a no came back more often than the others.

## If it holds, if it does not

- **Holds**: a decision (the next §), H1 `held`, the README's line stays and the brief, the stage-weighted rubrics and the
  shorter way come before new faces.
- **Does not hold**: H1 `refuted` with what was learned (which tasks lost, why: ceremony, a no that was noise, a brief that
  said nothing), and the way of a goal is cut down to what won.
