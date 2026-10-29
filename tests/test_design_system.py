"""Orkboard drawn in orkUI (docs/specs/40-design-system.md): design-system/orkui is orkUI's office look as orkUI made it, the
roles map onto its tokens, the page and the phone load it and nothing of the old Camp sheets, and Orkboard's own sheets carry
no colour, no font and no corner of their own."""
from __future__ import annotations

import re

from orkboard.design import orkui, tokens
from orkboard.gui import server

STATIC = server.STATIC
SHEETS = [STATIC / "page.css", STATIC / "js" / "shell" / "shell.css", STATIC / "js" / "board" / "board.css",
          STATIC / "js" / "arena" / "arena.css", STATIC / "js" / "arena" / "systemmap.css", STATIC / "js" / "arena" / "limits.css", STATIC / "js" / "arena" / "play.css", STATIC / "pwa" / "app.css", STATIC / "pwa" / "party.css"]
SHEETS += sorted(p for d in ("frame", "table", "hand") for p in (STATIC / "js" / d).glob("*.css"))   # the window as two parts (spec 98): every sheet of its folders


def test_the_copy_is_orkuis_office_look_as_stamped():
    assert orkui.problems() == []
    stamp = orkui.stamp()
    assert stamp["from"] == "https://github.com/orkCraft/orkUI" and stamp["look"] == "office" and stamp["version"]
    for name in ("tokens.css", "components.css", "fonts.css", "tokens.json", "LICENSE", "NOTICE", "icons/icons.svg",
                 "races/peon-laborer.png", "races/elf-elder@2x.png", "races/goblin-warrior.png", "races/gnome-laborer.png"):
        assert name in stamp["files"], name
    assert ".ork-race__head" in (orkui.ROOT / "components.css").read_text(encoding="utf-8")


def test_the_copy_leaves_out_what_the_window_does_not_draw_and_keeps_what_the_phone_does(tmp_path, monkeypatch):
    """Spec 96 §1: `emblems/` is not copied and not stamped; `moons/` and the goal types' signs stay for the phone (until spec 94 E)."""
    assert orkui.SKIP == ("emblems",)
    assert not (orkui.ROOT / "emblems").exists() and not [n for n in orkui.stamp()["files"] if n.split("/")[0] in orkui.SKIP]
    assert (orkui.ROOT / "moons").is_dir() and "signs/moon.svg" in orkui.stamp()["files"] and "signs/night.svg" in orkui.stamp()["files"]
    assert "signs/bug.svg" in orkui.stamp()["files"]
    (orkui.ROOT / "emblems").mkdir()
    try:
        (orkui.ROOT / "emblems" / "a.svg").write_text("x", encoding="utf-8")
        assert orkui.problems() == ["emblems/a.svg: not orkUI's (copy orkUI again, never edit here)"]
    finally:
        import shutil
        shutil.rmtree(orkui.ROOT / "emblems")
    assert orkui.problems() == []


def test_the_copy_is_orkui_0_15_3_with_the_ink_marks_the_moon_and_the_cards_tokens():
    stamp = orkui.stamp()
    assert tuple(int(n) for n in stamp["version"].split(".")) >= (0, 15, 3) and len(stamp["commit"]) == 40
    for tool in ("claude", "codex", "agy", "cursor", "hermes", "pi"):
        for name in (f"marks/harness-{tool}.png", f"marks/harness-{tool}-ink.png", f"marks/harness-{tool}-ink@2x.png"):
            assert name in stamp["files"], name
    for n in (1, 2, 3):
        assert f"marks/rank-{n}-ink.png" in stamp["files"]
    for race in ("peon", "elf", "goblin", "gnome", "knight", "lich", "skeleton", "shaman", "dryad", "imp", "fairy", "unicorn"):
        assert orkui.race_png(race, "laborer") in stamp["files"] or orkui.race_png(race, "elder") in stamp["files"], race
    assert "races/peon-crown.png" in stamp["files"] and "races/griffin-laborer.png" not in stamp["files"]
    tokens_css = (orkui.ROOT / "tokens.css").read_text(encoding="utf-8")
    assert "--ork-card:" in tokens_css and "--ork-card-frame:" in tokens_css


