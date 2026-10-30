# 115. The live product under each leader's eyes: Play as a map, marks on it, hints by code

Decisions §193 (to be written at the owner's yes on `docs/mockups/play-lenses/`). The owner: *Play today is only to poke at
the product and come back with an idea. I propose to gather feedback while working with the running project: what is pressed
and how, cards on the interface where there are doubts, the technical logs, and above all the person can always pick an area
of a page or a screen of the product and pick the problem (the party's leader, and a question or a complaint): a bug, the
wrong design, a feature to hand over.* And then: *it is the same work as with the leaders' lenses, where you leave comments,
but done right on the live product.* **Builds:** Claude (the cheaper model builds, the spec's author reviews) · **Review:**
full · P1. After spec 113 (the preview known) and spec 109 (the rubrics). **Waves** (parts in a wave share no file): **1** A,
B, C; **2** D; **3** E (after the owner's yes on the mockup).

**What it is, and is not:** Play is **one more map, the product itself, shared by every party**: under a party's tab it is
seen through that leader's lens (its map's parts on this screen, its concerns, its aspects), and the person marks a place on
it the way a party's map is picked (spec 102 §6), the mark carrying what the live product knows and a map does not (the
screen, the element, the commit, the errors, the requests, the server's last lines, a picture of the moment). What the
probe sees by rule (an error, a failed or slow request, a press that did nothing, a press again and again) is **a hint**, as
the maps' hints of code are (spec 109 §3), shown in the lens of the party whose aspect it is. Not: **analytics of real
people** (a project's live users: a later spec reads PostHog, Sentry or Firebase into Product's, Run's and Marketing's maps;
on dev the only player is the person, and a heat map of one says nothing); **a recording of the session** (rrweb's replay:
later, when a bug's mark shows it is wanted); **a native app on a device** (Play is the machine's web preview; an Expo or
Flutter web build is a web build and is covered); **the phone** (it has no Play: spec 112 §3.3); **a new pane, column or
drawer** (decisions §104.0, §145).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The probe and its proxy** | Play's page goes through the host, which puts a small script in every HTML answer; the script tells the page where it is, what is under a box, and what went wrong | new `gui/play_proxy.py`, new `gui/static/play/probe.js` (served by the proxy alone), `gui/ideas_assets.py` (`Play`: its `url` the proxy's; the command's lines kept with their time), new `gui/static/vendor/rrweb-snapshot/` (unchanged, its licence beside it, a line in `NOTICE`); new `tests/test_play_proxy.py`, new `tests/test_play_probe_browser.py` |
| **B. Where you are** | the page's path → Design's screen; the element's file → the parts of every map | new `realm/play_place.py`, `realm/screen_map.py` (`screen_of`, public: today's `_target` on the newest screens); new `tests/test_play_place.py`, `tests/test_screen_map.py` |
| **C. Hints by code** | the probe's events → hints of kinds, each in one craft's aspect | new `realm/play_signals.py`, `realm/lens_rubrics.py` (the kinds in their aspects), `realm/lexicon.py`; new `tests/test_play_signals.py`, `tests/test_lens_rubrics.py` |
| **D. The mark** | a box on the live product, a line, a kind, the party → a goal with its marks, its screen lens and its play | new `gui/ideas_play_mark.py` (`ideas.play_mark`, `ideas.play_place`, `ideas.play_hints`), `gui/ideas.py` (the commands' table), `realm/idea_lens.py` (a screen taken from Play), new `realm/idea_play.py` (`play.json` beside the goal, read into its calls), `realm/goal_route.py` (a bug's mark with its failure `reproduces`); new `tests/test_gui_play_mark.py`, `tests/test_idea_play.py`, `tests/test_goal_route.py` |
| **E. The faces** | the lens strip over Play, the concerns and hints on the frame, *Mark*, the mark's field | `js/arena/play.js`, new `js/arena/playlens.js`, new `js/arena/playmark.js`, `js/arena/play.css`, `js/frame/state.js` (Play stays open when the tab changes); new `tests/test_play_lens_browser.py`, `tests/test_play_mark_browser.py` |

## 0. What is there today

- **Play** (spec 88 §5, spec 112, `js/arena/play.js`, `gui/ideas_assets.py` `Play`): dev's head in a worktree, the
  project's preview command on a port, its page in an `iframe` over the pane (sandbox `allow-scripts allow-same-origin
  allow-pointer-lock`). The frame's origin is the preview's (`127.0.0.1:<port>`), not the page's: **the page can read
  nothing inside it**. The command's last 30 lines are kept (`idea_shot` `tail`) only to say why a build did not start.
- **The maps and their parts** (spec 102, `realm/map_parts.py`): every map's parts by the ids its face stamps
  (`data-pick-map`, `data-pick-id`); **picking** on a map sends `marks: [{map, id, name, group?}]` with a new goal.
- **A screen with areas marked** (`realm/idea_lens.py`, decisions §53): `{kind: "screen", screen, marks: [{x, y, w, h,
  note}], note}`, the box in shares of the picture (0 to 1), read into the calls in words (*from 20 % to 45 % across…*).
  **The same shape this spec's mark takes**, with the picture taken from Play rather than from the screens kept.
- **Design's screens by route** (`realm/screen_routes.py`, `realm/screen_map.py`): `_target(path, patterns)` already says
  which screen a path reaches (an exact path, else the best fit by static segments).
- **Concerns and aspects** (spec 108, spec 109): a leader's look marks its map's parts, each concern of an aspect; hints of
  code ground the aspects; *Make it a goal*, *Not a problem*.
- **A bug's short way** (`realm/goal_route.py`): a bug of Tech's alone is short; with its failure in the report it
  `reproduces` and skips the diagnosis call.

## 1. The words

New (`TERMS`, C): **mark** / **marks** (*a box the person drew on Play with a line*: the live product's own picking;
`play_mark`); **hint** / **hints** if `TERMS` has none yet (*what code noticed and no one said*: spec 109's word, now also
the probe's). On Play's bar: **Mark** (its key `M`), *Draw a box or press a part* · *Cancel*. The field: the kinds **Bug**,
**Looks wrong**, **Missing**, **Confusing**; *→ <Party> ×*; *With:* and the chips of what goes with it (*the screen*, *the
part*, *<n> errors*, *<n> failed requests*, *the server's last lines*, *the game's state*), each with its ×; **Send**;
*Add to "<goal>"*; *Sent to <Party>*. The strip: *<Leader> on <screen>*, *Not on <map>*. The hints' words: *An error here*, *A request failed:
<METHOD> <path> <status>*, *Slow: <path> <n> ms*, *A press did nothing*, *Pressed again and again*. Without a probe: *Marks
keep the picture and the place only*.

## 2. Part A: the probe and its proxy

1. **The proxy** (`gui/play_proxy.py`): when Play plays, the host listens on a port of its own on `127.0.0.1` and passes
   every request to the preview's page port as it is, the answer back as it is, but:
   - an answer of `text/html` (asked with `Accept-Encoding: identity`) gets
     `<script src="/__ork/probe.js?o=<the page's origin>&p=<play id>"></script>` as the first child of `<head>` (or of the
     document when there is no head); `Content-Length` set again;
   - its `Content-Security-Policy` and `-Report-Only` headers are dropped (dev only: the proxy serves no one else);
   - `/__ork/*` is the host's (the probe and the vendored snapshot library), never passed on;
   - an `Upgrade: websocket` request is tunnelled byte for byte (Vite's and Next's hot reload); a dev server whose client
     connects to its own port directly is left to do so.
   `Play.answer`'s `url` is the proxy's. `.orkcraft/checks.toml` `preview_probe = false` turns it off: Play then is
   today's, and the page says *Marks keep the picture and the place only*. A proxy that cannot start does the same, saying
   why in the log.
2. **The probe** (`gui/static/play/probe.js`, no dependency but the snapshot library loaded on demand; ES2019, no build):
   talks to the page by `postMessage` to the origin it was given, each message `{ork: 1, play, kind, …}`, and takes only
   messages from that origin. It says:
   - `place`: the path (`location.pathname` and the hash's route), the viewport, at load and at every change of the history
     (`pushState`, `replaceState`, `popstate`, `hashchange`);
   - `under` (asked with a box in the frame's pixels): the elements the box covers best, three at most, each `{selector,
     role, text (≤ 80), rect, file?}`, where `file` is what the dev build tells of its component's source (a
     `data-source`/`data-inspector-*` attribute the project's plugin stamps, else React's or Vue's dev fields read
     defensively; none is fine) and a `canvas` is named as one;
   - `event` as they come: `error` (an uncaught error, an unhandled rejection, `console.error`: message ≤ 300 and the
     stack's first line), `request` (fetch and XHR: method, path without its query, status, ms; a body is never read),
     `press` (a click: the element's selector and rect, and whether within 1 s the DOM changed, the path changed or a
     request began);
   - `picture` (asked): a snapshot of the DOM as it is now (rrweb-snapshot, inputs masked, canvas as data URLs taken right
     after a frame), at most 4 MB, else `none`;
   - `state` (asked): `window.__ork?.state?.()` as JSON, at most 2 KB (a game may give its level, its currencies; nothing
     else is read from the page).
   Nothing is sent anywhere but the page. The probe adds no element to the page and changes no style.
3. **The command's lines kept** (`Play`): while it plays, the preview command's output lines are kept with their time, the
   last 400 (colour codes out, secrets out by `hooks/warder.is_secret` line by line), for a mark's *the server's last lines*.
4. Tests: a static page and a Vite page through the proxy (the script is in the head, the page works, a websocket passes); a
   CSP header dropped; `preview_probe = false`; the probe's messages in a real browser (place on navigation, under a box,
   an error, a failed request, a press that did nothing, a picture, a state; a message from another origin ignored).

## 3. Part B: where you are

`realm/play_place.py` (no model, no face):

```
play_place.screen(state_dir, root, path)                 # Design's screen the path reaches: {id, name, step} or None (screen_map.screen_of)
play_place.parts(state_dir, root, path, files=())        # {map: [{id, name}]} of every map this place touches, by rule (below); {} when none
```

By rule, from the newest snapshot of dev (the maps' own reads, never a model):
- **Design** (`screens`): the screen the path reaches.
- **Tech** (`system`): the parts whose folder holds a `file` the probe named, else the screen's component file.
- **Art** (`art`): the assets the screen's file and the named files name (as `art_map`'s *used* reads them).
- **Marketing** (`marketing`): the step of the way in whose file is one of them (the onboarding, the store page's link).
- **Game design** (`game-design`): the loop's steps that rest on one of them (`rests_on`).
- **Product** (`product`): the jobs whose goals touched one of them (`touches` of the goals the tree names). Weak by nature:
  a job is about people, not files; none is fine.
- **Release**: none (it is no place on a screen).
Bounded: ten parts a map. Tests: a React Router app, a Next.js app, a static page, a path no screen fits, a game's canvas.

## 4. Part C: hints by code

`realm/play_signals.py` (no model, no face) reads one play's events, kept by the host for that play only (a ring of the last
2,000, dropped when Play stops):

| kind | when | craft · aspect |
|---|---|---|
| `error` | an uncaught error or rejection, or `console.error`, on this path | Tech · *Security and reliability* |
| `failed` | a request answered 5xx, or 4xx but 401 and 404 of a path asked once | Tech · *Security and reliability* |
| `slow` | a request over 1,000 ms (`preview_slow_ms` in the checks file) | Tech · *Hotspots* |
| `dead_press` | a press on something that looks pressable (a button, a link, a role) and within 1 s no change of the DOM, the path or a request | Design · *The way through* |
| `again` | three presses or more within 1 s on one element | Design · *State and errors* |

`play_signals.hints(events, path)` → `[{kind, on: {selector, rect} | None, words, at}]`, one a kind and element (the newest),
twenty at most. `lens_rubrics`: each kind in exactly one aspect, as the table says (its tests keep the rule that every kind is
in one aspect). A hint lives as long as the play, unless it is made into a goal (*Make it a goal*: a goal as a mark of the
kind *Bug* with the hint's element) or let be (*Not a problem*: not shown again this play). Tests: each kind from events; a
401 is no hint; three presses on two elements are no `again`; the aspects.

## 5. Part D: the mark

1. **`ideas.play_place {path}`** → `{screen, parts}` (B), and **`ideas.play_hints {}`** → the hints of this play (C), for
   the face.
2. **`ideas.play_mark {text, kind, party?, box: {x, y, w, h}, path, under?, with: [...], add_to?}`** (the box in shares of
   the frame; `with` the chips left on: `screen`, `part`, `errors`, `requests`, `lines`, `state`):
   - **the goal** is `ideas.add`'s, with `party` (the open tab's, or none on the project's tab: the Orkmaster routes it), the
     kind's goal type (*Bug* `bug`, *Missing* `feature`, *Confusing* `pain`, *Looks wrong* none: its party's own), and
     `marks` from B for the maps `with` keeps (`part`);
   - **its screen lens** (`idea_lens`): `{kind: "screen", screen, marks: [{x, y, w, h, note: text}], picture}`, the picture
     the probe's snapshot drawn in the host's Chromium (`idea_shot`'s) at the frame's size, else the page's path drawn anew
     (*the picture is of the page, not of the moment*), kept as the screens kept are;
   - **its play** (`realm/idea_play.py`, `<state_dir>/ideas/<slug>/play.json`): `{commit, path, under, errors, requests,
     lines, state, at}`, each bounded (ten errors, ten requests, the 40 server lines before the mark, 2 KB of state),
     secrets out, read into the route's calls after the lens (`idea_play.prompt_lines`), Tech's first;
   - **a bug** (*Bug*) with an error or a failed request kept `reproduces` (`goal_route.shape`): its Talk is no diagnosis
     call;
   - **`add_to`**: a goal's slug instead of a new goal; the mark joins that goal's lens and play (*Add to "<goal>"* is
     offered when a goal not yet started has a mark on the same screen and of the same kind: by code, no model).
3. Tests: a mark with each kind; on the project's tab (no party); `with` taking chips off; a bug with an error `reproduces`;
   `add_to`; the picture from a snapshot and from the path; secrets out of the lines; no probe (a box and a path only).

## 6. Part E: the faces (after the owner's yes on `docs/mockups/play-lenses/`)

1. **Play stays open when the tab changes** (`frame/state.js`): the die's view is the pane's over the open tab; another
   tab changes the lens over it, never closes it.
2. **The lens strip** (`arena/playlens.js`): under Play's bar, as the concerns' strip is on a map (`cn-strip`), the open
   tab's leader's head and *<Leader> on <screen>* (*The Product designer on Today · Step 1*), then the rubric's aspect chips in their
   state for this screen's parts only; *Not on <map>* when this place has none of the leader's parts. The project's tab
   has no strip.
3. **On the frame**: the concerns of this screen's parts and this lens's hints, each a quiet mark at its element's rect
   (an outline in the alert's or the muted ink, the leader's small head at its corner for a concern, a hollow square for a
   hint) when the probe knows the element, else in the strip. A press on one opens its back as a lifted card's is
   (`ConcernsBack`: what, why, the fix, *Make it a goal*, *Not a problem*). The marks never take the product's presses:
   they are drawn on a layer that lets presses through, and **Hide the marks** in the bar hides them. No count, no badge.
4. **Mark** (`arena/playmark.js`): the bar's **Mark** (or `M`, or a press on a hint's *Make it a goal*) lays a still layer
   over the frame (the product stops taking presses; *Draw a box or press a part* · *Cancel*, Esc); a drag draws the box
   (dashed, in the ink), a press takes the element under it (`under`'s first). The field opens beside the box (inside the
   pane, never over the hand): the line, the kinds as chips, *→ <Party> ×* (the open tab's, changed by `@`), *With:* and
   its chips, *Add to "<goal>"* when offered, **Send**. Sent: the box stays a moment on the frame in the goal's element's colour,
   the bar says *Sent to <Party>: <the goal's short name>*, Play stays open, and the goal is in the first lane as a new goal is.
5. **A game** (a `canvas` under the box): the field's chips gain *the game's state* when the probe has one; under Game
   design's tab the loop's steps are offered as chips (*At which step?*), since no code knows it.
6. Tests: the tab changed with Play open; the strip's words and aspects on a screen and on a path with no screen; a concern
   and a hint on their elements; *Hide the marks*; marking by box and by press; the field's chips; sending; *Add to*; a
   canvas; no probe; reduced motion (the box's moment is still).

## 7. Tests

Each part's above; the critical tests (`tests/test_architecture.py`: `realm/play_place.py`, `realm/play_signals.py`,
`realm/idea_play.py` import no `gui/`), `tests/test_board_alone.py`, `tests/test_updates.py`, and every touched module's.
`tests/test_gui_wording.py` keeps the words of §1.
