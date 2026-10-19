# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Public API for Plans."""

from __future__ import unicode_literals

import json

import frappe
from frappe.utils import cint, flt, getdate, now, nowdate

from .plan_engine import (
    activate_plan as engine_activate,
    cancel_plan as engine_cancel,
    complete_plan as engine_complete,
    refresh_plan,
    _compute_kpi_measures,
)
from .config import get_decision_center_settings
from .expenses import get_expense_categories
from .periods import get_period_dates
from .registry import compute_baseline, get_metric_capability
from .rules import RULES, evaluate_all_rules


# ── Helpers ──────────────────────────────────────────────────────────────────

def _default_company():
    return frappe.defaults.get_user_default("Company") or frappe.db.get_value("Company", {}, "name")


def _validate_metric_for_plans(metric_key):
    meta = get_metric_capability(metric_key)
    if not meta:
        frappe.throw(frappe._("Unknown metric: {0}").format(metric_key))
    if not meta.get("system_available"):
        frappe.throw(frappe._("Metric {0} is not system-available: {1}").format(metric_key, meta.get("unavailable_reason")))
    if not meta.get("enabled_for_plans"):
        frappe.throw(frappe._("Metric {0} is not enabled for plans.").format(metric_key))
    return meta


def _kpi_preview_baseline(kpi_row, start_date):
    meta = get_metric_capability(kpi_row.metric_key)
    strategy = meta.get("baseline_strategy") if meta else kpi_row.baseline_strategy
    try:
        info = compute_baseline(
            metric_key=kpi_row.metric_key,
            strategy=strategy,
            reference_date=start_date,
            plan_start_date=start_date,
        )
        kpi_row.computed_baseline = flt(info.get("value"))
    except Exception:
        kpi_row.computed_baseline = 0.0


@frappe.whitelist()
def has_plan_management_permission():
    """Return True if the current user may create/edit/activate plans."""
    user = frappe.session.user
    if user == "Administrator":
        return True
    return "Decision Center Manager" in frappe.get_roles(user) or "System Manager" in frappe.get_roles(user)


@frappe.whitelist()
def compute_baseline_preview(metric_key, reference_date, plan_start_date=None, company=None):
    """Return a preview baseline for a metric used in plan forms."""
    meta = get_metric_capability(metric_key)
    if not meta:
        frappe.throw(frappe._("Unknown metric: {0}").format(metric_key))
    if not meta.get("system_available"):
        frappe.throw(frappe._("Metric {0} is not system-available.").format(metric_key))
    try:
        info = compute_baseline(
            metric_key=metric_key,
            strategy=meta.get("baseline_strategy"),
            reference_date=reference_date,
            plan_start_date=plan_start_date or reference_date,
            company=company,
        )
    except Exception as e:
        frappe.throw(frappe._("Could not compute baseline: {0}").format(str(e)))
    return {
        "value": flt(info.get("value")),
        "from_date": info.get("from_date"),
        "to_date": info.get("to_date"),
        "source": info.get("source"),
    }


@frappe.whitelist()
def get_plan_reference_options():
    """Return metrics, rules, expense categories, and defaults for plan creation."""
    from .registry import list_metrics_for_plans
    categories = []
    try:
        categories = get_expense_categories(enabled_only=False) or []
    except Exception:
        categories = []
    settings = get_decision_center_settings()
    return {
        "metrics": list_metrics_for_plans(),
        "rules": [{"id": r["id"], "title": r["title_template"]} for r in RULES],
        "expense_categories": categories,
        "default_plan_priority": getattr(settings, "default_plan_priority", None) or "Medium",
    }


