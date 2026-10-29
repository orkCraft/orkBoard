# Decisions §45–§50: Orkboard's ground

Copied on 18 October 2026 from Orkline's `docs/design/decisions-2026-10.md` (orkWorks/orkLine, `main` at 163fea1f),
sections 45 to 50 as they stood when Orkboard moved to its own repository (docs/specs/37-board-and-line.md §9). They say
why the four windows — the Board with its goals, the preview, Agents and Review — became a tool of their own, and how
Orkline goes on from it. Orkline's file stays the record of the decisions before §45 and goes on after §50; the links
below that name `docs/design/…`, `docs/specs/…` (other than specs 33–37) or Orkline's code point into that repository.
A decision taken here from now on is added at the end of this file, numbered on from §50.

## 45. v1 is three buildings in plain windows; Camp waits, its art goes on (17 October, the owner)

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

## 46. v1 round 2: goals and ideas by dialog, straight to the model; agents by task type (17 October, the owner)

From the owner's test of spec 33: (1) **a goal** is made in a dialog with metrics, a priority, links to documents and a
deadline, and **goes to the keeper at once** on saving; (2) **an idea** is a short text with **Process now** or
**Later**; closing the dialog with text saves it as Later; the keeper then fills its priority from the goal and the
rest; (3) **agents**: a role is a model and an instruction (and a limit), and each **task type** (code, tests, docs,
text for people, research) is assigned a role, or a new one is made from there; this brings §45.8's roles into v1 now;
(4) every dialog and menu opens on a dimmed backdrop; (5) a phone is paired from the shell (QR, Tailscale said
plainly). Spec 34. Improvements of v1's existing mechanics; the roles are §45.8's named exception to §27.

## 47. The Board does the writing; it starts what is safe; the Target picks the minds; the low work waits for the night (18 October, the owner and the PM)

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

## 48. Agents shows what each ork costs and how often it gets it right; Review's decisions are the signal (18 October, the owner and the PM)

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

## 49. Two branches and the gate between them; orks never on the same files at once; checks by paths (18 October, the owner and the PM)

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

## 50. Orkboard and Orkline: one engine, three slices; the loop is the graph's unit; the game only reads (18 October, the owner)

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

## 51. Operations: the person's everyday work by templates, across projects; a template checks with you until it may go by itself (18 October, the owner)

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

## 52. The Map: a project's work on one screen; the preview becomes tabs; the skill tree is Camp's skin (19 October, the owner)

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

## 53. Orkboard is drawn in orkUI; an agent's craft is its race, its tier the gear on its head (19 October, the owner)

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

## 54. The phone, round 3: what waits for you is the signal, a name fits its chip, a question comes with its answer picked (20 October, the owner)

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

## 55. Coming back: the Board says what it did, not only what it costs; the game only reads, and rewards results and thrift (20 October, the owner and the PM)

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

## 56. A goal's party is measured: a check says what it found, the party's work is shown, its price is seen before it starts (20 October, the owner and the PM)

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

## 57. Low work spends the week's room: by day when the week is ahead of its pace, at night when it is not behind (20 October, the owner and the PM)

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

## 58. A tool that is not signed in opens its own sign-in at once; the work that needs it waits for it (20 October, the owner)

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

## 59. A goal's trail: its party asks with its leader, its leader lays out its ideas as proposals, the desktop catches up with the phone (20 October, the owner)

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

## 60. One product and its labs: Orkboard, OrkWiki and OrkWatch crystallise Orkline's buildings; a building's mechanic is the shape of its work (21 October, the owner and the PM)

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

## 61. The Map shows one goal: its ideas by stage, its party in lanes; results are merged on the idea; Review's column goes (21 October, the owner)

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

## 62. One window: the goals as tabs, Planning over the leader, the party at the foot, what waits for you along the bottom; the gate is built (21 October, the owner and the PM)

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

## 63. Parties and goals: what was a goal is a party, what was an idea is a goal; a goal raises its flag in main; a party's goals are decks of one element (21 October, the owner)

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

## 64. Pick one: a task may make a few variants of one kind (pictures, sounds, clips, texts) and the person picks one with a note (21 October, the owner)

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

