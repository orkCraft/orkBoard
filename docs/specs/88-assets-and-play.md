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

## As built (A)

Files: new `realm/assets.py`, `realm/commit_goal.py`, `gui/ideas_assets.py` (wired in `gui/ideas.py`: `AssetsMixin`, its four commands,
`play_tick` in `tick`); `gui/media.py` (an asset's address and serving), `core/idea_shot.py` (`opened` takes `env`), `realm/lexicon.py`
(`asset`), `realm/event_log.py` (`play_started`, `play_stopped`), and one line in `gui/board_projects.py` (closing a project stops its
Play). Tests: `tests/test_assets.py`, `tests/test_commit_goal.py`, `tests/test_play.py`, `tests/test_media_route.py`,
`tests/test_lexicon.py`, `tests/test_event_log.py`. No model anywhere.

**The commands' answers** (the shapes B and C read; `ref` is the project's `merge_into`, `dev` by default):

- `ideas.assets {since?}` → `{commit, short, ref, since, assets, removed, stacks, goals}`. `since` is the face's last look: a commit
  (short or full, one of dev's) or an ISO time (dev's last commit at or before it); the answer's `since` is the commit it was read as,
  `""` when none (then nothing is marked and `removed` is `[]`). `commit` is dev's head (`""` with no dev branch).
  - `assets`: `[{id, kind, name, bytes, w, h, seconds, goal, task, at, change, url, stack?, others?}]`, at most 600, **the changed first,
    then the newest `at`**. `id` is the repository path (a screen's is `screen:<goal>/<task>`); `kind` one of `screen`, `art`, `sound`,
    `music`, `clip`, `font` (the faces' column order); `w`/`h` for art, a screen and a clip, `seconds` for a sound, music or a clip when
    the header says (else null; a sound of unknown length is music unless its folder names `sfx|sound(s)|audio`); `goal`/`task`/`at` of
    the last commit that touched it (`goal` `""`: the person's own, or older than the newest 5 000 commits); `change` `"added"`,
    `"changed"` or `""` since `since` (a screen is `"added"` when taken after `since`'s commit); `url` its signed address (a screen's is
    its pick route's); `stack` the folder when it is one of a stack; `others` for a file a *Pick one* wrote:
    `{goal, pick, picked, variants: [{key, name, mime, w, h, seconds, url}]}`, the variants not picked.
  - `removed`: `[{id, kind, goal, task, at}]` since `since` (the last commit that touched it, its goal `""` for the person's own).
  - `stacks`: `[{folder, kind, n}]`, a folder holding more than six of one kind.
  - `goals`: `{slug: {title, element}}` of every goal named above.
- `ideas.asset_before {path, since}` → `{path, since, url, bytes, w, h, seconds}`, the file as it was at `since` (`url` signed);
  `{path, since, url: ""}` when it was added since (or `since` names no commit of dev, `since` then `""`). A path that may not be an
  asset: *That is not one of the project's assets*.
- `ideas.play {fresh?, peek?}` answers at once (a start takes up to `OPEN_S`, and a command never holds the page's loop):
  `{state: "starting", commit, short}` → `{state: "playing", url, commit, short, dev}` (`url` `http://127.0.0.1:<port><preview_path>`;
  `dev` is dev's head now: when it differs from `commit`, a merge came since and *Play* pressed with `fresh: true` starts it anew) or
  `{state: "failed", error, none?}` (`error` `no preview` with `none: true`: *Nothing here yet*; else `did not open`, `There is no dev
  branch yet`, `could not make its worktree: …`). `peek: true` only says what it is now, starting nothing (`{state: "stopped"}` when
  nothing runs). A second `ideas.play` while it starts or plays answers the same. The face presses with `ideas.play`, polls with
  `{peek: true}` about every second while it starts, and while the tab shows the build sends `{peek: true}` at least every few
  minutes: **ten minutes with no `ideas.play` of any kind stops it**. On start, failure and stop the bus carries `play.changed` (the
  snapshot follows). A phone is refused both commands: *Play on the computer*.
- `ideas.play_stop {}` → `{ok: true, stopped}` (`stopped` false when nothing ran); it answers at once, the preview's process group
  is killed and `<state_dir>/play/` removed by Play's own thread.

**Addresses.** An asset is `GET /media/_asset/<commit>/<path>?s=<signature>` (`media.asset_url`), served by the page's server and the
phones' listener (C reads them) with the pick route's headers (`private, immutable`, `nosniff`, `CSP: sandbox; default-src 'none'`,
inline) and Range; its media type by its extension. Not only the version before: **every asset is served from the before-cache**,
`<state_dir>/assets-before/<commit>/<path>`, written once from git (`git cat-file`) on the first request, the newest 16 commits kept,
so the working tree is never read and a signed address stays good.

**Events.** `play_started` (`seconds`, `ok`, `why`: `""` · `no preview` · `did not open` · `could not make its worktree: …`) and
`play_stopped` (`why`: `stopped` · `idle` · `closed` · `quit` · `again` · `exited`, the last when the preview's command ended by itself).

**For spec 89** (`realm/commit_goal.py`): `of(state_dir, root, sha, ref="dev")` → `{goal, task}` or `{}`; `index(state_dir, root, ref)`
→ `{sha: {goal, task}}` of every commit a task brought (cached by dev's head and the plans); `resolve(root, since, ref)` → the commit a
sha or a time names, `""` for none; `last_touch(root, ref, since="")` → `{path: {sha, at}}`, the newest commit of `since..ref` that
touched each file; `head(root, ref)`. A task's own commits are its `commit` and the commits behind it no earlier landing reached, as
many as its `subjects`, so a person's commit between two landings is nobody's.

**Security.** Only signed paths are served; a path is refused before git sees it when it has `..`, `.`, an empty part, a backslash or a
control character, a hidden folder or one of `code_map.SKIP`'s, `design/looks/`, an extension that is no asset's, or a name
`is_secret` names; the commit is a full hex sha; git runs with fixed arguments, `--literal-pathspecs` and `--` before a path; a file
of the tree that is a link or a submodule is never an asset; the cache refuses a path that leads out through a link. Play's static
preview listens on 127.0.0.1; a command preview is given `HOST=127.0.0.1` and `PORT` (where it binds is its own), and the address
handed out is always `127.0.0.1`. Nothing proxies it: the phones' listener has no route to it, and the phone is refused the commands.

**Decided here, not in the text above:** `assets.listed(state_dir, root, ref, changes)` and `assets.changed(state_dir, root, since,
ref)` take the state folder (screens, picks and goals live there); `since` may be a time as well as a commit; `ideas.play` does not
wait for the port (above) and has `fresh` and `peek`; Stop all does not stop Play (it is the person's, not an agent's); a screen is a
task's newest picture, one per task.

## As built (C)

Files: new `pwa/shell-assets.js`; `pwa/shell-project.js` (`makeAssets(core)`, its section drawn after the parties, `assets.load()` when the sheet opens, `assets.leave()` when it is put away); `pwa/app.css` (the block
*Assets (spec 88 C)*, orkUI's tokens only); `pwa/sw.js` (`CACHE` is `orkcraft-app-v95`, `shell-assets.js` in `SHELL`); the pins of the version in `tests/test_pwa.py`, `tests/test_pwa_look_browser.py` and
`tests/test_pwa_quiet_browser.py`; new `tests/test_pwa_assets_browser.py` (Chromium at 390 × 844 over the stub host of spec 70's tests, `ideas.assets` and `ideas.asset_before` answering as "As built (A)" says). No Play, no model.

- **The section** *Assets* is the last of the project's sheet (after the parties; the sheet's first screen is as it was). It asks `ideas.assets {since?}` each time the sheet opens; an error (a host without it) or
  no answer leaves the section out, a project with no files says *Nothing here yet*. Each kind (§0's order, *Screens* · *Art and icons* · *Sound* · *Music* · *Clips* · *Fonts*, its count beside it) is a row of
  74 px tokens (5:7) that wrap, never scroll sideways: art and a screen drawn whole (`object-fit: contain`, crisp when 64 px or less on a side), a sound or music the `sound` sign and its length, a clip the `film`
  sign and its length (no video is loaded for a token), a font *Aa* set in itself (`FontFace`; the `text` sign until it loads or when the browser cannot read it); the name as the person wrote it at the foot.
  The host's order is kept (the changed first). A kind shows its first eight entries and *All n* shows it whole. A stack (`stack`) is one token with edges and *×n* that a press opens in place; its front token
  folds it again. *Play on the computer* closes the section (a line with the `play` sign, nothing to press).
- **The marks.** What `ideas.assets` says changed (`change` *added* / *changed*) is raised (`is-changed`) and wears its goal's element (`goals[goal].element`); a removed file is a dashed ghost with a cross and
  its goal's element, first in its kind, nothing to press. A change of the person's own (no goal) has the raised token and no element. The title and label say *Changed by <goal>*.
- **The last look** is `localStorage` `orkcraft.assets.look`, `{project: dev's commit}`, written when the project's sheet is put away **after the section came into view** (an `IntersectionObserver`; a token
  pressed counts): a sheet opened only to reach a party does not clear the marks. With no look yet nothing is marked (`since` not sent).
- **The asset's screen** is a sheet of its own (full, mounted in the page's body on first use so the project's sheet's queries do not find it): the file's name and its length and size, the thing large (art drawn whole,
  crisp art a whole number of times its size; a sound or a clip an `audio` / `video` with controls, `play()` tried at once and left to the controls when the browser refuses; a font set in itself), *Changed by <goal>* with
  the element, and for a *changed* file two 44 px buttons **Before** / **Now** (`ideas.asset_before {path, since}` asked on the first *Before*, kept; a `url` of `""` removes the pair). Under it
  *Not picked (n)*: picks.js's `tiles` for `others.variants`, looked at and listened to only, a press never picks (their label strips are disabled, a press is stopped before it reaches the tile). Closing the
  screen pauses what plays and returns to the project's sheet.

**Decided here, not in the text above:** the section is last in the sheet, not first; *All n* is the one new string (§0 has none for showing a kind whole), the shortest; a kind shows eight
entries; a clip's token is its sign, not its first frame (a row of videos is heavy on a phone); removed files appear as ghosts (§7 asks only for the changes marked); the last look is kept when the section was
seen, not when the sheet is left; the asset's screen is a sheet over the project's, not a route of the Board's screens.
