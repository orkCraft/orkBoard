"""The Board in a phone's browser (gui/pwa.py): the app's files from the phone listener (Orkboard's shell alone, no
camp file), a browser's socket that names its token as a subprotocol, the pairing link on the tailnet, and Tailscale's
state for the desktop."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import http.client
import json
import posixpath
import re
import subprocess
import threading
from pathlib import Path

import pytest
from websockets.asyncio.client import connect
from websockets.exceptions import InvalidStatus

from orkboard.gui import phone_tls, phones, pwa, tailnet
from orkboard.gui.board_host import Orkboard
from tests.test_phones import _pair, _pinned, _serve, _ws_url


def _get(address: str, path: str, method: str = "GET") -> tuple[int, dict[str, str], bytes]:
    host, port = address.removeprefix("https://").rsplit(":", 1)
    conn = http.client.HTTPSConnection(host, int(port), context=_pinned(), timeout=5)
    try:
        conn.request(method, path)
        r = conn.getresponse()
        return r.status, {k.lower(): v for k, v in r.getheaders()}, r.read()
    finally:
        conn.close()


# -- the files, without a network -------------------------------------------------------------------------

def _split(raw: bytes) -> tuple[str, bytes]:
    head, _, body = raw.partition(b"\r\n\r\n")
    return head.decode("ascii"), body


def test_the_app_is_its_own_files_and_nothing_else():
    names = set(pwa.files())
    assert {"index.html", "old.html", "frame.js", "frame.css", "board-app.js", "app.css", "manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png",
            "apple-touch-icon.png"} <= names
    head, body = _split(pwa.serve("GET", "/app/"))            # the desktop's page, in the frame (spec 117 A)
    assert head.startswith("HTTP/1.1 200") and b'src="frame.js"' in body and b"board-app.js" not in body
    assert "Content-Security-Policy: default-src 'self'; script-src 'self' 'sha256-" in head
    head, body = _split(pwa.serve("GET", "/app/old.html"))     # the phone's old face, until spec 94 E
    assert head.startswith("HTTP/1.1 200") and b'src="board-app.js"' in body and b"frame.js" not in body
    assert "Content-Security-Policy: default-src 'self'; script-src 'self'; style-src" in head
    head, _ = _split(pwa.serve("GET", "/app/board-app.js"))
    assert "text/javascript" in head and "Content-Security-Policy" not in head
    assert "Service-Worker-Allowed: /app/" in _split(pwa.serve("GET", "/app/sw.js"))[0]
    for path in ("/app/../phones.py", "/app/..%2Fphones.py", "/app/nothing.js", "/app/js/app.js", "/app/app.js"):
        assert _split(pwa.serve("GET", path))[0].startswith("HTTP/1.1 404"), path
    assert _split(pwa.serve("POST", "/app/"))[0].startswith("HTTP/1.1 405")
    assert "Location: /app/" in _split(pwa.serve("GET", "/app"))[0]
    head, body = _split(pwa.serve("GET", "/app/fonts/ibm-plex-mono-latin-400-normal.woff2"))   # orkUI's faces, as the desktop's
    assert "Content-Type: font/woff2" in head and body[:4] == b"wOF2"
    faces = _split(pwa.serve("GET", "/app/fonts.css"))[1]
    assert b"IBM Plex Mono" in faces and b"Pixelify Sans" in faces
    assert _split(pwa.serve("GET", "/app/fonts/OFL-IBM-Plex-Mono.txt"))[0].startswith("HTTP/1.1 404")
    head, body = _split(pwa.serve("GET", "/app/races/elf-elder.png"))                         # orkUI's race heads
    assert "Content-Type: image/png" in head and body[:8] == b"\x89PNG\r\n\x1a\n"
    for mark in ("harness-claude", "rank-1"):                                                    # orkUI's marks (spec 49 §1.6), the cache-first kind
        for suffix in (".png", "@2x.png"):
            head, body = _split(pwa.serve("GET", f"/app/marks/{mark}{suffix}"))
            assert "Content-Type: image/png" in head and "immutable" in head and body[:8] == b"\x89PNG\r\n\x1a\n", mark + suffix
    assert _split(pwa.serve("GET", "/app/marks/README.md"))[0].startswith("HTTP/1.1 404")
    assert "image/svg+xml" in _split(pwa.serve("GET", "/app/icons/icons.svg"))[0]              # orkUI's pixel icons
    for folder, names in (("elements", ("meadow", "ice", "dust", "void", "lava")), ("signs", ("check", "cross", "work", "night", "alert", "flag", "before", "after", "play", "pause", "sound", "film", "text",
                                                                         "feature", "bug", "tidy", "screen", "picture", "logo", "target", "flask", "horn", "chart", "page", "restructure", "abtest", "landing", "post", "tagline",
                                                                         "mechanic", "level", "balance", "character", "release", "store", "tune"))):
        for name in names:                                                                       # orkUI's elements and signs (spec 50 §1, §1.6): masks need the page's own origin
            head, body = _split(pwa.serve("GET", f"/app/{folder}/{name}.svg"))
            assert head.startswith("HTTP/1.1 200") and "Content-Type: image/svg+xml" in head and b"<svg" in body and b'viewBox="0 0 7 7"' in body, f"{folder}/{name}"
        assert _split(pwa.serve("GET", f"/app/{folder}/README.md"))[0].startswith("HTTP/1.1 404")
    css = _split(pwa.serve("GET", "/app/components.css"))[1].decode()                          # every mask of components.css resolves beside it
    masks = set(re.findall(r"url\(((?:elements|signs)/[a-z]+\.svg)\)", css))
    assert len(masks) == 46 and masks <= set(pwa.files())                                # five elements, forty-one signs (orkUI 0.15: moon beside night, sword, shield; 0.15.5 question; 0.16 compass, steps)
    head, body = _split(pwa.serve("HEAD", "/app/app.css"))
    assert head.startswith("HTTP/1.1 200") and body == b""


def test_the_app_serves_the_desktops_page_its_import_map_by_hash_and_orkui_by_the_pages_own_address():
    """Spec 117 A: the page's files from the one place the desktop has them, under /app/page/ (the old face's own board.js keeps /app/board.js),
    Preact and the rest with their licences and no terminal, `roles.css` made from the tokens, and orkUI at /ds/orkui/ as `js/orkui.js` names it."""
    from orkboard.gui import server
    for name, source in {"page/board.js": "board.js", "page/page.css": "page.css", "page/js/link.js": "js/link.js", "page/js/hand/upright.js": "js/hand/upright.js",
                         "page/vendor/preact.mjs": "vendor/preact.mjs", "page/vendor/LICENSE-preact.txt": "vendor/LICENSE-preact.txt"}.items():
        head, body = _split(pwa.serve("GET", f"/app/{name}"))
        assert head.startswith("HTTP/1.1 200") and body == (server.STATIC / source).read_bytes(), name
        assert ("text/javascript" if name.endswith((".js", ".mjs")) else "text/css" if name.endswith(".css") else "text/plain") in head, name
    assert _split(pwa.serve("GET", "/app/board.js"))[1] == (pwa.ROOT / "board.js").read_bytes()               # the old face's, untouched
    for name in ("page/vendor/xterm.mjs", "page/vendor/xterm.css", "page/vendor/LICENSE-xterm.txt", "page/vendor/README.md", "page/play/probe.js", "page/js/../index.html"):
        assert _split(pwa.serve("GET", f"/app/{name}"))[0].startswith("HTTP/1.1 404"), name
    head, body = _split(pwa.serve("GET", "/app/roles.css"))
    assert "text/css" in head and b".ok-font-status" in body and b".ok-tone-muted" in body
    # every stylesheet and module the page links or imports by `new URL(…, import.meta.url)` is served
    served = set(pwa.files())
    for name, path in pwa.page_files().items():
        for rel in re.findall(r'new URL\("(\./[^"]+\.css)", import\.meta\.url\)', path.read_text(encoding="utf-8")) if name.endswith(".js") else []:
            assert posixpath.normpath(posixpath.join(posixpath.dirname(name), rel)) in served, f"{name} links {rel}"
    # orkUI by the page's address: the same bytes as under /app/, only orkUI's files, nothing of the app's own
    for name in ("races/elf-elder.png", "marks/harness-claude.png", "icons/icons.svg", "signs/check.svg", "elements/meadow.svg"):
        assert _split(pwa.serve("GET", f"/ds/orkui/{name}")) == _split(pwa.serve("GET", f"/app/{name}")), name
    for name in ("index.html", "frame.js", "sw.js", "board-app.js", "manifest.webmanifest", "page/board.js", "assets.json", ""):
        assert _split(pwa.serve("GET", f"/ds/orkui/{name}"))[0].startswith("HTTP/1.1 404"), name
    assert pwa.wants("/ds/orkui/races/x.png") and not pwa.wants("/ds/sprites/x.png") and not pwa.wants("/static/board.js")
    head, _ = _split(pwa.serve("POST", "/ds/orkui/icons/icons.svg"))
    assert head.startswith("HTTP/1.1 405")
    # the import map is the one inline script, allowed by its hash; its addresses are the page's, relative to the app
    head, body = _split(pwa.serve("GET", "/app/"))
    maps = re.findall(rb'<script type="importmap">(.*?)</script>', body, re.S)
    assert len(maps) == 1 and re.findall(rb"<script(?![^>]*\bsrc=)[^>]*>", body) == [b'<script type="importmap">']        # no other inline script
    digest = base64.b64encode(hashlib.sha256(maps[0]).digest()).decode()
    csp = next(line for line in head.splitlines() if line.startswith("Content-Security-Policy")).split(": ", 1)[1]
    assert f"script-src 'self' 'sha256-{digest}';" in csp and "unsafe" not in csp and "style-src 'self';" in csp
    imports = json.loads(maps[0])["imports"]
    assert set(imports) == {"preact", "preact/hooks", "htm", "@preact/signals-core", "@preact/signals"}
    for target in imports.values():
        assert target.startswith("./page/vendor/") and posixpath.normpath(target[2:]) in served, target
    assert pwa.csp(b"<html></html>") == pwa.CSP                                                                     # a page with none gets the plain one


def test_every_picture_orkuis_components_draw_is_served_beside_it():
    """The potions' bottles, a tool's rune, the big signs, the card backs: `components.css` masks them by relative address, so each must be there (the 404s of the first run of the page on a phone)."""
    css = _split(pwa.serve("GET", "/app/components.css"))[1].decode()
    wanted = {u for u in re.findall(r"url\(['\"]?([^)'\"]+)\)", css) if not u.startswith("data:")}
    assert len(wanted) > 150 and wanted <= set(pwa.files()), sorted(wanted - set(pwa.files()))
    for name in ("signs/big/bug.svg", "potion/body.svg", "runes/key.svg", "tools/bell-note.svg", "backs/back.svg"):
        head, body = _split(pwa.serve("GET", f"/ds/orkui/{name}"))
        assert head.startswith("HTTP/1.1 200") and "image/svg+xml" in head and b"<svg" in body, name
    for name in ("potion/sizes.json", "potion/README.md", "tools/README.md", "die/die.json", "signs/big"):
        assert _split(pwa.serve("GET", f"/ds/orkui/{name}"))[0].startswith("HTTP/1.1 404"), name


def test_the_page_files_are_the_ones_the_desktop_serves_but_for_what_a_phone_has_no_use_of():
    from orkboard.gui import server
    on_phone = {name.removeprefix(pwa.PAGE) for name in pwa.page_files()}
    on_desktop = {p.relative_to(server.STATIC).as_posix() for p in server.STATIC.rglob("*") if p.is_file()
                  and (p.suffix in (".js", ".css", ".mjs", ".txt") or p.name == "board.js")}
    left = on_desktop - on_phone
    assert all(name.startswith(("vendor/xterm", "vendor/LICENSE-xterm", "play/", "pwa/")) or name == "index.html" or "/__" in name for name in left), left


def test_every_import_of_a_served_module_is_a_served_module_with_the_names_it_takes():
    """The app's module graph, as the phone loads it (the owner's phone stuck on "Loading…" when the desktop's layout
    gained imports /app/ did not serve, and one name that resolved to the app's own ground.js): every relative import
    in a served .js resolves, under /app/, to a served .js that exports each name taken from it."""
    import posixpath
    import re
    served = pwa.files()
    imports = re.compile(r'import\s*\{([^}]*)\}\s*from\s*"(\.{1,2}/[^"]+)"|import\s*"(\.{1,2}/[^"]+)"')
    exports = re.compile(r"export\s+(?:async\s+)?(?:function\*?|const|let|var|class)\s+([\w$]+)|export\s*\{([^}]*)\}")
    for name, path in served.items():
        if not name.endswith(".js") or name == "sw.js":
            continue
        for names, rel, bare in imports.findall(path.read_text(encoding="utf-8")):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), rel or bare))
            assert target in served, f"{name} imports {rel or bare}: /app/{target} is not served"
            text = served[target].read_text(encoding="utf-8")
            has = {m[0] for m in exports.findall(text) if m[0]}
            has |= {x.split(" as ")[-1].strip() for m in exports.findall(text) if m[1] for x in m[1].split(",")}
            for line in re.findall(r"^export\s+(?:const|let|var)\s+(.*)$", text, re.M):       # `export const A = 1, B = 2`: every name
                has |= set(re.findall(r"(?:^|,)\s*([\w$]+)\s*=", line))
            for one in filter(None, (x.split(" as ")[0].strip() for x in names.split(","))):
                assert one in has, f"{name} takes {one} from {target}, which does not export it"


def test_the_service_worker_keeps_every_module_the_app_loads():
    """The frame's and the old face's modules are in the worker's own list; the page's are the list gui/pwa.py writes into the worker it serves (`PAGE`)."""
    sw = (pwa.ROOT / "sw.js").read_text(encoding="utf-8")
    shell = set(re.findall(r'"([^"]+)"', sw[sw.index("const SHELL"):sw.index("];", sw.index("const SHELL"))]))
    assert {k for k in pwa.files() if k.endswith(".js") and k != "sw.js" and not k.startswith(pwa.PAGE)} <= shell
    assert {"./", "frame.js", "frame.css", "old.html"} <= shell
    served = _split(pwa.serve("GET", "/app/sw.js"))[1].decode()
    page = set(json.loads(re.search(r"const PAGE = (\[.*?\]);", served).group(1)))
    assert page == set(pwa.page_shell()) >= set(pwa.page_files()) | {"roles.css"}
    assert {name for name in pwa.ds_files() if name not in pwa.STYLES} <= page                                     # orkUI's faces, heads, marks and pictures
    assert {"fonts/ibm-plex-sans-latin-400-normal.woff2", "races/peon-crown@2x.png", "signs/big/bug.svg", "potion/body.svg"} <= page
    assert {k for k in pwa.files() if k.startswith(pwa.PAGE) and k.endswith((".js", ".mjs", ".css"))} <= page
    assert {"page/board.js", "page/js/link.js", "page/js/hand/upright.js", "page/vendor/preact.mjs", "page/page.css", "roles.css"} <= page
    assert not any("xterm" in k for k in page)


def test_the_service_worker_also_keeps_the_elements_and_the_signs_the_masks_draw():
    sw = (pwa.ROOT / "sw.js").read_text(encoding="utf-8")
    shell = set(re.findall(r'"([^"]+)"', sw[sw.index("const SHELL"):sw.index("];", sw.index("const SHELL"))]))
    assert {k for k in pwa.files() if k.startswith(("elements/", "signs/")) and k.count("/") == 1} <= shell      # (signs/big/ and the rest of orkUI's pictures are kept as they are first drawn)


def test_the_manifest_carries_a_token_only_as_a_token():
    plain = json.loads(_split(pwa.serve("GET", "/app/manifest.webmanifest"))[1])
    assert plain["start_url"] == "./" and plain["display"] == "standalone"
    token = "A" * 43
    with_k = json.loads(_split(pwa.serve("GET", f"/app/manifest.webmanifest?k={token}"))[1])
    assert with_k["start_url"] == f"./#k={token}" and with_k["name"] == plain["name"]
    for bad in ("short", "x" * 43 + '"}', "%22%7D" + "a" * 40):
        assert json.loads(_split(pwa.serve("GET", f"/app/manifest.webmanifest?k={bad}"))[1])["start_url"] == "./"


def test_a_browser_names_its_token_among_the_subprotocols():
    token = "abc_DEF-123" * 4
    assert pwa.ws_token({"sec-websocket-protocol": f"orkcraft.v1, bearer.{token}"}) == token
    assert pwa.ws_token({"sec-websocket-protocol": "orkcraft.v1"}) == ""
    assert pwa.ws_token({"sec-websocket-protocol": "bearer.no spaces"}) == ""
    assert pwa.ws_token({}) == ""
    assert pwa.select(None, ["orkcraft.v1", "bearer.x"]) == "orkcraft.v1" and pwa.select(None, []) is None
    assert pwa.link("https://town.tail1.ts.net:4443", "a/b") == "https://town.tail1.ts.net:4443/app/#pair=a%2Fb"


# -- over the listener ------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_the_listener_serves_the_app_and_a_browsers_socket(fake_repo):
    server, task = await _serve(fake_repo)
    try:
        _, token = await _pair(server)
        status, headers, body = await asyncio.to_thread(_get, server.phones.address, "/app/")
        assert status == 200 and b"Orkboard" in body and "content-security-policy" in headers
        for path, kind in (("/app/page/board.js", "text/javascript"), ("/app/page/vendor/preact.mjs", "text/javascript"), ("/app/roles.css", "text/css"),
                           ("/ds/orkui/races/elf-elder.png", "image/png"), ("/ds/orkui/icons/icons.svg", "image/svg+xml"), ("/app/old.html", "text/html")):
            status, headers, body = await asyncio.to_thread(_get, server.phones.address, path)       # the page's files and orkUI by the page's address, from the listener
            assert status == 200 and kind in headers["content-type"] and body, path
        assert (await asyncio.to_thread(_get, server.phones.address, "/ds/orkui/index.html"))[0] == 404
        assert (await asyncio.to_thread(_get, server.phones.address, "/ds/sprites/orks/ork.png"))[0] == 404     # a camp's pictures are not the phone's
        async with connect(_ws_url(server), ssl=_pinned(), subprotocols=["orkcraft.v1", f"bearer.{token}"]) as ws:
            assert ws.subprotocol == "orkcraft.v1"
            first = json.loads(await asyncio.wait_for(ws.recv(), 5))
            assert first["t"] == "state"
        with pytest.raises(InvalidStatus) as e:
            async with connect(_ws_url(server), ssl=_pinned(), subprotocols=["orkcraft.v1", "bearer." + "x" * 43]):
                pass
        assert e.value.response.status_code == 403
    finally:
        server.stop()
        await asyncio.wait_for(task, 10)


@pytest.mark.asyncio
async def test_the_apps_link_is_offered_only_on_a_tailnet_with_its_certificate(fake_repo, monkeypatch, tmp_path):
    listener = phones.Listener(Orkboard(fake_repo), cert_folder=tmp_path)
    monkeypatch.setattr(phones, "lan_ip", lambda: None)
    listener.tail_find = lambda: tailnet.Tail("127.0.0.1", "")
    try:
        offer = listener.pair()
        assert offer["app_link"] == "" and offer["app_qr"] is None             # no name, no certificate a browser trusts
    finally:
        listener.stop()
    listener.tail_find = lambda: tailnet.Tail("127.0.0.1", "town.tail12.ts.net")
    listener.tail_cert = lambda tail: phone_tls.ensure(tmp_path)             # stands in for `tailscale cert`
    try:
        offer = listener.pair()
        assert listener.tail_trusted
        assert offer["app_link"] == f"{listener.tail_address}/app/#pair={offer['code']}"
        assert offer["app_link"].startswith("https://town.tail12.ts.net:") and offer["app_qr"].startswith("data:image/svg")
    finally:
        listener.stop()


@pytest.mark.asyncio
async def test_a_new_pairing_finds_a_tailnet_that_came_after_the_listener(fake_repo, tmp_path, monkeypatch):
    listener = phones.Listener(Orkboard(fake_repo), cert_folder=tmp_path)
    monkeypatch.setattr(phones, "lan_ip", lambda: "127.0.0.1")               # the LAN, and no Tailscale yet
    listener.bind, listener.tail_find = None, lambda: None
    try:
        first = listener.pair()
        assert first["app_link"] == "" and listener.tail_server is None
        listener.tail_find = lambda: tailnet.Tail("127.0.0.2", "town.tail12.ts.net")   # Tailscale came
        listener.tail_cert = lambda tail: None                                # …without certificates
        assert listener.pair()["app_link"] == "" and listener.tail_server is not None
        listener.tail_cert = lambda tail: phone_tls.ensure(tmp_path)          # …and then they were turned on
        again = listener.pair()
        assert listener.tail_trusted and again["app_link"].startswith("https://town.tail12.ts.net:")
        assert listener.server is not None                                    # the LAN's listener stayed
    finally:
        listener.stop()


# -- Tailscale's state, for the desktop ---------------------------------------------------------------------

def _ran(stdout: str, code: int = 0):
    return lambda argv, **kw: subprocess.CompletedProcess(argv, code, stdout, "")


STATUS = {"BackendState": "Running",
          "Self": {"TailscaleIPs": ["100.64.0.7"], "DNSName": "town.tail12.ts.net.", "UserID": 7},
          "User": {"7": {"LoginName": "orkboss@example.com"}},
          "Peer": {"a": {"HostName": "iphone-15", "OS": "iOS", "Online": False},
                   "b": {"HostName": "pixel", "OS": "android", "Online": True},
                   "c": {"HostName": "nas", "OS": "linux", "Online": True}}}


def test_the_phones_in_the_tailnet_and_the_account_to_log_in_as():
    got = tailnet.phones(_ran(json.dumps(STATUS)))
    assert got == {"account": "orkboss@example.com", "phones": [
        {"name": "pixel", "os": "Android", "online": True}, {"name": "iphone-15", "os": "iOS", "online": False}]}
    assert tailnet.phones(_ran(json.dumps({**STATUS, "BackendState": "Stopped"}))) is None
    assert tailnet.phones(_ran("", 1)) is None
    assert tailnet.find(_ran(json.dumps(STATUS))) == tailnet.Tail("100.64.0.7", "town.tail12.ts.net")


def test_the_desktop_reads_tailscale_at_most_every_few_seconds():
    asked = []

    class L:
        tail_trusted = True

    t = pwa.Tailnet(L(), lambda: asked.append(1) or {"account": "a", "phones": []})
    first = t.read(now=0.0)
    assert first["running"] and first["trusted"] and first["install"] == pwa.INSTALL and first["install_qr"]
    assert first["dns"] == pwa.DNS and first["dns_qr"] and "installed" in first
    t.read(now=1.0)
    assert len(asked) == 1
    t.read(now=pwa.TAIL_S + 0.1)
    assert len(asked) == 2
    assert not pwa.Tailnet(L(), lambda: None).read(now=0.0)["running"]


@pytest.mark.asyncio
async def test_tailscale_that_comes_after_the_town_is_taken_within_a_minute_on_the_same_port(
        fake_repo, tmp_path, monkeypatch):
    listener = phones.Listener(Orkboard(fake_repo), cert_folder=tmp_path)
    monkeypatch.setattr(phones, "lan_ip", lambda: "127.0.0.1")
    listener.bind, listener.tail_find = None, lambda: None
    watch = pwa.TailWatch(listener, every=60.0)
    assert not watch.wanted()                                               # no phone paired: nothing to look for
    listener.pairing.add("Phone")
    try:
        listener.start()                                                    # the town opens; Tailscale is not up yet
        port = listener.pairing.port()
        assert watch.wanted() and listener.tail_server is None
        asked = []
        listener.tail_find = lambda: asked.append(1) or tailnet.Tail("127.0.0.2", "town.tail12.ts.net")
        listener.tail_cert = lambda tail: phone_tls.ensure(tmp_path)
        watch.tick(now=watch._at + 30.0)
        assert not asked                                                    # not before a minute
        watch.tick(now=watch._at + 61.0)
        for _ in range(100):
            if not watch._busy:
                break
            await asyncio.sleep(0.02)
        assert asked and listener.tail_trusted and listener.tail_address == f"https://town.tail12.ts.net:{port}"
        assert not watch.wanted()                                           # done: it looks no more
        assert listener.server is not None                                  # the LAN's listener stayed
    finally:
        listener.stop()



CAMP = re.compile(r':root\[data-(?:look|theme)="camp"\]')


def _rules(css: str) -> list[tuple[str, str]]:
    """`(selector, body)` of each rule of a stylesheet, an @media's own too."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return [(m.group(1).strip(), m.group(2)) for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css)]


