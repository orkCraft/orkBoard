// orkUI's pixel symbols on the phone (docs/specs/50-parties-and-goals.md §1, §1.6): a goal's element (`.ork-elem`: meadow, ice, dust, void, lava) and the eight signs (`.ork-sign`:
// check, cross, work, night, alert, flag, before, after), drawn as masks of orkUI's own files (elements/, signs/, served beside the sheets: gui/pwa.py). No Unicode symbol stands in for
// one. A sign is `aria-hidden`: its words are its title or the text beside it. An element is shown, never named.
import { h } from "./util.js";

export const ELEMENTS = ["meadow", "ice", "dust", "void", "lava"];

/** A goal's rune as a node (null when the goal has none yet): its shape `name` in its colour `hue` (spec 128 G; one of ELEMENTS, else the shape's own; page.css `.ork-elem.k-<hue>`); `dim`: it is not read yet, drawn in the faint ink; `big`: 28 px (else 14). */
export function elem(name, { dim = false, big = false, hue = "" } = {}) {
  const colour = ELEMENTS.includes(hue) && hue !== name ? ` k-${hue}` : "";
  return ELEMENTS.includes(name) ? h("span", { class: `ork-elem ${name}${colour}${big ? " big" : ""}${dim ? " dim" : ""}`, "aria-hidden": "true" }) : null;
}

/** A goal's moon (spec 74 §6) as a node, 14 px (`big`: 28 px): `phase` is new, crescent, half, gibbous or full; null (no node) for a goal that has none. Shown, never named: `aria-hidden`. */
export function moon(phase, { big = false } = {}) {
  return phase ? h("span", { class: `ork-moon ${phase}${big ? " big" : ""}`, "aria-hidden": "true" }) : null;
}

/** The class of a type's sign, its goal's colour (spec 55 §1.2): the element's, `dim` (faint) while the element is drawn dim, `none` (muted) for a goal with no element. */
export const typeTone = (element, dim = false) => (!ELEMENTS.includes(element) ? "none" : dim ? "dim" : element);

/** A sign by its name, 14 px (`big`: 28 px), its words (when it has none beside it) in its title. */
export function sign(name, title = "", { big = false } = {}) {
  return h("span", { class: `ork-sign ${name}${big ? " big" : ""}`, "aria-hidden": "true", title: title || null });
}

// What the host writes where a sign goes (a Today row's mark): the glyph and its sign.
const GLYPHS = { "✓": "check", "✗": "cross", "↻": "work", "☾": "night", "!": "alert", "⚑": "flag", "←": "before", "→": "after" };

/** The sign a glyph of the host stands for (its words in `title`), else the glyph itself as text. */
export function glyph(g, title = "") {
  return GLYPHS[g] ? sign(GLYPHS[g], title) : g;
}

/** The next goal's shape from the complete project's snapshot goal-node collection across every party.
 * Matches the host's `idea_element.holds` and `pick`: valid shapes hold unless done with a seen result;
 * snapshot `seen` represents persisted `seen_at`. Dropped goals and legacy goals without hue still count.
 * Ties follow ELEMENTS order. Returns only a shape; hue prediction belongs to the host. */
export function nextElement(nodes) {
  const used = (nodes || []).filter((n) => ELEMENTS.includes(n.element) && (n.state !== "done" || !n.seen)).map((n) => n.element);
  return ELEMENTS.reduce((best, e) => (used.filter((u) => u === e).length < used.filter((u) => u === best).length ? e : best), ELEMENTS[0]);
}