def test_the_page_draws_the_ink_marks_the_moon_and_no_head_at_12_x_11():
    js = STATIC / "js"
    for name in ("table/header.js", "table/tabs.js", "arena/limits.js"):
        text = (js / name).read_text(encoding="utf-8")
        assert ("-ink" in text or "markSrc" in text) and "ork-mark" in text, name   # a party's tool beside its seats, a limit's chip: the ink mark
    assert "-ink" in (js / "table" / "data.js").read_text(encoding="utf-8")
    head = (js / "orkui.js").read_text(encoding="utf-8")
    assert not re.search(r"\bsmall\b", head.split("export function Head")[1].split("export function Switch")[0].replace("`small`", ""))
    assert "ork-icon g7" in head
    for path in js.rglob("*.js"):
        if "vendor" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"<\$\{(Head|Who|WhoHead)\}[^>]*\bsmall\b", text), path.name       # no head is drawn at 12 x 11 (spec 96 §2.1)
        assert "sign night" not in text and 'name="night"' not in text, path.name                # the sign is `moon` (the phone keeps `night`)
    page = (STATIC / "page.css").read_text(encoding="utf-8")
    assert ".ork-icon.g7 { --ork-icon: 21px; }" in page


def test_a_hand_edit_of_the_copy_is_caught(tmp_path, monkeypatch):
    copy = tmp_path / "orkui"
    copy.mkdir()
    (copy / "a.css").write_text("x", encoding="utf-8")
    monkeypatch.setattr(orkui, "ROOT", copy)
    monkeypatch.setattr(orkui, "STAMP", copy / "ORKUI.json")
    assert orkui.problems() and "missing" in orkui.problems()[0]
    (copy / "ORKUI.json").write_text('{"files": {"a.css": "0"}}', encoding="utf-8")
    assert orkui.problems() == ["a.css: changed by hand"]


def test_the_roles_wear_orkuis_type_and_colours():
    assert tokens.problems() == []
    css = tokens.roles_css()
    assert ".ok-font-heading { font: var(--ork-type-heading)" in css and ".ok-tone-error { color: var(--ork-danger); }" in css
    declared = set(re.findall(r"^\s*(--[\w-]+):", (tokens.ORKUI / "tokens.css").read_text(encoding="utf-8"), re.M))
    assert set(re.findall(r"var\((--[\w-]+)\)", css)) <= declared


def test_the_page_loads_orkui_and_no_camp_sheet():
    page = (STATIC / "index.html").read_text(encoding="utf-8")
    links = re.findall(r'<link rel="stylesheet" href="([^"]+)">', page)
    assert links[:3] == ["/ds/orkui/fonts.css", "/ds/orkui/tokens.css", "/ds/orkui/components.css"]
    assert 'data-look="office"' in page and "data-theme" not in page
    for href in links:
        assert href == "/roles.css" or server.resolve(href) is not None, href
    for gone in ("layout", "lake", "town", "camp", "yards", "cover", "office", "onboarding", "bench", "lastlook", "inside", "kit"):
        assert not (STATIC / f"{gone}.css").exists(), gone


