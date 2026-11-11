// What a part of the mock uses (js/mock/mocklink.js `PARTS`): a reply of the recording by name, a goal of the map by slug,
// and the mark an example carries in what a person reads, so an example is never taken for the project's own.
export const EXAMPLE = " · example";
export const reply = (data, name) => (data.replies || []).find((r) => r.name === name);
export const nodesOf = (data) => reply(data, "ideas.map")?.result?.nodes || [];
export const nodeOf = (data, slug) => nodesOf(data).find((n) => n.slug === slug) || null;
/** The latest goals of a state, newest first by their number. */
export const latest = (data, state, n = 1) => nodesOf(data).filter((x) => x.state === state).sort((a, b) => parseInt(b.slug) - parseInt(a.slug)).slice(0, n);
/** A recorded answer, or a new one added under `name` with no arguments. */
export function ensure(data, name, result) {
  const r = reply(data, name);
  if (r) return r.result;
  data.replies.push({ name, args: {}, ok: true, result });
  return result;
}
