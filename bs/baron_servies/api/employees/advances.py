# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Advances (السلف): disbursement, installment schedule, pause, manual payment and closing."""

import math

import frappe
from frappe import _
from frappe.utils import add_months, cint, flt, get_first_day, getdate, nowdate

from bs.baron_servies.api.employees import accounting
from bs.baron_servies.api.employees.common import company_currency, default_company, parse_json, period_bounds, require_hr

LIST_FIELDS = [
	"name", "employee", "employee_name", "posting_date", "amount", "recovered_amount", "remaining_amount",
	"installment_amount", "installments_count", "recovery_method", "status", "start_period",
]


def _get(name, statuses=None):
	doc = frappe.get_doc("BS Employee Advance", name)
	if statuses and doc.status not in statuses:
		frappe.throw(_("لا يمكن تنفيذ العملية على سلفة بحالة {0}").format(doc.status))
	return doc


@frappe.whitelist()
def get_advances(company=None, status=None, employee=None):
	require_hr()
	company = default_company(company)
	filters = {"company": company}
	if status:
		filters["status"] = status
	if employee:
		filters["employee"] = employee
	rows = frappe.get_all("BS Employee Advance", filters=filters, fields=LIST_FIELDS,
		order_by="posting_date desc", limit_page_length=500)

	open_rows = frappe.get_all("BS Employee Advance", filters={"company": company, "status": ["in", ["Active", "Paused"]]},
		fields=["amount", "remaining_amount"])
	start, end = period_bounds(None)
	deducted = frappe.db.sql(
		"""select coalesce(sum(r.amount), 0) from `tabBS Advance Repayment` r
		join `tabBS Employee Advance` a on a.name = r.parent
		where a.company = %s and r.posting_date between %s and %s""",
		(company, start, end),
	)[0][0]
	summary = {
		"open_total": flt(sum(flt(r.amount) for r in open_rows), 2),
		"deducted_this_month": flt(deducted, 2),
		"remaining": flt(sum(flt(r.remaining_amount) for r in open_rows), 2),
		"open_count": len(open_rows),
	}
	return {"rows": rows, "summary": summary, "currency": company_currency(company)}


def schedule(doc):
	"""Past repayments + projected upcoming installments."""
	rows = [
		{"period": str(r.period or r.posting_date)[:7], "date": str(r.posting_date), "amount": flt(r.amount),
			"source": r.source, "status": "Paid", "payroll_entry": r.payroll_entry, "journal_entry": r.journal_entry}
		for r in sorted(doc.repayments, key=lambda r: getdate(r.posting_date))
	]
	if doc.status in ("Active", "Paused") and doc.recovery_method != "Manual" and flt(doc.remaining_amount) > 0:
		paid_periods = {getdate(r.period) for r in doc.repayments if r.source == "Payroll" and r.period}
		period = max(get_first_day(getdate(doc.start_period)), get_first_day(getdate(nowdate())))
		while period in paid_periods:
			period = add_months(period, 1)
		remaining = flt(doc.remaining_amount)
		step = flt(doc.installment_amount) or remaining
		for _i in range(60):
			if remaining <= 0:
				break
			amount = min(step, remaining)
			rows.append({"period": str(period)[:7], "amount": flt(amount, 2), "source": "Payroll",
				"status": "Paused" if doc.status == "Paused" else "Upcoming"})
			remaining = flt(remaining - amount, 2)
			period = add_months(period, 1)
	return rows


@frappe.whitelist()
def get_advance(name):
	require_hr()
	doc = frappe.get_doc("BS Employee Advance", name)
	data = doc.as_dict()
	data["schedule"] = schedule(doc)
	data["modes_of_payment"] = frappe.get_all("Mode of Payment", filters={"enabled": 1}, pluck="name", order_by="name")
	data["default_mode_of_payment"] = accounting.resolve_accounts(doc.company, doc.employee).mode_of_payment
	return data


@frappe.whitelist()
def get_form_options(company=None):
	require_hr()
	company = default_company(company)
	return {
		"modes_of_payment": frappe.get_all("Mode of Payment", filters={"enabled": 1}, pluck="name", order_by="name"),
		"default_mode_of_payment": accounting.resolve_accounts(company).mode_of_payment,
	}


