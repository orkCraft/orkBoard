"""The registry of AI tools (realm/harnesses.py): every tool answers, reads and works through it, and
its output is read the same way whatever the tool."""
from __future__ import annotations

import json

import pytest

from orkboard.realm import harnesses, tool_run


def _lines(*events: dict) -> str:
    return "\n".join(json.dumps(e) for e in events)


# agy's envelope from the logs of 26 October: a spec's read that asked for a terminal command, refused headless, and said nothing.
AGY_REFUSED = json.dumps({"conversation_id": "9d5b2443", "status": "SUCCESS", "response": "", "duration_seconds": 44.4, "num_turns": 1,
                          "usage": {"input_tokens": 26158, "output_tokens": 1819, "total_tokens": 27977},
                          "denied_actions": [{"action": "command", "display_name": "RunCommand"}]})


def test_hermes_reads_its_stream():
    out = _lines({"type": "system", "subtype": "init", "model": "m", "session_id": "20261007_120000_abcdef"},
                 {"type": "text", "text": "par"}, {"type": "text", "text": "tial"},
                 {"type": "result", "session_id": "20261007_120000_abcdef", "exit_code": 0, "text": "the answer",
                  "tokens": {"input": 10, "output": 5, "total": 15}})
    assert harnesses.hermes_result(out) == ("the answer", None, 15, "20261007_120000_abcdef")
    assert harnesses.hermes_error(_lines({"type": "result", "error": "no provider"})) == "no provider"
    h = harnesses.need("hermes")
    assert "--toolsets" in h.read("x", "/r") and "write" not in " ".join(h.read("x", "/r"))
    assert h.env("read", "/r")["HERMES_WRITE_SAFE_ROOT"] == harnesses.NOWHERE           # reading writes nowhere
    assert h.env("work", "/w")["HERMES_WRITE_SAFE_ROOT"] == "/w"                        # working: its worktree


def test_pi_sums_its_messages_and_their_price():
    usage = lambda n, usd: {"totalTokens": n, "cost": {"total": usd}}                  # noqa: E731
    out = _lines({"type": "session", "version": 3, "id": "u-1", "cwd": "/r"},
                 {"type": "message_end", "message": {"role": "assistant", "content": [{"type": "text", "text": "a"}],
                                                     "usage": usage(100, 0.01)}},
                 {"type": "message_end", "message": {"role": "toolResult", "content": []}},
                 {"type": "message_end", "message": {"role": "assistant", "content": [{"type": "text", "text": "done"}],
                                                     "usage": usage(50, 0.02)}})
    text, cost, tokens, session = harnesses.pi_result(out)
    assert (text, round(cost, 4), tokens, session) == ("done", 0.03, 150, "u-1")
    h = harnesses.need("pi")
    read = h.read("x", "/r")
    assert "--no-tools" in h.ask("x", "/f") and read[read.index("--tools") + 1] == "read,grep,find,ls"
    assert read[read.index("-e") + 1].endswith("orkcraft.ts")                         # the Warder rides along


def test_claude_says_why_it_failed_from_its_envelope():
    # the owner's 19 October: a draft said only `claude exited with 1: {"duration_api_ms":0,…`; the envelope puts
    # is_error and result after usage, so a line cut from the raw JSON never says why
    env = {"duration_api_ms": 0, "stop_reason": "stop_sequence", "session_id": "s-1", "total_cost_usd": 0,
           "usage": {"input_tokens": 0, "output_tokens": 0}, "type": "result", "is_error": True, "num_turns": 1,
           "subtype": "success", "result": "Not logged in · Please run /login"}
    out = json.dumps(env)
    assert harnesses.claude_error(out) == "Not logged in · Please run /login"
    assert harnesses.claude_error(_lines({"type": "system", "subtype": "init"}, env)) == env["result"]   # stream-json
    assert harnesses.claude_error(json.dumps({**env, "is_error": False})) == ""
    assert harnesses.claude_error(json.dumps({"type": "result", "subtype": "error_max_turns", "is_error": True})) \
        == "error_max_turns"
    assert harnesses.claude_error("error: unknown option '--nope'") == ""          # its stderr says it then
    err = tool_run.failure("claude", 1, out, "")
    assert str(err) == "claude exited with 1: Not logged in · Please run /login" and err.kind == "login"


