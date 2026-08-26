# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class StoreAdvertisement(Document):
	def validate(self):
		if self.start_date and self.end_date:
			if getdate(self.start_date) > getdate(self.end_date):
				frappe.throw("Start date cannot be after end date")