def test_the_phone_wears_the_design_system_and_no_camp_file():
    """The app's page loads orkUI (fonts.css, tokens.css, components.css: the desktop's files, design-system/orkui) in its
    office look; every picture a rule of app.css draws is served, no rule of it is Camp's, and Camp's pictures (the fence
    round a window, v4's kit, the HUD's resources: Orkline's) never are."""
    from orkboard.design import tokens

    head, body = _split(pwa.serve("GET", "/app/"))
    assert b'data-look="office"' in body
    for name in ("fonts.css", "tokens.css", "components.css"):
        assert f'href="{name}"'.encode() in body, name
    for name in pwa.STYLES:
        head, body = _split(pwa.serve("GET", f"/app/{name}"))
        assert "text/css" in head and body == (tokens.ORKUI / name).read_bytes(), name
    rules = _rules((pwa.ROOT / "app.css").read_text())
    assert not [sel for sel, _body in rules if any(CAMP.match(part.strip()) for part in sel.split(","))]
    for url in sorted({u for _sel, body in rules for u in re.findall(r'url\("([^"]+)"\)', body)}):
        assert _split(pwa.serve("GET", f"/app/{url}"))[0].startswith("HTTP/1.1 200"), url
    for url in ["fence/row.png", "icons/res-gold.png", "camp/ork-walk.png", "sprites/forge.png", "v3/manifest.json"]:
        assert _split(pwa.serve("GET", f"/app/{url}"))[0].startswith("HTTP/1.1 404"), url


