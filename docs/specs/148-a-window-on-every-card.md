# 148. A window on every card, never empty

Decisions §252. **Builds:** the cheaper model, after spec 147 B and C are in: A (the host and the window), then B (its
places) with spec 147 D · **Review:** the critical tests and each part's own · P1.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The window and its picture** | one window component choosing what it shows; the host serves a goal's first picture as a thumbnail | a new `table/cardwindow.js` + `cardwindow.css`; the snapshot's goal node and hand card (`gui/ideas_map.py` or where nodes and stops are built), `realm/idea_photos.py` (a `first` and a thumbnail), the server's file route; `tests/test_idea_photos.py`, a new `tests/test_card_window_browser.py` |
| **B. Its places** | the hand's card under its cut, *At work*'s front card, the discard, a lane's card's fallback, the opened card, a new goal's card with what is attached | `hand/stopcard.js`, `hand/pluscard.js`, `hand/fieldsquares.js`, `table/piles.js`, `table/discard.js`, `table/card.js`; the tests of each (`test_hand_desktop_browser.py`, `test_column_browser.py`, `test_discard_table_browser.py`, `test_lifted_card_browser.py`, `test_field_squares_browser.py`) |

## A. The window and its picture

1. **`table/cardwindow.js`**: a pure `windowOf({ made, picture, words })` → `{ kind: "made" | "picture" | "words" | "none",
   … }` in §252.2's order, and `CardWindow({ of, h })`: one frame (the lanes' window frame of `table/card.js`, its tokens),
   `h` its height from the place; `made` drawn by `table/made.js` as today; `picture` an `<img>` with `object-fit:
   contain` on the table's ground, `loading="lazy"`, its `alt` the goal's name; `words` the text in the reading face,
   clamped to the lines the height holds, real text.
2. **The host**: a goal's node in the snapshot carries `picture` (a URL, or absent): its first attached picture
   (`idea_photos.listed`) served as a thumbnail of at most 320 px on its longer side (made once beside the photo, e.g.
   `photos/1.thumb.jpg`, with Pillow if it is in the project's dependencies, else the photo itself when it is under
   200 KB, else none), through the server's existing route for the Board's files (find where `made` URLs are served,
   §249.3 / spec 142 D) and never outside the project's `.orkcraft/`. A hand card about a goal carries the same
   `picture`. No model is called.
3. Tests: `windowOf`'s order (made over picture over words, none when all are missing); the host's `picture` for a goal
   with a photo and without; the thumbnail is the size it says; the route refuses a path outside the state.

## B. Its places

1. **The hand's card** (spec 147 C): under the cut, the window in place of the *why* lines (its height the same, the
   hand unchanged): `made`, else `picture`, else the why words. A fork with a picture on each side: the two side by side.
2. **At work's front card** (spec 147 B.4): the window where *now* was (the same height; the wait bar stays): `made`, else
   `picture`, else what it does now. The cards behind still show only their foot.
3. **The discard's card**: its window between the name and the foot: the last `made`, else the goal's picture, else its
   line.
4. **A lane's card**: its window as §249.3 has it; where it would draw today's type sign alone, it draws the goal's
   picture or the task's words instead.
5. **The opened card** (spec 147 D.1): a window at the top of its body, 160 px high (the card stays 404 × 566; the body
   scrolls): `made`, else `picture`, else nothing extra (its question is its body).
6. **A new goal's card** (spec 147 D.2): its window holds what is attached as it is attached: the pictures
   (`fieldPhotos`) as thumbnails of the data the field holds, the files (`fieldFiles`) as chips (`FileChips`), and is the
   place a picture or a file is dropped on (the field's own drop, moved onto the window); with nothing attached, the hint
   words. The field's other controls stay.
7. Tests: each place draws the window and its order (a goal with a photo shows it in the hand's risen card, *At work* and
   the discard; without one, the words); a new goal shows a picture's thumbnail in its window when one is attached.
