"""Robert Shiller's U.S. stock market data (monthly since 1871): CAPE, price, earnings, dividends, long rate.
The workbook layout is validated on every run; a layout change fails loudly instead of loading wrong numbers.
`code` is the column header, e.g. 'CAPE'."""
import re
from datetime import date
import requests

URLS = ["https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/downloads/ie_data.xls",
        "http://www.econ.yale.edu/~shiller/data/ie_data.xls"]
HEADERS = {"CAPE": "CAPE", "Price": "P", "Earnings": "E", "Dividend": "D", "Rate GS10": "Rate GS10"}
_cache: dict = {}


def _candidates(session=None):
    """The site links the current workbook (its blob URL changes with every update); fall back to known URLs."""
    found = []
    try:
        html = (session or requests).get("https://shillerdata.com/", timeout=30).text
        found = [u.replace("&amp;", "&") for u in re.findall(r"https?://[^\"'\s>]+?ie_data\.xls[^\"'\s>]*", html)]
    except requests.RequestException:
        pass
    return list(dict.fromkeys(found + URLS))


def _last_date(wb):
    sheet = wb.sheet_by_name("Data")
    last = 0.0
    for r in range(sheet.nrows - 1, 0, -1):
        v = sheet.cell_value(r, 0)
        if isinstance(v, float) and v > 1800:
            last = v
            break
    return last


def _workbook(session=None):
    """Download every candidate link and keep the workbook with the most recent data."""
    if "wb" in _cache:
        return _cache["wb"]
    import xlrd
    best, notes = None, []
    for url in _candidates(session):
        try:
            r = (session or requests).get(url, timeout=60)
            if r.status_code >= 400 or r.content[:4] not in (b"\xd0\xcf\x11\xe0", b"PK\x03\x04"):
                notes.append(f"{url[:90]} -> HTTP {r.status_code}, not a workbook")
                continue
            wb = xlrd.open_workbook(file_contents=r.content)
            last = _last_date(wb)
            notes.append(f"{url[:90]} -> data through {last}")
            if best is None or last > best[0]:
                best = (last, wb)
        except Exception as exc:  # one bad link must not hide the others
            notes.append(f"{url[:90]} -> {type(exc).__name__}")
    print("shiller candidates:", " | ".join(notes), flush=True)
    if best is None:
        raise RuntimeError("could not download the Shiller workbook: " + " | ".join(notes))
    _cache["wb"] = best[1]
    return best[1]


def fetch(series, since=None, session=None):
    sheet = _workbook(session).sheet_by_name("Data")
    header_row = next((i for i in range(0, 15) if str(sheet.cell_value(i, 0)).strip() == "Date"), None)
    if header_row is None:
        raise RuntimeError("Shiller layout changed: header row not found")
    # headers span two rows (e.g. 'Rate' / 'GS10'); join them
    heads = [" ".join(str(sheet.cell_value(r, c)).strip() for r in (header_row - 1, header_row)).strip() for c in range(sheet.ncols)]
    wanted = series["code"]
    tokens = wanted.lower().split()
    col = next((c for c, h in enumerate(heads) if all(t in h.lower() for t in tokens)), None)
    if col is None:
        raise RuntimeError(f"Shiller layout changed: column '{wanted}' not found among {[h for h in heads if h]}")
    out = []
    for r in range(header_row + 1, sheet.nrows):
        d, v = sheet.cell_value(r, 0), sheet.cell_value(r, col)
        if not isinstance(d, float) or not isinstance(v, float):
            continue
        year, month = int(d), int(round((d - int(d)) * 100))  # 1871.01 = Jan ... 1871.1 = Oct
        if 1 <= month <= 12:
            out.append((date(year, month, 1), v, r >= sheet.nrows - 3))  # last rows are provisional
    if not out:
        raise RuntimeError(f"no Shiller data for column '{wanted}'")
    return out


def validate(series, session=None):
    rows = fetch(series, session=session)
    return f"{series['code']}: {len(rows)} observations, latest {rows[-1][0]}"
