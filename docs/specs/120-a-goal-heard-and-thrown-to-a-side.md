# 120. A goal heard at the Orkmaster: Talk by itself, an agreed goal starts by itself, a dispute is a hearing thrown to a side

Decisions §198. The owner, 1 November: *the person presses the green card at the foot, and the field is a card, a big text in its
middle; the rune is given by itself, and only when the person wants another is there a way to change it. Sent, the card goes to
the Orkmaster's lane and the Orkmaster holds the debate with the leaders; show that it is being talked over, but at the least, so
it does not get in the way. Then two slices: either the leaders have questions, and they come to the hand as cards while the
spec's card stays at the Orkmaster; or the questions are closed and each leader says what it thinks of the goal. When all say
yes, nothing much is shown: the card lies a while at the Orkmaster, as if ready, and after a minute or ten minutes the work
begins, weighed by the goal's priority against its risks. When they disagree, a card in the middle and the leaders at its
sides with their phrases, and you swipe the card, as in Tinder on a phone, to the one whose arguments you take.* Three sides,
not four (the owner's pick); the decision of an agreed goal written by itself and marked so; Product's word needed for an
agreed goal to start by itself (the owner's three yeses). **Builds:** Claude (the cheaper model builds, the spec's author
reviews) · **Review:** full · P1. After spec 117 (the PWA loads the page: the phone's middle is the page's), spec 111 (the
rune chosen in the field), spec 108 (a leader's no).

The owner, then: *the green card is in truth a card's back: pressed, it turns over and grows into the big card of the text;
sent, it turns back, its rune lit, and goes face down to the Orkmaster; while it is talked over it lies face down, and its ring
of runes is the wait; when the wait ends it turns up and flies to its leader's lane; hovered or pressed while it is talked
over, it turns and shows what is on it.* And: *when a leader hands you a card, its question or the goal come back with an
error, today it vanishes from the leader and something appears in your hand: show who played which card, at the least.*

**What it is, and is not:** the way of a goal from the + card to its sections with **no press where the leaders agree**;
**one face for every disagreement**: a *hearing*, the goal's card in the middle and at most three sides around it, thrown by a
swipe, a drag, a key or a press; **one card through the goal's life** (its back while it is written to and talked over, its
face when it is read or played); and **every card the hand gets comes from where it was played**, the one who played it on it,
and goes back there when it is answered. Not: a debate between the leaders (a reply round: §9, later); a leader's proposals on its lens,
Product's summary of the table, an asset sheet for Art (§9, a spec of their own); a change of the plan's autostart
(`idea_risk.AUTOSTART` stays); the short way of a bug or a tidy (`ideas.route_start`, unchanged); a new pane, column or drawer
(§104.0, §145).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The mockup** | the card-field, the goal heard in the lane, the wait to start, a hearing at both widths and on the phone | new `docs/mockups/hearing/` (orkUI's sheets only); **the owner's yes before F** |
| **B. Talk by itself, heard as it goes** | the routed goal goes to Talk with no press; each leader's answer marked as it comes; Product heard on every goal | `gui/ideas_route.py`, `core/idea_talk.py` (`_hear` marks `heard`; `idea_talk.py` stays under 600 lines: the new work is in C's module), `realm/idea_questions.py` (`heard`); `tests/test_gui_route.py` (or where `ideas.add` is tested), `tests/test_idea_talk.py` |
| **C. The verdicts after the answers, the weigher, the wait** | the leaders who were not *go* judge again after the answers; Product weighs a goal it is not routed on; priority and risk read from the verdicts; the wait to start and its end | new `core/idea_verdict.py` (a mixin of `IdeaKeeper`, as `idea_talk.py` is), new `realm/idea_ripe.py`, `realm/idea_talk_parse.py` (`priority`, `risk`), `core/idea_decide.py` (`confirm(by="leaders")`), `gui/ideas.py` (`tick` calls `ripe_tick`: one line), `realm/idea_target.py` (step `talk_verdict`), `realm/event_log.py`; new `tests/test_idea_verdict.py`, new `tests/test_idea_ripe.py`, `tests/test_idea_decide.py` |
| **D. The hearing, faceless** | the sides of a Talk's disagreement and of a fork, the throw and what it does | new `realm/idea_hearing.py`, `realm/idea_objections.py` (its rows become one `hearing` row), `realm/board_map.py`, new `gui/ideas_hearing.py` (`ideas.hearing`, `ideas.throw`, `ideas.ripe_hold`; wired in `gui/ideas.py`'s table), `realm/lexicon.py`; new `tests/test_idea_hearing.py`, `tests/test_gui_hearing.py` |
| **E. The leader's call, measured first** | the cache of a leader's call measured; then, only when the numbers say so, a staggered start and the map in the system prompt | `realm/call_log.py` (`talk_floor`), `core/idea_talk.py` (`_hear`'s start), `realm/harness_claude.py` (`--append-system-prompt` when `cli_has`); `tests/test_call_log.py`, `tests/test_harnesses.py`, `tests/test_idea_talk.py` |
| **G. orkUI: the turn and the slow seal** | a card's two sides and its turn; the seal's rite slowed to a wait, held at a share; a card handed from a place and played back to it | repository orkCraft/orkUI (`.ork-turn`: a card's face and back and the turn between them; `.ork-sigil.is-waiting` with `--ork-sigil-share`; `.ork-gives`: a head's one beat as it plays a card; `.ork-deal` and `.ork-play` reused with their origins), then copied here (`python -m orkboard.design.orkui <orkUI>`). **Until it is copied** the faces draw what orkUI has (§6.11) |
| **F. The faces** | the card's life (the + back, its face, its back at the Orkmaster, the seal as the wait, the turn and the flight to its lane); the hearing (swipe, drag, keys, presses); the cards handed and played back, on the desktop and the phone | `js/hand/pluscard.js`, new `js/hand/hearing.js`, new `js/hand/hearing.css`, `js/hand/objectioncard.js` and `js/hand/forkcard.js` (their lifted face is the hearing), `js/table/card.js` (the goal's back, its turn, the wait), `js/hand/decisioncard.js` (*Hold*), `js/hand/motion.js` (`fromWhere`, `useHanded`, `playBack`), `js/hand/stacks.js` and `js/hand/hand.css` (a dealt card's place of origin), `js/hand/uptop.js` (the phone's crown as a place of origin); `tests/test_design_system.py` (`SHEETS`), new `tests/test_hearing_browser.py`, new `tests/test_card_life_browser.py`, new `tests/test_handed_browser.py` |

