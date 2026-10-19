<template>
  <div class="p-6 max-w-5xl mx-auto space-y-6" dir="rtl">
    <!-- Header -->
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-3 min-w-0">
        <router-link
          :to="{ name: 'DecisionCenterPlans' }"
          class="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-all flex items-center gap-1"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
          {{ isEdit ? __('العودة إلى الخطط') : __('العودة إلى الخطط') }}
        </router-link>
        <h1 class="text-xl font-bold text-slate-900 truncate">
          {{ isEdit ? __('تعديل الخطة') : __('إنشاء خطة جديدة') }}
        </h1>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" :loading="saving" @click="save(isEdit ? plan.status : 'Draft')">
          {{ isEdit ? __('حفظ التغييرات') : __('حفظ كمسودة') }}
        </Button>
        <Button
          v-if="canSchedule"
          variant="solid"
          :loading="saving"
          @click="save('Scheduled')"
        >
          {{ __('حفظ وجدولة') }}
        </Button>
      </div>
    </div>

    <!-- Unauthorized -->
    <div v-if="!loading && !canManage" class="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-center">
      <p class="text-rose-700 font-semibold">{{ __('غير مصرح') }}</p>
      <p class="text-sm text-rose-600 mt-1">{{ __('لا تمتلك صلاحية إدارة الخطط') }}</p>
    </div>

    <template v-else>
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

      <template v-else>
        <!-- Basic info -->
        <section class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div class="flex items-center gap-2 mb-2">
            <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h2 class="font-bold text-slate-800">{{ __('المعلومات الأساسية') }}</h2>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField v-model="plan.plan_name" label="اسم الخطة" required />
            <FormField v-model="plan.priority" label="الأولوية" type="select" :options="priorityOptions" />
            <FormField v-model="plan.start_date" label="تاريخ البداية" type="date" required />
            <FormField v-model="plan.end_date" label="تاريخ النهاية" type="date" required />
            <FormField v-model="plan.description" label="الوصف" type="textarea" class="md:col-span-2" />
          </div>
        </section>

        <!-- Primary KPI -->
        <section class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div class="flex items-center gap-2 mb-2">
            <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <h2 class="font-bold text-slate-800">{{ __('الهدف الرئيسي') }}</h2>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">{{ __('اختر المؤشر') }}</label>
              <select
                v-model="primaryKpi.metric_key"
                class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              >
                <option value="" disabled>{{ __('اختر مؤشراً') }}</option>
                <option v-for="m in planMetrics" :key="m.metric_key" :value="m.metric_key">
                  {{ m.metric_label_ar || m.metric_label_en || m.metric_key }}
                </option>
              </select>
            </div>
            <FormField
              v-model="primaryKpi.target_value"
              label="القيمة المستهدفة"
              type="number"
              required
            />
            <FormField v-model="primaryKpi.direction" label="الاتجاه" type="select" :options="directionOptions" />
            <FormField v-model="primaryKpi.weight" label="الوزن" type="number" />
            <FormField v-model="primaryKpi.tolerance_pct" label="نسبة التسامح (%)" type="number" />
          </div>

          <div v-if="primaryMeta" class="bg-slate-50 rounded-xl p-4 space-y-2 text-sm">
            <p><span class="text-slate-500">{{ __('المصدر:') }}</span> {{ sourceLabel(primaryMeta) }}</p>
            <p><span class="text-slate-500">{{ __('طريقة الحساب:') }}</span> {{ formulaSummary(primaryMeta) }}</p>
            <p><span class="text-slate-500">{{ __('نوع القياس:') }}</span> {{ strategyLabel(primaryMeta.progress_strategy) }}</p>
          </div>

          <div class="bg-blue-50 border border-blue-100 rounded-xl p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-blue-800">{{ __('خط الأساس المحسوب') }} <HelpLink topic="baseline" /></span>
              <span v-if="primaryKpi.baseline_preview !== null" class="text-lg font-bold text-blue-900">
                {{ formatValue(primaryKpi.baseline_preview, primaryMeta?.unit) }}
              </span>
              <span v-else class="text-sm text-blue-400">{{ __('—') }}</span>
            </div>
            <div class="flex items-center gap-2">
              <input
                :id="'override-baseline-primary'"
                v-model="primaryKpi.override_enabled"
                type="checkbox"
                class="rounded text-blue-600"
              />
              <label :for="'override-baseline-primary'" class="text-sm text-blue-800">{{ __('تعديل خط الأساس') }}</label>
            </div>
            <div v-if="primaryKpi.override_enabled" class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
              <FormField v-model="primaryKpi.override_baseline" label="خط الأساس المعتمد" type="number" required />
              <FormField v-model="primaryKpi.override_reason" label="سبب التعديل" required />
            </div>
            <div v-if="primaryKpi.override_enabled && primaryKpi.override_baseline !== null" class="mt-2 text-sm text-blue-700">
              {{ __('خط الأساس المعتمد:') }} {{ formatValue(primaryKpi.override_baseline, primaryMeta?.unit) }}
            </div>
          </div>
        </section>

        <!-- Supporting KPIs -->
        <section class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h2 class="font-bold text-slate-800">{{ __('مؤشرات مساندة') }}</h2>
            </div>
            <button
              type="button"
              class="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1"
              @click="addSupportingKpi"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              {{ __('إضافة مؤشر') }}
            </button>
          </div>

          <div v-for="(kpi, idx) in supportingKpis" :key="idx" class="border border-slate-100 rounded-xl p-4 space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-slate-700">{{ __('مؤشر مساند') }} #{{ idx + 1 }}</h3>
              <button type="button" class="text-rose-500 hover:text-rose-700 text-sm" @click="removeSupportingKpi(idx)">
                {{ __('حذف') }}
              </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-600 mb-1">{{ __('المؤشر') }}</label>
                <select
                  v-model="kpi.metric_key"
                  class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                >
                  <option value="" disabled>{{ __('اختر مؤشراً') }}</option>
                  <option v-for="m in planMetrics" :key="m.metric_key" :value="m.metric_key">
                    {{ m.metric_label_ar || m.metric_label_en || m.metric_key }}
                  </option>
                </select>
              </div>
              <FormField v-model="kpi.target_value" label="الهدف" type="number" />
              <FormField v-model="kpi.direction" label="الاتجاه" type="select" :options="directionOptions" />
              <FormField v-model="kpi.weight" label="الوزن" type="number" />
            </div>
            <div v-if="kpi.metric_key" class="bg-slate-50 rounded-lg p-3 text-xs space-y-1">
              <p><span class="text-slate-500">{{ __('طريقة القياس:') }}</span> {{ strategyLabel(kpiMeta(kpi.metric_key)?.progress_strategy) }}</p>
              <p><span class="text-slate-500">{{ __('خط الأساس:') }}</span> {{ formatValue(kpi.baseline_preview, kpiMeta(kpi.metric_key)?.unit) }}</p>
            </div>
          </div>

          <div v-if="!supportingKpis.length" class="text-center text-sm text-slate-400 py-4">
            {{ __('لا توجد مؤشرات مساندة') }}
          </div>
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
            <button
              type="button"
              class="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1"
              @click="addAction"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              {{ __('إضافة إجراء') }}
            </button>
          </div>

          <div v-for="(action, idx) in plan.actions" :key="idx" class="border border-slate-100 rounded-xl p-4 space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-slate-700">{{ __('إجراء') }} #{{ idx + 1 }}</h3>
              <button type="button" class="text-rose-500 hover:text-rose-700 text-sm" @click="removeAction(idx)">
                {{ __('حذف') }}
              </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              <FormField v-model="action.title" label="عنوان الإجراء" required />
              <FormField v-model="action.due_date" label="تاريخ الاستحقاق" type="date" />
              <FormField v-model="action.weight" label="الوزن" type="number" />
              <FormField v-model="action.status" label="الحالة" type="select" :options="actionStatusOptions" />
            </div>
            <FormField v-model="action.description" label="الوصف" type="textarea" />
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-600 mb-1">{{ __('قاعدة مرتبطة (اختياري)') }}</label>
                <select
                  v-model="action.related_rule_id"
                  class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                >
                  <option value="">{{ __('لا يوجد') }}</option>
                  <option v-for="r in referenceOptions.rules" :key="r.id" :value="r.id">{{ r.title }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-600 mb-1">{{ __('مؤشر مرتبط (اختياري)') }}</label>
                <select
                  v-model="action.related_metric_key"
                  class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                >
                  <option value="">{{ __('لا يوجد') }}</option>
                  <option v-for="m in planMetrics" :key="m.metric_key" :value="m.metric_key">
                    {{ m.metric_label_ar || m.metric_label_en || m.metric_key }}
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-600 mb-1">{{ __('تصنيف مصروفات مرتبط (اختياري)') }}</label>
                <select
                  v-model="action.related_expense_category"
                  class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                >
                  <option value="">{{ __('لا يوجد') }}</option>
                  <option v-for="c in referenceOptions.expense_categories" :key="c.name" :value="c.name">{{ c.category_name }}</option>
                </select>
              </div>
            </div>
          </div>

          <div v-if="!plan.actions.length" class="text-center text-sm text-slate-400 py-4">
            {{ __('لا توجد إجراءات مسجلة') }}
          </div>
        </section>

        <!-- Footer actions -->
        <div class="flex justify-end gap-3">
          <Button variant="outline" :loading="saving" @click="save(isEdit ? plan.status : 'Draft')">
            {{ isEdit ? __('حفظ التغييرات') : __('حفظ كمسودة') }}
          </Button>
          <Button v-if="canSchedule" variant="solid" :loading="saving" @click="save('Scheduled')">
            {{ __('حفظ وجدولة') }}
          </Button>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call } from '@/utils/apiWrapper'
