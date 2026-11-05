// Whether the keyboard is up on the phone (docs/specs/147-one-card-four-corners.md part F.3, decisions §251.6): the visual viewport is clearly shorter than the window (`visualViewport.height` against `window.innerHeight`: the keyboard takes the difference; a pinch zoom, which
// shortens it too, is not a keyboard). `keyboardAt()` is pure over the browser's numbers: 0 with no keyboard, else the px of the layout viewport the screen leaves above the keyboard (its top edge from the page's top). `useKeyboard()` follows it, so a card can give up 5 : 7 for the field
// (stopcard.js `Lifted`, upright.css) and take it back when the keyboard goes. (The field a + card opens keeps its own: updeck.js.)
import { useEffect, useState } from "preact/hooks";

export const KEYBOARD_MIN = 120;                // px the visual viewport must be shorter than the window by: a browser's bar growing or shrinking is a few dozen, a keyboard 250 and more

/** The px above the keyboard (`offsetTop + height` of the visual viewport) while it is up, else 0. */
export function keyboardAt(vv = window.visualViewport, inner = window.innerHeight) {
  if (!vv || !(Number(vv.height) > 0)) return 0;
  if ((vv.scale || 1) > 1.05) return 0;                                  // zoomed in: the viewport is smaller by the zoom, not by a keyboard
  return inner - vv.height >= KEYBOARD_MIN ? Math.round((vv.offsetTop || 0) + vv.height) : 0;
}

/** The px above the keyboard while it is up, else 0 (`keyboardAt`), kept as the visual viewport and the window change. */
export function useKeyboard() {
  const [at, setAt] = useState(() => keyboardAt());
  useEffect(() => {
    const vv = window.visualViewport, set = () => setAt(keyboardAt());
    set();
    vv?.addEventListener("resize", set);
    vv?.addEventListener("scroll", set);
    window.addEventListener("resize", set);
    return () => { vv?.removeEventListener("resize", set); vv?.removeEventListener("scroll", set); window.removeEventListener("resize", set); };
  }, []);
  return at;
}
