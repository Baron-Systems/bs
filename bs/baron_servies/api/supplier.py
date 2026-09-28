# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Supplier API - Financial summary, statement, and payment creation."""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt, nowdate


@frappe.whitelist()
def get_suppliers(search_term="", limit=50):
	"""Search suppliers by name, mobile, or email."""
	filters = {"disabled": 0}

	or_filters = []
	if search_term:
		like = f"%{search_term}%"
		or_filters = [
			["name", "like", like],
			["supplier_name", "like", like],
			["mobile_no", "like", like],
			["email_id", "like", like],
		]

	result = frappe.get_all(
		"Supplier",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "supplier_name", "mobile_no", "email_id", "supplier_group", "supplier_type"],
		limit_page_length=int(limit) if limit else 50,
		order_by="supplier_name asc",
	)
	return result


@frappe.whitelist()
def get_supplier_financial_summary(supplier, company=None):
	"""Get supplier financial summary."""
	if not supplier:
		frappe.throw(_("Supplier is required"))

	params = {"supplier": supplier, "docstatus": 1}
	cc = "AND company = %(company)s" if company else ""
	if company:
		params["company"] = company

	total_purchases = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(grand_total), 0) FROM `tabPurchase Invoice`
		WHERE supplier=%(supplier)s AND docstatus=%(docstatus)s {cc}
	""".format(cc=cc), params)[0][0])

	total_payments = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(paid_amount), 0) FROM `tabPayment Entry`
		WHERE party=%(supplier)s AND party_type='Supplier'
		AND docstatus=1 AND payment_type='Pay' {cc}
	""".format(cc=cc), params)[0][0])

	outstanding_balance = get_supplier_gl_balance(supplier, company)

	currency = frappe.db.get_value("Company", company, "default_currency") if company else \
		frappe.db.get_single_value("Global Defaults", "default_currency")

	return {
		"total_purchases": total_purchases,
		"total_payments": total_payments,
		"outstanding_balance": outstanding_balance,
		"currency": currency,
	}


def get_supplier_gl_balance(supplier, company=None):
	"""Get supplier balance from General Ledger."""
	payable_account = None
	if company:
		payable_account = frappe.db.get_value("Company", company, "default_payable_account")

	gl_filters = {
		"party_type": "Supplier",
		"party": supplier,
		"is_cancelled": 0,
	}
	if company:
		gl_filters["company"] = company
	if payable_account:
		gl_filters["account"] = payable_account

	result = frappe.db.sql("""
		SELECT COALESCE(SUM(credit), 0) - COALESCE(SUM(debit), 0) as balance
		FROM `tabGL Entry`
		WHERE party_type = %(party_type)s
		AND party = %(party)s
		AND is_cancelled = %(is_cancelled)s
		{company_filter}
		{account_filter}
	""".format(
		company_filter="AND company = %(company)s" if company else "",
		account_filter="AND account = %(account)s" if payable_account else "",
	), gl_filters)

	return flt(result[0][0]) if result else 0


@frappe.whitelist()
def create_supplier_payment(supplier, company, amount, mode_of_payment="Cash", payment_type="Pay"):
	"""Create a Payment Entry for a supplier."""
	if not supplier:
		frappe.throw(_("Supplier is required"))
	if not company:
		frappe.throw(_("Company is required"))

	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("Amount must be greater than zero"))

	# Resolve mode of payment (support Arabic names)
	if not frappe.db.exists("Mode of Payment", mode_of_payment):
		alternatives = []
		if mode_of_payment == "Cash":
			alternatives = ["نقدي", "كاش", "نقداً"]
		elif mode_of_payment == "نقدي":
			alternatives = ["Cash", "كاش", "نقداً"]
		found = False
		for alt in alternatives:
			if frappe.db.exists("Mode of Payment", alt):
				mode_of_payment = alt
				found = True
				break
		if not found:
			frappe.throw(_("Mode of Payment {0} does not exist").format(mode_of_payment))

	if payment_type not in ("Pay", "Receive"):
		frappe.throw(_("Payment type must be either 'Pay' or 'Receive'"))

	payable_account = frappe.db.get_value("Company", company, "default_payable_account")
	if not payable_account:
		frappe.throw(_("Default Payable Account not set for Company {0}").format(company))

	mode_account = frappe.db.get_value("Mode of Payment Account", {"parent": mode_of_payment, "company": company}, "default_account")
	if not mode_account:
		mode_account = frappe.db.get_value("Company", company, "default_cash_account")
	if not mode_account:
		frappe.throw(_("Payment account not found for mode of payment {0}").format(mode_of_payment))

	pe = frappe.get_doc({
		"doctype": "Payment Entry",
		"payment_type": payment_type,
		"party_type": "Supplier",
		"party": supplier,
		"company": company,
		"paid_amount": amount,
		"received_amount": amount,
		"paid_from": mode_account if payment_type == "Pay" else payable_account,
		"paid_to": payable_account if payment_type == "Pay" else mode_account,
		"mode_of_payment": mode_of_payment,
		"posting_date": nowdate(),
		"reference_no": f"BS-SUP-{frappe.generate_hash(length=8)}",
		"reference_date": nowdate(),
	})

	pe.insert(ignore_permissions=True)
	pe.submit()

	summary = get_supplier_financial_summary(supplier, company)
	return {
		"payment_entry": pe.name,
		"amount": amount,
		"supplier": supplier,
		"updated_summary": summary,
	}


@frappe.whitelist()
def get_supplier_statement(supplier, company=None, limit=300):
	"""Get supplier statement: purchase invoices and payments, sorted chronologically."""
	if not supplier:
		frappe.throw(_("Supplier is required"))

	inv_filters = {"supplier": supplier, "docstatus": 1}
	if company:
		inv_filters["company"] = company
	invoices = frappe.get_all(
		"Purchase Invoice",
		filters=inv_filters,
		fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount", "status", "currency", "supplier_name", "is_return"],
		order_by="posting_date asc, name asc",
		limit=limit,
	)
	for inv in invoices:
		inv["type"] = "invoice"
		inv["items"] = frappe.get_all(
			"Purchase Invoice Item",
			filters={"parent": inv.name},
			fields=["name", "item_code", "item_name", "qty", "rate", "amount", "uom", "description"],
			order_by="idx asc",
		)

	pay_filters = {"party": supplier, "party_type": "Supplier", "docstatus": 1}
	if company:
		pay_filters["company"] = company
	payments = frappe.get_all(
		"Payment Entry",
		filters=pay_filters,
		fields=["name", "posting_date", "paid_amount", "mode_of_payment", "reference_no", "payment_type", "remarks"],
		order_by="posting_date asc, name asc",
		limit=limit,
	)
	for pay in payments:
		pay["type"] = "payment"

	combined = sorted(invoices + payments, key=lambda x: (x.posting_date or "0000-00-00", x.name), reverse=True)
	return combined
