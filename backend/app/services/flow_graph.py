"""Flow Graph Generator — builds a control flow graph from AST."""

import ast
from typing import Any, Dict, List, Tuple


def build_flow_graph(code: str) -> Dict[str, Any]:
    """Parse code and produce a control flow graph with nodes, edges, and Mermaid string."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"nodes": [], "edges": [], "mermaid": "graph TD\n  Error[Syntax Error]"}

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, int]] = []
    node_id = 0

    def _add_node(ntype: str, label: str = "") -> int:
        nonlocal node_id
        nid = node_id
        nodes.append({"id": nid, "type": ntype, "label": label or ntype})
        node_id += 1
        return nid

    def _process_body(body: list, prev_id: int) -> int:
        """Process a list of statements, chaining them sequentially."""
        current = prev_id
        for stmt in body:
            nid = _process_stmt(stmt)
            if nid is not None:
                edges.append({"from": current, "to": nid})
                current = nid
        return current

    def _process_stmt(stmt: ast.AST) -> int | None:
        """Process a single statement and return its node id."""

        if isinstance(stmt, ast.FunctionDef):
            nid = _add_node("FunctionDef", f"def {stmt.name}()")
            if stmt.body:
                _process_body(stmt.body, nid)
            return nid

        elif isinstance(stmt, ast.For):
            nid = _add_node("Loop", f"for (line {stmt.lineno})")
            last = _process_body(stmt.body, nid)
            # Loop-back edge
            edges.append({"from": last, "to": nid})
            return nid

        elif isinstance(stmt, ast.While):
            nid = _add_node("Loop", f"while (line {stmt.lineno})")
            last = _process_body(stmt.body, nid)
            edges.append({"from": last, "to": nid})
            return nid

        elif isinstance(stmt, ast.If):
            nid = _add_node("Condition", f"if (line {stmt.lineno})")
            if stmt.body:
                _process_body(stmt.body, nid)
            if stmt.orelse:
                _process_body(stmt.orelse, nid)
            return nid

        elif isinstance(stmt, ast.Return):
            return _add_node("Return", f"return (line {stmt.lineno})")

        elif isinstance(stmt, ast.Assign):
            targets = ", ".join(
                t.id if isinstance(t, ast.Name) else "…"
                for t in stmt.targets
            )
            return _add_node("Assignment", f"{targets} = … (line {stmt.lineno})")

        elif isinstance(stmt, ast.Expr):
            if isinstance(stmt.value, ast.Call):
                func_name = ""
                if isinstance(stmt.value.func, ast.Name):
                    func_name = stmt.value.func.id
                elif isinstance(stmt.value.func, ast.Attribute):
                    func_name = stmt.value.func.attr
                return _add_node("Call", f"{func_name}() (line {stmt.lineno})")
            return _add_node("Expression", f"expr (line {stmt.lineno})")

        elif isinstance(stmt, ast.AugAssign):
            target = stmt.target.id if isinstance(stmt.target, ast.Name) else "…"
            return _add_node("Assignment", f"{target} += … (line {stmt.lineno})")

        elif isinstance(stmt, ast.Try):
            return _add_node("TryBlock", f"try (line {stmt.lineno})")

        elif isinstance(stmt, ast.ClassDef):
            return _add_node("ClassDef", f"class {stmt.name}")

        else:
            return None

    # Build the graph
    start_id = _add_node("Start", "Start")
    last_id = _process_body(tree.body, start_id)
    end_id = _add_node("End", "End")
    edges.append({"from": last_id, "to": end_id})

    # Generate Mermaid string
    mermaid = _generate_mermaid(nodes, edges)

    return {"nodes": nodes, "edges": edges, "mermaid": mermaid}


def _sanitize_label(label: str) -> str:
    """Sanitize label for Mermaid compatibility."""
    return label.replace('"', "'").replace("(", "‹").replace(")", "›")


def _generate_mermaid(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, int]]
) -> str:
    """Convert nodes and edges to a Mermaid graph TD string."""
    lines = ["graph TD"]

    shape_map = {
        "Start": ("([", "])"),
        "End": ("([", "])"),
        "Condition": ("{", "}"),
        "Loop": ("[[", "]]"),
        "FunctionDef": ("[/", "/]"),
        "Return": (">", "]"),
    }
    default_shape = ("[", "]")

    for node in nodes:
        nid = f"N{node['id']}"
        label = _sanitize_label(node["label"])
        left, right = shape_map.get(node["type"], default_shape)
        lines.append(f"  {nid}{left}\"{label}\"{right}")

    for edge in edges:
        lines.append(f"  N{edge['from']} --> N{edge['to']}")

    return "\n".join(lines)
