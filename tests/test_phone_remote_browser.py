"""The phone's way through the project's remote (docs/specs/136 C, decisions §243), in a real browser at 390 × 844 with touch, the installed app's frame (tests/test_pwa_frame_browser.py's `App`)
against a GitHub that is a stand-in (`FakeGitHub`, a route on https://api.github.com: no network). The repository and its token in the crown's menu and, before pairing, in the first card, the
lines of §243.7 word for word, a public repository and a token that cannot write refused, the token sent to GitHub's API alone, forgotten by Remove. Screenshots to $REMOTE_SHOTS when it is set."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.gui import pwa  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_pwa_frame_browser import DEVICE, App  # noqa: E402

pytestmark = pytest.mark.browser

SLOW_MS = 120_000
SHOTS = Path(os.environ["REMOTE_SHOTS"]) if os.environ.get("REMOTE_SHOTS") else None
TOKEN = "github_pat_" + "x" * 30
CAN = ("This token can change any file of the repository, the code too; Orkboard writes only orkboard/inbox. Make one for this repository alone, with Contents: read and write. "
       "A rule on main that asks for a pull request keeps the code safe.")
KEPT = "Kept on this phone in the app's storage; the app from the store will keep it in the phone's keychain."
READY = "Ready: goals go through orkboard/inbox when your computer cannot be reached"
PUBLIC = "This repository is public: goals sent through it would be seen by everyone. Make it private, or use the phone at home."


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


class FakeGitHub:
    """GitHub's REST API for one repository, in memory: the repository's flags, the journal's `status.json` with its ETag, the inbox branch and its files, the limits."""

    def __init__(self, repo="me/shop"):
        self.repo, self.private, self.push = repo, True, True
        self.journal: dict | None = None            # status.json
        self.etag = 'W/"1"'
        self.branch = False                         # orkboard/inbox exists
        self.files: dict[str, bytes] = {}           # inbox path -> bytes
        self.requests: list[dict] = []
        self.limit = 0                              # epoch seconds: every call answers 403 with no calls left, until then
        self.status = 0                             # a status every call answers (401), 0 for none
        self.conflicts = 0                          # the next PUTs that answer 409
        self.down = False                           # the network is gone

    def attach(self, ctx):
        ctx.route("https://api.github.com/**", self.route)
        return self

    def route(self, route):
        req = route.request
        url = urlsplit(req.url)
        path = unquote(url.path)
        body = json.loads(req.post_data) if req.post_data else None
        head = {"access-control-allow-origin": "*", "access-control-allow-headers": "*", "access-control-allow-methods": "GET, POST, PUT, OPTIONS",
                "access-control-expose-headers": "etag, x-ratelimit-remaining, x-ratelimit-reset"}
        if req.method == "OPTIONS":
            route.fulfill(status=204, headers=head)
            return
        self.requests.append({"method": req.method, "path": path, "query": url.query, "body": body, "headers": req.headers})
        if self.down:
            route.abort("internetdisconnected")
            return

        def send(status, doc=None, extra=None, raw=None):
            text = raw if raw is not None else (json.dumps(doc) if doc is not None else "")
            route.fulfill(status=status, body=text, headers={**head, "content-type": "application/json", **(extra or {})})

        if self.limit:
            send(403, {"message": "API rate limit exceeded"}, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(self.limit)})
            return
        if self.status:
            send(self.status, {"message": "Bad credentials"})
            return
        root = f"/repos/{self.repo}"
        if not path.startswith(root):
            send(404, {"message": "Not Found"})
            return
        rest = path[len(root):]
        if req.method == "GET" and rest == "":
            send(200, {"full_name": self.repo, "private": self.private, "permissions": {"push": self.push, "pull": True}})
        elif req.method == "GET" and rest == "/contents/status.json":
            if self.journal is None:
                send(404, {"message": "Not Found"})
            elif req.headers.get("if-none-match") == self.etag:
                send(304, extra={"etag": self.etag})
            else:
                send(200, extra={"etag": self.etag}, raw=json.dumps(self.journal))
        elif req.method == "GET" and rest == "/git/ref/heads/orkboard/inbox":
            send(200, {"ref": "refs/heads/orkboard/inbox"}) if self.branch else send(404, {"message": "Not Found"})
        elif req.method == "POST" and rest == "/git/commits":
            send(201, {"sha": "c" * 40})
        elif req.method == "POST" and rest == "/git/refs":
            self.branch = True
            send(201, {"ref": body["ref"]})
        elif req.method == "PUT" and rest.startswith("/contents/inbox/"):
            if not self.branch:
                send(404, {"message": "Branch orkboard/inbox not found"})
            elif self.conflicts:
                self.conflicts -= 1
                send(409, {"message": "is at abc but expected def"})
            elif rest[len("/contents/"):] in self.files:
                send(422, {"message": 'Invalid request.\n\n"sha" wasn\'t supplied.'})
            else:
                assert body["branch"] == "orkboard/inbox"
                self.files[rest[len("/contents/"):]] = base64.b64decode(body["content"])
                send(201, {"content": {"path": rest[len("/contents/"):]}})
        else:
            send(404, {"message": "Not Found"})

    def inbox(self, suffix=".json") -> dict[str, dict]:
        """The goals written, by path."""
        return {p: json.loads(b) for p, b in self.files.items() if p.endswith(suffix) and not p.endswith(".answer.json" if suffix == ".json" else "-")}


