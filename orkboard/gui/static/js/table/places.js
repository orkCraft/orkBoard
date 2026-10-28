// The places that were dialogs, drawn over the pane (docs/specs/98-the-table-and-the-hand.md §3.1, §3.6): *Settings*, *Open a project…*, New party, Edit the party and Remove party are today's forms (shell/settings.js,
// projects.js, goaldialog.js, goalwizard.js, partyremove.js) and they open and close themselves with `openDialog` and `closeDialog` (shell/modals.js). In the window as two parts a place lies in the pane, never in a
// dialog, so this file lays the two together without changing either:
//   · a form asked for as a dialog (Ctrl+O, the Edit form's *Remove party*) is opened over the pane instead (`openOver`), and the dialog signal holds a placeholder that `Dialogs` draws as nothing;
//   · a form that closes itself (`closeDialog`: Save, Cancel, Done, Esc in its own `Modal`) takes the pane back to its map; ← and Esc on the pane take the placeholder away.
// A form of any other kind (Pair a phone, a confirmation) stays a dialog until the window (spec 98 E) moves it too.
import { effect, untracked } from "@preact/signals";
import { dialog } from "../shell/modals.js";
import { closeOver, openOver, over } from "../frame/state.js";
import { isForm } from "./over.js";

export const HOLD = { kind: "pane", props: {} };           // `Dialogs` draws no dialog for it (no such kind)

const TO = {
  settings: () => ({ kind: "settings", props: {}, title: "Settings" }),
  "open-folder": () => ({ kind: "projects", props: { open: true }, title: "Open a project…" }),
  goal: (p) => ({ kind: "party", props: { slug: p.slug || "", then: p.then || "", preset: p.preset || "", proposal: p.proposal || "" }, title: p.slug ? "Edit the party" : "New party" }),
  "remove-party": (p) => ({ kind: "party", props: { slug: p.slug, remove: true }, title: "Remove party" }),
};

/** Starts the lay-together; `where()` says where a place came from ({title, key}). Returns the function that stops it. */
export function bindPlaces(where) {
  const asked = effect(() => {
    const d = dialog.value;
    if (!d || d === HOLD || !TO[d.kind]) return;
    const to = TO[d.kind](d.props || {});
    dialog.value = HOLD;
    untracked(() => openOver(to.kind, to.props, over.peek()?.from || where(), to.title));
  });
  const closed = effect(() => {
    if (dialog.value === null && untracked(() => isForm(over.value))) untracked(() => closeOver());
  });
  const held = effect(() => {
    const o = over.value;
    untracked(() => {
      if (isForm(o)) { if (dialog.value === null) dialog.value = HOLD; }
      else if (dialog.value === HOLD) dialog.value = null;
    });
  });
  return () => { asked(); closed(); held(); if (dialog.value === HOLD) dialog.value = null; };
}
