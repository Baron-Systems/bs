# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Journal entries for payroll accrual/payment and employee advances."""

import frappe
from frappe import _
from frappe.utils import flt, nowdate

from bs.baron_servies.api.employees.common import company_accounts

PARTY_ACCOUNT_TYPES = ("Receivable", "Payable", "", None)


def resolve_accounts(company, employee=None):
	"""Accounts + cost center for a company, with per-employee overrides."""
	row = company_accounts(company)
	emp = frappe.db.get_value("Employee", employee, ["bs_cost_center", "bs_salary_expense_account"], as_dict=True) if employee else None
	return frappe._dict(
		salary_expense=(emp and emp.bs_salary_expense_account) or row.get("salary_expense_account"),
		payable=row.get("payroll_payable_account"),
		advance=row.get("employee_advance_account"),
		cost_center=(emp and emp.bs_cost_center) or row.get("cost_center")
		or frappe.get_cached_value("Company", company, "cost_center"),
		mode_of_payment=row.get("default_mode_of_payment"),
	)


def require(value, label):
	if not value:
		frappe.throw(_("يرجى تحديد {0} في إعدادات الموظفين").format(label), title=_("إعداد ناقص"))
	return value


def cash_account(mode_of_payment, company):
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account

	if not mode_of_payment:
		frappe.throw(_("يرجى اختيار طريقة الدفع"))
	return get_bank_cash_account(mode_of_payment, company)["account"]


def _row(account, debit=0, credit=0, employee=None, cost_center=None):
	row = {
		"account": account,
		"debit_in_account_currency": flt(debit, 2),
		"credit_in_account_currency": flt(credit, 2),
		"cost_center": cost_center,
	}
	# ERPNext only accepts a party on receivable / payable (or untyped) accounts.
	if employee and frappe.get_cached_value("Account", account, "account_type") in PARTY_ACCOUNT_TYPES:
		row.update(party_type="Employee", party=employee)
	return row


def make_journal_entry(company, posting_date, remark, rows):
	rows = [r for r in rows if r["debit_in_account_currency"] or r["credit_in_account_currency"]]
	if not rows:
		return None
	je = frappe.new_doc("Journal Entry")
	je.update({
		"voucher_type": "Journal Entry",
		"company": company,
		"posting_date": posting_date or nowdate(),
		"user_remark": remark,
	})
	for row in rows:
		je.append("accounts", row)
	je.flags.ignore_permissions = True
	je.insert()
	je.submit()
	return je.name


def cancel_journal_entry(name):
	if not name or not frappe.db.exists("Journal Entry", name):
		return
	je = frappe.get_doc("Journal Entry", name)
	if je.docstatus == 1:
		je.flags.ignore_permissions = True
		je.cancel()


def make_accrual_je(entry):
	"""Dr salary expense (gross) / Cr employee advances (installments) / Cr payroll payable (net)."""
	acc = resolve_accounts(entry.company, entry.employee)
	require(acc.salary_expense, _("حساب مصاريف الرواتب"))
	require(acc.payable, _("حساب رواتب مستحقة"))
	if flt(entry.total_advances):
		require(acc.advance, _("حساب سلف الموظفين"))
	remark = _("استحقاق {0} عن {1} — {2}").format(entry.employee_name, str(entry.period)[:7], entry.name)
	return make_journal_entry(entry.company, entry.period_end, remark, [
		_row(acc.salary_expense, debit=entry.gross_amount, cost_center=acc.cost_center),
		_row(acc.advance, credit=entry.total_advances, employee=entry.employee, cost_center=acc.cost_center) if acc.advance else _empty(),
		_row(acc.payable, credit=entry.net_amount, employee=entry.employee, cost_center=acc.cost_center),
	])


def make_payment_je(entry, mode_of_payment, posting_date=None):
	"""Dr payroll payable / Cr cash or bank."""
	acc = resolve_accounts(entry.company, entry.employee)
	require(acc.payable, _("حساب رواتب مستحقة"))
	cash = cash_account(mode_of_payment, entry.company)
	remark = _("دفع استحقاق {0} عن {1} — {2}").format(entry.employee_name, str(entry.period)[:7], entry.name)
	return make_journal_entry(entry.company, posting_date, remark, [
		_row(acc.payable, debit=entry.net_amount, employee=entry.employee, cost_center=acc.cost_center),
		_row(cash, credit=entry.net_amount, cost_center=acc.cost_center),
	])


