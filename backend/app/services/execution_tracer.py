"""Execution Tracer — step-by-step execution trace for 6 languages.

Python  -> sys.settrace (precise variable capture).
JS/C++/Java/Go/Rust -> print-based line instrumentation:
  Each language's trace wrapper runs the code and emits JSON-formatted
  trace lines to stdout (or stderr for Rust), which we parse into the
  unified trace format.
"""

import json
import math
import os
import re
import subprocess
import sys
import tempfile
from typing import Any, Dict, List


def _sanitize_json_value(value: Any) -> Any:
    """Recursively convert non-JSON-safe values to safe representations."""
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return value
    if isinstance(value, list):
        return [_sanitize_json_value(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize_json_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _sanitize_json_value(v) for k, v in value.items()}
    return value

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
            err_lines = [ln.strip() for ln in r.stderr.splitlines() if ln.strip()]
            err = err_lines[-1][:200] if err_lines else "No trace output produced"
            return [{"line": -1, "variables": {"__error__": err}}]
        return trace
    except FileNotFoundError:
        tool = cmd[0]
        return [{"line": -1, "variables": {"__error__": "'" + tool + "' not found — is it installed and on PATH?"}}]
    except subprocess.TimeoutExpired:
        return [{"line": -1, "variables": {"__error__": "Execution timed out (8s limit)"}}]


# ─────────────────────────────────────────────────────────────
# JavaScript (Node.js) tracer
# ─────────────────────────────────────────────────────────────

def _extract_js_var_names(code: str) -> List[str]:
    """Extract user-declared variable/function/const/let names from JS source."""
    names: set = set()
    for m in re.finditer(r'\b(?:let|const|var)\s+(?:\{([^}]+)\}|\[([^\]]+)\]|(\w+))', code):
        if m.group(1):
            for part in re.findall(r'\b(\w+)\b', m.group(1)):
                names.add(part)
        elif m.group(2):
            for part in re.findall(r'\b(\w+)\b', m.group(2)):
                names.add(part)
        elif m.group(3):
            names.add(m.group(3))
    for m in re.finditer(r'\bfunction\s+(\w+)\s*\(([^)]*)\)', code):
        names.add(m.group(1))
        for param in m.group(2).split(','):
            param = param.strip().lstrip('...')
            if param:
                names.add(param.split('=')[0].strip())
    _keywords = {
        'if', 'else', 'for', 'while', 'do', 'return', 'break', 'continue',
        'new', 'delete', 'typeof', 'instanceof', 'in', 'of', 'switch', 'case',
        'default', 'try', 'catch', 'finally', 'throw', 'class', 'extends',
        'import', 'export', 'from', 'async', 'await', 'true', 'false', 'null',
        'undefined', 'this', 'super', '__step', '__trace', '__traceLine',
    }
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

    def _make_capture(line_no: int) -> str:
        if not user_vars:
            return 'try { __traceLine(' + str(line_no) + ', {}); } catch(__te) {}'
        entries = ", ".join(
            '"' + v + '": (typeof ' + v + ' !== "undefined" ? ' + v + ' : undefined)'
            for v in user_vars
        )
        return ('try { __traceLine(' + str(line_no) + ', { ' + entries + ' }); } '
                'catch(__te) { __traceLine(' + str(line_no) + ', {}); }')

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


# ─────────────────────────────────────────────────────────────
# C++ tracer
# ─────────────────────────────────────────────────────────────

def _build_cpp_trace(code: str) -> str:
    """Instrument C++ to emit TRACE JSON with variable values after each statement.

    Uses brace-depth tracking to determine which variables are currently in scope.
    For-loop variables (int i) are assigned to depth+1 so they're only emitted
    inside the loop body.
    All code strings are built via Python concatenation to avoid f-string brace conflicts.
    """
    lines = code.splitlines()

    # ── Pass 1: find all declared variables and the brace-depth at declaration ──
    _decl_re = re.compile(
        r'\b(?:int|long|short|unsigned|float|double|char|bool|string|auto|size_t)'
        r'(?:\s*[*&])?\s+(\w+)\s*[=;(,\[]'
    )
    _for_re = re.compile(r'\bfor\s*\(\s*(?:int|long|auto|size_t|unsigned)\s+(\w+)')
    _cpp_kw = {
        'if', 'else', 'for', 'while', 'do', 'return', 'break', 'continue',
        'new', 'delete', 'class', 'struct', 'namespace', 'using',
        'public', 'private', 'protected', 'static', 'const', 'void',
        'main', 'endl', 'cout', 'cin', 'cerr',
    }
    var_decl_depth: Dict[str, int] = {}
    depth = 0
    for line in lines:
        stripped = line.strip()
        # For-loop variables are scoped inside the block that follows (depth + 1)
        for m in _for_re.finditer(stripped):
            name = m.group(1)
            if name not in _cpp_kw:
                var_decl_depth[name] = depth + 1
        # Regular variable declarations at current depth
        for m in _decl_re.finditer(stripped):
            name = m.group(1)
            if name not in _cpp_kw and name not in var_decl_depth:
                var_decl_depth[name] = depth
        depth += stripped.count('{') - stripped.count('}')

    # ── Pass 2: build the instrumented source ──
    _skip_re = re.compile(
        r'^(class|struct|namespace|using|void\s+\w|int\s+main|'
        r'[a-zA-Z_]\w*\s+[a-zA-Z_]\w*\s*\()'
    )
    out = []
    depth = 0
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Update depth BEFORE appending so the depth reflects the current nesting
        depth += stripped.count('{') - stripped.count('}')
        out.append(line)

        if (not stripped
                or stripped.startswith('//')
                or stripped.startswith('#')
                or stripped in ('{', '}')
                or _skip_re.match(stripped)):
            continue

        # Determine which variables are in scope right now
        in_scope = [v for v, d in sorted(var_decl_depth.items()) if depth >= d]

        line_str = str(i)
        if in_scope:
            # Build each kv pair as:  "\"name\": \"" << (var) << "\""
            kv_segs = []
            for v in in_scope:
                kv_segs.append('"\\\"' + v + '\\\": \\\"" << (' + v + ') << "\\\"" ')
            kv_chain = ' << "," << '.join(kv_segs)
            emit = (
                'std::cout << "TRACE:{\\\"line\\\":' + line_str
                + ',\\\"variables\\\":{" << ' + kv_chain
                + ' << "}}"; std::cout << std::endl;'
            )
        else:
            emit = (
                'std::cout << "TRACE:{\\\"line\\\":' + line_str
                + ',\\\"variables\\\":{}}" << std::endl;'
            )

        out.append('  ' + emit)

    result = '\n'.join(out)
    if '#include <iostream>' not in result:
        result = '#include <iostream>\n' + result
    return result


def run_cpp_trace(code: str) -> List[Dict[str, Any]]:
    instrumented = _build_cpp_trace(code)
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "sol.cpp")
        exe = os.path.join(tmpdir, "sol.exe" if os.name == "nt" else "sol")
        with open(src, "w", encoding="utf-8") as f:
            f.write(instrumented)
        try:
            comp = subprocess.run(
                ["g++", "-o", exe, src, "-std=c++17"],
                capture_output=True, text=True, timeout=15,
            )
        except FileNotFoundError:
            return [{"line": -1, "variables": {"__error__": "'g++' not found. Is it installed and on PATH?"}}]
        if comp.returncode != 0:
            err = (comp.stderr.splitlines() or ["Compile error"])[-1][:200]
            return [{"line": -1, "variables": {"__error__": "Compile error: " + err}}]
        return _run_and_parse([exe])


