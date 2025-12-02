def normalize_insights(insights: dict) -> dict:
    """
    Normalize insights object to the new bullet-list schema.
    Converts old paragraph-style strings into 1-item lists.
    Ensures all required fields exist as lists.
    """

    if not insights:
        return {}

    required_fields = [
        "trend_summary",
        "risk_trend",
        "compliance_trend",
        "recurring_issues",
        "category_hotspots",
        "recommendations",
        "anomaly_detection"
    ]

    normalized = dict(insights)

    for field in required_fields:

        value = normalized.get(field)

        # ---- Case 1: Missing field → empty list
        if value is None:
            normalized[field] = []
            continue

        # ---- Case 2: Already proper list
        if isinstance(value, list):
            normalized[field] = [
                str(item).strip()
                for item in value
                if isinstance(item, (str, int, float)) and str(item).strip()
            ]
            continue

        # ---- Case 3: Old paragraph string → convert to single bullet
        if isinstance(value, str):
            cleaned = value.strip()
            normalized[field] = [cleaned] if cleaned else []
            continue

        # ---- Case 4: Numbers or objects → stringify
        normalized[field] = [str(value)]

    return normalized
