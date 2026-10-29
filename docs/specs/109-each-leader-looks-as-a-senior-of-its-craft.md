# 109. Each leader looks as a senior of its craft: the lenses measured against the field's frameworks

Decisions §184 (1–8). The owner, 29 October: *analyse every party leader's lens, compare it with the frameworks and ways
senior specialists use to review an architecture, a product, its marketing and the other crafts, adapt them to our window,
and build it.* **Builds:** Claude (the cheaper model builds, the spec's author reviews) · **Review:** full · P1. After
spec 108 (concerns on every map), on its rails: no new pane, no new column, no new call.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The rubrics** | each craft's framework as five or so *aspects*; the leader's look and Talk judge by them; a concern names its aspect; the record keeps the hints of code; the scorecard | new `realm/lens_rubrics.py`; `realm/concerns.py`, `core/idea_concerns.py`, `gui/ideas_concerns.py`, `realm/idea_objections.py`, `realm/lexicon.py`; new `tests/test_lens_rubrics.py`, `tests/test_concerns.py`, `tests/test_idea_concerns.py` (or where the look's tests are) |
| **B. The signals** | the hints of code each framework can ground, for every craft with a map (Art, Release and Marketing had none) | `realm/map_signals.py` (Tech, Design, Product, Game design), new `realm/map_signals_crafts.py` (Art, Release, Marketing), `realm/loop.py` (`findings_kinds`); `tests/test_map_signals.py`, new `tests/test_map_signals_crafts.py`, `tests/test_loop.py` |
| **C. The face** | the aspects as a row of chips on the strip, each in its state; a press steps through its cards; a concern's back names its aspect | `js/table/concerns.js`, `js/table/concerns.css`; `tests/test_concerns_desktop_browser.py` |

## 0. What the lenses are today, and what a senior of each craft would look at

Every party with a map has one (spec 102, spec 89), its text in the leader's calls, and since spec 108 a leader's look
that marks where it hurts. But the look is asked one question for every craft (*where is it wrong, at risk, or about to
hurt the product?*), so what it says depends on the model's mood, not on how the craft reviews its work; and only Tech,
Design, Product and Game design have hints of code. A senior in each field reviews by a known frame: a short list of
aspects, each with questions and signals. That frame is what this spec gives each leader.

| Craft · map | Today | How a senior reviews it | Gap | Taken here | Not taken (why) |
|---|---|---|---|---|---|
| **Tech · System** | C4-like containers and parts, links; hints: cycle, fan-in, fan-out, a big file, a shared part changed from many containers, churn with no test | **C4** (context, containers, components); **arc42**'s quality goals and **ISO/IEC 25010** (maintainability: modularity, analysability, modifiability, testability; security, reliability); **hotspots** (Tornhill, *Your Code as a Crime Scene*: change frequency × size); **Martin's stability metrics** (instability I = Ce/(Ca+Ce), the stable-dependencies principle); fitness functions; ADRs | hotspots are two separate hints, never one; no stability; security and reliability are never asked | aspects *Modularity, Coupling, Hotspots, Testability, Security and reliability*; hints `hotspot` (often changed and big), `unstable` (many depend on a part that itself depends on many) | ADRs and fitness functions as records (a later spec: the decisions are the Board's pages today); ATAM's workshop (a people's process) |
| **Design · Screens** | the screens along their flow, the pains pinned; hints: a screen nothing leads to, a dead end, no picture; the look reads the newest pictures | **Nielsen's ten heuristics** with severity; **WCAG 2.2 AA** (text alternatives, keyboard, labels, contrast, target size 24 px); task flows and journey maps; state coverage (empty, loading, error, success); design-system consistency | no state coverage; accessibility only by the pictures; consistency never asked | aspects *The way through, State and errors, Accessibility, Consistency, Seen*; hints `no_states` (a screen's file says nothing of loading, error or empty), `a11y` (an image with no `alt`, a press on a `div` or `span` with no role, an input with no label) | a full WCAG audit (a specialist's, §151.4 later); contrast by code (needs the rendered page) |
| **Product · Tree** | Torres' **opportunity solution tree**: an outcome, jobs (JTBD's sentence), the goals serving them, experiments; hints: an unserved job, pains piling | **OST** (outcome → opportunities → solutions → assumption tests); **JTBD**; **RICE/ICE** prioritisation; assumption mapping (desirable, viable, feasible, usable); North Star and its input metrics | an outcome that is no number passes; bets built with no test pass; goals in line that serve no job pass | aspects *Outcome, Opportunities, Evidence, Focus*; hints `vague_outcome` (the outcome holds no number), `no_evidence` (a job served by two goals or more and no experiment), `off_tree` (goals in line of the project that serve no job) | a RICE score per goal (asks the person for numbers we do not have; the leader weighs in words in Talk, spec 108 §4) |
| **Game design · Loop** | core, session, meta loops; each step's feeling (MDA's eight) and intensity; currencies; hooks D1, D7, D30; findings: no source, piles up, rewards nothing, unfed, flat | **MDA** and LeBlanc's eight kinds of fun; **core/session/meta loops**; **economy as sources and sinks** (Machinations); **flow** (Csikszentmihalyi: challenge rising with rests); retention hooks D1/D7/D30; design pillars | spikes in intensity pass; a missing first-day hook passes; a step resting on no file passes | aspects *Core loop, Economy, Pacing and flow, Retention, Grounded*; the findings by kind; hints `spike` (two neighbouring steps three or more apart), `no_hook` (no D1 hook), `unground` (a step that rests on no file) | player-type models (Bartle, Quantic Foundry: they need a player survey); design pillars as a record (the loop's line says the aim) |
| **Art · Assets** | lanes by kind, variants under the pick; no hint | an **art bible** (style, palette, a grid of sizes); the **asset pipeline** (names, folders, used or not); a **budget** (size per file and per kind); audio loudness (LUFS) | nothing by code at all | aspects *Style, Pipeline, Budget, Sound*; hints `mixed_sizes` (a folder of pictures with four sizes or more), `naming` (a name with a space or capitals among lower-case names), `heavy` (a picture or sound of 1 MB or more), `unused` (an asset no source file names) | loudness by code (needs decoding); palette extraction (needs pixels: Design's pictures are read by the model) |
| **Release · Dev and main** | goals in dev not in main, ticked; *To main*; *Since <version>*; no hint | **DORA's four keys** (deployment frequency, lead time for changes, change failure rate, time to restore); small batches; a **release-readiness** checklist (go/no-go); **semantic versioning**; *Keep a Changelog* | nothing by code at all | aspects *Batch size, Lead time, Readiness, Change failure*; hints `big_batch` (eight goals or sixty files or more wait), `stale` (a goal waiting seven days or more), `no_changelog` (dev holds no changelog), `reverts` (reverts in dev since main) | time to restore (needs incidents we do not record; Run's later map) |
| **Marketing · The way in** | channels → the store or the site → the install → the first session; no hint | **AARRR** (acquisition, activation, retention, referral, revenue); **ASO** (App Store title 30 characters, Google Play short description 80, screenshots); **positioning** (Dunford: alternatives, what is unique, value, who, the category); the Bullseye's channels | the way stops at the first session: retention, referral and revenue are never asked; nothing by code | aspects *Acquisition, Store page, Activation, Retention, Referral, Revenue* (AARRR with ASO in its store step); hints `no_channel`, `aso_title`, `aso_short`, `no_shots`, `no_onboarding`, `no_return` (no notification or push in the code), `no_share`, `no_revenue` (no purchase or payment library) | positioning as a record (a later map: it is the person's words, not the code's); the funnel's numbers (no analytics are read) |
| **Run, LiveOps** | no map | **Google SRE**: SLOs and error budgets, the four golden signals (latency, traffic, errors, saturation), runbooks, on-call; LiveOps: an events calendar, KPIs (DAU, retention, ARPDAU), remote config | no map, so no look | their rubric judges in Talk (§2.4) | the map of services and their SLOs, the events calendar: a later spec (§5) |

## 1. The word

**aspect** (`TERMS`: *aspect / aspects*): one thing a craft's senior looks at on its map (*Hotspots*, *Accessibility*,
*Economy*, *Retention*), with the question it asks. A concern names its aspect; an aspect is never a *check* (the gate's,
and the Checks seats') nor a *finding* (a check's).

