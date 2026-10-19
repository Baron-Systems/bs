# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Metrics Engine for the Decision Center.

Every query is:
  • **Return-safe** – uses ``SUM(qty/amount)`` across normal + return docs
    (ERPNext returns already store negative values; no manual negation).
  • **Company-safe** – stock queries filter by ``Bin.company``; invoice
    queries filter by the ``company`` field on the invoice header.
  • **Snapshot-aware** – Bin data is the *current* stock snapshot.
"""

from __future__ import unicode_literals

import frappe
from frappe.utils import flt, getdate, date_diff


# ═══════════════════════════════════════════════════════════════════════════
# Sales metrics
# ═══════════════════════════════════════════════════════════════════════════

def _sales_agg(company, from_date, to_date):
    """Aggregate net sales from Sales Invoice (return-safe).

    Returns dict with ``total``, ``count`` (non-return invoices only),
    ``avg_invoice``.
    """
    row = frappe.db.sql("""
        SELECT
            COALESCE(SUM(grand_total), 0)   AS total,
            SUM(CASE WHEN is_return = 0 THEN 1 ELSE 0 END) AS cnt
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND company = %(company)s
          AND posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, {"company": company, "from_date": from_date, "to_date": to_date},
        as_dict=True)[0]

    total = flt(row.total)
    cnt = int(row.cnt or 0)
    avg_inv = flt(total / cnt) if cnt else 0
    return {"total": total, "count": cnt, "avg_invoice": avg_inv}


