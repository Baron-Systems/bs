<template>
  <div class="flex flex-col sm:flex-row sm:items-stretch gap-2">
    <template v-for="(step, i) in steps" :key="i">
      <div
        class="flex-1 rounded-xl border px-3 py-2.5 text-center flex flex-col items-center justify-center gap-1"
        :class="stepStyle(step)"
      >
        <span v-if="step.icon" class="text-lg leading-none" v-text="step.icon" />
        <span class="text-xs font-semibold leading-snug" v-text="step.label" />
        <span v-if="step.caption" class="text-[10px] opacity-75 leading-snug" v-text="step.caption" />
      </div>
      <div v-if="i < steps.length - 1" class="flex items-center justify-center text-slate-400 flex-shrink-0">
        <svg class="h-4 w-4 sm:-rotate-0 rotate-90 rtl:rotate-180 sm:rtl:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
  steps: { type: Array, required: true }, // {icon?, label, caption?, tone?: 'default'|'success'|'warn'|'danger'|'info'}
})

const TONES = {
  default: 'bg-slate-50 border-slate-200 text-slate-700',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
  success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
  warn: 'bg-amber-50 border-amber-200 text-amber-800',
  danger: 'bg-rose-50 border-rose-200 text-rose-800',
  muted: 'bg-white border-dashed border-slate-300 text-slate-500',
}

function stepStyle(step) {
  return TONES[step.tone || 'default']
}
</script>