def test_assets_json_lists_every_cache_first_file_with_a_hash(monkeypatch):
    monkeypatch.setattr(pwa, "_ASSETS", pwa._ASSETS)  # the map this test warms up goes with it
    monkeypatch.setattr(pwa, "READY", threading.Event())
    pwa.assets()                                     # the listener's warm-up
    head, body = _split(pwa.serve("GET", "/app/assets.json"))
    assert head.startswith("HTTP/1.1 200") and "application/json" in head
    assert "public, max-age=" not in head
    data = json.loads(body)
    cf_files = {k: v for k, v in pwa.files().items() if pwa.is_cache_first(k)}
    assert set(data.keys()) == set(cf_files.keys())
    for path, h in data.items():
        assert len(h) == 10 and all(c in "0123456789abcdef" for c in h)
        real_hash = hashlib.sha1(cf_files[path].read_bytes()).hexdigest()[:10]
        assert h == real_hash


def test_a_changed_file_changes_its_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(pwa, "_ASSETS", pwa._ASSETS)  # the map this test warms up goes with it
    monkeypatch.setattr(pwa, "READY", threading.Event())
    dummy = tmp_path / "custom.png"
    dummy.write_bytes(b"content_version_one")
    real_files = pwa.files()
    monkeypatch.setattr(pwa, "files", lambda: {**real_files, "sprites/custom.png": dummy})
    h1 = pwa.assets()["sprites/custom.png"]
    assert h1 == hashlib.sha1(b"content_version_one").hexdigest()[:10]

    dummy.write_bytes(b"content_version_two_changed")
    h2 = pwa.assets()["sprites/custom.png"]
    assert h2 == hashlib.sha1(b"content_version_two_changed").hexdigest()[:10]
    assert h1 != h2
    _, body = _split(pwa.serve("GET", "/app/assets.json"))
    assert json.loads(body)["sprites/custom.png"] == h2


