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

import json

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
			"entries": [ { posting_date, voucher_type, voucher_subtype, voucher_no,
						   account, debit, credit, balance, remarks, against_voucher } ]
			(one entry per voucher; against_voucher lists every invoice it settled)
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

	# --- Fetch only the newest N vouchers for display ---
	# One row per voucher: a payment allocated against several invoices produces one GL row
	# per invoice (same voucher_no); the statement shows it as a single movement.
	entries = frappe.db.sql(f"""
		SELECT
			MIN(name) AS gl_entry,
			posting_date,
			voucher_type,
			MAX(voucher_subtype) AS voucher_subtype,
			voucher_no,
			MAX(account) AS account,
			MAX(against_voucher_type) AS against_voucher_type,
			GROUP_CONCAT(DISTINCT against_voucher ORDER BY against_voucher SEPARATOR ', ') AS against_voucher,
			MAX(against) AS against,
			MAX(remarks) AS remarks,
			SUM(debit) AS debit,
			SUM(credit) AS credit,
			SUM(debit_in_account_currency) AS debit_in_account_currency,
			SUM(credit_in_account_currency) AS credit_in_account_currency,
			MAX(account_currency) AS account_currency,
			COUNT(*) AS gl_rows,
			MAX(creation) AS creation
		FROM `tabGL Entry`
		WHERE {' AND '.join(entry_conditions)}
		GROUP BY posting_date, voucher_type, voucher_no
		ORDER BY posting_date DESC, MAX(creation) DESC
		LIMIT %(limit)s
	""", {**entry_params, "limit": limit}, as_dict=True)

	for entry in entries:
		entry["debit"] = flt(entry["debit"])
		entry["credit"] = flt(entry["credit"])

	# --- Totals over the FULL date range ---
	# If we fetched fewer vouchers than the limit, the result is complete and we can
	# sum the rows we have. Otherwise, run a separate aggregate over the full range.
	if len(entries) < limit:
		total_debit = sum(entry["debit"] for entry in entries)
		total_credit = sum(entry["credit"] for entry in entries)
		closing_balance = opening_balance + total_debit - total_credit
	else:
		totals = frappe.db.sql(f"""
			SELECT
				COALESCE(SUM(debit), 0) AS total_debit,
				COALESCE(SUM(credit), 0) AS total_credit
			FROM `tabGL Entry`
			WHERE {' AND '.join(entry_conditions)}
		""", entry_params, as_dict=True)[0]

		total_debit = flt(totals.total_debit)
		total_credit = flt(totals.total_credit)
		closing_balance = opening_balance + total_debit - total_credit

	# --- Compute running balance backwards from the real closing balance ---
	# Entries are ordered newest-first; the first row therefore shows the closing balance.
	balance = closing_balance
	for entry in entries:
		entry["balance"] = flt(balance, 2)
		balance -= entry["debit"] - entry["credit"]

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


@frappe.whitelist()
def get_vouchers_items(vouchers):
	"""
	Batch version of get_voucher_items — one call for every invoice in a ledger.

	Args:
		vouchers (list | json): [ { voucher_type, voucher_no } ]

	Returns:
		dict: { voucher_no: [ { item_code, item_name, qty, rate, amount, uom } ] }
	"""
	if isinstance(vouchers, str):
		vouchers = json.loads(vouchers or "[]")

	names_by_type = {}
	for v in (vouchers or [])[:500]:
		vtype, vno = v.get("voucher_type"), v.get("voucher_no")
		if vtype in INVOICE_ITEM_DOCTYPES and vno:
			names_by_type.setdefault(vtype, set()).add(vno)
	allowed = {t: n for t, n in names_by_type.items() if frappe.has_permission(t, "read")}
	return fetch_vouchers_items(allowed)


INVOICE_ITEM_DOCTYPES = {"Sales Invoice": "Sales Invoice Item", "Purchase Invoice": "Purchase Invoice Item"}


def fetch_vouchers_items(names_by_type):
	"""{voucher_type: {names}} → {voucher_no: [items]} — no permission checks (callers do them)."""
	result = {}
	for vtype, names in names_by_type.items():
		if vtype not in INVOICE_ITEM_DOCTYPES or not names:
			continue
		for row in frappe.get_all(
			INVOICE_ITEM_DOCTYPES[vtype],
			filters={"parent": ["in", list(names)], "parenttype": vtype},
			fields=["name", "parent", "item_code", "item_name", "qty", "rate", "amount", "uom"],
			order_by="parent asc, idx asc",
			limit_page_length=0,
		):
			result.setdefault(row.pop("parent"), []).append(row)
		for name in names:
			result.setdefault(name, [])
	return result
