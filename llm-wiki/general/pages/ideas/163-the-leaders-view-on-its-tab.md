---
owner: board
kind: idea
track: product
order: 12
size:
priority: high
short: The leader's view on its tab
phase: talk
route: product, design, tech
asks: person
by: claude-code
schema: 3
---
# The leader's view on its tab: its digest, its journal, its concerns and its framework at work

## Gist
When I open Orkboard I want to see each leader's view of the project: on its tab, what its lens knows of the product (its digest), the decisions of its craft and what it said and what came of it (its journal), its open concerns, and how it applied its craft's framework to this project (not just the framework's name over the map). Today the engine keeps all of it (realm/journals.py, the digest, read_in of docs/decisions.md: 233 decisions, 27 into leaders' journals; realm/concerns.py) but the page shows none of the journal or the digest: spec 125 said 'No new face', and I now replace that. The project's decisions are already on the Orkmaster's tab as the past's week decks (spec 162); the leaders' views are what is missing. On a fresh open the views must not be empty: read in the project's documents and lay what the code knows without a model where it can. Desktop page only: the phone is not touched in this goal. This goal comes first, before the goals waiting in work.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

## Open questions
- Which decisions lie in a leader's journal? (**Its goals' decisions only** / By title words, as read in) — §277.4 keeps a decision of no goal off a party's tab; read_in put 27 in leaders' journals by their titles' words · Its goals' decisions only: One rule with the past; the 27 word-placed lines leave the journals · By title words, as read in: The 27 stay; a tab shows decisions §277.4 keeps on the Orkmaster's
  - Answered: Its goals' decisions only (decided by §277.4, 2026-11-08)
- What writes the digest on first open? (**The Lay the tables goal** / A goal of its own / Wait for twelve entries) — §267.4 calls no model on opening and a digest is a leader's model pass (spec 125 D), so a fresh tab has none · The Lay the tables goal: One priced pass lays each table and writes its leader's digest · A goal of its own: Its price said apart; the tabs show the journals until it runs · Wait for twelve entries: No cost now; the tab says what writes the digest and when
- Product's tree in this goal? (**Yes, hypotheses laid from the pages** / No, its own goal later) — the Gist asks each framework at work; goal 162 left the tree for later; the pages' Talk lines carry assumes: code can read · Yes, hypotheses laid from the pages: Product's tab opens with proposed hypotheses; jobs and outcome wait a pass · No, its own goal later: Product's tab keeps Propose on an empty tree; this goal ships smaller
  - Answered: No, its own goal later (decided by §277.6, 2026-11-08)
- Where does a leader's view lie? (**A plate over its map** / In its bubble under its head / A page over the pane) — the Gist asks to see it on opening the tab; a bubble or a page hides it behind a press · A plate over its map: Seen on opening the tab; the map starts lower, Tech's System too · In its bubble under its head: One press on its head; the digest sits above the question's field · A page over the pane: Opened from the party's …; the map stays whole, the view rarely found
- Its concerns in the view too? (**Listed, each a step to its card** / Marks on the map only) — a mark is a sign until its card is lifted; words in the view, pressed, step to the card (concerns.js stepMarked) · Listed, each a step to its card: The view says each concern's what; pressed, its card lifts on the map · Marks on the map only: The view holds digest and journal; the aspects' chips step to the marks
- The framework at work, laid by code? (**Code's hints by aspect, every craft** / Tech's hotspots only / Wait for Lay the tables) — map_signals lays cycles, hotspots, a11y and unserved jobs with no model; only a leader's look reads them today · Code's hints by aspect, every craft: Each tab lays its rubric's aspects with what code found, no model · Tech's hotspots only: System marks hotspots and cycles; the other tabs keep their header · Wait for Lay the tables: The view holds journal and digest; frames come with a priced pass
- Not so on each journal line? (**Not so on each line** / Read only in this goal) — ideas.journal_strike is built (spec 125) with no caller; a wrong line, as a word-placed decision, is read into every call · Not so on each line: Struck from the tab and from every later call, kept marked · Read only in this goal: The plate shows the lines; a wrong one stays read into calls

## Decisions

## Product
### Talk
- verdict: doubt — four views on every craft's tab in one goal is wide; I'd go with the journal and digest first and each framework laid only where code reads it, Product's from its pages
- stance: Product backs it: a leader's view is what makes the Board's choices trusted; laid by code on a fresh open, a model's pass only priced and started by the person (§267.4)
- for: Spec 125 keeps journals no face shows; 233 decisions and the Talk stances in the pages are there for code to lay; the person runs all through Orkboard and put this first
- against: Wide across every craft; read_in put 27 decisions in leaders' journals by title words, which §277.4 keeps off a tab; a digest is a model's call, so a fresh open has none
- instead: The journal and the digest on each leader's tab now; each craft's framework at work a goal of its own after it, Product's tree first
- assumes: the person reads a leader's view on its tab and it changes what is picked next — shown by: a week's event log: picks and answers made after a leader's view was opened

## Design
### Talk
- verdict: doubt — only if the view has one place seen on opening the tab, deals seven then All · search (§277.5), speaks in the leader's voice, not the call's *you*, and counts nothing
- stance: Design keeps the frame: the view is a plate on the tab over its map, no list column, drawer or count; the journal dealt as the past is, the digest in the body face
- for: Heuristic 1: what a leader said and what came of it is kept (spec 125) but unseen; Design's tab here is its header and aspect names over no map, saying nothing of its lens
- against: Journal lines are kept in the second person for the leader's call (*You said no to…*): shown as kept, the person reads *you* as themselves; concerns are marks on the map already
- instead: The digest and the journal on a plate over each leader's map now, concerns staying its marks; each craft's framework laid by Lay the tables (§267.4)
- assumes: a digest and seven journal lines fit a plate a third of the pane high at 1366 × 768 — shown by: a picture of Tech's tab at 1366 × 768 with a 900-character digest and seven lines laid

## Tech
### Talk
- verdict: doubt — only as one read of what the engine keeps (journal, digest, concerns, map_signals' hints) in a module of its own, and read_in split before it grows past 600 lines
- stance: Tech builds it on the desktop page alone: one host read `ideas.leader_view {party}` beside ideas_journal.py, a plate in pane.js over the map; no new store, no model on opening
- for: What it shows is kept and unseen: ideas.journal and journal_strike have no caller on the page; map_signals lays hotspots, cycles, a11y, unserved jobs by code, a framework at work
- against: read_in.py is at 502 lines, gui/ideas.py at 769; a fresh open has no digest or concerns (model passes); entries are kept in the call's *you*, misread when shown as kept
- instead: Journal, digest and code's map hints by aspect on one plate, one read a tab; concerns stay marks; reading in by goals a module split from read_in.py
- assumes: code's hints are cheap enough to lay when a tab opens — shown by: map_signals.signals for tech on this repository timed at dev's head, under a second