def test_a_request_only_reads_the_map_the_warm_up_hashed(tmp_path, monkeypatch):
    """Only the warm-up hashes: a request for assets.json reads the map it kept and touches no file."""
    monkeypatch.setattr(pwa, "_ASSETS", None)
    monkeypatch.setattr(pwa, "READY", threading.Event())   # not warmed: neither the map nor the flag
    head, _ = _split(pwa.serve("GET", "/app/assets.json"))
    assert head.startswith("HTTP/1.1 503")             # not warmed yet: no map rather than a wrong one
    dummy = tmp_path / "custom.png"
    dummy.write_bytes(b"one")
    real_files = pwa.files()
    monkeypatch.setattr(pwa, "files", lambda: {**real_files, "sprites/custom.png": dummy})
    h1 = pwa.assets()["sprites/custom.png"]
    dummy.write_bytes(b"two")
    with monkeypatch.context() as m:
        m.setattr(pwa.hashlib, "sha1", lambda *a: pytest.fail("a request hashed"))
        m.setattr(Path, "stat", lambda *a, **k: pytest.fail("a request looked at a file"))
        _, body = _split(pwa.serve("GET", "/app/assets.json"))
    assert json.loads(body)["sprites/custom.png"] == h1


def test_a_warm_up_that_fails_still_says_it_ended_and_logs_why(monkeypatch, caplog):
    """A request never waits HEAD_S for a warm-up that died: READY is set, the error logged, assets.json a 503."""
    monkeypatch.setattr(pwa, "_ASSETS", None)
    monkeypatch.setattr(pwa, "READY", threading.Event())

    def broken():
        raise RuntimeError("the sprites folder went away")
    monkeypatch.setattr(pwa, "files", broken)
    with caplog.at_level("ERROR", logger=pwa.__name__):
        pwa.assets()
    assert pwa.READY.is_set()
    assert "the sprites folder went away" in caplog.text
    head, _ = _split(pwa.serve("GET", "/app/assets.json"))
    assert head.startswith("HTTP/1.1 503")