## 2. Part A: the rubrics

### 2.1 `realm/lens_rubrics.py` (no face, no model)

```
lens_rubrics.RUBRICS[craft] = {"framework": str, "short": str, "aspects": ({"id", "name", "ask", "signals": (kind, …)}, …)}
lens_rubrics.rubric(craft)                       # the craft's rubric, or None (a craft with none)
lens_rubrics.aspect_of(craft, kind)              # the aspect a hint's kind belongs to, "" for none
lens_rubrics.prompt_lines(craft)                 # the rubric as lines for a model: "How a senior of <craft> reviews this map: <framework>." then "- <id>: <name>. <ask>"; "" for none
lens_rubrics.scorecard(craft, rec)               # [{id, name, ask, state, n, hints: [words]}] in the rubric's order, from a concerns record (§2.2); [] for none
```

`framework` is a line for the model, `short` the few words the strip shows (§4). The rubrics, as the table of §0 says
(the ids are code's, the names and asks the interface's and the model's):

- **tech** · *C4 · ISO 25010 · hotspots* · framework: *C4's containers and parts; ISO/IEC 25010's maintainability, security
  and reliability; hotspots, where change and size meet; the stable-dependencies principle* —
  `modularity` *Modularity* (Are the parts' edges clean: no cycles, no part reaching into many others?; `cycle`, `fan_out`,
  `unstable`) · `coupling` *Coupling* (Does a change ripple: a part everyone needs, a shared part changed from many
  containers?; `fan_in`, `shared_churn`) · `hotspots` *Hotspots* (Where is code both big and often changed, where bugs and slow
  work collect?; `big`, `hotspot`) · `testability` *Testability* (Is what changes often covered by tests?; `untested_churn`) ·
  `safety` *Security and reliability* (Does a part take people's input, secrets or money without a guard; is one part a
  single point of failure?; none).
- **design** · *Nielsen · WCAG 2.2* · framework: *Nielsen's ten usability heuristics, WCAG 2.2 AA, and the person's way
  through the screens* — `flow` *The way through* (Can a person reach every screen and finish what they came for?; `loose`,
  `dead_end`) · `status` *State and errors* (Does each screen show loading, empty and error states and say what happened?;
  `no_states`) · `access` *Accessibility* (Text alternatives, keyboard, labels, contrast and touch targets of 24 px or more?;
  `a11y`) · `consistency` *Consistency* (Do the screens use one set of words, controls and layouts for the same thing?;
  none) · `seen` *Seen* (Has each screen been looked at as a picture?; `no_picture`).
- **product** · *OST · JTBD · RICE* · framework: *Teresa Torres' opportunity solution tree, jobs to be done, and
  prioritising by reach, impact, confidence and effort* — `outcome` *Outcome* (Is the outcome one number the team can
  move?; `vague_outcome`) · `opportunities` *Opportunities* (Is every job served, and where do pains pile up?; `unserved`,
  `pains`, `pain_loose`) · `evidence` *Evidence* (Is a bet tested by an experiment before it is built big?; `no_evidence`) ·
  `focus` *Focus* (Do the goals in line serve the outcome, the best bets first?; `off_tree`).
- **game-design** · *MDA · loops · economy* · framework: *MDA and the eight kinds of fun, core, session and meta loops, an
  economy of sources and sinks, flow, and why a player comes back* — `loop` *Core loop* (Does every loop reward the player,
  and does each span feed the next?; `no_reward`, `unfed`) · `economy` *Economy* (Does every currency have a source and a
  sink?; `no_source`, `pile_up`) · `pacing` *Pacing and flow* (Do the intensities rise and rest, with no flat stretch or
  sudden spike?; `flat`, `spike`) · `retention` *Retention* (Is there a reason to come back on day 1, day 7 and day 30?;
  `no_hook`) · `grounded` *Grounded* (Does each step rest on the files that make it?; `unground`).
- **art** · *Art bible · pipeline · budget* · framework: *an art bible (one style, one grid of sizes), the asset pipeline
  (names, folders, every asset used), and a budget for what ships* — `style` *Style* (Do the pictures keep one style and
  one grid of sizes?; `mixed_sizes`) · `pipeline` *Pipeline* (Are files named and kept by one convention, and is every asset
  used?; `naming`, `unused`) · `budget` *Budget* (Are files light enough for where they ship?; `heavy`) · `sound` *Sound*
  (Do the sounds and music share one loudness and cover the game's moments?; none).
- **release** · *DORA · readiness · semver* · framework: *DORA's four keys (how often, how fast, how often it fails, how fast
  it recovers), small batches, a release-readiness checklist and semantic versioning* — `batch` *Batch size* (Is what waits
  for main small enough to ship and to take back?; `big_batch`) · `lead_time` *Lead time* (How long has done work waited for
  main?; `stale`) · `readiness` *Readiness* (Is the changelog written and the version said?;
  `no_changelog`) · `failure` *Change failure* (How often must a change be reverted or fixed again?; `reverts`).
- **marketing** · *AARRR · ASO · positioning* · framework: *AARRR (acquisition, activation, retention, referral, revenue),
  app store optimisation, and April Dunford's positioning* — `acquisition` *Acquisition* (Where do people first hear of
  it?; `no_channel`) · `store` *Store page* (Does the store page or site say who it is for and why, within the stores'
  limits?; `aso_title`, `aso_short`, `no_shots`) · `activation` *Activation* (Does the first session reach the moment the
  product is worth it?; `no_onboarding`) · `retention` *Retention* (What brings people back?; `no_return`) · `referral`
  *Referral* (Can people bring others?; `no_share`) · `revenue` *Revenue* (Where does it earn?; `no_revenue`).
