# -*- coding: utf-8 -*-
# Copyright (c) 2026, AL Baron Systems and contributors
# For license information, please see license.txt

"""Patch: Add the Employees section cards to a stored BS Home Settings cards_config.

Idempotent — employee cards are kept as one ordered block; their enabled/users values are preserved.
When no config is stored the defaults in utilities._DEFAULT_HOME_CARDS apply.
"""

import json

import frappe


def execute():
	from bs.baron_servies.api.utilities import EMPLOYEE_CARDS

	try:
		doc = frappe.get_doc("BS Home Settings", "BS Home Settings")
	except frappe.DoesNotExistError:
		return

	raw = doc.get("cards_config")
	if not raw or not raw.strip():
		return

	try:
		cards = json.loads(raw)
	except (json.JSONDecodeError, TypeError):
		frappe.log_error(title="Employees patch: malformed cards_config — skipping", message=raw[:500])
		return
	if not isinstance(cards, list):
		return

	# Re-emit the Employees cards as one block in canonical order, keeping any stored
	# enabled/users choices; other cards keep their positions.
	employee_ids = [c["id"] for c in EMPLOYEE_CARDS]
	stored = {c.get("id"): c for c in cards if isinstance(c, dict) and c.get("id") in employee_ids}
	block = [{**c, **{k: stored[c["id"]][k] for k in ("enabled", "users") if k in stored.get(c["id"], {})}} for c in EMPLOYEE_CARDS]
	positions = [i for i, c in enumerate(cards) if isinstance(c, dict) and c.get("id") in employee_ids]
	insert_at = positions[0] if positions else len(cards)
	others = [c for c in cards if not (isinstance(c, dict) and c.get("id") in employee_ids)]
	insert_at = min(insert_at, len(others))
	new_cards = others[:insert_at] + block + others[insert_at:]
	if new_cards == cards:
		return

	cards = new_cards
	doc.cards_config = json.dumps(cards, ensure_ascii=False)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