def test_a_refused_claude_sign_in_says_what_is_different_here():
    # the owner's 19 October: "not signed in", while claude starts in the terminal
    from orkboard.realm import tool_errors
    no = tool_errors.claude_sign_in("Not logged in · Please run /login", env={})
    assert "Orkboard runs it with another config folder (CLAUDE_CONFIG_DIR) or another claude" in no and "Save logs" in no
    key = tool_errors.claude_sign_in("Invalid API key · Fix external API key", env={"ANTHROPIC_API_KEY": "sk-x"})
    assert key.startswith("ANTHROPIC_API_KEY is set where Orkboard runs, and claude -p uses it before your sign-in")
    assert "sk-x" not in key
    assert tool_errors.claude_sign_in("OAuth token revoked · Please run /login", env={}) == "Sign in again in a terminal: claude, then /login."
    err = tool_errors.ToolError("claude", "Not logged in · Please run /login", 1)
    line = tool_errors.plainly(err)
    assert line.startswith("Claude Code is not signed in, or its sign-in has expired. Claude Code said: Not logged in")
    assert line.endswith("Else sign in in a terminal: claude, then /login.")
    long = tool_errors.plainly(tool_errors.ToolError("claude", "Not logged in " + "x" * 2000, 1))
    assert len(long) <= tool_errors.PLAIN_CHARS and "…" in long and long.endswith("then /login.")   # its words cut, the step kept


def test_a_claude_sign_in_it_could_not_renew_says_retry_waits_for_a_new_one():
    # the owner's 20 October: "Claude Code said: Failed to authenticate: OAuth session expired and could not be
    # refreshed Sign in again in a terminal: …", its words and the step run together; Claude Code had deleted the
    # saved sign-in (code.claude.com/docs/en/errors#login-expired), so Retry alone never helps
    from orkboard.realm import tool_errors
    said = "Failed to authenticate: OAuth session expired and could not be refreshed"
    err = tool_errors.ToolError("claude", said, 1)
    assert err.kind == "login"
    assert tool_errors.plainly(err) == (
        "Claude Code is not signed in, or its sign-in has expired. Claude Code said: Failed to authenticate: OAuth "
        "session expired and could not be refreshed. Claude Code could not renew its sign-in and removed it, so Retry "
        "fails until you sign in again in a terminal: claude, then /login.")
    assert tool_errors.claude_sign_in("Login expired · Please run /login", env={}).startswith(
        "Claude Code could not renew its sign-in and removed it")
    # another claude was renewing it (Orkboard runs several at once): wait, no new sign-in needed
    busy = tool_errors.claude_sign_in("Failed to refresh OAuth token: another Claude Code process is refreshing it or "
                                      "exited mid-refresh. This is usually transient; retry in a minute", env={})
    assert busy.startswith("Another Claude Code was renewing the sign-in: Retry in a minute.")
    assert tool_errors.plainly(tool_errors.ToolError("claude", "Login expired!", 1)).count("!.") == 0   # its own end kept


def test_cursor_reads_its_result_line():
    out = _lines({"type": "system", "subtype": "init", "session_id": "c-1", "model": "Auto"},
                 {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "hi"}]},
                  "session_id": "c-1"},
                 {"type": "result", "subtype": "success", "is_error": False, "result": "hi", "session_id": "c-1",
                  "usage": {"inputTokens": 7, "outputTokens": 3, "cacheReadTokens": 0, "cacheWriteTokens": 0}})
    assert harnesses.cursor_result(out) == ("hi", None, 10, "c-1")
    assert harnesses.cursor_error(_lines({"type": "result", "subtype": "error", "is_error": True, "result": "bad model"})) \
        == "bad model"
    assert "--mode" in harnesses.need("cursor").read("x", "/r")                         # ask: never edits


