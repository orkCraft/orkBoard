"""A task's log as the host gives it to the pane (docs/specs/168 I1): the values of the goal's secrets masked before the log leaves the host (in plain words, in a URL, in a JSON line), its steps and its party with it,
a task run in the person's own AI tool with no log, and `ideas.task_log` the light read of its tail."""
from __future__ import annotations

import json

from orkboard.realm import idea_secrets, ideas
from tests.test_gui_ideas import _review, host  # noqa: F401  (fixture)

VALUE = "sk-live-9f3A/b+c=Zq7"
LOG = (f"== round 1 · now\nthe prompt, with {VALUE} in it\n== the gate, try 1\nGET https://api.x.io/v1?key=sk-live-9f3A%2Fb%2Bc%3DZq7\n"
       f"{json.dumps({'key': VALUE})}\nplain {VALUE} here\nand a short word: ok\n")


def _goal_with_a_secret(host, monkeypatch, tmp_path, **more):
    monkeypatch.setenv("ORKCRAFT_LOGINS_FILE", str(tmp_path / "logins.json"))          # the OS keychain is kept out of the tests
    slug = _review(host, **more)
    state = host.ideas.state_dir
    ideas.edit_plan(state, slug, lambda p: p.update(todos=[{"id": "t9", "title": "PAY_KEY", "kind": "secret", "for": ["k1"], "why": "x", "done": True}]))
    idea_secrets.put(state, slug, "t9", VALUE)
    log = state / "ideas" / slug / "k1.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(LOG, encoding="utf-8")
    host.ideas.runner(need=True)
    return slug


def test_the_log_leaves_the_host_with_the_goals_secret_masked_in_every_form(host, monkeypatch, tmp_path):
    slug = _goal_with_a_secret(host, monkeypatch, tmp_path)
    for name in ("ideas.task", "ideas.task_log"):
        got = host.command(name, {"slug": slug, "task": "k1"})
        text = got["log"]
        assert VALUE not in text and "sk-live" not in text and "9f3A%2F" not in text, (name, text)
        assert text.count("••••") == 4 and "and a short word: ok" in text and "== the gate, try 1" in text
    assert host.command("ideas.task_log", {"slug": slug, "task": "k1"})["state"] == "review"


def test_a_task_run_in_the_persons_own_ai_tool_has_no_log_and_says_so(host, monkeypatch, tmp_path):
    slug = _goal_with_a_secret(host, monkeypatch, tmp_path, ran_in="own")
    got = host.command("ideas.task", {"slug": slug, "task": "k1"})
    assert got["own_tool"] is True and got["log"] == ""
    assert host.command("ideas.task_log", {"slug": slug, "task": "k1"})["own_tool"] is True
