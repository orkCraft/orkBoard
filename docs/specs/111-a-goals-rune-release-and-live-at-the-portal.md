# 111. A goal's rune from its summoning to main; Release and Live at the portal; a party's sword and shield

Decisions §187 (1–5), §188 (1–6), §189 (1–4). The owner, 30 October, on `docs/mockups/runes-life/` and
`docs/mockups/window-runes/` (read both before building: they are the target). **Builds:** Claude (the cheaper model builds,
the spec's author reviews) · **Review:** full · P1. After spec 110 (the runes are the elements, the ring and the seal hold a
goal's rune, the table's end is laid on the page).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. orkUI 0.21.0** | the glow; the seal's free runes and its rite; the ring's rite, its corners and its gate of heads; a portal guarded without its X | repository orkCraft/orkUI: `office/components.css`, `tools/build_runes.py` and `office/runes/runes.json` (the free runes' places), `office/preview.html`, the READMEs, `CHANGELOG.md`, `tests/test_orkui.py` |
| **B. The page: the stacks, the choice, the rite at the +, the tabs** | one rune per stack and its flame; the rune chosen in the field; the summoning rite; the sword and shield on a tab; a potion marking its tabs | `realm/idea_element.py`, the command that adds a goal (`ideas.add`), `gui/ideas_map.py`; `js/table/card.js`, `js/table/cascade.js`, `js/table/table.css`, `js/table/work.css`, `js/hand/pluscard.js`, `js/hand/hand.css`, `js/table/tabs.js`, `js/hand/mana.js`; their tests |
| **C. The page: the road and the gate** | Release and Live out of the tabs into the ring's corners, asleep or awake; the checks on the way into main as skeletons that block the portal; the rite in the portal | new `realm/main_checks.py`, `realm/gate_config.py` (`[gate.main]`), `realm/goal_main.py`, `gui/ideas_gate.py`; `js/table/portal.js`, `js/table/portal.css`, `js/table/discard.js`, `js/table/tabs.js`, `js/table/data.js`, `js/hand/data.js`; their tests |

Order: A (merged to orkUI's `main`), then B, then C (each on its own branch, merged to Orkboard's `main` when the critical tests
and the touched modules' tests pass, per CLAUDE.md's alpha rule). B and C both touch `tabs.js`: C starts from B's merge.

## 1. The words

New visible words, all in English as the interface is: the field's runes row has no visible label; its group is *Its rune* and its radios *Rune 1* … *Rune 5* in the elements'
order, for a screen reader (the elements are never named, §63.4); the tab's marks' words *Does on <tool> · Checks on <tool>* (*no
separate check* for Lean); a station's words *Release: open its view*, *Live: open its view*; a skeleton's words *<check>:
checking*, *<check>: passed*, *<check>: <reason>*; the portal's line *Checking the way into main*; the sealed line
*Sealed: <check> is red: <reason>*. The default checks' names are *The merge* and *Tests*. CLAUDE.md's wording rules hold.
`realm/lexicon.py` `TERMS` gains `check` only if it is not there (*a check on the way into main*); no skeleton or goblin gets
a job title.

## 2. Part A: orkUI 0.21.0

1. **The glow**: `.ork-elem.is-glowing`: `animation: ork-glow 2.4s steps(6) infinite` with `@keyframes ork-glow { 0%, 100% {
   opacity: 0.62 } 50% { opacity: 1 } }`; under reduced motion no animation and full opacity. A test: only `opacity` moves, six
   steps, 2.4 s, off under reduced motion; the motion tests that forbid idling (`infinite`) allow this one rule by name, beside
   `.ork-busy` (keep that list explicit).
2. **The seal's free runes**: up to four `<span class="ork-sigil__free at-<deg>"><span class="ork-elem <name>"></span></span>`
   children of `.ork-sigil`, at the band's places 90°, 270°, 180° and 45° (in that order of use), each a 14 x 14 box at the
   place's 7 x 7 cells (2 px a cell; the generator computes the four boxes as it does the seal's and writes `left/top` into the
   CSS, checked by a test). Hidden at rest; on the card's hover or focus (`.ork-plus:hover`, `.ork-plus:focus-visible`, and a
   class `.is-choosing` for a held state) the decorative runes (`::after`) give way (`opacity: 0`) and the free ones show at
   75 %, one after another (90 ms apart, four steps; at once under reduced motion). `.small` has none.
