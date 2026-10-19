<template>
<header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
	<div class="min-w-0">
		<p v-if="eyebrow" class="text-[11px] font-semibold tracking-wide text-blue-600">{{ eyebrow }}</p>
		<h1 class="mt-1 truncate text-2xl font-extrabold tracking-tight text-slate-900">{{ title }}</h1>
		<p v-if="subtitle || $slots.meta" class="mt-1 text-xs text-slate-500">
			{{ subtitle }}<slot name="meta" />
		</p>
	</div>
	<div v-if="$slots.actions" class="flex flex-wrap items-center gap-2">
		<slot name="actions" />
	</div>
</header>
</template>

<script setup>
defineProps({
	title: { type: String, required: true },
	subtitle: { type: String, default: "" },
	eyebrow: { type: String, default: "" },
})
</script>
