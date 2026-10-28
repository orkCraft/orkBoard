// What can open over the pane (docs/specs/98-the-table-and-the-hand.md §0.2, §3.6, decisions §142) and who draws it: the table's
// part (js/table/) or the hand's (js/hand/). A face opens one with frame/state.js `openOver(kind, props, from)`; the pane draws
// the one open with the component registered for its kind. Written by the lead; a part registers its own kinds' components
// with `drawn(kind, Component)` from its own module, never by editing this file.
export const KINDS = {
  file: "table", diff: "table", log: "table", task: "table", role: "table", settings: "table", projects: "table",
  files: "table", party: "table", play: "table", limits: "table",
  deck: "hand", discard: "hand", result: "hand", stop: "hand",
};

const FACES = {};

/** `Component` draws `kind` over the pane: `({props, close}) => html`. */
export function drawn(kind, Component) {
  if (!(kind in KINDS)) throw new Error(`no such kind over the pane: ${kind}`);
  FACES[kind] = Component;
}

/** The component that draws `kind`, null when its part is not loaded. */
export const faceOf = (kind) => FACES[kind] || null;