- **run** and **liveops** (no map: Talk only, §2.4) · *SRE* / *LiveOps* · framework: *Google SRE: SLOs and error budgets,
  the four golden signals (latency, traffic, errors, saturation), runbooks* / *LiveOps: an events calendar, KPIs (daily
  players, retention, revenue per player), remote config* — run: `slo` *SLOs*, `signals` *Golden signals*, `runbooks`
  *Runbooks*; liveops: `calendar` *Events*, `kpis` *KPIs*, `config` *Remote config* (asks in the same plain words; no
  signals).

Every kind of §3 is in exactly one aspect of its craft (tested); `aspect_of` of an unknown kind is "".

### 2.2 The record and the parse (`realm/concerns.py`)

- A concern gains **`aspect`**: the leader's answer's `aspect` when it is one of its craft's aspect ids; else the aspect of
  the hint of code on its part (`aspect_of(craft, signal)`); else "". `parse(party, answer, parts, dismissed, hashes,
  signals, craft="")` takes the craft for it; `read` keeps `aspect` (a line of 40, "" when absent).
- The record gains **`hints`**: `[{on, kind, aspect, words}]`, the hints of code the last look was given (at most
  `map_signals.MAX_SIGNALS`), kept by `concerns_run` with the concerns. `read` keeps the well-formed ones.
