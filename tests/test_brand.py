"""The product's name (orkboard/brand.py, decisions §95): Orkboard says Orkboard, on the page, on the phone's app and in its
commits and messages; there is no other product to say."""
from __future__ import annotations

from orkboard import brand
from orkboard.gui import pwa, server
from orkboard.realm import project_folder


def test_orkboard_names_itself():
    assert brand.name() == "Orkboard" and brand.board_author() == ("Orkboard board", "board@orkboard.local")
    assert brand.git_identity() == ["-c", "user.name=Orkboard", "-c", "user.email=orkboard@localhost"]
    page = (server.STATIC / "index.html").read_bytes()
    assert b"<title>Orkboard</title>" in page and b'data-product="Orkboard"' in page and b"Orkline" not in page
    for name in ("", "manifest.webmanifest", "sw.js"):
        body = pwa.serve("GET", f"/app/{name}")
        assert b"Orkline" not in body, name
    assert "Orkboard's own" in project_folder.refusal(pwa.ROOT.parents[3] / "orkboard")
