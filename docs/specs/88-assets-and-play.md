# Spec 88 — Assets and Play: what the project is made of, seen and touched

The owner, 26 October (decisions §104.11, §104.14): *an indie developer wants to see and touch what comes out: the
screens, the icons, the clips, the sounds; maybe a tab of its own for them.* Today what a goal made is a line (*What it
made*) and, for a screen, one picture (spec 85); the art, the sounds and the variants not picked live in folders nobody
opens, and the build is never played from the Board. **Builds:** Claude (A), a cheaper model reviewed by Claude (B, C) ·
**Review:** full (A serves the project's files and runs its preview) · P1. **A first**; **B and C at once** once A is in.

**What it is, and is not:** the Orkmaster's level gets three tabs, **Field** (today's), **Assets** and **Play**; Assets
lays the project's own files out by kind as cards on the table, each card's face the thing itself, lifted to look or
listen, turned over to its version before; the variants not picked lie under the one picked; Play opens the project's
preview of dev in the pane. A goal's merged files are attributed to it. Read from the files, git and the picks: **no
model**. Not: an editor of the files; a file uploaded or sent anywhere; a store's assets (Release's, spec 68); Play on the
phone; the map's lenses (§104's phases).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §1–§5 | new `realm/assets.py` (the files by kind, what changed and its goal, the version before), new `realm/commit_goal.py` (a commit of dev → its goal and task, from the merged tasks' `commit`), `gui/media.py` (an asset's signed address), new `gui/ideas_assets.py` (`ideas.assets`, `ideas.asset_before`, `ideas.play`, `ideas.play_stop`; wired in `gui/ideas.py`), `core/idea_shot.py` (`preview_of` and `opened` for Play, unchanged in what they do), `realm/lexicon.py`, `realm/event_log.py`; new `tests/test_assets.py`, new `tests/test_commit_goal.py`, new `tests/test_play.py`, `tests/test_media_route.py` |
| **B. Desktop** | §6 | `js/arena/project.js` (the level's tabs), new `js/arena/assets.js` (the table of assets, a card lifted, turned over), new `js/arena/play.js` (the preview in the pane), new `js/arena/assets.css` (`@import`ed by `arena.css`, in `tests/test_design_system.py` `SHEETS`), `js/arena/picks.js` (its media tiles reused, not changed in what they do); new `tests/test_assets_desktop_browser.py` |
| **C. Phone** | §7 | `pwa/shell-project.js` (the project's sheet: *Assets*), new `pwa/shell-assets.js`, `pwa/app.css`, `pwa/sw.js` (`CACHE` one up, `shell-assets.js` in `SHELL`) with `tests/test_pwa.py`'s pin; new `tests/test_pwa_assets_browser.py` |

## 0. The words
`TERMS` gains (realm/lexicon.py) **asset** · *assets* (`asset`): a file the project is made of that people see or hear (a
screen's picture, art, an icon, a sound, music, a clip, a font). New strings: *Field*, *Assets*, *Play*, *Screens*, *Art
and icons*, *Sound*, *Music*, *Clips*, *Fonts*, *Before*, *Now*, *Not picked (n)*, *Changed by <goal>*, *Nothing here
yet*, *Open the build*, *Starting the build…*, *The build would not start: <why>*, *Stop the build*, *Plays dev at
<short commit>*. A person's own file names are shown as they are.

## 1. The assets (A)
`assets.listed(root, ref="dev")` → the files of `ref`'s tree (`git ls-tree -r`), never the working tree's, of these kinds
by extension: **art** (`png jpg jpeg webp gif svg`), **sound** (`wav ogg mp3 flac` under a path naming `sfx|sound|sounds|
audio` or shorter than 10 s when its header says), **music** (the other sounds), **clip** (`mp4 webm mov`), **font**
(`ttf otf woff woff2`); **screens** are spec 85's pictures (`realm/idea_shots.py`), the newest a screen. Skipped:
`code_map.SKIP`'s folders, `design/looks/` (spec 85's picks keep their own), a file over 50 MB, a file `is_secret` names.
Each: `{id: path, kind, name, bytes, w, h, seconds, goal, task, at}` (`w`/`h` for art, read from its header; `seconds`
for a sound or a clip when its header says; `goal`/`task`/`at` of the last change, §3). At most `MAX_ASSETS` = 600, the
changed first. A **stack** is a folder of one kind with more than six files (*×n*, spec 50 §3.4).

## 2. The variants not picked (A)
A file a *Pick one* wrote (spec 64, `idea_pick.history`) carries `others`: the variants of its pick not picked, with
their signed addresses (gui/media.py, as a pick's today). Shown under the card, *Not picked (n)*.

## 3. What changed, and by which goal (A)
`commit_goal.of(state_dir, root, sha)` → `{goal, task}` of the merged task whose `commit` (core/idea_runner.py keeps it on
landing) is the first at or after `sha` in dev's history; `{}` for a commit no task landed (the person's own).
`assets.changed(root, since, ref="dev")` → `git diff --name-status <since>..<ref>` of the assets' kinds: `added`,
`changed`, `removed`, each with its goal by the last commit that touched it. `since` is the face's own (the device's last
look, §6.4); none: nothing is marked.

## 4. The version before (A)
`ideas.asset_before {path, since}` → the signed address of the file as it was at `since` (`git show <since>:<path>`,
written once into `<state_dir>/assets-before/<sha>/<path>` and served from there), or none when it was added since.

## 5. Play (A)
`ideas.play` opens the project's preview (`idea_shot.preview_of`: `checks.toml`'s `preview`, a static `index.html`, the
package's `dev|preview|start` script) in **a worktree of dev's head** (`<state_dir>/play/`, made as a task's is, its
dependencies linked as spec 86 §2 does), on a free port, and answers `{url, commit}` once it listens (`OPEN_S`), else
`{error}`. One Play a project; a second `ideas.play` while it runs answers the same; a merge into dev changes nothing until
*Play* is pressed again (`commit` says which). `ideas.play_stop`, closing the project, or ten minutes with no face
showing it stops it and removes the worktree. Events `play_started` (`seconds`, `ok`, `why`) and `play_stopped` (`why`).
The preview's address is the machine's own (`127.0.0.1`); the phones' listener never serves it.

## 6. The desktop (B)
1. **The Orkmaster's level has three tabs** over its table: **Field** (today's level, spec 79), **Assets**, **Play**.
   The level opens on Field as now.
