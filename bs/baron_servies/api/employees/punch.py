# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Check-in / check-out screen (تسجيل الدخول والخروج) — works like a time clock.

Controls (BS Employee Settings):
- Server time only: the browser's clock is never trusted.
- Optional per-employee PIN.
- Minimum minutes between punches (stops double taps).
- Earliest check-in window before the shift starts.
- Punching on a day off / holiday only when allowed.
- No punching on an approved leave day.
- Overnight shifts: a check-out after midnight closes yesterday's open record.
Every punch is also kept in BS Attendance Log for audit.
"""

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime
from frappe.utils.password import get_decrypted_password

from bs.baron_servies.api.employees.attendance import _active_employees, _employed_on
from bs.baron_servies.api.employees.common import (
	default_company,
	employee_schedule,
	employees_on_leave,
	format_time,
	get_settings,
	require_hr,
	working_dates,
)

OPEN_OVERNIGHT_HOURS = 18  # an open check-in older than this is not closed automatically
DEFAULT_MIN_INTERVAL = 2
DEFAULT_EARLY_WINDOW = 120


def _int_setting(settings, field, default):
	value = settings.get(field)
	return default if value in (None, "") else cint(value)


def _now():
	now = now_datetime()
	return now, now.date(), now.hour * 60 + now.minute


def _today_record(employee, day):
	name = frappe.db.get_value("BS Attendance", {"employee": employee, "attendance_date": day}, "name")
	return frappe.get_doc("BS Attendance", name) if name else None


def _open_overnight_record(employee, now, schedule):
	"""Yesterday's record that is still checked in, for shifts that cross midnight."""
	if schedule.start is None or schedule.end is None or schedule.end >= schedule.start:
		return None
	yesterday = (now - timedelta(days=1)).date()
	rec = _today_record(employee, yesterday)
	if not rec or not rec.check_in or rec.check_out or rec.status != "Present":
		return None
	started = get_datetime(f"{yesterday} {format_time(rec.check_in)}")
	if now - started > timedelta(hours=OPEN_OVERNIGHT_HOURS):
		return None
	return rec


def _state(rec):
	if not rec or rec.get("status") not in ("Present", "Work Mission") or not rec.get("check_in"):
		return "out_none"  # not checked in today
	if not rec.get("check_out"):
		return "in"
	return "done"


def _verify_pin(employee, pin):
	stored = get_decrypted_password("Employee", employee, "bs_attendance_pin", raise_exception=False)
	if not stored:
		frappe.throw(_("لم يُحدَّد رمز دخول لهذا الموظف — حدّده من ملف الموظف"))
	if str(pin or "").strip() != str(stored).strip():
		frappe.throw(_("رمز الدخول غير صحيح"))


@frappe.whitelist()
def get_board(company=None):
	"""Employees with today's punch state + server time for the kiosk clock."""
	require_hr()
	company = default_company(company)
	now, today, _minutes = _now()
	settings = get_settings()
	on_leave = employees_on_leave(company, today)
	rows = []
	for emp in _active_employees(company, today, today):
		if not _employed_on(emp, today):
			continue
		schedule = employee_schedule(emp)
		rec = _open_overnight_record(emp.name, now, schedule) or _today_record(emp.name, today)
		rows.append({
			"employee": emp.name,
			"employee_name": emp.employee_name,
			"designation": emp.designation,
			"image": emp.image,
			"shift_start": format_time(schedule.start),
			"shift_end": format_time(schedule.end),
			"is_work_day": bool(working_dates(emp, today, today, schedule)),
			"on_leave": on_leave.get(emp.name),
			"state": "leave" if emp.name in on_leave else _state(rec),
			"check_in": format_time(rec.check_in) if rec else None,
			"check_out": format_time(rec.check_out) if rec else None,
			"late_minutes": rec.late_minutes if rec else 0,
			"working_hours": rec.working_hours if rec else 0,
		})
	logs = frappe.get_all("BS Attendance Log",
		filters={"company": company, "log_time": [">=", str(today)]},
		fields=["employee_name", "log_type", "log_time"], order_by="log_time desc", limit_page_length=15)
	return {
		"server_time": str(now),
		"date": str(today),
		"require_pin": cint(settings.punch_require_pin),
		"rows": rows,
		"logs": logs,
	}


@frappe.whitelist()
def punch(employee, pin=None):
	"""Record the next punch (IN or OUT) for an employee at the current server time."""
	require_hr()
	settings = get_settings()
	now, today, now_min = _now()

	emp = frappe.get_doc("Employee", employee)
	if emp.status != "Active":
		frappe.throw(_("الموظف غير فعال"))
	if not _employed_on(frappe._dict(date_of_joining=emp.date_of_joining, relieving_date=emp.relieving_date), today):
		frappe.throw(_("الموظف خارج فترة عمله"))
	if cint(settings.punch_require_pin):
		_verify_pin(employee, pin)

	schedule = employee_schedule(emp)
	rec = _open_overnight_record(employee, now, schedule)
	if not rec:
		if employee in employees_on_leave(emp.company, today):
			frappe.throw(_("الموظف في إجازة معتمدة اليوم"))
		rec = _today_record(employee, today)

	if rec and rec.source == "Leave":
		frappe.throw(_("هذا اليوم مرتبط بإجازة معتمدة"))

	state = _state(rec)
	if state == "done":
		frappe.throw(_("تم تسجيل الدخول والخروج اليوم — لتعديل الأوقات استخدم شاشة الدوام"))

	time_str = now.strftime("%H:%M:%S")
	min_interval = _int_setting(settings, "punch_min_interval_minutes", DEFAULT_MIN_INTERVAL)

	if state == "in":
		started = get_datetime(f"{rec.attendance_date} {format_time(rec.check_in)}")
		if min_interval and now - started < timedelta(minutes=min_interval):
			frappe.throw(_("تم تسجيل الدخول قبل أقل من {0} دقيقة").format(min_interval))
		rec.check_out = time_str
		log_type = "OUT"
	else:
		is_work_day = bool(working_dates(emp, today, today, schedule))
		if not is_work_day and not cint(settings.punch_allow_day_off):
			frappe.throw(_("اليوم ليس يوم عمل لهذا الموظف"))
		early = _int_setting(settings, "punch_early_window_minutes", DEFAULT_EARLY_WINDOW)
		if is_work_day and early and schedule.start is not None and now_min < schedule.start - early:
			frappe.throw(_("لا يمكن تسجيل الدخول قبل {0} دقيقة من بداية الدوام ({1})").format(early, format_time(schedule.start)))
		rec = rec or frappe.new_doc("BS Attendance")
		rec.update({
			"employee": employee,
			"company": emp.company,
			"attendance_date": today,
			"status": "Present",
			"check_in": time_str,
			"check_out": None,
		})
		log_type = "IN"

	rec.source = "Punch"
	rec.save(ignore_permissions=True)

	frappe.get_doc({
		"doctype": "BS Attendance Log",
		"employee": employee,
		"company": emp.company,
		"log_time": now,
		"log_type": log_type,
		"attendance": rec.name,
		"recorded_by": frappe.session.user,
		"ip_address": getattr(frappe.local, "request_ip", None),
	}).insert(ignore_permissions=True)

	return {
		"employee": employee,
		"employee_name": emp.employee_name,
		"log_type": log_type,
		"time": time_str[:5],
		"late_minutes": rec.late_minutes,
		"working_hours": rec.working_hours,
		"overtime_hours": rec.overtime_hours,
	}
