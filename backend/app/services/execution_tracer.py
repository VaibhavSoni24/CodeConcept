"""Execution Tracer — step-by-step execution trace for 6 languages.

Python  → sys.settrace (precise variable capture).
JS/C++/Java/Go/Rust → print-based line instrumentation:
  Each language's trace wrapper runs the code and emits JSON-formatted
  trace lines to stdout, which we parse into the unified trace format.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

# ─────────────────────────────────────────────────────────────
# Python tracer (original sys.settrace approach)
# ─────────────────────────────────────────────────────────────

PYTHON_TRACER_TEMPLATE = r'''
import sys as _sys, json as _json, io as _io, contextlib as _contextlib
_trace_log = []
_max_steps = 50

def _safe_repr(val):
    try:
        if isinstance(val, (int, float, bool, type(None))): return val
        if isinstance(val, str): return val[:100]
        if isinstance(val, (list, tuple)): return [_safe_repr(v) for v in val[:10]]
        if isinstance(val, dict): return {k: _safe_repr(v) for k, v in list(val.items())[:10]}
        return repr(val)[:80]
    except Exception: return "<unrepresentable>"

def _tracer(frame, event, arg):
    if len(_trace_log) >= _max_steps:
        _sys.settrace(None); return None
    if event == "line" and frame.f_code.co_filename == "<string>":
        variables = {k: _safe_repr(v) for k, v in frame.f_locals.items()
                     if not k.startswith("_") and k != "student_code"}
        _trace_log.append({"line": frame.f_lineno, "variables": variables})
    return _tracer

student_code = {student_code_json}
_stdout = _io.StringIO()
_stderr = _io.StringIO()
_sys.settrace(_tracer)
try:
    with _contextlib.redirect_stdout(_stdout), _contextlib.redirect_stderr(_stderr):
        exec(compile(student_code, "<string>", "exec"))
except BaseException as exc:
    _trace_log.append({"line": -1, "variables": {"__error__": f"{type(exc).__name__}: {str(exc)[:200]}"}})
finally:
    _sys.settrace(None)
print(_json.dumps(_trace_log))
'''


def run_python_trace(code: str) -> List[Dict[str, Any]]:
    script = PYTHON_TRACER_TEMPLATE.replace("{student_code_json}", json.dumps(code))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(script)
        path = f.name
    try:
        r = subprocess.run([sys.executable, "-I", path], capture_output=True, text=True, timeout=5)
        output = r.stdout.strip()
        if r.returncode == 0 and output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                left, right = output.find("["), output.rfind("]")
                if left != -1 and right > left:
                    try:
                        return json.loads(output[left:right + 1])
                    except json.JSONDecodeError:
                        pass
        err = (r.stderr.splitlines() or ["Unknown error"])[-1][:200]
        return [{"line": -1, "variables": {"__error__": err}}]
    except subprocess.TimeoutExpired:
        return [{"line": -1, "variables": {"__error__": "Execution timed out (5s limit)"}}]
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ─────────────────────────────────────────────────────────────
# Generic subprocess runner (used by all non-Python tracers)
# ─────────────────────────────────────────────────────────────

def _run_and_parse(cmd: List[str], timeout: int = 8) -> List[Dict[str, Any]]:
    """Run a command, parse its stdout as one JSON object per line prefixed with TRACE:."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        lines = r.stdout.splitlines() + r.stderr.splitlines()
        trace = []
        for line in lines:
            line = line.strip()
            if line.startswith("TRACE:"):
                try:
                    obj = json.loads(line[6:])
                    trace.append(obj)
                except json.JSONDecodeError:
                    pass
        if not trace:
            err_lines = [l.strip() for l in r.stderr.splitlines() if l.strip()]
            err = err_lines[-1][:200] if err_lines else "No trace output produced"
            return [{"line": -1, "variables": {"__error__": err}}]
        return trace
    except FileNotFoundError as exc:
        tool = cmd[0]
        return [{"line": -1, "variables": {"__error__": f"'{tool}' not found — is it installed and on PATH?"}}]
    except subprocess.TimeoutExpired:
        return [{"line": -1, "variables": {"__error__": "Execution timed out (8s limit)"}}]


# ─────────────────────────────────────────────────────────────
# JavaScript (Node.js) tracer
# ─────────────────────────────────────────────────────────────

