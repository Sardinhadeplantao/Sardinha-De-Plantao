"""US Treasury daily par yield curve (official, keyless). `code` is the CSV column, e.g. '10 Yr'."""
import csv
import io
from datetime import date
from kondratiev.http import get_text

URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all"


def fetch(series, since=None, session=None, first_year=2000):
    out = []
    for year in range(first_year, date.today().year + 1):
        text = get_text(URL.format(y=year), {"type": "daily_treasury_yield_curve", "field_tdr_date_value": year,
                                              "page": "", "_format": "csv"}, min_interval=1.0, session=session)
        for row in csv.DictReader(io.StringIO(text)):
            raw = (row.get(series["code"]) or "").strip()
            if not raw or raw.upper() == "N/A":
                continue
            m, d, y = row["Date"].split("/")
            out.append((date(int(y), int(m), int(d)), float(raw), False))
    if not out:
        raise RuntimeError(f"no Treasury data for column {series['code']}")
    return out


def validate(series, session=None):
    rows = fetch(series, session=session, first_year=date.today().year)
    return f"{series['code']}: latest {max(rows)[0]}"
