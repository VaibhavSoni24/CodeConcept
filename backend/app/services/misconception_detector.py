"""Misconception Detector — extended AST visitor for logical misconceptions."""

import ast
from typing import Any, Dict, List


class MisconceptionVisitor(ast.NodeVisitor):
    """Detects 10+ common Python misconceptions via AST patterns."""

    BUILTINS = {
        "list", "dict", "set", "tuple", "str", "int", "float", "bool",
        "type", "id", "input", "print", "len", "range", "map", "filter",
        "sum", "min", "max", "abs", "sorted", "reversed", "enumerate", "zip",
        "open", "file", "object", "super", "next", "iter", "hash", "format",
    }

    def __init__(self) -> None:
        self.results: List[Dict[str, Any]] = []
        self._assigned_names: Dict[str, int] = {}
        self._read_names: set = set()

    # --- 1. Off-by-one: range(len(arr)+1) ---
    def visit_For(self, node: ast.For) -> None:
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == "range" and node.iter.args:
                arg = node.iter.args[0]
                if (
                    isinstance(arg, ast.BinOp)
                    and isinstance(arg.op, ast.Add)
                    and isinstance(arg.right, ast.Constant)
                    and arg.right.value == 1
                    and isinstance(arg.left, ast.Call)
                    and isinstance(arg.left.func, ast.Name)
                    and arg.left.func.id == "len"
                ):
                    self.results.append({
                        "misconception_id": "off_by_one_range",
                        "misconception": "Array bounds misunderstanding",
                        "concept": "Array indexing",
                        "severity": "medium",
                        "detail": f"range(len(...)+1) iterates one index beyond the list. Line {node.lineno}.",
                    })
        self.generic_visit(node)

    # --- 2. Mutable default argument ---
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for default in node.args.defaults + node.args.kw_defaults:
            if default is not None and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.results.append({
                    "misconception_id": "mutable_default_arg",
                    "misconception": "Mutable default argument",
                    "concept": "Mutable defaults",
                    "severity": "high",
                    "detail": f"Function '{node.name}' uses a mutable default argument (line {node.lineno}). "
                              "This is shared across all calls.",
                })
        self.generic_visit(node)

    # --- 3. Float equality (==) ---
    def visit_Compare(self, node: ast.Compare) -> None:
        for op in node.ops:
            if isinstance(op, ast.Eq):
                # Check if either side involves float literals or float() calls
                for operand in [node.left] + node.comparators:
                    if isinstance(operand, ast.Constant) and isinstance(operand.value, float):
                        self.results.append({
                            "misconception_id": "float_equality",
                            "misconception": "Float equality comparison",
                            "concept": "Float comparison",
                            "severity": "medium",
                            "detail": f"Comparing floats with == is unreliable due to precision (line {node.lineno}).",
                        })
                        break
        self.generic_visit(node)

    # --- 4. Bare except ---
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.results.append({
                "misconception_id": "bare_except",
                "misconception": "Bare except clause",
                "concept": "Exception handling",
                "severity": "medium",
                "detail": f"Bare 'except:' catches all exceptions including KeyboardInterrupt (line {node.lineno}).",
            })
        self.generic_visit(node)

    # --- 5–10. Expression-level checks via generic walk ---
    def visit_Expr(self, node: ast.Expr) -> None:
        # 5. String concatenation in loop detected elsewhere
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                # 9. Shadowing built-in names
                if target.id in self.BUILTINS:
                    self.results.append({
                        "misconception_id": "shadow_builtin",
                        "misconception": "Shadowing built-in name",
                        "concept": "Name shadowing",
                        "severity": "medium",
                        "detail": f"Variable '{target.id}' shadows a Python built-in (line {node.lineno}).",
                    })
                self._assigned_names[target.id] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self._read_names.add(node.id)
        self.generic_visit(node)


