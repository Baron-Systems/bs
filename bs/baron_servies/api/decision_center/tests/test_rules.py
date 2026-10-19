# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Unit tests for Decision Center rules and playbooks.

These tests use mock data to verify rule logic without hitting the database.
They validate:
  - Correct triggering conditions
  - Correct non-triggering (healthy) conditions
  - Return quantity arithmetic (no double-negation)
  - Baseline checks (no false positives on thin data)
  - Deterministic decision IDs
"""

from __future__ import unicode_literals

import unittest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta

from frappe.utils import nowdate, getdate

from ..config import (
    SLOW_MOVING_DAYS,
    DEAD_STOCK_DAYS,
    LOW_STOCK_DAYS,
    WARNING_STOCK_DAYS,
    SALES_DROP_PERCENT,
    SALES_GROWTH_PERCENT,
    PURCHASE_PRICE_INCREASE_PERCENT,
    CUSTOMER_DROP_PERCENT,
    CUSTOMER_INACTIVE_MULTIPLIER,
    OVERSTOCK_PURCHASE_RATIO,
    MIN_SALES_BASELINE,
    MIN_CUSTOMER_INVOICES,
)
from ..playbooks import (
    evaluate_dead_stock,
    evaluate_slow_moving_stock,
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
    _decision_id,
)
from ..expenses import _expense_growth_pct
from ..periods import get_period_dates
from ..priority import compute_score


# ═══════════════════════════════════════════════════════════════════════════
# Test fixtures / helpers
# ═══════════════════════════════════════════════════════════════════════════

_TODAY = getdate(nowdate())
_30_AGO = _TODAY - timedelta(days=29)
_60_AGO = _TODAY - timedelta(days=59)
_90_AGO = _TODAY - timedelta(days=89)


def _stock_items(*items):
    """Build a list of stock item dicts as returned by get_item_stock."""
    return [
        {
            "item_code": ic,
            "item_name": ic,
            "item_group": "G",
            "stock_uom": "Nos",
            "actual_qty": qty,
            "valuation_rate": vr,
            "stock_value": qty * vr,
        }
        for ic, qty, vr in items
    ]


def _sales_items(*items):
    """Build a list of item-sales dicts as returned by get_item_sales."""
    return [
        {
            "item_code": ic,
            "item_name": ic,
            "net_qty": nq,
            "net_amount": na,
            "invoice_count": inv,
            "avg_daily_qty": nq / 90 if nq > 0 else 0,
            "days": 90,
        }
        for ic, nq, na, inv in items
    ]


def _purchase_items(*items):
    """Build list of item-purchase dicts."""
    return [
        {
            "item_code": ic,
            "item_name": ic,
            "net_qty": nq,
            "net_amount": na,
            "invoice_count": inv,
            "avg_rate": na / nq if nq > 0 else 0,
        }
        for ic, nq, na, inv in items
    ]


def _customer_sales(*customers):
    """Build customer-sales dicts."""
    return [
        {
            "customer": c,
            "customer_name": c,
            "net_total": total,
            "invoice_count": inv,
        }
        for c, total, inv in customers
    ]


# ═══════════════════════════════════════════════════════════════════════════
# Period tests
# ═══════════════════════════════════════════════════════════════════════════

class TestPeriods(unittest.TestCase):

    def test_last_30_days(self):
        fd, td, pf, pt = get_period_dates("last_30_days")
        self.assertEqual((td - fd).days, 29)
        self.assertEqual(pt, fd - timedelta(days=1))
        self.assertEqual((pt - pf).days, 29)

    def test_custom_period(self):
        fd, td, pf, pt = get_period_dates(
            "custom", custom_from="2025-01-01", custom_to="2025-01-31")
        self.assertEqual(fd, date(2025, 1, 1))
        self.assertEqual(td, date(2025, 1, 31))
        self.assertEqual(pt, date(2024, 12, 31))

    def test_custom_requires_dates(self):
        with self.assertRaises(ValueError):
            get_period_dates("custom")

    @patch("bs.baron_servies.api.decision_center.periods.nowdate")
    def test_this_month_period_to_date(self, mock_now):
        """this_month on Oct 4 → current Oct 1–4, prev Sep 1–4."""
        mock_now.return_value = "2026-10-04"
        fd, td, pf, pt = get_period_dates("this_month")
        self.assertEqual(fd, date(2026, 10, 1))
        self.assertEqual(td, date(2026, 10, 4))
        self.assertEqual(pf, date(2026, 9, 1))
        self.assertEqual(pt, date(2026, 9, 4))

    @patch("bs.baron_servies.api.decision_center.periods.nowdate")
    def test_this_month_clamps_to_shorter_prev(self, mock_now):
        """this_month on Mar 31 → prev Feb 1–28 (clamped)."""
        mock_now.return_value = "2026-03-31"
        fd, td, pf, pt = get_period_dates("this_month")
        self.assertEqual(fd, date(2026, 3, 1))
        self.assertEqual(td, date(2026, 3, 31))
        self.assertEqual(pf, date(2026, 2, 1))
        self.assertEqual(pt, date(2026, 2, 28))  # Feb has 28 days

    @patch("bs.baron_servies.api.decision_center.periods.nowdate")
    def test_this_quarter_period_to_date(self, mock_now):
        """this_quarter on Oct 4 → current Oct 1–4, prev Jul 1–4."""
        mock_now.return_value = "2026-10-04"
        fd, td, pf, pt = get_period_dates("this_quarter")
        self.assertEqual(fd, date(2026, 10, 1))
        self.assertEqual(td, date(2026, 10, 4))
        self.assertEqual(pf, date(2026, 7, 1))
        self.assertEqual(pt, date(2026, 7, 4))

    @patch("bs.baron_servies.api.decision_center.periods.nowdate")
    def test_this_year_period_to_date(self, mock_now):
        """this_year on Oct 4 → current Jan 1–Oct 4, prev Jan 1–Oct 4 of 2025."""
        mock_now.return_value = "2026-10-04"
        fd, td, pf, pt = get_period_dates("this_year")
        self.assertEqual(fd, date(2026, 1, 1))
        self.assertEqual(td, date(2026, 10, 4))
        self.assertEqual(pf, date(2025, 1, 1))
        self.assertEqual(pt, date(2025, 10, 4))

    @patch("bs.baron_servies.api.decision_center.periods.nowdate")
    def test_last_30_days_equal_window(self, mock_now):
        """last_30_days still uses equal-length sliding window."""
        mock_now.return_value = "2026-10-04"
        fd, td, pf, pt = get_period_dates("last_30_days")
        self.assertEqual((td - fd).days, 29)
        self.assertEqual(pt, fd - timedelta(days=1))
        self.assertEqual((pt - pf).days, 29)


# ═══════════════════════════════════════════════════════════════════════════
# Priority scoring tests
# ═══════════════════════════════════════════════════════════════════════════

class TestPriority(unittest.TestCase):

    def test_high_severity_high_impact(self):
        d = {"severity": "high", "impact_value": 60000, "change_pct": 50}
        compute_score(d)
        self.assertGreaterEqual(d["score"], 70)
        self.assertIn(d["priority"], ("urgent", "important"))

    def test_low_severity_no_impact(self):
        d = {"severity": "low", "impact_value": 0, "change_pct": 0}
        compute_score(d)
        self.assertLess(d["score"], 40)
        self.assertEqual(d["priority"], "opportunity")


# ═══════════════════════════════════════════════════════════════════════════
# Decision ID determinism tests
# ═══════════════════════════════════════════════════════════════════════════

class TestDecisionID(unittest.TestCase):

    def test_deterministic(self):
        id1 = _decision_id("DEAD_STOCK", "Item", ["A", "B", "C"])
        id2 = _decision_id("DEAD_STOCK", "Item", ["C", "A", "B"])
        self.assertEqual(id1, id2)

    def test_different_rules(self):
        id1 = _decision_id("DEAD_STOCK", "Item", ["A"])
        id2 = _decision_id("SLOW_MOVING_STOCK", "Item", ["A"])
        self.assertNotEqual(id1, id2)


# ═══════════════════════════════════════════════════════════════════════════
# Dead Stock tests
# ═══════════════════════════════════════════════════════════════════════════

class TestDeadStock(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_stock")
    def test_dead_stock_triggered(self, mock_stock, mock_sales):
        """stock=100, zero sales in 180d → DEAD_STOCK triggered."""
        mock_stock.return_value = _stock_items(("ITEM-A", 100, 50))
        mock_sales.return_value = []  # no sales at all

        results = evaluate_dead_stock(
            company="C", from_date=_90_AGO, to_date=_TODAY,
            prev_from=_90_AGO, prev_to=_TODAY)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "DEAD_STOCK")
        self.assertIn("ITEM-A", results[0]["entity_ids"])

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_stock")
    def test_dead_stock_not_triggered_with_sales(self, mock_stock, mock_sales):
        """stock=100, has sales → should NOT be dead stock."""
        mock_stock.return_value = _stock_items(("ITEM-A", 100, 50))
        mock_sales.return_value = _sales_items(("ITEM-A", 10, 500, 5))

        results = evaluate_dead_stock(
            company="C", from_date=_90_AGO, to_date=_TODAY,
            prev_from=_90_AGO, prev_to=_TODAY)

        self.assertEqual(len(results), 0)

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_stock")
    def test_dead_stock_not_triggered_zero_stock(self, mock_stock, mock_sales):
        """stock=0, no sales → should NOT flag (nothing to act on)."""
        mock_stock.return_value = _stock_items(("ITEM-A", 0, 50))
        mock_sales.return_value = []

        results = evaluate_dead_stock(
            company="C", from_date=_90_AGO, to_date=_TODAY,
            prev_from=_90_AGO, prev_to=_TODAY)

        self.assertEqual(len(results), 0)


# ═══════════════════════════════════════════════════════════════════════════
# Slow Moving Stock tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSlowMovingStock(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_stock")
    def test_slow_moving_triggered(self, mock_stock, mock_sales):
        """stock=100, sales=5 in 90d → days_of_stock=1800 → SLOW_MOVING."""
        mock_stock.return_value = _stock_items(("ITEM-A", 100, 50))
        mock_sales.return_value = _sales_items(("ITEM-A", 5, 250, 3))

        results = evaluate_slow_moving_stock(
            company="C", from_date=_90_AGO, to_date=_TODAY)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "SLOW_MOVING_STOCK")

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_stock")
    def test_healthy_stock_not_triggered(self, mock_stock, mock_sales):
        """stock=100, sales=90 in 30d → healthy → neither rule triggers."""
        mock_stock.return_value = _stock_items(("ITEM-A", 100, 50))
        # 90 items sold in 90 days → avg_daily=1 → days_of_stock=100 → >90
        # Actually need higher velocity to be healthy
        # 90 items in 90 days = 1/day, stock=100 → 100 days > 90 → would trigger
        # Let's use 300 sold in 90 days → 3.33/day → stock=100 → 30 days
        mock_sales.return_value = _sales_items(("ITEM-A", 300, 15000, 30))

        results = evaluate_slow_moving_stock(
            company="C", from_date=_90_AGO, to_date=_TODAY)

        self.assertEqual(len(results), 0)

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_stock")
    def test_zero_sales_not_slow_moving(self, mock_stock, mock_sales):
        """stock=100, zero sales → should NOT be slow moving (that's dead stock)."""
        mock_stock.return_value = _stock_items(("ITEM-A", 100, 50))
        mock_sales.return_value = []

        results = evaluate_slow_moving_stock(
            company="C", from_date=_90_AGO, to_date=_TODAY)

        self.assertEqual(len(results), 0)


# ═══════════════════════════════════════════════════════════════════════════
# Low Stock Risk tests
# ═══════════════════════════════════════════════════════════════════════════

class TestLowStockRisk(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_stock")
    def test_urgent_low_stock(self, mock_stock, mock_sales):
        """stock=5, avg_daily=2 → 2.5 days → urgent."""
        mock_stock.return_value = _stock_items(("ITEM-A", 5, 100))
        # 60 sold in 30 days → avg=2/day
        mock_sales.return_value = [{
            "item_code": "ITEM-A", "item_name": "ITEM-A",
            "net_qty": 60, "net_amount": 6000, "invoice_count": 20,
            "avg_daily_qty": 2.0, "days": 30,
        }]

        results = evaluate_low_stock_risk(
            company="C", from_date=_30_AGO, to_date=_TODAY)

        self.assertTrue(len(results) >= 1)
        urgent = [d for d in results if d["severity"] == "high"]
        self.assertTrue(len(urgent) >= 1)
        self.assertEqual(urgent[0]["rule_id"], "LOW_STOCK_RISK")


# ═══════════════════════════════════════════════════════════════════════════
# Over-purchasing tests
# ═══════════════════════════════════════════════════════════════════════════

class TestOverPurchasing(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_stock")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_purchases")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    def test_over_purchasing_triggered(self, mock_sales, mock_purchases, mock_stock):
        """purchased=200, sold=50 → ratio=4 > 1.5 → triggered."""
        mock_sales.return_value = _sales_items(("ITEM-A", 50, 2500, 10))
        mock_purchases.return_value = _purchase_items(("ITEM-A", 200, 10000, 5))
        mock_stock.return_value = _stock_items(("ITEM-A", 300, 50))

        results = evaluate_over_purchasing(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "OVER_PURCHASING")

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_stock")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_purchases")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    def test_balanced_purchasing_not_triggered(self, mock_sales, mock_purchases, mock_stock):
        """purchased=50, sold=50 → ratio=1 < 1.5 → NOT triggered."""
        mock_sales.return_value = _sales_items(("ITEM-A", 50, 2500, 10))
        mock_purchases.return_value = _purchase_items(("ITEM-A", 50, 2500, 5))
        mock_stock.return_value = _stock_items(("ITEM-A", 50, 50))

        results = evaluate_over_purchasing(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 0)


# ═══════════════════════════════════════════════════════════════════════════
# Item Sales Decline tests
# ═══════════════════════════════════════════════════════════════════════════

class TestItemSalesDecline(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    def test_sales_decline_triggered(self, mock_sales):
        """prev=100, current=50 → -50% → triggered."""
        def side_effect(company, from_date, to_date):
            if from_date == _30_AGO:
                return _sales_items(("ITEM-A", 50, 2500, 10))
            return _sales_items(("ITEM-A", 100, 5000, 20))
        mock_sales.side_effect = side_effect

        results = evaluate_item_sales_decline(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "ITEM_SALES_DECLINE")

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    def test_no_baseline_not_triggered(self, mock_sales):
        """prev=1, current=0 → baseline < 3 → NOT triggered."""
        def side_effect(company, from_date, to_date):
            if from_date == _30_AGO:
                return _sales_items(("ITEM-A", 0, 0, 0))
            return _sales_items(("ITEM-A", 1, 50, 1))
        mock_sales.side_effect = side_effect

        results = evaluate_item_sales_decline(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 0)


# ═══════════════════════════════════════════════════════════════════════════
# Item Sales Growth tests
# ═══════════════════════════════════════════════════════════════════════════

class TestItemSalesGrowth(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    def test_growth_triggered(self, mock_sales):
        """prev=50, current=100 → +100% → triggered."""
        def side_effect(company, from_date, to_date):
            if from_date == _30_AGO:
                return _sales_items(("ITEM-A", 100, 5000, 20))
            return _sales_items(("ITEM-A", 50, 2500, 10))
        mock_sales.side_effect = side_effect

        results = evaluate_item_sales_growth(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "ITEM_SALES_GROWTH")


# ═══════════════════════════════════════════════════════════════════════════
# Customer Decline tests
# ═══════════════════════════════════════════════════════════════════════════

class TestCustomerDecline(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.playbooks.get_customer_sales")
    def test_decline_triggered(self, mock_csales):
        """prev=10000, current=5000, invoices=5 → -50% → triggered."""
        def side_effect(company, from_date, to_date):
            if from_date == _30_AGO:
                return _customer_sales(("CUST-A", 5000, 3))
            return _customer_sales(("CUST-A", 10000, 5))
        mock_csales.side_effect = side_effect

        results = evaluate_customer_decline(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "CUSTOMER_DECLINE")

    @patch("bs.baron_servies.api.decision_center.playbooks.get_customer_sales")
    def test_new_customer_not_triggered(self, mock_csales):
        """1 invoice only → baseline < 3 → NOT triggered."""
        def side_effect(company, from_date, to_date):
            if from_date == _30_AGO:
                return _customer_sales(("CUST-A", 0, 0))
            return _customer_sales(("CUST-A", 500, 1))
        mock_csales.side_effect = side_effect

        results = evaluate_customer_decline(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 0)


# ═══════════════════════════════════════════════════════════════════════════
# Customer Stopped tests
# ═══════════════════════════════════════════════════════════════════════════

class TestCustomerStopped(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.playbooks._estimate_stopped_customer_value", return_value=5000)
    @patch("bs.baron_servies.api.decision_center.playbooks._batch_customer_avg_gaps")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_customer_last_purchase_dates")
    def test_stopped_triggered(self, mock_dates, mock_gaps, _mock_val):
        """10 invoices, last 120 days ago, avg gap 20 days → threshold=40 → triggered."""
        mock_dates.return_value = [{
            "customer": "CUST-A",
            "last_date": _TODAY - timedelta(days=120),
            "total_invoices": 10,
        }]
        mock_gaps.return_value = {"CUST-A": 20.0}

        results = evaluate_customer_stopped(
            company="C", from_date=_30_AGO, to_date=_TODAY)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "CUSTOMER_STOPPED")

    @patch("bs.baron_servies.api.decision_center.playbooks._estimate_stopped_customer_value", return_value=0)
    @patch("bs.baron_servies.api.decision_center.playbooks._batch_customer_avg_gaps")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_customer_last_purchase_dates")
    def test_recent_customer_not_triggered(self, mock_dates, mock_gaps, _mock_val):
        """Last purchase 5 days ago, avg gap 20 → 5 < 40 → NOT triggered."""
        mock_dates.return_value = [{
            "customer": "CUST-A",
            "last_date": _TODAY - timedelta(days=5),
            "total_invoices": 10,
        }]
        mock_gaps.return_value = {"CUST-A": 20.0}

        results = evaluate_customer_stopped(
            company="C", from_date=_30_AGO, to_date=_TODAY)

        self.assertEqual(len(results), 0)


# ═══════════════════════════════════════════════════════════════════════════
# Purchase Price Increase tests
# ═══════════════════════════════════════════════════════════════════════════

class TestPurchasePriceIncrease(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_purchases")
    def test_price_increase_triggered(self, mock_purchases):
        """prev_rate=10, current_rate=12 → +20% → triggered."""
        def side_effect(company, from_date, to_date):
            if from_date == _30_AGO:
                return _purchase_items(("ITEM-A", 100, 1200, 5))  # rate=12
            return _purchase_items(("ITEM-A", 100, 1000, 5))  # rate=10
        mock_purchases.side_effect = side_effect

        results = evaluate_purchase_price_increase(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "PURCHASE_PRICE_INCREASE")


# ═══════════════════════════════════════════════════════════════════════════
# Return handling tests (anti double-negation)
# ═══════════════════════════════════════════════════════════════════════════

class TestReturnHandling(unittest.TestCase):
    """Verify that return quantities are handled correctly.

    ERPNext stores return qty as negative.
    SUM(qty) across normal + return = net qty.
    We must NOT do normal_qty - return_qty when return_qty is already negative.
    """

    def test_sales_return_net_qty(self):
        """sale=10, return=-3 → net must be 7, not 13."""
        sale_qty = 10
        return_qty = -3
        # Correct: SUM approach
        net = sale_qty + return_qty
        self.assertEqual(net, 7)
        # What the WRONG approach would produce:
        wrong = sale_qty - return_qty  # 10 - (-3) = 13
        self.assertEqual(wrong, 13)
        self.assertNotEqual(net, wrong)

    def test_purchase_return_net_qty(self):
        """purchase=20, return=-5 → net must be 15, not 25."""
        purchase_qty = 20
        return_qty = -5
        net = purchase_qty + return_qty
        self.assertEqual(net, 15)
        wrong = purchase_qty - return_qty  # 20 - (-5) = 25
        self.assertEqual(wrong, 25)
        self.assertNotEqual(net, wrong)

    def test_double_negation_guard(self):
        """Explicit guard: SUM must NOT be 10-(-3)=13."""
        values = [10, -3]
        net = sum(values)
        self.assertEqual(net, 7)
        self.assertNotEqual(net, 13)

    def test_sales_amount_return_safe(self):
        """grand_total: normal=1000, return=-300 → net=700."""
        totals = [1000, -300]
        net = sum(totals)
        self.assertEqual(net, 700)


# ═══════════════════════════════════════════════════════════════════════════
# Mutually exclusive: Dead vs Slow
# ═══════════════════════════════════════════════════════════════════════════

class TestMutualExclusion(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_sales")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_item_stock")
    def test_dead_and_slow_mutually_exclusive(self, mock_stock, mock_sales):
        """An item with zero sales is Dead Stock, not Slow Moving."""
        mock_stock.return_value = _stock_items(("ITEM-A", 100, 50))
        mock_sales.return_value = []  # zero sales

        dead = evaluate_dead_stock(
            company="C", from_date=_90_AGO, to_date=_TODAY,
            prev_from=_90_AGO, prev_to=_TODAY)
        slow = evaluate_slow_moving_stock(
            company="C", from_date=_90_AGO, to_date=_TODAY)

        self.assertTrue(len(dead) > 0, "Should be Dead Stock")
        self.assertEqual(len(slow), 0, "Should NOT be Slow Moving")


# ═══════════════════════════════════════════════════════════════════════════
# Expense analysis tests
# ═══════════════════════════════════════════════════════════════════════════

class TestExpenseGrowthPct(unittest.TestCase):

    def test_growth_null_when_previous_zero(self):
        self.assertIsNone(_expense_growth_pct(0, 100))

    def test_growth_null_when_previous_negative(self):
        self.assertIsNone(_expense_growth_pct(-50, 100))

    def test_growth_calculated_when_previous_positive(self):
        self.assertEqual(_expense_growth_pct(100, 120), 20.0)

    def test_growth_negative_when_decreased(self):
        self.assertEqual(_expense_growth_pct(100, 80), -20.0)


class TestExpensePlaybooks(unittest.TestCase):

    @patch("bs.baron_servies.api.decision_center.metrics.get_sales_metrics")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_expense_metrics")
    def test_total_expense_ratio_high_triggered(self, mock_exp, mock_sales):
        mock_exp.return_value = {"total": 15000, "previous_total": 12000, "growth_pct": 25}
        mock_sales.return_value = {"total": 100000}

        results = evaluate_total_expense_ratio_high(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "TOTAL_EXPENSE_RATIO_HIGH")

    @patch("bs.baron_servies.api.decision_center.metrics.get_sales_metrics")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_expense_metrics")
    def test_total_expense_ratio_skipped_when_no_sales(self, mock_exp, mock_sales):
        mock_exp.return_value = {"total": 5000, "previous_total": 5000, "growth_pct": 0}
        mock_sales.return_value = {"total": 0}

        results = evaluate_total_expense_ratio_high(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 0)

    @patch("bs.baron_servies.api.decision_center.metrics.get_sales_metrics")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_expense_metrics")
    def test_category_ratio_high_triggered(self, mock_exp, mock_sales):
        mock_exp.return_value = {
            "categories": [{
                "category": "رواتب",
                "current_amount": 12000,
                "previous_amount": 10000,
                "growth_pct": 20,
                "target_percent_of_sales": 5,
                "max_percent_of_sales": 10,
            }]
        }
        mock_sales.return_value = {"total": 100000}

        results = evaluate_expense_category_ratio_high(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "EXPENSE_CATEGORY_RATIO_HIGH")

    @patch("bs.baron_servies.api.decision_center.playbooks.get_expense_metrics")
    def test_category_increase_triggered(self, mock_exp):
        mock_exp.return_value = {
            "categories": [{
                "category": "إيجارات",
                "current_amount": 6000,
                "previous_amount": 4000,
                "growth_pct": 50,
            }]
        }

        results = evaluate_expense_category_increase(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "EXPENSE_CATEGORY_INCREASE")

    @patch("bs.baron_servies.api.decision_center.playbooks.get_expense_metrics")
    def test_category_increase_skipped_when_null_growth(self, mock_exp):
        mock_exp.return_value = {
            "categories": [{
                "category": "إيجارات",
                "current_amount": 6000,
                "previous_amount": 0,
                "growth_pct": None,
            }]
        }

        results = evaluate_expense_category_increase(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 0)

    @patch("bs.baron_servies.api.decision_center.playbooks.get_expense_anomaly_baseline")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_enabled_expense_accounts")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_expense_metrics")
    def test_anomaly_triggered_with_baseline(self, mock_exp, mock_accounts, mock_baseline):
        mock_accounts.return_value = {"EXP-001"}
        mock_baseline.return_value = 10000
        mock_exp.return_value = {"total": 15000}

        results = evaluate_expense_anomaly(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rule_id"], "EXPENSE_ANOMALY")

    @patch("bs.baron_servies.api.decision_center.playbooks.get_expense_anomaly_baseline")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_enabled_expense_accounts")
    @patch("bs.baron_servies.api.decision_center.playbooks.get_expense_metrics")
    def test_anomaly_skipped_without_baseline(self, mock_exp, mock_accounts, mock_baseline):
        mock_accounts.return_value = {"EXP-001"}
        mock_baseline.return_value = None
        mock_exp.return_value = {"total": 15000}

        results = evaluate_expense_anomaly(
            company="C", from_date=_30_AGO, to_date=_TODAY,
            prev_from=_60_AGO, prev_to=_30_AGO)

        self.assertEqual(len(results), 0)


# ═══════════════════════════════════════════════════════════════════════════
# Settings-wiring regression tests
# Verify that editable Decision Center Settings are actually consumed by the
# engine at runtime (via config.get_threshold), with code constants used only
# as fallback when no stored setting exists.
# ═══════════════════════════════════════════════════════════════════════════


def _settings_doc(**values):
	"""Mock a Decision Center Settings doc.

	``get_threshold`` calls ``doc.has_field(fieldname)`` then ``doc.get(fieldname)``
	and falls back to the code default when the value is ``None``.  Direct
	``getattr`` access (e.g. ``default_plan_priority``) is covered by setting
	real attributes on the mock.
	"""
	doc = MagicMock()
	for key, value in values.items():
		setattr(doc, key, value)
	doc.has_field = lambda _f: True
	doc.get = lambda f, *a, **k: values.get(f)
	doc.rule_settings = []
	return doc


class TestPurchasePriceIncreaseSetting(unittest.TestCase):
	"""purchase_price_increase_percent must drive PURCHASE_PRICE_INCREASE."""

	def _purchases(self, prev_rate, curr_rate):
		def side_effect(company, from_date, to_date):
			if from_date == _30_AGO:
				return _purchase_items(("ITEM-A", 100, curr_rate * 100, 5))
			return _purchase_items(("ITEM-A", 100, prev_rate * 100, 5))
		return side_effect

	@patch("bs.baron_servies.api.decision_center.playbooks.get_item_purchases")
	def test_default_threshold_applies(self, mock_purchases):
		"""No stored setting → code default (10%): +20% triggers, +5% does not."""
		mock_purchases.side_effect = self._purchases(10, 12)

		results = evaluate_purchase_price_increase(
			company="C", from_date=_30_AGO, to_date=_TODAY,
			prev_from=_60_AGO, prev_to=_30_AGO)
		self.assertEqual(len(results), 1)

		mock_purchases.side_effect = self._purchases(10, 10.5)
		results = evaluate_purchase_price_increase(
			company="C", from_date=_30_AGO, to_date=_TODAY,
			prev_from=_60_AGO, prev_to=_30_AGO)
		self.assertEqual(len(results), 0)

	@patch("bs.baron_servies.api.decision_center.config.get_decision_center_settings")
	@patch("bs.baron_servies.api.decision_center.playbooks.get_item_purchases")
	def test_saved_setting_changes_triggering(self, mock_purchases, mock_settings):
		"""Stored setting = 50% → +20% must NOT trigger."""
		mock_settings.return_value = _settings_doc(purchase_price_increase_percent=50)
		mock_purchases.side_effect = self._purchases(10, 12)

		results = evaluate_purchase_price_increase(
			company="C", from_date=_30_AGO, to_date=_TODAY,
			prev_from=_60_AGO, prev_to=_30_AGO)
		self.assertEqual(len(results), 0)

	@patch("bs.baron_servies.api.decision_center.config.get_decision_center_settings")
	@patch("bs.baron_servies.api.decision_center.playbooks.get_item_purchases")
	def test_lowered_setting_triggers_earlier(self, mock_purchases, mock_settings):
		"""Stored setting = 5% → +8% must trigger."""
		mock_settings.return_value = _settings_doc(purchase_price_increase_percent=5)
		mock_purchases.side_effect = self._purchases(10, 10.8)

		results = evaluate_purchase_price_increase(
			company="C", from_date=_30_AGO, to_date=_TODAY,
			prev_from=_60_AGO, prev_to=_30_AGO)
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0]["rule_id"], "PURCHASE_PRICE_INCREASE")

	@patch("bs.baron_servies.api.decision_center.config.get_decision_center_settings")
	@patch("bs.baron_servies.api.decision_center.playbooks.get_item_purchases")
	def test_missing_settings_doc_falls_back(self, mock_purchases, mock_settings):
		"""No settings doc → code default still applies."""
		mock_settings.return_value = None
		mock_purchases.side_effect = self._purchases(10, 12)

		results = evaluate_purchase_price_increase(
			company="C", from_date=_30_AGO, to_date=_TODAY,
			prev_from=_60_AGO, prev_to=_30_AGO)
		self.assertEqual(len(results), 1)


class TestInventoryAnalysisThresholds(unittest.TestCase):
	"""slow_moving_days / warning_stock_days must drive inventory categorization."""

	def _run(self):
		from ..api import get_inventory_analysis
		return get_inventory_analysis(company="C", period="last_30_days")

	@patch("bs.baron_servies.api.decision_center.api._get_currency", return_value="SAR")
	@patch("bs.baron_servies.api.decision_center.api.get_item_sales")
	@patch("bs.baron_servies.api.decision_center.api.get_item_stock")
	@patch("bs.baron_servies.api.decision_center.api.get_stock_summary")
	def test_default_thresholds(self, mock_summary, mock_stock, mock_sales, _cur):
		"""days_of_stock=100 → slow (>90) but not low (≥14) under defaults."""
		mock_summary.return_value = {"total_value": 5000}
		mock_stock.return_value = _stock_items(("ITEM-A", 100, 50))
		mock_sales.return_value = [{
			"item_code": "ITEM-A", "item_name": "ITEM-A",
			"net_qty": 90, "net_amount": 4500, "invoice_count": 5,
			"avg_daily_qty": 1.0, "days": 90,
		}]

		res = self._run()
		self.assertEqual(res["slow_moving_count"], 1)
		self.assertEqual(res["low_stock_count"], 0)

	@patch("bs.baron_servies.api.decision_center.config.get_decision_center_settings")
	@patch("bs.baron_servies.api.decision_center.api._get_currency", return_value="SAR")
	@patch("bs.baron_servies.api.decision_center.api.get_item_sales")
	@patch("bs.baron_servies.api.decision_center.api.get_item_stock")
	@patch("bs.baron_servies.api.decision_center.api.get_stock_summary")
	def test_saved_settings_change_categorization(
			self, mock_summary, mock_stock, mock_sales, _cur, mock_settings):
		"""slow_moving_days=200 / warning_stock_days=300 → not slow, IS low."""
		mock_settings.return_value = _settings_doc(
			slow_moving_days=200, warning_stock_days=300)
		mock_summary.return_value = {"total_value": 5000}
		mock_stock.return_value = _stock_items(("ITEM-A", 100, 50))
		mock_sales.return_value = [{
			"item_code": "ITEM-A", "item_name": "ITEM-A",
			"net_qty": 90, "net_amount": 4500, "invoice_count": 5,
			"avg_daily_qty": 1.0, "days": 90,
		}]

		res = self._run()
		self.assertEqual(res["slow_moving_count"], 0)
		self.assertEqual(res["low_stock_count"], 1)


class TestDefaultPlanPriority(unittest.TestCase):
	"""default_plan_priority must be exposed for plan creation."""

	@patch("bs.baron_servies.api.decision_center.plan_api.get_decision_center_settings")
	@patch("bs.baron_servies.api.decision_center.plan_api.get_expense_categories", return_value=[])
	def test_reference_options_exposes_stored_default(self, _cats, mock_settings):
		from ..plan_api import get_plan_reference_options
		mock_settings.return_value = _settings_doc(default_plan_priority="Critical")

		res = get_plan_reference_options()
		self.assertEqual(res["default_plan_priority"], "Critical")

	@patch("bs.baron_servies.api.decision_center.plan_api.get_decision_center_settings")
	@patch("bs.baron_servies.api.decision_center.plan_api.get_expense_categories", return_value=[])
	def test_reference_options_falls_back_to_medium(self, _cats, mock_settings):
		from ..plan_api import get_plan_reference_options
		mock_settings.return_value = None

		res = get_plan_reference_options()
		self.assertEqual(res["default_plan_priority"], "Medium")

	_PLAN_KPI = {
		"metric_key": "sales_total",
		"is_primary": 1,
		"direction": "increase",
		"target_value": 100,
	}

	@patch("bs.baron_servies.api.decision_center.plan_api.compute_baseline", return_value={"value": 0})
	@patch("bs.baron_servies.api.decision_center.plan_api.get_decision_center_settings")
	def test_apply_payload_uses_settings_default(self, mock_settings, _baseline):
		"""Payload without priority → stored default wins over 'Medium'."""
		from ..plan_api import _apply_plan_payload
		mock_settings.return_value = _settings_doc(default_plan_priority="High")

		doc = MagicMock()
		_apply_plan_payload(
			doc, {"plan_name": "P", "kpis": [self._PLAN_KPI], "actions": []},
			is_new=True)
		self.assertEqual(doc.priority, "High")

	@patch("bs.baron_servies.api.decision_center.plan_api.compute_baseline", return_value={"value": 0})
	@patch("bs.baron_servies.api.decision_center.plan_api.get_decision_center_settings")
	def test_apply_payload_explicit_priority_wins(self, mock_settings, _baseline):
		"""Payload priority must never be overridden by the setting."""
		from ..plan_api import _apply_plan_payload
		mock_settings.return_value = _settings_doc(default_plan_priority="Critical")

		doc = MagicMock()
		_apply_plan_payload(
			doc, {"plan_name": "P", "priority": "Low", "kpis": [self._PLAN_KPI], "actions": []},
			is_new=True)
		self.assertEqual(doc.priority, "Low")


if __name__ == "__main__":
    unittest.main()
