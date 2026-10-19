# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate
from frappe.utils.html_utils import sanitize_html


class StoreAdvertisement(Document):
	def validate(self):
		if self.start_date and self.end_date:
			if getdate(self.start_date) > getdate(self.end_date):
				frappe.throw(_("تاريخ البداية لا يمكن أن يكون بعد تاريخ النهاية"))
		# Content is rendered as HTML on the public storefront — strip scripts / handlers.
		self.content = sanitize_html(self.content or "")
		link = (self.link_url or "").strip()
		if link and not re.match(r"^(https?://|/)", link):
			frappe.throw(_("الرابط يجب أن يبدأ بـ https:// أو /"))
		self.link_url = link

	def on_update(self):
		from bs.baron_servies.api.store import clear_store_cache

		clear_store_cache()

	def on_trash(self):
		from bs.baron_servies.api.store import clear_store_cache

		clear_store_cache()
