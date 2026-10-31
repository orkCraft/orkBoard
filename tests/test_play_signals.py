"""Spec 115 C (docs/specs/115-the-live-product-under-each-leaders-eyes.md §4; decisions §193): the hints of code from a play's probe events (`realm/play_signals.py`): each kind, what is no hint, the bounds,
the ring. Pure code, no model."""
from __future__ import annotations

import threading

from orkboard.realm import play_signals as ps

RECT = {"x": 10, "y": 20, "w": 80, "h": 30}


def _err(msg="x is undefined", at=1000, path="/today"):
    return {"kind": "error", "message": msg, "stack": "at f (app.js:1)", "path": path, "at": at}


def _req(path="/api/plants", status=200, ms=50, at=1000, method="GET"):
    return {"kind": "request", "method": method, "path": path, "status": status, "ms": ms, "at": at}


def _press(sel="button#water", at=1000, changed=True, pressable=True, path="/today"):
    return {"kind": "press", "selector": sel, "rect": RECT, "changed": changed, "pressable": pressable, "at": at, "path": path}


def _kinds(hs):
    return [h["kind"] for h in hs]


def test_an_error_is_a_hint_in_plain_words_with_no_element():
    assert ps.hints([_err()], "/today") == [{"kind": "error", "on": None, "words": "An error here: x is undefined", "at": 1000}]
    assert ps.hints([_err(path="/other")], "/today") == [], "an error of another page is not this page's"
    assert _kinds(ps.hints([_err(path="/other")], "")) == ["error"], "no path: all of the play"
    long = ps.hints([_err("e" * 500)], "/today")[0]["words"]
    assert long.startswith("An error here: ") and len(long) <= len("An error here: ") + ps.WORDS_MAX


def test_a_failed_request_is_5xx_or_4xx_but_a_401_and_a_404_asked_once():
    got = ps.hints([_req("/api/water", 500, method="POST")], "/today")
    assert got == [{"kind": "failed", "on": None, "words": "A request failed: POST /api/water 500", "at": 1000}]
    assert _kinds(ps.hints([_req("/api/x", 400)], "/")) == ["failed"] and _kinds(ps.hints([_req("/api/x", 403)], "/")) == ["failed"]
    assert ps.hints([_req("/api/me", 401)], "/") == [], "a sign-in is asked for: no hint"
    assert ps.hints([_req("/favicon.ico", 404)], "/") == [], "a 404 of a path asked once is a probe for a file"
    twice = ps.hints([_req("/api/gone", 404, at=1000), _req("/api/gone", 404, at=2000)], "/")
    assert _kinds(twice) == ["failed"] and twice[0]["words"] == "A request failed: GET /api/gone 404" and twice[0]["at"] == 2000
    assert ps.hints([_req("/api/ok", 200), _req("/api/redirect", 304), _req("/api/none", 0)], "/") == []


def test_a_slow_request_is_over_the_limit_and_the_limit_can_be_set():
    got = ps.hints([_req("/api/plants", ms=1840)], "/")
    assert got == [{"kind": "slow", "on": None, "words": "Slow: GET /api/plants 1840 ms", "at": 1000}]
    assert ps.hints([_req(ms=1000)], "/") == [], "over, not at"
    assert _kinds(ps.hints([_req(ms=1001)], "/")) == ["slow"]
    assert _kinds(ps.hints([_req(ms=300)], "/", slow_ms=200)) == ["slow"] and ps.hints([_req(ms=1840)], "/", slow_ms=2000) == []
    both = ps.hints([_req("/api/x", 500, ms=3000)], "/")
    assert sorted(_kinds(both)) == ["failed", "slow"]


def test_a_dead_press_is_on_something_pressable_that_changed_nothing():
    got = ps.hints([_press(changed=False)], "/today")
    assert got == [{"kind": "dead_press", "on": {"selector": "button#water", "rect": RECT}, "words": "A press did nothing", "at": 1000}]
    assert ps.hints([_press(changed=True)], "/today") == [], "it changed something"
    assert ps.hints([_press(changed=False, pressable=False)], "/today") == [], "a press on a bare area is no dead press"
    bare = _press(changed=False)
    del bare["pressable"]
    assert ps.hints([bare], "/today") == []
    assert ps.hints([_press(changed=False, path="/other")], "/today") == []


