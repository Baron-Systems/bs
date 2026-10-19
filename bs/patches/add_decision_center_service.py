# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Patch: Add Decision Center service to BS Home Settings.

Idempotent — safe to run multiple times.
- Appends decision_center to existing cards_config only if missing
- Never reorders, duplicates, or resets existing entries
- Handles missing/empty/malformed cards_config gracefully
"""

from __future__ import unicode_literals

import json

import frappe


DECISION_CENTER_CARD = {
    "id": "decision_center",
    "label": "\u0645\u0631\u0643\u0632 \u0627\u0644\u0642\u0631\u0627\u0631",
    "route": "DecisionCenter",
    "type": "route",
    "enabled": 1,
    "users": [],
}


def execute():
    """Append decision_center to stored BS Home Settings cards_config."""
    try:
        doc = frappe.get_doc("BS Home Settings", "BS Home Settings")
    except frappe.DoesNotExistError:
        # DocType or single doc doesn't exist yet — nothing to patch
        return
    except Exception:
        # Any other error (permissions, DB) — log and skip
        frappe.log_error(
            title="Decision Center patch: cannot read BS Home Settings",
            message=frappe.get_traceback(),
        )
        return

    raw = doc.get("cards_config")

    # ── No stored config → nothing to patch (defaults handle it) ──
    if not raw or not raw.strip():
        return

    # ── Parse existing config ──
    try:
        cards = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Malformed JSON — log warning, do NOT overwrite
        frappe.log_error(
            title="Decision Center patch: malformed cards_config — skipping",
            message=f"Could not parse cards_config: {raw[:500]}",
        )
        return

    if not isinstance(cards, list):
        frappe.log_error(
            title="Decision Center patch: cards_config is not a list — skipping",
            message=f"Type: {type(cards).__name__}",
        )
        return

    # ── Idempotent check ──
    existing_ids = {c.get("id") for c in cards if isinstance(c, dict)}
    if "decision_center" in existing_ids:
        # Already present — nothing to do
        return

    # ── Append and save ──
    cards.append(DECISION_CENTER_CARD)
    doc.cards_config = json.dumps(cards, ensure_ascii=False)
    doc.save(ignore_permissions=True)
    frappe.db.commit()
