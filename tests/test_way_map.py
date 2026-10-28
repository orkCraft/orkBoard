"""Spec 102 C §3.3 (docs/specs/102-the-other-maps-and-picking-on-them.md, decisions §151.7): Marketing's map, the way in. Four steps (channels, the store page or the
site, the install, the first session) read by name from dev's tree (never the working tree, never a file's contents); a step with nothing *Nothing to read yet: …*; the
first session's entry screen by the routers' own names (realm/screen_map.py is not in this tree); its text. Real git repositories, no model."""
from __future__ import annotations

import sys

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.gui.ideas_maps import MapsMixin, maps_commands
from orkboard.realm import way_map
from tests.test_assets import put
from tests.test_commit_goal import git, repo, state  # noqa: F401  (the fixture)


def paths(step: dict) -> list[tuple[str, str]]:
    return [(h["path"], h["kind"]) for h in step["holds"]]


FILES = {"marketing/plan.md": b"x", "press/kit.md": b"x", "sitemap.xml": b"x", "robots.txt": b"x", "notes/press.md": b"x",
         "fastlane/metadata/en-US/title.txt": b"x", "fastlane/metadata/en-US/description.txt": b"x", "store/listing.md": b"x",
         "landing/index.html": b"x", "site/about.md": b"x", "web/src/App.tsx": b"x", "web/pricing.mdx": b"x",
         "install.sh": b"x", "Dockerfile": b"x", "fastlane/Fastfile": b"x", "Formula/app.rb": b"x", "electron-builder.yml": b"x", "src/Dockerfile": b"x",
         "app/page.tsx": b"x", "src/App.tsx": b"x", "src/screens/Home.tsx": b"x"}


def test_each_step_holds_what_the_project_names_for_it_sorted_with_its_kind(repo):
    put(repo, FILES)
    got = way_map.read(state(repo), repo)
    assert got["steps"] == ["channels", "store", "install", "first_session"] and got["commit"] == git(repo, "rev-parse", "dev") and got["short"] == got["commit"][:7]
    assert paths(got["channels"]) == [("marketing/plan.md", "channel"), ("press/kit.md", "channel"), ("robots.txt", "channel"), ("sitemap.xml", "channel")]
    assert paths(got["store"]) == [("fastlane/metadata/en-US/description.txt", "store"), ("fastlane/metadata/en-US/title.txt", "store"), ("landing/index.html", "site"),
                                   ("site/about.md", "site"), ("store/listing.md", "store"), ("web/pricing.mdx", "site")]       # web/src/App.tsx is not a page
    assert paths(got["install"]) == [("Dockerfile", "install"), ("Formula/app.rb", "install"), ("electron-builder.yml", "install"), ("fastlane/Fastfile", "install"),
                                     ("install.sh", "install")]                                                               # src/Dockerfile is not the project's
    assert paths(got["first_session"]) == [("app/page.tsx", "entry")]                                                          # Next.js before src/App
    for step in way_map.STEPS:
        assert got[step]["none"] is False and got[step]["more"] == 0


def test_a_step_with_nothing_to_read_is_none_and_no_dev_is_an_empty_map(repo):
    put(repo, {"README.md": b"# hi", "src/lib.py": b"x"})
    got = way_map.read(state(repo), repo)
    assert all(got[s] == {"holds": [], "none": True, "more": 0} for s in way_map.STEPS)
    gone = way_map.read(state(repo), repo, "no-such")
    assert gone["commit"] == "" and all(gone[s]["none"] for s in way_map.STEPS) and way_map.text(state(repo), repo, ref="no-such") is None


def test_dev_trees_only_secrets_hidden_and_skipped_folders_never(repo):
    put(repo, {"marketing/plan.md": b"x", "marketing/.env": b"SECRET=1", "marketing/id_rsa": b"k", ".github/marketing/x.md": b"x", "node_modules/marketing/x.md": b"x"})
    (repo / "marketing" / "draft.md").write_bytes(b"x")                                      # the working tree's: never read
    git(repo, "checkout", "-q", "main")
    put(repo, {"press/main-only.md": b"x"})                                                   # main's, not dev's
    git(repo, "checkout", "-q", "dev")
    assert paths(way_map.read(state(repo), repo)["channels"]) == [("marketing/plan.md", "channel")]


