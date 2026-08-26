# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Store API - Public storefront + admin management.

Security notes:
- Public endpoints use allow_guest=True and accept ONLY non-sensitive data.
- create_store_order receives only item_code + qty + customer contact info.
- ALL pricing, company, warehouse, price_list, delivery_fee are re-fetched
  from the backend (Store Settings / Store Item / Delivery Area).
- Rate limiting: 5 orders per minute per IP using frappe.cache (Redis).
"""

from __future__ import unicode_literals

import json
import time

import frappe
from frappe import _
from frappe.utils import flt, cint, nowdate


# ============================================================
# PUBLIC APIs (allow_guest = True)
# ============================================================

@frappe.whitelist(allow_guest=True)
def get_store_config():
	"""Public: return store config (no sensitive data like company/warehouse/customer)."""
	settings = _get_settings()
	if not settings:
		return {"is_enabled": 0, "store_name": "", "banner_image": "", "contact_phone": "", "contact_whatsapp": "", "delivery_areas": []}

	areas = []
	for row in settings.get("delivery_areas", []):
		areas.append({
			"area_name": row.get("area_name", ""),
			"delivery_fee": flt(row.get("delivery_fee", 0)),
		})

	return {
		"is_enabled": cint(settings.get("is_enabled", 0)),
		"store_name": settings.get("store_name", ""),
		"banner_image": settings.get("banner_image", ""),
		"contact_phone": settings.get("contact_phone", ""),
		"contact_whatsapp": settings.get("contact_whatsapp", ""),
		"delivery_areas": areas,
	}


@frappe.whitelist(allow_guest=True)
def get_store_items(group=None, search=None):
	"""Public: return published store items only."""
	conditions = ["si.is_published = 1", "i.disabled = 0", "i.is_sales_item = 1"]
	params = {}

	if group:
		conditions.append("si.item_group = %(group)s")
		params["group"] = group

	if search:
		conditions.append("(si.item_name LIKE %(search)s OR si.item LIKE %(search)s)")
		params["search"] = f"%{search}%"

	where = " AND ".join(conditions)

	rows = frappe.db.sql(f"""
		SELECT
			si.item AS item_code,
			si.item_name,
			si.item_group,
			si.stock_uom,
			si.price,
			si.image,
			si.description,
			si.display_order,
			si.max_order_qty
		FROM `tabStore Item` si
		INNER JOIN `tabItem` i ON si.item = i.name
		WHERE {where}
		ORDER BY si.display_order ASC, si.item_name ASC
	""", params, as_dict=True)

	return rows


@frappe.whitelist(allow_guest=True)
def get_store_item_groups():
	"""Public: return item groups that have published items."""
	rows = frappe.db.sql("""
		SELECT DISTINCT si.item_group
		FROM `tabStore Item` si
		INNER JOIN `tabItem` i ON si.item = i.name
		WHERE si.is_published = 1 AND i.disabled = 0 AND i.is_sales_item = 1
		  AND si.item_group IS NOT NULL AND si.item_group != ''
		ORDER BY si.item_group ASC
	""", as_dict=True)

	return [r["item_group"] for r in rows if r.get("item_group")]


@frappe.whitelist(allow_guest=True)
def create_store_order(customer_name, phone, delivery_area, address, items, notes=None):
	"""Public: create a draft Sales Order from store cart.

	SECURITY: Only accepts item_code + qty from client.
	All pricing, company, warehouse, delivery fee are re-fetched from backend.
	Rate limited: 5 orders per minute per IP.
	"""
	# --- Rate limiting ---
	_check_rate_limit()

	# --- Validate store is enabled ---
	settings = _get_settings()
	if not settings or not cint(settings.get("is_enabled", 0)):
		frappe.throw(_("Store is currently unavailable"), frappe.PermissionError)

	# --- Validate inputs ---
	customer_name = (customer_name or "").strip()
	phone = (phone or "").strip()
	delivery_area = (delivery_area or "").strip()
	address = (address or "").strip()

	if not customer_name:
		frappe.throw(_("Customer name is required"))
	if not phone:
		frappe.throw(_("Phone number is required"))
	if not address:
		frappe.throw(_("Delivery address is required"))

	# items can be a JSON string or list
	if isinstance(items, str):
		try:
			items = json.loads(items)
		except (json.JSONDecodeError, ValueError):
			frappe.throw(_("Invalid items data"))
	if not items or not isinstance(items, list):
		frappe.throw(_("Cart is empty"))

	if len(items) > 100:
		frappe.throw(_("Too many items in cart (max 100)"))

	# --- Validate company / customer / warehouse ---
	company = settings.get("company")
	default_customer = settings.get("default_customer")
	warehouse = settings.get("default_warehouse")
	price_list = settings.get("selling_price_list")

	if not company:
		frappe.throw(_("Store is not configured properly (missing company)"))
	if not default_customer:
		frappe.throw(_("Store is not configured properly (missing default customer)"))
	if not warehouse:
		frappe.throw(_("Store is not configured properly (missing warehouse)"))

	# --- Validate delivery area and get fee ---
	delivery_fee = 0
	if delivery_area:
		area_row = None
		for row in settings.get("delivery_areas", []):
			if row.get("area_name") == delivery_area:
				area_row = row
				break
		if not area_row:
			frappe.throw(_("Invalid delivery area: {0}").format(delivery_area))
		delivery_fee = flt(area_row.get("delivery_fee", 0))

	# --- Build validated items list (re-fetch price from backend) ---
	currency = frappe.db.get_value("Company", company, "default_currency") or ""

	validated_items = []
	for entry in items:
		if not isinstance(entry, dict):
			continue
		item_code = (entry.get("item_code") or "").strip()
		qty = flt(entry.get("qty", 0))

		if not item_code:
			continue
		if qty <= 0:
			frappe.throw(_("Invalid quantity for item {0}").format(item_code))

		# Verify the item is published and valid
		store_item = frappe.db.get_value(
			"Store Item",
			{"item": item_code, "is_published": 1},
			["name", "price", "max_order_qty", "item_name", "stock_uom"],
			as_dict=True,
		)
		if not store_item:
			frappe.throw(_("Item {0} is not available in the store").format(item_code))

		# Verify Item is not disabled and is a sales item
		item_disabled = frappe.db.get_value("Item", item_code, ["disabled", "is_sales_item"], as_dict=True)
		if not item_disabled or item_disabled.get("disabled") or not item_disabled.get("is_sales_item"):
			frappe.throw(_("Item {0} is not available").format(item_code))

		# Check max_order_qty
		max_qty = flt(store_item.get("max_order_qty", 0))
		if max_qty > 0 and qty > max_qty:
			frappe.throw(_("Quantity for {0} exceeds maximum allowed ({1})").format(
				store_item.get("item_name") or item_code, max_qty))

		rate = flt(store_item.get("price", 0))
		if rate <= 0:
			# Fallback to Item.standard_rate
			rate = flt(frappe.db.get_value("Item", item_code, "standard_rate") or 0)

		validated_items.append({
			"item_code": item_code,
			"item_name": store_item.get("item_name", ""),
			"qty": qty,
			"rate": rate,
			"uom": store_item.get("stock_uom") or frappe.db.get_value("Item", item_code, "stock_uom"),
			"warehouse": warehouse,
		})

	if not validated_items:
		frappe.throw(_("No valid items in cart"))

	# --- Create Sales Order (draft) ---
	so = frappe.new_doc("Sales Order")
	so.customer = default_customer
	so.company = company
	so.transaction_date = nowdate()
	so.delivery_date = nowdate()
	so.set_warehouse = warehouse
	if price_list:
		so.selling_price_list = price_list

	# Store customer data in custom fields
	so.store_customer_name = customer_name
	so.store_phone = phone
	so.store_delivery_area = delivery_area
	so.store_delivery_fee = delivery_fee
	so.store_address = address
	so.store_notes = notes or ""
	so.store_order_source = "Online Store"

	# Add items
	for vi in validated_items:
		so.append("items", {
			"item_code": vi["item_code"],
			"item_name": vi["item_name"],
			"qty": vi["qty"],
			"rate": vi["rate"],
			"uom": vi["uom"],
			"warehouse": vi["warehouse"],
			"delivery_date": nowdate(),
		})

	# Add delivery fee as a line item if > 0
	if delivery_fee > 0:
		delivery_item_code = _get_or_create_delivery_item(company)
		if delivery_item_code:
			so.append("items", {
				"item_code": delivery_item_code,
				"item_name": "Delivery Charge",
				"qty": 1,
				"rate": delivery_fee,
				"uom": "Nos",
				"warehouse": warehouse,
				"delivery_date": nowdate(),
			})

	so.flags.ignore_permissions = True
	so.insert()
	# Keep as draft (docstatus = 0) — do not submit

	return {
		"sales_order": so.name,
		"total": flt(so.grand_total or so.total),
		"currency": currency,
		"message": _("Order created successfully"),
	}


# ============================================================
# ADMIN APIs (require login)
# ============================================================

@frappe.whitelist()
def get_admin_settings():
	"""Admin: return all store settings."""
	settings = _get_settings()
	if not settings:
		return _default_settings()
	return settings


@frappe.whitelist()
def update_admin_settings(data):
	"""Admin: update store settings."""
	if isinstance(data, str):
		data = json.loads(data)

	settings = frappe.get_single("Store Settings")
	if not settings:
		settings = frappe.new_doc("Store Settings")

	# Update scalar fields
	for field in ["is_enabled", "store_name", "company", "banner_image",
				  "contact_phone", "contact_whatsapp", "default_customer",
				  "default_warehouse", "selling_price_list"]:
		if field in data:
			setattr(settings, field, data[field])

	# Update delivery areas
	if "delivery_areas" in data:
		settings.delivery_areas = []
		for area in data["delivery_areas"]:
			if isinstance(area, dict) and area.get("area_name"):
				settings.append("delivery_areas", {
					"area_name": area["area_name"],
					"delivery_fee": flt(area.get("delivery_fee", 0)),
				})

	settings.flags.ignore_permissions = True
	settings.save()
	frappe.db.commit()

	return {"message": _("Settings updated"), "settings": _get_settings()}


@frappe.whitelist()
def get_admin_items(search=None):
	"""Admin: return all items with their store publication status."""
	conditions = ["i.is_sales_item = 1"]
	params = {}
	if search:
		conditions.append("(i.item_name LIKE %(search)s OR i.name LIKE %(search)s)")
		params["search"] = f"%{search}%"

	where = " AND ".join(conditions)

	rows = frappe.db.sql(f"""
		SELECT
			i.name AS item_code,
			i.item_name,
			i.item_group,
			i.stock_uom,
			i.standard_rate,
			i.image AS item_image,
			i.disabled,
			si.name AS store_item_name,
			si.is_published,
			si.price AS store_price,
			si.image AS store_image,
			si.description AS store_description,
			si.display_order,
			si.max_order_qty
		FROM `tabItem` i
		LEFT JOIN `tabStore Item` si ON i.name = si.item
		WHERE {where}
		ORDER BY si.is_published DESC, i.item_name ASC
		LIMIT 500
	""", params, as_dict=True)

	return rows


@frappe.whitelist()
def toggle_store_item(item_code, is_published):
	"""Admin: toggle publication status of an item."""
	if not item_code:
		frappe.throw(_("Item code is required"))

	is_published = cint(is_published)

	store_item_name = frappe.db.get_value("Store Item", {"item": item_code}, "name")
	if store_item_name:
		si = frappe.get_doc("Store Item", store_item_name)
		si.is_published = is_published
		si.flags.ignore_permissions = True
		si.save()
	else:
		# Create a new Store Item
		si = frappe.new_doc("Store Item")
		si.item = item_code
		si.is_published = is_published
		# validate() will auto-fill price and image
		si.flags.ignore_permissions = True
		si.insert()

	frappe.db.commit()
	return {"message": _("Item publication status updated"), "is_published": is_published}


@frappe.whitelist()
def upsert_store_item(item_code, price=None, image=None, description=None,
					  is_published=None, display_order=None, max_order_qty=None):
	"""Admin: create or update a Store Item record."""
	if not item_code:
		frappe.throw(_("Item code is required"))

	store_item_name = frappe.db.get_value("Store Item", {"item": item_code}, "name")
	if store_item_name:
		si = frappe.get_doc("Store Item", store_item_name)
	else:
		si = frappe.new_doc("Store Item")
		si.item = item_code

	if price is not None:
		si.price = flt(price)
	if image is not None:
		si.image = image
	if description is not None:
		si.description = description
	if is_published is not None:
		si.is_published = cint(is_published)
	if display_order is not None:
		si.display_order = cint(display_order)
	if max_order_qty is not None:
		si.max_order_qty = flt(max_order_qty)

	si.flags.ignore_permissions = True
	if si.is_new:
		si.insert()
	else:
		si.save()

	frappe.db.commit()
	return {"message": _("Store item saved"), "store_item": si.name}


@frappe.whitelist()
def get_delivery_areas():
	"""Admin: return delivery areas from settings."""
	settings = _get_settings()
	if not settings:
		return []
	return settings.get("delivery_areas", [])


# ============================================================
# HELPERS
# ============================================================

def _get_settings():
	"""Get Store Settings as dict (cached)."""
	try:
		doc = frappe.get_single("Store Settings")
		if not doc:
			return None
		areas = []
		for row in doc.delivery_areas:
			areas.append({
				"name": row.name,
				"area_name": row.area_name,
				"delivery_fee": flt(row.delivery_fee or 0),
			})
		return {
			"is_enabled": cint(doc.is_enabled or 0),
			"store_name": doc.store_name or "",
			"company": doc.company or "",
			"banner_image": doc.banner_image or "",
			"contact_phone": doc.contact_phone or "",
			"contact_whatsapp": doc.contact_whatsapp or "",
			"default_customer": doc.default_customer or "",
			"default_warehouse": doc.default_warehouse or "",
			"selling_price_list": doc.selling_price_list or "",
			"delivery_areas": areas,
		}
	except Exception:
		return None


def _default_settings():
	return {
		"is_enabled": 0,
		"store_name": "",
		"company": "",
		"banner_image": "",
		"contact_phone": "",
		"contact_whatsapp": "",
		"default_customer": "",
		"default_warehouse": "",
		"selling_price_list": "",
		"delivery_areas": [],
	}


def _check_rate_limit():
	"""Rate limit: 5 orders per minute per IP."""
	ip = frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "unknown"
	if not ip:
		ip = "unknown"

	cache_key = f"store_order_rate:{ip}"
	now = time.time()
	window = 60  # 1 minute
	max_requests = 5

	try:
		data = frappe.cache().get(cache_key)
		if data:
			data = json.loads(data)
		else:
			data = []
	except (json.JSONDecodeError, TypeError, ValueError):
		data = []

	# Remove entries outside the window
	data = [t for t in data if now - t < window]

	if len(data) >= max_requests:
		frappe.throw(
			_("Too many orders. Please wait a minute and try again."),
			frappe.TooManyRequestsError,
		)

	data.append(now)
	frappe.cache().set(cache_key, json.dumps(data))
	# Set TTL to expire the key
	frappe.cache().expire(cache_key, window)


def _get_or_create_delivery_item(company):
	"""Find or create a 'Delivery Charge' item for adding delivery fees to orders."""
	# Try to find an existing delivery item
	delivery_item = frappe.db.get_value("Item", {"item_name": "Delivery Charge"}, "name")
	if delivery_item:
		return delivery_item

	# Try alternate names
	for name in ["Delivery Fee", "رسوم التوصيل", "توصيل"]:
		delivery_item = frappe.db.get_value("Item", {"item_name": name}, "name")
		if delivery_item:
			return delivery_item

	# Create a new delivery item
	try:
		item = frappe.new_doc("Item")
		item.item_code = "DELIVERY-CHARGE"
		item.item_name = "Delivery Charge"
		item.item_group = frappe.db.get_single_value("Selling Settings", "default_item_group") or "All Item Groups"
		item.stock_uom = "Nos"
		item.is_stock_item = 0
		item.is_sales_item = 1
		item.disabled = 0
		# Add item default for the company
		item.append("item_defaults", {
			"company": company,
			"default_warehouse": frappe.db.get_value("Company", company, "default_warehouse"),
		})
		item.flags.ignore_permissions = True
		item.insert()
		return item.name
	except Exception as e:
		frappe.log_error(f"Failed to create delivery item: {e}")
		return None


# ============================================================
# ADVERTISEMENTS API
# ============================================================

@frappe.whitelist(allow_guest=True)
def get_store_ads():
	"""Public: return active advertisements for display in storefront."""
	today = nowdate()
	rows = frappe.db.sql("""
		SELECT name, title, content, image, link_url, display_order
		FROM `tabStore Advertisement`
		WHERE is_active = 1
		AND (start_date IS NULL OR start_date <= %(today)s)
		AND (end_date IS NULL OR end_date >= %(today)s)
		ORDER BY display_order ASC, creation DESC
	""", {"today": today}, as_dict=True)
	return rows


@frappe.whitelist()
def get_admin_ads():
	"""Admin: return all advertisements."""
	rows = frappe.db.get_all(
		"Store Advertisement",
		fields=["name", "title", "content", "image", "link_url",
				"is_active", "display_order", "start_date", "end_date"],
		order_by="display_order ASC, creation DESC",
	)
	return rows


@frappe.whitelist()
def create_ad(title, content=None, image=None, link_url=None,
			  is_active=1, display_order=0, start_date=None, end_date=None):
	"""Admin: create a new advertisement."""
	ad = frappe.new_doc("Store Advertisement")
	ad.title = title
	ad.content = content or ""
	ad.image = image or ""
	ad.link_url = link_url or ""
	ad.is_active = cint(is_active)
	ad.display_order = cint(display_order)
	ad.start_date = start_date
	ad.end_date = end_date
	ad.flags.ignore_permissions = True
	ad.insert()
	frappe.db.commit()
	return {"message": _("Advertisement created"), "name": ad.name}


@frappe.whitelist()
def update_ad(name, title=None, content=None, image=None, link_url=None,
			  is_active=None, display_order=None, start_date=None, end_date=None):
	"""Admin: update an existing advertisement."""
	if not frappe.db.exists("Store Advertisement", name):
		frappe.throw(_("Advertisement not found"))

	ad = frappe.get_doc("Store Advertisement", name)
	if title is not None:
		ad.title = title
	if content is not None:
		ad.content = content
	if image is not None:
		ad.image = image
	if link_url is not None:
		ad.link_url = link_url
	if is_active is not None:
		ad.is_active = cint(is_active)
	if display_order is not None:
		ad.display_order = cint(display_order)
	if start_date is not None:
		ad.start_date = start_date
	if end_date is not None:
		ad.end_date = end_date
	ad.flags.ignore_permissions = True
	ad.save()
	frappe.db.commit()
	return {"message": _("Advertisement updated"), "name": ad.name}


@frappe.whitelist()
def delete_ad(name):
	"""Admin: delete an advertisement."""
	if not frappe.db.exists("Store Advertisement", name):
		frappe.throw(_("Advertisement not found"))
	frappe.delete_doc("Store Advertisement", name, ignore_permissions=True)
	frappe.db.commit()
	return {"message": _("Advertisement deleted")}


@frappe.whitelist()
def toggle_ad(name, is_active):
	"""Admin: toggle advertisement active status."""
	if not frappe.db.exists("Store Advertisement", name):
		frappe.throw(_("Advertisement not found"))
	ad = frappe.get_doc("Store Advertisement", name)
	ad.is_active = cint(is_active)
	ad.flags.ignore_permissions = True
	ad.save()
	frappe.db.commit()
	return {"message": _("Advertisement status updated"), "is_active": cint(is_active)}
