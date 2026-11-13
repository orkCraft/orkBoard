// The small face-up card (docs/specs/168-the-window-played-as-a-card-games-table.md A2, decisions §283.3, §284.2; mockup docs/mockups/table-template/): 56 x 78, an index with no words. Top left the goal's rune (its shape in its element's colour,
// decisions §206.10), bottom left a dot for each party of its route in that party's colour (filled when that party is done, hollow while it lies ahead), in its middle a small picture: the goal's first attached picture (`n.picture`, a URL the host
// serves: realm/idea_photos.py) or the picture the caller gives, else its kind's sign, big. A signal (`alert`: it waits for the person; `danger`: it failed) is the card's own frame (decisions §268.1, §276). Its words are its label.
// Hovered or focused it is shown at 144 x 202 beside it (preview.js). Later stages (a leader's table, a party's lane) lay it with these props; this file knows no pile and holds no state.
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { raceOf } from "./felt.js";
import { withPreview } from "./preview.js";

/** The dots of a route: `parties` are the party objects (`{slug, leader}`) or their slugs, `done` the slugs (or parties) that are done; one `{slug, race, done}` each, in the route's order. */
export function dotsOf(parties = [], done = []) {
  const over = new Set((done || []).map((d) => (typeof d === "string" ? d : d?.slug)));
  return (parties || []).map((p) => {
    const g = typeof p === "string" ? { slug: p } : p || {};
    return { slug: g.slug || "", race: raceOf(g), done: over.has(g.slug) };
  });
}

/** The small card of goal `n`. `parties`/`done`: its route and the parties done; `signal`: "alert", "danger" or ""; `picture`: an element (vnode) for its middle in place of the goal's own picture or its kind's sign; `onPress`: with it the card is a button, else a
 *  focusable box; `preview`: false puts the preview off; `extra`: more attributes (a data id, a class); `time`, `much`: the card's time in words and its spend, shown in its preview only (the small card has no room for them: decisions §283.17). */
export function SmallCard({ n, parties = [], done = [], signal = "", picture = null, onPress = null, preview = true, extra = {}, time = "", much = "" }) {
  const el = n.element || "", hue = n.hue || el, name = n.title || n.short || "", dots = dotsOf(parties, done), url = typeof n.picture === "string" ? n.picture.trim() : "", kind = n.type?.sign || "";
  const face = html`
    <span class="sm-tl" aria-hidden="true"><${Elem} name=${el} hue=${hue} dim=${!el} /></span>
    <span class="sm-pic" aria-hidden="true">${picture ? picture : url ? html`<img class="sm-pic__img" src=${url} alt="" loading="lazy" decoding="async" draggable="false" />` : kind && html`<${Sign} name=${kind} big=${true} />`}</span>
    <span class="sm-dots" aria-hidden="true">${dots.map((d, i) => html`<i key=${d.slug || i} class=${cls("sm-dot", { "is-done": d.done })} data-race=${d.race || undefined} data-party=${d.slug}></i>`)}</span>`;
  const { class: more, ...rest } = extra;
  const props = { ...rest, class: cls("ork-card sm", { [`el-${hue}`]: !!hue, [`is-${signal}`]: !!signal, [more || ""]: !!more }), "data-goal": n.slug, "data-signal": signal || undefined, "aria-label": name };
  const on = preview ? withPreview(props, () => ({ mode: "face", name, element: el, hue, kind, signal, picture: url, node: picture, time, much })) : props;
  return onPress ? html`<button type="button" ...${on} onClick=${onPress}>${face}</button>` : html`<span tabindex="0" role="group" ...${on}>${face}</span>`;
}
