# 150. The table, its edge and the past through the open tab; one back; a conflict thrown; the new goal's corners; the first open as four cards

Decisions §254. **Builds:** the cheaper model, a part a session, each in its own worktree, reviewed by the spec's author and
merged into `main` on the critical tests and the part's own (CLAUDE.md, alpha). **Waves** (parts of a wave share no file):
**1** A, B, C · **2** D, E1 · **3** E2, F · **4** G. The look: `docs/mockups/table-edge/` (its sections are named below).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The column under a card** | the Orkmaster's column is covered, not cut, by a card laid over it (§254.10) | `frame/frame.css`, `table/column.css`, `hand/hand.css`; `tests/test_column_browser.py` |
| **B. orkUI 0.30.0** | one back (variant C), the conflict sign, Resume on the die's right face; copied in | orkUI (`office/backs/`, `office/signs/conflict.svg`, `office/die/`), then `python -m orkboard.design.orkui`; `tests/test_design_system.py` |
| **C. The word *table* and words that fit** | `map` says *table*; the page's words; a budget in the calls that word a card | `realm/lexicon.py`, the page's strings (list in C.2), `realm/idea_words.py`, the calls in C.3; `tests/test_gui_wording.py`, `tests/test_lexicon*.py`, the calls' tests |
| **D. The table's edge** | the ring (the imp at twelve, the lich at six) always drawn, the discard, the die, the potions in a strip at the right of the table and the hand; the die's right face | `frame/frame.css`, `frame/frame.js`, a new `frame/edge.js` + `edge.css`, `table/portal.js`, `portal.css`, `road.js`, `discard.js`, `discard.css`, `table/pane.js`, `hand/hand.js`, `hand/hand.css`, `hand/mana.css`, `hand/playdie.js`; `test_portal_browser.py`, `test_discard_table_browser.py`, `test_road_browser.py`, `test_play_die_browser.py`, `test_hand_mana_browser.py`, a new `test_table_edge_browser.py` |
| **E1. The host: a conflict and the past by craft** | the decision's call says a conflict as data; a `conflict` card in the hand; its answer; the chronicle read by party; the last three decisions of a craft | `core/idea_decide.py`, `realm/board_map.py`, `gui/ideas_board.py`, a new `gui/ideas_conflict.py`, `gui/ideas_chronicle.py`, `realm/chronicle.py`, `realm/chronicle_decisions.py`; `test_idea_decide*.py`, a new `test_conflict.py`, `test_ideas_chronicle.py` |
| **E2. The page: the conflict card, the past, the pyramid** | the conflict card and the earlier decision out of the portal; the lich opens the past through the open tab; the pyramid in the ring | a new `hand/conflictcard.js`, `arena/arenawords.js`, `table/chronicle.js` + its parts, `table/releasemap.js`, a new `table/pyramid.js` + `pyramid.css`, `table/portal.js`; `test_chronicle_browser.py`, a new `test_conflict_browser.py`, a new `test_pyramid_browser.py` |
| **F. The new goal's corners** | rune, kind, who picked in the corners; **Now** and **Later** | `hand/pluscard.js`, `hand/fieldsquares.js`, `hand/openedcard.css`, `gui/ideas.py` (`ideas.add`), `gui/ideas_route.py`; `test_field_squares_browser.py`, `test_hand_desktop_browser.py`, the host's `test_ideas_add*.py` |
| **G. The first open as four cards** | the dark room, the Orkmaster's four backs thrown to the potions, the portal, the table, the hand | `hand/setupcards.js`, a new `frame/firstopen.js` + `.css`, `realm/first_open.py`, `gui/first_open_cards.py`; `test_first_open.py`, `test_first_open_browser.py` |

## A. The Orkmaster's column under a card (§254.10)

1. Today a card over the column (the new goal's field, `hand/hand.css` `.hand .hand-field`, fixed, z 50 in `.hand`'s context;
   the lifted card `.hand-card--big`, z 60) lies over `.frame-column` (z 1), but the column's piles are clipped at their own
   box (`column.css` `.col-scroll`, `.col-room` `overflow: hidden`, the hover's `margin-right: -72px` slide) so that what is
   under the card looks cut at the card's edge. **The rule**: the column is never clipped at a card's edge; a card over it
   covers it whole, with the card's shadow (`box-shadow` in the canvas at about 60%, a token's colour) falling on it.
   Find what draws the cut (a clip on the column, or a background patch of the field's that matches the card's box) and
   remove it; keep the column's own tuck (13 px under the window's edge) and its never-scroll rule.
