<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6" dir="rtl">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-3 min-w-0">
        <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-purple-700 shadow-lg shadow-indigo-500/25">
          <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <div class="min-w-0">
          <h1 class="text-lg font-bold text-slate-900 truncate">{{ __('التقارير الشهرية') }}</h1>
          <p class="text-xs text-slate-500 truncate">{{ __('لقطات شهرية محفوظة وغير قابلة للتعديل') }}</p>
        </div>
      </div>
      <Button variant="outline" size="sm" @click="load">{{ __('تحديث') }}</Button>
    </div>

    <div v-if="!loading && !reports.length" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-10 text-center space-y-4">
      <div class="mx-auto w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
        <svg class="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <h2 class="text-lg font-bold text-slate-900">{{ __('لا توجد تقارير شهرية بعد') }}</h2>
      <p class="text-sm text-slate-500 max-w-md mx-auto">
        {{ __('التقارير تُنشأ تلقائيًا في أول يوم من كل شهر للشهر السابق. يمكنك أيضًا إنشاء تقرير الشهر الماضي يدويًا الآن.') }}
      </p>
      <Button variant="solid" size="sm" :loading="processing" @click="generateLastMonthReport">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        {{ __('إنشاء تقرير الشهر الماضي') }}
      </Button>
    </div>

    <div v-else class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <DataTable :columns="columns" :data="reports" :loading="loading" row-key="month" :searchable="false">
        <template #cell-month="{ value }">
          <RouterLink
            :to="{ name: 'DecisionCenterMonthlyReport', params: { month: value } }"
            class="text-blue-600 hover:underline font-medium"
          >
            {{ value }}
          </RouterLink>
        </template>
        <template #cell-is_locked="{ value }">
          <span v-if="value" class="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{{ __('مغلق') }}</span>
          <span v-else class="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">{{ __('مفتوح') }}</span>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import Button from "frappe-ui/src/components/Button.vue"
import DataTable from "@/components/dc/DataTable.vue"

const { showError, showSuccess } = useToast()
const reports = ref([])
const loading = ref(false)
const processing = ref(false)

function previousMonth() {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()
  if (month === 0) return `${year - 1}-12`
  return `${year}-${String(month).padStart(2, '0')}`
}

async function generateLastMonthReport() {
  processing.value = true
  try {
    const month = previousMonth()
    await call('bs.baron_servies.api.decision_center.snapshot_api.regenerate_snapshot', {
      month,
      reason: __('إنشاء يدوي من صفحة التقارير الشهرية'),
    })
    showSuccess(__('تم إنشاء التقرير بنجاح'))
    await load()
  } catch (e) {
    showError(e.message || __('فشل إنشاء التقرير'))
  } finally {
    processing.value = false
  }
}

const columns = [
  { key: "month", label: "الشهر" },
  { key: "generated_at", label: "تاريخ الإنشاء" },
  { key: "sales_total", label: "المبيعات" },
  { key: "total_expenses", label: "المصاريف" },
  { key: "expense_to_sales_pct", label: "المصاريف/المبيعات %" },
  { key: "decision_count", label: "القرارات" },
  { key: "is_locked", label: "الحالة" },
  { key: "engine_version", label: "الإصدار" },
]

async function load() {
  loading.value = true
  try {
    const res = await call("bs.baron_servies.api.decision_center.snapshot_api.get_monthly_report_list", { count: 24 })
    reports.value = res.reports || []
  } catch (e) {
    showError(e.message || "فشل تحميل التقارير")
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
