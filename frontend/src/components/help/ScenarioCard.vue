<template>
  <HelpCard :anchor="scenario.id" accent="emerald">
    <div class="space-y-3">
      <div class="flex items-center gap-3">
        <div class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-700 text-white shadow-sm">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="scenario.icon" />
          </svg>
        </div>
        <div class="min-w-0">
          <h4 class="text-sm font-bold text-slate-900">{{ scenario.title }}</h4>
          <p class="text-[11px] text-slate-500">{{ __('متى تستخدمه:') }} {{ scenario.trigger }}</p>
        </div>
      </div>

      <ol class="space-y-2">
        <li v-for="(step, i) in scenario.steps" :key="i" class="flex items-start gap-2.5">
          <span class="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-bold mt-0.5">
            {{ i + 1 }}
          </span>
          <div class="flex-1 min-w-0">
            <RouterLink
              v-if="step.route"
              :to="{ path: step.route, query: step.query || {} }"
              class="text-xs text-slate-700 leading-snug hover:text-indigo-700 hover:underline underline-offset-2 decoration-indigo-300"
            >{{ step.label }}</RouterLink>
            <p v-else class="text-xs text-slate-700 leading-snug">{{ step.label }}</p>
          </div>
        </li>
      </ol>

      <button
        v-if="scenario.helpRef"
        type="button"
        class="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800"
        @click="$emit('open-help', scenario.helpRef)"
      >
        {{ __('القاعدة المرتبطة: اذهب لشرحها') }}
        <svg class="h-3 w-3 rtl:-scale-x-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
      </button>
    </div>
  </HelpCard>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import HelpCard from './HelpCard.vue'

defineProps({
  scenario: { type: Object, required: true },
})
defineEmits(['open-help'])
</script>