import { useToast } from '@/composables/useToast'
import HelpLink from '@/components/HelpLink.vue'
import Button from 'frappe-ui/src/components/Button.vue'

const route = useRoute()
const router = useRouter()
const { showSuccess, showError } = useToast()

const planId = computed(() => route.params.planId)
const isEdit = computed(() => !!planId.value)
const canManage = ref(false)
const loading = ref(false)
const saving = ref(false)
const referenceOptions = reactive({ metrics: [], rules: [], expense_categories: [] })

const defaultPriority = ref('Medium')

const plan = reactive({
  plan_name: '',
  description: '',
  priority: 'Medium',
  start_date: '',
  end_date: '',
  notes: '',
  kpis: [],
  actions: [],
})

const priorityOptions = [
  { value: 'Low', label: 'منخفضة' },
  { value: 'Medium', label: 'متوسطة' },
  { value: 'High', label: 'عالية' },
  { value: 'Critical', label: 'حرجة' },
]

const directionOptions = [
  { value: 'increase', label: 'زيادة' },
  { value: 'decrease', label: 'انخفاض' },
]

const actionStatusOptions = [
  { value: 'Not Started', label: 'لم يبدأ' },
  { value: 'In Progress', label: 'قيد التنفيذ' },
  { value: 'Completed', label: 'مكتمل' },
  { value: 'Cancelled', label: 'ملغى' },
]

