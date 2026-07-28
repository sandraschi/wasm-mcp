# wasm-mcp — MCP Server Capabilities

**Server:** wasm-mcp v0.1.0
**Description:** FastMCP server for WebAssembly sandbox execution. Loads .wasm and .wat files, inspects exports and imports, calls exported functions with numeric arguments, and returns structured JSON results. All execution happens inside Wasmtime with strong sandbox guarantees.

---

## Architecture Overview

wasm-mcp uses the Wasmtime runtime (via `wasmtime-py`) to provide a secure, sandboxed WebAssembly execution environment. Wasmtime is developed by the Bytecode Alliance and implements the WASM MVP specification plus many post-MVP proposals including bulk memory operations, reference types, SIMD, and multi-value returns.

### Execution Model

Each tool invocation creates a fresh Wasmtime `Store` and `Instance`:

- **Full isolation:** No state persists between calls. Global variables reset on every invocation.
- **No caching:** Modules load from disk on every call. No module cache.
- **No host functions:** The server provides zero WASM imports. Modules requiring imports will fail.
- **Single-threaded:** WASM runs synchronously in the MCP server thread.
- **Stdio transport by default:** Compatible with Claude Desktop, Cursor, and all MCP stdio clients.

### Security Model

Wasmtime provides these guarantees:

- **No filesystem access:** WASM modules cannot read or write files on the host.
- **No network access:** WASM modules cannot open sockets or make HTTP requests.
- **No OS access:** WASM modules cannot spawn processes, read environment variables, or execute system calls.
- **Memory safety:** Wasmtime uses a sandboxed linear memory model. No out-of-bounds memory access is possible.
- **Deterministic execution:** Given identical inputs, the same WASM module produces identical outputs (excluding traps).

### Data Flow

```
MCP Client → Tool Request (path, export_name, args_json)
  → wasm-mcp server reads .wasm from disk
  → Wasmtime parses and validates the binary
  → Fresh Store and Instance created
  → Module instantiated with empty imports
  → Exported function called with parsed args
  → Return value converted to Python primitives
  → Structured JSON returned to client
```

### Transport

- **Stdio mode:** Default. Compatible with Claude Desktop, Cursor, VS Code MCP extensions.
- **HTTP mode:** Set `MCP_TRANSPORT=http`. The server binds to `http://localhost:8000` with SSE transport (`GET /sse`, `POST /messages?session_id=<id>`).

---

## Tool Reference

### 1. wasm_inspect

**Purpose:** Inspect a WASM module file to discover its exports and import requirements without executing any exported function. Use this before `wasm_call` or `wasm_run` to understand the module's interface.

**How it works:**
1. Reads the file from the specified path. Supports both `.wasm` (binary) and `.wat` (text format, auto-parsed by Wasmtime).
2. Parses the WASM binary with the Wasmtime engine.
3. Attempts to instantiate the module with no imports.
4. If successful, enumerates all exports with their names and kinds (`Func`, `Memory`, `Global`, `Table`).
5. If instantiation fails (module requires imports), returns an error.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `str` | Yes | — | Filesystem path to a `.wasm` or `.wat` file. Relative paths resolve from the server's CWD. |

**Return Format (success):**
```json
{
  "ok": true,
  "path": "C:/wasm/math.wasm",
  "exports": [
    {"name": "add", "kind": "Func"},
    {"name": "subtract", "kind": "Func"},
    {"name": "multiply", "kind": "Func"},
    {"name": "memory", "kind": "Memory"},
    {"name": "__data_end", "kind": "Global"}
  ],
  "imports": []
}
```

**Return Format (instantiation fails):**
```json
{
  "ok": false,
  "error": "module requires at least 1 import",
  "exports": [],
  "imports": ["Module requires imports; list not available without instantiating."]
}
```

**Return Format (file not found):**
```json
{
  "ok": false,
  "error": "WASM file not found: C:/nonexistent.wasm",
  "exports": [],
  "imports": []
}
```

**Export kinds:** `Func` (callable), `Memory` (linear memory), `Global` (readable/writable variable), `Table` (indirect function call table).

---

### 2. wasm_call

**Purpose:** Load a WASM module, instantiate it, call a named exported function with the given arguments, and return the result. Freshly loads and instantiates on every call.

