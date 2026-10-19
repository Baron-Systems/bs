# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, now


class DecisionCenterPlan(Document):

    def validate(self):
        self._validate_dates()
        self._validate_primary_kpi()
        self._validate_status_transition()
        self._validate_active_constraints()
        self._validate_baseline_override()

    def before_insert(self):
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_at:
            self.created_at = now()

    def before_save(self):
        self._update_effective_baselines()

    def _validate_dates(self):
        if self.end_date and self.start_date and getdate(self.end_date) < getdate(self.start_date):
            frappe.throw(frappe._("End Date must be on or after Start Date"))

    def _validate_primary_kpi(self):
        if not self.kpis:
            return
        primary_count = sum(1 for kpi in self.kpis if kpi.is_primary)
        if primary_count != 1:
            frappe.throw(frappe._("Exactly one KPI must be marked as primary. Found {0}.").format(primary_count))

    def _validate_status_transition(self):
        if self.is_new():
            return
        previous = self.get_doc_before_save()
        if not previous:
            return
        allowed = {
            "Draft": ["Draft", "Scheduled", "Cancelled"],
            "Scheduled": ["Scheduled", "Active", "Cancelled"],
            "Active": ["Active", "Completed", "Cancelled"],
            "Completed": ["Completed"],
            "Cancelled": ["Cancelled"],
        }
        if self.status not in allowed.get(previous.status, []):
            frappe.throw(
                frappe._("Invalid status transition from {0} to {1}").format(previous.status, self.status)
            )

    def _validate_active_constraints(self):
        if self.status != "Active":
            return
        if getdate(self.start_date) > getdate(nowdate()):
            frappe.throw(frappe._("An Active plan cannot start before its Start Date."))
        active_plans = frappe.get_all(
            "Decision Center Plan",
            filters={"status": "Active", "name": ("!=", self.name)},
            pluck="name",
            limit_page_length=1,
        )
        if active_plans:
            frappe.throw(
                frappe._("Only one Active plan is allowed. Plan '{0}' is already Active.").format(active_plans[0])
            )

    def _validate_baseline_override(self):
        for kpi in self.kpis:
            if kpi.override_baseline and not kpi.override_reason:
                frappe.throw(frappe._("Override reason is required when overriding baseline for metric {0}").format(kpi.metric_key))

    def _update_effective_baselines(self):
        for kpi in self.kpis:
            kpi.effective_baseline = kpi.override_baseline if kpi.override_baseline is not None else kpi.computed_baseline

    def on_update(self):
        if self.status == "Active" and not self.activated_at:
            self.db_set("activated_at", now())
        if self.status in ("Completed", "Cancelled") and self.scheduler_status != "none":
            self.db_set("scheduler_status", "none")
