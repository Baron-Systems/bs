# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Idempotent patch: seed missing Decision Center threshold fields on existing
installations without overwriting values that have already been configured.
"""

from __future__ import unicode_literals

import frappe
from frappe.utils import cint, flt

DEFAULT_THRESHOLDS = {
    "slow_moving_days": 90,
    "dead_stock_days": 180,
    "low_stock_days": 7,
    "warning_stock_days": 14,
    "sales_drop_percent": 30,
    "sales_growth_percent": 30,
    "min_sales_baseline": 3,
    "purchase_price_increase_percent": 10,
    "overstock_purchase_ratio": 1.5,
    "customer_drop_percent": 30,
    "customer_inactive_multiplier": 2.0,
    "min_customer_invoices": 3,
    "expense_vs_sales_threshold": 10,
    "expense_increase_threshold": 20,
    "expense_anomaly_threshold": 30,
    "plan_health_tolerance_pct": 10.0,
    "priority_urgent": 80,
    "priority_important": 60,
    "priority_review": 40,
}


def execute():
    if not frappe.db.exists("Decision Center Settings", "Decision Center Settings"):
        return

    doc = frappe.get_doc("Decision Center Settings", "Decision Center Settings")
    meta = doc.meta
    changed = False

    for field, default in DEFAULT_THRESHOLDS.items():
        if not meta.has_field(field):
            continue
        current = doc.get(field)
        if current is None or current == "" or (
            isinstance(current, (int, float)) and current == 0 and default != 0
        ):
            doc.set(field, default)
            changed = True

    if changed:
        doc.save(ignore_permissions=True)