@frappe.whitelist()
def get_plan_decisions(plan_name):
    """Return decisions related to a plan during its active date range."""
    plan = frappe.get_doc("Decision Center Plan", plan_name)
    company = frappe.defaults.get_user_default("Company") or frappe.db.get_value("Company", {}, "name")
    start = getdate(plan.start_date)
    end = getdate(plan.end_date)
    today = getdate(nowdate())
    to_date = min(end, today)
    if to_date < start:
        return {"decisions": []}

    fd, td, pf, pt = get_period_dates("custom", custom_from=str(start), custom_to=str(to_date))
    decisions = evaluate_all_rules(company, fd, td, pf, pt)

    kpi_keys = {k.metric_key for k in plan.kpis}
    action_rule_ids = {a.related_rule_id for a in plan.actions if a.related_rule_id}
    kpi_categories = {get_metric_capability(k).get("category") for k in kpi_keys if get_metric_capability(k)}

    def is_related(d):
        if d.get("rule_id") in action_rule_ids:
            return True
        if d.get("metric_key") in kpi_keys:
            return True
        if d.get("category") in kpi_categories:
            return True
        return False

    return {"decisions": [d for d in decisions if is_related(d)]}


# ── Read endpoints ───────────────────────────────────────────────────────────

@frappe.whitelist()
def get_current_plan():
    """Return the currently Active plan with computed progress and health."""
    active = frappe.get_all(
        "Decision Center Plan",
        filters={"status": "Active"},
        fields=["name"],
        limit_page_length=1,
    )
    if not active:
        return None
    return get_plan_detail(active[0].name)


@frappe.whitelist()
def get_plans(status=None, limit_start=0, limit_page_length=50):
    filters = {}
    if status:
        filters["status"] = status
    plans = frappe.get_all(
        "Decision Center Plan",
        filters=filters,
        fields=["name", "plan_name", "status", "scheduler_status", "priority", "start_date", "end_date", "target_achieved", "modified"],
        order_by="modified desc",
        start=limit_start,
        page_length=limit_page_length,
    )
    return {"plans": plans}


@frappe.whitelist()
def get_plan_detail(plan_name):
    plan = frappe.get_doc("Decision Center Plan", plan_name)
    refresh_info = refresh_plan(plan.name, save=True)
    plan.reload()

    progress = {
        "outcome_progress": flt(refresh_info.get("outcome", {}).get("progress_or_pace_value")),
        "execution_progress": flt(refresh_info.get("execution_progress")) if refresh_info.get("execution_progress") is not None else None,
        "time_progress": flt(refresh_info.get("time_progress")),
        "health": refresh_info.get("health"),
    }

    kpis = []
    for kpi in plan.kpis:
        kpis.append({
            "metric_key": kpi.metric_key,
            "metric_label": kpi.metric_label,
            "is_primary": kpi.is_primary,
            "direction": kpi.direction,
            "progress_strategy": kpi.progress_strategy,
            "baseline_strategy": kpi.baseline_strategy,
            "computed_baseline": flt(kpi.computed_baseline),
            "override_baseline": flt(kpi.override_baseline),
            "override_reason": kpi.override_reason,
            "effective_baseline": flt(kpi.effective_baseline),
            "target_value": flt(kpi.target_value),
            "current_value": flt(kpi.current_value),
            "target_achieved": bool(kpi.target_achieved),
        })

    actions = []
    for action in plan.actions:
        actions.append({
            "title": action.title,
            "description": action.description,
            "due_date": str(action.due_date) if action.due_date else None,
            "status": action.status,
            "weight": flt(action.weight),
            "related_rule_id": action.related_rule_id,
            "related_expense_category": action.related_expense_category,
            "related_metric_key": action.related_metric_key,
            "completed_at": str(action.completed_at) if action.completed_at else None,
            "completed_by": action.completed_by,
        })

    checkpoints = []
    for cp in plan.checkpoints:
        checkpoints.append({
            "month": cp.month,
            "from_date": str(cp.from_date) if cp.from_date else None,
            "to_date": str(cp.to_date) if cp.to_date else None,
            "target_value": flt(cp.target_value),
            "actual_value": flt(cp.actual_value),
            "health": cp.health,
            "final_target_completion_pct": flt(cp.final_target_completion_pct),
            "pace_attainment_pct": flt(cp.pace_attainment_pct),
            "cap_utilization_pct": flt(cp.cap_utilization_pct),
            "remaining_amount": flt(cp.remaining_amount),
            "consumption_pace_pct": flt(cp.consumption_pace_pct),
        })

    return {
        "name": plan.name,
        "plan_name": plan.plan_name,
        "description": plan.description,
        "status": plan.status,
        "scheduler_status": plan.scheduler_status,
        "priority": plan.priority,
        "start_date": str(plan.start_date),
        "end_date": str(plan.end_date),
        "target_achieved": bool(plan.target_achieved),
        "notes": plan.notes,
        "created_by": plan.created_by,
        "created_at": str(plan.created_at) if plan.created_at else None,
        "activated_at": str(plan.activated_at) if plan.activated_at else None,
        "completed_at": str(plan.completed_at) if plan.completed_at else None,
        "progress": progress,
        "kpis": kpis,
        "actions": actions,
        "checkpoints": checkpoints,
    }