def _post_process_checks(visitor: MisconceptionVisitor, tree: ast.AST) -> None:
    """Run checks that require full-tree context."""

    # 7. `is` vs `==` for value comparison on literals
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op, comparator in zip(node.ops, node.comparators):
                if isinstance(op, ast.Is) and isinstance(comparator, ast.Constant):
                    if not isinstance(comparator.value, (bool, type(None))):
                        visitor.results.append({
                            "misconception_id": "is_vs_equals",
                            "misconception": "Using 'is' for value comparison",
                            "concept": "Identity vs equality",
                            "severity": "high",
                            "detail": f"'is' checks identity, not equality. Use '==' for values (line {node.lineno}).",
                        })

    # 8. Global variable mutation inside function
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Global):
                    visitor.results.append({
                        "misconception_id": "global_mutation",
                        "misconception": "Global variable mutation",
                        "concept": "Scope rules",
                        "severity": "medium",
                        "detail": f"Function '{node.name}' mutates global state (line {child.lineno}).",
                    })

    # 10. type() instead of isinstance()
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comparator in [node.left] + node.comparators:
                if (
                    isinstance(comparator, ast.Call)
                    and isinstance(comparator.func, ast.Name)
                    and comparator.func.id == "type"
                ):
                    visitor.results.append({
                        "misconception_id": "type_vs_isinstance",
                        "misconception": "Using type() instead of isinstance()",
                        "concept": "Type checking",
                        "severity": "low",
                        "detail": f"Prefer isinstance() over type() for type checks (line {node.lineno}).",
                    })

    # 4b. Modifying list while iterating
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Name):
            iter_name = node.iter.id
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    if (
                        isinstance(child.func.value, ast.Name)
                        and child.func.value.id == iter_name
                        and child.func.attr in ("append", "remove", "pop", "insert", "extend")
                    ):
                        visitor.results.append({
                            "misconception_id": "modify_while_iterating",
                            "misconception": "Modifying collection while iterating",
                            "concept": "Iteration mutation",
                            "severity": "high",
                            "detail": f"Modifying '{iter_name}' while looping over it (line {child.lineno}).",
                        })

    # 5b. String concatenation in loop
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            for child in ast.walk(node):
                if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                    if isinstance(child.target, ast.Name):
                        visitor.results.append({
                            "misconception_id": "string_concat_loop",
                            "misconception": "Potential string concatenation in loop",
                            "concept": "String performance",
                            "severity": "low",
                            "detail": f"'+=' in a loop may cause O(n²) if used on strings (line {child.lineno}).",
                        })
                        break
                        
    # Unused variables (assigned but never read)
    for name, lineno in visitor._assigned_names.items():
        if name not in visitor._read_names and name not in visitor.BUILTINS and not name.startswith("_"):
            visitor.results.append({
                "misconception_id": "unused_variable",
                "misconception": "Unused variable",
                "concept": "Code cleanliness",
                "severity": "low",
                "detail": f"Variable '{name}' is assigned but never used (line {lineno}).",
            })
            
    # Inefficient nested loops
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            for child in getattr(node, "body", []):
                for subnode in ast.walk(child):
                    if isinstance(subnode, (ast.For, ast.While)):
                        visitor.results.append({
                            "misconception_id": "inefficient_nested_loop",
                            "misconception": "Inefficient nested loops",
                            "concept": "Algorithmic complexity",
                            "severity": "medium",
                            "detail": f"A loop is nested inside another loop (line {subnode.lineno}). This can lead to O(N^2) or worse performance.",
                        })
                        break

    # Recursion no base case
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
            has_recursive_call = False
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == node.name:
                    has_recursive_call = True
            if has_recursive_call and not has_return:
                visitor.results.append({
                    "misconception_id": "recursion_no_base_case",
                    "misconception": "Recursion without base case",
                    "concept": "Recursion fundamentals",
                    "severity": "high",
                    "detail": f"Function '{node.name}' calls itself without a return statement base case (line {node.lineno}).",
                })

    # Infinite Loop (while True without break)
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            is_true = isinstance(node.test, ast.Constant) and node.test.value is True
            has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
            if is_true and not has_break:
                visitor.results.append({
                    "misconception_id": "possible_infinite_loop",
                    "misconception": "Infinite loop",
                    "concept": "Loop termination condition",
                    "severity": "high",
                    "detail": f"while True loop without a break statement will run infinitely (line {node.lineno}).",
                })


def detect_misconceptions(code: str) -> List[Dict[str, Any]]:
    """Run the misconception detector on the given source code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = MisconceptionVisitor()
    visitor.visit(tree)
    _post_process_checks(visitor, tree)

    # Deduplicate by misconception_id + line
    seen = set()
    unique = []
    for r in visitor.results:
        key = (r["misconception_id"], r.get("detail", ""))
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique
