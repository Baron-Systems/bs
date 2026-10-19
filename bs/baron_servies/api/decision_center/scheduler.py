# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Scheduler-only maintenance tasks for Decision Center plans and snapshots.

The scheduler never activates or completes a plan. It only sets the
`scheduler_status` recommendation field and manages monthly snapshots.
"""

from __future__ import unicode_literals

import frappe
from frappe.utils import getdate, now, nowdate

from .snapshot_service import run_scheduler as run_snapshot_scheduler_service


@frappe.whitelist()
def refresh_plan_scheduler_status():
    """Set scheduler_status recommendation based on dates.

    Draft/Scheduled plans: ready_to_start if start_date <= today
    Active plans: ready_to_close if end_date < today
    Cancelled/Completed: always none
    """
    today = getdate(nowdate())

    for plan in frappe.get_all(
        "Decision Center Plan",
        filters={"status": ["in", ["Scheduled", "Active"]]},
        fields=["name", "status", "start_date", "end_date", "scheduler_status"],
    ):
        new_status = "none"
        if plan.status == "Scheduled" and getdate(plan.start_date) <= today:
            new_status = "ready_to_start"
        elif plan.status == "Active" and getdate(plan.end_date) < today:
            new_status = "ready_to_close"

        if new_status != plan.scheduler_status:
            frappe.db.set_value(
                "Decision Center Plan",
                plan.name,
                {
                    "scheduler_status": new_status,
                    "scheduler_status_updated_at": now(),
                },
                update_modified=False,
            )


@frappe.whitelist()
def run_snapshot_scheduler():
    """Generate previous-month snapshot and lock expired snapshots."""
    run_snapshot_scheduler_service()