- `scorecard(craft, rec)` (in `lens_rubrics`) gives each aspect its **state**: `alert` (an open concern of the aspect at
  alert), else `note` (an open one at note), else `hint` (a hint of code on the aspect the leader did not raise: code
  noticed it, the leader let it be), else `clear` (a look was made: nothing), else `unlooked` (no look yet: `rec.at` empty).
  `n` is the open concerns of the aspect; `hints` the words of its hints (three at most). A concern made into a goal is not
  open (as `counts`).

### 2.3 The look (`core/idea_concerns.py`)

The prompt gains, before the map, **the rubric** (`prompt_lines(craft)`): *How a senior of <craft> reviews this map:
<framework>. Judge by these aspects:* and the lines. A hint's line names its aspect (`- <words> [on <id>] (aspect
<id>)`). The rules gain: *Give each concern its `aspect`, one id of the aspects above. Look at every aspect, not only those
the hints name: an aspect with no hint can still hurt (security, consistency, sound).* The JSON example gains `"aspect"`.
The step, its tier, its reads, its context's cut are as they were (spec 108 §2.3).

### 2.4 Talk (`realm/idea_objections.py`)

`lens(craft)` ends with *, as a senior of it would: by <framework>* when the craft has a rubric, so a leader's verdict in
Talk judges by the same frame as its look (Run and LiveOps, which have no map, judge by theirs).

### 2.5 The command (`gui/ideas_concerns.py`)

Every concern command's record (`ideas.concerns` and the others, `_concern_reply`) gains `rubric`: `{framework, short,
aspects: scorecard(craft, rec)}`, `null` for a craft with none. The concerns carry `aspect`. Nothing else changes.

## 3. Part B: the signals

Each is grounded in what the map or the tree holds, read by code (dev's tree, git, the Board), no model; a hint that cannot
be read is no hint. `on` is a part's id as its map stamps it (`realm/map_parts.py`), "" for a hint of no part. The words
are a line in plain English for a model, as today's.

- **Tech** (`map_signals._tech`): `hotspot`: a part changed `HOT_TIMES` (4) times or more in the last `CHURN_DAYS` days whose
  longest source file is `HOT_LINES` (400) lines or more (*server/rooms changed 7 times in the last 30 days and holds
  rooms.ts of 520 lines*); `unstable`: a part used by `UNSTABLE_IN` (4) parts or more whose instability `uses / (uses +
  used_by)` is `UNSTABLE_I` (0.6) or more (*server/lobby is used by 5 parts and itself uses 9: what many stand on keeps
  changing with what it uses*). Order: after `big` and before `shared_churn`, as `ORDER` lists them.
- **Design** (`map_signals._design`; the screen's own file, at the ref, read once, at most `SCREEN_BYTES` 200 KB):
  `no_states`: a screen whose file names none of *loading, error, empty, spinner, skeleton, retry, fallback, catch*
  (case aside); `a11y`: a screen whose file has an `<img` with no `alt=`, an `onClick`/`@click`/`on:click` on a `<div` or
  `<span` with no `role=`, or an `<input` with none of `aria-label`, `aria-labelledby`, `id=` (a `<label for>` needs it) or
  `placeholder` (the words name the first found: *Lobby (/lobby): an image with no alt text*). A screen with no file read
  has neither.
- **Product** (`map_signals._product`): `vague_outcome` (`on` "": the tree's face stamps no outcome as a part) for each
  outcome whose text holds no digit; `no_evidence` on a job served by `EVIDENCE_GOALS` (2) goals or more of which none has an
  experiment (`tests`); `off_tree` (`on` ""): the goals of the Board's line (`goal_line.line`) not served to any job,
  when `pages` is given and there are `OFF_TREE` (3) or more (*4 goals in line serve no job: …* with three titles).
- **Game design** (`map_signals._game`): each finding by its kind (`loop.findings_kinds(data)` →
  `[(on, kind, words)]`: `no_source`, `pile_up`, `no_reward`, `unfed`, `flat`; `findings_on` and `findings` are read from
  it and say what they say today), then `spike` (two neighbouring steps of one loop whose intensities differ by `SPIKE` (3)
  or more, on the later step), `no_hook` (a loop is kept and no hook is `D1`; `on` the core loop's first step), `unground`
  (a step that rests on no file, when another step of the loop does: each on its step). These three are hints only: the
  map's *what the loop says* stays as it is.
- **Art** (`map_signals_crafts.art(state_dir, root, ref)`, from `art_map.read`): `mixed_sizes` (a folder of pictures, kind
  `art`, with `MIXED_SIZES` (4) different `w×h` or more, on its first picture: *sprites/ holds pictures of 5 sizes: 16×16,
  32×32, …*); `naming` (a file whose name has a space or a capital in a folder where most names are lower-case with no
  space); `heavy` (a picture of `HEAVY_ART` 1 MB or more, a sound of `HEAVY_SOUND` 1 MB or more); `unused` (an asset of
  Art's kinds whose file name no source file at the ref names: one `git grep -F -o -h` of the names, at most
  `UNUSED_NAMES` (200) names asked, the project's `code_map` source kinds and `.json`, `.html`, `.css`).
- **Release** (`map_signals_crafts.release(state_dir, root, pages)`, from `release_map.read`): `big_batch` (`on` ""):
  `BATCH_GOALS` (8) goals or more, or `BATCH_FILES` (60) files or more, wait for main; `stale`: a goal whose commit is
  `STALE_DAYS` (7) days old or more (its commit's time, `git log -1 --format=%ct`); `no_changelog` (`on` ""): dev holds no `CHANGELOG*`, `CHANGES*`, `HISTORY*` or `NEWS*` at its top while goals wait;
  `reverts` (`on` ""): commits in dev and not in main whose subject begins `Revert` (*2 changes waiting for main were
  reverts: …*).
- **Marketing** (`map_signals_crafts.marketing(state_dir, root, ref)`, from `way_map.read` and the tree's names; files'
  contents read only for the store's two texts and the code's `grep`): `no_channel` (`on` ""): the channels step holds
  nothing; `aso_title`: a store `title.txt` (or `name.txt`) of more than 30 characters; `aso_short`: a
  `short_description.txt` (or `subtitle.txt`) of more than 80; `no_shots` (`on` the first store file): store metadata and no
  `screenshots/` folder or image under it; `no_onboarding` (`on` the first session's file): no file named onboarding,
  tutorial, welcome, intro or walkthrough; `no_return` (`on` ""): no source file names *notification*, *push*,
  *daily reward* or *streak* (one `git grep -i -l -e … -q`); `no_share` (`on` ""): none names `navigator.share`,
  *share*, *invite* or *referral*; `no_revenue` (`on` ""): no manifest (`package.json`, `pubspec.yaml`, `Podfile`,
  `build.gradle*`, `requirements*.txt`, `pyproject.toml`, `Gemfile`, `go.mod`, `Cargo.toml`) names *stripe*, *revenuecat*,
  *purchases*, *billing*, *in_app_purchase*, *storekit*, *paddle*, *lemonsqueezy*, *paypal* (case aside).

`signals(…, craft)` dispatches `art`, `release`, `marketing` to the new module; every list stays bounded by
`MAX_SIGNALS`, each module under ~600 lines.

## 4. Part C: the face

1. **The aspects on the strip** (`concerns.js` `Strip`, under its line, the same strip): a row `.cn-aspects` (role
   `group`, label *What <the leader> looks at*), its first item the rubric's `short` in the muted caption, then each aspect
   an `.ork-chip` button `.cn-aspect` with `data-state` and `data-aspect`: a small mark of its state then its name —
   `alert` orkUI's alert sign in the alert tone, `note` the muted dot (as a card's), `hint` a hollow square in the muted
   ink (code noticed it), `clear` a small tick in the ink, `unlooked` nothing, the name muted. No count is drawn (§145.3);
   `aria-label` *Hotspots: 2 concerns* · *Hotspots: a hint from code* · *Hotspots: nothing wrong* · *Hotspots: not looked
   at yet*; `title` its ask, then the hints' words.
2. **A press on an aspect** steps through the cards whose open concerns are of that aspect, as a press on the counts steps
   through all (scrolled into view and lifted; picking wins). An aspect with no card (a hint of no part, or none) is pressed
   to nothing more than its `title`; it is a button only while it has a card (else a `span`, not focusable).
3. **The back of a marked card** names each concern's aspect beside its level: *Alert · Hotspots*.
4. The row wraps at the narrow width (no sideways scroll), every chip 44 px tall on a touch screen; orkUI's pieces and
   tokens only; nothing moves. A record with no `rubric` (an older host) draws no row.

## 5. Later (not here)

- **Run's map**: the services read from the deploy's files (`Dockerfile`, `docker-compose.yml`, `fly.toml`, `Procfile`,
  k8s manifests), each with its health check, its SLO kept by the person, its runbook (a file named for it), and the golden
  signals it exposes; **LiveOps' map**: the events calendar and remote config. Their rubrics are written here already.
- ADRs and fitness functions as Tech's records; positioning (Dunford's five) as Marketing's; design pillars as Game
  design's: the person's words, kept as the loop and the tree are.
- The specialists' concerns (spec 108 §5) take the same aspects (Security's, Accessibility's).
- Measured after a week: the concerns by aspect, made goals or dismissed; an aspect always dismissed is asked less.

## 6. Order and tests

A, B and C at once (they share no file; C is built against §2.5's shape with its stub host). Each keeps the critical tests
green (`tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`) and its modules' tests. A: every
craft's rubric well-formed, every signal kind of B in one aspect of its craft, `aspect_of`, `prompt_lines`, the scorecard's
five states, `parse` giving the aspect from the answer and else from the hint, the record keeping `hints` and `aspect`,
the prompt naming the rubric, `lens(craft)` naming the framework, `ideas.concerns` carrying `rubric`. B: each new kind on a
small git project made in the test (a hotspot, an unstable part, a screen with no states and one with an image with no alt,
a vague outcome, a job with two goals and no experiment, a spike, no D1, an unground step, mixed sizes, a heavy picture, an
unused asset, a stale goal, a revert, no changelog, a long store title, no revenue library), and none where it does not
hold. C: the row at both widths in each state, a press stepping through an aspect's cards, the back naming the aspect, no
row for a record without `rubric`, no sideways scroll.

## As built

- **A** (c05ca3a): `realm/lens_rubrics.py` (the nine crafts' rubrics, `aspect_of`, `prompt_lines`, `scorecard`); a concern's `aspect`,
  the record's `hints`; the look's prompt carries the rubric; `rubric` on every concern command; Talk's `lens` names the
  framework; `aspect` in `TERMS`.
- **B**: every kind of §3 but `unticked` (dropped: Release's ticks live only on the face, nothing records them, so it could
  never fire); `realm/map_signals_crafts.py` for Art, Release and Marketing; `loop.findings_kinds`. Narrower than §3 says, to
  keep the hints true: `no_return` and `no_share` match *notification*, *streak*, *daily reward*, a `push` that is no call,
  `navigator.share`, *invite*, *referral*, *share* as a word (a bare *push* or *share* is in nearly every file); `no_shots`
  accepts a `screenshots` folder anywhere (fastlane keeps it beside `metadata`); a screen's file shared by several screens
  or past `SCREEN_BYTES` is not judged; `unused` is not said where git cannot answer. A test keeps the rubrics and the
  emitted kinds the same set.
- **C** (9a71efe): the aspects as chips on the strip, each in its state, a press stepping through its cards; *Alert · <aspect>*
  on a card's back; no row for a record without `rubric`.
- **Not yet**: §5; at the narrow width the row takes two lines over the map.
