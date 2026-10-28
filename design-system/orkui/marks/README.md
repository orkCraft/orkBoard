# orkUI / office / marks

The AI tools' marks and the level chevrons of orkLine's camp, as orkcraft 0.2.9 drew them: 10 pictures, each 16 x 16 and
`@2x` 32 x 32 (20 files), and their 20 ink versions. Copied unchanged from orkLine (`design-system/sprites/icons` at `be11f7f`). They are small accents
beside a name, never a picture on their own (`.ork-mark` in `components.css`).

    harness-<tool>.png, harness-<tool>@2x.png   the tool's mark in its own colours, with the house's dark outline: an orange
                                                starburst (claude), a green tile with >_ (codex), an arch in four colours
                                                (agy, Antigravity), a grey cube (cursor), a purple winged staff (hermes), a
                                                rose tile with a pi (pi); no one's logo
    harness-pipeline.png, @2x                   a scheme's P: a step that is a pipeline and not a tool
    rank-1.png, rank-2.png, rank-3.png (+ @2x)  one, two, three gold chevrons: Novice, Seasoned, Veteran

**The ink versions** (0.15.0, orkUI's own): each tool's mark and the ranks' chevrons also come in ink, `<name>-ink.png` and
`<name>-ink@2x.png` (`harness-claude-ink.png`, `rank-2-ink@2x.png`, ... 20 files): the mark's shape in the ink token
(`--ork-ink`) and no other colour, fully opaque or clear. The house's dark outline is dropped, on a tile (codex, pi) the light
glyph is cut out of the tile, and the cube (cursor) keeps a line between its faces. They are for a seat's tool under its head,
a limit's chip and the ranks beside a name; the coloured marks stay for the seat's popover, where a tool is chosen. They are
made from the coloured ones by `python tools/build_icons.py` (`--check` compares them), never drawn by hand.

Drawn by orkLine's `tools/icon_sprites.py` on a pixel grid, one letter a pixel; so they are drawn at their own size or a
whole multiple (16, 32), `image-rendering: pixelated`, never resampled. Copied unchanged: a change is made in orkLine's
`tools/icon_sprites.py` and copied over whole, never edited here (`tests/test_orkui.py` compares them with orkLine's when
a checkout is beside this one). Their colours (the coloured ones) are the tools' own, not the look's tokens: a person tells the tools apart by them; the ink
versions say it by their shape.
