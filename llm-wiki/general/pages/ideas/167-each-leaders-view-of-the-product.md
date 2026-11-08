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
### Why
- Product answers what is worth doing next; today no page says where the product stands, so a goal is laid from its gist alone, against nothing that hurts.
- A view a lens, read from the goal pages and the decisions (§282.3), is the studio that sees its product H1 promises, said in Product's words: what works, what hurts, what next.
- It rests on a belief no one has shown (the person reads a view before laying a goal), so Product writes it as a hypothesis with its signal, not as a reason to build more.
### Done when
- [test] When Product's view is written for this repository, then it says what works, what hurts and what comes next, each line naming the goal slug, decision § or tree part it read
- [test] When Product's view is written while the Board holds no tree (goal 163 not landed), then it says the tree is not on the Board and names no job it did not read
- [test] When the product leader's Accept pass runs as a skill, then its role file tells it to write Product's view into journals/product.md in the tree, from the pages and decisions (§282.6)
- [test] When the person opens a leader's view, then an event names the party and the view's date, never its words, so H6's signal can be counted
- [person] When the person reads Product's view of this repository, then they find in it where the product stands, not a list of the goals done
### Checks
- Every line of Product's view traces to a goal page, a decision or a tree part it read; no number it did not read, no invented job.
- No count of what waits, no streak, no score in a view (§50.5, §280.4).
- The view says party and goal, orks by their orkish names, everything else by what it does (CLAUDE.md, lexicon `TERMS`).
- H6 in docs/hypotheses.md says what proves it, what refutes it and how it is tested, its signal the event above.
- A view is kept in the tree's journals/<party>.md, never only in .orkcraft/, so a clone and an AI tool read the same one.
### Will be
- new hyp:h6 — the belief the view rests on (the person reads a leader's view before laying a goal on its tab), with its signal, in docs/hypotheses.md
### Out
- The tree, its outcome, jobs and the use cases talked of here: goal 163 lays them on Product's table (§282.4).
- The view on the phone: a goal of its own (§282.5).
- The view's face and place in the window: Design's mockups, the person picks (§282.4).
### Risks
- medium
- Until goal 163 lands, Product's view reads pages and decisions only: its lens's places (the tree's jobs) are empty, and the view is thin.
- H6 is untested: a call a party on each closing goal may buy summaries the person never opens.
- The calls grow with the route's length and with Orkboard's own analysis; spend the person did not see coming.
- A view written by a skill's Accept pass and one by the window's call may disagree until one is the truth in the tree.
### Defaults
- Product's hero is the default (Angel Invest Knight): its view's places are the tree's outcome and jobs, so it keeps no table of its own.
- Works, hurts and next are the three heads of every leader's view, within the digest's 900 characters (journals.DIGEST_CHARS).
- The hypothesis is H6, the next free number in docs/hypotheses.md (H1–H5 are taken).
- Orkboard's analysis by itself (§282.2) runs when a map's look runs (core/idea_concerns.py, on open); no new timer.

## Design
### Talk
- verdict: doubt — go if the view lies at the top of the leader's bubble (ask.js), as the evening line does; a block atop the tab brings back the strip spec 123 §4 took off the map
- stance: Design reads the view where the leader already speaks, its bubble: three short lines (works, hurts, next), dated by what it last read; no new block over the map or the lanes
- for: The bubble is built and opens itself once a day for an unseen evening line; a view there costs no new screen and no step, and the map keeps its place
- against: The digest is one prose line up to 900 characters (journals.DIGEST_CHARS), not a few lines; the bubble is desktop-only, so under 760 px the view has no way in (WCAG 1.4.10)
- instead: the view as three dated lines at the top of the open leader's bubble; the party's … opens it over the pane when the window is narrow
- assumes: the person reads the view in the bubble, not closing it unread — shown by: in the owner's week, a bubble with a view stays open longer than a glance before ×
### Why
- A view the person cannot find, or cannot read at a glance, is a call spent for nothing: Design answers where it lies on the tab, how it reads and how it is reached by key.
- Two or three faces seen before one is built (§282.4) keep the frame (§104.0, §145) from moving on a guess: the map and the first lane keep their place unless the person picks otherwise.
- Under 760 px no bubble opens (ask.js), so the face picked must still be reached in a narrow window (WCAG 1.4.10), the phone apart (§282.5).
### Done when
- [look] When docs/mockups/leader-view/ opens, then it shows two or three faces of a leader's view on a tab with no goal picked, each at 1280 × 800 and at 600 px wide, with a view written and with none
- [person] When the person has looked at the mockups, then they pick one face, written in this goal's Decisions before the face's stage starts
- [test] When the page opens at 1280 × 800 on a leader's tab whose view is written, no goal picked, then the view is one press away by key or pointer and says works, hurts, next, its date and what it read
- [test] When the window opens 600 px wide on that tab, then the party's … reaches the view, and it reads whole with nothing scrolling sideways (WCAG 1.4.10)
- [test] When a leader's tab opens with no view written yet, then its place says in a line that the leader has not looked yet, beside a button that says it makes one call to look now
### Checks
- The mockups and the face read orkUI's tokens and classes only: no colour, font or corner of their own (tests/test_design_system.py for the sheets).
- The view's words in the body face, never the pixel face (CLAUDE.md); its text 4.5:1 with the lamp lit and out; focus seen; Esc closes and the focus returns to what opened it.
- No count of what waits, no score, no streak in the view or its mockups (§50.5, §280.4).
- The view and the evening line never both open by themselves on one day: at most one opens unasked a party a day.
- The view says party and goal, orks by their orkish names; its strings in today's word (lexicon `TERMS`, tests/test_gui_wording.py).
### Will be
- changed home — each leader's tab shows its view in the face the person picks from the mockups, reached from the party's … under 760 px
### Out
- The view on the phone's app (§282.5, a goal of its own).
- What the view says and the call that writes it: Product's words, Tech's call (§282.3, §282.6).
- A new colour, a picture or a drawer for the view; a legend panel.
### Risks
- medium
- The digest runs to 900 characters of prose (journals.DIGEST_CHARS): three short lines may not hold it at 1280 × 800 without a scroll.
- The bubble opens by itself once a day for the evening line; a view in it competes with that line for the same place.
- The mockups are drawn before a view is written (Product's lines), so they may show words no call writes.
- A plate atop the pane, if picked, brings back the strip spec 123 §4 took off the map and pushes the first lane down.
### Defaults
- The mockups are one page, docs/mockups/leader-view/index.html, drawn on the three ways Talk named: the bubble's top, a plate atop the pane, over the pane from the party's ….
- A narrow desktop window (under 760 px) is in this goal; only the phone's app is out (§282.5).
- The view's heads (works, hurts, next) in orkUI's label face, its lines in the body face; its date and sources muted.
- Design's hero is the default (Pixel-Perfect Dryad): no table kept.

## Tech
### Talk
- verdict: doubt — go if journals/<party>.md in the tree is the digest's truth, read back: read_in.take_outside takes entries only, so two machines' digest: lines overwrite each other
- stance: Small as Product's digest: ideas.journal already returns it, no new command; the work is the read-back, a landing trigger in core and decision lines in the digest's call
- for: No new part or store: journals.py, idea_journal.py and the tree's mirror (spec 151 B.1) are built; a landing trigger fits core/idea_journal.py (164 lines)
- against: gui/ideas.py (769 lines) and realm/ideas.py (689) are past the 600-line split; the digest call reads only its own journal, so feeding it decisions grows a cheaper call
- instead: the digest read back from the tree and shown atop the bubble, its call fed the project journal's decision lines; no new file, no new trigger
- assumes: stance, accepted and learned lines say what works and hurts in the product, not only how goals went — shown by: a digest of goals 163–167's lines names a hurt System's heat shows
