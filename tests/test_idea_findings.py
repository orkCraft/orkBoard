"""Spec 132 D.2, D.3, D.5 (docs/specs/132-four-levels-the-way-down-and-findings.md; decisions §234.3, §237.1–§237.2): a finding gathered where it is found (a goal reaching the discard, a lens's alarm), told by its
party's leader (step `finding`, one call a party) and sorted by the Orkmaster (step `finding_level`, one call a goal), a call that fails keeping code's words and `work`, the commands (*Fix it there* at each level,
*Not now*, *Fix all there*, *Another level…*) and the *Quality* page. The model call is stubbed (`keeper.call`), as `tests/test_idea_journal.py` does."""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

import pytest

from orkboard.core import idea_findings, idea_keeper
from orkboard.gui.ideas_args import IdeasError
from orkboard.gui.board_host import Orkboard
from orkboard.realm import event_log, findings, findings_gather, goal_main, goal_result, goal_team, idea_questions, idea_spend, idea_target, ideas, library, spec_sections

NOTHING_TOUCHED = {"parts": [], "screens": [], "files": 0}


@pytest.fixture
def host(fake_repo, monkeypatch) -> Orkboard:
    monkeypatch.setattr(goal_result, "touched", lambda *a, **k: dict(NOTHING_TOUCHED))
    h = Orkboard(fake_repo)
    assert isinstance(h.ideas.keeper, idea_findings.FindingsMixin) and idea_keeper.FindingsMixin is idea_findings.FindingsMixin
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


TOLD = {"findings": []}


class Model:
    """The keeper's call stubbed: every call is kept; `told` and `sorted` answer the two steps (a callable of the call, a dict, text or an Exception)."""

    def __init__(self, host, told=None, sorted_=None):
        self.host, self.calls, self.told, self.sorted = host, [], told, sorted_
        host.ideas.keeper.call = self

    def steps(self, step):
        return [c for c in self.calls if c["step"] == step]

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        step = k.measure()["step"]
        self.calls.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": step, "key": getattr(k._tls, "key", "")})
        answer = self.told if step == "finding" else self.sorted
        answer = answer(self.calls[-1]) if callable(answer) else answer
        if isinstance(answer, Exception):
            raise answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""


def _ids(call):
    return [ln.split()[2] for ln in call["prompt"].splitlines() if ln.startswith("- id f-")]


def tells(what="told"):
    """A leader that tells each finding it is asked about."""
    return lambda call: {"findings": [{"id": i, "what": f"{what} {i}", "shows": "the screen", "promised": "a winner first", "cause": "nobody sorted it"} for i in _ids(call)]}


def sorts(level="work", **by):
    return lambda call: {"levels": [{"id": i, "level": by.get(i, level), "change": f"change at {by.get(i, level)}"} for i in _ids(call)]}


def _done_goal(host, party, title="show the winner", merged=1, of=2):
    """A goal that is done: a section of `party` with a *Will be* line and a *Done when*, `merged` of `of` tasks landed."""
    root, st = host.ideas.root(), host.ideas.state_dir
    slug = ideas.add_idea(root, title, party, st)
    page = ideas.idea_page(root, slug)
    spec_sections.arrange(page, {}, [(ideas.track_page(root, party).title, spec_sections.join({"Will be": "- changed Results — plain list", "Done when": "- The winner shows"}))])
    ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
    tasks = []
    for n in range(of):
        t = idea_keeper._task(f"k{n}", f"Task {n}", f"Do {n}", "code", "warrior", [])
        t.update(state="merged" if n < merged else "ready", role="grunt")
        tasks.append(t)
    ideas._write_json(ideas.state_folder(st, slug) / "plan.json", {"idea": slug, "made_at": "2026-10-23T09:00:00", "passed_at": "2026-10-23T09:30:00", "passed_by": "person", "estimate": idea_keeper.estimate(tasks),
                                                                  "todos": [], "tasks": tasks})
    ideas.save_state(st, slug, state="done")
    return slug


def _found(host, slug, party, on="src/results", found="Not quite: changed src/results", source="verdict"):
    return findings.add(host.ideas.state_dir, {"source": source, "idea": slug, "party": party, "on": on, "found": found})


def _wait(host, key):
    for _ in range(1000):
        if not host.ideas.keeper.busy(key):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _events(host, name):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


