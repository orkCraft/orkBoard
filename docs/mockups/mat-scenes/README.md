# The mats' mockups (decisions §309 to §312)

Static pages of the six mats as decided on 14 November 2026, the person's Gemini takes laid on them. Each page is
self-contained (orkUI's tokens and these pictures); open it over http from the repository's root (`python3 -m http.server`),
not `file://`, or Chrome drops the CSS masks (the crafts' marks, the signs).

| Page | Mat | States (`?state=`) |
|---|---|---|
| `discussion.html` | Discussion: a card and its route's tokens on a ring | `differ`, `pick`, `undo`, `fab`, `note` (phone) |
| `choice.html` | Choice: two to six ways, the view above | `pick`, `undo`, `fab`, `note` (phone) |
| `slots.html` | Slots: the story map in pockets; the rolodex | `pick`, `undo`, `fab` |
| `scheme.html` | Scheme: decks and arrows | `pick`, `undo`, `fab`, `note` (phone) |
| `piles.html` | Piles: the discard by branch; the book by day | `book`, `pick`, `undo`, `fab` |
| `backpack.html` | The backpack's team: seats by the hero's steps, in pockets | `fab` |
| `../battle-field/index.html` | Battle, and the Gate | `preview-new`, `preview-old`, `inspect`, `undo`, `fab`, `note` (phone), `gate`, `gate-green` |

Every page takes `?face=desk` (1440 × 900) or `?face=phone` (390 × 844). Shots in `shots/` (and `../battle-field/shots/`);
`all-desk.png`, `all-phone.png`, `all-notes-phone.png`, `all-fab-desk.png` and `all-pick-undo-desk.png` are the contact sheets.

**Pictures** (prompts in `docs/pictures-cartoon.md`; the final cuts are orkUI's, these are the mockups'):
- `sheets/` the taken sheets: C1–C8 (the scenes' corner props, now unused on the mats: §311.1), G1–G5, H2's ork's hand;
- `surfaces/` F1–F5 and H1 (the tavern table, the parchment, the workbench, the scribe's desk, the backpack's leather, the pocket);
- the hand's cards past the row are dealt over every slot as strips (the drum, §313), a strip showing its price gem only;
- `props/header-bar.png` (G1), `props/signs/` (G2), `props/crafts/` (G3, white masks), `props/chips/undo.png` (G4) and
  `props/chips/obj-{die,token,card}.png` (the hand's three things, cut bare from G4 until G6 is taken), `props/hand-ork-*.png`
  (H2), `props/hand-pocket.png` (H1, the slots' pockets);
- `cut.py` cuts a 2 × 2 sheet of corner props; `cut_grid.py` any grid of framed tiles (`--white` for a mask).

**Left for the page's build** (seen in the last review, small): a phone's lifted rolodex card and its strips; a battle note's
edge on the phone; the mockups' words are placeholders (the Board's own data lays them, §301).
