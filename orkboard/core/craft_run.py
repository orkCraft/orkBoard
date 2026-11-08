"""Picture and Sound makers (spec 160 B).

Each call makes one asset. The caller owns reservations and the pick manifest;
makers only send the prompt and return validated files. No redirects or remote
asset URLs are followed. Tests inject a transport, never a provider SDK.
"""
from __future__ import annotations

import base64
import binascii
import http.client
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from orkboard.realm import craft_tools, idea_pick, media_sniff

TIMEOUT = 120.0


class MakerError(ValueError):
    """A failed tool request, safe to show without provider text or credentials."""


@dataclass(frozen=True)
class Response:
    status: int
    mime: str
    body: bytes


Transport = Callable[..., Response]


def https_transport(*, host: str, path: str, headers: dict, body: bytes,
                    timeout: float, limit: int) -> Response:
    """Bounded HTTPS POST to a registry host. Redirects are returned, never followed."""
    if host not in {t.host for t in craft_tools.REGISTRY.values()} or not path.startswith("/v1/"):
        raise MakerError("The maker's endpoint is not allowed")
    word = next(t.maker for t in craft_tools.REGISTRY.values() if t.host == host)
    connection = http.client.HTTPSConnection(host, timeout=timeout)
    try:
        connection.request("POST", path, body=body, headers=headers)
        answer = connection.getresponse()
        data = answer.read(limit + 1)
        if len(data) > limit:
            raise MakerError(f"The {word}'s answer is too large")
        return Response(answer.status, answer.getheader("Content-Type", "").split(";")[0].strip().lower(), data)
    finally:
        connection.close()


class _Maker:
    tool_id: str
    kind: str
    path: str

    def __init__(self, transport: Transport | None = None, *, spend=None):
        self.transport = transport or https_transport
        self.spend = spend

    @property
    def word(self) -> str:
        return craft_tools.get(self.tool_id).maker

    def _request(self, payload: dict) -> Response:
        tool = craft_tools.get(self.tool_id)
        credential = craft_tools.key(self.tool_id)  # only at the request
        if not credential:
            raise MakerError(f"The {self.word} has no key on this computer")
        headers = {"Content-Type": "application/json"}
        if self.kind == "image":
            headers["Authorization"] = f"Bearer {credential}"
        else:
            headers["xi-api-key"] = credential
        # A base64 JSON image answer needs more room than its decoded asset.
        limit = (idea_pick.KINDS[self.kind].limit * 4 // 3 + 65536
                 if self.kind == "image" else idea_pick.KINDS[self.kind].limit)
        body = json.dumps(payload).encode()
        # Only commit money once local preparation has succeeded. Once handed
        # to the transport, an uncertain request may still be billed.
        reservation = self.spend.reserve(payload) if self.spend else None
        try:
            response = self.transport(host=tool.host, path=self.path, headers=headers,
                                      body=body, timeout=TIMEOUT, limit=limit)
        except MakerError:
            raise
        except (OSError, http.client.HTTPException, ValueError):
            raise MakerError(f"The {self.word}'s request failed or timed out") from None
        if not 200 <= response.status < 300:
            raise MakerError(f"The {self.word}'s request failed (HTTP {response.status})")
        if len(response.body) > limit:
            raise MakerError(f"The {self.word}'s answer is too large")
        if self.spend:
            self.spend.settle(reservation)
        return response

    def make(self, prompt: str, destination: Path, *, count: int = 1) -> list[Path]:
        """Make assets in a new folder; remove that folder on any failure.

        Existing folders are refused so cleanup cannot remove an earlier pick.
        The runner can put this folder at idea_pick.PICK_DIR in its worktree.
        """
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= idea_pick.N_MAX:
            raise MakerError(f"The {self.word} makes between one and six variants")
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=False)
        made, total = [], 0
        try:
            for i in range(count):
                data, declared = self._asset(prompt)
                kind = idea_pick.KINDS[self.kind]
                if len(data) > kind.limit:
                    raise MakerError(f"The {self.word}'s {kind.word} is at most {idea_pick.size_words(kind.limit)}")
                total += len(data)
                if total > idea_pick.PICK_MAX:
                    raise MakerError(f"The {self.word}'s pick is at most {idea_pick.size_words(idea_pick.PICK_MAX)}")
                candidate = destination / f"{i + 1}.part"
                candidate.write_bytes(data)
                mime = media_sniff.sniff(candidate)
                if mime not in kind.mimes or mime != declared:
                    raise MakerError(f"The {self.word} did not return a {kind.word} of the stated type ({kind.formats})")
                asset = candidate.with_suffix('.' + idea_pick.EXT[mime])
                candidate.rename(asset)
                made.append(asset)
            return made
        except BaseException:
            import shutil
            shutil.rmtree(destination)
            raise


class PictureMaker(_Maker):
    tool_id, kind, path = "openai-images", "image", "/v1/images/generations"

    def _asset(self, prompt: str) -> tuple[bytes, str]:
        answer = self._request({"model": "gpt-image-2", "prompt": prompt, "n": 1,
                                "size": "1024x1024", "quality": "low", "output_format": "png"})
        if answer.mime != "application/json":
            raise MakerError("The Picture maker did not return a JSON answer")
        try:
            rows = json.loads(answer.body)["data"]
            if not isinstance(rows, list) or len(rows) != 1:
                raise ValueError
            return base64.b64decode(rows[0]["b64_json"], validate=True), "image/png"
        except (ValueError, KeyError, TypeError, binascii.Error):
            raise MakerError("The Picture maker did not return one base64 picture") from None


class SoundMaker(_Maker):
    tool_id, kind, path = "elevenlabs-sound", "audio", "/v1/sound-generation"

    def _asset(self, prompt: str) -> tuple[bytes, str]:
        answer = self._request({"text": prompt, "duration_seconds": 5, "prompt_influence": 0.3})
        if answer.mime not in idea_pick.KINDS["audio"].mimes:
            raise MakerError("The Sound maker did not return a sound of a kind the Board takes")
        return answer.body, answer.mime
