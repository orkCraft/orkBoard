---
owner: board
kind: idea
track: product
order: 12
size:
priority: normal
short: Product's tree
phase: talk
route: product, design, tech
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
- Which hypotheses go with the tree? (**hypotheses.json beside the tree** / docs/hypotheses.md as theirs / Stay on the machine) — the tree's text sets each hypothesis under its job; a tree moved alone shows no test · hypotheses.json beside the tree: One Board file set: jobs, goals and their tests, read on every machine · docs/hypotheses.md as theirs: H1 and its kin under jobs; two hypothesis stores kept in step · Stay on the machine: Tree in the repo without its tests; a clone sees no hypothesis
  - Answered: hypotheses.json beside the tree (the person, 2026-11-08)
- How are the 121 done goals attached? (**Leader proposes, you take each job** / Only goals done in the window / By hand) — one cheaper call reads the titles and routes; you keep the say, as with the tree's first proposal (§172.2) · Leader proposes, you take each job: One call drafts it all; you keep, move or drop per job · Only goals done in the window: The 119 history goals stay unattached; closed cases count from now · By hand: No model cost; 121 picks before the tree says what is done
  - Answered: Leader proposes, you take each job (the person, 2026-11-08)
- How are a job's done goals drawn? (**Newest seven, then All · search** / Every done goal, whole cards / Open goals only; done in the past) — about twenty done cards a job bury its open goals and the empty jobs; §277.5 already deals the past seven · Newest seven, then All · search: Open goals on top; a job's done deck deals seven, the rest over the pane · Every done goal, whole cards: One long column a job; its open goals sink under twenty done ones · Open goals only; done in the past: The tree shows no closed cases; the Gist's one place is not kept
  - Answered: Newest seven, then All · search (the person, 2026-11-08)
- Where do you take proposed attachments? (**On the tree, dashed until kept** / A hand card a job / One hand card opening the tree) — proposed hypotheses are already kept on the tree (Keep, Drop): the same act, where the goal will lie · On the tree, dashed until kept: Each job's proposed goals dashed; Keep all, or Move or Drop one · A hand card a job: Five to seven cards, each a job and its goals listed; the tree waits · One hand card opening the tree: One card says the tree is proposed; its press opens Product's tab
  - Answered: On the tree, dashed until kept (the person, 2026-11-08)
- Where does a goal's job lie? (**job: in the goal's page** / serves in the tree file) — no two goal branches edit one file; a goal carries its job as it carries route: (§277.3) · job: in the goal's page: 121 pages gain a line; a goal's branch edits only its own page · serves in the tree file: The whole tree in one file; two goal branches conflict in it
  - Answered: job: in the goal's page (the person, 2026-11-08)
- Which form does the tree's file take? (**Markdown, llm-wiki/general/tree.md** / tree.json as kept now) — the Board's files are Markdown read in a commit, as docs/hypotheses.md is · Markdown, llm-wiki/general/tree.md: Read and edited as a page; a parser and writer to build and test · tree.json as kept now: Moved as it is, no parser; the pull request shows a JSON diff
  - Answered: Markdown, llm-wiki/general/tree.md (the person, 2026-11-08)

## Decisions
- §283: the person's answers (8 November 2026)

## Product
### Talk
- verdict: go
- stance: Product's own: the tree is built (realm/opportunity_tree.py, js/table/treemap.js) but kept in .orkcraft/, so no clone or skill reads it, and goal 167 waits on it
- for: Wide reach for little cost: the tree and its drawing stay, the file moves; then every leader's call and AI tool reads one outcome, its jobs and what served them
- against: Jobs read from our own specs are the backlog's themes, not users' heard jobs; 121 done goals filed at once may sit under jobs by guess
- instead: the tree into the Board with its first proposal now; attaching the 121 done goals a goal of its own
- assumes: the jobs read from the specs, decisions and H1 are the users' jobs, not the owner's themes — shown by: the person keeps most proposed jobs, and every goal in line finds one

## Design
### Talk
- verdict: doubt — go once a job's done goals fold to seven, then All · search (§277.5): treemap.js Column lists every goal serving a job, so 121 attached ones bury the open goals
- stance: The tree stays Product's map in its pane, where it is built (treemap.js, spec 102 §8.4); only a job's done goals need a fold, as the past's decks have
- for: The face is built: jobs, goal cards with their place (Done), picking; a job's closed cases read beside its open goals, with no new screen or step
- against: Columns of about twenty whole cards a job: open goals and empty jobs sink below the fold, and the same done goals also lie in the past's decks
- assumes: the person reads closed use cases by job, not by version as the past deals them — shown by: in Play the person opens a job's done goals, not the past's decks, to see what was done

## Tech
### Talk
- verdict: go
- stance: Small for Tech: opportunity_tree.read/keep keep their signature for their 8 callers; only the file moves into the Board's tree, written through BoardTree as hypotheses_bind already is
- for: No new part or caller: BoardTree.edit_file already commits a Board file with the pages (hypotheses_bind); read() already trusts no file, so a hand edit by an AI tool is safe
- against: One file every goal's branch edits (serves) conflicts on merge; BoardTree.pages, the kept-off ref and orkboard check must learn it; Orkline's frozen copy keeps reading .orkcraft/tree.json
- assumes: the owner's .orkcraft/tree.json is the only tree kept, read in once — shown by: one tree.json under .orkcraft on the owner's computer, none on another
