<template>
<div
	class="bg-white rounded-xl border shadow-sm p-4 flex flex-col gap-2 transition-colors hover:border-blue-200"
	:class="borderClass"
>
	<!-- Header row: priority badge + category -->
	<div class="flex items-center gap-2 flex-wrap">
		<span
			v-if="decision.related_to_current_plan"
			class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100"
		>
			{{ __("مرتبط بالخطة") }}
		</span>
		<span
			class="px-2 py-0.5 rounded-full text-[10px] font-bold"
			:class="priorityBadge"
		>{{ priorityLabel }}</span>
		<span class="text-[10px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">{{ categoryLabel }}</span>
		<span v-if="decision.score" class="text-[10px] text-slate-400 mr-auto">{{ decision.score }}</span>
	</div>

	<!-- Title -->
	<h4 class="text-sm font-bold text-slate-900 leading-snug line-clamp-2">{{ decision.title }}</h4>

	<!-- Summary -->
	<p class="text-xs text-slate-600 leading-relaxed line-clamp-2">{{ decision.summary }}</p>

	<!-- Evidence (top 2) -->
	<div v-if="topEvidence.length" class="flex flex-col gap-0.5">
		<div v-for="(ev, i) in topEvidence" :key="i" class="flex items-center gap-1 text-[11px] text-slate-500">
			<svg class="w-3 h-3 flex-shrink-0 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
			</svg>
			<span class="truncate"><strong>{{ ev.label }}:</strong> {{ ev.value }}</span>
		</div>
	</div>

	<!-- Recommendation -->
	<p v-if="decision.recommendation" class="text-[11px] text-blue-700 bg-blue-50 rounded-lg px-2 py-1 leading-relaxed line-clamp-2">
		{{ decision.recommendation }}
	</p>

	<!-- Action -->
	<div class="flex items-center gap-2 mt-1">
		<router-link
			:to="detailRoute"
			class="text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
		>{{ __("عرض التفاصيل") }} ←</router-link>
	</div>
</div>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
	decision: { type: Object, required: true },
	queryParams: { type: Object, default: () => ({}) },
})

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

const priorityInfo = computed(() => PRIORITY_MAP[props.decision.priority] || PRIORITY_MAP.review)
const priorityLabel = computed(() => __(priorityInfo.value.label))
const priorityBadge = computed(() => priorityInfo.value.badge)
const borderClass = computed(() => priorityInfo.value.border)
const categoryLabel = computed(() => __(CATEGORY_MAP[props.decision.category] || props.decision.category))

const topEvidence = computed(() => {
	const ev = props.decision.evidence
	if (!Array.isArray(ev)) return []
	return ev.slice(0, 2)
})

const detailRoute = computed(() => ({
	name: "DecisionDetail",
	params: { decisionId: props.decision.id },
	query: props.queryParams,
}))
</script>