const planMetrics = computed(() =>
  referenceOptions.metrics.filter((m) => m.system_available && m.enabled_for_plans)
)

const primaryKpi = computed(() => plan.kpis.find((k) => k.is_primary) || null)
const supportingKpis = computed(() => plan.kpis.filter((k) => !k.is_primary))

const primaryMeta = computed(() => {
  if (!primaryKpi.value) return null
  return referenceOptions.metrics.find((m) => m.metric_key === primaryKpi.value.metric_key) || null
})

function kpiMeta(metricKey) {
  return referenceOptions.metrics.find((m) => m.metric_key === metricKey) || null
}

const canSchedule = computed(() => {
  if (!isEdit.value) return true
  return plan.status === 'Draft'
})

function strategyLabel(strategy) {
  const map = {
    level: 'مستوى',
    cumulative_growth: 'نمو تراكمي',
    cumulative_ceiling: 'سقف تراكمي',
  }
  return map[strategy] || strategy
}

function sourceLabel(meta) {
  const module = (meta?.calculation_module || '').toLowerCase()
  const formula = (meta?.formula_description || '').toLowerCase()
  if (module.includes('sales_invoice') || formula.includes('sales invoice') || meta.category === 'sales') {
    return __('فواتير المبيعات')
  }
  if (module.includes('purchase') || formula.includes('purchase')) {
    return __('فواتير المشتريات')
  }
  if (module.includes('gl_entry') || formula.includes('expense') || formula.includes('debit') || meta.category === 'expenses') {
    return __('القيود المحاسبية')
  }
  if (module.includes('bin') || module.includes('stock') || formula.includes('stock') || meta.category === 'inventory') {
    return __('حركة المخزون')
  }
  if (formula.includes('customer') || meta.category === 'customers') {
    return __('بيانات العملاء')
  }
  return __('بيانات النظام')
}

