// Orkboard in VS Code: the Board of a workspace's folder in an editor tab. The page is Orkboard's own (orkboard/gui/),
// served by `orkboard --serve` on 127.0.0.1 and shown in an iframe, so the tab and the app's window are one page.
import { randomBytes } from "node:crypto";
import * as vscode from "vscode";
import { BoardProcess, INSTALL, launches, type Served } from "./board";

const VIEW = "orkboard.board";

interface State {
  folder?: string;
}

class Board {
  private readonly process: BoardProcess;
  private served: Served | null = null;
  private disposed = false;

  constructor(readonly folder: string | undefined, readonly panel: vscode.WebviewPanel, home: vscode.Uri,
              private readonly log: vscode.OutputChannel, private readonly gone: () => void) {
    const config = vscode.workspace.getConfiguration("orkboard");
    const ways = launches(config.get<string>("command", ""), config.get<string[]>("args", []), folder);
    this.process = new BoardProcess(ways, folder, {
      served: (served) => void this.show(served),
      log: (text) => log.append(text),
      exit: (code, missing) => void this.stopped(code, missing),
    });
    panel.iconPath = vscode.Uri.joinPath(home, "media", "icon.png");
    panel.webview.options = { enableScripts: true };
    panel.onDidDispose(() => {
      this.disposed = true;
      this.process.close();
      this.gone();
    });
    this.page("Opening the Board…");
    this.process.start();
  }

  close(): void {
    if (!this.disposed) this.panel.dispose();
  }

  private async show(served: Served): Promise<void> {
    this.served = served;
    const external = await vscode.env.asExternalUri(vscode.Uri.parse(served.url, true));
    const url = external.toString(true);
    this.log.appendLine(`The Board ${served.version} is at ${served.origin}`);
    this.page("", url);
  }

  private async stopped(code: number | null, missing: boolean): Promise<void> {
    if (this.disposed) return;
    if (missing) {
      this.page("Orkboard, which runs the Board, is not installed.");
      const pick = await vscode.window.showErrorMessage(
        `Orkboard is not installed. Install it with ${INSTALL}, or name the program in the setting orkboard.command.`,
        "Copy the install command", "Open the setting");
      if (pick === "Copy the install command") await vscode.env.clipboard.writeText(INSTALL);
      if (pick === "Open the setting") await vscode.commands.executeCommand("workbench.action.openSettings", "orkboard.command");
      return;
    }
    if (code === 0 && this.served === null) return;
    if (code === 0) {                                        // it stopped on its own
      this.close();
      return;
    }
    this.page(`The Board stopped (exit code ${code}).`);
    const pick = await vscode.window.showErrorMessage(`The Board stopped (exit code ${code}).`, "Show the log", "Start again");
    if (pick === "Show the log") this.log.show();
    if (pick === "Start again") {
      this.served = null;
      this.page("Opening the Board…");
      this.process.start();
    }
  }

  /** The tab: the Board's page in an iframe once it is served, else a line that says what is happening. */
  private page(text: string, url?: string): void {
    if (this.disposed) return;
    const nonce = randomBytes(16).toString("base64");
    const frame = url ? new URL(url).origin : "";
    const state = JSON.stringify({ folder: this.folder } satisfies State);
    const esc = (s: string) => s.replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`);
    this.panel.webview.html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';${frame ? ` frame-src ${frame};` : ""}">
<style>
html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #141210; color: var(--vscode-editor-foreground); }
iframe { border: 0; width: 100%; height: 100%; display: block; }
p { font: 13px/1.5 system-ui, sans-serif; margin: 24px; }
</style>
</head>
<body>
${url ? `<iframe src="${esc(url)}" allow="clipboard-read; clipboard-write"></iframe>` : `<p>${esc(text)}</p>`}
<script nonce="${nonce}">acquireVsCodeApi().setState(${state});</script>
</body>
</html>`;
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const log = vscode.window.createOutputChannel("Orkboard");
  const boards = new Map<string, Board>();
  const key = (folder: string | undefined) => folder ?? "";

  const open = (folder: string | undefined, panel?: vscode.WebviewPanel): Board => {
    const existing = boards.get(key(folder));
    if (existing && !panel) {
      existing.panel.reveal();
      return existing;
    }
    const name = folder ? vscode.workspace.asRelativePath(folder, true).split(/[\\/]/).pop() : "";
    panel ??= vscode.window.createWebviewPanel(VIEW, name ? `Board · ${name}` : "Board", vscode.ViewColumn.Active,
                                               { enableScripts: true, retainContextWhenHidden: true });
    const board = new Board(folder, panel, context.extensionUri, log, () => {
      if (boards.get(key(folder)) === board) boards.delete(key(folder));
    });
    boards.set(key(folder), board);
    return board;
  };

  const pickFolder = async (): Promise<string | undefined | null> => {
    const folders = vscode.workspace.workspaceFolders ?? [];
    if (folders.length <= 1) return folders[0]?.uri.fsPath;
    const pick = await vscode.window.showWorkspaceFolderPick({ placeHolder: "The project whose Board opens" });
    return pick ? pick.uri.fsPath : null;
  };

  context.subscriptions.push(
    log,
    vscode.commands.registerCommand("orkboard.openBoard", async () => {
      const folder = await pickFolder();
      if (folder !== null) open(folder);
    }),
    vscode.commands.registerCommand("orkboard.closeBoard", () => {
      for (const board of [...boards.values()]) board.close();
    }),
    vscode.commands.registerCommand("orkboard.showLog", () => log.show()),
    vscode.window.registerWebviewPanelSerializer(VIEW, {
      async deserializeWebviewPanel(panel: vscode.WebviewPanel, state: State | undefined) {
        open(state?.folder, panel);
      },
    }),
    { dispose: () => { for (const board of [...boards.values()]) board.close(); } },
  );
}

export function deactivate(): void {}
