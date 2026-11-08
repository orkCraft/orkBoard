---
owner: board
kind: idea
track: product
order: 14
size:
priority: normal
short: A leader's view
phase: work
route: product, design, tech
spec: docs/specs/167-each-leaders-view-of-the-product.md
by: claude-code
schema: 3
asks: person
---
# Each leader's view of the product, on its tab

## Gist
I want to open Orkboard and read, from Product, Tech and Design each, where the product stands now: what works, what hurts, what comes next, in a few lines, on that leader's tab. Today no such view is written anywhere: there is no llm-wiki/general/project.md (the project's brief), no journals (llm-wiki/general/journals/), no leader's table (pages/tables/); a leader speaks only per goal (its Talk and section on the goal's page) and, on a map's open, as concerns on its map's parts (core/idea_concerns.py, the cheaper tier, kept in .orkcraft/ on one machine). Product's view needs Product's tree on the Board (goal 163). The view is written into the Board's files so every machine and AI tool reads the same one, kept fresh after a goal lands or when the map changed, at a cost the person agrees to, and it reads the decisions (§281.7).

From another session's Talk on a goal the owner dropped as this one's double (passed on by the owner, 8 November):
1. Journal lines are stored addressed to the leader (*You said no to …*, realm/journals.py); the view shows them in the leader's voice, never as *you*.
2. `ideas.journal_strike` (spec 125) is built but the page never calls it: a wrong line is read into every later call. Tech and Product there recommended a *Not so* on each line the view shows.
3. The framework at work, laid by code with no model: realm/map_signals' hints laid by the rubric's aspects (realm/lens_rubrics.py), so a fresh tab shows something before *Look now*.
4. `orkboard import --dry-run` here places 27 of 233 decisions into leaders' journals by their titles' words (realm/read_in.py). §277.4 says a decision of no goal is never placed by its words: a view that reads the journal must not carry them.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages
- [ ] A. Three faces of a leader's view, drawn
  - party: Design. One page `docs/mockups/leader-view/index.html` (with its `leader-view.css`), drawn on the three ways Talk named (§282.4): the view at the top of the leader's bubble (as `gui/static/js/table/ask.js` draws the evening line), a plate atop the pane, and over the pane from the party's … (`js/table/menu.js`). Each face on a leader's tab with no goal picked, at 1280 × 800 and at 600 px wide, once with a view written and once with none (a line that the leader has not looked yet, beside a button that says it makes one call to look now). The view: three heads *Works*, *Hurts*, *Next* in orkUI's label face, short lines in the body face, each naming a goal slug or a § of this repository (so it shows words a call can write), its date and what it read muted. orkUI's tokens and classes only (`design-system/orkui`), no colour, font or corner of its own; no count, score or streak (§50.5, §280.4); no phone (§282.5). A camera `docs/mockups/leader-view/shoot.py` in `docs/mockups/answer-cards/shoot.py`'s way writes the twelve pictures to `MOCK_OUT`.
  - proves: Design's "When docs/mockups/leader-view/ opens, then it shows two or three faces…" (a [look] line: the person judges the pictures)
- [ ] B. The person picks a face (waits for the person)
  - party: Design, by the conductor; no Grunt and no code. Once A has landed, its pictures are shown to the person and one question is laid under *Open questions* as BOARD.md's line: *Which face for a leader's view?*, its ways A's faces, the one Design recommends in bold, a line each; `asks: person`, and the goal waits. The person's pick is written under the question and as a line in this goal's *Decisions* (§282.4). L, M and N never start before it. C to K need no pick: where the conductor may go on while the question waits, they may be built meanwhile.
  - proves: Design's "When the person has looked at the mockups, then they pick one face, written in this goal's Decisions…"
