"""Canvases (docs/specs/78-canvases.md): the store (core/canvases.py), the cards and their commands (gui/ideas_canvases.py).
The tools' readers (sources/canvases.py §1) and the hook (hooks/canvas.py §5) have their tests below these."""
from __future__ import annotations

import base64
import json
import sys

import pytest

from orkboard.core import canvases as store_mod
from orkboard.core.canvases import MADE, Canvases
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.sources.canvases import Canvas

ART = "https://claude.ai/artifact/0f3c"


def _c(at: str, url: str = ART, **kw) -> Canvas:
    return Canvas(kw.pop("tool", "claude"), kw.pop("kind", "design"), kw.pop("title", "Onboarding"), at, url=url, **kw)


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


# -- the store (§2) -----------------------------------------------------------------------------------------------

def test_a_canvas_is_kept_told_and_drawn_again_is_one_card_moved(tmp_path):
    told = []
    s = Canvases(tmp_path, lambda topic, **d: told.append((topic, d)))
    assert s.add(_c("2026-10-25T10:00:00+00:00")) and not s.add(_c("2026-10-25T10:00:00+00:00"))
    assert s.add(_c("2026-10-25T11:00:00+00:00", title="Onboarding, v2"))
    new, seen = s.shown()
    assert [c.title for c in new] == ["Onboarding, v2"] and seen == []
    assert [t for t, _ in told] == [MADE, MADE] and told[0][1]["key"] == f"claude:{ART}"
    assert store_mod.path(tmp_path).is_file()


# -- the words (§2.4) and the log ---------------------------------------------------------------------------------

# -- the cards and their commands (§3) ----------------------------------------------------------------------------

def test_the_cards_their_head_and_seen(host, fake_repo):
    store = host.ideas.canvas_store
    store.add(_c("2026-10-25T10:00:00+00:00", model="claude-opus-5-5"))
    store.add(Canvas("codex", "picture", "A pixel elf", "2026-10-25T11:00:00+00:00", url="https://evil.com/x"))
    got = host.command("ideas.canvases")
    json.dumps(got)
    first, second = got["canvases"]
    assert (first["tool_word"], first["kind"], first["url"], first["link_text"]) == ("Codex", "picture", "", "https://evil.com/x")
    assert (second["host"], second["url"], second["head"]) == ("claude.ai", ART, {"craft": "design", "race": "elf", "tier": "elder"})
    assert first["head"]["race"] == "elf" and first["head"]["tier"] == "warrior"        # no model: warrior
    assert host.ideas.canvas_store.new_count() == 2
    host.command("ideas.canvas_seen", {"key": second["key"]})
    got = host.command("ideas.canvases")
    assert [c["key"] for c in got["seen"]] == [second["key"]] and host.ideas.canvas_store.new_count() == 1
    with pytest.raises(CommandError):
        host.command("ideas.canvas_seen", {"key": "claude:https://claude.ai/artifact/gone"})


def test_a_canvas_opens_only_on_an_allowed_host_and_never_from_the_phone(host, monkeypatch):
    import webbrowser
    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url) or True)
    store = host.ideas.canvas_store
    store.add(_c("2026-10-25T10:00:00+00:00"))
    store.add(_c("2026-10-25T10:00:01+00:00", url="https://evil.com/x"))
    host.command("ideas.canvas_open", {"key": f"claude:{ART}"})
    assert opened == [ART]
    for args in ({"key": "claude:https://evil.com/x"}, {"key": f"claude:{ART}", "device": "phone"}):
        with pytest.raises(CommandError):
            host.command("ideas.canvas_open", args)
    assert opened == [ART]


def test_a_local_file_shows_only_from_the_allowed_folders(host, fake_repo, tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    png = fake_repo / "design" / "elf.png"
    png.parent.mkdir()
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    page = fake_repo / "design" / "page.html"
    page.write_text("<h1>Hi</h1>", encoding="utf-8")
    outside = tmp_path / "secret.png"
    outside.write_bytes(b"\x89PNG")
    pic = tmp_path / "codex" / "generated_images" / "s1" / "c1.png"
    pic.parent.mkdir(parents=True)
    pic.write_bytes(b"\x89PNG")
    store = host.ideas.canvas_store
    for i, f in enumerate((png, page, outside, pic)):
        store.add(Canvas("codex", "picture", f.name, f"2026-10-25T10:00:0{i}+00:00", file=str(f)))
    cards = {c["title"]: c for c in host.command("ideas.canvases")["canvases"]}
    assert {t for t, c in cards.items() if c["local"]} == {"elf.png", "page.html", "c1.png"}
    got = host.command("ideas.canvas_file", {"key": cards["elf.png"]["key"]})
    assert got["mime"] == "image/png" and base64.b64decode(got["data"]).startswith(b"\x89PNG")
    assert host.command("ideas.canvas_file", {"key": cards["page.html"]["key"]})["text"] == "<h1>Hi</h1>"
    with pytest.raises(CommandError):
        host.command("ideas.canvas_file", {"key": cards["secret.png"]["key"]})


# -- one tool call as a canvas (sources/canvases.py `from_call`: the readers' and the hook's) -----------------------

from orkboard.sources.canvases import from_call  # noqa: E402

AT = "2026-10-25T10:00:00+00:00"


def test_an_artifact_published_is_a_canvas_and_a_read_or_an_asset_is_not():
    said = [{"type": "text", "text": f"Published: {ART}\nThis session watches it."}]
    c = from_call("claude", "Artifact", {"file_path": "/home/u/p/onboarding.html", "icon": "chart"}, said, AT, "s1", "claude-opus-5-5")
    assert (c.kind, c.title, c.url, c.file, c.session) == ("page", "onboarding", ART, "/home/u/p/onboarding.html", "s1")
    d = from_call("claude", "Artifact", {"type_url": "https://claude.ai/artifact/types/design", "title": "Login"}, ART, AT)
    assert (d.kind, d.title, d.file) == ("design", "Login", "")
    assert from_call("claude", "Artifact", {"type_url": "x/slides"}, ART, AT).kind == "slides"
    assert from_call("claude", "Artifact", {"action": "read", "url": ART}, "<html>", AT) is None
    assert from_call("claude", "Artifact", {"asset": True, "url": ART, "file_path": "/a.png"}, ART, AT) is None
    assert from_call("claude", "Artifact", {"file_path": "a.html"}, "refused", AT) is None

