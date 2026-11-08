---
owner: board
kind: idea
track: product
order: 14
size:
priority: normal
short: A leader's view
phase: talk
route: product, design, tech
by: claude-code
schema: 3
---
# Each leader's view of the product, on its tab

## Gist
I want to open Orkboard and read, from Product, Tech and Design each, where the product stands now: what works, what hurts, what comes next, in a few lines, on that leader's tab. Today no such view is written anywhere: there is no llm-wiki/general/project.md (the project's brief), no journals (llm-wiki/general/journals/), no leader's table (pages/tables/); a leader speaks only per goal (its Talk and section on the goal's page) and, on a map's open, as concerns on its map's parts (core/idea_concerns.py, the cheaper tier, kept in .orkcraft/ on one machine). Product's view needs Product's tree on the Board (goal 163). The view is written into the Board's files so every machine and AI tool reads the same one, kept fresh after a goal lands or when the map changed, at a cost the person agrees to, and it reads the decisions (§281.7).

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

## Open questions
- What is a leader's view? (**Its journal's digest, shown** / A view file of its own / Its concerns, in words) — spec 125 D's digest is already what a lens knows of the product, mirrored to journals/ by spec 151 B.1 · Its journal's digest, shown: No new file: the digest says works, hurts, next and tops the tab · A view file of its own: A new file a party, a second summary to keep beside the digest · Its concerns, in words: The map's look said in lines; kept in .orkcraft/, no clone reads it
  - Answered: The product as the leader's framework sees it (its hero's places), with its journal's digest and its concerns, in the window; the face agreed on mockups (the person, 2026-11-08)
- When is a view written again? (**After a goal lands** / After a landing or a map change / Only when you press) — one cheaper call a party on the landed goal's route is a cost you can see; the maps change with every commit · After a goal lands: A call for each party on its route, when its gate is green · After a landing or a map change: Fresher, but a commit moving a map's heat starts calls on each tab · Only when you press: No spend unasked; a view goes stale until you ask for it
  - Answered: When a goal closes, when the person asks, and when Orkboard analyses the project by itself (the person, 2026-11-08)
- What feeds a view made in a skill? (**The passes write journal lines** / The call reads pages and log / Only Orkboard's own calls) — here every Talk and Accept ran as a skill and wrote no journal line, so a digest has nothing to read · The passes write journal lines: Talk's verdict, Accept's learned land in journals/<party>.md, read in · The call reads pages and log: Each call reads done goals and decisions; dearer, nothing kept between · Only Orkboard's own calls: The views stay empty here until goals run in Orkboard's window
  - Answered: The call reads pages and log (the person, 2026-11-08)
- Where does a leader's view lie? (**At the top of the leader's bubble** / A plate atop the pane, over the map / Over the pane from the party's …) — the bubble (ask.js) already opens itself once a day with the evening line; the strip over the map was taken off (spec 123 §4) · At the top of the leader's bubble: Pressing the open head reads it; the map and the lanes keep their place · A plate atop the pane, over the map: Read without a press; the map and the first lane slide down a block · Over the pane from the party's …: One more press through a menu; the map hidden while it is read
  - Answered: Two or three mockups first, the person picks among them; the use cases talked of here lie on Product's table (goal 163) (the person, 2026-11-08)
- Where is the view under 760 px and on the phone? (**The party's … opens it; the phone its own goal** / The party's … and the phone, in this goal) — no bubble opens under 760 px or on touch, so a narrow window needs a way in (WCAG 1.4.10); §281.5 gave reach's phone its own goal · The party's … opens it; the phone its own goal: Narrow windows read it over the pane; the phone waits for its goal · The party's … and the phone, in this goal: One goal wider: the phone's party page shows it under its header
  - Answered: No phone for now: a goal of its own (the person, 2026-11-08)
- Who writes the view in skills? (**The leader's Accept pass, in the tree** / Orkboard's call, on the window's next goal / A command the conductor runs) — here every pass is a skill, and Orkboard's digest call runs only when a goal is added in its window · The leader's Accept pass, in the tree: No new call: the pass rewrites digest: from its journal, read back on open · Orkboard's call, on the window's next goal: One writer; a skill-only project's view waits for the window · A command the conductor runs: orkboard journal digest: a new CLI command and a call outside the pass
  - Answered: The leader's Accept pass, in the tree (the person, 2026-11-08)

## Decisions
- §282: the person's answers in Talk (8 November 2026)

## Product
### Talk
- verdict: doubt — half built: spec 125 D's digest is a lens's view, mirrored to journals/ (151 B.1), empty as no skill pass writes a journal line; go if this fills and shows it, no new file
- stance: Product wants each lens's state of the product read on its tab, as the journal's digest grown, not a new file; Product's own view waits on goal 163's tree
- for: Wide reach at small cost: every party, clone and AI tool reads one view in journals/; the person sees what hurts before laying the next goal
- against: Goal 163 is in Talk with six questions open; a call a party after each landing spends on a summary no one has shown the person reads before choosing
- instead: the leaders' skill passes write journal lines and the digest shows atop each tab; no new file, no new call
- assumes: the person reads a lens's view before laying a goal, not only the goals and the past — shown by: in the owner's week, a tab's view opened before a goal is laid on it

## Design
### Talk
- verdict: doubt — go if the view lies at the top of the leader's bubble (ask.js), as the evening line does; a block atop the tab brings back the strip spec 123 §4 took off the map
- stance: Design reads the view where the leader already speaks, its bubble: three short lines (works, hurts, next), dated by what it last read; no new block over the map or the lanes
- for: The bubble is built and opens itself once a day for an unseen evening line; a view there costs no new screen and no step, and the map keeps its place
- against: The digest is one prose line up to 900 characters (journals.DIGEST_CHARS), not a few lines; the bubble is desktop-only, so under 760 px the view has no way in (WCAG 1.4.10)
- instead: the view as three dated lines at the top of the open leader's bubble; the party's … opens it over the pane when the window is narrow
- assumes: the person reads the view in the bubble, not closing it unread — shown by: in the owner's week, a bubble with a view stays open longer than a glance before ×

## Tech
### Talk
- verdict: doubt — go if journals/<party>.md in the tree is the digest's truth, read back: read_in.take_outside takes entries only, so two machines' digest: lines overwrite each other
- stance: Small as Product's digest: ideas.journal already returns it, no new command; the work is the read-back, a landing trigger in core and decision lines in the digest's call
- for: No new part or store: journals.py, idea_journal.py and the tree's mirror (spec 151 B.1) are built; a landing trigger fits core/idea_journal.py (164 lines)
- against: gui/ideas.py (769 lines) and realm/ideas.py (689) are past the 600-line split; the digest call reads only its own journal, so feeding it decisions grows a cheaper call
- instead: the digest read back from the tree and shown atop the bubble, its call fed the project journal's decision lines; no new file, no new trigger
- assumes: stance, accepted and learned lines say what works and hurts in the product, not only how goals went — shown by: a digest of goals 163–167's lines names a hurt System's heat shows
