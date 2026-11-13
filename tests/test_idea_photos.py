"""A goal's first photo as its card's picture (docs/specs/148-a-window-on-every-card.md part A): `idea_photos.first` and `thumb`, the host's `picture` on a goal's node (`MapMixin.pictures_for`), and the signed route
`/media/_photo/<goal>/<file>` (gui/media.py): the first photo only, nothing outside the goal's photos folder."""
from __future__ import annotations

from pathlib import Path

import pytest

from orkboard.gui import media
from orkboard.realm import idea_photos

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture
def state(tmp_path: Path) -> Path:
    s = tmp_path / "project" / ".orkcraft"
    s.mkdir(parents=True)
    return s


def test_a_photo_over_the_size_gives_no_picture_and_one_at_it_gives_one(state):
    idea_photos.put(state, "big", JPEG + b"\x00" * idea_photos.THUMB_BYTES)
    assert idea_photos.thumb(state, "big") is None, "larger than 200 KB and no image Pillow can read: the card keeps its words"
    idea_photos.put(state, "edge", JPEG + b"\x00" * (idea_photos.THUMB_BYTES - len(JPEG)))
    assert idea_photos.thumb(state, "edge").stat().st_size == idea_photos.THUMB_BYTES


def test_a_goal_node_carries_picture_with_a_photo_and_none_without(state):
    from orkboard.gui.ideas_map import MapMixin

    class Stub(MapMixin):
        state_dir = state

    idea_photos.put(state, "with", JPEG)
    got = {"nodes": [{"slug": "with"}, {"slug": "without"}]}
    Stub().pictures_for(got)
    assert got["nodes"][0]["picture"].startswith("/media/_photo/with/1.jpg?s=") and "picture" not in got["nodes"][1]


def get(state: Path, target: str):
    return media.serve("GET", target, "", [state])


def test_the_route_serves_the_first_photo_signed_and_refuses_the_rest(state):
    idea_photos.put(state, "dark-mode", JPEG)
    idea_photos.put(state, "dark-mode", PNG)
    ok = get(state, media.photo_url("dark-mode", "1.jpg"))
    assert ok.status == 200 and ok.read() == JPEG and dict(ok.headers)["Content-Type"] == "image/jpeg"
    assert dict(ok.headers)["X-Content-Type-Options"] == "nosniff"
    path, sig = media.photo_url("dark-mode", "1.jpg").split("?s=")
    assert get(state, path).status == 404, "unsigned"
    assert get(state, f"{path}?s={sig[:-1]}{'0' if sig[-1] != '0' else '1'}").status == 404, "a wrong signature"
    assert get(state, media.photo_url("dark-mode", "2.png")).status == 404, "the second photo is no card's picture"
    assert get(state, media.photo_url("other", "1.jpg")).status == 404, "another goal's"
    for bad in ("../1.jpg", "..", "1.jpg/x", "%2e%2e%2f1.jpg", "1.thumbs.jpg", "1.thumb.svg", ".hidden", "1.svg"):
        assert media.parse_photo(f"/media/_photo/dark-mode/{bad}") is None
    assert media.parse_photo("/media/_photo/../1.jpg") is None and media.parse_photo("/media/_photo/Dark/1.jpg") is None
    assert media.parse_photo("/media/_photo/dark-mode/1.jpg") is not None and media.parse_photo("/media/_photo/dark-mode/1.thumb.jpg") is not None


# -- the small copy (spec 148 A.2, Pillow a dependency) ------------------------------------------------------------------

def _image(w: int, h: int, mode: str = "RGB", fmt: str = "JPEG") -> bytes:
    import io

    from PIL import Image
    img = Image.new(mode, (w, h), (200, 80, 40, 128) if mode == "RGBA" else (200, 80, 40))
    for x in range(0, w, 7):                                    # something to compress, not one flat colour
        img.putpixel((x, (x * 3) % h), (10, 200, 90, 255) if mode == "RGBA" else (10, 200, 90))
    out = io.BytesIO()
    img.save(out, fmt)
    return out.getvalue()


def test_a_large_photo_is_shown_as_a_copy_of_at_most_320_px_made_once_beside_it(state):
    from PIL import Image
    idea_photos.put(state, "big", _image(1600, 900))
    shown = idea_photos.thumb(state, "big")
    assert shown.name == "1.thumb.jpg" and shown.parent == idea_photos.folder(state, "big")
    with Image.open(shown) as img:
        assert img.size == (320, 180) and img.format == "JPEG"
    made = shown.stat().st_mtime_ns
    assert idea_photos.thumb(state, "big").stat().st_mtime_ns == made, "made once, then kept"
    assert idea_photos.listed(state, "big") == [".orkcraft/ideas/big/photos/1.jpg"], "the copy is no photo of the goal's"
    ok = get(state, media.photo_url("big", "1.thumb.jpg"))
    assert ok.status == 200 and dict(ok.headers)["Content-Type"] == "image/jpeg" and ok.read() == shown.read_bytes()
    assert get(state, media.photo_url("big", "1.jpg")).status == 404, "the photo itself is not served once a copy is shown"


def test_a_small_picture_is_shown_as_it_is_a_sprite_keeps_its_pixels(state):
    idea_photos.put(state, "coin", _image(16, 16, fmt="PNG"))
    assert idea_photos.thumb(state, "coin").name == "1.png" and not list(idea_photos.folder(state, "coin").glob("*.thumb.*"))


def test_a_goal_node_carries_its_copys_address(state):
    from orkboard.gui.ideas_map import MapMixin

    class Stub(MapMixin):
        state_dir = state

    idea_photos.put(state, "with", _image(1200, 800))
    got = {"nodes": [{"slug": "with"}]}
    Stub().pictures_for(got)
    assert got["nodes"][0]["picture"].startswith("/media/_photo/with/1.thumb.jpg?s=")
