"""The paid makers run on fake transports; a missing fake fails before networking."""
import base64
import http.client
import json
import socket
from dataclasses import replace

import pytest

from orkboard.core import craft_run as run
from orkboard.realm import idea_pick
from tests import pick_files as pf


@pytest.fixture(autouse=True)
def fake_keys(monkeypatch):
    monkeypatch.setattr(run.craft_tools, "key", lambda tool: "test-only-credential")


def picture(data=None):
    return run.Response(200, "application/json", json.dumps({"data": [
        {"b64_json": base64.b64encode(pf.png() if data is None else data).decode()}
    ]}).encode())


@pytest.mark.parametrize("maker,answer,host,path,auth", [
    (run.PictureMaker, picture(), "api.openai.com", "/v1/images/generations", "Authorization"),
    (run.SoundMaker, run.Response(200, "audio/mpeg", pf.mp3()), "api.elevenlabs.io", "/v1/sound-generation", "xi-api-key"),
])
def test_each_maker_uses_fake_transport_fixed_endpoint_timeout_and_request_time_key(
        tmp_path, monkeypatch, maker, answer, host, path, auth):
    calls, keys = [], []
    monkeypatch.setattr(run.craft_tools, "key", lambda tool: keys.append(tool) or "test-only-credential")

    def fake(**kwargs):
        calls.append(kwargs)
        return answer

    tool = maker(fake)
    assert keys == []
    files = tool.make("A small asset", tmp_path / "assets", count=2)
    assert len(files) == len(calls) == len(keys) == 2
    assert all(p.is_file() for p in files)
    for call in calls:
        assert call["host"] == host and call["path"] == path
        assert call["timeout"] == run.TIMEOUT > 0 and call["limit"] > 0
        assert "test-only-credential" in call["headers"][auth]
        assert "A small asset" in json.loads(call["body"]).values()
        assert b"test-only-credential" not in call["body"]


@pytest.mark.parametrize("maker,answer,why", [
    (run.PictureMaker, picture(pf.wav()), "stated type"),
    (run.PictureMaker, run.Response(200, "text/html", b"bad"), "JSON answer"),
    (run.PictureMaker, run.Response(200, "application/json", b'{"data":[{"url":"https://other.example/a.png"}]}'), "base64 picture"),
    (run.PictureMaker, run.Response(200, "application/json", b'{"data":[{"b64_json":"!!!"}]}'), "base64 picture"),
    (run.SoundMaker, run.Response(200, "audio/mpeg", pf.png()), "stated type"),
    (run.SoundMaker, run.Response(200, "audio/wav", pf.mp3()), "stated type"),
    (run.SoundMaker, run.Response(200, "text/plain", b"bad"), "sound"),
    (run.PictureMaker, run.Response(302, "text/plain", b"secret"), "HTTP 302"),
    (run.SoundMaker, run.Response(401, "text/plain", b"secret"), "HTTP 401"),
])
def test_invalid_answers_fail_in_words_and_remove_files(tmp_path, maker, answer, why):
    destination = tmp_path / "assets"
    with pytest.raises(run.MakerError, match=why) as error:
        maker(lambda **kwargs: answer).make("prompt", destination)
    assert run.craft_tools.get(maker.tool_id).maker in str(error.value)
    assert "secret" not in str(error.value)
    assert not destination.exists()


@pytest.mark.parametrize("maker,good,kind", [
    (run.PictureMaker, picture(), "image"),
    (run.SoundMaker, run.Response(200, "audio/mpeg", pf.mp3()), "audio"),
])
def test_per_file_and_whole_pick_limits_remove_earlier_variants(tmp_path, monkeypatch, maker, good, kind):
    size = len(pf.png() if kind == "image" else pf.mp3())
    monkeypatch.setitem(idea_pick.KINDS, kind, replace(idea_pick.KINDS[kind], limit=size - 1))
    with pytest.raises(run.MakerError, match="at most|too large"):
        maker(lambda **kw: good).make("prompt", tmp_path / "assets")
    assert not (tmp_path / "assets").exists()
    monkeypatch.setitem(idea_pick.KINDS, kind, replace(idea_pick.KINDS[kind], limit=size))
    monkeypatch.setattr(idea_pick, "PICK_MAX", size)
    with pytest.raises(run.MakerError, match="pick is at most"):
        maker(lambda **kw: good).make("prompt", tmp_path / "assets", count=2)
    assert not (tmp_path / "assets").exists()


def test_timeout_after_an_asset_removes_all_output_and_hides_provider_text(tmp_path):
    calls = []

    def fake(**kw):
        if calls:
            raise TimeoutError("test-only-credential")
        calls.append(kw)
        return picture()

    with pytest.raises(run.MakerError, match="timed out") as error:
        run.PictureMaker(fake).make("prompt", tmp_path / "assets", count=2)
    assert "credential" not in str(error.value)
    assert not (tmp_path / "assets").exists()


