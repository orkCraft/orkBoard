// The table of cards' pieces (goal 170): shared by docs/mockups/table-cards/ and docs/mockups/spreads/.
const O = "../../../design-system/orkui/", PIC = (f) => `../phone/feed-pics/${f}.png`, FACE = (f) => `../table-cards/faces/${f}.png`;
const Q = new URLSearchParams(location.search), FACE_OF = Q.get("face") || "desk", OPEN = Q.get("open") || "";
const head = (f) => `<img src="${O}races/${f}.png" srcset="${O}races/${f}@2x.png 2x" alt="">`;
const face = (f) => `<img src="${FACE(f)}" alt="">`;
const mark = (id) => `<img class="ork-mark" src="${O}marks/harness-${id}.png" srcset="${O}marks/harness-${id}@2x.png 2x" alt="">`;
const icon = (id) => `<svg class="ork-icon" aria-hidden="true"><use href="${O}icons/icons.svg#${id}"/></svg>`;
const sign = (s) => `<span class="ork-sign ${s}" aria-hidden="true"></span>`;
const elem = (e) => `<span class="ork-elem ${e}"></span>`;
const P = { om: "var(--ork-party-orkmaster)", tech: "var(--ork-party-ork)", art: "var(--ork-party-elf)", gd: "var(--ork-party-knight)", rel: "var(--ork-party-undead)", mkt: "var(--ork-party-gnome)" };
const H = { tech: "shaman-elder", art: "dryad-elder", gd: "unicorn-elder", rel: "lich-elder", mkt: "fairy-elder" };
const N = { om: "Orkmaster", tech: "Tech", art: "Art", gd: "Game design", rel: "Release", mkt: "Marketing" };
const CH = { tech: "ork", art: "elf", gd: "knight", rel: "undead", mkt: "gnome" };
const pot = (id, now, low = false) => `<div class="pot${low ? " low" : ""}">${mark(id)}<span class="slot"><span class="ork-potion small${low ? " is-warn" : ""}" style="--ork-potion-left:${now / 100}"></span></span><span class="pct">${now}%</span></div>`;
const LAB = (t, k) => `<p class="lab" style="--pc:${P[k] || "var(--ork-ink-faint)"}"><span class="dot"></span>${t}</p>`;
const MARK = { for: "✓", risk: "!", question: "?", against: "✕" };
// a token: whose (its party's colour), which view, its word
const tok = (k, v, word = v, cls = "") => `<span class="tok ${cls}" style="--tc:${P[k]}" title="${N[k]}: ${v}"><i>${MARK[v]}</i>${word}</span>`;
const avOf = (k) => k === "om" ? `<span class="av face">${face("thoughtful")}</span>` : `<span class="av">${head(H[k])}</span>`;

// S: a goal upright. ix: its rune and its kind; foot: a bar or its tokens
const S = (k, ix, title, line, foot = "", cls = "", st = "") => `<article class="cd s ${cls}" style="--pc:${P[k]};${st}"><span class="ix tl">${ix}</span>
  ${cls.includes("up") ? `<span class="ask tok asks"><i>!</i></span>` : ""}<span class="pic">${k === "om" ? face("thoughtful") : head(H[k])}</span><b>${title}</b>${line ? `<small>${line}</small>` : ""}${foot}<span class="ix br">${ix}</span></article>`;
// M: a leader's word on its side. ix: top right; foot: the details bottom left
const M = (k, when, title, body = "", foot = "", cls = "", ix = "") => `<article class="cd m ${cls}" style="--pc:${P[k]}"><span class="ix tr">${ix}</span>
  <div class="ph">${avOf(k)}<span class="who"><b>${N[k]}</b><small>${when}</small></span></div>
  ${title ? `<h3>${title}</h3>` : ""}${body ? `<p>${body}</p>` : ""}${foot ? `<div class="foot">${foot}</div>` : ""}</article>`;
const ART = (when) => `<article class="cd m art" style="--pc:${P.art}"><span class="shot"><i></i></span>
  <div class="ph">${avOf("art")}<span class="who"><b>Art</b><small>${when}</small></span></div>
  <div class="over"><b>The lobby, after</b><small>2 screens changed · the game's colours</small></div></article>`;

// L: the question opened, its ways
const L = () => `<div class="veil"><article class="cd l"><span class="ix tl">${elem("meadow")}${sign("question")}</span><span class="ix br">${elem("meadow")}${sign("question")}</span>
  <button class="btn shut">${icon("close")}Close</button>
  <div class="ph">${avOf("tech")}<span><b>Tech asks you</b><small>Double jump · 11:58</small></span></div>
  <h2>How high is the second jump?</h2>
  <p>A second press in the air jumps again, once. Its height sets how far a round's coins can be.</p>
  <div class="toks">${tok("gd", "for", "Game design: half", "big")}${tok("art", "question", "Art: its sprite?", "big")}</div>
  <div class="ways">
    <button class="way pick"><span class="k">1</span><span>Half<small>Game design's pick</small></span></button>
    <button class="way"><span class="k">2</span><span>The same<small>One rule for both jumps</small></span></button>
    <button class="way"><span class="k">3</span><span>Tech decides<small>Tech picks after a try</small></span></button>
    <button class="way other"><span class="k">4</span><span>Your own words…</span></button></div>
  <div class="notes"><b>Why the tokens</b>
    <p>${tok("gd", "for", "Game design")} Half keeps a round's coins in reach.</p>
    <p>${tok("art", "question", "Art")} Either way the sprite needs a second pose.</p></div>
  <div class="lfoot"><span>From the hand</span><span>Tech waits for it</span></div></article></div>`;

