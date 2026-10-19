<template>
	<div class="w-full">
		<main class="flex flex-col gap-5">
			<PageHeader :eyebrow="__('الرئيسية')" :title="__('لوحة المعلومات')" :subtitle="__('ملخص المحل من دفتر الأستاذ العام')">
				<template #meta>
					<span v-if="data" class="tabular-nums"> · {{ data.from_date }} → {{ data.to_date }}</span>
				</template>
				<template #actions>
					<select
						v-model="selectedCompany"
						class="bs-input !w-auto min-w-[180px] !py-2"
						:disabled="loadingCompanies"
						@change="loadData"
					>
						<option value="" disabled>{{ loadingCompanies ? __("جاري التحميل...") : __("اختر الشركة") }}</option>
						<option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
					</select>
				</template>
			</PageHeader>

			<!-- Filter row -->
			<div class="flex flex-wrap items-center gap-2">
				<div class="bs-segment">
					<button
						v-for="p in presets"
						:key="p.days"
						@click="setPeriod(p.days)"
						class="bs-segment-item !py-1.5 !text-[12px]"
						:class="activePreset === p.days ? 'bs-segment-item-active' : ''"
					>{{ p.label }}</button>
				</div>
				<div class="bs-segment items-center !gap-1.5">
					<input v-model="fromDate" type="date" class="border-0 bg-transparent px-2 py-1 text-[12px] focus:ring-0" @change="loadData" />
					<span class="text-slate-300">←</span>
					<input v-model="toDate" type="date" class="border-0 bg-transparent px-2 py-1 text-[12px] focus:ring-0" @change="loadData" />
				</div>
			</div>

			<!-- First load skeleton -->
			<div v-if="loading && !data" class="grid grid-cols-12 gap-4 animate-pulse">
				<div v-for="i in 4" :key="i" class="col-span-6 lg:col-span-3 h-28 bs-card"></div>
				<div class="col-span-12 lg:col-span-8 h-80 bs-card"></div>
				<div class="col-span-12 lg:col-span-4 h-80 bs-card"></div>
			</div>

			<div v-else-if="data" class="flex flex-col gap-4 transition-opacity" :class="loading ? 'opacity-50 pointer-events-none' : ''">
				<!-- Primary KPIs -->
				<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
					<KpiTile :label="__('صافي المبيعات')" :value="formatCurrency(s.total_sales)" :spark="trend.map((m) => m.sales)" :color="SERIES[0]" :hint="__('شهري')" />
					<KpiTile :label="__('صافي الربح')" :value="formatCurrency(s.gross_profit)" :hint="s.total_sales ? __('هامش') + ' ' + margin + '%' : ''" />
					<KpiTile :label="__('صافي التدفق النقدي')" :value="formatCurrency(s.net_cash)" :hint="__('النقدية والبنوك')" />
					<KpiTile :label="__('المشتريات')" :value="formatCurrency(s.total_purchases)" :spark="trend.map((m) => m.purchases)" :color="SERIES[5]" :hint="__('شهري')" />
				</div>

				<div class="grid grid-cols-12 gap-4">
					<!-- Trend -->
					<ChartCard class="col-span-12 lg:col-span-8" :title="__('المبيعات مقابل المشتريات')" :subtitle="__('شهري')" :height="300" :empty="!trend.some((m) => m.sales || m.purchases)">
						<Bar :data="trendChart" :options="trendOptions" />
					</ChartCard>

					<!-- Cash & balances -->
					<section class="col-span-12 lg:col-span-4 bs-card bs-card-pad flex flex-col">
						<h3 class="bs-card-title">{{ __("النقدية والأرصدة") }}</h3>
						<p class="bs-card-subtitle">{{ __("حركة النقد خلال الفترة والأرصدة حتى نهايتها") }}</p>
						<div class="mt-4 grid grid-cols-2 gap-3">
							<div class="bs-soft p-3">
								<p class="bs-stat-label">{{ __("مدفوعات واردة") }}</p>
								<p class="bs-stat-value text-emerald-700">{{ formatCurrency(s.total_payments_in) }}</p>
							</div>
							<div class="bs-soft p-3">
								<p class="bs-stat-label">{{ __("مدفوعات صادرة") }}</p>
								<p class="bs-stat-value text-rose-700">{{ formatCurrency(s.total_payments_out) }}</p>
							</div>
						</div>
						<div class="mt-4 flex h-2.5 overflow-hidden rounded-full gap-[2px]">
							<div class="h-full rounded-s-full" :style="{ width: cashInShare + '%', backgroundColor: SERIES[2] }"></div>
							<div class="h-full flex-1 rounded-e-full" :style="{ backgroundColor: SERIES[1] }"></div>
						</div>
						<ul class="mt-5 flex flex-col divide-y divide-slate-100 text-[13px]">
							<li class="flex items-center justify-between py-2.5">
								<span class="text-slate-600">{{ __("مستحقات العملاء") }}</span>
								<span class="font-bold text-slate-900 tabular-nums">{{ formatCurrency(s.outstanding_receivable) }}</span>
							</li>
							<li class="flex items-center justify-between py-2.5">
								<span class="text-slate-600">{{ __("مستحقات للموردين") }}</span>
								<span class="font-bold text-slate-900 tabular-nums">{{ formatCurrency(s.outstanding_payable) }}</span>
							</li>
							<li class="flex items-center justify-between py-2.5">
								<span class="text-slate-600">{{ __("تكلفة البضاعة المباعة") }}</span>
								<span class="font-bold text-slate-900 tabular-nums">{{ formatCurrency(s.cogs) }}</span>
							</li>
						</ul>
					</section>
				</div>

				<div class="grid grid-cols-12 gap-4">
					<ChartCard class="col-span-12 lg:col-span-7" fluid :title="__('أفضل الأصناف مبيعاً')" :empty="!data.top_items.length">
						<RankList :rows="data.top_items" label-key="item_name" value-key="amount" secondary-key="qty" :format="formatCurrency" :secondary-format="(v) => formatNumber(v) + ' ' + __('وحدة')" :color="SERIES[0]" />
					</ChartCard>
					<ChartCard class="col-span-12 lg:col-span-5" fluid :title="__('المقبوضات حسب الحساب')" :subtitle="__('النقدية والبنوك')" :empty="!data.payments_by_mode.length">
						<DonutPanel :rows="data.payments_by_mode.map((m) => ({ label: m.mode, value: m.amount }))" :format="formatCurrency" :center-label="__('الإجمالي')" />
					</ChartCard>
				</div>

				<div class="grid grid-cols-12 gap-4">
					<ChartCard class="col-span-12 lg:col-span-4" fluid :title="__('أفضل العملاء')" :empty="!data.top_customers.length">
						<RankList :rows="data.top_customers" label-key="customer" value-key="total" secondary-key="invoices" :format="formatCurrency" :secondary-format="(v) => formatNumber(v) + ' ' + __('فاتورة')" :color="SERIES[0]" />
					</ChartCard>
					<ChartCard class="col-span-12 lg:col-span-4" fluid :title="__('أقل الأصناف مبيعاً')" :empty="!data.bottom_items.length">
						<RankList :rows="data.bottom_items" label-key="item_name" value-key="amount" secondary-key="qty" :format="formatCurrency" :secondary-format="(v) => formatNumber(v) + ' ' + __('وحدة')" :color="SERIES[1]" />
					</ChartCard>
					<ChartCard class="col-span-12 lg:col-span-4" fluid :title="__('أصناف منخفضة المخزون')" :subtitle="__('الكمية المتوفرة 5 أو أقل')">
						<ul v-if="data.low_stock_items.length" class="flex flex-col divide-y divide-slate-100">
							<li v-for="item in data.low_stock_items" :key="item.item_code" class="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
								<span class="bs-badge" :class="item.actual_qty <= 0 ? 'bs-badge-red' : 'bs-badge-amber'">
									{{ item.actual_qty <= 0 ? __("نفد") : __("منخفض") }}
								</span>
								<span class="flex-1 min-w-0 truncate text-[13px] font-medium text-slate-700">{{ item.item_name || item.item_code }}</span>
								<span class="text-[13px] font-bold tabular-nums" :class="item.actual_qty <= 0 ? 'text-rose-700' : 'text-amber-700'">
									{{ formatNumber(item.actual_qty) }} <span class="text-[11px] font-medium text-slate-400">{{ item.stock_uom }}</span>
								</span>
							</li>
						</ul>
						<div v-else class="bs-empty">
							<svg class="h-8 w-8 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							{{ __("المخزون بحالة جيدة") }}
						</div>
					</ChartCard>
				</div>
			</div>
		</main>
	</div>