# -- gathered where each thing is found ----------------------------------------------------------------------------------------------------------------

def test_a_goal_reaching_the_discard_with_a_difference_gathers_one_finding_a_line(host, tech):
    slug = _done_goal(host, tech, merged=1, of=2)
    assert findings_gather.verdict(host.ideas.state_dir, host.ideas.root(), Path(host.repo_root), slug) == 1
    got = findings.of_goal(host.ideas.state_dir, slug)
    assert len(got) == 1 and got[0]["source"] == "verdict" and got[0]["party"] == tech and got[0]["on"] == "Results"        # the part's id as the *Will be* line wrote it
    assert got[0]["status"] == "found" and "Results" in got[0]["found"] and got[0]["what"] == got[0]["found"]
    rec = findings.record(host.ideas.state_dir, slug)
    assert rec["verdict"] and rec["verdict"][0]["party"] == tech and rec["at"] and rec["status"] == "gathered"      # the verdict read once, kept with the time it reached the discard
    assert findings_gather.verdict(host.ideas.state_dir, host.ideas.root(), Path(host.repo_root), slug) == 0       # read again: kept once
    assert len(findings.of_goal(host.ideas.state_dir, slug)) == 1


def test_a_goal_that_did_all_it_promised_gathers_nothing_and_a_goal_not_done_is_not_read(host, tech):
    ok = _done_goal(host, tech, merged=2, of=2)
    assert findings_gather.verdict(host.ideas.state_dir, host.ideas.root(), Path(host.repo_root), ok) in (0, 1)       # a craft with a map to read may still say the part was not touched
    open_ = _done_goal(host, tech, "other goal", merged=0, of=2)
    ideas.save_state(host.ideas.state_dir, open_, state="working")
    assert findings_gather.verdict(host.ideas.state_dir, host.ideas.root(), Path(host.repo_root), open_) == 0
    assert findings.record(host.ideas.state_dir, open_)["at"] == ""


def test_the_gate_gathers_when_a_goal_goes_to_main_and_a_read_that_fails_never_fails_the_merge(host, tech, monkeypatch):
    slug = _done_goal(host, tech, merged=0, of=2)
    gui = host.ideas
    monkeypatch.setattr(gui, "_to_main_args", lambda a: (slug, {"root": gui.root(False), "into": "dev", "main": "main"}))
    monkeypatch.setattr(gui, "_checks_refusal", lambda s, w: "")
    monkeypatch.setattr(gui, "_flag_after_goal", lambda *a, **k: None)
    monkeypatch.setattr(goal_main, "merge", lambda *a, **k: {"goals": [slug], "commits": ["abc"], "files": 1, "pushed": False, "commit": "abc", "note": ""})
    assert gui.to_main({"idea": slug})["ok"] is True
    got = findings.of_goal(gui.state_dir, slug)
    assert len(got) == 1 and "Not done" in got[0]["found"]                                                   # nothing of it landed: a `missing` line
    monkeypatch.setattr(findings_gather, "verdict", lambda *a, **k: 1 / 0)
    assert gui.to_main({"idea": slug})["ok"] is True                                                         # a gathering that broke changes nothing for the merge


def test_a_lens_alarm_on_a_part_a_goal_touched_is_that_goals_and_elsewhere_it_is_no_goals(host, tech, monkeypatch):
    sd, repo = host.ideas.state_dir, Path(host.repo_root)
    slug = _done_goal(host, tech)
    findings.save_record(sd, slug, at=dt.datetime.now().isoformat(timespec="seconds"))                            # it reached the discard just now
    monkeypatch.setattr(goal_result, "touched", lambda *a, **k: {"parts": ["src/results"], "screens": [], "files": 2})
    concerns = [{"id": "c-1", "on": "src/results", "name": "Results", "level": "alert", "what": "Results is slow"},
                {"id": "c-2", "on": "src/other", "name": "Other", "level": "alert", "what": "Other leaks"},
                {"id": "c-3", "on": "src/results", "name": "Results", "level": "note", "what": "a note is no finding"},
                {"id": "c-4", "on": "src/results", "name": "Results", "level": "alert", "what": "already a goal", "idea": "some-goal"}]
    assert findings_gather.lens(sd, repo, tech, "tech", concerns) == 2
    mine = findings.of_goal(sd, slug)
    assert [(f["source"], f["on"], f["party"]) for f in mine] == [("lens", "c-1", tech)] and "Results is slow" in mine[0]["found"]
    loose = findings.of_goal(sd, "")
    assert [(f["source"], f["on"], f["idea"]) for f in loose] == [("concern", "c-2", "")]
    assert findings_gather.lens(sd, repo, tech, "tech", concerns) == 0                                            # the same look again adds nothing


