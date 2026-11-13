"""The listener for phones, stage 1 of docs/design/mobile.md: pairing, device tokens, TLS pinned by its
fingerprint, and a socket that passes only what a phone may send."""
from __future__ import annotations

import asyncio
import hashlib
import http.client
import json
import os
import ssl
import stat
from pathlib import Path

import pytest
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidStatus

from orkboard import settings
from orkboard.gui import pairing, phone_tls, phones
from orkboard.gui.board_host import BoardPhone, Orkboard
from orkboard.gui.server import PROTOCOL, Server


# -- pairing, without a network ----------------------------------------------------------------------

def test_a_code_pairs_once_and_the_host_keeps_only_the_tokens_hash(tmp_path):
    p = pairing.Pairing(tmp_path / "settings.json")
    code = p.new_code(now=0.0)
    assert len(code) >= 43                                          # 32 random bytes
    device_id, token, name = p.pair(code, "  My\x07 phone ", now=1.0)
    assert name == "My phone" and p.device(token)["id"] == device_id
    raw = (tmp_path / "settings.json").read_text()
    assert token not in raw and code not in raw and hashlib.sha256(token.encode()).hexdigest() in raw
    assert set(p.public()[0]) == {"id", "name", "paired", "seen"}
    with pytest.raises(pairing.PairError):
        p.pair(code, "again", now=2.0)                              # once
    assert p.device("guess") is None and p.device("") is None and p.device(token[:-1]) is None


def test_the_sixth_attempt_in_a_minute_locks_pairing_until_a_new_code(tmp_path):
    p = pairing.Pairing(tmp_path / "settings.json")
    code = p.new_code(now=0.0)
    assert all(p.attempt(now=float(i)) for i in range(5))
    assert not p.attempt(now=6.0) and p.locked
    with pytest.raises(pairing.PairError):
        p.pair(code, "right code, too late", now=7.0)               # the code went with the lock
    assert not p.attempt(now=100.0)                                 # locked until the desktop shows a new code
    fresh = p.new_code(now=101.0)
    assert p.attempt(now=101.0) and p.pair(fresh, "phone", now=102.0)


def test_forget_is_at_once_and_a_town_that_loaded_earlier_never_brings_a_phone_back(tmp_path):
    file = tmp_path / "settings.json"
    stale = settings.load(file)                                     # another town on this machine, opened before
    p = pairing.Pairing(file)
    device_id, token, _ = p.pair(p.new_code(), "phone")
    loaded = settings.load(file)
    assert [d["id"] for d in loaded.phones] == [device_id]
    settings.save(stale, file)                                      # it saves its own settings…
    assert p.device(token) is not None                              # …and the phone stays paired
    assert p.forget(device_id) and p.device(token) is None
    settings.save(loaded, file)                                     # a town that knew the phone saves…
    assert p.device(token) is None and settings.load(file).phones == []   # …and it stays forgotten


def test_the_certificate_is_made_once_kept_private_and_named_by_its_fingerprint(tmp_path):
    cert, key = phone_tls.ensure(tmp_path)
    assert stat.S_IMODE(os.stat(key).st_mode) == 0o600 and stat.S_IMODE(os.stat(cert).st_mode) == 0o600
    fp = phone_tls.fingerprint(cert)
    assert len(fp.split(":")) == 32
    assert phone_tls.ensure(tmp_path) == (cert, key) and phone_tls.fingerprint(cert) == fp


def test_a_phone_may_not_pair_list_or_forget_phones(fake_repo):
    host = Orkboard(fake_repo)
    for name in ("phones.pair", "phones.list", "phones.forget", "phones.pair_stop", "watch", "term.attach",
                 "term.replay", "town.settings.set"):
        assert not BoardPhone.allowed(host, name, {}), name


# -- the listener, over TLS on 127.0.0.1 -----------------------------------------------------------

