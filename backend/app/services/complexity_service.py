"""
Structural complexity analysis using Lizard.
Supports: Python, JavaScript, C++, Java, Go, Rust.
"""
import lizard
from typing import Any, Dict


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

    try:
        analysis = lizard.analyze_file.analyze_source_code(fake_filename, code)
    except Exception:
        return {
            "loc": 0,
            "function_count": 0,
            "average_function_length": 0,
            "cyclomatic_complexity": 1,
            "max_nesting_depth": 0,
        }

    functions = analysis.function_list

    return {
        "loc": analysis.nloc,
        "function_count": len(functions),
        "average_function_length": (
            round(sum(f.length for f in functions) / len(functions), 1)
            if functions else 0
        ),
        "cyclomatic_complexity": (
            max(f.cyclomatic_complexity for f in functions)
            if functions else 1
        ),
        "max_nesting_depth": (
            max(f.max_nesting_depth for f in functions)
            if functions else 0
        ),
    }
