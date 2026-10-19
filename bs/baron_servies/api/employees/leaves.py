# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Leaves (الإجازات): requests, approval flow and annual balance."""

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from bs.baron_servies.api.employees.common import (
	default_company,
	leave_balance,
	parse_json,
	require_hr,
	working_dates,
)

LEAVE_FIELDS = [
	"name", "employee", "employee_name", "leave_type", "from_date", "to_date", "total_days",
	"status", "reason", "attachment", "approved_by", "decision_date", "creation",
]

STATUS_TRANSITIONS = {
	"Pending": {"Approved", "Rejected", "Cancelled"},
	"Approved": {"Cancelled"},
	"Rejected": {"Pending"},
	"Cancelled": {"Pending"},
}


@frappe.whitelist()
def get_leaves(company=None, status=None, employee=None, from_date=None, to_date=None):
	require_hr()
	company = default_company(company)
	filters = {"company": company}
	if status:
		filters["status"] = status
	if employee:
		filters["employee"] = employee
	if from_date and to_date:
		filters["from_date"] = ["<=", to_date]
		filters["to_date"] = [">=", from_date]
	rows = frappe.get_all("BS Leave Application", filters=filters, fields=LEAVE_FIELDS,
		order_by="from_date desc", limit_page_length=500)

	today = getdate(nowdate())
	base = {"company": company}
	summary = {
		"today_requests": frappe.db.count("BS Leave Application",
			{**base, "creation": [">=", str(today)]}),
		"pending": frappe.db.count("BS Leave Application", {**base, "status": "Pending"}),
		"on_leave_now": frappe.db.count("BS Leave Application",
			{**base, "status": "Approved", "from_date": ["<=", today], "to_date": [">=", today]}),
	}
	return {"rows": rows, "summary": summary}


@frappe.whitelist()
def count_days(employee, from_date, to_date):
	require_hr()
	if not (employee and from_date and to_date) or getdate(to_date) < getdate(from_date):
		return {"days": 0}
	return {"days": len(working_dates(employee, from_date, to_date))}


@frappe.whitelist()
def get_leave_balance(employee, year=None):
	require_hr()
	return leave_balance(employee, year)


@frappe.whitelist()
def save_leave(data):
	require_hr()
	data = parse_json(data)
	for field in ("employee", "leave_type", "from_date", "to_date"):
		if not data.get(field):
			frappe.throw(_("يرجى تعبئة الحقول المطلوبة"))
	if data.get("name"):
		doc = frappe.get_doc("BS Leave Application", data["name"])
		if doc.status != "Pending":
			frappe.throw(_("لا يمكن تعديل طلب تم البت فيه"))
	else:
		doc = frappe.new_doc("BS Leave Application")
		doc.status = "Approved" if data.get("approve_now") else "Pending"
	doc.update({k: data.get(k) or None for k in ("employee", "leave_type", "from_date", "to_date", "reason", "attachment")})
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "total_days": doc.total_days, "status": doc.status}


@frappe.whitelist()
def set_leave_status(name, status):
	require_hr()
	doc = frappe.get_doc("BS Leave Application", name)
	if status not in STATUS_TRANSITIONS.get(doc.status, set()):
		frappe.throw(_("لا يمكن تغيير الحالة من {0} إلى {1}").format(doc.status, status))
	doc.status = status
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def delete_leave(name):
	require_hr()
	if frappe.db.get_value("BS Leave Application", name, "status") == "Approved":
		frappe.throw(_("ألغِ الإجازة المعتمدة قبل حذفها"))
	frappe.delete_doc("BS Leave Application", name, ignore_permissions=True)
	return {"success": True}
