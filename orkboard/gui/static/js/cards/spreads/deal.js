// The deal (docs/mockups/spreads/, "deal"): the Orkmaster deals a goal onto the chairs of the parties of its route (orkUI's chairs, a party's leader
// on its chair, the goal's card on it); a party not dealt is an empty chair, *not dealt*. *Change the deal* lets a card be moved off a chair or onto
// an empty one (a chair pressed, or its number); *Deal it* sends the route as it stands (`ideas.route_set {idea, route}` when it changed, then
// `ideas.route_start {idea}`, as the hand's route card sends them). Release is no chair to move: its road is the goal's end, not a part of the route.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { command, toast } from "../../link.js";
import { Icon, ORKUI } from "../../orkui.js";
import { partiesAll } from "../../table/data.js";
import { HeadOf, whoOf } from "../../table/post.js";
import { nodeOf } from "../feed.js";
import { closeSpread } from "./open.js";
import { Key, SpCard, SpreadFrame, faceOf } from "./shell.js";

const CHAIRS = ["ork", "elf", "knight", "undead", "gnome", "goblin"];

/** The party slugs a goal's route deals to, in its order. */
export const routeOf = (n) => (n?.route || []).filter((r) => r.step === "party" && r.party).map((r) => r.party);

function Chair({ g, dealt, n, first, edit, onPress, k }) {
  const w = whoOf(g.slug), race = CHAIRS.includes(w.race) ? w.race : "ork", locked = g.party_craft === "release";
  const src = `${ORKUI}/chair/chair-leader-${race}`, words = dealt ? (first ? "writes its spec" : "does its part") : "not dealt";
  return html`<button type="button" class=${cls("sp-chair", { "is-empty": !dealt })} data-race=${w.race || "orkmaster"} data-dealt=${dealt ? "1" : "0"} disabled=${!edit || locked}
      aria-pressed=${edit && !locked ? String(dealt) : undefined} aria-label=${`${w.name}: ${words}${edit && !locked ? (dealt ? ". Press to take the card off this chair" : ". Press to deal it here") : ""}`} onClick=${onPress}>
    <img class="sp-chair__ch" src=${`${src}.png`} srcset=${`${src}@2x.png 2x`} alt="" />
    <span class="sp-chair__hd"><${HeadOf} w=${w} size="mid" /></span>
    ${dealt && html`<${SpCard} party=${g.slug} n=${faceOf(n)} name=${n?.short || n?.title} size="sm" tilt=${first ? -4 : k % 2 ? 3 : -2} />`}
    <b class="sp-chair__n">${w.name}</b><small>${words}</small>${edit && !locked && html`<span class="sp-chair__k"><${Key} k=${String(k + 1)} /></span>`}</button>`;
}

export function Deal({ slug }) {
  const n = nodeOf(slug), all = partiesAll(), was = routeOf(n), [dealt, setDealt] = useState(was), [edit, setEdit] = useState(false), title = n?.short || n?.title || slug;
  const toggle = (p) => setDealt((d) => (d.includes(p) ? d.filter((x) => x !== p) : [...d, p]));
  useEffect(() => {
    const key = (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const i = "123456789".indexOf(e.key), g = all[i];
      if (edit && g && g.party_craft !== "release") toggle(g.slug);
      else if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        const chairs = [...document.querySelectorAll(".sp-chair:not(:disabled)")], at = chairs.indexOf(document.activeElement);
        if (chairs.length) chairs[(at + (e.key === "ArrowRight" ? 1 : -1) + chairs.length) % chairs.length].focus();
      }
    };
    addEventListener("keydown", key);
    return () => removeEventListener("keydown", key);
  });
  const names = dealt.map((p) => whoOf(p).name), changed = dealt.join() !== was.join();
  const line = names.length ? `To ${names[0]} for its spec${names.length > 1 ? `, then ${names.slice(1).join(" and ")} for the work` : ""}` : "To nobody yet: deal it to a party";
  const deal = async () => {
    try {
      if (changed) await command("ideas.route_set", { idea: slug, route: dealt });
      await command("ideas.route_start", { idea: slug });
      toast(`Sent: ${title} is dealt`);
      closeSpread();
    } catch (e) { toast(e?.message || "The deal was not sent", "error"); }
  };
  return html`<${SpreadFrame} kind="deal" title=${`The Orkmaster deals ${title}`} line=${line}
      say=${edit ? "Press a chair to take the card off it, or to deal it there. Then deal it." : "Here is my deal. Move a card off a chair, or onto the empty one, before I start."}
      note=${edit ? html`<${Key} k="←" /><${Key} k="→" /> move between the chairs; a number deals to its party.` : "Change the deal to move a card between chairs."}
      acts=${html`<button type="button" class="ork-btn" data-act="change" aria-pressed=${String(edit)} onClick=${() => setEdit(!edit)}><${Icon} name="pencil" /><span>${edit ? "Stop changing" : "Change the deal"}</span></button>
        <button type="button" class="ork-btn primary" data-act="deal" disabled=${!dealt.length} onClick=${deal}><${Icon} name="play" /><span>Deal it</span></button>`}>
    <div class="sp-col sp-deal">
      <div class="sp-dealer"><${HeadOf} w=${whoOf("orkmaster")} size="big" /><${SpCard} party=${n?.goal} n=${faceOf(n)} name=${title} line="the goal" size="lg" /></div>
      <div class="sp-chairs">${all.map((g, k) => html`<${Chair} key=${g.slug} g=${g} n=${n} dealt=${dealt.includes(g.slug)} first=${dealt[0] === g.slug} edit=${edit} k=${k} onPress=${() => toggle(g.slug)} />`)}</div>
    </div>
  </${SpreadFrame}>`;
}