# ─────────────────────────────────────────────────────────────
# Java tracer
# ─────────────────────────────────────────────────────────────

def _extract_java_vars(code: str) -> List[str]:
    """Extract user-declared local variable names from Java source."""
    names: set = set()
    for m in re.finditer(
        r'\b(?:int|long|short|byte|float|double|char|boolean|String|var|Integer|Double|Long)'
        r'(?:\[\])?\s+(\w+)\s*[=;(,\[]',
        code
    ):
        names.add(m.group(1))
    for m in re.finditer(r'\bfor\s*\(\s*(?:int|long|var)\s+(\w+)', code):
        names.add(m.group(1))
    _exclude = {
        'if', 'else', 'for', 'while', 'do', 'return', 'break', 'continue',
        'new', 'class', 'public', 'private', 'protected', 'static', 'void',
        'main', 'args', 'System',
    }
    return [n for n in sorted(names) if n not in _exclude]


def _build_java_trace(code: str) -> str:
    """Inject System.out.println TRACE lines with variable values after each statement."""
    user_vars = _extract_java_vars(code)
    lines = code.splitlines()
    out = []
    _skip_re = re.compile(r'^(public|private|protected|class|import|package|@)')

    for i, line in enumerate(lines, start=1):
        out.append(line)
        stripped = line.strip()

        if (not stripped
                or stripped.startswith('//')
                or stripped in ('{', '}')
                or _skip_re.match(stripped)):
            continue

        line_str = str(i)
        if user_vars:
            # Build JSON via String concat: "\"name\": \"" + var + "\""
            kv_parts = []
            for v in user_vars:
                kv_parts.append('"\\\"' + v + '\\\": \\\"" + ' + v + ' + "\\\"" ')
            kv_str = ' + "," + '.join(kv_parts)
            emit = (
                '        try { System.out.println("TRACE:{\\\"line\\\":' + line_str
                + ',\\\"variables\\\":{" + ' + kv_str
                + ' + "}}"); }'
                + ' catch (Exception __te) { System.out.println("TRACE:{\\\"line\\\":' + line_str
                + ',\\\"variables\\\": {}}"); }'
            )
        else:
            emit = (
                '        System.out.println("TRACE:{\\\"line\\\":' + line_str
                + ',\\\"variables\\\": {}}");'
            )

        out.append(emit)

    return "\n".join(out)


