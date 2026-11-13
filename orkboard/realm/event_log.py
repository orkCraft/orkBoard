"""📒 The local event log (docs/design/dogfood-logs.md §3): every product event, exact, on this machine, and to the project's own remote only when it asks.

    event_log.record(root, event_log.ASKED, building="pool", ork="Grunt", task="t1", text="Which port?")
    event_log.read(root, since="2026-10-14")       # the lines, oldest first
    event_log.counts(root, since="2026-10-14")     # {event: how many}
    event_log.summary(root, since=…)               # the counts the owner reads after a week (`orkcraft usage local`)

It sits beside the anonymous usage stats (core/usage.py) and is not them: whatever the person said to sharing,
these lines are written to `.orkcraft/usage/events.jsonl` in the town's folder and no longer leave the machine by
themselves — no proxy, no batch: they go to the project's own remote only when `[journal]` in orkcraft.toml asks for
it (realm/remote_journal.py, decisions §229). They may hold the town's own words (a question an ork asked, its options), because
only the person who owns the town reads them, by hand or in the analytics zip (realm/analytics.py).

A closed list of events (`EVENTS`); an unknown one is not written. A field is kept as it is when it is plain data
(a string, a number, a bool, a list of strings); a string is cut at `TEXT_MAX`. Writing never troubles the town:
a disk that refuses is ignored. Nothing is written in the demo (the caller passes no root).

No face here: a service records, a face reads (decisions §8: these counts size the way to ask after a week).
"""
from __future__ import annotations

import datetime as dt
import json
import threading
from collections import Counter
from pathlib import Path
from typing import Any

PATH = Path(".orkcraft") / "usage" / "events.jsonl"
TEXT_MAX = 2_000

# The way to ask (ork-console.md §4, §20): what an ork asked, marked, was answered, and where a run stopped.
ASKED = "question_asked"          # building, ork, task, harness, text, options, via ("block" | "line"), at_work
ASSUMED = "assumption_marked"     # building, ork, task, harness, text, at_work (the person's working hours held)
ANSWERED = "question_answered"    # building, ork, task, who ("person" | "steward" | "timer"), waited_s, text
STOPPED = "run_stopped_on_question"   # building, ork, task, harness: the run ended to wait for the person
# A wait the person skipped (ork-console.md §19): which wait, and how long it had lasted.
WAIT_SKIPPED = "wait_skipped"     # building, task, wait, waited_s
# Quiet working hours (audience.md §2a): a question's toast or push held for "since your last look".
HELD_AT_WORK = "question_held_at_work"   # how ("toast" | "push"), title
# Leaving the camp (audience.md §2a): "I'm off", and back (by the person, at evening, or the work done).
CAMP_LEFT = "camp_left"           # carts, first, cap_pct, until, on_power
CAMP_BACK = "camp_back"           # why ("person" | "evening"), minutes, window_pct, capped, carts_left
# Mission 1 (first-mission.md): a quest started, done or skipped.
QUEST_STARTED = "quest_started"   # quest
QUEST_DONE = "quest_done"         # quest, seconds
QUEST_SKIPPED = "quest_skipped"   # quest
# "Since your last look" (audience.md §2a): what the town made while the person was away, and their looks.
BUILT = "result_built"            # building, kind ("passed" | "launched" | "done"), title, ref, tokens, cost (None: unrecorded)
CART_MOVED = "cart_moved"         # source, target, title: a cart delivered along a road
LOOKED = "look"                   # started, seconds: the GUI in front of the person (looks a day, their length)