2. Test (`test_column_browser.py`): with the field open over the column at 1280 × 800, the column's *At work* card under
   the field keeps its full width (its box is not narrowed or clipped: `getBoundingClientRect().width` is 144) and the
   field's computed `box-shadow` is not `none`.

## B. orkUI 0.30.0 (§254.4, §254.5, §254.6)

Made in orkUI (`github.com/orkCraft/orkUI`), then copied (`python -m orkboard.design.orkui <orkUI>`): **one back**
(`backs/back.svg` on a 40 × 56 grid: four plain one-cell strips, a curl in each corner; `back-small.svg` without the curls;
the ring of runes drawn by `.ork-card-back` itself, `.ork-card-back.small` for backs under about 100 px); **`signs/conflict.svg`**
(two cards crossed) and `.ork-sign.conflict`; **`.ork-die.right-resume`** (Resume on the right face in `--_side` with
`.front-stop`). After the copy, the page drops any ring it drew over a back itself (`table/fan.js`, `table/piles.js`,
`hand/stacks.js`, `table/turnfly.js`: an `.ork-sigil` inside a back) and puts `.small` on backs under 100 px (the fan's
56 × 78). Tests: `test_design_system.py` as it holds the copy; the fan's test asks the rune in each back's middle as today.

## C. The word *table* and words that fit (§254.1, §254.2)

1. **`TERMS`** (`realm/lexicon.py`): `_t("map", "table", "tables", "map", "maps")`. *Lens* and *view* are not put in `was`
   (they would match `pitch_view` and the goal's `lens`, other concepts): the strings that say them for what a tab shows are
   changed by hand (2). `board_map` (*Map*, spec 39) is another concept and stays.
2. **The page's words** (each a template's own text, so `test_gui_wording.py` catches what is left): `table/data.js`
   `MAP_NAMES` (*Board* stays *Board*; *System* → *Tech's table*; every tab's map named *<Leader's party>'s table*, the
   project's *the Orkmaster's table*); `table/mapkit.js` *The map could not be read* → *The table could not be read*;
   `table/tabs.js` *is looking at the map* → *is looking at the table*, *has an alert on the map* → *on the table*;
   `table/header.js` *looks at the map again* → *at the table again*; `table/ask.js` *is reading the map* → *the table*;
   `table/picking.js` *Open <name>'s map to pick* → *table*; `table/hypothesisform.js` *Whose map* → *Whose table*;
   `table/goalview.js` *on the whole map*, *on <name>'s map*; `hand/routecard.js` *touches its map* → *touches its table*;
   `table/portal.js` *Release: open its view* → *Release: open the past*, *Live: open its view* → *Live: open what is live*.
   The phone's `pitch_view` words stay. Every string a test checks is changed with it.
3. **The budget in the calls** (`realm/idea_words.py`, one place): `CARD_TITLE_WORDS = 7`, `CARD_LINE_CHARS = 140` and
   `CARD_RULE = "A card's title is at most seven words; what a card says under it is at most three short lines (140
   characters); the whole is kept for the card lifted."`. Every call that names or words a card says `CARD_RULE` in its
   rules and asks its title in seven words: the Orkmaster's goal title (`core/idea_goals.py` `goal_prompt`, `core/idea_draft.py`),
   a leader's question (`core/idea_talk.py` `round_prompt`: `q` its title, `why` its line), a task's name
   (`core/idea_plan.py` `plan_prompt`, today *60 characters*), the decision's title (`core/idea_decide.py` `decision_prompt`,
   today *120 characters*). The parsers keep their character caps as a net (`idea_words.title_of`, `idea_questions`); a
   title over seven words is kept whole (no cut in the middle of a thought, §247.4) and the page clamps it.
4. **The page's net**: a card's title is clamped at three lines and its window's words at three (`-webkit-line-clamp`,
   `overflow-wrap: anywhere`), with the whole in its `title` and on the lifted card; check `table/card.js`, `table/corners.js`,
   `hand/stopcard.js`, `table/discard.js`, the column's cards.