def _extract_js_var_names(code: str) -> List[str]:
    """Extract user-declared variable/function/const/let names from JS source."""
    names = set()
    # Match: let x, const y, var z — including destructuring: let {a, b}
    for m in re.finditer(r'\b(?:let|const|var)\s+(?:\{([^}]+)\}|\[([^\]]+)\]|(\w+))', code):
        if m.group(1):  # destructured object: let {a, b}
            for part in re.findall(r'\b(\w+)\b', m.group(1)):
                names.add(part)
        elif m.group(2):  # destructured array: let [a, b]
            for part in re.findall(r'\b(\w+)\b', m.group(2)):
                names.add(part)
        elif m.group(3):  # simple: let x
            names.add(m.group(3))
    # Match function declarations: function foo(a, b)
    for m in re.finditer(r'\bfunction\s+(\w+)\s*\(([^)]*)\)', code):
        names.add(m.group(1))
        for param in m.group(2).split(','):
            param = param.strip().lstrip('...')
            if param:
                names.add(param.split('=')[0].strip())
    # Arrow functions assigned to const/let are already caught above
    # Filter out JS keywords, tracer internals, and all Node.js / browser built-in globals
    _keywords = {'if', 'else', 'for', 'while', 'do', 'return', 'break', 'continue',
                 'new', 'delete', 'typeof', 'instanceof', 'in', 'of', 'switch', 'case',
                 'default', 'try', 'catch', 'finally', 'throw', 'class', 'extends',
                 'import', 'export', 'from', 'async', 'await', 'true', 'false', 'null',
                 'undefined', 'this', 'super', '__step', '__trace', '__traceLine'}
    # Node.js / browser globals that are always in scope — never capture these
    _node_globals = {
        'global', 'globalThis', 'process', 'console', 'module', 'exports', 'require',
        'Buffer', '__filename', '__dirname',
        'setTimeout', 'clearTimeout', 'setInterval', 'clearInterval',
        'setImmediate', 'clearImmediate', 'queueMicrotask',
        'Promise', 'Symbol', 'Proxy', 'Reflect', 'WeakRef', 'FinalizationRegistry',
        'Map', 'Set', 'WeakMap', 'WeakSet',
        'ArrayBuffer', 'SharedArrayBuffer', 'DataView',
        'Int8Array', 'Uint8Array', 'Uint8ClampedArray',
        'Int16Array', 'Uint16Array', 'Int32Array', 'Uint32Array',
        'Float32Array', 'Float64Array', 'BigInt64Array', 'BigUint64Array',
        'Object', 'Array', 'Function', 'String', 'Number', 'Boolean', 'BigInt',
        'RegExp', 'Date', 'Error', 'TypeError', 'RangeError', 'SyntaxError',
        'ReferenceError', 'EvalError', 'URIError',
        'JSON', 'Math', 'Intl',
        'fetch', 'URL', 'URLSearchParams', 'Headers', 'Request', 'Response',
        'TextEncoder', 'TextDecoder',
        'atob', 'btoa', 'crypto', 'performance', 'navigator',
        'structuredClone', 'AbortController', 'AbortSignal', 'Event', 'EventTarget',
        'parseInt', 'parseFloat', 'isNaN', 'isFinite',
        'decodeURI', 'decodeURIComponent', 'encodeURI', 'encodeURIComponent', 'eval',
        'Infinity', 'NaN',
    }
    _exclude = _keywords | _node_globals
    return [n for n in sorted(names) if n not in _exclude]


