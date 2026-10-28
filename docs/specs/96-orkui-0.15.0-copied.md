# Spec 96 — orkUI 0.15.0 copied: the window's look, its heads and its motions here

The owner and the PM, 28 October (decisions §148, §149.2–§149.4, §151.9, §152.4, §154, §155, §158.5; orkUI's
`docs/specs/0.15.0-the-window.md`). orkUI 0.15.0 is made in orkUI (its parts A, B, C); this spec copies it here and keeps
today's page whole on it. **Builds:** a cheaper model, reviewed by Claude · **Review:** full · P0. **One part, D**, after
orkUI 0.15.0 is in orkUI's `main`; before spec 98's C, D, E and spec 99's A.

**What it is, and is not:** the copy (`python -m orkboard.design.orkui <orkUI>`), what of orkUI's `office/` the window
no longer draws left out of it, and the page's few lines that name what 0.15.0 renamed or resized (the heads at 16 and
32, the sign `moon`, the AI tools' marks in ink where the window draws a seat's tool and a limit's chip). Not: any new
face (spec 98 draws the frame on these parts); the races by party (spec 99 A); the phone's faces beyond keeping them
working (spec 94 E removes them).

| part | builds | files (and their tests) |
|---|---|---|
| **D. The copy** | §1–§3 | `design-system/orkui/**` (by the command only), `orkboard/design/orkui.py` (`SKIP`, `race_png`'s sizes), the page's sheets and modules that name a head's size, `.small`, the sign `night` or a coloured mark where the window draws a seat's tool or a limit's chip (`static/js/orkui.js`, `static/js/**/*.css`, `static/page.css`); `tests/test_design_system.py`, `tests/test_orkui_copy.py` (or the test that runs `orkui.problems`), the browser tests that pin a head's 24 × 22 size |

## 1. The copy (D)
`python -m orkboard.design.orkui /home/user/orkUI` with orkUI at its 0.15.0 commit; `ORKUI.json` stamps it. Never an
edit by hand (`orkui.problems()` stays empty). **Left out** (`orkui.SKIP`, so the stamp lists only what is copied):
`emblems/` (§148.9: the signs say it; no face draws one) and `races/v1/` (the 12 × 11 heads are Orkline's). Kept, for the
phone until spec 94 E: `moons/` and the goal types' signs.

## 2. The page on it (D)
1. **Heads**: `race_png` gives the 16 × 16 file (`big`: the 32 × 32 @2x); a head drawn smaller than 16 px today is drawn at
   16 (§148.7); `.ork-race__head.small` (gone in 0.15.0) is no longer written; a head drawn at 24 × 22 or 48 × 44 is
   drawn at 16 or 32 (whole pixels: `image-rendering: pixelated`, never a size between).
2. **Signs**: the page writes `moon` where it wrote `night` (orkUI keeps `night` as its alias for Orkline and the
   phone).
3. **Marks**: a seat's tool under its head and a limit's chip draw the ink mark (`harness-<id>-ink.png`); the coloured
   mark stays where a tool is chosen (a seat's popover, Settings' AI tools).
4. **Icons**: orkUI's own icons (←, ×, …, +, the search, the microphone, ▶, ■, the chevrons) are drawn at 14, 21 or 28
   px, never at 24 (its 7 grid).

## 3. Tests
The copy's stamp and `problems()` empty; the left-out folders absent; `tests/test_design_system.py` as it is (the sheets
carry no colour of their own); every desktop browser test that pinned a head's or an icon's size pinned anew; the
critical tests (`tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`) and the phone's
browser tests still passing (it keeps `night`, `moons/` and the type signs).
