<template>
<div class="group relative bg-white rounded-2xl border border-slate-200/80 p-4 sm:p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)] hover:shadow-[0_8px_24px_-12px_rgba(15,23,42,0.18)] transition-shadow overflow-hidden">
	<div class="flex items-center justify-between gap-2">
		<p class="text-[12px] font-semibold text-slate-500 truncate">{{ label }}</p>
		<span v-if="badge" class="text-[10px] font-semibold text-slate-400 bg-slate-100 rounded-full px-2 py-0.5 whitespace-nowrap">{{ badge }}</span>
	</div>

	<p class="mt-2 text-[22px] sm:text-2xl font-extrabold text-slate-900 tracking-tight truncate" :title="value">{{ value }}</p>

	<div class="mt-2 flex items-center gap-2 min-h-[20px]">
		<span
			v-if="hasDelta"
			class="inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[11px] font-bold"
			:class="deltaClass"
		>
			<svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
				<path v-if="Number(delta) >= 0" stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
				<path v-else stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
			</svg>
			{{ Math.abs(Number(delta)).toFixed(1) }}%
		</span>
		<span v-if="hint" class="text-[11px] text-slate-400 truncate">{{ hint }}</span>
	</div>

	<!-- Sparkline -->
	<svg
		v-if="sparkPath"
		class="absolute bottom-0 inset-x-0 w-full h-12 pointer-events-none opacity-80"
		viewBox="0 0 100 30"
		preserveAspectRatio="none"
		aria-hidden="true"
	>
		<defs>
			<linearGradient :id="gradId" x1="0" x2="0" y1="0" y2="1">
				<stop offset="0%" :stop-color="color" stop-opacity="0.18" />
				<stop offset="100%" :stop-color="color" stop-opacity="0" />
			</linearGradient>
		</defs>
		<path :d="sparkPath + ' L100,30 L0,30 Z'" :fill="`url(#${gradId})`" />
		<path :d="sparkPath" fill="none" :stroke="color" stroke-width="1.5" vector-effect="non-scaling-stroke" stroke-linejoin="round" />
	</svg>
	<div v-if="sparkPath" class="h-6"></div>
</div>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
	label: { type: String, required: true },
	value: { type: String, default: "—" },
	delta: { type: [Number, String], default: null },
	// true when an increase is bad (e.g. expenses)
	invert: { type: Boolean, default: false },
	hint: { type: String, default: "" },
	badge: { type: String, default: "" },
	spark: { type: Array, default: () => [] },
	color: { type: String, default: "#2a78d6" },
})

const gradId = `spark-${Math.random().toString(36).slice(2, 9)}`

const hasDelta = computed(() => props.delta !== null && props.delta !== undefined && props.delta !== "" && !isNaN(Number(props.delta)))

const deltaClass = computed(() => {
	const n = Number(props.delta)
	if (n === 0) return "bg-slate-100 text-slate-500"
	const good = props.invert ? n < 0 : n > 0
	return good ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
})

const sparkPath = computed(() => {
	const pts = (props.spark || []).map((v) => Number(v || 0))
	if (pts.length < 2 || pts.every((v) => v === 0)) return ""
	const min = Math.min(...pts)
	const max = Math.max(...pts)
	const span = max - min || 1
	return pts
		.map((v, i) => {
			const x = (i / (pts.length - 1)) * 100
			const y = 28 - ((v - min) / span) * 24
			return `${i ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`
		})
		.join(" ")
})
</script>
