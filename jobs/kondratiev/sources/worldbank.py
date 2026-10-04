from datetime import date
from kondratiev.http import get_json

BASE = "https://api.worldbank.org/v2"


def fetch(series, since=None, session=None):
    """Annual series; ref_date is the end of the reference year. Null values are skipped."""
    url = f"{BASE}/country/{series['country']}/indicator/{series['code']}"
    data = get_json(url, {"format": "json", "per_page": 500, "date": f"1960:{date.today().year}"}, session=session)
    if not isinstance(data, list) or len(data) < 2 or data[1] is None:
        raise RuntimeError(f"unexpected World Bank response for {series['code']} (invalid indicator?)")
    out = []
    for r in data[1]:
        if r["value"] is None:
            continue
        out.append((date(int(r["date"]), 12, 31), float(r["value"]), False))
    return out


def validate(series, session=None):
    rows = fetch(series, session=session)
    if not rows:
        raise RuntimeError(f"no data for {series['code']}")
    return f"{series['code']}: {len(rows)} observations"
