from typing import Dict, Any
from .base import get_empty_analysis
from ..flow_graph import build_flow_graph

def run_js_analysis(code: str) -> Dict[str, Any]:
    analysis = get_empty_analysis()
    analysis["flow_graph"] = build_flow_graph("javascript", code)
    return analysis
