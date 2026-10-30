// Talk on the pane (docs/specs/100-a-goals-way-as-cards.md §2.1–§2.2; docs/specs/99-a-goals-way.md §5.3; decisions §142.5, §153.6): the stances of the leaders on a goal's route, in a row, each its head and its party's name, its stance line,
// *For* and *Against* a line each, and *More*, which unfolds the Talk as the host kept it (`ideas.talk_read`: that leader's questions, each waiting, answered by the person or left to its pick) in place; and, on request (*All the questions*, or opened so by a lifted question: `props.together`), the questions together as a form, each its
// choices with the leader's pick on, an *Other…* line, and one button that sends them all (`ideas.talk_answer`, hand/questions.js). Props: `{idea, together?}`. Registered as the pane's kind `talk` (frame/kinds.js).
// Over the pane, never a dialog. While the goal's `talk` row waits on the Board the page follows it (its questions can be answered together); once the Talk is answered, or the goal is past it, the page is the Talk as kept
// (`ideas.talk_read`), opened from the pane's title (*Talk*, table/pane.js).
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { command } from "../link.js";
import { Elem, Head } from "../orkui.js";
import { drawn } from "../frame/kinds.js";
import { cardSig, given, give, scopeOf, sendRow } from "../hand/questions.js";
import { named } from "../hand/todoform.js";
import { nameOf, partiesAll } from "./data.js";

/** The Talk as the host kept it (`ideas.talk_read {idea}`): `{stances: [{party, leader, stance, for, against, questions}], cause}`; undefined while it is asked, null when the host has none. Asked again when the row's questions change. */
function useKept(idea, sig) {
  const [kept, setKept] = useState(undefined);
  useEffect(() => {
    let live = true;
    command("ideas.talk_read", { idea }, true).then((a) => { if (live) setKept(a && Array.isArray(a.stances) ? a : null); }).catch(() => { if (live) setKept(null); });
    return () => { live = false; };
  }, [idea, sig]);
  return kept;
}

/** How a question stands, in words: *Waits for you*, *You said: …*, *Its pick stands: …*. */
const standing = (q) => (q.state === "answered" ? `${q.how === "text" ? "You wrote" : q.how === "decide" ? "Left to its pick" : "You said"}: ${q.answer}` : q.state === "closed" ? `Its pick stands: ${q.answer}` : "Waits for you");

/** One leader's stance: its head and its party's name, the line, *For* and *Against*; *More* the Talk as kept, in place: its questions, how each stands. */
function Stance({ st, g, asked }) {
  const [more, setMore] = useState(false);
  return html`<li class="talk-stance" data-party=${st.party}>
    <div class="talk-stance__who">${g?.leader?.head && html`<${Head} race=${g.leader.head.race} tier=${g.leader.head.tier} size="mid" />`}<span class="talk-stance__nm">${nameOf(g) || st.party}</span></div>
    ${st.stance && html`<p class="body talk-stance__line">${st.stance}</p>`}
    ${st.for && html`<p class="talk-stance__side"><span class="ork-label">For</span> ${st.for}</p>`}
    ${st.against && html`<p class="talk-stance__side"><span class="ork-label">Against</span> ${st.against}</p>`}
    ${asked.length > 0 && html`<button type="button" class="ork-btn quiet talk-stance__more" aria-expanded=${String(more)} onClick=${() => setMore(!more)}>${more ? "Less" : "More"}</button>`}
    ${more && html`<ul class="talk-stance__asks" aria-label="Its questions">${asked.map((c) => html`<li key=${c.id + c.q} data-state=${c.state || "waiting"}><span class="body">${c.q}</span>
      <span class="cap">${c.choices.map((x, i) => (i === c.pick ? `● ${x}` : x)).join(" · ")}${c.why ? ` — ${c.why}` : ""}</span>
      ${c.state && html`<span class="cap talk-stance__ans">${standing(c)}</span>`}</li>`)}</ul>`}
  </li>`;
}