3. **The rite**: `.ork-sigil.is-summoning` and `.ork-portal-ring.is-sending`, with one of `.rite-meadow`, `.rite-ice`,
   `.rite-dust`, `.rite-void`, `.rite-lava` setting `--_rite` to that element's token. The seal's lines and runes (its `::before`
   and `::after`) and the ring's runes (its `::after`) are painted `conic-gradient(var(--_rite) 0 var(--_turn), <their rest
   colour> var(--_turn))` while `--_turn` goes 0 → 360deg in eight steps (`jump-start`) over `calc(var(--ork-motion-base) * 3.5)`
   (about 640 ms), then the rite colour fades in four steps; once (`animation-iteration-count: 1`, `forwards`); the caller takes
   the class off after. The seal's icon (`.ork-plus > .ork-icon` while the seal is summoning) takes `--_rite` for the fill's last
   step. Reduced motion: nothing plays. Tokens only.
4. **The ring's corners**: `.ork-portal-ring__before` (lower left: `left: -6px; bottom: -8px`) and `.ork-portal-ring__after`
   (upper right: `right: -6px; top: -4px`, its heads in reverse order), each a row of `.ork-race__head` at 24 x 22 with 2 px
   between, a box the caller makes a button. `.is-asleep` on a corner draws its heads in grey at 40 % (`filter: grayscale(1);
   opacity: 0.4`). A head may hold `.ork-portal-ring__tick` (the `check` sign, 10 px, the success colour) or an alert (the `alert`
   sign, the danger colour). `.is-working` steps its first head as `.ork-tab[data-working]` heads step (1.2 s, two steps; still
   under reduced motion).
5. **The gate**: `.ork-portal-ring__gate`: a row centred in front of the portal's lower part (`top: 104px`, `z-index` over the
   portal), of heads at 48 x 44 (`.ork-race__head.big`), each in a `.ork-portal-ring__guard` box that may be `.is-red` (a 2 px
   drop shadow in the danger colour, an alert sign over it) or `.is-working` (steps). At most three.
6. **A guarded portal**: `.ork-portal.is-guarded` with `.is-sealed`: the sealed stillness without its X (`--_bar`, `--_bardark`,
   `--_knot` transparent).
7. The gallery: the glow on cards; the seal at rest, choosing (free runes, two and four), summoning (with a *Play the rite*
   button); the ring sending; the ring with the lich asleep and the imp asleep, the gate checking (three guards working), passed
   (three heads with ticks in the lower corner), red (one red guard, two ticks), Live awake with an alert. READMEs, `## 0.21.0`,
   version 0.21.0 (pyproject, uv.lock, tokens.json and `build_tokens.py`), `docs/preview-office.png` again. All generators'
   `--check` and `pytest` pass.

## 3. Part B: the page (the stacks, the choice, the rite at the +, the tabs)

### 3.1 One rune per stack and its flame (§187.1, §187.2)

- `table/card.js` `TaskCard`: no `Elem` in the header. `TaskEdge`: no `Elem`. `OwnCard` keeps its `Elem` and shows the goal's
  whole title (it is the goal's header). `Token` keeps its `Elem`.
- `table/cascade.js` `GoalBlock`: a goal whose cascade is only its own card (the Orkmaster reading, routing or joining it: the
  callers that draw `OwnCard`) has no `GoalStrip`.
- **The flame**: `Stage` takes the goal's element; while the task is at work (`aliveState(t.state)`, the same test `useWorked`
  uses), the stage's sign is replaced by `<Elem name=… glowing>` (`.ork-elem.is-glowing`). On an edge of a task at work, the
  element glowing stands before the stage's sign. `orkui.js`'s `Elem` takes a `glowing` flag.
