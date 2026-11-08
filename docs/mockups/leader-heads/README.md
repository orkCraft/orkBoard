# The leaders' heads: where they go next

Work the owner and Claude did on 7–8 November 2026. **Nothing here is in the product or in orkUI.** It is the record of
what was tried, what the window showed, and what the next round should aim at.

## Why the heads must change

orkUI's heads are 12 × 11 cells. That was right when a head said *a craft and a tier*. Since §266 a leader is **a hero of
a school** (several heroes a craft), and a head must say *who*. In 12 × 11 the heroes differ only by a few recoloured
cells (`checks/00-heroes-today.png`: four unicorns are one helm in four shades). They cannot be told apart at 24 px, nor
without colour, and recolouring now clashes with *colour is the party*.

## What the window needs from a head (learned the hard way)

- **An icon, not a portrait**: the head only, the face filling the frame; a bust with shoulders and a hood is a blob at
  24 px (`checks/02-portraits-at-our-sizes.png`).
- **A real 24 × 24 grid, 2 px a cell**: 48 px in a tab, 24 px in a squad or a card. The tab grows from 36 to 48 px (36 does
  not divide a 24 grid). The members (Grunt, elves, skeletons…) can stay 12 × 11: same 2 px pixel, less detail.
- **The six moods must read at 48 px** (calm, focused, worried, says no, pleased, asleep, §201), carried by big eyes,
  brows and mouth; at 24 px only the big gestures survive.
- **Identity in layers**: the race by the head's shape and its big feature; the hero (the school) by one signature detail
  in the silhouette; the tier by its gear; the mood by eyes and mouth (overlays shared across a race).
- **Mid-tone skin, bone-coloured horns**, clearly lighter than the window's #151412; no red or yellow that reads as a signal.
- Gemini does not keep a pixel grid: it draws at ~60 cells whatever is asked. Its sheets are concept art; the sprites are
  drawn on the grid by hand afterwards (`sketches/` shows the method).

## What was tried, and the owner's verdict

