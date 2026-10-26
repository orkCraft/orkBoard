"""What realm/system_overview.py knows by name (docs/specs/90-what-the-first-look-said.md §6.2, §6.5; decisions §105.6): the well-known
packages of npm, PyPI, Go and Cargo with the name a person knows them by and their role in a container's stack, and the folder names
that say a part's role in its container's layers. A list, read once; no model, no face, nothing fetched.

    LIBS["react"]          # ("React", "UI")
    LIBS["socket.io"]      # ("Socket.IO", "realtime")
    lib("Flask_SQLAlchemy")  # ("SQLAlchemy", "data"): a name as its registry spells it, matched as the registry would
    ROLES["views"]         # "face"

A package's roles: *UI*, *server*, *realtime*, *data*, *build*, *test*, *game*. Packages a person knows as one (`react`, `react-dom`)
share their name, so a stack names it once. A folder's roles: `face`, `doors`, `data`, `settings`.
"""
from __future__ import annotations

import re

STACK_ROLES = ("UI", "server", "realtime", "data", "game", "build", "test")      # the order a stack is read in

# Each line: the package as its registry spells it (lower case), then the name a person knows it by.
_KNOWN = {
    "UI": """
        react React
        react-dom React
        react-native React Native
        expo Expo
        next Next.js
        gatsby Gatsby
        remix Remix
        @remix-run/react Remix
        vue Vue
        nuxt Nuxt
        @angular/core Angular
        svelte Svelte
        @sveltejs/kit SvelteKit
        solid-js Solid
        preact Preact
        lit Lit
        alpinejs Alpine.js
        jquery jQuery
        htmx.org htmx
        astro Astro
        @builder.io/qwik Qwik
        ember-source Ember
        backbone Backbone
        react-router React Router
        react-router-dom React Router
        @tanstack/react-router TanStack Router
        vue-router Vue Router
        tailwindcss Tailwind CSS
        bootstrap Bootstrap
        @mui/material MUI
        @chakra-ui/react Chakra UI
        antd Ant Design
        @mantine/core Mantine
        styled-components styled-components
        @emotion/react Emotion
        sass Sass
        framer-motion Framer Motion
        @radix-ui/react-dialog Radix UI
        @headlessui/react Headless UI
        lucide-react Lucide
        react-icons React Icons
        d3 D3
        chart.js Chart.js
        recharts Recharts
        echarts ECharts
        @reduxjs/toolkit Redux
        redux Redux
        zustand Zustand
        mobx MobX
        jotai Jotai
        recoil Recoil
        pinia Pinia
        vuex Vuex
        @tanstack/react-query TanStack Query
        swr SWR
        react-hook-form React Hook Form
        formik Formik
        i18next i18next
        react-i18next i18next
        electron Electron
        @tauri-apps/api Tauri
        streamlit Streamlit
        gradio Gradio
        textual Textual
        rich Rich
        tkinter Tkinter
        pyqt5 PyQt
        pyqt6 PyQt
        pyside6 PySide
        kivy Kivy
        flet Flet
        nicegui NiceGUI
        jinja2 Jinja
        yew Yew
        leptos Leptos
        dioxus Dioxus
        egui egui
        eframe egui
        iced iced
        tauri Tauri
        github.com/a-h/templ templ
        fyne.io/fyne/v2 Fyne
    """,
    "server": """
        express Express
        koa Koa
        @koa/router Koa
        fastify Fastify
        hapi hapi
        @hapi/hapi hapi
        @nestjs/core NestJS
        @nestjs/common NestJS
        restify restify
        hono Hono
        elysia Elysia
        @trpc/server tRPC
        @trpc/client tRPC
        apollo-server Apollo Server
        @apollo/server Apollo Server
        @apollo/client Apollo Client
        graphql GraphQL
        graphql-yoga GraphQL Yoga
        axios axios
        node-fetch node-fetch
        ky ky
        got got
        cors cors
        body-parser body-parser
        cookie-parser cookie-parser
        helmet Helmet
        express-session express-session
        passport Passport
        jsonwebtoken jsonwebtoken
        bcrypt bcrypt
        bcryptjs bcrypt
        multer Multer
        morgan morgan
        http-proxy-middleware http-proxy-middleware
        nodemailer Nodemailer
        @aws-sdk/client-s3 AWS SDK
        aws-sdk AWS SDK
        firebase Firebase
        firebase-admin Firebase
        @supabase/supabase-js Supabase
        stripe Stripe
        dotenv dotenv
        winston winston
        pino pino
        zod Zod
        joi Joi
        yup Yup
        flask Flask
        django Django
        djangorestframework Django REST framework
        fastapi FastAPI
        starlette Starlette
        uvicorn Uvicorn
        gunicorn Gunicorn
        hypercorn Hypercorn
        aiohttp aiohttp
        tornado Tornado
        sanic Sanic
        bottle Bottle
        falcon Falcon
        quart Quart
        litestar Litestar
        pyramid Pyramid
        requests Requests
        httpx HTTPX
        pydantic Pydantic
        celery Celery
        dramatiq Dramatiq
        rq RQ
        boto3 AWS SDK
        grpcio gRPC
        @grpc/grpc-js gRPC
        github.com/gin-gonic/gin Gin
        github.com/labstack/echo/v4 Echo
        github.com/gofiber/fiber/v2 Fiber
        github.com/go-chi/chi/v5 chi
        github.com/gorilla/mux gorilla/mux
        google.golang.org/grpc gRPC
        github.com/spf13/cobra Cobra
        github.com/spf13/viper Viper
        actix-web Actix Web
        axum Axum
        rocket Rocket
        warp warp
        hyper hyper
        tower tower
        tonic tonic
        reqwest reqwest
        tokio Tokio
        async-std async-std
        serde serde
        serde-json serde
        clap clap
        tracing tracing
    """,
    "realtime": """
        socket.io Socket.IO
        socket.io-client socket.io-client
        @socket.io/redis-adapter Socket.IO
        ws ws
        isomorphic-ws ws
        uws µWebSockets
        uwebsockets.js µWebSockets
        sockjs SockJS
        sockjs-client SockJS
        @microsoft/signalr SignalR
        pusher Pusher
        pusher-js Pusher
        ably Ably
        mqtt MQTT
        partykit PartyKit
        partysocket PartyKit
        colyseus Colyseus
        colyseus.js Colyseus
        @colyseus/core Colyseus
        peerjs PeerJS
        simple-peer simple-peer
        yjs Yjs
        y-websocket Yjs
        livekit-client LiveKit
        python-socketio Socket.IO
        flask-socketio Flask-SocketIO
        websockets websockets
        channels Django Channels
        github.com/gorilla/websocket gorilla/websocket
        nhooyr.io/websocket websocket
        tokio-tungstenite tungstenite
        tungstenite tungstenite
    """,
    "data": """
        mongoose Mongoose
        mongodb MongoDB
        prisma Prisma
        @prisma/client Prisma
        sequelize Sequelize
        typeorm TypeORM
        drizzle-orm Drizzle
        knex Knex
        pg PostgreSQL
        postgres PostgreSQL
        mysql MySQL
        mysql2 MySQL
        sqlite3 SQLite
        better-sqlite3 SQLite
        redis Redis
        ioredis Redis
        @upstash/redis Redis
        lowdb lowdb
        dexie Dexie
        idb idb
        localforage localForage
        pouchdb PouchDB
        @libsql/client libSQL
        kysely Kysely
        objection Objection
        mikro-orm MikroORM
        @mikro-orm/core MikroORM
        neo4j-driver Neo4j
        @elastic/elasticsearch Elasticsearch
        kafkajs Kafka
        amqplib RabbitMQ
        bullmq BullMQ
        bull Bull
        sqlalchemy SQLAlchemy
        flask-sqlalchemy SQLAlchemy
        alembic Alembic
        psycopg2 PostgreSQL
        psycopg2-binary PostgreSQL
        psycopg PostgreSQL
        asyncpg PostgreSQL
        pymongo MongoDB
        motor MongoDB
        mongoengine MongoEngine
        peewee peewee
        tortoise-orm Tortoise ORM
        sqlmodel SQLModel
        pymysql MySQL
        redis-py Redis
        pandas pandas
        polars Polars
        numpy NumPy
        scipy SciPy
        duckdb DuckDB
        pyarrow Arrow
        elasticsearch Elasticsearch
        gorm.io/gorm GORM
        github.com/jackc/pgx/v5 PostgreSQL
        github.com/lib/pq PostgreSQL
        github.com/go-redis/redis/v8 Redis
        github.com/redis/go-redis/v9 Redis
        go.mongodb.org/mongo-driver MongoDB
        github.com/mattn/go-sqlite3 SQLite
        sqlx sqlx
        diesel Diesel
        sea-orm SeaORM
        rusqlite SQLite
    """,
    "game": """
        phaser Phaser
        pixi.js PixiJS
        @pixi/react PixiJS
        three Three.js
        @react-three/fiber React Three Fiber
        @react-three/drei React Three Fiber
        babylonjs Babylon.js
        @babylonjs/core Babylon.js
        kaboom Kaboom
        kaplay KAPLAY
        excalibur Excalibur
        matter-js Matter.js
        cannon-es cannon-es
        @dimforge/rapier3d Rapier
        planck-js Planck.js
        howler Howler
        tone Tone.js
        playcanvas PlayCanvas
        melonjs melonJS
        littlejsengine LittleJS
        gsap GSAP
        animejs anime.js
        pygame pygame
        pygame-ce pygame
        arcade Arcade
        pyglet pyglet
        panda3d Panda3D
        ursina Ursina
        pymunk Pymunk
        bevy Bevy
        macroquad macroquad
        ggez ggez
        piston piston
        fyrox Fyrox
        rapier2d Rapier
        rapier3d Rapier
        github.com/hajimehoshi/ebiten/v2 Ebitengine
        github.com/faiface/pixel Pixel
    """,
    "build": """
        vite Vite
        @vitejs/plugin-react Vite
        @vitejs/plugin-react-swc Vite
        @vitejs/plugin-vue Vite
        webpack webpack
        webpack-cli webpack
        rollup Rollup
        esbuild esbuild
        parcel Parcel
        @swc/core SWC
        @babel/core Babel
        turbo Turborepo
        nx Nx
        lerna Lerna
        typescript TypeScript
        ts-node ts-node
        tsx tsx
        tsup tsup
        nodemon nodemon
        concurrently concurrently
        npm-run-all npm-run-all
        eslint ESLint
        prettier Prettier
        @biomejs/biome Biome
        postcss PostCSS
        autoprefixer PostCSS
        husky husky
        lint-staged lint-staged
        electron-builder electron-builder
        setuptools setuptools
        hatchling Hatch
        poetry-core Poetry
        flit-core Flit
        maturin maturin
        ruff Ruff
        black Black
        mypy mypy
        flake8 Flake8
        pylint Pylint
        pre-commit pre-commit
        pyinstaller PyInstaller
        wasm-bindgen wasm-bindgen
        wasm-pack wasm-pack
    """,
    "test": """
        jest Jest
        ts-jest Jest
        vitest Vitest
        mocha Mocha
        chai Chai
        jasmine Jasmine
        ava AVA
        tap tap
        supertest SuperTest
        cypress Cypress
        @playwright/test Playwright
        playwright Playwright
        puppeteer Puppeteer
        @testing-library/react Testing Library
        @testing-library/vue Testing Library
        @testing-library/jest-dom Testing Library
        @testing-library/user-event Testing Library
        jsdom jsdom
        happy-dom happy-dom
        msw MSW
        sinon Sinon
        nock nock
        @storybook/react Storybook
        storybook Storybook
        pytest pytest
        pytest-asyncio pytest
        pytest-cov pytest
        pytest-mock pytest
        hypothesis Hypothesis
        tox tox
        nox nox
        coverage coverage
        selenium Selenium
        locust Locust
        factory-boy factory_boy
        faker Faker
        github.com/stretchr/testify testify
        github.com/onsi/ginkgo/v2 Ginkgo
        github.com/onsi/gomega Gomega
        criterion Criterion
        proptest proptest
        insta insta
        mockall mockall
        rstest rstest
    """,
}

