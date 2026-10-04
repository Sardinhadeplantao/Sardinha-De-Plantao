"""Ember monthly electricity data (open data, keyless): generation mix and power-sector CO2 intensity by country.
`code` is 'AREA|Category|Variable|Unit', where AREA matches the ISO-3 code or the area name (e.g. 'USA' or 'World').
The file is large, so it is streamed once per run and only the requested rows are kept."""
import csv
import io
from datetime import date
import requests

URLS = ["https://storage.googleapis.com/emb-prod-bkt-publicdata/public-downloads/monthly_full_release_long_format.csv"]
_cache: dict = {}


def _rows(session=None):
    if "rows" in _cache:
        return _cache["rows"]
    last = None
    for url in URLS:
        try:
            r = (session or requests).get(url, timeout=180, stream=True)
            if r.status_code >= 400:
                last = f"HTTP {r.status_code}"
                continue
            text = r.text if not hasattr(r, "iter_lines") else "\n".join(l.decode("utf-8", "replace") if isinstance(l, bytes) else l for l in r.iter_lines())
            reader = csv.DictReader(io.StringIO(text))
            keep = []
            for row in reader:
                cat = (row.get("Category") or "").lower()
                if cat in ("electricity generation", "power sector emissions"):
                    keep.append(row)
            if not keep:
                raise RuntimeError(f"Ember layout changed: columns {reader.fieldnames}")
            _cache["rows"] = keep
            return keep
        except requests.RequestException as exc:
            last = type(exc).__name__
    raise RuntimeError(f"could not download Ember data ({last})")


def fetch(series, since=None, session=None):
    area, category, variable, unit = [p.strip().lower() for p in series["code"].split("|")]
    out = {}
    for row in _rows(session):
        names = {(row.get("ISO 3 code") or "").lower(), (row.get("Area") or "").lower()}
        if area not in names or (row.get("Category") or "").lower() != category:
            continue
        if (row.get("Variable") or "").lower() != variable or (row.get("Unit") or "").lower() != unit:
            continue
        try:
            y, m = row["Date"][:7].split("-")
            out[date(int(y), int(m), 1)] = float(row["Value"])
        except (ValueError, KeyError):
            continue
    if not out:
        raise RuntimeError(f"no Ember data for {series['code']}")
    return [(d, out[d], False) for d in sorted(out)]


def validate(series, session=None):
    rows = fetch(series, session=session)
    return f"{series['code']}: {len(rows)} months, latest {rows[-1][0]}"
