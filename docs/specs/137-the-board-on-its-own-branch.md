# 137. The Board on its own branch: its pages and its state in the repository, one holder at a time by a lease

Decisions §244 (1–15). The owner: *the Board must be kept in the repository, that is the key decision here.* **Builds:**
A and B by the cheaper model, the spec's author reviewing and merging; C, D, E after them · **Review:** the critical tests
and each part's own; A and B also by a test of **two hosts on one bare repository** · P1. After spec 136's A and B (the
journal's `status.json`/`taken.json`, `realm/remote_inbox.py`). **Checked before D is built** (§244.15): Actions' quota and
price on GitHub's own page; Claude Code signed in on a runner by both secrets (`CLAUDE_CODE_OAUTH_TOKEN`,
`ANTHROPIC_API_KEY`). No new pane, column, drawer or dialog.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The Board's branch** | what goes and what never does; packed and committed by git's plumbing; a working copy kept from it; the scrub | new `realm/board_branch.py`; `realm/remote_journal.py` (its `scrub` and plumbing shared, not copied); new `tests/test_board_branch.py` |
| **B. The lease and the pushes** | `lease.json`, taken and renewed by a push without force; the holder's pushes; the computer that wakes under a cloud run | new `realm/board_lease.py`; `gui/board_host.py` (the tick, beside `_journal_tick`); `realm/remote_inbox.py` (§244.4: the holder takes); `realm/event_log.py`; new `tests/test_board_lease.py`, new `tests/test_board_two_hosts.py` |
| **C. The answers through the inbox** | `inbox/<device>/<id>.answer.json`, taken by the holder as a goal is | `realm/remote_inbox.py`, the hand's answer commands, `gui/static/pwa/*` |
| **D. The cloud run** | `.github/workflows/orkboard.yml` written on a yes; its steps; the ceiling; `orkboard drive cloud-run` | new `realm/cloud_run.py`, `gui/drive.py`, the workflow's template |
| **E. Settings and the words** | the switch, which secret pays, the schedule, the lines | Settings, `realm/lexicon.py` |

Nothing changes for a project that has not turned the Board's branch on: A and B do nothing without `[board]` in
`orkcraft.toml` (A.1), so they are merged as soon as they are green.

## 0. What is there today

- The Board's **pages** (parties, goals, their sections) live in a worktree of their own, `<state_dir>/board/`
  (`realm/idea_git.py` `BoardTree`, spec 35 §13): a write is a commit on the work branch (the writes of 10 s as one),
  pushed only by `ideas.push`.
- The Board's **state** is not in git: each goal's `state.json`, `plan.json`, `route.json`, `talk.jsonl`, `pick.json`,
  `lens.json`, the parties' `goals/`, `roles/`, `kinds.json`, `project.json`, … in `<state_dir>` (`.orkcraft/`). A worker
  that is not the person's computer has the specs and no Board.
- The journal (§229, `realm/remote_journal.py`) is sent to `orkboard/journal` by git's plumbing (a temporary index,
  `hash-object`, `commit-tree`, `update-ref`, a push without force), with every line scrubbed for a secret's shape.
- Spec 136 B reads `orkboard/inbox` and takes a goal in `taken.json` first, as a lock between hosts.

## A. The Board's branch

### A.1 Turned on

```toml
[board]
remote = "origin"            # the remote's name
branch = "orkboard/board"    # a branch of its own: no history shared with the code, never merged, no workflow in it
```

`board_branch.read_config(root)` → `BoardConfig(remote, branch)` or None (off: nothing of A–D runs). Written only by E's
switch (on the person's yes), never by itself. **A private repository only** (§244.11): before it is written, an anonymous
`GET https://api.github.com/repos/<owner>/<name>` for an origin on `github.com`: a 200 is a public repository and is
refused in words (*The Board holds your goals' words and specs: it goes only to a private repository*); a 404 (private, or
not reachable without a token) goes on. A remote not on GitHub goes on with a line that it must be private.

### A.2 What goes, laid out as `.orkcraft/` is (§244.1, §244.12)

The branch's tree is `<state_dir>`'s own paths, so a working copy is the branch's files and nothing is renamed (Orkline
reads the same Board):

- **Goes**: `board/<wiki_rel>/pages/` and `board/<wiki_rel>/specs/` (the pages, as the Board's tree holds them; never its
  `.git`); `ideas/<slug>/` all but `secrets.json` and anything under a `worktree` or `sign-in` folder; `goals/`, `roles/`,
  `kinds.json`, `segments.json`, `project.json`, `checks.toml`, `canvases.jsonl`, `slices.json`, `cascades.json`
  (spec 131), the goals' photos (each at most `PHOTO_MAX = 2 MB`, a larger one held back and said); and `lease.json` (B).
