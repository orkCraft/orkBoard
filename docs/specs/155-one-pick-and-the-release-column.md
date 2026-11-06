# 155. One card picked, on either side; the table by the phase; the Release column at the right; the die and the drum in the hand

Decisions §260, §261. **Builds:** the cheaper model, a part a session, each in its own worktree, reviewed by the spec's author and
merged into `main` on the critical tests and the part's own (CLAUDE.md, alpha). **Waves** (parts of a wave share no file):
**1** A, B · **2** C · **3** D · **4** E (§261.5: C and D share `table/pane.js`). The page's paths are under `orkboard/gui/static/js/`. No mockup: the owner took the idea
from its words (§260's *Why*).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. orkUI 0.31.0** | the die at 2 px a cell (`.small`); the drum of potions (`.ork-drum`) | orkUI (`office/die/`, a new `office/drum/`), then `python -m orkboard.design.orkui <orkUI>`; `tests/test_design_system.py` |
| **B. One pick** | one card picked from the column (face down too) or the hand's lifted card's goal; put away by itself, Esc, an empty press or the address; the tabs grey off the route; no × | `frame/state.js`, `table/table.js`, `table/column.js`, `table/piles.js`, `table/fan.js`, `table/tabs.js`, `table/pane.js` (`Title`), `hand/stacks.js`, `realm/lexicon.py`; `test_column_browser.py`, `test_column_fan_browser.py`, `test_pile_waits_browser.py`, a new `test_one_pick_browser.py`, `test_gui_wording.py` |
| **C. The table by the phase** | the table shows the picked card's phase at each tab; the phases a mark; *Earlier* folded | `table/pane.js` (`Phases`), `table/goalview.js`, `table/talkpage.js`, `table/specpage.js`, `table/qualitypage.js`, `table/boardmap.js`, `hand/routecard.js` (read only); `test_goal_phase.py`, a new `test_table_by_phase_browser.py` |
| **D. The Release column, no edge** | Live and Release tabs at the row's end; the discard a lane under Release's tab, on every tab, through its eyes; the portal round the ready card; the past deeper in it; the edge, the pyramid and the lich's line gone | `frame/frame.css`, `frame/frame.js`, `frame/edge.js` + `edge.css` (gone), `table/tabs.js`, `table/data.js` (`roadParties`), `table/road.js`, `table/discard.js` + `discard.css`, `table/portal.js` + `portal.css`, `table/checks.js`, `table/pyramid.js` + `pyramid.css` (gone), `table/chronicle.js` and its parts, `table/pastseen.js`, `table/tabmarks.js`; `test_discard_table_browser.py`, `test_portal_browser.py`, `test_road_browser.py`, `test_chronicle_browser.py`, `test_table_edge_browser.py` (made the Release column's), `test_pyramid_browser.py` (gone) |
| **E. The hand's right end** | the small die and the drum under the discard, the hand's height; Stop all and Resume in words under the die; the drum turned by the Board, unrolled on hover | `hand/playdie.js`, `hand/mana.js`, `hand/mana.css`, `hand/windows.js`, `hand/addtool.js`, `hand/hand.css`; `test_play_die_browser.py`, `test_hand_mana_browser.py`, `test_mana_two_windows_browser.py`, `test_mana_notice_browser.py`, `test_hand_desktop_browser.py` |

## A. orkUI 0.31.0 (§260.11, §260.13)

Made in orkUI (`github.com/orkCraft/orkUI`), then copied:

1. **The die's `.small`**: the cell 2 px, a box of **48 × 60** (a face of 36), whole pixels as `big` is; `tools/build_die.py`
   writes it. The front face's marks (`front-stop`, `front-resume`, `right-resume`) stay in orkUI for whoever uses them;
   Orkboard stops using them (E.3).