class Listener:
    """The phone listener's files (`pwa.serve`) on a plain local port: the app's few hundred modules come at network speed instead of through the browser's route one by one."""

    def __init__(self):
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                head, _, body = pwa.serve("GET", self.path).partition(b"\r\n\r\n")
                lines = head.decode("ascii").split("\r\n")
                self.send_response(int(lines[0].split()[1]))
                for line in lines[1:]:
                    k, _, v = line.partition(": ")
                    if k.lower() not in ("content-length", "connection"):
                        self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.origin = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


class RemoteApp(App):
    """The installed app with GitHub stood in; its pairing answer names the computer's repository."""

    def __init__(self, browser, origin, host=None, repo="me/shop"):
        super().__init__(browser, origin, host)
        self.ctx.unroute("**/app/**")                  # the files come from the listener itself
        self.ctx.unroute("**/ds/orkui/**")
        self.github = FakeGitHub(repo).attach(self.ctx)
        self.remote = repo
        self.pg.set_default_timeout(SLOW_MS)

    def ready(self):
        """The page up: the app's files come one by one through the stand-in listener, which a slow machine takes half a minute over."""
        self.pg.wait_for_selector("[data-frame][data-upright='1']", timeout=SLOW_MS)
        return self.pg

    def pair(self, route):
        self.paired.append(json.loads(route.request.post_data))
        route.fulfill(status=200, content_type="application/json", body=json.dumps({"id": DEVICE["id"], "token": DEVICE["token"], "name": DEVICE["name"], "remote": self.remote}))

    def stored(self, key="orkcraft.remote"):
        raw = self.pg.evaluate("(k) => localStorage.getItem(k)", key)
        return json.loads(raw) if raw else None

    def foreign(self):
        """Every request the page made that was neither the app's own nor GitHub's API."""
        return [r for r in self.requests if not r.startswith((self.origin, "https://api.github.com", "data:", "blob:", "wss://"))]


@pytest.fixture(scope="module")
def listener():
    one = Listener()
    yield one
    one.server.shutdown()


@pytest.fixture
def app(gui, listener):
    server, browser = gui
    one = RemoteApp(browser, listener.origin)
    one.requests = []
    one.pg.on("request", lambda r: one.requests.append(r.url))
    yield one
    one.close()


def open_settings(app):
    """Paired, the page up, the crown's menu open and *Your repository* opened in it."""
    app.keep_pairing()
    pg = app.open()
    app.ready()
    pg.get_by_role("button", name="The leaders and their goals", exact=True).click()
    pg.get_by_role("button", name="Your repository").click()
    pg.locator(".remote-settings").wait_for()
    return pg


def row_state(pg):
    return pg.get_by_role("button", name="Your repository").locator(".up-phone__state").inner_text()


def fill(pg, repo="me/shop", token=TOKEN):
    pg.locator(".remote-settings input[name=repo]").fill(repo)
    pg.locator(".remote-settings input[name=token]").fill(token)
    pg.get_by_role("button", name="Check and keep").click()


def test_the_crowns_menu_takes_the_repository_and_the_token_and_says_what_the_token_can_do(app):
    pg = open_settings(app)
    box = pg.locator(".remote-settings")
    assert box.locator("input[name=token]").get_attribute("type") == "password"
    texts = box.locator(".remote-say").all_inner_texts()
    assert texts == [CAN, KEPT], "the two lines of decisions §243.7, word for word"
    assert row_state(pg) == "Not set"
    assert box.get_by_role("button", name="Remove").is_hidden(), "nothing to remove before a token is kept"
    assert box.locator("input[name=repo]").input_value() == "", "no repository named before pairing's answer: the fixture's computer has none"
    shot(pg, "settings-empty")
    fill(pg)
    box.locator(".remote-line", has_text=READY).wait_for()
    kept = app.stored()
    assert (kept["repo"], kept["token"]) == ("me/shop", TOKEN)
    assert row_state(pg) == "Set"
    assert box.locator("input[name=token]").input_value() == "", "the token is typed once and not shown again"
    assert box.get_by_role("button", name="Remove").is_visible()
    check = [r for r in app.github.requests if r["method"] == "GET"]
    assert [r["path"] for r in check] == ["/repos/me/shop"] and check[0]["headers"]["authorization"] == f"Bearer {TOKEN}"
    assert app.foreign() == [], app.foreign()
    narrow_sideways(pg)
    shot(pg, "settings-ready")
    assert not app.errors, "\n".join(app.errors)


def narrow_sideways(pg):
    from tests import narrow
    pg.wait_for_timeout(500)                      # the sheet has slid in
    narrow.no_sideways(pg)


def test_a_public_repository_and_a_token_that_cannot_write_are_refused_and_the_token_is_not_kept(app):
    pg = open_settings(app)
    app.github.private = False
    fill(pg)
    pg.locator(".remote-line.is-bad", has_text=PUBLIC).wait_for()
    assert app.stored() is None or not app.stored().get("token")
    shot(pg, "settings-public")
    app.github.private, app.github.push = True, False
    pg.get_by_role("button", name="Check and keep").click()
    pg.locator(".remote-line.is-bad", has_text="This token cannot write to the repository").wait_for()
    assert not (app.stored() or {}).get("token")
    app.github.push, app.github.status = True, 401
    pg.get_by_role("button", name="Check and keep").click()
    pg.locator(".remote-line.is-bad", has_text="The token was refused: give a new one in Settings").wait_for()
    assert not (app.stored() or {}).get("token")
    assert [e for e in app.errors if "api.github.com" not in e] == [], "the browser's own note of the 401 is the only noise"