5. **Only the table scrolls** (§251.4, §254.2): at the wide width nothing outside `.frame-table` scrolls but an opened
   card's body and what opens over the pane; a new browser test at 1280 × 800 and 1366 × 768 with a full board (the
   column's host) asks that `.frame-column`, `.frame-hand` and their descendants have no box whose `scrollHeight` exceeds
   its `clientHeight` with `overflow-y` `auto` or `scroll`, the opened card's body excepted.
6. Tests: the lexicon's tests for the term; `test_gui_wording.py` green; a test per call that its prompt holds `CARD_RULE`.

## D. The table's edge (§254.3, §254.4)

1. **The frame** (`frame/frame.css`, `frame.js`): at 760 px and up the frame has a third column, **`--edge-w: 212px`**, to
   the right of the table and the hand, spanning both rows: `<aside class="frame-edge">` (a new `frame/edge.js` + `edge.css`)
   on orkUI's room, a frame line at its left. Under 760 px nothing changes (the narrow page and the phone keep theirs). The
   tabs' row, the lanes and the hand keep their grid (`--cols`) inside the table's column.
2. **What lies in it, top to bottom**, `justify-content: space-between`, nothing else, no words but each object's own:
   **the ring** (`table/portal.js` `Portal`, moved from `.table-end`), **the discard** (`table/discard.js` `Discard`, moved),
   **the die** (`hand/playdie.js` `PlayDie`, moved from `.hand-end`), **the potions** (`hand/mana.js` `Mana`, moved, at the
   hand's level, the empty slot with them). `DiscardEnd` and `.table-end` go from the wide pane (`table/pane.js`,
   `discard.css`), and `.table-body`'s `padding-right` for the end with them; the hand's last track (`.hand-end`) goes at
   the wide width. The narrow page keeps `.table-end` and `.hand-end` as today.
3. **The ring is always drawn from Start** (this changes §247.1, `portal.js` `drawn`/`is-bare`): while a project has a gate
   (`noGate()` false) and is laid, the ring is drawn; nothing ready, it is asleep (`is-asleep`, faint and still: no
   `is-bare`). *Main* (its label) only while something is ready or checked.
4. **The heads on the ring** (`table/road.js` `Corner`, `portal.css`): Live's head (the imp) **on the ring at twelve**,
   Release's (the lich) **at six**, each 36 × 33, its word beside it (*Live*, *Release*) in the caption's face, asleep grey
   as today, woken as today (§188.2). Pressed: the imp opens Live's view as today; the lich opens **the past** (E2; until
   E2 lands, Release's view as today). The skeletons of the gate (`road.js` `Gate`) stay in front of the portal.
5. **To main** flies the discard's card up into the ring (the card's travel, `portal-go`, now upward from the discard
   under it); the rite as today.
6. **The die** (`hand/playdie.js`): the front face Stop all, **the right face Resume** (`.right-resume`, B) while the front
   is Stop all; after a press the cube turns a quarter (`is-turning`) and the front is Resume, as today. The words under it
   as today (*Play · Stop all*, *Play · Stopped*). Its buttons are laid over its faces as today.
7. **Heights**: in a 1366 × 768 window everything in the edge fits with no scroll: the ring 192 + its heads, the discard
   144 × 202, the die, the potions; when the window is shorter the discard shows its top card cut under the die (the die and
   the potions keep their place at the foot).
8. Tests (a new `test_table_edge_browser.py` and the moved modules' tests made to look in the edge): at 1280 × 800 the
   edge is at the frame's right, its children in that order; the ring is drawn with nothing ready (asleep), the imp above
   the ring's centre and the lich below it; the table's right edge is the edge's left (the table gained the width: no
   `padding-right` on `.table-body`); the die's right face has the resume mark while Stop all is in front; at 390 px the
   edge is not drawn and `.table-end`/`.hand-end` are as today.

## E1. The host: a conflict and the past by craft (§254.6, §254.7)

1. **The decision's call says a conflict as data** (`core/idea_decide.py` `decision_prompt` and `clean_decision`): beside
   `changes`, `conflicts: [{number, point}]` (at most two): a standing decision the goal's decision goes against (read from
   the slices the call is given, `held_rule`), its number and the point in one line (`CARD_LINE_CHARS`). Kept on
   `way["decision"]["conflicts"]`. A decision with a conflict is **not confirmable** until each conflict is answered.
