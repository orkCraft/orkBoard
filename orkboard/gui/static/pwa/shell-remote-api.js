// GitHub's REST API, as much of it as the phone needs and no library (docs/specs/136 C, decisions §243): the repository's check, the journal's `status.json` read with its ETag, and
// the inbox's files written one by one on `orkboard/inbox`. The token goes to `https://api.github.com` in an Authorization header and nowhere else. Every failure is a `RemoteError`
// with a `kind` the caller can act on: `token` (401), `limit` (a 403 or 429 with no calls left, `until` the ms when they come back), `network`, `missing` (404), `conflict` (409),
// `invalid` (422), `forbidden` (another 403), `refused` (the rest).

export const API = "https://api.github.com";
export const JOURNAL = "orkboard/journal";
export const INBOX = "orkboard/inbox";
export const EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904";     // git's empty tree: the root of a branch that shares no history with the code
export const RETRIES = 3;                                                  // a 409 (the branch moved under the write) is tried this often

export class RemoteError extends Error {
  constructor(kind, message, extra = {}) { super(message); this.name = "RemoteError"; this.kind = kind; Object.assign(this, extra); }
}

/** `owner/name` or "" (a GitHub address and a trailing .git are taken as what they name). */
export function cleanRepo(text) {
  const t = String(text || "").trim().replace(/^(?:https?:\/\/|git@)?(?:www\.)?github\.com[\/:]/i, "").replace(/\.git$/i, "").replace(/\/+$/, "");
  return /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(t) ? t : "";
}

const safe = (text) => { try { return JSON.parse(text); } catch { return null; } };
const b64 = (text) => { let s = ""; for (const b of new TextEncoder().encode(text)) s += String.fromCharCode(b); return btoa(s); };
const unb64 = (text) => new TextDecoder().decode(Uint8Array.from(atob(String(text).replace(/\s/g, "")), (c) => c.charCodeAt(0)));
const path = (p) => p.split("/").map(encodeURIComponent).join("/");

/** A client for one repository. `fetch`, `now` and `sleep` are given so a test needs no network and no wait. */
export function client({ fetch: fetcher = globalThis.fetch?.bind(globalThis), repo, token, now = Date.now, sleep = (ms) => new Promise((r) => setTimeout(r, ms)) }) {
  const base = `${API}/repos/${repo}`;
  let branch = false;                                // the inbox branch is known to exist (this run)

  /** One call: `{status, etag, body}`; the statuses in `allow` come back, every other failure is thrown. */
  async function call(method, url, { body, headers = {}, allow = [] } = {}) {
    let r;
    try {
      r = await fetcher(base + url, {
        method, cache: "no-store",
        headers: { Accept: "application/vnd.github+json", Authorization: `Bearer ${token}`, "X-GitHub-Api-Version": "2022-11-28", ...(body ? { "Content-Type": "application/json" } : {}), ...headers },
        ...(body ? { body: JSON.stringify(body) } : {}),
      });
    } catch (e) {
      throw new RemoteError("network", "Could not reach GitHub", { cause: e });
    }
    const head = (k) => r.headers?.get?.(k) ?? null;
    if (r.ok || allow.includes(r.status)) {
      const text = r.status === 304 || r.status === 204 ? "" : await r.text();
      return { status: r.status, etag: head("etag") || "", body: text };
    }
    const said = safe(await r.text().catch(() => "")), words = (said && said.message) || `GitHub answered ${r.status}`;
    if (r.status === 401) throw new RemoteError("token", words, { status: 401 });
    if ((r.status === 403 || r.status === 429) && (head("x-ratelimit-remaining") === "0" || r.status === 429 || head("retry-after"))) {
      const reset = Number(head("x-ratelimit-reset")), after = Number(head("retry-after"));
      throw new RemoteError("limit", words, { status: r.status, until: reset ? reset * 1000 : now() + (after || 60) * 1000 });
    }
    throw new RemoteError({ 403: "forbidden", 404: "missing", 409: "conflict", 422: "invalid" }[r.status] || "refused", words, { status: r.status });
  }
  const json = (r) => safe(r.body);

  return {
    /** `{private, push, name}` of the repository, or throws (`missing`: no such repository, or the token cannot see it). */
    async info() {
      const body = json(await call("GET", "")) || {};
      return { private: body.private === true, push: body.permissions?.push === true, name: String(body.full_name || repo) };
    },

    /** `status.json` of the journal branch, asked with the ETag last given: `{changed: false}` (304), `{missing: true}` (no journal yet), else `{changed: true, etag, data}`. */
    async journal(etag = "") {
      const r = await call("GET", `/contents/status.json?ref=${encodeURIComponent(JOURNAL)}`,
        { headers: { Accept: "application/vnd.github.raw+json", ...(etag ? { "If-None-Match": etag } : {}) }, allow: [304, 404] });
      if (r.status === 304) return { changed: false };
      if (r.status === 404) return { missing: true };
      let data = json(r);
      if (data && typeof data.content === "string" && data.encoding === "base64") data = safe(unb64(data.content));      // the JSON form of the contents' answer
      return { changed: true, etag: r.etag, data: data && typeof data === "object" && !Array.isArray(data) ? data : null };
    },

    /** The inbox branch exists, made on the first goal from an empty tree's commit (no history shared with the code). */
    async ensureBranch() {
      if (branch) return;
      if ((await call("GET", `/git/ref/heads/${path(INBOX)}`, { allow: [404] })).status !== 404) { branch = true; return; }
      const message = "orkboard/inbox: goals from the phone";
      let commit;
      try {
        commit = json(await call("POST", "/git/commits", { body: { message, tree: EMPTY_TREE, parents: [] } }));
      } catch (e) {
        if (e.kind !== "invalid" && e.kind !== "missing") throw e;                      // this repository has no empty tree yet: a tree of one line is as good
        const tree = json(await call("POST", "/git/trees", { body: { tree: [{ path: "README.md", mode: "100644", type: "blob", content: "Goals dropped by a phone: one file a goal, read by Orkboard.\n" }] } }));
        commit = json(await call("POST", "/git/commits", { body: { message, tree: tree?.sha, parents: [] } }));
      }
      try {
        await call("POST", "/git/refs", { body: { ref: `refs/heads/${INBOX}`, sha: commit?.sha } });
      } catch (e) {
        if (e.kind !== "invalid") throw e;                                            // "Reference already exists": another made it first
      }
      branch = true;
    },

    /** Adds the file `file` (`inbox/<device>/<id>.json`) to the inbox, with `text` or `base64`. Never edits: a file that is there is the same one sent twice (`{existed: true}`). */
    async add(file, { text = "", base64 = "" }, message = "orkboard/inbox: from the phone") {
      await this.ensureBranch();
      const content = base64 || b64(text);
      for (let i = 0; ; i++) {
        try {
          await call("PUT", `/contents/${path(file)}`, { body: { message, content, branch: INBOX } });
          return { existed: false };
        } catch (e) {
          if (e.kind === "invalid" && /sha/i.test(e.message)) return { existed: true };
          if (e.kind === "missing" && /branch/i.test(e.message) && i < RETRIES) { branch = false; await this.ensureBranch(); continue; }
          if (e.kind === "conflict" && i < RETRIES - 1) { await sleep(300 * (i + 1)); continue; }
          throw e;
        }
      }
    },
  };
}