def run_java_trace(code: str) -> List[Dict[str, Any]]:
    match = re.search(r'public\s+class\s+(\w+)', code)
    class_name = match.group(1) if match else "Main"
    instrumented = _build_java_trace(code)
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, class_name + ".java")
        with open(src, "w", encoding="utf-8") as f:
            f.write(instrumented)
        try:
            comp = subprocess.run(
                ["javac", src], capture_output=True, text=True, timeout=20,
            )
        except FileNotFoundError:
            return [{"line": -1, "variables": {"__error__": "'javac' not found. Is Java installed and on PATH?"}}]
        if comp.returncode != 0:
            err = (comp.stderr.splitlines() or ["Compile error"])[-1][:200]
            return [{"line": -1, "variables": {"__error__": "Compile error: " + err}}]
        return _run_and_parse(["java", "-cp", tmpdir, class_name])


# ─────────────────────────────────────────────────────────────
# Go tracer
# ─────────────────────────────────────────────────────────────

def _extract_go_vars(code: str) -> List[str]:
    """Extract user-declared variable names from Go source."""
    names: set = set()
    for m in re.finditer(r'\b(\w+)\s*:=', code):
        names.add(m.group(1))
    for m in re.finditer(r'\bvar\s+(\w+)\s+\w+', code):
        names.add(m.group(1))
    for m in re.finditer(r'\bfor\s+(\w+)\s*:=', code):
        names.add(m.group(1))
    _exclude = {
        'if', 'else', 'for', 'range', 'return', 'break', 'continue',
        'fmt', 'err', 'main', '_',
    }
    return [n for n in sorted(names) if n not in _exclude]


def _build_go_trace(code: str) -> str:
    """Inject fmt.Printf TRACE lines with variable values after each statement in Go."""
    user_vars = _extract_go_vars(code)
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

        if (in_import
                or not stripped
                or stripped.startswith("//")
                or stripped in ("{", "}")
                or stripped.startswith("package ")
                or stripped.startswith("import")
                or stripped.startswith("func ")
                or stripped.startswith("type ")):
            continue

        line_str = str(i)
        if user_vars:
            # fmt.Printf with %v format for each variable
            # e.g.: TRACE:{"line":3,"variables":{"x":"%v","i":"%v"}}
            kv_fmt = ",".join('\\"' + v + '\\":\\"%v\\"' for v in user_vars)
            fmt_args = ", ".join(user_vars)
            fmt_str = 'TRACE:{\\\"line\\\":' + line_str + ',\\\"variables\\\":{' + kv_fmt + '}}\\n'
            emit = '\tfmt.Printf("' + fmt_str + '", ' + fmt_args + ')'
        else:
            fmt_str = 'TRACE:{\\\"line\\\":' + line_str + ',\\\"variables\\\":{}}\\n'
            emit = '\tfmt.Printf("' + fmt_str + '")'

        out.append(emit)

    out_str = "\n".join(out)
    if '"fmt"' not in code:
        if 'import (' in out_str:
            out_str = out_str.replace("import (", 'import (\n\t"fmt"', 1)
        else:
            out_str = re.sub(r'(package\s+\w+\s*\n)', r'\1\nimport "fmt"\n', out_str)
    return out_str


