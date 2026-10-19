# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Pure payroll arithmetic (no database access) so the rules are easy to test.

Rules (see BS Employee Settings):
- Day rate: monthly salary ÷ month working days (or ÷ 30); daily rate; hourly rate × daily hours.
- Hour rate: day rate ÷ daily hours; hourly employees use their rate directly.
- Base: monthly salary prorated by employed working days; daily = (present + paid leave) days;
  hourly = regular hours worked + paid leave hours. Overtime is always paid on top of base.
- Absence and unpaid leave are deducted for monthly employees only — daily/hourly employees
  are simply not paid for those days.
- Late minutes beyond grace are deducted (when enabled) for monthly and daily employees;
  hourly employees already lose the unworked time.
- Advance installments are capped so the net never goes below zero.
"""

from dataclasses import dataclass, field


def _r(value):
	return round(float(value or 0) + 1e-9, 2)


@dataclass
class PayInputs:
	pay_type: str = "Monthly"
	monthly_salary: float = 0
	hourly_rate: float = 0
	daily_rate: float = 0
	daily_hours: float = 8
	day_rate_basis: str = "Working Days"
	overtime_multiplier: float = 1.25
	late_deduction_enabled: bool = False
	month_working_days: int = 0  # work days in the full month per the employee's schedule
	required_days: int = 0  # work days inside the employment window
	present_days: int = 0
	absent_days: int = 0
	paid_leave_days: int = 0
	unpaid_leave_days: int = 0
	late_minutes: int = 0
	worked_hours: float = 0
	overtime_hours: float = 0


@dataclass
class PayResult:
	day_rate: float = 0
	hour_rate: float = 0
	base_amount: float = 0
	base_quantity: float = 0
	base_unit: str = ""  # month | day | hour
	lines: list = field(default_factory=list)  # dicts: line_type, component, quantity, amount, note


def rates(inp: PayInputs):
	daily_hours = float(inp.daily_hours or 8)
	if inp.pay_type == "Hourly":
		hour_rate = float(inp.hourly_rate or 0)
		return hour_rate * daily_hours, hour_rate
	if inp.pay_type == "Daily":
		day_rate = float(inp.daily_rate or 0)
		return day_rate, day_rate / daily_hours
	divisor = 30 if inp.day_rate_basis == "30 Days" else (inp.month_working_days or 30)
	day_rate = float(inp.monthly_salary or 0) / divisor
	return day_rate, day_rate / daily_hours


def compute(inp: PayInputs) -> PayResult:
	day_rate, hour_rate = rates(inp)
	res = PayResult(day_rate=_r(day_rate), hour_rate=_r(hour_rate))
	daily_hours = float(inp.daily_hours or 8)

	if inp.pay_type == "Hourly":
		regular_hours = max(0.0, float(inp.worked_hours or 0) - float(inp.overtime_hours or 0))
		hours = regular_hours + inp.paid_leave_days * daily_hours
		res.base_quantity, res.base_unit = _r(hours), "hour"
		res.base_amount = _r(hours * hour_rate)
	elif inp.pay_type == "Daily":
		days = inp.present_days + inp.paid_leave_days
		res.base_quantity, res.base_unit = days, "day"
		res.base_amount = _r(days * day_rate)
	else:
		salary = float(inp.monthly_salary or 0)
		full = inp.month_working_days or 0
		employed = inp.required_days if full else 0
		if full and employed < full:
			res.base_amount = _r(salary * employed / full)
			res.base_quantity, res.base_unit = employed, "day"
		else:
			res.base_amount = _r(salary)
			res.base_quantity, res.base_unit = 1, "month"

	if inp.overtime_hours:
		amount = float(inp.overtime_hours) * hour_rate * float(inp.overtime_multiplier or 1)
		res.lines.append(_line("Earning", "Overtime", inp.overtime_hours, amount))

	if inp.pay_type == "Monthly":
		if inp.absent_days:
			res.lines.append(_line("Deduction", "Absence", inp.absent_days, inp.absent_days * day_rate))
		if inp.unpaid_leave_days:
			res.lines.append(_line("Deduction", "Unpaid Leave", inp.unpaid_leave_days, inp.unpaid_leave_days * day_rate))

	if inp.late_deduction_enabled and inp.late_minutes and inp.pay_type in ("Monthly", "Daily"):
		res.lines.append(_line("Deduction", "Late", inp.late_minutes, inp.late_minutes * hour_rate / 60))

	return res


def _line(line_type, component, quantity, amount, note=""):
	return {
		"line_type": line_type,
		"component": component,
		"quantity": _r(quantity),
		"amount": _r(amount),
		"note": note,
		"is_auto": 1,
	}


def totals(base_amount, lines):
	"""Return (earnings, deductions, advances, gross, net) for a set of lines."""
	earnings = _r(sum(float(l["amount"] or 0) for l in lines if l["line_type"] == "Earning"))
	deductions = _r(sum(float(l["amount"] or 0) for l in lines if l["line_type"] == "Deduction"))
	advances = _r(sum(float(l["amount"] or 0) for l in lines if l["line_type"] == "Advance"))
	gross = _r(float(base_amount or 0) + earnings - deductions)
	return earnings, deductions, advances, gross, _r(gross - advances)


def cap_installments(gross, installments):
	"""Trim advance installments [(key, amount)] in order so their sum never exceeds gross."""
	available = max(0.0, float(gross or 0))
	capped = []
	for key, amount in installments:
		take = _r(min(float(amount or 0), available))
		if take > 0:
			capped.append((key, take))
			available = _r(available - take)
	return capped


def installment_due(method, installment_amount, remaining):
	"""Amount an advance should recover in one payroll period."""
	remaining = max(0.0, float(remaining or 0))
	if method == "Manual" or not remaining:
		return 0.0
	if method == "Next Payroll":
		return _r(remaining)
	return _r(min(float(installment_amount or 0), remaining))
