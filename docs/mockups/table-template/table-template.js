// Decision §283's "drawn first": the table's template, a mockup page. Nothing here is in the product. It lays one window of a party
// game at work (Game design, Tech, Art and Marketing at the table) in the scene asked for; the words are samples, the parts orkUI's.
//   ?scene=project      the Orkmaster's project, nothing picked (§283.16.1), with the column's three piles and the right column
//   ?scene=idea-om      an idea picked, through the Orkmaster: the leaders' assessments as small cards (§283.16.3)
//   ?scene=idea-leader  the same idea through Tech: its verdict, what needs your answer, what could be better (§283.16.4)
//   ?scene=ask          that table with one of Tech's cards lifted to the table's foot, its ways in the hand (§283.19)
//   ?scene=leader       Tech's project: the header of small cards in three groups over its scheme (§283.16.2)
//   &layout=groups|rows the idea through a leader in one row of three groups, or in three rows (the owner's pick)
//   &small=a|b          the small card's face: dots in the bottom left (a) or along the foot under a kind's pip (b)
//   &balloon=1          the Orkmaster's news over the start of the tabs (§283.9)
//   &hover=1            a small card's preview (§283.4)
const Q = new URLSearchParams(location.search);
const scene = Q.get("scene") || "project", layout = Q.get("layout") || "groups", face = Q.get("small") || "a";
const balloon = Q.get("balloon") === "1", hover = Q.get("hover") === "1";
const pics = Q.get("pics") === "1", card = Q.get("card") || "conflict";   // &pics=1: the ways with the owner's pictures (docs/pictures-wanted.md, sheet 1); &card=risk: the risk lifted
const O = "../../../design-system/orkui/";

const head = (f, cls = "") => `<img class="ork-race__head ${cls}" src="${O}races/${f}.png" srcset="${O}races/${f}@2x.png 2x" alt="">`;
const icon = (n, cls = "") => `<svg class="ork-icon ${cls}" aria-hidden="true"><use href="${O}icons/icons.svg#${n}"/></svg>`;
const sign = (n, cls = "") => `<span class="ork-sign ${n} ${cls}" aria-hidden="true"></span>`;

const L = {   // the leaders at the table, in the route's order
  game: { name: "Game design", party: "game", hue: "knight", head: "unicorn-elder", hero: "Dungeon Master Knight", seat: "knight-warrior" },
  tech: { name: "Tech", party: "tech", hue: "ork", head: "shaman-elder", hero: "Scene Shaman", seat: "peon-warrior" },
  art: { name: "Art", party: "art", hue: "elf", head: "dryad-elder", hero: "Sprite Dryad", seat: "elf-warrior" },
  mkt: { name: "Marketing", party: "marketing", hue: "gnome", head: "fairy-elder", hero: "Position Gnome", seat: "gnome-warrior" },
};
const ORDER = ["game", "tech", "art", "mkt"];

const G = {   // the goals: a rune is a shape and an element's colour (§206.10)
  results: { t: "Results screen with the round's best answer", rune: "key", el: "dust", kind: "screen", route: ["game", "tech", "art"] },
  timer: { t: "Round timer shows on every phone", rune: "eye", el: "ice", kind: "feature", route: ["game", "tech"] },
  music: { t: "Lobby music loop", rune: "hook", el: "meadow", kind: "sound", route: [] },
  seat: { t: "Keep the seat when a socket reconnects", rune: "tusks", el: "ice", kind: "feature", route: ["tech", "game"] },
  reset: { t: "Reset the round timer when a player rejoins", rune: "ladder", el: "lava", kind: "bug", route: ["tech"] },
  lobby: { t: "Tidy the lobby code", rune: "spiral", el: "void", kind: "tidy", route: ["tech"] },
  bar: { t: "A timer bar that drains", rune: "staff", el: "meadow", kind: "picture", route: ["art", "tech"] },
  colours: { t: "Check the bar's colours", rune: "hourglass", el: "dust", kind: "picture", route: ["art"] },
  rules: { t: "Write the timer's rules", rune: "diamond", el: "lava", kind: "mechanic", route: ["game"] },
  sound: { t: "A sound at the round's end", rune: "wave", el: "void", kind: "sound", route: ["art"] },
  seats: { t: "Seat colours by player", rune: "comb", el: "ice", kind: "screen", route: ["art", "tech"] },
};

