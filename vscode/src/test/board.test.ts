// The Board's process without VS Code: what `orkboard --serve` says is read, a missing program gives way to the next,
// and closing stdin stops it (orkboard/gui/extension.py).
import * as assert from "node:assert/strict";
import { test } from "node:test";
import { BoardProcess, launches, parseServed, SOURCE, type Served } from "../board";

const SAID = { url: "http://127.0.0.1:5000/?t=abc&app=1", origin: "http://127.0.0.1:5000", version: "0.1.0" };

// A stand-in for `orkboard --serve`: says where it is, then serves until its stdin closes.
const FAKE = `
process.stdout.write("Orkline is starting\\n" + JSON.stringify(${JSON.stringify(SAID)}) + "\\n");
process.stdin.resume();
process.stdin.on("end", () => process.exit(0));
`;

test("the address is read from its line of JSON, and only a loopback http one", () => {
  assert.deepEqual(parseServed(JSON.stringify(SAID) + "\r"), SAID);
  assert.equal(parseServed("Orkline is at http://127.0.0.1:5000"), null);
  assert.equal(parseServed("{not json"), null);
  assert.equal(parseServed(JSON.stringify({ ...SAID, url: "https://example.com/?t=abc" })), null);
  assert.equal(parseServed(JSON.stringify({ origin: SAID.origin })), null);
});

test("the setting's program is the one way, else orkboard and then uvx", () => {
  assert.deepEqual(launches(" python3 ", ["-m", "orkboard.gui.board_host"], "/p"),
                   [{ command: "python3", args: ["-m", "orkboard.gui.board_host", "--serve", "/p"] }]);
  assert.deepEqual(launches("", [], undefined), [
    { command: "orkboard", args: ["--serve"] },
    { command: "uvx", args: ["--from", SOURCE, "orkboard", "--serve"] },
  ]);
});

test("a missing program gives way to the next; it is served, logs the rest and stops when its stdin closes", async () => {
  const served: Served[] = [], logs: string[] = [];
  const exited = new Promise<[number | null, boolean]>((resolve) => {
    const board = new BoardProcess(
      [{ command: "orkboard-not-here", args: [] }, { command: process.execPath, args: ["-e", FAKE] }], undefined, {
        served: (s) => { served.push(s); board.close(); },
        log: (text) => logs.push(text),
        exit: (code, missing) => resolve([code, missing]),
      });
    board.start();
  });
  assert.deepEqual(await exited, [0, false]);
  assert.deepEqual(served, [SAID]);
  assert.ok(logs.some((l) => l.includes("Orkline is starting")));
});

test("no program at all is said as missing", async () => {
  const exited = await new Promise<[number | null, boolean]>((resolve) => {
    new BoardProcess([{ command: "orkboard-not-here", args: [] }], undefined, {
      served: () => {}, log: () => {}, exit: (code, missing) => resolve([code, missing]),
    }).start();
  });
  assert.deepEqual(exited, [null, true]);
});
