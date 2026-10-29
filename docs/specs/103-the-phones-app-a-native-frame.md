# Spec 103 — The phone's app a native frame: the hand first with the top card's context, the table on its side without the hand, push through a relay that reads nothing, an answer from the notification, widgets

The owner, 29 October (decisions §174; §128, §145, §150, §153.6; spec 42 §3, spec 94 §3–§4). The phone's slice, **S5**,
after spec 94 holds on the owner's phone. **Builds:** Claude · **Review:** full · P1. **A and B at once** (the page; they
share no file but the narrow width's signal, which A reads and B does not change), **C at once with them** (the relay: no
file of Orkboard's), **then D** (the native frame, on A–C), **then E and F at once** (the widgets; the host's words).

**Changed by decisions §178 and §179** (the owner's answers to `docs/mockups/phone/` v1): spec 94 B–E are built first and the phone
becomes the page (§178.1); upright the potions stand in one row at the top, left of *The Board*, the frame on the tool the
work goes to (§1.2.5); the Orkmaster's line at the screen's top (§1.6); *Go on paid?* is a card of the hand (§1.7, §5.4); one
stack (§1.1); the Board on a phone only on its side, with the discard and the portal (§1.4, §2.1); the portal merges from the
phone too. Where this spec's text below says otherwise, §178 holds.

**What it is, and is not:** the narrow width's first screen made the hand with the top card's context; the low window on a
touch screen made the table without the hand; a native frame (Capacitor) round the one page, as `vscode/` is the desktop's,
for iOS first and then Android; the relay; the notification's words and actions; the widgets. Not: a second face (the frame
draws nothing of the Board, §128); a new command for answering (the frame sends the hand's own); a Live Activity while Play
runs (§6); the stores' listing and its pictures (§150.5, the marketing's).