def test_the_workers_install_fills_its_cache_past_the_http_cache():
    """A new cache is filled from the town, never from the HTTP cache (its PNGs and fonts are immutable there): the
    install fetches every SHELL file and assets.json with cache "reload", and stores the map."""
    sw = (pwa.ROOT / "sw.js").read_text(encoding="utf-8")
    install = sw[sw.index('addEventListener("install"'):sw.index('addEventListener("activate"')]
    assert "addAll" not in install                    # addAll fetches with the default cache mode
    assert re.search(r'\[\.\.\.new Set\(\[\.\.\.SHELL, \.\.\.PAGE\]\)\]\.map\(async \(path\) => \{\s*const resp = await fetch\(path, \{ cache: "reload" \}\)',
                     install)
    assert 'fetch("assets.json", { cache: "reload" })' in install
    assert 'put("assets.json"' in install


def test_service_worker_names_cache_version_and_cache_first_prefixes():
    sw = (pwa.ROOT / "sw.js").read_text(encoding="utf-8")
    assert "orkcraft-app-v104" in sw
    prefixes = sw[sw.index("CACHE_PREFIXES = ["):sw.index("];", sw.index("CACHE_PREFIXES = ["))]
    assert set(re.findall(r'"([^"]+)"', prefixes)) == set(pwa.CACHE_PREFIXES) == {"fonts/"}


