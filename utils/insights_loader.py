import json
from typing import Optional, Dict, Any
from db import db_util
from datetime import datetime

def safe_call(fn, *args, default=None, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return default

def get_latest_insights() -> Optional[Dict[str, Any]]:
    insights_history = safe_call(db_util.get_insights_history, limit=1, default=[])

    if not insights_history:
        return None
    
    latest = insights_history[0]

    try:
        insights_data = json.loads(latest["insights_data"])
    except:
        return None

    return {
        "run_id": latest["run_id"],
        "timestamp": latest["timestamp"],
        "insights": insights_data
    }
