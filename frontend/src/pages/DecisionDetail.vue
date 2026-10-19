<template>
<div class="w-full">
<main class="flex flex-col gap-4 max-w-3xl">
	<!-- Back button -->
	<router-link
		:to="{ name: 'DecisionCenter', query: backQuery }"
		class="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
	>
		<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
		</svg>
		{{ __("العودة لمركز القرار") }}
	</router-link>

	<!-- Loading -->
	<div v-if="loading" class="flex items-center justify-center py-16">
		<svg class="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
			<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
		</svg>
	</div>

	<!-- Error -->
	<div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
		<p class="text-sm text-red-700">{{ error }}</p>
	</div>

	<!-- Decision detail -->
	<template v-else-if="decision">
		<!-- Header -->
		<div class="bg-white rounded-xl border shadow-sm p-5" :class="borderClass">
			<div class="flex items-center gap-2 flex-wrap mb-3">
				<span class="px-2.5 py-1 rounded-full text-xs font-bold" :class="priorityBadge">{{ priorityLabel }}</span>
				<span class="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">{{ categoryLabel }}</span>
				<span class="text-xs text-slate-400">{{ __("النتيجة") }}: {{ decision.score }}</span>
			</div>
			<h1 class="text-lg font-bold text-slate-900 mb-1">{{ decision.title }}</h1>
			<p class="text-sm text-slate-600 leading-relaxed">{{ decision.summary }}</p>
		</div>

		<!-- ما الذي حدث؟ — الأدلة -->
		<div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
			<h2 class="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
				<svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
				</svg>
				{{ __("الأدلة") }}
			</h2>
			<div v-if="decision.evidence && decision.evidence.length" class="space-y-2">
				<div v-for="(ev, i) in decision.evidence" :key="i" class="flex items-center gap-3 p-2 rounded-lg bg-slate-50">
					<div class="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
						<span class="text-[10px] font-bold text-blue-700">{{ i + 1 }}</span>
					</div>
					<div class="min-w-0">
						<span class="text-xs font-semibold text-slate-700">{{ ev.label }}</span>
						<span class="text-xs text-slate-500 mr-1">{{ ev.value }}</span>
					</div>
				</div>
			</div>
			<p v-else class="text-xs text-slate-400">{{ __("لا توجد أدلة") }}</p>
		</div>

		<!-- القاعدة المطبقة -->
		<div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
			<h2 class="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
				<svg class="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0" />
				</svg>
				{{ __("القاعدة المطبقة") }}
			</h2>
			<div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
				<div class="bg-slate-50 rounded-lg p-3">
					<p class="text-[10px] text-slate-500 mb-0.5">{{ __("معرف القاعدة") }}
						<HelpLink v-if="decision.rule_id" tab="rules" :section="decision.rule_id" />
					</p>
					<p class="text-xs font-mono font-semibold text-slate-800">{{ decision.rule_id }}</p>
				</div>
				<div class="bg-slate-50 rounded-lg p-3">
					<p class="text-[10px] text-slate-500 mb-0.5">{{ __("النتيجة") }}</p>
					<p class="text-xs font-bold text-slate-800">{{ decision.score }} / 100</p>
				</div>
				<div class="bg-slate-50 rounded-lg p-3">
					<p class="text-[10px] text-slate-500 mb-0.5">{{ __("التأثير المالي") }}</p>
					<p class="text-xs font-semibold text-slate-800">{{ fmtCurrency(decision.impact_value) }}</p>
				</div>
			</div>
		</div>

		<!-- المتأثرون -->
		<div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
			<h2 class="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
				<svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
				</svg>
				{{ __("المتأثرون") }}
			</h2>

			<!-- Rich table from extra data -->
			<template v-if="extraItems.length">
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="bg-slate-50 text-slate-600">
								<th v-for="col in extraItemCols" :key="col.key" class="px-3 py-2 text-xs font-semibold text-right">{{ col.label }}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-100">
							<tr v-for="(item, i) in extraItems" :key="i" class="hover:bg-slate-50">
								<td v-for="col in extraItemCols" :key="col.key" class="px-3 py-2 text-right text-xs">
									<template v-if="col.format === 'currency'">{{ fmtCurrency(item[col.key]) }}</template>
									<template v-else-if="col.format === 'number'">{{ fmtNumber(item[col.key]) }}</template>
									<template v-else-if="col.format === 'pct'">{{ fmtPct(item[col.key]) }}</template>
									<template v-else>{{ item[col.key] ?? "—" }}</template>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>

			<!-- Fallback: plain entity IDs -->
			<template v-else-if="decision.entity_ids && decision.entity_ids.length">
				<div class="flex flex-wrap gap-2">
					<span
						v-for="eid in decision.entity_ids"
						:key="eid"
						class="px-2 py-1 bg-slate-100 text-xs text-slate-700 rounded-lg font-mono"
					>{{ eid }}</span>
				</div>
			</template>

			<p v-else class="text-xs text-slate-400">{{ __("لا توجد كيانات متأثرة") }}</p>
		</div>

		<!-- الإجراء المقترح -->
		<div class="bg-blue-50 rounded-xl border border-blue-200 shadow-sm p-5">
			<h2 class="text-sm font-bold text-blue-800 mb-2 flex items-center gap-2">
				<svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
				</svg>
				{{ __("الإجراء المقترح") }}
			</h2>
			<p class="text-sm text-blue-900 leading-relaxed">{{ decision.recommendation }}</p>
			<a
				v-if="decision.action_route && isExternalRoute(decision.action_route)"
				:href="decision.action_route"
				class="inline-flex items-center gap-1 mt-3 text-xs font-semibold text-blue-700 hover:text-blue-900 transition-colors"
			>
				{{ __("انتقل إلى الإجراء") }}
				<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
				</svg>
			</a>
		</div>
	</template>
