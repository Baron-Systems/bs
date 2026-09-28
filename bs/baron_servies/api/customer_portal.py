# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Customer Portal API for the bs app.

Provides lightweight authentication (name + customer number) and read-only
access to the customer's ledger statement inside the bs Vue frontend.
"""

from __future__ import unicode_literals

import base64
import hmac
import hashlib
import json
import re

import frappe
from frappe import _
from frappe.utils import add_to_date, flt, get_datetime, now, nowdate


_AR_DIACRITICS_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
TOKEN_VERSION = "cp1"
TOKEN_LIFETIME_DAYS = 7


def _get_secret():
	"""Return a stable site-level secret for signing portal tokens."""
	from frappe.utils.password import get_encryption_key

	secret = frappe.local.conf.get("customer_portal_secret")
	if not secret:
		secret = frappe.local.conf.get("secret")
	if not secret:
		secret = get_encryption_key()
	return secret


def _sign(payload_str):
	return hmac.new(
		_get_secret().encode("utf-8"),
		payload_str.encode("utf-8"),
		digestmod=hashlib.sha512,
	).hexdigest()


def _generate_token(customer_id, customer_name):
	"""Generate a signed token for the customer portal."""
	exp = get_datetime(add_to_date(now(), days=TOKEN_LIFETIME_DAYS))
	payload = {
		"v": TOKEN_VERSION,
		"customer_id": customer_id,
		"customer_name": customer_name,
		"exp": exp.isoformat(),
	}
	payload_b64 = base64.urlsafe_b64encode(
		json.dumps(payload, separators=(",", ":")).encode("utf-8")
	).decode("utf-8").rstrip("=")
	signature = _sign(payload_b64)
	return "{}.{}".format(payload_b64, signature)


def _verify_token(token):
	"""Verify a signed customer portal token and return payload."""
	if not token or "." not in token:
		return None

	parts = token.split(".")
	if len(parts) != 2:
		return None

	payload_b64, signature = parts
	expected_signature = _sign(payload_b64)
	if not hmac.compare_digest(signature, expected_signature):
		return None

	try:
		payload_json = base64.urlsafe_b64decode(
			payload_b64 + "=" * (-len(payload_b64) % 4)
		).decode("utf-8")
		payload = json.loads(payload_json)
	except Exception:
		return None

	if payload.get("v") != TOKEN_VERSION:
		return None

	exp = payload.get("exp")
	if not exp or get_datetime(exp) < get_datetime(now()):
		return None

	return payload


def _get_customer_from_token():
	"""Resolve customer_id from X-Customer-Token header or customer_token cookie.

	We intentionally avoid the standard Authorization/Bearer header because Frappe
	intercepts it for session/OAuth authentication and rejects our custom token.
	"""
	token = None
	if frappe.request:
		token = frappe.get_request_header("X-Customer-Token")
	if not token:
		token = frappe.request.cookies.get("customer_token") if frappe.request else None
	if not token:
		return None

	payload = _verify_token(token)
	if not payload:
		return None

	return payload.get("customer_id")


def _set_token_cookie(token):
	"""Set the customer portal token cookie."""
	from frappe.auth import CookieManager

	if not hasattr(frappe.local, "cookie_manager"):
		frappe.local.cookie_manager = CookieManager()

	frappe.local.cookie_manager.set_cookie(
		"customer_token",
		token,
		httponly=True,
		secure=True,
		samesite="Lax",
	)


@frappe.whitelist(allow_guest=True)
def customer_portal_login(name, id_no):
	"""Login using customer name and customer number (id_no)."""
	try:
		name = (name or "").strip()
		id_no = (id_no or "").strip()

		if not name or not id_no:
			return {
				"success": False,
				"message": "يرجى إدخال الاسم ورقم العميل",
			}

		name_clean = _normalize_ar(name)
		id_no_clean = _normalize_id_no(id_no)

		# Find customer by ID NO: tolerant matching on stored value
		customers = frappe.db.sql(
			"""
			SELECT name, customer_name, id_no
			FROM `tabCustomer`
			WHERE REPLACE(REPLACE(REPLACE(IFNULL(id_no, ''), ' ', ''), '-', ''), '_', '') = %s
			  AND IFNULL(disabled, 0) = 0
			LIMIT 1
			""",
			(id_no_clean,),
			as_dict=True,
		)

		if not customers:
			return {
				"success": False,
				"message": "لم يتم العثور على عميل بهذا الرقم",
			}

		customer = customers[0]
		stored_name = _normalize_ar(customer.customer_name)

		# First name is enough: input must match the beginning of the stored name
		if not stored_name.startswith(name_clean):
			return {
				"success": False,
				"message": "الاسم غير متطابق (يكفي إدخال الاسم الأول كما هو مسجل)",
			}

		token = _generate_token(customer.name, customer.customer_name)
		_set_token_cookie(token)

		return {
			"success": True,
			"token": token,
			"customer": {
				"name": customer.name,
				"customer_name": customer.customer_name,
				"id_no": customer.id_no,
			},
		}
	except Exception as e:
		frappe.log_error(f"Customer Portal Login Error: {str(e)}")
		return {
			"success": False,
			"message": "حدث خطأ أثناء تسجيل الدخول: " + str(e),
		}


@frappe.whitelist(allow_guest=True)
def customer_portal_logout():
	"""Logout from the customer portal."""
	try:
		from frappe.auth import CookieManager
		if not hasattr(frappe.local, "cookie_manager"):
			frappe.local.cookie_manager = CookieManager()
		frappe.local.cookie_manager.delete_cookie("customer_token")
	except Exception:
		pass
	return {"success": True}


@frappe.whitelist(allow_guest=True)
def get_customer_portal_dashboard():
	"""Return summary data for the logged-in customer."""
	customer_id = _get_customer_from_token()
	if not customer_id:
		return {"success": False, "message": "غير مصرح لك بالوصول"}

	try:
		customer = frappe.db.get_value(
			"Customer", customer_id, ["customer_name", "id_no"], as_dict=True
		) or {}

		# Compute outstanding balance from GL Entry (same source as General Ledger)
		balance = frappe.db.sql(
			"""
				SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) AS outstanding
				FROM `tabGL Entry`
				WHERE party_type = 'Customer'
				  AND party = %s
				  AND is_cancelled = 0
			""",
			customer_id,
			as_dict=True,
		)[0]

		# Recent sales invoices and payment totals
		invoice_totals = frappe.db.sql(
			"""
				SELECT
					COALESCE(SUM(CASE WHEN docstatus = 1 THEN grand_total ELSE 0 END), 0) AS total_sales,
					COALESCE(SUM(CASE WHEN docstatus = 1 AND status IN ('Unpaid', 'Overdue', 'Partly Paid') THEN outstanding_amount ELSE 0 END), 0) AS outstanding_invoices,
					COUNT(CASE WHEN docstatus = 1 AND status IN ('Unpaid', 'Overdue') THEN 1 END) AS unpaid_invoice_count
				FROM `tabSales Invoice`
				WHERE customer = %s
			""",
			customer_id,
			as_dict=True,
		)[0]

		payment_totals = frappe.db.sql(
			"""
				SELECT COALESCE(SUM(paid_amount), 0) AS total_payments
				FROM `tabPayment Entry`
				WHERE party_type = 'Customer'
				  AND party = %s
				  AND docstatus = 1
			""",
			customer_id,
			as_dict=True,
		)[0]

		currency = frappe.db.get_single_value("Global Defaults", "default_currency") or "SAR"

		return {
			"success": True,
			"customer": customer,
			"summary": {
				"outstanding_balance": flt(balance.outstanding),
				"total_sales": flt(invoice_totals.total_sales),
				"total_payments": flt(payment_totals.total_payments),
				"unpaid_invoice_count": int(invoice_totals.unpaid_invoice_count or 0),
				"currency": currency,
			},
		}
	except Exception as e:
		frappe.log_error(f"Customer Portal Dashboard Error: {str(e)}")
		return {"success": False, "message": "حدث خطأ أثناء جلب بيانات لوحة التحكم: " + str(e)}


@frappe.whitelist(allow_guest=True)
def get_customer_portal_ledger(from_date=None, to_date=None, limit=500):
	"""Return the customer general-ledger statement."""
	customer_id = _get_customer_from_token()
	if not customer_id:
		return {"success": False, "message": "غير مصرح لك بالوصول"}

	try:
		from bs.baron_servies.api.ledger_report import get_party_ledger
		ledger = get_party_ledger(
			party_type="Customer",
			party=customer_id,
			company=None,
			from_date=from_date,
			to_date=to_date,
			limit=limit,
		)
		return {"success": True, "ledger": ledger}
	except Exception as e:
		frappe.log_error(f"Customer Portal Ledger Error: {str(e)}")
		return {"success": False, "message": "حدث خطأ أثناء جلب كشف الحساب"}


@frappe.whitelist(allow_guest=True)
def get_customer_portal_voucher_items(voucher_type, voucher_no):
	"""Return line items for a voucher belonging to the logged-in customer."""
	customer_id = _get_customer_from_token()
	if not customer_id:
		return {"success": False, "message": "غير مصرح لك بالوصول"}

	if not voucher_type or not voucher_no:
		return {"success": False, "message": "نوع ورقم المستند مطلوبان"}

	# Verify the voucher belongs to this customer
	if voucher_type == "Sales Invoice":
		owner = frappe.db.get_value("Sales Invoice", voucher_no, "customer")
	elif voucher_type == "Purchase Invoice":
		owner = frappe.db.get_value("Purchase Invoice", voucher_no, "supplier")
	elif voucher_type == "Payment Entry":
		owner = frappe.db.get_value("Payment Entry", voucher_no, "party")
	elif voucher_type == "Journal Entry":
		# Journal entries can involve multiple parties; allow for now
		owner = customer_id
	else:
		return {"success": False, "message": "نوع المستند غير مدعوم"}

	if owner != customer_id:
		return {"success": False, "message": "غير مصرح لك بالوصول لهذا المستند"}

	try:
		from bs.baron_servies.api.ledger_report import get_voucher_items
		items = get_voucher_items(voucher_type, voucher_no)
		return {"success": True, "items": items or []}
	except Exception as e:
		frappe.log_error(f"Customer Portal Voucher Items Error: {str(e)}")
		return {"success": False, "message": "حدث خطأ أثناء جلب أصناف المستند"}


def _normalize_id_no(value):
	"""Remove spaces, dashes, underscores and slashes from an id number."""
	return re.sub(r"[\s\-_/]+", "", str(value or ""))


def _normalize_ar(value):
	"""Normalize Arabic text for tolerant matching: no diacritics, common letter variants."""
	s = str(value or "").strip().lower()
	s = s.replace("ـ", "")  # tatweel
	s = _AR_DIACRITICS_RE.sub("", s)
	# Normalize common Arabic letter variants
	s = re.sub(r"[إأآٱ]", "ا", s)
	s = s.replace("ى", "ي")
	s = s.replace("ؤ", "و").replace("ئ", "ي")
	# Keep extra spaces collapsed
	s = re.sub(r"\s+", " ", s)
	return s
