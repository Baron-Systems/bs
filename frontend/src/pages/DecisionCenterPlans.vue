<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6" dir="rtl">
    <!-- Header -->
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-3 min-w-0">
        <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-600 to-teal-700 shadow-lg shadow-emerald-500/25">
          <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        </div>
        <div class="min-w-0">
          <h1 class="text-lg font-bold text-slate-900 truncate">{{ __('الخطط') }}</h1>
          <p class="text-xs text-slate-500 truncate">{{ __('أهداف الإدارة ومؤشرات الأداء والإجراءات') }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button v-if="canManage" variant="solid" size="sm" @click="createPlan">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          {{ __('إنشاء خطة جديدة') }}
        </Button>
        <Button variant="outline" size="sm" @click="refresh">
          {{ __('تحديث') }}
        </Button>
      </div>
    </div>

    <!-- Active plan -->
    <div v-if="activePlan" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-5">
      <div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div class="space-y-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700">
              {{ __('الخطة الحالية') }}
            </span>
            <span class="px-2.5 py-1 rounded-full text-xs font-semibold" :class="statusClass(activePlan.status)">
              {{ statusLabel(activePlan.status) }}
            </span>
            <span v-if="activePlan.target_achieved" class="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              {{ __('تم تحقيق الهدف') }}
            </span>
          </div>
          <h2 class="text-xl font-bold text-slate-900">{{ activePlan.plan_name }}</h2>
          <p v-if="primaryMetricLabel" class="text-sm text-slate-600">
            <span class="text-slate-400">{{ __('الهدف الرئيسي:') }}</span> {{ primaryMetricLabel }}
          </p>
          <div class="flex gap-4 text-sm text-slate-500 flex-wrap">
            <span>{{ activePlan.start_date }} {{ __('إلى') }} {{ activePlan.end_date }}</span>
            <span>{{ __('الأيام المتبقية:') }} {{ daysRemaining(activePlan.end_date) }}</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <Button variant="outline" size="sm" @click="openPlan(activePlan.name)">
            {{ __('عرض التفاصيل') }}
          </Button>
        </div>
      </div>

      <!-- Scheduler banner -->
      <div v-if="activePlan.scheduler_status === 'ready_to_close'" class="bg-amber-50 border border-amber-100 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <p class="text-sm font-medium text-amber-800">{{ __('انتهت مدة الخطة وتحتاج إلى مراجعة وإغلاق') }}</p>
        <Button variant="solid" size="sm" :loading="processing === activePlan.name" @click="completePlan(activePlan.name)">
          {{ __('مراجعة وإكمال الخطة') }}
        </Button>
      </div>

      <!-- Progress cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <ProgressCard :label="outcomeLabel" :value="activePlan.progress?.outcome_progress" />
        <ProgressCard :label="__('تقدم التنفيذ')" :value="activePlan.progress?.execution_progress" color="bg-purple-500" />
        <ProgressCard :label="__('تقدم الوقت')" :value="activePlan.progress?.time_progress" color="bg-slate-500" />
      </div>

      <!-- KPI summary -->
      <div v-if="activePlan.__primaryKpi" class="bg-slate-50 rounded-xl p-4">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
          <div>
            <p class="text-slate-500">{{ __('القيمة الحالية') }}</p>
            <p class="font-semibold text-slate-800">{{ formatValue(activePlan.__primaryKpi.current_value, activePlan.__primaryMeta?.unit) }}</p>
          </div>
          <div>
            <p class="text-slate-500">{{ __('خط الأساس') }}</p>
            <p class="font-semibold text-slate-800">{{ formatValue(activePlan.__primaryKpi.effective_baseline, activePlan.__primaryMeta?.unit) }}</p>
          </div>
          <div>
            <p class="text-slate-500">{{ __('الهدف') }}</p>
            <p class="font-semibold text-slate-800">{{ formatValue(activePlan.__primaryKpi.target_value, activePlan.__primaryMeta?.unit) }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state when no active plan -->
    <div v-else-if="!loading" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-10 text-center space-y-4">
      <div class="mx-auto w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
        <svg class="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
      </div>
      <h2 class="text-lg font-bold text-slate-900">{{ __('لا توجد خطة حالية') }}</h2>
      <p class="text-sm text-slate-500 max-w-md mx-auto">
        {{ __('أنشئ خطة لربط أهداف الإدارة بمؤشرات الأداء والإجراءات وقياس تقدمها بمرور الوقت.') }}
      </p>
      <Button v-if="canManage" variant="solid" size="sm" @click="createPlan">
        {{ __('إنشاء خطة جديدة') }}
      </Button>
    </div>

    <!-- Upcoming -->
    <PlanSection
      v-if="upcomingPlans.length"
      title="الخطط القادمة"
      icon="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
      :plans="upcomingPlans"
      :processing="processing"
      @open="openPlan"
      @activate="activatePlan"
      @complete="completePlan"
      @cancel="cancelPlan"
      @schedule="schedulePlan"
    />

    <!-- Drafts -->
    <PlanSection
      v-if="draftPlans.length"
      title="المسودات"
      icon="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
      :plans="draftPlans"
      :processing="processing"
      @open="openPlan"
      @activate="activatePlan"
      @complete="completePlan"
      @cancel="cancelPlan"
      @schedule="schedulePlan"
    />

    <!-- Previous -->
    <PlanSection
      v-if="previousPlans.length"
      title="الخطط السابقة"
      icon="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      :plans="previousPlans"
      :processing="processing"
      @open="openPlan"
    />

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <svg class="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call } from '@/utils/apiWrapper'
import { useToast } from '@/composables/useToast'
import Button from 'frappe-ui/src/components/Button.vue'

const router = useRouter()
const { showError, showSuccess } = useToast()

const plans = ref([])
const activePlan = ref(null)
const loading = ref(false)
const canManage = ref(false)
const processing = ref('')

const upcomingPlans = computed(() => plans.value.filter((p) => p.status === 'Scheduled'))
const draftPlans = computed(() => plans.value.filter((p) => p.status === 'Draft'))
const previousPlans = computed(() => plans.value.filter((p) => ['Completed', 'Cancelled'].includes(p.status)))

const primaryMetricLabel = computed(() => activePlan.value?.__primaryKpi?.metric_label || activePlan.value?.__primaryKpi?.metric_key || '')
const outcomeLabel = computed(() => {
  const strategy = activePlan.value?.__primaryKpi?.progress_strategy
  if (strategy === 'cumulative_ceiling') return __('وتيرة الاستهلاك')
  if (strategy === 'cumulative_growth') return __('تحقيق النمو التراكمي')
  return __('تحقيق الهدف')
})

function createPlan() {
  router.push({ name: 'DecisionCenterPlanNew' })
}

function openPlan(name) {
  router.push({ name: 'DecisionCenterPlanDetail', params: { planId: name } })
}

function statusLabel(status) {
  const map = { Draft: 'مسودة', Scheduled: 'مجدولة', Active: 'نشطة', Completed: 'مكتملة', Cancelled: 'ملغاة' }
  return map[status] || status
}

function statusClass(status) {
  const map = {
    Draft: 'bg-slate-100 text-slate-700',
    Scheduled: 'bg-blue-100 text-blue-700',
    Active: 'bg-emerald-100 text-emerald-700',
    Completed: 'bg-purple-100 text-purple-700',
    Cancelled: 'bg-rose-100 text-rose-700',
  }
  return map[status] || 'bg-slate-100 text-slate-700'
}

function daysRemaining(endDate) {
  if (!endDate) return '—'
  const end = new Date(endDate)
  const today = new Date()
  const diff = Math.ceil((end - today) / (1000 * 60 * 60 * 24))
  return diff >= 0 ? `${diff} يوم` : __('انتهت')
}

function formatValue(value, unit) {
  if (value === null || value === undefined || value === '') return '—'
  const n = Number(value)
  if (isNaN(n)) return '—'
  if (unit === 'currency') return n.toLocaleString('en-US', { maximumFractionDigits: 2 })
  if (unit === 'percent' || unit === 'pct') return `${n.toFixed(1)}%`
  if (unit === 'days') return `${n.toFixed(0)} يوم`
  return n.toLocaleString('en-US', { maximumFractionDigits: 2 })
}

async function loadPermission() {
  try {
    canManage.value = await call('bs.baron_servies.api.decision_center.plan_api.has_plan_management_permission')
  } catch (e) {
    canManage.value = false
  }
}

async function loadPlans() {
  loading.value = true
  try {
    const res = await call('bs.baron_servies.api.decision_center.plan_api.get_plans', { limit_page_length: 100 })
    plans.value = res.plans || []
  } catch (e) {
    showError(e.message || __('فشل تحميل الخطط'))
  } finally {
    loading.value = false
  }
}

async function loadCurrentPlan() {
  try {
    const res = await call('bs.baron_servies.api.decision_center.plan_api.get_current_plan')
    if (!res?.name) {
      activePlan.value = null
      return
    }
    const detail = await call('bs.baron_servies.api.decision_center.plan_api.get_plan_detail', { plan_name: res.name })
    activePlan.value = detail
    activePlan.value.__primaryKpi = detail.kpis.find((k) => k.is_primary) || null
    try {
      const metaRes = await call('bs.baron_servies.api.decision_center.plan_api.get_plan_reference_options')
      activePlan.value.__primaryMeta = (metaRes.metrics || []).find((m) => m.metric_key === activePlan.value.__primaryKpi?.metric_key) || null
    } catch (e) {
      activePlan.value.__primaryMeta = null
    }
  } catch (e) {
    activePlan.value = null
  }
}

async function refresh() {
  await Promise.all([loadPlans(), loadCurrentPlan()])
}

async function activatePlan(name) {
  processing.value = name
  try {
    await call('bs.baron_servies.api.decision_center.plan_api.activate_plan', { plan_name: name })
    showSuccess(__('تم تفعيل الخطة'))
    await refresh()
  } catch (e) {
    showError(e.message || __('فشل تفعيل الخطة'))
  } finally {
    processing.value = ''
  }
}

async function completePlan(name) {
  processing.value = name
  try {
    await call('bs.baron_servies.api.decision_center.plan_api.complete_plan', { plan_name: name })
    showSuccess(__('تم إكمال الخطة'))
    await refresh()
  } catch (e) {
    showError(e.message || __('فشل إكمال الخطة'))
  } finally {
    processing.value = ''
  }
}

async function cancelPlan(name) {
  if (!confirm(__('هل أنت متأكد من إلغاء الخطة؟'))) return
  processing.value = name
  try {
    await call('bs.baron_servies.api.decision_center.plan_api.cancel_plan', { plan_name: name })
    showSuccess(__('تم إلغاء الخطة'))
    await refresh()
  } catch (e) {
    showError(e.message || __('فشل إلغاء الخطة'))
  } finally {
    processing.value = ''
  }
}

async function schedulePlan(name) {
  processing.value = name
  try {
    await call('bs.baron_servies.api.decision_center.plan_api.schedule_plan', { plan_name: name })
    showSuccess(__('تمت جدولة الخطة'))
    await refresh()
  } catch (e) {
    showError(e.message || __('فشل جدولة الخطة'))
  } finally {
    processing.value = ''
  }
}

onMounted(async () => {
  await loadPermission()
  await refresh()
})
</script>

<script>
import { defineComponent, h, computed } from 'vue'

const ProgressCard = defineComponent({
  props: ['label', 'value', 'color'],
  setup(props) {
    const pct = computed(() => {
      if (props.value === null || props.value === undefined || props.value === '') return 0
      const n = Number(props.value)
      return isNaN(n) ? 0 : Math.min(100, Math.max(0, n))
    })
    const text = computed(() => {
      if (props.value === null || props.value === undefined || props.value === '') return '—'
      const n = Number(props.value)
      if (isNaN(n)) return '—'
      return `${n.toFixed(1)}%`
    })
    const barColor = computed(() => {
      const n = Number(props.value)
      if (props.color) return props.color
      if (isNaN(n)) return 'bg-slate-500'
      if (n >= 90) return 'bg-emerald-500'
      if (n >= 70) return 'bg-amber-500'
      return 'bg-rose-500'
    })
    return () => h('div', { class: 'bg-slate-50 rounded-xl p-4' }, [
      h('p', { class: 'text-xs text-slate-500 mb-2' }, props.label),
      h('p', { class: 'text-lg font-bold text-slate-800 mb-2' }, text.value),
      h('div', { class: 'h-2 w-full bg-slate-200 rounded-full overflow-hidden' }, [
        h('div', { class: `h-full ${barColor.value} transition-all`, style: { width: `${pct.value}%` } }),
      ]),
    ])
  },
})

const PlanSection = defineComponent({
  props: ['title', 'icon', 'plans', 'processing'],
  emits: ['open', 'activate', 'complete', 'cancel', 'schedule'],
  setup(props, { emit }) {
    function statusLabel(status) {
      const map = { Draft: 'مسودة', Scheduled: 'مجدولة', Active: 'نشطة', Completed: 'مكتملة', Cancelled: 'ملغاة' }
      return map[status] || status
    }
    function statusClass(status) {
      const map = { Draft: 'bg-slate-100 text-slate-700', Scheduled: 'bg-blue-100 text-blue-700', Active: 'bg-emerald-100 text-emerald-700', Completed: 'bg-purple-100 text-purple-700', Cancelled: 'bg-rose-100 text-rose-700' }
      return map[status] || 'bg-slate-100 text-slate-700'
    }
    function schedulerLabel(s) {
      const map = { ready_to_start: 'جاهزة للبدء', ready_to_close: 'جاهزة للإغلاق' }
      return map[s] || ''
    }
    return () => h('div', { class: 'bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4' }, [
      h('div', { class: 'flex items-center gap-2' }, [
        h('svg', { class: 'w-5 h-5 text-slate-600', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
          h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: props.icon }),
        ]),
        h('h2', { class: 'font-bold text-slate-800' }, props.title),
      ]),
      h('div', { class: 'space-y-3' }, props.plans.map((p) => h('div', { key: p.name, class: 'border border-slate-100 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4' }, [
        h('div', { class: 'flex-1 space-y-1' }, [
          h('div', { class: 'flex items-center gap-2 flex-wrap' }, [
            h('p', { class: 'font-semibold text-slate-800' }, p.plan_name),
            h('span', { class: `px-2 py-0.5 rounded text-xs font-semibold ${statusClass(p.status)}` }, statusLabel(p.status)),
            p.scheduler_status && p.scheduler_status !== 'none' ? h('span', { class: 'px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-700' }, schedulerLabel(p.scheduler_status)) : null,
          ]),
          h('p', { class: 'text-xs text-slate-500' }, `${p.start_date} → ${p.end_date}`),
        ]),
        h('div', { class: 'flex items-center gap-2 flex-wrap' }, [
          p.scheduler_status === 'ready_to_start' && p.status === 'Scheduled' ? h('button', { class: 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700', onClick: () => emit('activate', p.name) }, 'تفعيل الخطة') : null,
          p.status === 'Draft' ? h('button', { class: 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700', onClick: () => emit('schedule', p.name) }, 'جدولة') : null,
          h('button', { class: 'px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50', onClick: () => emit('open', p.name) }, 'عرض'),
          ['Draft', 'Scheduled', 'Active'].includes(p.status) ? h('button', { class: 'px-3 py-1.5 rounded-lg text-xs font-semibold border border-rose-200 text-rose-600 hover:bg-rose-50', onClick: () => emit('cancel', p.name) }, 'إلغاء') : null,
        ]),
      ]))),
    ])
  },
})

export default defineComponent({
  components: { ProgressCard, PlanSection },
})
</script>
