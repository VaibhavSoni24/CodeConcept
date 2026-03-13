"""Code Smell Analyzer — detects poor coding practices via AST, pylint, and radon."""

import ast
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

def _max_nesting_depth(node: ast.AST, current: int = 0) -> int:
    max_depth = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While, ast.If, ast.With)):
            depth = _max_nesting_depth(child, current + 1)
            max_depth = max(max_depth, depth)
        else:
            depth = _max_nesting_depth(child, current)
            max_depth = max(max_depth, depth)
    return max_depth

def detect_code_smells(code: str) -> List[Dict[str, Any]]:
    """Analyze code for common code smells using ast, pylint, and radon."""
    smells: List[Dict[str, Any]] = []

    # 1. AST-based analysis
    try:
        tree = ast.parse(code)

        # Deep nesting & Excessive loops via AST
        loop_count = 0
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
            if isinstance(node, (ast.For, ast.While)):
                loop_count += 1
                
        if loop_count > 3:
             smells.append({
                "type": "Excessive Loops",
                "severity": "medium",
                "message": f"Found {loop_count} loops in the code. Consider refactoring to reduce iteration.",
                "line": 1,
            })

    except SyntaxError:
        return smells

    # Write code to temp file for pylint and radon
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        # 2. Pylint analysis
        pylint_cmd = [
            sys.executable, "-m", "pylint",
            "--output-format=json",
            "--disable=all",
            "--enable=unused-variable,duplicate-code,too-many-branches,too-many-nested-blocks,too-many-locals,too-many-statements,too-many-arguments",
            tmp_path
        ]
        result = subprocess.run(pylint_cmd, capture_output=True, text=True)
        if result.stdout.strip():
            try:
                pylint_data = json.loads(result.stdout)
                for issue in pylint_data:
                    symbol = issue.get("symbol", "")
                    if symbol == "unused-variable":
                        smells.append({
                            "type": "Unused Variable",
                            "severity": "low",
                            "message": issue.get("message", "Unused variable detected."),
                            "line": issue.get("line", 0)
                        })
                    elif symbol == "duplicate-code":
                        smells.append({
                            "type": "Duplicate Logic",
                            "severity": "medium",
                            "message": "Duplicate code blocks detected.",
                            "line": issue.get("line", 0)
                        })
                    elif symbol == "too-many-arguments":
                        smells.append({
                            "type": "Long Function",
                            "severity": "medium",
                            "message": issue.get("message", "Too many arguments in function."),
                            "line": issue.get("line", 0)
                        })
            except json.JSONDecodeError:
                pass

        # 3. Radon analysis
        radon_cmd = [sys.executable, "-m", "radon", "cc", "-j", tmp_path]
        result2 = subprocess.run(radon_cmd, capture_output=True, text=True)
        if result2.stdout.strip():
            try:
                radon_data = json.loads(result2.stdout)
                file_blocks = radon_data.get(tmp_path, [])
                if isinstance(file_blocks, list):
                    for block in file_blocks:
                        if block.get("type") == "function":
                            complexity = block.get("complexity", 1)
                            if complexity > 5:
                                smells.append({
                                    "type": "Deep Nesting",
                                    "severity": "high" if complexity > 10 else "medium",
                                    "message": f"Function '{block.get('name')}' has high cyclomatic complexity ({complexity}).",
                                    "line": block.get("lineno", 0)
                                })
            except json.JSONDecodeError:
                pass

        radon_raw_cmd = [sys.executable, "-m", "radon", "raw", "-j", tmp_path]
        result3 = subprocess.run(radon_raw_cmd, capture_output=True, text=True)
        if result3.stdout.strip():
            try:
                radon_raw = json.loads(result3.stdout)
                stats = radon_raw.get(tmp_path, {})
                loc = stats.get("loc", 0)
                if loc > 20:
                    smells.append({
                        "type": "Long Function",
                        "severity": "medium",
                        "message": f"Code length is {loc} lines. Consider breaking into smaller functions.",
                        "line": 1
                    })
            except (json.JSONDecodeError, AttributeError):
                pass

    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    # Deduplicate smells based on message
    unique_smells = []
    seen_messages = set()
    for s in smells:
        if s["message"] not in seen_messages:
            unique_smells.append(s)
            seen_messages.add(s["message"])

    return unique_smells
