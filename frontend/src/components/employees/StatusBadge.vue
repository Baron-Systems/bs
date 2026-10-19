<template>
	<span
		v-if="entry"
		class="inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset"
		:class="entry.cls"
	>
		{{ __(entry.label) }}
	</span>
	<span v-else class="text-xs text-slate-400">—</span>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
	status: { type: String, default: "" },
	map: { type: Object, required: true },
})

const entry = computed(() => (props.status ? props.map[props.status] : null))
</script>
