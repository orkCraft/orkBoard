"""Spec 115 B (docs/specs/115-the-live-product-under-each-leaders-eyes.md §3): `realm/play_place.py`, where you are on the running product: the page's path → Design's screen, and the path with the
files the probe named → the parts of every map that place touches (the ids the maps' faces stamp, `realm/map_parts.py`). Small apps in real git repositories (tests/test_screen_map.py's: the files
are committed to `dev`), no model."""
from __future__ import annotations

import json


from orkboard.realm import ideas, loop, map_parts, opportunity_tree as tree, play_place
from tests.test_commit_goal import repo, state  # noqa: F401  (the fixture)
from tests.test_screen_map import NEXT_APP, REACT, on_dev

SHOP = {
    **REACT,
    "src/pages/Orders.tsx": 'import hero from "../assets/hero.png";\nexport default function Orders() { return <img src="/orders-cover.jpg" alt="" />; }\n',
    "src/components/Button.tsx": "export const Button = () => null;\n",
    "src/assets/hero.png": "png",
    "src/assets/unseen.png": "png",
    "public/orders-cover.jpg": "jpg",
    "marketing/launch.md": "# Launch\n",
}

GAME = {
    "package.json": json.dumps({"name": "dungeon", "devDependencies": {"vite": "5"}}),
    "index.html": '<html><body><canvas id="game"></canvas><script type="module" src="/src/main.ts"></script></body></html>\n',
    "src/main.ts": 'import { draw } from "./game/render";\ndraw(document.getElementById("game"));\n',
    "src/game/render.ts": 'const sheet = "sprites/hero.png";\nexport const draw = (c: HTMLCanvasElement) => c.getContext("2d");\n',
    "src/game/loot.ts": "export const loot = () => 1;\n",
    "sprites/hero.png": "png",
}


def ids(got: dict, map_id: str) -> list[str]:
    return [p["id"] for p in got.get(map_id, [])]


# -- the screen ---------------------------------------------------------------------------------------------------------------------------

def test_a_react_router_app_reaches_a_screen_by_an_exact_path_or_a_parameter_with_its_step(repo):
    on_dev(repo, SHOP)
    assert play_place.screen(state(repo), repo, "/orders") == {"id": "orders", "name": "Orders", "step": 2}
    assert play_place.screen(state(repo), repo, "/orders/12?tab=lines#top") == {"id": "orders-id", "name": "Order detail", "step": 3}
    assert play_place.screen(state(repo), repo, "/") == {"id": "home", "name": "Home", "step": 1}


def test_a_next_app_reaches_its_screens_through_route_groups_and_dynamic_segments(repo):
    on_dev(repo, NEXT_APP)
    assert play_place.screen(state(repo), repo, "/cart")["id"] == "cart"
    assert play_place.screen(state(repo), repo, "/dashboard/blue/settings") == {"id": "dashboard-team-settings", "name": "Dashboard team settings", "step": 4}




def test_a_path_no_screen_fits_a_non_path_and_a_project_with_no_screen_have_no_screen(repo):
    on_dev(repo, SHOP)
    for path in ("/nowhere/at/all", "/orders/12/lines", "", None, 7):
        assert play_place.screen(state(repo), repo, path) is None
    assert play_place.parts(state(repo), repo, "/nowhere/at/all") == {}




# -- the parts of the maps ----------------------------------------------------------------------------------------------------------------



def test_techs_parts_are_the_folders_of_the_files_the_probe_named_in_any_spelling_else_the_screens_file(repo):
    on_dev(repo, SHOP)
    named = ["./src/components/Button.tsx:12:5", f"file://{repo}/src/pages/Orders.tsx", "/elsewhere/on/the/machine/src/x.tsx", "../outside.tsx", ".env", 3]
    got = play_place.parts(state(repo), repo, "/orders", named)
    assert ids(got, "system") == ["src/components", "src/pages"]
    assert ids(play_place.parts(state(repo), repo, "/orders", ["/elsewhere/x.tsx", "style.css"]), "system") == ["src/pages"]       # none held: the screen's file's folder
    assert "system" not in play_place.parts(state(repo), repo, "/nowhere", ["style.css"])                                              # no part, no screen
    assert ids(play_place.parts(state(repo), repo, "/nowhere", ["src/components/Button.tsx"]), "system") == ["src/components"]       # a file alone is a place too
    assert "screens" not in play_place.parts(state(repo), repo, "/nowhere", ["src/components/Button.tsx"])


