# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Seed the Decision Center Metric Capability registry from code.

System-controlled fields are set in the patch because the controller prevents
normal UI/API mutation of formula / availability / strategy fields.
"""

from __future__ import unicode_literals

import frappe

from bs.baron_servies.api.decision_center.registry import METRIC_REGISTRY


def execute():
    for metric_key, meta in METRIC_REGISTRY.items():
        name = metric_key
        if frappe.db.exists("Decision Center Metric Capability", name):
            doc = frappe.get_doc("Decision Center Metric Capability", name)
        else:
            doc = frappe.new_doc("Decision Center Metric Capability")
            doc.metric_key = metric_key

        doc.metric_label_ar = meta.get("metric_label_ar") or ""
        doc.metric_label_en = meta.get("metric_label_en") or ""
        doc.category = meta.get("category")
        doc.unit = meta.get("unit")
        doc.system_available = 1 if meta.get("system_available") else 0
        doc.enabled_for_plans = 1 if meta.get("enabled_for_plans") else 0
        doc.unavailable_reason = meta.get("unavailable_reason") or ""
        doc.formula_description = meta.get("formula_description") or ""
        doc.calculation_module = meta.get("calculation_module") or ""
        doc.baseline_strategy = meta.get("baseline_strategy") or ""
        doc.progress_strategy = meta.get("progress_strategy") or ""
        doc.is_negative_good = 1 if meta.get("is_negative_good") else 0
        doc.requires_snapshot = 1 if meta.get("requires_snapshot") else 0
        doc.schema_version = meta.get("schema_version") or ""

        if doc.is_new():
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)