- [ ] C. H6, the belief the view rests on
  - party: Product. `docs/hypotheses.md`: a section *H6* in H5's shape (status open, raised 2026-11-08, goal 167): the belief (the person reads a leader's view before laying a goal on its tab), what would prove it and refute it, how it is tested (in the owner's week, a `view_opened` on a tab before an `idea_added` on the same party; its signal the event of I, which keeps no word of the view), and what follows if it holds.
  - proves: Product's *Will be* `new hyp:h6` and its check "H6 in docs/hypotheses.md says what proves it, what refutes it and how it is tested"
- [ ] D. The view keeps its date and what it read
  - party: Tech. `realm/journals.py`: `digest()` returns `{text, upto, at, read}` (`read`: the sources it read, goal slugs, `§N` and map part ids, at most 20, each at most 80 characters); `save_digest(state_dir, scope, text, upto, read=(), at="")` keeps them (`at` given only by a view read back from the tree, else now). `realm/write_out.py` `journal_file`: after `digest:`, the lines `digest_at: <at>` and `digest_read: <sources, comma separated>` when there is a digest. No new store (§282.1). Tests in tests/test_journals.py, tests/test_write_out.py.
  - proves: none alone: the ground of E and G (Tech's *Defaults*: `{text, upto, at, read}`, `digest_at:` and `digest_read:`)
- [ ] E. The tree's view read back, the newest kept
  - party: Tech. `realm/read_in.py` `parse_export` also returns the front matter's `digest`, `digest_at` and `digest_read`; `take_outside` hands each party's to a new `journals.take_view(state_dir, scope, text, at, read)` in `realm/journals.py`, which keeps it as the party's view only when its `at` is newer than the machine's (the machine's `upto` stays), and says whether it did. An older view in the tree is written over by the next `write_out.journals_into` (as now). A file with a view and no entry (a skill's Accept pass, K) is read too. `read_in.py` (502 lines) gains a few lines only: the work is in `journals.py`. Tests in tests/test_read_in_write_out.py: a newer tree view kept and nothing written over it; an older one replaced.
  - proves: Tech's "When the tree's `journals/<party>.md` holds a view newer than the machine's, then the next journals look keeps it…"
- [ ] F. The view's call reads the pages and the decisions
  - party: Tech. `core/idea_journal.py` `journal_prompt` becomes the view's (§282.1, §282.3): it is given the goals done since the last view's `at` (their *Gist* and the party's own `## <Party title>` section, from `ideas.ideas_and_pages`), newest first; the decisions those goals cite (the §N in their *Decisions*) and the log's last ten headings (`chronicle_decisions.read(self._log_text())`); the party's table `<wiki>/pages/tables/<party>.md` where it has one; the parts of its map its open concerns are on (`realm/concerns.py`: id and name, never the concern's words); its journal's entries as now. All cut to `idea_target.CONTEXT["journal"]`, newest kept. For Product, while the Board's files hold no tree (goal 163 not built), the prompt says Product's tree is not on the Board. The answer asked: `{"works": [lines], "hurts": [lines], "next": [lines]}`, at most three lines a head, each naming the slug, § or part it rests on. Still the cheaper tier, no tools, READS 0, the party's own step (`goal:<party>`). Tests in tests/test_idea_journal.py with a fake leader: the prompt holds a done goal's gist and a decision's heading.
  - proves: Tech's "When the view's call runs, then its prompt holds the done goals' pages and the decisions it read…" (its first half)
- [ ] G. Every line traced, or dropped
  - party: Tech. `core/idea_journal.py` `clean` becomes the view's: a line is kept only when it names a goal slug it was given, a `§N` whose number it was given, or a map part id it was given; the kept text is `Works: …; … Hurts: … Next: …` within `journals.DIGEST_CHARS`, kept by `save_digest` with `read` (the sources the kept lines name). For Product with no tree, the code (not the model) adds under *Hurts* a line that the tree is not on the Board yet, naming `163-products-tree-on-the-board`. An answer with no line kept, a failed or stopped call keeps nothing; the next trigger tries again. Event `journal_digested` gains `why` (`done`, `ask`, `open` or `add`) and `dropped` (a count), never a word of the view. Tests in tests/test_idea_journal.py: a line naming nothing given is dropped; Product with no tree says so and names no job; a fake answer over this repository's own pages and decisions keeps only lines naming a slug or §.
  - proves: Tech's "…a line naming no goal slug, § or map part it was given is dropped before the view is kept" (its second half); Product's "When Product's view is written for this repository, then it says what works, what hurts and what comes next, each line naming…", "When Product's view is written while the Board holds no tree…"
- [ ] H. A goal done begins its route's views
  - party: Tech. `core/idea_journal.py`: `journal_view(party, why)` begins the view's call without `DIGEST_AFTER`'s twelve entries, one a party; False, never an error, when `_may_run()` or `refuse_spent()` refuses, or the party is busy (`goal:<party>`); `journal_view_for(parties, why)` once each. `gui/ideas_journal.py`: `views_when_done(slug)` begins the views of the goal's `route` (its page's, else its party). In the window: `gui/ideas_gate.py` `_flag_when_done` calls it first (so `gui/ideas.py` gains no line). Outside: `gui/ideas_phase.py` `phase_moved` calls it for a page moved to done (`m["to"] == "done"` and not `m["new"]`: a page laid done is history, spec 155 G.2, and begins none). `ideas.add`'s trigger (spec 125 D) stays and begins the same call. Tests in tests/test_idea_journal.py and the phase's tests (tests/test_goal_phase*.py): one call a party of the route; none when the window or the limit is spent.
  - proves: Tech's "When a goal moves to done, in the window or outside it, then one view call is begun for each party of its route, and none when the window or the limit is spent"
- [ ] I. The view read, and a look now
  - party: Tech. `gui/ideas_journal.py`, registered in `journal_commands` (no line in `gui/ideas.py`): `ideas.view {party}` → `{view: {text, at, read} | {}, looking: bool, leader}`, and logs a new event `view_opened` (`party`, `at`: the view's date or "", never its words) in `realm/event_log.py` (`EVENTS +=`); `ideas.view_look {party}` → `keeper.journal_view(party, "ask")` → `{ok, asked, why?}`, a refusal's plain words in `why`; a second ask while one runs begins none. Tests in tests/test_journal_readers.py (or a new tests/test_leader_view.py).
  - proves: Tech's "When the person asks for a look now…, then one view call is begun; a second ask while it runs begins none" (the press); Product's "When the person opens a leader's view, then an event names the party and the view's date, never its words…" (the host's half)
- [ ] J. Orkboard's own look, on opening a tab
  - party: Tech. `gui/ideas_concerns.py` `concerns` (the command a tab's opening calls, the map's look on open: §282.2, Product's *Defaults*): after the map's look, `keeper.journal_view(party, "open")`, begun only when the party's view is a day old (`DIGEST_AGE_S`) or there is none, quietly; a party busy with its map's look begins none and the next opening tries again. No new timer. Tests in tests/test_concerns.py.
  - proves: Tech's "…or a map's look runs on open and the view is a day old, then one view call is begun…" (the open)
- [ ] K. In a skill, the leader's Accept pass writes its view
  - party: Tech. `realm/seat_frames.py`, a leader's `accept` step, *Write*: one more line, its view in `<wiki>/journals/<party>.md` in the tree (§282.6): front matter `orkboard-journal: <party>`, `party:`, `digest: "Works: …; … Hurts: … Next: …"`, `digest_at:` (now) and `digest_read:` (what it read), read from the goal pages and the decisions log (§282.3), each line naming the slug, § or part it rests on; the file's entries left as they are. `realm/agent_rules_text.py` `role_body`: a leader's role file gets a short part *Your view* saying the same, so `roles/<craft>-leader.md` tells it (not `seat_accept_rules.rules()`, which the window's call also reads). Then this repository's generated files are written again by Orkboard's writer (`realm/agent_rules.py`), never by hand: `llm-wiki/general/roles/{product,design,tech}-leader.md` and `.claude/skills/{product,design,tech}-leader/SKILL.md`. Tests in tests/test_seat_frames.py, tests/test_agent_rules.py.
  - proves: Tech's "When a leader's Accept frame is written for a skill, then it tells the leader to write its view…"; Product's "When the product leader's Accept pass runs as a skill, then its role file tells it to write Product's view into journals/product.md…"
- [ ] L. The view on its tab, in the face picked
  - party: Design, only after B's pick. The view in the face the person picked (the bubble: `js/table/ask.js`; a plate: `js/table/tabs.js`; over the pane: `js/table/menu.js`; its drawing in a new `js/table/leaderview.js` and its sheet beside it): on opening it calls `ideas.view`, says *Works*, *Hurts*, *Next* (orkUI's label face), its lines (body face), its date and what it read (muted); one press away by key or pointer at 1280 × 800; Esc closes and the focus returns to what opened it; text 4.5:1 with the lamp lit and out. The evening line and the view never both open by themselves on one day: at most one opens unasked a party a day (`ask.js`'s day key). The view's word in `orkboard/realm/lexicon.py` `TERMS` (one word, today's). A browser test tests/test_leader_view_browser.py at 1280 × 800; tests/test_gui_wording.py and tests/test_design_system.py stay green.
  - proves: Design's "When the page opens at 1280 × 800 on a leader's tab whose view is written, no goal picked, then the view is one press away…"; Product's "When the person opens a leader's view, then an event names the party…" (the face's half)
- [ ] M. No view yet: one call to look now
  - party: Design, after L. Where a party has no view, its place says in one line that its leader has not looked yet, beside a button whose words say it makes one call to look now; the press sends `ideas.view_look` and the place says the leader is looking while `looking`; a refusal's words shown in the place. In `js/table/leaderview.js`. The browser test of L, a tab with no view.
  - proves: Design's "When a leader's tab opens with no view written yet, then its place says in a line that the leader has not looked yet, beside a button…"
- [ ] N. Under 760 px, from the party's …
  - party: Design, after L. At 600 px wide the party's … (`js/table/menu.js`) has an item that opens the view over the pane (no bubble opens under 760 px, `ask.js`, §181.8); it reads whole with nothing scrolling sideways (WCAG 1.4.10), Esc closes it and returns the focus to the …. No phone (§282.5). The browser test of L at 600 × 800: the view's `scrollWidth` is not past its `clientWidth`.
  - proves: Design's "When the window opens 600 px wide on that tab, then the party's … reaches the view, and it reads whole with nothing scrolling sideways"
- [ ] O. Product's view of this repository, read by the person
  - party: Product, last. Product's Accept pass, run as a skill once K has landed, writes by K's rule Product's view of this repository into `llm-wiki/general/journals/product.md` (§282.6), committed with the work; E reads it back and L shows it. The conductor shows it to the person and lays one question under *Open questions*: *Does Product's view say where the product stands?*, `asks: person`; the answer stays under it.
  - proves: Product's "When the person reads Product's view of this repository, then they find in it where the product stands, not a list of the goals done" (a [person] line)

Accepting: Tech accepts after K; Design once, after N (A and B are its stages too); Product after N, its Accept pass (a skill) writing O's view, its [person] line `cannot see` until O's answer.

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
- Which face for a leader's view? (docs/mockups/leader-view/shots/) (A, the leader's bubble / B, a plate atop the pane / C, over the pane from the party's …) — §282.4: the person picks among the mockups

## Decisions
- §291: the person's answers (8 November 2026)
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
### Why
- The view is the journal's digest grown (§282.1): one store, `<scope>.digest.json`, mirrored to the tree's `journals/<party>.md`; a second store or a second writer that wins blindly would split the truth between machines.
- Two writers now write it, the window's call and a skill's Accept pass (§282.6); today `read_in.take_outside` reads entries only, so the tree's `digest:` is overwritten by the next `journals_into`.
- Each trigger (a goal done, a press, Orkboard's look) is a cheaper call with a cost; Tech keeps it one call a party, refused as every call is, and out of `gui/ideas.py`, already past 600 lines.
### Done when
- [test] When the tree's `journals/<party>.md` holds a view newer than the machine's, then the next journals look keeps it as the party's view and writes nothing over it; an older one is replaced
- [test] When a goal moves to done, in the window or outside it, then one view call is begun for each party of its route, and none when the window or the limit is spent
- [test] When the view's call runs, then its prompt holds the done goals' pages and the decisions it read, and a line naming no goal slug, § or map part it was given is dropped before the view is kept
- [test] When the person asks for a look now, or a map's look runs on open and the view is a day old, then one view call is begun; a second ask while it runs begins none
- [test] When a leader's Accept frame is written for a skill, then it tells the leader to write its view (works, hurts, next, its date, what it read) into `<wiki>/journals/<party>.md` in the tree
### Checks
- `tests/test_architecture.py` stays green: the view's code lies in `core/idea_journal.py` and `realm/journals.py`, neither importing `gui/`; no new CLI command, no new store.
- `gui/ideas.py` and `realm/ideas.py` gain no line; a new command goes in `gui/ideas_journal.py`, and no touched module grows past ~600 lines.
- The view's call stays the cheaper tier, no tools, READS 0: the pages and decisions are given in its prompt, cut to its budget; its cost lands in the party's ledger as the *spec* stage.
- The tree's file carries the view, its date and its sources only: nothing of `.orkcraft/` beyond them, no secret, no concern's words.
- Event `journal_digested` keeps no word of the view; a failed or stopped call keeps nothing and the next trigger tries again.
### Will be
- changed orkboard/core/idea_journal.py — the digest's call becomes the view's: it reads goal pages and decisions, and is begun on a goal done, on a press and on a map's look
### Out
- The view's face, its place on the tab and its button's words: Design's mockups and the person's pick (§282.4).
- The view on the phone (§282.5), and Product's tree and its jobs (goal 163).
- The concerns written into the tree: they stay in `.orkcraft/` on one machine, shown beside the view; the tree's file carries the digest alone.
### Risks
- medium
- Two writers of one key (a skill's Accept pass, the window's call): the newest `at` wins, so a machine's clock set wrong keeps the older view.
- The landing trigger sits in `gui/ideas_phase.py`'s `phase_moved` and the window's own move to done, next to `gui/ideas.py` (770 lines), a hotspot.
- Spend grows with a route's length and with each look on open; a goal done with four parties is four calls the person may not have seen coming.
- Pages and decisions may outgrow the cheaper tier's budget; cut newest first, a view reads thinner on a long project.
### Defaults
- The view is the digest grown: `<scope>.digest.json` keeps `{text, upto, at, read}`, its text three heads, *Works:*, *Hurts:*, *Next:*, within `journals.DIGEST_CHARS`; the tree's file adds `digest_at:` and `digest_read:`.
- The call reads the goals done since the last view (their Gist and the party's section), the decisions those goals cite with the log's last ten headings, and the party's table where its hero lays one.
- A goal done begins its route's views without `DIGEST_AFTER`'s twelve entries; Orkboard's own look rides the concerns' look on open (`core/idea_concerns.py`), no new timer.
- Tech's hero is the default (Sh.man): no table kept.
