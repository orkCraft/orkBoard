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

from orkboard.core import idea_journal, idea_keeper
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


def test_a_digest_less_than_a_day_old_is_not_due_again_however_many_entries_follow_it(host, tech):
    _fill(host, tech)
    _old_digest(host, tech, days=0)
    _fill(host, tech, DIGEST_AFTER, start=100)
    assert len(journals.since_digest(host.ideas.state_dir, tech)) == DIGEST_AFTER and not host.ideas.keeper.journal_due(tech)
    f = journals._file(host.ideas.state_dir, tech, ".digest.json")
    f.write_text(json.dumps({**journals.digest(host.ideas.state_dir, tech), "at": (dt.datetime.now() - dt.timedelta(days=1, minutes=1)).isoformat(timespec="seconds")}), encoding="utf-8")
    assert host.ideas.keeper.journal_due(tech)


def test_nothing_is_begun_for_a_journal_that_is_not_due_a_party_that_is_gone_or_a_call_that_cannot_be_made(host, tech, model):
    keeper = host.ideas.keeper
    assert keeper.journal_digest(tech) is False and model.calls == []         # nothing to digest
    _fill(host, tech)
    assert keeper.journal_digest("ghost") is False
    keeper.budget_ok = lambda: False                                          # today's spend limit: no call, no error
    assert keeper.journal_digest(tech) is False and model.calls == []
    keeper.budget_ok = lambda: True
    keeper.demo = True
    assert keeper.journal_digest(tech) is False and model.calls == []
    keeper.demo = False
    keeper.window_until = lambda: time.time() + 3600                          # a spent window: no error either
    assert keeper.journal_digest(tech) is False and model.calls == []


def test_a_party_the_keeper_is_busy_with_is_skipped_never_an_error(host, tech, model):
    _fill(host, tech)
    keeper = host.ideas.keeper
    keeper._claim(f"goal:{tech}", "looking")
    assert keeper.journal_digest(tech) is False and model.calls == []
    keeper._busy.pop(f"goal:{tech}")
    assert keeper.journal_digest(tech) is True
    _wait(host, tech)


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


def test_the_step_has_its_tables_and_its_tier(host):
    assert "journal" in idea_target.STEPS and idea_spend.STEP_STAGE["journal"] == "spec"
    for target in idea_target.TARGETS:
        assert idea_target.pick("journal", target) == idea_target.pick("concerns", target)
    assert idea_target.pick("journal", "thrift") == ("laborer", "") and idea_target.pick("journal", "quality") == ("warrior", "medium")
    assert idea_target.READS["journal"] == 0 and idea_target.CONTEXT["journal"] == 10_000 and idea_target.CAPS["journal"] == 0.05
    assert idea_target.budget("journal", "balance") == 0.15                                # never under 1.5 floors, as for every cheaper step
    assert set(idea_target.MATRIX) >= set(idea_target.STEPS)


def test_a_long_journal_is_given_the_newest_entries_that_fit(host, tech, model):
    for i in range(80):
        journals.add(host.ideas.state_dir, tech, "stance", f"You said go on “Goal {i}” " + "w" * 250, idea=f"goal-{i}")
    host.ideas.keeper.journal_digest(tech)
    _wait(host, tech)
    p = model.calls[0]["prompt"]
    assert "Goal 79" in p and "Goal 0”" not in p and len(p) < idea_target.CONTEXT["journal"] + 3000


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


def test_a_view_is_cut_to_the_limit_in_whole_lines_and_made_one_line(host, tech, model):
    model.answer = {"works": ["A line\n  on goal-0.", "Another goal-1 " + "z" * 2000, "Short goal-2."]}
    _fill(host, tech)
    host.ideas.keeper.journal_digest(tech)
    _wait(host, tech)
    text = journals.digest(host.ideas.state_dir, tech)["text"]
    assert text == "Works: A line on goal-0.; Short goal-2." and "\n" not in text and len(text) <= journals.DIGEST_CHARS


@pytest.mark.parametrize("answer", ["not json", {"digest": ""}, {"digest": "A digest of no view."}, {"works": ["It names nothing given."]}, {"other": "x"}, RuntimeError("the tool failed")])
def test_a_call_that_fails_keeps_nothing_and_the_next_trigger_tries_again(host, tech, model, answer):
    _fill(host, tech)
    model.answer = answer
    assert host.ideas.keeper.journal_digest(tech) is True
    _wait(host, tech)
    assert len(model.calls) == 2                                                          # asked once more
    assert journals.digest(host.ideas.state_dir, tech) == {} and _events(host) == [] and host.ideas.keeper.journal_due(tech)
    model.answer = DIGEST
    assert host.ideas.keeper.journal_digest(tech) is True
    _wait(host, tech)
    assert journals.digest(host.ideas.state_dir, tech)["text"] == DIGEST_TEXT


def test_a_stop_keeps_nothing(host, tech, model):
    _fill(host, tech)

    def stopped(call):
        host.ideas.keeper._tls.cancel.set()
        return DIGEST
    model.answer = stopped
    host.ideas.keeper.journal_digest(tech)
    _wait(host, tech)
    assert journals.digest(host.ideas.state_dir, tech) == {} and _events(host) == []


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


