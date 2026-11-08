# 164. A craft's heroes work on what is built: fifteen heroes, a game's heroes, the Orkmaster's star marks, the role files say today's heroes

Goal: `llm-wiki/general/pages/ideas/164-a-crafts-heroes-work-on-what-is-built.md` (route: product, design, tech). The person's request is the page's *Gist*. This spec is the leaders' sections of that page as they wrote them in the Board's flow (Talk, then their sections), with the person's answers above them (decisions §278, §279, §281); each leader's *Talk* and *Accepted* stay in the page. **Builds:** the goal's stages (the page's *Stages*, the Taskmaster's), each task by a Grunt on the simpler model, in the branch `claude/stoic-newton-c85q7q`, into a pull request.

## The person's answers (8 November 2026)

1. Does the star seat its hero? — **Marks the ware only**.
2. When a party's hero is cut? — **Default seated, said once**.
3. How does Lantern Imp sit at Run? — **Run's default, no table**.

## Product

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

## Design

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

## Tech

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
