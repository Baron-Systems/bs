# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Public API for Monthly Snapshots / Reports."""

from __future__ import unicode_literals

import json

import frappe
from frappe.utils import cint, flt, getdate

from .snapshot_service import (
    get_or_generate_snapshot,
    regenerate_snapshot as service_regenerate,
)


def _json_or_empty(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except Exception:
        return {}


@frappe.whitelist()
def get_monthly_report_list(count=24):
    """Return last N monthly snapshots with summary metadata."""
    snapshots = frappe.get_all(
        "Decision Center Monthly Snapshot",
        fields=["name", "month", "generated_at", "locked_at", "locked", "locked_by", "engine_version"],
        order_by="month desc",
        page_length=cint(count),
    )
    result = []
    for snap in snapshots:
        metrics = _json_or_empty(frappe.db.get_value("Decision Center Monthly Snapshot", snap.name, "metrics_snapshot"))
        plan = _json_or_empty(frappe.db.get_value("Decision Center Monthly Snapshot", snap.name, "plan_snapshot"))
        expense = _json_or_empty(frappe.db.get_value("Decision Center Monthly Snapshot", snap.name, "expense_categories_snapshot"))
        result.append({
            "month": snap.month,
            "generated_at": str(snap.generated_at) if snap.generated_at else None,
            "is_locked": bool(snap.locked),
            "locked_at": str(snap.locked_at) if snap.locked_at else None,
            "sales_total": metrics.get("sales_total", {}).get("value"),
            "total_expenses": expense.get("total_expenses"),
            "expense_to_sales_pct": expense.get("expense_to_sales_pct"),
            "decision_count": _json_or_empty(
                frappe.db.get_value("Decision Center Monthly Snapshot", snap.name, "decisions_snapshot")
            ).get("count", 0),
            "plan_status": plan.get("status") if plan.get("active_plan") else None,
            "engine_version": snap.engine_version,
        })
    return {"reports": result}


@frappe.whitelist()
def get_monthly_report(month):
    """Return a historical monthly report reading exclusively from the snapshot."""
    if not frappe.db.exists("Decision Center Monthly Snapshot", month):
        frappe.throw(frappe._("No snapshot found for month {0}").format(month))

    snap = frappe.get_doc("Decision Center Monthly Snapshot", month)
    metrics = _json_or_empty(snap.metrics_snapshot)
    expense = _json_or_empty(snap.expense_categories_snapshot)
    inventory = _json_or_empty(snap.inventory_snapshot)
    plan = _json_or_empty(snap.plan_snapshot)
    decisions = _json_or_empty(snap.decisions_snapshot)
    settings_version = _json_or_empty(snap.settings_version)

    # Previous-month comparison (also from snapshot)
    prev_month = _previous_month_str(month)
    prev_metrics = {}
    if frappe.db.exists("Decision Center Monthly Snapshot", prev_month):
        prev_metrics = _json_or_empty(
            frappe.db.get_value("Decision Center Monthly Snapshot", prev_month, "metrics_snapshot")
        )

    changes = {}
    for key in ["sales_total", "total_expenses", "active_customers"]:
        cur = metrics.get(key, {}).get("value")
        prev = prev_metrics.get(key, {}).get("value")
        if cur is not None and prev is not None and flt(prev) != 0:
            changes[key] = round(((flt(cur) - flt(prev)) / flt(prev)) * 100.0, 2)
        else:
            changes[key] = None

    revisions = frappe.get_all(
        "Decision Center Snapshot Revision",
        filters={"parent_snapshot": snap.name},
        fields=["revision_number", "action", "performed_by", "performed_at", "reason", "engine_version"],
        order_by="revision_number desc",
    )

    return {
        "month": month,
        "generated_at": str(snap.generated_at) if snap.generated_at else None,
        "is_locked": bool(snap.locked),
        "locked_at": str(snap.locked_at) if snap.locked_at else None,
        "metrics": metrics,
        "expense_categories": expense,
        "inventory": inventory,
        "plan": plan,
        "decisions": decisions,
        "changes_from_previous_month": changes,
        "settings_version": settings_version,
        "rule_version_hash": snap.rule_version_hash,
        "engine_version": snap.engine_version,
        "revisions": revisions,
    }


@frappe.whitelist()
def regenerate_snapshot(month, reason):
    if not reason:
        frappe.throw(frappe._("Reason is required to regenerate a snapshot."))
    doc = service_regenerate(month, reason)
    return {"month": doc.month, "generated_at": str(doc.generated_at)}


def _previous_month_str(month):
    d = getdate("{}-01".format(month))
    if d.month == 1:
        return "{:04d}-12".format(d.year - 1)
    return "{:04d}-{:02d}".format(d.year, d.month - 1)