function formulaSummary(meta) {
  const formula = meta?.formula_description || ''
  const map = {
    'SUM(Sales Invoice.grand_total)': 'مجموع قيم فواتير المبيعات',
    'total_expenses / sales_total * 100': 'إجمالي المصاريف ÷ إجمالي المبيعات × 100',
    'SUM(GL Entry.debit - credit) for mapped expense accounts': 'مجموع مدين - دائن لحسابات المصاريف المرتبطة',
    'COUNT(DISTINCT customer) from Sales Invoice in period': 'عدد العملاء الفريدين في فواتير المبيعات',
    'sales_total / invoice_count': 'إجمالي المبيعات ÷ عدد الفواتير',
    'SUM(stock_value) for items with no sales in dead_stock_days': 'مجموع قيمة أصناف لم تُباع خلال فترة المخزون الراكد',
    'SUM(stock_value) for items with sales velocity implying days_of_stock > slow_moving_days': 'مجموع قيمة أصناف أيام المخزون فيها أعلى من حد البطء',
    'actual_qty / avg_daily_sales': 'الكمية المتاحة ÷ متوسط المبيعات اليومية',
  }
  return map[formula] || formula
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

function makeKpi(isPrimary = false) {
  return {
    is_primary: isPrimary ? 1 : 0,
    metric_key: '',
    direction: 'increase',
    target_value: null,
    weight: isPrimary ? 1 : 0,
    tolerance_pct: 10,
    override_enabled: false,
    override_baseline: null,
    override_reason: '',
    baseline_preview: null,
  }
}

function makeAction() {
  return {
    title: '',
    description: '',
    due_date: '',
    status: 'Not Started',
    weight: 0,
    related_rule_id: '',
    related_metric_key: '',
    related_expense_category: '',
  }
}

function addSupportingKpi() {
  plan.kpis.push(makeKpi(false))
}

function removeSupportingKpi(index) {
  const toRemove = supportingKpis.value[index]
  const idx = plan.kpis.indexOf(toRemove)
  if (idx > -1) plan.kpis.splice(idx, 1)
}

function addAction() {
  plan.actions.push(makeAction())
}

function removeAction(index) {
  plan.actions.splice(index, 1)
}

async function loadPermission() {
  try {
    canManage.value = await call('bs.baron_servies.api.decision_center.plan_api.has_plan_management_permission')
  } catch (e) {
    canManage.value = false
  }
}

async function loadReferenceOptions() {
  const res = await call('bs.baron_servies.api.decision_center.plan_api.get_plan_reference_options')
  referenceOptions.metrics = res.metrics || []
  referenceOptions.rules = res.rules || []
  referenceOptions.expense_categories = res.expense_categories || []
  defaultPriority.value = res.default_plan_priority || 'Medium'
}

async function loadPlan() {
  if (!isEdit.value) {
    plan.priority = defaultPriority.value
    plan.kpis = [makeKpi(true)]
    return
  }
  if (!planId.value) {
    showError(__('معرّف الخطة غير موجود'))
    return
  }
  const res = await call('bs.baron_servies.api.decision_center.plan_api.get_plan_detail', {
    plan_name: planId.value,
  })
  plan.plan_name = res.plan_name
  plan.description = res.description
  plan.priority = res.priority
  plan.start_date = res.start_date
  plan.end_date = res.end_date
  plan.notes = res.notes
  plan.status = res.status
  plan.kpis = (res.kpis || []).map((k) => ({
    is_primary: k.is_primary ? 1 : 0,
    metric_key: k.metric_key,
    direction: k.direction || 'increase',
    target_value: k.target_value,
    weight: k.weight,
    tolerance_pct: k.tolerance_pct || 10,
    override_enabled: k.override_baseline !== null && k.override_baseline !== undefined,
    override_baseline: k.override_baseline,
    override_reason: k.override_reason || '',
    baseline_preview: k.computed_baseline,
  }))
  if (!plan.kpis.find((k) => k.is_primary)) {
    plan.kpis.unshift(makeKpi(true))
  }
  plan.actions = (res.actions || []).map((a) => ({
    title: a.title,
    description: a.description,
    due_date: a.due_date || '',
    status: a.status,
    weight: a.weight,
    related_rule_id: a.related_rule_id || '',
    related_metric_key: a.related_metric_key || '',
    related_expense_category: a.related_expense_category || '',
  }))
}

async function previewBaseline(kpi) {
  if (!kpi.metric_key || !plan.start_date) return
  try {
    const res = await call('bs.baron_servies.api.decision_center.plan_api.compute_baseline_preview', {
      metric_key: kpi.metric_key,
      reference_date: plan.start_date,
      plan_start_date: plan.start_date,
    })
    kpi.baseline_preview = res.value
  } catch (e) {
    kpi.baseline_preview = null
  }
}

// Watch primary KPI metric/start date for baseline preview
watch(
  () => [primaryKpi.value?.metric_key, plan.start_date],
  () => {
    if (primaryKpi.value) previewBaseline(primaryKpi.value)
  },
  { immediate: true }
)

// Watch supporting KPIs metric/start date
watch(
  () => [supportingKpis.value.map((k) => k.metric_key), plan.start_date],
  () => {
    supportingKpis.value.forEach((k) => previewBaseline(k))
  },
  { deep: true }
)

function buildPayload(status) {
  return {
    plan_name: plan.plan_name,
    description: plan.description,
    priority: plan.priority,
    start_date: plan.start_date,
    end_date: plan.end_date,
    notes: plan.notes,
    status,
    kpis: plan.kpis.map((k) => ({
      is_primary: k.is_primary ? 1 : 0,
      metric_key: k.metric_key,
      direction: k.direction,
      target_value: k.target_value,
      weight: k.weight,
      tolerance_pct: k.tolerance_pct,
      override_baseline: k.override_enabled ? k.override_baseline : null,
      override_reason: k.override_enabled ? k.override_reason : null,
    })),
    actions: plan.actions.map((a) => ({
      title: a.title,
      description: a.description,
      due_date: a.due_date || null,
      status: a.status,
      weight: a.weight,
      related_rule_id: a.related_rule_id || null,
      related_metric_key: a.related_metric_key || null,
      related_expense_category: a.related_expense_category || null,
    })),
  }
}

async function save(status) {
  if (!plan.plan_name || !plan.start_date || !plan.end_date) {
    showError(__('يرجى ملء اسم الخطة وتواريخ البداية والنهاية'))
    return
  }
  if (!primaryKpi.value || !primaryKpi.value.metric_key) {
    showError(__('يرجى اختيار الهدف الرئيسي'))
    return
  }
  if (new Date(plan.end_date) < new Date(plan.start_date)) {
    showError(__('تاريخ النهاية يجب أن يكون بعد تاريخ البداية'))
    return
  }

  saving.value = true
  try {
    const payload = buildPayload(status)
    if (isEdit.value) {
      await call('bs.baron_servies.api.decision_center.plan_api.update_plan', {
        plan_name: planId.value,
        data: JSON.stringify(payload),
      })
      showSuccess(__('تم تحديث الخطة'))
    } else {
      const res = await call('bs.baron_servies.api.decision_center.plan_api.create_plan', {
        data: JSON.stringify(payload),
      })
      showSuccess(__('تم إنشاء الخطة'))
      router.push({ name: 'DecisionCenterPlanDetail', params: { planId: res.name } })
      return
    }
    router.push({ name: 'DecisionCenterPlanDetail', params: { planId: planId.value } })
  } catch (e) {
    showError(e.message || __('فشل حفظ الخطة'))
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await loadPermission()
    await loadReferenceOptions()
    if (isEdit.value && !canManage.value) return
    await loadPlan()
  } catch (e) {
    showError(e.message || __('فشل تحميل الخطة'))
  } finally {
    loading.value = false
  }
})
</script>