def test_a_trigger_that_breaks_never_troubles_the_goal(host, tech, model, monkeypatch):
    _fill(host, tech)

    def boom(self, parties):
        raise RuntimeError("no")
    monkeypatch.setattr(JournalMixin, "journal_digest_for", boom)
    got = _add(host, tech)
    assert got["slug"] and ideas.idea_page(host.ideas.root(), got["slug"]) is not None and model.steps("journal") == []


def test_a_goal_added_with_no_journal_due_makes_no_digest_call(host, tech, model):
    _add(host, tech)
    assert model.steps("journal") == []
    assert idea_journal.JournalMixin.journal_digest_for(host.ideas.keeper, [tech, "", tech]) == 0


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


def test_the_views_prompt_reads_only_the_goals_done_since_the_last_view(host, tech):
    old = _done_goal(host, tech, "Old goal", "Long ago.", "Tech did it.", [])
    keeper = host.ideas.keeper
    assert old in keeper.journal_prompt(tech, {}, [])
    later = (dt.datetime.now() + dt.timedelta(days=1)).isoformat(timespec="seconds")
    after = keeper.journal_prompt(tech, {"text": "You know.", "at": later}, [])
    assert old not in after and "Your view so far:\nYou know." in after


def test_the_views_prompt_names_the_parts_of_the_map_the_open_concerns_are_on_never_their_words(host, tech):
    from orkboard.realm import concerns
    concerns.save(host.ideas.state_dir, tech, concerns=[{"id": "c1", "on": "cache", "name": "The cache", "level": "alert", "what": "SECRET-WORDS", "why": "", "fix": "", "signal": "", "aspect": ""}])
    p = host.ideas.keeper.journal_prompt(tech, {}, [])
    assert "The cache (cache)" in p and "SECRET-WORDS" not in p


def test_the_views_prompt_holds_the_partys_table_where_it_has_one(host, tech):
    folder = host.ideas.root() / "pages" / "tables"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{tech}.md").write_text("# Table\n\nThe hero lays the cache first.\n", encoding="utf-8")
    assert "The hero lays the cache first." in host.ideas.keeper.journal_prompt(tech, {}, [])


def test_product_with_no_tree_is_told_so_and_an_answer_in_heads_is_read(host):
    product = _party(host, "Product", "product-manager", ["pm"], "product")
    assert product == "product"
    assert "Product's tree is not on the Board." in host.ideas.keeper.journal_prompt(product, {}, [])
    given = {"slugs": {"x-goal"}, "nums": {7}, "ids": {"cache"}}
    assert idea_journal.clean({"works": ["a (x-goal)"], "hurts": [], "next": ["b §7"]}, given) == ("Works: a (x-goal) Next: b §7", ["x-goal", "§7"], 0)


# -- every line traced, or dropped (spec 167 G) ----------------------------------------------------------------------------------------------

GIVEN = {"slugs": {"x-goal"}, "nums": {7}, "ids": {"cache"}}


def test_a_line_naming_nothing_the_call_was_given_is_dropped_and_counted():
    raw = {"works": ["Fine, x-goal", "Fine, but nothing named"], "hurts": ["Slow, §7", "Slow, §8", "Slow, §7 and §8"], "next": ["The cache (cache) next", "x-goal-2 is another", "Ship it"]}
    text, read, dropped = idea_journal.clean(raw, GIVEN)
    assert text == "Works: Fine, x-goal Hurts: Slow, §7 Next: The cache (cache) next" and read == ["x-goal", "§7", "cache"] and dropped == 5
    assert idea_journal.clean({"works": ["Nothing named"]}, GIVEN) is None and idea_journal.clean({"works": ["x-goal"]}, None) is None


def test_the_views_words_never_say_you():
    assert idea_journal.clean({"works": ["You said no to x-goal", "Your no on x-goal held", "x-goal holds"]}, GIVEN) == ("Works: x-goal holds", ["x-goal"], 2)


def test_product_with_no_tree_says_so_in_code_and_names_no_job(host, model):
    product = _party(host, "Product", "product-manager", ["pm"], "product")
    assert product == "product"
    journals.add(host.ideas.state_dir, product, "stance", "You said go on “Cache”.", idea="cache-goal")
    model.answer = {"works": ["The cache is cached, cache-goal."]}
    for i in range(DIGEST_AFTER):
        journals.add(host.ideas.state_dir, product, "stance", f"You said go on “G{i}”.", idea="cache-goal")
    assert host.ideas.keeper.journal_digest(product) is True
    _wait(host, product)
    got = journals.digest(host.ideas.state_dir, product)
    assert "Hurts: Product's tree is not on the Board yet (163-products-tree-on-the-board)." in got["text"] and "163-products-tree-on-the-board" in got["read"]
    assert "job" not in got["text"].lower()
    nothing = {"hurts": ["No source named here."]}
    assert idea_journal.clean(nothing, GIVEN, no_tree=True) is None             # the code adds its line only to a view that has lines