def _pinned() -> ssl.SSLContext:
    """As a phone does: no CA, the certificate's fingerprint checked after the handshake."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname, ctx.verify_mode = False, ssl.CERT_NONE
    return ctx


def _fp(der: bytes) -> str:
    return ":".join(f"{b:02X}" for b in hashlib.sha256(der).digest())


def _https(address: str, method: str, path: str, body: dict | None = None, headers: dict | None = None,
           raw: bytes | None = None) -> tuple[int, dict, str]:
    host, port = address.removeprefix("https://").rsplit(":", 1)
    conn = http.client.HTTPSConnection(host, int(port), context=_pinned(), timeout=5)
    try:
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        hdrs = {"Content-Type": "application/json"} if data is not None else {}
        conn.request(method, path, body=data, headers={**hdrs, **(headers or {})})
        fp = _fp(conn.sock.getpeercert(binary_form=True))
        r = conn.getresponse()
        text = r.read().decode()
        try:
            out = json.loads(text)
        except ValueError:
            out = {}
        return r.status, out, fp
    finally:
        conn.close()


async def _serve(repo: Path):
    server = Server(Orkboard(repo))
    server.phones.bind = "127.0.0.1"
    task = asyncio.create_task(server.run())
    for _ in range(200):
        if server.ready.is_set():
            break
        await asyncio.sleep(0.02)
    return server, task


async def _listening(server: Server) -> None:
    for _ in range(200):
        if server.phones.server is not None and not isinstance(server.phones.server, phones._Pending):
            return
        await asyncio.sleep(0.02)
    raise AssertionError("the listener did not come up")


async def _pair(server: Server, name: str = "Test phone") -> tuple[str, str]:
    offer = server.host.command("phones.pair")
    await _listening(server)
    status, body, fp = await asyncio.to_thread(_https, offer["address"], "POST", "/api/pair",
                                               {"code": offer["code"], "name": name})
    assert status == 200 and fp == offer["fingerprint"], body
    assert offer["link"].endswith("code=" + offer["code"]) and offer["qr"]
    return body["id"], body["token"]


def _ws_url(server: Server) -> str:
    return server.phones.address.replace("https://", "wss://") + "/ws"


@pytest.mark.asyncio
async def test_a_paired_phone_reads_the_compact_town_and_sends_only_what_a_phone_may(fake_repo):
    server, task = await _serve(fake_repo)
    try:
        device_id, token = await _pair(server)
        auth = {"Authorization": f"Bearer {token}"}
        status, body, _ = await asyncio.to_thread(_https, server.phones.address, "GET", "/api/version", None, auth)
        assert status == 200 and body["protocol"] == PROTOCOL and body["api"] == phones.API
        status, _, _ = await asyncio.to_thread(_https, server.phones.address, "GET", "/api/version")
        assert status == 403
        assert (await asyncio.to_thread(_https, server.phones.address, "GET", "/", None, auth))[0] == 404

        async with connect(_ws_url(server), ssl=_pinned(), additional_headers=auth) as ws:
            first = json.loads(await asyncio.wait_for(ws.recv(), 5))
            assert first["t"] == "state" and "rev" in first["state"] and "projects" in first["state"]
            assert not set(Orkboard.COMPUTER_ONLY) & set(first["state"])        # the computer's own stay on the computer

            async def cmd(i, name, args=None):
                await ws.send(json.dumps({"t": "cmd", "id": i, "name": name, "args": args or {}}))
                while True:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), 5))
                    if msg["t"] == "reply" and msg["id"] == i:
                        return msg

            hello = await cmd(1, "mobile.hello")
            assert hello["ok"] and hello["result"]["api"] == phones.API
            said = set(hello["result"]["commands"])                    # what this phone may send, not what the host has
            assert {"ideas.board", "halt", "projects.use"} <= said and "files.read" in said
            assert not {"phones.pair", "git.status", "tools.sign_in", "onboarding.skip"} & said
            assert all(BoardPhone.allowed(server.host, c, {"path": "x.md"}) for c in said)
            same = await cmd(2, "mobile.snapshot", {"since": first["state"]["rev"]})
            assert same["result"]["same"] is True
            for i, name in enumerate(("term.input", "town.build", "watch", "term.attach", "phones.pair",
                                      "town.settings.set"), start=10):
                refused = await cmd(i, name, {"key": "x", "data": "rm -rf /\r"})
                assert not refused["ok"] and refused["error"] == f"Not from a phone: {name}"
            answered = await cmd(20, "ideas.board")                  # the Board's commands are a phone's
            assert answered["ok"] and "tracks" in answered["result"]
            halted = await cmd(21, "halt")
            assert halted["ok"] and isinstance(halted["result"], int)
        seen = server.host.command("phones.list")["phones"]
        assert [p["id"] for p in seen] == [device_id]
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)


@pytest.mark.asyncio
async def test_without_a_device_token_there_is_no_socket(fake_repo):
    server, task = await _serve(fake_repo)
    try:
        await _pair(server)
        for headers in ({}, {"Authorization": "Bearer guess"}, {"Authorization": f"Bearer {server.token}"}):
            with pytest.raises(InvalidStatus) as e:
                async with connect(_ws_url(server), ssl=_pinned(), additional_headers=headers):
                    pass
            assert e.value.response.status_code == 403
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)


@pytest.mark.asyncio
async def test_forget_closes_the_phones_socket_at_once_and_its_token_is_dead(fake_repo):
    server, task = await _serve(fake_repo)
    try:
        device_id, token = await _pair(server)
        await _pair(server, "Second phone")                          # another stays: the listener keeps listening
        auth = {"Authorization": f"Bearer {token}"}
        async with connect(_ws_url(server), ssl=_pinned(), additional_headers=auth) as ws:
            await asyncio.wait_for(ws.recv(), 5)
            left = server.host.command("phones.forget", {"id": device_id})
            assert [p["name"] for p in left["phones"]] == ["Second phone"] and left["listening"]
            with pytest.raises(ConnectionClosed) as e:
                await asyncio.wait_for(ws.recv(), 5)
            assert e.value.rcvd.code == 1008
        with pytest.raises(InvalidStatus):
            async with connect(_ws_url(server), ssl=_pinned(), additional_headers=auth):
                pass
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)


@pytest.mark.asyncio
async def test_pairing_locks_after_five_wrong_codes_and_says_so_on_the_desktop(fake_repo):
    server, task = await _serve(fake_repo)
    toasts = []
    server.host.on_toast = toasts.append
    try:
        offer = server.host.command("phones.pair")
        await _listening(server)
        address = offer["address"]
        for _ in range(5):
            status, body, _ = await asyncio.to_thread(_https, address, "POST", "/api/pair", {"code": "guess", "name": "x"})
            assert status == 403
        status, body, _ = await asyncio.to_thread(_https, address, "POST", "/api/pair", {"code": offer["code"], "name": "x"})
        assert status == 429 and "locked" in body["error"]
        assert any("Too many pairing attempts" in t["message"] for t in toasts)
        fresh = server.host.command("phones.pair")
        status, _, _ = await asyncio.to_thread(_https, address, "POST", "/api/pair", {"code": fresh["code"], "name": "x"})
        assert status == 200
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)


@pytest.mark.asyncio
async def test_two_get_requests_on_one_connection_both_answered_keep_alive(fake_repo):
    server, task = await _serve(fake_repo)
    try:
        offer = server.host.command("phones.pair")
        await _listening(server)
        def run():
            host, port = offer["address"].removeprefix("https://").rsplit(":", 1)
            conn = http.client.HTTPSConnection(host, int(port), context=_pinned(), timeout=5)
            try:
                conn.request("GET", "/app/")
                r1 = conn.getresponse()
                assert r1.status == 200
                assert r1.getheader("Connection", "").lower() == "keep-alive"
                body1 = r1.read()
                assert b"Orkboard" in body1

                conn.request("GET", "/app/frame.js")
                r2 = conn.getresponse()
                assert r2.status == 200
                assert r2.getheader("Connection", "").lower() == "keep-alive"
                body2 = r2.read()
                assert len(body2) > 0
            finally:
                conn.close()
        await asyncio.to_thread(run)
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)




# -- spec 42 C: a phone's Web Push subscription ---------------------------------------------------------------

_PUSH = {"endpoint": "https://push.example.com/send/abc", "p256dh": "BCVxsr7N_eNgVRqvHtD0", "auth": "BTBZMqHH6r4T", "at": "2026-10-01T10:00:00",
         "morning": "2026-10-19"}






def test_a_subscription_is_kept_with_the_device_and_forgotten_with_it(tmp_path):
    p = pairing.Pairing(tmp_path / "settings.json")
    device_id, _token, _name = p.add("Pixel")
    assert p.set_push(device_id, _PUSH) and p.get(device_id)["push"] == _PUSH
    assert "push" not in p.public()[0] and not p.set_push(device_id, {**_PUSH, "endpoint": "nope"}) and p.set_push(device_id, None)
    assert "push" not in p.get(device_id)
    p.set_push(device_id, _PUSH)
    assert p.forget(device_id) and p.get(device_id) is None and not p.set_push(device_id, _PUSH)



@pytest.mark.asyncio
async def test_a_phone_with_its_socket_open_is_known_and_its_push_commands_carry_its_own_id(fake_repo):
    server, task = await _serve(fake_repo)
    try:
        device_id, token = await _pair(server)
        auth = {"Authorization": f"Bearer {token}"}
        assert server.phones.open_ids() == set()
        async with connect(_ws_url(server), ssl=_pinned(), additional_headers=auth) as ws:
            await asyncio.wait_for(ws.recv(), 5)
            assert server.phones.open_ids() == {device_id}

            async def cmd(i, name, args=None):
                await ws.send(json.dumps({"t": "cmd", "id": i, "name": name, "args": args or {}}))
                while True:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), 5))
                    if msg["t"] == "reply" and msg["id"] == i:
                        return msg
            got = await cmd(1, "mobile.push_on", {"endpoint": _PUSH["endpoint"], "p256dh": _PUSH["p256dh"], "auth": _PUSH["auth"], "device_id": "someone-else"})
            assert got["ok"] and got["result"]["ok"]
            assert server.phones.pairing.get(device_id)["push"]["endpoint"] == _PUSH["endpoint"]            # its own, not the one it named
            assert (await cmd(2, "mobile.push_off"))["ok"] and "push" not in server.phones.pairing.get(device_id)
        await asyncio.sleep(0.2)
        assert server.phones.open_ids() == set()
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)
