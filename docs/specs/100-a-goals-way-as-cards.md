# Spec 100 — A goal's way as cards: the route card, Talk's questions, the decision, a fork, a bug's cause, the project's questions, the one place of the parties

The owner and the PM, 28 October (decisions §117, §118, §121.2, §133, §134.5, §136.2, §140, §147, §151.5, §153,
§156.6, §158.1–§158.3, §159, §160, §167; spec 95 §4.2, §5.2–§5.3, §6.3–§6.6; the mockup `docs/mockups/s2b/`). The faces of
spec 99's way, drawn on spec 98's frame (the table and the hand) with spec 99's Needs you rows. **Builds:** a cheaper
model, each part reviewed by Claude · **Review:** full · P0. **A, B and D at once** (they share no file), **C after B** (it deals a fork's sides with B's `hand/choose.js`);
**E after them**. Each hand part registers its row kinds' sign and lifted card with `hand/ways.js` `way(kind, …)` and each
page over the pane with `frame/kinds.js` `drawn(kind, …)` (`talk`, `spec`, `parties`, `choose`), from its own module (the stub
the lead wrote; `hand/wayparts.js`, `table/wayparts.js` load them). **Only after the owner's yes on the S2b mockup**, after spec 98 D and E (the hand and the window) and the spec 99
part each face reads (A: spec 99 C; B: D and G; C: E; D: A).

**Every card here wears spec 101's face** (decisions §167.1: the element at the left of its header, its name
left-aligned, a low window with its one sign and the asker's head in its corner, the label row with the gem at its
right) and **lies in the hand under the lane of who asks** (§167.7, spec 101 D); no deck (§167.5). After spec 101.

