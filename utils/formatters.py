from datetime import datetime

def format_timestamp(ts: str) -> str:
    if not ts or ts == "N/A":
        return "N/A"

    # Normalize common ISO variants
    ts = ts.strip().replace("T", " ").replace("Z", "")

    # Try known formats in sequence
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ):
        try:
            dt = datetime.strptime(ts, fmt)
            return dt.strftime("%Y-%b-%d %H:%M")
        except:
            pass

    # Final fallback
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%b-%d %H:%M")
    except:
        return ts
