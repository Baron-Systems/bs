# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Expense analysis for the Decision Center.

Expense movement is defined as SUM(debit - credit) over operating-period
GL entries only. Closing, cancelled, and opening entries are excluded.
"""

from __future__ import unicode_literals

import frappe
from frappe.utils import flt, getdate, add_to_date, date_diff


# ───────────────────────────────────────────────────────────────────────────
# Category / account mapping
# ───────────────────────────────────────────────────────────────────────────


def get_expense_categories(enabled_only=True):
    """Return expense categories with their mapped accounts."""
    filters = {}
    if enabled_only:
        filters["enabled"] = 1

    categories = frappe.get_all(
        "Decision Center Expense Category",
        filters=filters,
        fields=["name", "category_name", "description", "enabled",
                "target_percent_of_sales", "max_percent_of_sales"],
        order_by="category_name",
    )

    account_rows = frappe.get_all(
        "Decision Center Expense Account",
        filters={"parenttype": "Decision Center Expense Category", "enabled": 1},
        fields=["parent", "account", "description", "enabled"],
    )

    account_map = {}
    for row in account_rows:
        account_map.setdefault(row.parent, []).append({
            "account": row.account,
            "description": row.description,
            "enabled": row.enabled,
        })

    for cat in categories:
        cat["accounts"] = account_map.get(cat.name, [])

    return categories


def get_enabled_expense_accounts():
    """Return set of all enabled mapped expense account names."""
    rows = frappe.get_all(
        "Decision Center Expense Account",
        filters={"parenttype": "Decision Center Expense Category", "enabled": 1},
        fields=["account"],
    )
    return {r.account for r in rows}


def get_account_to_category_map():
    """Return dict {account: category_name} for enabled mappings."""
    rows = frappe.db.sql("""
        SELECT dcea.account, dcec.category_name
        FROM `tabDecision Center Expense Account` dcea
        INNER JOIN `tabDecision Center Expense Category` dcec
            ON dcea.parent = dcec.name
        WHERE dcea.enabled = 1 AND dcec.enabled = 1
    """, as_dict=True)
    return {r.account: r.category_name for r in rows}


# ───────────────────────────────────────────────────────────────────────────
# GL expense aggregation
# ───────────────────────────────────────────────────────────────────────────


def _expense_gl_query(accounts, company, from_date, to_date):
    """Return total (debit - credit) for mapped accounts in date range."""
    if not accounts:
        return []

    return frappe.db.sql("""
        SELECT
            account,
            COALESCE(SUM(debit - credit), 0) AS amount
        FROM `tabGL Entry`
        WHERE company = %(company)s
          AND account IN %(accounts)s
          AND posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND is_cancelled = 0
          AND is_opening != 'Yes'
          AND voucher_type != 'Period Closing Voucher'
        GROUP BY account
    """, {
        "company": company,
        "accounts": tuple(accounts),
        "from_date": from_date,
        "to_date": to_date,
    }, as_dict=True)


def _period_length_days(from_date, to_date):
    return max(date_diff(getdate(to_date), getdate(from_date)), 0) + 1


def _historical_periods(period_length_days, current_from, current_to, count=3):
    """Build `count` comparable previous periods of the same length."""
    periods = []
    length = period_length_days
    end = add_to_date(getdate(current_from), days=-1)
    for _ in range(count):
        start = add_to_date(end, days=-(length - 1))
        periods.append((start, end))
        end = add_to_date(start, days=-1)
    return list(reversed(periods))


# ───────────────────────────────────────────────────────────────────────────
# Metrics
# ───────────────────────────────────────────────────────────────────────────


def get_expense_metrics(company, from_date, to_date, prev_from, prev_to):
    """Return expense metrics with previous-period comparison and category detail."""
    account_map = get_account_to_category_map()
    accounts = list(account_map.keys())

    current_rows = {r.account: flt(r.amount) for r in _expense_gl_query(accounts, company, from_date, to_date)}
    previous_rows = {r.account: flt(r.amount) for r in _expense_gl_query(accounts, company, prev_from, prev_to)}

    total = sum(current_rows.values())
    prev_total = sum(previous_rows.values())

    category_current = {}
    category_previous = {}
    account_metrics = []

    for account in accounts:
        category = account_map[account]
        cur = current_rows.get(account, 0)
        prev = previous_rows.get(account, 0)
        category_current[category] = category_current.get(category, 0) + cur
        category_previous[category] = category_previous.get(category, 0) + prev

        account_metrics.append({
            "account": account,
            "category": category,
            "current_amount": cur,
            "previous_amount": prev,
            "growth_pct": _expense_growth_pct(prev, cur),
        })

    categories = get_expense_categories()
    category_metrics = []
    for cat in categories:
        name = cat.category_name
        cur = category_current.get(name, 0)
        prev = category_previous.get(name, 0)
        category_metrics.append({
            "category": name,
            "current_amount": cur,
            "previous_amount": prev,
            "growth_pct": _expense_growth_pct(prev, cur),
            "target_percent_of_sales": flt(cat.target_percent_of_sales),
            "max_percent_of_sales": flt(cat.max_percent_of_sales),
        })

    return {
        "total": total,
        "previous_total": prev_total,
        "growth_pct": _expense_growth_pct(prev_total, total),
        "categories": category_metrics,
        "accounts": account_metrics,
    }


def get_expense_trend(company, accounts, from_date, to_date, granularity="monthly"):
    """Return monthly or weekly trend for mapped accounts."""
    if not accounts:
        return []

    if granularity == "weekly":
        period_expr = "YEARWEEK(posting_date)"
        label_expr = "CONCAT(YEAR(posting_date), '-W', WEEK(posting_date))"
    else:
        period_expr = "DATE_FORMAT(posting_date, '%%Y-%%m')"
        label_expr = "DATE_FORMAT(posting_date, '%%Y-%%m')"

    rows = frappe.db.sql("""
        SELECT
            {label} AS label,
            {period} AS period_key,
            COALESCE(SUM(debit - credit), 0) AS amount
        FROM `tabGL Entry`
        WHERE company = %(company)s
          AND account IN %(accounts)s
          AND posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND is_cancelled = 0
          AND is_opening != 'Yes'
          AND voucher_type != 'Period Closing Voucher'
        GROUP BY period_key
        ORDER BY period_key
    """.format(label=label_expr, period=period_expr), {
        "company": company,
        "accounts": tuple(accounts),
        "from_date": from_date,
        "to_date": to_date,
    }, as_dict=True)

    return [{"label": r.label, "amount": flt(r.amount)} for r in rows]


# ───────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────


def _expense_growth_pct(old, new):
    """Percentage change; returns None when old <= 0 to avoid misleading ratios."""
    old = flt(old)
    new = flt(new)
    if old <= 0:
        return None
    return flt(((new - old) / old) * 100, 2)


def get_expense_anomaly_baseline(company, accounts, current_from, current_to, periods_count=3):
    """Return average expense over the previous N comparable periods.

    Returns None if there is not enough history to compare.
    """
    if not accounts:
        return None

    length = _period_length_days(current_from, current_to)
    historical = _historical_periods(length, current_from, current_to, count=periods_count)

    totals = []
    for start, end in historical:
        rows = _expense_gl_query(accounts, company, start, end)
        totals.append(sum(flt(r.amount) for r in rows))

    # Require all requested periods to have data before triggering anomaly
    if len(totals) < periods_count or any(t == 0 for t in totals):
        return None

    return flt(sum(totals) / len(totals), 2)
