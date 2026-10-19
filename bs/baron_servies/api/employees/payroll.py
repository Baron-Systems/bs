# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Payroll (الاستحقاقات): monthly entries built from attendance, leaves and advances."""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate

from bs.baron_servies.api.employees import accounting
from bs.baron_servies.api.employees.attendance import _active_employees, employee_month_stats
from bs.baron_servies.api.employees.common import (
	company_currency,
	default_company,
	get_settings,
	parse_json,
	period_bounds,
	require_hr,
	working_dates,
)
from bs.baron_servies.api.employees.payroll_calc import PayInputs, cap_installments, compute

EARNING_COMPONENTS = {"Overtime", "Bonus", "Commission", "Transport Allowance", "Food Allowance", "Phone Allowance", "Other Earning"}
DEDUCTION_COMPONENTS = {"Absence", "Late", "Unpaid Leave", "Administrative", "Other Deduction"}

LIST_FIELDS = [
	"name", "employee", "employee_name", "status", "pay_type", "base_amount", "total_earnings",
	"total_deductions", "total_advances", "net_amount", "accrual_journal_entry", "payment_journal_entry",
]


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------

def _get_entry(name, statuses=None):
	doc = frappe.get_doc("BS Payroll Entry", name)
	if statuses and doc.status not in statuses:
		frappe.throw(_("لا يمكن تنفيذ العملية على استحقاق بحالة {0}").format(doc.status))
	return doc


def _open_advances(employee, period, exclude_entry=None):
	"""[(advance_doc, due_amount)] for active advances owing an installment this period."""
	result = []
	for name in frappe.get_all("BS Employee Advance", filters={"employee": employee, "status": "Active"},
			pluck="name", order_by="posting_date asc"):
		adv = frappe.get_doc("BS Employee Advance", name)
		due = adv.due_for(period, exclude_entry=exclude_entry)
		if due > 0:
			result.append((adv, due))
	return result


def build_entry(doc):
	"""(Re)compute a draft entry: snapshot pay data, attendance, auto lines and advances.

	Manual lines (is_auto = 0) are kept untouched.
	"""
	emp = frappe.get_doc("Employee", doc.employee)
	settings = get_settings()
	start, end = period_bounds(doc.period)
	stats, _days = employee_month_stats(doc.employee, start)

	doc.company = emp.company
	doc.currency = company_currency(emp.company)
	doc.pay_type = emp.get("bs_pay_type") or "Monthly"
	doc.monthly_salary = flt(emp.get("bs_monthly_salary"))
	doc.hourly_rate = flt(emp.get("bs_hourly_rate"))
	doc.daily_rate = flt(emp.get("bs_daily_rate"))
	doc.daily_hours = flt(emp.get("bs_daily_hours")) or flt(settings.default_daily_hours) or 8
	doc.month_working_days = len(working_dates(emp, start, end))
	for key in ("required_days", "present_days", "absent_days", "paid_leave_days", "unpaid_leave_days",
			"late_minutes", "worked_hours", "overtime_hours"):
		doc.set(key, stats[key])

	result = compute(PayInputs(
		pay_type=doc.pay_type,
		monthly_salary=doc.monthly_salary,
		hourly_rate=doc.hourly_rate,
		daily_rate=doc.daily_rate,
		daily_hours=doc.daily_hours,
		day_rate_basis=settings.day_rate_basis or "Working Days",
		overtime_multiplier=flt(settings.overtime_multiplier) or 1,
		late_deduction_enabled=bool(cint(settings.late_deduction_enabled)),
		month_working_days=doc.month_working_days,
		**{k: stats[k] for k in ("required_days", "present_days", "absent_days", "paid_leave_days",
			"unpaid_leave_days", "late_minutes", "worked_hours", "overtime_hours")},
	))
	doc.day_rate = result.day_rate
	doc.hour_rate = result.hour_rate
	doc.base_amount = result.base_amount
	doc.base_quantity = result.base_quantity
	doc.base_unit = result.base_unit

	manual = [l.as_dict() for l in doc.lines if not cint(l.is_auto)]
	doc.set("lines", [])
	for line in result.lines + [_clean_line(l) for l in manual]:
		doc.append("lines", line)

	# Advances last, capped so net never goes negative.
	doc.update_totals()
	due = _open_advances(doc.employee, start, exclude_entry=doc.name)
	for adv_name, amount in cap_installments(doc.gross_amount, [(adv.name, amt) for adv, amt in due]):
		doc.append("lines", {"line_type": "Advance", "component": "Advance Installment", "amount": amount,
			"advance": adv_name, "is_auto": 1, "note": adv_name})
	doc.update_totals()
	return doc


