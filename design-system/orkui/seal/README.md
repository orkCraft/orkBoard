# orkUI / office / seal

**A mat's move's seal** (0.43.0): the round token a mat's move is pressed with, in the owner's colour take (sheet `races/art/cartoon/e2-seal.jpg`), four states: `rest` (bronze, at rest), `ready` (gold with a yellow
ring: it can be pressed), `pressed` and `dim` (stone grey: not now). `<state>.png` is **96 px across at 1x**, `@2x` 192 and `@3x` 288, transparent and centred; the four lie on one canvas and one scale, so the seal does
not jump from state to state. Cut like the heads (not traced) by `tools/build_things_from_art.py` from `races/art/things.json`. Nothing in `components.css` draws them yet.
