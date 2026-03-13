import ast
import json
import subprocess
import sys
import tempfile
import os
from typing import Dict, Any, List


class ConceptVisitor(ast.NodeVisitor):
    def __init__(self):
        self.flags: List[Dict[str, Any]] = []
        self.function_stack: List[ast.FunctionDef] = []

    def visit_While(self, node: ast.While):
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            has_break = any(isinstance(child, ast.Break) for child in ast.walk(node))
            if not has_break:
                self.flags.append(
                    {
                        "mistake_id": "possible_infinite_loop",
                        "detail": "Detected while True without a break condition.",
                    }
                )
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr):
        if isinstance(node.value, ast.Compare):
            self.flags.append(
                {
                    "mistake_id": "compare_instead_of_assign",
                    "detail": "Standalone comparison found. Did you mean assignment?",
                }
            )
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == "range" and node.iter.args:
                first = node.iter.args[0]
                if isinstance(first, ast.Call) and isinstance(first.func, ast.Name) and first.func.id == "len":
                    self.flags.append(
                        {
                            "mistake_id": "inefficient_index_loop",
                            "detail": "Consider iterating directly over the collection instead of range(len(...)).",
                        }
                    )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.function_stack.append(node)
        self.generic_visit(node)
        self._check_recursion_without_base_case(node)
        self.function_stack.pop()

    def _check_recursion_without_base_case(self, node: ast.FunctionDef):
        calls_self = False
        has_if_guard = False
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == node.name:
                calls_self = True
            if isinstance(child, ast.If):
                has_if_guard = True
        if calls_self and not has_if_guard:
            self.flags.append(
                {
                    "mistake_id": "recursion_no_base_case",
                    "detail": f"Function '{node.name}' is recursive but no base-case conditional was detected.",
                }
            )


def _run_pylint(code: str) -> List[Dict[str, Any]]:
    """Run pylint on code in a temp file and return parsed messages."""
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        result = subprocess.run(
            [sys.executable, "-m", "pylint", "--output-format=json", "--disable=C,R", tmp_path],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.stdout.strip():
            messages = json.loads(result.stdout.strip())
            return [
                {
                    "type": m.get("type", ""),
                    "symbol": m.get("symbol", ""),
                    "message": m.get("message", ""),
                    "line": m.get("line", 0),
                }
                for m in messages[:10]
            ]
    except Exception:
        pass
    finally:
        try:
            os.remove(tmp_path)
        except (OSError, UnboundLocalError):
            pass
    return []


def _run_radon(code: str) -> Dict[str, Any]:
    """Compute cyclomatic complexity via radon."""
    try:
        from radon.complexity import cc_visit

        results = cc_visit(code)
        blocks = []
        for block in results:
            blocks.append({
                "name": block.name,
                "type": block.letter,
                "complexity": block.complexity,
                "line": block.lineno,
            })
        avg = sum(b["complexity"] for b in blocks) / max(len(blocks), 1)
        return {"blocks": blocks, "average_complexity": round(avg, 2)}
    except Exception:
        return {"blocks": [], "average_complexity": 0}


def run_static_analysis(code: str) -> Dict[str, Any]:
    analysis: Dict[str, Any] = {
        "syntax": "ok",
        "syntax_error": None,
        "ast_flags": [],
        "pylint": [],
        "radon": {},
    }

    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        analysis["syntax"] = "error"
        analysis["syntax_error"] = {
            "message": str(error),
            "line": error.lineno,
            "offset": error.offset,
        }
        return analysis

    visitor = ConceptVisitor()
    visitor.visit(tree)
    analysis["ast_flags"] = visitor.flags
    analysis["pylint"] = _run_pylint(code)
    analysis["radon"] = _run_radon(code)
    return analysis
