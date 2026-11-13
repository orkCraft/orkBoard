"""realm/idea_words.py: the words New idea completes with."""
from __future__ import annotations

from orkboard.realm import idea_words


def test_titles_first_then_words_by_use_in_any_script_names_of_code_kept_common_words_left_out():
    got = idea_words.words(["Офлайн режим для телефона: офлайн очередь. Также нужно чтобы SyncQueue и sync_queue.py работали.",
                            "Offline mode keeps the edits; offline first."], ["Офлайн режим", "Offline mode"])
    assert got[:2] == ["Офлайн режим", "Offline mode"]
    assert got[2:4] == ["offline", "офлайн"]                      # twice each; a tie is written in lower case
    assert {"SyncQueue", "sync_queue.py", "очередь", "телефона"} <= set(got)
    assert not {"также", "нужно", "чтобы", "the", "для", "и"} & {w.lower() for w in got}


def test_a_short_name_is_the_first_sentence_without_its_asking_words_cut_at_a_words_end():
    # spec 41 §3: what fits a chip, no model
    s = idea_words.short_of
    assert s("Давай сделаем тёмную тему в настройках") == "Сделаем тёмную тему"            # never ends on "в"
    assert s("Давай, может, переделаем шапку. И табы тоже") == "Переделаем шапку"
    assert s("Let's add a dark mode toggle to the settings page.") == "Add a dark mode toggle"
    assert s("Ship the offline mode: the SyncQueue keeps writes") == "Ship the offline mode"
    assert s("  - **Fix** the `sync_queue` error") == "Fix the sync_queue error"     # Markdown's marks left out
    assert s("sync_queue drops writes") == "sync_queue drops writes"                # a name of the code as written
    assert s("docs/specs/41-phone-round-3.md is long") == "41-phone-round-3.md"     # a path too long: its file's name
    assert s("Supercalifragilisticexpialidocious here") == "Supercalifragilisticexpi"
    assert s("Нужно") == "Нужно" and s("") == "" and s("  \n ") == ""
    assert all(len(s(t)) <= idea_words.SHORT_CHARS for t in ("x " * 40, "Добавить оплату картой через Stripe и Apple Pay"))

