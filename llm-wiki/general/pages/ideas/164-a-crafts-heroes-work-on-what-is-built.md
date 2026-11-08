---
owner: board
kind: idea
track: product
order: 13
size:
priority: normal
short: A craft's heroes
phase: done
route: product, design, tech
spec: docs/specs/164-a-crafts-heroes-work-on-what-is-built.md
by: claude-code
gate: b624cd2 · 291 files · green
schema: 3
---
# A craft's heroes work on what is built

## Gist
Build decisions §278 and §279 (the owner, 8 November; first taken on 7 November on the branch claude/class-leaders-frameworks-nw3xxx, which never reached main): a craft keeps only the heroes whose framework stands on what Orkboard builds today (its craft's map and aspects, and data gathered by code, Play, the brief or the mana's record), no least number and six at most; the fifteen heroes named there (Product, Design, Tech, Run, Marketing, Release), the ones not taken and the later ones; the Orkmaster's star read from the project's kind and stage; a game's heroes at Game design (Dungeon Master Knight, Economy Knight, Pillar Knight) and Art (Sprite Dryad), LiveOps' chair empty until its map, a game's star; a hero with nothing to stand on in the project's kind is not offered there. Today §266.3 (three to six a craft) is what main builds. The new faces are drawn in orkUI before they are used (§266.4) and the heroes' names go in TERMS. Implementation on the simpler models.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages
- [ ] A. Six heroes cut, Lantern Imp Run's default
  - party: Tech (the simpler model; §278.1–3, §281.3). `orkboard/realm/seat_hero_rules.py`: remove `uni-lean`, `dry-diamond`, `dry-atom`, `sh-ddd`, `sh-fit`, `imp-slo`; add `CUT = {id: (name, why)}` for those six, each why a line of §278.3 (`"uni-lean": ("Pivot Knight", "no measure to pivot by: the project's analytics are not read")`); `imp-obs` becomes `_default("imp-obs", "run", "Lantern Imp", "Observability first", "trace → read → fix", "standard", 2, 2)`, no places (no table, §281.3). Sprint Dryad's places become Map, Sketch, Decide, Test (Prototype goes; Test asks "What did Play show of the sketch picked on the phone?"); its `prototype` aspect goes and its `test` aspect asks of Play, not of five people. `orkboard/realm/seat_rubric_rules.py` `RUBRICS["run"]`: framework "Observability first: …", short "Observability", aspects traces, errors and slow places, no signals. `orkboard/realm/heroes.py`'s docstring says the catalog as it now is. Mend the tests that pin a cut id with a kept one (`sh-xp`, `uni-jtbd`): tests/test_heroes.py, test_stall.py, test_lay_tables.py, test_hero_table.py, test_stall_browser.py, test_hero_table_browser.py (its rows table keeps `layout: rows` under a kept id; `LAYOUTS` keeps `rows`). Leave tests/test_seat_rule_outputs.py red: stage D writes its baseline again, once.
  - proves: Tech's "When the catalog is read, then it holds §278.2's and §279.1–2's heroes…" (its half: no cut hero, Run's default Lantern Imp)