LIBS: dict[str, tuple[str, str]] = {}
for _role, _lines in _KNOWN.items():
    for _line in _lines.strip().splitlines():
        _pkg, _name = _line.split(None, 1)
        LIBS.setdefault(_pkg, (_name.strip(), _role))

# A folder's name and the role its part has in its container's layers (§6.5): its face, its doors, its data, its settings.
FOLDER_ROLES = ("face", "doors", "data", "settings")
ROLES: dict[str, str] = {
    **dict.fromkeys(("views", "view", "pages", "page", "screens", "screen", "components", "component", "ui", "widgets", "layouts",
                     "layout", "templates", "scenes", "frontend", "styles"), "face"),
    **dict.fromkeys(("routes", "route", "router", "routers", "api", "apis", "controllers", "controller", "handlers", "handler",
                     "endpoints", "resolvers", "graphql", "rpc", "middleware", "middlewares"), "doors"),
    **dict.fromkeys(("db", "database", "models", "model", "store", "stores", "schema", "schemas", "repositories", "repository",
                     "repos", "entities", "migrations", "prisma", "dao", "persistence", "storage"), "data"),
    **dict.fromkeys(("config", "configs", "configuration", "settings", "conf", "env"), "settings"),
}

_PYPI = re.compile(r"[-_.]+")
_GO_MAJOR = re.compile(r"/v\d+$")
_GO = {_GO_MAJOR.sub("", k): v for k, v in LIBS.items() if "/" in k and "." in k.split("/", 1)[0]}


def norm(name: str, registry: str = "npm") -> str:
    """A package's name as LIBS keeps it: lower case; PyPI's and Cargo's `_` and `.` read as `-` (as the registries match them)."""
    name = (name or "").strip().lower()
    return _PYPI.sub("-", name) if registry in ("pypi", "cargo") else name


def lib(name: str, registry: str = "npm") -> tuple[str, str] | None:
    """`(the name a person knows it by, its role)` of a package, or None for one not on the list."""
    key = norm(name, registry)
    got = LIBS.get(key)
    if got is None and registry == "go":                       # a module's major version (`/v2`) read as the module's
        got = _GO.get(_GO_MAJOR.sub("", key))
    return got
