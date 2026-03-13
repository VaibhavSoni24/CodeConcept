"""Complexity Analyzer — computes code complexity metrics via pure AST walking."""

import ast
from typing import Any, Dict


def _count_branches(tree: ast.AST) -> int:
    """Count decision points: if, elif, for, while, except, and, or."""
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
            count += 1
        if isinstance(node, ast.BoolOp):
            # Each `and` / `or` adds len(values) - 1 decision points
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
    """Check if any function calls itself."""
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


def analyze_complexity(code: str) -> Dict[str, Any]:
    """Return complexity metrics for the given source code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            "cyclomatic_complexity": 0,
            "loop_depth": 0,
            "has_recursion": False,
            "branch_count": 0,
        }

    branches = _count_branches(tree)
    # Cyclomatic = branches + 1 (single connected component)
    cyclomatic = branches + 1
    loop_depth = _max_loop_depth(tree)
    has_recursion = _detect_recursion(tree)

    return {
        "cyclomatic_complexity": cyclomatic,
        "loop_depth": loop_depth,
        "has_recursion": has_recursion,
        "branch_count": branches,
    }