def _build_progress(plan):
    from .registry import plan_health, time_progress
    primary = next((k for k in plan.kpis if k.is_primary), None)
    if not primary:
        return {"outcome": None, "execution": None, "time": None, "health": None}

    measures = _compute_kpi_measures(primary, plan, None)
    strategy = primary.progress_strategy or "level"
    if strategy == "cumulative_ceiling":
        outcome = flt(measures.get("consumption_pace_pct"))
    else:
        outcome = flt(measures.get("pace_attainment_pct"))

    time_pct = time_progress(plan.start_date, plan.end_date)
    from .plan_engine import _compute_execution_progress
    execution = _compute_execution_progress(plan.actions)
    health = plan_health(outcome, time_pct, _get_tolerance(plan, primary), strategy=strategy)
    return {
        "outcome_progress": outcome,
        "execution_progress": execution,
        "time_progress": time_pct,
        "health": health,
    }


def _get_tolerance(plan, primary):
    if primary and primary.tolerance_pct:
        return flt(primary.tolerance_pct)
    settings = frappe.get_single("Decision Center Settings")
    return flt(settings.get("plan_health_tolerance_pct") or 10)


# ── Write endpoints ───────────────────────────────────────────────────────────

@frappe.whitelist()
def create_plan(data):
    payload = json.loads(data) if isinstance(data, str) else data
    doc = frappe.new_doc("Decision Center Plan")
    _apply_plan_payload(doc, payload, is_new=True)
    doc.insert()
    return {"name": doc.name, "message": "Plan created"}


@frappe.whitelist()
def update_plan(plan_name, data):
    payload = json.loads(data) if isinstance(data, str) else data
    doc = frappe.get_doc("Decision Center Plan", plan_name)
    if doc.status in ("Completed", "Cancelled"):
        frappe.throw(frappe._("Cannot edit a Completed or Cancelled plan."))
    new_status = payload.get("status")
    if new_status and new_status != doc.status:
        _transition_status(doc, new_status)
    _apply_plan_payload(doc, payload, is_new=False)
    doc.save()
    return {"name": doc.name, "message": "Plan updated"}


def _transition_status(doc, new_status):
    allowed = {
        "Draft": {"Scheduled"},
        "Scheduled": {"Draft"},
    }
    current = doc.status
    if current == new_status:
        return
    if new_status in allowed.get(current, set()):
        doc.status = new_status
    else:
        frappe.throw(
            frappe._("Cannot transition plan from {0} to {1} via update. Use lifecycle actions.").format(current, new_status)
        )


