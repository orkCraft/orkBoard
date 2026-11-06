// The drum's order (spec 156 E.4, decisions §261.13, §262.1): which potion stands in front and which stand beside it. Pure over the tools in the person's order (`tools.order`, as `potionsOf` gives them) and a function that says a tool's level.
// **The front** is the active tool: the picked goal's work tool while a goal at work is picked, else the open tab's tool (`framedOf`, decisions §177.1's rule with its frame gone). **The neighbours** are the front's two in the person's order (round the drum: the first
// tool's place before it is taken by the last, the last's after it by the first, so three stand in sight whenever there are three, decisions §265), **except that a tool at the warn or the danger level takes the nearer neighbour's place** (`.is-alert`: full brightness, its share in words under it), the nearest such tool on either side first, a second on the other side's
// place. The rest lie behind the neighbours, in the order they came in, unseen. Returns `{seq, front, alerts}`: the tools in the drum's places (`--ork-drum-at` is a tool's index in `seq`), the index in front, and the ids of the alert neighbours.
export const ALERT_LEVELS = ["warn", "danger"];

export function drumOf(limits, wanted, levelOf) {
  if (!limits.length) return { seq: [], front: 0, alerts: [] };
  const f = Math.max(0, limits.findIndex((l) => l.provider === wanted)), alert = (l) => ALERT_LEVELS.includes(levelOf(l));
  const near = limits.map((l, i) => ({ l, side: i < f ? -1 : 1, d: Math.abs(i - f) })).filter((x) => x.d > 0 && alert(x.l)).sort((a, b) => a.d - b.d).slice(0, 2);
  const take = { "-1": null, 1: null };
  if (near[0]) take[near[0].side] = near[0].l;
  if (near[1]) { const side = near[1].side === near[0].side ? -near[0].side : near[1].side; if (!take[side]) take[side] = near[1].l; }
  const used = new Set([take[-1], take[1]].filter(Boolean).map((l) => l.provider));
  const before = limits.slice(0, f).reverse().filter((l) => !used.has(l.provider)), after = limits.slice(f + 1).filter((l) => !used.has(l.provider));
  let left = take[-1] || before.shift() || null, right = take[1] || after.shift() || null;
  if (!left) left = after.pop() || null;                     // the first in front: the last stands before it (round the drum, §265)
  if (!right) right = before.pop() || null;                  // the last in front: the first stands after it
  const seq = [...before.reverse(), ...(left ? [left] : []), limits[f], ...(right ? [right] : []), ...after];
  return { seq, front: before.length + (left ? 1 : 0), alerts: [take[-1], take[1]].filter(Boolean).map((l) => l.provider) };
}
