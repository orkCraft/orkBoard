"""Stage A: a chair's tools and permissions, with no paid calls or real keys."""
import json
from dataclasses import replace

import pytest

from orkboard.realm import craft_tools as tools, ideas


@pytest.fixture
def art(tmp_path, monkeypatch):
    for name in ("OPENAI_API_KEY", "ELEVENLABS_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(tools.idea_secrets, "_keychain", lambda: None)
    slug = ideas.add_track(tmp_path, "Art and sound")
    page = ideas.track_page(tmp_path, slug)
    page.set("recipe", "art")
    page.set("tool", "codex")
    page.set("tools", '{"artist": "agy"}')
    page.set("extra", "keep me")
    ideas._write(tmp_path / ideas.TRACKS / f"{slug}.md", page.text())
    return tmp_path, slug


def test_chair_reports_missing_keys_then_here_without_exposing_keys(art, monkeypatch):
    root, party = art
    rows = tools.for_party(root, party, "codex")
    assert {r["id"] for r in rows} == {"openai-images", "elevenlabs-sound"}
    assert all(not r["here"] and r["why"] == "no key on this computer" for r in rows)
    assert all(not r["taken"] and r["cap"] is None for r in rows)
    monkeypatch.setenv("OPENAI_API_KEY", "fake-picture-credential")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake-sound-credential")
    rows = tools.for_party(root, party, "codex")
    assert all(r["here"] and r["why"] == "" for r in rows)
    assert "credential" not in json.dumps(rows)


def test_chair_reports_harness_and_unofficial_api_reasons(art, monkeypatch):
    root, party = art
    original = tools.REGISTRY["openai-images"]
    monkeypatch.setitem(tools.REGISTRY, original.id, replace(original, kind="code", key_env="", needs=("pictures",)))
    assert tools.for_party(root, party, "codex")[0]["why"] == "its harness cannot make it"
    assert tools.for_party(root, party, "missing")[0]["here"] is False
    assert tools.for_party(root, party, "agy")[0]["here"] is True
    monkeypatch.setitem(tools.REGISTRY, original.id, replace(original, official_api=False))
    assert tools.for_party(root, party, "agy")[0]["why"] == "no official API"


def test_keychain_account_precedence_and_environment_fallback(art, monkeypatch):
    calls = []

    class Keychain:
        def get_password(self, service, account):
            calls.append((service, account))
            return "fake-keychain-key"

    monkeypatch.setenv("OPENAI_API_KEY", "fake-environment-key")
    monkeypatch.setattr(tools.idea_secrets, "_keychain", lambda: Keychain())
    assert tools.key("openai-images") == "fake-keychain-key"
    assert calls == [("orkcraft-ideas", "tools/openai-images")]
    monkeypatch.setattr(Keychain, "get_password", lambda *a: None)
    assert tools.key("openai-images") == "fake-environment-key"

    def broken(*args):
        raise RuntimeError("unavailable")

    monkeypatch.setattr(Keychain, "get_password", broken)
    assert tools.key("openai-images") == "fake-environment-key"
    assert tools.key("unknown") is None


def test_taken_caps_roundtrip_and_clear_preserve_harness_and_page(art):
    root, party = art
    assert tools.taken(root, party) == {}
    before = ideas.track_page(root, party)
    chosen = {"openai-images": {"cap": {"amount": "1.20", "currency": "USD"}}}
    tools.set_taken(root, party, chosen)
    assert tools.taken(root, party) == chosen
    row = tools.for_party(root, party, "codex")[0]
    assert row["taken"] and row["cap"] == chosen["openai-images"]["cap"]
    after = ideas.track_page(root, party)
    assert after.sections == before.sections
    for name in ("tool", "tools", "extra"):
        assert after.get(name) == before.get(name)
    tools.set_taken(root, party, {})
    assert tools.taken(root, party) == {}


@pytest.mark.parametrize("amount", [None, True, "NaN", "Infinity", "-1", "0", "words"])
def test_invalid_cap_cannot_take_paid_tool(art, amount):
    root, party = art
    with pytest.raises(ValueError, match="cap"):
        tools.set_taken(root, party, {"openai-images": {"cap": {"amount": amount, "currency": "USD"}}})
    assert tools.taken(root, party) == {}


@pytest.mark.parametrize("raw", ["bad json", "[]", '{"unknown": {}}', '{"openai-images": {}}',
                                 '{"openai-images": {"cap": {"amount": "1", "currency": "EUR"}}}'])
def test_malformed_page_permissions_read_as_none(raw):
    assert tools.clean_taken(raw) == {}


def test_registry_is_art_only_official_dated_and_in_money(art):
    root, _ = art
    other = ideas.add_track(root, "Tech")
    assert tools.for_party(root, other, "codex") == []
    assert tools.for_party(root, "missing", "codex") == []
    for tool in tools.REGISTRY.values():
        assert tool.crafts == ("art",)
        assert tool.official_api and tool.kind == "api"
        assert tool.host in ("api.openai.com", "api.elevenlabs.io")
        assert tool.prices and tool.leaves
        assert all(p.currency == "USD" and p.dated == "2026-11-08" and p.source.startswith("https://") for p in tool.prices)
    with pytest.raises(ValueError, match="craft"):
        tools.set_taken(root, other, {"openai-images": {"cap": {"amount": "1", "currency": "USD"}}})
    with pytest.raises(ValueError, match="No party"):
        tools.set_taken(root, "missing", {})
