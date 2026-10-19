# -*- coding: utf-8 -*-
# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Patch: order-tracking fields for online store Sales Orders + store defaults.

Idempotent — existing custom fields are skipped, settings are only filled when empty.
"""

import frappe

CUSTOM_FIELDS = [
	{
		"fieldname": "store_status",
		"label": "Store Order Status",
		"fieldtype": "Select",
		"options": "\nNew\nConfirmed\nOut for Delivery\nDelivered\nCancelled",
		"insert_after": "store_order_source",
		"allow_on_submit": 1,
		"in_standard_filter": 1,
		"read_only": 1,
	},
	{
		"fieldname": "store_invoice",
		"label": "Store Delivery Invoice",
		"fieldtype": "Link",
		"options": "Sales Invoice",
		"insert_after": "store_status",
		"allow_on_submit": 1,
		"read_only": 1,
	},
]


def execute():
	for cf in CUSTOM_FIELDS:
		if frappe.db.get_value("Custom Field", {"dt": "Sales Order", "fieldname": cf["fieldname"]}, "name"):
			continue
		frappe.get_doc({"doctype": "Custom Field", "dt": "Sales Order", "module": "Baron servies", **cf}).insert(
			ignore_permissions=True
		)
	frappe.clear_cache(doctype="Sales Order")

	# Existing online orders start as "New" (drafts) or "Confirmed" (submitted)
	frappe.db.sql(
		"""update `tabSales Order` set store_status = if(docstatus = 1, 'Confirmed', if(docstatus = 2, 'Cancelled', 'New'))
		where store_order_source = 'Online Store' and coalesce(store_status, '') = ''"""
	)

	# Sensible defaults for the new store settings
	selling = frappe.get_single("Selling Settings")
	defaults = {
		"customer_group": selling.customer_group,
		"territory": selling.territory,
		"out_of_stock_policy": "Allow",
		"delivery_mode_of_payment": "Cash" if frappe.db.exists("Mode of Payment", "Cash") else None,
	}
	for field, value in defaults.items():
		row = frappe.db.sql("select value from `tabSingles` where doctype='Store Settings' and field=%s", field)
		if value and (not row or row[0][0] in (None, "")):
			frappe.db.set_single_value("Store Settings", field, value)
	frappe.db.commit()
