"""Spec 102 A (docs/specs/102-the-other-maps-and-picking-on-them.md §1, decisions §112.7, §134.2): Design's map, the app's screens along their flow, read by code from
dev's tree. Each router's routes (React Router, Vue Router, Next.js `pages/` and `app/`, SvelteKit, Flutter, Expo Router, a `screens/` folder), the links read by
name, the steps breadth first from the entry, a screen's newest picture, a pain's place, the text bounded and the same bytes for the same dev, no screen no map.
Real git repositories (tests/test_commit_goal.py's: the files are committed to `dev`), no model."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import idea_lens, idea_shots, ideas, screen_map, screen_routes
from tests.test_commit_goal import commit, git, repo, state  # noqa: F401  (the fixture)
from tests.test_system_overview import write

PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32


def on_dev(repo: Path, files: dict[str, str], message: str = "the app") -> str:
    write(repo, files)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "dev")


def by_path(got: dict) -> dict[str, dict]:
    return {s["path"]: s for s in got["screens"]}


def pairs(got: dict) -> list[tuple[str, str]]:
    return [(k["from"], k["to"]) for k in got["links"]]


# -- the fixtures: a small app per router ------------------------------------------------------------------------------------------------------

REACT = {
    "package.json": json.dumps({"dependencies": {"react": "18", "react-router-dom": "6"}}),
    "src/main.tsx": 'import { createBrowserRouter, RouterProvider } from "react-router-dom";\n'
                    'import Home from "./pages/Home";\nimport Orders from "./pages/Orders";\nimport OrderDetail from "./pages/OrderDetail";\n'
                    'import { Settings as SettingsPage } from "./pages/Settings";\nimport Layout from "./Layout";\n'
                    'const Lazy = React.lazy(() => import("./pages/Lazy"));\n'
                    "// { path: '/commented', element: <Nope /> }\n"
                    'const router = createBrowserRouter([\n'
                    '  { path: "/", element: <Layout />, children: [\n'
                    '    { index: true, element: <Home /> },\n'
                    '    { path: "orders", element: <Orders />, children: [{ path: ":id", element: <OrderDetail /> }] },\n'
                    '    { path: "settings", element: <SettingsPage /> },\n'
                    '    { path: "lazy", element: <Lazy /> },\n'
                    '    { path: "*", element: <NotFound /> },\n'
                    '  ] },\n]);\n',
    "src/pages/Home.tsx": 'import { Link } from "react-router-dom";\nexport default function Home() { return <div><Link to="/orders">Orders</Link>\n'
                          '<a href="/settings">Settings</a></div>; }\n',
    "src/pages/Orders.tsx": 'export default function Orders() { const go = useNavigate(); return <li onClick={() => navigate(`/orders/${id}`)}>x</li>; }\n',
    "src/pages/OrderDetail.tsx": 'export default function OrderDetail() { navigate("/"); navigate("/orders"); return null; }\n',
    "src/pages/Settings.tsx": "export const Settings = () => null;\n",
    "src/pages/Lazy.tsx": "export default () => null;\n",
}

REACT_JSX = {
    "package.json": json.dumps({"dependencies": {"react-router-dom": "6"}}),
    "src/App.jsx": 'import { Routes, Route } from "react-router-dom";\nimport Home from "./Home";\nimport Cart from "./Cart";\nimport Pay from "./Pay";\n'
                   'export default () => (\n<Routes>\n  <Route path="/" element={<Home />} />\n'
                   '  <Route path="/cart" element={<Cart onGo={(a) => a > 1} />}>\n    <Route path="pay" element={<Pay />} />\n  </Route>\n</Routes>);\n',
    "src/Home.jsx": 'export default () => <Link to="/cart">Cart</Link>;\n',
    "src/Cart.jsx": 'export default () => <Link to="/cart/pay">Pay</Link>;\n',
    "src/Pay.jsx": "export default () => null;\n",
}

VUE = {
    "package.json": json.dumps({"dependencies": {"vue": "3", "vue-router": "4"}}),
    "src/router/index.ts": "import { createRouter, createWebHistory } from 'vue-router'\nimport HomeView from '../views/HomeView.vue'\n"
                           "const router = createRouter({ history: createWebHistory(), routes: [\n"
                           "  { path: '/', name: 'home', component: HomeView },\n"
                           "  { path: '/about', component: () => import('../views/AboutView.vue') },\n"
                           "  { path: '/users/:id', component: () => import('../views/UserView.vue') },\n] })\n",
    "src/views/HomeView.vue": '<template><router-link to="/about">About</router-link><button @click="$router.push(\'/users/7\')">me</button></template>\n',
    "src/views/AboutView.vue": '<template><router-link :to="\'/\'">Home</router-link></template>\n',
    "src/views/UserView.vue": "<template><p>user</p></template>\n",
}

NEXT_PAGES = {
    "package.json": json.dumps({"dependencies": {"next": "14", "react": "18"}}),
    "pages/_app.tsx": "export default () => null;\n",
    "pages/index.tsx": 'export default () => <Link href="/blog">Blog</Link>;\n',
    "pages/blog/index.tsx": 'export default () => <a href="/blog/hello">Hello</a>;\n',
    "pages/blog/[slug].tsx": "export default () => null;\n",
    "pages/api/hello.ts": "export default () => null;\n",
}

NEXT_APP = {
    "package.json": json.dumps({"dependencies": {"next": "14"}}),
    "app/layout.tsx": "export default () => null;\n",
    "app/page.tsx": "export default () => <Link href='/dashboard'>Go</Link>;\n",
    "app/(shop)/cart/page.tsx": "export default () => null;\n",
    "app/dashboard/page.tsx": "export default () => <Link href='/cart'>Cart</Link>;\n",
    "app/dashboard/[team]/settings/page.tsx": "export default () => null;\n",
}

SVELTEKIT = {
    "package.json": json.dumps({"devDependencies": {"@sveltejs/kit": "2"}}),
    "src/routes/+layout.svelte": "<slot />\n",
    "src/routes/+page.svelte": '<a href="/play">Play</a>\n',
    "src/routes/play/+page.svelte": '<script>import { goto } from "$app/navigation"; const end = () => goto("/scores/42");</script>\n',
    "src/routes/play/+page.ts": "export const load = () => ({});\n",
    "src/routes/scores/[game]/+page.svelte": "<p>scores</p>\n",
}

FLUTTER = {
    "pubspec.yaml": "name: shop\n",
    "lib/main.dart": "import 'package:flutter/material.dart';\nvoid main() => runApp(MaterialApp(initialRoute: '/', routes: {\n"
                     "  '/': (context) => const HomeScreen(),\n  '/cart': (context) => CartScreen(),\n  '/pay': (context) { return PayScreen(); },\n}));\n",
    "lib/screens/home_screen.dart": "class HomeScreen extends StatelessWidget { go(context) { Navigator.pushNamed(context, '/cart'); } }\n",
    "lib/screens/cart_screen.dart": "class CartScreen extends StatelessWidget { go(context) { Navigator.of(context).pushNamed('/pay'); Navigator.pushNamed(context, \"/pay\"); } }\n",
    "lib/screens/pay_screen.dart": "class PayScreen extends StatelessWidget {}\n",
}

EXPO = {
    "package.json": json.dumps({"dependencies": {"expo": "51", "expo-router": "3"}}),
    "app/_layout.tsx": "export default () => null;\n",
    "app/index.tsx": 'export default () => <Link href="/profile">Me</Link>;\n',
    "app/profile.tsx": "export default () => null;\n",
    "app/(tabs)/feed.tsx": "export default () => null;\n",
    "app/+not-found.tsx": "export default () => null;\n",
}

FOLDER = {
    "package.json": json.dumps({"name": "toy"}),
    "src/screens/Home.js": 'export default () => navigate("/order-list");\n',
    "src/screens/OrderListScreen.js": 'export default () => navigate("/order-list/receipt");\n',
    "src/screens/Receipt/index.js": "export default () => null;\n",
    "src/screens/Receipt/Row.js": "export const Row = () => null;\n",
    "src/screens/Home.test.js": "test('x', () => {});\n",
}


# -- §1.1 the screens, by router ---------------------------------------------------------------------------------------------------------------

def test_react_router_s_object_table_gives_its_nested_routes_by_name_with_the_components_files(repo):
    on_dev(repo, REACT)
    got = screen_map.read(state(repo), repo)
    assert got["source"] == "react-router"
    assert [(s["path"], s["name"], s["file"]) for s in got["screens"]] == [
        ("/", "Home", "src/pages/Home.tsx"),                                                       # the index route is the screen, the layout around it is not
        ("/orders", "Orders", "src/pages/Orders.tsx"), ("/orders/:id", "Order detail", "src/pages/OrderDetail.tsx"),
        ("/settings", "Settings", "src/pages/Settings.tsx"), ("/lazy", "Lazy", "src/pages/Lazy.tsx")]
    assert "/commented" not in by_path(got) and "*" not in by_path(got) and "/*" not in by_path(got)      # a comment and the catch-all are no screen


def test_react_router_s_jsx_routes_nest_and_a_component_with_a_function_prop_still_reads(repo):
    on_dev(repo, REACT_JSX)
    got = screen_map.read(state(repo), repo)
    assert [(s["path"], s["name"], s["file"]) for s in got["screens"]] == [
        ("/", "Home", "src/Home.jsx"), ("/cart", "Cart", "src/Cart.jsx"), ("/cart/pay", "Pay", "src/Pay.jsx")]
    assert pairs(got) == [("home", "cart"), ("cart", "cart-pay")]


def test_vue_router_s_table_gives_a_component_by_import_or_lazy_import(repo):
    on_dev(repo, VUE)
    got = screen_map.read(state(repo), repo)
    assert got["source"] == "vue-router"
    assert [(s["path"], s["name"], s["file"]) for s in got["screens"]] == [
        ("/", "Home", "src/views/HomeView.vue"), ("/about", "About", "src/views/AboutView.vue"), ("/users/:id", "User", "src/views/UserView.vue")]
    assert pairs(got) == [("home", "about"), ("home", "users-id"), ("about", "home")]       # router-link, $router.push, :to


def test_next_pages_skip_the_app_wrapper_and_the_api_and_take_index_and_parameters(repo):
    on_dev(repo, NEXT_PAGES)
    got = screen_map.read(state(repo), repo)
    assert got["source"] == "next-pages"
    assert [(s["path"], s["file"]) for s in got["screens"]] == [("/", "pages/index.tsx"), ("/blog", "pages/blog/index.tsx"), ("/blog/:slug", "pages/blog/[slug].tsx")]
    assert pairs(got) == [("home", "blog"), ("blog", "blog-slug")]                              # "/blog/hello" fits /blog/:slug


def test_next_app_takes_the_page_files_and_drops_route_groups(repo):
    on_dev(repo, NEXT_APP)
    got = screen_map.read(state(repo), repo)
    assert got["source"] == "next-app"
    assert [s["path"] for s in got["screens"]] == ["/", "/cart", "/dashboard", "/dashboard/:team/settings"]
    assert pairs(got) == [("home", "dashboard"), ("dashboard", "cart")]


def test_sveltekit_takes_the_page_svelte_files(repo):
    on_dev(repo, SVELTEKIT)
    got = screen_map.read(state(repo), repo)
    assert got["source"] == "sveltekit"
    assert [(s["path"], s["file"]) for s in got["screens"]] == [
        ("/", "src/routes/+page.svelte"), ("/play", "src/routes/play/+page.svelte"), ("/scores/:game", "src/routes/scores/[game]/+page.svelte")]
    assert pairs(got) == [("home", "play"), ("play", "scores-game")]


def test_flutter_s_routes_map_gives_each_screen_class_its_file(repo):
    on_dev(repo, FLUTTER)
    got = screen_map.read(state(repo), repo)
    assert got["source"] == "flutter"
    assert [(s["path"], s["name"], s["file"]) for s in got["screens"]] == [
        ("/", "Home", "lib/screens/home_screen.dart"), ("/cart", "Cart", "lib/screens/cart_screen.dart"), ("/pay", "Pay", "lib/screens/pay_screen.dart")]
    assert pairs(got) == [("home", "cart"), ("cart", "pay")]


def test_flutter_go_router_routes_read_too(repo):
    on_dev(repo, {"pubspec.yaml": "name: g\n", "lib/router.dart": "final r = GoRouter(routes: [\n  GoRoute(path: '/', builder: (c, s) => const Home()),\n"
                                                                    "  GoRoute(name: 'one', path: '/one', builder: (c, s) => One()),\n]);\n"})
    assert [(s["path"], s["name"]) for s in screen_map.read(state(repo), repo)["screens"]] == [("/", "Home"), ("/one", "One")]


def test_expo_router_takes_the_app_folder_without_layouts_groups_and_not_found(repo):
    on_dev(repo, EXPO)
    got = screen_map.read(state(repo), repo)
    assert got["source"] == "expo-router"
    assert [s["path"] for s in got["screens"]] == ["/", "/feed", "/profile"]
    assert pairs(got) == [("home", "profile")]


def test_a_screens_folder_is_the_fallback_a_folder_with_an_index_is_one_screen_and_a_test_is_none(repo):
    on_dev(repo, FOLDER)
    got = screen_map.read(state(repo), repo)
    assert got["source"] == "screens"
    assert [(s["path"], s["name"], s["file"]) for s in got["screens"]] == [
        ("/home", "Home", "src/screens/Home.js"), ("/order-list", "Order list", "src/screens/OrderListScreen.js"), ("/receipt", "Receipt", "src/screens/Receipt/index.js")]
    assert pairs(got) == [("home", "order-list")]                                                # "/order-list/receipt" fits none


def test_a_project_with_no_screen_has_no_map_and_no_text(repo):
    on_dev(repo, {"pyproject.toml": "[project]\nname='lib'\n", "lib/core.py": "X = 1\n", "node_modules/a/pages/x.js": "x\n", "tests/pages/t.js": "x\n"})
    assert screen_map.read(state(repo), repo)["screens"] == [] and screen_map.text(state(repo), repo) is None


def test_a_project_with_no_dev_has_no_map(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    assert screen_map.read(tmp_path / ".orkcraft", tmp_path) == {"head": "", "source": "", "entry": "", "more": 0, "loose": [], "links": [], "steps": [], "screens": []}
    assert screen_map.text(tmp_path / ".orkcraft", tmp_path) is None


def test_the_working_tree_is_never_read_only_dev(repo):
    on_dev(repo, REACT_JSX)
    write(repo, {"src/App.jsx": "export default () => null;\n", "src/Draft.jsx": "x\n"})              # uncommitted
    git(repo, "checkout", "-q", "-b", "side")
    write(repo, {"pages/index.tsx": "x\n"})
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "side")
    assert [s["path"] for s in screen_map.read(state(repo), repo)["screens"]] == ["/", "/cart", "/cart/pay"]


def test_a_secret_file_and_a_symlink_are_not_read(repo):
    on_dev(repo, {**FOLDER, ".env": "A=1\n", "src/screens/secrets.js": "x\n"})
    (repo / "src" / "screens" / "Linked.js").symlink_to(repo / "package.json")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "link")
    assert "Linked" not in {s["name"] for s in screen_map.read(state(repo), repo)["screens"]}
    assert screen_routes.Tree(repo, git(repo, "rev-parse", "dev")).files.count(".env") == 0


# -- §1.2 the flow: the links and the steps --------------------------------------------------------------------------------------------------------

def test_the_steps_run_breadth_first_from_the_entry_a_screen_once_and_the_unlinked_are_the_last_step(repo):
    on_dev(repo, {**FOLDER, "src/screens/Home.js": 'navigate("/order-list"); navigate("/receipt");\n',
                  "src/screens/OrderListScreen.js": 'navigate("/receipt");\n', "src/screens/Orphan.js": "x\n"})
    got = screen_map.read(state(repo), repo)
    assert got["entry"] == "home" and pairs(got) == [("home", "order-list"), ("home", "receipt"), ("order-list", "receipt")]
    assert got["steps"] == [["home"], ["order-list", "receipt"], ["orphan"]] and got["loose"] == ["orphan"]
    assert sorted(x for row in got["steps"] for x in row) == sorted(s["id"] for s in got["screens"])


def test_the_entry_is_slash_else_the_first_screen_nothing_links_to_else_the_first(repo):
    on_dev(repo, {"package.json": "{}", "src/screens/Alpha.js": 'navigate("/beta");\n', "src/screens/Beta.js": 'navigate("/gamma");\n', "src/screens/Gamma.js": "x\n"})
    assert screen_map.read(state(repo), repo)["entry"] == "alpha"
    on_dev(repo, {"src/screens/Gamma.js": 'navigate("/alpha");\n'})                                    # a loop: all are linked to, the first is the entry
    assert screen_map.read(state(repo), repo)["entry"] == "alpha"
    on_dev(repo, {"src/screens/Home.js": "x\n"}, "a home")                                              # `/home` is no `/`
    assert screen_map.read(state(repo), repo)["entry"] == "home"


def test_a_screen_two_routes_share_a_file_with_says_nothing_of_either_and_ids_never_clash(repo):
    on_dev(repo, {"package.json": json.dumps({"dependencies": {"react-router": "6"}}),
                  "src/r.jsx": 'import { Route } from "react-router";\nconst a = <Route path="/a-b" element={<X />} />; const b = <Route path="/a/b" element={<Y />} />;\n'
                               'navigate("/a/b");\n'})
    got = screen_map.read(state(repo), repo)
    assert [s["id"] for s in got["screens"]] == ["a-b", "a-b-2"] and got["links"] == []


def test_the_read_is_cached_by_the_dev_head_and_follows_dev(repo):
    one = on_dev(repo, REACT_JSX)
    assert screen_map.read(state(repo), repo)["head"] == one
    two = on_dev(repo, {"src/Pay.jsx": "export default () => <a href='/'>home</a>;\n"})
    got = screen_map.read(state(repo), repo)
    assert got["head"] == two and ("cart-pay", "home") in pairs(got)


# -- a screen's picture -----------------------------------------------------------------------------------------------------------------------------

def land_shot(repo: Path, slug: str, files: dict[str, str], at: str) -> str:
    """A task that landed in dev with the `files`, its picture kept (a plan with the task's `shot`)."""
    sha = on_dev(repo, files, f"task of {slug}")
    folder = ideas.state_folder(state(repo), slug)
    folder.mkdir(parents=True, exist_ok=True)
    png = repo / "pic.png"
    png.write_bytes(PNG)
    shot = idea_shots.store(state(repo), slug, "k1", 1, png)
    (folder / "plan.json").write_text(json.dumps({"tasks": [{"id": "k1", "state": "merged", "commit": sha, "shot": {**shot, "at": at}}]}))
    return sha


def test_a_screen_s_picture_is_the_newest_a_task_that_changed_its_file_took(repo):
    on_dev(repo, REACT_JSX)
    assert all("picture" not in s for s in screen_map.read(state(repo), repo)["screens"])
    land_shot(repo, "older", {"src/Cart.jsx": 'export default () => <Link to="/cart/pay">Pay now</Link>;\n'}, "2026-10-01T10:00:00")
    land_shot(repo, "newer", {"src/Cart.jsx": 'export default () => <Link to="/cart/pay">Pay!</Link>;\n'}, "2026-10-02T10:00:00")
    pics = {s["id"]: s.get("picture") for s in screen_map.read(state(repo), repo)["screens"]}
    assert pics["home"] is None and pics["cart-pay"] is None
    assert pics["cart"]["kind"] == "shot" and pics["cart"]["goal"] == "newer" and pics["cart"]["id"] == "k1-shot-r1" and pics["cart"]["file"] == "shot.png"


def test_a_screen_kept_with_a_lens_is_the_picture_of_the_screen_that_goes_by_its_name_when_it_is_the_newest(repo):
    on_dev(repo, REACT_JSX)
    sid = idea_lens.keep_screen(state(repo), PNG, "Cart")
    got = {s["id"]: s.get("picture") for s in screen_map.read(state(repo), repo)["screens"]}
    assert got["cart"]["kind"] == "lens" and got["cart"]["id"] == sid and got["home"] is None
    land_shot(repo, "later", {"src/Cart.jsx": "export default () => null;\n"}, "2999-01-01T00:00:00")
    assert screen_map.read(state(repo), repo)["screens"][1]["picture"]["kind"] == "shot"


# -- §1.3 a pain's place --------------------------------------------------------------------------------------------------------------------------------

def test_a_pain_is_pinned_to_a_screen_or_a_step_and_read_back(repo):
    on_dev(repo, REACT_JSX)
    idea_lens.keep_segment(state(repo), "Shop owners", "Orders get lost")
    idea_lens.keep_segment(state(repo), "Shop owners", "Refunds take a week", on="cart")
    idea_lens.keep_segment(state(repo), "Buyers", "Checkout is long", on=screen_map.step_id(3))
    got = {s["segment"]: s["pains"] for s in idea_lens.segments_placed(state(repo))}
    assert got["Shop owners"] == [{"text": "Refunds take a week", "on": "cart"}, {"text": "Orders get lost", "on": ""}]
    assert got["Buyers"] == [{"text": "Checkout is long", "on": "step:3"}]


# -- §1.4 the text ----------------------------------------------------------------------------------------------------------------------------------------

def test_the_text_names_the_steps_the_flow_and_the_pains_under_their_screens_by_segment(repo):
    on_dev(repo, REACT_JSX)
    idea_lens.keep_segment(state(repo), "Shop owners", "Refunds take a week", on="cart")
    idea_lens.keep_segment(state(repo), "Buyers", "Paying is slow", on="cart")
    idea_lens.keep_segment(state(repo), "Buyers", "Whole flow is long", on="step:2")
    idea_lens.keep_segment(state(repo), "Buyers", "No place yet")
    idea_lens.keep_segment(state(repo), "Buyers", "Screen is gone", on="deleted-screen")
    text = screen_map.text(state(repo), repo)
    assert text.startswith(f"The map of the screens at dev {git(repo, 'rev-parse', 'dev')[:7]}, read from React Router; the entry is Home (/)\n")
    assert "Step 1: Home (/)\nStep 2: Cart (/cart)\nStep 3: Pay (/cart/pay)" in text
    assert "- Home to Cart\n- Cart to Pay" in text
    assert ("\nStep 2\n- Buyers: Whole flow is long\nCart (/cart)\n- Buyers: Paying is slow\n- Shop owners: Refunds take a week\n"
            "Not pinned to a screen:\n") in text
    assert "- Buyers: No place yet" in text.split("Not pinned to a screen:")[1] and "- Buyers: Screen is gone" in text.split("Not pinned to a screen:")[1]
    assert len(text) <= screen_map.LIMIT


def test_the_same_dev_is_the_same_bytes_and_a_picture_does_not_change_them(repo):
    on_dev(repo, REACT_JSX)
    idea_lens.keep_segment(state(repo), "Buyers", "Paying is slow", on="cart")
    one = screen_map.text(state(repo), repo)
    assert screen_map.text(state(repo), repo) == one == screen_map.text(state(repo), repo, "")
    idea_lens.keep_screen(state(repo), PNG, "Cart")
    assert screen_map.text(state(repo), repo) == one


def test_a_big_app_stays_in_the_bound_and_says_what_is_left_out(repo):
    files = {"package.json": "{}"}
    for n in range(90):
        files[f"src/screens/Screen{n:03d}.js"] = f'navigate("/screen{(n + 1) % 90:03d}");\n'
    on_dev(repo, files)
    for n in range(60):
        idea_lens.keep_segment(state(repo), f"Segment {n % 4}", f"A pain of some length number {n} that goes on and on", on=f"screen{n:03d}")
    got = screen_map.read(state(repo), repo)
    assert len(got["screens"]) == screen_map.MAX_SCREENS and got["more"] == 30
    text = screen_map.text(state(repo), repo)
    assert len(text) <= screen_map.LIMIT and "(30 more screens are not named)" in text and "more pains" in text
    assert screen_map.text(state(repo), repo) == text


def test_one_step_with_many_screens_is_one_bounded_line(repo):
    files = {"package.json": "{}", "src/screens/Home.js": "".join(f'navigate("/page{n:02d}");\n' for n in range(40))}
    files.update({f"src/screens/Page{n:02d}.js": "x\n" for n in range(40)})
    on_dev(repo, files)
    lines = [ln for ln in screen_map.text(state(repo), repo).splitlines() if ln.startswith("Step 2")]
    assert len(lines) == 1 and len(lines[0]) <= screen_map.LINE and lines[0].endswith(" more")


def test_since_says_the_screens_that_came_or_went_after_the_commit(repo):
    first = on_dev(repo, REACT_JSX)
    base = screen_map.text(state(repo), repo)
    assert screen_map.text(state(repo), repo, first).endswith("Changed since your last call: nothing.")
    write(repo, {"src/App.jsx": REACT_JSX["src/App.jsx"].replace('<Route path="pay" element={<Pay />} />', '<Route path="refund" element={<Pay />} />')})
    on_dev(repo, {"src/Pay.jsx": "export default () => 1;\n"})
    got = screen_map.text(state(repo), repo, first)
    assert got.split("\n\n")[-1] == "Changed since your last call:\n- new screen Pay (/cart/refund)\n- gone screen Pay (/cart/pay)"
    assert screen_map.text(state(repo), repo, "0" * 40).endswith("not known (that commit is not on dev).")
    assert base.split("\n", 1)[1] != "" and "Changed since" not in screen_map.text(state(repo), repo)