**What it is, and is not:** a card face and its lifted state for each new row (`route`, `start`, `talk`, `cause`,
`decision`, `fork`, `project_q`), a goal's stack of questions answered one card a press, the phase's page on the pane
(*Talk*'s stances, *Spec*'s sections and a fork's sides), the phase marks in the pane's title, the route's dots on the
tabs, and the one place of the parties over the pane in place of today's form. Not: the other maps and picking on them
(S3); a specialist's view (§151.4, S3); the phone's page (S5); *Start now* and the wait's card (S6).

| part | builds | files (and their tests) |
|---|---|---|
| **A. The route card** | §1 | new `static/js/hand/routecard.js`, new `static/js/hand/startcard.js`, new `static/js/hand/way.css`; new `tests/test_route_card_desktop_browser.py` |
| **B. Talk's questions** | §2, §5 | new `static/js/hand/choose.js` (*Choose a card* over the pane, kind `choose`: the banner, the choice cards, *Other…*, *Let … decide*; used by C), `static/js/hand/questioncard.js` (a question; a goal's stack of them; the project's stack), new `static/js/hand/causecard.js`, new `static/js/table/talkpage.js` (the stances on the pane), new `static/js/hand/questions.css`, `hand/data.js` (the `project_q` row's stack: a row of no goal's); new `tests/test_talk_desktop_browser.py` |
| **C. The decision and a fork** | §3 | new `static/js/hand/decisioncard.js`, new `static/js/hand/forkcard.js`, new `static/js/table/specpage.js` (the sections on the pane, a fork's sides lit), new `static/js/table/spec.css`; new `tests/test_decision_fork_desktop_browser.py` |
| **D. The one place of the parties** | §4 | new `static/js/table/parties.js`, `partyseats2.js` (the squad's columns), new `static/js/table/parties.css`; today's `shell/goalwizard.js`, `partyform.js`, `partyseats.js`, `partypresets.js`, `partysize.js`, `partydraft.js`, `partymodel.js` removed once nothing imports them (E); new `tests/test_parties_desktop_browser.py` |
| **E. The wiring** | §5, §6 | `static/js/hand/stopcard.js` (each new kind to its card), `static/js/frame/kinds.js` (`parties`, `talk`, `spec` over the pane), `static/js/table/pane.js` (the phase marks), `static/js/table/tabs.js` (the route's dots), the removed party form's modules; `tests/test_hand_desktop_browser.py`, `tests/test_table_desktop_browser.py` |

## 0. The words
*Talk*, *Spec*, *Work*, *Done* (the phase marks); *Talk*, *Later, by itself*, *Start*, *The long way*; *<Party> alone:
finding the cause*; *<Party> alone: the report has a failing test*; *about n calls, about n% of <tool>'s week*; *n-th in
line*; *Other…*; *Let <leader> decide*; *Yes*, *No, it's elsewhere*; *Confirm and start*; *Decision <n>*; *<A> and <B>
disagree*; *Pick an answer: the leader writes it into the spec* (once, under the first card with answers; on the
project's questions *the leader keeps it for the project*); *Read from the project: <kind>*; *The project is here*;
*the one way into main*; *Lean*, *Standard*, *Full* and each one's line; *Does*, *Checks*; *These parties: about n% of
<tool>'s week a goal*; *Start* (the first time), *Save*. No word of a race but the leaders' names of §164 (*Angel Invest Knight*, *Dungeon Master Knight*, *Sh.man*, *Pixel-Perfect
Dryad*, *Sprite Dryad*, *Uptime Imp*, *Event Imp*, *Growth Hack Gnome*, *Release Night King*), said only on the leader's
row of the one place of the parties; elsewhere a party says its name, a seat its role.

## 1. The route card (A; §133.1, §136.2, §140.2–§140.3, §147.4, §156.6, §158.2)
The `route` row is a card of the goal's stack under the first lane (spec 101 D): its face the goal's element and
name, the route's sign in its window with the Orkmaster's head in its corner, the gem of its cost in its label row. **Lifted**: the route as the leaders' heads in order with a small × at each one's corner (a press
on a head opens its popover, §140.2), a **+** offering the project's parties but Release (and the `offer`ed ones
first, *touches its map*), the route in words (*Game design, then Art, then Tech*), the cost (gem and words), its place
(*3rd in line*), and one act: **Talk** (with **Later, by itself** beside it only when `low`, laying the goal in the
first lane's *In line*, §167.5). An edit sends
`ideas.route_set`, the cost said again from the answer. **A bug**: *Tech alone: finding the cause* and **Talk**; when
`reproduces`, *Tech alone: the report has a failing test*, **Start** and *The long way* (a quiet link, `ideas.talk`).
The route's parties carry a dot on their tabs while the goal is picked (E). The **`start`** row: its card says the new
cost with the old one beside it, struck, and **Start**.

## 2. Talk's questions and a bug's cause (B; §121.2, §153.5–§153.6, §158.1)
1. **A question is a card**: its face the question's sign (`question`, orkUI 0.15.5) with its leader's head in the
   window's corner, the question at its foot (two lines), under its leader's lane; **lifted, its choices are dealt as
   cards over the pane** (*Choose a card*, §167.2): the question as a banner over the row, two to four choice cards (each
   its name in the header, a choice of a look its preview in the window, the leader's pick raised with its why at its
   foot, a choice that spends more its gem), *Other…* a blank card with **+** (the field opened on it with the pick's
   words), *Put it back*. A press on a choice card answers it at once: the card is played off and the next of the stack is on
   top; the answers go together after the last (`ideas.talk_answer`). Under the row, a quiet button, *Let <leader>
   decide* (the rest answered with the picks, `decide: true`). The stack's edges hint how many are left (never a count).
   With the stack lifted, **the questions together** open over the pane (`talk`) for whoever wants them so.
2. **The stances on the pane** (`talkpage.js`): while a goal is at *Talk* and picked, the pane (the Orkmaster's tab for
   a goal of several parties, its party's for one) shows the route's leaders' stances in a row, each its head and name,
   its stance line, *For* and *Against* a line each; *More* unfolds the talk in place (§142.5).
3. **A bug's cause** (`causecard.js`): the `cause` row's card, its face *The cause* and Tech's head; lifted, the guess
   (*I think …*) with its parts named (`where`, each a press lighting the part on System), **Yes**, **No, it's
   elsewhere** (opens one line for where) and *Other…*. Its questions about the cases are question cards of the same
   stack, before it.
4. **The project's questions** (`project_q`): the same question cards in a stack of no goal's, its leader's head on its
   face; the one line *Pick an answer: the leader keeps it for the project* under its first lifted card, once.

## 3. The decision and a fork (C; §117.3, §134.5, §147.3)
1. **The decision's card**: its face *Decision <n>* and the goal's element; lifted, its title, *Why* and its numbered
   points (the Orkmaster's words), an *Edit* that opens the text as a field on the card (sent as `text`), and one button
   **Confirm and start** (`ideas.confirm`). No gem: it spends nothing new.
2. **A fork**: its face *<A> and <B> disagree*, under the first lane; lifted, the two sides dealt as two choice cards
   (§167.2), each its leader's head in its window, what it says in its header and its why at its foot, a press on a
   side answering (`ideas.fork_answer`), *Other…* the blank card. While it is lifted, the pane
   shows the goal's *Spec* page with the two sections' disagreeing lines lit (`specpage.js`: the common part, then the
   sections each with its leader's head, its *Done when* at the left and its *Will be* named at the right).

## 4. The one place of the parties (D; §122.5, §137.1, §151.1–§151.3, §151.5–§151.6, §158.4–§158.5)
Over the pane (`parties`), from the first start, the tabs' **+** and a party's **…** *Edit*; title *← Parties*:
- **at the left**, *Read from the project: <kind>* (a field to correct), then the parties under the stages' headings
  *Idea*, *Being made*, *Live*, the project's stage picked on its heading (*The project is here*: `ideas.stage_set`),
  the stages reached ticked; **Release** under *In every project*, ticked and locked (*the one way into main*); each
  party a row with its leader's head (its party's race, §158.5), ticked or not, pressed to open it at the right;
- **at the right**, the size (*Lean · Standard · Full*, each with its line and its price a goal, `ideas.party_price`),
  the leader's row (its head, its name of its own beside its role, §164: *Sh.man · Architect*, *Map: <its map in one line>*, its AI tool's mark in ink and its tier), then two
  columns, **Does** under orkUI's sword and **Checks** under its shield, of the craft's role cards (head, role, tool's
  mark, tier's gear), each ticked or not (at most five *Does*, two *Checks*), a press opening the seat's popover (spec
  98 §3.4); under *Lean* the *Checks* column dimmed (*No separate check: the doer runs its own tests*), under *Standard*
  *One checker checks each task*, under *Full* *Every checker a task concerns*; under the leader's row what it keeps of
  the project (the facts kept for its party: §153.4, read and changed here, *From the next goal*);
- **at its foot**, *These parties: about n% of <tool>'s week a goal* and **Start** (the first time) or **Save**
  (*From the next task*).
At the narrow width the left is a screen and the right the next (spec 94 §1.4).

## 5. The wiring (E)
`stopcard.js` draws each new kind with its card (A–C); `frame/kinds.js` adds `parties` (D), `talk` (B) and `spec` (C)
over the pane; the pane's title carries the picked goal's phase marks *Talk · Spec · Work · Done*, the current one
marked, a past one opened by a press (§126.4); the route's dots on the tabs. Today's party form (`goalwizard.js` and its
modules) goes once nothing imports it: *New party* and *Edit* are D's.

## 5b. The host's few (F; found by A, B, D)
| part | builds | files (and their tests) |
|---|---|---|
| **F. The host's few** | §5b | `realm/goal_route.py` (the route row's `type`), new `gui/ideas_facts.py` (wired by the lead), `realm/project_facts.py`, `realm/project_kind.py` (the kind kept), `core/idea_talk.py` or `realm/idea_questions.py` (the talk read); `tests/test_goal_route.py`, new `tests/test_gui_facts.py`, `tests/test_project_facts.py`, `tests/test_project_kind.py` |

1. **The route row carries the goal's type** (`type`: `bug`, `tidy`, `balance`, …), so a short goal that is no bug is worded as its own.
2. **`ideas.project_facts {party}`** → `{facts: [{key, text, by}]}` (the facts kept for that party's calls, `project_facts.for_call`'s
   source), and **`ideas.project_fact_set {party, key, text}`** (*From the next goal*; an empty text drops it).
3. **`ideas.project_kind_set {kind}`**: the person's correction of the kind read from the project, kept in `project.json` (`kind`), read
   before the files from then on (`project_kind.read_full` honours it).
4. **`ideas.talk_read {idea}`** → the goal's Talk as kept (`talk.json`/`talk.jsonl`: each leader's stance, its for and against, its
   questions), for the stances' *More*.

## 6. Tests
Each at both widths (`tests/narrow.py`) against a stub host answering spec 99's rows and commands. A: the route card's
face and lifted state, a head's × and its popover, **+** with no Release and the offered parties first, the cost said
again after an edit, *Later, by itself* only when `low`, the bug's two cards, the `start` card's two costs. B: a question
answered with one press and the next on top, *Other…* with the pick's words, *Let … decide*, the answers sent once after
the last, the questions together over the pane, the stances on the pane, the cause's *Yes* / *No* / *Other…*, the
project's stack and its one line once. C: the decision's card with one button and its edit, a fork's sides and the
sections lit on the *Spec* page. D: the stages and the parties ticked by stage, Release locked, the size's lines and the
dimmed *Checks*, at most five and two seats, the leader's row and its facts, *Start* then *Save*. E: every kind drawn,
the phase marks, the dots, no import of the old form. The critical tests (`tests/test_architecture.py`,
`tests/test_board_alone.py`, `tests/test_updates.py`), `tests/test_gui_wording.py`, `tests/test_design_system.py` and
each part's browser tests.

## As built (A)

`hand/routecard.js` (`way("route")`: the sign `after`, the Orkmaster's crowned head, the gem by `price`; lifted: the leaders' heads in order with
their ×, a head's `SeatPop` in place, **+** of the parties off the route but Release (the offered first, *touches its map*), the route in words,
the cost's gem and words, *n-th in line*, **Talk**, **Later, by itself** when `low` (`ideas.route_later`), an edit by `ideas.route_set` said again
from its answer; a short one's two cards, **Start** by `ideas.route_start`, *The long way* by `ideas.talk`); `hand/startcard.js` (`way("start")`:
the new cost, the old struck, **Start**); `hand/way.css`. The seam grew: `hand/cost.js` asks a way's `price`, `stopcard.js` a way's `head`.
**Left (E):** the label words *route* and *start* in `KIND_WORD`; the route row carries no goal type, so a short goal that is no bug is worded as
one (the row's `type` to add); a party added by **+** goes last.

## As built (B)

A question a card (`hand/questions.js` makes a `talk` row's, a `cause` row's case questions and a `project_q` row's into one stop a question,
the answers kept and sent together after the last: `ideas.talk_answer`, `ideas.cause_answer`, `ideas.project_answer`); lifted, `hand/choose.js`
deals its choices over the pane (kind `choose`: `<Choose question choices pick onChoose onOther decide together onBack by element head hint />`,
a choice `{id, name, why?, gem?, preview?, head?, sign?}`; a part fills the kind by `chooseFor(source, Component)`), the pick raised with its why,
*Other…* a blank card with +, *Let … decide*, *All the questions*, *Put it back*, the hint once; a refusal deals them again. `hand/causecard.js`
(*The cause*: the guess, its parts lighting System, **Yes**, **No, it's elsewhere**, **Other…**); `table/talkpage.js` (kind `talk`: the stances,
*For*, *Against*, *More*; the questions together). The project's stack under its leader's lane. **Decided here:** a goal's Talk lies under the
first lane (§167.7: the whole goal's), a bug's under Tech's. **Left:** *More* shows only the leader's questions (no command reads `talk.jsonl`);
the host sends no gem or preview on a question's choices yet; E opens the stances page.

## As built (D)

`table/parties.js` (kind `parties`, `openParties({party?, first?})`): the project's kind read (a field, held in the page: **no host command
corrects it**), the stages' headings with *The project is here* (`ideas.stage_set`), Release locked, the parties' rows; `table/partyseats2.js`:
the size's three with their lines and prices, the leader's row with its own name (§164), **Does** and **Checks** (five and two at most, Checks dimmed
under Lean), a made seat's popover; the foot's price and **Start** (`ideas.goal_save` each, then `ideas.project_ask`) or **Save** (what changed).
**Left:** the facts kept for a party (no host command reads or changes them: `ideas.project_facts` proposed, drawn only when answered); the kind's
correction; `table/seatpop.js` says a race word (*Novice ork*) against spec 100 §0; E opens it from the tabs' + and a party's *Edit*.

## As built (C)

`hand/decisioncard.js` (`way("decision")`: the sign `page`, the Orkmaster's head, *Decision <n>* at its foot, no gem; lifted: *Why*, the numbered
points, **Edit** (the entry as a field, sent as `text` only when changed), **Confirm and start**; after a failed confirm the error and the button
asking the sections again); `hand/forkcard.js` (`way("fork")`: the sign `question`, the first side's leader's head; lifted, the sides dealt by
`Choose` (`chooseFor("fork")`), each its leader's head, what it says, its why, its party; **Other…** as `text`; the next fork in its place) with the
goal's *Spec* page beside them; `table/specpage.js` (kind `spec`, `ideas.page`: the common part, a section a party with its head, *Done when* left,
*Will be* right; the sides' sections lit, and their lines sharing the side's words). The seam grew: a way's `foot`, a choice's own `by`.
**Left:** the fork's face carries one head; the page's *Will be* reader is a port of `realm/spec_sections.py` (change both together); a hint
under the fork's banner (*The side you pick stands; the other leaders write their sections again*) said here.

## As built (F)

The route row's `type` (the goal's type id); `gui/ideas_facts.py`: `ideas.project_facts {party}`, `ideas.project_fact_set {party, key, text}`
(empty drops), `ideas.project_kind_set {kind}` (kept in `project.json`, read first by `project_kind.read_full`, reaching the stage and the
proposals), `ideas.talk_read {idea}` (the Talk kept: stances, questions with their state, the cause). Wired by the lead.

## As built (E)

`KIND_WORD` for the way's kinds (*Route*, *Start*, *Talk*, *The cause*, *Decision* (said *Decision <n>* once), *A fork*, *About the project*); the
route card worded by the row's `type` (a bug's two cards only for `bug`, *Tech alone: a small clean-up* for `tidy`, *a small change to the
numbers* for `balance`); the one place of the parties opened by the tabs' **+**, a party's *Edit* and the hand's *Edit the party*, its kind a
select sending `ideas.project_kind_set`, a made party's facts edited in place (`ideas.project_fact_set`, *Forget*, *From the next goal*); the
old party form gone (`goalwizard`, `partyform`, `partyseats`, `partypresets`, `partysize`, `partydraft`, `partymodel`, `goaldialog` and what only
they used; the `party` kind kept for *Remove party*); the phase marks *Talk · Spec · Work · Done* in the pane's title (Talk and Spec open
their pages); the route's dots from the picked goal's rows too; the stances' *More* from `ideas.talk_read`; no race word in a seat's popover.
**Decided here:** the first start opens the parties' place by a button on the empty Board (*Choose the parties*), not by itself. **Left:** a
goal between its decision and its plan showed only its own party's dot: a node carries its route at every state from `routed` to `done` (tests/test_board_map.py), and a goal routed
to one party that is not the one it lies in carries that party too (`idea_route.route`; decisions §169); the kinds' list is the page's own copy of
`project_kind.KINDS`; no *add a fact*; the title is *Board · Parties*, not *← Parties*.

## As built (G; decisions §169.4, §169.6)

**The first start opens by itself** (`table/parties.js` `useFirstStart`, called by `table/table.js`): once the map and the Board have answered, with no party but General and nothing open
over the pane, `openParties({first: true})`, once per project per page load; ← or Esc leaves it to the empty Board, whose *Choose the parties* opens it again (this replaces E's
*Decided here*). **A fact is added** (`table/partyseats2.js` `Facts`): under a made party's facts *Add a fact* opens one field (Esc closes it), Enter or *Add* sends
`ideas.project_fact_set {party, key, text}` with `factKey(text, keys)`: the text's first four words, slugged to `a-z0-9_` (40 at most), `_2`, `_3` … among the party's keys and never one of the
common core's (`for_whom`, `hurts`, `leaves_out`), `fact` for a text with no letter; the list is the answer's. A made party the host answers with no fact now draws the section too, with *Add a fact*.
