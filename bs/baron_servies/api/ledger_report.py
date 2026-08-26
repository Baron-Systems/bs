# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Party Ledger Report API.

Reads directly from `tabGL Entry` (same source as the General Ledger report)
and computes a running balance after each transaction, so the balance after
every movement matches the General Ledger exactly.

Works for both Customer (Receivable) and Supplier (Payable) parties.
"""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate, add_days


@frappe.whitelist()
def get_party_ledger(party_type, party, company=None, from_date=None, to_date=None, limit=500):
	"""
	Get party ledger entries from GL Entry with running balance.

	This reads directly from `tabGL Entry` — the same table used by the
	General Ledger report — so the running balance after each transaction
	is identical to what the General Ledger report shows.

	Args:
		party_type (str): "Customer" or "Supplier"
		party (str): Party name (ID)
		company (str, optional): Company filter
		from_date (str, optional): Start date (YYYY-MM-DD)
		to_date (str, optional): End date (YYYY-MM-DD)
		limit (int): Max rows to return (default 500)

	Returns:
		dict: {
			"opening_balance": float,
			"closing_balance": float,
			"total_debit": float,
			"total_credit": float,
			"entries": [ { posting_date, voucher_type, voucher_no,
						   account, debit, credit, balance, remarks, against_voucher } ]
		}
	"""
	if not party:
		frappe.throw(_("Party is required"))
	if party_type not in ("Customer", "Supplier"):
		frappe.throw(_("Party type must be Customer or Supplier"))

	if not to_date:
		to_date = nowdate()
	if not from_date:
		from_date = add_days(to_date, -365)

	if getdate(from_date) > getdate(to_date):
		frappe.throw(_("From date cannot be after to date"))

	# Determine the receivable/payable account for this party + company
	party_account = None
	if company:
		if party_type == "Customer":
			party_account = frappe.db.get_value("Company", company, "default_receivable_account")
		else:
			party_account = frappe.db.get_value("Company", company, "default_payable_account")

	# --- Opening balance: sum of all GL entries before from_date ---
	opening_conditions = [
		"party_type = %(party_type)s",
		"party = %(party)s",
		"is_cancelled = 0",
		"posting_date < %(from_date)s",
	]
	opening_params = {
		"party_type": party_type,
		"party": party,
		"from_date": from_date,
	}
	if company:
		opening_conditions.append("company = %(company)s")
		opening_params["company"] = company
	if party_account:
		opening_conditions.append("account = %(account)s")
		opening_params["account"] = party_account

	opening = frappe.db.sql(f"""
		SELECT COALESCE(SUM(debit), 0) AS total_debit,
		       COALESCE(SUM(credit), 0) AS total_credit
		FROM `tabGL Entry`
		WHERE {' AND '.join(opening_conditions)}
	""", opening_params, as_dict=True)[0]

	opening_balance = flt(opening.total_debit) - flt(opening.total_credit)

	# --- GL entries within the date range ---
	entry_conditions = [
		"party_type = %(party_type)s",
		"party = %(party)s",
		"is_cancelled = 0",
		"posting_date >= %(from_date)s",
		"posting_date <= %(to_date)s",
	]
	entry_params = {
		"party_type": party_type,
		"party": party,
		"from_date": from_date,
		"to_date": to_date,
	}
	if company:
		entry_conditions.append("company = %(company)s")
		entry_params["company"] = company
	if party_account:
		entry_conditions.append("account = %(account)s")
		entry_params["account"] = party_account

	entries = frappe.db.sql(f"""
		SELECT
			name AS gl_entry,
			posting_date,
			account,
			voucher_type,
			voucher_subtype,
			voucher_no,
			against_voucher_type,
			against_voucher,
			against,
			remarks,
			debit,
			credit,
			debit_in_account_currency,
			credit_in_account_currency,
			account_currency,
			creation
		FROM `tabGL Entry`
		WHERE {' AND '.join(entry_conditions)}
		ORDER BY posting_date ASC, creation ASC
		LIMIT %(limit)s
	""", {**entry_params, "limit": limit}, as_dict=True)

	# --- Compute running balance ---
	balance = opening_balance
	total_debit = 0
	total_credit = 0

	for entry in entries:
		entry["debit"] = flt(entry["debit"])
		entry["credit"] = flt(entry["credit"])
		balance += entry["debit"] - entry["credit"]
		entry["balance"] = flt(balance)
		total_debit += entry["debit"]
		total_credit += entry["credit"]

	closing_balance = opening_balance + total_debit - total_credit

	# Reverse for display (newest first)
	entries.reverse()

	currency = None
	if company:
		currency = frappe.db.get_value("Company", company, "default_currency")
	if not currency:
		currency = frappe.db.get_single_value("Global Defaults", "default_currency")

	return {
		"opening_balance": flt(opening_balance),
		"closing_balance": flt(closing_balance),
		"total_debit": flt(total_debit),
		"total_credit": flt(total_credit),
		"entries": entries,
		"currency": currency,
		"party_account": party_account,
		"from_date": from_date,
		"to_date": to_date,
	}


@frappe.whitelist()
def get_voucher_items(voucher_type, voucher_no):
	"""
	Get line items for a Sales/Purchase Invoice voucher.

	Args:
		voucher_type (str): "Sales Invoice" or "Purchase Invoice"
		voucher_no (str): Voucher name

	Returns:
		list: [ { item_code, item_name, qty, rate, amount, uom } ]
	"""
	if not voucher_type or not voucher_no:
		return []

	if voucher_type == "Sales Invoice":
		child_doctype = "Sales Invoice Item"
	elif voucher_type == "Purchase Invoice":
		child_doctype = "Purchase Invoice Item"
	else:
		return []

	items = frappe.get_all(
		child_doctype,
		filters={"parent": voucher_no},
		fields=["name", "item_code", "item_name", "qty", "rate", "amount", "uom", "description"],
		order_by="idx asc",
	)
	return items
