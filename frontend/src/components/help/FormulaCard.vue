<template>
  <HelpCard :title="card.title" :anchor="card.key" icon="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" accent="blue">
    <div class="space-y-3">
      <div class="flex items-center justify-center gap-1.5 flex-wrap rounded-xl bg-slate-50 border border-slate-200 px-3 py-3">
        <span
          v-for="(part, i) in card.formula"
          :key="i"
          class="px-2 py-1 rounded-md text-xs font-bold"
          :class="isOperator(part) ? 'bg-indigo-100 text-indigo-700' : 'bg-white border border-slate-200 text-slate-800'"
        >
          {{ part }}
        </span>
      </div>

      <div class="rounded-lg bg-blue-50/70 border border-blue-100 px-3 py-2">
        <p class="text-[11px] font-semibold text-blue-700 mb-0.5">{{ __('مثال') }}</p>
        <p class="text-[11px] text-slate-600 leading-snug">{{ card.example }}</p>
      </div>

      <p class="text-xs text-slate-600 leading-relaxed">{{ card.explanation }}</p>

      <details v-if="card.techDetails" class="rounded-lg border border-slate-200 bg-slate-50/50 px-3 py-2">
        <summary class="text-[11px] font-semibold text-slate-500 cursor-pointer select-none">
          {{ __('تفاصيل تقنية') }}
        </summary>
        <p class="text-[11px] text-slate-500 leading-relaxed mt-1.5">{{ card.techDetails }}</p>
      </details>
    </div>
  </HelpCard>
</template>

<script setup>
import HelpCard from './HelpCard.vue'

const props = defineProps({
  card: { type: Object, required: true },
})

function isOperator(part) {
  return ['÷', '×', '+', '−', '=', '≤', '≥'].includes(part)
}
</script>
