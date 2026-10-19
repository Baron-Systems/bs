# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_first_day, get_last_day, getdate

from bs.baron_servies.api.employees.payroll_calc import totals


class BSPayrollEntry(Document):
	@property
	def period_end(self):
		return get_last_day(getdate(self.period))

	def validate(self):
		self.period = get_first_day(getdate(self.period))
		existing = frappe.db.get_value(
			"BS Payroll Entry",
			{"employee": self.employee, "period": self.period, "name": ["!=", self.name]},
			"name",
		)
		if existing:
			frappe.throw(_("يوجد استحقاق لهذا الموظف عن نفس الشهر: {0}").format(existing))
		self.update_totals()

	def update_totals(self):
		lines = [{"line_type": l.line_type, "amount": l.amount} for l in self.lines]
		(self.total_earnings, self.total_deductions, self.total_advances,
			self.gross_amount, self.net_amount) = totals(self.base_amount, lines)

	def on_trash(self):
		if self.status != "Draft":
			frappe.throw(_("لا يمكن حذف استحقاق معتمد أو مدفوع"))