def test_a_goal_that_reached_the_discard_long_ago_owns_no_alarm(host, tech, monkeypatch):
    sd, repo = host.ideas.state_dir, Path(host.repo_root)
    slug = _done_goal(host, tech)
    findings.save_record(sd, slug, at=(dt.datetime.now() - dt.timedelta(days=findings_gather.LENS_DAYS + 1)).isoformat(timespec="seconds"))
    monkeypatch.setattr(goal_result, "touched", lambda *a, **k: {"parts": ["src/results"], "screens": [], "files": 2})
    findings_gather.lens(sd, repo, tech, "tech", [{"id": "c-1", "on": "src/results", "name": "Results", "level": "alert", "what": "slow"}])
    assert findings.of_goal(sd, slug) == [] and [f["source"] for f in findings.of_goal(sd, "")] == ["concern"]


def test_a_design_alarm_is_matched_to_the_screens_a_goal_changed(host, design, monkeypatch):
    sd, repo = host.ideas.state_dir, Path(host.repo_root)
    slug = _done_goal(host, design)
    findings.save_record(sd, slug, at=dt.datetime.now().isoformat(timespec="seconds"))
    monkeypatch.setattr(goal_result, "touched", lambda *a, **k: {"parts": [], "screens": [{"screen": "results", "name": "Results", "path": "ui/results.tsx"}], "files": 1})
    findings_gather.lens(sd, repo, design, "design", [{"id": "c-1", "on": "results", "name": "Results", "level": "alert", "what": "contrast is low"}])
    assert [f["source"] for f in findings.of_goal(sd, slug)] == ["lens"]
    assert findings_gather.touched_by(None, "tech", "x") is False and findings_gather.touched_by({"parts": ["a"], "screens": []}, "art", "a") is False       # a craft with no map read from files is never touched


# -- told by the leader, sorted by the Orkmaster -----------------------------------------------------------------------------------------------------------

def test_the_told_call_is_one_a_party_and_the_sorted_one_a_goal(host, tech, design):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    a, b = _found(host, slug, tech, on="a"), _found(host, slug, tech, on="b")
    c = _found(host, slug, design, on="c", source="lens")
    model = Model(host, told=tells(), sorted_=sorts("work", **{c["id"]: "spec", a["id"]: "decision"}))
    host.ideas.keeper.findings_run(slug)
    assert len(model.steps("finding")) == 2 and len(model.steps("finding_level")) == 1                               # a call a party, a call a goal
    keys = sorted(c["key"] for c in model.steps("finding"))
    assert keys == sorted([f"goal:{tech}", f"goal:{design}"])                                                      # each its party's own step: its leader, its tool, its ledger
    assert all(c["tools"] for c in model.steps("finding")) and model.steps("finding_level")[0]["tools"] is False       # the leader reads, the Orkmaster does not
    assert sorted(len(_ids(c)) for c in model.steps("finding")) == [1, 2]
    told = model.steps("finding")[0]["prompt"]
    assert "What your section promised" in told and "The winner shows" in told and "Results" in told        # the party's section, its Will be and Done when
    assert "Read at most 4 files" in model.steps("finding")[0]["prompt"] and "Read no file" in model.steps("finding_level")[0]["prompt"]
    got = {f["id"]: f for f in findings.of_goal(sd, slug)}
    assert {f["status"] for f in got.values()} == {"sorted"}
    assert got[a["id"]]["level"] == "decision" and got[b["id"]]["level"] == "work" and got[c["id"]]["level"] == "spec"
    assert got[a["id"]]["what"] == f"told {a['id']}" and got[a["id"]]["cause"] == "nobody sorted it" and got[a["id"]]["change"] == "change at decision"
    sorted_prompt = model.steps("finding_level")[0]["prompt"]
    assert all(i in sorted_prompt for i in got) and "nobody sorted it" in sorted_prompt                                # the Orkmaster is given every finding as told


