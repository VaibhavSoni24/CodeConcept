import os
from typing import Dict, Any
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
    }


def generate_diagnostic_with_ai(payload: Dict[str, Any], mapped_issue: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_diagnostic(mapped_issue)

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
concept_missed, mistake_type, explanation, hint_1, hint_2, hint_3, practice
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
            import json
            return json.loads(text)
    except Exception:
        return _fallback_diagnostic(mapped_issue)

    return _fallback_diagnostic(mapped_issue)
