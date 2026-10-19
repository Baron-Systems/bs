# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Decision Center Metric Capability controller.

System-controlled fields are protected from UI/API mutation.
Only code-level patches and explicit whitelisted maintenance functions may change
system_available, formula, calculator identity, baseline_strategy, progress_strategy etc.
"""

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


_PROTECTED_FIELDS = (
    "system_available",
    "formula_description",
    "calculation_module",
    "baseline_strategy",
    "progress_strategy",
    "is_negative_good",
    "requires_snapshot",
    "schema_version",
)


class DecisionCenterMetricCapability(Document):

    def validate(self):
        self._ensure_system_truth_integrity()
        self._ensure_enabled_for_plans_only_when_available()

    def _ensure_system_truth_integrity(self):
        if self.is_new() or frappe.flags.in_patch or frappe.flags.in_import:
            return

        if not self.get_doc_before_save():
            return

        previous = self.get_doc_before_save()
        for fieldname in _PROTECTED_FIELDS:
            if self.get(fieldname) != previous.get(fieldname):
                frappe.throw(
                    frappe._(
                        "Field {0} is system-controlled and cannot be changed through the UI/API. "
                        "Use a code-level patch or maintenance function instead."
                    ).format(frappe.bold(fieldname))
                )

    def _ensure_enabled_for_plans_only_when_available(self):
        if self.enabled_for_plans and not self.system_available:
            frappe.throw(
                frappe._(
                    "Cannot enable '{0}' for plans because it is not system-available."
                ).format(self.metric_key)
            )
