from typing import Dict, Any
from ..static_analyzer import run_static_analysis
from ..misconception_detector import detect_misconceptions
from ..smell_analyzer import detect_code_smells
from ..complexity_analyzer import analyze_complexity
from ..concept_detector import detect_concepts
from ..flow_graph import build_flow_graph

def run_python_analysis(code: str) -> Dict[str, Any]:
    analysis = run_static_analysis(code)
    is_ok = analysis["syntax"] == "ok"
    return {
        "analysis": analysis,
        "misconceptions": detect_misconceptions(code) if is_ok else [],
        "code_smells": detect_code_smells(code) if is_ok else [],
        "complexity": analyze_complexity(code),
        "concepts_detected": detect_concepts(code) if is_ok else [],
        "flow_graph": build_flow_graph("python", code) if is_ok else {"nodes": [], "edges": [], "mermaid": ""}
    }
