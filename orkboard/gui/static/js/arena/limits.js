// What is left of your AI tools, and what used it (docs/specs/49-one-window.md §8, docs/specs/91-the-owners-list.md §2, decisions §107).
//
//   export function Limits({ provider })      — the panel a tool's chip opens in the top bar (shell/topbar.js): `<Limits provider=${id} />`
//   export function Usage({ provider, line })  — the same panel's body on its own: *What used it* for one tool
//   export function tokensWords(n)             — "12k tokens"
//
// **`<Limits />` with no provider** is the tool lines as before (spec 90 §2.3): a line per tool of the snapshot's limits — its mark and name,
// ten diamonds for what is left (the last ones hatched for the reserve, Claude only), its % — and under them what the hatching is and when the
// tightest window resets. A tool whose limits were not read says so and has no diamonds.
//
// **`<Limits provider=${id} />`** is one tool's panel: its line (mark, name, diamonds, % left, its window and when it resets), then — when
// the host says it can (`ideas.usage` answers `scopes` with "all") — a two-way switch *This project* / *All projects*, then a row per party
// (its name, a thin meter, its share of the window) and under it a smaller row per member, then *Outside Orkboard*, and the line *Each share
// is estimated: the limit read before and after, split by the tokens of each call.* It asks `ideas.usage {provider, scope}` when it is
// shown (and again when the tool's % changes or the switch is pressed), keeps the last answer while it asks, and says in words when the
// host cannot tell. With fewer than two reads the rows carry tokens and say so. The caller puts it inside the panel; it has no frame of its own
// (`.arena-usage`, js/arena/limits.css) and the host's `ideas.usage` is the one place the shares come from (no model, realm/limit_usage.py).
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { ORKUI } from "../orkui.js";
import { town, command } from "../link.js";
import { resetWords } from "../shell/topbar.js";
import { limitLine } from "./arenawords.js";

const MARKED = ["claude", "codex", "agy", "cursor", "hermes", "pi"];

