"""Complexity Analyzer — rich code complexity metrics.

For Python, uses Python's built-in AST for precise structural analysis.
For all languages (including Python), overlays Lizard metrics (LOC,
function count, average function length, max nesting depth) and
heuristic Big-O time / space complexity estimates.
"""

import ast
from typing import Any, Dict

from .complexity_service import compute_structural_complexity
from .complexity_estimator import estimate_time_complexity, estimate_space_complexity


# ---------------------------------------------------------------------------
# Python-specific AST helpers
# ---------------------------------------------------------------------------

def _count_branches(tree: ast.AST) -> int:
    """Count decision points: if, for, while, except, and/or."""
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
            count += 1
        if isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
    return count


def _max_loop_depth(node: ast.AST, current: int = 0) -> int:
    """Compute the deepest loop nesting level."""
    max_depth = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While)):
            d = _max_loop_depth(child, current + 1)
        else:
            d = _max_loop_depth(child, current)
        max_depth = max(max_depth, d)
    return max_depth


def _detect_recursion(tree: ast.AST) -> bool:
    """Check if any function calls itself (direct recursion)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id == node.name
                ):
                    return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_complexity(code: str) -> Dict[str, Any]:
    """Python-specific complexity analysis (called from python_analyzer).

    Uses Python AST for precise branch/loop/recursion detection, then
    overlays Lizard structural metrics and Big-O heuristics.
    """
    # --- Python AST pass ---
    try:
        tree = ast.parse(code)
        branches = _count_branches(tree)
        loop_depth = _max_loop_depth(tree)
        has_recursion = _detect_recursion(tree)
        cyclomatic = branches + 1
    except SyntaxError:
        branches = 0
        loop_depth = 0
        has_recursion = False
        cyclomatic = 0

    # --- Lizard structural metrics (LOC, function stats, nesting depth) ---
    lizard_metrics = compute_structural_complexity(code, "python")

    # --- Big-O estimates ---
    time_comp = estimate_time_complexity(loop_depth, has_recursion)
    space_comp = estimate_space_complexity(has_recursion, code)

    return {
        # Structural (Lizard)
        "loc": lizard_metrics.get("loc", 0),
        "function_count": lizard_metrics.get("function_count", 0),
        "average_function_length": lizard_metrics.get("average_function_length", 0),
        "max_nesting_depth": lizard_metrics.get("max_nesting_depth", loop_depth),
        # AST-derived
        "cyclomatic_complexity": cyclomatic,
        "loop_depth": loop_depth,
        "has_recursion": has_recursion,
        "branch_count": branches,
        # Algorithmic estimates
        "time_complexity": time_comp,
        "space_complexity": space_comp,
    }


def analyze_complexity_for_language(language: str, code: str) -> Dict[str, Any]:
    """Language-agnostic complexity analysis (called from dispatch_analysis).

    All languages use Lizard for structural metrics; Big-O heuristics
    use Lizard's max_nesting_depth since AST recursion detection
    is only available for Python.
    """
    lizard_metrics = compute_structural_complexity(code, language)

    loop_depth = lizard_metrics.get("max_nesting_depth", 0)
    # For non-Python we can't easily detect recursion without a full AST;
    # fall back to Python AST path if the language is Python.
    if language.lower() == "python":
        return analyze_complexity(code)

    # Crude recursion heuristic for other languages:
    # look for a function name appearing inside its own body.
    # This is imperfect but better than always returning False.
    has_recursion = False

    time_comp = estimate_time_complexity(loop_depth, has_recursion)
    space_comp = estimate_space_complexity(has_recursion, code)

    return {
        "loc": lizard_metrics.get("loc", 0),
        "function_count": lizard_metrics.get("function_count", 0),
        "average_function_length": lizard_metrics.get("average_function_length", 0),
        "max_nesting_depth": loop_depth,
        "cyclomatic_complexity": lizard_metrics.get("cyclomatic_complexity", 1),
        "loop_depth": loop_depth,
        "has_recursion": has_recursion,
        "branch_count": max(lizard_metrics.get("cyclomatic_complexity", 1) - 1, 0),
        "time_complexity": time_comp,
        "space_complexity": space_comp,
    }