**How it works:**
1. Loads and parses the WASM binary from the specified path.
2. Attempts to instantiate the module with no imports.
3. Looks up the named export. Returns all available exports listed in the error if not found.
4. Parses `args_json` as a JSON array of numbers.
5. Calls the function with the parsed arguments.
6. Converts WASM return values: single → Python primitive, tuple → Python list, void → `null`.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `str` | Yes | — | Filesystem path to the `.wasm` file. |
| `export_name` | `str` | Yes | — | Name of the exported function to call. Case-sensitive. |
| `args_json` | `str` | No | `"[]"` | JSON array of numeric arguments, e.g. `"[1, 2]"` or `"[3.14]"`. |

**Return Format (single value):**
```json
{
  "ok": true,
  "path": "C:/wasm/math.wasm",
  "export": "add",
  "result": 3
}
```

**Return Format (multi-value):**
```json
{
  "ok": true,
  "path": "C:/wasm/multi.wasm",
  "export": "divide",
  "result": [3, 1]
}
```

**Return Format (void):**
```json
{
  "ok": true,
  "path": "C:/wasm/store.wasm",
  "export": "store",
  "result": null
}
```

**Error Formats:**
```json
{"ok": false, "error": "WASM file not found: C:/no_file.wasm", "result": null}
{"ok": false, "error": "Export not found: addd. Available: ['add', 'subtract']", "result": null}
{"ok": false, "error": "Invalid args JSON: Expecting value line 1 column 5", "result": null}
{"ok": false, "error": "wasm trap: wasm `unreachable` instruction executed", "result": null}
```

---

### 3. wasm_run

**Purpose:** Convenience wrapper around `wasm_call` with a default entry point of `_start` (WASI convention). Use for running WASM modules that follow the WASI initialization pattern.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `str` | Yes | — | Filesystem path to the `.wasm` file. |
| `entry_export` | `str` | No | `"_start"` | Entry point export name. Common: `"_start"`, `"main"`, `"run"`. |
| `args_json` | `str` | No | `"[]"` | JSON array of numeric arguments. |

**Return Format:**
```json
{
  "ok": true,
  "path": "C:/wasm/hello.wasm",
  "export": "_start",
  "result": null
}
```

**Notes:** Delegates to the same internal `_call_export` function as `wasm_call`. The only difference is the default value of `entry_export`.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `"stdio"` | Transport mode. `"http"` for HTTP/SSE. |

No other environment variables are required or consumed.

## Security & Privacy

- **Strong sandboxing:** Wasmtime enforces memory safety, control-flow integrity, and isolation. No host access.
- **No persistence:** Fresh Store and Instance on every call. No cross-call state sharing.
- **File access:** Any readable `.wasm` file on the filesystem can be loaded. Restrict via OS permissions.
- **No network calls:** wasm-mcp makes zero network requests. Everything is local.

## Detailed Parameter Specifications

### wasm_inspect Complete Parameter Reference

The `path` parameter accepts any filesystem path that the server process can read. Relative paths are resolved against the server's current working directory. Absolute paths (e.g. `C:/wasm/module.wasm`, `/home/user/wasm/module.wasm`) are recommended for reproducibility. The path must point to a valid WASM binary file (typically `.wasm` extension) or a WASM text format file (`.wat` extension). Wasmtime's binary parser handles both formats transparently. If the file does not exist, the tool returns an error with `"WASM file not found: {path}"`. If the file exists but is not valid WASM, Wasmtime will throw a parse error which is caught and returned as a structured error with the Wasmtime error message.

### wasm_call Complete Parameter Reference

The `path` parameter has the same semantics as in `wasm_inspect`. The `export_name` parameter must match an exported function name exactly (case-sensitive). Common export names include `"add"`, `"main"`, `"_start"`, `"run"`, `"init"`, `"process"`, `"compute"`, and any other name the module's author chose for its exported functions. Use `wasm_inspect` before calling to discover the exact export names. The `args_json` parameter must be a valid JSON string. Valid values include: `"[]"` for no arguments, `"[42]"` for a single integer argument, `"[1, 2, 3]"` for multiple integer arguments, `"[3.14, 2.718]"` for float arguments, and `"[1, 2.5, 3]"` for mixed numeric arguments. The JSON parser expects exactly the format specified by RFC 7159. Invalid JSON produces an error message containing the JSON decoder's position-specific error, helping the caller locate the syntax problem. Arguments are passed to the WASM function in the order they appear in the array. Wasmtime performs type coercion according to the WASM function's declared signature. If the argument types do not match the function signature, Wasmtime will throw a runtime error that is caught and returned.