- [ ] B. Seven new heroes, Pillar Knight at two crafts
  - party: Tech (the simpler model; §278.2, §279.1–2, §279.5, §279.4, §278.5). `seat_hero_rules.py` stays pure: `Hero` gains `also: tuple[str, ...] = ()` (the other crafts it sits at), `kinds: tuple[str, ...] = ()` (the project kinds it is offered in; empty is every kind) and `not_here: str = ""` (its why, in words, where it is not offered); `sits_at(hero, craft)`; `of(craft)` gives the default first, then the craft's own heroes in the catalog's order, then those that sit there by `also`. New ones, size, `decides` and `says_no` as their siblings':
    - `uni-pillar` Pillar Knight, product, `also=("game-design",)`, "Design pillars", "pillars → the goal against them → keep or cut", after Appetite Knight; places Pillars ("What must it always be? (the brief's pillars)"), Leaves out ("What does it leave out on purpose? (the brief's leaves out)"), Against them ("Which goal goes against a pillar?"), Keep or cut ("Is the goal kept or cut, and why?").
    - `uni-mda` Dungeon Master Knight, game-design's `_default`, "MDA and the loops", "loop → reward → hook"; `uni-econ` Economy Knight, game-design, "Sources and sinks", "currency → source → sink", places Currencies, Sources, Sinks.
    - `dry-a11y` Inclusive Dryad, design, "WCAG 2.2", "barriers → contrast and keys → fix", places Barriers ("Who is stopped, and on which screen?"), Contrast and keys ("Which text or control fails contrast, a key or a label?"), Fixed ("Which barrier is gone, seen again?"); its aspects ask only what the `a11y` hint reads (§209.3–4 are not built).
    - `dry-sprite` Sprite Dryad, art's `_default`, "An art bible, its pipeline and a budget", "style → pipeline → budget".
    - `sh-scene` Scene Shaman, tech, "An engine's scenes", "scene → autoloads → coupling", places Scenes, Autoloads, Coupling; `fairy-pos` Position Gnome, marketing, "Positioning", "the alternatives → what only it does → who cares", places The alternatives (the brief's why this, not what they use now), What only it does, Who cares.
    - `kinds`: `sh-scene` `("game",)`; `dry-heur`, `dry-sprint`, `dry-a11y` `("empty", "mobile", "game", "web", "design")`; `fairy-aso` `("mobile", "web", "game")`, each with its `not_here` ("Scene Shaman reads an engine's scenes: this project is not a game", and so on). `STARS = {"game": ("uni-mda", "dry-sprite", "sh-scene", "fairy-pos"), "web": ("uni-ost", "dry-heur", "sh-xp", "fairy-aso"), "mobile": (the same as web)}`.
    `orkboard/realm/goal_team.py` `hero_of` and `set_hero`, and `orkboard/realm/lens_rubrics.py` `_hero`, take a hero by `sits_at`, not `craft ==`. Tests in tests/test_heroes.py (eighteen heroes, six at most a craft, one default each but LiveOps), test_goal_team.py, test_lens_rubrics.py, test_hero_table.py.
  - proves: Tech's "When the catalog is read, then it holds §278.2's and §279.1–2's heroes, Pillar Knight once at Product and Game design…", "When a Game design party takes Pillar Knight, then `hero_of` gives `uni-pillar` there…"
- [ ] C. The heroes' names in TERMS and LEADERS
  - party: Tech (the simpler model; §278.7, §279.6). `orkboard/realm/lexicon.py`: `_t("hero.<id>", "<name>")` for each of the eighteen, beside `hero.frame`; `orkboard/gui/ideas_stall.py` writes a hero's word on its ware and hand card through `lexicon.term(f"hero.{id}")`. `orkboard/gui/static/js/table/partyseats2.js` `LEADERS`: run "Lantern Imp", no liveops key (seatpop.js already shows no name when none). Tests: tests/test_lexicon.py (each `HEROES[id].name` is `TERMS`' `hero.<id>` word; no cut id has one) and tests/test_heroes.py (partyseats2.js's `LEADERS`, read as text, names each craft's default as the catalog does; LiveOps none); tests/test_gui_wording.py holds.
  - proves: Tech's and Design's Checks on `TERMS` and `LEADERS` (no Done when line by itself)
- [ ] D. The leaders' role files say today's heroes
  - party: Tech (the simpler model; §281.7, §278.2, §279.1–2). `orkboard/realm/agent_rules_text.py`: only `table_text` changes (goal 166 edits the file next): each hero of `of(craft)` (Pillar Knight at Product and at Game design), its school and places, and where it is not offered (`not_here`); "" for LiveOps. Write the repository's `llm-wiki/general/roles/*-leader.md` and `.claude/agents/ork-*-leader.md` again through `agent_rules.write(<repo>, "llm-wiki/general")`, in this commit. Write `tests/fixtures/seat_rules_original.json.gz` again once from `tests/seat_rule_cases.py` `outputs()`; diff the decompressed JSON before and after, and the difference is only the leaders' hero part and Run's rubric lines (say so in the commit message). Tests: tests/test_agent_rules.py, test_agent_rules_prompts.py, test_seat_rule_outputs.py.
  - proves: Product's "When Orkboard writes the role files, then `roles/product-leader.md` names Angel Invest, Jobwise, Appetite and Pillar Knight…"; Design's "When Orkboard writes the role files, then `roles/design-leader.md` names Pixel-Perfect, Sprint and Inclusive Dryad…"
