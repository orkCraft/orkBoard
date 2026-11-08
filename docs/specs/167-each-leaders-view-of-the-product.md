# 167. Each leader's view of the product, on its tab: the product as its framework sees it, with its digest and its concerns; written again when a goal closes, when asked and on Orkboard's own look; its face chosen on mockups

Goal: `llm-wiki/general/pages/ideas/167-each-leaders-view-of-the-product.md` (route: product, design, tech). The person's request is the page's *Gist*. This spec is the leaders' sections of that page as they wrote them in the Board's flow (Talk, then their sections), with the person's answers above them (decision §282); each leader's *Talk* and *Accepted* stay in the page. **Builds:** the goal's stages (the page's *Stages*, the Taskmaster's), each task by a Grunt on the simpler model, in the branch `claude/stoic-newton-c85q7q`, into a pull request.

## The person's answers (8 November 2026)

1. What is a leader's view? — **The product as the leader's framework sees it (its hero's places), with its journal's digest and its concerns, in the window; the face agreed on mockups**.
2. When is a view written again? — **When a goal closes, when the person asks, and when Orkboard analyses the project by itself**.
3. What feeds a view made in a skill? — **The call reads pages and log**.
4. Where does a leader's view lie? — **Two or three mockups first, the person picks among them; the use cases talked of here lie on Product's table (goal 163)**.
5. Where is the view under 760 px and on the phone? — **No phone for now: a goal of its own**.
6. Who writes the view in skills? — **The leader's Accept pass, in the tree**.

## Product

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
