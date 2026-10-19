# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""Tests for snapshot immutability, revision history and permission integrity."""

from __future__ import unicode_literals

import frappe
import frappe.utils


def test_snapshot_revision_is_separate_doctype():
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
    assert len(revisions) >= 1

    # Clean up
    frappe.delete_doc("Decision Center Snapshot Revision", rev.name, ignore_permissions=True)
    frappe.delete_doc("Decision Center Monthly Snapshot", snap.name, ignore_permissions=True)


def test_locked_snapshot_cannot_be_modified():
    snap = frappe.new_doc("Decision Center Monthly Snapshot")
    snap.month = "2026-02"
    snap.insert(ignore_permissions=True)
    snap.is_locked = 1
    snap.save(ignore_permissions=True)

    # Attempt to mutate a locked snapshot should raise ValidationError
    try:
        snap.metrics_snapshot = "{changed: true}"
        snap.save(ignore_permissions=True)
        raise AssertionError("Locked snapshot mutation succeeded unexpectedly")
    except frappe.ValidationError:
        pass

    frappe.delete_doc("Decision Center Monthly Snapshot", snap.name, ignore_permissions=True)
