# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Customer search API for the bs app."""

from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def get_customers(search_term="", limit=50):
	"""
	Search customers by name, mobile, email, or tax_id.

	Args:
		search_term (str): Search query.
		limit (int): Maximum results.

	Returns:
		list[dict]: Customer records.
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

	result = frappe.get_all(
		"Customer",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "customer_name", "mobile_no", "email_id", "id_no", "customer_group", "territory"],
		limit_page_length=int(limit) if limit else 50,
		order_by="customer_name asc",
	)
	return result
