# wasm-mcp (MCPB Bundle)

FastMCP server for WebAssembly sandbox execution (instantiate, call exports, inspect modules)

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "wasm-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "wasm_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **wasm_inspect**: wasm_inspect
- **wasm_call**: wasm_call
- **wasm_run**: wasm_run

## Requirements

- Python 3.12+
- uv