def _clean_line(line):
	return {k: line.get(k) for k in ("line_type", "component", "quantity", "amount", "note", "is_auto", "advance")}


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_period(company=None, period=None):
	require_hr()
	company = default_company(company)
	start, end = period_bounds(period)
	rows = frappe.get_all("BS Payroll Entry", filters={"company": company, "period": start},
		fields=LIST_FIELDS, order_by="employee_name asc")
	missing = [
		{"employee": e.name, "employee_name": e.employee_name}
		for e in _active_employees(company, start, end)
		if e.name not in {r.employee for r in rows}
	]
	summary = {
		"employees": len(rows),
		"base": flt(sum(flt(r.base_amount) for r in rows), 2),
		"earnings": flt(sum(flt(r.total_earnings) for r in rows), 2),
		"deductions": flt(sum(flt(r.total_deductions) for r in rows), 2),
		"advances": flt(sum(flt(r.total_advances) for r in rows), 2),
		"net": flt(sum(flt(r.net_amount) for r in rows), 2),
		"by_status": {s: sum(1 for r in rows if r.status == s) for s in ("Draft", "Approved", "Paid")},
	}
	return {"period": str(start)[:7], "rows": rows, "summary": summary, "missing": missing,
		"currency": company_currency(company)}


@frappe.whitelist()
def get_entry(name):
	require_hr()
	doc = frappe.get_doc("BS Payroll Entry", name)
	data = doc.as_dict()
	data["lines"] = [l.as_dict() for l in doc.lines]
	data["period_label"] = str(doc.period)[:7]
	data["modes_of_payment"] = frappe.get_all("Mode of Payment", filters={"enabled": 1}, pluck="name", order_by="name")
	data["default_mode_of_payment"] = accounting.resolve_accounts(doc.company, doc.employee).mode_of_payment
	return data


@frappe.whitelist()
def get_employee_entries(employee, limit=12):
	require_hr()
	return frappe.get_all("BS Payroll Entry", filters={"employee": employee},
		fields=LIST_FIELDS + ["period"], order_by="period desc", limit_page_length=cint(limit) or 12)


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------

@frappe.whitelist()
def generate_period(company=None, period=None, employees=None):
	"""Create draft entries for active employees that don't have one for the period yet."""
	require_hr()
	company = default_company(company)
	start, end = period_bounds(period)
	selected = set(parse_json(employees) or [])
	existing = set(frappe.get_all("BS Payroll Entry", filters={"company": company, "period": start}, pluck="employee"))
	created, errors = [], []
	for emp in _active_employees(company, start, end):
		if emp.name in existing or (selected and emp.name not in selected):
			continue
		frappe.db.savepoint("bs_payroll_generate")
		try:
			doc = frappe.new_doc("BS Payroll Entry")
			doc.update({"employee": emp.name, "company": company, "period": start, "status": "Draft"})
			build_entry(doc)
			doc.insert(ignore_permissions=True)
			created.append(doc.name)
		except Exception as e:
			frappe.db.rollback(save_point="bs_payroll_generate")
			frappe.clear_last_message()
			errors.append({"employee": emp.employee_name, "error": str(e)})
	return {"created": len(created), "errors": errors}


@frappe.whitelist()
def recalculate(name):
	require_hr()
	doc = _get_entry(name, ("Draft",))
	build_entry(doc)
	doc.save(ignore_permissions=True)
	return get_entry(doc.name)


@frappe.whitelist()
def recalculate_period(company=None, period=None):
	require_hr()
	company = default_company(company)
	start, _end = period_bounds(period)
	count = 0
	for name in frappe.get_all("BS Payroll Entry", filters={"company": company, "period": start, "status": "Draft"}, pluck="name"):
		doc = frappe.get_doc("BS Payroll Entry", name)
		build_entry(doc)
		doc.save(ignore_permissions=True)
		count += 1
	return {"updated": count}


@frappe.whitelist()
def add_line(name, line_type, component, amount, note=None, quantity=None):
	require_hr()
	if line_type == "Earning" and component not in EARNING_COMPONENTS:
		frappe.throw(_("نوع الإضافة غير صحيح"))
	if line_type == "Deduction" and component not in DEDUCTION_COMPONENTS:
		frappe.throw(_("نوع الخصم غير صحيح"))
	if line_type not in ("Earning", "Deduction"):
		frappe.throw(_("نوع السطر غير صحيح"))
	if flt(amount) <= 0:
		frappe.throw(_("القيمة يجب أن تكون أكبر من صفر"))
	doc = _get_entry(name, ("Draft",))
	doc.append("lines", {"line_type": line_type, "component": component, "amount": flt(amount, 2),
		"note": note, "quantity": flt(quantity) or None, "is_auto": 0})
	build_entry(doc)  # re-cap advances against the new gross
	doc.save(ignore_permissions=True)
	return get_entry(doc.name)