def test_the_events_count_and_say_no_word_of_a_finding(host, tech):
    slug = _done_goal(host, tech)
    a = _found(host, slug, tech, on="a", found="a secret thing that must stay out of the log")
    _found(host, slug, tech, on="b")
    Model(host, told=tells(), sorted_=sorts("work", **{a["id"]: "spec"}))
    host.ideas.keeper.findings_run(slug)
    told, sorted_ = _events(host, event_log.FINDINGS_TOLD), _events(host, event_log.FINDINGS_SORTED)
    assert len(told) == 1 and told[0]["idea"] == slug and told[0]["party"] == tech and told[0]["findings"] == 2 and told[0]["failed"] is False and "seconds" in told[0] and told[0]["cost"] == pytest.approx(0.01)
    assert len(sorted_) == 1 and sorted_[0]["findings"] == 2 and sorted_[0]["levels"] == {"work": 1, "spec": 1, "decision": 0} and sorted_[0]["failed"] is False
    assert "secret" not in json.dumps(told + sorted_) and event_log.FINDINGS_TOLD in event_log.EVENTS and event_log.FINDINGS_SORTED in event_log.EVENTS


def test_both_steps_are_in_the_target_and_cost_the_goals_ledger(host, tech):
    for step in ("finding", "finding_level"):
        assert step in idea_target.STEPS and step in idea_target.MATRIX and idea_target.CONTEXT[step] == 9000 and step in idea_target.CAPS and idea_spend.STEP_STAGE[step] == "spec"
    assert idea_target.READS["finding"] == 4 and idea_target.READS["finding_level"] == 0
    for target in idea_target.TARGETS:
        assert idea_target.pick("finding", target) is not None and idea_target.pick("finding_level", target)[0] in ("laborer", "warrior")
    slug = _done_goal(host, tech)
    _found(host, slug, tech)
    Model(host, told=tells(), sorted_=sorts())
    host.ideas.keeper.findings_run(slug)
    steps = [r.get("step") for r in idea_spend.read(idea_spend.ledger(host.ideas.state_dir, slug, "")) ] + [r.get("step") for r in idea_spend.read(idea_spend.ledger(host.ideas.state_dir, "", tech))]
    assert "finding" in steps and "finding_level" in steps


def test_a_call_that_fails_keeps_codes_words_and_work_and_never_stops_the_card(host, tech):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    a = _found(host, slug, tech, on="a", found="Not quite: changed a")
    model = Model(host, told=RuntimeError("the tool is out"), sorted_="not json at all")
    host.ideas.keeper.findings_run(slug)
    got = findings.get(sd, a["id"])
    assert got["what"] == "Not quite: changed a" and got["cause"] == "" and got["level"] == "work" and got["status"] == "sorted"       # the card still comes
    assert len(model.steps("finding")) == 2 and len(model.steps("finding_level")) == 2                                 # each tried once more
    assert _events(host, event_log.FINDINGS_TOLD)[0]["failed"] is True and _events(host, event_log.FINDINGS_SORTED)[0]["failed"] is True
    assert [r["kind"] for r in findings.rows(sd, host.ideas.root())] == ["quality"]


def test_a_finding_the_orkmaster_left_out_is_work(host, tech):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    a, b = _found(host, slug, tech, on="a"), _found(host, slug, tech, on="b")
    Model(host, told=tells(), sorted_=lambda call: {"levels": [{"id": a["id"], "level": "decision", "change": "word it again"}]})
    host.ideas.keeper.findings_run(slug)
    assert findings.get(sd, a["id"])["level"] == "decision" and findings.get(sd, b["id"])["level"] == "work" and findings.get(sd, b["id"])["status"] == "sorted"


def test_a_stop_leaves_the_findings_as_they_were(host, tech):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    a = _found(host, slug, tech)
    Model(host, told=InterruptedError("stopped"), sorted_=sorts())
    host.ideas.keeper.findings_run(slug)
    assert findings.get(sd, a["id"])["status"] == "found"                                                          # the next tick tells it again


def test_a_finding_of_no_party_keeps_codes_words_without_a_call_to_a_leader(host, tech):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    h = findings.add(sd, {"source": "hypothesis", "idea": slug, "party": "", "on": "H4", "found": "H4 was refuted: nobody opened the drawer"})
    model = Model(host, told=tells(), sorted_=sorts("spec"))
    host.ideas.keeper.findings_run(slug)
    assert model.steps("finding") == [] and findings.get(sd, h["id"])["what"].startswith("H4 was refuted") and findings.get(sd, h["id"])["level"] == "spec"


