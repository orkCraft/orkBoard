"""The phone's answers through the inbox (realm/remote_answers.py, gui/phone_journal.py `apply`; spec 137 C, decisions §244.5): two clones of one
bare repository ticking, an answer applied once; a card gone taken with its words; an unreadable file taken with its error; what names the card
comes from the Board's row, never from the file; the answer's own keys alone passed on; goals untouched by answer files."""
from __future__ import annotations

import json
from types import SimpleNamespace

from orkboard.gui import phone_journal
from orkboard.realm import remote_answers as ra, remote_inbox as ri
from tests.test_remote_inbox import NOW, CONFIG, Board, drop, goal_file, journal_taken, world  # noqa: F401  (world: fixture)

A1, A2 = "01JC00000000000000A1", "01JC00000000000000A2"


def answer_file(id_: str, card: str = "idea-1", kind: str = "talk", answer: dict | None = None, **more) -> dict:
    return {"v": 1, "id": id_, "device": "phone1", "at": "2026-11-04T14:02:11+01:00", "card": card, "kind": kind,
            "answer": {"answers": [{"id": "q1", "pick": 1}]} if answer is None else answer, **more}


class Hand:
    """The host's side: the cards that wait, and the commands the hand's answers go through."""

    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.called: list[tuple[str, dict]] = []
        self.refuse = ""

    def apply(self, answer: dict) -> tuple[str, str]:
        names = {v[0] for v in ra.KINDS.values()}
        p = SimpleNamespace(ideas=SimpleNamespace(board=lambda make=False: {"needs_you": self.rows}), commands={n: self.command(n) for n in names})
        return phone_journal.PhoneJournal.apply(p)(answer)

    def command(self, name: str):
        def run(args: dict):
            self.called.append((name, args))
            return {"error": self.refuse} if self.refuse else {"ok": True}
        return run


def tick(root, hand: Hand, name: str, **kw) -> dict:
    board = Board()
    return ri.take(root, root / ".orkcraft", CONFIG, ri.Context(parties={"tech"}), board.lay, board.find, name, kw.pop("now", NOW), force=True,
                   apply=hand.apply, **kw)


def test_an_answer_is_applied_once_by_the_hand_s_own_command_and_said_in_the_journal(world):
    origin, a, b, phone = world
    drop(phone, {f"inbox/phone1/{A1}.answer.json": json.dumps(answer_file(A1))})
    ha, hb = Hand([{"kind": "talk", "idea": "idea-1", "goal": "tech"}]), Hand([{"kind": "talk", "idea": "idea-1", "goal": "tech"}])
    got_a, got_b = tick(a, ha, "host-a"), tick(b, hb, "host-b")
    assert got_a["answered"] == 1 and got_b["answered"] == 0
    assert ha.called == [("ideas.talk_answer", {"idea": "idea-1", "answers": [{"id": "q1", "pick": 1}], "device": "phone"})] and hb.called == []
    assert [(r["id"], r["by"], r["slug"], r["error"]) for r in journal_taken(origin)] == [(A1, "host-a", "idea-1", "")]
    tick(a, ha, "host-a")
    tick(b, hb, "host-b")
    assert len(ha.called) == 1 and hb.called == []                                   # and not on the next tick either


def test_a_card_gone_is_taken_with_the_hosts_words_and_not_asked_again(world):
    origin, a, b, phone = world
    drop(phone, {f"inbox/phone1/{A1}.answer.json": json.dumps(answer_file(A1, card="gone"))})
    hand = Hand([{"kind": "talk", "idea": "idea-1"}])
    assert tick(a, hand, "host-a")["answer_errors"] == 1 and hand.called == []
    assert [(r["slug"], r["error"]) for r in journal_taken(origin)] == [("", "That card is gone, or answered already")]
    assert tick(a, hand, "host-a")["answer_errors"] == 0


def test_a_command_that_refuses_is_taken_with_its_words(world):
    origin, a, b, phone = world
    drop(phone, {f"inbox/phone1/{A1}.answer.json": json.dumps(answer_file(A1))})
    hand = Hand([{"kind": "talk", "idea": "idea-1"}])
    hand.refuse = "That is answered already"
    tick(a, hand, "host-a")
    assert [(r["slug"], r["error"]) for r in journal_taken(origin)] == [("", "That is answered already")]




def test_goals_and_answers_share_the_inbox_and_do_not_mix(world):
    origin, a, b, phone = world
    drop(phone, {"inbox/phone1/01JC0000000000000001.json": json.dumps(goal_file("01JC0000000000000001", party="tech")),
                 f"inbox/phone1/{A1}.answer.json": json.dumps(answer_file(A1))})
    board, hand = Board(), Hand([{"kind": "talk", "idea": "idea-1"}])
    got = ri.take(a, a / ".orkcraft", CONFIG, ri.Context(parties={"tech"}), board.lay, board.find, "host-a", NOW, force=True, apply=hand.apply)
    assert (got["laid"], got["answered"]) == (1, 1) and list(board.laid) == ["01JC0000000000000001"]
    assert [e.id for e in ri.entries(a)] == ["01JC0000000000000001"] and [x.id for x in ra.entries(a)] == [A1]






