"""The window's words (the table and the hand, the Board, the levels, a goal's way, the corners and the piles, the opened card; the inventory and a way's
kind): two blocks of realm/lexicon.py `TERMS`, kept here so the glossary's module stays under ~600 lines (CLAUDE.md). `TERMS` splices `WINDOW` and
`SLOTS` back in their places, so the glossary's order and its keys are as they were; a new word of the window goes in one of them. Pure module."""
from __future__ import annotations

from orkboard.realm.lexicon_term import Term, _t


WINDOW: tuple[Term, ...] = (
    # The table and the hand (docs/specs/98-the-table-and-the-hand.md §0.1, §2.4; decisions §145): the window's two parts
    _t("not_checked", "not checked"),                              # a goal's *Done when* line nobody looked at, or the acceptance could not see (spec 168 G1, decisions §283.16.10): never *ok* by default
    _t("not_met", "not met"),                                      # a *Done when* line the acceptance looked at and found not met
    _t("landed_not_compared", "landed, not compared"),             # a promised part of a craft whose map has no file touch: its tasks landed, nothing was compared (spec 168 G1)
    _t("result_built", "built"),                                   # a result table (spec 168 G2, decisions §283.16.11): what the spec planned against what was built
    _t("result_before", "Before"),                                 # … the code's work before the goal (Tech's System at the commit before it, Design's picture before it)
    _t("result_after", "After"),                                   # … and after it (the System at its last commit, the picture its task kept)
    _t("result_sent_back", "sent back"),                           # a task that ran more than one round: one of the goal's errors
    _t("result_red_test", "red test"),                             # a test red on a task's gate, and not red before the goal: one of the goal's errors
    _t("table", "table"),                                          # the window's upper part: the leaders' tabs and the pane under them (what and why, through whose eyes)
    _t("hand", "hand"),                                            # the window's lower part: what the person decides, under the lanes, with the stacks of stops and the discard
    _t("discard", "discard"),                                      # the goals done and not yet seen, and what is ready for main (read *Done*)
    _t("lane", "lane", "lanes"),                                   # a party's column on the Board under its tab
    _t("blank_card", "blank card", "blank cards"),                 # the + card alone under the first lane, and the field it grows into: *Write a goal…*
    _t("lifted_card", "lifted card", "lifted cards"),              # a card pressed and raised over the pane, with its answers and *Put it back*
    _t("map", "table", "tables", "map", "maps"),                                   # what a party's tab shows under its header: Tech's is *System* (a part of it is never called a card)
    _t("spread", "spread", "spreads"),                             # cards laid to show one thing at a time: the centre what is talked of, a fan a choice, a pile a group (decisions §296.9)
    _t("mat", "mat", "mats"),                                      # a leader's mat: an M card of the table of cards, a change in the leader's framework or a spread of it, opened as that table or spread (decisions §297)
    _t("craft_token", "token", "tokens"),                          # a leader's verdict on a card: its craft's tool in its party's ring, its checks as squares under it (decisions §298.3)
    _t("blocker", "blocks", ""),                                   # a craft's risk that holds a card's start until its leader lifts it (decisions §298.3)
    _t("dropped", "Dropped"),                                      # the discard's third pile: the cards the person dropped, face down, each can be taken back (decisions §298.8)
    _t("seal", "seal", "seals"),                                   # the stamp at a mat's foot's right that a move which cannot be undone (Merge into main, Send to a branch, Ship a release, a paid pass) asks for: dim with its why until a way is picked, pressed it sends the move with `sealed: true`; every other move is one press with its Undo (decisions §300.15, §302.4)
    _t("battle", "battle", "battles"),                             # the Orkmaster's spread of a new card against the cards it goes against, axis by axis, no winner said (decisions §298.6)
    _t("blank_deck", "deck of blank cards"),                       # at the hand's right edge: a new goal is a card drawn from it and named (decisions §298.2, §298.9)
    _t("concern", "concern", "concerns"),                          # what a party's leader says is wrong or at risk in one part of its map, with why and what would fix it (spec 108, decisions §183.7); not a flag, not a finding
    _t("measure", "measure", "measures"),                          # how the arguing turned out, counted from the project's own event log: a no heeded or overruled, a goal accepted the first time (spec 124 B, decisions §202.3); never a count in the window
    _t("journal", "journal", "journals"),                          # what was said and what came of it, kept for the project and for each leader, and read into the leaders' calls (spec 125, decisions §203.1); not the talk of one goal, not the event log
    _t("inbox", "inbox", "inboxes"),                               # the branch of the project's repository the phone drops goals into, `orkboard/inbox`: one file a goal, added and never edited (spec 136, decisions §243.2); not the mailbox (§219), not a list in the window
    _t("taken", "taken"),                                          # a goal from the inbox read by the computer or a cloud session and laid on the Board, said in the journal first (spec 136 B, decisions §243.4); *Waiting to be taken* until then
    _t("waiting_to_be_taken", "Waiting to be taken"),              # what a goal in the inbox says on the phone until the computer or a cloud session has taken it (spec 136 C.4, decisions §243.3)
    _t("as_of", "As of"),                                          # what the phone's screens say before the journal's time (*As of 14:02*): what it shows was true then, never now (spec 136 C.4, decisions §243.5)
    # The Board in the repository (docs/specs/137-the-board-on-its-own-branch.md E; decisions §244.14)
    _t("board_branch", "the Board's branch"),                      # the branch of the project's repository that holds the Board's pages and state, `orkboard/board`: never merged, no workflow in it, private repositories only (spec 137 A, decisions §244.1); not the work branch, not the journal's or the inbox's
    _t("holds", "holds the Board"),                                # what the one worker that may write the Board's branch does, by a lease renewed every three minutes: the computer with Orkboard open, or a cloud run (spec 137 B, decisions §244.2)
    _t("cloud_run", "cloud run", "cloud runs"),                    # the second worker of the Board, a job on GitHub Actions that reads the goals and takes the answers in, never the work (spec 137 D, decisions §244.6–7); not the computer
    _t("planned", "Planned"),                                      # what a goal says after a cloud run: its plan is made, its work waits for the person's computer (*Planned: the work starts on your computer*; spec 137 D, decisions §244.7); not the plan card, not a state of the runner
    _t("cloud_secret", "the secret that pays"),                    # which of the two secrets GitHub gives a cloud run pays for the model's calls: the subscription's (`CLAUDE_CODE_OAUTH_TOKEN`, sharing the week's limits) or an API key's (`ANTHROPIC_API_KEY`, by the token) (decisions §244.8)
    _t("cloud_ceiling", "ceiling", "ceilings"),                    # the most dollars one cloud run may spend of an API key's calls (*At most $1 a cloud run*), a number the person sets; not a week's limit, not the day's spend limit (decisions §244.8)
    _t("board_rules", "the Board's rules"),                        # the block in AGENTS.md and CLAUDE.md, BOARD.md and the roles that let any AI tool work the Board as Orkboard does (spec 151 C, decisions §255.5): written on the person's yes, written again when Orkboard's change; not the project's own rules, which win over them
    _t("acceptance", "acceptance", "acceptances"),                  # a leader's check of its step against its section (spec 152 B, D; decisions §256.3): the leader accepts, or sends back; the person's at Review stays Merge
    # The Board in the code, or off it (docs/specs/151 F; decisions §255.10): the person's yes or no, asked first in a public repository
    _t("in_code", "the Board in the code"),                       # whether the Board's pages go to the work branch of the project's repository (`[board] in_code`): a yes is public in a public repository, in its history, and a later no does not take it back
    _t("in_code_public", "Your goals, their specs, the leaders' words and the decisions will be public, in the repository's history: a later No does not take them back."),   # the question's words (the Orkmaster's card, Settings' line, `orkboard init`)
    _t("in_code_pages", "<n> pages of the Board are already in its history"),     # … and, when there are some, how many are
    _t("publish_board", "Publish the Board"),                      # … its yes: `in_code = true`
    _t("keep_board_off", "Keep the Board off the repository"),     # … its no: `in_code = false`; the Board stays on this computer, and no rules are written
    _t("is_private", "Is this repository private?"),               # asked first when the remote is one Orkboard cannot read (not on GitHub, or no answer)
    _t("repo_private", "Private"),                                      # … its yes: `in_code = true`, nothing is public
    _t("repo_public", "Public"),                                        # … its no: the publish question follows
    _t("rules_find_no_board", "The Board is kept off this repository: the rules would find no Board"),     # Settings' line for the Board's rules while `in_code` is false
    _t("keep_goal_off", "Keep off the repository"),                # the new goal's card: this goal's page and files stay on this computer, in a public repository with the yes (F.4)
    _t("goal_kept_off", "Kept off the repository: on this computer only"),     # … what the goal's row says of a goal so kept
    _t("taken_by", "Taken by <by> until <time>"),                  # a goal another tool holds, on its row (spec 151 D.1: realm/goal_take.py `line_of`); `taken` is the inbox's word
    _t("slice", "slice", "slices"),                              # a leader's part of a decision: the key conclusion for its craft and the points it rests on, cut once at Confirm and read into the leader's calls (spec 131, decisions §233.1); not shown yet
    # Four levels and findings (docs/specs/132-four-levels-the-way-down-and-findings.md D.6; decisions §234.8, §237.9): the words of the levels, of a finding and of the quality card
    _t("level", "level", "levels"),                                # where a change or a finding lies: Decision, Spec, Work or Quality, the heaviest and cheapest to change first (decisions §234.1); not a goal's tier nor a party's size
    _t("quality_finding", "finding", "findings"),                  # what a goal did against what was promised, found where it was found and taken up to the level that holds its cause (decisions §234.3); not a check's `check_finding`, not a concern
    _t("quality_record", "quality record", "quality records"),     # a goal's verdict against its spec, its checks, the lenses' alarms and its findings with what became of them, kept once the goal is done (decisions §234.4)
    _t("level.decision", "Decision"),                              # the level of what and why
    _t("level.spec", "Spec"),                                      # the level of how, by craft
    _t("level.work", "Work"),                                      # the level of the tasks and the code
    _t("level.quality", "Quality"),                                # the level of what came out against what was promised
    _t("quality_of", "Quality of"),                                # the quality card's title, before the goal's (decisions §237.1)
    _t("found", "found"),                                          # *<Party> found: …*, a finding's line in the hand
    _t("cause_in_code", "The cause is in the code"),               # a finding sorted to Work
    _t("cause_in_spec", "The cause is in the spec"),               # a finding sorted to Spec
    _t("cause_in_decision", "The cause is in the decision"),       # a finding sorted to Decision
    _t("fix_there", "Fix it there"),                               # a finding answered at its level (decisions §237.2)
    _t("fix_all_there", "Fix all there"),                          # every finding of a quality card answered at once, its cost said first
    _t("another_level", "Another level…"),                         # the rare answer, under a finding's …: the person moves its level
    _t("not_now", "Not now"),                                      # a finding put off: it stays on the goal's quality record and leaves the hand
    _t("looks_like_part_of", "Looks like part of: <title>"),       # the new-goal field's line when a goal sent looks like part of one lying face down (spec 135 A, decisions §242.1)
    _t("add_to_it", "Add to it"),                                  # … its yes: the words join that goal through *Add to the goal* (§242.2)
    _t("keep_apart", "Keep apart"),                                # … its no: the goal goes on its own; and a group of the backlog's card kept as it is (§242.5)
    _t("look_like_one", "These look like one goal"),               # the one card of the backlog's groups, at the reset (spec 135 B)
    _t("join", "Join"),                                            # a group of that card taken as one goal
    _t("split", "Split"),                                          # a joined goal given back as the goals it was (spec 135 C)
    _t("add_to_goal", "Add to the goal"),                        # the bubble's line on a goal not yet agreed (spec 132 A)
    _t("change_decision", "Change…"),                              # the decision's one button beside *Confirm and start* (decisions §237.3)
    _t("or_say_change", "Or say what to change"),                  # the line under the decision's field
    _t("proposes", "Proposes"),                                    # what a leader's card says of its proposal to change a slice of the decisions (spec 131 B.4, decisions §233.8)
    _t("agrees", "Agrees"),                                        # … of a leader that agrees with the change in its own slice
    _t("disagrees", "Disagrees"),                                  # … of a leader that does not: a fork for the person
    _t("stopped_after_steps", "Stopped after <n> steps"),          # where a cascade stopped at its bound of steps, with who was not asked (decisions §233.7)
    _t("stopped_at_price", "Stopped at its price"),                # … or at the price it may spend, 2 % of the main tool's week
    _t("agree_line", "<A> and <B> agree"),                         # the card's one line when no leader disagreed: *Tech and Art agree* (decisions §237.6)
    _t("answer_the_fork_first", "Answer the fork first"),          # what Confirm says while a leader's disagreement has no answer
    _t("goes_against", "Goes against §<n>"),                       # a conflict's line: the goal's decision goes against a standing decision, the point in conflict beside it (spec 150 E1, decisions §254.6)
    _t("new_wins", "New wins", was="The new one replaces §<n>"),   # a battle's first way (the old table's conflict card too): §N gives way, the new decision replaces it; one press with its Undo (goal "The battle and the gate" K, decisions §303.4)
    _t("old_wins", "Old wins", was="Keep §<n>"),                   # … its second: the new decision is worded again within §N; sealed, its cost said first
    _t("keep_decision", "Keep §<n>"),                              # the line the keeper is given when the old one wins (*Keep §N: <point>*), not a way's name
    _t("your_words", "Your words", was="Other…"),                  # … its third: the new decision is worded again with the person's own words; written first, then sealed
    _t("aspect", "aspect", "aspects"),                            # one thing a craft's senior looks at on its map (*Hotspots*, *Accessibility*, *Economy*), with the question it asks; a concern names its aspect; never a check (the gate's) nor a finding (spec 109, decisions §184.2)
    _t("hint", "hint", "hints"),                                   # what code noticed and no one said: a map's hint of code (spec 109 §3), a press that did nothing on Play (spec 115 §4)
    _t("reach", "reach", "reaches"),                               # what a goal not yet started would change on a leader's map, one and two steps out (spec 165, decisions §280.1)
    _t("play_mark", "mark", "marks"),                             # a box the person drew on Play with a line: the live product's own picking (spec 115 §5)
    _t("hypothesis", "hypothesis", "hypotheses"),                  # what the project believes and has not shown, with the signal that would show it, on Product's tree; tested by goals, judged in the hand (spec 116)
    _t("refuted_way", "way it is refuted", "ways it is refuted"),  # one of the one to three conditions that would refute a hypothesis, named by what it would teach (the hook, the noise); the verdict picks the one that was met (decisions §235.1, spec 133 A)
    _t("test_measure", "measure", "measures"),                     # what a hypothesis is tested by besides a goal: a thing counted, where it is read from, its bar in each condition and the date it is read on (decisions §235.2, spec 133 B); `measure` is the table's own
    _t("seat", "seat", "seats"),                                  # one place in a party: its leader's, a builder's, a checker's; a head sits in it
    _t("squad", "squad", "squads"),                                # a party's seats together, grouped *Leads* | *Does* | *Checks*
    _t("size", "size", "sizes"),                                   # how large a party is, in one word: lean, standard or full (the Target's, spec 75)
    _t("in_line", "in line", "", "deck", "decks"),                 # a goal not started, waiting its turn: the first lane's last cascade (decisions §167.5; it was the *deck*, whose place value `deck` the code keeps)
    _t("cascade", "cascade", "cascades"),                          # a goal's tasks laid in its party's lane, the front one whole and the others as strips (decisions §167.4); and what a leader's proposal changes in the other leaders' slices, step by step, before it is a decision (spec 131 B, decisions §233.6): one word for both
    _t("hold", "Hold", "", "Later today"),                         # put a goal off until the person presses Start now; its card says Held (decisions §247.2; the queue `hold`, a raw `night` reads so)
    _t("later", "Later", "", "Later, by itself"),                  # a goal that starts by itself at an hour the Board says: after the reset, in the person's hours, tonight (`ideas.route_later`; decisions §247.2)
    _t("save", "Save"),                                            # the to-do form's button (was *Keep it*, which is now only the drop question's *do not drop it*; decisions §247.2)
    _t("limits_not_read", "Limits not read"),                      # a potion's words for an AI tool whose limits were not read (hand/mana.js; decisions §247.3)
    # The first open is the Orkmaster's (spec 130, decisions §232.11): the AI tools set from the hand, never from a form.
    _t("tool_order", "the order the work moves on in"),            # the AI tools in the person's order, the potions' left to right: the first is the main tool, and the work goes on with the next when it runs dry (`machine.tool_order`)
    _t("add_ai_tool", "Add an AI tool"),                           # the card the empty slot lifts: one tool, how it is paid, a sign-in or the key found, Test & add (never *shop*, *buy*, *belt*)
    _t("test_and_add", "Test & add"),                              # one short request to the tool's lightest model; a tool is in the hand only after it answered
    _t("add_another", "Add another"),                              # the card turned after a tool is in the hand: the card again, without the tools in the hand
    _t("go_on_to_the_parties", "Go on to the parties"),            # the first open's way from the AI tools to the parties' card (later *Done*)
    _t("put_back", "Put back"),                                    # a tool taken out of the hand between tasks, with Undo in the toast; the last one asks first
    _t("which_project", "Which project shall we work on?"),        # the Orkmaster's first question, its answers cards in the hand
    _t("waits_for_the_reset", "waits for the reset"),              # the line under In analysis while goals put off wait: *waits for the reset · Mon 09:00*, a state, never a count (decisions §239.4)
    _t("table_laid", "The table is laid"),                         # what the Orkmaster says at the project's first Start: the leaders sit down, the table is drawn once
    # A goal's way (docs/specs/99-a-goals-way.md §10; decisions §117, §118, §121.1): the words of the route, Talk, the decision and the spec, each once
    _t("route", "route", "routes"),                                # the parties that write a goal's spec and do its work, in order; the Orkmaster routes a goal, never a job title
    _t("route_card", "route card", "route cards"),                 # a goal's first card: its route, the cost said before, its place in line, and Talk (the `route` row)
    _t("step", "step", "steps"),                                   # one party's turn on a route: its leader writes its section, then its work is planned and done
    _t("phase", "phase", "phases"),                                # where a goal is on its way: Talk, Spec, Work, Done
    _t("phase.talk", "Talk"),                                      # the route's leaders answer short, the person answers in the hand
    _t("phase.spec", "Spec"),                                      # the decision is made; each leader writes its section, the Orkmaster joins them
    _t("phase.work", "Work"),                                      # the steps' tasks run
    _t("phase.done", "Done"),                                      # the goal is in dev, its result to be seen
    _t("phase_earlier", "Earlier"),                                # the table's one folded line under a picked goal past Talk: *Earlier: Talk · Spec*, each phase unfolding what it said at this tab (spec 156 C.3, decisions §261.4)
    _t("section", "section", "sections"),                          # one party's part of a goal's spec, written by its leader
    _t("project_stage", "stage", "stages"),                        # how far the project is: idea, being made, live (realm/project_stage.py); a party's `stage` is the other word above
    _t("will_be", "Will be"),                                      # the change a section promises, on the maps it touches
    _t("fork", "fork", "forks"),                                   # two sections that disagree: the person decides, and only the sections it touches are written again
    _t("its_leader_takes_it_next", "Its leader takes it next"),     # the same on a task its party's leader does: a leader's seat never says a member's word (spec 143 F.2, decisions §250.7)
    _t("takes_it_next", "takes it next"),                          # a waiting lane card's window: *an elf takes it next* (spec 142 C, decisions §249.5)
    # a card's four corners, the bottom right's one figure (spec 147 A, decisions §251.2; table/corners.js `muchOf`)
    _t("corner_asks", "asks you"),                                  # a card that waits for the person: the figure in the alert
    _t("corner_left", "left"),                                      # the time a task at work has left: *4 min left*
    _t("corner_took", "took"),                                      # the time a task or a goal done took: *took 18 min*
    _t("corner_worked", "worked"),                                  # a task at work with no estimate: the time it has worked, as it did before
    _t("corner_tokens", "tok"),                                     # the bottom right's unit when a tool's window cannot be measured: *18k tok* (spec 168 C5, decisions §283.17)
    _t("corner_estimate", "≈"),                                     # before the figure of a card ahead: its party's average for its kind, an estimate
    _t("corner_in_main", "in main since"),                          # the discard's card: *3 tasks, in main since 11:40*
    # the words under the Orkmaster's piles (spec 147 B, decisions §251.10; table/piles.js): *reading: <goal>* under In analysis, *next in 2 min: <goal>* (a decision's wait) or *next at 13:40: <goal>* (a spec's look) under To review
    _t("column_reading", "reading"),                                # the goal the Orkmaster or its leaders are on, under *In analysis*
    _t("next_in", "next in"),                                       # the next to start by itself and the time left, under *To review*
    _t("next_at", "next at"),                                       # the same for a spec that waits for its look: the clock time it starts at
    # the Orkmaster's piles are the goal's stages (spec 168 B1, decisions §283.11–§283.12; table/stages.js `PILES`); the phone's menu keeps the old three (table/oldpiles.js)
    _t("pile_ideas", "Ideas", "", "In analysis"),                    # the goals the Orkmaster reads and routes, in Talk, an agreed decision's wait: the fan of small backs
    _t("pile_specs", "Specs", "", "To review"),                     # the sections being written, the plan, the look's wait: a squared deck of small backs on their side
    _t("pile_implementation", "Implementation", "", "At work · later"),   # the goals at work (held after the spec or waiting for the night at the foot): the cascade of standing cards
    _t("column_writing", "writing"),                                # the spec being written, under *Specs*: *writing: Round timer*
    _t("head_at_work", "at work"),                                  # a leader's header: its goals in flight as small cards (spec 168 E1, decisions §283.16.2)
    _t("head_concerns", "concerns"),                                # … the header's group of its open concerns as small cards
    _t("head_ask", "ask"),                                          # … the header's group of the ? card, the quick question to this leader
    _t("column_at_work", "at work"),                                # the goal at work, under *Implementation*: *at work: Round timer*
    # a party's tab greyed while a goal is picked that its route does not pass (spec 156 B.5, decisions §261.3, §261.15; table/tabs.js): *Product is not on this goal. Press to leave it and look at Product's table.*
    _t("tab_off_is", "is not on this goal"),
    _t("tab_off_press", "Press to leave it and look at"),
    # the opened card and a new goal's card (spec 147 D, spec 148 B.6, decisions §251.2, §252.4; hand/openwords.js): the empty corners say what will stand there, the window what to drop on it, the foot who asks
    _t("slot_rune", "the rune: given when it is laid"),            # a new goal's top left, dashed until the goal is laid
    _t("slot_who", "who: the Orkmaster routes it"),                 # its bottom left, until the party is known
    _t("slot_kind", "the Orkmaster reads it"),                        # a new goal's top right, until a kind is picked (spec 150 F.1, decisions §254.9)
    _t("now", "Now"),                                               # a new goal's primary: sent, and Talk starts at once when the limits allow and it costs no more than agreed (spec 150 F.2; `ideas.add` `now`)
    _t("slot_much", "how much: after its estimate"),                # its bottom right, until the goal is estimated
    _t("attach_hint", "Drop pictures or files here, or paste a picture"),     # a new goal's window while nothing is attached
    # the card in play (spec 168 D1, D2; decisions §283.19, §286; hand/fielddeal.js, hand/answercards.js): what the words field says of its keys, and what *Now* and *Later* are when they are dealt as cards
    _t("field_now_line", "The Orkmaster talks it over at once, as far as the limits allow."),      # the card *Now*, dealt by a new goal's last corner
    _t("field_later_line", "It lies in line and talks by itself at the hour the Board says."),      # the card *Later*
    _t("field_keys_now", "Enter is Now · Shift+Enter a new line"),                                   # a new goal's field: its keys
    _t("pen_keys", "Enter sends · Shift+Enter a new line"),                                          # *Your own words…*: its keys
    _t("opened_leader", "leader"),                                 # the opened card's foot: *the Tech leader asks*
    _t("opened_asks", "asks"),                                      # the same, and *the Orkmaster asks*
    _t("look_wait", "Give me time to look"),                    # Settings: the wait of every spec made before its plan is passed by itself, 30 min · 2 h · until tonight · do not wait (spec 144 B, decisions §225.1)
    _t("my_hours", "When I am at the computer"),                  # Settings: the person's days and hours (spec 138 B.1, decisions §245.5); empty, nothing changes
    _t("not_before", "not before"),                                # a goal put off, on its row: *not before 14:05* (spec 138 B.5, decisions §245.4)
    _t("work_goes_on", "the work goes on at"),                     # a goal at work held by a spent window, on its row: *the work goes on at 14:00* (spec 138 B.5)
    _t("judge_again", "Judge again now"),                          # the Orkmaster's table of an idea: the leaders that doubted, said no, were turned down or were touched judge it again (spec 168 C2, decisions §283.25)
    _t("stage_assessing", "Assessing…"),                           # the Orkmaster's table of an idea: a leader that has not said its verdict yet, beside its back (spec 168 C3, decisions §283.16.3)
    _t("stage_later_step", "Its step comes when the step before it is accepted"),     # the Orkmaster's table of the implementation: a later leader's step, a placeholder until the step before it is accepted (spec 168 C3, decisions §283.14)
    _t("stage_part", "part"),                                      # the Orkmaster's table of a spec: a leader's section as a card, *Tech's part* (spec 168 C3)
    _t("ask_card_goal", "Make it a goal"),                         # a quick question's answer card (the card of the kind ?, spec 168 D3, decisions §283.20): its way that opens the new goal's field with the suggested line
    _t("ask_card_more", "Ask more"),                               # … its way that asks the same leader again, the words kept
    _t("ask_card_got_it", "Got it"),                               # … its way that puts the card away: the answer is taken in and nothing changes (the way's kind is `take`)
    _t("say_needs", "Needs your answer"),                         # a leader's table of an idea: what its risks, conflicts and questions ask of the person (spec 168 C1, decisions §283.23)
    _t("say_better", "Could be better"),                           # … and its improvements, each a line of the goal rewritten (spec 168 C1)
    _t("say_verdict", "Its verdict"),                              # a leader's table of an idea: the group that holds the leader's own card, its sign (spec 168 C4, decisions §284.1)
    _t("say_undo", "Undo"),                                        # the Orkmaster's rewrite of the goal's words, put back exactly as they were (spec 168 C4, decisions §283.24)
    _t("doubt_still", "still doubts"),                              # a leader's card in the hand after the leaders judged the goal again once: *The Architect still doubts* (spec 168 D5, decisions §283.25); its why at its foot
    _t("doubt_still_no", "still says no"),                          # … when the leader's verdict is a no
    _t("to_hearing", "To the hearing"),                             # … its way that takes the goal to its hearing now, with no second judging (`ideas.to_hearing`; the way's kind is `go_on`)
    # -- a goal's branch, the discard's two piles and To main (spec 168 F2, F3; decisions §283.26–§283.28). <dev> is the project's work branch, <branch> a branch, <n> a count --------
    _t("to_dev", "To dev"),                                        # the lower pile's card played: the goal goes from its own branch into dev (`ideas.goal_to_dev`; the way's kind is `go_on`)
    _t("to_dev_untested", "To dev without the tests"),             # … in the card's menu: the gate's tests are not run (`untested: true`; the way's kind is `accept_risk`), as *To main without the tests* is for main (§274.3)
    _t("try_again", "Try again"),                                  # a goal blocked before dev: the way that asks the gate again (`ideas.goal_to_dev`; the way's kind is `start_again`)
    _t("waits_dev", "Waiting for dev"),                            # the lower pile's word: goals done on their own branch, not in dev yet; drawn only while *Lands in dev by itself* is off
    _t("waits_main", "Waiting for main"),                          # the upper pile's word: goals in dev, not in main yet
    _t("plate_press", "Choose the branch"),                        # a plate's hint (the plate says the branch's name): pressed, the branches are dealt to the hand
    _t("branch_new", "A new branch from <dev>"),                   # the card of the lower pile's branches that makes one: its name is written in the card's own field
    _t("branch_warn", "Goals are at work"),                        # the card dealt first when a plate is pressed while goals are at work
    _t("branch_warn_line", "Changing the branch moves where the work still to come lands and is checked; what is done stays where it is."),      # … its foot
    _t("branch_go", "Choose a branch anyway"),                     # … its way
    _t("branch_here", "here now"),                                 # the mark of the branch the plate stands for now
    _t("dev_blocked", "cannot go into <dev>"),                     # a blocked goal's card in the hand: *Lobby cannot go into dev*, its why at the foot
    _t("dev_why_off", "Lands in dev by itself is off: it waits for you"),                                  # a goal done on its branch waits because the setting says so
    _t("dev_no_tests", "This project has no tests, so nothing can show the goal is safe for <dev>: send it with To dev without the tests"),      # no gate to run for the goal
    _t("dev_no_test_ran", "No test ran on <dev> with the goal: nothing shows it is safe for <dev>"),       # the gate ran and no test touched the goal
    _t("dev_red", "The tests are red on <dev> with the goal: <tail>"),                                     # the gate is red on dev with the goal
    _t("dev_could_not_run", "The tests could not run: <why>"),                                              # the gate could not start
    _t("dev_conflict", "<dev> conflicts with <branch> in <files>"),                                        # dev does not merge into the goal's branch
    _t("dev_task_running", "That goal still has a task running"),                                          # refused: a task of the goal is at work
    _t("dev_no_branch", "That goal has no branch waiting for <dev>"),                                      # refused: the goal is in dev already or never had a branch
    _t("dev_not_done", "That goal is not done: its last step is not accepted yet"),                       # refused: more steps to go
    # -- a red gate's Fix it, by where the goal is (goal "The battle and the gate" G, H; decisions §303.5). <tests> the failing tests, <way> dev or main --------
    _t("fix_stage", "Run its stage again"),                        # Fix it on a goal unmerged on its own branch whose way to dev went red: sealed, one task added, the goal at work (`ideas.gate_fix_stage`)
    _t("fix_stage_task", "Make the failing tests pass: <tests>"),   # … the one task it adds to the goal's plan
    _t("fix_goal_title", "Fix: <tests>"),                           # Fix it on a goal done whose way to main went red: the new goal it lays in one press, its first line (`ideas.gate_fix_goal`)
    _t("fix_goal_named", "The failing tests: <tests>"),             # … its Gist's line naming every failing test
    _t("fix_goal_of", "The goal whose way to main went red: <goal>"),     # … and the goal it fixes (`fixes: <slug>` in its page)
    _t("fix_not_done", "That goal is not in dev yet: Fix it runs its stage again"),                        # refused: `ideas.gate_fix_goal` on a goal not done in dev
    _t("fix_in_dev", "That goal is in dev already: Fix it lays a new Fix goal"),                           # refused: `ideas.gate_fix_stage` on a goal done in dev
    _t("fix_not_red", "No test failed on its way to <way>: nothing to fix"),                              # refused: its gate is not red, or named no failing test
    _t("fix_no_party", "This project has no Tech party to fix it"),                                       # refused: a Fix goal is routed to Tech
    _t("to_main_runes", "its goals go through the portal's ring of runes"),                                # what To main does with the cards it takes (nothing moves under reduced motion)
    _t("step_lacks", "its tool cannot do what this step needs"),    # a seat marked ! on a spec's header of steps (spec 168 C4, decisions §283.16.6)
    _t("spec_now", "Now"),                                         # a spec's part as it is, and ...
    _t("spec_will", "As it will be"),                              # ... as the goal will leave it (spec 168 C4, decisions §283.16.6)
    _t("lane_makes", "Those who make"),                            # the implementation's lanes by seats: who makes, ... (spec 168 C4, decisions §283.16.8)
    _t("lane_checks", "Those who check"),                          # ... who checks, ...
    _t("lane_accepts", "Acceptance"),                              # ... the leader's acceptance of the step ...
    _t("lane_sent_back", "Sent back"),                             # ... and the tasks sent back after it
    _t("hearing", "hearing", "hearings"),                         # a goal's card in the middle and the sides its leaders argue, thrown to the one the person takes (spec 120 §1); not a fork, which stays two sections that disagree, nor a council, the Review board's
    _t("sketch", "sketch", "sketches"),                            # a goal's throwaway variants, made by its craft's leader before its spec is written, touched and one picked (spec 121 §1); not a pick, which a task makes inside the work, nor a mockup, the word of the docs' own drawings
    _t("out_of_contract", "out of the contract"),                 # a task whose work goes past what its section promised: it waits for the person
    _t("release_version", "Release a version"),                    # the Release party's act: a version goes out (not a step of a route)
    _t("chronicle", "Chronicle"),                                  # Release's past: a chapter a version, the goals that went through the portal in it and the decisions written in its span (spec 134, decisions §238)
    _t("chronicle_earlier", "Earlier"),                            # the lens's one line: *Earlier: v0.3 · 28 Oct ›* (spec 134 B)
    _t("chronicle_week", "The week of"),                           # a chapter of a project with no version yet: *The week of 3 Nov* (spec 134 A.4)
    _t("history", "History"),                                      # the book's table: the project's past as a grid of goal cards, a row a day (spec 168 G3, decisions §283.16.14)
    _t("history_agreed", "agreed"),                                # the history dated by the day a goal's decision was agreed (the default)
    _t("history_done", "done"),                                    # … by the day its work was done
    _t("history_main", "in main"),                                 # … by the day it went into main
    _t("past", "The past"),                                        # the chronicle read through the open tab, the lich's (spec 150 E2.2, decisions §254.7): its title *The past · through Design · v0.3*
    _t("every_version", "every version"),                          # … no deck picked: every version dealt, newest first
    _t("unreleased", "Unreleased"),                                # … the deck on top: what went through the portal after the last version
    _t("past_search", "Search <party>'s past…"),                   # … its search (*Search the past…* on the Orkmaster's tab)
    _t("past_line", "<party>'s past"),                             # the lich's line in the table's edge, *Design's past ›* (gone with the edge: spec 156 D.5; the word stays for what was written with it)
    _t("project_past", "The project's past"),                      # … on the Orkmaster's tab
    _t("show_on_table", "Show on <party>'s table"),                # a card lifted in the past: that tab, what it touched lit
    _t("open_in_past", "Open in the past"),                        # the conflict's earlier decision: the past, its deck dealt and its card lit (spec 150 E2.1)
    _t("how_works_now", "How it works now"),                      # a goal's row in the chronicle opens the living spec of its part (spec 127, spec 134 A.5)
    _t("changed_by", "changed by"),                                # a spec or a decision a later decision changed: *changed by §238* (spec 134 A.5)
    _t("other_choice", "Other…"),                                  # a question card's last choice: the person's own words
    _t("party_discard", "<party>'s discard"),                      # Release's lane, the discard through the open tab's eyes: *Discard* on the Orkmaster's tab, *Tech's discard* on a party's (spec 156 D.3, decisions §261.7)
    _t("new_decision", "A decision is newer than your last look at this party's past"),   # the muted dot on a party's tab (spec 156 D.5, decisions §261.9)
    _t("checks_before_main", "Checks before main"),                # Release's table while a goal is chosen for main: a skeleton a check (spec 156 D.4, decisions §261.8)
    _t("to_main", "To main"),                                     # merge what is ready in dev into main, by code (the discard's button)
    _t("to_main_untested", "To main without the tests"),          # the card's second act: the goal goes to main with no test run, the only skip (decisions §274.3; `ideas.to_main` `untested: true`)
    # the night's ladder (spec 168 H3, decisions §283.32; settings.py `night_rung`, core/idea_night.py)
    _t("night_slot", "The night"),                                 # the slot's label: when the Board works by itself and how far it goes
    _t("night_rung_off", "Off"),                                   # the lowest rung: the night does nothing
    _t("night_rung_ideas", "Ideas and specs"),                     # Talk and the specs of the goals in line; nothing built
    _t("night_rung_builds", "and the builds"),                     # also builds what was agreed and is ready to build (the old *Work at night*)
    _t("night_rung_proposals", "and the leaders' proposals"),      # also one proposal for each leader picked, three a night at most, to a ready spec, never built without a press
    _t("proposed", "proposed"),                                    # the mark of a night's proposal in *Specs* until the person's Take or Drop
    # A seat's work (docs/specs/168 I1, decisions §283.16.9)
    _t("seat_log", "log"),                                         # a task's session output, read only, in a terminal's face over the pane; the values of the goal's secrets are masked in it
    _t("own_tool_run", "run in your own AI tool"),                 # a task whose session the host did not see (a skill, decisions §258): the pane says so instead of a log
    _t("secret_mask", "••••"),                                     # what stands in a log in the place of a secret's value
)