def run_go_trace(code: str) -> List[Dict[str, Any]]:
    instrumented = _build_go_trace(code)
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "main.go")
        with open(src, "w", encoding="utf-8") as f:
            f.write(instrumented)
        return _run_and_parse(["go", "run", src])


# ─────────────────────────────────────────────────────────────
# Rust tracer
# ─────────────────────────────────────────────────────────────

def _extract_rust_vars(code: str) -> List[str]:
    """Extract user-declared variable names from Rust source."""
    names: set = set()
    for m in re.finditer(r'\blet\s+(?:mut\s+)?(\w+)\s*[=:]', code):
        names.add(m.group(1))
    _exclude = {
        'if', 'else', 'for', 'while', 'loop', 'return', 'break', 'continue',
        'fn', 'main', '_', 'mut',
    }
    return [n for n in sorted(names) if n not in _exclude]


def _build_rust_trace(code: str) -> str:
    """Inject eprintln! TRACE lines with variable values into Rust code (uses stderr)."""
    user_vars = _extract_rust_vars(code)
    lines = code.splitlines()
    out = []

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        out.append(line)

        if (not stripped
                or stripped.startswith("//")
                or stripped in ("{", "}")
                or stripped.startswith("use ")
                or stripped.startswith("fn ")
                or stripped.startswith("#[")
                or stripped.startswith("pub ")
                or stripped.startswith("mod ")):
            continue

        line_str = str(i)
        if user_vars:
            # {:?} gives Debug repr for any type
            kv_fmt = ",".join('\\"' + v + '\\":\\"{:?}\\"' for v in user_vars)
            fmt_args = ", ".join(user_vars)
            fmt_str = 'TRACE:{\\\"line\\\":' + line_str + ',\\\"variables\\\":{' + kv_fmt + '}}'
            emit = '    eprintln!("' + fmt_str + '", ' + fmt_args + ');'
        else:
            fmt_str = 'TRACE:{\\\"line\\\":' + line_str + ',\\\"variables\\\":{}}'
            emit = '    eprintln!("' + fmt_str + '");'

        out.append(emit)

    return "\n".join(out)


def run_rust_trace(code: str) -> List[Dict[str, Any]]:
    instrumented = _build_rust_trace(code)
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "main.rs")
        exe = os.path.join(tmpdir, "main.exe" if os.name == "nt" else "main")
        with open(src, "w", encoding="utf-8") as f:
            f.write(instrumented)
        try:
            comp = subprocess.run(
                ["rustc", src, "-o", exe], capture_output=True, text=True, timeout=30,
            )
        except FileNotFoundError:
            return [{"line": -1, "variables": {"__error__": "'rustc' not found. Is Rust installed and on PATH?"}}]
        if comp.returncode != 0:
            err = (comp.stderr.splitlines() or ["Compile error"])[-1][:200]
            return [{"line": -1, "variables": {"__error__": "Compile error: " + err}}]
        try:
            r = subprocess.run([exe], capture_output=True, text=True, timeout=8)
            trace = []
            for ln in r.stderr.splitlines():
                if ln.startswith("TRACE:"):
                    try:
                        trace.append(json.loads(ln[6:]))
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
        trace = run_python_trace(code)
    elif lang in ("javascript", "js", "node"):
        trace = run_js_trace(code)
    elif lang in ("cpp", "c++", "c"):
        trace = run_cpp_trace(code)
    elif lang == "java":
        trace = run_java_trace(code)
    elif lang == "go":
        trace = run_go_trace(code)
    elif lang in ("rust", "rs"):
        trace = run_rust_trace(code)
    else:
        trace = [{"line": -1, "variables": {"__error__": "Tracing not supported for '" + language + "'"}}]

    return _sanitize_json_value(trace)
