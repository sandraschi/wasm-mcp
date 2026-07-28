"""
wasm-mcp: FastMCP server for WebAssembly sandbox execution.

Tools: inspect module exports/imports, call exported functions.
Runtime: Wasmtime (sandboxed, no host access by default).
"""

import json
import logging
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from wasmtime import Instance, Module, Store

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="wasm-mcp",
    version="0.1.0",
)


def _load_module(store: Store, path: str) -> tuple[Module, bytes]:
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"WASM file not found: {path}")
    data = p.read_bytes()
    module = Module(store.engine, data)
    return module, data


def _inspect_module(path: str) -> dict[str, Any]:
    store = Store()
    try:
        module, _ = _load_module(store, path)
    except Exception as e:
        return {"ok": False, "error": str(e), "exports": [], "imports": []}
    exports: list[dict[str, str]] = []
    imports: list[dict[str, str]] = []
    try:
        instance = Instance(store, module, [])
        ex = instance.exports(store)
        for name in ex:
            exports.append({"name": name, "kind": type(ex[name]).__name__})
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "exports": [],
            "imports": ["Module requires imports; list not available without instantiating."],
        }
    return {"ok": True, "path": path, "exports": exports, "imports": imports}


def _call_export(path: str, export_name: str, args_json: str) -> dict[str, Any]:
    store = Store()
    try:
        module, _ = _load_module(store, path)
    except Exception as e:
        return {"ok": False, "error": str(e), "result": None}
    try:
        instance = Instance(store, module, [])
        exports = instance.exports(store)
        if export_name not in exports:
            return {
                "ok": False,
                "error": f"Export not found: {export_name}. Available: {list(exports.keys())}",
                "result": None,
            }
        func = exports[export_name]
        args: list[int | float] = []
        if args_json.strip():
            args = json.loads(args_json)
            if not isinstance(args, list):
                args = [args]
        result = func(store, *args)
        if result is None:
            out: Any = None
        elif hasattr(result, "__iter__") and not isinstance(result, (str, bytes)):
            out = list(result)
        else:
            out = result
        return {"ok": True, "path": path, "export": export_name, "result": out}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Invalid args JSON: {e}", "result": None}
    except Exception as e:
        logger.exception("wasm_call failed")
        return {"ok": False, "error": str(e), "result": None}


@mcp.tool()
def wasm_inspect(path: str) -> dict[str, Any]:
    """
    Inspect a WebAssembly module file: list its exports and report import requirements.

    Use this to discover which functions (or other exports) a .wasm file exposes
    before calling them with wasm_call or wasm_run.

    Args:
        path: Filesystem path to a .wasm or .wat file.

    Returns:
        Dict with ok, path, exports (list of {name, kind}), imports (if any),
        and error if ok is False.
    """
    return _inspect_module(path)


@mcp.tool()
def wasm_call(path: str, export_name: str, args_json: str = "[]") -> dict[str, Any]:
    """
    Load a WASM module from path, call an exported function by name with given arguments.

    The module is instantiated with no imports (host functions). If the module
    requires imports, the call will fail. Arguments are passed as a JSON array
    of numbers (i32/i64/f32/f64); use args_json="[1, 2]" for two integer arguments.

    Args:
        path: Filesystem path to the .wasm file.
        export_name: Name of the exported function to call.
        args_json: JSON array of numeric arguments, e.g. "[1, 2]" or "[]".

    Returns:
        Dict with ok, path, export, result (return value or list of values), and error if ok is False.
    """
    return _call_export(path, export_name, args_json)


@mcp.tool()
def wasm_run(path: str, entry_export: str = "_start", args_json: str = "[]") -> dict[str, Any]:
    """
    Run a WASM module: load from path, call the given export (default _start) with optional args.

    Convenience wrapper around wasm_call. Use entry_export to choose which export to invoke
    (e.g. _start for WASI-like modules, or main, run, etc.).

    Args:
        path: Filesystem path to the .wasm file.
        entry_export: Export name to call (default _start).
        args_json: JSON array of arguments (default "[]").

    Returns:
        Same shape as wasm_call: ok, path, export, result, error.
    """
    return _call_export(path, entry_export, args_json)


def main() -> None:
    """Run the MCP server (stdio)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