SLOTS: tuple[Term, ...] = (
    # -- the Inventory (spec 157 A.5) ------------------------------------------------------------------
    _t("inventory", "Inventory"),
    # -- the inventory as slots (spec 168 H1, H2, decisions §283.30, §283.31): a slot's card and its ways dealt to the hand ---------------------------------
    _t("slot.as_set", "as set"),                                  # the foot of a slot's card: the way it carries is the one set
    _t("slot.cheaper", "A cheaper way exists"),                   # the coin on a slot's card
    _t("slot.fixed", "fixed"),                                    # a slot the project fixes (Release's hero and gate)
    _t("slot.no_choice", "no choice"),                            # a slot with one way only (a hero its craft has no other for)
    _t("slot.default", "Default"),                                # a way among the others: what the slot goes back to
    _t("slot.pick", "The Orkmaster's pick"),                      # the star on a way
    _t("slot.not_here", "not here"),                              # a way the host says cannot be taken, with its why
    _t("slot.put_back", "Put it back"),                           # the ways dealt go back to the table, nothing sent
    _t("slot.build_starts", "The build starts"),                  # `autostart` and `look_wait` as one setting: at once, in 30 min, in 2 h, tonight, by hand
    # -- a leader's ways of answering (spec 168 H4, decisions §266.5, §283.22, §283.33): one word each, and the veto card's two ways --------------------------
    _t("way.pen", "Pen"),                                         # the leader asks; the person answers in their own words each time
    _t("way.choice", "Choice"),                                   # the leader offers its ways; the person picks one
    _t("way.fork", "Fork"),                                       # its ways worked out (gains, costs, risks) in one more call a question, on the elder tier; its price on the card
    _t("way.silent", "Silent"),                                   # the leader decides and lays a card the person can overrule; never for going into main, money, dropping or holding a goal, a decision against an earlier one
    _t("way.accepted", "Accepted"),                               # the veto card's way: the decision stands as it is
    _t("way.replay", "Replay"),                                   # the veto card's way: the question comes back with its ways
    _t("way.decided", "decided"),                                 # the sign on the veto card of what a leader decided itself
    _t("hero", "hero", "heroes"),
    _t("hero.yours", "Yours"),
    _t("hero.yours_before", "Yours before"),
    _t("hero.back_to_default", "Back to default"),
    _t("hero.in_your_hand", "in your hand"),
    _t("hero.what_leaves", "What leaves this computer"),
    _t("hero.lay_tables", "Lay the tables"),
    _t("hero.frame", "frame", "frames"),
    _t("hero.uni-ost", "Angel Invest Knight"),
    _t("hero.uni-jtbd", "Jobwise Knight"),
    _t("hero.uni-shape", "Appetite Knight"),
    _t("hero.uni-pillar", "Pillar Knight"),
    _t("hero.dry-heur", "Pixel-Perfect Dryad"),
    _t("hero.dry-sprint", "Sprint Dryad"),
    _t("hero.dry-a11y", "Inclusive Dryad"),
    _t("hero.sh-c4", "Sh.man"),
    _t("hero.sh-xp", "Spike Shaman"),
    _t("hero.sh-scene", "Scene Shaman"),
    _t("hero.imp-obs", "Lantern Imp"),
    _t("hero.fairy-aarrr", "Growth Hack Gnome"),
    _t("hero.fairy-pos", "Position Gnome"),
    _t("hero.fairy-aso", "Store Gnome"),
    _t("hero.uni-mda", "Dungeon Master Knight"),
    _t("hero.uni-econ", "Economy Knight"),
    _t("hero.dry-sprite", "Sprite Dryad"),
    _t("hero.release", "Release Night King"),
    # -- a way's kind (spec 168 J1, realm/way_kinds.py): the owner's picture of it is `pictures/<kind>.png` --------
    _t("way_kind.replace", "Replace"),
    _t("way_kind.keep", "Keep"),
    _t("way_kind.smaller", "Smaller"),
    _t("way_kind.later", "Later"),
    _t("way_kind.drop", "Drop"),
    _t("way_kind.split", "Split"),
    _t("way_kind.go_on", "Go on"),
    _t("way_kind.mitigate", "Mitigate"),
    _t("way_kind.accept_risk", "Accept the risk"),
    _t("way_kind.ask_more", "Ask more"),
    _t("way_kind.leader_decides", "The leader decides"),
    _t("way_kind.start_again", "Start again"),
    _t("way_kind.take", "Take"),
    _t("way_kind.not_a_problem", "Not a problem"),
    _t("way_kind.make_it_a_goal", "Make it a goal"),
    _t("way_kind.other", "Your own words"),
)