@pytest.mark.parametrize("tool, answer, expect", [
    ("hermes", _lines({"type": "result", "session_id": "s", "text": "{}", "tokens": {"total": 3}}), ("{}", None)),
    ("pi", _lines({"type": "session", "id": "s"}, {"type": "message_end", "message": {
        "role": "assistant", "content": [{"type": "text", "text": "{}"}], "usage": {"totalTokens": 3, "cost": {"total": 0.5}}}}),
     ("{}", 0.5)),
    ("cursor", _lines({"type": "result", "result": "{}", "session_id": "s"}), ("{}", None)),
])
def test_a_decision_runs_on_any_tool(tool, answer, expect, tmp_path, monkeypatch):
    fake, record = tmp_path / f"fake-{tool}", tmp_path / "argv.json"
    fake.write_text("#!/usr/bin/env python3\nimport json, os, sys\n"
                    "stdin = '' if sys.stdin is None or sys.stdin.isatty() else sys.stdin.read()\n"
                    f"json.dump({{'argv': sys.argv[1:], 'stdin': stdin, 'env': dict(os.environ)}}, open({str(record)!r}, 'w'))\n"
                    f"sys.stdout.write({answer!r})\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv(f"ORKCRAFT_{tool.upper()}_BIN", str(fake))
    assert tool_run.ask(tool, "plan it") == expect
    rec = json.loads(record.read_text())
    assert ("plan it" in rec["argv"]) != (rec["stdin"] == "plan it")
    assert not any(k.startswith("ORKCRAFT_") for k in rec["env"])
    assert tool_run.resolve("main") in harnesses.ids()


def test_logins_of_the_new_tools_are_told_from_disk(tmp_path):
    from orkboard import tools
    home = tmp_path
    assert tools._hermes_login({}, home) == (None, "subscription")
    (home / ".hermes").mkdir()
    (home / ".hermes" / ".env").write_text("OPENROUTER_API_KEY=sk-x\n", encoding="utf-8")
    assert tools._hermes_login({}, home) == (True, "api")
    (home / ".hermes" / "auth.json").write_text('{"providers": {"nous": {}}}', encoding="utf-8")
    assert tools._hermes_login({}, home) == (True, "subscription")
    (home / ".pi" / "agent").mkdir(parents=True)
    (home / ".pi" / "agent" / "auth.json").write_text('{"anthropic": {"type": "oauth"}}', encoding="utf-8")
    assert tools._pi_login({}, home) == (True, "subscription")
    assert tools._cursor_login({"CURSOR_API_KEY": "k"}, home) == (True, "subscription")
    assert tools._cursor_login({}, home) == (None, "subscription")
    found = tools.detect(which=lambda b: f"/bin/{b}" if b in ("pi", "cursor-agent") else None,
                         run=lambda *a, **k: type("P", (), {"stdout": "1.0.4", "stderr": "", "returncode": 0})(),
                         env={}, home=home)
    assert [s.id for s in found if s.found] == ["pi", "cursor"] and found[4].logged_in


# -- spec 97 part A: the read-only call bounded in fact, its floor bare, its reads counted ---------------------------------

def _flag_values(argv, flag):
    return [argv[i + 1] for i, a in enumerate(argv) if a == flag]


def _stream(*uses, text="done", subtype="success", denied=(), cost=0.04, session="s-1"):
    """A read call's stream-json: its init, each tool use `(name, input)` with its result, and its result event."""
    out = [{"type": "system", "subtype": "init", "session_id": session}]
    for n, (name, given) in enumerate(uses):
        out += [{"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"t{n}", "name": name, "input": given}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{n}", "content": "x"}]}}]
    out.append({"type": "result", "subtype": subtype, "is_error": False, "result": text, "total_cost_usd": cost,
                "session_id": session, "usage": {"input_tokens": 900, "output_tokens": 100, "cache_creation_input_tokens": 3000,
                                                 "cache_read_input_tokens": 4000}, "permission_denials": list(denied)})
    return _lines(*out)


def _envelope(**over):
    return json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "done", "total_cost_usd": 0.04,
                       "session_id": "s-1", "usage": {"input_tokens": 900, "output_tokens": 100, "cache_creation_input_tokens": 3000,
                                                      "cache_read_input_tokens": 4000}, **over})


