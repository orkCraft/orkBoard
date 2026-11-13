"""Spec 116 C (docs/specs/116-hypotheses-on-products-tree.md §4; decisions §194): the hypotheses of Product's map on the host. `ideas.hypotheses` (each with its state as shown and its goals' title,
element and place), `ideas.hypothesis_set` (the person's, open at once), `_keep`, `_drop`, `_attach` (a goal that rests on it, a goal that tests it), `_evidence`, `_judge` (held and refuted write a
numbered decision with no goal and the row *Did it hold?* leaves; unsure keeps it open) and `ideas.hypotheses_propose` (the keeper's, called only where it is). Refusals in plain words. The keeper's
proposal (Part B) is stubbed."""
from __future__ import annotations

import subprocess
import sys

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import decisions_log, hypotheses, ideas, opportunity_tree as tree

COMMANDS = {"ideas.hypotheses", "ideas.hypothesis_set", "ideas.hypothesis_keep", "ideas.hypothesis_drop", "ideas.hypothesis_attach", "ideas.hypothesis_evidence", "ideas.hypothesis_judge",
            "ideas.hypotheses_propose"}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    (h.ideas.state_dir / "project.json").write_text('{"decisions": "docs/decisions.md"}', encoding="utf-8")        # this project keeps its decisions as one file (a project with no log gets a MADR folder: spec 127 B.4)
    h.ideas.root()                                                    # the Board's tree stands: a decision is committed to dev
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def make_goal(host, title, state="", element=""):
    slug = ideas.add_idea(host.ideas.root(), title, "general", host.ideas.state_dir)
    changes = {**({"state": state} if state else {}), **({"element": element} if element else {})}
    if changes:
        ideas.save_state(host.ideas.state_dir, slug, **changes)
    return slug


def hold(host, text="People want a sketch first", signal="most ask for one within a minute", **more):
    return host.command("ideas.hypothesis_set", {"text": text, "signal": signal, **more})["item"]


def with_test(host, state="done", **more):
    """An open hypothesis with one test goal in `state`."""
    item = hold(host, **more)
    goal = make_goal(host, "Interview five founders", state=state, element="ice")
    host.command("ideas.hypothesis_attach", {"id": item["id"], "test": goal})
    return item["id"], goal


def hand(host):
    return [n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "hypothesis"]


def refused(host, command, args, match):
    with pytest.raises(CommandError, match=match):
        host.command(command, args)


# -- read and keep ----------------------------------------------------------------------------------------------------------------------------

def test_the_person_s_hypothesis_is_open_at_once_and_its_words_change_with_its_id_staying(host):
    got = host.command("ideas.hypothesis_set", {"text": " People  want a sketch first ", "signal": "most ask for one", "axis": "desirable"})
    item = got["item"]
    assert got["ok"] is True and item["id"] == "people-want-a-sketch-first" and item["state"] == "open" and item["by"] == "person" and item["axis"] == "desirable" and item["tests"] == [] and item["rests"] == []
    again = host.command("ideas.hypothesis_set", {"id": item["id"], "text": "People want a sketch before anything"})["item"]
    assert again["id"] == item["id"] and again["text"] == "People want a sketch before anything" and again["signal"] == "most ask for one"
    assert host.command("ideas.hypotheses", {})["items"] == [again]


def test_a_hypothesis_on_a_job_names_a_job_of_the_tree(host):
    tree.keep(host.ideas.state_dir, [{"text": "Cut the time to a first sketch"}], [{"when": "I start", "want": "see a sketch", "so": "judge it", "segment": "founders"},
                                                                                     {"when": "I finish", "want": "share it", "so": "show it", "segment": "founders"},
                                                                                     {"when": "I doubt", "want": "compare two", "so": "choose", "segment": "founders"}], "person")
    job = tree.read(host.ideas.state_dir)["jobs"][0]["id"]
    assert hold(host, on=job)["on"] == job
    refused(host, "ideas.hypothesis_set", {"text": "Another", "signal": "s", "on": "no-such-job"}, "That job is gone")


def test_a_proposed_hypothesis_is_kept_or_dropped(host):
    proposed = hypotheses.add(host.ideas.state_dir, "Founders pay for it", "ten say so", by="leader", party="product")
    assert host.command("ideas.hypotheses", {})["items"][0]["state"] == "proposed"
    got = host.command("ideas.hypothesis_keep", {"id": proposed["id"]})
    assert got["ok"] is True and got["item"]["state"] == "open"
    other = hypotheses.add(host.ideas.state_dir, "Teams want sharing", "they ask", by="leader", party="product")
    assert host.command("ideas.hypothesis_drop", {"id": other["id"]}) == {"ok": True}
    assert [i["id"] for i in host.command("ideas.hypotheses", {})["items"]] == [proposed["id"]]


