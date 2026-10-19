<template>
<div class="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
	<div class="flex items-center gap-2 mb-2">
		<div
			class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
			:class="iconBg"
		>
			<svg class="w-4 h-4" :class="iconColor" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="icon" />
			</svg>
		</div>
		<p class="text-xs font-semibold text-slate-600 truncate">{{ label }}</p>
	</div>
	<p class="text-lg font-bold text-slate-900 truncate">{{ formattedValue }}</p>
	<div v-if="!snapshot && changePct !== null && changePct !== undefined && changePct !== ''" class="flex items-center gap-1 mt-1">
		<span class="text-xs font-semibold" :class="changeColor">
			{{ changeDirection }}{{ Math.abs(Number(changePct)).toFixed(1) }}%
		</span>
		<svg v-if="Number(changePct) > 0" class="w-3 h-3 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11l5-5m0 0l5 5m-5-5v12" />
		</svg>
		<svg v-else-if="Number(changePct) < 0" class="w-3 h-3 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 13l-5 5m0 0l-5-5m5 5V6" />
		</svg>
		<span v-else class="text-xs text-slate-400">—</span>
	</div>
	<div v-else-if="snapshot" class="mt-1">
		<span class="text-[10px] text-slate-400">{{ __("لقطة حالية") }}</span>
	</div>
</div>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
	label: { type: String, required: true },
	value: { type: [Number, String], default: 0 },
	changePct: { type: [Number, String], default: null },
	format: { type: String, default: "number" }, // number | currency | count | pct
	formatFn: { type: Function, default: null },
	icon: { type: String, default: "M4 6h16M4 10h16M4 14h16M4 18h16" },
	iconBg: { type: String, default: "bg-blue-100" },
	iconColor: { type: String, default: "text-blue-600" },
	snapshot: { type: Boolean, default: false },
})

const formattedValue = computed(() => {
	if (props.formatFn) return props.formatFn(props.value)
	if (props.format === "count") return Number(props.value || 0).toLocaleString("en-US")
	if (props.format === "pct") return `${Number(props.value ?? 0).toFixed(1)}%`
	return String(props.value ?? "—")
})

const changeColor = computed(() => {
	const n = Number(props.changePct)
	if (n > 0) return "text-emerald-600"
	if (n < 0) return "text-red-600"
	return "text-slate-400"
})

const changeDirection = computed(() => {
	const n = Number(props.changePct)
	if (n > 0) return "+"
	if (n < 0) return ""
	return ""
})
</script>
