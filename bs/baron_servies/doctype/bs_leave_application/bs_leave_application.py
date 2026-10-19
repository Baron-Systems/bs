# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate

from bs.baron_servies.api.employees.common import leave_balance, working_dates

LEAVE_LABELS = {
	"Annual": "إجازة سنوية",
	"Sick": "إجازة مرضية",
	"Emergency": "إجازة طارئة",
	"Unpaid": "إجازة بدون راتب",
	"Other": "إجازة",
}


class BSLeaveApplication(Document):
	def validate(self):
		if getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("تاريخ النهاية يجب أن يكون بعد تاريخ البداية"))
		self.total_days = len(working_dates(self.employee, self.from_date, self.to_date))
		if not self.total_days:
			frappe.throw(_("لا توجد أيام عمل ضمن الفترة المحددة"))
		if self.status in ("Pending", "Approved"):
			self.validate_overlap()
			self.validate_balance()
		if self.has_value_changed("status") and self.status in ("Approved", "Rejected"):
			self.approved_by = frappe.session.user
			self.decision_date = nowdate()

	def validate_overlap(self):
		overlap = frappe.db.get_value(
			"BS Leave Application",
			{
				"employee": self.employee,
				"name": ["!=", self.name],
				"status": ["in", ["Pending", "Approved"]],
				"from_date": ["<=", self.to_date],
				"to_date": [">=", self.from_date],
			},
			"name",
		)
		if overlap:
			frappe.throw(_("يوجد طلب إجازة متداخل لنفس الموظف: {0}").format(overlap))

	def validate_balance(self):
		if self.leave_type != "Annual":
			return
		balance = leave_balance(self.employee, getdate(self.from_date).year, exclude=self.name)
		if self.total_days > balance["remaining"]:
			frappe.throw(
				_("رصيد الإجازة السنوية غير كافٍ. المتبقي {0} يوم").format(balance["remaining"])
			)

	def on_update(self):
		self.sync_attendance()

	def on_trash(self):
		self.clear_attendance()

	def clear_attendance(self):
		for name in frappe.get_all("BS Attendance", filters={"leave_application": self.name}, pluck="name"):
			frappe.delete_doc("BS Attendance", name, ignore_permissions=True, force=True)

	def sync_attendance(self):
		"""Approved leave owns its days in attendance; anything else releases them."""
		self.clear_attendance()
		if self.status != "Approved":
			return
		label = LEAVE_LABELS.get(self.leave_type, self.leave_type)
		for day in working_dates(self.employee, self.from_date, self.to_date):
			existing = frappe.db.get_value(
				"BS Attendance", {"employee": self.employee, "attendance_date": day}, "name"
			)
			att = frappe.get_doc("BS Attendance", existing) if existing else frappe.new_doc("BS Attendance")
			att.update(
				{
					"employee": self.employee,
					"company": self.company,
					"attendance_date": day,
					"status": "On Leave",
					"source": "Leave",
					"leave_type": self.leave_type,
					"leave_application": self.name,
					"note": label,
				}
			)
			att.save(ignore_permissions=True)