@frappe.whitelist()
def remove_line(name, row_name):
	require_hr()
	doc = _get_entry(name, ("Draft",))
	row = next((l for l in doc.lines if l.name == row_name), None)
	if not row:
		frappe.throw(_("السطر غير موجود"))
	if cint(row.is_auto):
		frappe.throw(_("السطور التلقائية تُحسب من الدوام والسلف — عدّل المصدر ثم أعد الحساب"))
	doc.remove(row)
	build_entry(doc)
	doc.save(ignore_permissions=True)
	return get_entry(doc.name)


@frappe.whitelist()
def save_note(name, note=None):
	require_hr()
	frappe.db.set_value("BS Payroll Entry", name, "note", note)
	return {"success": True}


def _approve(doc):
	build_entry(doc)
	if flt(doc.net_amount) < 0:
		frappe.throw(_("صافي الاستحقاق سالب — راجع الخصومات"))
	doc.status = "Approved"
	doc.save(ignore_permissions=True)
	doc.accrual_journal_entry = accounting.make_accrual_je(doc)
	doc.db_set("accrual_journal_entry", doc.accrual_journal_entry)
	for line in doc.lines:
		if line.line_type == "Advance" and line.advance:
			adv = frappe.get_doc("BS Employee Advance", line.advance)
			adv.append("repayments", {"posting_date": doc.period_end, "period": doc.period, "amount": line.amount,
				"source": "Payroll", "payroll_entry": doc.name, "journal_entry": doc.accrual_journal_entry})
			adv.save(ignore_permissions=True)


@frappe.whitelist()
def approve(name):
	require_hr()
	doc = _get_entry(name, ("Draft",))
	_approve(doc)
	return get_entry(doc.name)


@frappe.whitelist()
def approve_period(company=None, period=None):
	"""Approve every draft of a period; each entry is its own transaction step."""
	require_hr()
	company = default_company(company)
	start, _end = period_bounds(period)
	approved, errors = 0, []
	for name in frappe.get_all("BS Payroll Entry", filters={"company": company, "period": start, "status": "Draft"}, pluck="name"):
		frappe.db.savepoint("bs_payroll_approve")
		try:
			_approve(frappe.get_doc("BS Payroll Entry", name))
			approved += 1
		except Exception as e:
			frappe.db.rollback(save_point="bs_payroll_approve")
			frappe.clear_last_message()
			errors.append({"name": name, "employee": frappe.db.get_value("BS Payroll Entry", name, "employee_name"), "error": str(e)})
	return {"approved": approved, "errors": errors}


@frappe.whitelist()
def revert_to_draft(name):
	require_hr()
	doc = _get_entry(name, ("Approved",))
	accounting.cancel_journal_entry(doc.accrual_journal_entry)
	for adv_name in {l.advance for l in doc.lines if l.advance}:
		adv = frappe.get_doc("BS Employee Advance", adv_name)
		adv.set("repayments", [r for r in adv.repayments if r.payroll_entry != doc.name])
		adv.save(ignore_permissions=True)
	doc.status = "Draft"
	doc.accrual_journal_entry = None
	doc.save(ignore_permissions=True)
	return get_entry(doc.name)


@frappe.whitelist()
def mark_paid(name, mode_of_payment=None, posting_date=None):
	require_hr()
	doc = _get_entry(name, ("Approved",))
	mode_of_payment = mode_of_payment or accounting.resolve_accounts(doc.company, doc.employee).mode_of_payment
	if flt(doc.net_amount) > 0:
		doc.payment_journal_entry = accounting.make_payment_je(doc, mode_of_payment, posting_date or nowdate())
	doc.mode_of_payment = mode_of_payment
	doc.paid_date = getdate(posting_date or nowdate())
	doc.status = "Paid"
	doc.save(ignore_permissions=True)
	return get_entry(doc.name)


@frappe.whitelist()
def cancel_payment(name):
	require_hr()
	doc = _get_entry(name, ("Paid",))
	accounting.cancel_journal_entry(doc.payment_journal_entry)
	doc.update({"status": "Approved", "payment_journal_entry": None, "paid_date": None, "mode_of_payment": None})
	doc.save(ignore_permissions=True)
	return get_entry(doc.name)


@frappe.whitelist()
def delete_entry(name):
	require_hr()
	_get_entry(name, ("Draft",))
	frappe.delete_doc("BS Payroll Entry", name, ignore_permissions=True)
	return {"success": True}