- The card's own motion of a task at work (spec 107 §7, `work.css`/`table.css`: find what moves on a card whose task runs, not the
  tab's head step) goes; the flame replaces it. The tab's head step stays.
- Tests: the table's browser tests (`tests/test_table_desktop_browser.py` and the cascade's) for one rune per stack, none on a
  task card's header or an edge, an own card with no strip and the goal's whole title, the flame on a task at work and not on one
  waiting or failed, no flame under reduced motion's animation (it stands), and the old motion gone.

### 3.2 The rune chosen (§187.3)

- The map's party nodes carry `free_elements` beside `next_element` (spec 110): the elements none of the party's open goals has,
  in `idea_element.ELEMENTS`' order (`idea_element.free_for(root, state_dir, party)`), **empty when none is free** (the face then
  shows all of them).
- `hand/pluscard.js`: the seal holds the free runes (`.ork-sigil__free`) of the addressed party, at most four (the default one
  stays in `__seal`, so it is left out of the free ones; with none free, the four others); on the Orkmaster's tab with no party
  named, none. The field gains a row of five radios (`role="radiogroup"`, each a 40 x 40 button holding the rune at 28 px), the
  default checked (the addressed party's `next_element`; none checked with no party), the used ones faint; arrows move the choice,
  Tab leaves the row; the seal's `__seal` follows the choice. Sending passes `element` to `ideas.add` only when the choice differs
  from the default.
- The goal's element: `ideas.add` takes an optional `element` (one of `ELEMENTS`, else refused in words); the goal is given that
  element at once (stored as `give` stores it), else `give` as today. Tests: the command (refused, stored, default untouched) and
  the field's browser test (the row, the default, the arrows, the element sent).

### 3.3 The summoning rite (§187.4)

- When `ideas.add` succeeds, the + card's seal gets `is-summoning rite-<element>` (the element the goal was given: the command's
  answer says it, add it to the answer if it does not), taken off after the animation (`animationend`, or a timer of 1.2 s);
  nothing under reduced motion. The field closes as today. Test: the class appears with the right element and goes.

### 3.4 The sword and shield on a tab (§189)

- `table/tabs.js` `Tab`: a second line under the name with the party's Does tool and Checks tool marks (`marks/harness-<id>-ink.png`
  and the coloured one on the open tab, 14 px, after orkUI's `sword` and `shield` signs at 14 px). Where the tools come from: the
  party's tool (`goal_team.tool_of`, "" = the machine's main tool) and its roles' own tools (`clean_tools`); Does is the tool most
  of its doing roles run on, Checks most of its checking roles; a dot when a column mixes tools; Lean (its size) draws the shield
  faint with no mark. Serve what the face needs on the map's party node (`does_tool`, `checks_tool`, `does_mixed`, `checks_mixed`,
  `lean`), computed in `gui/ideas_map.py` from the realm's functions; the project's tab uses the machine's main tool for both.
- Words: `title` and `aria-label` add *Does on <tool's name> · Checks on <tool's name>*. Narrow width (compact tabs): no second line.
- `hand/mana.js`: hovering or focusing a potion adds `is-marked` to the marks of that tool on the tabs (a 1 px ink outline,
  `table.css`), and the potion's words add *<n> parties do on it* / *check on it*. Tests: the marks per party, Lean, mixed, the
  open tab in colour, the potion's marking.

## 4. Part C: the page (the road and the gate)

### 4.1 Release and Live out of the tabs (§188.1, §188.2)

- `table/data.js`: `roadParties()`: the party whose map node's `party_craft` is `release` (Release) and the one whose craft is `run`
  or `liveops` (Live, the first if both). At the wide width `tabs.js` leaves them out of the tab row and the lanes leave out their
  columns (`partiesNow` for the tabs and lanes; keep a separate list for everything else that needs all parties). The narrow width
  keeps them as today.
