# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Quick Purchase Invoice API.

Creates a Purchase Invoice document as a draft (docstatus=0).
Optional: update each item's last purchase price and the default buying
price list based on the newly entered rates.
"""

from __future__ import unicode_literals

import json

import frappe
from frappe import _
from frappe.query_builder import DocType, functions as fn
from frappe.utils import add_days, cint, flt, nowdate
from pypika import Order


# =============================================================================
# Permission helpers
# =============================================================================

def _check_purchase_invoice_permission(action="create"):
	if not frappe.has_permission("Purchase Invoice", action):
		frappe.throw(
			_("You do not have {0} permission on Purchase Invoice").format(_(action)),
			frappe.PermissionError,
		)


def _check_company_permission(company):
	if company and not frappe.has_permission("Company", "read", doc=company):
		frappe.throw(
			_("You do not have permission to access Company {0}").format(company),
			frappe.PermissionError,
		)


# =============================================================================
# Whitelisted endpoints
# =============================================================================

@frappe.whitelist()
def get_suppliers_for_purchase_invoice(search_term="", limit=50):
	"""Search active suppliers for the quick purchase invoice page."""
	filters = {"disabled": 0}

	or_filters = []
	if search_term:
		like = f"%{search_term}%"
		or_filters = [
			["name", "like", like],
			["supplier_name", "like", like],
			["mobile_no", "like", like],
			["email_id", "like", like],
		]

	return frappe.get_all(
		"Supplier",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "supplier_name", "mobile_no", "email_id", "supplier_group", "supplier_type"],
		limit_page_length=int(limit) if limit else 50,
		order_by="supplier_name asc",
	)


@frappe.whitelist()
def search_items_for_purchase_invoice(search_term, company, warehouse=None, limit=20):
	"""Search stock items for the Quick Purchase Invoice page."""
	if not company:
		frappe.throw(_("Company is required"))

	_check_company_permission(company)

	search_term = (search_term or "").strip()
	limit = cint(limit) or 20

	Item = DocType("Item")
	qb = frappe.qb

	# Barcode exact match
	if search_term:
		barcode_parent = frappe.db.get_value("Item Barcode", {"barcode": search_term}, "parent")
		if barcode_parent:
			item_row = frappe.db.get_value(
				"Item",
				{"name": barcode_parent, "disabled": 0, "is_stock_item": 1},
				[
					"name as item_code", "item_name", "stock_uom", "image",
					"last_purchase_rate", "has_batch_no", "has_serial_no",
				],
				as_dict=True,
			)
			if item_row:
				item_company = frappe.db.get_value("Item", barcode_parent, "custom_company") or ""
				if item_company in ("", company):
					items = [item_row]
					return _enrich_items(items, company, warehouse)

	query = (
		qb.from_(Item)
		.select(
			Item.name.as_("item_code"),
			Item.item_name,
			Item.stock_uom,
			Item.image,
			Item.last_purchase_rate,
			Item.has_batch_no,
			Item.has_serial_no,
		)
		.where(Item.disabled == 0)
		.where(Item.is_stock_item == 1)
		.where(fn.Coalesce(Item.has_variants, 0) == 0)
		.where(fn.Coalesce(Item.custom_company, "").isin([company, ""]))
	)

	if search_term:
		words = [w.strip() for w in search_term.split() if w.strip()]
		if words:
			concat = fn.Concat(
				fn.Coalesce(Item.name, ""),
				" ",
				fn.Coalesce(Item.item_name, ""),
				" ",
				fn.Coalesce(Item.description, ""),
			)
			cond = None
			for w in words:
				wcond = concat.like(f"%{w}%")
				cond = wcond if cond is None else cond & wcond
			if cond is not None:
				query = query.where(cond)

		relevance = (
			qb.terms.Case()
			.when(fn.Lower(Item.item_name) == fn.Lower(search_term), 1000)
			.when(fn.Lower(Item.name) == fn.Lower(search_term), 900)
			.when(Item.item_name.like(f"{search_term}%"), 500)
			.when(Item.name.like(f"{search_term}%"), 400)
			.else_(100)
		)
		query = query.orderby(relevance, order=Order.desc).orderby(Item.item_name)
	else:
		query = query.orderby(Item.item_name.asc())

	query = query.limit(limit)
	items = query.run(as_dict=True)

	return _enrich_items(items, company, warehouse)


def _enrich_items(items, company, warehouse):
	"""Enrich item rows with stock, buying price list rate, and UI metadata."""
	if not items:
		return []

	qb = frappe.qb
	buying_price_list = _get_default_buying_price_list(company)

	stock_map = {}
	if warehouse:
		item_codes = [it["item_code"] for it in items]
		warehouses = [warehouse]
		if frappe.db.get_value("Warehouse", warehouse, "is_group"):
			children = frappe.db.get_descendants("Warehouse", warehouse) or []
			if children:
				warehouses = children

		Bin = DocType("Bin")
		rows = (
			qb.from_(Bin)
			.select(Bin.item_code, fn.Sum(Bin.actual_qty).as_("actual_qty"))
			.where(Bin.item_code.isin(item_codes))
			.where(Bin.warehouse.isin(warehouses))
			.groupby(Bin.item_code)
			.run(as_dict=True)
		)
		stock_map = {r["item_code"]: flt(r["actual_qty"]) for r in rows}

	for it in items:
		it["last_purchase_rate"] = flt(it.get("last_purchase_rate") or 0)
		it["actual_qty"] = stock_map.get(it["item_code"], 0.0)
		it["has_batch_no"] = cint(it.get("has_batch_no") or 0)
		it["has_serial_no"] = cint(it.get("has_serial_no") or 0)
		it["buying_price_list_rate"] = _get_buying_item_price(
			it["item_code"], buying_price_list
		)

	return items


def _get_buying_item_price(item_code, price_list):
	"""Get the buying price for an item from a price list."""
	if not price_list:
		return None
	price = frappe.db.get_value(
		"Item Price",
		{
			"item_code": item_code,
			"price_list": price_list,
			"buying": 1,
			"price_list_rate": [">", 0],
		},
		"price_list_rate",
		order_by="modified desc",
	)
	return flt(price) if price else None


@frappe.whitelist()
def create_quick_purchase_invoice(
	company,
	supplier,
	warehouse,
	items,
	posting_date=None,
	due_date=None,
	update_stock=0,
	update_purchase_price=0,
	price_list=None,
	submit=0,
	is_paid=0,
	mode_of_payment="Cash",
):
	"""Create a Purchase Invoice (draft or submitted).

	If update_purchase_price is checked, update each item's last_purchase_rate
	and create/update an Item Price in the selected/default buying price list.
	If submit is checked, the document is submitted immediately.
	"""
	_check_purchase_invoice_permission("create")
	_check_company_permission(company)

	if not supplier:
		frappe.throw(_("Supplier is required"))
	if not frappe.db.exists("Supplier", supplier):
		frappe.throw(_("Supplier {0} not found").format(supplier))
	if frappe.db.get_value("Supplier", supplier, "disabled"):
		frappe.throw(_("Supplier {0} is disabled").format(supplier))

	if not warehouse:
		frappe.throw(_("Warehouse is required"))
	if not frappe.db.exists("Warehouse", warehouse):
		frappe.throw(_("Warehouse {0} not found").format(warehouse))

	if isinstance(items, str):
		items = json.loads(items)

	if not items or not isinstance(items, (list, tuple)):
		frappe.throw(_("No items provided for purchase invoice"))

	posting_date = posting_date or nowdate()
	if not due_date:
		# Default due date: posting_date + 30 days for supplier credit
		try:
			due_date = add_days(posting_date, 30)
		except Exception:
			due_date = posting_date

	update_stock = cint(update_stock)
	update_purchase_price = cint(update_purchase_price)
	submit = cint(submit)
	is_paid = cint(is_paid)

	# Resolve buying price list when updating prices
	buying_price_list = None
	if update_purchase_price:
		buying_price_list = price_list or _get_default_buying_price_list(company)

	rows = []
	price_updates = []

	for idx, raw in enumerate(items, start=1):
		item_code = raw.get("item_code")
		qty = flt(raw.get("qty") or 0)
		rate = flt(raw.get("rate") or 0)

		if not item_code:
			frappe.throw(_("Row {0}: item_code is missing").format(idx))
		if not frappe.db.exists("Item", item_code):
			frappe.throw(_("Row {0}: Item {1} not found").format(idx, item_code))
		if qty <= 0:
			frappe.throw(_("Row {0}: Quantity must be greater than zero").format(idx))
		if rate <= 0:
			frappe.throw(_("Row {0}: Rate must be greater than zero").format(idx))

		stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")

		rows.append({
			"item_code": item_code,
			"qty": qty,
			"rate": rate,
			"uom": stock_uom,
			"warehouse": warehouse if update_stock else None,
			"conversion_factor": 1,
		})

		price_updates.append({
			"item_code": item_code,
			"rate": rate,
			"uom": stock_uom,
		})

	if not rows:
		frappe.throw(_("No valid rows to create purchase invoice"))

	cash_bank_account = None
	if is_paid:
		cash_bank_account = _get_cash_bank_account(company, mode_of_payment)

	doc = frappe.get_doc({
		"doctype": "Purchase Invoice",
		"company": company,
		"supplier": supplier,
		"posting_date": posting_date,
		# Without this ERPNext resets posting_date to today on validate.
		"set_posting_time": 1,
		"due_date": due_date,
		# Keep the invoice total exactly equal to the screen total (no rounding adjustment);
		# also required so a paid invoice can be paid in full.
		"disable_rounded_total": 1,
		"set_warehouse": warehouse if update_stock else None,
		"update_stock": update_stock,
		"is_paid": is_paid,
		"mode_of_payment": mode_of_payment if is_paid else None,
		"cash_bank_account": cash_bank_account,
		"items": rows,
	})

	doc.insert()

	if is_paid and doc.grand_total:
		payable = doc.rounded_total if not cint(doc.disable_rounded_total) and doc.rounded_total else doc.grand_total
		doc.paid_amount = payable
		doc.base_paid_amount = flt(payable * flt(doc.conversion_rate or 1), doc.precision("base_paid_amount"))
		doc.save()

	if submit:
		# Check submit permission explicitly before finalizing
		if not frappe.has_permission("Purchase Invoice", "submit", doc=doc):
			frappe.throw(
				_("You do not have {0} permission on Purchase Invoice").format(_("submit")),
				frappe.PermissionError,
			)
		doc.submit()

	price_list_updated = None
	if update_purchase_price:
		if not buying_price_list:
			frappe.msgprint(
				_("لم يتم تحديث أسعار الشراء: لا توجد قائمة أسعار شراء افتراضية في إعدادات الشراء"),
				indicator="orange",
				alert=True,
			)
		else:
			_update_purchase_prices(price_updates, buying_price_list, company)
			price_list_updated = buying_price_list

	return {
		"name": doc.name,
		"docstatus": doc.docstatus,
		"url": f"/app/purchase-invoice/{doc.name}",
		"grand_total": doc.grand_total,
		"outstanding_amount": doc.outstanding_amount,
		"price_list_updated": price_list_updated,
	}


@frappe.whitelist()
def get_supplier_purchased_items(supplier, company, warehouse=None, limit=300):
	"""Items previously bought from a supplier (submitted, non-return invoices).

	Each row carries the last purchase date/rate from this supplier, how many invoices
	included it and the total quantity, plus the usual stock enrichment.
	"""
	if not frappe.has_permission("Purchase Invoice", "read"):
		frappe.throw(_("You do not have {0} permission on Purchase Invoice").format(_("read")), frappe.PermissionError)
	_check_company_permission(company)
	if not supplier:
		frappe.throw(_("Supplier is required"))

	history = frappe.db.sql(
		"""
		select pii.item_code,
			max(pi.posting_date) as last_date,
			count(distinct pi.name) as invoice_count,
			sum(pii.stock_qty) as total_qty
		from `tabPurchase Invoice Item` pii
		join `tabPurchase Invoice` pi on pi.name = pii.parent
		where pi.docstatus = 1 and pi.is_return = 0
			and pi.supplier = %(supplier)s and pi.company = %(company)s
		group by pii.item_code
		order by last_date desc
		limit %(limit)s
		""",
		{"supplier": supplier, "company": company, "limit": cint(limit) or 300},
		as_dict=True,
	)
	if not history:
		return []

	codes = [h.item_code for h in history]
	# Latest rate per item (per stock unit) from this supplier
	last_rates = {}
	for row in frappe.db.sql(
		"""
		select pii.item_code, pii.stock_uom_rate, pii.rate, pii.conversion_factor
		from `tabPurchase Invoice Item` pii
		join `tabPurchase Invoice` pi on pi.name = pii.parent
		where pi.docstatus = 1 and pi.is_return = 0
			and pi.supplier = %(supplier)s and pi.company = %(company)s
			and pii.item_code in %(codes)s
		order by pi.posting_date desc, pi.creation desc, pii.idx asc
		""",
		{"supplier": supplier, "company": company, "codes": codes},
		as_dict=True,
	):
		if row.item_code not in last_rates:
			rate = flt(row.stock_uom_rate) or flt(row.rate) / (flt(row.conversion_factor) or 1)
			last_rates[row.item_code] = flt(rate, 4)

	items = frappe.get_all(
		"Item",
		filters={"name": ["in", codes], "disabled": 0},
		fields=[
			"name as item_code", "item_name", "stock_uom", "image",
			"last_purchase_rate", "has_batch_no", "has_serial_no",
		],
	)
	by_code = {it["item_code"]: it for it in _enrich_items(items, company, warehouse)}

	result = []
	for h in history:  # keep "most recently bought first"
		it = by_code.get(h.item_code)
		if not it:
			continue  # disabled / deleted item
		it.update({
			"last_supplier_date": h.last_date,
			"last_supplier_rate": last_rates.get(h.item_code, 0),
			"invoice_count": cint(h.invoice_count),
			"total_qty": flt(h.total_qty),
		})
		result.append(it)
	return result


# =============================================================================
# Quick "new item" from the purchase invoice screen
# =============================================================================

def _suggest_item_code():
	"""Next numeric item code (codes on this site are plain numbers)."""
	row = frappe.db.sql("select max(cast(name as unsigned)) from `tabItem` where name regexp '^[0-9]+$'")
	return str(cint(row[0][0] if row else 0) + 1)


@frappe.whitelist()
def get_new_item_options(company=None):
	if not frappe.has_permission("Item", "create"):
		frappe.throw(_("ليس لديك صلاحية إنشاء أصناف"), frappe.PermissionError)
	stock = frappe.get_cached_doc("Stock Settings")
	return {
		"item_groups": frappe.get_all("Item Group", filters={"is_group": 0}, pluck="name", order_by="name"),
		"uoms": frappe.get_all("UOM", filters={"enabled": 1}, pluck="name", order_by="name"),
		"default_item_group": stock.item_group,
		"default_uom": stock.stock_uom or "Nos",
		"suggested_code": _suggest_item_code(),
		"buying_price_list": _get_default_buying_price_list(company) if company else None,
		"selling_price_list": frappe.db.get_single_value("Selling Settings", "selling_price_list"),
	}


def _upsert_item_price(item_code, price_list, rate, uom, buying=False, company=None):
	if not price_list or flt(rate) <= 0:
		return
	filters = {"item_code": item_code, "price_list": price_list, "buying" if buying else "selling": 1}
	existing = frappe.db.get_value("Item Price", filters, "name")
	if existing:
		frappe.db.set_value("Item Price", existing, "price_list_rate", flt(rate))
		return
	frappe.get_doc({
		"doctype": "Item Price",
		"item_code": item_code,
		"price_list": price_list,
		"buying": 1 if buying else 0,
		"selling": 0 if buying else 1,
		"price_list_rate": flt(rate),
		"uom": uom,
		"currency": frappe.db.get_value("Price List", price_list, "currency")
		or (company and frappe.db.get_value("Company", company, "default_currency")),
	}).insert(ignore_permissions=True)


@frappe.whitelist()
def create_quick_item(data, company, warehouse=None):
	"""Create a stock item and return it shaped like a search result (ready for the cart)."""
	if not frappe.has_permission("Item", "create"):
		frappe.throw(_("ليس لديك صلاحية إنشاء أصناف"), frappe.PermissionError)
	_check_company_permission(company)
	data = json.loads(data) if isinstance(data, str) else (data or {})

	item_name = (data.get("item_name") or "").strip()
	item_code = (data.get("item_code") or "").strip()
	item_group = data.get("item_group")
	stock_uom = data.get("stock_uom")
	barcode = (data.get("barcode") or "").strip()

	if not item_name:
		frappe.throw(_("اسم الصنف مطلوب"))
	if len(item_name) > 140:
		frappe.throw(_("اسم الصنف طويل جداً (الحد 140 حرفاً)"))
	if not item_group or not frappe.db.exists("Item Group", item_group):
		frappe.throw(_("يرجى اختيار مجموعة الصنف"))
	if not stock_uom or not frappe.db.exists("UOM", stock_uom):
		frappe.throw(_("يرجى اختيار الوحدة"))

	same_name = frappe.db.get_value("Item", {"item_name": item_name, "disabled": 0}, "name")
	if same_name:
		frappe.throw(_("يوجد صنف بنفس الاسم: {0} ({1})").format(item_name, same_name))
	if item_code:
		if frappe.db.exists("Item", item_code):
			frappe.throw(_("الكود {0} مستخدم لصنف آخر").format(item_code))
	else:
		item_code = _suggest_item_code()
	if barcode:
		used_by = frappe.db.get_value("Item Barcode", {"barcode": barcode}, "parent")
		if used_by:
			frappe.throw(_("الباركود {0} مستخدم للصنف {1}").format(barcode, used_by))

	item = frappe.get_doc({
		"doctype": "Item",
		"item_code": item_code,
		"item_name": item_name,
		"description": item_name,
		"item_group": item_group,
		"stock_uom": stock_uom,
		"is_stock_item": 1,
		"include_item_in_manufacturing": 0,
		"item_defaults": [{"company": company, "default_warehouse": warehouse}] if warehouse else [{"company": company}],
		"barcodes": [{"barcode": barcode}] if barcode else [],
	})
	if frappe.get_meta("Item").has_field("custom_company"):
		item.custom_company = company
	item.insert()

	_upsert_item_price(item.name, _get_default_buying_price_list(company), data.get("buying_rate"), stock_uom, True, company)
	_upsert_item_price(item.name, frappe.db.get_single_value("Selling Settings", "selling_price_list"),
		data.get("selling_rate"), stock_uom, False, company)

	rows = [{
		"item_code": item.name, "item_name": item.item_name, "stock_uom": item.stock_uom,
		"image": item.image, "last_purchase_rate": 0, "has_batch_no": 0, "has_serial_no": 0,
	}]
	return _enrich_items(rows, company, warehouse)[0]


@frappe.whitelist()
def get_modes_of_payment():
	"""List enabled modes of payment suitable for purchase invoice payments."""
	return frappe.db.get_all(
		"Mode of Payment",
		filters={"enabled": 1},
		fields=["name", "type"],
		order_by="name",
	) or []


def _get_cash_bank_account(company, mode_of_payment="Cash"):
	"""Resolve the cash/bank account for a paid purchase invoice."""
	if not mode_of_payment or not frappe.db.exists("Mode of Payment", mode_of_payment):
		frappe.throw(_("Mode of Payment {0} not found").format(mode_of_payment))

	# 1) Mode of Payment Account for this company
	account = frappe.db.get_value(
		"Mode of Payment Account",
		{"parent": mode_of_payment, "company": company},
		"default_account",
	)
	if account and frappe.db.exists("Account", account):
		return account

	# 2) Company default cash account
	account = frappe.db.get_value("Company", company, "default_cash_account")
	if account and frappe.db.exists("Account", account):
		return account

	frappe.throw(
		_(
			"لم يُعثر على حساب نقدي/بنكي للشركة {0} وطريقة الدفع {1}. "
			"يرجى ضبطها في Mode of Payment أو في Company."
		).format(company, mode_of_payment)
	)


def _get_default_buying_price_list(company):
	"""Resolve the default buying price list for updating item prices."""
	buying_pl = frappe.db.get_single_value("Buying Settings", "buying_price_list")
	if buying_pl and frappe.db.exists("Price List", buying_pl):
		is_buying, enabled = frappe.db.get_value("Price List", buying_pl, ["buying", "enabled"])
		if cint(is_buying) and cint(enabled):
			return buying_pl
	return None


def _update_purchase_prices(price_updates, buying_price_list, company):
	"""Create/update the Item Price in the default buying price list.

	Item.last_purchase_rate is left to ERPNext: it is set when the invoice is submitted
	(and correctly ignores back-dated invoices), so a draft never changes it.
	"""
	for update in price_updates:
		item_code = update["item_code"]
		rate = update["rate"]

		if buying_price_list:
			existing = frappe.db.get_value(
				"Item Price",
				{
					"item_code": item_code,
					"price_list": buying_price_list,
					"buying": 1,
					"uom": ["in", [update.get("uom") or "", ""]],
				},
				"name",
			) or frappe.db.get_value(
				"Item Price",
				{"item_code": item_code, "price_list": buying_price_list, "buying": 1},
				"name",
			)
			if existing:
				frappe.db.set_value("Item Price", existing, "price_list_rate", rate)
			else:
				ip = frappe.get_doc({
					"doctype": "Item Price",
					"item_code": item_code,
					"price_list": buying_price_list,
					"buying": 1,
					"price_list_rate": rate,
					"uom": update.get("uom"),
					"currency": frappe.db.get_value("Price List", buying_price_list, "currency")
					or frappe.db.get_value("Company", company, "default_currency"),
				})
				ip.insert(ignore_permissions=True)
