<template>
  <HelpCard :anchor="rule.id" accent="slate">
    <div class="space-y-3">
      <div class="flex items-start justify-between gap-2 flex-wrap">
        <div class="min-w-0">
          <h4 class="text-sm font-bold text-slate-900">{{ rule.title }}</h4>
          <p class="text-[11px] text-slate-500 mt-0.5">{{ categoryLabel }} · قاعدة {{ rule.id }}</p>
        </div>
        <div class="flex items-center gap-1.5 flex-shrink-0">
          <StatusChip kind="severity" :value="rule.severity" />
          <span
            v-if="enabled !== null"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold"
            :class="enabled ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'"
          >
            <span class="h-1.5 w-1.5 rounded-full" :class="enabled ? 'bg-emerald-500' : 'bg-slate-400'" />
            {{ enabled ? __('مفعّلة حاليًا') : __('غير مفعّلة حاليًا') }}
          </span>
          <span v-if="rule.simplified" class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-indigo-50 text-indigo-600">
            {{ __('تبسيط للقاعدة') }}
          </span>
        </div>
      </div>

      <HelpFlow :steps="flowSteps" />

      <p class="text-[11px] leading-relaxed text-slate-600 bg-slate-50 rounded-lg px-3 py-2">
        <span class="font-semibold text-slate-700">{{ __('الشروط الكاملة:') }}</span>
        {{ rule.fullNotes }}
      </p>

      <div>
        <p class="text-[11px] font-semibold text-slate-700 mb-1">{{ __('لماذا يهمك؟') }}</p>
        <p class="text-xs text-slate-600 leading-relaxed">{{ rule.whyItMatters }}</p>
      </div>

      <div>
        <p class="text-[11px] font-semibold text-slate-700 mb-1.5">{{ __('إجراءات مقترحة') }}</p>
        <ul class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
          <li v-for="(a, i) in rule.suggestedActions" :key="i" class="flex items-start gap-1.5 text-xs text-slate-600">
            <svg class="h-3.5 w-3.5 mt-0.5 flex-shrink-0 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            <span class="leading-snug">{{ a }}</span>
          </li>
        </ul>
      </div>

      <div v-if="rule.relatedSettings?.length" class="flex items-center gap-1.5 flex-wrap">
        <span class="text-[11px] font-semibold text-slate-500">{{ __('الإعدادات المرتبطة:') }}</span>
        <button
          v-for="sk in rule.relatedSettings"
          :key="sk"
          type="button"
          class="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600 hover:bg-indigo-50 hover:text-indigo-700 transition-colors"
          @click="$emit('open-setting', sk)"
        >
          {{ settingLabel(sk) }}
        </button>
      </div>
    </div>
  </HelpCard>
</template>

<script setup>
import { computed } from 'vue'
import HelpCard from './HelpCard.vue'
import HelpFlow from './HelpFlow.vue'
import StatusChip from './StatusChip.vue'
import { RULE_CATEGORIES, SETTINGS_HELP } from '@/data/help'

const props = defineProps({
  rule: { type: Object, required: true },
  enabled: { type: [Boolean, null], default: null },
})
defineEmits(['open-setting'])

const categoryLabel = computed(() =>
  RULE_CATEGORIES.find((c) => c.id === props.rule.category)?.label || props.rule.category
)

const flowSteps = computed(() => [
  ...props.rule.conditions.map((c) => ({ label: c, tone: 'info' })),
  { label: props.rule.result, tone: 'warn' },
])

function settingLabel(key) {
  return SETTINGS_HELP.find((s) => s.key === key)?.label || key
}
</script>
