"""Going on paid (docs/specs/105 §3): the Orkmaster's row when every subscription is dry and an API tool is on, none without one, and the answers, a yes and a wait,
both ending at the reset. Nothing is run by a tool billed by its API without the yes."""
from __future__ import annotations

import datetime as dt
import json
import time

import pytest

from orkboard import settings
from orkboard.core import bus as b
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, ideas, paid, tool_now
from orkboard.sources.limits import Limit

AT = float(int(time.time()))
H = 3600.0


def left(tool: str, share: float, resets_in: float = 6 * H, window: str = "session") -> Limit:
    return Limit(tool, "", window, share, dt.datetime.fromtimestamp(AT + resets_in))


def machine_of(*on: str, api: tuple[str, ...] = ()) -> settings.MachineSettings:
    m = settings.MachineSettings()
    for t in on:
        m.tools[t] = settings.ToolChoice(enabled=True, billing="api" if t in api else "subscription")
    return m


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    h.machine = machine_of("claude", "codex", api=("codex",))
    h.limits.rows = [left("claude", 0.0, 5 * H)]                    # the one subscription is out
    h.moves = []
    h.project.bus.subscribe(b.TOOL_MOVED, lambda e: h.moves.append(dict(e.data)))
    return h


def rows(host) -> list[dict]:
    return [n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "paid"]


def test_the_row_when_every_subscription_is_dry_and_an_api_tool_is_on(host):
    (row,) = rows(host)
    json.dumps(row)
    assert row["tool"] == "codex" and row["name"] == "Codex" and row["text"] == "Go on paid?" and row["blocks"] is True
    assert row["until"] == dt.datetime.fromtimestamp(AT + 5 * H).isoformat(timespec="minutes")
    assert row["usd_task"] is None or row["usd_task"] > 0
    assert host.snapshot()["mana"]["now"] is None                     # the work holds meanwhile
    assert host.snapshot()["needs_you"] == 1                          # a card of the hand like the others: it counts (decisions §178.5)


def test_no_row_without_an_api_tool_or_while_a_subscription_has_room(host):
    host.machine = machine_of("claude", "codex")                      # both by subscription
    assert rows(host) == []
    host.machine = machine_of("claude", "codex", api=("codex",))
    host.limits.rows = [left("claude", 0.0, 5 * H), left("codex", 0.5)]
    assert len(rows(host)) == 1 and host.snapshot()["mana"]["now"] is None    # codex has room, but it is billed by its API: it is no subscription to move on to
    host.machine = machine_of("claude", "agy", "codex", api=("codex",))
    host.limits.rows = [left("claude", 0.0, 5 * H), left("agy", 0.7)]
    assert rows(host) == [] and host.snapshot()["mana"]["now"] == "agy"
    host.limits.rows = []                                              # nothing read: no limit holds
    assert rows(host) == []


def test_the_row_carries_the_tools_own_cost_a_task_once_it_has_one(host):
    root = host.ideas.root()
    goal = ideas.add_track(root, "First goal")
    slug = host.command("ideas.add", {"text": "Something", "track": goal, "hold": True})["slug"]
    plan = {"idea": slug, "made_at": "x", "passed_at": "y", "todos": [], "tasks": [
        {"id": "k1", "state": "merged", "tool": "codex", "cost": 0.5, "role": "grunt"},
        {"id": "k2", "state": "merged", "tool": "codex", "cost": 0.3, "role": "grunt"},
        {"id": "k3", "state": "merged", "tool": "claude", "cost": 9.0, "role": "grunt"}]}
    ideas.save_plan(host.ideas.state_dir, slug, plan)
    assert host.ideas.usd_task_of("codex") == 0.4
    (row,) = rows(host)
    assert row["usd_task"] == 0.4