## 0. What is there today

- **The + card** (`hand/pluscard.js`, §187.3): pressed, it grows into one field over the hand, *Write a goal…*; the rune is given
  by rule (`next_element`, the least used among the addressed party's open goals) and may be chosen in a row of five radios.
- **The route card** (`hand/routecard.js`, §138.2, §147.2): the goal's first card, a stop: its route, its cost and **Talk**
  (**Later, by itself** when the limits run low). Nothing is asked of a model until it is pressed.
- **Talk** (`core/idea_talk.py`, spec 99 §5, spec 108 §4): one call a leader of the route, at once, on the cheaper tier, no file
  read. Each answers its stance, for, against, a **verdict** (`go` · `doubt` · `no`, why, `instead`, `after`) and at most three
  questions; the three cards are picked by rule. A second round only for questions a leader said it might need. The verdicts
  are given **before** the person's answers and are never asked again.
- **A no** is a Needs you row of its own (`objection`, `realm/idea_objections.py`, `hand/objectioncard.js`): *Drop the goal*,
  *Do the smaller one*, *Not now*, *Go on anyway*. A doubt is said on the decision's card.
- **The decision** (`core/idea_decide.py`, `hand/decisioncard.js`, §147.3): the Orkmaster words it; one button, **Confirm and
  start**, writes it to the decisions file, commits it to dev, and the leaders write their sections.
- **A fork** (`core/idea_sections.py`, `hand/forkcard.js`): what two sections disagree on; lifted, its sides are dealt as cards
  over the pane (`choose.js`), a press answers, *Other…* takes the person's words.
- **The plan starts by itself** by risk and priority (`gui/ideas_board.py` `autostart`, `realm/idea_risk.py` `AUTOSTART`):
  low risk starts at high and normal priority, medium only at high, high never.
- **Product** is heard only when the goal's types name its party (`realm/goal_route.py`).
- **The phone** (§195): the goal's top card lies in the middle with its answers, answered with one tap; *the arrows and the
  swipe go* (§195.4); never a swipe from the screen's edge (§195.1).
- **The motion** (§149.1, `hand/motion.js`, orkUI's `.ork-deal`, `.ork-play`, `.ork-crumble`): a card that comes to the hand is
  dealt **from just under its place** (`hand.css`: `--ork-deal-y` a share of the card's height, `--ork-deal-x` 0), so it seems
  to rise out of the hand, wherever it came from; a card that goes crumbles where it lay, an answered one too. orkUI's
  `.ork-deal` already reads `--ork-deal-x/-y` and `.ork-play` `--ork-play-x/-y`: where a card comes from and goes to is the
  page's to say. orkUI has a card's back (`.ork-card-back`, its seal at the centre) and the + card wears it; it has no turn.
- **The goal's own card** in the Orkmaster's lane (§187.1) is face up while it is read, routed and joined, its header the goal's.

## 1. The words

New in `TERMS` (D): **hearing** / **hearings** (*the goal's card in the middle and the sides its leaders argue, thrown to the
one the person takes*; not *fork*, which stays the word for two sections that disagree, nor *council*, the Review board's).
The interface:
- The card-field: *Write a goal…* (as today), the rune's `aria-label` *Its rune: Rune 3, change it*, **Send**.
- The goal heard, in the lane: its route's heads, the card's `aria-label` *<goal>: the leaders are talking it over* · *<n> of
  <m> leaders have said*; a press turns it, *Turn it back* on its face.
- A card handed: its label row *From <Leader>* (the Orkmaster's: *From the Orkmaster*), for a screen reader *<Leader> hands
  you <what>* said once, politely (`aria-live`), when it lands.
- The wait: *Starts by itself in 4 min* (under a minute: *in 40 s*), **Hold** on the lifted card; held: *Held: start it when
  you are ready* and **Start**; *All the leaders agreed* on the card's back above the decision.
- The hearing: its title *<Leader> and <Leader> disagree* (one leader: *<Leader> says no*); a side's line is its leader's own
  words, its foot the outcome: *Do it* · *Drop it* · *Do the smaller one: <instead>* · *After <goal>* · for a fork, the side's
  *says*; the middle's foot *Or say it in your own words*; the hint once a device (`localStorage`, a convenience only):
  *Swipe the card to the side you take, or press it*. After a throw a toast: *Thrown to <Leader>: <outcome>* with **Undo**
  (a drop: *Dropped. Undo*).
- The decision file's heading of an agreed goal: `## <n>. <title> (<date>, the leaders, all agreed; <host>)`.

## 2. Part B: Talk by itself, heard as it goes

1. **`ideas.add` of a routed goal goes to Talk by itself** (`gui/ideas_route.py`): the goal is `routed` as today, then, in
   the same command, `ideas.talk` is made for it **when** the keeper may run (`_may_run`), the window is not spent, the week's
   limits are not low (§147.4) and the route spends nothing paid (spec 105's *Go on paid?*). Otherwise the route card is dealt
   as today, with its reason (this changes §138.2: the route card comes first only when the goal cannot go on by itself). A
   goal of the short way (`short`) keeps its route card (*Start* or *Talk*: a bug's way is the person's choice).
2. **The route stays editable while Talk runs**: the goal's card in the lane, lifted, shows the route's heads with their × and
   **+** (the route card's `RouteLifted`, reused). A party added is heard alone (one call); a party taken off has its answer and
   its cards dropped. An edit once Talk is done is as today (a `start` row).
3. **Heard as it goes**: `_hear` writes each leader's party into the Talk's record (`idea_questions.record` `heard: [party]`) as
   its answer is parsed, and publishes the goal. Nothing else of the answer is shown before the round is whole.
4. **Product weighs every goal** (§198.4): when the project has a party whose craft is Product and the route does not name it,
   the round calls Product's leader too, as a **weigher**: its verdict, why, `instead`, `after` and `priority` only (no
   questions, no project questions, no section later); it is not on the route, its call is in the route's cost (one
   `talk_round`). A bug, a tidy, a balance pass (the short way) have no weigher.

## 3. Part C: the verdicts after the answers, the weigher, the wait

1. **Two new fields in a round's answer** (`idea_talk_parse.clean_round`): Product's leader (route or weigher) gives
   `priority` (`high` · `normal` · `low`: how this goal stands against the goals in line, which it is given); Tech's leader gives
   `risk` (`low` · `medium` · `high`: what the change may break, by its map and its concerns). Others give neither; a value out of
   the set is dropped. The round's prompt names them in one rule each, with the JSON.
2. **The verdicts after the answers** (`core/idea_verdict.py`, step **`talk_verdict`**, the cheaper tier, no tools, READS 0, as
   `talk_round`): when the person has answered the cards, the leaders whose verdict was `doubt` or `no`, and those whose own
   question was answered otherwise than their `pick`, are heard again, at once, one call each, given the goal, their first
   answer and the answers: `{"verdict", "why", "instead", "after", "priority"?, "risk"?}`. The others' verdicts stand. When no
   card was asked, nobody is heard again. It runs before the second round's questions are dealt when there is one (a leader in
   both is heard once, the second round's prompt asking its verdict too).
3. **The goal's weight** (`realm/idea_ripe.py`, no face, no model): `weight(stances, how)` → `{priority, risk}`: priority is
   Product's (none: `normal`); risk is `idea_risk.assess(touches=how.touched, texts=[the gist, Tech's against], risk_model=Tech's
   risk or "low").risk`, so the rules no model talks down (secrets, data, CI, a public API, wide) still raise it.
4. **What the verdicts make** (`idea_ripe.outcome(rec, has_product)`):
   - **any `no` or `doubt`** → a **hearing** (§4) in the hand; the decision waits for its throw;
   - **all `go`, with Product's word** (Product on the route or weighing; a project with no Product party: risk `low` only) →
     the decision's call is made as today (step `decide`), then **the wait** (§3.5);
   - **all `go` and no Product's word possible** (a project with no Product party, risk above `low`) → the decision's card as
     today, *Confirm and start*.
5. **The wait** (`idea_ripe.wait_s(priority, risk)`): `idea_risk.decide(risk, priority)` says `start` or `night` → **60 s** for
   high priority at low risk, **600 s** otherwise; `wait` → **no wait**: the decision's card as today. Kept in `way.json`
   (`spec_sections.record`) as `ripe: {left_s, risk, priority, held: false, by: ""}`.
   - **It runs only while a face is open** (the host's `server.clients` is not empty, through the host): `ripe_tick(dt)` takes
     `dt` from `left_s` each `tick` of `gui/ideas.py`; with no face open the time left is kept, so a goal never starts unseen.
   - **At its end** `confirm(slug, by="leaders")`: the entry written as §1's heading says, its points the leaders' stances (*For
     <Leader>: <for>*) and the Orkmaster's words; committed to dev as every decision is; then the sections, as *Confirm and
     start* goes on. The plan's own autostart after the sections is unchanged (`AUTOSTART`).
   - **Hold** (`ideas.ripe_hold {idea}`): `held: true`, the time gone; the decision's card is the goal's top card with
     *Start* (`ideas.confirm`, `by` the person, as today). Opening the card, reading it, or answering another card does not hold it.
   - A spent window or a Stop all at the end: the goal waits held, with why (`refuse_spent`'s words), never started on paid.
6. **Events**: `talk_heard {idea, party, weigher}`, `talk_verdict {idea, party, before, after}`, `ripe_started {idea, seconds,
   priority, risk}`, `ripe_held {idea, left_s}`, `ripe_done {idea}`. After a week (the owner reads them): the share of agreed goals
   held (most held: the waits are too short), and the verdicts changed after the answers.

## 4. Part D: the hearing, faceless

1. **Sides of a Talk** (`idea_hearing.of_talk(rec, name_of)` → `{moment: "talk", title, sides: [...], own: true}`), **at most
   three**, each `{dir, kind, leaders: [party], line, outcome}`, `line` the first leader's `why` (a `go` side: its `for`), the
   other leaders of the side named after it (*and <Leader>*):
   - **`go`** (*Do it*): the leaders who said `go`; with none, the side stands alone, *Go on anyway*, no head;
   - **`drop`** (*Drop it*): a `no` with neither `instead` nor `after`;
   - **`smaller`** (*Do the smaller one*): the first `instead` in the route's order (a no's before a doubt's);
   - **`later`** (*After <goal>*): the first `after` (Product's).
   `go` is always **right** (→). **Left** (←) takes the first of `drop`, `later`; **up** (↑) the next of `smaller`, `later`,
   `drop`. A kind with no leader is no side; a doubt with neither `instead` nor `after` adds its leader's words to `go`'s side
   (*doubts: <why>*), as the decision says a doubt today. More kinds than three: the last in that order is left out and its
   leaders' words go to the decision.
2. **Sides of a fork** (`idea_hearing.of_fork(fork)`): its sides in their order, → ← ↑, at most three (a fourth: the fork's
   `about` says it, the person's own words answer it); `kind: "side"`, `line` the side's `why`, `outcome` its `says`.
3. **The throw** (`ideas.throw {idea, moment, dir | text}`, `gui/ideas_hearing.py`): Talk's — `go` → `confirm` (by the person;
   the overruled named, as spec 108 §4.4) and the sections; `drop` → `ideas.drop`; `smaller` → the goal's words become `instead`
   (`idea_objections.reword`), then `confirm`; `later` → `waits_on` the goal named, as *Not now* does; `text` → `confirm` with the
   person's words kept as written (`confirm(text=)`). A fork's → `fork_answer(side=)` or `fork_answer(text=)`. A throw of a
   hearing no longer open is refused in plain words (*This was decided already*).
4. **The rows**: `idea_objections.open_rows` gives one row `{kind: "hearing", idea, moment: "talk", ...}` a goal in place of a
   row a no (the decision waits while it is open); a fork's row stays `fork` and its lifted face is the hearing. A doubt is no
   longer only on the decision's card: it is a side or a line of one.
5. `ideas.hearing {idea}` → the open hearing of the goal (Talk's first, else its first open fork), `null` with none.

## 5. Part E: the leader's call, measured first

1. **Measured** (`call_log.talk_floor(lines)`; `python -m orkboard.realm.call_log talk <project>`): of the `talk_round` lines
   of the last 7 days, grouped by goal, each call's `cache_creation_input_tokens` and `cache_read_input_tokens` and its place
   (first or not) in its round. It answers two questions: does each parallel call write the shared prefix again (the calls after
   the first show creation, not reads), and is the map read from a cache between two calls of one leader at one head of dev.
   The owner runs it on their game; the numbers go into this spec's *As built*.
2. **Only when the first holds**: `_hear` submits the route's first leader, waits `STAGGER_S` (4 s) or its end, then the rest.
3. **Only when the second fails**: a leader's voice, its map's text and its rubric go in `--append-system-prompt` (when the
   installed CLI lists it, `cli_has`), the goal's words and the answers in `-p`, so the map is read from the cache by the
   leader's next call at the same head (`map_text`'s claim, §156.2, made true). Measured again after a day on it.

## 6. Part F: the faces

**The card's life** (§6.1–§6.3): one card, its back and its face. **The + card is a card's back** (it wears `.ork-card-back`
already): the seal at its centre, the + its sign. A goal's back is the same back, told apart from the + card and from the
other goals' backs: **its own rune lit** at the seal's top in its colour (the + card's holds the rune it *would* give, at a
quarter's strength), **its short name** at the back's foot in the body face (two lines at most), **no +**; the + card alone
keeps the green. In a card game face down is *not played yet*: that is what Talk is.

1. **The card-field** (`pluscard.js`): pressed, the + card **turns over and grows** into **a card** over the pane's middle (5:7
   at the wide width, the screen's width less the gutters on the phone), in one motion (the turn, the growth and the travel
   from its place at the lane's end: a FLIP, about 360 ms, orkUI's `.ork-turn`). Its face: its rune large at its top left where
   a card's element stands, *Write a goal…* its body, the text the person's (never the pixel face), **Send** at its foot, the
   party's address (*→ Tech ×*) and the chips of *@* as today. **The text field takes the focus in the press itself**, before
   the motion (on iOS a keyboard rises only for a focus given inside the press: given after the motion, the field opens with no
   keyboard). **A press on the rune** opens the five runes in a row under it (40 px each, as §187.3's); doing nothing keeps the
   rule. Esc or a press away turns it back into the + card where it lay, its text and rune kept. Under reduced motion: no turn
   and no growth, the card is there.
2. **Sent: it turns back and goes face down to the Orkmaster.** On **Send** the face turns to its back, the seal plays the rite
   from the goal's rune (§187.4, as today), and the back shrinks and travels to its place in the Orkmaster's lane (`.ork-play`
   with `--ork-play-x/-y` to that place). A new + card is dealt at the lane's end (its rune the next goal's).
3. **Talked over, face down** (`table/card.js`, the goal's own card in the Orkmaster's lane, §187.1, while Talk and the verdicts
   after the answers run): its back, **the rune at the seal's top glowing** (orkUI's `.is-glowing`, §187.2's flame, counted among
   them), and under the card its route's heads small (16 px), faint until `heard` names them, then in full: never on the ring,
   so the ring has one meaning at a time. No verdict, no tick, no count is drawn (§145.3). The questions are the hand's cards
   (§6.9); the goal's card stays in the lane, face down.
   - **To look at it**: hovered, the card only **lifts and leans** (orkUI's `.ork-leans`, its corner raised, as a hand lifts a
     card to peek under it): a pointer crossing the lane turns nothing. **Pressed** (or Enter on it), it **turns over** in place
     and is lifted: its face says its words, its route (the route card's `RouteLifted`, so the route is edited here, §2.2), what
     each leader that has said said (*stance*, a line each), its cost. A press away or *Turn it back* turns it face down again.
     On the phone the goal picked in the middle is its face; the menu's row shows the back's rune glowing.
4. **The wait** (the same back): the rune stands lit, still, and **the seal's own ring of runes is the wait**: it fills clockwise
   from the rune, in the goal's colour, in eight steps over the wait (the rite of §187.4, slowed: orkUI's `.ork-sigil.is-waiting`,
   its share `--ork-sigil-share` set by the page from `ripe.left_s`), and stands where it is while the wait is held or no face is
   open. Under the card: *Starts by itself in 4 min*. Pressed: it turns; its face holds the decision's words, *All the leaders
   agreed*, **Hold**. Under reduced motion the ring is drawn at its share and does not move between steps.
5. **The wait's end: it turns up, then flies to its lane.** The ring closed, the back **turns face up** where it lies (the goal's
   header, its rune, its name), a beat (orkUI's base motion), then **flies** to its place in the lane of the route's first
   party (`.ork-play`), where its stack begins. One card flies at a time: a second goal whose wait ends meanwhile waits for the
   first to land. Not seen (the page hidden, another tab picked with the lane out of view): no flight, the card is in its lane
   (§89.0: a motion plays once, never for what changed unseen). On the phone: it turns face up in the middle if it is picked, and
   its row moves under its party in the menu; nothing flies.
6. **A hearing turns it up in the middle**: the face-down card leaves the lane, turns face up and lies in the hearing's middle
   (§6.7); thrown, it flies to the side, then to where the side sends it (*Do it*: the first party's lane at the sections' end;
   *Drop it*: the discard, §176; *After <goal>*: back to the Orkmaster's lane, face down; *the smaller one*: back to the lane, its
   words changed, face down).
7. **The hearing** (new `hearing.js`, `hearing.css`; the lifted face of a `hearing` and of a `fork` row; opened over the pane as
   a fork's sides are, `openOver`): the goal's card in the middle (its rune, its name, *Done when* when the sections are
   written, else its gist); its sides at the right, the left and the top, each its leaders' heads (the leader's at 28 px,
   the others 16 px), its line in the body face, its outcome at its foot; the middle's foot *Or say it in your own words*.
   - **Swipe or drag**: the card follows the pointer (`setPointerCapture`, `touch-action: none` on the card alone, so the page
     scrolls elsewhere), turns a few degrees toward the side it nears, and that side grows and its outcome is stamped on the
     card. Let go past a third of the way (or flung): thrown; short of it: back. Down is no side: the card comes back. A gesture
     starts only on the card, never at the screen's edge (§195.1).
   - **A press on a side** throws it (§195.2's one tap); **keys**: → ← ↑ throw, Enter on the middle opens the field for the
     person's words. Every side is a button with its outcome in its `aria-label`.
   - **The throw** flies the card off to the side (none under reduced motion), the toast says it with **Undo**; a drop is sent
     only when the toast goes (6 s), Undo before then sends nothing; the other throws are sent at once, Undo takes the hearing
     back while the next call has not begun.
   - **The phone** (the page in the PWA, §195): the hearing is the goal's top card in the middle; thrown, the next goal with a
     card is picked (§195.2's), so a morning of hearings is gone through as a deck. A side's line wraps to three lines and
     opens whole on a press of its *More*.
8. **The decision's card** keeps *Confirm and start* for a goal with no wait; a held goal's says **Start**.

**The cards handed** (§6.9–§6.10): today a card leaves a leader and appears in the hand as two things that do not touch, so
who played what is a guess. A card is now **handed from where it was played and played back there when it is answered**, at
the least motion that says it: one small *give* at the origin, one flight, no turn.

9. **Handed from where it was played** (`motion.js` `fromWhere(row)` → a box on the page, or none; `useHanded` in place of
   `useDealt` for the hand's cards):
   - **The origin**, the first in view of: the goal's own card or stack on the table (`[data-goal=<idea>]`: the face-down
     back at the Orkmaster for Talk's questions, a hearing, the decision, a fork; the stack's front card in its party's lane for
     a stage's stop: a result to review, a failure, a member's question its leader passes on, a goal ready for main); else the
     leader's tab (`[data-tab=<party>]`; the Orkmaster's tab for the Orkmaster's cards); else, on the phone, the goal picked in
     the middle when it is the card's goal, else **the crown** (the menu of the leaders lives there, §195.1). A card of no goal
     and no party (an update, *Go on paid?*) is dealt from under its place, as today.
   - **The give**: the head of who plays it (its head under the face-down card, or on the tab, or the crown) rises one step and
     settles (orkUI's `.ork-gives`, one beat of the base motion); the goal's card leans toward the hand as it lets the card go.
   - **The flight**: the card is dealt from the origin's centre to its place in the hand (orkUI's `.ork-deal` with
     `--ork-deal-x/-y` the origin less the place, set by the page), face up, starting at the origin's size and ending at its
     own, **its asker's head already in its window**, so who played it is seen in the air; its label row says **From <Leader>**
     and keeps saying it. A goal that comes to the hand itself (its row is the goal: a result back with an error, a goal ready
     for main) leaves its lane as a whole (`.ork-play` to its place in the hand) and the lane closes behind it.
   - **Several at once** (Talk's three questions): one after another, orkUI's deal gap apart, in the route's order; at most
     three fly, the others are dealt from under their place. **Never while a pointer is down** in the hand (the no lost tap of
     spec 50 §6.9: they wait for it to come up), **never for what came while the page was hidden** (§89.0: on coming back the
     cards are there, each saying *From <Leader>*), never under reduced motion (the card is there, the origin's head drawn in
     full for a moment instead of rising).
   - **On the phone** the hand's row scrolls sideways: a card that lands out of its view moves no scroll; the row's cue at its
     edge (`scrollcue.js`) brightens once.
10. **Played back where it came from**: a card answered (a question's pick, the decision confirmed, a fork's side, a stop's
    answer) **flies back to its origin** (`playBack`: `.ork-play` with `--ork-play-x/-y` toward it) and is taken into it, and the
    head that asked is drawn in full there (it has its answer); with no origin in view it goes as it does today. **A card dropped
    or dismissed crumbles where it lay** (`.ork-crumble`, as today): flying back means *answered*, crumbling means *gone*, so the
    two never read alike. A hearing's throw is §6.6's.
11. **Until orkUI's pieces are copied** (G): the turn is the back and the face crossfading in place; the slow seal is the words
    alone, the rune lit; the give is nothing; the flights use `.ork-deal` and `.ork-play`, which orkUI has, with the origins set.

## 7. Order and tests

A and G first (G in orkUI, drawn on A's yes); B, D and E at once (they share no file but `gui/ideas.py`'s table of commands, which D alone touches); C after B; F
after A's yes, against C's and D's shapes with its stub host, and drawing what orkUI has until G is copied (§6.11). Each keeps the critical tests green (`tests/test_architecture.py`,
`tests/test_board_alone.py`, `tests/test_updates.py`) and its modules' tests. B: a routed goal goes to Talk by itself and keeps
its route card when the keeper may not run, the limits are low or the route is paid; a short way keeps its card; `heard` as
each answers; Product weighs a goal it is not routed on, asks nothing and writes no section. C: `priority` and `risk` parsed
and dropped out of their sets; who is heard after the answers (a doubt, a no, a pick overridden; nobody when no card); the
weight raised by `idea_risk`'s rules; each outcome of §3.4; the wait's seconds; time kept with no face open; Hold; the end
writing the heading of §1 and starting the sections; a spent window holding. D: the sides of every mix of verdicts (all
no, one leader, a doubt with and without `instead`, more kinds than three), of a fork of two, three and four sides; each
throw doing what it says; a late throw refused; one row a goal. E: the floor's grouping on recorded lines; the stagger and
the system prompt only behind their switches. F: the field as a card with its rune changed by a press; the heads lit as
`heard` grows; the ring's words; a hearing at both widths and on a phone-sized page: a swipe past and short of a third, a
press, the keys, Undo of a drop sending nothing, no sideways scroll, nothing moving under reduced motion. The card's life: the + card
turned into the field with the field focused in the press; Send turning it back and its back in the Orkmaster's lane, its rune lit
and its name at its foot, never green; hover lifting and not turning, a press turning; the seal's share following `left_s`; the
wait's end turning it up and one flight at a time; nothing flying for a hidden page. The cards handed: the origin found in its
order (the goal's card, the leader's tab, the crown, none); `--ork-deal-x/-y` set from it; *From <Leader>* on the card; three
flights at most; none while a pointer is down; an answered card played back to its origin, a dropped one crumbling.

## 8. What it changes

§138.2 (the route card comes first: now only when the goal cannot go on by itself), §147.3 (the decision's one button: an agreed
goal confirms itself at the wait's end, its heading saying so), §118.1 (the person confirms the decision: except an agreed
goal's), §183.3 (a no's card: now one hearing a goal, its sides), §195.4 (the swipe goes: it comes back on a hearing's card
only), §149.1 (a card that comes is dealt from under its place: now from where it was played; an answered card crumbles: now
it is played back), §187.1 (the goal's own card face up while it is read: face down while it is talked over), §187.3 (the rune
chosen in a field over the hand: now on the card's face, by a press on the rune).

## 9. Later (not here)

- **A reply round**: on a disagreement, each leader given the others' verdicts and answering in a line (*keeps* or *changes*),
  so the hearing's lines answer each other.
- **A leader's offers on its lens**: a third level beside alert and note, a ghost on its map, with the job of Product's tree it
  serves; taken, a goal whose author's Talk is already `go`.
- **Product's summary of the table** (a line a party: its open alerts, Play's newest hints, what waits in line) in Product's
  calls; **Art's sheet** (one picture of the changed assets' thumbnails) in Art's look and Talk.
