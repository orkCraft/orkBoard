"""Money is held durably before any fake paid request leaves the runner."""
import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from orkboard.core import craft_spend
from orkboard.realm import craft_tools, ideas
from tests.test_craft_pick import setup, run
from tests.test_craft_run import picture


def cap(data, amount):
    runner, slug, *_ = data
    party = ideas.idea_page(runner.repo_root, slug).get('track')
    craft_tools.set_taken(runner.repo_root, party, {
        'openai-images': {'cap': {'amount': amount, 'currency': 'USD'}}})


def ledger(data):
    runner, slug, *_ = data
    return craft_spend.Spend(runner.state_dir, slug, 'k1', 'openai-images',
                             {'amount': '1', 'currency': 'USD'})


def test_next_variant_over_cap_is_not_sent_and_receipt_counts_first(setup, monkeypatch):
    cap(setup, '0.10')
    calls = []
    spend = ledger(setup)

    def fake(**kw):
        entries = json.loads(spend.path.read_text())['k1']
        assert entries[-1]['status'] == 'reserved'  # on disk before transport
        calls.append(kw)
        return picture()

    monkeypatch.setattr('orkboard.core.craft_run.https_transport', fake)
    with pytest.raises(ValueError, match=r"The Picture maker's next request costs about .* USD.*0.10 USD cap"):
        run(setup)
    assert len(calls) == 1
    assert setup[-1]['craft_cost']['amount'] == '0.061455'
    assert json.loads(spend.path.read_text())['k1'][0]['status'] == 'settled'
    assert not (setup[3] / '.orkcraft-pick').exists()


@pytest.mark.parametrize('failure', ['crash', 'timeout', 'send back'])
def test_restart_and_send_back_never_erase_earlier_spend(setup, monkeypatch, failure):
    cap(setup, '0.15' if failure == 'send back' else '0.10')
    calls = []

    def fake(**kw):
        calls.append(kw)
        if failure == 'crash':
            raise SystemExit('lost process')
        if failure == 'timeout':
            raise TimeoutError('uncertain bill')
        return picture()

    monkeypatch.setattr('orkboard.core.craft_run.https_transport', fake)
    if failure == 'crash':
        with pytest.raises(SystemExit):
            run(setup)
    elif failure == 'timeout':
        with pytest.raises(ValueError, match='timed out'):
            run(setup)
    else:
        run(setup)
    # A reconstructed Spend reads disk; a new round must not grant fresh money.
    setup[2]['round'] = 2
    with pytest.raises(ValueError, match='cap'):
        run(setup)
    assert len(calls) == (2 if failure == 'send back' else 1)
    assert Decimal(ledger(setup).cost()['amount']) <= Decimal('0.15')


def test_parallel_reservations_and_failed_atomic_replace(tmp_path, monkeypatch):
    def reserve(_):
        spend = craft_spend.Spend(tmp_path, 'goal', 'k1', 'elevenlabs-sound',
                                  {'amount': '0.01', 'currency': 'USD'})
        try:
            return spend.reserve({'duration_seconds': 5})
        except ValueError:
            return None
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(x is not None for x in pool.map(reserve, range(8))) == 1
    spend = craft_spend.Spend(tmp_path, 'goal', 'k1', 'elevenlabs-sound',
                              {'amount': '1', 'currency': 'USD'})
    before = spend.path.read_bytes()
    monkeypatch.setattr(craft_spend.os, 'replace', lambda *a: (_ for _ in ()).throw(OSError('disk')))
    with pytest.raises(OSError):
        spend.reserve({'duration_seconds': 5})
    assert spend.path.read_bytes() == before


def test_registry_prices_and_estimate_words():
    sound = craft_spend.price('elevenlabs-sound', {'duration_seconds': 5})
    assert sound == dict(amount='0.01', currency='USD', estimate=True, dated='2026-11-08')
    image = craft_spend.price('openai-images', {'prompt': 'A logo'})
    assert image['estimate'] and image['dated'] == '2026-11-08'
    assert Decimal(image['amount']) == Decimal('0.061455')