# The board (docs/specs/33-v1-shell.md §9): every action of the v1 shell, for the day's analysis. `device` is "desktop" or "phone".
IDEA_ADDED = "idea_added"         # idea, track, chars, now (the keeper reads it at once), priority, queue, photos (how many came with it), files (how many `@path` it named, spec 107 K), lens (the kinds pointed at), device,
#                                    type (its goal type's id, else ""), asks (how many answered), refs (how many pictures were Refs'), joined (the agent, else ""), out (the member, else "") (spec 52 §2.7),
#                                    offered (how many types the party offered), near (how many of them with someone missing) (spec 59 §5)
IDEA_SAID = "idea_said"           # idea, section, chars, text, device (the person's turn to the Taskmaster)
KEEPER_STATE = "keeper_state"     # idea, state, was, seconds in the previous state
PLAN_MADE = "plan_made"           # idea, tasks, todos, usd_low, usd_high
PLAN_PASSED = "plan_passed"       # idea, tasks, device, seconds from plan_made, by ("person" · "auto"), risk, priority, via (where the press was: gui/ideas_args.py VIA, else "idea"), pace (by auto: it goes on by day, the week having room),
#                                    joined (the agent who joined at the press, else ""), missing (how many kinds the plan missed when it passed) (spec 52 §2.7)
PLAN_STARTED_NOW = "plan_started_now"   # idea, device, via (gui/ideas_args.py VIA, else "idea"), held (how many tasks the reserve or the week held; old lines none): a plan held for the night, or its tasks held by the reserve, started now (spec 41 §4)
IDEA_QUEUED = "idea_queued"       # idea, queue ("now" · "night"), device, via (gui/ideas_args.py VIA, else "idea") (spec 41 §4)
RESULT_SEEN = "result_seen"       # idea, device: a done goal's result opened from the discard, the goal in the history (spec 98 §2.2)
TODO_DONE = "todo_done"           # idea, todo, kind, device, seconds since the plan, skipped (gone without it), words (a file described instead) (a secret's value never; spec 54 §1.3)
TASK_STATE = "task_state"         # idea, task, state (waiting · ready · held · running · testing · picking · review · merged · failed · dropped: the person's Drop), was, round, tier, role, seconds in the previous state, tokens, cost, ran_tier, effort,
#                                    check (true: a check task's), clean (true: a check that found nothing, merged with no commit; spec 43 §1.3),
#                                    ran_why (running only: why it ran on another tier than planned, else ""; spec 107 §2.3), error (failed, or review with one: its words, cut at 600)
TASK_PAGES_PUT_BACK = "task_pages_put_back"   # idea, task, files: the Board's pages a task edited, restored by code at the gate (spec 143 A)
CHECK_DONE = "check_done"         # idea, task, by (the checker's slug), found, fixed, left, round, cost: a round of a check task ended with findings read
RESULT_READY = "result_ready"     # idea, task, round, passed, failed, files, added, removed, cost, role, exit (the gate's), verdict (green · red · could_not_run · docs · nothing: spec 107 §1.2)
GATE_RAN = "gate_ran"             # idea, task, round, attempt, command, exit, seconds, verdict (as result_ready's), missing (what a run that could not run found missing, else ""),
#                                    linked (how many dependency folders lay linked in the worktree): one per try of the gate (spec 107 §1.2); red_before, flaky (tests of the run red on the base too / green run again alone: spec 149 E)
RESULT_DECIDED = "result_decided"  # idea, task, round, decision (merge · back · fix · drop · install · test again), why, why_kind (on a send back: "suggested" the line the face wrote · "typed", spec 107 §1.4), into, pushed, conflict, device,
#                                    seconds from result_ready, dear (on a merge: the person said it cost too much for this, spec 36 §4)
TASK_STOPPED = "task_stopped"     # idea, task, device
TASK_SKIPPED = "task_skipped"     # idea, task, device: a task taken out of its plan before it ran (a check skipped)
CHECK_SKIPPED = "check_skipped"   # idea, by (the checker), skipped (false: taken again), task ("" before a plan), usd (what it spares), device
STOP_ALL = "stop_all"             # count, device
INTO_CHANGED = "into_changed"     # branch, push, device
GATE_MERGED = "gate_merged"       # commits, ideas, files (what dev held that main lacked), how ("fast-forward" · "merge"), pushed, into, main, device (spec 49 §2.1: dev merged into main)
GOAL_TO_MAIN = "goal_to_main"     # idea, goals (the slugs it took into main: it and what it stood on), commits, files, pushed, into, main, tests ("run" · "skipped": To main without the tests, decisions §274.3), checks_s (the checks' seconds, when they ran), device (spec 105 §5: a goal sent to main on its own)
PICK_ASKED = "pick_asked"         # idea, task, n, media (image · audio · video · text), round (spec 51 §2.4: a task left variants for the person to pick from)
PICK_ANSWERED = "pick_answered"   # idea, task, key (the variant's letter; null: none of them, new ones asked), note_chars, via (hand · front · drawer · screen; else idea), seconds from pick_asked, device, round (the round that was answered)
#                                    tool (maker's id), cost ({amount, currency, estimate}, from pick.json), only for a maker's pick; no prompt, credential or file
IDEA_FLAGGED = "idea_flagged"   # idea, goal (its party), by ("gate" · "done"), tasks, first_time, usd, days (spec 50 §2.2: a goal raised its flag in main)
OPENED = "opened"                 # what (idea · plan · todo · task · result · tab · map · recap · flag · week · push · party · gate · today · pick), ref, via (map · board · needs · agents · review · recap · week · flags · push · hand · front · party · today · gate; old lines ""), device
CANVAS_MADE = "canvas_made"       # tool (claude · codex · agy), kind (design · slides · document · page · picture), task ("" outside a task) (spec 78 §2)
SHOT_TAKEN = "shot_taken"         # idea, task, ok, why ("" · no preview · no page · no browser · no picture), seconds, round (spec 85 §3: the picture of what a task changed)
PLAY_STARTED = "play_started"     # seconds, ok, why ("" · no preview · did not open · nopage · could not make its worktree: …), command (what the preview ran, else ""), url (the page it opened, else ""), tail (a failed start: the command's last output, cut at 600) (spec 88 §5: the project's preview of dev opened in Play; spec 107 §2)
PLAY_STOPPED = "play_stopped"     # why (stopped · idle · closed · quit · again · exited) (spec 88 §5)
MAP_OPENED = "map_opened"         # lens (system), party, parts, changed (parts marked), hours (since the device's last look; None for none), device (spec 89 §4: a leader's map opened)
MAP_PART_PRESSED = "map_part_pressed"   # lens, party, changed (its change since the last look: new · changed · gone · ""), goals (n), device (spec 89 §4)
MAP_SNAPSHOT_FAILED = "map_snapshot_failed"   # commit (12), why (spec 89 §1: the parts not kept after a landing; the landing stands)
CANVAS_SEEN = "canvas_seen"       # device: a canvas folded into Seen (spec 78 §3)
LIMITS_READ = "limits_read"       # provider, left, window
# Round 2 (docs/specs/34-v1-round-2.md §4): goals by dialog, agents by task type.
GOAL_SAVED = "goal_saved"         # goal, new, metrics (their names), links, priority, device, party (the id of the saved party it was picked from, else ""),
#                                    joined, out (the agent who joined, the member who left, else ""), via ("type": New goal by its type · "plan": a plan's stop · "": Edit the party) (spec 52 §2.7),
#                                    preset (the library's party the seats started from, else ""), stages ("<builders>/<checkers>": the leader's seats) (spec 59 §5), tool (the party's AI tool id, else "": the Main tool) (spec 81), tools (each seat's own AI tool, as "<agent>:<tool>" strings: an event keeps no map of words) (spec 91 §6)
GOAL_ACCEPTED = "goal_accepted"   # goal, met, by (its leader's name), and the call's measure
GOAL_READ = "goal_read"           # goal, state (asks · ready · raw: not read), seconds the keeper took, tier, effort
ROLE_SAVED = "role_saved"         # role, model, max_parallel, new, device, kinds (the types it takes), instruction_chars
ROLE_DROPPED = "role_dropped"     # role, kinds (the task types sent back to Grunt), device
KIND_SET = "kind_set"             # kind, role, device
# Spec 35 §12: the Board writes and starts what is safe (its night went: spec 99 §3).
BOARD_SET = "board_set"           # target, autostart, night, device
IDEA_DRAFTED = "idea_drafted"     # idea, risk, triggers, questions, tier, effort, seconds
IDEA_ANSWERED = "idea_answered"   # idea, answers (how many), picked, recommended, typed, decided, from ("hand": the lifted card's answers · "open": after Open…; else absent) (spec 41 §10, spec 158)
GOAL_ANSWERED = "goal_answered"   # goal, answers, picked, recommended, typed, decided, device, from (as idea_answered) (spec 41 §10, spec 158)
# … and every keeper event (goal_read, idea_drafted, idea_answered, idea_said, plan_made, night_run) carries §0's
# step, prompt_chars, tokens ({"in", "out", "cache_read"}) and cost (null when unpriced, never 0)
KEEPER_STOPPED = "keeper_stopped"  # idea (the person stopped the keeper's run on it)
NIGHT_RUN = "night_run"           # no longer written (spec 99 §3: the night is gone); old lines are still read (recap, week): drafted, started, refreshed, proposed, held, paced (the Board's Low ideas the week's pace left for later), seconds
PROPOSAL_MADE = "proposal_made"   # no longer written (the night proposed them); old lines are still read: idea, goal
PROPOSAL_ANSWERED = "proposal_answered"   # idea, take, has_reason
BOARD_COMMITTED = "board_committed"   # commit, pages, what, seconds (spec 35 §13: the Board's pages on the work branch)
BOARD_HELD = "board_held"         # why (the work branch could not move to the Board's commit)
# Spec 37 §8: the project, as in an IDE (in the project's own log).
PROJECT_OPENED = "project_opened"   # new (never opened on this machine), git, device
PROJECT_CLOSED = "project_closed"   # stopped (its running tasks were stopped)
FILE_SAVED = "file_saved"         # kind (markdown · text), bytes: never the path or the text
GIT_COMMITTED = "git_committed"   # files (how many), device
GIT_PUSHED = "git_pushed"         # branch, device

