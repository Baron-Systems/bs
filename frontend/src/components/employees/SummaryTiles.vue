<template>
	<div class="grid gap-3" :class="gridCls">
		<component
			:is="tile.onClick ? 'button' : 'div'"
			v-for="tile in tiles"
			:key="tile.key || tile.label"
			type="button"
			class="rounded-2xl border bg-white p-3 text-start shadow-sm transition-colors"
			:class="[
				tile.active ? 'border-blue-400 ring-2 ring-blue-100' : 'border-slate-200',
				tile.onClick ? 'hover:border-blue-300 cursor-pointer' : '',
			]"
			@click="tile.onClick && tile.onClick()"
		>
			<p class="truncate text-xs font-medium text-slate-500">{{ tile.label }}</p>
			<p class="mt-1 truncate text-lg font-bold tabular-nums" :class="toneCls(tile.tone)">{{ tile.value }}</p>
			<p v-if="tile.hint" class="truncate text-[11px] text-slate-400">{{ tile.hint }}</p>
		</component>
	</div>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
	tiles: { type: Array, required: true }, // [{label, value, hint?, tone?, active?, onClick?}]
	cols: { type: Number, default: 4 },
})

const gridCls = computed(() => ({
	2: "grid-cols-2",
	3: "grid-cols-2 sm:grid-cols-3",
	4: "grid-cols-2 sm:grid-cols-4",
	5: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-5",
	6: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-6",
}[props.cols] || "grid-cols-2 sm:grid-cols-4"))

function toneCls(tone) {
	return {
		green: "text-emerald-600",
		red: "text-red-600",
		amber: "text-amber-600",
		blue: "text-blue-600",
		sky: "text-sky-600",
		slate: "text-slate-500",
	}[tone] || "text-slate-900"
}
</script>
