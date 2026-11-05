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


def test_the_copy_is_orkui_0_27_0_with_the_room_the_chair_the_door_and_the_leaders_faces():
    """Spec 123 B: `--ork-room`, `chair/`, `door/` and a face of each leader race and of the Orkmaster's crown, in five moods and at both sizes."""
    stamp = orkui.stamp()
    assert tuple(int(n) for n in stamp["version"].split(".")) >= (0, 27, 0) and len(stamp["commit"]) == 40
    tokens_css = (orkui.ROOT / "tokens.css").read_text(encoding="utf-8")
    assert "--ork-room: #090807;" in tokens_css and '"room": "#090807"' in (orkui.ROOT / "tokens.json").read_text(encoding="utf-8")
    for name in ("chair/back-posts.svg", "chair/back-panel.svg", "chair/big-posts.svg", "chair/big-panel.svg", "chair/empty-posts.svg", "chair/empty-panel.svg", "door/frame.svg", "door/interior.svg"):
        assert name in stamp["files"], name
    css = (orkui.ROOT / "components.css").read_text(encoding="utf-8")
    assert ".ork-chair" in css and ".ork-chair.is-empty" in css and ".ork-door" in css and ".ork-door.is-open" in css
    for race in ("shaman", "dryad", "imp", "fairy", "unicorn", "lich"):
        for mood in ("focused", "worried", "no", "pleased", "asleep"):
            assert any(n.startswith(f"races/{race}-") and n.endswith(f"-{mood}.png") for n in stamp["files"]), (race, mood)
            assert any(n.startswith(f"races/{race}-") and n.endswith(f"-{mood}@2x.png") for n in stamp["files"]), (race, mood, "@2x")
    for mood in ("focused", "worried", "no", "pleased", "asleep"):
        assert f"races/peon-crown-{mood}.png" in stamp["files"] and f"races/peon-crown-{mood}@2x.png" in stamp["files"], mood


def test_head_draws_a_mood_only_for_a_leader_or_the_crown_and_chair_and_door_are_orkuis_spans():
    js = (STATIC / "js" / "orkui.js").read_text(encoding="utf-8")
    head = js.split("export function Head")[1].split("export function Switch")[0]
    assert "mood" in head and "hasFaces(race, tier)" in head and 'LEADER_RACES = ["shaman", "dryad", "imp", "fairy", "unicorn", "lich"]' in js
    assert 'race === "peon" && tier === "crown"' in js
    chair = js.split("export function Chair")[1].split("export function Door")[0]
    door = js.split("export function Door")[1].split("const LEADER_RACES")[0]
    assert "ork-chair" in chair and "is-empty" in chair and "aria-hidden" in chair and "ork-door" in door and "is-open" in door and "aria-hidden" in door


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
        legacy -= {"--at", "--of", "--span"} | {f"--hc-{n}" for n in ("w", "h", "pad", "gap", "head", "window", "label", "top", "edge", "tight", "shown", "rise", "room", "tabs", "lean", "cap", "pots", "pot1", "first", "rest", "lead")}   # spec 101 §4: the hand's sizes and a lane's fan; spec 104 §5: the tabs' height a lifted card stays under, its lean; §3: the mana's caption and potions
        legacy -= {"--c", "--h", "--i", "--peek"}   # spec 128 B: the Orkmaster's column's card colour, a pile's height, a card's place in it and the foot showing of each (table/column.css)
        legacy -= {"--k"}   # decisions §241: a head's place in the fan behind the fourth head of a face-down card's ring (table/column.css `.col-mid__fan`)
        legacy -= {"--hw", "--hh"}   # decisions §241: the size of the heads in the ring's middle, a size smaller from three heads on (table/column.css `.col-mid`)
        legacy -= {"--cue-v", "--cue-h"}   # spec 107 §6.2: the scroll cue's two layers, one for each axis (page.css `.gui-scrolls`)
        legacy -= {"--table-end-w", "--table-end-h"}   # spec 104 §4: the room the table keeps beside and above the discard (table/discard.css)
        legacy -= {f"--hc-{n}" for n in ("face", "big", "corner", "fgap", "lh", "title", "lines")}   # spec 142 B: the hand's card with no window, its face's height, the lifted card's, the corner, the fan's gap, the title's lines
        legacy -= {f"--hc-{n}" for n in ("wlh", "wpad", "why0", "ends", "seen", "die", "potw")}   # spec 147 C: the hand's card cut under its title: the why's line and padding, where it starts, what the die and the potions need, what the rim shows (hand/handcard.css, mana.css)
        legacy -= {"--under"}   # spec 142 A: the room under a face-up pile's front card, its cards' feet (table/column.css `.col-pile.is-up`)
        legacy -= {"--hf-left", "--hf-w"}   # spec 128 A.1: where the field lies, its left edge on the + card's and its width (hand/fieldturn.js `placeField`)
        legacy -= {"--column-tuck", "--column-w", "--col-shown", "--col-edge", "--col-out"}   # spec 130 E: the column's width of its own, a face-down card's tuck, what shows of it, the piles' right edge, the room a card slides out into (frame/frame.css, table/column.css)
        legacy -= {"--dash"}   # spec 130 B.1: the empty slot's dashes in the edge or the ink (hand/mana.css), until orkUI draws `.ork-potion.is-empty`
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
    assert "var(--ork-table)" not in sheets                                       # only orkUI's .ork-table draws the wood (the sheets use its rim: spec 123 §7.7)