def test_a_read_only_call_is_denied_the_files_no_leader_needs_in_its_one_list(tmp_path, monkeypatch):
    from orkboard.realm import harness_claude
    monkeypatch.setattr(harness_claude, "cli_has", lambda h, flag: False)
    h = harnesses.get("claude")
    assert len(harnesses.READ_DENIED) == len(set(harnesses.READ_DENIED)) == 18 + 8 + 11 + 4 + 2
    for web in (False, True):
        argv = harnesses._claude_read(h, "p", str(tmp_path), "opus", web)
        [deny] = _flag_values(argv, "--disallowedTools")                        # one list, never a second flag
        rules = deny.split(",")
        for rule in ("Read(**/package-lock.json)", "Read(**/uv.lock)", "Read(**/packages.lock.json)", "Read(**/go.sum)",
                     "Read(**/node_modules/**)", "Read(**/vendor/**)", "Read(**/.venv/**)", "Read(**/dist/**)",
                     "Read(**/__pycache__/**)", "Read(**/*.min.js)", "Read(**/*.map)", "Read(**/decisions.md)",
                     "Read(**/DECISIONS.md)", "Edit", "Bash"):
            assert rule in rules
        assert ("WebSearch" in rules) is (not web)                              # the lists it had are kept whole
        assert set(harnesses.READ_DENIED) <= set(rules)
    assert "--disallowedTools" in h.read("p", tmp_path, "opus", tools=False)    # no tools at all: still the lists it had
    for argv in (h.work("p", tmp_path, "opus"), h.ask("p", tmp_path, "opus")):
        assert "Read(**" not in " ".join(argv)                                  # a work or an ask keeps its flags


def test_a_result_is_read_the_same_from_the_one_object_and_from_its_stream_json_twin():
    stream, single = _stream(("Read", {"file_path": "a.py"}), ("Grep", {"pattern": "x"})), _envelope()
    for out in (stream, single):
        assert harnesses.get("claude").result(out, 0) == ("done", 0.04, 8000, "s-1")
        assert harnesses.get("claude").outcome(out, 0, "opus") == ("done", 0.04, 8000, "s-1")
        assert harnesses.usage_split(out) == {"in": 3900, "out": 100, "cache_read": 4000}
        assert harnesses.claude_error(out) == "" and not harnesses.capped(out)
    from orkboard.realm import call_log
    assert call_log.session_of(stream) == call_log.session_of(single) == "s-1" and call_log.session_of("plain") == ""
    assert harnesses.get("claude").result("plain words", 0) == ("plain words", None, None, "")
    assert harnesses.usage_split("plain words") is None
    cut = _lines({"type": "system", "subtype": "init"}, {"type": "assistant", "message": {"content": []}})
    assert harnesses.get("claude").result(cut, 0)[0] == ""                                  # a stream that never reached its result
    bare = '{"subtype": "error_max_budget_usd"}'
    assert harnesses.get("claude").result(bare, 0)[0] == bare                               # as json_result gave it
    assert harnesses.json_result(single)[:2] == ("done", 0.04)                              # the others' reader is as it was


def test_claude_reads_counts_files_searches_denials_and_makes_paths_relative(tmp_path):
    folder = tmp_path / "game"
    out = _stream(("Read", {"file_path": str(folder / "src" / "a.py")}), ("Read", {"file_path": str(folder / "src" / "a.py")}),
                  ("Read", {"file_path": "/etc/hosts"}), ("Read", {"file_path": str(folder / "uv.lock")}),
                  ("Grep", {"pattern": "x"}), ("Glob", {"pattern": "*.py"}), ("Bash", {"command": "ls"}),
                  denied=[{"tool_name": "Read", "tool_use_id": "t3", "tool_input": {}}, {"tool_name": "Bash"},
                          {"tool_name": "Glob"}, "junk"])
    got = harnesses.claude_reads(out, folder)
    assert got == {"files": 3, "searches": 2, "paths": ["src/a.py", "/etc/hosts", "uv.lock"], "denied": 2}
    assert harnesses.claude_reads(out)["paths"][0] == str(folder / "src" / "a.py")           # no folder: as named
    many = harnesses.claude_reads(_stream(*[("Read", {"file_path": f"/f/{n}.py"}) for n in range(40)]))
    assert many["files"] == 40 and len(many["paths"]) == 30
    assert harnesses.claude_reads(_envelope()) == {"files": 0, "searches": 0, "paths": [], "denied": 0}
    assert harnesses.claude_reads("not json") == {"files": 0, "searches": 0, "paths": [], "denied": 0}
