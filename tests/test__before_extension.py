"""Orkboard in an editor (gui/extension.py, vscode/): `orkboard --serve` says where the page is as one line of JSON,
serves it to an iframe of the server's own origin, and stops when the editor closes its stdin."""
from __future__ import annotations

import io
import json
import os
import threading

import pytest
from websockets.exceptions import InvalidStatus
from websockets.sync.client import connect

from orkboard.gui import board_host, extension
from orkboard.gui.board_host import Orkboard
from orkboard.gui.server import Server


def test_serve_says_the_address_and_stops_when_stdin_closes(fake_repo):
    host = Orkboard(fake_repo)
    server = Server(host)
    thread = server.start_thread()
    read, write = os.pipe()
    stdin, out, closed = os.fdopen(read), io.StringIO(), []
    done = threading.Thread(target=extension.serve,
                            args=(host, server, thread, lambda *a: closed.append(a)), kwargs={"stdin": stdin, "out": out})
    done.start()
    try:
        while not out.getvalue():
            done.join(0.01)
        said = json.loads(out.getvalue())
        assert said["origin"] == server.origin and said["url"].endswith("&app=1") and f"t={server.token}" in said["url"]
        assert host.updates.quit == server.stop                  # an update that restarts stops this server
        ws = f"ws://127.0.0.1:{server.port}/ws?t={server.token}"
        with connect(ws, origin=said["origin"]) as socket:        # the panel's iframe: the server's own origin
            assert json.loads(socket.recv(5))["t"] == "state"
    finally:
        os.close(write)                                          # the editor went away
        done.join(10)
    assert not done.is_alive() and closed and not thread.is_alive()


def test_serve_is_asked_for_and_kept_over_an_update(fake_repo, monkeypatch):
    started, restarted = [], []
    monkeypatch.setenv("ORKCRAFT_NO_UPDATE", "1")
    monkeypatch.setattr(board_host, "run", lambda root, browser=False, port=0, serve=False:
                        started.append(serve) or board_host.core_updates.RESTART)
    monkeypatch.setattr(board_host.core_updates, "restart", restarted.append)
    board_host.main(["--serve", str(fake_repo)])
    assert started == [True] and restarted == [["--repo", str(fake_repo.resolve()), "--serve"]]


def test_the_socket_takes_the_server_as_localhost_and_no_other_origin(fake_repo):
    """An editor's `asExternalUri` may name the server `localhost`: the same machine, the same port."""
    server = Server(Orkboard(fake_repo))
    thread = server.start_thread()
    ws = f"ws://127.0.0.1:{server.port}/ws?t={server.token}"
    try:
        with connect(ws, origin=f"http://localhost:{server.port}") as socket:
            assert json.loads(socket.recv(5))["t"] == "state"
        for other in (f"http://localhost:{server.port + 1}", "vscode-webview://abc", "https://example.com"):
            with pytest.raises(InvalidStatus):
                connect(ws, origin=other)
    finally:
        server.stop()
        thread.join(10)
