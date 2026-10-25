"""The product's name (orkboard/brand.py, decisions §91): Orkboard says Orkboard; where Orkline runs the same modules
(its orkGet profile bound) the page, the phone's app and the messages say Orkline, never the other product."""
from __future__ import annotations

import pytest

from orkboard import brand
from orkboard.gui import pwa, server
from orkboard.orkget import profile
from orkboard.realm import project_folder


def test_orkboard_names_itself():
    assert brand.name() == "Orkboard"
    page = server.named((server.STATIC / "index.html").read_bytes())
    assert b"<title>Orkboard</title>" in page and b'data-product="Orkboard"' in page and b"Orkline" not in page


@pytest.fixture
def orkline(monkeypatch):
    monkeypatch.setattr(profile, "_current", profile.Profile(product="orkline", name="Orkline", package="orkcraft",
                                                             version="0", agent="orkline", manifest="", source=""))


def test_where_orkline_runs_them_everything_says_orkline(orkline):
    assert brand.name() == "Orkline"
    page = server.named((server.STATIC / "index.html").read_bytes())
    assert b"<title>Orkline</title>" in page and b'data-product="Orkline"' in page and b"Orkboard" not in page
    for name in ("", "manifest.webmanifest", "sw.js"):
        body = pwa.serve("GET", f"/app/{name}")
        assert b"Orkline" in body and b"Orkboard" not in body, name
    assert "Orkline's own" in project_folder.refusal(pwa.ROOT.parents[3] / "orkboard")
