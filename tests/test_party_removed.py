"""A party removed (docs/specs/80-a-party-removed.md, part A): `ideas.drop_track` and the host's `ideas.track_drop`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, idea_spend, ideas, own_parties


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party_with_goals(host, *texts):
    party = host.command("ideas.track_add", {"title": "Billing"})["slug"]
    slugs = [host.command("ideas.add", {"text": t, "track": party, "night": True})["slug"] for t in texts]
    return party, slugs


def _gone_events(host):
    return [e for e in event_log.read(Path(host.town.repo_root)) if e["event"] == event_log.PARTY_REMOVED]


def test_goals_move_to_general_and_the_page_goes(host):
    party, (a, b) = _party_with_goals(host, "alpha", "beta")
    root = host.ideas.root()
    got = host.command("ideas.track_drop", {"slug": party})
    assert got == {"ok": True, "moved": 2, "dropped": 0, "title": "Billing"}
    assert not (root / ideas.TRACKS / f"{party}.md").exists()
    assert party not in (root / ideas.TRACKS / "index.md").read_text(encoding="utf-8")
    board = host.command("ideas.board")
    assert [t["slug"] for t in board["tracks"]] == ["general"] and board["tracks"][0]["count"] == 2
    assert {i["slug"]: i["track"] for i in board["ideas"]} == {a: "general", b: "general"}
    assert [i["slug"] for i in ideas.ideas(root, "general")] == [a, b]            # their order kept


def test_goals_dropped_with_it_keep_their_spend(host):
    party, (a, b) = _party_with_goals(host, "alpha", "beta")
    state = host.ideas.state_dir
    idea_spend.append(state, {"at": "2026-10-25T10:00:00", "step": "read", "cost": 0.12}, idea=a)
    got = host.command("ideas.track_drop", {"slug": party, "goals": "drop"})
    assert got["moved"] == 0 and got["dropped"] == 2
    assert host.command("ideas.board")["ideas"] == []
    gone = (state / "ideas" / idea_spend.GONE).read_text(encoding="utf-8")
    assert json.loads(gone.splitlines()[0])["idea"] == a
    assert not (state / "ideas" / a).exists()


def test_an_empty_party_goes(host):
    party = host.command("ideas.track_add", {"title": "Empty"})["slug"]
    assert host.command("ideas.track_drop", {"slug": party})["moved"] == 0
    assert party not in [t["slug"] for t in host.command("ideas.board")["tracks"]]


def test_general_an_unknown_party_and_bad_goals_are_refused(host):
    host.command("ideas.track_add", {"title": "Billing"})
    with pytest.raises(CommandError, match="General stays: it is where goals without a party go"):
        host.command("ideas.track_drop", {"slug": "general"})
    with pytest.raises(CommandError, match="That party is gone"):
        host.command("ideas.track_drop", {"slug": "nope"})
    with pytest.raises(CommandError, match="That party is gone"):
        host.command("ideas.track_drop", {"slug": "../x"})
    with pytest.raises(CommandError, match="move"):
        host.command("ideas.track_drop", {"slug": "billing", "goals": "burn"})
    assert [t["slug"] for t in host.command("ideas.board")["tracks"]] == ["general", "billing"] or "billing" in [t["slug"] for t in host.command("ideas.board")["tracks"]]


@pytest.mark.parametrize("how", ["state", "keeper", "runner"])
def test_a_goal_at_work_refuses_and_nothing_changes(host, how):
    party, (a, b) = _party_with_goals(host, "alpha", "beta")
    if how == "state":
        ideas.save_state(host.ideas.state_dir, a, state="working")
    elif how == "keeper":
        host.ideas.keeper._busy[a] = "reading"
    else:
        host.ideas._runner = type("R", (), {"_runs": {(a, "k1"): object()}, "busy": lambda self: True})()
    with pytest.raises(CommandError, match=r"^1 goal at work: stop it first$"):
        host.command("ideas.track_drop", {"slug": party})
    with pytest.raises(CommandError, match="1 goal at work"):
        host.command("ideas.track_drop", {"slug": party, "goals": "drop"})
    root = host.ideas.root()
    assert (root / ideas.TRACKS / f"{party}.md").exists()
    assert {i["slug"] for i in ideas.ideas(root, party)} == {a, b}
    assert _gone_events(host) == []


def test_two_goals_at_work_say_so(host):
    party, (a, b) = _party_with_goals(host, "alpha", "beta")
    for s in (a, b):
        ideas.save_state(host.ideas.state_dir, s, state="working")
    with pytest.raises(CommandError, match=r"^2 goals at work: stop them first$"):
        host.command("ideas.track_drop", {"slug": party})


def test_the_event_names_the_party_and_the_face(host):
    party, _ = _party_with_goals(host, "alpha")
    host.command("ideas.track_drop", {"slug": party, "device": "phone"})
    (e,) = _gone_events(host)
    assert (e["slug"], e["title"], e["moved"], e["dropped"], e["face"]) == (party, "Billing", 1, 0, "phone")


def test_the_proposal_of_the_party_goes(host):
    party, _ = _party_with_goals(host, "alpha")
    folder = host.ideas.state_dir / "goals" / party
    folder.mkdir(parents=True)
    (folder / "party-proposal.json").write_text('{"by": "x", "runs": 8}', encoding="utf-8")
    host.command("ideas.track_drop", {"slug": party})
    assert not (folder / "party-proposal.json").exists()


def test_readers_still_answer_when_something_names_the_removed_party(host):
    party, (a,) = _party_with_goals(host, "alpha")
    other = host.command("ideas.track_add", {"title": "Other"})["slug"]
    host.command("ideas.move", {"slug": a, "track": other})                      # a route: from `party`, to `other`
    assert [m["from"] for m in host.command("ideas.board")["ideas"] and __import__("orkboard.realm.idea_route", fromlist=["x"]).moves(host.ideas.state_dir, a)] == [party]
    pid = own_parties.save(name="Mine", craft="engineering", leader="architect", team=["grunt", "tester", "reviewer"], every=["reviewer"])
    own_parties.used(pid, "aaaaaaaaaaaa", "shop", party)                         # an own party's use of the removed party
    host.command("ideas.track_drop", {"slug": party})
    for command, args in (("ideas.board", {}), ("ideas.map", {}), ("ideas.recap", {"since": 0}), ("ideas.page", {"slug": a}),
                          ("ideas.parties", {}), ("ideas.week", {})):
        json.dumps(host.command(command, args))
    with pytest.raises(CommandError, match="That party is gone"):
        host.command("ideas.party", {"goal": party})
