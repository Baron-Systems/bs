# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Dashboard API - Sales, purchases, cash flow, top items summary."""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days, nowdate, get_first_day, get_last_day


@frappe.whitelist()
def get_dashboard_data(company=None, from_date=None, to_date=None):
	"""
	Get complete dashboard data for the store.

	Returns:
		dict: {
			summary: {total_sales, total_purchases, total_payments_in, total_payments_out, net_cash, gross_profit},
			sales_by_month: [{month, sales, purchases}],
			payments_by_mode: [{mode, amount, count}],
			top_items: [{item_code, item_name, qty, amount}],
			top_customers: [{customer, total, invoices}],
			recent_invoices: [{name, customer, grand_total, posting_date, status}],
			low_stock_items: [{item_code, item_name, actual_qty, reorder_level}],
		}
	"""
	if not to_date:
		to_date = nowdate()
	if not from_date:
		# Default: last 6 months
		from_date = add_days(to_date, -180)

	filters = {}
	if company:
		filters["company"] = company

	summary = _get_summary(company, from_date, to_date)
	sales_by_month = _get_monthly_trend(company, from_date, to_date)
	payments_by_mode = _get_payments_by_mode(company, from_date, to_date)
	top_items = _get_top_items(company, from_date, to_date, limit=10)
	top_customers = _get_top_customers(company, from_date, to_date, limit=10)
	recent_invoices = _get_recent_invoices(company, from_date, to_date, limit=10)
	low_stock_items = _get_low_stock_items(company, limit=10)
	bottom_items = _get_bottom_items(company, from_date, to_date, limit=10)

	return {
		"summary": summary,
		"sales_by_month": sales_by_month,
		"payments_by_mode": payments_by_mode,
		"top_items": top_items,
		"top_customers": top_customers,
		"recent_invoices": recent_invoices,
		"low_stock_items": low_stock_items,
		"bottom_items": bottom_items,
		"from_date": from_date,
		"to_date": to_date,
	}


def _get_summary(company, from_date, to_date):
	"""Get summary totals for the period.

	All figures are taken from the General Ledger (GL Entry) so they reconcile
	with the accounting reports:
	- Opening entries (opening invoices / opening balances) are excluded from
	  period flows (sales, purchases, cash in/out).
	- Cash in/out include POS invoice payments, not only Payment Entries.
	- Receivable/payable are the party-account balances as of to_date.
	"""
	gc = "AND gle.company = %(company)s" if company else ""
	cc = "AND company = %(company)s" if company else ""
	params = {"from_date": from_date, "to_date": to_date}
	if company:
		params["company"] = company

	# Net Sales: direct income accounts (returns reduce it automatically)
	total_sales = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(gle.credit - gle.debit), 0)
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.is_opening = 'No'
		AND acc.root_type = 'Income' AND IFNULL(acc.account_type, '') != 'Indirect Income'
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{gc}
	""".format(gc=gc), params)[0][0], 2)

	# Cost of Goods Sold
	cogs = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(gle.debit - gle.credit), 0)
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.is_opening = 'No'
		AND acc.account_type = 'Cost of Goods Sold'
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{gc}
	""".format(gc=gc), params)[0][0], 2)

	# Profit = all Income - all Expenses (same as "Profit for the year" in Profit and Loss Statement)
	gross_profit = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(gle.credit - gle.debit), 0)
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.is_opening = 'No'
		AND acc.root_type IN ('Income', 'Expense')
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{gc}
	""".format(gc=gc), params)[0][0], 2)

	# Total Purchases (excluding opening invoices), in company currency
	total_purchases = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(base_grand_total), 0)
		FROM `tabPurchase Invoice`
		WHERE docstatus = 1 AND is_opening = 'No'
		AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		{cc}
	""".format(cc=cc), params)[0][0], 2)

	# Cash/Bank movement: debit = money in, credit = money out
	cash_in, cash_out = frappe.db.sql("""
		SELECT COALESCE(SUM(gle.debit), 0), COALESCE(SUM(gle.credit), 0)
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.is_opening = 'No'
		AND acc.account_type IN ('Cash', 'Bank')
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{gc}
	""".format(gc=gc), params)[0]
	total_payments_in = flt(cash_in, 2)
	total_payments_out = flt(cash_out, 2)
	net_cash = flt(total_payments_in - total_payments_out, 2)

	# Customer receivable balance as of to_date
	outstanding_receivable = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(gle.debit - gle.credit), 0)
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0
		AND acc.account_type = 'Receivable' AND gle.party_type = 'Customer'
		AND gle.posting_date <= %(to_date)s
		{gc}
	""".format(gc=gc), params)[0][0], 2)

	# Supplier payable balance as of to_date
	outstanding_payable = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(gle.credit - gle.debit), 0)
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0
		AND acc.account_type = 'Payable' AND gle.party_type = 'Supplier'
		AND gle.posting_date <= %(to_date)s
		{gc}
	""".format(gc=gc), params)[0][0], 2)

	currency = frappe.db.get_value("Company", company, "default_currency") if company else \
		frappe.db.get_single_value("Global Defaults", "default_currency")

	return {
		"total_sales": total_sales,
		"total_purchases": total_purchases,
		"total_payments_in": total_payments_in,
		"total_payments_out": total_payments_out,
		"net_cash": net_cash,
		"gross_profit": gross_profit,
		"cogs": cogs,
		"outstanding_receivable": outstanding_receivable,
		"outstanding_payable": outstanding_payable,
		"currency": currency,
	}


