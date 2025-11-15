import json
import re

def extract_json_block(text: str):
    """
    Extract JSON from an LLM response, even if wrapped in markdown fences
    like ```json ... ``` or mixed with other text.
    Returns a dict or None.
    """
    if not text:
        return None

    # Remove markdown fences
    cleaned = (
        text.replace("```json", "")
            .replace("```", "")
            .strip()
    )

    # Capture the JSON object between {...}
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None

    json_str = match.group(0)

    # Try parsing
    try:
        return json.loads(json_str)
    except Exception:
        return None
