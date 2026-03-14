from typing import Dict, Any

def get_empty_analysis() -> Dict[str, Any]:
    return {
        "analysis": {"syntax": "ok", "syntax_error": None, "ast_flags": []},
        "misconceptions": [],
        "code_smells": [],
        "complexity": {"cyclomatic_complexity": 0},
        "concepts_detected": [],
        "flow_graph": {"nodes": [], "edges": [], "mermaid": ""}
    }
