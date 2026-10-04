from datetime import date


def status(latest_ref: date, stale_after_days: int, today: date | None = None) -> str:
    """ok: within limit; atrasado: up to 2x the limit; obsoleto: beyond."""
    age = ((today or date.today()) - latest_ref).days
    if age <= stale_after_days:
        return "ok"
    return "atrasado" if age <= 2 * stale_after_days else "obsoleto"
