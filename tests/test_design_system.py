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
                                                                   "--lanes", "--card-w", "--col-w",            # decisions §167.7: the lanes, a card's and a lane's width
                                                                   "--board-cols", "--live-t"}                 # spec 156 D.1: the Board's columns (the tabs' less Release's), and Live's track when the project has a Live party
        legacy -= {"--at", "--of", "--span"} | {f"--hc-{n}" for n in ("w", "h", "pad", "gap", "head", "window", "label", "top", "edge", "tight", "shown", "rise", "room", "tabs", "lean", "cap", "pots", "pot1", "first", "rest", "lead", "cx", "far", "cut", "ph", "pc")}   # spec 101 §4: the hand's sizes and a lane's fan; spec 104 §5: the tabs' height a lifted card stays under, its lean; §3: the mana's caption and potions
        legacy -= {"--c", "--h", "--i", "--peek"}   # spec 128 B: the Orkmaster's column's card colour, a pile's height, a card's place in it and the foot showing of each (table/column.css)
        legacy -= {"--r", "--step", "--x", "--y", "--behind"}   # spec 147 B: a back's turn in the Orkmaster's hand and the step between two backs; a standing card's place in its pile, below and right of the front one, and the room under it (table/column.css `.col-fan`, `.col-pile.is-up`)
        legacy -= {"--cue-v", "--cue-h"}   # spec 107 §6.2: the scroll cue's two layers, one for each axis (page.css `.gui-scrolls`)
        legacy -= {"--table-end-w", "--table-end-h"}   # spec 104 §4: the room the table keeps beside and above the discard (table/discard.css)
        legacy -= {f"--hc-{n}" for n in ("face", "big", "corner", "fgap", "lh", "title", "lines")}   # spec 142 B: the hand's card with no window, its face's height, the lifted card's, the corner, the fan's gap, the title's lines
        legacy -= {f"--hc-{n}" for n in ("wlh", "wpad", "why0", "ends", "seen", "die", "potw")}   # spec 147 C: the hand's card cut under its title: the why's line and padding, where it starts, what the die and the potions need, what the rim shows (hand/handcard.css, mana.css)
        legacy -= {"--under"}   # spec 142 A: the room under a face-up pile's front card, its cards' feet (table/column.css `.col-pile.is-up`)
        legacy -= {"--hf-left", "--hf-w", "--hf-top"}   # spec 128 A.1, spec 147 D.2: where the field lies, its left edge on the + card's, its width and its top over the hand (hand/fieldturn.js `placeField`)
        legacy -= {"--column-tuck", "--column-w", "--col-shown", "--col-edge", "--col-out"}   # spec 130 E: the column's width of its own, a face-down card's tuck, what shows of it, the piles' right edge, the room a card slides out into (frame/frame.css, table/column.css)
        legacy -= {"--up-h", "--up-rise"}   # spec 147 F: the phone's opened card as tall as the screen leaves while the keyboard is up, and how far a pressed card of the hand's row rises (hand/upright.css, stopcard.js)
        legacy -= {"--hc-lap", "--hc-ways", "--hc-wleft", "--hc-sunk-s"}   # spec 158 F: the sunk hand's shrink beside the ways row; spec 150 A: how far past its box a card laid over the column lets its shadow fall (hand/hand.css, the field and the lifted card); spec 158 F: where the answer cards lie, from the hand's foot and from its left (hand/openedcard.css)
        legacy -= {"--dash"}   # spec 130 B.1: the empty slot's dashes in the edge or the ink (hand/mana.css), until orkUI draws `.ork-potion.is-empty`
        legacy -= {"--edge-w"}   # spec 150 D.1: the width of the table's edge, the frame's third column (frame/frame.css)
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


# ---- spec 160 C (decisions §268, §269, §275, §276): orkUI 0.35.0, the table's colours and their contrast ----------------------

