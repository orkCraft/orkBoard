"""The phone's inbox read on the host (realm/remote_inbox.py, spec 136 B, decisions §243.2–4): two clones of one bare repository, both
ticking, a goal laid once; a refused push taken again; a goal that cannot be read taken with its error; `clean`'s rules; nothing ever
written to the inbox; the glue's `Ideas.add` keeping the inbox id."""
from __future__ import annotations

import base64
import datetime as dt
import json
import subprocess
from pathlib import Path

import pytest

from orkboard.realm import event_log, remote_inbox as ri, remote_journal as rj

NOW = dt.datetime(2026, 11, 4, 14, 0, 0)
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32
CONFIG = rj.JournalConfig(inbox="orkboard/inbox")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def clone(origin: Path, where: Path) -> Path:
    subprocess.run(["git", "clone", "-q", str(origin), str(where)], check=True, capture_output=True)
    git(where, "config", "user.email", "t@x")
    git(where, "config", "user.name", "T")
    (where / ".gitignore").write_text(".orkcraft/\n")
    (where / "orkcraft.toml").write_text('[journal]\ninbox = "orkboard/inbox"\n')
    return where


def goal_file(id_: str, text: str = "Make the table sort", **more) -> dict:
    return {"v": 1, "id": id_, "device": "phone1", "at": "2026-11-04T14:02:11+01:00", "text": text, **more}


def drop(phone: Path, files: dict[str, str | bytes]) -> None:
    """What the phone does: files added to `orkboard/inbox` (a branch of its own), never edited. Here by a clone of its own."""
    has = subprocess.run(["git", "rev-parse", "--verify", "-q", "origin/orkboard/inbox"], cwd=phone, capture_output=True).returncode == 0
    if has:
        git(phone, "checkout", "-q", "-B", "orkboard/inbox", "origin/orkboard/inbox")
    else:
        git(phone, "checkout", "-q", "--orphan", "orkboard/inbox")
        git(phone, "rm", "-rfq", "--ignore-unmatch", ".")
    for name, body in files.items():
        f = phone / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(body if isinstance(body, bytes) else body.encode())
    git(phone, "add", "-A")
    git(phone, "commit", "-qm", "goal")
    git(phone, "push", "-q", "origin", "orkboard/inbox")
    git(phone, "fetch", "-q", "origin")


@pytest.fixture
def world(tmp_path: Path):
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(origin)], check=True, capture_output=True)
    seed = tmp_path / "seed"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "t@x")
    git(seed, "config", "user.name", "T")
    (seed / "a.txt").write_text("one\n")
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "start")
    git(seed, "remote", "add", "origin", str(origin))
    git(seed, "push", "-q", "origin", "main")
    a, b, phone = clone(origin, tmp_path / "a"), clone(origin, tmp_path / "b"), clone(origin, tmp_path / "phone")
    return origin, a, b, phone


class Board:
    """A host's Board as the glue gives it: what `lay` and `find` see."""

    def __init__(self, refuse: str = "") -> None:
        self.laid: dict[str, str] = {}
        self.refuse = refuse

    def lay(self, goal: dict, inbox_id: str) -> str:
        if self.refuse and self.refuse in goal["text"]:
            raise RuntimeError("A goal needs a party")
        self.laid[inbox_id] = slug = f"goal-{len(self.laid) + 1}"
        self.goal = goal
        return slug

    def find(self, inbox_id: str) -> str:
        return self.laid.get(inbox_id, "")


def tick(root: Path, board: Board, name: str, ctx: ri.Context | None = None, **kw) -> dict:
    return ri.take(root, root / ".orkcraft", CONFIG, ctx or ri.Context(parties={"tech"}, types=lambda p: {"bug"}), board.lay, board.find,
                   name, kw.pop("now", NOW), force=True, **kw)


def journal_taken(origin: Path) -> list[dict]:
    return json.loads(git(origin, "show", "orkboard/journal:taken.json"))["taken"]


def test_two_hosts_reading_the_same_inbox_lay_a_goal_once(world):
    origin, a, b, phone = world
    drop(phone, {"inbox/phone1/01JC0000000000000001.json": json.dumps(goal_file("01JC0000000000000001", party="tech", element="ice"))})
    ba, bb = Board(), Board()
    got_a, got_b = tick(a, ba, "host-a"), tick(b, bb, "host-b")
    assert (got_a["taken"], got_a["laid"]) == (1, 1) and (ba.goal["party"], ba.goal["element"]) == ("tech", "ice")
    assert got_b["taken"] == 0 and bb.laid == {} and got_b["laid"] == 0       # b found it taken: its push was refused, it laid nothing
    rows = journal_taken(origin)
    assert [(r["id"], r["by"], r["slug"], r["error"]) for r in rows] == [("01JC0000000000000001", "host-a", "goal-1", "")]
    assert json.loads(git(origin, "show", "orkboard/journal:status.json"))["taken"][0]["slug"] == "goal-1"
    assert tick(a, ba, "host-a")["laid"] == 0 and tick(b, bb, "host-b")["laid"] == 0         # and not on the next tick either
    assert len(ba.laid) == 1 and not bb.laid


