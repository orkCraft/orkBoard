"""Spec 125 D (docs/specs/125-the-journals.md §D; decisions §203): a leader's digest of its own journal, written in the background on the cheaper tier. Due after `DIGEST_AFTER` entries and a
day; one call of the party's leader, step `journal`, no tools, given its old digest and the entries since; kept with the last entry it read; a call that fails keeps nothing; the trigger on
`ideas.add`; the event `journal_digested`. The model call is stubbed (`keeper.call`), as `tests/test_idea_project_q.py` does.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

import pytest

from orkboard.core import idea_keeper
from orkboard.core.idea_journal import DIGEST_AFTER, JournalMixin
from orkboard.gui.board_host import Orkboard
from orkboard.realm import event_log, goal_team, idea_spend, idea_target, ideas, journals, library

DIGEST = {"works": ["The person shrinks goals that touch the cache (goal-0), and the no's on it held."]}
DIGEST_TEXT = "Works: The person shrinks goals that touch the cache (goal-0), and the no's on it held."


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    assert isinstance(h.ideas.keeper, JournalMixin) and idea_keeper.JournalMixin is JournalMixin
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


@pytest.fixture
def design(host):
    return _party(host, "Design", "product-designer", ["artist"], "design")


class Model:
    """The keeper's call stubbed: `answer` the JSON (or text, or a callable of the call) every call gets, `calls` every call made."""

    def __init__(self, host, answer=DIGEST):
        self.host, self.calls, self.answer = host, [], answer
        host.ideas.keeper.call = self

    def steps(self, step):
        return [c for c in self.calls if c["step"] == step]

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        self.calls.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"],
                           "key": getattr(k._tls, "key", "")})
        answer = self.answer(self.calls[-1]) if callable(self.answer) else self.answer
        if isinstance(answer, Exception):
            raise answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""


@pytest.fixture
def model(host):
    return Model(host)


def _wait(host, party):
    for _ in range(1000):
        if not host.ideas.keeper.busy(f"goal:{party}"):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _fill(host, party, n=DIGEST_AFTER, start=0):
    for i in range(start, start + n):
        assert journals.add(host.ideas.state_dir, party, "stance", f"You said go on “Goal {i}”.", idea=f"goal-{i}")


def _old_digest(host, party, days=2):
    got = journals.save_digest(host.ideas.state_dir, party, "You know the cache.", journals.read(host.ideas.state_dir, party)[-1]["id"])
    at = (dt.datetime.now() - dt.timedelta(days=days)).isoformat(timespec="seconds")
    f = journals._file(host.ideas.state_dir, party, ".digest.json")
    f.write_text(json.dumps({**got, "at": at}), encoding="utf-8")


def _events(host):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == event_log.JOURNAL_DIGESTED]


# -- due and not due ---------------------------------------------------------------------------------------------------------------------

def test_a_journal_is_due_at_twelve_entries_after_its_digest_and_with_no_digest_or_one_a_day_old(host, tech):
    keeper = host.ideas.keeper
    assert DIGEST_AFTER == 12 and not keeper.journal_due(tech)
    _fill(host, tech, DIGEST_AFTER - 1)
    assert not keeper.journal_due(tech)                                       # eleven are too few
    _fill(host, tech, 1, start=99)
    assert keeper.journal_due(tech)                                           # twelve, no digest
    _old_digest(host, tech, days=2)
    assert not keeper.journal_due(tech)                                       # all of them are in the digest
    _fill(host, tech, DIGEST_AFTER - 1, start=200)
    assert not keeper.journal_due(tech)
    _fill(host, tech, 1, start=300)
    assert keeper.journal_due(tech)                                           # twelve after it, and it is two days old


# -- the call ------------------------------------------------------------------------------------------------------------------------------

def test_the_digest_is_one_call_of_the_partys_leader_on_the_cheaper_tier_with_no_tools_and_no_file_read(host, tech, model):
    _fill(host, tech)
    assert host.ideas.keeper.journal_digest(tech) is True
    _wait(host, tech)
    (call,) = model.calls
    assert call["step"] == "journal" and call["tools"] is False and call["key"] == f"goal:{tech}"
    assert (call["tier"], call["effort"]) == idea_target.pick("journal", "balance") == ("warrior", "low")
    assert call["budget"] == idea_target.budget("journal", "balance")
    p = call["prompt"]
    assert p.startswith("You are Architect, the leader of this goal's party")                                                        # its leader's voice
    assert "Read no file" in p and '{"works": ["…"], "hurts": ["…"], "next": ["…"]}' in p and str(journals.DIGEST_CHARS) in p
    assert "I said go on “Goal 0”." in p and "I said go on “Goal 11”." in p and "You said" not in p and "Your view so far" not in p            # no view yet


def test_the_call_is_given_its_old_digest_and_only_the_entries_since(host, tech, model):
    _fill(host, tech)
    _old_digest(host, tech)
    _fill(host, tech, DIGEST_AFTER, start=100)
    assert host.ideas.keeper.journal_digest(tech) is True
    _wait(host, tech)
    p = model.calls[0]["prompt"]
    assert "Your view so far:\nYou know the cache." in p
    assert "Goal 100" in p and "Goal 111" in p and "Goal 3”" not in p                    # the first twelve are in the digest already


# -- what is kept --------------------------------------------------------------------------------------------------------------------------

