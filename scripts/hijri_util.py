"""Hijri calendar helpers — ONE source of truth for occasion windows (B047, June 18 2026).

Born from the scar of hardcoded Gregorian Ramadan windows scattered across the codebase
(year_map.py, build_content_calendar.py, staleness_report.py each carried their own
`date(2027,2,8) <= d <= date(2027,3,8)` guess). Those windows are correct for exactly ONE
Gregorian year and silently WRONG for every other — a 2026 render fell entirely outside the
2027 window, so real Ramadan days were mislabelled ordinary evergreen. A wrong occasion is a
post Mohamed would kill (trust is the currency; "one enforced boundary, all doors").

Ramadan is Hijri month 9 — derive it from the Hijri calendar, never from constants. This is
the single door every Ramadan check must come through.
"""
import datetime
from hijridate import Gregorian

RAMADAN_MONTH = 9  # Hijri month index for Ramadan


def hijri_month(d: datetime.date) -> int:
    """The Hijri month (1-12) a Gregorian date falls in."""
    return Gregorian(d.year, d.month, d.day).to_hijri().month


def in_ramadan(d: datetime.date) -> bool:
    """True iff the Gregorian date d falls within Ramadan (Hijri month 9), any year."""
    return hijri_month(d) == RAMADAN_MONTH
