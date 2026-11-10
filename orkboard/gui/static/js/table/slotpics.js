// The pictures of the inventory's ways (docs/specs/168 H1, J2; decisions §283.34, §289): orkUI's `pictures/pictures.json` says which file draws a way of a slot (`slots`: `{"<slot>.<way id>": "<path under pictures/>"}`; a key
// without the slot, `"<way id>"`, serves every slot that has the way, and `/` stands for `.`). orkUI has no `pictures/` yet (the owner's are being redrawn, §289), so the file is not there and a slot's card draws its kind's sign
// (stallfaces.js `Mark`) where it has no picture: J2 only adds the files and the list. The list is read once, when the first slot asks; a missing or a broken one is an empty list.
import { signal } from "@preact/signals";
import { ORKUI } from "../orkui.js";

/** The list as read: null before the first read ends, then `{}` or the file's own. */
export const pictures = signal(null);
let reading = false;

/** Reads `pictures/pictures.json` once. */
export function readPictures() {
  if (reading || typeof fetch !== "function") return;
  reading = true;
  const FILE = "pictures/pictures.json";      // asked for only when orkUI's stamp names it: a copy without it makes no failed request
  fetch(`${ORKUI}/ORKUI.json`).then((r) => (r.ok ? r.json() : {})).then((stamp) => (stamp?.files && FILE in stamp.files ? fetch(`${ORKUI}/${FILE}`).then((r) => (r.ok ? r.json() : {})) : {})).catch(() => ({})).then((j) => { pictures.value = j && typeof j === "object" && !Array.isArray(j) ? j : {}; });
}

/** The address of the picture of way `id` of `slot`, or "" where orkUI has none. */
export function pictureOf(slot, id) {
  const list = pictures.value?.slots;
  if (!list || typeof list !== "object") return "";
  const file = [`${slot}.${id}`, `${slot}/${id}`, String(id)].map((k) => list[k]).find((f) => typeof f === "string" && f && !f.includes(".."));
  return file ? `${ORKUI}/pictures/${file.replace(/^\/+/, "")}` : "";
}
