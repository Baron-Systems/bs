<template>
  <span
    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold leading-5"
    :class="chipClass"
  >
    <span v-if="dot" class="h-1.5 w-1.5 rounded-full" :class="dotClass" />
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  kind: { type: String, default: 'default' }, // 'plan-status' | 'health' | 'priority' | 'scheduler' | 'severity' | 'default'
  value: { type: String, required: true },
  dot: { type: Boolean, default: true },
})

const MAPS = {
  'plan-status': {
    Draft: { label: 'مسودة', cls: 'bg-slate-100 text-slate-600', dot: 'bg-slate-400' },
    Scheduled: { label: 'مجدولة', cls: 'bg-blue-50 text-blue-700', dot: 'bg-blue-500' },
    Active: { label: 'نشطة', cls: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
    Completed: { label: 'مكتملة', cls: 'bg-indigo-50 text-indigo-700', dot: 'bg-indigo-500' },
    Cancelled: { label: 'ملغاة', cls: 'bg-slate-100 text-slate-500', dot: 'bg-slate-400' },
  },
  health: {
    on_track: { label: 'على المسار', cls: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
    needs_attention: { label: 'يحتاج انتباه', cls: 'bg-amber-50 text-amber-700', dot: 'bg-amber-500' },
    behind: { label: 'متأخر', cls: 'bg-rose-50 text-rose-700', dot: 'bg-rose-500' },
  },
  priority: {
    urgent: { label: 'عاجل', cls: 'bg-rose-50 text-rose-700', dot: 'bg-rose-500' },
    important: { label: 'مهم', cls: 'bg-amber-50 text-amber-700', dot: 'bg-amber-500' },
    review: { label: 'مراجعة', cls: 'bg-blue-50 text-blue-700', dot: 'bg-blue-500' },
    opportunity: { label: 'فرصة', cls: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
  },
  scheduler: {
    none: { label: 'لا توصية', cls: 'bg-slate-100 text-slate-500', dot: 'bg-slate-400' },
    ready_to_start: { label: 'جاهزة للبدء', cls: 'bg-blue-50 text-blue-700', dot: 'bg-blue-500' },
    ready_to_close: { label: 'جاهزة للإغلاق', cls: 'bg-purple-50 text-purple-700', dot: 'bg-purple-500' },
  },
  severity: {
    high: { label: 'عالية', cls: 'bg-rose-50 text-rose-700', dot: 'bg-rose-500' },
    medium: { label: 'متوسطة', cls: 'bg-amber-50 text-amber-700', dot: 'bg-amber-500' },
    low: { label: 'منخفضة', cls: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
    critical: { label: 'حرجة', cls: 'bg-rose-100 text-rose-800', dot: 'bg-rose-600' },
  },
  default: {},
}

const entry = computed(() => MAPS[props.kind]?.[props.value] || null)
const label = computed(() => entry.value?.label || props.value)
const chipClass = computed(() => entry.value?.cls || 'bg-slate-100 text-slate-600')
const dotClass = computed(() => entry.value?.dot || 'bg-slate-400')
</script>
