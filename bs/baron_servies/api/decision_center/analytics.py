# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Analytics API for the Decision Center page (charts only).

Accounting figures (sales, cost, expenses, profit) come from the General
Ledger so they reconcile with the Profit and Loss Statement. Opening entries
and opening invoices are always excluded from period figures.
"""

from __future__ import unicode_literals

import datetime

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, add_days, nowdate, date_diff

from .api import _resolve_period, _get_currency
from . import config as cfg


MAX_DAILY_DAYS = 62
WEEKDAYS = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]

# Expense accounts that belong to cost of sales (not operating expenses)
COST_OF_SALES_TYPES = ("Cost of Goods Sold", "Stock Adjustment")


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _context(company, period, from_date, to_date):
	if not company:
		company = frappe.db.get_single_value("Global Defaults", "default_company")
	if not company:
		frappe.throw(_("Company is required"))
	fd, td, pf, pt = _resolve_period(period, from_date, to_date)
	gran = "daily" if date_diff(td, fd) + 1 <= MAX_DAILY_DAYS else "monthly"
	return frappe._dict(
		company=company, fd=getdate(fd), td=getdate(td), pf=getdate(pf), pt=getdate(pt),
		gran=gran, currency=_get_currency(company),
	)


def _params(ctx, prev=False, **extra):
	p = {
		"company": ctx.company,
		"from_date": ctx.pf if prev else ctx.fd,
		"to_date": ctx.pt if prev else ctx.td,
	}
	p.update(extra)
	return p


def _bucket_expr(ctx, column):
	fmt = "%%Y-%%m-%%d" if ctx.gran == "daily" else "%%Y-%%m"
	return "DATE_FORMAT({0}, '{1}')".format(column, fmt)


def _buckets(ctx):
	"""Ordered list of (key, label) covering the period."""
	out = []
	if ctx.gran == "daily":
		d = ctx.fd
		while d <= ctx.td:
			out.append((d.strftime("%Y-%m-%d"), d.strftime("%d/%m")))
			d = add_days(d, 1)
	else:
		d = ctx.fd.replace(day=1)
		while d <= ctx.td:
			out.append((d.strftime("%Y-%m"), d.strftime("%Y-%m")))
			d = (d.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
	return out


def _fill(ctx, rows, fields):
	"""Map SQL rows keyed by ``bucket`` onto the full bucket list."""
	by_key = {r["bucket"]: r for r in rows}
	result = []
	for key, label in _buckets(ctx):
		r = by_key.get(key, {})
		entry = {"key": key, "label": label}
		for f in fields:
			entry[f] = flt(r.get(f), 2)
		result.append(entry)
	return result


def _pct(old, new):
	old, new = flt(old), flt(new)
	# Too small a base makes the percentage meaningless
	if abs(old) < 1:
		return None
	return flt((new - old) / abs(old) * 100, 1)


def _pl_totals(ctx, prev=False):
	"""Income / cost of sales / operating expenses from the GL."""
	row = frappe.db.sql("""
		SELECT
			COALESCE(SUM(CASE WHEN acc.root_type = 'Income'
				AND IFNULL(acc.account_type, '') != 'Indirect Income'
				THEN gle.credit - gle.debit END), 0) AS sales,
			COALESCE(SUM(CASE WHEN acc.root_type = 'Income'
				AND acc.account_type = 'Indirect Income'
				THEN gle.credit - gle.debit END), 0) AS other_income,
			COALESCE(SUM(CASE WHEN acc.root_type = 'Expense'
				AND acc.account_type IN %(cos)s
				THEN gle.debit - gle.credit END), 0) AS cost_of_sales,
			COALESCE(SUM(CASE WHEN acc.root_type = 'Expense'
				AND IFNULL(acc.account_type, '') NOT IN %(cos)s
				THEN gle.debit - gle.credit END), 0) AS expenses
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.is_opening = 'No'
		AND gle.voucher_type != 'Period Closing Voucher'
		AND acc.root_type IN ('Income', 'Expense')
		AND gle.company = %(company)s
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", _params(ctx, prev, cos=COST_OF_SALES_TYPES), as_dict=True)[0]

	sales = flt(row.sales, 2)
	cost = flt(row.cost_of_sales, 2)
	expenses = flt(row.expenses, 2)
	other = flt(row.other_income, 2)
	gross = flt(sales - cost, 2)
	return {
		"sales": sales,
		"cost_of_sales": cost,
		"gross_profit": gross,
		"other_income": other,
		"expenses": expenses,
		"net_profit": flt(gross + other - expenses, 2),
	}