# Spec 43 §4: the night's proposal to take a checker out of a goal's party, and the person's answer.
PARTY_PROPOSED = "party_proposed"   # no longer written (the night proposed them); old lines are still read: goal, by (the checker's slug), runs
PARTY_ANSWERED = "party_answered"   # goal, by, take, has_reason, device

# Spec 44 §4: the Claude week came back; what was left of it unused.
WEEK_RESET = "week_reset"         # left (the share left, read just before it came back), provider

# Spec 43 §6: the person's own parties, saved from a goal and picked again in any project.
PARTY_SAVED = "party_saved"       # party (its id), members, own (agents of the person's own it carries), replaced, device
PARTY_DROPPED = "party_dropped"   # party, device
PARTY_REMOVED = "party_removed"   # slug, title, moved, dropped, face (a project's party removed, spec 80), device
NIGHT_ALLOWED = "night_allowed"   # no longer written (`ideas.night_allow` only stores the answer, spec 99 §3); old lines are still read: allow (Low work may run at night), moved (goals taken off the night), face, device (spec 83)

# Spec 62 §4.4: the spec after the start: a section written by hand, the plan change the leader proposes, and the answer.
IDEA_EDITED = "idea_edited"       # idea, section, chars, passed (its plan was passed), device: a section written by hand
PLAN_REVISED = "plan_revised"     # idea, changed (the sections it was made for), added, changed_n, dropped, usd_low, usd_high (what it adds; negative when it saves),
#                                    and the call's measure (step, prompt_chars, tokens, cost): the leader's plan change was saved
PLAN_CHANGE_ANSWERED = "plan_change_answered"   # idea, take, added, changed_n, dropped (taken: what was applied; kept: what was proposed), left (how many of its tasks had started meanwhile), via (gui/ideas_args.py VIA, else "idea"), device

# Spec 65 §6: Ideation's pitches judged, sent, passed and judged again (never a pitch's words).
PITCH_JUDGED = "pitch_judged"     # goal (the pitch), answer (invest · reshape · pass), kills (their ids), tokens, cost, seconds
PITCH_SENT = "pitch_sent"         # goal, to (the party), type (its goal type, else ""), as_decided (the party the Investor named), device
PITCH_PASSED = "pitch_passed"     # goal, as_decided (the Investor said pass), has_reason, device
PITCH_AGAIN = "pitch_again"       # goal, changed (its words were changed), device

# Spec 68 §4: a goal's route across parties, a release (A release) made and out, a party switch (never a goal's words).
IDEA_MOVED = "idea_moved"         # goal, from, to (parties), device
RELEASE_MADE = "release_made"     # goal, party, goals (n), parties (n), device
RELEASE_OUT = "release_out"       # goal, goals (n), days (from its first goal's flag to out; None when no flag is dated), device
PARTY_SHOWN = "party_shown"       # from, to (parties), face (desktop, phone), device