# -- the goals: rests on, tests, and the state as shown ---------------------------------------------------------------------------------------

def test_a_goal_rests_on_a_hypothesis_and_a_test_tests_it_each_with_its_title_element_and_place(host):
    item = hold(host)
    rests = make_goal(host, "Dark mode", state="working", element="lava")
    test = make_goal(host, "Interview five founders", element="ice")
    host.command("ideas.hypothesis_attach", {"id": item["id"], "goal": rests})
    got = host.command("ideas.hypothesis_attach", {"id": item["id"], "test": test})["item"]
    assert got["rests"] == [{"slug": rests, "title": "Dark mode", "element": "lava", "hue": "lava", "place": "work"}]
    assert got["tests"] == [{"slug": test, "title": "Interview five founders", "element": "ice", "hue": "ice", "place": "line"}]
    assert got["state"] == "testing"                                                                  # a test is in line: shown as testing, kept as open
    assert hypotheses.read(host.ideas.state_dir)["items"][0]["state"] == "open"
    ideas.save_state(host.ideas.state_dir, test, state="done")
    assert host.command("ideas.hypotheses", {})["items"][0]["state"] == "open"


# -- judged ------------------------------------------------------------------------------------------------------------------------------------

def test_the_row_comes_when_the_last_test_is_done_and_judging_it_held_writes_the_next_numbered_decision_and_the_row_leaves(host):
    host.ideas.keeper.write_decision("An earlier decision", "Why: before.", host.ideas._decision_tree())
    item_id, goal = with_test(host, state="working")
    host.command("ideas.hypothesis_evidence", {"id": item_id, "text": "Four of five asked for it", "ref": goal})
    assert hand(host) == []
    ideas.save_state(host.ideas.state_dir, goal, state="done")
    (row,) = hand(host)
    assert row["id"] == item_id and row["tests"] == [{"slug": goal, "title": "Interview five founders"}] and row["blocks"] is False
    got = host.command("ideas.hypothesis_judge", {"id": item_id, "state": "held", "why": "Clear enough to build on"})
    assert got["ok"] is True and got["decision"]["number"] == 2 and got["decision"]["commit"] and got["item"]["state"] == "held"
    assert got["item"]["verdict"]["decision"] == 2 and got["item"]["verdict"]["why"] == "Clear enough to build on"
    assert hand(host) == []
    log = git(host.repo_root, "show", "dev:docs/decisions.md")
    assert decisions_log.headings(log)[-1].split(" (")[0] == "2. Hypothesis held: People want a sketch first"
    entry = log[log.index("## 2. "):]
    assert "the person and Orkboard)" in entry.splitlines()[0]
    assert "Signal: most ask for one within a minute" in entry and "- Four of five asked for it (" + goal + ")" in entry
    assert "Tests: Interview five founders" in entry and "Why: Clear enough to build on" in entry
    assert git(host.repo_root, "log", "-1", "--format=%s", "dev") == "board: decision 2 — Hypothesis held: People want a sketch first"


def test_not_sure_yet_keeps_it_open_with_the_why_as_evidence_and_writes_nothing(host):
    item_id, goal = with_test(host)
    got = host.command("ideas.hypothesis_judge", {"id": item_id, "state": "unsure", "why": "Only two of five answered"})
    assert got["ok"] is True and "decision" not in got and got["item"]["state"] == "open" and got["item"]["verdict"] == {}
    assert [e["text"] for e in got["item"]["evidence"]] == ["Only two of five answered"]
    assert not decisions_log.path(host.repo_root).exists() and "decisions.md" not in git(host.repo_root, "ls-tree", "-r", "--name-only", "dev")
    assert len(hand(host)) == 1                                                                       # it is still due: the answer was not final


# -- refusals ----------------------------------------------------------------------------------------------------------------------------------

