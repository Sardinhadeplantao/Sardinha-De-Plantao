"""US Treasury daily par yield curve (official, keyless). `code` is the CSV column, e.g. '10 Yr'."""
import csv
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from kondratiev.http import get_text

URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all"


_cache: dict[int, str] = {}


def _year(series, year, session):
    if year not in _cache:  # the CSV holds every maturity: fetch each year once per run
        _cache[year] = get_text(URL.format(y=year), {"type": "daily_treasury_yield_curve", "field_tdr_date_value": year,
                                          "page": "", "_format": "csv"}, session=session)
    text = _cache[year]
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        raw = (row.get(series["code"]) or "").strip()
        if not raw or raw.upper() == "N/A":
            continue
        m, d, y = row["Date"].split("/")
        out.append((date(int(y), int(m), int(d)), float(raw), False))
    return out


def fetch(series, since=None, session=None, first_year=2000):
    years = range(first_year, date.today().year + 1)
    with ThreadPoolExecutor(max_workers=4) as pool:  # a few years at a time keeps us polite and fast
        out = [row for rows in pool.map(lambda y: _year(series, y, session), years) for row in rows]
    if not out:
        raise RuntimeError(f"no Treasury data for column {series['code']}")
    return sorted(out)


def validate(series, session=None):
    rows = fetch(series, session=session, first_year=date.today().year)
    return f"{series['code']}: latest {max(rows)[0]}"
