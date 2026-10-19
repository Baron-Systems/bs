# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Rules Engine for the Decision Center.

Each rule is a plain Python dict in the ``RULES`` registry.  The engine
iterates through enabled rules and delegates evaluation to the
corresponding playbook function.
"""

from __future__ import unicode_literals

from . import config as cfg
from .playbooks import (
    evaluate_slow_moving_stock,
    evaluate_dead_stock,
    evaluate_low_stock_risk,
    evaluate_over_purchasing,
    evaluate_item_sales_decline,
    evaluate_item_sales_growth,
    evaluate_customer_decline,
    evaluate_customer_stopped,
    evaluate_purchase_price_increase,
    evaluate_total_expense_ratio_high,
    evaluate_expense_category_ratio_high,
    evaluate_expense_category_increase,
    evaluate_expense_anomaly,
)


# ───────────────────────────────────────────────────────────────────────────
# Rule registry
# ───────────────────────────────────────────────────────────────────────────

RULES = [
    {
        "id": "DEAD_STOCK",
        "category": "inventory",
        "title_template": "مخزون راكد — {count} صنف",
        "description": "الكشف عن الأصناف التي لم تُباع خلال فترة المخزون الراكد.",
        "severity": "high",
        "enabled": True,
        "evaluator": evaluate_dead_stock,
    },
    {
        "id": "SLOW_MOVING_STOCK",
        "category": "inventory",
        "title_template": "مخزون بطيء الحركة — {count} صنف",
        "description": "الكشف عن الأصناف ذات الحركة البطيئة مقارنة بحد الأيام المحدد.",
        "severity": "medium",
        "enabled": True,
        "evaluator": evaluate_slow_moving_stock,
    },
    {
        "id": "LOW_STOCK_RISK",
        "category": "inventory",
        "title_template": "خطر نفاد المخزون — {count} صنف",
        "description": "تنبيه عندما يكون المخزون المتاح أقل من الأيام المحددة للنفاد.",
        "severity": "high",
        "enabled": True,
        "evaluator": evaluate_low_stock_risk,
    },
    {
        "id": "OVER_PURCHASING",
        "category": "inventory",
        "title_template": "شراء يفوق الحاجة — {count} صنف",
        "description": "الكشف عن الأصناف التي تم شراؤها بكميات تفوق الاستهلاك المتوقع.",
        "severity": "medium",
        "enabled": True,
        "evaluator": evaluate_over_purchasing,
    },
    {
        "id": "ITEM_SALES_DECLINE",
        "category": "sales",
        "title_template": "تراجع مبيعات — {count} صنف",
        "description": "تنبيه عند انخفاض مبيعات صنف عن الفترة السابقة بنسبة تتجاوز الحد.",
        "severity": "medium",
        "enabled": True,
        "evaluator": evaluate_item_sales_decline,
    },
    {
        "id": "ITEM_SALES_GROWTH",
        "category": "sales",
        "title_template": "نمو مبيعات — {count} صنف",
        "description": "تنبيه عند نمو مبيعات صنف بشكل ملحوظ مقارنة بالفترة السابقة.",
        "severity": "low",
        "enabled": True,
        "evaluator": evaluate_item_sales_growth,
    },
    {
        "id": "CUSTOMER_DECLINE",
        "category": "customers",
        "title_template": "تراجع مشتريات عميل — {count} عميل",
        "description": "تنبيه عند انخفاض مشتريات عميل مقارنة بالفترة السابقة.",
        "severity": "medium",
        "enabled": True,
        "evaluator": evaluate_customer_decline,
    },
    {
        "id": "CUSTOMER_STOPPED",
        "category": "customers",
        "title_template": "عميل توقف عن الشراء — {count} عميل",
        "description": "الكشف عن العملاء الذين توقفوا عن الشراء خلال الفترة الحالية.",
        "severity": "high",
        "enabled": True,
        "evaluator": evaluate_customer_stopped,
    },
    {
        "id": "PURCHASE_PRICE_INCREASE",
        "category": "purchases",
        "title_template": "ارتفاع سعر الشراء — {count} صنف",
        "description": "تنبيه عند ارتفاع سعر شراء صنف عن متوسط أسعار الشراء السابقة.",
        "severity": "medium",
        "enabled": True,
        "evaluator": evaluate_purchase_price_increase,
    },
    {
        "id": "TOTAL_EXPENSE_RATIO_HIGH",
        "category": "expenses",
        "title_template": "نسبة المصاريف الإجمالية مرتفعة",
        "description": "تنبيه عندما ترتفع نسبة المصاريف الإجمالية إلى المبيعات فوق الحد المحدد.",
        "severity": "medium",
        "enabled": True,
        "evaluator": evaluate_total_expense_ratio_high,
    },
    {
        "id": "EXPENSE_CATEGORY_RATIO_HIGH",
        "category": "expenses",
        "title_template": "تصنيف مصاريف يتجاوز نسبة المبيعات",
        "description": "تنبيه عندما يتجاوز تصنيف مصاريف النسبة المحددة من إجمالي المبيعات.",
        "severity": "medium",
        "enabled": True,
        "evaluator": evaluate_expense_category_ratio_high,
    },
    {
        "id": "EXPENSE_CATEGORY_INCREASE",
        "category": "expenses",
        "title_template": "ارتفاع كبير في مصاريف التصنيف",
        "description": "تنبيه عند ارتفاع مصروفات تصنيف معين بنسبة تتجاوز الحد المحدد.",
        "severity": "medium",
        "enabled": True,
        "evaluator": evaluate_expense_category_increase,
    },
    {
        "id": "EXPENSE_ANOMALY",
        "category": "expenses",
        "title_template": "مصاريف غير طبيعية مقارنة بالمتوسط التاريخي",
        "description": "الكشف عن قيم مصروفات شاذة مقارنة بالمتوسط التاريخي لتصنيف المصاريف.",
        "severity": "high",
        "enabled": True,
        "evaluator": evaluate_expense_anomaly,
    },
]


def get_rule(rule_id):
    """Return the rule dict for the given *rule_id*, or ``None``."""
    for r in RULES:
        if r["id"] == rule_id:
            return r
    return None


def evaluate_all_rules(company, from_date, to_date, prev_from, prev_to):
    """Run every enabled rule and return a flat list of Decision dicts."""
    decisions = []
    for rule in RULES:
        if not cfg.get_rule_enabled(rule["id"], default=rule.get("enabled", True)):
            continue
        evaluator = rule["evaluator"]
        results = evaluator(
            company=company,
            from_date=from_date,
            to_date=to_date,
            prev_from=prev_from,
            prev_to=prev_to,
        )
        decisions.extend(results)
    return decisions
