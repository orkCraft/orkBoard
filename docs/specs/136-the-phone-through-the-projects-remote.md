# 136. The phone through the project's remote: goals dropped into `orkboard/inbox`, the journal read, a goal taken once

Decisions §243 (1–8, 10). **Builds:** the cheaper model, A and D first, then B and C side by side, the spec's author
reviewing and merging · **Review:** the critical tests and each part's own · P1. After §229's journal (built,
`realm/remote_journal.py`). Not here: the Board on a branch and a cloud session carrying a goal past its taking (§243.9),
the native frame's Keychain and GitHub sign-in (spec 103), the mailbox (§219.2–3, waiting).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The journal for the phone** | `status.json` beside `status.md`; `taken.json`; the journal asked for when a phone is paired with a remote | `realm/remote_journal.py` (`_status` split: the data, then its Markdown), the page's Settings (*Your phone*); `tests/test_remote_journal.py` |
| **B. The inbox on the host** | the inbox branch read; a goal taken in the journal first, laid on the Board after the push; the lock; the tick | new `realm/remote_inbox.py` (pure but for `git`: read, clean, take), `gui/board_host.py` (`_journal_tick` reads the inbox too), `gui/ideas.py` `add` (called as the + card calls it); `tests/test_remote_inbox.py`, `tests/fixtures/inbox/` |
| **C. The phone's way through the remote** | the repository and its token in the phone's settings; the journal read with its ETag; the + card's goal written to the inbox when the computer cannot be reached; what is shown and how old it is | new `pwa/shell-remote.js` (GitHub's REST API: no library), `js/link.js` / `js/linkpaired.js` (a link that is the remote when the computer is not), `js/hand/pluscard.js` (where its goal goes), `pwa/frame.js` (the settings before pairing); `tests/test_phone_remote_browser.py` |
| **D. The words** | `TERMS`: *inbox*, *taken*, *Waiting to be taken*, *As of*; every line below | `realm/lexicon.py`, `tests/test_lexicon.py`, `tests/test_gui_wording.py` |

## The shapes (all parts build to them)

**A goal in the inbox**, `inbox/<device>/<id>.json` on `orkboard/inbox` (the device the phone's id from pairing; `id` a
ULID made on the phone, so the files sort by time):

```json
{"v": 1, "id": "01JC…", "device": "<device id>", "at": "2026-11-04T14:02:11+01:00",
 "text": "<the person's words, at most ideas.SECTION_CHARS>", "element": "<rune or absent>", "party": "<slug or absent>",
 "type": "<the party's type or absent>", "asks": "<or absent>", "marks": [], "photos": ["01JC….1.jpg"]}
```

Its photos beside it, `inbox/<device>/<id>.<n>.jpg` (each at most 2 MB, at most 4). Anything else on the branch is read as
nothing.

**`taken.json`** in the journal: `{"v": 1, "taken": [{"id", "by", "at", "slug": "<slug or empty>", "error": "<words or
empty>"}]}`, `by` the machine's name (`socket.gethostname()`, for a cloud session its own, §243.9), the last 30 days kept.

**`status.json`** in the journal: `{"v": 1, "written": "<ISO>", "parties": [{"slug", "title", "goals": [{"slug", "title",
"state", "phase", "needs_you": bool, "error": ""}]}], "failed": [{"slug", "title", "error"}], "taken": <taken.json's
list, the last 7 days>}`. `needs_you` true when a card for it waits in the hand. Scrubbed as every journal file is
(`scrub`).

## A. The journal for the phone

1. **`status.json`**: `_status` is cut in two, `status_data(...)` (the dict above) and its Markdown (`status.md`, as
   today, written from the data); `pack_counted` adds `status.json` and `taken.json`.
2. **The journal asked for when a phone is paired and the project has a remote on GitHub** (`git remote get-url origin`
   names `github.com`): Settings' *Your phone* shows, once, *Follow this project from your phone away from home? Its
   status goes to a branch of its own on origin, orkboard/journal, and goals from your phone come through
   orkboard/inbox. No code and no prompts. The repository must be private.* **Turn it on** writes `[journal]` (§229.1) and
   `inbox = "orkboard/inbox"` in it; **Not now** asks no more (Settings keep the switch).
3. **When** (§243.8): `every` 15 for a user (the forge's choice for a contributor, §230.4); and at once (`urgent`) when a
   goal was taken, or a card that needs the person came to the hand.

## B. The inbox on the host

1. **Read**: at each `_journal_tick` whose project has `inbox`, at most every 2 minutes, `git fetch <remote>
   refs/heads/<inbox>:refs/orkboard/inbox` (no checkout, the working tree untouched), then `git ls-tree -r` and `git
   cat-file` for the `inbox/*/*.json` not in `taken.json`. A fetch that fails is said in the event log and troubles no
   work. No inbox branch yet: nothing to read.
2. **Cleaned** (`remote_inbox.clean`): `v` 1; `text` non-empty, cut to `SECTION_CHARS`; `element`, `party`, `type` dropped
   when not the project's (the + card's rules, so the route decides); `photos` only those beside it, within their
   limits. One that cannot be read is taken with its `error` (*Could not read this goal: <why>*), so it is not read again.