def test_a_refused_push_is_taken_again_with_what_is_left(world):
    origin, a, b, phone = world
    drop(phone, {"inbox/phone1/01JC0000000000000001.json": json.dumps(goal_file("01JC0000000000000001", "first"))})
    ba, bb = Board(), Board()
    tick(b, bb, "host-b")                                    # b has sent the journal once: it holds a journal ref that will go stale
    assert list(bb.laid) == ["01JC0000000000000001"]
    drop(phone, {"inbox/phone1/01JC0000000000000002.json": json.dumps(goal_file("01JC0000000000000002", "second"))})
    drop(phone, {"inbox/phone1/01JC0000000000000003.json": json.dumps(goal_file("01JC0000000000000003", "third"))})
    tick(a, ba, "host-a")                                    # a takes both new ones … and the first, taken by b, it merges when refused
    assert set(ba.laid) == {"01JC0000000000000002", "01JC0000000000000003"}
    # a third goal arrives while b's journal ref is stale: its first push is refused, it fetches, finds 2 and 3 taken
    drop(phone, {"inbox/phone1/01JC0000000000000004.json": json.dumps(goal_file("01JC0000000000000004", "fourth"))})
    got = tick(b, bb, "host-b")
    assert got["taken"] == 1 and set(bb.laid) == {"01JC0000000000000001", "01JC0000000000000004"}
    ids = {r["id"]: r["by"] for r in journal_taken(origin)}
    assert ids == {"01JC0000000000000001": "host-b", "01JC0000000000000002": "host-a", "01JC0000000000000003": "host-a",
                   "01JC0000000000000004": "host-b"}


def test_a_broken_goal_is_taken_with_its_error_and_not_read_again(world):
    origin, a, _, phone = world
    drop(phone, {"inbox/phone1/01JC0000000000000001.json": "{not json",
                 "inbox/phone1/01JC0000000000000002.json": json.dumps(goal_file("01JC0000000000000002", "  ")),
                 "inbox/phone1/notes.txt": "anything else is nothing"})
    board = Board()
    got = tick(a, board, "host-a")
    assert (got["read"], got["taken"], got["errors"], board.laid) == (2, 2, 2, {})
    rows = journal_taken(origin)
    assert [r["slug"] for r in rows] == ["", ""] and all(r["error"].startswith("Could not read this goal: ") for r in rows)
    again = tick(a, board, "host-a")
    assert (again["taken"], again["errors"]) == (0, 0)
    said = [r for r in event_log.read(a, since="2026-01-01") if r.get("event") == event_log.INBOX_TAKEN]
    assert len(said) == 2 and all(r["error"] for r in said)


def test_a_goal_the_board_refuses_is_taken_with_the_adds_words(world):
    origin, a, _, phone = world
    drop(phone, {"inbox/phone1/01JC0000000000000001.json": json.dumps(goal_file("01JC0000000000000001", "refuse me"))})
    got = tick(a, Board(refuse="refuse"), "host-a")
    assert (got["taken"], got["laid"], got["errors"]) == (1, 0, 1)
    row = journal_taken(origin)[0]
    assert row["slug"] == "" and row["error"] == "A goal needs a party"


def test_a_goal_already_on_the_board_is_not_laid_again_and_one_taken_and_not_laid_is_laid_after_a_stop(world):
    origin, a, _, phone = world
    drop(phone, {"inbox/phone1/01JC0000000000000001.json": json.dumps(goal_file("01JC0000000000000001")),
                 "inbox/phone1/01JC0000000000000002.json": json.dumps(goal_file("01JC0000000000000002"))})
    board = Board()
    board.laid["01JC0000000000000001"] = "already-there"       # the host stopped between the add and its journal
    got = tick(a, board, "host-a")
    assert got["laid"] == 2 and list(board.laid) == ["01JC0000000000000001", "01JC0000000000000002"]
    assert {r["id"]: r["slug"] for r in journal_taken(origin)}["01JC0000000000000001"] == "already-there"
    # taken in the journal, the host stops before the add: the next tick lays it
    done = {"by": "host-a", "at": NOW.isoformat(), "error": ""}
    rj.write_taken(a / ".orkcraft", [{"id": "01JC0000000000000001", "slug": "already-there", **done}, {"id": "01JC0000000000000002", "slug": "", **done}])
    board.laid.clear()
    assert tick(a, board, "host-a")["laid"] == 1 and list(board.laid) == ["01JC0000000000000002"]


