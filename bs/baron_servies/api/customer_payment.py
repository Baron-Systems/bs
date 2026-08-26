# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Customer Payment API - Financial summary, statement, and payment creation."""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt, nowdate


@frappe.whitelist()
def get_customer_financial_summary(customer, company=None):
	if not customer:
		frappe.throw(_("Customer is required"))

	params = {"customer": customer, "docstatus": 1}
	cc = "AND company = %(company)s" if company else ""
	if company:
		params["company"] = company

	total_sales = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(grand_total), 0) FROM `tabSales Invoice`
		WHERE customer=%(customer)s AND docstatus=%(docstatus)s {cc}
	""".format(cc=cc), params)[0][0])

	total_payments = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(paid_amount), 0) FROM `tabPayment Entry`
		WHERE party=%(customer)s AND party_type='Customer'
		AND docstatus=1 AND payment_type='Receive' {cc}
	""".format(cc=cc), params)[0][0])

	outstanding_balance = get_general_ledger_balance(customer, company)

	unpaid_count = frappe.db.sql("""
		SELECT COUNT(*) FROM `tabSales Invoice`
		WHERE customer=%(customer)s AND docstatus=%(docstatus)s
		AND outstanding_amount > 0 {cc}
	""".format(cc=cc), params)[0][0]

	currency = frappe.db.get_value("Company", company, "default_currency") if company else \
		frappe.db.get_single_value("Global Defaults", "default_currency")

	return {
		"total_sales": total_sales,
		"total_payments": total_payments,
		"outstanding_balance": outstanding_balance,
		"unpaid_invoice_count": unpaid_count,
		"currency": currency,
	}


def get_general_ledger_balance(customer, company=None):
	"""Get customer balance from General Ledger (GL Entry)."""
	receivable_account = None
	if company:
		receivable_account = frappe.db.get_value("Company", company, "default_receivable_account")

	gl_filters = {
		"party_type": "Customer",
		"party": customer,
		"is_cancelled": 0,
	}
	if company:
		gl_filters["company"] = company
	if receivable_account:
		gl_filters["account"] = receivable_account

	result = frappe.db.sql("""
		SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) as balance
		FROM `tabGL Entry`
		WHERE party_type = %(party_type)s
		AND party = %(party)s
		AND is_cancelled = %(is_cancelled)s
		{company_filter}
		{account_filter}
	""".format(
		company_filter="AND company = %(company)s" if company else "",
		account_filter="AND account = %(account)s" if receivable_account else "",
	), gl_filters)

	return flt(result[0][0]) if result else 0


@frappe.whitelist()
def get_customer_statement(customer, company=None, limit=300):
	"""Get customer statement: sales invoices and payments, sorted chronologically."""
	if not customer:
		frappe.throw(_("Customer is required"))

	inv_filters = {"customer": customer, "docstatus": 1}
	if company:
		inv_filters["company"] = company
	invoices = frappe.get_all(
		"Sales Invoice",
		filters=inv_filters,
		fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount", "status", "currency", "customer_name", "is_return"],
		order_by="posting_date asc, name asc",
		limit=limit,
	)
	for inv in invoices:
		inv["type"] = "invoice"
		inv["items"] = frappe.get_all(
			"Sales Invoice Item",
			filters={"parent": inv.name},
			fields=["name", "item_code", "item_name", "qty", "rate", "amount", "uom", "description"],
			order_by="idx asc",
		)

	pay_filters = {"party": customer, "party_type": "Customer", "docstatus": 1}
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


@frappe.whitelist()
def create_customer_payment(customer, company, amount, mode_of_payment="Cash", payment_type="Receive"):
	"""Create a Payment Entry for a customer."""
	if not customer:
		frappe.throw(_("Customer is required"))
	if not company:
		frappe.throw(_("Company is required"))

	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("Payment amount must be greater than zero"))

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

	if payment_type not in ("Receive", "Pay"):
		frappe.throw(_("Payment type must be either 'Receive' or 'Pay'"))

	from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
	account_info = get_bank_cash_account(mode_of_payment, company)
	if not account_info or not account_info.get("account"):
		frappe.throw(_("Could not determine payment account for {0}").format(mode_of_payment))

	company_doc = frappe.get_cached_doc("Company", company)
	if not company_doc.default_receivable_account:
		frappe.throw(_("Default receivable account not set for company {0}").format(company))

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.posting_date = nowdate()
	pe.party_type = "Customer"
	pe.party = customer
	pe.company = company
	pe.mode_of_payment = mode_of_payment
	pe.reference_no = f"BS-PAY-{frappe.generate_hash(length=8)}"
	pe.reference_date = nowdate()

	if payment_type == "Receive":
		pe.paid_from = company_doc.default_receivable_account
		pe.paid_to = account_info.get("account")
		pe.paid_amount = amount
		pe.received_amount = amount
		pe.remarks = _("Payment - {0}").format(mode_of_payment)

		outstanding_invoices = frappe.get_all(
			"Sales Invoice",
			filters={"customer": customer, "company": company, "docstatus": 1, "outstanding_amount": [">", 0]},
			fields=["name", "outstanding_amount", "grand_total", "posting_date"],
			order_by="posting_date asc",
		)

		allocated = []
		if outstanding_invoices:
			remaining = amount
			for inv in outstanding_invoices:
				if remaining <= 0.005:
					break
				alloc = min(remaining, flt(inv.outstanding_amount))
				if alloc <= 0:
					continue
				pe.append("references", {
					"reference_doctype": "Sales Invoice",
					"reference_name": inv.name,
					"total_amount": inv.grand_total,
					"outstanding_amount": inv.outstanding_amount,
					"allocated_amount": alloc,
				})
				allocated.append({"invoice": inv.name, "amount": alloc})
				remaining -= alloc
	else:
		pe.paid_from = account_info.get("account")
		pe.paid_to = company_doc.default_receivable_account
		pe.paid_amount = amount
		pe.received_amount = amount
		pe.remarks = _("Payment to Customer - {0}").format(mode_of_payment)
		allocated = []

	pe.flags.ignore_permissions = True
	pe.insert()
	pe.submit()
	frappe.db.commit()

	summary = get_customer_financial_summary(customer, company)
	return {
		"payment_entry": pe.name,
		"allocated_invoices": allocated,
		"updated_summary": summary,
	}