- The ring's corners (`table/portal.js`, the ring spec 110 laid): `__before` holds Release's leader's head (and, awake, up to two of
  its members' heads), `__after` Live's; each a `<button>` that opens that party as a tab does (`openTab(slug)`; the pane then shows
  that party, with no tab lit in the row). No corner for a party the project does not have.
- **Awake** (else `.is-asleep`): Release when `readyOf()` has goals, a task of the party runs, or it has a question or an alert in
  the hand; Live when a task of its runs, or it has a question or an alert (the same signals the tabs use today: `isWorking`,
  `hasAlert`, the route dot: reuse them). `.is-working` while one of its tasks runs; an alert sign on its leader when it has one.
- Their hand cards (`hand/data.js` `laneOf`): a row whose party is a road party lies in the hand's last lane, at its right end
  before the potions.

### 4.2 The checks on the way into main (§188.3)

- `realm/gate_config.py`: `[gate.main]` in `orkcraft.toml`: `checks = [{name = "Unit tests", run = "pytest -q tests/unit"}, …]`
  (each a name and a command; a bad entry said in `Gate.error` as today); `main_checks(root) -> list[Check]`. With none written:
  `[Check("The merge", ""), Check("Tests", <the gate's own command and files, as a task's result runs them>)]`; *The merge* is the
  plan's trial pick itself.
