<template>
  <div
    class="rounded-xl border px-4 py-3 flex items-start gap-3"
    :class="tone === 'info'
      ? 'bg-blue-50 border-blue-200 text-blue-800'
      : 'bg-amber-50 border-amber-200 text-amber-800'"
  >
    <svg class="h-4 w-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <div class="text-xs leading-relaxed">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  tone: { type: String, default: 'amber' }, // 'amber' | 'info'
})
</script>