| part | builds | files (and their tests) |
|---|---|---|
| **A. The hand first, the top card's context** | §1 | new `js/hand/context.js` (the context over the hand), `js/hand/hand.js` (the narrow width's order: context, stack, blank card), `js/hand/hand.css`, the narrow width's screens (*The Board* opens the table's screen, spec 94 §3.2); new `tests/test_hand_context_narrow_browser.py` (on `tests/narrow.py`) |
| **B. On its side, the table without the hand** | §2 | the low window's layout (spec 94 §3.1, where it is built): no fan, no blank card under `pointer: coarse`; a stop's sign opens its card over the table (`js/hand/questioncard.js`, `stopcard.js` drawn there as they are); new `tests/test_low_window_touch_browser.py` |
| **C. The relay** | §3 | new `relay/` (its own small service, its own `pyproject.toml`; nothing in `orkboard/` imports it, nor it Orkboard): `relay/app.py` (the two routes), `relay/vapid.py` (the signature checked), `relay/apns.py`, `relay/fcm.py`; new `relay/tests/` |
| **D. The native frame** | §4, §5 | new `mobile/` (Capacitor: `capacitor.config.ts`, `ios/`, `android/`, the page copied in by `npm run page`), `mobile/ios/App/NotificationService/` (opens a sealed push), the frame's bridge in `js/frame/frame.js` (native or not; pairing, push, arrival, orientation through it); `gui/phone_push.py` (the words and actions, §5), `gui/settings` row (§3.5); `tests/test_phone_push.py`, `tests/test_architecture.py` (`mobile/` imports nothing of the Board's face but the page it carries), `cd mobile && npm test` |
| **E. Widgets** | §6 | `mobile/ios/App/Widgets/` (WidgetKit, App Intents), `mobile/android/app/src/main/java/…/widget/` (Glance), the top card kept by the frame (`js/frame/frame.js` → the bridge's `setTopCard`) and by the Notification Service Extension; `gui/phone_push.py` (the quiet `top` push, §6.4); `tests/test_phone_push.py` |
| **F. The words** | §0 | `realm/lexicon.py` `TERMS` (*relay*, *widget*), `gui/phone_push.py` `KIND_WORDS` unchanged, spec 42 §3.1's count gone; `tests/test_lexicon.py`, `tests/test_gui_wording.py` |

## 0. The words
- New strings: *The Board* (the hand's top, the narrow width), *Recommended: <pick>*, *<member> waits for your answer*,
  *Take the pick*, *Open*, *Turn the phone on its side to see the Board* and *The work waits for your answer* (§178), *New goal* (the widget's, as the hand's), *Notifications to the app go through Orkboard's relay,
  sealed: it reads nothing and keeps nothing.* (Settings, under Notifications), *Sent when the computer answers* (kept from
  spec 94 §2.4, on an answer the notification could not send).
- `TERMS` gets two lines: `relay` (*relay*: the server of ours that passes a notification, sealed, to Apple's or Google's
  push service; spec 103 §3) and `widget` (*widget*, *widgets*: the app's small window on the phone's home or lock screen,
  the top card or *New goal*; spec 103 §6).
- Never in what a person reads: a count of what waits, *card*, *deck*, *stack* (spec 95 §12), *APNs*, *FCM*, *VAPID*.

## 1. The hand first, the top card's context (A; §174.1–§174.2)
1. **At the narrow width the first screen is the hand**, from the top: the potions' row and *The Board* (§1.2.5), the top
   card's context (§1.2), **one stack** (one question a card, its depth its edges, §153.6; every goal's cards in Needs you's
   order, a goal's together, §178.6), the blank card with the microphone at the foot. The row of heads and the table go to
   their own screen (§1.4).
2. **The context** (`js/hand/context.js`), over the stack, never more than a quarter of the screen's height, its own scroll
   past that (the stack and its answers never move):
   1. **Who and which goal**: the leader's head (24 × 22) and its party's name; the goal's element, its type's sign and its
      short name. A project question (§153.2, no goal) says the project's name instead of a goal.
   2. **Why**: the question's `why` (one line, as the leader wrote it, `core/idea_talk.py`), in the body's face, never the
      pixel face. No `why`, no line: never a filler.
   3. **The leader's pick**: *Recommended: <pick>* when the card has one.
   4. **What waits on it**: *<member> waits for your answer* when the card `blocks`; nothing when it does not. No number.
   5. **The tools** (§178.2, §179.1): one row at the top, left of *The Board* and no taller than it: each tool its mark with
      its share under it (*62%*, `levelOf`'s colours), **no bottle**, a 44 px target (`hand/mana.js`, the row's own layout
      at the narrow width under `pointer: coarse`);
      the frame on `town.mana.now`, else the Main tool (§178.3), sliding as on the desktop; the paid slot after them while a
      yes holds. A press opens what used it, as on the desktop. With the hand empty the row stays, *The Board* beside it.
   A press on the context opens the goal's way over the pane (§142); **←** comes back to the same card.
3. **When the top card goes** (answered, let go, *Let … decide*), the context changes with the next card, at once (no new
   motion, spec 95 §9). With the hand empty the context is not drawn and the blank card takes the screen.
4. **The Board** (a 44 × 44 target at the top right; its label *The Board*) opens the table **on its side only** (§178.7): in
   the native app the frame turns the screen to its side (§4.4); in a browser, upright, it says *Turn the phone on its side
   to see the Board* (nothing turns a web page). Under `pointer: coarse` there is no upright table; a narrow window with a
   fine pointer keeps spec 94 §3's.
5. Turning keeps the place (§150.4): the card on top upright is the goal lit on the table on its side.
6. **The Orkmaster's line** (spec 105 D.3, `table/notice.js`): when `town.mana.moved` is new, a strip at the screen's top over
   the potions' row, the crowned head, the line, *Dismiss*; put away as on the desktop.
7. **Go on paid?** (spec 105 C, `hand/paidcard.js`) is a card of the stack: its context the Orkmaster's crowned head and the
   project's name, no goal, no *Recommended*, *The work waits for your answer*; its answers on the card.

## 2. On its side, the table without the hand (B; §174.3)
1. **A low window under `pointer: coarse`** (under 500 CSS px of height, 760 or more of width): the table compact as §150.2
   says, **without the hand**: no fan, no blank card; the table takes the whole height. **The discard and the portal stay**
   on the table (§178.7; spec 104 C, spec 105 F): at the table's right edge **one column, the portal over the pile** (the portal's line over it, the word *Main* its label for a screen reader), and a goal ready for main a card **left of the pile** (the owner, `docs/mockups/phone/` v8). **The foot is the
   goals' legend** (§179.2, §179.4): each goal on the table its type's sign in its element's colour and its short name (the
   moon beside it while it waits for the reset), in the lanes' order, one row (sideways scroll if it must), 44 px targets; a
   press picks the goal and lights its cards. **A token** on its side is its task's type's sign in its goal's element's
   colour (the sign 28 px on a 52 × 72 card, two to a lane: the owner, `docs/mockups/phone/` v6); a task that asks keeps the
   alert's edge.
2. **A stop's sign on a head** (✗ or !, spec 53 §1.2) is a press: it opens that stop's card over the table, answered there as
   in the hand; the card closes and the table stays. Nothing else of the hand is reachable on its side.