## 65. The leader deals the goal types; a type says who the party needs; the stages wear the party's faces; a stop is counted only where it cannot be seen; the party switch is a deck (22 October, the owner)

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

## 66. The phone, simpler: the deck beside the party's name, the faces are the members, New goal at once with the party first, a goal's two marks on every card (22 October, the owner)

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

## 67. One hand: every stop of the project in it, the most urgent in the middle, no count anywhere; every stop has a way out (22 October, the owner)

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

## 68. The type top right: a card's top right holds its goal's type, in its goal's colour; the state's sign leaves the top (22 October, the owner)

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

## 69. Fantasy signs: each goal type its own sign, a thing of the realm, never a being; orkUI keeps a library (22 October, the owner)

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

## 70. The deal on Start: a plan started from the hand deals its tasks onto the field (22 October, the owner)

Why: the owner. *Start the work* is the moment the party is set to work and money starts to be spent, and its only sign
is a stop that goes and tasks that rise where the eye is not. §62.9 already says *you deal the work*. So:
1. **A plan started by a press in the hand deals its new tasks from that stop's place to their columns** (≈ 0.3 s, in
   steps, six at most); every other start keeps the rise.
2. **It is the one motion that travels**, an exception to §62.8 kept to this press: it says what changed (how many
   tasks, to whom); nothing else flies (§65.8 stands), none under reduced motion or a hidden page, none into a column
   under the pointer; the phone deals only into the stage shown and never switches it.
The owner's call, before the testers' numbers. Spec 57.

## 71. A stop and its task: the link before the answer, one change after (22 October, the owner)

Why: the owner asked how an answered card in the hand could be read as landing on its task, more simply than a flight
(§65.8 turned the flight and the lighting down). The link is wanted before the answer, not after it. So:
1. **While a stop is looked at, its task is shown**: the desktop rings its task's cards on the field (an ink outline, no
   motion); the phone's raised card names its goal and task (and the member).
2. **An answered stop leaves where it stands, in the frame its task changes**: a fade in place, no removal before the
   Board is reread, so the eye reads one change; nothing flies, nothing is lit after (§65.8 stands).
The owner's call, before the testers' numbers. Spec 58.
## 72. Parties of mixed crafts first; the leader sets the stages and their seats; the goal types come from the team, not the leader (22 October, the owner)

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

## 73. The phone's members wear their tool and level again, beside their names (23 October, the owner)

Why: the owner: *on the phone, while the party works, you cannot see each member's tool and level: only the heads on top
and the names below; the desktop has them.* Spec 53 took the marks off with the members' strip (§66.2). So:
1. **Over each column**, the member's tool mark before its name and its level's chevrons after it; the name is cut,
   the marks never.
2. **A member's card** (its solo) says its tool in words after its head's words.
3. Not on the stage switch's faces: they are its buttons, 24 px, with the state sign on them.
Refines §66.2. The owner's call, before the testers' numbers. Spec 60.

## 74. Your own goal, first (23 October, the owner)

