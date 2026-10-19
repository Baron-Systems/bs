<template>
<ol class="flex flex-col gap-3">
	<li v-for="(row, i) in rows" :key="i" class="min-w-0">
		<div class="flex items-baseline justify-between gap-3 text-[12px]">
			<span class="flex items-center gap-2 min-w-0">
				<span class="w-5 text-[11px] font-bold text-slate-400 tabular-nums flex-shrink-0">{{ i + 1 }}</span>
				<span class="font-medium text-slate-700 truncate" :title="row[labelKey]">{{ row[labelKey] }}</span>
			</span>
			<span class="flex items-baseline gap-2 flex-shrink-0">
				<span v-if="secondaryKey && row[secondaryKey] !== undefined" class="text-[11px] text-slate-400 tabular-nums">{{ secondaryFormat(row[secondaryKey]) }}</span>
				<span class="font-bold text-slate-900 tabular-nums">{{ format(row[valueKey]) }}</span>
			</span>
		</div>
		<div class="mt-1.5 ms-7 h-1.5 rounded-full bg-slate-100 overflow-hidden">
			<div class="h-full rounded-full transition-[width] duration-500" :style="{ width: pct(row[valueKey]) + '%', backgroundColor: color }"></div>
		</div>
	</li>
</ol>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
	rows: { type: Array, default: () => [] },
	labelKey: { type: String, default: "name" },
	valueKey: { type: String, default: "amount" },
	secondaryKey: { type: String, default: "" },
	format: { type: Function, default: (v) => v },
	secondaryFormat: { type: Function, default: (v) => v },
	color: { type: String, default: "#2a78d6" },
})

const max = computed(() => Math.max(...props.rows.map((r) => Math.abs(Number(r[props.valueKey] || 0))), 1))
const pct = (v) => Math.max(2, (Math.abs(Number(v || 0)) / max.value) * 100)
</script>