- [ ] E. Offered, locked or starred by the project's kind
  - party: Tech (the simpler model; §279.5, §279.4, §281.1, §57.3). `orkboard/realm/heroes.py`: `offer(root, state_dir, craft)` → `[(hero, why)]` in `of`'s order, `why` "" where offered, else its `not_here`, the kind read by `project_kind.read_full(root, state_dir=state_dir)["kind"]`; `star(root, state_dir, craft)` the id of `STARS[kind]` at that craft, "" for a kind with none. `orkboard/gui/ideas_stall.py`: a locked hero's ware has `price: {locked: why}`; `stall_take` of a locked hero is refused with its why and the page keeps its hero; the starred ware carries `star: true`, the hand's card never; the hero shelf only where two or more heroes are offered (one: its hand card alone; none: no hero card, no shelf); `stall_back` where the craft has no default hero is refused "This party has no hero"; nothing but a take writes `hero`. Keep ideas_stall.py under ~600 lines. Tests in tests/test_stall.py (the kind set by `project_kind.keep`): Product's shelf in order with no Pivot Knight; Pillar Knight's take line (its four places, one pass); a web app's Design shelf with Pixel-Perfect's `star`; Scene Shaman locked and refused in a web app, a ware starred in a game, no `hero` key written; a game's Art with no shelf; LiveOps with no card and Back to default refused in words.
  - proves: Tech's "When a web app's Tech stall is asked to take Scene Shaman…", "When a LiveOps party's stall opens…"; Product's "When a Product party's stall opens as a person first meets it…", "When a Product party takes Pillar Knight…"; Design's "When a web app's Design party's stall opens…" and "When a game's Art party's stall opens…" (the host's half: the sign and the head are I's)