@frappe.whitelist()
def create_advance(data):
	require_hr()
	data = parse_json(data)
	for field in ("employee", "posting_date", "amount"):
		if not data.get(field):
			frappe.throw(_("يرجى تعبئة الحقول المطلوبة"))
	doc = frappe.new_doc("BS Employee Advance")
	doc.update({
		"employee": data["employee"],
		"posting_date": data["posting_date"],
		"amount": flt(data["amount"]),
		"mode_of_payment": data.get("mode_of_payment"),
		"recovery_method": data.get("recovery_method") or "Installments",
		"installment_amount": flt(data.get("installment_amount")),
		"installments_count": cint(data.get("installments_count")),
		"start_period": data.get("start_period") or data["posting_date"],
		"note": data.get("note"),
		"status": "Active",
	})
	doc.insert(ignore_permissions=True)
	doc.db_set("journal_entry", accounting.make_advance_je(doc))
	return {"name": doc.name}


@frappe.whitelist()
def set_paused(name, paused):
	require_hr()
	doc = _get(name, ("Active", "Paused"))
	doc.status = "Paused" if cint(paused) else "Active"
	doc.save(ignore_permissions=True)
	return get_advance(name)


@frappe.whitelist()
def update_installment(name, installment_amount=None, installments_count=None, recovery_method=None):
	"""Change how the remaining balance is recovered; counts apply to the remaining balance."""
	require_hr()
	doc = _get(name, ("Active", "Paused"))
	if recovery_method:
		doc.recovery_method = recovery_method
	if doc.recovery_method == "Installments":
		if cint(installments_count) > 0:
			installment_amount = math.ceil(flt(doc.remaining_amount) * 100 / cint(installments_count)) / 100
		if flt(installment_amount) <= 0:
			frappe.throw(_("يرجى تحديد قيمة القسط أو عدد الأقساط"))
		doc.installment_amount = flt(installment_amount, 2)
	doc.save(ignore_permissions=True)
	return get_advance(name)


@frappe.whitelist()
def record_payment(name, amount, mode_of_payment=None, posting_date=None, note=None):
	"""Employee pays back part of the advance directly (cash / bank)."""
	require_hr()
	doc = _get(name, ("Active", "Paused"))
	amount = flt(amount, 2)
	if amount <= 0 or amount > flt(doc.remaining_amount):
		frappe.throw(_("المبلغ يجب أن يكون بين 0 والمتبقي ({0})").format(doc.remaining_amount))
	mode_of_payment = mode_of_payment or accounting.resolve_accounts(doc.company, doc.employee).mode_of_payment
	je = accounting.make_advance_repayment_je(doc, amount, mode_of_payment, posting_date or nowdate())
	doc.append("repayments", {"posting_date": posting_date or nowdate(), "amount": amount, "source": "Manual",
		"journal_entry": je, "note": note})
	doc.save(ignore_permissions=True)
	return get_advance(name)


@frappe.whitelist()
def close_advance(name, note=None):
	"""Stop the advance; any unrecovered balance is written off to salary expense."""
	require_hr()
	doc = _get(name, ("Active", "Paused", "Completed"))
	remaining = flt(doc.remaining_amount)
	if remaining > 0:
		je = accounting.make_advance_write_off_je(doc, remaining, nowdate())
		doc.append("repayments", {"posting_date": nowdate(), "amount": remaining, "source": "Write Off",
			"journal_entry": je, "note": note or _("شطب عند الإغلاق")})
	doc.status = "Closed"
	doc.save(ignore_permissions=True)
	return get_advance(name)


@frappe.whitelist()
def cancel_advance(name):
	"""Undo a mistaken advance that has no repayments yet (cancels its journal entry)."""
	require_hr()
	doc = _get(name)
	if doc.repayments:
		frappe.throw(_("لا يمكن إلغاء سلفة عليها أقساط مستردة — استخدم الإغلاق"))
	from bs.baron_servies.api.employees.payroll import build_entry

	accounting.cancel_journal_entry(doc.journal_entry)
	draft_entries = set(frappe.get_all("BS Payroll Line", filters={"advance": name, "parenttype": "BS Payroll Entry"}, pluck="parent"))
	frappe.delete_doc("BS Employee Advance", name, ignore_permissions=True, force=True)
	# Drafts that already listed an installment for this advance are rebuilt without it.
	for entry_name in draft_entries:
		entry = frappe.get_doc("BS Payroll Entry", entry_name)
		if entry.status == "Draft":
			build_entry(entry)
			entry.save(ignore_permissions=True)
	return {"success": True}