const rune = (g, cls = "") => `<i class="ork-rune ${G[g].rune} ${cls}" style="color:var(--ork-elem-${G[g].el})" aria-hidden="true"></i>`;
const hue = (p) => `var(--ork-party-${L[p].hue})`;

// ---- cards --------------------------------------------------------------------------------------------------------------
// A big card, 144 x 202, read by its four corners (§251.2): the rune, the kind, who, how much; its window between (§252).
function big(g, { kind = G[g].kind, title = G[g].t, win = "", who = "", much = "", cls = "", signal = "" } = {}) {
  return `<article class="bc ${cls} ${signal}" data-el="${G[g].el}">
    <div class="bc-top">${rune(g)}${sign(kind)}</div>
    <p class="bc-t">${title}</p>
    <div class="bc-win">${win}</div>
    <div class="bc-foot"><span class="bc-who">${who}</span><span class="bc-much">${much}</span></div></article>`;
}
const bigBack = (g, cls = "") => `<div class="ork-card-back bb ${cls}" title="${G[g].t}"><span class="ork-card-back__seal">${rune(g, "big")}</span></div>`;
const smBack = (g, cls = "") => `<div class="ork-card-back small sm-back ${cls}" title="${G[g].t}"><span class="ork-card-back__seal">${rune(g)}</span></div>`;
const plusBack = () => `<div class="ork-card-back small sm-back is-new" title="A new concern: it can be a goal of its own"><span class="ork-card-back__seal">${icon("plus")}</span></div>`;
const dots = (ps, done = []) => ps.map((p) => `<i class="dot${done.includes(p) ? " is-done" : ""}" style="--c:${hue(p)}"></i>`).join("");
// A small card, 56 x 78: an index with no words (§283.3). a: the dots in the bottom left; b: a kind's pip top right, the dots along the foot.
function sm(g, { pic = "", ps = G[g].route, done = [], signal = "", kind = G[g].kind, cls = "" } = {}) {
  const b = face === "b";
  return `<div class="sm ${b ? "is-b" : ""} ${signal} ${cls}" data-el="${G[g].el}" title="${G[g].t}">
    <span class="sm-tl">${rune(g)}</span>${b ? `<span class="sm-tr">${sign(kind)}</span>` : ""}
    <span class="sm-pic">${pic}</span><span class="sm-dots">${dots(ps, done)}</span></div>`;
}
// Where a picture made in Gemini will stand (§283.34): its kind said, so the owner sees which pictures are wanted.
const pic = (kind, words, inner = "") => `<span class="pic" data-kind="${kind}">${inner || sign(kind === "doubt" ? "question" : kind, "big")}<em>${words}</em></span>`;
const strip = (g) => `<div class="strip" data-el="${G[g].el}">${rune(g)}<span>${G[g].t}</span></div>`;
const edges = (n) => `<div class="edges">${Array.from({ length: n }, (_, i) => `<i style="--i:${i}"></i>`).join("")}</div>`;