### wasm_run Complete Parameter Reference

The `entry_export` parameter defaults to `"_start"`, which is the WASI standard entry point. Many WASM modules compiled with Emscripten or WASI SDKs export `_start`. Modules compiled with `--target wasm32-unknown-unknown` typically do not have `_start` — they use custom export names or `main` instead. The `wasm_run` tool is a convenience wrapper that differs from `wasm_call` only in its default export name. Both tools call the exact same internal implementation (`_call_export`). If `_start` is not found, the error message lists all available exports, allowing the caller to correct the entry point name.

### Return Value Handling

The result converter in `_call_export` handles three return value cases: (1) If the WASM function returns `None` (void), `result` is set to `null`. (2) If the return value is a scalar (int, float), `result` is that scalar directly. (3) If the return value is iterable (multi-value WASM returns, tuples), `result` is a JSON array. The converter explicitly excludes strings and bytes from iterable unwrapping to avoid breaking on WASM memory objects. If the function returns a single-element tuple from a multi-value return, it appears as a single-element array like `[42]`.

### Error Handling Architecture

All errors in wasm-mcp follow a consistent pattern: `ok` is `false`, `error` contains a human-readable description, and `result` is `null`. There are five error categories:
1. **File system errors:** The file does not exist or cannot be read. Error message: `"WASM file not found: {path}"`.
2. **Module instantiation errors:** The WASM binary is valid but requires imports that wasm-mcp does not provide. Error message: `"module requires at least 1 import"`.
3. **Export resolution errors:** The named export is not found in the module. Error message includes the list of available exports: `"Export not found: {name}. Available: [{exports}]"`.
4. **Argument parse errors:** The `args_json` string is not valid JSON. Error message includes the JSON decoder's position: `"Invalid args JSON: {decoder message}"`.
5. **Runtime traps:** The WASM function encountered an error during execution. Error message comes from Wasmtime: `"wasm trap: {trap description}"`.

### WASM Module Requirements

For a WASM module to work with wasm-mcp, it must meet these requirements:
- Must be a valid WASM binary or text format file
- Must not require any imports (no WASI, no host functions, no JavaScript imports)
- Must export at least one function (to call with `wasm_call` or `wasm_run`)
- Exported functions must accept numeric parameters (i32, i64, f32, f64) if any
- The module must not depend on WASI system calls (stdin, stdout, stderr, file I/O, clock)

Modules compiled with `wasm32-unknown-unknown` target typically meet these requirements. Modules compiled with `wasm32-wasi` typically do not, as they depend on WASI imports.

### Creating Compatible WASM Modules

**From Rust (recommended):** Use `#![no_std]` and `#[no_mangle]` to export functions. Compile with `--target wasm32-unknown-unknown`. Avoid `std` crate features that depend on the OS.

**From C:** Use `-nostdlib` flag with Clang. Export functions with `__attribute__((used))` or linker export flags. Avoid libc functions that require system calls.

**From AssemblyScript:** Use the `as-export` mechanism. AssemblyScript modules may include runtime imports — check with `wasm_inspect` first.

**From Go:** Go WASM modules typically require a `resume` function and a JavaScript runtime. They are unlikely to work with wasm-mcp.

## Complete Error Reference

Every error response follows the same schema: `{ "ok": false, "error": "<description>", "result": null }`. The `error` string always contains enough context for an automated agent to diagnose and recover from the failure. Below is every error that each tool can produce.

### wasm_inspect Error Types
- **File not found:** The specified path does not exist or is not accessible. Error: `"WASM file not found: {path}"`. Recovery: verify the path is correct and the file exists.
- **Import requirement:** The module needs host-provided imports that wasm-mcp does not supply. Error: `"module requires at least 1 import"`. Recovery: use a different WASM module that is self-contained without imports.
- **Parse error:** The file exists but is not valid WASM binary or text format. Error: Wasmtime parser exception message. Recovery: verify the file is a valid `.wasm` or `.wat` file.

