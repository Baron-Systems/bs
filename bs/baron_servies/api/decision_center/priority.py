# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
Priority Engine for the Decision Center.

Computes a deterministic score (0-100) for each decision based on:
  • severity_base   – base score from rule severity
  • impact_score    – financial impact (stock value, sales amount)
  • change_score    – magnitude of percentage change
"""

from __future__ import unicode_literals

from frappe.utils import flt

from . import config as cfg


# ───────────────────────────────────────────────────────────────────────────
# Severity base scores
# ───────────────────────────────────────────────────────────────────────────

_SEVERITY_BASE = {
    "critical": 50,
    "high": 40,
    "medium": 25,
    "low": 10,
}


def compute_score(decision):
    """Compute priority score (0–100) and attach ``score`` + ``priority``
    fields to the decision dict *in place*.

    Returns the decision for convenience.
    """
    severity = decision.get("severity", "medium")
    base = _SEVERITY_BASE.get(severity, 25)

    impact = _impact_score(decision)
    change = _change_score(decision)

    raw = base + impact + change
    score = max(0, min(100, int(raw)))

    decision["score"] = score
    decision["priority"] = _label(score)
    return decision


def _impact_score(decision):
    """0–30 based on financial impact."""
    val = flt(decision.get("impact_value", 0))
    if val <= 0:
        return 0
    if val > 100000:
        return 30
    if val > 50000:
        return 25
    if val > 20000:
        return 20
    if val > 10000:
        return 15
    if val > 5000:
        return 10
    if val > 1000:
        return 5
    return 2


def _change_score(decision):
    """0–20 based on percentage change magnitude."""
    pct = abs(flt(decision.get("change_pct", 0)))
    if pct >= 80:
        return 20
    if pct >= 60:
        return 15
    if pct >= 40:
        return 10
    if pct >= 20:
        return 5
    return 0


def _label(score):
    """Map score to priority label."""
    if score >= cfg.get_threshold('PRIORITY_URGENT'):
        return "urgent"
    if score >= cfg.get_threshold('PRIORITY_IMPORTANT'):
        return "important"
    if score >= cfg.get_threshold('PRIORITY_REVIEW'):
        return "review"
    return "opportunity"
