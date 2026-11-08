"""Spec 162 E: the chronicle's search kept to one deck (realm/chronicle_find.py `find` with a deck's id): only that deck's goals and decisions, every word in an item found, every deck without an id."""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import chronicle_find
from tests.test_ideas_chronicle import host, tag, through  # noqa: F401  (the fixture and helpers)


def _find(host, query, **kw):
    h = host.ideas
    return chronicle_find.find(h.state_dir, Path(h.root(make=False)), Path(host.repo_root), h.keeper._log_text(), query, **kw)


def test_a_deck_alone_is_searched_and_every_word_must_be_in_an_item(host, fake_repo):
    tag(fake_repo, "v0.1", "2026-10-10")
    tag(fake_repo, "v0.2", "2026-10-20")
    a = through(host, "Purple buttons", "2026-10-05", 1)
    b = through(host, "Purple pages", "2026-10-15")
    c = through(host, "Purple next", "2026-10-25")
    assert _find(host, "purple")["found"] >= 3
    got = _find(host, "purple", deck="v:v0.2")
    assert [ch["id"] for ch in got["chapters"]] == ["v:v0.2"] and [g["idea"] for g in got["chapters"][0]["goals"]] == [b] and got["unreleased"] is None
    assert [g["idea"] for g in _find(host, "purple", deck="unreleased")["unreleased"]["goals"]] == [c]
    assert _find(host, "purple pages", deck="v:v0.1")["found"] == 0
    assert _find(host, "purple buttons", deck="v:v0.1")["found"] == 1 and a
    assert _find(host, "purple pink", deck="v:v0.1")["found"] == 0
    assert _find(host, "purple", deck="v:gone")["found"] == 0