def test_findings_of_no_goal_are_told_and_sorted_too(host, tech):
    sd = host.ideas.state_dir
    f = findings.add(sd, {"source": "concern", "idea": "", "party": tech, "on": "c-1", "found": "Results: it leaks"})
    model = Model(host, told=tells(), sorted_=sorts("work"))
    host.ideas.keeper.findings_run("")
    assert len(model.steps("finding")) == 1 and len(model.steps("finding_level")) == 1
    assert findings.get(sd, f["id"])["status"] == "sorted" and [r["kind"] for r in findings.rows(sd, host.ideas.root())] == ["finding"]


# -- on the clock's tick ----------------------------------------------------------------------------------------------------------------------------------

def test_the_clock_begins_a_goals_run_only_when_its_findings_are_in(host, tech):
    sd, keeper = host.ideas.state_dir, host.ideas.keeper
    slug = _done_goal(host, tech)
    a = _found(host, slug, tech)
    model = Model(host, told=tells(), sorted_=sorts())
    findings.save_record(sd, slug, at=dt.datetime.now().isoformat(timespec="seconds"))
    assert keeper.findings_due() == 0 and model.calls == []                                                      # the lens has not looked, a day has not passed
    keeper.__dict__["_findings_at"] = float("-inf")
    findings.save_record(sd, slug, at=(dt.datetime.now() - dt.timedelta(hours=findings.QUIET_H + 1)).isoformat(timespec="seconds"))
    assert keeper.findings_due() == 1
    _wait(host, f"quality:{slug}")
    assert findings.get(sd, a["id"])["status"] == "sorted"
    keeper.__dict__["_findings_at"] = float("-inf")
    assert keeper.findings_due() == 0                                                                            # nothing left to tell
    assert not keeper.findings_begin(slug)


def test_a_demo_or_a_spent_cap_begins_nothing(host, tech):
    slug = _done_goal(host, tech)
    _found(host, slug, tech)
    findings.save_record(host.ideas.state_dir, slug, at=(dt.datetime.now() - dt.timedelta(days=2)).isoformat(timespec="seconds"))
    model = Model(host, told=tells(), sorted_=sorts())
    host.ideas.keeper.demo = True
    assert host.ideas.keeper.findings_due() == 0 and model.calls == []


# -- the commands -----------------------------------------------------------------------------------------------------------------------------------------------

def _sorted_finding(host, slug, party, level, on="src/results", change=""):
    f = _found(host, slug, party, on=on)
    findings.told(host.ideas.state_dir, slug, f["id"], {"what": "The list is plain", "shows": "the screen shows no order", "promised": "a winner first", "cause": "no one sorted it"})
    return findings.sorted_(host.ideas.state_dir, slug, f["id"], level, change)


def _cmd(host, name, **args):
    return host.ideas.commands()[name](args)


@pytest.fixture
def started(host, monkeypatch):
    """The keeper's sections stubbed: the goals the fix goals would start."""
    calls = []
    monkeypatch.setattr(host.ideas.keeper, "sections", lambda slug: calls.append(slug), raising=False)
    return calls


def test_fix_it_there_at_work_makes_a_bug_fix_goal_whose_diagnosis_is_the_finding(host, tech, started):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    f = _sorted_finding(host, slug, tech, "work", change="sort the list")
    got = _cmd(host, "ideas.finding_fix", id=f["id"])
    fix = got["fix"]["idea"]
    assert got["ok"] and got["level"] == "work"
    page = ideas.idea_page(host.ideas.root(), fix)
    assert page.title.startswith("Fix: The list is plain") and page.get("fixes") == slug and page.get("track") == tech          # marked as the fix of the goal it was found in
    assert "no one sorted it" in page.section("Gist") and "the screen shows no order" in page.section("Gist")
    st = ideas.state(sd, fix)
    assert st["state"] == "sections" and [r["party"] for r in st["route"]] == [tech] and st["route_how"]["kind"] == "bug" and st["route_how"]["short"] and st["queue"] == ""
    cause = idea_questions.record(sd, fix)["cause"]
    assert cause["text"] == "no one sorted it" and cause["confirmed"] is True and cause["pending"] is False         # no `diagnose` call: the finding is the diagnosis
    assert started == [fix]                                                                                        # its sections begun, the leader's Why the cause
    again = findings.get(sd, f["id"])
    assert again["status"] == "answered" and again["answer"] == "fix" and again["fix"] == {"idea": fix}
    assert findings.rows(sd, host.ideas.root()) == []
    with pytest.raises(IdeasError, match="answered already"):
        _cmd(host, "ideas.finding_fix", id=f["id"])


