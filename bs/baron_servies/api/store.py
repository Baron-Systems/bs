# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Store API — public storefront, order tracking and store administration.

Security:
- Public endpoints (allow_guest) accept only non-sensitive data; prices, company,
  warehouse and delivery fees are always resolved on the server.
- Admin endpoints require a store manager role (System Manager / Sales Manager).
- Advertisement HTML is sanitised before it is stored and before it is served.
- Rate limits (Redis): orders per IP and per phone, tracking lookups per IP.

Data flow:
- The storefront (config + groups + items + ads) is served from one cached payload
  (Redis, 5 min) that is cleared whenever a store document changes. Stock is cached
  separately for 1 minute. Order creation never uses the cache.
- Each order is linked to a Customer matched or created by phone number and saved as
  a draft Sales Order with store_status "New".
- Lifecycle: New → Confirmed (Sales Order submitted) → Out for Delivery → Delivered
  (Sales Invoice with stock update, optionally paid in cash) or → Cancelled.
"""

from __future__ import unicode_literals

import json
import re
import time

import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate
from frappe.utils.html_utils import sanitize_html

STORE_MANAGER_ROLES = {"System Manager", "Sales Manager"}
SETTINGS_DOCTYPE = "Store Settings"

CACHE_KEY = "bs_store:storefront"
CACHE_TTL = 300
STOCK_CACHE_KEY = "bs_store:stock"
STOCK_CACHE_TTL = 60

ORDER_SOURCE = "Online Store"
ORDER_STATUSES = ("New", "Confirmed", "Out for Delivery", "Delivered", "Cancelled")
STATUS_TRANSITIONS = {
	"New": {"Confirmed", "Cancelled"},
	"Confirmed": {"Out for Delivery", "Delivered", "Cancelled"},
	"Out for Delivery": {"Delivered", "Cancelled"},
	"Delivered": set(),
	"Cancelled": set(),
}
DELIVERY_ITEM_CODE = "DELIVERY-CHARGE"

MAX_CART_LINES = 100
ORDER_RATE_PER_IP = (5, 60)  # 5 orders / minute / IP
ORDER_RATE_PER_PHONE = (10, 24 * 3600)  # 10 orders / day / phone
TRACK_RATE_PER_IP = (20, 60)


# ============================================================
# Helpers: permissions, settings, cache
# ============================================================

def _require_store_manager():
	user = frappe.session.user
	if user == "Administrator" or STORE_MANAGER_ROLES.intersection(frappe.get_roles(user)):
		return
	frappe.throw(_("ليس لديك صلاحية إدارة المتجر"), frappe.PermissionError)


def _settings():
	return frappe.get_cached_doc(SETTINGS_DOCTYPE)


def missing_settings(s=None):
	"""Labels of settings required before the store can take orders."""
	s = s or _settings()
	missing = []
	if not s.company:
		missing.append(_("الشركة"))
	if not s.default_warehouse:
		missing.append(_("المستودع"))
	if not s.selling_price_list:
		missing.append(_("قائمة الأسعار"))
	return missing


def clear_store_cache(*_args, **_kwargs):
	"""Drop cached storefront data (called from store document controllers)."""
	frappe.cache().delete_value([CACHE_KEY, STOCK_CACHE_KEY])


def _rate_limit(key, limit, window, message):
	cache = frappe.cache()
	now = time.time()
	try:
		hits = [t for t in json.loads(cache.get_value(key) or "[]") if now - t < window]
	except (TypeError, ValueError):
		hits = []
	if len(hits) >= limit:
		frappe.throw(message, frappe.TooManyRequestsError)
	hits.append(now)
	cache.set_value(key, json.dumps(hits), expires_in_sec=window)


def _client_ip():
	return getattr(frappe.local, "request_ip", None) or "unknown"


def normalize_phone(value):
	"""Local form of a phone number: digits only, country code (970/972) → leading 0.

	"+970-592804775", "00972592804775" and "0592804775" all become "0592804775".
	"""
	digits = re.sub(r"\D", "", str(value or ""))
	if digits.startswith("00"):
		digits = digits[2:]
	for code in ("970", "972"):
		if digits.startswith(code) and len(digits) > 9:
			digits = "0" + digits[len(code):]
			break
	if len(digits) == 9 and digits.startswith("5"):
		digits = "0" + digits
	return digits


# ============================================================
# Catalogue: prices, stock, items
# ============================================================

def _price_list_rates(item_codes, price_list):
	"""{item_code: rate} from the selling price list (valid today, stock-UOM rows first)."""
	if not item_codes or not price_list:
		return {}
	today = nowdate()
	rows = frappe.db.sql(
		"""
		select ip.item_code, ip.price_list_rate,
			(case when coalesce(ip.uom, '') in ('', i.stock_uom) then 0 else 1 end) as uom_rank
		from `tabItem Price` ip
		join `tabItem` i on i.name = ip.item_code
		where ip.price_list = %(pl)s and ip.selling = 1 and ip.item_code in %(codes)s
			and (ip.valid_from is null or ip.valid_from <= %(today)s)
			and (ip.valid_upto is null or ip.valid_upto >= %(today)s)
		order by uom_rank asc, ip.valid_from desc, ip.modified desc
		""",
		{"pl": price_list, "codes": list(item_codes), "today": today},
		as_dict=True,
	)
	rates = {}
	for r in rows:
		rates.setdefault(r.item_code, flt(r.price_list_rate))
	return rates


def resolve_prices(items, price_list):
	"""Single source of truth for store prices.

	Store Item price (> 0) is an explicit override; otherwise the selling price list;
	otherwise Item.standard_rate. `items` rows need item_code, store_price, standard_rate.
	"""
	pl_rates = _price_list_rates({r["item_code"] for r in items}, price_list)
	prices = {}
	for r in items:
		code = r["item_code"]
		if flt(r.get("store_price")) > 0:
			prices[code] = (flt(r["store_price"]), "store")
		elif flt(pl_rates.get(code)) > 0:
			prices[code] = (flt(pl_rates[code]), "price_list")
		elif flt(r.get("standard_rate")) > 0:
			prices[code] = (flt(r["standard_rate"]), "standard_rate")
		else:
			prices[code] = (0.0, None)
	return prices


def _stock_map(warehouse, use_cache=True):
	"""{item_code: actual_qty} for published store items in the store warehouse."""
	if not warehouse:
		return {}
	cache = frappe.cache()
	if use_cache:
		cached = cache.get_value(STOCK_CACHE_KEY)
		if cached is not None:
			return cached
	warehouses = [warehouse]
	if frappe.db.get_value("Warehouse", warehouse, "is_group"):
		warehouses = frappe.db.get_descendants("Warehouse", warehouse) or [warehouse]
	rows = frappe.db.sql(
		"""
		select b.item_code, sum(b.actual_qty) as qty
		from `tabBin` b
		join `tabStore Item` si on si.item = b.item_code and si.is_published = 1
		where b.warehouse in %(whs)s
		group by b.item_code
		""",
		{"whs": warehouses},
		as_dict=True,
	)
	stock = {r.item_code: flt(r.qty) for r in rows}
	if use_cache:
		cache.set_value(STOCK_CACHE_KEY, stock, expires_in_sec=STOCK_CACHE_TTL)
	return stock


def _published_items(item_codes=None):
	conditions = ["si.is_published = 1", "i.disabled = 0", "i.is_sales_item = 1"]
	params = {}
	if item_codes is not None:
		if not item_codes:
			return []
		conditions.append("si.item in %(codes)s")
		params["codes"] = list(item_codes)
	return frappe.db.sql(
		f"""
		select si.item as item_code, coalesce(nullif(si.item_name, ''), i.item_name) as item_name,
			coalesce(nullif(si.item_group, ''), i.item_group) as item_group,
			coalesce(nullif(si.stock_uom, ''), i.stock_uom) as stock_uom,
			si.price as store_price, i.standard_rate, coalesce(nullif(si.image, ''), i.image) as image,
			si.description, si.display_order, si.max_order_qty, si.is_unavailable
		from `tabStore Item` si
		join `tabItem` i on i.name = si.item
		where {' and '.join(conditions)}
		order by si.display_order asc, item_name asc
		""",
		params,
		as_dict=True,
	)


def _clean_ad(ad):
	ad["content"] = sanitize_html(ad.get("content") or "")
	link = (ad.get("link_url") or "").strip()
	ad["link_url"] = link if re.match(r"^(https?://|/)", link) else ""
	return ad


def _public_config(s):
	return {
		"is_enabled": 1 if cint(s.is_enabled) and not missing_settings(s) else 0,
		"store_name": s.store_name or "",
		"banner_image": s.banner_image or "",
		"contact_phone": s.contact_phone or "",
		"contact_whatsapp": s.contact_whatsapp or "",
		"currency": frappe.get_cached_value("Company", s.company, "default_currency") if s.company else "",
		# area_name is matched exactly when ordering, so it is shown as stored
		"delivery_areas": [{"area_name": a.area_name, "delivery_fee": flt(a.delivery_fee)} for a in s.delivery_areas],
	}


def _build_storefront():
	s = _settings()
	config = _public_config(s)
	if not config["is_enabled"]:
		return {"config": config, "groups": [], "items": [], "ads": []}

	items = _published_items()
	prices = resolve_prices(items, s.selling_price_list)
	out_items = []
	for it in items:
		price, _source = prices[it.item_code]
		if price <= 0:
			continue  # an item without a price cannot be ordered — keep it off the shelf
		out_items.append({
			"item_code": it.item_code,
			"item_name": (it.item_name or "").strip(),
			"item_group": it.item_group,
			"stock_uom": it.stock_uom,
			"price": price,
			"image": it.image,
			"description": it.description,
			"max_order_qty": flt(it.max_order_qty),
			"is_unavailable": cint(it.is_unavailable),
		})

	ads = frappe.db.sql(
		"""
		select name, title, content, image, link_url, display_order
		from `tabStore Advertisement`
		where is_active = 1
			and (start_date is null or start_date <= %(today)s)
			and (end_date is null or end_date >= %(today)s)
		order by display_order asc, creation desc
		""",
		{"today": nowdate()},
		as_dict=True,
	)
	groups = sorted({it["item_group"] for it in out_items if it["item_group"]})
	return {"config": config, "groups": groups, "items": out_items, "ads": [_clean_ad(a) for a in ads]}


def _apply_stock(payload):
	"""Mark / hide items according to the out-of-stock policy (fresh-ish stock, 1 min cache)."""
	s = _settings()
	policy = s.out_of_stock_policy or "Allow"
	stock = _stock_map(s.default_warehouse) if policy != "Allow" else {}
	items = []
	for it in payload["items"]:
		sold_out = bool(it["is_unavailable"]) or (policy != "Allow" and flt(stock.get(it["item_code"])) <= 0)
		if sold_out and policy == "Hide" and not it["is_unavailable"]:
			continue
		row = dict(it)
		row["sold_out"] = 1 if sold_out else 0
		row.pop("is_unavailable", None)
		items.append(row)
	return {**payload, "items": items, "groups": sorted({i["item_group"] for i in items if i["item_group"]})}


# ============================================================
# PUBLIC APIs (allow_guest = True)
# ============================================================

@frappe.whitelist(allow_guest=True)
def get_storefront():
	"""Public: everything the storefront needs in one (cached) call."""
	payload = frappe.cache().get_value(CACHE_KEY)
	if payload is None:
		payload = _build_storefront()
		frappe.cache().set_value(CACHE_KEY, payload, expires_in_sec=CACHE_TTL)
	return _apply_stock(payload)


@frappe.whitelist(allow_guest=True)
def get_store_config():
	"""Public (legacy): store config only."""
	return get_storefront()["config"]


@frappe.whitelist(allow_guest=True)
def get_store_items(group=None, search=None):
	"""Public (legacy): published items, optionally filtered."""
	items = get_storefront()["items"]
	if group:
		items = [i for i in items if i["item_group"] == group]
	if search:
		q = search.strip().lower()
		items = [i for i in items if q in (i["item_name"] or "").lower() or q in i["item_code"].lower()]
	return items


@frappe.whitelist(allow_guest=True)
def get_store_item_groups():
	"""Public (legacy)."""
	return get_storefront()["groups"]


@frappe.whitelist(allow_guest=True)
def get_store_ads():
	"""Public (legacy)."""
	return get_storefront()["ads"]


@frappe.whitelist(allow_guest=True)
def create_store_order(customer_name, phone, delivery_area=None, address=None, items=None, notes=None):
	"""Public: create a draft Sales Order from the store cart.

	Only item_code + qty are taken from the client; everything else is resolved here.
	"""
	_rate_limit(f"bs_store:order_ip:{_client_ip()}", *ORDER_RATE_PER_IP,
		_("طلبات كثيرة خلال وقت قصير، يرجى المحاولة بعد دقيقة"))

	s = _settings()
	if not cint(s.is_enabled) or missing_settings(s):
		frappe.throw(_("المتجر غير متاح حالياً"), frappe.PermissionError)

	customer_name = (customer_name or "").strip()[:140]
	address = (address or "").strip()[:500]
	notes = (notes or "").strip()[:1000]
	delivery_area = (delivery_area or "").strip()
	phone_key = normalize_phone(phone)

	if not customer_name:
		frappe.throw(_("الاسم مطلوب"))
	if not 7 <= len(phone_key) <= 15:
		frappe.throw(_("رقم الهاتف غير صحيح"))
	if not address:
		frappe.throw(_("العنوان مطلوب"))

	_rate_limit(f"bs_store:order_phone:{phone_key}", *ORDER_RATE_PER_PHONE,
		_("تم تجاوز عدد الطلبات المسموح لهذا الرقم اليوم"))

	delivery_fee = 0
	if s.delivery_areas:
		area = next((a for a in s.delivery_areas if a.area_name == delivery_area), None)
		if not area:
			frappe.throw(_("يرجى اختيار منطقة التوصيل"))
		delivery_fee = flt(area.delivery_fee)

	lines = _validated_lines(items, s)
	customer = get_or_create_store_customer(customer_name, phone_key, s)

	so = frappe.new_doc("Sales Order")
	so.update({
		"customer": customer,
		"company": s.company,
		"transaction_date": nowdate(),
		"delivery_date": nowdate(),
		"set_warehouse": s.default_warehouse,
		"selling_price_list": s.selling_price_list,
		"ignore_pricing_rule": 1,
		"store_customer_name": customer_name,
		"store_phone": phone_key,
		"store_delivery_area": delivery_area,
		"store_delivery_fee": delivery_fee,
		"store_address": address,
		"store_notes": notes,
		"store_order_source": ORDER_SOURCE,
		"store_status": "New",
	})
	for line in lines:
		so.append("items", {**line, "warehouse": s.default_warehouse, "delivery_date": nowdate()})
	if delivery_fee > 0:
		code, uom = _delivery_item()
		so.append("items", {
			"item_code": code, "qty": 1, "rate": delivery_fee, "price_list_rate": delivery_fee,
			"uom": uom, "warehouse": s.default_warehouse, "delivery_date": nowdate(),
		})
	so.flags.ignore_permissions = True
	so.insert()

	return {
		"sales_order": so.name,
		"total": flt(so.grand_total),
		"currency": so.currency,
		"phone": phone_key,
		"message": _("تم استلام طلبك"),
	}


def _validated_lines(items, s):
	"""Merge, validate and price the cart lines (fresh data — no cache)."""
	if isinstance(items, str):
		try:
			items = json.loads(items)
		except ValueError:
			frappe.throw(_("بيانات السلة غير صحيحة"))
	if not items or not isinstance(items, list):
		frappe.throw(_("السلة فارغة"))

	qty_by_code = {}
	for entry in items:
		if not isinstance(entry, dict):
			continue
		code = str(entry.get("item_code") or "").strip()
		qty = flt(entry.get("qty"))
		if not code:
			continue
		if qty <= 0:
			frappe.throw(_("كمية غير صحيحة"))
		qty_by_code[code] = qty_by_code.get(code, 0) + qty
	if not qty_by_code:
		frappe.throw(_("السلة فارغة"))
	if len(qty_by_code) > MAX_CART_LINES:
		frappe.throw(_("عدد الأصناف في السلة كبير جداً (الحد {0})").format(MAX_CART_LINES))

	published = {r.item_code: r for r in _published_items(qty_by_code.keys())}
	prices = resolve_prices(list(published.values()), s.selling_price_list)
	policy = s.out_of_stock_policy or "Allow"
	stock = _stock_map(s.default_warehouse, use_cache=False) if policy != "Allow" else {}

	lines = []
	for code, qty in qty_by_code.items():
		it = published.get(code)
		if not it:
			frappe.throw(_("الصنف {0} غير متوفر في المتجر").format(code))
		if cint(it.is_unavailable):
			frappe.throw(_("{0} غير متوفر حالياً").format(it.item_name))
		if flt(it.max_order_qty) > 0 and qty > flt(it.max_order_qty):
			frappe.throw(_("أقصى كمية لـ {0} هي {1}").format(it.item_name, flt(it.max_order_qty)))
		if policy != "Allow" and qty > flt(stock.get(code)):
			available = max(0, flt(stock.get(code)))
			frappe.throw(_("الكمية المتوفرة من {0}: {1}").format(it.item_name, available))
		rate = prices[code][0]
		if rate <= 0:
			frappe.throw(_("{0} غير متاح للطلب حالياً").format(it.item_name))
		lines.append({"item_code": code, "item_name": it.item_name, "qty": qty, "rate": rate,
			"price_list_rate": rate, "uom": it.stock_uom})
	return lines


def get_or_create_store_customer(customer_name, phone_key, s=None):
	"""Customer for a phone number: existing customer (customer / contact phone), else a new one."""
	s = s or _settings()
	tail = phone_key[-9:]
	like = f"%{tail}"
	candidates = frappe.db.sql(
		"""
		select name, mobile_no as phone from `tabCustomer` where disabled = 0 and mobile_no like %(like)s
		union
		select dl.link_name as name, cp.phone from `tabContact Phone` cp
		join `tabDynamic Link` dl on dl.parent = cp.parent and dl.parenttype = 'Contact' and dl.link_doctype = 'Customer'
		join `tabCustomer` c on c.name = dl.link_name and c.disabled = 0
		where cp.phone like %(like)s
		""",
		{"like": like},
		as_dict=True,
	)
	for c in candidates:
		if normalize_phone(c.phone) == phone_key:
			return c.name

	selling = frappe.get_cached_doc("Selling Settings")
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": customer_name,
		"customer_type": "Individual",
		"customer_group": s.customer_group or selling.customer_group,
		"territory": s.territory or selling.territory,
		"mobile_no": phone_key,
	})
	customer.flags.ignore_permissions = True
	customer.insert()
	return customer.name


def _delivery_item():
	"""(item_code, uom) of the non-stock 'delivery charge' item — created on first use."""
	for filters in ({"name": DELIVERY_ITEM_CODE}, {"item_name": ["in", ["Delivery Charge", "Delivery Fee", "رسوم التوصيل", "توصيل"]]}):
		row = frappe.db.get_value("Item", {**filters, "disabled": 0}, ["name", "stock_uom"], as_dict=True)
		if row:
			return row.name, row.stock_uom

	stock = frappe.get_cached_doc("Stock Settings")
	item_group = stock.item_group if stock.item_group and not frappe.db.get_value("Item Group", stock.item_group, "is_group") \
		else frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	uom = stock.stock_uom or ("Nos" if frappe.db.exists("UOM", "Nos") else frappe.db.get_value("UOM", {"enabled": 1}, "name"))
	if not item_group or not uom:
		frappe.throw(_("تعذر إنشاء صنف رسوم التوصيل: يرجى ضبط مجموعة الأصناف والوحدة الافتراضية في إعدادات المخزون"))
	item = frappe.get_doc({
		"doctype": "Item",
		"item_code": DELIVERY_ITEM_CODE,
		"item_name": "رسوم التوصيل",
		"item_group": item_group,
		"stock_uom": uom,
		"is_stock_item": 0,
		"is_sales_item": 1,
		"include_item_in_manufacturing": 0,
	})
	item.flags.ignore_permissions = True
	item.insert()
	return item.name, item.stock_uom


@frappe.whitelist(allow_guest=True)
def track_store_order(order, phone):
	"""Public: order status for the customer — requires the order number and its phone."""
	_rate_limit(f"bs_store:track_ip:{_client_ip()}", *TRACK_RATE_PER_IP,
		_("محاولات كثيرة، يرجى المحاولة بعد دقيقة"))
	order = (order or "").strip()
	phone_key = normalize_phone(phone)
	so = frappe.db.get_value(
		"Sales Order",
		{"name": order, "store_order_source": ORDER_SOURCE},
		["name", "store_phone", "store_status", "transaction_date", "grand_total", "currency",
			"store_delivery_area", "store_delivery_fee", "creation"],
		as_dict=True,
	)
	if not so or not phone_key or normalize_phone(so.store_phone) != phone_key:
		frappe.throw(_("لم يتم العثور على طلب بهذا الرقم والهاتف"))
	items = frappe.get_all(
		"Sales Order Item",
		filters={"parent": so.name, "item_code": ["!=", DELIVERY_ITEM_CODE]},
		fields=["item_name", "qty", "rate", "amount"],
		order_by="idx asc",
	)
	return {
		"order": so.name,
		"status": so.store_status or "New",
		"date": so.creation,
		"total": flt(so.grand_total),
		"currency": so.currency,
		"delivery_area": so.store_delivery_area,
		"delivery_fee": flt(so.store_delivery_fee),
		"items": items,
	}


# ============================================================
# ADMIN APIs — settings, items, ads
# ============================================================

SETTINGS_FIELDS = [
	"is_enabled", "store_name", "company", "banner_image", "contact_phone", "contact_whatsapp",
	"default_warehouse", "selling_price_list", "customer_group", "territory", "out_of_stock_policy",
	"delivery_mode_of_payment",
]


@frappe.whitelist()
def get_admin_settings():
	_require_store_manager()
	s = frappe.get_single(SETTINGS_DOCTYPE)
	data = {f: s.get(f) for f in SETTINGS_FIELDS}
	data["is_enabled"] = cint(s.is_enabled)
	data["out_of_stock_policy"] = s.out_of_stock_policy or "Allow"
	data["delivery_areas"] = [{"area_name": a.area_name, "delivery_fee": flt(a.delivery_fee)} for a in s.delivery_areas]
	data["missing"] = missing_settings(s)
	data["options"] = {
		"customer_groups": frappe.get_all("Customer Group", {"is_group": 0}, pluck="name", order_by="name"),
		"territories": frappe.get_all("Territory", {"is_group": 0}, pluck="name", order_by="name"),
		"modes_of_payment": frappe.get_all("Mode of Payment", {"enabled": 1}, pluck="name", order_by="name"),
	}
	return data


@frappe.whitelist()
def update_admin_settings(data):
	_require_store_manager()
	if isinstance(data, str):
		data = json.loads(data)
	s = frappe.get_single(SETTINGS_DOCTYPE)
	for field in SETTINGS_FIELDS:
		if field in data:
			s.set(field, data[field])
	if "delivery_areas" in data:
		s.set("delivery_areas", [])
		for area in data["delivery_areas"] or []:
			if isinstance(area, dict) and (area.get("area_name") or "").strip():
				s.append("delivery_areas", {"area_name": area["area_name"].strip(), "delivery_fee": flt(area.get("delivery_fee"))})
	s.flags.ignore_permissions = True
	s.save()
	return {"message": _("تم حفظ الإعدادات"), "settings": get_admin_settings()}


@frappe.whitelist()
def get_admin_items(search=None, only_published=0):
	"""Admin: sales items with their store status, effective price and stock."""
	_require_store_manager()
	s = _settings()
	conditions = ["i.is_sales_item = 1", "i.disabled = 0", "i.name != %(delivery)s"]
	params = {"delivery": DELIVERY_ITEM_CODE}
	if search:
		conditions.append("(i.item_name like %(search)s or i.name like %(search)s)")
		params["search"] = f"%{search}%"
	if cint(only_published):
		conditions.append("si.is_published = 1")
	rows = frappe.db.sql(
		f"""
		select i.name as item_code, i.item_name, i.item_group, i.stock_uom, i.standard_rate,
			i.image as item_image, si.name as store_item_name, coalesce(si.is_published, 0) as is_published,
			coalesce(si.is_unavailable, 0) as is_unavailable, si.price as store_price, si.image as store_image,
			si.description as store_description, si.display_order, si.max_order_qty
		from `tabItem` i
		left join `tabStore Item` si on si.item = i.name
		where {' and '.join(conditions)}
		order by is_published desc, i.item_name asc
		limit 500
		""",
		params,
		as_dict=True,
	)
	prices = resolve_prices(rows, s.selling_price_list)
	stock = _stock_map(s.default_warehouse, use_cache=False)
	extra = {r.item_code for r in rows if not r.is_published}
	if extra and s.default_warehouse:  # stock for unpublished rows too
		for b in frappe.get_all("Bin", {"item_code": ["in", list(extra)], "warehouse": s.default_warehouse},
				["item_code", "actual_qty"]):
			stock[b.item_code] = flt(b.actual_qty)
	for r in rows:
		r["effective_price"], r["price_source"] = prices[r.item_code]
		r["actual_qty"] = flt(stock.get(r.item_code))
	return rows


def _store_item(item_code):
	name = frappe.db.get_value("Store Item", {"item": item_code}, "name")
	if name:
		return frappe.get_doc("Store Item", name)
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("الصنف غير موجود"))
	si = frappe.new_doc("Store Item")
	si.item = item_code
	return si


def _save_store_item(si):
	si.flags.ignore_permissions = True
	if si.is_new():
		si.insert()
	else:
		si.save()
	return si


@frappe.whitelist()
def toggle_store_item(item_code, is_published):
	_require_store_manager()
	si = _store_item(item_code)
	si.is_published = cint(is_published)
	_save_store_item(si)
	return {"message": _("تم تحديث حالة النشر"), "is_published": si.is_published}


@frappe.whitelist()
def set_store_item_unavailable(item_code, is_unavailable):
	_require_store_manager()
	si = _store_item(item_code)
	si.is_unavailable = cint(is_unavailable)
	_save_store_item(si)
	return {"is_unavailable": si.is_unavailable}


@frappe.whitelist()
def upsert_store_item(item_code, price=None, image=None, description=None,
		is_published=None, display_order=None, max_order_qty=None, is_unavailable=None):
	"""Admin: create or update a Store Item (price 0 = use the price list)."""
	_require_store_manager()
	if not item_code:
		frappe.throw(_("Item code is required"))
	si = _store_item(item_code)
	if price is not None:
		si.price = max(0, flt(price))
	if image is not None:
		si.image = image
	if description is not None:
		si.description = description
	if is_published is not None:
		si.is_published = cint(is_published)
	if is_unavailable is not None:
		si.is_unavailable = cint(is_unavailable)
	if display_order is not None:
		si.display_order = cint(display_order)
	if max_order_qty is not None:
		si.max_order_qty = max(0, flt(max_order_qty))
	_save_store_item(si)
	return {"message": _("تم حفظ الصنف"), "store_item": si.name}


@frappe.whitelist()
def get_delivery_areas():
	_require_store_manager()
	return [{"area_name": a.area_name, "delivery_fee": flt(a.delivery_fee)} for a in _settings().delivery_areas]


@frappe.whitelist()
def get_admin_ads():
	_require_store_manager()
	return frappe.db.get_all(
		"Store Advertisement",
		fields=["name", "title", "content", "image", "link_url", "is_active", "display_order", "start_date", "end_date"],
		order_by="display_order asc, creation desc",
	)


@frappe.whitelist()
def create_ad(title, content=None, image=None, link_url=None, is_active=1, display_order=0, start_date=None, end_date=None):
	_require_store_manager()
	ad = frappe.new_doc("Store Advertisement")
	ad.update({
		"title": title, "content": content or "", "image": image or "", "link_url": link_url or "",
		"is_active": cint(is_active), "display_order": cint(display_order),
		"start_date": start_date or None, "end_date": end_date or None,
	})
	ad.flags.ignore_permissions = True
	ad.insert()
	return {"message": _("تم إنشاء الإعلان"), "name": ad.name}


@frappe.whitelist()
def update_ad(name, title=None, content=None, image=None, link_url=None,
		is_active=None, display_order=None, start_date=None, end_date=None):
	_require_store_manager()
	ad = frappe.get_doc("Store Advertisement", name)
	for field, value in (("title", title), ("content", content), ("image", image), ("link_url", link_url)):
		if value is not None:
			ad.set(field, value)
	if is_active is not None:
		ad.is_active = cint(is_active)
	if display_order is not None:
		ad.display_order = cint(display_order)
	if start_date is not None:
		ad.start_date = start_date or None
	if end_date is not None:
		ad.end_date = end_date or None
	ad.flags.ignore_permissions = True
	ad.save()
	return {"message": _("تم تحديث الإعلان"), "name": ad.name}


@frappe.whitelist()
def delete_ad(name):
	_require_store_manager()
	frappe.delete_doc("Store Advertisement", name, ignore_permissions=True)
	return {"message": _("تم حذف الإعلان")}


@frappe.whitelist()
def toggle_ad(name, is_active):
	_require_store_manager()
	ad = frappe.get_doc("Store Advertisement", name)
	ad.is_active = cint(is_active)
	ad.flags.ignore_permissions = True
	ad.save()
	return {"message": _("تم تحديث حالة الإعلان"), "is_active": ad.is_active}


# ============================================================
# ADMIN APIs — orders
# ============================================================

ORDER_LIST_FIELDS = [
	"name", "customer", "store_customer_name", "store_phone", "store_delivery_area", "store_address",
	"store_status", "grand_total", "currency", "docstatus", "creation", "store_invoice",
]


@frappe.whitelist()
def get_store_orders(status=None, search=None, limit=200):
	_require_store_manager()
	filters = {"store_order_source": ORDER_SOURCE}
	if status:
		filters["store_status"] = status
	or_filters = None
	if search:
		like = f"%{search.strip()}%"
		or_filters = [["name", "like", like], ["store_customer_name", "like", like], ["store_phone", "like", like]]
	rows = frappe.get_all("Sales Order", filters=filters, or_filters=or_filters, fields=ORDER_LIST_FIELDS,
		order_by="creation desc", limit_page_length=cint(limit) or 200)
	counts = dict(frappe.db.sql(
		"""select coalesce(store_status, 'New'), count(*) from `tabSales Order`
		where store_order_source = %s group by coalesce(store_status, 'New')""",
		ORDER_SOURCE,
	))
	return {"rows": rows, "counts": {st: cint(counts.get(st)) for st in ORDER_STATUSES}}


@frappe.whitelist()
def get_new_orders_count():
	_require_store_manager()
	return frappe.db.count("Sales Order", {"store_order_source": ORDER_SOURCE, "store_status": "New"})


def _get_order(name):
	so = frappe.get_doc("Sales Order", name)
	if so.store_order_source != ORDER_SOURCE:
		frappe.throw(_("هذا ليس طلباً من المتجر"))
	return so


@frappe.whitelist()
def get_store_order(name):
	_require_store_manager()
	so = _get_order(name)
	s = _settings()
	codes = [i.item_code for i in so.items]
	stock = {}
	if s.default_warehouse and codes:
		for b in frappe.get_all("Bin", {"item_code": ["in", codes], "warehouse": s.default_warehouse}, ["item_code", "actual_qty"]):
			stock[b.item_code] = flt(b.actual_qty)
	customer_phone = frappe.db.get_value("Customer", so.customer, "mobile_no")
	return {
		**{f: so.get(f) for f in ORDER_LIST_FIELDS},
		"store_notes": so.store_notes,
		"store_delivery_fee": flt(so.store_delivery_fee),
		"customer_phone": customer_phone,
		"status": so.store_status or "New",
		"next_statuses": sorted(STATUS_TRANSITIONS.get(so.store_status or "New", set()), key=ORDER_STATUSES.index),
		"items": [
			{"name": i.name, "item_code": i.item_code, "item_name": i.item_name, "qty": flt(i.qty), "rate": flt(i.rate),
				"amount": flt(i.amount), "uom": i.uom, "actual_qty": stock.get(i.item_code),
				"is_delivery": i.item_code == DELIVERY_ITEM_CODE}
			for i in so.items
		],
		"total": flt(so.total),
		"modes_of_payment": frappe.get_all("Mode of Payment", {"enabled": 1}, pluck="name", order_by="name"),
		"default_mode_of_payment": s.delivery_mode_of_payment,
	}


@frappe.whitelist()
def update_store_order_items(name, items):
	"""Admin: change quantities / remove lines while the order is still New (draft)."""
	_require_store_manager()
	so = _get_order(name)
	if so.docstatus != 0 or (so.store_status or "New") != "New":
		frappe.throw(_("يمكن تعديل الطلب فقط قبل تأكيده"))
	if isinstance(items, str):
		items = json.loads(items)
	qty_by_row = {r.get("name"): flt(r.get("qty")) for r in items or [] if r.get("name")}
	keep = []
	for row in so.items:
		if row.item_code == DELIVERY_ITEM_CODE:
			keep.append(row)
			continue
		qty = qty_by_row.get(row.name, flt(row.qty))
		if qty > 0:
			row.qty = qty
			keep.append(row)
	if not any(r.item_code != DELIVERY_ITEM_CODE for r in keep):
		frappe.throw(_("لا يمكن أن يكون الطلب بدون أصناف — استخدم الإلغاء"))
	so.set("items", keep)
	so.flags.ignore_permissions = True
	so.save()
	return get_store_order(so.name)


@frappe.whitelist()
def set_store_order_status(name, status, paid=1, mode_of_payment=None):
	"""Admin: move an order through its lifecycle (see STATUS_TRANSITIONS)."""
	_require_store_manager()
	so = _get_order(name)
	current = so.store_status or "New"
	if status not in STATUS_TRANSITIONS.get(current, set()):
		frappe.throw(_("لا يمكن نقل الطلب من {0} إلى {1}").format(_(current), _(status)))

	if status == "Confirmed":
		so.flags.ignore_permissions = True
		so.submit()
	elif status == "Delivered":
		if so.docstatus == 0:
			so.flags.ignore_permissions = True
			so.submit()
		invoice = _make_delivery_invoice(so, cint(paid), mode_of_payment)
		so.db_set("store_invoice", invoice)
	elif status == "Cancelled":
		if so.docstatus == 1:
			so.flags.ignore_permissions = True
			so.cancel()
	so.db_set("store_status", status)
	return get_store_order(so.name)


def _make_delivery_invoice(so, paid, mode_of_payment=None):
	"""Sales Invoice from the order (stock leaves the warehouse) + cash Payment Entry if paid."""
	from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

	si = make_sales_invoice(so.name)
	si.update_stock = 1
	si.set_posting_time = 1
	si.posting_date = nowdate()
	si.due_date = nowdate()
	for row in si.items:
		if not row.warehouse:
			row.warehouse = so.set_warehouse
	si.flags.ignore_permissions = True
	si.insert()
	si.submit()

	if paid and flt(si.outstanding_amount) > 0:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
		from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account

		mode_of_payment = mode_of_payment or _settings().delivery_mode_of_payment or "Cash"
		pe = get_payment_entry("Sales Invoice", si.name)
		pe.mode_of_payment = mode_of_payment
		pe.paid_to = get_bank_cash_account(mode_of_payment, si.company)["account"]
		pe.reference_no = si.name
		pe.reference_date = nowdate()
		pe.flags.ignore_permissions = True
		pe.insert()
		pe.submit()
	return si.name