def test_a_task_cards_sign_is_one_of_orkuis_two_tone_drawings():
    """Decisions §170.1: a task card's window draws its kind's sign at 28 px, so every kind's sign has its 14 x 14 drawing in two tones."""
    import re
    data = (STATIC / "js" / "table" / "data.js").read_text(encoding="utf-8")
    table = re.search(r"const KIND_SIGN = \{(.*?)\};", data, re.S).group(1)
    signs = set(re.findall(r'\w+: "([a-z]+)"', table))
    from pathlib import Path
    big = Path(__file__).resolve().parents[1] / "design-system" / "orkui" / "signs" / "big"
    assert signs and all((big / f"{s}.svg").is_file() and (big / f"{s}-light.svg").is_file() for s in signs), sorted(s for s in signs if not (big / f"{s}.svg").is_file())


def test_the_copy_is_orkui_0_28_0_with_the_turn_the_wait_the_give_and_the_dies_play_arrow():
    stamp = orkui.stamp()
    assert tuple(int(n) for n in stamp["version"].split(".")) >= (0, 28, 0) and len(stamp["commit"]) == 40
    css = (orkui.ROOT / "components.css").read_text(encoding="utf-8")
    for piece in (".ork-turn {", ".ork-turn__back", ".ork-turn__face", ".ork-sigil.is-waiting::after", "--ork-sigil-share", ".ork-gives {", "@keyframes ork-give", ".ork-die.face-play"):
        assert piece in css, piece


def test_the_page_draws_the_turn_the_wait_the_give_and_the_play_arrow_with_orkui_and_keeps_no_stand_in():
    sheets = "\n".join(re.sub(r"/\*.*?\*/", "", p.read_text(encoding="utf-8"), flags=re.S) for p in SHEETS)
    assert "--_arc" not in sheets and "--_rest" not in sheets, "the wait's ring is orkUI's `.ork-sigil.is-waiting`: the page sets the share and the colour only"
    assert "is-turned-up" not in sheets and "table-turn-up" not in sheets and "perspective(" not in sheets, "the card turns in orkUI's `.ork-turn`"
    js = "\n".join(p.read_text(encoding="utf-8") for p in (STATIC / "js").rglob("*.js"))
    assert "is-turned-up" not in js and "ork-gives" in js and "ork-turn" in js
    assert '"play"' in (STATIC / "js" / "hand" / "playdie.js").read_text(encoding="utf-8")