def test_the_digest_is_kept_with_the_last_entry_it_read_and_the_event_has_no_word_of_it(host, tech, model):
    _fill(host, tech)
    last = journals.read(host.ideas.state_dir, tech)[-1]["id"]
    assert host.ideas.keeper.journal_digest(tech) is True
    _wait(host, tech)
    got = journals.digest(host.ideas.state_dir, tech)
    assert got["text"] == DIGEST_TEXT and got["upto"] == last and got["read"] == ["goal-0"]
    assert journals.since_digest(host.ideas.state_dir, tech) == [] and not host.ideas.keeper.journal_due(tech)
    (ev,) = _events(host)
    assert ev["party"] == tech and ev["entries"] == DIGEST_AFTER and ev["chars"] == len(DIGEST_TEXT) and ev["why"] == "add" and ev["dropped"] == 0 and ev["cost"] == 0.01 and isinstance(ev["seconds"], float)
    assert DIGEST_TEXT not in json.dumps(ev) and "Goal" not in json.dumps(ev)
    assert "shrinks goals" in journals.text(host.ideas.state_dir, tech)                       # and it is read into the leader's calls from then on


def test_the_digest_runs_as_its_partys_step_in_the_specs_stage_of_its_partys_ledger(host, tech, model):
    _fill(host, tech)
    host.ideas.keeper.journal_digest(tech)
    _wait(host, tech)
    spent = idea_spend.of_goal(host.ideas.state_dir, tech)
    assert spent["usd"] == 0.01 and spent["stages"]["spec"]["usd"] == 0.01


# -- the trigger ---------------------------------------------------------------------------------------------------------------------------

def _add(host, party, **more):
    return host.command("ideas.add", {"text": "add a score board", "track": party, "hold": True, **more})


def test_adding_a_goal_digests_the_journal_of_each_party_on_its_route_that_is_due_quietly(host, tech, design, model):
    _fill(host, tech)
    _fill(host, design, DIGEST_AFTER - 1)
    got = _add(host, tech)
    assert "error" not in got
    _wait(host, tech)
    assert [c["key"] for c in model.steps("journal")] == [f"goal:{tech}"]                       # Tech's was due; Design's, eleven entries, was not
    assert journals.digest(host.ideas.state_dir, tech)["text"] == DIGEST_TEXT and journals.digest(host.ideas.state_dir, design) == {}


# -- the view's prompt (spec 167 F) --------------------------------------------------------------------------------------------------------

def _done_goal(host, party, title, gist, own, cites):
    root = host.ideas.root()
    slug = ideas.add_idea(root, gist, party)
    ideas.set_meta(root, slug, phase="done", route=party)
    page = ideas.idea_page(root, slug)
    page.sections += [("Tech", own), ("Decisions", "\n".join(f"- §{n}" for n in cites))]
    ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
    return slug


def _log(host, text):
    (host.ideas.state_dir / "project.json").write_text('{"decisions": "docs/decisions.md"}', encoding="utf-8")
    base, rel = host.ideas.keeper._decisions()                 # the Board's tree where it stands, else the working copy
    (base / rel).parent.mkdir(parents=True, exist_ok=True)
    (base / rel).write_text(text, encoding="utf-8")


def test_the_views_prompt_holds_a_done_goals_gist_and_the_decision_it_cites_and_asks_the_three_heads(host, tech, model):
    slug = _done_goal(host, tech, "Cache the lobby", "The lobby is cached for a minute.", "Tech built a keyed cache.", [7])
    _log(host, "# Decisions\n\n## 7. Cache the lobby for a minute (1 May, the owner)\n\nWhy: speed.\n\n## 8. No accounts (2 May, the owner)\n\nWhy: scope.\n")
    _fill(host, tech)
    assert host.ideas.keeper.journal_digest(tech) is True
    _wait(host, tech)
    p = model.calls[0]["prompt"]
    assert slug in p and "The lobby is cached for a minute." in p and "Tech built a keyed cache." in p
    assert "§7. Cache the lobby for a minute" in p and "§8. No accounts" in p
    assert '"works"' in p and '"hurts"' in p and '"next"' in p and "Read no file" in p


# -- every line traced, or dropped (spec 167 G) ----------------------------------------------------------------------------------------------

GIVEN = {"slugs": {"x-goal"}, "nums": {7}, "ids": {"cache"}}


# -- a goal done begins its route's views (spec 167 H) ---------------------------------------------------------------------------------------

def _wait_all(host, *parties):
    for p in parties:
        _wait(host, p)


def test_a_goal_done_begins_one_view_call_for_each_party_of_its_route(host, tech, design, model):
    slug = _done_goal(host, tech, "Cache", "The lobby is cached.", "Built.", [])
    ideas.set_meta(host.ideas.root(), slug, route=f"{tech}, {design}")
    assert host.ideas.views_when_done(slug) == 2
    _wait_all(host, tech, design)
    assert {c["key"] for c in model.steps("journal")} == {f"goal:{tech}", f"goal:{design}"}      # a call a party (one retry each: the stub names no source)


# -- the view read, and a look now (spec 167 I) -----------------------------------------------------------------------------------------------

def test_a_look_now_begins_one_call_and_a_second_ask_while_it_runs_begins_none(host, tech, model):
    keeper = host.ideas.keeper
    keeper._claim(f"goal:{tech}", "busy")
    assert host.ideas.view_look({"party": tech}) == {"ok": True, "asked": False, "why": "The leader is looking already"}
    keeper._busy.pop(f"goal:{tech}", None)
    assert host.ideas.view_look({"party": tech}) == {"ok": True, "asked": True}
    assert host.ideas.view_look({"party": tech})["asked"] is False
    _wait(host, tech)
    assert {c["key"] for c in model.steps("journal")} == {f"goal:{tech}"}

