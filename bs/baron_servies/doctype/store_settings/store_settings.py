# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class StoreSettings(Document):
	def validate(self):
		if cint(self.is_enabled):
			from bs.baron_servies.api.store import missing_settings

			missing = missing_settings(self)
			if missing:
				frappe.throw(_("لا يمكن تفعيل المتجر قبل تحديد: {0}").format("، ".join(missing)))
		if self.default_warehouse and self.company:
			wh_company = frappe.db.get_value("Warehouse", self.default_warehouse, "company")
			if wh_company and wh_company != self.company:
				frappe.throw(_("المستودع {0} لا يتبع الشركة {1}").format(self.default_warehouse, self.company))
		seen = set()
		for area in self.delivery_areas:
			area.area_name = (area.area_name or "").strip()
			name = area.area_name
			if name in seen:
				frappe.throw(_("منطقة التوصيل مكررة: {0}").format(name))
			seen.add(name)
			if flt(area.delivery_fee) < 0:
				frappe.throw(_("رسوم التوصيل لا يمكن أن تكون سالبة"))

	def on_update(self):
		from bs.baron_servies.api.store import clear_store_cache

		clear_store_cache()
