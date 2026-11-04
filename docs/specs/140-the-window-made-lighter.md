# 140. The window made lighter

Decisions §247. **Builds:** the cheaper model, its parts with the areas they live in (the column's, the hand's, the
table's end, the mana's) · **Review:** the critical tests and each part's own · P1. The look: the decision's text; the
review's pictures (1440 and 390 px on `tests/test_column_browser.py`'s `ColumnHost`).

| Part | What | Where (and its tests) |
|---|---|---|
| **A1. The portal and the discard only when they hold something** | the ring drawn while a goal is ready for main or its checks run; Release's and Live's heads where its corners are, asleep alone, otherwise; the discard drawn from its first goal done | `table/portal.js`, `portal.css`, `table/road.js`, `table/discard.js`, `discard.css`; `tests/test_portal_browser.py`, `test_road_browser.py`, `test_discard_table_browser.py` |
| **A2. A pile's foot without a cut name** | the foot: rune, time or heads, state; the name in `title` and the words | `table/piles.js`, `column.css`; `tests/test_column_browser.py` |
| **A3. The pane's title only for a goal** | no *The whole project · through X* when no goal is picked; the row keeps back and **…** | `table/pane.js`; `tests/test_table_desktop_browser.py` |
| **A4. A lifted card says its title once** | a line equal to the title is not drawn; one sentence of what it says | `hand/stopcard.js`, `stopface.js`, `table/column.js` (To review's lifted card); `tests/test_lifted_card_browser.py` |
| **B. Hold and Later** | the words for putting a goal off; *Keep it* only *do not drop*; the to-do form's **Save** | `table/column.js`, `hand/routecard.js`, `hand/todoform.js`, the pile's list, `realm/lexicon.py` (`TERMS`, `was`); `tests/test_gui_wording.py`, `test_lexicon.py`, `test_column_browser.py`, `test_route_card_desktop_browser.py` |
| **C1. The potions** | the sizes kept; the now share alone under a potion; the week's words only when the week runs out first; an unread tool its mark, muted, no bottle, *Limits not read* | `hand/mana.js`, `hand/windows.js`, `mana.css`; `tests/test_hand_mana_browser.py`, `test_mana_two_windows_browser.py` |
| **C2. A tab's tool marks only where they differ** | sword and shield marks only on a party off the default tool or on several; a potion hovered lights tabs, not a 1 px outline | `table/tabmarks.js`, `table/tabs.js` (its css); `tests/test_leaders_table_browser.py` |
| **C3. One place moves at a time** | a running motion (the ring's sweep, a rune's glow, a leader stepping) only on the goal picked, else the first at work in the Orkmaster's order | `table/piles.js`, `table/backcard.js`, `table/card.js`, `table/column.css`, `table/moods.js` (stepping); a browser test |

## A1

1. The ring (`portal.js`, `.table-end`) is drawn only while a goal is ready for main (the discard's view holds one) or a
   goal's checks run (§188.3–4). Otherwise **no ring and no *Main***; Release's and Live's heads (`road.js`) stand where
   the ring's lower left and upper right corners are, asleep (§188.2), pressed as today.
2. The discard (`discard.js`) is drawn from its first goal done; **empty, nothing**: no frame, no word. A goal's flight
   to it lays it.
3. Tests: no ring with nothing ready; the ring with a goal ready; the corners' heads present without the ring; no
   discard when empty.

## A2

The foot (`piles.js` `col-foot`, line ~140 today): the rune, then the time or the leaders' heads and the count, then the
state's sign. **No `col-fnm`**; the foot's `title` and `aria-label` hold the goal's whole name. Test: no name text in a
foot; the `title` is the name.

## A3

`table/pane.js`: when no goal is picked, the title's words are not drawn (`mapName(...)`); the back arrow and the **…**
stay where they are. A goal picked: its name and its phases as today. Test.

## A4

On a lifted card (the hand's `stopcard.js`/`stopface.js`, the column's To review card in `column.js`): a line whose text
equals the title (trimmed, case-insensitive) is not drawn; the explanation is one sentence (*Its spec is ready; it starts
by itself in its turn.*), anything longer behind its **…**. Test.

## B. Hold and Later

1. **Hold**: today's *Later today* on To review (`column.js`, `ideas.ripe_hold`) is **Hold**, its `title` *Nothing
   starts it until you press Start now*; the card's state says *Held* (as today); *Back to review* stays.
2. **Later**: the route card's *Later, by itself* (`hand/routecard.js`, `ideas.route_later`) is **Later**, its line
   *Starts by itself after the reset, Mon 09:00* as today; the night's put-off is *Later* too in what is said (*Later,
   tonight 01:00*), its command unchanged.
3. §239.3's *Keep it* (if built) is **Hold**. *Keep it* stays only in the drop question (`table/dropgoal.js`). The to-do
   form's *Keep it* (`hand/todoform.js`) is **Save**.
4. `TERMS`: *Hold* (was *Later today*), *Later* (was *Later, by itself*), *Save*, *Limits not read*; the old words in
   `was`. Commands and keys keep their names.
5. Tests: the wording test green; the buttons say Hold, Later, Save.

## C1. The potions

`mana.js`: the bottle's size stays the week (§192). Under the potion **the now share alone**; *week 80%* only while the
week is the window that runs out first (its share the lower), else only in the words. A tool whose limits were not read:
its mark muted, **no bottle**, and in its words *Limits not read* (today an empty potion with *?*). Tests.

## C2. A tab's tool marks

`tabmarks.js`: the second line's marks (sword + Does's tool, shield + Checks's tool) are drawn only when the party's Does
or Checks run on a tool other than the project's default (§177.1), or on several (the dot). A Lean party keeps its faint
shield. A potion hovered lights the tabs whose parties run on it by the tab's own lit state (as hover lights a tab), not
by the 1 px outline (`markedTool`). Tests.

## C3. One place moves at a time

A motion that runs on (`ork-sigil-sweep` on a face-down card, `.ork-elem.is-glowing` on a rune, a leader's stepping in
the tabs) runs only on **the goal picked**, else on **the first goal at work in the Orkmaster's order** (the column's
order); every other card shows its state still (its sign). Motions played once are unchanged (§89.0). Test: with two
goals at work, one glows.
