<template>
  <div class="p-6 max-w-5xl mx-auto space-y-6" dir="rtl">
    <!-- Header -->
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-3 min-w-0">
        <router-link
          :to="{ name: 'DecisionCenterPlans' }"
          class="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all flex items-center gap-1"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
          {{ __('العودة إلى الخطط') }}
        </router-link>
        <h1 class="text-xl font-bold text-slate-900 truncate">{{ plan?.plan_name || __('تفاصيل الخطة') }}</h1>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <Button v-if="!isTerminal" variant="outline" size="sm" @click="editPlan">
          {{ __('تعديل') }}
        </Button>
        <Button v-if="plan?.status === 'Draft'" variant="solid" size="sm" :loading="processing" @click="schedulePlan">
          {{ __('جدولة') }}
        </Button>
        <Button v-if="plan?.status === 'Scheduled'" variant="solid" size="sm" :loading="processing" @click="activatePlan">
          {{ __('تفعيل') }}
        </Button>
        <Button v-if="plan?.status === 'Active'" variant="solid" size="sm" :loading="processing" @click="completePlan">
          {{ __('إكمال') }}
        </Button>
        <Button v-if="!isTerminal" variant="outline" size="sm" class="text-rose-600" :loading="processing" @click="cancelPlan">
          {{ __('إلغاء') }}
        </Button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="flex flex-col items-center gap-3">
        <svg class="animate-spin h-10 w-10 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-slate-500 text-sm">{{ __('جاري التحميل...') }}</p>
      </div>
    </div>

    <template v-else-if="plan">
      <!-- Summary -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-5">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="space-y-1">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2.5 py-1 rounded-full text-xs font-semibold" :class="statusClass(plan.status)">
                {{ statusLabel(plan.status) }}
              </span>
              <span class="px-2.5 py-1 rounded-full text-xs font-semibold" :class="priorityClass(plan.priority)">
                {{ priorityLabel(plan.priority) }}
              </span>
              <span v-if="plan.target_achieved" class="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                {{ __('تم تحقيق الهدف') }}
              </span>
            </div>
            <p v-if="plan.description" class="text-sm text-slate-600">{{ plan.description }}</p>
          </div>
          <div class="text-left md:text-right text-sm text-slate-500 space-y-1">
            <p><span class="font-medium text-slate-700">{{ __('البداية:') }}</span> {{ plan.start_date }}</p>
            <p><span class="font-medium text-slate-700">{{ __('النهاية:') }}</span> {{ plan.end_date }}</p>
            <p><span class="font-medium text-slate-700">{{ __('الأيام المتبقية:') }}</span> {{ daysRemaining }}</p>
          </div>
        </div>

        <!-- Scheduler banners -->
        <div v-if="plan.scheduler_status === 'ready_to_start'" class="bg-blue-50 border border-blue-100 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <p class="text-sm font-medium text-blue-800">{{ __('الخطة جاهزة للبدء') }}</p>
          <Button variant="solid" size="sm" :loading="processing" @click="activatePlan">{{ __('تفعيل الخطة') }}</Button>
        </div>
        <div v-if="plan.scheduler_status === 'ready_to_close'" class="bg-amber-50 border border-amber-100 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <p class="text-sm font-medium text-amber-800">{{ __('انتهت مدة الخطة وتحتاج إلى مراجعة وإغلاق') }}</p>
          <Button variant="solid" size="sm" :loading="processing" @click="completePlan">{{ __('مراجعة وإكمال الخطة') }}</Button>
        </div>
        <div v-if="activePlanConflict" class="bg-amber-50 border border-amber-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <p class="text-sm text-amber-800">
            {{ __('لا يمكن تفعيل هذه الخطة لأن الخطة') }}
            <span class="font-bold">{{ activePlanConflict.plan_name || activePlanConflict.name }}</span>
            {{ __('نشطة حالياً — النظام يسمح بخطة نشطة واحدة فقط. أكملها أو ألغها أولاً.') }}
          </p>
          <Button variant="outline" size="sm" @click="openActivePlan">
            {{ __('عرض الخطة النشطة') }}
          </Button>
        </div>

        <!-- Progress -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <ProgressBox
            :label="outcomeLabel"
            :value="plan.progress?.outcome_progress"
            type="pct"
            :color="progressColor(plan.progress?.outcome_progress)"
          />
          <ProgressBox
            label="تقدم التنفيذ"
            :value="plan.progress?.execution_progress"
            type="pct"
            color="bg-purple-500"
          />
          <ProgressBox
            label="تقدم الوقت"
            :value="plan.progress?.time_progress"
            type="pct"
            color="bg-slate-500"
          />
        </div>

        <div v-if="primaryKpi" class="bg-slate-50 rounded-xl p-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-sm">
            <div>
              <span class="text-slate-500">{{ __('المؤشر الرئيسي:') }}</span>
              <span class="font-semibold text-slate-800">{{ primaryKpi.metric_label }}</span>
            </div>
            <div class="flex gap-4">
              <span><span class="text-slate-500">{{ __('الحالي:') }}</span> {{ formatValue(primaryKpi.current_value, primaryMeta?.unit) }}</span>
              <span><span class="text-slate-500">{{ __('الهدف:') }}</span> {{ formatValue(primaryKpi.target_value, primaryMeta?.unit) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Primary KPI -->
      <section v-if="primaryKpi" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
          <h2 class="font-bold text-slate-800">{{ __('الهدف الرئيسي') }}</h2>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div class="bg-slate-50 rounded-xl p-4 space-y-2">
            <p><span class="text-slate-500">{{ __('المؤشر:') }}</span> {{ primaryKpi.metric_label }}</p>
            <p><span class="text-slate-500">{{ __('طريقة القياس:') }}</span> {{ strategyLabel(primaryKpi.progress_strategy) }}</p>
            <p><span class="text-slate-500">{{ __('الاتجاه:') }}</span> {{ directionLabel(primaryKpi.direction) }}</p>
            <p><span class="text-slate-500">{{ __('استراتيجية خط الأساس:') }}</span> {{ baselineLabel(primaryKpi.baseline_strategy) }}</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-4 space-y-2">
            <p><span class="text-slate-500">{{ __('خط الأساس المحسوب:') }}</span> {{ formatValue(primaryKpi.computed_baseline, primaryMeta?.unit) }}</p>
            <p v-if="primaryKpi.override_baseline !== null && primaryKpi.override_baseline !== undefined">
              <span class="text-slate-500">{{ __('خط الأساس المعتمد:') }}</span> {{ formatValue(primaryKpi.override_baseline, primaryMeta?.unit) }}
            </p>
            <p><span class="text-slate-500">{{ __('القيمة المستهدفة:') }}</span> {{ formatValue(primaryKpi.target_value, primaryMeta?.unit) }}</p>
            <p><span class="text-slate-500">{{ __('القيمة الحالية:') }}</span> {{ formatValue(primaryKpi.current_value, primaryMeta?.unit) }}</p>
            <p><span class="text-slate-500">{{ __('حالة الصحة:') }}</span> {{ healthLabel(plan.progress?.health) }} <HelpLink topic="plan_health" /></p>
          </div>
        </div>
      </section>

      <!-- Supporting KPIs -->
      <section class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h2 class="font-bold text-slate-800">{{ __('المؤشرات المساندة') }}</h2>
        </div>
        <div v-if="supportingKpis.length" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="(kpi, idx) in supportingKpis" :key="idx" class="bg-slate-50 rounded-xl p-4 text-sm space-y-2">
            <p class="font-semibold text-slate-800">{{ kpi.metric_label }}</p>
            <p><span class="text-slate-500">{{ __('الهدف:') }}</span> {{ formatValue(kpi.target_value, kpiMeta(kpi.metric_key)?.unit) }}</p>
            <p><span class="text-slate-500">{{ __('الحالي:') }}</span> {{ formatValue(kpi.current_value, kpiMeta(kpi.metric_key)?.unit) }}</p>
            <p><span class="text-slate-500">{{ __('تم تحقيق الهدف:') }}</span> {{ kpi.target_achieved ? __('نعم') : __('لا') }}</p>
          </div>
        </div>
        <div v-else class="text-center text-sm text-slate-400 py-4">{{ __('لا توجد مؤشرات مساندة') }}</div>
      </section>

      <!-- Actions -->
      <section class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            <h2 class="font-bold text-slate-800">{{ __('إجراءات الخطة') }}</h2>
          </div>
          <Button v-if="plan.status === 'Active' && canManage" variant="solid" size="sm" :loading="savingActions" @click="saveActions">
            {{ __('حفظ تحديث الإجراءات') }}
          </Button>
        </div>

        <div v-if="plan.actions.length" class="space-y-3">
          <div v-for="(action, idx) in plan.actions" :key="idx" class="border border-slate-100 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="flex-1 text-sm">
              <p class="font-semibold text-slate-800">{{ action.title }}</p>
              <p v-if="action.description" class="text-slate-600 mt-1">{{ action.description }}</p>
              <div class="flex gap-4 mt-2 text-xs text-slate-500 flex-wrap">
                <span v-if="action.due_date">{{ __('الاستحقاق:') }} {{ action.due_date }}</span>
                <span>{{ __('الوزن:') }} {{ action.weight || 0 }}</span>
                <span v-if="action.completed_by">{{ __('أنجز بواسطة:') }} {{ action.completed_by }}</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <span
                class="px-2.5 py-1 rounded-full text-xs font-semibold"
                :class="actionStatusClass(action.status)"
              >
                {{ actionStatusLabel(action.status) }}
              </span>
              <select
                v-if="plan.status === 'Active' && canManage"
                v-model="action.status"
                class="border border-slate-300 rounded-lg px-2 py-1 text-sm bg-white focus:ring-2 focus:ring-blue-500"
              >
                <option v-for="opt in actionStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-sm text-slate-400 py-4">{{ __('لا توجد إجراءات مسجلة') }}</div>
      </section>

      <!-- Checkpoints -->
      <section class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <h2 class="font-bold text-slate-800">{{ __('نقاط التحقق') }}</h2>
        </div>
        <div v-if="plan.checkpoints.length" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-slate-50 text-slate-600">
                <th class="px-3 py-2 text-right">{{ __('الشهر') }}</th>
                <th class="px-3 py-2 text-right">{{ __('الهدف') }}</th>
                <th class="px-3 py-2 text-right">{{ __('الفعلي') }}</th>
                <th class="px-3 py-2 text-right">{{ __('الصحة') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="cp in plan.checkpoints" :key="cp.month" class="hover:bg-slate-50">
                <td class="px-3 py-2">{{ cp.month }}</td>
                <td class="px-3 py-2">{{ formatValue(cp.target_value, primaryMeta?.unit) }}</td>
                <td class="px-3 py-2">{{ formatValue(cp.actual_value, primaryMeta?.unit) }}</td>
                <td class="px-3 py-2">
                  <span class="px-2 py-0.5 rounded text-xs font-semibold" :class="healthClass(cp.health)">
                    {{ healthLabel(cp.health) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-center text-sm text-slate-400 py-4">{{ __('لا توجد نقاط تحقق') }}</div>
      </section>

      <!-- Related decisions -->
      <section class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <h2 class="font-bold text-slate-800">{{ __('القرارات المرتبطة') }}</h2>
        </div>
        <div v-if="relatedDecisions.length" class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div v-for="decision in relatedDecisions" :key="decision.id" class="border border-slate-100 rounded-xl p-4 text-sm">
            <div class="flex items-center justify-between mb-2">
              <p class="font-semibold text-slate-800">{{ decision.title }}</p>
              <span class="px-2 py-0.5 rounded text-xs font-semibold" :class="severityClass(decision.severity)">{{ decision.severity }}</span>
            </div>
            <p class="text-slate-600 line-clamp-2">{{ decision.summary }}</p>
          </div>
        </div>
        <div v-else class="text-center text-sm text-slate-400 py-4">{{ __('لا توجد قرارات مرتبطة بالفترة الحالية') }}</div>
      </section>

      <!-- Lifecycle history -->
      <section class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 class="font-bold text-slate-800">{{ __('سجل دورة الحياة') }}</h2>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
          <div class="bg-slate-50 rounded-lg p-3">
            <p class="text-slate-500">{{ __('تاريخ الإنشاء') }}</p>
            <p class="font-medium text-slate-800">{{ plan.created_at ? formatDateTime(plan.created_at) : '—' }}</p>
          </div>
          <div class="bg-slate-50 rounded-lg p-3">
            <p class="text-slate-500">{{ __('تاريخ التفعيل') }}</p>
            <p class="font-medium text-slate-800">{{ plan.activated_at ? formatDateTime(plan.activated_at) : '—' }}</p>
          </div>
          <div class="bg-slate-50 rounded-lg p-3">
            <p class="text-slate-500">{{ __('تاريخ الإكمال') }}</p>
            <p class="font-medium text-slate-800">{{ plan.completed_at ? formatDateTime(plan.completed_at) : '—' }}</p>
          </div>
        </div>
      </section>
    </template>

    <div v-else class="text-center py-12 text-slate-500">{{ __('الخطة غير موجودة') }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call } from '@/utils/apiWrapper'
import { useToast } from '@/composables/useToast'
import Button from 'frappe-ui/src/components/Button.vue'
import HelpLink from '@/components/HelpLink.vue'

const route = useRoute()
const router = useRouter()
const { showSuccess, showError } = useToast()

const planId = computed(() => route.params.planId)
const plan = ref(null)
const loading = ref(false)
const processing = ref(false)
const savingActions = ref(false)
const activePlanConflict = ref(null)
const canManage = ref(false)
const relatedDecisions = ref([])

const actionStatusOptions = [
  { value: 'Not Started', label: 'لم يبدأ' },
  { value: 'In Progress', label: 'قيد التنفيذ' },
  { value: 'Completed', label: 'مكتمل' },
  { value: 'Cancelled', label: 'ملغى' },
]

const isTerminal = computed(() => ['Completed', 'Cancelled'].includes(plan.value?.status))
const primaryKpi = computed(() => plan.value?.kpis?.find((k) => k.is_primary) || null)
const supportingKpis = computed(() => plan.value?.kpis?.filter((k) => !k.is_primary) || [])
const primaryMeta = computed(() => getMetricMeta(primaryKpi.value?.metric_key))

function getMetricMeta(metricKey) {
  if (!metricKey) return null
  return plan.value?.__metricMeta?.[metricKey] || null
}

const daysRemaining = computed(() => {
  if (!plan.value?.end_date) return '—'
  const end = new Date(plan.value.end_date)
  const today = new Date()
  const diff = Math.ceil((end - today) / (1000 * 60 * 60 * 24))
  return diff >= 0 ? `${diff} يوم` : __('انتهت')
})

const outcomeLabel = computed(() => {
  const strategy = primaryKpi.value?.progress_strategy
  if (strategy === 'cumulative_ceiling') return __('وتيرة الاستهلاك')
  if (strategy === 'cumulative_growth') return __('تحقيق النمو التراكمي')
  return __('تحقيق الهدف')
})

function formatValue(value, unit) {
  if (value === null || value === undefined || value === '') return '—'
  const n = Number(value)
  if (isNaN(n)) return '—'
  if (unit === 'currency') return n.toLocaleString('en-US', { maximumFractionDigits: 2 })
  if (unit === 'percent' || unit === 'pct') return `${n.toFixed(1)}%`
  if (unit === 'days') return `${n.toFixed(0)} يوم`
  return n.toLocaleString('en-US', { maximumFractionDigits: 2 })
}

function formatPct(value) {
  if (value === null || value === undefined || value === '') return '—'
  const n = Number(value)
  if (isNaN(n)) return '—'
  return `${n.toFixed(1)}%`
}

function formatDateTime(value) {
  if (!value) return '—'
  try {
    const d = new Date(value)
    return d.toLocaleString('ar-SA', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return value
  }
}

function statusLabel(status) {
  const map = { Draft: 'مسودة', Scheduled: 'مجدولة', Active: 'نشطة', Completed: 'مكتملة', Cancelled: 'ملغاة' }
  return map[status] || status
}

function priorityLabel(priority) {
  const map = { Low: 'منخفضة', Medium: 'متوسطة', High: 'عالية', Critical: 'حرجة' }
  return map[priority] || priority
}

function strategyLabel(strategy) {
  const map = { level: 'مستوى', cumulative_growth: 'نمو تراكمي', cumulative_ceiling: 'سقف تراكمي' }
  return map[strategy] || strategy
}

function baselineLabel(strategy) {
  const map = {
    previous_equivalent_period: 'الفترة المكافئة السابقة',
    average_previous_3_periods: 'متوسط آخر 3 فترات',
    snapshot_at_plan_start: 'لقطة عند بدء الخطة',
    manual_only: 'يدوي فقط',
  }
  return map[strategy] || strategy
}

function directionLabel(dir) {
  return dir === 'decrease' ? 'انخفاض' : 'زيادة'
}

function healthLabel(health) {
  const map = { on_track: 'على المسار', needs_attention: 'يحتاج اهتمام', behind: 'متأخر' }
  return map[health] || health || '—'
}

function actionStatusLabel(status) {
  const map = { 'Not Started': 'لم يبدأ', 'In Progress': 'قيد التنفيذ', Completed: 'مكتمل', Cancelled: 'ملغى' }
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

function priorityClass(priority) {
  const map = { Low: 'bg-slate-100 text-slate-700', Medium: 'bg-blue-100 text-blue-700', High: 'bg-amber-100 text-amber-700', Critical: 'bg-rose-100 text-rose-700' }
  return map[priority] || 'bg-slate-100 text-slate-700'
}

function healthClass(health) {
  const map = { on_track: 'bg-emerald-100 text-emerald-700', needs_attention: 'bg-amber-100 text-amber-700', behind: 'bg-rose-100 text-rose-700' }
  return map[health] || 'bg-slate-100 text-slate-700'
}

function actionStatusClass(status) {
  const map = { 'Not Started': 'bg-slate-100 text-slate-700', 'In Progress': 'bg-blue-100 text-blue-700', Completed: 'bg-emerald-100 text-emerald-700', Cancelled: 'bg-rose-100 text-rose-700' }
  return map[status] || 'bg-slate-100 text-slate-700'
}

function severityClass(severity) {
  const map = { high: 'bg-rose-100 text-rose-700', medium: 'bg-amber-100 text-amber-700', low: 'bg-blue-100 text-blue-700', urgent: 'bg-rose-100 text-rose-700' }
  return map[severity] || 'bg-slate-100 text-slate-700'
}

function progressColor(value) {
  const n = Number(value)
  if (isNaN(n)) return 'bg-slate-500'
  if (n >= 90) return 'bg-emerald-500'
  if (n >= 70) return 'bg-amber-500'
  return 'bg-rose-500'
}

function kpiMeta(metricKey) {
  if (!metricKey || !plan.value?.__metricMeta) return null
  return plan.value.__metricMeta[metricKey]
}

async function loadPermission() {
  try {
    canManage.value = await call('bs.baron_servies.api.decision_center.plan_api.has_plan_management_permission')
  } catch (e) {
    canManage.value = false
  }
}

async function loadPlan() {
  if (!planId.value) {
    plan.value = null
    return
  }
  loading.value = true
  try {
    const res = await call('bs.baron_servies.api.decision_center.plan_api.get_plan_detail', { plan_name: planId.value })
    plan.value = res
    await loadMetricMeta(res.kpis)
    await loadDecisions()
  } catch (e) {
    showError(e.message || __('فشل تحميل الخطة'))
  } finally {
    loading.value = false
  }
}

async function loadMetricMeta(kpis) {
  if (!kpis?.length) return
  try {
    const res = await call('bs.baron_servies.api.decision_center.plan_api.get_plan_reference_options')
    const meta = {}
    ;(res.metrics || []).forEach((m) => { meta[m.metric_key] = m })
    plan.value.__metricMeta = meta
  } catch (e) {
    // silent
  }
}

async function loadDecisions() {
  try {
    const res = await call('bs.baron_servies.api.decision_center.plan_api.get_plan_decisions', { plan_name: planId.value })
    relatedDecisions.value = res.decisions || []
  } catch (e) {
    relatedDecisions.value = []
  }
}

function editPlan() {
  router.push({ name: 'DecisionCenterPlanEdit', params: { planId: planId.value } })
}

async function schedulePlan() {
  processing.value = true
  try {
    await call('bs.baron_servies.api.decision_center.plan_api.schedule_plan', { plan_name: planId.value })
    showSuccess(__('تمت جدولة الخطة'))
    await loadPlan()
  } catch (e) {
    showError(e.message || __('فشل جدولة الخطة'))
  } finally {
    processing.value = false
  }
}

async function activatePlan() {
  activePlanConflict.value = null
  processing.value = true
  try {
    // Single Active plan is enforced by the engine — pre-check for a friendly UX
    const res = await call('bs.baron_servies.api.decision_center.plan_api.get_plans', { status: 'Active' })
    const other = (res?.plans || []).find((p) => p.name !== planId.value)
    if (other) {
      activePlanConflict.value = other
      return
    }
    await call('bs.baron_servies.api.decision_center.plan_api.activate_plan', { plan_name: planId.value })
    showSuccess(__('تم تفعيل الخطة'))
    await loadPlan()
  } catch (e) {
    const msg = e.message || ''
    const m = msg.match(/Plan '([^']+)' is already Active/)
    if (m) activePlanConflict.value = { name: m[1], plan_name: m[1] }
    showError(msg || __('فشل تفعيل الخطة'))
  } finally {
    processing.value = false
  }
}

function openActivePlan() {
  if (!activePlanConflict.value) return
  router.push({ name: 'DecisionCenterPlanDetail', params: { planId: activePlanConflict.value.name } })
  activePlanConflict.value = null
}

async function completePlan() {
  processing.value = true
  try {
    await call('bs.baron_servies.api.decision_center.plan_api.complete_plan', { plan_name: planId.value })
    showSuccess(__('تم إكمال الخطة'))
    await loadPlan()
  } catch (e) {
    showError(e.message || __('فشل إكمال الخطة'))
  } finally {
    processing.value = false
  }
}

async function cancelPlan() {
  if (!confirm(__('هل أنت متأكد من إلغاء الخطة؟'))) return
  processing.value = true
  try {
    await call('bs.baron_servies.api.decision_center.plan_api.cancel_plan', { plan_name: planId.value })
    showSuccess(__('تم إلغاء الخطة'))
    await loadPlan()
  } catch (e) {
    showError(e.message || __('فشل إلغاء الخطة'))
  } finally {
    processing.value = false
  }
}

async function saveActions() {
  savingActions.value = true
  try {
    await call('bs.baron_servies.api.decision_center.plan_api.update_plan_actions', {
      plan_name: planId.value,
      actions: JSON.stringify(plan.value.actions),
    })
    showSuccess(__('تم تحديث الإجراءات'))
    await loadPlan()
  } catch (e) {
    showError(e.message || __('فشل تحديث الإجراءات'))
  } finally {
    savingActions.value = false
  }
}

watch(planId, loadPlan)
onMounted(async () => {
  await loadPermission()
  await loadPlan()
})
</script>

<script>
import { defineComponent, h, computed } from 'vue'

const ProgressBox = defineComponent({
  props: ['label', 'value', 'type', 'color'],
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
    return () => h('div', { class: 'bg-slate-50 rounded-xl p-4' }, [
      h('p', { class: 'text-xs text-slate-500 mb-2' }, props.label),
      h('div', { class: 'flex items-center justify-between mb-1' }, [
        h('span', { class: 'text-lg font-bold text-slate-800' }, text.value),
      ]),
      h('div', { class: 'h-2 w-full bg-slate-200 rounded-full overflow-hidden' }, [
        h('div', { class: `h-full ${props.color || 'bg-blue-500'} transition-all`, style: { width: `${pct.value}%` } }),
      ]),
    ])
  },
})

export default defineComponent({
  components: { ProgressBox },
})
</script>
