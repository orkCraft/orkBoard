// A party's parts on the phone's feed (docs/specs/117-the-phone-a-menu-of-the-leaders.md §5.2, decisions §195.2; since goal 169 F, decisions §291.7, the feed narrowed to the party: hand/upfeed.js): its **Concerns**, what its leader says is wrong or at risk, the alert sign and the
// line, what it is on in the caption; none when it has none. (Its leader's long header, its squad and its tools were the party's own screen, which the narrowed feed replaced; its goals at work are the feed's sideways cards.) A leader's map is not drawn on a phone
// (decisions §195.5). Layout only (uplook.css).
import { useEffect } from "preact/hooks";
import { html } from "../html.js";
import { Sign } from "../orkui.js";
import { mapData } from "../shell/store.js";
import { recordOf, readConcerns } from "../table/concerns.js";

/** The open concerns of a party's record (those not made into a goal yet), the alerts first: `[{id, level, what, on}]`. */
export function concernsOf(party) {
  const list = (recordOf(party)?.concerns || []).filter((c) => !(c.idea || c.goal) && c.what);
  return [...list.filter((c) => c.level === "alert"), ...list.filter((c) => c.level !== "alert")];
}

/** The party's concerns, read now and again when the Board changes; nothing when it has none. */
export function Concerns({ slug }) {
  const rev = mapData.value?.rev;
  useEffect(() => { readConcerns(slug); }, [slug, rev]);
  const concerns = concernsOf(slug);
  if (!concerns.length) return null;
  return html`<section class="up-sec" aria-label="Concerns"><p class="up-lab">Concerns</p>
    <ul class="up-concerns">${concerns.map((c) => html`<li key=${c.id} class="up-concern" data-level=${c.level}>${c.level === "alert" ? html`<${Sign} name="alert" />` : html`<i class="cn-dot" aria-hidden="true"></i>`}
      <span><span class="up-concern__what">${c.what}</span>${c.on && html`<span class="up-concern__on">${c.on}</span>`}</span></li>`)}</ul></section>`;
}