/** The questions together: each its choices (the pick on) and a line of one's own; one button sends them all. */
function Together({ row, g, close }) {
  const scope = scopeOf(row), cards = row.questions.filter((c) => !given.value[cardSig(scope, c)]);
  const [said, setSaid] = useState({}), lead = g?.leader?.name;
  const of = (c) => said[c.id] || { pick: c.pick };
  const set = (c, v) => setSaid({ ...said, [c.id]: v });
  const send = (decide) => {
    for (const c of cards) give(scope, c, of(c));
    sendRow(row, lead, decide);
    close();
  };
  return html`<form class="talk-together" aria-label="The questions together" onSubmit=${(e) => { e.preventDefault(); send(false); }}>
    ${cards.map((c) => {
      const now = of(c), own = typeof now.text === "string";
      return html`<fieldset class="talk-ask" key=${c.id} data-card=${c.id}><legend class="body">${c.q}</legend>
        <div class="talk-ask__choices" role="group" aria-label=${c.q}>${c.choices.map((x, i) => html`<button type="button" key=${x} class=${cls("ork-btn", { primary: !own && now.pick === i })} aria-pressed=${String(!own && now.pick === i)}
          title=${i === c.pick && c.why ? c.why : undefined} onClick=${() => set(c, { pick: i })}>${i === c.pick ? "● " : ""}${x}</button>`)}</div>
        <input class="ork-field" value=${own ? now.text : ""} aria-label=${`Other…: ${c.q}`} placeholder="Other…" onInput=${(e) => set(c, e.target.value ? { text: e.target.value } : { pick: c.pick })} />
      </fieldset>`;
    })}
    <p class="cap talk-together__hint">Pick an answer: the leader writes it into the spec</p>
    <div class="talk-together__acts"><button type="submit" class="ork-btn primary" disabled=${!cards.length}>Send the answers</button>
      <button type="button" class="ork-btn quiet" disabled=${!cards.length} onClick=${() => send(true)}>Let ${named(lead)} decide</button></div>
  </form>`;
}

export function TalkPage({ props, close }) {
  const row = (board.value?.needs_you || []).find((r) => r.kind === "talk" && r.idea === props.idea) || null, parties = partiesAll();
  const [together, setTogether] = useState(!!props.together);
  const node = (mapData.value?.nodes || []).find((n) => n.slug === props.idea);
  const kept = useKept(props.idea, row ? row.questions.map((c) => c.id).join("|") : "");
  const g = (slug) => parties.find((x) => x.slug === slug);
  const title = node?.title || row?.title || "";
  const head = html`<header class="talk-page__head"><${Elem} name=${node?.element || ""} dim=${!node?.element} /><h2 class="talk-page__title">${title}</h2><span class="ork-label">Talk</span></header>`;
  const kq = (party) => (kept?.stances || []).find((x) => x.party === party)?.questions || [];       // the kept questions of a party, with how each stands
  if (!row) {                                                                                           // nothing waits: the Talk as kept
    const stances = (kept?.stances || []).filter((x) => x.stance || x.questions.length);
    return html`<article class="talk-page" data-kind="talk" data-idea=${props.idea} aria-label="Talk">${head}
      ${kept === undefined ? html`<p class="table-over__muted">Reading the Talk…</p>`
        : stances.length ? html`<ul class="talk-page__row" aria-label="The leaders’ stances">${stances.map((st) => html`<${Stance} key=${st.party} st=${st} g=${g(st.party)} asked=${st.questions} />`)}</ul>`
        : html`<p class="table-over__muted">Nothing waits for you in this Talk.</p>`}
    </article>`;
  }
  const scope = scopeOf(row), left = row.questions.filter((c) => !given.value[cardSig(scope, c)]);
  const first = row.stances.find((s) => s.party === left[0]?.by) || row.stances[0];
  const asked = (st) => (kq(st.party).length ? kq(st.party) : row.questions.filter((c) => c.by === st.party));
  return html`<article class="talk-page" data-kind="talk" data-idea=${props.idea} aria-label="Talk">${head}
    <ul class="talk-page__row" aria-label="The leaders’ stances">${row.stances.map((st) => html`<${Stance} key=${st.party} st=${st} g=${g(st.party)} asked=${asked(st)} />`)}</ul>
    ${left.length > 0 && !together && html`<p class="talk-page__acts"><button type="button" class="ork-btn" onClick=${() => setTogether(true)}>All the questions</button></p>`}
    ${together && html`<${Together} row=${row} g=${g(first?.party) || g(row.goal)} close=${close} />`}
  </article>`;
}
drawn("talk", TalkPage);
