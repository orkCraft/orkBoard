"""Spec 121 D (docs/specs/121-the-day-the-morning-and-the-night.md §5.1, decisions §199.5): the screens a goal's merged tasks changed, with their route paths, by code. A screen whose component file
changed, a file its component imports (one level down), none; the flow's order; four at most; a router's table names no screen; no screen no answer. Real git projects, tests/test_commit_goal.py's."""
from __future__ import annotations

import json
from pathlib import Path

from orkboard.realm import goal_screens
from tests.test_commit_goal import commit, git, land, repo, state  # noqa: F401  (the fixture)

APP = {
    "package.json": json.dumps({"dependencies": {"react-router-dom": "6"}}),
    "src/App.jsx": 'import { Routes, Route } from "react-router-dom";\nimport Home from "./pages/Home";\nimport Cart from "./pages/Cart";\nimport Pay from "./pages/Pay";\n'
                   'import Help from "./pages/Help";\nimport About from "./pages/About";\nimport Terms from "./pages/Terms";\n'
                   'export default () => <Routes><Route path="/" element={<Home />} /><Route path="/cart" element={<Cart />} /><Route path="/pay" element={<Pay />} />'
                   '<Route path="/help" element={<Help />} /><Route path="/about" element={<About />} /><Route path="/terms" element={<Terms />} /></Routes>;\n',
    "src/pages/Home.jsx": 'export default () => <><Link to="/cart">Cart</Link><Link to="/help">Help</Link></>;\n',
    "src/pages/Cart.jsx": 'import Row from "../components/CartRow";\nimport "../styles/cart.css";\nexport default () => <><Row /><Link to="/pay">Pay</Link></>;\n',
    "src/pages/Pay.jsx": "export default () => null;\n",
    "src/pages/Help.jsx": 'export default () => <Link to="/about">About</Link>;\n',
    "src/pages/About.jsx": 'export default () => <Link to="/terms">Terms</Link>;\n',
    "src/pages/Terms.jsx": "export default () => null;\n",
    "src/components/CartRow.jsx": "export default () => <li />;\n",
    "src/styles/cart.css": ".cart { color: red }\n",
    "src/util/format.js": "export const money = (n) => n;\n",
}


def app(repo: Path) -> None:
    for name, text in APP.items():
        commit(repo, name, text, f"add {name}")


def of(repo: Path, slug: str) -> list[dict]:
    return goal_screens.of(state(repo), repo, slug)


def test_a_screen_whose_component_file_a_task_changed_is_a_screen_of_the_goal_with_its_route_path(repo):
    app(repo)
    land(repo, "pay-now", "k1", {"src/pages/Pay.jsx": "export default () => <button>Pay now</button>;\n"})
    assert of(repo, "pay-now") == [{"screen": "pay", "name": "Pay", "path": "/pay"}]


def test_a_file_no_screen_uses_or_a_goal_that_changed_none_has_no_screens(repo):
    app(repo)
    land(repo, "money", "k1", {"src/util/format.js": "export const money = (n) => `$${n}`;\n", "README.md": "words\n"})
    assert of(repo, "money") == []
    assert of(repo, "nobody") == [] and of(repo, "") == []                               # a goal no task of which landed


def test_the_screens_come_in_the_flows_order_and_four_at_most(repo):
    app(repo)
    edits = {f"src/pages/{n}.jsx": APP[f"src/pages/{n}.jsx"] + "// changed\n" for n in ("Terms", "Pay", "About", "Home", "Help")}      # the links stay: the flow is dev's now
    land(repo, "everything", "k1", edits)
    got = of(repo, "everything")
    assert [s["screen"] for s in got] == ["home", "help", "pay", "about"]       # breadth first: home, cart + help, pay + about, terms: the fifth, terms, is left off
    assert [s["path"] for s in got] == ["/", "/help", "/pay", "/about"]


def test_only_the_goals_own_commits_count(repo):
    app(repo)
    land(repo, "pay-now", "k1", {"src/pages/Pay.jsx": "export default () => <b>Pay</b>;\n"})
    commit(repo, "src/pages/Home.jsx", "export default () => <i>my own change</i>;\n", "my own")        # the person's, no goal's
    land(repo, "terms", "k1", {"src/pages/Terms.jsx": "export default () => <i>Terms</i>;\n"})
    assert [s["screen"] for s in of(repo, "pay-now")] == ["pay"]
    assert [s["screen"] for s in of(repo, "terms")] == ["terms"]