</template>

<script setup>
import { Bar } from "vue-chartjs"
import {
	Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement,
	ArcElement, BarController, LineController, Tooltip, Legend, Filler,
} from "chart.js"
import { call } from "@/utils/apiWrapper"
import { session } from "@/data/session"
import { useToast } from "@/composables/useToast"
import router from "@/router"
import { computed, onMounted, ref } from "vue"
import PageHeader from "@/components/ui/PageHeader.vue"
import KpiTile from "@/components/dc/KpiTile.vue"
import ChartCard from "@/components/dc/ChartCard.vue"
import RankList from "@/components/dc/RankList.vue"
import DonutPanel from "@/components/dc/DonutPanel.vue"
import { SERIES, FONT, tooltip, legend, valueAxis, categoryAxis, barStyle } from "@/components/dc/vizTheme"

ChartJS.register(
	CategoryScale, LinearScale, PointElement, LineElement, BarElement,
	ArcElement, BarController, LineController, Tooltip, Legend, Filler,
)
ChartJS.defaults.font.family = FONT

const { showError } = useToast()

// State
const companies = ref([])
const selectedCompany = ref("")
const loadingCompanies = ref(false)
const loading = ref(false)
const data = ref(null)
const fromDate = ref("")
const toDate = ref("")
const activePreset = ref(180)