def test_the_worker_never_keeps_a_picks_files_network_only():
    """Pick one (docs/specs/51-pick-one.md §3): `/media/…` is asked of the town every time, never answered by the worker and never kept: its fetch handler lets the request go first of all (the
    browser asks the town itself, with its Range requests), and neither the shell nor a precache can hold one."""
    sw = (pwa.ROOT / "sw.js").read_text(encoding="utf-8")
    fetch = sw[sw.index('addEventListener("fetch"'):sw.index('addEventListener("message"')]
    guard = fetch.index("isMedia(e.request.url)")
    assert re.search(r"isMedia\(e\.request\.url\)\) return;", fetch) and guard < fetch.index("respondWith") and guard < fetch.index("caches.open")   # before anything that answers or keeps
    assert '"/media/"' in sw[sw.index("const isMedia"):sw.index('addEventListener("fetch"')]
    shell = sw[sw.index("const SHELL"):sw.index("];", sw.index("const SHELL"))]
    assert "media/" not in shell                                                                    # nothing of the shell is a pick's file
    message = sw[sw.index('addEventListener("message"'):sw.index('addEventListener("push"')]
    assert "!isMedia(path)" in message and message.index("!isMedia(path)") < message.index("fetch(path")      # a precache asked for one fetches none
    assert pwa.wants("/media/dark-mode/k1-r1/a.png") is False                                       # and the app's address space has none of them: they are the listener's own route


