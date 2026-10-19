# -*- coding: utf-8 -*-
# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Patch: Seed defaults for the check-in / check-out settings on BS Employee Settings.

Single doctypes don't receive new field defaults on migrate, so empty values are filled here.
Idempotent — only fields that are still empty (NULL) are set.
"""

import frappe

DEFAULTS = {
	"punch_min_interval_minutes": 2,
	"punch_early_window_minutes": 120,
	"punch_require_pin": 0,
	"punch_allow_day_off": 0,
	"count_early_arrival_as_overtime": 0,
}


def execute():
	for field, value in DEFAULTS.items():
		row = frappe.db.sql(
			"select value from `tabSingles` where doctype = %s and field = %s",
			("BS Employee Settings", field),
		)
		if not row or row[0][0] in (None, ""):
			frappe.db.set_single_value("BS Employee Settings", field, value)
	frappe.db.commit()
