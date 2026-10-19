# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Playbook implementations for the Decision Center.

Each ``evaluate_*`` function receives the standard kwargs
(company, from_date, to_date, prev_from, prev_to) and returns a
list of Decision dicts.

Key invariants
--------------
- Returns are already negative in ERPNext → use ``SUM(qty)`` directly.
- Bin data is the **current** stock snapshot.
- Sales velocity lookbacks are calculated from ``to_date`` backwards (today).
- Decision IDs are deterministic.
"""

from __future__ import unicode_literals

import hashlib

from frappe.utils import flt, getdate, nowdate, date_diff

from . import config as cfg
from .metrics import (
    get_item_stock,
    get_item_sales,
    get_item_purchases,
    get_customer_sales,
    get_customer_last_purchase_dates,
    get_customer_purchase_gaps,
)
from .expenses import (
    get_expense_metrics,
    get_expense_anomaly_baseline,
    get_enabled_expense_accounts,
)
from .priority import compute_score


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _decision_id(rule_id, entity_type, keys):
    """Build a deterministic decision ID."""
    raw = f"{rule_id}|{entity_type}|{'|'.join(sorted(str(k) for k in keys))}"
    h = hashlib.md5(raw.encode("utf-8")).hexdigest()[:cfg.get_threshold('DECISION_HASH_LENGTH')]
    return f"{rule_id}-{entity_type}-{h}"


def _make_decision(rule_id, category, severity, entity_type, entity_ids,
                   title, summary, evidence, recommendation, action_route,
                   impact_value=0, change_pct=0, extra=None):
    """Build and score a Decision dict."""
    d = {
        "id": _decision_id(rule_id, entity_type, entity_ids),
        "rule_id": rule_id,
        "category": category,
        "severity": severity,
        "title": title,
        "summary": summary,
        "evidence": evidence,
        "recommendation": recommendation,
        "entity_type": entity_type,
        "entity_ids": entity_ids,
        "action_route": action_route,
        "impact_value": flt(impact_value),
        "change_pct": flt(change_pct),
    }
    if extra:
        d["extra"] = extra
    return compute_score(d)


# ═══════════════════════════════════════════════════════════════════════════
# PB1 — Slow Moving Stock
# stock > 0, net_sales > 0, days_of_stock > SLOW_MOVING_DAYS
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_slow_moving_stock(company, from_date, to_date, **_kw):
    stock = {r["item_code"]: r for r in get_item_stock(company)}
    if not stock:
        return []

    # Use a long lookback for velocity: SLOW_MOVING_DAYS from today
    today = getdate(nowdate())
    lookback_from = today - __import__("datetime").timedelta(days=cfg.get_threshold('SLOW_MOVING_DAYS'))
    sales_map = {r["item_code"]: r for r in get_item_sales(company, lookback_from, today)}

    flagged = []
    for item_code, s in stock.items():
        actual_qty = flt(s.get("actual_qty"))
        if actual_qty <= 0:
            continue

        sale = sales_map.get(item_code)
        if not sale or flt(sale.get("net_qty")) <= 0:
            # No sales → this is Dead Stock territory, not Slow Moving
            continue

        avg_daily = flt(sale.get("avg_daily_qty"))
        if avg_daily <= 0:
            continue

        days_of_stock = actual_qty / avg_daily
        if days_of_stock > cfg.get_threshold('SLOW_MOVING_DAYS'):
            flagged.append({
                "item_code": item_code,
                "item_name": s.get("item_name", item_code),
                "actual_qty": actual_qty,
                "stock_value": flt(s.get("stock_value")),
                "avg_daily_sales": avg_daily,
                "days_of_stock": round(days_of_stock, 1),
            })

    if not flagged:
        return []

    total_value = sum(f["stock_value"] for f in flagged)
    entity_ids = [f["item_code"] for f in flagged]

    return [_make_decision(
        rule_id="SLOW_MOVING_STOCK",
        category="inventory",
        severity="medium",
        entity_type="Item",
        entity_ids=entity_ids,
        title=f"مخزون بطيء الحركة — {len(flagged)} صنف",
        summary=f"يوجد {len(flagged)} صنف لديه مبيعات لكن المخزون الحالي يكفي لأكثر من {cfg.get_threshold('SLOW_MOVING_DAYS')} يوماً",
        evidence=[
            {"label": "عدد الأصناف", "value": len(flagged)},
            {"label": "إجمالي قيمة المخزون البطيء", "value": total_value, "format": "currency"},
        ],
        recommendation="مراجعة كميات الشراء لهذه الأصناف وتقليلها",
        action_route="/app/query-report/Stock Balance",
        impact_value=total_value,
        extra={"items": flagged[:50]},
    )]


# ═══════════════════════════════════════════════════════════════════════════
# PB2 — Dead Stock
# stock > 0, zero net sales for DEAD_STOCK_DAYS
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_dead_stock(company, from_date, to_date, **_kw):
    stock = {r["item_code"]: r for r in get_item_stock(company)}
    if not stock:
        return []

    today = getdate(nowdate())
    lookback_from = today - __import__("datetime").timedelta(days=cfg.get_threshold('DEAD_STOCK_DAYS'))
    sales_map = {r["item_code"]: r for r in get_item_sales(company, lookback_from, today)}

    flagged = []
    for item_code, s in stock.items():
        actual_qty = flt(s.get("actual_qty"))
        if actual_qty <= 0:
            continue

        sale = sales_map.get(item_code)
        net_qty = flt(sale.get("net_qty")) if sale else 0

        if net_qty <= 0:
            flagged.append({
                "item_code": item_code,
                "item_name": s.get("item_name", item_code),
                "actual_qty": actual_qty,
                "stock_value": flt(s.get("stock_value")),
                "days_without_sales": cfg.get_threshold('DEAD_STOCK_DAYS'),
            })

    if not flagged:
        return []

    total_value = sum(f["stock_value"] for f in flagged)
    entity_ids = [f["item_code"] for f in flagged]

    return [_make_decision(
        rule_id="DEAD_STOCK",
        category="inventory",
        severity="high",
        entity_type="Item",
        entity_ids=entity_ids,
        title=f"مخزون راكد — {len(flagged)} صنف",
        summary=f"يوجد {len(flagged)} صنفاً بمخزون موجود ولا توجد أي مبيعات خلال {cfg.get_threshold('DEAD_STOCK_DAYS')} يوماً",
        evidence=[
            {"label": "عدد الأصناف", "value": len(flagged)},
            {"label": "إجمالي قيمة المخزون الراكد", "value": total_value, "format": "currency"},
            {"label": "فترة بدون مبيعات", "value": f"{cfg.get_threshold('DEAD_STOCK_DAYS')} يوم"},
        ],
        recommendation="مراجعة هذه الأصناف — إيقاف الشراء أو تصفية المخزون",
        action_route="/app/query-report/Stock Balance",
        impact_value=total_value,
        extra={"items": flagged[:50]},
    )]


# ═══════════════════════════════════════════════════════════════════════════
# PB3 — Low Stock Risk
# avg_daily_sales > 0, days_of_stock < LOW_STOCK_DAYS / WARNING_STOCK_DAYS
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_low_stock_risk(company, from_date, to_date, **_kw):
    stock = {r["item_code"]: r for r in get_item_stock(company)}
    if not stock:
        return []

    # Use last 30 days for velocity
    today = getdate(nowdate())
    lookback_from = today - __import__("datetime").timedelta(days=30)
    sales_map = {r["item_code"]: r for r in get_item_sales(company, lookback_from, today)}

    urgent = []
    warning = []

    for item_code, s in stock.items():
        actual_qty = flt(s.get("actual_qty"))
        if actual_qty <= 0:
            continue

        sale = sales_map.get(item_code)
        if not sale:
            continue
        avg_daily = flt(sale.get("avg_daily_qty"))
        if avg_daily <= 0:
            continue

        days_of_stock = actual_qty / avg_daily

        entry = {
            "item_code": item_code,
            "item_name": s.get("item_name", item_code),
            "actual_qty": actual_qty,
            "stock_value": flt(s.get("stock_value")),
            "avg_daily_sales": round(avg_daily, 2),
            "days_of_stock": round(days_of_stock, 1),
        }

        if days_of_stock < cfg.get_threshold('LOW_STOCK_DAYS'):
            urgent.append(entry)
        elif days_of_stock < cfg.get_threshold('WARNING_STOCK_DAYS'):
            warning.append(entry)

    decisions = []

    if urgent:
        total_val = sum(f["stock_value"] for f in urgent)
        ids = [f["item_code"] for f in urgent]
        decisions.append(_make_decision(
            rule_id="LOW_STOCK_RISK",
            category="inventory",
            severity="high",
            entity_type="Item",
            entity_ids=ids,
            title=f"خطر نفاد مخزون عاجل — {len(urgent)} صنف",
            summary=f"{len(urgent)} صنف يكفي مخزونه لأقل من {cfg.get_threshold('LOW_STOCK_DAYS')} أيام حسب معدل البيع الحالي",
            evidence=[
                {"label": "عدد الأصناف", "value": len(urgent)},
                {"label": "أقل أيام مخزون", "value": min(f["days_of_stock"] for f in urgent)},
            ],
            recommendation="طلب شراء عاجل لهذه الأصناف",
            action_route="/app/item",
            impact_value=total_val,
            extra={"items": urgent[:50]},
        ))

    if warning:
        total_val = sum(f["stock_value"] for f in warning)
        ids = [f["item_code"] for f in warning]
        decisions.append(_make_decision(
            rule_id="LOW_STOCK_RISK",
            category="inventory",
            severity="medium",
            entity_type="Item",
            entity_ids=[f"warn-{i}" for i in ids],
            title=f"تنبيه مخزون منخفض — {len(warning)} صنف",
            summary=f"{len(warning)} صنف يكفي مخزونه لأقل من {cfg.get_threshold('WARNING_STOCK_DAYS')} يوماً",
            evidence=[
                {"label": "عدد الأصناف", "value": len(warning)},
            ],
            recommendation="التخطيط لشراء هذه الأصناف قريباً",
            action_route="/app/item",
            impact_value=total_val,
            extra={"items": warning[:50]},
        ))

    return decisions


# ═══════════════════════════════════════════════════════════════════════════
# PB4 — Over-purchasing
# purchased_qty > sold_qty × OVERSTOCK_PURCHASE_RATIO in the period
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_over_purchasing(company, from_date, to_date, **_kw):
    sales_map = {r["item_code"]: r for r in get_item_sales(company, from_date, to_date)}
    purchases = get_item_purchases(company, from_date, to_date)
    stock_map = {r["item_code"]: r for r in get_item_stock(company)}

    flagged = []
    for p in purchases:
        item_code = p["item_code"]
        purchased_qty = flt(p.get("net_qty"))
        if purchased_qty <= 0:
            continue

        sold_qty = flt(sales_map.get(item_code, {}).get("net_qty", 0))
        threshold = max(sold_qty * cfg.get_threshold('OVERSTOCK_PURCHASE_RATIO'), 1)

        if purchased_qty > threshold:
            s = stock_map.get(item_code, {})
            sv = flt(s.get("stock_value"))
            aq = flt(s.get("actual_qty"))
            # Skip items with negative stock (over-issued / data issue)
            if aq < 0 or sv < 0:
                continue
            flagged.append({
                "item_code": item_code,
                "item_name": p.get("item_name", item_code),
                "purchased_qty": purchased_qty,
                "sold_qty": sold_qty,
                "current_stock": aq,
                "stock_value": sv,
                "ratio": round(purchased_qty / max(sold_qty, 0.01), 1),
            })

    if not flagged:
        return []

    total_value = sum(f["stock_value"] for f in flagged)
    entity_ids = [f["item_code"] for f in flagged]

    return [_make_decision(
        rule_id="OVER_PURCHASING",
        category="inventory",
        severity="medium",
        entity_type="Item",
        entity_ids=entity_ids,
        title=f"شراء يفوق الحاجة — {len(flagged)} صنف",
        summary=f"{len(flagged)} صنف تم شراؤه بكمية تفوق المبيعات بنسبة {cfg.get_threshold('OVERSTOCK_PURCHASE_RATIO')}x أو أكثر خلال الفترة",
        evidence=[
            {"label": "عدد الأصناف", "value": len(flagged)},
            {"label": "إجمالي قيمة المخزون الحالي", "value": total_value, "format": "currency"},
        ],
        recommendation="مراجعة سياسة الشراء لهذه الأصناف",
        action_route="/app/query-report/Stock Balance",
        impact_value=total_value,
        extra={"items": flagged[:50]},
    )]


# ═══════════════════════════════════════════════════════════════════════════
# PB5 — Item Sales Decline
# current qty < prev qty by > SALES_DROP_PERCENT, baseline >= MIN_SALES_BASELINE
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_item_sales_decline(company, from_date, to_date, prev_from, prev_to, **_kw):
    current = {r["item_code"]: r for r in get_item_sales(company, from_date, to_date)}
    previous = {r["item_code"]: r for r in get_item_sales(company, prev_from, prev_to)}

    flagged = []
    for item_code, prev in previous.items():
        prev_qty = flt(prev.get("net_qty"))
        if prev_qty < cfg.get_threshold('MIN_SALES_BASELINE'):
            continue

        curr = current.get(item_code, {})
        curr_qty = flt(curr.get("net_qty", 0))

        if prev_qty > 0:
            drop_pct = ((prev_qty - curr_qty) / prev_qty) * 100
            # Cap at 100% — returns exceeding sales is still a full decline
            drop_pct = min(drop_pct, 100.0)
        else:
            continue

        if drop_pct >= cfg.get_threshold('SALES_DROP_PERCENT'):
            flagged.append({
                "item_code": item_code,
                "item_name": prev.get("item_name", item_code),
                "prev_qty": prev_qty,
                "current_qty": curr_qty,
                "drop_pct": round(drop_pct, 1),
                "prev_amount": flt(prev.get("net_amount")),
                "current_amount": flt(curr.get("net_amount", 0)),
            })

    if not flagged:
        return []

    flagged.sort(key=lambda x: x["drop_pct"], reverse=True)
    lost_amount = max(sum(f["prev_amount"] - f["current_amount"] for f in flagged), 0)
    entity_ids = [f["item_code"] for f in flagged]

    return [_make_decision(
        rule_id="ITEM_SALES_DECLINE",
        category="sales",
        severity="medium",
        entity_type="Item",
        entity_ids=entity_ids,
        title=f"تراجع مبيعات — {len(flagged)} صنف",
        summary=f"{len(flagged)} صنف انخفضت مبيعاته بأكثر من {cfg.get_threshold('SALES_DROP_PERCENT')}% مقارنة بالفترة السابقة",
        evidence=[
            {"label": "عدد الأصناف المتراجعة", "value": len(flagged)},
            {"label": "إجمالي الخسارة في المبيعات", "value": round(lost_amount, 2), "format": "currency"},
            {"label": "أكبر نسبة تراجع", "value": f"{flagged[0]['drop_pct']}%"},
        ],
        recommendation="مراجعة أسباب التراجع — التسعير، التوفر، المنافسة",
        action_route="/app/item",
        impact_value=lost_amount,
        change_pct=-flagged[0]["drop_pct"],
        extra={"items": flagged[:50]},
    )]


# ═══════════════════════════════════════════════════════════════════════════
# PB6 — Item Sales Growth
# current qty > prev qty by > SALES_GROWTH_PERCENT, baseline >= MIN_SALES_BASELINE
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_item_sales_growth(company, from_date, to_date, prev_from, prev_to, **_kw):
    current = {r["item_code"]: r for r in get_item_sales(company, from_date, to_date)}
    previous = {r["item_code"]: r for r in get_item_sales(company, prev_from, prev_to)}

    flagged = []
    for item_code, curr in current.items():
        curr_qty = flt(curr.get("net_qty"))
        if curr_qty < cfg.get_threshold('MIN_SALES_BASELINE'):
            continue

        prev = previous.get(item_code, {})
        prev_qty = flt(prev.get("net_qty", 0))

        if prev_qty < cfg.get_threshold('MIN_SALES_BASELINE'):
            continue

        if prev_qty > 0:
            growth_pct = ((curr_qty - prev_qty) / prev_qty) * 100
        else:
            continue

        if growth_pct >= cfg.get_threshold('SALES_GROWTH_PERCENT'):
            flagged.append({
                "item_code": item_code,
                "item_name": curr.get("item_name", item_code),
                "prev_qty": prev_qty,
                "current_qty": curr_qty,
                "growth_pct": round(growth_pct, 1),
                "current_amount": flt(curr.get("net_amount")),
            })

    if not flagged:
        return []

    flagged.sort(key=lambda x: x["growth_pct"], reverse=True)
    total_amount = sum(f["current_amount"] for f in flagged)
    entity_ids = [f["item_code"] for f in flagged]

    return [_make_decision(
        rule_id="ITEM_SALES_GROWTH",
        category="sales",
        severity="low",
        entity_type="Item",
        entity_ids=entity_ids,
        title=f"نمو مبيعات — {len(flagged)} صنف",
        summary=f"{len(flagged)} صنف نمت مبيعاته بأكثر من {cfg.get_threshold('SALES_GROWTH_PERCENT')}% مقارنة بالفترة السابقة",
        evidence=[
            {"label": "عدد الأصناف النامية", "value": len(flagged)},
            {"label": "إجمالي مبيعات الأصناف النامية", "value": total_amount, "format": "currency"},
            {"label": "أكبر نسبة نمو", "value": f"{flagged[0]['growth_pct']}%"},
        ],
        recommendation="فرصة — ضمان توفر المخزون الكافي لهذه الأصناف",
        action_route="/app/item",
        impact_value=total_amount,
        change_pct=flagged[0]["growth_pct"],
        extra={"items": flagged[:50]},
    )]


# ═══════════════════════════════════════════════════════════════════════════
# PB7 — Customer Decline
# current < prev by > CUSTOMER_DROP_PERCENT, >= MIN_CUSTOMER_INVOICES historical
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_customer_decline(company, from_date, to_date, prev_from, prev_to, **_kw):
    current = {r["customer"]: r for r in get_customer_sales(company, from_date, to_date)}
    previous = {r["customer"]: r for r in get_customer_sales(company, prev_from, prev_to)}

    flagged = []
    for customer, prev in previous.items():
        prev_total = flt(prev.get("net_total"))
        prev_invoices = int(prev.get("invoice_count", 0))

        if prev_invoices < cfg.get_threshold('MIN_CUSTOMER_INVOICES'):
            continue
        if prev_total <= 0:
            continue

        curr = current.get(customer, {})
        curr_total = flt(curr.get("net_total", 0))

        drop_pct = ((prev_total - curr_total) / prev_total) * 100
        if drop_pct >= cfg.get_threshold('CUSTOMER_DROP_PERCENT'):
            flagged.append({
                "customer": customer,
                "customer_name": prev.get("customer_name", customer),
                "prev_total": prev_total,
                "current_total": curr_total,
                "drop_pct": round(drop_pct, 1),
            })

    if not flagged:
        return []

    flagged.sort(key=lambda x: x["drop_pct"], reverse=True)
    lost = sum(f["prev_total"] - f["current_total"] for f in flagged)
    entity_ids = [f["customer"] for f in flagged]

    return [_make_decision(
        rule_id="CUSTOMER_DECLINE",
        category="customers",
        severity="medium",
        entity_type="Customer",
        entity_ids=entity_ids,
        title=f"تراجع مشتريات عميل — {len(flagged)} عميل",
        summary=f"{len(flagged)} عميل انخفضت مشترياته بأكثر من {cfg.get_threshold('CUSTOMER_DROP_PERCENT')}%",
        evidence=[
            {"label": "عدد العملاء المتراجعين", "value": len(flagged)},
            {"label": "إجمالي الانخفاض في المبيعات", "value": lost, "format": "currency"},
        ],
        recommendation="التواصل مع هؤلاء العملاء لمعرفة السبب",
        action_route="/app/customer",
        impact_value=lost,
        change_pct=-flagged[0]["drop_pct"],
        extra={"customers": flagged[:50]},
    )]


# ═══════════════════════════════════════════════════════════════════════════
# PB8 — Customer Stopped Buying
# was active (>= MIN_CUSTOMER_INVOICES), gap > avg_gap × CUSTOMER_INACTIVE_MULTIPLIER
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_customer_stopped(company, from_date, to_date, **_kw):
    today = getdate(nowdate())
    customers = get_customer_last_purchase_dates(company)

    # Pre-compute average gaps in a single batch query
    avg_gaps = _batch_customer_avg_gaps(company, customers)

    flagged = []
    for c in customers:
        total_invoices = int(c.get("total_invoices", 0))
        if total_invoices < cfg.get_threshold('MIN_CUSTOMER_INVOICES'):
            continue

        last_date = getdate(c.get("last_date"))
        days_since = date_diff(today, last_date)

        avg_gap = avg_gaps.get(c["customer"])
        if avg_gap is None or avg_gap <= 0:
            continue

        threshold = avg_gap * cfg.get_threshold('CUSTOMER_INACTIVE_MULTIPLIER')
        if days_since > threshold:
            flagged.append({
                "customer": c["customer"],
                "total_invoices": total_invoices,
                "last_purchase_date": str(last_date),
                "days_since_last": days_since,
                "avg_gap_days": round(avg_gap, 1),
                "threshold_days": round(threshold, 1),
            })

    if not flagged:
        return []

    flagged.sort(key=lambda x: x["days_since_last"], reverse=True)
    entity_ids = [f["customer"] for f in flagged]

    return [_make_decision(
        rule_id="CUSTOMER_STOPPED",
        category="customers",
        severity="high",
        entity_type="Customer",
        entity_ids=entity_ids,
        title=f"عميل توقف عن الشراء — {len(flagged)} عميل",
        summary=f"{len(flagged)} عميل منتظم توقف عن الشراء لفترة تفوق المعتاد",
        evidence=[
            {"label": "عدد العملاء", "value": len(flagged)},
            {"label": "أطول فترة بدون شراء", "value": f"{flagged[0]['days_since_last']} يوم"},
        ],
        recommendation="التواصل مع هؤلاء العملاء فوراً",
        action_route="/app/customer",
        impact_value=flt(_estimate_stopped_customer_value(company, flagged)),
        extra={"customers": flagged[:50]},
    )]


# ═══════════════════════════════════════════════════════════════════════════
# PB9 — Purchase Price Increase
# avg rate up > PURCHASE_PRICE_INCREASE_PERCENT vs previous period
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_purchase_price_increase(company, from_date, to_date, prev_from, prev_to, **_kw):
    current = {r["item_code"]: r for r in get_item_purchases(company, from_date, to_date)}
    previous = {r["item_code"]: r for r in get_item_purchases(company, prev_from, prev_to)}

    flagged = []
    for item_code, curr in current.items():
        curr_rate = flt(curr.get("avg_rate"))
        if curr_rate <= 0:
            continue

        prev = previous.get(item_code)
        if not prev:
            continue
        prev_rate = flt(prev.get("avg_rate"))
        if prev_rate <= 0:
            continue

        increase_pct = ((curr_rate - prev_rate) / prev_rate) * 100
        if increase_pct >= cfg.get_threshold('PURCHASE_PRICE_INCREASE_PERCENT'):
            flagged.append({
                "item_code": item_code,
                "item_name": curr.get("item_name", item_code),
                "prev_rate": round(prev_rate, 2),
                "current_rate": round(curr_rate, 2),
                "increase_pct": round(increase_pct, 1),
                "current_amount": flt(curr.get("net_amount")),
            })

    if not flagged:
        return []

    flagged.sort(key=lambda x: x["increase_pct"], reverse=True)
    total_amount = sum(f["current_amount"] for f in flagged)
    entity_ids = [f["item_code"] for f in flagged]

    return [_make_decision(
        rule_id="PURCHASE_PRICE_INCREASE",
        category="purchases",
        severity="medium",
        entity_type="Item",
        entity_ids=entity_ids,
        title=f"ارتفاع سعر الشراء — {len(flagged)} صنف",
        summary=f"{len(flagged)} صنف ارتفع سعر شرائه بأكثر من {cfg.get_threshold('PURCHASE_PRICE_INCREASE_PERCENT')}%",
        evidence=[
            {"label": "عدد الأصناف", "value": len(flagged)},
            {"label": "أكبر نسبة ارتفاع", "value": f"{flagged[0]['increase_pct']}%"},
            {"label": "إجمالي المشتريات المتأثرة", "value": total_amount, "format": "currency"},
        ],
        recommendation="التفاوض مع الموردين أو البحث عن بدائل",
        action_route="/app/item",
        impact_value=total_amount,
        change_pct=flagged[0]["increase_pct"],
        extra={"items": flagged[:50]},
    )]


# ═══════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════

def _batch_customer_avg_gaps(company, customers):
    """Compute average purchase gap for multiple customers in a single query.

    Returns dict {customer: avg_gap_days}.  Uses the standard deviation of
    posting dates to compute average inter-purchase intervals efficiently.
    """
    import frappe as _frappe

    eligible = [c["customer"] for c in customers
                if int(c.get("total_invoices", 0)) >= cfg.get_threshold('MIN_CUSTOMER_INVOICES')]

    if not eligible:
        return {}

    # Get all posting dates per customer in one query
    rows = _frappe.db.sql("""
        SELECT customer, posting_date
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND is_return = 0
          AND company = %(company)s
          AND customer IN %(customers)s
        ORDER BY customer, posting_date ASC
    """, {"company": company, "customers": eligible}, as_dict=True)

    # Group by customer
    from collections import defaultdict
    dates_by_cust = defaultdict(list)
    for r in rows:
        dates_by_cust[r["customer"]].append(getdate(r["posting_date"]))

    result = {}
    for cust, dates in dates_by_cust.items():
        if len(dates) < 2:
            continue
        gaps = []
        for i in range(1, len(dates)):
            g = date_diff(dates[i], dates[i - 1])
            if g > 0:
                gaps.append(g)
        if gaps:
            result[cust] = flt(sum(gaps) / len(gaps))

    return result


def _estimate_stopped_customer_value(company, flagged_customers):
    """Estimate the annual value at risk from stopped customers.

    Uses a simple lookback: sum of last 365 days of sales for these customers.
    """
    import frappe as _frappe
    import datetime

    if not flagged_customers:
        return 0

    customer_ids = [f["customer"] for f in flagged_customers]
    today = getdate(nowdate())
    year_ago = today - datetime.timedelta(days=365)

    row = _frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0) AS total
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND company = %(company)s
          AND customer IN %(customers)s
          AND posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, {"company": company, "customers": customer_ids,
          "from_date": year_ago, "to_date": today}, as_dict=True)

    return flt(row[0].total) if row else 0


# ═══════════════════════════════════════════════════════════════════════════
# PB — Expense Analysis Decisions
# ═══════════════════════════════════════════════════════════════════════════


def evaluate_total_expense_ratio_high(company, from_date, to_date, prev_from, prev_to, **_kw):
    """Trigger when total expenses exceed the configured threshold of net sales."""
    from .metrics import get_sales_metrics

    expense = get_expense_metrics(company, from_date, to_date, prev_from, prev_to)
    sales = get_sales_metrics(company, from_date, to_date, prev_from, prev_to)
    total = flt(expense.get("total"))
    net_sales = flt(sales.get("total"))

    if net_sales <= 0:
        return []

    threshold = cfg.get_threshold("EXPENSE_VS_SALES_THRESHOLD")
    ratio = (total / net_sales) * 100 if net_sales else 0
    if ratio <= threshold:
        return []

    return [_make_decision(
        rule_id="TOTAL_EXPENSE_RATIO_HIGH",
        category="expenses",
        severity="medium",
        entity_type="Expense",
        entity_ids=["total_expenses"],
        title="نسبة المصاريف الإجمالية مرتفعة",
        summary=f"إجمالي المصاريف يمثل {ratio:.1f}% من المبيعات (الحد المسموح: {threshold}%)",
        evidence=[
            {"label": "إجمالي المصاريف", "value": total, "format": "currency"},
            {"label": "المبيعات الصافية", "value": net_sales, "format": "currency"},
            {"label": "النسبة", "value": f"{ratio:.1f}%"},
        ],
        recommendation="مراجعة بنود المصاريف الرئيسية والبحث عن فرص للتوفير",
        action_route="/app/decision-center-expense-category",
        impact_value=total,
        change_pct=ratio,
    )]


def evaluate_expense_category_ratio_high(company, from_date, to_date, prev_from, prev_to, **_kw):
    """Trigger when an individual expense category exceeds its max % of sales."""
    from .metrics import get_sales_metrics

    expense = get_expense_metrics(company, from_date, to_date, prev_from, prev_to)
    sales = get_sales_metrics(company, from_date, to_date, prev_from, prev_to)
    net_sales = flt(sales.get("total"))
    if net_sales <= 0:
        return []

    flagged = []
    for cat in expense.get("categories", []):
        max_pct = flt(cat.get("max_percent_of_sales"))
        if not max_pct:
            continue
        current = flt(cat.get("current_amount"))
        ratio = (current / net_sales) * 100
        if ratio > max_pct:
            flagged.append({
                "category": cat["category"],
                "current_amount": current,
                "ratio": round(ratio, 1),
                "max_percent": max_pct,
            })

    if not flagged:
        return []

    flagged.sort(key=lambda x: x["ratio"], reverse=True)
    top = flagged[0]
    return [_make_decision(
        rule_id="EXPENSE_CATEGORY_RATIO_HIGH",
        category="expenses",
        severity="medium",
        entity_type="ExpenseCategory",
        entity_ids=[f["category"] for f in flagged],
        title=f"تصنيف مصاريف يتجاوز نسبة المبيعات — {len(flagged)}",
        summary=f"تصنيف '{top['category']}' يمثل {top['ratio']}% من المبيعات (الحد: {top['max_percent']}%)",
        evidence=[
            {"label": "التصنيف", "value": top["category"]},
            {"label": "المبلغ", "value": top["current_amount"], "format": "currency"},
            {"label": "النسبة من المبيعات", "value": f"{top['ratio']}%"},
        ],
        recommendation="مراجعة سياسة هذا التصنيف والتأكد من كفاءة الإنفاق",
        action_route="/app/decision-center-expense-category",
        impact_value=top["current_amount"],
        change_pct=top["ratio"],
        extra={"categories": flagged[:10]},
    )]


def evaluate_expense_category_increase(company, from_date, to_date, prev_from, prev_to, **_kw):
    """Trigger when an expense category grows faster than the configured threshold."""
    expense = get_expense_metrics(company, from_date, to_date, prev_from, prev_to)
    threshold = cfg.get_threshold("EXPENSE_INCREASE_THRESHOLD")

    flagged = []
    for cat in expense.get("categories", []):
        pct = cat.get("growth_pct")
        if pct is None:
            continue
        if pct >= threshold:
            flagged.append({
                "category": cat["category"],
                "current_amount": flt(cat.get("current_amount")),
                "previous_amount": flt(cat.get("previous_amount")),
                "growth_pct": pct,
            })

    if not flagged:
        return []

    flagged.sort(key=lambda x: x["growth_pct"], reverse=True)
    top = flagged[0]
    return [_make_decision(
        rule_id="EXPENSE_CATEGORY_INCREASE",
        category="expenses",
        severity="medium",
        entity_type="ExpenseCategory",
        entity_ids=[f["category"] for f in flagged],
        title=f"ارتفاع كبير في مصاريف التصنيف — {len(flagged)}",
        summary=f"تصنيف '{top['category']}' ارتفع بـ {top['growth_pct']}% عن الفترة السابقة",
        evidence=[
            {"label": "التصنيف", "value": top["category"]},
            {"label": "الفترة الحالية", "value": top["current_amount"], "format": "currency"},
            {"label": "الفترة السابقة", "value": top["previous_amount"], "format": "currency"},
            {"label": "نسبة الارتفاع", "value": f"{top['growth_pct']}%"},
        ],
        recommendation="تحليل أسباب الارتفاع والتأكد من علاقته بالنمو في المبيعات",
        action_route="/app/decision-center-expense-category",
        impact_value=top["current_amount"] - top["previous_amount"],
        change_pct=top["growth_pct"],
        extra={"categories": flagged[:10]},
    )]


def evaluate_expense_anomaly(company, from_date, to_date, prev_from, prev_to, **_kw):
    """Trigger when total expenses are significantly above the historical baseline.

    Baseline is the average of at least 3 comparable previous periods.
    If there is not enough history, no decision is generated.
    """
    accounts = list(get_enabled_expense_accounts())
    baseline = get_expense_anomaly_baseline(
        company, accounts, from_date, to_date, periods_count=3
    )
    if baseline is None or baseline <= 0:
        return []

    expense = get_expense_metrics(company, from_date, to_date, prev_from, prev_to)
    current_total = flt(expense.get("total"))
    if current_total <= 0:
        return []

    pct_above = ((current_total - baseline) / baseline) * 100
    threshold = cfg.get_threshold("EXPENSE_ANOMALY_THRESHOLD")
    if pct_above < threshold:
        return []

    return [_make_decision(
        rule_id="EXPENSE_ANOMALY",
        category="expenses",
        severity="high",
        entity_type="Expense",
        entity_ids=["total_expenses"],
        title="مصاريف غير طبيعية مقارنة بالمتوسط التاريخي",
        summary=f"إجمالي المصاريف أعلى من المتوسط التاريخي بـ {pct_above:.1f}% (الحد: {threshold}%)",
        evidence=[
            {"label": "المصاريف الحالية", "value": current_total, "format": "currency"},
            {"label": "المتوسط التاريخي", "value": baseline, "format": "currency"},
            {"label": "الانحراف", "value": f"{pct_above:.1f}%"},
        ],
        recommendation="مراجعة القيود المحاسبية الأخيرة والتأكد من عدم وجود تسجيلات غير معتادة",
        action_route="/app/query-report/General Ledger",
        impact_value=current_total - baseline,
        change_pct=pct_above,
    )]
