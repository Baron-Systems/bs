# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Seed default Decision Center settings, expense categories, and rule settings.
"""

from __future__ import unicode_literals

import frappe
from frappe.utils import cint


DEFAULT_CATEGORIES = [
    {
        "category_name": "رواتب وموظفين",
        "description": "Salaries, wages, and employee-related expenses",
    },
    {
        "category_name": "إيجارات",
        "description": "Rent and lease payments",
    },
    {
        "category_name": "كهرباء ومياه",
        "description": "Utilities",
    },
    {
        "category_name": "نقل وتوزيع",
        "description": "Transportation, fuel, delivery, and vehicle maintenance",
    },
    {
        "category_name": "تسويق",
        "description": "Marketing and advertising expenses",
    },
    {
        "category_name": "صيانة",
        "description": "General maintenance",
    },
    {
        "category_name": "مصاريف إدارية",
        "description": "Administrative expenses",
    },
    {
        "category_name": "مصاريف تشغيلية",
        "description": "Operating expenses",
    },
    {
        "category_name": "مصاريف مالية",
        "description": "Bank charges, interest, and financial fees",
    },
    {
        "category_name": "أخرى",
        "description": "Other uncategorized expenses",
    },
]

DEFAULT_RULES = [
    {"rule_id": "DEAD_STOCK", "enabled": 1},
    {"rule_id": "SLOW_MOVING_STOCK", "enabled": 1},
    {"rule_id": "LOW_STOCK_RISK", "enabled": 1},
    {"rule_id": "OVER_PURCHASING", "enabled": 1},
    {"rule_id": "ITEM_SALES_DECLINE", "enabled": 1},
    {"rule_id": "ITEM_SALES_GROWTH", "enabled": 1},
    {"rule_id": "CUSTOMER_DECLINE", "enabled": 1},
    {"rule_id": "CUSTOMER_STOPPED", "enabled": 1},
    {"rule_id": "PURCHASE_PRICE_INCREASE", "enabled": 1},
    {"rule_id": "TOTAL_EXPENSE_RATIO_HIGH", "enabled": 1},
    {"rule_id": "EXPENSE_CATEGORY_RATIO_HIGH", "enabled": 1},
    {"rule_id": "EXPENSE_CATEGORY_INCREASE", "enabled": 1},
    {"rule_id": "EXPENSE_ANOMALY", "enabled": 1},
]

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
    "priority_urgent": 80,
    "priority_important": 60,
    "priority_review": 40,
}


def execute():
    create_settings()
    create_categories()


def create_settings():
    if frappe.db.exists("Decision Center Settings", "Decision Center Settings"):
        doc = frappe.get_doc("Decision Center Settings", "Decision Center Settings")
    else:
        doc = frappe.new_doc("Decision Center Settings")
        doc.name = "Decision Center Settings"

    for field, value in DEFAULT_THRESHOLDS.items():
        if not doc.get(field):
            doc.set(field, value)

    existing_rule_ids = {r.rule_id for r in doc.rule_settings}
    for rule in DEFAULT_RULES:
        if rule["rule_id"] in existing_rule_ids:
            continue
        doc.append("rule_settings", rule)

    doc.save(ignore_permissions=True)


def create_categories():
    for cat in DEFAULT_CATEGORIES:
        if frappe.db.exists("Decision Center Expense Category", cat["category_name"]):
            continue
        doc = frappe.new_doc("Decision Center Expense Category")
        doc.category_name = cat["category_name"]
        doc.description = cat["description"]
        doc.enabled = 1
        doc.save(ignore_permissions=True)
