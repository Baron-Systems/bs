# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Plan engine: lifecycle helpers, progress computation, checkpoints."""

from __future__ import unicode_literals

import json
from datetime import date, datetime, timedelta

import frappe
from frappe.utils import cint, flt, getdate, now, nowdate

from .registry import (
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


# ── Lifecycle actions ────────────────────────────────────────────────────────

@frappe.whitelist()
def activate_plan(plan_name):
    plan = frappe.get_doc("Decision Center Plan", plan_name)
    if plan.status != "Scheduled":
        frappe.throw(frappe._("Only Scheduled plans can be activated."))
    if getdate(plan.start_date) > getdate(nowdate()):
        frappe.throw(frappe._("Cannot activate a plan before its Start Date."))

    active = frappe.get_all(
        "Decision Center Plan",
        filters={"status": "Active"},
        pluck="name",
        limit_page_length=1,
    )
    if active and active[0] != plan.name:
        frappe.throw(
            frappe._("Only one Active plan is allowed. Plan '{0}' is already Active.").format(active[0])
        )

    _lock_baselines(plan)
    _generate_checkpoints(plan)

    plan.reload()
    plan.status = "Active"
    plan.scheduler_status = "none"
    plan.activated_at = now()
    plan.save()
    _refresh_kpis(plan, save=True)
    return {"status": "Active", "message": "Plan activated and baselines locked."}


@frappe.whitelist()
def complete_plan(plan_name):
    plan = frappe.get_doc("Decision Center Plan", plan_name)
    if plan.status != "Active":
        frappe.throw(frappe._("Only Active plans can be completed."))
    _refresh_kpis(plan, save=True)
    plan.status = "Completed"
    plan.scheduler_status = "none"
    plan.completed_at = now()
    plan.save()
    return {"status": "Completed", "message": "Plan completed."}


@frappe.whitelist()
def cancel_plan(plan_name):
    plan = frappe.get_doc("Decision Center Plan", plan_name)
    if plan.status in ("Completed", "Cancelled"):
        frappe.throw(frappe._("Plan is already terminal."))
    plan.status = "Cancelled"
    plan.scheduler_status = "none"
    plan.save()
    return {"status": "Cancelled"}


# ── KPI refresh / progress computation ───────────────────────────────────────

def refresh_plan(plan_name, as_of_date=None, save=True):
    plan = frappe.get_doc("Decision Center Plan", plan_name)
    return _refresh_kpis(plan, as_of_date=as_of_date, save=save)


def _refresh_kpis(plan, as_of_date=None, save=True):
    as_of = getdate(as_of_date or nowdate())
    plan_as_of_end = min(as_of, getdate(plan.end_date))

    primary_kpi = None
    for kpi in plan.kpis:
        if kpi.is_primary:
            primary_kpi = kpi
        _refresh_single_kpi(kpi, plan, plan_as_of_end)

    outcome = _compute_outcome(primary_kpi, plan, as_of)
    execution = _compute_execution_progress(plan.actions)
    time_pct = time_progress(plan.start_date, plan.end_date, as_of)

    health = plan_health(
        outcome["progress_or_pace_value"],
        time_pct,
        _get_tolerance(plan, primary_kpi),
        strategy=primary_kpi.progress_strategy if primary_kpi else "level",
    )

    plan.target_achieved = outcome["target_achieved"]

    if save:
        # Save individual KPI current values/flags via db updates to avoid
        # full recursive save while in hooks.  Then save the parent for flags.
        for kpi in plan.kpis:
            kpi.db_update()
        plan.save()

    return {
        "outcome": outcome,
        "execution_progress": execution,
        "time_progress": time_pct,
        "health": health,
        "target_achieved": plan.target_achieved,
    }


def _refresh_single_kpi(kpi, plan, as_of_end):
    meta = get_metric_capability(kpi.metric_key)
    if not meta:
        return

    # Current value: from plan start to as-of date
    try:
        current_result = compute_metric(kpi.metric_key, plan.start_date, as_of_end)
        kpi.current_value = flt(current_result.get("value"))
    except Exception:
        kpi.current_value = 0.0

    # Progress measures based on strategy
    measures = _compute_kpi_measures(kpi, plan, as_of_end)
    for key, value in measures.items():
        setattr(kpi, key, value)

    # Target achieved (non-sticky, computed from current data)
    kpi.target_achieved = target_achieved(
        current=kpi.current_value,
        target=kpi.target_value,
        direction=kpi.direction,
        progress_strategy=kpi.progress_strategy,
        plan_status=plan.status,
    )


def _compute_kpi_measures(kpi, plan, as_of_end):
    strategy = kpi.progress_strategy
    current = flt(kpi.current_value)
    target = flt(kpi.target_value)
    baseline = flt(kpi.effective_baseline)
    time_pct = time_progress(plan.start_date, plan.end_date, as_of_end)

    measures = {
        "final_target_completion_pct": 0.0,
        "pace_attainment_pct": 0.0,
        "cap_utilization_pct": 0.0,
        "remaining_amount": 0.0,
        "consumption_pace_pct": 0.0,
    }

    if strategy == "level":
        progress = level_progress(current, baseline, target, kpi.direction)
        measures["final_target_completion_pct"] = progress
        measures["pace_attainment_pct"] = progress
    elif strategy == "cumulative_growth":
        cm = cumulative_growth_measures(current, target, time_pct)
        measures["final_target_completion_pct"] = cm["final_target_completion_pct"]
        measures["pace_attainment_pct"] = cm["pace_attainment_pct"]
    elif strategy == "cumulative_ceiling":
        cm = cumulative_ceiling_measures(current, target, time_pct)
        measures["cap_utilization_pct"] = cm["cap_utilization_pct"]
        measures["remaining_amount"] = cm["remaining_amount"]
        measures["consumption_pace_pct"] = cm["consumption_pace_pct"]

    return measures


def _compute_outcome(primary_kpi, plan, as_of_end):
    """Return outcome value used for health plus target_achieved flag."""
    if not primary_kpi:
        return {"progress_or_pace_value": 0.0, "target_achieved": False}

    strategy = primary_kpi.progress_strategy
    if strategy == "cumulative_ceiling":
        # Health uses consumption pace; 100 = exactly on expected pace
        progress_or_pace = flt(primary_kpi.consumption_pace_pct)
    else:
        progress_or_pace = flt(primary_kpi.pace_attainment_pct)

    return {
        "progress_or_pace_value": progress_or_pace,
        "target_achieved": bool(primary_kpi.target_achieved),
    }


def _compute_execution_progress(actions):
    non_cancelled = [a for a in actions if a.status != "Cancelled"]
    if not non_cancelled:
        return None
    total_weight = sum(flt(a.weight) for a in non_cancelled)
    if total_weight == 0:
        completed = sum(1 for a in non_cancelled if a.status == "Completed")
        return (completed / len(non_cancelled)) * 100.0
    completed_weight = sum(flt(a.weight) for a in non_cancelled if a.status == "Completed")
    return (completed_weight / total_weight) * 100.0


def _get_tolerance(plan, primary_kpi):
    if primary_kpi and primary_kpi.tolerance_pct:
        return flt(primary_kpi.tolerance_pct)
    settings = frappe.get_single("Decision Center Settings")
    return flt(settings.get("plan_health_tolerance_pct") or 10)


# ── Baseline locking ─────────────────────────────────────────────────────────

def _lock_baselines(plan):
    """Recompute and lock effective baselines at explicit activation."""
    company = _default_company()
    for kpi in plan.kpis:
        strategy = kpi.baseline_strategy
        if strategy == "manual_only":
            kpi.computed_baseline = None
            if kpi.override_baseline is None:
                frappe.throw(
                    frappe._("Baseline is manual-only for metric {0}; please provide an override baseline.").format(kpi.metric_key)
                )
        else:
            # snapshot_at_plan_start requires start_date <= today, already checked
            baseline_info = compute_baseline(
                metric_key=kpi.metric_key,
                strategy=strategy,
                reference_date=plan.start_date,
                plan_start_date=plan.start_date,
                company=company,
            )
            kpi.computed_baseline = flt(baseline_info.get("value"))

        kpi.effective_baseline = kpi.override_baseline if kpi.override_baseline is not None else kpi.computed_baseline
        kpi.db_update()


# ── Checkpoints ──────────────────────────────────────────────────────────────

def _generate_checkpoints(plan):
    # Remove existing checkpoints
    for cp in list(plan.checkpoints):
        plan.remove(cp)

    start = getdate(plan.start_date)
    end = getdate(plan.end_date)
    today = getdate(nowdate())

    current = date(start.year, start.month, 1)
    while current <= end:
        month_end = (current.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        cp_end = min(month_end, end)
        cp_start = max(current, start)
        _add_checkpoint(plan, current.strftime("%Y-%m"), cp_start, cp_end, today)
        # next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)


def _add_checkpoint(plan, month, from_date, to_date, today):
    primary = next((k for k in plan.kpis if k.is_primary), None)
    if not primary:
        return

    cp = plan.append("checkpoints", {})
    cp.month = month
    cp.from_date = from_date
    cp.to_date = to_date

    time_pct = time_progress(plan.start_date, plan.end_date, to_date)
    target = flt(primary.target_value)
    baseline = flt(primary.effective_baseline)
    strategy = primary.progress_strategy

    if strategy == "level":
        # Linear trajectory from baseline to target
        cp.target_value = baseline + (target - baseline) * (time_pct / 100.0)
    elif strategy == "cumulative_growth":
        cp.target_value = target * (time_pct / 100.0)
    elif strategy == "cumulative_ceiling":
        cp.target_value = target * (time_pct / 100.0)

    # Actual value is only computed if the checkpoint period has started
    if today >= from_date:
        try:
            result = compute_metric(primary.metric_key, str(from_date), str(min(to_date, today)))
            cp.actual_value = flt(result.get("value"))
        except Exception:
            cp.actual_value = 0.0
        _update_checkpoint_measures(cp, primary, plan, today)


def _update_checkpoint_measures(cp, primary, plan, as_of_end):
    as_of_end = min(getdate(as_of_end), getdate(cp.to_date))
    current = flt(cp.actual_value)
    target = flt(primary.target_value)
    baseline = flt(primary.effective_baseline)
    time_pct = time_progress(plan.start_date, plan.end_date, as_of_end)
    strategy = primary.progress_strategy

    if strategy == "level":
        progress = level_progress(current, baseline, target, primary.direction)
        cp.final_target_completion_pct = progress
        cp.pace_attainment_pct = progress
        cp.consumption_pace_pct = 0.0
        cp.cap_utilization_pct = 0.0
        cp.remaining_amount = 0.0
        health_value = progress
    elif strategy == "cumulative_growth":
        cm = cumulative_growth_measures(current, target, time_pct)
        cp.final_target_completion_pct = cm["final_target_completion_pct"]
        cp.pace_attainment_pct = cm["pace_attainment_pct"]
        cp.consumption_pace_pct = 0.0
        cp.cap_utilization_pct = 0.0
        cp.remaining_amount = 0.0
        health_value = cm["pace_attainment_pct"]
    elif strategy == "cumulative_ceiling":
        cm = cumulative_ceiling_measures(current, target, time_pct)
        cp.cap_utilization_pct = cm["cap_utilization_pct"]
        cp.remaining_amount = cm["remaining_amount"]
        cp.consumption_pace_pct = cm["consumption_pace_pct"]
        cp.final_target_completion_pct = 0.0
        cp.pace_attainment_pct = 0.0
        health_value = cm["consumption_pace_pct"]

    tolerance = _get_tolerance(plan, primary)
    cp.health = plan_health(health_value, time_pct, tolerance, strategy=strategy)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _default_company():
    return frappe.defaults.get_user_default("Company") or frappe.db.get_value("Company", {}, "name")