def test_arts_parts_are_the_assets_the_screens_file_and_the_named_files_name(repo):
    on_dev(repo, SHOP)
    assert ids(play_place.parts(state(repo), repo, "/orders"), "art") == ["public/orders-cover.jpg", "src/assets/hero.png"]
    assert ids(play_place.parts(state(repo), repo, "/settings"), "art") == []
    got = play_place.parts(state(repo), repo, "/settings", ["src/pages/Orders.tsx"])
    assert got["art"][0] == {"id": "public/orders-cover.jpg", "name": "orders-cover.jpg"} and "src/assets/unseen.png" not in ids(got, "art")
    assert {p["id"] for p in got["art"]} <= {p["id"] for p in map_parts.parts(state(repo), repo, "art")}




def test_the_home_screen_of_a_next_app_is_the_way_in_s_first_session(repo):
    on_dev(repo, NEXT_APP)
    assert play_place.parts(state(repo), repo, "/")["marketing"] == [{"id": "app/page.tsx", "name": "page.tsx"}]
    assert "marketing" not in play_place.parts(state(repo), repo, "/cart")




def test_a_games_canvas_file_gives_the_loops_steps_that_rest_on_it_or_on_its_folder(repo):
    on_dev(repo, GAME)
    state_dir = state(repo)
    loop.keep(state_dir, repo, {"loops": [{"span": "core", "name": "Fight", "line": "A line", "steps": [
        {"name": "Draw", "line": "A line", "rests_on": ["src/game/render.ts"]}, {"name": "Loot", "line": "A line", "rests_on": ["src/game"]},
        {"name": "Rest", "line": "A line", "rests_on": ["src/main.ts"]}, {"name": "Free", "line": "A line"}]}], "currencies": []}, "person")
    got = play_place.parts(state_dir, repo, "/", ["src/game/render.ts:3:1"])
    assert [p["name"] for p in got["game-design"]] == ["Draw", "Loot"]
    assert {p["id"] for p in got["game-design"]} <= {p["id"] for p in map_parts.parts(state_dir, repo, "game-design")}
    assert ids(got, "system") == ["src/game"] and ids(got, "art") == ["sprites/hero.png"]
    assert "screens" not in got and "product" not in got and "release" not in got


def test_products_jobs_are_those_whose_goals_touched_a_named_file_and_none_without_the_boards_pages(repo, tmp_path):
    on_dev(repo, SHOP)
    state_dir, pages = state(repo), tmp_path / "pages"
    fast = ideas.add_idea(pages, "Fast orders", "general", state_dir)
    other = ideas.add_idea(pages, "Dark mode", "general", state_dir)
    ideas.set_meta(pages, fast, touches=json.dumps(["src/pages/", "src/components/Button.tsx"]))
    ideas.set_meta(pages, other, touches=json.dumps(["src/theme.css"]))
    tree.keep(state_dir, [{"text": "Cut the time to a first order from ten minutes to two"}],
              [{"when": "I shop", "want": w, "so": "buy", "segment": "buyers"} for w in ("find an order", "pay quickly", "look good")], "person")
    jobs = tree.read(state_dir)["jobs"]
    tree.attach(state_dir, jobs[0]["id"], fast)
    tree.attach(state_dir, jobs[2]["id"], other)
    got = play_place.parts(state_dir, repo, "/orders", pages=pages)
    assert got["product"] == [{"id": jobs[0]["id"], "name": "find an order"}]
    assert got["product"][0]["id"] in {p["id"] for p in map_parts.parts(state_dir, repo, "product", pages)}
    assert "product" not in play_place.parts(state_dir, repo, "/orders")                                    # no pages, no goals to read
    assert "product" not in play_place.parts(state_dir, repo, "/nowhere", ["src/assets/hero.png"], pages=pages)   # a place none of the goals touched




def test_a_map_that_cannot_be_read_gives_nothing_never_an_exception(repo, tmp_path, monkeypatch):
    assert play_place.parts(tmp_path / "nowhere", tmp_path / "nowhere", "/orders", ["a.py"]) == {}
    assert play_place.screen(tmp_path / "nowhere", tmp_path / "nowhere", "/") is None
    on_dev(repo, SHOP)

    def broken(*_a, **_k):
        raise RuntimeError("unreadable")
    monkeypatch.setattr(play_place.art_map, "read", broken)
    monkeypatch.setattr(play_place.loop, "read", broken)
    got = play_place.parts(state(repo), repo, "/orders", pages=tmp_path / "pages")
    assert set(got) == {"screens", "system"}


