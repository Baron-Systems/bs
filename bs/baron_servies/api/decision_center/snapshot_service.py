# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Monthly snapshot service for Decision Center.

Guarantees historical integrity by persisting every value shown in monthly reports.
Snapshots are immutable after the configured grace period; regeneration is audited
via the Decision Center Snapshot Revision DocType.
"""

from __future__ import unicode_literals

import hashlib
import json
from calendar import monthrange
from datetime import date, timedelta

import frappe
from frappe.utils import cint, flt, getdate, now, nowdate

from .config import get_decision_center_settings, get_threshold
from .expenses import get_expense_categories, get_expense_metrics
from .metrics import get_item_sales, get_sales_metrics
from .periods import get_period_dates
from .rules import evaluate_all_rules
from .registry import (
    ENGINE_VERSION,
    METRIC_REGISTRY,
    compute_baseline,
    compute_metric,
    cumulative_ceiling_measures,
    cumulative_growth_measures,
    get_metric_capability,
    level_progress,
    plan_health,
    target_achieved,
    time_progress,
)

SNAPSHOT_ENGINE_VERSION = "1.0.0"


# ── Public API ──────────────────────────────────────────────────────────────

def get_or_generate_snapshot(month, company=None, reason=None, force=False, called_by_scheduler=False):
    """Return existing snapshot or generate a new one.

    If the snapshot is locked, generation is blocked unless force=True and the
    caller has permission (handled in regenerate_snapshot).
    """
    company = company or _default_company()
    if frappe.db.exists("Decision Center Monthly Snapshot", month):
        doc = frappe.get_doc("Decision Center Monthly Snapshot", month)
        if not force or doc.locked:
            return doc
    return _generate_snapshot(month, company, reason=reason, action="regenerated", called_by_scheduler=called_by_scheduler)


def regenerate_snapshot(month, reason, company=None):
    if not reason:
        frappe.throw(frappe._("Regeneration reason is required."))

    if not frappe.db.exists("Decision Center Monthly Snapshot", month):
        return get_or_generate_snapshot(month, company=company, reason=reason, called_by_scheduler=False)

    doc = frappe.get_doc("Decision Center Monthly Snapshot", month)
    if doc.locked and not frappe.flags.get("in_snapshot_maintenance"):
        frappe.throw(frappe._("Snapshot is locked and cannot be regenerated outside maintenance mode."))

    return _generate_snapshot(month, company=company, reason=reason, action="unlocked_override", called_by_scheduler=False)


def lock_snapshot(month):
    if not frappe.db.exists("Decision Center Monthly Snapshot", month):
        return
    doc = frappe.get_doc("Decision Center Monthly Snapshot", month)
    if doc.locked:
        return
    doc.db_set("locked", 1, update_modified=False)
    doc.db_set("locked_at", now(), update_modified=False)
    doc.db_set("locked_by", frappe.session.user, update_modified=False)
    _create_revision(doc, action="locked", reason="Auto-locked after grace period")


def run_scheduler():
    """Called by the daily scheduler event."""
    settings = get_decision_center_settings()
    if not cint(settings.get("monthly_snapshot_enabled")):
        return

    today = getdate(nowdate())
    # Generate snapshot for the previous month if today is after month-end.
    if today.day == 1:
        prev_month = _previous_month(today)
        get_or_generate_snapshot(prev_month, called_by_scheduler=True)

    # Lock snapshots whose grace period has passed
    grace_days = cint(settings.get("auto_lock_snapshots_days") or 7)
    lock_cutoff = today - timedelta(days=grace_days)
    for snap_name in frappe.get_all(
        "Decision Center Monthly Snapshot",
        filters={"locked": 0},
        pluck="name",
    ):
        snap = frappe.get_doc("Decision Center Monthly Snapshot", snap_name)
        month_date = date(int(snap.month[:4]), int(snap.month[5:7]), 1)
        grace_end = _month_end(month_date) + timedelta(days=grace_days)
        if today > grace_end:
            lock_snapshot(snap.name)


# ── Core generation ─────────────────────────────────────────────────────────

def _generate_snapshot(month, company, reason=None, action="generated", called_by_scheduler=False):
    month_start, month_end = _month_bounds(month)
    company = company or _default_company()

    previous_payload = None
    if frappe.db.exists("Decision Center Monthly Snapshot", month):
        previous_payload = _snapshot_payload(frappe.get_doc("Decision Center Monthly Snapshot", month))

    metrics_snapshot = _build_metrics_snapshot(month_start, month_end, company)
    expense_snapshot = _build_expense_snapshot(month_start, month_end, company)
    inventory_snapshot = _build_inventory_snapshot(month_end, company)
    plan_snapshot = _build_plan_snapshot(month_start, month_end, company)
    decisions_snapshot = _build_decisions_snapshot(month_start, month_end, company)
    settings_version = _settings_version()
    rule_hash = _rule_version_hash()

    payload = {
        "month": month,
        "company": company,
        "metrics": metrics_snapshot,
        "expense_categories": expense_snapshot,
        "inventory": inventory_snapshot,
        "plan": plan_snapshot,
        "decisions": decisions_snapshot,
        "settings_version": settings_version,
        "rule_version_hash": rule_hash,
        "engine_version": SNAPSHOT_ENGINE_VERSION,
    }

    if frappe.db.exists("Decision Center Monthly Snapshot", month):
        doc = frappe.get_doc("Decision Center Monthly Snapshot", month)
        _set_snapshot_fields(doc, payload)
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.new_doc("Decision Center Monthly Snapshot")
        doc.name = month
        doc.month = month
        _set_snapshot_fields(doc, payload)
        doc.insert(ignore_permissions=True)

    doc.db_set("generated_at", now())
    doc.db_set("created_by_scheduler", 1 if called_by_scheduler else 0)

    _create_revision(doc, action=action, reason=reason or "Snapshot generated", previous_payload=previous_payload)

    return doc


def _set_snapshot_fields(doc, payload):
    doc.metrics_snapshot = json.dumps(payload["metrics"], ensure_ascii=False, default=str)
    doc.expense_categories_snapshot = json.dumps(payload["expense_categories"], ensure_ascii=False, default=str)
    doc.inventory_snapshot = json.dumps(payload["inventory"], ensure_ascii=False, default=str)
    doc.plan_snapshot = json.dumps(payload["plan"], ensure_ascii=False, default=str)
    doc.decisions_snapshot = json.dumps(payload["decisions"], ensure_ascii=False, default=str)
    doc.settings_version = json.dumps(payload["settings_version"], ensure_ascii=False, default=str)
    doc.rule_version_hash = payload["rule_version_hash"]
    doc.engine_version = payload["engine_version"]


def _snapshot_payload(doc):
    return {
        "month": doc.month,
        "metrics": _json_or_empty(doc.metrics_snapshot),
        "expense_categories": _json_or_empty(doc.expense_categories_snapshot),
        "inventory": _json_or_empty(doc.inventory_snapshot),
        "plan": _json_or_empty(doc.plan_snapshot),
        "decisions": _json_or_empty(doc.decisions_snapshot),
        "settings_version": _json_or_empty(doc.settings_version),
        "rule_version_hash": doc.rule_version_hash,
        "engine_version": doc.engine_version,
    }


def _json_or_empty(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except Exception:
        return {}


# ── Snapshot components ──────────────────────────────────────────────────────

def _build_metrics_snapshot(month_start, month_end, company):
    snapshot = {}
    for metric_key, meta in METRIC_REGISTRY.items():
        if not meta.get("system_available"):
            continue
        try:
            result = compute_metric(metric_key, month_start, month_end, company=company)
            snapshot[metric_key] = {
                "value": result.get("value"),
                "unit": meta.get("unit"),
                "formula": result.get("formula_description"),
                "source": result.get("source"),
                "period": result.get("period"),
            }
        except Exception as e:
            snapshot[metric_key] = {
                "value": None,
                "error": str(e),
                "source": meta.get("calculation_module"),
            }
    return snapshot


def _build_expense_snapshot(month_start, month_end, company):
    prev_start = month_start - timedelta(days=(month_end - month_start).days + 1)
    prev_end = month_start - timedelta(days=1)
    result = get_expense_metrics(company, month_start, month_end, prev_start, prev_end)
    categories = []
    cats = get_expense_categories()
    account_map = {}
    for cat in cats:
        for acc in cat.get("accounts", []):
            account_map[acc.get("account")] = {
                "category": cat.get("category_name"),
                "target": flt(cat.get("target_percent_of_sales")),
                "max": flt(cat.get("max_percent_of_sales")),
            }

    for row in result.get("categories", []):
        cat_name = row.get("category")
        categories.append({
            "category": cat_name,
            "amount": flt(row.get("current_amount")),
            "previous_amount": flt(row.get("previous_amount")),
            "growth_pct": flt(row.get("growth_pct")),
            "target": account_map.get(cat_name, {}).get("target"),
            "max": account_map.get(cat_name, {}).get("max"),
        })

    total_expenses = flt(result.get("total"))
    try:
        sales_result = get_sales_metrics(company, month_start, month_end, prev_start, prev_end)
        sales_total = flt(sales_result.get("total"))
    except Exception:
        sales_total = 0.0
    expense_to_sales_pct = (total_expenses / sales_total * 100.0) if sales_total else 0.0

    return {
        "total_expenses": total_expenses,
        "sales_total": sales_total,
        "expense_to_sales_pct": expense_to_sales_pct,
        "categories": categories,
    }


def _build_inventory_snapshot(month_end, company):
    """Reconstruct inventory from Stock Ledger Entry. Mark unavailable if unreliable."""
    try:
        rows = frappe.db.sql(
            """
            SELECT
                item_code,
                SUM(actual_qty) AS qty,
                SUM(stock_value_difference) AS stock_value
            FROM `tabStock Ledger Entry`
            WHERE company = %(company)s
              AND posting_date <= %(month_end)s
              AND is_cancelled = 0
            GROUP BY item_code
            HAVING qty > 0
            """,
            {"company": company, "month_end": month_end},
            as_dict=True,
        )
        if not rows:
            return {"unavailable": True, "reason": "No Stock Ledger Entries found for period", "items": []}

        dead_days = cint(get_threshold("dead_stock_days", 180))
        slow_days = cint(get_threshold("slow_moving_days", 90))
        lookback_start_dead = month_end - timedelta(days=dead_days)
        lookback_start_slow = month_end - timedelta(days=slow_days)

        sales_dead = get_item_sales(company, lookback_start_dead, month_end)
        sales_slow = get_item_sales(company, lookback_start_slow, month_end)
        sold_dead = {i["item_code"] for i in sales_dead if flt(i.get("net_qty", 0)) > 0}
        sales_slow_map = {i["item_code"]: i for i in sales_slow}

        dead_value = 0.0
        slow_value = 0.0
        total_value = 0.0
        item_count = 0
        items = []
        for row in rows:
            item_code = row.get("item_code")
            qty = flt(row.get("qty"))
            value = flt(row.get("stock_value"))
            total_value += value
            item_count += 1
            is_dead = qty > 0 and item_code not in sold_dead
            is_slow = False
            sales = sales_slow_map.get(item_code, {})
            s_qty = flt(sales.get("net_qty", 0))
            s_days = cint(sales.get("days", 1))
            avg_daily = s_qty / s_days if s_days else 0
            if qty > 0 and avg_daily > 0 and (qty / avg_daily) > slow_days:
                is_slow = True
            if is_dead:
                dead_value += value
            if is_slow:
                slow_value += value
            items.append({
                "item_code": item_code,
                "qty": qty,
                "stock_value": value,
                "dead": is_dead,
                "slow": is_slow,
            })

        return {
            "unavailable": False,
            "total_value": total_value,
            "item_count": item_count,
            "dead_stock_value": dead_value,
            "slow_moving_stock_value": slow_value,
            "source": "Stock Ledger Entry reconstruction as of month-end",
            "items": items,
        }
    except Exception as e:
        return {"unavailable": True, "reason": str(e), "items": []}


def _build_plan_snapshot(month_start, month_end, company):
    active_plan = frappe.get_all(
        "Decision Center Plan",
        filters={"status": "Active"},
        fields=["name"],
        limit_page_length=1,
    )
    if not active_plan:
        return {"active_plan": None}

    plan = frappe.get_doc("Decision Center Plan", active_plan[0].name)
    # Refresh KPIs as of month_end
    as_of = min(month_end, getdate(plan.end_date))
    primary = next((k for k in plan.kpis if k.is_primary), None)

    kpi_snapshot = []
    for kpi in plan.kpis:
        measures = _kpi_measures_at_date(kpi, plan, as_of)
        kpi_snapshot.append({
            "metric_key": kpi.metric_key,
            "is_primary": kpi.is_primary,
            "direction": kpi.direction,
            "target_value": flt(kpi.target_value),
            "effective_baseline": flt(kpi.effective_baseline),
            "current_value": flt(kpi.current_value),
            "progress_strategy": kpi.progress_strategy,
            "measures": measures,
            "target_achieved": bool(kpi.target_achieved),
        })

    # Actions completed during the month, persisted here
    completed_actions = []
    for action in plan.actions:
        if action.status == "Completed" and action.completed_at:
            completed_at = getdate(action.completed_at)
            if month_start <= completed_at <= month_end:
                completed_actions.append({
                    "title": action.title,
                    "completed_at": str(completed_at),
                    "completed_by": action.completed_by,
                })

    return {
        "active_plan": plan.name,
        "plan_name": plan.plan_name,
        "status": plan.status,
        "start_date": str(plan.start_date),
        "end_date": str(plan.end_date),
        "target_achieved": bool(plan.target_achieved),
        "primary_kpi": primary.metric_key if primary else None,
        "kpis": kpi_snapshot,
        "completed_actions": completed_actions,
    }


def _kpi_measures_at_date(kpi, plan, as_of_date):
    current = flt(kpi.current_value)
    target = flt(kpi.target_value)
    baseline = flt(kpi.effective_baseline)
    time_pct = time_progress(plan.start_date, plan.end_date, as_of_date)
    strategy = kpi.progress_strategy

    if strategy == "level":
        progress = level_progress(current, baseline, target, kpi.direction)
        return {
            "final_target_completion_pct": progress,
            "pace_attainment_pct": progress,
        }
    if strategy == "cumulative_growth":
        return cumulative_growth_measures(current, target, time_pct)
    if strategy == "cumulative_ceiling":
        return cumulative_ceiling_measures(current, target, time_pct)
    return {}


def _build_decisions_snapshot(month_start, month_end, company):
    prev_start = month_start - timedelta(days=(month_end - month_start).days + 1)
    prev_end = month_start - timedelta(days=1)
    try:
        decisions = evaluate_all_rules(company, month_start, month_end, prev_start, prev_end)
        return {"count": len(decisions), "decisions": decisions}
    except Exception as e:
        return {"count": 0, "error": str(e), "decisions": []}


# ── Versioning / hashing ─────────────────────────────────────────────────────

def _settings_version():
    settings = get_decision_center_settings()
    return {
        "slow_moving_days": cint(settings.get("slow_moving_days")) if settings else 90,
        "dead_stock_days": cint(settings.get("dead_stock_days")) if settings else 180,
        "low_stock_days": cint(settings.get("low_stock_days")) if settings else 7,
        "sales_drop_percent": flt(settings.get("sales_drop_percent")) if settings else 30.0,
        "sales_growth_percent": flt(settings.get("sales_growth_percent")) if settings else 30.0,
        "purchase_price_increase_percent": flt(settings.get("purchase_price_increase_percent")) if settings else 10.0,
        "customer_drop_percent": flt(settings.get("customer_drop_percent")) if settings else 30.0,
        "expense_vs_sales_threshold": flt(settings.get("expense_vs_sales_threshold")) if settings else 10.0,
        "expense_increase_threshold": flt(settings.get("expense_increase_threshold")) if settings else 20.0,
        "expense_anomaly_threshold": flt(settings.get("expense_anomaly_threshold")) if settings else 30.0,
        "plan_health_tolerance_pct": flt(settings.get("plan_health_tolerance_pct")) if settings else 10.0,
        "auto_lock_snapshots_days": cint(settings.get("auto_lock_snapshots_days")) if settings else 7,
    }


def _rule_version_hash():
    settings = get_decision_center_settings()
    if not settings:
        return "no_settings"
    enabled = {r.get("rule_id"): r.get("enabled") for r in settings.get("rule_settings", [])}
    payload = json.dumps(enabled, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ── Revision history ───────────────────────────────────────────────────────

def _create_revision(doc, action, reason, previous_payload=None):
    existing_count = frappe.db.count("Decision Center Snapshot Revision", filters={"parent_snapshot": doc.name})
    rev = frappe.new_doc("Decision Center Snapshot Revision")
    rev.parent_snapshot = doc.name
    rev.revision_number = existing_count + 1
    rev.action = action
    rev.performed_by = frappe.session.user
    rev.performed_at = now()
    rev.reason = reason
    rev.engine_version = SNAPSHOT_ENGINE_VERSION
    rev.settings_hash = hashlib.sha256(doc.settings_version.encode("utf-8")).hexdigest()[:16] if doc.settings_version else ""
    rev.rule_hash = doc.rule_version_hash or ""
    if previous_payload:
        rev.previous_snapshot_payload = json.dumps(previous_payload, ensure_ascii=False, default=str)
    rev.insert(ignore_permissions=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _month_bounds(month):
    year = int(month[:4])
    mon = int(month[5:7])
    _, last_day = monthrange(year, mon)
    return date(year, mon, 1), date(year, mon, last_day)


def _month_end(month_date):
    _, last_day = monthrange(month_date.year, month_date.month)
    return date(month_date.year, month_date.month, last_day)


def _previous_month(d):
    if d.month == 1:
        return "{:04d}-12".format(d.year - 1)
    return "{:04d}-{:02d}".format(d.year, d.month - 1)


def _default_company():
    return frappe.defaults.get_user_default("Company") or frappe.db.get_value("Company", {}, "name")