def make_advance_je(advance):
	"""Dr employee advances / Cr cash or bank."""
	acc = resolve_accounts(advance.company, advance.employee)
	require(acc.advance, _("حساب سلف الموظفين"))
	cash = cash_account(advance.mode_of_payment, advance.company)
	remark = _("صرف سلفة لـ {0} — {1}").format(advance.employee_name, advance.name)
	return make_journal_entry(advance.company, advance.posting_date, remark, [
		_row(acc.advance, debit=advance.amount, employee=advance.employee, cost_center=acc.cost_center),
		_row(cash, credit=advance.amount, cost_center=acc.cost_center),
	])


def make_advance_repayment_je(advance, amount, mode_of_payment, posting_date=None):
	"""Dr cash or bank / Cr employee advances (employee pays back directly)."""
	acc = resolve_accounts(advance.company, advance.employee)
	require(acc.advance, _("حساب سلف الموظفين"))
	cash = cash_account(mode_of_payment, advance.company)
	remark = _("سداد سلفة من {0} — {1}").format(advance.employee_name, advance.name)
	return make_journal_entry(advance.company, posting_date, remark, [
		_row(cash, debit=amount, cost_center=acc.cost_center),
		_row(acc.advance, credit=amount, employee=advance.employee, cost_center=acc.cost_center),
	])


def make_advance_write_off_je(advance, amount, posting_date=None):
	"""Dr salary expense / Cr employee advances (unrecovered balance absorbed as a staff cost)."""
	acc = resolve_accounts(advance.company, advance.employee)
	require(acc.advance, _("حساب سلف الموظفين"))
	require(acc.salary_expense, _("حساب مصاريف الرواتب"))
	remark = _("شطب رصيد سلفة {0} — {1}").format(advance.employee_name, advance.name)
	return make_journal_entry(advance.company, posting_date, remark, [
		_row(acc.salary_expense, debit=amount, cost_center=acc.cost_center),
		_row(acc.advance, credit=amount, employee=advance.employee, cost_center=acc.cost_center),
	])


def _empty():
	return {"debit_in_account_currency": 0, "credit_in_account_currency": 0}


# ---------------------------------------------------------------------------
# Default account creation (settings page helper)
# ---------------------------------------------------------------------------

DEFAULT_ACCOUNTS = {
	"salary_expense_account": {
		"account_name": "رواتب وأجور", "root_type": "Expense", "account_type": "",
		"siblings": ["%salar%", "%wage%", "%رواتب%", "%أجور%"], "groups": ["%indirect%", "%غير مباشر%"],
	},
	"payroll_payable_account": {
		"account_name": "رواتب مستحقة الدفع", "root_type": "Liability", "account_type": "Payable",
		"siblings": ["%payroll%", "%رواتب%"], "groups": [], "hint": "default_payable_account",
	},
	"employee_advance_account": {
		"account_name": "سلف الموظفين", "root_type": "Asset", "account_type": "Receivable",
		"siblings": ["%employee advance%", "%سلف%"], "groups": ["%advances%", "%سلفيات%", "%سلف%"],
		"hint": "default_receivable_account",
	},
}


def _parent_group(company, spec):
	"""Pick a sensible group for a new ledger: next to similar ledgers, a named group, the company
	default's group, or the deepest group of that root type."""
	base = {"company": company, "root_type": spec["root_type"]}
	for pattern in spec["siblings"]:
		parent = frappe.db.get_value("Account", {**base, "is_group": 0, "account_name": ["like", pattern]}, "parent_account")
		if parent:
			return parent
	for pattern in spec["groups"]:
		group = frappe.db.get_value("Account", {**base, "is_group": 1, "account_name": ["like", pattern]}, "name")
		if group:
			return group
	if spec.get("hint"):
		hint = frappe.get_cached_value("Company", company, spec["hint"])
		parent = hint and frappe.db.get_value("Account", hint, "parent_account")
		if parent:
			return parent
	groups = frappe.get_all("Account", filters={**base, "is_group": 1}, pluck="name", order_by="lft desc")
	for g in groups:
		if not frappe.db.exists("Account", {"parent_account": g, "is_group": 1}):
			return g
	return groups[0] if groups else None


def create_default_accounts(company):
	"""Create (or reuse) the three payroll ledgers for a company; returns {field: account}."""
	result = {}
	for field, spec in DEFAULT_ACCOUNTS.items():
		existing = frappe.db.get_value("Account", {"company": company, "account_name": spec["account_name"], "is_group": 0})
		if existing:
			result[field] = existing
			continue
		parent = _parent_group(company, spec)
		if not parent:
			frappe.throw(_("تعذر إيجاد حساب رئيسي مناسب لـ {0}").format(spec["account_name"]))
		acc = frappe.get_doc({
			"doctype": "Account",
			"company": company,
			"account_name": spec["account_name"],
			"parent_account": parent,
			"account_type": spec["account_type"],
			"is_group": 0,
		})
		acc.flags.ignore_permissions = True
		acc.insert()
		result[field] = acc.name
	return result
