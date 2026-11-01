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

**What it is, and is not:** the way of a goal from the + card to its sections with **no press where the leaders agree**, and
**one face for every disagreement**: a *hearing*, the goal's card in the middle and at most three sides around it, thrown by a
swipe, a drag, a key or a press. Not: a debate between the leaders (a reply round: §9, later); a leader's proposals on its lens,
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
| **F. The faces** | the card-field, the goal heard in the lane, the wait, the hearing (swipe, drag, keys, presses) on the desktop and the phone | `js/hand/pluscard.js`, new `js/hand/hearing.js`, new `js/hand/hearing.css`, `js/hand/objectioncard.js` and `js/hand/forkcard.js` (their lifted face is the hearing), `js/table/card.js` (the goal heard, the wait), `js/hand/decisioncard.js` (*Hold*); `tests/test_design_system.py` (`SHEETS`), new `tests/test_hearing_browser.py`, `tests/test_plus_card_browser.py` (or where the field is tested) |

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

## 1. The words

New in `TERMS` (D): **hearing** / **hearings** (*the goal's card in the middle and the sides its leaders argue, thrown to the
one the person takes*; not *fork*, which stays the word for two sections that disagree, nor *council*, the Review board's).
The interface:
- The card-field: *Write a goal…* (as today), the rune's `aria-label` *Its rune: Rune 3, change it*, **Send**.
- The goal heard, in the lane: its route's heads, the card's `aria-label` *The leaders are talking it over* · *<n> of <m>
  leaders have said*.
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

1. **The card-field** (`pluscard.js`): pressed, the + card grows into **a card** over the pane's middle (5:7 at the wide width,
   the screen's width less the gutters on the phone): its rune large at its top left where a card's element stands, *Write a
   goal…* its body, the text the person's (never the pixel face), **Send** at its foot, the party's address (*→ Tech ×*) and
   the chips of *@* as today. **A press on the rune** opens the five runes in a row under it (40 px each, as §187.3's); doing
   nothing keeps the rule. Enter sends, Esc keeps the text and the rune. The rite on send is §187.4's.
2. **The goal heard** (`table/card.js`, the goal's own card in the Orkmaster's lane, §187.1): while Talk runs (and the verdicts
   after the answers) its rune **glows** (orkUI's `.is-glowing`, §187.2's flame, counted among them) and under its name its
   route's heads stand small (16 px), faint until `heard` names them, then in full. No verdict, no tick, no count is drawn
   (§145.3). The questions are the hand's cards, as today; the goal's card stays in the lane.
3. **The wait** (the same card): the rune stands lit and a ring of orkUI's decorative runes around it fills clockwise, in the
   goal's colour, in eight steps over the wait (the rite's ring, §187.4, slowed); the label row says *Starts by itself in 4 min*.
   Lifted: the decision's words, *All the leaders agreed*, **Hold**. Under reduced motion no ring moves: the words alone.
   **Until orkUI draws the slow ring**, the card says the words and shows the rune lit, nothing more.
4. **The hearing** (new `hearing.js`, `hearing.css`; the lifted face of a `hearing` and of a `fork` row; opened over the pane as
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
5. **The decision's card** keeps *Confirm and start* for a goal with no wait; a held goal's says **Start**.

## 7. Order and tests

A first; B, D and E at once (they share no file but `gui/ideas.py`'s table of commands, which D alone touches); C after B; F
after A's yes, against C's and D's shapes with its stub host. Each keeps the critical tests green (`tests/test_architecture.py`,
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
press, the keys, Undo of a drop sending nothing, no sideways scroll, nothing moving under reduced motion.

## 8. What it changes

§138.2 (the route card comes first: now only when the goal cannot go on by itself), §147.3 (the decision's one button: an agreed
goal confirms itself at the wait's end, its heading saying so), §118.1 (the person confirms the decision: except an agreed
goal's), §183.3 (a no's card: now one hearing a goal, its sides), §195.4 (the swipe goes: it comes back on a hearing's card
only).

## 9. Later (not here)

- **A reply round**: on a disagreement, each leader given the others' verdicts and answering in a line (*keeps* or *changes*),
  so the hearing's lines answer each other.
- **A leader's offers on its lens**: a third level beside alert and note, a ghost on its map, with the job of Product's tree it
  serves; taken, a goal whose author's Talk is already `go`.
- **Product's summary of the table** (a line a party: its open alerts, Play's newest hints, what waits in line) in Product's
  calls; **Art's sheet** (one picture of the changed assets' thumbnails) in Art's look and Talk.
