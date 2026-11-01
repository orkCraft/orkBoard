# 121. The day, the morning and the night: a sketch to touch on the phone, the night's work played in the morning, the work at night

Decisions §199. The owner, 1 November: *an indie maker has three jobs. Morning and evening: run my product, see that all is
well, and give feedback on it quickly and easily, through the lenses and Play. During the day: throw in my ideas, UI and UX
first of all, and have quick prototypes of them to touch. At night: all the work and the checks.* And before it: *during the
day, at the main job, you want to see mock-ups and prototypes first: how your ideas will feel in the product, what the look or
the music will be; in the evening you judge through the lenses whether it is a step in the right direction and nothing broke;
at night the building itself begins.* And: *a good enough idea may come by day that you want built now, and its result by
day, from the phone: that stays possible.* **Builds:** Claude (the cheaper model builds, the spec's author reviews) · **Review:**
full · P1. After spec 120 (a goal heard and thrown; the cards handed), spec 115 (Play's marks), spec 51 (Pick one).

**What it is, and is not:** for each of the three jobs the one thing missing. **Job 2, the day**: a goal that is seen or heard
gets a **sketch** before its spec is written: two or three throwaway variants made by its craft's leader (a screen as one HTML
page, a picture, a loop on a page), kept beside the goal, never in the project's code, touched and picked on the phone, the
one picked what the spec's *Will be* rests on. **Job 1, the morning and the evening**: the night's work is a card that opens
Play **on the screens each goal changed**; a mark costs no work by day; each leader says in a line, at its look, whether what
changed went toward its aims and what broke. **Job 3, the night**: one setting, **Work at night**, holds the building of what
was decided by day for the night's window, in Product's order, and **Build it now** on any goal held for the night starts
it by day, its result seen on the phone as its pictures (spec 85) and its ready card. Not: Play on the phone (a sketch is not the product: Play stays
the computer's, spec 112 §3.3); a sketch built into the project (it is thrown away once the work is done); music or pictures made
by a paid service without the person's word (§3.3); the leaders' voices (spec 122, later); a new pane, column or drawer.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The sketch, faceless** | which goals get one; who makes it; a page made by a call, pictures and sounds by a pick task; kept as a pick; the one picked read by the sections and the build | new `core/idea_sketch.py` (a mixin of `IdeaKeeper`, as `idea_talk.py` is), new `realm/sketches.py`, `realm/idea_pick.py` (the kind `page`, `by: "leader"`), `realm/media_sniff.py` (an HTML page), `realm/idea_target.py` (step `sketch`), `core/idea_ripe.py`'s end and `idea_hearing`'s *Do it* (spec 120: they lead to the sketch when there is one), `core/idea_sections.py` (the sketch in the sections' context), `realm/task_brief.py` (the sketch named in the build's brief), `realm/lexicon.py`, `realm/event_log.py`; new `tests/test_idea_sketch.py`, new `tests/test_sketches.py`, `tests/test_idea_pick.py`, `tests/test_media_sniff.py` |
| **B. The sketch served** | a page served in its own sandbox: no script of it reaches the Board, no request leaves it | `gui/media.py` (the page's own CSP), `gui/pwa.py` (`frame-src` for `/media/`); `tests/test_media.py`, `tests/test_pwa.py` |
| **C. Work at night** | the setting; what it holds and what it lets through; the night's order | `orkboard/settings.py` (`work_at_night`), `gui/ideas_board.py` (`autostart`), `realm/idea_risk.py` (`decide` with `held_for_night`), `gui/ideas_board.py` (`start_now` widened, its settings words), `gui/ideas_pick.py` (`now`); `tests/test_settings.py`, `tests/test_ideas_board.py` (or where `autostart` is tested), `tests/test_idea_risk.py` |
| **D. The morning** | what the night did, each goal with the screens it changed and their paths; Play opened on a path | `realm/board_recap.py` (`night`), new `realm/goal_screens.py`, `gui/ideas_assets.py` (`ideas.play {path?}`), `gui/play_proxy.py` (the first page asked at `path`), `gui/ideas_recap.py` (`ideas.night`); new `tests/test_goal_screens.py`, `tests/test_board_recap.py`, `tests/test_play_proxy.py` |
| **E. The evening line** | each leader's look says whether what changed since its last look went toward its aims, and what broke | `core/idea_concerns.py` (the look's answer gains `since`), `realm/concerns.py` (kept), `gui/ideas_concerns.py` (in the record); `tests/test_concerns.py`, `tests/test_idea_concerns.py` |
| **F. The faces** | the sketch's card and its variants on the phone and the desktop; the morning's card and *Play it*; the setting; the evening line on the strip | new `js/hand/sketchcard.js`, new `js/hand/sketch.css`, new `js/hand/nightcard.js`, `js/arena/play.js` (a path asked), `js/table/concerns.js` (the line), `js/settings.js` (the setting); `tests/test_design_system.py` (`SHEETS`), new `tests/test_sketch_browser.py`, new `tests/test_night_card_browser.py` |
| **G. The measures** | the events each job is measured by; hypothesis H2 | `realm/event_log.py`; `docs/hypotheses.md` (H2, written with this spec) |

## 0. What is there today

- **Pick one** (spec 51, `realm/idea_pick.py`, `gui/media.py`): a task of the plan may end with two to six variants (pictures,
  sounds, clips, texts of 4 KB), stored in the goal's state folder (`picks/<task>-r<round>/`, `pick.json`) and served by signed
  addresses (`/media/<goal>/<pick>/<file>?s=…`) to the page and to the paired phone; the person picks one with a note, or
  asks again. A variant is made **inside the work**, after the spec and the plan: there is no variant before a spec.
- **The phone has no Play** (spec 112 §3.3): its die says *Play it on the computer*.
- **Play** (spec 88, 115): the preview of dev's head through the host's proxy and its probe; **marks** on it make goals with
  the screen, the element, the errors, the requests; it opens at the preview's first page.
- **While you were away** (spec 42, `realm/board_recap.py`): what the Board did since a device's last look, as data: goals
  done, failed, flags met. Nothing ties a goal to the screens it changed, so nothing opens Play where to look.
- **The night** (`settings.IDEAS`: `night` *01:00–07:00*, `reserve_night`; `idea_risk.AUTOSTART`): a low-priority plan of low
  risk starts in the night's window; every other plan that may start, starts at once.
- **A leader's look** (spec 108–109): concerns on its map by its rubric's aspects; nothing says whether the last day's change
  went the right way.
- **After spec 120**: an agreed goal's wait ends in its sections; a hearing's *Do it* goes to its sections.

## 1. The words

New in `TERMS` (A): **sketch** / **sketches** (*a goal's throwaway variants made before its spec, by its craft's leader, to be
touched and one picked*; not *pick*, which a task makes inside the work, nor *mockup*, the word of the docs' own drawings).
The interface:
- The sketch's card: its face *<Leader> sketched it* (*From <Leader>*, spec 120 §6.9), the variants' names (*A*, *B*, *C* and
  the line the leader gave each); lifted: **Pick this one** (with *A note (optional)*), **Sketch again** (with *What to change*),
  **No sketch: go on**. While it is made, on the goal's back (spec 120 §6.3): *<Leader> is sketching*.
- A sketch that cannot be made: *No sketch: <why>* (*no Design, Art or Game design on the route*, *the media tools are not set
  up*, *the window is spent*), and the goal goes on to its spec.
- The setting (Settings, the Board's): **Work at night** — *What you decide by day is built in the night's window
  (<night>). Talk, hearings and sketches still run by day. A bug's short way, and anything you start with a press, starts at
  once.*
- On a held plan: *Waits for the night (01:00)* and **Build it now** (its cost said beside it: *about <gem>, from the
  5-hour window*); on a sketch's card, beside **Pick this one**, **Pick and build now**; on the morning's card: *The night: <n> goals in dev* (a count of what was
  done, not of what waits), each row *<goal> · <screens>* and **Play it**; *Failed: <goal>* with its reason; *Reverted*;
  *Checks red: <check>*.
- The evening line on a leader's strip: *Since your last look: <line>*, its mark *toward*, *away* or *unclear* as a word for a
  screen reader (`aria-label`), drawn as orkUI's signs (§6.4).

## 2. Part A: the sketch, faceless

1. **Which goals get one** (`sketches.wanted(route, how, types)`): a goal whose route has Design, Art or Game design, or whose
   types are a screen, art, a sound or a balance of the loop, **and** that is not the short way (a bug, a tidy) nor a pitch. The
   person can ask for one on any goal (*Sketch it first* on the goal's face, spec 120 §6.3) and turn it off for a goal (*No
   sketch: go on*). A project with neither preview nor screens nor assets gets none (nothing to sketch from).
2. **When**: in place of the sections, after the decision (spec 120's wait's end, a hearing's *Do it*, *Confirm and start*):
   the goal's state is `sketch`, then `sections` once one is picked or none is wanted. On the Orkmaster's lane the goal's back
   keeps its rune lit and its sketching leader's head glowing (one flame, spec 120 §6.3).
3. **Who and what** (`core/idea_sketch.py`), by the route's first craft that sketches:
   - **Design: a page** (step **`sketch`**, the party's tier, no tools, READS 0): one call, given the goal's words, its decision,
     Design's map text (`map_text`, the screens touched in detail), the project's look (the design tokens or the top stylesheet
     at dev, `sketches.look(root)`, at most 4,000 characters) and **the picture of the screen it changes** when one is kept
     (spec 85's shot or Play's, one image). It answers two or three variants, each `{name, why, html}`: **one self-contained
     HTML page** (inline style and script, no network, no external font), at most `PAGE_KB` (60) KB, drawn at a phone's width
     first. Parsed strictly; a page with an external `src`, `href` or `url(` to another origin is refused (§3.2 enforces it too).
   - **Game design: a loop on a page**: the same call, its page a small playable of the step the goal changes (a press, its
     reward, the currency moving), with no art.
   - **Art: pictures; a sound or music**: a **pick task** (spec 51) in a worktree, `pick: {n: 2–3, kind, ask, target}`, with
     the media tools, **only when the project has them set up** (spec 86's media tools); else *No sketch: the media tools are
     not set up*, and the goal goes on. A tool that spends money (a paid image or music service) is used only when the person
     said yes to it in Settings (spec 105's *paid*), never by default; its cost is on the card.
   - Several crafts on the route: one sketch, by the first; the others read it in their sections.
4. **Kept as a pick** (`idea_pick.store(…, by="leader")`, kind **`page`**: `text/html`, `PAGE_KB`, sniffed by its bytes as
   `media_sniff` sniffs the others): `picks/sketch-r<round>/`, `pick.json`, a variant's file `a.html`. **Never in the project's
   tree**, never committed: it is thrown away with the goal's state.
5. **Answered** (`ideas.pick` as today, the pick's `task` being `sketch`): **Pick this one** (`picked`, `note`) → the goal goes
   to its sections, **Sketch again** (`note`) → a new round given the note and the variants before (at most `ROUNDS` (3)
   rounds; the fourth is refused in words: *Three rounds: pick one or go on*), **No sketch: go on** → the sections.
6. **Read by the work**: the sections' context (`idea_sections`) gains *The sketch the person picked* — its name, the note, and
   for a page its HTML cut to 6,000 characters (a picture or a sound: its name and the line, not the file) — before the map;
   *Will be* is told to rest on it. The build's brief (`task_brief`) names the picked file's path in the goal's state folder as
   a reference to follow, not a file to copy. The sketch's cost goes to the goal's ledger as its *spec* stage.
7. **Events**: `sketch_made {idea, craft, kind, n, round, seconds, cost}`, `sketch_answered {idea, answer, round, minutes_since_goal}`,
   `sketch_skipped {idea, why}`.

## 3. Part B: the sketch served

1. A `page` variant is served by `gui/media.py` (the page's server and the phones' listener, signed as every file of a pick)
   with its own headers: `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';
   img-src data:; font-src data:; media-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'self'` and
   `X-Content-Type-Options: nosniff`. **Nothing it holds can reach the network**.
2. The faces show it only in an `iframe` with `sandbox="allow-scripts"` and **no** `allow-same-origin`: its origin is opaque, so
   its scripts never reach the Board's page, its storage, its token or its socket. The PWA's CSP gains `frame-src 'self'` for
   `/media/` alone.
3. Tested: the headers on both servers; a page asking an outside address loads nothing (a browser test with a page that tries
   `fetch`, an `<img src=https://…>`, a `<link>`); the frame cannot read `parent.document`.

## 4. Part C: work at night

1. **The setting** `work_at_night` (`settings.IDEAS`, the Board's, `False` by default; the onboarding asks it once, on the
   phone's first pairing: *Do you build at night?*).
2. **What it holds** (`gui/ideas_board.autostart`, `idea_risk.decide(…, held_for_night=True)`): a plan that would start by
   itself (`start`) **waits for the night's window** (`night`) instead; a plan the person starts with a press (*Start*, *Do it*
   of a hearing thrown, a held wait's *Start*) and **a bug's short way** start at once, as today. Talk, the verdicts, hearings,
   sketches and the leaders' looks run by day (they are the day's job and cost little). The plan's own `AUTOSTART` rules are
   unchanged: what waits for the person still waits.
3. **The night's order** (the runner's queue when the window opens): the goals held for the night by Product's `priority`
   (spec 120 §3.1), then their place in line; at most `max_parallel` at once, as today; a window spent stops the night as it
   does.
4. The held plan's card on the table: its back (spec 120's face-down card in its lane) and *Waits for the night (01:00)*.
5. **Build it now** (§4.2's rule kept: a press starts at once): **the day's case stays whole** (the owner, §199.4). Any goal held
   for the night has **Build it now** on its card, on the phone as on the desktop: **today's `ideas.start_now {slug}`**
   (`gui/ideas_board.py`, which already starts a plan held for the night and a task the reserve holds: the press is the
   person's), widened to a plan held by *Work at night*; it runs ahead of the night's queue. A goal still at its sketch has **Pick and
   build now** (`ideas.pick` with `now: true`: the pick answered, then its sections and plan, and the plan passed at once when it is made, unless
   `AUTOSTART` would make it wait for the person: then its *Start* is the hand's card, as today). Refused in words only for
   what refuses every start (a spent window, *Go on paid?*, Stop all). **Its result by day on the phone**: the goal's ready card
   (a goal ready for main is an entry of the phone's hand, §195.4) carries the pictures its tasks took (spec 85, `idea_shot`),
   the picked sketch beside the result's first picture (*Sketched · Built*), and its picks if a task made any; Play stays the
   computer's. Event `built_now {idea, from: "card" | "sketch", device}`.

## 5. Part D: the morning

1. **Each goal's screens** (`realm/goal_screens.py`, no model): `of(state_dir, root, slug, ref)` → `[{screen, name, path}]` the
   screens the goal's merged tasks changed: each changed file through `screen_map.screen_of`'s rule backwards (a screen whose
   component file is the file, or a file its component imports one level down, `code_map`'s links), with the screen's route
   path (`screen_routes`); at most four, the flow's order. None when the project has no screens.
2. **The night** (`board_recap.night(root, state_dir, since, now)`): the recap of spec 42 cut to the last night's window (or
   since the device's last look, whichever is later): goals that reached dev, each with `screens` (§5.1); goals failed with
   their reason; reverts in dev; checks red; Play's hints of the last play (`play_signals`) when there was one.
3. **Play at a path** (`ideas.play {path}`): the preview starts as today; its first page is asked at `path` (the proxy's
   address with the path) instead of `/`. A path no route has is refused in words before the start.
4. `ideas.night {}` (`gui/ideas_recap.py`) → §5.2's record for the face, `null` when the night did nothing.

## 6. Part E: the evening line

1. **The look's answer gains `since`** (`core/idea_concerns.py`; the same call, no new one): when its map changed since its
   last look, the leader says `{"since": {"way": "toward" | "away" | "unclear", "line": "…"}}`: whether what changed (the
   *Changed since your last call* lines it is given, with their goals) went toward what its craft keeps (Product: the tree's
   outcome; Tech: its aspects; Design: the way through the screens; and so on), and in the line what broke, if anything. One line
   of 200 characters at most; a `way` out of the three is `unclear`.
2. Kept in the concerns record (`since: {way, line, at, map_hash}`), shown until the next look. Product's look runs at the first
   opening of the evening (§2.3 of spec 108's rule: a changed map, a day old) as every look does.

## 7. Part F: the faces

1. **The sketch's card** (`sketchcard.js`): handed from the goal's back by its sketching leader (spec 120 §6.9). Lifted:
   - **on the phone**, the middle shows **one variant at a time at the screen's width**, in its sandboxed frame, scrolled and
     pressed as the real thing would be; **A · B · C** above it (buttons, never a sideways swipe: the frame takes the gestures);
     under it the variant's line, **Pick this one**, *A note*, **Sketch again**, **No sketch: go on**;
   - **on the desktop**, the variants side by side over the pane (as Pick one's tiles), each frame at a phone's width, the same
     answers; a picture or a sound as Pick one draws it today.
   - with *Work at night* on, **Pick and build now** beside **Pick this one** (§4.5), quieter than it: the night is the default.
   - The frame's page is drawn in its own look (it is the product's), the card around it in orkUI's.
2. **The morning's card** (`nightcard.js`): from the Orkmaster, the first card of the hand after the night's window when it
   did something; lifted: each goal as a row (its rune, its short name, its screens' names) with **Play it** (`ideas.play
   {path}` of its first screen, the die thrown as today); *Failed*, *Reverted*, *Checks red* rows with their reasons, each a
   way to its goal. On the phone **Play it** is *Play it on the computer*, and the rows stay. Answered by *Done* or by playing
   each; it goes when the next night comes.
3. **The setting** in Settings with its words (§1); the held plan's words and **Build it now** on its card (lifted on the
   phone's middle as on the table). A goal built by day's ready card on the phone: its pictures, *Sketched · Built* side by
   side when there is a sketch.
4. **The evening line** on the leader's strip (`concerns.js`), under the aspects' row: orkUI's signs for the way (*toward*: the
   check sign in the ink; *away*: the alert sign in the alert tone; *unclear*: the muted dot), the line in the body face. None
   when the map did not change since the look before.
5. Reduced motion, the narrow width, no sideways scroll as every face; the frames have `title` *Sketch A by <Leader>*.

## 8. Part G: the measures

Events (A, C, D): `sketch_made`, `sketch_answered`, `sketch_skipped`; `night_held {idea}`, `night_started {idea, at}`, `built_now {idea, from, device}`;
`night_card_opened {goals}`, `play_at_path {idea, path}`; and Play's own (`play_mark` with `minutes_since_open`). Hypothesis
**H2** (`docs/hypotheses.md`) is measured from them after the owner's week: a first sketch within 15 minutes of the goal; most
sketches picked, not skipped; most building in the night's window with *Work at night* on; from the morning card's opening to
the first mark under two minutes; fewer goals failed or reverted at night than by day.

## 9. Order and tests

A, B, C and E at once (they share no file but `realm/lexicon.py`, which A alone touches, and `realm/event_log.py`, whose
events each adds in its own lines); D after spec 120's B (the recap reads `heard`'s goals); F after A, B and D against their
shapes with its stub host. Each keeps the critical tests green (`tests/test_architecture.py`, `tests/test_board_alone.py`,
`tests/test_updates.py`) and its modules' tests. A: which goals are sketched (each craft, a type, the short way and a pitch
none, a project with nothing to sketch from none); the page's call parsed strictly (two or three, the size, an outside
address refused); Art's pick task asked only with media tools and a paid tool only with the person's yes; the rounds' bound;
each answer's way on; the sections given the picked sketch; the brief naming its path; nothing written to the project's tree.
B: §3.3. C: a plan held for the night and started when the window opens, in Product's order; a press and a bug's short way
starting at once; the setting off changing nothing; **Build it now** passing a held plan at once from the phone's
command list and the desktop's (`ideas.start_now`), ahead of the queue; **Pick and build now** answering the pick and passing the plan when it is
made (and leaving it to the person when `AUTOSTART` says wait); both refused for a spent window. D: a goal's screens (a component, a file it imports, none); the night's
record; Play asked at a path, a path no route has refused. E: `since` parsed and kept, `unclear` for a bad `way`, none without a
change. F: the sketch at both widths and on a phone-sized page (A · B · C, the answers, the frame's sandbox); the morning's
card with *Play it* opening Play at the path; the setting's words; **Build it now** and **Pick and build now** on a phone-sized
page; a ready card with *Sketched · Built*; the evening line's three ways.

## 10. What it changes

Spec 112 §3.3 (the phone has no Play: it still has none, but it plays a goal's sketches), spec 51 §2 (a pick is made inside the
work only: a leader's sketch is a pick made before the spec), spec 120 §3.5 and §4.3 (the wait's end and a hearing's *Do it*
go to the sketch when the goal has one), spec 42 §1 (the recap gains the night and each goal's screens).

## 11. Later (not here)

- **The leaders' voices** (spec 122): a hearing and a sketch's lines heard on the way, each leader its own voice on the device.
- A sketch of a marketing page or a store page (Marketing's) and of a sound by a free tool on the machine.
- A sketch kept as the screen's *before → will be* on Design's map (spec 104 §5), a ghost until the work lands.

## As built

Built by the cheaper model, a part a branch (B and C; D and E; A; F), each reviewed and merged by the spec's author on
`claude/leaders-lenses-system-55m0qp`.

- **A** (`realm/sketches.py`, `core/idea_sketch.py`, `gui/ideas_sketch.py`): `after_decision` is called by `confirm`, so the wait's end,
  a hearing's throw and *Confirm and start* all go through it. The step `sketch` runs on the elder tier at balance (warrior at thrift);
  Design reads one picture: the newest kept picture of a screen whose name is in the goal's words (no touches exist before the spec).
  *The media tools set up* is read as `task_commands.MEDIA`: pictures need python3, node or ffmpeg, sounds ffmpeg or sox (the owner's
  to confirm). Art's pick task runs in a scratch folder under the goal's state, not a worktree, once. No sketching craft on the route:
  a type that names one asks the project's first party of it; *Sketch it first* with none falls back to Design, Game design, Art. A
  first round that fails skips the sketch; a later one reopens the round before with its error and spends no round. Stop all puts the
  goal back at `decided`. A project with no look, screens, preview or assets gets none unless asked. The record is `sketch.json`.
- **B**: besides §3.1's policy a page gets `Content-Security-Policy: sandbox allow-scripts` first, so its address opened on its own
  keeps an opaque origin. `realm/sketches.outside` refuses outside addresses before the page is kept, character references resolved.
- **C** (`realm/night_order.py`): `work_at_night` is a Board setting (per project). Held plans reuse `start_at: "night"`; the clock's
  `older_night_plans` passes them when the window opens (a plan made inside the window starts at once). Only a press on the plan and a
  bug's short way start at once: *Do it* and *Confirm and start* lead to a plan that is held. `night_started` has no `at` field (the
  line's own). The onboarding's *Do you build at night?* is not done.
- **D, E**: `board_recap.night` takes the Board's rows, `into` and `hints`; `night_since` is the later of the night's start and the
  device's last look (12 hours back with no window). `ideas.play {path}` turns a route into a page's path (`:id` and `[id]` → `1`) and
  refuses a path no screen has; a Play already playing is answered at the path. The concerns record gains `head` (the commit a look
  read, so the next look is given *Changed since your last call*); Product, Marketing and Release keep no change log, so their line
  rests on the hash alone. A look of an unchanged map clears `since`. Play's last hints are kept in memory after Play stops.
- **F**: the setting is in `js/shell/settings.js`; *Waits for the night* and **Build it now** are on the hand's `plan` stop; the sketch is
  the pick card's lifted face (`kind: "pick"`, `task: "sketch"`), the variants over the pane on the desktop (`choose`, source
  `sketch`), one at a time at 56vh on the phone; *Sketch again* past three rounds is not offered. The morning's card is put first by
  `hand.js`; *Done* is kept per night in `localStorage`. The evening line is the desktop strip's only. The die (§200.5): `new_n` in the
  snapshot (computer only), pips 1–6 in the ink on the up face; at rest it stays the five until orkUI has `face-play`.
