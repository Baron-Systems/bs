# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Shared helpers for the Employees section (permissions, settings, schedules)."""

import json
from datetime import date, datetime, timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, get_first_day, get_last_day, getdate

HR_ROLES = {"System Manager", "BS HR Manager"}
SETTINGS_DOCTYPE = "BS Employee Settings"

# Python weekday() index → short code stored in bs_work_days
WEEKDAY_CODES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

PAID_LEAVE_TYPES = {"Annual", "Sick", "Emergency", "Other"}


def is_hr_user(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(HR_ROLES.intersection(frappe.get_roles(user)))


def require_hr():
	if not is_hr_user():
		frappe.throw(_("ليس لديك صلاحية على قسم الموظفين"), frappe.PermissionError)


def parse_json(value):
	if isinstance(value, str):
		return json.loads(value) if value else {}
	return value or {}


def default_company(company=None):
	if company:
		return company
	company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)
	if not company:
		company = frappe.db.get_value("Company", {"is_group": 0}, "name")
	if not company:
		frappe.throw(_("يرجى تحديد الشركة"))
	return company


def company_currency(company):
	return frappe.get_cached_value("Company", company, "default_currency") or frappe.db.get_single_value(
		"Global Defaults", "default_currency"
	)


def get_settings():
	return frappe.get_cached_doc(SETTINGS_DOCTYPE)


def company_accounts(company):
	"""Return the configured accounts row for a company (or an empty dict)."""
	for row in get_settings().get("company_accounts") or []:
		if row.company == company:
			return row.as_dict()
	return frappe._dict()


def period_bounds(period=None):
	"""Normalise 'YYYY-MM' / any date inside a month → (first_day, last_day)."""
	if not period:
		period = getdate()
	elif isinstance(period, str) and len(period) == 7:
		period = period + "-01"
	start = get_first_day(getdate(period))
	return start, get_last_day(start)


def to_minutes(value):
	"""Convert a Time value (timedelta from DB, 'HH:MM[:SS]' string, time) to minutes."""
	if value in (None, ""):
		return None
	if isinstance(value, int):  # already minutes
		return value
	if isinstance(value, timedelta):
		return int(value.total_seconds() // 60)
	if isinstance(value, datetime):
		return value.hour * 60 + value.minute
	if hasattr(value, "hour") and hasattr(value, "minute"):
		return value.hour * 60 + value.minute
	parts = str(value).split(":")
	try:
		return int(parts[0]) * 60 + int(parts[1] if len(parts) > 1 else 0)
	except ValueError:
		return None


def format_time(value):
	minutes = to_minutes(value)
	if minutes is None:
		return None
	return f"{(minutes // 60) % 24:02d}:{minutes % 60:02d}"


def employee_schedule(employee):
	"""Effective schedule for an employee: employee fields with settings fallbacks."""
	if isinstance(employee, str):
		employee = frappe.get_cached_doc("Employee", employee)
	settings = get_settings()
	work_days = (employee.get("bs_work_days") or settings.default_work_days or "Sat,Sun,Mon,Tue,Wed,Thu")
	start = to_minutes(employee.get("bs_shift_start") or settings.default_shift_start or "08:00")
	end = to_minutes(employee.get("bs_shift_end") or settings.default_shift_end or "16:00")
	grace = employee.get("bs_grace_minutes")
	if grace in (None, ""):
		grace = settings.default_grace_minutes
	daily_hours = flt(employee.get("bs_daily_hours")) or flt(settings.default_daily_hours) or 8
	return frappe._dict(
		work_days={d.strip() for d in work_days.split(",") if d.strip()},
		start=start,
		end=end,
		grace=cint(grace),
		daily_hours=daily_hours,
		holiday_list=employee.get("holiday_list")
		or frappe.get_cached_value("Company", employee.get("company"), "default_holiday_list"),
	)


def holidays_between(holiday_list, start, end):
	if not holiday_list:
		return set()
	rows = frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list, "holiday_date": ["between", [start, end]]},
		pluck="holiday_date",
	)
	return {getdate(d) for d in rows}


def iter_dates(start, end):
	day = getdate(start)
	end = getdate(end)
	while day <= end:
		yield day
		day += timedelta(days=1)


def working_dates(employee, start, end, schedule=None):
	"""Dates in [start, end] that are work days for the employee (excluding holidays)."""
	schedule = schedule or employee_schedule(employee)
	holidays = holidays_between(schedule.holiday_list, start, end)
	return [
		d for d in iter_dates(start, end)
		if WEEKDAY_CODES[d.weekday()] in schedule.work_days and d not in holidays
	]


def annual_allowance(employee):
	if isinstance(employee, str):
		employee = frappe.get_cached_doc("Employee", employee)
	value = employee.get("bs_annual_leave_days")
	if value in (None, "", 0):
		value = get_settings().default_annual_leave_days
	return flt(value)


def leave_balance(employee, year=None, exclude=None):
	"""Annual-leave balance for a calendar year."""
	year = cint(year) or getdate().year
	filters = {
		"employee": employee,
		"leave_type": "Annual",
		"status": "Approved",
		"from_date": ["between", [date(year, 1, 1), date(year, 12, 31)]],
	}
	if exclude:
		filters["name"] = ["!=", exclude]
	used = flt(sum(frappe.get_all("BS Leave Application", filters=filters, pluck="total_days")))
	allowance = annual_allowance(employee)
	return {"year": year, "allowance": allowance, "used": used, "remaining": flt(allowance - used, 2)}


def employees_on_leave(company, on_date=None):
	"""Map employee → leave_type for approved leaves covering a date."""
	on_date = getdate(on_date)
	rows = frappe.get_all(
		"BS Leave Application",
		filters={
			"company": company,
			"status": "Approved",
			"from_date": ["<=", on_date],
			"to_date": [">=", on_date],
		},
		fields=["employee", "leave_type"],
	)
	return {r.employee: r.leave_type for r in rows}


def pay_rate_label(emp):
	"""Return (amount, unit) describing an employee's pay."""
	pay_type = emp.get("bs_pay_type") or "Monthly"
	if pay_type == "Hourly":
		return flt(emp.get("bs_hourly_rate")), "hour"
	if pay_type == "Daily":
		return flt(emp.get("bs_daily_rate")), "day"
	return flt(emp.get("bs_monthly_salary")), "month"