def test_fix_it_there_at_spec_writes_the_finders_section_again_before_its_plan(host, tech, started):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    f = _sorted_finding(host, slug, tech, "spec")
    fix = _cmd(host, "ideas.finding_fix", id=f["id"])["fix"]["idea"]
    st = ideas.state(sd, fix)
    assert st["state"] == "sections" and [r["party"] for r in st["route"]] == [tech] and started == [fix]            # the section is written first; the plan follows it as it always does
    cause = idea_questions.record(sd, fix)["cause"]["text"]
    assert "The spec said the wrong thing" in cause and "no one sorted it" in cause and "Write your section again" in cause
    assert ideas.idea_page(host.ideas.root(), fix).get("fixes") == slug


def test_fix_it_there_at_the_decision_is_a_proposal_into_the_cascade_or_a_refusal_in_words(host, tech):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    spec_sections.save_record(sd, slug, {"decision": {"title": "D", "text": "t", "number": 240, "confirmed": True, "changes": []}})
    f = _sorted_finding(host, slug, tech, "decision", change="word the order again")
    if hasattr(host.ideas.keeper, "cascade_propose"):                              # spec 131 B is built: this test fakes it as it is told to be
        del host.ideas.keeper.__class__.cascade_propose
    with pytest.raises(IdeasError, match="The decision's change comes with the cascade"):
        _cmd(host, "ideas.finding_fix", id=f["id"])
    assert findings.get(sd, f["id"])["status"] == "sorted"                         # nothing was answered
    seen = []
    host.ideas.keeper.cascade_propose = lambda party, slice_id, says, why, points, from_step="", idea="": (seen.append((party, slice_id, says, why, points, from_step, idea)) or "cas-1")
    got = _cmd(host, "ideas.finding_fix", id=f["id"])
    assert got["level"] == "decision" and got["fix"] == {"cascade": "cas-1"}
    assert seen == [(tech, "", "word the order again", "no one sorted it", ["240"], "finding", slug)]
    assert findings.get(sd, f["id"])["fix"] == {"cascade": "cas-1"} and findings.get(sd, f["id"])["answer"] == "fix"


def test_not_now_keeps_the_finding_on_the_record_and_out_of_the_hand(host, tech):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    f = _sorted_finding(host, slug, tech, "work")
    assert [r["kind"] for r in host.ideas.board()["needs_you"] if r["kind"] == "quality"] == ["quality"]
    assert _cmd(host, "ideas.finding_later", id=f["id"]) == {"ok": True}
    assert [r for r in host.ideas.board()["needs_you"] if r["kind"] == "quality"] == []
    got = _cmd(host, "ideas.quality", idea=slug)
    assert [x["id"] for x in got["findings"]] == [f["id"]] and got["findings"][0]["answer"] == "later"          # the record keeps it, taken again with no new call
    assert "quality" not in host.ideas.board()["ideas"][0]["levels"] and findings.get(sd, f["id"])["status"] == "answered"
    with pytest.raises(IdeasError):
        _cmd(host, "ideas.finding_later", id="f-nothing")