def test_the_copy_is_orkui_0_35_0_with_the_felts_steps_plate_bronze_pennant_chain_backpack_and_leather():
    stamp = orkui.stamp()
    assert tuple(int(n) for n in stamp["version"].split(".")) >= (0, 35, 0) and len(stamp["commit"]) == 40
    tok = (orkui.ROOT / "tokens.css").read_text(encoding="utf-8")
    for race in ("ork", "knight", "elf", "undead", "goblin", "gnome", "orkmaster"):
        assert f"--ork-party-{race}:" in tok, race
        assert all(f"--ork-felt-{race}-{n}:" in tok for n in ("1", "2", "3", "4", "5", "out", "rim")), race
        assert f"--ork-plate-{race}:" in tok, race
    for name in ("plate", "plaque", "bronze", "bronze-hi", "bronze-lo", "gilt", "gilt-hi", "leather", "leather-hi", "leather-lo", "leather-edge", "stitch"):
        assert f"--ork-{name}:" in tok, name
    css = (orkui.ROOT / "components.css").read_text(encoding="utf-8")
    for piece in (".ork-table[data-party]", ".ork-table[data-party].is-out", ".ork-plate {", ".ork-plaque {", ".ork-pennant {", ".ork-pennant.is-open",
                  ".ork-chain {", ".ork-chain.is-pulled", ".ork-pack {", ".ork-pack.is-open", ".ork-leather"):
        assert piece in css, piece
    for folder in ("pennant", "chain", "pack", "leather"):
        assert (orkui.ROOT / folder).is_dir() and any(n.startswith(f"{folder}/") for n in stamp["files"]), folder


