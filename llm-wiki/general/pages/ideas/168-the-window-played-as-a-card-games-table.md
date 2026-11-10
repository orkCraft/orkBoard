---
owner: board
kind: idea
track: design
order: 15
size:
priority: high
short: The window as a card game's table
phase: work
route: design, tech, product
spec: docs/specs/168-the-window-played-as-a-card-games-table.md
decisions: §283, §284, §285
by: claude-code
schema: 3
---
# The window played as a card game's table

## Gist
Two card sizes; everything left and right that is a place changes the table; the leaders' tabs say through whose eyes; the
Orkmaster leads a goal with one card and deals each leader its card at every stage (idea, spec, implementation); a table for
every stage and every eye; a question lifted to the table's foot with its answers in the hand; the Orkmaster's news as a balloon;
a goal's own branch and the discard's two piles; the history as a book; the inventory as slots; pictures on the cards. The
person's proposal and answers, talked through on 9 November 2026, are decisions §283–§285; the mockup is
`docs/mockups/table-template/`.

## Why
- A goal in analysis had an empty table: its leaders got cards only at work (§241, §251.7), so the cheap stage the person uses
  most showed nothing of what the leaders said.
- The desktop drew about seventeen card sizes where §270.7 decided two, the hand and the discard changed size by what was open,
  and *Stop all* could not be pressed while a card was lifted.
- Talk read no file and doubted what one search answers (trial 152 F6); a result said *ok* where nobody had looked (trial 152-e F4).

## Done when
- [look] When the window opens at 1366 × 768, then it is laid as `docs/mockups/table-template/shots/1-project.png` shows: the column's three piles, the right column's head with the potions, the chain and Stop all, the three places in the hand's right end
- [test] When any card is drawn on the desktop, then it is 144 × 202 or 56 × 78, and the column, the table, the discard and the hand keep their sizes with anything open
- [test] When a goal is picked in each of its stages, then the Orkmaster's tab and each leader's tab show that stage's table (spec 168 C3, C4)
- [test] When a card is lifted, then it rises at the table's foot, the asking leader's tab opens and its ways are the hand, cut by the rim
- [test] When a goal's tasks land, then they land on `goal/<slug>`, and the goal goes into dev once, after its last acceptance and a green gate
- [test] When a goal is done, then its result says *ok* only for the lines its acceptance met
- [test] When the inventory opens, then its settings are slots on the table and their ways cards in the hand
- [person] When the person plays a goal from an idea to main, then every stage's table says what the leaders said and did

## Out
The phone and the window under 760 px; Release's and Live's tabs; a branch chosen for a single goal; the log as the tool's
events; the lich's seal; the pictures themselves (made by the owner from `docs/pictures-wanted.md`).

## Risks
- high
- Ten goals' worth of work in one spec: each wave reaches main on its own critical tests, so a later wave may find an earlier
  one's face wrong; the leader's look after each goal is the net.
- F (a goal's branch) changes where every task lands: a fault there strands work; it is built on git fixtures first.
- C1 and H4 grow the leaders' calls (needs, better, ways); Talk's minute is measured after C (§283.23).

## Depends on
Decisions §283, §284, §285; orkUI 0.37.0 (the book, the ringed back) before A5.

## Stages
The spec's waves, in order: **1** A (A0 orkUI 0.37.0, A1–A6) · **2** B (B1–B3) · **3** C (C1–C5) · **4** D (D1–D5) · **5** E (E1) ·
**6** F (F1–F4) · **7** G (G1–G3) · **8** H (H1–H4) · **9** I (I1) · **10** J (J1–J2). A stage a Grunt on the simpler model, in a
worktree of its own; the parts of a wave sharing no file side by side.

**Where it stands** (10 November 2026): waves **A–I are built and in main**, each merged on the critical tests and its stages' own; J1 (a way's
kind) and J3 (the heads, orkUI 0.38.0, from the owner's pixel art) are in main. **The owner's art is made** (decision §290, 10 November 2026): the cartoon heads K1, K2, K3, K4 (a 3x2 grid, the Grunt first), K6 and one sheet of moods
(8 heads x 5), and the pixel card sheets 1 to 4 (the fourth in two takes). The heads are cut as a mockup (`docs/mockups/table-template/heads/cartoon/`);
**J3 comes again, in the cartoon**, once orkUI (`races/art/`) takes them in and they are copied here: the members' tiers laid by code from the
leaders' gear in K3, the heroes showing their calm face (their moods, and K6's small faults, wait until after the beta). **J2 takes the pixel
pictures for the beta**; the cards' pictures are redrawn in the cartoon later (P1–P4, O1–O6), when the work moves to the phone, then on the
desktop. The code reads orkUI's `pictures/pictures.json` and the heads by their names, so they arrive as files.

**Not accepted yet** (left from the stages, for their leaders' look or a later goal):
- D1: a lifted plan, decision or route lies in a hand-high panel, not yet as ways' cards.
- H4: *Replay* on a Silent leader's veto card works while the goal is still at Talk; Pen has no face of its own; the seats' grid is the stall's.
- H1–H2: the narrow page and the phone keep the old stall (the spec said the stall goes and the narrow page stays: the narrow page won).
- I1: a task run in the person's own AI tool must be marked `own_tool` by that run (spec 151, §258) for the log's face to say so.
- F3: *To main without the tests* is a quiet button in the To main bar, not a menu; the dissolve is a stepped fade, not the portal's runes.
- The leaders' acceptance passes (Design for the faces, Tech for the engine) after B–I are still to run; each wave was looked at from its
  pictures and diff and its tests when merged.
- Old reds not caused by this goal (they failed before wave A): the hand field over a map part in two picking tests, the seal's ring in
  `test_field_squares_browser`, the plus-party in `test_owners_day_desktop_browser`, the phone's fan sigils, three phone-send tests.

## Open questions

## Decisions
- §283, §284, §285 (9 November 2026, the owner): every point of this goal; Talk is answered by them.