# Spec 71 §5: the Orkmaster keeps the parties from colliding (never a goal's words: the pair is its two slugs).
COLLIDE_FOUND = "collide_found"   # pair ("a|b", sorted), by ("plan" · "change"), judged (the judge answered), collide (it said they collide), tokens, cost
COLLIDE_ANSWERED = "collide_answered"   # pair, answer ("first:<slug>" · "one" · "replan" · "leave"), device

# Spec 75 §4.4: the Orkmaster fits the parties to the project (never the person's line: only the kind it was read as).
PROPOSALS_SHOWN = "proposals_shown"   # kind (id), n (proposals), ask (an empty folder asked its line), read (the line was read by the model; None without a line), device
PROPOSAL_TAKEN = "proposal_taken"     # kind (id), recipe (id), size (lean · standard · full), device
PARTY_RESIZED = "party_resized"       # party (slug), from (lean · standard · full · ""), to, joins, leaves (the agents that came and went with it, spec 81 §3), device

# Spec 42 §3: notifications to a paired phone (counts and tags, never a word of the push).
PUSH_SET = "push_set"             # on, device
PUSH_SENT = "push_sent"           # tag, devices, gone

# Spec 45 §7: a tool's own sign-in (how often and how fast, nothing more).
SIGN_IN_NEEDED = "sign_in_needed"   # harness, where (task · draft · plan · op · check · ask)
SIGNED_IN = "signed_in"             # harness, by (browser · terminal · elsewhere), s (seconds from the episode's start)
SIGN_IN_FAILED = "sign_in_failed"   # harness, why (timeout · cancelled · refused · no_browser · check)

# Spec 105 §2.5, §3: the work moved to another tool (or back), and the person's answer to *Go on paid?* (never a word of theirs).
TOOL_MOVED = "tool_moved"         # from, to (tool ids; to is "" while every tool is out), until (epoch seconds the Main tool is back, else None)
PAID_ANSWERED = "paid_answered"   # tool, yes (go on, paid) or no (wait), device

# Spec 106 (decisions §181.7): a quick question on the open tab, and the press that turns its answer into a goal.
BOARD_ASKED = "board_asked"       # party (its slug, or "orkmaster"), chars, text (the question, cut at 300), ok (it was answered), seconds, step, prompt_chars, tokens, cost
LEADER_CHANGE_ASKED = "leader_change_asked"   # idea, party, shape ("plan" · "looks"), chars (the person's words), ok (the leader answered), changed_n (its tasks it changes), step, prompt_chars, tokens, cost
LEADER_CHANGE_ANSWERED = "leader_change_answered"   # idea, party, take (Accept) or kept (Keep the spec, Talk more), look (the look's key taken, "" for a plan), added, changed_n, dropped, via, device
ASK_MADE_GOAL = "ask_made_goal"   # party ("" for the Orkmaster's tab), device: *Make it a goal* pressed under an answer
ASK_GOT_IT = "ask_got_it"         # party (who answered), tab (where it was asked), device: *Got it* pressed on a quick question's answer card (spec 168 D3)

# Spec 107 §2 (decisions §182.2): what the logs lacked of a day. A command the host refused, and an error the person was shown.
COMMAND_REFUSED = "command_refused"   # command, error (cut at TEXT_MAX), device (desktop · phone), kind ("refused": the host said no · "broken": it raised); never the arguments
ERROR_SHOWN = "error_shown"       # title, text: a toast of severity error the person was shown
# Spec 108 C (decisions §183.1–§183.3): a leader's verdict in Talk, and the person's answer to its no (never a word of theirs or of the leader's).
LEADER_OBJECTED = "leader_objected"          # idea, party, verdict ("doubt" or "no"), has_instead (it named a smaller or other goal that would serve)
OBJECTION_ANSWERED = "objection_answered"    # idea, party, answer ("drop", "smaller", "later" or "go": the person went on anyway)
# Spec 108 A (decisions §183.4–§183.6, §183.8): a leader's look at its own map, and what the person did with its concerns (never a word of the leader's or the person's).
CONCERNS_MADE = "concerns_made"      # party, n (concerns kept), alerts, notes, signals (hints of code it was given), seconds, cost (None: unrecorded), why ("open" · "again"), since (the evening line's way: toward · away · unclear, else "": spec 121 §6)
CONCERN_OPENED = "concern_opened"    # party, level: a concern's back was opened on its map
CONCERN_GOAL = "concern_goal"        # party, level, idea: *Make it a goal* pressed on a concern
CONCERN_DISMISSED = "concern_dismissed"   # party, level: *Not a problem* pressed on a concern
CONCERN_LATER = "concern_later"         # party, level: *Later* pressed on a concern (spec 168 D4)
# Spec 121 C (decisions §199.4): Work at night. A plan that would start by itself waits for the night's window, starts in it, or is built now by day.
NIGHT_HELD = "night_held"         # idea: a plan that would have started by itself was held for the night's window (once for each hold)
NIGHT_STARTED = "night_started"   # idea (its line's own `at` is the time it started, in the night's window): a held plan was passed when the window opened
BUILT_NOW = "built_now"           # idea, from ("card": Build it now on a held plan · "sketch": Pick and build now), device: a goal built by day that Work at night held
# Spec 121 D (decisions §199.5): the morning's card, and Play opened on a screen (the time to the first mark is read from `play_mark`; never a word of anyone's).
NIGHT_CARD_OPENED = "night_card_opened"   # goals (how many goals the night's record held), device: the morning's card was lifted
PLAY_AT_PATH = "play_at_path"     # idea ("" when the press had no goal), path (the page's path Play was asked to open first, cut), device: *Play it* on a goal's screen
# Spec 121 A (decisions §199.3): a goal's sketch, made before its spec by its craft's leader. Never a word of the goal's, the leader's or the person's (the note is counted, as a pick's is).
SKETCH_MADE = "sketch_made"             # idea, craft ("design" · "game-design" · "art"), kind ("page" · "image" · "audio"), n (variants), round, seconds, cost (None: unrecorded)
SKETCH_ANSWERED = "sketch_answered"     # idea, answer ("picked" · "again" · "skipped"), round, minutes_since_goal (from the goal's being added to the answer; None when unknown), note_chars, via, device
SKETCH_SKIPPED = "sketch_skipped"       # idea, why (a few words: "the person said no" · "the media tools are not set up" · "it would be paid" · "the window is spent" · "the call failed" …)
# Spec 120 D (decisions §198.6): a hearing thrown to a side (never a word of the goal's, a leader's or the person's).
HEARING_THROWN = "hearing_thrown"    # idea, moment ("talk" or "fork"), kind ("go" · "drop" · "smaller" · "later" · "side" · "own"), dir ("right" · "left" · "up" · "" for the person's words), leaders (how many stood on that side)
# Spec 120 (decisions §198): a goal heard at the Orkmaster. Never a word of a leader's or the person's.
TALK_HEARD = "talk_heard"        # idea, party, weigher (Product weighing a goal it is not routed on)
TALK_GROUND = "talk_ground"    # idea, party, settled (a leader's doubt looked up in the code: true when what was found settled it)
TALK_VERDICT = "talk_verdict"    # idea, party, before, after (a leader's verdict after the person's answers: go · doubt · no)
RIPE_STARTED = "ripe_started"    # idea, seconds (the wait), priority, risk
ROUTE_HELD = "route_held"        # idea: **Hold** on the route card, nothing starts it until the person's Talk (spec 130 E.3)
RIPE_HELD = "ripe_held"          # idea, left_s (what was left of the wait when it was held), why ("person" · the reason a spent window or a stop gave)
RIPE_DONE = "ripe_done"          # idea: the wait ended and the leaders' decision was written