def test_three_presses_within_a_second_on_one_element_are_again_and_a_pair_is_not():
    three = [_press(at=1000), _press(at=1400), _press(at=1900)]
    got = ps.hints(three, "/today")
    assert got == [{"kind": "again", "on": {"selector": "button#water", "rect": RECT}, "words": "Pressed again and again", "at": 1900}]
    assert ps.hints(three[:2], "/today") == []
    assert ps.hints([_press(at=1000), _press(at=1600), _press(at=2200)], "/today") == [], "three, but over a second"
    assert ps.hints([_press("a", at=1000), _press("b", at=1100), _press("a", at=1200)], "/today") == [], "three presses on two elements"
    assert ps.hints([_press("a", at=1000), _press("b", at=1100), _press("a", at=1200), _press("b", at=1300)], "/today") == []
    assert ps.hints([_press(at=1000), _press(at=1500), _press(at=2000)], "/today")[0]["at"] == 2000, "exactly a second is within"


def test_again_takes_the_newest_run_and_may_come_with_a_dead_press():
    events = [_press(at=t, changed=False) for t in (1000, 1100, 1200, 5000, 5100, 5200)]
    got = {h["kind"]: h for h in ps.hints(events, "/today")}
    assert got["again"]["at"] == 5200 and got["dead_press"]["at"] == 5200


def test_one_hint_a_kind_and_element_the_newest_and_newest_first():
    events = [_err("boom", at=1000), _err("boom", at=3000), _err("bang", at=2000), _req("/a", 500, at=1500), _req("/a", 502, at=2500), _req("/b", 500, at=500)]
    got = ps.hints(events, "/today")
    assert [(h["kind"], h["at"]) for h in got] == [("error", 3000), ("failed", 2500), ("error", 2000), ("failed", 500)]
    assert got[1]["words"] == "A request failed: GET /a 502", "the newest of the same request"
    assert [h["words"] for h in got if h["kind"] == "error"] == ["An error here: boom", "An error here: bang"]
    assert len(ps.hints([_err("a", at=1000), _err("a", at=1000)], "/today")) == 1


def test_twenty_hints_at_most_the_newest():
    events = [_err(f"e{n}", at=n) for n in range(50)]
    got = ps.hints(events, "/today")
    assert len(got) == ps.MAX_HINTS == 20 and got[0]["at"] == 49 and got[-1]["at"] == 30


def test_events_of_another_shape_are_skipped():
    junk = [None, 3, "x", {}, {"kind": "scroll", "at": 1}, {"kind": "error", "message": "no time"}, {"kind": "request", "path": "/a", "status": 500, "at": "late"}, {"kind": "press", "at": 1, "changed": False, "pressable": True}]
    assert ps.hints(junk, "") == [] and ps.hints(None, "") == [] and ps.hints([], "") == []
    assert _kinds(ps.hints([{"type": "error", "message": "m", "path": "/", "at": 1}], "/")) == ["error"], "`type` is taken for `kind`"


def test_each_kind_is_a_crafts():
    assert ps.CRAFT == {"error": "tech", "failed": "tech", "slow": "tech", "dead_press": "design", "again": "design"}
    every = [_err(), _req("/a", 500, ms=2000), _press(changed=False), _press("z", at=1), _press("z", at=2), _press("z", at=3)]
    assert set(_kinds(ps.hints(every, "/today"))) == set(ps.CRAFT)


def test_the_ring_keeps_the_last_two_thousand_and_clears():
    ring = ps.Ring()
    for n in range(2500):
        ring.add({"kind": "error", "message": str(n), "path": "/", "at": n})
    got = ring.events()
    assert len(got) == len(ring) == ps.RING_SIZE == 2000 and got[0]["at"] == 500 and got[-1]["at"] == 2499
    ring.add("not an event")
    assert len(ring) == 2000
    ring.clear()
    assert ring.events() == [] and len(ring) == 0
    small = ps.Ring(3)
    for n in range(5):
        small.add({"n": n})
    assert [e["n"] for e in small.events()] == [2, 3, 4]


def test_the_ring_keeps_its_own_copies():
    ring, e = ps.Ring(), {"kind": "error", "message": "a", "path": "/", "at": 1}
    ring.add(e)
    e["message"] = "changed"
    got = ring.events()
    got.clear()
    assert ring.events()[0]["message"] == "a" and len(ring) == 1


def test_the_ring_is_safe_to_add_to_from_many_threads():
    ring = ps.Ring(500)

    def work(t):
        for n in range(400):
            ring.add({"kind": "request", "path": f"/{t}", "status": 200, "ms": 1, "at": n})
            ring.events()
    threads = [threading.Thread(target=work, args=(t,)) for t in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(ring) == 500
