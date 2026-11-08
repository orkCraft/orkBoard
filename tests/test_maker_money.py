"""Spec 158 K: the plate's agreement follows fake paid calls into the pick."""
import json
import threading
from decimal import Decimal
from types import SimpleNamespace

import pytest

from orkboard.core import craft_pick, craft_spend
from orkboard.core.idea_picking import PickMixin
from orkboard.realm import craft_tools, idea_pick, ideas, party_recipes
from tests.test_board_35 import host, model, runner  # noqa: F401
from tests.test_craft_run import picture
from tests import pick_files as pf
from tests.test_stall import _party, shelf, stall, ware


def run_from_plate(host, tmp_path, party, amount, tool_id):
    result = host.command('ideas.stall_take', dict(
        chair=party, slot='craft_tools', value=tool_id,
        cap=dict(amount=amount, currency='USD')))
    plate = ware(result['stall'], 'craft_tools', tool_id)
    root = host.ideas.root()
    slug = ideas.add_idea(root, 'Paid picture', track=party)
    task = dict(id='k1', pick=dict(n=2, kind='image' if tool_id == 'openai-images' else 'audio', ask='A logo', target='logo.png' if tool_id == 'openai-images' else 'sound.mp3', tool=plate['id']))
    saved = {}
    work = tmp_path / 'work'
    work.mkdir()
    r = SimpleNamespace(repo_root=root, state_dir=host.ideas.state_dir, tool_of=lambda *a: 'codex',
                        _set_task=lambda *a, **kw: saved.update(kw),
                        _session=lambda *a: pytest.fail('AI tool session started'))
    def run():
        return craft_pick.session(r, slug, 'k1', task, work, threading.Event(), '', {}, '', '', {}, '')
    return plate, r, slug, task, work, saved, run


@pytest.mark.parametrize('tool_id,amount,calls_expected,unit', [
    ('openai-images', '0.01', 0, '0.061455'),
    ('openai-images', '0.10', 1, '0.061455'),
    ('openai-images', '0.13', 2, '0.061455'),
    ('elevenlabs-sound', '0.001', 0, '0.01'),
    ('elevenlabs-sound', '0.015', 1, '0.01'),
    ('elevenlabs-sound', '0.025', 2, '0.01'),
])
def test_plate_cap_controls_calls_and_pick_receipt(host, tmp_path, monkeypatch, tool_id, amount, calls_expected, unit):
    monkeypatch.setattr(craft_tools, 'key', lambda _: 'fake-money-key')
    party = _party(host, 'art')
    plate, r, slug, task, work, saved, run = run_from_plate(host, tmp_path, party, amount, tool_id)
    assert plate['price'] == {'money': f"{'about ' if tool_id == 'elevenlabs-sound' else ''}{amount} USD cap"}
    calls = []
    def fake(**kw):
        calls.append(kw)
        return picture() if tool_id == 'openai-images' else craft_pick.craft_run.Response(200, 'audio/mpeg', pf.mp3())
    monkeypatch.setattr(craft_pick.craft_run, 'https_transport', fake)
    if calls_expected < 2:
        with pytest.raises(craft_spend.CapStopped) as error:
            run()
        stop = saved['craft_stop']
        assert stop['party'] == party and stop['tool'] == plate['id']
        assert stop['cap'] == plate['cap']
        assert stop['held'] == saved['craft_cost']
        assert Decimal(stop['held']['amount']) + Decimal(stop['price']['amount']) > Decimal(amount)
        assert f'{unit} USD' in str(error.value) and f'{amount} USD cap' in str(error.value)
        assert 'already held' in str(error.value)
    else:
        run()
        r._role = lambda _: {'slug': 'artist'}
        r.git = SimpleNamespace(restore=lambda *a: None)
        r._emit = lambda *a, **kw: None
        r._log = lambda *a: None
        assert PickMixin._variants(r, slug, 'k1', task, work, 'base', 1)
        pick = idea_pick.current(r.state_dir, slug, task)
        assert pick['tool'] == plate['id'] and pick['cap'] == plate['cap']
        assert pick['cost'] == saved['craft_cost']
        # Read the real pick into the face's receipt data, without a stub receipt.
        task.update(state='picking')
        rows = host.ideas.pick_rows(dict(slug=slug, track=party, title='Paid picture', priority='normal'), {'tasks': [task]})
        assert rows[-1]['maker'] == dict(id=plate['id'], word=craft_tools.get(tool_id).maker, cost=pick['cost'], cap=plate['cap'])
    assert len(calls) == calls_expected
    entries = json.loads((ideas.state_folder(r.state_dir, slug) / 'craft-spend.json').read_text())['k1'] if calls else []
    total = sum((Decimal(e['price']['amount']) for e in entries), Decimal(0))
    assert total == Decimal(unit) * len(calls) <= Decimal(amount)
    assert saved['craft_cost'] == dict(amount=format(total, 'f'), currency='USD', estimate=True)


def test_first_inventory_only_art_has_two_money_plates_and_disclosures(host, monkeypatch):
    monkeypatch.setattr(craft_tools, 'key', lambda tid: 'fake-money-key' if tid == 'openai-images' else None)
    assert set(craft_tools.REGISTRY) == {'openai-images', 'elevenlabs-sound'}
    for craft in party_recipes.CRAFTS:
        party = _party(host, craft)
        first = stall(host, party)
        if craft != 'art':
            assert all(s['slot'] != 'craft_tools' for s in first['shelves'])
            continue
        assert all(w['price'] == {'word': 'Set a cap'} and w['cap'] is None
                   for w in shelf(first, 'craft_tools')['wares'])
        # A missing key may have a shared Board cap, but remains not here locally.
        craft_tools.set_taken(host.ideas.root(), party, {
            tid: {'cap': dict(amount='1.25', currency='USD')} for tid in craft_tools.REGISTRY})
        plates = shelf(stall(host, party), 'craft_tools')['wares']
        assert [p['price']['money'] for p in plates] == ['1.25 USD cap', 'about 1.25 USD cap']
        assert plates[0]['here']
        assert not plates[1]['here'] and plates[1]['why'] == 'no key on this computer'
        for p in plates:
            assert p['leaves'] == craft_tools.get(p['id']).leaves and 'prompt is sent to' in p['leaves']
            visible = ' '.join((p['word'], p['line'], p['price']['money'], p['leaves'], p['why']))
            assert not any(w in visible.lower() for w in ('tokens', 'credits', '%', 'harness', 'suno'))
