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
import sys as _sys
import json as _json
import io as _io
import contextlib as _contextlib

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
        _sys.settrace(None)
        return None
    if event == "line" and frame.f_code.co_filename == "<string>":
        variables = {}
        for k, v in frame.f_locals.items():
            if not k.startswith("_") and k != "student_code":
                variables[k] = _safe_repr(v)
        _trace_log.append({
            "line": frame.f_lineno,
            "variables": variables,
        })
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


def run_execution_trace(code: str) -> List[Dict[str, Any]]:
    """Execute code in a sandboxed subprocess and return trace data."""
    script = TRACER_SCRIPT_TEMPLATE.replace(
        "{student_code_json}", json.dumps(code)
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
        output = result.stdout.strip()

        if result.returncode == 0 and output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # Recover if any extra output sneaks in before/after the JSON array.
                left = output.find("[")
                right = output.rfind("]")
                if left != -1 and right != -1 and right > left:
                    try:
                        return json.loads(output[left : right + 1])
                    except json.JSONDecodeError:
                        pass
                return [{"line": -1, "variables": {"__error__": "Trace output parse error"}}]
        else:
            if result.stderr:
                lines = [line.strip() for line in result.stderr.splitlines() if line.strip()]
                error_msg = lines[-1][:200] if lines else "Unknown error"
            else:
                error_msg = "Unknown error"
            return [{"line": -1, "variables": {"__error__": error_msg}}]

    except subprocess.TimeoutExpired:
        return [{"line": -1, "variables": {"__error__": "Execution timed out (3s limit)"}}]
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
