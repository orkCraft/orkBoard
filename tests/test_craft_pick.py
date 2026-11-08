"""A tool makes the ordinary pick, without a harness session or paid connection."""
import threading
from dataclasses import replace
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
    def make(self, prompt, dest, count):
        assert prompt == 'A logo' and count == 2
        dest.mkdir()
        files = [dest / f'{i}.svg' for i in range(count)]
        for f in files:
            f.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>')
        return files
    monkeypatch.setattr(craft_pick.craft_run.PictureMaker, 'make', make)
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
    assert pick['cost'] == {'amount': None, 'currency': 'USD'}
    assert saved['craft_cost'] == pick['cost']


@pytest.mark.parametrize('reason', ['no key on this computer', 'its harness cannot make it', 'no official API', 'not taken'])
def test_unavailable_refused_without_session_or_maker(setup, monkeypatch, reason):
    tool = craft_tools.get('openai-images')
    if reason == 'no key on this computer':
        monkeypatch.setattr(craft_tools, 'key', lambda _: None)
    elif reason == 'its harness cannot make it':
        monkeypatch.setitem(craft_tools.REGISTRY, tool.id, replace(tool, needs=('pictures',)))
    elif reason == 'no official API':
        monkeypatch.setitem(craft_tools.REGISTRY, tool.id, replace(tool, official_api=False))
    else:
        craft_tools.set_taken(setup[0].repo_root, ideas.idea_page(setup[0].repo_root, setup[1]).get('track'), {})
    monkeypatch.setattr(craft_pick.craft_run.PictureMaker, 'make', lambda *a, **kw: pytest.fail('maker started'))
    with pytest.raises(ValueError, match='has not taken' if reason == 'not taken' else reason):
        run(setup)


def test_planning_only_offers_taken_here_tools(setup, monkeypatch):
    r, slug, task, _, _ = setup
    party = ideas.idea_page(r.repo_root, slug).get('track')
    assert idea_pick.clean_ask(task['pick'])['tool'] == 'openai-images'
    prompt = craft_pick.plan_lines(r.repo_root, party)
    assert 'openai-images' in prompt and 'elevenlabs-sound' not in prompt and 'fake-key' not in prompt
    plan = {'tasks': [task, {'pick': {**task['pick'], 'tool': 'elevenlabs-sound'}}]}
    craft_pick.clean_plan(plan, r.repo_root, party)
    assert plan['tasks'][0]['pick']['tool'] == 'openai-images'
    assert 'tool' not in plan['tasks'][1]['pick']
    monkeypatch.setattr(craft_tools, 'key', lambda _: None)
    craft_pick.clean_plan(plan, r.repo_root, party)
    assert 'tool' not in task['pick']