Why: the owner: *a party's fixed set of goal types limits the person; leave a free goal, its card filled in by the
person.* The free goal is there (*A blank goal* on the desktop, *No type* on the phone) but last, and named as empty. So:
1. It is called **Your own goal** and stands **first** on both faces; on the phone it is the one picked when the form
   opens (reverses spec 53's first type picked).
2. A type is a shortcut (its asks, its refs, its plan's hint), never a limit: a goal of one's own still gets the plan's
   *missing* line and *Add and start* when it asks for work no one of the party does (§65.5).
3. **Measured** as §65's types are: the share of one's own goals, by party and face; above about a third, the owner
   reads their words for the types the catalog lacks.
The owner's call, before the testers' numbers. Spec 61.

## 75. The spec after the start: talked over with the party's leader, and a change re-plans what is left (23 October, the owner)

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

## 76. The party gathered: what it can take as it is picked; its heads gather into the deck; three moments travel (23 October, the owner)

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

## 77. The flags raised travel from the gate to the flag line (23 October, the owner)

Why: the owner asked whether a goal's end has a motion, and whether it should. A merged task fades with a one-frame ✓
and lights its member's number (§62.8); a goal's end, its flag raised in main (§63.3), only makes the flag line stand. So:
1. **When the flag line first stands** on a device (once, as today), its goals' elements travel from the gate to the
   line (the deal's timing, six at most) and stay in it, small, before its words; then the line's flag is raised (one
   short step up) and the line is lit once.
2. **From the gate's merge** when the person merged a moment ago, else the gate's button; when no gate is on screen,
   nothing travels and the flag is still raised.
3. The third of §76.3's three moments; no sound, no confetti, no colour but the office's.
The owner's call, before the testers' numbers. Spec 64.

## 78. Ideation: small ideas read from four sides, and the Investor invests or passes (23 October, the owner)

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

## 79. Team briefs: Operations prepare the daily, the retro, the refinement and a 1:1, never a judgement of a person (23 October, the owner)

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

## 80. A member struck by a failure, a member calling with a question (23 October, the owner)

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

## 81. The hand first on the phone: the field a board of tokens, every member on the screen, the most urgent stop answered where it stands (23 October, the owner)

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

## 82. On a subscription a spend is a share of Claude's five-hour window, not ≈$ (23 October, the owner)

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

## 83. A party is a team, a goal has a route: a goal keeps itself across parties; a Release party gathers the flags (23 October, the owner)

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

## 84. On the desktop the left column is the parties: a party a heading, its goals under it; the project takes the top line (24 October, the owner)

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

## 85. The project has a level of its own, and an ork for it: the Orkmaster deals the parties and a goal's party (24 October, the owner)

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

## 86. The Orkmaster keeps the parties from colliding: what two goals both touch, a spec changed under another party, a goal that waits for another party's (24 October, the owner)

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

## 87. A closed party says what it is at work on, in one line (24 October, the owner)

Why: the owner: *the goals the parties are at work on, in the list?* Only the open party's goals are in the left column
(§84); a closed party says *k/n* and one sign, so what the others are doing now needs a switch or the project's level.
So: **under a closed party's heading, one quiet line: its goals at work**, each its element and short name (*↻ WebAuthn
register · Session cookies*), *and k more* when they do not fit; none at work, no line. A press on a goal opens that
party with the goal picked into the filter. On the phone the same line is under each party of the parties' sheet but
the one shown. The owner's call. Spec 72.

## 88. A lighter column: a goal is one line; the open party's heading is its leader; New and Flags are rows; New goal at the Orkmaster (24 October, the owner)

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

## 89. Moments of magic, not a theme: the seal at Review, a collision that crumbles, the empty Board in the void, the moon (24 October, the owner)

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

## 90. The Orkmaster fits the parties to the project, each in three sizes; a party's size is its Target (25 October, the owner)

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

## 91. The Orkmaster is crowned: a rank, not a tier (25 October, the owner)

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

## 92. The field is a game table: Orkboard's wood, a surface and never a mark (25 October, the owner)

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


## 93. Canvases: what an AI tool draws outside the code is a card with the elf's head (25 October, the owner)

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

## 94. The project's level is played on the table too: its goals are the field's cards (25 October, the owner)

Why: a press on the Orkmaster turned the cards into tickets: the level drew its goals as small decks in ruled columns
on the bare canvas, a tracker's board and not the game the party's field is (§92). So:
1. **One table**: the project's columns lie on orkUI's `.ork-table`; the party heads stand above it on the canvas, as a
   party's members do above its field.
2. **One card**: a goal on the level is the field's card, 5:7, its element, state and type as the field's Planning
   card draws them; no ruled columns.
3. **Not now**: the phone's project sheet keeps its rows.
The owner's call. Spec 79.

## 95. Orkboard is published on its own, as each building's product, under its own name (25 October, the owner)

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

## 96. Orkboard stays Apache-2.0; its names and the ork mark are not licensed; the licence is looked at again with running on our models (25 October, the owner)

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

## 97. A party can be removed; its goals move to General or go with it, never while one is at work (25 October, the owner)

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

## 98. A party picks its AI tool from a list; its size is how many agents it has and of what tiers (25 October, the owner and the PM)

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

## 99. The field is read at a glance: a row is what runs at once; a card at work turns; members are faces over their columns (25 October, the owner)

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

## 100. New goal is one field on the desktop too; the night is only for Low work and only on the person's word (25 October, the owner)

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

## 101. The next task need not wait for your look: a safe result lands in dev by itself, and what depends on nothing runs beside it (25 October, the owner and the PM)

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

## 102. Progress is seen: the elf asks about the look before it is built, and what changed shows its picture (25 October, the owner)

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

## 103. What the logs of the owner's day said: a task may run its project's commands, the gate runs the project's tests, a resumed session's cost is counted once, a send back that cannot help is not offered, a budget is never under its call's floor (25 October, the owner and the PM)

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

## 104. A party is a small team and a lens: its leader's map of the project, drawn as cards on the table; the field goes to the Orkmaster; the spec is read in the hand; the will-be map is the contract (26 October, the owner and the PM)

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

## 105. What the first look said: Play opens the page, not a port; the right column is where a thing opened is seen; Assets fills the table; a party is removed from its menu; System is the project's architecture, not its folders (26 October, the owner)

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

## 106. Warm: easier on the eyes. The ground lifted, the ink softened, warm greys, the interface in IBM Plex Sans; the pixel face for titles, headings and buttons only (26 October, the owner)

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

## 107. The owner's list: the limits always seen and what used them, a quieter top bar, Play that breathes, an AI tool for each seat, New party in two halves, parties and goals beside the Orkmaster (26 October, the owner)

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

## 108. Running the project is a party by the project's kind; working with people is a party, Team; Operations are no longer a tab (26 October, the owner)

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

## 109. A party does one kind of work and is its lens; a goal is one, and goes through the parties its work needs; the left column is the Orkmaster's goals; the Board is the Orkmaster's alone (27 October, the owner and the PM)

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

## 110. The leaders are the pane's tabs; a party's header says what it does, holds its squad and its lenses' views as a segmented control; the left column is what is looked at, the tab who looks (27 October, the owner and the PM)

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

## 111. Play is what is looked at, not a lens: the whole project or one goal, under every tab, opened where the goal changed it; Tech keeps how the project runs (27 October, the owner and the PM)

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

## 112. System reads what the project really is, a container a card first; a change on a map says who decided it; the lenses of judgement are drawn from what the project has, and the ones with nothing to read wait (27 October, the owner and the PM)

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

## 113. Play runs every process the project needs, a client and a server together; a mobile app plays as its web build in a phone's frame, and on the person's own phone over the local network when they allow it (27 October, the owner)

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

## 114. A goal's row carries its signs: the hourglass while it works, a failure that does not look like closing; a sign pressed lifts its card in the hand, where Retry and Start are (27 October, the owner and the PM)

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

## 115. Warm at half its tint, to be tried: the same lightness, half the warmth (27 October, the owner)

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

## 116. Parties are made when a project is first opened, in the Orkmaster's tab; a new goal is the blank card of the hand; its kind is picked in two short rows: the whole way or one party, then that party's kinds (27 October, the owner and the PM)

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

## 117. The Orkmaster routes and gathers, never writes a spec: each leader on a goal's route writes its own part, the Orkmaster joins the parts, and what they disagree on is a fork (27 October, the owner and the PM)

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

## 118. A goal goes Idea → Talk → Decided → Spec → Work → Done; its decision is written in the project's docs/decisions.md in git; its spec is a common part and a part a party; a change while it works is a new idea of the goal; a bug goes straight to Tech (27 October, the owner and the PM)

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

## 119. The Orkmaster's views stay its tab's; *The whole project* opens that tab, and the tab reads as one with the Orkmaster's line (27 October, the owner and the PM)

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

## 120. No right column: a card of the map is lifted and turned where it lies; what is read long opens as the pane's one temporary tab; the window is three parts again (27 October, the owner and the PM)

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

## 121. One word each for the new things; the hand is a stack a goal; a goal's cost is said before it is talked or started, and a goal may wait for the limits to reset; Orkline follows later (27 October, the owner and the PM)

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

## 122. The parties that did not fit: General, Team and Ideation go; Release is called only to release; a recurring goal is decided once; the project's stage chooses the crafts (27 October, the owner)

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

## 123. Three measures of §104–§122, read from the event log; the first slice is the parties by craft, the tabs, the sections and Talk on one real game; the rest after it is measured (27 October, the owner and the PM)

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

## 124. A new idea is written as a message: one field, Enter sends; no priority, no kind, no lens; *@party* or the open party's tab addresses it, and only then the party's views are pointed at (27 October, the owner and the PM)

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

## 125. The blank card takes a voice: a microphone writes the words into the field, never sends them; where the voice goes is said plainly (27 October, the owner)

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

## 126. Less to read twice: no top bar, a goal's row one sign, no Overview, a goal's pane follows its phase, nothing over System's table (27 October, the owner and the PM)

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

## 127. No dialogs; Operations off the left column; one closed set of signs and motions; Settings only for what lives nowhere near the work (27 October, the owner and the PM)

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

## 128. After the first slice, one face for the desktop and the phone: one page fitted to the width, the phone's app its frame (27 October, the owner and the PM)

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

## 129. No measures: the owner's yes or no after each slice is built (27 October, the owner)

Why: the owner is the one person using Orkboard; a slice is judged by them using it, not by counted events. So (this
changes §123.1 and every *Measured* of §104–§128: §104.14, §109.8, §117.6, §119.4, §120.4, §128.2):
1. **No measures are built**: §123.1's three measures and their weekly report are not made; no event is added only to
   count.
2. **A slice is done when the owner says yes**: built, the owner uses it on their own project and says **yes** (it stays,
   the next slice starts), or **no** with what is wrong (it is fixed, or taken back). §123.2's first slice and §123.3's
   order stay; *after it is measured* reads *after the owner's yes*.
3. Where a decision said *asked again if the measures show* (§119.4, §120.4), it is asked again when the owner says so.
The owner's call.

## 130. A goal done stays in the list until its result is seen, then leaves it; the done goals are a history, the temporary tab (27 October, the owner)

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

## 131. What the new window does already goes: *Process now*, the night, the gate's line, collisions as stops, a goal type's sign, the row's peek, the analytics page, the canvases (27 October, the owner)

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

## 132. The window grows from what there is: no onboarding of its own; a part comes when it has something to hold, first the pane, then the goals, then the hand (27 October, the owner and the PM)

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

## 133. A goal's first card is its route: the parties, the cost and one press before any call; the row's sign is the head of whoever has the goal now; a goal waiting for the reset may start now (27 October, the owner and the PM)

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

## 134. Less said twice: what waits is the hand's alone; a party is one map; its header is its name and its squad; *The whole project* is no goal picked; a goal with nothing to settle starts on its decision (27 October, the owner and the PM)

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

## 135. The Orkmaster keeps *Board* alone; Assets is what is looked at, beside Play, under every tab; Art's map is the Assets of its kinds (27 October, the owner and the PM)

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

## 136. What §132–§135 left uneven: one meaning for the hourglass, a cost said again when the route grows, no Assets button, recurring rounds and the wait as signs, how the project runs on System, Stop all on the phone, the picking mode, a goal at work through the Orkmaster is its Board, Agents goes; the first slice counted again (27 October, the owner and the PM)

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

## 137. Release is in every project from its start and is the one way into main: its map is dev against main; *To main* by code, *Release a version* with its cost (27 October, the owner and the PM)

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

## 138. *Done* is in dev; the route card comes first on the first start too; a goal's place is *in line*; a goal before *Work* opens on the Orkmaster's tab; files with no Tech nor Design are the Orkmaster's menu's; a recurring round waits for the reset; a decision is committed to dev (27 October, the owner and the PM)

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

## 139. A goal of one party opens on that party's tab at every phase (27 October, the owner)

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

## 140. The Orkmaster's tier is not chosen; a head on the route card is taken off by its ×; *+* never offers Release; the picking mode ends on *Stop picking* (27 October, the owner and the PM)

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

## 141. An idea addressed to a party may pin any card of that party's map (27 October, the owner)

Why: §124.5 names what an addressed idea may point at (*a part of System, a screen or a pain*), written when those were
the only maps; Art's map (§135.4), Game design's *Loop* (§112.8) and Release's map (§137.3) came after, and each would
need its line. So (this changes §124.5 and §135.4's last clause):
1. **In picking (spec 94 §1.5), any card of the addressed party's one map (§134.2) is pinned** to the blank card as a
   mark: a part of System, a screen, a pain, an asset, a card of the loop, a goal on Release's map, and whatever map
   comes later, with no list to grow.
2. A general idea (the Orkmaster's tab, no party addressed, §124.4) has no picking: it is its text alone.
The owner's call.

## 142. No temporary tab: the pane opens one thing over its map, with ← back; the tabs are the leaders alone (27 October, the owner and the PM)

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

## 143. The Board's columns stand under the tabs: a tab is its column's head, the Board has no header of its own; the Orkmaster's column is its routing (27 October, the owner)

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

## 144. The card battler kept: a card is played onto its party's lane, a card that spends carries its cost in its corner, the lane it is about rises while it is held (27 October, the owner and the PM)

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

## 145. No left column: the window is two parts, the table and the hand; a goal lives in the deck, the hand, on the table or in the discard; the Orkmaster's line is its tab (27 October, the owner and the PM)

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

## 146. In VS Code a read opens in the editor, not over the pane; the Board can stand in the editor's side bar, narrow (27 October, the owner and the PM)

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

## 147. Operations leave Orkboard's window; the person reads four phases; the decision has one button; *Later* only when the limits run low (27 October, the owner and the PM)

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

## 148. orkUI made to fit the new window: the half-tint warm taken; one moon; the icons at the signs' weight; the marks in ink; the elements apart from the signals; the heads at 16 px at least; the races, signs and emblems Orkboard draws; the preview the window as decided (27 October, the owner and the PM)

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

## 149. The cards react as in Balatro, with no motion added; a hand card face down has one back; the heads on a 16 grid read by their silhouette; the detailed art is the marketing's (27 October, the owner and the PM)

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

## 150. The phone turned on its side is the table, as Balatro's: a low window keeps the wide layout made compact; upright stays the quick answer; nothing is locked (27 October, the owner and the PM)

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

## 151. A party's squad is who it has, its size how the work goes; a specialist's view is marks on its party's map; one place makes and edits the parties; Marketing comes back with UA (28 October, the owner and the PM)

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

## 152. In picking, cards are taken with a box, as Warcraft's units; a box that takes a whole group pins the group (28 October, the owner and the PM)

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

## 153. What a party asks of the project: Product at the start, each other leader at its party's first goal, inside a goal's three; a question is a card of up to four choices and *Other…*; a goal's questions a stack, one a card (28 October, the owner and the PM)

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

## 154. Product's party is the knights, Release's the undead: a lich leads it, skeletons are its hands; Orkboard draws six races (28 October, the owner)

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

## 155. A party's leader is its race's higher form, grown, not worn: the tier is what a head wears, the leader what grows out of it; Product's members are griffins (28 October, the owner and the PM)

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

## 156. A leader reads the project through its map: every call carries its map as text, read by code and current with dev; the parties are kept in step by the parts of their maps, never by reading each other's specs; what a call may read is bounded in fact (28 October, the owner)

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

## 157. What §151–§156 left uneven: the project's questions are a stack among the stacks; Release's squad is its leader until seats are added; spec 95 read up to §157 (28 October, the owner and the PM)

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

## 158. A bug's Talk finds its cause; a party's race is its party's, not its role's craft: six parties, six races, six leaders; the rest of the cast is the marketing's (28 October, the owner and the PM)

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

## 159. Release's card is the discard's: the goals done and those ready for main are one pile at the hand's right (28 October, the owner)

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

## 160. The hand is three places: the deck with the new goal's card drawn off it, the stacks, the discard; the deck's back says the next goal; a card's face its gem, its words when lifted (28 October, the owner and the PM)

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

## 161. The heads keep their old drawing: the races are told by their faces and colours on the 12 × 11 grid, the leaders and the griffin drawn the same way (28 October, the owner)

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

## 162. Product's party is the knights again, led by a golden unicorn knight with an angel's wings; the shaman without the war paint (28 October, the owner)

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

## 163. A card is neutral on the warm table: the cards' own fill and frame, soft greys a step lighter (28 October, the owner)

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

## 164. The leaders have names of their own, said only where a party is made and edited (28 October, the owner)

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

## 165. Light cards are for later: §163's neutral cards stay; a light card asks its own heads and a second palette (28 October, the owner)

Why: a fourth way was drawn beside §163's (orkUI's `docs/compare/cards.html`, D): the cards the colour of today's ink
(`#dedbd6`), their words dark. It reads as cards on a table most of all (12.8:1 against it, §163's A 1.30:1), but the
heads are drawn for dark grounds (25 of their 32 colours fall under 3:1 on the light card, the elf's and the dryad's faces
1.02:1), and the elements and signals need darker kin on it. So:
1. **§163 stays**: the cards neutral on the warm table.
2. **Light cards are a later pass** of orkUI's, apart from the slices: a set of heads that stand on a light ground, the
   elements and signals' kin for it, and both grounds measured; then the owner looks again.
The owner's call.

## 166. The cards a hint cold: a slate grey on the warm table (28 October, the owner)

Why: the owner, after §163's neutral cards: *let's try them colder.* Two cool tints of A were laid beside it at the same
lightness (orkUI's `docs/compare/cards.html`): A1, a hint cold (CIELAB chroma about 3, hue about 250), and A2, cold
(chroma about 6). Both hold every measure; A2 reads as a colour of its own across a whole screen, A1 as paper. So (this
makes §163.1 precise):
1. **The cards' fill is a slate grey**: `card` `#2a2e31`, `card-frame` `#383d41` (chroma about 3, hue about 250, almost
   opposite the warm table's), the backs' greys with them; every measure of §163.2 held on it (the faint ink 4.54, the
   heads' edges 3.03 at least, at least 20 CIE76 from `ice` and `void`).
2. In orkUI 0.15.4, then copied here (spec 96).
The owner's call.

## 167. The cards read as a card game's, a goal lies as a cascade in its party's lane, the hand lies under the lanes, the deck goes into the first lane (28 October, the owner and the PM)

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

## 168. The cards' names in the body face; the + card turned and green; a stack and a goal's tasks as a fan (28 October, the owner)

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

## 169. S1 and S2b taken; seven seats; a risky step waits; the first start opens the parties' place; a fact can be added (28 October, the owner)

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

## 170. orkUI 0.16 taken: the goal types' big signs in two tones, a pick's suits the asking party's race's tool (28 October, the owner)

Why: the owner made orkUI 0.16.0 (its CHANGELOG): the signs at 28 px were coarse, and the choices of a pick wanted telling apart by
their shape, with the craft of the race said with a joke. So (this makes §167.1–§167.2 precise):
1. **A goal type's sign at 28 px** is orkUI's 14 × 14 drawing in two tones (the silhouette in the text's colour, its light over it);
   the states', the media signs, `sword`, `shield` and `question` keep their 7 × 7. *New feature*'s three kinds have their own
   signs: the wand (`feature`), the compass (`shaped-feature`), the shoe (`flow-feature`: `steps`).
2. **A choice's card wears its suit**: the asking party's race's tool (orks a drum, elves a bow, goblins a pick, gnomes a bell,
   knights a map, skeletons an hourglass), its four variants by the choice's place; a preview or a fork's side's head in its place
   where there is one.
The owner's call.

## 171. S3's faces as the mockup drew them; a task card's every kind in a two-tone drawing (29 October, the owner)

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

## 172. Product's map is an opportunity solution tree, its opportunities the users' jobs to be done; the pains along the journey are Design's (29 October, the owner and the PM)

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

## 173. A task card shows a drawing of the race that does it (29 October, the owner)

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


## 174. The phone's app a native frame: upright it is the hand with the top card's context above, on its side the table without the hand; push through a relay that reads nothing, an answer from the notification, widgets (29 October, the owner)

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

## 175. The tree as drawn; the AI tools' limits move to the hand as its mana (29 October, the owner)

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


## 176. The mana is blue, the potions lie flush right; the discard lies on the table; a lifted card is a card (29 October, the owner)

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

## 177. The default tool is the potion in the frame, and work goes on with the next when it runs dry; a goal is sent to main through a portal (29 October, the owner)

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

## 178. The phone is the page first, then the native frame; upright the hand with the potions in its top row; the Board only on its side, with the discard and the portal (29 October, the owner)

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

## 179. Upright the tools are their marks and shares, as tall as *The Board*; on its side the Board's foot is the goals' legend (29 October, the owner)

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

## 180. The phone is the hand alone: no Board on it for now; the portal is a card of the hand; the top card narrower over a fan; New goal the green deck under the thumb; **…** for the rest (29 October, the owner)

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
