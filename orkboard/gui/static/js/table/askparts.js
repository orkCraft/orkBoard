// A hand to take the scheme's parts into the quick question (docs/specs/168 E1, decisions §283.16.2, §283.20): while the ? card's question is open on this leader's tab, a press on a part of its scheme (any element with `data-pick-id`, picking.js) does not lift it: it
// names the part in the question (ask.js `openAsk` with the part: the chip with × in the bubble, which the question is sent with). Nothing is dragged: the scheme has no drag of its own, so the press is the way in. While the new goal's field is picking, that is the press's own.
import { useEffect } from "preact/hooks";
import { askOpen, openAsk } from "./ask.js";
import { pickFor } from "./picking.js";

/** The element a press on `target` takes in: the part (`{id, name}`) of the scheme it lies on, or null. */
export function partOf(target) {
  const el = target instanceof Element ? target.closest("#table-pane .table-body [data-pick-id]") : null;
  return el ? { id: el.dataset.pickId, name: el.dataset.pickName || el.dataset.pickId } : null;
}

/** While the question of `party` is open, the pane's parts are taken into it by a press. */
export function useTakingParts(party) {
  useEffect(() => {
    const press = (e) => {
      if (askOpen.value !== party || pickFor.value || e.button) return;
      const part = partOf(e.target);
      if (!part) return;
      e.preventDefault();
      e.stopPropagation();
      openAsk(party, part);
    };
    document.addEventListener("click", press, true);
    return () => document.removeEventListener("click", press, true);
  }, [party]);
}