2. **The drum** (`office/drum/`, `.ork-drum`): a row of `.ork-potion`s laid as a drum seen from the front: **the front one at its
   own size** (3 px a cell, one of the four bottles of 0.23.0); **its two neighbours at `.small`** (2 px a cell), each half behind
   it, at brightness 0.62; the others hidden. **A neighbour `.is-alert`** (§261.1) is at full brightness, not behind the front,
   with room under it for its share in words. `--ork-drum-front` names the front's index; changed, the drum turns: each potion
   slides one place round (a transform on `--ork-motion-base`; none under `prefers-reduced-motion`). **`.is-open`** lays the drum
   as a row, every potion at its own size, nothing dimmed. The box at rest is at most **88 × 90** (the front's 42 and two halves
   of 28, its mark above, its share under), and at most **124 × 90** with an alert neighbour (the die's 48 and a gap beside it
   stay within the Release column's 180).
3. Tests: `test_design_system.py` holds the copy (the version, the die's `.small` box, the drum's sheet with no colour of its own).

## B. One pick (§260.1–3, §260.5–6)

1. **The state** (`frame/state.js`): `picked` stays the one pick, the goal's slug or "". `pick(slug)` toggles, as today. **Esc**,
   with nothing open over the pane, puts it away; a press on an empty place of the column puts it away. **The address**: the pick
   is written as `#goal=<slug>` (`history.replaceState` when it changes from a pick to another, `pushState` from none to one), read
   on load and on `popstate`; a slug the snapshot does not have reads as none. `lifted` stays for a hand's card only (B.4).
   **One writer** (§261.4): only `frame/state.js` writes or reads `#goal=` and handles the pick's Esc; `table/table.js` drops its
   own Esc for the pick and its effect that opens the picked goal's party's tab (today about its line 72) and calls state.js's
   instead. Its narrow back entry (`useBackButton`) keeps its order with the pick's: a file opened over a pick closes on the
   first back, the pick on the second.
2. **The column** (`table/column.js`, `table/piles.js`, `table/fan.js`): **a face-down card is picked by a press**, as a face-up
   one; the pile's list over the pane goes (its *Next* and *Remove* stay in the goal's menu; the order by dragging as today).
   **A pile hovered or focused fans its backs** (fan.js's fan, the one back), so each is reached; §236's tuck and slide stay for
   the pile's top card. **The picked card**: risen by the rise token, its edge in the ink (`--ork-ink`, the frame line's width
   doubled), nothing else dimmed. A card of *To review* picked shows *Start now* and *Hold* on the table through the Orkmaster
   (C), no more in a lift over the pane.
3. **The pane's title** (`table/pane.js` `Title`): the picked goal's rune and title, then the phase mark (C.2); **the ×
   (`table-title__unpick`) goes**. ← stays only while a file or a diff is open over the pane (`over` of kind `file` or `diff`).
4. **The hand** (`hand/stacks.js`): a hand's card lifted picks its goal too (`pick` with the card's goal, never toggling it off);
   its lowering leaves the pick. While a goal is picked, its cards in the hand wear the ink edge of B.2 at the hand's size.
5. **The tabs** (`table/tabs.js`): while a goal is picked, a party's tab whose party is not on its route (`route`, none while
   not routed) is **grey** (`is-off`: its head at the asleep look, its name muted) and its `title` is §260.15's line; pressed, it
   puts the pick away and opens that tab. The Orkmaster's tab is never grey. When the pick changes to a goal whose route lacks
   the open tab, the Orkmaster's tab is opened (`openTab`, as the person's own press: §139.3 holds, the code opens it on the
   person's pick). The dot of *the picked goal's route has it* goes: grey says it.
6. **The words** (`realm/lexicon.py` `TERMS` and the strings): §260.15's grey line; `test_gui_wording.py` checks it.
7. Tests (a new `test_one_pick_browser.py` at 1280 × 800 with the column's host): a face-down card pressed is picked (the
   address holds `#goal=`); the same card pressed again, Esc, an empty press of the column and the browser's back each put it
   away; no `[data-unpick]` in the title; a goal routed to Tech and Design greys Product's tab, whose press leaves the pick and
   opens Product; a pick from Design's tab to a goal without Design opens the Orkmaster's tab; a hand's card lifted picks its goal.
   At 390 px: a pick, then a file opened over it, then the browser's back twice closes the file, then the pick (§261.4).
   `test_column_browser.py` and `test_column_fan_browser.py` made to the press and the fan; `test_pile_waits_browser.py` without
   the pile's list.

## C. The table by the phase (§260.4)