- **Never**: `secrets.json`, `sign-in/`, `drive.json`, `worktrees/`, `logs/`, `usage/`, `crashes/`, `repair/`,
  `screens/`, `claims.json`, `journal.json`, **anything not listed** (`GOES`, an allow list; `NEVER`, checked again over
  it, so a file of a listed folder named as never stays home).
- Every text file is scrubbed line by line for a secret's shape (`remote_journal.scrub`): a line that has one is replaced
  by `HELD`, the count told; a JSON file whose line was held back is not sent at all (a broken JSON on the branch is worse
  than a missing one), said by its path.

`board_branch.pack(state_dir, wiki_rel)` → `{path: bytes}`, `held: [path]`. Pure but for reading files.

### A.3 Committed and read by plumbing

- `board_branch.commit(root, state_dir, config, files, message, parent)` → the commit, or "" when the tree is the
  parent's: a temporary index in the state folder (`board.index`), `hash-object -w`, `update-index --add --cacheinfo`,
  `write-tree`, `commit-tree -p <parent>` (none for the first), `update-ref refs/orkboard/board`. The person's working
  tree, index and branches are never touched (as the journal's). Author *Orkboard* `orkboard@localhost`.
- `board_branch.fetch(root, config)` → the remote's tip or "": `git fetch <remote> +refs/heads/<branch>:refs/orkboard/board-remote`
  (no checkout); a fetch that fails is a result in words.
- `board_branch.push(root, config, commit)` → `{ok, refused, why}`: `push <remote> <commit>:refs/heads/<branch>`, never
  `--force`; `refused` true for a non-fast-forward.
- `board_branch.files_at(root, ref)` → `{path: bytes}` by `ls-tree -r` and `cat-file`.

The plumbing helpers of `remote_journal` (its `_git`, its temporary index) are moved where both read them
(`realm/plumbing.py`), not copied; `remote_journal`'s tests stay green unchanged.

### A.4 The working copy, kept from the branch

`board_branch.unpack(state_dir, files, board_tree)` writes the branch's files into `<state_dir>` when a worker takes the
Board (B.2): each state file written whole (to a temporary name, then renamed); a listed file on disk that the branch does
not hold is removed (a goal dropped by the other worker), **a file not listed is never touched** (the secrets, the sign-ins,
the logs stay). The pages go into the Board's tree (`BoardTree.root()`) and are committed there as one write
(`flush(force=True, message="board: the Board taken from <by>")`), so the work branch and the orks' worktrees cut from it
see them (§244.1, §244.10).

### A.5 Tests (`tests/test_board_branch.py`)

The allow list (each *never* stays home, a file not listed stays home, a `secrets.json` inside `ideas/<slug>/` stays home);
the scrub (a token's shape held back, a JSON with one not sent); `commit` makes no commit for the same tree; `unpack`
writes, removes a listed file the branch dropped, leaves a never-file alone, commits the pages once; config off: nothing
runs; the public check refuses a 200 (a fake HTTP).

## B. The lease and the pushes

### B.1 `lease.json` (`realm/board_lease.py`)

On the Board's branch: `{"v": 1, "by": "<the machine's name or the run's>", "kind": "computer" | "cloud run",
"until": "<ISO, UTC>", "at": "<ISO>"}`. **Held** while `until` is ahead of now (`LEASE_S = 600`). Only the holder writes
the branch (§244.2).

- `take(root, state_dir, config, me, kind, now)` → `{held: True}` or `{held: False, by, kind, until}`: fetch; read the
  remote's `lease.json`; held by another → not taken; else a commit of the Board **as the remote has it** with a new
  `lease.json` (the parent the remote's tip), pushed without force. **The push decides**: refused (another pushed first)
  → fetch and read again, once; still refused → not taken. Taken: the branch's files unpacked (A.4) before anything else
  is written. A branch that does not exist yet: the first `take` makes it from this machine's Board (no parent).
- `renew(...)` every `RENEW_S = 180` while the holder runs: `until` moved ten minutes on, pushed with what changed.
- `give_back(...)`: `until` set to now, pushed with the Board; a cloud run's last step (D) and the computer's quit.
- Clocks: `until` is UTC; a lease is read held for `SKEW_S = 60` past its `until` (two machines' clocks).

### B.2 The computer's tick

In `gui/board_host.py`, beside `_journal_tick`, with `[board]` set: at the host's start and then every `RENEW_S`:

1. Not holding → `take`. Taken: the host goes on as today on the unpacked Board. Not taken (a cloud run holds it): the
   Board is read from the branch's files (unpacked, as a reader) and **nothing that writes runs** (the keeper refuses in
   the words *A cloud run has the Board: it gives it back when it ends (at most 30 min)*), the line in the host's status
   (`board_held: {by, kind, until}`) for E's face; tried again at the next tick.
2. Holding → `renew`, with **the pushes** (§244.3): the Board packed and committed when it changed, pushed at most every
   `PUSH_S = 120` while it changes; **at once** when a card for the person comes to the hand (spec 136 A.3's `urgent`);
   and on `give_back`.
3. **Offline**: a renew that cannot push keeps the host working (the person is at it). Back online: when the remote's tip
   is still this host's last push, it pushes and renews; when another took the Board meanwhile (the tip moved), this host's
   state since its last push is kept aside, whole, in `<state_dir>/board-aside/<at>/`, the branch's Board unpacked, and the
   line says so (*Another worker had the Board while you were offline: your changes since <time> are kept aside*); event
   `board_aside`. Nothing is merged by itself.
4. **The holder takes the inbox's goals** (§244.4, this changes §243.4): `remote_inbox`'s tick runs only on the holder;
   `taken.json` stays for the phone to read, no longer as a lock (its retries stay harmless).

Events: `board_taken` (`by`, `kind`, `files`), `board_pushed` (`commit`, `files`, `held_back`, `why`), `board_refused`
(`by`, `kind`, `until`), `board_given_back`, `board_aside`. Never a word of the Board.

### B.3 Tests

`tests/test_board_lease.py`: take on an empty remote makes the branch; held by another refuses; a lease past
`until + SKEW_S` is taken; renew moves `until`; give back frees it; a refused push read again once. 
`tests/test_board_two_hosts.py`: two clones of one bare repository, each with its own `<state_dir>`, ticking: one holds,
the other reads and refuses to write; the holder gives back, the other takes and sees the first's goals and pages; the
offline case keeps the diverged state aside; the inbox's goal is laid once, by the holder.

## C. The answers through the inbox (§244.5)

An answer to a card of the hand from the phone away from home: `inbox/<device>/<id>.answer.json`
`{"v": 1, "id", "device", "at", "card": "<the row's id>", "kind": "<the row's kind>", "answer": {...}}` (the same
arguments the hand's command takes), taken by the holder as a goal is (`taken.json`), applied through the same host
command as the hand's; a card gone or answered already is taken with its words as `error`. The phone writes it as it
writes a goal (spec 136 C.5) when the computer cannot be reached.

## D. The cloud run (§244.6–9)

`orkboard drive cloud-run` (`gui/drive.py`): `take` with `kind: "cloud run"` (held by an awake computer: it ends at once,
exit 0, *The computer has the Board*); reads the inbox; carries each goal as far as **the reading** goes (the Orkmaster's
route, Talk's rounds, the sections, the plan) and takes the answers in; **never the work** (a goal whose next step is a
task waits: *Planned: the work starts on your computer*); pushes; gives back. A ceiling per run in dollars with an API key
(`--usd 1`, *At most $1 a cloud run*), the job's timeout 30 minutes. The workflow (`.github/workflows/orkboard.yml` on the
default branch, written only on the person's yes and committed as their file): `workflow_dispatch` and the chosen
`schedule`, `concurrency: orkboard`, the two secrets as §244.8 says. Built after the checks above.

## E. Settings and the words

- Settings' *Your phone* (after spec 136 A.2's journal line): **Keep the Board in the repository** — *Its pages and its state
  go to a branch of their own, orkboard/board. Secrets, sign-ins and logs stay on this computer. The repository must be
  private.* **Turn it on** / **Not now**.
- The cloud run's switch (D): which secret pays, the schedule (*Every 2 hours*, *Never*), *About a minute of Actions when it
  finds nothing*, *At most $1 a cloud run*.
- `TERMS`: `board_branch` (*the Board's branch*), `holds` (*holds the Board*), `cloud_run` (*cloud run*); the lines above,
  *A cloud run has the Board: it gives it back when it ends (at most 30 min)*, *Planned: the work starts on your computer*,
  *Another worker had the Board while you were offline: your changes since <time> are kept aside*.

## Done when

- With `[board]` on, the Board's pages and state are on `orkboard/board` within two minutes of a change, a secret never;
  a second clone takes the Board after the first gives it back and shows the same goals, phases and pages.
- Two hosts never write the branch at once (the push decides); a host offline loses nothing.
- Without `[board]`, nothing of this runs.
- The critical tests pass: `tests/test_architecture.py` (`realm/board_branch.py`, `realm/board_lease.py` import no
  `gui/`), `tests/test_board_alone.py`, `tests/test_updates.py`, and each part's own.
