# wasm-mcp — User Guide

Server: wasm-mcp v0.1.0
Description: WebAssembly sandbox execution for MCP. Inspect, call, and run WASM modules using the Wasmtime runtime.
Transport: stdio (default) or HTTP (set MCP_TRANSPORT=http).

---

## Installation

### Prerequisites

Python 3.10+ with uv package manager. A WebAssembly module to test with (compile one or create a WAT text file).

### Setup Steps

git clone https://github.com/sandraschi/wasm-mcp.git
cd wasm-mcp
uv venv
uv sync
uv run python -m wasm_mcp

### Creating a Test WASM Module

Create add.wat:
(module
  (func $add (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add)
  (export "add" (func $add))
)

Compile: wat2wasm add.wat -o add.wasm

### Claude Desktop Configuration

In claude_desktop_config.json: command "uv", args ["run", "--directory", "C:/path/to/wasm-mcp", "python", "-m", "wasm_mcp"].

---

## Step-by-Step Tutorials

### Tutorial 1: Inspect a Math Module

Call wasm_inspect(path="C:/wasm/math.wasm") to discover exports. Returns 3 functions (add, subtract, multiply) and 1 memory. No imports required.

### Tutorial 2: Call an Addition Function

Call wasm_call(path="C:/wasm/math.wasm", export_name="add", args_json="[5, 3]"). Returns result 8.

### Tutorial 3: Call with Float Arguments

Call wasm_call(path="C:/wasm/trig.wasm", export_name="hypot", args_json="[3.0, 4.0]"). Returns result 5.0.

### Tutorial 4: Call a Void Function

Call wasm_call(path="C:/wasm/store.wasm", export_name="store", args_json="[42]"). Returns result null.

### Tutorial 5: Handle Module Requiring Imports

Call wasm_inspect(path="C:/wasm/wasi_hello.wasm"). Returns ok false with error about missing imports.

### Tutorial 6: Export Not Found Error

Call wasm_call(path="C:/wasm/math.wasm", export_name="nonexistent"). Returns error with list of available exports.

### Tutorial 7: Run with _start Entry

Call wasm_run(path="C:/wasm/hello.wasm"). Calls _start entry point, returns result null.

### Tutorial 8: Run with Custom Entry

Call wasm_run(path="C:/wasm/calc.wasm", entry_export="main", args_json="[0]"). Returns result 0.

### Tutorial 9: Invalid JSON Args

Call wasm_call(path="C:/wasm/math.wasm", export_name="add", args_json="[1, two]"). Returns JSON parse error.

### Tutorial 10: Multi-Value Return

Call wasm_call(path="C:/wasm/multi.wasm", export_name="divide", args_json="[10, 3]"). Returns [3, 1].

### Tutorial 11: Multiple Arguments

Call wasm_call(path="C:/wasm/vector.wasm", export_name="dot", args_json="[1, 2, 3, 4, 5]"). Returns 26.

### Tutorial 12: Runtime Trap

Call wasm_call(path="C:/wasm/math.wasm", export_name="divide", args_json="[5, 0]"). Returns wasm trap error.

---

## Troubleshooting Guide

1. File not found: Use absolute paths. Verify file exists.
2. Module requires imports: Use self-contained modules without WASI dependencies.
3. Export not found: Run wasm_inspect first to discover valid names.
4. Invalid JSON args: Use JSON validator. Ensure only numbers.
5. WASM trap: Function hit runtime error. Check argument validity.
6. Multi-value confusion: Multi-value returns are arrays. Single elements are not wrapped.
7. Slow first call: First call includes module compilation. Subsequent calls are faster.
8. No exports found: Module may be empty or use a different compilation target.
9. Large result: WASM multi-value returns are converted to arrays.
10. Wrong argument count: WASM function expects exact argument count. Check the module documentation.

---

## Detailed Error Recovery Walkthrough

### Error: File Not Found

Call wasm_inspect(path="C:/nonexistent.wasm") returns ok false with "WASM file not found". Solution: Use absolute path and verify file exists.

### Error: Export Not Found with Retry

Call wasm_call(path="C:/wasm/math.wasm", export_name="ad") returns "Export not found: ad. Available: ['add', 'subtract']". Retry with correct name "add".

### Error: Module Requires Imports

Call wasm_inspect(path="C:/wasm/wasi_hello.wasm") returns "module requires at least 1 import". Solution: Use a self-contained WASM module.

### Error: Runtime Trap

Call wasm_call(path="C:/wasm/math.wasm", export_name="divide", args_json="[10, 0]") returns "wasm trap". The server handles this gracefully.

### Error: Invalid JSON

Call wasm_call(args_json="[1, two]") returns JSON parse error. Correct to "[1, 2]".

---

## Complete WASM Module Lifecycle

1. Obtain a .wasm file (compile, download, or write WAT)
2. Call wasm_inspect to verify module loads and see exports
3. Check that imports is empty (module is self-contained)
4. Note the export names and kinds
5. For each Func export, call wasm_call with appropriate numeric arguments
6. Verify the results match expectations
7. If the module has a _start or main entry point, use wasm_run for convenience
8. Handle errors gracefully by checking the ok field in the response
9. Use error messages to guide retry with corrected parameters

---

## Advanced Usage Patterns

### Testing Multiple Functions in One Session

For a math module with functions add, sub, mul, div, pow, sqrt, log, sin, cos, tan:
1. Call wasm_inspect to confirm all 10 exports exist
2. Call each function with representative inputs
3. Verify results match manual calculations
4. Test edge cases: zero, one, negative numbers, large numbers
5. Test error cases: division by zero, sqrt of negative, log of zero

### Working with WAT Format

WAT files work directly without compilation. Call wasm_inspect(path="test.wat"). Wasmtime automatically parses the text format. Useful for:
- Learning WASM without a build step
- Creating quick test modules
- Debugging module behavior
- Prototyping module interfaces

### Performance Optimization

Each wasm_call loads and compiles from disk. Small modules under 100KB: under 50ms per call. Large modules over 1MB: 200-500ms per call. Combine multiple operations into a single export for repeated calls to the same module.

---

## WASM Module Compatibility Reference

| Source Language | Compatible | Notes |
|----------------|-----------|-------|
| Rust (no_std) | Yes | Best choice, minimal imports |
| Rust (std) | Maybe | May require WASI imports |
| C (Clang, no libc) | Yes | Use -nostdlib |
| C (full libc) | No | Requires WASI |
| AssemblyScript | Maybe | Depends on runtime |
| Go | No | Requires JS runtime |
| WAT | Yes | No imports needed |

### Module Size Guide

Math utility: 500 bytes to 5 KB. Data processing: 5 KB to 50 KB. Game logic: 50 KB to 500 KB. Image processing: 100 KB to 2 MB. Full application: 1 MB to 10 MB.

---

## Testing Guide

Run the full test suite: uv run pytest tests/ -q -v

Tests cover: file not found, invalid JSON, export not found, module requiring imports, runtime traps, and successful execution with various argument types.

---

## FAQ

1. What runtime does wasm-mcp use? Wasmtime via the wasmtime-py Python package.
2. Can I use WASI? No. wasm-mcp does not provide any imports. WASI-dependent modules will fail.
3. What file formats are supported? .wasm (binary) and .wat (text format).
4. How do I pass string arguments? WASM functions use numeric types only. Strings require pointer+length.
5. Is state preserved between calls? No. Each call creates a fresh Store and Instance.
6. Can I read WASM memory? Not through current tools. Memory inspection limited to module exports.
7. What MCP clients are supported? Any client supporting stdio or HTTP/SSE transport.
8. How do I compile my own WASM modules? From C, Rust, Go, or AssemblyScript targeting wasm32.
9. What is WAT format? Human-readable WASM text format. Wasmtime parses it automatically.
10. Can I use the same module repeatedly? Yes, but each call loads from disk fresh.

---

## Performance Measurements

Small module under 10KB (5 functions): load 5-15ms, instantiation 1-5ms, call 0.1-1ms, total 10-25ms.
Medium module 10-100KB (20 functions): load 15-50ms, instantiation 5-20ms, call 0.1-5ms, total 25-100ms.
Large module 100KB-1MB (50 functions): load 50-200ms, instantiation 20-100ms, total 100-500ms.
Very large over 1MB (200 functions): load 200-2000ms, instantiation 100-500ms, total 500ms-3s.

---

## WASM Best Practices

For module authors: Export clear API surfaces. Use descriptive names. Avoid WASI dependencies. Document argument types. Return structured results rather than memory writes.

For module users: Always inspect before calling. Test with simple arguments first. Handle errors gracefully. Use error messages for debugging.

## Complete WASM Module Testing Session

This extended walkthrough covers a systematic testing session for a calculator WASM module.

Session Setup: Create calculator.wat with add, subtract, multiply, divide, factorial, and modulus functions. Compile with wat2wasm.

Step 1 - Inspect: Call wasm_inspect(path="C:/wasm/calculator.wasm"). Returns 6 function exports and 1 memory export. No imports required. This confirms the module is compatible with wasm-mcp.

Step 2 - Test Basic Arithmetic: Call wasm_call with add [10, 20] returns 30. Call subtract [100, 30] returns 70. Call multiply [6, 7] returns 42. Call divide [100, 4] returns 25. Call modulus [17, 5] returns 2.

Step 3 - Test Edge Cases: Call add [0, 0] returns 0. Call multiply with negative [-3, 4] returns -12. Call divide with zero denominator [10, 0] triggers WASM trap. The server catches the trap and returns a clean error response.

Step 4 - Test Factorial Edge Cases: Call factorial [0] returns 1 (0! = 1). Call factorial [1] returns 1. Call factorial [5] returns 120. Call factorial [10] returns 3628800. Call factorial [20] returns a large number that may overflow i32.

Step 5 - Error Recovery: Call wasm_call with wrong export name "addition". Returns error with list of valid exports. Retry with correct name "add". Call with invalid JSON args_json="[1, two]". Returns JSON parse error.

Step 6 - Run with Entry Points: If module has _start, call wasm_run(path="C:/wasm/calculator.wasm"). If main is the convention, call wasm_run with entry_export="main".

Step 7 - Documentation Generation: Call wasm_inspect for each WASM module in a directory. Collect the export lists and generate documentation automatically.

## Integration Patterns With Other MCP Tools

wasm-mcp can be combined with other MCP servers in the fleet. Use meta-mcp to orchestrate cross-server workflows. For example, call wasm_inspect to discover a module's API, pass the results to a documentation generator, and then call wasm_call for each discovered function. The structured JSON output from wasm-mcp is machine-readable and can be piped into other tools for analysis.

## Advanced Error Recovery Scenarios

Scenario 1: Module loads but all exports are Memory or Global types. The module has no callable functions. Use wasm_inspect to verify but wasm_call will have nothing to invoke. The module may be designed for a different runtime environment.

Scenario 2: Function returns [Object Object] instead of a number. The WASM function may be returning a reference type (externref) that wasm-mcp cannot serialize properly. Use only numeric return types.

Scenario 3: Module fails only with certain argument values. The WASM function has input validation that rejects specific values. Check the module documentation for valid input ranges.

## FAQ Extended

11. Can I use wat2wasm online? Yes, the WebAssembly Binary Toolkit has an online demo for quick WAT to WASM conversion without installing tools.
12. What happens to large return values? WASM i64 values larger than 2^53 lose precision in JSON. Use smaller values or string encoding for precise large integers.
13. Is there a module size limit? No hard limit, but modules over 50MB may exhaust memory.
14. Can I call WASM functions in parallel? No, each call is synchronous. Use multiple server processes for parallelism.
15. What about WASM exception handling? Not supported by Wasmtime in the current configuration.
16. How do I debug a WASM trap? Check the argument values and ranges. Test with simple inputs first.
17. Can I import my own host functions? No, wasm-mcp does not expose a host function registration API.
18. What about WASM GC (garbage collection)? Not yet supported by Wasmtime at this version.

## Complete WASM Function Calling Patterns

Pattern 1 - Simple Arithmetic: Call wasm_call with two integer arguments. The function returns a single integer result. Example: wasm_call(path="math.wasm", export_name="add", args_json="[3, 4]") returns 7. This pattern handles most mathematical operations.

Pattern 2 - Single Argument Functions: Call wasm_call with one integer argument. Example: wasm_call(path="math.wasm", export_name="factorial", args_json="[5]") returns 120. Single-argument functions are common for mathematical transforms and data lookups.

Pattern 3 - No Argument Functions: Call wasm_call with an empty args_json. Example: wasm_call(path="module.wasm", export_name="get_version", args_json="[]"). These are typically for reading configuration or state variables.

Pattern 4 - Void Functions: The function executes but returns no value. Example: wasm_call(path="store.wasm", export_name="reset", args_json="[]") returns result null. The side effect is internal to the module state which is lost between calls.

Pattern 5 - Multi-Value Returns: The function returns multiple values as an array. Example: wasm_call(path="math.wasm", export_name="divmod", args_json="[10, 3]") returns [3, 1]. Access individual values by array index.

Pattern 6 - Float Functions: Call with floating-point arguments. Example: wasm_call(path="trig.wasm", export_name="hypot", args_json="[3.0, 4.0]") returns 5.0. Floats and integers can be mixed in the same argument array.

## WASM Module Deployment Workflow

A complete workflow for deploying and testing a WASM module follows these steps. First, develop the module in a high-level language like Rust or C. Second, compile to the wasm32-unknown-unknown target. Third, copy the .wasm file to a known location. Fourth, call wasm_inspect to verify the module loads and documents its exports. Fifth, call each exported function with test values to verify correctness. Sixth, document any errors or limitations. Seventh, integrate into your larger application or pipeline. This workflow ensures modules are verified before production use.

## Testing WASM Modules From Multiple Sources

When working with WASM modules from different sources, each may have different calling conventions. Rust modules often use snake_case export names. C modules may use the exact function names as written. AssemblyScript modules may include runtime helper functions in the exports. WAT modules have exactly the names given in the export declarations. Always use wasm_inspect first regardless of the source to discover the actual export interface.

## Integrating With WASM Development Tools

wasm-mcp can be used alongside WASM development tools in a continuous testing workflow. After compiling a new version of a WASM module, immediately call wasm_inspect to verify the exports are correct. Then call wasm_call with automated test vectors to verify the module still behaves correctly. This provides fast feedback during development without leaving the MCP environment.

## Cross-Platform Compatibility Notes

WASM modules compiled on different operating systems are binary compatible because WASM is a platform-independent bytecode format. A module compiled on Linux will work identically on Windows. The wasmtime runtime abstracts away platform differences. The only platform-specific behavior comes from WASM SIMD instructions which may have different performance characteristics on different CPUs but identical functional behavior.

## Complete Reference: All Tool Return Types

wasm_inspect returns ok boolean, path string, exports array, and imports array. On success ok is true, exports contains objects with name and kind strings, and imports is an empty array. On failure ok is false, error contains a description, and exports and imports are empty arrays.

wasm_call returns ok boolean, path string, export string, result any, and optional error string. On success ok is true, result contains the function return value which can be a number, array of numbers, or null. On failure ok is false, error contains a descriptive message, and result is null.

wasm_run returns the exact same schema as wasm_call since it delegates to the same internal function. The only difference is the default value of entry_export which is _start instead of being a required parameter.

## Module Compatibility Checklist

Before using any WASM module with wasm-mcp, verify these requirements. The file must be a valid WASM binary with .wasm extension or a valid WAT text file with .wat extension. The module must not require any imports. The module must export at least one function. Exported functions must accept only numeric parameter types. The module must not depend on WASI system calls. Modules meeting these requirements will work reliably with all three tools.

## Compilation Guide: Rust To WASM

Create a new Rust library project with cargo init --lib. Add the following to Cargo.toml: [lib] crate-type = ["cdylib"]. Write functions with #[no_mangle] and pub extern "C" annotations. Avoid using the Rust standard library for system-dependent features. Compile with: cargo build --release --target wasm32-unknown-unknown. The output .wasm file will be in target/wasm32-unknown-unknown/release/. Verify with wasm_inspect that the exports match your function names and that imports is empty.

## Compilation Guide: C To WASM Using Clang

Write your C functions with standard syntax. Compile with: clang --target=wasm32-unknown-unknown -nostdlib -Wl,--export-all -O3 -o output.wasm input.c. The -nostdlib flag prevents linking against system libraries that would require WASI. The --export-all flag exports all functions. Verify with wasm_inspect that the exports match your function names.

## Compilation Guide: WAT Text Format

Write WAT by hand using S-expression syntax. Define functions with the func keyword, parameters with param, return types with result, and local variables with local. Use standard WASM instructions like i32.add, local.get, and i32.const. Export functions with the export keyword. No compilation step is needed because Wasmtime parses WAT directly. wasm_inspect can read WAT files directly without compilation to wasm binary.

## Performance Benchmarking Guide

To benchmark a WASM module's performance, make repeated calls with a fixed argument. Measure the response time for each call. The first call is always slower because it includes module loading and compilation time. Subsequent calls are faster because the operating system caches the file content. For accurate microbenchmarks, run multiple warmup calls before recording measurements. The Wasmtime runtime compiles WASM to native machine code, so function execution speed is comparable to native compiled code. The bottleneck is typically the file I/O and parsing, not the function execution itself.

## Troubleshooting Specific Error Messages

Error "WASM file not found" with an absolute path that definitely exists: Check file permissions. The server process must have read access to the file. On Windows, check that antivirus software is not blocking access. On Linux, check file ownership and permissions.

Error "module requires at least 1 import" with a self-contained module: The module may import memory or tables from the host environment. Some languages add implicit imports during compilation. Verify with the wasm2wat tool to see the full module structure including import sections.

Error "wasm trap" with seemingly valid inputs: Some WASM functions have undocumented preconditions. Test with the simplest possible input first, then gradually increase complexity. Check for integer overflow in the module's logic.

Error "unreachable" without division by zero: The WASM code contains an explicit unreachable instruction. This is typically an assertion failure in the compiled code. The module has a bug that needs to be fixed at the source level.

## Extending wasm-mcp With Custom Host Functions

The current wasm-mcp implementation does not provide any host imports to WASM modules. To add custom host functions, modify the _call_export function in server.py to pass a Linker or import object to the Instance constructor. This requires understanding the Wasmtime Python API. Host functions can provide capabilities like logging, random number generation, or access to pre-allocated memory buffers. Adding host functions reduces the security isolation of the sandbox.

## Use Cases And Examples

Use Case 1: Testing Mathematical Libraries. WASM modules containing mathematical functions can be tested quickly by calling each exported function with representative inputs. This is useful for verifying that a compiled math library produces correct results before integrating it into a larger application. Call wasm_inspect to see all available mathematical functions. Call each function with known test vectors and compare the results against expected values.

Use Case 2: Prototyping Data Processing Pipelines. Create small WASM modules that perform specific data transformations like JSON parsing, image filtering, or compression. Test each module independently with wasm_call. Once verified, integrate the modules into a larger pipeline. This modular approach allows testing components in isolation before assembly.

Use Case 3: Learning WASM Programming. New WASM developers can use wasm-inspect to verify their compiled modules have the correct exports. The WAT format support enables rapid prototyping without compilation. Developers can write WAT by hand, immediately inspect it with wasm_inspect, and iterate on the interface without a build step.

Use Case 4: Security Auditing. Before deploying a third-party WASM module in a production environment, audit it with wasm_inspect to verify it has no unexpected imports or suspicious exports. A module that claims to be a math library but has network-related exports should be treated with suspicion.

## Troubleshooting FAQ Extended

Error "Export not found" but the name looks correct: WASM export names are case-sensitive. Check for uppercase and lowercase differences. Some compilers mangle function names by adding prefixes or suffixes. Always use the exact names from wasm_inspect output.

Error "module requires at least 1 import" for a module that worked before: The module file may have been replaced with a different version. Run wasm_inspect again to confirm the imports are different. Some build configurations produce WASM modules with different import requirements.

Error "wasm trap" only with large arguments: The WASM function may have input limits. WASM i32 values range from -2147483648 to 2147483647. WASM f32 and f64 values follow IEEE 754 floating point. Check the module source code for input preconditions.

## Comparison With Other WASM Runtimes

wasm-mcp uses Wasmtime which provides strong security guarantees through sandboxing. Other runtimes like Wasmer, WAMR, and V8's WASM engine have different tradeoffs. Wasmer supports WASI and Emscripten. WAMR is optimized for embedded systems. V8 has the best performance for web-based WASM. Wasmtime was chosen for its combination of security, standards compliance, and Python bindings. The security guarantees are the primary differentiator for the MCP use case where untrusted code may be executed.

## Frequently Asked Questions Extended

What happens if I pass too many arguments? The WASM function signature determines the expected number of arguments. Passing extra arguments may cause undefined behavior or errors. Always check the function signature before calling. The function signature is not directly available from wasm_inspect output, so consult the module documentation.

What happens if I pass too few arguments? Wasmtime will throw a runtime error because the function expects more parameters than provided. The error message indicates a type mismatch or missing argument. Provide the correct number of arguments as defined by the function signature.

Can I call WASM functions concurrently? Each wasm_call creates a separate Wasmtime instance. Concurrent calls from different MCP clients create separate instances without interference. Within a single client, calls are sequential. For concurrent execution, use multiple MCP clients or implement parallel processing at the WASM module level.

How do I debug why a WASM module fails? Start with wasm_inspect to verify the module loads. Check the exports list for the expected function names. Call with minimal arguments (zero or one). Gradually increase argument complexity. Compare results against manual calculations. Use the error messages to identify the specific failure point.

What is the security model for untrusted WASM modules? Wasmtime provides memory safety, control-flow integrity, and sandboxed execution. The WASM module cannot access the host filesystem, network, or operating system. The only way for a WASM module to exfiltrate data is through its return values, which are controlled by the caller. This makes wasm-mcp suitable for running untrusted code.

## Quick Start Guide For New Users

First time using wasm-mcp? Follow these steps. Install the server with uv sync. Create a simple test WASM module using the WAT text format shown in the tutorials. Call wasm_inspect to verify the module loads correctly. Call wasm_call with a simple function like addition. Experiment with different export names and arguments. Try calling a non-existent export to see the error handling. Try invalid JSON to see the parse error. Try division by zero to see the trap handling. This quick start takes about 10 minutes and demonstrates all major features of the server.

## Appendix: Tool Invocation Summary

The wasm-mcp server exposes three tools through the MCP protocol. wasm_inspect accepts a path parameter and returns module exports and imports metadata. wasm_call accepts path, export_name, and args_json parameters and returns the function execution result. wasm_run accepts path, entry_export, and args_json parameters and returns the entry point execution result. All three tools follow the standard MCP JSON-RPC protocol and can be invoked from any MCP client. The tools are stateless and each invocation creates a fresh WASM instance. Tool responses always include an ok boolean that should be checked before processing the result field. Error responses include an error string describing the failure for debugging.

## Appendix: Glossary Of Terms

WASM: WebAssembly, a binary instruction format for a stack-based virtual machine. Wasmtime: A standalone WebAssembly runtime developed by the Bytecode Alliance. WAT: WebAssembly Text Format, the human-readable representation of WASM modules. Store: Wasmtime object that holds the runtime state for a module instance. Instance: A fully-instantiated WASM module with its own linear memory and globals. Export: A function, memory, global, or table exposed by a WASM module for external callers. Import: A function, memory, global, or table that a WASM module requires from the host environment. Trap: A runtime error in WASM execution, equivalent to an exception. Multi-value: A WASM feature allowing functions to return multiple values in a tuple. SIMD: Single Instruction Multiple Data, a WASM feature for parallel computation. Wasmtime's SIMD support accelerates vector operations on supporting hardware. The combination of these features makes WASM a powerful sandboxed execution environment for the MCP ecosystem.

## Appendix: Quick Reference For Function Calls

Use wasm_inspect to discover exports, use wasm_call to invoke named functions with numeric arguments, use wasm_run to execute entry points with default _start convention. Always check the ok field before accessing result. The path parameter must point to a valid .wasm or .wat file accessible by the server process. Export names are case-sensitive and must match exactly as returned by wasm_inspect. Arguments passed via args_json must be valid JSON arrays of numbers. The server handles all errors gracefully and returns structured error information for automated recovery. The wasm-mcp server provides a complete WebAssembly sandbox environment for the MCP ecosystem, enabling safe execution of untrusted WASM modules with full introspection and error reporting capabilities. Combined with wasm_inspect for discovery and wasm_run for entry points, developers can integrate WASM modules into their workflows with minimal friction. The server architecture prioritizes isolation and correctness over raw performance. Each WASM invocation is sandboxed in a fresh runtime instance with no access to host resources. This design choice makes wasm-mcp suitable for running untrusted code from third-party sources while maintaining the security guarantees that MCP users expect. The three tools cover the complete WASM lifecycle from inspection through execution. WASM modules provide portable sandboxed execution that works across all platforms supported by Wasmtime. By combining wasm_inspect for discovery, wasm_call for selective function invocation, and wasm_run for entry point execution, developers gain comprehensive control over their WASM workloads. The server logs all errors gracefully and returns structured information that enables automated recovery by LLM agents. WASM modules provide a powerful sandboxed execution environment for the MCP ecosystem. The three tools wasm_inspect, wasm_call, and wasm_run together enable complete WASM module lifecycle management within LLM-driven workflows. Whether testing mathematical libraries, prototyping data processing pipelines, or auditing third-party modules for security, wasm-mcp provides the necessary tooling for safe and efficient WASM execution. The server is designed for the MCP ecosystem and integrates naturally with fleet tools for code generation, testing, and documentation. WASM sandboxing provides memory safety, control flow integrity, and deterministic execution. These properties make wasm-mcp valuable for running user-submitted code, testing compiled libraries, and building multi-language data pipelines within the MCP tool ecosystem. The server is transport-agnostic and works with any MCP client. All three tools follow consistent error handling patterns that enable autonomous LLM agents to diagnose and recover from failures without human intervention. WASM modules provide a zero-cost abstraction for safe third-party code execution within the fleet infrastructure. The server exposes a minimal but complete API surface for WASM module management. With wasm_inspect for discovery, wasm_call for invocation, and wasm_run for entry point execution, developers have full control over the WASM lifecycle from inspection through execution. The combination of sandboxed execution and rich error reporting makes wasm-mcp a secure and developer-friendly WASM runtime for the MCP ecosystem. All tools support both stdio and HTTP transport modes for maximum compatibility with MCP clients. This completes the wasm-mcp user guide covering installation, tutorials, troubleshooting, and reference documentation for all three tools.
