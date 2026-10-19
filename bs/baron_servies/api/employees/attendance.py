# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Attendance (الدوام): daily board, monthly summary, per-employee month, manual entry."""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from bs.baron_servies.api.employees.common import (
	PAID_LEAVE_TYPES,
	WEEKDAY_CODES,
	default_company,
	employee_schedule,
	format_time,
	get_settings,
	holidays_between,
	iter_dates,
	parse_json,
	period_bounds,
	require_hr,
)

EMPLOYEE_FIELDS = [
	"name", "employee_name", "designation", "department", "branch", "image", "company",
	"status", "date_of_joining", "relieving_date", "holiday_list",
	"bs_work_days", "bs_shift_start", "bs_shift_end", "bs_grace_minutes", "bs_daily_hours",
]

ATTENDANCE_FIELDS = [
	"name", "employee", "attendance_date", "status", "check_in", "check_out", "working_hours",
	"late_minutes", "early_exit_minutes", "overtime_hours", "leave_type", "source", "note",
]


def _active_employees(company, start=None, end=None, employee=None):
	"""Employees employed at any point in [start, end] (or currently active)."""
	filters = {"company": company}
	if employee:
		filters["name"] = employee
	rows = frappe.get_all("Employee", filters=filters, fields=EMPLOYEE_FIELDS, order_by="employee_name asc")
	result = []
	for emp in rows:
		if start and end:
			if emp.date_of_joining and getdate(emp.date_of_joining) > getdate(end):
				continue
			if emp.relieving_date and getdate(emp.relieving_date) < getdate(start):
				continue
			if emp.status == "Left" and not emp.relieving_date:
				continue
		elif emp.status != "Active":
			continue
		result.append(emp)
	return result


def _attendance_map(company, start, end, employee=None):
	filters = {"company": company, "attendance_date": ["between", [start, end]]}
	if employee:
		filters["employee"] = employee
	out = {}
	for row in frappe.get_all("BS Attendance", filters=filters, fields=ATTENDANCE_FIELDS):
		row.check_in = format_time(row.check_in)
		row.check_out = format_time(row.check_out)
		out[(row.employee, getdate(row.attendance_date))] = row
	return out


def _employed_on(emp, day):
	if emp.date_of_joining and day < getdate(emp.date_of_joining):
		return False
	if emp.relieving_date and day > getdate(emp.relieving_date):
		return False
	return True


def build_days(emp, start, end, att_map, today=None, schedule=None, holidays=None):
	"""Day-by-day rows for one employee, deriving Absent / Day Off where no record exists."""
	today = getdate(today)
	schedule = schedule or employee_schedule(emp)
	if holidays is None:
		holidays = holidays_between(schedule.holiday_list, start, end)
	treat_missing = cint(get_settings().treat_missing_as_absent)
	days = []
	for day in iter_dates(start, end):
		is_work_day = WEEKDAY_CODES[day.weekday()] in schedule.work_days and day not in holidays
		record = att_map.get((emp.name, day))
		row = {"date": str(day), "is_work_day": is_work_day, "employed": _employed_on(emp, day), "derived": False}
		if record:
			row.update(record)
			row["date"] = str(day)
		elif not row["employed"]:
			row["status"] = None
		elif not is_work_day:
			row.update(status="Holiday" if day in holidays else "Day Off", derived=True)
		elif day <= today and treat_missing:
			row.update(status="Absent", derived=True)
		else:
			row["status"] = None
		days.append(row)
	return days


def summarize_days(days):
	"""Aggregate day rows into the numbers payroll and the UI need."""
	stats = frappe._dict(
		required_days=0, present_days=0, absent_days=0, paid_leave_days=0, unpaid_leave_days=0,
		work_mission_days=0, late_days=0, late_minutes=0, worked_hours=0.0, overtime_hours=0.0,
		day_off_work_days=0,
	)
	for d in days:
		if not d["employed"]:
			continue
		if d["is_work_day"]:
			stats.required_days += 1
		status = d.get("status")
		if status in ("Present", "Work Mission"):
			# Work on a day off is paid as overtime hours, not as an extra present day.
			if d["is_work_day"]:
				stats.present_days += 1
			else:
				stats.day_off_work_days += 1
			if status == "Work Mission":
				stats.work_mission_days += 1
		elif status == "Absent":
			stats.absent_days += 1
		elif status == "On Leave":
			if d.get("leave_type") in PAID_LEAVE_TYPES:
				stats.paid_leave_days += 1
			else:
				stats.unpaid_leave_days += 1
		if cint(d.get("late_minutes")):
			stats.late_days += 1
			stats.late_minutes += cint(d.get("late_minutes"))
		stats.worked_hours += flt(d.get("working_hours"))
		stats.overtime_hours += flt(d.get("overtime_hours"))
	stats.worked_hours = flt(stats.worked_hours, 2)
	stats.overtime_hours = flt(stats.overtime_hours, 2)
	return stats


def employee_month_stats(employee, period=None, today=None):
	"""Stats + day rows for one employee over a month (used by summary and payroll)."""
	emp = frappe.db.get_value("Employee", employee, EMPLOYEE_FIELDS, as_dict=True)
	if not emp:
		frappe.throw(_("الموظف غير موجود"))
	start, end = period_bounds(period)
	att_map = _attendance_map(emp.company, start, end, employee=employee)
	days = build_days(emp, start, end, att_map, today=today)
	return summarize_days(days), days


