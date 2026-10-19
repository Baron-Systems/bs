# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Tests for snapshot immutability, revision history and permission integrity."""

from __future__ import unicode_literals

import json

import frappe
import frappe.utils
from frappe.tests.utils import FrappeTestCase


class TestSnapshotRevisionDocType(FrappeTestCase):

    def test_snapshot_revision_is_separate_doctype(self):
        """Snapshot Revision must be queried by parent_snapshot, not a child table."""
        snap = frappe.new_doc("Decision Center Monthly Snapshot")
        snap.month = "2026-01"
        snap.insert(ignore_permissions=True)

        rev = frappe.new_doc("Decision Center Snapshot Revision")
        rev.parent_snapshot = snap.name
        rev.revision_number = 1
        rev.action = "generated"
        rev.performed_by = "Administrator"
        rev.performed_at = frappe.utils.now()
        rev.reason = "Test generation"
        rev.insert(ignore_permissions=True)

        revisions = frappe.get_all(
            "Decision Center Snapshot Revision",
            filters={"parent_snapshot": snap.name},
            pluck="name",
        )
        self.assertGreaterEqual(len(revisions), 1)

        frappe.delete_doc("Decision Center Snapshot Revision", rev.name, force=True, ignore_permissions=True)
        frappe.delete_doc("Decision Center Monthly Snapshot", snap.name, force=True, ignore_permissions=True)

    def test_locked_snapshot_cannot_be_regenerated(self):
        """Regenerating a locked snapshot must be rejected."""
        from ..snapshot_service import _generate_snapshot, lock_snapshot, regenerate_snapshot

        snap = _generate_snapshot("2026-02", company="_Test Company", called_by_scheduler=False)
        lock_snapshot("2026-02")

        with self.assertRaises(frappe.ValidationError):
            regenerate_snapshot("2026-02", "Attempted after lock")

        for rev in frappe.get_all("Decision Center Snapshot Revision", filters={"parent_snapshot": snap.name}, pluck="name"):
            frappe.delete_doc("Decision Center Snapshot Revision", rev, force=True, ignore_permissions=True)
        frappe.delete_doc("Decision Center Monthly Snapshot", snap.name, force=True, ignore_permissions=True)

    def test_monthly_report_reads_from_snapshot_only(self):
        """Monthly report endpoint must not issue live metric queries."""
        snap = frappe.new_doc("Decision Center Monthly Snapshot")
        snap.month = "2026-03"
        snap.metrics_snapshot = json.dumps({"sales_total": {"value": 99999}})
        snap.expense_categories_snapshot = json.dumps({"total_expenses": 0})
        snap.inventory_snapshot = json.dumps({"unavailable": False})
        snap.plan_snapshot = json.dumps({"active_plan": None})
        snap.decisions_snapshot = json.dumps({"count": 0, "decisions": []})
        snap.settings_version = json.dumps({})
        snap.rule_version_hash = "abc"
        snap.engine_version = "1.0.0"
        snap.insert(ignore_permissions=True)

        from ..snapshot_api import get_monthly_report
        report = get_monthly_report("2026-03")
        self.assertEqual(report["metrics"]["sales_total"]["value"], 99999)

        frappe.delete_doc("Decision Center Monthly Snapshot", snap.name, ignore_permissions=True)

    def test_snapshot_integrity_ignores_later_setting_changes(self):
        """Changing settings after snapshot generation must not alter the stored snapshot."""
        from ..snapshot_service import _generate_snapshot

        # Create a minimal snapshot for a month in the past
        snap = _generate_snapshot("2025-12", company="_Test Company", called_by_scheduler=False)
        snap.db_set("locked", 1)
        snap.reload()
        original_metrics = json.loads(snap.metrics_snapshot)

        # Mutate settings after snapshot is locked
        settings = frappe.get_doc("Decision Center Settings", "Decision Center Settings")
        old_threshold = settings.slow_moving_days
        settings.slow_moving_days = old_threshold + 999
        settings.save(ignore_permissions=True)

        # Re-read snapshot from DB
        reloaded = frappe.get_doc("Decision Center Monthly Snapshot", snap.name)
        reloaded_metrics = json.loads(reloaded.metrics_snapshot)
        self.assertEqual(reloaded_metrics, original_metrics)

        # Restore
        settings.slow_moving_days = old_threshold
        settings.save(ignore_permissions=True)
        for rev in frappe.get_all("Decision Center Snapshot Revision", filters={"parent_snapshot": snap.name}, pluck="name"):
            frappe.delete_doc("Decision Center Snapshot Revision", rev, force=True, ignore_permissions=True)
        frappe.delete_doc("Decision Center Monthly Snapshot", snap.name, force=True, ignore_permissions=True)
