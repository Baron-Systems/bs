# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def get_csrf_token():
	"""
	Get CSRF token for the current session.
	Only returns CSRF token if user is authenticated with a valid session.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.AuthenticationError)

	if not frappe.db.get_value("User", frappe.session.user, "enabled"):
		frappe.throw(_("User is disabled"), frappe.AuthenticationError)

	if not frappe.session.sid or frappe.session.sid == "Guest":
		frappe.throw(_("Invalid session"), frappe.AuthenticationError)

	csrf_token = frappe.sessions.get_csrf_token()

	if not csrf_token:
		frappe.throw(_("Failed to generate CSRF token"), frappe.ValidationError)

	return {
		"csrf_token": csrf_token,
		"session_id": frappe.session.sid,
	}


@frappe.whitelist()
def get_companies():
	"""List non-group companies the session user can read."""
	rows = frappe.db.get_all(
		"Company",
		filters={"is_group": 0},
		fields=["name", "default_currency"],
		order_by="name",
	)
	return rows


@frappe.whitelist()
def get_company_letterhead(company):
	"""Get the default letterhead (header and footer) for a company."""
	if not company:
		frappe.throw(_("Company is required"))

	default_letterhead = frappe.db.get_value("Company", company, "default_letter_head")
	if not default_letterhead:
		default_letterhead = frappe.db.get_value(
			"Letter Head",
			{"is_default": 1, "disabled": 0},
			"name",
		)

	if not default_letterhead:
		return {"content": "", "footer": ""}

	lh = frappe.db.get_value("Letter Head", default_letterhead, ["content", "footer"], as_dict=True)
	return {
		"name": default_letterhead,
		"content": lh.get("content") or "",
		"footer": lh.get("footer") or "",
	}
