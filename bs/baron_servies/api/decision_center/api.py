# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Public API layer for the Decision Center.

All endpoints are ``@frappe.whitelist()`` and accept period selection.
Heavy computation is delegated to the Metrics / Rules / Playbook engines.
"""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt, cint

from .periods import get_period_dates
from .metrics import (
    get_sales_metrics,
    get_purchase_metrics,
    get_stock_summary,
    get_item_stock,
    get_item_sales,
    get_item_purchases,
    get_customer_sales,
    get_top_items_by_sales,
    get_top_items_by_purchases,
    get_top_suppliers,
    get_top_customers,
)
from .expenses import (
    get_expense_metrics,
    get_expense_trend,
    get_expense_categories,
)
from .rules import evaluate_all_rules, get_rule, RULES
from .plan_engine import _compute_kpi_measures
from . import config as cfg


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _resolve_period(period, from_date=None, to_date=None):
    """Parse period args and return (from_date, to_date, prev_from, prev_to)."""
    period = period or "last_30_days"
    return get_period_dates(period, custom_from=from_date, custom_to=to_date)


def _get_currency(company):
    if company:
        return frappe.db.get_value("Company", company, "default_currency") or ""
    return frappe.db.get_single_value("Global Defaults", "default_currency") or ""


# ═══════════════════════════════════════════════════════════════════════════
# Summary  (Overview tab)
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_decision_center_summary(company=None, period=None, from_date=None, to_date=None):
    """Return overview metrics + top decisions."""
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        frappe.throw(_("Company is required"))

    fd, td, pf, pt = _resolve_period(period, from_date, to_date)

    sales = get_sales_metrics(company, fd, td, pf, pt)
    purchases = get_purchase_metrics(company, fd, td, pf, pt)
    stock = get_stock_summary(company)
    expenses = get_expense_metrics(company, fd, td, pf, pt)
    currency = _get_currency(company)

    expense_to_sales_pct = None
    if flt(sales.get("total")) > 0:
        expense_to_sales_pct = round((flt(expenses.get("total")) / flt(sales.get("total"))) * 100, 1)

    # Generate all decisions and pick top N
    decisions = evaluate_all_rules(company, fd, td, pf, pt)
    decisions.sort(key=lambda d: d.get("score", 0), reverse=True)
    top_decisions = _strip_extra(decisions[:8])

    current_plan = _get_current_plan_summary()
    top_decisions = _link_decisions_to_current_plan(top_decisions, current_plan)

    return {
        "metrics": {
            "sales_total": sales["total"],
            "sales_prev": sales["prev_total"],
            "sales_growth_pct": sales["growth_pct"],
            "sales_count": sales["count"],
            "sales_avg_invoice": sales["avg_invoice"],
            "purchase_total": purchases["total"],
            "purchase_prev": purchases["prev_total"],
            "purchase_growth_pct": purchases["growth_pct"],
            "purchase_count": purchases["count"],
            "stock_value": stock["total_value"],
            "stock_item_count": stock["item_count"],
            "active_customers": sales["active_customers"],
            "prev_active_customers": sales["prev_active_customers"],
            "active_customers_change_pct": sales.get("active_customers_change_pct"),
            "total_expenses": expenses.get("total"),
            "expenses_prev": expenses.get("previous_total"),
            "expenses_growth_pct": expenses.get("growth_pct"),
            "expenses_to_sales_pct": expense_to_sales_pct,
        },
        "top_decisions": top_decisions,
        "total_decisions": len(decisions),
        "current_plan": current_plan,
        "currency": currency,
        "period": {"from_date": str(fd), "to_date": str(td),
                    "prev_from": str(pf), "prev_to": str(pt)},
    }


def _get_current_plan_summary():
    active = frappe.get_all(
        "Decision Center Plan",
        filters={"status": "Active"},
        fields=["name", "plan_name", "start_date", "end_date", "target_achieved"],
        limit_page_length=1,
    )
    if not active:
        return None
    plan = active[0]
    plan_doc = frappe.get_doc("Decision Center Plan", plan.name)
    primary = next((k for k in plan_doc.kpis if k.is_primary), None)

    progress_value = None
    if primary:
        measures = _compute_kpi_measures(primary, plan_doc, None)
        strategy = primary.progress_strategy or "level"
        if strategy == "cumulative_ceiling":
            progress_value = flt(measures.get("consumption_pace_pct"))
        else:
            progress_value = flt(measures.get("pace_attainment_pct"))
    return {
        "name": plan.name,
        "plan_name": plan.plan_name,
        "start_date": str(plan.start_date),
        "end_date": str(plan.end_date),
        "target_achieved": bool(plan.target_achieved),
        "primary_metric": primary.metric_key if primary else None,
        "primary_progress": progress_value,
    }


def _link_decisions_to_current_plan(decisions, current_plan):
    if not current_plan:
        return decisions
    active_categories = set()
    active_rule_ids = set()
    active_metrics = set()

    plan_doc = frappe.get_doc("Decision Center Plan", current_plan["name"])
    for kpi in plan_doc.kpis:
        meta = None
        try:
            from .registry import get_metric_capability
            meta = get_metric_capability(kpi.metric_key)
        except Exception:
            pass
        if meta:
            active_categories.add(meta.get("category"))
        active_metrics.add(kpi.metric_key)
    for action in plan_doc.actions:
        if action.related_rule_id:
            active_rule_ids.add(action.related_rule_id)
        if action.related_expense_category:
            active_metrics.add(action.related_expense_category)
        if action.related_metric_key:
            active_metrics.add(action.related_metric_key)

    for d in decisions:
        related = False
        if d.get("category") in active_categories:
            related = True
        if d.get("rule_id") in active_rule_ids:
            related = True
        # Heuristic: decision evidence mentions an expense category or item linked to plan actions
        for ev in d.get("evidence", []):
            label = ev.get("label", "")
            if label in active_metrics:
                related = True
        d["related_to_current_plan"] = related
    return decisions


# ═══════════════════════════════════════════════════════════════════════════
# Decisions list
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_decisions(company=None, period=None, from_date=None, to_date=None,
                  category=None, severity=None, sort_by=None):
    """Return all decisions with optional filters."""
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        frappe.throw(_("Company is required"))

    fd, td, pf, pt = _resolve_period(period, from_date, to_date)
    decisions = evaluate_all_rules(company, fd, td, pf, pt)

    # Filter
    if category:
        decisions = [d for d in decisions if d.get("category") == category]
    if severity:
        decisions = [d for d in decisions if d.get("priority") == severity]

    # Sort
    if sort_by == "impact":
        decisions.sort(key=lambda d: flt(d.get("impact_value", 0)), reverse=True)
    elif sort_by == "newest":
        decisions.sort(key=lambda d: d.get("id", ""), reverse=True)
    else:
        decisions.sort(key=lambda d: d.get("score", 0), reverse=True)

    return {
        "decisions": _strip_extra(decisions),
        "total": len(decisions),
        "currency": _get_currency(company),
        "period": {"from_date": str(fd), "to_date": str(td)},
    }


# ═══════════════════════════════════════════════════════════════════════════
# Decision detail
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_decision_detail(decision_id, company=None, period=None,
                        from_date=None, to_date=None):
    """Return a single decision by its deterministic ID.

    Recomputes all decisions for the period and finds the matching one.
    """
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        frappe.throw(_("Company is required"))

    fd, td, pf, pt = _resolve_period(period, from_date, to_date)
    decisions = evaluate_all_rules(company, fd, td, pf, pt)

    for d in decisions:
        if d.get("id") == decision_id:
            rule = get_rule(d.get("rule_id"))
            d["rule_info"] = {
                "id": rule["id"],
                "category": rule["category"],
                "severity": rule["severity"],
            } if rule else None
            return {
                "decision": d,
                "currency": _get_currency(company),
                "period": {"from_date": str(fd), "to_date": str(td)},
            }

    frappe.throw(_("Decision not found"), frappe.DoesNotExistError)


# ═══════════════════════════════════════════════════════════════════════════
# Sales analysis tab
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_sales_analysis(company=None, period=None, from_date=None, to_date=None):
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        frappe.throw(_("Company is required"))

    fd, td, pf, pt = _resolve_period(period, from_date, to_date)
    sales = get_sales_metrics(company, fd, td, pf, pt)
    top_items = get_top_items_by_sales(company, fd, td, limit=10)
    top_customers_list = get_top_customers(company, fd, td, limit=10)

    # Item-level comparison for growth/decline
    current_items = {r["item_code"]: r for r in get_item_sales(company, fd, td)}
    previous_items = {r["item_code"]: r for r in get_item_sales(company, pf, pt)}

    growing = []
    declining = []
    from . import config as cfg
    for item_code, curr in current_items.items():
        prev = previous_items.get(item_code, {})
        prev_qty = flt(prev.get("net_qty", 0))
        curr_qty = flt(curr.get("net_qty", 0))
        if prev_qty >= cfg.get_threshold('MIN_SALES_BASELINE') and curr_qty > 0:
            pct = ((curr_qty - prev_qty) / prev_qty) * 100
            entry = {
                "item_code": item_code,
                "item_name": curr.get("item_name", item_code),
                "prev_qty": prev_qty,
                "current_qty": curr_qty,
                "change_pct": round(pct, 1),
                "current_amount": flt(curr.get("net_amount", 0)),
            }
            if pct >= cfg.get_threshold('SALES_GROWTH_PERCENT'):
                growing.append(entry)
            elif pct <= -cfg.get_threshold('SALES_DROP_PERCENT'):
                declining.append(entry)

    growing.sort(key=lambda x: x["change_pct"], reverse=True)
    declining.sort(key=lambda x: x["change_pct"])

    return {
        "metrics": sales,
        "top_items": top_items[:10],
        "top_customers": top_customers_list[:10],
        "growing_items": growing[:10],
        "declining_items": declining[:10],
        "currency": _get_currency(company),
        "period": {"from_date": str(fd), "to_date": str(td)},
    }


# ═══════════════════════════════════════════════════════════════════════════
# Purchases analysis tab
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_purchase_analysis(company=None, period=None, from_date=None, to_date=None):
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        frappe.throw(_("Company is required"))

    fd, td, pf, pt = _resolve_period(period, from_date, to_date)
    purchases = get_purchase_metrics(company, fd, td, pf, pt)
    top_items = get_top_items_by_purchases(company, fd, td, limit=10)
    top_suppliers_list = get_top_suppliers(company, fd, td, limit=10)

    # Price increases
    current_pi = {r["item_code"]: r for r in get_item_purchases(company, fd, td)}
    previous_pi = {r["item_code"]: r for r in get_item_purchases(company, pf, pt)}

    price_increases = []
    from . import config as cfg
    for item_code, curr in current_pi.items():
        prev = previous_pi.get(item_code)
        if not prev:
            continue
        prev_rate = flt(prev.get("avg_rate"))
        curr_rate = flt(curr.get("avg_rate"))
        if prev_rate > 0 and curr_rate > 0:
            pct = ((curr_rate - prev_rate) / prev_rate) * 100
            if pct >= cfg.get_threshold('PURCHASE_PRICE_INCREASE_PERCENT'):
                price_increases.append({
                    "item_code": item_code,
                    "item_name": curr.get("item_name", item_code),
                    "prev_rate": round(prev_rate, 2),
                    "current_rate": round(curr_rate, 2),
                    "increase_pct": round(pct, 1),
                })

    price_increases.sort(key=lambda x: x["increase_pct"], reverse=True)

    return {
        "metrics": purchases,
        "top_items": top_items[:10],
        "top_suppliers": top_suppliers_list[:10],
        "price_increases": price_increases[:10],
        "currency": _get_currency(company),
        "period": {"from_date": str(fd), "to_date": str(td)},
    }


# ═══════════════════════════════════════════════════════════════════════════
# Inventory analysis tab
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_inventory_analysis(company=None, period=None, from_date=None, to_date=None):
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        frappe.throw(_("Company is required"))

    fd, td, pf, pt = _resolve_period(period, from_date, to_date)
    stock = get_stock_summary(company)
    items = get_item_stock(company)

    # Enrich with sales velocity (last 90 days from today)
    from frappe.utils import nowdate, getdate
    import datetime
    today = getdate(nowdate())
    lookback = today - datetime.timedelta(days=90)
    sales_map = {r["item_code"]: r for r in get_item_sales(company, lookback, today)}

    for item in items:
        sale = sales_map.get(item["item_code"])
        aq = flt(item.get("actual_qty"))
        if sale and flt(sale.get("avg_daily_qty")) > 0:
            item["avg_daily_sales"] = round(flt(sale["avg_daily_qty"]), 2)
            item["days_of_stock"] = round(aq / sale["avg_daily_qty"], 1) if aq > 0 else 0
        else:
            item["avg_daily_sales"] = 0
            item["days_of_stock"] = None  # Cannot compute

    # Categorize
    from . import config as cfg
    dead = [i for i in items if flt(i["actual_qty"]) > 0 and i["days_of_stock"] is None]
    slow = [i for i in items if flt(i["actual_qty"]) > 0 and i.get("days_of_stock") is not None and i["days_of_stock"] > cfg.get_threshold('SLOW_MOVING_DAYS')]
    low_stock = [i for i in items if flt(i["actual_qty"]) > 0 and i.get("days_of_stock") is not None and i["days_of_stock"] < cfg.get_threshold('WARNING_STOCK_DAYS') and i["avg_daily_sales"] > 0]

    return {
        "summary": stock,
        "items": items[:200],
        "dead_stock_count": len(dead),
        "dead_stock_value": sum(flt(i.get("stock_value")) for i in dead),
        "slow_moving_count": len(slow),
        "slow_moving_value": sum(flt(i.get("stock_value")) for i in slow),
        "low_stock_count": len(low_stock),
        "currency": _get_currency(company),
        "snapshot_label": "المخزون الحالي",
    }


# ═══════════════════════════════════════════════════════════════════════════
# Customer analysis tab
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_customer_analysis(company=None, period=None, from_date=None, to_date=None):
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        frappe.throw(_("Company is required"))

    fd, td, pf, pt = _resolve_period(period, from_date, to_date)
    top = get_top_customers(company, fd, td, limit=10)

    current = {r["customer"]: r for r in get_customer_sales(company, fd, td)}
    previous = {r["customer"]: r for r in get_customer_sales(company, pf, pt)}

    from . import config as cfg
    growing = []
    declining = []
    for customer, curr in current.items():
        prev = previous.get(customer, {})
        prev_total = flt(prev.get("net_total", 0))
        curr_total = flt(curr.get("net_total", 0))
        if prev_total > 0 and int(prev.get("invoice_count", 0)) >= cfg.get_threshold('MIN_CUSTOMER_INVOICES'):
            pct = ((curr_total - prev_total) / prev_total) * 100
            entry = {
                "customer": customer,
                "customer_name": curr.get("customer_name", customer),
                "prev_total": prev_total,
                "current_total": curr_total,
                "change_pct": round(pct, 1),
            }
            if pct >= cfg.get_threshold('SALES_GROWTH_PERCENT'):
                growing.append(entry)
            elif pct <= -cfg.get_threshold('CUSTOMER_DROP_PERCENT'):
                declining.append(entry)

    growing.sort(key=lambda x: x["change_pct"], reverse=True)
    declining.sort(key=lambda x: x["change_pct"])

    return {
        "top_customers": top[:10],
        "growing_customers": growing[:10],
        "declining_customers": declining[:10],
        "active_count": len(current),
        "currency": _get_currency(company),
        "period": {"from_date": str(fd), "to_date": str(td)},
    }


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _strip_extra(decisions):
    """Remove bulky ``extra`` field for list views (keep for detail)."""
    result = []
    for d in decisions:
        out = {k: v for k, v in d.items() if k != "extra"}
        result.append(out)
    return result


# ═══════════════════════════════════════════════════════════════════════════
# Expense analysis tab
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_expense_analysis(company=None, period=None, from_date=None, to_date=None):
    """Return expense metrics, category breakdown, account breakdown, and trend."""
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        frappe.throw(_("Company is required"))

    fd, td, pf, pt = _resolve_period(period, from_date, to_date)
    expenses = get_expense_metrics(company, fd, td, pf, pt)

    # Sort categories and accounts by current amount
    categories = sorted(expenses.get("categories", []), key=lambda x: flt(x.get("current_amount")), reverse=True)
    accounts = sorted(expenses.get("accounts", []), key=lambda x: flt(x.get("current_amount")), reverse=True)

    # Trend over current range, split monthly
    enabled_accounts = [a["account"] for a in expenses.get("accounts", []) if a.get("account")]
    trend = get_expense_trend(company, enabled_accounts, fd, td, granularity="monthly")

    return {
        "metrics": {
            "total": expenses.get("total"),
            "previous_total": expenses.get("previous_total"),
            "growth_pct": expenses.get("growth_pct"),
        },
        "categories": categories[:50],
        "accounts": accounts[:50],
        "trend": trend,
        "currency": _get_currency(company),
        "period": {"from_date": str(fd), "to_date": str(td),
                   "prev_from": str(pf), "prev_to": str(pt)},
    }


# ═══════════════════════════════════════════════════════════════════════════
# Settings APIs
# ═══════════════════════════════════════════════════════════════════════════

_EDITABLE_FIELDS = {
    "slow_moving_days": {"type": "int", "min": 1},
    "dead_stock_days": {"type": "int", "min": 1},
    "low_stock_days": {"type": "int", "min": 1},
    "warning_stock_days": {"type": "int", "min": 1},
    "sales_drop_percent": {"type": "percent", "min": 0, "max": 100},
    "sales_growth_percent": {"type": "percent", "min": 0, "max": 100},
    "min_sales_baseline": {"type": "int", "min": 0},
    "purchase_price_increase_percent": {"type": "percent", "min": 0, "max": 100},
    "overstock_purchase_ratio": {"type": "float", "min": 0},
    "customer_drop_percent": {"type": "percent", "min": 0, "max": 100},
    "customer_inactive_multiplier": {"type": "float", "min": 0},
    "min_customer_invoices": {"type": "int", "min": 0},
    "expense_vs_sales_threshold": {"type": "percent", "min": 0, "max": 100},
    "expense_increase_threshold": {"type": "percent", "min": 0, "max": 100},
    "expense_anomaly_threshold": {"type": "percent", "min": 0, "max": 100},
    "plan_health_tolerance_pct": {"type": "percent", "min": 0, "max": 100},
    "auto_lock_snapshots_days": {"type": "int", "min": 0},
    "priority_urgent": {"type": "int", "min": 0, "max": 100},
    "priority_important": {"type": "int", "min": 0, "max": 100},
    "priority_review": {"type": "int", "min": 0, "max": 100},
}


def _validate_settings(settings_data):
    """Validate incoming settings against the server-side whitelist."""
    for key, value in settings_data.items():
        if key in ("rule_settings", "default_plan_priority", "monthly_snapshot_enabled", "name"):
            continue
        if key not in _EDITABLE_FIELDS:
            frappe.throw(_("Field '{0}' is not editable").format(key), frappe.ValidationError)

        meta = _EDITABLE_FIELDS[key]
        try:
            if meta["type"] == "int":
                num = cint(value)
            elif meta["type"] == "float":
                num = flt(value)
            else:
                num = flt(value)
        except Exception:
            frappe.throw(_("Field '{0}' must be numeric").format(key), frappe.ValidationError)

        if "min" in meta and num < meta["min"]:
            frappe.throw(_("Field '{0}' must be at least {1}").format(key, meta["min"]), frappe.ValidationError)
        if "max" in meta and num > meta["max"]:
            frappe.throw(_("Field '{0}' must not exceed {1}").format(key, meta["max"]), frappe.ValidationError)

    low = settings_data.get("low_stock_days")
    warning = settings_data.get("warning_stock_days")
    if low is not None and warning is not None and cint(low) >= cint(warning):
        frappe.throw(
            _("حد النقص الحرج ({0}) يجب أن يكون أقل من حد التحذير ({1})").format(cint(low), cint(warning)),
            frappe.ValidationError,
        )

    p_urgent = settings_data.get("priority_urgent")
    p_important = settings_data.get("priority_important")
    p_review = settings_data.get("priority_review")
    if p_urgent is not None and p_important is not None and cint(p_urgent) <= cint(p_important):
        frappe.throw(_("الحد العاجل يجب أن يكون أكبر من الحد المهم"), frappe.ValidationError)
    if p_important is not None and p_review is not None and cint(p_important) <= cint(p_review):
        frappe.throw(_("الحد المهم يجب أن يكون أكبر من حد المراجعة"), frappe.ValidationError)


def _apply_settings(doc, settings_data):
    """Apply only whitelisted settings fields to the document."""
    for key, value in settings_data.items():
        if key == "rule_settings":
            doc.set("rule_settings", [])
            for row in (value or []):
                doc.append("rule_settings", {
                    "rule_id": row.get("rule_id"),
                    "enabled": cint(row.get("enabled", 1)),
                })
            continue
        if key == "name":
            continue
        if key in ("default_plan_priority", "monthly_snapshot_enabled"):
            doc.set(key, value)
            continue
        if key in _EDITABLE_FIELDS:
            doc.set(key, value)


@frappe.whitelist()
def get_decision_center_settings():
    """Return Decision Center settings and expense categories for the settings UI."""
    if frappe.session.user == "Guest":
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    doc = cfg.get_decision_center_settings()
    saved_rule_map = {r.rule_id: bool(r.enabled) for r in doc.rule_settings} if doc else {}
    rule_settings = []
    for rule in RULES:
        rule_settings.append({
            "rule_id": rule["id"],
            "category": rule["category"],
            "title": rule["title_template"],
            "description": rule.get("description", ""),
            "enabled": saved_rule_map.get(rule["id"], rule.get("enabled", True)),
        })

    settings = {
        "slow_moving_days": cfg.get_threshold("SLOW_MOVING_DAYS"),
        "dead_stock_days": cfg.get_threshold("DEAD_STOCK_DAYS"),
        "low_stock_days": cfg.get_threshold("LOW_STOCK_DAYS"),
        "warning_stock_days": cfg.get_threshold("WARNING_STOCK_DAYS"),
        "sales_drop_percent": cfg.get_threshold("SALES_DROP_PERCENT"),
        "sales_growth_percent": cfg.get_threshold("SALES_GROWTH_PERCENT"),
        "min_sales_baseline": cfg.get_threshold("MIN_SALES_BASELINE"),
        "purchase_price_increase_percent": cfg.get_threshold("PURCHASE_PRICE_INCREASE_PERCENT"),
        "overstock_purchase_ratio": cfg.get_threshold("OVERSTOCK_PURCHASE_RATIO"),
        "customer_drop_percent": cfg.get_threshold("CUSTOMER_DROP_PERCENT"),
        "customer_inactive_multiplier": cfg.get_threshold("CUSTOMER_INACTIVE_MULTIPLIER"),
        "min_customer_invoices": cfg.get_threshold("MIN_CUSTOMER_INVOICES"),
        "expense_vs_sales_threshold": cfg.get_threshold("EXPENSE_VS_SALES_THRESHOLD"),
        "expense_increase_threshold": cfg.get_threshold("EXPENSE_INCREASE_THRESHOLD"),
        "expense_anomaly_threshold": cfg.get_threshold("EXPENSE_ANOMALY_THRESHOLD"),
        "plan_health_tolerance_pct": cfg.get_threshold("PLAN_HEALTH_TOLERANCE_PCT"),
        "priority_urgent": cfg.get_threshold("PRIORITY_URGENT"),
        "priority_important": cfg.get_threshold("PRIORITY_IMPORTANT"),
        "priority_review": cfg.get_threshold("PRIORITY_REVIEW"),
        "default_plan_priority": getattr(doc, "default_plan_priority", "Medium") if doc else "Medium",
        "auto_lock_snapshots_days": getattr(doc, "auto_lock_snapshots_days", 7) if doc else 7,
        "monthly_snapshot_enabled": bool(getattr(doc, "monthly_snapshot_enabled", 1)) if doc else True,
        "rule_settings": rule_settings,
    }

    categories = get_expense_categories(enabled_only=False)
    return {
        "settings": settings,
        "categories": categories,
    }


@frappe.whitelist()
def update_decision_center_settings(payload):
    """Save Decision Center settings. Restricted to Administrator."""
    if frappe.session.user != "Administrator":
        frappe.throw(_("Only Administrator can update Decision Center settings"), frappe.PermissionError)

    import json

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            frappe.throw(_("Invalid JSON payload"))

    if not isinstance(payload, dict):
        frappe.throw(_("Payload must be an object"))

    settings_data = payload.get("settings") or {}
    categories_data = payload.get("categories") or []

    _validate_settings(settings_data)

    # Save single settings doc
    doc = frappe.get_doc("Decision Center Settings", "Decision Center Settings")
    _apply_settings(doc, settings_data)
    doc.save(ignore_permissions=True)

    # Save categories (accounts are nested in each category dict)
    for cat in categories_data:
        name = cat.get("name")
        if name and frappe.db.exists("Decision Center Expense Category", name):
            cat_doc = frappe.get_doc("Decision Center Expense Category", name)
        else:
            cat_doc = frappe.new_doc("Decision Center Expense Category")
            cat_doc.category_name = cat.get("category_name")

        cat_doc.description = cat.get("description", "")
        cat_doc.enabled = cint(cat.get("enabled", 1))
        cat_doc.target_percent_of_sales = flt(cat.get("target_percent_of_sales"))
        cat_doc.max_percent_of_sales = flt(cat.get("max_percent_of_sales"))

        cat_doc.set("accounts", [])
        for acc in (cat.get("accounts") or []):
            cat_doc.append("accounts", {
                "account": acc.get("account"),
                "enabled": cint(acc.get("enabled", 1)),
                "description": acc.get("description", ""),
            })

        cat_doc.save(ignore_permissions=True)

    return {"success": True}


@frappe.whitelist()
def delete_expense_category(category_name):
    """Delete an expense category. Restricted to Administrator."""
    if frappe.session.user != "Administrator":
        frappe.throw(_("Only Administrator can delete expense categories"), frappe.PermissionError)

    if not category_name or not frappe.db.exists("Decision Center Expense Category", category_name):
        frappe.throw(_("Category not found"), frappe.DoesNotExistError)

    frappe.delete_doc("Decision Center Expense Category", category_name, ignore_permissions=True)
    return {"success": True}
