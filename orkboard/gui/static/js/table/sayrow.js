// An idea through a leader (docs/specs/168 C4, decisions §283.16.4, §284.1): **one row of three groups**, the owner's pick over three rows (mockup docs/mockups/table-template/shots/5-idea-tech-groups.png): *Its verdict* (the leader's card, its
// sign by `Verdict`), *Needs your answer* (its risks, conflicts and questions) and *Could be better* (its improvements, each a line of the goal rewritten), three cards a group at most. A card open is pressed to be lifted and answered
// (sayask.js); once the Orkmaster has rewritten the goal's words the group says so beside an *Undo* (`ideas.undo_rewrite`), and an open fork (what was taken disagrees) lies first among the needs. The data is the map node's `say`
// (realm/idea_say.py `node`); a leader that has not said anything yet leaves the table to talkpage.js's `PartyTalk`. The words are the lexicon's `say_needs`, `say_better`, `say_verdict`, `say_undo`. Layout: say.css.
import { html } from "../html.js";
import { command } from "../link.js";
import { tab } from "../frame/state.js";
import { mapName, partiesAll } from "./data.js";
import { BetterCard, ForkCard, NeedCard, VerdictCard, fitted, MAX_CARDS } from "./saycards.js";
import { liftSay } from "./sayask.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./say.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** The leader of the party `slug` on the idea `n`'s say, null when it has not spoken. */
export const sayOf = (n, slug) => (n?.say?.leaders || []).find((l) => l.party === slug) || null;

function Group({ id, label, children, aside = null }) {
  return html`<section class="say-group" data-group=${id} aria-label=${label}><header class="say-group__hd"><span class="ork-label">${label}</span>${aside}</header><div class="say-group__cards">${children}</div></section>`;
}

/** The row of three groups of the idea `n` through the leader of the party `g`. */
export function SayRow({ n, g }) {
  const l = sayOf(n, g.slug), head = g.leader?.head || null, from = { title: mapName(tab.value, partiesAll()), key: "" };
  const fork = n.say?.fork || null, needs = fitted(l.needs), better = fitted(l.better), rewrite = n.say?.rewrite || null;
  const lift = (id) => () => liftSay(n, id, from);
  return html`<div class="say-row" data-view="say" data-goal=${n.slug} data-party=${g.slug}>
    <${Group} id="verdict" label="Its verdict"><${VerdictCard} n=${n} l=${l} head=${head} /><//>
    <${Group} id="needs" label="Needs your answer">
      ${fork && html`<${ForkCard} key=${fork.id} n=${n} fork=${fork} onPress=${lift(fork.id)} />`}
      ${needs.slice(0, MAX_CARDS - (fork ? 1 : 0)).map((x) => html`<${NeedCard} key=${x.id} n=${n} need=${x} head=${head} onPress=${lift(x.id)} />`)}
      ${!fork && !needs.length && html`<p class="say-group__none">Nothing</p>`}<//>
    <${Group} id="better" label="Could be better" aside=${rewrite && html`<span class="say-group__undo"><span class="cap">The goal's words were rewritten</span>
        ${rewrite.undoable && html`<button type="button" class="ork-btn quiet" data-act="undo-rewrite" onClick=${() => command("ideas.undo_rewrite", { idea: n.slug }).catch(() => {})}>Undo</button>`}</span>`}>
      ${better.map((x) => html`<${BetterCard} key=${x.id} n=${n} better=${x} head=${head} onPress=${lift(x.id)} />`)}
      ${!better.length && html`<p class="say-group__none">Nothing</p>`}<//>
  </div>`;
}