# Spec 125 D (decisions §203): a leader's digest of its own journal, written in the background. Never a word of the journal or of the digest.
JOURNAL_DIGESTED = "journal_digested"   # party, entries (how many the call read), chars (of the digest kept), seconds, cost (None: unrecorded), why (done, ask, open or add: what began the view), dropped (how many lines were dropped; a count, never a word)

# Spec 167 I: a leader's view opened on its tab (H6's signal). Never a word of the view.
VIEW_OPENED = "view_opened"   # party, at (the view's date, "" when it has none)

# Spec 131 A (decisions §233): a decision cut into the leaders' slices, and a leader's fold of the slices past the bound, both in the background. Never a word of a decision or of a slice.
SLICES_CUT = "slices_cut"        # decision (its number), parties (how many got a slice), none (how many none), replaced (slices replaced), seconds, cost (None: unrecorded), failed (true: nothing kept)
SLICES_FOLDED = "slices_folded"  # party, slices (how many the call read), chars (of the digest kept), seconds, cost (None: unrecorded), failed (true: nothing kept)

# Spec 127 C (decisions §205): a goal that reached main folded into the product's living specs, in the background. Never a word of the goal or of a spec.
SPEC_FOLDED = "spec_folded"   # idea, capability (its slug), added, modified, removed (how many requirements), cost (None: unrecorded)

EVENTS = (ASKED, ASSUMED, ANSWERED, STOPPED, WAIT_SKIPPED, HELD_AT_WORK, CAMP_LEFT, CAMP_BACK, QUEST_STARTED,
          QUEST_DONE, QUEST_SKIPPED, BUILT, CART_MOVED, LOOKED, IDEA_ADDED, IDEA_SAID, KEEPER_STATE, PLAN_MADE, PLAN_PASSED,
          TODO_DONE, TASK_STATE, CHECK_DONE, RESULT_READY, GATE_RAN, RESULT_DECIDED, TASK_STOPPED, TASK_SKIPPED, CHECK_SKIPPED, STOP_ALL, INTO_CHANGED, GATE_MERGED, GOAL_TO_MAIN, IDEA_FLAGGED, PICK_ASKED, PICK_ANSWERED, OPENED, LIMITS_READ, GOAL_SAVED, GOAL_READ, GOAL_ACCEPTED, ROLE_SAVED,
          ROLE_DROPPED, KIND_SET, BOARD_SET, IDEA_DRAFTED, KEEPER_STOPPED, NIGHT_RUN, PROPOSAL_MADE, PROPOSAL_ANSWERED,
          IDEA_ANSWERED, GOAL_ANSWERED, PLAN_STARTED_NOW, IDEA_QUEUED, RESULT_SEEN, BOARD_COMMITTED, BOARD_HELD, PROJECT_OPENED, PROJECT_CLOSED, FILE_SAVED, GIT_COMMITTED,
          GIT_PUSHED, PUSH_SET, PUSH_SENT, PARTY_PROPOSED, PARTY_ANSWERED, PARTY_SAVED, PARTY_DROPPED, PARTY_REMOVED, NIGHT_ALLOWED, WEEK_RESET, IDEA_EDITED, PLAN_REVISED, PLAN_CHANGE_ANSWERED,
          PITCH_JUDGED, PITCH_SENT, PITCH_PASSED, PITCH_AGAIN, IDEA_MOVED, RELEASE_MADE, RELEASE_OUT, PARTY_SHOWN, COLLIDE_FOUND, COLLIDE_ANSWERED,
          PROPOSALS_SHOWN, PROPOSAL_TAKEN, PARTY_RESIZED, CANVAS_MADE, CANVAS_SEEN, SHOT_TAKEN, PLAY_STARTED, PLAY_STOPPED, MAP_OPENED, MAP_PART_PRESSED, MAP_SNAPSHOT_FAILED, SIGN_IN_NEEDED, SIGNED_IN, SIGN_IN_FAILED, TOOL_MOVED, PAID_ANSWERED, BOARD_ASKED, ASK_MADE_GOAL, ASK_GOT_IT, COMMAND_REFUSED, ERROR_SHOWN, LEADER_OBJECTED, OBJECTION_ANSWERED, CONCERNS_MADE, CONCERN_OPENED, CONCERN_GOAL, CONCERN_DISMISSED, CONCERN_LATER, HEARING_THROWN, TALK_HEARD, TALK_GROUND, TALK_VERDICT, RIPE_STARTED, ROUTE_HELD, RIPE_HELD, RIPE_DONE)