def test_a_yes_keeps_the_work_going_with_the_api_tool_until_the_reset(host):
    runner = host.ideas.runner(need=True)
    task = {"id": "k1", "kind": "code"}
    assert runner.tool_of("demo", task) == "claude"                    # no yes: nothing runs on the tool billed by its API
    got = host.command("ideas.paid", {"yes": True})
    assert got["ok"] is True and got["tool"] == "codex" and got["until"] == dt.datetime.fromtimestamp(AT + 5 * H).isoformat(timespec="minutes")
    assert rows(host) == []
    assert runner.tool_of("demo", task) == "codex"                     # the next task starts on it
    mana = host.snapshot()["mana"]
    assert mana["now"] == "codex" and mana["main"] == "claude"
    assert mana["paid"]["tool"] == "codex" and mana["paid"]["name"] == "Codex" and mana["paid"]["until"] == got["until"]      # the hand's slot after the potions (spec 105 D)
    assert mana["paid"]["usd_task"] is None or mana["paid"]["usd_task"] > 0
    json.dumps(mana)
    assert host.moves == [{"from": "claude", "to": "codex", "until": pytest.approx(AT + 5 * H, abs=1)}]
    kept = json.loads((host.ideas.state_dir / "paid.json").read_text())
    assert list(kept) == ["paid_until"] and kept["paid_until"] == pytest.approx(AT + 5 * H, abs=1)
    lines = [json.loads(ln) for ln in event_log.path(host.repo_root).read_text().splitlines()]
    assert [ln for ln in lines if ln["event"] == event_log.PAID_ANSWERED][0]["yes"] is True
    # it ends with the reset
    assert paid.until(host.ideas.state_dir, kept["paid_until"] + 1) is None
    assert tool_now.now(host.machine, host.limits.rows, kept["paid_until"] + 1, paid.until(host.ideas.state_dir, kept["paid_until"] + 1))["now"] == "claude"     # the subscription is back


def test_a_wait_is_not_asked_again_before_the_reset(host):
    assert host.command("ideas.paid", {"yes": False})["ok"] is True
    assert rows(host) == []
    assert host.snapshot()["needs_you"] == 0                          # answered: no longer counted
    mana = host.snapshot()["mana"]
    assert mana["paid"] is None                                        # a wait is no paid work: no slot
    assert mana["now"] is None and host.ideas.runner(need=True).tool_of("demo", {"id": "k1", "kind": "code"}) == "claude"
    kept = json.loads((host.ideas.state_dir / "paid.json").read_text())
    assert list(kept) == ["paid_wait"] and kept["paid_wait"] == pytest.approx(AT + 5 * H, abs=1)
    assert paid.waiting(host.ideas.state_dir, kept["paid_wait"] - 1) and not paid.waiting(host.ideas.state_dir, kept["paid_wait"] + 1)
    # a different window still dry after that reset asks again
    host.limits.rows = [left("claude", 0.0, 5 * H + 2 * H)]
    assert paid.row(host.ideas.state_dir, host.machine, {"now": None, "until": AT + 7 * H}, None, kept["paid_wait"] + 1)[0]["kind"] == "paid"


def test_a_yes_replaces_a_wait_and_the_other_way_round(host):
    host.command("ideas.paid", {"yes": False})
    assert list(json.loads((host.ideas.state_dir / "paid.json").read_text())) == ["paid_wait"]
    state = host.ideas.state_dir
    paid.answer(state, True, AT + 5 * H, AT)
    assert list(json.loads((state / "paid.json").read_text())) == ["paid_until"]
    paid.answer(state, False, None, AT)                                # no reset known: the five-hour window
    assert json.loads((state / "paid.json").read_text()) == {"paid_wait": AT + tool_now.PAID_HOLD_S}


def test_the_answer_is_refused_when_nothing_asks(host):
    with pytest.raises(CommandError, match="yes is true or false"):
        host.command("ideas.paid", {"yes": "maybe"})
    host.limits.rows = [left("claude", 0.9)]
    with pytest.raises(CommandError, match="Nothing asks to go on paid now"):
        host.command("ideas.paid", {"yes": True})
    host.machine = machine_of("claude", "codex")
    host.limits.rows = [left("claude", 0.0, 5 * H)]
    with pytest.raises(CommandError, match="Nothing asks"):
        host.command("ideas.paid", {"yes": True})
    assert not (host.ideas.state_dir / "paid.json").exists()


def test_the_command_is_the_boards_and_a_phones(host):
    from orkboard.gui.board_host import BoardPhone
    assert "ideas.paid" in host.commands and BoardPhone.allowed(host, "ideas.paid", {})


def test_the_row_is_not_asked_in_the_demo(fake_repo):
    h = Orkboard(fake_repo, demo=True)
    h.machine = machine_of("claude", "codex", api=("codex",))
    h.limits.rows = [left("claude", 0.0, 5 * H)]
    assert rows(h) == []
