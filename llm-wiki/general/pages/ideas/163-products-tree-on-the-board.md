---
owner: board
kind: idea
track: product
order: 12
size:
priority: normal
short: Product's tree
phase: new
by: claude-code
schema: 3
---
# Product's tree on the Board

## Gist
I want to keep the product's direction and the closed use cases on Product's table: the outcome the project means to move, the users' jobs under it, which goals served each job (the done ones are the closed use cases) and which hypotheses test them, so I read where the product is going and what is already done in one place.

Goal 162 put the past on the parties' tables and left Product's tree for this goal (decision §277.6). Today:
1. Product's tree (realm/opportunity_tree.py, decisions §172, spec 102 §8) is kept in <state_dir>/tree.json, inside .orkcraft/: it lives on one machine, it is not in the repository, and a clone, another computer or an AI tool's skill never sees it. Product's leader could not read it in goal 162's Talk.
2. There is no llm-wiki/general/project.md, the project's brief: the Orkmaster routes and the leaders talk without it.
3. None of the 121 done goals is attached to a job, so the tree, even where it is kept, says nothing of what was done.

What I expect:
- The tree is a file of the Board, in the repository beside the pages, as the goals and decisions are, so every machine and every AI tool reads the same one; what stays in .orkcraft/ is the machine's own.
- The first outcomes and jobs are proposed from what is written (the specs, the decisions, docs/hypotheses.md, the trials), and I take or change them.
- The done goals are attached to the jobs they served, so Product's table shows each job with its closed use cases and its open goals.
- Product and Design say in Talk where on Product's table the tree is drawn, and Tech how the file is kept so Orkboard and Orkline read the same one.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

## Open questions

## Decisions
