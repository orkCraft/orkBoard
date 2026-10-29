// The quick question (docs/specs/106-a-quick-question.md §3, decisions §181): one line at the top of the pane, *Ask the Orkmaster…* on the Orkmaster's tab, *Ask the <its leader's role>…* on a party's. Enter sends it
// (`ideas.ask {party, q}`, party "" on the Orkmaster's tab); while it is read the field is off and a line under it says who is reading. The answer lies under the line on the tab it was asked on only (`town.ask`, the host keeps
// one): the asker's small head, the question muted, the answer in the body face with its line breaks (plain text, never Markdown), up to four sources as small chips, and × (*Put away*, `ideas.ask_clear`). When the answer
// suggests a goal, *Make it a goal* opens the new goal's field with that line written (`ideas.ask_goal` says it was pressed; the field is the hand's, addressed to the open tab as it always is). A read, not a card: no phase, no count.
// Typing here never opens the new goal's field: the hand opens it on a key typed with nothing focused (hand/hand.js), and this field has the focus.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, Icon } from "../orkui.js";
import { command, town } from "../link.js";
import { ORKMASTER } from "../frame/state.js";
import { fieldText } from "../hand/state.js";
import { openField } from "../hand/pluscard.js";
import { groupsOf } from "./data.js";

const Q_CHARS = 500;                                                  // as realm/board_ask.py Q_CHARS
const CROWN = { race: "peon", tier: "crown" };                        // the Orkmaster's head, as the tabs and the notice draw it

/** Who answers on a tab: `{name, head}`, the Orkmaster, or the party's leader seat (*the leader* when it has none). `party` "" is the Orkmaster's. */
export function askerOf(party, parties) {
  if (!party) return { name: "Orkmaster", head: CROWN };
  const g = parties.find((x) => x.slug === party), seat = g ? groupsOf(g).find((x) => x.band === "lead")?.seats[0] : null;
  return { name: seat?.name || "leader", head: seat?.head || null };
}

/** The answer, or the failure, put under the line. */
function Answer({ ask, who }) {
  const away = () => { command("ideas.ask_clear", {}).catch(() => {}); };
  const goal = () => {
    command("ideas.ask_goal", {}).catch(() => {});
    fieldText.value = ask.goal;
    openField();
  };
  const x = html`<button type="button" class="ork-btn quiet table-ask__x" aria-label="Put away" title="Put away" onClick=${away}><${Icon} name="close" /></button>`;
  if (ask.status === "failed") {
    return html`<section class="table-ask__answer ork-panel is-failed" aria-label="The question failed">
      <p class="table-ask__err" role="alert">${ask.error || "No answer came: ask again"}</p>${x}</section>`;
  }
  const sources = Array.isArray(ask.sources) ? ask.sources : [];
  return html`<section class="table-ask__answer ork-panel" aria-label=${`The ${who.name}'s answer`} data-party=${ask.party}>
    <div class="table-ask__who">${who.head && html`<${Head} race=${who.head.race} tier=${who.head.tier} />`}<p class="table-ask__q">${ask.q}</p></div>
    <p class="table-ask__text">${ask.answer}</p>
    ${sources.length > 0 && html`<ul class="table-ask__srcs" aria-label="Where it is said">${sources.map((s) => html`<li key=${s} class="ork-chip table-ask__src">${s}</li>`)}</ul>`}
    ${ask.goal && html`<div class="table-ask__goal"><button type="button" class="ork-btn" title=${ask.goal} onClick=${goal}>Make it a goal</button></div>`}
    ${x}
  </section>`;
}

/** The line and, under it, the answer when it was asked on this tab. `tab`: the open tab (ORKMASTER or a party's slug); `parties`: the Board's. */
export function AskLine({ tab, parties }) {
  const [q, setQ] = useState(""), [sending, setSending] = useState(false);
  const ask = town.value?.ask || null, party = tab === ORKMASTER ? "" : tab, here = askerOf(party, parties);
  const reading = ask?.status === "asking", readBy = reading ? askerOf(ask.party || "", parties) : null;
  const words = `Ask the ${here.name}`;
  const send = async (e) => {
    e.preventDefault();
    const text = q.trim();
    if (!text || sending || reading) return;
    setSending(true);
    try { await command("ideas.ask", { party, q: text }); setQ(""); } catch { /* refused: the host's words are in a toast, the question stays */ }
    setSending(false);
  };
  const mine = ask && ask.status !== "asking" && (ask.party || "") === party;
  return html`<div class="table-ask" data-tab=${tab}>
    <form class="table-ask__form" onSubmit=${send}>
      <input type="text" class="ork-field table-ask__field" aria-label=${words} placeholder=${`${words}…`} maxlength=${Q_CHARS} autocomplete="off" enterkeyhint="send"
        value=${q} disabled=${reading} onInput=${(e) => setQ(e.currentTarget.value)} />
    </form>
    ${reading && html`<p class="table-ask__reading" role="status"><span class="ork-busy"></span>The ${readBy.name} is reading…</p>`}
    ${mine && html`<${Answer} ask=${ask} who=${here} />`}
  </div>`;
}
