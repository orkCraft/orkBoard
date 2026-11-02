# 128. The Orkmaster's column on every tab, a goal picked at every leader, one way to talk to a leader, the + card turned where it lies, runes of 25

Decisions §206 (1–12). **Builds:** the cheaper model, part by part, the spec's author reviewing and merging · **Review:**
the critical tests and each part's own · P1. The look is `docs/mockups/goal-card/` (the window played, the seal, the
runes): a part copies what it shows, not its code (the mockup is plain JS on orkUI's classes; the page is Preact).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The + card turned where it lies** | the field grows from the + card, foot under the window's edge; the squares *Rune*, *To*, *Type*, *Files*; the seal's whole ring | `hand/pluscard.js`, `hand/fieldturn.js`, `hand/hand.css`, `hand/state.js`; a new `hand/fieldsquares.js` when pluscard.js would pass ~600 lines; `tests/test_hand_plus_browser.py` (or the file that tests the + card today) |
| **B. The Orkmaster's column** | the pinned column, its head the Orkmaster's tab, the three piles, the moves between them; the tabs the leaders' only | `frame/frame.js`, `frame/frame.css`, `table/tabs.js`, `table/pane.js`, `table/table.js`, `table/card.js`, `table/backcard.js`; new `table/column.js`, `table/column.css`, `table/piles.js`; its browser test new |
| **C. Questions and failures as flights; the night to the discard** | a question flies from its goal to the hand and back; a failure red, thrown to the hand, a place left; the night's goals done to the discard under a moon; the morning's card gone | `hand/stacks.js`, `hand/motion.js`, `table/flight.js`, `table/discard.js`, `hand/nightcard.js`, `hand/hand.js`; their browser tests |
| **D. Passing a question on** | a leader's question marked for whom; one another leader can answer goes through the Orkmaster and back; the snapshot's rows for it | `core/` (the Talk's and a task's questions: `idea_questions`, the keeper's mixin that asks), `realm/board_map.py` (a row `passing`), `gui/ideas*.py` (`ideas.pass_take`, `ideas.pass_now`); `tests/test_pass_on.py` |
| **E. Make it a change** | the bubble's *Make it a change*: the leader's plan now and proposed, its cost, a decision in the hand; Design's three looks | `table/ask.js`, `core/` (a change asked of a leader: `ideas.change`), `hand/decisioncard.js`; `tests/test_make_change.py`, the bubble's browser test |
| **F. A goal picked at every leader** | the Orkmaster's tab: the goal's plan with arrows; a leader's tab: what it will change; the discard picked: what it changed against its spec; the die in its rune | `table/boardmap.js`, `table/maps.js`, `table/syspane.js`, `table/screensmap.js`, `table/discard.js`, `hand/playdie.js`; new `table/goalview.js`, `table/planarrows.js`; their browser tests |
| **G. Runes of 25** | a goal's rune a shape and a colour, unique across the project, shape first; drawn everywhere a rune is | `realm/idea_element.py` (`pick`, `give`, `hue`), the snapshot's `hue` beside `element`, `gui/static/js/orkui.js` (`Elem` takes `hue`), every `Elem` of a goal; `tests/test_idea_element.py`, a browser test |

**Order.** A, B, C, D and E are built side by side (their files do not meet). F after B (it draws in the pane B leaves);
G last (it touches every `Elem`). Each part merged into main as soon as its own tests and the critical ones are green.

## A. The + card turned where it lies

1. Pressed (or a key typed with nothing focused), **the + card itself turns over and grows**, from where it lies, to a
   card 5 : 7 about 2.8 times its width, its left edge on the + card's, its top so that about 330 px show above the
   window's edge (its foot goes under it): `fieldturn.js` `growFrom` animates a transform from the + card's box (a
   perspective turn of 180°, then the grow), and the + card is hidden while the field is open. Esc or a press away turns
   it back into the + card where it lay, keeping its words; *Send* turns it to its back and sends the back to the
   column's In analysis (B), or to the Orkmaster's lane until B is merged. Under reduced motion it appears and goes at
   once. The phone (under 760 px) keeps the field as wide as the screen, as today.
2. **The squares**: under the card's top a row of 44 × 44 squares, each with its caption under it (the label face):
   *Rune* (the goal's rune, as today's `RuneButton`), *To* (the addressed leader's head, the Orkmaster's crown when none),
   *Type* (the type's sign, faint when the party chooses it), *Files* (the file icon, the number of files attached at its
   corner). A square pressed opens its row of choices under it (one row open at a time, a radio group each, the arrows
   move in it, Esc closes the row first): the five runes (as today); the leaders' heads and the Orkmaster's crown with
   their names under them; the addressed party's types by their pictures (none and faint until a party is named:
   *Name a party to choose its type*); *From this computer* (a picture, as today's pictures) and the project's files
   (the mention list's files, `mention.js`). While a row is open the text gives it room, so *Send* stays above the edge.
3. **Words**: *Add a picture* goes; *Files* says plainly what it takes (*Pictures from this computer, or a file of the
   project*). An attached file is a chip in the row of *Send* (`fieldPhotos` for pictures; a project file as a mark, as
   *@* gives it today).
4. **The seal's ring is whole** on the + card while the runes are offered (`.is-choosing`): the free runes in their four
   places as today, and in the three others (135°, 225°, 315°) three of orkUI's own runes (`.ork-rune`, `eye`, `key`,
   `hourglass`) at three quarters, so the eight places are lit. Positions are layout (hand.css); no colour of its own.

## B. The Orkmaster's column

1. **The frame**: the column lies at the window's left, the table's height (the tabs' row and the pane), the canvas's
   colour (off the table, as the hand is), about 176 px wide; the table (tabs and pane) to its right with orkUI's
   `.ork-table` rim; the hand under both, as today. The frame's `--lanes` no longer counts the Orkmaster's lane. At the
   narrow width (under 760 px) there is no column: the phone keeps its own (upright.js), unchanged.
2. **Its head is the Orkmaster's tab**: the crown and *The Orkmaster*, a tab (`role="tab"`, `data-tab` the Orkmaster's),
   open at first, underlined when open. Its pane is the Board as today with nothing picked (every leader's lane: who
   does what), less the Orkmaster's own lane (its goals are in the column). The tabs at the top are the leaders' only
   (the Orkmaster's tab button goes from `tabs.js`); Release and Live stay in the portal ring's corners.
3. **Three piles**, from the snapshot's nodes (`mapData`), top to bottom:
   - **In analysis**: a goal not yet agreed: its state in `goal_route.LINE_STATES` less `decided` (raw, reading, asks,
     ready, planning, plan, routed, talk; `sketch` and `sections` are at work). Its card is **face down and sideways**
     (157 × 112: the seal, its rune at the seal's top, upright; **no name**). The pile is tight: the front card whole,
     the others 4 px edges each (at most three edges, then none). The front card is the goal the Orkmaster or its
     leaders are on (reading, routing, talk): its ring runs (orkUI's `ork-sigil-sweep` on the sigil's `::after`, the
     goal's colour; still under reduced motion). Under the pile's title: *writing: <short name>* (or *talked over:* while
     in Talk). A press on the pile lifts its list over the pane: each goal's rune and whole title in the Orkmaster's
     order, *Next* (moves it after the front, `ideas.reorder` as dragging does today) and *Remove* (as today's).
   - **To review**: `decided` with a wait running (`back.ripe`, not `held`, not the night's): face up and still, its foot
     its wait: the first's as a bar in eighths and its seconds or minutes (`backbody.js` `shareOf`, `leftWords`), the
     others the time they would start. It starts by itself (as today, §198).
   - **At work · later**: at work (a node with a task past waiting, or `sketch`/`sections`): face up, its rune glowing
     in its header and its foot, its leaders' heads at its foot (the parties of its tasks at work); then **put off**
     (`ripe.held`, or the night's: `start_at`/`queue` `night`): its foot *Held* or the moon and the night's hour.
   A pile shows its front card whole (112 × 157) and the foot of each card under it (20 px: its rune, its short name,
   its time or heads, its sign of state), at most three under it, then 4 px edges; no number. A card hovered or focused
   slides out of its pile whole (a transform; none under reduced motion).
4. **Moves**: a goal agreed: its card turns upright and face up where it lay (orkUI's `.ork-turn` after a quarter turn)
   and goes to To review; its wait over: it goes to At work and its tasks fly to their leaders' lanes (`flight.js`); a
   goal done goes to the discard (as today). A card's state on its foot: a yellow `question` sign while it waits for the
   person, a faint one while it asked another leader (D), the `alert` sign in danger while a task failed.
5. **Picking**: a face-up card pressed picks its goal (`picked`), as a stack does today; a face-down one cannot be picked
   (its press lifts the pile's list). A card of To review pressed also lifts *Start now*, *Later today*, *Tonight* (the
   wait's own commands: `ideas.ripe_now`, `ideas.hold`, the night's queue as today); a put-off card *Start now* and
   *Back to review*.
6. **Words**: the piles' titles *In analysis*, *To review*, *At work · later*; a card's label says its state and its
   goal's whole title (*Round timer on phones: its spec is ready; it starts by itself in 4 min*).

## C. Questions and failures as flights; the night to the discard

1. **A question for the person**: when a goal's task or Talk asks the person, the goal's card stays where it is (its
   lane's card, or its column card), its line yellow and still (`is-asks`), and each question's card is dealt into the
   hand **from that card** (a flight from its box: `flight.js`), not from the hand's edge. Answered, the question's card
   flies back into the goal's card and leaves the hand; when none is left the yellow goes.
2. **A failure**: a task failed (its checks red twice, as today) turns its card red (`fails`), and after a beat the card
   is thrown from where it lay into the hand (a flight with a turn), a dashed place (orkUI's `.ork-card-place`) left in
   its lane with *Back here on Start again* (the failure card's button, as it is named today). *Start again* flies it back to its place.
3. **The night**: the goals done in the night's window (`ideas.night`'s `goals` with `done`) go to the discard, each
   with a small moon on its card until its result is seen (§130.1); on the first look at the project after the night
   they are dealt into the discard one by one. A night's failure comes to the hand as a failure (2). The morning's card
   goes (`nightcard.js`'s stops are not dealt); its *Play it* moves to the discard picked (F).
4. Reduced motion: the cards appear in their places at once.

## D. Passing a question on

1. **A question says for whom**: a leader's question (Talk's or a task's) carries `for`: `person`, or a party's slug
   whose map or code answers it, or `""` (the leader does not know: the person). The prompts that ask for questions add:
   *for: "person" for what only the person can choose (the look, money, the direction, anything that cannot be undone);
   a party when its map or the code answers it*. A question about money, safety or anything that cannot be undone is the
   person's whatever its `for` says (code checks the words the rules already check for a paid task).
2. **Passed on**: a question for another party is not dealt to the hand: it waits `PASS_S` (10 s) in the snapshot's
   `passing` rows (`{id, idea, task, by, to, q, left_s}`), then the party it is for answers it in one call on the cheaper
   tier (reading only, its map and the code's summary, §181's limits), and the answer is given to the asking task or
   Talk as the person's would be, marked *answered by <party>* in its journal. `ideas.pass_take {id}` makes it the
   person's (dealt to the hand now); `ideas.pass_now {id}` passes it at once. A party that cannot answer (its answer says
   so, or the call fails) gives it to the person: one hop.
3. **On the page** (B's column): a passing question is a small card over the column's foot (its goal's rune, the two
   heads, the question, *passing on · 6 s*); pressed, *Answer it myself* and *Pass it now*. It flies to the answering
   leader's tab, the tab says *answering…*, and the answer flies back into the goal's card. The goal's card says
   *Asked Tech* (the `question` sign faint), not yellow.

## E. Make it a change

1. **The bubble** (`table/ask.js`): opened from the open tab's head as today, and also **from a part of a goal's change**
   (F) with that part as a mark (a chip, × takes it off). It is about what is picked: nothing (the project), a goal, a
   part. Its answer stays a read (§181.1). Under the answer: *Make it a goal* (as today: the + card opens with the
   words in it, addressed to the tab's party) when nothing or a goal done is picked; **Make it a change** when a goal
   agreed or at work is picked on a leader's tab.
2. **A change asked** (`ideas.change {idea, party, part?, text}`): the leader replans its part of the goal from the
   person's words (one call, as a plan's replan: its tasks not started; its spec's sections it owns), and the result is
   a decision row (`needs_you` kind `change`, existing) with `before` and `after` (its plan's tasks and its change's
   lines) and its estimated cost. Design's answer is three looks (its sketch's way: `sketchcard.js`'s choices) instead.
3. **The decision card** in the hand (`decisioncard.js`): lifted, *Now* and *Proposed* side by side, the cost, and
   *Accept* (the plan and the spec take it; written into the goal's decisions as the person's), *Talk more* (the bubble
   again, the part kept), *Keep the spec* (nothing changes). Design's: the three looks as cards, *Let Design decide*.

**As built.** The row is a kind of its own, `leader_change` (in `board_map.NEEDS`; kind `change` is the goal's plan change of spec 62, one a goal, with its own answers), kept in the goal's state folder
(`realm/leader_change.py`: `leader_changes.json`) and made by the party's leader (`core/idea_leader_change.py`: step `plan`, no tools, one call; its tasks not started by their role, its own *Will be* lines of the spec).
Commands: `ideas.change {idea, party, part?, text}` → `{ok, id}`; `ideas.change_take {idea, id, look?, decide?}` (the runner's `revise_tasks`, the party's *Will be* written, *The person decided …* in Decisions);
`ideas.change_keep {idea, id}`. The row: `{kind, id, task (= id), idea, goal = party, party, part, said, shape: plan | looks, status: ready | failed, text, why, before, after: {tasks: [{id, title, short, op}], lines}, looks:
[{key, name, why, lines}], usd_low, usd_high, error}`. Design's looks are three text looks (its sketch's pages are too heavy for one call here); each is its lines of the goal's *Will be*. The card is `hand/changecard.js`.

## F. A goal picked at every leader

1. **The Orkmaster's tab, a goal picked**: the Board shows that goal's tasks only (every other goal's are not drawn), in
   their leaders' lanes, planned ones faint, done ones grey, the one at work glowing; **arrows** from each task to the
   tasks that wait for it (its plan's `after`/`deps`), drawn in an SVG over the lanes (`planarrows.js`), a dashed arrow
   from a task done. A goal with no plan yet: *Its tasks are dealt to the leaders when it is agreed* in the lanes' place.
2. **A leader's tab, a goal agreed or at work picked**: the pane shows **what it will change**, not the map: its parts
   on this leader's map (the will-be map's parts the goal touches, §104), each a card with its name and *New*, *Changes*
   or *Read only* and its lines (*+* added, *~* changed, from the goal's will-be against the map now); Tech's contract
   lines as a diff; Design's screens *Now* → *Will be* with their states. Beside it: a small whole map with its parts lit,
   its *Done when*, its tasks at this leader. A part pressed opens this leader's bubble with it (E).
3. **The discard picked**: the same view, **what it changed against what its spec promised**: each part ✓ *As
   promised*, ≠ *Not quite* (with the leader's line), + *More than promised*, ✗ *Not done*, from the goal's result (its
   tasks' review and the folded living spec, spec 127 C), and its *Done when*, checked. The Play die (`playdie.js`) wears
   the goal's rune colour while a goal done or at work is picked, and its words say it (*Play: Lobby music*); pressed it
   plays dev opened at the goal's screen (`ideas.play {idea}`), and offers *As it was when it landed* (the goal's last
   merge commit) when the host can build it.
4. With nothing picked each tab is as today; Esc or the look bar's ✕ picks nothing.

**As built.** *The data.* The snapshot's tasks gain `party` (the leader whose work it is: the plan's step, `""` for a plan of before) and `step`; their `after` (the tasks one waits for) was there already, so no dependency was added. A new read `ideas.goal_result {idea}`
(`gui/ideas_goalview.py`, `realm/goal_result.py`, no model) judges a goal done against its spec: `{idea, state, files, screens, parties: [{party, title, parts: [{id, kind, verdict, line, note}], done_when: [{text, state}]}]}`. The promise is the party's section of the goal's page:
its *Will be* lines (`new|changed|gone <id>`) and *Done when*; what was done is read from the commits of dev the goal's tasks brought: **Tech** (the Architect's party) by the System's parts (a file's folder; a part inside a promised one touches it; the project's top touches only itself),
**Design** by the screens whose component changed (`goal_screens.of`, at most four), a screen named by its id, name or path. Verdicts: **ok** (*As promised*) the part was touched; **differs** (*Not quite*) its party's tasks all landed and nothing of the part changed; **missing** (*Not done*) not
touched and the tasks not all landed; **extra** (*More than promised*) touched and no line promised it (at most eight). A craft whose map the host does not read from files (Product, Game design, Art …) is judged by its tasks alone (all merged *As promised*, some *Not quite*, none *Not done*;
never *More than promised*). A *Done when* line is `ok` (✓) when the goal is done, its party's tasks all landed and no check task left a finding; otherwise it carries no mark. *F.1.* The Orkmaster's tab with a goal picked, at the wide width only (the column is pinned; the narrow Board keeps today's):
`table/planboard.js` draws the goal's tasks (not the dropped) in the lane of `t.party` (else the goal's own, else the first lane; Release and Live have none at the wide width), by wave then as written, each a task card in a `.plan-slot` that is faint while planned, grey when merged and whole at work (the
card's own flame); `table/planarrows.js` measures the slots and draws one SVG path a pair `after → task` (along the row to a lane at the right, left edge to right edge to one at the left, else foot to head), dashed from a merged task, `pointer-events: none`. No task yet: *Its tasks are dealt to the leaders when it is agreed* over the lanes.
*F.2.* A leader's tab with a goal `decided` … `working`, `failed` (`goalmap.js` `WILL_STATES`, the bubble's `AGREED` and a failure) picked: `table/goalview.js` takes the map's place under the leader's header. Its cards are the party's *Will be* lines (`ideas.page`, `specpage.js` `readSpec`): **New** is `new`, **Changes** is `changed`,
**Goes** is `gone` (a fourth word, for a part the leader removes), **Read only** is derived where the host reads the map (Tech's System by `ideas.system`, Design's screens by `ideas.screens` with their links): a part a promised one uses (Tech) or is linked to (Design) and no line names, at most four; a craft with no map shows only the lines.
A card's lines are its note under + / ~ / − (or *it is new*, *it changes*, *it goes*); the *Contract* diff (Tech) is the section's *Will be* lines, one a line, `+` `~` `-`; Design's card draws *Now* (the screen's picture, or *none* for a new one) → *Will be* (a wireframe: no picture of the screen to come exists). Beside it: the small whole map (Tech's parts by folder, Design's screens by step) with the
parts lit in the goal's element colour, a new part beside the map, the ones read only half-lit; *Done when*; the goal's tasks at this leader. A part pressed (or Enter, Space) calls `openAsk(<this tab>, {id, name})`. *F.3.* A press on a goal's row in the discard also **picks** it (`seeResult`; the Result opens as before, and the open tab stays): put away, each leader's tab
shows the same view as *what it changed against what its spec promised* (`data-view="changed"`): each part ✓ *As promised*, ≠ *Not quite*, + *More than promised*, ✗ *Not done* with the host's line, and *Done when, checked*. The Play die (`playdie.js`, `mana.css`) with a goal done or at work picked (`goalmap.js` `playable`: done, in At work · later, or a task running) carries `data-elem`, wears orkUI's
element token on its pips and edge (`--_pip`, `--_edge`), says *Play: <goal>* (`title`, `aria-label`) and pressed opens Play with `{idea}` (`ideas.play {idea}`). *F.4.* Esc (the shell's) and a × in the pane's title (`.table-title__unpick`, only while a goal is picked and nothing is open over the pane) pick nothing. **Not built:** *Design's states* (the host keeps no states of a screen
to come), *As it was when it landed* on the die (the host cannot build a goal's merge commit yet), a *Done when* line as unmet (only met is said), and a map of the other crafts (Product, Game design, Art, Release, Marketing): their view has cards and no small map. Tests: `tests/test_goal_result.py`, `tests/test_goal_view_browser.py`, `tests/test_plan_arrows_browser.py`.

## G. Runes of 25

1. `idea_element`: a goal has `element` (its shape, one of `ELEMENTS`) and `hue` (its colour, one of `ELEMENTS`);
   `give` picks among the project's open goals and its done goals not yet seen: the shape used least, then the hue used
   least among the goals of that shape, ties in `ELEMENTS`' order; a goal with an `element` and no `hue` has its element
   as its hue (every goal kept today keeps its look). A chosen rune (the field's) is the shape; its hue is picked.
2. The snapshot gives `hue` beside `element` on a node and wherever an element is given (`next_element` with
   `next_hue`, `free_elements` stay shapes). `Elem` (`orkui.js`) takes `hue` and draws the shape's mask in that colour
   (`background: var(--ork-elem-<hue>)`, orkUI's token); every `Elem` of a goal passes its `hue`. The + card's free runes
   stay shapes in their own colours.
3. A browser test: two goals of one shape and different hues are drawn in their hues; the first five goals given differ
   in shape.

## Tests and wording

Each part adds its tests beside the files it touches and keeps the critical ones green (`tests/test_architecture.py`,
`tests/test_board_alone.py`, `tests/test_updates.py`). The interface says *goal*, *party*, *leader*, *the Orkmaster*,
never *orc* (`tests/test_gui_wording.py`); Orkboard's sheets carry no colour, font or corner of their own
(`tests/test_design_system.py`). No module past ~600 lines.
