import { computed, ref } from "vue"
import { session } from "@/data/session"
import { call } from "@/utils/apiWrapper"

export const SETTINGS_ID = "home_settings"

// Visual/navigation metadata for each service card id returned by the backend.
// `group` controls sidebar grouping; `paths` are inline SVG icon paths.
export const serviceMeta = {
	dashboard: {
		group: "main",
		iconCls: "bg-blue-50 text-blue-600",
		paths: ["M4 6h16M4 10h16M4 14h16M4 18h16"],
	},
	quick_inventory: {
		group: "operations",
		iconCls: "bg-emerald-50 text-emerald-600",
		paths: ["M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"],
	},
	decision_center_overview: {
		group: "decision_center",
		iconCls: "bg-blue-50 text-blue-600",
		paths: ["M4 6a2 2 0 012-2h2a2 2 0 012 2v0a2 2 0 01-2 2H6a2 2 0 01-2-2v0zM14 6a2 2 0 012-2h2a2 2 0 012 2v0a2 2 0 01-2 2h-2a2 2 0 01-2-2v0zM4 16a2 2 0 012-2h2a2 2 0 012 2v0a2 2 0 01-2 2H6a2 2 0 01-2-2v0zM14 16a2 2 0 012-2h2a2 2 0 012 2v0a2 2 0 01-2 2h-2a2 2 0 01-2-2v0z"],
	},
	decision_center_plans: {
		group: "decision_center",
		iconCls: "bg-emerald-50 text-emerald-600",
		paths: ["M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"],
	},
	decision_center_reports: {
		group: "decision_center",
		iconCls: "bg-indigo-50 text-indigo-600",
		paths: ["M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"],
	},
	decision_center_help: {
		group: "decision_center",
		iconCls: "bg-violet-50 text-violet-600",
		paths: ["M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"],
	},
	decision_center_settings: {
		group: "decision_center",
		iconCls: "bg-slate-100 text-slate-500",
		paths: [
			"M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
			"M15 12a3 3 0 11-6 0 3 3 0 016 0z",
		],
	},
	quick_purchase_invoice: {
		group: "operations",
		iconCls: "bg-emerald-50 text-emerald-600",
		paths: ["M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h2m-2 4h2m-2-8h2M5 7h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2z"],
	},
	customer_payment: {
		group: "operations",
		iconCls: "bg-amber-50 text-amber-600",
		paths: ["M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"],
	},
	supplier_payment: {
		group: "operations",
		iconCls: "bg-purple-50 text-purple-600",
		paths: ["M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"],
	},
	customer_report: {
		group: "customers",
		iconCls: "bg-amber-50 text-amber-600",
		paths: ["M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"],
	},
	customer_portal: {
		group: "customers",
		iconCls: "bg-indigo-50 text-indigo-600",
		paths: ["M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"],
	},
	store_manage: {
		group: "store",
		iconCls: "bg-cyan-50 text-cyan-600",
		paths: ["M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"],
	},
	storefront: {
		group: "store",
		iconCls: "bg-emerald-50 text-emerald-600",
		paths: ["M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"],
	},
	decision_center: {
		group: "decision_center",
		iconCls: "bg-blue-50 text-blue-600",
		paths: ["M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"],
	},
	employees: {
		group: "employees",
		iconCls: "bg-indigo-50 text-indigo-600",
		paths: ["M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"],
	},
	employee_payroll: {
		group: "employees",
		iconCls: "bg-blue-50 text-blue-600",
		paths: ["M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"],
	},
	employee_advances: {
		group: "employees",
		iconCls: "bg-amber-50 text-amber-600",
		paths: ["M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"],
	},
	employee_attendance: {
		group: "employees",
		iconCls: "bg-emerald-50 text-emerald-600",
		paths: ["M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"],
	},
	employee_leaves: {
		group: "employees",
		iconCls: "bg-sky-50 text-sky-600",
		paths: ["M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"],
	},
	employee_settings: {
		group: "employees",
		iconCls: "bg-slate-100 text-slate-500",
		paths: [
			"M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
			"M15 12a3 3 0 11-6 0 3 3 0 016 0z",
		],
	},
	[SETTINGS_ID]: {
		group: "admin",
		iconCls: "bg-slate-100 text-slate-500",
		paths: [
			"M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
			"M15 12a3 3 0 11-6 0 3 3 0 016 0z",
		],
	},
}

