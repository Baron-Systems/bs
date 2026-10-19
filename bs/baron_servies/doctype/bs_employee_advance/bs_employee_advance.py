# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

import math

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_first_day, getdate

from bs.baron_servies.api.employees.common import company_currency
from bs.baron_servies.api.employees.payroll_calc import installment_due


class BSEmployeeAdvance(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("قيمة السلفة يجب أن تكون أكبر من صفر"))
		self.currency = company_currency(self.company)
		if not self.start_period:
			self.start_period = self.posting_date
		self.start_period = get_first_day(getdate(self.start_period))
		self.set_installments()
		self.update_balances()

	def set_installments(self):
		if self.recovery_method == "Installments":
			if cint(self.installments_count) > 0 and not flt(self.installment_amount):
				self.installment_amount = flt(math.ceil(flt(self.amount) * 100 / cint(self.installments_count)) / 100, 2)
			if flt(self.installment_amount) <= 0:
				frappe.throw(_("يرجى تحديد قيمة القسط أو عدد الأقساط"))
			self.installments_count = math.ceil(flt(self.amount) / flt(self.installment_amount))
		elif self.recovery_method == "Next Payroll":
			self.installment_amount = self.amount
			self.installments_count = 1
		else:
			self.installment_amount = 0
			self.installments_count = 0

	def update_balances(self):
		self.recovered_amount = flt(sum(flt(r.amount) for r in self.repayments), 2)
		self.remaining_amount = flt(flt(self.amount) - self.recovered_amount, 2)
		if self.remaining_amount < 0:
			frappe.throw(_("المسترد أكبر من قيمة السلفة"))
		if self.status == "Closed":
			return
		if self.remaining_amount <= 0:
			self.status = "Completed"
		elif self.status == "Completed":
			self.status = "Active"

	def due_for(self, period, exclude_entry=None):
		"""Installment this advance should contribute to a payroll period (0 if none)."""
		period = get_first_day(getdate(period))
		if self.status != "Active" or period < getdate(self.start_period):
			return 0
		for r in self.repayments:
			if r.source == "Payroll" and r.period and getdate(r.period) == period and r.payroll_entry != exclude_entry:
				return 0
		# a repayment already booked by the entry being recalculated is released first
		remaining = flt(self.remaining_amount) + sum(
			flt(r.amount) for r in self.repayments if exclude_entry and r.payroll_entry == exclude_entry
		)
		return installment_due(self.recovery_method, self.installment_amount, remaining)