def test_nothing_is_written_to_the_inbox_nor_to_the_working_tree(world):
    origin, a, _, phone = world
    drop(phone, {"inbox/phone1/01JC0000000000000001.json": json.dumps(goal_file("01JC0000000000000001"))})
    before = git(origin, "rev-parse", "orkboard/inbox")
    branch, status = git(a, "branch", "--show-current"), git(a, "status", "--porcelain")
    tick(a, Board(), "host-a")
    assert git(origin, "rev-parse", "orkboard/inbox") == before
    assert git(a, "branch", "--show-current") == branch and git(a, "status", "--porcelain") == status
    assert not (a / "inbox").exists()


def test_no_inbox_branch_yet_is_nothing_and_a_failed_fetch_is_said_not_raised(world, tmp_path):
    origin, a, _, _ = world
    got = tick(a, Board(), "host-a")
    assert (got["read"], got["taken"], got["why"]) == (0, 0, "")
    git(a, "remote", "set-url", "origin", str(tmp_path / "nowhere.git"))
    got = tick(a, Board(), "host-a")
    assert got["why"] and got["taken"] == 0
    said = [r for r in event_log.read(a, since="2026-01-01") if r.get("event") == event_log.INBOX_TAKEN]
    assert said and said[-1]["ok"] is False


def test_it_reads_at_most_every_two_minutes(world):
    _, a, _, _ = world
    board = Board()
    ctx = ri.Context(parties={"tech"})
    ri.take(a, a / ".orkcraft", CONFIG, ctx, board.lay, board.find, "h", NOW)
    assert not ri.due(a / ".orkcraft", NOW + dt.timedelta(seconds=60)) and ri.due(a / ".orkcraft", NOW + dt.timedelta(seconds=121))


def test_a_goal_laid_comes_with_its_photos(world):
    _, a, _, phone = world
    drop(phone, {"inbox/phone1/01JC0000000000000001.json": json.dumps(goal_file("01JC0000000000000001", photos=["01JC0000000000000001.1.jpg"])),
                 "inbox/phone1/01JC0000000000000001.1.jpg": PNG})
    board = Board()
    assert tick(a, board, "host-a")["laid"] == 1
    assert [base64.b64decode(p["data"]) for p in board.goal["photos"]] == [PNG]


# -- clean ------------------------------------------------------------------------------------------------------------------

E = ri.Entry("01JC0000000000000001", "phone1", "inbox/phone1/01JC0000000000000001.json")
CTX = ri.Context(parties={"tech", "design"}, types=lambda p: {"bug"} if p == "tech" else set(), chars=20)


def test_clean_keeps_what_is_the_projects_and_drops_the_rest():
    goal, err = ri.clean(json.dumps(goal_file(E.id, "x" * 50, party="tech", type="bug", element=CTX.elements[0], asks={"steps": "click", "n": 3},
                                              marks=[{"map": "system"}])), E, CTX)
    assert err == "" and goal == {"text": "x" * 20, "party": "tech", "type": "bug", "asks": {"steps": "click"}, "element": CTX.elements[0],
                                  "marks": [{"map": "system"}]}
    goal, _ = ri.clean(json.dumps(goal_file(E.id, party="gone", type="bug", element="nope")), E, CTX)
    assert goal == {"text": "Make the table sort"[:20]}                              # not the project's party, rune: the route decides
    goal, _ = ri.clean(json.dumps(goal_file(E.id, party="design", type="bug")), E, CTX)
    assert goal == {"text": "Make the table sort"[:20], "party": "design"}           # a type the party is not offered is dropped


@pytest.mark.parametrize("raw,why", [("[]", "goal's file"), ("nope", "goal's file"), (json.dumps({"v": 2, "text": "x"}), "version"),
                                     (json.dumps({"v": 1, "text": "   "}), "no words"), (json.dumps({"v": 1}), "no words")])
def test_clean_refuses_what_cannot_be_read_in_words(raw, why):
    goal, err = ri.clean(raw, E, CTX)
    assert goal is None and err.startswith("Could not read this goal: ") and why in err


def test_clean_keeps_only_the_photos_beside_it_within_their_limits():
    big = ri.PHOTO_BYTES + 1
    entry = ri.Entry(E.id, "phone1", E.path, tuple((f"inbox/phone1/{E.id}.{n}.jpg", s) for n, s in enumerate([10, big, 10, 10, 10, 10], 1)))
    bodies = {p: (PNG if s <= 10 else b"0" * s) for p, s in entry.photos}
    bodies[entry.photos[2][0]] = b"not an image"
    goal, _ = ri.clean(json.dumps(goal_file(E.id)), entry, CTX, lambda p: bodies[p])
    assert len(goal["photos"]) == 4                                            # the big one and the non-image dropped; four is the most
    goal, _ = ri.clean(json.dumps(goal_file(E.id)), entry, CTX)
    assert "photos" not in goal


