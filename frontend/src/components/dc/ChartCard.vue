<template>
<section class="bg-white rounded-2xl border border-slate-200/80 shadow-[0_1px_2px_rgba(15,23,42,0.04)] p-4 sm:p-5 flex flex-col min-w-0">
	<header class="flex items-start justify-between gap-3 mb-4">
		<div class="min-w-0">
			<h3 class="text-[14px] font-bold text-slate-800 truncate">{{ title }}</h3>
			<p v-if="subtitle" class="text-[11px] text-slate-400 mt-0.5 truncate">{{ subtitle }}</p>
		</div>
		<div class="flex-shrink-0"><slot name="actions" /></div>
	</header>
	<div v-if="empty" class="flex-1 flex flex-col items-center justify-center gap-2 text-slate-400" :style="{ minHeight: height + 'px' }">
		<svg class="w-8 h-8 text-slate-300" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" d="M3 3v18h18M7 15l3-3 3 3 5-6" />
		</svg>
		<span class="text-xs">{{ __("لا توجد بيانات للفترة المحددة") }}</span>
	</div>
	<div v-else-if="fluid" class="flex-1 min-w-0"><slot /></div>
	<div v-else class="relative w-full" :style="{ height: height + 'px' }">
		<slot />
	</div>
</section>
</template>

<script setup>
defineProps({
	title: { type: String, required: true },
	subtitle: { type: String, default: "" },
	height: { type: Number, default: 260 },
	empty: { type: Boolean, default: false },
	// Content sizes itself (lists, legends) instead of a fixed canvas height
	fluid: { type: Boolean, default: false },
})
</script>
