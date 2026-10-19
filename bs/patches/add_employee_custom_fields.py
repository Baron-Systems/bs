# -*- coding: utf-8 -*-
# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Patch: Add Baron Service pay/schedule fields to Employee and create the HR role.

Idempotent — existing custom fields are skipped.
"""

import frappe

HR_ROLE = "BS HR Manager"

CUSTOM_FIELDS = [
	{"fieldname": "bs_tab", "label": "Baron Service", "fieldtype": "Tab Break", "insert_after": "old_parent"},
	{"fieldname": "bs_national_id", "label": "National ID", "fieldtype": "Data", "insert_after": "bs_tab"},
	{
		"fieldname": "bs_employee_type",
		"label": "Employee Type",
		"fieldtype": "Select",
		"options": "\nFull Time\nPart Time\nTemporary\nSeasonal",
		"default": "Full Time",
		"insert_after": "bs_national_id",
	},
	{"fieldname": "bs_pay_section", "label": "Pay", "fieldtype": "Section Break", "insert_after": "bs_employee_type"},
	{
		"fieldname": "bs_pay_type",
		"label": "Pay Type",
		"fieldtype": "Select",
		"options": "Monthly\nHourly\nDaily",
		"default": "Monthly",
		"insert_after": "bs_pay_section",
	},
	{
		"fieldname": "bs_monthly_salary",
		"label": "Monthly Salary",
		"fieldtype": "Currency",
		"depends_on": "eval:doc.bs_pay_type=='Monthly'",
		"insert_after": "bs_pay_type",
	},
	{
		"fieldname": "bs_hourly_rate",
		"label": "Hourly Rate",
		"fieldtype": "Currency",
		"depends_on": "eval:doc.bs_pay_type=='Hourly'",
		"insert_after": "bs_monthly_salary",
	},
	{
		"fieldname": "bs_daily_rate",
		"label": "Daily Rate",
		"fieldtype": "Currency",
		"depends_on": "eval:doc.bs_pay_type=='Daily'",
		"insert_after": "bs_hourly_rate",
	},
	{"fieldname": "bs_daily_hours", "label": "Daily Hours", "fieldtype": "Float", "default": "8", "insert_after": "bs_daily_rate"},
	{"fieldname": "bs_pay_cb", "fieldtype": "Column Break", "insert_after": "bs_daily_hours"},
	{"fieldname": "bs_cost_center", "label": "Cost Center", "fieldtype": "Link", "options": "Cost Center", "insert_after": "bs_pay_cb"},
	{
		"fieldname": "bs_salary_expense_account",
		"label": "Salary Expense Account",
		"fieldtype": "Link",
		"options": "Account",
		"insert_after": "bs_cost_center",
	},
	{"fieldname": "bs_schedule_section", "label": "Schedule", "fieldtype": "Section Break", "insert_after": "bs_salary_expense_account"},
	{
		"fieldname": "bs_work_days",
		"label": "Work Days",
		"fieldtype": "Data",
		"description": "Comma separated: Sat,Sun,Mon,Tue,Wed,Thu",
		"insert_after": "bs_schedule_section",
	},
	{"fieldname": "bs_shift_start", "label": "Shift Start", "fieldtype": "Time", "insert_after": "bs_work_days"},
	{"fieldname": "bs_shift_end", "label": "Shift End", "fieldtype": "Time", "insert_after": "bs_shift_start"},
	{"fieldname": "bs_schedule_cb", "fieldtype": "Column Break", "insert_after": "bs_shift_end"},
	{"fieldname": "bs_grace_minutes", "label": "Grace Minutes", "fieldtype": "Int", "insert_after": "bs_schedule_cb"},
	{"fieldname": "bs_annual_leave_days", "label": "Annual Leave Days", "fieldtype": "Float", "insert_after": "bs_grace_minutes"},
	{
		"fieldname": "bs_attendance_pin",
		"label": "Attendance PIN",
		"fieldtype": "Password",
		"length": 12,
		"description": "Used on the Baron check-in / check-out screen when a PIN is required",
		"insert_after": "bs_annual_leave_days",
	},
]


def execute():
	if not frappe.db.exists("Role", HR_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": HR_ROLE, "desk_access": 1}).insert(ignore_permissions=True)

	for cf in CUSTOM_FIELDS:
		if frappe.db.get_value("Custom Field", {"dt": "Employee", "fieldname": cf["fieldname"]}, "name"):
			continue
		frappe.get_doc({"doctype": "Custom Field", "dt": "Employee", "module": "Baron servies", **cf}).insert(
			ignore_permissions=True
		)

	frappe.db.commit()
	frappe.clear_cache(doctype="Employee")