EVENTS += (NIGHT_HELD, NIGHT_STARTED, BUILT_NOW)       # spec 121 C
EVENTS += (NIGHT_CARD_OPENED, PLAY_AT_PATH)       # spec 121 D
EVENTS += (SKETCH_MADE, SKETCH_ANSWERED, SKETCH_SKIPPED)       # spec 121 A
EVENTS += (JOURNAL_DIGESTED,)       # spec 125 D
EVENTS += (VIEW_OPENED,)            # spec 167 I
PLAY_MARK = "play_mark"          # spec 121 G (H2): a mark made on Play (`ideas.play_mark`): idea, kind ("bug" · "looks" · "missing" · "confusing"), joined (added to a goal not started), minutes_since_open (the first mark after the morning's card was lifted: the minutes since `night_card_opened`; None for any other mark), device. Never a word of the mark's.
HEARING_UNTHROWN = "hearing_unthrown"    # spec 120 F: a throw taken back (Undo): idea, moment ("talk"), kind (what had been thrown), seconds (since the throw)
EVENTS += (HEARING_UNTHROWN, PLAY_MARK)
QUESTION_PASSED = "question_passed"      # spec 128 D: a leader's question passed through the Orkmaster: idea, party (who asked), to (the party it was for), how ("answered" · "cannot" · "failed" · "taken" · "stopped"), seconds, step, prompt_chars, tokens, cost (never a word of the question)
EVENTS += (QUESTION_PASSED,)       # spec 128 D
EVENTS += (SPEC_FOLDED,)            # spec 127 C
EVENTS += (TASK_PAGES_PUT_BACK,)       # spec 143 A
PLAN_UNCLAIMED = "plan_unclaimed"       # spec 153 C.3: idea, step, lines (the numbers, as strings, of the Done when lines no task of the plan proves, after the plan was asked once more or not), asked_again (bool). Never a word of the goal.
EVENTS += (PLAN_UNCLAIMED,)
EVENTS += (SLICES_CUT, SLICES_FOLDED)       # spec 131 A

# Spec 132 D (decisions §234.3): a goal's findings told by their leaders and sorted by the Orkmaster, in the background. Never a word of a finding.
FINDINGS_TOLD = "findings_told"      # idea (the goal's slug, "" for findings of no goal), party, findings (how many), seconds, cost (None: unrecorded), failed (true: code's words kept)
FINDINGS_SORTED = "findings_sorted"  # idea, findings (how many), levels ({work, spec, decision} counts), seconds, cost (None: unrecorded), failed (true: all left at work)
EVENTS += (FINDINGS_TOLD, FINDINGS_SORTED)       # spec 132 D
STEP_ACCEPTED = "step_accepted"      # spec 152 B.3: idea, step, party, verdict (accepted · back · gone_on), round, back (items sent back), seconds, cost (None: unrecorded), failed (true: the call did not answer); never a word of the goal
EVENTS += (STEP_ACCEPTED,)       # spec 152 B
MEASURE_READ = "measure_read"        # spec 146 C.1 (spec 133 B.3): idea (the hypothesis's id), party, measures (asked), read (kept), seconds, cost (None: unrecorded); never a number
EVENTS += (MEASURE_READ,)       # spec 146 C

