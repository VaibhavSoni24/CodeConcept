"""Execution Tracer — sandboxed step-by-step code execution trace."""

import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

# The tracer script is written to a temp file and run in a subprocess.
# It uses sys.settrace to capture line events and variable snapshots.
TRACER_SCRIPT_TEMPLATE = r'''
import sys
import json

_trace_log = []
_max_steps = 50
_code_line_offset = 0

def _safe_repr(val):
    """Convert a value to a JSON-safe representation."""
    try:
        if isinstance(val, (int, float, bool, type(None))):
            return val
        if isinstance(val, str):
            return val[:100]
        if isinstance(val, (list, tuple)):
            return [_safe_repr(v) for v in val[:10]]
        if isinstance(val, dict):
            return {k: _safe_repr(v) for k, v in list(val.items())[:10]}
        return repr(val)[:80]
    except Exception:
        return "<unrepresentable>"

def _tracer(frame, event, arg):
    if len(_trace_log) >= _max_steps:
        sys.settrace(None)
        return None
    if event == "line" and frame.f_code.co_filename == "<string>":
        variables = {}
        _skip = {"_safe_repr", "_tracer", "_trace_log", "_max_steps", "_code_line_offset", "sys", "json", "student_code"}
        for k, v in frame.f_locals.items():
            if not k.startswith("_") and k not in _skip:
                variables[k] = _safe_repr(v)
        _trace_log.append({
            "line": frame.f_lineno,
            "variables": variables,
        })
    return _tracer

student_code = __STUDENT_CODE__

sys.settrace(_tracer)
try:
    exec(compile(student_code, "<string>", "exec"))
except Exception as exc:
    _trace_log.append({"line": -1, "variables": {"__error__": str(exc)[:200]}})
finally:
    sys.settrace(None)

print(json.dumps(_trace_log), file=sys.stderr)
'''


def run_execution_trace(code: str) -> List[Dict[str, Any]]:
    """Execute code in a sandboxed subprocess and return trace data."""
    script = TRACER_SCRIPT_TEMPLATE.replace(
        "__STUDENT_CODE__", json.dumps(code)
    )

    with tempfile.NamedTemporaryFile(
        "w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(script)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, "-I", tmp_path],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        # Trace JSON is written to stderr to separate from student stdout
        stderr_text = result.stderr.strip() if result.stderr else ""
        # Try to parse the last line of stderr as JSON (the trace data)
        if stderr_text:
            # The trace JSON is always the last line
            lines = stderr_text.rsplit("\n", 1)
            trace_line = lines[-1].strip()
            try:
                return json.loads(trace_line)
            except json.JSONDecodeError:
                pass
        if result.returncode != 0:
            error_msg = stderr_text[:200] if stderr_text else "Unknown error"
            return [{"line": -1, "variables": {"__error__": error_msg}}]
        return [{"line": -1, "variables": {"__error__": "No trace data produced"}}]

    except subprocess.TimeoutExpired:
        return [{"line": -1, "variables": {"__error__": "Execution timed out (3s limit)"}}]
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
