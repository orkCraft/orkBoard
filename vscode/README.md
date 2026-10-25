# Orkboard for VS Code

The Board in an editor tab: a project's parties and their goals, the goals' specs and plans, the orks at work and the
results to review. It is the same page as Orkboard's own window, for the folder open in VS Code.

## What it needs

The extension runs the Board with the **orkboard** program (Python 3.11 or later) on this computer:

```sh
uv tool install 'orkboard @ git+https://github.com/orkCraft/orkBoard'
```

Without it the extension starts the Board through `uvx` when `uv` is installed, which downloads Orkboard on first use.
The orks themselves are your AI tools (Claude Code, Codex and others): the Board's first screen shows which ones it
found and lets you choose.

## Use

- **Orkboard: Open the Board** opens the Board of the workspace's folder (with several folders, it asks which one).
- **Orkboard: Close the Board** closes every Board and stops Orkboard.
- **Orkboard: Show the log** shows what Orkboard printed.

A Board left open opens again when VS Code restarts.

## Settings

| Setting | What it does |
| --- | --- |
| `orkboard.command` | The program that runs the Board. Empty: `orkboard` from the PATH, else `uvx`. |
| `orkboard.args` | Arguments put before the extension's own, e.g. `["-m", "orkboard.gui.board_host"]` when `orkboard.command` is a Python. |

## How it works, and what it does not do

The extension starts `orkboard --serve <folder>`. Orkboard serves the Board on `127.0.0.1` only, behind a random token,
and the tab shows that page. Closing the tab stops it. Nothing leaves your computer except what your AI tools send
themselves, and the usage stats and crash reports you choose on the first screen.

- **Local folders only for now.** Remote SSH, WSL, Dev Containers and Codespaces are not supported yet.
- VS Code's own shortcuts do not reach the Board while it has the focus: click the editor to use them.

## Licence

The extension and Orkboard are open source under the [Apache License 2.0](LICENSE). The names and the ork mark (the
extension's icon) are not part of the licence ([NOTICE](NOTICE)).
