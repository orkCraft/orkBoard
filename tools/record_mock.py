"""Record the page's mock (goal 170, stage M): run `orkboard --serve <folder>`, open the page in a browser, keep what crosses
its socket (the snapshot, every command the page sends and the host's reply), walk the leaders' tabs, and write it to
`orkboard/gui/static/mock/board.json`, which `?mock=1` replays with no host (js/mock/mocklink.js). A camera on a real host,
not a test.

    uv run --with playwright python tools/record_mock.py [folder]

Paths under the home folder are written as `~`; the snapshot is checked for anything like a key before it is written.
"""
import json, os, re, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FOLDER = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT).resolve()
OUT = ROOT / "orkboard/gui/static/mock/board.json"
EXTRA = [["ideas.feed", {}], ["ideas.recap", {"since": ""}], ["ideas.turns", {}], ["ideas.verdicts", {}], ["ideas.tables", {}], ["ideas.ask_cost", {}]]
SPY = """(() => {
  const Real = window.WebSocket; window.__mock = { state: null, replies: [], sent: {} };
  window.WebSocket = function (url, p) {
    const ws = new Real(url, p); const send = ws.send.bind(ws);
    ws.send = (d) => { try { const m = JSON.parse(d); if (m.t === "cmd") window.__mock.sent[m.id] = { name: m.name, args: m.args }; } catch (e) {} return send(d); };
    ws.addEventListener("message", (e) => { if (typeof e.data !== "string") return; const m = JSON.parse(e.data);
      if (m.t === "state") window.__mock.state = m.state;
      if (m.t === "reply" && window.__mock.sent[m.id]) window.__mock.replies.push({ ...window.__mock.sent[m.id], ok: m.ok, result: m.result, error: m.error }); });
    return ws; };
  window.WebSocket.prototype = Real.prototype; Object.assign(window.WebSocket, Real);
})();"""


def main() -> None:
    host = subprocess.Popen(["orkboard", "--serve", str(FOLDER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, cwd=FOLDER)
    try:
        url = json.loads(host.stdout.readline())["url"]
        with sync_playwright() as p:
            exe = next((c for c in (os.environ.get("ORKCRAFT_CHROMIUM", ""), "/opt/pw-browsers/chromium") if c and Path(c).exists()), None)
            b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
            for vp in ({"width": 1440, "height": 900}, {"width": 390, "height": 844}):
                page = b.new_page(viewport=vp)
                page.add_init_script(SPY)
                page.goto(url)
                page.wait_for_timeout(6000)
                # what the new faces read and the old ones do not ask yet: the feed, the recap since the last look, the cards' turns, verdicts, tables and the cost of a paid pass (gui/ideas_mats.py)
                page.evaluate("""() => import("/static/js/link.js").then((l) => Promise.all(%s.map(([n, a]) =>
                    l.command(n, a, true).catch(() => null))))""" % json.dumps(EXTRA))
                page.wait_for_timeout(2000)
                for tab in page.locator("[role=tab], .ork-tab, .gui-tab").all()[:12]:   # every leader's lane asks its own
                    try: tab.click(timeout=1500); page.wait_for_timeout(1200)
                    except Exception: pass
                rec = page.evaluate("window.__mock")
                page.close()
                if vp["width"] == 1440: desk = rec
            mock = {"recorded": time.strftime("%Y-%m-%d %H:%M"), "folder": FOLDER.name, "state": desk["state"], "replies": []}
            seen = set()
            for r in desk["replies"] + rec["replies"]:
                key = r["name"] + json.dumps(r.get("args") or {}, sort_keys=True)
                if key not in seen: seen.add(key); mock["replies"].append(r)
    finally:
        host.stdin.close(); host.terminate()
    text = json.dumps(mock, ensure_ascii=False, indent=1)
    text = text.replace(str(Path.home()), "~").replace(str(FOLDER), "<project>")
    for bad in (r"sk-[A-Za-z0-9]{16,}", r"gh[pousr]_[A-Za-z0-9]{20,}", r"AKIA[0-9A-Z]{16}", r"-----BEGIN"):
        if re.search(bad, text): sys.exit(f"refused: the snapshot holds something like a key ({bad})")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text + "\n", encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(mock['replies'])} replies, {len(text) // 1024} KB")


if __name__ == "__main__":
    main()
