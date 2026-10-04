"""HTTP helper: rate limiting and retry with exponential backoff."""
import time
import requests

_last_call: dict[str, float] = {}


def get_json(*a, **k):
    return _get(*a, parse=lambda r: r.json(), **k)


def get_text(*a, **k):
    return _get(*a, parse=lambda r: r.text, **k)


def _get(url, params=None, headers=None, min_interval=0.0, retries=2, session=None, timeout=20, parse=None):
    """GET a document. `min_interval` spaces calls to the same host (rate limit)."""
    host = url.split("/")[2]
    s = session or requests
    delay = 2.0
    for attempt in range(retries + 1):
        wait = _last_call.get(host, 0) + min_interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_call[host] = time.monotonic()
        try:
            r = s.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {r.status_code}")
            if r.status_code >= 400:  # not retryable (bad key, bad id): fail now, report the status only
                raise RuntimeError(f"request to {url} failed: HTTP {r.status_code}")
            r.raise_for_status()
            return parse(r)
        except RuntimeError:
            raise
        except (requests.RequestException, ValueError) as exc:
            if attempt == retries:
                # never include params: they may carry an API key
                raise RuntimeError(f"request to {url} failed: {type(exc).__name__} {exc if isinstance(exc, requests.HTTPError) else ''}".strip()) from None
            time.sleep(delay)
            delay *= 2
