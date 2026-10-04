import os
from datetime import date
from kondratiev.http import get_json

BASE = "https://api.stlouisfed.org/fred"


def _key():
    key = (os.environ.get("FRED_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("FRED_API_KEY is not set")
    return key


def _parse(code):
    """'A' -> ('A', None, 1.0); 'A/B*0.1' -> ('A', 'B', 0.1): ratio of two series on matching dates, scaled."""
    scale = 1.0
    if "*" in code:
        code, k = code.split("*")
        scale = float(k)
    num, _, den = code.partition("/")
    return num, den or None, scale


def fetch(series, since=None, session=None):
    """Return [(ref_date, value, is_provisional)]. FRED encodes missing values as '.'."""
    num, den, scale = _parse(series["code"])
    if den:
        a = {d: v for d, v, _ in _observations(num, since, session)}
        b = {d: v for d, v, _ in _observations(den, since, session)}
        return [(d, a[d] / b[d] * scale, False) for d in sorted(a) if d in b and b[d]]
    return [(d, v * scale, p) for d, v, p in _observations(num, since, session)]


def _observations(code, since=None, session=None):
    params = {"series_id": code, "api_key": _key(), "file_type": "json"}
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
    """Confirm the series IDs exist; return their titles."""
    num, den, _ = _parse(series["code"])
    titles = []
    for code in filter(None, (num, den)):
        data = get_json(f"{BASE}/series", {"series_id": code, "api_key": _key(), "file_type": "json"},
                        min_interval=0.5, session=session)
        titles.append(data["seriess"][0]["title"])
    return " / ".join(titles)
