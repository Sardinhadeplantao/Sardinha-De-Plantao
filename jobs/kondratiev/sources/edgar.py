"""SEC EDGAR XBRL company facts (official, keyless; the SEC requires a descriptive User-Agent).

Hyperscaler AI-capex proxy: trailing-four-quarter capital expenditure and operating cash flow, summed over
Microsoft, Alphabet, Amazon, Meta and Oracle. `code` is 'capex_ocf' (ratio, %) or 'capex' (US$ bn).
Cash-flow statements report year-to-date amounts, so discrete quarters are rebuilt by differencing."""
import os
from datetime import date, datetime
import requests
from kondratiev.http import get_json

COMPANIES = {"MSFT": 789019, "GOOGL": 1652044, "AMZN": 1018724, "META": 1326801, "ORCL": 1341439}
CAPEX, OCF = "PaymentsToAcquirePropertyPlantAndEquipment", "NetCashProvidedByUsedInOperatingActivities"
UA = os.environ.get("SEC_USER_AGENT") or "KondratievMonitor/0.3 (+https://github.com/Sardinhadeplantao/Sardinha-De-Plantao)"
_cache: dict = {}


def _facts(cik, session=None):
    if cik not in _cache:
        _cache[cik] = get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
                               headers={"User-Agent": UA}, min_interval=0.3, session=session)
    return _cache[cik]


def _d(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def discrete_quarters(entries):
    """entries: facts with start/end/val/filed. Returns {quarter_end: discrete value} from year-to-date amounts."""
    best = {}
    for e in entries:
        if e.get("form") not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            continue
        key = (e["start"], e["end"])
        if key not in best or e["filed"] > best[key]["filed"]:
            best[key] = e
    by_start = {}
    for (s, en), e in best.items():
        days = (_d(en) - _d(s)).days
        if days > 400:
            continue
        by_start.setdefault(s, {})[en] = (days, e["val"])
    out = {}
    for s, ends in by_start.items():
        prev_val, prev_end = 0.0, None
        for en in sorted(ends):
            days, val = ends[en]
            span = (_d(en) - _d(prev_end)).days if prev_end else days
            if prev_end is None or 60 <= span <= 120:  # consecutive year-to-date points roughly one quarter apart
                out[_d(en)] = val - prev_val
                prev_val, prev_end = val, en
    return out


def ttm(quarters):
    """Trailing four discrete quarters, only when they are consecutive (about 91 days apart)."""
    ends = sorted(quarters)
    res = {}
    for i in range(3, len(ends)):
        w = ends[i - 3:i + 1]
        if all(70 <= (w[k + 1] - w[k]).days <= 110 for k in range(3)):
            res[w[-1]] = sum(quarters[x] for x in w)
    return res


def _calendar_quarter(d):
    """Map a fiscal quarter end to the nearest calendar quarter end (Aug->Sep, Nov->Dec, Feb->Mar, May->Jun)."""
    m = d.month
    m = {1: 3, 2: 3, 3: 3, 4: 6, 5: 6, 6: 6, 7: 9, 8: 9, 9: 9, 10: 12, 11: 12, 12: 12}[m]
    y = d.year + (1 if d.month == 12 and m == 3 else 0)
    return date(y, m, 30 if m in (6, 9) else 31)


def fetch(series, since=None, session=None):
    per_company = {}
    for name, cik in COMPANIES.items():
        gaap = _facts(cik, session)["facts"]["us-gaap"]
        cap = ttm(discrete_quarters(gaap[CAPEX]["units"]["USD"]))
        ocf = ttm(discrete_quarters(gaap[OCF]["units"]["USD"]))
        per_company[name] = {_calendar_quarter(d): (cap[d], ocf[d]) for d in cap if d in ocf}
    quarters = set.intersection(*(set(v) for v in per_company.values()))
    if not quarters:
        raise RuntimeError("no common quarters across the five companies")
    out = []
    for q in sorted(quarters):
        capex = sum(per_company[c][q][0] for c in per_company)
        ocf = sum(per_company[c][q][1] for c in per_company)
        if series["code"] == "capex_ocf":
            out.append((q, capex / ocf * 100, False))
        else:
            out.append((q, capex / 1e9, False))
    return out


def validate(series, session=None):
    rows = fetch(series, session=session)
    return f"{series['code']}: {len(rows)} quarters, latest {rows[-1][0]} = {rows[-1][1]:.1f}"
