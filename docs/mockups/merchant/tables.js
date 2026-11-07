/* The eighteen tables: each leader's table laid as its hero reads it (decisions §266.3: a hero brings its craft's framework,
   its lens's aspects (§184) and how its table is laid). The Orkmaster's is the Board; Release Night King's is dev against main;
   the sixteen heroes each lay their craft's map (spec 95 §3) by their school. The project is the mockup's Guild app, a party
   game; its goals, numbers and names are made up. Loaded before the page's script; it reads HEROES, RACE, HIMG and the
   pennants at call time. */
(() => {
  const E = e => e ? `<span class="ork-elem ${e}"></span>` : "";
  const S = id => `<span class="ork-sign ${id}"></span>`;
  const card = (name, o = {}) => `<div class="mc${o.cls ? " " + o.cls : ""}" style="${o.w ? `width:${o.w}px;` : ""}${o.h ? `height:${o.h}px;` : ""}${o.style || ""}">`
    + (o.e || o.sign ? `<div class="mc__top">${E(o.e)}${o.sign ? S(o.sign) : ""}</div>` : "") + `<b>${name}</b>${o.sub ? `<small>${o.sub}</small>` : ""}${o.foot || ""}</div>`;
  const lane = (h, inner, o = {}) => `<div class="ml${o.cls ? " " + o.cls : ""}" style="${o.w ? `width:${o.w}px;` : ""}${o.h ? `height:${o.h}px;` : ""}${o.style || ""}"><p class="ml__h">${h}${o.hs ? `<span>${o.hs}</span>` : ""}</p>${inner}</div>`;
  const chip = (t, cls = "") => `<span class="chip ${cls}">${t}</span>`;
  const meter = (f, cls = "") => `<span class="meter ${cls}"><i style="width:${Math.round(f * 100)}%"></i></span>`;
  const sq = s => `<span class="sq">${[...s].map(c => `<i class="${c === "." ? "" : c}"></i>`).join("")}</span>`;
  const at = (x, y, html, style = "") => `<div style="position:absolute;left:${x}px;top:${y}px;${style}">${html}</div>`;
  const phone = (rows, on) => `<div class="phone${on ? " on" : ""}">${rows.map(r => `<i class="${r}"></i>`).join("")}</div>`;
  let gid = 0;
  /* boxes and named arrows: nodes {id, x, y, w, h, html}, edges [from, to, label, {dash, both, curve}] */
  function graph(w, h, nodes, edges, style = "") {
    const N = Object.fromEntries(nodes.map(n => [n.id, n])), id = "ah" + (++gid);
    const ends = (a, b) => {
      const ca = [a.x + a.w / 2, a.y + a.h / 2], cb = [b.x + b.w / 2, b.y + b.h / 2], dx = cb[0] - ca[0], dy = cb[1] - ca[1];
      const t = (n) => Math.min(dx ? n.w / 2 / Math.abs(dx) : Infinity, dy ? n.h / 2 / Math.abs(dy) : Infinity);
      const ta = t(a) + 4 / Math.hypot(dx, dy), tb = t(b) + 6 / Math.hypot(dx, dy);
      return [ca[0] + dx * ta, ca[1] + dy * ta, cb[0] - dx * tb, cb[1] - dy * tb];
    };
    let lines = "", labels = "";
    edges.forEach(([f, t, lab, o = {}]) => {
      const [x1, y1, x2, y2] = ends(N[f], N[t]);
      lines += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" style="stroke:var(--ork-edge);stroke-width:1.5${o.dash ? ";stroke-dasharray:4 3" : ""}" marker-end="url(#${id})"${o.both ? ` marker-start="url(#${id}s)"` : ""}/>`;
      if (lab) labels += `<span class="elabel" style="left:${(x1 + x2) / 2 + (o.dx || 0)}px;top:${(y1 + y2) / 2 + (o.dy || 0)}px">${lab}</span>`;
    });
    return `<div class="mgraph" style="width:${w}px;height:${h}px;${style}"><svg width="${w}" height="${h}" aria-hidden="true"><defs>
      <marker id="${id}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L8 4L0 8z" style="fill:var(--ork-edge)"/></marker>
      <marker id="${id}s" viewBox="0 0 8 8" refX="1" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M8 0L0 4L8 8z" style="fill:var(--ork-edge)"/></marker></defs>${lines}</svg>`
      + nodes.map(n => `<div class="node" style="left:${n.x}px;top:${n.y}px;width:${n.w}px;height:${n.h}px">${n.html}</div>`).join("") + labels + `</div>`;
  }
  const svg = (w, h, inner, style = "") => `<svg width="${w}" height="${h}" style="position:absolute;left:0;top:0;overflow:visible;${style}" aria-hidden="true">${inner}</svg>`;

  /* ---------------- the maps ---------------- */
  const MAPS = {
    /* the Orkmaster: the Board, a lane a party, the first lane its routing and the goals in line */
    keeper: () => `<div class="mrow" style="height:390px">`
      + lane("In line", card("Friends list", { e: "void", sub: "routed: Product, Design", w: 160 }) + card("Guild bank", { e: "lava", sub: "waits: a question for you", w: 160, cls: "hot" }) + card("Talk: Daily quest", { sign: "question", sub: "Product and Tech disagree", w: 160 }), { w: 184, h: 390 })
      + lane("Product", card("Daily quest", { e: "dust", sub: "spec · its jobs", w: 160 }) + card("pains on Results", { e: "dust", sub: "a task", w: 144, style: "margin-left:16px" }), { w: 184, h: 390 })
      + lane("Design", card("Lobby chat", { e: "ice", sub: "work · 2 of 4", w: 160 }) + card("the chat line", { e: "ice", sub: "a Grunt at it", w: 144, style: "margin-left:16px", cls: "on" }), { w: 184, h: 390 })
      + lane("Tech", card("Waves", { e: "meadow", sub: "work · 3 of 5", w: 160 }) + card("spawner", { e: "meadow", sub: "a test fails twice", w: 144, style: "margin-left:16px", cls: "bad" }) + card("wave timer", { e: "meadow", sub: "done", w: 144, style: "margin-left:16px" }) + card("boss HP", { e: "meadow", sub: "next", w: 144, style: "margin-left:16px", cls: "faint" }), { w: 184, h: 390 })
      + lane("Release", card("Lobby chat 0.3", { e: "ice", sub: "in dev · the gate green", w: 160, cls: "good" }), { w: 184, h: 390 })
      + `</div>` + `<div class="mfoot"><span>The whole project through the Orkmaster: <b>a lane a party</b>, the first lane its routing, Talk and the goals in line.</span></div>`,

    /* Tech · Sh.man: C4 and hotspots: the containers and their named links, the hot parts of the one opened */
    "sh-c4": () => graph(972, 196, [
        { id: "ph", x: 0, y: 20, w: 150, h: 64, html: card("Phone client", { sign: "screen", sub: "Kotlin · 3 screens changed" }) },
        { id: "web", x: 0, y: 120, w: 150, h: 64, html: card("Web client", { sign: "screen", sub: "TypeScript" }) },
        { id: "gs", x: 330, y: 78, w: 170, h: 70, html: card("Game server", { sign: "work", sub: "Go · ways in: socket, 18 messages", cls: "on" }) },
        { id: "mm", x: 330, y: 0, w: 170, h: 40, html: card("Matchmaker", { sub: "Go", cls: "" }) },
        { id: "db", x: 700, y: 70, w: 140, h: 60, html: card("Postgres", { sign: "page", sub: "data · 31 tables" }) },
        { id: "push", x: 700, y: 150, w: 140, h: 40, html: card("Push service", { sub: "a queue" }) },
      ], [["ph", "gs", "socket · 18 messages"], ["web", "gs", "socket"], ["mm", "gs", "starts"], ["gs", "db", "SQL"], ["gs", "push", "events", { dash: true }]])
      + at(0, 210, `<p class="mh">Game server's parts <small>opened · its layers · a hotspot is many changes in complex code</small></p>`)
      + at(0, 234, `<div class="mcol" style="gap:8px">`
        + `<div class="mrow"><span class="mnote" style="width:120px;padding-top:8px">Ways in</span>${card("socket handlers", { sub: `churn ${sq("nn...")}` })}${card("HTTP: login", { sub: `churn ${sq("n....")}` })}</div>`
        + `<div class="mrow"><span class="mnote" style="width:120px;padding-top:8px">Rules</span>${card("waves · spawner", { sub: `churn ${sq("aaaaa")}`, cls: "hot", foot: `<small class="warn">31 changes, 4 authors</small>` })}${card("lobby", { sub: `churn ${sq("nn...")}` })}${card("guild", { sub: `churn ${sq("n....")}` })}${card("boss", { sub: `churn ${sq("nnn..")}` })}</div>`
        + `<div class="mrow"><span class="mnote" style="width:120px;padding-top:8px">Data</span>${card("store", { sub: `churn ${sq("nn...")}` })}${card("migrations", { sub: `churn ${sq("n....")}` })}</div></div>`),

    /* Tech · Domain Shaman: bounded contexts, their words, the context map */
    "sh-ddd": () => {
      const reg = (x, y, w, h, name, words, extra = "") => `<div class="region" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px"><span class="mh">${name}</span><div class="chips">${words}</div>${extra}</div>`;
      return reg(0, 0, 300, 180, "Play", chip("wave") + chip("spawner") + chip("round") + chip("boss") + chip("player", "hot"), `<div style="margin-top:10px">${card("Waves", { e: "meadow", sub: "lives here", w: 120 })}</div>`)
        + reg(420, 0, 260, 180, "Guild", chip("guild") + chip("bank") + chip("rank") + chip("member"), `<div style="margin-top:10px">${card("Guild bank", { e: "lava", sub: "lives here", w: 120 })}</div>`)
        + reg(0, 240, 300, 150, "Store", chip("offer") + chip("gem") + chip("receipt"))
        + reg(420, 240, 260, 150, "Identity", chip("player", "hot") + chip("friend") + chip("session"), `<div style="margin-top:10px">${card("Friends list", { e: "void", sub: "lives here", w: 120 })}</div>`)
        + svg(972, 440, `<g style="stroke:var(--ork-edge);stroke-width:1.5;fill:none"><path d="M300 90H420"/><path d="M550 180V240"/><path d="M300 315H420" style="stroke-dasharray:4 3"/><path d="M150 180V240"/></g>`)
        + `<span class="elabel" style="left:360px;top:78px">events: round won</span><span class="elabel" style="left:600px;top:210px">shared kernel: player id</span><span class="elabel" style="left:360px;top:303px">an anti-corruption layer</span><span class="elabel" style="left:150px;top:210px">customer → supplier</span>`
        + at(720, 0, `<div class="mcol" style="width:250px"><p class="mh">The words</p>${card("“player”, two meanings", { cls: "hot", w: 250, sub: "Play: one in a round. Identity: an account. A goal that touches both asks which." })}${card("New word: “raid”", { cls: "ghost", w: 250, sub: "Guild bank's spec says it; no context owns it yet" })}<p class="mnote">A context is a border in the code: a word means one thing inside it. A change that crosses a border is named on the arrow it crosses.</p></div>`);
    },

    /* Tech · Spike Shaman: extreme programming: red, green, refactor, small releases */
    "sh-xp": () => `<div class="mrow" style="height:372px">`
      + lane("Red", card("spawns 3 at wave 2", { e: "meadow", sign: "bug", sub: "fails: got 2", w: 196, cls: "bad" }) + card("boss HP scales by party", { e: "meadow", sub: "written first, no code yet", w: 196, cls: "bad" }), { w: 220, h: 372, hs: "a failing test" })
      + lane("Green", card("wave timer resets", { e: "meadow", sub: "passes · 12 lines", w: 196, cls: "good" }) + card("chat line ≤ 200 chars", { e: "ice", sub: "passes", w: 196, cls: "good" }), { w: 220, h: 372, hs: "passes, as simply as it can" })
      + lane("Refactor", card("spawner: one table, not three ifs", { e: "meadow", sub: "tests stay green", w: 196 }), { w: 220, h: 372, hs: "the same tests, cleaner code" })
      + lane("Released small", card("Lobby chat 0.3", { e: "ice", sub: "6 tests · 1 day", w: 196 }) + card("Waves 0.4", { e: "meadow", sub: "waits for its red", w: 196, cls: "ghost" }), { w: 220, h: 372, hs: "a day's step" })
      + `</div><div class="mfoot"><span><b>412 tests</b> · <span class="no">2 red</span> · run in 38 s</span><span>the last 24 runs ${sq("gggggrgggggggggggggggrrg".replace(/g/g, "g"))}</span><span class="mnote">No code without a test that failed first; a failing test retried once, then asked.</span></div>`,

    /* Tech · Fitness Shaman: evolutionary architecture: the fitness functions every change is checked against */
    "sh-fit": () => {
      const fit = (name, rule, now, trend, cls, mark) => card(name, { w: 300, cls, sub: `${rule} · now <b class="${mark}">${now}</b>`, foot: `<div class="bars" style="height:26px;margin-top:6px">${trend.map(([h, c]) => `<i class="${c || ""}" style="height:${h}px"></i>`).join("")}</div>` });
      const T = (a, hot) => a.map((h, i) => [h, hot && i >= a.length - hot ? "hot" : ""]);
      return `<p class="mh">The fitness functions <small>what the system must keep while it changes; a change is checked against them before it lands</small></p>`
        + `<div style="display:grid;grid-template-columns:repeat(3,300px);gap:12px;margin-top:10px">`
        + fit("Round latency", "p95 under 120 ms", "96 ms", T([10, 12, 11, 14, 13, 12, 15, 14, 16, 15, 17, 16])) + fit("Server start", "under 3 s", "2.4 s", T([9, 9, 10, 10, 11, 10, 12, 12, 12, 13, 13, 14]))
        + fit("Client bundle", "under 4 MB", "4.3 MB", T([14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26], 3), "bad", "no") + fit("Spawner's complexity", "under 15", "19", T([10, 11, 12, 14, 15, 17, 18, 19, 19, 19, 19, 19], 4), "hot", "warn")
        + fit("No client code in the server", "imports: 0", "0", T([2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])) + fit("Migrations reversible", "every one", "12 of 12", T([12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12]))
        + `</div><div class="mfoot"><span>The last 10 changes against them ${sq("ggggggaggr")}</span><span class="mnote">Red: the bundle grew past 4 MB with the boss's art. The leader asks before it lets it land.</span></div>`;
    },

    /* Design · Pixel-Perfect Dryad: Nielsen's heuristics, walked along the screens' flow */
    "dry-heur": () => {
      const scr = (name, rows, on, finds) => `<div class="screen" style="width:150px">${phone(rows, on)}<b>${name}</b><div class="chips" style="justify-content:center">${finds}</div></div>`;
      return `<div class="mrow" style="gap:42px;padding-left:20px;position:relative">`
        + scr("Lobby", ["t", "", "", "", "btn"], false, chip("no findings", "mute"))
        + scr("Party", ["t", "b", "", "btn"], false, chip("1 · status"))
        + scr("Waves", ["t", "b", "b", ""], true, chip("3 · no way out mid-wave", "hot"))
        + scr("Results", ["t", "", "", "btn"], false, chip("9 · no error state", "hot"))
        + scr("Store", ["t", "b", "", "btn"], false, chip("4 · two words for gems"))
        + `</div>` + svg(972, 200, `<g style="stroke:var(--ork-edge);stroke-width:1.5">${[0, 1, 2, 3].map(i => `<path d="M${20 + 150 * (i + 1) + 42 * i - 30} 66H${20 + 150 * (i + 1) + 42 * (i + 1) - 30}"/>`).join("")}</g>`)
        + at(0, 252, `<p class="mh">The ten rules <small>a screen walked against each; a finding pinned to its screen</small></p>`)
        + at(0, 278, `<div class="mrow" style="gap:6px;flex-wrap:wrap;width:972px">${[["1", "visible status", ""], ["2", "the players' words", "good"], ["3", "control and a way out", "hot"], ["4", "consistency", ""], ["5", "prevent errors", "good"], ["6", "recognise, not recall", "good"], ["7", "shortcuts", "mute"], ["8", "minimal", "good"], ["9", "recover from errors", "hot"], ["10", "help", "mute"]].map(([n, t, c]) => card(`${n} · ${t}`, { w: 90, cls: c === "hot" ? "hot" : c === "mute" ? "faint" : "", sub: c === "hot" ? `<span class="warn">a finding</span>` : c === "good" ? `<span class="ok">nothing wrong</span>` : c === "mute" ? "not looked at" : "a note" })).join("")}</div>`);
    },

    /* Design · Diamond Dryad: the Double Diamond: discover, define, develop, deliver */
    "dry-diamond": () => svg(972, 400, `<g style="fill:none;stroke:var(--ork-edge);stroke-width:1.5"><path d="M0 190L240 30L480 190L240 350Z"/><path d="M480 190L720 30L960 190L720 350Z" /></g><path d="M480 190L720 30L960 190L720 350Z" style="fill:var(--ork-ink);opacity:.03"/>`)
      + at(40, 0, `<span class="mh">Discover</span>`, "") + at(320, 0, `<span class="mh">Define</span>`) + at(560, 0, `<span class="mh">Develop</span> <span class="chip">now</span>`) + at(820, 0, `<span class="mh">Deliver</span>`)
      + at(70, 110, `<div class="mcol">${card("5 talks with players", { w: 128, sign: "post" })}${card("the chat's logs", { w: 128 })}${card("store reviews: 212", { w: 128 })}</div>`)
      + at(380, 150, card("“Parties fall apart between waves”", { w: 160, cls: "on", sub: "the problem, in the players' words" }))
      + at(600, 100, `<div class="mcol">${card("A: the party waits", { w: 128, e: "meadow" })}${card("B: a rejoin card", { w: 128, e: "meadow", cls: "on", sub: "the leader's pick" })}${card("C: auto-fill", { w: 128, e: "meadow" })}</div>`)
      + at(850, 160, card("Waves 0.4", { w: 110, e: "meadow", cls: "ghost", sub: "after B is tested" }))
      + `<div class="mfoot"><span>Two diamonds: <b>wide to find, narrow to decide</b>, twice. The leader stays in a phase until its point is reached, and asks before it narrows.</span></div>`,

    /* Design · Atom Dryad: atomic design: tokens, atoms, molecules, organisms, screens */
    "dry-atom": () => {
      const row = (h, sub, inner) => `<div class="mrow" style="align-items:center;min-height:62px"><p class="mh" style="width:130px">${h}<br><small style="margin:0">${sub}</small></p><div class="mrow" style="gap:8px;align-items:center">${inner}</div></div>`;
      const sw = v => `<span style="display:inline-block;width:28px;height:28px;background:var(${v});border:1px solid var(--ork-frame)" title="${v}"></span>`;
      return `<div class="mcol" style="gap:10px">`
        + row("Tokens", "orkUI's", ["--ork-canvas", "--ork-card", "--ork-frame", "--ork-ink", "--ork-action", "--ork-alert", "--ork-danger"].map(sw).join("") + `<span class="chip">Pixelify · Plex</span><span class="chip">0 corner</span>`)
        + row("Atoms", "12", card("button", { w: 88 }) + card("chip", { w: 70 }) + card("head 24", { w: 80 }) + card("element", { w: 80 }) + card("icon", { w: 64 }))
        + row("Molecules", "9", card("party row", { w: 100 }) + card("score pill", { w: 100 }) + card("chat line", { w: 100, e: "ice" }) + card("boss bar", { w: 100, cls: "ghost hot", sub: "<span class=warn>new: asked</span>" }))
        + row("Organisms", "5", card("lobby list", { w: 120 }) + card("wave HUD", { w: 120, e: "meadow" }) + card("store shelf", { w: 120 }))
        + row("Screens", "5", card("Lobby", { w: 100, sign: "screen" }) + card("Waves", { w: 100, sign: "screen", e: "meadow" }) + card("Results", { w: 100, sign: "screen" }))
        + `</div><div class="mfoot"><span>Built up from the tokens: <b>a new part is asked</b>, the rest decided from the parts there are. The boss bar waits for your yes.</span></div>`;
    },

    /* Design · Sprint Dryad: the design sprint, five days */
    "dry-sprint": () => `<div class="mrow" style="height:372px">`
      + lane("Mon · Map", `<div class="mcol">${card("the flow, Lobby → Results", { w: 150 })}${card("the target: rejoin after a wave", { w: 150, cls: "on" })}</div>`, { w: 178, h: 372 })
      + lane("Tue · Sketch", `<div class="mrow" style="flex-wrap:wrap;gap:6px">${phone(["t", "b", "btn"])}${phone(["t", "", "b"])}</div>`, { w: 178, h: 372 })
      + lane("Wed · Decide", `${card("storyboard: the rejoin card", { w: 150, foot: `<small>votes ${sq("nnnnn")}</small>` })}${card("the waiting room", { w: 150, foot: `<small>votes ${sq("nn")}</small>`, cls: "faint" })}`, { w: 178, h: 372 })
      + lane("Thu · Prototype", card("rejoin card, clickable", { w: 150, e: "meadow", sign: "screen", sub: "today" }), { w: 178, h: 372, cls: "now", hs: "today" })
      + lane("Fri · Test", `${card("5 players", { w: 150, sub: "tomorrow", foot: `<small>${sq(".....")}</small>`, cls: "ghost" })}`, { w: 178, h: 372 })
      + `</div><div class="mfoot"><span>A question answered in five days, <b>a day a step</b>; Friday's five talks decide what is built.</span></div>`,

    /* Product · Angel Invest Knight: the opportunity solution tree */
    "uni-ost": () => graph(972, 400, [
        { id: "o", x: 361, y: 0, w: 250, h: 58, html: card("Day-7 return: 18% → 25%", { cls: "on big", sub: "the outcome" }) },
        { id: "p1", x: 40, y: 110, w: 220, h: 58, html: card("Friends drift apart after a round", { sub: "an opportunity · 4 talks" }) },
        { id: "p2", x: 376, y: 110, w: 220, h: 58, html: card("New players lose in wave 1", { sub: "an opportunity · the data" }) },
        { id: "p3", x: 712, y: 110, w: 220, h: 58, html: card("Nothing to come back for tomorrow", { sub: "an opportunity" }) },
        { id: "s1", x: 0, y: 220, w: 140, h: 58, html: card("Party stays together", { e: "meadow", sub: "Waves" }) },
        { id: "s2", x: 160, y: 220, w: 140, h: 58, html: card("Friends list", { e: "void" }) },
        { id: "s3", x: 416, y: 220, w: 140, h: 58, html: card("A gentler wave 1", { cls: "ghost" }) },
        { id: "s4", x: 672, y: 220, w: 140, h: 58, html: card("Daily quest", { e: "dust" }) },
        { id: "s5", x: 832, y: 220, w: 140, h: 58, html: card("Guild bank", { e: "lava" }) },
        { id: "x1", x: 0, y: 330, w: 140, h: 50, html: card("Ask 5 players", { sign: "post", sub: "done", cls: "good" }) },
        { id: "x3", x: 416, y: 330, w: 140, h: 50, html: card("A/B: wave 1 at 80% HP", { sign: "abtest", sub: "6 days left" }) },
        { id: "x4", x: 672, y: 330, w: 140, h: 50, html: card("A fake door", { sign: "flask", sub: "312 of 500 seen" }) },
      ], [["o", "p1"], ["o", "p2"], ["o", "p3"], ["p1", "s1"], ["p1", "s2"], ["p2", "s3"], ["p3", "s4"], ["p3", "s5"], ["s1", "x1"], ["s3", "x3"], ["s4", "x4"]]),

    /* Product · Jobwise Knight: jobs to be done */
    "uni-jtbd": () => card("“When my friends are online after work, I want to drop into a quick round together, so I can unwind with them.”", { cls: "on big", w: 972, sub: "the job · heard in 6 of 8 talks", style: "min-height:0" })
      + `<div class="mrow" style="margin-top:14px">`
      + lane("Struggles", `${card("waiting for the party to fill", { w: 210, sub: "on Lobby" })}${card("lost the party after a wave", { w: 210, sub: "on Waves", cls: "hot" })}${card("no idea who is online", { w: 210, sub: "on Friends" })}`, { w: 234, h: 300, hs: "pinned to screens" })
      + lane("Hired instead", `${card("a group chat, then another game", { w: 210 })}${card("a quick match with strangers", { w: 210 })}`, { w: 234, h: 300, hs: "what we compete with" })
      + lane("Our goals", `${card("Waves: the party stays", { e: "meadow", w: 210 })}${card("Lobby chat", { e: "ice", w: 210 })}${card("Friends list", { e: "void", w: 210 })}`, { w: 234, h: 300, hs: "a job each" })
      + lane("Forces", `<div class="mcol" style="gap:10px"><span>push of the old way ${meter(.7)}</span><span>pull of ours ${meter(.55)}</span><span>anxiety: will they come? ${meter(.6, "hot")}</span><span>habit: the group chat ${meter(.8)}</span></div>`, { w: 234, h: 300, hs: "what moves them" })
      + `</div>`,

    /* Product · Pivot Knight: the Lean Startup's build, measure, learn */
    "uni-lean": () => `<div class="mrow" style="height:330px">`
      + lane("Believe", `${card("Players come back for a daily quest", { w: 196, e: "dust" })}${card("Guilds make players pay", { w: 196, e: "lava" })}`, { w: 220, h: 330, hs: "a hypothesis a card" })
      + lane("Testing", `${card("A fake door: daily quest", { w: 196, e: "dust", sign: "flask", sub: "312 of 500 seen · 9% press", foot: meter(.62) })}${card("Wave 1 at 80% HP", { w: 196, sign: "abtest", sub: "6 days left", foot: meter(.4) })}`, { w: 220, h: 330, hs: "the smallest test" })
      + lane("Learned", `${card("A gentler wave 1 keeps new players", { w: 196, cls: "good", sub: "<span class=ok>+6 points: true</span>" })}${card("Chat stickers sell", { w: 196, cls: "bad", sub: "<span class=no>0.3%: false</span>" })}`, { w: 220, h: 330, hs: "true or false" })
      + lane("Decide", `${card("Persevere", { w: 196, cls: "on", sub: "the return grows 2 points a week" })}${card("Pivot: a guild game", { w: 196, cls: "ghost", sub: "if the daily quest stays under 10%" })}`, { w: 220, h: 330 })
      + `</div><div class="mfoot"><span>The one number: <b>Day-7 return 18%</b></span><span class="mnote">Every goal is a bet with a test; a bet that fails asks you: persevere or pivot.</span></div>`,

    /* Product · Appetite Knight: Shape Up: pitches, the betting table, the hill */
    "uni-shape": () => `<div class="mrow" style="height:250px">`
      + lane("Pitches", `${card("Party stays", { e: "meadow", w: 170, sub: "appetite: 2 weeks" })}${card("Guild bank", { e: "lava", w: 170, sub: "appetite: 6 weeks" })}${card("Daily quest", { e: "dust", w: 170, sub: "appetite: 2 weeks" })}`, { w: 194, h: 250, hs: "shaped" })
      + lane("Bet this cycle", `${card("Party stays", { e: "meadow", w: 170, cls: "on", sub: "week 3 of 6" })}`, { w: 194, h: 250 })
      + lane("Not now", `${card("Guild bank", { e: "lava", w: 170, cls: "faint", sub: "no backlog: pitched again" })}`, { w: 194, h: 250 })
      + `<div class="mcol" style="width:360px"><p class="mh">The hill <small>figuring it out ↗ · making it happen ↘</small></p><div style="position:relative;height:160px">`
      + svg(360, 150, `<path d="M0 140C90 140 110 20 180 20S270 140 360 140" style="fill:none;stroke:var(--ork-edge);stroke-width:1.5"/><path d="M180 10V146" style="stroke:var(--ork-frame);stroke-dasharray:3 3"/><g style="fill:var(--ork-ink)"><rect x="232" y="44" width="8" height="8"/><rect x="292" y="104" width="8" height="8"/></g><rect x="60" y="92" width="8" height="8" style="fill:var(--ork-alert)"/>`)
      + `<span class="slab" style="left:0;top:110px">boss HP <span class="warn">stuck</span></span><span class="slab" style="left:210px;top:24px">spawner</span><span class="slab" style="left:286px;top:118px">timer</span></div></div>`
      + `</div><div class="mfoot"><span><b>The appetite is fixed, the scope moves</b>: a bet that runs out of time stops, it is not stretched.</span><span>Cycle: week 3 of 6, then two weeks of cool-down</span></div>`,

    /* Run · Uptime Imp: SLOs and error budgets */
    "imp-slo": () => {
      const svc = (n, slo, left, cls) => card(n, { w: 228, cls, sub: `SLO: ${slo}`, foot: `<small>budget left: <b class="${cls === "hot" ? "warn" : ""}">${Math.round(left * 100)}%</b></small>${meter(left, cls)}` });
      return `<div class="mrow">${svc("Game server", "99.5% of rounds start", .62)}${svc("Matchmaker", "95% matched in 10 s", .18, "hot")}${svc("Login", "99.9% succeed", .91)}${svc("Store", "99% of receipts", 1)}</div>`
        + `<p class="mh" style="margin-top:22px">The month's budget, burned a day <small>the Matchmaker's</small></p>`
        + `<div class="bars" style="height:130px;margin-top:10px">${[3, 2, 4, 3, 2, 5, 3, 2, 2, 4, 3, 6, 9, 14, 18, 12, 6, 4, 3].map((h, i) => `<i class="${h > 8 ? "hot" : ""}" style="height:${h * 6}px;width:22px"></i>`).join("")}${Array(11).fill(0).map(() => `<i class="lo" style="height:2px;width:22px"></i>`).join("")}</div>`
        + `<div class="mfoot"><span>Quiet until a budget burns <b>twice as fast</b> as the month allows; then it asks to slow the releases.</span></div>`;
    },

    /* Run · Lantern Imp: observability first: a trace read before a fix */
    "imp-obs": () => {
      const x = ms => Math.round(ms / 1900 * 640) + 160;
      const span = (y, a, b, name, cls = "") => `<span class="slab" style="left:0;top:${y - 1}px;width:150px">${name}</span><span class="span ${cls}" style="left:${x(a)}px;top:${y}px;width:${Math.max(3, x(b) - x(a))}px"></span><span class="slab" style="left:${x(b) + 6}px;top:${y - 1}px;color:var(--ork-ink-faint)">${b - a} ms</span>`;
      return `<p class="mh">A trace: join a party <small>1 840 ms · slow · 10% of requests traced, every error</small></p><div style="position:relative;height:190px;margin-top:12px">`
        + span(0, 0, 40, "phone client · tap") + span(26, 40, 90, "gateway") + span(52, 90, 1600, "matchmaker · find", "hot") + span(78, 120, 1500, "  postgres · parties by rank", "hot") + span(104, 1600, 1810, "game server · seat") + span(130, 1810, 1840, "phone client · show", "lo")
        + `<span class="slab" style="left:160px;top:160px;color:var(--ork-ink-faint)">0</span><span class="slab" style="left:790px;top:160px;color:var(--ork-ink-faint)">1.9 s</span></div>`
        + `<div class="mrow" style="margin-top:10px">${card("parties by rank: no index", { w: 300, cls: "hot", sign: "bug", sub: "1 380 ms of the 1 840; a goal made from it" })}${card("the logs at that moment", { w: 300, sub: "<code>seq scan on parties (rows 48 211)</code>" })}${card("the slowest five today", { w: 300, sub: `join party ${sq("aaann")}` })}</div>`
        + `<div class="mfoot"><span><b>Read the trace before the fix</b>: a goal of Run's starts from the span that took the time.</span></div>`;
    },

    /* Marketing · Growth Hack Gnome: AARRR, the funnel */
    "fairy-aarrr": () => {
      const step = (n, what, w, num, goal, cls) => `<div class="mrow" style="align-items:center;height:62px"><p class="mh" style="width:130px">${n}</p><div style="width:520px;display:flex;justify-content:center"><div style="width:${w}px;height:44px;background:${cls ? "var(--ork-alert)" : "var(--ork-ink-muted)"};opacity:${cls ? .9 : .35}"></div></div><div style="width:150px;padding-left:16px"><b>${num}</b><br><span class="mnote">${what}</span></div>${goal}</div>`;
      return step("Acquisition", "installs a month", 520, "12 400", "") + step("Activation", "finish wave 1", 400, "41%", card("A gentler wave 1", { w: 130, cls: "ghost" }))
        + step("Retention", "back on day 7", 230, "18% · the leak", card("Waves: party stays", { e: "meadow", w: 130 }), true) + step("Referral", "invite a friend", 120, "6%", card("Friends list", { e: "void", w: 130 }))
        + step("Revenue", "pay", 60, "2.1%", card("Guild bank", { e: "lava", w: 130 }))
        + `<div class="mfoot"><span>A step a number; <b>the leak is worked first</b>, a goal pinned to the step it moves.</span></div>`;
    },

    /* Marketing · Store Gnome: the store page first */
    "fairy-aso": () => `<div class="mrow" style="gap:16px"><div style="width:72px;height:72px;border:2px solid var(--ork-edge);display:grid;place-items:center"><img class="hd" src="${RACE("peon-warrior")}" width="48" height="44" alt=""></div>`
      + `<div class="mcol" style="gap:4px"><p style="font:600 18px/22px var(--ork-font-read);color:var(--ork-ink)">Guild Waves: Party Brawler <span class="chip">27 / 30</span></p><p>Quick rounds with your friends <span class="chip hot">30 / 30 · full</span></p><p class="mnote">★ 4.3 · 212 reviews · “parties fall apart” in 31 of them</p></div></div>`
      + `<p class="mh" style="margin-top:16px">The shots <small>the first two decide</small></p><div class="mrow" style="margin-top:8px;gap:10px">${["Waves", "Party", "Boss", "Guild", "Chat"].map((n, i) => `<div class="screen">${phone(i === 0 ? ["t", "b", "b", ""] : i === 1 ? ["t", "", "", "btn"] : ["t", "b", ""], i < 2)}<b>${n}</b></div>`).join("")}`
      + `<div class="mcol" style="margin-left:20px;width:300px">${card("A/B: Waves first, or Party first", { w: 300, sign: "abtest", sub: "52% · 48% of installs · 6 days left", foot: meter(.52) })}<p class="mh" style="margin-top:6px">Keywords</p><div class="chips">${chip("party #8")}${chip("co-op #14")}${chip("waves #3", "good")}${chip("guild #22")}${chip("friends #41", "hot")}</div></div></div>`
      + `<div class="mfoot"><span><b>The store page before anyone comes</b>: a title in its limit, the first shots tested, the words people search.</span></div>`,

    /* Release · Release Night King: dev against main, and the version it would be */
    release: () => `<div class="mrow" style="height:300px">`
      + lane("In dev, not in main", `${card("Lobby chat 0.3", { e: "ice", w: 200, cls: "good", sub: "<span class=ok>✓ the gate green</span>" })}${card("Waves: wave timer", { e: "meadow", w: 200, cls: "good", sub: "<span class=ok>✓ the gate green</span>" })}${card("Waves: spawner", { e: "meadow", w: 200, cls: "bad", sub: "<span class=no>✗ 2 tests red</span>: not ready" })}`, { w: 226, h: 300, hs: "ticked: ready" })
      + lane("The next version", `${card("1.4.0", { w: 200, cls: "on big", sub: "minor: new things, nothing broken" })}<p class="mnote">A fix alone would be 1.3.1; a broken save would be 2.0.0.</p>`, { w: 226, h: 300 })
      + lane("Since 1.3, in main", `${card("Friends list", { e: "void", w: 200, cls: "faint" })}${card("Fix: the login loop", { e: "void", w: 200, cls: "faint" })}`, { w: 226, h: 300, style: "opacity:.8" })
      + `<div class="mcol" style="width:250px;gap:10px"><p class="mh">Readiness</p>${["the gate green", "a changelog line each", "a way back: 1.3 kept"].map((t, i) => `<span>${i === 1 ? `<span class="warn">◻</span>` : `<span class="ok">✓</span>`} ${t}</span>`).join("")}<p class="mh" style="margin-top:12px">DORA's keys</p><span>deploys: <b>3 a week</b></span><span>lead time: <b>2 days</b></span><span>changes that failed: <b>1 of 12</b></span></div>`
      + `</div><div class="mfoot"><span>Main is yours: the portal opens on what is ready; <b>Release asks, always</b>.</span></div>`,
  };

  /* ---------------- who: the eighteen, in their crafts' order ---------------- */
  const LIST = [
    ["keeper", "Guild app", "felt", "the Board: a lane a party, the goals in line in the first"],
    ["uni-ost", "Product", "contours", "an outcome, its opportunities, their solutions and the experiments under them, a tree"],
    ["uni-jtbd", "Product", "contours", "the job in the players' words, its struggles pinned to screens, what they hire instead"],
    ["uni-lean", "Product", "contours", "hypotheses through a test to true or false, then persevere or pivot"],
    ["uni-shape", "Product", "contours", "pitches with an appetite, the bet of the cycle and its hill"],
    ["dry-heur", "Design", "dots", "the screens along the flow, each walked against the ten rules"],
    ["dry-diamond", "Design", "dots", "two diamonds: discover and define, develop and deliver"],
    ["dry-atom", "Design", "dots", "tokens up to screens: the parts there are and the one asked"],
    ["dry-sprint", "Design", "dots", "five days: map, sketch, decide, prototype, test"],
    ["sh-c4", "Tech", "grid", "the containers and their named links, the opened one's parts with their hotspots"],
    ["sh-ddd", "Tech", "grid", "the bounded contexts, their words, the arrows between them"],
    ["sh-xp", "Tech", "grid", "red, green, refactor, released small, and the tests' runs"],
    ["sh-fit", "Tech", "grid", "the fitness functions every change is checked against"],
    ["release", "Release", "stones", "dev against main, the next version's number and DORA's keys"],
    ["imp-slo", "Run", "stripes", "the services' objectives and the budgets they burn"],
    ["imp-obs", "Run", "stripes", "a slow request's trace, span by span, before the fix"],
    ["fairy-aarrr", "Marketing", "chevrons", "the funnel, a number a step, the leak first"],
    ["fairy-aso", "Marketing", "chevrons", "the store page: the title in its limit, the shots tested, the words people search"],
  ];
  const headOf = id => id === "keeper" ? RACE("peon-crown") : id === "release" ? RACE("lich-elder") : HIMG(id);
  const nameOf = id => id === "keeper" ? "Orkmaster" : id === "release" ? "Release Night King" : HEROES[id].name;
  const schoolOf = id => id === "keeper" ? "the whole project" : id === "release" ? "DORA's keys, readiness and semver" : HEROES[id].school;
  function figure([id, craft, tex, lays], i) {
    return `<figure class="tfig" id="t-${id}" style="margin:0"><div class="tfig__top"><span class="tfig__n">${String(i + 1).padStart(2, "0")}</span>
      <div class="chair on"><span class="chair__seat"><span class="ork-chair big"></span><img class="hd" src="${headOf(id)}" alt=""></span>${craft}</div>
      <div class="tfig__who"><b>${nameOf(id)}</b><span>${schoolOf(id)}</span></div><p class="tfig__lays">Lays its table as ${lays}.</p></div>
      <div class="table ork-table" data-tex="${tex}"><div class="table__head"><b>${id === "keeper" ? "The whole project" : craft + "'s table"}</b> · through ${id === "keeper" ? "the Orkmaster" : nameOf(id)}</div>${map(id)}</div></figure>`;
  }
  function map(id) { return `<div class="map">${MAPS[id]()}</div>`; }
  window.TABLES = {
    list: LIST, map,
    gallery() {
      return `<nav class="tindex">${LIST.map(([id, craft]) => `<a href="#t-${id}"><img class="hd" src="${headOf(id)}" alt="">${nameOf(id)}<span style="color:var(--ork-ink-faint)">· ${craft}</span></a>`).join("")}</nav>`
        + `<div class="tables">${LIST.map(figure).join("")}</div>`;
    },
  };
})();