@pytest.mark.parametrize('existing', [False, True])
def test_missing_key_pick_preserves_ledger_then_one_request_fits_cap(setup, monkeypatch, existing):
    from orkboard.core import craft_pick
    cap(setup, craft_spend.price('openai-images', {'prompt': 'A logo'})['amount'])
    spend = ledger(setup)
    if existing:
        other = craft_spend.Spend(setup[0].state_dir, setup[1], 'other-task',
                                  'elevenlabs-sound', {'amount': '1', 'currency': 'USD'})
        other.reserve({'duration_seconds': 5})
    before = spend.path.read_bytes() if existing else None
    calls = []
    monkeypatch.setattr(craft_tools, 'key', lambda _: None)
    monkeypatch.setattr('orkboard.core.craft_run.https_transport',
                        lambda **kw: calls.append(kw) or picture())
    with monkeypatch.context() as missing:
        missing.setattr(craft_pick.craft_spend, 'Spend',
                        lambda *a, **kw: pytest.fail('Spend created before key check'))
        with pytest.raises(ValueError, match='Picture maker is not here: no key on this computer'):
            run(setup)
    assert calls == []
    assert (spend.path.read_bytes() if spend.path.exists() else None) == before
    monkeypatch.setattr(craft_tools, 'key', lambda _: 'fake-key')
    # Picks need at least two variants. The one-request cap must allow the
    # first request, then stop the second rather than blocking the whole retry.
    with pytest.raises(ValueError, match='USD.*cap'):
        run(setup)
    assert len(calls) == 1
    entries = json.loads(spend.path.read_text())['k1']
    assert len(entries) == 1 and entries[0]['status'] == 'settled'
    assert setup[-1]['craft_cost']['amount'] == setup[-1]['craft_cap']['amount']


def test_fake_key_only_read_at_request_and_absent_from_artifacts(setup, monkeypatch):
    from orkboard.core.idea_picking import PickMixin
    from types import SimpleNamespace
    from orkboard.core import craft_pick
    key = 'FAKE-STAGE-D-KEY-7b169'
    reads, calls, events, logs = [], [], [], []
    monkeypatch.setattr(craft_tools, 'key', lambda _: reads.append(True) or key)
    def fake(**kw):
        # The chair checks both makers' presence, then each request re-reads
        # its own key instead of retaining the availability credential.
        assert len(reads) == len(calls) + 3
        assert kw['headers']['Authorization'] == 'Bearer ' + key
        calls.append(True)
        return picture()
    monkeypatch.setattr('orkboard.core.craft_run.https_transport', fake)
    runner, slug, task, work, saved = setup
    prompt = 'The harness prompt'
    plan = json.dumps({'tasks': [task]})
    run(setup)
    runner._role = lambda _: {'slug': 'artist'}
    runner.git = SimpleNamespace(restore=lambda *a: None)
    runner._emit = lambda *a, **kw: events.append((a, kw))
    runner._log = lambda *a: logs.append(a)
    PickMixin._variants(runner, slug, 'k1', task, work, 'base', 1)
    assert len(calls) == 2 and len(reads) == 4
    artifacts = [p.read_bytes() for p in runner.repo_root.rglob('*.md')]
    artifacts += [p.read_bytes() for p in runner.state_dir.rglob('*.json')]
    artifacts += [json.dumps(events).encode(), json.dumps(logs).encode(), plan.encode(), prompt.encode()]
    assert all(key.encode() not in artifact for artifact in artifacts)


def test_cap_stop_keeps_price_cap_party_and_maker_for_its_plate(setup, monkeypatch):
    cap(setup, '0.01')
    monkeypatch.setattr('orkboard.core.craft_run.https_transport', lambda **kw: pytest.fail('request sent'))
    with pytest.raises(craft_spend.CapStopped):
        run(setup)
    runner, slug, _, _, saved = setup
    stop = saved['craft_stop']
    assert stop == {'tool': 'openai-images', 'party': ideas.idea_page(runner.repo_root, slug).get('track'),
                    'price': {'amount': '0.061455', 'currency': 'USD', 'estimate': True, 'dated': '2026-11-08'},
                    'cap': {'amount': '0.01', 'currency': 'USD'},
                    'held': {'amount': '0', 'currency': 'USD', 'estimate': True}}
    from orkboard.realm.board_map import _run_of
    assert _run_of(saved)['craft_stop'] == stop