def test_refusals_are_in_plain_words(host):
    refused(host, "ideas.hypothesis_set", {"text": "", "signal": "s"}, "says what we believe")
    refused(host, "ideas.hypothesis_set", {"text": "t", "signal": ""}, "what we'll know when")
    refused(host, "ideas.hypothesis_set", {"text": "t", "signal": "s", "axis": "loud"}, "what people want")
    refused(host, "ideas.hypothesis_set", {"id": "nobody", "text": "t"}, "That hypothesis is gone")
    refused(host, "ideas.hypothesis_keep", {"id": "nobody"}, "That hypothesis is gone")
    refused(host, "ideas.hypothesis_drop", {"id": "nobody"}, "That hypothesis is gone")
    refused(host, "ideas.hypothesis_evidence", {"id": "nobody", "text": "x"}, "That hypothesis is gone")
    item = hold(host)
    refused(host, "ideas.hypothesis_evidence", {"id": item["id"], "text": " "}, "Evidence is a line")
    refused(host, "ideas.hypothesis_attach", {"id": item["id"]}, "Say which goal")
    refused(host, "ideas.hypothesis_attach", {"id": item["id"], "test": "no-such-goal"}, "That goal is gone")
    refused(host, "ideas.hypothesis_attach", {"id": "nobody", "goal": make_goal(host, "A goal")}, "That hypothesis is gone")
    refused(host, "ideas.hypothesis_set", {"text": 3, "signal": "s"}, "text is not text")


# -- the leaders' proposal ----------------------------------------------------------------------------------------------------------------------

# -- a goal sent with a hypothesis as a mark (spec 116 E) ------------------------------------------------------------------------------------------

def product_party(host, team=("experimenter",), leader="product-manager"):
    """A party with its leader and team, as Edit the party keeps them (no model): the experiment is one of its goal types."""
    from orkboard.realm import goal_team, library

    root, state = host.ideas.root(), host.ideas.state_dir
    slug, _new = ideas.save_goal(root, None, "Product", "About Product", None, "normal")
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    goal_team.set_team(root, slug, list(team), leader=leader)
    host.ideas.keeper.draft = lambda *a, **k: None                       # the draft is a model's
    return slug


def mark(item, name=""):
    return {"map": "product", "id": f"hyp:{item['id']}", "name": name or item["text"]}


def kept(host, id):
    return next(i for i in hypotheses.read(host.ideas.state_dir)["items"] if i["id"] == id)


def test_an_experiment_sent_with_a_hypothesis_marked_becomes_its_test(host):
    party = product_party(host)
    item = hold(host)
    got = host.command("ideas.add", {"text": "Show the big code to half of the hosts", "track": party, "type": "experiment", "marks": [mark(item)]})
    assert got["type"] == "experiment" and kept(host, item["id"])["tests"] == [got["slug"]] and kept(host, item["id"])["rests"] == []
    assert ideas.state(host.ideas.state_dir, got["slug"])["marks"] == [{"map": "product", "name": item["text"], "id": f"hyp:{item['id']}"}], "the mark stays the goal's, as any picked part's"
    assert host.command("ideas.hypotheses", {})["items"][0]["tests"][0]["slug"] == got["slug"]


def test_the_goal_that_tests_a_hypothesis_asks_did_it_hold_once_it_is_done(host):
    """The two halves: *Test it* attaches the new goal; when it is done the hand's row comes (spec 116 C)."""
    party = product_party(host)
    item = hold(host)
    got = host.command("ideas.add", {"text": "Show the big code to half of the hosts", "track": party, "type": "experiment", "marks": [mark(item)]})
    assert hand(host) == []
    ideas.save_state(host.ideas.state_dir, got["slug"], state="done")
    assert [r["id"] for r in hand(host)] == [item["id"]]

# -- spec 133 A: the ways it is refuted and the draft of the decision ----------------------------------------------------------------------

WAYS = [{"name": "the hook", "when": "opens rise, goals do not", "change": "Do not build the push."}, {"name": "the noise", "when": "one in five turns it off"}]


def test_a_hypothesis_is_set_with_its_ways_and_its_draft_and_a_bad_list_is_refused(host):
    item = hold(host, refuted=WAYS, if_holds="Make it a setting.")
    assert [w["name"] for w in item["refuted"]] == ["the hook", "the noise"] and item["if_holds"] == "Make it a setting."
    got = host.command("ideas.hypothesis_set", {"id": item["id"], "refuted": [WAYS[1]], "if_holds": ""})["item"]
    assert [w["name"] for w in got["refuted"]] == ["the noise"] and got["if_holds"] == "" and got["signal"] == item["signal"]
    refused(host, "ideas.hypothesis_set", {"id": item["id"], "refuted": "no"}, "not a list of ways")
    refused(host, "ideas.hypothesis_set", {"id": item["id"], "refuted": [{"name": "x"}]}, "says when")
    assert host.command("ideas.hypotheses")["items"][0]["refuted"] == got["refuted"]


