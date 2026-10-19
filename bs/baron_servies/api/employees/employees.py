# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Employees (الموظفون): list, profile, save and the unified employee summary."""

import frappe
from frappe import _
from frappe.utils import flt

from bs.baron_servies.api.employees.attendance import employee_month_stats
from bs.baron_servies.api.employees.common import (
	company_currency,
	default_company,
	employees_on_leave,
	format_time,
	leave_balance,
	parse_json,
	pay_rate_label,
	period_bounds,
	require_hr,
)

LIST_FIELDS = [
	"name", "employee_name", "designation", "department", "branch", "status", "image",
	"cell_number", "date_of_joining", "bs_pay_type", "bs_monthly_salary", "bs_hourly_rate",
	"bs_daily_rate",
]

# Fields the Baron form may write; everything else on Employee is left untouched.
EDITABLE_FIELDS = [
	"employee_name", "employee_number", "cell_number", "bs_national_id", "date_of_birth", "gender",
	"current_address", "image",
	"date_of_joining", "designation", "department", "branch", "reports_to", "bs_employee_type",
	"bs_pay_type", "bs_monthly_salary", "bs_hourly_rate", "bs_daily_rate", "bs_daily_hours",
	"bs_work_days", "bs_shift_start", "bs_shift_end", "bs_grace_minutes", "bs_annual_leave_days",
	"holiday_list",
	"bs_cost_center", "bs_salary_expense_account", "salary_mode", "bank_name", "bank_ac_no",
	"status", "relieving_date", "reason_for_leaving",
]

TIME_FIELDS = ("bs_shift_start", "bs_shift_end")


@frappe.whitelist()
def get_employees(company=None):
	require_hr()
	company = default_company(company)
	rows = frappe.get_all("Employee", filters={"company": company}, fields=LIST_FIELDS,
		order_by="employee_name asc")
	on_leave = employees_on_leave(company)
	counts = {"all": 0, "Active": 0, "On Leave": 0, "Suspended": 0, "Left": 0}
	for row in rows:
		row.pay_amount, row.pay_unit = pay_rate_label(row)
		row.display_status = row.status
		if row.status == "Inactive":
			row.display_status = "Suspended"
		if row.status == "Active" and row.name in on_leave:
			row.display_status = "On Leave"
		counts["all"] += 1
		counts[row.display_status] = counts.get(row.display_status, 0) + 1
	return {"rows": rows, "counts": counts, "currency": company_currency(company)}


@frappe.whitelist()
def get_lookups(company=None):
	require_hr()
	company = default_company(company)
	dept_filters = {"company": company} if frappe.get_meta("Department").has_field("company") else {}
	return {
		"company": company,
		"currency": company_currency(company),
		"departments": frappe.get_all("Department", filters={**dept_filters, "is_group": 0}, pluck="name", order_by="name"),
		"designations": frappe.get_all("Designation", pluck="name", order_by="name"),
		"branches": frappe.get_all("Branch", pluck="name", order_by="name"),
		"genders": frappe.get_all("Gender", pluck="name", order_by="name"),
		"holiday_lists": frappe.get_all("Holiday List", pluck="name", order_by="name"),
		"managers": frappe.get_all("Employee", filters={"company": company, "status": "Active"},
			fields=["name", "employee_name"], order_by="employee_name"),
		"cost_centers": frappe.get_all("Cost Center", filters={"company": company, "is_group": 0},
			pluck="name", order_by="name"),
		"expense_accounts": frappe.get_all("Account",
			filters={"company": company, "is_group": 0, "root_type": "Expense"}, pluck="name", order_by="name"),
	}


@frappe.whitelist()
def get_employee(name):
	require_hr()
	doc = frappe.get_doc("Employee", name)
	data = {f: doc.get(f) for f in EDITABLE_FIELDS}
	for f in TIME_FIELDS:
		data[f] = format_time(data[f])
	data.update(name=doc.name, company=doc.company)
	data["pay_amount"], data["pay_unit"] = pay_rate_label(doc)
	# The PIN itself is never sent back — only whether one is set.
	data["has_attendance_pin"] = bool(doc.get("bs_attendance_pin"))
	return data


@frappe.whitelist()
def save_employee(data):
	require_hr()
	data = parse_json(data)
	full_name = (data.get("employee_name") or "").strip()
	if not full_name:
		frappe.throw(_("اسم الموظف مطلوب"))
	if not data.get("date_of_joining"):
		frappe.throw(_("تاريخ بدء العمل مطلوب"))
	if data.get("status") == "Left" and not data.get("relieving_date"):
		frappe.throw(_("تاريخ انتهاء العمل مطلوب عند إنهاء الخدمة"))

	if data.get("name"):
		doc = frappe.get_doc("Employee", data["name"])
	else:
		doc = frappe.new_doc("Employee")
		doc.company = default_company(data.get("company"))

	for field in EDITABLE_FIELDS:
		if field in data and field != "employee_name":
			value = data[field]
			doc.set(field, None if value == "" else value)

	pin = str(data.get("bs_attendance_pin") or "").strip()
	if pin:
		if not pin.isdigit() or not 4 <= len(pin) <= 8:
			frappe.throw(_("رمز الدخول يجب أن يكون من 4 إلى 8 أرقام"))
		doc.bs_attendance_pin = pin
	elif data.get("clear_attendance_pin"):
		doc.bs_attendance_pin = None

	# ERPNext builds employee_name from the name parts; keep the whole name in first_name.
	doc.first_name = full_name
	doc.middle_name = None
	doc.last_name = None
	if doc.status != "Left":
		doc.relieving_date = None
		doc.reason_for_leaving = None

	# The Baron form only asks for name + start date; ERPNext also demands gender / birth date.
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def get_employee_summary(name, period=None):
	"""Everything the employee page needs about the current month in one call."""
	require_hr()
	emp = frappe.get_doc("Employee", name)
	start, _end = period_bounds(period)
	stats, _days = employee_month_stats(name, start)
	summary = {
		"period": str(start)[:7],
		"attendance": stats,
		"leave_balance": leave_balance(name, start.year),
		"on_leave_today": name in employees_on_leave(emp.company),
		"currency": company_currency(emp.company),
		"payroll": None,
		"advances_remaining": 0,
	}
	summary.update(_finance_summary(name, start))
	return summary


def _finance_summary(employee, period_start):
	"""Payroll / advances figures — empty until those doctypes exist (phase 2)."""
	out = {}
	if frappe.db.table_exists("BS Payroll Entry"):
		out["payroll"] = frappe.db.get_value("BS Payroll Entry",
			{"employee": employee, "period": period_start},
			["name", "status", "base_amount", "total_earnings", "total_deductions", "total_advances", "net_amount"],
			as_dict=True)
	if frappe.db.table_exists("BS Employee Advance"):
		out["advances_remaining"] = flt(frappe.db.sql(
			"""select coalesce(sum(remaining_amount), 0) from `tabBS Employee Advance`
			where employee=%s and status in ('Active', 'Paused')""", employee)[0][0])
	return out