# Spec 131 B (decisions §233.5–§233.9): a leader's proposal to change a slice of its own, the cascade it runs in the background, the card's two answers. Never a word of a slice or of a decision.
SLICE_PROPOSED = "slice_proposed"         # party, from_step (the call it came in: talk_round · talk_verdict · section_first · section · plan · accept · ask · finding), dropped ("" kept · open · bad · blocked · gone)
CASCADE_READY = "cascade_ready"           # party, steps (leaders asked), agreed, forks, stopped ("" · steps · price), sections (what follows), changes (decisions changed), seconds, cost (None: unrecorded)
CASCADE_CONFIRMED = "cascade_confirmed"   # party, decision (its number), slices (replaced), forks (answered), sections (written again), left (goals busy), via, device
CASCADE_PUT_BACK = "cascade_put_back"     # party, forks, via, device
EVENTS += (SLICE_PROPOSED, CASCADE_READY, CASCADE_CONFIRMED, CASCADE_PUT_BACK)       # spec 131 B
EVENTS += (LEADER_CHANGE_ASKED, LEADER_CHANGE_ANSWERED)      # spec 128 E
JOURNAL_SENT = "journal_sent"      # decisions §229: the journal sent to the project's remote (or not): sent, remote, branch, files, held_back (lines held for a secret's shape), commit, why (a failure's words, "nothing changed")
EVENTS += (JOURNAL_SENT,)
INBOX_TAKEN = "inbox_taken"      # spec 136 B, decisions §243.4: a goal of the phone's inbox taken (or the inbox not read): id, by, slug (the goal's on the Board, "" when not laid), error (the words, "" when none), ok (False: the fetch or the taking failed)
EVENTS += (INBOX_TAKEN,)
LOOK_WAITS = "look_waits"      # spec 144 A.2, decisions §225.1: a spec made waits for the person's look: idea, until (epoch seconds), choice (30m · 2h · tonight)
LOOK_ENDED = "look_ended"      # spec 144 A.3: the look's wait ended: idea, how ("started" · "night" · "wait")
EVENTS += (LOOK_WAITS, LOOK_ENDED)
SPEC_CHANGE_ASKED = "spec_change_asked"        # spec 144 C.4: a change to a spec asked of the Orkmaster: idea, chars (the person's words), parties (the leaders it went to), ok (the leaders answered), step, prompt_chars, tokens, cost
SPEC_CHANGE_ANSWERED = "spec_change_answered"  # idea, answer ("take" · "more" · "drop"), parties, wrote (the sections written), added, changed_n, dropped, via, device
EVENTS += (SPEC_CHANGE_ASKED, SPEC_CHANGE_ANSWERED)
BOARD_TAKEN = "board_taken"      # spec 137 B, decisions §244.2: this computer (or a run) took the Board's lease: by, kind ("computer" | "cloud run"), files (what the branch held)
BOARD_PUSHED = "board_pushed"      # the Board pushed to its branch (or not): commit, files, held_back (files or lines held for a secret's shape or a size), why (a failure's words, "")
BOARD_REFUSED = "board_refused"      # the lease is held by another and was not taken: by, kind, until (never a word of the Board)
BOARD_GIVEN_BACK = "board_given_back"      # the lease given back: by, kind
BOARD_ASIDE = "board_aside"      # another worker had the Board while this one was away: its changes since `since` kept aside, whole: by, files, since
EVENTS += (BOARD_TAKEN, BOARD_PUSHED, BOARD_REFUSED, BOARD_GIVEN_BACK, BOARD_ASIDE)
CLOUD_RUN = "cloud_run"      # spec 137 D, decisions §244.6: a cloud run ended: taken (it held the Board), stopped ("quiet" | "time" | "ceiling" | "lost" | ""), laid, answered, planned (goals waiting for the work), usd, seconds, given (the lease given back); never a word of the Board
EVENTS += (CLOUD_RUN,)
GOAL_ADDED_TO = "goal_added_to"      # spec 132 A: words added to a goal in analysis (*Add to the goal*): idea, chars, reworded (its decision was worded again), via ("match" · "bubble" · "groups" · ""), element (the rune given that idea), device
DECISION_CHANGED = "decision_changed"      # spec 132 A: the decision's one *Change…*: idea, kept (the person's text, as written), said (worded again by the Orkmaster), device
EVENTS += (GOAL_ADDED_TO, DECISION_CHANGED)
CONFLICT_ANSWERED = "conflict_answered"      # spec 150 E1.3: a decision's conflict answered: idea, number (the earlier decision), choice (replace · keep · other), device
EVENTS += (CONFLICT_ANSWERED,)
GOAL_MATCHED = "goal_matched"        # spec 135 A: a new goal sent from the field looks like part of a face-down goal, offered and not added: idea (the candidate), score, why, reworded, device
GOAL_KEPT_APART = "goal_kept_apart"  # spec 135 A: *Keep apart* pressed on that offer, the goal added: with (the candidate), device
EVENTS += (GOAL_MATCHED, GOAL_KEPT_APART)
BACKLOG_GROUPED = "backlog_grouped"  # spec 135 B: the one call at a reset over the goals put off: goals (how many were given), groups (how many came back), seconds, cost, failed (never a title)
GROUPS_ANSWERED = "groups_answered"  # spec 135 B: the card *These look like one goal* answered: joined (groups), apart (groups), dropped (goals joined into another), not_now, device
EVENTS += (BACKLOG_GROUPED, GROUPS_ANSWERED)
GOAL_MOVED_OUTSIDE = "goal_moved_outside"      # spec 151 A.4: a goal's page was moved to another phase by someone else (an AI tool, a hand): slug, from (its phase before), to, commit ("" when not committed)
EVENTS += (GOAL_MOVED_OUTSIDE,)
GOAL_TAKEN = "goal_taken"            # spec 151 D.1: a goal taken on `orkboard/taken` so no other tool works it meanwhile: slug, by, kind ("orkboard" | "tool"), until
GOAL_TAKE_REFUSED = "goal_take_refused"      # …held by another and not taken: slug, by (the holder), until
GOAL_GIVEN_BACK = "goal_given_back"  # …given back (it waits for the person, or ended): slug, by
EVENTS += (GOAL_TAKEN, GOAL_TAKE_REFUSED, GOAL_GIVEN_BACK)
BOARD_IN_CODE_ANSWERED = "board_in_code_answered"   # spec 151 F.1: the Board in the code answered: answer ("publish" · "off" · "private"), visibility ("public" · "unknown" · "private" …), device
EVENTS += (BOARD_IN_CODE_ANSWERED,)

_LOCK = threading.Lock()