3. **A low window with a fine pointer** (a laptop's split screen) keeps §150.2's fan, unchanged.
4. A goal is written upright: on its side there is no field for one (§150.3's field goes on touch).

## 3. The relay (C; §174.5)
1. **Its own service** under `relay/`, stateless, Python: two routes, nothing kept but each device's registration (the
   device's push token, its platform, the computer's VAPID public key, when it was registered) in one small table.
2. **`POST /register`**: the app sends its platform (`ios`, `android`), its native token and the paired computer's VAPID
   public key (from `mobile.hello`); the relay answers an endpoint `https://<relay>/p/<id>` (`id` 32 random bytes,
   base64url), which the app hands the computer as a Web Push subscription's `endpoint` with its own `p256dh` and `auth`
   (`mobile.push_on`, as a browser's today). The computer's side is unchanged (`gui/web_push.py`).
3. **`POST /p/<id>`**: a Web Push request as RFC 8030 and RFC 8291 make it. The relay checks the VAPID signature (RFC 8292)
   against the key registered for `id` (else 401), the size (else 413), a rate per `id` (else 429), and passes the sealed body
   to APNs (`mutable-content`, an alert the extension rewrites) or FCM (a data message). `Urgency: very-low` goes as a
   background push (§6.4). It answers 201, or 404/410 when the platform says the token is gone, so the computer drops it as
   today (`push_sent`'s `gone`).
4. **It reads nothing and keeps nothing**: the body is sealed to the device; no body is logged, only the status and `id`'s
   first 8 characters.
5. **Settings say it** (§0), under Notifications, on a device paired through the app; the PWA's notifications go as today,
   straight to the browser's push service.
6. Where it runs and what it costs: asked again later (§7). Until then the app's builds point at a relay named by its config.

## 4. The native frame (D; §174.4)
1. **Capacitor, `mobile/`**: `capacitor.config.ts`, `ios/`, `android/`; `npm run page` copies the page (what `gui/pwa.py`
   serves under `/app/`) into the app. The page is carried in the app, never loaded from the computer; a computer and an app
   of different versions meet as today (`mobile.hello`'s `commands`: what the phone may not do is not offered, spec 94 §2.2).
2. **Pairing**: the QR's link (`gui/phones.py` `pair_link`: the address, `fp`, the code) read by the camera; the socket's
   certificate **pinned** to `fp`, and refused otherwise (*This is not the computer this phone was paired with.*). The device
   token kept in the Keychain (Android's Keystore).
3. **`js/frame/frame.js`** asks the bridge (`window.Capacitor`) whether it runs native: pairing, push's renew and drop, the
   arrival (`#from=push-…`) and the orientation go through it; in a browser, as spec 94 §4.2 has them.
4. **The orientation**: free everywhere (§150.1) but *The Board*'s screen, which the frame turns to its side and frees
   again on **←**.
5. **The Notification Service Extension** (`mobile/ios/App/NotificationService/`) opens the sealed body (RFC 8291 with
   CryptoKit; the key in the app group's Keychain), writes the notification's words (§5) and the top card for the widgets
   (§6.3); on Android the app's messaging service does the same.
6. Apache-2.0 as the rest; Capacitor and its plugins as they come, their licences beside them and a line in `NOTICE`.

## 5. A notification says the card (D; §174.6)
1. **What goes and when** stays spec 42 §3.1 (`gui/phone_push.py`): an answer that waits, the morning; never in the quiet
   hours, under Do not disturb, to a device whose socket is open, more than one a tag every `PUSH_GAP_S`.
2. **Its words**: title, the leader and the party (*Tech asks*); body, the goal's short name and the question's first line, at
   most 120 characters (*Passkey · Which sign-in first?*). A project question, the project's name for the goal's. The morning's
   as today, less its count.
3. **No number**: `badge` is no longer sent as a number (the app shows no badge; Android a dot); *3 wait for your answer* goes
   from the body.
4. **Its actions**: *Take the pick* when the card has a pick, and *Open*; *Go on paid?* has *Open* only (§178.5). *Take the pick* sends the hand's own answer (the
   command the stack sends for a pick) from the background over the paired socket; when the computer cannot be reached the
   answer waits in the outbox (spec 94 §2.4) and the notification is replaced by *Sent when the computer answers*. *Open*
   opens the app on that card (the arrival).
5. The message stays under `web_push.MAX_MESSAGE`: `{title, body, tag, url, card: {id, goal, pick}}`.

## 6. Widgets (E; §174.7)
1. **Small**: the leader's head, the goal's short name and the alert sign; with nothing in the hand, *New goal*. A press opens
   the app on that card, or on the blank card.
2. **Medium**: the top card's context in two lines (§1.2.1–§1.2.2) and *Take the pick* · *Open* (iOS App Intents, Android
   Glance actions), sent as §5.4.
3. **Lock screen** (iOS's accessory, Android's lock-screen shortcut where there is one): *New goal*, opening the blank card
   with the microphone on.
4. **Their data** is the top card the app keeps (the app group, Android's preferences): written by the page through the frame
   on every snapshot (`setTopCard`) and by the extension on every push. When the top card changes or the hand empties while
   the device has no socket, the computer sends a **quiet push** (tag `top`, `Urgency: very-low`, no alert): the app updates
   the widgets and shows nothing. Never in the quiet hours; at most one every `PUSH_GAP_S`.
5. Drawn in orkUI's office (dark, monochrome, colour a signal; the head an accent; the pixel face for *New goal* only). Never a
   count.

## 7. Asked again later
- Where the relay runs, what it costs, who keeps its keys (the APNs key, FCM's service account).
- A Live Activity (and Android's ongoing notification) while Play runs: the party's leader's head and the task's short name.
- A notification's actions beyond the pick (each choice of the card, up to four, §153).
- The stores' listing and pictures on its side (§150.5).