2. **The card** (`realm/board_map.py` `NEEDS` gains `conflict`; `way_rows`): one row a conflict, `{kind: "conflict",
   number, point, title_then (the earlier decision's title, `decisions_log`), why_then (its first line of *Why*)}`, under
   the first lane (the Orkmaster's), before the decision's card; `gui/ideas_board.py` `sort_needs` puts it before
   `decision`.
3. **The answer** (a new `gui/ideas_conflict.py`, registered as the other mixins are): `ideas.conflict {idea, number,
   choice}` with `choice` **`replace`** (the decision keeps §N in `changes`, and its cut of slices replaces §N's, as
   §233.2), **`keep`** (§N is dropped from `changes`, the decision is worded again within §N: `reword` with the line *Keep
   §N: <point>*), or **`other`** with `text` (worded again with the person's words). Answered, the conflict leaves the
   hand; the last one answered lets *Confirm and start* show. Its words: *Goes against §N*, *The new one replaces §N*,
   *Keep §N*, *Other…* (`TERMS`).
4. **The past by craft** (`gui/ideas_chronicle.py`, `realm/chronicle.py`, `realm/chronicle_decisions.py`): the chronicle's
   commands take an optional **`party`**: a decision is a party's when that party holds a slice of it (`realm/slices.py`
   `read`, standing or replaced), a goal is a party's when its route held that party; no party, the whole project. A new
   **`ideas.chronicle_last {party?, n=3}`**: the party's last `n` decisions, newest first, `{number, title, element (its
   goal's), kind: "decision", parties: [...], version, at}`, by code, no call.
5. Tests: a decision whose call says a conflict is not confirmable until `ideas.conflict` answers it; each choice does
   what 3 says (`replace` keeps the number, `keep` drops it and rewords); `board_map` gives the card under the first lane
   before the decision; `chronicle_last` by party reads the slices; the chronicle filtered by party.

## E2. The page: the conflict card, the past, the pyramid (§254.6, §254.7)

1. **The conflict card** (a new `hand/conflictcard.js`; `arena/arenawords.js` the kind's word *Goes against §N*; the kind's
   sign `conflict`, B): in the hand under the first lane, the alert's edge (it asks you). Lifted: **two L cards side by
   side over the pane**: the new goal's side (its title, its why, *Goes against §N: <point>*, the three choices) and **the
   earlier decision, come out of the portal** (its title, its why, what rests on it; a motion from the ring to its place,
   once, none under reduced motion). The choices send `ideas.conflict`. Mockup section 4.
2. **The past through the open tab** (`table/chronicle.js` and its parts; `table/releasemap.js`): the lich pressed (and a
   step of the pyramid pressed) opens the chronicle over the pane with **`party`** = the open tab's party (none on the
   Orkmaster's tab). Its title says both axes: *The past · through Design · every version* / *· v0.3*; its search *Search
   Design's past…*; at its left **a deck a version** (*Unreleased* on top, the chapters as decks, a deck picked deals its
   cards; none picked, every version, newest first, each card's version in its bottom right); **←** goes back to the tab's
   table. A card lifted is today's row (a goal as it was, a decision with *Changes* and *changed by*) with **Show on
   <party>'s table** (opens that tab, the cards of what it touched lit). The line *Earlier: v0.3 · 28 Oct ›* goes from
   Release's view (`releasemap.js` `EarlierLine`). Under the lich in the edge, **its line**: *Design's past ›*, *The
   project's past ›*, changing with the tab. Mockup section 5.
3. **The pyramid** (a new `table/pyramid.js` + `pyramid.css`, in the ring, `portal.js`): `ideas.chronicle_last {party}`
   as three small face-up cards (56 × 78: the rune, the sign `page`, *§N*, the heads) in the portal's eye, **the newest in
   front and whole, each older one smaller (0.74, 0.54) and darker (brightness 0.62, 0.42), higher, going into the swirl**.
   A decision newer than the party's last look (`localStorage` `orkboard.past.seen.<party>`, the newest number seen; written
   when the past is opened) comes out to the front with its edge in the ink; the others step one deeper (one motion, none
   under reduced motion); else it lies still. A step hovered or focused rises whole under the ring (144 × 202: title, its
   why in a line, its version); pressed, it opens the past (2) with that card lit. **While something is ready for main or
   checked, or the rite plays, the pyramid is not drawn** (it sinks: a motion down into the eye, once). Mockup section 5
   (*Or out of the portal itself*, the pyramid).
