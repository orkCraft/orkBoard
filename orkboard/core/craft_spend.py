"""Durable paid-request reservations (spec 158 D).

Uncertain requests stay reserved. Send-backs share the task's allowance: changing
its round number never erases money already committed. Prices are estimates,
not provider bills; no response currently supplies a settled monetary charge.
"""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from orkboard.realm import craft_tools, ideas


def price(tool_id: str, payload: dict) -> dict:
    tool = craft_tools.get(tool_id)
    rates = tool.prices
    if tool_id == 'openai-images':
        # No image input is sent. UTF-8 bytes conservatively estimate text tokens;
        # allow 4096 output tokens for the fixed low-quality 1024-square image.
        text = next(p for p in rates if 'text input' in p.unit)
        output = next(p for p in rates if 'image output' in p.unit)
        amount = (Decimal(text.amount) * len(payload['prompt'].encode('utf-8'))
                  + Decimal(output.amount) * 4096) / Decimal(1000000)
    elif tool_id == 'elevenlabs-sound':
        amount = Decimal(rates[0].amount) * Decimal(str(payload['duration_seconds'])) / 60
    else:
        raise ValueError('That tool has no request price')
    return dict(amount=format(amount, 'f'), currency=rates[0].currency,
                estimate=True, dated=max(p.dated for p in rates))


class Spend:
    def __init__(self, state_dir: Path, slug: str, tid: str, tool_id: str, cap: dict):
        self.path = ideas.state_folder(state_dir, slug) / 'craft-spend.json'
        self.tid, self.tool_id, self.cap = tid, tool_id, cap

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                data = json.loads(self.path.read_text()) if self.path.exists() else {}
                yield data
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def write(self, data):
        fd, temporary = tempfile.mkstemp(dir=self.path.parent, prefix='.craft-spend-')
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(data, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            directory = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def entries(self, data):
        return data.setdefault(self.tid, [])

    def total(self, data):
        return sum((Decimal(e['price']['amount']) for e in self.entries(data)), Decimal(0))

    def reserve(self, payload):
        quote = price(self.tool_id, payload)
        with self.locked() as data:
            # Count all earlier requests, including unsettled and other tool IDs.
            if quote['currency'] != self.cap['currency'] or any(
                    e['price']['currency'] != quote['currency'] for e in self.entries(data)):
                raise ValueError('The tool price and the cap need the same currency')
            if self.total(data) + Decimal(quote['amount']) > Decimal(self.cap['amount']):
                raise ValueError(f"The next request costs an estimated {quote['amount']} {quote['currency']}; "
                                 f"with {self.total(data)} {quote['currency']} already held, "
                                 f"it exceeds the {self.cap['amount']} {self.cap['currency']} cap")
            token = uuid4().hex
            self.entries(data).append(dict(id=token, tool=self.tool_id, price=quote, status='reserved'))
            self.write(data)
            return token

    def settle(self, token):
        with self.locked() as data:
            entry = next(e for e in self.entries(data) if e['id'] == token)
            entry['status'] = 'settled'
            self.write(data)

    def cost(self):
        with self.locked() as data:
            return dict(amount=format(self.total(data), 'f'), currency=self.cap['currency'], estimate=True)
