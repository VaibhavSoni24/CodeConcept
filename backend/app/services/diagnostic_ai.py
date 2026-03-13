"""AI Diagnostic Engine — LLM-based analysis with rule-based fallback."""

import os
import json
import logging
import re
import requests
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


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
        elif stype == "Excessive Loops":
            suggestions.append("Consider combining loops or extracting loop logic into helper functions.")

    if not suggestions:
        suggestions.append("Consider adding docstrings to your functions.")
        suggestions.append("Review variable names for clarity and descriptiveness.")

    return suggestions[:5]


def _extract_json(text: str) -> dict | None:
    """Extract JSON from text that may be wrapped in markdown code fences."""
    # Strip markdown code fences like ```json ... ```
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def generate_diagnostic_with_ai(
    payload: Dict[str, Any],
    mapped_issue: Dict[str, Any],
    code_smells: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Generate LLM-based diagnostic, falling back to rules if no API key."""
    api_key = os.getenv("INCEPTION_API_KEY", "sk_e63438e4b9d465e41f5454ed81b7198a")

    # Always generate refactoring suggestions (rule-based)
    refactoring = _generate_refactoring_suggestions(
        payload.get("student_code", ""), code_smells or []
    )

    if not api_key:
        logger.info("No INCEPTION_API_KEY set — using rule-based fallback.")
        result = _fallback_diagnostic(mapped_issue)
        result["refactoring_suggestions"] = refactoring
        return result

    prompt = f"""
You are an educational coding tutor. Diagnose the conceptual misunderstanding, if any. Do not reveal full solution.
If the code is perfectly fine and there are no conceptual misunderstandings or logical errors:
- Set mistake_type to "none"
- Set concept_missed to "Basic implementation"
- Provide an explanation praising the logic or code.
- Provide suggestions for advanced variations or optimizations in hints.

Input:
student_code:
{payload.get('student_code', '')}

error_logs:
{payload.get('error_logs', {})}

ast_analysis:
{payload.get('ast_analysis', {})}

student_history:
{payload.get('student_history', {})}
"""

    response_schema = {
        "name": "Diagnostic",
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
                "refactoring_suggestions": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": [
                "concept_missed", "mistake_type", "explanation",
                "hint_1", "hint_2", "hint_3", "practice", "refactoring_suggestions"
            ]
        }
    }

    url = "https://api.inceptionlabs.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    data = {
        "model": "mercury-2",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": response_schema
        },
        "stream": False,
    }

    try:
        logger.info("Sending request to Inception AI API…")
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=25)
        response.raise_for_status()
        
        res_json = response.json()
        text = res_json["choices"][0]["message"]["content"].strip()
        logger.info("Received response from Inception AI API (%d chars).", len(text))

        result = _extract_json(text)
        if result:
            if "refactoring_suggestions" not in result:
                result["refactoring_suggestions"] = refactoring
            elif not isinstance(result["refactoring_suggestions"], list):
                # Ensure it's a list even if AI returned a string
                if isinstance(result["refactoring_suggestions"], str):
                    result["refactoring_suggestions"] = [result["refactoring_suggestions"]]
                else:
                    result["refactoring_suggestions"] = refactoring
            return result
        else:
            logger.warning("Could not parse JSON from Inception AI response, using fallback.")
    except Exception as exc:
        logger.exception("Inception AI API call failed: %s", exc)

    result = _fallback_diagnostic(mapped_issue)
    result["refactoring_suggestions"] = refactoring
    return result