def test_orkboards_own_sheets_carry_no_colour_no_font_and_no_corner_of_their_own():
    for path in SHEETS:
        css = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        drawn = re.sub(r"mask-image:[^;}]*", "", css)                       # a mask's black is its shape, not a colour
        assert not re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", drawn), path.name
        assert not re.findall(r"border-radius", css), path.name
        assert all(f.startswith("var(--ork-font-") for f in re.findall(r"font-family:\s*([^;}]+)", css)), path.name
        assert "[data-look=\"camp\"]" not in css and "[data-theme" not in css, path.name
        legacy = set(re.findall(r"var\((--(?!ork-)[\w-]+)", css)) - {"--agents-h", "--sec", "--role", "--tabs",
                                                                   "--rot", "--dy", "--z", "--ov", "--cols",   # spec 49: a fan's turn, rise, order and overlap; the columns
                                                                   "--dx", "--s", "--delay",                    # spec 57: a dealt card's travel (--dy as the fan's), scale and delay
                                                                   "--lanes", "--card-w", "--col-w"}            # decisions §167.7: the lanes, a card's and a lane's width
        legacy -= {"--at", "--of", "--span"} | {f"--hc-{n}" for n in ("w", "h", "pad", "gap", "head", "window", "label", "top", "edge", "tight", "shown", "rise", "room", "tabs", "lean", "cap", "pots", "first", "rest", "lead")}   # spec 101 §4: the hand's sizes and a lane's fan; spec 104 §5: the tabs' height a lifted card stays under, its lean; §3: the mana's caption and potions
        legacy -= {"--cue-v", "--cue-h"}   # spec 107 §6.2: the scroll cue's two layers, one for each axis (page.css `.gui-scrolls`)
        legacy -= {"--table-end-w", "--table-end-h"}   # spec 104 §4: the room the table keeps beside and above the discard (table/discard.css)
        assert not legacy, (path.name, legacy)


def test_every_crafts_head_is_in_the_copy_and_the_pages_words_are_the_glossarys():
    from orkboard.realm import lexicon, roles

    for craft, race in roles.RACES.items():
        assert lexicon.term(f"race.{race}") and lexicon.term(f"craft.{craft}") == roles.CRAFT_LABELS[craft]
        for tier in roles.TIERS:
            for big in (False, True):
                assert (orkui.ROOT / orkui.race_png(race, tier, big)).is_file(), (race, tier, big)
    words = {"TIER_WORDS": {t: lexicon.term(f"tier.{t}") for t in roles.TIERS},
             "RACE_WORDS": {r: lexicon.term(f"race.{r}") for r in (*roles.RACES.values(), "skeleton")},      # the library's own race (spec 68 §1.3)
             "CRAFT_WORDS": {c: lexicon.term(f"craft.{c}") for c in roles.CRAFTS}}
    for path in (STATIC / "js" / "orkui.js", STATIC / "pwa" / "shell-who.js"):
        js = path.read_text(encoding="utf-8")
        for name, want in words.items():
            got = dict(re.findall(r'(\w+): "([^"]+)"', re.search(rf"const {name} = \{{([^}}]*)\}}", js).group(1)))
            assert got == want, (path.name, name)


def test_the_field_is_orkuis_table_its_wood_a_surface_and_never_a_mark():
    """Spec 77 (decisions §92): the field the work is dealt on wears orkUI's table; the wood is orkUI's, never a sheet's."""
    tok = (orkui.ROOT / "tokens.css").read_text(encoding="utf-8")
    assert all(f"--ork-{t}:" in tok for t in ("table", "table-rim", "table-rim-hi"))
    assert ".ork-table" in (orkui.ROOT / "components.css").read_text(encoding="utf-8")
    pane = (STATIC / "js" / "table" / "pane.js").read_text(encoding="utf-8")
    assert re.search(r'<section class="table-pane ork-table"', pane)           # spec 98 §3: the table starts at the pane's top, the Board and what is opened over it on its wood
    sheets = "".join(p.read_text(encoding="utf-8") for p in SHEETS)
    assert "--ork-table" not in sheets                                            # only orkUI's .ork-table draws the wood


def test_a_task_cards_sign_is_one_of_orkuis_two_tone_drawings():
    """Decisions §170.1: a task card's window draws its kind's sign at 28 px, so every kind's sign has its 14 x 14 drawing in two tones."""
    import re
    data = (STATIC / "js" / "table" / "data.js").read_text(encoding="utf-8")
    table = re.search(r"const KIND_SIGN = \{(.*?)\};", data, re.S).group(1)
    signs = set(re.findall(r'\w+: "([a-z]+)"', table))
    from pathlib import Path
    big = Path(__file__).resolve().parents[1] / "design-system" / "orkui" / "signs" / "big"
    assert signs and all((big / f"{s}.svg").is_file() and (big / f"{s}-light.svg").is_file() for s in signs), sorted(s for s in signs if not (big / f"{s}.svg").is_file())