def path(root: Path) -> Path:
    return Path(root) / PATH


def _plain(value: Any) -> Any:
    """A field as it is kept: plain data only, strings cut; None for anything else (it is dropped)."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return round(value, 3) if isinstance(value, float) else value
    if isinstance(value, str):
        return value[:TEXT_MAX]
    if isinstance(value, (list, tuple)) and all(isinstance(v, str) for v in value):
        return [v[:TEXT_MAX] for v in value][:50]
    if isinstance(value, dict) and len(value) <= 8 and all(isinstance(k, str) and (v is None or (
            isinstance(v, (int, float)) and not isinstance(v, bool))) for k, v in value.items()):
        return dict(value)                     # a small count of numbers: a call's tokens (spec 35 §0)
    return None


def line(event: str, at: dt.datetime | None = None, **fields: Any) -> dict | None:
    """The line `record` writes; None for an event not in `EVENTS`."""
    if event not in EVENTS:
        return None
    at = at or dt.datetime.now().astimezone()
    row: dict[str, Any] = {"at": at.isoformat(timespec="seconds"), "event": event}
    for k, v in fields.items():
        if event == PICK_ANSWERED and k == "cost" and isinstance(v, dict):
            # Money has strings, unlike token counts. Keep only its receipt fields.
            money = {name: v[name] for name in ("amount", "currency") if isinstance(v.get(name), str)}
            if isinstance(v.get("estimate"), bool):
                money["estimate"] = v["estimate"]
            row[k] = money
            continue
        kept = _plain(v)
        if kept is not None or v is None:
            row[k] = kept
    return row


def record(root: Path | None, event: str, **fields: Any) -> bool:
    """One event, appended to the town's local log. False when nothing was written (no root, an unknown event,
    a disk that refused)."""
    row = line(event, **fields)
    if root is None or row is None:
        return False
    target = path(root)
    try:
        with _LOCK:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        return False
    return True


def read(root: Path, since: str = "", until: str = "") -> list[dict]:
    """The lines, oldest first; `since` / `until`: ISO days or times (the line's `at` compared as text), inclusive
    of `since`'s day, exclusive of `until`'s."""
    try:
        text = path(root).read_text(encoding="utf-8")
    except OSError:
        return []
    rows = []
    for raw in text.splitlines():
        try:
            row = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(row, dict) or row.get("event") not in EVENTS:
            continue
        at = str(row.get("at") or "")
        if (since and at < since) or (until and at >= until):
            continue
        if row["event"] == OPENED:
            row.setdefault("via", "")           # a line from before spec 39
        rows.append(row)
    return rows


def counts(root: Path, since: str = "", until: str = "") -> dict[str, int]:
    """How many of each event, every event named (0 when none)."""
    found = Counter(r["event"] for r in read(root, since, until))
    return {e: found.get(e, 0) for e in EVENTS}


def summary(root: Path, since: str = "", until: str = "") -> dict[str, Any]:
    """What the owner reads after a week (decisions §8): the counts, and how long the person's answers took."""
    rows = read(root, since, until)
    c = Counter(r["event"] for r in rows)
    waits = sorted(float(r["waited_s"]) for r in rows if r["event"] == ANSWERED and r.get("who") == "person"
                   and isinstance(r.get("waited_s"), (int, float)))
    median = waits[len(waits) // 2] if waits else None
    runs = {(r.get("building"), r.get("task")) for r in rows if r["event"] in (ASKED, ASSUMED)}
    return {"counts": {e: c.get(e, 0) for e in EVENTS}, "answer_wait_median_s": median,
            "tasks_with_questions_or_assumptions": len(runs), "first": rows[0]["at"] if rows else "",
            "last": rows[-1]["at"] if rows else ""}
GOAL_REWRITTEN = "goal_rewritten"      # spec 168 C2, decisions §283.24: a goal's words rewritten with what the person took from its leaders: idea, taken (how many), changed, chars, cost
REWRITE_UNDONE = "rewrite_undone"      # … put back as it was: idea, taken
REWRITE_FORKED = "rewrite_forked"      # … what was taken disagrees, one card of choices instead: idea, ids
SAY_ANSWERED = "say_answered"          # a leader's better or need taken or turned down (spec 168 C1): idea, party, what ("better" · "need"), how ("taken" · "left"), weight, kind
JUDGED_AGAIN = "judged_again"          # the leaders judged again after the person's answers or at *Judge again now* (spec 168 C2, §283.25): idea, parties, round, now (pressed), hearing (the second round ended in a hearing)
TO_HEARING = "to_hearing"              # the person took a goal to the hearing at once (spec 168 D5, §283.25): idea, parties (the leaders that still doubted or said no)
EVENTS += (GOAL_REWRITTEN, REWRITE_UNDONE, REWRITE_FORKED, SAY_ANSWERED, JUDGED_AGAIN, TO_HEARING)
GOAL_TO_DEV = "goal_to_dev"            # a goal went from its own branch into dev (spec 168 F1, §283.26): idea, into
EVENTS += (GOAL_TO_DEV,)
BRANCH_SET = "branch_set"              # a discard plate's branch chosen (spec 168 F2, §283.27): which ("dev" · "main"), branch, was, device
EVENTS += (BRANCH_SET,)
MOVE_PLAYED = "move_played"            # a one-press move of the hand played, its Undo kept (spec 171 D, §302.4): idea, kind (core/idea_undo.py), from ("hand" · "mat" · ""), device
MOVE_UNDONE = "move_undone"            # … put back from the history: idea, kind
EVENTS += (MOVE_PLAYED, MOVE_UNDONE)
