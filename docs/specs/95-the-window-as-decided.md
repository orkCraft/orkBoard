# Spec 95 — The window as decided: §104–§146 read as one

The owner and the PM, 27 October. `docs/decisions.md` is a log: from §104 to §146 one decision often changes another made
hours before (§134 changes §133, §138 changes §136, §145 turns §104.0's frame round). This spec is that log read as one
window, with no deltas, so that a slice's spec is written from it and not from forty entries. **Builds:** nothing by
itself; each slice's spec builds a part of it. **When a decision after §146 changes the window, this spec is changed in
the same commit**; where it and a decision differ, the decision is right and this spec is fixed.

**What it is, and is not:** the window as it will be, each part with the decisions it rests on. Not: how it is built
(files, tests: the slices' specs), the phone's frame (spec 94), the engine's calls beyond what the person sees.

## 1. The frame
1. **Two parts** (§145.1): **the table** (the leaders' tabs and the pane: what and why, through whose eyes) and **the
   hand** at its foot (what the person decides, and where the goals wait). No top bar (§126.1), no left column (§145),
   no right column (§120), no drawer (§104.8), no dialog (§127.1), no temporary tab (§142).
2. **The roles** (§104.0): the Orkmaster says what is done and who does it; a party's leader says how, what changes and
   why; a member does, and asks only its leader. A member's question reaches the person only as its leader's fork.
3. **Two axes** (§110.1, §145.5): **what is looked at** (the whole project, or the picked goal) and **through whom** (the
   tab). The pane's title says both: *Waves · through Tech*, *The whole project · through Design*.
4. **No count anywhere** (§67): a stack's edges hint how many (five at most).

## 2. The tabs
1. **The Orkmaster's tab first**, the project's name on it (*Orkmaster · Party game*); its **…** holds the projects'
   switcher, *Settings*, *Operations*, the history and the files (§145.6, §138.5). Its header: its AI tool alone, its
   tier always the cheaper, said in its popover (§140.1).
2. **Then a tab a party**, its leader's head and the party's name (§110.3); more than fit, the heads alone, the name on
   hover and in the pane's title. A picked goal's route puts a dot on its parties' tabs, its step's in its element.
3. **At the tabs' end**: **+** (*New party*), the AI tools' limits as chips (a press: what used them, §107.1) and **Stop
   all** (§126.1).
4. **A tab is its column's head on the Board** (§143): while the Board is shown the tabs take their columns' widths.
5. **A party's header is its name and its squad** (§134.3): a seat each (*Leads*, *Does*, *Checks*, at most three), the
   member's head with its tier's gear, its AI tool under it, turned while it works; an empty seat a ghost (*+ Checker*).
   A head pressed opens its popover (§110.7): its role, what the party does, its AI tool, its tier and what it costs,
   *From the next task*, *Set* with *Undo*, *Take off the seat*, the role's text (§136.11). A party's menu (**…**):
   change the leader, remove the party (§97, as a card in the hand, §127.1).

## 3. The pane: one map a tab
1. **Every tab shows one map** (§134.2, §135.1); no segmented control. The maps:

   | tab | its map | read from |
   |---|---|---|
   | Orkmaster | **Board**: a column a party under its tab, its tasks at work as cards with their member's head; the Orkmaster's own column its routing and joining (§143) | the Board |
   | Tech | **System**: the containers first, their named links (*commands: 40 · starts*), a container pressed opens its parts in layers (§112.1–§112.4); a part's files on its back (§136.3); a container's command, port and last lines (§136.7) | the code, no model |
   | Design | **the screens along their flow**, their pictures as cards, a band at the foot of what they use (logo, icons, fonts) (§112.7, §136.3) | pictures, routes |
   | Product | **the same map as Design's**, its pains pinned to screens and steps, a segment as a filter (§134.2) | the same, `segments.json` |
   | Game design | **the loop**, four to six cards the person and the leader keep, each tied to its configs (§112.8) | the person's and the leader's |
   | Art | **its assets**: art and icons, sound, music, clips; a card lifted shows it large and plays it; variants not picked under the one picked (§135.4) | the files, git, the picks |
   | Release | **dev against main**: a card a goal in dev not in main, ticked; what reached main since the last version faint under *Since 1.3* (§137.3) | git |

   A party with nothing to read is its header alone (§112.9). A kind whose craft has no party lies on Design's band,
   else among System's files, else in the Orkmaster's **…** (§136.3, §138.5).
2. **A map is cards on the table** (§104.2): 128 × 180 on the desktop, its name up to four lines, its goal's element top
   left, its kind's sign top right. What happens is a motion (§89): new is dealt, changed is sealed with its goal's
   element, gone crumbles, promised is a ghost, at work turns with its member's head. A changed card says **who decided
   it**: the person, the leader, or a member alone (the last in the signal's colour) (§112.6).
3. **The reveal** (§104.12): opened after being away, a map plays what landed since the last look; *Since <version>*
   from the tab's **…** (§126.5).
4. **A card pressed is lifted** where it lies and turns over (§120.1): its back the details (a part's files, *Uses*,
   *Used by*, its changes and their goals; a task's *What it made*). At most twice a card, never over what it is about.
   Esc or a press away lowers it. A mark pressed says which goal made it and lights that goal's other marks (§126.5).
5. **The pane opens one thing over its map** (§142): **Open** on a lifted card's back (a diff, a log, a failure's lines,
   a file, an asset large, a role's text), a place from the Orkmaster's **…** (*Settings*, *Operations*, the history,
   the files) or **+** (*New party*), and **▶ Play** (§111). Its title says where it came from (*← System ·
   server/lobby.ts*); **←** or Esc goes back to the map as it was, the card it came from lit. One at a time, nothing
   pinned. Play keeps running after **←**; **▶** returns to it, **■** stops it. **In VS Code** a read opens in the editor
   (its diff, the file at its line, an output channel *Orkboard*) (§146.1).
6. **The pane's title**: what is looked at · through whom, the picked goal's phase marks (a past phase opened by a press
   on its mark, §126.4), **▶ Play** (§136.3).

## 4. The hand
From left to right (§145.3–§145.4, §121.2, §137.5):
1. **The blank card** (§116.2, §124): one field; Enter sends, Shift+Enter a new line; a picture pasted goes with it; a
   microphone writes the words into it, never sends (§125). No priority, no kind. **Addressed to a party** by *@Tech* in
   the text, or by the party's tab being open (*→ Tech ×*, one press takes it off); on the Orkmaster's tab it is general.
   An addressed idea puts its party's map in **picking**, always seen: *Pick a part to point at it* · *Stop picking*; any
   card of that map is pinned to the blank card as a mark (§141, §140.4; spec 94 §1.5).
2. **The deck**: the goals in line (not started; waiting for the reset under the moon). Pressed, it opens over the pane
   as a list in the Orkmaster's order, with a search; a goal not started is moved by dragging; a press picks it.
3. **The stacks**, one a goal that asks the person (§121.2): its most urgent card face up; a stack pressed fans out in
   place and picks its goal. The stacks lie by their top card's urgency: money and failures, then a question the work
   waits for, then the rest.
4. **Release's card** *n goals ready for main*, its leader's head on it; pressed, it opens Release's tab (§137.5).
5. **The discard**: the goals done and not yet seen, the last face up. Pressed, it opens them over the pane; a goal's
   *Result* opened, the goal leaves for the history (§130.1).
6. **A card is lifted** with its answers on it while the pane shows the map it is about, each answer's change drawn
   there (§104.5, §104.8); the lanes or cards it is about rise a little (§144.3); *Put it back* lowers it.
7. **A card that spends** carries its share of the limits in a small frame at its bottom left (*4%*), its words on the
   card (*about 4% of Claude's week*); a card that spends nothing carries none (§144.2).
8. **The hand stays under everything opened** (§142.6).

## 5. A goal's life
1. **Four places** (§145.2): the deck, the hand, the table, the discard. Its signs are its places': the moon in the
   deck; the leader's head (it works) and the alert (it failed) on its cards on the table and its stack; *done* in the
   discard (§145.7). The hourglass is a card a member works on where no head stands (§136.1).
2. **The phases** (§118.1): **Idea** → **Talk** → **Decided** → **Spec** → **Work** → **Done**.
   - **Idea**: sent from the blank card, routed by the Orkmaster (code or the cheaper tier). **The route card** comes
     first (§133.1, §138.2): the leaders' heads in order (a head's × takes it off, **+** adds any party but Release,
     §140.2–§140.3), the cost, its place (*3rd in line*, §138.3), **Talk** and **Later, by itself**. No call before
     that press. *Later* puts it in the deck.
   - **Talk**: the route's leaders answer short on the cheaper tier (a stance, for and against, questions); the person
     answers in the hand, two rounds at most; the questions left take their leaders' defaults (§118.1, §121.2).
   - **Decided**: the Orkmaster words the decision; **Confirm and start** or **Confirm** (§134.5). Confirmed, it is
     committed to dev, numbered, in the project's `docs/decisions.md` (§138.7).
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
3. **The short way** (§118.2): a bug goes to Tech alone and skips Talk and Decided; its route card says so, with
   **Start** and the long way beside it. A small goal is offered the same.
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
1. **One craft, one map** (§109.1). A game: Game design, Tech, Art, Release, LiveOps. An app or a site: Product,
   Design, Tech, Release, Run. **Release is in every project** and cannot be removed (§137.1); General, Team and
   Ideation are no parties (§122).
2. **The project's stage chooses the crafts** (§122.5): *Idea*, *Being made*, *Live*.
3. **A party's size is its seats** (§104.1): **Lean** the leader alone, **Standard** the leader and its builder,
   **Full** the leader, its builder and its checker.
4. **New party** opens over the pane: the crafts the stage needs, each ticked with its size and squad (§116.1, §127.1).

## 7. The first start
§132, §145.8: the AI tools found and their *Check* (`gui/onboarding.py`); then the Orkmaster's tab alone: *Open a
project*, *Where is the project?*, the parties ticked, one **Start**, the leaders' heads dealt onto the tabs. With no
goal, the blank card lies large in the pane's middle with two or three examples read from the project; sent, it moves
to the hand and the route card is dealt beside it. The deck comes with the first goal in line, the discard with the
first goal done. One line, once: under the first question of *Talk*, *Pick an answer: the leader writes it into the
spec*. No tour, no *Skip*.

## 8. Widths and frames
1. **One page at every width** (§128, spec 94): under 760 CSS px (§136.9) the table above (the tabs a row of heads, the
   Board's columns a head's width with tokens, §143.4) and the hand at the foot; what opens over the pane is a screen;
   **←** is the browser's back; *Stop all* at the end of the row of heads, the limits' chips in the Orkmaster's **…**.
2. **The phone's app is a frame** (spec 94 §4): pairing, the cache, push, the update, what is kept with no signal.
3. **VS Code** (§146): the Board in an editor tab, or in the side bar at the narrow width; reads open in the editor.

## 9. Signs and motions
The closed set, kept in orkUI (§127.3): **signs** — the goal's element, the signal's colour, the alert, the hourglass,
the moon, *done*; the heads are accents, the cost's frame a number's place. **Motions** — dealt (and played, from the
hand to a lane), sealed, crumbled, ghost, turned, lifted, the microphone's pulse. A new thing takes one of them or
replaces one. Under reduced motion each is still.

## 10. Gone
The top bar; the left column, its groups and *The whole project* row; the right column; the drawer; the dialogs; the
temporary tab and pinning; a party's *Overview*, *Now* line and stance; the views' segmented control; *Feature modules*
as a tab; the Assets button; *Agents*; the analytics page; the canvases; the night and *Process now*; a goal's priority,
kind and lens switch; the moon of progress; *waits for you* on rows and tabs; the *Flags* fold; the parties General,
Team and Ideation; *Storyboard* and *Versions*; the measures (§129).

## 11. The first slice
As decided (§136.12, §137.6, §145.10), on the owner's Node party game, done at the owner's yes: **before it** §131's
list and Agents go; **the slice** is the parties by craft with Release, the stage at the first opening, the route and
the sections; the table and the hand with the deck and the discard; the Orkmaster's tab (*Board*) and the leaders'
tabs with their headers and popovers; Tech's *System* as it is read today; the blank card as a message; the phases
with the route card, *Talk*, *Confirm and start*, the forks and *Start*; the hand by goal; the goal's signs; *To main*
on Release's map; the words and the closed set of signs; spec 94 §1's rules. **After it**: the other maps and picking on
them; Play and System anew; the phone; the limits' wait, *Start now*, recurring goals, *Release a version*; the voice,
the history, Settings, the reveal *Since <version>*.

**Asked, not decided**: cutting the slice to what proves the frame first (the table with *System* and *Board*, the hand
with the route card, *Talk* and *Start*, the deck and the discard), the rest after the owner's yes.

## 12. The words
`TERMS` gets its one word each with the slice's first spec (§121.1): *table*, *hand*, *deck*, *discard*, *lane*,
*blank card*, *lifted card*, *route*, *route card*, *step*, *phase*, *section*, *seat*, *stage*, *map*, *will be*,
*fork*, *out of the contract*, *To main*, *Release a version*, *in line*. A part of a map is not called a *card* where a
person reads it (spec 70 §0); the deck reads *In line* and the discard *Done* on hover, so the battler's words are never
the only ones.
