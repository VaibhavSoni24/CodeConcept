"""Concept Detector — identifies which programming constructs are used."""

import ast
from typing import List


def detect_concepts(code: str) -> List[str]:
    """Return a list of programming concept names found in the code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    concepts: set = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            concepts.add("loops")
        elif isinstance(node, ast.While):
            concepts.add("loops")
        elif isinstance(node, ast.If):
            concepts.add("conditionals")
        elif isinstance(node, ast.FunctionDef):
            concepts.add("functions")
        elif isinstance(node, ast.AsyncFunctionDef):
            concepts.add("functions")
            concepts.add("async")
        elif isinstance(node, ast.ClassDef):
            concepts.add("classes")
        elif isinstance(node, ast.Try):
            concepts.add("exception_handling")
        elif isinstance(node, ast.ListComp):
            concepts.add("list_comprehensions")
        elif isinstance(node, ast.DictComp):
            concepts.add("dict_comprehensions")
        elif isinstance(node, ast.SetComp):
            concepts.add("set_comprehensions")
        elif isinstance(node, ast.GeneratorExp):
            concepts.add("generators")
        elif isinstance(node, ast.Yield) or isinstance(node, ast.YieldFrom):
            concepts.add("generators")
        elif isinstance(node, ast.Lambda):
            concepts.add("lambda_functions")
        elif isinstance(node, ast.Return):
            concepts.add("return_values")
        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            concepts.add("imports")

    # Detect recursion (function calls itself)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id == node.name
                ):
                    concepts.add("recursion")

    # Detect decorators
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            concepts.add("decorators")

    return sorted(concepts)