### wasm_call Error Types
- **File not found:** Same as wasm_inspect.
- **Import requirement:** Same as wasm_inspect.
- **Export not found:** The named export does not exist. Error includes all available exports. Recovery: call wasm_inspect first to discover valid export names.
- **JSON parse error:** The args_json string is not valid JSON. Error includes the JSON decoder's position-specific error. Recovery: ensure args_json is valid JSON containing only numbers.
- **Runtime trap:** The WASM function hit an error during execution. Error includes the Wasmtime trap description. Recovery: verify arguments are within valid ranges for the function.

### wasm_run Error Types
Same as wasm_call, plus:
- **Default export not found:** If `_start` is not found and no `entry_export` was specified. Recovery: specify the correct entry point or use wasm_inspect first.

## WASM Module Requirements

Wasmtime in wasm-mcp supports these WASM features:
- Core WASM MVP: function calls, control flow, linear memory, global variables
- Bulk memory: `memory.copy`, `memory.fill`, `table.copy`, `table.init`
- Reference types: `externref`, `funcref`
- SIMD: 128-bit vector operations
- Multi-value: functions returning multiple values
- Mutable globals
- Sign extension operators

Not supported: WASI (any version), threads, shared memory, GC proposal.

## Working with WAT (Text Format)

The `.wat` file format is the human-readable text representation of WASM. Wasmtime automatically parses WAT files, so `wasm_inspect`, `wasm_call`, and `wasm_run` all work with `.wat` files without any special handling. WAT is useful for creating quick test modules without a compiler toolchain.

## Integration Points

- **Wasmtime:** The sole WASM runtime supporting WASM MVP + post-MVP proposals.
- **Standard MCP transport:** Compatible with any MCP client (stdio or HTTP/SSE).
- **Filesystem:** Loads `.wasm` and `.wat` files from any accessible path.
## Working with WASM Modules Detailed Examples

### Example 1: Simple Arithmetic Module
Create rith.wat with add, subtract, multiply, divide. Compile with wat2wasm. Inspect with wasm_inspect to see 4 exports. Call each with sample arguments. Test division by zero to verify trap handling. This is the canonical "hello world" for wasm-mcp.

### Example 2: Factorial Module
Create act.wat with a recursive factorial implementation. Test with small values (0, 1, 5, 10). Note that large inputs (>20) overflow i32 and produce incorrect results due to integer wrapping. The WASM spec defines i32 wrapping behavior, so the returned values are technically correct but may differ from mathematical expectation.

### Example 3: Memory-Only Module
Some WASM modules export only a memory and use it as a scratch buffer. wasm_inspect will show the Memory export. No functions are callable. These modules are typically used with JavaScript on web pages and are not useful with wasm-mcp.

### Example 4: Multi-Value Return Module
WASM multi-value proposal allows functions to return multiple values. A divide function can return both quotient and remainder. wasm_call converts multi-value returns to JSON arrays. A function returning (quotient, remainder) as (i32, i32) will produce [3, 1] for arguments 10 and 3.

### Example 5: Module with Globals
Some modules export global variables (read-only or mutable). wasm_inspect lists these with kind "Global". They cannot be called or modified through wasm_call. They are typically used for configuration or module metadata.

## WASM Module Source Compatibility Table

| Toolchain | Build Command | Compatible | Notes |
|-----------|--------------|-----------|-------|
| Rust wasm32-unknown-unknown | rustc --target wasm32-unknown-unknown -O | Yes | Use no_std or handle imports |
| Rust wasm32-wasi | rustc --target wasm32-wasi | No | Requires WASI imports |
| Clang wasm32 | clang --target=wasm32 -nostdlib | Yes | Export functions explicitly |
| Clang wasm32 with libc | clang --target=wasm32 | No | Requires WASI imports |
| Emscripten | emcc | No | Requires JS runtime |
| AssemblyScript | asc | Maybe | Depends on runtime imports |
| WAT manual | wat2wasm | Yes | No imports needed |
| Go | GOOS=js GOARCH=wasm | No | Requires JS runtime |
| TinyGo | tinygo build -target=wasi | No | WASI imports |
| Zig | zig build-exe -target wasm32-freestanding | Yes | Use no-entry |

## Deeper Dive: WASM Memory and Data

WASM linear memory is a contiguous byte array accessible by the WASM module. Modules use memory for heap-allocated data, strings, arrays, and complex data structures. wasm-mcp does not provide tools to read or write WASM memory directly. Functions that accept pointer arguments (i32 memory addresses) and length arguments are common for string processing. For example, a hash(data_ptr: i32, data_len: i32) -> i32 function takes a pointer and length in WASM linear memory as two integer arguments. The caller must ensure that the memory region at the given address contains valid data before calling.

## WASM Instantiation Process

When wasm_call or wasm_run is invoked, the server performs these steps:
1. Read the file bytes from disk
2. Pass bytes to Wasmtime Module constructor (parses and validates)
3. Create a fresh Store for the module
4. Call Instance constructor with empty imports list
5. If instantiation fails due to missing imports, return error
6. If instantiation succeeds, look up the named export
7. If export not found, return error with available exports
8. Parse args_json as JSON array
9. Call the exported function with parsed args
10. Convert the return value to Python type
11. Return structured JSON

Each step can fail independently and the error is caught at the appropriate level. The server never crashes due to a WASM error.

## Binary Format Specifications

### WASM Binary Format
The WASM binary format is a structured binary encoding defined by the WASM specification. It consists of sections: magic number, version, type section, import section, function section, table section, memory section, global section, export section, start section, element section, code section, data section, and custom sections. The Wasmtime engine parses all standard sections and validates the module before instantiation.

### WASM Text Format (WAT)
The WAT text format uses S-expressions to represent WASM modules. Wasmtime includes a built-in WAT parser, so WAT files are supported transparently without any separate compilation step. The parser converts WAT to binary before compilation.

### Module Practical Limits
Wasmtime does not enforce strict module size limits, but:
- Modules larger than 50MB may exhaust server memory
- The Wasmtime compiler may take significant time for very large modules
- Linear memory allocation is limited by available system memory

## Working with Module Features

### SIMD Support
Wasmtime supports WASM SIMD (128-bit vector operations). Modules using SIMD instructions work transparently. SIMD acceleration depends on host CPU support.

### Bulk Memory Operations
Wasmtime supports bulk memory instructions: memory.copy, memory.fill, table.copy, table.init, elem.drop. These allow efficient memory manipulation within the WASM sandbox.

### Reference Types
Wasmtime supports externref and funcref reference types for indirect function calls or opaque external references.

### Multi-Value Returns
Wasmtime supports the multi-value proposal, allowing functions to return multiple values. wasm-mcp converts multi-value returns to JSON arrays automatically.

## Detailed Module Lifecycle And Testing Strategy

When working with unknown WASM modules, follow this systematic approach. First, identify the module's purpose from its filename or documentation. Second, call wasm_inspect to learn the exact export interface. Third, examine the exports list for function names and argument patterns. Fourth, call each function with small test values to verify behavior. Fifth, test boundary conditions like zero, maximum values, and invalid inputs. Sixth, handle all error types including file-not-found, import-missing, export-missing, and runtime traps. This systematic approach catches integration issues early and builds confidence in the module's behavior.

The WASM instantiation process involves six critical steps that can each fail independently. File reading can fail if the path is wrong or permissions are denied. WASM parsing can fail if the binary is corrupted or the format is invalid. Module instantiation can fail if the module requires imports that are not provided. Export resolution can fail if the function name does not match. Argument parsing can fail if the JSON is malformed. Function execution can fail with a runtime trap if the arguments cause an error. Each failure mode returns a distinct error message to guide recovery.

The server architecture prioritizes stability over performance. Each tool invocation is completely isolated from previous calls. WASM modules are loaded, parsed, instantiated, executed, and discarded in a single request. This ensures no cross-call contamination but adds overhead for repeated calls. For production use cases requiring high throughput, consider combining multiple operations into a single WASM module or caching compiled modules at the application level.

## Environment Setup for Development

### Installing Wasmtime
The wasmtime-py package is installed automatically by uv sync. It includes the Wasmtime runtime as a shared library. On Windows, this may require the Visual C++ Redistributable.

### Installing wat2wasm
For compiling WAT to WASM binary, install the WebAssembly Binary Toolkit (wabt) from the official GitHub releases page and add it to your PATH.

### Installing Rust WASM Target
For compiling Rust to WASM: run rustup target add wasm32-unknown-unknown. Then compile with rustc using the wasm32-unknown-unknown target and --crate-type cdylib flag.
