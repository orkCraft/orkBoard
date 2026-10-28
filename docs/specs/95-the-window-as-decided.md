# Spec 95 — The window as decided: §104–§146 read as one

The owner and the PM, 27 October. `docs/decisions.md` is a log: from §104 to §146 one decision often changes another made
hours before (§134 changes §133, §138 changes §136, §145 turns §104.0's frame round). This spec is that log read as one
window, with no deltas, so that a slice's spec is written from it and not from forty entries. **Builds:** nothing by
itself; each slice's spec builds a part of it. **When a decision after §146 changes the window, this spec is changed in
the same commit**; where it and a decision differ, the decision is right and this spec is fixed. Read up to §167.

**What it is, and is not:** the window as it will be, each part with the decisions it rests on. Not: how it is built
(files, tests: the slices' specs), the phone's frame (spec 94), the engine's calls beyond what the person sees.

## 1. The frame
1. **Two parts** (§145.1): **the table** (the leaders' tabs and the pane: what and why, through whose eyes) and **the
   hand** at its foot, under the table's lanes (what the person decides, §167.7). No top bar (§126.1), no left column (§145),
   no right column (§120), no drawer (§104.8), no dialog (§127.1), no temporary tab (§142).
2. **The roles** (§104.0): the Orkmaster says what is done and who does it; a party's leader says how, what changes and
   why; a member does, and asks only its leader. A member's question reaches the person only as its leader's fork.
3. **Two axes** (§110.1, §145.5): **what is looked at** (the whole project, or the picked goal) and **through whom** (the
   tab). The pane's title says both: *Waves · through Tech*, *The whole project · through Design*.
4. **No count anywhere** (§67): a stack's edges hint how many (five at most).

## 2. The tabs
1. **The project's tab first**, its name with the crowned head (*Party game*, §167.6): its lane is the whole project's
   (routing, Talk, decisions, joining, the goals in line); the pane's title names the Orkmaster (*through the
   Orkmaster*). Its **…** holds the projects' switcher, *Settings*, the history and the files (§145.6, §138.5, §147.1). Its header: its AI tool alone, its
   tier always the cheaper, said in its popover (§140.1).
2. **Then a tab a party**, its leader's head and the party's name (§110.3); more than fit, the heads alone, the name on
   hover and in the pane's title. A picked goal's route puts a dot on its parties' tabs, its step's in its element.
3. **At the tabs' end**: **+** (*New party*), the AI tools' limits as chips (a press: what used them, §107.1) and **Stop
   all** (§126.1).
4. **A tab is its column's head on the Board** (§143): the tabs, the Board's lanes and the hand share one grid, every
   lane a card and a quarter wide, narrowing to a card's width when they don't fit (§167.7).
5. **A party's header is its name, its squad and its size** (§134.3, §151.3): the squad's heads at 24 px grouped
   *Leads* | *Does* | *Checks* (at most seven), each with its tier's gear and its AI tool's mark, turned while it works,
   the leader its race's higher form (§155); the size in one word beside them.
   A head pressed opens its popover (§110.7): its role, what the party does, its AI tool, its tier and what it costs,
   *From the next task*, *Set* with *Undo*, *Take off the seat*, the role's text (§136.11), **Open its view** (§151.4).
   A party's menu (**…**): *Edit* (§151.5), change the leader, remove the party (§97, as a card in the hand, §127.1).

## 3. The pane: one map a tab
1. **Every tab shows one map** (§134.2, §135.1); no segmented control. The maps:

   | tab | its map | read from |
   |---|---|---|
   | the project's | **Board**: a lane a party under its tab, a goal a cascade of its tasks in its lane, the picked goal's unfolded (§167.4); the first lane its routing, Talk, decisions, joining and the goals *In line* (§143, §167.5) | the Board |
   | Tech | **System**: the containers first, their named links (*commands: 40 · starts*), a container pressed opens its parts in layers (§112.1–§112.4); a part's files on its back (§136.3); a container's command, port and last lines (§136.7) | the code, no model |
   | Design | **the screens along their flow**, their pictures as cards, a band at the foot of what they use (logo, icons, fonts) (§112.7, §136.3) | pictures, routes |
   | Product | **the same map as Design's**, its pains pinned to screens and steps, a segment as a filter (§134.2) | the same, `segments.json` |
   | Game design | **the loop**, four to six cards the person and the leader keep, each tied to its configs (§112.8) | the person's and the leader's |
   | Art | **its assets**: art and icons, sound, music, clips; a card lifted shows it large and plays it; variants not picked under the one picked (§135.4) | the files, git, the picks |
   | Release | **dev against main**: a card a goal in dev not in main, ticked; what reached main since the last version faint under *Since 1.3* (§137.3) | git |

   A party with nothing to read is its header alone (§112.9). A kind whose craft has no party lies on Design's band,
   else among System's files, else in the Orkmaster's **…** (§136.3, §138.5).
2. **A map is cards on the table** (§104.2; the Board's cards are §167.1's, below): 128 × 180 on the desktop, its name up to four lines, its goal's element top
   left, its kind's sign top right. What happens is a motion (§89): new is dealt, changed is sealed with its goal's
   element, gone crumbles, promised is a ghost, at work turns with its member's head. A changed card says **who decided
   it**: the person, the leader, or a member alone (the last in the signal's colour) (§112.6). **Another party's change
   shows too** (§156.3–§156.4): a card that rests on a part another goal changed is sealed with that goal's element, one
   that rests on a part promised to change carries that goal's ghost, its back saying which goal and who decided.
3. **The reveal** (§104.12): opened after being away, a map plays what landed since the last look; *Since <version>*
   from the tab's **…** (§126.5).
4. **A card pressed is lifted** where it lies and turns over (§120.1): its back the details (a part's files, *Uses*,
   *Used by*, its changes and their goals; a task's *What it made*). At most twice a card, never over what it is about.
   Esc or a press away lowers it. A mark pressed says which goal made it and lights that goal's other marks (§126.5).
5. **The pane opens one thing over its map** (§142): **Open** on a lifted card's back (a diff, a log, a failure's lines,
   a file, an asset large, a role's text), a place from the Orkmaster's **…** (*Settings*, the history,
   the files) or **+** (*New party*), and **▶ Play** (§111). Its title says where it came from (*← System ·
   server/lobby.ts*); **←** or Esc goes back to the map as it was, the card it came from lit. One at a time, nothing
   pinned. Play keeps running after **←**; **▶** returns to it, **■** stops it. **In VS Code** a read opens in the editor
   (its diff, the file at its line, an output channel *Orkboard*) (§146.1).
6. **The pane's title**: what is looked at · through whom, the picked goal's phase marks (a past phase opened by a press
   on its mark, §126.4), **▶ Play** (§136.3).

## 4. The hand
**Under the table's lanes** (§167.5, §167.7, §145.3–§145.4, §121.2, §159), a card under the lane it is about:
1. **The + card under the first lane** (§160.2, §167.5): pressed (or typing with nothing focused) it grows into **the
   field** over the hand (§116.2, §124): Enter sends, Shift+Enter a new line; a picture pasted goes with it; a
   microphone writes the words into it, never sends (§125). No priority, no kind. **Addressed to a party** by *@Tech* in
   the text, or by the party's tab being open (*→ Tech ×*, one press takes it off); on the project's tab it is general.
   An addressed idea puts its party's map in **picking**, always seen: *Pick a part to point at it* · *Stop picking*;
   any card of that map is pinned to the field as a mark (§141, §140.4; spec 94 §1.5), one by a press or several by a
   box as Warcraft's units (§152; a whole group pinned as the group). **No deck**: the goals in line lie in the first
   lane's *In line* (§167.5).
2. **The stacks**, one a goal and a lane that asks the person (§121.2, §167.7): under the lane of who asks (a failure
   its party's, a leader's question its party's; the route, Talk of several leaders, the decision and a fork under the
   first lane, fanned beside the + card); a goal's cards from one party one stack, its most urgent card in front; two
   goals under one lane fan within its width, the urgent in front, those behind their edge and element only, rising on
   hover or a press; a stack pressed picks its goal, its stacks lit alike. **A question is a card** of two to four
   choices, one picked for the person with its why; lifted, **its choices are dealt as cards over the pane** (*Choose a
   card*, §167.2): the pick raised, a choice that spends more with its gem, *Other…* a blank card with **+** (the field
   opened with the pick's words), *Let … decide* a quiet button answering the rest with the picks; a goal's questions
   are its stack, answered one a press, the answers sent together after the last (§153.5–§153.6). **The project's
   questions** (§153.1) are a stack of no goal's under their leader's lane, holding nothing back (§157.1).
3. **The discard under the tabs' end** (§145.4, §159, §167.7: under the limits' chips and *Stop all*): the goals done and not yet seen, the last face up; while
   dev holds goals main lacks, its top card carries Release's leader's head and *n ready for main*. Pressed, it opens
   over the pane: the goals done and not seen (a goal's *Result* opened, the goal leaves for the history, §130.1), and
   *Ready for main* with **To main** (§137.4); no act on main lies on the pile (§160.5).
4. **A card's face** (§167.1): the element at the left of its header, its name left-aligned (three lines at most); a
   low window with one toned-down sign (the action's: the alert, the question, *done*) and the head of who asks small
   in its corner; its label row the party's name and, when it spends, its gem at the right; its foot the question or
   the line. **The hand shows the cards' upper part** (§167.8), a card rising whole on hover, focus or a tap. **A card
   is lifted** with its answers on it while the pane shows the map it is about, each answer's change drawn there
   (§104.5, §104.8), its cost's words there (*about 4% of Claude's week*, §160.6); the lanes or cards it is about rise
   a little (§144.3); *Put it back* lowers it. A card that spends nothing carries no gem.
5. **The hand stays under everything opened** (§142.6).

## 5. A goal's life
1. **Three places** (§145.2, §167.5): the table (in line in the first lane, or at work in its party's), the hand, the
   discard. Its signs are its places': the moon on it in line while it waits for the reset; its task's type and stage
   on its cards on the table, the alert when it failed; the action's sign and its leader's head on its stack; *done* in
   the discard (§145.7, §167.1).
2. **The phases as the person reads them** (§147.2): **Talk** → **Spec** → **Work** → **Done** (the engine keeps
   *Idea* and *Decided* as its own states, §118.1).
   - **Talk** opens with **the route card** (§133.1, §138.2), once the Orkmaster has routed the idea sent from the blank
     card (code or the cheaper tier): the leaders' heads in order (a head's × takes it off, **+** adds any party but
     Release, §140.2–§140.3; a party whose map the goal's change touches is offered on it, §156.6), the cost, its
     place (*3rd in line*, §138.3), and **Talk**; **Later, by itself** beside it only when the limits run low
     (§147.4), laying it in line (§167.5). No call before that press. Then the route's leaders answer short on the cheaper
     tier (a stance, for and against, questions); at its party's first goal a leader's questions about the project
     share the goal's three (§153.3); the person answers in the hand, two rounds at most; the questions left take
     their leaders' defaults (§118.1, §121.2). **Talk closes with the
     decision's card**: the Orkmaster words the decision, one button, **Confirm and start** (§147.3); confirmed, it is
     committed to dev, numbered, in the project's `docs/decisions.md` (§138.7). A goal is held back by *Hold* in the
     **…** of its stack or of its lifted card on the table, or by *Stop all*.
   - **Spec**: every leader on the route writes its section at once (§117.2): *Why*, *Done when* (five at most),
     *Checks*, *Will be*, *Out*, *Risks*, *Defaults*, *Questions*; the Orkmaster joins them on the cheaper tier, never
     changing a leader's words; what two sections disagree on is a fork in the hand, both sides with their why (§117.3,
     §118.3). After *Confirm and start*, the work starts by itself when nothing is left to settle; a step added since
     the route card brings a *Start* card with the new cost (§136.2).
   - **Work**: *Start* plays the goal's card onto the lane of its first step (§144.1); each leader plans its own step;
     the will-be's ghosts fill as tasks land in dev (§104.6, §101). The hand holds only forks and *out of the
     contract* (§104.9).
   - **Done**: its work in dev (§138.1), its *Result* promised against made; it goes to the discard, and to Release's
     map until *To main*.
3. **The short way** (§118.2, §158.1–§158.3): a bug goes to Tech alone. Its Talk is its diagnosis: one round, at most
   three questions about its cases and a card of Tech's guess of the cause; no decision is written. A bug that already
   reproduces (a failure's lines, a stack trace, a failing test) skips it: its route card says so, with **Start** and
   the long way beside it. A small goal is offered the same.
4. **A change while it works** is a new idea of the same goal, written with the goal picked, talked only with the
   leaders it touches, decided as an entry that names what it changes; only the tasks whose sections changed are planned
   again (§118.7).
5. **The limits** (§121.3, §133.4, §136.5): when they run low the Orkmaster offers the short way or **Later, by
   itself**; a goal waiting for the reset carries the moon, its hour on hover and on its route card with **Start now**
   (*from your reserve* said on the button when it spends it).
6. **A recurring goal** of LiveOps or Run is decided once; its rounds take no route card and start by themselves within
   the limits, else wait under the moon, never spending the reserve (§122.6, §136.4, §138.6).
7. **Which tab a picked goal opens on** (§138.4, §139): a goal of one party on that party's tab at every phase; a goal of
   several on the Orkmaster's tab before *Work* (the page of its phase), on its step's tab from *Work*. At *Work*,
   through the Orkmaster's tab, a goal is its Board (§136.10). The open tab is never switched under the person.
8. **Main**: only Release writes it (§137): **To main** merges the ticked goals by code, no call (one goal ticked is a
   fix for production); **Release a version** is the goal *A release*, its cost said before. The gate's checks run on it.

## 6. Parties
1. **One craft, one map** (§109.1). A game: Game design, Tech, Art, Release, LiveOps, Marketing. An app or a site:
   Product, Design, Tech, Release, Run, Marketing. **Release is in every project** and cannot be removed (§137.1);
   **Marketing** comes at *Live*, led by Growth, with ASO and UA (§151.7–§151.8); General, Team and Ideation are no
   parties (§122). Marketing's map is the way people come: the channels → the store page or the site → the install →
   the first session.
2. **The project's stage chooses the crafts** (§122.5): *Idea*, *Being made*, *Live*.
3. **The squad is who the party has; the size is how the work goes** (§151.1–§151.2): the squad the specialists
   picked from the craft's cards (at most seven: a leader, up to five who do, up to two who check), a task given to the
   one it is for; the size **Lean** (plan → do, one at once), **Standard** (plan → do → one check, two at once) or
   **Full** (plan → do → every checker it concerns, three at once), its cost said on it. Release: its leader, Lean;
   a seat added to it is a skeleton (§157.2).
4. **A specialist's view is marks on its party's map** (§151.4): its head and the alert on the cards it speaks of;
   **Open its view** from its popover opens the whole of it over the pane. Never a tab or a switch.
5. **One place makes and edits the parties** (§151.5), over the pane: at the left the project's kind and the parties
   under the stages' headings (the project's stage picked on its heading, Release locked); at the right the size, the
   leader's row (its name of its own, §164, beside its role), **Does** (a sword) and **Checks** (a shield) of role cards; under the leader's row what it keeps of
   the project, its answers read and changed from the next goal (§153.4); at the foot the cost and **Start** or
   **Save**.
6. **A party's race is its party's; its leader is its race's higher form, grown out of the head, never worn** (§53,
   §154–§155, §158.4–§158.5): every seat wears its party's race, whatever its role's craft. Product, or a game's Game
   design: knights led by a golden unicorn knight with an angel's wings (§162); Tech: orks led by an ork shaman; Design, or a game's Art: elves led by an
   elf dryad; Run, or a game's LiveOps: goblins led by an imp; Marketing: gnomes led by a gnome fairy; Release: a lich
   leading skeletons. Six parties, six races, so no two leaders of a project share a head; the tier is the gear
   every head wears; the crown is the Orkmaster's alone. The rest of the cast is the marketing's (§158.6).

## 7. The first start
§132, §145.8: the AI tools found and their *Check* (`gui/onboarding.py`); then the Orkmaster's tab alone: *Open a
project*, *Where is the project?*, the parties ticked, one **Start**, the leaders' heads dealt onto the tabs. With no
goal, the + card lies large in the pane's middle with two or three examples read from the project; sent, it moves
to the hand and the route card is dealt beside it. **The project's questions** are dealt after **Start** as one stack
(§153.1–§153.2, §157.1): Product's (whom it is for, what hurts them, what it leaves out), Game design's in a game, the
Orkmaster's *What is this project for?* with neither; each only where the project's files do not say it, the leader's
reading picked where they do; the other leaders are quiet at the start. *In line* comes with the first goal in line, the
discard with the first goal done. One line, once: under the first card with answers, *Pick an answer: the leader writes
it into the spec* (on the project's questions, *the leader keeps it for the project*). No tour, no *Skip*.

## 8. Widths and frames
1. **One page at every width** (§128, spec 94): under 760 CSS px (§136.9) the table above (the tabs a row of heads, the
   Board's columns a head's width with tokens, §143.4) and the hand at the foot; what opens over the pane is a screen;
   **←** is the browser's back; *Stop all* at the end of the row of heads, the limits' chips in the Orkmaster's **…**.
   **A phone on its side is the table** (§150): a low window (under 500 px high) keeps the wide layout made compact,
   the hand a fan of overlapping cards, the + card and the discard at its ends; nothing locks the orientation.
2. **The phone's app is a frame** (spec 94 §4): pairing, the cache, push, the update, what is kept with no signal.
3. **VS Code** (§146): the Board in an editor tab, or in the side bar at the narrow width; reads open in the editor.

## 9. Signs and motions
The closed set, kept in orkUI (§127.3): **signs** — the goal's element, the signal's colour, the alert, the hourglass,
the moon, *done*; the heads are accents, the cost's frame a number's place. **Motions** — dealt (and played, from the
hand to a lane), sealed, crumbled, ghost, turned, lifted, the microphone's pulse. A new thing takes one of them or
replaces one. Under reduced motion each is still.
**The look** (§106, §115, §148, §163): orkUI's office in the half-tint warm (0.14.0's greys), the cards on their own fill a step lighter, a slate grey a hint cold (§166); the moon one sign only; the
icons drawn at the signs' weight; the AI tools' marks in ink; the elements on hues no signal has; a head at its own 24 × 22 (or 48 × 44, §161),
never the action's green; six races, each leader its race's higher form (§154.3, §155); the cost in orkUI's gem.
**The cards answer the hand as Balatro's** (§149): they lean toward the pointer, give when pressed, fly with weight
when played, fan out when dealt, break into pixel shards when they crumble; still at rest and while read, none of it
under reduced motion. A hand card face down shows **one back** (a pixel pattern). The heads are drawn on a
12 × 11 grid as they always were, told by their faces and colours, the leaders drawn the same way (§161); the detailed art is the marketing's.

## 10. Gone
The top bar; the left column, its groups and *The whole project* row; the right column; the drawer; the dialogs; the
temporary tab and pinning; a party's *Overview*, *Now* line and stance; the views' segmented control; *Feature modules*
as a tab; the Assets button; *Agents*; the analytics page; the canvases; the night and *Process now*; a goal's priority,
kind and lens switch; the moon of progress; *waits for you* on rows and tabs; the *Flags* fold; the parties General,
Team and Ideation; *Storyboard* and *Versions*; the measures (§129); Operations in Orkboard's window, *Idea* and
*Decided* as the person's phases, a bare *Confirm*, *Later* on every route card (§147).

## 11. The first slice
As decided (§136.12, §137.6, §145.10), on the owner's Node party game, done at the owner's yes: **before it** §131's
list and Agents go; **the slice** is the parties by craft with Release, the stage at the first opening, the route and
the sections; the table and the hand with the discard (§167: no deck, the line in the first lane); the Orkmaster's tab (*Board*) and the leaders'
tabs with their headers and popovers; Tech's *System* as it is read today; the blank card as a message; the phases
with the route card, *Talk*, *Confirm and start*, the forks and *Start*; the hand by goal; the goal's signs; *To main*
on Release's map; the words and the closed set of signs; spec 94 §1's rules. **Joined it since**: the squad, the size
and the one place of the parties (§151.10); the project's questions and a question a card (§153.7); the races and the
leaders' forms (§154.5, §155.7); a leader's map as text in its calls, the project's facts by party, bounded reads and a
task's own section (§156.14). **After it**: the other maps and picking on
them; Play and System anew; the phone; the limits' wait, *Start now*, recurring goals, *Release a version*; the voice,
the history, Settings, the reveal *Since <version>*.

**Cut** (spec 98, which settles what was asked here): the frame first on today's engine (spec 98: the table with *System*
and *Board*, the hand with the deck, the stacks, Release's card and the discard), then a goal's way on it (spec 99 its
engine, spec 100 its faces: the route card, *Talk*, *Confirm and start*, the forks, the project's questions, the one place
of the parties), each at the owner's yes.

## 12. The words
`TERMS` gets its one word each with the slice's first spec (§121.1): *table*, *hand*, *discard*, *lane*,
*blank card*, *lifted card*, *cascade*, *route*, *route card*, *step*, *phase* (*Talk*, *Spec*, *Work*, *Done*), *Hold*, *section*, *seat*, *stage*, *map*, *will be*,
*fork*, *out of the contract*, *To main*, *Release a version*, *in line*, *squad*, *size*, *Other…*. A part of a map is not called a *card* where a
person reads it (spec 70 §0); the first lane's line reads *In line* and the discard *Done* on hover, so the battler's words are never
the only ones.
