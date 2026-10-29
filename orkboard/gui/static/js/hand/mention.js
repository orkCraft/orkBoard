// @ in New goal's field (docs/specs/107-what-the-owners-day-said.md §11, decisions §182.13): typed at a word's start, `@` opens a list: who (a party, as `@Party` already addresses it: state.js `addressOf`),
// then what on (a file or a folder of the project: `files.find`); once a party is taken (`@Game design `) the list goes on with that party's second step, filtered by what is typed after it — what it can do (its goal
// types, `mapData` goals[].types: taking one makes the goal that type, a chip on the field and `type` sent with `ideas.add`, never a word in the text) and what it already has (the parts of its map, `ideas.pickables`: the
// same `{map, id, name}` picking takes, so a part taken is one more mark of picking.js, a chip as a picked card's). At the first `@` a word that names no party but a type (`@mech`) offers *New mechanic · Game design*:
// taking it takes both. ↑ ↓ move, Enter or Tab take, Esc closes the list and leaves the field, at most eight rows; while the list is open Enter takes and does not send, and with nothing to take it sends as always. The
// list lies over the field's top edge, not under the caret: the field lies at the window's foot, where nothing opens downward. A file taken is written `@path/to/file `; the host turns it into `path` (realm/goal_mentions.py).
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, Icon, Sign } from "../orkui.js";
import { command } from "../link.js";
import { marks } from "../table/picking.js";
import { fieldText, fieldType } from "./state.js";

if (typeof document !== "undefined") {
  const href = new URL("./mention.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const ROWS = 8;                               // the list's rows at most
const REST_MAX = 24;                                 // what is typed after a party stays a filter this long; longer is the goal's words
const TYPES_SHOWN = 5;                               // of the second step's rows, at most this many are types (the parts have room too)

/** The `@` being typed at `caret`: null, or `{at, stage: 1, q}` (who or what on: `q` is what follows the `@`) or `{at, stage: 2, party, q}` (the party taken, `q` what follows it). `parties`: [{slug, name, ...}]. */
export function mentionAt(text, caret, parties) {
  const before = String(text || "").slice(0, caret), at = before.lastIndexOf("@");
  if (at < 0 || (at > 0 && !/\s/.test(before[at - 1]))) return null;                 // an `@` in a word (an address, a path) is not a mention
  const q = before.slice(at + 1), low = q.toLowerCase();
  if (q.includes("\n")) return null;
  const party = [...parties].sort((a, b) => b.name.length - a.name.length).find((p) => low.startsWith(`${p.name.toLowerCase()} `));
  if (party) { const rest = q.slice(party.name.length + 1); return rest.length > REST_MAX ? null : { at, stage: 2, party, q: rest }; }
  if (/\s/.test(q) && !parties.some((p) => p.name.toLowerCase().startsWith(low))) return null;      // a party's name may hold a space (*Game design*), a file's does not
  return { at, stage: 1, q };
}

const words = (s) => String(s || "").toLowerCase().split(/\s+/).filter(Boolean);
/** A type or a part matches what was typed after its party: the start of its name or of one of its words. */
const matches = (name, q) => { const w = q.toLowerCase().trim(); return !w || String(name).toLowerCase().startsWith(w) || words(name).some((x) => x.startsWith(w)); };

/** The rows of a mention: parties (and types by name) and files at the first step; types and parts at the second. `files`, `parts`: what the host answered. Each `{key, kind, ...}`. */
export function rowsOf(ctx, parties, files, parts, taken) {
  if (!ctx) return [];
  const q = ctx.q.toLowerCase();
  if (ctx.stage === 1) {
    const who = parties.filter((p) => p.name.toLowerCase().startsWith(q)).map((p) => ({ key: `p:${p.slug}`, kind: "party", party: p, name: p.name }));
    const by = q.length >= 2 && !/\s/.test(q) ? parties.flatMap((p) => p.types.filter((t) => matches(t.name, q)).map((t) => ({ key: `pt:${p.slug}:${t.id}`, kind: "ptype", party: p, type: t, name: t.name }))) : [];
    const on = /\s/.test(q) ? [] : files.map((f) => ({ key: `f:${f.path}`, kind: f.dir ? "folder" : "file", path: f.path, name: f.path }));
    return [...who, ...by, ...on].slice(0, ROWS);
  }
  const types = ctx.party.types.filter((t) => matches(t.name, ctx.q) && taken.type !== t.id).map((t) => ({ key: `t:${t.id}`, kind: "type", type: t, name: t.name }));
  const have = parts.filter((p) => matches(p.label || p.name, ctx.q) && !taken.marks.some((m) => m.map === p.map && m.id === p.id)).map((p) => ({ key: `m:${p.map}:${p.id}`, kind: "part", part: p, name: p.label || p.name }));
  const t = types.slice(0, Math.max(TYPES_SHOWN, ROWS - have.length));
  return [...t, ...have].slice(0, ROWS);
}

/** The hook of the field: the mention at the caret, its rows, and the keys. `area`: the textarea's ref; `parties`: [{slug, name, head, types}]. Returns `{rows, active, take, onKey, look, shut}`. */
export function useMention(area, parties) {
  const [ctx, setCtx] = useState(null), [files, setFiles] = useState([]), [parts, setParts] = useState({ slug: "", list: [] }), [active, setActive] = useState(0), [shut, setShut] = useState(-1);
  const look = () => {                                                              // where the caret is now (typed, moved by a key or a press)
    const el = area.current;
    const next = el ? mentionAt(el.value, el.selectionStart ?? el.value.length, parties) : null;
    if (!next) setShut(-1);
    setCtx((was) => (was && next && was.at === next.at && was.stage === next.stage && was.q === next.q && was.party?.slug === next.party?.slug ? was : next));
  };
  const hidden = !!ctx && ctx.at === shut;
  const first = ctx?.stage === 1 && !/\s/.test(ctx.q) ? ctx.q : null, slug = ctx?.stage === 2 ? ctx.party.slug : "";
  useEffect(() => {                                                                 // the project's files matching what follows the `@`, after a short pause in typing
    setFiles([]);                                                                   // what answered for the last letters is not offered for these
    if (first === null || hidden) return undefined;
    let live = true;
    const t = setTimeout(() => { command("files.find", { q: first, limit: 20 }, true).then((r) => { if (live) setFiles(r?.entries || []); }).catch(() => {}); }, 120);
    return () => { live = false; clearTimeout(t); };
  }, [first, hidden]);
  useEffect(() => {                                                                 // the party's map parts, once for the party taken
    if (!slug || hidden) return undefined;
    let live = true;
    command("ideas.pickables", { party: slug }, true).then((r) => { if (live) setParts({ slug, list: r?.parts || [] }); }).catch(() => {});
    return () => { live = false; };
  }, [slug, hidden]);
  const rows = hidden ? [] : rowsOf(ctx, parties, files, parts.slug === slug ? parts.list : [], { type: fieldType.value?.id || "", marks: marks.value });
  const sig = rows.map((r) => r.key).join("|");
  useEffect(() => { setActive(0); }, [sig]);
  /** Writes `text` into the field with the caret at `caret`. */
  const put = (text, caret) => {
    const el = area.current;
    if (el) { el.value = text; el.setSelectionRange(caret, caret); }
    fieldText.value = text;
    look();
  };
  const take = (row) => {
    const el = area.current;
    if (!el || !row || !ctx) return;
    const text = el.value, caret = el.selectionStart ?? text.length, after = text.slice(caret);
    const typeOf = (party, t) => { fieldType.value = { id: t.id, name: t.name, sign: t.sign, party: party.slug }; };
    if (row.kind === "party") { const w = `@${row.party.name} `; put(text.slice(0, ctx.at) + w + after, ctx.at + w.length); return; }
    if (row.kind === "ptype") { const w = `@${row.party.name} `; typeOf(row.party, row.type); put(text.slice(0, ctx.at) + w + after, ctx.at + w.length); return; }
    if (row.kind === "file" || row.kind === "folder") { const w = `@${row.path} `; put(text.slice(0, ctx.at) + w + after, ctx.at + w.length); return; }
    const keep = ctx.at + 1 + ctx.party.name.length + 1;                            // the party's step: what was typed after `@Party ` was the filter, not the goal's words
    if (row.kind === "type") typeOf(ctx.party, row.type);
    else marks.value = [...marks.value, { map: row.part.map, id: row.part.id, name: row.part.name, ...(row.part.group ? { group: row.part.group } : {}) }];
    put(text.slice(0, keep) + after, keep);
  };
  /** The field's key, before its own: true when the list used it. */
  const onKey = (e) => {
    if (!rows.length) return false;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); setActive((i) => (i + (e.key === "ArrowDown" ? 1 : rows.length - 1)) % rows.length); return true; }
    if ((e.key === "Enter" && !e.shiftKey && !e.isComposing) || e.key === "Tab") { e.preventDefault(); take(rows[Math.min(active, rows.length - 1)]); return true; }
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); setShut(ctx.at); return true; }
    return false;
  };
  return { rows, active, take, onKey, look, setActive };
}