def test_the_verdict_writes_the_draft_as_the_decision_with_the_way_it_was_refuted(host):
    item_id, _goal = with_test(host, refuted=WAYS, if_holds="Make it a setting.")
    refused(host, "ideas.hypothesis_judge", {"id": item_id, "state": "refuted", "way": "the cold"}, "Pick the way it is refuted")
    assert hypotheses.read(host.ideas.state_dir)["items"][0]["state"] == "open"
    got = host.command("ideas.hypothesis_judge", {"id": item_id, "state": "refuted", "way": "the hook", "why": "Only opens rose"})
    assert got["way"] == "the hook" and got["item"]["verdict"]["way"] == "the hook"
    log = git(host.repo_root, "show", "dev:docs/decisions.md")
    body = log[log.rindex("## 1. "):].split("\n", 1)[1].strip()
    assert body.startswith("Do not build the push.") and "Refuted: the hook — opens rise, goals do not" in body and body.index("Do not build") < body.index("Refuted:") < body.index("Signal:")


def test_a_held_verdict_writes_the_saved_draft_or_the_persons_own_words_over_it(host):
    a, _ = with_test(host, text="Alpha holds", if_holds="Saved draft.")
    host.command("ideas.hypothesis_judge", {"id": a, "state": "held"})
    b, _ = with_test(host, text="Beta holds", if_holds="Saved draft.")
    host.command("ideas.hypothesis_judge", {"id": b, "state": "held", "draft": "My own words."})
    log = git(host.repo_root, "show", "dev:docs/decisions.md")
    first, second = log[log.index("## 1. "):log.index("## 2. ")], log[log.index("## 2. "):]
    assert "Saved draft." in first and "Saved draft." not in second and "My own words." in second and "Signal:" in second


# -- spec 133 C: the project's own hypotheses file, written and committed with the Board's pages ---------------------------------------------

OWN_FILE = """# Hypotheses

## H1. People want a sketch first

**Status:** open. **Raised:** the owner.

### What would prove it, what would refute it

- **Holds** when most ask for one within a minute
- **Refuted, the hook**: they look and do not pick

### If it holds

Sketch first, always.
"""


@pytest.fixture
def fhost(fake_repo) -> Orkboard:
    (fake_repo / "docs" / "hypotheses.md").write_text(OWN_FILE, encoding="utf-8")
    git(fake_repo, "add", "docs/hypotheses.md")
    git(fake_repo, "commit", "-q", "-m", "A hypotheses file")
    h = Orkboard(fake_repo)
    (h.ideas.state_dir / "project.json").write_text('{"decisions": "docs/decisions.md"}', encoding="utf-8")
    h.ideas.root()
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def test_the_project_s_file_is_read_in_and_a_hypothesis_added_is_committed_in_it_with_the_boards_pages(fhost):
    got = fhost.command("ideas.hypotheses", {})
    assert got["file"] == "docs/hypotheses.md" and [(i["id"], i["text"], i["state"]) for i in got["items"]] == [("h1", "People want a sketch first", "open")]
    assert got["items"][0]["refuted"][0]["name"] == "the hook" and got["items"][0]["if_holds"] == "Sketch first, always."
    item = hold(fhost, text="Founders pay", signal="ten say so", refuted=[{"name": "the price", "when": "none would"}])
    assert item["id"] == "h2"
    log = git(fhost.repo_root, "show", "dev:docs/hypotheses.md")
    assert "## H2. Founders pay" in log and "- **Refuted, the price**: none would" in log
    assert git(fhost.repo_root, "log", "-1", "--format=%s", "dev") == "board: hypothesis h2 — added"
    assert git(fhost.repo_root, "show", "--name-only", "--format=", "dev").split() == ["docs/hypotheses.md"]
    assert fhost.repo_root.joinpath("docs/hypotheses.md").read_text("utf-8") == OWN_FILE                      # the person's own checkout is not touched: dev holds the Board's


