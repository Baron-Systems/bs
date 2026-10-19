# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Decision Center Metric Capability Registry and computation dispatcher.

This module defines:
- The canonical list of metrics the Decision Center can reason about.
- Metadata for each metric (baseline strategy, progress strategy, etc.).
- A dispatcher to compute a metric value for a given date range.
- Baseline computation helpers.
- Progress / health / target-achievement helpers that respect metric semantics.

No AI/LLM logic is used. All calculations are deterministic and auditable.
"""

from __future__ import unicode_literals

from datetime import date, timedelta

import frappe
from frappe.utils import cint, flt, getdate, nowdate

from .config import get_decision_center_settings, get_threshold
from .expenses import get_expense_categories, get_expense_metrics
from .metrics import (
    get_customer_sales,
    get_item_sales,
    get_item_stock,
    get_purchase_metrics,
    get_sales_metrics,
)
from .periods import get_period_dates

ENGINE_VERSION = "1.0.0"

# Metric key -> canonical metadata.  Only the code (patches/maintenance) may
# change system-controlled fields; Settings UI may only toggle `enabled_for_plans`.
METRIC_REGISTRY = {
    "sales_total": {
        "metric_label_ar": "إجمالي المبيعات",
        "metric_label_en": "Sales Total",
        "category": "sales",
        "unit": "currency",
        "system_available": 1,
        "enabled_for_plans": 1,
        "unavailable_reason": "",
        "formula_description": "SUM(Sales Invoice.grand_total) where docstatus=1 and posting_date in range",
        "calculation_module": "bs.baron_servies.api.decision_center.registry:_compute_sales_total",
        "baseline_strategy": "previous_equivalent_period",
        "progress_strategy": "cumulative_growth",
        "is_negative_good": 0,
        "requires_snapshot": 0,
        "schema_version": "1.0.0",
    },
    "expenses_to_sales_pct": {
        "metric_label_ar": "نسبة المصاريف إلى المبيعات",
        "metric_label_en": "Expenses to Sales %",
        "category": "expenses",
        "unit": "percent",
        "system_available": 1,
        "enabled_for_plans": 1,
        "unavailable_reason": "",
        "formula_description": "total_expenses / sales_total * 100",
        "calculation_module": "bs.baron_servies.api.decision_center.registry:_compute_expenses_to_sales_pct",
        "baseline_strategy": "previous_equivalent_period",
        "progress_strategy": "level",
        "is_negative_good": 1,
        "requires_snapshot": 0,
        "schema_version": "1.0.0",
    },
    "total_expenses": {
        "metric_label_ar": "إجمالي المصاريف",
        "metric_label_en": "Total Expenses",
        "category": "expenses",
        "unit": "currency",
        "system_available": 1,
        "enabled_for_plans": 1,
        "unavailable_reason": "",
        "formula_description": "SUM(GL Entry.debit - credit) for mapped expense accounts",
        "calculation_module": "bs.baron_servies.api.decision_center.registry:_compute_total_expenses",
        "baseline_strategy": "previous_equivalent_period",
        "progress_strategy": "cumulative_ceiling",
        "is_negative_good": 1,
        "requires_snapshot": 0,
        "schema_version": "1.0.0",
    },
    "active_customers": {
        "metric_label_ar": "العملاء النشطين",
        "metric_label_en": "Active Customers",
        "category": "customers",
        "unit": "quantity",
        "system_available": 1,
        "enabled_for_plans": 1,
        "unavailable_reason": "",
        "formula_description": "COUNT(DISTINCT customer) from Sales Invoice in period",
        "calculation_module": "bs.baron_servies.api.decision_center.registry:_compute_active_customers",
        "baseline_strategy": "previous_equivalent_period",
        "progress_strategy": "level",
        "is_negative_good": 0,
        "requires_snapshot": 0,
        "schema_version": "1.0.0",
    },
    "average_invoice_value": {
        "metric_label_ar": "متوسط قيمة الفاتورة",
        "metric_label_en": "Average Invoice Value",
        "category": "sales",
        "unit": "currency",
        "system_available": 1,
        "enabled_for_plans": 1,
        "unavailable_reason": "",
        "formula_description": "sales_total / invoice_count",
        "calculation_module": "bs.baron_servies.api.decision_center.registry:_compute_average_invoice_value",
        "baseline_strategy": "previous_equivalent_period",
        "progress_strategy": "level",
        "is_negative_good": 0,
        "requires_snapshot": 0,
        "schema_version": "1.0.0",
    },
    "declining_customer_count": {
        "metric_label_ar": "عدد العملاء المت declining",
        "metric_label_en": "Declining Customer Count",
        "category": "customers",
        "unit": "quantity",
        "system_available": 1,
        "enabled_for_plans": 1,
        "unavailable_reason": "",
        "formula_description": "COUNT customers with sales decline > threshold vs previous equivalent period",
        "calculation_module": "bs.baron_servies.api.decision_center.registry:_compute_declining_customer_count",
        "baseline_strategy": "snapshot_at_plan_start",
        "progress_strategy": "level",
        "is_negative_good": 1,
        "requires_snapshot": 0,
        "schema_version": "1.0.0",
    },
    "dead_stock_value": {
        "metric_label_ar": "قيمة المخزون الراكد",
        "metric_label_en": "Dead Stock Value",
        "category": "inventory",
        "unit": "currency",
        "system_available": 1,
        "enabled_for_plans": 1,
        "unavailable_reason": "",
        "formula_description": "SUM(stock_value) for items with no sales in dead_stock_days",
        "calculation_module": "bs.baron_servies.api.decision_center.registry:_compute_dead_stock_value",
        "baseline_strategy": "snapshot_at_plan_start",
        "progress_strategy": "level",
        "is_negative_good": 1,
        "requires_snapshot": 1,
        "schema_version": "1.0.0",
    },
    "slow_moving_stock_value": {
        "metric_label_ar": "قيمة المخزون البطيء",
        "metric_label_en": "Slow Moving Stock Value",
        "category": "inventory",
        "unit": "currency",
        "system_available": 1,
        "enabled_for_plans": 1,
        "unavailable_reason": "",
        "formula_description": "SUM(stock_value) for items with sales velocity implying days_of_stock > slow_moving_days",
        "calculation_module": "bs.baron_servies.api.decision_center.registry:_compute_slow_moving_stock_value",
        "baseline_strategy": "snapshot_at_plan_start",
        "progress_strategy": "level",
        "is_negative_good": 1,
        "requires_snapshot": 1,
        "schema_version": "1.0.0",
    },
    "days_of_stock": {
        "metric_label_ar": "أيام المخزون",
        "metric_label_en": "Days of Stock",
        "category": "inventory",
        "unit": "days",
        "system_available": 1,
        "enabled_for_plans": 1,
        "unavailable_reason": "",
        "formula_description": "Average days of stock coverage from stock summary",
        "calculation_module": "bs.baron_servies.api.decision_center.registry:_compute_days_of_stock",
        "baseline_strategy": "average_previous_3_periods",
        "progress_strategy": "level",
        "is_negative_good": 0,
        "requires_snapshot": 0,
        "schema_version": "1.0.0",
    },
    "purchase_total": {
        "metric_label_ar": "إجمالي المشتريات",
        "metric_label_en": "Purchase Total",
        "category": "purchases",
        "unit": "currency",
        "system_available": 1,
        "enabled_for_plans": 1,
        "unavailable_reason": "",
        "formula_description": "SUM(Purchase Invoice.grand_total) where docstatus=1 and posting_date in range",
        "calculation_module": "bs.baron_servies.api.decision_center.registry:_compute_purchase_total",
        "baseline_strategy": "previous_equivalent_period",
        "progress_strategy": "cumulative_growth",
        "is_negative_good": 0,
        "requires_snapshot": 0,
        "schema_version": "1.0.0",
    },
    "gross_profit": {
        "metric_label_ar": "الربح الإجمالي",
        "metric_label_en": "Gross Profit",
        "category": "financial",
        "unit": "currency",
        "system_available": 0,
        "enabled_for_plans": 0,
        "unavailable_reason": "COGS not yet verified",
        "formula_description": "sales_total - cost_of_goods_sold (pending validation)",
        "calculation_module": "",
        "baseline_strategy": "manual_only",
        "progress_strategy": "level",
        "is_negative_good": 0,
        "requires_snapshot": 0,
        "schema_version": "1.0.0",
    },
    "net_profit": {
        "metric_label_ar": "صافي الربح",
        "metric_label_en": "Net Profit",
        "category": "financial",
        "unit": "currency",
        "system_available": 0,
        "enabled_for_plans": 0,
        "unavailable_reason": "accounting basis not yet verified",
        "formula_description": "gross_profit - operating_expenses - taxes (pending validation)",
        "calculation_module": "",
        "baseline_strategy": "manual_only",
        "progress_strategy": "level",
        "is_negative_good": 0,
        "requires_snapshot": 0,
        "schema_version": "1.0.0",
    },
}


def get_registry():
    return METRIC_REGISTRY.copy()


def get_metric_capability(metric_key):
    return METRIC_REGISTRY.get(metric_key)


def list_metrics_for_plans():
    return [
        {"metric_key": k, **v}
        for k, v in METRIC_REGISTRY.items()
        if v.get("system_available") and v.get("enabled_for_plans")
    ]


def _default_company():
    return frappe.defaults.get_user_default("Company") or frappe.db.get_value("Company", {}, "name")


# ── Individual metric calculators ──────────────────────────────────────────

def _compute_sales_total(company, from_date, to_date, **kwargs):
    _, _, prev_from, prev_to = get_period_dates(
        "custom", custom_from=from_date, custom_to=to_date
    )
    result = get_sales_metrics(company, from_date, to_date, prev_from, prev_to)
    return _ok(value=flt(result.get("total")), source="Sales Invoice")


def _previous_period(from_date, to_date):
    duration_days = max(1, (getdate(to_date) - getdate(from_date)).days + 1)
    prev_to = getdate(from_date) - timedelta(days=1)
    prev_from = prev_to - timedelta(days=duration_days - 1)
    return str(prev_from), str(prev_to)


def _compute_total_expenses(company, from_date, to_date, **kwargs):
    prev_from, prev_to = _previous_period(from_date, to_date)
    result = get_expense_metrics(company, from_date, to_date, prev_from, prev_to)
    return _ok(value=flt(result.get("total")), source="GL Entry")


def _compute_expenses_to_sales_pct(company, from_date, to_date, **kwargs):
    prev_from, prev_to = _previous_period(from_date, to_date)
    expense_result = get_expense_metrics(company, from_date, to_date, prev_from, prev_to)
    total_expenses = flt(expense_result.get("total"))

    sales_result = get_sales_metrics(company, from_date, to_date, prev_from, prev_to)
    sales_total = flt(sales_result.get("total"))

    value = (total_expenses / sales_total * 100.0) if sales_total else 0.0
    return _ok(value=value, source="GL Entry / Sales Invoice")


def _compute_active_customers(company, from_date, to_date, **kwargs):
    _, _, prev_from, prev_to = get_period_dates(
        "custom", custom_from=from_date, custom_to=to_date
    )
    result = get_sales_metrics(company, from_date, to_date, prev_from, prev_to)
    return _ok(value=cint(result.get("active_customers")), source="Sales Invoice")


def _compute_average_invoice_value(company, from_date, to_date, **kwargs):
    _, _, prev_from, prev_to = get_period_dates(
        "custom", custom_from=from_date, custom_to=to_date
    )
    result = get_sales_metrics(company, from_date, to_date, prev_from, prev_to)
    total = flt(result.get("total"))
    invoice_count = cint(result.get("invoice_count"))
    value = (total / invoice_count) if invoice_count else 0.0
    return _ok(value=value, source="Sales Invoice")


def _compute_declining_customer_count(company, from_date, to_date, **kwargs):
    _, _, prev_from, prev_to = get_period_dates(
        "custom", custom_from=from_date, custom_to=to_date
    )
    current = get_customer_sales(company, from_date, to_date)
    previous = get_customer_sales(company, prev_from, prev_to)

    prev_map = {c["customer"]: flt(c.get("net_total", 0)) for c in previous}
    threshold = flt(get_threshold("CUSTOMER_DROP_PERCENT"))

    declining = 0
    for c in current:
        prev = prev_map.get(c["customer"], 0)
        cur = flt(c.get("net_total", 0))
        if prev > 0 and cur < prev * (1 - threshold / 100.0):
            declining += 1
        elif prev == 0 and cur == 0:
            # exclude inactive entirely; only count existing customers who dropped
            pass

    return _ok(value=declining, source="Sales Invoice")


def _compute_dead_stock_value(company, from_date, to_date, **kwargs):
    stock = get_item_stock(company)
    dead_days = cint(get_threshold("DEAD_STOCK_DAYS"))
    items = get_item_sales(company, from_date, to_date)
    sold_item_codes = {i["item_code"] for i in items if flt(i.get("net_qty", 0)) > 0}

    total = 0.0
    for row in stock:
        item_code = row.get("item_code")
        if item_code in sold_item_codes:
            continue
        actual_qty = flt(row.get("actual_qty"))
        stock_value = flt(row.get("stock_value"))
        # Dead stock is only meaningful for items that currently exist in stock
        # with positive valuation. Negative values come from returns/adjustments
        # and should not be counted as "dead inventory".
        if actual_qty <= 0 or stock_value <= 0:
            continue
        total += stock_value

    return _ok(value=total, source="Bin / Stock Ledger", is_snapshot=True)


def _compute_slow_moving_stock_value(company, from_date, to_date, **kwargs):
    stock = get_item_stock(company)
    slow_days = cint(get_threshold("SLOW_MOVING_DAYS"))
    items = get_item_sales(company, from_date, to_date)
    item_sales = {i["item_code"]: i for i in items}

    total = 0.0
    for row in stock:
        item_code = row.get("item_code")
        sales = item_sales.get(item_code, {})
        qty = flt(sales.get("net_qty", 0))
        days = cint(sales.get("days", 1))
        avg_daily = qty / days if days else 0
        actual_qty = flt(row.get("actual_qty", 0))
        stock_value = flt(row.get("stock_value", 0))
        days_of_stock = (actual_qty / avg_daily) if avg_daily > 0 else 9999
        if actual_qty > 0 and stock_value > 0 and days_of_stock > slow_days:
            total += stock_value

    return _ok(value=total, source="Bin / Stock Ledger", is_snapshot=True)


def _compute_days_of_stock(company, from_date, to_date, **kwargs):
    stock = get_item_stock(company)
    items = get_item_sales(company, from_date, to_date)
    item_sales = {i["item_code"]: i for i in items}

    values = []
    for row in stock:
        sales = item_sales.get(row.get("item_code"), {})
        qty = flt(sales.get("net_qty", 0))
        days = cint(sales.get("days", 1))
        avg_daily = qty / days if days else 0
        actual_qty = flt(row.get("actual_qty", 0))
        if actual_qty > 0 and avg_daily > 0:
            values.append(actual_qty / avg_daily)

    value = sum(values) / len(values) if values else 0.0
    return _ok(value=value, source="Bin / Stock Ledger")


def _compute_purchase_total(company, from_date, to_date, **kwargs):
    _, _, prev_from, prev_to = get_period_dates(
        "custom", custom_from=from_date, custom_to=to_date
    )
    result = get_purchase_metrics(company, from_date, to_date, prev_from, prev_to)
    return _ok(value=flt(result.get("total")), source="Purchase Invoice")


# ── Dispatch ───────────────────────────────────────────────────────────────

_COMPUTE_FUNCS = {
    "sales_total": _compute_sales_total,
    "total_expenses": _compute_total_expenses,
    "expenses_to_sales_pct": _compute_expenses_to_sales_pct,
    "active_customers": _compute_active_customers,
    "average_invoice_value": _compute_average_invoice_value,
    "declining_customer_count": _compute_declining_customer_count,
    "dead_stock_value": _compute_dead_stock_value,
    "slow_moving_stock_value": _compute_slow_moving_stock_value,
    "days_of_stock": _compute_days_of_stock,
    "purchase_total": _compute_purchase_total,
}


def compute_metric(metric_key, from_date, to_date, company=None):
    meta = get_metric_capability(metric_key)
    if not meta:
        raise ValueError("Unknown metric key: {}".format(metric_key))
    if not meta.get("system_available"):
        raise ValueError("Metric {} is not system-available: {}".format(metric_key, meta.get("unavailable_reason")))

    company = company or _default_company()
    calc_path = meta.get("calculation_module", "")
    func = _COMPUTE_FUNCS.get(metric_key)
    if not func:
        raise ValueError("No calculator registered for metric {}".format(metric_key))

    result = func(company=company, from_date=getdate(from_date), to_date=getdate(to_date))
    result.update({
        "metric_key": metric_key,
        "metric_label_ar": meta.get("metric_label_ar"),
        "metric_label_en": meta.get("metric_label_en"),
        "category": meta.get("category"),
        "unit": meta.get("unit"),
        "formula_description": meta.get("formula_description"),
        "progress_strategy": meta.get("progress_strategy"),
        "is_negative_good": meta.get("is_negative_good"),
        "period": {"from": str(from_date), "to": str(to_date)},
    })
    return result


def _ok(value, source, is_snapshot=False):
    return {
        "value": flt(value),
        "source": source,
        "is_snapshot": is_snapshot,
    }


# ── Baseline helpers ─────────────────────────────────────────────────────────

def compute_baseline(metric_key, strategy, reference_date, plan_start_date=None, company=None):
    """Compute baseline value for a metric using its registered strategy.

    Returns a dict with value, period, and source notes.
    """
    company = company or _default_company()
    reference = getdate(reference_date)

    if strategy == "manual_only":
        return {"value": None, "from_date": None, "to_date": None, "source": "manual_only"}

    if strategy == "snapshot_at_plan_start":
        if not plan_start_date:
            raise ValueError("plan_start_date required for snapshot_at_plan_start")
        from_date = to_date = getdate(plan_start_date)
        result = compute_metric(metric_key, from_date, to_date, company=company)
        return {
            "value": result["value"],
            "from_date": str(from_date),
            "to_date": str(to_date),
            "source": "snapshot_at_plan_start",
        }

    if strategy == "previous_equivalent_period":
        plan_start = getdate(plan_start_date) if plan_start_date else reference
        plan_end = reference
        duration_days = max(1, (plan_end - plan_start).days + 1)
        prev_end = plan_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=duration_days - 1)
        result = compute_metric(metric_key, prev_start, prev_end, company=company)
        return {
            "value": result["value"],
            "from_date": str(prev_start),
            "to_date": str(prev_end),
            "source": "previous_equivalent_period",
        }

    if strategy == "average_previous_3_periods":
        plan_start = getdate(plan_start_date) if plan_start_date else reference
        plan_end = reference
        duration_days = max(1, (plan_end - plan_start).days + 1)
        values = []
        periods = []
        end = plan_start - timedelta(days=1)
        for _ in range(3):
            start = end - timedelta(days=duration_days - 1)
            try:
                res = compute_metric(metric_key, start, end, company=company)
                values.append(flt(res["value"]))
                periods.append({"from": str(start), "to": str(end)})
            except Exception:
                pass
            end = start - timedelta(days=1)
        value = (sum(values) / len(values)) if values else 0.0
        return {
            "value": value,
            "periods": periods,
            "source": "average_previous_3_periods",
        }

    raise ValueError("Unknown baseline strategy: {}".format(strategy))


# ── Progress / health / target-achievement helpers ──────────────────────────

def level_progress(current, baseline, target, direction):
    if target == baseline:
        return 100.0 if current == target else 0.0
    if direction == "increase":
        progress = (current - baseline) / (target - baseline)
    else:
        progress = (baseline - current) / (baseline - target)
    return max(0.0, min(100.0, progress * 100.0))


def cumulative_growth_measures(current, target, time_progress_pct):
    expected_to_date = target * (time_progress_pct / 100.0) if time_progress_pct is not None else target
    final_target_completion_pct = (current / target * 100.0) if target else 0.0
    pace_attainment_pct = (current / expected_to_date * 100.0) if expected_to_date else 0.0
    return {
        "final_target_completion_pct": flt(final_target_completion_pct),
        "expected_to_date": flt(expected_to_date),
        "pace_attainment_pct": flt(pace_attainment_pct),
    }


def cumulative_ceiling_measures(current, cap, time_progress_pct):
    expected_consumption_to_date = cap * (time_progress_pct / 100.0) if time_progress_pct is not None else cap
    cap_utilization_pct = (current / cap * 100.0) if cap else 0.0
    remaining_amount = cap - current
    consumption_pace_pct = (current / expected_consumption_to_date * 100.0) if expected_consumption_to_date else 0.0
    return {
        "cap_utilization_pct": flt(cap_utilization_pct),
        "remaining_amount": flt(remaining_amount),
        "expected_consumption_to_date": flt(expected_consumption_to_date),
        "consumption_pace_pct": flt(consumption_pace_pct),
    }


def plan_health(outcome_progress_or_pace, time_progress_pct, tolerance_pct, strategy="level"):
    tolerance = flt(tolerance_pct) or 10.0
    if strategy == "cumulative_ceiling":
        # consumption_pace_pct vs 100: lower is better (under pace)
        gap = 100.0 - outcome_progress_or_pace
    else:
        gap = outcome_progress_or_pace - time_progress_pct
    if gap >= -tolerance:
        return "on_track"
    if gap >= -(tolerance * 2):
        return "needs_attention"
    return "behind"


def target_achieved(current, target, direction, progress_strategy, plan_status):
    """Return True if the target condition is currently met.

    For cumulative_ceiling the target is only evaluated at plan completion;
    during the plan we report health/pace only.
    """
    if progress_strategy == "cumulative_ceiling":
        return plan_status == "Completed" and current <= target
    if progress_strategy == "cumulative_growth":
        return current >= target
    # level
    if direction == "increase":
        return current >= target
    return current <= target


def time_progress(start_date, end_date, as_of_date=None):
    start = getdate(start_date)
    end = getdate(end_date)
    as_of = getdate(as_of_date or nowdate())
    total_days = max(1, (end - start).days + 1)
    elapsed_days = max(0, (as_of - start).days + 1)
    return min(100.0, (elapsed_days / total_days) * 100.0)
