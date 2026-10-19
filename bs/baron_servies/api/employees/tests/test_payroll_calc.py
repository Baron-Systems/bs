# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Tests for the pure payroll rules in payroll_calc."""

import unittest

from ..payroll_calc import PayInputs, cap_installments, compute, installment_due, totals


def line(res, component):
	return next((l for l in res.lines if l["component"] == component), None)


class TestMonthly(unittest.TestCase):
	def base(self, **kw):
		data = dict(pay_type="Monthly", monthly_salary=3000, daily_hours=8, month_working_days=25, required_days=25)
		data.update(kw)
		return PayInputs(**data)

	def test_full_month_no_events(self):
		res = compute(self.base(present_days=25))
		self.assertEqual(res.base_amount, 3000)
		self.assertEqual(res.day_rate, 120)
		self.assertEqual(res.hour_rate, 15)
		self.assertEqual(res.lines, [])

	def test_thirty_day_basis(self):
		res = compute(self.base(day_rate_basis="30 Days", absent_days=1))
		self.assertEqual(res.day_rate, 100)
		self.assertEqual(line(res, "Absence")["amount"], 100)

	def test_absence_and_unpaid_leave(self):
		res = compute(self.base(absent_days=1, unpaid_leave_days=2))
		self.assertEqual(line(res, "Absence")["amount"], 120)
		self.assertEqual(line(res, "Unpaid Leave")["amount"], 240)

	def test_overtime_uses_multiplier(self):
		res = compute(self.base(overtime_hours=4, overtime_multiplier=1.25))
		self.assertEqual(line(res, "Overtime")["amount"], 75)  # 4 × 15 × 1.25

	def test_late_only_when_enabled(self):
		self.assertIsNone(line(compute(self.base(late_minutes=30)), "Late"))
		res = compute(self.base(late_minutes=30, late_deduction_enabled=True))
		self.assertEqual(line(res, "Late")["amount"], 7.5)  # 30 min × 15/60

	def test_prorated_when_joining_mid_month(self):
		res = compute(self.base(required_days=10))
		self.assertEqual(res.base_amount, 1200)
		self.assertEqual(res.base_unit, "day")


class TestDailyAndHourly(unittest.TestCase):
	def test_daily_pays_present_and_paid_leave(self):
		res = compute(PayInputs(pay_type="Daily", daily_rate=120, present_days=20, paid_leave_days=2, absent_days=3))
		self.assertEqual(res.base_amount, 2640)
		self.assertIsNone(line(res, "Absence"))

	def test_daily_late_deduction(self):
		res = compute(PayInputs(pay_type="Daily", daily_rate=120, daily_hours=8, late_minutes=60, late_deduction_enabled=True))
		self.assertEqual(line(res, "Late")["amount"], 15)

	def test_hourly_excludes_overtime_from_base(self):
		res = compute(PayInputs(pay_type="Hourly", hourly_rate=25, daily_hours=8, worked_hours=180,
			overtime_hours=4, overtime_multiplier=1.5, paid_leave_days=1))
		self.assertEqual(res.base_quantity, 184)  # 176 regular + 8 paid leave
		self.assertEqual(res.base_amount, 4600)
		self.assertEqual(line(res, "Overtime")["amount"], 150)

	def test_hourly_never_deducts_late(self):
		res = compute(PayInputs(pay_type="Hourly", hourly_rate=25, late_minutes=60, late_deduction_enabled=True))
		self.assertIsNone(line(res, "Late"))


class TestTotalsAndAdvances(unittest.TestCase):
	def test_totals(self):
		lines = [
			{"line_type": "Earning", "amount": 200},
			{"line_type": "Deduction", "amount": 115},
			{"line_type": "Advance", "amount": 500},
		]
		self.assertEqual(totals(3000, lines), (200, 115, 500, 3085, 2585))

	def test_cap_installments(self):
		self.assertEqual(cap_installments(700, [("a", 500), ("b", 500)]), [("a", 500), ("b", 200)])
		self.assertEqual(cap_installments(-10, [("a", 500)]), [])

	def test_installment_due(self):
		self.assertEqual(installment_due("Installments", 500, 2000), 500)
		self.assertEqual(installment_due("Installments", 500, 300), 300)
		self.assertEqual(installment_due("Next Payroll", 0, 2000), 2000)
		self.assertEqual(installment_due("Manual", 500, 2000), 0)
