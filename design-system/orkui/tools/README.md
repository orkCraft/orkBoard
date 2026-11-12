# orkUI / office / tools

**A race's tool, for a pick of four** (0.16.0). Where the person picks one of four (a look, a name, a way), each choice's card can wear
its party's tool: one tool per race, the craft of its party said with a joke, and **four variants of it**, one silhouette with one
zone that changes, so four cards side by side read as one tool told apart at a glance.

    drum        orks (Tech)                    a shaman's drum with a spanner for its beater; the rune on its skin changes
                                               (drum-gear, drum-bolt, drum-spiral, drum-tusk)
    bow         elves (Design, Art)            a bow whose arrow is a brush; the brush changes
                                               (bow-round, bow-flat, bow-drip, bow-fan)
    pick        goblins (Run, LiveOps, Data)   a pickaxe (data mining); what it dug out changes
                                               (pick-gem, pick-coin, pick-gear, pick-mushroom)
    bell        gnomes (Marketing)             a crier's handbell; what rings out of it changes
                                               (bell-waves, bell-stars, bell-note, bell-hearts)
    map         knights (Product, Game design) a treasure map (the roadmap); the mark at the path's end changes
                                               (map-cross, map-star, map-heart, map-crown)
    hourglass   skeletons (Release)            an hourglass (the release date); its finial changes
                                               (hourglass-candle, hourglass-bone, hourglass-gem, hourglass-ring)

**Since 0.42.0 each also has the owner's colour take**, a transparent, trimmed, centred PNG beside its masks: `<tool>-<variant>.png` at 28 x 28, `@2x` 56 x 56 and `@3x` 84 x 84 (cut, not traced, from
the sheets `w1-tools-1.jpg` and `w2-tools-2.jpg` by `tools/build_things_from_art.py`, which `races/art/things.json` feeds; one tool's four variants share one box, so the thing does not jump). A colour picture
cannot be a CSS mask, so `.ork-tool` still draws the two-tone SVGs below, coloured by party or token, and no CSS draws the PNGs yet.

Each is a **14 x 14** drawing in **two tones**, as a goal type's big sign (`../signs/README.md`): `<tool>-<variant>.svg` the silhouette and
`<tool>-<variant>-light.svg` its light, in the signs' format, made from `../../drawings/drawings.json` by `python tools/build_big.py`.
`.ork-tool` in `components.css` draws one at **28 px**, two pixels a cell, the size of a pick's window, never another: the silhouette in
the colour of its text (the goal's element on a pick's card), its light over it lightened toward the ink. A tool adds no colour of its
own and is `aria-hidden`: the card's words say the choice.

    <span class="ork-tool bow-drip" aria-hidden="true"></span>     28 x 28, in the text's colour