</main>
</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue"
import { useRoute } from "vue-router"
import { call } from "@/utils/apiWrapper"
import HelpLink from "@/components/HelpLink.vue"

const route = useRoute()

const loading = ref(false)
const error = ref("")
const decision = ref(null)
const apiCurrency = ref("")

// ── Query context ──
const backQuery = computed(() => {
	const q = {}
	if (route.query.company) q.company = route.query.company
	if (route.query.period) q.period = route.query.period
	if (route.query.from_date) q.from_date = route.query.from_date
	if (route.query.to_date) q.to_date = route.query.to_date
	return q
})

// ── Priority/category display ──
const PRIORITY_MAP = {
	urgent: { label: "عاجل", badge: "bg-red-100 text-red-700", border: "border-red-200" },
	important: { label: "مهم", badge: "bg-amber-100 text-amber-700", border: "border-amber-200" },
	review: { label: "مراجعة", badge: "bg-blue-100 text-blue-700", border: "border-slate-200" },
	opportunity: { label: "فرصة", badge: "bg-emerald-100 text-emerald-700", border: "border-emerald-200" },
}
const CATEGORY_MAP = {
	inventory: "المخزون",
	sales: "المبيعات",
	purchases: "المشتريات",
	customers: "العملاء",
}

const priorityInfo = computed(() => PRIORITY_MAP[decision.value?.priority] || PRIORITY_MAP.review)
const priorityLabel = computed(() => __(priorityInfo.value.label))
const priorityBadge = computed(() => priorityInfo.value.badge)
const borderClass = computed(() => priorityInfo.value.border)
const categoryLabel = computed(() => __(CATEGORY_MAP[decision.value?.category] || decision.value?.category || ""))

// ── Extra data: items or customers from detail API ──
const extraItems = computed(() => {
	if (!decision.value?.extra) return []
	// Items (inventory/sales/purchases rules)
	if (Array.isArray(decision.value.extra.items)) return decision.value.extra.items
	// Customers (customer rules)
	if (Array.isArray(decision.value.extra.customers)) return decision.value.extra.customers
	return []
})

const extraItemCols = computed(() => {
	if (!extraItems.value.length) return []
	const sample = extraItems.value[0]
	const cols = []
	// Build columns dynamically from first item's keys
	const KNOWN_COLS = {
		item_code: { label: __("كود الصنف") },
		item_name: { label: __("الصنف") },
		customer: { label: __("العميل") },
		customer_name: { label: __("العميل") },
		actual_qty: { label: __("الكمية"), format: "number" },
		stock_value: { label: __("القيمة"), format: "currency" },
		days_of_stock: { label: __("أيام التغطية"), format: "number" },
		avg_daily_sales: { label: __("متوسط البيع"), format: "number" },
		prev_qty: { label: __("الكمية السابقة"), format: "number" },
		current_qty: { label: __("الكمية الحالية"), format: "number" },
		prev_total: { label: __("السابق"), format: "currency" },
		current_total: { label: __("الحالي"), format: "currency" },
		change_pct: { label: __("التغير %"), format: "pct" },
		net_qty: { label: __("الكمية"), format: "number" },
		net_amount: { label: __("المبلغ"), format: "currency" },
		prev_rate: { label: __("السعر السابق"), format: "currency" },
		current_rate: { label: __("السعر الحالي"), format: "currency" },
		increase_pct: { label: __("الزيادة %"), format: "pct" },
		last_purchase: { label: __("آخر شراء") },
		avg_gap_days: { label: __("متوسط الفاصل"), format: "number" },
	}
	for (const key of Object.keys(sample)) {
		if (key === "extra" || key === "id") continue
		const known = KNOWN_COLS[key]
		if (known) {
			cols.push({ key, label: known.label, format: known.format || "" })
		}
	}
	return cols
})

// ── Route detection: Frappe Desk vs Vue ──
function isExternalRoute(route) {
	if (!route) return false
	return route.startsWith("/app/") || route.startsWith("http") || route.startsWith("/api/")
}

// ── Currency formatting ──
function fmtCurrency(value) {
	const n = Number(value || 0)
	const cur = apiCurrency.value
	if (cur) {
		try {
			return new Intl.NumberFormat("en-US", { style: "currency", currency: cur, minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(n)
		} catch (e) { /* fallback */ }
	}
	return n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function fmtNumber(value) {
	if (value === null || value === undefined) return "—"
	return Number(value).toLocaleString("en-US", { maximumFractionDigits: 2 })
}

function fmtPct(value) {
	if (value === null || value === undefined) return "—"
	const n = Number(value)
	if (isNaN(n)) return "—"
	const sign = n > 0 ? "+" : ""
	return `${sign}${n.toFixed(1)}%`
}

// ── Fetch decision ──
async function fetchDecision() {
	const id = route.params.decisionId
	if (!id) return
	loading.value = true
	error.value = ""
	try {
		const params = {
			decision_id: id,
			company: route.query.company || undefined,
			period: route.query.period || undefined,
		}
		if (route.query.from_date) params.from_date = route.query.from_date
		if (route.query.to_date) params.to_date = route.query.to_date
		const result = await call("bs.baron_servies.api.decision_center.api.get_decision_detail", params)
		decision.value = result?.decision || null
		apiCurrency.value = result?.currency || ""
	} catch (e) {
		error.value = e?.message || __("فشل تحميل تفاصيل القرار")
	} finally {
		loading.value = false
	}
}

onMounted(fetchDecision)

// Refetch if decision ID changes
watch(() => route.params.decisionId, fetchDecision)
</script>
