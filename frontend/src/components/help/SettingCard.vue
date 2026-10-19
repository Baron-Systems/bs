<template>
  <HelpCard :anchor="setting.key" accent="slate">
    <div class="space-y-3">
      <div class="flex items-start justify-between gap-2 flex-wrap">
        <div class="min-w-0">
          <h4 class="text-sm font-bold text-slate-900">{{ setting.label }}</h4>
          <p class="text-[11px] text-slate-500 mt-0.5">{{ sectionLabel }}</p>
        </div>
        <div class="flex items-center gap-1.5 flex-shrink-0 flex-wrap">
          <span class="px-2 py-0.5 rounded-lg text-[11px] font-medium bg-slate-100 text-slate-600">
            {{ __('الافتراضي:') }} {{ setting.default }}{{ setting.unit && setting.unit !== '×' ? ' ' + setting.unit : '' }}
          </span>
          <span
            v-if="current !== undefined && current !== null"
            class="px-2 py-0.5 rounded-lg text-[11px] font-semibold bg-indigo-50 text-indigo-700"
          >
            {{ __('الحالية:') }} {{ current }}{{ setting.unit && setting.unit !== '×' ? ' ' + setting.unit : '' }}
          </span>
        </div>
      </div>

      <p class="text-xs text-slate-600 leading-relaxed">{{ setting.meaning }}</p>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <div class="rounded-lg bg-emerald-50/60 border border-emerald-100 px-3 py-2">
          <p class="text-[11px] font-semibold text-emerald-700 mb-0.5">{{ __('إذا زدته ↑') }}</p>
          <p class="text-[11px] text-slate-600 leading-snug">{{ setting.raiseEffect }}</p>
        </div>
        <div class="rounded-lg bg-amber-50/60 border border-amber-100 px-3 py-2">
          <p class="text-[11px] font-semibold text-amber-700 mb-0.5">{{ __('إذا نقصته ↓') }}</p>
          <p class="text-[11px] text-slate-600 leading-snug">{{ setting.lowerEffect }}</p>
        </div>
      </div>

      <div class="rounded-lg bg-blue-50/70 border border-blue-100 px-3 py-2">
        <p class="text-[11px] font-semibold text-blue-700 mb-0.5">{{ __('مثال عملي') }}</p>
        <p class="text-[11px] text-slate-600 leading-snug">{{ setting.example }}</p>
      </div>

      <p v-if="setting.extraNote" class="text-[11px] text-slate-500 leading-snug">
        <span class="font-medium text-slate-600">{{ __('ملاحظة:') }}</span> {{ setting.extraNote }}
      </p>

      <div class="flex items-center justify-between gap-2 flex-wrap">
        <div v-if="ruleLabels.length" class="flex items-center gap-1.5 flex-wrap">
          <span class="text-[11px] font-semibold text-slate-500">{{ __('يؤثر في:') }}</span>
          <button
            v-for="r in ruleLabels"
            :key="r.id"
            type="button"
            class="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600 hover:bg-indigo-50 hover:text-indigo-700 transition-colors"
            @click="$emit('open-rule', r.id)"
          >
            {{ r.label }}
          </button>
        </div>
        <RouterLink
          :to="{ name: 'DecisionCenterSettings' }"
          class="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800"
        >
          {{ __('عرض في الإعدادات') }}
          <svg class="h-3 w-3 rtl:-scale-x-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </RouterLink>
      </div>
    </div>
  </HelpCard>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import HelpCard from './HelpCard.vue'
import { SETTINGS_SECTIONS, RULES_HELP } from '@/data/help'

const props = defineProps({
  setting: { type: Object, required: true },
  current: { type: [Number, String], default: undefined },
})
defineEmits(['open-rule'])

const sectionLabel = computed(() =>
  SETTINGS_SECTIONS.find((s) => s.id === props.setting.section)?.label || ''
)

const ruleLabels = computed(() =>
  (props.setting.affectsRules || [])
    .map((id) => ({ id, label: RULES_HELP.find((r) => r.id === id)?.title || id }))
)
</script>