- New `realm/main_checks.py` (no face, no model): `run(repo, state_dir, slug, *, root, into, main, on_step)`: builds the trial (the
  plan's picks onto main in the `gate-main-try` worktree, as `goal_main.plan` does, kept until the checks end, then removed), runs
  each check's command there in order, with the gate's timeout, and reports each check `{name, state: "waiting" | "running" |
  "passed" | "failed", words}` through `on_step`; a failed merge fails *The merge* and leaves the others `waiting`. The worktree is
  gone whatever happens. Under the repository's lock only while it makes and removes the worktree.
- `gui/ideas_gate.py`: `ideas.to_main_checks {idea}` starts the run in the background and publishes each step on the bus
  (`main.check`, `{idea, checks}`); `ideas.to_main` refuses while any check of that goal is not `passed` (*Sealed: <check> is red:
  <words>*, or *Checking the way into main*). The last results are kept per goal until the plan changes (a new commit in it).
- Tests (no network, a temporary repository): the default checks, a written `[gate.main]`, a bad one, a failing command, a merge
  that conflicts, the worktree gone after, the refusal while checking and after a failure, the bus steps.

### 4.3 The skeletons at the gate (§188.4, §188.5)

- When a goal is chosen for main (`portal.js` `choose`), the page asks `ideas.to_main_checks` and follows `main.check`. The skeletons
  are Release's members' heads (skeleton laborer, warrior, elder in that order: one per check, the fourth and more folded into the
  third's words *and n more*):
  - **running or waiting**: in `.ork-portal-ring__gate`, `.is-working` for the one running; the portal `is-sealed is-guarded`; the
    line *Checking the way into main*; Release's corner awake;
  - **passed**: the head leaves the gate for Release's corner with a tick;
  - **failed**: it stays in the gate, `.is-red`, and the line says *Sealed: <check> is red: <words>* in the danger colour; the others
    that passed are in the corner with their ticks.
  - When every check passed, the gate is empty and the portal is open (`is-open`, as spec 110).
  A sealed reason that no check owns (`plan.sealed`: a goal not done, main behind its origin) keeps today's sealed portal with its X.
- A check whose command calls a model (none by default) would carry its tool's mark: not built here (no check runs a model yet);
  leave a comment where it would go.

### 4.4 The rite in the portal (§187.4)

- When `ideas.to_main` succeeds, the ring gets `is-sending rite-<element of the goal>` while the card goes in (`GO_MS`), taken off
  after; nothing under reduced motion.

### 4.5 Tests of C

The discard's, the portal's and the tabs' browser tests: Release and Live not in the tabs at the wide width and in the row at the
narrow; their corners asleep and awake on the signals; a press opens their view; the gate's three states with a scripted
`main.check` (checking, passed, red), the line's words, the X only for a reason no check owns, `ideas.to_main` refused while a
skeleton stands; the rite's classes; the hand's cards of a road party at the right end. The critical tests and every touched
module's tests pass.

## 5. Later (not here)

- A check judged by a model (a visual check by a model, with its tool's mark and its cost).
- The phone's own face (spec 94 B–E) gets the road.

## As built

**Part B** (branch `spec-111-b`, on orkUI 0.21.0 copied with `python -m orkboard.design.orkui`). *Built as specced*: one rune per stack (`TaskCard` and `TaskEdge` carry none; `OwnBlock` has no strip, `OwnCard` its rune and the goal's whole title); the flame
(`Elem glowing`, orkUI's `.is-glowing`) in the stage's sign's place on a card and before the sign on an edge of a task at work (`aliveState`), the old step of the drawing and the dotted line gone from `work.css` (the state-change flash stays); `idea_element.free` /
`free_for` and `free_elements` on the map's party nodes (empty when none is free); `give(..., want=)` and `ideas.add`'s optional `element` (refused with *Pick one of the five runes*, stored at once under the lock, so no read of the Map can give the goal another first; the
answer's `element` is the one it wears); the free runes in the seal (`.ork-sigil__free` at-90, at-270, at-180, at-45, the default left out, none at the narrow width and none on the Orkmaster's tab), `is-choosing` while the field is open; the field's *Its rune* row (five 40 x 40
radios, *Rune 1* … *Rune 5*, the default checked, the used faint, arrows and press choose, Tab leaves, the seal follows; `element` is sent only when it differs from the default); the rite (`summon` in `hand/state.js`: `is-summoning rite-<element>` on the seal for 1.2 s, none under
reduced motion); the tabs' second line (`table/tabmarks.js`: sword and shield with the tools' marks, the open tab's in colour, a dot for a mixed column, the faint shield for Lean, the words in `title` and `aria-label`, none at the narrow width); `markedTool` set by a potion's hover or
focus (`is-marked`, 1 px ink outline) and the potion's words adding *<n> parties do on it, <n> parties check on it*. The map serves `does_tool`, `checks_tool`, `does_mixed`, `checks_mixed` and `lean` from `MapMixin.marks_of`: a seat runs on its own tool, else the party's, else the machine's main tool
(resolved there, so *mixed* is true only when the tools really differ); Does is the tool most of the installed doing seats run on (the leader's with none), Checks the same for the checking seats (the leader's with none: it checks, `goal_team.checkers`), none for Lean.
*Departures*: (1) `OwnCard` wears `ork-picked` when its goal is picked, since with no strip a goal in two lanes would otherwise be lit in one only. (2) The narrow width's `Token` keeps its rune and it glows while its front task is at work (the spec names no flame for it; the
token's own stepping drawing went with the rest of the old motion). (3) A tool's name in the tab's words and the potion's is the limits' own (*Claude*, *Codex*, as the potion says it), not the registry's full title (*Claude Code*), so the page needs no list of names; a tool with no mark shows its initial.
(4) A potion marks the project's tab's marks as well as the parties' (the spec says *the tabs*); the potion's counts are of parties only. (5) The seats the map knows are the installed ones, as its other party fields: `marks_of` reads those. (6) `tests/test_hand_mention_browser.py` pinned the + card's hatch, which spec 110 removed
(decisions §185.4) and failed on `main` before this part; it now pins its absence. *Tests*: `tests/test_idea_element.py` (free, `free_for`, `give` with `want`, `free_elements` on the map, `ideas.add` with and refused `element`), the new `tests/test_map_party_marks.py`, and the browser tests of the table
(`test_table_desktop_browser.py`: one rune per stack, the flame and its absence, reduced motion, the tabs' marks per party, Lean, mixed, colour on the open tab, the potion's outline), the hand (`test_hand_desktop_browser.py`: the free runes, the row, its arrows, the default not sent, the rite and its
absence under reduced motion), the mana (`test_hand_mana_browser.py`: the potion's marking and words) and the owner's day (`test_owners_day_browser.py`: the flame replacing the old motion).
