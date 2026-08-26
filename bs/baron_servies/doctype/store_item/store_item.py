# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class StoreItem(Document):
	def validate(self):
		if self.item:
			# Auto-fill price from Item.standard_rate if not set
			if not self.price:
				std_rate = frappe.db.get_value("Item", self.item, "standard_rate")
				if std_rate:
					self.price = std_rate
			# Auto-fill image from Item.image if not set
			if not self.image:
				item_image = frappe.db.get_value("Item", self.item, "image")
				if item_image:
					self.image = item_image
