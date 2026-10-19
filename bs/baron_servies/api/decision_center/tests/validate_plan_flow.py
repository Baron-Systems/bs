# -*- coding: utf-8 -*-
"""Runtime validation of plan management APIs used by the Vue frontend."""

import json

import frappe
from frappe.utils import nowdate


def run():
    """Create, edit, schedule, activate, complete and clean up a plan via public APIs."""
    from bs.baron_servies.api.decision_center.plan_api import (
        activate_plan,
        cancel_plan,
        complete_plan,
        compute_baseline_preview,
        create_plan,
        get_current_plan,
        get_plan_decisions,
        get_plan_detail,
        get_plan_reference_options,
        has_plan_management_permission,
        schedule_plan,
        update_plan,
        update_plan_actions,
    )

    print("=" * 60)
    print("Decision Center Plan Management Runtime Validation")
    print("=" * 60)

    # 1. Permission
    print("\n[1] Permission checks")
    assert has_plan_management_permission() is True
    print("  -> Administrator has plan management permission: True")

    test_user = "dc_test_user@example.com"
    if not frappe.db.exists("User", test_user):
        user = frappe.get_doc({
            "doctype": "User",
            "email": test_user,
            "first_name": "Test",
            "enabled": 1,
            "roles": [{"role": "Decision Center User"}],
        })
        user.insert(ignore_permissions=True)
    else:
        user = frappe.get_doc("User", test_user)
        user.set("roles", [{"role": "Decision Center User"}])
        user.save(ignore_permissions=True)

    frappe.set_user(test_user)
    assert has_plan_management_permission() is False
    print("  -> Decision Center User has plan management permission: False")
    frappe.set_user("Administrator")

    # 2. Reference options
    print("\n[2] Loading reference options for forms")
    opts = get_plan_reference_options()
    metrics = {m["metric_key"]: m for m in opts["metrics"]}
    assert "sales_total" in metrics
    assert "gross_profit" not in metrics  # not enabled for plans
    assert opts["rules"]
    print("  -> metrics: {}".format(list(metrics.keys())[:5]))
    print("  -> rules: {}".format([r["id"] for r in opts["rules"][:3]]))

    # 3. Baseline preview
    print("\n[3] Baseline preview for sales_total")
    preview = compute_baseline_preview("sales_total", nowdate())
    assert preview is not None and "value" in preview
    print("  -> baseline value: {}".format(preview["value"]))

    # 4. Create plan
    print("\n[4] Creating Draft plan via create_plan")
    payload = {
        "plan_name": "Runtime Validation Plan",
        "description": "Validating full plan lifecycle from the UI backend",
        "priority": "High",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "status": "Draft",
        "kpis": [
            {
                "is_primary": 1,
                "metric_key": "sales_total",
                "direction": "increase",
                "target_value": 50000.0,
                "weight": 1,
                "tolerance_pct": 10,
            },
            {
                "is_primary": 0,
                "metric_key": "active_customers",
                "direction": "increase",
                "target_value": 100.0,
                "weight": 0.5,
                "tolerance_pct": 10,
            },
        ],
        "actions": [
            {
                "title": "Boost sales campaign",
                "description": "Run targeted promotions",
                "due_date": "2026-03-31",
                "status": "Not Started",
                "weight": 1,
                "related_rule_id": "ITEM_SALES_DECLINE",
                "related_metric_key": "sales_total",
            }
        ],
    }

    # Cancel any active plan to avoid activation conflict
    active = frappe.get_all("Decision Center Plan", filters={"status": "Active"}, pluck="name")
    for name in active:
        cancel_plan(name)
        print("  -> cancelled existing active plan: {}".format(name))

    created = create_plan(json.dumps(payload))
    plan_name = created["name"]
    print("  -> created plan: {}".format(plan_name))

    # 5. Edit plan (add action, change target)
    print("\n[5] Editing plan via update_plan")
    payload["actions"].append({
        "title": "Second action",
        "description": "Follow-up",
        "due_date": "2026-06-30",
        "status": "Not Started",
        "weight": 0.5,
    })
    payload["kpis"][0]["target_value"] = 60000.0
    update_plan(plan_name, json.dumps(payload))
    print("  -> plan updated")

    # 6. Plan detail
    print("\n[6] Fetching plan detail")
    detail = get_plan_detail(plan_name)
    assert detail["status"] == "Draft"
    assert len(detail["kpis"]) == 2
    assert len(detail["actions"]) == 2
    print("  -> status: {}, kpis: {}, actions: {}".format(detail["status"], len(detail["kpis"]), len(detail["actions"])))

    # 7. Schedule plan
    print("\n[7] Scheduling plan")
    schedule_plan(plan_name)
    detail = get_plan_detail(plan_name)
    assert detail["status"] == "Scheduled"
    print("  -> status: {}".format(detail["status"]))

    # 8. Activate plan
    print("\n[8] Activating plan")
    activate_plan(plan_name)
    detail = get_plan_detail(plan_name)
    assert detail["status"] == "Active"
    print("  -> status: {}, progress: {}".format(detail["status"], detail["progress"]))

    current = get_current_plan()
    assert current and current["name"] == plan_name
    print("  -> current plan matches: {}".format(current["name"]))

    # 9. Update action status
    print("\n[9] Updating action status (mark first Completed)")
    actions = detail["actions"]
    actions[0]["status"] = "Completed"
    update_plan_actions(plan_name, json.dumps(actions))
    detail = get_plan_detail(plan_name)
    assert detail["actions"][0]["status"] == "Completed"
    assert detail["actions"][0]["completed_by"]
    print("  -> first action completed by: {}".format(detail["actions"][0]["completed_by"]))

    # 10. Related decisions
    print("\n[10] Fetching related decisions")
    decisions = get_plan_decisions(plan_name)
    print("  -> related decisions count: {}".format(len(decisions["decisions"])))

    # 11. Complete plan
    print("\n[11] Completing plan")
    complete_plan(plan_name)
    detail = get_plan_detail(plan_name)
    assert detail["status"] == "Completed"
    print("  -> status: {}".format(detail["status"]))

    # Cleanup
    print("\n[12] Cleanup")
    frappe.delete_doc("Decision Center Plan", plan_name, force=True, ignore_permissions=True)
    print("  -> deleted validation plan")

    print("\n" + "=" * 60)
    print("All runtime validation checks passed.")
    print("=" * 60)
