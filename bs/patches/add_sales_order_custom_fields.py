# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Patch: Add Custom Fields to Sales Order for online store orders."""

from __future__ import unicode_literals

import frappe


def execute():
	"""Add custom fields to Sales Order for storing customer data from online store."""

	custom_fields = [
		{
			"fieldname": "store_customer_name",
			"label": "Store Customer Name",
			"fieldtype": "Data",
			"insert_after": "customer_name",
			"read_only": 1,
			"allow_on_submit": 1,
		},
		{
			"fieldname": "store_phone",
			"label": "Store Phone",
			"fieldtype": "Data",
			"insert_after": "store_customer_name",
			"read_only": 1,
			"allow_on_submit": 1,
		},
		{
			"fieldname": "store_delivery_area",
			"label": "Store Delivery Area",
			"fieldtype": "Data",
			"insert_after": "store_phone",
			"read_only": 1,
			"allow_on_submit": 1,
		},
		{
			"fieldname": "store_delivery_fee",
			"label": "Store Delivery Fee",
			"fieldtype": "Currency",
			"insert_after": "store_delivery_area",
			"read_only": 1,
			"allow_on_submit": 1,
		},
		{
			"fieldname": "store_address",
			"label": "Store Address",
			"fieldtype": "Small Text",
			"insert_after": "store_delivery_fee",
			"read_only": 1,
			"allow_on_submit": 1,
		},
		{
			"fieldname": "store_notes",
			"label": "Store Notes",
			"fieldtype": "Text",
			"insert_after": "store_address",
			"read_only": 1,
			"allow_on_submit": 1,
		},
		{
			"fieldname": "store_order_source",
			"label": "Store Order Source",
			"fieldtype": "Data",
			"insert_after": "store_notes",
			"read_only": 1,
			"allow_on_submit": 1,
			"default": "Online Store",
		},
	]

	for cf in custom_fields:
		field_name = "store_" + cf["fieldname"].replace("store_", "")
		existing = frappe.db.get_value(
			"Custom Field",
			{"dt": "Sales Order", "fieldname": cf["fieldname"]},
			"name",
		)
		if existing:
			continue

		doc = frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Sales Order",
			"module": "Baron servies",
			**cf,
		})
		doc.insert(ignore_permissions=True)

	frappe.db.commit()
	frappe.clear_cache()