/** The list over the field's top edge. */
export function MentionList({ rows, active, take, setActive }) {
  if (!rows.length) return null;
  return html`<ul class="hand-mention" role="listbox" aria-label="Mention a party, a file or a folder">
    ${rows.map((r, i) => html`<li key=${r.key} role="option" aria-selected=${String(i === active)} class=${cls("hand-mention__row", { "is-on": i === active })} data-kind=${r.kind}
      onMouseDown=${(e) => e.preventDefault()} onMouseMove=${() => i !== active && setActive(i)} onClick=${() => take(r)}>
      ${r.kind === "party" && r.party.head ? html`<${Head} race=${r.party.head.race} tier=${r.party.head.tier} />` : null}
      ${(r.kind === "type" || r.kind === "ptype") && html`<${Sign} name=${r.type.sign} />`}
      ${r.kind === "part" && html`<${Icon} name="map" />`}
      ${r.kind === "file" && html`<${Icon} name="file" />`}
      ${r.kind === "folder" && html`<${Icon} name="folder" />`}
      <span class=${cls("hand-mention__name", { "is-code": r.kind === "file" || r.kind === "folder" || (r.kind === "part" && r.part.map === "system") })}>${r.kind === "party" ? `@${r.name}` : r.name}</span>
      ${r.kind === "ptype" && html`<span class="hand-mention__note">${r.party.name}</span>`}
      ${r.kind === "part" && r.part.label !== r.part.name && html`<span class="hand-mention__note">${r.part.name}</span>`}
    </li>`)}
  </ul>`;
}
