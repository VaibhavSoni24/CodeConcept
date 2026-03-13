"""Code Smell Analyzer — detects poor coding practices via AST inspection."""

import ast
from typing import Any, Dict, List


def _max_nesting_depth(node: ast.AST, current: int = 0) -> int:
    """Recursively compute the maximum nesting depth of loops and conditionals."""
    max_depth = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While, ast.If, ast.With)):
            depth = _max_nesting_depth(child, current + 1)
            max_depth = max(max_depth, depth)
        else:
            depth = _max_nesting_depth(child, current)
            max_depth = max(max_depth, depth)
    return max_depth


def _count_statements(body: list) -> int:
    """Count total statements recursively."""
    count = 0
    for node in body:
        count += 1
        if hasattr(node, "body"):
            count += _count_statements(node.body)
        if hasattr(node, "orelse") and node.orelse:
            count += _count_statements(node.orelse)
    return count


def detect_code_smells(code: str) -> List[Dict[str, Any]]:
    """Analyze code for common code smells."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    smells: List[Dict[str, Any]] = []

    for node in ast.walk(tree):
        # 1. Large functions (> 20 statements)
        if isinstance(node, ast.FunctionDef):
            stmt_count = _count_statements(node.body)
            if stmt_count > 20:
                smells.append({
                    "type": "Large Function",
                    "severity": "medium",
                    "message": f"Function '{node.name}' has {stmt_count} statements (recommended: ≤20).",
                    "line": node.lineno,
                })

            # 3. Long parameter list (> 4)
            total_params = len(node.args.args) + len(node.args.kwonlyargs)
            if total_params > 4:
                smells.append({
                    "type": "Long Parameter List",
                    "severity": "medium",
                    "message": f"Function '{node.name}' has {total_params} parameters (recommended: ≤4).",
                    "line": node.lineno,
                })

    # 2. Deep nesting (> 3 levels)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            depth = _max_nesting_depth(node)
            if depth > 3:
                smells.append({
                    "type": "Deep Nesting",
                    "severity": "high",
                    "message": f"Function '{node.name}' has nesting depth {depth} (recommended: ≤3).",
                    "line": node.lineno,
                })

    # 4. Unused variables (simple heuristic: assigned but never loaded)
    assigned: Dict[str, int] = {}
    loaded: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                if node.id not in assigned:
                    assigned[node.id] = node.lineno
            elif isinstance(node.ctx, ast.Load):
                loaded.add(node.id)

    for name, line in assigned.items():
        if name not in loaded and not name.startswith("_"):
            smells.append({
                "type": "Unused Variable",
                "severity": "low",
                "message": f"Variable '{name}' is assigned but never used.",
                "line": line,
            })

    # 5. Duplicate string literals (same string > 3 times)
    string_counts: Dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) > 3:
            string_counts[node.value] = string_counts.get(node.value, 0) + 1

    for literal, count in string_counts.items():
        if count > 3:
            smells.append({
                "type": "Duplicate String Literal",
                "severity": "low",
                "message": f"String \"{literal[:30]}{'…' if len(literal) > 30 else ''}\" appears {count} times. Consider using a constant.",
                "line": 0,
            })

    return smells
