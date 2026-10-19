# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Period date helpers for the Decision Center.

Each period key maps to a (from_date, to_date) range.  A comparison
"previous period" of the same length is computed automatically.
"""

from __future__ import unicode_literals

from datetime import date, timedelta

from frappe.utils import getdate, nowdate, get_first_day, get_last_day, add_days


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_period_dates(period_key, custom_from=None, custom_to=None):
    """Return (from_date, to_date, prev_from, prev_to) for the given key.

    Args:
        period_key: One of the recognised keys below, or ``"custom"``.
        custom_from / custom_to: Required when *period_key* is ``"custom"``.

    Returns:
        Tuple of four ``datetime.date`` objects.
    """
    today = getdate(nowdate())
    from_date = to_date = None

    if period_key == "today":
        from_date = to_date = today

    elif period_key == "last_7_days":
        to_date = today
        from_date = today - timedelta(days=6)

    elif period_key == "last_30_days":
        to_date = today
        from_date = today - timedelta(days=29)

    elif period_key == "this_month":
        from_date = get_first_day(today)
        to_date = today

    elif period_key == "last_month":
        last_month_end = get_first_day(today) - timedelta(days=1)
        from_date = get_first_day(last_month_end)
        to_date = last_month_end

    elif period_key == "this_quarter":
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        from_date = date(today.year, quarter_month, 1)
        to_date = today

    elif period_key == "this_year":
        from_date = date(today.year, 1, 1)
        to_date = today

    elif period_key == "custom":
        if not custom_from or not custom_to:
            raise ValueError("custom_from and custom_to are required for custom period")
        from_date = getdate(custom_from)
        to_date = getdate(custom_to)

    else:
        # Fallback: last 30 days
        to_date = today
        from_date = today - timedelta(days=29)

    # Ensure from <= to
    if from_date > to_date:
        from_date, to_date = to_date, from_date

    # ── Compute previous comparison period ──
    # Calendar period-to-date periods compare to the same elapsed portion
    # of the previous calendar period.  Rolling periods use equal-length
    # sliding windows.
    prev_from, prev_to = _compute_comparison_period(
        period_key, from_date, to_date, today)

    return from_date, to_date, prev_from, prev_to


# ---------------------------------------------------------------------------
# Comparison period logic
# ---------------------------------------------------------------------------

def _compute_comparison_period(period_key, from_date, to_date, today):
    """Return (prev_from, prev_to) for the comparison period.

    Calendar periods (this_month, this_quarter, this_year) use
    **period-to-date** comparison: same elapsed days in the previous
    calendar period.

    Rolling periods (last_7_days, last_30_days, today) and custom
    periods use an equal-length sliding window.
    """

    if period_key == "this_month":
        # Same elapsed days of previous month
        elapsed_days = (to_date - from_date).days  # 0-based day-of-month offset
        prev_month_start = get_first_day(from_date - timedelta(days=1))
        prev_to = min(
            prev_month_start + timedelta(days=elapsed_days),
            get_last_day(prev_month_start),  # clamp to month end
        )
        return prev_month_start, prev_to

    elif period_key == "last_month":
        # Full previous month vs full month before that
        prev_end = from_date - timedelta(days=1)
        prev_start = get_first_day(prev_end)
        return prev_start, prev_end

    elif period_key == "this_quarter":
        # Same elapsed portion of previous quarter
        elapsed_days = (to_date - from_date).days
        prev_q_start = _quarter_start(from_date, offset=-1)
        prev_to = prev_q_start + timedelta(days=elapsed_days)
        # Clamp to previous quarter end
        prev_q_end = from_date - timedelta(days=1)
        prev_to = min(prev_to, prev_q_end)
        return prev_q_start, prev_to

    elif period_key == "this_year":
        # Same elapsed portion of previous year
        elapsed_days = (to_date - from_date).days
        prev_year_start = date(today.year - 1, 1, 1)
        prev_to = prev_year_start + timedelta(days=elapsed_days)
        # Clamp to Dec 31 of previous year
        prev_year_end = date(today.year - 1, 12, 31)
        prev_to = min(prev_to, prev_year_end)
        return prev_year_start, prev_to

    else:
        # Rolling / custom: equal-length sliding window
        delta = (to_date - from_date).days
        prev_to = from_date - timedelta(days=1)
        prev_from = prev_to - timedelta(days=delta)
        return prev_from, prev_to


def _quarter_start(ref_date, offset=0):
    """Return the first day of the quarter containing *ref_date*,
    shifted by *offset* quarters (e.g. -1 for previous quarter)."""
    # Current quarter index (0-based)
    q = (ref_date.month - 1) // 3 + offset
    year = ref_date.year
    # Handle year wraparound
    while q < 0:
        q += 4
        year -= 1
    while q > 3:
        q -= 4
        year += 1
    month = q * 3 + 1
    return date(year, month, 1)