def test_cache_control_headers_for_cache_first_and_shell():
    for path in ("/app/fonts/ibm-plex-mono-latin-400-normal.woff2", "/app/races/peon-warrior.png"):
        head_cf, _ = _split(pwa.serve("GET", path))
        assert "Cache-Control: public, max-age=31536000, immutable" in head_cf, path
    head_shell, _ = _split(pwa.serve("GET", "/app/board-app.js"))
    assert "Cache-Control: no-cache" in head_shell
    head_html, _ = _split(pwa.serve("GET", "/app/"))
    assert "Cache-Control: no-cache" in head_html
    head_assets, _ = _split(pwa.serve("GET", "/app/assets.json"))
    assert "Cache-Control: no-cache" in head_assets


def test_the_worker_shows_every_push_and_a_tap_opens_the_pushs_address():
    sw = (pwa.ROOT / "sw.js").read_text(encoding="utf-8")
    push = sw[sw.index('addEventListener("push"'):sw.index('addEventListener("notificationclick"')]
    assert "showNotification(" in push and "if (" not in push.split("e.waitUntil")[1].split("showNotification")[0]      # nothing decides whether it shows
    assert "tag" in push and "data: { url" in push and "setAppBadge" in push and "clearAppBadge" in push and 'icon: "icon-192.png"' in push
    click = sw[sw.index('addEventListener("notificationclick"'):]
    assert "e.notification.data" in click and "openWindow(target)" in click and "from=push-" in click and "all[0].focus()" in click


