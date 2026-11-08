"""Spec 160 L: paid pick answers count money, without the generation's contents."""
import json
import threading
from types import SimpleNamespace

import pytest

from orkboard.core import craft_pick
from orkboard.core.idea_picking import PickMixin
from orkboard.realm import event_log, idea_pick
from tests.test_craft_pick import setup, run  # noqa: F401
from tests.test_craft_run import picture


@pytest.mark.parametrize('key', ['B', None], ids=['picked', 'skipped'])
def test_maker_answer_records_receipt_without_prompt_key_or_file(setup, monkeypatch, key):
    r, slug, task, work, saved = setup
    secret = 'fake-key'
    prompt = 'Private prompt about an unreleased character'
    note = 'Private feedback; make another one'
    task['pick']['ask'] = prompt
    calls = []
    def fake(**kw):
        calls.append(kw)
        return picture()
    monkeypatch.setattr(craft_pick.craft_run, 'https_transport', fake)
    run(setup)
    assert len(calls) == 2
    assert all(secret in str(call['headers']) for call in calls)
    r._role = lambda _: {'slug': 'artist'}
    r.git = SimpleNamespace(restore=lambda *a: None)
    published = []
    def emit(event, **kw):
        published.append(kw)
        event_log.record(r.repo_root, event, **kw)
    r._emit = emit
    r._log = lambda *a: None
    PickMixin._variants(r, slug, 'k1', task, work, 'base', 1)
    task.update(state='picking', round=1)
    pick = idea_pick.current(r.state_dir, slug, task)
    # Even unrelated receipt fields must not reach the event.
    path = idea_pick.folder_of(r.state_dir, slug, pick['id']) / 'pick.json'
    raw = json.loads(path.read_text())
    raw['cost'].update(prompt=prompt, api_key=secret, file='private-source.png')
    path.write_text(json.dumps(raw))
    r._lock = threading.RLock()
    r._task = lambda *a: task
    r._runs, r._active = {}, [slug]
    taken, spawned = [], []
    r._take = lambda *a: taken.append(a)
    r._spawn = lambda *a: spawned.append(a)
    r._changed = lambda *a: None
    PickMixin.pick(r, slug, 'k1', key, note)
    [answer] = [e for e in event_log.read(r.repo_root) if e['event'] == event_log.PICK_ANSWERED]
    assert answer['tool'] == pick['tool'] == 'openai-images'
    assert answer['cost'] == pick['cost']
    assert answer['key'] == key and answer['round'] == 1
    assert answer['note_chars'] == len(note)
    assert set(answer) == {'at', 'event', 'idea', 'task', 'key', 'note_chars', 'via', 'seconds', 'device', 'round', 'tool', 'cost'}
    serialized = json.dumps([answer, published[-1]])
    for private in (prompt, secret, note, 'private-source.png', pick['target'], pick['variants'][0]['file']):
        assert private not in serialized
    assert bool(taken) == (key is not None) and len(spawned) == 1
    assert idea_pick.current(r.state_dir, slug, task)['picked'] == key