def test_missing_key_never_calls_transport(tmp_path, monkeypatch):
    monkeypatch.setattr(run.craft_tools, "key", lambda tool: None)
    with pytest.raises(run.MakerError, match="no key"):
        run.SoundMaker(lambda **kw: pytest.fail("transport called")).make("prompt", tmp_path / "assets")
    assert not (tmp_path / "assets").exists()


@pytest.mark.parametrize('maker,payload', [
    (run.PictureMaker, {'prompt': 'picture'}),
    (run.SoundMaker, {'duration_seconds': 5}),
])
def test_pre_transport_refusal_never_reserves(tmp_path, monkeypatch, maker, payload):
    from orkboard.core.craft_spend import Spend
    spend = Spend(tmp_path, 'goal', 'k1', maker.tool_id,
                  {'amount': '1', 'currency': 'USD'})
    tool = maker(lambda **kw: pytest.fail('transport called'), spend=spend)
    monkeypatch.setattr(run.craft_tools, 'key', lambda _: None)
    with pytest.raises(run.MakerError, match='no key on this computer'):
        tool._request(payload)
    assert not spend.path.exists()
    monkeypatch.setattr(run.craft_tools, 'key', lambda _: 'fake-key')
    with pytest.raises(TypeError):
        tool._request({**payload, 'invalid': object()})
    assert not spend.path.exists()


@pytest.mark.parametrize("host", ["api.openai.com", "api.elevenlabs.io"])
def test_real_maker_endpoint_fails_the_gate_before_network(tmp_path, host):
    maker = run.PictureMaker if host == "api.openai.com" else run.SoundMaker
    with pytest.raises(pytest.fail.Exception, match="paid tool host"):
        maker().make("prompt", tmp_path / "assets")
    assert not (tmp_path / "assets").exists()
    with pytest.raises(pytest.fail.Exception, match="paid tool host"):
        socket.getaddrinfo(host.upper() + ".", 443)
    with socket.socket() as sock:
        with pytest.raises(pytest.fail.Exception, match="paid tool host"):
            sock.connect((host, 443))


def test_guard_allows_localhost_http_and_dns(monkeypatch):
    # Sandbox forbids binding sockets. Stop at the HTTP send seam, beneath the
    # guard, to prove localhost requests still reach the normal HTTP machinery.
    sent = []
    monkeypatch.setattr(http.client.HTTPConnection, "_send_output",
                        lambda self, *a, **kw: sent.append(self.host))
    connection = http.client.HTTPConnection("localhost", 12345, timeout=2)
    connection.request("GET", "/")
    assert sent == ["localhost"]
    assert socket.getaddrinfo("localhost", 12345)



def test_https_transport_is_bounded_closes_and_never_follows_redirects(monkeypatch):
    events = []

    class Connection:
        def __init__(self, host, timeout):
            events.append((host, timeout))

        def request(self, *args, **kwargs):
            events.append(args)

        def getresponse(self):
            return self

        status = 302

        def getheader(self, name, default):
            return "application/json; charset=utf-8"

        def read(self, limit):
            events.append(limit)
            return b"x" * limit

        def close(self):
            events.append("closed")

    monkeypatch.setattr(run.http.client, "HTTPSConnection", Connection)
    with pytest.raises(run.MakerError, match="too large"):
        run.https_transport(host="api.openai.com", path="/v1/images/generations", headers={},
                            body=b"{}", timeout=3, limit=10)
    assert events == [("api.openai.com", 3), ("POST", "/v1/images/generations"), 11, "closed"]
    with pytest.raises(run.MakerError, match="endpoint"):
        run.https_transport(host="other.example", path="/v1/else", headers={}, body=b"", timeout=3, limit=10)


@pytest.mark.parametrize("mime,data", [
    ("audio/mpeg", pf.mp3()), ("audio/wav", pf.wav()),
    ("audio/ogg", pf.ogg()), ("audio/mp4", pf.mp4(b"soun")),
])
def test_sound_accepts_the_picks_audio_types(tmp_path, mime, data):
    files = run.SoundMaker(lambda **kw: run.Response(200, mime, data)).make("sound", tmp_path / "assets")
    assert files[0].read_bytes() == data
    assert files[0].suffix == "." + idea_pick.EXT[mime]


def test_existing_assets_are_never_removed(tmp_path):
    folder = tmp_path / "assets"
    folder.mkdir()
    kept = folder / "kept.txt"
    kept.write_text("earlier work")
    with pytest.raises(FileExistsError):
        run.PictureMaker(lambda **kw: pytest.fail("request sent")).make("picture", folder)
    assert kept.read_text() == "earlier work"


@pytest.mark.parametrize("count", [0, 7, True, 1.5])
def test_invalid_count_never_sends_or_writes(tmp_path, count):
    with pytest.raises(run.MakerError, match="between one and six"):
        run.PictureMaker(lambda **kw: pytest.fail("request sent")).make("picture", tmp_path / "assets", count=count)
    assert not (tmp_path / "assets").exists()
