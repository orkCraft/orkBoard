// Pictures the person likes (docs/specs/50-parties-and-goals.md §3.7, docs/specs/85-the-elf-asks-and-shows.md §1): a few files, each shrunk to a JPEG of at most MAX_PX on its longer side and sent as a data
// URL (`photos` of `ideas.add` and of `ideas.answer`), for the leader or the elf to read. New goal's Refs and a look's question (*Pictures you like*) take them the same way.
import { useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { toast } from "../link.js";

export const MAX_PICTURES = 4;                     // realm/idea_photos.py MAX_PHOTOS
export const MAX_PX = 1600;                        // as the phone's (pwa/shell-idea-field.js): a JPEG of at most this, for the leader to read
export const PICTURE_TYPES = ["image/png", "image/jpeg", "image/webp", "image/gif"];

/** A picture the person likes, as `ideas.add`'s `photos` takes it: a JPEG of at most MAX_PX on its longer side, as a data URL. */
export async function shrink(file) {
  const url = await new Promise((ok, fail) => { const r = new FileReader(); r.onload = () => ok(r.result); r.onerror = fail; r.readAsDataURL(file); });
  const img = new Image();
  img.src = url;
  await img.decode();
  const k = Math.min(1, MAX_PX / Math.max(img.naturalWidth, img.naturalHeight));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(img.naturalWidth * k));
  canvas.height = Math.max(1, Math.round(img.naturalHeight * k));
  canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.85);
}

/** The pictures a form holds: `{list, add(files), drop(i)}`; a file that is not a picture is left, one that cannot be read is said. */
export function usePictures() {
  const [list, setList] = useState([]);
  const add = async (files) => {
    const got = [];
    for (const f of files.filter((x) => PICTURE_TYPES.includes(x.type)).slice(0, Math.max(0, MAX_PICTURES - list.length))) {
      try { got.push(await shrink(f)); } catch { toast("That picture could not be read: try another.", "warning"); }
    }
    if (got.length) setList((now) => [...now, ...got].slice(0, MAX_PICTURES));
  };
  return { list, add, drop: (i) => setList((now) => now.filter((_, k) => k !== i)) };
}

/** *Add a picture* and the small thumbnails with ×, for a question whose answer takes pictures. */
export function PictureAdd({ pictures, label = "Pictures you like" }) {
  const file = useRef();
  return html`<div class="arena-refs__pics" data-pictures>
    ${pictures.list.map((url, i) => html`<span key=${i} class="arena-refs__pic"><img src=${url} alt=${`Picture ${i + 1}`} />
      <button type="button" class="ork-btn" aria-label=${`Remove picture ${i + 1}`} onClick=${() => pictures.drop(i)}>×</button></span>`)}
    <button type="button" class="ork-btn" aria-label=${`Add a picture: ${label}`} disabled=${pictures.list.length >= MAX_PICTURES} onClick=${() => file.current?.click()}>Add a picture</button>
    <input ref=${file} type="file" accept=${PICTURE_TYPES.join(",")} multiple hidden onChange=${(e) => { pictures.add([...e.target.files]); e.target.value = ""; }} />
  </div>`;
}