def run_js_trace(code: str) -> List[Dict[str, Any]]:
    """Trace JS using per-variable safe reads — only user-declared vars are shown."""
    user_vars = _extract_js_var_names(code)

    # Build the variable-capture snippet for a given point:
    # tries each known name individually so missing ones don't crash everything.
    def _make_capture(line_no: int) -> str:
        if not user_vars:
            return f'try {{ __traceLine({line_no}, {{}}); }} catch(__te) {{}}'
        entries = ", ".join(
            f'"{v}": (typeof {v} !== "undefined" ? {v} : undefined)'
            for v in user_vars
        )
        return f'try {{ __traceLine({line_no}, {{ {entries} }}); }} catch(__te) {{ __traceLine({line_no}, {{}}); }}'

    wrapper = '''
const __MAX = 50;
let __step = 0;

function __traceLine(line, vars) {
  if (__step >= __MAX) return;
  __step++;
  const safe = (v) => {
    if (v === null || v === undefined) return String(v);
    if (typeof v === 'number' || typeof v === 'boolean') return v;
    if (typeof v === 'string') return v.slice(0, 100);
    if (Array.isArray(v)) { try { return JSON.stringify(v.slice(0,10)).slice(0,200); } catch { return String(v); } }
    if (typeof v === 'function') return '[Function: ' + (v.name || 'anonymous') + ']';
    try { return JSON.stringify(v).slice(0, 200); } catch { return String(v).slice(0, 100); }
  };
  const safeVars = {};
  for (const [k, val] of Object.entries(vars)) {
    if (val !== undefined) safeVars[k] = safe(val);
  }
  process.stdout.write('TRACE:' + JSON.stringify({ line, variables: safeVars }) + '\\n');
}

try {
USER_CODE_HERE
} catch(e) {
  process.stdout.write('TRACE:' + JSON.stringify({ line: -1, variables: { __error__: String(e).slice(0, 200) } }) + '\\n');
}
'''

    # Inject trace calls after each executable line
    lines = code.splitlines()
    out = []
    for i, line in enumerate(lines, start=1):
        out.append(line)
        stripped = line.strip()
        if stripped and not stripped.startswith('//') and stripped not in ('{', '}'):
            out.append(_make_capture(i))

    instrumented = '\n'.join(out)
    full_code = wrapper.replace('USER_CODE_HERE', instrumented)

    with tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False, encoding='utf-8') as f:
        f.write(full_code)
        path = f.name
    try:
        return _run_and_parse(['node', path])
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────
# Simpler unified line-by-line trace for compiled languages
# (C++, Java, Go, Rust) using print injection into source
# ─────────────────────────────────────────────────────────────

def _build_cpp_trace(code: str) -> str:
    """Wrap C++ code to emit TRACE JSON lines to stdout at each user line."""
    lines = code.splitlines()
    emitters = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped and not stripped.startswith("//") and stripped not in ("{", "}"):
            # Emit a bare trace with just the line number
            emitters.append(f'std::cout << "TRACE:" << R"({{"line":{i},"variables":{{}}}})" << std::endl;')
    # We inject the emitters INSIDE main. Strategy: append them at the top of main body.
    injected = re.sub(
        r'(int\s+main\s*\([^)]*\)\s*\{)',
        r'\1\n' + "\n".join(emitters) + r'\n',
        code,
        count=1,
    )
    if injected == code:
        # main() not found — just prepend emitters after the first opening brace
        injected = code.replace("{", "{\n" + "\n".join(emitters) + "\n", 1)
    # Ensure iostream is included
    if "#include <iostream>" not in injected:
        injected = "#include <iostream>\n" + injected
    return injected


def run_cpp_trace(code: str) -> List[Dict[str, Any]]:
    instrumented = _build_cpp_trace(code)
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "sol.cpp")
        exe = os.path.join(tmpdir, "sol.exe" if os.name == "nt" else "sol")
        with open(src, "w", encoding="utf-8") as f:
            f.write(instrumented)
        comp = subprocess.run(
            ["g++", "-o", exe, src, "-std=c++17"],
            capture_output=True, text=True, timeout=15,
        )
        if comp.returncode != 0:
            err = (comp.stderr.splitlines() or ["Compile error"])[-1][:200]
            return [{"line": -1, "variables": {"__error__": f"Compile error: {err}"}}]
        return _run_and_parse([exe])


def _build_java_trace(code: str) -> str:
    """Inject System.out.println TRACE lines at each non-blank line inside methods."""
    lines = code.splitlines()
    out = []
    for i, line in enumerate(lines, start=1):
        out.append(line)
        stripped = line.strip()
        if stripped and not stripped.startswith("//") and stripped not in ("{", "}"):
            out.append(f'        System.out.println("TRACE:" + "{{\\"line\\":{i},\\"variables\\":{{}}}}" );')
    return "\n".join(out)