# -- the glue: Ideas.add keeps the inbox id ---------------------------------------------------------------------------------

def test_ideas_add_keeps_the_inbox_id_of_a_goal_laid_from_the_inbox(fake_repo):
    from orkboard.gui.board_host import Orkboard
    from orkboard.gui import phone_journal
    host = Orkboard(fake_repo)
    p = host.project
    from orkboard.realm import ideas
    party = ideas.add_track(p.ideas.root(), "Chips")
    pj = phone_journal.PhoneJournal(host)
    slug = pj.lay(p)({"text": "A goal from the phone", "party": party}, "01JC0000000000000009")
    assert pj.find(p)("01JC0000000000000009") == slug and pj.find(p)("01JC0000000000000008") == ""
    st = json.loads((Path(p.ideas.state_dir) / "ideas" / slug / "state.json").read_text())
    assert (st["via"], st["inbox_id"]) == ("inbox", "01JC0000000000000009")
    other = p.ideas.add({"text": "A goal from the page", "track": party, "via": "inbox", "inbox_id": "x"})["slug"]      # a bad id is not kept
    assert json.loads((Path(p.ideas.state_dir) / "ideas" / other / "state.json").read_text()).get("inbox_id", "") == ""


# -- A.2 and A.3: asked for once; urgent when a card came to the hand -----------------------------------------------------------

@pytest.fixture
def pj(fake_repo, monkeypatch):
    from orkboard.gui import phone_journal
    from orkboard.gui.board_host import Orkboard
    monkeypatch.setattr(phone_journal, "paired", lambda: True)
    host = Orkboard(fake_repo)
    return phone_journal.PhoneJournal(host), host


def test_the_journal_is_asked_for_once_when_a_phone_is_paired_and_origin_is_on_github(pj, fake_repo, monkeypatch):
    j, host = pj
    assert j.ask()["ask"] is False                                              # no origin at all
    git(fake_repo, "remote", "add", "origin", "https://gitlab.com/me/mine.git")
    assert j.ask()["ask"] is False                                              # not on github.com
    git(fake_repo, "remote", "set-url", "origin", "git@github.com:me/mine.git")
    asked = j.ask()
    assert asked["ask"] is True and "orkboard/inbox" in asked["line"] and asked["line"].startswith("Follow this project from your phone away from home?")
    monkeypatch.setattr("orkboard.gui.phone_journal.paired", lambda: False)
    assert j.ask()["ask"] is False                                              # no phone paired
    monkeypatch.setattr("orkboard.gui.phone_journal.paired", lambda: True)
    assert j.not_now() == {"ok": True} and j.ask()["ask"] is False and rj.read_config(fake_repo) is None     # asked no more; nothing turned on


def test_turn_it_on_writes_the_journal_and_the_inbox_and_asks_no_more(pj, fake_repo):
    j, host = pj
    git(fake_repo, "remote", "add", "origin", "https://github.com/me/mine.git")
    assert j.ask()["ask"] is True
    assert j.turn_on()["inbox"] == "orkboard/inbox"
    assert rj.read_config(fake_repo).inbox == "orkboard/inbox" and j.ask()["ask"] is False
    assert {"journal.phone_ask", "journal.turn_on", "journal.not_now"} <= set(host.commands)


def test_a_card_that_came_to_the_hand_is_urgent_and_the_first_look_is_not(pj, monkeypatch):
    j, host = pj
    p = host.project
    rows = []
    monkeypatch.setattr(p.ideas, "board", lambda make=True: {"needs_you": rows})
    assert j._cards(p, 0.0) == (set(), frozenset(), False)
    rows.append({"idea": "g1", "kind": "asks"})
    assert j._cards(p, 5.0)[2] is False                                         # looked at too lately: no new look
    cards, goals, urgent = j._cards(p, 30.0)
    assert (cards, goals, urgent) == ({("g1", "asks")}, frozenset({"g1"}), True)
    assert j._cards(p, 60.0)[2] is False                                        # the same card is not news twice
    rows[:] = [{"idea": "g1", "kind": "asks"}, {"idea": "g2", "kind": "proposal"}]
    assert j._cards(p, 90.0)[2] is False                                        # a proposal waits for no one


def test_the_context_is_the_projects_parties_and_the_types_they_are_offered(pj):
    from orkboard.realm import ideas
    j, host = pj
    p = host.project
    party = ideas.add_track(p.ideas.root(), "Chips")
    ctx = j.context(p)
    assert party in ctx.parties and isinstance(ctx.types(party), set)
