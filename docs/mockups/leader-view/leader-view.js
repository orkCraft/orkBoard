// A mockup's page: builds Product's tab with its map, and the view in the face asked for. Sample words for this very product.
const Q = new URLSearchParams(location.search);
const face = Q.get("face") || "a", state = Q.get("state") || "view";
const narrow = matchMedia("(max-width: 760px)").matches;
const R = "../../../design-system/orkui/races/";
const head = (f, cls = "") => `<img class="ork-race__head ${cls}" src="${R}${f}.png" srcset="${R}${f}@2x.png 2x" alt="">`;
const VIEW = {
  works: [
    ["A goal runs from Talk to done with the gate's record on its page.", "163-products-tree-on-the-board"],
    ["Each leader's map takes the shape of its framework.", "165-each-leaders-map-a-board-games-shape"],
    ["The Orkmaster reads the decisions before it routes.", "166-the-orkmaster-reads-the-decisions"],
  ],
  hurts: [
    ["Product's tree is not on the Board yet, so its map is still the old list.", "163-products-tree-on-the-board"],
    ["No leader says where the product stands, only a line a goal.", "§282"],
  ],
  next: [
    ["Read a leader's view before laying a goal on its tab.", "167-each-leaders-view-of-the-product"],
    ["The phone's party page shows the same view, a goal of its own.", "§282.5"],
  ],
};
const WHEN = "Looked 8 Nov 2026 · read 3 goals done, §281, §282 and 6 parts of its map";
const NONE = "Product has not looked at this project yet.";
const btnLook = `<button class="ork-btn primary" type="button">Look now: makes one call</button>`;
const lis = (a) => a.map(([t, s]) => `<li>${t} <code>${s}</code></li>`).join("");
const sec = (k, l) => `<section><h3>${l}</h3><ul>${lis(VIEW[k])}</ul></section>`;
const heads = () => sec("works", "Works") + sec("hurts", "Hurts") + sec("next", "Next");
const x = `<button class="ork-btn quiet x" type="button" aria-label="Close">Close <span class="ork-kbd">Esc</span></button>`;
const who = (close = true) => `<div class="vhead"><span class="ork-race">${head("unicorn-elder", "mid")}</span><span class="who">Product's view</span>${close ? x : ""}</div>`;
const whenLine = () => `<div class="when">${WHEN}</div>`;
const noneBlock = () => `<p class="none">${NONE}</p>${btnLook}`;

const lanes = `<div class="lanes">
  <div class="lane"><div class="ork-label">Talk</div>
    <div class="ork-card"><div class="card-t">A leader's view on its tab</div><div class="card-s">167 · Product asks</div></div>
    <div class="ork-card"><div class="card-t">The phone's party page</div><div class="card-s">168 · new</div></div></div>
  <div class="lane"><div class="ork-label">Spec</div>
    <div class="ork-card"><div class="card-t">Product's tree on the Board</div><div class="card-s">163 · Design writes</div></div></div>
  <div class="lane"><div class="ork-label">Work</div>
    <div class="ork-card"><div class="card-t">Each leader's map, a board game's shape</div><div class="card-s">165 · Tech, stage 4</div></div>
    <div class="ork-card"><div class="card-t">The Orkmaster reads the decisions</div><div class="card-s">166 · a Grunt working</div></div></div>
</div>`;
const map = `<div class="map"><div class="ork-label">Product's map</div><div class="tree">
  <div class="ork-row root"><span class="ork-race">${head("knight-elder", "bare")}<span class="ork-race__word">Orkboard: the Board for any AI tool</span></span></div>
  <div class="ork-row">Parties and goals</div><div class="ork-row hot">The hand and Play</div><div class="ork-row">Release to main</div><div class="ork-row">VS Code and the window</div>
  <div class="ork-row">The leaders' maps</div><div class="ork-row">The decisions log</div><div class="ork-row">The gate</div><div class="ork-row">The phone</div></div></div>`;

const tabs = (more = "") => `<div class="tabs ork-tabs" role="tablist">
  ${[["Orkmaster", "peon-crown"], ["Product", "unicorn-elder"], ["Design", "dryad-elder"], ["Tech", "shaman-elder"], ["Release", "lich-elder"]]
    .map(([n, f]) => `<button class="ork-tab" role="tab" aria-selected="${n === "Product"}"><span class="ork-race">${head(f, "bare")}<span class="ork-race__word">${n}</span></span></button>`).join("")}
  <span class="more"><button class="ork-btn quiet" type="button" aria-label="The party's menu" aria-haspopup="menu">&hellip;</button></span></div>${more}`;

const hand = `<div class="hand">
  <div class="ork-card asks"><div class="card-t">Which face for a leader's view?</div><div class="card-s">Product asks you</div></div>
  <div class="ork-card"><div class="card-t">Play: 166, stage 2</div><div class="card-s">a Grunt is ready</div></div>
  <div class="ork-card"><div class="card-t">To main: 165</div><div class="card-s">the gate is green</div></div></div>`;
const discard = `<aside class="discard"><div class="ork-label">Done</div>
  ${["162 The past from history", "161 The table's look", "160 The tools of a craft", "159 A way's own line", "158 The window as a table"].map((t) => `<div class="ork-row card-s">${t}</div>`).join("")}</aside>`;

let paneTop = "", over = "", menu = "";
if (face === "c" || (narrow && face === "a")) {
  menu = `<div class="menu" role="menu"><div class="ork-row is-on" role="menuitem">Product's view <span class="ork-kbd">V</span></div>
    <div class="ork-row" role="menuitem">Its table</div><div class="ork-row" role="menuitem">Its map, look again</div><div class="ork-row" role="menuitem">Rest the party</div></div>`;
  const inner = state === "view" ? heads() + `<div class="src">${whenLine()}</div>` : noneBlock();
  over = `<div class="sheet">${who()}<div class="view cols">${inner}</div></div>`;
} else if (face === "a") {
  const inner = state === "view" ? heads() + whenLine() : noneBlock();
  over = `<div class="bubble" role="dialog" aria-label="Product's view">${who()}<div class="view">${inner}</div>
    <div class="evening"><div class="ork-label">This evening</div><p>The evening line waits: only one opens by itself a party a day.</p></div></div>`;
} else if (face === "b") {
  paneTop = state === "view"
    ? `<div class="plate">${who(false)}<div class="view"><div class="cols">${heads()}</div></div><div class="foot view">${whenLine()}</div></div>`
    : `<div class="plate slim view"><span class="ork-race">${head("unicorn-elder", "bare")}</span><p class="none">${NONE}</p>${btnLook}</div>`;
}
document.getElementById("root").innerHTML = `<div class="win">
  <header class="top"><b>Orkboard</b><span>orkBoard</span><span>main</span></header>
  <main class="table">${tabs(menu)}<div class="pane">${paneTop}${lanes}${map}${over}</div></main>
  ${discard}${hand}</div>`;
