"""BIS statistics (official, keyless) through the SDMX REST API. `code` is '<dataflow>/<key>', e.g.
'WS_CREDIT_GAP/Q.US.P.A.C' (credit-to-GDP gap, US, private non-financial sector, actual minus HP trend)."""
import csv
import io
from datetime import date
from kondratiev.http import get_text

BASE = "https://stats.bis.org/api/v1/data"


def _quarter_end(label: str) -> date:
    year, q = label.split("-Q")
    month = int(q) * 3
    return date(int(year), month, 30 if month in (6, 9) else 31)


def fetch(series, since=None, session=None):
    text = get_text(f"{BASE}/{series['code']}", {"format": "csv"}, session=session, min_interval=1.0)
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        period, value = row.get("TIME_PERIOD", ""), (row.get("OBS_VALUE") or "").strip()
        if "-Q" not in period or not value:
            continue
        out.append((_quarter_end(period), float(value), False))
    if not out:
        raise RuntimeError(f"no BIS data for {series['code']}")
    return sorted(out)


def validate(series, session=None):
    rows = fetch(series, session=session)
    return f"{series['code']}: {len(rows)} observations, latest {rows[-1][0]}"
