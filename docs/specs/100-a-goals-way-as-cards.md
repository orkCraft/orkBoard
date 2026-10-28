# Spec 100 — A goal's way as cards: the route card, Talk's questions, the decision, a fork, a bug's cause, the project's questions, the one place of the parties

The owner and the PM, 28 October (decisions §117, §118, §121.2, §133, §134.5, §136.2, §140, §147, §151.5, §153,
§156.6, §158.1–§158.3, §159, §160, §167; spec 95 §4.2, §5.2–§5.3, §6.3–§6.6; the mockup `docs/mockups/s2b/`). The faces of
spec 99's way, drawn on spec 98's frame (the table and the hand) with spec 99's Needs you rows. **Builds:** a cheaper
model, each part reviewed by Claude · **Review:** full · P0. **A, B, C and D at once** (they share no file); **E after
them**. **Only after the owner's yes on the S2b mockup**, after spec 98 D and E (the hand and the window) and the spec 99
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
| **B. Talk's questions** | §2, §5 | new `static/js/hand/questioncard.js` (a question; a goal's stack of them; the project's stack), new `static/js/hand/causecard.js`, new `static/js/table/talkpage.js` (the stances on the pane), new `static/js/hand/questions.css`; new `tests/test_talk_desktop_browser.py` |
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