<script>
import { defineComponent, h } from 'vue'

const FormField = defineComponent({
  props: ['modelValue', 'label', 'type', 'options', 'required'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const baseClass = 'w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white'
    return () => {
      const label = h('label', { class: 'block text-xs font-medium text-slate-600 mb-1' }, props.label + (props.required ? ' *' : ''))
      let input
      if (props.type === 'textarea') {
        input = h('textarea', {
          class: baseClass,
          value: props.modelValue,
          onInput: (e) => emit('update:modelValue', e.target.value),
          rows: 3,
        })
      } else if (props.type === 'select') {
        input = h('select', {
          class: baseClass,
          value: props.modelValue,
          onChange: (e) => emit('update:modelValue', e.target.value),
        }, [
          ...(props.options || []).map((opt) => h('option', { value: opt.value }, opt.label)),
        ])
      } else if (props.type === 'number') {
        input = h('input', {
          class: baseClass,
          type: 'number',
          value: props.modelValue === null || props.modelValue === undefined ? '' : props.modelValue,
          onInput: (e) => emit('update:modelValue', e.target.value === '' ? null : Number(e.target.value)),
        })
      } else if (props.type === 'date') {
        input = h('input', {
          class: baseClass,
          type: 'date',
          value: props.modelValue || '',
          onInput: (e) => emit('update:modelValue', e.target.value),
        })
      } else {
        input = h('input', {
          class: baseClass,
          type: 'text',
          value: props.modelValue || '',
          onInput: (e) => emit('update:modelValue', e.target.value),
        })
      }
      return h('div', {}, [label, input])
    }
  },
})

export default defineComponent({
  components: { FormField },
})
</script>