def test_a_verdict_writes_the_decision_and_the_file_each_one_commit(fhost):
    goal = make_goal(fhost, "Interview five founders", state="done", element="ice")
    fhost.command("ideas.hypothesis_attach", {"id": "h1", "test": goal})
    fhost.command("ideas.hypothesis_evidence", {"id": "h1", "text": "Four of five asked", "ref": goal})
    got = fhost.command("ideas.hypothesis_judge", {"id": "h1", "state": "held", "why": "Clear"})
    assert got["item"]["state"] == "held" and got["decision"]["number"] == 1
    text = git(fhost.repo_root, "show", "dev:docs/hypotheses.md")
    assert "**Status:** held; became decision §1." in text and "- Four of five asked (" + goal + ")" in text
    subjects = git(fhost.repo_root, "log", "-4", "--format=%s", "dev").splitlines()
    assert subjects[:2] == ["board: hypothesis h1 — judged held", "board: decision 1 — Hypothesis held: People want a sketch first"] and subjects[2] == "board: hypothesis h1 — evidence"
    assert [i["state"] for i in fhost.command("ideas.hypotheses", {})["items"]] == ["held"] and hand(fhost) == []


# -- spec 133 D: a refuted verdict is a finding --------------------------------------------------------------------------------------------------

def test_a_refuted_verdict_is_a_finding_naming_the_goals_that_rested_on_it_and_begins_the_run(host, monkeypatch):
    from orkboard.realm import findings
    began = []
    monkeypatch.setattr(host.ideas.keeper, "findings_begin", lambda slug: began.append(slug) or True)
    rests = make_goal(host, "Weekly digest")
    item_id, tested = with_test(host, refuted=WAYS, if_holds="Make it a setting.")
    host.command("ideas.hypothesis_attach", {"id": item_id, "goal": rests})
    got = host.command("ideas.hypothesis_judge", {"id": item_id, "state": "refuted", "way": "the hook", "why": "Only opens rose"})
    sd = host.ideas.state_dir
    (f,) = findings.of_goal(sd, "")
    assert got["finding"] == f["id"] and f["source"] == "hypothesis" and f["on"] == item_id and f["idea"] == "" and f["status"] == "found"
    assert "(the hook: opens rise, goals do not)" in f["found"] and f"Goals that rested on it: {rests} (Weekly digest)" in f["found"]
    assert got["item"]["verdict"]["finding"] == f["id"] and hypotheses.read(sd)["items"][0]["verdict"]["finding"] == f["id"]
    outcome = findings.record(sd, tested)["hypothesis"]
    assert (outcome["id"], outcome["state"], outcome["way"], outcome["why"]) == (item_id, "refuted", "the hook", "Only opens rose")
    assert findings.record(sd, rests)["hypothesis"] is None                                    # a goal that only rested on it is named in the finding, not given the outcome
    assert began == [""] and hand(host) == []                                                  # the run is begun, and the judged hypothesis has no card of its own: the finding's is the one


# -- spec 133 B: measures, the date, the values typed ------------------------------------------------------------------------------------------

BAR = {"op": "<=", "n": 70, "unit": "%"}


def test_a_measure_is_set_dropped_and_its_value_typed_and_no_number_is_shown_before_its_date(host):
    item = hold(host, refuted=WAYS)
    got = host.command("ideas.hypothesis_measure_set", {"id": item["id"], "what": "the cost of an install", "from": "the ads' platforms", "holds": BAR,
                                                        "refuted": [{"way": "the noise", "op": ">", "n": 100}], "span_days": 28})["item"]
    (m,) = got["measures"]
    assert m["id"] == "m1" and m["date"] > item["at"][:10] and m["bars"]["holds"]["n"] == 70 and m["bars"]["refuted"][0]["way"] == "the noise"
    typed = host.command("ideas.hypothesis_value", {"id": item["id"], "measure": "m1", "n": 64, "from": "the dashboard"})["item"]
    assert typed["measures"][0]["value"] is None                                                       # its date is not reached: the number is kept, not shown
    assert hypotheses.read(host.ideas.state_dir)["items"][0]["measures"][0]["value"]["n"] == 64.0
    assert host.command("ideas.hypotheses", {})["items"][0]["measures"][0]["value"] is None
    changed = host.command("ideas.hypothesis_measure_set", {"id": item["id"], "measure": "m1", "date": "2020-01-01"})["item"]["measures"][0]
    assert changed["date"] == "2020-01-01" and changed["value"]["n"] == 64.0 and changed["bars"]["refuted"]                                  # a date reached: the value is shown
    refused(host, "ideas.hypothesis_value", {"id": item["id"], "measure": "m1", "n": "lots"}, "is a number")
    refused(host, "ideas.hypothesis_measure_set", {"id": item["id"], "what": "x"}, "its bar")
    refused(host, "ideas.hypothesis_measure_drop", {"id": item["id"], "measure": "m9"}, "That measure is gone")
    assert host.command("ideas.hypothesis_measure_drop", {"id": item["id"], "measure": "m1"})["item"]["measures"] == []