def _call_args(text: str, start: int) -> list[str]:
    """The arguments of the call whose `(` ends at `start`, split at its own commas (not those of what they hold)."""
    args, depth, cur, quote, i = [], 0, "", None, start
    while i < len(text):
        c = text[i]
        if quote:
            cur += c
            if c == "\\":
                cur += text[i + 1]
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote, cur = c, cur + c
        elif c in "([{":
            depth, cur = depth + 1, cur + c
        elif c in ")]}":
            if depth == 0:
                return [*args, cur]
            depth, cur = depth - 1, cur + c
        elif c == "," and depth == 0:
            args, cur = [*args, cur], ""
        else:
            cur += c
        i += 1
    return [*args, cur]


def test_no_child_handed_to_the_page_can_be_null():
    """`replaceChildren`, `append` and `prepend` write a null as the word "null" (the owner saw it under *The party*, under Takes and in a failed
    operation's sheet): an argument that may be null (`a ? b : null`, `a ? null : b`, `a || null`, `a && b`) is filtered first, `...[…].filter(Boolean)`."""
    found = []
    for name, path in pwa.files().items():
        if not name.endswith(".js"):
            continue
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"\.(?:replaceChildren|append|prepend)\(", text):
            for arg in _call_args(text, m.end()):
                top, depth = "", 0
                for c in arg:
                    if c in "([{":
                        depth += 1
                    elif c in ")]}":
                        depth -= 1
                    elif depth == 0:
                        top += c
                if re.search(r"\?.*:\s*null\s*$|\?\s*null\s*:|\|\|\s*null\s*$|&&", top.strip()):
                    found.append(f"{name}:{text[:m.start()].count(chr(10)) + 1}")
    assert not found, found
