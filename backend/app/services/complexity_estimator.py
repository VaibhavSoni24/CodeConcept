"""
Algorithmic (Big-O) complexity estimator based on structural heuristics.
These are approximations — not proof-level analysis.
"""
import re
from typing import Any, Dict


def _detect_arrays(code: str) -> bool:
    """Check if code uses array/list-like or hash-map-like data structures."""
    patterns = [
        r"\[\s*\]",           # empty list []
        r"\blist\(",          # list()
        r"\bdict\(",          # dict()
        r"\bset\(",           # set()
        r"new\s+Array",       # JS new Array
        r"new\s+ArrayList",   # Java ArrayList
        r"new\s+HashMap",     # Java HashMap
        r"new\s+vector",      # C++ vector
        r"Vec::",             # Rust Vec
        r"make\(\[\]",        # Go slice
    ]
    return any(re.search(p, code) for p in patterns)


def estimate_time_complexity(loop_depth: int, has_recursion: bool) -> str:
    """
    Heuristic time complexity estimation.
    Rules (in order of priority):
      - recursion + no loops  → O(log n)  [e.g. binary search / divide & conquer]
      - loop_depth == 0       → O(1)
      - loop_depth == 1       → O(n)
      - loop_depth == 2       → O(n²)
      - loop_depth >= 3       → O(n³)
    """
    if has_recursion and loop_depth == 0:
        return "O(log n)"
    if loop_depth == 0:
        return "O(1)"
    if loop_depth == 1:
        return "O(n)"
    if loop_depth == 2:
        return "O(n²)"
    return "O(n³)"


def estimate_space_complexity(has_recursion: bool, code: str = "") -> str:
    """
    Heuristic space complexity estimation.
    Rules (in order of priority):
      - recursion             → O(log n)  [call-stack depth]
      - array / map usage     → O(n)
      - otherwise             → O(1)
    """
    if has_recursion:
        return "O(log n)"
    if code and _detect_arrays(code):
        return "O(n)"
    return "O(1)"


def estimate_algorithm_complexity(code: str, loop_depth: int, has_recursion: bool) -> Dict[str, Any]:
    """
    Convenience wrapper that returns both time and space estimates.
    """
    return {
        "time_complexity": estimate_time_complexity(loop_depth, has_recursion),
        "space_complexity": estimate_space_complexity(has_recursion, code),
    }
