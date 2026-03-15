"""AI Diagnostic Engine — LLM-based analysis with rule-based fallback."""

import os
import json
from typing import Dict, Any, List
import requests
from dotenv import load_dotenv

load_dotenv()


def _fallback_diagnostic(mapped_issue: Dict[str, Any]) -> Dict[str, Any]:
    mistake_type = mapped_issue.get("mistake_type", "Concept misunderstanding")
    if mistake_type == "none":
        understanding_score = 80
    elif mistake_type in {"syntax", "syntax_error"}:
        understanding_score = 55
    else:
        understanding_score = 45

    return {
        "concept_missed": mapped_issue.get("concept", "General Python fundamentals"),
        "mistake_type": mistake_type,
        "explanation": mapped_issue.get(
            "explanation",
            "There is a conceptual issue in your code. Focus on understanding the execution flow before patching syntax.",
        ),
        "hint_1": mapped_issue.get("hint_1", "Trace values line by line to find where assumptions fail."),
        "hint_2": mapped_issue.get("hint_2", "Ask: what condition should become true or false to finish correctly?"),
        "hint_3": mapped_issue.get("hint_3", "Apply one small fix, then re-run and compare behavior."),
        "practice": mapped_issue.get("practice", "Write a tiny version of this problem and solve it with print tracing."),
        "understanding_score": understanding_score,
        "concept_scores": {},
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
    api_key = os.getenv("INCEPTION_API_KEY")

    # Always generate refactoring suggestions (rule-based)
    refactoring = _generate_refactoring_suggestions(
        payload.get("student_code", ""), code_smells or []
    )

    if not api_key:
        result = _fallback_diagnostic(mapped_issue)
        result["refactoring_suggestions"] = refactoring
        return result

    prompt = f"""
You are an educational coding tutor. Diagnose the conceptual misunderstanding and do not reveal the full solution.

Input:
Language: {payload.get('language', 'python')}

student_code:
{payload.get('student_code', '')}

error_logs:
{payload.get('error_logs', {})}

ast_analysis:
{payload.get('ast_analysis', {})}

student_history:
{payload.get('student_history', {})}

Return strictly valid JSON with keys only:
concept_missed, mistake_type, explanation, hint_1, hint_2, hint_3, practice, understanding_score, concept_scores

Scoring rules:
- understanding_score: integer 0-100 based on conceptual understanding and code quality.
- concept_scores: object mapping concept names to integer 0-100.
- Keep scores realistic and granular (avoid only 0 or 100 unless clearly warranted).
"""

    response_schema = {
        "name": "DiagnosticResult",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "concept_missed": {"type": "string"},
                "mistake_type": {"type": "string"},
                "explanation": {"type": "string"},
                "hint_1": {"type": "string"},
                "hint_2": {"type": "string"},
                "hint_3": {"type": "string"},
                "practice": {"type": "string"},
                "understanding_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "concept_scores": {
                    "type": "object",
                    "additionalProperties": {"type": "integer", "minimum": 0, "maximum": 100},
                },
            },
            "required": [
                "concept_missed",
                "mistake_type",
                "explanation",
                "hint_1",
                "hint_2",
                "hint_3",
                "practice",
                "understanding_score",
                "concept_scores",
            ],
            "additionalProperties": False,
        },
    }

    request_body = {
        "model": os.getenv("INCEPTION_MODEL", "mercury-2"),
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {
            "type": "json_schema",
            "json_schema": response_schema,
        },
        "stream": False,
    }

    try:
        response = requests.post(
            "https://api.inceptionlabs.ai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            data=json.dumps(request_body),
            timeout=20,
        )
        response.raise_for_status()
        body = response.json()

        content = (
            body.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if isinstance(content, list):
            # Some providers return a list of content parts.
            text = "".join(part.get("text", "") for part in content if isinstance(part, dict)).strip()
        elif isinstance(content, dict):
            result = content
            result["refactoring_suggestions"] = refactoring
            return result
        else:
            text = str(content).strip()

        # Accept JSON wrapped in markdown/code fences.
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        if not text.startswith("{") and "{" in text and "}" in text:
            text = text[text.find("{"): text.rfind("}") + 1]

        if text.startswith("{"):
            result = json.loads(text)
            if not isinstance(result.get("understanding_score"), int):
                result["understanding_score"] = 60
            result["understanding_score"] = max(0, min(100, result["understanding_score"]))

            concept_scores = result.get("concept_scores")
            if not isinstance(concept_scores, dict):
                result["concept_scores"] = {}
            else:
                sanitized_scores = {}
                for key, value in concept_scores.items():
                    if not isinstance(key, str):
                        continue
                    if isinstance(value, bool):
                        continue
                    if isinstance(value, (int, float)):
                        sanitized_scores[key] = int(max(0, min(100, round(value))))
                result["concept_scores"] = sanitized_scores

            result["refactoring_suggestions"] = refactoring
            return result
    except Exception:
        pass

    result = _fallback_diagnostic(mapped_issue)
    result["refactoring_suggestions"] = refactoring
    return result