const presets = [
	{ days: 30, label: __("30 يوم") },
	{ days: 90, label: __("90 يوم") },
	{ days: 180, label: __("6 أشهر") },
	{ days: 365, label: __("سنة") },
]

const s = computed(() => data.value?.summary || {})
const trend = computed(() => data.value?.sales_by_month || [])
const margin = computed(() => (s.value.total_sales ? ((s.value.gross_profit / s.value.total_sales) * 100).toFixed(1) : "0"))
const cashInShare = computed(() => {
	const total = Number(s.value.total_payments_in || 0) + Number(s.value.total_payments_out || 0)
	return total ? (Number(s.value.total_payments_in || 0) / total) * 100 : 50
})

// Lifecycle
onMounted(async () => {
	if (!session.isLoggedIn) {
		router.replace({ name: "Login" })
		return
	}
	setPeriod(180, false)
	await loadCompanies()
	await loadData()
})

// Methods
async function loadCompanies() {
	loadingCompanies.value = true
	try {
		companies.value = await call("bs.baron_servies.api.utilities.get_companies") || []
		if (companies.value.length && !selectedCompany.value) {
			selectedCompany.value = companies.value[0].name
		}
	} catch (e) {
		showError(e?.message || __("فشل تحميل الشركات"))
	} finally {
		loadingCompanies.value = false
	}
}

async function loadData() {
	loading.value = true
	try {
		data.value = await call("bs.baron_servies.api.dashboard.get_dashboard_data", {
			company: selectedCompany.value || undefined,
			from_date: fromDate.value || undefined,
			to_date: toDate.value || undefined,
		})
	} catch (e) {
		showError(e?.message || __("فشل تحميل البيانات"))
	} finally {
		loading.value = false
	}
}

function setPeriod(days, reload = true) {
	const today = new Date()
	const past = new Date()
	past.setDate(past.getDate() - days)
	toDate.value = today.toISOString().split("T")[0]
	fromDate.value = past.toISOString().split("T")[0]
	activePreset.value = days
	if (reload) loadData()
}

// Chart
const trendChart = computed(() => ({
	labels: trend.value.map((d) => d.label),
	datasets: [
		{ label: __("المبيعات"), data: trend.value.map((d) => d.sales), backgroundColor: SERIES[0], ...barStyle },
		{ label: __("المشتريات"), data: trend.value.map((d) => d.purchases), backgroundColor: SERIES[5], ...barStyle },
	],
}))

const trendOptions = {
	responsive: true,
	maintainAspectRatio: false,
	interaction: { mode: "index", intersect: false },
	plugins: {
		legend,
		tooltip: tooltip({ callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${formatCurrency(ctx.parsed.y)}` } }),
	},
	scales: { x: categoryAxis(), y: valueAxis() },
}

// Formatters
function formatCurrency(value) {
	const n = Number(value || 0)
	const cur = data.value?.summary?.currency || ""
	return n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + (cur ? " " + cur : "")
}

function formatNumber(value) {
	return Number(value || 0).toLocaleString("en-US", { maximumFractionDigits: 2 })
}
</script>