def test_a_decision_placed_in_a_journal_by_its_titles_words_never_reaches_the_view(host, tech, model):
    journals.add(host.ideas.state_dir, tech, "decision", "Decision 12: Cache the lobby (by its words, no goal)", ref="docs/decisions.md#12")
    _fill(host, tech)
    host.ideas.keeper.journal_digest(tech)
    _wait(host, tech)
    assert "Cache the lobby" not in model.calls[0]["prompt"] and "I said go on" in model.calls[0]["prompt"]
    assert idea_journal.view_entries([{"kind": "decision"}, {"kind": "stance"}]) == [{"kind": "stance"}]


def test_a_stored_line_is_read_into_the_view_call_in_the_leaders_voice(host, tech, model):
    assert idea_journal.voiced("You said no to “A”; your no was overruled. You are right, You have won.") == "I said no to “A”; my no was overruled. I am right, I have won."
    journals.add(host.ideas.state_dir, tech, "overruled", "You said no to the cache; your no was overruled.", idea="goal-9")
    _fill(host, tech)
    host.ideas.keeper.journal_digest(tech)
    _wait(host, tech)
    p = model.calls[0]["prompt"]
    assert "overruled (goal-9): I said no to the cache; my no was overruled." in p and "You said no" not in p and "never say *you*" in p


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


def test_a_goal_done_with_no_route_begins_its_partys_view(host, tech, model):
    slug = _done_goal(host, tech, "Cache", "The lobby is cached.", "Built.", [])
    ideas.set_meta(host.ideas.root(), slug, route="")
    assert host.ideas.views_when_done(slug) == 1
    _wait_all(host, tech)
    assert {c["key"] for c in model.steps("journal")} == {f"goal:{tech}"}


def test_no_view_is_begun_when_the_limit_or_the_window_is_spent_or_the_party_is_busy(host, tech, model):
    keeper = host.ideas.keeper
    keeper.budget_ok = lambda: False
    assert keeper.journal_view(tech, "done") is False and keeper.journal_view_for([tech, tech], "done") == 0
    keeper.budget_ok = lambda: True
    keeper.window_until = lambda: time.time() + 3600
    assert keeper.journal_view(tech, "done") is False
    keeper.window_until = lambda: None
    keeper.demo = True
    assert keeper.journal_view(tech, "ask") is False and keeper.journal_view("ghost", "ask") is False
    keeper.demo = False
    keeper._claim(f"goal:{tech}", "busy")
    assert keeper.journal_view(tech, "done") is False
    assert model.calls == []


def test_the_window_flag_of_a_done_goal_begins_the_views_first(host, tech, monkeypatch):
    seen = []
    monkeypatch.setattr(type(host.ideas), "views_when_done", lambda self, slug: seen.append(slug) or 0)
    host.ideas._flag_when_done("some-goal")
    assert seen == ["some-goal"]


# -- the view read, and a look now (spec 167 I) -----------------------------------------------------------------------------------------------

def test_the_view_is_read_with_its_date_and_what_it_read_and_its_opening_logs_no_word(host, tech, monkeypatch):
    logged = []
    monkeypatch.setattr(event_log, "record", lambda root, event, **f: logged.append((event, f)))
    host.ideas.host.demo = False
    assert host.ideas.view({"party": tech})["view"] == {} and host.ideas.view({"party": tech})["looking"] is False
    journals.save_digest(host.ideas.state_dir, tech, DIGEST_TEXT, "e1", read=["goal-0"], at="2026-11-08T10:00:00")
    got = host.ideas.view({"party": tech})
    assert got["view"] == {"text": DIGEST_TEXT, "at": "2026-11-08T10:00:00", "read": ["goal-0"]} and got["leader"]
    opened = [f for e, f in logged if e == "view_opened"]
    assert opened[-1]["party"] == tech and opened[-1]["at"] == "2026-11-08T10:00:00" and DIGEST_TEXT not in json.dumps(opened)
    with pytest.raises(Exception, match="No such party"):
        host.ideas.view({"party": "ghost"})


def test_a_look_now_begins_one_call_and_a_second_ask_while_it_runs_begins_none(host, tech, model):
    keeper = host.ideas.keeper
    keeper._claim(f"goal:{tech}", "busy")
    assert host.ideas.view_look({"party": tech}) == {"ok": True, "asked": False, "why": "The leader is looking already"}
    keeper._busy.pop(f"goal:{tech}", None)
    assert host.ideas.view_look({"party": tech}) == {"ok": True, "asked": True}
    assert host.ideas.view_look({"party": tech})["asked"] is False
    _wait(host, tech)
    assert {c["key"] for c in model.steps("journal")} == {f"goal:{tech}"}


def test_a_look_now_refused_says_why_in_plain_words(host, tech, model):
    host.ideas.keeper.budget_ok = lambda: False
    got = host.ideas.view_look({"party": tech})
    assert got["asked"] is False and "spend limit" in got["why"] and model.calls == []
