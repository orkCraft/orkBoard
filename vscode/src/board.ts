// The Board's process (orkboard/gui/extension.py): `orkboard --serve <folder>` says where its page is as one line of JSON
// on stdout and lives as long as its stdin is open. Nothing here imports vscode, so the tests run it with Node alone.
import { spawn, type ChildProcess } from "node:child_process";

/** What `orkboard --serve` says once it listens, and again after an update restarted it in place. */
export interface Served {
  url: string;
  origin: string;
  version: string;
}

/** One way to start the Board: a program and its arguments, the extension's own put last. */
export interface Launch {
  command: string;
  args: string[];
}

export const SOURCE = "git+https://github.com/orkWorks/orkBoard";
export const INSTALL = `uv tool install 'orkboard @ ${SOURCE}'`;

/** A line of stdout that says where the page is, else null (anything else Orkboard prints goes to the log). */
export function parseServed(line: string): Served | null {
  const text = line.trim();
  if (!text.startsWith("{")) return null;
  try {
    const said = JSON.parse(text);
    if (typeof said.url !== "string" || typeof said.origin !== "string") return null;
    const url = new URL(said.url);
    if (url.protocol !== "http:" || !["127.0.0.1", "localhost"].includes(url.hostname)) return null;
    return { url: said.url, origin: said.origin, version: String(said.version ?? "") };
  } catch {
    return null;
  }
}

/** The ways to start the Board, tried in turn while a program is missing: the setting's, else `orkboard`, else uvx. */
export function launches(command: string, args: string[], folder: string | undefined): Launch[] {
  const own = ["--serve", ...(folder ? [folder] : [])];
  if (command.trim()) return [{ command: command.trim(), args: [...args, ...own] }];
  return [
    { command: "orkboard", args: [...args, ...own] },
    { command: "uvx", args: ["--from", SOURCE, "orkboard", ...args, ...own] },
  ];
}

export interface Events {
  served(served: Served): void;
  log(text: string): void;
  /** It stopped: `code` its exit code, `missing` when no way to start it was found. */
  exit(code: number | null, missing: boolean): void;
}

/** One Board's process: started on the first launch whose program exists, closed by closing its stdin. */
export class BoardProcess {
  private child: ChildProcess | null = null;
  private closing = false;

  constructor(private readonly ways: Launch[], private readonly cwd: string | undefined,
              private readonly on: Events) {}

  get running(): boolean {
    return this.child !== null;
  }

  start(): void {
    this.closing = false;
    this.attempt(0);
  }

  private attempt(i: number): void {
    const way = this.ways[i];
    if (!way) {
      this.on.exit(null, true);
      return;
    }
    this.on.log(`$ ${way.command} ${way.args.join(" ")}\n`);
    const child = spawn(way.command, way.args, { cwd: this.cwd, stdio: ["pipe", "pipe", "pipe"], windowsHide: true });
    this.child = child;
    let started = false, rest = "";
    child.on("spawn", () => { started = true; });
    child.on("error", (e: NodeJS.ErrnoException) => {
      if (!started && e.code === "ENOENT") {
        this.child = null;
        this.attempt(i + 1);
      } else {
        this.on.log(`${e.message}\n`);
      }
    });
    child.stdout!.setEncoding("utf8");
    child.stdout!.on("data", (chunk: string) => {
      const lines = (rest + chunk).split("\n");
      rest = lines.pop() ?? "";
      for (const line of lines) {
        const served = parseServed(line);
        if (served) this.on.served(served);
        else if (line.trim()) this.on.log(line + "\n");
      }
    });
    child.stderr!.setEncoding("utf8");
    child.stderr!.on("data", (chunk: string) => this.on.log(chunk));
    child.on("exit", (code) => {
      if (!started) return;                                  // the next way is being tried
      if (this.child === child) this.child = null;
      this.on.exit(this.closing ? 0 : code, false);
    });
  }

  /** Closing stdin stops it (the editor went away); a process that has not stopped in `graceMs` is killed. */
  close(graceMs = 5000): void {
    const child = this.child;
    if (!child) return;
    this.closing = true;
    child.stdin?.end();
    const kill = setTimeout(() => child.kill(), graceMs);
    child.once("exit", () => clearTimeout(kill));
  }
}
