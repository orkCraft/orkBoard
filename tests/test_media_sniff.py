"""Spec 121 A (docs/specs/121-the-day-the-morning-and-the-night.md §2.4): a sketch's page is sniffed by its bytes as `text/html`, never by its name; the other types keep their sniffing
(tests/test_idea_pick.py)."""
from __future__ import annotations

import pytest

from orkboard.realm import media_sniff
from tests import pick_files as pf

PAGE = b"<!doctype html><html><body><button>Press</button></body></html>"


@pytest.mark.parametrize("data", [
    PAGE, b"<!DOCTYPE HTML>\n<html></html>", b"<html lang=en><body></body></html>", b"<HTML>\n<body>x</body></HTML>", b"\xef\xbb\xbf<!doctype html><p>x</p>",
    b"  \n\t<!doctype html>\n<title>t</title>", b"<!-- a sketch -->\n<!doctype html><title>t</title>", b"<!-- one --><!-- two -->\n<html></html>",
])
def test_a_page_is_html_by_its_bytes(tmp_path, data):
    assert media_sniff.sniff(pf.write(tmp_path, "whatever.bin", data)) == "text/html"


def test_a_page_is_html_whatever_its_name_says(tmp_path):
    assert media_sniff.sniff(pf.write(tmp_path, "logo.png", PAGE)) == "text/html"            # a page called a picture
    assert media_sniff.sniff(pf.write(tmp_path, "page.html", pf.text("just words"))) == "text/plain"      # words called a page


@pytest.mark.parametrize("data", [
    b"<div>a fragment is no page</div>", b"<b>bold</b>", b"A note that says <html> in the middle", b"<!doctypehtml>", b"<htmlish></htmlish>", b"# <html>\n", b"<style>x{}</style><html></html>",
])
def test_a_text_that_is_not_a_page_stays_a_text(tmp_path, data):
    assert media_sniff.sniff(pf.write(tmp_path, "a.html", data)) == "text/plain"


def test_a_page_with_a_control_character_or_cut_in_a_character_is_not_text_at_all(tmp_path):
    assert media_sniff.sniff(pf.write(tmp_path, "a.html", PAGE + b"\x00")) is None
    assert media_sniff.sniff(pf.write(tmp_path, "b.html", b"<!doctype html>\x07")) is None
    assert media_sniff.sniff(pf.write(tmp_path, "c.html", b"<!doctype html>\xff\xfe")) is None


def test_the_other_types_are_unchanged_and_a_page_has_no_size(tmp_path):
    assert media_sniff.sniff(pf.write(tmp_path, "a.svg", pf.svg())) == "image/svg+xml"
    assert media_sniff.sniff(pf.write(tmp_path, "b.svg", b"<?xml version='1.0'?><svg viewBox='0 0 1 1'/>")) == "image/svg+xml"
    assert media_sniff.sniff(pf.write(tmp_path, "a.png", pf.png())) == "image/png"
    assert media_sniff.measure(pf.write(tmp_path, "p.html", PAGE), "text/html") == {"w": None, "h": None, "seconds": None}


def test_a_long_page_is_sniffed_from_its_start(tmp_path):
    big = b"<!doctype html><body>" + b"<p>caf\xc3\xa9</p>" * 20_000
    assert media_sniff.sniff(pf.write(tmp_path, "big.html", big)) == "text/html"
