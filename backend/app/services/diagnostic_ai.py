"""AI Diagnostic Engine — LLM-based analysis with rule-based fallback."""

import os
import json
from typing import Dict, Any, List
from openai import OpenAI


def _fallback_diagnostic(mapped_issue: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "concept_missed": mapped_issue.get("concept", "General Python fundamentals"),
        "mistake_type": mapped_issue.get("mistake_type", "Concept misunderstanding"),
        "explanation": mapped_issue.get(
            "explanation",
            "There is a conceptual issue in your code. Focus on understanding the execution flow before patching syntax.",
        ),
        "hint_1": mapped_issue.get("hint_1", "Trace values line by line to find where assumptions fail."),
        "hint_2": mapped_issue.get("hint_2", "Ask: what condition should become true or false to finish correctly?"),
        "hint_3": mapped_issue.get("hint_3", "Apply one small fix, then re-run and compare behavior."),
        "practice": mapped_issue.get("practice", "Write a tiny version of this problem and solve it with print tracing."),
        "refactoring_suggestions": [],
    }


def _generate_refactoring_suggestions(code: str, smells: List[Dict[str, Any]]) -> List[str]:
    """Generate rule-based refactoring suggestions from code smells."""
    suggestions: List[str] = []
    for smell in smells:
        stype = smell.get("type", "")
        if stype == "Large Function":
            suggestions.append("Break this function into smaller, focused helper functions.")
        elif stype == "Deep Nesting":
            suggestions.append("Reduce nesting by using early returns or guard clauses.")
        elif stype == "Long Parameter List":
            suggestions.append("Group related parameters into a dataclass or dictionary.")
        elif stype == "Unused Variable":
            suggestions.append(f"Remove unused variable: {smell.get('message', '')}.")
        elif stype == "Duplicate String Literal":
            suggestions.append("Extract repeated string literals into named constants.")

    if not suggestions:
        suggestions.append("Consider adding docstrings to your functions.")
        suggestions.append("Review variable names for clarity and descriptiveness.")

    return suggestions[:5]


def generate_diagnostic_with_ai(
    payload: Dict[str, Any],
    mapped_issue: Dict[str, Any],
    code_smells: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Generate LLM-based diagnostic, falling back to rules if no API key."""
    api_key = os.getenv("OPENAI_API_KEY")

    # Always generate refactoring suggestions (rule-based)
    refactoring = _generate_refactoring_suggestions(
        payload.get("student_code", ""), code_smells or []
    )

    if not api_key:
        result = _fallback_diagnostic(mapped_issue)
        result["refactoring_suggestions"] = refactoring
        return result

    prompt = f"""
You are an educational coding tutor. Diagnose the conceptual misunderstanding, do not reveal full solution.

Input:
student_code:
{payload.get('student_code', '')}

error_logs:
{payload.get('error_logs', {})}

ast_analysis:
{payload.get('ast_analysis', {})}

student_history:
{payload.get('student_history', {})}

Output JSON keys only:
concept_missed, mistake_type, explanation, hint_1, hint_2, hint_3, practice, refactoring_suggestions
"""

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=prompt,
            temperature=0.2,
        )
        text = response.output_text.strip()
        if text.startswith("{"):
            result = json.loads(text)
            if "refactoring_suggestions" not in result:
                result["refactoring_suggestions"] = refactoring
            return result
    except Exception:
        pass

    result = _fallback_diagnostic(mapped_issue)
    result["refactoring_suggestions"] = refactoring
    return result
