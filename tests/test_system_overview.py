"""Spec 90 E1 (docs/specs/90-what-the-first-look-said.md §6.1–§6.6): System as the project's architecture, read from the files with no
model. The owner's party game as the model case (a Vite and React client, an Express and Socket.IO server, a config both use): its three
containers, their stacks, the HTTP and socket link with its routes and events, the ways in, the layers, the shared part; a Python project
as one container; nothing read in skipped folders; a file over the limit never read."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import code_map, stacks_known, system_overview


def write(root: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8")
    return root


GAME = {
    "package.json": json.dumps({"name": "party", "private": True, "workspaces": ["client", "server"],
                                "scripts": {"dev": "concurrently \"npm:dev -w client\" \"npm:dev -w server\""},
                                "devDependencies": {"concurrently": "^8.2.0"}}),
    "config/balance.ts": "export const BALANCE = { rounds: 5, seconds: 30 };\n",
    "client/package.json": json.dumps({"name": "client", "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
                                       "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1", "socket.io-client": "^4.7.5",
                                                        "left-pad": "1.3.0"},
                                       "devDependencies": {"vite": "^5.4.0", "@vitejs/plugin-react": "^4.3.1", "@types/react": "^18"}}),
    "client/index.html": "<!doctype html><div id=root></div><script type=module src=/src/main.tsx></script>\n",
    "client/vite.config.ts": "import { defineConfig } from 'vite';\nexport default defineConfig({ server: { proxy: { '/api': 'http://localhost:3000' } } });\n",
    "client/src/main.tsx": "import { App } from './App';\nApp();\n",
    "client/src/App.tsx": "import { TvView } from './views/TvView';\nimport { PlayerView } from './views/PlayerView';\n"
                          "import { JudgeView } from './views/JudgeView';\nexport const App = () => [TvView, PlayerView, JudgeView];\n",
    "client/src/views/TvView.tsx": "import { socket } from '../net/socket';\nsocket.on('state', (s) => s);\nexport const TvView = 1;\n",
    "client/src/views/PlayerView.tsx": "import { BALANCE } from '../../../config/balance';\nimport { join, room } from '../net/api';\n"
                                       "export const PlayerView = () => [BALANCE.rounds, join, room];\n",
    "client/src/views/JudgeView.tsx": "import { socket } from '../net/socket';\nexport const JudgeView = () => socket.emit('answer', 2);\n",
    "client/src/net/socket.ts": "import { io } from 'socket.io-client';\nexport const socket = io();\n"
                                "socket.on('connect', () => socket.emit('join', { name: 'ann' }));\n",
    "client/src/net/api.ts": "import axios from 'axios';\nconst api = axios.create({ baseURL: '' });\n"
                             "export const join = () => fetch('/api/rooms', { method: 'POST' });\n"
                             "export const room = (code) => fetch(`/api/rooms/${code}`);\n"
                             "export const health = () => api.get('/api/health');\n"
                             "export const weather = () => fetch('https://weather.example.com/today');\n",
    "server/package.json": json.dumps({"name": "server", "main": "src/index.ts", "scripts": {"dev": "tsx watch src/index.ts",
                                                                                      "start": "node dist/index.js"},
                                       "dependencies": {"express": "^4.19.2", "socket.io": "^4.7.5", "nanoid": "^5.0.0"},
                                       "devDependencies": {"@types/express": "^4"}}),
    "server/src/index.ts": "import express from 'express';\nimport { createServer } from 'http';\nimport { Server } from 'socket.io';\n"
                           "import { rooms } from './routes/rooms';\nimport { tick } from './timeline';\n"
                           "const app = express();\napp.use('/api', rooms);\napp.get('/api/health', (_q, r) => r.send('ok'));\n"
                           "const http = createServer(app);\nconst io = new Server(http);\n"
                           "io.on('connection', (socket) => {\n  socket.on('join', (p) => io.to(p.room).emit('state', tick()));\n"
                           "  socket.on('answer', () => socket.emit('welcome'));\n});\nhttp.listen(process.env.PORT || 3000);\n",
    "server/src/timeline.ts": "import { BALANCE } from '../../config/balance';\nimport { score } from './balance';\n"
                              "export const tick = () => score(BALANCE.rounds);\n",
    "server/src/balance.ts": "export const score = (n) => n * 2;\n",
    "server/src/routes/rooms.ts": "import { Router } from 'express';\nimport { tick } from '../timeline';\nimport { save } from '../db/store';\n"
                                  "export const rooms = Router();\nrooms.post('/rooms', (_q, r) => r.json(save(tick())));\n"
                                  "rooms.get('/rooms/:code', (_q, r) => r.json({}));\nrooms.delete('/rooms/:code', (_q, r) => r.end());\n",
    "server/src/db/store.ts": "export const save = (x) => x;\n",
}


@pytest.fixture
def game(tmp_path: Path) -> Path:
    return write(tmp_path / "party", GAME)


def by_path(got: dict) -> dict[str, dict]:
    return {c["path"]: c for c in got["containers"]}


def test_the_party_game_is_three_containers_each_with_its_stack(game):
    got = system_overview.read(game)
    assert set(got) == {"containers", "links", "shared"}
    cs = by_path(got)
    assert list(cs) == [".", "client", "server"] and [c["name"] for c in got["containers"]] == ["Root", "client", "server"]
    assert cs["client"]["manifests"] == ["package.json"] and cs["."]["manifests"] == ["package.json"]
    assert cs["client"]["stack"] == [{"name": "React", "role": "UI"}, {"name": "socket.io-client", "role": "realtime"},
                                     {"name": "Vite", "role": "build"}]
    assert cs["server"]["stack"] == [{"name": "Express", "role": "server"}, {"name": "Socket.IO", "role": "realtime"}]
    assert cs["client"]["unknown"] == 1 and cs["server"]["unknown"] == 1          # left-pad, nanoid: counted, not named; @types/ neither
    assert cs["."]["stack"] == [{"name": "concurrently", "role": "build"}]
    assert cs["client"]["parts"] == ["client", "client/src", "client/src/net", "client/src/views"]
    assert cs["server"]["parts"] == ["server/src", "server/src/db", "server/src/routes"] and cs["."]["parts"] == ["config"]


def test_the_client_calls_and_the_server_answers_one_link_with_its_routes_and_events(game):
    links = system_overview.read(game)["links"]
    assert len(links) == 1
    link, = links
    assert (link["from"], link["to"]) == ("client", "server")
    assert [(r["method"], r["path"]) for r in link["http"]] == [("GET", "/api/health"), ("POST", "/api/rooms"), ("GET", "/api/rooms/:code")]
    rooms = next(r for r in link["http"] if r["method"] == "POST")
    assert rooms["called_in"] == "client/src/net/api.ts" and rooms["answered_in"] == "server/src/routes/rooms.ts"
    assert link["socket"] == [
        {"event": "answer", "way": "out", "emitted_in": "client/src/views/JudgeView.tsx", "handled_in": "server/src/index.ts"},
        {"event": "join", "way": "out", "emitted_in": "client/src/net/socket.ts", "handled_in": "server/src/index.ts"},
        {"event": "state", "way": "back", "emitted_in": "server/src/index.ts", "handled_in": "client/src/views/TvView.tsx"}]


def test_the_ways_in_a_page_a_main_a_listen_and_the_scripts(game):
    cs = by_path(system_overview.read(game))
    assert cs["client"]["ways_in"] == [{"kind": "page", "name": "", "path": "client/index.html"},
                                       {"kind": "script", "name": "dev", "path": "client/package.json"},
                                       {"kind": "script", "name": "build", "path": "client/package.json"}]
    assert cs["server"]["ways_in"] == [{"kind": "main", "name": "", "path": "server/src/index.ts"},
                                       {"kind": "script", "name": "dev", "path": "server/package.json"},
                                       {"kind": "script", "name": "start", "path": "server/package.json"},
                                       {"kind": "listen", "name": "", "path": "server/src/index.ts"}]
    assert cs["."]["ways_in"] == [{"kind": "script", "name": "dev", "path": "package.json"}]


def test_the_layers_by_the_imports_and_the_folders_roles(game):
    cs = by_path(system_overview.read(game))
    assert cs["client"]["layers"] == [{"role": "", "parts": ["client", "client/src"]}, {"role": "face", "parts": ["client/src/views"]},
                                      {"role": "", "parts": ["client/src/net"]}]
    assert cs["server"]["layers"] == [{"role": "", "parts": ["server/src"]}, {"role": "doors", "parts": ["server/src/routes"]},
                                      {"role": "data", "parts": ["server/src/db"]}]
    assert cs["."]["layers"] == [{"role": "settings", "parts": ["config"]}]


def test_the_config_both_use_is_shared(game):
    assert system_overview.read(game)["shared"] == [{"path": "config", "container": ".", "containers": ["client", "server"],
                                                     "used_by": ["client/src/views", "server/src"]}]


def test_a_part_imported_by_an_alias_is_shared_too(game):
    write(game, {"client/src/views/PlayerView.tsx": "import { BALANCE } from '@config/balance';\nexport const PlayerView = BALANCE;\n"})
    shared, = system_overview.read(game)["shared"]
    assert shared["path"] == "config" and shared["containers"] == ["client", "server"]


def test_with_no_manifest_at_the_root_its_own_code_is_the_root_container(game):
    (game / "package.json").unlink()
    cs = by_path(system_overview.read(game))
    assert list(cs) == [".", "client", "server"] and cs["."]["manifests"] == [] and cs["."]["parts"] == ["config"]


def test_a_python_project_is_one_container(tmp_path):
    root = write(tmp_path / "shop", {
        "pyproject.toml": '[project]\nname = "shop"\ndependencies = ["Flask>=3", "Flask_SQLAlchemy", "tiny-thing==1"]\n'
                          '[project.optional-dependencies]\ndev = ["pytest"]\n[project.scripts]\nshop = "shop.cli:main"\n',
        "shop/__init__.py": "",
        "shop/__main__.py": "from shop import app\napp.run()\n",
        "shop/app.py": "from flask import Flask\nfrom shop.routes import items\napp = Flask(__name__)\n",
        "shop/routes/__init__.py": "",
        "shop/routes/items.py": "from shop.models import item\n@bp.route('/items/<int:n>', methods=['GET', 'DELETE'])\ndef one(n): ...\n",
        "shop/models/__init__.py": "",
        "shop/models/item.py": "X = 1\n",
        "tests/test_items.py": "from shop.routes import items\n",
    })
    got = system_overview.read(root)
    c, = got["containers"]
    assert (c["path"], c["name"], c["manifests"]) == (".", "Root", ["pyproject.toml"])
    assert c["stack"] == [{"name": "Flask", "role": "server"}, {"name": "SQLAlchemy", "role": "data"}, {"name": "pytest", "role": "test"}]
    assert c["unknown"] == 1
    assert {"kind": "bin", "name": "shop", "path": "shop.cli:main"} in c["ways_in"]
    assert {"kind": "listen", "name": "", "path": "shop/__main__.py"} in c["ways_in"]
    assert [l["role"] for l in c["layers"]] == ["", "doors", "data"]
    assert got["links"] == [] and got["shared"] == []


def test_nothing_in_skipped_folders_is_read(game):
    write(game, {
        "node_modules/socket.io/package.json": json.dumps({"name": "socket.io", "dependencies": {"ws": "8"}}),
        "client/node_modules/react/package.json": json.dumps({"name": "react"}),
        "client/node_modules/react/index.js": "app.get('/from-modules', f);\n",
        "dist/package.json": json.dumps({"name": "built"}),
        "build/server.js": "app.get('/api/built', f);\n",
        ".cache/tool/package.json": json.dumps({"name": "hidden"}),
        "server/.env": "SECRET=1\n",
        "client/src/net/more.ts": "fetch('/from-modules'); fetch('/api/built');\n",
    })
    got = system_overview.read(game)
    assert [c["path"] for c in got["containers"]] == [".", "client", "server"]
    assert {r["path"] for r in got["links"][0]["http"]} == {"/api/health", "/api/rooms", "/api/rooms/:code"}


def test_a_file_over_the_limit_is_never_read(game):
    big = "app.get('/huge', f);\nio.on('connection', (s) => s.on('huge', f));\n" + "// pad\n" * (code_map.MAX_BYTES // 7 + 10)
    write(game, {"server/src/huge.ts": big, "client/src/net/huge.ts": "fetch('/huge');\nsocket.emit('huge');\n"})
    link, = system_overview.read(game)["links"]
    assert "/huge" not in {r["path"] for r in link["http"]} and "huge" not in {e["event"] for e in link["socket"]}


def test_a_changed_manifest_or_page_matters_and_a_note_does_not():
    assert all(map(system_overview.matters, ["client/package.json", "go.mod", "client/index.html", "a/b.tsx", "requirements.txt"]))
    assert not any(map(system_overview.matters, ["README.md", "notes/plan.txt", "art/hero.png"]))


def test_the_known_list_names_a_few_hundred_packages_and_the_folders_roles():
    assert len(stacks_known.LIBS) >= 300
    assert {role for _name, role in stacks_known.LIBS.values()} == set(stacks_known.STACK_ROLES)
    assert stacks_known.lib("react-dom") == stacks_known.lib("react") == ("React", "UI")
    assert stacks_known.lib("Flask_SQLAlchemy", "pypi") == ("SQLAlchemy", "data")
    assert stacks_known.lib("github.com/labstack/echo/v5", "go") == ("Echo", "server")
    assert stacks_known.lib("no-such-thing") is None
    assert {stacks_known.ROLES[f] for f in ("views", "pages", "screens", "components", "ui")} == {"face"}
    assert {stacks_known.ROLES[f] for f in ("routes", "api", "controllers", "handlers")} == {"doors"}
    assert {stacks_known.ROLES[f] for f in ("db", "models", "store", "schema", "repositories")} == {"data"}
    assert {stacks_known.ROLES[f] for f in ("config", "settings")} == {"settings"}
    assert set(stacks_known.ROLES.values()) == set(stacks_known.FOLDER_ROLES)


def test_owner_is_the_deepest_container():
    paths = [".", "apps/web", "apps"]
    assert system_overview.owner("apps/web/src", paths) == "apps/web"
    assert system_overview.owner("apps/api", paths) == "apps" and system_overview.owner("lib", paths) == "."
    assert system_overview.owner("lib", ["client"]) is None


def test_a_web_client_and_a_python_api_are_linked_route_by_route(tmp_path):
    root = write(tmp_path / "shop", {
        "web/package.json": json.dumps({"dependencies": {"vue": "3", "axios": "1"}}),
        "web/src/api.js": "import axios from 'axios';\n"
                          "export const add = (id) => axios.post(`${BASE}/v1/items/${id}`, {});\nexport const all = () => fetch('/v1/items');\n",
        "api/pyproject.toml": '[project]\nname = "api"\ndependencies = ["fastapi", "uvicorn[standard]>=0.30"]\n',
        "api/app/main.py": "from fastapi import FastAPI\nfrom app.routes import items\napp = FastAPI()\n"
                           "app.include_router(items.router, prefix='/v1')\n",
        "api/app/routes/items.py": "router = APIRouter()\n@router.post('/items/{item_id}')\ndef add(item_id: int): ...\n"
                                   "@router.get('/items')\ndef all(): ...\n@router.delete('/items/{item_id}')\ndef drop(item_id: int): ...\n",
    })
    got = system_overview.read(root)
    assert [(c["path"], [s["name"] for s in c["stack"]]) for c in got["containers"]] == [
        ("api", ["FastAPI", "Uvicorn"]), ("web", ["Vue", "axios"])]
    link, = got["links"]
    assert (link["from"], link["to"], link["socket"]) == ("web", "api", [])
    assert [(r["method"], r["path"]) for r in link["http"]] == [("GET", "/v1/items"), ("POST", "/v1/items/{item_id}")]