- [ ] F. A cut hero said once
  - party: Tech (the simpler model; §281.2, the person's answer *Default seated, said once*). `orkboard/realm/heroes.py`: the cut said kept in `<state>/heroes_cut.json` (`{party: hero id}`, through `ideas._json` / `ideas._write_json` under `ideas.LOCK`). `ideas_stall.stall`: where the party's page keeps a `hero` in `CUT` and the record does not hold it, `say` begins "<name> was cut: <why>. <default>, its craft's default, leads now." and the record is written; the page's `hero` key and `pages/tables/<party>.md` are never written by it. Tests in tests/test_stall.py: each of the six ids; a second open and a new host on the same state (a restart) say nothing; the page and the table file byte for byte as they were.
  - proves: Tech's "When a party's page keeps a cut hero…"; Product's "When a Product party whose page keeps `hero: uni-lean` opens its stall first…", "When that party's stall says Pivot Knight was cut…"
- [ ] G. A locked hero's why on the page
  - party: Design (the simpler model; §279.5: said, not hidden). `orkboard/gui/static/js/table/stall.js` `Ware`: a locked hero shows its why in words under its plate (the makers' `stall-maker__why` way, always visible for a hero, id `hero-why-<id>`), its button `aria-describedby` it and `aria-disabled="true"`; a press and Enter send no `ideas.stall_take`. `stall.css`: the why lies outside the dimmed face, in orkUI's tokens at 4.5:1 or more, no new colour; the plate keeps its lock shape. A browser test in tests/test_stall_browser.py: a web app's Tech stall, Scene Shaman locked, its why by aria-describedby, a press and Enter take nothing.
  - proves: Design's "When a web app's Tech party's stall opens as a person first meets it, then Scene Shaman lies locked…"
- [ ] H. The seven faces and the star's sign, drawn in orkUI and copied
  - party: Design (§266.4, §278.6, §279.6; drawn in orkUI, github.com/orkCraft/orkUI, and merged there first, so nothing before this stage waits on it). In orkUI: the heads `races/hero-<id>-<tier>[-<mood>][@2x].png` of `uni-pillar`, `uni-mda`, `uni-econ`, `dry-a11y`, `dry-sprite`, `sh-scene`, `fairy-pos`, every tier and mood `hero-uni-jtbd` has, each unlike the others of its shelf and its race's head; and the star's sign `signs/pick.svg`, in the sizes orkUI's signs have. Here, only `python -m orkboard.design.orkui <orkUI>`: `design-system/orkui/` and `ORKUI.json` stamped, nothing edited by hand. A test in tests/test_heroes.py: every hero not a default that a kind offers, and Dungeon Master Knight and Sprite Dryad, has `hero-<id>-elder.png` in `roles.RACE_FILES`. Tests: tests/test_design_system.py, test_heroes.py.
  - proves: Design's "When the catalog offers its heroes in each kind… the seven new heroes' heads (`hero-<id>-elder.png` and their moods) are in orkUI's copy, stamped in `ORKUI.json`" (its second half)
- [ ] I. The faces and the star on the stall
  - party: Design (the simpler model; §281.1, §279.4, §266.4). `orkboard/gui/static/js/table/stall.js` (or `stallfaces.js`): a ware with `star` draws orkUI's `signs/pick.svg` on its face, `role="img"`, `aria-label` *The Orkmaster's pick*; the hand's card never draws it (it says *Yours*). Tests: tests/test_heroes.py, for each of `project_kind.KINDS` and each craft, no two heroes offered on one shelf have the same `heroes.head`; tests/test_stall_browser.py, a web app's Design shelf Pixel-Perfect, Sprint, Inclusive Dryad in order, Pixel-Perfect's sign named *The Orkmaster's pick*, and a game's Art party with Sprite Dryad in the hand drawn by `hero-dry-sprite`, no shelf.
  - proves: Design's "When a web app's Design party's stall opens as a person first meets it…", "When a game's Art party's stall opens…", "When the catalog offers its heroes in each kind, then no two wares of one shelf draw the same head…" (its first half)

## Open questions
- Does the star seat its hero? (**Marks the ware only** / Seats new parties / Seats every unchosen party) — Spike Shaman (the dearest) and Store Gnome lay frames, a model's pass each; a cost moved by itself is the person's (§57.3) · Marks the ware only: Nothing changes by itself; each craft's default stays until taken · Seats new parties: A new app's Tech starts on Spike Shaman, the dearest; old parties keep theirs · Seats every unchosen party: Projects on update switch heroes; each new frame laid in a pass
  - Answered: Marks the ware only (the person, 2026-11-08)
- When a party's hero is cut? (**Default seated, said once** / Default seated silently / Kept until another is taken) — the person took it and the hand marks it Yours (§266.1); a swap unseen breaks H1 · Default seated, said once: The stall's line names the cut hero and why; its table file stays as was · Default seated silently: As goal_team.hero_of does today; the hand shows another hero unasked · Kept until another is taken: The cut hero still works for who carries it; the shelf marks it retired
  - Answered: Default seated, said once (the person, 2026-11-08)
- How does Lantern Imp sit at Run? (**Run's default, no table** / Its own table, a pass) — Run has no map to lay, and no pass is spent by itself (§57.3); its rubric then says what Play gathers · Run's default, no table: Run's rubric becomes traces, errors and slow places; no model's pass · Its own table, a pass: Every Run party lays Lantern's four places in a model's pass on update
  - Answered: Run's default, no table (the person, 2026-11-08)

## Decisions
- §281: the person's answers in Talk (8 November 2026)

## Product
### Talk
- verdict: go — a game's Game design and Art chairs have no hero today, Pivot Knight's frame waits on analytics never read; what the new heroes stand on is built (loop, assets, brief)
- stance: Product keeps four heroes (Angel Invest, Jobwise, Appetite, Pillar) and lets Pivot Knight go: a ware that lays places nothing fills is a promise the stall should not sell
- for: it cuts before it adds: six heroes with no map or data go, and the indie game maker (§218.2) gets heroes on the Loop and Assets maps already built, in every game
- against: no person has yet been seen taking a hero in the stall; seven new schools widen a shelf whose worth is untested, and Product's tree still lives in .orkcraft/ only (goal 163)
- instead: first the cut and a game's two defaults (Dungeon Master Knight, Sprite Dryad, on the Loop and Assets maps); the five new schools once a hero taken is seen
- assumes: a hero's school changes its leader's say enough for a person to pick one — shown by: two heroes' Talk on one goal differ in verdict or questions, and a tester takes one

### Why
- A Product hero is the school its leader judges a goal by; one whose places nothing fills (Pivot Knight, no analytics read) is a promise the stall should not sell.
- Pillar Knight stands on the brief's pillars and leaves_out, already asked; the leader's role file must say today's heroes, or it judges by a cut one (§281.7).

### Done when
- [test] When a Product party's stall opens as a person first meets it, then its hero shelf offers Angel Invest, Jobwise, Appetite and Pillar Knight, in that order, and no Pivot Knight.
- [test] When a Product party whose page keeps `hero: uni-lean` opens its stall first after the update, then its hand shows Angel Invest Knight, the line names Pivot Knight cut and why; a second open, no line.
- [test] When that party's stall says Pivot Knight was cut, then its table file `pages/tables/<party>.md` stays byte for byte as it was.
- [test] When a Product party takes Pillar Knight, then the stall's line names its four places (Pillars, Leaves out, Against them, Keep or cut) and its price is one pass.
- [test] When Orkboard writes the role files, then `roles/product-leader.md` names Angel Invest, Jobwise, Appetite and Pillar Knight with their places, and no Pivot Knight.

### Checks
- Pillar Knight's Pillars and Leaves out places ask from the brief's own keys (`project_facts` `pillars`, `leaves_out`); no new brief key is made.
- Each Product hero's place names what fills it (the tree, the brief, the mana's record); none asks for a number nothing gathers.
- The star on a web app's Product shelf (Angel Invest Knight) changes no party's `hero` key (§281.1).
- `.claude/agents/ork-product-leader.md`, written again, says the same heroes as `roles/product-leader.md`.
- Pillar Knight's name is in `TERMS` (§278.7) and the stall writes it from there.

### Will be
- none — the tree (map_parts `product`: jobs, hypotheses) is unchanged; the work changes Product's heroes (`realm/seat_hero_rules.py`), not its map

### Out
- Pivot Knight's return with the project's analytics (§278.4, spec 115's later part).
- Game design's, Art's and the other crafts' heroes, and every new face in orkUI (Design's and Tech's sections).
- The Orkmaster reading the decisions before it routes (§281.7, a goal of its own).

### Risks
- risk: medium
- Pillar Knight's places lie empty where the brief's second sitting (pillars) was never answered: the fault Pivot Knight was cut for, smaller.
- Pillar Knight is one hero at two crafts: `goal_team.hero_of`'s `kept.craft == craft` would drop it at one and seat the default unsaid.
- The shelf's worth is still untested: no person has been seen taking a hero (Talk's assumes).
- A role file on disk keeps Pivot Knight until Orkboard writes it again.

### Defaults
- Pillar Knight's places, in lanes: Pillars (What must it always be?), Leaves out (What does it leave out on purpose?), Against them, Keep or cut; the same at Game design.
- Pillar Knight is offered in every kind with a Product chair: the brief is asked of all; its places stay empty until the brief answers.
- *Said once* is the first stall open after the update; the hero kept on the page then reads as the default.
- The shelf keeps the catalog's order, the default first.

### Accepted
- met: When a Product party's stall opens as a person first meets it, then its hero shelf offers Angel Invest, Jobwise, Appetite and Pillar Knight, in that order, and no Pivot Knight.
- met: When a Product party whose page keeps `hero: uni-lean` opens its stall first after the update, then its hand shows Angel Invest Knight, the line names Pivot Knight cut and why; a second open, no line.
- met: When that party's stall says Pivot Knight was cut, then its table file `pages/tables/<party>.md` stays byte for byte as it was.
- met: When a Product party takes Pillar Knight, then the stall's line names its four places (Pillars, Leaves out, Against them, Keep or cut) and its price is one pass.
- met: When Orkboard writes the role files, then `roles/product-leader.md` names Angel Invest, Jobwise, Appetite and Pillar Knight with their places, and no Pivot Knight.

## Design
### Talk
- verdict: doubt — a cut hero a party carries falls back silently (goal_team.hero_of); go once the stall says so and the seven new faces are in orkUI first (§266.4)
- stance: Design keeps Pixel-Perfect and Sprint Dryad, gains Inclusive Dryad; a hero not for the kind lies locked with its why (§279.5: said, not hidden), never just missing
- for: the shelf loses wares whose places nothing fills (Diamond's research, Sprint's five people); a game's Art gets Sprite Dryad on the Assets map already drawn
- against: seven new faces, none in orkUI yet (heroes.head falls back to the race's head: three knights alike); Inclusive Dryad stands on one a11y hint the default reads
- instead: first the cut and Sprite Dryad with its face; Inclusive Dryad once §209.3–4's contrast and focus path are read on Play
- assumes: Inclusive Dryad says more than the default's Accessibility aspect on one a11y hint — shown by: both heroes' Talk on one screen goal differ in verdict or questions

### Why
- A hero's face and its plate are all a person sees before taking it: two heroes drawn alike, or a lock whose why hides in a tooltip, make the stall a guess.
- Design's own shelf must offer only heroes whose places Orkboard fills (Diamond's research, Sprint's five people are not gathered), and a game's Art must get its one.

### Done when
- [test] When a web app's Design party's stall opens as a person first meets it, then its shelf offers Pixel-Perfect, Sprint and Inclusive Dryad in that order, no Diamond or Atom Dryad, Pixel-Perfect starred by a sign named *The Orkmaster's pick*.
- [test] When a web app's Tech party's stall opens as a person first meets it, then Scene Shaman lies locked, its why in words under it tied to its button by aria-describedby, not only a title; pressed or Enter, nothing is taken.
- [test] When a game's Art party's stall opens as a person first meets it, then Sprite Dryad, its one hero, is in the hand drawn by its own orkUI head, and no shelf offers a choice of heroes.
- [test] When the catalog offers its heroes in each kind, then no two wares of one shelf draw the same head, and the seven new heroes' heads (`hero-<id>-elder.png` and their moods) are in orkUI's copy, stamped in `ORKUI.json`.
- [test] When Orkboard writes the role files, then `roles/design-leader.md` names Pixel-Perfect, Sprint and Inclusive Dryad with their places, no Diamond or Atom Dryad, and Sprint's Test asks what Play showed of the sketch picked.

### Checks
- orkUI's copy is not edited here: the seven heads and the star's sign come from orkUI through `python -m orkboard.design.orkui`, and `tests/test_design_system.py` holds.
- A locked ware's plate and its why read from orkUI's tokens at 4.5:1 or more on the rug; no new colour, and the lock is a shape, not a colour alone.
- Inclusive Dryad's aspects read only the `a11y` hint today; none of its places asks for contrast or a focus path Play does not gather (§209.3–4).
- Design's and Art's heroes' names (Pixel-Perfect, Sprint, Inclusive, Sprite Dryad) are in `TERMS`, and the stall and `partyseats2.js` `LEADERS` say them as `TERMS` does.
- The star is on the shelf only: the hand's card says *Yours* for what the party carries, never the star (§281.1).

### Will be
- none — the screens map (map_parts `design`: steps and screens) is unchanged: no screen or route is added; the stall's shelf and orkUI's heads change

### Out
- Inclusive Dryad reading contrast and the focus path on Play (§209.3–4): its places stay on the `a11y` hint until those are built.
- The catalog's data, its kinds and the stall's filter (Tech's section); Product's and Game design's heroes' places (Product's section).
- Diamond and Atom Dryad's return (§278.4: Atom with a hint of a part made outside the project's library).

### Risks
- risk: medium
- The faces wait on orkUI: drawn there and copied first (§266.4); until then `heroes.head` draws the race's head and Pillar, Dungeon Master and Economy Knight look alike.
- Inclusive Dryad may say no more than the default's Accessibility aspect on one hint (Talk's assumes); then the shelf sells a ware twice.
- Locked wares shown, not hidden, lengthen a shelf: on the phone it scrolls, and a person may read a lock as a hero to buy later.
- Today a hero's lock says its why only in `title` (mouse alone); the makers' locked way (`stall-maker__why`) is the pattern to reuse.

### Defaults
- A hero not for the project's kind lies on its shelf locked, its why in words (§279.5: said, not hidden); a craft with no hero for the kind is an empty chair, no shelf.
- Inclusive Dryad's places, in lanes: Barriers (Who is stopped, and on which screen?), Contrast and keys (Which text or control fails contrast, a key or a label?), Fixed (Which barrier is gone, seen again?).
- Sprint Dryad's places become Map, Sketch, Decide, Test (§278.2's flow): Prototype goes, the sketch picked on the phone is it; Test asks what Play showed of it.
- The star is a sign of orkUI's, drawn with the faces, its accessible name *The Orkmaster's pick*.

### Accepted
- met: When a web app's Design party's stall opens as a person first meets it, then its shelf offers Pixel-Perfect, Sprint and Inclusive Dryad in that order, no Diamond or Atom Dryad, Pixel-Perfect starred by a sign named *The Orkmaster's pick*.
- met: When a web app's Tech party's stall opens as a person first meets it, then Scene Shaman lies locked, its why in words under it tied to its button by aria-describedby, not only a title; pressed or Enter, nothing is taken.
- met: When a game's Art party's stall opens as a person first meets it, then Sprite Dryad, its one hero, is in the hand drawn by its own orkUI head, and no shelf offers a choice of heroes.
- met: When the catalog offers its heroes in each kind, then no two wares of one shelf draw the same head, and the seven new heroes' heads (`hero-<id>-elder.png` and their moods) are in orkUI's copy, stamped in `ORKUI.json`.
- met: When Orkboard writes the role files, then `roles/design-leader.md` names Pixel-Perfect, Sprint and Inclusive Dryad with their places, no Diamond or Atom Dryad, and Sprint's Test asks what Play showed of the sketch picked.

## Tech
### Talk
- verdict: go — one catalog (realm/seat_hero_rules.py, 196 lines) and the stall's filter; no new caller of gui, no cycle; Run's default and the JS copy of the names must be mended with it
- stance: Tech builds it as data: kinds on each hero, Pillar Knight one hero at two crafts, Dungeon Master Knight and Sprite Dryad as their crafts' defaults (their hints are the rubric's)
- for: Game design and Art get heroes whose frame is their rubric already (no_reward to heavy), so they cost no pass; six frames nothing fills leave the catalog and the leaders' role files
- against: cutting Uptime Imp leaves Run no default: ideas_stall._default reads default(craft).id and breaks; partyseats2.js LEADERS keeps its own names; six test files pin the cut ids
- instead: land the whole catalog now, a non-default hero offered only when orkUI's copy has its face (heroes.head's file), so §266.4 holds by code, not by the order of commits
- assumes: project_kind reads a project's kind rightly enough to lock heroes by it — shown by: the testers' project.json seldom carry the person's `kind` correction

