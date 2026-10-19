<template>
<ul class="flex flex-col divide-y divide-slate-100">
	<li v-for="(row, i) in rows" :key="i" class="py-2.5 first:pt-0 last:pb-0 flex items-center gap-3 min-w-0">
		<span
			class="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center"
			:class="Number(row.change) >= 0 ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'"
			:aria-label="Number(row.change) >= 0 ? __('نمو') : __('تراجع')"
		>
			<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
				<path v-if="Number(row.change) >= 0" stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
				<path v-else stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
			</svg>
		</span>
		<div class="flex-1 min-w-0">
			<p class="text-[12px] font-medium text-slate-700 truncate" :title="row.name">{{ row.name }}</p>
			<p class="text-[11px] text-slate-400 tabular-nums truncate">
				{{ format(row.previous) }} ← {{ format(row.current) }}
			</p>
		</div>
		<span
			class="flex-shrink-0 text-[12px] font-bold tabular-nums"
			:class="Number(row.change) >= 0 ? 'text-emerald-700' : 'text-rose-700'"
		>{{ Number(row.change) >= 0 ? "+" : "−" }}{{ format(Math.abs(Number(row.change))) }}</span>
	</li>
</ul>
</template>

<script setup>
defineProps({
	rows: { type: Array, default: () => [] },
	format: { type: Function, default: (v) => v },
})
</script>
