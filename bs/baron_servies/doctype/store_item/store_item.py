# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class StoreItem(Document):
	def validate(self):
		if self.item:
			# Price is NOT copied from the item any more: 0 means "use the store price list"
			# (see store.resolve_prices), so later price-list changes reach the store.
			if flt(self.price) < 0:
				self.price = 0
			if not self.image:
				item_image = frappe.db.get_value("Item", self.item, "image")
				if item_image:
					self.image = item_image

	def on_update(self):
		from bs.baron_servies.api.store import clear_store_cache

		clear_store_cache()

	def on_trash(self):
		from bs.baron_servies.api.store import clear_store_cache

		clear_store_cache()
