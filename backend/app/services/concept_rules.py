import json
from pathlib import Path
from typing import Dict, Any


RULE_PATH = Path(__file__).resolve().parent.parent / "data" / "concept_rules.json"


def load_rules() -> Dict[str, Any]:
    with open(RULE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)
