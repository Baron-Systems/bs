// Help Center — shared config: tabs, search index, topic map for HelpLink.
import { RULES_HELP, RULE_CATEGORIES } from "./rules"
import { SETTINGS_HELP, SPECIAL_SETTINGS_HELP, SETTINGS_SECTIONS } from "./settings"
import { SCREENS_HELP } from "./screens"
import { SCENARIOS } from "./scenarios"
import { CONCEPTS } from "./concepts"
import { FORMULA_CARDS, PROGRESS_STRATEGIES, UNAVAILABLE_METRICS, AVAILABLE_METRICS } from "./metrics"

export const HELP_TABS = [
	{ id: "start", label: "ابدأ من هنا", icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
	{ id: "plans", label: "الخطط", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" },
	{ id: "screens", label: "شرح الواجهات", icon: "M4 5a1 1 0 011-1h14a1 1 0 011 1v10a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm4 15h8" },
	{ id: "settings", label: "الإعدادات", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065zM15 12a3 3 0 11-6 0 3 3 0 016 0z" },
	{ id: "rules", label: "القواعد الإدارية", icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" },
	{ id: "formulas", label: "كيف تُحسب الأرقام", icon: "M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" },
	{ id: "scenarios", label: "أمثلة عملية", icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" },
]

export const DEFAULT_TAB = "start"

// topic → {tab, section} for contextual ؟ HelpLink
export const HELP_TOPICS = {
	baseline: { tab: "plans", section: "baseline" },
	target: { tab: "plans", section: "target" },
	plan_health: { tab: "plans", section: "plan_health" },
	plan_status: { tab: "plans", section: "plan_status" },
	scheduler_status: { tab: "plans", section: "scheduler_status" },
	checkpoints: { tab: "plans", section: "checkpoints" },
	priority_score: { tab: "formulas", section: "priority_score" },
	expenses_to_sales_pct: { tab: "formulas", section: "expenses_to_sales_pct" },
	days_of_stock: { tab: "formulas", section: "days_of_stock" },
	monthly_snapshot: { tab: "screens", section: "monthly_snapshot" },
	decision: { tab: "screens", section: "decision" },
	settings_overview: { tab: "settings", section: "settings-intro" },
	rules_overview: { tab: "rules", section: "rules-intro" },
}

// ── search index ────────────────────────────────────────────────────────────
// Each entry: {title, text, tab, section} — section is the anchor id.
export const HELP_SEARCH_INDEX = [
	...RULES_HELP.map((r) => ({
		title: r.title,
		text: `${r.title} ${r.conditions.join(" ")} ${r.whyItMatters} ${r.fullNotes}`,
		tab: "rules",
		section: r.id,
	})),
	...SETTINGS_HELP.map((s) => ({
		title: s.label,
		text: `${s.label} ${s.meaning} ${s.example}`,
		tab: "settings",
		section: s.key,
	})),
	...SPECIAL_SETTINGS_HELP.map((s) => ({
		title: s.label,
		text: `${s.label} ${s.meaning}`,
		tab: "settings",
		section: s.key,
	})),
	...SCREENS_HELP.map((s) => ({
		title: s.title,
		text: `${s.title} ${s.purpose} ${s.keyElements.join(" ")}`,
		tab: "screens",
		section: s.id,
	})),
	...SCENARIOS.map((s) => ({
		title: s.title,
		text: `${s.title} ${s.trigger} ${s.steps.map((st) => st.label).join(" ")}`,
		tab: "scenarios",
		section: s.id,
	})),
	...CONCEPTS.map((c) => ({
		title: c.title,
		text: `${c.title} ${c.text}`,
		tab: c.section,
		section: c.id,
	})),
]

export { RULES_HELP, RULE_CATEGORIES, SETTINGS_HELP, SPECIAL_SETTINGS_HELP, SETTINGS_SECTIONS, SCREENS_HELP, SCENARIOS, CONCEPTS, FORMULA_CARDS, PROGRESS_STRATEGIES, UNAVAILABLE_METRICS, AVAILABLE_METRICS }
