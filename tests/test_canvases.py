"""Canvases (docs/specs/78-canvases.md): the store (core/canvases.py), the cards and their commands (gui/ideas_canvases.py).
The tools' readers (sources/canvases.py §1) and the hook (hooks/canvas.py §5) have their tests below these."""
from __future__ import annotations

import base64
import json
import sys

import pytest

from orkboard.core import canvases as store_mod
from orkboard.core.canvases import KEEP, MADE, SEEN, Canvases
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, lexicon
from orkboard.sources.canvases import Canvas, link_host

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


def test_seen_folds_it_survives_a_restart_and_a_drawing_again_makes_it_new(tmp_path):
    s = Canvases(tmp_path)
    s.add(_c("2026-10-25T10:00:00+00:00"))
    rev = s.rev
    assert s.seen(f"claude:{ART}") and s.rev > rev and not s.seen("claude:https://claude.ai/artifact/none")
    again = Canvases(tmp_path)
    assert again.shown()[0] == [] and [c.key for c in again.shown()[1]] == [f"claude:{ART}"]
    again.add(_c("2099-01-01T00:00:00+00:00"))
    assert [c.key for c in Canvases(tmp_path).shown()[0]] == [f"claude:{ART}"]


def test_the_hooks_lines_are_read_when_the_file_changes(tmp_path):
    s = Canvases(tmp_path)
    assert s.new_count() == 0
    p = store_mod.path(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = _c("2026-10-25T10:00:00+00:00", tool="agy", kind="picture", url="", file=str(tmp_path / "a.png")).line()
    p.write_text(json.dumps(line) + "\nnot json\n" + json.dumps({"tool": "nope"}) + "\n", encoding="utf-8")
    assert s.new_count() == 1 and s.shown()[0][0].tool == "agy"


def test_the_store_keeps_the_last_canvases_only(tmp_path):
    s = Canvases(tmp_path)
    for i in range(KEEP + 5):
        s.add(_c(f"2026-10-25T10:{i // 60:02d}:{i % 60:02d}+00:00", url=f"https://claude.ai/artifact/{i}"))
    new, _ = Canvases(tmp_path).shown()
    assert len(new) == KEEP and new[-1].url.endswith("/5")


def test_a_line_that_is_no_canvas_is_none():
    assert Canvas.from_line({"key": "x", "seen": "now"}) is None
    assert Canvas.from_line({"tool": "claude", "kind": "design", "url": "http://claude.ai/a"}) is None   # not https, no file
    assert Canvas.from_line({"tool": "claude", "kind": "drawing", "url": ART}) is None


def test_only_the_allowed_hosts_are_links():
    assert link_host(ART) == "claude.ai" and link_host("https://www.figma.com/design/k/x") == "figma.com"
    assert link_host("http://claude.ai/a") == "" and link_host("https://claude.ai.evil.com/a") == ""
    assert link_host("https://evil.com/claude.ai") == "" and link_host("not a url") == ""


# -- the words (§2.4) and the log ---------------------------------------------------------------------------------

def test_canvas_is_a_word_of_the_glossary_and_its_events_are_logged():
    assert lexicon.term("canvas") == "canvas" and lexicon.term("canvas", many=True) == "canvases"
    assert {event_log.CANVAS_MADE, event_log.CANVAS_SEEN} <= set(event_log.EVENTS)


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
    assert host.snapshot()["canvases_new"] == 2
    host.command("ideas.canvas_seen", {"key": second["key"]})
    got = host.command("ideas.canvases")
    assert [c["key"] for c in got["seen"]] == [second["key"]] and host.snapshot()["canvases_new"] == 1
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


def test_the_phone_may_call_the_canvas_commands(host):
    from orkboard.gui.board_host import BoardPhone
    for name in ("ideas.canvases", "ideas.canvas_seen", "ideas.canvas_file"):
        assert BoardPhone.allowed(host, name, {})
    assert SEEN == "canvas.seen"


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


def test_a_doc_a_figma_file_and_a_picture_are_canvases():
    doc = from_call("claude", "mcp__Claude_Docs__batch", {"container": {"kind": "project", "create": {"name": "Plan"}}},
                    {"ack": f"made {ART}"}, AT)
    assert (doc.kind, doc.title, doc.url) == ("document", "Plan", ART)
    assert from_call("claude", "mcp__Claude_Docs__batch", {"container": {"id": "x"}}, ART, AT) is None
    fig = from_call("codex", "mcp__figma__create_new_file", {"fileName": "Board"}, "https://www.figma.com/design/K/Board.", AT)
    assert (fig.tool, fig.kind, fig.url) == ("codex", "design", "https://www.figma.com/design/K/Board")
    assert from_call("claude", "mcp__Figma__get_screenshot", {}, "https://www.figma.com/design/K", AT) is None
    assert from_call("codex", "mcp__tldraw__create", {}, "https://evil.com/x", AT) is None
    pic = from_call("agy", "generate_image", {"Prompt": "a pixel elf\nsmall"}, "Saved to /home/u/.gemini/brain/c1/elf.png", AT)
    assert (pic.kind, pic.title, pic.file) == ("picture", "a pixel elf", "/home/u/.gemini/brain/c1/elf.png")
    assert from_call("claude", "Bash", {"command": "ls"}, "", AT) is None


def test_a_canvas_says_its_time_in_one_spelling():
    """The store compares `at` as text: `…Z`, `…+00:00`, a fraction and another offset all read as one UTC spelling."""
    from orkboard.sources.canvases import norm_at
    assert _c("2026-10-25T10:00:00.123Z").at == "2026-10-25T10:00:00+00:00" == norm_at("2026-10-25T12:00:00+02:00")
    assert norm_at("not a time") == "not a time"