def _get_monthly_trend(company, from_date, to_date):
	"""Get monthly sales (GL net sales) and purchases trend."""
	gc = "AND gle.company = %(company)s" if company else ""
	cc = "AND company = %(company)s" if company else ""
	params = {"from_date": from_date, "to_date": to_date}
	if company:
		params["company"] = company

	sales = frappe.db.sql("""
		SELECT
			DATE_FORMAT(gle.posting_date, '%%Y-%%m') as month,
			COALESCE(SUM(gle.credit - gle.debit), 0) as total
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.is_opening = 'No'
		AND acc.root_type = 'Income' AND IFNULL(acc.account_type, '') != 'Indirect Income'
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{gc}
		GROUP BY month
		ORDER BY month
	""".format(gc=gc), params, as_dict=True)

	purchases = frappe.db.sql("""
		SELECT
			DATE_FORMAT(posting_date, '%%Y-%%m') as month,
			COALESCE(SUM(base_grand_total), 0) as total
		FROM `tabPurchase Invoice`
		WHERE docstatus = 1 AND is_opening = 'No'
		AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		{cc}
		GROUP BY month
		ORDER BY month
	""".format(cc=cc), params, as_dict=True)

	# Build a complete month list
	months = []
	current = getdate(from_date)
	end = getdate(to_date)
	# Move to first day of month
	current = getdate(get_first_day(current))
	while current <= end:
		months.append(current.strftime("%Y-%m"))
		# Next month
		next_m = add_days(get_last_day(current), 1)
		current = next_m

	sales_map = {r["month"]: flt(r["total"], 2) for r in sales}
	purchases_map = {r["month"]: flt(r["total"], 2) for r in purchases}

	result = []
	for m in months:
		# Format month label as "Mon YYYY" in Arabic-friendly format
		dt = getdate(m + "-01")
		label = dt.strftime("%b %Y")
		result.append({
			"month": m,
			"label": label,
			"sales": sales_map.get(m, 0),
			"purchases": purchases_map.get(m, 0),
		})

	return result


def _get_payments_by_mode(company, from_date, to_date):
	"""Get money received per cash/bank account from the GL (includes POS payments)."""
	gc = "AND gle.company = %(company)s" if company else ""
	params = {"from_date": from_date, "to_date": to_date}
	if company:
		params["company"] = company

	rows = frappe.db.sql("""
		SELECT
			acc.account_name as mode,
			COALESCE(SUM(gle.debit), 0) as amount,
			COUNT(DISTINCT gle.voucher_type, gle.voucher_no) as count
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.is_opening = 'No'
		AND acc.account_type IN ('Cash', 'Bank')
		AND gle.debit > 0
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{gc}
		GROUP BY acc.account_name
		ORDER BY amount DESC
	""".format(gc=gc), params, as_dict=True)

	return rows


