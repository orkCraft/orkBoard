// What a goal picked reads on a leader's map (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md F.2–F.3): the data of the view in goalview.js, kept apart from its drawing. Pure functions over the goal's spec
// (`ideas.page` through specpage.js `readSpec`: the party's section, its *Done when* and its *Will be* lines `new|changed|gone <id>`), over the leader's map as the host reads it from dev (Tech's System, `ideas.system`: the parts by
// folder and what each uses; Design's screens, `ideas.screens`: the screens and their links), and over what a goal done changed against its spec (`ideas.goal_result`, realm/goal_result.py). A craft whose map the host does not read from
// the files (Product, Game design, Art …) has no map here: its parts are the *Will be* lines alone and nothing is read-only.
import { useEffect, useState } from "preact/hooks";
import { command } from "../link.js";
import { mapData } from "../shell/store.js";
import { leadsSystem } from "./data.js";
import { AGREED } from "./ask.js";
import { kindOf } from "./piles.js";

/** The goal's states a leader's tab can show *what it will change* for: agreed or at work (the bubble's *Make it a change* has the same: ask.js `AGREED`), and a goal at work that failed. */
export const WILL_STATES = [...AGREED, "failed"];
/** Whether a goal picked has a view of its own at a leader: what it will change (agreed, at work) or what it changed (done). */
export const viewable = (n) => !!n && (n.state === "done" || WILL_STATES.includes(n.state));
/** Whether the Play die wears the goal's rune: it is done, or at work. */
export const playable = (n) => !!n && (n.state === "done" || kindOf(n)?.pile === "work" || (n.tasks || []).some((t) => t.state === "running" || t.state === "testing"));

/** The picked goal's node on the snapshot, null for none. */
export const nodeOf = (slug) => (slug && (mapData.value?.nodes || []).find((n) => n.slug === slug)) || null;

const norm = (x) => String(x || "").toLowerCase().replace(/[^a-z0-9]/g, "");
const inside = (a, b) => { a = String(a).replace(/^\/+|\/+$/g, ""); b = String(b).replace(/^\/+|\/+$/g, ""); return !!a && !!b && a !== "." && b !== "." && (a === b || a.startsWith(`${b}/`) || b.startsWith(`${a}/`)); };

/** Whether a *Will be* id names the part `p` of the map `info` (Tech: the same folder or one inside the other; Design: the screen's id, name or path without case or signs). */
export function names(info, id, p) {
  if (!info || !p) return false;
  return info.kind === "parts" ? inside(id, p.id) : norm(id) !== "" && [p.id, p.name, p.path].some((x) => norm(x) === norm(id));
}

/** The part of the map a *Will be* id names, null for none. */
export const partFor = (info, id) => (info ? info.parts.find((p) => names(info, id, p)) || null : null);

/** The lines of a part, the way the leader wrote them: its note under a sign for its kind (+ new, ~ changed, − gone). */
export function linesOf(kind, note) {
  const sign = { new: "+", changed: "~", gone: "-" }[kind] || "·";
  return [`${sign} ${note || { new: "it is new", changed: "it changes", gone: "it goes" }[kind] || ""}`.trim()];
}

/** The parts a leader's section promises, as cards: `[{id, name, kind: new | changed | gone | read, lines}]`, then (when the map has them) the parts the promised ones use and no line names, read only, at most `READ_MAX`.
 *  `will`: the section's lines (specpage.js `willBe`), `info`: the map (`useMap`). */
export const READ_MAX = 4;
export function partsOf(will, info) {
  const said = (will || []).filter((w) => w.id && w.kind);
  const out = said.map((w) => ({ id: w.id, name: partFor(info, w.id)?.name || w.id.split("/").pop() || w.id, kind: w.kind, lines: linesOf(w.kind, w.note), note: w.note }));
  if (!info) return out;
  const read = [];
  for (const w of said.filter((x) => x.kind !== "gone")) {
    const p = partFor(info, w.id);
    for (const u of p?.uses || []) {
      const q = info.parts.find((x) => x.id === u);
      if (q && !said.some((s) => names(info, s.id, q)) && !read.some((r) => r.id === q.id) && read.length < READ_MAX) read.push({ id: q.id, name: q.name, kind: "read", lines: [`· ${p.name} uses it; nothing of it changes`], note: "" });
    }
  }
  return [...out, ...read];
}

/** The leader's map as the host reads it, for the party `g`: `{kind: "parts" | "screens", parts: [{id, name, path, uses: [ids], group}], groups: [{name, ids}]}`, null while it is read, for a craft with no map or when it cannot be read. */
export function useMap(g) {
  const kind = leadsSystem(g) ? "parts" : g?.party_craft === "design" ? "screens" : "", [info, setInfo] = useState(null), rev = mapData.value?.rev;
  useEffect(() => {
    if (!kind) { setInfo(null); return undefined; }
    let live = true;
    const take = (v) => { if (live) setInfo(v); };
    if (kind === "parts") {
      command("ideas.system", { party: g.slug }, true).then((r) => {
        if (!r || r.error || !Array.isArray(r.columns)) return take(null);
        const groups = r.columns.map((c) => ({ name: c.name, parts: [...c.parts, ...(c.stack || [])] }));
        take({ kind, parts: groups.flatMap((c) => c.parts.map((p) => ({ id: p.path, name: p.name, path: p.path, uses: p.uses || [], group: c.name }))), groups: groups.map((c) => ({ name: c.name, ids: c.parts.map((p) => p.path) })) });
      }).catch(() => take(null));
    } else {
      command("ideas.screens", {}, true).then((r) => {
        if (!r || r.error || !Array.isArray(r.screens)) return take(null);
        const out = (id) => (r.links || []).filter((l) => l.from === id || l.to === id).map((l) => (l.from === id ? l.to : l.from));
        const steps = (r.steps || []).map((ids, i) => ({ name: `Step ${i + 1}`, ids })), held = new Set(steps.flatMap((s) => s.ids)), rest = r.screens.filter((s) => !held.has(s.id)).map((s) => s.id);
        take({ kind, parts: r.screens.map((s) => ({ id: s.id, name: s.name, path: s.path, uses: out(s.id), group: "", picture: s.picture || null })), groups: [...steps, ...(rest.length ? [{ name: "More", ids: rest }] : [])] });
      }).catch(() => take(null));
    }
    return () => { live = false; };
  }, [kind, g?.slug, rev]);
  return info;
}

/** What a goal done changed against what its spec promised, read now and again when the Board changes; undefined while it is read, null when it cannot be. */
export function useResult(idea, on) {
  const [res, setRes] = useState(undefined), rev = mapData.value?.rev;
  useEffect(() => {
    if (!on) { setRes(undefined); return undefined; }
    let live = true;
    command("ideas.goal_result", { idea }, true).then((r) => { if (live) setRes(r && !r.error ? r : null); }).catch(() => { if (live) setRes((was) => was || null); });
    return () => { live = false; };
  }, [idea, on, rev]);
  return res;
}