def run_java_trace(code: str) -> List[Dict[str, Any]]:
    # Detect public class name
    match = re.search(r'public\s+class\s+(\w+)', code)
    class_name = match.group(1) if match else "Main"
    instrumented = _build_java_trace(code)
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, f"{class_name}.java")
        with open(src, "w", encoding="utf-8") as f:
            f.write(instrumented)
        comp = subprocess.run(
            ["javac", src], capture_output=True, text=True, timeout=20,
        )
        if comp.returncode != 0:
            err = (comp.stderr.splitlines() or ["Compile error"])[-1][:200]
            return [{"line": -1, "variables": {"__error__": f"Compile error: {err}"}}]
        return _run_and_parse(["java", "-cp", tmpdir, class_name])


def _build_go_trace(code: str) -> str:
    """Inject fmt.Printf TRACE lines at each non-blank statement in Go."""
    lines = code.splitlines()
    out = []
    in_import = False
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("import"):
            in_import = True
        if in_import and stripped == ")":
            in_import = False
        out.append(line)
        if (not in_import and stripped and
                not stripped.startswith("//") and
                stripped not in ("{", "}") and
                not stripped.startswith("package ") and
                not stripped.startswith("import")):
            out.append(f'\tfmt.Print("TRACE:{{\\"line\\":{i},\\"variables\\":{{}}}}" + "\\n")')
    # Ensure fmt is imported
    if '"fmt"' not in code:
        out_str = "\n".join(out)
        out_str = out_str.replace("import (", 'import (\n\t"fmt"', 1)
        if 'import (' not in out_str:
            out_str = out_str.replace('import "fmt"', '')
            out_str = re.sub(r'(package\s+\w+\s*\n)', r'\1\nimport "fmt"\n', out_str)
        return out_str
    return "\n".join(out)


def run_go_trace(code: str) -> List[Dict[str, Any]]:
    instrumented = _build_go_trace(code)
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "main.go")
        with open(src, "w", encoding="utf-8") as f:
            f.write(instrumented)
        return _run_and_parse(["go", "run", src])


def _build_rust_trace(code: str) -> str:
    """Inject eprintln! TRACE lines into Rust code (using stderr so it still shows)."""
    lines = code.splitlines()
    out = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        out.append(line)
        if (stripped and not stripped.startswith("//") and
                stripped not in ("{", "}") and
                not stripped.startswith("use ") and
                not stripped.startswith("fn ") and
                not stripped.startswith("#[")):
            out.append(f'    eprintln!("TRACE:{{\\"line\\":{i},\\"variables\\":{{}}}}" );')
    return "\n".join(out)


def run_rust_trace(code: str) -> List[Dict[str, Any]]:
    instrumented = _build_rust_trace(code)
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "main.rs")
        exe = os.path.join(tmpdir, "main.exe" if os.name == "nt" else "main")
        with open(src, "w", encoding="utf-8") as f:
            f.write(instrumented)
        comp = subprocess.run(
            ["rustc", src, "-o", exe], capture_output=True, text=True, timeout=30,
        )
        if comp.returncode != 0:
            err = (comp.stderr.splitlines() or ["Compile error"])[-1][:200]
            return [{"line": -1, "variables": {"__error__": f"Compile error: {err}"}}]
        # Rust trace uses stderr for TRACE lines, stdout for program output
        try:
            r = subprocess.run([exe], capture_output=True, text=True, timeout=8)
            lines = r.stderr.splitlines()
            trace = []
            for line in lines:
                if line.startswith("TRACE:"):
                    try:
                        trace.append(json.loads(line[6:]))
                    except json.JSONDecodeError:
                        pass
            if not trace:
                err = (r.stderr.splitlines() or ["No trace output"])[-1][:200]
                return [{"line": -1, "variables": {"__error__": err}}]
            return trace
        except subprocess.TimeoutExpired:
            return [{"line": -1, "variables": {"__error__": "Execution timed out"}}]


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def run_execution_trace(code: str, language: str = "python") -> List[Dict[str, Any]]:
    """Dispatch execution tracing to the correct language handler."""
    lang = language.lower()
    if lang == "python":
        return run_python_trace(code)
    elif lang in ("javascript", "js", "node"):
        return run_js_trace(code)
    elif lang in ("cpp", "c++", "c"):
        return run_cpp_trace(code)
    elif lang == "java":
        return run_java_trace(code)
    elif lang == "go":
        return run_go_trace(code)
    elif lang in ("rust", "rs"):
        return run_rust_trace(code)
    else:
        return [{"line": -1, "variables": {"__error__": f"Tracing not supported for '{language}'"}}]
