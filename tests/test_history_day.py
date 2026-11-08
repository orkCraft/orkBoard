"""Spec 162 A (docs/specs/162-the-past-from-history-on-the-parties-tables.md; decisions §277.2): a history page's day, from its decisions, else its spec's §N, else the day it was laid."""
from __future__ import annotations

from orkboard.realm import history_day
from orkboard.realm.idea_page import Page

LOG = [{"number": 260, "day": "2026-10-20"}, {"number": 261, "day": "2026-10-26"}, {"number": 270, "day": "2026-11-02"},
       {"number": 274, "day": "2026-11-05"}, {"number": 280, "day": ""}]
LAID = "2026-11-08"


def page(decisions: str = "") -> Page:
    return Page(meta=[("decisions", decisions)])


def test_several_decisions_take_the_newest():
    assert history_day.day(page("270, 274"), "", LOG, LAID) == "2026-11-05"
    assert history_day.day(page("274, 260"), "§261", LOG, LAID) == "2026-11-05"


def test_a_decision_not_in_the_log_is_not_counted():
    assert history_day.day(page("270, 999"), "", LOG, LAID) == "2026-11-02"
    assert history_day.day(page("999"), "§261", LOG, LAID) == "2026-10-26"       # none of its own held: the spec's
    assert history_day.day(page("280"), "", LOG, LAID) == LAID                    # held with no day: not counted


def test_the_spec_s_highest_held_section_when_the_page_has_none():
    spec = "Changes §260 and §274 and §999 (not decided)"
    assert history_day.day(page(), spec, LOG, LAID) == "2026-11-05"
    assert history_day.day(page(), "see §999 only", LOG, LAID) == LAID


def test_no_section_at_all_gives_the_day_laid():
    assert history_day.day(page(), "no cites here", LOG, LAID) == LAID
    assert history_day.day(page(), "", [], LAID) == LAID
    assert history_day.day(None, None, None, None) == ""


def test_sub_numbers_count_as_their_section():
    assert history_day.cited("§261.9 and § 270.2.1, §x, 12") == {261, 270}
    assert history_day.day(page(), "decisions §261.9", LOG, LAID) == "2026-10-26"