2. **Assets** lays the assets on the table as cards (the field's card, 128 x 180, spec 87 §2), in columns by kind in the
   order of §0, a stack for a folder of one kind (§1). A card's face is the thing: art drawn whole (`object-fit:
   contain`, pixelated when it is smaller than the card), a screen its picture, a sound or music its name over orkUI's
   `sound` sign and its length, a clip its first frame when the browser gives one (else the `film` sign), a font its name
   set in it. Its foot: its name and, when it changed, *Changed by <goal>* with the goal's element.
3. **A card pressed lifts** in the pane (picks.js's tiles, large): art at its size up to the pane, a sound or a clip
   playing with its controls, *Not picked (n)* under it (§2). **A changed card has *Before* / *Now***: the card turns over
   (spec 74's steps, ≤ 0.42 s) to the version before (§4).
4. **What changed since the device's last look** (`localStorage`, set when the tab is left) is played once when the tab
   is opened: added cards dealt, changed ones sealed with their goal's element, removed ones crumble (spec 74 §0's rules;
   none under reduced motion). A filter by kind and by goal (*All goals*, or one).
5. **Play**: *Open the build* → *Starting the build…* → the preview in the pane (an `iframe` with `sandbox="allow-scripts
   allow-same-origin allow-pointer-lock"`, its own origin), *Plays dev at <short commit>* over it, *Stop the build*. An
   error says *The build would not start: <why>*. No preview found: *Nothing here yet* with the one line of how
   (`checks.toml`'s `preview`).

## 7. The phone (C)
The project's sheet (spec 70 §2) has a section **Assets**: the kinds as rows of tokens (74 px, spec 67), a token pressed
opens the asset's screen (large, playing, *Before* / *Now*, *Not picked (n)*), the changes since the device's last look
marked with the goal's element. No Play (it is the machine's own address); its place says *Play on the computer*.

## 8. Tests
A: the kinds by extension and path; skipped folders and secrets; the cap, changed first; stacks; a pick's others signed;
a commit to its goal through the tasks' `commit`, a person's own commit none; added, changed, removed since a commit with
their goals; the version before written once and signed, none when added; a signed asset served with Range, a forged or
`..` path 404; Play started on a stub preview in a worktree of dev, answered once, the same while it runs, stopped by
command and by the idle timeout, its worktree removed, the events. B: the three tabs; the cards by kind with their faces;
lifted art, a playing sound; turned over; dealt, sealed and crumbled once, not under reduced motion; the filter; Play's
three states and the frame's sandbox. C: the section, a token's screen, the marks, no Play, the service worker's version.
The critical tests and each part's files' tests.