4. Tests: the conflict card under the first lane, lifted with its two sides and the three choices sending `ideas.conflict`;
   the lich on Design's tab opens the past with `party` Design and its title; the decks; the pyramid's three steps with
   their scales in order, the newest in front; a new one marked and the mark gone once the past is opened; the pyramid not
   drawn while a goal is ready for main.

## F. The new goal's corners, Now and Later (§254.9)

1. **The corners** (`hand/pluscard.js`, `hand/fieldsquares.js`, `hand/openedcard.css`): the field's squares *Rune*, *To*,
   *Type* move into the card's corners: **top left the rune** (the next given; pressed, the runes to pick, §187.3), **top
   right the kind** (default *the Orkmaster reads it*; pressed: Feature, Bug *the short way*, Tidy, Screen and the rest of
   `idea_kind`'s types, *the Orkmaster reads it*), **bottom left who** (default the crowned head and *the Orkmaster routes
   it*; pressed: the parties' heads; a party picked addresses the goal as *@Tech* and the open tab do). A corner left to its
   default is dashed and says its default; picked, drawn whole. A choice list opens on the card itself (no dialog); Esc
   closes it. *Files* stays in the window (§252.4).
2. **Bottom right: Now and Later** in place of how much: **Now** (primary; Enter) sends the goal and, once it is routed,
   starts Talk at once **when the route costs no more than the route card's limit and the limits allow** (`ideas.add`
   `now: true`: the host does what *Talk* on the route card does, `ideas_route.py`), **else** the route card asks as today
   with its cost. **Later** sends it with `later: true`: routed and laid in line to start itself at the Board's hour
   (`route_later`'s way, offered whatever the limits). Shift+Enter a new line as today.
3. Tests: the corners drawn dashed with their defaults; a kind picked is sent as `type`; a party picked as `party`; Enter
   sends `now: true`; Later sends `later: true`; the host: `now` starts Talk when the cost is within the limit and leaves
   the route card otherwise; `later` lays it in line.

## G. The first open as four cards (§254.8)

1. **The room** (a new `frame/firstopen.js` + `.css`, `hand/setupcards.js`): while `first_open.step` is not `laid` and the
   project has no parties of its own, the frame draws **the room dark**: no table, no hand, no edge; **the Orkmaster in its
   middle** (48 × 44), its bubble *I'm the Orkmaster. Four cards, and we start.*, **holding four backs** (the one back, B),
   fanned. Only the cards whose step is not done are held (a tool already in the hand: three; a project open: fewer).
2. **Each card thrown flies to its place, and the place appears as it lands** (one motion each, `table/flight.js`'s way;
   none under reduced motion: the place appears):
   1. **To the potions' place** (the edge's foot): the tools step (`tool_hand`, the adding card of spec 130 B.2 lifted
      there); a ready tool offered as one press *Use <tool>*. The first potion fills.
   2. **To the portal's place**: the ring appears (asleep); the project step's card (§232.3's answers) and **its release
      branch** (`Release branch` with the branch read from git, `main` by default, a press lists the local branches; kept
      as the project's main for the portal, the setting the gate already reads). GitHub: later (§254.12).
   3. **The table appears**: the kind's card (§232.3) and **the parties as empty chairs at the table's far side** (orkUI's
      `.ork-chair.is-empty`); a chair pressed seats its leader (its size and seats as §232's line under its head); **Start**
      lays the table in §232.1's order.
   4. **The hand appears**: the + card, and its card opens (F) **with its corners lit one at a time as each fills**; no tour.
3. A project with parties of its own is laid at once (§232.1); a second project skips the tools (as today).
4. Tests (`test_first_open_browser.py` made to the new way): from an empty folder, four backs in the room; each step's card
   lands at its place and the place appears (the potions, the ring, the table, the hand); a second project holds fewer;
   reduced motion lays each place at once.

## Order of building, and what each part must not do

- A part changes only its files; a part that finds it must change another's says so in its report and does not.
- Wave 1 (A, B, C) is merged before D starts (D moves what A touched; B gives D the die's right face). E1 runs beside D.
  E2 after D and E1; F beside E2; G last.
- No part changes `docs/decisions.md`; a part that finds the decision wrong says so in its report.
- Each part: its tests and the critical tests (`tests/test_architecture.py`, `tests/test_board_alone.py`,
  `tests/test_updates.py`) green before it is merged.
