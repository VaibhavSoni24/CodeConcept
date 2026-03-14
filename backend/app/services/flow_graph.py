"""Flow Graph Generator — builds a control flow graph from JSON AST."""
from typing import Any, Dict, List
from .ast_service import parse_ast

def build_flow_graph(language: str, code: str) -> Dict[str, Any]:
    ast_json = parse_ast(language, code)
    if not ast_json or ast_json.get("type") in ["SyntaxError", "UnsupportedLanguageOrParserMissing"]:
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

    def _get_mapped_type(ntype: str) -> str:
        if ntype in ["For", "While", "for_statement", "while_statement", "do_statement", "for_in_statement"]:
            return "Loop"
        if ntype in ["If", "if_statement"]:
            return "Condition"
        if ntype in ["Assign", "AugAssign", "variable_declaration", "lexical_declaration", "assignment_expression"]:
            return "Assignment"
        if ntype in ["Call", "call_expression"]:
            return "Call"
        if ntype in ["Return", "return_statement"]:
            return "Return"
        if ntype in ["FunctionDef", "function_declaration", "arrow_function"]:
            return "FunctionDef"
        return ""

    def _traverse(node: Dict[str, Any], prev_id: int) -> int:
        current = prev_id
        mapped_type = _get_mapped_type(node.get("type", ""))
        
        nid = None
        if mapped_type:
            label = f"{mapped_type} (line {node.get('line', '?')})"
            if mapped_type == "FunctionDef":
                label = f"Function {node.get('label', '')}" 
            nid = _add_node(mapped_type, label)
            edges.append({"from": current, "to": nid})
            current = nid

        children = node.get("children", [])
        
        last_in_body = current
        for child in children:
            last_in_body = _traverse(child, last_in_body)

        if mapped_type == "Loop" and nid is not None:
            edges.append({"from": last_in_body, "to": nid})
            return nid 
            
        return last_in_body

    start_id = _add_node("Start", "Start")
    last_id = _traverse(ast_json, start_id)
    end_id = _add_node("End", "End")
    edges.append({"from": last_id, "to": end_id})

    mermaid = _generate_mermaid(nodes, edges)

    return {"nodes": nodes, "edges": edges, "mermaid": mermaid}


def _sanitize_label(label: str) -> str:
    return label.replace('"', "'").replace("(", "‹").replace(")", "›")


def _generate_mermaid(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, int]]
) -> str:
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