1. **What the table shows for the picked goal** (`table/pane.js`, `table/boardmap.js`, `table/goalview.js`): through the
   **Orkmaster**: while not routed or routed and not talked, its route and its cost (the route card's words, `hand/routecard.js`,
   read only: its acts stay the card's in the hand); from Talk on, its plan in the lanes as today (§206.4). Through **a leader on
   its route**: **Talk**, its say (talkpage.js's stance of this party, the verdict, for, against, what instead); **Spec**, its
   section (specpage.js's section of this party); **Work**, what it will change (GoalView, as today); **Done**, what it changed
   against what was promised (GoalView's result) and, under it, the quality record (qualitypage.js). The pages Talk, Spec and
   Quality no longer open over the pane: each is drawn as the table.
2. **The phase mark** (`Phases`): *Talk · Spec · Work · Done*, spans, the one now `aria-current="step"`, the ones gone by lit;
   **no button**.
3. **Earlier** (§260.15): under the table, while the goal is past Talk, one folded line *Earlier: Talk · Spec* (the phases gone
   by); a phase pressed unfolds what it said at this tab in place (the same parts as C.1), pressed again folds it. Nothing over
   the pane.
4. Tests (`test_goal_phase.py`, a new `test_table_by_phase_browser.py`): a goal in Talk picked on Tech's tab shows Tech's stance
   and no `button[data-phase]`; in Spec, Tech's section; at work, GoalView; done, the result and the quality record; *Earlier*
   unfolds Talk's stance in place; through the Orkmaster a routed goal not talked shows its route and cost.

## D. The Release column, no edge (§260.7–10)

1. **The frame** (`frame/frame.css`, `frame/frame.js`): at 760 px and up the third column `--edge-w` and `.frame-edge` go
   (`frame/edge.js`, `edge.css` removed). **`--cols`** becomes the lanes, the tabs' end (`minmax(280px, 1fr)`, the empty chair
   and the door), **Live's lane** (`--col-w`, when the project has a Live party) and **Release's lane** (`--col-w`), the last,
   flush with the window's right edge less the gutter. The hand's grid follows (its last track the Release column's: E).
2. **The tabs** (`table/tabs.js`, `table/data.js` `roadParties`, `table/road.js`): at the wide width Release and Live are tabs
   as at the narrow one and in a project with no gate (spec 113 §4), **Live before Release, Release last**; their heads leave
   the ring. `road.js` keeps the corners' waking rules (§188.2) for the tabs' faces (asleep, awake, at work, an alert).
3. **The discard is Release's lane, on every tab** (`table/discard.js`, `discard.css`): the label *Discard* on the Orkmaster's
   tab, *<party>'s discard* on a party's and on Release's; the cards whole, the hand's size, **top to bottom**: the goal ready
   for main (D.4), the goals done and not yet seen (newest first; the moon as today), then the past (D.5). On a party's tab, a
   goal is there when its route held the party; on Live's tab, the project's. Each card is picked (B), the discard's view over
   the pane (`discard` kind) goes. A goal seen still leaves *not yet seen* (`ideas.seen`, sent when it is picked) and lies
   with its version in the past.
4. **The portal** (`table/portal.js`, `portal.css`, `table/checks.js`): drawn **round the top card while a goal is ready for
   main, its checks run, or the rite plays**, else no ring (`is-asleep` goes). The ready card picked: its *To main* is on the
   table through every tab on its route, and **Release's table shows its checks**, a skeleton a check with its name and its
   state, the red one's *why* in words (`checks.js`'s data, laid in the pane, not in front of the portal). *To main* pressed
   plays the rite at the discard's top (`is-sending rite-<element>`), as today. With no gate (`noGate`) no portal, as today.
5. **The past deeper in the discard** (`table/chronicle.js` and its parts): under the goals not yet seen, *Unreleased*, then a
   deck a version, newest first, through the open tab's eyes (`ideas.chronicle {party}` of spec 150 E1); a deck pressed deals
   its cards in the lane, pressed again gathers them; a card is picked (B) and the table shows it as it was (C.1's *Done*). The
   chronicle over the pane, the lich's line, the pyramid (`table/pyramid.js`, `pyramid.css`) go. **A decision newer than a
   party's last look** (`pastseen.js`) is a muted dot on its tab (`tabmarks.js`), gone once that tab's discard is scrolled to it.
6. **A project without a Release party**: its last lane is the discard with no head over it and the word *Discard*; no portal
   unless the gate has a main.
7. **Heights**: the lane scrolls with the table (only the table scrolls, §254.2): the ready card and the first not seen are in
   view at 1366 × 768.
8. Tests: `test_table_edge_browser.py` made the Release column's (at 1280 × 800 no `.frame-edge`; Release's tab the row's last,
   Live's before it; the discard's lane under Release's tab, its right edge the table's); `test_discard_table_browser.py` (the
   discard on Tech's tab holds Tech's goals only, its label *Tech's discard*; a card pressed is picked, no `discard` over);
   `test_portal_browser.py` (no ring while nothing is ready; the ring round the ready card; To main from the picked card; the
   checks on Release's table); `test_road_browser.py` (the tabs' faces by the old corners' rules); `test_chronicle_browser.py`
   (the decks in the lane); `test_pyramid_browser.py` removed; at 390 px the narrow page as today.

## E. The hand's right end (§260.11–13)

1. **Its place** (`hand/hand.css`): the hand's last track is the Release column's (`--col-w`); in it, side by side, **the die**
   then **the drum**, both standing in the hand's shown height (`--hc-shown`, 100 px at the wide width) with their words.
2. **The die** (`hand/playdie.js`): orkUI's `.small` (48 × 60); its up face as today (the arrow, the spark, the pips, the cross,
   asleep the five). One press over the whole die: Play.
3. **The word under it** (§260.12): *Play* (*Playing* while the preview plays), and, **while the orks work, the button *Stop all***
   in the danger's colour (`halt_all` as today, `aria-label` *Stop all: stop every run of this project's orks*); **stopped, the
   button *Resume***. The front face's marks and the quarter turn (`is-turning`, `right-resume`) go.
4. **The drum** (`hand/mana.js`, `mana.css`): orkUI's `.ork-drum`. **The front** is the active tool: the picked goal's work's tool
   while a goal at work is picked, else the open tab's (§177.1's rule, its frame gone); **the neighbours** by the person's order
   (`tools.order`) round it, **except that a tool at the warn or the danger level** (`levelOf`) takes the nearer neighbour's place,
   **at full brightness (`.is-alert`) with its share in words under it** in its level's colour (§261.1: *8%*, *back 14:00*).
   The front's share under it as today (*62%*, *back 14:00*, *week 80%* by §192's rules); a neighbour at rest has no words. The drum
   turns when the front changes; nothing the person does turns it.
5. **Unrolled** (`.is-open`, hover or focus, Esc or the pointer leaving folds it): a row over the hand, right-aligned to the
   window, every potion with its mark and shares (a lifted card's cost hatched off its tool's top as today), and at
   its end **the empty slot** (`hand/addtool.js`'s adding card; lit while the Orkmaster asks for a tool, as §232.4). A potion
   pressed lifts its tool's card (`hand/toolcard.js`), where the person sets which tool a party works on; a drag in the row
   changes `tools.order`.
6. **More than six tools**: the row unrolled shows them all, two rows when they do not fit; the drum keeps three in sight.
7. Tests: `test_play_die_browser.py` (the die's box 48 × 60; *Stop all* a button under it only while a run is on; *Resume* after
   it; no `.front-stop`); `test_hand_mana_browser.py` (three potions drawn at rest whatever the count; the front the open tab's
   tool, then the picked goal's; a tool in danger beside the front, not dimmed, its share in its words; hover unrolls every potion and the empty slot); the die and
   the drum inside `--hc-shown` and inside the Release column's width at 1280 × 800.

## Order of building, and what each part must not do

- **A** first in orkUI; nothing here draws a die at 2 px or a drum before it is copied.
- **B** and **A** together (no shared file). **C** after B (the title's ×, the pick). **D** after C (both change
  `table/pane.js`: C its `Phases`, D the `discard` view it draws; §261.5). **E** after A and D (the hand's last track is the
  Release column).
- No part changes the narrow page's or the phone's layout; each runs the 390 px test of its modules.
- No part adds a list column, a drawer or a count of what waits (CLAUDE.md's frame); the discard is cards, the past decks.
- The host is not touched but for `ideas.seen` on a pick (D.3), which it already has.