| round | references | verdict |
|---|---|---|
| dark fantasy portraits | `references/01` | good art, wrong job: portraits, one hood, all alike at 24 px |
| dark fantasy icons | `references/02`, `checks/03` | the right *format* (icon, face fills, race by silhouette); too grim, mixed rendering |
| shaman heroes, dark | `references/03` | consistent, but a generic grim ork mask |
| caricature (cartoon) | `references/04` | funnier, but the gags were weak and a red line read as blood |
| stickers (the owner's examples) | `references/05`, `06`, `checks/04`, `05` | the moods read best of all, but **far too cute** |
| sticker shaman | `references/07` | too cute |
| ugly-cute v1, v2 | `references/08`, `09`, `checks/06`–`08` | the character finally ours (a grumpy, scheming ork); v2's moods read at full size, but drawn at ~60 cells, dark |
| redrawn by Claude on 24 × 24 | `checks/09`, `10`, `sketches/shaman24.py` | the moods read at 48 px, but **still cute** |
| grotesque card creature v1 | `references/10`, `checks/11`–`14` | the character right at last (heavy, menacing, dry); the skin too dark and grey, the whites small: at 48 px calm, focused, worried and asleep read, no and pleased do not (pleased reads as a snarl); at 24 px only worried |

**The owner's direction now: closer to Slay the Spire.** Not cute, not a sticker, not a cartoon: a hand-painted roguelike
card's creature (grotesque, heavy, a strong silhouette, a dramatic light) translated into pixel art, with the moods kept.

## The heroes (from `docs/mockups/merchant`), and a signature each (a proposal, by shape, never by colour)

| race (craft) | hero (school) | signature |
|---|---|---|
| shaman (Tech) | Sh.man (C4 and hotspots) | three square beads in a braid, the last one burning |
| | Domain Shaman (DDD) | a line of war paint splitting the face, its halves disagreeing |
| | Spike Shaman (XP) | an iron spike through one ear, spikes on the scalp |
| | Fitness Shaman (evolutionary architecture) | one horn branching like an antler, still growing |
| unicorn knight (Product, a helm with no mouth) | Angel Invest Knight (opportunity solution tree) | the horn branching in three, like a tree |
| | Jobwise Knight (JTBD) | a visor raised like a work helmet's peak |
| | Pivot Knight (Lean Startup) | the horn bent at a right angle |
| | Appetite Knight (Shape Up) | an hourglass on the brow |
| dryad (Design) | Pixel-Perfect Dryad (Nielsen's heuristics) | a loupe over one eye |
| | Diamond Dryad (Double Diamond) | two diamond crystals on the antlers' tips |
| | Atom Dryad (Atomic design) | three dots orbiting the antlers |
| | Sprint Dryad (Design sprint) | antlers swept back, a headband |
| imp (Run) | Uptime Imp (SLOs) | one horn broken off |
| | Lantern Imp (Observability) | a lantern hanging from a horn |
| fairy gnome (Marketing) | Growth Hack Gnome (AARRR) | a pirate's eye patch |
| | Store Gnome (ASO) | a price tag on a string from a wing |
| lich (Release) | Release Night King | a thin crown of black iron spikes |
| the Orkmaster | — | an olive ork, big tusks, a battered crooked crown, no hood |

Tiers (§154, §162): the same face bare, in iron, in a hood.

## Files

- `references/`: the sheets Gemini made, in order (the owner's prompts are in the conversation; the last ones are below).
- `checks/`: each sheet at the window's sizes beside today's heads, and in the Tech tab.
- `sketches/check_sheet.py`: a Gemini sheet of six moods (3 × 2) cut into heads at the window's sizes, beside today's
  heads (`python docs/mockups/leader-heads/sketches/check_sheet.py SHEET.jpg OUT_DIR [race]` → `OUT_DIR/sizes.png`).
- `sketches/shoot_tab.py`: those heads put in the Tech tab on the table-look mockup, one shot a mood (see its docstring).
- `sketches/shaman24.py`: the shaman drawn on 24 × 24 with six moods as overlays (`python sketches/shaman24.py OUT_DIR`);
  `sticker24.py`, the sticker round; `scale2x.py`, the dropped Scale2x round.

## The last prompt's rules worth keeping

```
An ICON, not a portrait: the head only, front view, the face filling the frame; the race's big feature breaks the
silhouette. A strict 24 x 24 pixel grid shown enlarged (hard square pixels, no anti-aliasing, no gradients). Two or three
tones per material, light from the top left, a 1-pixel outline. The EYES stay big and expressive (at least 5 x 4 pixels
with a dot pupil): the mood is carried by the eyes, the brows and the mouth as big simple gestures. Mid-tone skin,
bone-coloured horns, lighter than the #151412 background. Moods: calm = deadpan; focused = one eye squinting, the other
wide; worried = huge eyes, a forced grin, a sweat drop; says no = side-eye, brows down; pleased = eyes closed in arcs, a
toothy grin, a sparkle; asleep = eyes as lines, a snot bubble. No text. Do not copy any existing character.
```

## The next round: a grotesque card creature (8 November 2026)

What makes a hand-painted roguelike card's creature, and what of it survives 24 × 24:

| trait | in the painting | on 24 × 24 |
|---|---|---|
| silhouette | one exaggerated mass (a huge jaw, a tiny skull, asymmetric horns), readable as a black shape | **survives best**: the race and the hero live here |
| proportion | heavy below: the jaw and the underbite wider than the brow, the eyes set deep and small | survives; the eyes stay big in *contrast*, not in size |
| light | one hard side light, half the face in shadow, a rim light on the dark side | survives as two flat planes (lit / shadow) at 48 px; at 24 px only the light side |
| line | a thick, uneven dark contour, broken where the light hits | a 1-px outline in the hue's darkest tone, dropped on the lit edge |
| palette | muddy, desaturated, one accent | survives; the shadow must stay lighter than #151412, so the rim light is not optional |
| face | pale eyes glinting in dark sockets, a heavy brow shelf, teeth | the moods read by the eyes' whites against the socket's shadow and by the mouth's shape |
| brushwork, wrinkles, texture | everywhere | **lost**: one or two dents in the planes at most |

The cute devices go (no sweat drop, no snot bubble, no sparkle): the mood is the face alone. Calm = heavy-lidded,
unimpressed; focused = one eye a slit, the other glaring; worried = pinpoint pupils in wide whites, a clenched grimace;
says no = side-eye, the jaw jutting, the lower lip over a tusk; pleased = a wide crooked grin, eyes narrowed to glinting
crescents; asleep = eyes shut as heavy lines, the jaw slack, a string of drool.

The prompt given to Gemini (one sheet first, the shaman):

```
A sheet of six pixel-art ICONS of the same creature's head, arranged in a 3 x 2 grid of equal cells on a perfectly flat
#151412 background (no vignette, no glow, no shadow cast on the background, no frames, no text, no labels).

The creature: an old ork shaman, grotesque and heavy, like a monster from a hand-painted dark roguelike card game, not
cute, not a cartoon, not a sticker. A small sloping skull, a brow shelf like a ledge, a massive underslung jaw much wider
than the skull with two thick chipped tusks pushing up past the upper lip, a broad flattened nose, ragged ears. Two heavy
ram horns of old bone curling down beside the jaw, one horn cracked. A thin braid with three square beads hanging from
one horn. Asymmetric, lumpy, weathered: it should feel heavy and a little menacing, with dry humour, never sweet.

Format: an ICON, not a portrait: the head only, front view, no neck or shoulders, the head filling the cell; the horns
and the jaw break the silhouette so the head reads as a black shape. Pixel art on a strict 24 x 24 grid shown enlarged:
hard square pixels, no anti-aliasing, no gradients, no dithering noise. One hard light from the upper left: the lit
side in two flat tones, the other side in shadow, with a thin cold rim light along the shadowed edge so that edge stays
clearly lighter than the background. A 1-pixel outline in the darkest tone of each material, left out where the light
hits. A muted, desaturated palette of at most 12 colours: grey-olive skin (mid-tone, clearly lighter than the
background, even in shadow), old bone horns and tusks, near-white eyes, a dark brown-violet mouth. No red, no yellow, no
orange anywhere.

The eyes sit deep under the brow, but their whites are large (at least 5 x 4 pixels) with a 1-pixel pupil, bright
against the shadowed sockets: the mood is carried only by the eyes, the brows and the mouth, as big simple shapes. No
sweat drops, no bubbles, no sparkles, no symbols. Same head, same size, same position and the same light in all six
cells; only the face changes:
1. calm: heavy half-closed lids, the mouth shut with the tusks up, utterly unimpressed.
2. focused: one eye squeezed to a slit, the other wide and glaring, the brow knotted.
3. worried: both eyes wide open with pinpoint pupils, the brows pushed up and together, the mouth stretched into a
   clenched grimace showing the teeth.
4. says no: a hard side-eye, the brows down, the jaw jutting forward, the lower lip pushed up over one tusk.
5. pleased: a wide crooked grin full of uneven teeth, the eyes narrowed to glinting crescents, the cheeks raised.
6. asleep: the eyes shut as heavy lines, the jaw hanging slack and open, a thin string of drool.

Do not copy any existing character or any existing game's art.
