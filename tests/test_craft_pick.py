"""A tool makes the ordinary pick, without a harness session or paid connection."""
import threading
from types import SimpleNamespace

import pytest

from orkboard.core import craft_pick
from orkboard.realm import craft_tools, idea_pick, ideas



@pytest.fixture
def setup(tmp_path, monkeypatch):
    root = tmp_path / 'board'
    party = ideas.add_track(root, 'Art and sound')
    page = ideas.track_page(root, party)
    page.set('recipe', 'art')
    ideas._write(root / ideas.TRACKS / f'{party}.md', page.text())
    monkeypatch.setattr(craft_tools, 'key', lambda _: 'fake-key')
    craft_tools.set_taken(root, party, {'openai-images': {'cap': {'amount': '1', 'currency': 'USD'}}})
    slug = ideas.add_idea(root, 'A picture', track=party)
    task = {'id': 'k1', 'pick': {'n': 2, 'kind': 'image', 'ask': 'A logo', 'target': 'logo.png', 'tool': 'openai-images'}}
    saved = {}
    def no_session(*a):
        pytest.fail('a harness session started')
    runner = SimpleNamespace(repo_root=root, state_dir=tmp_path / 'state', tool_of=lambda *a: 'codex',
                             _session=no_session, _set_task=lambda *a, **kw: saved.update(kw))
    work = tmp_path / 'work'
    work.mkdir()
    return runner, slug, task, work, saved


def run(data):
    r, slug, task, work, _ = data
    return craft_pick.session(r, slug, 'k1', task, work, threading.Event(), 'model', {}, 'prompt', '', {}, '')


def test_maker_feeds_existing_pick_and_receipt(setup, monkeypatch):
    from tests.test_craft_run import picture
    monkeypatch.setattr(craft_pick.craft_run, 'https_transport', lambda **kw: picture())
    assert run(setup) == ''
    r, slug, task, work, saved = setup
    variants, why = idea_pick.read(work, task)
    assert not why and len(variants) == 2
    from orkboard.core.idea_picking import PickMixin
    r._role = lambda task: {'slug': 'artist'}
    r.git = SimpleNamespace(restore=lambda *args: None)
    r._emit = lambda *args, **kwargs: None
    r._log = lambda *args: None
    assert PickMixin._variants(r, slug, 'k1', task, work, 'base', 1)
    assert saved['state'] == 'picking'
    pick = idea_pick.current(r.state_dir, slug, task)
    assert idea_pick.current(r.state_dir, slug, task) == pick
    assert pick['tool'] == 'openai-images'
    assert pick['cap'] == {'amount': '1', 'currency': 'USD'}
    assert pick['cost'] == {'amount': '0.122910', 'currency': 'USD', 'estimate': True}
    assert saved['craft_cost'] == pick['cost']


@pytest.mark.parametrize('again', [{'why': 'Make the logo round', 'files': []}, {'conflict': True}])
def test_a_send_back_runs_the_ai_tools_session_not_the_paid_maker_again(setup, monkeypatch, again):
    r, slug, task, work, _ = setup
    monkeypatch.setattr(craft_pick.craft_run, 'https_transport', lambda **kw: pytest.fail('the maker was paid again'))
    sessions = []
    r._session = lambda *a: sessions.append(a) or 'session'
    assert craft_pick.session(r, slug, 'k1', task, work, threading.Event(), 'model', {}, 'prompt', '', {}, '', again) == 'session'
    assert len(sessions) == 1 and not (work / idea_pick.PICK_DIR).exists()


def test_stop_between_variants_pays_for_no_further_request(setup, monkeypatch):
    from tests.test_craft_run import picture
    stop, calls = threading.Event(), []

    def fake(**kw):
        calls.append(kw)
        stop.set()                                       # Stop pressed while the first variant is made
        return picture()

    monkeypatch.setattr(craft_pick.craft_run, 'https_transport', fake)
    r, slug, task, work, _ = setup
    with pytest.raises(InterruptedError):
        craft_pick.session(r, slug, 'k1', task, work, stop, 'model', {}, 'prompt', '', {}, '')
    assert len(calls) == 1 and not (work / idea_pick.PICK_DIR).exists()