def _get_top_items(company, from_date, to_date, limit=10):
	"""Get top selling items by quantity and amount."""
	cc = "AND si.company = %(company)s" if company else ""
	params = {"from_date": from_date, "to_date": to_date, "limit": limit}
	if company:
		params["company"] = company

	rows = frappe.db.sql("""
		SELECT
			si_item.item_code,
			si_item.item_name,
			COALESCE(SUM(si_item.qty), 0) as qty,
			COALESCE(SUM(si_item.base_net_amount), 0) as amount
		FROM `tabSales Invoice Item` si_item
		INNER JOIN `tabSales Invoice` si ON si_item.parent = si.name
		WHERE si.docstatus = 1 AND si.is_opening = 'No'
		AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{cc}
		GROUP BY si_item.item_code, si_item.item_name
		ORDER BY amount DESC
		LIMIT %(limit)s
	""".format(cc=cc), params, as_dict=True)

	return rows


def _get_bottom_items(company, from_date, to_date, limit=10):
	"""Get least selling items (stock items with lowest sales in the period)."""
	cc = "AND si.company = %(company)s" if company else ""
	params = {"from_date": from_date, "to_date": to_date, "limit": limit}
	if company:
		params["company"] = company

	# Items that had sales but the lowest amounts
	rows = frappe.db.sql("""
		SELECT
			si_item.item_code,
			si_item.item_name,
			COALESCE(SUM(si_item.qty), 0) as qty,
			COALESCE(SUM(si_item.base_net_amount), 0) as amount
		FROM `tabSales Invoice Item` si_item
		INNER JOIN `tabSales Invoice` si ON si_item.parent = si.name
		WHERE si.docstatus = 1 AND si.is_opening = 'No'
		AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{cc}
		GROUP BY si_item.item_code, si_item.item_name
		ORDER BY amount ASC
		LIMIT %(limit)s
	""".format(cc=cc), params, as_dict=True)

	return rows


def _get_top_customers(company, from_date, to_date, limit=10):
	"""Get top customers by total sales."""
	cc = "AND company = %(company)s" if company else ""
	params = {"from_date": from_date, "to_date": to_date, "limit": limit}
	if company:
		params["company"] = company

	rows = frappe.db.sql("""
		SELECT
			customer,
			COALESCE(SUM(base_grand_total), 0) as total,
			COUNT(*) as invoices
		FROM `tabSales Invoice`
		WHERE docstatus = 1 AND is_opening = 'No'
		AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		{cc}
		GROUP BY customer
		ORDER BY total DESC
		LIMIT %(limit)s
	""".format(cc=cc), params, as_dict=True)

	return rows


def _get_recent_invoices(company, from_date, to_date, limit=10):
	"""Get recent sales invoices."""
	filters = {"docstatus": 1, "is_opening": "No", "posting_date": ["between", [from_date, to_date]]}
	if company:
		filters["company"] = company

	rows = frappe.get_all(
		"Sales Invoice",
		filters=filters,
		fields=["name", "customer", "grand_total", "posting_date", "status", "outstanding_amount"],
		order_by="posting_date desc, creation desc",
		limit=limit,
	)
	return rows


def _get_low_stock_items(company, limit=10):
	"""Get items with low stock (actual_qty <= reorder_level or actual_qty <= 0)."""
	# Get items that have reorder_level custom field or are low in stock
	# First try with Bin join
	cc = "AND i.custom_company = %(company)s" if company else ""
	params = {"limit": limit}
	if company:
		params["company"] = company

	# Get items with stock below a threshold (using Bin actual_qty)
	# Simplified: items with total stock <= 5 (configurable later)
	rows = frappe.db.sql("""
		SELECT
			i.name as item_code,
			i.item_name,
			i.stock_uom,
			COALESCE(SUM(b.actual_qty), 0) as actual_qty
		FROM `tabItem` i
		LEFT JOIN `tabBin` b ON i.name = b.item_code
		WHERE i.disabled = 0
		AND i.is_stock_item = 1
		{cc}
		GROUP BY i.name, i.item_name, i.stock_uom
		HAVING actual_qty <= 5
		ORDER BY actual_qty ASC
		LIMIT %(limit)s
	""".format(cc=cc), params, as_dict=True)

	return rows
