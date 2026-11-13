"""The mobile API on Orkboard's host (docs/design/mobile.md; gui/board_host.py `BoardPhone`): the handshake, the
compact snapshot and what a phone may send."""
from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from orkboard.gui import phones
from orkboard import __version__
from orkboard.gui.board_host import BoardPhone, Orkboard
from orkboard.gui.server import PROTOCOL, Server


def _host(repo: Path) -> Orkboard:
    return Orkboard(repo)


def test_a_phone_may_send_the_boards_commands_and_halt_but_not_build_or_type(fake_repo):
    host = _host(fake_repo)
    may = lambda name, args=None: BoardPhone.allowed(host, name, args)      # noqa: E731
    assert may("halt") and may("mobile.snapshot") and may("ideas.answer") and may("ideas.merge")
    assert not may("ideas.nothing") and not may("act", {"id": "pit", "act": "drop"})
    for name in ("town.build", "town.demolish", "term.input", "sessions.new", "hut.move", "roads.lay",
                 "orders.answer", "phones.pair", "update.policy", "update.restart", "link.open"):
        assert not may(name, {}), name
    assert may("update.check") and may("update.install")         # a newer version, installed from the phone (js/shell/update.js)
    assert may("repair.start") and may("repair.stop") and may("repair.update")   # Fix it (spec 119 §3.3, decisions §197.4)


@pytest.mark.asyncio
async def test_the_version_handshake_takes_the_token(fake_repo):
    server = Server(_host(fake_repo))
    task = asyncio.create_task(server.run())
    for _ in range(100):
        if server.ready.is_set():
            break
        await asyncio.sleep(0.02)

    def get(path: str, headers: dict | None = None) -> tuple[int, dict]:
        req = urllib.request.Request(f"{server.origin}{path}", headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, {}
    try:
        assert (await asyncio.to_thread(get, "/api/version"))[0] == 403
        assert (await asyncio.to_thread(get, "/api/version?t=guess"))[0] == 403
        status, body = await asyncio.to_thread(get, f"/api/version?t={server.token}")
        assert status == 200 and body == {"name": "orkcraft", "version": body["version"], "protocol": PROTOCOL,
                                          "api": phones.API}
        status, _ = await asyncio.to_thread(get, "/api/version", {"Authorization": f"Bearer {server.token}"})
        assert status == 200
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)


def test_the_phone_sees_a_newer_version_small_and_installs_it(fake_repo, monkeypatch):
    """A newer Orkboard on the phone (js/shell/update.js): what it is and a few notes, then `update.install` from the
    phone installs it on the computer, which restarts on it (gui/updates.py)."""
    from types import SimpleNamespace
    from orkboard.core import updates
    from orkboard.gui import updates as gui_updates
    host = _host(fake_repo)
    assert host.command("mobile.snapshot")["update"] is None
    host.updates._method = lambda: updates.Method("uv", (("uv", "tool", "upgrade", "orkboard"),))
    rels = [{"version": f"9.0.{n}", "notes": f"notes {n}"} for n in range(5, 0, -1)]
    host.updates._read(updates.State(manifest={"releases": rels}))
    u = host.command("mobile.snapshot")["update"]
    assert (u["version"], u["major"], u["critical"], u["can"], u["state"]) == ("9.0.5", True, False, True, "idle")
    assert u["notes"] == ["9.0.5: notes 5", "9.0.4: notes 4", "9.0.3: notes 3"] and u["current"] == __version__
    before = host.command("mobile.snapshot")["rev"]
    monkeypatch.setattr(gui_updates.threading, "Thread", lambda target, **kw: SimpleNamespace(start=target))
    monkeypatch.setattr(updates, "install", lambda way: updates.Result(True, "ok", "9.0.5"))
    monkeypatch.setattr(updates, "remember", lambda result, version: None)
    quits = []
    host.updates.quit = lambda: quits.append(1)
    assert BoardPhone.allowed(host, "update.install", {})
    host.command("update.install", BoardPhone.guard("update.install", {}, {"id": "d1"}))
    assert quits == [1] and host.updates.restart_wanted                 # the window closes: `orkboard` opens again on 9.0.5
    after = host.command("mobile.snapshot")
    assert after["update"]["state"] == "installed" and after["rev"] != before
    host.close()


