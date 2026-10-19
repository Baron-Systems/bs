<template>
<div class="flex flex-col sm:flex-row items-center gap-5">
	<div class="relative w-44 h-44 flex-shrink-0">
		<Doughnut :data="chartData" :options="options" />
		<div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
			<span class="text-[10px] font-semibold text-slate-400">{{ centerLabel }}</span>
			<span class="text-[15px] font-extrabold text-slate-900 tracking-tight">{{ format(total) }}</span>
		</div>
	</div>
	<ul class="flex-1 w-full flex flex-col gap-2.5 min-w-0">
		<li v-for="(s, i) in segments" :key="s.label" class="flex items-center gap-2.5 text-[12px] min-w-0">
			<span class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: s.color }"></span>
			<span class="flex-1 text-slate-600 truncate" :title="s.label">{{ s.label }}</span>
			<span class="font-bold text-slate-900 tabular-nums">{{ format(s.value) }}</span>
			<span class="w-12 text-end text-[11px] text-slate-400 tabular-nums">{{ s.pct.toFixed(1) }}%</span>
		</li>
	</ul>
</div>
</template>

<script setup>
import { computed } from "vue"
import { Doughnut } from "vue-chartjs"
import { SERIES, OTHER, tooltip } from "./vizTheme"

const props = defineProps({
	rows: { type: Array, default: () => [] }, // [{label, value, color?}]
	format: { type: Function, default: (v) => v },
	centerLabel: { type: String, default: "" },
	maxSegments: { type: Number, default: 6 },
	colors: { type: Array, default: null },
})

const segments = computed(() => {
	let list = props.rows.filter((r) => Number(r.value || 0) > 0)
	if (list.length > props.maxSegments) {
		const head = list.slice(0, props.maxSegments - 1)
		const rest = list.slice(props.maxSegments - 1).reduce((a, r) => a + Number(r.value), 0)
		list = [...head, { label: __("أخرى"), value: rest, isOther: true }]
	}
	const total = list.reduce((a, r) => a + Number(r.value), 0) || 1
	const palette = props.colors || SERIES
	return list.map((r, i) => ({
		...r,
		value: Number(r.value),
		color: r.color || (r.isOther ? OTHER : palette[i % palette.length]),
		pct: (Number(r.value) / total) * 100,
	}))
})

const total = computed(() => segments.value.reduce((a, s) => a + s.value, 0))

const chartData = computed(() => ({
	labels: segments.value.map((s) => s.label),
	datasets: [{
		data: segments.value.map((s) => s.value),
		backgroundColor: segments.value.map((s) => s.color),
		borderColor: "#ffffff",
		borderWidth: 2,
		hoverOffset: 4,
	}],
}))

const options = {
	responsive: true,
	maintainAspectRatio: false,
	cutout: "72%",
	plugins: {
		legend: { display: false },
		tooltip: tooltip({
			callbacks: {
				label: (ctx) => ` ${ctx.label}: ${props.format(ctx.parsed)}`,
			},
		}),
	},
}
</script>