def get_sales_metrics(company, from_date, to_date, prev_from, prev_to):
    """Sales summary with period comparison."""
    current = _sales_agg(company, from_date, to_date)
    previous = _sales_agg(company, prev_from, prev_to)
    growth = _pct_change(previous["total"], current["total"])

    # Active customers (non-return invoices only)
    active = frappe.db.sql("""
        SELECT COUNT(DISTINCT customer) AS cnt
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND is_return = 0
          AND company = %(company)s
          AND posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, {"company": company, "from_date": from_date, "to_date": to_date})[0][0]

    prev_active = frappe.db.sql("""
        SELECT COUNT(DISTINCT customer) AS cnt
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND is_return = 0
          AND company = %(company)s
          AND posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, {"company": company, "from_date": prev_from, "to_date": prev_to})[0][0]

    active_int = int(active or 0)
    prev_active_int = int(prev_active or 0)

    return {
        "total": current["total"],
        "count": current["count"],
        "avg_invoice": current["avg_invoice"],
        "prev_total": previous["total"],
        "prev_count": previous["count"],
        "growth_pct": growth,
        "active_customers": active_int,
        "prev_active_customers": prev_active_int,
        "active_customers_change_pct": _pct_change(prev_active_int, active_int),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Purchase metrics
# ═══════════════════════════════════════════════════════════════════════════

def _purchase_agg(company, from_date, to_date):
    row = frappe.db.sql("""
        SELECT
            COALESCE(SUM(grand_total), 0)   AS total,
            SUM(CASE WHEN is_return = 0 THEN 1 ELSE 0 END) AS cnt
        FROM `tabPurchase Invoice`
        WHERE docstatus = 1
          AND company = %(company)s
          AND posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, {"company": company, "from_date": from_date, "to_date": to_date},
        as_dict=True)[0]

    total = flt(row.total)
    cnt = int(row.cnt or 0)
    return {"total": total, "count": cnt}


def get_purchase_metrics(company, from_date, to_date, prev_from, prev_to):
    current = _purchase_agg(company, from_date, to_date)
    previous = _purchase_agg(company, prev_from, prev_to)
    growth = _pct_change(previous["total"], current["total"])
    return {
        "total": current["total"],
        "count": current["count"],
        "prev_total": previous["total"],
        "prev_count": previous["count"],
        "growth_pct": growth,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Stock metrics  (current snapshot from Bin)
# ═══════════════════════════════════════════════════════════════════════════

def get_stock_summary(company):
    """Total stock value and item count — current snapshot."""
    row = frappe.db.sql("""
        SELECT
            COALESCE(SUM(b.stock_value), 0) AS total_value,
            COUNT(DISTINCT b.item_code)     AS item_count
        FROM `tabBin` b
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        WHERE b.actual_qty > 0
          AND w.company = %(company)s
    """, {"company": company}, as_dict=True)[0]

    return {
        "total_value": flt(row.total_value),
        "item_count": int(row.item_count or 0),
    }


def get_item_stock(company):
    """Per-item stock data — current snapshot, company-safe.

    Returns list of dicts: item_code, item_name, item_group, stock_uom,
    actual_qty, valuation_rate, stock_value.
    """
    return frappe.db.sql("""
        SELECT
            b.item_code,
            i.item_name,
            i.item_group,
            i.stock_uom,
            SUM(b.actual_qty)       AS actual_qty,
            -- weighted-average valuation rate across warehouses
            CASE WHEN SUM(b.actual_qty) > 0
                 THEN SUM(b.stock_value) / SUM(b.actual_qty)
                 ELSE 0 END         AS valuation_rate,
            SUM(b.stock_value)      AS stock_value
        FROM `tabBin` b
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE w.company = %(company)s
          AND i.disabled = 0
          AND i.is_stock_item = 1
        GROUP BY b.item_code
    """, {"company": company}, as_dict=True)


# ═══════════════════════════════════════════════════════════════════════════
# Item-level sales  (return-safe)
# ═══════════════════════════════════════════════════════════════════════════

def get_item_sales(company, from_date, to_date):
    """Per-item net sales qty and amount (return-safe).

    Returns list of dicts: item_code, item_name, net_qty, net_amount,
    invoice_count.
    """
    days = max(date_diff(to_date, from_date) + 1, 1)

    rows = frappe.db.sql("""
        SELECT
            sii.item_code,
            sii.item_name,
            SUM(sii.qty)                AS net_qty,
            SUM(sii.amount)             AS net_amount,
            COUNT(DISTINCT si.name)     AS invoice_count
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1
          AND si.company = %(company)s
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY sii.item_code
    """, {"company": company, "from_date": from_date, "to_date": to_date},
        as_dict=True)

    for r in rows:
        r["net_qty"] = flt(r["net_qty"])
        r["net_amount"] = flt(r["net_amount"])
        r["avg_daily_qty"] = flt(r["net_qty"] / days) if r["net_qty"] > 0 else 0
        r["days"] = days

    return rows


# ═══════════════════════════════════════════════════════════════════════════
# Item-level purchases  (return-safe)
# ═══════════════════════════════════════════════════════════════════════════

def get_item_purchases(company, from_date, to_date):
    """Per-item net purchase qty, amount, avg rate (return-safe)."""
    rows = frappe.db.sql("""
        SELECT
            pii.item_code,
            pii.item_name,
            SUM(pii.qty)                AS net_qty,
            SUM(pii.amount)             AS net_amount,
            COUNT(DISTINCT pi.name)     AS invoice_count
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE pi.docstatus = 1
          AND pi.company = %(company)s
          AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY pii.item_code
    """, {"company": company, "from_date": from_date, "to_date": to_date},
        as_dict=True)

    for r in rows:
        r["net_qty"] = flt(r["net_qty"])
        r["net_amount"] = flt(r["net_amount"])
        r["avg_rate"] = flt(r["net_amount"] / r["net_qty"]) if r["net_qty"] > 0 else 0

    return rows


# ═══════════════════════════════════════════════════════════════════════════
# Customer-level sales  (return-safe)
# ═══════════════════════════════════════════════════════════════════════════

def get_customer_sales(company, from_date, to_date):
    """Per-customer net sales (return-safe)."""
    return frappe.db.sql("""
        SELECT
            si.customer,
            si.customer_name,
            COALESCE(SUM(si.grand_total), 0)   AS net_total,
            SUM(CASE WHEN si.is_return = 0 THEN 1 ELSE 0 END) AS invoice_count
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.company = %(company)s
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY si.customer
    """, {"company": company, "from_date": from_date, "to_date": to_date},
        as_dict=True)


def get_customer_last_purchase_dates(company):
    """Return last non-return invoice date per customer."""
    return frappe.db.sql("""
        SELECT
            customer,
            MAX(posting_date)  AS last_date,
            COUNT(*)           AS total_invoices
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND is_return = 0
          AND company = %(company)s
        GROUP BY customer
    """, {"company": company}, as_dict=True)


def get_customer_purchase_gaps(company, customer):
    """Return average gap in days between successive invoices for a customer."""
    dates = frappe.db.sql("""
        SELECT posting_date
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND is_return = 0
          AND company = %(company)s
          AND customer = %(customer)s
        ORDER BY posting_date ASC
    """, {"company": company, "customer": customer}, as_list=True)

    if len(dates) < 2:
        return None

    gaps = []
    for i in range(1, len(dates)):
        gap = date_diff(dates[i][0], dates[i - 1][0])
        if gap > 0:
            gaps.append(gap)

    return flt(sum(gaps) / len(gaps)) if gaps else None


# ═══════════════════════════════════════════════════════════════════════════
# Top items by various criteria (for tab views)
# ═══════════════════════════════════════════════════════════════════════════

def get_top_items_by_sales(company, from_date, to_date, limit=10):
    """Top selling items by net amount."""
    return frappe.db.sql("""
        SELECT
            sii.item_code,
            sii.item_name,
            SUM(sii.qty)    AS net_qty,
            SUM(sii.amount) AS net_amount
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1
          AND si.company = %(company)s
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY sii.item_code
        HAVING net_qty > 0
        ORDER BY net_amount DESC
        LIMIT %(limit)s
    """, {"company": company, "from_date": from_date, "to_date": to_date,
          "limit": limit}, as_dict=True)


def get_top_items_by_purchases(company, from_date, to_date, limit=10):
    """Top purchased items by net amount."""
    return frappe.db.sql("""
        SELECT
            pii.item_code,
            pii.item_name,
            SUM(pii.qty)    AS net_qty,
            SUM(pii.amount) AS net_amount
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE pi.docstatus = 1
          AND pi.company = %(company)s
          AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY pii.item_code
        HAVING net_qty > 0
        ORDER BY net_amount DESC
        LIMIT %(limit)s
    """, {"company": company, "from_date": from_date, "to_date": to_date,
          "limit": limit}, as_dict=True)


def get_top_suppliers(company, from_date, to_date, limit=10):
    """Top suppliers by net purchase amount."""
    return frappe.db.sql("""
        SELECT
            pi.supplier,
            pi.supplier_name,
            COALESCE(SUM(pi.grand_total), 0) AS net_total,
            SUM(CASE WHEN pi.is_return = 0 THEN 1 ELSE 0 END) AS invoice_count
        FROM `tabPurchase Invoice` pi
        WHERE pi.docstatus = 1
          AND pi.company = %(company)s
          AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY pi.supplier
        HAVING net_total > 0
        ORDER BY net_total DESC
        LIMIT %(limit)s
    """, {"company": company, "from_date": from_date, "to_date": to_date,
          "limit": limit}, as_dict=True)


def get_top_customers(company, from_date, to_date, limit=10):
    """Top customers by net sales amount."""
    return frappe.db.sql("""
        SELECT
            si.customer,
            si.customer_name,
            COALESCE(SUM(si.grand_total), 0) AS net_total,
            SUM(CASE WHEN si.is_return = 0 THEN 1 ELSE 0 END) AS invoice_count
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.company = %(company)s
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY si.customer
        HAVING net_total > 0
        ORDER BY net_total DESC
        LIMIT %(limit)s
    """, {"company": company, "from_date": from_date, "to_date": to_date,
          "limit": limit}, as_dict=True)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _pct_change(old, new):
    """Percentage change from *old* to *new*.  Returns 0 when old is zero."""
    old = flt(old)
    new = flt(new)
    if old == 0:
        return 100.0 if new > 0 else (0.0 if new == 0 else -100.0)
    return flt(((new - old) / abs(old)) * 100, 2)
