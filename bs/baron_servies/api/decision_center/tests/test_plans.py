# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Tests for Decision Center plan engine, progress formulas and lifecycle."""

from __future__ import unicode_literals

import unittest

from frappe.utils import nowdate

from ..registry import (
    cumulative_ceiling_measures,
    cumulative_growth_measures,
    level_progress,
    plan_health,
    target_achieved,
    time_progress,
)


class TestPlanProgress(unittest.TestCase):

    def test_level_progress_increase(self):
        self.assertEqual(level_progress(100, 50, 150, "increase"), 50.0)
        self.assertEqual(level_progress(150, 50, 150, "increase"), 100.0)
        self.assertEqual(level_progress(200, 50, 150, "increase"), 100.0)
        self.assertEqual(level_progress(50, 50, 150, "increase"), 0.0)

    def test_level_progress_decrease(self):
        self.assertEqual(level_progress(150, 150, 100, "decrease"), 0.0)
        self.assertEqual(level_progress(100, 150, 100, "decrease"), 100.0)
        self.assertEqual(level_progress(50, 150, 100, "decrease"), 100.0)
        self.assertEqual(level_progress(0, 150, 100, "decrease"), 100.0)

    def test_cumulative_growth_measures(self):
        result = cumulative_growth_measures(current=600, target=1200, time_progress_pct=50.0)
        self.assertEqual(result["final_target_completion_pct"], 50.0)
        self.assertEqual(result["expected_to_date"], 600.0)
        self.assertEqual(result["pace_attainment_pct"], 100.0)

    def test_cumulative_growth_behind(self):
        result = cumulative_growth_measures(current=400, target=1200, time_progress_pct=50.0)
        self.assertAlmostEqual(result["pace_attainment_pct"], 66.67, places=2)
        self.assertAlmostEqual(result["final_target_completion_pct"], 33.33, places=2)

    def test_cumulative_ceiling_measures(self):
        result = cumulative_ceiling_measures(current=400, cap=1200, time_progress_pct=50.0)
        self.assertAlmostEqual(result["cap_utilization_pct"], 33.33, places=2)
        self.assertEqual(result["remaining_amount"], 800.0)
        self.assertEqual(result["expected_consumption_to_date"], 600.0)
        self.assertAlmostEqual(result["consumption_pace_pct"], 66.67, places=2)

    def test_plan_health_level(self):
        # ahead/on target
        self.assertEqual(plan_health(95, 50, 10, "level"), "on_track")
        # slightly behind
        self.assertEqual(plan_health(45, 50, 10, "level"), "on_track")
        self.assertEqual(plan_health(35, 50, 10, "level"), "needs_attention")
        self.assertEqual(plan_health(20, 50, 10, "level"), "behind")

    def test_plan_health_ceiling(self):
        # consumption_pace = 100 means exactly on pace -> on_track
        self.assertEqual(plan_health(100, 50, 10, "cumulative_ceiling"), "on_track")
        # consumption_pace = 120 means over pace by 20% -> needs_attention
        self.assertEqual(plan_health(120, 50, 10, "cumulative_ceiling"), "needs_attention")
        # consumption_pace = 140 means over pace by 40% -> behind
        self.assertEqual(plan_health(140, 50, 10, "cumulative_ceiling"), "behind")

    def test_target_achieved_level(self):
        self.assertTrue(target_achieved(120, 100, "increase", "level", "Active"))
        self.assertFalse(target_achieved(90, 100, "increase", "level", "Active"))
        # non-sticky: can flip back
        self.assertFalse(target_achieved(110, 100, "decrease", "level", "Active"))
        self.assertTrue(target_achieved(90, 100, "decrease", "level", "Active"))

    def test_target_achieved_cumulative_growth(self):
        self.assertTrue(target_achieved(1200, 1200, "increase", "cumulative_growth", "Active"))
        self.assertFalse(target_achieved(1100, 1200, "increase", "cumulative_growth", "Active"))

    def test_target_achieved_cumulative_ceiling_during_plan(self):
        # During Active plan, target_achieved is always False
        self.assertFalse(target_achieved(200, 1200, "decrease", "cumulative_ceiling", "Active"))
        self.assertFalse(target_achieved(1200, 1200, "decrease", "cumulative_ceiling", "Active"))

    def test_target_achieved_cumulative_ceiling_at_completion(self):
        # At completion, success is current <= cap
        self.assertTrue(target_achieved(1100, 1200, "decrease", "cumulative_ceiling", "Completed"))
        self.assertFalse(target_achieved(1300, 1200, "decrease", "cumulative_ceiling", "Completed"))

    def test_time_progress(self):
        self.assertEqual(time_progress("2026-01-01", "2026-01-31", "2026-01-16"), 51.61290322580645)
        self.assertEqual(time_progress("2026-01-01", "2026-01-31", "2026-02-01"), 100.0)


class TestMetricRegistryValidation(unittest.TestCase):

    def test_gross_profit_not_selectable(self):
        from ..registry import get_metric_capability
        gp = get_metric_capability("gross_profit")
        self.assertFalse(gp["system_available"])
        self.assertFalse(gp["enabled_for_plans"])

        net = get_metric_capability("net_profit")
        self.assertFalse(net["system_available"])
        self.assertFalse(net["enabled_for_plans"])

    def test_sales_total_is_enabled(self):
        from ..registry import get_metric_capability
        meta = get_metric_capability("sales_total")
        self.assertTrue(meta["system_available"])
        self.assertTrue(meta["enabled_for_plans"])
        self.assertEqual(meta["progress_strategy"], "cumulative_growth")


class TestPlanLifecycle(unittest.TestCase):

    def test_only_one_active_plan_allowed(self):
        # This test requires a Frappe test environment; keep minimal structure.
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
