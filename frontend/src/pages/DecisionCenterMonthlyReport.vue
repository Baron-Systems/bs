<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6" dir="rtl">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{{ __('التقرير الشهري') }}</h1>
        <p class="text-slate-500 text-sm">{{ month }}</p>
      </div>
      <div class="flex items-center gap-3">
        <span
          v-if="report?.is_locked"
          class="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800"
        >
          {{ __('مغلق') }}
        </span>
        <span v-else class="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
          {{ __('مفتوح') }}
        </span>
        <Button variant="outline" size="sm" @click="refresh">{{ __('تحديث') }}</Button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-slate-500">{{ __('جاري التحميل...') }}</div>

    <template v-else-if="report">
      <!-- Metrics -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          :label="__('إجمالي المبيعات')"
          :value="formatCurrency(report.metrics?.sales_total?.value)"
          type="currency"
        />
        <MetricCard
          :label="__('إجمالي المصاريف')"
          :value="formatCurrency(report.expense_categories?.total_expenses)"
          type="currency"
        />
        <MetricCard
          :label="__('المصاريف/المبيعات %')"
          :value="formatPct(report.expense_categories?.expense_to_sales_pct)"
          type="pct"
        />
        <MetricCard
          :label="__('العملاء النشطون')"
          :value="report.metrics?.active_customers?.value"
          type="number"
        />
      </div>

      <!-- Plan snapshot -->
      <div v-if="report.plan?.active_plan" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4">{{ __('الخطة الحالية في اللقطة') }}</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-4 bg-slate-50 rounded-xl">
            <div class="text-sm text-slate-500">{{ __('اسم الخطة') }}</div>
            <div class="font-medium text-slate-800">{{ report.plan.plan_name }}</div>
          </div>
          <div class="p-4 bg-slate-50 rounded-xl">
            <div class="text-sm text-slate-500">{{ __('المؤشر الرئيسي') }}</div>
            <div class="font-medium text-slate-800">{{ report.plan.primary_kpi }}</div>
          </div>
          <div class="p-4 bg-slate-50 rounded-xl">
            <div class="text-sm text-slate-500">{{ __('تحقيق الهدف') }}</div>
            <div class="font-medium text-slate-800">{{ report.plan.target_achieved ? __('نعم') : __('لا') }}</div>
          </div>
        </div>
      </div>

      <!-- Expense categories -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4">{{ __('تصنيفات المصاريف') }}</h2>
        <DataTable :columns="expenseColumns" :data="report.expense_categories?.categories || []" row-key="category" :searchable="false" />
      </div>

      <!-- Decisions -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4">{{ __('القرارات') }} ({{ report.decisions?.count || 0 }})</h2>
        <div v-if="!decisions.length" class="text-slate-500 text-sm">{{ __('لا توجد قرارات') }}</div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <DecisionCard v-for="decision in decisions" :key="decision.id" :decision="decision" />
        </div>
      </div>

      <!-- Audit -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h2 class="text-lg font-bold text-slate-800">{{ __('سجل التدقيق') }}</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-slate-600">
          <div class="bg-slate-50 rounded-xl p-3">
            <p class="text-slate-500">{{ __('إصدار المحرك') }}</p>
            <p class="font-medium text-slate-800">{{ report.engine_version }}</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-3">
            <p class="text-slate-500">{{ __('بصمة إصدار القواعد') }}</p>
            <p class="font-medium text-slate-800 break-all">{{ report.rule_version_hash }}</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-3">
            <p class="text-slate-500">{{ __('تاريخ الإنشاء') }}</p>
            <p class="font-medium text-slate-800">{{ report.generated_at }}</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-3">
            <p class="text-slate-500">{{ __('تاريخ القفل') }}</p>
            <p class="font-medium text-slate-800">{{ report.locked_at || '—' }}</p>
          </div>
        </div>

        <h3 class="font-bold text-slate-800 mt-6 mb-2">{{ __('المراجعات') }}</h3>
        <DataTable :columns="revisionColumns" :data="report.revisions || []" row-key="revision_number" :searchable="false" />
      </div>
    </template>

    <div v-else class="text-center py-12 text-slate-500">{{ __('التقرير غير موجود') }}</div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue"
import { useRoute } from "vue-router"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import Button from "frappe-ui/src/components/Button.vue"
import MetricCard from "@/components/dc/MetricCard.vue"
import DataTable from "@/components/dc/DataTable.vue"
import DecisionCard from "@/components/dc/DecisionCard.vue"

const route = useRoute()
const { showError } = useToast()
const report = ref(null)
const loading = ref(false)
const currency = ref("")

const month = computed(() => route.params.month)
const decisions = computed(() => report.value?.decisions?.decisions || [])

const expenseColumns = [
  { key: "category", label: "التصنيف" },
  { key: "amount", label: "المبلغ" },
  { key: "previous_amount", label: "الفترة السابقة" },
  { key: "growth_pct", label: "النمو %" },
  { key: "target", label: "المستهدف %" },
  { key: "max", label: "الحد الأقصى %" },
]

const revisionColumns = [
  { key: "revision_number", label: "#" },
  { key: "action", label: "الإجراء" },
  { key: "performed_by", label: "بواسطة" },
  { key: "performed_at", label: "التاريخ" },
  { key: "reason", label: "السبب" },
]

function formatCurrency(value) {
  const n = Number(value || 0)
  return n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function formatPct(value) {
  if (value === null || value === undefined) return "—"
  const n = Number(value)
  if (isNaN(n)) return "—"
  return `${n.toFixed(1)}%`
}

async function refresh() {
  loading.value = true
  try {
    const res = await call("bs.baron_servies.api.decision_center.snapshot_api.get_monthly_report", {
      month: month.value,
    })
    report.value = res
  } catch (e) {
    showError(e.message || "Failed to load report")
  } finally {
    loading.value = false
  }
}

watch(month, refresh)
onMounted(refresh)
</script>
