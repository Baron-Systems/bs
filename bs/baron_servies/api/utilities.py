# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_csrf_token():
	"""
	Get CSRF token for the current session.
	Returns the session CSRF token for both authenticated and guest users
	so that public/guest endpoints (e.g., customer portal) can make POST calls.
	"""
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


_DEFAULT_HOME_CARDS = [
	{"id": "dashboard", "label": "لوحة المعلومات", "route": "Dashboard", "type": "route", "enabled": 1, "users": []},
	{"id": "quick_inventory", "label": "جرد سريع", "route": "QuickInventory", "type": "route", "enabled": 1, "users": []},
	{"id": "quick_purchase_invoice", "label": "فاتورة شراء سريعة", "route": "QuickPurchaseInvoice", "type": "route", "enabled": 1, "users": []},
	{"id": "customer_report", "label": "تقرير العميل مفصل", "route": "CustomerReport", "type": "route", "enabled": 1, "users": []},
	{"id": "customer_payment", "label": "دفع العميل", "route": "CustomerPayment", "type": "route", "enabled": 1, "users": []},
	{"id": "supplier_payment", "label": "دفع المورد", "route": "SupplierPayment", "type": "route", "enabled": 1, "users": []},
	{"id": "store_manage", "label": "إدارة المتجر", "route": "StoreManage", "type": "route", "enabled": 1, "users": []},
	{"id": "customer_portal", "label": "بوابة العميل", "route": "CustomerPortalLogin", "type": "route", "enabled": 1, "users": []},
	{"id": "storefront", "label": "المتجر", "route": "/bs/store", "type": "link", "enabled": 1, "users": []},
]


@frappe.whitelist()
def get_bs_home_settings():
	"""Return the configured home service cards (visible to all authenticated users)."""
	config_doc = frappe.get_doc("BS Home Settings", "BS Home Settings")
	stored = config_doc.get("cards_config") if config_doc else None
	if stored:
		try:
			parsed = json.loads(stored)
			if isinstance(parsed, list) and parsed:
				return {"cards": parsed}
		except Exception:
			pass
	return {"cards": _DEFAULT_HOME_CARDS}


@frappe.whitelist()
def update_bs_home_settings(cards_config):
	"""Save home service cards visibility. Restricted to Administrator."""
	if frappe.session.user != "Administrator":
		frappe.throw(_("Only Administrator can update home settings"), frappe.PermissionError)

	try:
		parsed = json.loads(cards_config)
	except Exception:
		frappe.throw(_("Invalid JSON config"))

	if not isinstance(parsed, list):
		frappe.throw(_("Cards config must be a list"))

	doc = frappe.get_doc("BS Home Settings", "BS Home Settings")
	doc.cards_config = json.dumps(parsed, ensure_ascii=False)
	doc.save(ignore_permissions=True)

	return {"success": True}


@frappe.whitelist()
def search_users_for_settings(search_term="", limit=20):
	"""Search active Frappe users for card assignment. Restricted to Administrator."""
	if frappe.session.user != "Administrator":
		frappe.throw(_("Only Administrator can search users"), frappe.PermissionError)

	filters = {"enabled": 1}
	if search_term:
		filters["name"] = ["like", f"%{search_term}%"]

	users = frappe.get_all(
		"User",
		filters=filters,
		fields=["name", "full_name", "email"],
		limit_page_length=limit,
		order_by="name",
	)

	return {"users": users}