def test_fix_all_there_answers_each_finding_of_the_card_and_says_what_it_could_not(host, tech, started):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    a = _sorted_finding(host, slug, tech, "work", on="a")
    b = _sorted_finding(host, slug, tech, "spec", on="b")
    c = _sorted_finding(host, slug, tech, "decision", on="c")
    card = next(r for r in host.ideas.board()["needs_you"] if r["kind"] == "quality")
    assert [f["level"] for f in card["findings"]] == ["decision", "spec", "work"] and card["pulls"]["estimate"]["usd_high"] > 0       # its cost is on the card before
    if hasattr(host.ideas.keeper, "cascade_propose"):
        del host.ideas.keeper.__class__.cascade_propose
    got = _cmd(host, "ideas.finding_fix_all", idea=slug)
    assert [x["level"] for x in got["fixed"]] == ["spec", "work"] and [x["id"] for x in got["refused"]] == [c["id"]] and "cascade" in got["refused"][0]["why"]
    assert findings.get(sd, a["id"])["answer"] == "fix" and findings.get(sd, b["id"])["answer"] == "fix" and findings.get(sd, c["id"])["status"] == "sorted"
    assert len(started) == 2
    with pytest.raises(IdeasError, match="cascade"):
        _cmd(host, "ideas.finding_fix_all", idea=slug)                       # nothing could be fixed: said in words
    findings.answer(sd, c["id"], "later")
    with pytest.raises(IdeasError, match="No finding waits"):
        _cmd(host, "ideas.finding_fix_all", idea=slug)


def test_another_level_moves_the_finding_and_says_its_pulls_again(host, tech):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech)
    f = _sorted_finding(host, slug, tech, "work")
    got = _cmd(host, "ideas.finding_move", id=f["id"], level="spec")
    assert got["ok"] and got["level"] == "spec" and got["pulls"]["level"] == "spec" and got["pulls"]["sections"]
    assert findings.get(sd, f["id"])["level"] == "spec" and findings.get(sd, f["id"])["answer"] == "moved" and findings.get(sd, f["id"])["status"] == "sorted"
    assert next(r for r in host.ideas.board()["needs_you"] if r["kind"] == "quality")["findings"][0]["level"] == "spec"
    with pytest.raises(IdeasError, match="decision, spec or work"):
        _cmd(host, "ideas.finding_move", id=f["id"], level="heaven")


def test_the_quality_page_is_the_record_of_the_goal_and_of_no_goal(host, tech):
    sd = host.ideas.state_dir
    slug = _done_goal(host, tech, merged=1, of=2)
    findings_gather.verdict(sd, host.ideas.root(), Path(host.repo_root), slug)
    f = findings.of_goal(sd, slug)[0]
    findings.sorted_(sd, slug, f["id"], "spec", "say it")
    findings.add(sd, {"source": "lens", "idea": slug, "party": tech, "on": "c-1", "found": "Results is slow"})
    got = _cmd(host, "ideas.quality", idea=slug)
    assert got["idea"] == slug and got["title"] == "show the winner" and got["state"] == "done" and got["at"] and got["verdict"] and got["checks"] == [] and got["hypothesis"] is None
    assert got["result"] is not None and got["result"]["parties"]                                                    # the verdict against the spec as the Done page gave it
    assert [x["source"] for x in got["lenses"]] == ["lens"] and [x["level"] for x in got["findings"]] == ["spec", ""]
    assert all("pulls" in x for x in got["findings"])
    loose = _cmd(host, "ideas.quality", idea="")
    assert loose["idea"] == "" and loose["findings"] == []
    with pytest.raises(IdeasError, match="gone"):
        _cmd(host, "ideas.quality", idea="no-such-goal")


def test_the_hands_rows_lie_after_the_urgent_ones_and_push_nothing(host, tech):
    from orkboard.gui.ideas_board import sort_needs
    from orkboard.gui import phone_journal
    slug = _done_goal(host, tech)
    _sorted_finding(host, slug, tech, "work")
    loose = findings.add(host.ideas.state_dir, {"source": "concern", "idea": "", "party": tech, "on": "c-1", "found": "Results leaks"})
    findings.told(host.ideas.state_dir, "", loose["id"], {})
    findings.sorted_(host.ideas.state_dir, "", loose["id"], "work")
    snap = host.ideas.snapshot()
    assert snap["needs_you"] == 0                                                                                    # no count of what waits (CLAUDE.md's frame)
    board = host.ideas.board()["needs_you"]
    assert {r["kind"] for r in board} == {"quality", "finding"} and all(r["blocks"] is False for r in board)
    mixed = sort_needs([{"kind": "quality", "blocks": False, "at": "1"}, {"kind": "failed", "blocks": True, "at": "9"}, {"kind": "asks", "blocks": False, "at": "5"}, {"kind": "finding", "blocks": False, "at": "2"}])
    assert [r["kind"] for r in mixed] == ["failed", "asks", "quality", "finding"]
    assert "quality" in phone_journal.NOT_A_CARD and "finding" in phone_journal.NOT_A_CARD