def _invoice_stats(ctx, prev=False):
	row = frappe.db.sql("""
		SELECT
			SUM(CASE WHEN is_return = 0 THEN 1 ELSE 0 END) AS invoices,
			COALESCE(SUM(CASE WHEN is_return = 1 THEN -base_net_total END), 0) AS returns,
			COUNT(DISTINCT CASE WHEN is_return = 0 THEN customer END) AS customers
		FROM `tabSales Invoice`
		WHERE docstatus = 1 AND is_opening = 'No'
		AND company = %(company)s
		AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", _params(ctx, prev), as_dict=True)[0]
	return {
		"invoices": cint(row.invoices),
		"returns": flt(row.returns, 2),
		"customers": cint(row.customers),
	}


def _purchase_total(ctx, prev=False):
	return flt(frappe.db.sql("""
		SELECT COALESCE(SUM(base_grand_total), 0)
		FROM `tabPurchase Invoice`
		WHERE docstatus = 1 AND is_opening = 'No'
		AND company = %(company)s
		AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", _params(ctx, prev))[0][0], 2)


def _meta(ctx):
	return {
		"currency": ctx.currency,
		"granularity": ctx.gran,
		"period": {"from_date": str(ctx.fd), "to_date": str(ctx.td),
				   "prev_from": str(ctx.pf), "prev_to": str(ctx.pt)},
	}


def _changes(current, previous, key, name_key, value_key, limit=8):
	"""Top growers and decliners by absolute amount change."""
	keys = set(current) | set(previous)
	rows = []
	for k in keys:
		cur = current.get(k, {})
		prev = previous.get(k, {})
		c, p = flt(cur.get(value_key)), flt(prev.get(value_key))
		if c == p:
			continue
		rows.append({
			key: k,
			"name": cur.get(name_key) or prev.get(name_key) or k,
			"current": flt(c, 2),
			"previous": flt(p, 2),
			"change": flt(c - p, 2),
		})
	rows.sort(key=lambda r: r["change"], reverse=True)
	growing = [r for r in rows if r["change"] > 0][:limit]
	declining = sorted([r for r in rows if r["change"] < 0], key=lambda r: r["change"])[:limit]
	return growing, declining


# ═══════════════════════════════════════════════════════════════════════════
# Overview
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_overview_analytics(company=None, period=None, from_date=None, to_date=None):
	ctx = _context(company, period, from_date, to_date)

	cur = _pl_totals(ctx)
	prev = _pl_totals(ctx, prev=True)
	inv = _invoice_stats(ctx)
	purchases = _purchase_total(ctx)
	prev_purchases = _purchase_total(ctx, prev=True)

	rows = frappe.db.sql("""
		SELECT
			{bucket} AS bucket,
			COALESCE(SUM(CASE WHEN acc.root_type = 'Income'
				AND IFNULL(acc.account_type, '') != 'Indirect Income'
				THEN gle.credit - gle.debit END), 0) AS sales,
			COALESCE(SUM(CASE WHEN acc.root_type = 'Expense'
				AND acc.account_type IN %(cos)s
				THEN gle.debit - gle.credit END), 0) AS cost_of_sales,
			COALESCE(SUM(CASE WHEN acc.root_type = 'Expense'
				AND IFNULL(acc.account_type, '') NOT IN %(cos)s
				THEN gle.debit - gle.credit END), 0) AS expenses,
			COALESCE(SUM(gle.credit - gle.debit), 0) AS net_profit
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.is_opening = 'No'
		AND gle.voucher_type != 'Period Closing Voucher'
		AND acc.root_type IN ('Income', 'Expense')
		AND gle.company = %(company)s
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY bucket
	""".format(bucket=_bucket_expr(ctx, "gle.posting_date")),
		_params(ctx, cos=COST_OF_SALES_TYPES), as_dict=True)

	trend = _fill(ctx, rows, ["sales", "cost_of_sales", "expenses", "net_profit"])
	for t in trend:
		t["gross_profit"] = flt(t["sales"] - t["cost_of_sales"], 2)

	sales = cur["sales"]
	return dict(_meta(ctx), **{
		"kpis": {
			"sales": sales,
			"sales_change_pct": _pct(prev["sales"], sales),
			"gross_profit": cur["gross_profit"],
			"gross_margin_pct": flt(cur["gross_profit"] / sales * 100, 1) if sales else None,
			"gross_profit_change_pct": _pct(prev["gross_profit"], cur["gross_profit"]),
			"net_profit": cur["net_profit"],
			"net_profit_change_pct": _pct(prev["net_profit"], cur["net_profit"]),
			"expenses": cur["expenses"],
			"expenses_change_pct": _pct(prev["expenses"], cur["expenses"]),
			"purchases": purchases,
			"purchases_change_pct": _pct(prev_purchases, purchases),
			"invoices": inv["invoices"],
			"avg_invoice": flt(sales / inv["invoices"], 2) if inv["invoices"] else 0,
			"customers": inv["customers"],
		},
		"trend": trend,
		"comparison": [
			{"label": "المبيعات", "current": sales, "previous": prev["sales"]},
			{"label": "مجمل الربح", "current": cur["gross_profit"], "previous": prev["gross_profit"]},
			{"label": "المصاريف", "current": cur["expenses"], "previous": prev["expenses"]},
			{"label": "صافي الربح", "current": cur["net_profit"], "previous": prev["net_profit"]},
			{"label": "المشتريات", "current": purchases, "previous": prev_purchases},
		],
		"sales_breakdown": [
			{"label": "تكلفة المبيعات", "value": max(cur["cost_of_sales"], 0)},
			{"label": "المصاريف", "value": max(cur["expenses"], 0)},
			{"label": "صافي الربح", "value": max(cur["net_profit"], 0)},
		],
	})


# ═══════════════════════════════════════════════════════════════════════════
# Sales
# ═══════════════════════════════════════════════════════════════════════════

def _item_sales(ctx, prev=False):
	rows = frappe.db.sql("""
		SELECT sii.item_code, sii.item_name,
			SUM(sii.qty) AS qty, SUM(sii.base_net_amount) AS amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1 AND si.is_opening = 'No'
		AND si.company = %(company)s
		AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY sii.item_code
	""", _params(ctx, prev), as_dict=True)
	return {r.item_code: r for r in rows}


@frappe.whitelist()
def get_sales_analytics(company=None, period=None, from_date=None, to_date=None):
	ctx = _context(company, period, from_date, to_date)
	si_where = """si.docstatus = 1 AND si.is_opening = 'No'
		AND si.company = %(company)s
		AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s"""

	pl = _pl_totals(ctx)
	prev_pl = _pl_totals(ctx, prev=True)
	inv = _invoice_stats(ctx)

	trend_rows = frappe.db.sql("""
		SELECT {bucket} AS bucket,
			COALESCE(SUM(si.base_net_total), 0) AS amount,
			SUM(CASE WHEN si.is_return = 0 THEN 1 ELSE 0 END) AS invoices,
			COALESCE(SUM(CASE WHEN si.is_return = 1 THEN -si.base_net_total END), 0) AS returns
		FROM `tabSales Invoice` si
		WHERE {w}
		GROUP BY bucket
	""".format(bucket=_bucket_expr(ctx, "si.posting_date"), w=si_where), _params(ctx), as_dict=True)

	weekday_rows = frappe.db.sql("""
		SELECT DAYOFWEEK(si.posting_date) AS dow,
			COALESCE(SUM(si.base_net_total), 0) AS amount,
			SUM(CASE WHEN si.is_return = 0 THEN 1 ELSE 0 END) AS invoices
		FROM `tabSales Invoice` si
		WHERE {w}
		GROUP BY dow
	""".format(w=si_where), _params(ctx), as_dict=True)
	wd = {cint(r.dow): r for r in weekday_rows}
	by_weekday = [{"label": WEEKDAYS[i - 1], "amount": flt(wd.get(i, {}).get("amount"), 2),
				   "invoices": cint(wd.get(i, {}).get("invoices"))} for i in range(1, 8)]

	hour_rows = frappe.db.sql("""
		SELECT HOUR(si.posting_time) AS hr,
			COALESCE(SUM(si.base_net_total), 0) AS amount,
			SUM(CASE WHEN si.is_return = 0 THEN 1 ELSE 0 END) AS invoices
		FROM `tabSales Invoice` si
		WHERE {w}
		GROUP BY hr
	""".format(w=si_where), _params(ctx), as_dict=True)
	hr = {cint(r.hr): r for r in hour_rows if r.hr is not None}
	by_hour = [{"label": "%02d:00" % h, "amount": flt(hr.get(h, {}).get("amount"), 2),
				"invoices": cint(hr.get(h, {}).get("invoices"))} for h in range(24)]

	by_group = frappe.db.sql("""
		SELECT IFNULL(sii.item_group, 'غير محدد') AS label,
			COALESCE(SUM(sii.base_net_amount), 0) AS value
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE {w}
		GROUP BY label
		HAVING value > 0
		ORDER BY value DESC
	""".format(w=si_where), _params(ctx), as_dict=True)

	current_items = _item_sales(ctx)
	previous_items = _item_sales(ctx, prev=True)
	top_items = sorted(
		[{"name": r.item_name or k, "amount": flt(r.amount, 2), "qty": flt(r.qty, 2)}
		 for k, r in current_items.items() if flt(r.amount) > 0],
		key=lambda r: r["amount"], reverse=True)[:10]
	growing, declining = _changes(current_items, previous_items, "item_code", "item_name", "amount")

	return dict(_meta(ctx), **{
		"kpis": {
			"sales": pl["sales"],
			"sales_change_pct": _pct(prev_pl["sales"], pl["sales"]),
			"invoices": inv["invoices"],
			"avg_invoice": flt(pl["sales"] / inv["invoices"], 2) if inv["invoices"] else 0,
			"returns": inv["returns"],
			"returns_pct": flt(inv["returns"] / (pl["sales"] + inv["returns"]) * 100, 1)
				if (pl["sales"] + inv["returns"]) else None,
			"gross_margin_pct": flt(pl["gross_profit"] / pl["sales"] * 100, 1) if pl["sales"] else None,
		},
		"trend": _fill(ctx, trend_rows, ["amount", "invoices", "returns"]),
		"by_weekday": by_weekday,
		"by_hour": by_hour,
		"by_item_group": _top_n_with_other(by_group, 8),
		"top_items": top_items,
		"growing_items": growing,
		"declining_items": declining,
	})


def _top_n_with_other(rows, n):
	rows = [{"label": r["label"], "value": flt(r["value"], 2)} for r in rows]
	if len(rows) <= n:
		return rows
	head = rows[:n]
	head.append({"label": "أخرى", "value": flt(sum(r["value"] for r in rows[n:]), 2)})
	return head


# ═══════════════════════════════════════════════════════════════════════════
# Purchases
# ═══════════════════════════════════════════════════════════════════════════

def _item_purchase_rates(ctx, prev=False):
	rows = frappe.db.sql("""
		SELECT pii.item_code, pii.item_name,
			SUM(pii.stock_qty) AS qty, SUM(pii.base_net_amount) AS amount
		FROM `tabPurchase Invoice Item` pii
		INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
		WHERE pi.docstatus = 1 AND pi.is_opening = 'No' AND pi.is_return = 0
		AND pi.company = %(company)s
		AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY pii.item_code
	""", _params(ctx, prev), as_dict=True)
	return {r.item_code: r for r in rows}


@frappe.whitelist()
def get_purchase_analytics(company=None, period=None, from_date=None, to_date=None):
	ctx = _context(company, period, from_date, to_date)
	pi_where = """pi.docstatus = 1 AND pi.is_opening = 'No'
		AND pi.company = %(company)s
		AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s"""

	total = _purchase_total(ctx)
	prev_total = _purchase_total(ctx, prev=True)

	trend_rows = frappe.db.sql("""
		SELECT {bucket} AS bucket,
			COALESCE(SUM(pi.base_grand_total), 0) AS amount,
			SUM(CASE WHEN pi.is_return = 0 THEN 1 ELSE 0 END) AS invoices
		FROM `tabPurchase Invoice` pi
		WHERE {w}
		GROUP BY bucket
	""".format(bucket=_bucket_expr(ctx, "pi.posting_date"), w=pi_where), _params(ctx), as_dict=True)
	trend = _fill(ctx, trend_rows, ["amount", "invoices"])

	top_suppliers = frappe.db.sql("""
		SELECT IFNULL(pi.supplier_name, pi.supplier) AS name,
			COALESCE(SUM(pi.base_grand_total), 0) AS amount,
			SUM(CASE WHEN pi.is_return = 0 THEN 1 ELSE 0 END) AS invoices
		FROM `tabPurchase Invoice` pi
		WHERE {w}
		GROUP BY pi.supplier
		HAVING amount > 0
		ORDER BY amount DESC
		LIMIT 10
	""".format(w=pi_where), _params(ctx), as_dict=True)

	top_items = frappe.db.sql("""
		SELECT pii.item_name AS name,
			COALESCE(SUM(pii.base_net_amount), 0) AS amount,
			SUM(pii.qty) AS qty
		FROM `tabPurchase Invoice Item` pii
		INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
		WHERE {w}
		GROUP BY pii.item_code
		HAVING amount > 0
		ORDER BY amount DESC
		LIMIT 10
	""".format(w=pi_where), _params(ctx), as_dict=True)

	by_group = frappe.db.sql("""
		SELECT IFNULL(pii.item_group, 'غير محدد') AS label,
			COALESCE(SUM(pii.base_net_amount), 0) AS value
		FROM `tabPurchase Invoice Item` pii
		INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
		WHERE {w}
		GROUP BY label
		HAVING value > 0
		ORDER BY value DESC
	""".format(w=pi_where), _params(ctx), as_dict=True)

	cur_rates = _item_purchase_rates(ctx)
	prev_rates = _item_purchase_rates(ctx, prev=True)
	price_changes = []
	for code, c in cur_rates.items():
		p = prev_rates.get(code)
		if not p or flt(c.qty) <= 0 or flt(p.qty) <= 0:
			continue
		cr, pr = flt(c.amount) / flt(c.qty), flt(p.amount) / flt(p.qty)
		if pr <= 0 or abs(cr - pr) < 0.005:
			continue
		price_changes.append({"name": c.item_name or code, "previous_rate": flt(pr, 2),
							  "current_rate": flt(cr, 2), "change_pct": flt((cr - pr) / pr * 100, 1)})
	price_changes.sort(key=lambda r: abs(r["change_pct"]), reverse=True)

	return dict(_meta(ctx), **{
		"kpis": {
			"purchases": total,
			"purchases_change_pct": _pct(prev_total, total),
			"invoices": cint(sum(t["invoices"] for t in trend)),
			"suppliers": len(top_suppliers),
			"avg_invoice": flt(total / sum(t["invoices"] for t in trend), 2)
				if sum(t["invoices"] for t in trend) else 0,
		},
		"trend": trend,
		"top_suppliers": [dict(r, amount=flt(r.amount, 2)) for r in top_suppliers],
		"top_items": [dict(r, amount=flt(r.amount, 2)) for r in top_items],
		"by_item_group": _top_n_with_other(by_group, 8),
		"price_changes": price_changes[:10],
	})


# ═══════════════════════════════════════════════════════════════════════════
# Inventory
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_inventory_analytics(company=None, period=None, from_date=None, to_date=None):
	ctx = _context(company, period, from_date, to_date)

	items = frappe.db.sql("""
		SELECT b.item_code, i.item_name, IFNULL(i.item_group, 'غير محدد') AS item_group,
			SUM(b.actual_qty) AS qty, SUM(b.stock_value) AS value
		FROM `tabBin` b
		INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
		INNER JOIN `tabItem` i ON i.name = b.item_code
		WHERE w.company = %(company)s AND i.is_stock_item = 1 AND i.disabled = 0
		GROUP BY b.item_code
		HAVING qty > 0
	""", {"company": ctx.company}, as_dict=True)

	# Sales velocity over the last 90 days (stock qty)
	today = getdate(nowdate())
	lookback_days = 90
	velocity = {r.item_code: flt(r.qty) / lookback_days for r in frappe.db.sql("""
		SELECT sii.item_code, SUM(sii.stock_qty) AS qty
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1 AND si.is_opening = 'No' AND si.company = %(company)s
		AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY sii.item_code
	""", {"company": ctx.company, "from_date": add_days(today, -(lookback_days - 1)), "to_date": today},
		as_dict=True)}

	slow_days = cint(cfg.get_threshold("SLOW_MOVING_DAYS")) or 90
	low_days = cint(cfg.get_threshold("WARNING_STOCK_DAYS")) or 14

	classes = {
		"dead": {"label": "راكد (بدون مبيعات 90 يوم)", "count": 0, "value": 0},
		"slow": {"label": "بطيء الحركة", "count": 0, "value": 0},
		"low": {"label": "قريب من النفاد", "count": 0, "value": 0},
		"normal": {"label": "طبيعي", "count": 0, "value": 0},
	}
	groups = {}
	total_value = 0
	for it in items:
		value = flt(it.value)
		total_value += value
		groups[it.item_group] = groups.get(it.item_group, 0) + value
		v = velocity.get(it.item_code, 0)
		if v <= 0:
			key = "dead"
		else:
			days = flt(it.qty) / v
			key = "slow" if days > slow_days else ("low" if days < low_days else "normal")
		classes[key]["count"] += 1
		classes[key]["value"] += value

	by_group = sorted([{"label": k, "value": v} for k, v in groups.items() if v > 0],
					  key=lambda r: r["value"], reverse=True)
	top_items = sorted([{"name": it.item_name or it.item_code, "value": flt(it.value, 2), "qty": flt(it.qty, 2)}
						for it in items], key=lambda r: r["value"], reverse=True)[:10]

	movement_rows = frappe.db.sql("""
		SELECT {bucket} AS bucket,
			COALESCE(SUM(CASE WHEN sle.stock_value_difference > 0 THEN sle.stock_value_difference END), 0) AS incoming,
			COALESCE(SUM(CASE WHEN sle.stock_value_difference < 0 THEN -sle.stock_value_difference END), 0) AS outgoing
		FROM `tabStock Ledger Entry` sle
		WHERE sle.is_cancelled = 0 AND sle.company = %(company)s
		AND sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY bucket
	""".format(bucket=_bucket_expr(ctx, "sle.posting_date")), _params(ctx), as_dict=True)

	return dict(_meta(ctx), **{
		"kpis": {
			"stock_value": flt(total_value, 2),
			"item_count": len(items),
			"dead_count": classes["dead"]["count"],
			"dead_value": flt(classes["dead"]["value"], 2),
			"slow_count": classes["slow"]["count"],
			"low_count": classes["low"]["count"],
		},
		"classification": [dict(v, key=k, value=flt(v["value"], 2)) for k, v in classes.items()],
		"by_item_group": _top_n_with_other(by_group, 8),
		"top_items": top_items,
		"movement": _fill(ctx, movement_rows, ["incoming", "outgoing"]),
	})


# ═══════════════════════════════════════════════════════════════════════════
# Customers
# ═══════════════════════════════════════════════════════════════════════════

def _customer_sales(ctx, prev=False):
	rows = frappe.db.sql("""
		SELECT si.customer, MAX(si.customer_name) AS customer_name,
			COALESCE(SUM(si.base_net_total), 0) AS amount,
			SUM(CASE WHEN si.is_return = 0 THEN 1 ELSE 0 END) AS invoices
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1 AND si.is_opening = 'No'
		AND si.company = %(company)s
		AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY si.customer
	""", _params(ctx, prev), as_dict=True)
	return {r.customer: r for r in rows}


@frappe.whitelist()
def get_customer_analytics(company=None, period=None, from_date=None, to_date=None):
	ctx = _context(company, period, from_date, to_date)

	current = _customer_sales(ctx)
	previous = _customer_sales(ctx, prev=True)
	active = [c for c, r in current.items() if cint(r.invoices) > 0]
	prev_active = [c for c, r in previous.items() if cint(r.invoices) > 0]

	# First-ever invoice date per customer → new customers in period
	first_rows = frappe.db.sql("""
		SELECT customer, MIN(posting_date) AS first_date
		FROM `tabSales Invoice`
		WHERE docstatus = 1 AND is_opening = 'No' AND is_return = 0 AND company = %(company)s
		GROUP BY customer
		HAVING first_date BETWEEN %(from_date)s AND %(to_date)s
	""", _params(ctx), as_dict=True)
	bucket_fmt = "%Y-%m-%d" if ctx.gran == "daily" else "%Y-%m"
	new_by_bucket = {}
	for r in first_rows:
		k = getdate(r.first_date).strftime(bucket_fmt)
		new_by_bucket[k] = new_by_bucket.get(k, 0) + 1

	active_rows = frappe.db.sql("""
		SELECT {bucket} AS bucket, COUNT(DISTINCT si.customer) AS active
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1 AND si.is_opening = 'No' AND si.is_return = 0
		AND si.company = %(company)s
		AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY bucket
	""".format(bucket=_bucket_expr(ctx, "si.posting_date")), _params(ctx), as_dict=True)
	trend = _fill(ctx, active_rows, ["active"])
	for t in trend:
		t["new"] = new_by_bucket.get(t["key"], 0)

	top_customers = sorted(
		[{"name": r.customer_name or c, "amount": flt(r.amount, 2), "invoices": cint(r.invoices)}
		 for c, r in current.items() if flt(r.amount) > 0],
		key=lambda r: r["amount"], reverse=True)[:10]

	receivables = frappe.db.sql("""
		SELECT gle.party AS customer, COALESCE(SUM(gle.debit - gle.credit), 0) AS balance
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND acc.account_type = 'Receivable'
		AND gle.party_type = 'Customer' AND gle.company = %(company)s
		AND gle.posting_date <= %(to_date)s
		GROUP BY gle.party
	""", _params(ctx), as_dict=True)
	total_receivable = flt(sum(flt(r.balance) for r in receivables), 2)
	names = dict(frappe.get_all("Customer", fields=["name", "customer_name"],
								filters={"name": ["in", [r.customer for r in receivables] or [""]]},
								as_list=True))
	top_receivables = sorted(
		[{"name": names.get(r.customer) or r.customer, "balance": flt(r.balance, 2)}
		 for r in receivables if flt(r.balance) > 0.005],
		key=lambda r: r["balance"], reverse=True)[:10]

	# Customer concentration: top 10 share of sales
	total_sales = sum(flt(r.amount) for r in current.values())
	top10 = sum(r["amount"] for r in top_customers)

	growing, declining = _changes(current, previous, "customer", "customer_name", "amount")

	return dict(_meta(ctx), **{
		"kpis": {
			"active_customers": len(active),
			"active_change_pct": _pct(len(prev_active), len(active)),
			"new_customers": len(first_rows),
			"avg_per_customer": flt(total_sales / len(active), 2) if active else 0,
			"receivable": total_receivable,
			"top10_share_pct": flt(top10 / total_sales * 100, 1) if total_sales else None,
		},
		"trend": trend,
		"top_customers": top_customers,
		"top_receivables": top_receivables,
		"concentration": [
			{"label": "أعلى 10 عملاء", "value": flt(top10, 2)},
			{"label": "باقي العملاء", "value": flt(max(total_sales - top10, 0), 2)},
		],
		"growing_customers": growing,
		"declining_customers": declining,
	})


# ═══════════════════════════════════════════════════════════════════════════
# Expenses (operating expenses from the GL)
# ═══════════════════════════════════════════════════════════════════════════

def _expense_by_account(ctx, prev=False):
	rows = frappe.db.sql("""
		SELECT gle.account, acc.account_name,
			COALESCE(SUM(gle.debit - gle.credit), 0) AS amount
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.is_opening = 'No'
		AND gle.voucher_type != 'Period Closing Voucher'
		AND acc.root_type = 'Expense' AND IFNULL(acc.account_type, '') NOT IN %(cos)s
		AND gle.company = %(company)s
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY gle.account
	""", _params(ctx, prev, cos=COST_OF_SALES_TYPES), as_dict=True)
	return {r.account: r for r in rows}


@frappe.whitelist()
def get_expense_analytics(company=None, period=None, from_date=None, to_date=None):
	ctx = _context(company, period, from_date, to_date)

	current = _expense_by_account(ctx)
	previous = _expense_by_account(ctx, prev=True)
	pl = _pl_totals(ctx)
	total = pl["expenses"]
	prev_total = flt(sum(flt(r.amount) for r in previous.values()), 2)

	trend_rows = frappe.db.sql("""
		SELECT {bucket} AS bucket, COALESCE(SUM(gle.debit - gle.credit), 0) AS amount
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.is_opening = 'No'
		AND gle.voucher_type != 'Period Closing Voucher'
		AND acc.root_type = 'Expense' AND IFNULL(acc.account_type, '') NOT IN %(cos)s
		AND gle.company = %(company)s
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY bucket
	""".format(bucket=_bucket_expr(ctx, "gle.posting_date")),
		_params(ctx, cos=COST_OF_SALES_TYPES), as_dict=True)

	by_account = sorted(
		[{"label": r.account_name, "value": flt(r.amount, 2)} for r in current.values() if flt(r.amount) > 0],
		key=lambda r: r["value"], reverse=True)

	accounts = set(current) | set(previous)
	comparison = sorted([{
		"label": (current.get(a) or previous.get(a)).account_name,
		"current": flt(current.get(a, {}).get("amount"), 2),
		"previous": flt(previous.get(a, {}).get("amount"), 2),
	} for a in accounts], key=lambda r: max(r["current"], r["previous"]), reverse=True)[:10]

	return dict(_meta(ctx), **{
		"kpis": {
			"expenses": total,
			"previous_expenses": prev_total,
			"expenses_change_pct": _pct(prev_total, total),
			"expenses_to_sales_pct": flt(total / pl["sales"] * 100, 1) if pl["sales"] else None,
			"accounts": len([r for r in by_account if r["value"] > 0]),
		},
		"trend": _fill(ctx, trend_rows, ["amount"]),
		"by_account": _top_n_with_other(by_account, 8),
		"comparison": comparison,
	})
