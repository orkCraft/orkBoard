// Canvases on the phone (docs/specs/78-canvases.md §4; decisions §93): what an AI tool drew outside the code (a page, a design, a deck, a document, a picture), one line each,
// in a fold row at the foot of the board, above what waits for you: *Canvases · n*, folded at first, there only when there are canvases. A line: the head of design's race (the elf, small),
// the kind in the pixel face's small caps, the title in the text face (what a person or an agent wrote is never in the pixel face), and under them the tool and what a tap does. A tap opens its link
// in the phone's browser (only an allowed host's: any other host is shown as text, never a link), or shows its picture in a sheet. A page (HTML, Markdown) is never shown on the phone: its line
// has no tap beyond its link. *Seen* folds a line away (`ideas.canvas_seen`). It reads `ideas.canvases` when the snapshot's `canvases_rev` moves; a canvas is not a signal: no alert colour, no count elsewhere.
import { h, sheet } from "./util.js";
import { whoHead } from "./shell-who.js";

const KINDS = { design: "Design", slides: "Slides", document: "Document", page: "Page", picture: "Picture" };
const PICTURE = /^image\/(png|jpeg|gif|webp)$/;          // the only mimes a picture is drawn from (never a page's: the phone shows no local page)
const HOSTS = { "claude.ai": "Open on claude.ai", "figma.com": "Open in Figma", "tldraw.com": "Open on tldraw.com", "canva.com": "Open on canva.com" };

/** What a line offers, in words: the link's host, a picture to show, or nothing. */
export const offerOf = (c) => (c.url ? HOSTS[c.host] || `Open on ${c.host}` : c.kind === "picture" && c.local ? "Show picture" : "");

/** `core`: the board's frame (`call`, `st`). Returns {el, sheets, render(snapshot)}. */
export function makeCanvases(core) {
  let cards = [], seen = [], open = false, project;
  let rev, read = false, loading = false, again = false;
  const quiet = () => {};                                // a host that has no canvases says so with an error: no toast for that
  const word = h("span", { class: "gfold__word" }, "Canvases"), n = h("span", { class: "gfold__n" });
  const chev = h("i", { class: "ork-chev right", "aria-hidden": "true" });
  const head = h("button", { class: "gfold__head", type: "button", "aria-expanded": "false", onclick: () => { open = !open; draw(); } }, chev, word, n);
  const list = h("div", { class: "cv-list" });
  const el = h("section", { class: "cv", "aria-label": "Canvases", "data-fold": "canvases", hidden: true }, h("div", { class: "gfold" }, head), list);

  // -- a picture, in a sheet ------------------------------------------------------------------------------------------------------
  const pic = h("img", { class: "cv-pic", alt: "" });
  const cap = h("p", { class: "cv-pic__title" });
  const view = sheet("Picture", pic, cap);

  async function show(c) {
    const got = await core.call("ideas.canvas_file", { key: c.key });
    if (!got) return;
    if (!got.data || !PICTURE.test(got.mime || "")) { core.flash("This canvas has no picture to show here"); return; }
    pic.src = `data:${got.mime};base64,${got.data}`;
    pic.alt = c.title;
    cap.textContent = c.title;
    view.open();
  }

  async function markSeen(c) {
    const got = await core.call("ideas.canvas_seen", { key: c.key });
    if (got) load();
  }

  // -- the lines -------------------------------------------------------------------------------------------------------------------
  function line(c, fresh) {
    const offer = offerOf(c);
    const body = [h("span", { class: "cv__top" }, whoHead(c.head, true), h("span", { class: "cv__kind" }, KINDS[c.kind] || c.kind), h("span", { class: "cv__title" }, c.title)),
      h("span", { class: "cv__sub muted" }, c.tool_word, offer ? ` · ${offer}` : "", c.link_text ? ` · ${c.link_text}` : "")];       // another host's link is text
    const main = c.url ? h("a", { class: "cv__main", href: c.url, target: "_blank", rel: "noopener noreferrer", "data-act": "open" }, ...body)
      : offer ? h("button", { class: "cv__main", type: "button", "data-act": "show", onclick: () => show(c) }, ...body)
        : h("div", { class: "cv__main is-still" }, ...body);
    return h("div", { class: `cv__line${fresh ? "" : " is-seen"}`, "data-key": c.key },
      main, fresh ? h("button", { class: "ork-btn cv__seen", type: "button", "data-act": "seen", "aria-label": `Seen: ${c.title}`, onclick: () => markSeen(c) }, "Seen") : null);
  }

  function draw() {
    const any = cards.length + seen.length > 0;
    el.hidden = !any;
    n.textContent = `· ${cards.length}`;
    head.setAttribute("aria-expanded", String(open));
    head.setAttribute("aria-label", `Canvases ${cards.length}`);
    chev.className = open ? "ork-chev" : "ork-chev right";
    list.hidden = !open;
    el.classList.toggle("is-open", open);
    if (!open) { list.replaceChildren(); return; }
    list.replaceChildren(...cards.map((c) => line(c, true)),
      ...(cards.length ? [] : [h("p", { class: "muted cv__none" }, "All seen.")]),
      ...(seen.length ? [h("h3", {}, "Seen"), ...seen.map((c) => line(c, false))] : []));
  }

  /** Reads the cards; once more when the snapshot said they changed meanwhile. */
  async function load() {
    if (loading) { again = true; return; }
    loading = true;
    try {
      const got = await core.call("ideas.canvases", {}, quiet);
      if (got) { cards = got.canvases || []; seen = got.seen || []; read = true; draw(); }
    } finally {
      loading = false;
      if (again) { again = false; load(); }
    }
  }

  draw();
  return {
    el,
    sheets: [view.el],
    render(s) {
      if (s.project !== project) { project = s.project; cards = []; seen = []; read = false; open = false; draw(); }
      if (read && s.canvases_rev === rev) return;
      rev = s.canvases_rev;
      load();
    },
  };
}
