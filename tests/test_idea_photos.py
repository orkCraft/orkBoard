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


def test_first_is_the_first_photo_in_the_order_they_came_and_empty_with_none(state):
    assert idea_photos.first(state, "dark-mode") == "" and idea_photos.thumb(state, "dark-mode") is None
    idea_photos.put(state, "dark-mode", JPEG)
    idea_photos.put(state, "dark-mode", PNG)
    assert idea_photos.first(state, "dark-mode") == ".orkcraft/ideas/dark-mode/photos/1.jpg"
    assert idea_photos.thumb(state, "dark-mode") == state / "ideas" / "dark-mode" / "photos" / "1.jpg"
    assert idea_photos.first(state, "other") == ""


def test_a_photo_over_the_size_gives_no_picture_and_one_at_it_gives_one(state):
    idea_photos.put(state, "big", JPEG + b"\x00" * idea_photos.THUMB_BYTES)
    assert idea_photos.thumb(state, "big") is None, "larger than 200 KB: the card keeps its words (no Pillow to make a smaller copy)"
    idea_photos.put(state, "edge", JPEG + b"\x00" * (idea_photos.THUMB_BYTES - len(JPEG)))
    assert idea_photos.thumb(state, "edge").stat().st_size == idea_photos.THUMB_BYTES


def test_a_photo_that_is_a_link_out_of_the_folder_gives_no_picture(state, tmp_path):
    outside = tmp_path / "secret.jpg"
    outside.write_bytes(JPEG)
    where = idea_photos.folder(state, "linked")
    where.mkdir(parents=True)
    (where / "1.jpg").symlink_to(outside)
    assert idea_photos.first(state, "linked") and idea_photos.thumb(state, "linked") is None


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
    for bad in ("../1.jpg", "..", "1.jpg/x", "%2e%2e%2f1.jpg", "1.thumb.jpg", ".hidden", "1.svg"):
        assert media.parse_photo(f"/media/_photo/dark-mode/{bad}") is None
    assert media.parse_photo("/media/_photo/../1.jpg") is None and media.parse_photo("/media/_photo/Dark/1.jpg") is None
    assert media.parse_photo("/media/_photo/dark-mode/1.jpg") is not None


def test_a_signed_path_outside_the_state_is_refused(state, tmp_path):
    (tmp_path / "outside.jpg").write_bytes(JPEG)
    for target in ("/media/_photo/dark-mode/..%2F..%2F..%2Foutside.jpg", "/media/_photo/%2e%2e/1.jpg", "/media/_photo/dark-mode/../../x.jpg"):
        signed = target.split("?")[0]
        assert get(state, f"{signed}?s={media.sign(signed)}").status == 404