// ---- the Orkmaster's column (§283.11–14) -------------------------------------------------------------------------------
function column(picked) {
  const fan = ["timer", "music", "results"];
  const mid = (fan.length - 1) / 2;
  const fanCards = fan.map((g, i) => `<div class="fan-card${g === picked ? " is-picked" : ""}" style="--i:${i};--d:${i - mid}">${smBack(g, g === "timer" ? "is-play" : "")}</div>`).join("");
  const ideasLine = picked === "results" ? `talked over: <b>Results screen…</b>` : `reading: <b>Lobby music loop</b>`;
  const deck = ["reset", "reset", "seat"].map((g, i) => `<div class="lie" style="--i:${i}">${smBack(g)}</div>`).join("");
  return `<nav class="col bronze" aria-label="The Orkmaster's column">
    <div class="col-head">${head("peon-crown", "mid")}<div class="col-name"><b>Shop: the party game for one room</b><span>Game · Being made</span></div>${icon("chevron-down", "col-switch")}</div>
    <div class="pile"><span class="ork-plaque">Ideas</span><p class="pile-line">${ideasLine}</p><div class="fan">${fanCards}</div></div>
    <div class="pile"><span class="ork-plaque">Specs</span><p class="pile-line">writing: <b>Keep the seat when a socket…</b></p><div class="deck">${deck}</div></div>
    <div class="pile"><span class="ork-plaque">Implementation</span><p class="pile-line">at work: <b>Tidy the lobby code</b></p>
      <div class="impl">${big("lobby", { win: `<p class="words">Now: move the room's state into rooms.ts</p>`, who: head(L.tech.head, "hd16"), much: "4%", cls: "is-working" })}
        <div class="foot-strip" data-el="${G.bar.el}">${rune("bar")}<em>${head(L.art.head, "hd16")} ${head(L.tech.head, "hd16")}</em><b>3%</b></div>
        <div class="foot-strip" data-el="${G.colours.el}">${rune("colours")}<em>${sign("moon")} tonight 01:00</em></div></div></div>
  </nav>`;
}

// ---- the tabs (§283.8): the Orkmaster's is the column's head; a leader off the route is grey ----------------------------
function tabs(open, offRoute = []) {
  return `<div class="tabs lanes-grid">${ORDER.map((p) => `<button class="tab${p === open ? " is-open" : ""}${offRoute.includes(p) ? " is-off" : ""}" type="button" style="--c:${hue(p)}">
      <span class="ork-pennant${p === open ? " is-open" : " small"}" data-party="${L[p].party}" aria-hidden="true"></span>
      <span class="tab-head">${head(L[p].head, p === open ? "big" : "mid")}</span>
      <span class="tab-words"><b>${L[p].name}</b>${p === open ? `<span>${L[p].hero}</span>` : ""}</span></button>`).join("")}
    <button class="tab chair" type="button" title="A new chair at the table">${icon("plus")}<span class="tab-words"><b>New chair</b></span></button></div>`;
}
const title = (g, whom, stage) => `<div class="pane-title ork-plate">${rune(g)}<b>${G[g].t}</b><span class="through">· through ${whom}</span>
  <span class="phases">${["Idea", "Spec", "Implementation", "Done"].map((s) => `<span${s === stage ? ' aria-current="step"' : ""}>${s}</span>`).join("·")}</span></div>`;

// ---- the tables ---------------------------------------------------------------------------------------------------------
function projectTable() {   // §283.16.1: a lane a leader: the ideas it assesses now, then its specs' and its implementation's cascades
  const lanes = {
    game: { ideas: [smBack("results", "is-thinking"), sm("timer", { pic: sign("check", "big ok"), done: ["game", "tech"] })],
      specs: strip("seat") + edges(0) + big("seat", { title: "Game design's part: where the seat waits", kind: "page", win: `<p class="words">The seat waits 30 s for its player, then the bot plays it.</p>`, who: head(L.game.head, "hd16"), much: "1%" }),
      impl: "" },
    tech: { ideas: [smBack("results", "is-thinking"), sm("timer", { pic: sign("check", "big ok"), done: ["game", "tech"] })],
      specs: strip("seat") + edges(1) + bigBack("seat", "is-writing"),
      impl: strip("lobby") + edges(1) + big("lobby", { title: "Move the room's state into rooms.ts", kind: "work", win: `<p class="words">Steps: read · move · test</p>`, who: head(L.tech.seat, "hd16"), much: "4%", cls: "is-working" }) },
    art: { ideas: [smBack("results", "is-thinking")],
      specs: "",
      impl: strip("bar") + edges(1) + big("bar", { title: "Draw the bar's twelve frames", kind: "picture", win: pic("picture", "what the work made: the bar's frames"), who: head(L.art.seat, "hd16"), much: "3%", cls: "is-working" }) },
    mkt: { ideas: [], specs: "", impl: "" },
  };
  return `<div class="lanes lanes-grid">${ORDER.map((p) => {
    const l = lanes[p];
    if (!l.ideas.length && !l.specs && !l.impl) return `<section class="lane" style="--c:${hue(p)}"><p class="ork-plate free">${L[p].name} is free · throw a goal here or @${L[p].name}</p></section>`;
    return `<section class="lane" style="--c:${hue(p)}">
      <p class="band">Ideas</p><div class="row-sm">${l.ideas.join("") || `<i class="none">—</i>`}</div>
      <p class="band">Specs</p><div class="cascade">${l.specs || `<i class="none">—</i>`}</div>
      <p class="band">Implementation</p><div class="cascade">${l.impl || `<i class="none">—</i>`}</div></section>`;
  }).join("")}</div>`;
}

function ideaOmTable() {   // §283.16.3: under each leader of the route a small card, face down while it assesses, its verdict once done
  const say = {
    game: [sm("results", { pic: sign("check", "big ok"), ps: ["game"], done: ["game"] }), "Go", "the best answer is the round's end"],
    tech: [sm("results", { pic: `<b class="verdict">!</b>`, ps: ["tech"], done: ["tech"], signal: "sig-alert" }), "Doubt · 2 to answer", "one clock on the server"],
    art: [smBack("results", "is-thinking"), "Assessing…", "about 20 s"],
  };
  const lanes = ORDER.map((p) => {
    if (!say[p]) return `<section class="lane is-off"><p class="ork-plate free">${L[p].name} is not on this goal</p></section>`;
    const [card, verdict, line] = say[p];
    const prev = hover && p === "tech" ? `<div class="preview">${big("results", { kind: "question", title: "Doubt: one clock on the server", win: pic("doubt", "picture: how far Tech agrees", head(L.tech.head + "-worried", "big")), who: head(L.tech.head, "hd16"), much: "asks you", signal: "sig-alert" })}</div>` : "";
    return `<section class="lane" style="--c:${hue(p)}"><div class="say">${card}${prev}<p><b>${verdict}</b><span>${line}</span></p></div></section>`;
  }).join("");
  return `<div class="om-route ork-plate">${head("peon-crown", "hd16")} Route: Game design · Tech · Art <span>· its spec ≈ 9% of Codex's 5 hours</span>
      <button class="ork-btn quiet" type="button" disabled>Judge again now</button></div>
    <div class="lanes lanes-grid">${lanes}</div>`;
}

const TECH = {   // Tech's say on the idea (§283.23): its verdict, what needs your answer, what could be better
  verdict: () => big("results", { kind: "question", title: "Doubt: one clock on the server", win: pic("doubt", "picture: how far Tech agrees", head(L.tech.head + "-worried", "big")), who: head(L.tech.head, "hd16"), much: "≈1%" }),
  needs: [
    () => big("results", { kind: "conflict", title: "Goes against §208: the round's state lives on the server", win: `<p class="words">The best answer would be picked on each phone.</p>`, who: head(L.tech.head, "hd16"), much: "asks you", signal: "sig-alert" }),
    () => big("results", { kind: "alert", title: "Every answer is kept until the round ends", win: `<p class="words">A room of eight keeps 64 answers in memory.</p>`, who: head(L.tech.head, "hd16"), much: "asks you", signal: "sig-alert" }),
  ],
  better: [
    () => big("results", { kind: "tune", title: "Show the best answer after the vote", win: pic("tune", "picture: smaller"), who: head(L.tech.head, "hd16"), much: "lighter" }),
    () => big("results", { kind: "feature", title: "Keep the last five rounds' best", win: pic("feature", "picture: more"), who: head(L.tech.head, "hd16"), much: "heavier" }),
  ],
};
function ideaLeaderTable(lifted) {   // §283.16.4
  const group = (label, cards, cls = "") => `<section class="grp ${cls}"><p class="band">${label}</p><div class="grp-cards">${cards.map((c, i) => (lifted !== false && label.startsWith("Needs") && i === lifted) ? `<div class="bc-slot"></div>` : c()).join("")}</div></section>`;
  return `<div class="idea-${layout}">${group("Its verdict", [TECH.verdict], "is-one")}${group("Needs your answer", TECH.needs)}${group("Could be better", TECH.better)}</div>`;
}

function leaderTable() {   // §283.16.2: Tech's project: the header in three groups, its scheme under it
  const grp = (label, cards) => `<div class="hgrp"><p class="band">${label}</p><div class="hcards">${cards}</div></div>`;
  const header = `<div class="lheader">
    ${grp("At work", smBack("seat") + smBack("reset") + sm("lobby", { pic: head(L.tech.seat, "mid"), done: [] }) + sm("bar", { pic: head(L.tech.seat, "mid"), ps: ["art", "tech"], done: ["art"] }))}
    ${grp("Concerns", smBack("lobby", "sig-alert-back") + plusBack())}
    ${grp("Ask", `<div class="sm ask" title="Ask Tech: take parts of the scheme with the hand">${sign("question", "big")}<span class="ask-hand">${icon("eye")}</span></div>`)}
    <button class="ork-btn quiet more" type="button" aria-label="Tech's menu">${icon("more-horizontal")}</button></div>`;
  const tile = (name, line, cls = "") => `<div class="tile ${cls}"><b>${name}</b><span>${line}</span></div>`;
  return `${header}<div class="scheme">
    <div class="sch-col"><p class="sch-h">server/ <span>Express</span></p>${tile("index.ts", "its doors · 2 files")}${tile("rooms.ts", "its data · 2 files · ! the room's state in two places", "is-hot")}${tile("lobby.ts", "its data · 2 files", "is-reach")}</div>
    <div class="sch-link">HTTP: 1 route</div>
    <div class="sch-col"><p class="sch-h">client/ <span>Vite</span></p>${tile("net.ts", "its face · 2 files")}${tile("timer.ts", "its face · 1 file", "is-reach2")}</div></div>`;
}

// ---- the right column (§283.7, §283.27): the head what never changes the table, then the discard's two piles ------------
function rightColumn() {
  // a row of potions (§285.1): three at most, their tops on one line; the 5 hours' share under each, the week's under a bottle smaller than the large
  const pot = (tool, left, share, week = "", cls = "") => `<figure class="pot${cls.includes("is-front") ? " is-front" : ""}" title="${tool}: ${share}${week ? `, the week ${week}` : ""}"><span class="ork-potion small ${cls}" style="--ork-potion-left:${left}" aria-hidden="true"></span><figcaption><b>${share}</b>${week ? `<span>week</span><span>${week}</span>` : ""}</figcaption></figure>`;
  const pots = `<div class="pots">${pot("Codex, where the work goes now", 0.62, "62%", "", "is-front")}${pot("Claude Code, back Thu 18:00", 0.02, "out", "3%", "size-vial is-danger")}${pot("Antigravity", 0.8, "80%", "30%", "size-small")}</div>`;
  return `<aside class="right bronze" aria-label="The discard">
    <div class="rhead">${pots}<div class="rh-side"><div class="rh-lamp"><span class="rh-here">Here<br>until 23:00</span><span class="ork-chain small" aria-hidden="true"></span></div><button class="ork-btn stop" type="button" title="Stop every run of this project's orks">Stop all</button></div></div>
    <span class="ork-plaque disc">Discard</span>
    <div class="pile2"><button class="ork-plate branch" type="button" title="Where it goes: press to choose the branch">${icon("git-merge")}main</button><span class="pile2-line">in dev · waits for main</span>
      <div class="pile2-cards">${edges(1)}${big("sound", { kind: "check", title: G.sound.t, win: pic("sound", "what the work made: the sound"), who: head(L.art.head, "hd16"), much: "12 min" })}</div></div>
    <div class="pile2"><button class="ork-plate branch" type="button" title="Where it goes: press to choose the branch">${icon("git-merge")}dev</button><span class="pile2-line">done · waits for dev</span>
      <div class="pile2-cards">${big("rules", { kind: "check", title: G.rules.t, win: `<p class="words">Round 90 s · vote 20 s · grace 5 s</p>`, who: head(L.game.head, "hd16"), much: "6 min" })}</div></div>
  </aside>`;
}

// ---- the hand (§283.5: its height never changes) -------------------------------------------------------------------------
const handCard = (g, kind, t, who, signal = "") => `<article class="hc ${signal}" data-el="${G[g].el}"><div class="bc-top">${rune(g)}${sign(kind)}</div><p class="bc-t">${t}</p><div class="hc-who">${head(L[who].head, "hd16")}</div></article>`;
function hand(ways) {
  const stacks = {
    game: handCard("results", "question", "How long does the best answer stay on screen?", "game", "sig-alert"),
    tech: handCard("results", "conflict", "Goes against §208: the round's state lives on the server", "tech", "sig-alert"),
    art: handCard("bar", "alert", "The bar's sprites come in four sizes", "art", "sig-alert"),
    mkt: "",
  };
  const plus = `<button class="ork-card ork-plus hplus" aria-label="New goal" title="New goal"><span class="ork-sigil" aria-hidden="true"><span class="ork-sigil__seal"><span class="ork-elem meadow" aria-hidden="true"></span></span></span>${icon("plus")}</button>`;
  const die = `<span class="ork-die small face-play" aria-hidden="true"><span class="ork-die__cube"><i class="ork-die__face is-up"></i><i class="ork-die__face is-front"></i><i class="ork-die__face is-right"></i><i class="ork-die__face is-back"></i><i class="ork-die__face is-left"></i><i class="ork-die__face is-down"></i></span></span>`;
  const book = `<span class="book" aria-hidden="true"></span>`;   // a closed book; orkUI draws it (and open, while the history is on the table)
  // the places, one size, each changing the table (§285.3): Play, the inventory, the history
  const end = `<div class="h-end${ways && scene !== "inventory" ? " is-lifting" : ""}"><figure><span class="place">${die}</span><figcaption>Play</figcaption></figure><figure><span class="place"><span class="ork-pack${scene === "inventory" ? " is-open" : ""}" aria-hidden="true"></span></span><figcaption>Inventory</figcaption></figure><figure><span class="place">${book}</span><figcaption>History</figcaption></figure></div>`;
  const row = `<div class="h-lanes lanes-grid${ways ? " is-sunk" : ""}">${ORDER.map((p) => `<div class="stack">${stacks[p] ? edges(p === "tech" ? 2 : 1) + stacks[p] : ""}</div>`).join("")}</div>`;
  return `<footer class="hand bronze${ways ? " has-ways" : ""}" aria-label="The hand"><div class="h-plus${ways ? " is-sunk" : ""}">${plus}</div>${row}${ways || ""}${end}</footer>`;
}
const WAYS = `<div class="ways">
  <article class="hc way" data-el="dust"><div class="bc-top">${rune("results")}${sign("conflict")}</div><p class="bc-t">The new one replaces §208</p><div class="way-win">${pic("replace", "picture: replace", sign("restructure", "big"))}</div><p class="way-line">Each phone picks; §208's slices change.</p></article>
  <article class="hc way is-up is-pick" data-el="dust"><div class="bc-top">${rune("results")}${sign("shield")}</div><p class="bc-t">Keep §208</p><div class="way-win">${pic("keep", "picture: keep", sign("shield", "big"))}</div><p class="way-line">The server picks the best answer; the idea is talked again within §208.</p><span class="pick-head" title="Tech's pick">${head(L.tech.head, "hd16")}</span></article>
  <article class="hc way" data-el="dust"><div class="bc-top">${rune("results")}${sign("pick")}</div><p class="bc-t">Tech decides</p><div class="way-win">${pic("leader", "picture: the leader decides", head(L.tech.head, "big"))}</div><p class="way-line">Tech's pick, said in its line.</p></article>
  <article class="hc way is-pen" data-el="dust"><div class="bc-top">${rune("results")}${sign("text")}</div><p class="bc-t">Your own words…</p><div class="way-win">${pic("pen", "picture: the pen", sign("text", "big"))}</div></article>
  <div class="way-acts"><button class="ork-btn quiet" type="button">Open…</button><button class="ork-btn quiet" type="button">Put it back</button></div></div>`;

// ---- the ways with pictures (§283.34, the owner's first sheet: docs/mockups/table-template/pictures/) ----------------------
// A way's card is read picture first: its corners, the picture, then its name and its line, so that at rest, cut by the hand's
// rim, it shows its picture and the first words of its name.
const PIC = {
  "replace": ["The new one replaces §208", "Each phone picks; §208's slices change.", "restructure"],
  "keep": ["Keep §208", "The server picks the best answer; the idea is talked again within §208.", "shield"],
  "smaller": ["Do the smaller one", "Keep only the last round's best answer.", "tune"],
  "later": ["Later", "After the round timer is on every phone.", "moon"],
  "drop": ["Drop it", "The results screen stays as it is.", "cross"],
  "split": ["Split it", "The screen now, the kept answers a goal of their own.", "restructure"],
  "go-on": ["Go on anyway", "Every answer kept; Tech's doubt written in the decision.", "play"],
  "mitigate": ["Keep the last answer only", "Each phone's answer is dropped when the round ends.", "shield"],
  "accept-risk": ["Accept the risk", "64 answers in memory for a room of eight; said in the decision.", "alert"],
  "ask-more": ["Ask more", "How many rounds does a room play?", "question"],
  "leader-decides": ["Tech decides", "Tech's pick, said in its line.", "pick"],
  "own-words": ["Your own words…", "", "text"],
  "start-again": ["Start again", "The task runs again from the last green commit.", "work"],
  "take": ["Take", "The proposed goal goes in line.", "check"],
  "not-a-problem": ["Not a problem", "The concern is not raised again until its part changes.", "check"],
  "make-it-a-goal": ["Make it a goal", "The + card opens with these words.", "feature"],
};
function wayCard(id, { up = false, pick = false, g = "results" } = {}) {
  const [name, line, kind] = PIC[id];
  return `<article class="hc way pic-way${up ? " is-up" : ""}${pick ? " is-pick" : ""}${id === "own-words" ? " is-pen" : ""}" data-el="${G[g].el}">
    <div class="bc-top">${rune(g)}${sign(kind)}</div><div class="way-pic"><img src="pictures/${id}.png" alt=""></div>
    <p class="bc-t">${name}</p>${line ? `<p class="way-line">${line}</p>` : ""}${pick ? `<span class="pick-head" title="Tech's pick">${head(L.tech.head, "hd16")}</span>` : ""}</article>`;
}
const acts = `<div class="way-acts"><button class="ork-btn quiet" type="button">Open…</button><button class="ork-btn quiet" type="button">Put it back</button></div>`;
const WAYS_CONFLICT = `<div class="ways">${wayCard("replace")}${wayCard("keep", { up: true, pick: true })}${wayCard("leader-decides")}${wayCard("own-words")}${acts}</div>`;
const WAYS_RISK = `<div class="ways">${wayCard("mitigate", { pick: true })}${wayCard("accept-risk", { up: true })}${wayCard("smaller")}${wayCard("later")}${wayCard("own-words")}${acts}</div>`;
function gallery() {   // every way of the first sheet as a card on the table, at the size it is played
  return `<div class="gallery">${Object.keys(PIC).map((id) => `<figure>${wayCard(id)}<figcaption>${id}</figcaption></figure>`).join("")}</div>`;
}

// ---- the inventory as slots (§283.30–31, H1–H2), with the owner's second sheet (pictures/settings/) ----------------------
const SLOTS = [
  { key: "deep", label: "How deep", at: 1, ways: [
    ["thrift", "Thrift", "Every step on the cheaper tier; a spec reads less.", "−4% a week"],
    ["balance", "Balance", "Each step on its usual tier.", "Yours"],
    ["quality", "Quality", "Specs and acceptances on the elder tier.", "+6% a week"]], cheaper: true, star: 1 },
  { key: "start", label: "The build starts", at: 2, ways: [
    ["at-once", "At once", "A spec agreed starts its build with no wait.", "same"],
    ["in-30-min", "In 30 min", "A spec waits half an hour for your look.", "same"],
    ["in-2-hours", "In 2 hours", "A spec waits 2 hours for your look, then starts.", "Yours"],
    ["tonight", "Tonight", "Specs agreed by day are built in the night's window.", "−2% a week"],
    ["by-hand", "By hand", "Nothing is built until you press Start.", "same"]], cheaper: true, star: 3 },
  { key: "night", label: "The night", at: 1, ways: [
    ["night-off", "Off", "Nothing runs at night.", "−3% a week"],
    ["night-ideas", "Ideas and specs", "Talk and specs of the goals in line; nothing built.", "Yours"],
    ["night-builds", "And the builds", "What was agreed by day is built at night.", "+5% a week"],
    ["night-proposals", "And proposals", "The leaders you pick may propose a goal each, to a ready spec.", "+7% a week"]], star: 2 },
  { key: "lands", label: "Lands in dev by itself", at: 0, ways: [
    ["lands-on", "On", "A green result goes into dev with no press.", "Yours"],
    ["lands-off", "Off", "A green result waits in the discard for your press.", "same"]], star: 0 },
  { key: "push", label: "Push", at: 1, ways: [
    ["push-no", "No", "Nothing leaves this computer.", "same"],
    ["push-main", "Main only", "Main is pushed after To main; dev stays here.", "Yours"],
    ["push-both", "Dev and main", "Dev and main are pushed after each merge.", "same"]], star: 1 },
  { key: "parallel", label: "Goals at once", at: 0, ways: [
    ["goals-one", "One", "One goal's work at a time.", "Yours"],
    ["goals-few", "Three", "Up to three goals' work side by side.", "+8% a week"],
    ["goals-many", "Eight", "Up to eight goals at once, while the limits hold.", "+20% a week"]], star: 0 },
];
const pips = (n, at) => `<span class="pips">${Array.from({ length: n }, (_, i) => `<i class="${i === at ? "is-on" : ""}"></i>`).join("")}</span>`;
function slotCard(sl, pressed) {
  const [id, name, line, price] = sl.ways[sl.at];
  return `<figure class="slot${pressed ? " is-pressed" : ""}"><span class="ork-plaque slot-label">${sl.label}</span>
    <article class="hc way pic-way slot-card${pressed ? " sig-alert" : ""}" data-el="meadow"><div class="bc-top">${pips(sl.ways.length, sl.at)}${sl.cheaper ? `<span class="cheaper" title="A cheaper way exists">${icon("coins")}</span>` : ""}</div>
    <div class="way-pic"><img src="pictures/settings/${id}.png" alt=""></div><p class="bc-t">${name}</p><p class="way-line">${line}</p>
    <div class="bc-foot"><span></span><span class="bc-much">${price === "Yours" ? "as set" : price}</span></div></article></figure>`;
}
function invWay(sl, i, up) {
  const [id, name, line, price] = sl.ways[i];
  const yours = i === sl.at, star = i === sl.star;
  return `<article class="hc way pic-way${up ? " is-up" : ""}${yours ? " is-yours" : ""}" data-el="meadow"><div class="bc-top"><span class="yours">${yours ? "Yours" : ""}</span>${star ? `<span class="star" title="The Orkmaster's pick">${sign("pick")}</span>` : ""}</div>
    <div class="way-pic"><img src="pictures/settings/${id}.png" alt=""></div><p class="bc-t">${name}</p><p class="way-line">${line}</p>
    <div class="bc-foot inv-foot"><span></span><span class="bc-much">${yours ? "" : price}</span></div></article>`;
}
function inventory() {
  const key = Q.get("slot") || "deep";
  const row = `<div class="slots">${SLOTS.map((sl) => slotCard(sl, sl.key === key)).join("")}</div>`;
  const sl = SLOTS.find((x) => x.key === key);
  const up = sl.ways.findIndex((w, i) => i !== sl.at);
  const hand = `<div class="ways inv-ways">${sl.ways.map((w, i) => invWay(sl, i, i === up)).join("")}<div class="way-acts"><button class="ork-btn quiet" type="button">Undo</button><button class="ork-btn quiet" type="button">Put it back</button></div></div>`;
  return { row, hand };
}

const BALLOON = `<div class="balloon ork-frame" role="status">${head("peon-crown", "hd16")}<p>Claude Code is out until Thu 18:00: the work goes on with Codex.</p><button class="ork-btn quiet" type="button">Show</button><button class="ork-btn quiet x" type="button" aria-label="Close">${icon("close")}</button></div>`;

// ---- the window -----------------------------------------------------------------------------------------------------------
function win() {
  let picked = "", open = "", off = [], party = "orkmaster", body = "", ttl = "", lifted = "", ways = "";
  if (scene === "project") body = projectTable();
  if (scene === "idea-om") { picked = "results"; off = ["mkt"]; ttl = title("results", "the Orkmaster", "Idea"); body = ideaOmTable(); }
  if (scene === "idea-leader" || scene === "ask") {
    picked = "results"; open = "tech"; off = ["mkt"]; party = "tech"; ttl = title("results", "Tech", "Idea"); const which = card === "risk" ? 1 : 0;
    body = ideaLeaderTable(scene === "ask" ? which : false);
    if (scene === "ask") { lifted = `<div class="lifted">${TECH.needs[which]()}</div>`; ways = pics ? (which ? WAYS_RISK : WAYS_CONFLICT) : WAYS; }
  }
  if (scene === "leader") { open = "tech"; party = "tech"; body = leaderTable(); }
  if (scene === "pictures") { open = "tech"; party = "tech"; body = gallery(); }
  if (scene === "inventory") { const inv = inventory(); body = inv.row; ways = inv.hand; ttl = `<div class="pane-title ork-plate"><b>Inventory</b><span class="through">· how the project is set · the whole project</span></div>`; }
  return `<div class="win" data-scene="${scene}">
    ${column(picked)}
    <main class="table"><div class="table-top">${tabs(open, off)}</div>
      <div class="pane ork-table${scene === "inventory" ? " ork-leather" : ""}" data-party="${party}">${ttl}<div class="pane-body">${body}</div>${lifted}</div></main>
    ${rightColumn()}
    ${hand(ways)}
    ${balloon ? BALLOON : ""}
  </div>`;
}
document.getElementById("root").innerHTML = win();
