# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Employees settings (قواعد الحساب والحسابات المحاسبية لكل شركة)."""

import frappe

from bs.baron_servies.api.employees.common import (
	SETTINGS_DOCTYPE,
	format_time,
	is_hr_user,
	parse_json,
	require_hr,
)

RULE_FIELDS = [
	"day_rate_basis", "overtime_multiplier", "late_deduction_enabled", "treat_missing_as_absent",
	"default_work_days", "default_shift_start", "default_shift_end", "default_grace_minutes",
	"default_daily_hours", "default_annual_leave_days",
	"punch_require_pin", "punch_min_interval_minutes", "punch_early_window_minutes", "punch_allow_day_off",
	"count_early_arrival_as_overtime",
]
ACCOUNT_FIELDS = [
	"company", "salary_expense_account", "payroll_payable_account", "employee_advance_account",
	"cost_center", "default_mode_of_payment",
]


@frappe.whitelist()
def can_manage():
	return {"allowed": is_hr_user()}


@frappe.whitelist()
def get_employee_settings():
	require_hr()
	doc = frappe.get_single(SETTINGS_DOCTYPE)
	data = {f: doc.get(f) for f in RULE_FIELDS}
	for f in ("default_shift_start", "default_shift_end"):
		data[f] = format_time(data[f])
	data["company_accounts"] = [{f: row.get(f) for f in ACCOUNT_FIELDS} for row in doc.company_accounts]
	return data


@frappe.whitelist()
def get_account_options(company):
	require_hr()

	def accounts(**filters):
		return frappe.get_all("Account", filters={"company": company, "is_group": 0, **filters},
			pluck="name", order_by="name")

	return {
		"expense": accounts(root_type="Expense"),
		"liability": accounts(root_type="Liability"),
		"asset": accounts(root_type="Asset"),
		"cost_centers": frappe.get_all("Cost Center", filters={"company": company, "is_group": 0},
			pluck="name", order_by="name"),
		"modes_of_payment": frappe.get_all("Mode of Payment", filters={"enabled": 1}, pluck="name", order_by="name"),
	}


@frappe.whitelist()
def save_employee_settings(data):
	require_hr()
	data = parse_json(data)
	doc = frappe.get_single(SETTINGS_DOCTYPE)
	for f in RULE_FIELDS:
		if f in data:
			doc.set(f, data[f])
	if "company_accounts" in data:
		doc.set("company_accounts", [])
		for row in data["company_accounts"] or []:
			if row.get("company"):
				doc.append("company_accounts", {f: row.get(f) or None for f in ACCOUNT_FIELDS})
	doc.save(ignore_permissions=True)
	return {"success": True}


@frappe.whitelist()
def create_default_accounts(company):
	"""Create the payroll ledgers (if missing) and link them in the company's settings row."""
	require_hr()
	from bs.baron_servies.api.employees.accounting import create_default_accounts as _create

	accounts = _create(company)
	doc = frappe.get_single(SETTINGS_DOCTYPE)
	row = next((r for r in doc.company_accounts if r.company == company), None) or doc.append(
		"company_accounts", {"company": company}
	)
	for field, account in accounts.items():
		if not row.get(field):
			row.set(field, account)
	if not row.cost_center:
		row.cost_center = frappe.get_cached_value("Company", company, "cost_center")
	if not row.default_mode_of_payment and frappe.db.exists("Mode of Payment Account", {"parent": "Cash", "company": company}):
		row.default_mode_of_payment = "Cash"
	doc.save(ignore_permissions=True)
	return {"accounts": accounts}
