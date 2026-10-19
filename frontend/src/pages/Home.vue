<template>
<div class="flex items-center justify-center py-24">
<div v-if="!loaded" class="flex flex-col items-center gap-3">
<svg class="animate-spin h-10 w-10 text-blue-600" fill="none" viewBox="0 0 24 24">
<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>
<p class="text-slate-500 text-sm">{{ __("جاري تحميل الخدمات...") }}</p>
</div>
<div v-else-if="!services.length" class="text-center">
<svg class="w-14 h-14 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
<p class="text-slate-600 font-medium">{{ __("لا توجد خدمات متاحة لك حالياً") }}</p>
</div>
</div>
</template>

<script setup>
import { useServices } from "@/data/services"
import router from "@/router"
import { onMounted, watchEffect } from "vue"

const { loaded, services, loadServices } = useServices()

onMounted(() => {
	loadServices()
})

// "/" is the entry point of the shell — go straight to the first available service.
watchEffect(() => {
	if (!loaded.value) return
	const target = services.value.find((s) => s.type === "route")
	if (target) {
		router.replace({ name: target.route })
	}
})
</script>