# sRGB colour maths on the hex values of the copy's `tokens.json`: WCAG 2.x contrast, and CIE Lab (D65) for the rings' lead.
def _rgb(h: str) -> list[int]:
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _lin(c: int) -> float:
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lum(h: str) -> float:
    r, g, b = map(_lin, _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: str, b: str) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _lab(h: str) -> tuple[float, float]:
    """(L, chroma) in CIE Lab."""
    import math
    r, g, b = map(_lin, _rgb(h))
    x, y, z = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, _lum(h), (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda v: v ** (1 / 3) if v > 216 / 24389 else (24389 / 27 * v + 16) / 116   # noqa: E731
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, math.hypot(500 * (fx - fy), 200 * (fy - fz))


def _hex(parts) -> str:
    return "#" + "".join(f"{int(round(v)):02x}" for v in parts)


def _tokens() -> dict:
    import json
    return json.loads((orkui.ROOT / "tokens.json").read_text(encoding="utf-8"))


def _grounds() -> dict[str, dict[str, str]]:
    """Each party's grounds as orkUI makes them from `felt` (lamp, felt): the five steps, the felt out and the flat plate."""
    tok = _tokens()
    grounds = {}
    for race, f in tok["felt"].items():
        lamp, felt = _rgb(f["lamp"]), _rgb(f["felt"])
        steps = [_hex(c + (l - c) * s for l, c in zip(lamp, felt)) for s in tok["felt_steps"]]
        grounds[race] = {**{f"step {i + 1}": h for i, h in enumerate(steps)},
                         "out": _hex(c * tok["felt_out"] for c in felt), "plate": _hex(c * tok["felt_plate"] for c in felt)}
    return grounds


def test_the_grounds_made_here_from_tokens_json_are_the_ones_orkui_wrote_in_tokens_css():
    tok_css = (orkui.ROOT / "tokens.css").read_text(encoding="utf-8")
    grounds = _grounds()
    assert set(grounds) == set(re.findall(r"--ork-party-([\w-]+):", tok_css)) and len(grounds) == 7
    for race, made in grounds.items():
        written = {f"step {n}": re.search(rf"--ork-felt-{race}-{n}: (#\w+);", tok_css).group(1) for n in range(1, 6)}
        written["out"] = re.search(rf"--ork-felt-{race}-out: (#\w+);", tok_css).group(1)
        written["plate"] = re.search(rf"--ork-plate-{race}: (#\w+);", tok_css).group(1)
        for name, h in made.items():
            assert max(abs(a - b) for a, b in zip(_rgb(h), _rgb(written[name]))) <= 1, (race, name, h, written[name])


def test_every_text_token_holds_4_5_to_1_on_each_partys_plate_and_each_felt_out():
    """Decisions §275.1, §275.2: text keeps 4.5:1 on every felt, lit or out; words lie on a flat plate."""
    tok = _tokens()
    texts = sorted({a for a, _b in tok["text_pairs"]} - {"on-ink", "action"})
    assert {"ink", "ink-muted", "ink-faint", "danger", "alert", "success"} <= set(texts)
    for race, grounds in _grounds().items():
        for name in ("plate", "out"):
            for text in texts:
                assert _contrast(tok["color"][text], grounds[name]) >= 4.5, (race, name, text)


def test_the_rings_danger_and_alert_are_seen_3_to_1_on_every_ground_and_lead_every_party_and_element_colour():
    """Decisions §268.2, §276.1: a ring is a failure's (danger) or a question's (alert), the brightest on the table, by a lead a person sees:
    5 in Lab L or 10 in Lab chroma over each party's and each element's colour. Success is no ring (§276.2): 3:1 on every ground, no lead."""
    tok = _tokens()
    col = tok["color"]
    for race, grounds in _grounds().items():
        assert len(grounds) == 7                                  # five steps, the felt out, the plate
        for ring in ("danger", "alert", "success"):
            for name, ground in grounds.items():
                assert _contrast(col[ring], ground) >= 3, (race, ring, name)
    others = {**{f"party {r}": h for r, h in tok["party"].items()}, **{k: v for k, v in col.items() if k.startswith("elem-")}}
    assert len(others) >= 12
    for ring in ("danger", "alert"):
        ring_l, ring_c = _lab(col[ring])
        for name, h in others.items():
            l, c = _lab(h)
            assert ring_l - l >= 5 or ring_c - c >= 10, (ring, name, round(ring_l - l, 1), round(ring_c - c, 1))


# No smooth gradient and no blurred shadow or glow (decisions §269.1): hard pixel rings and hard-stop dithers only.
# These sheets still hold soft ones (the scroll cues' and the opened card's fade masks, the lifted card's cast shadow); a later stage of
# spec 160 takes each out and removes its file here. A file not listed must hold none, so a new one is caught.
SOFT_KNOWN = {"page.css", "js/hand/openedcard.css"}          # js/hand/hand.css lost its blurred shadow in spec 160 F


def _top_split(text: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in text:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return parts + [cur.strip()]


def _calls(css: str, name: str) -> list[str]:
    """The argument text of every `name(...)` in `css`, parentheses balanced."""
    found = []
    for m in re.finditer(rf"(?<![\w-]){name}\(", css):
        depth, i = 1, m.end()
        while i < len(css) and depth:
            depth += (css[i] == "(") - (css[i] == ")")
            i += 1
        found.append(css[m.end():i - 1])
    return found


def _blurred(shadow: str) -> bool:
    """True when a shadow's third length (its blur) is not a plain zero."""
    bare = re.sub(r"\b(?:rgba?|hsla?|color-mix|var)\((?:[^()]|\([^()]*\))*\)", "C", shadow.replace("inset", ""))
    lengths = re.findall(r"(?<![\w#.-])-?[\d.]+(?:px|em|rem)?(?![\w#])", bare)
    return len(lengths) >= 3 and float(re.match(r"-?[\d.]+", lengths[2]).group(0)) != 0


def _soft_things(css: str) -> list[str]:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    soft = []
    for fn in ("linear-gradient", "radial-gradient", "conic-gradient"):
        for args in _calls(css, fn):
            stops = [s for s in _top_split(args) if not re.match(r"^(to |-?[\d.]+(deg|turn|rad)|at |circle|ellipse|closest|farthest|from )", s)]
            flat = len({re.sub(r"(\s+(calc\(.*\)|-?[\d.]+\S*))+$", "", s) for s in stops}) == 1     # one colour: no fade
            # a hard stop gives its colour two places (`red 0 2px`) and the next begins where it ends; a stop with one place or none fades
            places = [len(re.findall(r"(?:^|\s)(?:calc\(.*\)|-?[\d.]+[\w%]*)(?=\s|$)", re.sub(r"\((?:[^()]|\([^()]*\))*\)", "C", s))) for s in stops]
            # the last stop may give one place, where the one before it ends (`… 4px 40%, c 40%`): it fills on, it does not fade
            if not flat and (min(places[:-1] or [2]) < 2 or places[-1] < 1):
                soft.append(f"{fn}({args[:60]})")
    for args in _calls(css, "blur") + [a for a in _calls(css, "drop-shadow") if _blurred(a)]:
        soft.append(f"blur/drop-shadow({args[:40]})")
    for m in re.finditer(r"(?<![\w-])box-shadow:\s*([^;}]+)", css):
        soft += [f"box-shadow: {one[:50]}" for one in _top_split(m.group(1)) if _blurred(one)]
    return soft


def test_no_sheet_adds_a_smooth_gradient_a_blurred_shadow_or_a_blur():
    """The desktop's and the phone's own sheets (`gui/static/**/*.css`, not the vendored xterm.css): none has a soft gradient, a blurred
    `box-shadow`, `filter: blur` or `drop-shadow` but those of `SOFT_KNOWN`."""
    sheets = {p.relative_to(STATIC).as_posix(): p for p in STATIC.rglob("*.css") if "vendor" not in p.relative_to(STATIC).parts}
    assert SOFT_KNOWN <= set(sheets), SOFT_KNOWN - set(sheets)
    found = {name: _soft_things(p.read_text(encoding="utf-8")) for name, p in sheets.items()}
    new = {name: things for name, things in found.items() if things and name not in SOFT_KNOWN}
    assert not new, f"soft gradients or blurs added (decisions §269.1: hard pixel rings and dithers only): {new}"
    assert all(found[name] for name in SOFT_KNOWN), f"a file of SOFT_KNOWN holds none now: remove it from the list ({[n for n in SOFT_KNOWN if not found[n]]})"


def test_the_soft_check_tells_a_hard_stop_from_a_fade():
    assert _soft_things(".a { background: linear-gradient(45deg, var(--ork-raised) 0 2px, var(--ork-panel) 2px 4px); }") == []
    assert _soft_things(".a { background: linear-gradient(90deg, red 0 4px, color-mix(in srgb, red 22%, blue) 4px 40%, blue 40%); }") == []
    assert _soft_things(".a { background: linear-gradient(90deg, red 0 4px, blue); }") != []
    assert _soft_things(".a { background: linear-gradient(105deg, transparent 0 30%, color-mix(in srgb, red 70%, transparent) 30% 70%, transparent 70% 100%); }") == []
    assert _soft_things(".a { background: linear-gradient(var(--ork-ink) 0 0); box-shadow: 0 0 0 2px red, inset 0 1px 0 3px blue; }") == []
    assert _soft_things(".a { filter: drop-shadow(1px 0 0 red) drop-shadow(0 1px 0 red); }") == []
    assert _soft_things(".a { background: linear-gradient(to bottom, red, blue); }")
    assert _soft_things(".a { background: linear-gradient(to bottom, black calc(100% - 40px), transparent); }")
    assert _soft_things(".a { background: radial-gradient(circle, red 0, blue 100%); }")
    assert _soft_things(".a { box-shadow: 0 0 0 1px red, -14px 10px 30px var(--ork-scrim); }")
    assert _soft_things(".a { filter: blur(2px); }") and _soft_things(".a { filter: drop-shadow(0 0 4px red); }")