def _apply_plan_payload(doc, payload, is_new):
    doc.plan_name = payload.get("plan_name")
    doc.description = payload.get("description")
    settings = get_decision_center_settings()
    default_priority = getattr(settings, "default_plan_priority", None) or "Medium"
    doc.priority = payload.get("priority") or default_priority
    doc.start_date = payload.get("start_date")
    doc.end_date = payload.get("end_date")
    doc.notes = payload.get("notes")
    if is_new:
        doc.status = payload.get("status", "Draft")
        doc.scheduler_status = "none"

    # Replace KPIs
    doc.set("kpis", [])
    primary_count = 0
    for kpi in payload.get("kpis", []):
        metric_key = kpi.get("metric_key")
        meta = _validate_metric_for_plans(metric_key)
        if kpi.get("is_primary"):
            primary_count += 1
        row = doc.append("kpis", {})
        row.is_primary = kpi.get("is_primary", 0)
        row.metric_key = metric_key
        row.metric_label = meta.get("metric_label_ar") or meta.get("metric_label_en") or metric_key
        row.direction = kpi.get("direction")
        row.weight = flt(kpi.get("weight"))
        row.tolerance_pct = flt(kpi.get("tolerance_pct"))
        row.baseline_strategy = meta.get("baseline_strategy")
        row.progress_strategy = meta.get("progress_strategy")
        row.target_value = flt(kpi.get("target_value"))
        row.override_baseline = flt(kpi.get("override_baseline")) if kpi.get("override_baseline") is not None else None
        row.override_reason = kpi.get("override_reason")
        if row.override_baseline is not None:
            row.overridden_by = frappe.session.user
            row.overridden_at = now()
        # Compute preview baseline for Scheduled plans
        if doc.status in ("Draft", "Scheduled"):
            _kpi_preview_baseline(row, doc.start_date)
        row.effective_baseline = row.override_baseline if row.override_baseline is not None else row.computed_baseline

    if primary_count != 1:
        frappe.throw(frappe._("Exactly one KPI must be primary."))

    # Replace actions
    doc.set("actions", [])
    for action in payload.get("actions", []):
        row = doc.append("actions", {})
        row.title = action.get("title")
        row.description = action.get("description")
        row.due_date = action.get("due_date")
        row.status = action.get("status", "Not Started")
        row.weight = flt(action.get("weight"))
        row.related_rule_id = action.get("related_rule_id")
        row.related_expense_category = action.get("related_expense_category")
        row.related_metric_key = action.get("related_metric_key")
        if row.status == "Completed" and not row.completed_at:
            row.completed_at = now()
            row.completed_by = frappe.session.user


@frappe.whitelist()
def activate_plan(plan_name):
    return engine_activate(plan_name)


@frappe.whitelist()
def complete_plan(plan_name):
    return engine_complete(plan_name)


@frappe.whitelist()
def cancel_plan(plan_name):
    return engine_cancel(plan_name)


@frappe.whitelist()
def schedule_plan(plan_name):
    """Move a Draft plan to Scheduled."""
    doc = frappe.get_doc("Decision Center Plan", plan_name)
    if doc.status != "Draft":
        frappe.throw(frappe._("Only Draft plans can be scheduled."))
    doc.status = "Scheduled"
    doc.scheduler_status = "none"
    doc.save()
    return {"status": "Scheduled", "message": "Plan scheduled."}


@frappe.whitelist()
def update_plan_actions(plan_name, actions):
    """Replace the actions table of a non-terminal plan and refresh execution progress."""
    actions_payload = json.loads(actions) if isinstance(actions, str) else actions
    doc = frappe.get_doc("Decision Center Plan", plan_name)
    if doc.status in ("Completed", "Cancelled"):
        frappe.throw(frappe._("Cannot edit actions of a terminal plan."))

    doc.set("actions", [])
    for action in actions_payload:
        row = doc.append("actions", {})
        row.title = action.get("title")
        row.description = action.get("description")
        row.due_date = action.get("due_date")
        row.status = action.get("status", "Not Started")
        row.weight = flt(action.get("weight"))
        row.related_rule_id = action.get("related_rule_id")
        row.related_expense_category = action.get("related_expense_category")
        row.related_metric_key = action.get("related_metric_key")
        if row.status == "Completed" and not row.completed_at:
            row.completed_at = now()
            row.completed_by = frappe.session.user
        elif row.status != "Completed":
            row.completed_at = None
            row.completed_by = None

    doc.save()
    refresh_plan(doc.name, save=True)
    return {"status": "ok", "message": "Actions updated."}


# ── Metric registry endpoints ────────────────────────────────────────────────

@frappe.whitelist()
def get_metric_capabilities():
    """Return metric registry for Settings / plan creation."""
    from .registry import METRIC_REGISTRY
    result = []
    for key, meta in METRIC_REGISTRY.items():
        row = dict(meta)
        row["metric_key"] = key
        result.append(row)
    return {"metrics": result}


@frappe.whitelist()
def compute_metric_value(metric_key, from_date, to_date, company=None):
    from .registry import compute_metric
    company = company or _default_company()
    return compute_metric(metric_key, from_date, to_date, company=company)
