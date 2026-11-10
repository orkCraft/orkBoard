# Decisions §45–§50: Orkboard's ground

Copied on 18 October 2026 from Orkline's `docs/design/decisions-2026-10.md` (orkWorks/orkLine, `main` at 163fea1f),
sections 45 to 50 as they stood when Orkboard moved to its own repository (docs/specs/37-board-and-line.md §9). They say
why the four windows — the Board with its goals, the preview, Agents and Review — became a tool of their own, and how
Orkline goes on from it. Orkline's file stays the record of the decisions before §45 and goes on after §50; the links
below that name `docs/design/…`, `docs/specs/…` (other than specs 33–37) or Orkline's code point into that repository.
A decision taken here from now on is added at the end of this file, numbered on from §50.

## 45. v1 is three buildings in plain windows; Camp waits, its art goes on (17 October 2026, the owner)

Why: the AgentCraft study (§37) shows a game image brings views (320k at launch) but not a habit (~200 npm installs a
week, 309 in Discord eight months on). Without the core working, a fun UI does not get far. So the first version is
the core, drawn plainly, and the owner tests it before anything else is built. A simplification (§27).

1. **v1 is three buildings:** the **Task board**, the **Agent pool** and the **Review gate**, shown as plain windows
   (Office's calm look, no camp map, no road graph, no animation). The person's path: an idea → the keeper's questions
   → the spec → the plan, passed on the board → the orks' work → the result, judged at the gate before it goes.
   External listeners and the Wiki are **not shown** in v1 (the idea pages still live in the Wiki, as §43.4 says).
2. **The phone first: three tabs, Board · Agents · Review** (the owner's sketch,
   [img/v1/phone-sketch.jpg](img/v1/phone-sketch.jpg), drawn as Board / Agents / Check). **The desktop shows the
   three at once as panes on one screen, left to right, as an IDE does:** Board | Agents | Review.
3. **The top bar, on every tab and pane:** what is left of the AI tools' limits, **the smaller of the window and the
   week** for each tool (Claude, Antigravity); a tap or hover shows both and when they reset. Beside it today's
   spend and **Stop all** (money and safety always visible).
4. **Board:** the goal (§44) at the top, **New idea**, the ideas in order, the person's to-dos. An idea's state is
   said in words (*new · reading · asks you · plan ready · working 2/5 · needs you*), not a badge. **A click on an
   idea opens its spec; a click on a to-do opens the plan the model wrote, scrolled to that to-do**, with one line on
   what it unblocks. **The plan is passed here, on the board** (§43.6). A secret to-do is entered only over the
   paired link, else *At the computer* (§43.8).
5. **Agents:** the orks grouped by role, each role with its tasks as chips: working · needs you · queued · done, in
   words beside the icon. A chip opens its task (what it does, its log, its spend, **Stop**). A waiting ork says what
   it waits on and leads to that idea. Roles keep **orkish names** (CLAUDE.md): the keeper is the **Taskmaster**, a
   worker is a **Grunt**, an image maker the **Alchemist**; a role the person makes keeps the name they give it.
6. **Review: only the results of work, before they go** (the plan is not here). Each result shows what changed, its
   tests (passed / failed, how many), what it cost, and its tasks. **Merge into `<branch>`** (default `dev`, the
   branch on the button) only when tests are green and nothing conflicts; red tests offer **Fix** (back to its task
   with the failure) and **Drop**, never a merge (§42). ✗ means **send back with one line why**; dropping is a
   separate button. Images are judged one by one (§39). The tab shows how many results wait.
7. **The testers' defaults:** a result merges into `dev`, never `main`, and nothing is pushed by itself (spec 29a's
   runner today merges into `main` and pushes: that stays the owner's setting only). The first start opens the three
   windows after the trust screen and the repository; **Mission 1 is not offered** (its code stays).
8. **Kept for later, by the owner's answers (not built until the three are tested):**
   - **Roles, models and limits are fully editable** (add an agent, edit a role: its model or tier, its parallel limit,
     its instructions). A new mechanic, so **a named exception to §27**. Each role a small file in the repository (seen
     in git, undone for free); three lean roles by default (§40); the waybill shows spend by role, so every experiment
     is measured.
   - **Image generation in the product (the Alchemist):** the owner uses it to finish the full Orkline, the camp and
     its orks drawn by Orkline itself. Off for testers by default. Cut by CLAUDE.md "Art" (once from the source, never
     re-pixelated).
9. **The product backlog is paused** (the owner): only what the three windows need is built; the owner tests them,
   then the rest. Everything else in specs/README.md waits, written specs included.
10. **Camp is frozen, not dropped; its art goes on.** The camp, the look switch and Mission 1 stay in the code (the
    full town behind `focus = ""`) and get no work: specs 17b, 20, 22, 23, 16, 14, 02 and 03 wait. **agy keeps
    making the art now** (the five buildings' sheets, the room kit), so Camp can be put in quickly once the core holds.
    18 and 19 are merged if they come back green.
11. **Dates stay (§22)**; **Halloween is dropped** (no decor, no Halloween post). Because Mission 1 leaves the first
    day, §27's first measure becomes: **of 3–5 testers, at least 3 take an idea of their own through to a merged
    result**; the second stays (**at least 2 come back within 7 days** unasked). After a week each tester is shown a
    screenshot of Camp and asked whether they would want it to look so: **two or more saying yes on their own** brings
    Camp back as the look over the working core.

## 46. v1 round 2: goals and ideas by dialog, straight to the model; agents by task type (17 October 2026, the owner)

From the owner's test of spec 33: (1) **a goal** is made in a dialog with metrics, a priority, links to documents and a
deadline, and **goes to the keeper at once** on saving; (2) **an idea** is a short text with **Process now** or
**Later**; closing the dialog with text saves it as Later; the keeper then fills its priority from the goal and the
rest; (3) **agents**: a role is a model and an instruction (and a limit), and each **task type** (code, tests, docs,
text for people, research) is assigned a role, or a new one is made from there; this brings §45.8's roles into v1 now;
(4) every dialog and menu opens on a dimmed backdrop; (5) a phone is paired from the shell (QR, Tailscale said
plainly). Spec 34. Improvements of v1's existing mechanics; the roles are §45.8's named exception to §27.

## 47. The Board does the writing; it starts what is safe; the Target picks the minds; the low work waits for the night (18 October 2026, the owner and the PM)

Why: after 34 the person still types what the model could write (a goal's title, metrics, links), and every idea waits
on the person three times (the talk, Take it to work, passing the plan) even when it is small and safe. The person's
time and the window's daytime share are what is short; the night's window goes unused. So:
1. **A goal is a description and a priority.** The keeper writes its title, its Summary as the context every idea
   under it starts from (the files it touches, what exists, the constraints), 1–3 measurable *done when* lines, and its
   links. On the elder tier: a goal is rare and everything below reads it. No goal-to-goal dependencies. This replaces
   the dialog of 34 §1 (its data stays readable).
2. **An idea is a text, a goal and a priority** (the person's). No idea without a goal: General stays only for what the
   system files (External listeners, calendar meetings, Mission 1). High and Normal are drafted **at once** into a
   full spec and plan; Low waits for **the night**. The 30-minute batch on the laborer tier (§43.3) goes.
3. **The spec, simpler:** Gist · Why · Done when · Out · Risks (product, tech) · Depends on (ideas of any goal) ·
   Stages · Open questions · Decisions. *In* and *Estimate* go (the price stays on Take it to work). The tasks are
   seen only in Stages: name, order, complexity, what runs in parallel.
4. **Autostart, on by default.** A plan starts by itself by its risk and its idea's priority: low risk starts (Low
   priority at night), medium risk starts only for High, high risk always waits for the person; Open questions always
   wait. The risk is the model's, raised by rules no model can talk down (secrets, data, CI, outward actions). This
   reverses §41.3 and §43.6 for what is safe: the Review gate after the work is unchanged and nothing merges into
   `main` or is pushed by itself (§45.7), so a wrong start costs tokens, never the code. For the testers it is one step
   fewer to §45.11's first measure.
5. **The limits:** nothing starts in a spent window; what starts by itself leaves the person a reserve of the window
   (30 % by day, 10 % at night); High goes first.
6. **The Target moves from the building to the Board's whole route** (§44.3): thrift · balance · quality picks the tier
   and the reasoning of every step, the keeper's and the orks'. A model the person picked for a role wins.
7. **The night** drafts the low ideas, starts what may start at night, reads again a goal whose files changed, and
   proposes **ideas, not goals** (the owner): two in balance, three in quality, none in thrift, never more than three
   waiting; a proposal has no spec until the person takes it, and a declined one is not proposed again.
8. **To-dos** carry their steps whatever their kind, and a new kind takes a **file**, kept like a secret (never in the
   repository, a page or a prompt).
9. **The Board's order:** the goals as a select with New goal and the Target; **Needs you** as one list (questions,
   plans, to-dos, failures, proposals), what blocks work first, then by priority; the ideas as one line each, a
   drafting one with a spinner and Stop, a night one with Process now and Delete.
10. **One call, one job, above all** (the owner's pain: long talks on ideas eat the context and the money). No
    session per idea: every keeper call is one shot, never resumed, given only what its job needs under a cap, with
    a bounded number of files to read and a money cap per call; the page is the memory and the talk never goes back
    to a model. One round of questions, answered together; after it the keeper decides and writes its assumptions
    into Decisions. A talk turn is an edit of one section, not a chat. This replaces §43.5.
11. **The specs are committed at every change to the work branch** (the owner: parallel orks must see each
    other's specs), from a detached worktree of the Board's own, so the person's checkout is never in the way.
    Two branches in the concept: **dev**, where the work and the specs land, and **main**, moved only by the
    person; the owner's repository works on `main` for now. This replaces §43.4's "the keeper never commits".
Improvements of v1's existing mechanics (§27). Spec 35.

## 48. Agents shows what each ork costs and how often it gets it right; Review's decisions are the signal (18 October 2026, the owner and the PM)

Why: the owner's ask (18 October). Agents is worth its place as the roles and what each does now; the money and the
quality of every step should be seen by goal, idea, task and ork; and the person's decisions at Review should tell the
product whether a result failed on quality or cost too much. Prioritised hard: the testers start on Friday 23, and spec
35 is being built on the same files.
1. **Agents is a monitor, not a settings page.** The roles and their live tasks, a task that needs the person first,
   leading to its Needs you item. The task types leave the window: an agent's dialog says which types it takes. A Grunt
   never asks in the middle of a task (§40, spec 35 §0's one round of questions): a task that cannot go on is a failure
   in Needs you, and the spec's quality is measured by how few there are.
2. **A role is who; the Target is how much thinking.** A role is a name, an instruction (at most 600 characters, as
   §40's personas), a limit and, if the person wants, a fixed tier; its model is *By Target* by default (the task's tier,
   shifted by the Target, as Grunt's). The effort always comes from the Target (spec 35 §1). No role gets an effort of
   its own: one dial moves the money, so the waybill can say what made a step dear, and the Target never says *Thrift*
   while an ork thinks at full effort. The raw model names leave the list (they repeat the tiers); a role file that
   names one still runs it.
3. **One currency: ≈$ at API prices** (on a subscription, a share of the five-hour window: §82), said plainly (*not
   your bill*; `sources/pricing.py`), never $0 for what is unpriced. What is left of a window stays in the top bar.
   Harnesses are compared once a second one runs roles; the tool and model of every run are recorded from now on, so the
   data is there by then.
4. **What is measured, goal → idea → task → stage → ork.** The stages: the goal's read (and its night refresh), the
   spec (draft, answers, talk), the plan, the work (round 1), the rework (the rounds after a send back), and what was
   dropped. Two numbers decide: **$ a merged result** and **merged the first time** (round 1, never in Needs you). The
   Taskmaster's number is the spec's: of its plans' tasks, how many finished without Needs you (target 95 %). The
   plan's estimate learns from the board's own runs (a tier's mean over its last 20 tasks, as the pool's
   `plans.tier_costs` did), so *over the estimate* means something.
5. **Review's decisions are the signal.** Send back keeps its one line (quality); Merge gets an optional *Cost too much
   for this* (cost); the card shows its cost against the plan's estimate. Nothing changes by itself on a signal. After
   the testers, the night turns repeated signals into proposals in Needs you (a line for a role's instruction, a
   lighter tier for a type of work), taken or declined as spec 35 §8's.
6. **Tools later, and as tools.** Making images is a tool (an MCP server, e.g. an image API on the person's own key)
   given to a role, not a harness that can draw: running Antigravity inside Orkline is §5's ban risk. After the
   testers, with the Alchemist (§45.8).
7. **Before the testers, two lines, both in spec 35:** every keeper event carries its step, tokens and cost, and every
   task's run its tool and model (the testers' week cannot be measured again later); and an Agents chip says what
   started by itself or waits for the night, and why a task is held (the limits or the person's reserve), since spec 35
   starts plans without the person. The rest is spec 36, after 35 is merged.
Improvements of v1's existing mechanics (§27); the roles stay §45.8's named exception. Spec 36.

## 49. Two branches and the gate between them; orks never on the same files at once; checks by paths (18 October 2026, the owner and the PM)

Why: the owner's flow (18 October). The person sees two branches only, **dev** and **main**: no pull requests, no
task branches. The orks' work lands in dev by itself when it holds; main moves only when the person passes it at the
Review gate. Prioritised hard, tokens above all: what paths and tests can decide, code decides; a model only writes
and fixes.
1. **Orks never work on the same files at once.** An idea claims its `touches` when its first task starts
   (`realm/claims.py`, written for the Agent pool and unused by the v1 runner); an idea whose paths meet an older
   one's waits for it. Conflicts are prevented, not merged: spec 35 §5 starts plans without the person, so two may
   run on the same files. In spec 35 part A (§5), before the testers.
2. **No messages into running sessions** about files that changed: a task is one `claude -p` run, a message would
   ride every later turn, and most changes do not concern it. A conflict is caught where it is today: at the rebase
   when the result lands, sent back with its files (`core/idea_runner.py`, `again["files"]`).
3. **No model looks for related specs.** The specs are on dev at every change (spec 35 §13); which ideas meet is a
   fact of their `touches` and `depends_on`, worked out by code (`claims.meets`): the draft gets the few ideas whose
   `touches` meet its own, a task gets the paths of at most three neighbouring specs. The Wiki stays for meaning
   (words, decisions), not for finding conflicts. After spec 35.
4. **Code lands in dev by itself** (`ideas.review` off): when its tests are green, it does not conflict, it touches
   no risk path its idea's risk left out (spec 35 §4) and it holds no media; else it waits in Needs you. No model
   reviews a task (§40: the tests are the review of code). After the testers, with item 5: their week keeps v1's
   result-by-result Review (§45.6).
5. **The Review gate is dev → main:** one card, *dev → main: N changes*, its report (the full suite, the browser
   tests, item 7's checks) and one press. Each result is a line of it with its cost against the plan, **Revert** (the
   quality signal, in place of Send back) and *Cost too much for this* (spec 36 §4's `dear`), so spec 36's two
   signals move with it. Spec 32's night gate (`core/night_gate.py` on `origin/dev`, written 17 October on a line that
   left main) is ported, not merged; its nightly model session that fixes dev waits for numbers on how often dev is
   red.
6. **Images, video and sound are judged one by one, before dev.** A result holding media does not land by itself: it
   waits in Review's **Look** row (Take · Another · Drop). The candidates live outside git
   (`<state_dir>/ideas/<slug>/candidates/`); only the one taken goes into the repository, cut once (CLAUDE.md "Art").
   No model looks at them; code checks size, format and alpha. The dev → main card says them in one line (*3 assets,
   taken 18 October*).
7. **Checks for what goes out are config, picked by paths, not by a model:** `.orkcraft/checks.toml` in the
   repository (`name`, `when` globs, `run`, `measure`, `compare = "main"`, `limit`). A short built-in catalogue
   (build size, bundle size, a benchmark, a document format lint) is offered once when a dev → main diff meets its
   paths; one click writes the line. Over a limit, *Pass to main* is off and says why. What goes to people (pages,
   mail, posts) stays §39's one-by-one look and waits for External listeners.
8. **Cut:** a model that orkestrates or reviews the orks' tasks; messages into running sessions; rebuilding the Wiki
   to find conflicts; a branch for assets; pull requests as the way (§42).
9. **Tokens, in spec 36 §6:** a task's prompt lists only the tasks it comes `after`, not every task before it in the
   plan (that list grows with the plan).
The order: spec 35 with item 1 → the testers → spec 36 A → **gate-kinds** (items 4–7, with spec 36's Review card) →
spec 36 B and C without the Review card. Item 3 rides gate-kinds or the Board's next round. Whether Orkline's own
repository moves to dev with item 4 or stays on main through the alpha is the owner's call. Improvements of v1's
existing mechanics (§27).

## 50. Orkboard and Orkline: one engine, three slices; the loop is the graph's unit; the game only reads (18 October 2026, the owner)

Why: the owner's plan (18 October). With specs 35 and 36 the four windows (the Board with its goals, the preview,
Agents, Review) are a whole tool. The owner wants it every day, at work and at home, on other projects, and to go on
building Orkline from what that use shows. Today the four windows live inside the town's code: about 12 800 of the
90 000 lines of Python are theirs (15 100 with specs 35 and 36), and the rest comes along through nine imports (`realm/jobs.py` runs a tool through
`realm/roads.py`; `realm/harnesses.py` and `realm/tiers.py` read the machine through `realm/builders.py`;
`realm/worktrees.py` reads the town's scroll; `gui/ideas.py` finds its Wiki among the town's buildings). The town
also has its own Agent pool and Review gate (`core/workers/barracks*.py`, `realm/gate.py`, `realm/team.py`, the road
engine) beside the Board's runner and review (`core/idea_runner.py`, `core/idea_review.py`), and its own building
windows (`gui/views/*`, `js/buildings/*`) beside the v1 panes (`js/shell/*`). Two engines: what one proves says
nothing of the other. So:
1. **Three slices, two products.**
   - **Orkboard:** the engine and its base modules (goals, ideas and their specs, agents, review; the Wiki under
     them) in one fixed loop, drawn as the v1 panes in Office's look, the phone included. The owner's lab, used every
     day on other projects; not published (§37.2 stands: the public name is Orkline). *Changed by §95 (25 October,
     the owner): Orkboard is published on its own, under its own name.*
   - **Orkline, Office:** the same modules, assembled by the person into loops (item 3); no game.
   - **Orkline, Camp:** the same graph with the camp's art and its game layer (item 5), for the first audience's
     evening (audience.md §2a): a clear switch from the day's job to one's own project.
   Office and Camp stay one product with two looks, switched by the shift (portrait.md §3). The name stays Orkline.
2. **One engine.** What Orkboard proves must hold in Orkline, so Orkline's nodes are Orkboard's modules: the Agent
   pool runs on the Board's runner, the Review gate on its review. The town's own pipeline (`barracks*`, `gate.py`,
   `team.py`) retires once those nodes stand on Orkboard's modules; what only it does (External listeners' read and
   reply paths, the `doc` path) moves over as modes. Never two copies: Orkline imports Orkboard's modules, never the
   other way round.
3. **The loop is the graph's unit**, not a free graph: sources → a goal → its track (the stations: the draft, the
   plan, the orks' work) → review → rework back into the track, or out to dev. Editing the graph is adding a loop, a
   station to a track, a source to a goal. Orkboard is one loop whose source is the person. A free graph is what
   scares the first audience off n8n (audience.md §1). The road engine may stay as the transport; the loop is the rule.
4. **A source has the person's contract:** it puts an idea into a goal. External listeners become sources attached
   to a goal, so their cards reach the goal they serve, not General.
5. **The game layer only reads.** The score, Renown, the stages and the missions subscribe to events (`core/bus.py`,
   the event log) and draw; they never change what the work does: no mission opens a feature, no reward moves a
   queue, and a mission that starts work does it through the person's own commands. So Camp is Office with a look and
   a reader, and what holds in Office holds in Camp. CLAUDE.md "One vocabulary, two looks" says so. The one exception
   today is Mission 1 (`core/mission.py`): it raises buildings, lays roads, makes the pool run no model (`drill.json`)
   and passes its own cart at the gate. It is frozen with Camp (§45.10) and moves onto the person's commands when Camp
   comes back. The score (`realm/score.py`) already only reads, but counts the town's results, not the Board's.
6. **The building windows are the panes.** In Orkline a click on the Task board, the Agent pool or the Review gate
   opens the same pane as in Orkboard, so Orkboard tests the interface too. Their `gui/views/*` retire with the
   town's pipeline (item 2).
7. **The contract between modules is written down now**, while there are four: what passes along each edge (a goal,
   an idea with its spec, a plan, a task, a result, a merge or a send back) and where it lives (the pages,
   `plan.json`, the event log); spec 37 §6. A setting that takes a step out (`ideas.review: false`, §49.4) is a loop
   without that node: in Orkline it becomes the graph's, not an `if` in the runner.
8. **The order:** Orkboard holds (the owner's daily use, the testers) → Orkline Office (the loops) → Camp. Camp's art
   goes on in agy meanwhile (§45.10). No graph and no game mechanic is built before the testers' numbers (§27, §36).
9. **Stage 1 now, in this repository (spec 37):** the boundary as a list of Orkboard's modules and a test that they
   import nothing of Orkline's (today's edges listed; the list only shrinks); the edges cut and Orkboard started on
   its own; the gate run on another repository's tests (its first need at work: today's gate knows only pytest and
   this repository's critical tests, and passes a result when no test file is found), its settings in a tracked
   `orkcraft.toml` at the repository's root (`.orkcraft/` is git-ignored, so §49.7's checks go there too). Nothing moves files while specs 35 and 36 are open on them. **Stage 2, right
   after Orkboard runs on its own** (changed the same day by the owner; first planned after the testers' numbers):
   Orkboard moves with its history to `orkWorks/orkBoard`, package `orkboard`; the state keeps its names, so both read
   the same settings and Boards. Orkline's copy stays frozen through the testers' week (a change lands in orkboard
   first), then Orkline depends on the package. Item 10 is built there. Spec 37 §9.
10. **Orkboard is a project's IDE** (the owner, the same day). It opens a folder as an IDE does (git started when
    there is none), keeps several projects open at once, each with its own Board, and shows one; it shows the
    project's files and its git: Markdown and code read and edited in place, the status, a file's diff, a commit, a
    branch, pull and push on the press. The goals, the ideas, the specs, the plans and the Board's settings (the
    Target, `merge_into`, the night…) are the project's, no longer the machine's. The orks still write the code; the
    person reads it, fixes small things, writes the Markdown and commits. What may hold a secret is never shown, and
    a Board page is edited only through the Board. Spec 37 §8, after Orkboard runs on its own.
Architecture and order, and for Orkboard the owner's named exception to §27 (item 10, as §45.8's roles); no new
mechanic in Orkline before the testers. Spec 37.

## 51. Operations: the person's everyday work by templates, across projects; a template checks with you until it may go by itself (18 October 2026, the owner)

Why: the owner wants Orkboard every day at work (§50), and most of a working day is small, frequent work that is no
code and belongs to no repository: a Jira task to file with its priority and epic, an email to answer. The Board's loop
(goal → spec → plan → orks in a worktree → the gate → Review) does not fit it: three or four calls where one is enough,
and the gate refuses a task that changes no file. Done by hand or in a chat with a skill, it has no queue, no check
before it goes and no memory of how the person wants it. So:
1. **Operations is the person's, one for all projects**, not a project's goal: its state in the person's folder
   (`~/.config/orkcraft/ops/`), never in a repository. The project's General is not renamed or touched: it stays the
   system's own place (spec 35 §2), and External listeners still go to the goals they serve (§50.4).
2. **A template is a Claude skill and a short form:** the skill's `SKILL.md` stays the person's and works in Claude
   Code as before; Orkboard's manifest beside it (`orkboard.toml`) names the fields asked at creation (a Jira task's
   priority and epic), the tools it may read with and the one tool that does its action. The person's own templates
   now (`~/.claude/skills/`); shared with a team later. Two built in: a Jira task, a reply to an email (saved as a
   draft).
3. **One job per call, as the keeper's (spec 35 §0):** a prepare that reads and changes nothing, the person's check,
   then an action allowed only its one tool, checked by code to have done exactly what was checked. Nothing outward is
   done twice by Orkboard.
4. **The way to by itself (the owner):** a template checks with you first; a check passed with no correction sends it
   by itself (after one, a setting); a correction makes it propose rules made general from it, and when the person
   takes them it goes by itself. A doubt of its prepare, a `high` risk or the day's cap still stops it at the check;
   **Not right** on what it did, a changed skill or **Check again** sends it back.
5. **What it reads stays the person's:** a mail's words and an issue's live only in the person's folder, its calls are
   kept there and not in a project's logs, and its texts go after 14 days.
6. **The template is the contract of a source:** when External listeners come (§50.4), a mail that came in fills the
   same form; what a source starts keeps the reserve (spec 35 §6).
A new mechanic before the testers' numbers: the owner's named exception to §27 (as §45.8 and §50.10). Spec 38.

## 52. The Map: a project's work on one screen; the preview becomes tabs; the skill tree is Camp's skin (19 October 2026, the owner)

Why: since spec 35 plans start by themselves and work goes on at night, and since spec 37 D several projects are open at
once; the Board still shows work as lists (Needs you, a goal's ideas, an idea's Stages). The owner wants to see a
project's goals, ideas and tasks and their links on one screen, as an RPG's skill tree (Diablo). The metaphor fits
the data, not only the look: a goal is a tree, an idea a skill, `depends_on` its prerequisite, a plan's tasks its
ranks (*working 2/5*), a plan's estimate its cost, the night's proposals the skills offered. So:
1. **The Map is a view, not a mechanic.** Read from what the Board holds (the pages, `plan.json`, the claims, the
   ledger) by `realm/board_map.py`; it changes nothing; its one action is *open*. Not a graph editor (§50.3): its shape
   is the goals and the ideas' `depends_on` as they are written. Named by what it does: *Map* (`TERMS` `board_map`).
2. **The preview becomes tabs**, as an IDE's (§50.10): the Map's tab first and pinned, every other thing in a tab that
   closes; one passing tab that a click replaces and an edit or a double-click keeps (VS Code's preview tabs); at most
   12; each project's tabs kept per device.
3. **The skill tree is Orkline Camp's skin over the same `ideas.map`** (§50.1, §50.5, §50.6): Camp's art, its *learn*
   the person's own Start, no points that open or move work. After the testers' numbers, or as §45.11's screenshot in
   place of the town's: cheaper art, and it shows the core.
4. **Measured:** the Map's opens per day, the first screen opened each morning, the share of ideas opened from it
   (`opened` gains `via`).
A view of existing data: an improvement of v1's existing mechanics (§27); the Camp skin waits as §50.8 says. Spec 39.

## 53. Orkboard is drawn in orkUI; an agent's craft is its race, its tier the gear on its head (19 October 2026, the owner)

Why: the page and the phone were drawn in the old design system's Office theme on top of Orkline's twelve Camp sheets
(the town, the yards, the kit), with its warm browns, a gold accent and four faces; orkUI (github.com/orkWorks/orkUI) is
now the design system of orkWorks' products, its first look *office*. And Agents said who works only in words: a role's
name and a model, never what kind of work it does. The owner: rebuild Orkboard on the new design system, and show an
agent's role and tier with the mascots, **orks the engineers, elves design, goblins data, gnomes marketing**. So:
1. **One look, orkUI's office**: dark, monochrome, dense; IBM Plex Mono for text, Pixelify Sans for headings and
   buttons; nothing round; selected raised with a 2 px ink bar; every arrow and icon a pixel mark. orkUI owns its tokens
   (`--ork-*`) and components (`.ork-*`); Orkboard's sheets read them and carry no colour, font or corner of their own.
2. **A copy, never edited here**: `design-system/orkui` is orkUI's `office/` with its licence, stamped in `ORKUI.json`
   (orkUI's version, commit, every file's hash) and refreshed by `python -m orkboard.design.orkui <orkUI>`. A copy, not
   a git submodule: the wheel, `uv tool install` and CI need nothing more than this repository. A change to the look is
   made in orkUI first.
3. **What leaves**: the old tokens, components and kit with their four faces; the twelve Camp sheets the page loaded;
   the phone's light Office (office is dark only), its fence, tiles and dock. The Camp skin stays Orkline's (§50.5).
4. **The pixel face never for a person's words**: a goal's or an idea's title, an agent's name, a Markdown heading, a
   file's name stay in the text face; headings, labels, buttons and tabs are the pixel face's.
5. **Colour means a signal** (danger, alert, success), except the one ork green of the primary action and the muted
   heads of the races; waiting is not a signal (`wait` reads as muted ink).
6. **An agent's craft is its race**: a role is engineering, design, data or marketing (`craft` in its file), drawn as
   orkUI's head of an ork, an elf, a goblin or a gnome. Taskmaster and the Grunts are orks, always (CLAUDE.md: orks by
   their orkish names); a role written before crafts is engineering. orkUI's knight and lich wait for a craft of their own.
7. **Its tier is the gear on its head**: a novice bare, a seasoned in iron, a veteran hooded. A role wears its own tier
   (or its hand-set model's); By Target, the tier the Target gives it now; a task, the tier it ran at (before it ran, the
   tier it will run at). The tiers are said in today's words everywhere, the model list too (*Veteran · opus*).
8. **A head is an accent, never a picture** (the owner): 24 × 22 beside an agent's name, 12 × 11 (a pixel a cell) in a
   chip, a plan's task, the Map's tasks, a task's Tier line; its words beside it or in its title. The Agents tab is an
   ork's head; a goal's mark is a flag.
An improvement of v1's existing mechanics (§27): the look and the words of what is there, one new field (`craft`).
Spec 40.

## 54. The phone, round 3: what waits for you is the signal, a name fits its chip, a question comes with its answer picked (20 October 2026, the owner)

Why: the owner's notes after a day on the phone. The top bar's ! repeats the Needs you tab's count and never says
whether work stands still; the project switcher, the gear and the Board's heading and Target row take the room the goal's
name and the limits need; goals' and ideas' names are cut on the Map; starting a plan takes two screens; Speak sits on
the Board unused; New goal is three screens for what is mostly a default, and a goal's team cannot be changed on the phone
once it is made; Add agent only makes a new agent; an agent's line spells its model in words; the questions' likely
answers are seldom the ones taken. So:
1. **Needs you is the signal**: orkUI's warning mark and colour while something waits for an answer — a
   question, a plan to start, a to-do, a failure, an Operation's check —; a plain count while only results wait in
   Review. The top bar's ! goes. Colour means a signal (§53.5): a result waiting for a look is not one.
2. **The top bar holds the goal and the limits**: the menu at its left opens the drawer (Stop all, today's spend, the
   projects, this project's settings with the Target, this phone's); the gear and the Board's heading and Target row go.
   A setting sits with what it sets: the phone's and the project's in the drawer, a goal's in Edit goal on its screen.
3. **A short name**: an idea, a goal and a task carry `short` (24 characters at most), written by code when it is made,
   then by the call that writes its title anyway (the draft, the plan, the goal's reading): no model call more. A chip
   or a tab shows it on two lines; the title stays on its screen.
4. **The Map gets one action beside open** (amends §52.1): a node that waits for the person alone — a plan whose ideas
   it depends on are done, a plan held for the night, an idea held for the night — has one button, with what it costs.
   Nothing is skipped from the trail but a check (spec 39); a task of code never, the next ones build on it.
5. **New goal on one sheet**: what it is for, the craft as a row of heads, the team folded to one line with Change (its
   bands in folds, one open at a time), the checks, Save always in sight. A goal's team changes from its screen.
6. **Agents**: Add agent takes one from the library or makes your own; an agent is one line — its head (the race its
   craft, the gear its tier), its name, how many at once, about what a task costs —; the Taskmaster and the Grunt say
   what they are told already beside the field that adds to it.
7. **A question comes with its answer picked**: the Taskmaster gives each question its choices, the one it recommends
   and why; the recommended ones are pressed, so one Send takes them, and *Let the Taskmaster decide* takes them unread,
   written in the spec's Decisions as its pick. Measured: how many answers are a choice, the recommended one, typed, or
   left to it — the research the owner asked for, before the next change to how it asks.
8. **Not done, and why.** *A goal stays a goal*: it has metrics, a flag and a verdict, and the Map's trail runs to that
   flag; a line of work by kind is the goal's craft, so goals may be grouped by craft, never renamed back to tracks
   (`track` is the word `goal` replaced, `TERMS`). *No sideways scroll of ideas*: it hides what is past the edge and
   breaks the trail's order; the trail packs tighter instead. *No token multiplier on an agent*: a person has nothing to
   hold it against and a token's price differs by model; dollars a task say it. *No new leader for delivery*: spreading
   the work across goals is the Taskmaster's (priority, autostart, how many at once, the limits); a release is an
   Operation's template (spec 38), a spec of its own when wanted. *No tool mark on an agent* while every agent of the
   Board runs on Claude Code (`core/idea_runner.py` `HARNESS`).
An improvement of v1's existing mechanics (§27): the look, the words and the order of what is there; two fields
(`short`, a question's `pick`), one command (`ideas.role_add`), one flag (`ideas.answer`'s `decide`). Spec 41.

## 55. Coming back: the Board says what it did, not only what it costs; the game only reads, and rewards results and thrift (20 October 2026, the owner and the PM)

Why: a product manager's review (20 October). The Board says loudly what it costs, what waits and what failed (the
spend, the limits, Stop all, Needs you's warning) and quietly what it did: a merged result goes into *Done (n)*, the
night's work is said nowhere (`night_run` and `night.json` are read by no face), an accepted goal is a flag of another
colour. The only reason to open it is Needs you, a duty, and that reaches the phone only while its page is alive (no
`push` handler in `pwa/sw.js`, no producer of the phone's `news`) and the desktop never. AgentCraft (§37, §45) showed
that a game's picture brings views, not a habit; what brings a person back is their own work, seen. So, a game layer
that only reads (§50.5):
1. **It rewards results and thrift, never volume or spend:** merged, merged the first time, $ a merged result, a
   goal's flag, a template that goes by itself. No points, levels, badges, leaderboards, sounds or confetti, and no
   streak of the person's: a day away costs nothing. The one run it counts is the Board's own (nights in a row with
   work done), kept by adding ideas, which is what the Board needs.
2. **Said once, in one place, closed by one press:** a card shows when it has something to say and not again; nothing
   pops over the work; a mark that moves moves once, and never under `prefers-reduced-motion`.
3. **Eight pieces, built in this order:** (A) *While you were away*, the card of what the Board did since this device's
   last look; (B) the flag raised once when a goal is accepted, with its tally, and *Flags*, the goals met; (C)
   notifications on the paired phone (Web Push from the desktop, no server of ours and no app store) for an answer that
   waits and the morning's summary, and Needs you's count on the app's icon; (D) an agent's record in its dialog (its
   line stays §54.6's); (E) a template's way to by itself as progress (*2 of 3 clean checks*); (F) this week's work
   beside the limits (≈$ at API prices, the results, what the nights did, *Nothing waits for tonight*); (G) *Last week*,
   a card on the first look of a week; (H) nights in a row, said only where A, F and G already speak.
4. **Measured:** each piece logs when it is seen and what was opened from it (`via`), read against §45.11's second
   measure (two come back within seven days unasked) and §52.4's first screen of the morning.
The owner's call: all eight now, before the testers' numbers: a named exception to §27 and §50.8 (as §45.8, §50.10 and
§51). Views of existing data, but C, which is how a question reaches the person, and two counters (`done_alone`,
`alone_since`) in a template's trust. Spec 42.

## 56. A goal's party is measured: a check says what it found, the party's work is shown, its price is seen before it starts (20 October 2026, the owner and the PM)

Why: a product manager's review (20 October). A goal's party is a deck-builder at heart — a library to pick from, a
craft, seats (one leader, three builders, two checkers), a party of each craft to start from, a checker's check that
holds every idea of the goal to it — and that is the right game for Orkboard, because the choice is the work's own:
what a goal costs against how carefully it is done. But it is half a loop: a party is picked once, and nothing says
afterwards whether it was a good one. Worse, a check cannot say "nothing found": a check task that changes no file
fails at the gate (`core/idea_task.py`: *You changed no file*), so a clean check is a failure in Needs you or a file
made to pass. So:
1. **A check says what it found** (`findings`, in a file the runner reads and never commits): none is clean and passes
   without a change; what it fixed goes through the gate as any work; what it left goes to Review, whatever
   `ideas.review` says, with *Fix them* and *Leave them*. The engine's one change here; the rest only reads.
2. **What the party did**, on the goal's screen and under its flag: each member's tasks, merged the first time and $;
   each checker's ideas checked, clean, caught, left and $.
3. **A party's price before it starts**, while it is picked: *about $2–4 an idea*, and what each check adds, from the
   project's own ideas once there are enough, a first guess before.
4. **What a check is worth**, in its agent's record (spec 42 D), and the night's one proposal from it: a checker that
   found nothing in the last eight ideas of a goal is proposed to leave that party, taken or kept by the person (as
   §48.5 means the night to turn signals into proposals; the first of them).
5. **Hints while picking**: at most two quiet lines (a check that seldom applies to the goal's craft, no builder for its
   code, a check that has found nothing lately); never a block.
6. **Your parties** (the owner, the same day): a party saved from a goal's screen and picked again for a goal in any
   project, kept in the person's folder as Operations are (§51.1), never in a repository; an agent of the person's own
   travels inside it and is installed where it is missing, never over a project's; a saved party's record is its
   goals, its projects and its flags.
Not a game's words: no cards, decks, mana or rarity in what a person reads (CLAUDE.md: everything by what it does); no
agent unlocked, no tier raised by use, no party ranked against another's. Built after spec 42, before the testers'
numbers: the owner's named exception to §27 (as §55). Spec 43.

## 57. Low work spends the week's room: by day when the week is ahead of its pace, at night when it is not behind (20 October 2026, the owner and the PM)

Why: the owner's idea (20 October): start waiting work while a window has room that would otherwise be lost. Today Low
work waits for the night whatever the week says (`realm/idea_risk.py` `AUTOSTART`: low risk, Low priority → night), and
at night it may spend down to 10 % of the smaller window (`idea_target.reserve`), the week's too: a tight week is spent
at night on Low work and High work finds nothing the next day; a loose one ends with its room unused. Normal work of
low risk starts at once already, and work of medium or high risk waits for the person on purpose. The week is the
budget; the five hours are a rate that comes back. So:
1. **One rule in place of "Low at night":** what the Board itself put off to the night (a Low idea's draft, a Low plan's
   start) goes **by day when the week is ahead of its pace** (its share left at least 10 points above the share of the
   week still to come) and **at night when the week is not behind** (its share left at least the share to come). What
   the person put off (*Tonight*) stays the person's: the night, as today.
2. **The five hours only ease the reserve:** within the hour before the five-hour window comes back, and while the week
   is not behind, the day's reserve on that window is the night's.
3. **Only "when", never "whether":** risk still decides what may start without the person; no forecast of a burn rate
   (whole percents read every ten minutes, and the person's own use in the same window, make it noise): a straight
   line from the week's reset is the pace.
4. **Measured first among it:** the week's share left when it resets (`week_reset`), said in This week (spec 42 F) as
   *Last week ended with 30 % unused*; if weeks end spent, the rule mostly holds Low work at night, which is its other
   use.
Improvements of v1's existing mechanics (§27): the same autostart, the same reserve, read against the week. Spec 44.

## 58. A tool that is not signed in opens its own sign-in at once; the work that needs it waits for it (20 October 2026, the owner)

Why: the owner (20 October): when Claude Code's sign-in fails, Orkline only says so (*Sign in again in a terminal:
claude, then /login*), and the task that hit it is failed. The person has to find a terminal, sign in, maybe in another
config folder than the one Orkline's runs use (`tool_errors.claude_sign_in`), and then start the work again by hand.
Every tool Orkline runs has its own sign-in; Claude Code (`claude auth login`) and Codex (`codex login`) open the
browser by themselves and take the answer back without a terminal (checked on 20 October: 2.1.304, 0.163.0). So:
1. **The sign-in opens at once**, for every tool: in the browser for a tool that signs in there by itself, in a terminal
   window opened with the tool for one that signs in only inside its own session (pi's `/login`). Orkline starts the
   tool's own sign-in with its own environment, so the sign-in lands where its runs look; it never sees a password, a
   code or a token.
2. **Only when someone is at the computer's page**: at once while the person uses Orkline, else the moment they come
   back to it; never on a phone, and never into a browser no one answers at night. At most once by itself for each
   time a tool needs it; *Sign in* opens it again any time.
3. **Never when a sign-in cannot help**: a key in the environment the tool takes first, another Claude Code renewing
   the sign-in; the line says what to do, as today.
4. **The work waits for it instead of failing**: what ran by itself (a task, a draft, an operation's run) is held for the
   sign-in, as a spent window holds it, and goes on by itself once the tool is signed in; at most a day.
Improvements of v1's existing mechanics (§27): the same failure, the same hold, with the tool's own sign-in. Spec 45.

## 59. A goal's trail: its party asks with its leader, its leader lays out its ideas as proposals, the desktop catches up with the phone (20 October 2026, the owner)

Why: the owner, after the phone's round 3 and a look at the desktop. A goal is read and asks its questions, then its
Map is a flag with nothing on the way to it: its ideas come one by one from the person, or two a night (balance) from
the proposals, never more than three waiting. Its party (§56) is picked for the goal and says nothing until the work:
the goal is read by its leader alone, whatever its designer or its reviewer would have asked. And the desktop is behind
the phone: New goal is a plain button under the goal's select (the owner could not find it), three steps where the
phone has one sheet; what waits for an answer hides in a tab behind the Board while Review, not a signal (§54.1), keeps
a column of its own; the Map has no button. So:
1. **The party asks with its leader, in the one round** (spec 35 §0 stands): in balance each member's view is in the
   leader's read (no call more); in quality each member asks first, by itself, without tools, cheaply; the leader keeps
   at most three questions (five in quality), each with the head of who asks. Not every agent asking its own: up to six
   reads of the repository a goal and eighteen questions, which the person would answer with *Let the Taskmaster
   decide*; a trail is as good as the person's answers, not as the number of askers.
2. **The leader lays out the goal's trail** once its questions are answered: up to 3 · 5 · 7 ideas by the Target, in
   their order with what each waits for, as **proposals**: no spec, no draft, no money until the person takes them;
   *Take all* drafts them one at a time. A checker's check is an idea of its own only where the work it checks needs
   one. By itself only for a goal with at most two ideas; *Lay out ideas* on the goal's screen any time after.
3. **An idea the person adds joins the trail**: its draft says which of the goal's ideas not drafted yet wait for it, and
   which proposal does the same thing; nothing is removed on a model's guess.
4. **The desktop catches up**: New goal on the Map's head and in the goal's select, on one sheet; Needs you, with Review
   under it, is the right column (Board · Files on the left; below 1 024 px the phone's three tabs); the Map's one
   action. Not the phone's top bar and drawer: the desktop has the room.
5. **Measured**: the trail's ideas taken, turned down (and why) and merged within 14 days; the members' questions
   against the leader's, by how they are answered (§54.7's research); what a goal costs to read and lay out, by Target.
Improvements of v1's existing mechanics (§27): the goal's read, the night's proposals, the draft, the Map, and the
phone's look on the desktop; two keeper steps (`ask`, in quality only; `trail`), no new setting. Spec 46.

## 60. One product and its labs: Orkboard, OrkWiki and OrkWatch crystallise Orkline's buildings; a building's mechanic is the shape of its work (21 October 2026, the owner and the PM)

Why: the owner (21 October), on the studio's positioning: a line of products on Orkline's engine, each joining a game's
mechanic to a problem of orkestrating agents. Orkboard, a card game: planning and following the work of several agents.
OrkTower, now **OrkWatch**, an idle game: mail sorted, replies drafted, events made in the calendar. OrkWiki, the links
of Mini Metro and Mini Motorways and their quality: an LLM wiki kept true, fresh, linked, placed by its rules and free
of contradictions. Orkline, Factorio: loops built and tuned for every kind of request, the person in them as little as
possible, the others in one line. The PM's review the same day: a strong thesis where the game's loop is the work's own
(as §52 and §56 found); a weak plan if it is four launches (four audiences for one person, and a skin is copied in a
weekend, as AgentCraft took its image first, §37); and parts of it against §37.1, §50.1, §55 and §56. The owner: not
four launches, one product and its labs. So:
1. **Orkline is the product; Orkboard, OrkWiki and OrkWatch are its labs.** Each crystallises one of Orkline's buildings
   on its own and checks that it is needed: the owner uses it every day, its shape and its words settle, its contract
   with the other modules is written (§50.7); then it enters Orkline ready, as that building, never a second copy (one
   engine, §50.2). A lab is not published (§50.1, for each), and the public name stays Orkline (§37.2). *Changed by
   §95 (25 October, the owner): each building's product is published on its own, under its own name.* A lab may end in
   *not needed*: a building no one turns out to need does not enter Orkline.
2. **The labs and their buildings:**
   - **Orkboard:** the Board with its goals, Agents and Review, which are Orkline's Task board, Agent pool and Review
     gate (§50.6).
   - **OrkWiki:** the Wiki (Camp's Scroll Dump) with its librarian, its Quality checks and its Rules for AI tools
     (Orkline's `docs/design/wiki-librarian.md`, `docs/design/wiki-folders-rules.md`; here `realm/wiki.py`,
     `realm/wiki_rules.py`): a wiki that people and models write and agents read stays true, fresh, linked, placed by
     its rules and free of contradictions.
   - **OrkWatch:** External listeners (Camp's Watchtower, `TERMS` `watchtower`) with Operations' reply to an email
     (§51): mail sorted, replies saved as drafts, events proposed for the calendar; nothing sent until its template may
     go by itself (§51.4).
   - **Orkline:** the factory that lays them into loops (§50.3), the person in them less and less (item 6).
3. **The order: Orkboard, then OrkWiki; OrkWatch is decided after.** Orkboard holds first (§50.8: the owner's daily use,
   the testers). OrkWiki is the next lab: its mechanic fits its work best (item 4), it is the owner's own daily need
   (the decisions, the specs and the rules every agent reads), and the other buildings' agents read it. Whether OrkWatch
   is needed is decided after OrkWiki, from Operations' email template in use; until then it is Operations' templates
   and no lab. What weighs against it: mail is the most crowded market (the mail clients' own assistants) and the most
   private data, and Gmail's scopes for a published app are restricted and need Google's verification. §50.8 stands for
   Orkline itself: its loops, then Camp.
4. **A building's mechanic is the shape of its work** (§52, §56): a game is picked because its loop is the work's, and
   the line's games go down a ladder of how much of each move is the person's, as a template earns going by itself
   (§51.4):
   - **Orkboard, a deck-builder** (Slay the Spire, Balatro), as §56 has it: a library to pick from, a party for a goal,
     its price against its care. Not a collectible card game: nothing collected, no packs, no rarity; an agent is set
     up, never won (§56).
   - **OrkWatch, an idle tower defense** (the owner, the same day): mail comes in waves, its rules and templates are the
     towers, what got through wrongly is the damage, and a tower grows when its template goes by itself (§51.4); it
     works while the person is away, and coming back is seeing what it held (§55.3 A). Not an idle clicker: a click is
     the work it saves, and *numbers go up* rewards volume (§55.1).
   - **OrkWiki, Mini Metro:** pages are the stations, links the lines, agents' questions the passengers, a crowded
     station a contradiction or a stale page, the trains the week's budget for checks. Its calm and its colour that only
     signals are orkUI's office already (§53.5).
   - **Orkline, Factorio** as the image its first audience knows (audience.md §1), shapez as the mechanic: loops, not a
     free graph (§50.3).
5. **In a lab the mechanic is a shape, never a skin.** A lab is drawn in orkUI's office (§53) and says everything by
   what it does (§56: no cards, decks, mana or rarity in what a person reads): the mechanic is the view's shape and the
   person's choices (the Map, §52; a party, §56). The art and a game's words are Orkline Camp's skin (§50.1, §52.3). In
   every product of the line the game only reads (§50.5) and rewards results and thrift, never volume, spend or a
   person's streak (§55.1). **A mechanic earns its place by the work** (the owner, the same day): no boosters, no fear
   of missing out, nothing that only spends a person's energy, strength or attention; each mechanic is tied to what the
   product does and is of use every day, never there for its looks.
6. **"The person as little as possible" is the ladder of trust:** the person decides what goes by itself (§51.4), and
   what leaves to people stops at the gate until then (§39). §37.1's line stands, *nothing passes without you*, and the
   line is never advertised as agents round the clock (audience.md §2a.5).
7. **What sells is the engine's result; the mechanic is how it feels.** A skin is copied in a weekend; the one engine
   (the loop, the gate, the ladder of trust) is not.
8. **The PM's proposals, settled the same day (the owner):** OrkWatch is an idle tower defense (item 4); OrkWiki is
   shown, for now, over an Obsidian vault (*a graph view that does something*), still open to change. Not taken: the
   PM's line for the studio (*games taught millions to run systems that work without them*); the site says what the
   studio makes in the owner's words, *game mechanics that help you work* (item 9).
9. **The studio's site shows the line** (the owner, the same day; orkWorks/orkPage `ff9e157`). Its first screen keeps
   its look and changes its lines (*Game mechanics that help you work*; nothing a game uses to hook you); Work vs Humans
   stays as it is. *Orks can build for you* gains the studio's three rules for a game (the game is the job; nothing to
   hook you; less of you, by trust), the line as a road of Orkcraft 0.2's buildings in the order the tools come (the
   Task Fields for Orkboard, the Scroll Dump for OrkWiki, the Watchtower for OrkWatch, the Forge for Orkline), and a
   card for each: the game it plays like, its job, how the game is the job, and its install or where it stands (a tool
   not out yet offers the letter when it ships). The dates are approximate, the owner's to move: Orkboard now, OrkWiki
   and OrkWatch autumn 2026, the whole line December 2026 (moved by the owner the same day; first winter 2026, spring
   2027, summer 2027; moved again in item 10). The site names a game by its kind alone (a deck-builder, a routing
   puzzle, idle tower defense, a factory game), never another studio's title; a tool's card opens from its building on
   the line (orkPage `8081bc3`).
10. **OrkMine, the third lab** (the owner and the PM, the same day): the Mine, Orkline's research building (Orkline's
    `docs/design/mine.md`, built 8 October), on its own: deep research by every AI tool that can search the web, each on
    its own, its findings checked against the others' and marked confirmed (two tools, two sites), one source or
    disputed, the disputes the person's, the report into the Wiki's inbox. It plays like an ASCII roguelike, taking from
    NetHack only what is the work: a claim is an unidentified item until it is identified (the altar's blessed,
    uncursed, cursed are the Mine's three marks), the fog is the question not yet searched, the stairs down a
    sub-question, the food the run's budget, the heroes the tools; never death, loot, levels or a grind (item 5). ASCII
    is the one game drawn in orkUI's office without art. Its line to OrkWiki: the Mine finds and checks what is new
    outside, its links the evidence of one question; the Wiki keeps what is known, its links the knowledge's shape over
    time; the Mine's report is the Wiki's first source, Orkline's first loop. What sells: research that shows what each
    line stands on, on the subscriptions a developer already has; against it, a crowded market (the vendors' research
    modes) and the cost of several tools (its price seen before it starts, as a party's, §56.3). The order becomes
    Orkboard, OrkWiki, OrkMine, OrkWatch; on the site OrkMine is third, its stop the Mine from orkUI's `game/buildings`,
    autumn 2026, OrkWatch December 2026 and the whole line February 2027; the line's names in small letters, their ork
    in the ork's green (orkPage `e43a915`).
The line's frame and its page: no product's code and no spec. §27 and §50.8 stand (no new mechanic before the testers'
numbers); a lab starts with a spec of its own, OrkWiki's first.

## 61. The Map shows one goal: its ideas by stage, its party in lanes; results are merged on the idea; Review's column goes (21 October 2026, the owner)

Why: the owner's notes on the trail Map (decisions §59, spec 46). It shows every goal at once and tells how far each is,
but not who is on an idea now, in which step, and what waits for the person's look: for that the person leaves for
Agents and Review, and on the desktop a column of results sits beside the Board for work that belongs to ideas. The
owner and the PM worked out a Map of one goal, drawn as an interactive mockup (Ideas and Phone Ideas; the older variants
Main, States, Lanes and Phone were turned down). So:
1. **The Map shows one goal.** Its header is the goal: title, priority, state, progress and %, *n of m ideas done*, *done
   when*, *≈$ so far*, today's merged and $; under it one line with the whole party and each member's state (*at work*,
   *next*, *tonight*, *free*, or the Needs you words in alert). The desktop picks the goal in its header; the phone's top
   bar already does.
2. **Below it, the goal's ideas in trail order.** An idea at work or waiting for the person is expanded; the rest are one
   line (the head of who is on it, the title, *<stage> · <state>*, a mark); the done ones fold into *Done (n)*, with *in
   dev · waits for main* while they are not in main.
3. **Every idea is in one of three stages**, worked out from its state and its plan, never written by hand: **Planning**
   (raw, reading, asks, ready, planning, plan, proposed), **Implementation** (a passed plan whose build tasks are not
   all merged), **Checking** (only check tasks left: their kind is a checker's tag), then Done. A word for the step, not
   a new state: the keeper's and the runner's states do not change.
4. **An expanded idea** is a stage track (the current one underlined, the past ones ✓), **lanes** of the party members
   active in the stage (the leader in Planning, the builders with tasks in Implementation, the checkers in Checking:
   at most 3 by the party's seats), **columns** that are the plan's waves, a task's card in its agent's lane and wave;
   tasks of one agent in one wave **stack** with a count. A merged task leaves the field with one animation, none
   under `prefers-reduced-motion` (§55.2). Members' questions in Planning are in the leader's lane, wearing the asker's
   head (spec 46 `by`).
5. **The idea's card**, in orkUI's double frame, on the right: title, stage, pips, *k of n tasks in dev*, ≈$ so far and
   the plan's estimate. In Planning with a plan waiting: **Start the work** (the plan's pass, autostart stays) and **Open
   the plan**. In Implementation and Checking: *Waits for your look* for that idea's results with **Merge into dev**,
   **Send back** and **Drop**, which are Review's actions, unchanged. On the phone the card is on top of the block, the
   waves rise bottom-up and one idea is expanded at a time.
6. **Yellow goes only on the agent the work stopped on**: a member who asks, the leader for a plan, a spec or a proposal,
   the agent of a failed task (its task in danger). A result waiting for a look is not a signal (§54.1): *in Review* in
   muted ink; it still counts in Needs you.
7. **The desktop's Review column goes.** Results are merged on the idea's card, one place each. The dev → main gate stays
   where §49.5 has it, in Needs you. No branch per idea and no *merge into main* on an idea: the person sees dev and
   main only (§49).
8. **The Map is no longer only a view.** This supersedes §52.1 (its one action *open*) and §54.4's single button, and
   spec 39's *Not in this spec: acting from the Map*: it has the actions of item 5, which are the Board's own commands;
   it invents no command and no setting.
9. **A check with findings** stays in Checking: its result waits for the person with its findings, *Send back* runs it
   again as round 2 (*Checking · round 2*); an idea is back in Implementation when a build task is sent back or fails.
   The runner is not changed.
10. **Measured:** the share of results merged from the Map against Review (`opened` `via: "map"`), the Map's opens per day
    (§52.4).
An improvement of v1's existing mechanics (§27) and a view's rewrite: the owner's call, before the testers' numbers, as
§55 and §59. Spec 48.

## 62. One window: the goals as tabs, Planning over the leader, the party at the foot, what waits for you along the bottom; the gate is built (21 October 2026, the owner and the PM)

Why: the owner's call to simplify the desktop radically, to one window (and the phone to one screen with no tabs). After
spec 48 the person still moves between three regions (the Board's column with Needs you, the Map with its tab strip,
Agents) to answer one question asked all day: *where is my goal, and what waits for me*. The owner and the PM drew it as
an interactive mockup (Design artifact *Orkboard: one window*: B, the desktop, and D, the phone; A, waves as columns,
was turned down; C lists what was taken from the game). So:
1. **One window.** The goals are tabs with their progress and their stops' count; under the tab, the leader heads
   the left column over its Planning; the party stands along the top of the field, each member's open tasks running
   down from it, the top row lit and the rows below muted (what a member is on is what is bright; item 9); the
   results that wait for a look are a column on the right; what waits for the person lies along the bottom with its
   quick answers; anything opened slides in as a drawer from the right, its tabs kept. The Agents pane, the Board's column and Needs you's list go as
   regions (the pool by agent and the files open in the drawer). The phone is the same on one column with no tab bar: a
   stage switch (Planning · Implementation · Checking) shows one stage's columns at a time, and a tap pops a stop out
   of the bottom row.
2. **The shape of a collectible card game, the words of the Board.** What a person reads there at a glance is taken
   where it means the same: a price before a move (a gem), two measured numbers on a member, the things to answer as a
   hand at the bottom with their answers on them, the end of a turn as the gate, what is left of a tool as diamonds with
   its reserve hatched, the day as a strip of marks, a peek at a member's whole face on hover, what waits for a task lit
   on hover. Taken with care: the checks stay in the party; a task appears with one motion. Not taken: packs, golden
   members, quests and streaks, a timer, emotes and sounds, dragging to play, a forecast of *done when* (no data). It is
   also the product's picture for marketing. The interface never says card, deck, hand, mana, hero or boss (§56).
3. **A member says two numbers and its kit**: its runs and redos this week (a checker's checks and catches, the
   leader's plans and plans made again) and its average price for a run (an estimate, by its level, until three have
   finished), beside its head; the head wears its harness's mark, its level's chevrons (Orkline's, now in orkUI) and
   its state as a sign (✗ a failure, ! a stop, ↻ at work). No octagon frame: the head is the picture (§53), small; the
   member is a small row, three of them across a phone. Showing one member's work reorders nothing: the others' tasks leave the field and its own lie across it.
4. **The gate is built** (§49.5's item 5, its one press): *Merge dev into main*, beside the party, with its count of
   ideas in dev not in main, its screen in the drawer, a fast-forward or a merge commit made in a worktree of its own, a
   conflict refused with main as it was. Its report (the full suite, the browser tests, `checks.toml`) and *Revert* stay
   §49.5's next round.
5. **Today's events** become a command and the strip on the left (the phone's *Today* sheet); the reserve is in the
   snapshot so the limits can show it.
6. **Quiet by default** (the owner, on the mockup): the goal's numbers are one line in the ideas bar, its details
   behind *About this goal*; Planning's rows are plain lines with a mark only for a stop; the alert colour stays where
   §61.6 puts it.
7. **Measured:** the share of answers given from the bottom row (`via: "hand"`) against the drawer and Needs you of
   before; opens from the strip (`via: "today"`) and from a member (`via: "party"`); the gate's presses a week.
8. **Motion says what changed, never decorates**: a task that leaves fades where it stands and its column settles
   into the gap, a task whose state moves it slides to its place, nothing moves under the pointer or the focus, a merge
   lights its member's number once; nothing flies, nothing bounces, none for what changed while the page was hidden.
9. **The party on top, the work running down to you** (the owner, on the flipped mockup): the members stand along the
   top of the field, each one's tasks queue down from it, what waits for the person lies along the bottom. You deal the
   work (a plan started, a question answered, a new idea), the party clears it (the front task is the one a member is
   on, a merged one fades and the queue steps up), and what it brings comes down to you. Read top-down, as the eye
   does: what is happening now first. The game's look stays in the hand, the prices, the gate and the diamonds; the
   words stay plain (§56).
A new face over v1's mechanics and the gate decided in §49.5: the owner's call, before the testers' numbers, as §55,
§59 and §61. Spec 49.

## 63. Parties and goals: what was a goal is a party, what was an idea is a goal; a goal raises its flag in main; a party's goals are decks of one element (21 October 2026, the owner)

Why: the owner, on the one window's mockup. The goal on a tab is a container the person never really chooses: what they
pick every day is **who works on it** (a leader, builders and checkers, the checks they hold the work to, what it
costs), while a goal's metrics, its *done when* and its verdict are written for them by the keeper and steer nothing;
and an idea, the thing that does have an end, has none the Board celebrates. A product team works the same way: a team
for the product, one for the platform, one for the whole flow, each with its own line of goals. So:
1. **The words move one step**: what the code calls a goal (a track, `pages/tracks/`) is a **party** in what a person
   reads; what the code calls an idea is a **goal**; a task stays a task. The code, the files, the commands, the keys,
   the events and the classes keep their names (CLAUDE.md), so Orkline reads the same Board. This reverses §54.8
   (*a goal stays a goal*) and §47.2's *no idea without a goal* (now: no goal without a party).
2. **A party has no end**: a team you picked and what it is for (its brief), its checks, its price; no metrics, no *done
   when*, no progress, no verdict: only a count, its done goals of all its goals (*5/12*). Nothing accepts it by itself any more; a party's reading no longer asks metrics.
   Parties are the tabs; a new one is one of yours (§56.6) or made from the library.
3. **A goal raises its flag when the gate takes it into main** (the person's press, §62.4), or when it is done where
   there is no gate. Done in dev, it waits for main. The flags of its goals are a party's record; a party's old flag
   (a verdict met, §55.3 B) stays as history. No backfill.
4. **A goal is a deck of one element**: a pixel symbol and a muted colour (orkUI's, five: meadow, ice, dust, void,
   lava) on every card of it, given once, the least used among its party's open goals. Never named in the interface.
5. **A member's work lies in stacks by phase**: its tasks of one goal at one phase (now, next, later: against the
   goal's current wave) are one stack of 5:7 cards that spreads on a press; what a task waits for is an arrow on
   hover (the desktop) or a line on the card (the phone): a card that does not go up shows why.
6. **The goals list filters the board**: one press shows only that goal's cards, more add to it, *Show all* clears;
   a goal stays in the list until its flag.
7. **Quiet at the top**: the party is one line, its goals one line; the details behind a press (*About this party*,
   the goals' sheet). The phone's project is a sheet of its own from the top bar.
8. **A tap is never lost to a redraw** (the phone): a redraw waits while a pointer is down, and the holds redraw only
   what they held back; the tests' retries go.
9. **New goal draws a blank card**: a face-down pile on the desktop, the FAB's dial on the phone; the card turns over
   and is filled in.
10. **Every symbol the window draws is orkUI's** (the owner): the elements and eight signs (done, failed, at work,
   tonight, a stop, a flag, what a task waits for and what waits for it) are pixel symbols of the look, drawn on a 7 × 7
   grid; no Unicode symbol stands in for one.
11. **The parties are a switch in the top bar, not a row of tabs** (the owner): a project has a few, three at most as a
   rule, and they change seldom; the switch says where you are (*project › party*) and the board gains the tab row's
   height. The phone keeps its chips.
12. **On the phone the party is in the top bar too** (the owner): one *where* button, *project › party ⌄*, with a count of
   what waits in the other parties; its sheet lists the parties, a new one and the other projects. The chips row goes.
13. **A card keeps its size; the members scroll instead** (the owner): a member's column is as wide as its card, and
   three or more members are a sideways strip with the third peeking; the cards never shrink to fit (this replaces
   spec 49's *no sideways scroll with three*).
14. **No Today button on the phone's top bar** (the owner): *Today* is an item of the menu; the bar holds the menu, where
   you are and the limits.
15. **One row for the goals and the gate on the phone** (the owner): the party's bar goes; *k at work* and *j ask you*
   were the stage switch's counts said twice; the party's details are behind the Goals sheet's *About … ›*.
16. **The phone's FAB is the desktop's New goal deck** (the owner): a small face-down deck that draws a blank goal; the
   dial goes (a new party is in the *where* sheet, a member in About this party).
A new face and new words over v1's mechanics, two small additions to the host (a goal's flag, its element), and the
end of a model call (a party's acceptance): the owner's call, before the testers' numbers, as §55, §59, §61 and §62.
Mockups E and F of *Orkboard: one window*. Spec 50.

## 64. Pick one: a task may make a few variants of one kind (pictures, sounds, clips, texts) and the person picks one with a note (21 October 2026, the owner)

Why: the owner. Some work is chosen by eye or by ear (an artist's logos, an icon, a jingle, a clip, a tagline), not
reviewed as a change; one variant a round makes the person wait a round for each look. So:
1. **A task may end with variants instead of a change**: two to six of one kind, which the plan asks for when the goal's
   spec asks to choose by eye or by ear; never code. The task leaves them as files and a manifest the runner reads and
   never commits (as a check's findings, §56.1); they live in the goal's state folder, not in the repository.
2. **The kinds are one mechanism**: pictures, sounds, clips and texts are files with a media type sniffed from their
   bytes, limits by kind, served by one signed route (Range for sound and video, a sandbox for anything that could run);
   the faces draw each kind as a tile. A new kind is a new tile and a line in `KINDS`, not a new flow.
3. **The person picks one, with a note, or none**: *Take B* commits the one picked to where the plan said and the work
   goes on (the note told to the tasks after); *None of them* asks for a note and runs the task again. It is a stop of the
   bottom row (*Pick one*), answered on the card or with a note in the drawer, on the phone in its raised card or on its
   own screen.
4. **Measured**: picks a week, taken at the first round or asked again, the time to pick, where, with a note or not.
A new end for a task over v1's runner and the faces of §62–§63, the owner's call. Spec 51.

## 65. The leader deals the goal types; a type says who the party needs; the stages wear the party's faces; a stop is counted only where it cannot be seen; the party switch is a deck (22 October 2026, the owner)

Why: the owner, on the one window as built. A new goal is a blank card, so the person writes from nothing what they
already know (it is a logo, a bug, a landing page), and the party works it with whoever is in it: a logo asked of a party
with no Artist goes to the Grunt. The phone's stage switch says *Planning 6 · Implementation 7 · Checking 3* in the
alert colour, read as *seven wait for you* when one does; and the tabs were always by band (the leader's, the builders',
the checkers'), not phases in order. So:
1. **The stages wear the party's faces**: the phone's switch shows the heads of each band over its word (*Planning*,
   *Implementation*, *Checking*: the words stay, a head never stands alone) and **no number**: a sign (✗ a failure, else
   ! a stop) on the faces of the band it comes from.
2. **A stop is counted only where it cannot be seen**: the bottom row is the count of the party shown; where a stop
   comes from has its sign, once (no alert edge, no alert words beside it); the only count of stops is that of the
   project's other parties, on the party switch. A failure keeps its danger edge.
3. **The party switch is a deck** (reverses §63.11 and the party half of §63.12): on the desktop over the leader at the
   left column's top, a press dealing the parties as cards; on the phone at the end of the stage switch, its sheet the
   parties. The top bar keeps the project; the phone's goals bar says the party.
4. **The leader deals the goal types**: each leader of the library has a few (a designer *New screen*, *New icon*, *New
   logo*, *New feature*; an architect *New feature*, *Fix a bug*, *Restructure*), the Taskmaster a general set (*New
   feature*, *Fix a bug*, *Clean up*), and a blank goal is always the last. A type is told by **its sign** (orkUI's),
   never a colour: colour is the goal's element and the signals. A type brings the few lines only the person can give,
   Refs where looks matter, the lens it opens first, and a line for the leader's draft and plan.
5. **A type says what kinds of work the party needs**; when no one of the party does one, the form says who would: a
   free seat, it joins; a full band, **a swap** (the owner: a swap, not a guest for one goal); a member with work open
   never leaves this way. A goal kept for tonight never changes the party.
6. **A plan that gives work to no one of the party says so on its stop**: *No one in the party does pixel art: Artist
   would*, with *Add and start* when a seat is free, else *Edit the party*; *Start without* keeps today's way.
7. **Members are not added in the stage switch**: the tabs show who works; the team is changed where the need shows
   (the type's form, a plan's stop, About this party) and, for a band with no one, from its empty line.
8. **Nothing flies** (§62.8 stays): the owner turned down an answered stop flying onto, or lighting, the task it answered;
   it would distract.
9. **Measured**: the share of new goals with a type, by leader and type; the asks answered; the join line kept, unticked
   or swapped; a plan's line and what was pressed; whether a typed goal's plan passes at its first round and raises its
   flag sooner.
A new start for a goal and a new place for the party switch and the counts over v1's mechanics, the owner's call before
the testers' numbers, as §62–§64. Spec 52.

## 66. The phone, simpler: the deck beside the party's name, the faces are the members, New goal at once with the party first, a goal's two marks on every card (22 October 2026, the owner)

Why: the owner, on the phone as spec 52 built it: four bands before the first card, the party's faces twice (on the
stage switch and in the members' strip under it), New goal behind two motions (≈ 1.2 s) and a form longer than the
screen that names the party twice. So:
1. **The party's deck stands at the goals bar's left**, beside the party's name and its *k of n goals done* (moves the
   phone's half of §65.3 from the stage switch's end); its count and its sheet are §65's.
2. **The faces are the members**: in the stage shown, a tap on a face shows only that member's tasks, again everyone;
   a stage's sign (✗, else !) stands on the face it comes from (refines §65.1). The members' strip goes: over each
   column its member's name; a member's runs and price stay in its solo.
3. **New goal opens at once**: the form slides up (180 ms; none under reduced motion); the lift, the deal and the turn
   of the create button go on the phone. The desktop's New goal is unchanged for now.
4. **The party first**: the form starts with the party (its leader's head, a list of the project's parties), then the
   priority, then the goal type (the party's leader's types, *No type* last), then **one field for the goal** (its
   first line its title), then the type's fields. A type belongs to its party's leader, so a change of party deals its
   types again. The form says no element, names the party once, has no lens switch for a typed goal, and *Low* says
   *Keep for tonight*.
5. **A goal's two marks, each in its place**: its element (which goal: shape and colour) at a card's corner; its type's
   sign (what kind: muted ink) before the goal's name wherever the name is written, task cards too (reverses spec 52
   §4.6's *no other place*). A type is still never a colour (§65.4).
6. **Nothing flies** (§62.8 stays).
The owner's call on the phone as built, before the testers' numbers, as §62–§65. Spec 53.

## 67. One hand: every stop of the project in it, the most urgent in the middle, no count anywhere; every stop has a way out (22 October 2026, the owner)

Why: the owner, on the window as specs 52–53 built it. An Artist asked for a reference picture as a plan's to-do; a file
to-do was done only with a file, so the goal stood still. And what waits was split: the party shown's in the hand, the
others' as a number on the party's deck. So:
1. **One hand for the project**: every party's stops and Operations' lie in it; a stop of another party says its party
   and opens there. What waits for the person is their inbox, not a party's.
2. **The most urgent in the middle**: red (a failure) first, then what holds work back, then what does not, then the
   results; the oldest first in each. The keys and a screen reader read them in that order.
3. **No count of stops anywhere** (reverses §65.2's one count and the count of §65.3's deck): nothing waits out of
   sight. The parties' list marks a party with a stop by a dot (red when one failed).
4. **Every stop has a way out that needs nothing from the person**: a question *Let <asker> decide*; a file to-do
   *Describe it instead* or *Go without it*; a choice *Let <leader> choose*; any other to-do *Go without it* (its tasks
   run without it and say so if they cannot). How often each is pressed, by agent and kind, says who asks too much.
5. On the phone, **the Target is one switch**, and **Agents is reached from a member** (*Edit* on its card); the menu
   keeps Stop all, Today and Spend at its head.
The owner's call on the window as built, before the testers' numbers, as §62–§66. Spec 54.

## 68. The type top right: a card's top right holds its goal's type, in its goal's colour; the state's sign leaves the top (22 October 2026, the owner)

Why: the owner, on the screenshots of spec 54: *where did the task type signs go on the cards? I see only the element;
maybe remove the exclamation mark or the error sign at the right of a card and put the type there, the type and the
element in one colour?* The sign was not seen because a goal made before spec 52 (and every goal of the test scene) has no
type, and where it is drawn (spec 53 §3) it is 14 × 14 in muted ink before the goal's short name, easily missed, and it
truncates the name. So:
1. **A card's top right holds its goal's type's sign**, 14 × 14, **in its goal's element's colour** (faint while the
   element is drawn dim, muted for a goal with no element). The top row reads as the goal's mark: left *which goal*, right
   *what kind of work*. Two goals of one type in a party still differ by colour. A goal with no type: the top right is
   empty.
2. **The state's sign leaves the card's top** (↻ at work, ✗ failed, the clock tonight, ! asks you / asks you to pick): the
   foot's words (*working 28 h*, *failed*, *tonight*, *asks you to pick*) and the card's edge (danger for a failure,
   alert for a stop, dashed for what waits) say it already. Edges, foot, label and tooltip stay.
3. **The goal line is the goal's short name alone**, its full width back; a Planning goal's card keeps the type's name
   (*Fix a bug*) or *Goal* (phone) / *Planning* (desktop), without a sign in the line.
4. **Everywhere a type's sign is drawn it wears its goal's colour**, the goals' lists too (one rule); the stops along the
   bottom (the element alone), the top bars, the stack's ghost flash and New goal's form are unchanged.
5. Reverses spec 53 §3's place of the type (before the goal's name, muted) and spec 50 §3.4's mark top right. A type is
   still never a colour of its own (§65.4): it takes its goal's. No orkUI change; the interface never names an element.
The owner's call on the cards as built, before the testers' numbers, as §62–§67. Spec 55.

## 69. Fantasy signs: each goal type its own sign, a thing of the realm, never a being; orkUI keeps a library (22 October 2026, the owner)

Why: the owner. A type's sign now stands on every card (§68), the most seen picture after the heads, and it is drawn
as an office mark (a star, a display, bars) in a look whose world is orks and their camp. Creatures were weighed and
turned down: at 7 × 7 a creature is a smudge, only the bug has a creature's metaphor, an element read as fire or ice
would say *urgent* or *frozen* where it means only *which goal*, and a second kind of being beside the heads would blur
*who works* and *what the work is*. So:
1. **Every goal type its own sign** (reverses spec 52 §1's four shared signs): sixteen, five new names.
2. **A thing of the realm, never a being**: a scroll, a potion, a war horn, a rune; on the same 7 × 7 grid, in its
   goal's colour (§68); it takes no shape a sign already means (a flag, a cross, a clock, !, a moon, a coin).
3. **Drawn many, picked by the owner**: candidates by a model, a sheet to look at, the owner's pick; what is picked
   beyond the types stays in orkUI as a library (emblems) no face draws until it is made a sign.
4. The elements, the state signs and the media tiles are unchanged.
The owner's call on the look, before the testers' numbers, as §62–§68. Spec 56.

## 70. The deal on Start: a plan started from the hand deals its tasks onto the field (22 October 2026, the owner)

Why: the owner. *Start the work* is the moment the party is set to work and money starts to be spent, and its only sign
is a stop that goes and tasks that rise where the eye is not. §62.9 already says *you deal the work*. So:
1. **A plan started by a press in the hand deals its new tasks from that stop's place to their columns** (≈ 0.3 s, in
   steps, six at most); every other start keeps the rise.
2. **It is the one motion that travels**, an exception to §62.8 kept to this press: it says what changed (how many
   tasks, to whom); nothing else flies (§65.8 stands), none under reduced motion or a hidden page, none into a column
   under the pointer; the phone deals only into the stage shown and never switches it.
The owner's call, before the testers' numbers. Spec 57.

## 71. A stop and its task: the link before the answer, one change after (22 October 2026, the owner)

Why: the owner asked how an answered card in the hand could be read as landing on its task, more simply than a flight
(§65.8 turned the flight and the lighting down). The link is wanted before the answer, not after it. So:
1. **While a stop is looked at, its task is shown**: the desktop rings its task's cards on the field (an ink outline, no
   motion); the phone's raised card names its goal and task (and the member).
2. **An answered stop leaves where it stands, in the frame its task changes**: a fade in place, no removal before the
   Board is reread, so the eye reads one change; nothing flies, nothing is lit after (§65.8 stands).
The owner's call, before the testers' numbers. Spec 58.
## 72. Parties of mixed crafts first; the leader sets the stages and their seats; the goal types come from the team, not the leader (22 October 2026, the owner)

Why: the owner, going through the library's parties and their goal types: *the parties used most will be mixed ones, a
game's (its leader a game designer) or a mobile app's (a product leader, and besides the code ASO and an Artist for the
pictures), more often than a party of one craft.* Spec 52 gave the goal types to the leader (§65.4), so a mobile app's
party led by the Product manager dealt *Solve a pain*, *Try an experiment*, *Write the launch* and never a store listing,
whoever was in it; and every party had the same seats (one leader, three builders, two checkers), so a game's party
(code, art, levels, sound) did not fit. So:
1. **The library gives parties of mixed crafts, first**: *Game*, *Mobile app*, *Website*, then the parties of one craft
   as today. New agents for them: a Game designer (an elf, a leader), a Level designer and a Sound designer (elves), a
   Playtester (an elf, a checker), ASO (a gnome).
2. **The leader sets the stages**: their words and how many seats each has, one leader and five more at most (the party
   stays six). A Game designer's: *Concept* (it), *Build* (four), *Playtest* (one). A stage is still one of the three
   bands (plans, builds, checks), so who plans, who takes a task by its kind and whose check joins a goal stay as they are.
   The leaders of today keep *Planning*, *Implementation*, *Checking* and three and two seats.
3. **The goal types come from the team** (reverses §65.4's dealer): one catalog of types, each with the kinds of work it
   needs; a party offers the types its members (the leader with them) can do, **and few others**: one it misses one agent
   for only when the leader itself does another part of it (§65.5's *needs:*, its join or swap), never work beside the
   leader's (*better fewer goals than a distracted person; neighbouring goals are another party's*); the general types
   (*New feature*, *Fix a bug*, *Clean up*) only when someone of the party writes code. A type that stands in for a
   general one (a designer's *New feature*) hides it when the party can do it. A type is still told by its sign (§65.4).
   The Product manager takes screens too (an app's leader writes its flows), so its parties are offered *New screen*
   with the Design system designer to join.
4. A goal keeps its type by the catalog's id; a type kept before by its leader (`architect/feature`) is read as the one
   the catalog gives it.
5. **Measured**: the share of new parties from each of the library's, mixed and of one craft; the types offered, picked and
   joined for, by party; whether a party with four builders swaps less than one with three.
Steps of a type's own (a skeleton the plan must keep) wait for the numbers: first see where a typed goal's plans differ.
The owner's call on the library before the testers' numbers, as §62–§71. Spec 59.

## 73. The phone's members wear their tool and level again, beside their names (23 October 2026, the owner)

Why: the owner: *on the phone, while the party works, you cannot see each member's tool and level: only the heads on top
and the names below; the desktop has them.* Spec 53 took the marks off with the members' strip (§66.2). So:
1. **Over each column**, the member's tool mark before its name and its level's chevrons after it; the name is cut,
   the marks never.
2. **A member's card** (its solo) says its tool in words after its head's words.
3. Not on the stage switch's faces: they are its buttons, 24 px, with the state sign on them.
Refines §66.2. The owner's call, before the testers' numbers. Spec 60.

## 74. Your own goal, first (23 October 2026, the owner)

Why: the owner: *a party's fixed set of goal types limits the person; leave a free goal, its card filled in by the
person.* The free goal is there (*A blank goal* on the desktop, *No type* on the phone) but last, and named as empty. So:
1. It is called **Your own goal** and stands **first** on both faces; on the phone it is the one picked when the form
   opens (reverses spec 53's first type picked).
2. A type is a shortcut (its asks, its refs, its plan's hint), never a limit: a goal of one's own still gets the plan's
   *missing* line and *Add and start* when it asks for work no one of the party does (§65.5).
3. **Measured** as §65's types are: the share of one's own goals, by party and face; above about a third, the owner
   reads their words for the types the catalog lacks.
The owner's call, before the testers' numbers. Spec 61.

## 75. The spec after the start: talked over with the party's leader, and a change re-plans what is left (23 October 2026, the owner)

Why: the owner: *I want to edit and discuss the spec with the leader, before the work starts and after it, ideally each
point on its own, and it should change the work in progress.* The talk per section is there (spec 35), signed *the
Taskmaster* whoever leads; once a plan is passed, a changed spec reaches no task. So:
1. **The talk names the party's leader** (§72: the leader plans the party's goals).
2. **A goal says which of its plan-making sections changed since its plan**, with *Re-plan* before the start and
   **Re-plan what is left** after it: a press, so a model call is never spent on every edit.
3. **The leader proposes a plan change**: the tasks not started changed, dropped or added; a task at work or merged is
   never touched. **It comes to the hand as one stop** — what changes and what it costs — answered *Take the new plan*
   or *Keep the plan*; nothing is applied before the person's *Take*. Taking it deals the added tasks as *Start the work*
   does (§70: the same moment).
4. **A party's description changes no goal by itself**: a party has no plan (§63); its goals read the new description
   when they are drafted or planned again.
5. **Measured**: the goals whose spec changed after the start; the plan changes asked, taken and kept; what they add.
The owner's call, before the testers' numbers. Spec 62.

## 76. The party gathered: what it can take as it is picked; its heads gather into the deck; three moments travel (23 October 2026, the owner)

Why: the owner: *put the accent on gathering the party, perhaps with a motion like folding into a deck, as a goal's start
has; and one at a goal's end: then three big motions — the party picked, the work started, the work done; without
making it complicated.* Today the party's form says what it costs, not what it opens, and its save is a dialog that
closes. So:
1. **New party and Edit the party say what the party can take** as its seats change: the goal types it would be offered
   (§72.3), a type a seat has just opened lit once. This, more than the motion, is the accent: it says why a member is
   worth its seat.
2. **A new party saved gathers its heads into the party's deck** (about 0.3 s, in steps, six at most), the deck lit once:
   it says where the party went.
3. **Three moments travel, and only three** (replaces §70.2's *the one motion that travels … never a precedent*): the
   party gathered (this), the work dealt (§70, and a plan change taken, §75.3), the flags raised (§77). Each says where
   something went, in steps, under half a second, never under reduced motion or on a hidden page, never for what the
   person did not press or see, never in the way of a press. Everything else stays as §62.8 and §65.8 say: nothing flies.
The owner's call, before the testers' numbers. Spec 63.

## 77. The flags raised travel from the gate to the flag line (23 October 2026, the owner)

Why: the owner asked whether a goal's end has a motion, and whether it should. A merged task fades with a one-frame ✓
and lights its member's number (§62.8); a goal's end, its flag raised in main (§63.3), only makes the flag line stand. So:
1. **When the flag line first stands** on a device (once, as today), its goals' elements travel from the gate to the
   line (the deal's timing, six at most) and stay in it, small, before its words; then the line's flag is raised (one
   short step up) and the line is lit once.
2. **From the gate's merge** when the person merged a moment ago, else the gate's button; when no gate is on screen,
   nothing travels and the flag is still raised.
3. The third of §76.3's three moments; no sound, no confetti, no colour but the office's.
The owner's call, before the testers' numbers. Spec 64.

## 78. Ideation: small ideas read from four sides, and the Investor invests or passes (23 October 2026, the owner)

Why: the owner wants to drop small ideas and concepts and have them judged from the product's, marketing's, engineering's
and design's side: where to take an idea, or why not to do it. A goal goes one way today, to code at Review and the gate;
a small idea has nothing to merge yet, and a dropped goal loses why it was not worth doing. So:
1. **A party of the library, Ideation**: its leader the **Investor** (a new leader, product's craft: it decides whether to
   invest the team's time), four views (Product, Market, Engineering, Design) and a Skeptic. **Always all four views**: a
   pitch is never decided on fewer.
2. **A pitch's own way**: the views each alone, then the case against, then the Investor's decision — invest (in which
   party, as what type), reshape, or pass, with why. No plan, no tasks, no Review, no gate. Code's kill reasons turn an
   invest without someone it is for, a metric it moves, or that repeats a goal, into a reshape.
3. **A passed pitch is kept with its why**, and every later pitch is read against the passed ones.
4. **Nothing moves by itself**: the person sends a pitch to a party (a new goal there, the views in its draft), passes,
   or changes it and has it judged again.
5. The Investor wears the lich's head for now; a mummy or a ghost of its own is drawn in orkUI first.
Spec 65.

## 79. Team briefs: Operations prepare the daily, the retro, the refinement and a 1:1, never a judgement of a person (23 October 2026, the owner)

Why: the owner wants help with people management: the team's work in Jira, GitHub and Slack, ready for the daily, the
retro, the refinement and 1:1s. It belongs to no project and repeats every week: Operations' (§51). So:
1. **A template may be a brief**: it reads and writes a page for the person, and does nothing outside. A brief may
   **stand**, prepared before its meeting; a brief may **follow** a person or a team, starting from the last one.
2. **About the work and the meeting, never about a person**: no strengths and weaknesses, no score, no ranking, no
   reading of tone, no counts of commits or messages as a measure of anyone; held by code (a fixed rule in the prompt, rules
   with such words dropped, Slack read only in the channels named, checked against the calls), not by the skill alone. The
   law, the team's trust and what the data can say all point the same way.
3. **A brief is the manager's alone**: never posted, sent or shown to the teammate, a 1:1's agenda too (the owner's call).
   What it reads is said on its form; **Forget** removes all that is kept about one person.
Spec 66.

## 80. A member struck by a failure, a member calling with a question (23 October 2026, the owner)

Why: the owner: *a short animation, as if it were hit, when an agent goes into a question or an error, as when a Pokémon
takes a blow: short, but it catches the eye.* A member that stopped waits for the person, and today only its head's sign
says so. A question is not a blow (*a question costs nothing*), so the two are told apart:
1. **A failure strikes the member**: when its head's sign turns ✗, the head is lit once (one inverted frame, as the quiet
   reward's light) and jolts sideways 2 px three times, in steps, about 0.3 s; the ✗ in the danger colour, the jolt in ink.
2. **A question, or any other stop, calls**: when its head's sign turns !, the sign pops up over the head and steps
   down into its corner, the head hops 2 px once, in steps, about 0.25 s.
3. **Once, on the change, for what the person sees**: never on the first read of a party, never for what changed while
   the page was hidden (the sign simply stands), never under reduced motion, never on a head under the pointer or the
   focus; at most three heads in one refresh, the rest wear the sign without it. Nothing travels: §76.3's three moments
   stay three. No sound, no colour but the office's.
The owner's call, before the testers' numbers. Spec 49 §11.7.

## 81. The hand first on the phone: the field a board of tokens, every member on the screen, the most urgent stop answered where it stands (23 October 2026, the owner)

Why: the owner, on the phone's screenshots (the Design canvas *Orkboard — after the cleanup*): *the person will not read
the task cards much; what matters are the cards in the hand. The target device is an iPhone: use its screen as
productively as we can, and no sideways scroll; four members is the most.* At 390 × 844 the field took almost the whole
screen with cards of 132 × 185 and a sideways strip from the third member on, while the hand was 56 px of cut words and
every answer took a raise first. And a waiting task said *after k1, k2*, ids the person never sees elsewhere. So:
1. **Every member on the screen**: the phone's columns share its width, one to four, with no sideways scroll (replaces
   §63.13's *the members scroll instead* and spec 50 §6.5's 148-px columns).
2. **A task's card is a token on the phone**, 74 px wide and 5:7, its stacks wrapping in its member's column: the top row
   as §68 has it (the element, the type's sign in its colour), the task's short name, one value (its time at work, or
   the hour it may start); the goal's line goes (reverses spec 55 §3 on the phone); the edge and the fill say the state,
   at work raised. The words stay in its label.
3. **What a task waits for is said by name** on both faces (*after Challenge store*), the desktop's card *waits for 2*.
4. **The hand takes the room**: 250 px while a stop waits; the most urgent stands upright in front with its banner, its
   text and its quick answers (two at most, else the recommended one and *More…*), the rest fanned around it, a card
   right of the front with its corner mirrored; a tap brings a fanned card to the front; an answer from the front is
   counted `via: "front"`.
The desktop is unchanged but for item 3. The owner's call, before the testers' numbers. Spec 67.

## 82. On a subscription a spend is a share of Claude's five-hour window, not ≈$ (23 October 2026, the owner)

Why: the owner: *money says nothing to me now: I don't know what the API costs.* §48.3 made ≈$ at API prices the one
currency, said *not your bill*; on a subscription nobody pays it, and what runs out is the window the top bar already
shows in percents. So, while Claude is on a subscription:
1. **A spend is said as a share of the five-hour window**: *≈18 % of 5h a task*, *plan ≈3–8 % of 5h*, *<1 % of 5h* under
   a percent; the five hours, not the week, so a task costs whole percents. Its hint says it is an estimate.
2. **An estimate, never a read**: Claude says its windows in whole percents and every session on the machine, the
   person's own too, spends the same window, so a task's share can't be read off it. It is its ≈$ at API prices over a
   rate: what 1 % of the window has cost on this machine, the API-equivalent $ of every Claude Code session since the
   window began over the percent it shows used, one sample a window (at least 5 % used), the median of the last 12
   (`sources/window_rate.py`, `~/.config/orkcraft/window-rate.json`). Use outside Claude Code (claude.ai) leaves no
   transcript: the share then reads high, never low.
3. **The $ stays underneath**: the ledgers, the estimates, Review's *Cost too much* and every event keep $ and tokens;
   only the page converts, through the snapshot's `rate`. With no rate learnt yet, or on an API key, the page says ≈$ as
   before. A tool of its own price (pi, Hermes) beside Claude on a subscription is said in Claude's window too: rare,
   known.
The owner's call, before the testers' numbers. Amends §48.3.

## 83. A party is a team, a goal has a route: a goal keeps itself across parties; a Release party gathers the flags (23 October 2026, the owner)

Why: the owner asked what if parties changed often: *ideation → a new mobile feature → ideation → a new feature →
testing → release*, not one party for the mobile app. Read as parties, that chain is one thing's way, not a change of
team: the features are the Mobile app party's goals, testing is its checkers and the gate, and switching party for each
step would scatter a feature's story over four parties, with no place that says where it is. What the chain does show
is two gaps: a goal sent from Ideation becomes a new goal that forgets where it came from, and a flag in main is not a
version out in the stores (a phone app has a build, a store's review, its notes and screenshots between them). So:
1. **A party is a team, and stays few** (§63.11 stays): a step of a goal's way is not a party. Testing is a party's
   checkers and the gate; a party of its own only for a team of its own.
2. **A goal has a route**: where it came from (a pitch's decision), the party it was moved from, its flag in main, the
   release it went into, and when that release was out. One line on the goal's screen; each step a press that opens
   that party with the goal picked. A goal moved or sent keeps its element where it is free.
3. **A goal moves to another party only before its work starts**: once a task of it has run, its party is where its
   work is; a new goal there is the way.
4. **A sent pitch follows its goal**: Ideation shows the goal's state (at work, in main, out), so the person sees
   whether the Investor was worth it without switching.
5. **Release is a party of the library**: its leader the **Release manager** (product's craft; a **skeleton**, the
   undead's, its own head drawn in orkUI first, a lich until then), its builders on the cheaper models (a Release
   engineer, Release notes, ASO: laborers), its Release checker a warrior. Its goal is *A release*: **what goes in** is
   the flags raised since the last release in the parties it releases from (every party but Ideation, by default),
   ticked by the person; its version, its notes and the stores' list are prepared and taken into main through the gate.
6. **Out is the person's press**: Orkboard submits nothing to a store; *Mark it out* says the version is out, and each
   goal that went in says *Out in 1.4*. In a project with a Release party, the other parties are not offered *A release*;
   without one, a party releases its own flags as today.
7. **Measured first**: the party switches a day, by face and pair, so §63.11's *seldom* is read, not assumed.
Spec 68.

## 84. On the desktop the left column is the parties: a party a heading, its goals under it; the project takes the top line (24 October 2026, the owner)

Why: the owner, on the window as built: the left column's top line (*Контент для … 0/5 · Parties ⌄*) cuts the party's
name and hides the other parties behind a deck, while a project has a few (Ideation, a product's party, Release, §83)
and a goal's route goes through them. The deck was right for the phone's one hand, not for a column that has the room.
So (reverses §65.3 on the desktop; the phone keeps its deck and sheet):
1. **The left column is a list of the parties**, in the Board's order, then Operations when the project has them,
   then *+ New party*. A party is a heading: its leader's head, its whole name (two lines, never cut), *k/n*, and one
   sign when something waits in it (a stop, a failure: §65.2 still counts only what cannot be seen).
2. **One party is open, the one the board shows**: opening another shows it (it is the party switch); the open one's
   heading cannot be closed. Under its heading: its leader (the member's row, as today), *Process now* (*Judge now* in
   Ideation), its goals as today, and **the New goal pile at its foot** (a goal's types are its party's team, §72:
   never one button for all the parties).
3. **The project takes the top line**: the project switcher leaves the top bar for the column's top, as wide as the
   column, with what waits in each project as the menu says today.
4. **The leader's big card goes**: its price and its details are behind its row's press and *About this party*, as a
   member's are. A new party's heads gather onto its heading's head (§76.3's moment, landing elsewhere).
The owner's call. Spec 69.

## 85. The project has a level of its own, and an ork for it: the Orkmaster deals the parties and a goal's party (24 October 2026, the owner)

Why: the owner: *one Orkmaster on the project, who keeps the parties and their goals in step; pressing it, the field
shows one level more: the goals in the parties' columns; and creating or picking a party goes through it.* The Board has
three levels (a party, its goals, their tasks) and a goal's route (§83) goes across parties, seen only from inside one
goal. A member does tasks, a party's leader deals the goal types and plans; nobody is above the parties. So:
1. **The Orkmaster** is the project's ork (an ork: engineering's head, its elder tier), drawn in the project's line at
   the left column's top. It plans nothing and moves nothing (§78.4, §83.6 hold): in this step it deals and suggests by
   rules, with no model.
2. **The project's level** (*The project*): a press on the Orkmaster shows the parties as the field's columns, each
   party's goals in it as decks (a goal's element and type sign, never a task's card), by where they are (*Planning*,
   *At work*, *Waits for main*, *Flags*), and a goal's route between them as links on hover. A press on a party's column
   opens that party. The phone has it as a sheet, a party a section.
3. **The Orkmaster deals the parties**: New party is its deck; the library's parties come first that the project lacks
   (Release when flags wait and no party releases, Ideation when none judges pitches), the ones it has last.
4. **A goal written on the project's level gets its party from the Orkmaster**: by its type and the parties' teams, the
   parties that can take it whole first, then those that miss one agent, each said; the person picks.
5. **Switching party stays one press** on its heading (§84): the Orkmaster is for the whole, for a new party and for a
   goal's party, never a step on the way.
The owner's call. Spec 70.

## 86. The Orkmaster keeps the parties from colliding: what two goals both touch, a spec changed under another party, a goal that waits for another party's (24 October 2026, the owner)

Why: the owner: *the Orkmaster coordinates the parties' work and the changes in their specs, so they do not collide.*
Each leader sees its own party; two parties' goals that change the same thing meet only at the gate, when the work is
done twice or undone. So (after §85, on its level):
1. **Before the work**: when a party's plan is made, the code compares what the goal touches (its page's `touches`,
   its tasks' files) with the open goals of the other parties; an overlap is a stop of the Orkmaster's in the hand:
   *<party> «<goal>» and <party> «<goal>» change the same thing*, with **<one> first** (the other waits), **One goal**,
   **Leave it**.
2. **A spec changed after the start** (§75): the goals of other parties that touch what it changed get a stop:
   *<party> changed «<goal>»: «<goal>» in <party> rests on what it was*, with **Re-plan it** (that party's leader
   re-plans what is left, as §75 does) and **Leave it**.
3. **A goal may wait for another party's goal**: its start held until that goal's flag; set only by the person's yes.
4. **Code finds, a model judges, the person decides**: the overlap is found by code (no cost); a model of the cheaper
   tier is asked only to tell a collision from a coincidence; the Orkmaster never edits another party's spec or plan, and
   nothing moves without the person's answer. Measured: its stops answered, taken or left.
The owner's call, after spec 70 is seen at work. Spec 71.

## 87. A closed party says what it is at work on, in one line (24 October 2026, the owner)

Why: the owner: *the goals the parties are at work on, in the list?* Only the open party's goals are in the left column
(§84); a closed party says *k/n* and one sign, so what the others are doing now needs a switch or the project's level.
So: **under a closed party's heading, one quiet line: its goals at work**, each its element and short name (*↻ WebAuthn
register · Session cookies*), *and k more* when they do not fit; none at work, no line. A press on a goal opens that
party with the goal picked into the filter. On the phone the same line is under each party of the parties' sheet but
the one shown. The owner's call. Spec 72.

## 88. A lighter column: a goal is one line; the open party's heading is its leader; New and Flags are rows; New goal at the Orkmaster (24 October 2026, the owner)

Why: the owner, on the column as built: *the list is overloaded.* A goal row was a small deck with two lines, a mark and
›; under the open party's heading its leader had a card of its own, then *Process now*, then *Goals n*, and at the foot
*New (n)* and *Flags (n) · k wait for main* wrapped as links, then the New goal pile. Mockup G of *Orkboard: one window*
(the phone's: H). So (on the desktop; the phone's Goals sheet takes the rows):
1. **A goal is one line**: its element, its type's sign (in its goal's colour), its title, one state's sign (at work,
   asks you, failed, flag); what its line said goes to its title (the tooltip). 28 px on the desktop, 44 px on the phone.
2. **The open party's heading is its leader**: the leader's head, the party's name, *<leader> leads* under it, the work
   sign and *k/n*. The leader's own row, its numbers and the *Goals n* heading go from the column (its price and numbers
   are in *About this party*; its question is in the hand).
3. **New and Flags are rows** like a goal's, folded: *New · n* with **Process now** at its right (*Judge now* in
   Ideation), *Flags · n* with *k wait for main* at its right.
4. **New goal is at the Orkmaster** on the desktop: a **+** beside its head in the project's line opens New goal with
   the party shown picked and its types first (spec 70 §4's form); the pile at the column's foot goes. The phone keeps its
   FAB (the thumb's), whose form already starts with the party shown.
The owner's call, on mockups G and H. Spec 73.

## 89. Moments of magic, not a theme: the seal at Review, a collision that crumbles, the empty Board in the void, the moon (24 October 2026, the owner)

Why: the owner, on how the goals read: *it is really like spells; a little more mystery?* Talking to a model is more and
more like casting. Weighed as a designer and a marketer (pixel faces, orks and races, the cards' game, now magic: four
layers on one screen), the line is **what explains stays, what decorates goes**. So:
1. **Moments, tied to an event**, never a backdrop: the arrows drawn from their start (built), a merged result's seal
   (its goal's element stamped), a sent-back result going back to the field, a collision's line that crumbles when it
   is answered, faint stars on the empty Board only, one line of words there.
2. **The moon** is a goal's progress (new to full, its tasks merged) and tonight's sign; made in orkUI first.
3. **Not**: a shimmering or moonlit background, runes on a press, a circle of the five elements at the gate, a
   first-goal fanfare, *spell* as a word of the interface, the void's colour as a general colour of magic, any magic on a
   control before it is pressed, any change to a signal (a collision, a failure, money, Stop all).
4. The landing and the clips may carry far more of it (the void, the full moon, runes): the product is the office where
   it shows in a few moments. *The orks do the work; the seal is yours.*
The owner's call, on the mockups of *Orkboard — магия целей*. Spec 74.

## 90. The Orkmaster fits the parties to the project, each in three sizes; a party's size is its Target (25 October 2026, the owner)

Why: the owner: *the choice of a party now goes through the Orkmaster: prepare three kinds of party, thrift, standard and
quality, as the toggle does now (it may go), one agent of the middle tier, a few with a leader of a high tier, a big set of
good tiers; and maybe the presets are not needed at all: an empty project gets Ideation, a mobile app gets its features,
its architecture and its release. A project need not be code: a manager's team wiki, a designer's folder.* Eleven tiles
make the person pick a team before they know what the project needs, and the Target is one switch for every party at
once whose effect is not seen where it acts. So:
1. **The Orkmaster reads what the project is**, by its files, with no model: an empty folder, a mobile app, a web app, a
   backend, a game, data work, a team's wiki, a designer's folder, texts, or code it cannot tell. An empty folder asks
   one line, *What is this project for?*, read by a model of the cheaper tier into one of those kinds.
2. **It proposes the parties that kind needs**, from recipes of the library's agents (an empty folder: Ideation; a mobile
   app: its features, its architecture, Release; a wiki: its pages and Ideation; a designer's folder: screens and
   pictures, and Ideation), each with a line of why for this project. The presets become those recipes; the library
   stays under *More* for a party of one's own.
3. **Each proposal comes in three sizes**, its price a goal beside each: **Lean**, one agent of the middle tier (the
   leader alone, its tasks done by the Grunt); **Standard**, the leader of the high tier with a few builders and one
   checker; **Full**, every seat of the recipe, builders of the middle tier at least, every check.
4. **A party's size is its Target**: Lean works as thrift, Standard as balance, Full as quality, for that party's goals;
   changed in a press in *About this party*. The Target leaves the top bar; Settings keeps it as what a party with no size
   of its own works as (the parties made before).
5. Parties stay teams and few (§83): a recipe proposes a party only for a team of its own (other agents or other
   checks), never one per step.
The owner's call. Spec 75.

## 91. The Orkmaster is crowned: a rank, not a tier (25 October 2026, the owner)

Why: the owner: *the Orkmaster could be an ork with a crown, so it stands out at once.* The Orkmaster wore `peon` ·
`elder`, the head the Taskmaster wears by default: on the project's line and at a party's heading the two stood side by
side, equal. So:
1. **The Orkmaster's head is the ork's under the crown of orkCraft's logo** (`peon-crown`: the logo's three points and
   gem, the peon's own face), drawn in orkUI as a **rank**: gear on the same
   grid and the same face, beside the three tiers and not one of them. orkUI's emblem `crown` already means *a rank*.
2. **§53.7 holds**: an agent's gear is its tier; the crown is no tier, no role picks it, no model list shows it. Only
   the Orkmaster wears it; the Taskmaster keeps its tier's gear.
3. **One picture, an accent** (§53.8): the crown is drawn into the head, never an emblem laid over it; the logo's
   gold and red toned to a muted brass and garnet under orkUI's race rules (as bright they would pass for signals).
The owner's call. Spec 76.

## 92. The field is a game table: Orkboard's wood, a surface and never a mark (25 October 2026, the owner)

Why: orkPage gave each tool its building's colour, and Orkboard's is the game table's wood (`#ac8266`, the Task Fields);
the owner: find it a place in the product, *a nod to the table cards are played on*. The Board already plays as one:
goals are dealt, the hand lies at the bottom, a party switch is a deck. So:
1. **The field is a table** (the owner picked it from the trial's options): the area the tasks are dealt on is drawn as
   orkUI's `.ork-table`, a dark walnut top in a wooden rim 3 px wide, its near lip lit.
2. **§53.5 names its third exception**: colour means a signal, except the ork green of the primary action, the muted
   heads of the races, and **the table's wood**: a material under the work, never on a control, a state, a label or a
   person's words; what lies on the table keeps its own colours, and a signal stays a signal on it.
3. **orkUI owns the wood** (§53.2): three tokens (`--ork-table`, `--ork-table-rim`, `--ork-table-rim-hi`) and the
   component, orkUI 0.8.0; Orkboard's sheets still carry no colour.
4. **Not now**: the hand's wooden shelf, the backs of a pile and the deck in wood, the phone's field, the name in the top
   bar (it stays *Orkline*, §50.1, while orkPage colours *line* copper): each its own call.
The owner's call. Spec 77.


## 93. Canvases: what an AI tool draws outside the code is a card with the elf's head (25 October 2026, the owner)

Why: the owner: *can Orkboard catch a canvas made in Claude and show it as a card, an elf's, the designer's?* The models
make more than code (a Claude artifact, a picture Antigravity or Codex generates, a file on Figma, tldraw or Canva), and
Orkboard saw none of it. So:
1. **A canvas is read, never made or fetched**: Orkboard reads what Claude Code, Codex and agy already write on the
   machine (transcripts, rollouts, the brain folder) and a PostToolUse hook that only appends a line; it opens a link in
   the person's browser and shows a local file, nothing more. No run of Orkboard's gets a tool to publish one.
2. **Design's craft, so the elf's head** (§53.6), at the tier of the model that drew it; a design role's own head when
   its task drew it.
3. **Not a signal, not a result** (§54.1): a folded row above *Waits for your look*, no colour, no count in the top bar.
4. **Not now**: a cloud session's canvases and a claude.ai chat's (nothing of them is on the machine), agy's plans,
   walkthroughs and recordings, a canvas drawn inside Orkboard.

## 94. The project's level is played on the table too: its goals are the field's cards (25 October 2026, the owner)

Why: a press on the Orkmaster turned the cards into tickets: the level drew its goals as small decks in ruled columns
on the bare canvas, a tracker's board and not the game the party's field is (§92). So:
1. **One table**: the project's columns lie on orkUI's `.ork-table`; the party heads stand above it on the canvas, as a
   party's members do above its field.
2. **One card**: a goal on the level is the field's card, 5:7, its element, state and type as the field's Planning
   card draws them; no ruled columns.
3. **Not now**: the phone's project sheet keeps its rows.
The owner's call. Spec 79.

## 95. Orkboard is published on its own, as each building's product, under its own name (25 October 2026, the owner)

Why: the owner: *Orkboard, like the other products of the buildings, will be published separately*; Orkboard first, in
VS Code's Marketplace (the extension, `vscode/`), the week after. §50.1 kept Orkboard the owner's lab, not published, and
§60.1 every lab with it; a tool used every day on other projects is worth putting in other people's hands, and its
words and shape have settled enough for that. So:
1. **Orkboard is a product, published on its own:** the app (`orkboard`, the window and the phone) and the VS Code
   extension, which starts it (`orkboard --serve`, `gui/extension.py`). The package installs from a place anyone can
   reach before the extension is listed, since the extension cannot run without it.
2. **So is each building's product** (OrkWiki, OrkWatch, OrkMine, §60.2, §60.10): published on its own once it holds
   (§60.3's order stands), each under its own name. A lab may still end in *not needed* (§60.1). One engine stands
   (§50.2): Orkline lays the same modules into loops, never a second copy.
3. **Its name is its own:** what a person reads says *Orkboard* (the window's title, the top bar, updates, settings, the
   phone, the extension). *Orkline* is the line's name and the factory's (§60.2), and §37.2's public name holds for
   Orkline itself. The state keeps its names (`~/.config/orkcraft/`, `<project>/.orkcraft/`, CLAUDE.md), so Orkboard and
   Orkline still read the same settings and Boards.
4. **A page shared with Orkline says its host's name:** where the Board's panes run inside Orkline they say Orkline, so a
   pane never names the other product.
This supersedes §50.1's *not published* and §60.1's *a lab is not published*. The owner's call.

## 96. Orkboard stays Apache-2.0; its names and the ork mark are not licensed; the licence is looked at again with running on our models (25 October 2026, the owner)

Why: Orkboard goes out on its own (§95), so others read its licence and its notices now. The owner asked the PM whether
to keep it open for the community or keep room for money (a licence of the source-available kind, the FSL, AGPL with a
commercial one). The PM's view: at the testers' stage what is scarce is people who come back (§45.11), not protection;
a tool that runs agents on a person's code and subscriptions is installed when its code can be read, and used at work
when its licence is one a company allows; and a skin is copied in a weekend whatever the licence (§60.7), so what keeps
the line its own is its names, its pace and the engine's results. NOTICE was Orkline's, and named fonts Orkboard does
not carry. So:
1. **Orkboard stays Apache-2.0**, the VS Code extension with it, as orkUI is.
2. **The names and the ork mark are not licensed** (the licence's section 6): Orkboard, Orkline, OrkWiki, OrkWatch,
   OrkMine, orkUI, orkCraft, orkWorks and the pixel ork (`design-system/logo/`, the extension's icon). `NOTICE` and
   `vscode/NOTICE` say so, as orkUI's does; a fork may say it comes from Orkboard, and goes by its own name and mark.
3. **What is bundled is named**: `NOTICE` gives each copied file's origin and licence, and each licence lies beside its
   files (orkUI's own, `gui/static/vendor/LICENSE-<package>.txt`).
4. **The licence is looked at again when running on our models is worked out** (the owner): the orks running on models
   the studio serves, beside the person's own subscriptions, is where a paid part may come; how is open. A version
   already out stays Apache-2.0 whatever is decided then: a licence given cannot be taken back.
The owner's call.

## 97. A party can be removed; its goals move to General or go with it, never while one is at work (25 October 2026, the owner)

Why: the owner asked whether a party can be removed: it cannot. A party is added (`ideas.track_add`) and edited, never
taken off the Board, so a project keeps every party it ever tried; a person's own saved parties (spec 43 §6) are removed
already, a project's are not. A party is not one file alone: its goals, their plans, worktrees and spend, the routes
that name it. So:
1. **A party is removed from its screen, on both faces** (*Remove party*), after one question that says what happens.
2. **Its goals move to General** (the default) **or are removed with it** (*Remove the party and its 3 goals*); a
   removed goal goes as `ideas.drop` has it, its spend kept in `spend-gone.jsonl`.
3. **Not while one of its goals is at work**: the question says *2 goals at work: stop them first*, and nothing is
   removed. A party's agents are never stopped by a removal.
4. **General is never removed**: it is where a goal goes when it has no party.
5. **No archive**: a party one does not want to see is closed already (§87); an archive is one more state for the column,
   the map, the project's level and the Orkmaster. Looked at again if people ask for a removed party back.
Spec 80. The owner's call.

## 98. A party picks its AI tool from a list; its size is how many agents it has and of what tiers (25 October 2026, the owner and the PM)

Why: the owner, testing: *when a party is made, pick its harness; the list of what is available may be long, so a list
that drops down*; and *the size should change the party's size itself: Lean one agent, Standard either every agent on
light models or the main ones on better models, Full the whole team on middle models and up*. Today a goal's work runs
on Claude whatever the party (`core/idea_runner.py` and `core/idea_keeper.py` `HARNESS = "claude"`); the Main tool moves
decisions only. Lean is the leader and the Grunt who does its tasks, two heads; Ideation and Release keep every seat in
every size; a library agent keeps its own tier at any size, so the size changes models only through the Target's effort;
and the switch in *About this party* changes the team only on a second confirm. So:
1. **A party has its AI tool**, picked when it is made and changed in *Edit the party*: a list that drops down (orkUI's
   select, the phone's own), the tools ready to run first, then those not signed in (picking one opens its sign-in,
   §58), then those not installed (shown, not picked). *Main tool* is the default. Its goals' tasks and its leader run on
   it; a tool with no tiers of its own (it runs its own model) says so in the list.
2. **The size is the team:** **Lean** one agent of the Seasoned tier, the leader, who plans and does its tasks itself (no
   Grunt; the owner: one Seasoned, not a Veteran on low effort); **Standard** the leader and the recipe's main seats;
   **Full** every seat, none below Seasoned, the leader and the checkers Veteran. In a party the size sets each seat's
   tier; a seat the person set by hand keeps it.
3. **Standard is the main seats on the better tier** (the leader Veteran, two builders and a checker Seasoned), not
   every seat on Novice: fewer hands to hand work between, and a light model on many seats makes more to send back.
   The owner's call.
4. **A change of size changes the team at once**, in one press, the heads that join and leave shown before it; a member
   with work open is not let go (spec 75 §5.4's refusal). Ideation and Release are sized too: Lean the leader reading
   from every side itself, Standard two views and the skeptic, Full all of them.
Spec 81.

## 99. The field is read at a glance: a row is what runs at once; a card at work turns; members are faces over their columns (25 October 2026, the owner)

Why: the owner, testing: *it is not clear which card is in progress; once every card on the field said wait*; *the
members' cards are narrower than the columns: make a member a face and a rule the width of its column*; *cards that come
later should lie lower: the first row what is done now and depends on nothing; one row, what can be done in parallel*;
*cards at work need something that turns*; *cards come into the hand unnoticed*; *the dependency arrows say nothing: do
it with rows, and the arrows in steps, not diagonals*. Today each member's column has its own rows (now, next, later) by
a goal's wave, so rows do not line up across the field; a held card (a window spent, the night, a sign-in) and a card
waiting for another are both drawn *wait*; nothing moves on a card at work; the arrows are diagonals, shown on hover;
a new stop takes its place in the fan without a sign. So:
1. **A row runs across the whole field**: the first, *Now*, holds what is at work or may start (nothing it waits for is
   open); each row under it waits only for rows above it. One row is what can run at once. The rows line up across the
   members' columns, each labelled at the table's left.
2. **A card at work turns**: orkUI's busy mark (a small pixel mark that turns, still under reduced motion) and *working
   4 min*; the member's face over its column turns with it.
3. ***Waits* and *held* are told apart**: a card waiting for another lies in a lower row (*after X*); a card held says its
   reason's sign (window, night, sign-in). When nothing is at work the table's top says why in one line (*Nothing at
   work: 2 results wait for your look*, *Claude's window is at 95 %: back at 14:20*).
4. **A member is a face**, not a framed card: the head and name over its column, and a rule the full width of the column
   under them, lit while it works, the danger colour while it calls.
5. **The arrows go in steps**: down from a card, across between the rows, down into the card that waits; square corners,
   still on hover and focus only.
6. **A new stop rises from the hand**: it comes up whole for two or three seconds, then sinks into its place in the fan;
   several, one after another; under reduced motion its edge lights instead.
Spec 82.

## 100. New goal is one field on the desktop too; the night is only for Low work and only on the person's word (25 October 2026, the owner)

Why: the owner, testing: *New goal still shows its title and what it is for apart: one field*; *only Low work is offered
the night, and only with the person's explicit permission*. The phone has had one field since §66.4, the desktop's typed
goal kept two. And the night comes without a word today: the Board puts a Low goal of low risk off to the night itself
(§57, `realm/idea_risk.py` `AUTOSTART`); closing New goal with words in it queues them tonight whatever their priority;
Ideation's *Tonight* and a held goal's *Tonight* take any priority. So:
1. **New goal is one field**, *The goal*, its first line its title (as the phone, §66.4), the type's asks under it.
2. **The night is asked, never assumed, and asked once**: one standing permission, *Low work may run at night*, asked
   the first time a Low goal is added (*Yes, at night* / *No, by day*) and changed in Settings at any time. With it,
   Low work goes at night as before; without it (and until it is answered) Low work runs by day, after the other
   priorities. No box on each goal (the owner: one standing permission, not one a goal). Only Low work goes at night.
3. **Closing New goal with words in it keeps them** (put back on the party, not started), never queues them tonight.
4. ***Tonight* elsewhere** (a pitch, a held goal) makes the goal Low as it puts it off.
5. **The night's own runs** (the leaders re-reading goals, their proposals, spec 44's pace) go under the same
   permission: off until the person says yes.
This supersedes §57.1 (the Board's own night, now on the person's standing word) and §66.4's *the desktop's New goal
is unchanged for now*. The owner's call. Spec 83.

## 101. The next task need not wait for your look: a safe result lands in dev by itself, and what depends on nothing runs beside it (25 October 2026, the owner and the PM)

Why: the owner, testing: *why does the work go on only after a merge into dev?* Because three things meet: a task that
comes `after` another starts from its merged work in dev (`core/idea_runner.py` `after_ok`, `realm/plans.py`); every
result waits at Review for the person's merge (`review` is on by default, `settings.py` `IDEAS`, for the testers' week,
§45.6), so §49.4's *code lands in dev by itself when it holds* was never on; and one task runs at a time
(`max_parallel` 1). A plan is mostly a chain, so the whole goal stands still behind one result waiting for a look. So:
1. **A result lands in dev by itself when it holds** (§49.4 as written): its tests ran and are green, no findings left,
   no risk path its goal's risk left out, no media. Anything else waits for the person's look, as now. Review becomes
   *Waits for your look* for what needs a look, and *dev → main* stays the person's gate (§49.5).
2. **What depends on nothing runs beside it**: tasks at once by size, Lean 1, Standard 2, Full 3, never past the
   window's reserve; one per member (orks never on the same files, §49.1).
3. **Not**: starting a task from a result that still waits (built on work the person may send back).
4. **`review` is off by default** (the owner: the testers' week, §45.6, is over for this): a result that holds lands
   by itself; the setting stays for a person who wants to look at each one.
The owner's call. Spec 84.

## 102. Progress is seen: the elf asks about the look before it is built, and what changed shows its picture (25 October 2026, the owner)

Why: the owner, testing: *users need more to look at and check; if this is a game the designer should send more questions
about style, pictures and so on; I sit and watch the cards move and do not feel the work progress.* Today a person is
asked about the look only by a *Pick one* (an icon, a logo, a tagline, a character, at most one a goal), by up to three
draft questions of the leader (rarely about the look), and by *Pictures you like* in New goal; a result shows its diff,
never what it looks like. So:
1. **The elf asks before it builds**: a goal that changes what people see (a screen, a flow, a landing, a level, a
   character, an icon, a logo) gets up to three questions of the look at its draft (the mood, the palette, the
   references), each with its answer picked and two or three others, as a stop in the hand.
2. **A screen is picked before it is built**: the plan of a screen's goal begins with a *Pick one* of two or three
   looks of it (§64, extended from icons and logos to screens).
3. **What changed shows its picture**: a task that changed what people see is shown as a picture of its screen
   (no model: the project's preview opened and drawn), on its card and in *Waits for your look*.
4. **A goal says how far it is**: *4 of 9 done* on its line and its stack; a card done turns over to say what it made.
5. Thrift holds (§49): questions and looks only for goals that change what people see, one round of each a goal.
Spec 85.

## 103. What the logs of the owner's day said: a task may run its project's commands, the gate runs the project's tests, a resumed session's cost is counted once, a send back that cannot help is not offered, a budget is never under its call's floor (25 October 2026, the owner and the PM)

Why: the owner's logs of 25 October (a Node game, two goals, 28 calls): the Board said **$11.22**, about **$4.5** was
spent. Read call by call:
- **A resumed session's cost was counted again and again**: Claude's `total_cost_usd` is the session's total so far, and
  the runner added it up on every `--resume`; one check task read $7.68 for about $1.13, its goal $8.73 for about $1.8,
  and was marked *cost too much*.
- **A task could run nothing**: `--permission-mode acceptEdits` with no command allowed, in `-p` with nobody to ask:
  77 of 412 turns were refused (`grep`, `cat`, `ls`, `npm test`, `python3`, `ffmpeg`), each a turn that read the whole
  context again; the Playtester never played; a pick of sounds failed twice for want of `ffmpeg`; every worktree tried
  `npm ci`.
- **The gate ran nothing**: with no `orkcraft.toml`, its `always` is Orkboard's own tests, absent from a Node project:
  18 results, *0 passed, 0 failed*, each merged.
- **A send back went round nine times**: the check said *the tests did not run*, which no session could fix, and
  *Fix the findings left* sent it back seven times, each round resuming a session of 200–600 k tokens.
- **A step's budget was under its call's floor**: one call of the leader costs $0.18–0.22 on the Veteran tier however
  little it writes (Claude Code's own context, written to the cache anew each time); Lean halves the budgets, so the
  answer to a draft's questions ($0.20) and the Orkmaster's collision judge ($0.025–0.05) ran out every time.
So:
1. **A resumed session's cost is its difference** from the session's last total, for every tool that reports a total.
2. **A task may run its project's commands**, by a list code gives it, never by a model: reading (`ls`, `cat`, `grep`,
   `find`, `head`, `tail`, `wc`, `git status|diff|log|show`), the project's own test, build and lint commands (the gate's
   and `package.json`'s scripts), local git (`add`, `commit`, `checkout`, `switch`, `stash`, `merge`, `rebase` on its own
   branch); a pick task also the media tools (`ffmpeg`, `sox`, `python3`, `node` on its candidates' folder). Never:
   `git push`, `rm -rf`, `sudo`, `curl`, `wget`, `ssh`, a package install (the worktree's dependencies are laid by code:
   the main checkout's `node_modules` (or `.venv`) linked into the worktree).
3. **The gate runs the project's tests**: with no `orkcraft.toml` `[gate]`, it is read from the project (`package.json`'s
   `test` script → `npm test`; `pyproject.toml` or `tests/` → pytest; `go.mod` → `go test ./...`; `Cargo.toml` →
   `cargo test`); with none, the result says *no tests in this project* where the tests are said, and lands only on the
   person's look, never by itself (§101.1).
4. **A finding is of the code or of the place it ran in**: a check writes `"kind": "code" | "env"`; *Fix the findings
   left* sends only the code's; a result whose findings left are all the place's offers Merge and Drop, not Send back;
   the same findings left after two rounds offer the same. A send back with a small ask starts **a fresh session** given
   the diff and the findings, when the old one is past 150 k tokens.
5. **A budget is never under its call's floor**: each step's cap is at least the floor measured for its tier on the tool
   (the last ten one-turn calls' median, else a table); Lean's draft, answer and judge run on the Seasoned tier, its goal
   reading and plan on the Veteran.
Spec 86.

## 104. A party is a small team and a lens: its leader's map of the project, drawn as cards on the table; the field goes to the Orkmaster; the spec is read in the hand; the will-be map is the contract (26 October 2026, the owner and the PM)

Why: the owner, after a day of use: *everything is automated so far that you sit and do not understand what the system
does: a card drips in now and then, a result lands in dev, the cards leave, and you never read the code.* Since §101 a
result that holds lands by itself, so the one moment a person saw a result is gone; §102's picture, *k of n done* and
*What it made* show a task's moment, and play once (§89.0: never for what changed while the page was hidden). A
prototype of a project map that plays what changed since the last look (the canvas *Orkboard — the map reveals*)
answered *what changed*, but not *was it wanted* nor *who decided*: in its own example a goal of waves removed the
player's difficulty picker, and nobody had been asked. The leaders already see the project each through one craft
(`realm/library.py`: the Architect its modules, the Product designer its flow and screens, the Product manager who it is
for and what they need, the Game designer the loop, the Investor value against cost, the analyst the metrics, growth the
channels, the Release manager the versions); they say it as text nobody reads whole. So:
0. **The frame: three parts of the window, three roles, and the person who decides.** The window: **the left column is
   where** (the projects, the parties, their goals), **the pane is what and why** (the Orkmaster's field, assets and
   play; a party's or a goal's lens: its theses, its maps before → will be), **the hand is what the person decides or
   does** (forks, out of the contract, dev → main, a to-do). The roles: **the Orkmaster says what is done and who does
   it** (it deals goals to parties, offers a party, keeps them apart); **a party's leader says how, what changes and,
   above all, why** (its lens, the spec, the will-be, the forks); **a member does** (builds or checks: one stage each),
   seen on the cards, never in a part of the window of its own. **A member never asks the person**: its question goes to
   its leader, who makes it a fork with its answers drawn on the map and its why (this changes §80's *a member calling
   with a question*); a checker's findings go the same way, as *out of the contract* or a failure.
1. **A party is a team and a lens** (§83.1 stays: a team, and few): its leader keeps **a map of the whole project as its
   craft sees it**, every goal on it, its party's own and the others'. The Orkmaster's map is the goals across the parties
   (the route, §83.2; the project's level, §85.2). A lens reads and asks; it never changes another party's work (§86).
   **A party is small, and its seats are its leader's stages**: one agent a stage at most, so a party's roles and its
   leader's stages (§72, `library.STAGES`) are one thing. **Lean** is the leader alone, running every stage; **Standard**
   the leader and its builder (the build stage); **Full** the leader, its builder and its checker. A stage keeps its
   leader's words (the Game designer's *Concept*, *Build*, *Playtest*). A party made before keeps its members.
   **The parties come ready, each leader with its lens's views**: **Tech** (the Architect: *System*, *Feature modules*; any
   code, not only a backend), **Product** (the Product manager: *Pains*, *Journey*, *Storyboard*), **Design** (the Product
   designer: *Flow*, *Screens*), **Game** (the Game designer: *Loop*, *Economy*, *Levels*), **Marketing** (growth:
   *Channels*), **Data** (the analyst: *Metrics*), **Ideation** (the Investor: *Bets*), **Release** (the Release manager:
   *Versions*). The Orkmaster offers the ones a project's kind needs (§90's recipes become these parties); a leader of a
   person's own is the rare, particular case. *Lens* is §53's word widened: the lens a leader points with at a new goal
   (`realm/idea_lens.py`: Code, Screen, Pain) is the one it keeps of the whole project, and the Architect's *System* is
   read by `realm/code_map.py` already.
2. **A map is a field of cards on the table, never a diagram** (§92): a part is a card (5:7, its goal's element top
   left, its kind's sign top right), a group a column or a stack, an order the field's arrow (few, short). What happens
   to it is the field's own motion (§89): new is dealt, changed is sealed with its goal's element, gone crumbles,
   promised is a ghost, at work turns with its member's head. **A card is read, not guessed**: on the desktop a card is
   128 x 180 (5:7; was 104 x 146 at most) and its name shows up to four lines (was two, about 12 characters a line, so
   cut almost always); the planner writes a task's name short (60 characters at most, the verb first); the whole name on
   hover and on a lifted card. The phone's tokens stay 74 px (spec 67).
3. **A map is read from the project where it can be**, with no model: modules and imports, routes and screens, the
   Board's goals and flags. A lens of judgement (people and needs, value, channels) is the leader's and the person's,
   kept in the project's state, marked as theirs and corrected by the person. A part has a stable id; a map keeps its
   layout.
4. **Every goal starts at the Orkmaster** (§88.4 on every face): one field; it deals the goal to a party by rules
   (§85.4), or, when no party covers it, offers one of the library in its three sizes (§90).
5. **The spec is read, not studied**: short theses (*Done when*) at the left, the leader's map **before → will be** at
   the right, **the leader's questions as cards in the hand** (three at most, §102.1), each with its answer picked and
   its change drawn on the map; selecting a card lights what it is about, an answer redraws the will-be. Every answer's
   change is written in the draft's own call, so a press costs no call (§103.5); only one's own answer does. A comment
   is pinned to a card or a thesis and goes to the leader with the others, in one call. *Start* when every card is
   answered. The full text is the agents', behind *More*. A goal that changes no map (a bug, a tidy, a balance pass)
   keeps today's way.
6. **The will-be is the contract**: the plan's call writes the map's change, each part of it tied to the task that makes
   it. At work, the promised cards are ghosts that fill as their tasks merge, with the working member's head on a card at
   work: the map is the goal's view at work too.
7. **Two levels, two questions**: **the Orkmaster's level holds the field**: every party a column on the table (§85.2,
   spec 79), its tasks at work as the field's cards with their member's head: who does what across the project, what is
   stuck, what it costs. **A party's level is its lens**: the left column lists the parties, a party's goals and specs
   under each. The project's name in the Orkmaster's line is the projects' switcher (spec 69's, moved there): one
   Orkmaster's head, the open projects in a list, each with one mark (waits for you, at work, or none); not tabs.
8. **The right pane is the lens's views, as tabs**: a party picked shows **Overview** (no prose: short lines under *Now*,
   *Next*, *Waits for you*, *Changed since your last look*, each leading to its part; and the leader's stance in a
   sentence or two), then **one to three views of its lens** (maps before → will be, as cards: the Product manager's
   *Pains*, *Journey* and *Storyboard*; the Architect's *System* and *Feature modules*; the Game designer's *Loop*,
   *Economy*, *Levels*; the Product designer's *Flow* and *Screens*), then **Board** last (the Orkmaster's field
   filtered to the party). A goal picked shows its tabs by its state: **Spec** (theses and the hand's questions), **Will
   be** (only the views it changes), **Board** (its tasks, at work), **Result** (promised → made, done), and opens on the
   tab its state names. Five tabs at most. A leader's views are set in the library, as its stages are (`STAGES`), never
   made up by a model. A tab with a change not yet seen carries the goal's element by its name; opening it plays its
   reveal. **The hand is one, under every tab**: a card pressed opens the tab it is about and rings its parts. On the
   phone the views are a list under the title (no sideways scroll, spec 67).
   **No drawer**: a hand card opens in the pane, never in a drawer from the right. A decision about a map (a question, a
   fork, out of the contract, dev → main) **lifts the card in the hand**, its answers on it, while the pane shows the tab
   it is about and each answer's change on the map; *Put it back* lowers it. A thing that is no map's (a task's log, a
   diff, a failure, a pick's variants, a to-do's steps, a document, Agents, Files) opens as **one temporary tab** at the
   end of the pane's, with ×: another replaces it unless it is pinned; *Back* returns to the tab before. The window is
   three parts: the left column (where), the pane and its tabs (what), the hand (decide). On the phone, the same as
   screens: a lifted card over the map, a thing opened as its own screen.
9. **During the work the hand holds only what asks a decision**: a **fork** (a choice the plan did not settle: its
   answers drawn as changes on the map; only the tasks after it wait; §64 from pictures to structure), and **out of the
   contract** (a task whose map removes a part, or adds an outward one, that the will-be did not promise: asked before
   that task's merge). Progress is never a stop. *Back to the spec* stops only the tasks whose part changed (§75.3). **A
   to-do comes last**: something the person must do themselves is a line in the spec's theses until the next task cannot
   start without it; only then is it dealt, after the forks and questions, with *Remind me when it's needed*. **dev → main
   is one card for the batch** (*4 goals ready for main*), its promised → made of them all; never a card a goal. No count
   of what waits anywhere (§67): the hand is the count.
10. **Work in progress is quiet**: an hourglass of orkUI's (7 x 7, the faint ink, a grain a second, turned over in a few
   steps, still under reduced motion) replaces `.ork-busy`'s running pixels; the moon stays a goal's progress (§89), and
   only a signal (a question, a failure, money) draws the eye. Made in orkUI first, then copied.
11. **Assets: what the project is made of, seen and touched**: the Orkmaster's level has tabs of its own, **Field**,
   **Assets** and **Play**. Assets lays the project's own files out by kind as cards on the table (its screens from §102's
   pictures, art and icons, sound, music, clips, fonts), each card's face the thing itself; a card lifted shows it large
   and plays a sound or a clip; a changed one turns over to its version before; the variants not picked in *Pick one*
   (§64) lie under the one picked; a change not yet seen carries its goal's element. Read from the files, git and the
   picks, with no model. **Play** opens the project's own preview (§102's) of dev in the pane, kept apart from the page;
   not on the phone. A goal's *Result* holds its assets.
12. **The reveal**: when the person opens the map after being away, it plays what landed since their last look (or since
   a release), promised against made; a press on a card says which goal changed it and how. The opening is the press,
   so §89.0 holds.
13. **What it replaces, once built** (else it only adds): the list of results on the right (*Waits for your look*, its
   reasons, §101) becomes cards in the hand (*out of the contract*, a failure, dev → main); *k of n done* and *What it
   made* (§102.4) become the map's cards; the spec's sections as the face (§75) become theses, map and hand; collisions
   by `touches` (§86) become two changes on the same cards; *Pick a look* (§102.2) becomes a fork; a party's field, its
   members' columns and its stages' seats (§99, §72) become the Orkmaster's field and a party's *Board* tab; the
   projects' switcher at the left column's head (spec 69) moves to the Orkmaster's line; the drawer and its tab per
   thing opened (spec 33 §6, spec 39 §3, spec 49 §9; `js/shell/preview.js`) become the lifted card and the pane's one
   temporary tab.
14. **First, with no measure needed**: the faces' small changes (the hourglass, the cards, the to-do last, a party's
    seats as its stages; spec 87) and Assets and Play (11; spec 88). **Then in phases, each measured before the next**:
    (1) the lenses read from the code, and the reveal, on one real
    project (a Node game): can the owner tell the day in a minute, and did they see what an agent decided alone; (2) the
    change in the plan's call, the spec screen with one *Start*, out of the contract; (3) progress on the map and forks,
    the tabs, and the replaced parts of 13 removed; (4) the lenses of judgement (pains, journey, storyboard, value), each
    view kept only while it is opened. The words (*lens*, *map*, *view*, *will be*, *fork*, *contract*) get their one word
    each in `TERMS` with the first spec; a part of a map is not called a *card* where a person reads it (spec 70 §0).
The owner's call. The mockup *Orkboard — the map on the table* first; the specs are written from it.

## 105. What the first look said: Play opens the page, not a port; the right column is where a thing opened is seen; Assets fills the table; a party is removed from its menu; System is the project's architecture, not its folders (26 October 2026, the owner)

Why: the owner opened their game (a Node party game: `client/` on Vite and React, `server/` on Express, `config/`
shared) on the Orkboard of specs 87–89: *I could not find how to remove an old party; Assets is the right tab but its
table is almost empty and a preview opens over the whole window; Play shows a white page, "Cannot GET /"; System looks
like a tree of folders, I want an overview of the architecture, cheaply; take Waits for your look away and show every
preview in the right column, wider, not over the pane; let the tabs and the faces lie on the table.* Play had started
(`play_started`, ok, 3.2 s): the first port that listened was Express's, which got the `PORT` Orkboard set; Vite's page
was on another. So:
1. **Play opens the page, not the first port**: every port the command prints, and `PORT`, is asked for `/` (and the
   configured `preview_path`); the first that answers a page (2xx, `text/html`) is shown. None: a plain line says the
   build started but no port gives a page, and how to name one (`.orkcraft/checks.toml`). The same choice serves §102's
   pictures. **While the build starts, the pane is black**: the project's name in the pixel face comes up and fades, a nod
   to a console's start screen, and the page comes out of the black only once it answered. Never a white frame.
2. **The right column is where a thing opened is seen** (§104.8's temporary tab, at the side): the drawer becomes the
   window's right column, about 480 px, **pushing the pane, never over it**, and **there is no right column while
   nothing is open**: the pane takes the width. An asset, a part of System, a task, its log, a diff, a document open
   there. What stood in the right column goes: *Waits for your look* to the hand (§104.9: what needs a look is a card),
   *Merge dev into main* to one card in the hand (*n goals ready for main*) and a quiet line in the project's line, the
   canvases (§93) to Assets, as assets of their own kind, the AI tools' limits to *Spend* in the top bar.
3. **Assets fills the table**: its kinds lie as sections one under another, each section's cards wrapping across the
   whole width; a stack still folds a folder. A card pressed opens in the right column (2), never over the window.
4. **The table starts at the pane's top**: a party's tabs (*System*, *Board*) and its members' faces lie on the wood, as
   tabs on a table's edge, so the table is never cut by a strip over it.
5. **A party is removed from its menu**: *Remove party* is on the party's menu in the left column (a right click, or its
   **…**) and on its column at the Orkmaster's level, the Orkmaster's being the parties' keeper (§104.0); the question is
   spec 80's, and *Edit the party* keeps it too.
6. **System is the project's architecture, read with no model** (§104.1's *System*; the folders become *Feature
   modules*): **its containers** (each folder with its own `package.json`, `pyproject.toml`, `go.mod` or `Cargo.toml`,
   and the root's own code), **each container's stack** (its dependencies, by a list of known libraries: React, Vite,
   Express, Socket.IO, …), **how the containers talk** (HTTP routes a client calls and a server answers, socket events
   emitted and handled, read by patterns, the arrow named by them: *HTTP: 6 routes · socket: 4 events*), **its ways in**
   (`index.html`, a `listen`, `bin`, scripts), **its layers** inside a container (by the imports: what nothing uses on top,
   what everything uses at the bottom; and a list of folder roles: views and components are its face, routes and api its
   doors, db and models its data, config its settings), and **what is shared** (a file both a client and a server use,
   like `config/balance.ts`, a part of its own: a change there touches both). The cards and the reveal stay §104.2's.
Spec 90.

## 106. Warm: easier on the eyes. The ground lifted, the ink softened, warm greys, the interface in IBM Plex Sans; the pixel face for titles, headings and buttons only (26 October 2026, the owner)

Why: the owner, on the Tech party's System: *the architecture reads badly: the pixel font tells on small modules, the
text on the brown reads oddly, and white text on such a black screen strains the eyes.* Measured: full ink on the canvas
was 16:1 (a glare, not legibility), a card on the table 1.01:1 (it melted into the wood), labels in the pixel face at
12 px, the body in a 12 px monospace and captions down to 10 px. Three palettes were drawn side by side (now, soft,
warm); the owner took soft (orkUI 0.12.0), then **warm** in its place (orkUI 0.13.0): the same rules in warm greys.
1. **orkUI 0.13.0** (made in orkUI, copied here as §53 says): canvas `#16140f`, panel `#1f1c17`, raised `#2a261f`, frame
   `#3d372d`, edge `#958a78`; ink `#e0dbd0` (13:1 on the canvas), muted `#b0a899`, faint `#9a9284`; every text pair
   still AA, the ink AAA. Still dark and monochrome: the warm tint is the ground's, colour stays a signal (§53.5).
2. **The table is a quiet warm grey** (`#1b1813`, its rim `#3d372d`), a step above the canvas; a card on it is raised
   (`#2a261f`) in its frame line, so it reads as a card.
3. **The interface reads in IBM Plex Sans** (orkUI 0.12.0): labels 12 px semibold caps, the body 14 px, captions 12 px
   (the phone 14, 16, 13). The pixel face is for titles, headings and buttons, never under 13 px and never for a person's
   words; IBM Plex Mono for code, paths, diffs, logs and terminals. **No text under 12 px.**
4. The heads whose edges fell under 3:1 on the lighter raised are one step lighter.
orkUI 0.12.0 and 0.13.0; spec 40.

## 107. The owner's list: the limits always seen and what used them, a quieter top bar, Play that breathes, an AI tool for each seat, New party in two halves, parties and goals beside the Orkmaster (26 October 2026, the owner)

Why: the owner, after a day on their game: *I liked it when the limits' percentages were seen without opening anything;
clean up the top right: Agents goes, Files goes into the Orkmaster's assets, Settings is a word after Orkboard, only the
limits and Stop all stay on the right; the toast was easier to see at the bottom; while the project builds the name could
come and go in a loop; making a party is still heavy: presets on one side, the team by stages on the other, the size
switched at once, each member's own AI tool (only Antigravity makes pictures today), the levels from the size; and the
New goal and New party buttons together beside the Orkmaster, in two rows, without twenty kinds in a row.* The mockups were
drawn and agreed the same day. So:
1. **The top bar's right is the AI tools' limits and Stop all**: a chip a tool, always seen; a press shows **what used
   it**, by party and member, estimated from the reads of the limit and the tokens of each call, with *Outside Orkboard*.
   *Settings* is a word beside the product's name. *Agents* and *Files* leave the bar; the files are in the Orkmaster's
   *Assets and files*.
2. **The toasts are at the page's foot** again (spec 90's top goes).
3. **Play breathes while the build starts**: the name fades in and out, the stage and the seconds under it; a failure
   shows the command's last lines.
4. **A seat has its own AI tool** (spec 81's *later call*, made now): the party's by default; the list says which tools can
   do what the role needs (pictures, sound) and why the others cannot.
5. **New party is two halves**: presets by the project's stage and by craft, and *Your own*, on the left; the team by
   seats (*Leads*, *Does*, *Checks*) on the right, the size changing seats and tiers at once.
6. **Beside the Orkmaster, two rows**: *Parties* (New party and two or three proposals) and *New goal* (one line, the party
   guessed, at most three kinds and *More kinds…*).
7. **Antigravity runs a task's commands** (the owner, the same afternoon, after its tasks came back empty: *let it run
   them in its sandbox*): agy's work skips its asking (`--dangerously-skip-permissions`), `--sandbox` keeping it to the
   task's worktree and the Warder's hook judging each command where it is installed; its reads (a spec, a plan, a talk)
   still run no command. The building's autonomy never reached a task's run, so it is no longer agy's condition.
Spec 91.

## 108. Running the project is a party by the project's kind; working with people is a party, Team; Operations are no longer a tab (26 October 2026, the owner)

Why: the owner: *Operations should not be a permanent tab but a party. We have LiveOps for games; something like it should
exist for other kinds of project: apps, services, an LLM wiki, and managing a team of people.* A permanent row in every
project's column holds what is the person's own and belongs to no project (§51.1), and a game's running after launch already
had a party of its own (spec 91 §7). So:
1. **The project's running is the fifth stage, a party for every kind of project**, named for what the project does when it
   runs: *LiveOps* for a game, *Run* for an app, a site, a service, code and data, *Upkeep* for a wiki, a design and texts.
   Made of the library's roles; it proposes two to four **recurring goals** when it is made (Run: *Weekly dependency check*,
   *Read the new reviews*, *Look at the crashes*; Upkeep: *Find stale pages*, *Check the links*, *Take in the new sources*;
   a game's LiveOps: the week's numbers, what players say, the crash reports, the next event), each ticked and left out by
   the person if they do not want it.
2. **A recurring goal is an ordinary goal that comes back** every day, week or month once it is done, with the same words in
   the same party; the done one stays as the record of that round. (The owner's brief said *the existing recurring-goal
   mechanism*; there was none, so this is it: a `repeat` on the goal's page and the host's clock.) It starts no model of its
   own, is seen and stopped from its drawer, and ends with its party.
3. **Working with people is a party, Team**, that the person puts in the one project they choose, e.g. their team's wiki. It
   holds today's Operations, unchanged in behaviour and in storage (the person's folder, §51.1): the templates (the daily
   brief, the email reply, the Jira task, the 1:1, the refinement, the retro), runs, checks and history. Its Board is
   Operations' list in place of goal cards; its leader is the Product manager; it is in New party on every kind. **There is
   one Team party across all of the person's projects**: elsewhere it is offered greyed, *Team is in <project>*. It holds no
   goals.
4. **The permanent *Operations* row goes** from the left column, on the desktop and on the phone, as soon as a Team party
   exists anywhere. Until then Operations stay reachable where they are, with the line *Make it a Team party*. What exists
   (runs, kept rules, standing) stays as it is; the Team party shows it, and removing the party gives the row back.
5. **Words**: `TERMS` says *Team* (a party that holds the person's Operations), *Run*, *Upkeep* and *recurring goal*;
   *Operations* stays the person's list, one for all projects, now reached through Team.
Spec 92.

## 109. A party does one kind of work and is its lens; a goal is one, and goes through the parties its work needs; the left column is the Orkmaster's goals; the Board is the Orkmaster's alone (27 October 2026, the owner and the PM)

Why: the leaders' lenses (§104.1) quarrel with the parties as they are made. A party mixes crafts (the game's party: the
Game designer leading Grunts and artists; the app's *features*: the Product manager leading code), and since §91.7 the
stages are parties whose leader changes with the kind (an app's Build led by the Product manager, a site's Run by the
Architect), so a leader's lens (*Pains*) is not what its party does (screens and code); *System* is drawn only where
`g.leader.slug == "architect"` happens to hold, and a game's code has no map unless a Tech party is added beside it.
§83 refused a party a step, because a goal's story scattered over parties; it is kept here by making the goal one, not
its party. So:
1. **A party is one craft, one kind of work, one lens**: its leader's craft is the work of all its seats. A game:
   **Game design** (the Game designer: *Loop*, *Economy*, *Levels*; it judges a game's ideas, Ideation's place),
   **Tech** (the Architect: *System*), **Art** (the Art director), **Release**, **LiveOps**. An app or a site:
   **Product** (the Product manager: who it is for and whether it is worth it, Ideation's place), **Design** (the Product
   designer: *Flow*, *Screens*), **Tech**, **Release**, **Run**. The mixed recipes (`game`, `mobile-features`,
   `web-pages`) and the Investor's Ideation as a project's party go; §91.7's stages are no longer parties but steps of a
   goal (2). A party made before keeps its members and its name.
2. **A goal is one and has a route of steps**, each a party's (§83.2 widened): *Concept · Game design → Build · Tech →
   Art · Art → Playtest*. The goal does not move: its step is handed to the next party, its page, story and element stay
   one. **The Orkmaster deals the route** (§85.4): only the steps the work needs (a bug: Tech alone; a balance pass: Game
   design and one task of Tech). The first step's leader writes **the one spec**, its theses by craft (a *Done when* for
   the design, the code, the art); each next leader plans its own step (a cheaper call), never rewrites the spec; a
   question back to an earlier step is a fork in the person's hand, never a talk between parties (§104.0). This changes
   §83.1 (a step of a goal's way may be a party now) and §83.3 (a goal goes on to another party after its work started,
   by its route, not by being moved).
3. **The left column is the Orkmaster's goals**: under the Orkmaster's line, every goal of the project, no party's
   heading over them and nothing to unfold; a goal's row says its step (the party's leader's head) and its route in one
   line. Under the goals the parties, a row each, a press opening its lens. The open party's goals under its heading
   (§84, spec 69, spec 73) go.
4. **The Board is the Orkmaster's alone**: its field (every party a column, its tasks with their members' heads, §104.7)
   is the only Board. **A party picked shows only its lens**: *Overview* (§104.8: *Now*, *Next*, *Waits for you*,
   *Changed since your last look*: the goals at its step and those coming to it) and its views; no *Board* tab (spec 89
   §6.1, spec 90 §6.7). A goal picked shows *Spec*, *Will be* (the views of the parties on its route) and *Result*; its
   tasks at work are on its Will be (§104.6) and lit on the Orkmaster's Board.
5. **System is the project's map, kept by Tech**: Tech draws its will-be; another party sees on it what its step touches
   (a lens reads and asks, §104.1). *Feature modules* is a container opened on System, not a tab (§105.6).
6. **The lens of New goal is the parties' maps**: pointing at a goal is pressing a part on a view of the route's parties
   (§53's Code, Screen, Pain become the parts of System, Screens and the Product's pains); with no view, the text.
7. **The phone**: the same list under the Orkmaster; a party's sheet its views as a list (spec 67).
8. **Measured**: the steps a goal takes, the calls each step costs against a goal in one party, and the forks asked back.
The owner's call. Spec 93.

## 110. The leaders are the pane's tabs; a party's header says what it does, holds its squad and its lenses' views as a segmented control; the left column is what is looked at, the tab who looks (27 October 2026, the owner and the PM)

Why: after §109 a party is a way of looking, not a place: a row of it among the goals in the left column (§109.3) mixed
two kinds of rows, goals pressed all day and parties seldom. A party's seats, their AI tools and tiers were behind *Edit
the party*, away from the map and from the limits they spend. So (this makes §109.3–§109.4 and §104.8 precise):
1. **Two axes**: **the left column is what is looked at** (the whole project or one goal), **the pane's tabs are who
   looks** (the Orkmaster, then each party's leader: its head and the party's name), the pane is the one through the
   other. The whole project through the Orkmaster: the Board; through a party: its views as they are. A goal through the
   Orkmaster: its spec (theses, route, *Result*); through a party: the goal's will-be on that party's views. The pane's
   title says both (*Waves · through Tech*).
2. **The left column**: the Orkmaster's line (the projects' switcher), the one field of *New goal* (§104.4), *The whole
   project*, then the goals **by their state**, not by party (*Waits for you*, *At work*, *Next*; *Done* folded; no
   count, §67); a goal's row its element, its name and its route as the leaders' small heads, its step lit, the steps
   done faint. No party rows (§109.3's go).
3. **The tabs**: the Orkmaster first, then the parties in their route's order; they lie on the table's edge (spec 90
   §4), never in the top bar. *+* at their end is *New party*; a tab's right click or **…** is §105.5's menu. A goal
   picked: the tabs of its route carry a dot, its step's its element; a tab off its route is faint and still pressed (a
   lens reads, §104.1). Picking a goal opens the tab of its step; then the tab stays as the person left it. A tab whose
   view holds a decision of the hand carries the signal's mark, no number; a hand card pressed opens its tab, its view
   and its goal (§104.8). More than six parties: the tabs shrink to the heads, the name on hover.
4. **A party's header, one band over its views**: at the left the party's name (the pixel face), what it does in one
   line (its recipe's `line`) and the leader's stance in one sentence (moved here from *Overview*, §104.8: seen under
   every view); in the middle **its squad**; at the right **its views as a segmented control**, an icon and a word each,
   *Overview* first. The Orkmaster's header: what it does (*Deals goals to parties*), its own AI tool and tier, and
   *Board*, *Assets*, *Play*.
5. **The views are looked at, not cast**: the segmented control is a switch (the picked one pressed in), never a bar of
   skills (no cooldown, no glow, no burst on a press). A view's word is what it shows (*System*, *Screens*, *Loop*), never
   a spell's name; the orkish is the icon's and the leader's head. The icons are orkUI's, drawn there first. A view with a
   change not yet seen carries its goal's element; a goal picked dims the views it does not change (still pressed).
6. **The squad in the header**: a seat by its stage (*Leads*, *Does*, *Checks*, §107.5), at most three: the member's
   head with its tier's gear (§53), its AI tool's name under it, turned while it works (a press: its task on the
   Orkmaster's Board); an empty seat a ghost (*+ Checker*), a press grows the party's size. **A member's description is
   never in the header**, only on hover and in its popover.
7. **A head pressed opens a small popover beside it** (no drawer, §104.8): the member's name, its role's line and what it
   does in this party; **its AI tool** (§107.4's list: the tools that can do what the role needs, the others with why
   not); **its tier**, each with what it costs said plainly; **when it takes effect**, plainly: *From the next task; the
   task at work finishes on <tool>*; then *Set* (nothing changes before it), a toast at the page's foot with *Undo*
   (§107.2); at its foot *Take off the seat* and its role on Agents. *Edit the party* keeps the rest (the leader, the
   recipe, removing the party).
8. **A member never speaks from the header** (§104.0): no question mark or bubble on a head; its questions go to its
   leader, and to the person only as a fork in the hand. The header shows who works, never their tasks (the Board's).
9. **The phone**: the leaders' tabs a row of heads over the screen (six at 44 px fit 390 px); the header one line (the
   name, what it does, the squad's heads), a head pressed opens a sheet with the popover's content; the views as icons
   when three or four, else a list under the title (spec 67: no sideways scroll); the goals the first screen's list.
The owner's call.

## 111. Play is what is looked at, not a lens: the whole project or one goal, under every tab, opened where the goal changed it; Tech keeps how the project runs (27 October 2026, the owner and the PM)

Why: §110.4 put *Play* among the Orkmaster's views, and the owner asked for it under Tech, to run *only what is new for a
goal*. Play is the project itself, touched: the parties that need it most are Game design (a playtest), Design (the
screens alive) and Product (the way through), so under Tech's tab a game's designer would look through other eyes to
play; and a goal's new part cannot run alone (waves need the whole game). What Tech owns is how the project runs. So
(this changes §110.4: the Orkmaster's views are *Board* and *Assets*):
1. **Play is on the left column's axis, not the tabs'** (§110.1): a ▶ in the pane's title under every tab plays what
   is looked at. *The whole project · through Game design ▶ Play*: dev's head, as §102 and spec 88. *Waves · through
   Tech ▶ Play this goal*: the goal's own build. It opens as the pane's one temporary tab (§104.8), never in the right
   column (§105.2: too narrow for a game).
2. **A goal's Play is dev with the goal's work**: the tasks of it landed and those not landed yet (each task's result as
   Review would merge it), in a worktree of its own, so its result is played before it is in dev.
3. **It opens where the goal changed the project**: on the screen or route its work touched (its tasks' files read
   against the routes and screens, §105.6's ways in, §102's pictures; else the goal's own screen, else `/`), with a strip
   over the frame, **What this goal changed**, a press on each opening its place (*Waves*, *Lobby*). Nothing to find by
   hand.
4. **One Play a project at a time** (spec 88): a goal's Play started while another plays asks once, plainly, *Stop the
   project's Play and play «Waves»?* Before and after side by side (two builds) is later, its own call.
5. **Tech keeps how the project runs**: its *Overview* says it in one line (*Runs: client + server, ports 5173 and
   3001*); the commands, ports and the build's log are Tech's, and a Play that did not start leads there (its failure's
   lines, §107.3), not to the Orkmaster.
6. **The phone**: Play stays the computer's (spec 88 §7); a goal's row says *Play it on the computer*.
The owner's call.

## 112. System reads what the project really is, a container a card first; a change on a map says who decided it; the lenses of judgement are drawn from what the project has, and the ones with nothing to read wait (27 October 2026, the owner and the PM)

Why: `system_overview.read` run on Orkboard itself (a Python host, a JavaScript page, a VS Code extension) found no link
at all, though the host and the page talk all day over a WebSocket (`ask("ideas.x")`) and the extension starts the host
(`orkboard --serve`); its ways in held test files (`listen`), its parts `docs/…` and `vendor/`, and its layers had no role
(`core`, `realm`, `gui` match no folder role), so the rows said nothing. And §104.14's phase 1 asks *did the owner see
what an agent decided alone*: no map says who decided a change. The lenses beyond Tech's (§104.1) were listed by craft,
some with nothing in the project to read them from, which §104.3 forbids. So:
1. **The links a project really has**: beside `fetch` and `socket.emit`, the patterns of a command or RPC channel (a
   name a client sends and a host dispatches: `ask("x")` / `"x":` handlers, JSON-RPC, tRPC, gRPC, a WebSocket's message
   types) and a process one container starts of another (`spawn`, `exec`, a CLI's name in its scripts); the arrow named
   as now (*commands: 40 · starts*).
2. **Nothing that is not the project's working code**: tests are never a way in (a `listen` under a test folder or in a
   test file), and `docs/`, vendored copies (`vendor/`, a folder with its own licence beside a copied library) and
   generated output are not parts.
3. **Layers that say something**: a layer's role from the folder roles when they match; else the rows are named by the
   axis (*Nothing uses these* at the top, *Everything uses these* at the bottom), never left blank; and a project's own
   words when it has them (its CLAUDE.md's or README's *Where code goes*, read with no model: a heading and the folders
   it names).
4. **A container is a card first**: System opens on one card a container (its stack, its ways in, its marks of change)
   and the named arrows between them; a press opens the container's parts (§109.5's *Feature modules*, laid in its
   layers). The architecture in a minute is the measure.
5. **The reveal from a chosen point** (§104.12 made precise): *Since your last look* by default, *Since <version>* when
   the project has a release, picked over the table.
6. **A change on a map says who decided it**: a changed, new or gone card carries, beside its goal's element, **the
   person** (an answer of theirs in the hand or the spec), **the leader** (written in the spec or its plan), or **a member
   alone** (made by a task and promised nowhere): the last in the signal's colour, with *out of the contract*'s card
   when the will-be was set (§104.9). Read from the spec, the plan and the answers, with no model.
7. **Design's *Screens* and *Flow* and Product's pains are read from the project**: the screens from §102's pictures and
   the routes (a router's table, a `pages/` or `screens/` folder), the flow from the links between them; Product's pains
   are pinned to a screen or a step of the flow, never a free list (§53's Pain, kept in `segments.json`, gains its
   place). *Journey* is the flow seen by a segment.
8. **Game design's *Loop* is a frame of four to six cards** the person and the leader keep (§104.3's judgement, marked as
   theirs), each tied to the parts and configs it rests on (`config/balance.ts`), so a goal that changes them shows on
   the loop.
9. **Cut, or wait for something to read**: *Storyboard* goes (the flow and the screens hold it); *Versions* goes (the
   hand's *n goals ready for main* and a goal's *Result*); *Economy*, *Levels*, *Channels* and *Metrics* wait until the
   project has where they are read from (configs, levels' files, analytics), never a model's drawing of cards.
10. **A leader's views are the library's**, beside its `STAGES` (§104.8): a party shows the views its leader has there,
   never by testing which slug leads it.
The owner's call.

## 113. Play runs every process the project needs, a client and a server together; a mobile app plays as its web build in a phone's frame, and on the person's own phone over the local network when they allow it (27 October 2026, the owner)

Why: Play runs one command (`.orkcraft/checks.toml`'s `preview`, else the root's `dev|preview|start`) and shows the first
port that answers a page (spec 90 §1). A project of a client and a server plays only when its root has a script that
starts both; otherwise one of them is missing. Every command gets the same `PORT`, so two cannot share it, and a
client's proxy names its server's port by hand (`localhost:3001`). A mobile app (Expo, React Native, Flutter) has no
page at all unless its web build is asked for, and its real behaviour is on a phone, which spec 88 §5 keeps from the
preview (`127.0.0.1` only). So (this changes spec 88 §5 for the case in 3, and only there):
1. **Several processes**: `checks.toml` may list them (`[[play]]`: `name`, `dir`, `run`, `port`, `page = true` for the
   one shown); with no list, Play reads them from the containers (§105.6, `system_overview`): each with a `dev` or
   `start` script, the one with a page (its stack's UI, an `index.html`) shown. **The order**: a container another one
   calls starts first (§112.1's links), the next once it listens. **The ports**: a process gets `PORT` only when it has
   no port of its own; one named in the project (a proxy's target, a `listen(3001)`) is kept, and a port already taken
   is said plainly (*Port 3001 is taken: stop your own dev server, or name another port in .orkcraft/checks.toml*).
   **One group**: each process its own process group and its own last lines; one ending stops them all, and the failure
   says whose. **The start screen** (spec 90 §1.3, §107.3) holds a line a process: *server · listens on 3001*, *client ·
   building…*.
2. **A mobile app's web build in a phone's frame** (a): an Expo or React Native project plays `expo start --web`, a
   Flutter one `flutter run -d web-server`, as one more process of 1; the frame is a phone's (`preview_size`, 390 x 844
   by default), and a line under it says plainly what it is not: *The web build: native modules, the camera and gestures
   behave otherwise on a phone.*
3. **On the person's own phone** (b), off by default, a setting of the project: **Let my phones open the build**, its
   words saying what it opens: *While Play runs, the build's port (Metro's, 8081) is open to every device on this
   network, not only your phones.* On, Play starts Expo's server listening on the local network, shows its QR code and
   `exp://` link beside the frame, and sends the link to the paired phones (a card on the phone: *Open in Expo Go*).
   Only that port, only while Play runs, only on the local network (never a tunnel); off, or Play stopped, it is closed.
   The phones' listener still never serves the preview itself. Each start with it on is an event (`play_lan_opened`,
   the port and the address).
4. **A simulator or an emulator in the pane** (c) is not made: a native project without a web build says so plainly
   and how to play it outside (*npx expo run:ios*, *flutter run*).
5. **Until it is built**, a project plays both by a root script (`concurrently`) or `preview` in `checks.toml`, as
   today.
The owner's call.

## 114. A goal's row carries its signs: the hourglass while it works, a failure that does not look like closing; a sign pressed lifts its card in the hand, where Retry and Start are (27 October 2026, the owner and the PM)

Why: the owner: a goal's red cross reads as closing the goal, and the hourglass and *Retry*/*Start* could be at each goal
in the left column. ✗ is everywhere the sign of closing or removing, the more so at a row's end where a close stands;
and *Start* (every question of the spec answered, §104.5) and *Retry* (new calls, money) are decisions, the hand's
(§104.0), dangerous as buttons in a list scrolled all day, and two ways in to one act drift apart. So (§110.2 made
precise):
1. **The hourglass is the row's** (§104.10, the faint ink): a goal a member works on now; in *At work* it tells working
   now from waiting its turn.
2. **A failure is not a cross**: orkUI's alert in the signal's colour (an exclamation, or a cracked gem: drawn in orkUI
   first, then copied), never ✗, and never at the row's end; on hover *Failed: <why>* (§65.2's ✗ goes, on the desktop
   and the phone).
3. **The sign is the way in**: a press on it opens the goal and lifts its card in the hand: the failure (what failed,
   its last lines, **Retry**), the spec waiting for its answers (**Start**), a fork. One act, one place: no *Retry* or
   *Start* button stands in a row. Where a row shows ↻, it is a true button that only lifts the same card, never retries
   at once.
The owner's call.

## 115. Warm at half its tint, to be tried: the same lightness, half the warmth (27 October 2026, the owner)

Why: the owner, after living with §106's warm: *it is too warm.* The warm greys tint the ground brown and the ink
yellow. Taking half the tint off each token and keeping its lightness keeps §106's measures (the ink 13:1 on the canvas,
every text pair AA, the ink AAA), so only the hue moves. So (§106.1 and §106.2 to be tried again):
1. **orkUI 0.14.0, a palette to try** (made in orkUI, copied here as §53 says; Orkboard carries no colour of its own):
   each warm token mixed halfway to the grey of its own lightness: canvas `#151412`, panel `#1e1c1a`, the table
   `#1a1816`, raised `#282622`, frame `#3a3832`, edge `#908a82`; ink `#dedbd6`, muted `#aca8a1`, faint `#96928c`.
   The ratios are measured again in orkUI before it is copied.
2. **Seen before it is taken**: drawn beside warm (0.13.0) and soft (0.12.0) on the same screens (the Tech party's
   System, a goal's spec, the left column), as §106's three were; the owner picks, and the one not picked is not copied.
3. Colour stays a signal (§53.5); the pixel face, IBM Plex and the sizes of §106.3 are unchanged.
The owner's call, after the side by side.

## 116. Parties are made when a project is first opened, in the Orkmaster's tab; a new goal is the blank card of the hand; its kind is picked in two short rows: the whole way or one party, then that party's kinds (27 October 2026, the owner and the PM)

Why: the owner: parties are made far more seldom than goals, yet *New party* stands beside *New goal* (§107.6); the
first goal's way is not understood, while people know writing at the foot of the window (Claude, Codex, Antigravity),
and here everything the person does is cards in the hand; and picking a goal's kind shows a long list of cards at once.
So (this changes §107.6 and §110.2):
1. **Opening a project is the Orkmaster's first tab**: with no project open, the Orkmaster's tab is *Open a project*, in
   the pane, never a dialog: the recent projects, a path, and the folders the host lists (a page cannot browse the
   disk). **The parties follow at once**: the Orkmaster reads the project's kind and lays out the parties it needs by
   craft (§109.1), each ticked, with its size and squad; the person leaves out what they do not want, and one *Start*
   makes them. A project open with no party opens the same tab. After, a new party is the small *+* at the tabs' end
   (§110.3); §107.6's row of *Parties* goes.
2. **A new goal is the hand's blank card**, always at the hand's left: its own shape (a dashed edge, a caret, *New
   goal*), never mistaken for a decision. Written and sent, it is dealt to the Orkmaster (§89's deal) and the goal comes
   into the left column; the answers come as cards in the hand (its party, its route, the leader's questions); no talk
   piles up, a goal is not a chat. **While the project has no goal**, the blank card lies large in the pane's middle with
   two or three examples read from the project with no model (*Add waves of enemies in server/game*); after the first,
   it goes to the hand. **One field** (§104.4): the field at the left column's head (§110.2) goes.
3. **Its kind in two short rows, both optional** (the text alone is enough, §53): the blank card pressed lays **the
   first row**: **The whole way** first (a goal that goes through every party it needs: a new feature; the Orkmaster
   deals its route, §109.2), then **a card a party** the project has (Game design, Design, Tech, …: a goal of that
   party's step alone, or starting there). A party's card pressed lays **the second row under the first**, the first
   row kept (so the way back is in sight): that party's kinds (spec 52's goal types: *An icon* for Design, *Better
   architecture* for Tech), at most five and *More kinds…*. A kind sets the route's first step and the lens open first
   (spec 52 §4.2). **Typing first is never blocked**: the caret is in the card from the start, and while the person
   writes the Orkmaster lights the row's card it guesses (§107.6), a guess never picked for them.
The owner's call.

## 117. The Orkmaster routes and gathers, never writes a spec: each leader on a goal's route writes its own part, the Orkmaster joins the parts, and what they disagree on is a fork (27 October 2026, the owner and the PM)

Why: §109.2 had the first step's leader write the one spec, *its theses by craft*: a Game designer does not write what Tech
must check in the architecture, so each step's own reviews were lost; and a goal sent as *The whole way* (§116.3) to the
Orkmaster alone would skip them too. The Orkmaster says what and who (§104.0), the leaders how and why. So (this makes
§109.2 precise):
1. **A party picked** (§116.3's first row): that party's leader writes the spec, the route starting at it; when the work
   needs other parties, it adds their steps and the Orkmaster confirms them; each added leader writes its part (2).
2. **The whole way**: **the Orkmaster only routes** (a cheaper call, §86.4: which parties, in what order); then **every
   leader on the route writes its own part** of the spec at once (parallel calls): its craft's theses (*Done when*), its
   reviews and checks, its questions; the leaders after the first step on the cheaper tier.
3. **The Orkmaster joins the parts**, on the cheaper tier, and is held to it: **it never changes a part's words** (the
   theses, the checks, the how are the leaders'); **what two parts disagree on is a fork** in the person's hand, both
   sides with each leader's why (*Game design: ten waves · Tech: the server holds six*), never settled by it; **the
   hand's three questions** (§102.1) are picked by rule, not taste: those the work cannot start without first, then by
   the route's order; the others are closed by their leaders' defaults, written in their parts and seen in the spec. No
   leader is above another: inside a party its leader, between parties the Orkmaster.
4. **After *Start*** each leader keeps its part and plans its own step (§109.2); a part changed after the start (§75)
   is checked by the Orkmaster against the other parts (§86.2).
5. **A small goal** (a bug, a balance pass) has a route of one party: one leader, one part, as today.
6. **Measured**: what the parts cost before the start against the forks and *out of the contract* cards they spare
   later.
The owner's call.

## 118. A goal goes Idea → Talk → Decided → Spec → Work → Done; its decision is written in the project's docs/decisions.md in git; its spec is a common part and a part a party; a change while it works is a new idea of the goal; a bug goes straight to Tech (27 October 2026, the owner and the PM)

Why: the owner works this way with an agent today: an idea, talked through with the leaders, a decision written in git
(this file), then the spec, then the work; and a change of a spec while it works goes through an idea again, never
edited silently. After §109 Ideation is no project's party, yet every goal needs its idea weighed. And after §117 a spec
has owners (the Orkmaster joins, each leader on the route writes its part) while its format is still one document for
one party (`realm/idea_page.py` `SECTIONS`: Gist, Why, Done when, Out, Risks, Depends on, Stages, Open questions,
Decisions). So (this makes §117 and §75 precise; spec 65's pitch flow is reused, not its party):
1. **A goal's phases**: **Idea** (the blank card's words, §116.2) → **Talk** (the route's leaders answer short, on the
   cheaper tier, as spec 65's views and skeptic do: a stance, for and against, questions; the person answers in the
   hand, in rounds, a comment pinned to a card; cards, never a chat; the talk is kept behind *More*) → **Decided** (the
   Orkmaster words the decision, *Why* and its points, as this file's entries; the person confirms or corrects it; it is
   **committed** to the project's `docs/decisions.md`, numbered, the path a setting of the project) → **Spec** (the
   parts, 3; it names its decision's number) → **Work** (the route's steps: code, assets, content) → **Done** (its
   *Result*, promised against made; its flag in main). A goal's row shows its phase as a small mark beside its route
   (§110.2's groups by state stay).
2. **The short way**: **a bug fix is routed by the Orkmaster straight to Tech** and skips Talk and Decided: its spec is
   Tech's one part, then the work. The Orkmaster offers the same short way to any small goal (a tidy, a balance pass, a
   word); the person may take the long way instead. A decision is never skipped for a goal that changes what the
   project is (a new feature, a removed one, a rule of the game).
3. **The spec's format**: **the common part**, the Orkmaster's and the person's: *Asked* (the person's words, as they
   are), *Gist* (one line, written when the parts are joined), *Route* (the parties in order, each step's leader and
   state), *Depends on* (§86.3), *Decisions* (the forks answered, each naming the part it is about). **A part a party on
   the route**, its leader's: *Why* (for its craft; Product's or Game design's is the goal's why), *Done when* (at most
   five theses), *Checks* (its checkers' `Check.done`, apart from the theses), *Will be* (the change on its lens's views,
   §104.6), *Out*, *Risks*, *Defaults* (questions closed by a default, seen), *Questions* (open; the Orkmaster deals three
   to the hand, §117.3), *Plan* (its step's tasks, after *Start*). *Stages* goes (the route and each part's plan); the
   common *Out*, *Risks* and *Open questions* go to the parts.
4. **Read through the tabs** (§110.1): a goal through the Orkmaster's tab is the common part and every part's theses in
   short, each with its leader's head; through a party's tab, that part whole, its theses at the left and its will-be on
   its views at the right (§104.5); a question in the hand opens its part's tab.
5. **A plan reads its own part whole** and of the others only *Done when* and *Will be*: the contract it must not break
   (today `PLAN_SECTIONS` reads the one spec's Gist, Done when, Out, Risks, Depends on).
6. **Every thesis says whose it is**: a leader's, the person's (a decision), or a default; §112.6's *who decided* is
   read from it.
7. **A change while it works is a new idea of the same goal**: written on the blank card with the goal picked; talked
   only with the leaders whose parts it touches; decided as a new entry that names what it changes (*changes §N.2*);
   the parts it touches rewritten by their leaders; only the tasks whose parts changed re-planned (§75.3). Nothing in a
   spec changes without its why in `docs/decisions.md`; a bug's short way excepted (2).
8. **A spec from before** is read as one part of its party, as an older goal's sections are (`OLD_TRACK_SECTIONS`).
The owner's call.

## 119. The Orkmaster's views stay its tab's; *The whole project* opens that tab, and the tab reads as one with the Orkmaster's line (27 October 2026, the owner and the PM)

Why: the owner asked whether the Orkmaster's views (*Board*, *Assets*) could stand in the left column. There they would
mix §110.1's two axes (a row of the left column is what is looked at; *Assets* through Tech means nothing), leave the
Orkmaster's tab empty and an exception to every other tab's header and views, and push the goals, scrolled all day,
down. So (§110.3 made precise):
1. **The Orkmaster's views stay in its tab** (*Board*, *Assets*, §111), its header as every party's.
2. **A press on *The whole project* opens the Orkmaster's tab on *Board*** (as picking a goal opens its step's tab,
   §110.3); after, the tab stays as the person leaves it.
3. **The Orkmaster's tab reads as one with its line** in the left column: the same head, the tabs' first, joined to the
   column's edge.
4. **Measured**: the tabs' switches; if the person lives on *Board* and seldom opens a party's tab, *Board* as the
   window's default is asked again.
The owner's call.

## 120. No right column: a card of the map is lifted and turned where it lies; what is read long opens as the pane's one temporary tab; the window is three parts again (27 October 2026, the owner and the PM)

Why: after §110–§119 what stood in the right column (§105.2) has a better place each: the spec reads under the tabs
(§118.4), Play is a temporary tab (§111), a result's acts are the hand's cards (§104.9), Agents went from the top bar and
Files to the Orkmaster's Assets (§107.1), a seat's settings are its popover (§110.7). What is left is either a quick look
at a card of the map or a long read, and the column made a fourth part of a window of three (§104.0) and moved the
pane's width each time it opened (§105.2), the reveal with it. So (this changes §105.2 and makes §104.8 precise):
1. **A card of the map is lifted where it lies**: a part of System, an asset, a link between containers, a task on the
   Board: pressed, it rises a little over its place and **turns over**: its back the details (a part's files, *Uses*,
   *Used by*, its changes and their goals; a task's *What it made* and its last lines; a link's routes and events). Again,
   Esc, or a press away lowers it. **It stays small**: at most twice a card, beside its place, never over the cards it
   is about; whatever needs more room opens as the temporary tab (2). §105's *not over the pane* holds by that.
2. **A long read is the pane's one temporary tab** (§104.8: at the end of the tabs, ×, *Back*, replaced by the next
   unless pinned): a diff, a task's whole log, a failure's lines, an asset or a canvas's file large (the pane's whole
   width, wider than the column was), the agents' full text behind *More*, a role of Agents, Play. On it, what it is
   about stays lit on the map for *Back*.
3. **The pane's width never moves**: no column opens or closes beside it.
4. **Side by side** (a diff beside the map) is not made now; asked again only if the measures show people going back and
   forth between a temporary tab and the map. Never as a standing column.
5. **Moved one kind at a time**: the spec first (§118.4), then diffs and logs to the temporary tab, then the lifted
   cards; the column's code is removed when nothing opens in it. On the phone (spec 67) a lifted card and a temporary tab
   are screens of their own, as today.
The owner's call.

## 121. One word each for the new things; the hand is a stack a goal; a goal's cost is said before it is talked or started, and a goal may wait for the limits to reset; Orkline follows later (27 October 2026, the owner and the PM)

Why: read together, §104–§120 used one word for two things (*part*: a part of the project on System, §89, and a party's
part of a spec, §117–§118) and four words for one family (*stage*: a leader's seats, §104.1, the project's stages,
§91.7, a step of a goal's route, §109.2, a goal's phase, §118.1); the hand gained Talk's questions, three a goal in
rounds, beside the forks, failures and *dev → main*, while no count may be shown (§67); §117–§118 made a goal cost more
calls before its work (a route, parallel sections, a join, Talk's rounds) and nothing says so before; and Orkline reads
the same state. So:
1. **The words** (`TERMS`, one each, with their first spec; this renames §117–§118's *part* of a spec): a **section**
   (a party's part of a goal's spec; a *part* is only a part of the project), a **seat** (*Leads*, *Does*, *Checks*: the
   leader's stages of §104.1), the project's **stage** (*Idea*, *Being made*, *Live*: §122.5), a **step** (a party's
   turn on a goal's **route**), a goal's **phase** (*Idea*, *Talk*, *Decided*, *Spec*, *Work*, *Done*), the **blank
   card**, a **lifted card**, the **temporary tab**.
2. **The hand is a stack a goal**: every card of one goal in one stack, the most urgent face up with its kind's sign;
   its edges hint there is more (five at most, never a number, §67). The stacks lie by their top card's urgency (money and
   failures, then a question the work waits for, then the rest). **A stack pressed fans out in place** and picks its
   goal in the left column, so the pane shows its map; one fanned at a time, the others close. The picked goal's stack
   is fanned. Two cards are no goal's and keep their places: the blank card at the left, *n goals ready for main* at the
   right. **Talk has two rounds at most**; after, the questions left take their leaders' defaults (§117.3).
3. **The cost is said before**: on a goal's route, before *Talk* and before *Start*, one line: *This way: about 6 calls,
   about 4% of Claude's week* (from the tiers, the route and §107.1's reads of the limits). **When the week's limits run
   low** the Orkmaster offers the short way (§118.2) or **Later, by itself**: the goal waits and starts itself when the
   limits reset, said plainly on its row (*Starts by itself after the reset, Mon 09:00*), stopped by a press.
4. **Orkline follows later**: Orkboard writes the new parties, routes and sections; Orkline, frozen now, is changed to read
   them when it is taken up again (in about two months); Orkboard keeps no reading of both until then.
The owner's call.

## 122. The parties that did not fit: General, Team and Ideation go; Release is called only to release; a recurring goal is decided once; the project's stage chooses the crafts (27 October 2026, the owner)

Why: after §109 a party is a craft, a lens and a step of a route; General (§80.4: never removed, where a goal with no
party goes), Team (§108.3: Operations, no goals), Ideation (its Investor's *Bets*, now each goal's *Talk*, §118.1) and
Release (its *Versions* gone, §112.9; it gathers many goals) were none of these. Only the owner uses Orkboard today, so
nothing need be carried over. So:
1. **General goes**: a goal with no route yet stays with the Orkmaster in its *Idea* phase.
2. **Team goes for now**: Operations stay the person's own list, reached as before §108 (§108.3–§108.4 undone); a party
   for them is asked again later.
3. **Ideation goes**, its parties removed with no move offered; a goal's ideas are weighed in its *Talk* (§118.1), spec
   65's views reused there.
4. **Release is called only for a release**: never a step of another goal's route; its goal is *A release* (§83.5: the
   flags since the last release, ticked; its version, notes and stores' list), its lens what goes in and what is out.
5. **The project's stage chooses the crafts**: the Orkmaster's first tab (§116.1) asks first *Where is the project?*
   (**Idea**, **Being made**, **Live**) and offers the crafts that stage needs: Idea, the concept's crafts lean (Game
   design and Art; Product and Design); Being made, Tech too, standard; Live, LiveOps or Run too, and Release offered.
   The stage is the project's, kept, and changed by the person (or offered by the Orkmaster: *Is the project live now?*,
   then LiveOps or Run). **New party** keeps its left half *by the project's stage*, under each stage parties by craft,
   never a party that is a stage (§107.5, §91.7 made precise).
6. **A recurring goal of LiveOps or Run** (§108.2) is talked and decided once, when it is made; each round after takes
   the short way (§118.2).
The owner's call.

## 123. Three measures of §104–§122, read from the event log; the first slice is the parties by craft, the tabs, the sections and Talk on one real game; the rest after it is measured (27 October 2026, the owner and the PM)

Why: almost every decision from §104 ends *Measured*, yet none says which measures decide nor where they are read; and
fourteen decisions (§109–§122) lean on each other, so built at once they could not be told apart when something is
better or worse. So:
1. **Three measures decide**, read from the event log (`realm/event_log.py`) with no model, and shown weekly in one short
   report beside the analytics (`realm/analytics.py`), today's against the week before the slice:
   - **the day in a minute** (§104.14): the time from opening the project to the first press on a goal or a hand card,
     and how often the person opens a temporary tab to understand what happened;
   - **what a member decided alone, seen** (§112.6): of the changes marked *a member alone*, the share the person
     looked at (a lifted card, its goal opened) before it went to main;
   - **a goal's cost** (§121.3): the calls and the share of the week's limits from *Idea* to *Done*, by route length,
     against a goal of the same kind before the slice; with the forks and *out of the contract* cards after *Start*.
2. **The first slice**, built and measured on one real project (the owner's Node party game): the parties by craft and
   the route (§109, §117, §122), the leaders' tabs with the header, the squad and the views (§110, §119), the blank card
   and the first opening (§116), the phases with *Talk* and *Decided* and the spec's sections read under the tabs
   (§118, §120.5's first move), the words, the hand's stacks and the cost said before (§121).
3. **After the slice is measured**: Play of a goal and several processes (§111, §113), System read anew and the lenses
   of judgement (§112), the row's signs (§114), the right column's other moves (§120). The palette's side by side (§115)
   is made in orkUI at any time, apart from the slices.
4. **Until the slice**, the owner's game plays its client and server by a root script (`concurrently`) or `preview` in
   `.orkcraft/checks.toml` (§113.5).
The owner's call.

## 124. A new idea is written as a message: one field, Enter sends; no priority, no kind, no lens; *@party* or the open party's tab addresses it, and only then the party's views are pointed at (27 October 2026, the owner and the PM)

Why: the owner: a general idea, not a party's, must be as seamless as writing to a chatbot. §116.3's two rows of kinds,
the priority, and the lens switch of New goal (§53, §109.6: Text, Code, Screen, Pain) each ask the person to decide
what the Orkmaster and the leaders decide anyway after it is sent. So (this changes §116.3 and §109.6; spec 52's goal
types are chosen by the Orkmaster or the leader, no longer by the person):
1. **The blank card is one field** (§116.2): written, **Enter sends**, Shift+Enter a new line; a picture pasted or
   dropped into it goes with it (`realm/idea_photos.py`), as in a chat. No other field.
2. **No priority**: the Orkmaster orders the goals; the person who disagrees moves a goal within *Next* in the left
   column, after, never as a field before.
3. **No kind**: §116.3's rows go. The Orkmaster (or, for a party's idea, its leader) picks the goal's kind of spec 52,
   which still sets the route's first step and the view opened first.
4. **Addressed to a party only on purpose**: **`@` in the text** lists the parties (*@Tech fix the crash in the lobby*),
   as a mention; and **with a party's tab open** the blank card carries **→ Tech ×**, one press taking it off. On the
   Orkmaster's tab and on *The whole project* the idea is general. The mark is always seen, so no idea goes to one party
   by the tab it happened to be written on.
5. **No lens switch**: a general idea is its text alone (the leaders point at the project in their sections, §117).
   **An idea addressed to a party** puts the pane's view, already that party's, in picking: a press on a part of
   System, a screen or a pain pins it to the blank card as a mark. §53's Text, Code, Screen, Pain switch goes.
The owner's call.

## 125. The blank card takes a voice: a microphone writes the words into the field, never sends them; where the voice goes is said plainly (27 October 2026, the owner)

Why: the owner: an idea is often faster said than typed, as people talk to a chatbot today. So (§124.1 widened):
1. **A microphone on the blank card**, beside the field: pressed (or held, on the phone), it listens and **writes what
   it hears into the field**, as it comes; a press again stops it. **It never sends**: the words stay to be read and
   corrected, Enter sends them as typed ones (§124.1). Any language the person speaks; the words are kept as said.
2. **Where the voice goes is said plainly before the first use**, and in the microphone's tip: recognised on this
   computer when the host has a local recogniser; else by the browser's own (*Your voice goes to Google to be written
   down*, Chrome's), the person's yes asked once; on the phone, the phone's own dictation. No recording is kept, nothing
   is sent to a model as sound.
3. **No microphone without a way to recognise**: a browser and host with none show no button (never a button that
   fails); the keyboard's dictation (the computer's, the phone's) still writes into the field as into any.
4. Listening is a signal while it lasts (the field's edge in the signal's colour, a slow pulse; still under reduced
   motion), so a microphone left on is never missed.
The owner's call.

## 126. Less to read twice: no top bar, a goal's row one sign, no Overview, a goal's pane follows its phase, nothing over System's table (27 October 2026, the owner and the PM)

Why: read together, §104–§125 show some things twice: the top bar holds four things on a band of its own; a goal's row
carries its element, route, phase, state and its group; a party's *Overview* repeats the left column, the hand and the
header's stance; a goal's own tabs (§104.8: *Spec*, *Will be*, *Board*, *Result*) repeat its phase (§118.1); and
System's table has a bar of controls over it. So (this changes §107.1, §104.8, §110.2, §110.4, §118.1 and spec 89 §6):
1. **No top bar**: the product's name is no longer shown in the window (the page's title, the browser's and VS Code's
   tab, keeps *Orkboard*); *Settings* goes to the Orkmaster's line in the left column, beside the projects' switcher;
   the AI tools' limits and *Stop all* stand at the right end of the leaders' tabs (§110.3), which had nothing there.
2. **A goal's row is its element, its name and one sign** (the hourglass, the failure's alert, *waits for you*); its
   route and phase are shown only on the picked goal (the pane's title, the tabs' dots, §110.3). **No *Waits for you*
   group**: the hand's stacks are it (§121.2); the left column is one list in the Orkmaster's order, *Done* folded at
   its foot (§110.2's groups go).
3. **No *Overview* view**: a party's header gains one line, *Now* (*2 goals at its step, 1 coming to it*); what changed
   since the last look is the element on a view's segment (§110.5); a party opens on its first view, and a party with no
   view is its header alone.
4. **A goal has no tabs of its own**: through the Orkmaster's tab the pane shows what its phase needs (*Talk*: the
   leaders' stances; *Spec*: the common section and the theses; *Work*: the will-be, its ghosts filling; *Done*: the
   result); a phase gone by is opened by a press on its mark in the pane's title.
5. **Nothing over System's table**: the reveal plays as it does; a press on a mark says which goal made it and lights
   that goal's other marks (the goals' buttons over the table go); *Rearrange* and *Since <version>* (§112.5) move to
   the tab's menu (**…**). The table begins under the header.
The owner's call.

## 127. No dialogs; Operations off the left column; one closed set of signs and motions; Settings only for what lives nowhere near the work (27 October 2026, the owner and the PM)

Why: after §109–§126 almost everything has a standing place (the pane, the temporary tab, a head's popover, a card in
the hand); the dialogs left (*New party*, *Edit the party*, the question before removing a party) are a fourth way of
asking. §122.2 put Operations back as the row they had before §108, against §126.2's one list of goals. The signs and the
field's motions grew one decision at a time. And Settings still holds what moved beside the work. So:
1. **No dialogs**: *New party* (the tabs' *+*) opens §116.1's layout of crafts by the project's stage as the temporary
   tab; *Edit the party* goes (the seats, tools and tiers are the header's popovers, §110.7; the leader changed and the
   party removed from the tab's menu, **…**); a question before an act (removing a party, a goal) is a card in the hand,
   never a modal window. A question to the person is always a card.
2. **Operations off the left column** (§122.2 made precise): reached from the Orkmaster's line's menu, beside *Settings*,
   as the temporary tab; the left column is the goals alone (§126.2).
3. **One closed set of signs and motions, kept in orkUI**: at most six signs and six motions, each one meaning; a new
   thing takes one of them or replaces one, never adds a seventh. Made in orkUI first (§53), the set read against
   today's (the goal's element, the signal's colour, the alert, the hourglass, *waits for you*, the moon; dealt, sealed,
   crumbled, ghost, turned, lifted, the microphone's pulse). **The moon of a goal's progress goes** (§89): the will-be's
   ghosts filling are its progress (§104.6).
4. **Settings is only what lives nowhere near the work**: the account, the AI tools connected, the paired phones, the
   project's paths (`docs/decisions.md`, §118.1, `.orkcraft/checks.toml`'s Play, §113); a seat's tool and tier are its
   popover's (§110.7), the project's stage its first tab's (§122.5), the voice its microphone's (§125.2). A setting of a
   party or a goal lives there, never in Settings.
The owner's call.

## 128. After the first slice, one face for the desktop and the phone: one page fitted to the width, the phone's app its frame (27 October 2026, the owner and the PM)

Why: the desktop (`static/board.js`, `js/shell`, `js/board`, `js/arena`) and the phone (`pwa/board-app.js`,
`pwa/shell-*.js`) are two faces of the same window; every decision says its phone's half (§110.9, §120.5, …) and is built
twice. After §109–§127 the window is one structure (the goals, the leaders' tabs, the pane, the hand); on a phone the
same parts a screen each. So:
1. **One page fitted to the width**: on a narrow screen the goals are the first screen, the pane and its tabs the next
   (the tabs a row of heads, §110.9), the hand at the foot, a lifted card and a temporary tab screens of their own
   (§120.5); spec 67's rules (no sideways scroll, the phone's sizes) are the narrow width's. The phone's PWA is its frame
   (its cache, its pairing), as the VS Code extension is the desktop's (`vscode/`).
2. **When**: after the first slice is measured (§123); the slice is built on the desktop alone, its specs written for
   one page fitted to the width, so nothing of it is built twice. Until then the phone stays as it is.
3. **Then the phone's own face is removed** (`pwa/shell-*.js`, `pwa/board-app.js`'s screens), its tests moved to the
   page's at the narrow width; `tests/test_architecture.py` keeps one face.
The owner's call.

## 129. No measures: the owner's yes or no after each slice is built (27 October 2026, the owner)

Why: the owner is the one person using Orkboard; a slice is judged by them using it, not by counted events. So (this
changes §123.1 and every *Measured* of §104–§128: §104.14, §109.8, §117.6, §119.4, §120.4, §128.2):
1. **No measures are built**: §123.1's three measures and their weekly report are not made; no event is added only to
   count.
2. **A slice is done when the owner says yes**: built, the owner uses it on their own project and says **yes** (it stays,
   the next slice starts), or **no** with what is wrong (it is fixed, or taken back). §123.2's first slice and §123.3's
   order stay; *after it is measured* reads *after the owner's yes*.
3. Where a decision said *asked again if the measures show* (§119.4, §120.4), it is asked again when the owner says so.
The owner's call.

## 130. A goal done stays in the list until its result is seen, then leaves it; the done goals are a history, the temporary tab (27 October 2026, the owner)

Why: today a goal done goes to *Flags · n* folded at the foot of its party (`js/arena/goals.js` `FlagsFold`, spec 73 §3),
with *k wait for main* over it: a fold seldom opened that only grows, two counts the list may not show (§67, §126.2), and
*wait for main* is the hand's *n goals ready for main* already (§121.2). So (this changes §126.2's *Done folded at its
foot* and spec 73 §3):
1. **A goal done stays in its place until its result is seen**: faint, with the sign *done*; once the person has opened
   its *Result* or seen its changes on a map's reveal, it leaves the list. Nothing done leaves unseen.
2. **Nothing of main in the list**: *wait for main* is the hand's card alone.
3. **No *Flags* fold**: the left column is the goals at work, waiting or not yet seen.
4. **The history is the temporary tab**, from the Orkmaster's line's menu beside *Settings* and *Operations*: the goals
   done by release (*Out in 1.4*), else by week, with a search; a goal pressed opens its *Result*, its route and what it
   cost.
The owner's call.

## 131. What the new window does already goes: *Process now*, the night, the gate's line, collisions as stops, a goal type's sign, the row's peek, the analytics page, the canvases (27 October 2026, the owner)

Why: each of these is done by a thing of §109–§130 or no longer needed. So:
1. ***Process now* and *Judge now* go** (spec 73 §1, spec 65 §8): the Orkmaster routes a new idea by itself (§117,
   §118), and *Later, by itself* (§121.3) starts it after the limits reset.
2. **The night goes** (spec 83, *night tonight*): one way of starting later, *Later, by itself*: at night or after the
   limits reset, said on the goal's row.
3. **The gate's quiet line in the project's line goes** (§105.2): *n goals ready for main* is the hand's card alone.
4. **Collisions are no stops of their own** (§86.1–§86.2): two goals changing the same thing is a fork in the hand and
   one mark on both goals' cards of the map; found by code and judged on the cheaper tier as before.
5. **A goal type's sign goes from the row** (spec 52 §3.2): the row is its element, name and one sign (§126.2); the type
   is the Orkmaster's (§124.3).
6. **The row's peek on hover goes** (spec 73: the board showing only a hovered goal's cards): a goal is picked with one
   press (§119).
7. **The analytics page goes** (`realm/analytics.py`'s page, its face): no measures (§129); what used the limits is the
   limit's chip pressed (§107.1), a goal's cost its history (§130.4).
8. **The canvases go** (spec 78; §105.2 made them a kind of Assets): their kind leaves Assets, their files stay the
   project's.
The owner's call.

## 132. The window grows from what there is: no onboarding of its own; a part comes when it has something to hold, first the pane, then the goals, then the hand (27 October 2026, the owner and the PM)

Why: the owner: a new person meets the three parts of the window (§104.0) all at once, two of them empty; opened one a
step (the Orkmaster and its tab, then the first goal, then the cards in the hand), each is learnt by using it. A tour
with *Next* would be a fourth way of asking (§127.1) and a state to keep, skip and reset; the window drawn from what
the project has needs none, and holds for a second project, the phone (§128) and a Board brought from Orkline, which
opens whole. So (this makes §116.1–§116.2 precise; part of the first slice, §123.2):
1. **A part of the window is drawn when it has something to hold**, never by a step of an onboarding: no flag of a tour
   seen, no *Skip*, no coach marks, no dialog. The first start keeps today's first screen, the AI tools found and their
   *Check* (`gui/onboarding.py`), before any project.
2. **The pane first**: with no project or no party, the window is the Orkmaster's tab (§116.1: *Open a project*, *Where
   is the project?*, the parties ticked, one *Start*); the left column is the Orkmaster's line alone (the projects'
   switcher, *Settings*, §126.1), with no *The whole project* and no list. The Orkmaster is met by what it does: its
   header's line (*Deals goals to parties*, §110.4) and the parties it laid out, never a story. On *Start* the leaders'
   heads are dealt onto the table's edge as their tabs (§89's *dealt*), one by one.
3. **Then the goals**: with parties and no goal, the blank card lies large in the pane's middle with its examples read
   from the project (§116.2). Sent, the first goal is dealt into the left column, which gains *The whole project* and the
   list then (§126.2).
4. **Then the hand**: the blank card moves from the pane's middle to the hand's left (§116.2), and the leaders' first
   cards (their questions in *Talk*, §118) are dealt beside it: where the person acts and decides is shown by the first
   thing to decide, never by an example card. An empty hand is the blank card alone, as at any time.
5. **One line, once**: on the first card with answers the person ever gets, a quiet line under them, *Pick an answer:
   the leader writes it into the spec*; gone once any answer is picked, on any project (kept in the machine's settings,
   `~/.config/orkcraft/`). No other hint.
6. **Parties before the first goal stay one press** (§116.1): every party the stage needs ticked, sizes and tiers by
   default, nothing that must be chosen; a seat's tool and tier are changed later in its popover (§110.7). Offering the
   parties from the first goal's route instead is asked again if the owner finds people stopping there (§129.3).
The owner's call.

## 133. A goal's first card is its route: the parties, the cost and one press before any call; the row's sign is the head of whoever has the goal now; a goal waiting for the reset may start now (27 October 2026, the owner and the PM)

Why: the owner wrote the flow of a general goal as they expect it: the idea written on the blank card, routed by the
Orkmaster on the cheaper tier, *a card in the hand: your idea was taken, these parties write its spec, it starts now or
later*, *I agree* or the goal opened to change its parties, and on the goal's row the heads of the leaders it is with.
Read against §116–§131 it holds, but for three things: the answer cards of §116.2 and the cost of §121.3 are two cards
where one would do; a row's one sign (§126.2) says that a goal works but never whose it is; and a goal waiting for the
limits to reset can only be stopped (§121.3), never started now. Priority stays out (§124.2), and *Process now* stays
gone (§131.1). So (this makes §116.2, §121.3 and §126.2 precise):
1. **A goal's first card is its route**, dealt as soon as the Orkmaster has routed it (code or the cheaper tier, §117.2,
   never the stronger): the route as the leaders' heads in order, the cost (*This way: about 6 calls, about 4% of
   Claude's week*, §121.3), its place in the Orkmaster's order (*3rd in Next*; never a priority, §124.2), and **Talk**
   and **Later, by itself**. A head pressed takes its party off the route, **+** adds one of the project's; the cost is
   said again at once, with no call. **No call is made for a goal before that press**, the short way (§118.2) too: its
   card says *Tech alone: a bug skips Talk* and **Start**, with the long way offered beside it.
2. **The hand after it follows the phases** (§118.1), nothing else: the route; Talk's questions (two rounds at most,
   §121.2); the decision to confirm (*Decided*); the spec's forks (§117.3) and **Start**; while it works, only forks and
   *out of the contract* (§104.9); *n goals ready for main* (§121.2).
3. **The row's sign while the goal works is the small head of the leader whose step it is in** (§126.2's hourglass while
   it waits for a step), turned as a card at work turns (§104.2); two steps at once show the earlier one's; a signal
   covers it (the failure's alert, *waits for you*). A head is an accent, not a seventh sign (§127.3). The route whole and
   the phase stay on the picked goal: the pane's title (*Waves · Talk*), the tabs' dots.
4. **A goal waiting for the reset may start now**: its row says *Starts by itself after the reset, Mon 09:00*; picked,
   its route card carries **Start now** beside **Don't start**, with what it spends of the limits left said plainly (*about
   4% of Claude's week; 6% is left*); it never spends the person's reserve (spec 49 §2.3) without saying so on the button
   (*Start now, from your reserve*).
The owner's call.

## 134. Less said twice: what waits is the hand's alone; a party is one map; its header is its name and its squad; *The whole project* is no goal picked; a goal with nothing to settle starts on its decision (27 October 2026, the owner and the PM)

Why: read as one window after §133: *waits for you* is said three times (the row's sign, §126.2; the tab's signal mark,
§110.3; the goal's stack in the hand, §121.2); after §112.9 a party has one or two views, and the second is the first
seen another way (*Flow* is the links between *Screens*; *Journey* is the flow seen by a segment; Product's pains are
pinned to the screens and the flow's steps, §112.7); a party's *Now* line (§126.3) lists the goals whose rows now carry
its leader's head (§133.3), and its stance in one sentence says nothing that a leader's stance on a goal, in *Talk*,
does not; *The whole project* only opens the Orkmaster's *Board* (§119.2); and a small goal asks three presses (its
route, its decision, *Start*) where nothing is left to settle after the second. So (this changes §110.3, §110.4–§110.5,
§112.7, §119.2, §126.2–§126.3, §132.3 and §133.2–§133.3):
1. **What waits for the person is said by the hand alone** (§104.9: the hand is the count): a goal's row carries no
   *waits for you* (its signs are the leader's head while it works, the hourglass while it waits for a step, the
   failure's alert), and a tab no signal mark. A stack pressed picks its goal and opens its tab, as before.
2. **A party is one map**: its tab shows one view, and no segmented control is drawn in a party's header. **Design's
   map is the screens laid out along their flow** (§112.7: read from the pictures and the routes); **Product looks at the
   same map** with its pains pinned to the screens and the flow's steps, and a segment picked over it as a filter (what
   was *Journey*); a project with Product and no Design draws the same map under Product's tab. Tech's is *System*, Game
   design's *Loop*; a party with nothing to read is its header alone (§112.9). The Orkmaster's tab keeps *Board* and
   *Assets*, its two views the one segmented control left.
3. **A party's header is its name and its squad**: the *Now* line goes (the rows' heads say it, §133.3), the leader's
   stance in a sentence goes (a leader's stance is on a goal, in *Talk*, §118.1), and what the party does is said on the
   leader's head's hover and in its popover (§110.7).
4. ***The whole project* is no goal picked**: its row goes from the left column; pressing the picked goal again, or Esc,
   lets it go, and the pane shows the whole project through the tab that is open (the pane's title: *The whole project ·
   through Tech*). The left column is the Orkmaster's line and the goals (§132.3: the list alone is dealt in with the
   first goal). On a narrow width the goals' screen carries the tabs' heads over the list: a head pressed opens the
   whole project through that party, a goal its step's tab (spec 94 §3.2).
5. **A goal with nothing to settle starts on its decision**: the card that confirms its decision (*Decided*, §118.1)
   carries **Confirm and start** first and **Confirm** beside it. **Confirm and start** commits the decision, has the
   sections written (§117.2) and, when they are joined with no fork and no open question (§117.3), starts the work by
   itself, with no *Start* card; with a fork or a question left, those come to the hand and *Start* after them, as
   before (§133.2). **Confirm** writes the sections and always waits for *Start*. The cost said on the route's card
   (§133.1) is the whole way's, so starting by itself spends nothing that was not said.
The owner's call.

## 135. The Orkmaster keeps *Board* alone; Assets is what is looked at, beside Play, under every tab; Art's map is the Assets of its kinds (27 October 2026, the owner and the PM)

Why: the owner: after §134.2 every tab is one map but the Orkmaster's, which keeps *Board* and *Assets*; could Assets go
to a party of its own, Art. Assets is not a craft's way of looking: it is the project's own material, the files with it
(§107.1), as Play is the project run (§111); under the Orkmaster's tab it was the one segmented control left. And Art,
whose craft is exactly those assets, has had no map (§112.9). So (this changes §104.11, §105.3, §110.4, §119.1 and
§134.2):
1. **The Orkmaster's tab is *Board* alone**: its header its name, its AI tool and tier (§110.4), no views; no segmented
   control is left in the window.
2. **Assets is on the left column's axis, as Play** (§111.1): **Assets** beside **▶ Play** in the pane's title, under
   every tab, opens what is looked at: the whole project (its assets and its files, §105.3's table by kinds), or the
   picked goal (what it made and changed, its *Result*'s assets, §104.11). It opens as the pane's one temporary tab, the
   pane's whole width (§120.2). On the phone it is read as on the computer (Play stays the computer's, §111.6).
3. **Through a party's tab Assets opens on its kinds first**: Art's (art and icons, sound, music, clips), Design's
   (screens, icons, fonts), Tech's (the files); the other kinds lie under them, nothing hidden.
4. **Art's map is the Assets table of its kinds**, in its tab as every party's map (§134.2: as Product looks at Design's
   map): a card lifted shows it large and plays it, a changed one turns to its version before, the variants not picked
   lie under the one picked (§104.11); an idea addressed to Art picks a card there (§124.5).
The owner's call.

## 136. What §132–§135 left uneven: one meaning for the hourglass, a cost said again when the route grows, no Assets button, recurring rounds and the wait as signs, how the project runs on System, Stop all on the phone, the picking mode, a goal at work through the Orkmaster is its Board, Agents goes; the first slice counted again (27 October 2026, the owner and the PM)

Why: §104–§135 read through once more: §133.3 gave the hourglass a second meaning (§127.3: one each); a leader may add
a step after the route's press (§117.1) while *Confirm and start* (§134.5) leans on the cost said before it; under Art's
tab the Assets button (§135.3) opened Art's own map, and a lens shows the assets of its craft better than a table apart;
recurring rounds (§122.6) and the wait for the reset (§121.3) did not fit §133.1 and §126.2; how the project runs had no
place once *Overview* went (§111.5, §126.3); the phone had no room for the limits and *Stop all* (§126.1, spec 94); and
Agents repeats the Board, the limits' chips and the seats' popovers. So (this changes §104.10, §107.1, §110.7, §111.5,
§114.1, §120.2, §123.2–§123.3, §126.4, §133.1–§133.4, §134.1, §134.5 and §135.2–§135.4):
1. **The hourglass means one thing: a member works on it now**, where no head stands for it (a card on a map, the
   Board). A goal's row: the head of the leader whose step it is in while it works (§133.3), **no sign** while it waits
   for a step.
2. **A cost changed is said again**: a step added after the route's press (§117.1) takes away *Confirm and start*'s own
   start (§134.5); a *Start* card comes with the new cost, the old one beside it.
3. **No Assets button: a lens shows the assets of its craft.** **Art's map** is its assets (art and icons, sound, music,
   clips, §135.4); **Design's map** has the screens' pictures as its cards and, at its foot, a band of what they use
   (the logo, icons, fonts); **Tech's System** carries the files: a part's files on its lifted card's back (§120.1), a
   file opened as the temporary tab. A kind whose craft has no party in the project lies on Design's band, else among
   System's files. A goal's assets are its *Result* (§104.11) and the changed cards of the maps. The pane's title keeps
   **▶ Play** alone.
4. **A recurring goal's rounds** (§122.6) take no route card: their cost is said once, when the goal is made (*each
   round: about 2 calls, about 1% of Claude's week*), and each round starts by itself.
5. **Waiting for the reset is a sign, not a line**: the moon (§127.3's, freed when the night went, §131.2) means *starts
   by itself later*; the hour on its hover and on the route card (*Starts by itself after the reset, Mon 09:00*, **Start
   now**, §133.4).
6. **A goal's row signs are**: the leader's head (it works), the alert (it failed), the moon (it waits for the reset),
   *done* (§130.1), or none. What waits for the person is the hand's alone (§134.1).
7. **How the project runs is on System's containers**: a container's lifted card shows its command, its port and its
   last lines; a Play that did not start opens its lines as the temporary tab and lifts the container that failed (this
   moves §111.5 off the gone *Overview*).
8. **On a narrow width** *Stop all* stands always on the Orkmaster's line; the limits' chips are in its menu, a chip
   pressed still showing what used it (§107.1; spec 94 §3.4).
9. **The picking mode and the narrow width are decided as spec 94 says**: picking a part for an idea is a mode that is
   always seen (spec 94 §1.5; §124.5 made precise), and the window is narrow under 760 CSS px of its width (spec 94
   §3.1).
10. **A goal through the Orkmaster's tab at *Work* is its Board**: the Board's cards filtered to its tasks, their
   members' heads on them (§126.4's *the will-be* moves): who does what. Its will-be is on its step's tab, its ghosts
   filling the progress (§104.6), and picking a goal at work opens that tab first (§110.3), so the contract is seen
   before the tasks.
11. **Agents goes** (spec 36's monitor): the tasks at work are the Board's; what a role spends, the limits' chips
   (§107.1); a role's text is read from its head's popover as the temporary tab (and written there for a role of the
   person's own); a seat is added by its ghost (§110.6). §110.7's *its role on Agents* and §120.2's *a role of Agents*
   read so.
12. **The first slice, counted again** (§123.2; at the owner's yes, §129.2), on the owner's Node party game:
    - **before it**, what goes goes: §131's list and Agents (11), so nothing new is built around them;
    - **the slice**: parties by craft, the project's stage at the first opening, the route and the sections (§109,
      §116.1, §117, §122); the window of three parts that grows from what there is (§120, §126.1, §132), the left column
      the Orkmaster's line and the goals (§126.2, §127.2, §134.4); the Orkmaster's tab *Board* alone and the leaders'
      tabs, each header its name and squad, its seats' popovers, *New party* as the temporary tab, no dialog (§110,
      §127.1, §134.3, §135.1); one map, Tech's *System*, as it is read today; the blank card as a message, addressed by
      *@* or the open tab (§124.1–§124.4); the phases with the route card and its cost, *Talk*, *Decided* with *Confirm
      and start*, the forks and *Start* (§118, §121.3, §133.1–§133.2, §134.5, 2); the hand by goal, the one place of
      what waits (§121.2, §134.1); the row's signs and a goal done until it is seen (§130.1–§130.3, 1, 6); a goal at work
      through the Orkmaster (10); the words (§121.1) and the closed set of signs in orkUI (§127.3); spec 94 §1's rules;
    - **after it, in this order**: the lenses (Design's and Product's map, Game design's *Loop*, Art's map, the assets in
      them, picking on them: §112.7–§112.8, §134.2, §135.4, 3, 9); Play of a goal and of several processes, System read
      anew and how it runs (§111, §112.1–§112.6, §113, 7); one page for the phone (§128, spec 94 §2–§5, 8); the wait
      for the reset, *Start now* and recurring goals (§121.3, §133.4, §122.6, 4, 5); the voice (§125), the history
      (§130.4), Settings made small (§127.4), the reveal *Since <version>* (§112.5).
The owner's call.

## 137. Release is in every project from its start and is the one way into main: its map is dev against main; *To main* by code, *Release a version* with its cost (27 October 2026, the owner and the PM)

Why: the owner: every other party lands its work in dev by itself (§101); let Release be the one party through which
anything goes into main. Today dev → main is a card of no goal's in the hand (*n goals ready for main*, §104.9, §121.2)
and Release is offered only to a live project and called only for a release (§122.4–§122.5), so a project being made
has no keeper of main, and §134.2's *a party is one map* left Release's map unsaid. Merging into main and releasing a
version are two acts (a store's version, its notes and its submission are not wanted on every merge), and a fix for
production must reach main in one press. So (this changes §104.9, §116.1, §121.2, §122.4–§122.5 and §136.12):
1. **Release comes with every project, at every stage**: laid out ticked among the first parties (§116.1, §122.5),
   lean (its leader alone, the cheaper tier); it cannot be removed (§97), its seat's tool and tier set in its popover
   (§110.7). It is still never a step of another goal's route (§122.4).
2. **Release alone writes main.** No other party, task or card merges into main; the gate's checks (§103: the project's
   tests) run on its act as they run today.
3. **Its map is dev against main**: a card a goal that is in dev and not in main, its element and name, ticked; a card
   lifted shows its *Result*, promised against made (§104.11); what landed in main since the last version lies faint
   under a line naming it (*Since 1.3*).
4. **Two acts, said plainly**: **To main** merges the ticked goals into main by code, with no model and no call (one goal
   ticked is a fix for production: one press); **Release a version** is §122.4's goal *A release* (its version, notes and
   stores' list), with its cost said before as every goal's (§121.3, §133.1), and *@Release* on the blank card starts it
   too.
5. **The hand keeps one card for it**: *n goals ready for main* is Release's card, its leader's head on it (no longer a
   card of no goal's, §121.2), at the hand's right; pressed, it opens Release's tab on its map.
6. **In the first slice** (§136.12): Release with every project and *To main* on its map, in place of today's card;
   *Release a version* after the slice, with the wait for the reset and recurring goals.
The owner's call.

## 138. *Done* is in dev; the route card comes first on the first start too; a goal's place is *in line*; a goal before *Work* opens on the Orkmaster's tab; files with no Tech nor Design are the Orkmaster's menu's; a recurring round waits for the reset; a decision is committed to dev (27 October 2026, the owner and the PM)

Why: read again after §137: §118.1's *Done* asked for a flag in main, which only Release writes now (§137.2), so goals
would stay at work until *To main* and the left column (§130) would not clear; §132.4 dealt the leaders' questions first,
while a goal's first card is its route (§133.1); *Next* is named in §124.2 and §133.1 though §126.2 removed the groups;
§110.3, §126.4 and §136.10 open a picked goal on its step's tab, which a goal before *Work* does not have; §136.3 leaves
a game at the *Idea* stage, with no Tech nor Design (§122.5), no place to open its files; a recurring round (§136.4)
starts by itself with nothing said for a week near its limits; and a decision is committed (§118.1) with no branch
named. So (this changes §118.1, §124.2, §130.1, §132.4, §133.1, §136.3, §136.4 and §136.10):
1. ***Done* is landed in dev**: a goal is done when its work is in dev (§101), its *Result* ready; it stays in the left
   column until its result is seen (§130.1) and lies on Release's map until *To main* (§137.3). Being in main is
   Release's, never a goal's phase.
2. **On the first start the route card comes first** (§132.4): the blank card moves to the hand, the goal's route card
   is dealt beside it (§133.1), then *Talk*'s questions; §132.5's one line stays on the first card with answers, a
   question of *Talk*.
3. **A goal's place is *in line***: the route card says *3rd in line*; the person moves a goal among the goals not yet
   started, in the left column's one list (§126.2), never as a field (§124.2).
4. **A picked goal opens on its phase**: before *Work* (*Idea*, *Talk*, *Decided*, *Spec*) on the Orkmaster's tab, the
   page of its phase (§126.4); from *Work*, on its step's tab (§110.3, §136.10); then the tab stays as the person left it.
5. **Files with no Tech nor Design** open from the Orkmaster's line's menu as the temporary tab, beside *Settings*,
   *Operations* and the history (§127.2, §130.4); once Tech is made, they are on System (§136.3).
6. **A recurring round within the limits starts by itself** (§136.4); near them, it waits for the reset under the moon
   (§136.5), as any goal, and never spends the person's reserve.
7. **A goal's decision is committed to dev** when it is confirmed (§118.1); it reaches main with the goal's work, by
   *To main* (§137.4).
The owner's call.

## 139. A goal of one party opens on that party's tab at every phase (27 October 2026, the owner)

Why: the owner: a goal that belongs to one party should open on its tab at once, whatever its phase. With one party on
its route the Orkmaster's page of a phase says little (*Asked*, a *Gist*, a route of one step): its one section is its
leader's (§117.5), *Talk* is its leader's alone, and the party's tab shows the same phase whole (the section, its theses
at the left, its will-be on its map at the right, §118.4); an idea addressed to a party is mostly written on its tab
(§124.4), and moving the person off it says nothing. So (this changes §138.4):
1. **A goal whose route is one party** (an idea addressed to it, *@Tech* or its open tab, §124.4; the short way, §118.2;
   a route of one step, §117.5) **opens on that party's tab at every phase**: *Talk* its leader's stance and questions,
   *Decided* the decision, *Spec* its section whole, *Work* its will-be, *Done* its *Result*, each through the party's
   map.
2. **A goal of several parties** keeps §138.4: before *Work* on the Orkmaster's tab, from *Work* on its step's tab.
3. **When the route changes**, the next opening follows it: a step added (§117.1, §133.1) makes it a goal of several
   parties; steps taken off to one make it a goal of one. The tab the person has open is never switched under them.
The owner's call.

## 140. The Orkmaster's tier is not chosen; a head on the route card is taken off by its ×; *+* never offers Release; the picking mode ends on *Stop picking* (27 October 2026, the owner and the PM)

Why: read again after §139: the Orkmaster's header offers its tier (§110.4, §135.1) though it routes and joins on the
cheaper tier, never the stronger (§117.2–§117.3, §133.1), so the choice changes nothing; a head pressed on the route card
takes its party off (§133.1) where a head pressed anywhere else opens its popover (§110.7), one gesture with two
meanings and a party lost by a slip; the route card's *+* offers any of the project's parties though Release is never a
step (§137.1); and the picking mode's *Done* (spec 94 §1.5) is a goal's phase's word too (§118.1; one word a thing,
§121.1). So (this changes §110.4, §133.1, §135.1 and spec 94 §0, §1.5):
1. **The Orkmaster's header shows its AI tool alone**; its tier is always the cheaper, said in its popover (*Routes and
   joins on the cheaper tier: it never writes a spec*, §117).
2. **On the route card a head is taken off by its ×**, small at its corner; a press on the head opens its popover, as
   everywhere (§110.7).
3. **The route card's *+* offers the parties that can be a step**: every party of the project but Release (§137.1).
4. **The picking mode ends on *Stop picking***, Esc, sending the idea or taking off its party's mark (spec 94 §1.5).
The owner's call.

## 141. An idea addressed to a party may pin any card of that party's map (27 October 2026, the owner)

Why: §124.5 names what an addressed idea may point at (*a part of System, a screen or a pain*), written when those were
the only maps; Art's map (§135.4), Game design's *Loop* (§112.8) and Release's map (§137.3) came after, and each would
need its line. So (this changes §124.5 and §135.4's last clause):
1. **In picking (spec 94 §1.5), any card of the addressed party's one map (§134.2) is pinned** to the blank card as a
   mark: a part of System, a screen, a pain, an asset, a card of the loop, a goal on Release's map, and whatever map
   comes later, with no list to grow.
2. A general idea (the Orkmaster's tab, no party addressed, §124.4) has no picking: it is its text alone.
The owner's call.

## 142. No temporary tab: the pane opens one thing over its map, with ← back; the tabs are the leaders alone (27 October 2026, the owner and the PM)

Why: the owner: the temporary tab is a weak place. It stands in the row of who looks (§110.1) while it holds what is
opened, and it has rules of its own to learn (replaced by the next, pinned, *Back*, §104.8, §120.2); on the phone it is
a screen anyway (spec 94 §3.2). What it holds is of three kinds: a read of a card (a diff, a task's log, a failure's
lines, a file, an asset large, a role's text, the talk behind *More*), a place (Settings, Operations, the history, the
files with no Tech nor Design, *New party*), and Play. So (this changes §104.8, §111.1, §120.2, §127.1–§127.2, §130.4,
§136.3, §136.7, §136.11, §138.5 and spec 94 §1.4, §3.2, §3.7):
1. **The pane opens one thing over its map**: whatever is no map opens in the pane itself, its title saying where it
   came from (*← System · server/lobby.ts*); **←** or Esc goes back to the map as it was left, the card it came from
   lit. Nothing is added to the row of tabs: **the tabs are the leaders alone** (§110.1). One thing at a time, the next
   replacing it; nothing is pinned.
2. **A read of a card**: the lifted card (§120.1) stays the quick look; **Open** on its back opens it over the pane (a
   diff, a log, a failure's lines, a file, an asset large, a role's text).
3. **A place**: *Settings*, *Operations*, the history, the files (§138.5) and *New party* open from the Orkmaster's
   line's menu (the tabs' *+* for *New party*) the same way, over the pane, with **←**.
4. **Play**: **▶ Play** turns the pane into the project running (§111); **←** goes back to the map while it keeps
   running, **▶** again returns to the same run, never a restart; **■** in the pane's title stops it (§111.4: one Play a
   project).
5. **A long text of a phase** (*More* of *Talk*, the agents' full text of a spec, §104.5, §118.1) unfolds in place on its
   phase's page, never opened elsewhere.
6. **The hand stays under everything opened** (§104.8): a card is answered while a diff is read.
7. **The narrow width does the same**: what opens over the pane is a screen of its own, **←** the browser's back (spec 94
   §3.3); one rule at both widths.
8. **Side by side and pinning** are not made; asked again when the owner says so (§120.4, §129.3).
The owner's call.

## 143. The Board's columns stand under the tabs: a tab is its column's head, the Board has no header of its own; the Orkmaster's column is its routing (27 October 2026, the owner)

Why: the Board is every party a column (§104.7), each headed by its leader's head and name, while the same heads stand
in the row of tabs over it (§110.3): the leaders said twice. The members' heads on the task cards are not a repeat (who
does a task, not who leads). The owner chose the tabs as the columns' heads over a Board by the state of the work. So
(this changes §104.7, §110.3 and spec 94 §3.5):
1. **On the Board each column stands under its party's tab**: the tab is the column's head and the Board draws no
   header of its own. While the Board is shown (the Orkmaster's tab with no goal picked, or a goal at *Work* through it,
   §136.10), the tabs take their columns' widths, in the same order; a tab pressed still opens its party's map
   (§110.1).
2. **The Orkmaster's column, under its tab, is its own work**: the routing and the joining of sections at work (§117),
   as cards with its head; never the goals themselves (they are the left column's, §126.2).
3. **The columns share the pane's width** (spec 67 §1.1): a column narrower than a card lays its tasks as spec 67's
   tokens; a tab narrower than its name shows its head alone, the name on its hover and in the pane's title (§110.3).
   No sideways scroll.
4. **At the narrow width the same**: the row of heads (§110.9) heads the columns, each a head's width, its tasks as
   tokens with their element, their member's head and their sign (the name on a lifted card, spec 94 §1.1).
The owner's call.

## 144. The card battler kept: a card is played onto its party's lane, a card that spends carries its cost in its corner, the lane it is about rises while it is held (27 October 2026, the owner and the PM)

Why: the owner wants the window to keep its reference to a card battler: the Board's columns under the leaders' heads
(§143) are its lanes under the heroes, the hand at the foot and the field's motions (§89) its cards. Kept within the
rules: a head is a small accent, never a hero's portrait (CLAUDE.md); a view is looked at, never cast (§110.5: no
cooldown, glow or burst); no count anywhere (§67), so no lane's power, no score, no hero's life and no opponent: the work
is not a fight. So:
1. **A card is played onto the table**: on *Start* (or *Confirm and start*, §134.5) the goal's card leaves the hand for
   the lane of the party of its first step, on the Board (§143), and is laid out there as its tasks, their members' heads
   coming over them. It is §89's *dealt*, from the hand to the lane: no new motion (§127.3), still under reduced motion.
2. **A card that spends carries its cost in its corner**, as a battler's card its mana: the route card, *Start*, *Start
   now*, *Release a version* and *Retry* show their share of the limits (*4%*) small at the bottom left, framed, with its
   words on the card as always (*about 4% of Claude's week*, §121.3); the limits' chips read as what is left to spend
   (§107.1). A card that spends nothing (a question of *Talk*, a fork, *To main*) carries no cost, so what is free is seen
   at once. The cost's frame is drawn in orkUI first (§127.3), not a seventh sign: it is the place of a number.
3. **The lane a held card is about rises**: while a card of the hand is lifted (§104.8), the lane, or the cards of a map,
   it is about lie a little raised, as a battler shows where a card will be played; §89's *lifted*, no new motion.
The owner's call.

## 145. No left column: the window is two parts, the table and the hand; a goal lives in the deck, the hand, on the table or in the discard; the Orkmaster's line is its tab (27 October 2026, the owner and the PM)

Why: the owner: after §143–§144 the left column could go. What it holds is said elsewhere already: what waits for the
person is the hand's (§121.2, §134.1), the goals at work are their cards in the lanes of the Board (§143–§144), a goal is
picked by its stack or a card of it, and *The whole project* is no goal picked (§134.4). Three things are nowhere else:
the goals not started or waiting for the reset, the goals done and not yet seen (§130.1), and the Orkmaster's line
(§126.1). A card battler has their places: the deck and the discard. Nothing of §104.0's frame is built yet: the first
slice only starts (§136.12), so this is cheapest now. So (this changes §104.0, §109.3, §110.1–§110.2, §119.3,
§126.1–§126.2, §127.2, §130.1, §130.4, §132.2–§132.4, §134.4, §136.6, §136.8, §136.12, §138.3–§138.5 and spec 94
§1.2, §2.4, §3.2, §3.4):
1. **The window is two parts**: **the table** (the leaders' tabs and the pane: what and why, through whose eyes,
   §110.1) and **the hand** at its foot (what the person decides, and where the goals wait). No left column. The roles
   are §104.0's: the Orkmaster says what and who, a leader how, what changes and why, a member does.
2. **A goal is in one of four places**: **the deck** (in line: not started, or waiting for the reset under the moon,
   §136.5), **the hand** (its stack while it asks the person, §121.2), **the table** (at work: its cards in its lanes,
   §143–§144, its will-be on its parties' maps), **the discard** (done, until its result is seen, §130.1, §138.1). A
   goal at work that asks a fork is on the table and in the hand at once; a goal is never in two piles.
3. **The deck lies at the hand's left**, beside the blank card; its edges hint how many (five at most, never a number,
   §121.2). Pressed, it opens over the pane (§142) as the goals in line in the Orkmaster's order, with a search: a goal is
   moved among those not started by dragging (§138.3), a press picks it. A goal sent from the blank card goes to the
   hand as its route card (§133.1); *Later, by itself* puts it in the deck; *Talk* or *Start* keeps it in play.
4. **The discard lies at the hand's right**, past Release's *n goals ready for main* (§137.5); its top card is the last
   goal done, face up. Pressed, it opens the goals done and not yet seen over the pane; a goal pressed opens its
   *Result*, and once seen it leaves for the history (§130.1). **The history is the whole discard**, from the
   Orkmaster's tab's menu (§130.4).
5. **A goal is picked** by its stack in the hand, any of its cards on the table (its other cards lit, as §126.5's
   marks), or a goal in the opened deck or discard. Esc, or a press on the picked thing again, picks none: the whole
   project (§134.4). The two axes stay (§110.1): what is picked, and the tab through which it is seen.
6. **The Orkmaster's line is its tab**: the project's name on it (*Orkmaster · Party game*); its **…** holds the
   projects' switcher, *Settings*, *Operations*, the history and the files (§138.5). The AI tools' limits and *Stop all*
   stand at the tabs' right end (§126.1); at the narrow width *Stop all* at the end of the row of heads, the limits'
   chips in the Orkmaster's **…** (§136.8), and *As of 14:02.* on its tab (spec 94 §2.4).
7. **A goal's signs are its places'** (§136.6 goes with the rows): the moon on its card in the deck, the leader's head
   and the alert on its cards on the table and its stack in the hand, *done* in the discard.
8. **The first start** (§132): the pane and the hand only; the blank card in the pane's middle while there is no goal
   (§116.2), then in the hand; the deck is dealt when the first goal waits in line, the discard when the first goal is
   done: a part comes when it has something to hold (§132.1).
9. **The narrow width** is one screen: the table above (the row of heads, the map), the hand at the foot with the deck
   and the discard; what opens over the pane is a screen of its own (§142.7). The goals' screen of spec 94 §3.2 goes.
10. **The first slice** (§136.12) reads *the table and the hand, with the deck, the discard and the Orkmaster's tab's
   menu* where it read *the left column the Orkmaster's line and the goals*.
The owner's call.

## 146. In VS Code a read opens in the editor, not over the pane; the Board can stand in the editor's side bar, narrow (27 October 2026, the owner and the PM)

Why: the owner: Orkboard may well be a VS Code extension, and windows inside the window are not wanted there. The editor
has its own explorer, its diff, its editors and its output; what the pane opens over its map (§142: a diff, a file, a
failure's lines, a log) is drawn a second time inside it. The extension stays a frame (CLAUDE.md, `vscode/`): it draws
nothing of the Board, and handing the editor what it does best is not drawing. So (this makes §142.2 precise for the
editor):
1. **In VS Code a read of a card opens in the editor**: *Open* on a card's back opens a diff as the editor's own diff,
   a file (a part of System, §136.3) at its line, a failure's lines and a task's log in an output channel *Orkboard*.
   The page, told it is in the editor (`app=1`, `gui/extension.py`), asks its frame by `postMessage`; the extension
   accepts only these asks, only from the page's own origin, and opens nothing outside the project's folder.
2. **Everywhere else** (a browser, the phone) the read opens over the pane, as §142 says; a place (*Settings*,
   *Operations*, the history, *New party*) and Play open over the pane in the editor too.
3. **The Board can stand in the editor's side bar**, as a view of its own beside the explorer: the same page at the
   narrow width (spec 94 §3), the table above and the hand at its foot, while diffs and files open beside it in the
   editor. The Board in an editor tab stays.
4. **The extension's tests** (`cd vscode && npm test`) cover the asks it accepts and the ones it refuses.
The owner's call.

## 147. Operations leave Orkboard's window; the person reads four phases; the decision has one button; *Later* only when the limits run low (27 October 2026, the owner and the PM)

Why: read once more as one window (spec 95), four things are still more than the work needs: *Operations* (the person's
daily, 1:1s, retro, mail and Jira, spec 38) are no project's goals, and with Team gone (§122.2) they hang in the
Orkmaster's menu; the person reads six phases where two are moments (*Idea*, while the Orkmaster routes; *Decided*, one
card at the end of *Talk*); the decision's card has *Confirm* beside *Confirm and start* (§134.5), the first only to read
the spec before the work, which is read at any time and stopped from its stack or by *Stop all*; and *Later, by itself*
stands on every route card (§133.1) though §121.3 offered it only when the limits run low. So (this changes §118.1's
phases as the person reads them, §122.2, §127.2, §133.1, §134.5, §145.6 and spec 95):
1. **Operations leave Orkboard's window**: no entry in the Orkmaster's **…**, no card, no row. Their code
   (`gui/ops.py`, `realm/ops_team.py`) stays for Orkline, frozen, which takes them up again with it (§121.4).
2. **The person reads four phases: Talk → Spec → Work → Done.** The route card opens *Talk*; the decision's card closes
   it. The pane's title, the phase marks and the words say these four; the engine keeps *Idea* and *Decided* as its own
   states (the decision is still worded, confirmed and committed to dev, §118.1, §138.7).
3. **The decision has one button, *Confirm and start*** (§134.5): the decision committed, the sections written, the work
   started by itself when nothing is left to settle, else the forks and *Start* after them. A goal is held back by *Hold*,
   in the **…** of its stack or of its lifted card on the table, or by *Stop all*, never by a second button on the card.
4. ***Later, by itself* is on the route card only when the limits run low** (§121.3); else the route card's one act is
   **Talk** (**Start** on the short way, §118.2).
The owner's call.

## 148. orkUI made to fit the new window: the half-tint warm taken; one moon; the icons at the signs' weight; the marks in ink; the elements apart from the signals; the heads at 16 px at least; the races, signs and emblems Orkboard draws; the preview the window as decided (27 October 2026, the owner and the PM)

Why: orkUI's whole set laid out on one sheet against spec 95: the frame holds (the pixel face for headings and buttons,
IBM Plex for the rest, square notched corners, the warm ground of a tabletop game, which the indie developers it is for
know), but its parts were drawn for windows since changed. Three crescents mean three things (the element *void*, the
sign *night*, the icon `moon`) while the moon now means *starts by itself later* (§136.5); the icons (pixelarticons, a
1 px line on a 24 grid) stand beside the signs and emblems (solid pixels on a 7 grid) as two styles; the AI tools'
marks are the most coloured things in a system where colour is a signal (§53.5); the elements sit on the signals' hues
(meadow `#7fbf9a` by success `#86c062`, dust `#d4b77a` by alert `#f0d050`) and lava is a grey that reads as disabled;
the ork's and goblin's green skin is the action's green (`#6aa84f`), so a head beside *Start* reads as a second button;
a head at 12 px is a blot and its tier unreadable; the knight, lich and skeleton are no craft of Orkboard's (§53) and
the lightest heads; the emblems repeat the signs under other names (anvil and restructure, beaker and flask, beetle and
bug, broom and tidy, scroll and page, stall and store); the goal types' signs went (§131.5), the moons of progress went
(§127.3); and orkUI's preview still shows *Agents* and *Review* tabs and counts (§67, §136.11). The repository still
holds orkUI 0.13.0, the full warm; §115's half tint was to be tried. So (made in orkUI first, then copied, CLAUDE.md;
this makes §115, §127.3 and §144.2 precise):
1. **The half-tint warm is taken** (§115, orkUI 0.14.0): canvas `#151412`, panel `#1e1c1a`, table `#1a1816`, raised
   `#282622`, frame `#3a3832`, edge `#908a82`; ink `#dedbd6`, muted `#aca8a1`, faint `#96928c`, the ratios measured in
   orkUI before it is copied.
2. **One moon**: the moon is the sign of *starts by itself later* alone (§136.5; the sign *night*, renamed); the icon
   `moon` goes; **the element *void* is drawn anew**, never a crescent (an empty ring, or a whirl).
3. **The icons at the signs' weight**: the icons the window draws (←, ×, **…**, **+**, the search, the microphone, ▶, ■,
   the chevrons) are drawn again on the signs' grid in solid pixels, orkUI's own; the others go. Pixelarticons' licence
   stays beside them while any of theirs is left.
4. **The AI tools' marks in ink** in the window (a seat's tool under its head, a limit's chip); their brands' colours only
   in the seat's popover, where the tool is chosen (§110.7). The ranks' chevrons in ink.
5. **The elements apart from the signals**: each of a hue no signal has, and each at least 3:1 on the raised panel:
   meadow toward teal, dust a darker ochre, lava a warm red-brown never the danger's, ice and void as they are but void's
   new mark; measured in orkUI.
6. **No head in the action's green**: the ork's and goblin's skin a step darker, toward olive, so a head beside a button
   is never read as one.
7. **A head is 16 px at least**: on a card, a seat, a token and a tab; where less room is left, the race's silhouette
   without its tier's gear.
8. **Orkboard draws the four crafts' races** (§53: ork, elf, goblin, gnome; the Orkmaster's crown); the knight, lich and
   skeleton stay orkUI's for Orkline and are not copied into Orkboard's copy.
9. **One vocabulary**: the emblems are not copied into Orkboard's copy (the signs say it); **the signs are pruned**: the
   goal types' signs go (§131.5) and the moons of progress (§127.3); a map card's kind keeps its sign (§104.2: a screen, a
   picture, a sound, a clip, a text, a page, a logo); the states are §127.3's closed set (spec 95 §9).
10. **The cost's frame is orkUI's gem** (its *a price* already), showing the share of the limits (*4%*, §144.2).
11. **orkUI's preview shows the window as decided** (spec 95): the table with its lanes under the tabs, the hand with
   the deck, the stacks, Release's card and the discard, a card with its cost; no count, no *Agents* or *Review* tab.
12. **When**: one orkUI release (0.15.0) with all of the above, copied here before the first slice's faces are drawn
   (§136.12).
The owner's call.

## 149. The cards react as in Balatro, with no motion added; a hand card face down has one back; the heads on a 16 grid read by their silhouette; the detailed art is the marketing's (27 October 2026, the owner and the PM)

Why: the owner asked whether the heads and the cards should be drawn in more detail, as Slay the Spire's or Balatro's.
Slay the Spire's card is a picture, each its own, and carries the game; ours carries what is read all day (a task's
name, its element, its sign, who does it), and a picture a goal would be noise and a cost, against the heads as an
accent (CLAUDE.md). Balatro's cards are plain pixels: what makes them a pleasure is how they answer a hand (they lean
toward the pointer, weigh when played, are dealt with a snap). That is ours to take, inside §89's motions and §127.3's
closed set. So (made in orkUI first, then copied; this makes §89, §127.3, §144 and §148.7 precise):
1. **The cards answer the hand, as Balatro's**, every one of it a part of a motion the window has:
   - **under the pointer** (part of *lifted*): a card of the hand or a map leans toward the pointer, at most 6°, and
     rises 4 px on a pixel shadow; back flat as the pointer leaves;
   - **pressed** (part of *lifted*): it gives a little (to 96%) and springs back on release;
   - **played** (§144.1, *dealt* from the hand to a lane): it flies on an arc with its weight, lands with a short
     overshoot, and the lane's cards beside it make room;
   - **dealt** to the hand: the cards fan out one after another (about 40 ms apart), the stacks closing up;
   - **sealed**: the element's stamp lands a little large and settles;
   - **crumbled**: the card breaks into a few pixel shards that fall, not a fade;
   - **fanned** (a stack pressed, §121.2): the cards spread with the same spring, and close the same way.
   Short and sure: 120–250 ms, a play at most 400 ms; transforms only, at 60 frames a second. **No idle motion**: a
   card at rest is still (a tool looked at all day never sways). **A card at rest and a lifted card being read are
   flat**, so their text and pixels stay crisp. **Under reduced motion** none of it: a card moves at once, a crossfade
   at most. No sound now. A view is still never cast (§110.5): no glow, no burst on a map's switch.
2. **orkUI keeps the motions as tokens** (durations, the spring's curve, the lean's angle, the shards' count), so the
   page carries none of its own (CLAUDE.md, `tests/test_design_system.py`), and its preview plays each.
3. **One back for a hand card face down**: the deck, the cards under a stack's top, the discard's cards under its top;
   a pixel pattern in the frame's and the faint ink's greys on the raised panel, the ork mark at its middle, no colour
   (§53.5). It is the one drawing on the work's surface that is no head and no sign. A map card's back stays its details
   (§120.1): a back pattern is the hand's alone.
4. **The heads on a 16 × 16 grid** (32 at @2x), so §148.7's 16 px is their own size, never a scaled one: **the race read
   by its silhouette** (the ork's tusks, the elf's long ears, the gnome's nose, the goblin's wide ears), **the tier by its
   gear's silhouette** (a hood, a helm, a crown), never by small coloured details.
5. **The detailed art is the marketing's**: large drawn portraits of the same leaders and their races (as rich as Slay
   the Spire's) for the site, the VS Code marketplace, the README and the store's pictures, and at the window's few big
   moments: the first start (§132) and an empty screen (orkUI's `ascii/`'s places). Never on a card, a tab or a seat.
6. **When**: with §148's orkUI release (0.15.0) for the tokens, the back and the heads; the cards' answers built with the
   first slice's hand and table (§136.12); the marketing's art apart from the slices.
The owner's call.

## 150. The phone turned on its side is the table, as Balatro's: a low window keeps the wide layout made compact; upright stays the quick answer; nothing is locked (27 October 2026, the owner and the PM)

Why: the owner: a phone held on its side, as Balatro is played, would set Orkboard apart, and since the person types
little, the keyboard costs little. On its side an iPhone is 844 × 390: the Board's columns under the tabs (§143) are six
of about 140 px, whole cards, where upright they are tokens of about 60 px (§143.4); the hand at the foot with the deck
at its left and the discard at its right is Balatro's own layout. But an installed web app on an iPhone cannot be held
on its side (iOS honours neither `screen.orientation.lock()` nor the manifest's `orientation`); the phone is mostly the
quick answer, a push opened, one card answered with one hand, in seconds; and an idea typed on its side leaves less than
half the 390 px above the keyboard. So (this makes spec 94 §3.1 and §6 precise):
1. **Both ways, nothing locked**: upright is spec 94's narrow width (the quick answer); on its side the phone is **the
   table**. The manifest asks for no orientation.
2. **A low window**: under 500 CSS px of height with 760 px of width or more (§136.9), the wide layout made compact:
   the tabs and the pane's title on one line; the table's cards smaller (spec 67's tokens where a column is narrower than
   a card, §143.3); the hand a strip whose cards overlap in a fan, as Balatro's, a card rising out of it under the finger
   (§149.1); the deck at its left, the discard at its right; the safe areas of the notch's side kept clear
   (`env(safe-area-inset-left)` and `-right`). The same layout serves any low window (a laptop's split screen).
3. **Writing on its side**: the blank card pressed grows into a field over the keyboard with **Send** and the
   microphone (§125, spec 94 §3.6); turning the phone upright to write is as good, the text kept as it was.
4. **Turning keeps the place**: what is picked, the open tab, a lifted card and what is open over the pane stay as they
   were when the phone turns.
5. **The marketing's pictures are on their side**: the VS Code marketplace, the site and the store show the table as a
   phone on its side shows it.
6. **When**: with the phone's one page (§128, spec 94), after the first slice.
The owner's call.

## 151. A party's squad is who it has, its size how the work goes; a specialist's view is marks on its party's map; one place makes and edits the parties; Marketing comes back with UA (28 October 2026, the owner and the PM)

Why: the owner asked to bring the lenses back as the squad's members' (an ASO and a UA specialist in marketing, an
accessibility check beside a designer). As tabs or screens a member that would be §134.2's segmented control again, and
the window would grow with the squad; as marks on the one map it is not. And the library already has the specialists
(`realm/library.py`: an Art director's Artist, Animator, Icon artist, Sound designer, Composer and Art reviewer; Tech's
Grunt, Tester, Reviewer and Security reviewer), more than §104.1's three seats (one a stage) hold, while a specialist
idle costs nothing: what a party spends is how many of its tasks run at once and how many stages each goes through. A
squad chosen by its cards is what the person understands (no Composer, no music); the size is what it costs. Marketing
was no party since §109.1 though its specialists are in the library, and UA is not. So (this changes §98, §104.1,
§107.5–§107.6, §110.6, §116.1, §127.1, §137.1 and §122.5; made with spec 95):
1. **The squad is who the party has**: the specialists the person picks from its craft's cards, at most seven (its
   leader, up to five who do, up to two who check). The leader gives each task to the one it is for (the music to the
   Composer) and each check to the checker it concerns; a task no one in the squad can do is said in *Talk* (*No
   composer in the squad*), never given to someone else.
2. **The size is how the work goes**, apart from the squad:

   | size | a task's stages | at once | |
   |---|---|---|---|
   | **Lean** | plan → do | 1 | no separate check: the doer runs its own tests |
   | **Standard** | plan → do → check | 2 | one checker checks each task |
   | **Full** | plan → do → check by every checker it concerns | 3 | the Reviewer and Security on code, Accessibility on screens |

   With no checker in the squad, the leader checks, said plainly. The cost is said on the size (*about 3% of Claude's
   week a goal*), never on the squad. A size sets the seats' tiers by default; each is changed in its popover (§110.7).
   When the limits run low the Orkmaster lowers *at once* by itself and says so.
3. **A party's header**: its squad's heads at 24 px grouped *Leads* | *Does* | *Checks*, turned while they work, and its
   size in one word beside them.
4. **A specialist's view is marks on its party's map**, never a tab, a screen or a switch: the specialist's small head
   and, when something is wrong, the alert on the cards it has something to say about; the lifted card's back lists what
   each said; **Open its view** in its popover opens its whole view over the pane (§142): Accessibility's report by
   screen, ASO's store page, Security's parts at risk, the Tester's cover on System's parts. A specialist with nothing to
   read in the project works with no view until there is (§112.9).
5. **One place makes and edits the parties**, over the pane (§142), from the first start (§116.1), the tabs' **+** and a
   party's **…** (*Edit*):
   - **at the left**, the project's kind as a list read from the project (*Read from the project: a Node game*, to be
     corrected), and under it the parties, **under the project's stages as their headings** (*Idea*, *Being made*,
     *Live*); the stage the project is at is picked on its heading (*The project is here*), and the parties of the
     stages reached come ticked. A party is ticked or unticked, and pressed it opens at the right. **Release** is ticked
     and locked (*the one way into main*, §137.1);
   - **at the right**, the size (*Lean · Standard · Full*) with what it means and costs at its left; under it the
     leader's row (its head, its name, its map in one line, *Map: System, the code's containers and their links*, its AI
     tool and tier); under it two columns, **Does** under a sword and **Checks** under a shield, of the craft's role cards
     (a head, a name, its tool's mark, its tier's gear), each ticked or not, a press opening the same popover as the
     header's (§110.7). The size shows on the columns: under **Lean** *Checks* is dimmed (*No separate check: the doer
     runs its own tests*), under **Standard** *One checker checks each task*, under **Full** *Every checker a task
     concerns*;
   - **at its foot**, what the ticked parties cost together (*These parties: about 9% of Claude's week a goal*) and one
     **Start** (the first time) or **Save**: *From the next task*, a task at work finishing as it was.
   At the narrow width the left is a screen and the right the next. *New party* and *Edit the party* are this one place.
6. **Release's squad** is its leader, its size **Lean**, its tier the cheaper (§137.1 said so).
7. **Marketing comes back as a party**, offered at the *Live* stage (§122.5): led by **Growth**; its squad from **ASO**,
   **UA**, **Copywriter**, **SEO** and **Community**, checked by the **Editor**. **ASO is Marketing's**: Release keeps
   the version (its engineer, its notes, its checker); a project with no Marketing may put ASO in Release's squad.
   **Marketing's map is the way people come**: the channels → the store page or the site → the install → the first
   session, UA's on the channels, ASO's on the store page, read from what the project holds (a store's metadata files,
   such as `fastlane/metadata`; the site's pages; the analytics when there are), else waiting (§112.9).
8. **UA joins the library**: *Buys the installs: the campaigns, the networks, what an install costs*, a gnome (§53:
   a gnome markets); its view reads the ad networks once they are connected, until then it works with none.
9. **The sword and the shield** are drawn in orkUI on the signs' grid (§148.3), as the columns' marks, not as signs of a
   state (§127.3).
10. **When**: the squad, the size and the one place of the parties with the first slice (its parties, §136.12);
   the specialists' views with the other maps after it; Marketing and UA in the library and the recipes at any time.
The owner's call.

## 152. In picking, cards are taken with a box, as Warcraft's units; a box that takes a whole group pins the group (28 October 2026, the owner and the PM)

Why: the owner: an idea addressed to a party could take its cards with a box, as units are taken in Warcraft, not only
one press a card (§141). A change often touches several places at once (three screens of one flow, two parts of System),
and orks taking their marks with a box is the reference the window wants (§144). Kept so the box never gets in the way:
only while picking, never against a touch screen's scroll, and never pinning a whole map card by card. So (this makes
§141 and spec 94 §1.5 precise):
1. **Only in picking** (spec 94 §1.5): out of it a drag on a map scrolls it and takes nothing.
2. **On the desktop** a drag from the table's empty place draws the box; every card it takes is pinned as a mark; Shift
   and a press adds or takes off one card; a press on a card still toggles that one.
3. **On a touch screen** a drag is the scroll and stays so: a tap toggles one card; the box is a long press on an empty
   place, then a drag.
4. **Seen as Warcraft's, in orkUI's look**: the box a dashed line in the ink; a card taken carries pixel brackets at its
   corners (as the rings under units taken) and rises a little (*lifted*, §89); no colour (§53.5). The brackets are
   drawn in orkUI (§148).
5. **A box that takes a whole group pins the group**: all of a container's parts pin the container (System), all of a
   flow's step its step (Design), all of a lane's cards that lane; a box over the whole map pins the map (*all of
   System*), the same as an idea with no mark, and it reads so.
6. **The marks on the blank card** are chips (a name and ×) wrapping on lines; past five, the first five and *and 3 more*
   in words, a press showing all.
7. **It ends as picking ends** (*Stop picking*, Esc, sending the idea, taking off the party's mark), what was taken
   staying the idea's marks.
The owner's call.

## 153. What a party asks of the project: Product at the start, each other leader at its party's first goal, inside a goal's three; a question is a card of up to four choices and *Other…*; a goal's questions a stack, one a card (28 October 2026, the owner and the PM)

Why: the owner asked whether each party's leader interviews the person about the project when it is first opened (what
it is for, whom, what hurts them). None does: the first start reads the project's files (spec 75, no model) and asks one
line only of an empty folder (*What is this project for?*); a leader asks at most three questions a goal, in *Talk*
(§121.2: two rounds at most); whom it is for and what hurts them are pinned only when the person puts them on Product's
map (§134.2). An interview of every leader at the start is too much: the parties are picked together at the first start
(§151.5), and four parties at two or three questions each is about twelve before any work. And the cards in the hand are
there so the person writes less: an answer should be one press, picked from what the project already says. So (this
makes spec 75 §2, spec 85 §1, §121.2, §132.4–§132.5 and §138.2 precise):
1. **At the start only Product asks** of the project: two or three cards, *whom it is for*, *what hurts them*, *what it
   leaves out*, each only where the project's files (the README, the docs) do not say it; where they do, the leader's
   reading is the card's pick, one press to confirm. **In a game Game design asks them** (§122.5: a game's first parties
   have no Product); with neither, the Orkmaster's one line (*What is this project for?*) stands, as for an empty folder.
   The other leaders are quiet at the start.
2. **Product's cards are dealt after *Start*** (§132.2), as one stack of no goal's, its leader's head on it, beside the
   blank card and Release's card (§121.2's two such cards become three). **They hold nothing back**: the blank card is
   written and the first goal sent with them unanswered, its route card coming first as §138.2 says; unanswered, they
   stay in the hand until answered or let go (*Let … decide*). §132.5's one line reads on them *Pick an answer: the
   leader keeps it for the project*.
3. **Every other leader asks of the project at its party's first goal** (the first goal whose route has its party), once
   in its party's life, in that goal's first round of *Talk*: Tech of the architecture and the stack, Design of the mood
   and the references (spec 85), Marketing of the channels and the tone. **Inside the goal's three, never beside them**:
   the goal's own questions and the project's of every leader on its route share the three places (§121.2). A small
   first goal (a bug) gets only the project question it cannot be done without; the rest wait for the party's next
   goals. A leader asks nothing the repository answers: Tech of a codebase reads its stack and containers
   (`realm/system_overview.py`) and asks only what the code cannot say (where it runs, what it must not use); from
   scratch only in an empty folder. Release asks nothing of the project (§137.1: no step of a goal's route).
4. **What is answered is the project's**, kept beside the segments (`<state_dir>/`), read into every party's prompts,
   never asked again; Product's whom and what hurts become the segments and pains of Product's map (§134.2). A fact a
   leader reads from the files is kept the same way, without a question. The answers are read and changed in the one
   place of the parties (§151.5), at the right under the leader's row; a change applies from the next goal.
5. **A question is a card of up to four choices and *Other…***: two to four real choices (`CHOICES`), never padded to
   four; one picked for the person (●), with its why. The choices come from what the project holds, not from what is
   common: Tech's first is the stack it found, with where it saw it; Product's are the segments and pains kept and the
   README's. ***Other…*** (it replaces *Open…* on a question's card) opens the field on the card, with the picked answer
   already in it, so the person edits rather than writes.
6. **A goal's questions are a stack, one question a card** (§121.2's stack a goal), never several on one card (a card is
   one decision; three questions of four choices are a form, unreadable on the phone, and a single *Send* under picks
   made for the person is pressed unread). The top card is answered with one press and the next is under it; the
   answers go together after the last (the leaders read them at once, as today). The stack's depth shows as its edges,
   never as a count (*1/3*, §121.2, §145). On the stack, *Let … decide* answers the rest with the picks; the goal's
   questions together open over the pane (§142), never as a dialog (§127.1), for whoever wants them so.
7. **When**: with *Talk*'s questions and the hand in the first slice (§136.12); the stack on the phone with the phone's
   one page (§128, §150.6).
The owner's call.

## 154. Product's party is the knights, Release's the undead: a lich leads it, skeletons are its hands; Orkboard draws six races (28 October 2026, the owner)

Why: read again after §153, §148.8 keeps four races in Orkboard's copy (the ork, the elf, the goblin, the gnome) and
leaves the knight, the lich and the skeleton to Orkline, while Product's leader is drawn a lich (`realm/roles.py`
`RACES`: *a lich for now*) and Release's a skeleton (`realm/library.py`); Release is in every project (§137.1) and
Product asks first (§153.1), so the first heads the person meets would have none. The owner: the undead are no
product's face, and a product wants more magic; the knights are already drawn in orkUI, and the undead suit the keepers
of what is out. So (this changes §148.8 and makes §53 precise):
1. **Product is the knights**: its craft's race is the knight (`RACES["product"]`), every product role, its leader too,
   wearing its tier's gear as every head (§53).
2. **Release is the undead**: its leader, the Release manager, a **lich**; every other seat of Release's squad (its
   engineer, its notes, its checker, §151.6) a **skeleton**, whatever their crafts elsewhere: in Release the race says
   the party, the lich who leads it. A role of Release's put in another party wears its craft's race there.
3. **Orkboard draws six races** (§148.8 changed): the ork, the elf, the goblin, the gnome, the knight and the undead
   (the lich and the skeleton); orkUI's copy keeps all three heads at every tier (they are there today), drawn anew on
   §149.4's 16 grid with the others, each read by its silhouette (the knight's helm, the lich's sunken face and jaw, never a
   crown: the crown is the Orkmaster's alone; the skeleton's bare skull), never by colour (§53.5).
4. **The words**: CLAUDE.md's *an agent's craft is its race* gains *a knight leads the product, the undead release it*;
   the races' names stay code (`knight`, `lich`, `skeleton`), the interface says a role's name, never its race.
5. **When**: with §148's orkUI release (0.15.0) for the heads; `RACES` and the library's races with the first slice's
   parties (§136.12).
The owner's call.

## 155. A party's leader is its race's higher form, grown, not worn: the tier is what a head wears, the leader what grows out of it; Product's members are griffins (28 October 2026, the owner and the PM)

Why: the owner liked Release's lich and skeletons (§154.2) and asked for the same in every party, so its leader stands
out by its silhouette. On a 16 px head (§148.7, §149.4) the tier is already the gear on top (the laborer's cap, the
warrior's helm, the elder's hood); a leader marked by another hat would merge with it. The lich and the skeleton work
because the creature changes, not the hat. Kept within the races of §154.3 (no new people beside them), the crown the
Orkmaster's alone, colour a signal (§53.5). So (this changes §154.1 and §154.3, and makes §53 and §149.4 precise):
1. **The tier is what a head wears; the leader is what grows out of it.** A party's leader (its *Leads* seat, §151.1)
   is drawn as its race's higher form; its mark grows **outside the gear's outline** (at the sides, from the temples,
   off the brow), never under or in place of the tier's gear, which the leader wears as every head (§53).
2. **The leaders and their parties**:

   | party | its members | its leader | the leader's mark |
   |---|---|---|---|
   | Tech | orks | **an ork shaman** | ram's horns curling down at the sides, braids with bone beads; war paint under the eyes; its skin a deeper green than the orks' |
   | Design | elves | **an elf dryad** | a stag's antlers rising from the temples, framing the gear |
   | Data | goblins | **an imp** | a goblin with small horns and small dark bat's wings low behind the ears; its skin a dark red-brown |
   | Marketing | gnomes | **a gnome fairy** | the bearded gnome with large light round wings rising over the shoulders |
   | Product | **griffins** | **a unicorn knight** | the knight's helm with a unicorn's horn off the visor's brow, slanting out of the gear's outline |
   | Release | skeletons | **a lich** | as it is (§154.2) |

   The Orkmaster stays the crowned ork (`peon-crown`), above every party.
3. **Kept apart on 16 px**: the shaman's horns curl down, the dryad's antlers branch up, the imp's horns are a small
   pair, the knight's horn is one slanting spike, so four marks of the head never read as one; the imp's wings are small,
   dark and low, the fairy's large, light and high. **The silhouette carries the leader**: the war paint, the shaman's
   green and the imp's red-brown are accents (§149.4: never by small coloured details). The imp's red-brown is lava's
   warm red-brown (§148.5), never the danger's red; the shaman's green deeper and darker than the orks', never the
   action's green (§148.6).
4. **Product's members are griffins** (§154.1 changed): a beak and a feathered crest, no horn, so the horn is the
   leader's alone; the knight is Product's leader only. A griffin reads at 16 px where a horse's head from the front
   does not.
5. **The names stay code** (§154.4): `shaman`, `dryad`, `imp`, `fairy`, `griffin`, beside `peon`, `elf`, `goblin`,
   `gnome`, `knight` (drawn with the horn), `lich`, `skeleton`; the interface says a role's name, never its race.
   CLAUDE.md's line on the races says it.
6. **Made in orkUI first** (CLAUDE.md): the six leaders drawn first at 16 px in one row, read side by side and without
   colour, before their tiers are drawn; then every head of every tier at 1x and @2x.
7. **When**: with §148's orkUI release (0.15.0), the heads redrawn on the 16 grid with the others (§149.4); the roles'
   races (`realm/roles.py` `RACES`, the leader's form by its seat) with the first slice's parties (§136.12).
The owner's call.

## 156. A leader reads the project through its map: every call carries its map as text, read by code and current with dev; the parties are kept in step by the parts of their maps, never by reading each other's specs; what a call may read is bounded in fact (28 October 2026, the owner)

Why: the owner asked whether, on a project opened as it is, each party's leader reads what it needs without being
flooded. It does not yet: the maps of §104.3 and §112 are read by code, but no call is given them; every leader's call
says *You may read the repository*, so Product, Design and Game would explore the code to learn its screens or its loop;
*Read at most n files* is a request (`IdeaKeeper.reads`), the budget the only bound; Claude Code's own context (the
project's CLAUDE.md, the person's MCP servers and skills) is paid on every call, and §117.2's parts at once pay it once a
leader; §153.4's *read into every party's prompts* has no bound; who reads the README and the docs for §153.1's picks is
not said; Orkboard's own `docs/decisions.md` is 293 KB; the night's refresh reads again every goal whose paths changed,
on the elder tier; a task is pointed at its whole spec. And the project changes under a leader not only by code: a spec
lands in dev too, and §86 finds two goals meeting by their files, while Product's map rests on screens and the flow's
steps, and a goal of Product may touch no file at all. So (this makes §86, §104.3, §104.6, §112.6–§112.8, §117,
§118.1, §118.5, §153.1 and §153.4 precise):
1. **Every leader's call carries its map as text**, after its voice and before the step's own context: *The map of
   <its lens> at dev <commit>*. Read by code, with no model, from what its views are read from (`system_overview`, the
   screens and routes, the segments and pains, the loop's cards); rebuilt at dev's every new head (as
   `project_map.landed` does for System), so a merge of code or of a spec. The leader reads the repository only to read
   further what its map names.
2. **The map's text is bounded**: the top level whole, a part a line (the containers, the flow's steps, the loop's
   cards, the segments and their pains); in detail only the parts the call is about (the idea's marks, its touches, its
   route's parts); then *Changed since your last call*, each change with its goal and who decided it (§112.6). About
   3,000 characters at most; past it the top level keeps only its names, and says so. The map stands before what
   changes from call to call, so its text is the same between two heads of dev and the prompt's cache keeps it.
3. **A map of judgement is never rewritten unseen**: its cards (the pains, the loop) are tied to what they rest on
   (§112.7–§112.8); a change under one marks the card with the changing goal's element, as a changed card is sealed
   (§104.2), its back saying *what it rests on changed: goal #N, decided by …*; the same line is in the map's text at the
   leader's next call. The leader may change the card, with its why, seen as the leader's (§118.6).
4. **A promised change is a ghost on every map it touches**, not only on its goal's (§104.6 widened): a spec's *Will be*
   names the parts of the maps by their ids; a part that another party's card rests on, promised to change, carries on
   that party's map the promising goal's ghost (§104.2's motion, in its element), its back saying *promised: goal #N will
   change this, decided by …*. No call. Neither mark adds a sign or a motion to §127.3's closed set.
5. **Goals meet by the parts of their maps as well as by their files** (§86.1–§86.2): an open goal of another party that
   rests on the parts a spec's *Will be* changes meets it as two goals changing the same thing do, a fork in the hand
   and a mark on both goals' cards (§131.4); the same cheap judge, the person decides, a re-plan only on their yes.
   Only then does a leader read another party's spec, and of it only *Done when* and *Will be* (§118.5).
6. **A change that touches another party's map offers that party on the route card** (§133.1), with its cost, before
   any start; a bug's short way (§118.2) too: a fix of Tech's whose *Will be* touches a part a card of Product rests on
   offers Product. The Orkmaster offers, the person says yes.
7. **The project's facts by party** (§153.4): each answer and each fact read from the files has its party; a leader is
   given the common core (whom it is for, what hurts them, what it leaves out: about 600 characters) and its own party's;
   another party's only when the goal's route has that party; a member none, but what its leader wrote in the task's
   brief.
8. **What a call may read is bounded in fact, not only in words**: the read-only calls deny `Read` on lockfiles,
   vendored copies, generated output and the decisions file whole (the rules `_claude_read_dirs` already writes);
   *Talk* reads no file (its map is enough); the files a call did read are counted from the tool's output, and a call
   past its bound is a line in the day's log.
9. **The floor of a leader's call**: a read-only call runs with none of the person's MCP servers (`--strict-mcp-config`
   with an empty configuration) and no skills (`--disable-slash-commands`); the project's CLAUDE.md stays (Claude Code
   reads it, and Tech needs it; `--bare` drops it but asks an API key, never a subscription). Measured before and after
   on `calls.jsonl`: what a call writes to the cache.
10. **Product's reading at the start** (§153.1): the files are chosen by code (the README, `docs/`'s top level by name,
   the first part of each), one call with no tools on the cheaper tier, its budget as the `kind` step's.
11. **The decisions file** (§118.1): its next number is read by code (the last `## N.`); a leader is given its goal's
   entry, cut by code, and the headings of the last ten, never the file whole. At the first opening, a log of decisions
   the project keeps already (`docs/adr/`, a `decisions.md` elsewhere) is offered as the path, never a second one.
12. **Coming back**: a party's reading (the summary a party keeps today, `read_goal`, read again by the night's refresh)
   gives way to its map's text (1), rebuilt by code at dev's head, so nothing is read again by a model when the person
   comes back; the night and its refresh go with §131.2.
13. **A task reads the spec's common part and its party's part**, and of the others only *Done when* and *Will be*
   (§118.5 for the task too); its prompt names those, not the whole spec.
14. **When**: 1–2, 7, 8, 12 and 13 with the first slice's sections (§136.12), Tech's *System* first and the other maps
   as they come (§104.14); 3–6 with the other maps; 10 with §153; 9 and 11 at any time, 9 after its measure.
The owner's call.

## 157. What §151–§156 left uneven: the project's questions are a stack among the stacks; Release's squad is its leader until seats are added; spec 95 read up to §157 (28 October 2026, the owner and the PM)

Why: §151–§156 read against spec 95 and each other: §153.2 lays Product's questions *beside the blank card and Release's
card*, §121.2's hand, while §145.3–§145.4 laid the hand anew (the blank card, the deck, the stacks, Release's card, the
discard); §154.2 names Release's engineer, notes and checker as its squad's seats, while §151.6 makes Release's squad its
leader alone; and spec 95, which a decision changing the window changes in the same commit, stopped at §152 (it still
says *the four crafts' races only*, §148.8, which §154.3 changed). So (this makes §153.2 and §154.2 precise):
1. **The project's questions are a stack among the stacks** (§145.3, §121.2): one stack of no goal's, its leader's head
   on it (Product's, or Game design's in a game, §153.1), laid by its top card's urgency as any stack (a question the
   work does not wait for: after the others); answered or let go (*Let … decide*), it leaves the hand. No fixed place
   beside the blank card or Release's card.
2. **Release's squad is its leader** (§151.6), Lean, on the cheaper tier; its engineer, its notes and its checker are
   seats the person may add in the one place of the parties (§151.5), and a seat added is a skeleton (§154.2).
3. **Spec 95 is read up to §157** in this commit: the project's questions and the stack (§153), the six races and the
   leaders' forms (§154–§155), what a leader's change shows on another party's map and on the route card (§156.3–§156.6),
   and the first slice with what joined it since §136.12.
The owner's call.

## 158. A bug's Talk finds its cause; a party's race is its party's, not its role's craft: six parties, six races, six leaders; the rest of the cast is the marketing's (28 October 2026, the owner and the PM)

Why: read after §157, two things were left open. A bug's short way skips Talk (§118.2), yet §153.3 asks a party's
question about the project *in its first goal's Talk*, and a bug's report is often too vague for its fix to hit its
cause. And §155.2 names the leaders of Tech, Design, Data, Marketing, Product and Release, while a game's parties are Game
design, Tech, Art, Release, LiveOps and Marketing, an app's Product, Design, Tech, Release, Run and Marketing
(§109.1, §122, §151.7): by their leaders' crafts (`realm/library.py`) a game's Game design and Art would both be led by
elves, a site's Run by a second ork shaman beside Tech's, against §155.3; and Data is no party. More characters would
make the heads less a sign of their party and cost orkUI a head at every tier, each told apart by its silhouette at
16 px (§149.4). So (this changes §118.2, §133.1, §147.4, §153.3, §53, §154.2 and §155.2; CLAUDE.md's line on the races
with it):
1. **A bug's Talk is its diagnosis**: Tech alone, one round, on the cheaper tier. Its leader reads its map and the parts
   the report touches, and the failure's lines or a log when there are; it asks at most three questions about the cases
   (where it happens, its choices read from the map's screens and containers; the steps; what was expected; since which
   version), each a card of §153.5, and lays **its guess of the cause** as one more card (*I think the lobby's timer is
   not reset on reconnect: `server/lobby.ts`*), with *Yes*, *No, it's elsewhere* and *Other…*. A question of Tech's about
   the project (§153.3) rides in the same stack. The cause found is the *Why* of Tech's section.
2. **A bug that already reproduces skips it**: a failure's lines from the gate, a stack trace or a failing test in the
   report; its route card keeps **Start** (§133.1, §147.4). Else the route card's one act is **Talk**, said plainly
   (*Tech alone: finding the cause*).
3. **A bug writes no decision** (§118.2, §118.7): it does not change what the project is; nothing is committed to the
   decisions file.
4. **A party's race is its party's** (§154.2's rule, for every party): every head on a party's seats wears that party's
   race, whatever its role's craft, and its leader is that race's higher form (§155.1). A role put in another party
   wears that party's race there; a Grunt is an ork in Tech, its party's race elsewhere; the Orkmaster stays the crowned
   ork. On the Board a head says its member's party at a glance.
5. **Six parties a project, six races, six leaders**:

   | in a game | in an app or a site | its race | its leader |
   |---|---|---|---|
   | **Game design** | Product | griffins | a unicorn knight |
   | Tech | Tech | orks | an ork shaman |
   | **Art** | Design | elves | an elf dryad |
   | **LiveOps** | **Run** | goblins | an imp |
   | Marketing | Marketing | gnomes | a gnome fairy |
   | Release | Release | the undead | a lich, skeletons its hands |

   Game design takes Product's knights: in a game its design is the product (§109.1, §153.1), and a game has no Product
   party, so two unicorn knights never meet; Art takes the elves (a game has no Design); LiveOps and Run take the goblins
   (a live project is watched by its numbers, its errors and its incidents), §155.2's *Data* row read as theirs. A
   project of another kind maps its parties by the same rows: what it makes, its code, its look, its running, its
   marketing, its release.
6. **No new characters on the table**: the cast that the heads draw stays these six races and the crowned Orkmaster.
   **The rest of the cast is the marketing's** (§149.5): large portraits of every race and leader, and a gallery of them
   with a line each on what they do, for the site, the VS Code marketplace and the README, and at the window's few big
   moments (the first start, an empty screen); never a card, a tab or a seat. A new face on the table, if the owner
   ever asks for one, is a form inside a race (§129.3), never a seventh race.
7. **The words** (CLAUDE.md): *an agent's craft is its race* becomes *a party's craft is its race*; the races' names stay
   code (`griffin`, `knight`, …), the interface says a role's name, never its race (§154.4).
8. **When**: the bug's Talk with *Talk* in the first slice (§136.12); the races by party with the first slice's parties
   and §148's orkUI release (0.15.0), as §154.5 and §155.7; the gallery apart from the slices.
The owner's call.

## 159. Release's card is the discard's: the goals done and those ready for main are one pile at the hand's right (28 October 2026, the owner)

Why: the owner, on S1's mockup (spec 98): *the bottom part with the cards is getting too complicated.* The hand held the
blank card, the deck, the stacks, Release's card and the discard; Release's card (*n goals ready for main*, §137.5) and
the discard (the goals done and not yet seen, §145.4) are both the goals whose work is done, one waiting for the
person's look, the other for *To main*, side by side at the hand's right. So (this changes §137.5 and §145.4):
1. **Release's card goes into the discard**: the discard's top card, the last goal done face up, carries Release's
   leader's head (the lich) and *n ready for main* under it while dev holds goals that main lacks; with nothing ready,
   the discard is as before; with nothing done to see and goals ready, the discard is that line alone on its back.
2. **Pressed, the discard opens over the pane** (§142) as two parts: the goals done and not yet seen (a goal pressed
   opens its *Result*, then it leaves for the history, §130.1), and **Ready for main**, Release's map's goals with
   **To main** (§137.4), as Release's tab shows them.
3. The hand from left to right: the blank card, the deck, the stacks, the discard. Release keeps its tab and its map
   (§137.3); *Release a version* is unchanged (§137.4).
The owner's call.

## 160. The hand is three places: the deck with the new goal's card drawn off it, the stacks, the discard; the deck's back says the next goal; a card's face its gem, its words when lifted (28 October 2026, the owner and the PM)

Why: the owner, on S1's mockup after §159: the blank card, the deck, the stacks and the discard are still four things to
read at the hand's foot, and the deck's back says nothing (an ork mark on every one). A card battler's hand is three:
what is to come, what is played, what is done. The blank card is a goal to come; the deck is the goals to come. So
(this changes §116.2, §124.1, §144.2, §145.3, §145.8 and §149.3):
1. **The hand is three places**: at the left **the deck**, at the middle **the stacks** (the goals that ask the person,
   §121.2), at the right **the discard** (§145.4, §159). Nothing else lies in the hand.
2. **The new goal's card is drawn off the deck**: the deck's top card lies a little off it, face up, its face a **+**
   (the blank card, §116.2). Pressed, it grows into the field over the hand (one field, Enter sends, a picture pasted
   goes with it, the microphone, §124–§125); typing with nothing focused opens it too. Sent, the goal goes to the deck
   or the hand as its place says (§145.2). With no goal at all, the + card lies large in the pane's middle (§145.8).
   Addressed to a party (*→ Tech ×*, *@Tech*) as before.
3. **The deck's back says the next goal**: the top back carries the element of the first goal in line as a small seal
   on the one back's pattern (§149.3: one back still, the seal its only mark), and the moon when that goal waits for
   the reset (§136.5). With nothing in line, the deck is the + card alone.
4. **The deck pressed fans out in a row over the hand** (only a press; under the pointer a card leans, §149.1): first
   the + card, then the goals in line in the Orkmaster's order, each its element and name; a goal dragged moves in the
   line (§138.3), a goal pressed is picked (§145.5). Past about seven, the row's last card is *All · search*, opening the
   goals in line over the pane (§142) with a search. Esc or a press away closes the row.
5. **To main stays one step inside the discard**: the discard says *n ready for main*; pressed, it opens over the pane
   with **To main** (§159.2). Main is production: no act on it lies on a pile.
6. **A card's face is its gem; its words are on the lifted card** (§144.2 changed): a card that spends shows its share
   in the gem (*4%*) on its face, and its words (*about 4% of Claude's week*) where it is lifted with its answers
   (§104.5). Every card of the hand has one size; what it asks is on its lifted state (§104.8).
The owner's call.

## 161. The heads keep their old drawing: the races are told by their faces and colours on the 12 × 11 grid, the leaders and the griffin drawn the same way (28 October 2026, the owner)

Why: the owner, on orkUI 0.15.0's heads (§149.4, §155): *I do not like the new heads; bring the old ones back and make
another pass; the decision that they stand apart by their silhouette should be looked at again.* The 16 × 16 heads were
drawn to be read by their outlines (horns, antlers, wings out of the gear's outline), and lost the faces and the manner
of the heads the window had. So (this changes §148.7, §149.4 and §155.1–§155.3; §154 and §158's races by party stay):
1. **The heads keep their old drawing**: orkUI's 12 × 11 grid of role letters, 2 px a cell (24 × 22), 4 px at @2x
   (48 × 44), as they were before 0.15.0; the ork, the elf, the goblin, the gnome, the knight, the lich and the skeleton
   as they were. A race is told by its face, its colour and its detail, the tier by its gear, as before; **not by the
   silhouette**.
2. **The new heads are drawn in the same manner**: the griffin (Product's and Game design's members) and the six leaders'
   higher forms (the ork shaman, the elf dryad, the imp, the gnome fairy, the unicorn knight, the lich, §155.2), each a
   head of that grid whose mark (horns, antlers, wings, the horn) is drawn inside its 12 × 11 like the old heads'
   detail, never needing an outline of its own; the crown stays the Orkmaster's alone.
3. **A head is drawn at its own sizes**, 24 × 22 or 48 × 44, never between and never at 12 × 11 (§148.7's *a blot* holds:
   no head smaller than its own size); §151.3's squad heads at 24 px are these.
4. The 16 × 16 heads are not drawn by the window; a second pass at the heads, if the owner asks for one, starts from
   these.
The owner's call.

## 162. Product's party is the knights again, led by a golden unicorn knight with an angel's wings; the shaman without the war paint (28 October 2026, the owner)

Why: the owner, on orkUI 0.15.2's heads (§161): *the heads are good; the problem is the griffins.* A griffin among the
humanoid heads reads as an animal in a row of people; the knights were Product's race before §155.4, and every other
leader carries a mark at its sides (the shaman's horns, the dryad's antlers, the imp's wings, the fairy's wings) but the
unicorn knight, whose horn is one spike at its brow. So (this changes §155.2 and §155.4; §158.5's table reads so):
1. **Product's members, and a game's Game design's, are knights** (`knight`, as drawn), wearing their tier's gear as
   every head.
2. **Their leader is a golden unicorn knight with an angel's wings** (`unicorn`): the knight's helm in gold, one horn
   off the visor's brow, and white feathered wings at the head's sides, so every leader carries its mark at its sides.
   The gold is the knight's armour, never a signal's yellow (§53.5: at least 20 CIE76 from `alert` and `warning`).
3. **The griffin is no head of the window**: it is not drawn by orkUI's office look.
4. **The ork shaman without the war paint**: its face is the ork's, its marks its horns and braids, its skin the deeper
   green (§155.2).
The owner's call.

## 163. A card is neutral on the warm table: the cards' own fill and frame, soft greys a step lighter (28 October 2026, the owner)

Why: a card on the table differed from it by its fill only 1.17:1 (`raised` on `table`), so the cards read as windows,
not things on a table. Three ways were laid side by side on one window (orkUI's `docs/compare/cards.html`): A, the table
warm and the cards soft; B, the table soft and the cards warm; C, as it was with the card a step lighter. The owner took
A. So (this makes §115, §148.1 and §149.3 precise):
1. **The cards have their own fill and frame**, two tokens of orkUI's (`card`, `card-frame`): neutral soft greys a step
   lighter than the half-tint `raised` (about `#2e2e2e`, its frame about `#3c3c3c`; measured in orkUI). Every card is
   drawn on them: a map's cards, the hand's cards, the lifted card, the backs and the deck's + card. The grounds, the
   panels, the tabs and the table stay the half-tint warm.
2. **What lies on a card holds its measures on the card's fill**: text AA (the faint ink a step lighter where it falls
   short), every sign, element and signal 3:1, every head's edge 3:1 (the few head colours that fall short a step lighter,
   as 0.12.0 did), the card's chroma below every element's (its greyness is no signal).
3. In orkUI's 0.15.x, with §162's heads, then copied here once (spec 96).
The owner's call.

## 164. The leaders have names of their own, said only where a party is made and edited (28 October 2026, the owner)

Why: the owner: the leaders' higher forms (§155, §162) are characters; a name of their own gives each a little life where
the person chooses its party, without noise where the work is read. §154.4 and §158.7 say a role's name and never a race
in the interface; these names are the one place where a race's word is said. So (this makes §151.5 precise and is the
one exception to §154.4 and §158.7):
1. **The names**: the Orkmaster stays *Orkmaster*; Product's leader *Angel Invest Knight*, a game's Game design's
   *Dungeon Master Knight*; Tech's *Sh.man*; Design's *Pixel-Perfect Dryad*, a game's Art's *Sprite Dryad*; Run's *Uptime
   Imp*, a game's LiveOps' *Event Imp*; Marketing's *Growth Hack Gnome*; Release's *Release Night King*.
2. **Said only in the one place of the parties** (§151.5), on the leader's row of the party picked at the right, beside
   its role (*Sh.man · Architect*). Everywhere else (the tabs, the cards, the popovers, the words of the cards) a leader
   is its role, as before.
3. They are words of the interface, written where the face writes them; code, keys and files keep their names.
The owner's call.

## 165. Light cards are for later: §163's neutral cards stay; a light card asks its own heads and a second palette (28 October 2026, the owner)

Why: a fourth way was drawn beside §163's (orkUI's `docs/compare/cards.html`, D): the cards the colour of today's ink
(`#dedbd6`), their words dark. It reads as cards on a table most of all (12.8:1 against it, §163's A 1.30:1), but the
heads are drawn for dark grounds (25 of their 32 colours fall under 3:1 on the light card, the elf's and the dryad's faces
1.02:1), and the elements and signals need darker kin on it. So:
1. **§163 stays**: the cards neutral on the warm table.
2. **Light cards are a later pass** of orkUI's, apart from the slices: a set of heads that stand on a light ground, the
   elements and signals' kin for it, and both grounds measured; then the owner looks again.
The owner's call.

## 166. The cards a hint cold: a slate grey on the warm table (28 October 2026, the owner)

Why: the owner, after §163's neutral cards: *let's try them colder.* Two cool tints of A were laid beside it at the same
lightness (orkUI's `docs/compare/cards.html`): A1, a hint cold (CIELAB chroma about 3, hue about 250), and A2, cold
(chroma about 6). Both hold every measure; A2 reads as a colour of its own across a whole screen, A1 as paper. So (this
makes §163.1 precise):
1. **The cards' fill is a slate grey**: `card` `#2a2e31`, `card-frame` `#383d41` (chroma about 3, hue about 250, almost
   opposite the warm table's), the backs' greys with them; every measure of §163.2 held on it (the faint ink 4.54, the
   heads' edges 3.03 at least, at least 20 CIE76 from `ice` and `void`).
2. In orkUI 0.15.4, then copied here (spec 96).
The owner's call.

## 167. The cards read as a card game's, a goal lies as a cascade in its party's lane, the hand lies under the lanes, the deck goes into the first lane (28 October 2026, the owner and the PM)

Why: the owner, after five rounds of `docs/mockups/cards/` (drawn on a card game's anatomy at the owner's ask): the
cards' face said too little at a glance and too much at once (a bright sign on black, a head on every card, the cost
and the element fighting the name), a goal's tasks were scattered over its lane, and the hand read apart from the
table. And the deck hid what waits behind a back. So (this changes §104.2 for the Board's and the hand's cards, §136.1's
hourglass, §144.1's members' heads and §144.2's cost place, §145.2, §153.5's lifted question, §160.1–§160.4, and
§2.1's tab name):
1. **A card's face** (the Board's tasks, the hand's cards, a question's choices): **its header** the goal's element at
   the left, bare (no frame), then its name left-aligned, up to three lines; **its window** low (its sign's height and a
   little room, the card's own fill, a hairline), one sign at the signs' big size, toned down: on the Board the task's
   type; in the hand the action's sign (the alert, the question, *done*) with the head of who asks (its leader) small in
   its corner; a choice of a look its preview; **its label row** the stage's small sign and word on the Board, the party's
   name in the hand, and at its right the gem when it spends; **its foot** in the hand the question or the line; on the
   Board none (the goal's strip says it). **No head on a Board's card**: who works is on its back and in its party's
   header. Other maps' cards (System, the screens, the loop, the assets) keep §104.2 until their slices.
2. **A question is chosen as a card** (*Choose a card*): lifted, its choices are dealt over the pane in a row under the
   question, the leader's pick raised with its why at its foot; a choice that spends more carries its gem; *Other…* is a
   blank card with **+**; *Let <leader> decide* a quiet button under the row; a stack's questions follow one a press as
   before (§153.5–§153.6).
3. **orkUI draws the sign `question`** (0.15.5, a question mark on the signs' grid), never `target`.
4. **A goal on the Board is a cascade in its party's lane**: a thin strip with its element and name, its tasks laid as
   a solitaire's cascade, the front one whole (a failed check first, then *Checking*, *Doing*, *Planning*), the others
   as strips of their name and stage's sign; no count, the strips say how many. Collapsed, but **the picked goal's
   cascade unfolds** into whole cards; a strip pressed lifts its task. The cascades of a lane in the hand's order; a goal
   in two lanes at once has its strip in both, lit together when picked.
5. **No deck**: the goals in line lie on the table, the first lane's last cascade *In line*, in the Orkmaster's order, a
   goal dragged to move it, the moon on one that waits for the reset. **A goal is on the table, in the hand or in the
   discard**; *Later, by itself* lays it in line. Under the first lane the hand holds the **+** card (a new goal) and the
   Orkmaster's stacks.
6. **The first tab is the project's**: its name with the crowned head (*Party game*); its lane holds what is the whole
   project's (routing, Talk, decisions, joining, the line). The Orkmaster is named where it speaks (*through the
   Orkmaster*, its cards).
7. **The hand lies under the lanes**: a goal's stack under the lane of who asks (a failure its party's, a leader's
   question its party's; what is the whole goal's, the route, Talk of several leaders, the decision, a fork, under the
   first); a goal's cards from one party one stack; two goals under one lane fan within its width, the urgent in front,
   those behind their edge and element only, rising on hover or a press; a picked goal's stacks lit alike; **the discard
   under the tabs' end** (the limits' chips and *Stop all*: the owner's, after the mockup), whatever parties there are. Every lane one width, a card and a quarter (room for a fan); when they don't fit they narrow
   to a card's width and the fans tighten, never a sideways scroll. Urgency reads by the frame's colour and what is in
   front.
8. **The hand shows its cards' upper part** (the header and the window); the rest lies under the window's edge, a card
   rising whole on hover, on focus or a tap, a press lifting it.
9. **At the narrow width** the hand is a free row in the lanes' order (the first lane's first, the discard last); a goal
   on the Board one token with its stack's edges, a press opening its tasks.
The owner's call.

## 168. The cards' names in the body face; the + card turned and green; a stack and a goal's tasks as a fan (28 October 2026, the owner)

Why: the owner, after spec 101's window: a goal's name is a person's words (CLAUDE.md: the pixel face is for headings
and buttons); the + card should read as the one to play; and cards laid straight one on another read as a ticket board,
not as cards. So (this makes §167.1, §167.4, §167.5 and §167.7 precise):
1. **A card's name is in the body face** (bold), never the pixel face; the pixel face keeps the labels (the stage, the
   party) and the buttons.
2. **The + card is turned a little**, its **+** and its frame the action's green; it lies behind the first lane's stacks.
3. **A hand card's head lies over its sign**, on its lower right corner, the two read as one figure (the mockup's).
4. **Always a fan, never card on card**: a stack's cards behind the front one turned a few degrees (2° to 4°) and moved
   a little aside, by turns left and right, three at most seen, a fixed turn a card (no shake on a redraw); a hover
   opens it a little wider; still under reduced motion. **On the Board** a goal's tasks behind its front card lie the
   same way, turned less (1° to 3°), showing their edge with the stage's sign and the element only; their names on a
   hover, which opens the fan, and on the picked goal, which unfolds as before. No strip of names (§167.4's strips go).
The owner's call.

## 169. S1 and S2b taken; seven seats; a risky step waits; the first start opens the parties' place; a fact can be added (28 October 2026, the owner)

Why: the owner's answers to the lead's questions after specs 98–101. So:
1. **S1 (the window: the table and the hand, spec 98, spec 101) and S2b (a goal's way as cards, spec 100) are taken** (§129):
   S3 may be specified.
2. **A party has at most seven seats in all** (its leader and six), at most five who do and two who check (§151.1 made
   exact): no craft's roles reach more today (the largest, Art, a leader, five who do and one who checks).
3. **A later step of high risk waits for the person's Start** (spec 99 §9): the route's *Start* covers its steps of
   ordinary risk; one of **high** risk (the plan's `risk`) is laid in the hand as the `start` card of that step, with its cost.
4. **The first start opens the one place of the parties at once** (spec 95 §7: no tour, no button before it), over the
   empty Board as soon as the project is read; ← or Esc leaves it to the empty Board, which keeps *Choose the parties*.
5. **The hint under a fork's banner** stays: *The side you pick stands; the other leaders write their sections again*.
6. **A fact can be added** to what a leader keeps of the project, beside correcting and forgetting one (§153.4).
7. **Release's leader on Seasoned, the Live crafts proposed Standard** (spec 99 A's picks) stay.
The owner's call.

## 170. orkUI 0.16 taken: the goal types' big signs in two tones, a pick's suits the asking party's race's tool (28 October 2026, the owner)

Why: the owner made orkUI 0.16.0 (its CHANGELOG): the signs at 28 px were coarse, and the choices of a pick wanted telling apart by
their shape, with the craft of the race said with a joke. So (this makes §167.1–§167.2 precise):
1. **A goal type's sign at 28 px** is orkUI's 14 × 14 drawing in two tones (the silhouette in the text's colour, its light over it);
   the states', the media signs, `sword`, `shield` and `question` keep their 7 × 7. *New feature*'s three kinds have their own
   signs: the wand (`feature`), the compass (`shaped-feature`), the shoe (`flow-feature`: `steps`).
2. **A choice's card wears its suit**: the asking party's race's tool (orks a drum, elves a bow, goblins a pick, gnomes a bell,
   knights a map, skeletons an hourglass), its four variants by the choice's place; a preview or a fork's side's head in its place
   where there is one.
The owner's call.

## 171. S3's faces as the mockup drew them; a task card's every kind in a two-tone drawing (29 October 2026, the owner)

Why: the owner's yes on `docs/mockups/s3/` (the other maps and picking on them), and *use the new pictures for the tasks' cards*. So:
1. **S3's faces are built as `docs/mockups/s3/` draws them** (spec 102 §5–§6): every map's cards wear §167.1's face (System's parts
   too: the path as the name, its sign in the window, the layer's word in the label row); a card that changed since its leader's
   last call carries the gem *new*; a card no goal changed carries no element; the map's name (*Screens*, *Loop*, …) where a thing
   opened over it says where it came from (*← Screens · Lobby*), the pane's title keeping its two axes (spec 95 §1.3: *The whole
   project · through Design*).
2. **A task card's window is always a two-tone drawing** (§170.1): every task kind maps to one of orkUI's twenty-five big
   drawings (docs a scroll, text a quill, sound and music a lyre, accessibility the shoe, security the seal, art direction the
   crown, animation a picture); a 7 × 7 never stands at 28 px on a card.
The owner's call.

## 172. Product's map is an opportunity solution tree, its opportunities the users' jobs to be done; the pains along the journey are Design's (29 October 2026, the owner and the PM)

Why: the owner: Product's map was meant to be the users' jobs to be done, not the pains met along the journey (those fit Design's
screens); and asked the PM to pick a discovery framework for the case. The PM's pick: Teresa Torres' opportunity solution tree,
its opportunities written as jobs to be done: its lowest tier already exists (the goals on the Board), so Product sees which goal
serves which job and which job none serves; a job map (Ulwick's steps) alone links to no goal, a Lean Canvas is still and of the
business, a story map would be Design's screens again. So (this changes §112.7's and §134.2's *Product looks at the same map*):
1. **Product's map is the tree**: at its top **the outcome** (one or two numbers the project means to move, said plainly); under it
   **the opportunities**, three to seven, each a job *When <situation>, I want to <motive>, so I can <outcome>* with its segment;
   under each **the goals that serve it** (the Board's, by their slugs) and under a goal **its experiments** (the goals of type
   *Try an experiment* that test it). A job no goal serves is seen empty.
2. **Kept as the loop is** (§112.8): the person and Product's leader keep it; its first proposal one call of Product's leader with
   no tools on the cheaper tier, given the project's files chosen by code and the project's answers (§153: whom it is for, what
   hurts them, what it leaves out); its text in Product's every call (§156.1); a goal written from Product's tab is offered under a
   job.
3. **The pains along the journey are Design's**: pinned to its screens and steps, the segment a filter over Design's map.
The owner's call.

## 173. A task card shows a drawing of the race that does it (29 October 2026, the owner)

Why: the owner: a task's picture should follow the race that does it first (the knights a map, the gnomes rockets and
firecrackers), and orkUI 0.16 already leans each party's things on its race and gives each race its tool. So (this makes §170.1
and §171.2 precise):
1. **A task card's window draws its kind's drawing when the race that does it** (the doer's head, its party's race) **has that
   drawing**: the orks the wand, the beetle, the broom, the anvil, the compass, the flask, the scroll; the elves the mirror, the gem,
   the seal, the shoe, the lyre; the goblins the gauge, the scales, the fork; the gnomes the rocket, the signpost, the letter, the
   quill, the stall; the knights the die, the castle, the crown, the heart, the fork; the undead the chest.
2. **Else it draws that race's tool** (the drum, the bow, the pick, the bell, the map, the hourglass), its variant by the task's kind,
   so one kind is one variant.
3. **A drawing for every kind in every race's way** (about 180) **is for later**, the owner's: until then 1 and 2 hold.
The owner's call.


## 174. The phone's app a native frame: upright it is the hand with the top card's context above, on its side the table without the hand; push through a relay that reads nothing, an answer from the notification, widgets (29 October 2026, the owner)

Why: the owner: the phone should be a real app (Capacitor), with notifications and widgets; upright its first screen the
answers to the cards and a new goal, the Board by parties a screen of its own on its side, with no hand; and the top card's
question with more of its context, at the screen's top. §150 already keeps upright for the quick answer and the side for the
table, and §128 makes the phone's app a frame round the one page, as `vscode/` is the desktop's; but in an installed web app
an iPhone neither locks a screen's orientation nor answers from a notification, and has no widget. A native frame can, and
draws nothing of the Board itself. A native app's push goes through Apple's and Google's services (APNs, FCM), whose keys
cannot be handed to every person's computer, so it needs a server of ours, which spec 42 §3 did without. So (this changes
§150.2–§150.3 and spec 42 §3.1's words, and makes §128.1, §145 and spec 94 §3–§4 precise):
1. **Upright, the narrow width's first screen is the hand** (the stack of cards, one question a card, §153.6; the blank card
   with the microphone at its foot), and **above it the top card's context**: whose question it is (its leader's head, its
   party), which goal (its element, its type's sign, its short name), why it is asked (the question's `why`, one line), what
   the leader recommends and that work waits on it (`blocks`), never a count. A press on it opens the goal's way over the
   pane (§142). It is the table's what and why for the one card in hand: §145's two parts, the table's a slice. With nothing
   in the hand the blank card takes the screen.
2. **The table at the narrow width is its own screen**, opened from the hand's top (*The Board*); in the native app that
   press turns the screen to its side (the one screen that asks an orientation, so a phone with its rotation locked still
   reaches the table); in a browser it opens upright, spec 94 §3's tokens.
3. **On its side a phone is the table without the hand** (a low window, §150.2, under `pointer: coarse`): no fan, no blank
   card; a stop's sign on a head opens its card over the table, answered there, so a stop is never a reason to turn the
   phone back. A low window with a fine pointer (a laptop's split screen) keeps §150.2's fan. A goal is written upright.
4. **The native frame** (Capacitor, `mobile/`): pairing by the QR with the computer's certificate pinned from it, the page
   carried in the app (never loaded from the computer), push, the arrival from a notification, the widgets' data, the
   orientation. Like `vscode/` it draws nothing of the Board; the PWA stays for whoever does not install the app.
5. **Push through the relay**, a server of ours that reads nothing: it takes a Web Push request as a push service does (the
   message sealed to the device, RFC 8291; signed by the paired computer, VAPID), checks the signature against the key the
   device registered, and passes the sealed bytes to APNs or FCM; the phone opens them (on iOS a Notification Service
   Extension). It keeps no message and logs none; the computer's `gui/web_push.py` is unchanged, the device's endpoint is the
   relay's. What goes and when stays the computer's (spec 42 §3.1). Settings say plainly that notifications to the app go
   through Orkboard's relay, sealed.
6. **A notification says the card**: its leader and party, the goal's short name and the question's first line, and its
   two actions *Take the pick* (the leader's recommended answer, sent from the notification) and *Open*. The lock screen's
   previews are the phone's own setting. **No number anywhere**: no count in a notification's words, no badge on the app's
   icon (Android a dot), so spec 42 §3.1's *3 wait for your answer* goes.
7. **Widgets**, native (WidgetKit, Android's Glance), from the top card the app keeps: small, the leader's head, the goal's
   short name and the alert sign, else *New goal*; medium, the top card with *Take the pick* and *Open*; on the lock screen,
   *New goal* with the microphone. Never a count.
8. **When**: S5, after spec 94 holds on the owner's phone; iOS first, then Android. A Live Activity while Play runs is
   asked again later.
The owner's call.

## 175. The tree as drawn; the AI tools' limits move to the hand as its mana (29 October 2026, the owner)

Why: the owner's yes on Product's opportunity tree as `docs/mockups/s3/` draws it, and: *the limits should move down to the
hand and look more like mana: there is no room at the top* (with six or seven parties the tabs' end clipped its chips). The
cards already carry their cost as a battler's mana (§144.2), so the pool they draw from belongs beside them. So (this changes
§2.3's chips at the tabs' end, §107.1 and §144.2's *the limits' chips read as what is left to spend*):
1. **Product's map is the tree as the mockup draws it** (spec 102 §8.4): the face is built (H).
2. **The limits are the hand's mana**, under the tabs' end beside the discard: each AI tool a pool with its ink mark, filled by
   its share left (the signal's colour as it runs low), its words on hover and for a screen reader (*Claude Code: 62 % of the week
   left*); a press opens what used it over the pane, as the chips did. A card lifted that spends shows its gem's share taken out of
   its tool's pool. The tabs' end keeps **+** and **Stop all**.
3. Drawn in orkUI first (the pool's frame and fill, §127.3), then here; until orkUI draws it, the page's own layout with orkUI's tokens.
The owner's call.


## 176. The mana is blue, the potions lie flush right; the discard lies on the table; a lifted card is a card (29 October 2026, the owner)

Why: the owner's yes on `docs/mockups/mana/` (the potion, flush against the window's right edge, six tools in two rows of
three, each tool's mark in its own colour), and three more: *when the flask is full make the mana blue, a nod to it, only
not bright so it does not pull the eye*; *there is room at the right now: the discard could go onto the table, out of the
hand, and give the cards more room below*; *a lifted card should still have a card's shape, not a panel or a dialog: it
appears as a card and may cover the cards under it*. A pool coloured only when it runs low says nothing while it is fine;
a card game's discard lies on the table by its player's zone; and the cards are the window's one metaphor, so the card a
person reads and answers is a card too. So (this changes §175.2's *ink mark* and *beside the discard*, §167's and §145.4's
discard in the hand, spec 101 §4.4–§4.5, spec 96 §2.3's monochrome marks, and CLAUDE.md's frame line):
1. **A tool's pool is a potion** (a round bottle with a neck and a cork, orkUI's pixel grid), its liquid filled by its share
   left. **The liquid is the mana's blue while the tool has room**, a dim, desaturated blue near the muted ink's brightness
   (orkUI's new `--ork-mana`), the warning's colour at the warning's level and the danger's at the danger's (`levelOf`, the
   levels the chips had). Blue here is a signal (*there is room to spend*), so it keeps orkUI's rule that colour is a signal (spec 40).
2. **The potions lie flush against the window's right edge** at the hand's end: up to three in a row, four to six in two
   rows of three; **each tool's mark above its potion in its own colour** (`marks/harness-<id>.png`: Claude's orange,
   Codex's green): the mark says who, the liquid how much. The share in words under it and for a screen reader; a press
   opens what used it over the pane, as the chips did. A lifted card that spends shows its share hatched off its tool's top.
3. **The discard lies on the table**, at its last column's foot, at the right, on every tab (on a party's tab the party's
   map ends above it); the hand keeps the + card, the stacks and the potions, and the width the discard had goes to the
   stacks. What the pile is and opens is §145.4's and §160.5's, unchanged. **A goal is on the table, in the hand or in the
   discard**, which now lies on the table.
4. **A lifted card is a card**: the hand card's frame and anatomy (element, name, the window with the action's sign and the
   asker's head, the party and the gem, the foot) at about twice the hand card's width, in its proportions, turned a degree
   or two as a card held up, its foot on the hand's line where its stack lies, over the cards beside it and the lanes'
   foot. What the panel held (the text, the answers, the cost's words, *Put it back*, a goal's way's own body) is the card's
   body between its window and its foot; a body longer than the card scrolls inside it, and the card never grows wider. At
   the narrow width it is the screen's width less the gutters, rising from the hand.
5. Drawn in orkUI first (the potion and `--ork-mana`, §127.3), then here (spec 104).
The owner's call.

## 177. The default tool is the potion in the frame, and work goes on with the next when it runs dry; a goal is sent to main through a portal (29 October 2026, the owner)

Why: the owner: *mark the default harness's potion, and when the default runs out every harness moves on to the next, so
the mark is seen to move*; and *make merging a portal: the cards are dropped into a portal that appears, at most two, main
or dev and a person's own branch*. The fear of a person on a subscription is that the work stops when its limit does, and
today it does: a failed tool only offers *Switch* (`tool_errors.report`). And the merge into main is the window's weightiest
act, done by a link in the discard's view, the one act no card plays. So (this changes §160.5's *To main* in the discard's
view, §175.2 and §176.2, and spec 98 §2.3's *Switch* as the only way on):
1. **The default tool's potion is framed**, a hotbar's chosen slot, in the ink (a choice, not a signal). **The frame follows
   the open tab**: on the project's tab the machine's main tool (`machine.main_tool`), on a party's tab that party's tool.
   The potions' order left to right is the order work moves on in.
2. **When the default tool runs dry** (at its reserve where it has one, Claude's), the work moves on to the next potion
   that has room **between tasks, never inside one**; the frame slides to it and the Orkmaster says it in one line (*Claude
   Code is out until Thu 18:00: the work goes on with Codex*). A party or a role set to its own tool on purpose (spec 49)
   waits and says what it waits for instead of moving on. **Only between subscriptions** (`billing: "subscription"`).
3. **When every subscription is dry**, the Orkmaster asks with a card in the hand under the first lane: *every
   subscription is out until <the soonest reset>; go on with <the tool paid by its API> at about <its cost> a task, or
   wait*, its answers **Go on, paid** and **Wait for <the reset>**; nothing is spent by a tool paid per token without that
   yes, and the yes holds until the next reset, said on the card.
4. **A goal is sent to main through a portal**: pressing (or starting to drag) a goal in the discard that is ready for main
   opens the portal on the table's right, above the discard; a goal dropped or pressed into it is merged into main. The
   portal says before it acts what goes (*Into main: Lobby, and Reconnect it stands on*), and is **sealed** with its reason
   while the gate holds the goal (a check red, a conflict). Pressing works as dragging does, and the keyboard too. The first
   time, the portal shimmers once with the line *Drag a goal done into the portal to send it to main*.
5. **One portal for now, main's.** A second, a person's own branch, comes with more people on one project.
6. A goal goes to main on its own: its commits from dev, with the goals it stands on that main lacks (said on the portal),
   so the per-goal merge (spec 102's *To main merges dev whole*) is built with it.
7. Drawn first (`docs/mockups/portals/`), built after the owner's yes.
8. Later the same day, the owner: **the portal is round and magical, never a door**; and **four tools stand two rows of
   two** (five and six two rows of three; this makes §176.2 precise).
9. The owner's yes on the mockup (`docs/mockups/portals/`, v2), with **the portal purple**: its light orkUI's new
   `--ork-portal`, a violet clearly apart from the void element's, a signal (*a goal can be played here*); drawn in orkUI
   first (`.ork-portal`, 0.18.0), then here (spec 105).
10. **The reserve is the person's**: at the Main tool's reserve only the work the Board started by itself moves on; a plan
   the person started, and a keeper's step, stay on the Main tool and may spend the reserve, and move on only when a window
   is spent (this makes 2 precise).
The owner's call.

## 178. The phone is the page first, then the native frame; upright the hand with the potions in its top row; the Board only on its side, with the discard and the portal (29 October 2026, the owner)

Why: read against §175–§177, spec 103 was written before the mana, the frame, the Orkmaster's line, the card *Go on paid?*
and the portal, and the phone's own face (`pwa/board-app.js`, `pwa/shell-*.js`) knows none of them; spec 94's B–E, which
make the phone a frame round the one page, are not built, while the page's narrow width already draws all of them. The
owner's answers to the questions sent with `docs/mockups/phone/` (v1). So (this changes §174.1–§174.3, spec 103 §1.4 and §2,
spec 94 §3.2 for a phone, and makes spec 105 As built C's *the phone has no card for it* go):
1. **Spec 94 B–E first**, then spec 103: the phone becomes the page at the narrow width, and its own face is removed; it is
   not patched with what the desktop gained. What the phone lacks today (`mana` in its snapshot, the paid card, the potions'
   and the portal's files in its cache) comes with the page.
2. **Upright, the potions stand in one row at the top**, left of *The Board*, at orkUI's `.small`, over the top card's
   context; the default framed. The foot is the blank card alone. With nothing in the hand they keep that row.
3. **The frame follows the work**, not a tab, on the hand's screen: `town.mana.now` (the Main tool when it has room); on the
   Board's screen it follows the open tab as on the desktop (§177.1).
4. **The Orkmaster's line** is a strip at the screen's top, over the context, until put away (spec 105 D.3).
5. **Go on paid?** is a card in the hand like the others: its context the Orkmaster's crowned head and the project's name,
   no goal and no pick, *The work waits for your answer*; its row counts in `needs_you` and is pushed; its notification has
   *Open* only, never *Take the pick*: money is spent from the card, on the screen.
6. **One stack in the hand**, in Needs you's order: a goal's cards together, the next goal's under them; its depth its edges.
7. **The Board on a phone only on its side**: no upright Board under `pointer: coarse`. *The Board* turns the phone in the
   native app; in a browser, where nothing turns it, it says *Turn the phone on its side to see the Board*. On its side the
   table keeps **the discard and the portal** (§176.3, §177.4: the discard lies on the table now), without the hand. A narrow
   window with a fine pointer (a desktop's, VS Code's side bar) keeps spec 94 §3's upright table.
8. **Merging into main from the phone is allowed** (the portal, `ideas.to_main`; spec 37 §8's *no git from the phone* keeps
   the Files pane's git and the terminal off the phone, not the Board's own merge).
The owner's call.

## 179. Upright the tools are their marks and shares, as tall as *The Board*; on its side the Board's foot is the goals' legend (29 October 2026, the owner)

Why: the owner on `docs/mockups/phone/` v3: the potions' row should be no taller than *The Board*, the bottles simplified or
gone; and on its side, *since there are no cards in the hand at the bottom now, show the goals' legend: a sign, what goal it
is*. A phone on its side shows the goals as tokens a lane wide (§143.4), whose element and sign say nothing without a name.
So (this changes §178.2 and spec 103 §1.2.5 and §2.1; the desktop's potions, §176, are unchanged):
1. **Upright, each AI tool is its mark with its share under it** (*62%*, the warning's and the danger's colour as it runs
   low, `levelOf`), no bottle, in one row at the top left of *The Board*, each a 44 px target, the row no taller than *The
   Board*; the default framed (§177.1, §178.3), its words as the potion's.
2. **On its side the table's foot is the goals' legend**, where the hand was: each goal on the table its element, its type's
   sign and its short name, in the lanes' order, one row that scrolls sideways if it must; a press picks the goal (§145.5) and
   lights its cards.
3. Drawn in `docs/mockups/phone/` v4.
4. Later the same day, the owner: **on its side a token is the task's type's sign in its goal's element's colour** (as the
   desktop's map cards tone a window's sign, spec 101), and **the legend says the same**: each goal its type's sign in its
   element's colour, then its short name. So the colour says which goal, the sign what the task is; a task that asks keeps the
   alert's frame (the token's edge), a goal waiting for the reset the moon beside its name in the legend.
The owner's call.

## 180. The phone is the hand alone: no Board on it for now; the portal is a card of the hand; the top card narrower over a fan; New goal the green deck under the thumb; **…** for the rest (29 October 2026, the owner)

Why: the owner asked, as product, whether a phone needs the Board at all. The phone is the quick answer (§150); on the Board
a phone can do two things, answer a stop and send a goal to main, and both can lie in the hand. The Board on its side costs
a layout of its own, the frame's turning and a browser's *turn the phone*, for a look the desktop already gives. The
owner's yes on `docs/mockups/phone/portal.html` and `docs/mockups/phone/hand.html` (v1). So (this changes §174.2–§174.3,
§178.7, §179.2–§179.4 and spec 103 §1.4 and §2; the desktop is unchanged):
1. **No Board on a phone for now** (under `pointer: coarse`, upright or on its side): spec 103 B is not built; on its side
   a phone shows the hand as upright. Asked again after the owner has lived with the phone a week.
2. **A goal ready for main is a card of the hand**, Release's (the lich asks): its context says what is done and that its
   checks are green; **the portal lies on the card** with its line (*Into main: Lobby, and Reconnect it stands on*); a press
   on the portal sends it (`ideas.to_main`); sealed with its reason as on the desktop (spec 105 F); *Later* puts it back
   in the discard. The first time the portal shimmers and says *Tap the portal to send it to main*.
3. **The top card is about a quarter narrower than the screen** (264 of 390 px) and a little shorter, turned a degree;
   **the rest of the hand lies in a fan under it**, their heads showing from under the screen's foot (element and name); a
   press on one lifts it to the top. One card left: no fan.
4. **New goal is the green deck under the thumb** (the old phone's button, spec 50 §6.7, a little larger): bottom right,
   over everything; a press opens the field over the keyboard with the microphone in it. With nothing in the hand: the
   line *Nothing waits for you.* and the deck.
5. **The top row's *The Board* becomes **…***: Stop all, the project and the projects' switcher, Settings.
6. Later the same day, the owner: **one goal a screen**, not a fan of every card: the top card is that goal's, under it only
   its other cards as edges (its depth, no count). **Arrows ← → at the top** switch to the previous or next goal in Needs
   you's order (a sideways swipe on the card too, never from the screen's edge); *Go on paid?*, a project question and each
   goal ready for main are entries of their own. **On an arrow the neighbour's leader head and its goal's element**, never a
   number (the owner chose this over a count of what waits beyond it, which would break §145.3 and §174.1). Answering a
   goal's last card moves to the next goal. This replaces 3's fan.
7. **A *Spec* button under the context** opens the goal's way on its Spec tab; while no spec is written it says *The spec is
   written after your answers* and opens its questions.
The owner's call.

## 181. A quick question is asked, not played: one line on the open tab, answered once by whom the tab looks through, reading only; a question that hides work becomes a goal by one press (29 October 2026, the owner and the PM)

Why: the owner, as product: *what if I have no idea and no task, only a quick question about the project; how is it
played (not as a card), and is it worth it?* A card is what the person decides or plays (§104.0, §167): it has a phase,
lies on the table, in the hand or in the discard and spends mana. A question has none of that: it changes nothing and
needs no life. Played as a card it would fill the hand with one-off things and blur *the hand is what you decide*. Not
having it sends the person to a terminal for what only Orkboard knows (where a goal is, why a party chose its way, what was
decided), and every question asked is a sign of what the table does not show by itself. So (spec 106):
1. **A question is a read, not a card**: no phase, never in the hand or the discard, no count of what waits; **its
   answer never changes anything** (the call has no tools and reads no file).
2. **It is asked through whose eyes the tab looks** (§104.0): on the Orkmaster's tab the Orkmaster answers *what and who*
   (where a goal is, who does it, why it is in that place in line), from the Board as text; on a party's tab its leader
   answers *how and why*, from its map as text (§156.1) and its party's goals. One line at the top of the pane, *Ask the
   Orkmaster…* or *Ask the <its leader's role>…* (§164.2: a leader is its role there); never a chat, a column or a drawer.
3. **One question at a time, one answer**: the answer lies under the line on its own tab, with the leader's head and up to
   four sources (a decision, a goal, a part of the map); × or a new question puts it away. No history.
4. **One call on the cheaper tier** (as Talk's round), no tools, its cost in the asking party's ledger (the Orkmaster's in
   the Board's own), refused in plain words as a talk is (the demo, a spent window, one already being answered); Stop all
   stops it.
5. **A question that hides work becomes a goal by one press**: when the answer names a goal it suggests, ***Make it a
   goal*** under it opens the new goal's field with that line written, addressed to the tab's party as the field always
   is; the person sends it or not.
6. **Only what Orkboard knows**: a question about the code at large is Claude Code's (beside it in VS Code); the call is
   told to say so in a line rather than guess.
7. **Measured from the first day**: each question (its party, its words cut short, its cost, whether it answered) and
   each *Make it a goal*; after a week of use, how many were asked, how many became goals and which repeat. A question
   that repeats is work for the table, not for the answer. If few are asked and none become goals, the line goes.
8. **The desktop only for now**; the phone is asked again with §180.1.
The owner's call.

## 182. A gate that cannot run is not red; the logs say the whole day; twelve looks of the owner's day (29 October 2026, the owner)

Why: the owner, after a day on a Node game, *errors all the time, I could not take one card to its end*, with the day's
logs and twelve notes on the window. The logs: every result came red from `sh: vitest: command not found` (a folder never
installed, a task that may not install), and was sent back five times with the line the face wrote. Spec 107 builds it.
1. **A gate that could not run is not red** (spec 107 A): a command not found, a package not installed, says so in words;
   it is never sent to the session (it cannot install), and Review offers **Install and test again** (Orkboard installs
   in the main checkout by the folder's lock, on the person's press) or **Test again**. A task that changed only documents
   runs no derived gate and waits for a look. A send back that changed nothing and failed the same way says so, and Fix
   opens empty.
2. **The logs say the whole day** (B): what was refused and what was shown red are events; the crashes, the server's own
   log, the project's gate and installs and the page's state go into the zip; a lower tier says why.
3. **A goal is dropped from its card** (D): **…** on a goal's cards, *Drop this goal…*, asked in place.
4. **A goal sent lies in the Orkmaster's lane at once** (E); **New goal is never under another card** (M 2).
5. **The System fits the pane** (F), down to half its size, then it scrolls with its cues.
6. **A log one reads** (C): sections, the prompts folded, its end first, the line of what happened above it.
7. **What works moves** (G): spec 49 §11's *motion says what changed* gains *and what is alive*: an ork at work moves, the
   time it has worked ticks; nothing that waits moves.
8. **+ Party** says its word (H); not green: green is New goal's (§180.4).
9. **The game's loops** (N): loops in loops (core, session, meta), the currencies with what gives and takes them, the
   feeling of each step (MDA's eight) and its intensity, why a player comes back, and what the loop says by code.
10. **The project's name has a ▾** (H) that opens the projects; *Switch project* leaves the Orkmaster's **…** (the phone
    keeps it).
11. **Play** (I): its sheet, lost with `assets.css`, is back; the start screen shows the product's logo when the project has
    one, coming up in steps with a sweep and two blinks, a console's start; full screen.
12. **Save logs is a button by the mana** (J): orkUI's bug under its magnifier, with an optional line of what went wrong.
13. **@ in New goal** (K) offers the parties and the project's files; a party taken, it offers at once **what that party can
    do** (its goal types: the goal takes that type) and **what it already has** (its map's parts: screens, System's parts, the
    game's loops: they become the goal's marks), and *@mech* finds *New mechanic · Game design*: who, then what, then on what
    (the owner's second note).
14. **The crowned ork is Orkboard's mark** (L, §91): favicon, the phone's icons, the Dock, VS Code, onboarding; Orkline
    keeps its own.
15. **New goal's card is worth looking at** (M): a double green frame with pixel corners and a fine hatch, a sweep on hover,
    in orkUI's pieces; offered to orkUI as `.ork-deck.is-main`.
The owner's call.

## 183. A leader says no, and shows where it hurts: objections in Talk, concerns on every map (29 October 2026, the owner)

Why: the owner: *the agents must not agree to every decision of the person: Product really prioritises and says no, this
is not needed, because…; Tech says it makes the architecture worse. And not only the Architect: any leader looks at its
own map and lights the problems, in the design, accessibility, the game's loop or anything else.* Talk had `against` that
changed nothing; no map said where it hurt (§151.4's marks were left to S4 and never built). Spec 108 builds it.
1. **A leader's round in Talk gives a verdict**: go, doubt or no, with why and, when it can, a smaller or other goal that
   would serve. A no rests on a part, a goal in line or a fact; a no without one is not a no.
2. **The prompt says the leader is not there to agree**: each judges by what its party answers for (Product by value
   against the goals in line, which it is given; Tech by the architecture; Design by the people's way; Game design by the
   loop and its economy).
3. **A no is a card in the hand**: *Drop the goal*, *Do the smaller one*, *Not now* (Product's, after the goal it named),
   *Go on anyway*. The person still decides, but overrules out loud: the decision's entry names who was overruled and why.
4. **Every party's leader has concerns on its own map**: what is wrong or at risk in a part, why, what would fix it,
   *alert* or *note*, at most seven. Code gives it signals (System's coupling, cycles, size, churn without tests; the loop's
   findings; screens nothing leads to; pains piling on a screen); the leader judges, drops what does not matter and adds
   what it sees. Design looks at the pictures of the screens changed, so it can speak of contrast and touch targets.
5. **A concern is a mark on the map's card** (**!** for an alert, a dot for a note, the leader's small head), a strip
   with the counts and *Ask again*, the card's back with *Make it a goal* and *Not a problem*; a party's tab shows **!**
   when its map has an alert. A concern dismissed is not raised again unless its part changes.
6. **Looked at when the person opens the map** and it changed since a look a day old or more, or on *Ask again*; never for
   a party nobody opens; the cheaper tier.
7. **The word is *concern*** (`TERMS`), not *flag* nor *finding*.
8. **Measured**: how many concerns become goals or are dismissed; how often a no is overruled (more than four in five: the
   rule's words are softened).
9. **Later**: specialists' concerns on the same rails (§151.4), the phone.
The owner's call.

## 184. Each leader looks as a senior of its craft: the lenses measured against the field's frameworks (29 October 2026, the owner)

Why: the owner: *analyse every party leader's lens, compare it with the frameworks senior specialists use to review an
architecture, a product, its marketing and the other crafts, and adapt them to our window.* Spec 108's look asked every
leader one question, so what it said hung on the model, not on how the craft reviews its work; Art, Release and Marketing
had no hint of code at all. Spec 109 builds it (its §0 is the comparison, craft by craft).
1. **Each craft's lens is a known frame**: Tech by C4, ISO 25010 and hotspots; Design by Nielsen's heuristics and WCAG 2.2;
   Product by the opportunity solution tree, jobs to be done and RICE; Game design by MDA, its loops, an economy of sources
   and sinks, flow and retention; Art by an art bible, its pipeline and a budget; Release by DORA's keys, readiness and
   semver; Marketing by AARRR, ASO and positioning; Run by SRE; LiveOps by its calendar and KPIs.
2. **A frame is four to six *aspects*** (`TERMS`), each a name and a question; the leader's look judges by them and gives
   each concern its aspect; Talk's verdict judges by the same frame.
3. **Code grounds what it can** in each aspect (hotspots, instability, a screen with no error state or an image with no alt,
   an outcome with no number, a bet with no test, a spike in the loop, no first-day hook, mixed sizes, heavy or unused
   assets, a big or stale batch, reverts, no changelog, a store title past its limit, no way back, no way to share, no way
   to earn); a hint is not a verdict.
4. **The strip shows the aspects** as a row of chips, each in its state (an alert, a note, a hint code noticed, nothing
   wrong, not looked at yet), a press stepping through its cards; no count is drawn.
5. **No new pane, column, call or tier**: the look and Talk are spec 108's, given the frame.
6. **Not taken**: a RICE score per goal (numbers we do not have), player-type models (a survey), loudness and palettes by
   code, a full WCAG audit (a specialist's, later), DORA's time to restore (no incidents recorded).
7. **Later**: Run's map of services and SLOs, LiveOps' calendar; ADRs, positioning and design pillars as records.
8. **Measured**: concerns by aspect, made goals or dismissed.
The owner's call.

## 185. The table's end is always laid: the portal's ring of runes and the discard's place; the + card bears a seal of summoning (30 October 2026, the owner)

Why: the owner: *what if the discard and the portal showed even while idle (the discard's place in a dashed line, the portal as
runes round its edge)? The right of the table under Play and Stop all looks empty; not to make the window busier, only more
alive*; and *make the + card's pattern magical and fantasy, not just a pattern*. Today the table's last column is empty until
the first goal is done (`DiscardEnd` draws nothing, §145.9) and the portal appears from nowhere (§177.4), so the window's
weightiest place reads as a hole, then fills by surprise. A card game's places lie on its table before a card does, and a
place laid in advance makes the first card's landing an event. The hatch on the + card is a pattern of the office, the one
card the person plays every day. The owner's yes on the mockup (`docs/mockups/table-end/`), with the full seal. So (this
changes §145.9's *the discard when the first goal is done*, §177.4's *opens the portal*, and §182.4's hatch on the + card):
1. **One rule for what is idle: still and colourless.** A place at rest is drawn in the edge and the faint ink, never moves and
   cannot be pressed; colour and motion come only when there is something to do.
2. **The portal's place is a ring of runes** (orkUI's `.ork-portal-ring`, 192 × 192), on the table's right above the discard,
   on every tab, with *Main* over it in the faint ink. **Asleep** with nothing ready for main: eight runes on a dotted circle,
   grey. **A goal ready** wakes it once: the runes light one after another in the portal's violet, a quick step each, then the
   portal's eye opens in the ring (`is-waking`, the portal's `is-new`); it stays open, its runes violet (`is-open`, `is-taking`
   while a card is held over it). **Sealed**: the portal with its X and the runes grey again, so asleep (no portal) and sealed
   never read alike. What the portal says and does is §177.4's, unchanged.
3. **The discard's place** (orkUI's `.ork-card-place`) is a card's outline in pixel dashes, with *Discard* over it, from the
   start; the first goal done lands on it and covers it. Pressed it does nothing: there is nothing to open.
4. **The + card bears a seal of summoning** (orkUI's `.ork-sigil`): a circle, a band of eight runes and a star of two squares
   under the +, in the action's green at about a quarter's strength, so the + stays the one bright thing. The hatch goes. The
   frame, the corner brackets and the lean stay (§182.4). On hover the runes light once round the circle, clockwise from the top,
   where a band of light crossed it; the large card keeps the same seal; at 80 px a circle, a diamond and four ticks, no runes.
5. **The runes are orkUI's own**: twelve marks on a 5 × 7 grid that spell nothing and are read by no one, never a letter of a
   real alphabet (no arrow up, no Y on a stem, no lightning, no diamond on legs: shapes some wear as hate symbols). They are the
   table's one vocabulary of magic: a goal is summoned at the + and leaves through a ring in the same runes. A face draws them
   only where they mean nothing; giving them a meaning (a goal's mark, say) is a decision of its own.
6. **The narrow width draws neither place**: there the portal and the pile appear as they do today (§180).
7. **Reduced motion**: the ring opens at once and the seal's runes do not turn.
8. Drawn in orkUI first (0.19.0: `runes/`, `.ork-portal-ring`, `.ork-sigil`, `.ork-card-place`), then here (the table's end,
   `table/discard.js` and `table/portal.js`; the + card, `hand/pluscard.js` and `hand/hand.css`).
The owner's call.

## 186. A goal's element is a rune: five of the twelve, each tied to its colour; the + card and the portal hold the goal's rune (30 October 2026, the owner)

Why: the owner, after §185: *should the runes replace the elements' signs? Take the most different ones and tie them to the
colours; on the + card and on the portal the goal's rune could be gold, but decide yourself.* An element is the mark that tells
a party's goals apart (§63.4): its colour does most of the work, its shape repeats it for colour blindness and for the dim
state, and it is never named. A leaf, a flake, stones, a ring and a flame are every fantasy game's, and §69 already feared
that a flame reads *urgent* and a flake *frozen*; a rune means nothing, which is what a mark of *which goal* should be, and it
is ours. With the runes already on the table (§185), the goal's own rune can stand in the seal that summons it and in the
ring it leaves through. So (this changes §63.4's *a pixel symbol*, §185.5's *a face draws them only where they mean
nothing*, spec 50 §1.1's shapes, and orkUI's elements README):
1. **The five elements are five runes**, chosen as the most different of the twelve by their pixels and their silhouettes,
   at a like weight (10 to 15 pixels), so no goal looks louder than another: **meadow the tusks** (two shoots from the
   ground), **ice the key** (an icicle hanging), **dust the comb** (stones under a lintel), **void the eye** (the old empty ring,
   with its centre), **lava the wave** (a flow). The colours stay as they are; the names stay in the code and are never said.
2. **The seven others are decoration only**: the ring and the seal are written in them and never in an element's rune, so a
   rune on the table that is not in a goal's colour never means a goal.
3. **The ring and the seal each keep one place for the goal's rune**, at their top: the ring holds the rune of the goal chosen
   for main (pressed or dragged, §177.4), the seal holds the rune the new goal will be given (the one used least among the
   addressed party's open goals, as `idea_element` gives it; none on the Orkmaster's tab until a party is named).
4. **Not gold: the goal's own colour.** Gold would be a sixth colour of meaning beside five, too near dust's ochre and the
   alert's yellow, and the window's rule is that colour is a signal; the goal's rune in its own colour, at full strength among
   runes at a quarter's, is the one coloured mark in the seal and the ring and says *this goal* the way every card of it does.
   Sealed, it stands in the faint ink.
5. **The portal's ring is open whenever a goal is ready for main** (§185.2), so the place the goal's rune takes is waiting
   before it is pressed.
6. Drawn in orkUI first (0.20.0), then here; spec 110, built by the cheaper model and reviewed by the spec's author.
The owner's call.

## 187. A goal's rune from its summoning to main: one rune per stack, a flame at the stage at work, the rune chosen, the rite (30 October 2026, the owner)

Why: the owner, on the stacks: *a stack's name is doubled; let the name stand on top only, and below a burning rune stand at
the stage being worked on*; on the + card: *show the runes not yet on the Board, choose your next goal's rune, and when + is
pressed let the circle light from the chosen rune, then the same in the portal*; and *show the work on a card by a rune
lighting and dimming, not only by the turning signs*. Today a goal's rune stands three or four times on a stack of three (its
strip, every edge of its fan, the front card's header), a goal the Orkmaster reads repeats its name under its strip, a card
at work moves twice, and the element is given, never chosen. The owner's yes on `docs/mockups/runes-life/` and
`docs/mockups/window-runes/`. So (this changes §167.1's element on a card's header, §168.4's element on an edge, §63.4's and
§186.3's *given*, spec 107 §7's motion of a card at work):
1. **One rune per stack**: the strip over a goal's stack holds its rune and name; a card holds its task's name and no rune; an
   edge of the fan holds the stage's sign. **A card that is the goal itself** (the Orkmaster reading, routing or joining it,
   no tasks yet) has no strip: its header is the goal's, its rune and its whole name. The narrow width's token keeps its rune.
2. **The flame**: while a task is at work, the goal's rune takes the place of the stage's sign on its card (beside *Doing ·
   3 m*) and on its edge, and **glows**: its strength from about 62 % to full and back, in six steps over 2.4 s, no halo. It
   replaces the card's own motion of a task at work; the heads' step on the tabs stays, and the swords and shields stay signs of
   the stage. At most as many flames as orks at work. Under reduced motion the rune stands at full strength, still. The words
   (*at work*, the time) stay for a screen reader. It is the second thing in orkUI that moves by itself, after `.ork-busy`.
3. **The rune is chosen**: hovering the + card shows the runes the addressed party's open goals do not use, each in its colour,
   dim, in the seal's band, the decorative runes giving way (all five when all are used); the one it would be given stays at the
   top. **The choice is made in the field** the card grows into: a row of the five runes, 40 px each, the free ones bright, the
   used ones faint but possible, the default the one given today (§186.3); arrows and Tab move it; doing nothing keeps the rule.
   Not on the card: a 14 px rune on a card that leans under the pointer is too small a target and too near the press that opens
   the field.
4. **The rite**: when the goal is sent, the seal fills from its rune, clockwise, in the goal's own colour, eight steps in about
   640 ms, the + takes the colour for a moment, the card is drawn into its lane, and the colour leaves; when the goal goes to
   main, the same in the portal's ring, from its rune at the top, as the card goes in. Once each time; never under reduced
   motion; the goal's colour, not gold (§186.4).
5. Drawn in orkUI first, then here; spec 111.
The owner's call.

## 188. Release and Live wait at the portal: asleep in its corners, awake when there is something to do; each skeleton a check that blocks the way into main (30 October 2026, the owner)

Why: the owner: *the skeletons and the imps stand apart: they work after the release, or on it; take them out of the tabs, put
the skeletons between the discard and the portal and the imps above the portal*; then *hide them, or show them only when
needed*; *give each skeleton a check (unit tests, looks, regression)*; *and let the skeletons block the portal*. Release
takes a goal into main and Live runs what people use: their work comes after the work the tabs show, and the table's end is
already that road (§185). On a tab they take two lanes for little; at the portal they say *before main* and *after main*.
The owner's yes on `docs/mockups/window-runes/` (6). So (this changes §145's and CLAUDE.md's *the leaders' tabs* for these
crafts, §177.4's sealed X, and §159.3's *Release keeps its tab*):
1. **At the wide width, the Release party and the Run or LiveOps party are not tabs** and have no lanes. Release waits in the
   portal ring's **lower left corner** (before main), Live in its **upper right** (past the portal). The narrow width keeps them
   in the row of heads, as today.
2. **Asleep, each is its leader's head alone, grey and still** (the lich, the imp): a way into that party's view, pressed as a
   tab is. **Awake, in colour, with its members' heads**, its leader stepping while it works, an alert on it when it has one.
   Release wakes when a goal is ready for main, a task of its runs, or it asks; Live when a task of its runs, it asks, or it has
   an alert. Their cards that ask lie at the hand's right end, before the potions.
3. **Each skeleton is a check on the way into main**: the checks of the gate's `[gate.main]` (`orkcraft.toml`), each a name and a
   command, run on the goal's commits picked onto main in a trial worktree; with none written, two: *The merge* (the picks apply)
   and *Tests* (the gate's own command). Three skeletons at most; more checks are one skeleton's *and n more*.
4. **The skeletons block the portal**: when a goal is chosen for main they stand in front of the portal while their checks run
   (the portal still behind them), step aside into the lich's corner with a tick each as their checks pass, and **one whose check
   is red stays in front and blocks it**, its reason in the danger colour (*Sealed: Regression is red: 2 tests fail*). The X of a
   sealed portal is left out where a skeleton seals it; a reason no check owns (a goal not done, main behind its origin) keeps the
   X. Nothing goes to main while a skeleton stands in front.
5. A check judged by a model carries its tool's mark; a script spends no mana and has none. A skeleton's words are on hover and
   for a screen reader (*Regression: 2 tests fail*); no skeleton gets a job title (CLAUDE.md).
6. Drawn in orkUI first, then here; spec 111.
The owner's call.

## 189. A party's sword and shield on its tab: the tools its Does and its Checks run on (30 October 2026, the owner)

Why: the owner: *on the tabs, mark attack and defence for the leaders, or the whole party, with the harnesses' small icons, as
a card's elements of attack and defence.* A party's squad is two columns, **Does** under a sword and **Checks** under a shield
(§151.5), each on an AI tool; who does and who checks is the first thing about a party's quality (a check by another model is a
real one), and today it is read only in the party's editor. So:
1. **A tab's second line under the party's name**: the sword and the mark of the tool its Does run on, then the shield and the
   mark of the tool its Checks run on (`marks/harness-<id>-ink`), 14 px, in ink; **the open tab's in colour**. A column whose
   roles run on more than one tool shows the most used with a dot. **Lean** (no separate check) shows the shield faint with no
   mark. The project's tab shows the machine's main tool on both unless set.
2. **Hovering a potion marks the tabs' marks of that tool** (who drinks from it), and its words say them. When work moves on to
   the next tool (§177.2), the marks follow.
3. Words on hover and for a screen reader: *Does on Claude Code · Checks on Codex*. Not pressable (inside the tab's button):
   changed in the party's editor, as today. The narrow width's tabs are heads only: no marks.
4. Built with spec 111.
The owner's call.

## 190. The bar's marks: a banner for + Party, boards across Stop all; Play is a die in the hand, thrown while the preview starts (31 October 2026, the owner)

Why: the owner: *style the Party and Play buttons, as an invite to a guild or a raid, as long as it is clear what each does*;
then *the three as flags*; then *Play as a die, bigger, seen from above, by the potions: it shakes on hover, is thrown onto the
screen when pressed and rolls while Play loads, then the product's logo comes up as today*, *it lands on a green tick or a red
cross*, *lying askew*. A button's word says what it does (CLAUDE.md), so the words stay and the marks bring the world: *Start a
raid* would promise work where Play opens dev's preview, *Invite to guild* a person where + Party gathers orks. The owner's yes
on `docs/mockups/buttons/` and `docs/mockups/play-die/`. So (this changes spec 88's *Open the build* in the pane's head, and
spec 107 §9.2's logo shown while it starts):
1. **+ Party wears a banner** (a square cloth on a pole, a + cut out of it, unfurling once on hover); **Stop all wears two thick
   planks nailed across a pole** (boarded up), in the danger colour. Both are orkUI icons on the 7 × 7 grid; the words stay.
   A pennant for Play was weighed and not taken: on a pole it is ⚑ (*a goal in main*) at 14 px.
2. **Play is a die lying in the hand**, left of the potions, its word under it (*Play*, *Playing* while the preview is open),
   seen from above (its top face large, its front and right faces three cells), the card's greys with pips in the muted ink,
   turned by the lean token. **Hovered, it wobbles once** and stays lifted. The pane's head loses Play.
3. **Pressed when the preview is not running, it is thrown onto the pane** (black: the start screen) **and rolls the whole start**,
   the stage line under it; it **lands on its outcome**, askew: **a green tick** when the page answered, then the project's logo
   comes up as today (about a second) and the frame rises; **a red cross** when the start failed, then it tips over and today's
   failure takes its place. **Warm** (the preview already running): it wobbles in the hand and the frame opens at once; no
   throw, no logo. While the preview is open its pips glow; pressed again, the preview closes.
4. Under reduced motion: no wobble, no throw, no roll: today's start screen.
5. Drawn in orkUI first (the icons and `.ork-die`), then here; spec 112, built by the cheaper model.
6. Later the same day, the owner: **the bug under the glass (Save logs, §182.12) leaves the hand for the top right**, a quiet icon
   after *Stop all* at the tabs' end, its panel opening downward; the hand's right end is the die and the potions (the die's 69 px
   folded the first lane's fan at 1280 and overlapped the first potion at 390).
7. Later the same day, the owner: *the die should feel like a 3D object; now it looks like a tile*. **The die is a cube** (orkUI
   0.24.0): six faces in CSS 3D seen from above and before, lit from above so a face darkens as it turns away; its box 69 × 72
   (`big` 138 × 144), a face 18 cells. **Rolling, the cube tumbles** (quarter turns, rising on an edge); **landing, its face rolls
   in from the back and it drops** onto the pane; **hovered, it rocks on its edges**. The slot on the pane only drifts and the
   flight barely turns flat (a flat spin would turn the table under it). The faces, the tick and the cross, the words, the
   lean and reduced motion are as in 2–4.
The owner's call.

## 191. A project with no preview or no gate: the die sleeps, and with no gate there is no ring and no Release corner (31 October 2026, the owner)

Why: the owner: *a project like a wiki will not have the die, right? And will it have Release, the portal and the skeletons?*
Today Play is pressed before anyone knows there is nothing to open (*Nothing here yet*), so the die of §190 would be thrown and land
on its red cross for what is no failure; and the portal's ring of §185 lies on every project, asleep for ever on one whose results
merge into main itself (no gate: `idea_gate.same`). So (this makes §185.2, §188.1 and §190.3 precise):
1. **The page knows before the press whether the project has a preview** (`idea_shot.preview_of`: a command, a static
   `index.html`, a package script). **With none, the die sleeps**: grey and still, as Release and Live sleep in the ring's corners,
   its word *Play*, its words on hover *Nothing to play yet*; pressed, it opens today's *Nothing here yet* and how to give it one,
   without a throw. A wiki with a site to serve (`preview = "mkdocs serve"`) has a die that wakes as a game's does.
2. **With no gate there is no ring and no Release corner**: the table's end is the discard's place and pile alone. Live's corner
   needs the ring too: with no gate, Live stays a tab, as at the narrow width.
3. **The skeletons are any command**: a project whose way into main is not code says its own checks in `[gate.main]` (a wiki's
   *Links* and *Build*); with none, *The merge* and *Tests* as today (a project with no tests passes *Tests*, saying so).
4. Spec 113, built by the cheaper model.
The owner's call.

## 192. The mana in two windows: the liquid is the 5-hour window, the bottle the week; a tab says whether its party follows the default tool (31 October 2026, the owner)

Why: the owner: *let the 5-hour limit be the liquid's level in the mana's bottles and the weekly one the bottle's size*; and *a
party may be set to the default tool: if it is, its tab should not just draw Claude*. A potion today is one share, the window that
binds hardest, while a subscriber asks two things: *can I work now?* and *will I last until the reset?*. And a party that follows
the default moves on with it when it runs dry (§177.2), while a party set to a tool on purpose waits: two tabs drawn alike behave
apart. The owner's yes on `docs/mockups/mana-two/`. So (this changes §176.1's one share, §189.1's marks):
1. **The liquid is the tool's shortest window** (Claude's 5 hours), **the bottle its longest** (the week), in **four drawn sizes**,
   never scaled: the large (orkUI's potion today) above 60 % of the week left, the medium 30 to 60 %, the small 10 to 30 %, the vial
   under 10 %. Each tool keeps the large bottle's place, the bottle on its floor. A tool with one window keeps the large bottle; a
   tool paid by its API keeps its coin.
2. **The colour follows whichever runs out first** (the lower of the two shares, at today's warning and danger levels): a vial
   brim-full is red.
3. **Two shares under it**: the now share in bold (in the warning's or the danger's colour), the week's muted under it; the words say
   both and when each comes back (*Claude Code: 30% of the 5 hours left, until 18:40; 82% of the week, until Thu 09:00*).
4. **A tab's sword and shield say whether their side follows the default**: a mark **in a small frame** (the default potion's frame)
   follows the default and shows the tool it is on now, changing when the work moves on; a **bare mark** is a tool set for the party,
   and when that tool is dry its mark is dim with the moon beside it (*waits for Claude Code until Thu 09:00*). The words say it:
   *Does on the default (now Claude Code)*, *Does on Claude Code, set for this party*. Hovering the default potion marks the framed
   marks too.
5. Drawn in orkUI first (the three smaller bottles), then here; spec 114, built by the cheaper model.
The owner's call.

## 193. Play is a map for every leader's lens: marks on the live product, hints by code (31 October 2026, the owner)

Why: the owner: *Play today is only to poke at the product and come back with an idea; gather feedback while working with the
running project, and let the person pick an area of a screen and a problem for a party's leader*; then: *it is the same work as
with the leaders' lenses, but on the live product.* So:
1. **Play is one more map, the product itself, shared by every party**: under a party's tab it is seen through that leader's
   lens (its map's parts on this screen, its concerns, its aspects); the tab changes the lens, never closes Play.
2. **A mark** is a box on the live product with a line, a kind (*Bug*, *Looks wrong*, *Missing*, *Confusing*) and the open
   tab's party; it becomes a goal carrying what the live product knows (the screen, the element, the commit, the errors, the
   requests, the server's last lines, a picture of the moment). A bug's mark with its failure reproduces: no diagnosis call.
3. **What the probe sees by rule is a hint** (an error, a failed or slow request, a press that did nothing, a press again and
   again), in the lens of the party whose aspect it is.
4. Not: analytics of real people (a later spec, through the tools a project already has), a recording of the session, a
   native app on a device, the phone.
5. Spec 115, built by the cheaper model; the owner sent it to the build without a review of its mockup.
The owner's call.

## 194. Hypotheses live on Product's tree: proposed by the leaders, tested by goals, judged in the hand (31 October 2026, the owner)

Why: the owner: *do we have a place for hypotheses in the product? Maybe on the analytics' or the product's leader's tab.*
There was none: the tree's experiments tie two goals, a goal's *Defaults* are lost in its spec, and the decisions file keeps
what was decided but not the belief under it. There is no Analytics party, and the analyst leads Run only once a project is
live, when hypotheses matter least. So:
1. **A hypothesis is on Product's map**, between a job and its goals: *We believe …*, *We'll know when …*; seven open at
   most. Product's leader keeps them; **any leader may propose one** (Talk's `assumes`), and Product's leader proposes the
   riskiest from what the leaders assumed, on a press.
2. **A test is an ordinary goal**; when its tests are done the hand asks **Did it hold?** (*Held*, *Refuted*, *Not sure yet*);
   held or refuted writes a decision.
3. The aspect *Evidence* gains the hint *Rests on an untested hypothesis*.
4. Spec 116, built by the cheaper model, without a mockup.
The owner's call.

## 195. The phone: a menu of the leaders from the crown, what is picked in the middle, the hand at the foot; the top card answered with one tap; the PWA first (31 October 2026, the owner)

Why: the owner, after living with the phone as the hand alone (§180.1 asked it again): *a left menu in place of the
Orkmaster's tab: a list whose rows are the leaders' tabs (with their attack and defence) and under each the goals at work;
the goals whose spec is still being found at the top; above the main area the mana's bottles, the die and the discard; in
it, by what is picked, a leader's header and lens or a goal's description and its stages; at the foot the hand and a + for
a new goal.* The phone today answers *what waits for me* and nothing else; *how is it going* sends the person to the
computer. The menu is the Board turned on its side (a lane a row, a goal's cascade a row under it), so the phone gets the
Board without a layout on its side. The owner's yes on `docs/mockups/phone/sidebar.html` (A, not B: the row of heads), and
*yes* to keeping one tap for the top card. So (this changes §145.9 and §104.8 for a phone, §174.1, §178.2, §179.1,
§180.1, §180.3–§180.6; the desktop is unchanged):
1. **The crown opens the menu** (top left; never an edge swipe, the left edge is iOS's back): at its head the project with
   its switcher, *Settings* and *Stop all* (what **…** held, §180.5); then **the Orkmaster's goals** (in Talk, in Spec, in
   line with the moon); then **each party** its leader's head, its name, its sword and shield (§189, §192.4) and its goals at
   work under it, each its element, its type's sign, its short name and its phase. **The menu is a way to look, never a place
   where something waits**: no count, no alert, no *waits for you*; what waits is the hand's. A press picks and closes it.
2. **The middle shows what is picked.** A goal: its name, its element and type, its phases, its route by its leaders'
   heads, why, and the tasks of its step at work; **its top card in the hand lies on it with its answers, answered with one
   tap** (§180's lifted card, in its place under the goal's name). A party: its leader's header (squad, size, the tools of
   its sword and shield), its goals at work and its concerns (§183). **With nothing picked, the goal of the hand's first card
   is picked**, so a push lands where it did; answering a goal's last card picks the next.
3. **The top row**: the crown, the potions as bottles in two windows (§192, `.small`: this changes §179.1's marks), the
   die (§190; on a phone it says *Play it on the computer*), the discard (pressed, it opens over the pane).
4. **The hand at the foot**: one card an entry of §180.6 (a goal's top card, a card of no goal, a goal ready for main),
   their upper parts in a row that scrolls sideways, the picked one raised; a press picks it. **The + card lies at the row's
   right end**, under the thumb, never over a card (this replaces §180.4's deck). The arrows and the swipe go.
5. **The map of a leader is not drawn on a phone yet** (neither as text nor as cards); asked again after the owner's week.
   The quick question (§181) stays the desktop's.
6. **The PWA first** (spec 94 D: `pwa/index.html` loads the page, the frame does only what a phone has); the native frame
   (§174.4) later. The phone's old face stays until spec 94 E.
7. Spec 117, built by the cheaper model.

## 196. The die's up face says what Play would show: the cross while the last start failed, a spark when dev is new (31 October 2026, the owner)

Why: the owner: *how else can the die be used while it just lies: show something useful on its up face*; of the ideas
weighed (the last outcome, dev's news, the probe's alarms, an empty face asleep, the leader's head), *1 and 2*. The question a
die in the hand can answer is *why press Play now*. A count would break §104.0 and §145 (no count of what waits), so the face
says *something*, never *how much*. So (this makes §190.2 and §190.7 precise):
1. **The cross stays** on the die in the hand **while the last start of dev's head failed**; it goes when a start plays, or
   when dev moves on (then 2).
2. **A spark** (orkUI's new `face-new`, in the ink: news, not a warning) when **dev's head is a commit the person has not tried in
   Play**; a project never tried says nothing.
3. **The cube rolls onto the face** that says it when it changes (orkUI's `is-landing`); not under reduced motion.
4. The word under the die stays *Play*; the button's `title` says it (*Play: it did not start last time*, *Play: dev has changed
   since you last played*). The phone has no Play and gets none of it.
5. Spec 118, built by the cheaper model.
The owner's call.

## 197. The hammer and the bug: Fix Orkboard starts Claude Code on its own code; the phone may ask for it (31 October 2026, the owner)

Why: the owner: *a tool that fixes the system: it takes the logs of the last hours, starts a new Claude session on the computer
and says fix it; Claude fixes Orkboard and pushes; the computer offers to update, and the restart keeps the phone's link, so from
work I press Fix, then Update and restart.* And: *a full Claude, not the limited agents; one that shows up in my Claude app as a
Remote Control session.* And: *the hammer squashes the bug.* So:
1. **The bug at the end of the tabs' row gains Fix it**, beside Save logs: the person's line and the logs since Orkboard last
   started go into a git worktree of Orkboard's own checkout, and **Claude Code's Remote Control** starts there in full
   (`--permission-mode auto`, not the Board's limited agents), named *Fix Orkboard*; the person says *go* in their Claude app.
   Only a git checkout on `main` with Claude Code on the PATH offers it: the person who can push Orkboard's code.
2. **Claude pushes to main after the critical tests**; Orkboard sees main move and the bug becomes **Update and restart**. The
   person presses it: the hand decides, nothing restarts by itself.
3. **The update is checked before the restart and rolled back after it**: the new code is imported and asked its version
   first; when the window does not come up on it, the checkout goes back to the commit it came from and Orkboard opens again on
   the same port, so the phone comes back.
4. **An exception to spec 37 §8** (no edit and no git from the phone): the phone may start, stop and update a fix. It still
   edits nothing and runs no git itself; Claude Code works on the computer, and the person tells it *go* in their own Claude app.
5. **The hammer squashes the bug**: orkUI gains the icon `hammer` and the sign `bug-squashed`; the button raises the hammer while
   Claude works and shows the squashed bug, in the signal, when the fix is in. Until orkUI's are copied, the button wears the
   signs orkUI has (`work`, `check`, `cross`).
6. Spec 119, built by the cheaper model. A cloud session is later, only if the computer's proves not enough.
The owner's call.

## 198. A goal heard at the Orkmaster: Talk by itself; an agreed goal starts by itself after a wait; a dispute is a hearing, thrown to a side (1 November 2026, the owner)

Why: the owner: *the green card's field is a card, the rune given by itself and changed only on a wish; sent, it goes to the
Orkmaster's lane, and the Orkmaster holds the debate with the leaders, shown at the least; the leaders' questions come to the
hand as cards while the spec's card stays at the Orkmaster; when all say yes, the card lies a while and the work begins by
itself, weighed by priority against risk; when they disagree, the card in the middle, the leaders at its sides with their
phrases, and you swipe it, as in Tinder on a phone, to the one whose arguments you take.* Today a goal with nothing to settle
still waits for two presses (*Talk* on the route card, *Confirm and start* on the decision's), the leaders' verdicts are given
before the person's answers and never again, a no is a card a leader and a doubt a line, a fork another face, and Product
weighs only the goals its types name. So (this changes §118.1, §138.2, §147.3, §149.1, §183.3, §187.1, §187.3 and §195.4):
1. **The + card's field is a card**: the text its body, its rune large at its top, given by rule; a press on the rune changes it.
2. **A routed goal goes to Talk by itself** when nothing stops it (the keeper may run, the limits are not low, nothing is
   paid); else its route card as today. While the leaders talk, the goal's card in the Orkmaster's lane wears its rune's flame
   and its route's heads, lit as each has said: no verdict, no count.
3. **The leaders judge again after the answers**: those who doubted, said no, or saw their pick overridden.
4. **Product's word is needed for a goal to start by itself**: a goal its types do not route to Product is weighed by
   Product's leader anyway (a verdict and a priority, no question, no section). Tech's leader gives the risk; the rules of
   `idea_risk` still raise it.
5. **All agree → the wait**: a minute for a high priority at low risk, ten minutes for what the plan's autostart would start,
   no wait for the rest (the decision's card as today). The wait runs only while a face is open; **Hold** stops it. At its
   end the decision is written by itself, its heading *the leaders, all agreed*, and the sections follow.
6. **Any no or doubt → a hearing**: the goal's card in the middle and at most **three sides** (*Do it* at the right; *Drop it*
   or *After …* at the left; *Do the smaller one* at the top), each its leaders' heads and words; the middle takes the
   person's own words. Thrown by a swipe or a drag (on the card only, never from the screen's edge), a key or a press (one tap
   stays); a drop can be undone for six seconds. A fork after the sections is a hearing too, its sides the fork's.
7. **The leader's call is measured before it is changed**: whether parallel calls write the same prefix again and whether
   the map is read from the cache; a staggered start and the map in the system prompt only where the numbers say so.
8. **One card through a goal's life**: the + card is a card's back; pressed, it turns over into the card of the text; sent, it
   turns back, its rune lit, and goes face down to the Orkmaster; talked over it lies face down (its own rune and name on its
   back, never the + card's green), and **the seal's ring of runes is the wait**; at the wait's end it turns up and flies to
   its lane. Hovered it only lifts; pressed it turns and shows its words, its route and what each leader said. A hearing
   turns it up in the middle.
9. **A card is handed from where it was played and played back there**: from the goal's card on the table, else the
   leader's tab, else (the phone) the crown; the head that plays it gives one beat, the card flies face up with its asker's
   head in its window and says *From <Leader>*; answered, it flies back into its origin; dropped, it crumbles where it lay.
   Never for what came while the page was hidden, never while a pointer is down, three at most at once, nothing under
   reduced motion. The turn, the slow seal and the give are drawn in orkUI first.
10. Spec 120, built by the cheaper model after the owner's yes on its mockup. A reply round between the leaders, a leader's
   offers on its lens, Product's summary of the table and Art's sheet of assets are later.
The owner's call.

## 199. Three jobs of an indie maker: the morning and the evening run the product and give feedback, the day touches sketches of its ideas on the phone, the night builds; a day's idea can still be built by day (1 November 2026, the owner)

Why: the owner: *an indie maker has little of two things: tokens (subscriptions to Claude, Codex and their kind, not always
large ones) and time (they work at a main job). During the day you want to glance at something quickly in a light face, and
at home to go deep. So it is a co-operative card game with friends: the leaders are your fellow players at the table, not
rivals.* And the jobs, plainly: *morning and evening, run my product, see that all is well, and give feedback on it quickly
and easily, through the lenses and Play; during the day, throw in my ideas, UI and UX first of all, and have quick prototypes
of them to touch; at night, all the work and the checks.* And: *a good enough idea may come by day that you want built now,
and its result by day, from the phone: that stays possible.* Talking costs little (a leader's call is the cheaper tier, no
file read); building costs much: so the day is for what is cheap and seen, the night for what is dear. So:
1. **The three jobs are the product's frame**: a feature serves one of them or waits. **Job 1, the morning and the evening**
   (the computer): run the product, see that all is well, give feedback fast through Play's marks and the lenses. **Job 2, the
   day** (the phone): throw in an idea and touch a quick sketch of it. **Job 3, the night**: the building and the checks.
2. **The leaders are fellow players**: they still say no (§183), warmly, as players argue a move in a co-operative game; the
   person plays the card.
3. **A goal that is seen or heard gets a sketch before its spec**: two or three throwaway variants by its craft's leader (a
   screen as one self-contained page, a picture, a loop on a page), kept beside the goal and never in the project's code,
   served in a sandbox that reaches neither the Board nor the network, touched and picked on the phone; the spec rests on the
   one picked. Pictures and sounds only with the media tools set up, and a paid one only with the person's yes.
4. **Work at night** (a setting, off until the person says): what would start by itself waits for the night's window, in
   Product's order; Talk, hearings, sketches and looks run by day. **The day's case stays whole**: *Build it now* on a goal
   held for the night (today's *Start now*, widened) and *Pick and build now* on a sketch start at once, from the phone too;
   the result is seen on the phone as its pictures and its ready card, Play staying the computer's. A bug's short way and any
   press start at once, as today.
5. **The morning's card** says what the night did, each goal with the screens it changed, and **Play it** opens Play on
   that screen; a mark costs no work by day. **The evening line**: each leader's look says in a line whether what changed
   since its last look went toward its aims, and what broke.
6. **Measured** as hypothesis H2 (`docs/hypotheses.md`).
7. Spec 121, built by the cheaper model. The leaders' voices, a hearing heard on the way, are spec 122, later.
The owner's call.

## 200. The die at rest shows the play arrow on its up face (1 November 2026, the owner)

Why: the owner: *by default the die's up face could show play as an arrow: it is clearer, and it suits the die.* Today the up
face at rest is the five (§196), which says nothing of what the die does. So (this makes §196 precise):
1. **At rest the up face is the play arrow**, drawn in the die's own marks (2 x 2 cells, the pips' muted ink; the ink and the
   glow while it plays): orkUI's new face `face-play`, made in orkUI first (`die/die.json`, `tools/build_die.py`), then copied.
2. **The cross and the spark stay** (§196.1–§196.2): they say more than the arrow, so they take its place while they hold.
3. **Asleep** (no preview, spec 113) the up face stays the five, grey: the arrow never promises a Play that cannot start.
4. The other faces keep the die's numbers, so it still reads as a die when it rolls. `playdie.js` `faceNow` gives `play` where it
   gives `5` today for a die awake; drawn in `docs/mockups/hearing/` §6.
5. **The spark becomes how many**: the owner, *the spark could be something plainer, +3 when there are three new features*. When dev's
   head holds goals the person has not tried in Play, the up face shows **that many pips** (one to five; six for six or more), in
   the ink, the die's own way of saying a number: a digit would not fit a face of 18 cells drawn in 2 x 2 marks, and pips read as a
   die. The arrow at rest (1) is what tells them from a roll. Its `title` says it (*Play: 3 new goals in dev since you last
   played*). This changes §196.2, and for the die alone §196's *never how much*: it counts what is new to play, never what waits
   for the person (§145.3 stands for the deck and the tabs). The snapshot's `play_face` gains `new_n`; `face-1` … `face-6`, which
   orkUI has, draw it (the spark stays in orkUI, unused here).
The owner's call.

## 201. The leaders at the table: the open leader large with its marks and its bubble, the header one row, the leaders' faces as states, chairs and the empty chair, the dark edges, Stop all a door (1 November 2026, the owner)

Why: the owner: *the vibe went from a card battle to a co-operative game (§199.2), so the faces on the tabs are your
companions at the table: the picked leader's face larger, its alerts and notes by its head; the heads could change their
expression, as real players; the question asked on a lens a bubble rather than a line; no Leads on a leader's lens, the
tab is the leader; the rest of the team named, with the sword and the shield by Does and Checks*. Then: *those who decide
or advise sit at the table with you; those who do and check are the leader's squad, on its lens*; *make the squad smaller*;
*the leaders sit on chairs above the table with the cards, and a new party is an empty chair*; *the back under the head,
it looked like a little house*; *black behind the chairs and behind the hand*; *no lines between the leaders off the
table*; *Stop all as a door*, *shut by default, opened when you press it*; *no lit box on the open tab, only the larger
head*; *the chair's back a solid colour*. The mockup `docs/mockups/lens-heads/`, the owner's yes on it. So:
1. **The open leader is its head, large** (48 x 44, the race sheet's @2x, §161), on the open tab, leaning in over the
   table's rim; the other leaders' heads at 36 x 33 (3 px a cell); no lit box, no bar: the open tab is told by its head,
   its party's name in the full ink with the leader's own name under it (§164), the others' muted. A tab grows in height,
   never in width (§143).
2. **Its concerns by its head**: the alert sign and the note's dot beside the open leader's head, each a press that steps
   through the marked parts (as the strip's counts did); the strip over the map goes (its counts, §67), **Ask again** goes to
   the party's **…**. The other tabs keep their alert sign.
3. **The quick question is the leader's bubble** (this changes spec 106 §3): the open leader's head pressed opens a bubble
   under it, the field focused (*Ask the Architect…*); the answer, *Make it a goal* and × in it; its foot the leader's seat
   (*Its seat: Claude Code · Veteran*, a press its popover, §110.7). One bubble is the one way a leader speaks: the answer,
   and later the evening line (spec 121 E) and a hearing's side (spec 120 §6.7). A member never speaks (§110.8). The
   desktop only (§181.8).
4. **The party's header is one row** (this changes §110.6, spec 95 §2.5): no *Leads* (the tab is the leader); **Does** with
   orkUI's sword and **Checks** with its shield, the AI tool's mark once by each (a seat carries its own only where it runs on
   another tool); each seat's role under its head in the muted caption; the size; the leader's aspects (spec 109 §4) at the
   row's right. The squad stays at 24 x 22, the smallest size a head is crisp at with its gear read (§148.7): who decides is
   larger, who does is not made smaller.
5. **The leaders' faces are states, never an idle motion** (§149.1): calm, focused (a task of its party runs), worried (an
   alert on its map), says no (its no in a hearing), pleased (its goal just done: a moment), asleep (its AI tool's window
   spent, or no tool). Drawn in orkUI for the leaders and the Orkmaster on the heads' 12 x 11 grid; a member keeps one face.
   A face is an accent: the alert sign and the words stay.
6. **The leaders sit on chairs at the table's far edge**: a chair's back, solid, lower than the head, behind each leader's
   head on the table's rim; the leader's lane on the Board is the table in front of its chair. **New party is the empty
   chair** (this changes §190.1's banner): the whole chair, faint, hovered or focused pulled out a little, its label *New
   party*; it stands only while a craft is not at the table. *Chair* is a picture, never a word (*seat* is the squad's).
7. **The dark edges**: the leaders' side and the hand on orkUI's room, near black under its canvas (never #000), the table
   lifted a step between, its rim on both sides; no line between the tabs off the table. The table is what is shared, the
   dark edges are the players' places: the + card leaves the dark hand for the lit table when it is sent.
8. **Stop all is a door** at the dark row's end (this changes §190.1's planks): shut at rest, whatever runs; pressed, it
   opens (the orks go out), its word *All stopped*, a second press doing nothing; it shuts when work starts again. Its word
   stays in the danger colour while it can be pressed. Not *Exit*: it halts, it closes nothing.
9. **At the narrow width** the heads' row as today, the open head at 36 with its marks, no chairs; the empty chair and the
   door as small marks before the row's end. The phone's menu (§195) is not changed here.
10. Spec 123 (spec 122 stays the leaders' voices), orkUI first (the room token, the chair, the empty chair, the door, the
   faces), built by the cheaper model, the spec's author reviewing.
The owner's call.

## 202. Orkboard is where a product is thought out with its leaders, not a crowd of agents at work: the brief every leader reads, the measures of the arguing, H1's trial (1 November 2026, the owner)

Why: the owner: *as a product, Orkboard is not a crowd of agents doing the work, even the stages of an indie maker's; it is
where you think out your product with a set of specialists who discuss your ideas, criticise them and polish them.* Read
against the Board as it is: Ideation (spec 65), a leader's no (spec 108), the seniors' frameworks (spec 109), the hearing
(spec 120) and the leaders as fellow players (§199.2, §201) already say so; hypothesis H1 states it, and lists what it lacks
before more faces: a brief every leader reads, any measure of how good the arguing turned out, and the head-to-head. A
team of personas alone reads as derivative (H1's table: BMAD); what may set Orkboard apart is the arguing grounded in the
real product, a no that goes to the person, a memory of what was decided, and the loop closed through the work and the gate.
So:
1. **The README's first line says it** (no longer *the agents at work and the results to review*): a product thought out
   with its leaders, who judge each goal against the real code and the live product, say no where it hurts, and hand it to
   the person's own AI tools. H1 stays open: the line says what Orkboard does, not that it is proven better.
2. **The brief every leader reads** (spec 124 A): the project's common core grows from three lines to six: whom it is for,
   what hurts them, **why this and not what they use now**, **what it must always be**, what it leaves out, **how it earns**.
   The first start asks the first three as before; the other half is a second sitting of the same call, asked once when a
   goal is added after the first is answered or let go. Every leader's call already reads the core (`project_facts.for_call`);
   Ideation's views, the Investor and the skeptic now read it too (they judged a pitch without knowing whom the product is for).
   No new face: the cards are the hand's, the facts the parties form's.
3. **The measures of the arguing** (spec 124 B): `realm/measures.py` reads the project's own event log, no new event: the
   leaders' no and doubt and what the person did with them, the leaders who changed their verdict, and **an overruled no
   that came back** (sent back, fixed or dropped at Review) beside the same share of the goals no leader objected to: the
   calibration a no is worth its noise by; concerns made a goal or not a problem; the Investor's word taken; sketches picked;
   **a goal accepted the first time**; the changes after the start. Read in the terminal (`orkboard measures`), never a count
   in the window (§104.0, CLAUDE.md).
4. **H1's head-to-head can be run** (spec 124 C): the protocol `docs/trials/h1-head-to-head.md`, and `orkboard trial`: a CSV
   to fill with each way shown blind as A or B, its tally and H1's verdict (20 points of first-time acceptance at no more than
   twice the minutes, over ten tasks at least). The trial itself is the owner's: real tasks, a person judging blind.
5. **What comes before new faces**, as H1 says, while it is tested: the brief's quality (§2), the stage-weighted rubrics,
   a shorter way for a goal one party can do alone, and the measures (§3) read weekly. Spec 124.
The owner's call.

## 203. The project keeps its journal and each leader its own: what was said and what came of it, written by code, read into every leader's call (1 November 2026, the owner)

Why: the owner: *in essence the main thing is to keep, all the time, the project's common history and the history of each of
the leaders' views.* A crowd of personas is copied in an evening; a product's history kept for months, through each craft's
eyes, is not. Today the pieces are scattered and mostly unread: the decisions file reaches a leader as its last ten headings,
and never Talk; the brief is a state with no why of its change; a concern dismissed is kept, one fixed is forgotten; the
evening line keeps only its last; a leader's no and what came of it live in the event log with no words; only a pitch passed
keeps its why. So:
1. **Two journals, one word** (`TERMS`: *journal*): **the project's journal** (what the project decided and what came of it:
   a decision and its number, a goal in main, a goal dropped and why, a hypothesis judged, the brief changed, a pitch passed)
   and **a leader's journal** (what its party's leader said and what came of it: its stance on a goal, its no heeded or
   overruled, a goal it objected to that came back or went through at Review, a concern made a goal or called not a problem,
   its evening line, its calibration). `realm/journals.py`, append only, beside the Board's state.
2. **Written by code where the thing happens**, one line in the product's words with the goal, the map's parts and the
   decision's number; never a model's call to write an entry. Nothing is rewritten: the person's *Not so* strikes an entry,
   which is kept marked and never read into a call again.
3. **Read into every leader's call**: its own journal (the digest, the entries on this goal and on the map's parts it
   touches, then the latest) and the project's journal; a member reads none (its leader's brief carries what it needs). A
   leader reads another leader's journal never: what another craft concluded reaches it through the project's journal.
4. **The leader's digest**: when its journal has grown since its last one, the leader writes *in short* what its lens knows
   of the product (900 characters at most), on the cheaper tier, no tools, in the background; the calls read the digest and
   what came after it, so the journal grows and the prompt does not.
5. **Calibration by code**: a leader's journal is given, as one line, how often its no was overruled and how many of those
   goals came back at Review, beside the goals no one objected to (spec 124's measures, by party).
6. **No new face now** (§104.0, §145): a quick question to a leader (its bubble) reads both journals, so *what did we decide
   about the lobby?* is answered from them; the host has the commands to read a journal and strike an entry; where the
   person reads and strikes in the window is a later spec, on the leader's lens.
7. Spec 125, built by the cheaper model, the spec's author reviewing.
The owner's call.

## 204. A project's own documents are read in, and the Board's are written out, in the formats the field keeps them in (1 November 2026, the owner)

Why: the owner: *check how the existing frameworks organise this, and make our specs and journals ready in a convenient,
common format, for a quick import of existing documentation and decisions into our product.* A project that comes to
Orkboard has a history already, kept in one of a few shapes: **ADRs** (Nygard's, by adr-tools: `doc/adr/NNNN-title.md` with
*Status, Context, Decision, Consequences*; **MADR 4**: `docs/decisions/NNNN-title.md` with YAML front matter `status`,
`date`, `decision-makers`, `consulted`, `informed`, and *Context and Problem Statement, Considered Options, Decision
Outcome, Consequences*); **spec kits** (GitHub Spec Kit: `.specify/memory/constitution.md` and `specs/NNN-feature/{spec,
plan,tasks}.md`; Kiro: `.kiro/steering/{product,tech,structure}.md` and `.kiro/specs/<name>/{requirements,design,tasks}.md`;
OpenSpec: `openspec/project.md`, `openspec/specs/<capability>/spec.md`, `openspec/changes/<id>/{proposal,tasks}.md` and
their archive; BMAD: `docs/prd.md`, `docs/architecture.md`, `docs/stories/*.story.md`); **an agent's memory** (Cline's
memory bank: `memory-bank/{projectbrief,productContext,systemPatterns,techContext,activeContext,progress}.md`; `AGENTS.md`,
`CLAUDE.md`); and **a changelog** (Keep a Changelog). Each is plain Markdown, most with a number and a date. So:
1. **Read in by code, no model** (spec 126 B): `orkboard import` and, once, the first start find the shapes above and read
   each decision into the project's journal on its own day (`decision`, its status said: *superseded*, *rejected*), a
   decision of one craft also into that leader's journal, a spec whose tasks are all done and a release of the changelog as
   `done`; nothing is read in twice. The documents that say what the product is (a constitution, the steering's product, a
   memory bank's brief and product context, OpenSpec's project, a PRD, `AGENTS.md`) are what Product's leader reads at the
   first start, so the brief's cards come as *the files say* (spec 99 §8, spec 124 A), one press each to confirm.
2. **Written out in the same shapes** (spec 126 C): `orkboard export` writes the decisions as MADR 4 files (or Nygard's),
   the brief and the journals as a Cline memory bank, and each journal as Markdown with front matter that `orkboard import`
   reads back: what Orkboard knows of a project is never locked in it.
3. **A project that keeps its decisions as ADRs keeps them so** (spec 126 D): the Board's decision is written as the
   folder's next `NNNN-title.md`, in the folder's own format (MADR or Nygard), not appended to one file; the leaders read
   the folder's records as they read the one file.
4. **The Board's own shapes stay** (`docs/decisions.md`, the goals' pages, the journals' JSON lines): the formats above are
   the doors in and out, not a new store.
5. Spec 126: its formats module by the spec's author, the rest by the cheaper model.
The owner's call.

## 205. The best of the field's formats in the Board's own: a decision's year, status and what it changes; MADR for a new project; Done when as scenarios; living specs of how it works now; a journal readable as Markdown (1 November 2026, the owner)

Why: the owner asked whether the Board's own formats are better or worse than the field's; the answer was mixed (§204):
ours are better in substance (the owner's voice, points a later spec names, §183.4; a spec's table of parts, files and
tests a cheaper model builds from; a journal kept append only with a digest over it), the field's in structure (a date
with its year, a status and what supersedes what, read by code; acceptance as scenarios that become tests; OpenSpec's
specs of **how the product works now** beside the changes to it; a memory a person can read). The owner: *do 127,
build it, and into main.* So:
1. **A decision's date has its year** (`1 November 2026`): the Board writes it so, and this file's 160 headings had it
   added (all were of 2026). A decision the Board writes says, under its heading, **`Changes: 110, 183`** when it changes
   earlier decisions (the Orkmaster names them from the headings it reads), and a `Status:` line when it is not accepted;
   both are read by code (`doc_formats.parse_log`), and a leader reading the headings sees which were changed and by what.
2. **A project with no decisions log gets MADR**: its first decision is `docs/decisions/0001-….md` (spec 126 D's folder),
   read by every ADR tool; a project with a log keeps its own, this repository its one file.
3. **Done when is written as scenarios** (*When …, then …*), each one a test can check; the bounds stay (five at most).
4. **Living specs** (OpenSpec's `specs/`): when a goal reaches main, its leader folds what it did into the spec of the
   capability it touched (*Requirement* and *Scenario*, added, changed or removed), kept with the Board's pages; the leaders
   read how the product works now there instead of following a chain of changes; `orkboard export` writes them as
   `openspec/specs/<capability>/spec.md`, and `orkboard import` reads OpenSpec's and Kiro's into them.
5. **A journal is readable**: beside its JSON lines, a Markdown mirror in the export's shape, written again after each
   change (`.orkcraft/journals/<scope>.md`).
6. Spec 127: A and the mirror by the spec's author; B and C by the cheaper model.
The owner's call.

## 206. The Orkmaster's column on every tab, three piles of whole cards; the + card turned where it lies; one way to talk to a leader; a goal picked is a view of its own at each leader; the discard picked against its spec; the night's goals to the discard; a rune is a shape and a colour (2 November 2026, the owner)

Changes: 145, 160, 167, 181, 186, 187, 198.

Why: the owner, over a day of mockups (`docs/mockups/goal-card/`): the field for a new goal opened in the window's middle
while the + card stayed where it lay, which looked broken; the Orkmaster's goals moved away whenever another leader's tab
was opened, so what is at work and what is next was out of sight; the goals the Orkmaster still reads, the ones the
leaders agreed and the ones at work looked alike; a question the person cannot answer came to the hand; the project's
question and a change to a goal were asked two different ways; a goal done could not be looked at against what it
promised; the five runes repeated in the Orkmaster's column; the morning's card repeated the discard. So:
1. **The + card turns over where it lies** and grows up from there, its foot under the window's edge; Esc or a press away
   turns it back with its words. Its choices are squares in a row, as the rune is: *Rune*, *To* (the leaders' heads; the
   Orkmaster decides when none), *Type* (the party's types by their pictures), *Files* (from this computer, or a file of
   the project). The seal's ring is whole: the five runes and three of orkUI's own, eight places, which are also the
   wait's eight steps.
2. **The Orkmaster's column is pinned at the window's left**, off the table on the canvas (as the hand is), the same on
   every tab; **its head is the Orkmaster's tab** (the Board: who does what), and the tabs at the top are the leaders'
   only. *No left column* (§145) still holds for a list or a drawer: this is the first lane, pinned, of whole cards.
3. **Three piles, top to bottom as a goal lives**: **In analysis** (not yet agreed: in line, read, routed, talked over),
   its cards **sideways and face down, with no name** (a tight pile; the one being worked on named under the title; a
   press reads the pile out in order, with *Next* and *Remove*); **To review** (agreed, its wait running: face up and
   still, its wait a bar in eighths, then a time; it starts by itself); **At work · later** (at work: its rune glowing,
   its leaders' heads at its foot; then put off: a time today, or the moon). A pile shows its front card whole and the
   foot of each card under it, then thin edges, never a count. A card agreed turns upright and face up into To review;
   its wait over, it moves to At work and its tasks are dealt to its leaders' lanes. A face-down card cannot be picked.
4. **A goal lies only in the column, its tasks only in its leaders' lanes.** Picked, every tab looks at it: **the
   Orkmaster's tab shows its plan alone**, its tasks in their leaders' lanes, their order as arrows; **a leader's tab
   shows another view, what it will change** at that leader's level (its parts, new, changed or read only, their lines,
   the contract's; Design's screens now and as they will be, with their states), a small whole map beside it with its
   parts lit, its *Done when*, its tasks there. With nothing picked a leader's tab is its map of the whole project.
5. **One way to talk to a leader** (§181 stays): the open tab's head pressed again (the Orkmaster's too), or a part of a
   change pressed, opens the bubble under the head, about what is picked (nothing: the project; a goal; the part as a
   mark). The answer reads and changes nothing; **a card only when something would change**: *Make it a goal* (the + card
   opens with the words in it) or *Make it a change* (a goal agreed or at work: the leader's plan now and proposed, and
   what it costs, a decision in the hand; Design's three looks to choose from). The + card is for new goals only.
6. **The hand gets only what needs the person**: a choice only a person makes, a question no leader could answer, a
   decision the person asked for, a failure. **A question another leader can answer goes through the Orkmaster**: it
   leaves its goal for the column (*passing on*), stays a few seconds where the person can take it (*Answer it myself*,
   *Pass it now*), goes to that leader, and the answer goes back into the goal; the goal says *Asked Tech* and is not
   yellow (yellow means only: you are needed). One hop: a leader that cannot answer sends it to the person.
7. **A question for the person leaves its goal**: the goal stays at its leader, yellow and still, and the question flies
   out of it into the hand, and back into it when answered. **A failure** turns its card red and throws it from where it
   lay into the hand; a dashed place stays in the lane for *Try again*.
8. **The discard can be picked**: the leaders' tabs show what the goal changed against what its spec promised (✓ as
   promised, ≠ not quite, + more than promised, ✗ not done) and its *Done when*, checked; **the Play die wears its
   rune** and plays the product with it (dev now, at its screen; or as it was when it landed). A rune is the goal's
   version of the product, never called a branch: the person sees dev and main only (§49).
9. **The night's goals done go to the discard** under a small moon until seen; a night's failure comes to the hand red;
   the morning's card goes (§199.5).
10. **A rune is a shape and a colour** (§186 changes): five shapes, five colours, 25, unique across the project's open
    goals and the results not yet seen; a new goal takes the shape used least, then the colour used least, so the first
    five differ by shape. orkUI draws an element's shape in any of the five colours.
11. **Cards in analysis lie sideways only while face down**; a face-up card is never turned (its text and its rune would
    turn with it). Moving is at work, still is waiting, yellow is you, red is a failure.
12. Spec 128 builds it, its parts by the cheaper model, into main as each is green (the critical tests). **orkUI's own
    changes wait for orkUI**: the stepped corner that grows with a card and the stronger glow (Orkboard's sheets carry
    no corner of their own). The rest is drawn here from orkUI's pieces and tokens: the busy ring is orkUI's sweep, the
    whole ring orkUI's runes in their places, a hue an element's token.
The owner's call.

## 207. A task shows its steps: what its worker is on now, the same on Claude Code, Codex and Antigravity (2 November 2026, the owner)

Changes: 167.

Why: the owner: a task's card says *Doing · 12 min* and nothing of what is being done; the person cannot tell a task
that moves from one that is stuck, nor see early that it went the wrong way. A card is a task, not a member (§167.1);
inside a task its worker goes through steps of its own. So:
1. **A task has steps while it is at work**: at most six, each *done*, *now* or *next*, in the worker's own short words.
   On its card the label row reads *Doing 2/5 · tests for join*: small square pips (the one now glowing: moving is at
   work) and the step now in one line; the time goes to the card's words. Lifted, the card lists its steps (✓ done, the
   one now lit, the next faint) beside its *Done when*. The goal's card in the Orkmaster's column says its tasks' count
   (*3/7*). Only a cascade's front card shows the line; under 760 px only the pips.
2. **The same on the three main tools** (Claude Code, Codex, Antigravity), so a step is read by one rule wherever the
   task runs: **the worker keeps its steps in a file of its worktree** (`.ork-steps.json`, never landed), told so in
   every working prompt; the runner reads it as the task runs. Where a tool streams its own to-do list (Claude Code's
   `TodoWrite` in stream-json, Codex's plan in `exec --json`) it is read too and fills in while the file is missing;
   with neither, the step is **what it is doing**, from the worktree's changed files and the last command it ran
   (*edits lobby.ts*). No model call reads steps.
3. **Checked on all three**: recorded outputs of each tool in the tests, and `orkboard steps-check --tool <tool>`,
   which runs one small real task in a scratch repository and says which steps it saw and from where, run on a machine
   where the tool is signed in.
4. Spec 129 builds it by the cheaper model, the host and the page side by side.
The owner's call.

## 208. The Tech lens measured against how small teams keep architecture: one map read from the code, what changes together, a load-bearing part being changed, quiet while a part is young, and the engines read (2 November 2026, the owner)

Changes: 89, 90, 109.

Why: the owner had a research run on how the crafts' frameworks are drawn and which of them indie developers keep (a
prompt to Gemini, its answer for Tech). What it said, unsourced and so taken as a hypothesis, not as evidence: a small team
keeps an architecture picture past a week only when it is very high (five to twelve blocks for the whole project) or
drawn from the repository with no one's hand; class diagrams and C4's third level kept by hand die at the first
prototype, when a game's architecture is rewritten in an evening; Tornhill's behavioural analysis (hotspots and
**temporal coupling**: two files changed in the same commits with no reference between them) is the part worth having,
since an import graph never shows it; Martin's metrics shrink to one rule: a part everything stands on that keeps
changing is the risk. It proposed a second map (a 2×2 of churn against complexity), files as small cards inside a
module's card, a phone list of *hot nodes of the week* ranked by a risk index, and a look of its own (a hex grey,
glows, red and amber outlines, a *God Object* badge). Measured against what is built (spec 89's System, spec 90's
containers and layers with the uses drawn on hover, spec 109's hints), the main map it recommends is the one we have.
So:
1. **System stays the one map, read from the code.** No second map and no new tab: the 2×2 is an analyst's chart of the
   same parts, and spec 109's aspect chips already narrow the map (a press on *Hotspots* leaves the hot cards and dims the
   rest). No files as cards inside a part's card: a part's files are seen when it is opened in the right column. The
   first question stays spec 89's, *what changed since your last look, and which goal changed it*; where a game's
   architecture moves in an evening, that is worth more than where it hurts.
2. **What changes together** (`co_change`, a new hint in *Coupling*): two parts changed together in most of the commits
   that touch either (a share and a least count of commits in the last CHURN_DAYS days), with no use between them either
   way. Spec 90's `shared_churn` stays for the containers. Its line between the two parts is drawn only while its concern
   is open or its card is hovered, dashed, never on the table at rest.
3. **A load-bearing part being changed** (`bearing`, in *Hotspots*) **takes `unstable`'s place**: a part used by many
   parts (fan-in at least BEARING_IN) changed many times in the last CHURN_DAYS days. Its words name both numbers
   (*9 parts use it; it was changed 14 times in 30 days*). Martin's instability is not shown to the person. The layers
   already lay what most use at the bottom (spec 90 §6.5), so nothing new is drawn: the hint lies on the bottom card.
   Tech's hints are nine kinds, one more than today.
4. **Quiet while a part is young**: a part placed in the layout less than YOUNG_DAYS ago gives no hint of change
   (`hotspot`, `co_change`, `untested_churn`); `bearing` alone speaks of it. A prototype is changed everywhere, and a
   lens that says so of every card is no longer looked at.
5. **The engines are read**: System reads Godot (`project.godot`, its autoloads, a scene and the scripts it holds,
   GDScript's `preload` and `extends`), Unity (each `.asmdef` a container, its references its links, C#'s `using`
   between parts) and Unreal (`.uproject`, each module's `.Build.cs` and its dependencies). Today `code_map` reads Python
   and JS/TS alone and the containers are found by `package.json`, `pyproject.toml`, `go.mod` and `Cargo.toml`, so a
   game made in an engine gets an empty System: for indie game development this comes before every hint above.
6. **The look is orkUI's**: the tokens alone, colour a signal, no glow; a hint's words say what happens, in numbers and
   plain words, never a label (no *God Object*). The phone gets no list of parts and no risk index: a concern that needs
   the person comes to the hand as a card, as every concern does.
7. **The evidence is asked for before the spec**: the research is asked again for its sources (GDC talks, postmortems,
   posts of indie teams on keeping or dropping their architecture pictures). Where they say otherwise, this decision is
   changed before it is built.
8. The spec that builds 2–6 comes in a few days, the engines (5) a part of their own.
The owner's call.

## 209. The Design lens measured against how small teams keep their screens: the states as a stack under a screen, the controller and the Deck, the focus path and contrast on Play, and a game's scenes read as its screens (2 November 2026, the owner)

Changes: 102, 109, 115, 208.

Why: the same research as §208, for Design (a prompt to Gemini, its answer unsourced and so taken as a hypothesis).
What it said: a map of screens kept by hand in Figma or FigJam lives only until the layout moves into code or an
engine's scene editor, so the map must be read from the code's router and the build's pictures; even indie games well
reviewed on Steam are faulted most for the controller and the states (an upgrade window *B* does not close on the
Steam Deck, *A* that starts what it should not, a window the D-pad cannot walk through). It proposed a *flow and state
atlas* (the screens left to right, each screen's states as a fanned stack of corners under its card, a missing one
dashed), a second map (a *focus and accessibility X-ray*: an enlarged copy of a screen laid beside it, the Tab or D-pad
path drawn over it, the contrast and small targets marked), pins by the model at a control's coordinates labelled
*H3 / Steam Deck: No B-button binding*, a hex grey, and a phone carousel of the screens with pins unresolved. Measured
against what is built (spec 102's Screens read from the router with the build's pictures and the steps left to right,
spec 109's `no_states` and `a11y`, spec 115's marks on Play held by the element), the main map is the one we have. So:
1. **Screens stays the one map, read from the code.** No second map, no copy of a card laid beside it.
2. **A screen's states as a stack under its card**: corners *Loading*, *Empty*, *Error* under the card, each solid when
   its file names that state, dashed when it does not (`no_states` split by state: its words name the states missing).
   The reading stays words in the screen's own file, not a syntax tree; a state handled in a child component or a hook
   is not seen, so the words say *not found in its file*, and a dashed corner is never red alone. *Empty* is shown only
   for a screen that loads something (a fetch, a query, a loader in its file).
3. **The controller and the Deck in Accessibility** for a game (a project whose stack has the role *game*, or an
   engine's): the rubric gains Valve's Steam Deck Verified points: *B* goes back and closes, every element is reached by
   the D-pad, the game is played with no keyboard, the glyphs are the controller's, the text is readable at 1280×800.
   They judge in the look and in Talk; by code only what a file says (a back or cancel action bound, the glyphs' assets
   present).
4. **The focus path and contrast on Play, under Design's tab**: the probe walks the page by Tab and draws the path over
   the live page, an element no Tab reaches and a target under 24 px marked as hints; the contrast checked on the
   rendered page by axe-core (copied unchanged into `gui/static/vendor/`, its licence beside it, a line in `NOTICE`).
   This is what spec 109 left for want of a rendered page. A pin is held by the element the probe knows, never by a
   model's coordinates on a picture.
5. **A game's scenes are its screens**: with no router, Screens reads an engine's scenes (Godot: a `.tscn` whose root is
   a `Control`, the moves by `change_scene_to_file` and `change_scene_to_packed`; Unity: the scenes in the build
   settings, UI Toolkit's `.uxml`, the moves by `SceneManager.LoadScene`). §208.5's engines are read for Screens too.
6. **The look is orkUI's and the words plain**: the tokens alone; a hint says what happens (*B does not close the
   upgrade window*), never a code (*H3*). The phone gets no carousel: a concern that needs the person comes to the hand
   as a card, and the phone has no Play (spec 112 §3.3).
7. **The evidence is asked for before the spec**, as §208.7: the Steam reviews it speaks of, named, and the indie teams'
   own words on keeping or dropping their screen maps.
8. The spec that builds 2–6 comes with §208's, the engines (5) in their part.
The owner's call.

## 210. The Product lens measured against how small teams keep their tree: one job in focus, a goal judged against the project's pillars, a solution posing as a job, a test's state on its goal; no score (2 November 2026, the owner)

Changes: 102, 109, 124, 172.

Why: the same research as §208, for Product (a prompt to Gemini, its answer unsourced and so taken as a hypothesis).
What it said: in small teams a RICE table and a sprawling opportunity tree die of the gap between the board one thinks
on (Miro) and the code; a RICE score demanded of every ticket cuts *shipping fast* off from *shipping right*, and a
feature scored high locally wears away the product's identity and positioning; RICE's own authors at Intercom say the
score is no hard rule (a low one is often what a large goal stands on, or table stakes), and a low *Confidence* is a
call for a quick experiment, not a factor. Torres' tree fits cards when the focus is narrow: one **target
opportunity** at a time, three competing solutions under it, a test of the riskiest assumption under each. It proposed
a four-tier tree under a North Star card with a live metric's line and three input metrics, one opportunity in focus
with lines only from it, a second map (a 2×2 of impact against evidence the assumptions are dragged onto), badges
(*Solution in Disguise*), a lit link when commits start on a solution whose riskiest test is not passed, a *blocking*
pin when a solution breaks the design pillars, and on the phone the branch in focus alone, for a pivot after a
playtest. Measured against what is built (§172's tree: one or two outcomes, three to seven jobs in JTBD's sentence, the
Board's goals serving them, experiments testing them; spec 109's `vague_outcome`, `no_evidence`, `off_tree`,
`untested`; spec 124's brief with *pillars* and *leaves_out*), the map is the one we have, and nothing of ours scores.
So:
1. **The Tree stays the one map, and nothing is scored**: no RICE or ICE anywhere, not on a goal, a job or a card. No
   second map: the 2×2's question is the *Evidence* aspect, and a test's state lies on the tree (4).
2. **One job in focus**: the person may mark one job the job now (one at a time; marking another moves it). Then the
   tree draws its lines from that job alone, its goals and their tests under it, the other jobs folded to their one
   line. A new hint in *Focus*, `off_focus`: goals at work that serve another job (a number of them, its words naming
   both jobs). With no job marked the tree is as today and the hint is silent.
3. **A goal judged against the project's pillars**: Product's leader reads the brief's *pillars* (*What it must always
   be*) and *leaves_out* (*What it leaves out*) in its look and in Talk, and a goal that goes against one is a concern
   that quotes it (*This goes against "What it must always be: …"*). A model's judgement, never by code; a concern like
   any other, never a block: the person decides, in the hand.
4. **A test's state on its goal's card**: a corner saying *no test*, *testing*, *held* or *failed* (the experiment's and
   the hypothesis' state, `realm/hypotheses.py`), so what is built on faith shows on the tree itself. `untested` stays
   the hint for a goal at work on an open hypothesis with no test.
5. **A solution posing as a job**: when a job's *I want to* names a feature rather than what the person is after, the
   leader asks in its look *This is a solution: what does it let them do?* (in *Opportunities*). A model's judgement.
6. **Not taken now**: the North Star's live line and input metrics (the project's analytics are not read yet: the
   later spec of spec 115 that reads PostHog, Sentry or Firebase); jobs gathered from Steam reviews and Discord (a
   connector of their own, later); three competing solutions as the tree's rule (an agent's variants are cheap, and a
   pick of variants is spec 51's); a view of its own on the phone (a pivot after a playtest is a card in the hand).
7. **The look is orkUI's and the words plain**: the tokens alone, the job in focus by the signal's token, never a badge
   in English jargon (*Solution in Disguise*).
8. **The evidence is asked for before the spec**, as §208.7: the post-mortems and Intercom's own words it speaks of,
   named. The spec builds 2–5 with §208's and §209's.
The owner's call.

## 211. The Game design lens measured against how small teams keep their loops: the hooks by how the game earns, the pillars over the loop, a currency's config and who changed it (2 November 2026, the owner)

Changes: 109, 156, 210.

Why: the same research as §208, for Game design (a prompt to Gemini, its answer unsourced and so taken as a
hypothesis; its figures of a *GDC 2023 survey*, 85% of AAA studios and 67% of indie teams keeping a design document,
68% drawing the core loop before code, are most likely made up and are checked first). What it said: the long design
document gave way to living pages and Stone Librande's one-page designs (GDC 2010); design pillars and non-goals at the
top (Tim Keenan, *Duskers*); a demo that ends abruptly loses the players a closing scene would have kept; small teams
seldom keep a Machinations graph beside the code, because the real numbers live in ScriptableObjects, Godot's
resources or JSON tables, so the economy's map should read the repository's configs. It proposed the loops as
concentric rings under the pillars, each card tied to its scenes and scripts; a second map (the currencies with their
sources and sinks read from the configs, a delta along the progression, and a flow curve with the players' deaths and
quits from PostHog or GameAnalytics laid over the designed difficulty), badges (*Currency Inflation* when a currency's
sinks vanish late in the game), a peak marked where players drop in the first fifteen minutes or at the demo's end,
and on the phone a playtest's summary. Measured against what is built (§156.3's loops one in another, each step tied to
the files it rests on, its feeling and intensity the designed curve; the currencies with what gives and takes them;
hooks D1, D7, D30; spec 109's `no_source`, `pile_up`, `no_reward`, `unfed`, `flat`; the leader reading the balance
configs), the map is the one we have. So:
1. **Loop stays the one map, laid out as today**: no rings (words along arcs read badly, the space is lost, a narrow
   width breaks them; `feeds` already says which loop feeds which) and no second map.
2. **The hooks by how the game earns**: the brief's *earns* (*How it earns*, spec 124) chooses them. A game sold once
   (Steam, a console, itch) has **the demo's end** (what makes a player wishlist it), **the first two hours** (Steam
   refunds a game played under two hours and bought under fourteen days ago) and **the ending**; a free game with
   purchases or ads keeps D1, D7, D30. The leader proposes the hooks that fit; zero to three as today, a hook's `when`
   one of the six.
3. **The pillars over the loop**: the brief's *pillars* and *leaves_out* lie as thin strips along the map's top edge,
   read from the brief, never kept twice; Game design's leader judges a step and a goal against them in its look and in
   Talk, as §210.3 (a concern that quotes the pillar, never a block).
4. **A currency rests on its config, and its change is seen**: a currency gains `rests_on` (the config files its
   numbers live in: a JSON or YAML table, a Godot `.tres`, a Unity ScriptableObject's `.asset`), checked against dev's
   tree as a step's are. A currency whose file changed since the person's last look says so on its card, with the goal
   that changed it (*Changed by <goal>*): an agent that quietly changed what a repair costs is seen. The numbers
   themselves are not parsed by code: every game keeps them its own way.
5. **Not taken now**: the inflation of a currency late in the game (it needs a simulation along the progression;
   `pile_up` keeps the static case); the flow curve with the players' deaths and quits, and a playtest's summary on the
   phone (the project's analytics are not read yet: the later spec of spec 115, PostHog or GameAnalytics among them).
6. **The look is orkUI's and the words plain**: the tokens alone; *Scrap is only earned: nothing takes it*, never
   *Currency Inflation*.
7. **The evidence is asked for before the spec**, as §208.7: the survey's figures and the post-mortem it speaks of,
   named. The spec builds 2–4 with §208's, §209's and §210's.
The owner's call.

## 212. The Art lens measured against how small teams keep their assets: the placeholders found, the look's anchors over the map, the loudness measured against the game's target (2 November 2026, the owner)

Changes: 88, 109, 210.

Why: the same research as §208, for Art (a prompt to Gemini, its answer unsourced and so taken as a hypothesis). What
it said: in a game one thing (a ghost, a weapon, a menu) is worked on at once by code, art, animation and sound, so a
relay board (design, code, art, QA) or a board per craft loses the thing whole; a solo developer cannot write code and
draw final art in one sitting, so the way that works is to code on **placeholders** and keep a plain register of what
is still to be replaced; Codecks' *hero cards* and *journeys* give a thing's card its sub-cards for code, sprite or
mesh, animation, dialogue and sound; a small team seldom does the long capture of the master bus that console
guidelines ask for, and Wwise 201 reads loudness **relative to the project's target** (the target is 0 LU, a sound
*+3 LU* above it) rather than as an absolute *−23 LUFS*. It proposed the art bible's anchors along the top (the palette,
a reference sprite with its grid, the audio target: −24 LUFS for PC and consoles, −18 for mobile and handhelds, true
peak −1 dBTP), the game's things as hero cards with slots *Code*, *Sprite/Mesh*, *Anim*, *Audio*, *VFX* (dashed where
a placeholder stands); a second map (a treemap of the build's weight on disk and in VRAM, and the audio groups on a
scale centred on 0 LU with their range, LRA); signals for a placeholder on a release scene, a budget broken, a sound
over the true peak or off the target by more than 2 LU; and on the phone a feed of the newest assets to accept.
Measured against what is built (spec 88's assets in lanes by kind with their variants under a pick; spec 109's aspects
*Style, Pipeline, Budget, Sound* and the hints `mixed_sizes`, `naming`, `heavy`, `unused`), the map is the one we have;
what is missing is the placeholders and any measure of sound. So:
1. **Assets stays the one map, in lanes by kind.** No second map, no treemap (`heavy` says what weighs; the memory a
   picture takes on the card is not read from the repository).
2. **The placeholders found** (`placeholder`, a new hint in *Pipeline*): an asset whose name or folder says it is
   temporary (`placeholder`, `temp`, `tmp`, `wip`, `dummy`, `todo`, as a word of its path), or an engine's default
   picture standing where art should (Godot's `icon.svg` named by a scene or a script other than the project's own
   settings). Its words say where it is used. **Release counts them**: a goal waiting for main that brings or keeps a
   placeholder in a file its changes touch says so in Release's *Readiness* (*3 placeholders go to main*). Agents
   make placeholders too, so the register is kept by code, never by hand.
3. **The look's anchors over the map**: the person may mark up to three assets as **the look** (a key sprite, the
   palette, a frame of the game); they lie as thin strips along the map's top edge, as the pillars do (§210.3,
   §211.3). Art's leader reads them beside the newest pictures in its look and judges new art against them (*Style*):
   the art bible as three files marked, not a document.
4. **The loudness measured against the game's target** (`loud`, a new hint in *Sound*), when `ffmpeg` is on the
   machine (its `ebur128` filter; with none the hint is silent, as any hint that cannot be read): only a sound of
   LOUD_MIN_S seconds or more (music, ambience, a voice; a short effect's integrated loudness says little). The target
   by the platform the brief names: −24 LUFS for a computer or a console, −18 for a phone or a handheld; the true peak
   at most −1 dBTP. A sound off the target by more than 2 LU, or over the peak, says it **relative to the target**, as
   Wwise reads it: *boss.ogg is 4 LU louder than the game's target*, never the absolute number alone.
5. **Not taken**: hero cards with slots (a thing worked on by several crafts at once is a **goal** already, its tasks
   in different parties, spec 59; guessing a thing from its files' names and drawing its empty slots would lie: not every
   thing has a sound); the loudness of buses and the range of loudness (a bus exists only in the running game); a feed
   of assets on the phone (accepting an asset is a decision, a *look* card in the hand as today).
6. **The look is orkUI's and the words plain**, as §208.6.
7. **The evidence is asked for before the spec**, as §208.7: the solo developers' words on placeholders, Codecks'
   pages, the Wwise course and the platform's loudness guideline, named. The spec builds 2–4 with §208's to §211's.
The owner's call.

## 213. The Release lens measured against how small teams ship: readiness gathered from every lens, a save broken by a patch, strings not translated, the changes drafted by Keep a Changelog, and a game not yet out on its own rhythm (2 November 2026, the owner)

Changes: 90, 109, 137, 212.

Why: the same research as §208, for Release (a prompt to Gemini, its answer unsourced and so taken as a hypothesis; its
*stress-free launch* is Codecks' own advertising, not a post-mortem). What it said: before a release a small team is
under the most strain, and one thing forgotten (a button the Steam Deck cannot press, a demo that ends abruptly) costs
wishlists and sales; milestones with the commits tied to their cards carry a launch through; DORA's four keys fit a
project by its kind: a web app's way to production, a game's rhythm of internal builds (dev, a playtest branch), the
project buildable and runnable at any moment. It proposed a bridge of three cards (dev with its changes sorted live by
Keep a Changelog's *Added*, *Changed*, *Fixed*; a *Go / No-Go* gate holding a check from every party: the build and a
smoke test from Tech, the controller and the screens' states from Design, no placeholder and no clipped sound from Art,
the saves' compatibility by semantic versioning and the store page from Marketing; main with the live version), a
second map (four DORA cards with a trend line of four weeks each: build cadence, commit to playable, broken builds,
recovery), a red *NO-GO* with a thread to the card at fault when one check fails (a save broken in a patch, new strings
not translated), and on the phone the release candidate with its gate and its patch notes approved in one tap.
Measured against what is built (§137's map, the goals in dev and not in main ticked, *To main* by the gate's merge,
*Since <version>*; spec 109's `big_batch`, `stale`, `no_changelog`, `reverts`; the gate's checks; spec 90's hand card
*n goals ready for main*), the map is the one we have. So:
1. **Dev and main stays the one map.** No bridge of three cards (the map is dev against main already), no second map of
   DORA cards with trend lines (a dashboard of counts; the aspects *Batch size*, *Lead time*, *Change failure* are
   there).
2. **The gate and readiness are two things**: the **gate** is the tests, red and hard, the one thing that stops a merge;
   **readiness** (*Readiness*) gathers the hints of every lens on the files that go to main (Art's placeholders,
   §212.2; a sound off the target, §212.4; a screen's state not found, §209.2; a currency's config changed, §211.4;
   and the two below), each naming its lens and opened on that lens's card. Readiness never turns the merge red and
   draws no *NO-GO*: the person weighs it, in the hand.
3. **A save broken by a patch** (`save_change`, a new hint in *Readiness*): a file that keeps or reads the player's
   save (a path word `save`, `savegame`, `persist`, `serializ…`) changed among the commits waiting for main. Its words:
   *The save's format may have changed: players' saves from <version> may not load.* By code; the leader judges it.
4. **Strings not translated** (`untranslated`, in *Readiness*): where the project keeps translations (`locales/` or
   `i18n/` JSON or YAML, gettext `.po`, Godot's translation CSV), the keys of its first language that another language
   lacks among what waits. Its words name the languages and the count.
5. **The changes drafted by Keep a Changelog**: the goals waiting are sorted under *Added*, *Changed*, *Fixed* by their
   type (`realm/goal_types.py`); the draft rides on the hand's card *n goals ready for main*, the person edits it and
   it lands in `CHANGELOG.md` with the merge. The words for players (a store's patch notes) stay the *Release notes*
   agent's.
6. **A game not yet out on its own rhythm**: while no version is out (*Since* has none), `stale` and `big_batch` are
   silent (dev is where the game lives until its first release); Release's question is then whether dev builds and
   runs (the gate's last run on dev), and its *Lead time* is to a playable dev, not to main.
7. **Not taken**: a view of its own on the phone (the release candidate is the hand's card, with its draft, as 5).
8. **The look is orkUI's and the words plain**, as §208.6.
9. **The evidence is asked for before the spec**, as §208.7. The spec builds 2–6 with §208's to §212's.
The owner's call.

## 214. The Marketing lens measured against how small teams are found: the Steam page read as the store, the app's hints silent for a game sold once, the positioning whole over the map, one or two channels in focus (2 November 2026, the owner)

Changes: 109, 124, 151, 210, 211.

Why: the same research as §208, for Marketing (a prompt to Gemini, its answer unsourced and so taken as a hypothesis;
its figures for *The Last Cat in the Universe*, 4,500 wishlists at launch and 4,000 copies sold in the first week, are
unlikely, a first week usually selling well under the wishlists, and are checked first). What it said: for a small team
marketing is where time is burnt and wasted: short videos for YouTube and TikTok cost much and moved few wishlists,
while personal ties with streamers, bundles with other indie games and a demo's ending carried the launch; April
Dunford: a product fails at the door when it keeps the category of its first day and looks a weak copy of the leader,
instead of starting from what only it has and the value that gives a segment; Gabriel Weinberg's Bullseye: most
companies cannot make one channel work, one channel at the centre is enough, and spreading over several at once fails.
It proposed the way in as one chain (Dunford's five cards, then a card of the live store page with its capsule, the
trailer's date, the first four screenshots, the short description and the tags, then AARRR's five cards of visits,
wishlists, a demo played over fifteen minutes, sales, reviews and bundles), a second map (three rings: at most two
channels at the centre with their conversion by UTM, up to three experiments in the middle, the other of the nineteen
channels frozen outside), signals (screenshots or a trailer older than the game's visual commits, a unique attribute
not in the trailer's first seconds or the store's text, work started on a frozen channel), and on the phone the week's
change in wishlists and sales. Measured against what is built (§151.7's way in, read by the files' names: channels, the
store's metadata from `fastlane` or a site's pages, the install, the first session; spec 109's hints `no_channel`,
`aso_title`, `aso_short`, `no_shots`, `no_onboarding`, `no_return`, `no_share`, `no_revenue`; spec 124's brief with
*Whom it is for*, *What hurts them*, *Why this, not what they use now*), the map is the one we have, but it knows an
app's stores alone: an indie game's store is Steam, and Steam's page is not in the repository. So:
1. **The way in stays the one map.** No rings, no second map, no funnel of numbers.
2. **The Steam page read as the store**: when the project names its Steam app (its id in the project's settings, or a
   `steam_appid.txt` in its tree), the store step holds the page as Steam's public store API gives it, with no key (the
   name, the short description, the capsule, the screenshots, the trailers, the tags, the release date), read at most
   once a day and kept as a snapshot. Nothing is sent to Steam but the id. A new hint `store_behind` (in the store's
   aspect): the game's screens or assets changed by STORE_GOALS goals or more since the store's screenshots last
   changed in the snapshots kept (*The store's screenshots are older than the game: 7 goals changed what players see
   since*). `aso_short` and `no_shots` read Steam's page too.
3. **An app's hints are silent for a game sold once**: by the brief's *earns* (as §211.2), `no_return` (a push, a daily
   reward, a streak), `no_share` and `no_revenue` (a payment library) say nothing of a game sold once on a store,
   where the store takes the payment and the player returns for other reasons.
4. **The positioning whole over the map**: Dunford's five are the brief's *Why this, not what they use now* (the
   alternatives) and *Whom it is for*, with three of Marketing's own records (spec 124's party records): **What only it
   has**, **What that gives them**, **Its shelf** (the category, a game's genre). The five lie as thin strips along the
   map's top edge, as the pillars do (§210.3). Marketing's leader judges the store's short description against *What
   only it has* in its look and in Talk (*What only it has is not said in the store's text*): a model's judgement.
5. **One or two channels in focus** (Bullseye): the person may mark up to two channels as the ones worked now (as
   §210.2's job); a new hint `spread` when goals at work reach CHANNELS_SPREAD channels or more beyond them (*Goals
   are at work on five channels; the focus is two*). With none marked it is silent.
6. **Not taken now**: AARRR's numbers, conversion by UTM and the week's change on the phone (Steam's wishlists and sales
   are Steamworks', behind a partner's key, and the project's analytics are not read yet: the later spec of spec 115);
   whether the trailer's first seconds show what only it has (it needs the video read: later); the field's practice of
   Steam marketing (a creator's outreach, festivals, bundles over short videos: Chris Zukowski's *How To Market A Game*
   among others) lives in Marketing's rubric for a game, never as a rule of the map.
7. **The look is orkUI's and the words plain**, as §208.6.
8. **The evidence is asked for before the spec**, as §208.7. The spec builds 2–5 with §208's to §213's.
The owner's call.

## 215. Run's and LiveOps' first map: a line of time with *Now* across it, a dated event that warns when its goal is not ready, what runs and where, and the players' numbers left for when they are read (2 November 2026, the owner)

Changes: 90, 109, 184.

Why: the same research as §208, for Run and LiveOps (a prompt to Gemini, its answer unsourced and so taken as a
hypothesis; its free tiers, Unity Cloud's fifty concurrent players in Relay, fifty thousand users a month, a hundred
thousand transactions and five gigabytes, change more often than anything and are not to be kept in code). §184.7 left
*Run's map of services and SLOs, LiveOps' calendar* for later; Run and LiveOps are the only crafts with no map, and
LiveOps is one of a game's six parties from its start (`party_recipes.GAME`), while most indie games run no server.
What it said: cloud servers cost a small studio too much and servers switched off for want of money kill a game, so
the indie stack is Steamworks' free peer to peer, servers on demand (Edgegap) or generous free tiers (Unity Cloud;
Photon Fusion or Nakama with PostHog, Sentry, Upstash, Cloudflare); an online game that does not reach its critical
mass in its first hour falls into matchmaking's death spiral (matches of the strong and the weak, players leaving,
waits without end); a spike in load or crashes almost always follows a patch, an event or a sale, so the stability
signals laid under the calendar show the cause at once. It proposed a line of time with *Now* across it (fourteen days
back, thirty ahead: the events, updates, streams and sales above; the four golden signals below, *Traffic*, *Errors*,
*Latency*, *Saturation*, from Sentry and the like), a second map (a monthly crash-free budget, a monitor of the free
tiers, the matchmaking's critical mass), a warning when an event comes within forty-eight hours and its assets are not
ready, and on the phone a pager (the players online, the budget left, the next event). So:
1. **The map is a line of time with *Now* across it**, Run's and LiveOps' alike: behind *Now* (about two weeks) the
   versions that went out (`realm/releases.py`'s, Release's), ahead of it (about a month) **dated events**: a launch, a
   demo in a festival, a store's sale, an in-game event, a content update, a stream. An event is a card put by the
   person or proposed by the leader, with its date and the goal it waits on; kept by the party, read by code. One line
   of cards along time, never a list or a calendar's grid.
2. **An event that warns when its goal is not ready** (`not_ready`, a new hint): an event within EVENT_DAYS days whose
   goal is not in main (*Next Fest is in 2 days and "the demo's ending" is still at work*). By code, from the Board.
3. **What runs and where**, only for a project that runs something: a strip along the map's top, by code, as the
   pillars lie on the other maps: spec 90's containers that serve (a server, a realtime stack) and the outside services
   the manifests and configs name (an error tracker, analytics, a game server or relay, a database, a host: Sentry,
   PostHog, Photon, Nakama, Supabase, Firebase, Steamworks' networking, `fly.toml`, `wrangler.toml` and the like, a
   list kept beside `stacks_known`), each with what it is for. A free tier's limits are the leader's knowledge, dated,
   in Talk; never a number on a card.
4. **Matchmaking in the rubric**: for an online game, LiveOps' leader (and Game design's before launch) asks whether
   there will be players enough for matchmaking in the first hour, and what holds it if not (bots, an asynchronous
   mode, crossplay): a judgement in the look and in Talk, never a part of the map.
5. **The players' numbers left for when they are read**: the four golden signals under the past, the crash-free budget,
   the free tiers' use and the matchmaking's critical mass need Sentry, PostHog and the services' APIs read; the line
   keeps their place under the past, filled by the later spec of spec 115 that reads them. No second map, and no pager
   on the phone: when they are read, a spike is a card in the hand or a push, never a view of its own.
6. **The look is orkUI's and the words plain**, as §208.6.
7. **The evidence is asked for before the spec**, as §208.7. The spec builds 1–4 with §208's to §214's.
The owner's call.

## 216. The Orkmaster measured against the game trackers: a dated event is the milestone, the scope's drift said in words, a decision in the hand when the date is lost, goals the milestone does not wait on (2 November 2026, the owner)

Changes: 167, 206, 210, 215.

Why: the same research as §208, for the Orkmaster (a prompt to Gemini, its answer unsourced and so taken as a
hypothesis). What it said: in Codecks (a card-based tracker made for games) a card goes down a funnel of growing
commitment, a deck, a milestone (*what we ship, and by when*), a run (*this week*), a person's hand (*what I take
today*, at most seven), started, and a solo developer skips the steps between; the threat at the project's level that
trackers ignore is **scope drift**: cards added all the time turn a plan of three months into eighteen, and the
Orkmaster should watch it by itself. It proposed a round table (the milestone in the middle with three to five hero
cards and bars of their tasks, the parties' sectors around it, each with a fan of one to five cards at work), whose hand
a card is in drawn by its outline, a second map (the milestone's budget of scope against what was added, the cards
that broke it, the stuck ones in Codecks' *Beast Mode*, the ones blocked between parties), a hand over seven cards
glowing and refusing more, and on the phone a stand-up console with the sprint's health. Measured against what is
built (§206's Orkmaster's column pinned at the left, three piles of whole cards, *In analysis*, *To review*, *At work ·
later*; §167's goal on the table, in the hand or in the discard; §207's steps of a task; our hand being *what the person
decides*, not Codecks' *what I take today*), the frame stays, and what is missing is a milestone and its drift. So:
1. **The frame stays**: no round table, no sectors (the first lane is pinned and the leaders are tabs, §206); whose a
   goal is shows by where it lies (the table, the hand, the discard), never by an outline; no limit on the hand and no
   refusal (our hand is the person's decisions); a goal stuck is §207's steps; no second map; no health or count on
   the phone, whose hand is already what waits for the person.
2. **A dated event is the milestone**: §215's event, its date and the goals it waits on (*The demo for Next Fest, 10
   June*), is the milestone; no new kind of thing. The Orkmaster, saying *what and who*, sets it with the person; a goal
   is tied to it as to an event.
3. **The scope's drift said in words** (`drift`, the Orkmaster's hint): for a milestone, the goals tied to it since it
   was set, the ones done, and the pace of the last DRIFT_WEEKS weeks (goals done a week); when at that pace it lands
   after its date the Orkmaster says so (*Since the demo was set, 14 goals were added and 6 done: at this pace it lands
   5 weeks after its date*). By code; a concern in words, never a scale, a bar or a count on the table.
4. **A decision in the hand when the date is lost**: the drift's concern comes to the hand as a card, its answers *Put
   these off*, *Move the date*, *Keep it*; the Orkmaster proposes the goals to put off, those that least serve the job in
   focus (§210.2) or the milestone.
5. **Goals the milestone does not wait on** (`off_milestone`, of the kind of §210.2's `off_focus`): with a milestone
   set, goals at work tied neither to it nor to the job in focus (*4 goals at work that the demo does not wait on*).
6. **The look is orkUI's and the words plain**, as §208.6.
7. **The evidence is asked for before the spec**, as §208.7 (Codecks' own pages and the teams' words on scope drift).
   The spec builds 2–5 with §215's.
The owner's call.

## 217. The product's voice: one door for the project, many owners; a signal goes to the lens where its place on the map is, LiveOps keeps time, the talk with players, what no one else takes and the fire now (2 November 2026, the owner)

Changes: 115, 206, 210, 215.

Why: the owner, after what Codecks teaches (players' bugs and words land on the board from Discord and the game
itself): where do the crashes (Sentry, Firebase Crashlytics), the product's analytics (PostHog and the like) and the
players' words (Discord, Steam reviews, a form in the game) come in? Into LiveOps, there is one way in; but then one
party holds the code's crashes, the product's numbers and the players' words, and each craft's leader judges its own
better. The two questions are apart: **where a signal comes in** and **who judges it**. Spec 115 already answers the
second for Play: what the probe sees is shown in the lens of the party whose aspect it is. So:
1. **One door, the project's**: the sources are connected once, in the project's settings, never inside a party
   (their tokens in the keychain's `orkcraft-ideas`, as every secret). The person need not know whose a signal is to
   connect it.
2. **Many owners: a signal goes to the lens where its place on the map is**:
   - a crash or an error → **Tech**, on the System part its stack's top file belongs to (a file to its part, as
     `realm/play_place.py` takes an element to its parts);
   - where players drop (a funnel, D1) → **Product** for an app, **Game design** for a game, on the screen or the
     loop's step where they leave;
   - the store's visits and wishlists → **Marketing**, on the way in's step;
   - a player's words: a bug → **Tech**; the interface, *I don't get it* → **Design** (a game has none: **Art** for the
     look, **Game design** for what it asks of the player); balance, *boring*, *too hard* → **Game design**, on the
     loop's step or the currency; *I wish…* → **Product**, at the job it serves on the tree.
   The numbers are sorted by code, by rule, as hints; the words by a model, as the Orkmaster routes a goal (§206.1).
   Words about one thing are **one concern pinned once**, with how many said it and a few of their words quoted as
   written, never a card each.
3. **LiveOps keeps four things**: **time** (§215's line: under a patch or an event the line of crashes and players, so
   *when* and *after what* it broke shows; Tech judges the cause, LiveOps sees its time); **the talk with players**
   (answering on Discord, the patch notes that say *we fixed what you wrote*: the voice going out); **what no one else
   takes** (a signal the model cannot place, or one whose party the project has not, goes to LiveOps, never to the
   person's hand); **the fire now** (a spike of crashes after a release: LiveOps brings it to the hand as a card, *Roll
   back* or *Fix it*, the person's decision). An app's project has Run in LiveOps' place.
4. **Only decisions reach the hand**: a signal is a leader's concern on its map; a member never asks the person
   (decisions §104.0); the hand gets what needs the person, as every concern.
5. **The players' words keep their words**: quoted as written, never retold in the Board's wording; what identifies a
   player (a name, an id) is not kept beyond the source's own link.
6. **The look is orkUI's and the words plain**, as §208.6.
7. The spec that reads the sources is spec 115's later one (Sentry, Crashlytics, PostHog, GameAnalytics, Discord, Steam
   reviews); this decision is its routing. Steam's wishlists and sales stay behind Steamworks' partner key (§214.6).
The owner's call.

## 218. Where Orkboard stands after the field was measured: the maps are what is ours, the indie game developer with a day job is whom it is for, the phone is half the product, the engines come first, nothing is promised before it is built (2 November 2026, the owner)

Changes: 95, 208, 209, 214.

Why: a market research (a prompt to Gemini with strict rules on sources; its answer, with first sources and dates, is
the best of the series, its vendors' own claims marked as such) checked four claims against 26 products: the agents'
runners (Conductor, Vibe Kanban, Sculptor, Multica, Cursor, Claude Code, Codex, Devin, Factory, OpenHands, Jules,
Copilot), trackers with agents (Linear, Jira with Rovo), companies of agents (MetaGPT, ChatDev, CrewAI,
Claude-Code-Game-Studios, Turnstone), game trackers (Codecks, HacknPlan), AI for games (Unity AI, Rosebud, Ludo, Bezi)
and code's maps (CodeSee, Swimm, Sourcegraph, CodeScene). Its verdicts: **H1, each craft's own map of the project read
from the code with its rubric, holds wholly**: every company of agents makes a role a prompt; CodeScene maps Tech
alone; CodeSee closed in 2024. **H2, standing roles for the whole product, holds in part**: Claude-Code-Game-Studios
(open source, said to be past 25,000 stars, living in the repository) keeps 49 roles from game design and art to
release and LiveOps, reads Godot, Unity and Unreal, and has `/balance-check`, `/asset-audit`, `/launch-checklist`; it
has no Marketing and no map. **H3, the person only decides, holds in part**: the idea is said by others (*you still make
every decision*; Multica's inbox that pings only for a call), our way of it (a hand of decisions, no chat with a member)
is ours. **H4, the indie game on Steam, holds in part**: the engines and a release's checklist are there; Steam's
refund window, Next Fest, the Deck, the placeholders and the loudness are not. The platforms are taking the running of
agents (worktrees, teams of agents, a phone that pings). The owner, on the phone: an indie developer most often has a
day job, and wants to turn to their own project for a few minutes during the day. So:
1. **The maps are what is ours**: each craft seeing the project its own way, read from the code, judged by its craft's
   rubric, is the one claim no product shares. The work goes there first. The running of agents (worktrees, parallel
   tasks, the tools' adapters) is kept working and well, but is not where Orkboard means to be ahead.
2. **Whom it is for: the indie game developer with a day job**. Their project works while they are at work; they turn
   to it in a few minutes between other things, and decide.
3. **The phone is half the product, not a remote**: it is where that person decides during the day. What it holds is
   what a few minutes need: the hand (the decisions, each answerable in under a minute, with the map's part it is about
   shown small beside it) and **what changed since your last look** on each lens, said in a line each, with the goal
   that changed it. It is not a terminal of agents (that is what the platforms' phones already do) and not a whole map.
   Measured: a decision taken on the phone, and the time it took.
4. **The engines come first** (§208.5, §209.5): Godot, Unity and Unreal read for System and Screens before any new hint;
   without them an engine's game gets empty maps, and Claude-Code-Game-Studios already reads them.
5. **Steam and Marketing early** (§214): no product reads a game's Steam page or keeps a Marketing party with a map;
   §214.2–§214.4 come right after the engines.
6. **Nothing is promised before it is built**: the README and the store's words say the maps and the hand as they are;
   Steam, the loudness, the refund window and the Deck are named only once they work. The line it stands on: *Orkboard
   shows each craft's leader your game as a map read from its code (the system, the screens, the loops, the assets) and
   brings you decisions, not a chat.*
7. **The models' rules are kept, not worked around**: a model may refuse to recreate an existing game; an original game,
   a genre and a mechanic described in its own words are made as ever. That Orkboard runs Claude Code, Codex and
   Antigravity gives a choice of model and of price; it is never said to be a way round a vendor's rules.
8. **Claude-Code-Game-Studios as a neighbour, not a rival**: its knowledge is in text files, ours is the maps and the
   hand. A project that uses it is to open in Orkboard with its agents read as members of the parties, once its licence
   is read and allows it.
9. **Checked before it is relied on**: Claude-Code-Game-Studios' licence, its stars, whether it has a Marketing role;
   Conductor's *100,000 users* (the vendor's own).
The owner's call.

## 219. The phone's app comes up the line; away from home the hand goes through a sealed mailbox (Cloudflare Durable Objects behind our own `mailbox`), push through FCM; Tailscale stays an optional way to the whole Board, which is the app's next wave; a sleeping computer and what the mailbox sees are said plainly (3 November 2026, the owner)

Changes: 174, 180, 218; spec 34, spec 103.

Why: after §218 (the indie developer with a day job, the phone half the product) the owner asked whether the phone needs
a full native app rather than the PWA, then whether Tailscale can be replaced with no loss of safety, whether the relay
could be Firebase, and which of Google, Amazon and Microsoft fits by price and by what it can do. What was found: the
native frame is already decided (§174, spec 103: Capacitor round the one page, iOS first) but not built (no `mobile/`);
an installed web app on an iPhone has no action in a notification, no widget, and push only once added to the home
screen, the three things a few minutes at work rest on; and today the phone reaches the computer only on the same
network or through Tailscale on both (spec 34), while §174's relay carries push alone, so away from home a
notification arrives and cannot be answered without Tailscale, which a work phone may not allow. The trust is already
made at pairing: the phone pins the computer's certificate from the QR on its screen, so what carries the bytes need
not be trusted. Measured for our load (a computer on line all day and quiet, a phone or two now and then, small
messages): Firebase's Realtime Database is a mailbox with a good SDK but no stream, under Google's SDK and rules;
Amazon (API Gateway's WebSockets with Lambda and DynamoDB, or IoT Core) fits but is several services and IAM to keep;
Microsoft's Web PubSub has a paid unit a day whatever the load and no queue of its own, its Notification Hubs no public
price; Cloudflare's Durable Objects give one object a pair (a mailbox, its WebSockets, its storage, its alarms), an idle
hibernating connection billed by no time, and can later splice a stream. So:
1. **The native frame comes up the line**: spec 103's `mobile/` (Capacitor, iOS first, then Android) is built beside the
   engines (§218.4), the two sharing no file. Capacitor stays: the page is the one face (a React Native or Flutter app
   would be a second one); native code only where the page cannot (opening a sealed push, the widgets, a notification's
   actions, the orientation).
2. **Away from home, the hand through a sealed mailbox**: the phone's hand (its answers, a small snapshot of the hand,
   the lines of *what changed since your last look*, §218.3) goes through a mailbox of ours, each message sealed end to
   end with keys made at pairing (libsodium: X25519 and XChaCha20-Poly1305 or Noise, never our own crypto), a counter
   inside the seal against replays. The computer opens no port for it: it holds an outgoing connection. **A message waits
   while the computer sleeps** and is taken when it wakes, then deleted (an alarm deletes what is left after
   MAILBOX_TTL); nothing is kept beyond its delivery.
3. **The mailbox is Cloudflare Durable Objects, behind our own interface** (`mailbox`: put, take, delete, present): one
   object a paired computer and its phones; only a pair registered at pairing gets in (the phone proves it by the key the
   pairing gave it), with limits, so it is never a free tunnel; a phone removed from the paired list is cut from the
   mailbox at once. Firebase is the way back if Cloudflare fails a region or a price; the interface keeps the change in
   one module.
4. **Push through FCM** for Android and iOS (FCM delivers to iOS through APNs); §174.5's checks stand (the push sealed to
   the device, signed by the paired computer, checked before it is passed on), done by the same Worker, so the relay of
   §174 and the mailbox are one service of ours.
5. **Tailscale stays an optional way to the whole Board**, direct, as spec 34 has it. **The whole Board away from home
   is the app's next wave**: then the same Durable Object splices the phone's and the computer's streams and the
   pinned TLS runs through it untouched (a blind relay, as TURN is); not before the hand works through the mailbox.
6. **Said plainly**: in Settings, *Away from home your phone talks to this computer through Orkboard's relay; what it
   carries is sealed, the relay sees only that you are in touch, and keeps nothing*; and on the phone, when the computer
   is not present, *Your computer is asleep or offline: work waits, your answers will reach it when it wakes*. Settings
   offer to keep the computer awake while work runs.
7. **Checked before it is built**: Cloudflare's and FCM's reach in the countries of the people it is for; the prices on
   the official pages (Durable Objects' requests and duration, FCM's none); Apple's and Google's accounts (about $99 a
   year, $25 once).
8. The spec builds 1–4 and 6 (spec 103 widened: the relay part becomes the mailbox's Worker); 5's stream is a later spec.
The owner's call.

## 220. What a project is built with: Play's contract is a web build made from the command line, Godot the engine best seen, a canvas marked by its coordinates, Play's proxy cross-origin isolated, a device before a release (3 November 2026, the owner)

Changes: 193, 208, 209, 213; spec 115.

Why: the owner asked whether Orkboard should offer cross-platform engines (Flutter, Unity, Godot) so that no Android or
iOS emulator need run. What spares the emulator is not being cross-platform but **a web build the agents can make with
no window and Play can open** (spec 115: Play is the machine's web preview; the probe, a task's pictures and the marks
live there); and the maps are read from the code (§208.5, §209.5), so a project read as text is seen better. Measured:
a web stack (React, Phaser, PixiJS, Three.js) builds natively and its DOM shows the probe everything; Godot exports
from the command line (`--headless --export-release`), its scenes and scripts plain text (`.tscn`, `.gd`), but draws on
a canvas; Flutter builds for the web (`flutter build web`), on a canvas, with a semantics tree when asked for; Unity
needs its editor and a licence in batch mode, its WebGL build takes minutes, its scenes are large YAML of GUIDs with
`.meta` files beside them, on a canvas; a native Swift or Kotlin app has no web build, so no Play. So:
1. **Play's contract is a web build made from the command line**: a project gets Play when its agents can build it for
   the web with no window and the build serves a page; not by its engine. A project without one is told so, with the
   engine's own way to add it (*Play needs a web build: add a Web export* and the line for Godot, Unity, Flutter or Expo).
   A native app is told plainly that Play and the live checks are not there for it, the other maps are.
2. **Godot is the engine best seen**: free, built from the command line, its project plain text, so its maps are the
   fullest; §208.5's and §209.5's engines are built Godot first, then Unity, then Unreal. Godot 4's C# does not export to
   the web: a C# project has no Play until it does, and is told so.
3. **Said at the start, never forbidden**: a new project hears *Orkboard sees web projects and Godot best; Unity and
   Flutter work, with some checks not there*; the person chooses.
4. **A canvas is marked by its coordinates**: an engine drawing on a canvas has no DOM elements, so on it §209.4's focus
   path and contrast and spec 115's marks held by an element are not there; a mark is held by its place on the canvas
   and the moment, with the screen's picture. A Flutter web build is built with its semantics tree on, and the probe
   reads it as elements where it is.
5. **Play's proxy is cross-origin isolated** when the build asks for it (`Cross-Origin-Opener-Policy: same-origin`,
   `Cross-Origin-Embedder-Policy: require-corp`), as Godot's threaded web export and other WebAssembly builds need
   (SharedArrayBuffer); Godot's single-threaded export needs none.
6. **A device before a release, in Readiness** (§213.2): the daily loop needs no emulator, but a release to phones asks
   for a run on a real device (touch, permissions, speed; an iOS build needs macOS with Xcode), and one to Steam for a run
   of the Linux build where the Deck is meant; Readiness says *Not yet run on a device* until the person ticks it.
7. **Checked before it is built**: Godot's web export of C# in its current version; Unity's batch-mode build without a
   paid licence; Flutter's semantics tree in its web build.
The owner's call.

## 221. A goal dropped from the phone: through the mailbox; the Orkmaster's reading at once on Seasoned, the leaders' sections and plan on Veteran when the limits allow; the join raised to Veteran only on a sign; work stops before reading does; where it went said in a line (3 November 2026, the owner)

Changes: 121, 180, 206, 216, 218, 219; spec 94, spec 100.

Why: the owner: *this is how work from the phone should go: the person drops a goal, it goes through its first reading
and into line, and its making may wait, for the limits for one*; then: do the leaders not need Veteran models to write
a good spec, and does the Orkmaster need one at all, when it only passes a goal to the right leaders and checks that
their decisions agree? `realm/idea_target.py`'s `MATRIX` already answers most of it: on *balance* the Orkmaster's
`route`, `decide`, `join` and `collide`, and Talk's rounds and verdicts, run on Seasoned; a leader's first section
(`section_first`), its reading of a goal (`goal`) and its plan on Veteran (about $0.18–0.22 a call, spec 86 §5). The
interface was read for this way: the phone's + card takes a goal with its rune, its leader, its type and its files
(`js/hand/pluscard.js`; the page has no microphone, the native frame's widget will, §174.7); the route card is dealt to
the hand as soon as the Orkmaster has routed it, with its cost and **Talk**, and **Later, by itself** when the limits run
low (`js/hand/routecard.js`); a hearing is lifted on a phone in the middle (`js/hand/hearing.js`); the computer's sleep
is a setting of three modes (`js/shell/settings.js`). What it lacks: upright the phone is the hand alone (§180), so once
Talk is pressed the person sees nothing of where the goal went, nor that its work waits for the reset; with no signal
the phone says *Cannot reach the board: is it running, and Tailscale on?* (`js/linkpaired.js`) and takes no goal; and
analysis waits on the route card's press. So:
1. **A goal from the phone goes through the mailbox** (§219.2), as an answer does: sent sealed, taken when the computer
   wakes. With no signal the + card still sends; the phone says *Your computer is asleep or offline: the goal will reach
   it when it wakes*, never the Tailscale line (which stays only for the whole Board, §219.5).
2. **The Orkmaster's reading at once, on Seasoned**, as today (`route`): the route card comes to the hand with whose the
   goal is and what it costs. The Orkmaster stays on Seasoned for routing and joining; a Veteran is not its seat's.
3. **The leaders' sections and plan on Veteran**, as today; they run at once when the limits allow, else after the reset
   and before any work, said on the route card (*Read after the reset, Mon 09:00*).
4. **The join raised to Veteran only on a sign**: `join` runs on Seasoned unless code finds a reason, then once on
   Veteran: two sections touch the same parts or files; a leader doubted or said no in Talk; a concern quotes a pillar
   (§210.3, §211.3); the route has three parties or more.
5. **Work stops before reading does**: when the week's limits run low the work waits first (its threshold
   WORK_FLOOR), the Orkmaster's reading and the leaders' sections go on to a lower one (READ_FLOOR), so a goal dropped at
   the week's end is read and costed, and only its making waits. A setting says it plainly: *Keep for reading new goals:
   10% of the week*.
6. **Reading on another tool, only if the person said so**: when one tool's week runs low, the reading and the sections
   may run on another tool's Veteran (Codex, Antigravity) if it is connected and the person turned it on (*Read goals
   on Codex when Claude runs low*); never by itself, since a spec's quality differs by model.
7. **Talk by itself under a cost the person set**: the route card waits for its press, as the money rule asks
   (§121.3), unless the person set a ceiling (*Start Talk by itself up to 2% of the week*, off at first); then a goal
   dropped and left is read through and its questions come to the hand.
8. **Where it went, in a line**: the phone's *what changed since your last look* (§218.3) says each goal's place in one
   line (*"The double jump": Game design and Tech, about 6 calls, starts by itself after the reset, Mon 09:00*); a push
   only for what needs the person (a question of Talk, a hearing, a decision), never for a goal put in line.
9. **After the reset, the line in order**: the goals a milestone waits on first (§216.2), then those that serve the job
   in focus (§210.2), then the rest in the Orkmaster's order.
10. The spec builds 1, 3–5, 7–9 with §219's (the phone and its mailbox); 6 when a second tool is connected.
The owner's call.

## 222. The phone around a goal: the crown's menu is the Orkmaster's three piles, the leaders a row of heads at its foot; a goal in analysis is the person's own words to add to, rewrite or remove; a goal picked is its header, its waiting card and its leaders as tabs, each showing its slice of its map, now and as it will be; no table and no chairs on a phone (3 November 2026, the owner)

Changes: 195, 206, 219, 221.

Why: the owner, after §221: the phone's interface has to be remade around a goal: the side menu is the Orkmaster's
column, its goals grouped as a spec still being made, specs waiting for their making, specs being made (the first not
pickable); a goal picked closes it and a header shows the goal (its rune, its cost and the rest); under it the faces of
the leaders working on it as tabs, and a leader picked shows its lens, as it was and as it will be; and, while a spec is
still being made, the person's own text can be edited, or the goal removed. Should the phone refer to the desktop's
table and chairs? What is built (§195, spec 117): the crown opens a sheet from the left (`js/hand/upmenu.js`) holding the
Orkmaster's goals and then each party with its goals at work; the middle shows a goal (its phases, its route, why, its
tasks) or a party (`js/hand/upparty.js`: its header, squad, tools, concerns), the top card answered with one tap; and
§195.5 left a leader's map off the phone. The desktop already shows a goal picked as each leader's view of what it will
change (§206.4; `js/table/goalmap.js`, pure functions over the spec and the maps). So (this changes §195.1, §195.2 and
§195.5 for a phone; the desktop is unchanged):
1. **The crown's menu is the Orkmaster's column, three piles**, as the desktop's (§206.3): **In analysis**, **To review**,
   **At work · later**; no count anywhere, a way to look and never where something waits (§195.1 holds). The parties'
   groups leave it: **the leaders are a row of heads at its foot**, a head pressed opening that leader (its header,
   squad, tools and concerns, `upparty.js` as built), so the concerns of §208–§217 keep a home on the phone. At its head
   the project, *Settings* and *Stop all*, as built.
2. **In analysis is not pickable**: its goals lie face down, the one being read named (*Being read: "The double jump"*),
   so the person sees that a goal dropped arrived (§221.8). **A goal in analysis pressed opens the person's own words**,
   at the foot as a sheet, with three acts:
   - **Add to it**: a line added to the goal's text, taken by its leaders at their next step; nothing starts again, nothing
     spent is lost. It is the act offered first, since a goal is most often missing a word, not wrong.
   - **Rewrite**: the text edited whole; the reading starts again from the Orkmaster's. Once a leader has begun its
     section the sheet says what is lost (*The leaders began reading: rewriting starts again; about 2 calls spent so
     far*). Before the Orkmaster has read it (in the mailbox, or in line), rewriting costs nothing and says so.
   - **Remove**: *Press again to remove*, never a dialog; a toast with *Undo* for a few seconds; what was spent stays
     spent, and the sheet says it when anything was.
   Away from home the three go through the mailbox in order (§219.2), taken when the computer wakes. Once a goal has left
   In analysis a change to it is a change of the goal, asked as it is today, never this sheet.
3. **A goal picked closes the menu; its header** at the top: its element (its rune), its type's sign, its short name, its
   phase, its cost (*about 6 calls · 4% of Claude's week*, the gem's), and its start or wait (*Starts by itself in 3 h*,
   *after the reset, Mon 09:00*). **Its waiting card lies under the header**, answered with one tap (§195.2 holds), above
   the tabs: a decision before anything to read.
4. **The goal's leaders as tabs**, their heads in a row: first **the Orkmaster's** (the plan: the tasks by leader in their
   order, each task's steps, §207), then each leader of its route. **A leader picked shows its slice of its own map for
   this goal**, `goalmap.js`'s, drawn narrow: the parts the goal touches marked *new*, *changed*, *gone* or *read only*,
   its *Done when*, and the leader's concerns on those parts. **Now | Will be** is a switch, never side by side (the
   width), *Will be* first, while the goal is not yet in dev; **Before | After** once its changes land. A craft whose map
   the host does not read from the files yet (Product, Game design, Art) shows its *Will be* lines, plainly, until its
   map is read for a goal. This lifts §195.5 for a goal's slice; a leader's whole map stays off the phone.
5. **Away from home**: a goal's slice comes through the mailbox when it is picked, kept on the phone, and shown with its
   time while the computer is not present (*As of 14:02*); a screen's pictures as small ones (this widens §219.2 by the
   picked goal's slice, never the whole Board).
6. **No table and no chairs on a phone**: the same things, not the same room. The cards, the runes, the leaders' heads,
   the hand's fan, the discard and the potions are Orkboard's words and look the same on both; the wooden table and its
   seats are a room, which a six-inch screen pays for in space and gains nothing by. The heads as tabs are the seats.
   The table stays for a phone on its side, in the next wave (§219.5).
7. **The mockup** is `docs/mockups/phone/goal-lens.html`; the spec after the owner's look at it.
The owner's call.

## 223. The phone's two screens, one shape (this amends §222): the project's screen with the Orkmaster and every leader as tabs on top, a leader's tab its lens of the whole project; a goal's screen one level down; no side menu; one header with the bottle of the goal's tool; the hand between the + card and the die, the picked goal's question raised; the die faint, white or in the goal's rune (3 November 2026, the owner)

Changes: 121, 195, 206, 218, 219, 220, 222.

Why: the owner's review of §222's mockups (`docs/mockups/phone/goal-lens.html` v1, `goal-lens-v2.html`,
`goal-lens-v3.html`): in v1 the goal's header, its waiting card and the tabs took near half the screen and the slice was
left little; the owner asked the header be one row with the bottles as a picker (not all of them shown), the rune and the
type in it with the Orkmaster, the moon and the share; the leader's question a card of the hand raised above the others;
the foot as the desktop's, the + card at the left, the hand, the die at the right, the die white while the spec is still
being made and in the rune's colour when something of the goal can be run, so the person can start the build on the
computer from the phone and leave feedback; the discard into the menu; the menu the first screen when there is no goal;
then, seeing v2: the leaders on top of that screen, which is no longer a menu but the project's main screen, and the
moment to show the lenses of the whole project. A count of the other goals' questions in the menu was weighed and left out
(§67, §121.2, §174.6: no count of what waits). So:
1. **The project's screen**, when no goal is picked: its header (the project and its switcher, *Settings*, *Stop all*,
   the default tool's bottle); under it **the Orkmaster and every leader as tabs**, their heads, the open one named under
   the row. **The Orkmaster's tab** is the three piles of §222.1 and **Done** as their last pile (the discard leaves the
   header). **A leader's tab is its lens of the whole project**, made for a few minutes: **what changed since your last
   look** (a line a part or step, with the goal that changed it or *by you*), **its concerns by its rubric's aspects** (spec
   109 C's chips, each in its state; pressed, its cards), and **its map made small** (Tech's containers and parts as
   chips, Game design's loops and currencies, Design's screens as small pictures), the changed and the hinted marked.
   This gives §218.3's *what changed* its place and replaces §222.4's *a leader's whole map stays off the phone*: the map
   made small is on it; the desktop's whole map is not. A leader with no map yet (Run and LiveOps until §215's line)
   shows its lines and concerns.
2. **A goal's screen is the same shape one level down** (§222.3–§222.4): the goal's header, its route's leaders as tabs
   (the Orkmaster's the plan), each its slice, *Now | Will be*, *Before | After*.
3. **No side menu**: the crown takes a goal's screen back to the project's, on the Orkmaster's tab always, so another
   goal is two taps away as it was through a menu. This replaces §195.1's and §222.1's sheet; the frame's *no drawer*
   holds on the phone too. A face-down goal in analysis on the Orkmaster's tab opens the person's own words as §222.2.
4. **The first screen**: a card in the hand → its goal's screen (§195.2 holds, a push lands there); nothing to decide → the
   project's screen on the Orkmaster's tab; no goal at all → the Orkmaster's tab invites the first goal, the + card large,
   and says the leaders have already read the project: their tabs hold their first look, read from the code, before any
   goal.
5. **One header on a goal's screen**: the crown; the goal (its rune, its type's sign, its short name; under it its phase,
   its wait with the moon, its share as the gem); **the bottle of the tool the goal runs on**, its alert colour when low,
   pressed **a picker** of every tool's bottle (its 5 hours, its week, its reset; the goal's one marked; moving the goal's
   reading and making to another as §221.6 says it). No die and no discard in a header.
6. **The foot as the desktop's**: the + card at the left, the hand, the die at the right. The hand is a stack a goal
   (§121.2): **the picked goal's stack raised**, its top card the leader's question with **its pick one tap away**
   (*Half · Game design's pick*); the card pressed lifts with every answer (two taps for any other); the other goals'
   stacks as narrow spines (the rune and the card's sign); never a count. On the Orkmaster's tab a goal that asks
   shows the question sign on its row, never a number: the hand's mirror, not a place where something waits (this
   softens §195.1). With nothing raised the foot is lower.
7. **The die**: **faint** when nothing can be run (no web build, §220.1, or its last build failed); **white** when dev
   runs and holds nothing of this goal yet; **in the goal's rune** when a build that runs holds its change. Pressed it
   starts the project's own build command on the computer, said plainly, *Stop the build* beside it. At home on the
   computer's network the build opens on the phone and is marked as on the desktop (spec 115; Play's port on the local
   network only). Away from home the computer sends small pictures of the screens the goal changes through the mailbox
   (§219.2), and a mark is a place drawn round on a picture (§220.4); live play away is the next wave (§219.5).
8. **Away from home** a leader's lens of the project comes as a goal's slice does (§222.5): on request through the
   mailbox, kept with its time; Design's pictures small.
9. **The mockups**: `docs/mockups/phone/goal-lens-v3.html` (v1 and v2 kept beside it). Open in it, for the spec: the +
   card's side for a right thumb; the spines with or without short names; a lens's order (what changed or concerns first);
   the tabs' names under the heads.
The owner's call.

## 224. A header of four places on both of the phone's screens, the Orkmaster above the leaders; a spec in To review starts at a clock time, never by a countdown, and is held while it is being changed; a change to a spec is written to the Orkmaster, who passes it to the leaders it touches, and comes back as one card (3 November 2026, the owner)

Changes: 121, 195, 206, 222, 223; spec 128.

Why: the owner, before v4 of the phone's mockup: should the Orkmaster stand above the leaders in the header, beside the
project's or the goal's name, on both screens (though in v3's row of tabs it set the two screens apart); would a Back
button make the header jump; and, for the whole flow, not the phone alone: a spec waits in To review with a timer
between its making (the cards face down) and its work. Would the timer strain the person? Yet a spec the person does
not look at must start by itself. And a spec's feedback meant for several leaders at once has no way: §206.5 gives one
way to talk to a leader, and *Make it a change* is one leader's card (`js/hand/changecard.js`, `realm/leader_change.py`);
*more and more it seems a spec's improvements should go through the Orkmaster and its routing, not as questions to the
leaders*. On the desktop the Orkmaster is no tab among the leaders: its column is pinned, its head is its tab, *the tabs
at the top are the leaders' only* (§206.2). So (this changes §223.1–§223.3 and §223.5, §206.3's wait and §206.5 for a
goal's spec; the desktop follows in 3–6):
1. **The header has four places on both screens**, the crown and the bottle never moving: **up** (on the project's
   screen *Your projects*, the switcher; on a goal's, *Back to the project*), **the crown**, **the middle** (the project's
   name with *Settings* and *Stop all*; or the goal: its rune, type and short name, under it its phase, its start or wait,
   its share), **the bottle** (§223.5). Only the middle changes between the screens; the system's back (iOS's edge, Android's
   button) does what up does on a goal's screen.
2. **The crown is the Orkmaster's view of the level**, ringed while it is open: on the project's screen the three piles
   and Done (§223.1), on a goal's its plan. **The tabs are the leaders' only**, each head named under it: every leader on
   the project's screen, the route's leaders on a goal's. With no leader's tab open, the crown's view is shown.
3. **A spec in To review starts at a clock time**: *Starts by itself at 13:40*, a quiet bar with no number, and *If you
   do not look, it starts*; never a countdown in minutes, never a push that it is about to start (a line in *what changed*
   only). **The wait is by the spec's size and the person's setting** (*Give me time to look: 30 min · 2 h · until
   tonight · do not wait*), longer for a costlier spec. Its acts: **Change the spec**, *Start now*, *Later*. **Looking
   does not hold it; writing a change does**: from the first word until it is sent or closed, and while the change is
   being made, the spec is held (*Held while you write*, *Held while its leaders rewrite*).
4. **A change to a spec is written to the Orkmaster**, from the crown's view of the goal (the phone) or the Orkmaster's
   head on a goal picked (the desktop): before it is sent it says which leaders it will go to and its cost (*It goes to
   Tech, Art, LiveOps · about 3 calls*); the Orkmaster routes it (Seasoned, as `route`) to the leaders whose sections it
   touches; they rewrite them; the join joins them (raised to Veteran on §221.4's signs). **It comes back as one card**
   for the goal, raised in the hand: lifted, the person's words, then each leader's section as a tab with *Now* and
   *Proposed*, whether the sections agree, the cost, and *Accept*, *Talk more*, *Drop it*. Accepted, the sections and the
   person's decision are written into the spec, and **the wait starts again from the accepting** (a new clock time).
5. **One leader directly stays**: from its tab, or *@Tech* in the words, it is §206.5's change of one leader, as built. The
   Orkmaster's way is the default; the leaders' own questions to the person stay their cards in the hand (§221, §222).
6. **The person's words on a goal before its work, one sheet**: in analysis *Add to it*, *Rewrite*, *Remove* (§222.2); in
   To review *Change the spec*, *Start now*, *Later*; at work a change of the plan, as built (spec 128 E).
7. **The mockup**: `docs/mockups/phone/goal-lens-v4.html` (v1–v3 kept beside it). Open in it: the wait by size or one
   setting; one card for the change or a leader's card each; the wait after accepting from then or kept; and v3's own.
The owner's call.

## 225. One setting for a spec's wait; a change comes back as one card from the Orkmaster; accepting a change is the look, so the work starts at once when the limits allow (3 November 2026, the owner)

Changes: 121, 221, 224.

Why: the owner's answers to §224's open questions: one setting is simpler to understand than a wait by the spec's size;
the change should come back as one card from the Orkmaster; and after *Accept*, rather than a new wait, the work could
start at once when the limits allow. A wait by size cannot be told in advance (*why did this one start before that
one?*), and the spec's size is already said by its cost; a person who has read a change and accepted it has looked,
so a second wait asks for a look already given. So (this changes §224.3 and §224.4):
1. **One setting for the wait**, for every spec: *Give me time to look: 30 min · 2 h · until tonight · do not wait*, 2 h
   at first; the line under the start says it (*If you do not look, it starts: you give every spec 2 hours*). The wait by
   size goes.
2. **A change comes back as one card from the Orkmaster**: its asker on the card's face is the Orkmaster's crowned head
   (the change was routed and joined by it); the leaders whose sections changed are inside it, a tab each, *Now* and
   *Proposed*.
3. **Accepting is the look**: the act says what follows, **Accept and start** when the limits allow (the card already
   says its cost, so the money rule holds, §121.3); when they run low, *Accept · starts after the reset, Mon 09:00*, the
   work waiting and the reading not (§221.5); when every seat is taken, the goal goes first in line and starts as soon as
   one is free. *Talk more* and *Drop it* as §224.4.
4. The mockup `docs/mockups/phone/goal-lens-v4.html` is changed to say it.
The owner's call.

## 226. The phone in daylight: the dark look pushed (brighter ink, every edge that tells something on orkUI's edge, the type a size up, nothing under 14 px, a goal's slice one column); no light look for now (3 November 2026, the owner)

Changes: 222, 223; spec 40.

Why: the owner, looking at the phone's mockups: there will be trouble with contrast on a phone, which is used in the
street on a sunny day, and the type seems small for it. Measured on orkUI 0.28's office tokens: text holds well (ink
12.8:1 on the table, 9.9:1 on a card; muted 7.5:1 and 5.8:1; faint 5.9:1 and 4.5:1, on the edge); what does not hold is
what is drawn by a line or a shade alone: `frame` 1.5:1 on the table and `card-frame` 1.25:1 on a card, under WCAG 1.4.11's
3:1 for a part's edge or its state; the canvas, the table and the panel 1.05–1.1:1 apart and a card 1.3:1 from the table,
one black plane in daylight; and the mockups' own 10–11 px text, under orkUI's phone scale. orkUI already has an
`edge` at 5.2:1, used for no edge that matters. The mockups `docs/mockups/phone/goal-lens-v5.html` (now and proposed)
and `goal-lens-v6.html` (now, dark for daylight, light for daylight) showed three ways; the owner chose the dark one and
put the light one off. So:
1. **The look stays orkUI's office, dark** (spec 40, CLAUDE.md); **no light look for now**. Glare washes a dark screen
   most, so a light look following the phone's own setting stays the one asked again later, as orkUI's second look.
2. **Asked of orkUI** (the look is changed there and copied, never here): on a phone, the ink and the muted ink brighter
   (about 15:1 and 10:1 on the table); **every edge that tells a part or a state on `edge`** (at least 3:1 on the table,
   the panel and a card: a switch, an aspect's chip, a container, a read-only part, a card's own frame), `frame` kept for
   dividers; the panel a step lighter; **the phone's type a size up**: body 17 px, captions 15, labels 14 bold, a part's
   name 16, a goal's name 19; IBM Plex Sans 500 added (the copy has 400 and 600 only). Until orkUI has it, the phone's
   sheets ask for nothing of their own (Orkboard carries no colour, font or corner).
3. **The phone's rules, in Orkboard's spec**: **no text under 14 px** on a phone; **a state is never told by an edge or a
   shade alone**: a word (*changed*, *new*, *read*), a sign or an ink line as well; the changed and the new 2 px;
   **a goal's slice one column, a row a part** (44 px at least), the lens scrolling more rather than shrinking; a rune
   always its shape and its colour, never its colour alone (the runes stand near the signals: dust near alert, lava near
   danger, meadow near success).
4. **A test of the tokens' contrast** (`tests/test_design_system.py`: text 4.5:1 on every ground, the ink 7:1, an edge,
   a signal and a rune 3:1) comes with the spec that takes orkUI's new copy.
5. **Checked on a phone in the sun** before the spec is closed: the mockup v6 opened outdoors, at the phone's own brightness.
The owner's call.

## 227. Orkboard driven from a terminal, by the page's own commands: an agent can serve a project, drop a goal, wait for its steps, run a scenario and take pictures of the page, with the AI tools hidden unless asked for; a stand-in tool for every step comes next (3 November 2026, the owner)

Changes: spec 37 §4, spec 107 §2.

Why: the owner: can Orkboard be changed so that an agent (Claude, in a session like this one) drives all its flows from
code, by console commands rather than the interface: create a goal and take it through the whole team, so the first
testing is done by the agent alone. Most of it was there: `orkboard --serve` serves a project with no window and says
its address (gui/extension.py); every act of the page is a command on one socket (gui/server.py: `ideas.add`,
`ideas.answer`, `ideas.start_now`, `ideas.gate_merge` and the rest); `/api/version` is the handshake for a client other
than the page; `command_log` records what is refused. Tried in this session on a fresh project: a party made, a goal
dropped, routed by code; but where an agent CLI was on the PATH the host ran Talk's first round on it at once (one call,
Sonnet, about 35 000 tokens), on the owner's limits. So:
1. **`orkboard drive`** (gui/drive.py), a client of the page's socket: `start` (the project served with no window, its
   address kept in `<project>/.orkcraft/drive.json`, readable by its owner alone, gone when it stops), `call` (one
   command, its answer as JSON, `--path` for one value), `state`, `wait` (a command asked again until the value at a path
   `--is`, `--has` or is `--not` something), `watch`, `run` (a scenario: steps and what each must find, a JSON line a
   step and a summary, the first failure ending it), `shot` (a picture of the page at a phone's size or the desktop's,
   by Playwright, Python's or Node's), `stop`. **It never has a way of its own**: each act is one of the page's commands,
   so a drive goes where a person's presses go and tests the real flow. The server stays on 127.0.0.1 with its token
   and Origin, as for the page.
2. **The AI tools are hidden unless asked for**: `drive start` runs with a PATH holding no agent CLI and no `gh` and
   reads no limits or model list, so a step that would ask a model waits or fails as a missing tool, spending nothing;
   `--real-tools` lets it run the tools it finds, said plainly that they spend their limits.
3. **Scenarios are tests too**: `tests/scenarios/a-goal-routed.json` (a party, a goal dropped, routed by code, its route
   card in the hand, the phone's and the desktop's pictures) is run by `tests/test_drive.py` against a real host and server
   (its pictures left out).
4. **Next, a stand-in tool for every step** (a spec of its own): a tool on the PATH, on when an environment variable
   says so and never shown in the interface, answering each call by its step (`route`, `talk_round`, `section`, `join`,
   `plan`, a task's work committing a file) in the form its reader takes, so a goal goes the whole way (route → Talk →
   sections → To review → work → the gate → ready for main) in seconds with no model, in CI and in a cloud session. Until
   then the whole way runs with `--real-tools` on the owner's machine, on a tool that has limits to spare.
5. **What the first drive found** (for the phone's spec, §222–§226): the route card's cost is said in dollars at API
   prices when no limits are read, not as a share of a tool's week; the desktop's discard writes *1 commit ready for
   master* past its card's edge.
The owner's call.

## 228. What the calls spent, in one command: by tool, step and goal, the dearest calls, and what is worth a look, read from the day logs with no model (3 November 2026, the owner)

Changes: 227; spec 36.

Why: the owner, before the beta's run: the usage logs must be at hand, to watch the tokens and not spend them for
nothing. Every call is kept already (`.orkcraft/logs/<day>/<building>/calls.jsonl`, realm/call_log.py: its tool, model,
step, goal, seconds, exit code, cost and the usage its tool printed, the prompt and the whole answer gzipped beside it;
and each goal's ledger, realm/idea_spend.py), but nothing added it up for a terminal or an agent. The first drive's one
call shows why it matters: a Talk round on Sonnet wrote 34 637 tokens to the cache and read none. So:
1. **`orkboard drive spend`** (realm/spend_report.py, printed by gui/drive.py, no server needed): the total (calls,
   tokens in, out, read from the cache and written to it, the share read from the cache, $ at API prices, the unpriced
   counted apart, never as $0), by tool and model, by step, by goal; the five dearest calls; `--since`, `--goal`, `--json`.
2. **What is worth a look**, named by rule and never a verdict: failed calls and their cost; a call that wrote a big cache
   (20 000 tokens or more) and read none; a heavy read with a short answer (60 000 in, under 1 000 out); a step asked
   again (three calls or more of one step for one goal). Each is a line to explain or a goal to make.
3. **The beta's run reports it** (`docs/beta/run-the-whole-way.md`): the goal's spend and every line worth a look, its
   call's prompt and answer at hand in the day log.
4. **Later**: the same in the page's *Spend* and on the phone, when the phone's spec (§222–§226) is built.
The owner's call.

## 229. The project's journal on its own remote: asked for once, a branch of its own, what it holds small and with no code, sent by code and never by a model, the Orkmaster's to keep (3 November 2026, the owner)

Changes: 227, 228; spec 41.

Why: the owner, before running the other decisions on Codex while away from the computer: the status, the logs and the
errors should go to the remote by default, as one more duty of the Orkmaster. What already leaves the machine: usage
stats and crash reports, to Orkboard's makers, only on a yes (`orkboard usage`); a goal's branches, to origin, when
`push` is on. Nothing tells the project's own remote how the work goes, so from a phone, from another machine or from an
agent's session in the cloud it cannot be read. But sending is publishing (a public repository shows it to everyone; the
day logs hold the project's code in their prompts and the models' answers, and a test may print a secret into a tool's
output), and a commit every few minutes is noise and, where CI runs on every branch, minutes spent. So:
1. **Asked for once, per project, in plain words**, never on by itself: `[journal]` in `orkcraft.toml` (`remote`, the
   remote's name, `origin` at first; `branch`; `every`, minutes; `prompts`, false). The page's Settings asks it in its
   words when it is built (*Send this project's journal to origin: its status, its errors and what its calls spent; no
   code and no prompts*); until then the file says it.
2. **A branch of its own**, `orkboard/journal` at first: it shares no history with the code, is never merged, holds no
   workflow, so no CI runs for it; it is committed by git's plumbing (no checkout, the working tree untouched) and pushed
   without force.
3. **What it holds**: `status.md` (the goals by pile and phase, what waits in the hand, what failed, when it was written);
   the event log's lines of the last days; `spend.json` and `spend.txt` (§228, with *worth a look*); the calls' metadata
   (tool, model, step, tokens, cost, exit code). **Never** the server's token (`drive.json`), an `.env`, a key; every
   line is read for a secret's shape (a provider's key, a token, a private key) and held back in words if it has one.
   The calls' whole prompts and answers only with `prompts = true`, said to be for a private repository.
4. **When**: when something changed since the last sending, at most every `every` minutes (15 at first), and at once when a
   goal fails, a gate turns red or a command breaks; nothing to send, nothing sent. Offline, it waits; a sending that
   fails troubles no work, and is said in the event log.
5. **Sent by code, no model**: it is the Orkmaster's duty (it says *what and who*, and keeps the record of it), done by
   code at no token's cost. The page shows it on the Orkmaster's head later (*Journal sent at 14:02*; a failure a card in
   the hand), with the phone's spec (§222–§226).
6. **From a terminal**: `orkboard drive journal` (`--dry-run`: what would go; `--now`: send it now).
The owner's call.

## 230. Who the person is to Orkboard itself: a user, a beta tester, a contributor; the bug for the first two, the hammer and the anvil, a forge, for the third: the journal's sync, its rhythm, where it goes, what is ready, Fix it here or from the cloud (3 November 2026, the owner)

Changes: 197, 229; spec 119.

Why: the owner, after §229: with a private repository the journal's sending could join the bug with the hammer (spec 119:
**Save logs**, and **Fix it**, which starts Claude Code on Orkboard's own code, only from a git checkout of Orkboard with
`claude` on that computer; a cloud session was left for later, §7); and then: a setting at the start, *become an Orkboard
contributor*, that turns the bug into a hammer with an anvil, where the journal's rhythm is set and the last sync is shown.
The bug today mixes two worlds: an indie developer needs to save the logs and say something broke; whoever makes Orkboard
needs a forge. And a beta needs a third: a tester who does not touch the code but whose reports must reach the makers. So:
1. **Three ways a person stands to Orkboard**, in Settings (*Orkboard itself*): **a user** (the default), **a beta tester**,
   **a contributor**. Nothing is asked of everyone at the start: when Orkboard runs from a git checkout of orkBoard it
   offers once *You work on Orkboard itself? Turn the forge on*; an installed copy (uv, brew, pipx) asks nothing, and the
   choice is in Settings for whoever wants it.
2. **A user: the bug**, as built: *What went wrong?*, **Save logs**.
3. **A beta tester: the bug and Send to the makers**: the person's line and the logs scrubbed (§229.3's shapes held back),
   no code and no prompts, shown before it goes and asked each time; through the channel the crash reports already use
   (`orkboard usage`, spec 41), as a report of its own kind. Its spec comes with the beta.
4. **A contributor: the hammer and the anvil, the forge**: the bug's button turns into a hammer over an anvil (orkUI's
   `hammer` exists; the anvil is drawn in orkUI first, then copied). Pressed, a panel, as the bug's is (no drawer):
   - **the sync**, its first line: *Journal sent at 14:02* with a check, or *Not sent at 14:02: <git's words>* in the alert's
     colour, and **Send now**; a state, never a count;
   - **the rhythm**, a choice of a few: *every 5 min · 15 · an hour · only when something fails*;
   - **where it goes**: the remote's name and **This repository is private**, the person's word for it (Orkboard cannot
     know); only with it does a bug's bundle go (5);
   - **what is ready**, a short list of ✓ and ✗: *Orkboard's checkout found · claude on this computer · the journal set ·
     the last beta run*, so a Fix it that cannot run says why;
   - **Fix it**, here (spec 119, as built) or **from the cloud** (5).
5. **The bug's bundle, the contributor's alone, to a private journal only**: a press of the hammer sends the journal at once
   with `bugs/<time>/` in it: the person's line, Orkboard's own log since it started (what Save logs packs), the traces,
   a snapshot of what was shown. **Fix it from the cloud** (spec 119 §7): a cloud Claude session reads that folder, fixes
   Orkboard's code, runs the critical tests and pushes to main; Orkboard sees main move and offers **Update and restart**,
   as built. Without *This repository is private* the hammer saves the logs here, and the journal goes without a bundle.
6. **§229 moves into the forge**: `[journal]` in orkcraft.toml stays what lies under it (the forge writes it); the journal
   is a contributor's tool for now; a user follows a project from the phone (§219, §222–§226), and the journal is offered to
   users only if they ask for it.
7. **Builds**: the forge's face and its settings, then the bug's bundle and Fix it from the cloud, after the beta's run;
   Send to the makers with the beta. The look by orkUI first (the anvil).
The owner's call.

## 231. Camp is tested in marketing, not in the product: each product's clips and landing in two looks, Work and Camp, both leading to the same product in orkUI's office; Camp is built in the product only if the gap between the Camp clip and the product loses the people it brings (3 November 2026, the owner)

Changes: 45 (item 11's measure), 50.8, 89.4; hypothesis H3.

Why: the owner proposed three looks of orkUI: *terminal* (every icon an emoji, the kit drawn in a terminal), *work*
(today's office) and *camp* (art in the look of the first orkcraft site, its humorous orks), with the trailers of Orkboard
and the other products A/B tested in the last two. Weighed as a designer and a marketer: three looks triple every
component, test and screenshot while the core changes every day; and the AgentCraft study (§45) already says a game's
picture brings views, not a habit. So what Camp has to show is not that it is watched more but that it **brings people who
stay**, and a clip can ask that before any Camp is built. So:
1. **Camp is tested in marketing alone**: the clips (trailers) and landing pages of Orkboard, then of each product as it
   ships (OrkWiki, OrkMine, OrkWatch), are made in two looks, **Work** (orkUI's office, as the product is) and **Camp** (the
   first site's orks with their humour, the art made for the clips). The product, the page and the phone stay in orkUI's
   office alone (§53.1): no look switch, no camp file in the package.
2. **Both arms lead to the same product.** So the test measures exactly what Camp would cost: a person brought by orks
   meeting an office. The landing shows the real product's picture above its install in both arms; nobody installs
   expecting a game.
3. **One script for both**: the same beats, the same shots of the product, the same words; only the wrapping differs (the
   first seconds, the frame around the product's shots, the characters, the music). Otherwise the script is tested, not
   the look. In the Camp clip the humour is in the wrapping, never in what is said of money or safety (CLAUDE.md).
4. **Measured past the views**, per arm: the first three seconds held, the clicks, the cost of an install or a letter on
   the waitlist; then **activation**, a goal of the person's own taken through to a merge (§45.11's first measure), and
   **coming back within 7 days**; and **the gap**: those who open Orkboard once and drop no goal on the first day. The
   arm goes with the link (`?via=camp`, `?via=work`) to the landing, the waitlist's letter and the install command, and
   reaches Orkboard only with the person's yes (`orkboard usage`, spec 41), never by itself.
5. **Decided beforehand** (first numbers, the owner's to move; at least 20 000 views per arm for the clicks, at least 100
   installs per arm before the later measures count, below that they are a direction and the test goes on):
   - **Camp wins the marketing** when its install costs at least 30% less and its activation and coming back are not
     worse by more than a tenth: the clips and landings are made in Camp from then on; the product stays office.
   - **The gap loses people** when Camp's installs are cheaper but its people drop on the first day at least 1.5 times
     as often as Work's, or come back within 7 days at most two thirds as often: **Camp is built in the product** (6).
   - **Camp loses** when it is dearer and no better: the clips stay Work; Camp stays frozen (§45.10).
6. **When Camp is built**, it is §50.5's Camp: a look and a reader over the same core, never a mechanic of its own.
   orkUI gets a second look, `camp` (its tokens and art made in orkUI first, then copied); Orkboard's sheets read it as
   they read office; a switch in Settings, office the default; what the clip showed first. Words about money and safety
   stay plain in it. A spec of its own then; §53.1's *one look* is amended by it, not before.
7. **The clips' art is made once, for both**: a sheet of the races (§53, §158) in the first site's humour, so the clips and
   a later Camp are one world; kept in orkUI as the clips' library (as §69's emblems), never loaded by the product. In
   the realm's own look, never another studio's.
8. **Replaces §45.11's screenshot shown to the testers** as the measure that brings Camp back. The order of §50.8 stands
   for the product; the clips are made beside it, and §27 is untouched (no mechanic is built for them).
9. **Not taken now: the terminal look.** Orkboard draws no face in a terminal (`tests/test_architecture.py`). What was
   weighed is kept for when the terminal's output (`orkboard drive`, `measures`, `spend`) is worked on: orkUI's tokens
   as ANSI colours and its 7 × 7 marks in half blocks (▀ ▄ █), never emoji (they differ by terminal, break the grid and
   colour what is no signal).
The owner's call.

## 232. The first open is the Orkmaster's: the project asked as cards in the hand; the AI tools added one a card from the potions' empty slot; the parties on the Orkmaster's large card, a party one line with its heads; a table is laid only at Start, and nothing of it lies beside a form (3 November 2026, the owner)

Changes: 145.9, 169.4, 175.2, 176.2, 176.4, 177.1, 185, 192.4, 206.3; spec 75 §5, spec 81 §4, spec 100 §4; the onboarding's
first screen (spec 33 §1).

Why: the owner, as a designer and a product: *the AI tools can be turned on and off, added and removed while working on a
project, not only at the start: better straight from the bottles*; *show adding the tools through the bottles in the
onboarding too, so it is clear later*; *opening the project's folder could be a talk with the Orkmaster, like the questions
with the leaders, which also teaches them*; *picking the parties as a card: the project's kind in a list at the top, the
stages and their parties under it*; *a head pressed, the leader's or a member's, picks its tool and under it its level as
three heads with their words*; *while the project is set up, no In analysis or To review at the left and no discard*;
*never the discard beside Settings: it looks like a bug*. Then, on the mockup's first draw: *adding a tool can be simpler: a
tool, how it is paid, then a sign-in or the key, and Test & add; after it the first bottle appears and a card to set the
next, up to six; if not, on to the parties*; *a party's row is too long (its size, its tool by full name, a price): put a
small size switch on the party's line and its heads under it, split into Does and Checks, the empty seats as shadows*;
*show the tool as its mark by the head, and a press opens the head's seat*; and: *the shadows are not pressed for now*;
*no key typed into Orkboard for now*. Today the tools are set once, on a table of checkboxes before the Board opens
(`onboarding.js` `ToolsStep`), and later only in Settings' rows, while the window's picture of them, the potions, can only
be read; the folder is a form and the parties a place of two halves, so the first thing a person meets is three forms and
not one of the window's own ways; the empty piles and the empty table's end are the first open's noise; and a place over
the pane leaves the ring and the discard standing beside a form. The owner's yes on `docs/mockups/setup/`. So:
1. **A table is laid at Start.** Until the project's first **Start** (8) the window is in its frame but **not yet laid**:
   the leaders' row holds the Orkmaster alone (no tabs, no empty chair, no door, no die); its column holds no pile, only its
   bubble; the table's end has neither the ring nor the discard's place; the hand has no + card and no deck, only the
   Orkmaster's cards and the AI tools at its right. At **Start** the table is laid once, in order: the leaders sit down in
   their chairs, the empty chair and the door appear, the ring and the discard's place appear at the table's end, the + card
   comes to the hand with its seal lit once (§185.4's hover, played by itself), and the Orkmaster says *The table is laid.
   What shall we make first? Play the + card.* in its bubble. Reduced motion: all at once. **A pile's heading appears with
   its first card**, never empty (this makes §206.3 precise). §185's *always laid* holds from Start on. A project opened
   that already has parties of its own (made by Orkline or an earlier Orkboard) is laid at once.
2. **Nothing of the table lies beside a form.** A place over the pane (§142: Settings, Open a project, the update, Pair a
   phone, Remove party) covers the whole table, **its end included**: no ring and no discard beside it. The Orkmaster's
   column and the hand stay as they are, since the work goes on under it (§142's *nothing traps the focus*).
3. **The Orkmaster asks for the project as cards in the hand**, the way every question for the person comes (§206.6), its
   line in its bubble (§201): *Which project shall we work on?* with **Open a folder…** (the system's dialog, opened from
   the card), **A new, empty folder…** and the recent projects as answers; then, for a folder with no git, *No git in
   <name> yet. Start git here?* (**Start git here**, **Choose another folder**); while it reads, its bubble says *Reading
   <name>* (`ork-think`); then *<name> is <kind>, <how>. Right?* with the signs it saw as chips (`project_kind.read`'s,
   spec 75 §1) and the stage read with it, answered **Yes** or **It is something else…** (the kinds' list in the card); an
   empty folder asks *What is it for?* in one line (spec 75's cheap call). No answer is typed that a press could give. The
   start screen and the Open folder form (projects.js) are this card when no project is open; with a project open, *Open a
   project…* stays a place (2).
4. **An AI tool is added by a card from the potions' empty slot.** The potions' row (§176.2) ends with **an empty slot**: a
   potion's place in pixel dashes with a +, faint at rest (§185.1), lit when the Orkmaster asks for a tool; hidden when six
   tools are in the hand. Pressed, it lifts **the card that adds one tool** (§176.4), *Add an AI tool · n of up to 6*:
   - **AI tool**: a list of the tools found on this computer that are not in the hand yet, in today's three groups
     (*Ready*, *Not signed in*, *Not installed*, toolpick.js's), a tool not installed shown with how to install it and not
     picked; the first ready tool picked.
   - **Paid by**: *Subscription* (picked) or *API key*.
   - **A third line that follows them**: on a subscription, *✓ Signed in to your subscription*, or *⚠ Not signed in* with
     **Sign in** (spec 45's sign-in; **Test & add** waits for it); on an API key, **only a key already in the environment**,
     named (*✓ Uses the key in your environment: CODEX_API_KEY*, *Paid per token, by that key*; the variables are
     `tool_errors.TAKES_KEYS`'), else *No key found: set <VAR> in your environment, then Test again* and Test & add waits.
     **A key that would win over the subscription is said before it costs**: on *Subscription* with the tool's key in the
     environment, *⚠ ANTHROPIC_API_KEY is set in your environment: Claude Code uses it before your subscription and is paid
     per token.*
   - **Test & add**: one short request to the tool's lightest model (the onboarding's Check; on an API key *about $0.001*,
     said under the button). A failure says why on the card in the tool's words, and nothing is added. It answers: the
     tool's potion comes into the hand at the end of the row (the first one framed: the main tool), and **the card turns**:
     *<Tool> is in your hand. Add another AI tool?*, **Add another** (the card again, without the tools in the hand) and
     **Go on to the parties** (the first open; later **Done**). At the sixth tool it goes on by itself.
   - An experimental tool asks its warning first (*Turn on … at my own risk*), and **Request a tool** stays, as the
     onboarding has them. *Found on this computer. Nothing else was run, and no key was read.*
   **A tool is in the hand or not**: there is no third state (*on* but not used). The interface says *AI tools*, *Add an AI
   tool*, *Test & add*, *Put back*, never *shop*, *buy* or *belt*: the nod to a game's potion belt is in the shape, not in
   the words (CLAUDE.md's *everything else by what it does*; §231).
5. **A potion pressed lifts its tool's card** (what a press did, *what used it*, becomes a link on it): the tool's mark,
   name and potion, its two shares in words (§192.3); **Paid by** *Subscription · API key* (the same third line as 4);
   **the order the work moves on in**, the hand's potions as marks with this one framed and **←** **→** (dragging a potion
   does the same; §177.1's order is the person's now, kept as `machine.tool_order`), the main tool the first; **Check**;
   its tiers' models (Settings' *AI tools* rows, moved here); and **Put back**, with what follows said under it: *The orks
   stop using it after the task at work* and each party set to it by name (*Art is set to Claude Code: it goes on with
   Codex, the next in your hand*). A tool is put back **between tasks, never inside one** (§177.2), with **Undo** in the
   toast; **the last tool** asks first (*Without it nothing is worked on: goals wait in the Orkmaster's column until you add
   a tool*). The adding card and the tool's card are the only places the tools are set: Settings' tool rows go (9).
6. **The parties are the Orkmaster's large card on the table** (the one place of the parties, spec 100 §4, becomes it):
   dealt from the Orkmaster's head onto the table, the same card the first time and later from the empty chair and a
   party's *Edit*. It is wider than a lifted card (§176.4's *never grows wider* is a hand card's), about 620 px at the wide
   width, and never covers the potions. At its top **The project is** and the kinds' list, with what it was read from;
   under it the stages (*Idea*, *Being made*, *Live*), the stage the project is at marked *The project is here* and set by
   a press on another's heading. **A party is one line** and its heads under it:
   - **The line**: its tick; its leader's head with **its AI tool's mark in the corner**, framed when the party follows the
     main tool and showing the tool it is on now, bare when a tool is set for the party (§192.4); its name; and **its size,
     a small switch** (*Lean · Standard · Full*, the label face, one line high) at the line's end. The party's price a goal
     is the switch's words (hover and the screen reader: *Standard: about $0.40–0.90 a goal*, `ideas.party_price`). Its
     line of what it does is the name's words (hover), not drawn.
   - **Under it, its team**: **Does** after orkUI's sword and **Checks** after its shield (§189's), each a row of the
     seats' heads at the small size (24 × 22), the seats the size gives (spec 81 §2) as heads and **the seats the craft has
     and the size leaves empty as shadows** (the head's silhouette, dark, no face and no gear), up to five who do and two
     who check. **Changing the size changes the heads at once**, nothing saved until Start or Save. Under *Lean* the
     Checks are dimmed with *Lean: the leader does it, and checks it itself*. **A shadow is not pressed**, for now.
   - **A member's head wears a tool's mark only when its tool differs from the party's**; the same tool shows none.
   - **Release** is ticked and locked (*in every project*), its size locked at Lean. **The stages not reached** lie in one
     line of heads and names (*offered when the project is live*), a tick seating one now.
   - **At its foot** what the ticked parties cost together, said plainly (*Together ≈ $1.30–3.00 a goal at the API's
     prices. On a subscription it is taken from its limits instead.*), and **Start** the first time (it makes them, then
     `ideas.project_ask`, as today), **Save** after (*From the next task*). The narrow width: the card is the screen, one
     party a block.
7. **A head or a mark pressed opens its seat** (seatpop.js, §110.7), any head of a party, the leader's too; hover only
   marks it, so a phone and a keyboard reach it. The seat says its role and what it does; **its AI tool**: on the leader's
   seat **the party's AI tool** (*Main tool (<name>): follows it* first, then the tools in the hand; *The leader and every
   member set to As the party run on it*), on a member's **its own** (*As the party (<tool>)* first, then the tools in the
   hand); and **its level as three heads**, the seat's race in its three gears (§158's tier is the gear on the head), each
   with its word (*Novice*, *Seasoned*, *Veteran*) and what a task (a leader's step) costs at it; under a leader set to
   Novice a line says the cost in quality plainly (*reads less of the project before it plans*). **Take off the seat** for a
   member, never for the leader. A seat set by hand keeps what was set and the party's size stays picked, as Agents' tiers do
   (spec 81 §2).
8. **The first open, in order**: the window not yet laid (1) → the project (3) → the AI tools (4), **only when the hand is
   empty** (the tools are this computer's: the second project skips it) → the parties' card (6) → **Start** → the table
   laid (1). The onboarding's table of checkboxes, its Next and its Skip go; closing the adding card with no tool added says
   *No AI tool: the Board opens, and nothing is worked on until you add one*. The Security reviewer's hooks (today's
   onboarding checkbox, off in focus) are not asked here.
9. **Settings keeps what is neither a tool nor a party**, in two groups, **This project** (Start plans by themselves, Work
   at night, A result that holds lands in dev, Push after merging, the Target) and **This computer** (Keep the computer
   awake, Your phone, Updates, the logs), and one line where the rest went: *AI tools are in your hand: press a potion, or
   the empty slot beside them. Parties, their size and their AI tool: the empty chair, or a party's Edit.* A card it is
   not: a card is a decision waiting for the person (§206.6), and Settings is not one.
10. **Not now**: a key typed into Orkboard (kept in the keychain, `orkcraft-ideas`, and given to the tool's run) is a
    decision of its own later; a shadow pressed to seat a role beyond the size; any of this on the phone, which shows the
    tools as today (§223's bottle) and sets none.
11. **The words** (`TERMS`): `tool_order` (*the order the work moves on in*); *Add an AI tool*, *Test & add*, *Add another*,
    *Go on to the parties*, *Put back*, *Which project shall we work on?*, *The project is*, *The project is here*, *The
    party's AI tool*, *Its level*, *The table is laid*. The word *shelf* is the code's only.
12. **Drawn first** (`docs/mockups/setup/`, eight looks); a spec of its own builds it (spec 130), its parts by the cheaper
    model. orkUI draws first (§127.3): the empty slot (`.ork-potion.is-empty`: the silhouette in pixel dashes, `.is-lit` in
    the ink), the small size switch, a head's shadow (`.ork-race__head.is-empty`), the three levels' tiles; until orkUI has
    them, the page's own layout with orkUI's tokens. Its parts: **A. Host** (`machine.tool_order` in `settings.py`, read by
    `harnesses.main`; the tools' commands out of `gui/onboarding.py` into `tools.*` of their own: the adding card's rows,
    the key found in the environment by name and never its value, test and add, put back between tasks with the last one
    refused without `sure`, order, billing; the project's questions answered from a card; the *laid* state, false until the
    first Start); **B. The hand** (`hand/mana.js`: the empty slot, the adding card, the tool's card; `hand/state.js`: the
    Orkmaster's setup cards); **C. The table** (`table/parties.js` and `partyseats2.js` as the large card, `seatpop.js` with
    the party's tool and the level, `frame/place.js` and `table/table.js` covering the table's end, `table/column.js` and
    `table/piles.js` with no empty pile, the laying's motion); **D. Settings and the onboarding** (`shell/settings.js` and
    `js/settings.js` lose the tools' rows, `onboarding.js`'s `ToolsStep` goes, `shell/projects.js`'s start screen becomes
    the card). Each part merged into main as its own tests and the critical ones are green, with a browser test of the first
    open from an empty folder to the laid table.
The owner's call.

## 233. Every leader keeps its slice of each decision: the decision cut once into a slice for each leader it touches, the slice's key conclusion and its reason's link; a leader proposes a change from its craft, and the change cascades through the slices that rest on it, three steps at most, to one card in the hand (3 November 2026, the owner)

Changes: 153.4, 206.5; spec 99 §6.1, §7.2.

Why: the owner, on what a step costs: *a decision costs the least: it is quick and cheap to change or to sync with the
others; a spec is harder: the leaders are asked again and the project's state checked*. So: *every leader keeps all the
decisions on its spec, each decision cut into the leaders' slices, the key conclusion for that slice and a link to its
reason, and can change decisions in a cascade from its craft*. Then, asked three things: *every leader the decision
touches, not only the route's: more tokens, but every leader sure to get the right context*; *only the new ones, from this
decision on*; *deeper, with a reasonable limit*; and, asked whether a leader so knows every decision and every later change of its
slice: *yes: add what a slice replaced, and fold what passes the bound instead of cutting it*. Today the decision's call reads the decisions file's last ten headings
only (spec 99 §6.1) and a section its own goal's decision (§7.2): a conflict with an earlier decision shows as a fork
after the sections are paid for, or not at all, and a leader that finds a decision wrong for its craft can only ask.
Changing decisions is cheap and rewriting sections dear, so the cascade runs deep in the decisions and touches the
sections once, at its end. So:
1. **The decision is the source; a slice is cut from it.** At **Confirm and start** (`ideas.confirm`), once the entry is
   committed, one call of the Orkmaster on the cheaper tier, no tools (step `slice`), given the entry and **every leader
   of the project** with its map in one line (`map_text`'s), answers for each leader either **its slice**, the key
   conclusion for its craft in one or two lines and the points it rests on (the link, *§240.2*), or **none**. Every leader
   the decision touches gets one, on the goal's route or not, Release too; *none* is an answer and is kept, so no leader
   is left out unseen. One call a decision, not one a leader.
2. **A slice is never edited**, by the person or a leader: a change is a new decision (5–8), and its cut replaces the
   slices that rest on the points it changes (`replaced_by`), the old ones kept and no longer read. **The new slice says
   once what it replaced**: *the screen holds 6 seconds (§240.2); was 10 seconds (§159.1)*, so the leader knows what moved
   and why and does not propose the old one back; the *was* goes at the slice's next replacement. Slices are kept beside
   the facts (§153.4), `<state_dir>/slices.json`, `{party: [{decision, points, says, at, replaced_by}]}`; they are derived,
   so a missing file is cut again from the decisions file (for the decisions this one covers, 4).
3. **Read into every leader's call** beside its facts (`project_facts.for_call`): its standing slices, the newest first,
   each with its link, bounded as the brief is (about 1,000 characters). **Past the bound they are folded, not cut**: one
   call of the leader on the cheaper tier, no tools (step `slice_digest`, as the journal's digest, spec 125 §D), given its
   old digest and the slices past the bound, writes its craft's digest of them with their links; the call then reads the
   digest and the newest slices whole, and the folded slices are kept and no longer read one by one. A slice replaced
   later is folded out of the digest at the next fold. A member reads none: its leader's brief carries what it needs.
   **The decision's call reads them too**: the standing
   slices of the route's leaders and of those whose parts of the map the goal touches, so a conflict with an earlier
   decision is seen and said in the decision, before any section is written.
4. **Only the new**: decisions from this one on are cut; the earlier are not. Until the slices fill, the last ten headings
   stay in every call as today; they go when a decision says so.
5. **A leader proposes, never changes** (§104: *what* and *why* are the Orkmaster's and the person's). When a leader is
   called anyway (writing its section, planning or checking a task, answering in Talk) and finds a standing slice of its
   own wrong for its craft (the project says otherwise, the work ran into it), its answer carries **a proposal**: the
   slice as it would read, why, and the link it changes. No call is made to look for one: nothing runs in the background
   (spec 99 §3). A proposal changes nothing by itself.
6. **The cascade, by code and short answers**: code finds the other leaders' standing slices that rest on the points the
   proposal changes (by their links, no model); each such leader answers in a sentence (the cheaper tier, no tools, given
   its slice and the change): **agrees**, with its slice as it would read, or **disagrees**, and why. An agreeing leader's
   changed slice is the next step: the slices resting on it are found and asked in turn. A disagreement is **a fork**, as
   spec 99 §7.3's, for the person.
7. **Its bounds**: **three steps** at most from the proposing leader; **a point changed once in a cascade is not changed
   again in it** (a second change of it is a fork); and **a price**: each step priced before it is asked, the cascade
   stopping at **2% of the main tool's week** (a default, tuned by H1's trial, spec 124 C), whichever comes first. Where it
   stopped is said on its card (*Stopped after three steps: Marketing was not asked*).
8. **One card in the hand**: a decision card, as *Make it a change*'s (§206.5) but proposed by the leader: the new
   decision worded by the Orkmaster's `decide` step, its `Changes:` line naming the decisions it changes; the chain as the
   leaders' heads in order, each slice before and after; the forks to answer first; the cost of what follows (the
   sections to write again); **Confirm and start** and **Put it back**. Until Confirm nothing changes: put back, every
   slice stands.
9. **After Confirm**: the entry appended and committed (spec 99 §6.2), cut (1); then only **the goals not done** whose
   sections rest on a changed point have those sections written again, one call a section (as a fork's answer, spec 99
   §7.3), a goal at work re-planning what is left (spec 62). **Goals in the discard are not touched**: each is checked
   against the spec it was built to (§206.8).
10. **Seen**: a leader's slices are read (never edited) in the one place of the parties under its leader's row, beside
    its facts (§153.4), each a link to its decision; the leader's bubble (§206.5) answers from them.
11. **The words** (`TERMS`): `slice` (*slice*: a leader's part of a decision), `cascade` (*cascade*); *Proposes*,
    *Agrees*, *Disagrees*, *Stopped after <n> steps*.
12. **Built** by a spec of its own (spec 131), its parts by the cheaper model: **A. Slices** (the cut, the store, the
    *was* line, the fold, the reading into the calls and the decision's call: host only, no face; merged on its own, useful
    alone); **B. The
    proposal and the cascade** (host: the proposal in a leader's answer, the links followed, the steps, the bounds, the
    card's row); **C. Faces** (the card in the hand, the slices in the one place of the parties). Each part merged into
    main as its own tests and the critical ones are green.
The owner's call.

## 234. Four levels, decision, spec, work and quality, ordered by their weight on the product and the cost of a change; a change goes down and redoes only what it touches; a finding goes up to the level that holds its cause, its content from the leader where it was found and its level the Orkmaster's; a goal is refined freely before Confirm; the phase marks are the levels (3 November 2026, the owner)

Changes: 126.4, 206.5, 206.8; spec 100 §5.

Why: the owner, on how the owner and Claude work on Orkboard itself (an idea, a decision, a spec, its build): *we have
three, even four levels: decision, spec, implementation, quality and improvements; they are sorted by their effect on the
system and by how hard and costly a change is; I want this scheme wholly present in Orkboard*. And, on a goal before its
decision: the column's face-down card cannot be picked, a leader's bubble on it changes nothing, *Make it a change* waits
for a goal agreed, Talk is one round and the decision is corrected by hand only, so the cheapest level is the least open
to change. Today the four are there as four mechanisms that do not know of each other: a decision (spec 99 §6, §233), a
section (spec 99 §7, §206.5's change), a task (spec 62's re-plan, a failure's *Start again*), and quality scattered over
the discard against its spec (§206.8), the checkers, the lenses (§208–§214), a leader's concerns (spec 108), the
hypotheses (§194) and the measures (§202). A change does not say its level, and a finding has no way up to its cause:
a ≠ in the discard becomes a new goal whether the code, the spec or the decision was wrong. Asked who sorts a finding:
*the Orkmaster, but the leader where it was found gives its whole content*. Asked whether the phase marks become the
levels: *yes*. So:
1. **The four levels**, heaviest and cheapest to change first: **Decision** (what and why: the decisions file and the
   leaders' slices, §233; the person and the Orkmaster; a change is one call without tools), **Spec** (how, by craft: the
   goal's sections; the leaders; a change is a leader's call reading its map), **Work** (the tasks and the code; the
   members; a change is a re-plan and the tasks again), **Quality** (what came out against what was promised; the
   checkers and the person through Play; a finding is cheap, its fix is at the level of its cause). The rule: **change at
   the highest level that holds the cause; redo below it only what the change touches; take a finding up to its cause.**
2. **A change goes down, and redoes only what it touches**: a decision changed (§233's cascade) → the sections resting on
   its changed points → the tasks of those sections not done (spec 62's re-plan) → their *Done when* checked again; a
   section changed (§206.5) → its tasks → their checks; a task changed → its checks. Nothing above the level a change
   enters is redone, nor what the change does not touch. **Every change card says its level and what it pulls after
   it**: its level's sign, then plainly *Changes the decision: 2 sections and 3 tasks to redo, about 4% of Claude's week*,
   the cost of the whole way down said before it is spent.
3. **A finding goes up to the level that holds its cause.** A finding is any of: a ≠ or ✗ of the discard against its spec
   (§206.8), a check red, a lens's alarm on a part the goal touched (§208–§214), a leader's concern (spec 108), a
   hypothesis refuted (§194), a measure missed (§202). **The leader of the craft where it was found gives its whole
   content** (one call, the cheaper tier, its map and the few files that show it: step `finding`): what was found, what
   shows it (the check, the screen, the part, the number), what was promised there (the *Done when*, the section, the
   slice), and its own reading of the cause. A member's finding goes to its leader (a member asks only its leader). Then
   **the Orkmaster sorts it** (one call, the cheaper tier, no tools: step `finding_level`), given that content, the
   decision's entry and the slices it rests on, the section and the task: **its level** (*Work*: the code missed what the
   spec said; *Spec*: the spec said the wrong thing or left it out; *Decision*: the decision was wrong) and what would
   change there. The card in the hand: *<Party> found: …*, the finder's head, the level's sign, *The cause is in the
   spec*, the cost of the fix and of everything below it (2); **Fix it there** (Work: a fix goal on the same route,
   short; Spec: the section's change, as §206.5's; Decision: a proposal into §233's cascade), **Another level…** (the
   person moves it; the cost said again), **Not now** (kept in the goal's quality record, 4). A failure while a goal is at
   work stays as today (its checks red twice, the failure card): this is for what a goal did once it landed, and for
   findings from outside a goal's work.
4. **Quality is one place, a goal's quality record**: once a goal is in the discard, its record gathers its verdict
   against its spec (✓ ≠ + ✗ by *Done when*), its checkers' results, the lenses' alarms on the parts it touched and a
   hypothesis's outcome when it tested one; each finding with its level and what became of it (fixed there, put off, moved
   by the person). Picked in the discard, the *Quality* page shows the record (it replaces *Done*'s result, §126.4). The
   findings put off stay on their goal's record, never in a list of their own (no list column, no count: CLAUDE.md's
   frame).
5. **A goal is refined freely before Confirm**, as the cheapest level should be: in a leader's or the Orkmaster's bubble
   about a goal in analysis, **Add to the goal** writes the person's words into its *Asked* (kept as written) and, when
   its decision is worded already, words it again (one `decide` call); on the decision's card, beside *Edit*, **Change it
   in words**: the person says what to change and the Orkmaster words the decision again (one `decide` call, the
   person's words given with the old entry). Neither has a bound of rounds; each card says its cost (one call). Talk's
   rounds stay as §121.2 has them: refining is the decision's, not a third round of the leaders'.
6. **The phase marks are the levels**: the pane's title says **Decision · Spec · Work · Quality** (§126.4's *Talk ·
   Spec · Work · Done*): *Talk* is the Decision mark's page (the stances), and the decision's entry is on it once worded;
   *Quality* is the record (4). A mark is lit when its level holds an open change or finding of the goal picked (no
   number); a press opens its page as today.
7. **§233 is the Decision level's mechanism** (its slices and cascade); §206.5's *Make it a change* is the Spec level's;
   spec 62's re-plan the Work level's; this decision adds the Quality level and the way up.
8. **The words** (`TERMS`): `level` (*level*), `finding` (*finding*), `quality_record` (*quality record*); *Decision*,
   *Spec*, *Work*, *Quality* (the marks); *<Party> found: …*, *The cause is in the code / the spec / the decision*, *Fix it
   there*, *Another level…*, *Not now*, *Add to the goal*, *Change it in words*, *Changes the <level>: …*. The tests that
   check the marks' words say them (`tests/test_gui_wording.py`, the table's browser tests).
9. **Built** by a spec of its own (spec 132, after spec 131), its parts by the cheaper model: **A. Refining** (5: the
   bubble's *Add to the goal*, the decision's *Change it in words*; host and face); **B. The marks** (6); **C. The way
   down** (2: what a change pulls, said on every change card); **D. Findings and the quality record** (3, 4: the steps
   `finding` and `finding_level`, the record, the card, the *Quality* page). A and B first: they stand alone.
The owner's call.

## 235. A hypothesis says when it holds and each way it is refuted, is tested by a goal, a measure or both, says what changes if it holds, and is read from the project's own hypotheses file; refuted, it is a finding (3 November 2026, the owner)

Changes: 194.1, 194.2; spec 116 §2, §6.2.

Why: the owner asked how hypotheses are present in Orkboard, after writing H4 in Orkboard's own `docs/hypotheses.md`.
Read side by side: Orkboard's hypothesis (§194, spec 116) is *We believe …* and one line *We'll know when …*, tested by
goals and judged *Did it hold?* when they are done; the hypotheses Orkboard itself is run by (H1–H4) say apart **when
they hold and each way they are refuted, with what each way teaches** (H4's *the hook* and *the noise*), are tested by
**measures over weeks** (an install's cost, coming back within 7 days, goals landed), and say **what changes if they
hold**. None of H3 or H4 can be kept in Orkboard as it is: it has no condition apart from the signal, no test but a goal,
no date to judge by and no draft of the decision it would write; and a project that keeps its hypotheses as a file, as
Orkboard does, has them twice. The owner's *yes* to all three and to this. So:
1. **Two conditions in place of one signal**: **Holds when …** (one line) and **Refuted when …**, one to three ways, each
   one line and named by what it would teach (*the hook*, *the noise*). An item kept before reads its `signal` as its
   *Holds when* and has no refuted way until one is written. A leader's proposal (spec 116 §3) answers both.
2. **A test is a goal, a measure, or both.** A measure: what is counted, where it is read from, its threshold in each
   condition, and **a date**: the span from the test's start (*four weeks*), the date kept. Its values come **from the
   leader whose map holds the source** (one call on the date, the cheaper tier: Run's or LiveOps' live product at the
   stage *live*, spec 115; Marketing's store page, §214), else **from the person**, asked on the card at the date (a number
   for each measure, the one answer here that is typed). No measure is shown counting before its date (no number in the
   window: CLAUDE.md's frame).
3. ***Did it hold?* comes when it is due**: every test goal done, or a measure's date reached, whichever is later of the
   two when it has both. Its card shows the values against each condition's threshold, code marking the condition they
   meet (*Holds: +24%, the bar 20%*; *Refuted, the noise: 1 in 4 turned it off*), and the person judges: **Held**,
   **Refuted** with its way (the met one picked), **Not sure yet** with a new date (the why kept as evidence, as today).
4. **If it holds, if it is refuted**: a hypothesis says **what changes if it holds**, and may say what changes for a
   refuted way; that text is **the draft of the decision** the verdict writes. *Held* or *Refuted* shows the draft on the
   card (*Edit*, *Change it in words*: §234.5) and writes it in the same press; a hypothesis with no such text is worded
   by the Orkmaster's `decide` call from the hypothesis, its evidence and the verdict, as today.
5. **Refuted, it is a finding** (§234.3): Product's leader gives its content (what was believed, what was measured, what
   the goals resting on it assumed) and the Orkmaster sorts its level; the goals that rest on it (`rests`) are named in
   it, so a decision they stood on reaches them by §233's cascade. **Held**, its decision is cut into slices (§233.1) like
   any other.
6. **The project's own hypotheses file** is the source, as its decisions file is (spec 126's read in and write out): a
   Markdown file of numbered hypotheses (`## H<n>. <title>`, *Status*, *The belief*, *What would prove it, what would
   refute it*, *How we test it*, *If it holds*), found and chosen as the decisions file is (the person's chosen path,
   else `docs/hypotheses.md` when it is there). Read in, each section is an item (the belief its text, the conditions
   from its list, the measures from *How we test it* where a line names one, *If it holds* its draft); a change made in
   Orkboard (kept, judged, evidence) is written back to its section and committed to dev with the Board's pages, as a
   decision is. `hypotheses.json` follows the file: it keeps only what the file has no place for (the goals attached, the
   proposal's status). A project with no file keeps them in `hypotheses.json` as today. So Orkboard, worked on in
   Orkboard, shows H1–H4 on its Product's tree.
7. **The bounds stay** (seven open or testing, spec 116 §2): a file that holds more opens the newest seven and reads the
   others as *waiting*, never dropped.
8. **The words** (`TERMS`): `refuted_way` (*way it is refuted*), `measure` (*measure*); *Holds when*, *Refuted when*,
   *If it holds*, *Read on <date>*, *The bar*, *Not sure yet: look again on <date>*.
9. **Built** by spec 133 (after spec 132 D for 5), its parts by the cheaper model: **A. Conditions and the draft** (1,
   4: `realm/hypotheses.py`'s item, the proposal's answer, the tree's lines, the card); **B. Measures and the date** (2,
   3: the measure, the due, the values read by a leader or asked, the card against the bars); **C. The file** (6:
   read in, written out, committed); **D. Refuted as a finding** (5, on §234's way up). A first; C stands alone.
The owner's call.

## 236. The Orkmaster's column narrows to its upright card: a face-down card lies tucked under the window's left edge, its seal whole in what shows; the column has a width of its own (3 November 2026, the owner)

Changes: 206.2, 206.3; spec 128 B.1, B.3.

Why: the owner: *what if the cards turned by 90° in the Orkmaster's column were not shown whole but cut a little on their
left, so the ring of runes is seen but they do not take so much room across*; and, told that a cut alone frees nothing,
since the column's width is a lane's (`--col-w`, 180 px, `frame/frame.css`) and not its widest card's: *yes*, both together.
Today a face-up card is 112 px wide and a face-down one 157 px, so the column has two right edges and 68 px empty beside
every face-up card. A face-down card carries no name, only its seal (§206.3): what a cut takes is its frame. So:
1. **A face-down card lies tucked under the window's left edge**: about 45 px of it under the edge, **112 px showing**,
   the face-up cards' width; the cut is the window's own edge (the canvas ends there: no margin, no frame at its left),
   so it reads as a deck slid under the table's edge, never as a box cut short. **Its seal is whole in what shows**,
   centred in the shown part (not the card's), its rune upright and the running ring (`ork-sigil-sweep`) never under the
   edge. The pile's thin edges are cut the same.
2. **Hovered or focused it slides out whole**, to the right over the table (a transform; at once under reduced motion),
   and goes back when left; its focus ring is drawn inside what shows. A press does what it does (§206.3: the pile's list).
3. **The column has a width of its own**: the upright card's width and its gutters, about **128 px** (`--column-w`), no
   longer a lane's (`--col-w`); the table gains what the column gives up. The three piles share one right edge.
4. **Unchanged**: sideways is still *not agreed yet* (§206.3), the card's size (157 × 112), the piles' order and moves; the
   narrow width has no column.
5. **Drawn first**: the column at 45 px and at 30 px tucked, the owner's pick; built with spec 130's first part, its tests
   the column's browser test (the seal whole in the shown part, the slide on hover and focus, the width).
The owner's call.

## 237. Today's decisions made lighter to use, nothing of what they can do lost: one quality card a goal, two buttons on a finding, one Change on the decision, the hypothesis short until More, no list of slices, and the hand kept for what is urgent (3 November 2026, the owner)

Changes: 233.8, 233.10, 234.3, 234.4, 234.5, 234.8, 235.1, 235.3.

Why: the owner, reading §233–§236 back: do they make the interface lighter or give the person more? Mostly more: only
§236 makes it lighter, and three of them bring the hand new cards (a cascade, a finding, a hypothesis due), the hypothesis
a form three times its size, the decision card a second button beside *Edit*. *If the person's way can be made lighter
without losing what it can do or its quality, put it in the decisions.* So:
1. **One quality card a goal** (this changes §234.3–§234.4): a goal's findings come to the hand **together**, as one card,
   *Quality of <goal>*, once the goal's checks, lenses and verdict against its spec are in (not a card a finding); lifted,
   its findings in order of their level (Decision first), each a line with the finder's head, the level's sign and its
   two answers. A finding of no goal (a lens's alarm or a concern outside a goal's work) is a card of its own, as §234.3.
2. **Two answers on a finding**: **Fix it there** and **Not now**; *Another level…* moves to the finding's **…** (it is
   the rare one). On the quality card, **Fix all there** answers every finding of it at once, its cost said first.
3. **One *Change* on the decision** (this changes §234.5): the decision's card has one button beside *Confirm and start*,
   **Change…**: the entry opens as a field (as *Edit* did), and under it one line, *Or say what to change*: what is typed
   in the field is kept as written; what is said in the line is worded again by the Orkmaster (one `decide` call, its
   cost said). *Edit* and *Change it in words* are this one button. *Add to the goal* stays in the bubble.
4. **A hypothesis is short until More** (this changes §235.1, §235.3 on the page; the file keeps its whole form):
   adding one asks only *We believe* and *Holds when*; **More** opens *Refuted when*, the measures with their date and
   *If it holds*. A leader's proposal answers all of them, shown short the same way. *Did it hold?* shows the values
   against the bars in one line each, the draft of the decision under *More*. **A refuted hypothesis is one card**: its
   verdict card carries the Orkmaster's level of the finding (§235.5) as its *Fix it there*, not a second card.
5. **No list of slices** (this changes §233.10): a leader's slices are not drawn in the one place of the parties; the
   leader's bubble answers from them (*what do you hold about the timer?*), and a slice's link in any answer opens its
   decision. Nothing of the slices is lost: they are read into every call as §233.3 says.
6. **A cascade folds when all agree** (this makes §233.8 shorter): with no fork, the card says the new decision and one
   line, *Tech and Art agree*, the chain before and after under **More**; with a fork, the fork first, as §233.8.
7. **A change says its cost in one line** (§234.2): *About 4% of Claude's week: 2 sections, 3 tasks*; what each is, under
   **More**.
8. **The hand is kept for what is urgent**: the cards of today's decisions (a cascade, a quality card, a hypothesis due)
   are never urgent. They lie in the hand **after** a failure and a question (the hand's order, `piles.js`), push nothing
   to the phone and show no toast; **at most one of each kind a goal** is in the hand (a second finding joins its goal's
   quality card, a second cascade on the same points waits for the first); **Not now** takes a card out of the hand and
   keeps it where it belongs (the quality record, the hypothesis open), from where it is taken again with no new call.
9. **The words** (`TERMS`): *Quality of <goal>*, *Fix all there*, *Change…*, *Or say what to change*, *<A> and <B>
   agree*; *Another level…*, *Edit* and *Change it in words* are said no more on a card's face.
10. **Built** with the specs of the decisions it lightens (spec 131 for 5–6, spec 132 for 1–3, 7–8, spec 133 for 4), each
   written to this decision, not to the heavier text before it.
The owner's call.

## 238. The past lives past the portal: the discard stays a pile that empties; Release keeps the chronicle, its lens showing what is not out yet and one line of the last version, the chronicle over the pane a chapter a version, the newest open, with a search (4 November 2026, the owner)

Why: the owner: *if decisions map to cards face up, and the specs being written and in review to the Orkmaster's piles,
is there a point in a page to look over all the past decisions or all the past specs?* Read against the window: the past
has no home in it. The discard holds only the goals done and not yet seen (`table/discard.js`, `ideas.seen`): once its
result is seen a goal leaves it, and its spec, its decision and its result are found only in the repository's files. A
person needs the past three ways: *why is it so* (answered in place, by a leader's bubble from its slices, §233, §237),
*what did we decide about X* (a search), *what was done this week or this version* (a timeline, which is also Release's
changelog, §213); reading every decision in a row is the decisions file's, not the window's. A pile of the past in the
discard was proposed first; the owner: *won't a pile that is always there in the discard weigh on the person? We meant
to tie into the wish to throw the discard into the portal*: the discard is an inbox that empties, and emptying it is the
reward. So the past goes where what is played goes, past the portal, to Release (the lich keeps what is gone); and, asked
whether the whole list then lies in the lich's lens: *no*, the lens keeps its own work. So:
1. **The discard is unchanged**: the goals done and not yet seen, and *Ready for main*; a goal seen leaves it, and the
   portal takes what is ready. It never holds the past.
2. **Release keeps the chronicle.** In Release's lens (its corner of the portal ring, §188; its tab where a project has no
   gate, spec 113) under what it shows today (the readiness, the draft *Unreleased* of the changelog, §213), **one line**:
   *Earlier: <the last version> · <its date> ›*. No list and no count in the lens. *Unreleased* is the chronicle's next
   chapter, not out yet: at a release it leaves the lens and becomes the chronicle's top chapter.
3. **The chronicle opens over the pane** (kind `chronicle`, as the pile's list and the place of the parties open; ← or
   Esc back to the lens): **a chapter a version**, the newest first and **the newest open**; each older chapter one line,
   *v0.3 · 28 Oct*, opened by a press. A chapter holds the goals that went through the portal in it and the decisions
   written in its span, by time; a decision of no goal (a hypothesis's verdict, a cascade, §233, §235) is a row of its own.
   **A search** at its top over the goals' titles, the decisions and the sections; its finds shown by chapter, the
   chapters with none folded away.
4. **A goal's row** opens the goal as it was: its spec as built (marked *changed by §<n>* where a later decision changed a
   point it rests on), its decision, its quality record (§234.4), and **How it works now ›**, the living spec of its part
   (spec 127). **A decision's row** opens its entry; its *Changes* and *changed by* are links, so a decision's history is
   walked without reading the list.
5. **What a version is**: the project's own (its release tags, else its changelog's headings); a project with none yet has
   chapters by week (*The week of 3 Nov*) until its first version. A goal seen but not through the portal is not in the
   chronicle: only what was played to the end is history.
6. **Not**: a tab or a page of its own for decisions (a second way into the same, and against the frame: no list column,
   no drawer, §206.2); a list of specs apart from their goals (a spec without its goal and its result says little); the
   chronicle on the phone, for now.
7. **The words** (`TERMS`): `chronicle` (*Chronicle*); *Earlier: <version> · <date>*, *The week of <date>*, *How it
   works now*, *changed by §<n>*.
8. **Built** by spec 134 (its goal row's quality record after spec 132 D; the rest stands alone), its parts by the
   cheaper model: **A. The host** (the chapters from the tags, the changelog or the weeks; the goals through the portal;
   the decisions by their dates; the search); **B. The face** (the line in Release's lens, the chronicle over the pane,
   a goal's and a decision's rows).
The owner's call.

## 239. A pile that waits for the limits: goals put off start one at a time after the reset, in the Orkmaster's order and by the week's pace; Keep it puts a goal by with no start of its own; the pile says why it waits (4 November 2026, the owner)

Changes: 133.1; spec 100 §1.

Why: the owner: *what if the face-down pile grows large, as now: our limits run out but ideas keep coming, and we do not
want to spend limits on their specs yet?* Dropping a goal costs nothing (no call before *Talk*, §133) and the pile does not
grow on the screen (its front card, three feet, thin edges, no count): so a large pile is fine, as long as nothing spends
by itself. Read in the code, something does: at the reset every goal put off with *Later, by itself* starts Talk **in the
same pass** of the host's clock (`gui/ideas_route.py` `route_tick`), with no queue and no bound, the reserve read from one
snapshot that does not yet see the calls just begun. Twenty ideas put off spend the new week's first hour on the backlog
and fill the hand with twenty goals' questions at once. And *Later* is offered only when the limits run low, so a person
cannot simply put an idea by without it starting by itself one day. So:
1. **After the reset, one at a time**: the goals put off start Talk one after another, **in the Orkmaster's order** (the
   pile's, the person's *Next* sets it); the next starts only when the one before is out of its Talk (its round's calls
   done and its questions answered, or it left Talk): the hand holds one backlog goal's questions at a time. A goal the
   person starts by hand is not in this queue.
2. **By the week's pace**: before each start the week's pace is read again (`idea_target.pace`): *ahead*, the next goes;
   *behind*, the queue waits and is looked at again on the clock's next pass; the reserve held as today. The backlog never
   spends the week the work needs.
3. **Keep it**: the route card offers **Keep it** at any time (beside *Talk*; *Later, by itself* stays beside it when the
   limits run low): the goal lies in the pile with no start of its own, until the person presses *Talk*. Nothing is spent.
4. **The pile says why it waits**: under *In analysis*, while goals put off wait for the reset, its line says *waits for
   the reset · <day> <time>* (a state, never a count), as *writing: …* and *talked over: …* say what it is on.
5. **The words** (`TERMS`): *Keep it*; *waits for the reset · <day> <time>*.
6. **Built**: 1–2 at once, on the host (`route_tick`), with their tests (the backlog's order, one at a time, the pace
   behind holding the queue); 3–4 with spec 130's first part.
The owner's call.

## 240. The hand is the person's move only: a goal that goes on by itself sends no card; the decision all leaders agreed on waits in the column, not in the hand, with *Change…* and *Start now* in the pile's list (4 November 2026, the owner)

Changes: 206.3, 237.8; spec 120 §3.5.

Why: the owner, thinking how to make an idea's way to a decision, a spec and its work simpler to see: *at each step a
card flies into the person's hand to confirm it, right?* Read in the code, less is asked than it looks: a goal goes to
Talk by itself (`AUTO_TALK`, spec 120 §2.1), a decision all the leaders agreed on is confirmed by itself after its wait
(spec 120 §3.5), a plan starts by itself; the hand already holds one stack a goal and a lane, its most urgent card on top
(`hand/stacks.js`). But **the decision all agreed on still lies in the hand** while its wait runs, a card with a clock
that asks nothing: the eye reads every step as a confirmation. The column already shows each step by where the card lies
(§224). So:
1. **The hand holds only the person's move**: a question, a disagreement (a no, a hearing, a fork), a cost grown, a
   failure, a change or a quality card to answer, a hypothesis due. A goal that goes on by itself sends **no card**: its
   card in the column turns and moves (§224's piles), and that is how the person sees it go.
2. **The decision all agreed on waits in the column**: while its wait runs (spec 120 §3.5: not held, not yet ended) its
   `decision` card is not dealt into the hand. Its goal lies face down in *In analysis* (§224), and the pile's line says
   it: *decided: <short> · starts its spec at <time>*. In the pile's list (§206.3, pressed) its row has **Change…** (its
   decision card comes into the hand, lifted: its wait is held, `ideas.ripe_hold`, so the goal lies put off in *At work ·
   later* until it is confirmed or sent back to review) and **Start now** (`ideas.confirm`, as To review's *Start now*),
   beside *Next* and *Remove*. Held (*Later*), it is the person's move again: in the hand as today.
3. **Unchanged**: a decision with a leader's no, a hearing or a doubt (no wait, spec 120 §3.5) is the person's move and
   lies in the hand; one stack a goal and a lane (§167.7); the face-down card cannot be picked (§206.3).
4. **The words**: *decided: <short> · starts its spec at <time>*, *Change…*, *Start now*.
5. **Built at once**, on the page (the hand's rows, the pile's line and list), its tests the hand's and the column's.
The owner's call.

## 241. The face-down card's ring says where the goal is: the heads of who has it in its middle, laid by how many; a play in its middle while an agreed decision waits, its ring counting the wait; filled in the rune's colour as the spec is written (4 November 2026, the owner)

Changes: 206.3, 240.2; spec 128 B.3.

Why: the owner: *how does the way from an idea and its Talk to the spec being made look now? We do not throw cards to
the leaders. I see it so: while Talk runs (the cheapest of our steps) the middle of the back shows the heads of the
leaders it talks with (empty for the Orkmaster); once the idea is talked through a play appears in the middle of the
ring, and a press starts the work on the spec; then the leaders' faces show in the middle again, and the ring fills with
the rune's colour.* Today the face-down card has three looks only (its ring running, yellow and still, at rest), and the
middle of its ring is empty; cards fly to the leaders' lanes only at work. Agreed, with three changes: the leaders of
Talk answer at once (a call each, in threads, `core/idea_talk.py`), so their heads stand together rather than take turns;
the play is the agreed decision's *Start now* (§240), its ring counting the wait, not a question; the ring fills by what
is written, never by the clock. And, for the heads: *not in a row: laid by how many, up to four: one large in the middle,
two a row, three a pyramid, four a square*; past four, the owner offered *+2* in the last place; the house says no number
(the stacks' *edges, never a number*), so the heads past four lie as a fan behind the fourth. So:
1. **The middle holds the heads of who has the goal now** (§133.3's rule, on the column's card): the route's leaders
   while it is in Talk and while its spec is written; **empty** while the Orkmaster reads and routes it (its ring runs,
   as today). Laid by how many: **one** in the middle; **two** side by side; **three** a pyramid (one over two); **four**
   a square, two by two; **more than four**, the square with the fourth place's head fanned over the rest (their edges
   behind it, as a stack's, peeking clearly), **no number**. One and two heads are a head's size; three and more a size
   smaller, so **the ring keeps room around them** (the owner, on the first pictures). A head whose call is still running steps (`.is-working`, as at the
   portal's corners); one that has answered or written stands still. Reduced motion: none steps.
2. **A play in the middle while an agreed decision waits** (§240): the heads give way to orkUI's play sign, and the
   ring counts the wait down in its eight places (the eighths the ring was drawn for, §232.4); the pile's line says
   *decided: <short> · starts its spec at <time>* as §240 has it. A press on the play is **Start now** (`ideas.confirm`):
   the one press a face-down card takes besides the pile's list (§206.3: the card itself is still never picked).
   *Change…* stays in the pile's list. A decision with a leader's no, a hearing or a fork shows no play: its ring is
   yellow and still, and the move is in the hand.
3. **The ring fills in the rune's colour as the spec is written**: once confirmed, the share of the ring filled is the
   share of the route's sections written, the Orkmaster's join the last share (`sections` and `sketch`); the heads in the
   middle are those still writing. Filled whole, the card turns face up into *To review* (§224). The fill is what is
   written, never the time passed.
4. **Only the pile's front card** shows this; the cards under it show their edges as today. It holds under §236 (the
   ring centred in the part that shows).
5. **orkUI's own parts**: the sigil's arc (`--_arc`), the rune's colour (`.rite-<element>`, `--_rite`), the play sign and
   the heads; the heads' places in the ring are the page's layout (no colour, font or corner of its own). Anything the
   ring needs that orkUI lacks is drawn in orkUI first, then copied.
6. **Built** after §240, on the page (`table/piles.js` `DownCard`, the column's sheet) with what the snapshot gives (the
   route's leaders, who has answered in Talk, which sections are written; a field added to the node where it lacks one),
   its tests the column's browser test.
The owner's call.

## 242. A new goal is matched against the face-down pile when it is sent: one that looks like part of another is offered to it in the field, *Add to it* or *Keep apart*, by code and with no call; the backlog is grouped once at the reset; nothing is merged without the person's yes (4 November 2026, the owner)

Changes: 234.5, 239.1; spec 128 A.1.

Why: the owner: *when a new idea is added, let it be checked against the face-down cards and joined with another idea
if they are related, so there are fewer runs from idea to spec.* Read in the code: the Orkmaster already judges a
*collision* (spec 71, `core/idea_collide.py`), but later and for another end: two goals of different parties whose plans
touch the same files, one cheap call to tell a collision from a coincidence, against conflicts at work. Nothing matches a
new goal against the pile when it comes in, where joining costs least: before Talk, a goal takes words in with one
`decide` call at most (§234.5), after its spec it takes them with its sections written again. Joining has its own risk:
two things glued into one goal, its spec written about both, a goal too big to land. So:
1. **Matched when it is sent, in the field**: at the + card's **Send** (§206.1), code compares the new goal with the
   face-down cards (*In analysis*, §224): its words against their titles and *Asked*, and the parties and parts of the
   map its route gives (the route is code's, no call). A match is said **in the field itself**, before it closes: *Looks
   like part of: <title>*, with **Add to it** and **Keep apart**. No card comes to the hand, no model is called; with no
   match the field sends as today.
2. **Add to it is §234.5's *Add to the goal***: the new words are written into that goal's *Asked*, kept as written and
   marked as the second idea's (its time, and its rune's place kept in the goal's history); a goal whose decision is
   worded already has it worded again (one `decide` call, its cost said on the button).
3. **Only before its spec**: a goal is offered for joining only while it lies face down before its sections (`raw`,
   `routed`, `talk`, `decided`); a goal whose spec is being written or is made is never offered (joining would write its
   sections again): the new goal goes on its own, or by *Make it a change* (§206.5).
4. **Not too big**: no match is offered when joining would add more than one party to the goal's route, or would make its
   *Asked* longer than a goal's words are kept (`GOAL_CHARS`): small goals land better.
5. **The backlog grouped once at the reset**: before §239's queue starts its first goal, the Orkmaster makes **one** call
   on the cheaper tier, no tools, over the titles of the goals put off (`collide`'s bounds), and answers groups that look
   like one; they come as **one card** in the hand, *These look like one goal*, each group with **Join** and **Keep
   apart**, and **Not now**. The queue waits for that card only while it lies lifted; not answered, the queue goes on.
6. **Nothing merged without the person's yes**, and **a joined goal can be split** while it has no spec: **Split** on its
   page gives each idea's words back to a goal of its own (its rune kept), the decision worded again where there was one.
7. **The words** (`TERMS`): *Looks like part of: <title>*, *Add to it*, *Keep apart*, *These look like one goal*, *Join*,
   *Split*.
8. **Built** by a spec of its own (spec 135), its parts by the cheaper model: **A. The match** (code: the words and the
   route's parties and parts; the field's line; *Add to it* through §234.5); **B. The backlog's groups** (the one call,
   the card, the queue's wait); **C. Split**. A first: it stands alone, and §234.5's *Add to the goal* is built with it.
The owner's call.

## 243. The project's own remote is the phone's way away from home: the phone drops goals into a branch of their own and reads the journal; whoever works takes a goal, the computer or a cloud session, and says so in the journal; a private repository only; the mailbox waits; the Board on a branch is the next step (4 November 2026, the owner)

Changes: 219.2, 219.3, 219.8, 221.1, 229, 230.6; spec 103, spec 136.

Why: the owner, after the phone was made half the product (§218): *let the phone be more on its own: tied straight to
the repository, it reads the status from there and puts goals into it, marked as not yet read by AI; the work on the
computer or in cloud sessions changes git now and then, and the phone shows it.* Read in the code: half of it is built.
The journal (§229, `realm/remote_journal.py`) already sends the project's status, its events and its spend to a branch of
its own, `orkboard/journal`, by git's plumbing and without force; what is missing is the other way (the phone to the
repository) and the phone reading the journal. The mailbox of §219 is not built (no `mailbox/`, no `relay/`, no
`mobile/`), and with it a goal dropped away from home waits until the person's computer wakes; through the repository it
can be taken by whoever works: the computer at home, or a cloud session while the computer sleeps, which is the indie
developer with a day job (§218) at work. What the repository cannot be: live (a commit every few seconds is noise, and the
journal goes every 15 minutes, §229.4), a push to the phone, or private by itself (a public repository shows the goals to
everyone). A token on the phone can write the whole repository, the code too: a fine-grained token is given per
repository, never per branch. And the Board itself lives in `.orkcraft/`, which git ignores: a cloud session has no Board
to lay a goal on. So:
1. **The project's remote is the phone's way away from home**, for what can wait: the phone drops goals into it and reads
   the journal from it. On the same network, or through Tailscale, the phone talks to the computer as today (spec 34),
   and that stays the way of the live hand. **The mailbox of §219.2–3 waits**: it is built only if the repository's way
   falls short (a project with no remote on GitHub, a person who will not give the phone a token). Push through FCM
   (§219.4) stays, for what needs the person now.
2. **The goals go to a branch of their own**, `orkboard/inbox`: it shares no history with the code, is never merged,
   holds no workflow, so no CI runs for it (as §229.2). The phone writes **one file a goal**, `inbox/<device>/<id>.json`
   (its words, its rune, its party, its type, its marks, when; its photos beside it), and **only adds**: it never edits
   or removes a file. Nothing else writes that branch.
3. **"Not yet read" is no mark in the file**: a goal is in the inbox and the journal has not named it. The phone shows it
   as a face-down card with the person's own words (§222.2), *Waiting to be taken: your computer or a cloud session will
   read it*.
4. **Whoever works takes a goal, and says so in the journal**: the computer (and, in the next step, a cloud session)
   reads the inbox at its rhythm, writes each goal not taken into the journal's `taken.json` (the goal's id, who took it,
   when), and **lays it on the Board only once that push went through**, through `ideas.add` as the + card does; its slug
   on the Board goes into the next journal. **The journal's push without force is the lock**: two that take the same goal
   both commit, one push is refused, that one reads the journal again, finds the goal taken, and lays nothing. A goal is
   taken once; one taken and not laid (the add refused) is said in the journal and on the phone, with the add's words.
5. **The phone reads the journal**: `status.json` beside `status.md` (the goals by pile and phase, what waits in the hand
   and needs the person, what failed, the taken goals, when it was written), read through GitHub's API with its ETag, so a
   read with nothing new costs nothing; every minute while the app is open, never in the background. What it shows says
   when it was written (*As of 14:02*), never as if it were now.
6. **A private repository only**: GitHub's API says whether a repository is private, so here Orkboard knows it (§230.4's
   *the person's word* is for a remote it cannot ask). On a public one the phone refuses in plain words: *This repository
   is public: goals sent through it would be seen by everyone. Make it private, or use the phone at home.*
7. **The token is said plainly and kept where it is safest**: a fine-grained token for that one repository, *Contents:
   read and write*; Settings and the phone say what it can do (*This token can change any file of the repository, the
   code too; Orkboard writes only orkboard/inbox*) and advise a rule on `main` (a pull request needed). It is kept in the
   native frame's Keychain (spec 103), in the installed web app's storage until then, said so; removed from the phone, it
   is gone from it. Signing in through GitHub, when the native frame is built (its device flow does not answer a web page).
8. **The journal becomes the user's too** (this changes §230.6): it is asked for when the phone is paired with a remote,
   in the words of §229.1, and its rhythm is the forge's for a contributor; for a user, 15 minutes, and at once when a
   goal is taken or something needs the person.
9. **The next step, not this one: the Board on a branch**, so a cloud session can carry a goal through Talk, the spec and
   the work, not only take it: what of `.orkcraft/` goes, how two writers share it, what stays local (the tokens, the
   sign-ins). A decision of its own, after the first step is used.
10. **The words** (`TERMS`): *inbox* (the branch the phone drops goals into), *taken*, *Waiting to be taken*, *As of*.
11. **Built** by spec 136: **A.** the journal's `status.json` and `taken.json`; **B.** the inbox read and taken on the
    host, with the lock; **C.** the phone's way through the repository (its settings, its reads, its + card); **D.** the
    words. Spec 103's relay stays for push; §219's mailbox is not built until (1) says so.
The owner's call.

## 244. The Board lives in the project's repository: its whole state on a branch of its own, `orkboard/board`, one holder at a time by a lease; the computer and a cloud run on GitHub Actions are two workers of one Board; the phone's answers go through the inbox too; secrets, sign-ins and logs stay on the machine (4 November 2026, the owner)

Changes: 219, 229, 243.4, 243.9; spec 35 §13, spec 136; spec 137.

Why: the owner, after §243: *GitHub itself can run AI in CI, on a push to a branch?*, and then: *the Board must be kept
in the repository, that is the key decision here.* Read in the code: half of the Board is in git already. Its pages (the
parties, the goals, their sections: the specs) live in a worktree of their own, `<state_dir>/board/`, and every change is
a commit on the work branch (spec 35 §13), so the orks read each other's specs; they are pushed only by `ideas.push`. What
is not in git is the Board's state: each goal's `state.json` (its phase), `plan.json`, `route.json`, `talk.jsonl`,
`pick.json`, `lens.json`, the parties' `goals/`, `roles/`, `kinds.json`, `project.json`; without them a worker that is not
the person's computer has the specs and no Board. Beside them lie what must never leave the machine: a goal's
`secrets.json`, `sign-in/`, the server's `drive.json`, the worktrees, the logs (prompts and answers, §229.3). GitHub
Actions can run Claude Code on a runner (the CLI, signed in by a secret), but a push to a branch runs the workflow of the
commit pushed, never `main`'s: an orphan branch with no workflow runs nothing (§243.2 rests on it), and the phone's token
cannot add one (a workflow file needs the *Workflows* right, which *Contents* does not give). A workflow on `main` is run
by `workflow_dispatch` (an API call) or on a `schedule` (GitHub may delay it); each run is billed by the minute, rounded
up a job, so a run every few minutes that finds nothing spends a quota on nothing. So:
1. **The Board lives in the repository**: its pages **and** its state on a branch of its own, `orkboard/board`, sharing
   no history with the code, never merged, holding no workflow, so no CI runs for it (as §229.2, §243.2). It is the truth;
   `.orkcraft/` on a machine is that machine's working copy of it. The work branch keeps the pages as spec 35 §13 has it,
   written from the Board's branch by whoever holds the Board, since the orks' worktrees are cut from it. What goes:
   `pages/` (parties and goals, as today), `ideas/<slug>/` (all but `secrets.json` and the worktree), `goals/`, `roles/`,
   `kinds.json`, `segments.json`, `project.json`, `checks.toml`, `canvases.jsonl`, the goals' photos (each at most 2 MB).
   **Never**: `secrets.json`, `sign-in/`, `drive.json`, `worktrees/`, `logs/`, `usage/`, `crashes/`, `repair/`,
   `screens/`, `claims.json`, anything not listed; every file read for a secret's shape before it is committed (§229.3's
   `scrub`), one that has it held back and said.
2. **One holder at a time, by a lease**: `lease.json` on the Board's branch (`by`, the machine's or the run's name; `kind`,
   *computer* or *cloud run*; `until`, ten minutes ahead). Only the holder writes the Board; the lease is taken and renewed
   by a push without force, so two cannot hold it at once (§243.4's lock, grown to the whole Board). The computer with
   Orkboard open renews it every three minutes and so holds the Board while it is awake; asleep, the lease runs out and a
   cloud run may take it; a cloud run gives it back when it ends. The computer that wakes while a cloud run holds the Board
   reads it and waits, said in a line: *A cloud run has the Board: it gives it back when it ends (at most 30 min)*. The
   phone holds nothing: it only reads and drops into the inbox.
3. **The holder pushes the Board**: its writes stay one commit for 10 s (spec 35 §13), and the branch is pushed at most every
   two minutes while it changes, at once when a card for the person comes to the hand, and when the lease is given back. A
   worker that takes the lease fetches the branch first and works only from it.
4. **The taking of a goal is the holder's** (this changes §243.4): the holder reads the inbox and lays its goals on the
   Board it holds; `taken.json` stays, as what the phone reads, no longer as a lock.
5. **The phone's answers go through the inbox too** (§243.2 widened): an answer to a card of the hand (a question of Talk,
   a hearing, a decision) is a file of its own beside the goals, `inbox/<device>/<id>.answer.json` (the card's id, the
   answer), taken by the holder as a goal is. The hand works away from home with nothing of ours in the way; push (FCM,
   §219.4) only says that something waits.
6. **A cloud run on GitHub Actions**, the second worker: a workflow on the default branch, `.github/workflows/orkboard.yml`,
   written by Orkboard only on the person's yes and committed as the person commits (it is their repository's file). It runs
   on `workflow_dispatch` (the phone calls it when it drops a goal or an answer, if its token has *Actions: read and write*;
   else it does not) and on a `schedule` the person chooses (*every 2 hours* at first, *never* offered); `concurrency` one
   run at a time. Its first step asks the lease: held by an awake computer, it ends at once (the computer does the work). It
   installs Orkboard and Claude Code, takes the lease, reads the inbox, carries each goal as far as the limits allow, pushes
   the Board, gives the lease back; the job's timeout, 30 minutes.
7. **What a cloud run does, for now**: the reading of a goal, all of it (the Orkmaster's route, Talk's rounds, the leaders'
   sections, the plan), and the person's answers taken in; **not the work**: a task writes code, lands it through the gate
   and is seen in Play, which want the person's computer, its tools and its secrets. A goal whose next step is work waits
   for the computer, said on its card (*Planned: the work starts on your computer*). The work in a cloud run is a decision
   of its own, when the reading has been used.
8. **What it spends, said plainly**: the run's minutes (the plan's quota of Actions for a private repository, then by the
   minute) and the model's calls: **either** the person's subscription (`claude setup-token`, the secret
   `CLAUDE_CODE_OAUTH_TOKEN`), which shares the week's limits with the computer (§239 counts them as one), **or** an API
   key (`ANTHROPIC_API_KEY`), paid by the token, with a ceiling a run the person sets (*At most $1 a cloud run*), at first
   $1. Settings say which, and what a scheduled run costs when it finds nothing (*about a minute of Actions*).
9. **The secrets stay on the machine, so does what needs them**: the Board's branch holds no secret, a cloud run gets only
   the model's secret from GitHub; a goal that needs a secret of its own is not read in a cloud run past the step that needs it.
10. **The work branch and a rule on `main`**: the Board's pages are committed to the work branch by its holder (spec 35
    §13); a project that keeps a rule on `main` (§243.7's advice) keeps `dev` as its work branch, so the pages land there.
    A cloud run writes the work branch's pages only; never code.
11. **A private repository only**, as §243.6: the Board holds the goals' words, their specs and Talk. On a public one the
    Board's branch is refused in words, and the computer keeps the Board as today.
12. **Orkline reads the same Board** (CLAUDE.md: the state keeps Orkline's names): the Board's branch is laid out as
    `.orkcraft/` is, so a working copy is the branch's files and nothing is renamed.
13. **The journal stays the phone's** (§229, §243.5): small, the Board's status for a phone; the Board's branch is the
    workers'. The mailbox (§219.2–3) moves further off: the inbox and the Board's branch do its work.
14. **The words** (`TERMS`): *the Board's branch*, *holds the Board*, *cloud run*; *A cloud run has the Board…*,
    *Planned: the work starts on your computer*, *At most $1 a cloud run*.
15. **Built** by spec 137, after spec 136's A and B: **A.** the Board's branch (what goes and what never does, the
    working copy kept from it, the scrub); **B.** the lease and the pushes; **C.** the answers through the inbox (host and
    phone); **D.** the cloud run (the workflow written on a yes, its steps, the ceiling, `orkboard drive cloud-run`);
    **E.** Settings and the words. Checked before it is built: Actions' quota and price on GitHub's own page; Claude Code
    signed in on a runner by both secrets.
The owner's call.

## 245. The day is read from the resets, never drawn as a schedule: the column stays its piles; a potion hovered lights the goals that wait for it; its hour under it only when it runs low; a goal put off waits for the window that fits it, its hour on its row; what asks nothing of the person takes a reset while they are away; the day as a line of time over the pane, from the potion (4 November 2026, the owner)

Changes: 189.2, 192.1, 239.1, 239.4; spec 114 §3.

Why: the owner: *what if the Orkmaster's column became the day's plan: the times the connected tools' limits reset, and
the specs' writing and their work tied to those times? Only without making the window harder*, asked as a product manager
and a designer. Read against the frame: the column is three piles by where a goal is (§206, §224), 128 px wide (§236); an
axis of time in it gives one place two orders, and the eye loses which one the cards lie by; it would read as a list or a
calendar's grid, which the frame refuses (CLAUDE.md; §215.1: one line of cards along time, never a grid). A schedule of
blocks (*14:00–16:00: the work of …*) promises what cannot be known: a goal's cost is *about* (§121.3), Claude's five hours
count from the first call, each tool keeps windows of its own; on its first day it would be wrong. An hour said as *not
before 14:05* is honest; a schedule is not (§218: nothing promised before it is built). And time is already half on the
Board: a spec in To review starts at a clock time (§224), the pile says *waits for the reset · <day> <time>* (§239.4), the
potion's words say when each window comes back (§192), a goal put off waits for the reset of whichever window ran out
(`idea_target.reserve_held`), a plan's tasks for the window's (`keeper.window_until`). What is missing is the link between
them, and one thing no picture gives: **the person's own hours**. Whom Orkboard is for works a day job (§218): a five-hour
window that comes back at 14:00 comes back while they are away; the work can go on without them, Talk and a review cannot.
So:
1. **The column stays its piles**: no axis of time in it, no hours along it, no schedule; where a card lies says where its
   goal is (§206, §224), unchanged.
2. **A potion hovered or focused lights the goals that wait for it** (§189.2 widened): beside the tabs' marks it lights
   today, the column's cards whose goal waits for that tool's reset (put off, held by its spent window, a spec's start at a
   clock time on that tool) stay as they are and the others dim (orkUI's muted ink, never hidden). **A card hovered does the
   reverse**: its tool's potion shows the goal's next step hatched off its top, as a lifted card's (§176.2). Its words add
   *goals wait for its reset* when some do, never how many (§67).
3. **The hour under a potion only when it says something**: while the tool has room, under it the shares as today (§192);
   at the danger's level or empty, the now share's place says **when it comes back** (*back 14:00*; *back Mon 09:00* when
   it is the week that ran out), the words both as today. As colour is a signal (spec 40), so is the hour.
4. **A goal put off waits for the window that fits it, its hour on its row**: today the goals put off start one at a time
   after the reset, by the week's pace (§239.1–2). The Orkmaster now gives each one of the queue **its window**: the next
   goal's step and its cost (§121.3) against what the coming window holds above the reserve; one that does not fit waits for
   the next window, the goals behind it in the order unchanged. The pile's line says the front's hour as §239.4 has it; in
   the pile's list (§206.3) each row says its own **not before 14:05**, and a goal at work held by a spent window says
   *the work goes on at 14:00*. Always the earliest hour, never a span and never a countdown (§224).
5. **The person's hours**: one setting, **When I am at the computer** (days and hours, the machine's local time; *weekdays
   19:00–23:00*, *weekends all day*), empty by default, and empty nothing changes. With it, the queue and the windows' holds
   are laid by what a step needs: **a step that asks nothing of the person** (a plan's tasks, the leaders' sections after
   Talk, Checks) **takes a reset while they are away**; **a step that will ask** (Talk's rounds, a review the work waits
   for) **is laid at the first reset within their hours**, so its questions come when someone is there to answer them, and
   the hand does not fill while they are away. A goal the person starts by hand, or drops from the phone (§221), goes at
   once, as today. The night (`night`, the reserve's, `idea_target.reserve`) is not this setting and stays as it is.
6. **The day, from the potion**: a potion pressed opens over the pane what used it, as today (§175.2), now **a line of
   time with *Now* across it** (§215.1's shape): behind *Now* what used it today; ahead, today and tomorrow, its windows'
   resets as marks and the goals that wait for them as cards on the reset they wait for (the step they will take in words,
   *Talk*, *spec*, *work*); the person's hours a lighter band when set. A row a tool, the one pressed on top, the other tools
   with goals waiting under it. It reads the same state as 2–5 and decides nothing: a card pressed opens its goal.
7. **Not now**: anchoring the window (a first call at a chosen hour, so the five hours come back when they are wanted) is a
   decision of its own, taken when 1–6 have been used; a schedule of blocks, an axis in the column, a countdown: never.
8. **The words** (`TERMS`): *back 14:00*, *not before 14:05*, *the work goes on at 14:00*, *goals wait for its reset*,
   *When I am at the computer*.
9. **Built** by spec 138: **A.** the link (2) and the hour (3), on the page, their tests the hand's and the column's;
   **B.** each goal's window and the person's hours (4–5), on the host (`route_tick`, `idea_target`), with tests (a goal
   that does not fit waits for the next window and the order holds; a step that asks is laid in the hours, one that asks
   nothing is not; no hours set is today's); **C.** the day over the pane (6). **Drawn first**, `docs/mockups/day/`: the
   column with a potion hovered, the potion's hour, the line over the pane; the owner's pick.
The owner's call.

## 246. The die is what moves, the door is the person, the bug hides: the die's up face Play and its front face the orks' work (*Stop all*, then *Resume*), rolled by the Board and never by the person; the door says whether the person is *Here* or *Away*, and the Board plans by it; the bug leaves the top row for the Orkmaster's menu and the place where something broke (4 November 2026, the owner)

Changes: 182.12, 190.2, 196, 197, 201.8, 230, 245.5; spec 112 §3, spec 118, spec 119 §4, spec 123 §7.6.

Why: the owner, after a review of the window as a product manager and a designer: *Stop all could go onto the die: its faces
turned, Stop all, Resume and starting the project; only I do not know how to make it clear*; *the door at the top could then
switch modes, at home or at work, and the Board would take it into account when it plans and how often it asks*; *and hide
the bug, I do not like it at the top any more*. Read against the frame: Play opens the game (dev's preview), Stop all stops
the orks; two things, often wanted at once (the orks work while the person plays the build), so one face cannot hold both,
and Stop all must stay one press and always seen (CLAUDE.md: money and safety always visible). A face turned by the person
is a hidden control (a face not up is never found; a turn is a different gesture on a mouse, a touchpad and a finger, and
nothing for a screen reader) and a toggle's old doubt (does the face say the state or what a press does?). But the die is
drawn from above (§190, orkUI's `.ork-die`, a cube in CSS 3D): **two faces are seen at once**, the up one and the front
one, and the up face already says what Play would show and rolls when it changes (§196, §200). Stop all is red whenever it
can be pressed (`table/door.js`), so the danger's colour sits in the corner while nothing runs and stops meaning anything
(spec 40: colour is a signal); and a halt is a moment, not a state: it kills what runs (`realm/halt.py`) and the Board's
clock starts new work by itself a minute later. An open door is an office's *come in*, a shut one its *do not disturb*: the
door says the person far better than it says a halt, and it is the face §245.5's hours lacked. The bug (§182.12, §197,
§230) is for a rare act about Orkboard itself, not about the project, and sits in the top row all day. So:
1. **The die's two faces**: the **up face is Play**, as §196 and §200 have it (the arrow, the spark or the pips, the cross,
   asleep the five); **the front face is the orks' work**: **■ Stop all**, muted while nothing runs, in the danger's colour
   only while something runs and spends; after a press **↻ Resume**. Each face is a button of its own (its own words and
   `aria-label`: *Play*, *Stop all: stop every run of this project's orks*, *Resume*); under the die two words, as under a
   potion: *Play · Stop all* (*Playing*, *Stopped*). On a phone the die is drawn large enough that the front face is at
   least 44 px.
2. **The Board rolls the die, never the person**: nothing is turned by a drag, a swipe or a key; when a face's state
   changes, the cube rolls onto it (`is-landing`, §200), so the roll is the answer to a press, seen once (§89.0; at once
   under reduced motion).
3. **Stopped is a state, Resume ends it**: *Stop all* kills what runs as today (`halt_all`) and the project is **stopped**:
   nothing starts by itself (no route, Talk, spec, plan or task, no queue of §239 or §245) until **Resume**, which starts
   again what the halt stopped (each task killed back in its place, started from its start, what it committed kept) and
   lets the Board's clock go on. A goal the person starts by hand while stopped resumes the project, said in one line
   (*The orks are back at work*). The host keeps what the halt stopped (`halt.py` grows a list of it), so Resume knows.
4. **The door is the person: *Here* or *Away***, at the top row's right end where Stop all stood (orkUI's `door/`, §201.8):
   **open, *Here***; **shut, *Away until 19:00*** (the hour from §245.5's hours when they are set, else no hour). Pressed it
   opens or shuts. **The hours lead, the door overrides**: with §245.5's *When I am at the computer* set, the door opens and
   shuts by it; a press holds the other state until the next edge of the hours (as a pause of notifications *until…*), then
   the hours lead again. With no hours set the door is the person's alone, open at first. One state for the person, the
   same on the computer and the phone (the phone's top row has the door too).
5. **What the door changes**: **Here**, as today: a step that asks starts when its turn comes and its cards come to the
   hand. **Away**: a step that will ask (Talk's rounds, a review the work waits for) is laid at the first reset after the
   door opens or the hours begin (§245.5), a step that asks nothing goes on (§245.5); the cards already in the hand stay
   there and send no push; a push is sent only for money and safety (a cost grown past what was agreed, paid going on, a
   run that must be stopped). Coming back the person finds what waits in the hand, never a count of it (§67).
6. **The bug hides as an icon**: it leaves the top row, and the top row's end is the door alone, the leaders' tabs the
   rest. **Report a problem…** is an item of the Orkmaster's menu (`table/menu.js`, beside Settings and Files; on the
   phone the crown's menu, `hand/upmenu.js`), opening the same panel (*What went wrong? (optional)*, **Fix it** when
   `repair.can`, §197). **Where something broke, it is offered there**: a crash the page caught (`crashes.js`) or a run of
   Orkboard's own that failed says *Report* (and *Fix it*) in its own line or card, its logs with it. **While a fix runs**
   the Orkmaster's line says it under the pane's title (`table/notice.js`: *Fixing Orkboard: …*); **a fix ready** is the
   person's move (§240), a card in the hand. The contributor's forge (§230) is reached the same way.
7. **Not now**: *Away, but ask me on the phone* (questions to the phone at chosen hours while away) is a decision of its
   own, when the door has been used; the door opening by itself when the person works at the computer while it is shut,
   the same; a third face of the die (its right one) for anything: no, the die is what moves.
8. **The words** (`TERMS`): *Here*, *Away*, *Away until 19:00*, *Stop all*, *Stopped*, *Resume*, *The orks are back at
   work*, *Report a problem…*, *Fixing Orkboard: …*.
9. **Built** by spec 139: **A.** the die's front face, its colours, words and rolls, and the bug moved (page); **B.**
   Stopped as a state and Resume (host: `halt.py`'s list, the clock held, the tasks started again), its tests (nothing
   starts while stopped; Resume starts what was killed; a goal started by hand resumes); **C.** the door, Here and Away,
   with §245's part B (host and page, the phone's top row), its tests (the hours lead, a press holds until the next
   edge, Away lays a step that asks in the hours and sends no push but money's and safety's). **Drawn first**,
   `docs/mockups/die-and-door/`: the die with both faces in each state, the roll after Stop all, the door open and shut
   with its line; the owner's pick.
The owner's call.

## 247. The window made lighter, nothing it does lost: the portal and the discard drawn only when they hold something; two words for putting a goal off, *Hold* and *Later*; the potions' sizes kept, the week said in words only when it is what runs out; a pile's foot without a cut name; the pane's title only for a goal; a lifted card says its title once; a tab's tool marks only where they differ; one place moves at a time (4 November 2026, the owner)

Changes: 176.3, 188.1, 189, 189.2, 192.1, 206.3, 239.3, 239.5; spec 104 §4, spec 111 §3.4, spec 114 §3, spec 128 B.3.

Why: a review of the window as a product manager and a designer (4 November 2026, the page at 1440 and 390 px on the column's
stub host, `tests/test_column_browser.py` `ColumnHost`), eleven points; the owner took 2, 3, 4 (keeping the bottles' sizes:
*three bottles of one size look dead*), 6, 7, 8, 10 and 11; 5 (Stop all always red) went to §246.1; 9 (two menus at the
Orkmaster) is not a double: the ▾ switches the project, the **…** holds Settings and Files, two jobs; 1 (the card's empty
window, half of every card) the owner looks at again. What was found: the portal's ring (*Main*) and the discard's dashed
frame take the table's right ~200 px on every tab while nothing is ready for main and nothing is done; the potion says two
shares four ways (the liquid, the bottle's size, *62%*, *week 80%*) and an unread tool is a bottle with *?*; a pile's foot
cuts a goal's name to seven letters (*Tidy th…*, *Rena…*), which says nothing; the pane's title on a tab with no goal picked
(*The whole project · through the Orkmaster*) repeats the open tab; a lifted card of To review says its goal's name twice,
its title and the line under it; the tabs' sword and shield (§189) say the same tool on every tab when every party runs on
one, and a potion hovered outlines them by 1 px, which the eye does not see; the running ring and the glowing runes move on
several cards at once and pull the eye from the side. And the words for putting a goal off, read in the code: **Later
today** (To review, `ideas.ripe_hold`) holds a goal **until Start now**, not until today ends; **Keep it** (§239.3) would
do the same and is already *do not drop it* (`table/dropgoal.js`) and *save this to-do* (`hand/todoform.js`): one word,
three meanings; *Later, by itself* (§121.3) starts it at the reset; the night's moon at an hour. *Put it back* is not one of
them: it lays a lifted card back in the hand and stays. So:
1. **The portal and the discard are drawn only when they hold something**: the ring with *Main* while a goal is ready for
   main or its checks run (§188.3–4), else no ring; Release's and Live's heads stay where its corners are (§188.1–2), asleep
   alone. The discard is drawn from its first goal done (the goal's flight lays it, §176.3); empty, nothing lies there, no
   frame and no word. The table gains the width.
2. **Two words for putting a goal off, each one meaning**: **Hold**: nothing starts it until *Start now* (today's *Later
   today*, and §239.3's *Keep it*); its card says *Held*; on a held card of To review *Back to review* stays its way back.
   **Later**: it starts by itself at an hour the Board says (*after the reset*, *in my hours* §245.5, *tonight*), the hour on
   its row as *not before 14:05* (§245.4); today's *Later, by itself* and the night are its cases. *Keep it* is only *do not
   drop it*; the to-do form's button is **Save**.
3. **The potions keep their sizes** (§192: the bottle the week, the liquid the 5 hours); under a potion **the now share
   alone**; the week's words (*week 80%*) only while the week is what runs out first, else in the potion's words for hover
   and a screen reader as today. **A tool whose limits were not read**: its mark, muted, with no bottle, its words *Limits
   not read*.
4. **A pile's foot without a cut name**: the rune, the time or the leaders' heads, the sign of its state (spec 128 B.3); the
   goal's name in the foot's `title` and words, and whole on hover as the card slides out (§236.2).
5. **The pane's title only for a goal**: on a tab with no goal picked the title says nothing (the open tab says whose eyes);
   the row keeps its back arrow and its **…**; a goal picked, its name and its phases as today.
6. **A lifted card says its title once**: a line that repeats the title is not drawn, and what the card says is one
   sentence (*Its spec is ready; it starts by itself in its turn.*), the rest behind its **…**.
7. **A tab's tool marks only where they differ**: the sword and shield's marks (§189) are drawn on a party's tab only when
   its Does or its Checks run on another tool than the project's default (§177.1), or on more than one (the dot); a Lean
   party keeps its faint shield. A potion hovered lights the goals that wait for it (§245.2) and the tabs whose parties run
   on it, as a tab is lit, not by a 1 px outline.
8. **One place moves at a time**: a motion that runs on (the ring's sweep, a rune's glow, a leader stepping) runs only on
   the goal picked, else on the first goal at work in the Orkmaster's order; every other card is still, its state said by
   its sign. A motion played once (a card turning, a flight, the die's roll) is §89.0's, unchanged.
9. **Unchanged**: the two menus at the Orkmaster (▾ the projects; **…** Settings, Files, and *Report a problem…* of
   §246.6); the card's size and window (§236.4) until the owner's look at the review's first point.
10. **The words** (`TERMS`): *Hold*, *Held*, *Later*, *Back to review*, *Save*, *Limits not read*; *Later today*, *Later,
    by itself* and §239's *Keep it* in `was`.
11. **Built** by spec 140, on the page, each with its module's browser test: **A.** 1, 4, 5, 6 (the table and the column);
    **B.** 2 (the words, the commands kept: `ideas.ripe_hold` is Hold, `ideas.route_later` is Later); **C.** 3, 7, 8 (the
    potions, the tabs, the motion).
The owner's call.

## 248. A card with a rune is picked by its rune: lit and still, the card risen and its edge in the ink; the corner brackets are only for a map's parts taken in picking (4 November 2026, the owner)

Changes: 152.4; spec 101 §2, spec 128 B, orkUI's `.ork-picked`.

Why: the owner: *picking a card lights its corners, which falls out of our window; it would be more natural to pick by
lighting its rune, and maybe a card a little larger*. The brackets came with §152.4, for picking: a map's parts (System's
containers, Design's screens) taken with a box as Warcraft's units, several at once and with no rune of their own, and
there they are right. Then orkUI's one `.ork-picked` came to mark everything picked: a goal's card in the column
(`table/piles.js`, `backcard.js`), on the lanes (`card.js`, `cascade.js`), its stacks in the hand (`hand/stacks.js`,
`stopcard.js`), a goal at the portal (`portal.js`), an answer chosen (`hand/choose.js`). A goal has a face of its own, its
rune (§206: a rune is a shape and a colour), and a frame drawn round it says what the rune can say from inside. Three
things are in the way and decide the look: a rune's glow, pulsing, already says *at work* (`ork-glow`, and §247.8 keeps one
place moving); orkUI is a pixel grid, so a card scaled by 1.04 blurs its pixel face and its heads; and a card hovered
already rises (a stack whole, the column's card sliding out, §236.2), so a pick that only rises cannot be told from a
hover. So:
1. **A card that carries a rune is picked by it**: the rune **lit and still**, at its full brightness (no pulse); **the
   card risen** by 3–4 px with its shadow, as a lifted card (§89), never scaled; **its edge in the ink**. It stays when the
   pointer leaves, which a hover does not. Every card of the picked goal is lit alike, in the column, on the lanes and in
   the hand, as today.
2. **The pulse stays *at work***: a picked goal at work pulses (§247.8 moves it, being picked); a picked goal at rest is
   lit and still; a goal not picked keeps its rune as it is. Light is the pick, the pulse the work.
3. **The brackets are only for picking** (§152.4): a map's part taken with a box or a press, with no rune, carries them;
   in orkUI a class of their own (`.ork-taken`), used by `table/picking.js` alone.
4. **An answer chosen** (`hand/choose.js`): its card carries its goal's rune, so it is picked as 1 says; the choices not
   taken stay as they lie.
5. **Said beside the look**: `aria-pressed` and `aria-current` as today; the pick is told by brightness and place, never by
   a hue alone (spec 40).
6. **Drawn in orkUI first** (CLAUDE.md: the design system is orkUI's): `.ork-picked` redrawn as 1, the brackets moved to
   `.ork-taken`, then copied (`python -m orkboard.design.orkui`); built by spec 141 on the page (`piles.js`, `backcard.js`,
   `card.js`, `cascade.js`, `stacks.js`, `stopcard.js`, `portal.js`, `choose.js` keep `.ork-picked`; `picking.js` takes
   `.ork-taken`), each with its module's browser test (picked: the rune lit and not pulsing, the card risen, no brackets;
   taken in picking: the brackets).
The owner's call.

## 249. A card's window is where it has something to show: the Orkmaster's column and the hand without one, the hand's kind a sign in its corner and who asks a small head beside it; the leaders' lanes keep it as a window onto the work, by its state and its craft, read from what the Board has (4 November 2026, the owner)

Changes: 236.4, 247.9; spec 101 §2, spec 128 B.3, spec 129 H2.

Why: the review's first point (§247): half of every upright card and every hand card is a window, and it is empty or holds
a sign and a small head; the column is 128 px wide and its cards 157 px tall; the hand's titles are cut in the middle of a
line. The owner, after `docs/mockups/card-windows/`: *remove them in the Orkmaster's column, and in the hand keep only the
kind in a corner (a question, a fork, an error); but for the leaders' lanes I would not remove them, rather make them more
interesting*. The three places say three things: the column *where* a goal is (its pile, rune, name and foot say it), the
hand *what is asked and by whom*, the lanes *the work itself*, and only the last has something a window can show. A lane
card's window that shows a picture for its own sake breaks the one look (CLAUDE.md: the races' heads the only pictures);
one that shows the work (what it made, how far it is) is the work's content, not the interface's picture. So:
1. **The column's upright card has no window**: its rune and its whole name (three lines at most; a longer one grows the
   card by a line, never cuts it), then its foot as today (the wait's bar and time, the leaders' heads at work, the count);
   its width 112 px (§236.3), its height its content's. The face-down cards keep their seal and size (§206.3, §236.1, §241).
2. **The hand's card has no window**: **its kind a sign in its top left corner** in its signal's colour (a question and
   a hearing the alert's, a failure the danger's, a fork, a decision, a hypothesis due, a cost grown, a change the muted
   ink's), **who asks a small head (16 px) in its top right corner**, never lost (a member asks only its leader, §104);
   under them **the title in three whole lines**, then the label row (the party, the gem when it spends). The card is
   about two thirds of today's height; the hand is as tall as the potions and the die set it. The + card and the lifted
   card (which shows what is asked whole) are unchanged.
3. **A lane's card keeps its window, a window onto the work**, by the task's state: **waiting**, the head of the seat
   that will take it, faint (*an elf takes it next*); **at work**, its steps (§207: the pips, the step now, who does it
   with the busy mark); **failed**, the alert and its reason in one line; **done or being checked**, **what it made, by its
   craft**: **Tech** the files it touched with their lines added and taken as pixel bars (`git diff --numstat` of the
   task's commits, three files at most); **Design** the screen it changed, before → after when both are known (Play's shot
   or the sketch's canvas); **Art** the asset itself at its pixels (the file the work made, an image); **Release** its
   checks on the way into main (§188.3: the skeletons' ticks); **Product** the hypothesis it tests and its state (§235);
   **Run** and **LiveOps** the dated event it waits for (§215). A craft or a task with nothing of these keeps today's
   type sign. Never a picture for its own sake; all of it read by code from what the Board has, no call to a model.
4. **One face**: every card keeps the frame, the header and the label row, so the short cards and the tall ones read as
   one deck; the height says where the work is.
5. **The words** (`TERMS`): *takes it next*; the craft windows' words are their data's.
6. **Built** by spec 142: **A.** the column's card and **B.** the hand's card (the page), each with its browser test;
   **C.** the lane's windows of waiting, at work and failed (the page, from the snapshot's task as it is); **D.** the craft
   windows (the host serves a task's `made`: Tech's numstat, Design's and Art's image paths, read by code; the page draws
   them). The mockup is the look: `docs/mockups/card-windows/`.
The owner's call.

## 250. A task is told what the gate holds it to: the Board's pages put back by code, a page's change tested by its browser tests, a test that could not run says what would run it, no key promised that a tool does not take, and the words on the table say what is so (4 November 2026, the owner, after a trial with real tools)

Changes: 182.1 (what *Install and test again* installs), 247.1 (what counts as holding something at the table's end), 249.3 (the words of a lane's waiting window); spec 81 §2, spec 107 §1, spec 142 C.

Why: the owner had spec 132 B run through a local Orkboard with real calls, Codex on its subscription and Antigravity by its key, and asked that everything it found be mended: *let's make a decision and a spec to fix everything you just found, and land them in main*. The goal took 26 minutes and 2.94 million tokens, and stopped at 2 tasks of 4 with 10 browser tests newly red. The thinking was good: Talk heard the leader in about 15 thousand tokens, Decision and the plan said the goal back faithfully. The doing was lost to Orkboard's own contradictions, not to the tool's work: every one of the four task sessions wrote a plan into the Board's page because the Architect's role tells it to, the gate refused it, and 1.29 million tokens (44%) went on attempts that left nothing in `dev`. So:
1. **A task is never told to write what the gate refuses.** The Architect's role stops asking for a plan *in the task's own file*; the plan is the Board's and is made before the task. A party's Lean leader doing a task is told it does this task, it does not shape it: a code task changes code. The spec page a task is given to read says it is the Board's, to read and never to write.
2. **The Board's pages touched by a task are put back by code**: at the gate, with no session called and no try spent, in one commit of Orkboard's, a line in the task's log saying so. A session is never asked to undo what Orkboard itself committed (it left the pages as `HEAD` has them, and `HEAD` already held the edit). A task with nothing left after that has changed no file, and is told so.
3. **A change to a page is tested by the page's browser tests.** The gate has run nothing but its `always` tests for a touched `.js` or `.css`, so a change that broke 10 tests passed green. A project names them in `orkcraft.toml` (`[gate] browser`, patterns); with none named nothing changes. A browser module skipped for want of a browser is said on the task's result, never counted as passed, and does not hold the merge. The plan keeps a code task and the tests it breaks in one task.
4. **A gate that could not run says what would run it.** *Install and test again* offers only what installs the tool that is missing: pytest missing never runs `npm ci` in another folder. Python stays the person's (§182.1 stands): the card names the command to run, and its button is *Test again*. With no `.venv`, the Python on the `PATH` that has pytest is asked before Orkboard's own, which never has it under `uv tool`.
5. **No key is promised that a tool does not take.** With `GEMINI_API_KEY` set and no Google sign-in, Antigravity 1.5.0 asked for the sign-in and ran nothing, while its card said *Uses the key in your environment*. Antigravity offers no key until one is shown to work; the card says it signs in with Google. Whether the trial's key was a good one could not be told from outside it, so the owner's one check (spec 143 D) can put it back; the promise does not stand until then.
6. **Release asks when there is a release to ask about.** Its reading, and its three questions, came at Start with nothing yet made, and its card lay over the result the person was waiting for. It reads when the first goal is ready for main, or when the person opens its lens. In a lane, a goal's own card lies in front of a party's question that blocks nothing.
7. **The words on the table say what is so.** A task to look at says *To look at* and one merged says *Done*, never *Planning*. A leader's seat says the leader takes it next, never *a Grunt*. A goal with a task failed or still to do is not ready for main. The Board's own commits are not a pile at the table's end (§247.1): they go with the next goal. Words stay inside their card; the + card's turned corner lies clear of the cards beside it.
8. **The spend says what it knows.** Codex's prices are read from OpenAI's published page, with its date (`OPENAI_PRICES` has been empty, so every call of Codex was unpriced); a model not on it stays unknown, and a report with no price known says so, never `$0.00`. A call's record names the model that ran, not its tier. `orkboard drive stop` takes `--folder` as its fellows do.
9. **Not decided here**, left to the owner: a failed task's *Start again* with a line from the person; a task of the `laborer` tier running on its seat's `warrior` (the trial's 448 thousand tokens for 20 lines); how long a gate may take with browser tests in it. The silently kept project kind that the trial seemed to show did not come back in three widths and is dropped.
10. **Built** by spec 143.
The owner's call.

## 251. One card, 5 : 7, read by its four corners: a card stands while it plays and lies face down while it waits; the Orkmaster's column never scrolls and gives way to the window; the hand's card is cut under its title; a goal's start turns its card up and the Orkmaster deals it to its leaders (5 November 2026, the owner)

Changes: 206.3, 206.11, 236.1, 236.3, 241, 249.1, 249.2, 249.4, 70.1; spec 128 B.1, B.3, spec 142 A, B.

Why: the owner, looking at the window: the cards came in many sizes (§249 cut each to its words) and should keep one
shape, and every card should say the same thing in the same place, the new goal's card too. The talk ran through
`docs/mockups/card-ratio/` in six versions; what it settled: a card laid on its side face up was too wide (and turned
the meaning §206.3 gave lying), cutting a column card at its foot with nothing over it looked broken, whole 5 : 7 cards
do not fit the column of a 1366 × 768 laptop, and the owner wants the column never to scroll on the desktop (*scrolling
only on an opened card and on the table*). Card games read a card by its corners, keep a card face down while it is not
yet in play and lay a card on its side while it does not act; a place hides part of a card only where something covers
it. So:
1. **Every card is 5 : 7**, at two sizes on the desktop: **144 × 202** (the column, the hand, the lanes, the discard)
   and **404 × 566** (opened, and a new goal); the phone's hand **80 × 112**; and **the Orkmaster's hand 56 × 78**, the one
   third size, as a hand across the table is drawn smaller in a card game.
2. **The four corners, the same on every card**: **top left the rune** (which goal); **top right the kind** (what card:
   a goal's feature, bug, tidy, screen; a decision's question, fork, failure, hypothesis, cost grown; a task's; done);
   **bottom left who** (whose work: the leaders at work, the seat doing a task, who asks); **bottom right how much**, one
   figure by the card's state (its cost before it is agreed, its time left at work, the time it took when done,
   *asks you* while it waits for you). Between them the title and what the place has room for. The signal colours (the
   alert: it waits for you; the danger: it failed) are in the kind's corner and the frame only. A corner's sign and head
   keep their size on every card (a sign 14 px, a head 16), so they read as an index. **A new goal's card** is the same
   card with its corners empty and dashed, each saying what will stand there, filled as the goal is made (the kind when
   it is picked, who when it is routed, how much when it is estimated, the rune when it is laid).
3. **A card stands while it plays and lies face down while it waits** (this changes §206.3 and §206.11): at work, in
   the hand and opened it stands face up; while it waits it is face down. **In analysis** is **the Orkmaster's hand**: its
   cards 56 × 78, standing, face down, held back to the person in a **near-straight fan** (1.5° apart), as a player's hand
   is seen across the table; spread while they are few (usually one to three, 44 px apart) and tighter as they grow,
   never a count; each back has **its rune in its middle**, as a big back's seal has it; the goal being read is **lifted
   out of the fan** and named under the pile's title (§206.3); a press on the fan reads it out in order, as today. **A
   goal laid** from its card turns face down, its rune lights in the middle of its back, and it flies, growing small,
   into the Orkmaster's hand, where it lies at the fan's end: one motion, none under reduced motion.
   **To review** (its spec made, waiting to start) lies on its side, face down, with no corners: its seal is the rune and
   its ring says what it waits for. It is a **squared deck that deals itself onto the table**:
   each back's ring fills in eighths as its start comes (orkUI's `.is-waiting`), a goal that waits for you has a still
   yellow ring and a yellow edge, and **the next to start is named under its title with its time**, so it can be held
   before it starts. A back pressed opens its goal's spec. *At work · later* stands, its cards 144 × 202.
4. **The Orkmaster's column is 160 px and never scrolls on the desktop.** A back is 157 × 112 with **13 px** under the
   window's left edge (§236.1), so the deck and *At work* keep one right edge, 144. The Orkmaster's fan (about 90 px)
   and the deck (112 px) keep their height whatever they hold, so only *At work* gives way to a short window, in three
   steps: its cards behind the front show
   their **foot** (26 px: who, how much); then a **thin edge** (3 px), the furthest first; then **the pile sinks under
   the hand's rim**, as the hand's cards go under the window's edge, the rim falling between two lines of the front card,
   the cards behind a sliver at its right. Nothing counts what waits. A card hovered or focused slides out whole.
   Scrolling on the desktop is the table's and an opened card's only; the phone's crown's piles are a screen of their
   own and may scroll.
5. **The hand's card is cut under its title** (this changes §249.2): 144 × 202, the hand's rim at **100 px** shows the
   rune, the kind and the title in three lines. **Who asks is the lane** the card lies under (a party's stacks under its
   lane, the Orkmaster's under the column), so the card's face does not repeat it; a choice is made only on the lifted
   card, so **the cost is shown there**, at the moment of choosing, and a cost that grew is a card of its own kind. Below
   the cut: why it is asked (up to three lines), who asks, how much; hovered, the card rises and shows them. Where the
   die or the potions make the hand taller, the cards keep their top and show more, the cut kept between two lines. On
   the narrow page and the phone the hand has no lanes: **it is laid by leader, a small head before each leader's cards**;
   its card 80 × 112 is cut at 62.
6. **The opened card never grows**: 404 × 566, its corners the hand card's, larger; its body scrolls inside; the answer
   and the buttons stay above its foot; its bottom right is the cost of the way picked and changes as one is picked. On
   the phone it is 5 : 7 at the screen's width; while the keyboard is up it keeps its top corners and title and is as
   tall as the screen leaves.
7. **A goal's start turns its card up and the Orkmaster deals it** (this extends §70.1 to a start by itself): the back
   leaves *To review*, turns face up and stands in *At work*; from it the goal's card is dealt to the lane of each party
   doing it (the heads in its bottom left), one motion, and each leader lays its tasks under it there (§70's deal, §167's
   cascade). The Orkmaster says what and who, a leader how: the Orkmaster never deals tasks. §70.2's limits hold: one
   motion that travels, six steps at most, none under reduced motion, a hidden page or into a lane under the pointer;
   several starts at once deal the first and lay the rest. What lands in a lane is the goal's strip as today (§167), the
   dealt card folding into it.
7a. **What the front card of *To review* carried moves** (this changes §241): a back has no room for the heads in its
   ring's middle, *Start now*, the ring filled as the spec is written, *Held* or *Asked Tech*. *Start now* and *Change…*
   stay on the pile's list; a goal held has a pause sign on its back and says so in its name; *Asked <leader>* is the
   pile's line for the first goal asked; the ring is the wait. The lines under the piles' titles are one line, whole on
   hover, so *At work* keeps its rune row in a 1366 × 768 window.
8. **A goal that asks you is dealt from the deck to your hand**: its back lifts, turns up and stands, and lies in the hand
   under the lane of the leader who asks.
9. **Unchanged**: the lanes' windows onto the work (§249.3) between their corners; §236's tuck under the window's edge
   (now 13 px); the + card; Play, the die and the potions.
10. **The words** (`TERMS`): *reading: <goal>* under *In analysis* (as today); *next in <time>: <goal>* under *To review*; a new goal's empty corners *the rune: given when
   it is laid*, *who: the Orkmaster routes it*, *how much: after its estimate*.
11. **Built** by spec 147. The mockup is the look: `docs/mockups/card-ratio/`.
The owner's call.

## 252. Every face-up card has a window between its corners, never empty: a picture when the goal has one, its words when not; a new goal's card shows what is attached to it (5 November 2026, the owner)

Changes: 249.1, 249.2, 249.4, 251.2, 251.5, 251.6; spec 142 A, B, spec 147 B.4, C.1, D.

Why: the owner: *unify the pictures in the cards (today only the table's cards have them); show the attached files'
previews when a card is made, and maybe even force the text, on a card in the hand or at work, into the same picture*.
§249 took the windows off the column and the hand because they were empty or held a sign; §251 gave every card its
four corners and left its middle to each place. A card game's card keeps its picture in one place on every card; a
window that always holds the card's own content, a picture or else its words, is never empty. The one look (CLAUDE.md)
allows no picture for its own sake: a window shows only what the person attached or the work made. So:
1. **Every face-up card's middle is its window**, inside one frame (the lanes' window of §249.3), between the corner rows
   and under the title: the column's *At work* card, the hand's card, a lane's card, the discard's card, the opened card
   and a new goal's card. A back has none (it hides what it holds).
2. **What a window shows, in this order**: what the work made last (§249.3's `made`: Design's screen, Art's asset, Play's
   shot); else **the goal's first picture** (the pictures attached when it was made, `realm/idea_photos.py`); else **its
   words**: the hand's card why it is asked, *At work* what it does now, a lane's card its steps or its failure (§249.3),
   the discard what it made, an opened card its question, a new goal what it should do. Words in a window are text in
   the reading face, never the pixel face and never drawn into an image: selectable, read out, found by a search.
3. **A window never makes its card taller**: it takes the middle the place already gives (the hand's below its cut, so
   the hand keeps its height; *At work*'s where *now* was; the lanes' as today; the opened card's at the top of its
   body, larger). A picture is shown whole inside it (`object-fit: contain` on the table's ground; pixel art at a whole
   scale, §249.3), served by the host at about twice the window's size, never the file itself.
4. **A new goal's card shows what is attached** in its window as the person attaches it: the pictures as thumbnails, the
   files as chips, the window the place a picture or a file is dropped on; with nothing attached, its hint. Laid, the
   goal keeps its first picture, which its cards show from then on.
5. **A fork in the hand** shows its sides' pictures side by side when both have one; a failure its reason's line; an
   asset its asset.
6. **Built** by spec 148, after spec 147's B and C.
The owner's call.

## 253. What the person chose steers the route, a task's gate has a budget and says when it ran out, a red from before is not the task's, one way to main with its checks in it, and Done is said against what was promised (5 November 2026, the owner)

Changes: 187.3 (the rune with no party addressed), 250.3 (how many browser tests a task's gate takes), 250.7 (what counts as ready for main), 250.9 (how long a gate may take: decided here); spec 128 G, spec 143 B.1, F.3, F.4.

Why: the owner: *let's pull the latest and take a simple goal of the repository from idea to implementation in Orkboard on local
Codex; you watch the run and its errors, a picture at each stage, then read the logs: how right the flow was and how right it is
set*, and *from the result make a decision and a spec and push them to main*. The goal was the fourth of
`docs/trials/143-four-goals-for-the-trial-again.md` (the field's Rune square, spec 128 G's *Not built*), pressed through the page on
a clone with no remote, a HOME of its own with only the Codex sign-in, a Tech party at Lean. It reached main: 13 calls, 3.30
million tokens (88% read from the cache), 15.6 minutes of the model, 14% of Codex's 5 hours and 2% of its week. No refused command,
no error toast, no console error, no Board page touched: §250.1, §250.2, §250.6 and §250.7's words held, and the section and the
plan were the best part of the run. What did not hold is below; spec 149 §0 has the run call by call. So:
1. **What the person chose steers the route.** The line's words guessed *bug* from *not a fixed one*. The person dropped the goal and
   sent it again, **To Tech, New feature**, and the route kept the guess, since `route_plan` passes the text alone: the card said *a
   small change*, the host ran a bug's diagnosis and asked about *The cause*, with no Talk and no decision. A type chosen is the
   route's kind; *fixed* no longer says a bug; the card says what the host will do; a goal routed as a bug with no failure in its
   report can be told **It is no bug** on its card, where today the only act is to drop it.
2. **A project is read by what lies at its root.** A fresh clone of Orkboard was asked *orkBoard is a game, Skyhop.uproject is here*,
   because of `tests/fixtures/engines/unreal/` (spec 145 C). A sign of a kind counts at the root, never in a fixture.
3. **A task's gate has a budget** (what §250.9 left open). `tests/test_{leaf}*_browser.py` took 56 modules for one line of a helper
   nothing reads in `pwa/`: 569 tests green in 16 minutes 13 seconds at six workers, 99 minutes of CPU, where the gate runs them one by
   one with 15 minutes. **No change to a file of the phone could ever pass.** A task's gate takes a pattern's modules only up to
   `[gate] browser_max`, else those of the file's own name; runs them in parallel; says what it left. What it left runs at the
   portal's check on the way to main, with a limit of its own.
4. **A gate that did not finish says so and keeps the work.** The card said *no answer within 900 s*; the log showed the session
   answering and nothing after it; no `gate_ran`, no output. *Start again*, the only act, reset the branch, threw the green commit away
   and paid 326,936 tokens for the same line. It is a gate that could not run (§250.4): *The tests did not finish in 15 minutes*, its
   output and its event kept, and **Test again** with no session called.
5. **A red from before is not the task's.** A gate was red on four tests of another goal's file: two red on clean `main` on a Mac
   (`Control+a`), two that pass alone. The session sent back spent 588,106 tokens, the dearest call of the run. Before a red gate calls
   a session, the red tests run again alone and then on the base; *flaky* and *red before this task* are said, spend no try and hold
   nothing. A session is told only what is left.
6. **A session is told what its sandbox allows.** Codex's `workspace-write` cannot write git's index or start a browser. Five of the six
   task calls hit `index.lock`, two went through `/Applications` after Chrome, and the check wrote both as findings, which took a press.
   §250.1's *what is settled goes in the commit's message* cannot work there: every commit said its title alone. The prompt says what
   the sandbox allows, a task may leave `.ork-commit.md` for the message, and a commit is authored by the running product's name.
7. **One way to main, its checks in it.** The discard's **To main** is `ideas.gate_merge`: dev whole, no test run, in 3 seconds; the portal
   runs its checks. The button takes the portal's way. `gate_merge` stays for commits of no goal and Release's map, and is refused
   while a goal with work in dev is not ready: nothing reaches main half made by a press that does not say so.
8. **Ready for main says what is so** (§250.7). The pile said *3 commits ready for main* with a goal at 2 of 4 and a task failed, and its
   page *commits that belong to no goal*; they were that goal's. After main, the fold's Board commit said *1 commit ready for main* again,
   as it will after every goal. The commits of a goal not ready are not counted, nor the Board's own, the living specs too.
9. **Done is said against what was promised, and the spend in what is known.** The result said *This goal so far: —* and four titles. It
   has the goal's **Done when** lines over what each task made (its files, lines and tests), read with no model, for the person to read
   side by side. With no price it says the tokens and the share of the tool's window. A Codex party's *$0.28–0.83 at API prices* came
   from Claude's table: a tool with no price known says its calls, with no dollars. `drive spend` calls work done twice what it is.
10. **A Done when is met where the person starts.** **To the Orkmaster**, what the field opens with, the square stayed the fixed dim rune
    the goal set out to change; only with a party addressed does it wear the host's hue. All tests were green and the review found no
    blocker, since neither looked at that state, and this project has no Play for the person to look. The rune is shown with no party
    addressed, since it is the project's (changes §187.3), and a section's *Done when* about a screen names the state it opens in.
    The trial's code is carried by the patch `docs/trials/149-the-rune-square.patch`.
11. **Small words.** A cause is cut at a word and whole in *Why* (*the host's per-shape hu*). A goal's thesis keeps a path's underscore
    (*realm/ideaelement.py*). A question with no choices does not say *Pick an answer*. A drive is told where a task at Review is read; `drive shot` runs
    on Python's Playwright. After `uv sync`, `playwright install chromium`: with none, every browser module skips.
12. **How this repository is set.** `orkcraft.toml` gets `browser_max`. What was set right and stays: Codex found and tested at the first
    open, a Lean party, a task on its own worktree and `.venv`'s Python, Release reading only when something is ready.
13. **Not decided here**, left to the owner: a party taken under *To* starts picking at once and slides the field and its words off the
    screen until *Stop picking*; at Lean a review cost 556,105 tokens, more than any task's first run, to say *no blockers*: whether a
    small goal at Lean plans a check; what Play runs for this repository; §250.9's *Start again* with a line and the `laborer` tier (every
    task here ran `warrior`); `OPENAI_PRICES`, still empty (§250.8).
14. **Built** by spec 149, then the trial again.
On the owner's word, from what the run showed.

## 254. What a tab shows is its table; only the table scrolls and a card's words are written to fit it; the table's edge: the portal with the imp at twelve and the lich at six, the discard, the die and the potions; one back for every card face down; a decision that conflicts with an earlier one is a card the Orkmaster throws, the earlier one drawn out of the portal; the first open as four cards the Orkmaster throws; the new goal's card with corners to pick and Now or Later; the Orkmaster's column goes under a card laid over it (5 November 2026, the owner)

Changes: 104.2, 120, 145.1, 145.4, 159, 167.7, 188.1, 188.2, 232.1, 232.3, 232.4, 238.2, 238.3, 246.1, 247.1, 251.2; spec 95 §1.1, §2.3,
§3, §4.1, §4.3, §7.

Why: the owner, as a designer and a product manager, nine points, talked through and answered the same day. *Lens* and *map* are
two words for one thing, and neither is the frame's: what a tab shows lies on the table (§145.1), the tabs are its far side, the
leaders sit at it (§201), so a tab opened is the table as its leader lays it. Long words on a card are read the less the longer
they are, and a card cut in the middle of a thought says nothing (§247.4). The portal's ring and the discard take the table's
right side, and §247.1 hid them while empty to win that width back; laid beside the table instead, they can stay, and they make
one road: done goals in the discard, sent up into the portal where the lich takes them in at six, out at twelve where the imp
keeps what is live. The back's pixel lattice (`backs/back.svg`) reads as a texture at 157 × 112 and as noise at 56 × 78 in the
Orkmaster's fan, so the backs look different wherever they lie. A conflict with an earlier decision is seen by the decision's
call (§233.3) but only said inside the decision's text, where it is missed. The first open (§232) asks the right things but lays
the whole frame at once; each card thrown where its thing will live teaches the place, not a text. The new goal's card already has
its four corners (§251.2), but nothing in them can be chosen, and a kind or a party can only be given by typing (*@Tech*). The
Orkmaster's column is cut at the edge of a card opened over it, where a card on a table would only cover it. The owner's answers:
the chronicle stays over the pane, so the table under it stays in use, and then, better, the past is the lich's, opened through the open tab and laid by version, its way in a pyramid of the craft's last decisions in the portal, the depth the age; the back plain, after a tarot back: the ring of runes, a plain strip on each side, the corners' curls; the die turns a quarter; GitHub at the first open later;
*Now* still meets the route card when it costs more than agreed. So:
1. **What a tab shows is its table**: *Tech's table*, *the Orkmaster's table*; never *map*, *lens* or *view* in what a person
   reads (Tech's *System* is Tech's table). The frame is unchanged: the table and the hand (§145.1); the open tab says whose
   table it is. `TERMS`: `map` says *table*, with *map*, *lens* and *view* in its `was`; code keeps `map`, `lens_view` and
   `project_map` (CLAUDE.md).
2. **Only the table scrolls on the desktop** (§251.4, made strict): it scrolls as one, its lanes together, the tabs and the hand
   held; never sideways; every other scroll found is a bug, but an opened card's body. **A card's words are written to fit**:
   every call that names or words a card (the route, a leader's question, a task, a result) is given the budget in its rules,
   **a title up to seven words, a window's words up to three lines**, a lifted card one sentence (§247.6); the page clamps
   as a net only, with an ellipsis, and the whole words are on the lifted card.
3. **The table's edge**: the portal and the discard leave the table. At the right of the table and the hand, one strip of
   objects, top to bottom: **the portal's ring**, Live's head (the imp) on it at **twelve**, Release's (the lich) at **six**
   (this changes §188.1–2: the heads on the ring, not at its corners); **the discard**; **the die**; **the potions**, at the
   hand's level. It is not a column: no list, no count, no words but each object's own (CLAUDE.md's frame holds). The ring is
   drawn from Start always, faint and still while nothing is ready for main, its heads asleep (this changes §247.1); the
   discard's place is drawn from its first goal done (§247.1 kept). **To main** flies the discard's cards up into the ring,
   where they go in at the lich. The imp pressed opens Live's table, the lich Release's (with *Earlier* of §238.2). The table
   gains the width the ring and the discard took. The narrow page and the phone keep theirs until a decision of their own.
4. **The die turns a quarter** (§246.1, its faces made plain): the up face Play, unchanged; **Stop all on the front face**,
   **Resume on its right face** from the start, muted and seen at the side. *Stop all* pressed, the cube turns a quarter about
   its up axis (orkUI's `.is-turning`) and Resume is the front; *Resume* pressed, it turns back. **The face seen is what a press
   does**; the words under the die say the state (*Play · Stop all*, *Play · Stopped*). The Play mark stands upright after a turn.
   The die lies under the discard and over the potions. §246.2–3 hold: the Board turns it, never the person.
5. **One back for every card face down**: the Orkmaster's fan, *To review*'s deck, a stack's cards behind its front, the
   discard's under its top, the first open's four. After the owner's tarot back, kept plain (the owner's pick of three drawn,
   *C*): **orkUI's ring of runes in its middle** with the goal's rune in it (§251.3's seal), **a thin plain strip along each of
   its four sides**, no diamond on any, and **a small curl in each corner**, two strokes. No colour but the rune; no moon (orkUI's
   sign for *waits for the reset*, §160.3, is never an ornament), no stars. At 56 × 78 the ring and the four strips only, the
   curls left out; lying (*To review*) it is the same back turned, the same on every side. Made in orkUI (`backs/back.svg`
   redrawn, the lattice gone), then copied.
6. **A conflict is a card the Orkmaster throws.** When the decision's call (§233.3) finds that the goal's decision goes against
   a standing decision, the Orkmaster throws **a card of the kind *conflict*** into the hand under the first lane, **before
   Confirm and start**, so nothing of the spec is paid. Its kind a sign of its own (orkUI: two cards crossed); its window the
   point in conflict in one line. **Lifted, the earlier decision comes out of the portal**, from the lich, and lies beside it over
   the pane, both with their why, as a fork's two sides (§252.5). Its choices: **The new one replaces §N** (the decision says it
   changes §N, and its slices replace §N's, §233.2), **Keep §N** (the goal is talked again within §N), *Other…*. The conflict
   ends with the card; nothing is decided without the person's press.
7. **The past through whose eyes: the lich holds it, the open tab says whose** (this changes §238.2–3: no line *Earlier* in a
   lens, no chronicle of its own over the pane). The chronicle is read on the frame's two axes (§1.3 of spec 95: what is looked
   at · through whom): **the lich pressed at the portal opens the past through the open tab**, over the pane: on a party's tab
   that craft's past (its decisions, a decision being a craft's when its leader keeps a slice of it, §233.1, and the goals it
   worked on), on the Orkmaster's tab the whole project's. **The line under the lich says whose past it holds** (*Design's past
   ›*, *The project's past ›*) and changes with the tab. Over the pane the only choice is **a deck a version** at its left,
   *Unreleased* on top (a week's deck for a project with no version yet, §238.5): none picked, every version, newest first, each
   card's version in its bottom right; one picked, that version's cards. **A search** over the top dims the decks with no find
   and lights the cards found. Its title says both axes (*The past · through Design · v0.3*); **←** goes back to the tab's
   table. **The way in is a pyramid in the portal** (the owner's pick of three drawn: a fan at the lich, a stack in the
   portal's eye, a pyramid): the last three decisions of the open tab's craft (the project's on the Orkmaster's tab) stand in
   the ring as small cards (56 × 78, face up: the rune, the kind's sign, the number, who) **stepping back into the swirl, each
   older one smaller and darker, so the depth is the age**. A new one since that craft's past was last looked at comes out to
   the front, its edge in the ink until seen, the others step one deeper and the oldest sinks: one motion, none under reduced
   motion, else the pyramid lies still (§247.8). A step hovered or focused rises whole under the ring (its title, its why in a
   line, its version); a step or the lich pressed opens the past. **While something is ready for main the pyramid sinks into
   the portal** and the ring is the gate's alone. A card lifted is §238.4's row: a goal as it was, a decision with its *Changes* and *changed by*; **Show on <party>'s
   table** opens that tab with what it touched lit. **The ring itself** stays the way into main, pressed only while something is
   ready; the imp is Live. The conflict's earlier decision (6) comes from the lich; *Open in the past* opens this, through the
   tab of the craft it is about, its deck dealt and the card lit.
8. **The first open is four cards the Orkmaster throws** (this changes how §232.1, §232.3 and §232.4 are shown, not what they
   ask): no project open and nothing set, **the room is dark**, no table and no hand; **the Orkmaster in its middle**, its bubble
   *I'm the Orkmaster. Four cards, and we start.*, holding **four backs** (5). Each card thrown flies to its place, and the place
   appears as it lands:
   1. **To the potions' place: the AI tools.** §232.4's card lifted there; the tools found ready are offered first, one press
      (*Use Claude Code*); its form only when none is ready. The first potion fills as the tool is added.
   2. **To the portal: the project.** The ring appears; §232.3's card: a local folder (*Open a folder…*, *A new, empty
      folder…*, the recent ones), git if it has none, and **its release branch**, the branch the portal sends into (*main*,
      read from git, changed by a press). GitHub's sign-in and a remote project: later (12).
   3. **The table appears: its kind and its parties on it.** *<name> is <kind>, <how>. Right?* (§232.3); then the kind's
      parties as **empty chairs at the table's far side**; a chair pressed seats its leader, its size and its seats under its
      head as §232's line; *Start* lays the table in §232.1's order. The Orkmaster's large card of §232 is not drawn.
   4. **The hand appears: the first goal.** The + card comes, and its card opens (9) with **its corners lit one at a time as
      each fills**, each saying what stands there (§251.10's words). No tour and no coach mark: the goal sent is the person's
      first real goal.
   A card whose thing is already set is not thrown (a tool set by Orkline, a project open), and the Orkmaster holds only the cards
   left; a project with parties of its own is laid at once (§232.1). Under reduced motion nothing flies: each place appears.
9. **The new goal's card has corners to pick** (404 × 566, §251.1–2; this changes spec 95 §4.1's *no kind*): **top left the
   rune** (the next one given, another picked, §187.3); **top right the kind** (feature, bug, tidy, screen…; by default *the
   Orkmaster reads it*; a bug takes the short way, §118.2); **bottom left who** (by default the Orkmaster's head: it routes; a
   leader picked addresses the goal, as *@Tech* or the open tab do); **bottom right Now and Later**, in place of how much:
   **Now** (Enter) sends it and Talk starts as soon as it is routed, when it fits the limits and costs no more than agreed, else
   the route card asks with its cost as today (§147.4, the money rule); **Later** lays it in line to start itself at the Board's
   hour (§247.2's word). A corner pressed opens its few choices on the card itself, no dialog; a corner left to its default is
   dashed and says its default, a corner picked is drawn whole.
10. **The Orkmaster's column goes under a card laid over it**: the new goal's card, an opened card and the chronicle cover the
    column where they lie, with their shadow; the column is never cut at a card's edge (§251: a place hides part of a card only
    where something covers it).
11. **The words** (`TERMS`): *table* (a tab's: *Tech's table*; *map*, *lens*, *view* in `was`); *Now*, *Later*; the conflict's
    kind *conflict*, its line *Goes against §N*, its choices *The new one replaces §N*, *Keep §N*; the first open's *I'm the
    Orkmaster. Four cards, and we start.*, *Use <tool>*, *Release branch*.
12a. **Not on the table's edge**: a craft's past is the lich's, opened through that craft's tab (7), never a pile at the edge;
    the edge holds four objects with one job each, and a pile of the past would stand there all day beside the discard (§238).
12b. **Release's view at the wide width is the past and the discard** (the owner, 6 November, on what the build found: the lich
    opens the past, so nothing opened Release's view of *dev against main* there): it is not opened at the wide width any more.
    What it showed lies where it belongs: what dev holds and main lacks is the discard's *Ready for main* (§145.4), what main
    holds and no version has yet is the past's deck *Unreleased* (§238.2), and the checks on the way are the gate's skeletons in
    front of the portal (§188.3). The narrow page keeps Release's tab as today.
12c. **Start git here names the first branch `main`** (the owner: *the more popular one*), whatever git's own default is
    (`git init -b main`, or `init` and `symbolic-ref` before git 2.28), so a project started from the first open's card shows
    *main* as its release branch.
12. **Not now**: at the first open's second card, **signing in with GitHub and picking a remote project with its default
    branch** (the remote is §243–244's; a decision of its own when it is built); the edge on the narrow page and the phone; a
    conflict found after Confirm (a finding, §234, as today).
13. **Built** by spec 150, in order: **A.** 10 (a fix); **B.** 5 (orkUI, then copied); **C.** 1 and 2 (the words, the budget in
    the calls, the scrolls); **D.** 3 and 4 (the edge, the die); **E.** 6 and 7 (the conflict, the past through the open tab);
    **F.** 9; **G.** 8 last, since it shows the rest. **Drawn first**, `docs/mockups/table-edge/`; the owner's pick.
The owner's call.

## 255. Any AI tool works the Board from the repository: its pages, each goal's phase and the journals on the work branch, the rules for agents in AGENTS.md and CLAUDE.md, Orkboard the best of the Board's readers; a tool leads the orks' work itself and stops at the person's decisions; a public repository's Board only on the person's yes; Orkboard's own repository first, its own documentation its Board (6 November 2026, the owner)

Changes: 244.1, 244.11, 244.12; spec 35 §13 (a public repository, a task's spec); spec 137 A.2 (the pages); spec 127 D (the journals' Markdown).

Why: the owner: *all of Orkboard's documentation and entities must be in the remote repository: I open the repository in any
harness and it works more or less as through the Orkboard app, only without its interface. Every repository on Orkboard has a
CLAUDE.md and rules for other agents, how to behave with Orkboard's entities.* Then, asked three things: *the code's branch: for a
private repository this is no problem at all, for a public one it is rather documentation and a vision of where the project
goes*; *it leads everything itself*; *published on an explicit yes*; and, asked again, yes: a tool leads the work itself and
stops at the person's decisions. Read in the code: half of it is there. The Board's pages (the parties, the goals and their
sections) are committed to the work branch at every change (spec 35 §13), and the page is the truth: a hand edit is read as it
is (`realm/ideas.py`); the questions of a goal are lines of its page's *Open questions*, read back (`realm/idea_questions.py`);
the decisions are the project's log or its ADR folder (spec 126 D); the gate is `orkcraft.toml`'s `[gate]`, readable by anyone.
What is not: a goal's phase, its route and its Hold are in `.orkcraft/ideas/<slug>/state.json`, never committed, or on
`orkboard/board` (§244), a branch that a tool opening the default branch never sees (a cloud session clones one branch: the
session this was decided in, a cloud container with the repository and no Orkboard, saw no Board at all); the journals and the
project's brief are in `<state_dir>`; and the rules (how the Orkmaster routes, what a leader says in Talk and writes in its
sections, what the hand asks, when a goal is done) are prompts in Python (`realm/goal_route.py`, `core/idea_talk.py`,
`core/idea_sections.py`, `realm/library.py`), never in the project. The tools that do this as files (Spec Kit, Kiro, OpenSpec,
BMAD) are files and rules in the repository: Orkboard reads each of them (spec 126), and none can read Orkboard's. Found on the
way: in a public repository the pages already go out with the work branch when the person pushes it (spec 35 §13), and nobody
was asked. So:
1. **The Board is files and rules in the repository; Orkboard is the best of its readers.** Any AI tool that opens the project
   (Claude Code, Codex, Cursor, Copilot, Gemini CLI, a cloud session of any of them) reads the Board and works it by its rules,
   with nothing installed. What only Orkboard gives stays Orkboard's, and is why it is installed: the table and the hand, the
   phone, the mana across the tools, orks in parallel, Talk in several voices, the Board's resets and hours.
2. **Two layers.** **The Board in the code**, on the work branch (spec 35 §13), all text: the parties' and the goals' pages
   with each goal's phase (3), the decisions (the project's log or ADR folder), the journals and the project's brief (4), the
   rules and the roles (5, 6). It goes with the code: a goal's spec and its work are one pull request. **The Board's working
   state**, Orkboard's alone: the lease, `talk.jsonl`, `route.json`, `pick.json`, `lens.json`, a plan's tasks, the mana, the
   inbox, on the Board's branch (§244) or the machine; a tool outside Orkboard never writes it. The goals' photos stay out of
   the code (on the Board's branch or the machine; the page names them): at up to 2 MB each they would weigh on every clone
   for ever. The Board's branch keeps the working state and the pages of the goals kept off the repository (10); the other
   pages leave it (this changes §244.1 and spec 137 A.2: two copies of one page are two truths).
3. **A goal's phase is in its page.** Its front matter gains `phase`: `new` (as the person wrote it), `talk` (routed: its
   leaders' say), `spec` (its sections written), `work` (its stages done in a branch), `done` (its gate green, its pull request
   open or merged); and `route` (its parties in order), `queue` (`hold`, `night` or none, as `state.json` keeps §247's *Hold*
   and *Later*), `asks` (`person` while a question waits for them), `gate` (the last gate's commit, what ran, how it ended),
   `by` (who laid it: `person`, or the tool) and `schema`. The page is the truth; `state.json` keeps what runs (the keeper's
   session, Talk's round, the finer state Orkboard moves through) and follows the page: a phase moved outside Orkboard moves its
   state to that phase's first, said in a line (*<goal> was moved to <phase> in <tool>*). The code's own keys keep their names
   (`track`, `order`). Orkline's frozen copy keeps every key it does not know, so it reads the same Board safely; it gains
   the phase when it depends on the `orkboard` package (spec 37 §9).
4. **The journals and the brief in the code**: each journal's Markdown (spec 127 D) is written into the Board's folder as
   Orkboard's export writes it (spec 126 C), and read back as an export is (spec 126 B: by its refs, never twice), so a tool
   outside Orkboard adds a line in that format and Orkboard takes it in; the project's brief beside them (the memory bank's
   `projectbrief.md` of spec 126 C). The `.jsonl` stays Orkboard's.
5. **The rules for agents.** Orkboard's block in `AGENTS.md` at the root, between its markers, at most 60 lines: what the
   Board is and where it lies, the way of a goal, what the person decides (7), what never; and a block in `CLAUDE.md` holding
   `@AGENTS.md` (Claude Code reads CLAUDE.md). The details are the Board folder's `BOARD.md` (the page's format, the phases, a
   question's line and its answer's, the gate's record, taking a goal), and the folder's own `AGENTS.md` and `CLAUDE.md` point
   to it, so a tool loads it where it works. The person's own words in these files are never touched, and **the project's own
   rules win over the block**: where they conflict, a tool asks. Written on the person's yes (Settings, or `orkboard init`
   in the project) and committed as the Board's pages are; written again when Orkboard's rules change (12).
6. **The roles in the project.** Each seat's instruction that Orkboard gives a model (the Orkmaster's route, each craft's
   leader: its say in Talk, its sections, its *no* and where it hurts as spec 108 has it; the Taskmaster; a Grunt) is a file of
   the Board's folder, `roles/<id>.md`, **written from the same code the prompt is built from**, never by hand; a test holds the
   file and the prompt to one text. From them, for the tools that take them: Claude Code's subagents
   (`.claude/agents/ork-<id>.md`) and a skill (`.claude/skills/orkboard/SKILL.md`). What a prompt reads of the project (the brief,
   the journals, the earlier decisions) the file names where to read. The prompts are so in the open: Apache-2.0 (§96) allows
   it, and what is Orkboard's is its table and its orkestration.
7. **A tool leads the orks' work itself, all of it, and stops at the person's decisions.** It takes a goal (8), routes it as
   the Orkmaster does, holds Talk with each leader of the route in a pass of its own (only that leader's role file and the
   page: one voice playing every leader agrees with itself), writes the spec, does the stages in a branch of its own, runs the
   gate and opens the pull request, each step written to the page and its phase moved. **What the hand would ask is the
   person's**: a question no leader can settle, a choice between ways, a cost above what was agreed (§147.4's money rule), a
   decision that goes against an earlier one (§254.6), dropping a goal or putting it on Hold, going into main, and a goal the
   tool thought of itself (laid with *Take this goal?*). The tool writes it as a question's line under *Open questions*
   (`idea_questions.line`), sets `asks: person`, says it in its chat and ends its turn; the person's answer is written under
   that line by whoever hears it. Orkboard and the phone show it as a card of the hand and write an answer given there the same
   way. Where no person watches (a scheduled job, a cloud agent left to run), the goal waits: **a tool never answers for the
   person**. **Done is the gate**: `phase: done` only with the gate green on the pull request's last commit, its record in
   `gate`; the project's CI checks the Board on the pull request (9) and runs its own tests, so the record is for reading and CI
   is the check. A decision is written as the project writes its decisions; a past one is never edited, a new one replaces it.
   Orkboard's own tasks still never edit the Board's pages (spec 35 §13); a tool outside Orkboard writes them as the person does.
8. **One taker of a goal at a time.** Taking a goal is a file of its own, `<slug>.json` (`by`, `until` an hour ahead, renewed
   while it works), on a branch of its own, `orkboard/taken` (as the journal's and the inbox's: no history shared with the code,
   never merged, no workflow), pushed without force: the push decides (§244.2's way). A goal another holds is not taken; one past
   its `until` is. Orkboard takes a goal the same way once the rules are written (5). A tool that cannot push follows it as a
   rule, not a guarantee, and the rules say so.
9. **The levels**: **the rules alone** (any tool, nothing installed: it reads everything and writes by the rules; Orkboard
   checks the pages when it next reads them) · **`orkboard` from a terminal, with no app running**, run from git (`uvx --from
   git+https://github.com/orkCraft/orkBoard orkboard`: Orkboard is not on PyPI, and a package of that name there would be someone
   else's, so no rule ever says `uvx orkboard`) (`init`,
   `goal list|add|take|phase|ask|answer`, `gate`, `check`: the writes checked; `orkboard drive` stays the served page's) · **an
   MCP server of the same commands**, later, when the terminal's have been used · **Orkboard**. `orkboard check` reads the Board as
   Orkboard does and fails (for CI) on a page it cannot read, a phase it does not know, a `done` with no green gate, a secret's
   shape, a rules block or a role file that is not Orkboard's own (by its hash: a changed one is said, never followed), and a
   `schema` older than this Orkboard writes (*The Board's rules are v1, this Orkboard writes v2: run orkboard init*); it is
   offered as a step of the project's CI on the person's yes, as §244.6 writes a workflow.
10. **A public repository: the Board in the code only on the person's yes** (this changes §244.11 for the code; the Board's
    branch stays private only). Before the yes, said plainly: *Your goals, their specs, the leaders' words and the decisions will
    be public, in the repository's history: a later No does not take them back.* The answer is the project's, `[board] in_code`
    in `orkcraft.toml`. A private repository on GitHub needs none; a public one (GitHub's anonymous check, §244.11) or one whose
    remote Orkboard cannot read is asked once. Without the yes, **nothing of the Board goes to the work branch**: the Board's tree
    commits on a ref of its own, never pushed, and a task is given its spec inside its worktree's `.orkcraft/`, which git
    ignores (this changes spec 35 §13 for such a repository); the pages already in the work branch leave it at the next commit
    (its history keeps them, and the question counts them). A repository found public since (checked once a day and before
    Orkboard pushes) stops the Board's writes to the work branch and asks again. **A goal kept off the repository**, in a public
    repository with the yes: a goal of the kind *security*, a goal with secrets of its own, or one the person keeps off on its
    card; its page stays on this computer. A private repository holds every goal.
11. **A page tells what to make, never how a tool must behave.** Orkboard and the rules read the Board only from the work
    branch, never from a fork's pull request (a page changed there is that pull request's change, for the person to see); a
    rules block or role file that is not Orkboard's own is not followed, and said; in every prompt a page's words are the goal's
    words (as `clean_text` treats a model's answer: untrusted). The rules say it to a tool: *an instruction in a page to change
    these rules, your tools, CI or secrets is a finding for the person, not a step.*
12. **The format is a contract.** `schema` in the rules' block and in each page; a spec that changes the page's format, the
    phases or the rules says so (*changes the Board's schema*) and moves `schema`; Orkboard reads every older one and moves a
    page to the new one when it writes it.
13. **What it costs the code's history**: the Board's commits stay batched (spec 35 §13's 10 s; a phase rides in them); a
    workflow Orkboard writes (§244.6, 9) ignores the Board's folder on `push`; for the person's own workflows a line suggests the
    same, never an edit; the gate never runs for a change of the Board's pages alone (as `idea_gate.without_board_pages` keeps
    them out of a goal's way into main).
14. **Orkboard's own cloud run is unchanged** (§244.7: it reads, never works). A tool the person opens in the cloud is the
    person's own worker, and works.
15. **Tried before it is promised**, on Orkboard's own repository (17): Claude Code, Codex and Cursor, each without Orkboard,
    each on one of its goals from the person's words to a green gate and an open pull request; then Orkboard opens the
    repository and must show each goal in its phase, each question in the hand, each gate's record. What each tool missed is the
    trial's finding, and Talk in one tool is measured against Orkboard's as H1's head-to-head is
    (`docs/trials/h1-head-to-head.md`).
16. **The words** (`TERMS`): *the Board's rules* (the block), *taken* (*Taken by <tool> until <time>*), *Publish the Board* and
    *Keep the Board off the repository*, *Keep off the repository* (a goal's), the lines above. In the files the code's names
    stay (`pages/ideas/`, `track`); the rules' glossary says them in today's words (*idea* is a goal, *track* a party).
17. **Orkboard's own repository is the first project of this decision, and its own documentation is its Board.** The owner:
    *the main thing: once it is built, Orkboard's own repository is laid out by the same principle*, its documentation as well
    as the way it works; and, on the three choices, *as recommended*. Once A–F are built:
    - `docs/decisions.md` is the Board's log as it is: its format is the one the Board writes (`doc_formats.parse_log`).
    - **Each spec of `docs/specs/` is a goal**: a thin page (its title, `phase`, `route`, a Gist of one line) whose spec is the
      spec's own file, kept in its long form and never rewritten into the page's sections; **the spec's parts are the goal's
      stages**. The specs up to 149 are laid `done`, and the list is shown to the owner to correct; 150 and 151 take their
      phase and their stages from what their commits say (`Spec <n> <part>:`). This is a shape `read_in` reads (spec 126 B),
      so any project with a folder of numbered specs can be laid the same way. From then on a new spec of this repository is
      written with its goal's page in the same commit.
    - `docs/hypotheses.md` is read as the Board's hypotheses (spec 133), Release's chronicle reads the tags (spec 134; `docs/updates.md` and `updates.json` are no changelog);
      the trials and the mockups stay documents the goals name.
    - The parties: Tech, Design, Product and Release, on the owner's yes.
    - `CLAUDE.md` stays this repository's own rules, which win over the block: the alpha's *merged into main as soon as the
      critical tests pass* over the block's *main is the person's*, which is the case the rule is for; `@AGENTS.md` is added to
      it, and `AGENTS.md` gets the block.
    - If the repository is public, its yes to 10 is the owner's first *Publish the Board*: its documentation goes out as the
      vision the owner named.
    - The README says how Orkboard is worked without the app (the four levels of 9); `BOARD.md` is part of the product's
      documentation.
    Done when a cloud session with nothing of Orkboard installed, in a clone of this repository, takes one of its goals by the
    rules and Orkboard then reads what it did. It is H1's test in the open (`docs/hypotheses.md`: specs handed to any agent).
18. **Built** by spec 151: **A.** the phase in the page; **B.** the journals and the brief in the code; **C.** the rules and the roles; **D.** taking a goal; **E.** `orkboard` from a terminal and `orkboard check`; **F.** a
    public repository and a goal kept off it; **H.** Orkboard's own repository on its Board (17); **G.** the trial, on it, last.
    The MCP server is not this spec.
The owner's call.

## 256. A leader holds its slice and never does the work: a party is its leader and at least one who does; the leader accepts its step against its section, once a step, a base early; its slice one file it keeps; asked once where once is enough; code before agents; a craft's own way of work (6 November 2026, the owner)

Changes: 151.2, 151.6, 157, 253.13; spec 81 §2, spec 99 §1.3, spec 143 A.2. (151.2: the sizes, who checks, *with no checker in
the squad, the leader checks*; 151.6 and 157: Release's squad is its leader; 253.13, answered: a goal at Lean plans no check, its
leader accepts it; spec 81 §2: Lean is one agent, the leader; spec 99 §1.3: the sizes; spec 143 A.2: a Lean leader told it does
the task.)

Why: the owner, as a product manager and an AI architect: *is a leader called three times: at the goal, to judge it; at the spec,
to write its part; and to work the task by its own way? So a leader is a slice of the project (marketing, design and so on) and a
way of working its own tasks?* Read in the code: the spine is so (Talk, its section, its step's plan), with more around it (a sketch
before the spec, the findings and the fold after, and a slice's own calls: concerns, the journal's digest, a quick question, a
question passed on, a change asked), each call a fresh one (spec 35 §0) given the leader's map, facts, journal, slices and living
specs, so the continuity is in those files, not in the leader; its stance in Talk is not read into its section. The work's way is
not the craft's: plan, do and check by the size for every craft, the craft giving only the seats, the tool, the checks' tags and a
sketch's kind. And the sizes do not do what §151.2 says: at Lean `tiers_for` makes every seat Seasoned, the leader too, and
`plan_one` gives every task to the leader (`lean_role`); the check tasks are still planned from the squad's checkers
(`with_check_tasks` reads no size) and given to the leader too, so the leader checks its own work: §253.13's review at Lean,
556,105 tokens to say *no blockers*. At Standard every checker that applies checks, as at Full; with no checker in the squad no
check is planned at all, though the party's map says the leader checks. `goal_team.WAY` and `checkers` are read only by the faces.
Then the owner's six points: 1. *a leader always holds its whole slice: its understanding of the project, its stance and its
doubts*; 2. *we do not run the leaders one after another where their answers can be reused or the asks to one batched*; 3. *a
leader always checks its team's work, and so keeps what it knows of its slice up to date*; 4. *leaders get tools: deterministic
ones, made beforehand or written during the work, and a leader's new job is to find where cheap code can stand in for agents; at
best a leader works a task by calling the tools and checking them*; 5. *a leader never steps down a level and never does the work
itself: it holds its slice; the smallest party is a leader and one who does*; 6. *a leader means its slice's tasks may have a way
of work of their own, not only implement and check*. Asked whether accepting once a step costs more than once a task: less, since
the slice's part of the call (its role, its section, its map) is paid once a step and not once a task (about 11 thousand tokens in
against 26 thousand for a step of four tasks: a reckoning, not a measure; the prompt's cache narrows it only when the tasks end
within its minutes); what once a step costs is time, a fault in a task the others build on found late, so such a base is accepted
early. On the three choices, as recommended: once a step, the checkers kept as specialists over it, the tools in the project's
repository. And with §255 and spec 151 being built, nothing here may conflict with them. So:
1. **A leader holds its slice and never does the work.** It plans its step, accepts it (3) and keeps its slice (4); it is never a
   task's doer nor a task's checker, at any size. **Its seat's tier is its own at every size**: Veteran, Release's Seasoned (§151.6),
   or the model the person set on it; a size no longer lowers it. What each of its calls runs on stays that call's own under the
   Target (`idea_target`), as at every size today; acceptance (3) runs Veteran at every Target. Its words say so: a leader's
   instruction never has it make a thing (*Draw and record nothing yourself unless the party is lean* loses its *unless*).
2. **A party is its leader and at least one who does.** A party with no one who does is not made nor saved (*A party needs one who
   does besides its leader*); a party made before with none keeps its seats (§109.1's way), its tasks going to the project's role
   of their tag, else Grunt, as a tag no seat takes goes today. The size is how the work goes:

   | size | a task's way | at once | who checks |
   |---|---|---|---|
   | **Lean** | plan → do → accept | 1 | no checker: the leader's acceptance is the check |
   | **Standard** | plan → do → check → accept | 2 | the first checker of the squad the task concerns |
   | **Full** | plan → do → check → accept | 3 | every checker of the squad the task concerns |

   With no checker in the squad, no checker checks and the leader's acceptance is the check (*the leader checks* of §151.2 is this
   now, at every size). The doers' tiers by size stay as §151.2 and spec 81 have them; the cost is still said on the size.
   **Release** gets its seats (§157: *until seats are added*; §154.2 named them): the release's engineer and its notes, Novice
   each; its leader plans and accepts; Lean and locked as before.
3. **The leader accepts its step**, once a step, against its own section: its *Done when* and *Will be*, never the code's lines
   (the gate holds the tests, and a checker, where there is one, the specialist's view). It is given its section whole, what code
   read of the promise (§253.9's *Done when* over what each task made, `goal_result`'s *Will be* lines), each task's files, gate
   record and pictures, a checker's findings left, and what it said of the goal in Talk; it may open a few of the files and
   pictures. It answers each *Done when* met or not, and accepts or sends back at most four things, each one more task of the
   step. **Twice at most**: what is still left after the second becomes the goal's findings (spec 132), the step goes on, and the
   person decides on the quality card as for any finding; a call that fails says so as a finding; nothing waits or is skipped
   in silence. The next step is planned, and the goal is done, only after its step is accepted. **A base is accepted early**: a
   task two or more tasks of its step wait for is accepted alone as soon as it lands, and they wait for it. What the leader learned
   goes into its journal (`accepted`, `sent_back`, a line or two learned), which §255.4 puts in the code; so acceptance is how
   the slice is kept up to date (4).
4. **A leader's slice is one file it keeps** (the owner's 1), its **dossier**: its understanding of the project, its stance and
   doubts on each open goal, what its last acceptances taught it; bounded as a digest is (§203), written only by its leader at
   known moments (after Talk, after an acceptance), read into each of its calls, so its Talk, its section, its plan and its
   acceptance are one leader's. It is a file of **the Board in the code** (§255.2, beside the journals of §255.4), so a tool that
   plays the leader in a pass of its own (§255.7) reads it as its role file. Never a kept session (spec 35 §0 stands: a session
   does not cross AI tools, grows dearer with every call and cannot be read). Until it is built, an acceptance writes to the
   leader's journal and its stance in Talk is read into its acceptance.
5. **A leader is asked once where once is enough** (the owner's 2): first what was said is reused (the first step's section and
   plan in one call; its stance, through the dossier, in its section), then the prompt's cache (its role, dossier and map the
   stable head of every call of it), and a batch last, only for small judgments of one kind (the verdicts of the goals in line, the
   findings of a step's tasks): several goals in one call mix them, and one failure holds the rest.
6. **Code before agents** (the owner's 4). A leader's tools are deterministic code that does a part of its craft's work (a
   version raised, notes gathered, an asset exported, a report counted); its new job is to find, in its steps and acceptances,
   the work that comes back alike and to propose a tool for it. A tool is made as any task (by one who does, through the gate and
   Review), lives in the project's repository with the Board (§255: any AI tool runs it too), has its test and a count of its
   use, and one unused for long is proposed for removal. At best a step is tools run and the leader accepting them. The Board's
   own rule already is this (the route by code first, a model only where code finds nothing: spec 99 §4.1; the map read by code).
7. **A craft's own way of work** (the owner's 6): a way is a recipe of steps of a few kinds, given as data and run by one engine:
   *tool*, *do*, *pick*, *look*, *ask the person*, *wait and measure*, *accept*. Plan → do → check → accept is one recipe; a pick,
   a sketch, a bug's diagnosis, an operation (prepare, check, act, learn) and a recurring goal are read as recipes; Marketing's
   (a hypothesis, variants, the person publishes, a wait, a measure, what was learned) and Release's (a freeze, the notes and the
   build by tools, the person submits, a watch) become ones. Each kind of step is one card of the hand at most, so a new recipe
   needs no new face (§104.0, §145).
8. **With §255**: the dossier, the tools and the recipes are files of the Board in the code, so any AI tool works them as Orkboard
   does (§255.1); the acceptance is a step of a goal's way in the rules (*Accept*, after a party's stages, before the next party's;
   for a tool, what is still left goes in its pull request) and a part of each leader's role file, written from the same code as
   its prompt (§255.6); a spec that changes the rules says so and moves `schema` (§255.12); and no part here touches a file of a
   part of spec 151 not yet merged: it waits for it.
9. **The order**, each measured on this repository against the one before it (a goal of §253's kind, spec 149's way): spec 152
   builds 1–3 and the rules' *Accept* (8); then the dossier (4); then reuse and the cache (5); then the recipes (7), *tool* among
   their kinds; then the tools a leader proposes (6), once the steps say what comes back alike. A spec each.
The owner's call.

## 257. A task is a whole session: the plan splits only for a reason, tells a task where to start, and claims every Done when line; a Done when line says how it is proven, and an acceptance may say it cannot see; Orkboard's own task is told the Board's rules are not its own (6 November 2026, the owner)

Changes: 256.3; spec 99 §7.1, spec 152 B, D. (256.3: the acceptance's answers gain *cannot see*; spec 99 §7.1: a section's *Done when*
lines carry their proof; spec 152 B and D: amended by this.)

Why: the owner, after §256: *let's go through the leaders' new flow once more: is there anything that would raise the quality of
the parties' work or lower the tokens?* Read in §253's run (spec 149 §0, one goal on Codex, this repository, Lean, 3,302,029
tokens): the doers' sessions spent 2,777,161 (84%), the leaders' and the Board's calls 513,257 (16%), so what a leader saves is
small beside what a doer spends. Of the doers', a send back for a red from before (588,106), a start again after a gate killed by
its clock (326,936) and the review at Lean (556,105) are gone by spec 149 and spec 152; what is left is three tasks of about 420
thousand each, for a change of four lines in three files and about 250 lines of tests: each session read the same code again. The
plan's rules (`core/idea_plan.py`) bound how many tasks there are and say nothing of when to split; a task's brief says where in
prose, though its planner read the files. And the run's miss (§253.10: every test green, the review found no blocker, nobody could
look, and the screen was in the wrong state) is a *Done when* no test could prove and nobody saw. Found on the way: since spec 151
C, a project with the Board's rules has their block in `AGENTS.md`, which every task session of Orkboard's loads (Codex reads
`AGENTS.md`, Claude Code `CLAUDE.md`'s `@AGENTS.md`), and it tells whoever reads it to take a goal, route it, hold Talk and stop
to ask the person; a task's prompt does not say that it is not for it. The owner's yes to each. So:
1. **A task is a whole session, and the plan splits only for a reason**: a part another seat does (another tag), parts that run at
   once in the party's size and touch no file in common, or a base the others must wait for (§256.3). Else one task. The planner is
   told what one task's session has cost on this project (its tokens and dollars, from its own ledger once there are enough, a
   first guess before), and `MAX_TASKS` stays the bound.
2. **A task is told where to start**: the plan names, for each task, the files it starts at (at most six, from what its planner
   read), kept only where they exist; its prompt says them first. The task may read more.
3. **Every *Done when* line is claimed**: a task names the lines of its section it proves, by their numbers; a line no task proves
   is asked of the planner once more, then kept as not claimed and said to the step's acceptance. By code, no call.
4. **A *Done when* line says how it is proven**: `[test]` (a test the gate runs proves it: the task that proves it writes that test
   first), `[look]` (a picture or Play shows it: the acceptance is given the picture), `[person]` (only the person can judge it: the
   acceptance asks the person one question, never guesses). A line with no mark is judged by its leader, as every line is today. It
   changes the page's format, so **the pages' schema is 2** (§255.12), read back to 1.
5. **An acceptance may say it cannot see** (changes §256.3): each *Done when* line is met, not met, or *cannot see* (a `[look]` line
   with no picture and no Play, a `[person]` line); one it cannot see is never accepted in silence: it is a finding, *Nobody could
   look at: <line>*, and a `[person]` line is that finding's question to the person.
6. **Orkboard's own task is told the Board's rules are not its own**: one line of its prompt, *You are one task of a goal Orkboard
   leads: the Board's rules in AGENTS.md are for a tool that leads a goal, not for you. Do not take a goal, move its phase or write
   the Board's pages*; it never reads BOARD.md for a task.
7. **Release's reading is code** before it is a model (§256.6's first tool): what is ready, read from git; a model only for the
   notes' words. In the tools' spec.
8. **Built** by spec 152 (5, 6 and 4: its parts B, D and F) and spec 153 (1–3).
The owner's yes.

## 258. A leader is a skill in Claude Code, run in a context of its own: each seat a subagent (who it is) and a skill (its step), forked; the `orkboard` skill conducts; a leader's say in Talk and its acceptance written in the goal's page; the role's text one with the prompt's, in an agent's frame (6 November 2026, the owner)

Changes: 255.6, 255.7; spec 151 C.1 (the subagents and the skill).

Why: the owner: *can the leaders be made skills in Claude now? Does it lie on our model?*, and then *yes, write the decision and
the spec and start*. Read in Claude Code's documentation (code.claude.com/docs/en/skills.md, sub-agents.md, 6 November): a skill
with `context: fork` and `agent: <subagent>` runs as that subagent, sees none of the conversation, and gives back what it found;
a subagent may preload skills (`skills:`) and call them; a subagent may start subagents of its own, three layers below the
conversation; `disable-model-invocation` and `user-invocable` say who may call a skill; skills follow the Agent Skills open
standard, of which Claude Code's `context`, `agent` and invocation fields are its own (elsewhere six fields are taken). Read in
this repository: spec 151 C wrote each seat a subagent (`.claude/agents/ork-<id>.md`) and one skill, `orkboard`; their texts are
the prompts' texts *for a call* (*Read no file*, *Answer with one JSON object*, *(The context follows here in the prompt…)*): an
agent in a tool reads nothing by them and answers into nothing; the subagents have every tool; a leader's say in Talk lives in
`talk.jsonl`, Orkboard's working state, so a tool outside Orkboard has nowhere to write it. And in the session that asked it,
Claude Code offered the six `ork-*` subagents and the `orkboard` skill from this repository's files at once. So:
1. **It lies on the model**: a fork is §255.7's *pass of its own* (a leader sees only its role and the page, so one voice does
   not agree with itself), and the layers are the frame's (*the Orkmaster says what and who, a leader how and why, a member
   does and asks only its leader*): the conversation is the person, the hand and the conducting; a leader runs below it; a
   member below its leader, whose work it accepts.
2. **Each seat is two files, written by Orkboard**: the subagent, *who* (its role's text, the tools its step needs, the model
   its tier names), and the skill, *its step* (`context: fork`, `agent: ork-<id>`): the Orkmaster's *route*, a leader's *talk*,
   *section* and *accept* (§256), the Taskmaster's *plan*. A Grunt is a subagent only, in a worktree of its own
   (`isolation: worktree`), started by the conductor for a task and accepted by its leader. A person calls a step too
   (`/tech-leader talk 151`).
3. **The tools a step needs, no more**: a leader, the Orkmaster and the Taskmaster read and write the goal's page and read the
   project (no shell, no web): a page's words cannot make them run a command (§255.11); a Grunt has the tools of the work.
4. **The model its tier names**: the party's tier for the seat, through Orkboard's own table for Claude Code; a seat with none
   inherits the conversation's.
5. **The `orkboard` skill conducts**: it takes the goal, calls the Orkmaster's *route*, the route's leaders' *talk* side by side,
   waits for them all, asks the person what is the person's and stops; then the *sections*, the Taskmaster's *plan*, a Grunt a
   task, its leader's *accept*, the gate, the pull request.
6. **A leader's say in Talk is written in the goal's page**, under its party's section, `### Talk`: its verdict (`go`, `doubt`,
   `no`) and why, its stance, for, against, what instead, what it assumes and what would show it; its questions are the page's
   *Open questions* as today (§255.7). Its acceptance under `### Accepted`, a line of its *Done when* each, *met*, *not met* or
   *cannot see* (§257.5). BOARD.md says both; the page's schema moves (§255.12). Orkboard reading them into Talk's record is a
   spec of its own.
7. **One text, two frames**: each seat's rules (what it judges and how) are one text, the one its prompt is built from (spec
   151 C.3); a call's frame (the context pasted, one JSON object back) stays the call's, unchanged by a character; an agent's
   frame says what to read (the paths), what to write (the page's part) and what to give back (a line to the conductor).
8. **Elsewhere**: a tool that reads Agent Skills without Claude Code's fork runs a step in its own conversation, the one voice
   of before; `AGENTS.md` stays what every tool reads. The trial (§255.15) measures Talk three ways: Orkboard's, forked skills in
   Claude Code, one voice.
9. **Built** by spec 154: **A.** the agent's frame of each seat; **B.** Talk and Accepted in the page; **C.** the seats as Claude
   Code's subagents and skills, and the conductor; **D.** this repository's files written again, and the trial's arm.
The owner's call.

## 259. A question a written decision or spec already settles is answered by its reference, never asked of the person; what nothing written settles stays the person's (6 November 2026, the owner)

Changes: 255.7 (the person decides), spec 151 A.6 (an answer's line), spec 154 C.3 (the conductor's step).

Why: goal 154's Talk, held by `/tech-leader talk` in a context of its own, asked the person three things, and the session
conducting it passed them on as the Board's rules say (*never answer for the person*). The first, *what does a seat's
subagent hold?*, was settled already: spec 154 C.1 says *its role's text, A's rules*; the code had missed it. The owner,
asked why the questions came: and then *yes, write it as a decision and an amendment to the block*. A rule that cannot tell a
question still open from one already decided asks the person again what they decided, and teaches them to wave questions
through. So:
1. **A question a written decision or spec settles is not the person's**: the conductor (or any tool working the Board)
   answers it by its reference, under the question's line, `  - Answered: its rules only (decided by spec 154 C.1, 2026-11-06)`,
   and says so in the chat, in a line: which, and why it settles it. The person sees it in the page and in the chat, and
   overrules it by answering again.
2. **A reference is one the project holds**: a decision of its log (`§258`, `§258.7`: its `## 258.` heading, or an ADR file
   numbered so) or a spec (`spec 154`, `spec 154 C.1`: a file `154-*.md` of its specs). `orkboard goal answer … --decided-by`
   refuses one that is not there; `orkboard check` finds one in a page.
3. **What nothing written settles stays the person's**, as §255.7 says: a choice between ways, a cost, a decision against an
   earlier one, a goal of one's own, going into main. Citing a reference that does not say what the answer says is answering
   for the person; the rules say so.
4. **The words**: the block's *The person decides* gains the line; BOARD.md shows the answer's line and its references; the
   conductor's step 4 answers the settled ones first and stops for the rest.
5. **Built** with this decision: `realm/agent_rules_text.py` (the block, BOARD.md, the conductor), `gui/board_cli_goals.py`
   (`--decided-by`), `realm/board_check.py` (`reference_exists`, the finding); this repository's files written again.
The owner's call.

## 260. What trial 152 found: a bad page never stops the Board; a step that changed what people see is looked at or said unlooked; a doubt the code settles is checked, a question a reference settles answered, and the weigher weighs only; the Board in the code opens as it is (6 November 2026, the owner)

Changes: 257.4 (a screen's line), 257.5 (a step nobody looked at), 259.1 (the app answers by reference too); keeps 156.8, 198.4
and 255.12, which the code had not followed.

Why: `docs/trials/152-a-leader-accepts.md`, two goals on local Codex against §253's run, at `452c44c0`. The flow cost 40% less
and split no task, but: Orkboard at `main` did not open on this repository (F1: a dot in goal 96's slug); every *Done when* line
was `[test]`, five of them about a screen, so nothing asked for a look and the base's miss was accepted as met (F2, F3); a brief
asked a Codex task for browser tests its sandbox refuses (F5); Talk asked the person what one search of the code answers, asked
what a spec had settled, and Product, weighing a goal not routed to it, made the person swipe past it (F6); the Board in the code
opened as a new project, its leaders as the Taskmaster, and committed 121 pages on the first open, its history as news (F8); a
diff's minus was always 0 (F9). The owner, given the ways and their costs: *let's go by your recommendations*. So:
1. **One bad page never stops the Board.** A goal's slug is `[a-z0-9-]+`: `orkboard import --goals` makes it so from a spec's
   file name (a dot is a dash); a page whose file name is not a slug is left out of the Board's list and `orkboard check` names it
   with the name it should have. This repository's goal 96 is renamed.
2. **A step that changed what people see is looked at, or said to be unlooked** (changes 257.5): when a task of the step changed
   what people see (code's own test, `core/idea_shot.py` `sees`), the step has no picture, and no line of the step's *Done when*
   is `[look]` or `[person]`, the acceptance raises, by code, *Nobody looked at what this step changed: <the files>*. It is
   told to the person as a line it cannot see is (§257.5).
3. **A screen's line is `[test]` only at the state a person first meets** (changes 257.4, spec 149 J.3): the section's rule says
   a line about what a person sees is `[look]` unless its test opens the screen in the state the line names, as a person first
   meets it; the acceptance of a step that changed what people see is told that a `[test]` line of a screen is met only so.
4. **A plan never asks a task for what its tool cannot do**: when the task's tool cannot start a browser (Codex), the planner is
   told to ask for no browser test and no test that serves a page; the gate runs them.
5. **A doubt the code settles is checked, not asked** (keeps 156.8): Talk's leaders still read no file; a doubt that reading the
   code would settle says what to look up, and one read-only call (`ground`, four files at most) looks it up before the hearing:
   settled, the doubt is a go with what was found; not, the doubt stands with it.
6. **The app answers by reference too** (changes 259.1, which was a tool's): before Talk's questions reach the hand, one call
   (`settle`) looks for a decision or spec that settles each; one it settles, by a reference that exists (`reference_exists`)
   and a choice of the question's own, is closed with its answer and its reference, kept in Talk's record and said in the goal's
   Talk; the rest reach the hand as today. What it cannot settle stays the person's.
7. **The weigher weighs only** (keeps 198.4): Product weighing a goal not routed to it gives a priority and the goals to wait for;
   its `doubt` or `no` opens no hearing and makes no objection; Talk's record says its priority and why, not an empty *For* and
   *Against*.
8. **The Board in the code opens as it is** (keeps 232.1, 255.12): a project whose Board has parties is laid at once, read where
   the Board's pages are; a party's leader named by the page and not yet on this machine is installed from the library; a leader
   wears its party's race; opening writes no page only to move its schema, writes no empty brief, and a goal already done when
   this machine first reads it is seen. **To main** stands above the goals not yet seen.
9. **The words**: a diff says what it removed.
10. **Built** by spec 155; F4 (what the checks into main do with a red from before) is a goal of its own.

## 261. One card picked, on either side; the table follows its phase; the edge goes: the discard is the Release column at the window's right, Live and Release tabs again, the die and a drum of potions in the hand under it, Stop all said in words (6 November 2026, the owner)

Changes: 126.4 (a phase gone by opened by its mark), 176.2 and 177.8 (the potions' rows), 177.1 (the default's frame),
188.1–2 (Release and Live not tabs at the wide width), 206.4 and spec 128 B (a face-down card not picked, the pile's list),
232.4 (the empty slot's place), 238.2–3 as 254.7 changed them, 246.1 and 254.4 (Stop all and Resume on the die's faces),
254.3 (the table's edge), 254.7 (the past held by the lich, the pyramid); spec 150 D and E2.2–E2.3.

Why: the owner, as designer and product manager: *the table's interface is too hard: the goal's phase switches, a cross for
the clean table, a card picked in the discard shows another table altogether, a back button*. Read in the page: three states
of their own (`frame/state.js` `picked`, `over`, `lifted`) and the tab, mixed freely, so neither ← nor × says where it goes;
the phases in the pane's title are four marks of which three open a page over the pane and one opens nothing; the discard
pressed opens a view of its own over the table; a face-down card in the column cannot be picked and lifts its pile's list. In
the edge (spec 150 D) eight objects ask three questions twice or thrice: *ready for main* at the discard's foot, the open ring
and the discard's view; *the past* at the lich, its line, the pyramid and the discard; the lich opens the past, not Release's
table; the die holds Play, Stop all and Resume, two of them on faces to be read in 3D, a safety control among them; the ring,
the largest object, sleeps most of the time. The owner's proposal: **one card picked at most, from the left or the right**, in
any phase, drawn plainly; the table the whole project's with none, the picked card's through a leader that works on it, else
that leader grey. Then, from the audit, the owner's yes on each: the portal and the discard one object, the past deeper in it,
Release and Live tabs again, Stop all off the die, the potions kept but their keeping hidden; then the potions as a drum, the
die left of it, both the discard's width and the hand's height, and the discard always there, through the open tab's eyes.
So:
1. **One card picked, or none.** A goal's card in the Orkmaster's column (any pile, face down too) or in the discard (a goal
   done, ready for main, or of the past) is picked by a press; one at a time across both sides. **Picked, it is drawn plainly**:
   risen, its edge in the ink, its rune and title said again in the pane's title. The other cards are not dimmed.
2. **The pick is put away by the same card pressed again, Esc, or a press on an empty place of the column or the discard.** No
   × for it; no ← for it. The pick is kept in the page's address, so the browser's and the phone's back put it away too. *Back*
   (←) is left only for a step down from the table into a file or a diff, and back from it.
3. **The tabs while a card is picked**: the Orkmaster's always, and the tabs of the leaders on its route; **the others grey**.
   A grey tab hovered says *<Leader's party> is not on this goal. Press to leave it and look at <party>'s table.*; pressed, it
   puts the pick away and opens that tab: no dead press. A card picked while the open tab is not on its route opens the
   Orkmaster's tab. A goal not routed yet greys every leader: it is the Orkmaster's alone.
4. **The table follows the picked card's phase** (this changes §126.4): through the Orkmaster, its route and what it costs while
   new, its plan once at work; through a leader, its say while in Talk, its section while in Spec, what it will change while at
   work (§206.4, kept), what it changed against what was promised once done (§206.8, kept). **The phases in the pane's title
   are a mark, not buttons**: *Talk · Spec · Work · Done*, the one now marked; what an earlier phase said lies folded at the
   table's foot, *Earlier: Talk · Spec*, opened where it lies.
5. **A face-down card is picked as any card** (this changes §206.4's and spec 128 B's press): a pile hovered fans its backs
   (one back, §254.5), any of them pressed is picked; the pile's list over the pane goes; the order is changed by dragging, as
   today. §236's tuck stays.
6. **The hand is not picked from**: a hand's card lifted (to answer it) picks its goal as well, so the table shows what the
   answer is about; the picked goal's cards in the hand are marked. One pick still.
7. **The discard is the Release column, at the window's right, on every tab** (this changes §254.3; §176.3's *on every tab, a
   party's its own* comes back): the frame's last column, a lane wide, under **Release's tab, the row's last; Live's tab before
   it** (this changes §188.1–2: at the wide width Release and Live are tabs and their heads leave the ring). **It shows the done
   through the open tab's eyes**: on the Orkmaster's tab the project's, on a party's tab that party's (a goal is a party's when
   its route held it), on Release's tab what is ready for main and the versions; its label *Discard*, *Tech's discard*. The
   pick's rule 3 keeps it whole: a tab open while a card is picked is on its route, so its discard holds the card.
8. **The portal is drawn round the card ready for main**, at the top of the discard, only while one is ready, checked or going
   in; **To main is the picked card's act**; picked, Release's table shows its checks (the skeletons, now on the table with
   their words) and the rite plays at the discard's top. Nothing ready, there is no ring.
9. **The past lies deeper in the discard**: under the goals done and not yet seen, the earlier ones by version (*Unreleased*,
   then a deck a version), newest first, through the open tab's eyes (the chronicle's `party`, spec 150 E1, kept). **The
   pyramid, the lich's line and the past over the pane go.** A decision newer than a party's last look is a mark on its tab.
10. **No edge**: `frame-edge` goes; the table gains its width less the Release column's.
11. **The hand's right end, under the discard and as wide as it**: **the die**, then **the drum of potions**, both within the
    hand's shown height (100 px at the wide width). The die is drawn at 2 px a cell (48 × 60, orkUI's new `.small`), its word
    under it.
12. **Stop all is said in words** (this changes §246.1 and §254.4): where the die's word is, while the orks work, the button
    *Stop all*; after it, *Resume*; else the word *Play*. The die's front face is a die's face again. §246.2 holds: the Board turns
    the die, never the person.
13. **The potions are a drum** (this changes §176.2, §177.1's frame and §177.8): **in front the active tool's potion** (the
    one the open tab's work, or the picked card's, goes to), at its size of §192 (kept); **beside it its two neighbours**, at 2 px
    a cell, darker and half behind it; the rest behind, unseen. **The drum turns by itself** when the active tool changes (one
    motion, none under reduced motion), **never by the person**: what is in front is never a choice made by a slip. A tool at
    the warn or the danger level takes a neighbour's place, in its colour. **Hovered or focused, the drum unrolls** into a row
    over the hand: every potion with its shares and its *back 14:00*, and at its end the empty slot (this moves §232.4's slot).
    A potion pressed lifts its tool's card as today; the tool a party works on is chosen there. The default's frame goes: the
    front is the default.
14. **Unchanged**: the narrow page and the phone keep their layout (they follow 1–6 through the same state); the runes, the
    rite, the moon of a night's goal, §192's sizes and windows, §236's tuck, the conflict card (§254.6), the first open's
    four cards (§254.8, its potions' and portal's places read again from 10 to 13).
15. **The words** (`TERMS`): *<party> is not on this goal. Press to leave it and look at <party>'s table.*; *Earlier*;
    *<party>'s discard*; *Stop all*, *Resume*, *Play* as today.
16. **Built** by spec 156: **A.** orkUI 0.31.0 (the small die, the drum), then copied; **B.** one pick; **C.** the table by the
    phase; **D.** the Release column and no edge; **E.** the hand's right end.
The owner's call.

## 262. Goal 156's Talk answered: a tool running low is said in words in the drum, all five parts are built, the owner's week shows it; the pick's address has one writer, and C and D are built one after the other (6 November 2026, the owner)

Changes: 261.13 (a tool at the warn or the danger level beside the front), 261.16 (the parts' order); spec 156's waves.

Why: goal 156's Talk, each leader in a context of its own (§258): Design *go*, against the drum's neighbour that says a tool
running out by a dimmed colour alone (WCAG 1.4.1, 1.4.11: it is money, CLAUDE.md's *say plainly*); Product *doubt*, the
Release column and the drum a second bet after §254's edge of a day ago, better after a week of the pick alone; Tech *doubt*,
the pick in the address a fourth writer of the browser's history (beside `table/table.js`, `upmenu.js`, `pwa/board.js`), and
`table/pane.js` shared by C and D. The owner: *1) agreed, 2) we do all, 3) without testers*. So:
1. **A tool at the warn or the danger level beside the drum's front is drawn at full brightness, its share in words under it**
   (*8%*, *back 14:00*), in its level's colour; only a neighbour at rest is dimmed and says nothing. The drum's box widens to
   what that needs, within the Release column (this changes §261.13).
2. **All five parts are built**, in spec 156's order (Product's split not taken).
3. **The simpler table is shown by the owner's own week of use**: a line in the project's journal when it ends, a pick lost or
   misread, or none; no tester is asked.
4. **The pick's address has one writer**: `frame/state.js` alone writes and reads `#goal=` and puts the pick away on Esc;
   `table/table.js` (its Esc, and its pick that opens the goal's party's tab) is made to go through it, and is one of B's files.
   The narrow page's back entry and the pick's keep their order: a file opened over a pick closes on the first back, the pick on
   the second.
5. **C and D are built one after the other** (spec 156's own rule, *parts of a wave share no file*; answered by its reference):
   waves **1** A, B · **2** C · **3** D · **4** E.
The owner's call.

## 263. The back redrawn closer to a tarot back; To review's ring at the middle of the back; the pane says nothing when nothing is picked (6 November 2026, the owner)

Changes: 254.5 (the back kept plain: four strips and four curls, no moon, no star, no lozenge); 261.6 (the pane's title when
nothing is picked).

Why: the owner, looking at the table after spec 156 D: *the ring of runes is not in the horizontal middle, and the curls are
poor: closer to the reference* (a tarot back: filigree corners, a line with a lozenge down each side, a moon in a circle at
the top and the bottom, stars round a sun). And, on the same screen: the pane kept an empty title row with its `…` when
nothing was picked, and *Nothing is at work* sat at the top of the last lane, not in the table's middle. So:
1. **The back is redrawn after the reference** (orkUI 0.32.0, `backs/back.svg`, `tools/build_back.py`): **filigree in the four
   corners** (a scroll that curls into itself, a tendril along each side ending in a small curl, a leaf at the very corner),
   **a thin line down each long side with a lozenge at its middle**, **a moon in a circle at the top and the bottom** of the
   card's axis with a bead and a small lozenge before the ring, **four small stars** round the ring. On a finer grid, 80 x 112
   (a stroke about 1.8 px on a 144 px card, an engraving's line). Still two greys, no colour (decisions §53.5): the
   reference's gold is not taken. The ring of runes stays the CSS's, and the small back keeps the sides and their lozenges
   alone.
2. **To review's back lies whole in what shows**: the deck's card keeps its 13 px under the window's edge (§251.4), but the
   back's drawing is laid on the part that shows, so its corners, its sides and its ring share one middle, the one the ring
   of the wait already had.
3. **The pane draws no title row while nothing is picked**: the table is the project's then, and the lanes say it; the
   Orkmaster's menu (`…`) stays, alone in the pane's corner over the lanes. *Nothing is at work* stands in the middle of the
   lanes, not at the top of the last one.
The owner's call.

## 264. The + card wears the back's drawing in its own green, round its seal; its corner brackets go (6 November 2026, the owner)

Changes: 185.4 (the + card's face: its corner brackets), 263.1 (the back's drawing is the + card's too).

Why: the owner, on the redrawn back (§263): *the same back must be on the card that makes a goal, only green and with the +*.
So:
1. **The + card wears the back's drawing in its own colour** (orkUI 0.33.0, `.ork-card.ork-plus::before`,
   `backs/plus-lines.svg`): the back's four corners, the first stretch of its sides and a moon in a circle at the top and the
   bottom, in the card's green at 42%, round the seal of summoning, its + and its element as they were. The seal (136 px on a
   144 px card) lies where the back has its stars, its bead and its sides' lozenges, so the + card leaves them out and its moon
   is a little smaller. On the narrow page the + card's seal is `.small`, and it takes the small back's sides alone.
2. **Its corner brackets go** (`hand/hand.css`): the back's corners stand there now.
The owner's call.

## 265. The drum shows three round its front; an alert neighbour's mark stands on its own bottle; the + card sits 32 px lower (6 November 2026, the owner)

Changes: 261.13 and orkUI's drum note *no wrap-around* (the places beside the front), 249.2 (the + card lies whole in the
window).

Why: the owner, on spec 156 E's hand: *fix the drum*: a tool in danger beside the front had its mark far over its small
bottle, and with the first tool in front the place before it stood empty. And: *lower the card that makes a goal a little,
so the goals at work have more room*. So:
1. **The drum shows three round its front whenever there are three tools**: with the first in the person's order in front,
   the last stands before it, and with the last in front, the first stands after it. A tool at the warn or the danger level
   still takes the nearer neighbour's place (§262.1). Nothing the person does turns the drum (§261.13).
2. **A mark over the drum stands 2 px over its own bottle**, whatever the bottle's size, the front's and an alert neighbour's.
3. **The + card sits 32 px lower** at the wide width: its foot, the lower moon of the back's drawing (§264), lies under the
   window's edge, its seal whole; the Orkmaster's column ends 32 px lower, so the goals at work have that room.
The owner's call.

## 266. The inventory: how the project is set, laid on the table, its ways in the hand; a leader is a hero of a school; four ways of answering; a chair is a craft; the die's faces are what the project can run; Stop all above the potions (7 November 2026, the owner)

Changes: 47.4 (*Start plans by themselves* as one switch), 57.1 (what the Board puts off, now by the goal's priority), 145.6
(the project's **…** keeps Settings' plumbing only), 151.5 (the one place of the parties), 164.1 (a leader's name its
hero's), 190 and 196 (the die one Play, its up face its state), 261.12 (Stop all and Resume at the die's word).

Why: the owner, as designer and product manager: *simplify the interface by game mechanics, not complicate it*; the settings
are rows of switches in Settings, the parties' place and the potions, and none says what it costs. Talked through on the
mockups `docs/mockups/merchant/` (and the first try, `docs/mockups/route-and-stall/`, not decided), from a merchant's stall
to what was kept: the table shows what is, the hand what the person decides, as everywhere in the window (§145.1, §167.7); a
leader is a set chosen at once, as a hero is; the person's trust stays the person's (§52.6). So:
1. **The inventory** (`TERMS`: *Inventory*, always beside *how the project is set*): a backpack, the row's last thing after
   the tabs. Opened, the table's edge is stitched and the tabs stay; **a tab picked says whose**: the Orkmaster's the whole
   project, a leader's its party. **The table lays that tab out as it is set**, a sheet of things in groups; **a thing
   pressed lays its ways in the hand** (the hand's cards step aside while it is open), each priced against the person's own
   in the first potion's week and hatched on the potions; **hovered, a way shows in its place on the table**; **played, it
   flies to its place**, with *Undo*. The person's own is marked *Yours*, what was before *Yours before*, the Orkmaster's
   pick a star. **A thing dropped on the discard goes back to its default** (in the inventory only; *Back to default* on a
   thing picked, for the keyboard and the phone). The potions and the die are pressed as they are. Settings' **…** keeps the
   plumbing (sign-ins, the Board in the repository, the rules for any AI tool, the phone, keeping awake, updates, logs) and
   ends with *How the project is set: Inventory*.
2. **The Orkmaster's sheet**: *When* (*Give me time to look*; *High*, *Normal*, *Low goals start*: *Now*, *By the week*,
   *Tonight*, *By hand*; *When I am here*), *How much* (how deep, the day's cap of what answers by itself), *What leaves
   this computer* (*Push after merging*; the cloud run, its money said as money), *The Orkmaster's questions* (a Low goal
   ready, a conflict with a decision). Risk still decides whether work may start without the person, whatever these say
   (§57.3). The gate is read, not traded, at Release's hero.
3. **A leader is a hero of a school**: a set of its craft's framework (its lens's aspects, §184, and how its table is laid),
   its flow (steps within the phases, never other phases), its size, **how much it decides itself** and **how often it says
   no**, and its cost, shown as stats on its card. Three to six a craft, the Orkmaster's pick starred; its name says its
   school, after §164 (*Spike Shaman*, *Jobwise Knight*), never a real person's. **How often it says no moves only where it
   stops**: a risk is said by every hero; the locks, the gate and §57.3 are no hero's. A leader's sheet: its hero, its
   questions, its conflicts with its spec, its seats' AI tool and tier. The framework is never a card of its own here.
4. **A hero's face** is its race's higher form with its skin or helm, its horns, antlers or wings and one detail changed
   (`heads/make_heads.py` drew four a race); the hood stays the tier's gear, the knight's helm a warm metal, no skin the
   action's green; the moods are laid over each. Drawn in orkUI before they are used.
5. **Four ways of answering**, a question kind each: **Pen** (the person's words), **Choice** (the leader's ways; *if you do
   not look in N, the leader's pick* is a Choice with a wait), **Fork** (three or four ways worked out, each drawn on the
   table, the leader's pick marked, *Other…* to the Pen; it costs, and says so), **Silent** (the leader decides and says it
   in its evening line). **A hero brings its own ways; what the person sets is the person's and outlives the hero.** Locked
   to Pen, Choice or Fork, never Silent nor a wait: going into main, money above what was agreed, dropping or holding a
   goal, a decision against an earlier one. The night offers a step up from how the person answered (§51.4), taken or not by
   the person.
6. **A conflict with an earlier spec**, a leader's: **Ask** (a Choice or a Fork), **Declare** (the leader rewrites the
   earlier spec and lays a card where it changed, with *Undo*), **Silent** (it rewrites; the evening line and the spec's
   *Changed since* say it); a spec rewritten often goes back to Declare by itself. **A decision is never rewritten**: a
   conflict with one is asked, always.
7. **A tab's chair is a craft**: the tabs stand in the route's order; the Orkmaster seats the crafts of the project's stage
   (§122.5) with its pick; the crafts a new stage brings come as **empty chairs**, no card; the empty chair at the end seats
   one sooner; a hero taken off leaves its chair empty. **An empty chair shows its craft's texture on its back; a taken one,
   its hero's race says the craft.** **A hero's card**: its craft's texture at the top left (whose), the one hero silhouette
   at the top right (what card; a new sign).
8. **Whose table, by its texture**: a pattern in the ink at a few percent on the table's surface, a craft each (Tech a
   blueprint's grid, Design a canvas's dots, Product contours, Release stones, Run stripes, Marketing chevrons, the
   Orkmaster plain felt), every day, not only in the inventory; the inventory is told by its stitched edge. No new colour.
9. **The die's faces are what the project can run**, read from Tech's table (§112): a client, a server, both at once as one
   face, an Android build, an iOS build; six at most. The up face is what Play starts; a side pressed turns the die to it;
   **each face its own state** (the cross of a start that failed, the spark of something new, §196's marks moved to the face
   they belong to). A build is the computer's work, no mana: its time is said (*about 4 min*), the die wobbles while it
   builds; an Android build goes to the paired phone or stays a file; **an iOS build needs a Mac with Xcode**, its face
   locked elsewhere with those words. In the inventory: the face it rests on, where an Android build goes.
10. **Stop all and Resume are words above the potions** (this changes §261.12): *Stop all* while the orks work, *Resume*
   after it; the die's word is Play's alone.
11. **Later, not decided here**: a forge where the person makes a hero (its framework a part there) and shares it as a copy
   (a leader's code: data only, read before it is taken, never a real person); the tiers' gear as no gear, an iron band, a
   silver circlet (the gold crown the Orkmaster's); the route drawn as a path on the table.
12. **The words** (`TERMS`, with the first spec): *Inventory*, *hero*, *Pen*, *Choice*, *Silent*, *Declare*, *Yours*, *Yours
   before*, *the hero's way*, *Back to default*, *Take off the chair*, *What leaves this computer*.
The owner's call.

## 267. The inventory is a merchant's stall: the wares on the rug, what you carry in the hand; a hero lays its table, its frame kept by its leader; the first goal lays the tables (7 November 2026, the owner)

Changes: 266.1 (the table and the hand turned round in the inventory; *Back to default* the merchant's service), 266.3 (how a
hero's table is laid, made precise), 266.11 (the route drawn on the table stays later); spec 95 §13.1.

Why: the owner, on the mockup `docs/mockups/merchant/` (its section 1, the stall, and section 2, the eighteen tables): *make the
merchant's mockup more like a deck-builder's merchant, and show how the tables of all eighteen agreed leaders will look*; then
*a spec and its implementation on the simpler models, into main*; and, asked whether laying the tables the first time calls a
model, *yes: make it the first goal of the onboarding*. §266.1 laid what is set on the table and the ways in the hand, so a
thing had to be pressed before anyone learned what there was to take; a merchant lays every ware at once, its price under it,
and what you carry stays yours in the hand. A hero's table needs what code can read (the Board, git, the System map, the
screens) and what only its leader can keep (a job's words, an opportunity tree, a bounded context); the first is free, the
second is a model's pass, which is the person's money and so is never spent silently (§57.3, §160.6). So:
1. **The inventory is a stall** (`TERMS`: *Inventory*, beside *how the project is set*). The backpack at the tabs' end opens it;
   the table's edge is stitched, the tabs stay and say whose. **The Orkmaster stands at the rug's left** and says in one line
   what it would take; **every ware of the chair picked lies on the rug at once**: on a leader's chair its heroes on the top
   shelf, the ways of the card lifted from the hand on the shelf below, its seats (its AI tool, its tier) as the small things at
   the right; on the Orkmaster's, its own wares. **A price plate under each ware**: what it adds to the first potion's week, a
   saving in the success colour, money said as money; what you carry reads *in your hand*, a locked ware *not here* with why.
   **The hand is what you carry** of that chair, a card a thing; a ware hovered shows in its card, the potions what it costs;
   pressed, it flies into the hand over the card it replaces, with *Undo*. **Back to default is the merchant's service**, free,
   at its feet: a card of the hand dropped on it, or pressed with a card lifted; the discard takes a card too (§266.1).
2. **A hero lays its table** (this makes §266.3's *how its table is laid* precise): **its frame** is its school's places, a lane
   or a row each with its question (XP's *Red*, *Green*, *Refactor*, *Released small*; AARRR's five steps). A hero whose
   school is its craft's default (§184: Sh.man, Pixel-Perfect Dryad, Angel Invest Knight, Uptime Imp, Growth Hack Gnome) lays
   its craft's map as today; **any other lays its frame**, its places filled from what its leader keeps and empty, with their
   questions, until then. The Orkmaster's table stays the Board, Release Night King's dev against main.
3. **The frame is kept in the Board**, a file a party (`llm-wiki/general/pages/tables/<party>.md`), its places and their lines
   written by the leader and read by any AI tool as the rest of the Board; each later pass of the leader keeps it.
4. **The first goal lays the tables**: after the first open the Orkmaster lays one goal, *Lay the tables*, routed to the parties
   seated, its price said; it waits in line as any goal, started by the person. **A hero taken in the stall lays a goal of its
   own**, *Lay <party>'s table*, and its plate says that pass's price. No model is called by opening a project.
5. **Not in this step, later**: a frame's places read by code (hotspots from git, the tests' runs, a trace, a funnel's numbers),
   the ways of answering's engine (§266.5–6), the starts by priority and the day's cap as settings (§266.2), the Orkmaster's star
   on a ware, the textures (§266.8), the die's faces (§266.9). A ware the engine does not have yet is not laid on the rug.
6. **The heroes' faces** are drawn in orkUI first (`heads/make_heads.py`, sixteen with the imp's and the fairy's two); until a
   hero's head is in orkUI, its race's elder head stands for it.
The owner's call.

## 268. Colour is the party, the element and a signal (8 November 2026, the owner)

Changes: 53.5 (colour means a signal), 92.2 (the table's wood as its exception); where 106, 115 and 148 say *colour is a
signal*, they read as this.

Why: the owner, on the mockup `docs/mockups/table-look/`: the window is flat; *colour is not only a signal*. So:
1. **Three layers of colour, told apart by their form, never mixed.** **The party** (its race) colours the frame of things:
   its tab's name, the rule under its tab, the light down its lane, its pennant, its table's felt. **The goal's element**
   colours the face of its cards: a band on top, a tinted face, the window round its sign. **A signal** (danger, alert,
   success) is the brightest, always a ring and an icon, never a fill.
2. **Nothing hides a signal.** A party's or an element's colour is never a ring round a card and never as bright as a
   signal. A test checks that a signal is seen on every felt and every element.
3. **The parties' colours, by race:** knights gold (Game design, Product), orks moss (Tech), elves plum (Design, Art), the
   undead night blue (Release), goblins rust (Run, LiveOps), gnomes sea (Marketing), the Orkmaster the table's warm wood.
   orkUI keeps them apart from the signals' hues; Tech's moss stays as the mockup has it (`#8fbf4a`), beside the action's
   green.
4. **Still without colour:** a person's words, a control's state, a label's meaning. The ork green stays the one green of
   a button.

The owner's call.

## 269. The table's look: a lamp at its top edge, each leader's felt, bronze frames, a pennant over each leader (8 November 2026, the owner)

Changes: 266.8 (the craft textures on the tables); 92.1 (the table's wood stays, as the Orkmaster's felt).

Why: the owner, on the same mockup: a table lit and framed as a game's, retro, with no smooth gradients. So:
1. **The light from the table's top edge**, in half rings, five steps, each step's edge dithered by a 2 px checker in the
   next step's colour. No smooth gradient anywhere (the room, the table, a lane, a card, the hand); a shadow or a glow is
   hard pixel rings, never a blur. The light is the lamp's (§271): out, it goes.
2. **Each leader's table its own felt**, in its party's colour, dark: Tech moss, Game design and Product oxblood with a
   gilt rim, Design and Art plum, Release night blue, Run and LiveOps rust, Marketing sea; the Orkmaster's the warm wood.
3. **Bronze frames** with rivets at the corners round the table, the column, the discard and the hand; the headings on
   bronze plaques, in the pixel face.
4. **A swallowtail pennant on a pole** in the party's colour over each leader, taller over the open one, clear of the
   window's top edge. Not the merchant mockup's craft pennants.
5. **A lane** has its party's light in three steps down from its tab; **an empty lane says whose it is** and how to give
   it a goal (*Release is free · throw a goal here or @Release*).
6. **A card**: a thick frame in its element's colour with a gilt inner line, the element in steps down its face, a
   bevelled window, the goal's strip a ribbon. A signal's ring is one ring and a faint second; in the column's stacked
   rows, its border.
7. **The hand** fans slightly (±2°) at the desktop's width; a card rises toward you on hover. Reduced motion: neither.
8. **Dropped:** the craft textures (§266.8) and the heads and signs drawn at twice the grid.
9. **orkUI first:** its tokens and components (the felts, the steps, `.ork-table`, `.ork-card`, a plaque, a pennant),
   copied here, then `gui/`.

The owner's call.

## 270. No big card: a lifted card stays a hand card, its answers are the hand, the table is its context (8 November 2026, the owner)

Changes: 251.1 (the opened size, 404 × 566), 251.6 (the opened card never grows); spec 147 D.1.

Why: the owner: *the words a big card holds will not be read*; a card game splits them: the table says why, the lifted
card what is asked, each answer is a card (`docs/mockups/answer-cards/`). So:
1. **A lifted card rises out of its slot onto the table's foot**, 144 × 202, in its signal's ring; the goal's card in the
   column is ringed the same.
2. **Its answers are the hand**: each a card of the same size, lying where the hand's cards lie, cut by the rim, rising
   when hovered: a way with one line of what it leads to (its point in its first words), the leader's pick marked by its
   head; *<Leader> decides* (the Silent way, §266.5); **Your own words…** (the Pen), pressed, a field on the table beside
   the question with *Send to <leader>*. A failure's ways the same (*Start again*, its cost in the corner). *Open…* and
   *Put it back* at the row's end.
3. **The rest of the hand sinks and goes grey** while a card is up, the + card, the die and the potions with it.
4. **The table is the context, no new mode**: lifting a card already turns the table to its goal. A goal not yet agreed
   lays on its table what its leaders said in Talk and its open question with its ways.
5. **A way's line is its leader's**, written to fit the card (§251).
6. **A new goal is made in the Orkmaster's first lane**, not opened: the + card lays a card of 144 × 202 at the lane's
   top, its words written in its middle, **its settings at its four corners** as every card is read (§251.2): top left its
   element, top right its kind (feature, bug, tidy, screen), bottom left who (the parties of its route, the Orkmaster's
   until changed), bottom right how much (its price, when it starts). A corner pressed deals its choices to the hand, as a
   question's answers are; the Orkmaster's pick starred.
7. Cards have two sizes on the desktop: 144 × 202 and the Orkmaster's hand 56 × 78. The phone follows in a goal of its own.

The owner's call.

## 271. The lamp is the person: its chain where the door stood, lit *Here*, out *Away* (8 November 2026, the owner)

Changes: 246.4 (the door's drawing and its place), 201.8 (orkUI's door). What Here and Away do (§246.4–5) is unchanged.

Why: the owner, on `docs/mockups/room-things/`: the door is one more sign; a lamp over the table makes the person's
presence the room's own light. So:
1. **A lamp's chain** hangs from the window's top edge at the head of its right column (the Release column, the discard),
   a bead to pull; its words beside it as the door's were: *Here · until 23:00*, *Away · until 19:00*, *· held* after a
   pull while the hours lead.
2. **Lit, the person is here**: the table's light (§269.1). **Out, away**: the light goes, the felt flat and darker, the
   lanes unlit but for the rule under their tabs; the cards keep their faces and a signal stays as bright.
3. **Pulled, it turns** as the door did (`presence.set`); the hours pull it by themselves (§246.4). The chain moves once,
   briefly; under reduced motion it is at once.
4. **orkUI draws the chain** (its bronze, the bead, pulled and at rest), in place of its door.
5. **Under 760 px** the chain and the backpack stand without their words (their `aria-label` and `title` keep them).

The owner's call.

## 272. The backpack and the new chair are things at the table's edge: the chair deals its crafts, the pick opens the backpack on it (8 November 2026, the owner)

Changes: 267.1 (the backpack at the tabs' end; the stall told by its stitched edge), 201 (the empty chair's press), spec 98
§3.6 (*New party* as a place over the pane).

Why: the owner, on the same mockup: the top row's controls as things; *the chair's press should deal the kinds of leader
to the hand, as a question's answers are, and the pick should open the backpack on that kind*. So:
1. **The backpack stands at the head of the discard's column** (§273), beside the lamp's chain (188 px holds both: the
   column is not widened). **orkUI draws it shut and open** (the flap fastened; thrown back, a card in its mouth). **Open, the table lies
   in its leather**: a stitched leather frame in place of the bronze, two straps with buckles over its top edge, no rivets;
   shut, the bronze is back.
2. **The new chair stays at the tabs' end.** Pressed, it is lit, the Orkmaster's question rises onto the table (*A new
   chair at the table · Which craft sits in it?*) and **the hand holds a card a craft not yet seated**, of those offered
   for the project's kind and stage (`project_stage.crafts`): its race's head, its line, its price a week; **the
   Orkmaster's pick starred** in the top corner. The rest of the hand sinks (§270.3); *Put it back* seats nothing.
3. **A craft's card pressed seats it**: its tab stands where the chair stood (its leader's head, its pennant, *new*), and
   **the backpack opens on its chair**: its heroes on the rug, its default starred and in the hand, a price plate under
   each; a hero is changed there as any ware (§267).
4. **Money is said before it is spent**: the craft's card says its price a week before the press (§57.3, §160.6); the
   chair's press alone seats nothing.
5. **New party's form goes; the project is said in the Orkmaster's header** (this changes §201's header): **its first line
   the project's name** (the switch of project beside it), **its second the project's kind and stage** (*Game · Being
   made*), in the caption face; the words *The Orkmaster* leave the header (its head stays, and its `aria-label` and
   `title` still name it). **The kind or the stage pressed deals its choices to the hand** (the kinds; *Idea*, *Being
   made*, *Live*), each card with one line of what changes (*Live: LiveOps and Run join the chair's crafts*), the present
   one marked; a card pressed changes it, *Put it back* nothing.

The owner's call.

## 273. The discard stands beside the table, not under Release: the window's right column is its own, its head the room's things (8 November 2026, the owner)

Changes: 261.7 (the discard under Release's tab, the row's last); 176.3 and 167 (the discard lies on the table, at its
right); CLAUDE.md's frame says *the discard … lies beside the table* once this is written.

Why: the owner, when the backpack and the lamp's chain needed a place: the right column's head is where they stand, so
the discard is not Release's: *we make it outside the table*. So:
1. **The discard is the window's right column, beside the table**, on every tab: what it holds is §261.7's (the done
   through the open tab's eyes, *<party>'s discard*, the portal round the card ready for main at its top, the past deeper
   in it, §261.8–9).
2. **Release's tab stands in the row with the other leaders'**, in the route's order (§266.7), not over the column.
3. **The column's head holds the room's things**: the backpack at its left, the lamp's chain at its right (§271, §272),
   over the label *Discard*. The column keeps its width.
4. The hand's right end under it is §261.11's (the die, the drum of potions).

The owner's call.

## 274. Release is no party a project must have: the person sends a goal to main from the discard, the gate's tests always run (8 November 2026, the owner)

Changes: 137.1 (Release in every project, never removed), 137.2 (Release alone writes main); 188's skeletons and 253.7's
*one way to main* hold only while Release is seated.

Why: the owner, once the discard stood beside the table (§273): *Release stops being one every project must have; through
the discard one goes to dev or main at once*; asked whether the gate's tests go too: *the tests always run* (the first of
three ways offered). Every party already lands its work in dev by itself (§101), and *To main* is code with no model and no
call (§137.4): Release's leader is needed for a version, not for a merge. So:
1. **Release is a craft as any**: offered at the chair (§272) and in the backpack, seated or removed by the person. Without it
   a project loses nothing of dev.
2. **To main is the person's act, from the discard**, on any tab, with or without Release: a goal's work in dev goes into
   main by code, **after the gate's tests** (`[gate]`: code, no model, no cost); a red stops it and says which test.
3. **To main without the tests** is a second act in the card's menu, said in those words; nothing else skips them.
4. **With Release seated**, its checks (the skeletons, §188) run before main as today, and it alone releases a version
   (§137.4's *Release a version*).

The owner's call.

## 275. A tab's name is light, its party's colour under it; words lie on a flat plate over the light's steps; the phone in the same goal (8 November 2026, the owner)

Changes: 268.1 (the party colours its tab's name), 269.1 (the steps under everything), 270.7 for the table's look (the phone in a
goal of its own).

Why: goal 161's Talk: Design's leader found the mockup below WCAG AA where a closed tab's name is in its party's dimmed colour
on the dark felt, and where the dithered steps of the light run under small words (a word then has no one contrast). The owner
picked the first of the two ways offered each time, and asked for the phone in the same goal. So:
1. **A tab's name is in the light ink**, open or closed; its party's colour is in the rule under it, its pennant and its glow.
   Text keeps 4.5:1 on every felt, lit or out; a test checks it.
2. **Words lie on a flat plate**: where the table's light steps and their dither would run under words (a label, a lane's words,
   a card's text), the words sit on a flat plate of one colour; the steps show between them.
3. **The phone in goal 161**: the table's look, the lamp and the backpack are drawn on the phone too, in the same goal.

The owner's call.

## 276. Success is no ring: the brightest signals are a failure's and a question's (8 November 2026, the owner)

Changes: 268.1 (a signal, danger, alert and success, the brightest, always a ring and an icon).

Why: goal 161's Design leader, at orkUI 0.35.0: the success green (`#86c062`) stands as light as Tech's moss (`#8fbf4a`, kept by
the owner), so it cannot be the brightest on the table without leaning on the action's green. The owner: success is no ring. So:
1. **A ring is a failure's or a question's** (danger, alert): the brightest colours on the table, by a lead a person sees over
   every party's and element's colour; orkUI's test asks a visible margin, not a unit.
2. **Success is a check and a word**, as today, in its green: told from the parties by its form, never a ring round a card; it
   keeps 3:1 on every felt, step and plate.

The owner's call.

## 277. The past from history is on the parties' tables: a goal done outside the window has its flag, dated by its decision; a long deck deals seven, then All · search (8 November 2026, the owner)

Changes: 261.9 (the past over the pane goes: a deck of more than seven now opens over the pane with a search).

Why: goal 162's Talk. A fresh Orkboard over this repository showed 0 goals in the past and an empty past on every party's tab: a
goal gets its flag only from Orkboard's gate, the chronicle reads a goal's route from the state alone, and a decision's parties
only when Orkboard decided it. This repository's git history begins on 6 November and its 119 history pages were laid by one
commit on 8 November, so no git date tells when a goal was built. The owner took the leaders' recommended ways, and for the day
the conductor's. So:
1. **A goal done outside the window gets a quiet flag** (`by: done`): no leader's fold into the living specs, no model call,
   no journal line. It stays history, never the discard; a flag is never undone.
2. **Its day is its decision's** (the page's `decisions:`); where it has none, the latest decision its spec names (§N); where
   none, the day it was laid.
3. **A page's `route:` counts for a party's eyes** while the state holds no route of its own. The history pages gain their
   `route:` once, in one commit the owner reads.
4. **A decision a goal carries is seen by that goal's parties**; a decision of no goal stays whole on the Orkmaster's tab, never
   placed by its words.
5. **A deck of the past deals its newest seven in place, then *All · search***: the whole deck over the pane with a search, as
   the goals in line end (§167.5).
6. **Product's tab shows its past now**; its jobs and the product's direction (Product's tree) wait for a goal of their own.

The owner's call.


## 278. A craft's heroes are only those that work on what is built: fifteen, no least number; the Orkmaster's star by the project (8 November 2026, the owner; taken on 7 November as §267 on a branch that never reached main)

Changes: 266 (its point 3: *three to six a craft*). Restores the owner's call of 7 November, whose number §267 main gave to the stall.

Why: the owner asked for each craft's heroes with their framework, flow and team, then for each to be weighed against the
product (the indie game developer with a day job, §218.2; a solo maker of a web or mobile app, H1; the day's three jobs,
§199), against what the window can show (its craft's map and aspects, spec 109) and against what is gathered by itself (the
hints of code, Play's signals, the brief, the mana's record). A hero whose framework has no map, no data or a cost the person
cannot carry is words the leader cannot stand on; the owner: *keep only the heroes that will surely work well; the least
number goes*. So:
1. **A craft's heroes are those that work on what is built today**: its framework has its craft's map and aspects, and what
   it judges by is gathered by code, Play, the brief or the mana's record. **No least number**: a craft has as many as work,
   six at most; a craft with one shows it with no choice; a hero is added when the map and the data it stands on are built.
2. **The heroes**, each with its school and its flow:
   - **Product**: *Angel Invest Knight* (the opportunity solution tree; outcome → jobs → goals), *Jobwise Knight* (jobs to be
     done; job → struggle → goal), *Appetite Knight* (Shape Up; shape → bet → build in the appetite, on the mana's record; the
     bet stays the person's), *Pillar Knight* (design pillars and what it leaves out; pillars → the goal against them → keep
     or cut, on the brief's *pillars* and *leaves_out*).
   - **Design**: *Pixel-Perfect Dryad* (Nielsen's heuristics; walk → the ten rules → fix), *Sprint Dryad* (the design sprint;
     map → sketch → decide → test: §199.3's sketches, picked on the phone, tried in Play), *Inclusive Dryad* (WCAG 2.2;
     barriers → contrast and keys → fix: `a11y` today, the controller, the Deck and the focus path once §209.3–4 are built).
   - **Tech**: *Sh.man* (C4 and hotspots; containers → parts → hotspots), *Spike Shaman* (extreme programming; test → code →
     refactor; the dearest of the three), *Scene Shaman* (an engine's scenes; scene → autoloads → coupling, on Godot, Unity
     and Unreal as System reads them).
   - **Run**: *Lantern Imp* (observability first; trace → read → fix, on Play's errors, failed requests and slow places).
   - **Marketing**: *Store Gnome* (the store page first; title → shots → test), *Growth Hack Gnome* (AARRR; acquire →
     activate → retain, by its hints, not numbers), *Position Gnome* (positioning; the alternatives → what only it does →
     who cares, on the brief's *why this, not what they use now*).
   - **Release**: *Release Night King*, not traded (as §266).
3. **Not taken, and why**: *Pivot Knight* (no measure to pivot by: the project's analytics are not read), *Diamond Dryad*
   (Full and dear, research there is none of, and its four steps are a goal's phases again, which §266.3 forbids), *Atom
   Dryad* (only for a project with a component library of its own, and Consistency has no hint), *Domain Shaman* (an indie
   game's architecture is rewritten in an evening, §208), *Fitness Shaman* (fitness functions as records are later, spec 109
   §5), *Uptime Imp* (no server and no SLO: nothing gathered). Talked of and dropped: a story map's, an API contract's,
   chaos', the cloud bill's and building in public's heroes, each needing a map or a source there is none of.
4. **Later**, when what they stand on is built: *Pivot Knight* with the project's analytics (spec 115's later part), *Uptime
   Imp* with Run's map (§215), *Atom Dryad* with a hint of a part made outside the project's library, a *Wishlist Gnome*
   (the Steam page → the demo's end → Next Fest) with §214.2 and §211.2.
5. **The Orkmaster's star by the project**, read from its kind and its stage (`project_kind`, `project_stage`), never fixed:
   for a game, *Jobwise Knight*, *Sprint Dryad*, *Scene Shaman*, *Position Gnome* (cheap, decided in a minute on the phone);
   for a web or mobile app, *Angel Invest Knight*, *Pixel-Perfect Dryad*, *Spike Shaman*, *Store Gnome*.
6. **The new faces**: *Pillar Knight*, *Inclusive Dryad*, *Scene Shaman* and *Position Gnome* are drawn in orkUI before they
   are used (§266.4); the mockup's heroes follow with the first spec.
7. **The words**: the heroes' names are words of the interface (§164.3), in `TERMS` with the first spec.
The owner's call.

## 279. A game's heroes: Game design's and Art's, LiveOps' chair empty until its map; the game's star mended (8 November 2026, the owner; taken on 7 November as §268 on a branch that never reached main)

Changes: 278 (its point 5: a game's star). Restores the owner's call of 7 November, whose number §268 main gave to colour.

Why: the owner asked whether §278's heroes fit every kind of project there is. Weighed against the parties each kind is
given (`party_recipes.RECIPES`: nine kinds take Product, Design, Tech, Release, Run and Marketing; a game takes Game design,
Tech, Art, Release, LiveOps and Marketing) and against what System reads (Python and JS/TS, Godot, Unity and Unreal): a web
app takes all fifteen; a mobile app most, React Native and Expo best (Flutter and native apps have no System, and Play is the
web client); a backend and code or data work take Tech, Product and Release, with Design empty and Run in part; a designer's
folder, a wiki, texts and an empty folder take mostly the heroes that stand on the brief or the sketches. **A game had no
hero at Game design, Art or LiveOps**, and §278.5 starred Jobwise Knight and Sprint Dryad for a game, whose chairs a game does
not have. So, by §278.1's rule (a hero works on what is built today):
1. **Game design's heroes** (the Loop map and its hints are built): *Dungeon Master Knight* (MDA and the loops; loop →
   reward → hook, on `no_reward`, `unfed`, `flat`, `spike`, `no_hook`), *Economy Knight* (sources and sinks; currency →
   source → sink, on `no_source`, `pile_up`), and *Pillar Knight* seated here too (the pillars over the loop are Game
   design's, §211.3), as at Product.
2. **Art's hero** (the Assets map and its hints are built): *Sprite Dryad* (an art bible, its pipeline and a budget; style →
   pipeline → budget, on `mixed_sizes`, `naming`, `unused`, `heavy`).
3. **LiveOps' chair stays empty** until its map (§215) is built: no map and no hint, so no hero; *Event Imp* comes with it.
4. **A game's star** (this replaces §278.5's for a game): *Dungeon Master Knight*, *Sprite Dryad*, *Scene Shaman*, *Position
   Gnome*. An app's stays as §278.5 says.
5. **What each kind takes is said, not hidden**: a hero with nothing to stand on in the project's kind (Scene Shaman outside a
   game, Design's heroes in a backend, a wiki or texts, Store Gnome with no store) is not offered there; a chair whose craft
   has no hero for the kind is an empty chair. That a wiki or texts is given a Design chair at all is the parties' recipe's
   question, not the heroes': later.
6. **The new faces**: *Dungeon Master Knight*, *Economy Knight* and *Sprite Dryad* are drawn in orkUI before they are used
   (§266.4), with §278.6's four; their names in `TERMS` with the first spec (§278.7).
The owner's call.

## 280. Each leader's map takes a board game's shape: heat on its parts, a goal's reach before it starts (8 November 2026, the owner; taken on 31 October as §195 on a branch, lost in a merge)

Restores the owner's call of 31 October (main's §195 is the phone's menu). Since then §206.4 shows a goal picked as each leader's view of what it changes (`js/table/goalmap.js`) and goal 161 laid the table's felt, light and frames: the reach below grows from the first, the maps' shapes lie on the second.

Why: the owner, after the lands (*style the leaders' tabs as the maps of their races' lands, with storytelling*) were turned
down as a skin (§50.5, spec 40's *an accent, never a picture*, and colours the elements already hold): *we refer to board
games everywhere: give each tab the right picture, a nod to some game.* A game earns a map when its loop is the map's work
(§50.4), and only its shape is taken (§50.5). The mockup of Tech's System (`docs/mockups/tech-reach/`) showed it: a network
game with outbreaks gives two rules that are the work, the heat of what code saw on a part and how far a change spreads
through what uses it, so a person compares goals by their spread before either starts. The owner: *the direction is right;
do it for every lens.* So:
1. **Two rules on every map, one grammar.** **Heat**: the hints code finds on a part (`map_signals`, every craft's) drawn on
   it, a hollow square a kind, three at most, beside the leader's concern's mark; until now they reached only the leader's
   prompt and the strip's chips. **Reach** (`TERMS`): a goal under the pointer in the hand, or picked, lights on the open
   tab's map the parts its section's *Will be* and its marks name (a solid edge in its element), what they reach by the map's
   own relation one step out (dashed) and two (dotted), and dims the rest; the strip says it in a line. Where the map knows
   what checks a part (System: a test), each reached part says so. Read by code, no call.
2. **A map's shape is its work's game**, its cards unchanged (one deck, a layout a map):
   - **System**, a network game: the columns as built (never a diagram); a link lights when a reach crosses it.
   - **Screens**, a dungeon's rooms: each screen's doors in and out on its sides, a wall where there is none (a dead end, a
     screen nothing leads to); a link back to an earlier step is a door too.
   - **The tree**, a tech tree: as built; the hypotheses (spec 116) are its parts when they are built.
   - **The loop**, a rondel: the ring closes, last step to first; what a step gives and takes lies on it as tokens.
   - **Art's assets**, an inventory: a card's width is its weight (light, normal, heavy), a lane's foot its total against
     the project's budget when one is set (`orkcraft.toml` `[art] budget_mb`); an asset nothing names lies faint.
   - **Dev and main**, a train and push your luck: the goals as cars, oldest first, each its age; past the eighth car the
     batch is big, marked where it starts; a goal's reach is the goals it must take to main with it (`goal_main.plan`).
   - **The way in** keeps its columns: no game fits it until people's numbers are read (§193.4); heat only.
3. **Not taken**: a free graph, an outbreak that spreads by itself, a timer, a score or a percentage of risk, the games'
   names or words in the interface (*changes*, *reaches*, *no test* say what happens), a new colour, a reach for a goal whose
   spec does not yet say what will change, the lands' pictures (Orkline Camp's, §50.1), a lore of the leaders.
4. **The rule of the line holds** (§50.5): no count of what waits, no streak; the reach is shown, Start stays the person's.
5. Its spec built by the cheaper model, each part reviewed; Tech's mockup (`docs/mockups/tech-reach/` on the branch `claude/tech-reach-mockup`) the only one.
The owner's call.

## 281. The heroes and the maps as the leaders recommended; the leaders' rules follow the decisions, and the Orkmaster reads them (8 November 2026, the owner)

Changes: 278.5 (the star seats nothing), 280 (its order of work and the phone).

Why: goals 164 and 165's Talk left six questions no decision settled; the owner took each leader's recommended way. The owner
also asked that, now that decisions are taken through the Board, its leaders work by every one of them: the role files carried
§266's heroes after §278 cut some, and the Orkmaster's role read no decision at all. So:
1. **The Orkmaster's star marks a hero on the stall's shelf only**; it seats no hero by itself (a hero not the craft's default
   costs a pass, §57.3).
2. **A party whose hero is cut gets its craft's default, said once** to the person.
3. **Lantern Imp is Run's default, with no table of its own.**
4. **Heat and reach come first, on the maps as they are**; each map's shape then comes as a stage of its own, seen in a picture.
5. **Reach on the desktop now**; the phone's in a goal of its own.
6. **Dev and main's reach on hover reads the plan kept**, without git's trial run.
7. **The leaders' rules follow the decisions**: the role files Orkboard writes say today's heroes (goal 164), and **the
   Orkmaster reads the decisions** its goal names and the log's newest before it routes (a goal of its own).

The owner's call.

## 282. A leader's view is the product as its framework sees it, with its digest and its concerns; written again when a goal closes, when asked and when Orkboard analyses the project; its face chosen on mockups (8 November 2026, the owner)

Why: goal 167's Talk. The leaders found half of it built (a party's journal digest, copied into `journals/<party>.md`) and empty
here, as the brief was never answered and the leaders' skill passes write no journal line. The owner:
1. **A leader's view** is the product as the leader's framework sees it (its hero's places), with its journal's digest and its
   concerns on its map, shown in the window.
2. **It is written again** when a goal closes, when the person asks, and when Orkboard analyses the project by itself.
3. **Its call reads the goal pages and the decisions log**, not only its party's journal.
4. **Its face is chosen on mockups**: two or three, the owner picks one. The use cases talked of in these goals lie on
   Product's table (goal 163).
5. **No phone for now**: the view on the phone is a goal of its own.
6. **In an AI tool's skill, the leader's Accept pass writes it**, in the tree.

The owner's call.

## 283. The window played as a card game's table: two sizes, a goal dealt to its leaders at every stage, a table for every stage and eye, the card in play at the table's foot, a goal's own branch and the discard's two piles, the history book, the inventory as slots, pictures on the cards (9 November 2026, the owner)

Changes: 101 (a task lands in dev), 177.2 (the Orkmaster's line under the pane's title), 181.1 and 181.3 (a quick question), 183.5
(where a concern lies), 198.3 (when the leaders judge again), 199.4 and spec 99 §3 (the night), 206.3, 206.8 (the branches seen),
225.1, 240.1, 241 (the heads in the ring), 247.2 (where a goal put off lies), 251.1–251.4, 251.7, 252.2, 254.8 (the release branch),
254.12a, 261.3, 261.7, 261.9, 261.11, 261.13, 266.2, 266.5, 267.1, 270.1, 270.6, 272.1, 273.2, 273.3, 277.5; CLAUDE.md's *One look*
and *The frame*.

Why: the owner, as designer and product manager, for the desktop alone (the phone is talked of apart): a proposal for the whole
window and for how it should work, talked through point by point with Claude the same day against the decisions, the page as built
(`main` at 9dcf841) and the trials on Codex (specs 143, 149, 155; trials 152, 152-e, 160). What the reading found: the desktop draws
about seventeen card sizes where §270.7 decided two; the hand grows to 214 px while the inventory is open (`hand/carry.css`) and a
form over the pane drops the discard's column (`table/lane.js`); a goal in analysis has an empty table (`docs/mockups/answer-cards/`
found it), since its leaders get cards only at work (§241, §251.7); a goal's spec is written while its card still lies in the fan;
*Stop all* lies in the hand's row, which is inert while a card is lifted; a lifted card never opens the tab of the leader who asks,
and its answers are drawn whole and do not rise; a goal dropped at work leaves its landed tasks in dev; Talk reads no file, so a
doubt is often one search away (trial 152 F6); a result says *ok* where the acceptance said *unseen* (trial 152-e F4); Codex has no
prices, so a task's money cannot be said; and a later party's step is planned only once the step before is accepted. The owner took
every recommendation, and on pictures: *yes, an explicit decision: the window has already turned more of a game (colour is no
longer a signal alone, §268), and now its cards get pictures*. So:

**The frame**
1. **Two card sizes on the desktop, and only two**: the big card, 144 × 202 (the hand, the table, the column's *Implementation*,
   the discard), and the small card, 56 × 78. Every other size goes: the new goal's field and the card opened with more than one
   question (404 × 566), the first open's cards (288 × 403) and its fan, the large + card, the passing card, the stall's wares, the
   carried cards, the deck's backs (112 × 157 on their side). Words a card cannot hold are cut; a choice is split into its question,
   a card on the table, and its ways, cards in the hand (§270).
2. **A scheme's parts are the board, never cards**: a part of a leader's scheme has no 5 : 7 and no four corners, so it is never
   taken for a card, and it keeps its own size (Art's width is its weight, §280.2).
3. **A small card is an index, with no words**: its back is the rune in its ring; its face has the rune in its top left corner as a
   pixel glyph, its shape and its colour (two goals of one colour differ by their shape alone, §206.10), a dot in its bottom left for
   each party in that party's colour (filled when done, hollow when ahead), a signal as the card's own frame (§268.1, §276), and in
   its middle a small picture: what is attached to its goal, else its kind's (a verdict's sign, a concern's aspect, a seat's head).
   This changes §252.2 for the small card, whose words do not fit.
4. **A small card hovered or focused shows itself**: a face-up card as the same card at 144 × 202 beside it, a back as its goal's
   name and its state's line; after about 300 ms, one at a time, put away by Esc, from the column to its right over the table.
5. **Nothing changes size by what is picked or opened**: the column, the table, the discard's column and the hand keep their sizes
   with a goal picked, a card lifted, or the inventory, the history, the launch table or a form open. The carried cards' taller hand
   and the column dropped under a form are bugs.
6. **What lies left and right and is a place changes the table**: a card of the column or of the discard, the die (the launch
   table: Play, as today), the backpack (the inventory), the book (the history). **What is not a place never changes it**: the
   potions, *Stop all* and *Resume*, *Here* and *Away*.
7. **The right column's head holds what does not change the table**: the lamp's chain at its right edge (§271 unchanged), the drum of
   potions left of it, unrolling down over the discard when hovered, and *Stop all* or *Resume* in words under the drum, which can
   be pressed while a card is lifted. **The hand's right end holds the places**: the die, the backpack and the book, about 48 to 56 px
   each, each drawn open while its table is on; they sink with the hand while a card is lifted. This changes §261.11, §261.13,
   §272.1 and §273.3; §266.10 is kept.
8. **The tabs say through whose eyes**: the Orkmaster's tab shows the order of the work between the leaders, a leader's tab its own
   view of what is picked, or of the whole project when nothing is. Nothing picked on the Orkmaster's tab is the project's table,
   the window at rest.
9. **The Orkmaster's news is a balloon**: what it says unasked (the work moved to another tool, the limits running low, what the
   night did, Orkboard mended) rises from its crown over the start of the tabs, at most about 420 px wide, one at a time (a newer one
   replaces it, the older ones go to the Orkmaster's journal), until × or until it is no longer so, a day at most. Its only act is
   *Show*, which picks the goal it is about; it is a polite live region and never takes the focus. A toast stays the answer to a
   press, where it was pressed; a decision stays in the hand (*Go on paid?*). This changes §177.2's line under the pane's title.
10. **One place moves** (§247.8 kept): only the picked goal's cards, its tasks at work as one place; orkUI's working step or a rune's
    glow of 2 s or slower; nothing flashes; nothing moves under reduced motion.

**The Orkmaster's column**
11. **Its piles are the goal's stages** (`TERMS`, the old names in `was`): **Ideas**, the small cards' fan; **Specs**, small cards on
    their side in a squared deck (this replaces §251.3–4's backs of 112 × 157; §236's tuck is kept); **Implementation**, the big
    cards' cascade.
12. **A goal lies where what happens to it next** (this changes §206.3's and §247.2's places): in *Ideas* while the Orkmaster reads
    and routes it, in Talk, and while an agreed decision waits (§241.2's play and ring); in *Specs* while its sections are written
    (§241.3's filling ring moves here), while it is planned and while it waits for the look; in *Implementation* at work. **Held or
    later before Talk**, at the fan's end with a pause or a clock on its back; **held after its spec, or waiting for the night's
    build**, at the cascade's foot (as *At work · later* today); **held at work**, in the cascade with a pause. A failure stays in its
    stage's pile in the danger's ring, and its card is thrown into the hand (§206.7).
13. **The fan is denser and turned like a hand's**: 4 to 6° a card on an arc, 12 to 16 px apart, seven within 160 px, tighter after
    that, never a count. **The column keeps its 160 px**; the project's name in its head takes two lines, then is cut, whole on hover.
14. **One card through a goal's life, led by the Orkmaster** (§198.8 kept), **and at each stage's start the Orkmaster deals every
    leader of the route its card for that stage**: an assessment card at *Ideas*, a section card at *Specs*, a step card at
    *Implementation*, its tasks laid under it when the step is planned. A later party's step is a placeholder until the step before
    it is accepted, since the engine plans it only then. This changes §241 (the heads in the ring) and §251.7 (dealt only at the
    start).

**The tables**
15. **One template**: a header of small cards in groups, held while the table scrolls; a body (the leaders' lanes on the
    Orkmaster's tables, the hero's scheme on a leader's, a grid for the history and the inventory, a log for a seat's work); and the
    table's foot at the left, kept for the card in play (19).
16. **The tables, by the stage picked and the open tab** (§261.4 made whole):
    1. **The Orkmaster's project** (nothing picked): a lane for each leader; in it a row of small cards for the ideas it is
       assessing now, then two cascades, its spec cards and its implementation cards. A card pressed picks its goal and opens that
       leader's table for that stage.
    2. **A leader's project**: its header in three groups: **at work** (its ideas and specs face down, its implementation face up,
       as in the column; pressed, the goal is picked and this leader's table for its stage opens), **concerns** (face down, with the
       rune of the goal it is about, or a + for a new one; pressed, it is lifted: *Not a problem*, *Later*, *Make it a goal*), and
       **ask** (a small ? card with a hand that takes parts of the scheme: 20). Under the header, the hero's scheme in its board
       game's shape (§280), its concerns marked on their parts as well.
    3. **An idea, through the Orkmaster**: a small card under each leader of the route, face down while it assesses, face up with
       its verdict once done (✓ go, ! doubt, ✗ no); Product's weighing is a card in Product's lane when Product is off the route.
       Pressed, the next table.
    4. **An idea, through a leader**: three rows of big cards: **its verdict** (its picture, how far it agrees); **needs your
       answer** (at most three: a risk, a conflict with a goal or a decision, a question, each with what it rests on and its ways);
       **could be better** (at most three improvements, each a line of the idea rewritten, said to be lighter, the same or heavier).
       Each is lifted and answered as any question (19).
    5. **A spec, through the Orkmaster**: a big card under each leader of the route, face up once its section is written, face
       down while it is being written. Pressed, the next table.
    6. **A spec, through a leader**: its header holds the small cards of its steps as fans, with their seats' heads and tools; **a
       seat whose tool cannot do what its step needs is marked !** (a browser for its tests, git's index, the network, a command
       not on the path: what trials 149, 152-e and 160 hit). Under the header, the parts of its scheme the spec changes, enlarged,
       **now and as they will be**: what is new as a ghost, what changes outlined, what goes struck through, and Design's sketch
       where one was made.
    7. **The implementation, through the Orkmaster**: the work from top to bottom, a lane for each leader, its task cards with
       arrows between them, a later step as a placeholder. Pressed, the next table.
    8. **The implementation, through a leader**: its header is its party (heads, tools) with an edit mark that opens its inventory;
       its lanes are **its seats**: those who make, those who check, and its acceptance, with the arrows task → check →
       acceptance → the tasks sent back (four at most, two rounds, §256). Pressed, a seat's work.
    9. **A seat's work**: its header holds its head, its tier and its tool, with an edit mark to the leader's inventory; its body is
       the session's log, read only, in a terminal's face, its tail live, its steps over it (§207), the values of the goal's secrets
       masked. A task run in the person's own AI tool (a skill, §258) says so instead.
    10. **The result, through the Orkmaster**: what the spec planned against what was built, a lane for each leader, each
        leader's problems lit.
    11. **The result, through a leader**: planned against built on its scheme, **before and after** where the code keeps both
        (Tech's System by commit, Design's screens' shots), elsewhere the parts touched; every error of the goal's work (a try that
        failed, a red gate, a step sent back, a finding).
    12. **The Orkmaster's inventory** (30–32).
    13. **A leader's inventory** (30, 33).
    14. **The project's history**: a grid of goal cards that scrolls, a row a day, a day's many cards as a cascade lying across;
        dated by when they were **agreed** (by default), **done** or **in main**, a switch in its header; a version's plate on the
        day it was released; **a search** over the titles, the gists and the decisions, the cards found lit and the rest dim.
        Pressed, the Orkmaster's result.
    15. **A leader's history**: the same, with the goals its party worked on. Pressed, its result.
    16. **The launch table**: Play, as today (the word is new).
17. **A card's bottom right is one figure, with its unit beside it** (this changes §251.2's *time*): **the share of its tool's
    window** where that can be measured, else **tokens**, and money only where a price is known (Codex has none); at work, what it
    has spent so far; done, what it spent in all; ahead, **≈** its party's average for its kind. The time is in its preview.
18. **The verdicts by their signs**: ✓ in the success colour, with no ring; ! and ✗ in the ink; red only for a call that failed;
    the alert's ring only where a question waits for the person.

**Asking and answering**
19. **The card in play lies at the table's foot, at its left**: a question, a failure, a concern or a conflict, lifted, rises there
    at 144 × 202 and leaves room over the hand for its answers; **its goal is picked in the column and the asking leader's tab
    opens** (the Orkmaster's, for its own question). This changes §261.3 for a lifted card and §270.1's place. Its answers are the
    hand: cut by the rim and rising when hovered (§270.2, not so today), the rest of the hand sunk.
20. **A new goal is that card**: the + card stays in the hand; pressed, a card of 144 × 202 rises at the table's foot, its words
    written in a field beside it on the table, and its corners' choices (its rune; its kind, **?** among them; who; *Now* or
    *Later*) are dealt to the hand. This changes §270.6's place. **A quick question is the card of the kind ?**: it goes through the
    Orkmaster to whoever knows (the open tab's leader; on the Orkmaster's tab the Orkmaster itself, or one hop), one call on the
    cheaper tier, no file, no rune, no place in the column, and **comes back as a card in the hand**: its answer on the table, its
    ways *Make it a goal*, *Ask more* and *Got it*. It is kept in the leader's journal (`asked`) and not shown. This changes §181.1
    and §181.3; §181.4–7 are kept.
21. **A concern at the alert's level is also in the hand**, one stack for each leader under its lane; the card in the hand, the one
    in the header and the mark on the scheme are one thing: one hovered or picked lights the others, and it is answered once. A
    note stays on the scheme and in the header. *Later* lays it face down in the header, out of the hand, until the leader's next
    look finds it again. This changes §183.5.
22. **A leader that decides by itself says so with a card that can be overruled**: muted (no alert's ring; its head; a sign of
    *decided*), its ways *Accepted* (as it stands) and *Replay* (back as a question with its ways); it leaves the hand by itself
    when its goal moves to its next stage. Never for §266.5's locks (going into main, money above what was agreed, dropping or
    holding a goal, a decision against an earlier one). This changes §240.1 for this card and §266.5's *in its evening line*.

**An idea's assessment**
23. **A leader's say in Talk** (`seat_talk_rules`): its verdict; at most three things that need an answer, each with what it rests
    on (a goal, a §, a part) and at most three ways, each way with its kind (34); at most three improvements, each a line of the
    idea rewritten, lighter, the same or heavier. **Code gives it what code knows**: the goals in the pile the idea looks like
    (§242), the decisions' slices (§233), the goals in line, its map's text. It reads no file, and a doubt code can settle is
    grounded (spec 155 D). About a minute of the machine's time, the person's answers and the agreed wait aside.
24. **The Orkmaster rewrites the idea** with what the person took, shown as a change to the person's own words (the Gist and its
    *Added:* lines) and undone by a press; improvements taken that contradict each other come back as one fork.
25. **The leaders judge again once all their cards are answered**, or at *Judge again now* on the Orkmaster's table of the idea:
    those that doubted or said no, whose proposal was turned down, or whose part the rewrite touches (§198.3); twice at most, then
    a hearing. No timer, except for a leader whose way of answering is a Choice with a wait (§266.5).

**A goal's branch, the discard, main**
26. **A goal's code has a branch of its own** (`goal/<slug>`; its tasks' branches stay `idea/<slug>/<task>`): its tasks land there
    (this changes §101's *in dev*), a later party's step starts from it, dev is merged into it as each step starts, and **it goes
    into dev once**, when its last step is accepted and the gate is green on dev with it. The Board's pages (the goal, its spec,
    the journals) land where the Board lives, as today: a page on another branch is not seen (trial 160 F1). **A goal dropped
    before dev loses its branch, and nothing is reverted.**
27. **The discard is two piles**, through the open tab's eyes: **the lower one, done on its branch and waiting for dev**, drawn only
    while *Lands in dev by itself* (today's `review`) is off; **the upper one, in dev and waiting for main**. Over each pile, **its
    branch's plate** (*dev*, *main*); pressed, the branches are dealt to the hand: for the lower pile any branch or a new one from
    dev, for the upper main or dev; a card warns first when goals are at work; `orkboard/*`, `goal/*` and `idea/*` are never
    offered. It is the project's setting (`merge_into`, the release branch; this changes §254.8's *chosen at the first open* and
    §206.8's *dev and main only*), never a view.
28. **To main** is a card's act, the goals it takes along lit (`goal_main.plan`), or the upper pile's: the gate's main tests run, a
    red one is named, and *To main without the tests* is in the card's menu (§274.3); its cards dissolve into the portal's ring of
    runes (nothing moves under reduced motion). **The past leaves the discard for the history book** (16.14; this changes §261.9
    and §277.5's place; §277's dates are kept).
29. **Release and Live wait**: their chairs are not offered; a Release already seated keeps its page, with no tab and its checks
    off; the versions are read from the tags and the changelog. This changes §261.7 and §273.2.

**The inventory**
30. **Both inventories work one way** (this changes §267.1's stall): a row of slots on the table, each showing its chosen way as a
    big card, with its label over it (what the setting is), its picture and what it does, the pips of its ways, and a mark when a
    cheaper way exists. Pressed, its ways are dealt to the hand, each with what it does and its price in its bottom right (what it
    changes in the share of the week), the Orkmaster's pick starred, *Yours* and *Yours before* marked; *Default* is a way among
    them; *Undo* is on the table's line.
31. **The Orkmaster's slots** (this changes §266.2 and §225.1's two settings): **How deep** (`target`: the default of the leaders'
    tiers); **The build starts** (*at once*, *in 30 min*, *in 2 h*, *tonight*, *by hand*: `autostart` and `look_wait` as one);
    **The night** (32); **Lands in dev by itself** (`review`); **Push** (*no*, *main only*, *dev and main*); **Goals at once**
    (`max_parallel`). The hours belong to the lamp's chain (a long pull); the reserves stay in Settings.
32. **The night is a ladder** (this changes §199.4 and spec 99 §3's *the night is gone*): *Off*; *Ideas and specs* (Talk and the
    specs of the goals in line, nothing built); *and the builds* of the goals agreed (today's `work_at_night`); *and the leaders'
    proposals*, the leaders picked as cards in the hand: one for each leader and three a night at most, each taken to a ready spec
    at most and never built without a press, in the morning in *Specs* marked *proposed* with a card in the hand, *Take* or
    *Drop*, all within the night's reserve. The night's window is chosen on its card.
33. **A leader's slots**: **its hero** (shown with no choice where its craft has one, §278.1); **its AI tool**; **its tier**, for
    its own calls (Talk, its section, its acceptance), over *How deep*'s default; **its party's size** (*lean*, *standard*,
    *full*: its seats' cells and how many work at once; no longer a Target of its own, as `realm/idea_target.py` has it); **how it
    answers**: *Pen* (your words, each time), *Choice* (its ways), *Fork* (its ways worked out, with their gains, costs and risks,
    drawn where it can, one more call a question at the elder tier, its price on the card), *Silent* (it decides: 22), with
    §266.5's locks kept. Under them, **its seats' grid**: each seat's head and name, its tool and its tier as small cards. The
    engine of the ways of answering (§267.5's *later*) is built with these slots.

**Pictures**
34. **Cards carry pictures** (this changes §252.2's *no picture for its own sake* and CLAUDE.md's *One look*): a way's kind
    (`way_kind`, about twelve, returned by every call that offers ways), an inventory's way, a question's kind where orkUI's signs
    do not say it; the heroes and the races as drawn. An idea's window keeps what is attached to it, and a task's what it made
    (§252.2 kept).
35. **Made with Gemini, laid on orkUI's grid in its palette** (its greys and the element's colour), taken into orkUI and copied,
    with a line in `NOTICE`; each in two sizes, a big card's window and a small card's middle. **A picture never carries the
    meaning alone**: the way's line stays under it, in the body face.
36. **Measured**: the time to answer and how often *Put it back* is pressed, in the owner's week (§262.3).

**The words** (`TERMS`, with each part's spec): *Ideas*, *Specs*, *Implementation* (*In analysis*, *To review*, *At work · later*
in `was`); the tables' names; *the launch table*; *History*; *Judge again now*; *Ask more*, *Got it*; *Accepted*, *Replay*;
*Lands in dev by itself*; *The build starts*; *The night*; *proposed*; *Take*, *Drop*.

**Not now**: the phone and the window under 760 px, each a goal of its own; Release's and Live's tabs; a branch chosen for a single
goal; the log read as the tool's events rather than its text; the lich's seal at *To main*.

**Built** by goals, in this order, each spec written by its leaders: **A.** the frame (1–10: the two sizes, the small card's face,
the preview, the geometry, the right column, the balloon), orkUI first (the small face, the book, the drum at the column's head);
**B.** the column (11–14); **C.** the idea, spec and implementation tables with the assessment's engine (16.1, 16.3–16.8, 17, 18,
23–25); **D.** asking and answering (19–22); **E.** the leader's project (16.2); **F.** the goal's branch and the discard (26–29);
**G.** honest results first (a Done when line is *ok* only where the acceptance said *met*, *unseen* says *not checked*, a craft
whose map has no file touch says *landed, not compared*, a finding told reaches the hand: trials 152-e F4, 160 F4), then the result
tables and the history (16.10, 16.11, 16.14, 16.15); **H.** the inventory (30–33); **I.** a seat's work (16.9); **J.** the pictures
(34–36), their list made once 23's ways have their kinds. **Drawn first**: `docs/mockups/table-template/`, the template with the
Orkmaster's project, an idea through the Orkmaster and through a leader, and the right column; the owner's pick.

The owner's call.

## 284. The table's template as the owner picked it: an idea through a leader in one row, the small card's first face, the potions in a row again, Stop all the die's word, the places of one size (9 November 2026, the owner)

Changes: 283.7 (the right column's head and the hand's right end), 283.16.4 (three rows); 261.13 (the drum), 266.10 (Stop all
above the potions); 261.12 is taken again.

Why: the owner, on the mockup §283 asked to be drawn first (`docs/mockups/table-template/`): an idea through a leader in three
rows does not fit a 1366 × 768 window (its third row falls under the hand, shot 6), while one row of three groups fits with room
to spare (shot 5); and with the drum, *Stop all* and the chain in the right column's head, the discard's lower pile was cut. The
owner: *one row; the first face; let us leave the drum and go back to a row of bottles, now there is room, so the chain and its
words can move further right; the die, the inventory and the history of one size; and Stop all down, so there is more room up
top for the discard*. So:
1. **An idea through a leader is one row of three groups** (this changes §283.16.4's three rows): its verdict; *needs your
   answer*; *could be better*, each group's cards side by side, at most three a group; the table scrolls only past that.
2. **The small card's face is the first one**: the rune in its top left corner, the dots of its parties in its bottom left, its
   picture in its middle (§283.3); no kind's pip.
3. **The potions stand in a row again** at the right column's head (this changes §283.7 and §261.13's drum): a bottle for each AI
   tool, its size the week and its liquid the 5 hours (§192), its share now under it (§247.3), a tool at the warn or the danger
   level in that level's colour with its words (*out*, §262.1); the tool the open tab's work goes to is the one whose share is
   said in the ink. **Three at most stand in the row**: the one the work goes to now, then any at the warn or the danger level,
   then the person's order; hovered or focused, the row shows them all with *back 14:00* and the empty slot at its end (§232.4).
   Nothing the person does reorders it. **The lamp's chain stands at the head's right edge**, its words beside it (§271.1).
4. **Stop all is the die's word again** (§261.12 taken again; this changes §266.10 and §283.7): under the die, *Stop all* while
   the orks work, *Resume* after it, else nothing (the die is Play's). **It stays lit and can be pressed while a card is lifted**,
   when the rest of the hand and the places sink (§270.3): the one thing in the hand that never sinks, since it is safety.
5. **The places are of one size**: the die, the backpack and the book each stand in a box of 48 × 60 at the hand's right end, the
   die at orkUI's `.small`, the backpack at 3 px a cell, the book drawn in orkUI at the same; each with its word under it but the
   die, whose word is 4's.
6. The mockup shows it (`docs/mockups/table-template/`, its shots made again).

The owner's call.

## 285. The right column's head as the owner drew it: the potions' tops on one line and the week said under a smaller bottle; the chain half as tall, Stop all under it; the places only what changes the table, the history a book (9 November 2026, the owner)

Changes: 284.3 (the potions' words), 284.4 (Stop all the die's word), 284.5 (the die's word); 283.7's *Stop all* at the head is
taken again; 247.3 (the week's words only while the week runs out first) for the row.

Why: the owner, on §284's mockup: *three bottles at most in a row, aligned at the top, so their tops are one line: under the large
bottle no "Week", only the percent; the smaller a bottle gets, the more room under it, so "Week" and the week's percent can stand
there. The chain and "Here" half as tall, about half the large bottle, and Stop all under them; then the three below, the die, the
history and the inventory, stay only for changing the table, with "Play" under the die, all three one size; and the history a book,
not a scroll*. A bottle's size is the week's share (§192), and its meaning was the row's hardest thing to read (§247): said under
the bottles that have shrunk, the week explains their size where it matters, and nowhere else. So:
1. **The potions' tops are on one line** (three at most, chosen as §284.3 says): under each its 5 hours' share (*62%*, *out*);
   **under a bottle smaller than the large, the week's share as well** (*week*, *30%*), in the room its smaller size leaves; the
   large bottle says the 5 hours alone. This changes §247.3 for the row: the week is said wherever its bottle has shrunk.
2. **The lamp's chain is half as tall** (orkUI's `.small`, 6 × 29), at the head's right edge, *Here* or *Away* and its hours beside
   it (§271), and **Stop all stands under it** (*Resume* after it; nothing while no ork works; this takes §283.7's place again and
   changes §284.4). In the right column, not the hand, it never sinks while a card is lifted.
3. **The hand's right end holds only what changes the table**, the three at one size: the die with *Play* under it (this changes
   §284.4–5), the backpack, and **the history drawn as a book**, shut and open as the backpack is, drawn in orkUI.
4. The mockup shows it (`docs/mockups/table-template/`, its shots made again).

The owner's call.

## 286. Words are written in the hand's place: the card at the table's foot at the left, the field as large as the hand at its right (9 November 2026, the owner)

Changes: 283.20 (the new goal's field beside its card on the table), 270.2 (the Pen's field on the table beside the question).

Why: the owner, on spec 168's D: *the text field could stand in place of the hand's cards: at the left the new goal's card, at
the right a text field the size of the hand*. While the person writes, the hand holds nothing to play: its cards would only
sink; a field as large as the hand gives the words the room of five lines without covering the table, which stays the
context (§270.4), and nothing changes size (§283.5). So:
1. **Whenever the person writes words, the field takes the hand's place**: the hand's cards sink as for a lifted card (§270.3),
   and **a field as large as the hand** (its height, from the column's right edge to the places) lies where they lay, focused at
   once. **Its card stands whole at the table's foot, at its left** (§283.19's place), so all four of its corners show and can be
   pressed. It holds for **a new goal** (the + card pressed: §283.20), **a quick question** (the card of the kind **?**) and
   **the Pen** (*Your own words…* on a lifted card).
2. **A corner pressed deals its choices to the hand in the field's place** (the rune, the kind, who, *Now* or *Later*); one
   played, the field comes back with its words as they were.
3. **Enter sends** (Shift+Enter a new line); **Esc** lays the card back and keeps its words as a draft; a picture or a file
   dropped on the field is attached, and the card's window shows it (§252.4).
4. Built by spec 168 D1 and D2.

The owner's call.

## 287. The cards' pictures as the owner's first sheet drew them: a way's card read picture first, the pictures in the heads' colours, a wide tile on one table edge (9 November 2026, the owner)

Changes: 283.35 (the palette and the two sizes), 252.3 (the window below the hand's cut, for a way's card).

Why: the owner's first sheet of pictures (`docs/pictures-wanted.md`, sheet 1), made in Gemini in three takes and laid on the
mockup's cards (`docs/mockups/table-template/`, shots 10–12): the pictures say most when they are seen at rest in the hand, they
are drawn in the colours of the leaders' heads they stand beside, and the third take's wide tiles on one wooden table edge read as
one set and fill a way's window exactly. The owner: *yes*. So:
1. **A way's card is read picture first**: its corners, its picture, then its name and its line; so in the hand, cut by the rim,
   it shows its picture and the first words of its name at rest, and a way is told before it is read. Every other card keeps its
   window under its title (§252).
2. **The pictures are drawn in the leaders' heads' colours** (orkUI's races), muted and earthy, with no large area of a signal's
   colour (the alert's yellow, the danger's red, the action's green) and no rainbow; the card's frame carries the element's colour.
   This changes §283.35's *its greys and the element's colour*.
3. **A tile is wide, about 1.9 : 1**, the window of a way's card (130 × 68); **every object stands on one wooden table edge** along
   its foot, one object and at most one small joke, filling about 70% of the tile's height, a black outline, light from the top
   left, no text. A way lives only on a big card, so it has one size; a small card's middle keeps its kind's sign, a head or what
   is attached (§283.3). A human hand in a picture is the person's act; the orks' own act is an ork's green hand.
4. **The sheets keep to the first**: the approved sheet is attached to every later prompt beside the heads, and `docs/pictures-
   wanted.md` says the rules. Spec 168 J2 builds the place for them.

The owner's call.

## 288. The heads everywhere are the owner's set: drawn in Gemini, fitted to orkUI's sizes; the tiers' gear laid by code; every hero its own portrait; five moods each (9 November 2026, the owner)

Changes: 266.4 (a hero's face its race's higher form with a few things changed: now a portrait of its own), 287 (the pictures were
the cards'; the heads are now the owner's too); orkUI's `races/` (the 12 × 11 grids written by `tools/build_races.py`, after §161).

Why: the owner's set of eight heads (the shaman, the dryad, the unicorn knight, the lich, the imp, the gnome fairy, the Orkmaster, a
Grunt), made in Gemini in the party colours, beside orkUI's at the window's sizes (`docs/mockups/table-template/heads/compare.png`):
richer and told apart at 48 and 36 px, darker at 16 px. Offered the new heads as portraits and orkUI's as the 16 px icons, the owner:
*no, the new heads everywhere*; then, of the ways offered, the tiers' gear laid by code, a portrait of its own for every hero, and
five moods each made in Gemini. So:
1. **Every head the window draws is the owner's set**, at every size (16, 24, 36, 48 px): the leaders, the crowned Orkmaster, each
   race's member, every hero. orkUI keeps its file names and sizes (`races/<race>-<tier>[-<mood>].png` at 24 × 22 and `@2x` at
   48 × 44, `hero-<id>-<tier>[-<mood>]`), so Orkboard's code changes nothing; what changes is how orkUI makes them.
2. **A head is drawn once, bare**, in Gemini, on a tile of 12 : 11, front-facing, every head the same height and its eyes on one
   line, whole inside its tile, in its party's colours (§268), on a flat grey to be cut out; orkUI cuts it, lays it on that line,
   brings it to 48 × 44 and 24 × 22 and to its palette.
3. **A tier is its gear laid by code** over the bare head (the hood, the band, the circlet: the gear the 12 × 11 heads wear), at
   the line every head shares; a mark (horns, antlers, wings) is never covered by more than a cell or two of it.
4. **Every hero is a portrait of its own**: its leader's race and party colours with what its school says (a detail, a colour of
   its helm or hair), drawn in Gemini as the leaders are; its tiers by 3, its moods by 5.
5. **The leaders, the Orkmaster and every hero have five moods** (focused, worried, no, pleased, asleep), each made in Gemini from
   its calm face, kept as one face; the members keep one face (as today, §201's states are the leaders').
6. **The sheets** are in `docs/pictures-wanted.md` (*The heads*); orkUI takes them in by a tool of its own and releases them; spec
   168 J3 builds it. Until a head is made, orkUI's 12 × 11 head stands for it.

The owner's call.

## 289. The look's pictures are a humorous flat cartoon, not pixels: the heads first (9 November 2026, the owner)

Changes: 288.2 (a head drawn in pixels and brought to orkUI's palette: now a flat cartoon, kept smooth), 283.34–36 and 287 (the
cards' pictures in the heads' pixel manner: now the cartoon), 268 (one look: its pictures are the cartoon; colour is still the
party, the element and a signal); orkUI's `races/` and `pictures/`.

Why: the owner, weighing a redraw against the pixel heads just taken in (§288), was offered two looks, a humorous flat cartoon and
a muted storybook illustration, and took the cartoon from a sheet of six leaders (`docs/mockups/table-template/heads/cartoon/`).
Seen at the window's sizes beside the pixel heads (`compare-phone-dpr3.png`, `compare-desktop-dpr1-x3.png`): on a phone (DPR 3)
it is sharper and says more at every size, 16 px included, where the pixels are blocks; its eyes carry the five moods (§288.5) as a
12 × 11 grid could not; its tone is the product's (orks, a card game's humour). Against it: at DPR 1 a 16 px cartoon head blurs, and
the lich's dark hood is lost on the dark room.

1. **The look's pictures are a humorous flat cartoon** (the owner's call): thick even dark outlines, flat colours with one shade,
   big expressive eyes, comic proportions; drawn in Gemini as before, described by these traits and never by a show's name, and
   never a show's own characters or manner copied.

How, as proposed with it from the comparison (the owner may change any of it):
2. **The order**: the heads (the leaders, the crowned Orkmaster, the members, the heroes, the tiers' gear, the moods) first; then
   the cards' pictures (§287's sheets again); then the objects (the potions, the die, the backpack, the book, the chair, the
   backs). The signs, the runes and the pixel face of the headings and buttons stay as they are until the heads and pictures are
   seen together in the window, and are decided then. Until a picture is redrawn, today's stands.
3. **A head is kept smooth** (no pixel grid, no palette cut, soft edges): orkUI writes today's names and sizes, and `@3x` for
   phones; **a 16 px head is its own simpler drawing** (the face, the eyes, the mark, a thicker outline), not the big one shrunk.
4. **Every head reads on the dark room**: no dark hood or dark helm without a light rim; its party's colour carries it.
5. **§288's way holds**: a head drawn bare (no hood, no cap, no hat: the tiers' gear is laid by code), the heroes' own portraits,
   five moods each, the sheets taken in by orkUI's tool (`races/art/sheets.json`), re-run for every new take.

## 290. The beta's pictures: the cartoon heads now, the cards' pictures pixel until the phone (10 November 2026, the owner)

Changes: 289.2 (the order: the heads, then the cards' pictures, then the objects: the cards' pictures and the objects wait for the
phone), 288.3 (a tier's gear taken from the tiers' sheets: now laid by code from the leaders' gear in sheet K3), 288.5 (five moods
for every head and every hero: the heroes' moods wait until after the beta); `docs/pictures-wanted.md`'s pixel head sheets (H2, T2,
H3, H4, H7–H11, the T1 and H5 fixes) are dropped.

Why: the owner, with the cartoon sheets made in Gemini (K1 the bare eight, K2 the eight at 16 px, K3 the leaders' tiers, K4 the
members, K6 the eighteen heroes, and one sheet of eight heads in five moods each in place of K7 and K8) and the pixel card pictures
(sheets 1 to 4, the fourth in two takes), weighed what the beta needs: the window should not be drawn half in one look and half in
another, and the cards' pictures, redrawn, are best seen where the work is done. So:
1. **The heads are the cartoon in the beta**, all at once: the leaders, the members, the Orkmaster, the heroes and the moods, never
   cartoon and pixel heads side by side. orkUI's pixel heads (0.38.0) stay until orkUI takes the cartoon heads in; the cut is made
   as a mockup (`docs/mockups/table-template/heads/cartoon/`), then orkUI's own tool (`races/art/`, spec 168 J3), then copied here.
2. **The cards' pictures stay pixel for the beta** (sheets 1 to 4 of `docs/pictures-wanted.md`; spec 168 J2 takes them). They are
   redrawn in the cartoon later (P1–P4, then the objects O1–O6 of `docs/pictures-cartoon.md`), when the work moves to the phone, then
   on the desktop too.
3. **No more sheets for the beta.** The members' tiers are laid by code from the leaders' gear in K3 (the Grunt from the shaman, the
   elf from the dryad, the goblin from the imp, the gnome from the gnome fairy, the skeleton from the lich, the knight member from
   the knight's plume); the frames a head crosses (the dryad's antlers) and the "z" letters drawn in the asleep bubbles are fixed by
   code when cutting; K5 is not made.
4. **After the beta**: the heroes' moods (K9–K13; a hero shows its calm face, its state beside it as today) and K6's small faults
   (the six hero knights lost their small wings, Spike Shaman's horns are not ram's horns). The Orkmaster's focused and no moods
   are close.
5. **A lesson for every sheet**: a sheet's whole image stays near square or at most 2 : 1; Gemini squashes the tiles of a wider
   grid (sheet 4's tiles 1–4 and K4 were drawn again as a 2 × 2 and a 3 × 2 grid).

The owner's call.

## 291. The look reads: Rubik, the colours a step lifted, round corners; the phone is a feed of blocks, what waits first, a deck only where it says something (10 November 2026, the owner)

Changes: 268 (one look: its type is Rubik, its corners round), 289.2 (the pixel face of the headings and the buttons, left to be
decided with the pictures: decided now, it goes; the signs and the runes still wait for the pictures), 223.1 and 223.2 (the
project's and a goal's screen on a phone: the tabs become one feed), 226.2 (the phone's sizes kept, now in Rubik); spec 40; the
CLAUDE.md line *The pixel face is for headings and buttons* is changed with the spec that builds this.

Why: the owner, the pictures leaving pixels for the cartoon (§289), asked whether the fonts, the colours and the cards' shape could
change for reading, on a phone above all. Three looks were laid over the table's template and the phone's hand
(`docs/mockups/readable-look/`: A Rubik, B Unbounded with Onest, C Alegreya SC with Alegreya Sans), with today's beside them and a
specimen in Latin and Cyrillic: Pixelify's Cyrillic read worst of all (*Пусть* as *Пуcтb*), C's old-style figures and small caps
read worst for the numbers; the owner liked Rubik best. Then the owner proposed the phone's tables broken into blocks and scrolled
as a social feed (`docs/mockups/phone/feed.html` v1), and weighed blocks cut at the foot and laid over each other as cards (its
screen 5) against a deck only where it says something (screen 6); the owner agreed with screen 6 and answered v1's three
questions (v2 draws the answers). So:
1. **The type is Rubik** (SIL OFL 1.1), for the headings, the buttons and the text, 400 to 800; **the pixel face goes** from the
   headings and the buttons; IBM Plex Mono stays for code, paths and ids. On the desktop the body is 15 px, a caption 13, nothing
   under 12; on a phone §226.2–226.3 hold (body 17, captions 15, labels 14, nothing under 14). A card's name is in the heading face.
   Today's sheets' own 10–11 px (`orkboard/gui/static`) come to the type tokens.
2. **The colours a step lifted, the same warm room**: a card `#33373a` (its frame `#4c5257`), the panel `#1f1d1a`, raised
   `#2e2b27`, the frame `#45423b`, the ink `#ebe7e0`, read `#d6d2ca`, muted `#bbb6ad`, faint `#a8a39a` (measured in the mockup's
   README); the parties', the elements' and the signals' colours stay (§268). §226.2's phone edges on `edge` hold.
3. **The corners are round**: orkUI's notch becomes a round corner, a card 10 px, a button and a chip 6 px, a picture's place
   inside a card 4–6 px; a card's top edge a faint light line.
4. **Made in orkUI first** (CLAUDE.md, *The design system is orkUI*): the fonts, the tokens and the corners are orkUI's, then
   copied; Orkboard's sheets still carry no colour, font or corner of their own. The mockup's fonts stay the mockup's.
5. **The phone is one feed** in place of §223's tabs, on the project's screen and, one level down, on a goal's: **the Orkmaster
   and the leaders as a row of heads on top** (a goal's: its route's), as a feed's stories; under it **one feed of blocks**, each a
   post from the one who says it (its head, its name, when), a block's own cards swiped sideways; **the hand at the foot as
   today** (§223.6), the questions in it, never in the feed. A block carries only the acts it had where it was (*Change the spec*,
   *Start now*, *To main*). Scrolled, the heads go and the header folds to one thin row.
6. **What waits for you first, then the news**, newest first (the owner's answer 1): the specs that start by themselves at a
   clock time, the goals done and waiting for main, then each leader's news since your last look.
7. **A head pressed narrows the feed to it** (the owner's answer 2): its news, its concerns, its map made small (§223.1's lens),
   the other heads faint; pressed again, the whole feed.
8. **A deck only where it says something** (screen 6; screen 5's blocks cut and laid over each other are not taken: every block
   would need a tap to be read, a cut block's acts would go under the next, and a pile is what the hand and the Orkmaster's piles
   already are): a block is read whole; **one leader's posts in a row are one stack**, the edges of the rest under its card,
   *More from <leader>* opens them; **what you have seen is one line** under *You have seen everything since <time>* (the owner's
   answer 3), its heads small, and pressed it spreads as a deck, each card's head showing.
9. **No count**: a head's ring says it has news, a yellow ring with **!** that it asks; never a number (§67, §223). The ring is
   never alone (§226.3): a sign beside it says the news, as the ! says the asking; the mockup's 12 px names under the heads are
   14 px when built.
10. **A goal of its own** carries it (`llm-wiki/general/pages/ideas/`), Design's party: the look in orkUI first, then the phone's
    feed.

The owner's call.

## 292. On a phone the die, the backpack and the book are under one round button; the lamp's chain hangs from the header (10 November 2026, the owner)

Changes: 223.6 and 291.5 (the foot on a phone: *the + card at the left, the hand, the die at the right*; the die is now under
the round button), 275.3 (the lamp and the backpack drawn on the phone too: where they stand on it), 285 (the places on a phone).
The desktop is unchanged: its places stay at the hand's right end, its chain in the discard's head (§273, §285).

Why: the owner, looking at the phone's feed (`docs/mockups/phone/feed.html` v2) and the objects' cartoon takes: the book, the
backpack and the die are hidden under a round button (a FAB, a selector) on a phone, and the chain is put in the header. So:
1. **One round button at the foot's right**, where the die stood; **its face is the die** in its state (§223.7: faint, white, or
   in the goal's rune), so the die's signal is never hidden. Pressed, it opens **a selector of three**, rising over the foot, each
   a picture and its word: **Play** (the die), **Inventory** (the backpack), **History** (the book); a second press or a tap
   outside closes it. Each opens what it opens today; Play still says plainly what it starts (§223.7).
2. **The + card stays at the foot's left**, the hand between them, as §223.6.
3. **The lamp's chain hangs from the header**, at its right beside the bottle: short at rest, pulled it says *Here* or *Away*
   (§271); what Here and Away do is unchanged (§246.4–5). It stays when the header folds on scroll (§291.5). *Stop all* stays in
   the header.
4. **No count** on the button (§223, §291.9); the selector's three are 44 px at least and each has its word, never a picture alone.
5. The objects are the cartoon takes of `docs/pictures-cartoon.md` (O2b, O3a, O4) when the phone's pictures are redrawn (§290.2);
   until then today's pictures stand.

The owner's call.

## 293. The desktop in the feed's look: every card a post, the Orkmaster's lane and the discard as drawn (10 November 2026, the owner)

Changes: 291 (the feed was the phone's: its look comes to the desktop's cards), 206 (the Orkmaster's lane: its parts as drawn), 273
and 285 (the discard's head and piles: as drawn), 290.2 and 292.5 (the places' pictures: the cartoon takes O2b, O3a, O4 now, on
both faces). The frame is unchanged (§104.0, §145, §273, §285): the leaders' tabs over the table, the Orkmaster's lane first and
pinned, the hand under the lanes with the places at its right, the discard beside the table in two piles.

Why: the owner, looking at the desktop drawn in the phone feed's look (`docs/mockups/desktop-look/`): *the style is liked, the left
column and the right discard above all*; the desktop's adaptation is taken into work on simpler models. So:
1. **Every card on the desktop is a post** as on the phone (§291.5): round (orkUI's card radius), the lifted card ground, its party's
   colour as its top edge, its head row the leader's round head, its name in the heading face, *when* under it, *···* at its right;
   a card that asks is ringed in the alert's yellow; a card's own acts only (*Change the spec*, *Start now*, *To main*).
2. **The Orkmaster's lane, as drawn**: *Waits for you* first (a spec that starts by itself at a clock time, its clock row, its bar and
   its acts), then *Goals* (the fan, *Being read: <goal>*), then *At work* (each goal at work as a post with its live bar in its
   party's colour). Whole cards, pinned, never a list (§206).
3. **A leader's lane**: what it asks first, then *New since your last look · <time>*, newest first; one leader's posts in a row one
   stack with *More from <leader>*; what was seen one line (*Seen since <when>*, its heads small), pressed it spreads (§291.8).
4. **The discard, as drawn**: under its head (the potions, *Stop all*, the lamp's chain at the right edge lit *Here*), the plate
   *main* (*done in dev · waits for main*) over its cards, the one ready for main ringed by the portal with *To main*; then the plate
   *dev* (*done · waits for dev*) over its cards; each card a post.
5. **The leaders' tabs as rings**: a tab's head ringed in its party's colour, a dot in that colour beside it for news, a yellow **!**
   when it asks; its name and its line under it (§275); never a number.
6. **The places**: the die, the backpack and the book in the cartoon takes (`docs/pictures-cartoon.md` O2b, O3a, O4; the chain O4),
   with their words; the die lit when something can be run (§223.7).
7. On the desktop's sizes (§291.1: body 15, caption 13, nothing under 12); orkUI's tokens only; made by a goal of its own, its
   implementation on simpler models.

The owner's call.