### Why
- The catalog is one pure module every leader's lens, table, role file and stall reads: a hero cut there must leave no caller reading a default that is gone (Run's) or a name kept twice (JS).
- A kind's lock and a cut hero must be decided once, in realm, and said by the stall; never a hero swapped unsaid under a party, nor a page or table file rewritten by a read.

### Done when
- [test] When the catalog is read, then it holds §278.2's and §279.1–2's heroes, Pillar Knight once at Product and Game design, six at most a craft, one default each but LiveOps, Run's Lantern Imp.
- [test] When a party's page keeps a cut hero (uni-lean, dry-diamond, dry-atom, sh-ddd, sh-fit, imp-slo), then its first stall open names it cut and why, a second (a restart too) does not, its page and table unwritten.
- [test] When a web app's Tech stall is asked to take Scene Shaman, then it is refused with the lock's why and the page keeps its hero; in a game it is a ware starred, and no star writes a `hero` key.
- [test] When a Game design party takes Pillar Knight, then `hero_of` gives `uni-pillar` there as at Product, and the table it lays has Pillar Knight's four places, in order.
- [test] When a LiveOps party's stall opens as a person first meets it, then it shows no hero card and no shelf, and Back to default is refused in words, not by an error.

### Checks
- `seat_hero_rules.py` stays pure (no import but the rubric's), the kind's lock and the star are read in `heroes.py`; `tests/test_architecture.py` holds and no module passes ~600 lines.
- Each hero's name is TERMS' `hero.<id>` word, and `partyseats2.js` `LEADERS` names each craft's default as the catalog does (Run: Lantern Imp; LiveOps none), checked by a test.
- `tests/fixtures/seat_rules_original.json.gz` is written again once, and its difference is only the leaders' hero part and Run's rubric lines.
- `agent_rules_text.py` changes in `table_text` only (goal 166 edits it next); the repository's `roles/*-leader.md` and `.claude/agents/ork-*-leader.md` are written again in the same commit.
- Every hero not a default that a kind offers has its `hero-<id>-elder.png` in orkUI's copy, checked by a test, so §266.4 holds by code.

### Will be
- changed orkboard/realm/seat_hero_rules.py — six cut, seven new, Lantern Imp Run's default, each hero's kinds, the cut ones' whys, the stars by kind
- changed orkboard/realm/heroes.py — a hero offered or locked in a kind, the star, a cut hero said once (a record in the state folder)
- changed orkboard/realm/goal_team.py — `hero_of` and `set_hero` take a hero at every craft it sits at (Pillar Knight's two)
- changed orkboard/gui/ideas_stall.py — locked wares with their why, takes of them refused, the star, the cut line said once, no shelf for a craft with one hero or none
- changed orkboard/realm/seat_rubric_rules.py — Run's rubric becomes traces, errors and slow places (§281.3)
- changed orkboard/realm/agent_rules_text.py — `table_text` says today's heroes and where each is offered
- changed orkboard/realm/lexicon.py — the heroes' names in TERMS (§278.7)
- changed orkboard/gui/static/js/table/partyseats2.js — `LEADERS` follows the catalog's defaults

### Out
- The Orkmaster reading the decisions before it routes (§281.7: goal 166, which edits `agent_rules_text.py` after this lands).
- The faces drawn in orkUI and the look of a locked ware and of the star (Design's section).
- A leader's rubric by the project's kind: `hero_of` stays kind-blind; a kind locks only what the stall offers.

### Risks
- risk: medium
- A hero's id is orkUI's file name: an id renamed after orkUI draws it falls back to the race's head unsaid.
- Six test files pin the cut ids, and the seat-rules baseline is written again: a careless rewrite hides a change to other rules.
- `project_kind` read wrong locks the wrong heroes (Talk's assumes); the person's `kind` correction is the mend.
- Goal 166 conflicts with this one if `agent_rules_text.py` is changed beyond `table_text`.

### Defaults
- New ids: `uni-pillar`, `uni-econ`, `uni-mda` (Game design's default), `dry-sprite` (Art's default), `dry-a11y`, `sh-scene`, `fairy-pos`; Lantern keeps `imp-obs`; Pillar has one `craft` and an `also`.
- A kind locks only what §279.5 names: Scene Shaman outside a game; Design's three in a backend, data, code, a wiki or texts; Store Gnome outside a mobile, web app or game.
- The star reads `project_kind` only (§278.5's lists are by kind; the stage adds none); kinds with no list get no star.
- *Said once* is kept in `<state>/heroes_cut.json` (`{party: hero id}`); Run's rubric has no signals, as it has no map.

### Accepted
- met: When the catalog is read, then it holds §278.2's and §279.1–2's heroes, Pillar Knight once at Product and Game design, six at most a craft, one default each but LiveOps, Run's Lantern Imp.
- met: When a party's page keeps a cut hero (uni-lean, dry-diamond, dry-atom, sh-ddd, sh-fit, imp-slo), then its first stall open names it cut and why, a second (a restart too) does not, its page and table unwritten.
- met: When a web app's Tech stall is asked to take Scene Shaman, then it is refused with the lock's why and the page keeps its hero; in a game it is a ware starred, and no star writes a `hero` key.
- met: When a Game design party takes Pillar Knight, then `hero_of` gives `uni-pillar` there as at Product, and the table it lays has Pillar Knight's four places, in order.
- met: When a LiveOps party's stall opens as a person first meets it, then it shows no hero card and no shelf, and Back to default is refused in words, not by an error.
