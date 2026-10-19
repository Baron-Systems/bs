# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Centralized configuration for the Decision Center.

Hard-coded values are defaults.  Live thresholds are loaded from the
``Decision Center Settings`` single DocType when available.
"""

from __future__ import unicode_literals

import frappe
from frappe.utils import cint, flt

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
_DEFAULTS = {
    # Stock thresholds
    "SLOW_MOVING_DAYS": 90,
    "DEAD_STOCK_DAYS": 180,
    "LOW_STOCK_DAYS": 7,
    "WARNING_STOCK_DAYS": 14,
    # Sales / Purchase thresholds
    "SALES_DROP_PERCENT": 30,
    "SALES_GROWTH_PERCENT": 30,
    "PURCHASE_PRICE_INCREASE_PERCENT": 10,
    "OVERSTOCK_PURCHASE_RATIO": 1.5,
    # Customer thresholds
    "CUSTOMER_DROP_PERCENT": 30,
    "CUSTOMER_INACTIVE_MULTIPLIER": 2.0,
    # Baseline minimums (prevent false positives on thin data)
    "MIN_SALES_BASELINE": 3,
    "MIN_CUSTOMER_INVOICES": 3,
    # Priority score thresholds
    "PRIORITY_URGENT": 80,
    "PRIORITY_IMPORTANT": 60,
    "PRIORITY_REVIEW": 40,
    # Decision ID hash length
    "DECISION_HASH_LENGTH": 12,
    # Expense thresholds
    "EXPENSE_VS_SALES_THRESHOLD": 10,
    "EXPENSE_INCREASE_THRESHOLD": 20,
    "EXPENSE_ANOMALY_THRESHOLD": 30,
    # Plan settings
    "PLAN_HEALTH_TOLERANCE_PCT": 10.0,
}

# Expose defaults directly for backward compatibility
for _k, _v in _DEFAULTS.items():
    globals()[_k] = _v


# ---------------------------------------------------------------------------
# Dynamic loader
# ---------------------------------------------------------------------------

def get_decision_center_settings():
    """Return the Decision Center Settings document or None."""
    if not frappe.db.table_exists("Decision Center Settings"):
        return None
    if not frappe.db.exists("Decision Center Settings", "Decision Center Settings"):
        return None
    return frappe.get_doc("Decision Center Settings", "Decision Center Settings")


def get_threshold(key):
    """Return live threshold from settings, falling back to hard-coded default."""
    doc = get_decision_center_settings()
    if doc:
        # Map constant name -> snake_case field name
        field = key.lower()
        if doc.has_field(field):
            value = doc.get(field)
            if value is not None:
                if isinstance(_DEFAULTS[key], int):
                    return cint(value)
                if isinstance(_DEFAULTS[key], float):
                    return flt(value)
                return value
    return _DEFAULTS[key]


def get_rule_enabled(rule_id, default=True):
    """Return whether a decision rule is enabled in settings."""
    doc = get_decision_center_settings()
    if not doc:
        return default
    for row in doc.rule_settings:
        if row.rule_id == rule_id:
            return bool(row.enabled)
    return default
