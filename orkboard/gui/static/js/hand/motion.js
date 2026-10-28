// How the hand's cards answer the hand (docs/specs/98-the-table-and-the-hand.md §6.1, decisions §149.1): orkUI draws every motion (`.ork-leans`, `.ork-deal`,
// `.ork-fan`, `.ork-crumble`: its tokens, its keyframes, nothing under reduced motion); the page only says when. A card leans toward the pointer (`lean`), a card that
// comes is dealt (`useDealt`), a card that goes crumbles where it lay (`useGone`), a fan opens and closes with the spring (`useFan`). At rest and under reduced motion
// nothing moves: the hooks add no class then.
import { h } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";

export const reduced = () => typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

export const DEAL_MS = 650, CRUMBLE_MS = 700, FAN_MS = 400;     // a dealt card's travel, the shards' fall (orkUI's play time and the six shards' gaps), a fan's closing

/** The pointer's place on a card, -1 to 1 each way, for orkUI's lean (`--ork-lean-x`, `--ork-lean-y`); set on the card itself. */
export function lean(e) {
  const el = e.currentTarget, r = el.getBoundingClientRect();
  if (!r.width || !r.height) return;
  el.style.setProperty("--ork-lean-x", String(Math.max(-1, Math.min(1, ((e.clientX - r.left) / r.width) * 2 - 1)).toFixed(2)));
  el.style.setProperty("--ork-lean-y", String(Math.max(-1, Math.min(1, ((e.clientY - r.top) / r.height) * 2 - 1)).toFixed(2)));
}
export function level(e) {
  e.currentTarget.style.removeProperty("--ork-lean-x");
  e.currentTarget.style.removeProperty("--ork-lean-y");
}
/** The handlers that give a card its lean. */
export const leans = { onPointerMove: lean, onPointerLeave: level };

/** The keys that came since the last draw (not the first draw, not under reduced motion): they are dealt, one after another, for DEAL_MS. `{key: i}`. Read while drawing, so that
 *  a card is dealt in the very frame it is first drawn. */
export function useDealt(keys) {
  const seen = useRef(null), live = useRef({}), [, tick] = useState(0), now = new Set(keys);
  if (seen.current === null || reduced()) seen.current = now;
  else {
    const came = keys.filter((k) => !seen.current.has(k));
    seen.current = now;
    if (came.length) {
      came.forEach((k, i) => { live.current[k] = i; });
      setTimeout(() => { for (const k of came) delete live.current[k]; tick((n) => n + 1); }, DEAL_MS + came.length * 40);
    }
  }
  return { ...live.current };                                                 // a new object each draw: a component that reads signals skips a draw whose props are the same
}

/** `items` with the ones that left kept where they lay for the crumble: `[{item, gone}]`. A card that goes under reduced motion goes at once. */
export function useGone(items, key) {
  const was = useRef(null), [ghosts, setGhosts] = useState([]), id = items.map(key).join("|");
  useEffect(() => {
    const prev = was.current;
    was.current = items.map((item, at) => ({ item, at }));
    if (!prev || reduced()) return undefined;
    const now = new Set(items.map(key)), left = prev.filter(({ item }) => !now.has(key(item)));
    if (!left.length) return undefined;
    setGhosts((g) => [...g, ...left.map(({ item, at }) => ({ item, at, gone: true }))]);
    const t = setTimeout(() => setGhosts((g) => g.filter((x) => !left.some((l) => key(l.item) === key(x.item)))), CRUMBLE_MS);
    return () => clearTimeout(t);
  }, [id]);
  const out = items.map((item) => ({ item, gone: false }));
  for (const g of ghosts) out.splice(Math.min(g.at, out.length), 0, g);
  return out;
}

/** The six shards of a card that goes (orkUI's `.ork-crumble`). */
export const Shards = () => {
  const n = 6;
  return h("span", { class: "ork-crumble", "aria-hidden": "true" }, Array.from({ length: n }, (_, i) => h("i", { key: i })));
};

/** A fan that opens and closes with the spring: `{shown, closing}`. It stays drawn for the closing, and not at all under reduced motion. */
export function useFan(open) {
  const [shown, setShown] = useState(open), [closing, setClosing] = useState(false);
  useEffect(() => {
    if (open) { setShown(true); setClosing(false); return undefined; }
    if (!shown) return undefined;
    if (reduced()) { setShown(false); return undefined; }
    setClosing(true);
    const t = setTimeout(() => { setShown(false); setClosing(false); }, FAN_MS);
    return () => clearTimeout(t);
  }, [open]);
  return { shown: open || shown, closing: !open && closing };
}