@pytest.mark.asyncio
async def test_the_server_serves_the_page_and_its_files_and_answers_the_sockets_commands(fake_repo):
    from websockets.asyncio.client import connect
    from websockets.exceptions import InvalidStatus

    server = Server(_host(fake_repo))
    task = asyncio.create_task(server.run())
    for _ in range(100):
        if server.ready.is_set():
            break
        await asyncio.sleep(0.02)

    def get(path: str) -> tuple[int, str, bytes]:
        try:
            with urllib.request.urlopen(f"{server.origin}{path}", timeout=5) as r:
                return r.status, r.headers.get("Content-Type", ""), r.read()
        except urllib.error.HTTPError as e:
            return e.code, "", b""

    try:
        status, kind, body = await asyncio.to_thread(get, "/")
        assert status == 200 and kind.startswith("text/html") and b"<html" in body.lower()
        assert (await asyncio.to_thread(get, "/favicon.ico"))[:2] == (200, "image/x-icon")
        assert (await asyncio.to_thread(get, "/roles.css"))[1].startswith("text/css")
        assert (await asyncio.to_thread(get, "/no/such/file.js"))[0] == 404
        assert (await asyncio.to_thread(get, "/api/analytics"))[0] == 403
        ws_url = f"ws://127.0.0.1:{server.port}/ws"
        for url, origin in ((ws_url, server.origin), (f"{ws_url}?t={server.token}", "http://evil.example")):
            with pytest.raises(InvalidStatus):
                async with connect(url, origin=origin):
                    pass
        async with connect(f"{ws_url}?t={server.token}", origin=server.origin) as ws:
            assert json.loads(await ws.recv())["t"] == "state"

            async def say(text: str) -> dict:
                await ws.send(text)
                while True:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), 5))
                    if msg["t"] == "reply":
                        return msg

            assert (await say("{"))["error"] == "Not a command"
            assert (await say(json.dumps({"t": "cmd", "id": 1, "name": "halt", "args": [1]})))["error"] == "Arguments are an object"
            assert (await say(json.dumps({"t": "cmd", "id": 2, "name": "no.such"})))["ok"] is False
            server.host.command = lambda name, args=None: 1 / 0
            broken = await say(json.dumps({"t": "cmd", "id": 3, "name": "halt"}))
            assert broken["ok"] is False and "ZeroDivisionError" in broken["error"]          # the page stays open
            del server.host.command
            assert (await say(json.dumps({"t": "cmd", "id": 4, "name": "halt"})))["ok"] is True
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)


def test_the_window_falls_back_to_the_browser_the_launcher_refuses_a_bad_folder_and_the_door_and_links_are_checked(
        fake_repo, tmp_path, monkeypatch, capsys):
    import sys
    from types import SimpleNamespace

    from orkboard.gui import board_host

    host = Orkboard(fake_repo)
    with pytest.raises(Exception, match="Only web links"):
        host.command("link.open", {"url": "javascript:alert(1)"})
    opened = []
    monkeypatch.setattr(board_host.webbrowser, "open", lambda url: opened.append(url) or True)
    assert host.command("link.open", {"url": "https://example.com/x"}) is True and opened == ["https://example.com/x"]
    with pytest.raises(Exception, match="Here or Away"):
        host.command("presence.set", {"here": "yes"})
    # no window toolkit, no pywebview, or a window that cannot start: the page opens in the browser, and the run ends clean
    calls = []
    server = SimpleNamespace(url="http://127.0.0.1:9/?t=k", stop=lambda: calls.append("server"))
    thread = SimpleNamespace(join=lambda t=None: calls.append("join"))
    shown = SimpleNamespace(updates=SimpleNamespace(quit=None))
    board_host.show(shown, server, thread, False, toolkit=lambda: False, stop=lambda: calls.append("stop"))
    assert "no window here" in capsys.readouterr().err and opened[-1] == server.url and calls[-1] == "stop"
    monkeypatch.setitem(sys.modules, "webview", None)
    board_host.show(shown, server, thread, False, toolkit=lambda: True)
    assert "no window toolkit" in capsys.readouterr().err

    class Window:
        destroy = staticmethod(lambda: None)

    made = {}
    fake = SimpleNamespace(create_window=lambda title, url, **kw: made.update(url=url) or Window(), start=lambda: None)
    monkeypatch.setitem(sys.modules, "webview", fake)
    dressed, attached = [], []
    board_host.show(shown, server, thread, False, toolkit=lambda: True, attach=attached.append, dress=lambda: dressed.append(1))
    assert made["url"].endswith("&app=1") and dressed and len(attached) == 1 and shown.updates.quit is Window.destroy
    fake.start = lambda: (_ for _ in ()).throw(RuntimeError("no GTK"))
    board_host.show(shown, server, thread, False, toolkit=lambda: True)
    assert "no window here (no GTK)" in capsys.readouterr().err
    # the folder `orkboard` opens: the last shown project, else none
    gone = SimpleNamespace(projects_recent=[str(tmp_path / "gone")])
    monkeypatch.chdir(tmp_path)
    assert board_host.start_folder(None, gone) is None
    assert board_host.start_folder(None, SimpleNamespace(projects_recent=[str(fake_repo)])) == fake_repo.resolve()
    monkeypatch.setattr(board_host.core_updates, "at_launch", lambda *a, **k: None)
    assert board_host.main([str(tmp_path / "not-a-folder")]) == 1 and "orkboard:" in capsys.readouterr().err