const NAV_GROUPS = [
	{ id: "main", title: "الرئيسية" },
	{ id: "operations", title: "العمليات" },
	{ id: "customers", title: "العملاء" },
	{ id: "store", title: "المتجر" },
	{ id: "decision_center", title: "مركز القرار", collapsible: true },
	{ id: "employees", title: "الموظفون", collapsible: true },
]

// Decision Center is analytics-only: plans, reports, help and settings are hidden.
const DECISION_CENTER_CHILDREN = []

const ADMIN_GROUP = { id: "admin", title: "الإدارة" }

// Module-level state so the service list is fetched once and shared
// between the app shell (sidebar) and any page that needs it.
const loaded = ref(false)
const loading = ref(false)
const loadError = ref("")
const cards = ref([])

export function useServices() {
	const isAdmin = computed(() => session.user === "Administrator")

	// Enabled services visible to the current user (same rules as before).
	const services = computed(() => {
		const user = session.user
		const admin = user === "Administrator"
		const base = (cards.value || [])
			.filter((c) => {
				if (!c.enabled || !serviceMeta[c.id]) return false
				if (admin) return true
				const allowed = Array.isArray(c.users) ? c.users : []
				if (allowed.length) return allowed.includes(user)
				return true
			})
			.map((c) => ({ ...c, ...serviceMeta[c.id] }))

		// Expand Decision Center into a dedicated sidebar group.
		const dcIndex = base.findIndex((s) => s.id === "decision_center")
		if (dcIndex >= 0) {
			const parent = base[dcIndex]
			const dcUsers = Array.isArray(parent.users) ? parent.users : []
			const expanded = [
				{
					...parent,
					id: "decision_center_overview",
					label: __("التحليلات"),
					route: "DecisionCenter",
					type: "route",
					users: dcUsers,
					...serviceMeta.decision_center_overview,
				},
				...DECISION_CENTER_CHILDREN.map((c) => ({ ...c, users: dcUsers })),
			]
			base.splice(dcIndex, 1, ...expanded)
		}

		return base
	})

	const adminServices = computed(() => {
		if (!isAdmin.value) return []
		return [
			{
				id: SETTINGS_ID,
				label: __("إعدادات الصفحة الرئيسية"),
				route: "Settings",
				type: "route",
				...serviceMeta[SETTINGS_ID],
			},
		]
	})

	const allServices = computed(() => [...services.value, ...adminServices.value])

	// Services grouped for the sidebar, keeping the configured order within each group.
	const navGroups = computed(() => {
		const groups = NAV_GROUPS.map((g) => ({
			...g,
			title: __(g.title),
			items: services.value.filter((s) => s.group === g.id),
		}))
		if (adminServices.value.length) {
			groups.push({ ...ADMIN_GROUP, title: __(ADMIN_GROUP.title), items: adminServices.value })
		}
		return groups.filter((g) => g.items.length)
	})

	async function loadServices(force = false) {
		if (loading.value || (loaded.value && !force)) return
		loading.value = true
		loadError.value = ""
		try {
			const result = await call("bs.baron_servies.api.utilities.get_bs_home_settings")
			cards.value = (result?.cards || []).map((c) => ({
				...c,
				enabled: !!c.enabled,
				users: Array.isArray(c.users) ? c.users : [],
			}))
			loaded.value = true
		} catch (e) {
			loadError.value = e?.message || __("فشل تحميل الإعدادات")
		} finally {
			loading.value = false
		}
	}

	return { loaded, loading, loadError, services, allServices, navGroups, isAdmin, loadServices }
}
