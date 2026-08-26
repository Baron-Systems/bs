# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Quick Inventory (Opening Stock) API.

Creates a Stock Reconciliation document with purpose="Opening Stock" as a
draft (docstatus=0).

Valuation rate rule (determined by the backend):
1. Item.last_purchase_rate > 0  -> use it (source = "last_purchase_rate")
2. Item Price in the approved buying price list > 0 -> use it (source = "buying_price_list")
3. Otherwise -> frappe.throw a clear message and abort
"""

from __future__ import unicode_literals

import json

import frappe
from frappe import _
from frappe.query_builder import DocType, functions as fn
from frappe.utils import cint, flt, nowdate
from pypika import Order


# =============================================================================
# Permission helpers
# =============================================================================

def _check_reconciliation_permission(action="create"):
	if not frappe.has_permission("Stock Reconciliation", action):
		frappe.throw(
			_("You do not have {0} permission on Stock Reconciliation").format(_(action)),
			frappe.PermissionError,
		)


def _check_company_permission(company):
	if company and not frappe.has_permission("Company", "read", doc=company):
		frappe.throw(
			_("You do not have permission to access Company {0}").format(company),
			frappe.PermissionError,
		)


# =============================================================================
# Valuation rate computation
# =============================================================================

def get_approved_buying_price_list(company=None):
	"""Resolve the approved buying price list for inventory valuation."""
	# 1) Stock Settings custom field
	custom_pl = frappe.db.get_value(
		"Stock Settings", "Stock Settings", "pos_abs_inventory_buying_price_list"
	)
	if custom_pl and frappe.db.exists("Price List", custom_pl):
		is_buying, enabled = frappe.db.get_value("Price List", custom_pl, ["buying", "enabled"])
		if cint(is_buying) and cint(enabled):
			return custom_pl

	# 2) Buying Settings global default
	buying_pl = frappe.db.get_single_value("Buying Settings", "buying_price_list")
	if buying_pl and frappe.db.exists("Price List", buying_pl):
		is_buying, enabled = frappe.db.get_value("Price List", buying_pl, ["buying", "enabled"])
		if cint(is_buying) and cint(enabled):
			return buying_pl

	# 3) Nothing configured
	frappe.throw(
		_(
			"لم يتم ضبط قائمة أسعار شراء معتمدة. يرجى ضبطها في "
			"Stock Settings أو في Buying Settings."
		)
	)


def get_buying_item_price(item_code, company=None, price_list=None):
	"""Get the buying price for an item from a price list."""
	if not price_list:
		price_list = get_approved_buying_price_list(company)

	price = frappe.db.get_value(
		"Item Price",
		{
			"item_code": item_code,
			"price_list": price_list,
			"price_list_rate": [">", 0],
		},
		"price_list_rate",
		order_by="modified desc",
	)

	return flt(price) if price else None


def compute_valuation_rate(item_code, company=None, fallback_price_list=None):
	"""Compute the valuation rate for an item per the approved rule."""
	last_purchase_rate = flt(
		frappe.db.get_value("Item", item_code, "last_purchase_rate") or 0
	)

	if last_purchase_rate > 0:
		return {"rate": last_purchase_rate, "source": "last_purchase_rate"}

	try:
		buying_price = get_buying_item_price(item_code, company)
	except frappe.ValidationError:
		buying_price = None

	if buying_price and buying_price > 0:
		return {"rate": buying_price, "source": "buying_price_list"}

	if fallback_price_list:
		fb_price = get_buying_item_price(item_code, company, price_list=fallback_price_list)
		if fb_price and fb_price > 0:
			return {"rate": fb_price, "source": "fallback_price_list"}

	return {"rate": None, "source": None}


# =============================================================================
# Whitelisted endpoints
# =============================================================================

@frappe.whitelist()
def get_price_lists():
	"""List enabled price lists for the fallback selector."""
	rows = frappe.db.get_all(
		"Price List",
		filters={"enabled": 1},
		fields=["name", "buying", "selling", "currency"],
		order_by="name",
	)
	return rows


@frappe.whitelist()
def get_warehouses(company=None):
	"""List non-group warehouses for a company (or all if no company given)."""
	filters = {"is_group": 0, "disabled": 0}
	if company:
		filters["company"] = company
		_check_company_permission(company)

	rows = frappe.db.get_all(
		"Warehouse",
		filters=filters,
		fields=["name", "warehouse_name"],
		order_by="name",
	)
	return rows


@frappe.whitelist()
def search_items_for_reconciliation(search_term, company, warehouse=None, limit=20, price_list=None):
	"""Search stock items for the Quick Inventory page."""
	if not company:
		frappe.throw(_("Company is required"))

	_check_company_permission(company)

	search_term = (search_term or "").strip()
	limit = cint(limit) or 20

	Item = DocType("Item")
	qb = frappe.qb

	# Barcode exact match
	if search_term:
		barcode_parent = frappe.db.get_value(
			"Item Barcode", {"barcode": search_term}, "parent"
		)
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
					return _enrich_items(items, company, warehouse, price_list)

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

	return _enrich_items(items, company, warehouse, price_list)


def _enrich_items(items, company, warehouse, fallback_price_list=None):
	"""Enrich item rows with stock, valuation rate, and UI metadata."""
	if not items:
		return []

	qb = frappe.qb

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

		vr = compute_valuation_rate(it["item_code"], company, fallback_price_list)
		it["valuation_rate"] = vr["rate"]
		it["valuation_rate_source"] = vr["source"]
		it["has_price"] = bool(vr["rate"] and vr["rate"] > 0)

	return items


@frappe.whitelist()
def create_opening_stock_reconciliation(company, warehouse, posting_date, items, price_list=None):
	"""Create a Stock Reconciliation (Opening Stock) as a draft."""
	_check_reconciliation_permission("create")
	_check_company_permission(company)

	if not warehouse:
		frappe.throw(_("Warehouse is required"))
	if not frappe.db.exists("Warehouse", warehouse):
		frappe.throw(_("Warehouse {0} not found").format(warehouse))
	if not posting_date:
		posting_date = nowdate()

	if isinstance(items, str):
		items = json.loads(items)

	if not items or not isinstance(items, (list, tuple)):
		frappe.throw(_("No items provided for reconciliation"))

	rows = []
	for idx, raw in enumerate(items, start=1):
		item_code = raw.get("item_code")
		qty = flt(raw.get("qty") or 0)
		client_rate = flt(raw.get("valuation_rate") or 0)

		if not item_code:
			frappe.throw(_("Row {0}: item_code is missing").format(idx))
		if not frappe.db.exists("Item", item_code):
			frappe.throw(_("Row {0}: Item {1} not found").format(idx, item_code))
		if qty <= 0:
			frappe.throw(
				_("Row {0}: Quantity must be greater than zero for item {1}").format(idx, item_code)
			)

		if client_rate > 0:
			rate = client_rate
		else:
			vr = compute_valuation_rate(item_code, company, price_list)
			rate = vr["rate"]

		if not rate or rate <= 0:
			frappe.throw(
				_("لا يوجد آخر سعر شراء أو سعر شراء في قائمة الأسعار للصنف {0}").format(item_code)
			)

		stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")

		rows.append({
			"item_code": item_code,
			"warehouse": warehouse,
			"qty": qty,
			"stock_uom": stock_uom,
			"valuation_rate": rate,
		})

	if not rows:
		frappe.throw(_("No valid rows to reconcile"))

	from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_difference_account

	expense_account = get_difference_account("Opening Stock", company)
	cost_center = frappe.get_cached_value("Company", company, "cost_center")

	doc = frappe.get_doc({
		"doctype": "Stock Reconciliation",
		"purpose": "Opening Stock",
		"company": company,
		"set_warehouse": warehouse,
		"posting_date": posting_date,
		"expense_account": expense_account,
		"cost_center": cost_center,
		"items": rows,
	})

	doc.insert()

	return {
		"name": doc.name,
		"docstatus": doc.docstatus,
		"url": f"/app/stock-reconciliation/{doc.name}",
	}
