import os
from datetime import date
from kondratiev.http import get_json

BASE = "https://api.stlouisfed.org/fred"


def _key():
    key = (os.environ.get("FRED_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("FRED_API_KEY is not set")
    return key


def fetch(series, since=None, session=None):
    """Return [(ref_date, value, is_provisional)]. FRED encodes missing values as '.'."""
    params = {"series_id": series["code"], "api_key": _key(), "file_type": "json"}
    if since:
        params["observation_start"] = since.isoformat()
    data = get_json(f"{BASE}/series/observations", params, min_interval=0.5, session=session)  # <120 req/min
    out = []
    for o in data.get("observations", []):
        if o["value"] in (".", "", None):
            continue
        out.append((date.fromisoformat(o["date"]), float(o["value"]), False))
    return out


def validate(series, session=None):
    """Confirm the series ID exists; return its title."""
    data = get_json(f"{BASE}/series", {"series_id": series["code"], "api_key": _key(), "file_type": "json"},
                    min_interval=0.5, session=session)
    return data["seriess"][0]["title"]
