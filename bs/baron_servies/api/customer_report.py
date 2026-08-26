# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Detailed Customer Report API.

Provides endpoints for the standalone Customer Report page (/frontend/customer-report)
which shows a comprehensive per-customer breakdown: profile, sales summary,
recent invoices, top items, payment history, and outstanding balances.
"""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate, add_days, date_diff


# =============================================================================
# Permission helpers
# =============================================================================

def _check_customer_permission(customer):
	"""Ensure read permission on the selected customer."""
	if customer and not frappe.has_permission("Customer", "read", doc=customer):
		frappe.throw(
			_("You do not have permission to access Customer {0}").format(customer),
			frappe.PermissionError,
		)


# =============================================================================
# Main endpoints
# =============================================================================

@frappe.whitelist()
def get_customers(search_term="", limit=50):
	"""
	Search customers for the customer report selector.

	Args:
		search_term (str): Search by name, customer_name, mobile_no, or email_id
		limit (int): Maximum results (default 50)

	Returns:
		list: Customer dicts with name, customer_name, customer_group, territory, mobile_no, email_id
	"""
	filters = {"disabled": 0}

	or_filters = []
	if search_term:
		like = f"%{search_term}%"
		or_filters = [
			["name", "like", like],
			["customer_name", "like", like],
			["mobile_no", "like", like],
			["email_id", "like", like],
			["tax_id", "like", like],
		]

	fields = [
		"name", "customer_name", "customer_group", "territory",
		"mobile_no", "email_id", "tax_id", "customer_primary_address",
	]

	customers = frappe.get_all(
		"Customer",
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		limit_page_length=cint(limit) or 50,
		order_by="customer_name asc",
	)

	return customers


@frappe.whitelist()
def get_customer_report(customer, from_date=None, to_date=None):
	"""
	Build a detailed report for a single customer.

	Args:
		customer (str): Customer name (ID)
		from_date (str, optional): Start date (YYYY-MM-DD). Defaults to 365 days ago.
		to_date (str, optional): End date (YYYY-MM-DD). Defaults to today.

	Returns:
		dict: {
			profile, summary, recent_invoices, top_items,
			payments, outstanding, monthly_trend
		}
	"""
	if not customer:
		frappe.throw(_("Customer is required"))

	_check_customer_permission(customer)

	if not to_date:
		to_date = nowdate()
	if not from_date:
		from_date = add_days(to_date, -365)

	if getdate(from_date) > getdate(to_date):
		frappe.throw(_("From date cannot be after to date"))

	return {
		"profile": _get_customer_profile(customer),
		"summary": _get_sales_summary(customer, from_date, to_date),
		"recent_invoices": _get_recent_invoices(customer, from_date, to_date, limit=20),
		"top_items": _get_top_items(customer, from_date, to_date, limit=10),
		"payments": _get_payment_history(customer, from_date, to_date, limit=20),
		"outstanding": _get_outstanding(customer),
		"monthly_trend": _get_monthly_trend(customer, from_date, to_date),
		"from_date": from_date,
		"to_date": to_date,
	}


# =============================================================================
# Report sections
# =============================================================================

def _get_customer_profile(customer):
	"""Return customer profile info including address and contact."""
	profile = frappe.db.get_value(
		"Customer",
		customer,
		[
			"name", "customer_name", "customer_group", "territory",
			"customer_type", "mobile_no", "email_id", "tax_id",
			"disabled", "default_currency", "default_price_list",
			"customer_primary_address", "customer_primary_contact",
		],
		as_dict=True,
	) or {}

	# Primary address lines
	if profile.get("customer_primary_address"):
		addr = frappe.db.get_value(
			"Address",
			profile["customer_primary_address"],
			["address_line1", "address_line2", "city", "state", "country", "pincode"],
			as_dict=True,
		)
		if addr:
			profile["address"] = addr

	# Primary contact
	if profile.get("customer_primary_contact"):
		contact = frappe.db.get_value(
			"Contact",
			profile["customer_primary_contact"],
			["first_name", "last_name", "mobile_no", "email_id"],
			as_dict=True,
		)
		if contact:
			profile["contact"] = contact

	# Loyalty / reward points if the field exists
	try:
		profile["loyalty_points"] = frappe.db.get_value(
			"Customer", customer, "loyalty_points"
		) or 0
	except Exception:
		profile["loyalty_points"] = 0

	return profile


def _get_sales_summary(customer, from_date, to_date):
	"""Aggregate sales totals for the period."""
	invoices = frappe.db.get_all(
		"Sales Invoice",
		filters={
			"customer": customer,
			"docstatus": 1,
			"posting_date": ["between", [from_date, to_date]],
		},
		fields=["name", "grand_total", "is_return", "total_qty", "net_total"],
	)

	total_invoices = len(invoices)
	total_sales = sum(flt(i.grand_total) for i in invoices if not cint(i.is_return))
	total_returns = sum(flt(i.grand_total) for i in invoices if cint(i.is_return))
	net_sales = total_sales - total_returns
	total_qty = sum(flt(i.total_qty) for i in invoices if not cint(i.is_return))
	returns_count = sum(1 for i in invoices if cint(i.is_return))
	avg_invoice = net_sales / (total_invoices - returns_count) if (total_invoices - returns_count) > 0 else 0

	return {
		"total_invoices": total_invoices,
		"returns_count": returns_count,
		"total_sales": total_sales,
		"total_returns": total_returns,
		"net_sales": net_sales,
		"total_qty": total_qty,
		"avg_invoice": avg_invoice,
	}


def _get_recent_invoices(customer, from_date, to_date, limit=20):
	"""Return recent submitted invoices in the period."""
	return frappe.db.get_all(
		"Sales Invoice",
		filters={
			"customer": customer,
			"docstatus": 1,
			"posting_date": ["between", [from_date, to_date]],
		},
		fields=[
			"name", "posting_date", "grand_total", "net_total",
			"total_qty", "is_return", "status", "outstanding_amount",
			"paid_amount", "pos_profile",
		],
		order_by="posting_date desc, creation desc",
		limit_page_length=limit,
	)


def _get_top_items(customer, from_date, to_date, limit=10):
	"""Aggregate top-selling items for the customer in the period."""
	items = frappe.db.sql(
		"""
		SELECT
			sii.item_code,
			sii.item_name,
			sii.uom,
			SUM(sii.qty) AS total_qty,
			SUM(sii.amount) AS total_amount,
			COUNT(DISTINCT si.name) AS invoice_count
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.customer = %(customer)s
			AND si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND si.is_return = 0
		GROUP BY sii.item_code, sii.item_name, sii.uom
		ORDER BY total_amount DESC
		LIMIT %(limit)s
		""",
		{
			"customer": customer,
			"from_date": from_date,
			"to_date": to_date,
			"limit": limit,
		},
		as_dict=True,
	)
	return items


def _get_payment_history(customer, from_date, to_date, limit=20):
	"""Return payment entries linked to the customer in the period."""
	payments = frappe.db.get_all(
		"Payment Entry",
		filters={
			"party": customer,
			"party_type": "Customer",
			"docstatus": 1,
			"posting_date": ["between", [from_date, to_date]],
		},
		fields=[
			"name", "posting_date", "paid_amount", "received_amount",
			"mode_of_payment", "reference_no", "reference_date", "paid_from", "paid_to",
		],
		order_by="posting_date desc, creation desc",
		limit_page_length=limit,
	)
	return payments


def _get_outstanding(customer):
	"""Return outstanding invoice balances (all-time)."""
	invoices = frappe.db.get_all(
		"Sales Invoice",
		filters={
			"customer": customer,
			"docstatus": 1,
			"outstanding_amount": [">", 0],
		},
		fields=[
			"name", "posting_date", "due_date", "grand_total",
			"paid_amount", "outstanding_amount", "status",
		],
		order_by="due_date asc",
	)

	total_outstanding = sum(flt(i.outstanding_amount) for i in invoices)
	overdue = 0
	overdue_count = 0
	today = getdate(nowdate())
	for inv in invoices:
		if inv.due_date and getdate(inv.due_date) < today:
			overdue += flt(inv.outstanding_amount)
			overdue_count += 1

	return {
		"total_outstanding": total_outstanding,
		"overdue_amount": overdue,
		"overdue_count": overdue_count,
		"open_invoices": invoices,
		"open_invoices_count": len(invoices),
	}


def _get_monthly_trend(customer, from_date, to_date):
	"""Aggregate net sales by month for a simple trend chart."""
	rows = frappe.db.sql(
		"""
		SELECT
			DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month,
			SUM(CASE WHEN si.is_return = 0 THEN si.grand_total ELSE 0 END) AS sales,
			SUM(CASE WHEN si.is_return = 1 THEN si.grand_total ELSE 0 END) AS returns,
			COUNT(*) AS invoice_count
		FROM `tabSales Invoice` si
		WHERE si.customer = %(customer)s
			AND si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY month
		ORDER BY month ASC
		""",
		{
			"customer": customer,
			"from_date": from_date,
			"to_date": to_date,
		},
		as_dict=True,
	)
	for r in rows:
		r["net"] = flt(r.sales) - flt(r.returns)
	return rows