/** A count of tokens in words: *840 tokens*, *12k tokens*, *1.2M tokens*. */
export function tokensWords(n) {
  const v = Number(n) || 0;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1).replace(/\.0$/, "")}M tokens`;
  if (v >= 1e3) return `${v >= 1e4 ? Math.round(v / 1e3) : (v / 1e3).toFixed(1).replace(/\.0$/, "")}k tokens`;
  return `${v} ${v === 1 ? "token" : "tokens"}`;
}

const shareWords = (n) => (n > 0 ? `${n} %` : "<1 %");

function Mark({ line }) {
  return html`<span class="arena-limit__name">${MARKED.includes(line.provider) && html`<img class="ork-mark" src=${`${ORKUI}/marks/harness-${line.provider}.png`} srcset=${`${ORKUI}/marks/harness-${line.provider}@2x.png 2x`} alt="" draggable="false" />`} ${line.name}</span>`;
}

function Tool({ l }) {
  return html`<span class=${cls("arena-limit", { "is-unread": !l.read })} data-provider=${l.provider} title=${l.tip} tabindex="0" aria-label=${l.tip}>
    <${Mark} line=${l} />
    ${l.read ? html`<span class="ork-crystals" aria-hidden="true">${l.cells.map((c, i) => html`<i key=${i} class=${c}></i>`)}</span><b>${l.pct}</b>` : html`<b class="arena-muted">${l.pct}</b>`}
  </span>`;
}

function Row({ title, share, tokens, tokensOnly, sub, party }) {
  return html`<div class=${cls("arena-usage__line", { "is-sub": sub })} data-party=${party}>
    <span class="arena-usage__who">${title}</span>
    ${tokensOnly ? html`<span class="arena-usage__pct">${tokensWords(tokens)}</span>` : html`<i class="arena-usage__bar" aria-hidden="true"><b style=${`width: ${Math.min(100, Math.max(0, share))}%`}></b></i><span class="arena-usage__pct">${shareWords(share)}</span>`}
  </div>`;
}

/** *What used it* for one tool: asks `ideas.usage` and draws the answer. `line`: the tool's `limitLine` (from the snapshot), for the answer to refresh on. */
export function Usage({ provider, line }) {
  const [scope, setScope] = useState("project");
  const [got, setGot] = useState(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let live = true;
    command("ideas.usage", { provider, scope }, true).then((a) => { if (live) { setGot(a); setFailed(false); } }).catch(() => { if (live) setFailed(true); });
    return () => { live = false; };
  }, [provider, scope, line?.pct]);
  const rows = got?.rows || [];
  const only = !!got?.tokens_only;
  return html`<div class="arena-usage" data-provider=${provider} aria-busy=${String(!got && !failed)}>
    <div class="arena-usage__head">
      <span class="arena-cap">What used it</span>
      ${got?.window && html`<span class="arena-cap arena-usage__window">${got.window}</span>`}
      ${got?.scopes?.includes("all") && html`<span class="arena-usage__scope" role="group" aria-label="Which projects">
        ${[["project", "This project"], ["all", "All projects"]].map(([id, words]) => html`<button key=${id} type="button" class="ork-btn" aria-pressed=${String(scope === id)} onClick=${() => setScope(id)}>${words}</button>`)}
      </span>`}
    </div>
    ${failed && !got && html`<p class="arena-usage__empty">What used it is not known here.</p>`}
    ${got && html`<ul class="arena-usage__rows" aria-label="What used it">
      ${rows.map((r) => html`<li key=${r.party} class="arena-usage__row">
        <${Row} party=${r.party} title=${r.title} share=${r.share} tokens=${r.tokens} tokensOnly=${only} />
        ${r.members?.length > 0 && html`<ul class="arena-usage__members" aria-label=${`Members of ${r.title}`}>
          ${r.members.map((m) => html`<li key=${m.agent}><${Row} sub=${true} party=${`${r.party}/${m.agent}`} title=${m.name} share=${m.share} tokens=${m.tokens} tokensOnly=${only} /></li>`)}
        </ul>`}
      </li>`)}
      ${!only && html`<li class="arena-usage__row is-outside"><${Row} party="outside" title="Outside Orkboard" share=${got.outside || 0} tokens=${0} tokensOnly=${false} /></li>`}
    </ul>`}
    ${got && rows.length === 0 && html`<p class="arena-usage__empty">${only ? "No call of Orkboard has used this tool yet." : "No call of Orkboard has used this limit yet."}</p>`}
    ${got && only && rows.length > 0 && html`<p class="arena-usage__empty">The limit has not been read twice yet, so these are tokens, not shares of it.</p>`}
    <p class="arena-cap arena-usage__note">Each share is estimated: the limit read before and after, split by the tokens of each call.</p>
  </div>`;
}

export function Limits({ provider = "" } = {}) {
  const t = town.value, reserve = t?.reserve || null;
  const lines = (t?.limits || []).map((l) => limitLine(l, reserve, resetWords));
  if (provider) {
    const l = lines.find((x) => x.provider === provider);
    return html`<section class="arena-limits is-one" aria-label=${`What is left of ${l?.name || provider}`}>
      ${l && html`<${Tool} l=${l} />`}
      ${l?.reset && html`<span class="arena-cap arena-limits__note">${l.reset}</span>`}
      <${Usage} provider=${provider} line=${l} />
    </section>`;
  }
  const kept = lines.some((l) => l.kept);
  const reset = lines.find((l) => l.reset)?.reset || "";
  return html`<section class="arena-limits" aria-label="What is left of your AI tools">
    ${lines.map((l) => html`<${Tool} key=${l.provider} l=${l} />`)}
    ${lines.length > 0 && html`<span class="arena-cap arena-limits__note">${kept ? `hatched: kept for ${reserve?.night ? "the morning" : "tonight"}` : ""}${kept && reset ? " · " : ""}${reset}</span>`}
  </section>`;
}
