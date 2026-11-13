// Where the focus goes when an L or a spread is put away (goal 170): back to the card that opened it. The card may have been drawn
// again while the L lay over it (the Board changed, a lane was dealt anew): then the focus goes to the card that took its place
// (the same goal or the same words), else to the first card of the table, never to the page's body. Nothing imports here.
const CARDS = ".cards-lanes .cards-m, .cards-lanes .cards-s, .cards-dealer .cards-s, .frame-hand button.hand-card";

function standIn(was) {
  const goal = was.dataset?.goal || "", label = was.getAttribute?.("aria-label") || "", key = was.dataset?.key || "";
  const mine = [...document.querySelectorAll(CARDS)];
  return mine.find((el) => (key && el.dataset.key === key) || (goal && el.dataset.goal === goal && el.getAttribute("aria-label") === label))
    || mine.find((el) => label && el.getAttribute("aria-label") === label) || null;
}

/** Gives the focus back to `from` (an element, maybe gone from the page by now); the card in its place, else the first card. */
export function giveBack(from) {
  const go = (el) => { try { el.focus({ preventScroll: true }); } catch { /* not focusable */ } return document.activeElement === el; };
  if (!from) return;
  if (from.isConnected && go(from)) return;
  const find = () => (from.isConnected ? from : standIn(from));
  const settle = () => {                                     // nothing has the focus: the first card of the table
    const active = document.activeElement;
    if (active && active !== document.body) return;
    const first = document.querySelector(CARDS);
    if (first) go(first);
  };
  const el = find();
  if (el && go(el)) return;
  if (typeof requestAnimationFrame !== "function") { settle(); return; }
  let frames = 12;                                           // the hand is drawn anew when a mat is put away (its cards come back from a pile): the card may be a few frames late
  const later = () => requestAnimationFrame(() => {
    if (document.activeElement && document.activeElement !== document.body) return;      // something has the focus already
    const now = find();
    if (now && go(now)) return;
    if (frames-- > 0) later(); else settle();
  });
  later();
}

/** Keeps Tab inside a dialog (`root`, or the list of its parts: the mat and the hand that follows it): from its last act it goes to its first and back; a focus outside comes in. Call it from the dialog's keydown. */
export function keepTab(root, e) {
  const roots = [].concat(root).filter(Boolean);
  if (e.key !== "Tab" || !roots.length) return;
  const all = roots.flatMap((r) => [...r.querySelectorAll("button, [href], input, textarea, select, [tabindex]")]).filter((el) => !el.disabled && el.tabIndex >= 0 && el.offsetParent !== null);
  if (!all.length) return;
  const first = all[0], last = all[all.length - 1], on = document.activeElement;
  if (!roots.some((r) => r.contains(on))) { e.preventDefault(); first.focus(); }
  else if (roots.length > 1) {                                   // the mat and its hand are two parts of the page: the focus goes through them in the order given, never by the page's own
    const at = all.indexOf(on);
    e.preventDefault();
    (at < 0 ? first : all[(at + (e.shiftKey ? all.length - 1 : 1)) % all.length]).focus();
  }
  else if (e.shiftKey && on === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && on === last) { e.preventDefault(); first.focus(); }
}
