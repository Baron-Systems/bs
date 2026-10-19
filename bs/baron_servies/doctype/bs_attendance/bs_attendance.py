# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from bs.baron_servies.api.employees.common import employee_schedule, get_settings, to_minutes, working_dates


class BSAttendance(Document):
	def validate(self):
		self.validate_duplicate()
		self.compute_times()

	def validate_duplicate(self):
		existing = frappe.db.get_value(
			"BS Attendance",
			{"employee": self.employee, "attendance_date": self.attendance_date, "name": ["!=", self.name]},
			"name",
		)
		if existing:
			frappe.throw(_("يوجد سجل دوام لهذا الموظف في نفس التاريخ: {0}").format(existing))

	def compute_times(self):
		self.working_hours = 0
		self.late_minutes = 0
		self.early_exit_minutes = 0
		self.overtime_hours = 0

		if self.status not in ("Present", "Work Mission"):
			self.check_in = None
			self.check_out = None
			return

		check_in = to_minutes(self.check_in)
		check_out = to_minutes(self.check_out)
		schedule = employee_schedule(self.employee)
		is_work_day = bool(working_dates(self.employee, self.attendance_date, self.attendance_date, schedule))

		if is_work_day and check_in is not None and schedule.start is not None:
			late = check_in - schedule.start
			if late > schedule.grace:
				self.late_minutes = late

		if check_in is None or check_out is None:
			return

		if check_out < check_in:  # overnight shift
			check_out += 24 * 60

		# Arriving before the shift only counts when the settings say so.
		effective_in = check_in
		if (is_work_day and schedule.start is not None and check_in < schedule.start
				and not cint(get_settings().count_early_arrival_as_overtime)):
			effective_in = schedule.start
		worked = max(0, check_out - effective_in)
		self.working_hours = flt(worked / 60, 2)

		if not is_work_day:  # every hour on a day off / holiday is overtime
			self.overtime_hours = self.working_hours
			return

		if schedule.end is not None:
			shift_end = schedule.end if schedule.end >= (schedule.start or 0) else schedule.end + 24 * 60
			self.early_exit_minutes = max(0, shift_end - check_out)

		shift_minutes = schedule.daily_hours * 60
		if schedule.start is not None and schedule.end is not None:
			span = schedule.end - schedule.start
			shift_minutes = span if span > 0 else span + 24 * 60
		self.overtime_hours = flt(max(0, worked - shift_minutes) / 60, 2)