def test_the_entry_screen_is_the_first_router_name_that_exists_else_a_screens_folders_home(repo):
    expect = [({"pages/index.js": b"x", "src/App.tsx": b"x"}, "pages/index.js"), ({"src/routes/+page.svelte": b"x", "index.html": b"x"}, "src/routes/+page.svelte"),
              ({"lib/main.dart": b"x", "lib/screens/home.dart": b"x"}, "lib/main.dart"), ({"app/index.tsx": b"x", "src/App.tsx": b"x"}, "app/index.tsx"),
              ({"public/index.html": b"x"}, "public/index.html"), ({"src/App.vue": b"x", "index.html": b"x"}, "src/App.vue")]
    for n, (files, entry) in enumerate(expect):
        git(repo, "checkout", "-q", "-B", f"dev{n}", "main")
        put(repo, files)
        assert paths(way_map.read(state(repo), repo, f"dev{n}")["first_session"]) == [(entry, "entry")], files
    git(repo, "checkout", "-q", "-B", "screens", "main")
    put(repo, {"src/screens/Settings.tsx": b"x", "src/screens/Welcome.tsx": b"x", "src/screens/Home.tsx": b"x", "src/pages/notes.md": b"x"})
    assert paths(way_map.read(state(repo), repo, "screens")["first_session"]) == [("src/screens/Home.tsx", "entry")]


def test_a_step_lists_at_most_the_cap_and_says_how_many_were_left_out(repo):
    put(repo, {f"fastlane/metadata/l{n:02d}/title.txt": b"x" for n in range(30)})
    store = way_map.read(state(repo), repo)["store"]
    assert len(store["holds"]) == way_map.HOLDS and store["more"] == 30 - way_map.HOLDS and store["holds"][0]["path"] == "fastlane/metadata/l00/title.txt"


# -- the text -----------------------------------------------------------------------------------------------------------------------

def test_the_text_is_the_four_steps_and_what_each_holds_and_nothing_to_read_yet(repo):
    put(repo, {"marketing/plan.md": b"x", "fastlane/metadata/en-US/title.txt": b"x", "src/App.tsx": b"x"})
    short = git(repo, "rev-parse", "dev")[:7]
    text = way_map.text(state(repo), repo)
    assert text == "\n".join([f"The map of the way in at dev {short} (how people come, read from the project's files by name)", "",
                              "1. Channels: marketing/plan.md",
                              "2. The store page or the site: fastlane/metadata/en-US/title.txt",
                              "3. The install: Nothing to read yet: the install's files (install.sh, a Dockerfile, fastlane/Fastfile).",
                              "4. The first session: src/App.tsx"])
    assert text == way_map.text(state(repo), repo, "abc123", None)
    put(repo, {"README.md": b"# x"})
    assert way_map.text(state(repo), repo).split("\n", 1)[1] == text.split("\n", 1)[1]


def test_the_text_names_six_files_a_step_and_how_many_more_and_is_bounded(repo):
    put(repo, {f"fastlane/metadata/l{n:02d}/title.txt": b"x" for n in range(30)})
    store = [ln for ln in way_map.text(state(repo), repo).splitlines() if ln.startswith("2.")][0]
    assert store.endswith("fastlane/metadata/l05/title.txt and 24 more") and store.count("title.txt") == 6
    put(repo, {"marketing/" + "d" * 80 + f"{n}/" + "f" * 80 + ".md": b"x" for n in range(30)})
    text = way_map.text(state(repo), repo)
    assert len(text) <= 4 * way_map.LINE + 200 and all(len(ln) <= way_map.LINE + 4 for ln in text.splitlines())


# -- ideas.way_map ---------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo):
    git(fake_repo, "branch", "dev")
    h = Orkboard(fake_repo)
    if not isinstance(h.ideas, MapsMixin):                                       # wired by the lead: the host's bases and its table
        h.ideas.__class__ = type("IdeasWithMaps", (MapsMixin, type(h.ideas)), {})
        h.commands.update(maps_commands(h.ideas))
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def test_the_command_answers_the_four_steps_of_dev(host, fake_repo):
    put(fake_repo, {"marketing/plan.md": b"x"})
    git(fake_repo, "branch", "-f", "dev", "HEAD")
    got = host.command("ideas.way_map", {})
    assert paths(got["channels"]) == [("marketing/plan.md", "channel")] and got["steps"] == ["channels", "store", "install", "first_session"]
    assert got["commit"] == git(fake_repo, "rev-parse", "dev") and got["store"]["none"] is True