3. **Taken first, laid after** (§243.4): the goals read are written into `taken.json` with `slug` empty and the journal is
   sent at once. **The push went through**: each goal is laid through `Ideas.add` with the + card's arguments (`text`,
   `track` from `party`, `element`, `type`, `asks`, `marks`, `photos`) and `via = "inbox"`; its slug, or the add's words as
   `error`, goes into the next journal. **The push was refused** (another took first, `non-fast-forward`): fetch the
   journal, read its `taken.json`, lay nothing that is in it, take what is left once more (at most 3 tries a tick).
   The local journal ref is moved to what the remote has before packing again (`send`'s rule).
4. **Never twice**: before laying, the Board is read for a goal with that inbox id (`state.json`'s `inbox_id`, written by
   the add); one already there is not laid again (a host that crashed between the add and its journal).
5. **Nothing written to the inbox** by the host, ever: it reads that branch and nothing else.
6. **The event log** says `inbox_taken` (the id, the slug or the error) as it says `journal_sent`.

## C. The phone's way through the remote

1. **Its settings**, on the phone's *Settings* (and before pairing, in `frame.js`): **the repository** (`owner/name`,
   filled from the computer at pairing when it has one: the pairing's answer carries `remote`), **its token** (pasted),
   and the lines of §243.7, word for word: *This token can change any file of the repository, the code too; Orkboard
   writes only orkboard/inbox. Make one for this repository alone, with Contents: read and write. A rule on main that asks
   for a pull request keeps the code safe.* and *Kept on this phone in the app's storage; the app from the store will keep
   it in the phone's keychain.* **Remove** forgets it at once.
2. **Checked when it is given**: `GET /repos/{owner}/{repo}`: `private` false → refused in §243.6's words, the token not
   kept; no right to write (`permissions.push` false) → *This token cannot write to the repository*; else *Ready: goals go
   through orkboard/inbox when your computer cannot be reached*.
3. **The journal read**: `GET /repos/{o}/{r}/contents/status.json?ref=orkboard/journal` with `If-None-Match`, every 60 s
   while the app is open and visible (`visibilitychange`), never in the background; a 304 changes nothing. Read only while
   the computer is not reached (on the same network the live Board is the truth); the first read when the link to the
   computer fails.
4. **What it shows** from it: the project's screen (§223) as far as the journal tells it: the parties, each goal's card
   with its state, the goals that need the person marked, what failed; every screen's header says *As of 14:02* (the
   journal's `written`), in the muted ink, and no button that needs the computer is pressable (*Needs your computer*).
   The goals of this phone's inbox not yet in `taken`: face down, the person's own words, *Waiting to be taken: your
   computer or a cloud session will read it*; taken with an error: the error's words.
5. **The + card through the remote**: when the link to the computer is down and the remote is set, **Send** writes the
   goal (`PUT /repos/{o}/{r}/contents/inbox/<device>/<id>.json` on `branch: orkboard/inbox`; its photos first, the same
   way); the branch made on the first goal (`POST /git/refs` from an empty tree's commit: no history shared with the code).
   A 409 (the branch moved under it) is tried again, 3 times. Offline, the goal waits in the app's storage
   (`orkcraft.v1`'s `outbox`) and is sent when the network comes back; the card says *Waits for the network*. The line
   §221.1 gave (*Your computer is asleep or offline…*) becomes *Sent through your repository: your computer or a cloud
   session will take it*.
6. **No remote set**: as today (§221.1's line), and once, *Set your repository in Settings to send goals while your
   computer is away*.
7. **GitHub's limits**: a 403 with `x-ratelimit-remaining: 0` stops the reads till `x-ratelimit-reset`, said in a line
   (*GitHub asks us to wait till 14:30*); a 401 says *The token was refused: give a new one in Settings*.

## D. The words

`TERMS` gets: `inbox` (*inbox*: the branch of the project's repository the phone drops goals into), `taken` (*taken*: a
goal from the inbox read by the computer or a cloud session and laid on the Board), and the lines above as written. The
interface says *goal* and *party*, never idea or track (CLAUDE.md); `inbox`, `taken.json`, `status.json` are names and
stay.

## Done when

- A goal written on a phone with the computer away is on the Board within 2 minutes of the computer's waking, once, with
  its rune and its photos; two hosts reading the same inbox lay it once (`tests/test_remote_inbox.py`, two clones of one
  bare repository, both ticking).
- The phone shows the journal's status with its *As of*, refuses a public repository and a token that cannot write.
- The critical tests pass: `tests/test_architecture.py` (`realm/remote_inbox.py` imports no `gui/`), `tests/test_board_alone.py`,
  `tests/test_updates.py`, and each part's own.
