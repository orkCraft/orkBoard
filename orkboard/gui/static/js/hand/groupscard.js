// The backlog's groups are one card in the hand (docs/specs/135-a-new-goal-matched-against-the-face-down-pile.md §B.2; decisions §242.5): the row `groups` (realm/backlog_groups.py: `{kind: "groups", id, groups: [{id,
// goals: [{idea, title, party, head}], why, adds}], cost: {calls, usd_high} | null, blocks, priority, at}`), asked once at a reset over the goals put off: *These look like one goal*. A row of no goal's: `groupsStops`
// makes its stop, whole to the Orkmaster's lane (data.js `WHOLE`), the Orkmaster the asker (its crowned head). Its face is the hand's card (stopcard.js): orkUI's page sign in the window, the first group's titles as its
// name, *These look like one goal* at its foot. Lifted: each group a line of its goals' titles, each with its leader's head, its `why` under it, and **Join** or **Keep apart**; a group answered stays marked until every
// group has its answer, then `ideas.groups_answer {id, join}` goes (an unnamed group is kept apart by the host); at the card's foot **Not now** (`ideas.groups_now`). A group whose joining brings in another party says
// which. Its cost is the generic line under the buttons (cost.js; none where no decision is worded). The card says nothing of how many goals wait. While it lies lifted it tells the host (`ideas.groups_open`), which
// holds the queue of §239 for it for ten minutes at most; put down, it lets it go.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { Head } from "../orkui.js";
import { command } from "../link.js";
import { act, mapData } from "../shell/store.js";
import { way } from "./ways.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as routecard.js links its own
  const href = new URL("./groups.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const ASK = "These look like one goal";
const JOIN = "Join", APART = "Keep apart", NOT_NOW = "Not now";

/** The Orkmaster's head, crowned: the asker of a card that no party's leader asks. */
const orkish = () => {
  const ork = mapData.value?.project?.orkmaster || null;
  return { race: ork?.race || "peon", tier: ork?.tier || "crown" };
};

/** The hand's stop of the `groups` row among `rows` (the Needs you rows): at most one. `ctx`: as questions.js `projectStops` has it (`open`). */
export function groupsStops(rows, ctx) {
  return rows.filter((r) => r.kind === "groups").map((row) => {
    const head = orkish(), first = row.groups?.[0]?.goals || [], title = first.map((g) => g.title).join(" + ") || ASK;
    return { key: `groups/${row.id}`, kind: "groups", ref: row, row: { ...row, goal: "", idea: undefined }, node: null, task: null, label: ASK, gem: "", tone: "", gemTip: "", head, small: true, whoTip: "",
      title, full: title, text: "", why: "", g: null, party: { slug: "", name: "Orkmaster", head, lead: "Orkmaster" }, other: false };
  });
}

/** What joining a group would bring in besides its goals, said for the person: the party a goal of it would add to the first one's route. */
const addsWords = (adds) => {
  const names = (adds || []).map((slug) => (mapData.value?.goals || []).find((g) => g.slug === slug)?.title || slug);
  return names.length ? `Brings in ${names.join(", ")}` : "";
};

/** The lifted card. */
export function GroupsLifted({ s, close }) {
  const row = s.row || {}, groups = row.groups || [], [choice, setChoice] = useState({}), [busy, setBusy] = useState(false);
  useEffect(() => {                                              // the card lies lifted: the host holds the queue for it (and lets it go when it is put down)
    command("ideas.groups_open", { id: row.id, open: true }).catch(() => {});
    return () => { command("ideas.groups_open", { id: row.id, open: false }).catch(() => {}); };
  }, [row.id]);
  const send = async (next) => {
    setBusy(true);
    try {
      if (await act("ideas.groups_answer", { id: row.id, join: groups.filter((g) => next[g.id] === "join").map((g) => g.id), apart: groups.filter((g) => next[g.id] === "apart").map((g) => g.id) })) close?.();
    } finally { setBusy(false); }
  };
  const pick = (id, how) => {
    const next = { ...choice, [id]: how };
    setChoice(next);
    if (groups.every((g) => next[g.id])) send(next);             // every group has its answer: it goes
  };
  const notNow = async () => {
    setBusy(true);
    try { if (await act("ideas.groups_now", { id: row.id })) close?.(); } finally { setBusy(false); }
  };
  return html`<div class="hand-way hand-way--groups" data-kind="groups" data-groups=${row.id}>
    <p class="ork-label">${ASK}</p>
    ${groups.map((g) => html`<section key=${g.id} class="hand-group" data-group=${g.id} aria-label=${g.goals.map((x) => x.title).join(" + ")}>
      <ul class="hand-way__points hand-group__goals">${g.goals.map((x) => html`<li key=${x.idea} class="body hand-group__goal" data-goal=${x.idea}>${x.head?.race && html`<${Head} race=${x.head.race} tier=${x.head.tier} /> `}<span>${x.title}</span></li>`)}</ul>
      ${g.why && html`<p class="body hand-way__place" data-part="why">${g.why}</p>`}
      ${addsWords(g.adds) && html`<p class="cap hand-way__place" data-part="adds">${addsWords(g.adds)}</p>`}
      <div class="hand-answers hand-way__acts" role="group" aria-label=${`Answer for ${g.goals[0].title}`}>
        <button type="button" class="ork-btn primary" disabled=${busy} aria-pressed=${choice[g.id] === "join"} data-answer="join" title="One goal takes the others' words; the others go" onClick=${() => pick(g.id, "join")}>${JOIN}</button>
        <button type="button" class="ork-btn" disabled=${busy} aria-pressed=${choice[g.id] === "apart"} data-answer="apart" title="They stay as they are" onClick=${() => pick(g.id, "apart")}>${APART}</button>
      </div>
    </section>`)}
    <div class="hand-answers hand-way__acts hand-group__foot" role="group" aria-label="Not now">
      <button type="button" class="ork-btn quiet" disabled=${busy} data-answer="not_now" title="Nothing is joined; these are not asked again until the next reset" onClick=${notNow}>${NOT_NOW}</button>
    </div>
  </div>`;
}

/** The generic cost line under the lifted card: what the joins would cost in all, one `decide` call for each first goal whose decision is worded (the host's `cost.usd_high`, a ceiling); none where no decision is worded. */
const price = (s) => {
  const usd = Number(s.row?.cost?.usd_high);
  return Number.isFinite(usd) && usd > 0 ? { low: usd, high: usd } : null;
};

// The face: the page sign, the Orkmaster as its asker, *These look like one goal* at its foot.
way("groups", { sign: "page", head: orkish, foot: () => ASK, price, Lifted: GroupsLifted });