@frappe.whitelist()
def get_daily(company=None, date=None):
	require_hr()
	company = default_company(company)
	day = getdate(date)
	employees = _active_employees(company, day, day)
	att_map = _attendance_map(company, day, day)
	rows = []
	summary = frappe._dict(total=0, present=0, absent=0, on_leave=0, late=0, day_off=0, unmarked=0)
	for emp in employees:
		if not _employed_on(emp, day):
			continue
		schedule = employee_schedule(emp)
		row = build_days(emp, day, day, att_map, schedule=schedule)[0]
		row.update(employee=emp.name, employee_name=emp.employee_name, designation=emp.designation,
			department=emp.department, image=emp.image,
			shift_start=format_time(schedule.start), shift_end=format_time(schedule.end))
		rows.append(row)
		summary.total += 1
		status = row.get("status")
		if status in ("Present", "Work Mission"):
			summary.present += 1
			if cint(row.get("late_minutes")):
				summary.late += 1
		elif status == "Absent":
			summary.absent += 1
		elif status == "On Leave":
			summary.on_leave += 1
		elif status in ("Day Off", "Holiday"):
			summary.day_off += 1
		else:
			summary.unmarked += 1
	return {"date": str(day), "summary": summary, "rows": rows}


@frappe.whitelist()
def get_monthly(company=None, period=None):
	require_hr()
	company = default_company(company)
	start, end = period_bounds(period)
	att_map = _attendance_map(company, start, end)
	rows = []
	for emp in _active_employees(company, start, end):
		stats = summarize_days(build_days(emp, start, end, att_map))
		rows.append({"employee": emp.name, "employee_name": emp.employee_name,
			"designation": emp.designation, "department": emp.department, **stats})
	return {"period": str(start)[:7], "rows": rows}


@frappe.whitelist()
def get_employee_month(employee, period=None):
	require_hr()
	stats, days = employee_month_stats(employee, period)
	start, _end = period_bounds(period)
	return {"period": str(start)[:7], "stats": stats, "days": days}


ALLOWED_STATUSES = {"Present", "Absent", "Work Mission", "Day Off"}


@frappe.whitelist()
def save_attendance(data):
	require_hr()
	data = parse_json(data)
	if not data.get("employee") or not data.get("attendance_date"):
		frappe.throw(_("الموظف والتاريخ مطلوبان"))
	status = data.get("status") or "Present"
	if status not in ALLOWED_STATUSES:
		frappe.throw(_("الإجازة تُسجّل من قسم الإجازات"))

	name = data.get("name") or frappe.db.get_value(
		"BS Attendance", {"employee": data["employee"], "attendance_date": data["attendance_date"]}, "name"
	)
	doc = frappe.get_doc("BS Attendance", name) if name else frappe.new_doc("BS Attendance")
	if doc.get("source") == "Leave":
		frappe.throw(_("هذا اليوم مرتبط بطلب إجازة معتمد، عدّل الإجازة أولاً"))
	doc.update({
		"employee": data["employee"],
		"attendance_date": data["attendance_date"],
		"status": status,
		"check_in": data.get("check_in") or None,
		"check_out": data.get("check_out") or None,
		"note": data.get("note") or None,
		"source": "Manual",
	})
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "working_hours": doc.working_hours, "late_minutes": doc.late_minutes,
		"overtime_hours": doc.overtime_hours}


@frappe.whitelist()
def mark_present_bulk(company=None, date=None, employees=None):
	"""Mark the given (or all unmarked) employees present with their shift times."""
	require_hr()
	company = default_company(company)
	day = getdate(date)
	selected = set(parse_json(employees) or [])
	created = 0
	for emp in _active_employees(company, day, day):
		if selected and emp.name not in selected:
			continue
		if frappe.db.exists("BS Attendance", {"employee": emp.name, "attendance_date": day}):
			continue
		schedule = employee_schedule(emp)
		if WEEKDAY_CODES[day.weekday()] not in schedule.work_days:
			continue
		doc = frappe.new_doc("BS Attendance")
		doc.update({
			"employee": emp.name,
			"attendance_date": day,
			"status": "Present",
			"check_in": format_time(schedule.start) if schedule.start is not None else None,
			"check_out": format_time(schedule.end) if schedule.end is not None else None,
			"source": "Manual",
		})
		doc.save(ignore_permissions=True)
		created += 1
	return {"created": created}


@frappe.whitelist()
def delete_attendance(name):
	require_hr()
	if frappe.db.get_value("BS Attendance", name, "source") == "Leave":
		frappe.throw(_("هذا اليوم مرتبط بطلب إجازة معتمد، عدّل الإجازة أولاً"))
	frappe.delete_doc("BS Attendance", name, ignore_permissions=True)
	return {"success": True}


@frappe.whitelist()
def get_shift(employee):
	"""Default check-in / check-out times for an employee (own shift, else the settings default)."""
	require_hr()
	schedule = employee_schedule(frappe.get_doc("Employee", employee))
	return {"shift_start": format_time(schedule.start), "shift_end": format_time(schedule.end)}
