# wasm-mcp

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>


> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

FastMCP server for **WebAssembly sandbox execution**. Run and inspect WASM modules via natural language (e.g. Claude Desktop).

- **Instantiate** modules from file path or bytes.
- **Call exports** (functions) with typed arguments.
- **Inspect** modules (exports, imports, memory).
- **Sandboxed** execution via Wasmtime; no host access unless explicitly imported.

## Quick Start

```powershell
git clone https://github.com/sandraschi/wasm-mcp
cd wasm-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:


## Install

```bash
uv add wasm-mcp
# or
pip install wasm-mcp
```

## Run

```bash
uv run wasm-mcp
# or
wasm-mcp
```

## Cursor / Claude Desktop

Add to MCP config (e.g. `~/.cursor/mcp.json` or Claude Desktop):

```json
{
  "wasm-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/wasm-mcp", "run", "wasm-mcp"]
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `wasm_inspect` | List exports and imports of a WASM module (from file path). |
| `wasm_call` | Load a module from path, call an export by name with JSON arguments, return result as JSON. |
| `wasm_run` | Run a WASM module from path with optional entry export and args (convenience wrapper). |

## Requirements

- Python 3.12+
- Wasmtime (native; installed automatically with `wasmtime` pip package on supported platforms).


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

MIT.
