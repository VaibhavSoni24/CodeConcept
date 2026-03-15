"""
Structural complexity analysis using Lizard.
Supports: Python, JavaScript, C++, Java, Go, Rust.
"""
import re
from typing import Any, Dict

try:
    import lizard
except ImportError:  # pragma: no cover - environment-dependent
    lizard = None


_LANG_EXT_MAP = {
    "python": "py",
    "javascript": "js",
    "js": "js",
    "node": "js",
    "cpp": "cpp",
    "c++": "cpp",
    "c": "c",
    "java": "java",
    "go": "go",
    "rust": "rs",
    "rs": "rs",
}


def _is_comment_or_empty(line: str, language: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("//"):
        return True
    if stripped.startswith("/*") or stripped.startswith("*") or stripped.startswith("*/"):
        return True
    if language.lower() == "python" and stripped.startswith("#"):
        return True
    return False


def _heuristic_function_count(code: str, language: str) -> int:
    lang = language.lower()
    if lang == "python":
        return len(re.findall(r"^\s*def\s+[A-Za-z_]\w*\s*\(", code, flags=re.MULTILINE))
    if lang in {"javascript", "js", "node"}:
        named = len(re.findall(r"\bfunction\s+[A-Za-z_$]\w*\s*\(", code))
        arrow = len(re.findall(r"\b(?:const|let|var)\s+[A-Za-z_$]\w*\s*=\s*\([^)]*\)\s*=>", code))
        return named + arrow
    if lang in {"cpp", "c++", "c", "java", "go", "rust", "rs"}:
        # Best-effort function signature matcher for brace-based languages.
        pattern = r"^\s*(?:[A-Za-z_][\w:<>,\s*&~]+\s+)+[A-Za-z_~][\w:<>]*\s*\([^;{}]*\)\s*(?:const\s*)?\{"
        return len(re.findall(pattern, code, flags=re.MULTILINE))
    return 0


def _heuristic_cyclomatic(code: str) -> int:
    decision_tokens = re.findall(
        r"\bif\b|\bfor\b|\bwhile\b|\bcase\b|\bcatch\b|&&|\|\||\?",
        code,
    )
    return max(1, 1 + len(decision_tokens))


def _heuristic_loop_depth(code: str, language: str) -> int:
    lang = language.lower()
    if lang == "python":
        lines = code.splitlines()
        depth_stack = []
        max_depth = 0
        for line in lines:
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line) - len(stripped)
            while depth_stack and depth_stack[-1] >= indent:
                depth_stack.pop()
            if re.match(r"(for|while)\b", stripped):
                depth_stack.append(indent)
                max_depth = max(max_depth, len(depth_stack))
        return max_depth

    # Brace-based language heuristic.
    # We track brace depth where loops are encountered, then normalize against
    # the shallowest loop depth to estimate loop nesting (independent of
    # surrounding function/class braces).
    brace_depth = 0
    loop_depth_candidates = []
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if re.search(r"\b(for|while|do)\b", line):
            loop_depth_candidates.append(brace_depth)
        opens = line.count("{")
        closes = line.count("}")
        brace_depth += opens
        brace_depth = max(0, brace_depth - closes)

    if not loop_depth_candidates:
        return 0
    baseline = min(loop_depth_candidates)
    return max((d - baseline + 1) for d in loop_depth_candidates)


def _heuristic_structural_complexity(code: str, language: str, reason: str) -> Dict[str, Any]:
    meaningful_lines = [ln for ln in code.splitlines() if not _is_comment_or_empty(ln, language)]
    function_count = _heuristic_function_count(code, language)
    cyclomatic = _heuristic_cyclomatic(code)
    max_nesting = _heuristic_loop_depth(code, language)

    avg_len = 0
    if function_count > 0:
        avg_len = round(len(meaningful_lines) / function_count, 1)

    return {
        "loc": len(meaningful_lines),
        "function_count": function_count,
        "average_function_length": avg_len,
        "cyclomatic_complexity": cyclomatic,
        "max_nesting_depth": max_nesting,
        "metric_source": "heuristic",
        "metric_warning": reason,
    }


def compute_structural_complexity(code: str, language: str) -> Dict[str, Any]:
    """
    Uses Lizard to compute structural complexity metrics for any supported language.
    Returns:
        loc                   – logical lines of code
        function_count        – number of functions / methods
        average_function_length – avg LOC per function
        cyclomatic_complexity – max cyclomatic complexity across functions
        max_nesting_depth     – max nesting depth across functions
    """
    ext = _LANG_EXT_MAP.get(language.lower(), "py")
    fake_filename = f"temp.{ext}"

    if lizard is None:
        return _heuristic_structural_complexity(
            code,
            language,
            "lizard_not_installed",
        )

    try:
        analysis = lizard.analyze_file.analyze_source_code(fake_filename, code)
    except Exception as exc:
        return _heuristic_structural_complexity(
            code,
            language,
            f"lizard_parse_failed:{exc.__class__.__name__}",
        )

    functions = analysis.function_list
    heuristic = _heuristic_structural_complexity(code, language, "")

    lizard_loc = analysis.nloc
    lizard_function_count = len(functions)
    lizard_avg_length = (
        round(sum(f.length for f in functions) / len(functions), 1)
        if functions else 0
    )
    lizard_cyclomatic = (
        max(f.cyclomatic_complexity for f in functions)
        if functions else 1
    )
    lizard_nesting = (
        max(f.max_nesting_depth for f in functions)
        if functions else 0
    )

    used_guard = False
    loc = max(lizard_loc, heuristic["loc"])
    function_count = max(lizard_function_count, heuristic["function_count"])
    cyclomatic = max(lizard_cyclomatic, heuristic["cyclomatic_complexity"])
    max_nesting_depth = max(lizard_nesting, heuristic["max_nesting_depth"])

    if cyclomatic != lizard_cyclomatic or max_nesting_depth != lizard_nesting or function_count != lizard_function_count:
        used_guard = True

    average_function_length = lizard_avg_length
    if function_count > 0 and average_function_length == 0:
        average_function_length = heuristic["average_function_length"]
        used_guard = True

    return {
        "loc": loc,
        "function_count": function_count,
        "average_function_length": average_function_length,
        "cyclomatic_complexity": cyclomatic,
        "max_nesting_depth": max_nesting_depth,
        "metric_source": "lizard+heuristic_guard" if used_guard else "lizard",
        "metric_warning": "lizard_sparse_metrics_guarded" if used_guard else "",
    }
