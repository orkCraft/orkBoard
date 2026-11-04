// The repository and its token, as the phone's Settings draws them (docs/specs/136 C.1–C.2): the frame mounts this node before pairing, the page in the crown's menu
// (js/hand/upphone.js, through `globalThis.orkboardPhone.remote.settingsNode()`). Plain DOM, no library: it is drawn by the frame, which imports none of the page's.
// The two lines of §243.7 are said under the fields word for word; the token is typed into a password field, never shown again, and *Remove* forgets it at once.
import { TOKEN_CAN, TOKEN_KEPT, READY } from "./shell-remote-words.js";

const h = (tag, attrs = {}, ...kids) => {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) el.append(kid);
  return el;
};

let nth = 0;

/** The settings node for `remote` (shell-remote.js); it follows the remote while it is in the page. */
export function settingsNode(remote) {
  const id = `remote-${++nth}`;
  const repo = h("input", { class: "ork-field", id: `${id}-repo`, name: "repo", type: "text", inputmode: "url", autocapitalize: "off", autocorrect: "off", spellcheck: "false", autocomplete: "off", placeholder: "owner/name" });
  const token = h("input", { class: "ork-field", id: `${id}-token`, name: "token", type: "password", autocapitalize: "off", autocorrect: "off", spellcheck: "false", autocomplete: "off" });
  const line = h("p", { class: "remote-line", role: "status" });
  const save = h("button", { class: "ork-btn primary", type: "button" }, "Check and keep");
  const remove = h("button", { class: "ork-btn", type: "button" }, "Remove");
  let touched = false;
  repo.addEventListener("input", () => { touched = true; });
  const say = (text, bad = false) => { line.textContent = text; line.className = `remote-line${bad ? " is-bad" : ""}`; };

  const show = () => {
    const s = remote.settings();
    if (!touched) repo.value = s.repo;                    // what the person typed stays; the field follows the settings until then
    token.placeholder = s.token ? "Kept: paste a new one to replace it" : "Paste the token";
    remove.hidden = !s.token;
    const held = remote.line();
    if (held) say(held, true);
    else if (s.token && !line.textContent) say(READY);
  };
  save.addEventListener("click", async () => {
    save.disabled = true;
    say("Checking…");
    const r = await remote.save({ repo: repo.value, token: token.value });
    save.disabled = false;
    say(r.line, !r.ok);
    if (r.ok) { token.value = ""; touched = false; }
    show();
  });
  remove.addEventListener("click", () => { remote.forget(); token.value = ""; say("The token is gone from this phone"); show(); });

  const node = h("section", { class: "remote-settings", "aria-label": "Your repository" },
    h("label", { for: `${id}-repo`, class: "remote-label" }, "Repository"), repo,
    h("label", { for: `${id}-token`, class: "remote-label" }, "Token"), token,
    h("p", { class: "remote-say" }, TOKEN_CAN),
    h("p", { class: "remote-say" }, TOKEN_KEPT),
    h("div", { class: "remote-row" }, save, remove), line);
  show();
  let seen = false;
  const off = remote.subscribe(() => {          // follows the remote while the node is in the page; let go once it was taken out
    if (node.isConnected) { seen = true; show(); } else if (seen) off();
  });
  return node;
}
