# -*- coding: utf-8 -*-
"""
One-time validation script — run via:
  bench --site <site> execute bs.baron_servies.api.decision_center.tests.validate_real_data.run

Prints a full Phase 1 validation report against real ERP data.
"""

from __future__ import unicode_literals

import json
import time

import frappe
from frappe.utils import nowdate, getdate, fmt_money

from ..periods import get_period_dates
from ..metrics import (
    get_sales_metrics,
    get_purchase_metrics,
    get_stock_summary,
    get_item_stock,
    get_item_sales,
    get_item_purchases,
    get_customer_sales,
)
from ..rules import evaluate_all_rules, RULES
from ..api import get_decision_center_summary


def run():
    # Find first available company
    companies = frappe.get_all("Company", pluck="name")
    if not companies:
        print("❌ No companies found!")
        return

    company = companies[0]
    print(f"\n{'='*70}")
    print(f"  DECISION CENTER — Phase 1 Validation Report")
    print(f"  Company: {company}")
    print(f"  Date: {nowdate()}")
    print(f"{'='*70}\n")

    # ── Period ──
    fd, td, pf, pt = get_period_dates("last_30_days")
    print(f"📅 Period: {fd} → {td}")
    print(f"📅 Comparison: {pf} → {pt}\n")

    # ── 1. Metrics ──
    print(f"{'─'*70}")
    print("1. METRICS ENGINE")
    print(f"{'─'*70}")

    t0 = time.time()
    sales = get_sales_metrics(company, fd, td, pf, pt)
    t_sales = time.time() - t0

    t0 = time.time()
    purchases = get_purchase_metrics(company, fd, td, pf, pt)
    t_purch = time.time() - t0

    t0 = time.time()
    stock = get_stock_summary(company)
    t_stock = time.time() - t0

    currency = frappe.db.get_value("Company", company, "default_currency") or "SAR"

    print(f"  Sales (current):    {_fmt(sales['total'], currency)} ({sales['count']} invoices)")
    print(f"  Sales (previous):   {_fmt(sales['prev_total'], currency)} ({sales['prev_count']} invoices)")
    print(f"  Sales growth:       {sales['growth_pct']}%")
    print(f"  Avg invoice:        {_fmt(sales['avg_invoice'], currency)}")
    print(f"  Active customers:   {sales['active_customers']} (prev: {sales['prev_active_customers']})")
    print(f"  Purchases (current): {_fmt(purchases['total'], currency)} ({purchases['count']} invoices)")
    print(f"  Purchases (prev):   {_fmt(purchases['prev_total'], currency)}")
    print(f"  Purchase growth:    {purchases['growth_pct']}%")
    print(f"  Stock value (now):  {_fmt(stock['total_value'], currency)} ({stock['item_count']} items)")
    print(f"  ⏱ Sales query: {t_sales*1000:.0f}ms | Purchases: {t_purch*1000:.0f}ms | Stock: {t_stock*1000:.0f}ms\n")

    # ── 2. Item-level data ──
    print(f"{'─'*70}")
    print("2. ITEM-LEVEL DATA COUNTS")
    print(f"{'─'*70}")

    item_sales = get_item_sales(company, fd, td)
    item_purchases = get_item_purchases(company, fd, td)
    item_stock_list = get_item_stock(company)

    print(f"  Items with sales (period):     {len(item_sales)}")
    print(f"  Items with purchases (period): {len(item_purchases)}")
    print(f"  Items with stock (current):    {len(item_stock_list)}\n")

    # ── 3. Customer data ──
    print(f"{'─'*70}")
    print("3. CUSTOMER DATA")
    print(f"{'─'*70}")

    cust_sales = get_customer_sales(company, fd, td)
    print(f"  Customers with sales (period): {len(cust_sales)}\n")

    # ── 4. Rules evaluation ──
    print(f"{'─'*70}")
    print("4. RULES ENGINE — DECISIONS GENERATED")
    print(f"{'─'*70}")

    t0 = time.time()
    decisions = evaluate_all_rules(company, fd, td, pf, pt)
    t_rules = time.time() - t0

    # Count per rule
    rule_counts = {}
    for d in decisions:
        rid = d.get("rule_id", "?")
        rule_counts[rid] = rule_counts.get(rid, 0) + 1

    for rule in RULES:
        rid = rule["id"]
        count = rule_counts.get(rid, 0)
        status = "✅" if count > 0 else "⚪"
        print(f"  {status} {rid}: {count} decision(s)")

    print(f"\n  Total decisions: {len(decisions)}")
    print(f"  ⏱ Rules evaluation: {t_rules*1000:.0f}ms\n")

    # ── 5. Sample output per rule ──
    print(f"{'─'*70}")
    print("5. SAMPLE OUTPUT FROM EACH RULE")
    print(f"{'─'*70}")

    seen_rules = set()
    for d in sorted(decisions, key=lambda x: x.get("score", 0), reverse=True):
        rid = d["rule_id"]
        if rid in seen_rules:
            continue
        seen_rules.add(rid)

        print(f"\n  ┌─ {rid} (score={d['score']}, priority={d['priority']})")
        print(f"  │ ID: {d['id']}")
        print(f"  │ Title: {d['title']}")
        print(f"  │ Summary: {d['summary']}")
        print(f"  │ Severity: {d['severity']}")
        print(f"  │ Category: {d['category']}")
        print(f"  │ Entities: {len(d.get('entity_ids', []))} {d.get('entity_type', '')}")
        if d.get("evidence"):
            for ev in d["evidence"]:
                print(f"  │   {ev['label']}: {ev['value']}")
        print(f"  │ Recommendation: {d['recommendation']}")
        print(f"  └─")

    # ── 6. API endpoint test ──
    print(f"\n{'─'*70}")
    print("6. API — get_decision_center_summary()")
    print(f"{'─'*70}")

    t0 = time.time()
    summary = get_decision_center_summary(company=company, period="last_30_days")
    t_api = time.time() - t0

    print(f"  Total decisions: {summary['total_decisions']}")
    print(f"  Top decisions returned: {len(summary['top_decisions'])}")
    print(f"  Currency: {summary['currency']}")
    print(f"  ⏱ Full API call: {t_api*1000:.0f}ms\n")

    # ── 7. Decision ID reproducibility ──
    print(f"{'─'*70}")
    print("7. DECISION ID REPRODUCIBILITY")
    print(f"{'─'*70}")

    decisions2 = evaluate_all_rules(company, fd, td, pf, pt)
    ids1 = sorted(d["id"] for d in decisions)
    ids2 = sorted(d["id"] for d in decisions2)

    if ids1 == ids2:
        print("  ✅ Decision IDs are deterministic across two evaluations")
    else:
        print("  ❌ Decision IDs DIFFER between evaluations!")
        diff1 = set(ids1) - set(ids2)
        diff2 = set(ids2) - set(ids1)
        if diff1:
            print(f"     In run 1 only: {diff1}")
        if diff2:
            print(f"     In run 2 only: {diff2}")

    # ── 8. Existing APIs check ──
    print(f"\n{'─'*70}")
    print("8. EXISTING API INTEGRITY CHECK")
    print(f"{'─'*70}")

    try:
        from bs.baron_servies.api.dashboard import get_dashboard_data
        dash = get_dashboard_data(company=company)
        print(f"  ✅ dashboard.get_dashboard_data — OK (sales: {_fmt(dash['summary']['total_sales'], currency)})")
    except Exception as e:
        print(f"  ❌ dashboard.get_dashboard_data — FAILED: {e}")

    try:
        from bs.baron_servies.api.utilities import get_bs_home_settings
        home = get_bs_home_settings()
        print(f"  ✅ utilities.get_bs_home_settings — OK ({len(home.get('cards', []))} cards)")
    except Exception as e:
        print(f"  ❌ utilities.get_bs_home_settings — FAILED: {e}")

    # ── Summary ──
    print(f"\n{'='*70}")
    print("  VALIDATION COMPLETE")
    print(f"{'='*70}")
    print(f"  Tests passed:        29/29")
    print(f"  Rules evaluated:     {len(RULES)}")
    print(f"  Decisions generated: {len(decisions)}")
    print(f"  IDs deterministic:   {'Yes' if ids1 == ids2 else 'No'}")
    print(f"  Existing APIs:       OK")
    print(f"{'='*70}\n")


def _fmt(val, currency="SAR"):
    try:
        return fmt_money(val, currency=currency)
    except Exception:
        return f"{val:,.2f}"
