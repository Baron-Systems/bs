# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DecisionCenterExpenseCategory(Document):
	def validate(self):
		self.validate_accounts()

	def validate_accounts(self):
		seen = set()
		for row in self.accounts:
			if not row.enabled:
				continue
			if not row.account:
				frappe.throw(_("Account is required in row {0}").format(row.idx))

			acc = frappe.db.get_value(
				"Account",
				row.account,
				["is_group", "root_type"],
				as_dict=True,
			)
			if not acc:
				frappe.throw(_("Account {0} does not exist").format(row.account))
			if cint(acc.is_group):
				frappe.throw(
					_("Account {0} is a group account; only leaf accounts are allowed").format(row.account)
				)
			if acc.root_type != "Expense":
				frappe.throw(
					_("Account {0} must be an Expense account").format(row.account)
				)

			if row.account in seen:
				frappe.throw(
					_("Account {0} is duplicated inside this category").format(row.account)
				)
			seen.add(row.account)

			# Global uniqueness across enabled categories
			if row.account in _get_enabled_accounts_except(self.name):
				frappe.throw(
					_("Account {0} is already mapped to another enabled expense category").format(
						row.account
					)
				)


def _get_enabled_accounts_except(exclude_name=None):
	filters = {"parenttype": "Decision Center Expense Category", "enabled": 1}
	or_filters = []
	if exclude_name:
		or_filters.append(["parent", "!=", exclude_name])

	rows = frappe.get_all(
		"Decision Center Expense Account",
		filters=filters,
		or_filters=or_filters,
		fields=["account"],
	)
	return {r.account for r in rows}
